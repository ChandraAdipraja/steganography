import os
import base64
import hashlib
import io
import json
import shutil
import tempfile
import time
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from PIL import Image

import numpy as np

from src.analysis import (
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
from src.prng import derive_prng_seed, generate_positions
from src.report import build_xlsx, channel_maxdiff
from src.steganography import (
    FULL_OVERHEAD,
    HEADER_SIZE,
    bits_to_bytes,
    calculate_capacity,
    embed_payload,
    extract_payload,
    normalize_image,
    parse_header,
    CapacityError,
    InvalidImageError,
    InvalidPayloadError,
)
from src.crypto import CRYPTO_OVERHEAD_BYTES, decrypt_message, encrypt_message

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stegocrypt-dev")
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB per request batch

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Uji dataset: payload otomatis x3 per citra (sama seperti scripts/benchmark.py)
DATASET_PAYLOADS = (("small", 16), ("medium", 256), ("large", 1024))
DATASET_JPEG_QUALITY = 90
DATASET_MAX_FILES = 10
DATASET_MAX_DIM = 1024
BATCH_TTL_SECONDS = 3600


def _prune_batches():
    """Hapus batch dataset lebih tua dari TTL — cegah disk penuh di hosting."""
    now = time.time()
    try:
        for child in UPLOAD_DIR.iterdir():
            if child.is_dir() and child.name.startswith("batch_"):
                try:
                    if now - child.stat().st_mtime > BATCH_TTL_SECONDS:
                        shutil.rmtree(child, ignore_errors=True)
                except OSError:
                    pass
    except OSError:
        pass


def _dataset_plaintext(size: int) -> bytes:
    return bytes((i * 31 + size) % 256 for i in range(size))


def draft_derive_prng_seed(password: str) -> bytes:
    # wrapper for backwards compat — delegate ke src.prng.derive_prng_seed
    return derive_prng_seed(password)


def _extract_message_from_image(image: Image.Image, password: str) -> str:
    """Extract + decrypt hidden message (dipakai ulang route /analysis/jpeg).

    Logika identik dengan route /decode: baca header pakai
    generate_positions sebanyak HEADER_SIZE*8, parse panjang payload,
    generate posisi lengkap, extract_payload, decrypt_message.
    """
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGB")

    width, height = image.size
    total_slots = width * height * 3
    seed = draft_derive_prng_seed(password)
    header_bits_needed = HEADER_SIZE * 8
    if total_slots < header_bits_needed:
        raise InvalidPayloadError("Gambar terlalu kecil untuk berisi payload.")
    # prefix-consistent: generate_positions(total, 64, seed)
    # == generate_positions(total, needed, seed)[:64]
    header_positions = generate_positions(total_slots, header_bits_needed, seed)
    normalized = normalize_image(image)
    flat = np.array(normalized)[:, :, :3].reshape(-1)
    header_bits = [int(flat[p]) & 1 for p in header_positions]
    payload_length = parse_header(bits_to_bytes(header_bits))
    needed = (HEADER_SIZE + payload_length) * 8
    if needed > total_slots:
        raise InvalidPayloadError("Password salah atau data telah dimodifikasi.")
    positions = generate_positions(total_slots, needed, seed)
    payload = extract_payload(image, positions)
    plaintext = decrypt_message(payload, password)
    return plaintext.decode("utf-8")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/encode")
def encode_page():
    return render_template("encode.html")


@app.post("/encode")
def encode_post():
    cover_file = request.files.get("cover")
    password = request.form.get("password", "").strip()
    message = request.form.get("message", "")

    if not cover_file or cover_file.filename == "":
        flash("Silakan upload cover image.", "error")
        return redirect(url_for("encode_page"))

    if not password:
        flash("Silakan masukkan password.", "error")
        return redirect(url_for("encode_page"))

    if not message:
        flash("Silakan masukkan pesan.", "error")
        return redirect(url_for("encode_page"))

    try:
        image = Image.open(cover_file.stream)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")

        capacity = calculate_capacity(image)  # Opsi A: budget plaintext
        plain_bytes = message.encode("utf-8")
        if len(plain_bytes) > capacity:
            flash(f"Pesan terlalu besar untuk gambar ini. Maks {capacity} byte, pesan {len(plain_bytes)} byte.", "error")
            return redirect(url_for("encode_page"))

        try:
            payload = encrypt_message(plain_bytes, password)
        except ValueError:
            flash("Password tidak boleh kosong.", "error")
            return redirect(url_for("encode_page"))

        width, height = image.size
        total_slots = width * height * 3
        needed = (HEADER_SIZE + len(payload)) * 8
        # safety net: blob + header harus muat di slot (harusnya sudah terjamin oleh cek plaintext)
        if needed > total_slots:
            flash("Pesan terlalu besar untuk gambar ini (setelah enkripsi).", "error")
            return redirect(url_for("encode_page"))

        seed = draft_derive_prng_seed(password)
        # hanya generate sebanyak yang dibutuhkan — hemat untuk gambar besar + pesan kecil
        # prefix-consistent: generate_positions(total, needed, seed)[:64] == generate_positions(total, 64, seed)
        positions = generate_positions(total_slots, needed, seed)
        stego = embed_payload(image, payload, positions)

        cover_id = uuid.uuid4().hex[:8]
        cover_path = UPLOAD_DIR / f"{cover_id}_cover.png"
        stego_path = UPLOAD_DIR / f"{cover_id}_stego.png"

        image.save(cover_path, format="PNG")
        stego.save(stego_path, format="PNG")

        mse_value = calculate_mse(image, stego)
        psnr_value = calculate_psnr(image, stego)

        cover_url = url_for("static", filename=f"uploads/{cover_path.name}")
        stego_url = url_for("static", filename=f"uploads/{stego_path.name}")
        if psnr_value == float("inf"):
            psnr_display = "∞ (gambar identik)"
        else:
            psnr_display = f"{psnr_value:.2f} dB"

        flash("Pesan berhasil disisipkan!", "success")
        return render_template(
            "encode.html",
            cover_url=cover_url,
            stego_url=stego_url,
            mse_display=f"{mse_value:.6f}",
            psnr_display=psnr_display,
            blob_display=f"{len(payload):,} bytes",
            message_value=message,
            cover_w=width,
            cover_h=height,
            cover_budget=capacity,
        )

    except CapacityError:
        flash("Pesan terlalu besar untuk gambar.", "error")
        return redirect(url_for("encode_page"))
    except InvalidImageError as e:
        flash(str(e), "error")
        return redirect(url_for("encode_page"))
    except Exception as e:
        flash(f"Encoding gagal: {e}", "error")
        return redirect(url_for("encode_page"))


@app.post("/decode")
def decode_post():
    stego_file = request.files.get("stego")
    password = request.form.get("password", "").strip()

    if not stego_file or stego_file.filename == "":
        flash("Silakan upload stego image.", "error")
        return redirect(url_for("encode_page") + "#decode")

    if not password:
        flash("Silakan masukkan password.", "error")
        return redirect(url_for("encode_page") + "#decode")

    try:
        image = Image.open(stego_file.stream)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")

        width, height = image.size
        total_slots = width * height * 3
        seed = draft_derive_prng_seed(password)
        header_bits_needed = HEADER_SIZE * 8
        if total_slots < header_bits_needed:
            flash("Gambar terlalu kecil untuk berisi payload.", "error")
            return redirect(url_for("encode_page") + "#decode")
        # hemat: generate hanya 64 dulu untuk header, karena prefix-consistent
        # generate_positions(total, 64, seed) == generate_positions(total, needed, seed)[:64]
        header_positions = generate_positions(total_slots, header_bits_needed, seed)
        normalized = normalize_image(image)
        flat = np.array(normalized)[:, :, :3].reshape(-1)
        header_bits = [int(flat[p]) & 1 for p in header_positions]
        payload_length = parse_header(bits_to_bytes(header_bits))
        needed = (HEADER_SIZE + payload_length) * 8
        if needed > total_slots:
            flash("Password salah atau data telah dimodifikasi.", "error")
            return redirect(url_for("encode_page") + "#decode")
        positions = generate_positions(total_slots, needed, seed)
        payload = extract_payload(image, positions)
        plaintext = decrypt_message(payload, password)
        decoded = plaintext.decode("utf-8")

        stego_id = uuid.uuid4().hex[:8]
        stego_preview_path = UPLOAD_DIR / f"{stego_id}_decode_preview.png"
        if image.mode not in {"RGB", "RGBA"}:
            preview_img = image.convert("RGB")
        else:
            preview_img = image
        preview_img.save(stego_preview_path, format="PNG")
        stego_preview_url = url_for("static", filename=f"uploads/{stego_preview_path.name}")

        flash("Pesan berhasil diekstrak!", "success")
        return render_template(
            "encode.html",
            decoded_message=decoded,
            stego_preview_url=stego_preview_url,
            stego_w=width,
            stego_h=height,
        )

    except InvalidPayloadError:
        flash("Password salah atau data telah dimodifikasi.", "error")
        return redirect(url_for("encode_page") + "#decode")
    except ValueError:
        flash("Password salah atau data telah dimodifikasi.", "error")
        return redirect(url_for("encode_page") + "#decode")
    except UnicodeDecodeError:
        flash("Payload tidak dapat dibaca. Password mungkin salah.", "error")
        return redirect(url_for("encode_page") + "#decode")
    except Exception as e:
        flash(f"Decoding gagal: {e}", "error")
        return redirect(url_for("encode_page") + "#decode")


@app.route("/analysis")
def analysis_page():
    return render_template("analysis.html")


@app.post("/analysis/histogram")
def analysis_histogram_post():
    cover_file = request.files.get("cover")
    stego_file = request.files.get("stego")

    if (
        not cover_file
        or cover_file.filename == ""
        or not stego_file
        or stego_file.filename == ""
    ):
        flash("Silakan upload cover image dan stego image.", "error")
        return redirect(url_for("analysis_page"))

    try:
        cover = Image.open(cover_file.stream)
        stego = Image.open(stego_file.stream)
        if cover.mode not in {"RGB", "RGBA"}:
            cover = cover.convert("RGB")
        if stego.mode not in {"RGB", "RGBA"}:
            stego = stego.convert("RGB")

        fig = plot_histogram(cover, stego)
        histogram_b64 = "data:image/png;base64," + figure_to_base64(fig)
        mse_value = calculate_mse(cover, stego)
        psnr_value = calculate_psnr(cover, stego)
        if psnr_value == float("inf"):
            psnr_display = "∞ (gambar identik)"
        else:
            psnr_display = f"{psnr_value:.2f} dB"

        return render_template(
            "analysis.html",
            active_tab="histogram",
            histogram_b64=histogram_b64,
            hist_mse=f"{mse_value:.6f}",
            hist_psnr=psnr_display,
        )

    except Exception as e:
        flash(f"Histogram gagal: {e}", "error")
        return redirect(url_for("analysis_page"))


@app.post("/analysis/lsb")
def analysis_lsb_post():
    image_file = request.files.get("image")

    if not image_file or image_file.filename == "":
        flash("Silakan upload gambar.", "error")
        return redirect(url_for("analysis_page"))

    try:
        image = Image.open(image_file.stream)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")

        plane = extract_lsb_plane(image)
        lsb_image = lsb_plane_to_image(plane)

        lsb_buf = io.BytesIO()
        lsb_image.save(lsb_buf, format="PNG")
        lsb_b64 = "data:image/png;base64," + base64.b64encode(
            lsb_buf.getvalue()
        ).decode("ascii")

        orig_buf = io.BytesIO()
        image.save(orig_buf, format="PNG")
        lsb_orig_b64 = "data:image/png;base64," + base64.b64encode(
            orig_buf.getvalue()
        ).decode("ascii")

        return render_template(
            "analysis.html",
            active_tab="lsb",
            lsb_b64=lsb_b64,
            lsb_orig_b64=lsb_orig_b64,
        )

    except Exception as e:
        flash(f"Steganalisis LSB gagal: {e}", "error")
        return redirect(url_for("analysis_page"))


@app.post("/analysis/dataset")
def analysis_dataset_post():
    _prune_batches()
    files = request.files.getlist("dataset")
    files = [f for f in files if f and f.filename]
    password = request.form.get("password", "").strip()

    if not files:
        flash("Silakan upload minimal 1 file citra PNG.", "error")
        return redirect(url_for("analysis_page"))
    if len(files) > DATASET_MAX_FILES:
        flash(f"Maksimal {DATASET_MAX_FILES} file per batch.", "error")
        return redirect(url_for("analysis_page"))
    if not password:
        flash("Silakan masukkan satu password untuk semua citra.", "error")
        return redirect(url_for("analysis_page"))

    batch_id = uuid.uuid4().hex[:12]
    batch_dir = UPLOAD_DIR / f"batch_{batch_id}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "batch_id": batch_id,
        "created": time.time(),
        "password_note": "satu password untuk semua citra (tidak disimpan)",
        "payload_sizes": [size for _, size in DATASET_PAYLOADS],
        "jpeg_quality": DATASET_JPEG_QUALITY,
        "images": [],
    }

    try:
        seed = derive_prng_seed(password)
    except (TypeError, ValueError):
        shutil.rmtree(batch_dir, ignore_errors=True)
        flash("Password tidak valid.", "error")
        return redirect(url_for("analysis_page"))

    processed = 0
    for upload in files:
        fname = Path(upload.filename).name
        stem = Path(fname).stem.replace(" ", "_")
        try:
            cover = Image.open(upload.stream)
        except Exception:
            flash(f"Lewati {fname}: bukan gambar valid.", "error")
            continue
        if cover.mode not in {"RGB", "RGBA"}:
            cover = cover.convert("RGB")
        width, height = cover.size
        if max(width, height) > DATASET_MAX_DIM:
            flash(f"Lewati {fname}: dimensi melebihi {DATASET_MAX_DIM}px.", "error")
            continue
        capacity = calculate_capacity(cover)
        total_slots = width * height * 3

        cover_file = f"cover_{stem}.png"
        cover.save(batch_dir / cover_file, format="PNG")
        lsb_cover_file = f"lsb_cover_{stem}.png"
        lsb_plane_to_image(extract_lsb_plane(cover)).save(
            batch_dir / lsb_cover_file, format="PNG"
        )

        entry = {
            "name": fname,
            "resolution": f"{width}x{height}",
            "capacity": capacity,
            "cover_file": cover_file,
            "lsb_cover_file": lsb_cover_file,
            "payloads": {},
            "jpeg": {"success": False, "error": "belum diuji", "file": ""},
        }

        for label, size in DATASET_PAYLOADS:
            if size > capacity:
                entry["payloads"][label] = {"skipped": True, "size": size}
                continue
            try:
                plain = _dataset_plaintext(size)
                blob = encrypt_message(plain, password)
                needed = (HEADER_SIZE + len(blob)) * 8
                positions = generate_positions(total_slots, needed, seed)
                stego = embed_payload(cover, blob, positions)
                # roundtrip check
                raw = extract_payload(
                    stego, generate_positions(total_slots, needed, seed)
                )
                ok = decrypt_message(raw, password) == plain

                stego_file = f"stego_{stem}_{label}.png"
                stego.save(batch_dir / stego_file, format="PNG")
                fig = plot_histogram(cover, stego)
                try:
                    hist_file = f"hist_{stem}_{label}.png"
                    (batch_dir / hist_file).write_bytes(figure_to_png_bytes(fig))
                finally:
                    try:
                        from matplotlib import pyplot as plt
                        plt.close(fig)
                    except Exception:
                        pass
                lsb_stego_file = f"lsb_stego_{stem}_{label}.png"
                lsb_plane_to_image(extract_lsb_plane(stego)).save(
                    batch_dir / lsb_stego_file, format="PNG"
                )

                mse_v = calculate_mse(cover, stego)
                psnr_v = calculate_psnr(cover, stego)
                entry["payloads"][label] = {
                    "size": size,
                    "blob_size": len(blob),
                    "mse": mse_v,
                    "psnr": None if psnr_v == float("inf") else psnr_v,
                    "ok": bool(ok),
                    "hist_file": hist_file,
                    "stego_file": stego_file,
                    "lsb_stego_file": lsb_stego_file,
                }
            except Exception as e:
                entry["payloads"][label] = {
                    "size": size, "error": f"{type(e).__name__}: {e}"
                }

        # JPEG attack per citra — pakai stego medium (konsisten dgn benchmark)
        medium = entry["payloads"].get("medium", {})
        if medium.get("stego_file"):
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_path = tmp.name
                shutil.copy(batch_dir / medium["stego_file"], tmp_path)

                def extract_fn(jpeg_path, _password=password):
                    with Image.open(jpeg_path) as jpg:
                        jpg.load()
                        return _extract_message_from_image(jpg, _password)

                jres = test_jpeg_robustness(
                    tmp_path, extract_fn, DATASET_JPEG_QUALITY
                )
                jpeg_file = f"jpeg_{stem}.jpg"
                if jres.get("jpeg_path") and os.path.isfile(jres["jpeg_path"]):
                    shutil.copy(jres["jpeg_path"], batch_dir / jpeg_file)
                    os.unlink(jres["jpeg_path"])
                entry["jpeg"] = {
                    "success": bool(jres.get("success")),
                    "error": jres.get("error"),
                    "file": jpeg_file,
                }
            except Exception as e:
                entry["jpeg"] = {
                    "success": False, "error": f"{type(e).__name__}: {e}", "file": ""
                }
            finally:
                if tmp_path and os.path.isfile(tmp_path):
                    os.unlink(tmp_path)

        # metrik histogram per citra (pakai medium, konsisten dgn benchmark)
        if medium.get("hist_file"):
            stego_m = Image.open(batch_dir / medium["stego_file"])
            hist = generate_histogram(cover, stego_m)
            diffs = {ch: channel_maxdiff(hist[ch]) for ch in ("R", "G", "B")}
            worst = max(diffs.values())
            npixels = width * height
            entry["hist_diffs"] = diffs
            entry["hist_verdict"] = (
                f"OK (maks {worst/npixels:.2%} piksel)"
                if worst <= 0.02 * npixels
                else f"tinjau (maks {worst/npixels:.2%} piksel)"
            )
            entry["hist_file"] = medium["hist_file"]

        summary["images"].append(entry)
        processed += 1

    if not processed:
        shutil.rmtree(batch_dir, ignore_errors=True)
        flash("Tidak ada citra valid yang diproses.", "error")
        return redirect(url_for("analysis_page"))

    (batch_dir / "summary.json").write_text(json.dumps(summary))

    def _url(name):
        return url_for("static", filename=f"uploads/batch_{batch_id}/{name}") if name else ""

    view = {
        "batch_id": batch_id,
        "images": [
            {
                "name": e["name"],
                "resolution": e["resolution"],
                "capacity": e["capacity"],
                "cover_url": _url(e["cover_file"]),
                "lsb_cover_url": _url(e["lsb_cover_file"]),
                "hist_verdict": e.get("hist_verdict", "-"),
                "hist_diffs": e.get("hist_diffs", {}),
                "jpeg": {
                    "success": e["jpeg"]["success"],
                    "error": e["jpeg"]["error"],
                },
                "payloads": {
                    label: (
                        {"skipped": True, "size": p.get("size")}
                        if p.get("skipped") or "mse" not in p
                        else {
                            "size": p["size"],
                            "mse": round(p["mse"], 6),
                            "psnr": (
                                "inf" if p["psnr"] is None
                                else round(p["psnr"], 2)
                            ),
                            "ok": p["ok"],
                            "hist_url": _url(p["hist_file"]),
                            "stego_url": _url(p["stego_file"]),
                            "lsb_stego_url": _url(p["lsb_stego_file"]),
                        }
                    )
                    for label, p in e["payloads"].items()
                },
            }
            for e in summary["images"]
        ],
    }

    flash(f"Batch selesai: {processed} citra × 3 payload.", "success")
    return render_template(
        "analysis.html",
        active_tab="dataset",
        dataset_batch=view,
        dataset_json=json.dumps(view),
    )


