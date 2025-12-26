"""
Benchmark API Router

Provides endpoints for company comparison/benchmark functionality:
- POST /api/benchmark - Get comparison data for 2-5 companies
- POST /api/benchmark/session - Save a comparison session
- GET /api/benchmark/session/{sessionId} - Load a saved session
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from etl.loader import engine
import logging
from uuid import UUID
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class BenchmarkRequest(BaseModel):
    companyRegNumbers: List[str] = Field(..., min_items=2, max_items=5)
    year: int = Field(..., ge=2000, le=2100)
    
    @validator('companyRegNumbers')
    def validate_reg_numbers(cls, v):
        # Remove duplicates
        unique = list(set(v))
        if len(unique) != len(v):
            raise ValueError("Duplicate company registration numbers not allowed")
        return unique


class SaveSessionRequest(BaseModel):
    companyRegNumbers: List[str] = Field(..., min_items=2, max_items=5)
    year: int
    source: str = Field(..., regex="^(company_profile|company_list|direct_url)$")


class FinancialData(BaseModel):
    revenue: Optional[float]
    profit: Optional[float]
    profitMargin: Optional[float]
    ebit: Optional[float]
    ebitda: Optional[float]
    assetsTotal: Optional[float]
    equityTotal: Optional[float]
    roe: Optional[float]
    roa: Optional[float]


class WorkforceData(BaseModel):
    employees: Optional[int]
    avgSalary: Optional[float]
    revenuePerEmployee: Optional[float]


class TrendPoint(BaseModel):
    year: int
    value: Optional[float]


class Trend(BaseModel):
    revenue: List[TrendPoint]
    employees: List[TrendPoint]


class PositionByRevenue(BaseModel):
    rank: Optional[int]
    total: Optional[int]
    percentile: Optional[float]


class IndustryBenchmark(BaseModel):
    avgRevenue: Optional[float]
    avgProfitMargin: Optional[float]
    avgSalary: Optional[float]
    avgRevenuePerEmployee: Optional[float]
    positionByRevenue: Optional[PositionByRevenue]


class CompanyBenchmarkData(BaseModel):
    regNumber: str
    name: str
    industryCode: Optional[str]
    industryName: Optional[str]
    dataYear: int
    financials: FinancialData
    workforce: WorkforceData
    trend: Trend
    industryBenchmark: Optional[IndustryBenchmark]


class BenchmarkResponse(BaseModel):
    yearRequested: int
    companies: List[CompanyBenchmarkData]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_company_data_for_year(conn, regcode: str, year: int, max_lookback: int = 5):
    """
    Fetch company data for the specified year, falling back to previous years if needed.
    Returns (data_dict, actual_year) or (None, None) if no data found.
    """
    for y in range(year, year - max_lookback - 1, -1):
        result = conn.execute(text("""
            SELECT 
                c.regcode,
                c.name,
                c.nace_code,
                c.nace_text,
                fr.year,
                fr.turnover,
                fr.profit,
                fr.employees,
                fr.ebitda,
                fr.equity,
                fr.total_assets,
                fr.net_profit_margin,
                fr.roe,
                fr.roa,
                tp.avg_employees,
                tp.total_tax_paid
            FROM companies c
            LEFT JOIN financial_reports fr ON c.regcode = fr.company_regcode AND fr.year = :year
            LEFT JOIN tax_payments tp ON c.regcode = tp.company_regcode AND tp.year = :year
            WHERE c.regcode = :regcode
        """), {"regcode": regcode, "year": y}).fetchone()
        
        if result and result.turnover is not None:
            return dict(result._mapping), y
    
    # If no financial data found, at least return company info
    result = conn.execute(text("""
        SELECT regcode, name, nace_code, nace_text
        FROM companies WHERE regcode = :regcode
    """), {"regcode": regcode}).fetchone()
    
    if result:
        return dict(result._mapping), year
    
    return None, None


def get_company_trends(conn, regcode: str, years: int = 5):
    """Get historical trends for revenue and employees"""
    result = conn.execute(text("""
        SELECT year, turnover, employees
        FROM financial_reports
        WHERE company_regcode = :regcode
        ORDER BY year DESC
        LIMIT :years
    """), {"regcode": regcode, "years": years}).fetchall()
    
    revenue_trend = []
    employee_trend = []
    
    for row in result:
        if row.turnover is not None:
            revenue_trend.append({"year": row.year, "value": float(row.turnover)})
        if row.employees is not None:
            employee_trend.append({"year": row.year, "value": row.employees})
    
    return sorted(revenue_trend, key=lambda x: x['year']), sorted(employee_trend, key=lambda x: x['year'])


def get_industry_benchmarks(conn, industry_code: str, year: int):
    """Get industry aggregate statistics"""
    result = conn.execute(text("""
        SELECT 
            avg_revenue,
            avg_profit_margin,
            avg_salary,
            avg_revenue_per_employee,
            total_companies
        FROM industry_year_aggregates
        WHERE industry_code = :code AND year = :year
    """), {"code": industry_code, "year": year}).fetchone()
    
    if result:
        return dict(result._mapping)
    return None


def get_company_ranking(conn, regcode: str, industry_code: str, year: int):
    """Get company's ranking within its industry"""
    result = conn.execute(text("""
        SELECT revenue_rank, total_companies, revenue_percentile
        FROM company_industry_rankings
        WHERE company_regcode = :regcode 
        AND industry_code = :industry 
        AND year = :year
    """), {"regcode": regcode, "industry": industry_code, "year": year}).fetchone()
    
    if result:
        return {
            "rank": result.revenue_rank,
            "total": result.total_companies,
            "percentile": float(result.revenue_percentile) if result.revenue_percentile else None
        }
    return None


