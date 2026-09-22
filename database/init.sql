-- Dark Pattern Detector Database Initialization
-- This file runs automatically when the PostgreSQL container starts

-- Create database (already created by Docker env vars)
-- Tables are created by SQLAlchemy on FastAPI startup

-- Insert some sample community reports for demo purposes
-- These will only insert if the table already exists (run after FastAPI startup)

SELECT 'Database initialized for Dark Pattern Detector' as message;
