from datetime import datetime

import asyncpg
from fastapi import APIRouter, HTTPException, Query, status

from database import db
from manager import manager
from models import TelemetryFrameCreate

router = APIRouter(prefix="/telemetry", tags=["Telemetría y Biomecánica"])


@router.post("/frame", status_code=status.HTTP_201_CREATED)
async def ingest_frame(data: TelemetryFrameCreate):
    """Store a processed telemetry frame and its optional heart-rate reading."""
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    now = datetime.now().astimezone()
    try:
        async with db.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    INSERT INTO telemetria_frames (
                        time, partido_id, jugador_id, frame_index,
                        longitud_zancada_cm, simetria_zancada_abi,
                        angulo_valgo_rodilla_deg, flexion_lumbar_deg,
                        rotacion_toraco_lumbar_deg, coordenada_x,
                        coordenada_y, en_zona_riesgo_esquina
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    now,
                    data.partido_id,
                    data.jugador_id,
                    data.frame_index,
                    data.longitud_zancada_cm,
                    data.simetria_zancada_abi,
                    data.angulo_valgo_rodilla_deg,
                    data.flexion_lumbar_deg,
                    data.rotacion_toraco_lumbar_deg,
                    data.coordenada_x,
                    data.coordenada_y,
                    data.en_zona_riesgo_esquina,
                )

                if data.fc_actual is not None:
                    await connection.execute(
                        """
                        INSERT INTO metricas_metabolicas (
                            time, partido_id, jugador_id, fc_actual, zona_fc
                        ) VALUES ($1, $2, $3, $4, $5)
                        """,
                        now,
                        data.partido_id,
                        data.jugador_id,
                        data.fc_actual,
                        data.zona_fc,
                    )
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo guardar la telemetría: {exc.__class__.__name__}. Verifica que el esquema SQL esté aplicado.",
        ) from exc

    return {"status": "success", "frame_index": data.frame_index}


