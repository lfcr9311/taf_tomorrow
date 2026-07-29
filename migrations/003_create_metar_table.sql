-- Migration: 003_create_metar_table.sql
-- Description: Create table for METAR observations from REDEMET
-- Created: 2024-07-29

CREATE TABLE IF NOT EXISTS metar_redemet (
    id SERIAL PRIMARY KEY,
    airport_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,       -- momento da busca (padrão das outras tabelas)
    metar_data TEXT NOT NULL,           -- mensagem METAR bruta
    observacao TIMESTAMP,               -- horário real da observação (validade_inicial da REDEMET)
    recebimento TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (airport_id) REFERENCES airports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metar_redemet_airport_id ON metar_redemet(airport_id);
CREATE INDEX IF NOT EXISTS idx_metar_redemet_observacao ON metar_redemet(observacao DESC);
CREATE INDEX IF NOT EXISTS idx_metar_redemet_timestamp ON metar_redemet(timestamp DESC);
