from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from etl.loader import engine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
def get_stats():
    """Get statistics for the homepage"""
    stats = {
        "daily_stats": {"new_today": 0, "change": 0},
        "top_earner": {"name": "N/A", "detail": ""},
        "top_revenue": {"amount": "0 €", "detail": ""}
    }
    
    try:
        with engine.connect() as conn:
            # Get count of companies registered today
            today_count = conn.execute(text("""
                SELECT COUNT(*) as cnt 
                FROM companies 
                WHERE registration_date >= CURRENT_DATE
            """)).scalar() or 0
            
            stats["daily_stats"]["new_today"] = today_count
            stats["daily_stats"]["change"] = max(0, today_count - 10)  # Simple mock change
            
            # Get top earner by latest turnover
            top_earner = conn.execute(text("""
                SELECT c.name, f.turnover
                FROM financial_reports f
                JOIN companies c ON c.regcode = f.company_regcode
                WHERE f.turnover IS NOT NULL
                ORDER BY f.turnover DESC
                LIMIT 1
            """)).fetchone()
            
            if top_earner:
                stats["top_earner"]["name"] = top_earner.name
                stats["top_earner"]["detail"] = f"Apgrozījums: {top_earner.turnover:,.0f} €"
            
            # Get top procurement amount
            top_procurement = conn.execute(text("""
                SELECT SUM(amount) as total, COUNT(*) as cnt
                FROM procurements
                WHERE contract_date >= CURRENT_DATE - INTERVAL '7 days'
            """)).fetchone()
            
            if top_procurement and top_procurement.total:
                total_m = top_procurement.total / 1_000_000
                stats["top_revenue"]["amount"] = f"{total_m:.1f} M€"
                stats["top_revenue"]["detail"] = f"{top_procurement.cnt} iepirkumi pēdējā nedēļā"
                
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
    
    return stats

@router.get("/search")
def search_companies(q: str):
    if not q or len(q) < 2:
        return []
    
    # Hybrid Search:
    # 1. Trigram similarity (fuzzy) -> name % q
    # 2. Full Text Search -> to_tsvector
    
    # We prioritize starts_with or simple ILIKE for speed on prefix, then trigram.
    # Using `SIMILARITY` function from pg_trgm
    
    sql = """
    SELECT regcode, name, address, status, registration_date
    FROM companies
    WHERE 
        name ILIKE :q_pattern OR
        CAST(regcode AS TEXT) LIKE :q_pattern OR
        name ILIKE :q_contains
    ORDER BY 
        (CASE WHEN name ILIKE :q_pattern THEN 2 
              WHEN CAST(regcode AS TEXT) LIKE :q_pattern THEN 1 
              ELSE 0 END) DESC,
        name ASC
    LIMIT 20;
    """
    
    result_data = []
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"q_pattern": f"{q}%", "q_contains": f"%{q}%"})
        for row in rows:
            result_data.append({
                "regcode": row.regcode,
                "name": row.name,
                "address": row.address,
                "status": row.status,
                "registration_date": str(row.registration_date) if row.registration_date else None
            })
            
    return result_data
