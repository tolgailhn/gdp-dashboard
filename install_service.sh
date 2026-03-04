#!/usr/bin/env bash
# Streamlit uygulamasını systemd service olarak kurar
# Kullanım: sudo bash install_service.sh
set -euo pipefail

# --- Kontroller ---
if [ "$EUID" -ne 0 ]; then
    echo "❌ Bu script root olarak çalıştırılmalı: sudo bash install_service.sh"
    exit 1
fi

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="streamlit-app"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Çalıştıran kullanıcıyı belirle (sudo yapan kişi)
RUN_USER="${SUDO_USER:-$(whoami)}"

echo "📦 Kurulum başlıyor..."
echo "   Uygulama dizini: $APP_DIR"
echo "   Kullanıcı: $RUN_USER"
echo "   Service: $SERVICE_NAME"
echo ""

# --- Service dosyasını oluştur ---
sed -e "s|__USER__|$RUN_USER|g" \
    -e "s|__APP_DIR__|$APP_DIR|g" \
    "$APP_DIR/streamlit-app.service" > "$SERVICE_FILE"

chmod 644 "$SERVICE_FILE"

# --- data dizini yoksa oluştur ---
mkdir -p "$APP_DIR/data"
chown "$RUN_USER":"$RUN_USER" "$APP_DIR/data"

# --- Systemd yeniden yükle ve başlat ---
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "✅ Kurulum tamamlandı!"
echo ""
echo "Yararlı komutlar:"
echo "  sudo systemctl status $SERVICE_NAME    # Durum"
echo "  sudo journalctl -u $SERVICE_NAME -f    # Canlı loglar"
echo "  sudo systemctl restart $SERVICE_NAME   # Yeniden başlat"
echo "  sudo systemctl stop $SERVICE_NAME      # Durdur"
echo ""

# Durumu göster
systemctl status "$SERVICE_NAME" --no-pager || true
