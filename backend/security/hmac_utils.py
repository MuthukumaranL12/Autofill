from __future__ import annotations

import hashlib
import hmac

from backend.settings import get_settings


def tokenise(value: str) -> str:
    secret = get_settings().hmac_salt_secret
    if not secret:
        raise RuntimeError("HMAC_SALT_SECRET is required")
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()