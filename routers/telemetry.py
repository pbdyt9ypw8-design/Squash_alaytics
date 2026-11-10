from fastapi import APIRouter, HTTPException, status
from models import TelemetryFrameCreate
from database import db
from manager import manager
from datetime import datetime, timezone

router = APIRouter(prefix="/telemetry", tags=["Telemetría y Biomecánica"])

@router.post("/frame", status_code=status.HTTP_201_CREATED)
async def ingest_frame(data: TelemetryFrameCreate):
    """Recibe y guarda un fotograma procesado por el sistema de visión artificial."""
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
                datetime.now(timezone.utc),
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
                data.en_zona_riesgo_esquina
            )
            
            if data.fc_actual is not None:
                await connection.execute(
                    """
                    INSERT INTO metricas_metabolicas (
                        time, partido_id, jugador_id, fc_actual, zona_fc
                    ) VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (time, partido_id, jugador_id) 
                    DO UPDATE SET fc_actual = EXCLUDED.fc_actual, zona_fc = EXCLUDED.zona_fc
                    """,
                    datetime.now(timezone.utc),
                    data.partido_id,
                    data.jugador_id,
                    data.fc_actual,
                    data.zona_fc
                )
    return {"status": "success", "frame_index": data.frame_index}


@router.get("/fatigue-check/{partido_id}/{jugador_id}")
async def check_fatigue(partido_id: int, jugador_id: int):
    """Ejecuta el análisis de fatiga y avisa al banquillo si hay riesgo crítico."""
    async with db.pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT * FROM detectar_fatiga_critica_en_tiempo_real($1, $2, 30)",
            partido_id,
            jugador_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="No hay suficientes datos recientes.")
            
        alert_data = {
            "partido_id": row["partido_id"],
            "jugador_id": row["jugador_id"],
            "tiempo_evaluacion": row["tiempo_evaluacion"].isoformat(),
            "inf_promedio": float(row["inf_promedio"]),
            "zancada_promedio": float(row["zancada_promedio"]),
            "asimetria_promedio": float(row["asimetria_promedio"]),
            "flexion_lumbar_promedio": float(row["flexion_lumbar_promedio"]),
            "alerta_generada": row["alerta_generada"],
            "motivo_alerta": row["motivo_alerta"]
        }

        if row["alerta_generada"]:
            await manager.broadcast_to_match(partido_id, {
                "tipo": "ALERTA_CRITICA_FATIGA",
                "prioridad": "ALTA",
                "data": alert_data
            })
            
        return alert_data
