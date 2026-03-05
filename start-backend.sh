#!/bin/bash
# Start the FastAPI backend server
cd "$(dirname "$0")"
echo "Starting X AI Otomasyon Backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
