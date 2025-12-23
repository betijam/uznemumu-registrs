from fastapi import APIRouter, Query, Response
from sqlalchemy import text
from etl.loader import engine
import logging
import math

router = APIRouter()
logger = logging.getLogger(__name__)

# NACE Section mappings (Level 1 codes A-U)
NACE_SECTIONS = {
    "A": {"name": "Lauksaimniecība un Mežsaimniecība", "icon": "🌾"},
    "B": {"name": "Ieguves Rūpniecība", "icon": "⛏️"},
    "C": {"name": "Apstrādes Rūpniecība", "icon": "🏭"},
    "D": {"name": "Elektroenerģija un Gāze", "icon": "⚡"},
    "E": {"name": "Ūdensapgāde un Atkritumi", "icon": "💧"},
    "F": {"name": "Būvniecība", "icon": "🏗️"},
    "G": {"name": "Tirdzniecība (Vairum/Mazum)", "icon": "🛒"},
    "H": {"name": "Transports un Uzglabāšana", "icon": "🚚"},
    "I": {"name": "Izmitināšana un Ēdināšana", "icon": "🏨"},
    "J": {"name": "Informācijas un Komunikācijas pak.", "icon": "💻"},
    "K": {"name": "Finanšu un Apdrošināšanas pak.", "icon": "🏦"},
    "L": {"name": "Nekustamais Īpašums", "icon": "🏠"},
    "M": {"name": "Profesionālie un Zinātniskie pak.", "icon": "🔬"},
    "N": {"name": "Administratīvie un Atbalsta pak.", "icon": "📋"},
    "O": {"name": "Valsts Pārvalde un Aizsardzība", "icon": "🏛️"},
    "P": {"name": "Izglītība", "icon": "🎓"},
    "Q": {"name": "Veselība un Sociālā Aprūpe", "icon": "🏥"},
    "R": {"name": "Māksla un Izklaide", "icon": "🎭"},
    "S": {"name": "Citi Pakalpojumi", "icon": "🔧"},
    "T": {"name": "Mājsaimniecības", "icon": "🏡"},
    "U": {"name": "Eksteritoriālās Organizācijas", "icon": "🌐"},
}

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

def safe_int(value):
    """Convert to int, returning None for invalid values"""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def format_large_number(value):
    """Format large numbers for display (e.g., 84.5 Md €)"""
    if value is None:
        return None
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f} Md €"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M€"
    if value >= 1_000:
        return f"{value / 1_000:.0f} k€"
    return f"{value:.0f} €"


# ============================================================================
# INDUSTRIES OVERVIEW ENDPOINT
# ============================================================================

@router.get("/industries/overview")
def get_industries_overview(response: Response):
    """
    Get macro-level industry analytics for the overview dashboard.
    Returns: macro KPIs, top lists (growth, salary, turnover), and all NACE sections.
    """
    response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        # Check if materialized table exists and has data
        try:
            stats_count = conn.execute(text(
                "SELECT COUNT(*) FROM industry_stats_materialized"
            )).scalar()
        except Exception:
            stats_count = 0
        
        # If materialized table is empty, compute on-the-fly (slower but works)
        if stats_count == 0:
            return _compute_overview_on_the_fly(conn)
        
        # Use pre-computed data from materialized table
        return _get_overview_from_cache(conn)


