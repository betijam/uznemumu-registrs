from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import text, or_
from app.routers.companies import engine, safe_float
import math
import logging
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed sort fields
SORT_FIELDS = {
    "turnover": "f.turnover",
    "profit": "f.profit",
    "employees": "f.employees",
    "reg_date": "c.registration_date",
    "salary": "salary_calc.avg_gross",
    "tax": "tp.total_tax_paid",
    "growth": "growth_calc" # CTE or formula
}

@router.get("/companies/list")
def list_companies(
    response: Response,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("turnover", pattern="^(turnover|profit|employees|reg_date|salary|tax|growth)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    nace: Optional[List[str]] = Query(None, description="List of NACE codes (partial match)"),
    region: Optional[str] = Query(None, description="Region search term, e.g. Riga"),
    status: str = Query("all", pattern="^(active|liquidated|all)$"),
    min_turnover: Optional[int] = Query(None),
    max_turnover: Optional[int] = Query(None),
    min_employees: Optional[int] = Query(None),
    year: Optional[int] = Query(None, description="Financial year filter, defaults to latest available if sorting by finance"),
    has_pvn: Optional[bool] = Query(None),
    has_sanctions: Optional[bool] = Query(None)
):
    """
    Universal Company Explorer Endpoint.
    Supports filtering, sorting, and pagination for the 'Super-Table'.
    """
    # Cache for 5 mins
    response.headers["Cache-Control"] = "public, max-age=300"
    
    offset = (page - 1) * limit
    
    # Determine efficient latest year if not provided
    if not year:
        # Simple heuristic: last year - 1
        year = 2024 
        
    prev_year = year - 1
    
    # Base Query Construction
    
    # If sorting by salary, we need tax payments - use INNER JOIN to exclude companies without data
    cte_salary = ""
    if sort_by == "salary":
        cte_salary = f"""
        INNER JOIN (
            SELECT company_regcode, 
                   (social_tax_vsaoi / NULLIF(avg_employees, 0) / 12 / 0.3409) as avg_gross
            FROM tax_payments 
            WHERE year = {year} AND avg_employees >= 5 AND social_tax_vsaoi > 0
        ) salary_calc ON salary_calc.company_regcode = c.regcode
        """
    
    cte_tax = ""
    if sort_by == "tax":
         cte_tax = f"""
        LEFT JOIN tax_payments tp ON tp.company_regcode = c.regcode AND tp.year = {year}
        """

    # Clause Builder
    where_clauses = ["1=1"]
    params = {}
    
    if status != "all":
        if status == "active":
             where_clauses.append("(c.status = 'active' OR c.status = 'A' OR c.status ILIKE 'aktīvs' OR c.status IS NULL OR c.status = '')")
        elif status == "liquidated":
             where_clauses.append("(c.status = 'liquidated' OR c.status = 'L' OR c.status ILIKE 'likvidēts' OR c.status ILIKE 'steigta likvidācija')")
    
    if nace:
        # Support multiple NACE codes
        nace_clauses = []
        for i, code in enumerate(nace):
            param_name = f"nace_{i}"
            nace_clauses.append(f"c.nace_code LIKE :{param_name}")
            params[param_name] = f"{code}%"
        
        if nace_clauses:
            where_clauses.append(f"({' OR '.join(nace_clauses)})")
        
    if region:
        where_clauses.append("c.address ILIKE :region")
        params["region"] = f"%{region}%"
        
    if min_turnover:
        # IMPORTANT: Exclude NaN because NaN > 5000 is True in Postgres numeric
        where_clauses.append("(f.turnover >= :min_t AND f.turnover <> 'NaN')")
        params["min_t"] = min_turnover
    
    if max_turnover:
        where_clauses.append("f.turnover <= :max_t")
        params["max_t"] = max_turnover
        
    if min_employees:
        if sort_by == "reg_date": 
             where_clauses.append("c.employee_count >= :min_e") 
        else:
             where_clauses.append("f.employees >= :min_e")
        params["min_e"] = min_employees

    if has_pvn:
        where_clauses.append("c.is_pvn_payer = TRUE")
        
    if has_sanctions:
        where_clauses.append("""
            EXISTS (SELECT 1 FROM risks r WHERE r.company_regcode = c.regcode AND r.active = TRUE AND r.risk_type = 'sanction')
        """)

    # Filter NaN from sorting fields to avoid bad data
    if sort_by in ["turnover", "profit"]:
        where_clauses.append(f"f.{sort_by} <> 'NaN'")
        where_clauses.append(f"f.{sort_by} IS NOT NULL")
        where_clauses.append(f"f.{sort_by} > 0")
    
    if sort_by == "growth":
         # Must have data for both years to calculate growth
         where_clauses.append("f.turnover IS NOT NULL AND f.turnover <> 'NaN' AND f.turnover > 0")
         where_clauses.append("prev.turnover IS NOT NULL AND prev.turnover <> 'NaN' AND prev.turnover > 0")
    
    if sort_by == "salary":
        where_clauses.append("salary_calc.avg_gross IS NOT NULL")
        where_clauses.append("salary_calc.avg_gross > 0")

    # Dynamic Order Clause
    sort_col = SORT_FIELDS.get(sort_by, "f.turnover")
    if sort_by == "growth":
        sort_col = "ROUND(((CAST(f.turnover AS NUMERIC) - CAST(prev.turnover AS NUMERIC)) / NULLIF(ABS(CAST(prev.turnover AS NUMERIC)), 0)) * 100, 1)"
        
    order_clause = f"{sort_col} {order.upper()} NULLS LAST"
    
    # Construct Query
    main_query = f"""
        SELECT 
            c.regcode, c.name, c.name_in_quotes, c."type" as company_type, c.type_text,
            c.nace_text, c.registration_date, c.status,
            f.turnover, f.profit, f.employees, f.year as fin_year,
            { "salary_calc.avg_gross as avg_salary," if sort_by == "salary" else "NULL as avg_salary," }
            { "tp.total_tax_paid," if sort_by == "tax" else "NULL as total_tax_paid," }
            (f.profit / NULLIF(f.turnover, 0)) * 100 as profit_margin,
            ROUND(((CAST(f.turnover AS NUMERIC) - CAST(prev.turnover AS NUMERIC)) / NULLIF(ABS(CAST(prev.turnover AS NUMERIC)), 0)) * 100, 1) as turnover_growth
        FROM companies c
        LEFT JOIN financial_reports f ON f.company_regcode = c.regcode AND f.year = :year
        LEFT JOIN financial_reports prev ON prev.company_regcode = c.regcode AND prev.year = :prev_year
        {cte_salary}
        {cte_tax}
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {order_clause}
        LIMIT :limit OFFSET :offset
    """
    
    # KPI / Stats Query
    stats_query = f"""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN f.turnover <> 'NaN' THEN f.turnover ELSE 0 END) as total_turnover,
            SUM(CASE WHEN f.profit <> 'NaN' THEN f.profit ELSE 0 END) as total_profit,
            SUM(f.employees) as total_employees
        FROM companies c
        LEFT JOIN financial_reports f ON f.company_regcode = c.regcode AND f.year = :year
        LEFT JOIN financial_reports prev ON prev.company_regcode = c.regcode AND prev.year = :prev_year
        {cte_salary}
        {cte_tax}
        WHERE {" AND ".join(where_clauses)}
    """
    
    # Logging for debugging
    logger.info(f"Explorer Request - Status: '{status}', Region: '{region}', Sort: '{sort_by}'")
    
    try:
        with engine.connect() as conn:
            # Execute Stats (includes Count)
            stats = conn.execute(text(stats_query), {**params, "year": year, "prev_year": prev_year}).fetchone()
            
            # Execute List
            result = conn.execute(text(main_query), {**params, "limit": limit, "offset": offset, "year": year, "prev_year": prev_year}).fetchall()
            
            companies = []
            for r in result:
                companies.append({
                    "regcode": r.regcode,
                    "name": r.name,
                    "name_in_quotes": r.name_in_quotes if hasattr(r, 'name_in_quotes') else None,
                    "type": r.company_type if hasattr(r, 'company_type') else None,
                    "type_text": r.type_text if hasattr(r, 'type_text') else None,
                    "nace": r.nace_text,
                    "reg_date": str(r.registration_date),
                    "status": r.status,
                    "turnover": safe_float(r.turnover),
                    "profit": safe_float(r.profit),
                    "employees": r.employees,
                    "salary": safe_float(r.avg_salary) if hasattr(r, 'avg_salary') else None,
                    "profit_margin": safe_float(r.profit_margin),
                    "tax_paid": safe_float(r.total_tax_paid) if hasattr(r, 'total_tax_paid') else None,
                    "turnover_growth": safe_float(r.turnover_growth)
                })
            
            return {
                "data": companies,
                "meta": {
                    "total": stats.total_count,
                    "page": page,
                    "limit": limit,
                    "sort_by": sort_by,
                    "financial_year": year
                },
                "stats": {
                    "count": stats.total_count,
                    "total_turnover": safe_float(stats.total_turnover),
                    "total_profit": safe_float(stats.total_profit),
                    "total_employees": stats.total_employees
                }
            }
            
    except Exception as e:
        logger.error(f"Explorer Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
