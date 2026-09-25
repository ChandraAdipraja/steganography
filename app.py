import os
import hashlib
import io
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image

import numpy as np

from src.analysis import calculate_mse, calculate_psnr
from src.prng import generate_positions
from src.steganography import (
    calculate_capacity,
    embed_payload,
    extract_payload,
    normalize_image,
    bits_to_bytes,
    parse_header,
    HEADER_SIZE,
    CapacityError,
    InvalidImageError,
    InvalidPayloadError,
)
from src.crypto import decrypt_message, encrypt_message

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stegocrypt-dev")

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def draft_derive_prng_seed(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("password must be a str")
    if not password.strip():
        raise ValueError("password must be a non-empty string")
    return hashlib.sha256((password + "|PRNG").encode("utf-8")).digest()


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

        capacity = calculate_capacity(image)
        try:
            payload = encrypt_message(message.encode("utf-8"), password)
        except ValueError:
            flash("Password tidak boleh kosong.", "error")
            return redirect(url_for("encode_page"))

        if len(payload) > capacity:
            flash("Pesan terlalu besar untuk gambar ini.", "error")
            return redirect(url_for("encode_page"))

        width, height = image.size
        total_slots = width * height * 3
        seed = draft_derive_prng_seed(password)
        needed = (HEADER_SIZE + len(payload)) * 8
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
            payload_len=len(payload),
            payload_hex_preview=payload.hex()[:512],
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
        header_positions = generate_positions(
            total_slots, header_bits_needed, seed
        )
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

        flash("Pesan berhasil diekstrak!", "success")
        return render_template("encode.html", decoded_message=decoded)

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


if __name__ == "__main__":
    app.run(debug=True)