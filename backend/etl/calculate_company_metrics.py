"""
ETL Script: Calculate and Store Pre-computed Company Metrics

This script populates the company_computed_metrics table with pre-calculated values
to improve company profile page performance.

Metrics calculated:
- avg_gross_salary: Monthly gross salary from VSAOI (social tax)
- avg_net_salary: Monthly net salary after deductions
- profit_margin: (profit / revenue) * 100
- revenue_per_employee: revenue / employees
- total_risk_score: Sum of active risk scores
- has_active_risks: Boolean flag for active risks

Run this script:
- Initially: python backend/etl/calculate_company_metrics.py
- Scheduled: Daily at 3 AM via cron
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

# Tax and salary calculation constants
VSAOI_RATE = 0.3409  # Social tax rate in Latvia (34.09%)
VSAOI_EMPLOYEE_RATE = 0.105  # Employee's portion of social tax (10.5%)
IIN_RATE = 0.20  # Personal income tax rate (20%)


def calculate_company_metrics(conn, year: int = None):
    """
    Calculate and store pre-computed metrics for companies.
    
    Args:
        conn: Database connection
        year: Specific year to process, or None for all years
    
    Returns:
        Number of records updated/inserted
    """
    year_filter = "AND fr.year = :year" if year else ""
    year_param = {"year": year} if year else {}
    
    logger.info(f"📊 Calculating company metrics for year: {year or 'all years'}")
    
    sql = f"""
    INSERT INTO company_computed_metrics (
        company_regcode, year,
        avg_gross_salary, avg_net_salary,
        profit_margin, revenue_per_employee,
        total_risk_score, has_active_risks
    )
    SELECT 
        c.regcode,
        fr.year,
        
        -- Salary calculations from VSAOI
        CASE 
            WHEN tp.social_tax_vsaoi IS NOT NULL 
             AND tp.avg_employees IS NOT NULL 
             AND tp.avg_employees > 0
            THEN ROUND(
                (tp.social_tax_vsaoi / {VSAOI_RATE}) / tp.avg_employees / 12, 
                2
            )
            ELSE NULL
        END as avg_gross_salary,
        
        CASE 
            WHEN tp.social_tax_vsaoi IS NOT NULL 
             AND tp.avg_employees IS NOT NULL 
             AND tp.avg_employees > 0
            THEN ROUND(
                ((tp.social_tax_vsaoi / {VSAOI_RATE}) / tp.avg_employees / 12) * 
                (1 - {VSAOI_EMPLOYEE_RATE} - {IIN_RATE} * (1 - {VSAOI_EMPLOYEE_RATE})),
                2
            )
            ELSE NULL
        END as avg_net_salary,
        
        -- Financial ratios
        CASE 
            WHEN fr.turnover IS NOT NULL AND fr.turnover > 0 AND fr.profit IS NOT NULL
            THEN ROUND((fr.profit / fr.turnover) * 100, 2)
            ELSE NULL
        END as profit_margin,
        
        CASE 
            WHEN fr.turnover IS NOT NULL AND fr.employees IS NOT NULL AND fr.employees > 0
            THEN ROUND(fr.turnover / fr.employees, 2)
            ELSE NULL
        END as revenue_per_employee,
        
        -- Risk aggregates
        COALESCE(
            (SELECT SUM(risk_score) 
             FROM risks 
             WHERE company_regcode = c.regcode AND active = TRUE), 
            0
        ) as total_risk_score,
        
        EXISTS(
            SELECT 1 FROM risks 
            WHERE company_regcode = c.regcode AND active = TRUE
        ) as has_active_risks
        
    FROM companies c
    INNER JOIN financial_reports fr ON c.regcode = fr.company_regcode
    LEFT JOIN tax_payments tp ON c.regcode = tp.company_regcode AND fr.year = tp.year
    WHERE c.status = 'active'
      AND fr.year IS NOT NULL
      {year_filter}
    
    ON CONFLICT (company_regcode, year)
    DO UPDATE SET
        avg_gross_salary = EXCLUDED.avg_gross_salary,
        avg_net_salary = EXCLUDED.avg_net_salary,
        profit_margin = EXCLUDED.profit_margin,
        revenue_per_employee = EXCLUDED.revenue_per_employee,
        total_risk_score = EXCLUDED.total_risk_score,
        has_active_risks = EXCLUDED.has_active_risks,
        computed_at = NOW(),
        data_version = company_computed_metrics.data_version + 1
    """
    
    result = conn.execute(text(sql), year_param)
    count = result.rowcount
    logger.info(f"✅ Updated/inserted {count} company-year metric records")
    
    return count


def run_metrics_etl(year: int = None):
    """
    Main function to run the company metrics ETL process.
    
    Args:
        year: Specific year to process, or None for all years
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("COMPANY METRICS ETL PROCESS STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        with engine.connect() as conn:
            # Calculate and store metrics
            count = calculate_company_metrics(conn, year)
            
            # Commit transaction
            conn.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ COMPANY METRICS ETL PROCESS COMPLETED")
            logger.info(f"   Records processed: {count}")
            logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"❌ ETL process failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    # Allow specifying year as command line argument
    year = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    run_metrics_etl(year)
