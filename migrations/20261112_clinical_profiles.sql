-- Clinical profile persistence for SquashAnalytics Pro.
-- Apply once to the same PostgreSQL/TimescaleDB database used by the API.
CREATE TABLE IF NOT EXISTS fichas_clinicas (
    id BIGSERIAL PRIMARY KEY,
    partido_id INT NOT NULL,
    jugador_id INT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    edad INT NOT NULL CHECK (edad BETWEEN 1 AND 120),
    deporte VARCHAR(120) NOT NULL,
    genero VARCHAR(20) NOT NULL CHECK (genero IN ('masculino', 'femenino', 'otro')),
    fase_ciclo_menstrual VARCHAR(120),
    descripcion_fase VARCHAR(1000),
    entrenamiento_sugerido VARCHAR(1000),
    vo2max_metodo VARCHAR(30) NOT NULL DEFAULT 'manual'
        CHECK (vo2max_metodo IN ('cooper', 'beep_test', 'rockport', 'manual')),
    vo2max_valor DOUBLE PRECISION CHECK (vo2max_valor IS NULL OR vo2max_valor BETWEEN 0 AND 100),
    vo2max_formula_hombre VARCHAR(500),
    vo2max_formula_mujer VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fichas_clinicas_partido_jugador UNIQUE (partido_id, jugador_id)
);

CREATE INDEX IF NOT EXISTS idx_fichas_clinicas_jugador_updated
    ON fichas_clinicas (jugador_id, updated_at DESC);
