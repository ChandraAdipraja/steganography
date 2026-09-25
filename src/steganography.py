from __future__ import annotations

import struct
from typing import Sequence

import numpy as np
from PIL import Image


SUPPORTED_FORMATS = {"PNG", "BMP"}

MAGIC = b"STG1"
HEADER_FORMAT = ">4sI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Full overhead per AGENTS.md §12: stego header + crypto blob (salt+nonce+tag)
# Import dari src.crypto — jangan hardcode 44, source of truth adalah CRYPTO_OVERHEAD_BYTES
from src.crypto import CRYPTO_OVERHEAD_BYTES  # noqa: E402

FULL_OVERHEAD = HEADER_SIZE + CRYPTO_OVERHEAD_BYTES

BITS_PER_CHANNEL = 1


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


def calculate_capacity(image: Image.Image) -> int:
    """
    Kapasitas maksimum plaintext (byte) yang boleh diketik user.

    Opsi A (AGENTS.md §12): budget plaintext = total slot / 8 - FULL_OVERHEAD,
    dengan FULL_OVERHEAD = HEADER_SIZE (8, format STG1) + CRYPTO_OVERHEAD_BYTES (44, salt+nonce+tag).
    Bukan budget blob — cek di app.py harus dilakukan pada panjang plaintext,
    atau setelah enkripsi bandingkan blob vs (capacity + CRYPTO_OVERHEAD_BYTES).
    """
    image = normalize_image(image)
    channels = get_used_channels(image)

    width, height = image.size

    capacity_bits = (
        width
        * height
        * channels
        * BITS_PER_CHANNEL
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


def embed_payload(
    image: Image.Image,
    payload: bytes,
    positions: Sequence[int],
) -> Image.Image:
    image = normalize_image(image)
    validate_image(image)

    prepared_payload = prepare_payload(payload)
    payload_bits = bytes_to_bits(prepared_payload)

    if len(payload_bits) > len(positions):
        raise CapacityError(
            "Payload exceeds the provided embedding capacity."
        )

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

    for bit, position in zip(payload_bits, positions):
        if position < 0 or position >= len(flat_rgb):
            raise InvalidPayloadError(
                f"Invalid embedding position: {position}"
            )

        flat_rgb[position] = (
            flat_rgb[position] & 0b11111110
        ) | bit

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
) -> bytes:
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

    required_header_bits = HEADER_SIZE * 8

    if len(positions) < required_header_bits:
        raise CapacityError(
            "Not enough positions to extract the header."
        )

    header_bits = []

    for position in positions[:required_header_bits]:
        if position < 0 or position >= len(flat_rgb):
            raise InvalidPayloadError(
                f"Invalid extraction position: {position}"
            )

        header_bits.append(
            int(flat_rgb[position]) & 1
        )

    header = bits_to_bytes(header_bits)

    payload_length = parse_header(header)

    required_payload_bits = payload_length * 8

    total_required_bits = (
        required_header_bits
        + required_payload_bits
    )

    if len(positions) < total_required_bits:
        raise CapacityError(
            "Image does not contain enough data for the declared payload."
        )

    payload_bits = []

    for position in positions[
        required_header_bits:total_required_bits
    ]:
        if position < 0 or position >= len(flat_rgb):
            raise InvalidPayloadError(
                f"Invalid extraction position: {position}"
            )

        payload_bits.append(
            int(flat_rgb[position]) & 1
        )

    return bits_to_bytes(payload_bits)