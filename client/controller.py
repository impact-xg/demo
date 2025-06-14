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
#ffmpeg_path = os.path.expanduser("~/bin/ffmpeg")
ffmpeg_path = "ffmpeg"

# Video sources
HIGH_QUALITY_FILE = "./input/webcam-20kmh-long-1.mp4"
LOW_QUALITY_FILE = "./input/webcam-20kmh-long-700.mp4"

fifo_fd = open(pipe_path, 'wb')

@app.route('/high_quality', methods=['GET'])
def high_quality():
    global current_quality
    global ffmpeg_process_low
    global ffmpeg_process_high
    global LOW_QUALITY_FILE
    global HIGH_QUALITY_FILE
    global pipe_path
    global fifo_fd
    
    if current_quality != "high":
        current_quality = "high"
        cmd = [ffmpeg_path, "-re", "-stream_loop", "-1", "-i", HIGH_QUALITY_FILE, "-input_format", "mjpeg", "-c", "copy", "-f", "mpegts", "-"]
        ffmpeg_process_high=subprocess.Popen(cmd, stdout=fifo_fd,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid)
        print(f"Started high-quality ffmpeg with PID: {ffmpeg_process_high.pid}")
        ffmpeg_process_low.terminate()
        ffmpeg_process_low.wait()
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
    global fifo_fd

    if current_quality != "low":
        current_quality = "low"
        cmd = [ffmpeg_path, "-re", "-stream_loop", "-1", "-i", LOW_QUALITY_FILE, "-input_format", "mjpeg", "-c", "copy", "-f", "mpegts", "-"]
        ffmpeg_process_low=subprocess.Popen(cmd, stdout=fifo_fd,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid)
        print(f"Started low-quality ffmpeg with PID: {ffmpeg_process_low.pid}")
        ffmpeg_process_high.terminate()
        ffmpeg_process_high.wait()
        return jsonify(status="switched to low quality")
    return jsonify(status="already low  quality")

def on_startup():
    """Initialize named pipe and start high-quality streaming."""
    global current_quality
    global ffmpeg_process_low
    global ffmpeg_process_high
    global LOW_QUALITY_FILE
    global HIGH_QUALITY_FILE
    global pipe_path
    global ffmpeg_path
    global fifo_fd

    current_quality="high"
    cmd = [ffmpeg_path, "-re", "-stream_loop", "-1", "-i", HIGH_QUALITY_FILE, "-input_format", "mjpeg", "-c", "copy",  "-f", "mpegts", "-"]
    ffmpeg_process_high=subprocess.Popen(cmd, stdout=fifo_fd,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid)
    print(f"Started high-quality ffmpeg with PID: {ffmpeg_process_high.pid}")

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
    print("hello!")
    try:
        on_startup()
        app.run(host='0.0.0.0', port=8001)
    finally:
        on_shutdown()