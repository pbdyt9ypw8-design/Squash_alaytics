from typing import Literal, Optional

from pydantic import BaseModel, Field


class TelemetryFrameCreate(BaseModel):
    partido_id: int = Field(..., ge=1, description="Identificador del partido", example=1)
    jugador_id: int = Field(..., ge=1, description="Identificador del jugador", example=1)
    frame_index: int = Field(..., ge=0, description="Índice del fotograma", example=101)
    longitud_zancada_cm: float = Field(..., ge=0, le=300, description="Longitud de zancada en centímetros", example=145.5)
    simetria_zancada_abi: float = Field(..., ge=0, le=100, description="Asimetría de zancada en porcentaje", example=2.5)
    angulo_valgo_rodilla_deg: float = Field(..., ge=-50, le=50, description="Ángulo estimado de rodilla", example=4.0)
    flexion_lumbar_deg: float = Field(..., ge=0, le=90, description="Proxy de inclinación del tronco; no diagnóstico", example=12.5)
    rotacion_toraco_lumbar_deg: float = Field(..., ge=-90, le=90, description="Rotación estimada", example=15.0)
    angulo_valgo_tobillo_deg: Optional[float] = Field(None, ge=-45, le=45)
    flexion_rodilla_deg: Optional[float] = Field(None, ge=0, le=180)
    elevacion_hombro_deg: Optional[float] = Field(None, ge=0, le=90)
    inclinacion_pelvis_deg: Optional[float] = Field(None, ge=-45, le=45)
    retardo_carga_raqueta_ms: Optional[int] = Field(None, ge=0, le=2000)
    coordenada_x: float
    coordenada_y: float
    en_zona_riesgo_esquina: bool = False
    fc_actual: Optional[int] = Field(None, ge=30, le=250)
    zona_fc: Optional[int] = Field(None, ge=1, le=5)


class EventoPuntoCreate(BaseModel):
    partido_id: int = Field(..., ge=1)
    jugador_id: int = Field(..., ge=1)
    set_numero: int = Field(..., ge=1)
    puntuacion_actual: str = Field(..., min_length=1, max_length=20)
    tipo_resultado: Literal["ganador", "error_no_forzado", "stroke", "let"]
    tipo_golpe: Optional[str] = Field(None, max_length=50)
    zona_origen_x: Optional[float] = Field(None, ge=0, le=6.4)
    zona_origen_y: Optional[float] = Field(None, ge=0, le=9.75)
    zona_destino_x: Optional[float] = Field(None, ge=0, le=6.4)
    zona_destino_y: Optional[float] = Field(None, ge=0, le=9.75)
    zona_rival_debil: bool = False
