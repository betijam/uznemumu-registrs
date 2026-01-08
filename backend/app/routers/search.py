
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from app.core.database import engine
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache for stats (5 minute TTL)
_stats_cache = {"data": None, "expires": 0}
STATS_CACHE_TTL = 300  # 5 minutes

@router.get("/stats")
def get_stats():
    """Get statistics for the homepage (cached for 5 minutes)"""
    from datetime import datetime
    
    # Return cached data if still valid
    if _stats_cache["data"] and time.time() < _stats_cache["expires"]:
        logger.debug("Returning cached stats")
        return _stats_cache["data"]
    
    stats = {
        "daily_stats": {"new_today": 0, "change": 0},
        "top_earner": {"name": "N/A", "detail": ""},
        "weekly_procurements": {"amount": "0 €", "detail": ""}
    }
    
    try:
        with engine.connect() as conn:
            # Current year for filtering
            current_year = datetime.now().year
            
            # Get count of companies registered today
            today_count = conn.execute(text("""
                SELECT COUNT(*) as cnt 
                FROM companies 
                WHERE registration_date >= CURRENT_DATE
            """)).scalar() or 0
            
            # Get yesterday's count for real trend
            yesterday_count = conn.execute(text("""
                SELECT COUNT(*) as cnt 
                FROM companies 
                WHERE registration_date = CURRENT_DATE - INTERVAL '1 day'
            """)).scalar() or 0
            
            stats["daily_stats"]["new_today"] = today_count
            stats["daily_stats"]["change"] = today_count - yesterday_count
            
            # Get top earner by most recent year with data
            top_earner =conn.execute(text("""
                SELECT c.name, f.turnover, f.year
                FROM financial_reports f
                JOIN companies c ON c.regcode = f.company_regcode
                WHERE f.turnover IS NOT NULL
                ORDER BY f.year DESC, f.turnover DESC
                LIMIT 1
            """)).fetchone()
            
            if top_earner:
                stats["top_earner"]["name"] = top_earner.name
                stats["top_earner"]["detail"] = f"Apgrozījums: {top_earner.turnover:,.0f} € ({top_earner.year})"
            
            # Get weekly procurement total (last 7 days)
            weekly_procurement = conn.execute(text("""
                SELECT SUM(amount) as total, COUNT(*) as cnt
                FROM procurements
                WHERE contract_date >= CURRENT_DATE - INTERVAL '7 days'
            """)).fetchone()
            
            if weekly_procurement and weekly_procurement.total:
                total_k = weekly_procurement.total / 1_000
                stats["weekly_procurements"]["amount"] = f"{total_k:,.0f} €"
                stats["weekly_procurements"]["detail"] = f"{weekly_procurement.cnt} iepirkumi pēdējās 7 dienās"
            else:
                stats["weekly_procurements"]["amount"] = "0 €"
                stats["weekly_procurements"]["detail"] = "Nav datu pēdējās 7 dienās"
                
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
    
    # Update cache with new data
    _stats_cache["data"] = stats
    _stats_cache["expires"] = time.time() + STATS_CACHE_TTL
    
    return stats

@router.get("/search")
def search_companies(q: str = "", nace: str = None):
    """
    Search companies by name/regcode with optional industry filter.
    Flexible matching: case/accent insensitive, word order independent.
    
    Args:
        q: Search query (name or registration code)
        nace: NACE section code filter (e.g., "C", "62", "J")
    """
    if (not q or len(q) < 2) and not nace:
        return []
    
    # Split query into words for flexible matching
    query_words = q.strip().split() if q else []
    
    # Build WHERE clause
    where_conditions = []
    params = {}
    
    # Ensure unaccent extension
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            conn.commit()
        except:
            pass
    
    # Common company type abbreviations
    TYPE_ABBREVIATIONS = ['sia', 'as', 'ik', 'zs', 'ks', 'ps', 'biedrība', 'nodibinājums']
    
    # Separate type words from name words
    name_words = []
    type_words = []
    for word in query_words:
        word_lower = word.lower()
        if word_lower in TYPE_ABBREVIATIONS:
            type_words.append(word_lower)
        else:
            name_words.append(word)
    
    # Text search - match ALL words in any order, accent-insensitive
    if query_words:
        # Check if it's a regcode search (all digits)
        if query_words[0].isdigit():
            where_conditions.append("CAST(regcode AS TEXT) LIKE :q_pattern")
            params["q_pattern"] = f"{query_words[0]}%"
        else:
            # Name word conditions
            for i, word in enumerate(name_words):
                where_conditions.append(f"immutable_unaccent(lower(name)) LIKE immutable_unaccent(lower(:word{i}))")
                params[f"word{i}"] = f"%{word}%"
            
            # Type conditions (if any type abbreviations in query)
            if type_words:
                type_cond = " OR ".join([f"LOWER(\"type\") = :type{i}" for i in range(len(type_words))])
                where_conditions.append(f"({type_cond})")
                for i, tw in enumerate(type_words):
                    params[f"type{i}"] = tw.lower()
    
    # Industry filter
    if nace:
        where_conditions.append("nace_section = :nace")
        params["nace"] = nace
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    # Build ORDER BY - prioritize exact prefix matches
        # Improve ranking: 
        # 1. Active companies
        # 2. Exact word match at start of name OR name_in_quotes
        # 3. Contains match
        order_by = """
            CASE WHEN status = 'active' THEN 0 ELSE 1 END,
            CASE 
                WHEN immutable_unaccent(lower(name)) LIKE immutable_unaccent(lower(:first_word)) THEN 0 
                WHEN immutable_unaccent(lower(name_in_quotes)) LIKE immutable_unaccent(lower(:first_word)) THEN 0
                ELSE 1 
            END,
            length(name) ASC, 
            name ASC
        """
    else:
        order_by = "CASE WHEN status = 'active' THEN 0 ELSE 1 END, name ASC"
    
    sql = f"""
    SELECT regcode, name, name_in_quotes, "type" as company_type, type_text,
           address, status, registration_date, 
           nace_section, nace_section_text
    FROM companies
    WHERE {where_clause}
    ORDER BY {order_by}
    LIMIT 50;
    """
    
    result_data = []
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params)
        for row in rows:
            result_data.append({
                "regcode": row.regcode,
                "name": row.name,
                "name_in_quotes": row.name_in_quotes if hasattr(row, 'name_in_quotes') else None,
                "type": row.company_type if hasattr(row, 'company_type') else None,
                "type_text": row.type_text if hasattr(row, 'type_text') else None,
                "address": row.address,
                "status": row.status,
                "registration_date": str(row.registration_date) if row.registration_date else None,
                "nace_section": row.nace_section,
                "nace_section_text": row.nace_section_text
            })
            
    return result_data

