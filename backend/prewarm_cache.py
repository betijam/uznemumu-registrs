
import sys
import os
import time
import json
import logging
from sqlalchemy import text

# Add current directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routers.companies import engine, build_full_profile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("prewarmer")

def prewarm():
    logger.info("Starting cache pre-warming...")
    
    # 1. Create table if not exists (safer)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS company_profile_cache (
                company_regcode BIGINT PRIMARY KEY,
                profile_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

    # 2. Get list of active companies (prioritize active ones)
    # Fetch top 2000 active companies by turnover
    with engine.connect() as conn:
        logger.info("Fetching top 2000 active companies by turnover...")
        # Check if financial_reports table exists and has turnover
        # Assuming it does based on previous knowledge
        rows = conn.execute(text("""
            SELECT c.regcode, c.name, fr.turnover 
            FROM companies c
            LEFT JOIN financial_reports fr ON c.regcode = fr.company_regcode AND fr.year = 2023
            WHERE c.status = 'active'
            ORDER BY fr.turnover DESC NULLS LAST
            LIMIT 2000
        """)).fetchall()

    logger.info(f"Found {len(rows)} companies to cache.")

    count = 0
    updated_count = 0
    skipped_count = 0
    errors_count = 0

    for row in rows:
        regcode = row.regcode
        count += 1
        
        # Check if already cached within 24h
        with engine.connect() as conn:
            cached = conn.execute(text("""
                SELECT 1 FROM company_profile_cache 
                WHERE company_regcode = :r 
                AND updated_at > NOW() - INTERVAL '24 HOURS'
            """), {"r": regcode}).fetchone()
        
        if cached:
            # logger.info(f"Skipping {regcode} ({row.name}) - already cached")
            skipped_count += 1
            if count % 100 == 0:
                logger.info(f"Processed {count}/{len(rows)}...")
            continue
            
        try:
            # Build profile
            start = time.time()
            
            # Recreate base_company_info as detailed in companies.py
            with engine.connect() as conn:
                res = conn.execute(text("SELECT * FROM companies WHERE regcode = :r"), {"r": regcode}).fetchone()
                if not res:
                    continue
                
                company = {
                    "regcode": res.regcode,
                    "name": res.name,
                    "name_in_quotes": res.name_in_quotes if hasattr(res, 'name_in_quotes') else None,
                    "type": res.type if hasattr(res, 'type') else None,
                    "type_text": res.type_text if hasattr(res, 'type_text') else None,
                    "addressid": res.addressid if hasattr(res, 'addressid') else None,
                    "address": res.address,
                    "registration_date": str(res.registration_date),
                    "status": res.status,
                    "sepa_identifier": res.sepa_identifier,
                    "pvn_number": res.pvn_number if hasattr(res, 'pvn_number') else None,
                    "is_pvn_payer": res.is_pvn_payer if hasattr(res, 'is_pvn_payer') else False,
                    "company_size_badge": res.company_size_badge if hasattr(res, 'company_size_badge') else None,
                    "latest_size_year": res.latest_size_year if hasattr(res, 'latest_size_year') else None,
                    "size_changed_recently": res.size_changed_recently if hasattr(res, 'size_changed_recently') else False,
                    "nace_code": res.nace_code,
                    "nace_text": res.nace_text,
                    "nace_section": res.nace_section,
                    "nace_section_text": res.nace_section_text,
                    "employee_count": res.employee_count,
                    "tax_data_year": res.tax_data_year
                }

            # This is the heavy calculation
            full_profile = build_full_profile(regcode, company)
            
            # Save to DB
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO company_profile_cache (company_regcode, profile_data, updated_at) 
                    VALUES (:r, :d, NOW()) 
                    ON CONFLICT (company_regcode) 
                    DO UPDATE SET profile_data = :d, updated_at = NOW()
                """), {"r": regcode, "d": json.dumps(full_profile, default=str)})
                conn.commit()
            
            elapsed = time.time() - start
            logger.info(f"Cached {regcode} ({row.name}) in {elapsed:.2f}s")
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to cache {regcode}: {e}")
            errors_count += 1
        
        if count % 100 == 0:
            logger.info(f"Processed {count}/{len(rows)}...")

    logger.info(f"Finished pre-warming. Updated: {updated_count}, Skipped: {skipped_count}, Errors: {errors_count}")

if __name__ == "__main__":
    prewarm()
