import os
import sys
from sqlalchemy import create_engine, text

# Add parent dir to path to find app module if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import from app config first
    from app.core.config import settings
    DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
    print("Loaded DATABASE_URL from app.core.config")
except Exception as e:
    print(f"Could not import settings ({e}), trying .env file")
    try:
        from dotenv import load_dotenv
        # Go up 3 levels: backend/migrations -> backend -> root
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        load_dotenv(env_path)
        DATABASE_URL = os.getenv("DATABASE_URL")
        print(f"Loaded DATABASE_URL from {env_path}")
    except ImportError:
        print("python-dotenv not installed. Please install it or set DATABASE_URL manually.")
        sys.exit(1)

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found!")
    sys.exit(1)

# Ensure correct driver for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Mask password for logging
safe_url = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else '...'
print(f"Connecting to DB: ...@{safe_url}")

engine = create_engine(DATABASE_URL)

def restore():
    print("Starting industry stats restoration...")
    sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_industry_materialized_view_multiyear.sql')
    
    if not os.path.exists(sql_file):
        print(f"ERROR: SQL file not found at {sql_file}")
        sys.exit(1)

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_commands = f.read()

    try:
        with engine.connect() as conn:
            # We use autocommit=True behavior via commit() or begin() block
            with conn.begin(): 
                print("Executing SQL script...")
                conn.execute(text(sql_commands))
        print("Restoration complete! Industry stats have been regenerated.")
    except Exception as e:
        print(f"ERROR during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    restore()
