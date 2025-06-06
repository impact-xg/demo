import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
import os
import websockets
import asyncio
import json
from datetime import datetime
from measurements import Measurements
from predictor import Predictor

WATCH_FOLDER = "./output"
LOCAL_IP = "192.168.154.10"
PATH_TO_GRU = "/home/ubuntu/demo/edge/qoe_prediction_model/models/gru_basic.h5"
PATH_TO_SCALER = "/home/ubuntu/demo/edge/qoe_prediction_model/models/scaler.save"

connected_clients = set()
measurements = Measurements()

qoe_predictor = Predictor(
    model_path= PATH_TO_GRU,  # Path to the model
    scaler_path=PATH_TO_SCALER,  # Path to the scaler
    seq_length=5,                # Sequence length (should match training), 5 is the default
    use_stats=True              # Set this based on how you trained the model
)


async def ws_handler(websocket):
    connected_clients.add(websocket)
    print(f"🔌 Client connected: {websocket.remote_address}")
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"❌ Client disconnected: {websocket.remote_address}")

async def start_ws_server():
    server = await websockets.serve(ws_handler,LOCAL_IP, 8765)
    print("🌐 WebSocket server running at ws://192.168.154.10:8765")
    return server

class PCAPHandler(FileSystemEventHandler):
    def on_closed(self, event):
        if not event.is_directory and event.src_path.endswith(".pcap"):
            #print(f"New file detected: {event.src_path}")
            self.process_pcap(event.src_path)

    async def broadcast(self, message):
        if connected_clients:
            await asyncio.gather(*(client.send(message) for client in connected_clients))
            #print(f"📤 Sent message to {len(connected_clients)} client(s).")
        #else:
        #    print("⚠️ No clients connected to send message.")
    #def on_any_event(self, event: FileSystemEvent) -> None:
    #    print(event)

    def process_pcap(self, file_name):
        cmd = [
            "tshark",
            "-r", file_name,
            "-d", "udp.port==5000,rtp",
            "-q",
            "-z", "rtp,streams",
            "-z", "io,stat,0"
        ]
        #print(f"Running tshark on {file_name}...")
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output = result.stdout
            #print(output)
            lines = output.split("\n")
            words = lines[4].split(" ")
            interval= float(words[2])
            #print("words:", interval )
            
            words = lines[12].split(" ")
            
            filtered_arr = [s for s in words if s.strip()]
            bytes = int(filtered_arr[7])*8/1000
            words = lines[16].split(" ")
            filtered_arr = [s for s in words if s.strip()]
            #loss = float(filtered_arr[10].strip("()%"))
            plost = filtered_arr[10]
            #loss = filtered_arr[11]
            loss = float(filtered_arr[11].strip("()%"))
            mean = float(filtered_arr[16])
            formatted_mean = "{:.3f}".format(mean)
            speed = 20 #get_speed()
            measurement = {}
            measurement["throughput"] = round(bytes/interval, 1)
            measurement["packets_lost"] = float(plost)
            measurement["packet_loss_rate"] = loss
            measurement["jitter"] = float(formatted_mean)
            measurement["speed"] = speed
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            measurements.add_measurement(timestamp, measurement)
            trace_data = measurements.get_measurements()
            measurement["qoe"]=0
            if trace_data:
                result = qoe_predictor.infer(trace_data)
                measurement["qoe"]= result
            print(measurement)
            asyncio.run(self.broadcast(json.dumps(measurement)))
        except Exception as e:
            print(e)

if __name__ == "__main__":
    event_handler = PCAPHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_FOLDER, recursive=False)
    observer.start()
    print(f"Monitoring {WATCH_FOLDER} for new .pcap files...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_ws_server())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("🛑 Stopping observer and server...")
        observer.stop()
        observer.join()

#tshark -i enp3s0 -b duration:2 -b files:100 -w output/capture.pcap -f "dst host 192.168.1.18 and udp port 8000"
#python3 -m pip install -U watchdog --break-system-packages