def _get_overview_from_cache(conn):
    """Get overview data from pre-computed materialized table"""
    
    # 1. Macro KPIs (national totals)
    macro = conn.execute(text("""
        SELECT 
            SUM(total_turnover) as total_turnover,
            SUM(total_profit) as total_profit,
            SUM(employee_count) as total_employees,
            ROUND(AVG(avg_gross_salary)) as avg_salary,
            MAX(data_year) as data_year
        FROM industry_stats_materialized
        WHERE nace_level = 1
        AND nace_code != '00'
        AND nace_name NOT ILIKE '%Cita nozare%'
    """)).fetchone()
    
    # Get previous year for trends
    prev_year = conn.execute(text("""
        SELECT 
            SUM(f.turnover) as prev_turnover,
            SUM(f.employees) as prev_employees
        FROM financial_reports f
        WHERE f.year = (SELECT MAX(year) - 1 FROM financial_reports)
    """)).fetchone()
    
    turnover_growth = None
    try:
        curr_turnover = safe_float(macro.total_turnover) or 0
        prev_turnover = safe_float(prev_year.prev_turnover) or 0
        if curr_turnover > 0 and prev_turnover > 0:
            turnover_growth = round(((curr_turnover - prev_turnover) / prev_turnover) * 100, 1)
    except Exception:
        turnover_growth = None
    
    employee_change = None
    try:
        curr_employees = safe_float(macro.total_employees) or 0
        prev_employees = safe_float(prev_year.prev_employees) or 0
        if curr_employees > 0 and prev_employees > 0:
            employee_change = round(((curr_employees - prev_employees) / prev_employees) * 100, 1)
    except Exception:
        employee_change = None
    
    # 2. Top Growth (by turnover growth %)
    top_growth = conn.execute(text("""
        SELECT nace_code, nace_name, turnover_growth
        FROM industry_stats_materialized
        WHERE nace_level = 1 
        AND turnover_growth IS NOT NULL
        AND nace_code != '00'
        AND nace_name NOT ILIKE '%Cita nozare%'
        ORDER BY turnover_growth DESC
        LIMIT 3
    """)).fetchall()
    
    # 3. Top Salary (by avg gross salary)
    top_salary = conn.execute(text("""
        SELECT nace_code, nace_name, avg_gross_salary
        SELECT nace_code, nace_name, avg_gross_salary
        FROM industry_stats_materialized
        WHERE nace_level = 1 
        AND avg_gross_salary IS NOT NULL
        AND nace_code != '00'
        AND nace_name NOT ILIKE '%Cita nozare%'
        ORDER BY avg_gross_salary DESC
        LIMIT 3
    """)).fetchall()
    
    # 4. Top Turnover (by absolute turnover)
    top_turnover = conn.execute(text("""
        SELECT nace_code, nace_name, total_turnover
        SELECT nace_code, nace_name, total_turnover
        FROM industry_stats_materialized
        WHERE nace_level = 1 
        AND total_turnover IS NOT NULL
        AND nace_code != '00'
        AND nace_name NOT ILIKE '%Cita nozare%'
        ORDER BY total_turnover DESC
        LIMIT 3
    """)).fetchall()
    
    # 5. All sections (for grid)
    sections = conn.execute(text("""
        SELECT 
            nace_code, nace_name, 
            total_turnover, turnover_growth, 
            avg_gross_salary, active_companies
        FROM industry_stats_materialized
        WHERE nace_level = 1
        AND nace_code != '00'
        AND nace_name NOT ILIKE '%Cita nozare%'
        ORDER BY nace_code
    """)).fetchall()
    
    return {
        "macro": {
            "total_turnover": safe_float(macro.total_turnover),
            "total_turnover_formatted": format_large_number(macro.total_turnover),
            "turnover_growth": turnover_growth,
            "total_employees": safe_int(macro.total_employees),
            "employee_change": employee_change,
            "avg_salary": safe_int(macro.avg_salary),
            "total_profit": safe_float(macro.total_profit),
            "total_profit_formatted": format_large_number(macro.total_profit),
            "data_year": macro.data_year
        },
        "top_growth": [
            {"nace_code": r.nace_code, "name": r.nace_name, "growth_percent": safe_float(r.turnover_growth)}
            for r in top_growth
        ],
        "top_salary": [
            {"nace_code": r.nace_code, "name": r.nace_name, "avg_salary": safe_int(r.avg_gross_salary)}
            for r in top_salary
        ],
        "top_turnover": [
            {"nace_code": r.nace_code, "name": r.nace_name, "turnover": safe_float(r.total_turnover), "turnover_formatted": format_large_number(r.total_turnover)}
            for r in top_turnover
        ],
        "sections": [
            {
                "nace_code": r.nace_code,
                "name": NACE_SECTIONS.get(r.nace_code, {}).get("name", r.nace_name),
                "icon": NACE_SECTIONS.get(r.nace_code, {}).get("icon", "📊"),
                "turnover": safe_float(r.total_turnover),
                "turnover_formatted": format_large_number(r.total_turnover),
                "turnover_growth": safe_float(r.turnover_growth),
                "avg_salary": safe_int(r.avg_gross_salary),
                "companies": safe_int(r.active_companies)
            }
            for r in sections
        ]
    }


