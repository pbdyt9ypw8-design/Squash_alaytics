import asyncpg
from fastapi import APIRouter, HTTPException, Query, status

from database import db
from models import EventoPuntoCreate

router = APIRouter(prefix="/events", tags=["Registro Táctico y Puntos"])


@router.post("/point", status_code=status.HTTP_201_CREATED)
async def registrar_punto(evento: EventoPuntoCreate):
    """Persist a confirmed shot/event and whether the player returned to the T."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            event_id = await connection.fetchval(
                """
                INSERT INTO eventos_puntos (
                    partido_id, jugador_id, set_numero, puntuacion_actual,
                    tipo_resultado, tipo_golpe, tipo_tactica, resultado_tactica,
                    llegada_t, zona_origen_x, zona_origen_y,
                    zona_destino_x, zona_destino_y, zona_rival_debil
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id
                """,
                evento.partido_id,
                evento.jugador_id,
                evento.set_numero,
                evento.puntuacion_actual,
                evento.tipo_resultado,
                evento.tipo_golpe,
                evento.tipo_tactica,
                evento.resultado_tactica,
                evento.llegada_t,
                evento.zona_origen_x,
                evento.zona_origen_y,
                evento.zona_destino_x,
                evento.zona_destino_y,
                evento.zona_rival_debil,
            )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo registrar el evento: {exc.__class__.__name__}. Aplica las migraciones SQL y verifica los IDs.",
        ) from exc

    return {
        "status": "success",
        "id": event_id,
        "partido_id": evento.partido_id,
        "jugador_id": evento.jugador_id,
        "tipo_resultado": evento.tipo_resultado,
        "tipo_golpe": evento.tipo_golpe,
        "tipo_tactica": evento.tipo_tactica,
        "llegada_t": evento.llegada_t,
    }


@router.get("/matches/{partido_id}/points")
async def listar_puntos(partido_id: int, jugador_id: int | None = Query(default=None, ge=1)):
    """List persisted point events for a match, optionally filtered by player."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")
    try:
        async with db.pool.acquire() as connection:
            if jugador_id is None:
                rows = await connection.fetch(
                    """SELECT id, partido_id, jugador_id, set_numero, puntuacion_actual,
                              tipo_resultado, tipo_golpe, tipo_tactica, resultado_tactica,
                              llegada_t, time
                       FROM eventos_puntos WHERE partido_id = $1 ORDER BY time, id""",
                    partido_id,
                )
            else:
                rows = await connection.fetch(
                    """SELECT id, partido_id, jugador_id, set_numero, puntuacion_actual,
                              tipo_resultado, tipo_golpe, tipo_tactica, resultado_tactica,
                              llegada_t, time
                       FROM eventos_puntos WHERE partido_id = $1 AND jugador_id = $2
                       ORDER BY time, id""",
                    partido_id,
                    jugador_id,
                )
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=503, detail=f"No se pudieron consultar los eventos: {exc.__class__.__name__}.") from exc

    return {"partido_id": partido_id, "eventos": [dict(row) for row in rows]}


@router.get("/matches/{partido_id}/t-arrivals")
async def contar_llegadas_t(partido_id: int, jugador_id: int | None = Query(default=None, ge=1)):
    """Count explicitly confirmed returns to the T for a match/player."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")
    try:
        async with db.pool.acquire() as connection:
            if jugador_id is None:
                count = await connection.fetchval(
                    "SELECT COUNT(*) FROM eventos_puntos WHERE partido_id = $1 AND llegada_t = TRUE",
                    partido_id,
                )
            else:
                count = await connection.fetchval(
                    "SELECT COUNT(*) FROM eventos_puntos WHERE partido_id = $1 AND jugador_id = $2 AND llegada_t = TRUE",
                    partido_id,
                    jugador_id,
                )
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=503, detail=f"No se pudo contar las llegadas a la T: {exc.__class__.__name__}.") from exc
    return {"partido_id": partido_id, "jugador_id": jugador_id, "llegadas_a_la_t": count}


@router.delete("/matches/{partido_id}/reset")
async def reset_estadisticas_partido(partido_id: int):
    """Delete point events for one match."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute("DELETE FROM eventos_puntos WHERE partido_id = $1", partido_id)
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo reiniciar la estadística del partido: {exc.__class__.__name__}.",
        ) from exc

    return {"status": "success", "partido_id": partido_id, "mensaje": "Estadísticas del partido reiniciadas."}
