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

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from etl.loader import engine

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


class LocationStats(BaseModel):
    name: str
    location_type: str  # 'municipality', 'city', 'parish'
    company_count: int
    total_employees: Optional[int]
    total_revenue: Optional[float]
    total_profit: Optional[float]
    avg_salary: Optional[float]
    avg_revenue_per_company: Optional[float]


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
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                a.municipality_name as name,
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
            WHERE a.municipality_name IS NOT NULL
              AND c.status = 'active'
            GROUP BY a.municipality_name
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
                total_profit=safe_float(row.total_profit)
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
    """
    if response:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                a.city_name as name,
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
            WHERE a.city_name IS NOT NULL
              AND c.status = 'active'
            GROUP BY a.city_name
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
                total_profit=safe_float(row.total_profit)
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
                total_profit=safe_float(row.total_profit)
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
    
    column = column_map[location_type]
    
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT 
                a.{column} as name,
                COUNT(DISTINCT c.regcode) as company_count,
                SUM(fr.employees) as total_employees,
                SUM(fr.turnover) as total_revenue,
                SUM(fr.profit) as total_profit,
                AVG(fr.turnover) as avg_revenue_per_company,
                AVG(fr.avg_salary) as avg_salary
            FROM companies c
            JOIN address_dimension a ON c.addressid = a.address_id
            LEFT JOIN LATERAL (
                SELECT employees, turnover, profit, 
                       CASE WHEN employees > 0 THEN turnover / employees ELSE NULL END as avg_salary
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) fr ON true
            WHERE a.{column} = :name
              AND c.status = 'active'
            GROUP BY a.{column}
        """), {"name": name})
        
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
