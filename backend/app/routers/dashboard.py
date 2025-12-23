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
        
        # New Companies (Today & This Week)
        # Using specific intervals for Postgres
        new_today = conn.execute(text("SELECT COUNT(*) FROM companies WHERE registration_date = CURRENT_DATE")).scalar()
        new_week = conn.execute(text("SELECT COUNT(*) FROM companies WHERE registration_date >= DATE_TRUNC('week', CURRENT_DATE)")).scalar()
        
        # Liquidated (This Week) - Assuming status change or liquidation event. 
        # For simplicity, if we don't have exact liquidation date index, we might skip or use a proxy.
        # Let's assume we count those with status 'liquidated' and updated_at this week? 
        # Or simplistic: just count total liquidated? The requirements asked for "Liquidated This Week".
        # If we don't have liquidation_date, we can't do exact. 
        # We'll use a placeholder or verify schema. init.sql has registration_date, but not liquidation_date.
        # We can try to use `last_updated` for liquidated companies as a proxy.
        liquidated_week = conn.execute(text("""
            SELECT COUNT(*) FROM companies 
            WHERE status = 'liquidated' 
            AND last_updated >= DATE_TRUNC('week', CURRENT_DATE)
        """)).scalar()

        # Total Turnover (Macro Stat - can becached or fast sum if indexed, but SUM is slow)
        # Better to take from cached materialized view or dashboard cache if calculated there.
        # Let's add it to the refresh script in future, but for now we can get it from industry_stats_materialized if it exists,
        # or just sum the tops? No, that's too small.
        # Let's do a fast approximate or use the one from refresh script if we added it.
        # We didn't add it to dashboard_data explicitly. 
        # Let's just do a heavy query cached? No, requirements say NO heavy queries.
        # We will use a static estimate or fetch from a pre-calculated aggregate table if available.
        # For now, let's calculate it in the cache script next time. 
        # Quick fix: query industry_stats_materialized sum if available.
        total_turnover = conn.execute(text("SELECT SUM(total_turnover) FROM industry_stats_materialized WHERE nace_level = 1")).scalar()
        
        # 3. Latest Registered (Live)
        latest_rows = conn.execute(text("""
            SELECT name, regcode, registration_date 
            FROM companies 
            ORDER BY registration_date DESC, regcode DESC 
            LIMIT 5
        """)).fetchall()
        
        latest_registered = [
            {
                "name": row.name,
                "regcode": row.regcode,
                "date": row.registration_date.isoformat() if row.registration_date else None,
                # Frontend can calc "time ago" or we can do it here if we had precise datetime
            }
            for row in latest_rows
        ]

        # Combine
        return {
            "pulse": {
                "active_companies": active_count,
                "new_today": new_today,
                "new_this_week": new_week,
                "liquidated_this_week": liquidated_week,
                "total_turnover": total_turnover or 0
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
    """
    if not q or len(q) < 2:
        return []
        
    conn = engine.connect()
    try:
        # Optimized ILIKE with limit
        # In real prod: ElasticSearch or tsvector
        rows = conn.execute(text("""
            SELECT name, regcode, 'company' as type 
            FROM companies 
            WHERE name ILIKE :q 
            LIMIT 5
        """), {"q": f"%{q}%"}).fetchall()
        
        return [{"name": r.name, "regcode": r.regcode, "type": r.type} for r in rows]
    finally:
        conn.close()
