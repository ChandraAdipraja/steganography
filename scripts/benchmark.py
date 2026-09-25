import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import (
    calculate_mse,
    calculate_psnr,
    extract_lsb_plane,
    figure_to_png_bytes,
    lsb_plane_to_image,
    plot_histogram,
    test_jpeg_robustness,
)
from src.crypto import decrypt_message, encrypt_message
from src.prng import derive_prng_seed, generate_positions
from src.steganography import (
    calculate_capacity,
    embed_payload,
    extract_payload,
)

COVER_DIR = ROOT / "assets" / "cover"
RESULTS_DIR = ROOT / "docs" / "results"
PASSWORD = "benchmark-key-123"
MESSAGE_SIZES = (("small", 16), ("medium", 256), ("large", 1024))
JPEG_QUALITY = 90


def make_plaintext(size):
    return bytes((i * 31 + size) % 256 for i in range(size))


def fmt_psnr(value):
    if value == float("inf"):
        return "inf"
    return f"{value:.2f}"


def run_experiment(cover_path, plaintext):
    cover = Image.open(cover_path)
    if cover.mode not in {"RGB", "RGBA"}:
        cover = cover.convert("RGB")
    width, height = cover.size
    total_slots = width * height * 3
    blob = encrypt_message(plaintext, PASSWORD)
    if len(blob) > calculate_capacity(cover):
        raise ValueError("payload exceeds capacity")
    seed = derive_prng_seed(PASSWORD)
    positions = generate_positions(total_slots, total_slots, seed)
    stego = embed_payload(cover, blob, positions)
    mse = calculate_mse(cover, stego)
    psnr = calculate_psnr(cover, stego)
    check_positions = generate_positions(total_slots, total_slots, seed)
    raw = extract_payload(stego, check_positions)
    recovered = decrypt_message(raw, PASSWORD)
    return {
        "cover": cover,
        "stego": stego,
        "width": width,
        "height": height,
        "payload_size": len(blob),
        "positions": positions,
        "mse": mse,
        "psnr": psnr,
        "ok": recovered == plaintext,
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    covers = sorted(COVER_DIR.glob("*.png"))
    if not covers:
        raise ValueError("no cover images in assets/cover")
    rows = []
    showcase = None
    for cover_path in covers:
        for label, size in MESSAGE_SIZES:
            plaintext = make_plaintext(size)
            result = run_experiment(cover_path, plaintext)
            rows.append(
                {
                    "image": cover_path.name,
                    "resolution": f"{result['width']}x{result['height']}",
                    "message_size": size,
                    "payload_size": result["payload_size"],
                    "mse": result["mse"],
                    "psnr": result["psnr"],
                    "extraction_ok": result["ok"],
                }
            )
            print(
                f"{cover_path.name} {label}({size}B): "
                f"mse={result['mse']:.6f} "
                f"psnr={fmt_psnr(result['psnr'])} ok={result['ok']}"
            )
            if showcase is None and label == "medium":
                showcase = (cover_path, plaintext, result)
    csv_path = RESULTS_DIR / "benchmark_5x3.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "image",
                "resolution",
                "message_size",
                "payload_size",
                "mse",
                "psnr",
                "extraction_ok",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["psnr"] = fmt_psnr(out["psnr"])
            writer.writerow(out)
    md_lines = [
        "# Benchmark 5 citra x 3 ukuran pesan",
        "",
        "Stego-key: `benchmark-key-123` (dummy tetap untuk reproduksibilitas, bukan secret asli).",
        "",
        "| image | resolution | message_size | payload_size | mse | psnr | extraction_ok |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['image']} | {row['resolution']} | {row['message_size']} "
            f"| {row['payload_size']} | {row['mse']:.6f} "
            f"| {fmt_psnr(row['psnr'])} | {row['extraction_ok']} |"
        )
    (RESULTS_DIR / "benchmark_5x3.md").write_text("\n".join(md_lines) + "\n")
    cover_path, _, result = showcase
    fig = plot_histogram(result["cover"], result["stego"])
    try:
        (RESULTS_DIR / "histogram_example.png").write_bytes(
            figure_to_png_bytes(fig)
        )
    finally:
        plt.close(fig)
    lsb_plane_to_image(extract_lsb_plane(result["stego"])).save(
        RESULTS_DIR / "lsb_example.png", format="PNG"
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        stego_path = tmp.name
    try:
        result["stego"].save(stego_path, format="PNG")
        positions = result["positions"]

        def extract_from_jpeg(jpeg_path):
            img = Image.open(jpeg_path)
            raw = extract_payload(img, positions)
            return decrypt_message(raw, PASSWORD)

        jpeg_result = test_jpeg_robustness(
            stego_path, extract_from_jpeg, quality=JPEG_QUALITY
        )
    finally:
        os.remove(stego_path)
    if jpeg_result["jpeg_path"] and os.path.isfile(jpeg_result["jpeg_path"]):
        shutil.copy(
            jpeg_result["jpeg_path"], RESULTS_DIR / "jpeg_example.jpg"
        )
        os.remove(jpeg_result["jpeg_path"])
    jpeg_md = [
        "# Hasil uji kerapuhan JPEG",
        "",
        f"Sumber: `{cover_path.name}` x pesan medium (256 byte plaintext), quality={JPEG_QUALITY}.",
        "",
        f"success: `{jpeg_result['success']}`",
        "",
        f"error: `{jpeg_result['error']}`",
        "",
        "File: `jpeg_example.jpg`",
        "",
    ]
    (RESULTS_DIR / "jpeg_test.md").write_text("\n".join(jpeg_md))
    print(f"wrote {len(rows)} rows to {csv_path}")


if __name__ == "__main__":
    main()
