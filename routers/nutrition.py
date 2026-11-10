from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from manager import manager

router = APIRouter(prefix="/nutrition", tags=["Estimación de hidratación (experimental)"])


class HydrationEstimateInput(BaseModel):
    partido_id: int = Field(..., ge=1, description="Identificador del partido", example=1)
    jugador_id: int = Field(..., ge=1, description="Identificador del jugador", example=1)
    peso_base_kg: float = Field(..., gt=20, le=250, description="Peso medido antes del partido, en kg", example=75)
    tasa_sudoracion_ml_min: float = Field(..., ge=0, le=100, description="Tasa de sudoración medida, no inferida por temperatura", example=15)
    minutos_transcurridos: int = Field(..., ge=0, le=600, description="Duración transcurrida en minutos", example=30)
    liquido_ingerido_ml: float = Field(0, ge=0, le=10000, description="Líquido ingerido durante el período, en ml", example=250)


@router.post("/estimate")
async def estimate_hydration(data: HydrationEstimateInput):
    """Estimate net fluid loss from supplied measurements; this is not medical advice."""
    sweat_loss_ml = data.tasa_sudoracion_ml_min * data.minutos_transcurridos
    net_loss_ml = sweat_loss_ml - data.liquido_ingerido_ml
    net_loss_pct = (net_loss_ml / (data.peso_base_kg * 1000)) * 100
    dehydration_flag = net_loss_pct >= 2.0

    result = {
        "status": "estimated",
        "partido_id": data.partido_id,
        "jugador_id": data.jugador_id,
        "minutos_transcurridos": data.minutos_transcurridos,
        "perdida_sudor_estimada_ml": round(sweat_loss_ml, 1),
        "liquido_ingerido_ml": round(data.liquido_ingerido_ml, 1),
        "balance_hidrico_estimado_ml": round(net_loss_ml, 1),
        "perdida_peso_estimada_pct": round(net_loss_pct, 2),
        "alerta_umbral_2pct": dehydration_flag,
        "alerta_gel": None,
        "recomendacion": (
            "La estimación alcanzó el umbral orientativo del 2%. Detén la actividad si hay síntomas y busca valoración profesional; este cálculo no diagnostica deshidratación."
            if dehydration_flag
            else "Estimación por debajo del umbral orientativo del 2%; no garantiza un estado de hidratación seguro."
        ),
        "nota": "Estimación experimental basada en entradas proporcionadas por el usuario. No estima la sudoración a partir de temperatura/FC ni determina dosis o momento de geles. No usar como criterio clínico o único criterio de seguridad.",
    }

    if dehydration_flag:
        try:
            await manager.broadcast_to_match(data.partido_id, {
                "tipo": "ALERTA_NUTRICIONAL",
                "prioridad": "MEDIA",
                "data": result,
            })
        except Exception as exc:
            raise HTTPException(status_code=503, detail="No se pudo transmitir la alerta nutricional.") from exc

    return result
