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
        total_turnover = conn.execute(text("SELECT SUM(total_turnover) FROM industry_stats_materialized WHERE nace_level = 0")).scalar()
        
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
    Fast autocomplete/hint endpoint with flexible search.
    - Case insensitive
    - Accent insensitive (ā=a, ē=e, etc.)
    - Word order independent ("SIA Animas" finds "Animas, SIA")
    Returns companies and persons separately.
    """
    if not q or len(q) < 2:
        return {"companies": [], "persons": []}
    
    # Normalize query: split into words for flexible matching
    query_words = q.strip().split()
    
    conn = engine.connect()
    try:
        # Ensure unaccent extension exists (run once, cached by PostgreSQL)
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            conn.commit()
        except:
            pass  # Extension may already exist
        
        # 1. Search Companies - flexible matching
        # Match ALL words in any order, accent-insensitive
        # Also search in 'type' column for abbreviations (SIA, AS, etc.)
        
        # Common company type abbreviations to handle
        TYPE_ABBREVIATIONS = {
            'sia': ['sia', 'sabiedrība', 'ierobežotu', 'atbildību'],
            'as': ['as', 'akciju', 'sabiedrība'],
            'ik': ['ik', 'individuālais', 'komersants'],
            'zs': ['zs', 'zemnieku', 'saimniecība'],
            'ks': ['ks', 'kooperatīvā', 'sabiedrība'],
            'ps': ['ps', 'pilnsabiedrība'],
        }
        
        if not query_words:
            companies = []
        else:
            # OPTIMIZED SEARCH: Match name words + Prioritized ranking
            conditions = []
            params = {"q_raw": q.strip()}
            
        # Filter out known abbreviations from search words (will match via type column)
        name_words = []
        type_words = []
        for word in query_words:
            word_lower = word.lower()
            if word_lower in TYPE_ABBREVIATIONS:
                type_words.append(word_lower)
            else:
                name_words.append(word)

        if not name_words and not type_words:
            return {"companies": [], "persons": []}
            
        # Use name_words for ranking, but fall back to all words if searching only SIA etc.
        primary_name = " ".join(name_words) if name_words else q.strip()
        
        # Use unaccented lower comparison to hit our new GIN/Trigram indexes
        conditions = []
        params = {"q_raw": primary_name}
        
        words_to_match = name_words if name_words else query_words
        for i, word in enumerate(words_to_match):
            conditions.append(f"immutable_unaccent(lower(name)) LIKE immutable_unaccent(lower(:word{i}))")
            params[f"word{i}"] = f"%{word}%"
            
            if type_words:
                type_cond = " OR ".join([f"LOWER(\"type\") = :type{i}" for i in range(len(type_words))])
                conditions.append(f"({type_cond})")
                for i, tw in enumerate(type_words):
                    params[f"type{i}"] = tw.lower()
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Ranking: Active > Exact/Prefix > Turnover (Denormalized column)
            company_sql = f"""
                SELECT name, name_in_quotes, "type" as company_type, regcode
                FROM companies 
                WHERE {where_clause}
                ORDER BY 
                    CASE WHEN status = 'active' THEN 0 ELSE 1 END,
                    CASE 
                        WHEN immutable_unaccent(lower(name_in_quotes)) = immutable_unaccent(lower(:q_raw)) THEN 0 
                        WHEN immutable_unaccent(lower(name_in_quotes)) LIKE immutable_unaccent(lower(:q_raw)) || '%' THEN 1
                        ELSE 2 
                    END,
                    latest_turnover DESC NULLS LAST
                LIMIT 7
            """
            companies = conn.execute(text(company_sql), params).fetchall()
        
        # 2. Search Persons - same flexible matching
        # 2. Search Persons - Optimized with functional index
        if len(query_words) >= 1:
            person_sql = """
                SELECT 
                    person_name, person_code, person_hash, 
                    COUNT(DISTINCT company_regcode) as company_count
                FROM persons
                WHERE immutable_unaccent(lower(person_name)) LIKE immutable_unaccent(lower(:q_pattern))
                GROUP BY person_code, person_name, person_hash
                ORDER BY company_count DESC, person_name
                LIMIT 5
            """
            persons = conn.execute(text(person_sql), {
                "q_pattern": f"%{' '.join(query_words)}%"
            }).fetchall()
        else:
            persons = []
        
        # Helper for person hash
        def get_person_hash(code, name, existing_hash):
            if existing_hash:
                return existing_hash
            normalized_name = " ".join(sorted(name.lower().split()))
            code_fragment = code[:6] if code else ""
            hash_input = f"{code_fragment}|{normalized_name}"
            hash_val = 0
            for char in hash_input:
                hash_val = ((hash_val << 5) - hash_val) + ord(char)
                hash_val = hash_val & 0xFFFFFFFF
            return format(abs(hash_val) & 0xFFFFFFFF, '08x')[:8]

        # Format company names as "Name, Type" for display
        formatted_companies = []
        for r in companies:
            # Use name_in_quotes if available, otherwise full name
            display_name = r.name_in_quotes if r.name_in_quotes else r.name
            # Add type suffix if available
            if r.company_type:
                display_name = f"{display_name}, {r.company_type}"
            
            formatted_companies.append({
                "name": display_name,
                "full_name": r.name,  # Keep original for reference
                "regcode": r.regcode, 
                "type": "company"
            })

        return {
            "companies": formatted_companies,
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

