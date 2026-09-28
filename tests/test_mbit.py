import math

import pytest
from PIL import Image

from src.steganography import (
    HEADER_SIZE,
    CapacityError,
    calculate_capacity,
    embed_payload,
    extract_payload,
)


def _cover(size=(64, 64)):
    return Image.new("RGB", size, color=(120, 150, 200))


def _positions(total, payload_len, m):
    need = -(-(HEADER_SIZE + payload_len) * 8 // m)
    assert need <= total
    return list(range(need))


@pytest.mark.parametrize("m", [1, 2, 3])
def test_roundtrip_per_m(m):
    img = _cover()
    msg = b"pesan varian m-bit 12345"
    total = 64 * 64 * 3
    assert len(msg) <= calculate_capacity(img, m)
    pos = _positions(total, len(msg), m)
    stego = embed_payload(img, msg, pos, m)
    assert extract_payload(stego, pos, m) == msg


@pytest.mark.parametrize("m", [1, 2, 3])
def test_capacity_scales_with_m(m):
    img = Image.new("RGB", (100, 100))
    expected = (100 * 100 * 3 * m) // 8 - HEADER_SIZE - 44
    assert calculate_capacity(img, m) == max(0, expected)


def test_default_is_one_bit_backward_compat():
    img = _cover()
    msg = b"legacy"
    total = 64 * 64 * 3
    pos = _positions(total, len(msg), 1)
    stego = embed_payload(img, msg, pos)  # tanpa argumen m
    assert extract_payload(stego, pos) == msg  # tanpa argumen m


def test_cross_m_extract_fails():
    img = _cover()
    msg = b"cross check"
    total = 64 * 64 * 3
    pos = _positions(total, len(msg), 2)
    stego = embed_payload(img, msg, pos, 2)
    from src.steganography import InvalidPayloadError
    with pytest.raises((InvalidPayloadError, CapacityError)):
        extract_payload(stego, pos, 1)


def test_invalid_m_rejected():
    img = _cover()
    with pytest.raises(ValueError):
        calculate_capacity(img, 0)
    with pytest.raises(ValueError):
        embed_payload(img, b"x", [0], 9)
    with pytest.raises(ValueError):
        extract_payload(img, [0], -1)


def test_auto_detect_order():
    # simulasi logika decode: m yang benar lolos header, yang salah gagal
    from src.steganography import (
        bits_to_bytes,
        normalize_image,
        parse_header,
    )
    import numpy as np

    img = _cover()
    msg = b"detect me"
    total = 64 * 64 * 3
    pos = _positions(total, len(msg), 3)
    stego = embed_payload(img, msg, pos, 3)
    flat = np.array(normalize_image(stego))[:, :, :3].reshape(-1)

    found = None
    for m in (1, 2, 3):
        mask = (1 << m) - 1
        need_chunks = -(-HEADER_SIZE * 8 // m)
        bits = []
        for p in pos[:need_chunks]:
            bits.extend(
                (int(flat[p]) & mask) >> s & 1 for s in range(m - 1, -1, -1)
            )
        try:
            parse_header(bits_to_bytes(bits[: HEADER_SIZE * 8]))
            found = m
            break
        except Exception:
            continue
    assert found == 3


def test_padding_edge_m3():
    # panjang bit tidak habis dibagi 3 → padding nol harus terbuang pas
    img = _cover()
    msg = b"AB"  # (8 + 2) * 8 = 80 bit, 80 % 3 != 0
    total = 64 * 64 * 3
    pos = _positions(total, len(msg), 3)
    stego = embed_payload(img, msg, pos, 3)
    assert extract_payload(stego, pos, 3) == msg
