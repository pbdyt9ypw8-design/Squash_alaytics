from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from manager import manager

router = APIRouter(prefix="/ws", tags=["WebSockets Banquillo"])

@router.websocket("/match/{partido_id}")
async def match_websocket_endpoint(websocket: WebSocket, partido_id: int):
    """Canal WebSocket para el banquillo del partido_id."""
    await manager.connect(websocket, partido_id)
    try:
        while True:
            # Mantiene la conexión abierta escuchando al cliente
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, partido_id)
