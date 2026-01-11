"""Quick script to create etl_state table"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Create etl_state table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS etl_state (
            id SERIAL PRIMARY KEY,
            job_name VARCHAR(100) UNIQUE NOT NULL,
            last_run_at TIMESTAMP WITH TIME ZONE,
            last_success_at TIMESTAMP WITH TIME ZONE,
            records_processed INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'IDLE',
            error_message TEXT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """))
    
    # Insert initial state
    conn.execute(text("""
        INSERT INTO etl_state (job_name, status) 
        VALUES ('extended_financial_fields', 'IDLE')
        ON CONFLICT (job_name) DO NOTHING
    """))
    
    # Add timestamps to financial_reports if missing
    conn.execute(text("""
        ALTER TABLE financial_reports 
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    """))
    
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_financial_reports_created_at 
        ON financial_reports(created_at)
    """))
    
    conn.execute(text("""
        UPDATE financial_reports 
        SET created_at = NOW(), updated_at = NOW() 
        WHERE created_at IS NULL
    """))
    
    conn.commit()
    
    # Verify
    result = conn.execute(text("SELECT * FROM etl_state")).fetchall()
    print(f"✅ Created etl_state table with {len(result)} rows")
    for row in result:
        print(f"  - {row}")
    
    result = conn.execute(text("""
        SELECT COUNT(*) as total, 
               COUNT(created_at) as with_timestamps 
        FROM financial_reports
    """)).fetchone()
    print(f"✅ Financial reports: {result[0]} total, {result[1]} with timestamps")

print("✅ Setup complete!")
