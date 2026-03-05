#!/usr/bin/env bash
# Streamlit uygulamasını başlatan wrapper script
# systemd service tarafından çağrılır

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# .env dosyası varsa yükle (API anahtarları vb.)
if [ -f "$APP_DIR/.env" ]; then
    set -a
    source "$APP_DIR/.env"
    set +a
fi

# Virtual environment varsa aktifle
if [ -f "$APP_DIR/venv/bin/activate" ]; then
    source "$APP_DIR/venv/bin/activate"
elif [ -f "$APP_DIR/.venv/bin/activate" ]; then
    source "$APP_DIR/.venv/bin/activate"
fi

exec streamlit run streamlit_app.py \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.port "${STREAMLIT_PORT:-8502}"
