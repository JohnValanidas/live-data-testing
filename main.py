

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
import asyncio
import json
from typing import List, Dict, Any
import uuid

from listener import get_postgres_listener
from websocket_manager import WebSocketManager
from telemetry import setup_telemetry, instrument_app

# Initialize OpenTelemetry before creating the app
setup_telemetry()

app = FastAPI()

# Apply instrumentation to the app
instrument_app(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a console handler and set its formatter
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Global connection manager instance
websocket_manager = WebSocketManager()


@app.get('/')
def root():
    return {"message": "hello"}


@app.get('/ws/stats')
def get_websocket_stats():
    return websocket_manager.get_connection_stats()


@app.on_event("startup")
async def startup_event():
    # Start the database notification listener
    asyncio.create_task(listen())
    logger.info("Database notification listener started")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = await websocket_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from {connection_id}: {data}")
            
            # Echo the message back to the sender
            response = f"Echo from server: {data}"
            await websocket_manager.send_personal_message(response, connection_id)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)


async def listen():
    listener = await get_postgres_listener()
    queue = listener.listen()

    try:
        while notify := await queue.get():
            logger.info(f"Database notification: {notify}")
            
            # Broadcast the notification to all connected WebSocket clients
            notification_message = json.dumps({
                "type": "database_notification",
                "channel": notify.channel,
                "payload": notify.payload,
            })
            
            await websocket_manager.broadcast(notification_message)
            
    except Exception as e:
        logger.error(f"Listen.error {e}")