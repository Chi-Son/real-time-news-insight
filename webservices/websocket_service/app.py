from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_service")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        logger.info(f"Broadcasting to {len(self.active_connections)} clients")
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "active_connections": len(manager.active_connections)
    }

@app.websocket("/ws/topics")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection attempt")
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.post("/ws-push/topics")
async def push_topics(payload: dict = Body(...)):
    logger.info(f"Received push request with {len(payload.get('data', []))} topics")
    await manager.broadcast(payload)
    return {"status": "ok"}
