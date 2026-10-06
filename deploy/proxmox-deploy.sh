#!/usr/bin/env bash
#
# One-command Proxmox deploy for GPMC Daemon.
# Run this ON the Proxmox host (as root). It will:
#   1. create an unprivileged Debian 12 LXC container (random ID, DHCP)
#   2. install GPMC Daemon as a 24x7 systemd service
#   3. install + configure Syncthing (LAN-accessible GUI) for phone camera sync
#
# Usage on the Proxmox host:
#   bash deploy/proxmox-deploy.sh
# or standalone (clones the repo for you):
#   curl -fsSL https://raw.githubusercontent.com/robocrax/gpmc-daemon/main/deploy/proxmox-deploy.sh | bash
#
# Override any of these with env vars:
#   CTID= CT_HOSTNAME= CORES= MEMORY= DISK= BRIDGE= STORAGE= GPMC_PORT=
#
set -euo pipefail

CT_HOSTNAME="${CT_HOSTNAME:-gpmc}"
CORES="${CORES:-2}"
MEMORY="${MEMORY:-1024}"
SWAP="${SWAP:-512}"
DISK="${DISK:-20}"               # rootfs size in GB (photos buffer here before upload)
BRIDGE="${BRIDGE:-vmbr0}"
GPMC_PORT="${GPMC_PORT:-8080}"
REPO_URL="${REPO_URL:-https://github.com/robocrax/gpmc-daemon.git}"

log()  { printf '\033[1;33m>> %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

command -v pct >/dev/null || die "This must run on a Proxmox VE host (pct not found)."

# ---- locate the app source (checkout, /root, or clone) -------------------
if [[ -n "${GPMC_SRC:-}" && -d "$GPMC_SRC/app" ]]; then
  SRC="$GPMC_SRC"
else
  SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -d "$SELF/../app" ]]; then
    SRC="$(cd "$SELF/.." && pwd)"
  elif [[ -d /root/gpmc-daemon/app ]]; then
    SRC="/root/gpmc-daemon"
  else
    log "Cloning $REPO_URL ..."
    SRC="$(mktemp -d)/gpmc-daemon"
    git clone --depth 1 "$REPO_URL" "$SRC" || die "git clone failed (install git, or place the repo at /root/gpmc-daemon)."
  fi
fi
log "App source: $SRC"

# ---- pick an unused container id -----------------------------------------
if [[ -z "${CTID:-}" ]]; then
  for n in $(seq 150 999); do
    if ! pct status "$n" >/dev/null 2>&1 && ! qm status "$n" >/dev/null 2>&1; then CTID="$n"; break; fi
  done
fi
[[ -n "${CTID:-}" ]] || die "Could not find a free container ID."
# add a little randomness so repeat runs differ
if [[ -z "${CTID_FIXED:-}" ]]; then
  cand=$(( (RANDOM % 850) + 150 ))
  if ! pct status "$cand" >/dev/null 2>&1 && ! qm status "$cand" >/dev/null 2>&1; then CTID="$cand"; fi
fi
log "Container ID: $CTID"

# ---- storage detection ---------------------------------------------------
STORAGE="${STORAGE:-$(pvesm status --content rootdir 2>/dev/null | awk 'NR>1{print $1; exit}')}"
[[ -n "$STORAGE" ]] || die "No storage supporting container rootfs found. Set STORAGE=."
TMPL_STORAGE="$(pvesm status --content vztmpl 2>/dev/null | awk 'NR>1{print $1; exit}')"
TMPL_STORAGE="${TMPL_STORAGE:-local}"
log "rootfs storage: $STORAGE | template storage: $TMPL_STORAGE"

# ---- ensure a Debian 12 template is present ------------------------------
log "Ensuring Debian 12 template..."
pveam update >/dev/null 2>&1 || true
TEMPLATE="$(pveam available --section system 2>/dev/null | awk '/debian-12-standard/{print $2}' | sort -V | tail -1)"
[[ -n "$TEMPLATE" ]] || die "No debian-12-standard template available from pveam."
if ! pveam list "$TMPL_STORAGE" 2>/dev/null | grep -q "$TEMPLATE"; then
  log "Downloading template $TEMPLATE ..."
  pveam download "$TMPL_STORAGE" "$TEMPLATE"
fi
TEMPLATE_REF="$TMPL_STORAGE:vztmpl/$TEMPLATE"

# ---- create + start the container ----------------------------------------
log "Creating container $CTID ($CT_HOSTNAME)..."
pct create "$CTID" "$TEMPLATE_REF" \
  --hostname "$CT_HOSTNAME" \
  --cores "$CORES" --memory "$MEMORY" --swap "$SWAP" \
  --rootfs "$STORAGE:$DISK" \
  --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" \
  --unprivileged 1 --features nesting=1 \
  --onboot 1

