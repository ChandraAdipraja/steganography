import matplotlib

matplotlib.use("Agg")

import base64
import io

import numpy as np
import pytest
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from PIL import Image

from src.analysis import (
    AnalysisError,
    calculate_mse,
    calculate_psnr,
    extract_lsb_plane,
    figure_to_base64,
    figure_to_png_bytes,
    generate_histogram,
    lsb_plane_to_image,
    plot_histogram,
    test_jpeg_robustness,
)


def make_solid(color, size=(8, 8), mode="RGB"):
    return Image.new(mode, size, color=color)


def make_random_rgb(width=32, height=32, seed=0):
    rng = np.random.default_rng(seed)
    arr = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def test_mse_identical_is_zero():
    img = make_solid((10, 20, 30))
    assert calculate_mse(img, img.copy()) == 0.0


def test_mse_known_difference():
    cover = Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8), mode="RGB")
    stego = Image.fromarray(np.ones((2, 2, 3), dtype=np.uint8), mode="RGB")
    assert calculate_mse(cover, stego) == pytest.approx(1.0)


def test_mse_shape_mismatch_raises():
    with pytest.raises(AnalysisError):
        calculate_mse(
            make_solid((0, 0, 0), size=(8, 8)),
            make_solid((0, 0, 0), size=(4, 4)),
        )


def test_mse_does_not_mutate_input():
    cover = make_random_rgb()
    stego = make_random_rgb(seed=1)
    before_cover = np.array(cover).copy()
    before_stego = np.array(stego).copy()
    calculate_mse(cover, stego)
    assert np.array_equal(np.array(cover), before_cover)
    assert np.array_equal(np.array(stego), before_stego)


def test_mse_unsupported_mode_raises():
    gray = Image.new("L", (8, 8))
    with pytest.raises(AnalysisError):
        calculate_mse(gray, gray)


def test_psnr_identical_is_inf():
    img = make_solid((1, 2, 3))
    assert calculate_psnr(img, img.copy()) == float("inf")


def test_psnr_small_vs_large_difference():
    cover = make_solid((128, 128, 128), size=(32, 32))
    cover_arr = np.array(cover).copy()
    small_arr = cover_arr.copy()
    small_arr[0, 0, 0] ^= 1
    small = Image.fromarray(small_arr, mode="RGB")
    large = make_solid((0, 0, 0), size=(32, 32))
    psnr_small = calculate_psnr(cover, small)
    psnr_large = calculate_psnr(cover, large)
    assert psnr_small > 30.0
    assert psnr_large < psnr_small


def test_psnr_shape_mismatch_raises():
    with pytest.raises(AnalysisError):
        calculate_psnr(
            make_solid((0, 0, 0), size=(8, 8)),
            make_solid((0, 0, 0), size=(4, 4)),
        )


def test_histogram_keys_and_totals():
    cover = make_random_rgb(16, 16, seed=0)
    stego = make_random_rgb(16, 16, seed=1)
    hist = generate_histogram(cover, stego)
    assert set(hist.keys()) == {"R", "G", "B"}
    for channel in ("R", "G", "B"):
        assert sum(hist[channel]["cover"]) == 16 * 16
        assert sum(hist[channel]["stego"]) == 16 * 16
        assert len(hist[channel]["bins"]) == 257


def test_histogram_solid_single_peak():
    cover = make_solid((10, 20, 30), size=(8, 8))
    stego = cover.copy()
    hist = generate_histogram(cover, stego)
    assert hist["R"]["cover"][10] == 64
    assert hist["G"]["cover"][20] == 64
    assert hist["B"]["cover"][30] == 64
    assert sum(hist["R"]["cover"]) == 64


def test_plot_histogram_returns_figure():
    cover = make_random_rgb(16, 16, seed=0)
    stego = make_random_rgb(16, 16, seed=1)
    fig = plot_histogram(cover, stego)
    try:
        assert isinstance(fig, Figure)
        assert len(fig.axes) == 3
    finally:
        plt.close(fig)


def test_plot_histogram_twice_no_state_leak():
    cover = make_random_rgb(8, 8, seed=0)
    stego = make_random_rgb(8, 8, seed=1)
    fig1 = plot_histogram(cover, stego)
    fig2 = plot_histogram(cover, stego)
    try:
        assert isinstance(fig1, Figure)
        assert isinstance(fig2, Figure)
        assert fig1 is not fig2
    finally:
        plt.close(fig1)
        plt.close(fig2)


