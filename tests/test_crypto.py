import pytest

from src.crypto import (
    CRYPTO_OVERHEAD_BYTES,
    NONCE_SIZE,
    SALT_SIZE,
    decrypt_message,
    encrypt_message,
    generate_nonce,
)
from src.key import derive_key, generate_salt


def test_encrypt_decrypt_roundtrip():
    plaintext = "Halo, ini pesan rahasia! 🔐".encode("utf-8")
    blob = encrypt_message(plaintext, "kunci-rahasia-123")
    assert isinstance(blob, bytes)
    assert len(blob) == len(plaintext) + CRYPTO_OVERHEAD_BYTES
    assert decrypt_message(blob, "kunci-rahasia-123") == plaintext


def test_decrypt_with_wrong_key_raises():
    blob = encrypt_message(b"pesan penting", "key-yang-benar")
    with pytest.raises(ValueError):
        decrypt_message(blob, "key-yang-salah")


def test_tampered_ciphertext_raises():
    blob = encrypt_message(b"pesan penting", "key-bersama")
    tampered = bytearray(blob)
    tampered[-1] ^= 0x01
    with pytest.raises(ValueError):
        decrypt_message(bytes(tampered), "key-bersama")


def test_generate_nonce_unique():
    assert generate_nonce() != generate_nonce()


def test_generate_salt_unique():
    assert generate_salt() != generate_salt()


def test_encrypt_same_input_gives_different_blob():
    plaintext = b"pesan yang sama"
    blob1 = encrypt_message(plaintext, "key-sama")
    blob2 = encrypt_message(plaintext, "key-sama")
    assert blob1 != blob2
    assert decrypt_message(blob1, "key-sama") == plaintext
    assert decrypt_message(blob2, "key-sama") == plaintext


def test_derive_key_empty_key_raises():
    with pytest.raises(ValueError):
        derive_key("", b"0" * 16)


def test_tampered_salt_raises():
    blob = encrypt_message(b"pesan penting", "key-bersama")
    tampered = bytearray(blob)
    tampered[0] ^= 0x01  
    with pytest.raises(ValueError):
        decrypt_message(bytes(tampered), "key-bersama")


def test_tampered_nonce_raises():
    blob = encrypt_message(b"pesan penting", "key-bersama")
    tampered = bytearray(blob)
    tampered[SALT_SIZE + 4] ^= 0x01  
    assert SALT_SIZE + 4 < SALT_SIZE + NONCE_SIZE
    with pytest.raises(ValueError):
        decrypt_message(bytes(tampered), "key-bersama")


def test_encrypt_empty_plaintext():
    blob = encrypt_message(b"", "kunci")
    assert len(blob) == CRYPTO_OVERHEAD_BYTES
    assert decrypt_message(blob, "kunci") == b""
