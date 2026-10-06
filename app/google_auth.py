"""Turn a Google 'EmbeddedSetup' oauth_token into a gpmc auth_data string.

This is the whole point of the easy-login flow: the user signs in once at
https://accounts.google.com/EmbeddedSetup, copies the `oauth_token` cookie, and
we exchange it server-side for a long-lived master token, then assemble the
auth_data credential that gpmc consumes. No mitmproxy, adb, or rooted phone.

The field set mirrors xob0t/gotohp's core/googleauth.go so the resulting
credential behaves identically to one captured from the official app.
"""
from __future__ import annotations

import os
import secrets
from urllib.parse import parse_qsl, urlencode

import httpx

EMBEDDED_SETUP_URL = "https://accounts.google.com/EmbeddedSetup"
_AUTH_ENDPOINT = "https://android.clients.google.com/auth"

# Signing certificates (public, well-known app fingerprints).
_GMS_SIG = "38918a453d07199354f8b19af05ec6562ced5788"
_PHOTOS_SIG = "24bb24c05e47e0aefa68a58a766179d9b613a600"
_PHOTOS_PKG = "com.google.android.apps.photos"
_PHOTOS_SERVICE = (
    "oauth2:openid https://www.googleapis.com/auth/mobileapps.native "
    "https://www.googleapis.com/auth/photos.native"
)
_GPS_VERSION = "240913000"
_USER_AGENT = "GoogleAuth/1.4 (Pixel XL PQ2A.190205.001); gzip"


class AuthError(Exception):
    """Raised when Google rejects the login or the token is unusable."""


def generate_android_id() -> str:
    return secrets.token_hex(8)


def normalize_oauth_token(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("oauth_token="):
        value = value[len("oauth_token="):]
    # People sometimes paste the whole "oauth_token\t<value>" DevTools row.
    value = value.split("\t")[-1].strip().strip('"')
    if not (16 <= len(value) <= 8192) or any(c in value for c in "\r\n"):
        raise AuthError("That doesn't look like an oauth_token. Copy the cookie value from Google sign-in.")
    return value


def parse_email(auth_data: str) -> str:
    try:
        d = dict(parse_qsl(auth_data))
        return d.get("Email", "") or "Google Account"
    except Exception:
        return "Google Account"


_FRIENDLY_ERRORS = {
    "BadAuthentication": "Google rejected the token. It is single-use and expires fast — grab a fresh oauth_token and try again.",
    "NeedsBrowser": "Google wants a fresh sign-in. Open the sign-in page again and redo the steps.",
    "MissingDroidguard": "Google rejected the device verification. Try again in a minute.",
}


def _exchange(oauth_token: str, android_id: str, proxy: str = "") -> dict:
    form = {
        "accountType": "HOSTED_OR_GOOGLE",
        "Email": "oauth-token@example.com",
        "has_permission": "1",
        "add_account": "1",
        "ACCESS_TOKEN": "1",
        "Token": oauth_token,
        "service": "ac2dm",
        "source": "android",
        "androidId": android_id,
        "device_country": "us",
        "operatorCountry": "us",
        "lang": "en",
        "sdk_version": "17",
        "google_play_services_version": _GPS_VERSION,
        "client_sig": _GMS_SIG,
        "callerSig": _GMS_SIG,
        "droidguard_results": "dummy123",
    }
    headers = {
        "Accept-Encoding": "identity",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": _USER_AGENT,
    }
    try:
        with httpx.Client(timeout=30, proxy=proxy or None, follow_redirects=False) as client:
            resp = client.post(_AUTH_ENDPOINT, data=form, headers=headers)
    except httpx.HTTPError as exc:
        raise AuthError(f"Could not reach Google authentication: {exc}") from exc

    if resp.status_code >= 300:
        raise AuthError(f"Google authentication returned HTTP {resp.status_code}")

    values: dict[str, str] = {}
    for line in resp.text.splitlines():
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            values[k] = v

    if "Error" in values:
        code = values["Error"]
        raise AuthError(_FRIENDLY_ERRORS.get(code, f"Google authentication failed: {code}"))

    master = values.get("Token", "")
    email = values.get("Email", "").strip()
    if not master:
        raise AuthError("Google did not return a master token. The oauth_token may be stale.")
    if "@" not in email:
        raise AuthError("Google did not return an account email.")
    return {"email": email, "master_token": master}


def build_auth_data(email: str, master_token: str, android_id: str) -> str:
    pairs = [
        ("androidId", android_id),
        ("app", _PHOTOS_PKG),
        ("callerPkg", _PHOTOS_PKG),
        ("callerSig", _PHOTOS_SIG),
        ("client_sig", _PHOTOS_SIG),
        ("device_country", "us"),
        ("Email", email),
        ("google_play_services_version", _GPS_VERSION),
        ("lang", "en_US"),
        ("oauth2_foreground", "1"),
        ("operatorCountry", "us"),
        ("sdk_version", "33"),
        ("service", _PHOTOS_SERVICE),
        ("source", "android"),
        ("Token", master_token),
    ]
    return urlencode(pairs)


def validate_auth_data(auth_data: str, proxy: str = "") -> str:
    """Prove the credential works by minting a bearer token. Returns the email."""
    try:
        from gpmc import Client
    except Exception as exc:  # pragma: no cover - gpmc always installed in prod
        raise AuthError(f"gpmc library is not available: {exc}") from exc
    try:
        client = Client(auth_data=auth_data, proxy=proxy, timeout=30, log_level="ERROR")
        _ = client.api.bearer_token  # forces the auth request
    except Exception as exc:
        raise AuthError(f"Google Photos rejected the credential: {exc}") from exc
    return parse_email(auth_data)


def connect_with_oauth_token(oauth_token: str, proxy: str = "") -> dict:
    """Full flow: oauth_token -> validated auth_data. Returns {email, auth_data, android_id}."""
    token = normalize_oauth_token(oauth_token)
    android_id = generate_android_id()
    exchanged = _exchange(token, android_id, proxy=proxy)
    auth_data = build_auth_data(exchanged["email"], exchanged["master_token"], android_id)
    email = validate_auth_data(auth_data, proxy=proxy)
    return {"email": email, "auth_data": auth_data, "android_id": android_id}


def connect_with_raw_auth(auth_data: str, proxy: str = "") -> dict:
    auth_data = (auth_data or "").strip()
    if "Token=" not in auth_data or "Email=" not in auth_data:
        raise AuthError("That auth_data looks incomplete (needs Email= and Token= fields).")
    email = validate_auth_data(auth_data, proxy=proxy)
    d = dict(parse_qsl(auth_data))
    return {"email": email, "auth_data": auth_data, "android_id": d.get("androidId", "")}
