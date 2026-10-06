# GPMC Daemon

**Full-quality Google Photos backup for your homelab.** Your phone's camera roll
syncs to a server, and GPMC uploads it to Google Photos in original quality —
automatically, around the clock. Built on the reverse-engineered mobile API via
[gpmc](https://github.com/xob0t/gpmc), so uploads aren't compressed the way the
official Library API forces.

> Think of it as a self-hosted, always-on version of
> [gotohp](https://github.com/xob0t/gotohp): same upload engine, but it runs 24/7
> on a server with a web UI, multiple accounts, and a one-command Proxmox install.

![Dashboard](docs/dashboard.png)

---

## Why

Google Photos stopped offering free unlimited storage, and third-party apps that
use the official API can only touch photos *they* created — and they get
downscaled. GPMC uses the same API the Android app does, so **you** back up
**your own** photos at **full resolution**, on hardware you control.

```text
  📱 your phone  ──Syncthing──▶  🖥️ this server  ──gpmc──▶  ☁️ Google Photos
   camera roll                   watches a folder            original quality
```

## Features

- **One-click-ish login** — sign in to Google once, paste a single cookie value, and GPMC builds the upload credential for you. No `adb`, no mitmproxy, no rooted phone. Scan a QR to do the sign-in from your phone.
- **Multiple accounts** — back up the whole family; each account is an independent lane with its own folder and schedule.
- **Live dashboard** — real photo thumbnails of what's queued, per-file upload progress, countdown to the next run.
- **Runs anywhere** — Docker, a bare-metal systemd service, or a one-command Proxmox LXC. Headless and always-on.
- **Phone camera auto-upload** — pairs with Syncthing so new photos flow in by themselves.
- **Sensible defaults** — skips files already in your account (hash check), optional delete-after-upload to reclaim space, per-folder albums, storage-saver or original quality, retries, and webhook/heartbeat notifications.

---

## Quick start

### Option A — Proxmox (one command)

Run on your Proxmox host. Creates an unprivileged Debian LXC (random ID, DHCP),
installs GPMC as a service, and sets up Syncthing — ready to pair your phone.

```bash
curl -fsSL https://raw.githubusercontent.com/robocrax/gpmc-daemon/main/deploy/proxmox-deploy.sh | bash
```

When it finishes it prints the container IP, the GPMC URL (`http://<ip>:8080`),
and the Syncthing GUI (`http://<ip>:8384`).

### Option B — Docker

```bash
docker run -d --name gpmc-daemon --restart unless-stopped \
  -p 8080:8080 \
  -v ./data/config:/config \
  -v ./data/sync:/sync \
  robocrax/gpmc-daemon:latest
```

or with Compose:

```bash
git clone https://github.com/robocrax/gpmc-daemon && cd gpmc-daemon
docker compose up -d
```

### Option C — Bare metal (no Docker, 24/7)

Any Debian/Ubuntu box. Installs a `systemd` service that restarts on boot.

```bash
git clone https://github.com/robocrax/gpmc-daemon && cd gpmc-daemon
sudo ./install.sh
```

Service control: `systemctl status gpmc-daemon` · logs: `journalctl -u gpmc-daemon -f`.

### Option D — Run it directly (dev)

```bash
pip install -r requirements.txt
python run.py           # http://localhost:8080
```

Then open **http://localhost:8080** (or the address printed on your server).

---

## Connect a Google account

Click **Connect** in the web UI and follow the three steps:

1. **Open Google sign-in** (there's a button, and a QR to open it on your phone).
   Sign in and tap **I agree**. The page may hang on a spinner — that's fine.
2. **Copy the sign-in token:** open your browser's DevTools → **Application**
   (or **Storage**) → **Cookies** → `accounts.google.com`, and copy the value of
   the **`oauth_token`** cookie.
3. **Paste it** into GPMC. It exchanges the token for a long-lived upload
   credential and verifies it — done.

> The token is single-use and expires in seconds, so paste it promptly. GPMC
> stores only the resulting credential, never your Google password. Already have
> an `auth_data` string (e.g. from gotohp or ReVanced)? Use **"Paste a captured
> credential instead"** in the dialog.

---

## Phone camera auto-upload (Syncthing)

This is the hands-off part: your phone's new photos land in the account's server
folder on their own, and GPMC uploads them.

**On the server** (already installed by the Proxmox deploy; otherwise install Syncthing):

1. Open the Syncthing GUI at `http://<server-ip>:8384`. Set a GUI password under
   **Actions → Settings → GUI**.

**On your phone:**

2. Install a Syncthing client — Android: **Syncthing** or **Syncthing-Fork**;
   iOS: **Möbius Sync**.
3. Pair the devices: in the server GUI, **Actions → Show ID** shows a QR code —
   scan it from the phone app to add the server as a remote device. Accept the
   pairing back on the server.
4. On the phone, add your **camera / DCIM** folder and set its **folder type to
   "Send Only"** (your phone is the source of truth — nothing ever gets deleted
   from it). Share it with the server.
5. Back in the server GUI, **accept** the shared folder and set:
   - **Folder path:** `/var/lib/gpmc-daemon/sync/<account>` (match the account's
     folder name shown in GPMC — Proxmox/bare-metal) or
     `/sync/<account>` inside the container (Docker).
   - **Folder type: "Receive Only".**

That's it. New photos sync to the server and GPMC uploads them on the next cycle.

> **About "delete after upload":** GPMC can delete each file from the server once
> it's safely in Google Photos (on by default) to keep the server lean. Because
> the server folder is **Receive Only**, those deletions stay local — Syncthing
> will **not** remove anything from your phone, and won't re-download the deleted
> files. The server's Syncthing folder will show a growing "Local Additions"
> count; that's cosmetic. Prefer a spotless Syncthing UI? Turn off **Delete after
> upload** in the account's settings (your server will keep the originals).

---

## Configuration

Per-account options (albums, quality, threads, delete-after, pause, heartbeat)
live in the UI. Global options (backup interval, theme, UI password, webhook)
are in **Settings**. Everything can be seeded from environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `8080` | Web UI / API port |
| `HOST` | `0.0.0.0` | Bind address |
| `SYNC_INTERVAL_MINUTES` | `5` | How often to scan & upload |
| `UI_PASSWORD` | *(unset)* | Sets an initial password lock for the UI |
| `ALLOW_REVEAL_AUTH` | `false` | Allow copying an account's raw `auth_data` from the UI |
| `GPMC_PROXY` | *(unset)* | Outbound proxy `http://user:pass@host:port` |
| `GPMC_CONFIG_DIR` | `/config` | Database, credentials, caches |
| `GPMC_SYNC_DIR` | `/sync` | Media root — one subfolder per account |
| `GPMC_HOME` | `<config>/gpmc_home` | gpmc's dedup cache (keep persistent) |

---

## How it works

- A background **folder watcher** keeps each account's queue preview live.
- A **scheduler** runs an upload cycle per account on your interval (and on demand).
- Each cycle calls `gpmc` in-process with a progress callback, so the dashboard
  shows real per-file progress. Files already in your account are skipped by hash.
- Credentials and settings live in a small SQLite database under `GPMC_CONFIG_DIR`.

## Troubleshooting

- **"Needs attention" / auth errors:** the account's credential was revoked or is
  stale. Open the account menu → **Reconnect** and redo the sign-in.
- **Nothing uploads:** check the file landed in the right folder and isn't a
  Syncthing temp file (`.syncthing.*`, `~syncthing~*`). Hit **Back up now**.
- **Logs:** per-account **Activity** tab in the UI, or `journalctl -u gpmc-daemon -f`
  (bare metal) / `docker logs -f gpmc-daemon` (Docker).

## Credits & disclaimer

Upload engine: [xob0t/gpmc](https://github.com/xob0t/gpmc). GUI inspiration and
the login flow: [xob0t/gotohp](https://github.com/xob0t/gotohp).

This is an **unofficial** tool that uses a reverse-engineered API with **your own**
Google account. It isn't affiliated with or endorsed by Google. Use it on accounts
you own.
