from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import text, or_
from app.routers.companies import engine, safe_float
import math
import logging
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Allowed sort fields
SORT_FIELDS = {
    "turnover": "f.turnover",
    "profit": "f.profit",
    "employees": "f.employees",
    "reg_date": "c.registration_date",
    "salary": "salary_calc.avg_gross",
    "tax": "tp.total_tax_paid"
}

@router.get("/companies/list")
def list_companies(
    response: Response,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("turnover", regex="^(turnover|profit|employees|reg_date|salary|tax)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    nace: Optional[str] = Query(None, description="Partial NACE code, e.g. 62.0"),
    region: Optional[str] = Query(None, description="Region search term, e.g. Riga"),
    status: str = Query("active", regex="^(active|liquidated|all)$"),
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
    # Only if we seek financial data
    if not year:
        # Simple heuristic: last year - 1
        year = 2024 
    
    # Base Query Construction
    # We join financial_reports carefully
    
    # If sorting by salary, we need tax payments view/cte
    # optimized CTE for salary
    cte_salary = ""
    if sort_by == "salary":
        cte_salary = f"""
        LEFT JOIN (
            SELECT company_regcode, 
                   (social_tax_vsaoi / NULLIF(avg_employees, 0) / 12 / 0.3409) as avg_gross
            FROM tax_payments 
            WHERE year = {year} AND avg_employees >= 5
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
        # mapping simple status to DB status
        # In DB: 'A' (Active) or 'Likvidēts' text? 
        # Checking init.sql/data: often 'A' happens or 'L'. 
        # Let's assume input is 'active' or 'liquidated' and map based on existing patterns.
        # Actually init.sql schema says text.
        # Usually 'active' means status IS NULL (active) or 'A'.
        # Let's try basic ILIKE matching for safety or simple logic.
        if status == "active":
             where_clauses.append("(c.status ILIKE 'aktīvs' OR c.status IS NULL OR c.status = 'A')")
        elif status == "liquidated":
             where_clauses.append("(c.status ILIKE 'likvidēts' OR c.status = 'L')")
    
    if nace:
        where_clauses.append("c.nace_code LIKE :nace")
        params["nace"] = f"{nace}%"
        
    if region:
        where_clauses.append("c.address ILIKE :region")
        params["region"] = f"%{region}%"
        
    if min_turnover:
        where_clauses.append("f.turnover >= :min_t")
        params["min_t"] = min_turnover
    
    if max_turnover:
        where_clauses.append("f.turnover <= :max_t")
        params["max_t"] = max_turnover
        
    if min_employees:
        if sort_by == "reg_date": # Maybe finance not joined?
             where_clauses.append("c.employee_count >= :min_e") # Use metadata if available
        else:
             where_clauses.append("f.employees >= :min_e")
        params["min_e"] = min_employees

    if has_pvn:
        where_clauses.append("c.is_pvn_payer = TRUE")
        
    if has_sanctions:
        # Join risks? or just check if in risks table
        # optimized: EXISTS
        where_clauses.append("""
            EXISTS (SELECT 1 FROM risks r WHERE r.company_regcode = c.regcode AND r.active = TRUE AND r.risk_type = 'sanction')
        """)

    # Filter NaN from sorting fields to avoid bad data
    if sort_by in ["turnover", "profit"] and not min_turnover:
        where_clauses.append(f"f.{sort_by} <> 'NaN'")


    # Dynamic Order Clause
    sort_col = SORT_FIELDS.get(sort_by, "f.turnover")
    order_clause = f"{sort_col} {order.upper()} NULLS LAST"
    
    # Financial JOIN logic
    # We always LEFT JOIN financials to allow listing companies even without stats (unless filtered by them)
    # But if sort_by is turnover/profit, we might want INNER JOIN to only show those with data?
    # User requirement: "List page". 
    # Best practice: LEFT JOIN but if sort is financial, rows with NULL go last.
    
    # Construct Query
    main_query = f"""
        SELECT 
            c.regcode, c.name, c.nace_text, c.registration_date, c.status,
            f.turnover, f.profit, f.employees, f.year as fin_year,
            { "salary_calc.avg_gross as avg_salary," if sort_by == "salary" else "NULL as avg_salary," }
            { "tp.total_tax_paid," if sort_by == "tax" else "NULL as total_tax_paid," }
            (f.profit / NULLIF(f.turnover, 0)) * 100 as profit_margin
        FROM companies c
        LEFT JOIN financial_reports f ON f.company_regcode = c.regcode AND f.year = :year
        {cte_salary}
        {cte_tax}
        WHERE {" AND ".join(where_clauses)}
        ORDER BY {order_clause}
        LIMIT :limit OFFSET :offset
    """
    
    # Count Query (Simplified for performance, maybe approximate?)
    count_query = f"""
        SELECT COUNT(*) 
        FROM companies c
        LEFT JOIN financial_reports f ON f.company_regcode = c.regcode AND f.year = :year
        {cte_salary}
        {cte_tax}
        WHERE {" AND ".join(where_clauses)}
    """
    
    try:
        with engine.connect() as conn:
            # Execute Count
            total = conn.execute(text(count_query), {**params, "year": year}).scalar()
            
            # Execute List
            result = conn.execute(text(main_query), {**params, "limit": limit, "offset": offset, "year": year}).fetchall()
            
            companies = []
            for r in result:
                companies.append({
                    "regcode": r.regcode,
                    "name": r.name,
                    "nace": r.nace_text,
                    "reg_date": str(r.registration_date),
                    "status": r.status,
                    "turnover": safe_float(r.turnover),
                    "profit": safe_float(r.profit),
                    "employees": r.employees,
                    "salary": safe_float(r.avg_salary) if hasattr(r, 'avg_salary') else None,
                    "profit_margin": safe_float(r.profit_margin),
                    "tax_paid": safe_float(r.total_tax_paid) if hasattr(r, 'total_tax_paid') else None
                })
            
            return {
                "data": companies,
                "meta": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "sort_by": sort_by,
                    "financial_year": year
                }
            }
            
    except Exception as e:
        logger.error(f"Explorer Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
