from __future__ import annotations

import struct
from typing import Sequence

import numpy as np
from PIL import Image


# ============================================================
# Constants
# ============================================================

SUPPORTED_FORMATS = {"PNG", "BMP"}

MAGIC = b"STG1"
HEADER_FORMAT = ">4sI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

BITS_PER_CHANNEL = 1


# ============================================================
# Custom Exceptions
# ============================================================

class SteganographyError(Exception):
    """Base exception for steganography-related errors."""


class InvalidImageError(SteganographyError):
    """Raised when the image format or mode is unsupported."""


class InvalidPayloadError(SteganographyError):
    """Raised when the payload or header is invalid."""


class CapacityError(SteganographyError):
    """Raised when the payload exceeds image capacity."""


# ============================================================
# Image Utilities
# ============================================================

def validate_image(image: Image.Image) -> None:
    """
    Validate that the image is a supported PNG or BMP image.

    The image must have RGB or RGBA mode.
    """
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
    """
    Normalize an image into RGB or RGBA.

    RGB remains RGB.
    RGBA remains RGBA.
    Other modes are converted to RGB.
    """
    if image.mode in {"RGB", "RGBA"}:
        return image.copy()

    return image.convert("RGB")


def get_used_channels(image: Image.Image) -> int:
    """
    Return the number of channels used for LSB embedding.

    RGB  -> 3
    RGBA -> 3

    The alpha channel is intentionally not modified.
    """
    if image.mode == "RGB":
        return 3

    if image.mode == "RGBA":
        return 3

    raise InvalidImageError(
        f"Unsupported image mode: {image.mode}"
    )


# ============================================================
# Capacity
# ============================================================

def calculate_capacity(image: Image.Image) -> int:
    """
    Calculate the maximum payload capacity in bytes.

    One LSB is used from each RGB channel.

    The returned capacity represents the maximum size of the
    payload itself, excluding the header.
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

    return max(0, capacity_bytes - HEADER_SIZE)


# ============================================================
# Byte / Bit Conversion
# ============================================================

def bytes_to_bits(data: bytes) -> list[int]:
    """
    Convert bytes into a list of bits.

    Example:
        b"A" -> [0, 1, 0, 0, 0, 0, 0, 1]
    """
    bits: list[int] = []

    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)

    return bits


def bits_to_bytes(bits: Sequence[int]) -> bytes:
    """
    Convert a sequence of bits into bytes.

    The number of bits must be a multiple of 8.
    """
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


# ============================================================
# Header
# ============================================================

def create_header(payload_length: int) -> bytes:
    """
    Create the payload header.

    Format:
        MAGIC (4 bytes)
        LENGTH (4 bytes, unsigned integer)
    """
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
    """
    Parse a header and return the payload length.
    """
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


# ============================================================
# Payload Preparation
# ============================================================

def prepare_payload(payload: bytes) -> bytes:
    """
    Add the steganography header to the payload.
    """
    if not isinstance(payload, bytes):
        raise InvalidPayloadError(
            "Payload must be bytes."
        )

    header = create_header(len(payload))

    return header + payload

# ============================================================
# LSB Embedding
# ============================================================

def embed_payload(
    image: Image.Image,
    payload: bytes,
    positions: Sequence[int],
) -> Image.Image:
    """
    Embed a payload into the image using the Least Significant Bit
    of RGB channels.

    Parameters
    ----------
    image:
        Cover image in RGB or RGBA format.

    payload:
        Payload bytes. The payload will automatically receive
        the steganography header.

    positions:
        Flattened channel indices where bits will be embedded.

    Returns
    -------
    Image.Image
        New image containing the embedded payload.

    Notes
    -----
    RGB channels are used.
    Alpha channel is never modified.
    """

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

    # RGBA
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

# ============================================================
# LSB Extraction
# ============================================================

def extract_payload(
    image: Image.Image,
    positions: Sequence[int],
) -> bytes:
    """
    Extract a payload from an image using the Least Significant Bit
    of RGB channels.

    The function first extracts the fixed-size header, reads the
    payload length, and then extracts exactly the required number
    of payload bytes.
    """

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