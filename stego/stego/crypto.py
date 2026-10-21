"""Optional password-based encryption layer for steganography payloads.

A key is derived from the password with PBKDF2-HMAC-SHA256 over a random
salt, and the data is sealed with Fernet (AES-128-CBC + HMAC authentication).
The random salt is prepended to the Fernet token so decryption can rederive
the key:

    [ 16-byte salt ][ Fernet token ]
"""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT_SIZE = 16
_PBKDF2_ITERATIONS = 390_000


class DecryptionError(Exception):
    """Raised when a payload cannot be decrypted (e.g. wrong password)."""


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a url-safe base64 Fernet key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    raw_key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt ``data`` with a key derived from ``password``.

    Returns the salt prepended to the Fernet token.
    """
    salt = os.urandom(_SALT_SIZE)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(data)
    return salt + token


def decrypt(token: bytes, password: str) -> bytes:
    """Decrypt a payload produced by :func:`encrypt`.

    Raises:
        DecryptionError: if the password is wrong or the data is corrupt.
    """
    if len(token) <= _SALT_SIZE:
        raise DecryptionError("ciphertext is too short to contain a salt")
    salt, body = token[:_SALT_SIZE], token[_SALT_SIZE:]
    key = _derive_key(password, salt)
    try:
        return Fernet(key).decrypt(body)
    except InvalidToken as exc:
        raise DecryptionError("wrong password or corrupt data") from exc
