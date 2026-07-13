-- Migration: 001_create_tables.sql
-- Description: Create airports and tafs tables
-- Created: 2024-07-13

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS tafs CASCADE;
DROP TABLE IF EXISTS airports CASCADE;

-- Create airports table
CREATE TABLE airports (
    id SERIAL PRIMARY KEY,
    iata_code VARCHAR(10) UNIQUE NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(50) DEFAULT 'Brasil',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on iata_code for faster queries
CREATE INDEX idx_airports_iata_code ON airports(iata_code);

-- Create tafs table
CREATE TABLE tafs (
    id SERIAL PRIMARY KEY,
    airport_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    taf_data TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (airport_id) REFERENCES airports(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_tafs_airport_id ON tafs(airport_id);
CREATE INDEX idx_tafs_source ON tafs(source);
CREATE INDEX idx_tafs_created_at ON tafs(created_at DESC);
CREATE INDEX idx_tafs_timestamp ON tafs(timestamp DESC);

-- Create composite index for common queries
CREATE INDEX idx_tafs_airport_source ON tafs(airport_id, source);
