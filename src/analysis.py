from __future__ import annotations

import math
import os
import tempfile
from collections.abc import Callable
from typing import Any

import numpy as np
from matplotlib.figure import Figure
from PIL import Image

SUPPORTED_MODES = ("RGB", "RGBA")
MAX_PIXEL_VALUE = 255
HISTOGRAM_CHANNELS = ("R", "G", "B")


class AnalysisError(Exception):
    pass


def _to_rgb_array(image: Image.Image) -> np.ndarray:
    if not isinstance(image, Image.Image):
        raise AnalysisError("cover and stego must be Pillow Image objects")
    if image.mode not in SUPPORTED_MODES:
        raise AnalysisError(
            f"Unsupported image mode: {image.mode}. Only RGB and RGBA "
            "are supported."
        )
    array = np.array(image)
    if image.mode == "RGBA":
        array = array[:, :, :3]
    return array


def calculate_mse(cover: Image.Image, stego: Image.Image) -> float:
    cover_arr = _to_rgb_array(cover)
    stego_arr = _to_rgb_array(stego)
    if cover_arr.shape != stego_arr.shape:
        raise AnalysisError(
            f"Image shapes differ: {cover_arr.shape} vs {stego_arr.shape}"
        )
    diff = cover_arr.astype(np.float64) - stego_arr.astype(np.float64)
    return float(np.mean(diff**2))


def calculate_psnr(cover: Image.Image, stego: Image.Image) -> float:
    mse = calculate_mse(cover, stego)
    if mse == 0:
        return float("inf")
    return float(10.0 * math.log10((MAX_PIXEL_VALUE**2) / mse))


def extract_lsb_plane(image: Image.Image) -> np.ndarray:
    rgb = _to_rgb_array(image)
    return ((rgb & 1) * 255).astype(np.uint8)


def generate_histogram(
    cover: Image.Image,
    stego: Image.Image,
) -> dict[str, dict[str, list[int]]]:
    cover_arr = _to_rgb_array(cover)
    stego_arr = _to_rgb_array(stego)
    if cover_arr.shape != stego_arr.shape:
        raise AnalysisError(
            f"Image shapes differ: {cover_arr.shape} vs {stego_arr.shape}"
        )
    bins = list(range(MAX_PIXEL_VALUE + 2))
    result: dict[str, dict[str, list[int]]] = {}
    for index, channel in enumerate(HISTOGRAM_CHANNELS):
        cover_counts = np.bincount(
            cover_arr[:, :, index].ravel(), minlength=256
        )[:256]
        stego_counts = np.bincount(
            stego_arr[:, :, index].ravel(), minlength=256
        )[:256]
        result[channel] = {
            "cover": [int(v) for v in cover_counts],
            "stego": [int(v) for v in stego_counts],
            "bins": bins,
        }
    return result


def plot_histogram(
    cover: Image.Image,
    stego: Image.Image,
) -> Figure:
    data = generate_histogram(cover, stego)
    fig = Figure(figsize=(12, 4))
    axes = fig.subplots(1, 3)
    for ax, channel in zip(axes, HISTOGRAM_CHANNELS):
        channel_data = data[channel]
        x = channel_data["bins"][:-1]
        ax.plot(x, channel_data["cover"], label="cover")
        ax.plot(x, channel_data["stego"], label="stego")
        ax.set_title(f"Channel {channel}")
        ax.set_xlabel("Pixel value")
        ax.set_ylabel("Count")
        ax.legend()
    fig.suptitle("Cover vs Stego Histogram")
    fig.tight_layout()
    return fig


def test_jpeg_robustness(
    stego_image_path: str,
    extract_fn: Callable[[str], Any],
    quality: int = 90,
) -> dict[str, Any]:
    if not callable(extract_fn):
        raise TypeError("extract_fn must be callable")
    if (
        isinstance(quality, bool)
        or not isinstance(quality, int)
        or not 1 <= quality <= 100
    ):
        raise ValueError("quality must be an int in range 1-100")

    if not isinstance(stego_image_path, (str, os.PathLike)):
        return {"success": False, "error": "invalid stego_image_path", "jpeg_path": ""}
    if not os.path.isfile(stego_image_path):
        return {
            "success": False,
            "error": f"file not found: {stego_image_path}",
            "jpeg_path": "",
        }

    jpeg_path = ""
    try:
        with Image.open(stego_image_path) as img:
            rgb = img.convert("RGB")
            with tempfile.NamedTemporaryFile(
                suffix=".jpg", delete=False
            ) as tmp:
                jpeg_path = tmp.name
            rgb.save(jpeg_path, format="JPEG", quality=quality)
    except Exception as exc:
        return {
            "success": False,
            "error": f"failed to create JPEG: {exc}",
            "jpeg_path": jpeg_path,
        }

    try:
        extract_fn(jpeg_path)
    except Exception as exc:
        return {
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "jpeg_path": jpeg_path,
        }
    return {"success": True, "error": None, "jpeg_path": jpeg_path}


test_jpeg_robustness.__test__ = False
