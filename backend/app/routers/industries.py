from fastapi import APIRouter, Query
from sqlalchemy import text
from etl.loader import engine
import logging
import math

router = APIRouter()
logger = logging.getLogger(__name__)

def safe_float(value):
    """Convert to float, returning None for inf/nan/None values"""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isinf(f) or math.isnan(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

@router.get("/industries/{nace_section}")
def get_industry_companies(
    nace_section: str,
    sort_by: str = Query("turnover", regex="^(turnover|profit)$"),
    limit: int = Query(100, le=500)
):
    """
    Get companies in specific NACE industry section
    
    Args:
        nace_section: NACE section code (e.g., "62" for IT)
        sort_by: Sort by "turnover" or "profit" (default: turnover)
        limit: Max companies to return (default: 100, max: 500)
    """
    with engine.connect() as conn:
        # Get section information
        section_info = conn.execute(text("""
            SELECT nace_section_text, COUNT(*) as total
            FROM companies
            WHERE nace_section = :section
            GROUP BY nace_section_text
        """), {"section": nace_section}).fetchone()
        
        if not section_info:
            return {
                "section": nace_section,
                "section_name": None,
                "total_companies": 0,
                "companies": []
            }
        
        
        # Build sort column - use CASE statement for safety
        # Get companies
        companies = conn.execute(text("""
            SELECT 
                c.regcode,
                c.name,
                c.nace_section,
                c.nace_section_text,
                c.employee_count,
                c.company_size_badge,
                c.pvn_number,
                c.is_pvn_payer,
                f.turnover,
                f.profit,
                f.employees as fin_employees,
                f.year,
                CASE WHEN :sort_by = 'turnover' THEN f.turnover ELSE f.profit END as sort_value
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) f ON true
            WHERE c.nace_section = :section
              AND CASE WHEN :sort_by = 'turnover' THEN f.turnover ELSE f.profit END IS NOT NULL
            ORDER BY sort_value DESC
            LIMIT :limit
        """), {"section": nace_section, "limit": limit, "sort_by": sort_by}).fetchall()
        
        return {
            "section": nace_section,
            "section_name": section_info[0] if section_info else None,
            "total_companies": section_info[1] if section_info else 0,
            "sort_by": sort_by,
            "companies": [
                {
                    "rank": idx + 1,
                    "regcode": c[0],
                    "name": c[1],
                    "turnover": safe_float(c[8]),
                    "profit": safe_float(c[9]),
                    "employees": c[4] or c[10],
                    "year": c[11],
                    "company_size": c[5],
                    "pvn_number": c[6],
                    "is_pvn_payer": c[7] or False
                }
                for idx, c in enumerate(companies)
            ]
        }

@router.get("/top100")
def get_top_100(
    sort_by: str = Query("turnover", regex="^(turnover|profit)$")
):
    """
    Get TOP 100 companies across all industries
    
    Args:
        sort_by: Sort by "turnover" or "profit" (default: turnover)
    """
    try:
        with engine.connect() as conn:
            companies = conn.execute(text("""
                SELECT 
                    c.regcode,
                    c.name,
                    c.nace_section,
                    c.nace_section_text,
                    c.employee_count,
                    c.company_size_badge,
                    c.pvn_number,
                    c.is_pvn_payer,
                    f.turnover,
                    f.profit,
                    f.employees as fin_employees,
                    f.year,
                    CASE WHEN :sort_by = 'turnover' THEN f.turnover ELSE f.profit END as sort_value
                FROM companies c
                LEFT JOIN LATERAL (
                    SELECT turnover, profit, employees, year
                    FROM financial_reports
                    WHERE company_regcode = c.regcode
                      AND turnover IS NOT NULL 
                      AND turnover > 0
                      AND turnover < 1e15
                    ORDER BY year DESC
                    LIMIT 1
                ) f ON true
                WHERE f.turnover IS NOT NULL
                  AND f.turnover > 0
                  AND f.turnover < 1e15
                ORDER BY sort_value DESC
                LIMIT 100
            """), {"sort_by": sort_by}).fetchall()
            
            result_companies = []
            for idx, c in enumerate(companies):
                try:
                    result_companies.append({
                        "rank": idx + 1,
                        "regcode": c[0],
                        "name": c[1],
                        "industry": c[3],
                        "turnover": safe_float(c[8]),
                        "profit": safe_float(c[9]),
                        "employees": c[4] or c[10],
                        "year": c[11],
                        "company_size": c[5],
                        "pvn_number": c[6],
                        "is_pvn_payer": bool(c[7]) if c[7] is not None else False
                    })
                except Exception as row_error:
                    logger.error(f"Error processing row {idx}: {row_error}, data: {c}")
                    continue
            
            return {
                "sort_by": sort_by,
                "total": len(result_companies),
                "companies": result_companies
            }
    except Exception as e:
        logger.error(f"TOP 100 query error: {e}")
        raise
