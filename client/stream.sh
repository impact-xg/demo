#!/bin/bash

SERVER_RTP="192.168.154.10:8000"


# Stream video via ffmpeg
# ~/bin/ffmpeg -re -i webcam-10sec-0kmh-1.mp4 -input_format mjpeg -c copy  -f rtp_mpegts "rtp://192.168.1.10?pkt_size=1316"
~/bin/ffmpeg -re \
  -i ./input/webcam-10sec-0kmh-1.mp4 \
  -input_format mjpeg \
  -c copy \
  -f rtp_mpegts "rtp://${SERVER_RTP}?pkt_size=1316"