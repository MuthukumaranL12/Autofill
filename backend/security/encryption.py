from __future__ import annotations

import os
from dataclasses import dataclass

from bson import Binary, ObjectId
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.database.mongodb import get_database
from backend.settings import get_settings


@dataclass(frozen=True)
class ActiveDek:
    id: ObjectId
    metadata: dict


def get_active_dek() -> ActiveDek:
    record = get_database().encryption_keys.find_one({"status": "active"})
    if record is None:
        raise RuntimeError("No active data-encryption key is configured")
    return ActiveDek(id=record["_id"], metadata=record)


def _aes_key() -> bytes:
    value = get_settings().local_aes_secret_key
    try:
        key = bytes.fromhex(value)
    except ValueError as exc:
        raise RuntimeError("LOCAL_AES_SECRET_KEY must be hexadecimal") from exc
    if len(key) != 32:
        raise RuntimeError("LOCAL_AES_SECRET_KEY must represent 32 bytes")
    return key


def encrypt_text(value: str) -> Binary:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_aes_key()).encrypt(nonce, value.encode("utf-8"), None)
    return Binary(nonce + ciphertext)