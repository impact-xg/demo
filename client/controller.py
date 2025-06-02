import os
import subprocess
import threading
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Global state
ffmpeg_process_low = None
ffmpeg_process_high = None
current_quality = "high"
pipe_path = "input.pipe"
ffmpeg_path = os.path.expanduser("~/bin/ffmpeg")

# Video sources
HIGH_QUALITY_FILE = "./input/webcam-10sec-0kmh-1.mp4"
LOW_QUALITY_FILE = "./input/webcam-10sec-0kmh-700.mp4"

@app.route('/high_quality', methods=['GET'])
def high_quality():
    global current_quality
    global ffmpeg_process_low
    global ffmpeg_process_high
    global LOW_QUALITY_FILE
    global HIGH_QUALITY_FILE
    global pipe_path
    global ffmpeg_path
    ffmpeg_cmd = [
       ffmpeg_path, "-re", "-stream_loop", "1", "-i", "-i", HIGH_QUALITY_FILE,
        "-f", "mpegts", "-", "|", "cat", ">", pipe_path
    ]
    if current_quality != "high":
        current_quality = "high"
        ffmpeg_process_high=subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ffmpeg_process_low.terminate()
        return jsonify(status="switched to high quality")
    return jsonify(status="already high quality")

@app.route('/low_quality', methods=['GET'])
def low_quality():
    global current_quality
    global ffmpeg_process_low
    global ffmpeg_process_high
    global LOW_QUALITY_FILE
    global HIGH_QUALITY_FILE
    global pipe_path
    global ffmpeg_path
    ffmpeg_cmd = [
        ffmpeg_path, "-re", "-stream_loop", "1", "-i", "-i", HIGH_QUALITY_FILE,
        "-f", "mpegts", "-", "|", "cat", ">", pipe_path
    ]
    if current_quality != "low":
        current_quality = "low"
        ffmpeg_process_low=subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ffmpeg_process_high.terminate()
        return jsonify(status="switched to high quality")
    return jsonify(status="already high quality")

def on_startup():
    """Initialize named pipe and start high-quality streaming."""
    global current_quality
    global ffmpeg_process_low
    global ffmpeg_process_high
    global LOW_QUALITY_FILE
    global HIGH_QUALITY_FILE
    global pipe_path

    current_quality="high"
    ffmpeg_cmd = [
        "ffmpeg", "-re", "-stream_loop", "1", "-i", "-i", HIGH_QUALITY_FILE,
        "-f", "mpegts", "-", "|", "cat", ">", pipe_path
    ]
    ffmpeg_process_high=subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def on_shutdown():
    """Terminate the ffmpeg process gracefully."""
    global current_quality
    global ffmpeg_process_low
    global ffmpeg_process_high
    global LOW_QUALITY_FILE
    global HIGH_QUALITY_FILE
    global pipe_path
    if current_quality == "high" :
        if ffmpeg_process_high:
            ffmpeg_process_high.terminate()
    else:
        if ffmpeg_process_low:
            ffmpeg_process_low.terminate()



# Hook Flask app startup
if __name__ == '__main__':
    try:
        on_startup()
        app.run(host='0.0.0.0', port=8000)
    finally:
        on_shutdown()