import asyncpg
from fastapi import APIRouter, HTTPException, status

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


@router.delete("/matches/{partido_id}/reset")
async def reset_estadisticas_partido(partido_id: int):
    """Reset the match stats for a given partido_id while preserving historical data if needed."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM eventos_puntos WHERE partido_id = $1",
                    partido_id,
                )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo reiniciar la estadística del partido: {exc.__class__.__name__}.",
        ) from exc

    return {
        "status": "success",
        "partido_id": partido_id,
        "mensaje": "Estadísticas del partido reiniciadas."
    }
