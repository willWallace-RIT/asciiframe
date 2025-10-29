#!/bin/bash


# Start Xvfb in the background
Xvfb :99 -screen 0 128x128x24 &
XVFB_PID=$!


# Set the DISPLAY variable
export DISPLAY=:99


# Wait for Xvfb to start
sleep 2


# Start your graphical application (e.g., a video player)
$1 &
APP_PID=$!


# Capture the Xvfb output and pipe it to the Python script
ffmpeg -video_size 128x128 -framerate 10 -f x11grab -i :99.0 -c:v png -f image2pipe - | python3 asciiterm.py


# Clean up processes when finished
kill $APP_PID
kill $XVFB_PID
