import subprocess
import os
import time
import threading
from fastapi import FastAPI

app = FastAPI()

# Global state
ffmpeg_process = None
current_quality = "high"
pipe_path = "input.pipe"

# Video sources
HIGH_QUALITY_FILE = "./input/webcam-10sec-0kmh-1.mp4"
LOW_QUALITY_FILE = "./input/webcam-10sec-0kmh-700.mp4"

def start_ffmpeg(input_file):
    """Start a new ffmpeg process that streams the given input file into the named pipe."""
    cmd = f"ffmpeg -re -stream_loop -1 -i {input_file} -f mpegts - | cat > {pipe_path}"
    return subprocess.Popen(cmd, shell=True, executable="/bin/bash", preexec_fn=os.setsid)

def switch_stream(new_file):
    """Switch to a new stream by starting a new process, then terminating the old one."""
    global ffmpeg_process
    # Start new process
    new_process = start_ffmpeg(new_file)

    # Allow brief time to stabilize
    time.sleep(1)

    # Kill old process if running
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        ffmpeg_process.wait()

    # Update reference
    ffmpeg_process = new_process

@app.on_event("startup")
def startup_event():
    global current_quality, ffmpeg_process
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    current_quality = "high"
    ffmpeg_process = start_ffmpeg(HIGH_QUALITY_FILE)

@app.get("/high_quality")
def switch_to_high_quality():
    global current_quality
    if current_quality != "high":
        current_quality = "high"
        threading.Thread(target=switch_stream, args=(HIGH_QUALITY_FILE,), daemon=True).start()
        return {"status": "switched to high quality"}
    return {"status": "already high quality"}

@app.get("/low_quality")
def switch_to_low_quality():
    global current_quality
    if current_quality != "low":
        current_quality = "low"
        threading.Thread(target=switch_stream, args=(LOW_QUALITY_FILE,), daemon=True).start()
        return {"status": "switched to low quality"}
    return {"status": "already low quality"}