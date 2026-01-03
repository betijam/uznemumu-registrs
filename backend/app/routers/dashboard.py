from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import json
import os
from dotenv import load_dotenv
from app.routers.companies import engine # Reuse engine

router = APIRouter()

@router.get("/home/dashboard")
def get_home_dashboard():
    """
    Agregēts endpoints sākumlapai (BI Dashboard).
    Atgriež:
    - Pulse (Live/Fast stats): Aktīvie, Jaunie šodien/šonedēļ, Likvidētie, Kopējais apgrozījums.
    - Tops (Cached): Apgrozījums, Peļņa, Algas (from dashboard_cache).
    - Latest (Live): Pēdējie 5 reģistrētie.
    """
    conn = engine.connect()
    
    try:
        # 1. Fetch Cached Tops & Gazeles
        cache_row = conn.execute(text("SELECT data FROM dashboard_cache WHERE key = 'main_dashboard'")).fetchone()
        cached_data = cache_row[0] if cache_row else {"tops": {}, "gazeles": []}
        
        # 2. Live Pulse Data (Fast Queries with Indexes)
        # Active Companies
        active_count = conn.execute(text("SELECT COUNT(*) FROM companies WHERE status = 'active'")).scalar()
        
        # Total Turnover (from industry_stats_materialized)
        total_turnover = conn.execute(text("SELECT SUM(total_turnover) FROM industry_stats_materialized WHERE nace_level = 1")).scalar()
        
        # Total Employees (from tax_payments for most recent year)
        total_employees_row = conn.execute(text("""
            SELECT SUM(avg_employees) as total_employees, year
            FROM tax_payments 
            WHERE year = (SELECT MAX(year) FROM tax_payments WHERE avg_employees IS NOT NULL)
            GROUP BY year
        """)).fetchone()
        total_employees = total_employees_row[0] if total_employees_row else 0
        employees_year = total_employees_row[1] if total_employees_row else None
        
        # Average Gross Salary (from tax_payments)
        # Formula: (social_tax_vsaoi / avg_employees / 12 / 0.3409) for companies with >= 5 employees
        avg_salary_row = conn.execute(text("""
            SELECT AVG(social_tax_vsaoi / NULLIF(avg_employees, 0) / 12 / 0.3409) as avg_gross
            FROM tax_payments 
            WHERE year = (SELECT MAX(year) FROM tax_payments)
              AND avg_employees >= 5
              AND social_tax_vsaoi > 0
        """)).fetchone()
        avg_salary = avg_salary_row[0] if avg_salary_row and avg_salary_row[0] else 0
        
        # 3. Latest Registered (Live)
        latest_rows = conn.execute(text("""
            SELECT name, name_in_quotes, "type" as company_type, type_text, regcode, registration_date 
            FROM companies 
            ORDER BY registration_date DESC, regcode DESC 
            LIMIT 5
        """)).fetchall()
        
        latest_registered = [
            {
                "name": row.name,
                "name_in_quotes": row.name_in_quotes if hasattr(row, 'name_in_quotes') else None,
                "type": row.company_type if hasattr(row, 'company_type') else None,
                "type_text": row.type_text if hasattr(row, 'type_text') else None,
                "regcode": row.regcode,
                "date": row.registration_date.isoformat() if row.registration_date else None,
            }
            for row in latest_rows
        ]

        # Combine
        return {
            "pulse": {
                "active_companies": active_count,
                "total_employees": int(total_employees) if total_employees else 0,
                "avg_salary": round(avg_salary) if avg_salary else 0,
                "total_turnover": total_turnover or 0,
                "data_year": employees_year
            },
            "tops": cached_data.get("tops", {}),
            "gazeles": cached_data.get("gazeles", []),
            "latest_registered": latest_registered
        }
        
    except Exception as e:
        print(f"Stats Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/home/search-hint")
def search_hint(q: str):
    """
    Fast autocomplete/hint endpoint.
    Returns companies and persons separately.
    """
    if not q or len(q) < 2:
        return {"companies": [], "persons": []}
        
    conn = engine.connect()
    try:
        # 1. Search Companies
        companies = conn.execute(text("""
            SELECT name, regcode, 'company' as type 
            FROM companies 
            WHERE name ILIKE :q 
            LIMIT 5
        """), {"q": f"%{q}%"}).fetchall()
        
        # 2. Search Persons
        persons = conn.execute(text("""
            SELECT 
                p.person_name,
                p.person_code,
                p.person_hash,
                COUNT(DISTINCT p.company_regcode) as company_count
            FROM persons p
            WHERE p.person_name ILIKE :q
                AND p.person_code IS NOT NULL
            GROUP BY p.person_code, p.person_name, p.person_hash
            ORDER BY company_count DESC, p.person_name
            LIMIT 5
        """), {"q": f"%{q}%"}).fetchall()
        
        # Helper for person hash
        def get_person_hash(code, name, existing_hash):
            if existing_hash:
                return existing_hash
            # Compute hash if missing
            # Normalize name: lowercase -> split -> sort -> join
            normalized_name = " ".join(sorted(name.lower().split()))
            
            # Use only first 6 chars of person_code (DDMMYY)
            code_fragment = code[:6] if code else ""
            hash_input = f"{code_fragment}|{normalized_name}"
            
            hash_val = 0
            for char in hash_input:
                hash_val = ((hash_val << 5) - hash_val) + ord(char)
                hash_val = hash_val & 0xFFFFFFFF
            return format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]

        return {
            "companies": [{"name": r.name, "regcode": r.regcode, "type": "company"} for r in companies],
            "persons": [
                {
                    "name": p.person_name,
                    "person_id": get_person_hash(p.person_code, p.person_name, p.person_hash),
                    "company_count": p.company_count,
                    "type": "person"
                } 
                for p in persons
            ]
        }
    finally:
        conn.close()

