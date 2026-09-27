import csv
import datetime
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
    generate_histogram,
    lsb_plane_to_image,
    plot_histogram,
    test_jpeg_robustness,
)
from src.crypto import decrypt_message, encrypt_message
from src.prng import derive_prng_seed, generate_positions
from src.report import build_xlsx, channel_maxdiff
from src.roundtrip import run_codec_case
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
    # Opsi A: capacity = budget plaintext → cek plaintext, bukan blob
    if len(plaintext) > calculate_capacity(cover):
        raise ValueError("plaintext exceeds capacity")
    blob = encrypt_message(plaintext, PASSWORD)
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
    medium_by_cover = {}
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
            if label == "medium":
                medium_by_cover[cover_path] = (plaintext, result)
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
    per_cover = build_per_cover_outputs(medium_by_cover)
    roundtrip = build_roundtrip_cases(rows, medium_by_cover)
    xlsx_path = RESULTS_DIR / "benchmark.xlsx"
    build_xlsx(
        rows, per_cover, xlsx_path,
        cover_desc=f"{len(medium_by_cover)} file PNG 256x256 (assets/cover)",
        message_desc="16 / 256 / 1024 byte plaintext (sintetis deterministik)",
        password_desc="benchmark-key-123 (dummy, reproduksibilitas)",
        jpeg_quality=JPEG_QUALITY,
        roundtrip=roundtrip,
    )
    print(f"wrote {len(rows)} rows to {csv_path}")
    print(f"wrote workbook to {xlsx_path}")


def build_roundtrip_cases(rows, medium_by_cover):
    """20 baris sheet Encode_Decode: 15 Benar (pakai ulang hasil run)
    + 5 Salah (decode stego medium dengan password salah, tanpa re-embed)."""
    cases = []
    for row in rows:
        if row["extraction_ok"]:
            cases.append({
                "image": row["image"],
                "message_size": row["message_size"],
                "key_status": "Benar",
                "fail_stage": "selesai",
                "success": True,
                "error": "-",
                "recovered": "Yes",
            })
        else:
            # jarang terjadi — jalankan staged helper untuk tahu tahap persisnya
            cover_path = next(
                p for p in medium_by_cover
                if p.name == row["image"]
            )
            cover = Image.open(cover_path)
            size = row["message_size"]
            detail = run_codec_case(
                cover, make_plaintext(size), PASSWORD, PASSWORD, "Benar"
            )
            cases.append({"image": row["image"], "message_size": size, **detail})
    for cover_path, (plaintext, result) in sorted(
        medium_by_cover.items(), key=lambda kv: kv[0].name
    ):
        detail = run_codec_case(
            result["cover"], plaintext,
            PASSWORD, PASSWORD + "-salah", "Salah",
            stego=result["stego"],
        )
        cases.append({
            "image": cover_path.name,
            "message_size": len(plaintext),
            **detail,
        })
        print(f"{cover_path.name} kunci-salah: {detail['fail_stage']} "
              f"success={detail['success']}")
    return cases


def build_per_cover_outputs(medium_by_cover):
    per_cover = []
    for cover_path, (_, result) in sorted(
        medium_by_cover.items(), key=lambda kv: kv[0].name
    ):
        stem = cover_path.stem
        cover = result["cover"]
        stego = result["stego"]
        width, height = result["width"], result["height"]
        npixels = width * height

        # 1. histogram full-res + metrik per channel
        fig = plot_histogram(cover, stego)
        try:
            hist_file = RESULTS_DIR / f"histogram_{stem}.png"
            hist_file.write_bytes(figure_to_png_bytes(fig))
        finally:
            plt.close(fig)
        hist = generate_histogram(cover, stego)
        diffs = {ch: channel_maxdiff(hist[ch]) for ch in ("R", "G", "B")}
        worst = max(diffs.values())
        verdict = (
            f"OK (maks {worst/npixels:.2%} piksel)"
            if worst <= 0.02 * npixels
            else f"tinjau (maks {worst/npixels:.2%} piksel)"
        )

        # 2. LSB plane full-res (cover + stego, untuk sheet Steganalisis)
        lsb_file = RESULTS_DIR / f"lsb_{stem}.png"
        lsb_plane_to_image(extract_lsb_plane(stego)).save(
            lsb_file, format="PNG"
        )
        lsb_cover_file = RESULTS_DIR / f"lsb_cover_{stem}.png"
        lsb_plane_to_image(extract_lsb_plane(cover)).save(
            lsb_cover_file, format="PNG"
        )
        stego_file = RESULTS_DIR / f"stego_{stem}_medium.png"
        stego.save(stego_file, format="PNG")

        # 3. uji kerapuhan JPEG quality=90 untuk citra ini
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            stego_path = tmp.name
        try:
            stego.save(stego_path, format="PNG")
            positions = result["positions"]

            def extract_from_jpeg(jpeg_path, _positions=positions):
                img = Image.open(jpeg_path)
                raw = extract_payload(img, _positions)
                return decrypt_message(raw, PASSWORD)

            jpeg_result = test_jpeg_robustness(
                stego_path, extract_from_jpeg, quality=JPEG_QUALITY
            )
        finally:
            os.remove(stego_path)
        jpeg_file = RESULTS_DIR / f"jpeg_{stem}.jpg"
        if jpeg_result["jpeg_path"] and os.path.isfile(jpeg_result["jpeg_path"]):
            shutil.copy(jpeg_result["jpeg_path"], jpeg_file)
            os.remove(jpeg_result["jpeg_path"])

        print(
            f"{cover_path.name}: hist R/G/B d={diffs['R']}/{diffs['G']}/{diffs['B']} "
            f"jpeg success={jpeg_result['success']}"
        )
        per_cover.append(
            {
                "cover": cover_path.name,
                "resolution": f"{width}x{height}",
                "hist_file": hist_file.name,
                "hist_path": str(hist_file),
                "r_diff": diffs["R"],
                "g_diff": diffs["G"],
                "b_diff": diffs["B"],
                "verdict": verdict,
                "lsb_file": lsb_file.name,
                "cover_file": cover_path.name,
                "cover_path": str(cover_path),
                "stego_file": stego_file.name,
                "stego_path": str(stego_file),
                "lsb_cover_file": lsb_cover_file.name,
                "lsb_cover_path": str(lsb_cover_file),
                "lsb_stego_file": lsb_file.name,
                "lsb_stego_path": str(lsb_file),
                "mse": result["mse"],
                "psnr": result["psnr"],
                "jpeg_file": jpeg_file.name,
                "jpeg_success": jpeg_result["success"],
                "jpeg_error": jpeg_result["error"],
            }
        )
    return per_cover


if __name__ == "__main__":
    main()
