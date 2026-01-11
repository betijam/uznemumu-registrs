"""
Create tables for feedback and newsletter signups
"""

-- Waitlist/Newsletter table (already exists, but let's ensure it)
CREATE TABLE IF NOT EXISTS waitlist_emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    source VARCHAR(100) DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(email, source)
);

-- Feedback/Ideas table (NEW)
CREATE TABLE IF NOT EXISTS feedback_submissions (
    id SERIAL PRIMARY KEY,
    feedback_text TEXT NOT NULL,
    email VARCHAR(255),
    source VARCHAR(100) DEFAULT 'feedback_button',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'new',
    notes TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_waitlist_created ON waitlist_emails(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback_submissions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback_submissions(status);

-- Verify
SELECT COUNT(*) as waitlist_count FROM waitlist_emails;
SELECT COUNT(*) as feedback_count FROM feedback_submissions;