@router.get("/fatigue-check/{partido_id}/{jugador_id}")
async def check_fatigue(
    partido_id: int,
    jugador_id: int,
    ventana_segundos: int = Query(default=30, ge=10, le=300),
):
    """Compare recent biomechanics with the player's opening baseline.

    This is an experimental screening heuristic, not a medical diagnosis.
    It requires at least five samples in both the baseline and recent windows.
    """
    if db.pool is None:
        raise HTTPException(status_code=503, detail="La base de datos no está conectada.")

    query = """
        WITH bounds AS (
            SELECT MIN(time) AS first_time, MAX(time) AS last_time
            FROM telemetria_frames
            WHERE partido_id = $1 AND jugador_id = $2
        ), baseline AS (
            SELECT COUNT(*) AS sample_count,
                   AVG(f.longitud_zancada_cm) AS stride,
                   AVG(f.simetria_zancada_abi) AS asymmetry,
                   AVG(f.flexion_lumbar_deg) AS lumbar
            FROM telemetria_frames f, bounds b
            WHERE f.partido_id = $1 AND f.jugador_id = $2
              AND f.time >= b.first_time
              AND f.time < b.first_time + make_interval(secs => $3)
        ), recent AS (
            SELECT COUNT(*) AS sample_count,
                   AVG(f.longitud_zancada_cm) AS stride,
                   AVG(f.simetria_zancada_abi) AS asymmetry,
                   AVG(f.flexion_lumbar_deg) AS lumbar
            FROM telemetria_frames f, bounds b
            WHERE f.partido_id = $1 AND f.jugador_id = $2
              AND f.time >= b.last_time - make_interval(secs => $3)
        ), latest_hr AS (
            SELECT fc_actual, zona_fc, time
            FROM metricas_metabolicas
            WHERE partido_id = $1 AND jugador_id = $2 AND fc_actual IS NOT NULL
            ORDER BY time DESC
            LIMIT 1
        )
        SELECT b.first_time, b.last_time,
               baseline.sample_count AS baseline_count,
               baseline.stride AS baseline_stride,
               baseline.asymmetry AS baseline_asymmetry,
               baseline.lumbar AS baseline_lumbar,
               recent.sample_count AS recent_count,
               recent.stride AS recent_stride,
               recent.asymmetry AS recent_asymmetry,
               recent.lumbar AS recent_lumbar,
               latest_hr.fc_actual, latest_hr.zona_fc, latest_hr.time AS hr_time
        FROM bounds b CROSS JOIN baseline CROSS JOIN recent
        LEFT JOIN latest_hr ON TRUE
    """

    try:
        async with db.pool.acquire() as connection:
            row = await connection.fetchrow(query, partido_id, jugador_id, ventana_segundos)
    except asyncpg.UndefinedTableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Faltan las tablas telemetria_frames o metricas_metabolicas. Aplica el esquema SQL antes de probar.",
        ) from exc
    except asyncpg.PostgresError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Error consultando la base de datos: {exc.__class__.__name__}.",
        ) from exc

    if row is None or row["first_time"] is None:
        raise HTTPException(status_code=404, detail="No hay telemetría para ese partido y jugador.")

    baseline_count = row["baseline_count"]
    recent_count = row["recent_count"]
    enough_samples = baseline_count >= 5 and recent_count >= 5
    enough_duration = (row["last_time"] - row["first_time"]).total_seconds() >= ventana_segundos

    if not enough_samples or not enough_duration:
        return {
            "status": "insufficient_data",
            "partido_id": partido_id,
            "jugador_id": jugador_id,
            "ventana_segundos": ventana_segundos,
            "muestras_referencia": baseline_count,
            "muestras_recientes": recent_count,
            "motivo_alerta": "Se requieren al menos 5 muestras en la referencia y en la ventana reciente, con datos separados por la duración de la ventana.",
            "alerta_generada": False,
            "nota": "Evaluación experimental; no es diagnóstico médico.",
        }

    baseline_stride = float(row["baseline_stride"] or 0)
    recent_stride = float(row["recent_stride"] or 0)
    baseline_asymmetry = float(row["baseline_asymmetry"] or 0)
    recent_asymmetry = float(row["recent_asymmetry"] or 0)
    baseline_lumbar = float(row["baseline_lumbar"] or 0)
    recent_lumbar = float(row["recent_lumbar"] or 0)

    # Transparent prototype score: normalized deterioration versus the player's
    # own opening window, weighted across three available biomechanical signals.
    stride_drop = max(0.0, (baseline_stride - recent_stride) / baseline_stride) if baseline_stride > 0 else 0.0
    asymmetry_rise = max(0.0, recent_asymmetry - baseline_asymmetry) / 10.0
    lumbar_rise = max(0.0, recent_lumbar - baseline_lumbar) / 30.0
    score = min(1.0, 0.45 * min(stride_drop / 0.25, 1.0)
                + 0.35 * min(asymmetry_rise, 1.0)
                + 0.20 * min(lumbar_rise, 1.0))
    alert = score >= 0.65

    result = {
        "status": "evaluated",
        "partido_id": partido_id,
        "jugador_id": jugador_id,
        "tiempo_evaluacion": row["last_time"].isoformat(),
        "ventana_segundos": ventana_segundos,
        "muestras_referencia": baseline_count,
        "muestras_recientes": recent_count,
        "inf_promedio": round(score, 3),
        "zancada_promedio": round(recent_stride, 2),
        "asimetria_promedio": round(recent_asymmetry, 2),
        "flexion_lumbar_promedio": round(recent_lumbar, 2),
        "frecuencia_cardiaca": row["fc_actual"],
        "zona_fc": row["zona_fc"],
        "alerta_generada": alert,
        "motivo_alerta": "Cambio biomecánico elevado respecto a la referencia inicial." if alert else "Sin cambio biomecánico elevado según los umbrales experimentales.",
        "nota": "Prototipo experimental basado en zancada, asimetría y flexión lumbar; no es diagnóstico ni debe usarse como único criterio de seguridad.",
    }

    if alert:
        await manager.broadcast_to_match(partido_id, {
            "tipo": "ALERTA_CRITICA_FATIGA",
            "prioridad": "ALTA",
            "data": result,
        })

    return result
