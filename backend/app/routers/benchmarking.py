"""
Benchmarking & competitor endpoints for companies.
Adds industry comparison and competitor analysis features.
"""
from fastapi import APIRouter
from sqlalchemy import text
from etl.loader import engine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/companies/{regcode}/benchmark")
def get_company_benchmark(regcode: int):
    """
    Calculate company's position within its industry.
    Returns percentile ranks and industry averages.
    """
    with engine.connect() as conn:
        # Get company info
        company = conn.execute(
            text("SELECT nace_section, nace_section_text, employee_count FROM companies WHERE regcode = :r"),
            {"r": regcode}
        ).fetchone()
        
        if not company or not company.nace_section or company.nace_section == '00':
            return {
                "error": "Company not found or has no industry classification", 
                "has_data": False
            }
        
        nace_section = company.nace_section
        
        # Get latest financial data for this company
        company_fin = conn.execute(text("""
            SELECT turnover, profit, employees
            FROM financial_reports
            WHERE company_regcode = :r
            ORDER BY year DESC LIMIT 1
        """), {"r": regcode}).fetchone()
        
        if not company_fin:
            return {"error": "No financial data available", "has_data": False}
        
        company_turnover = float(company_fin.turnover) if company_fin.turnover else 0
        company_employees = company_fin.employees or company.employee_count or 0
        
        # Get industry statistics
        industry_stats = conn.execute(text("""
            SELECT 
                COUNT(*) as total_companies,
                AVG(fr.turnover) as avg_turnover,
                AVG(fr.employees) as avg_employees,
                AVG(c.employee_count) as avg_vid_employees
            FROM companies c
            LEFT JOIN financial_reports fr ON fr.company_regcode = c.regcode 
                AND fr.year = (SELECT MAX(year) FROM financial_reports WHERE company_regcode = c.regcode)
            WHERE c.nace_section = :section
                AND c.nace_section != '00'
        """), {"section": nace_section}).fetchone()
        
        # Calculate turnover percentile
        if company_turnover > 0:
            turnover_rank = conn.execute(text("""
                SELECT COUNT(*) + 1 as rank
                FROM financial_reports fr
                JOIN companies c ON c.regcode = fr.company_regcode
                WHERE c.nace_section = :section
                    AND fr.year = (SELECT MAX(year) FROM financial_reports WHERE company_regcode = c.regcode)
                    AND fr.turnover > :turnover
            """), {"section": nace_section, "turnover": company_turnover}).scalar()
            
            total_with_turnover = conn.execute(text("""
                SELECT COUNT(DISTINCT c.regcode)
                FROM companies c
                JOIN financial_reports fr ON fr.company_regcode = c.regcode
                WHERE c.nace_section = :section
                    AND fr.turnover IS NOT NULL
                    AND fr.turnover > 0
            """), {"section": nace_section}).scalar()
            
            turnover_percentile = round((1 - (turnover_rank / total_with_turnover)) * 100, 1) if total_with_turnover > 0 else None
        else:
            turnover_percentile = None
        
        # Calculate employee percentile
        if company_employees > 0:
            employee_rank = conn.execute(text("""
                SELECT COUNT(*) + 1 as rank
                FROM companies c
                WHERE c.nace_section = :section
                    AND COALESCE(c.employee_count, 0) > :employees
            """), {"section": nace_section, "employees": company_employees}).scalar()
            
            total_with_employees = conn.execute(text("""
                SELECT COUNT(*)
                FROM companies c
                WHERE c.nace_section = :section
                    AND COALESCE(c.employee_count, 0) > 0
            """), {"section": nace_section}).scalar()
            
            employee_percentile = round((1 - (employee_rank / total_with_employees)) * 100, 1) if total_with_employees > 0 else None
        else:
            employee_percentile = None
        
        return {
            "has_data": True,
            "industry": {
                "section": nace_section,
                "name": company.nace_section_text,
                "total_companies": industry_stats.total_companies
            },
            "company": {
                "turnover": company_turnover,
                "employees": company_employees
            },
            "percentiles": {
                "turnover": turnover_percentile,
                "employees": employee_percentile
            },
            "industry_averages": {
                "turnover": float(industry_stats.avg_turnover) if industry_stats.avg_turnover else None,
                "employees": float(industry_stats.avg_employees or industry_stats.avg_vid_employees or 0)
            }
        }


@router.get("/companies/{regcode}/competitors")
def get_top_competitors(regcode: int, limit: int = 5):
    """
    Find top competitors in the same industry.
    Matches by NACE section and similar size (employee count ±30%).
    """
    with engine.connect() as conn:
        # Get company info
        company = conn.execute(
            text("SELECT nace_code, nace_text, employee_count FROM companies WHERE regcode = :r"),
            {"r": regcode}
        ).fetchone()
        
        if not company or not company.nace_code or len(company.nace_code) < 3:
            return []
        
        nace_prefix = company.nace_code[:3]
        employee_count = company.employee_count or 0
        
        # Calculate size range (±30%)
        min_employees = int(employee_count * 0.7) if employee_count > 0 else 0
        max_employees = int(employee_count * 1.3) if employee_count > 0 else 999999
        
        # Find competitors
        competitors = conn.execute(text("""
            SELECT 
                c.regcode,
                c.name,
                c.employee_count,
                c.nace_text,
                fr.turnover,
                fr.profit,
                fr.year
            FROM companies c
            LEFT JOIN financial_reports fr ON fr.company_regcode = c.regcode
                AND fr.year = (SELECT MAX(year) FROM financial_reports WHERE company_regcode = c.regcode)
            WHERE c.nace_code LIKE :nace_prefix
                AND c.regcode != :regcode
                AND (:min_emp = 0 OR c.employee_count BETWEEN :min_emp AND :max_emp)
            ORDER BY fr.turnover DESC NULLS LAST, c.employee_count DESC
            LIMIT :limit
        """), {
            "nace_prefix": f"{nace_prefix}%",
            "regcode": regcode,
            "min_emp": min_employees,
            "max_emp": max_employees,
            "limit": limit
        }).fetchall()
        
        return [
            {
                "regcode": c.regcode,
                "name": c.name,
                "employee_count": c.employee_count,
                "nace_text": c.nace_text,
                "turnover": float(c.turnover) if c.turnover else None,
                "profit": float(c.profit) if c.profit else None,
                "year": c.year
            }
            for c in competitors
        ]


@router.get("/industries")
def get_industry_statistics():
    """
    Get statistics for all industries.
    Returns company count, total employees, and average turnover per industry section.
    """
    with engine.connect() as conn:
        industries = conn.execute(text("""
            SELECT 
                c.nace_section,
                c.nace_section_text,
                COUNT(DISTINCT c.regcode) as company_count,
                SUM(c.employee_count) as total_employees,
                AVG(fr.turnover) as avg_turnover
            FROM companies c
            LEFT JOIN financial_reports fr ON fr.company_regcode = c.regcode
                AND fr.year = (SELECT MAX(year) FROM financial_reports WHERE company_regcode = c.regcode)
            WHERE c.nace_section IS NOT NULL 
                AND c.nace_section != '00'
            GROUP BY c.nace_section, c.nace_section_text
            HAVING COUNT(DISTINCT c.regcode) > 10
            ORDER BY company_count DESC
        """)).fetchall()
        
        return [
            {
                "section": i.nace_section,
                "name": i.nace_section_text,
                "company_count": i.company_count,
                "total_employees": int(i.total_employees) if i.total_employees else 0,
                "avg_turnover": float(i.avg_turnover) if i.avg_turnover else None
            }
            for i in industries
        ]
