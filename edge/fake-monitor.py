import subprocess
import time
import os
import websockets
import asyncio
import json
import random
from datetime import datetime
from measurements import Measurements

connected_clients = set()
measurements = Measurements()
LOCAL_IP = "192.168.1.16"  # Define the IP used by the WebSocket server

async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"🔌 Client connected: {websocket.remote_address}")
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"❌ Client disconnected: {websocket.remote_address}")

async def broadcast(message):
    if connected_clients:
        await asyncio.gather(*[client.send(message) for client in connected_clients])

async def generate_and_broadcast_measurements():
    while True:
        measurement = {
            "throughput": random.randint(1, 100),
            "packets_lost": random.randint(1, 100),
            "packet_loss_rate": random.randint(1, 100),
            "jitter": random.randint(1, 100),
            "speed": 20,
            "qoe": random.randint(1, 100)
        }
        await broadcast(json.dumps(measurement))
        await asyncio.sleep(2)

async def start_ws_server():
    server = await websockets.serve(ws_handler, LOCAL_IP, 8765)
    print("🌐 WebSocket server running at ws://192.168.1.16:8765")
    return server

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_ws_server())
    loop.create_task(generate_and_broadcast_measurements())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("📛 Stopping observer and server...")
        # observer.stop()
        # observer.join()
        pass

#tshark -i enp3s0 -b duration:2 -b files:100 -w output/capture.pcap -f "dst host 192.168.1.18 and udp port 8000"
#python3 -m pip install -U watchdog --break-system-packages