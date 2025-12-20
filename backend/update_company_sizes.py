#!/usr/bin/env python3
"""
Update company_size_badge column with EU classification

Run this to pre-calculate company sizes in database for faster API responses.
Can be run:
- Manually via: python update_company_sizes.py
- As part of ETL process
- Via cron job (weekly recommended)
"""

import logging
from sqlalchemy import text
from etl.loader import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def update_company_sizes():
    """Update company_size_badge for all companies with financial data"""
    logger.info("Starting company size calculation...")
    
    with engine.connect() as conn:
        # Get all companies with latest financial data
        query = text("""
            SELECT 
                c.regcode,
                c.employee_count as vid_employees,
                f.employees as fin_employees,
                f.turnover,
                f.total_assets
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT employees, turnover, total_assets
                FROM financial_reports
                WHERE company_regcode = c.regcode
                ORDER BY year DESC
                LIMIT 1
            ) f ON true
        """)
        
        rows = conn.execute(query).fetchall()
        logger.info(f"Processing {len(rows)} companies...")
        
        updates = []
        for row in rows:
            # Prefer VID employee data, fallback to financial reports
            employees = row.vid_employees or row.fin_employees or 0
            turnover = float(row.turnover) if row.turnover else 0
            assets = float(row.total_assets) if row.total_assets else 0
            
            size = calculate_size(employees, turnover, assets)
            updates.append((size, row.regcode))
        
        # Batch update
        logger.info(f"Updating {len(updates)} company sizes...")
        conn.execute(
            text("UPDATE companies SET company_size_badge = :size WHERE regcode = :regcode"),
            [{"size": size, "regcode": regcode} for size, regcode in updates]
        )
        conn.commit()
        
        # Statistics
        stats = conn.execute(text("""
            SELECT company_size_badge, COUNT(*) as count
            FROM companies
            WHERE company_size_badge IS NOT NULL
            GROUP BY company_size_badge
            ORDER BY count DESC
        """)).fetchall()
        
        logger.info("✅ Company size update complete!")
        logger.info("Distribution:")
        for stat in stats:
            logger.info(f"  {stat.company_size_badge}: {stat.count}")

if __name__ == "__main__":
    update_company_sizes()
