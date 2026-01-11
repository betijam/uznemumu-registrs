-- Recent views table for user history tracking
-- Recent views table for user history tracking
CREATE TABLE IF NOT EXISTS recent_views (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    entity_id VARCHAR(20) NOT NULL,
    entity_type VARCHAR(10) NOT NULL CHECK (entity_type IN ('company', 'person')),
    entity_name VARCHAR(255),
    viewed_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (user_id, entity_id, entity_type)
);

-- Index for fast retrieval of recent views
CREATE INDEX IF NOT EXISTS idx_recent_views_time ON recent_views(user_id, viewed_at DESC);

-- Comments for documentation
COMMENT ON TABLE recent_views IS 'User browsing history for companies and persons';
COMMENT ON COLUMN recent_views.viewed_at IS 'Last time this entity was viewed (updated on each view)';
