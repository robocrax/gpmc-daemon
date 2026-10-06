#!/usr/bin/env python3
"""Bare-metal / direct entrypoint (no Docker).

    python run.py

Honors PORT, HOST, GPMC_CONFIG_DIR, GPMC_SYNC_DIR, etc. (see app/config.py).
"""
import uvicorn

from app import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, log_level="info")
