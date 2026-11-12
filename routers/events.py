import asyncpg
from fastapi import APIRouter, HTTPException, Query, status

from database import db
from models import EventoPuntoCreate

router = APIRouter(prefix="/events", tags=["Registro Táctico y Puntos"])


@router.post("/point", status_code=status.HTTP_201_CREATED)
async def registrar_punto(evento: EventoPuntoCreate):
    """Store a point outcome and optional court locations."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            event_id = await connection.fetchval(
                """
                INSERT INTO eventos_puntos (
                    partido_id, jugador_id, set_numero, puntuacion_actual,
                    tipo_resultado, tipo_golpe, zona_origen_x, zona_origen_y,
                    zona_destino_x, zona_destino_y, zona_rival_debil
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                """,
                evento.partido_id,
                evento.jugador_id,
                evento.set_numero,
                evento.puntuacion_actual,
                evento.tipo_resultado,
                evento.tipo_golpe,
                evento.zona_origen_x,
                evento.zona_origen_y,
                evento.zona_destino_x,
                evento.zona_destino_y,
                evento.zona_rival_debil,
            )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo registrar el evento: {exc.__class__.__name__}. Aplica la migración SQL y verifica los IDs.",
        ) from exc

    return {"status": "success", "id": event_id, "tipo_resultado": evento.tipo_resultado}


@router.get("/matches/{partido_id}/court-zones")
async def resumen_zonas_cancha(
    partido_id: int,
    jugador_id: int | None = Query(default=None, ge=1),
):
    """Count landing points in a 3-column by 2-row grid and return zone percentages.

    Coordinates use the court dimensions validated by EventoPuntoCreate:
    x=0..6.4 and y=0..9.75. Points without a destination coordinate are omitted.
    """
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    # Six equally sized areas (equal area; not literal squares, due to court proportions).
    # IDs progress left-to-right, then near-to-far along the y axis.
    query = """
        WITH zone_counts AS (
            SELECT
                LEAST(1, FLOOR(ep.zona_destino_y / (9.75 / 2.0))::int) * 3
                    + LEAST(2, FLOOR(ep.zona_destino_x / (6.4 / 3.0))::int) AS zona_id,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE ep.tipo_resultado IN ('ganador', 'stroke')) AS aciertos,
                COUNT(*) FILTER (WHERE ep.tipo_resultado = 'error_no_forzado') AS errores
            FROM eventos_puntos AS ep
            WHERE ep.partido_id = $1
              AND ($2::int IS NULL OR ep.jugador_id = $2)
              AND ep.zona_destino_x IS NOT NULL
              AND ep.zona_destino_y IS NOT NULL
            GROUP BY 1
        ), all_counts AS (
            SELECT COALESCE(SUM(total), 0)::int AS total
            FROM zone_counts
        ), zones AS (
            SELECT * FROM (VALUES
                (0, 'fila_1_izquierda'), (1, 'fila_1_centro'), (2, 'fila_1_derecha'),
                (3, 'fila_2_izquierda'), (4, 'fila_2_centro'), (5, 'fila_2_derecha')
            ) AS z(zona_id, nombre)
        )
        SELECT z.zona_id, z.nombre,
               COALESCE(c.total, 0)::int AS total,
               COALESCE(c.aciertos, 0)::int AS aciertos,
               COALESCE(c.errores, 0)::int AS errores,
               CASE WHEN a.total > 0
                    THEN ROUND(COALESCE(c.total, 0) * 100.0 / a.total, 2)
                    ELSE 0 END AS porcentaje_caidas,
               CASE WHEN COALESCE(c.total, 0) > 0
                    THEN ROUND(COALESCE(c.aciertos, 0) * 100.0 / c.total, 2)
                    ELSE 0 END AS porcentaje_acierto,
               CASE WHEN COALESCE(c.total, 0) > 0
                    THEN ROUND(COALESCE(c.errores, 0) * 100.0 / c.total, 2)
                    ELSE 0 END AS porcentaje_error,
               a.total AS total_caidas
        FROM zones AS z
        CROSS JOIN all_counts AS a
        LEFT JOIN zone_counts AS c ON c.zona_id = z.zona_id
        ORDER BY z.zona_id
    """
    try:
        async with db.pool.acquire() as connection:
            rows = await connection.fetch(query, partido_id, jugador_id)
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo calcular el resumen por zonas: {exc.__class__.__name__}.",
        ) from exc

    return {
        "partido_id": partido_id,
        "jugador_id": jugador_id,
        "total_caidas": rows[0]["total_caidas"] if rows else 0,
        "zonas": [dict(row) for row in rows],
    }
