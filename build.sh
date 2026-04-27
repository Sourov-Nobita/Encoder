#!/usr/bin/env bash

set -e

# Create bin directory
mkdir -p bin

# Download FFmpeg
if [ ! -f "bin/ffmpeg" ]; then
    echo "Downloading FFmpeg..."
    curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz
    tar -xJf ffmpeg.tar.xz
    cp ffmpeg-*-amd64-static/ffmpeg bin/
    cp ffmpeg-*-amd64-static/ffprobe bin/
    rm -rf ffmpeg-*-amd64-static ffmpeg.tar.xz
fi

# Download Aria2
if [ ! -f "bin/aria2c" ]; then
    echo "Downloading Aria2..."
    # Using a known working static build from asdo92
    curl -L https://github.com/asdo92/aria2-static-builds/releases/download/v1.37.0/aria2-1.37.0-linux-gnu-64bit-build1.tar.bz2 -o aria2.tar.bz2
    tar -xjf aria2.tar.bz2
    cp aria2-1.37.0-linux-gnu-64bit-build1/aria2c bin/
    rm -rf aria2-1.37.0-linux-gnu-64bit-build1 aria2.tar.bz2
fi

chmod +x bin/*

# Install python dependencies
pip install -r requirements.txt
