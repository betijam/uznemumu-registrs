"""
Locations API Router - VARIS Address Dimension

Endpoints for location-based filtering using real address data from VARIS.
Replaces/supplements the old ATVK territory system with precise geolocation.

Endpoints:
- GET /api/locations/municipalities - List all municipalities
- GET /api/locations/cities - List all cities  
- GET /api/locations/parishes - List all parishes
- GET /api/locations/{type}/{name}/stats - Get statistics for a location
"""

import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["locations"])


# ============================================================================
# Helper Functions
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


# ============================================================================
# Pydantic Models
# ============================================================================

class LocationItem(BaseModel):
    name: str
    company_count: int
    total_employees: Optional[int]
    total_revenue: Optional[float]
    total_profit: Optional[float]
    avg_salary: Optional[float]


class LocationStats(BaseModel):
    name: str
    location_type: str  # 'municipality', 'city', 'parish'
    company_count: int
    total_employees: Optional[int]
    total_revenue: Optional[float]
    total_profit: Optional[float]
    avg_salary: Optional[float]
    avg_revenue_per_company: Optional[float]


class TopCompanyInLocation(BaseModel):
    regcode: int
    name: str
    turnover: Optional[float]
    profit: Optional[float]
    employees: Optional[int]
    nace_text: Optional[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/municipalities", response_model=List[LocationItem])
def get_municipalities(
    min_companies: int = Query(0, description="Minimum number of companies"),
    limit: int = Query(50, ge=1, le=200),
    response: Response = None,
):
    """
    Get list of all municipalities with company counts and basic stats.
    Uses materialized view for fast loading.
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                location_name as name,
                company_count,
                total_employees,
                total_revenue,
                total_profit,
                avg_salary
            FROM location_statistics
            WHERE location_type = 'municipality'
              AND company_count >= :min_companies
            ORDER BY company_count DESC
            LIMIT :limit
        """), {"min_companies": min_companies, "limit": limit})
        
        return [
            LocationItem(
                name=row.name,
                company_count=row.company_count,
                total_employees=row.total_employees,
                total_revenue=safe_float(row.total_revenue),
                total_profit=safe_float(row.total_profit),
                avg_salary=safe_float(row.avg_salary)
            )
            for row in result.fetchall()
        ]


@router.get("/cities", response_model=List[LocationItem])
def get_cities(
    min_companies: int = Query(0, description="Minimum number of companies"),
    limit: int = Query(50, ge=1, le=200),
    response: Response = None,
):
    """
    Get list of all cities with company counts and basic stats.
    Uses materialized view for fast loading.
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                location_name as name,
                company_count,
                total_employees,
                total_revenue,
                total_profit,
                avg_salary
            FROM location_statistics
            WHERE location_type = 'city'
              AND company_count >= :min_companies
            ORDER BY company_count DESC
            LIMIT :limit
        """), {"min_companies": min_companies, "limit": limit})
        
        return [
            LocationItem(
                name=row.name,
                company_count=row.company_count,
                total_employees=row.total_employees,
                total_revenue=safe_float(row.total_revenue),
                total_profit=safe_float(row.total_profit),
                avg_salary=safe_float(row.avg_salary)
            )
            for row in result.fetchall()
        ]


@router.get("/parishes", response_model=List[LocationItem])
def get_parishes(
    min_companies: int = Query(1, description="Minimum number of companies"),
    limit: int = Query(100, ge=1, le=500),
    response: Response = None,
):
    """
    Get list of all parishes with company counts.
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                a.parish_name as name,
                COUNT(DISTINCT c.regcode) as company_count,
                SUM(fr.employees) as total_employees,
                SUM(fr.turnover) as total_revenue,
                SUM(fr.profit) as total_profit
            FROM companies c
            JOIN address_dimension a ON c.addressid = a.address_id
            LEFT JOIN LATERAL (
                SELECT employees, turnover, profit
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) fr ON true
            WHERE a.parish_name IS NOT NULL
              AND c.status = 'active'
            GROUP BY a.parish_name
            HAVING COUNT(DISTINCT c.regcode) >= :min_companies
            ORDER BY company_count DESC
            LIMIT :limit
        """), {"min_companies": min_companies, "limit": limit})
        
        return [
            LocationItem(
                name=row.name,
                company_count=row.company_count,
                total_employees=row.total_employees,
                total_revenue=safe_float(row.total_revenue),
                total_profit=safe_float(row.total_profit),
                avg_salary=safe_float(row.avg_salary)
            )
            for row in result.fetchall()
        ]


