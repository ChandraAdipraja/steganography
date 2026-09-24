import secrets

from Crypto.Cipher import AES

from .key import derive_key, generate_salt

SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
CRYPTO_OVERHEAD_BYTES = SALT_SIZE + NONCE_SIZE + TAG_SIZE

PBKDF2_ITERATIONS = 200_000
AES_KEY_LEN = 32

_AES_LABEL = "|AES"


def generate_nonce() -> bytes:
    return secrets.token_bytes(NONCE_SIZE)


def encrypt_message(plaintext: bytes, key: str) -> bytes:
    if not isinstance(plaintext, bytes):
        raise TypeError("plaintext must be bytes")
    if not isinstance(key, str) or not key.strip():
        raise ValueError("key must be a non-empty string")

    salt = generate_salt(SALT_SIZE)
    aes_key = derive_key(
        key + _AES_LABEL,
        salt,
        iterations=PBKDF2_ITERATIONS,
        key_len=AES_KEY_LEN,
    )
    nonce = generate_nonce()
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return salt + nonce + tag + ciphertext


def decrypt_message(payload: bytes, key: str) -> bytes:
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    if not isinstance(key, str) or not key.strip():
        raise ValueError("key must be a non-empty string")
    if len(payload) < CRYPTO_OVERHEAD_BYTES:
        raise ValueError(
            f"payload too short: got {len(payload)} bytes, "
            f"need at least {CRYPTO_OVERHEAD_BYTES} (salt+nonce+tag)"
        )

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    tag = payload[SALT_SIZE + NONCE_SIZE : CRYPTO_OVERHEAD_BYTES]
    ciphertext = payload[CRYPTO_OVERHEAD_BYTES:]

    aes_key = derive_key(
        key + _AES_LABEL,
        salt,
        iterations=PBKDF2_ITERATIONS,
        key_len=AES_KEY_LEN,
    )
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    try:
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as exc:
        raise ValueError(
            "Decryption failed: wrong key or tampered data"
        ) from exc
