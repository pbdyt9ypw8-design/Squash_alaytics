from typing import Optional

from pydantic import BaseModel, Field


class TelemetryFrameCreate(BaseModel):
    partido_id: int = Field(..., description="Identificador del partido", example=1)
    jugador_id: int = Field(..., description="Identificador del jugador", example=1)
    frame_index: int = Field(..., ge=0, description="Índice del fotograma", example=101)
    longitud_zancada_cm: float = Field(
        ..., ge=0, le=300, description="Longitud de zancada en centímetros", example=145.5
    )
    simetria_zancada_abi: float = Field(
        ..., ge=0, le=100, description="Asimetría de zancada en porcentaje (0–100)", example=2.5
    )
    angulo_valgo_rodilla_deg: float = Field(
        ..., ge=-50, le=50, description="Ángulo de valgo de rodilla en grados", example=4.0
    )
    flexion_lumbar_deg: float = Field(
        ..., ge=0, le=90, description="Flexión lumbar en grados", example=12.5
    )
    rotacion_toraco_lumbar_deg: float = Field(
        ..., ge=-90, le=90, description="Rotación toraco-lumbar en grados", example=15.0
    )
    coordenada_x: float = Field(..., description="Coordenada X en la cancha", example=3.2)
    coordenada_y: float = Field(..., description="Coordenada Y en la cancha", example=4.1)
    en_zona_riesgo_esquina: bool = Field(
        False, description="Indica si el jugador está en una zona de riesgo", example=False
    )
    fc_actual: Optional[int] = Field(
        None, ge=30, le=250, description="Frecuencia cardíaca en latidos por minuto", example=165
    )
    zona_fc: Optional[int] = Field(
        None, ge=1, le=5, description="Zona de frecuencia cardíaca (1–5)", example=4
    )
