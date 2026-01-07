CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    auth_provider VARCHAR(50) DEFAULT 'email', -- email, google, linkedin
    provider_id VARCHAR(255), -- ID from external provider
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(50) DEFAULT 'user' -- user, admin
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
