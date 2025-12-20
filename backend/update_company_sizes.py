#!/usr/bin/env python3
"""
Calculate and cache company sizes (EU SME classification) for all companies.
Also tracks historical size changes year-by-year in company_size_history table.

This script:
1. Auto-creates necessary tables and columns
2. Calculates size based on latest financial data (employees + turnover)
3. Stores historical size per year
4. Detects recent size category changes
5. Updates companies.company_size_badge for fast API access
"""

import sys
import os
from sqlalchemy import create_engine, text
from decimal import Decimal
import logging
from etl.loader import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)

def migrate_company_size_tables():
    """Auto-create company size tables and columns if they don't exist"""
    logger.info("Checking/creating company size database schema...")
    
    with engine.connect() as conn:
        try:
            # Add columns to companies table
            conn.execute(text("""
                ALTER TABLE companies 
                ADD COLUMN IF NOT EXISTS company_size_badge VARCHAR(20),
                ADD COLUMN IF NOT EXISTS latest_size_year INTEGER,
                ADD COLUMN IF NOT EXISTS size_changed_recently BOOLEAN DEFAULT FALSE
            """))
            
            # Create company_size_history table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS company_size_history (
                    id SERIAL PRIMARY KEY,
                    company_regcode BIGINT NOT NULL,
                    year INTEGER NOT NULL,
                    size_category VARCHAR(20) NOT NULL,
                    employees INTEGER,
                    turnover NUMERIC(15,2),
                    total_assets NUMERIC(15,2),
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_regcode, year)
                )
            """))
            
            # Add missing columns to existing table (if table was created before)
            conn.execute(text("""
                ALTER TABLE company_size_history 
                ADD COLUMN IF NOT EXISTS total_assets NUMERIC(15,2)
            """))
            conn.execute(text("""
                ALTER TABLE company_size_history 
                ADD COLUMN IF NOT EXISTS calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            
            # Add indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_company_size_badge 
                ON companies(company_size_badge)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_company_size_history_regcode 
                ON company_size_history(company_regcode)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_company_size_history_year 
                ON company_size_history(year)
            """))
            
            conn.commit()
            logger.info("✅ Company size schema ready")
            
        except Exception as e:
            logger.warning(f"Migration warning (may be safe to ignore): {e}")
def calculate_size(employees: int, turnover: float, assets: float) -> str:
    """EU SME Classification"""
    employees = employees or 0
    turnover = turnover or 0
    assets = assets or 0
    
    if employees == 0 and turnover == 0 and assets == 0:
        return None
    
    if employees < 10 and (turnover <= 2_000_000 or assets <= 2_000_000):
        return "Mikro"
    elif employees < 50 and (turnover <= 10_000_000 or assets <= 10_000_000):
        return "Mazs"
    elif employees < 250 and (turnover <= 50_000_000 or assets <= 43_000_000):
        return "Vidējs"
    else:
        return "Liels"

def process_company_sizes():
    """Main processing function"""
    
    # Auto-migrate database schema
    migrate_company_size_tables()
    
    logger.info("Starting company size calculation...")
    
    with engine.connect() as conn:
        # Get all financial reports with year-by-year data
        query = text("""
            SELECT 
                f.company_regcode,
                f.year,
                f.employees,
                f.turnover,
                f.total_assets,
                c.employee_count as vid_employees
            FROM financial_reports f
            JOIN companies c ON c.regcode = f.company_regcode
            WHERE f.year >= 2020  -- Only recent years
            ORDER BY f.company_regcode, f.year
        """)
        
        rows = conn.execute(query).fetchall()
        logger.info(f"Processing {len(rows)} financial reports...")
        
        # Calculate size for each year
        history_records = []
        for row in rows:
            # Prefer VID employee data for latest year, otherwise use financial report
            employees = row.employees or 0
            if row.year == 2024:  # Latest year - prefer VID data
                employees = row.vid_employees or row.employees or 0
            
            turnover = float(row.turnover) if row.turnover else 0
            assets = float(row.total_assets) if row.total_assets else 0
            
            size = calculate_size(employees, turnover, assets)
            
            # SKIP records where size is None (no meaningful data for classification)
            if size is None:
                continue
            
            history_records.append({
                "regcode": row.company_regcode,
                "year": row.year,
                "size": size,
                "employees": employees,
                "turnover": turnover,
                "assets": assets
            })
        
        # Insert/update history (upsert)
        logger.info(f"Upserting {len(history_records)} size history records...")
        for record in history_records:
            conn.execute(text("""
                INSERT INTO company_size_history 
                    (company_regcode, year, size_category, employees, turnover, total_assets)
                VALUES (:regcode, :year, :size, :employees, :turnover, :assets)
                ON CONFLICT (company_regcode, year) 
                DO UPDATE SET 
                    size_category = EXCLUDED.size_category,
                    employees = EXCLUDED.employees,
                    turnover = EXCLUDED.turnover,
                    total_assets = EXCLUDED.total_assets,
                    calculated_at = NOW()
            """), record)
        
        conn.commit()
        
        # Detect size changes in last year
        logger.info("Detecting recent size changes...")
        conn.execute(text("""
            WITH size_changes AS (
                SELECT 
                    company_regcode,
                    size_category,
                    LAG(size_category) OVER (PARTITION BY company_regcode ORDER BY year) as prev_size,
                    year
                FROM company_size_history
                WHERE year >= (SELECT MAX(year) - 1 FROM company_size_history)
            )
            UPDATE companies c
            SET 
                company_size_badge = (
                    SELECT size_category 
                    FROM company_size_history 
                    WHERE company_regcode = c.regcode 
                    ORDER BY year DESC LIMIT 1
                ),
                latest_size_year = (
                    SELECT year 
                    FROM company_size_history 
                    WHERE company_regcode = c.regcode 
                    ORDER BY year DESC LIMIT 1
                ),
                size_changed_recently = EXISTS (
                    SELECT 1 FROM size_changes sc
                    WHERE sc.company_regcode = c.regcode
                    AND sc.size_category IS DISTINCT FROM sc.prev_size
                    AND sc.prev_size IS NOT NULL
                )
        """))
        conn.commit()
        
        # Calculate size for each report
        reports = conn.execute(text("""
            SELECT 
                company_regcode as regcode,
                year,
                employees,
                turnover,
                total_assets as assets
            FROM financial_reports
            WHERE employees IS NOT NULL 
               OR turnover IS NOT NULL 
               OR total_assets IS NOT NULL
            ORDER BY company_regcode, year DESC
        """)).fetchall()
        
        logger.info(f"Processing {len(reports)} financial reports...")
        
        # Calculate sizes
        size_data = []
        for r in reports:
            size = calculate_size(r.employees or 0, r.turnover or 0, r.assets or 0)
            # SKIP if size is None (no meaningful data)
            if size is not None:
                size_data.append({
                    'regcode': r.regcode,
                    'year': r.year,
                    'size': size,
                    'employees': r.employees or 0,
                    'turnover': r.turnover or 0,
                    'assets': r.assets or 0
                })
        
        logger.info(f"Upserting {len(size_data)} size history records...")
        
        # Batch upserthat changed size
        changed = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM companies
            WHERE size_changed_recently = TRUE
        """)).fetchone()
        
        # Statistics
        stats = conn.execute(text("""
            SELECT 
                year,
                size_category,
                COUNT(*) as count
            FROM company_size_history
            WHERE size_category IS NOT NULL
            GROUP BY year, size_category
            ORDER BY year DESC, count DESC
        """)).fetchall()
        
        logger.info("✅ Size history update complete!")
        logger.info("\nDistribution by year:")
        current_year = None
        for stat in stats:
            if stat.year != current_year:
                current_year = stat.year
                logger.info(f"\n{stat.year}:")
            logger.info(f"  {stat.size_category}: {stat.count}")
        
        # Companies that changed size
        changed = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM companies
            WHERE size_changed_recently = TRUE
        """)).fetchone()
        
        logger.info(f"\n🔄 Companies with size changes in last year: {changed.count}")

if __name__ == "__main__":
    process_company_sizes()
