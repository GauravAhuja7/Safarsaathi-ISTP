CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    distance_km INTEGER,
    max_altitude_m INTEGER,
    last_connectivity_point VARCHAR(150),
    nearest_hospital_name VARCHAR(100),
    nearest_hospital_phone VARCHAR(20),
    nearest_hospital_distance_km INTEGER
);

-- month_end < month_start means the range wraps across the year (e.g. Oct=10 to Feb=2)
CREATE TABLE IF NOT EXISTS route_baselines (
    id SERIAL PRIMARY KEY,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    month_start INTEGER NOT NULL CHECK (month_start BETWEEN 1 AND 12),
    month_end INTEGER NOT NULL CHECK (month_end BETWEEN 1 AND 12),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    reason TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS weather_cache (
    id SERIAL PRIMARY KEY,
    district VARCHAR(50) NOT NULL,
    forecast_json JSONB NOT NULL DEFAULT '{}',
    summary TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS official_alerts (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('road_closed', 'disaster_warning', 'construction', 'landslide', 'other')),
    description TEXT,
    source VARCHAR(50),
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS reporters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    role VARCHAR(50) CHECK (role IN ('taxi_driver', 'dhaba_owner', 'homestay_owner', 'other')),
    location_name VARCHAR(150),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    route_id INTEGER REFERENCES routes(id) ON DELETE SET NULL,
    consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    consent_date DATE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    strike_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reporter_reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL REFERENCES reporters(id) ON DELETE CASCADE,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    condition VARCHAR(20) NOT NULL CHECK (condition IN ('blocked', 'rough', 'clear', 'other')),
    description TEXT,
    photo_url VARCHAR(255),
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pois (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('hospital', 'police', 'petrol', 'mechanic', 'reporter', 'emergency', 'checkpoint')),
    phone VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    route_id INTEGER REFERENCES routes(id) ON DELETE SET NULL,
    notes TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_reporter_reports_route_time
    ON reporter_reports (route_id, reported_at DESC);

CREATE INDEX IF NOT EXISTS idx_official_alerts_route_expires
    ON official_alerts (route_id, expires_at);

CREATE INDEX IF NOT EXISTS idx_weather_cache_district_time
    ON weather_cache (district, scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_pois_category
    ON pois (category);
