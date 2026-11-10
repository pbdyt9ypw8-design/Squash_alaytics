import asyncpg
from fastapi import APIRouter, HTTPException

from database import db

router = APIRouter(prefix="/training-plan", tags=["Resumen post-partido (experimental)"])


@router.get("/{partido_id}/{jugador_id}")
async def generar_resumen_post_partido(partido_id: int, jugador_id: int):
    """Return descriptive match metrics and conservative, non-clinical follow-up guidance.

    This endpoint does not diagnose injuries or prescribe rehabilitation, hydration
    volumes, supplements, or carbohydrate doses. Biomechanics from 2D video are
    experimental proxies and should be interpreted by a qualified professional.
    """
    if partido_id < 1 or jugador_id < 1:
        raise HTTPException(status_code=422, detail="Los identificadores deben ser positivos.")
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    try:
        async with db.pool.acquire() as connection:
            metrics = await connection.fetchrow(
                """
                SELECT COUNT(*) AS sample_count,
                       AVG(angulo_valgo_rodilla_deg) AS avg_valgo,
                       AVG(flexion_lumbar_deg) AS avg_lumbar,
                       AVG(simetria_zancada_abi) AS avg_asymmetry,
                       AVG(inclinacion_pelvis_deg) AS avg_pelvis,
                       MIN(time) AS first_time,
                       MAX(time) AS last_time
                FROM telemetria_frames
                WHERE partido_id = $1 AND jugador_id = $2
                """,
                partido_id,
                jugador_id,
            )
    except asyncpg.UndefinedColumnError as exc:
        raise HTTPException(
            status_code=503,
            detail="Falta aplicar la migración de cinemática antes de generar el resumen.",
        ) from exc
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(status_code=503, detail="Falta la tabla telemetria_frames.") from exc
    except asyncpg.PostgresError as exc:
        raise HTTPException(status_code=503, detail=f"Error consultando datos: {exc.__class__.__name__}.") from exc

    if not metrics or metrics["sample_count"] == 0:
        raise HTTPException(status_code=404, detail="No hay telemetría para ese partido y jugador.")

    def rounded(value):
        return round(float(value), 2) if value is not None else None

    return {
        "status": "descriptive_summary",
        "partido_id": partido_id,
        "jugador_id": jugador_id,
        "muestras_telemetria": metrics["sample_count"],
        "periodo_datos": {
            "inicio": metrics["first_time"].isoformat() if metrics["first_time"] else None,
            "fin": metrics["last_time"].isoformat() if metrics["last_time"] else None,
        },
        "promedios_experimentales": {
            "angulo_valgo_rodilla_deg": rounded(metrics["avg_valgo"]),
            "flexion_lumbar_proxy_deg": rounded(metrics["avg_lumbar"]),
            "asimetria_zancada_pct": rounded(metrics["avg_asymmetry"]),
            "inclinacion_pelvis_proxy_deg": rounded(metrics["avg_pelvis"]),
        },
        "orientacion_general": {
            "sombra": "Planificar trabajo técnico de baja intensidad y progresión gradual con supervisión del entrenador; ajustar o cancelar ante dolor, mareo o malestar.",
            "fuerza": "Usar una sesión general de fuerza y control motor solo dentro del plan habitual del atleta; las métricas de este prototipo no seleccionan ejercicios terapéuticos.",
            "recuperacion": "Seguir el plan individual de alimentación e hidratación basado en mediciones reales y orientación de un profesional cualificado; este endpoint no calcula dosis ni volúmenes.",
        },
        "nota": "Resumen experimental, no prescripción clínica ni diagnóstico. No usar estos promedios para decidir seguridad, tratamiento, suplementos o dosificación nutricional.",
    }