def _compute_overview_on_the_fly(conn):
    """Fallback: compute overview without materialized table (slower)"""
    logger.warning("Computing industry overview on-the-fly - consider running migration SQL")
    
    # Get section stats directly from source tables
    sections_data = conn.execute(text("""
        WITH section_stats AS (
            SELECT 
                c.nace_section as nace_code,
                MAX(c.nace_section_text) as nace_name,
                SUM(f.turnover) as total_turnover,
                SUM(f.profit) as total_profit,
                SUM(f.employees) as employee_count,
                COUNT(DISTINCT c.regcode) as active_companies
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) f ON true
            WHERE c.nace_section IS NOT NULL AND c.status = 'active'
            GROUP BY c.nace_section
        ),
        section_tax AS (
            SELECT 
                c.nace_section,
                SUM(t.social_tax_vsaoi) as total_vsaoi,
                SUM(t.avg_employees) as tax_employees
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT social_tax_vsaoi, avg_employees
                FROM tax_payments WHERE company_regcode = c.regcode
                ORDER BY year DESC LIMIT 1
            ) t ON true
            WHERE c.nace_section IS NOT NULL
            GROUP BY c.nace_section
        )
        SELECT 
            s.nace_code, s.nace_name, s.total_turnover, s.total_profit,
            s.employee_count, s.active_companies,
            CASE WHEN t.tax_employees > 0 
                THEN ROUND((t.total_vsaoi / 0.3409 / t.tax_employees / 12)::NUMERIC)
                ELSE NULL 
            END as avg_salary
        FROM section_stats s
        LEFT JOIN section_tax t ON t.nace_section = s.nace_code
        ORDER BY s.nace_code
    """)).fetchall()
    
    # Calculate totals
    total_turnover = sum(safe_float(r.total_turnover) or 0 for r in sections_data)
    total_profit = sum(safe_float(r.total_profit) or 0 for r in sections_data)
    total_employees = sum(safe_int(r.employee_count) or 0 for r in sections_data)
    salaries = [safe_int(r.avg_salary) for r in sections_data if r.avg_salary]
    avg_salary = int(sum(salaries) / len(salaries)) if salaries else None
    
    return {
        "macro": {
            "total_turnover": total_turnover,
            "total_turnover_formatted": format_large_number(total_turnover),
            "turnover_growth": None,
            "total_employees": total_employees,
            "employee_change": None,
            "avg_salary": avg_salary,
            "total_profit": total_profit,
            "total_profit_formatted": format_large_number(total_profit),
            "data_year": 2023
        },
        "top_growth": [],
        "top_salary": sorted(
            [{"nace_code": r.nace_code, "name": r.nace_name, "avg_salary": safe_int(r.avg_salary)} 
             for r in sections_data if r.avg_salary],
            key=lambda x: x["avg_salary"] or 0, reverse=True
        )[:3],
        "top_turnover": sorted(
            [{"nace_code": r.nace_code, "name": r.nace_name, "turnover": safe_float(r.total_turnover), "turnover_formatted": format_large_number(r.total_turnover)} 
             for r in sections_data if r.total_turnover],
            key=lambda x: x["turnover"] or 0, reverse=True
        )[:3],
        "sections": [
            {
                "nace_code": r.nace_code,
                "name": NACE_SECTIONS.get(r.nace_code, {}).get("name", r.nace_name),
                "icon": NACE_SECTIONS.get(r.nace_code, {}).get("icon", "📊"),
                "turnover": safe_float(r.total_turnover),
                "turnover_formatted": format_large_number(r.total_turnover),
                "turnover_growth": None,
                "avg_salary": safe_int(r.avg_salary),
                "companies": safe_int(r.active_companies)
            }
            for r in sections_data
        ]
    }


# ============================================================================
# INDUSTRY SEARCH ENDPOINT
# ============================================================================

@router.get("/industries/search")
def search_industries(q: str = Query(..., min_length=1), limit: int = Query(10, le=50)):
    """
    Search NACE codes and names for autocomplete.
    Returns matching industries by code or name.
    """
    with engine.connect() as conn:
        # Search in NACE sections from companies table
        results = conn.execute(text("""
            SELECT DISTINCT 
                nace_section as code,
                nace_section_text as name,
                1 as level
            FROM companies
            WHERE nace_section IS NOT NULL
              AND (
                  LOWER(nace_section) LIKE LOWER(:q) || '%'
                  OR LOWER(nace_section_text) LIKE '%' || LOWER(:q) || '%'
              )
            ORDER BY nace_section
            LIMIT :limit
        """), {"q": q, "limit": limit}).fetchall()
        
        return {
            "query": q,
            "results": [
                {
                    "code": r.code,
                    "name": NACE_SECTIONS.get(r.code, {}).get("name", r.name),
                    "icon": NACE_SECTIONS.get(r.code, {}).get("icon", "📊"),
                    "level": r.level
                }
                for r in results
            ]
        }