def calculate_profit_margin(profit: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """Calculate profit margin percentage"""
    if profit is not None and revenue is not None and revenue > 0:
        return round((profit / revenue) * 100, 2)
    return None


def calculate_revenue_per_employee(revenue: Optional[float], employees: Optional[int]) -> Optional[float]:
    """Calculate revenue per employee"""
    if revenue is not None and employees is not None and employees > 0:
        return round(revenue / employees, 2)
    return None


def calculate_avg_salary(total_tax: Optional[float], employees: Optional[float]) -> Optional[float]:
    """Estimate average salary from tax data"""
    if total_tax is not None and employees is not None and employees > 0:
        # Rough estimate: divide total labor tax by employee count
        # This is a simplification; actual calculation depends on tax structure
        return round(total_tax / employees, 2)
    return None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/benchmark", response_model=BenchmarkResponse)
def get_benchmark_data(request: BenchmarkRequest, response: Response):
    """
    Get benchmark comparison data for 2-5 companies.
    
    Falls back to previous years (up to 5 years) if data not available for requested year.
    Returns 422 error if fewer than 2 companies have any financial data.
    """
    response.headers["Cache-Control"] = "public, max-age=1800"  # Cache for 30 minutes
    
    logger.info(f"Benchmark request: {len(request.companyRegNumbers)} companies for year {request.year}")
    
    with engine.connect() as conn:
        companies_data = []
        companies_with_data = 0
        
        for regcode in request.companyRegNumbers:
            # Get company data
            company_data, actual_year = get_company_data_for_year(conn, regcode, request.year)
            
            if not company_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Company with registration number {regcode} not found"
                )
            
            # Check if we have financial data
            has_financial_data = company_data.get('turnover') is not None
            if has_financial_data:
                companies_with_data += 1
            
            # Get trends
            revenue_trend, employee_trend = get_company_trends(conn, regcode)
            
            # Calculate metrics
            profit_margin = calculate_profit_margin(
                company_data.get('profit'),
                company_data.get('turnover')
            )
            
            avg_salary = calculate_avg_salary(
                company_data.get('total_tax_paid'),
                company_data.get('avg_employees')
            )
            
            revenue_per_employee = calculate_revenue_per_employee(
                company_data.get('turnover'),
                company_data.get('employees')
            )
            
            # Get industry benchmarks
            industry_benchmark = None
            if company_data.get('nace_code'):
                ind_stats = get_industry_benchmarks(
                    conn,
                    company_data['nace_code'],
                    actual_year
                )
                ranking = get_company_ranking(
                    conn,
                    regcode,
                    company_data['nace_code'],
                    actual_year
                )
                
                if ind_stats or ranking:
                    industry_benchmark = {
                        "avgRevenue": float(ind_stats['avg_revenue']) if ind_stats and ind_stats.get('avg_revenue') else None,
                        "avgProfitMargin": float(ind_stats['avg_profit_margin']) if ind_stats and ind_stats.get('avg_profit_margin') else None,
                        "avgSalary": float(ind_stats['avg_salary']) if ind_stats and ind_stats.get('avg_salary') else None,
                        "avgRevenuePerEmployee": float(ind_stats['avg_revenue_per_employee']) if ind_stats and ind_stats.get('avg_revenue_per_employee') else None,
                        "positionByRevenue": ranking
                    }
            
            # Build company benchmark data
            company_benchmark = {
                "regNumber": regcode,
                "name": company_data['name'],
                "industryCode": company_data.get('nace_code'),
                "industryName": company_data.get('nace_text'),
                "dataYear": actual_year,
                "financials": {
                    "revenue": float(company_data['turnover']) if company_data.get('turnover') else None,
                    "profit": float(company_data['profit']) if company_data.get('profit') else None,
                    "profitMargin": profit_margin,
                    "ebit": None,  # Not available in current schema
                    "ebitda": float(company_data['ebitda']) if company_data.get('ebitda') else None,
                    "assetsTotal": float(company_data['total_assets']) if company_data.get('total_assets') else None,
                    "equityTotal": float(company_data['equity']) if company_data.get('equity') else None,
                    "roe": float(company_data['roe']) if company_data.get('roe') else None,
                    "roa": float(company_data['roa']) if company_data.get('roa') else None
                },
                "workforce": {
                    "employees": company_data.get('employees'),
                    "avgSalary": avg_salary,
                    "revenuePerEmployee": revenue_per_employee
                },
                "trend": {
                    "revenue": revenue_trend,
                    "employees": employee_trend
                },
                "industryBenchmark": industry_benchmark
            }
            
            companies_data.append(company_benchmark)
        
        # Validate that at least 2 companies have data
        if companies_with_data < 2:
            raise HTTPException(
                status_code=422,
                detail=f"Nepietiek datu salīdzināšanai. Vismaz diviem uzņēmumiem jābūt finanšu datiem. Atrasti tikai {companies_with_data} uzņēmumi ar datiem."
            )
        
        return {
            "yearRequested": request.year,
            "companies": companies_data
        }


