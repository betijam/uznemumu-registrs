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
        
        # Build sort column
        sort_column = "f.turnover" if sort_by == "turnover" else "f.profit"
        
        # Get companies
        companies = conn.execute(text(f"""
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
                f.year
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) f ON true
            WHERE c.nace_section = :section
              AND {sort_column} IS NOT NULL
            ORDER BY {sort_column} DESC
            LIMIT :limit
        """), {"section": nace_section, "limit": limit}).fetchall()
        
        return {
            "section": nace_section,
            "section_name": section_info.nace_section_text,
            "total_companies": section_info.total,
            "sort_by": sort_by,
            "companies": [
                {
                    "rank": idx + 1,
                    "regcode": c.regcode,
                    "name": c.name,
                    "turnover": float(c.turnover) if c.turnover else None,
                    "profit": float(c.profit) if c.profit else None,
                    "employees": c.employee_count or c.fin_employees,
                    "year": c.year,
                    "company_size": c.company_size_badge,
                    "pvn_number": c.pvn_number,
                    "is_pvn_payer": c.is_pvn_payer or False
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
        sort_column = "f.turnover" if sort_by == "turnover" else "f.profit"
        
        companies = conn.execute(text(f"""
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
                f.year
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) f ON true
            WHERE {sort_column} IS NOT NULL
            ORDER BY {sort_column} DESC
            LIMIT 100
        """)).fetchall()
        
        return {
            "sort_by": sort_by,
            "total": 100,
            "companies": [
                {
                    "rank": idx + 1,
                    "regcode": c.regcode,
                    "name": c.name,
                    "industry": c.nace_section_text,
                    "turnover": float(c.turnover) if c.turnover else None,
                    "profit": float(c.profit) if c.profit else None,
                    "employees": c.employee_count or c.fin_employees,
                    "year": c.year,
                    "company_size": c.company_size_badge,
                    "pvn_number": c.pvn_number,
                    "is_pvn_payer": c.is_pvn_payer or False
                }
                for idx, c in enumerate(companies)
            ]
        }
