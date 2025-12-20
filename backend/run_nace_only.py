#!/usr/bin/env python3
"""
Standalone NACE Classification Runner

Run ONLY the NACE industry classification without other ETL processes.
This is useful for:
- Initial NACE data load after migration
- Re-processing NACE after dictionary updates
- Fixing NACE data without full ETL

Usage:
    python run_nace_only.py
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run NACE classification only"""
    logger.info("=" * 60)
    logger.info("NACE CLASSIFICATION - STANDALONE RUN")
    logger.info("=" * 60)
    
    try:
        # Import after adding parent to path
        from etl.process_nace import process_nace
        from etl.config import VID_URLS
        import pandas as pd
        
        # 1. Find NACE.csv
        logger.info("Step 1: Locating NACE.csv...")
        current_dir = Path(__file__).parent
        possible_paths = [
            current_dir / 'NACE.csv',  # backend/NACE.csv
            current_dir.parent / 'NACE.csv',  # root/NACE.csv
            Path('/app/NACE.csv'),  # Railway/Docker
        ]
        
        nace_path = None
        for path in possible_paths:
            if path.exists():
                nace_path = str(path.absolute())
                logger.info(f"✅ Found NACE.csv at: {nace_path}")
                break
        
        if not nace_path:
            logger.error(f"❌ NACE.csv not found. Searched: {[str(p) for p in possible_paths]}")
            sys.exit(1)
        
        # 2. Download VID tax data
        logger.info("Step 2: Downloading VID tax data...")
        url = VID_URLS["tax_payments"]
        logger.info(f"Downloading from: {url}")
        
        try:
            df_temp = pd.read_csv(url, sep=',', dtype=str, on_bad_lines='skip')
            if df_temp.shape[1] < 5:
                df_temp = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
        except:
            df_temp = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
        
        logger.info(f"Downloaded {len(df_temp)} VID records")
        
        # 3. Save to temp file
        logger.info("Step 3: Saving temporary VID data...")
        temp_dir = Path('/tmp/etl_data')
        temp_dir.mkdir(parents=True, exist_ok=True)
        vid_path = str(temp_dir / 'vid_tax_data_nace.csv')
        df_temp.to_csv(vid_path, index=False, sep=';')
        logger.info(f"Saved to: {vid_path}")
        
        # 4. Process NACE
        logger.info("Step 4: Processing NACE classification...")
        process_nace(vid_path, nace_path)
        
        logger.info("=" * 60)
        logger.info("✅ NACE CLASSIFICATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        # Cleanup
        try:
            Path(vid_path).unlink()
            logger.info("Cleaned up temporary files")
        except:
            pass
            
    except Exception as e:
        logger.error(f"❌ NACE processing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
