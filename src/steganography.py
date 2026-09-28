from __future__ import annotations

import struct
from typing import Sequence

import numpy as np
from PIL import Image


SUPPORTED_FORMATS = {"PNG", "BMP"}

MAGIC = b"STG1"
HEADER_FORMAT = ">4sI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

from src.crypto import CRYPTO_OVERHEAD_BYTES  # noqa: E402

FULL_OVERHEAD = HEADER_SIZE + CRYPTO_OVERHEAD_BYTES

BITS_PER_CHANNEL = 1
MIN_BITS_PER_CHANNEL = 1
MAX_BITS_PER_CHANNEL = 8  # batas fisik channel 8-bit (UI produk membatasi 1..3)


def _check_bits_per_channel(bits_per_channel: int) -> int:
    if (
        isinstance(bits_per_channel, bool)
        or not isinstance(bits_per_channel, int)
    ):
        raise ValueError("bits_per_channel must be an int")
    if not MIN_BITS_PER_CHANNEL <= bits_per_channel <= MAX_BITS_PER_CHANNEL:
        raise ValueError(
            f"bits_per_channel must be between {MIN_BITS_PER_CHANNEL} "
            f"and {MAX_BITS_PER_CHANNEL}"
        )
    return bits_per_channel


class SteganographyError(Exception):
    pass


class InvalidImageError(SteganographyError):
    pass


class InvalidPayloadError(SteganographyError):
    pass


class CapacityError(SteganographyError):
    pass


def validate_image(image: Image.Image) -> None:
    if image.format is not None:
        image_format = image.format.upper()

        if image_format not in SUPPORTED_FORMATS:
            raise InvalidImageError(
                f"Unsupported image format: {image_format}. "
                f"Only PNG and BMP are supported."
            )

    if image.mode not in {"RGB", "RGBA"}:
        raise InvalidImageError(
            f"Unsupported image mode: {image.mode}. "
            f"Only RGB and RGBA are supported."
        )


def normalize_image(image: Image.Image) -> Image.Image:
    if image.mode in {"RGB", "RGBA"}:
        return image.copy()

    return image.convert("RGB")


def get_used_channels(image: Image.Image) -> int:
    if image.mode == "RGB":
        return 3

    if image.mode == "RGBA":
        return 3

    raise InvalidImageError(
        f"Unsupported image mode: {image.mode}"
    )


def calculate_capacity(
    image: Image.Image,
    bits_per_channel: int = BITS_PER_CHANNEL,
) -> int:
    m = _check_bits_per_channel(bits_per_channel)
    image = normalize_image(image)
    channels = get_used_channels(image)

    width, height = image.size

    capacity_bits = (
        width
        * height
        * channels
        * m
    )

    capacity_bytes = capacity_bits // 8

    return max(0, capacity_bytes - FULL_OVERHEAD)


def bytes_to_bits(data: bytes) -> list[int]:
    bits: list[int] = []

    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)

    return bits


def bits_to_bytes(bits: Sequence[int]) -> bytes:
    if len(bits) % 8 != 0:
        raise InvalidPayloadError(
            "Bit sequence length must be a multiple of 8."
        )

    result = bytearray()

    for index in range(0, len(bits), 8):
        byte = 0

        for bit in bits[index:index + 8]:
            if bit not in {0, 1}:
                raise InvalidPayloadError(
                    f"Invalid bit value: {bit}"
                )

            byte = (byte << 1) | bit

        result.append(byte)

    return bytes(result)


def create_header(payload_length: int) -> bytes:
    if payload_length < 0:
        raise InvalidPayloadError(
            "Payload length cannot be negative."
        )

    if payload_length > 0xFFFFFFFF:
        raise InvalidPayloadError(
            "Payload is too large for the header format."
        )

    return struct.pack(
        HEADER_FORMAT,
        MAGIC,
        payload_length,
    )


def parse_header(header: bytes) -> int:
    if len(header) != HEADER_SIZE:
        raise InvalidPayloadError(
            f"Header must be exactly {HEADER_SIZE} bytes."
        )

    magic, payload_length = struct.unpack(
        HEADER_FORMAT,
        header,
    )

    if magic != MAGIC:
        raise InvalidPayloadError(
            "Invalid steganography header."
        )

    return payload_length


def prepare_payload(payload: bytes) -> bytes:
    if not isinstance(payload, bytes):
        raise InvalidPayloadError(
            "Payload must be bytes."
        )

    header = create_header(len(payload))

    return header + payload


