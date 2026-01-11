"""
Database migration runner for favorites and history features.
Runs migrations 04 and 05 to create favorites and recent_views tables.
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import logging

# Try to load .env file
try:
    from dotenv import load_dotenv
    # Load .env from project root (one level up from backend)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
    else:
        # Try backend directory as fallback
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ Loaded environment from {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Or set DATABASE_URL environment variable manually")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variable"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        logger.error("\nPlease either:")
        logger.error("1. Create a .env file in the backend directory with DATABASE_URL=your_connection_string")
        logger.error("2. Set DATABASE_URL environment variable: $env:DATABASE_URL='your_connection_string'")
        sys.exit(1)
    return db_url

def run_migration(engine, migration_file: Path):
    """Run a single migration file"""
    logger.info(f"Running migration: {migration_file.name}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Split SQL into individual statements (by semicolon)
        statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
        
        with engine.connect() as conn:
            for i, statement in enumerate(statements, 1):
                try:
                    logger.info(f"  Executing statement {i}/{len(statements)}...")
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    # Check if error is "already exists" - that's OK
                    if "already exists" in str(e).lower():
                        logger.warning(f"  Statement {i} skipped (already exists)")
                    else:
                        logger.error(f"  Failed on statement {i}: {e}")
                        raise
            
            logger.info(f"✓ Successfully executed {migration_file.name}")
            return True
            
    except Exception as e:
        logger.error(f"✗ Failed to execute {migration_file.name}: {e}")
        return False

def verify_tables(engine):
    """Verify that tables were created successfully"""
    logger.info("Verifying tables...")
    
    try:
        with engine.connect() as conn:
            # Check favorites table
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('favorites', 'recent_views')
            """))
            
            tables = [row[0] for row in result]
            
            if 'favorites' in tables:
                logger.info("✓ Table 'favorites' exists")
            else:
                logger.error("✗ Table 'favorites' not found")
                
            if 'recent_views' in tables:
                logger.info("✓ Table 'recent_views' exists")
            else:
                logger.error("✗ Table 'recent_views' not found")
            
            return len(tables) == 2
            
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return False

def main():
    """Main migration runner"""
    logger.info("=" * 60)
    logger.info("Starting Dashboard Migrations (Favorites + History)")
    logger.info("=" * 60)
    
    # Get database URL
    db_url = get_database_url()
    logger.info(f"Connecting to database...")
    
    # Create engine
    engine = create_engine(db_url)
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent / 'db' / 'migrations'
    
    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Migration files to run
    migration_files = [
        migrations_dir / '04_create_favorites.sql',
        migrations_dir / '05_create_recent_views.sql'
    ]
    
    # Check if migration files exist
    for migration_file in migration_files:
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            sys.exit(1)
    
    # Run migrations
    success_count = 0
    for migration_file in migration_files:
        if run_migration(engine, migration_file):
            success_count += 1
    
    logger.info("-" * 60)
    
    # Verify tables
    if verify_tables(engine):
        logger.info("=" * 60)
        logger.info(f"✓ All migrations completed successfully ({success_count}/{len(migration_files)})")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Deploy backend to Railway")
        logger.info("2. Deploy frontend to Railway")
        logger.info("3. Test favorites and history features")
        return 0
    else:
        logger.error("=" * 60)
        logger.error("✗ Migration verification failed")
        logger.error("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
