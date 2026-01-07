from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in environment variables")
    exit(1)

print(f"🔌 Connecting to database...")
engine = create_engine(DATABASE_URL)

def run_migration():
    migration_file = os.path.join(os.path.dirname(__file__), 'db', 'migrations', '01_create_users.sql')
    
    print(f"📖 Reading migration file: {migration_file}")
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_statements = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Migration file not found at {migration_file}")
        return

    print("🚀 Applying migration...")
    try:
        with engine.connect() as conn:
            # Split by ; to handle multiple statements if any, though usually execute handles it
            # But specific drivers might need separate executions. Neon/Postgres usually okay with execute.
            conn.execute(text(sql_statements))
            conn.commit()
        print("✅ Users table created successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
