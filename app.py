import os
import base64
import hashlib
import io
import shutil
import tempfile
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image

import numpy as np

from src.analysis import (
    calculate_mse,
    calculate_psnr,
    extract_lsb_plane,
    figure_to_base64,
    lsb_plane_to_image,
    plot_histogram,
    test_jpeg_robustness,
)
from src.prng import derive_prng_seed, generate_positions
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

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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


@app.post("/analysis/jpeg")
def analysis_jpeg_post():
    stego_file = request.files.get("stego")
    password = request.form.get("password", "").strip()
    quality_raw = request.form.get("quality", "90")
    try:
        quality = int(quality_raw)
    except (TypeError, ValueError):
        quality = 90
    if quality not in (90, 70, 50):
        quality = 90

    if not stego_file or stego_file.filename == "":
        flash("Silakan upload stego image.", "error")
        return redirect(url_for("analysis_page"))

    if not password:
        flash("Silakan masukkan password.", "error")
        return redirect(url_for("analysis_page"))

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        stego_file.save(tmp_path)

        def extract_fn(jpeg_path: str) -> str:
            with Image.open(jpeg_path) as jpg:
                jpg.load()
                return _extract_message_from_image(jpg, password)

        result = test_jpeg_robustness(tmp_path, extract_fn, quality)

        stego_id = uuid.uuid4().hex[:8]
        with Image.open(tmp_path) as orig:
            if orig.mode not in {"RGB", "RGBA"}:
                orig = orig.convert("RGB")
            orig_path = UPLOAD_DIR / f"{stego_id}_analysis_orig.png"
            orig.save(orig_path, format="PNG")
        jpeg_stego_url = url_for("static", filename=f"uploads/{orig_path.name}")

        jpeg_url = None
        internal_jpeg = result.get("jpeg_path") or ""
        if internal_jpeg and os.path.isfile(internal_jpeg):
            jpeg_path = UPLOAD_DIR / f"{stego_id}_converted_q{quality}.jpg"
            shutil.copy(internal_jpeg, jpeg_path)
            os.unlink(internal_jpeg)
            jpeg_url = url_for("static", filename=f"uploads/{jpeg_path.name}")

        return render_template(
            "analysis.html",
            active_tab="jpeg",
            jpeg_success=bool(result.get("success")),
            jpeg_error=result.get("error"),
            jpeg_quality=quality,
            jpeg_url=jpeg_url,
            jpeg_stego_url=jpeg_stego_url,
        )

    except Exception as e:
        flash(f"Uji JPEG gagal: {e}", "error")
        return redirect(url_for("analysis_page"))
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    app.run(debug=True)