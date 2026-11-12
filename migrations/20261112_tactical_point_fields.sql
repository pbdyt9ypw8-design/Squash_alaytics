-- Add tactical classifications and an explicit flag for each player return to the T.
ALTER TABLE eventos_puntos
    ADD COLUMN IF NOT EXISTS tipo_tactica VARCHAR(20),
    ADD COLUMN IF NOT EXISTS resultado_tactica VARCHAR(20),
    ADD COLUMN IF NOT EXISTS llegada_t BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_eventos_puntos_partido_llegada_t
    ON eventos_puntos (partido_id, llegada_t)
    WHERE llegada_t = TRUE;
