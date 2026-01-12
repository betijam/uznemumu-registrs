CREATE TABLE IF NOT EXISTS waitlist_emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(50),
    ip_address VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist_emails(email);

-- Required for ON CONFLICT (email, source) logic in backend
CREATE UNIQUE INDEX IF NOT EXISTS idx_waitlist_unique ON waitlist_emails(email, COALESCE(source, 'default'));
-- Or just simple unique on (email, source) if source is not null?
-- waitlist.py schemas uses source with default="pricing_page".
-- Let's make it simple UNIQUE(email, source).
CREATE UNIQUE INDEX IF NOT EXISTS idx_waitlist_email_source ON waitlist_emails(email, source);
