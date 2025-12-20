from fastapi import APIRouter, Query
from sqlalchemy import text
from etl.loader import engine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

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
                    "turnover": float(c[8]) if c[8] else None,
                    "profit": float(c[9]) if c[9] else None,
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
                ORDER BY year DESC
                LIMIT 1
            ) f ON true
            WHERE CASE WHEN :sort_by = 'turnover' THEN f.turnover ELSE f.profit END IS NOT NULL
            ORDER BY sort_value DESC
            LIMIT 100
        """), {"sort_by": sort_by}).fetchall()
        
        return {
            "sort_by": sort_by,
            "total": 100,
            "companies": [
                {
                    "rank": idx + 1,
                    "regcode": c[0],
                    "name": c[1],
                    "industry": c[3],
                    "turnover": float(c[10]) if c[10] else None,
                    "profit": float(c[11]) if c[11] else None,
                    "employees": c[4] or c[12],
                    "year": c[13],
                    "company_size": c[5],
                    "pvn_number": c[6],
                    "is_pvn_payer": c[7] or False
                }
                for idx, c in enumerate(companies)
            ]
        }
