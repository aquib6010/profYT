"""Token encryption helpers — Fernet (AES-128-CBC + HMAC-SHA256).

OAuth access/refresh tokens are encrypted before being written to the database.
Plaintext tokens never touch Postgres. The key lives in the .env file
(`TOKEN_ENCRYPTION_KEY`), separate from the database, giving us defense-in-depth:
a database leak alone is insufficient to impersonate users against YouTube.

Public API:
    encrypt_token(plaintext: str) -> bytes
    decrypt_token(ciphertext: bytes) -> str
    generate_key() -> str   # for one-time setup

The Fernet instance is cached so we don't re-derive the key on every call.
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class TokenEncryptionError(RuntimeError):
    """Raised when encryption/decryption fails (bad key, tampered ciphertext)."""


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = get_settings().token_encryption_key
    if not key:
        raise TokenEncryptionError(
            "TOKEN_ENCRYPTION_KEY is empty. Generate one with "
            "`python -m app.scripts.gen_key` and put it in backend/.env."
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as e:
        raise TokenEncryptionError(f"TOKEN_ENCRYPTION_KEY is not a valid Fernet key: {e}") from e


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a plaintext OAuth token. Output is base64-encoded ciphertext bytes."""
    if not isinstance(plaintext, str) or not plaintext:
        raise ValueError("encrypt_token expects a non-empty string")
    return _fernet().encrypt(plaintext.encode("utf-8"))


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt ciphertext back to the original token string.

    Raises TokenEncryptionError if the ciphertext was tampered with or the
    current key cannot decrypt it.
    """
    if not isinstance(ciphertext, bytes | bytearray | memoryview) or not ciphertext:
        raise ValueError("decrypt_token expects non-empty bytes")
    try:
        return _fernet().decrypt(bytes(ciphertext)).decode("utf-8")
    except InvalidToken as e:
        raise TokenEncryptionError(
            "Failed to decrypt token — key mismatch or tampered ciphertext"
        ) from e


def generate_key() -> str:
    """Generate a fresh Fernet key. For one-time setup."""
    return Fernet.generate_key().decode("utf-8")
