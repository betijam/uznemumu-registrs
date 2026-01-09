from fastapi import APIRouter, Query, Response
from sqlalchemy import text
from app.core.database import engine
from app.nace_names import NACE_DIVISIONS, get_nace_name
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
            {"nace_code": r.nace_code, "name": NACE_DIVISIONS.get(r.nace_code, r.nace_name), "growth_percent": safe_float(r.turnover_growth)}
            for r in top_growth
        ],
        "top_salary": [
            {"nace_code": r.nace_code, "name": NACE_DIVISIONS.get(r.nace_code, r.nace_name), "avg_salary": safe_int(r.avg_gross_salary)}
            for r in top_salary
        ],
        "top_turnover": [
            {"nace_code": r.nace_code, "name": NACE_DIVISIONS.get(r.nace_code, r.nace_name), "turnover": safe_float(r.total_turnover), "turnover_formatted": format_large_number(r.total_turnover)}
            for r in top_turnover
        ],
        "sections": [
            {
                "nace_code": r.nace_code,
                # Use NACE_DIVISIONS for proper names, fallback to NACE_SECTIONS (letters), then DB name
                "name": NACE_DIVISIONS.get(r.nace_code) or NACE_SECTIONS.get(r.nace_code, {}).get("name") or r.nace_name,
                "icon": NACE_SECTIONS.get(r.nace_code, {}).get("icon", "🏭"),
                "turnover": safe_float(r.total_turnover),
                "turnover_formatted": format_large_number(r.total_turnover),
                "turnover_growth": safe_float(r.turnover_growth),
                "avg_salary": safe_int(r.avg_gross_salary),
                "companies": safe_int(r.active_companies)
            }
            for r in sections
            if r.nace_code not in ('00', None) and (not r.nace_name or 'cita nozare' not in r.nace_name.lower())
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

    conn = engine.connect()
    
    # helper for percentage
    def calc_growth(cur, prev):
        if cur and prev and prev > 0:
            return round(((cur - prev) / prev) * 100, 1)
        return None

    try:
        # Determine if this is a section code (2 digits) or sub-industry code (4 digits)
        # 2-digit codes use nace_section, 4-digit codes use nace_code LIKE
        is_section = len(nace_code) <= 2
        
        if is_section:
            nace_filter = "c.nace_section = :code"
            nace_param = nace_code
        else:
            nace_filter = "LEFT(c.nace_code, :code_len) = :code"
            nace_param = nace_code
        
        code_len = len(nace_code)
        
        # Year selection: validate that selected year has sufficient data for this industry
        # Find the best year with at least 5 companies reporting data (lower threshold for sub-industries)
        min_companies = 10 if is_section else 3
        
        best_year_query = f"""
            SELECT f.year, COUNT(*) as cnt
            FROM financial_reports f
            JOIN companies c ON c.regcode = f.company_regcode
            WHERE {nace_filter} AND f.turnover IS NOT NULL
            GROUP BY f.year
            HAVING COUNT(*) >= :min_companies
            ORDER BY f.year DESC
            LIMIT 1
        """
        best_year_row = conn.execute(text(best_year_query), {
            "code": nace_param, 
            "code_len": code_len, 
            "min_companies": min_companies
        }).fetchone()
        
        best_year = best_year_row.year if best_year_row else 2024
        
        # If no year specified or specified year has insufficient data, use best year
        if not year:
            year = best_year
        else:
            # Check if the requested year has enough data
            year_check_query = f"""
                SELECT COUNT(*) as cnt
                FROM financial_reports f
                JOIN companies c ON c.regcode = f.company_regcode
                WHERE {nace_filter} AND f.year = :year AND f.turnover IS NOT NULL
            """
            year_check = conn.execute(text(year_check_query), {
                "code": nace_param, 
                "code_len": code_len, 
                "year": year
            }).fetchone()
            
            # If requested year has very few companies, use best year instead
            if not year_check or year_check.cnt < min_companies:
                logger.info(f"Year {year} has insufficient data ({year_check.cnt if year_check else 0} companies), falling back to {best_year}")
                year = best_year

        # 1. Basic Info & NACE Name - prioritize NACE_DIVISIONS dictionary
        # This ensures proper names even when DB has "Cita nozare"
        nace_name = NACE_DIVISIONS.get(nace_code)
        
        # Map 2-digit codes to sections for icons
        NACE_CODE_TO_SECTION = {
            "01": "A", "02": "A", "03": "A",  # Agriculture
            "05": "B", "06": "B", "07": "B", "08": "B", "09": "B",  # Mining
            "10": "C", "11": "C", "12": "C", "13": "C", "14": "C", "15": "C", "16": "C", "17": "C", "18": "C",
            "19": "C", "20": "C", "21": "C", "22": "C", "23": "C", "24": "C", "25": "C", "26": "C", "27": "C",
            "28": "C", "29": "C", "30": "C", "31": "C", "32": "C", "33": "C",  # Manufacturing
            "35": "D",  # Electricity
            "36": "E", "37": "E", "38": "E", "39": "E",  # Water/Waste
            "41": "F", "42": "F", "43": "F",  # Construction
            "45": "G", "46": "G", "47": "G",  # Trade
            "49": "H", "50": "H", "51": "H", "52": "H", "53": "H",  # Transport
            "55": "I", "56": "I",  # Hospitality
            "58": "J", "59": "J", "60": "J", "61": "J", "62": "J", "63": "J",  # IT/Media
            "64": "K", "65": "K", "66": "K",  # Finance
            "68": "L",  # Real Estate
            "69": "M", "70": "M", "71": "M", "72": "M", "73": "M", "74": "M", "75": "M",  # Professional
            "77": "N", "78": "N", "79": "N", "80": "N", "81": "N", "82": "N",  # Admin
            "84": "O",  # Public Admin
            "85": "P",  # Education
            "86": "Q", "87": "Q", "88": "Q",  # Health
            "90": "R", "91": "R", "92": "R", "93": "R",  # Arts
            "94": "S", "95": "S", "96": "S",  # Other Services
            "97": "T", "98": "T",  # Households
            "99": "U",  # Extraterritorial
        }
        
        # Get icon from section mapping
        section = NACE_CODE_TO_SECTION.get(nace_code[:2])
        if section and section in NACE_SECTIONS:
            nace_icon = NACE_SECTIONS[section]["icon"]
        elif nace_code in NACE_SECTIONS:
            nace_icon = NACE_SECTIONS[nace_code]["icon"]
        else:
            nace_icon = "🏭"
        
        # If no NACE name found in dictionary, try database
        if not nace_name:
            if is_section:
                # For 2-digit codes, check materialized view first
                nace_db = conn.execute(text("""
                    SELECT nace_name FROM industry_stats_materialized 
                    WHERE nace_code = :code AND nace_level = 1
                    LIMIT 1
                """), {"code": nace_code}).fetchone()
                
                if nace_db and nace_db.nace_name and 'cita nozare' not in nace_db.nace_name.lower():
                    nace_name = nace_db.nace_name
            else:
                # For 4-digit codes, get name from companies table
                nace_db = conn.execute(text("""
                    SELECT nace_text FROM companies 
                    WHERE LEFT(nace_code, :code_len) = :code 
                      AND nace_text IS NOT NULL 
                      AND nace_text NOT ILIKE '%nenoteikt%'
                    LIMIT 1
                """), {"code": nace_code, "code_len": len(nace_code)}).fetchone()
                
                if nace_db and nace_db.nace_text:
                    nace_name = nace_db.nace_text
            
            # Final fallback
            if not nace_name:
                nace_info = NACE_SECTIONS.get(nace_code)
                nace_name = nace_info["name"] if nace_info else f"Nozare {nace_code}"

        # 2. Main KPIs for Selected Year
        # We compute this dynamically from companies/financial_reports to be fresh
        # and consistent with the specific selected 'year'
        stats_query = f"""
            SELECT 
                SUM(f.turnover) as total_turnover,
                SUM(f.profit) as total_profit,
                SUM(f.employees) as total_employees,
                COUNT(DISTINCT c.regcode) as active_companies
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees
                FROM financial_reports
                WHERE company_regcode = c.regcode AND year = :year
                  AND turnover IS NOT NULL AND turnover < 1e15
            ) f ON true
            WHERE {nace_filter}
              AND c.status = 'active'
        """
        stats = conn.execute(text(stats_query), {"code": nace_param, "code_len": code_len, "year": year}).fetchone()

        # Previous Year for Growth
        prev_stats_query = f"""
            SELECT SUM(f.turnover) as total_turnover
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT turnover
                FROM financial_reports
                WHERE company_regcode = c.regcode AND year = :prev_year
                  AND turnover IS NOT NULL AND turnover < 1e15
            ) f ON true
            WHERE {nace_filter}
              AND c.status = 'active'
        """
        prev_stats = conn.execute(text(prev_stats_query), {"code": nace_param, "code_len": code_len, "prev_year": year - 1}).fetchone()

        # Salary Data (from tax_payments)
        salary_data_query = f"""
            SELECT 
                SUM(t.social_tax_vsaoi) as total_vsaoi,
                SUM(t.avg_employees) as total_employees
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT social_tax_vsaoi, avg_employees
                FROM tax_payments
                WHERE company_regcode = c.regcode AND year = :year
            ) t ON true
            WHERE {nace_filter}
        """
        salary_data = conn.execute(text(salary_data_query), {"code": nace_param, "code_len": code_len, "year": year}).fetchone()
        
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

        # 3. Market Share Base (Total Industry Turnover)
        total_industry_turnover = safe_float(stats.total_turnover) or 0

        # 4. TOP 5 Leaders with Market Share
        leaders_query = f"""
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
                  AND turnover IS NOT NULL AND turnover > 0 AND turnover < 1e15
            ) f ON true
            WHERE {nace_filter}
              AND c.status = 'active'
              AND f.turnover IS NOT NULL
            ORDER BY f.turnover DESC
            LIMIT 5
        """
        leaders = conn.execute(text(leaders_query), {"code": nace_param, "code_len": code_len, "year": year}).fetchall()

        leaders_data = []
        for l in leaders:
            t_val = safe_float(l.turnover) or 0
            market_share = 0
            if total_industry_turnover > 0:
                market_share = round((t_val / total_industry_turnover) * 100, 2)
            
            leaders_data.append({
                "regcode": l.regcode,
                "name": l.name,
                "turnover": t_val,
                "turnover_formatted": format_large_number(t_val),
                "profit": safe_float(l.profit),
                "profit_formatted": format_large_number(l.profit),
                "employees": l.employees,
                "market_share": market_share
            })
        
        # 5. Tax Burden
        tax_data_query = f"""
            SELECT 
                SUM(t.total_tax_paid) as total_tax
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT total_tax_paid FROM tax_payments
                WHERE company_regcode = c.regcode AND year = :year
            ) t ON true
            WHERE {nace_filter}
        """
        tax_data = conn.execute(text(tax_data_query), {"code": nace_param, "code_len": code_len, "year": year}).fetchone()
        
        tax_burden = None
        total_tax = safe_float(tax_data.total_tax) or 0
        if total_industry_turnover > 0:
            tax_burden = round((total_tax / total_industry_turnover) * 100, 2)

        # 6. Market Concentration (HHI proxy / Top 5 share)
        concentration_val = 0
        if leaders_data and total_industry_turnover > 0:
            top5_sum = sum(l['turnover'] for l in leaders_data)
            concentration_val = round((top5_sum / total_industry_turnover) * 100, 1)
        
        concentration_level = "Zema"
        if concentration_val > 40: concentration_level = "Vidēja"
        if concentration_val > 70: concentration_level = "Augsta"

        # 7. Financial History (Last 5 Years)
        # We want years: [year-4, year-3, year-2, year-1, year]
        start_year = year - 4
        history_query = f"""
            SELECT 
                f.year,
                SUM(f.turnover) as total_turnover,
                SUM(f.profit) as total_profit
            FROM companies c
            JOIN financial_reports f ON f.company_regcode = c.regcode
            WHERE {nace_filter}
              AND f.year BETWEEN :start_year AND :end_year
              AND f.turnover IS NOT NULL AND f.turnover < 1e15
            GROUP BY f.year
            ORDER BY f.year ASC
        """
        history_rows = conn.execute(text(history_query), {"code": nace_param, "code_len": code_len, "start_year": start_year, "end_year": year}).fetchall()

        history_data = [
            {
                "year": row.year,
                "turnover": safe_float(row.total_turnover),
                "profit": safe_float(row.total_profit)
            }
            for row in history_rows
        ]

        # 8. Sub-industry Breakdown (Level 4 NACE - 4-digit codes)
        # Only show sub-industries for section-level (2-digit) codes
        # For 4-digit codes, don't show sub-industries (they ARE the sub-industry)
        sub_industries = []
        if is_section:
            sub_industries_query = f"""
                SELECT 
                    LEFT(c.nace_code, 4) as sub_code,
                    MAX(c.nace_text) as sub_name_sample, 
                    SUM(f.turnover) as sub_turnover,
                    COUNT(DISTINCT c.regcode) as company_count
                FROM companies c
                LEFT JOIN LATERAL (
                     SELECT turnover FROM financial_reports 
                     WHERE company_regcode = c.regcode AND year = :year 
                       AND turnover IS NOT NULL AND turnover > 0 AND turnover < 1e15
                     ORDER BY year DESC LIMIT 1
                ) f ON true
                WHERE {nace_filter}
                  AND c.nace_code IS NOT NULL
                  AND f.turnover IS NOT NULL
                  AND c.nace_text NOT ILIKE '%nenoteikt%'
                GROUP BY LEFT(c.nace_code, 4)
                ORDER BY sub_turnover DESC
                LIMIT 10
            """
            sub_industries_rows = conn.execute(text(sub_industries_query), {"code": nace_param, "code_len": code_len, "year": year}).fetchall()

            for row in sub_industries_rows:
                st = safe_float(row.sub_turnover) or 0
                share = 0
                if total_industry_turnover > 0:
                    share = round((st / total_industry_turnover) * 100, 1)
                
                # Use the name from DB, filtering out "Nenoteikta nozare"
                name = row.sub_name_sample
                if not name or 'nenoteikt' in name.lower():
                    name = f"Apakšnozare {row.sub_code}"
                
                sub_industries.append({
                    "code": row.sub_code,
                    "name": name,
                    "turnover": st,
                    "formatted_turnover": format_large_number(st),
                    "share": share,
                    "companies": row.company_count or 0
                })

        return {
            "nace_code": nace_code,
            "nace_name": nace_name,
            "icon": nace_icon,
            "year": year,
            "stats": {
                "total_turnover": safe_float(stats.total_turnover),
                "total_turnover_formatted": format_large_number(stats.total_turnover),
                "turnover_growth": calc_growth(safe_float(stats.total_turnover), safe_float(prev_stats.total_turnover)),
                "total_profit": safe_float(stats.total_profit),
                "total_profit_formatted": format_large_number(stats.total_profit),
                "active_companies": stats.active_companies or 0,
                "total_employees": safe_int(stats.total_employees),
                "avg_salary": industry_avg_salary,
                "national_avg_salary": national_avg_salary,
                "salary_ratio": salary_ratio,
                "tax_burden": tax_burden,
                "concentration_val": concentration_val,
                "concentration_level": concentration_level
            },
            "leaders": leaders_data,
            "history": history_data,
            "sub_industries": sub_industries
        }

    except Exception as e:
        logger.error(f"Error fetching industry detail: {e}")
        if response:
            response.status_code = 500
        return {"error": str(e)}
    finally:
        conn.close()


# ============================================================================
# EXISTING INDUSTRY COMPANIES ENDPOINT (kept for backwards compat)
# ============================================================================

@router.get("/industries/{nace_section}")
def get_industry_companies(
    nace_section: str,
    sort_by: str = Query("turnover", pattern="^(turnover|profit)$"),
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
    sort_by: str = Query("turnover", pattern="^(turnover|profit)$")
):
    """
    Get TOP 100 companies across all industries.
    Optimized to use materialized view for instant loading.
    """
    try:
        with engine.connect() as conn:
            # Check if materialized view exists/has data
            # If not (e.g. before migration run), fall back might be needed, 
            # but we assume migration is run as per instructions.
            
            sql = f"""
                SELECT 
                    regcode,
                    name,
                    nace_section_text as industry,
                    turnover,
                    profit,
                    employees,
                    data_year as year,
                    company_size_badge as company_size,
                    pvn_number,
                    is_pvn_payer
                FROM company_stats_materialized
                WHERE {sort_by} IS NOT NULL 
                ORDER BY {sort_by} DESC
                LIMIT 100
            """
            
            companies = conn.execute(text(sql)).fetchall()
            
            result_companies = []
            for idx, c in enumerate(companies):
                result_companies.append({
                    "rank": idx + 1,
                    "regcode": c.regcode,
                    "name": c.name,
                    "industry": c.industry,
                    "turnover": safe_float(c.turnover),
                    "profit": safe_float(c.profit),
                    "employees": c.employees,
                    "year": c.year,
                    "company_size": c.company_size,
                    "pvn_number": c.pvn_number,
                    "is_pvn_payer": c.is_pvn_payer
                })
            
            return {
                "sort_by": sort_by,
                "total": len(result_companies),
                "companies": result_companies
            }
    except Exception as e:
        logger.error(f"TOP 100 query error: {e}")
        # Fallback to empty list or re-raise depending on policy
        # For now, let's re-raise so we know if something is broken
        raise
