import secrets

from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2

DEFAULT_SALT_LENGTH = 16
DEFAULT_ITERATIONS = 200_000
DEFAULT_KEY_LEN = 32


def generate_salt(length: int = 16) -> bytes:
    if length <= 0:
        raise ValueError("salt length must be a positive integer")
    return secrets.token_bytes(length)


def derive_key(
    stego_key: str,
    salt: bytes,
    iterations: int = 200_000,
    key_len: int = 32,
) -> bytes:
    if not isinstance(stego_key, str) or not stego_key.strip():
        raise ValueError("stego_key must be a non-empty string")
    if not isinstance(salt, bytes) or len(salt) == 0:
        raise ValueError("salt must be non-empty bytes")
    if iterations <= 0:
        raise ValueError("iterations must be a positive integer")
    if key_len <= 0:
        raise ValueError("key_len must be a positive integer")

    return PBKDF2(
        stego_key.encode("utf-8"),
        salt,
        dkLen=key_len,
        count=iterations,
        hmac_hash_module=SHA256,
    )
