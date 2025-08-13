#!/bin/bash
set -e

# Start FastAPI backend on port 8000
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait a moment for backend to start
sleep 2

# Serve frontend static files on port 5173
cd frontend_dist
python3 -m http.server 5173 --bind 0.0.0.0