# ============================================================================
# DETAILED INDUSTRY ENDPOINT (ENHANCED)
# ============================================================================

@router.get("/industries/{nace_code}/detail")
def get_industry_detail(
    nace_code: str,
    year: int = Query(None, description="Year for data (default: latest)"),
    response: Response = None
):
    """
    Get detailed industry analytics for the industry detail page.
    Returns: KPIs, TOP 5 leaders, salary comparison, tax burden, market concentration.
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        # Determine data year
        if year is None:
            year_result = conn.execute(text("SELECT MAX(year) FROM financial_reports")).scalar()
            year = year_result or 2023
        
        # Get section metadata
        section_meta = conn.execute(text("""
            SELECT 
                nace_section_text as name,
                COUNT(DISTINCT regcode) as total_companies
            FROM companies
            WHERE nace_section = :code
            GROUP BY nace_section_text
        """), {"code": nace_code}).fetchone()
        
        if not section_meta:
            return {
                "nace_code": nace_code,
                "error": "Industry not found",
                "meta": None
            }
        
        # 1. KPIs for this industry (current year)
        kpi_data = conn.execute(text("""
            SELECT 
                SUM(f.turnover) as total_turnover,
                SUM(f.profit) as total_profit,
                SUM(f.employees) as employee_count,
                COUNT(DISTINCT c.regcode) as active_companies
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees
                FROM financial_reports
                WHERE company_regcode = c.regcode AND year = :year
            ) f ON true
            WHERE c.nace_section = :code
              AND c.status = 'active'
        """), {"code": nace_code, "year": year}).fetchone()
        
        # Previous year for growth calculation
        prev_kpi = conn.execute(text("""
            SELECT 
                SUM(f.turnover) as prev_turnover,
                SUM(f.profit) as prev_profit
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit
                FROM financial_reports
                WHERE company_regcode = c.regcode AND year = :prev_year
            ) f ON true
            WHERE c.nace_section = :code
        """), {"code": nace_code, "prev_year": year - 1}).fetchone()
        
        # Calculate growth percentages
        turnover_growth = None
        if kpi_data.total_turnover and prev_kpi.prev_turnover and prev_kpi.prev_turnover > 0:
            turnover_growth = round(((kpi_data.total_turnover - prev_kpi.prev_turnover) / prev_kpi.prev_turnover) * 100, 1)
        
        profit_growth = None
        if kpi_data.total_profit and prev_kpi.prev_profit and prev_kpi.prev_profit > 0:
            profit_growth = round(((kpi_data.total_profit - prev_kpi.prev_profit) / prev_kpi.prev_profit) * 100, 1)
        
        # 2. Average Salary for this industry
        salary_data = conn.execute(text("""
            SELECT 
                SUM(t.social_tax_vsaoi) as total_vsaoi,
                SUM(t.avg_employees) as total_employees
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT social_tax_vsaoi, avg_employees
                FROM tax_payments
                WHERE company_regcode = c.regcode AND year = :year
            ) t ON true
            WHERE c.nace_section = :code
        """), {"code": nace_code, "year": year}).fetchone()
        
        industry_avg_salary = None
        try:
            vsaoi = safe_float(salary_data.total_vsaoi) or 0
            employees = safe_float(salary_data.total_employees) or 0
            if vsaoi > 0 and employees > 0:
                industry_avg_salary = round(vsaoi / 0.3409 / employees / 12)
        except Exception:
            industry_avg_salary = None
        
        # National average salary
        national_salary_data = conn.execute(text("""
            SELECT 
                SUM(social_tax_vsaoi) as total_vsaoi,
                SUM(avg_employees) as total_employees
            FROM tax_payments
            WHERE year = :year
        """), {"year": year}).fetchone()
        
        national_avg_salary = None
        try:
            nat_vsaoi = safe_float(national_salary_data.total_vsaoi) or 0
            nat_employees = safe_float(national_salary_data.total_employees) or 0
            if nat_vsaoi > 0 and nat_employees > 0:
                national_avg_salary = round(nat_vsaoi / 0.3409 / nat_employees / 12)
        except Exception:
            national_avg_salary = None
        
        salary_ratio = None
        if industry_avg_salary and national_avg_salary and national_avg_salary > 0:
            salary_ratio = round(industry_avg_salary / national_avg_salary, 1)
        
        # 3. TOP 5 Leaders
        leaders = conn.execute(text("""
            SELECT 
                c.regcode,
                c.name,
                f.turnover,
                f.profit,
                f.employees
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees
                FROM financial_reports
                WHERE company_regcode = c.regcode AND year = :year
                  AND turnover IS NOT NULL AND turnover > 0
            ) f ON true
            WHERE c.nace_section = :code
              AND c.status = 'active'
              AND f.turnover IS NOT NULL
            ORDER BY f.turnover DESC
            LIMIT 5
        """), {"code": nace_code, "year": year}).fetchall()
        
        # 4. Tax Burden
        tax_data = conn.execute(text("""
            SELECT 
                SUM(t.total_tax_paid) as total_tax,
                SUM(f.turnover) as total_turnover
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT total_tax_paid FROM tax_payments
                WHERE company_regcode = c.regcode AND year = :year
            ) t ON true
            LEFT JOIN LATERAL (
                SELECT turnover FROM financial_reports
                WHERE company_regcode = c.regcode AND year = :year
            ) f ON true
            WHERE c.nace_section = :code
        """), {"code": nace_code, "year": year}).fetchone()
        
        tax_burden = None
        if tax_data.total_tax and tax_data.total_turnover and tax_data.total_turnover > 0:
            tax_burden = round((tax_data.total_tax / tax_data.total_turnover) * 100, 1)
        
        # 5. Market Concentration (TOP 5 share)
        top5_turnover = sum(safe_float(l.turnover) or 0 for l in leaders)
        total_turnover = safe_float(kpi_data.total_turnover) or 0
        top5_concentration = None
        concentration_level = None
        if top5_turnover and total_turnover > 0:
            top5_concentration = round((top5_turnover / total_turnover) * 100, 1)
            if top5_concentration >= 60:
                concentration_level = "Augsta"
            elif top5_concentration >= 40:
                concentration_level = "Vidēja"
            else:
                concentration_level = "Zema"
        
        # 6. New companies this year
        new_companies = conn.execute(text("""
            SELECT COUNT(*) FROM companies
            WHERE nace_section = :code
              AND EXTRACT(YEAR FROM registration_date) = :year
        """), {"code": nace_code, "year": year}).scalar() or 0
        
        return {
            "nace_code": nace_code,
            "data_year": year,
            "available_years": [2021, 2022, 2023],  # Can be made dynamic
            "meta": {
                "name": NACE_SECTIONS.get(nace_code, {}).get("name", section_meta.name),
                "icon": NACE_SECTIONS.get(nace_code, {}).get("icon", "📊"),
                "description": f"NACE sekcija {nace_code}"
            },
            "kpi": {
                "total_turnover": safe_float(kpi_data.total_turnover),
                "total_turnover_formatted": format_large_number(kpi_data.total_turnover),
                "turnover_growth": turnover_growth,
                "total_profit": safe_float(kpi_data.total_profit),
                "total_profit_formatted": format_large_number(kpi_data.total_profit),
                "profit_growth": profit_growth,
                "active_companies": safe_int(kpi_data.active_companies),
                "new_companies": new_companies,
                "avg_salary": industry_avg_salary,
                "salary_ratio": salary_ratio
            },
            "leaders": [
                {
                    "rank": idx + 1,
                    "regcode": l.regcode,
                    "name": l.name,
                    "turnover": safe_float(l.turnover),
                    "turnover_formatted": format_large_number(l.turnover),
                    "profit": safe_float(l.profit),
                    "profit_formatted": format_large_number(l.profit),
                    "employees": safe_int(l.employees)
                }
                for idx, l in enumerate(leaders)
            ],
            "salary_analytics": {
                "industry_avg": industry_avg_salary,
                "national_avg": national_avg_salary,
                "ratio": salary_ratio,
                "ratio_text": f"{salary_ratio}x pret vidējo" if salary_ratio else None
            },
            "tax_burden": {
                "percent": tax_burden,
                "description": "No apgrozījuma tiek samaksāts nodokļos"
            },
            "market_concentration": {
                "top5_percent": top5_concentration,
                "level": concentration_level,
                "description": "TOP 5 uzņēmumu tirgus daļa"
            }
        }


# ============================================================================
# EXISTING INDUSTRY COMPANIES ENDPOINT (kept for backwards compat)
# ============================================================================

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
