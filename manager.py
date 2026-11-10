from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Mapea partido_id -> lista de WebSockets conectados al banquillo
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, partido_id: int):
        await websocket.accept()
        if partido_id not in self.active_connections:
            self.active_connections[partido_id] = []
        self.active_connections[partido_id].append(websocket)

    def disconnect(self, websocket: WebSocket, partido_id: int):
        if partido_id in self.active_connections:
            self.active_connections[partido_id].remove(websocket)
            if not self.active_connections[partido_id]:
                del self.active_connections[partido_id]

    async def broadcast_to_match(self, partido_id: int, message: dict):
        """Envía una alerta en tiempo real a todas las pantallas conectadas a ese partido."""
        if partido_id in self.active_connections:
            for connection in self.active_connections[partido_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()