@app.get("/analysis/dataset/download/<batch_id>")
def analysis_dataset_download(batch_id):
    if not batch_id or not batch_id.replace("_", "").isalnum() or len(batch_id) > 32:
        flash("Batch tidak valid.", "error")
        return redirect(url_for("analysis_page"))
    batch_dir = UPLOAD_DIR / f"batch_{batch_id}"
    summary_path = batch_dir / "summary.json"
    if not batch_dir.is_dir() or not summary_path.is_file():
        flash("Batch tidak ditemukan (mungkin sudah dibersihkan).", "error")
        return redirect(url_for("analysis_page"))

    summary = json.loads(summary_path.read_text())
    rows = []
    per_cover = []
    for e in summary["images"]:
        for label, size in DATASET_PAYLOADS:
            p = e["payloads"].get(label, {})
            if p.get("skipped") or "mse" not in p:
                continue
            rows.append({
                "image": e["name"],
                "resolution": e["resolution"],
                "message_size": p["size"],
                "payload_size": p["blob_size"],
                "mse": p["mse"],
                "psnr": float("inf") if p["psnr"] is None else p["psnr"],
                "extraction_ok": p["ok"],
            })
        if e.get("hist_file"):
            med = e["payloads"].get("medium", {})
            per_cover.append({
                "cover": e["name"],
                "resolution": e["resolution"],
                "hist_file": e["hist_file"],
                "hist_path": str(batch_dir / e["hist_file"]),
                "r_diff": e["hist_diffs"]["R"],
                "g_diff": e["hist_diffs"]["G"],
                "b_diff": e["hist_diffs"]["B"],
                "verdict": e["hist_verdict"],
                "lsb_file": e["lsb_cover_file"],
                "cover_file": e["cover_file"],
                "cover_path": str(batch_dir / e["cover_file"]),
                "stego_file": med.get("stego_file", ""),
                "stego_path": str(batch_dir / med["stego_file"]) if med.get("stego_file") else "",
                "lsb_cover_file": e["lsb_cover_file"],
                "lsb_cover_path": str(batch_dir / e["lsb_cover_file"]),
                "lsb_stego_file": med.get("lsb_stego_file", ""),
                "lsb_stego_path": str(batch_dir / med["lsb_stego_file"]) if med.get("lsb_stego_file") else "",
                "mse": med.get("mse"),
                "psnr": med.get("psnr"),
                "jpeg_file": e["jpeg"]["file"],
                "jpeg_success": e["jpeg"]["success"],
                "jpeg_error": e["jpeg"]["error"],
            })

    buf = io.BytesIO()
    build_xlsx(
        rows, per_cover, buf,
        cover_desc=f"{len(summary['images'])} file upload (uji dataset web)",
        message_desc="16 / 256 / 1024 byte plaintext (sintetis deterministik)",
        password_desc="satu password untuk semua citra (tidak disimpan)",
        jpeg_quality=summary.get("jpeg_quality", DATASET_JPEG_QUALITY),
    )
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"laporan_dataset_{batch_id}.xlsx",
    )


if __name__ == "__main__":
    app.run(debug=True)