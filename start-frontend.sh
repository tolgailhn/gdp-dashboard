#!/bin/bash
# Start the Next.js frontend dev server
cd "$(dirname "$0")/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Starting X AI Otomasyon Frontend..."
npm run dev
