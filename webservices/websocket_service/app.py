from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
import json
import time
from shared.redis_connect import redis_connection

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_service")

# Redis connection
redis = redis_connection()

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
crisis_manager = ConnectionManager()

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "active_connections": len(manager.active_connections),
        "crisis_connections": len(crisis_manager.active_connections)
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

@app.websocket("/ws/crisis")
async def crisis_websocket_endpoint(websocket: WebSocket):
    logger.info("Crisis WebSocket connection attempt")
    await crisis_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Crisis WebSocket disconnected")
        crisis_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Crisis WebSocket error: {e}")
        crisis_manager.disconnect(websocket)

@app.post("/ws-push/crisis")
async def push_crisis_alerts(payload: dict = Body(...)):
    crisis_data = payload.get('data', [])
    logger.info(f"Received crisis alert push with {len(crisis_data)} alerts")
    
    # Lưu từng crisis alert vào Redis với TTL 1 ngày (86400 giây)
    for alert in crisis_data:
        topic_id = alert.get('topic_id')
        if topic_id:
            redis_key = f"crisis:alert:{topic_id}"
            
            # Thêm timestamp vào alert
            alert['stored_at'] = int(time.time())
            
            # Lưu vào Redis với TTL 1 ngày
            redis.setex(
                redis_key,
                86400,  # 24 giờ = 86400 giây
                json.dumps(alert)
            )
            
            # Thêm vào sorted set để dễ query (score = crisis_score)
            redis.zadd(
                "crisis:alerts:ranking",
                {topic_id: alert.get('crisis_score', 0)}
            )
            redis.expire("crisis:alerts:ranking", 86400)
            
            logger.info(f"Stored crisis alert for topic {topic_id} in Redis (TTL: 24h)")
    
    # Broadcast qua WebSocket
    await crisis_manager.broadcast(payload)
    return {"status": "ok", "stored_count": len(crisis_data)}

@app.get("/api/crisis/alerts")
async def get_crisis_alerts(limit: int = 20):
    """
    Lấy danh sách các crisis alerts đang active (trong vòng 24h)
    """
    try:
        # Lấy top crisis alerts từ sorted set
        raw = redis.zrevrange("crisis:alerts:ranking", 0, limit - 1, withscores=True)
        
        alerts = []
        for topic_id, crisis_score in raw:
            tid = topic_id.decode() if isinstance(topic_id, bytes) else topic_id
            redis_key = f"crisis:alert:{tid}"
            
            # Lấy chi tiết alert từ Redis
            alert_data = redis.get(redis_key)
            if alert_data:
                alert = json.loads(alert_data)
                alerts.append(alert)
        
        return {
            "status": "ok",
            "count": len(alerts),
            "data": alerts,
            "updated_at": int(time.time())
        }
    except Exception as e:
        logger.error(f"Failed to get crisis alerts: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }
