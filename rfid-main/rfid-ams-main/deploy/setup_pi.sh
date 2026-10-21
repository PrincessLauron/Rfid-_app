#!/usr/bin/env bash
set -euo pipefail

# Basic Raspberry Pi setup script (run with sudo)

PROJECT_DIR="/opt/rfid-ams"
PYTHON_BIN="/usr/bin/python3"

apt update
apt install -y python3 python3-venv python3-pip nginx git pkg-config libffi-dev libssl-dev

mkdir -p "$PROJECT_DIR"
if [ -d "$PROJECT_DIR/.git" ]; then
  git -C "$PROJECT_DIR" fetch --all
  git -C "$PROJECT_DIR" reset --hard origin/main
else
  cp -r . "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

$PYTHON_BIN -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p /etc/rfid-ams
if [ ! -f /etc/rfid-ams/rfid-ams.env ]; then
  cat > /etc/rfid-ams/rfid-ams.env <<'ENV'
AMS_SQLITE_PATH=/opt/rfid-ams/backend/app/app.db
AMS_SECRET_KEY=replace_with_long_random_secret
AMS_INGEST_DEVICE_TOKEN=replace_with_scanner_token
AMS_API_BASE_URL=http://127.0.0.1:8000
AMS_API_TOKEN=replace_with_scanner_token
AMS_SERIAL_PORT=/dev/ttyAMA0
AMS_BAUDRATE=115200
ENV
  chmod 600 /etc/rfid-ams/rfid-ams.env
fi

alembic upgrade head
python -m backend.app.seed

cp deploy/backend.service /etc/systemd/system/backend.service
cp deploy/scanner.service /etc/systemd/system/scanner.service
systemctl daemon-reload
systemctl enable backend.service scanner.service
systemctl restart backend.service scanner.service

cp deploy/nginx.conf /etc/nginx/sites-available/rfid-ams
ln -sf /etc/nginx/sites-available/rfid-ams /etc/nginx/sites-enabled/rfid-ams
systemctl restart nginx

echo "Setup complete. Validate with: systemctl status backend.service scanner.service"