@router.get("/{location_type}/{name}/stats", response_model=LocationStats)
def get_location_stats(
    location_type: str,
    name: str,
    response: Response = None,
):
    """
    Get detailed statistics for a specific location.
    location_type: 'municipality', 'city', or 'parish'
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=900"
    
    # Map type to column
    column_map = {
        "municipality": "municipality_name",
        "city": "city_name",
        "parish": "parish_name"
    }
    
    if location_type not in column_map:
        raise HTTPException(status_code=400, detail="Invalid location_type. Use: municipality, city, or parish")
    
    # For parish, we still need to calculate on the fly as it's not in the materialized view (yet)
    if location_type == 'parish':
         with engine.connect() as conn:
            # Determine stable year
            stable_year = 2024
            
            result = conn.execute(text(f"""
                SELECT 
                    a.parish_name as name,
                    COUNT(DISTINCT c.regcode) as company_count,
                    SUM(fr.employees) as total_employees,
                    SUM(fr.turnover) as total_revenue,
                    SUM(fr.profit) as total_profit,
                    AVG(fr.turnover) as avg_revenue_per_company,
                    AVG(CASE WHEN fr.employees > 0 THEN (fr.turnover / 12) / fr.employees ELSE NULL END) as avg_salary
                FROM companies c
                JOIN address_dimension a ON c.addressid = a.address_id
                LEFT JOIN LATERAL (
                    -- Prefer 2024, fallback to latest available if missing
                    SELECT employees, turnover, profit
                    FROM financial_reports
                    WHERE company_regcode = c.regcode
                      AND turnover > 0
                      AND year >= 2023
                    ORDER BY (year = :stable_year) DESC, year DESC
                    LIMIT 1
                ) fr ON true
                WHERE a.parish_name = :name
                  AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
                GROUP BY a.parish_name
            """), {"name": name, "stable_year": stable_year})
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Parish not found")
            
            return LocationStats(
                name=row.name,
                location_type=location_type,
                company_count=row.company_count,
                total_employees=row.total_employees,
                total_revenue=safe_float(row.total_revenue),
                total_profit=safe_float(row.total_profit),
                avg_salary=safe_float(row.avg_salary),
                avg_revenue_per_company=safe_float(row.avg_revenue_per_company)
            )

    # For cities and municipalities, use the materialized view
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                location_name as name,
                company_count,
                total_employees,
                total_revenue,
                total_profit,
                avg_salary,
                avg_revenue_per_company
            FROM location_statistics
            WHERE location_type = :type
              AND location_name = :name
        """), {"type": location_type, "name": name})
        
        row = result.fetchone()
        
        if not row:
             raise HTTPException(status_code=404, detail=f"{location_type.capitalize()} not found")
        
        return LocationStats(
            name=row.name,
            location_type=location_type,
            company_count=row.company_count,
            total_employees=row.total_employees,
            total_revenue=safe_float(row.total_revenue),
            total_profit=safe_float(row.total_profit),
            avg_salary=safe_float(row.avg_salary),
            avg_revenue_per_company=safe_float(row.avg_revenue_per_company)
        )


@router.get("/{location_type}/{name}/top-companies", response_model=List[TopCompanyInLocation])
def get_location_top_companies(
    location_type: str,
    name: str,
    year: Optional[int] = Query(None, description="Year for financial data"),
    limit: int = Query(20, ge=1, le=100),
    response: Response = None,
):
    """
    Get top companies in a specific location by turnover.
    Refactored to use live financial reports for accuracy and "latest available data" logic.
    """
    if response:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    
    print(f"CRITICAL_DEPLOY_V6: Fetching top companies for {location_type} {name} (Year: 2024 Priority)")
    logger.error(f"CRITICAL_DEPLOY_V6: Fetching top companies for {location_type} {name}")
    
    # Use 2024 as default stable year
    stable_year = year or 2024
    
    # Map type to column
    column_map = {
        "city": "city_name",
        "municipality": "municipality_name",
        "parish": "parish_name"
    }
    
    if location_type not in column_map:
        raise HTTPException(status_code=400, detail="Invalid location_type. Use: city, municipality, or parish")
    
    column = column_map[location_type]
    
    with engine.connect() as conn:
        # Optimized query favoring 2024 but falling back to latest if missing
        query = f"""
            SELECT 
                c.regcode,
                c.name,
                fr.turnover,
                fr.profit,
                fr.employees,
                c.nace_text
            FROM companies c
            JOIN address_dimension a ON c.addressid = a.address_id
            LEFT JOIN LATERAL (
                SELECT turnover, profit, employees, year
                FROM financial_reports
                WHERE company_regcode = c.regcode
                  AND turnover > 0
                  AND year >= 2023
                ORDER BY (year = :stable_year) DESC, year DESC
                LIMIT 1
            ) fr ON true
            WHERE a.{column} = :name
              AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
            ORDER BY fr.turnover DESC
            LIMIT :limit
        """
        result = conn.execute(text(query), {"name": name, "limit": limit, "stable_year": stable_year})
        rows = result.fetchall()
        
        # 2. Fallback: If address_dimension yielded insufficient results, try address text fallback
        if len(rows) < limit:
            exclude_regcodes = [r.regcode for r in rows] or [-1]
            
            fallback_query = """
                SELECT 
                    c.regcode,
                    c.name,
                    fr.turnover,
                    fr.profit,
                    fr.employees,
                    c.nace_text
                FROM companies c
                LEFT JOIN LATERAL (
                    SELECT turnover, profit, employees, year
                    FROM financial_reports
                    WHERE company_regcode = c.regcode
                      AND turnover > 0
                      AND year >= 2023
                    ORDER BY (year = :stable_year) DESC, year DESC
                    LIMIT 1
                ) fr ON true
                WHERE c.address ILIKE :search_pattern
                  AND (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
                  AND c.regcode NOT IN :exclude_regcodes
                ORDER BY fr.turnover DESC
                LIMIT :remaining_limit
            """
            
            remaining_limit = limit - len(rows)
            fallback_rows = conn.execute(text(fallback_query), {
                "search_pattern": f"%{name}%", 
                "remaining_limit": remaining_limit,
                "exclude_regcodes": exclude_regcodes
            }).fetchall()
            
            rows.extend(fallback_rows)
            # Re-sort combined
            rows.sort(key=lambda x: safe_float(x.turnover) or 0, reverse=True)
            rows = rows[:limit]

        return [
            TopCompanyInLocation(
                regcode=row.regcode,
                name=row.name,
                turnover=safe_float(row.turnover),
                profit=safe_float(row.profit),
                employees=row.employees,
                nace_text=row.nace_text
            )
            for row in rows
        ]
