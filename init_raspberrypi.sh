#!/bin/bash
set -e

# Zieluser bestimmen: wenn mit sudo gestartet -> SUDO_USER, sonst USER
TARGET_USER="${SUDO_USER:-$USER}"
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)

if [ -z "$TARGET_HOME" ]; then
  echo "Couldn't determine home of user '$TARGET_USER'. Aborting"
  exit 1
fi

BASE="$TARGET_HOME/Humidity_Temp_Monitor"
WWW="$BASE/www"
SERV="/etc/systemd/system"

echo "==> Target user:     $TARGET_USER"
echo "==> Target home:     $TARGET_HOME"
echo "==> Project base:    $BASE"
echo "==> Systemd dir:     $SERV"

echo "creating www folder if not existent..."
mkdir -p "$WWW"

echo "writing air_quality_logger.service ..."
sudo tee "$SERV/air_quality_logger.service" > /dev/null <<EOF
[Unit]
Description=Air Quality Logger (Flask)
After=network.target

[Service]
WorkingDirectory=$BASE
ExecStart=$BASE/venv/bin/python Pi/logger.py
Restart=always
User=$TARGET_USER
StandardOutput=append:$BASE/logger.log
StandardError=append:$BASE/logger.err

[Install]
WantedBy=multi-user.target
EOF

echo "writing air_quality_dashboard.service..."
sudo tee "$SERV/air_quality_dashboard.service" > /dev/null <<EOF
[Unit]
Description=Dashboard Renderer (PNG + HTML)
After=network.target

[Service]
WorkingDirectory=$BASE
ExecStart=$BASE/venv/bin/python Pi/render_dashboard.py
Restart=always
User=$TARGET_USER
StandardOutput=append:$BASE/dashboard.log
StandardError=append:$BASE/dashboard.err

[Install]
WantedBy=multi-user.target
EOF

echo "writing air_quality_http.service..."
sudo tee "$SERV/air_quality_http.service" > /dev/null <<EOF
[Unit]
Description=Air Quality HTTP Server
After=network.target

[Service]
WorkingDirectory=$WWW
ExecStart=/usr/bin/python3 -m http.server 8000
Restart=always
User=$TARGET_USER
StandardOutput=append:$BASE/httpserver.log
StandardError=append:$BASE/httpserver.err

[Install]
WantedBy=multi-user.target
EOF

echo "systemd daemon-reload..."
sudo systemctl daemon-reload

echo "activating services..."
sudo systemctl enable air_quality_logger.service
sudo systemctl enable air_quality_dashboard.service
sudo systemctl enable air_quality_http.service

echo "starting services..."
sudo systemctl restart air_quality_logger.service
sudo systemctl restart air_quality_dashboard.service
sudo systemctl restart air_quality_http.service

echo "Done"
