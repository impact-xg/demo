#!/bin/bash

INPUT="rtp://192.168.1.18:5000"
OUTPUT="udp://192.168.1.18:1234?pkt_size=1316"

~/bin/ffmpeg -i ${INPUT} -c copy -f mpegts ${OUTPUT}

#vlc rtsp://192.168.1.18:8554/camera