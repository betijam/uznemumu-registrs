CREATE TABLE IF NOT EXISTS waitlist_emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(50),
    ip_address VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist_emails(email);
