from typing import Optional

import asyncpg
from fastapi import APIRouter, HTTPException, Query, status

from database import db
from models import ClinicalProfileCreate

router = APIRouter(prefix="/clinical-profile", tags=["Ficha clínica"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def save_clinical_profile(profile: ClinicalProfileCreate):
    """Create or update a player's clinical profile for a match."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO fichas_clinicas (
                    partido_id, jugador_id, nombre, edad, deporte, genero,
                    fase_ciclo_menstrual, descripcion_fase,
                    entrenamiento_sugerido, vo2max_metodo, vo2max_valor,
                    vo2max_formula_hombre, vo2max_formula_mujer
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                ON CONFLICT (partido_id, jugador_id) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    edad = EXCLUDED.edad,
                    deporte = EXCLUDED.deporte,
                    genero = EXCLUDED.genero,
                    fase_ciclo_menstrual = EXCLUDED.fase_ciclo_menstrual,
                    descripcion_fase = EXCLUDED.descripcion_fase,
                    entrenamiento_sugerido = EXCLUDED.entrenamiento_sugerido,
                    vo2max_metodo = EXCLUDED.vo2max_metodo,
                    vo2max_valor = EXCLUDED.vo2max_valor,
                    vo2max_formula_hombre = EXCLUDED.vo2max_formula_hombre,
                    vo2max_formula_mujer = EXCLUDED.vo2max_formula_mujer,
                    updated_at = NOW()
                RETURNING *
                """,
                profile.partido_id,
                profile.jugador_id,
                profile.nombre,
                profile.edad,
                profile.deporte,
                profile.genero,
                profile.fase_ciclo_menstrual,
                profile.descripcion_fase,
                profile.entrenamiento_sugerido,
                profile.vo2max_metodo,
                profile.vo2max_valor,
                profile.vo2max_formula_hombre,
                profile.vo2max_formula_mujer,
            )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo guardar la ficha clínica: {exc.__class__.__name__}. Aplica la migración SQL.",
        ) from exc

    return {"status": "success", "ficha": dict(row)}


@router.get("/{jugador_id}")
async def get_clinical_profile(
    jugador_id: int,
    partido_id: Optional[int] = Query(default=None, ge=1),
):
    """Get a player's latest profile, or the profile for a specified match."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            if partido_id is not None:
                row = await connection.fetchrow(
                    """SELECT * FROM fichas_clinicas
                       WHERE jugador_id = $1 AND partido_id = $2""",
                    jugador_id,
                    partido_id,
                )
            else:
                row = await connection.fetchrow(
                    """SELECT * FROM fichas_clinicas
                       WHERE jugador_id = $1
                       ORDER BY updated_at DESC LIMIT 1""",
                    jugador_id,
                )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo consultar la ficha clínica: {exc.__class__.__name__}. Aplica la migración SQL.",
        ) from exc

    if row is None:
        raise HTTPException(status_code=404, detail="No se encontró una ficha clínica para ese jugador.")
    return dict(row)
