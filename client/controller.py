import os
import subprocess
import threading
import time
from flask import Flask, jsonify

app = Flask(__name__)

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
    """Start new ffmpeg process, then terminate the old one after a short delay."""
    global ffmpeg_process
    new_process = start_ffmpeg(new_file)
    time.sleep(1)
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        ffmpeg_process.wait()
    ffmpeg_process = new_process

@app.route('/high_quality', methods=['GET'])
def high_quality():
    global current_quality
    if current_quality != "high":
        current_quality = "high"
        threading.Thread(target=switch_stream, args=(HIGH_QUALITY_FILE,), daemon=True).start()
        return jsonify(status="switched to high quality")
    return jsonify(status="already high quality")

@app.route('/low_quality', methods=['GET'])
def low_quality():
    global current_quality
    if current_quality != "low":
        current_quality = "low"
        threading.Thread(target=switch_stream, args=(LOW_QUALITY_FILE,), daemon=True).start()
        return jsonify(status="switched to low quality")
    return jsonify(status="already low quality")

def on_startup():
    """Initialize named pipe and start high-quality streaming."""
    global ffmpeg_process, current_quality
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    current_quality = "high"
    ffmpeg_process = start_ffmpeg(HIGH_QUALITY_FILE)

def on_shutdown():
    """Terminate the ffmpeg process gracefully."""
    global ffmpeg_process
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        ffmpeg_process.wait()

# Hook Flask app startup
if __name__ == '__main__':
    try:
        on_startup()
        app.run(host='0.0.0.0', port=8000)
    finally:
        on_shutdown()