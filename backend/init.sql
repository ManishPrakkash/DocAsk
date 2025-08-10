-- PostgreSQL initialization script for ClauseWise
-- This script sets up security configurations and extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types for enums (will be handled by SQLAlchemy but good to have)
DO $$ BEGIN
    CREATE TYPE document_status AS ENUM ('pending', 'processing', 'complete', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Set up row-level security (will be configured by application)
ALTER DATABASE clausewise SET row_security = on;

-- Performance optimizations
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Security configurations
ALTER SYSTEM SET ssl = 'on';
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
ALTER SYSTEM SET log_statement = 'all';

-- Reload configuration
SELECT pg_reload_conf();

-- Create indexes that will be useful for the application
-- (These will also be created by SQLAlchemy, but ensuring they exist)

-- Note: Actual table creation is handled by SQLAlchemy in the application
-- This file focuses on database-level configurations and optimizations