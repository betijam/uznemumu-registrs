"""
Regional Economics API Router

Endpoints:
- GET /api/regions/overview - Get all territories with economic metrics for map/table
- GET /api/regions/{id}/details - Get detailed view for specific territory
- GET /api/regions/{id}/industries - Get industry breakdown for territory
- GET /api/regions/{id}/top-companies - Get top companies in territory
- POST /api/regions/compare - Compare multiple territories
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db

router = APIRouter(prefix="/regions", tags=["regions"])


# ============================================================================
# Pydantic Models
# ============================================================================

class TerritoryOverview(BaseModel):
    id: int
    code: str
    name: str
    type: str
    year: Optional[int]
    total_revenue: Optional[float]
    total_profit: Optional[float]
    total_employees: Optional[int]
    avg_salary: Optional[float]
    company_count: Optional[int]
    revenue_growth_yoy: Optional[float]


class TerritoryDetails(BaseModel):
    id: int
    code: str
    name: str
    type: str
    level: int
    
    # Latest year stats
    year: Optional[int]
    total_revenue: Optional[float]
    total_profit: Optional[float]
    total_employees: Optional[int]
    avg_salary: Optional[float]
    company_count: Optional[int]
    
    # Growth rates
    revenue_growth_yoy: Optional[float]
    employee_growth_yoy: Optional[float]
    salary_growth_yoy: Optional[float]
    
    # Historical data
    history: Optional[List[dict]]


class IndustryBreakdown(BaseModel):
    industry_code: str
    industry_name: Optional[str]
    total_revenue: Optional[float]
    total_employees: Optional[int]
    company_count: Optional[int]
    revenue_share: Optional[float]


class TopCompany(BaseModel):
    regcode: int
    name: str
    turnover: Optional[float]
    profit: Optional[float]
    employees: Optional[int]
    nace_text: Optional[str]


class CompareRequest(BaseModel):
    territory_ids: List[int]
    year: Optional[int] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/overview", response_model=List[TerritoryOverview])
def get_regions_overview(
    year: Optional[int] = Query(None, description="Year for data (default: latest)"),
    metric: str = Query("revenue", description="Sort by metric: revenue, employees, salary, growth"),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    Get overview of all territories with economic metrics.
    Used for choropleth map and summary table.
    """
    # Cache for 15 minutes
    response.headers["Cache-Control"] = "public, max-age=900"
    
    # Get latest year if not specified
    if not year:
        result = db.execute(text("SELECT MAX(year) FROM territory_year_aggregates"))
        year = result.scalar() or 2023
    
    # Sort column mapping
    sort_map = {
        "revenue": "tya.total_revenue",
        "employees": "tya.total_employees",
        "salary": "tya.avg_salary",
        "growth": "tya.revenue_growth_yoy",
        "companies": "tya.company_count"
    }
    sort_col = sort_map.get(metric, "tya.total_revenue")
    
    sql = f"""
    SELECT 
        t.id,
        t.code,
        t.name,
        t.type,
        tya.year,
        tya.total_revenue,
        tya.total_profit,
        tya.total_employees,
        tya.avg_salary,
        tya.company_count,
        tya.revenue_growth_yoy
    FROM territories t
    LEFT JOIN territory_year_aggregates tya ON t.id = tya.territory_id AND tya.year = :year
    WHERE t.level = 2  -- Municipalities only
      AND (t.valid_to IS NULL OR t.valid_to > NOW())
    ORDER BY {sort_col} DESC NULLS LAST
    """
    
    result = db.execute(text(sql), {"year": year})
    
    return [
        TerritoryOverview(
            id=row.id,
            code=row.code,
            name=row.name,
            type=row.type,
            year=row.year,
            total_revenue=float(row.total_revenue) if row.total_revenue else None,
            total_profit=float(row.total_profit) if row.total_profit else None,
            total_employees=row.total_employees,
            avg_salary=float(row.avg_salary) if row.avg_salary else None,
            company_count=row.company_count,
            revenue_growth_yoy=float(row.revenue_growth_yoy) if row.revenue_growth_yoy else None
        )
        for row in result.fetchall()
    ]


