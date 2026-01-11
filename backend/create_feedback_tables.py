"""Quick script to create feedback tables"""
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    # Create waitlist table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS waitlist_emails (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            source VARCHAR(100) DEFAULT 'unknown',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(email, source)
        )
    """))
    
    # Create feedback table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS feedback_submissions (
            id SERIAL PRIMARY KEY,
            feedback_text TEXT NOT NULL,
            email VARCHAR(255),
            source VARCHAR(100) DEFAULT 'feedback_button',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            status VARCHAR(50) DEFAULT 'new',
            notes TEXT
        )
    """))
    
    # Indexes
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_waitlist_created ON waitlist_emails(created_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback_submissions(created_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback_submissions(status)"))
    
    conn.commit()
    
    # Verify
    result = conn.execute(text("SELECT COUNT(*) FROM waitlist_emails")).fetchone()
    print(f"✅ waitlist_emails table: {result[0]} records")
    
    result = conn.execute(text("SELECT COUNT(*) FROM feedback_submissions")).fetchone()
    print(f"✅ feedback_submissions table: {result[0]} records")

print("✅ Feedback tables created!")
