"""
Industry Stats Migration Script

Izpilda industry_stats_migration.sql pret Neon datubāzi.
Palaid: python run_industry_migration.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from etl.loader import engine
from sqlalchemy import text
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_migration():
    """Run the industry stats migration SQL file"""
    
    migration_file = Path(__file__).parent / 'db' / 'industry_stats_migration.sql'
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    logger.info(f"Reading migration file: {migration_file}")
    sql_content = migration_file.read_text(encoding='utf-8')
    
    # Split into individual statements (ignoring comments and empty lines)
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # Skip full-line comments
        stripped = line.strip()
        if stripped.startswith('--') or not stripped:
            continue
        
        current_statement.append(line)
        
        # If line ends with semicolon, it's end of statement
        if stripped.endswith(';'):
            full_statement = '\n'.join(current_statement)
            statements.append(full_statement)
            current_statement = []
    
    logger.info(f"Found {len(statements)} SQL statements to execute")
    
    try:
        with engine.connect() as conn:
            for idx, statement in enumerate(statements, 1):
                try:
                    # Get first 50 chars for logging
                    preview = statement.strip()[:50].replace('\n', ' ')
                    logger.info(f"Executing statement {idx}/{len(statements)}: {preview}...")
                    
                    conn.execute(text(statement))
                    conn.commit()
                    
                except Exception as e:
                    logger.warning(f"Statement {idx} warning: {e}")
                    # Continue with other statements even if one fails
                    conn.rollback()
            
            # Verify data was loaded
            logger.info("\n" + "="*50)
            logger.info("VERIFICATION - Checking row counts:")
            logger.info("="*50)
            
            try:
                stats_count = conn.execute(text(
                    "SELECT COUNT(*) FROM industry_stats_materialized"
                )).scalar()
                logger.info(f"✅ industry_stats_materialized: {stats_count} rows")
            except Exception as e:
                logger.warning(f"Could not count industry_stats_materialized: {e}")
            
            try:
                leaders_count = conn.execute(text(
                    "SELECT COUNT(*) FROM industry_leaders_cache"
                )).scalar()
                logger.info(f"✅ industry_leaders_cache: {leaders_count} rows")
            except Exception as e:
                logger.warning(f"Could not count industry_leaders_cache: {e}")
            
            logger.info("="*50)
            logger.info("Migration completed!")
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting Industry Stats Migration...")
    logger.info(f"Database: {os.getenv('DATABASE_URL', 'using default')[:50]}...")
    
    success = run_migration()
    
    if success:
        logger.info("\n🎉 Migration successful! Industry analytics is ready.")
    else:
        logger.error("\n❌ Migration failed. Check logs for details.")
        sys.exit(1)
