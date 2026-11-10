-- Initial schema required by the FastAPI endpoints.
-- This script runs automatically on first database initialization only.
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS partidos (
    id SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado VARCHAR(30) NOT NULL DEFAULT 'programado'
);

CREATE TABLE IF NOT EXISTS jugadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS telemetria_frames (
    time TIMESTAMPTZ NOT NULL,
    partido_id INT NOT NULL REFERENCES partidos(id) ON DELETE CASCADE,
    jugador_id INT NOT NULL REFERENCES jugadores(id) ON DELETE CASCADE,
    frame_index INT NOT NULL CHECK (frame_index >= 0),
    longitud_zancada_cm NUMERIC(6,2) NOT NULL CHECK (longitud_zancada_cm BETWEEN 0 AND 300),
    simetria_zancada_abi NUMERIC(5,2) NOT NULL CHECK (simetria_zancada_abi BETWEEN 0 AND 100),
    angulo_valgo_rodilla_deg NUMERIC(5,2) NOT NULL CHECK (angulo_valgo_rodilla_deg BETWEEN -50 AND 50),
    flexion_lumbar_deg NUMERIC(5,2) NOT NULL CHECK (flexion_lumbar_deg BETWEEN 0 AND 90),
    rotacion_toraco_lumbar_deg NUMERIC(5,2) NOT NULL CHECK (rotacion_toraco_lumbar_deg BETWEEN -90 AND 90),
    coordenada_x NUMERIC(7,3) NOT NULL,
    coordenada_y NUMERIC(7,3) NOT NULL,
    en_zona_riesgo_esquina BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (time, partido_id, jugador_id, frame_index)
);

SELECT create_hypertable('telemetria_frames', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_telemetria_partido_jugador_time
    ON telemetria_frames (partido_id, jugador_id, time DESC);

CREATE TABLE IF NOT EXISTS metricas_metabolicas (
    time TIMESTAMPTZ NOT NULL,
    partido_id INT NOT NULL REFERENCES partidos(id) ON DELETE CASCADE,
    jugador_id INT NOT NULL REFERENCES jugadores(id) ON DELETE CASCADE,
    fc_actual INT CHECK (fc_actual BETWEEN 30 AND 250),
    zona_fc INT CHECK (zona_fc BETWEEN 1 AND 5),
    PRIMARY KEY (time, partido_id, jugador_id)
);

SELECT create_hypertable('metricas_metabolicas', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_metricas_metabolicas_partido_jugador_time
    ON metricas_metabolicas (partido_id, jugador_id, time DESC);
