from fastapi import WebSocket, WebSocketDisconnect
import logging
import asyncio
import time
from typing import Dict, Any
import uuid
from opentelemetry import trace, metrics

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

active_connections_gauge = meter.create_gauge(
    name="websocket_active_connections",
    description="Number of active WebSocket connections"
)

message_counter = meter.create_counter(
    name="websocket_messages_total",
    description="Total number of WebSocket messages processed"
)

connection_duration_histogram = meter.create_histogram(
    name="websocket_connection_duration_seconds",
    description="Duration of WebSocket connections in seconds"
)

broadcast_duration_histogram = meter.create_histogram(
    name="websocket_broadcast_duration_seconds",
    description="Time taken to broadcast messages to all connections"
)

broadcast_fanout_histogram = meter.create_histogram(
    name="websocket_broadcast_fanout",
    description="Number of connections a broadcast was sent to"
)

class WebSocketManager:
    def __init__(self):
        # Dictionary to store active connections with their metadata
        self.active_connections: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket) -> str:
        with tracer.start_as_current_span("websocket_connect") as span:
            await websocket.accept()
            connection_id = str(uuid.uuid4())
            
            current_time = time.time()
            self.active_connections[connection_id] = {
                "websocket": websocket,
                "connected_at": current_time,
                "message_count": 0
            }
            
            # Update metrics
            active_connections_gauge.set(len(self.active_connections))
            
            # Add span attributes
            span.set_attribute("connection_id", connection_id)
            span.set_attribute("total_connections", len(self.active_connections))
            
            logger.info(f"WebSocket connected: {connection_id}. Total connections: {len(self.active_connections)}")
            return connection_id
    
    def disconnect(self, connection_id: str):
        with tracer.start_as_current_span("websocket_disconnect") as span:
            if connection_id in self.active_connections:
                connection_info = self.active_connections[connection_id]
                duration = time.time() - connection_info["connected_at"]
                
                # Record metrics
                connection_duration_histogram.record(duration)
                
                del self.active_connections[connection_id]
                
                # Update active connections gauge
                active_connections_gauge.set(len(self.active_connections))
                
                # Add span attributes
                span.set_attribute("connection_id", connection_id)
                span.set_attribute("connection_duration", duration)
                span.set_attribute("message_count", connection_info['message_count'])
                span.set_attribute("remaining_connections", len(self.active_connections))
                
                logger.info(f"WebSocket disconnected: {connection_id}. "
                           f"Duration: {duration:.2f}s, Messages: {connection_info['message_count']}. "
                           f"Remaining connections: {len(self.active_connections)}")
    
    async def send_direct_message(self, message: str, connection_id: str):
        with tracer.start_as_current_span("websocket_send_direct_message") as span:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]["websocket"]
                try:
                    await websocket.send_text(message)
                    self.active_connections[connection_id]["message_count"] += 1
                    
                    # Record metrics
                    message_counter.add(1, {"message_type": "direct"})
                    
                    # Add span attributes
                    span.set_attribute("connection_id", connection_id)
                    span.set_attribute("message_length", len(message))
                    
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error_message", str(e))
                    logger.error(f"Error sending message to {connection_id}: {e}")
                    self.disconnect(connection_id)
    
    async def broadcast(self, message: str):
        with tracer.start_as_current_span("websocket_broadcast") as span:
            if not self.active_connections:
                logger.debug("No active connections to broadcast to")
                span.set_attribute("connection_count", 0)
                return
            
            start_time = time.time()
            connection_count = len(self.active_connections)
            
            logger.info(f"Broadcasting to {connection_count} connections: {message}")
            disconnected_connections = []
            successful_sends = 0
            
            for connection_id, connection_info in self.active_connections.items():
                websocket = connection_info["websocket"]
                try:
                    await websocket.send_text(message)
                    connection_info["message_count"] += 1
                    successful_sends += 1
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
            
            # Clean up disconnected connections
            for connection_id in disconnected_connections:
                self.disconnect(connection_id)
            
            # Record metrics
            broadcast_duration = time.time() - start_time
            broadcast_duration_histogram.record(broadcast_duration)
            broadcast_fanout_histogram.record(successful_sends)
            message_counter.add(successful_sends, {"message_type": "broadcast"})
            
            # Add span attributes
            span.set_attribute("connection_count", connection_count)
            span.set_attribute("successful_sends", successful_sends)
            span.set_attribute("failed_sends", len(disconnected_connections))
            span.set_attribute("message_length", len(message))
            span.set_attribute("broadcast_duration", broadcast_duration)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "id": conn_id,
                    "connected_at": info["connected_at"],
                    "message_count": info["message_count"],
                    "duration": asyncio.get_event_loop().time() - info["connected_at"]
                }
                for conn_id, info in self.active_connections.items()
            ]
        }