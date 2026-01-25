#!/bin/bash

# Start Uvicorn
echo "Starting Uvicorn..."
uvicorn mindweaver.app:app --host 0.0.0.0 --port 8000 &

# Start Nginx
echo "Starting Nginx..."
nginx -g "daemon off;"
