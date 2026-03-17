from typing import Dict, Set, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Mapeia condomínio_id -> conjunto de conexões ativas
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, condominio_id: str):
        await websocket.accept()
        if condominio_id not in self.active_connections:
            self.active_connections[condominio_id] = set()
        self.active_connections[condominio_id].add(websocket)
        logger.info(f"Cliente conectado ao condomínio {condominio_id}")

    def disconnect(self, websocket: WebSocket, condominio_id: str):
        if condominio_id in self.active_connections:
            self.active_connections[condominio_id].discard(websocket)
            if not self.active_connections[condominio_id]:
                del self.active_connections[condominio_id]
            logger.info(f"Cliente desconectado do condomínio {condominio_id}")

    async def broadcast_to_condominio(self, condominio_id: str, message: dict):
        """Envia uma mensagem para todos os clientes conectados de um condomínio."""
        if condominio_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[condominio_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Erro ao enviar mensagem: {e}")
                    disconnected.add(connection)
            
            # Remove conexões mortas
            for conn in disconnected:
                self.active_connections[condominio_id].discard(conn)

    def get_active_condominio_count(self, condominio_id: str) -> int:
        return len(self.active_connections.get(condominio_id, set()))

manager = ConnectionManager()
