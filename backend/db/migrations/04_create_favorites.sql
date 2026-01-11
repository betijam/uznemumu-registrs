-- Favorites table for user watchlist
-- Favorites table for user watchlist
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    entity_id VARCHAR(20) NOT NULL,
    entity_type VARCHAR(10) NOT NULL CHECK (entity_type IN ('company', 'person')),
    entity_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, entity_id, entity_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_created ON favorites(user_id, created_at DESC);

-- Comments for documentation
COMMENT ON TABLE favorites IS 'User favorites/watchlist for companies and persons';
COMMENT ON COLUMN favorites.entity_type IS 'Type of entity: company or person';
