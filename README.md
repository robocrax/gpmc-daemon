# GPMC Controller

![Docker Image Size](https://img.shields.io/docker/image-size/robocrax/gpmc-daemon/latest)
![Docker Pulls](https://img.shields.io/docker/pulls/robocrax/gpmc-daemon)
![License](https://img.shields.io/github/license/robocrax/gpmc-daemon)

**GPMC Controller** is a lightweight, automated web controller and daemon for syncing media files directly to Google Photos using [GPMC](https://github.com/xob0t/gpmc).

Built with a fast Python/FastAPI backend and a modern Tailwind CSS frontend, it offers per-profile media directory monitoring, live queues, automatic retries, webhook alerts, and rate-limit prevention.

---

## 📸 Screenshots

> **Dashboard Overview**
> <img width="1008" height="606" alt="image" src="https://github.com/user-attachments/assets/94ffe136-4285-4040-a87b-1aefd4ebbde9" />
> *View multi-account profile sync status, live queue previews, and countdown timers.*

<br />

> **Profile Settings**
> <img width="1044" height="600" alt="image" src="https://github.com/user-attachments/assets/f149dc84-1dcc-47a9-8a0a-c6fa79aa2983" />
> *Configure upload delays, concurrent threads, and webhook alerts.*

---

## ✨ Key Features

* 🚀 **Multi-Account Management**: Manage and schedule independent Google Photos sync profiles simultaneously. It's not only you in the family, your nephew also wants free uploads.
* 📦 **Live Media Queue Canvas**: Real-time visual previews for pending photos and videos (`.jpg`, `.png`, `.heic`, `.mp4`, `.mov`).
* ⏱️ **Google Rate-Limit Protection**: Configurable upload cycle delays with a real-time countdown timer to mimic natural phone backup behavior.
* ⚡ **Multi-Threaded Execution**: Boost upload throughput with configurable concurrent thread limits (default: 3 threads).
* 🔔 **Webhook Alerts**: Send instant batch completion and error reports to Discord or Slack.

---

## 🚀 Quick Start with Docker

Run GPMC Controller instantly using Docker:

```bash
docker run -d \
  --name gpmc-controller \
  -p 8080:8080 \
  -v ./config:/config \
  -v ./sync:/sync \
  robocrax/gpmc-daemon:latest
```

Or using compose file:

```yaml
services:
  gpmc-daemon:
    ports:
      - 8080:8080
    volumes:
      - ./config:/config
      - ./sync:/sync
    image: robocrax/gpmc-daemon:latest
```

Open your browser and navigate to `http://localhost:8080`.

📁 Mounting Folders
-------------------

-   `/config`: Stores profiles and auth data (SQLite database).

-   `/sync`: Root directory containing profile subfolders (e.g. `/sync/profile_1`, `/sync/profile_2`). Media dropped inside these folders will automatically sync to Google Photos using the profile's auth data.

⚙️ Environment Variables
------------------------

| **Variable** | **Default** | **Description** |
| --- | --- | --- |
| `PORT` | `8080` | Web UI and API HTTP port. |
| `UI_PASSWORD` | *(None)* | Optional initial admin password to lock the Web UI. |
| `SYNC_INTERVAL_MINUTES` | `5` | Initial delay between scheduled upload cycles. I personally use 60 as i can wait for an hour, depends on your patience |

🛠️ Obtaining `AUTH_DATA`
-------------------------

GPMC uses mobile authentication data captured from Android Google Photos client traffic.

For step-by-step instructions on obtaining your `AUTH_DATA` string, consult [GPMC Auth Documentation](https://github.com/xob0t/gpmc#auth_data-where-do-i-get-mine).

🤝 Next features?
---------------

Might add a built-in syncthing or Resilio sync inside this so it can directly connect to iPhones or other devices without having to setup a separate sync.
