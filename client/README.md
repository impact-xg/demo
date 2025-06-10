# Preparation
mkfifo input.pipe
python3 -m pip install flask

# Execution
First run `stream.sh` then run `python3 controller.py`

# Network errors
sudo tc qdisc add dev enp0s3 root netem loss 1%

restore
sudo tc qdisc del dev enp0s3 root


# Manual execution for testing
ffmpeg -re -stream_loop -1 -i ./input/webcam-10sec-0kmh-1.mp4 -f mpegts - | cat > input.pipe