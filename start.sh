#!/bin/sh
# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting second Python script..."
python main.py
# If you want processes to run concurrently, use '&'
# python script2.py &
# wait -n # wait for any background process to exit
