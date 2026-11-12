-- Tactical point-event persistence extension.
-- Run after 20261110_kinematics_and_point_events.sql.
-- Safe to re-run: columns and indexes are guarded with IF NOT EXISTS.
ALTER TABLE eventos_puntos
    ADD COLUMN IF NOT EXISTS tipo_tactica VARCHAR(20),
    ADD COLUMN IF NOT EXISTS resultado_tactica VARCHAR(20),
    ADD COLUMN IF NOT EXISTS llegada_t BOOLEAN NOT NULL DEFAULT FALSE;

-- Keep values constrained to the tactical classifications used by the API.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_eventos_puntos_tipo_tactica'
          AND conrelid = 'eventos_puntos'::regclass
    ) THEN
        ALTER TABLE eventos_puntos
            ADD CONSTRAINT ck_eventos_puntos_tipo_tactica
            CHECK (tipo_tactica IS NULL OR tipo_tactica IN ('ataque', 'defensa'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_eventos_puntos_resultado_tactica'
          AND conrelid = 'eventos_puntos'::regclass
    ) THEN
        ALTER TABLE eventos_puntos
            ADD CONSTRAINT ck_eventos_puntos_resultado_tactica
            CHECK (resultado_tactica IS NULL OR resultado_tactica IN ('acierto', 'error'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_eventos_puntos_partido_llegada_t
    ON eventos_puntos (partido_id, llegada_t)
    WHERE llegada_t = TRUE;
CREATE INDEX IF NOT EXISTS idx_eventos_puntos_partido_jugador_time
    ON eventos_puntos (partido_id, jugador_id, time DESC);
