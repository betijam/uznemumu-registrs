import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/ur_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

print("=== Updating Address Schema ===\n")

# Read SQL file
with open('db/addresses.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# Execute
with engine.connect() as conn:
    # Split by statement delimiter and execute
    statements = sql.split('$$;')
    for i, stmt in enumerate(statements):
        if stmt.strip():
            try:
                conn.execute(text(stmt + ('$$;' if i < len(statements) - 1 and '$$' in stmt else '')))
                conn.commit()
            except Exception as e:
                print(f"Statement {i}: {str(e)[:100]}")
    
    print("✅ Schema updated\n")
    
    # Now refresh the dimension
    print("Refreshing address dimension...")
    conn.execute(text("CALL core.refresh_address_dimension();"))
    conn.commit()
    print("✅ Dimension refreshed")