def _bits_to_chunks(bits: list[int], m: int) -> list[int]:
    """Kelompokkan aliran bit menjadi chunk m-bit (MSB-first), padding nol."""
    padded = bits + [0] * ((-len(bits)) % m)
    chunks = []
    for index in range(0, len(padded), m):
        value = 0
        for bit in padded[index:index + m]:
            value = (value << 1) | bit
        chunks.append(value)
    return chunks


def _chunks_to_bits(chunks: Sequence[int], m: int) -> list[int]:
    """Uraikan chunk m-bit kembali menjadi aliran bit (MSB-first)."""
    bits: list[int] = []
    for value in chunks:
        for shift in range(m - 1, -1, -1):
            bits.append((value >> shift) & 1)
    return bits


def embed_payload(
    image: Image.Image,
    payload: bytes,
    positions: Sequence[int],
    bits_per_channel: int = BITS_PER_CHANNEL,
) -> Image.Image:
    m = _check_bits_per_channel(bits_per_channel)
    image = normalize_image(image)
    validate_image(image)

    prepared_payload = prepare_payload(payload)
    chunks = _bits_to_chunks(bytes_to_bits(prepared_payload), m)

    if len(chunks) > len(positions):
        raise CapacityError(
            "Payload exceeds the provided embedding capacity."
        )

    keep_mask = 0xFF ^ ((1 << m) - 1)

    array = np.array(image)

    if image.mode == "RGB":
        pixel_array = array.reshape(-1, 3)

    elif image.mode == "RGBA":
        pixel_array = array[:, :, :3].reshape(-1, 3)

    else:
        raise InvalidImageError(
            f"Unsupported image mode: {image.mode}"
        )

    flat_rgb = pixel_array.reshape(-1)

    for chunk, position in zip(chunks, positions):
        if position < 0 or position >= len(flat_rgb):
            raise InvalidPayloadError(
                f"Invalid embedding position: {position}"
            )

        flat_rgb[position] = (
            int(flat_rgb[position]) & keep_mask
        ) | chunk

    if image.mode == "RGB":
        result_array = flat_rgb.reshape(array.shape)

        return Image.fromarray(
            result_array.astype(np.uint8),
            mode="RGB",
        )

    result_array = array.copy()

    rgb_result = flat_rgb.reshape(
        array.shape[0],
        array.shape[1],
        3,
    )

    result_array[:, :, :3] = rgb_result

    return Image.fromarray(
        result_array.astype(np.uint8),
        mode="RGBA",
    )


def extract_payload(
    image: Image.Image,
    positions: Sequence[int],
    bits_per_channel: int = BITS_PER_CHANNEL,
) -> bytes:
    m = _check_bits_per_channel(bits_per_channel)
    image = normalize_image(image)
    validate_image(image)

    array = np.array(image)

    if image.mode == "RGB":
        pixel_array = array.reshape(-1, 3)

    elif image.mode == "RGBA":
        pixel_array = array[:, :, :3].reshape(-1, 3)

    else:
        raise InvalidImageError(
            f"Unsupported image mode: {image.mode}"
        )

    flat_rgb = pixel_array.reshape(-1)
    channel_mask = (1 << m) - 1

    def _read_chunks(count: int, offset: int = 0) -> list[int]:
        chunks = []
        for position in positions[offset:offset + count]:
            if position < 0 or position >= len(flat_rgb):
                raise InvalidPayloadError(
                    f"Invalid extraction position: {position}"
                )
            chunks.append(int(flat_rgb[position]) & channel_mask)
        return chunks

    required_header_bits = HEADER_SIZE * 8
    header_chunks_needed = -(-required_header_bits // m)

    if len(positions) < header_chunks_needed:
        raise CapacityError(
            "Not enough positions to extract the header."
        )

    header_bits = _chunks_to_bits(
        _read_chunks(header_chunks_needed), m
    )[:required_header_bits]

    header = bits_to_bytes(header_bits)

    payload_length = parse_header(header)

    required_payload_bits = payload_length * 8

    total_required_bits = (
        required_header_bits
        + required_payload_bits
    )
    total_chunks_needed = -(-total_required_bits // m)

    if len(positions) < total_chunks_needed:
        raise CapacityError(
            "Image does not contain enough data for the declared payload."
        )

    payload_bits = _chunks_to_bits(
        _read_chunks(total_chunks_needed), m
    )[required_header_bits:total_required_bits]

    return bits_to_bytes(payload_bits)