"""Helper uji roundtrip encode→decode bertahap untuk sheet Encode_Decode.

Bukan logic baru — hanya pembungkus try/except per tahap di atas
fungsi existing (crypto/prng/steganography), supaya laporan tahu
Tahap Gagal + pesan exception persisnya.

Kontrak hasil (dict):
    key_status: "Benar" | "Salah"
    fail_stage: "selesai" jika pulih penuh, atau salah satu dari:
        "cek kapasitas" | "enkripsi" | "embed (LSB)" |
        "ekstrak header" | "ekstrak payload" | "dekripsi (AES-GCM)" |
        "verifikasi pesan"
    success: bool (ditulis ke Excel sebagai TRUE/FALSE)
    error: pesan exception persis, atau "-" jika tidak ada
    recovered: "Yes" | "No"
"""

from __future__ import annotations

from PIL import Image

from src.crypto import decrypt_message, encrypt_message
from src.prng import derive_prng_seed, generate_positions
from src.steganography import (
    HEADER_SIZE,
    bits_to_bytes,
    calculate_capacity,
    embed_payload,
    extract_payload,
    normalize_image,
    parse_header,
)

import numpy as np


def _fail(key_status, stage, exc=None):
    return {
        "key_status": key_status,
        "fail_stage": stage,
        "success": False,
        "error": "-" if exc is None else f"{type(exc).__name__}: {exc}",
        "recovered": "No",
    }


def run_codec_case(
    cover: Image.Image,
    plaintext: bytes,
    enc_password: str,
    dec_password: str,
    key_status: str,
    stego=None,
):
    """Jalankan satu kasus encode→decode bertahap.

    Jika `stego` diberikan (kasus kunci Salah memakai ulang stego yang
    sudah ada), tahap cek kapasitas/enkripsi/embed dilewati — langsung
    ke ekstrak dengan seed dari dec_password.
    """
    if cover.mode not in {"RGB", "RGBA"}:
        cover = cover.convert("RGB")
    width, height = cover.size
    total_slots = width * height * 3

    if stego is None:
        # --- tahap 1: cek kapasitas (budget plaintext, Opsi A) ---
        try:
            if len(plaintext) > calculate_capacity(cover):
                raise ValueError("plaintext exceeds capacity")
        except Exception as exc:
            return _fail(key_status, "cek kapasitas", exc)

        # --- tahap 2: enkripsi ---
        try:
            blob = encrypt_message(plaintext, enc_password)
        except Exception as exc:
            return _fail(key_status, "enkripsi", exc)

        # --- tahap 3: embed (LSB) ---
        try:
            needed = (HEADER_SIZE + len(blob)) * 8
            seed = derive_prng_seed(enc_password)
            positions = generate_positions(total_slots, needed, seed)
            stego = embed_payload(cover, blob, positions)
        except Exception as exc:
            return _fail(key_status, "embed (LSB)", exc)
    else:
        if stego.mode not in {"RGB", "RGBA"}:
            stego = stego.convert("RGB")

    # --- tahap 4-5: ekstrak header + payload (seed dari dec_password) ---
    try:
        seed = derive_prng_seed(dec_password)
        header_bits_needed = HEADER_SIZE * 8
        if total_slots < header_bits_needed:
            raise ValueError("Gambar terlalu kecil untuk berisi payload.")
        header_positions = generate_positions(
            total_slots, header_bits_needed, seed
        )
        normalized = normalize_image(stego)
        flat = np.array(normalized)[:, :, :3].reshape(-1)
        header_bits = [int(flat[p]) & 1 for p in header_positions]
        payload_length = parse_header(bits_to_bytes(header_bits))
    except Exception as exc:
        return _fail(key_status, "ekstrak header", exc)

    try:
        needed = (HEADER_SIZE + payload_length) * 8
        if needed > total_slots:
            raise ValueError("Payload melebihi kapasitas gambar.")
        positions = generate_positions(total_slots, needed, seed)
        raw = extract_payload(stego, positions)
    except Exception as exc:
        return _fail(key_status, "ekstrak payload", exc)

    # --- tahap 6: dekripsi (AES-GCM) ---
    try:
        recovered = decrypt_message(raw, dec_password)
    except Exception as exc:
        return _fail(key_status, "dekripsi (AES-GCM)", exc)

    # --- tahap 7: verifikasi pesan ---
    if recovered != plaintext:
        return {
            "key_status": key_status,
            "fail_stage": "verifikasi pesan",
            "success": False,
            "error": "-",
            "recovered": "No",
        }

    return {
        "key_status": key_status,
        "fail_stage": "selesai",
        "success": True,
        "error": "-",
        "recovered": "Yes",
    }
