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
    "turnover": "s.turnover",
    "profit": "s.profit",
    "employees": "s.employees",
    "reg_date": "c.registration_date",
    "salary": "s.avg_salary",
    "tax": "s.tax_paid",
    "growth": "s.turnover_growth"
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
    year: Optional[int] = Query(None, description="Financial year filter"),
    has_pvn: Optional[bool] = Query(None),
    has_sanctions: Optional[bool] = Query(None)
):
    """
    Universal Company Explorer Endpoint.
    Uses 'company_stats_materialized' for high performance.
    """
    # Cache for 5 mins
    response.headers["Cache-Control"] = "public, max-age=300"
    
    offset = (page - 1) * limit
    
    # Determine efficient latest year if not provided
    if not year:
        year = 2024 
    
    # Clause Builder
    where_clauses = ["1=1"]
    params = {"year": year}
    
    if status != "all":
        if status == "active":
             where_clauses.append("(c.status = 'active' OR c.status = 'A' OR c.status ILIKE 'aktīvs' OR c.status IS NULL OR c.status = '')")
        elif status == "liquidated":
             where_clauses.append("(c.status = 'liquidated' OR c.status = 'L' OR c.status ILIKE 'likvidēts' OR c.status ILIKE 'steigta likvidācija')")
    
    if nace:
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
        where_clauses.append("(s.turnover >= :min_t)")
        params["min_t"] = min_turnover
    
    if max_turnover:
        where_clauses.append("s.turnover <= :max_t")
        params["max_t"] = max_turnover
        
    if min_employees:
        if sort_by == "reg_date": 
             where_clauses.append("c.employee_count >= :min_e") 
        else:
             where_clauses.append("s.employees >= :min_e")
        params["min_e"] = min_employees

    if has_pvn:
        where_clauses.append("c.is_pvn_payer = TRUE")
        
    if has_sanctions:
        where_clauses.append("""
            EXISTS (SELECT 1 FROM risks r WHERE r.company_regcode = c.regcode AND r.active = TRUE AND r.risk_type = 'sanction')
        """)

    # Dynamic Order Clause
    sort_col = SORT_FIELDS.get(sort_by, "s.turnover")
    
    # Exclude NULL values when sorting by financial columns to avoid showing empty records first
    if sort_by in ["turnover", "profit", "salary", "tax", "growth"]:
        where_clauses.append(f"{sort_col} IS NOT NULL")
    
    # We rely on the Materialized View having pre-cleaned NULLs (instead of 'NaN' strings)
    # The NULLS LAST clause handles the sorting order.
    order_clause = f"{sort_col} {order.upper()} NULLS LAST"
    
    # Construct Query
    main_query = f"""
        SELECT 
            c.regcode, c.name, c.name_in_quotes, c."type" as company_type, c.type_text,
            c.nace_text, c.registration_date, c.status,
            s.turnover, s.profit, s.employees, s.year as fin_year,
            s.avg_salary,
            s.tax_paid as total_tax_paid,
            s.profit_margin,
            s.turnover_growth
        FROM companies c
        LEFT JOIN company_stats_materialized s ON s.regcode = c.regcode AND s.year = :year
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {order_clause}
        LIMIT :limit OFFSET :offset
    """
    
    # KPI / Stats Query
    stats_query = f"""
        SELECT 
            COUNT(*) as total_count,
            SUM(COALESCE(s.turnover, 0)) as total_turnover,
            SUM(COALESCE(s.profit, 0)) as total_profit,
            SUM(COALESCE(s.employees, 0)) as total_employees
        FROM companies c
        LEFT JOIN company_stats_materialized s ON s.regcode = c.regcode AND s.year = :year
        WHERE {" AND ".join(where_clauses)}
    """
    
    logger.info(f"Explorer Request (MatView) - Sort: '{sort_by}'")
    
    try:
        with engine.connect() as conn:
            # Execute Stats
            stats = conn.execute(text(stats_query), params).fetchone()
            
            # Execute List
            result = conn.execute(text(main_query), {**params, "limit": limit, "offset": offset}).fetchall()
            
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
        # Build strict fallback if MatView fails? 
        # For now, just raise error, as MatView should exist.
        raise HTTPException(status_code=500, detail=str(e))
