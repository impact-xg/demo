#!/bin/bash

INPUT="rtp://192.168.154.10:5000"
OUTPUT="udp://192.168.154.10:1234?pkt_size=1316"

~/bin/ffmpeg -i ${INPUT} -c copy -f mpegts ${OUTPUT}

#vlc rtsp://192.168.154.10:8554/camera