@router.get("/years")
def get_available_years(db: Session = Depends(get_db)):
    """Get list of years with data available"""
    result = db.execute(text("""
        SELECT DISTINCT year 
        FROM territory_year_aggregates 
        ORDER BY year DESC
    """))
    return [row.year for row in result.fetchall()]


@router.get("/{territory_id}/details", response_model=TerritoryDetails)
def get_territory_details(
    territory_id: int,
    year: Optional[int] = Query(None, description="Year for data"),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed economic data for a specific territory.
    Includes KPIs, growth rates, and historical trends.
    """
    response.headers["Cache-Control"] = "public, max-age=900"
    
    # Get territory info
    territory = db.execute(text("""
        SELECT id, code, name, type, level
        FROM territories
        WHERE id = :id
    """), {"id": territory_id}).fetchone()
    
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    # Get latest year if not specified
    if not year:
        result = db.execute(text("""
            SELECT MAX(year) FROM territory_year_aggregates WHERE territory_id = :id
        """), {"id": territory_id})
        year = result.scalar() or 2023
    
    # Get current year stats
    stats = db.execute(text("""
        SELECT *
        FROM territory_year_aggregates
        WHERE territory_id = :id AND year = :year
    """), {"id": territory_id, "year": year}).fetchone()
    
    # Get historical data (last 5 years)
    history = db.execute(text("""
        SELECT year, total_revenue, total_profit, total_employees, avg_salary, company_count,
               revenue_growth_yoy, employee_growth_yoy, salary_growth_yoy
        FROM territory_year_aggregates
        WHERE territory_id = :id
        ORDER BY year DESC
        LIMIT 5
    """), {"id": territory_id}).fetchall()
    
    return TerritoryDetails(
        id=territory.id,
        code=territory.code,
        name=territory.name,
        type=territory.type,
        level=territory.level,
        year=year,
        total_revenue=float(stats.total_revenue) if stats and stats.total_revenue else None,
        total_profit=float(stats.total_profit) if stats and stats.total_profit else None,
        total_employees=stats.total_employees if stats else None,
        avg_salary=float(stats.avg_salary) if stats and stats.avg_salary else None,
        company_count=stats.company_count if stats else None,
        revenue_growth_yoy=float(stats.revenue_growth_yoy) if stats and stats.revenue_growth_yoy else None,
        employee_growth_yoy=float(stats.employee_growth_yoy) if stats and stats.employee_growth_yoy else None,
        salary_growth_yoy=float(stats.salary_growth_yoy) if stats and stats.salary_growth_yoy else None,
        history=[
            {
                "year": h.year,
                "total_revenue": float(h.total_revenue) if h.total_revenue else None,
                "total_profit": float(h.total_profit) if h.total_profit else None,
                "total_employees": h.total_employees,
                "avg_salary": float(h.avg_salary) if h.avg_salary else None,
                "company_count": h.company_count
            }
            for h in history
        ]
    )


@router.get("/{territory_id}/industries", response_model=List[IndustryBreakdown])
def get_territory_industries(
    territory_id: int,
    year: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get industry breakdown for a territory (top industries by revenue)"""
    
    if not year:
        result = db.execute(text("""
            SELECT MAX(year) FROM territory_industry_year_aggregates WHERE territory_id = :id
        """), {"id": territory_id})
        year = result.scalar() or 2023
    
    # Get total revenue for percentage calculation
    total = db.execute(text("""
        SELECT SUM(total_revenue) as total
        FROM territory_industry_year_aggregates
        WHERE territory_id = :id AND year = :year
    """), {"id": territory_id, "year": year}).fetchone()
    
    total_revenue = float(total.total) if total and total.total else 1
    
    result = db.execute(text("""
        SELECT 
            industry_code,
            industry_name,
            total_revenue,
            total_employees,
            company_count
        FROM territory_industry_year_aggregates
        WHERE territory_id = :id AND year = :year
        ORDER BY total_revenue DESC NULLS LAST
        LIMIT :limit
    """), {"id": territory_id, "year": year, "limit": limit})
    
    return [
        IndustryBreakdown(
            industry_code=row.industry_code,
            industry_name=row.industry_name,
            total_revenue=float(row.total_revenue) if row.total_revenue else None,
            total_employees=row.total_employees,
            company_count=row.company_count,
            revenue_share=round(float(row.total_revenue) / total_revenue * 100, 1) if row.total_revenue else None
        )
        for row in result.fetchall()
    ]


@router.get("/{territory_id}/top-companies", response_model=List[TopCompany])
def get_territory_top_companies(
    territory_id: int,
    year: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get top companies in a territory by turnover"""
    
    # Get territory code
    territory = db.execute(text("""
        SELECT code FROM territories WHERE id = :id
    """), {"id": territory_id}).fetchone()
    
    if not territory:
        raise HTTPException(status_code=404, detail="Territory not found")
    
    if not year:
        result = db.execute(text("SELECT MAX(year) FROM financial_reports"))
        year = result.scalar() or 2023
    
    result = db.execute(text("""
        SELECT 
            c.regcode,
            c.name,
            fr.turnover,
            fr.profit,
            fr.employees,
            c.nace_text
        FROM companies c
        JOIN financial_reports fr ON c.regcode = fr.company_regcode
        WHERE c.atvk = :territory_code
          AND fr.year = :year
          AND c.status = 'active'
        ORDER BY fr.turnover DESC NULLS LAST
        LIMIT :limit
    """), {"territory_code": territory.code, "year": year, "limit": limit})
    
    return [
        TopCompany(
            regcode=row.regcode,
            name=row.name,
            turnover=float(row.turnover) if row.turnover else None,
            profit=float(row.profit) if row.profit else None,
            employees=row.employees,
            nace_text=row.nace_text
        )
        for row in result.fetchall()
    ]


@router.post("/compare")
def compare_territories(
    request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    Compare up to 5 territories side by side.
    Returns comparison table with all metrics.
    """
    if len(request.territory_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 territories allowed")
    
    if not request.territory_ids:
        raise HTTPException(status_code=400, detail="At least one territory required")
    
    year = request.year
    if not year:
        result = db.execute(text("SELECT MAX(year) FROM territory_year_aggregates"))
        year = result.scalar() or 2023
    
    # Get data for all territories
    placeholders = ", ".join([f":id{i}" for i in range(len(request.territory_ids))])
    params = {f"id{i}": tid for i, tid in enumerate(request.territory_ids)}
    params["year"] = year
    
    result = db.execute(text(f"""
        SELECT 
            t.id,
            t.code,
            t.name,
            t.type,
            tya.total_revenue,
            tya.total_profit,
            tya.total_employees,
            tya.avg_salary,
            tya.company_count,
            tya.revenue_growth_yoy,
            tya.employee_growth_yoy,
            tya.salary_growth_yoy
        FROM territories t
        LEFT JOIN territory_year_aggregates tya ON t.id = tya.territory_id AND tya.year = :year
        WHERE t.id IN ({placeholders})
    """), params)
    
    territories = []
    for row in result.fetchall():
        territories.append({
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "type": row.type,
            "total_revenue": float(row.total_revenue) if row.total_revenue else None,
            "total_profit": float(row.total_profit) if row.total_profit else None,
            "total_employees": row.total_employees,
            "avg_salary": float(row.avg_salary) if row.avg_salary else None,
            "company_count": row.company_count,
            "revenue_growth_yoy": float(row.revenue_growth_yoy) if row.revenue_growth_yoy else None,
            "employee_growth_yoy": float(row.employee_growth_yoy) if row.employee_growth_yoy else None,
            "salary_growth_yoy": float(row.salary_growth_yoy) if row.salary_growth_yoy else None
        })
    
    return {
        "year": year,
        "territories": territories
    }


@router.get("/search")
def search_territories(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search territories by name"""
    result = db.execute(text("""
        SELECT id, code, name, type, level
        FROM territories
        WHERE LOWER(name) LIKE LOWER(:query)
          AND level = 2
          AND (valid_to IS NULL OR valid_to > NOW())
        ORDER BY name
        LIMIT :limit
    """), {"query": f"%{q}%", "limit": limit})
    
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "type": row.type,
            "level": row.level
        }
        for row in result.fetchall()
    ]
