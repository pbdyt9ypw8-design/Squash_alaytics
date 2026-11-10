from pydantic import BaseModel, Field
from typing import Optional

class TelemetryFrameCreate(BaseModel):
    partido_id: int
    jugador_id: int
    frame_index: int
    longitud_zancada_cm: float = Field(..., ge=0, le=300)      # Zancada lógica entre 0 y 300 cm
    simetria_zancada_abi: float = Field(..., ge=0, le=100)      # Porcentaje de asimetría (0 a 100%)
    angulo_valgo_rodilla_deg: float = Field(..., ge=-50, le=50) # Desviación de rodilla
    flexion_lumbar_deg: float = Field(..., ge=0, le=90)         # Inclinación de tronco
    rotacion_toraco_lumbar_deg: float = Field(..., ge=-90, le=90) # Torque en revés
    coordenada_x: float
    coordenada_y: float
    en_zona_riesgo_esquina: bool = False
    fc_actual: Optional[int] = None                             # Frecuencia cardíaca opcional
    zona_fc: Optional[int] = Field(None, ge=1, le=5)            # Zonas de FC (1 a 5)
