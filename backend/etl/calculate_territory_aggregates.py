"""
ETL Script: Calculate Territory Economic Aggregates

Calculates and stores pre-computed economic indicators for each territory:
- Total revenue, profit, employees
- Average salary
- Company count
- Year-over-year growth rates
- Industry breakdown

Run this script:
- Initially: python backend/etl/calculate_territory_aggregates.py
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


def calculate_territory_year_aggregates(conn, year: int = None):
    """
    Calculate economic aggregates for each territory
    
    Args:
        conn: Database connection
        year: Specific year to process, or None for all years
    
    Returns:
        Number of records updated/inserted
    """
    year_filter = "AND fr.year = :year" if year else ""
    year_param = {"year": year} if year else {}
    
    logger.info(f"📊 Calculating territory aggregates for year: {year or 'all years'}")
    
    sql = f"""
    INSERT INTO territory_year_aggregates (
        territory_id, year,
        total_revenue, total_profit, total_employees,
        avg_salary, company_count
    )
    SELECT 
        t.id AS territory_id,
        COALESCE(fr.year, {year or 2024}) as year,
        SUM(CASE WHEN fr.turnover = 'NaN'::float OR fr.turnover > 1e15 THEN 0 ELSE fr.turnover END) AS total_revenue,
        SUM(CASE WHEN fr.profit = 'NaN'::float OR fr.profit > 1e15 THEN 0 ELSE fr.profit END) AS total_profit,
        SUM(CASE WHEN fr.employees > 1000000 THEN 0 ELSE fr.employees END) AS total_employees,
        AVG(CASE WHEN cm.avg_gross_salary = 'NaN'::float OR cm.avg_gross_salary > 100000 THEN NULL ELSE cm.avg_gross_salary END) AS avg_salary,
        COUNT(DISTINCT c.regcode) AS company_count
    FROM companies c
    JOIN companies_with_address cwa ON c.regcode = cwa.regcode
    JOIN territories t ON (
        (t.level = 3 AND (t.name = cwa.city_name OR t.name = cwa.parish_name)) OR
        (t.level = 2 AND (t.name = cwa.city_name OR t.name = cwa.municipality_name))
    )
    -- Left join to include companies without reports in the count
    LEFT JOIN financial_reports fr ON c.regcode = fr.company_regcode AND fr.year = {year or 2024}
    LEFT JOIN company_computed_metrics cm 
        ON c.regcode = cm.company_regcode AND fr.year = cm.year
    WHERE (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
      AND (t.valid_to IS NULL OR t.valid_to > NOW())
    GROUP BY t.id, COALESCE(fr.year, {year or 2024})
    
    ON CONFLICT (territory_id, year)
    DO UPDATE SET
        total_revenue = EXCLUDED.total_revenue,
        total_profit = EXCLUDED.total_profit,
        total_employees = EXCLUDED.total_employees,
        avg_salary = EXCLUDED.avg_salary,
        company_count = EXCLUDED.company_count,
        computed_at = NOW()
    """
    
    result = conn.execute(text(sql), year_param)
    count = result.rowcount
    logger.info(f"✅ Updated/inserted {count} territory-year records")
    
    return count


def calculate_growth_rates(conn):
    """
    Calculate year-over-year growth rates for all territories
    """
    logger.info("📈 Calculating YoY growth rates...")
    
    sql = """
    UPDATE territory_year_aggregates tya
    SET 
        revenue_growth_yoy = CASE 
            WHEN prev.total_revenue > 0 
            THEN ROUND(((tya.total_revenue - prev.total_revenue) / prev.total_revenue * 100)::NUMERIC, 2)
            ELSE NULL
        END,
        employee_growth_yoy = CASE 
            WHEN prev.total_employees > 0 
            THEN ROUND(((tya.total_employees - prev.total_employees)::NUMERIC / prev.total_employees * 100)::NUMERIC, 2)
            ELSE NULL
        END,
        salary_growth_yoy = CASE 
            WHEN prev.avg_salary > 0 
            THEN ROUND(((tya.avg_salary - prev.avg_salary) / prev.avg_salary * 100)::NUMERIC, 2)
            ELSE NULL
        END
    FROM territory_year_aggregates prev
    WHERE prev.territory_id = tya.territory_id
      AND prev.year = tya.year - 1
    """
    
    result = conn.execute(text(sql))
    count = result.rowcount
    logger.info(f"✅ Calculated growth rates for {count} records")
    
    return count


def calculate_territory_industry_aggregates(conn, year: int = None):
    """
    Calculate industry breakdown for each territory
    """
    year_filter = "AND fr.year = :year" if year else ""
    year_param = {"year": year} if year else {}
    
    logger.info(f"🏭 Calculating territory-industry aggregates for year: {year or 'all years'}")
    
    sql = f"""
    INSERT INTO territory_industry_year_aggregates (
        territory_id, industry_code, industry_name, year,
        total_revenue, total_profit, total_employees, company_count
    )
    SELECT 
        t.id AS territory_id,
        c.nace_code AS industry_code,
        c.nace_text AS industry_name,
        fr.year,
        SUM(CASE WHEN fr.turnover = 'NaN'::float OR fr.turnover > 1e15 THEN 0 ELSE fr.turnover END) AS total_revenue,
        SUM(CASE WHEN fr.profit = 'NaN'::float OR fr.profit > 1e15 THEN 0 ELSE fr.profit END) AS total_profit,
        SUM(CASE WHEN fr.employees > 1000000 THEN 0 ELSE fr.employees END) AS total_employees,
        COUNT(DISTINCT c.regcode) AS company_count
    FROM companies c
    JOIN companies_with_address cwa ON c.regcode = cwa.regcode
    JOIN territories t ON (
        (t.level = 3 AND (t.name = cwa.city_name OR t.name = cwa.parish_name)) OR
        (t.level = 2 AND (t.name = cwa.city_name OR t.name = cwa.municipality_name))
    )
    INNER JOIN financial_reports fr ON c.regcode = fr.company_regcode
    WHERE (c.status IS NULL OR c.status = '' OR c.status IN ('active', 'A', 'AKTĪVS', 'reģistrēts'))
      AND (t.valid_to IS NULL OR t.valid_to > NOW())
      AND c.nace_code IS NOT NULL
      {year_filter}
    GROUP BY t.id, c.nace_code, c.nace_text, fr.year
    
    ON CONFLICT (territory_id, industry_code, year)
    DO UPDATE SET
        industry_name = EXCLUDED.industry_name,
        total_revenue = EXCLUDED.total_revenue,
        total_profit = EXCLUDED.total_profit,
        total_employees = EXCLUDED.total_employees,
        company_count = EXCLUDED.company_count,
        computed_at = NOW()
    """
    
    result = conn.execute(text(sql), year_param)
    count = result.rowcount
    logger.info(f"✅ Updated/inserted {count} territory-industry records")
    
    return count


def run_territory_aggregates_etl(year: int = None):
    """
    Main function to run the territory aggregates ETL process
    
    Args:
        year: Specific year to process, or None for all years
    """
    engine = create_engine(DATABASE_URL)
    
    logger.info("=" * 60)
    logger.info("TERRITORY AGGREGATES ETL PROCESS STARTED")
    logger.info("=" * 60)
    start_time = datetime.now()
    
    try:
        with engine.connect() as conn:
            # Step 1: Calculate territory-year aggregates
            territory_count = calculate_territory_year_aggregates(conn, year)
            
            # Step 2: Calculate growth rates
            growth_count = calculate_growth_rates(conn)
            
            # Step 3: Calculate industry breakdown
            industry_count = calculate_territory_industry_aggregates(conn, year)
            
            # Commit transaction
            conn.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ TERRITORY AGGREGATES ETL PROCESS COMPLETED")
            logger.info(f"   Territory-year records: {territory_count}")
            logger.info(f"   Growth rates calculated: {growth_count}")
            logger.info(f"   Territory-industry records: {industry_count}")
            logger.info(f"   Time elapsed: {elapsed:.2f} seconds")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"❌ ETL process failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    # Allow specifying year as command line argument
    year = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    run_territory_aggregates_etl(year)
