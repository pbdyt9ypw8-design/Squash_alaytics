-- Migration: optional kinematic fields and tactical point events.
-- Apply to the same PostgreSQL/TimescaleDB database configured for the API.
ALTER TABLE telemetria_frames
    ADD COLUMN IF NOT EXISTS angulo_valgo_tobillo_deg NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS flexion_rodilla_deg NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS elevacion_hombro_deg NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS inclinacion_pelvis_deg NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS retardo_carga_raqueta_ms INT;

CREATE TABLE IF NOT EXISTS eventos_puntos (
    id SERIAL PRIMARY KEY,
    partido_id INT NOT NULL REFERENCES partidos(id) ON DELETE CASCADE,
    jugador_id INT NOT NULL REFERENCES jugadores(id) ON DELETE CASCADE,
    set_numero INT NOT NULL CHECK (set_numero >= 1),
    puntuacion_actual VARCHAR(20) NOT NULL,
    tipo_resultado VARCHAR(30) NOT NULL CHECK (
        tipo_resultado IN ('ganador', 'error_no_forzado', 'stroke', 'let')
    ),
    tipo_golpe VARCHAR(50),
    zona_origen_x NUMERIC(5,2) CHECK (zona_origen_x IS NULL OR zona_origen_x BETWEEN 0 AND 6.4),
    zona_origen_y NUMERIC(5,2) CHECK (zona_origen_y IS NULL OR zona_origen_y BETWEEN 0 AND 9.75),
    zona_destino_x NUMERIC(5,2) CHECK (zona_destino_x IS NULL OR zona_destino_x BETWEEN 0 AND 6.4),
    zona_destino_y NUMERIC(5,2) CHECK (zona_destino_y IS NULL OR zona_destino_y BETWEEN 0 AND 9.75),
    zona_rival_debil BOOLEAN NOT NULL DEFAULT FALSE,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_eventos_puntos_partido_time
    ON eventos_puntos (partido_id, time DESC);
