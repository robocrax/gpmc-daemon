#!/usr/bin/env bash
#
# Bare-metal installer for GPMC Daemon (no Docker).
# Installs into /opt/gpmc-daemon, runs 24x7 as a systemd service.
#
# Usage (from a checkout of this repo):
#   sudo ./install.sh
#
# Environment overrides:
#   GPMC_PORT=8080            web UI port
#   GPMC_DATA=/var/lib/gpmc-daemon   data root (config + sync live here)
#   GPMC_USER=gpmc           service user (created if missing)
#   UI_PASSWORD=...          optional initial web UI password
#
set -euo pipefail

GPMC_PORT="${GPMC_PORT:-8080}"
GPMC_DATA="${GPMC_DATA:-/var/lib/gpmc-daemon}"
GPMC_USER="${GPMC_USER:-gpmc}"
APP_DIR="/opt/gpmc-daemon"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root (sudo ./install.sh)." >&2
  exit 1
fi

echo ">> Installing system packages..."
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y --no-install-recommends python3 python3-venv python3-pip libheif1 ca-certificates
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y python3 python3-pip libheif
else
  echo "Unsupported distro: install python3, python3-venv and libheif manually." >&2
fi

echo ">> Creating service user '$GPMC_USER'..."
if ! id "$GPMC_USER" >/dev/null 2>&1; then
  useradd --system --home "$GPMC_DATA" --shell /usr/sbin/nologin "$GPMC_USER" || \
  useradd --system --home-dir "$GPMC_DATA" --shell /usr/sbin/nologin "$GPMC_USER"
fi

echo ">> Copying application to $APP_DIR..."
mkdir -p "$APP_DIR"
cp -r "$SRC_DIR/app" "$APP_DIR/"
cp "$SRC_DIR/run.py" "$SRC_DIR/requirements.txt" "$APP_DIR/"

echo ">> Creating data directories under $GPMC_DATA..."
mkdir -p "$GPMC_DATA/config" "$GPMC_DATA/sync" "$GPMC_DATA/gpmc_home"
chown -R "$GPMC_USER":"$GPMC_USER" "$GPMC_DATA" "$APP_DIR"

echo ">> Building Python virtualenv..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip -q
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
chown -R "$GPMC_USER":"$GPMC_USER" "$APP_DIR"

echo ">> Writing systemd unit..."
cat > /etc/systemd/system/gpmc-daemon.service <<UNIT
[Unit]
Description=GPMC Daemon - Google Photos uploader
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$GPMC_USER
Group=$GPMC_USER
WorkingDirectory=$APP_DIR
Environment=PORT=$GPMC_PORT
Environment=HOST=0.0.0.0
Environment=GPMC_CONFIG_DIR=$GPMC_DATA/config
Environment=GPMC_SYNC_DIR=$GPMC_DATA/sync
Environment=GPMC_HOME=$GPMC_DATA/gpmc_home
Environment=HOME=$GPMC_DATA/gpmc_home
${UI_PASSWORD:+Environment=UI_PASSWORD=$UI_PASSWORD}
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/run.py
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=full
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT

echo ">> Enabling and starting service..."
systemctl daemon-reload
systemctl enable --now gpmc-daemon.service

sleep 2
systemctl --no-pager --full status gpmc-daemon.service | head -n 12 || true

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "============================================================"
echo " GPMC Daemon is running."
echo "   Web UI:   http://${IP:-localhost}:$GPMC_PORT"
echo "   Data:     $GPMC_DATA   (drop media in $GPMC_DATA/sync/<account>)"
echo "   Logs:     journalctl -u gpmc-daemon -f"
echo "============================================================"
