"""Pydantic request/response models."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AccountSettings(BaseModel):
    label: str = ""
    album_mode: str = "auto"          # auto | none | custom
    album_name: str = ""              # used when album_mode == custom
    delete_after: bool = True         # remove local file once uploaded
    saver: bool = False               # storage-saver quality instead of original
    use_quota: bool = False           # count uploads against Google quota
    recursive: bool = True
    skip_existing_filenames: bool = False
    threads: int = Field(3, ge=1, le=16)
    max_retries: int = Field(3, ge=1, le=10)
    enabled: bool = True
    heartbeat_url: str = ""


class AccountUpdate(AccountSettings):
    pass


class ConnectToken(BaseModel):
    """Finish the easy-login flow: exchange an EmbeddedSetup oauth_token."""
    oauth_token: str
    label: str = ""


class ConnectRaw(BaseModel):
    """Advanced path: paste an already-captured auth_data string."""
    auth_data: str
    label: str = ""


class GlobalSettings(BaseModel):
    sync_interval_min: int = Field(5, ge=1, le=1440)
    webhook_url: str = ""
    allow_reveal_auth: bool = False
    password: Optional[str] = None     # set/replace UI password; "" clears it
    theme: str = "system"              # system | dark | light


class LoginRequest(BaseModel):
    password: str
