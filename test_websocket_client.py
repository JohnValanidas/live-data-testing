import asyncio
import websockets
import time
import argparse
from typing import List

# TODO: consider instrumenting this to track client connections and messages.
class WebSocketTestClient:
    def __init__(self, uri: str = "ws://localhost:8000/ws"):
        self.uri = uri
        self.clients: List[websockets.WebSocketServerProtocol] = []
    
    async def connect_client(self, client_id: int, duration: int = 30):
        try:
            async with websockets.connect(self.uri) as websocket:
                print(f"Client {client_id} connected")
                
                start_time = time.time()
                message_count = 0
                
                while time.time() - start_time < duration:
                    message = f"Test message {message_count} from client {client_id}"
                    await websocket.send(message)
                    message_count += 1
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        print(f"Client {client_id} received: {response}")
                    except asyncio.TimeoutError:
                        print(f"Client {client_id} timeout waiting for response")
                    
                    # Wait before next message
                    await asyncio.sleep(.12)
                
                print(f"Client {client_id} disconnecting after {message_count} messages")
                
        except Exception as e:
            print(f"Client {client_id} error: {e}")
    
    async def run_load_test(self, num_clients: int = 5, duration: int = 30):
        """Run a load test with multiple concurrent clients"""
        print(f"Starting load test with {num_clients} clients for {duration} seconds")
        
        tasks = []
        for i in range(num_clients):
            task = asyncio.create_task(self.connect_client(i, duration))
            tasks.append(task)
            
            # Stagger client connections slightly
            # TODO: consider removing this
            if i < num_clients - 1:
                await asyncio.sleep(0.5)
        
        await asyncio.gather(*tasks)
        print("Load test completed")


async def run_simple_test():
    client = WebSocketTestClient()
    await client.connect_client(0, 10)


async def run_load_test(num_clients: int, duration: int):
    client = WebSocketTestClient()
    await client.run_load_test(num_clients, duration)


def main():
    parser = argparse.ArgumentParser(description="WebSocket Load Test Client")
    parser.add_argument("--clients", "-c", type=int, default=1000, 
                       help="Number of concurrent clients (default: 1000)")
    parser.add_argument("--duration", "-d", type=int, default=200,
                       help="Test duration in seconds (default: 200)")
    parser.add_argument("--simple", "-s", action="store_true",
                       help="Run simple single client test")
    
    args = parser.parse_args()
    
    if args.simple:
        print("Running simple WebSocket test...")
        asyncio.run(run_simple_test())
    else:
        print(f"Running load test with {args.clients} clients for {args.duration} seconds...")
        asyncio.run(run_load_test(args.clients, args.duration))


if __name__ == "__main__":
    main()