log "Starting container..."
pct start "$CTID"

# ---- wait for DHCP + network --------------------------------------------
log "Waiting for the container to get an IP (DHCP)..."
IP=""
for _ in $(seq 1 60); do
  IP="$(pct exec "$CTID" -- bash -c "hostname -I 2>/dev/null | awk '{print \$1}'" 2>/dev/null || true)"
  [[ -n "$IP" ]] && break
  sleep 2
done
[[ -n "$IP" ]] || die "Container did not get an IP. Check your DHCP / bridge ($BRIDGE)."
log "Container IP: $IP"

ex() { pct exec "$CTID" -- bash -lc "$*"; }

# ---- base packages -------------------------------------------------------
log "Installing base packages (this takes a few minutes)..."
ex "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y -qq curl ca-certificates gnupg git python3 python3-venv python3-pip libheif1 >/dev/null"

# ---- Syncthing (official apt repo) --------------------------------------
log "Installing Syncthing..."
ex "curl -fsSL https://syncthing.net/release-key.gpg | gpg --dearmor -o /usr/share/keyrings/syncthing-archive-keyring.gpg"
ex "echo 'deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable' > /etc/apt/sources.list.d/syncthing.list"
ex "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y -qq syncthing >/dev/null"

# ---- push + install GPMC Daemon -----------------------------------------
log "Deploying GPMC Daemon into the container..."
TARBALL="$(mktemp --suffix=.tgz)"
tar czf "$TARBALL" -C "$SRC" app run.py requirements.txt install.sh
pct push "$CTID" "$TARBALL" /root/gpmc-src.tgz
rm -f "$TARBALL"
ex "mkdir -p /root/gpmc-src && tar xzf /root/gpmc-src.tgz -C /root/gpmc-src"
ex "cd /root/gpmc-src && GPMC_PORT=$GPMC_PORT bash install.sh"

# ---- configure Syncthing to run as the gpmc user, LAN-accessible GUI -----
log "Configuring Syncthing..."
ST_HOME="/var/lib/gpmc-daemon/syncthing"
ex "install -d -o gpmc -g gpmc '$ST_HOME'"
cat <<UNIT | pct exec "$CTID" -- bash -c "cat > /etc/systemd/system/gpmc-syncthing.service"
[Unit]
Description=Syncthing for GPMC
After=network-online.target
Wants=network-online.target

[Service]
User=gpmc
Group=gpmc
ExecStart=/usr/bin/syncthing serve --no-browser --no-restart --logflags=0 --home=$ST_HOME
Restart=on-failure
RestartSec=5
SuccessExitStatus=3 4
RestartForceExitStatus=3 4

[Install]
WantedBy=multi-user.target
UNIT
ex "systemctl daemon-reload && systemctl enable --now gpmc-syncthing.service"
# Syncthing writes its config on first start (no sudo needed). Wait for it, then
# bind the GUI to the LAN so you can pair your phone from a browser, and restart.
ex "for i in \$(seq 1 20); do [ -f '$ST_HOME/config.xml' ] && break; sleep 1; done"
ex "systemctl stop gpmc-syncthing.service"
ex "sed -i 's#<address>127.0.0.1:8384</address>#<address>0.0.0.0:8384</address>#' '$ST_HOME/config.xml'"
ex "systemctl start gpmc-syncthing.service"
sleep 2
DEVID="$(ex "grep -oE '[A-Z0-9]{7}(-[A-Z0-9]{7}){7}' '$ST_HOME/config.xml' | head -1" || true)"

# ---- done ----------------------------------------------------------------
cat <<DONE

============================================================
 ✅  GPMC Daemon deployed

   Container:        CTID $CTID  ($CT_HOSTNAME)  —  IP $IP
   GPMC web UI:      http://$IP:$GPMC_PORT
   Syncthing GUI:    http://$IP:8384
   Syncthing ID:     ${DEVID:-open the GUI to view}

 Next:
   1. Open the GPMC web UI and click "Connect" to add your Google account.
   2. Open the Syncthing GUI, set a GUI password (Actions -> Settings),
      and pair your phone (scan its Device ID under Actions -> Show ID).
   3. Share your phone's camera folder (Send Only) with this server and
      point it at /var/lib/gpmc-daemon/sync/<account>  (Receive Only).

 Manage:  pct enter $CTID   |   remove:  pct stop $CTID && pct destroy $CTID
============================================================
DONE