def test_extract_lsb_plane_known_pattern():
    arr = np.array(
        [[[0, 1, 2], [3, 4, 5]], [[6, 7, 8], [9, 10, 11]]],
        dtype=np.uint8,
    )
    img = Image.fromarray(arr, mode="RGB")
    plane = extract_lsb_plane(img)
    assert plane.dtype == np.uint8
    assert set(np.unique(plane).tolist()) <= {0, 255}
    assert np.array_equal(plane, ((arr & 1) * 255).astype(np.uint8))


def test_extract_lsb_plane_only_zero_255_and_immutable():
    img = make_random_rgb(8, 8, seed=2)
    before = np.array(img).copy()
    plane = extract_lsb_plane(img)
    assert plane.shape == (8, 8, 3)
    assert set(np.unique(plane).tolist()) <= {0, 255}
    assert np.array_equal(np.array(img), before)


def test_extract_lsb_plane_rgba_ignores_alpha():
    rgba = Image.new("RGBA", (4, 4), color=(10, 11, 12, 0))
    plane = extract_lsb_plane(rgba)
    assert plane.shape == (4, 4, 3)


def test_jpeg_robustness_success_mock(tmp_path):
    stego = make_solid((120, 150, 200), size=(32, 32))
    stego_path = str(tmp_path / "stego.png")
    stego.save(stego_path, format="PNG")

    def fake_extract(path):
        with Image.open(path) as im:
            im.load()
        return b"payload"

    result = test_jpeg_robustness(stego_path, fake_extract, quality=90)
    assert result["success"] is True
    assert result["error"] is None
    assert result["jpeg_path"] != ""


def test_jpeg_robustness_failing_mock(tmp_path):
    stego = make_solid((120, 150, 200), size=(32, 32))
    stego_path = str(tmp_path / "stego.png")
    stego.save(stego_path, format="PNG")

    def fake_extract(path):
        raise RuntimeError("extract failed")

    result = test_jpeg_robustness(stego_path, fake_extract, quality=90)
    assert result["success"] is False
    assert "extract failed" in result["error"]
    assert result["jpeg_path"] != ""


def test_jpeg_robustness_missing_path():
    result = test_jpeg_robustness("/nonexistent/stego.png", lambda p: b"x")
    assert result["success"] is False
    assert result["error"] is not None


def test_figure_to_png_bytes_valid_png():
    cover = make_solid((10, 20, 30), size=(16, 16))
    stego = make_solid((11, 20, 30), size=(16, 16))
    fig = plot_histogram(cover, stego)
    try:
        data = figure_to_png_bytes(fig)
        assert isinstance(data, bytes)
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        reopened = Image.open(io.BytesIO(data))
        reopened.load()
        assert reopened.format == "PNG"
    finally:
        plt.close(fig)


def test_figure_to_base64_roundtrip():
    cover = make_solid((10, 20, 30), size=(16, 16))
    stego = make_solid((11, 20, 30), size=(16, 16))
    fig = plot_histogram(cover, stego)
    try:
        encoded = figure_to_base64(fig)
        assert isinstance(encoded, str)
        assert base64.b64decode(encoded)[:8] == b"\x89PNG\r\n\x1a\n"
    finally:
        plt.close(fig)


def test_lsb_plane_to_image_roundtrip():
    plane = extract_lsb_plane(make_random_rgb(8, 8, seed=3))
    img = lsb_plane_to_image(plane)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    assert img.size == (8, 8)
    assert np.array_equal(np.array(img), plane)


def test_lsb_plane_to_image_rejects_bad_input():
    with pytest.raises(AnalysisError):
        lsb_plane_to_image(np.zeros((4, 4, 3), dtype=np.int32))
    with pytest.raises(AnalysisError):
        lsb_plane_to_image(np.zeros((4, 4), dtype=np.uint8))
    with pytest.raises(AnalysisError):
        lsb_plane_to_image(np.full((4, 4, 3), 128, dtype=np.uint8))
    with pytest.raises(AnalysisError):
        lsb_plane_to_image([[0, 1, 2]])
