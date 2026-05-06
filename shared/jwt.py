import os
import uuid
import json
import time
import hashlib
import base64
import hmac
import hashlib as hl
from typing import Optional


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _sign(payload: dict, secret: str) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    body   = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig    = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), f"{header}.{body}".encode(), hl.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


def _verify(token: str, secret: str) -> Optional[dict]:
    try:
        token = token.strip()
        h, b, s = token.split(".")
        expected = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{h}.{b}".encode(), hl.sha256).digest()
        ).rstrip(b"=").decode()
        if s != expected:
            return None
        pad  = 4 - len(b) % 4
        data = json.loads(base64.urlsafe_b64decode(b + "=" * pad))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None


def _make_tokens(user: dict, secret: str, refresh_secret: str) -> dict:
    now = int(time.time())
    access_payload = {
        "sub":   str(user["id"]),
        "email": user["email"],
        "name":  user["name"],
        "role":  str(user["role"]),
        "roles": [str(user["role"])],
        "exp":   now + 900,
        "jti":   str(uuid.uuid4()),
    }
    refresh_payload = {
        "sub": str(user["id"]),
        "exp": now + 60 * 60 * 24 * 7,
        "jti": str(uuid.uuid4()),
    }
    return {
        "access_token":  _sign(access_payload,  secret),
        "refresh_token": _sign(refresh_payload, refresh_secret),
        "token_type":    "bearer",
        "expires_in":    900,
    }
