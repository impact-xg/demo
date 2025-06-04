mkfifo input.pipe
ffmpeg -re -stream_loop -1 -i ./input/webcam-10sec-0kmh-1.mp4 -f mpegts - | cat > input.pipe