@router.post("/benchmark/session")
def save_benchmark_session(request: SaveSessionRequest):
    """
    Save a benchmark session and return a shareable URL.
    """
    session_id = uuid.uuid4()
    company_ids_str = ",".join(request.companyRegNumbers)
    
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO benchmark_sessions (id, year, company_ids, source)
            VALUES (:id, :year, :company_ids, :source)
        """), {
            "id": str(session_id),
            "year": request.year,
            "company_ids": company_ids_str,
            "source": request.source
        })
        conn.commit()
    
    logger.info(f"Saved benchmark session: {session_id}")
    
    return {
        "sessionId": str(session_id),
        "shareUrl": f"/benchmark?s={session_id}"
    }


@router.get("/benchmark/session/{session_id}")
def get_benchmark_session(session_id: str, response: Response):
    """
    Load a saved benchmark session and return the comparison data.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    with engine.connect() as conn:
        session = conn.execute(text("""
            SELECT year, company_ids
            FROM benchmark_sessions
            WHERE id = :id
        """), {"id": str(session_uuid)}).fetchone()
        
        if not session:
            raise HTTPException(status_code=404, detail="Benchmark session not found")
        
        # Parse company IDs and create benchmark request
        company_reg_numbers = session.company_ids.split(',')
        
        request = BenchmarkRequest(
            companyRegNumbers=company_reg_numbers,
            year=session.year
        )
        
        # Return benchmark data using the main endpoint logic
        return get_benchmark_data(request, response)
