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
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import engine

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

import math

def safe_float(val):
    """Convert value to JSON-safe float. Returns None for inf/NaN."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

@router.get("/overview", response_model=List[TerritoryOverview])
def get_regions_overview(
    year: Optional[int] = Query(None, description="Year for data (default: latest)"),
    metric: str = Query("revenue", description="Sort by metric: revenue, employees, salary, growth"),
    response: Response = None,
):
    """
    Get overview of all territories with economic metrics.
    Used for choropleth map and summary table.
    """
    # Cache for 15 minutes
    if response:
        response.headers["Cache-Control"] = "public, max-age=900"
    
    with engine.connect() as conn:
        # Get latest year if not specified - avoid incomplete years (like 2025)
        if not year:
            # Get max year that has at least some significant data across many territories
            result = conn.execute(text("""
                SELECT year FROM territory_year_aggregates 
                GROUP BY year 
                HAVING COUNT(*) > 20
                ORDER BY year DESC LIMIT 1
            """))
            year = result.scalar() or 2024
        
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
        
        result = conn.execute(text(sql), {"year": year})
        
        return [
            TerritoryOverview(
                id=row.id,
                code=row.code,
                name=row.name,
                type=row.type,
                year=row.year,
                total_revenue=safe_float(row.total_revenue),
                total_profit=safe_float(row.total_profit),
                total_employees=row.total_employees,
                avg_salary=safe_float(row.avg_salary),
                company_count=row.company_count,
                revenue_growth_yoy=safe_float(row.revenue_growth_yoy)
            )
            for row in result.fetchall()
        ]


@router.get("/years")
def get_available_years():
    """Get list of years with data available"""
    with engine.connect() as conn:
        result = conn.execute(text("""
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
):
    """
    Get detailed economic data for a specific territory.
    Includes KPIs, growth rates, and historical trends.
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=900"
    
    with engine.connect() as conn:
        # Get territory info
        territory = conn.execute(text("""
            SELECT id, code, name, type, level
            FROM territories
            WHERE id = :id
        """), {"id": territory_id}).fetchone()
        
        if not territory:
            raise HTTPException(status_code=404, detail="Territory not found")
        
        # Get latest year if not specified - avoid incomplete years
        if not year:
            year = 2024
            
        print(f"DEPLOY_VERIFY: Fetching territory details for territory ID: {territory_id} for year {year}")
        
        # Get current year stats on the fly to match top companies logic
        stats_query = """
            WITH location_companies AS (
                SELECT c.regcode
                FROM companies c
                JOIN address_dimension ad ON c.addressid = ad.address_id
                WHERE (ad.city_name = :t_name OR ad.municipality_name = :t_name OR ad.parish_name = :t_name)
                  AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
            )
            SELECT 
                COUNT(*) as company_count,
                SUM(CASE WHEN fr.turnover IS NULL OR fr.turnover = 'NaN'::float OR fr.turnover > 1e15 THEN 0 ELSE fr.turnover END) as total_revenue,
                SUM(CASE WHEN fr.profit IS NULL OR fr.profit = 'NaN'::float OR fr.profit > 1e15 THEN 0 ELSE fr.profit END) as total_profit,
                SUM(CASE WHEN fr.employees IS NULL OR fr.employees > 1000000 THEN 0 ELSE fr.employees END) as total_employees,
                AVG(CASE WHEN cm.avg_gross_salary IS NULL OR cm.avg_gross_salary = 'NaN'::float OR cm.avg_gross_salary > 100000 THEN NULL ELSE cm.avg_gross_salary END) as avg_salary
            FROM location_companies lc
            LEFT JOIN financial_reports fr ON lc.regcode = fr.company_regcode AND fr.year = :year
            LEFT JOIN company_computed_metrics cm ON lc.regcode = cm.company_regcode AND cm.year = :year
        """
        stats = conn.execute(text(stats_query), {"t_name": territory.name, "year": year}).fetchone()
        
        # Get historical data (last 5 years)
        history = conn.execute(text("""
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
            total_revenue=safe_float(stats.total_revenue) if stats else None,
            total_profit=safe_float(stats.total_profit) if stats else None,
            total_employees=stats.total_employees if stats else None,
            avg_salary=safe_float(stats.avg_salary) if stats else None,
            company_count=stats.company_count if stats else None,
            revenue_growth_yoy=None, # Not easily calculated on-the-fly without prev year stats
            employee_growth_yoy=None,
            salary_growth_yoy=None,
            history=[
                {
                    "year": h.year,
                    "total_revenue": safe_float(h.total_revenue),
                    "total_profit": safe_float(h.total_profit),
                    "total_employees": h.total_employees,
                    "avg_salary": safe_float(h.avg_salary),
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
):
    """Get industry breakdown for a territory (top industries by revenue)"""
    
    with engine.connect() as conn:
        # Default to 2024 as the latest stable year
        if not year:
            year = 2024
        
        # Get total revenue for percentage calculation
        total = conn.execute(text("""
            SELECT SUM(total_revenue) as total
            FROM territory_industry_year_aggregates
            WHERE territory_id = :id AND year = :year
        """), {"id": territory_id, "year": year}).fetchone()
        
        total_revenue = float(total.total) if total and total.total else 1
        
        result = conn.execute(text("""
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
                total_revenue=safe_float(row.total_revenue),
                total_employees=row.total_employees,
                company_count=row.company_count,
                revenue_share=safe_float(float(row.total_revenue) / total_revenue * 100) if row.total_revenue else None
            )
            for row in result.fetchall()
        ]


@router.get("/{territory_id}/top-companies", response_model=List[TopCompany])
def get_territory_top_companies(
    territory_id: int,
    year: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
):
    """Get top companies in a territory by turnover"""
    
    with engine.connect() as conn:
        # Get territory info
        territory = conn.execute(text("""
            SELECT id, name, type, level FROM territories WHERE id = :id
        """), {"id": territory_id}).fetchone()
        
        if not territory:
            raise HTTPException(status_code=404, detail="Territory not found")
        
        # Default to 2024 as stable year
        stable_year = year or 2024
        print(f"DEPLOY_VERIFY_V5: Fetching top companies for territory {territory.name} (Year: {stable_year})")

        # Filter companies by joining with address_dimension on territory name
        # We use a LATERAL join to get the latest valid report, prioritizing 2024
        result = conn.execute(text("""
            SELECT 
                c.regcode,
                c.name,
                fr.turnover,
                fr.profit,
                fr.employees,
                c.nace_text
            FROM companies c
            JOIN address_dimension ad ON c.addressid = ad.address_id
            JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                  AND turnover IS NOT NULL 
                  AND turnover != 'NaN'::float
                  AND turnover > 0
                  AND year >= 2023 
                ORDER BY (year = :stable_year) DESC, year DESC
                LIMIT 1
            ) fr ON true
            WHERE (ad.city_name = :t_name OR ad.municipality_name = :t_name OR ad.parish_name = :t_name)
              AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
            ORDER BY fr.turnover DESC NULLS LAST
            LIMIT :limit
        """), {
            "t_name": territory.name, 
            "limit": limit,
            "stable_year": stable_year
        })
        
        return [
            TopCompany(
                regcode=row.regcode,
                name=row.name,
                turnover=safe_float(row.turnover),
                profit=safe_float(row.profit),
                employees=row.employees,
                nace_text=row.nace_text
            )
            for row in result.fetchall()
        ]


@router.post("/compare")
def compare_territories(
    request: CompareRequest,
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
    
    with engine.connect() as conn:
        # Use 2024 as default latest stable year unless specific year is requested
        if not year:
            year = 2024
        
        # Get data for all territories
        placeholders = ", ".join([f":id{i}" for i in range(len(request.territory_ids))])
        params = {f"id{i}": tid for i, tid in enumerate(request.territory_ids)}
        params["year"] = year
        
        sql = f"""
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
        """
        
        result = conn.execute(text(sql), params)
        
        territories = []
        for row in result.fetchall():
            territories.append({
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "type": row.type,
                "total_revenue": safe_float(row.total_revenue),
                "total_profit": safe_float(row.total_profit),
                "total_employees": row.total_employees,
                "avg_salary": safe_float(row.avg_salary),
                "company_count": row.company_count,
                "revenue_growth_yoy": safe_float(row.revenue_growth_yoy),
                "employee_growth_yoy": safe_float(row.employee_growth_yoy),
                "salary_growth_yoy": safe_float(row.salary_growth_yoy)
            })
        
        return {
            "year": year,
            "territories": territories
        }


@router.get("/search")
def search_territories(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
):
    """Search territories by name"""
    with engine.connect() as conn:
        result = conn.execute(text("""
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
