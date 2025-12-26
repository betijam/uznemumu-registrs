"""
ETL Script: Calculate Industry Aggregates and Company Rankings

This script populates:
1. industry_year_aggregates - Pre-computed industry statistics per year
2. company_industry_rankings - Company rankings within their industry

Run this script after importing financial data to enable fast benchmark queries.
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")


def calculate_industry_aggregates(conn, year: int = None):
    """
    Calculate and store industry aggregate statistics.
    
    If year is None, calculates for all available years.
    """
    logger.info(f"📊 Calculating industry aggregates for year: {year or 'all years'}")
    
    year_filter = "AND fr.year = :year" if year else ""
    year_param = {"year": year} if year else {}
    
    # Calculate aggregates
    sql = f"""
    INSERT INTO industry_year_aggregates (
        industry_code,
        year,
        avg_revenue,
        median_revenue,
        avg_profit,
        avg_profit_margin,
        avg_employees,
        avg_salary,
        avg_revenue_per_employee,
        total_companies,
        profitable_companies,
        revenue_p25,
        revenue_p50,
        revenue_p75,
        revenue_p90,
        updated_at
    )
    SELECT 
        c.nace_code AS industry_code,
        fr.year,
        AVG(fr.turnover) AS avg_revenue,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fr.turnover) AS median_revenue,
        AVG(fr.profit) AS avg_profit,
        AVG(CASE 
            WHEN fr.turnover > 0 THEN (fr.profit / fr.turnover) * 100 
            ELSE NULL 
        END) AS avg_profit_margin,
        AVG(fr.employees) AS avg_employees,
        AVG(
            CASE 
                WHEN tp.avg_employees > 0 THEN tp.total_tax_paid / tp.avg_employees 
                ELSE NULL 
            END
        ) AS avg_salary,
        AVG(
            CASE 
                WHEN fr.employees > 0 THEN fr.turnover / fr.employees 
                ELSE NULL 
            END
        ) AS avg_revenue_per_employee,
        COUNT(DISTINCT c.regcode) AS total_companies,
        COUNT(DISTINCT CASE WHEN fr.profit > 0 THEN c.regcode END) AS profitable_companies,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fr.turnover) AS revenue_p25,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fr.turnover) AS revenue_p50,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fr.turnover) AS revenue_p75,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY fr.turnover) AS revenue_p90,
        NOW() AS updated_at
    FROM companies c
    INNER JOIN financial_reports fr ON c.regcode = fr.company_regcode
    LEFT JOIN tax_payments tp ON c.regcode = tp.company_regcode AND fr.year = tp.year
    WHERE c.status = 'active'
      AND c.nace_code IS NOT NULL
      AND fr.turnover IS NOT NULL
      {year_filter}
    GROUP BY c.nace_code, fr.year
    ON CONFLICT (industry_code, year) 
    DO UPDATE SET
        avg_revenue = EXCLUDED.avg_revenue,
        median_revenue = EXCLUDED.median_revenue,
        avg_profit = EXCLUDED.avg_profit,
        avg_profit_margin = EXCLUDED.avg_profit_margin,
        avg_employees = EXCLUDED.avg_employees,
        avg_salary = EXCLUDED.avg_salary,
        avg_revenue_per_employee = EXCLUDED.avg_revenue_per_employee,
        total_companies = EXCLUDED.total_companies,
        profitable_companies = EXCLUDED.profitable_companies,
        revenue_p25 = EXCLUDED.revenue_p25,
        revenue_p50 = EXCLUDED.revenue_p50,
        revenue_p75 = EXCLUDED.revenue_p75,
        revenue_p90 = EXCLUDED.revenue_p90,
        updated_at = NOW()
    """
    
    result = conn.execute(text(sql), year_param)
    count = result.rowcount
    logger.info(f"✅ Updated {count} industry-year combinations")
    
    return count


def calculate_company_rankings(conn, year: int = None):
    """
    Calculate and store company rankings within their industries.
    
    If year is None, calculates for all available years.
    """
    logger.info(f"🏆 Calculating company rankings for year: {year or 'all years'}")
    
    year_filter = "AND fr.year = :year" if year else ""
    year_param = {"year": year} if year else {}
    
    # First, create a temporary table with rankings
    sql = f"""
    WITH company_industry_data AS (
        SELECT 
            c.regcode AS company_regcode,
            c.nace_code AS industry_code,
            fr.year,
            fr.turnover AS revenue,
            fr.profit,
            fr.employees,
            COUNT(*) OVER (PARTITION BY c.nace_code, fr.year) AS total_companies,
            RANK() OVER (PARTITION BY c.nace_code, fr.year ORDER BY fr.turnover DESC NULLS LAST) AS revenue_rank,
            RANK() OVER (PARTITION BY c.nace_code, fr.year ORDER BY fr.profit DESC NULLS LAST) AS profit_rank,
            RANK() OVER (PARTITION BY c.nace_code, fr.year ORDER BY fr.employees DESC NULLS LAST) AS employee_rank,
            PERCENT_RANK() OVER (PARTITION BY c.nace_code, fr.year ORDER BY fr.turnover DESC NULLS LAST) AS revenue_pct_rank,
            PERCENT_RANK() OVER (PARTITION BY c.nace_code, fr.year ORDER BY fr.profit DESC NULLS LAST) AS profit_pct_rank
        FROM companies c
        INNER JOIN financial_reports fr ON c.regcode = fr.company_regcode
        WHERE c.status = 'active'
          AND c.nace_code IS NOT NULL
          AND fr.turnover IS NOT NULL
          {year_filter}
    )
    INSERT INTO company_industry_rankings (
        company_regcode,
        industry_code,
        year,
        revenue_rank,
        profit_rank,
        employee_rank,
        total_companies,
        revenue_percentile,
        profit_percentile,
        updated_at
    )
    SELECT 
        company_regcode,
        industry_code,
        year,
        revenue_rank,
        profit_rank,
        employee_rank,
        total_companies,
        ROUND(((1 - revenue_pct_rank) * 100)::NUMERIC, 2) AS revenue_percentile,
        ROUND(((1 - profit_pct_rank) * 100)::NUMERIC, 2) AS profit_percentile,
        NOW() AS updated_at
    FROM company_industry_data
    ON CONFLICT (company_regcode, industry_code, year)
    DO UPDATE SET
        revenue_rank = EXCLUDED.revenue_rank,
        profit_rank = EXCLUDED.profit_rank,
        employee_rank = EXCLUDED.employee_rank,
        total_companies = EXCLUDED.total_companies,
        revenue_percentile = EXCLUDED.revenue_percentile,
        profit_percentile = EXCLUDED.profit_percentile,
        updated_at = NOW()
    """
    
    result = conn.execute(text(sql), year_param)
    count = result.rowcount
    logger.info(f"✅ Updated {count} company rankings")
    
    return count


def run_benchmark_etl(year: int = None):
    """
    Main function to run all benchmark ETL processes.
    
    Args:
        year: Specific year to process, or None for all years
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("BENCHMARK ETL PROCESS STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        with engine.connect() as conn:
            # Step 1: Calculate industry aggregates
            logger.info("\n📊 Step 1: Calculating industry aggregates...")
            agg_count = calculate_industry_aggregates(conn, year)
            
            # Step 2: Calculate company rankings
            logger.info("\n🏆 Step 2: Calculating company rankings...")
            rank_count = calculate_company_rankings(conn, year)
            
            # Commit transaction
            conn.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ BENCHMARK ETL PROCESS COMPLETED")
            logger.info(f"   Industry aggregates updated: {agg_count}")
            logger.info(f"   Company rankings updated: {rank_count}")
            logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"❌ ETL process failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    # Allow specifying year as command line argument
    year = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    run_benchmark_etl(year)
