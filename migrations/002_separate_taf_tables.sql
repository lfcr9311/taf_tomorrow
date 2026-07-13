-- Migration: 002_separate_taf_tables.sql
-- Description: Create separate tables for Tomorrow and REDEMET TAFs
-- Created: 2024-07-13

-- Drop old tafs table
DROP TABLE IF EXISTS tafs CASCADE;

-- Create taf_tomorrow table
CREATE TABLE taf_tomorrow (
    id SERIAL PRIMARY KEY,
    airport_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    taf_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (airport_id) REFERENCES airports(id) ON DELETE CASCADE
);

-- Create taf_redemet table
CREATE TABLE taf_redemet (
    id SERIAL PRIMARY KEY,
    airport_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    taf_data TEXT NOT NULL,
    validade_inicial TIMESTAMP,
    validade_final TIMESTAMP,
    recebimento TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (airport_id) REFERENCES airports(id) ON DELETE CASCADE
);

-- Create indexes for taf_tomorrow
CREATE INDEX idx_taf_tomorrow_airport_id ON taf_tomorrow(airport_id);
CREATE INDEX idx_taf_tomorrow_created_at ON taf_tomorrow(created_at DESC);
CREATE INDEX idx_taf_tomorrow_timestamp ON taf_tomorrow(timestamp DESC);

-- Create indexes for taf_redemet
CREATE INDEX idx_taf_redemet_airport_id ON taf_redemet(airport_id);
CREATE INDEX idx_taf_redemet_created_at ON taf_redemet(created_at DESC);
CREATE INDEX idx_taf_redemet_timestamp ON taf_redemet(timestamp DESC);
