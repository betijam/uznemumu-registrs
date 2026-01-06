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
 
  
 @ r o u t e r . g e t ( " / { l o c a t i o n _ t y p e } / { n a m e } / t o p - c o m p a n i e s " ,   r e s p o n s e _ m o d e l = L i s t [ T o p C o m p a n y I n L o c a t i o n ] )  
 d e f   g e t _ l o c a t i o n _ t o p _ c o m p a n i e s (  
         l o c a t i o n _ t y p e :   s t r ,  
         n a m e :   s t r ,  
         l i m i t :   i n t   =   Q u e r y ( 2 0 ,   g e = 1 ,   l e = 1 0 0 ) ,  
         r e s p o n s e :   R e s p o n s e   =   N o n e ,  
 ) :  
         " " "  
         G e t   t o p   c o m p a n i e s   i n   a   s p e c i f i c   l o c a t i o n   b y   t u r n o v e r .  
         l o c a t i o n _ t y p e :   ' c i t y '   o r   ' m u n i c i p a l i t y '  
         " " "  
         i f   r e s p o n s e :  
                 r e s p o n s e . h e a d e r s [ " C a c h e - C o n t r o l " ]   =   " p u b l i c ,   m a x - a g e = 3 6 0 0 "  
          
         #   M a p   t y p e   t o   c o l u m n  
         c o l u m n _ m a p   =   {  
                 " c i t y " :   " c i t y _ n a m e " ,  
                 " m u n i c i p a l i t y " :   " m u n i c i p a l i t y _ n a m e "  
         }  
          
         i f   l o c a t i o n _ t y p e   n o t   i n   c o l u m n _ m a p :  
                 r a i s e   H T T P E x c e p t i o n ( s t a t u s _ c o d e = 4 0 0 ,   d e t a i l = " I n v a l i d   l o c a t i o n _ t y p e .   U s e :   c i t y   o r   m u n i c i p a l i t y " )  
          
         c o l u m n   =   c o l u m n _ m a p [ l o c a t i o n _ t y p e ]  
          
         w i t h   e n g i n e . c o n n e c t ( )   a s   c o n n :  
                 r e s u l t   =   c o n n . e x e c u t e ( t e x t ( f " " "  
                         S E L E C T    
                                 c . r e g c o d e ,  
                                 c . n a m e ,  
                                 f r . t u r n o v e r ,  
                                 f r . p r o f i t ,  
                                 f r . e m p l o y e e s ,  
                                 c . n a c e _ t e x t  
                         F R O M   c o m p a n i e s   c  
                         J O I N   a d d r e s s _ d i m e n s i o n   a   O N   c . a d d r e s s i d   =   a . a d d r e s s _ i d  
                         L E F T   J O I N   L A T E R A L   (  
                                 S E L E C T   t u r n o v e r ,   p r o f i t ,   e m p l o y e e s  
                                 F R O M   f i n a n c i a l _ r e p o r t s  
                                 W H E R E   c o m p a n y _ r e g c o d e   =   c . r e g c o d e  
                                     A N D   t u r n o v e r   I S   N O T   N U L L  
                                     A N D   t u r n o v e r   ! =   ' I n f i n i t y ' : : f l o a t    
                                     A N D   t u r n o v e r   ! =   ' N a N ' : : f l o a t  
                                 O R D E R   B Y   y e a r   D E S C  
                                 L I M I T   1  
                         )   f r   O N   t r u e  
                         W H E R E   a . { c o l u m n }   =   : n a m e  
                             A N D   c . s t a t u s   =   ' a c t i v e '  
                             A N D   f r . t u r n o v e r   I S   N O T   N U L L  
                         O R D E R   B Y   f r . t u r n o v e r   D E S C  
                         L I M I T   : l i m i t  
                 " " " ) ,   { " n a m e " :   n a m e ,   " l i m i t " :   l i m i t } )  
                  
                 r e t u r n   [  
                         T o p C o m p a n y I n L o c a t i o n (  
                                 r e g c o d e = r o w . r e g c o d e ,  
                                 n a m e = r o w . n a m e ,  
                                 t u r n o v e r = s a f e _ f l o a t ( r o w . t u r n o v e r ) ,  
                                 p r o f i t = s a f e _ f l o a t ( r o w . p r o f i t ) ,  
                                 e m p l o y e e s = r o w . e m p l o y e e s ,  
                                 n a c e _ t e x t = r o w . n a c e _ t e x t  
                         )  
                         f o r   r o w   i n   r e s u l t . f e t c h a l l ( )  
                 ]  
 