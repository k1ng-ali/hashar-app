"""
Проверка ID-токена Google (вход через Google).

Фронтенд получает ID-токен от Google Identity Services (сайт) или от нативного входа (Android)
и присылает его на /auth/google. Токен — JWT, подписанный ключами Google (RS256):
проверяем подпись по открытым ключам Google, издателя, срок и то, что токен выпущен для нашего
OAuth-клиента (aud входит в GOOGLE_CLIENT_IDS). Ключи кэшируются на время из Cache-Control.
"""

import asyncio
import json
import re
import time
import urllib.request

from jose import JWTError, jwt

from app.core.config import settings

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
# Если Google не прислал max-age — держим ключи час
DEFAULT_CERTS_TTL = 60 * 60
CERTS_TIMEOUT_SECONDS = 10

_certs: dict | None = None
_certs_expire_at = 0.0
_certs_lock = asyncio.Lock()


class GoogleTokenError(Exception):
    """Токен не прошёл проверку (подпись, срок, издатель или чужой клиент)."""


def _download_certs() -> tuple[dict, int]:
    with urllib.request.urlopen(GOOGLE_CERTS_URL, timeout=CERTS_TIMEOUT_SECONDS) as response:
        match = re.search(r"max-age=(\d+)", response.headers.get("Cache-Control", ""))
        return json.loads(response.read()), int(match.group(1)) if match else DEFAULT_CERTS_TTL


async def _get_certs(force: bool = False) -> dict:
    global _certs, _certs_expire_at
    async with _certs_lock:
        if force or _certs is None or time.monotonic() >= _certs_expire_at:
            _certs, ttl = await asyncio.to_thread(_download_certs)
            _certs_expire_at = time.monotonic() + ttl
        return _certs


def _decode(id_token: str, certs: dict) -> dict:
    # aud проверяем сами: клиентов несколько (веб и Android), а jose принимает только один.
    # at_hash не проверяем — к ID-токену для входа access-токен не прилагается
    return jwt.decode(
        id_token,
        certs,
        algorithms=["RS256"],
        options={"verify_aud": False, "verify_at_hash": False},
    )


async def verify_google_id_token(id_token: str) -> dict:
    """Claims проверенного токена: sub, email, email_verified, name, picture."""
    try:
        kid = jwt.get_unverified_header(id_token).get("kid")
        certs = await _get_certs()
        # Google меняет ключи — незнакомый kid значит, что кэш устарел
        if kid and not any(key.get("kid") == kid for key in certs.get("keys", [])):
            certs = await _get_certs(force=True)
        claims = _decode(id_token, certs)
    except JWTError as error:
        raise GoogleTokenError(str(error)) from error

    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise GoogleTokenError("Wrong issuer")
    if claims.get("aud") not in settings.GOOGLE_CLIENT_IDS:
        raise GoogleTokenError("Token issued for another client")
    if not claims.get("sub"):
        raise GoogleTokenError("No subject")
    return claims
