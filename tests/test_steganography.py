from PIL import Image
import pytest

from src.steganography import (
    HEADER_SIZE,
    MAGIC,
    CapacityError,
    InvalidPayloadError,
    bytes_to_bits,
    bits_to_bytes,
    calculate_capacity,
    create_header,
    parse_header,
    prepare_payload,
)


def test_bytes_to_bits_and_back():
    original = b"Hello Steganography!"

    bits = bytes_to_bits(original)
    result = bits_to_bytes(bits)

    assert result == original


def test_empty_bytes_conversion():
    original = b""

    bits = bytes_to_bits(original)
    result = bits_to_bytes(bits)

    assert result == original


def test_invalid_bit_length():
    with pytest.raises(InvalidPayloadError):
        bits_to_bytes([1, 0, 1])


def test_invalid_bit_value():
    with pytest.raises(InvalidPayloadError):
        bits_to_bytes([0, 1, 2, 0, 0, 0, 0, 1])


def test_header_creation_and_parsing():
    payload_length = 1234

    header = create_header(payload_length)

    assert len(header) == HEADER_SIZE
    assert parse_header(header) == payload_length


def test_invalid_header_magic():
    invalid_header = b"XXXX" + (100).to_bytes(4, "big")

    with pytest.raises(InvalidPayloadError):
        parse_header(invalid_header)


def test_prepare_payload():
    payload = b"Hello"

    prepared = prepare_payload(payload)

    assert len(prepared) == HEADER_SIZE + len(payload)
    assert prepared[HEADER_SIZE:] == payload
    assert parse_header(prepared[:HEADER_SIZE]) == len(payload)


def test_rgb_capacity():
    image = Image.new("RGB", (100, 100))

    capacity = calculate_capacity(image)

    expected = (100 * 100 * 3) // 8 - HEADER_SIZE

    assert capacity == expected


def test_rgba_capacity():
    image = Image.new("RGBA", (100, 100))

    capacity = calculate_capacity(image)

    expected = (100 * 100 * 3) // 8 - HEADER_SIZE

    assert capacity == expected