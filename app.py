import os
import io
import uuid
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image

from src.steganography import (
    calculate_capacity,
    embed_payload,
    extract_payload,
    HEADER_SIZE,
    CapacityError,
    InvalidImageError,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stegocrypt-dev")

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
        payload = message.encode("utf-8")

        if len(payload) > capacity:
            flash("Pesan terlalu besar untuk gambar ini.", "error")
            return redirect(url_for("encode_page"))

        positions = list(range((capacity + HEADER_SIZE) * 8))
        stego = embed_payload(image, payload, positions)

        cover_id = uuid.uuid4().hex[:8]
        cover_path = UPLOAD_DIR / f"{cover_id}_cover.png"
        stego_path = UPLOAD_DIR / f"{cover_id}_stego.png"

        # save original (normalized) for preview
        image.save(cover_path, format="PNG")
        stego.save(stego_path, format="PNG")

        cover_url = url_for("static", filename=f"uploads/{cover_path.name}")
        stego_url = url_for("static", filename=f"uploads/{stego_path.name}")

        flash("Pesan berhasil disisipkan!", "success")
        return render_template("encode.html", cover_url=cover_url, stego_url=stego_url)

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

        capacity = calculate_capacity(image)
        positions = list(range((capacity + HEADER_SIZE) * 8))
        payload = extract_payload(image, positions)
        decoded = payload.decode("utf-8")

        flash("Pesan berhasil diekstrak!", "success")
        return render_template("encode.html", decoded_message=decoded)

    except UnicodeDecodeError:
        flash("Payload tidak dapat dibaca. Password mungkin salah.", "error")
        return redirect(url_for("encode_page") + "#decode")
    except Exception as e:
        flash(f"Decoding gagal: {e}", "error")
        return redirect(url_for("encode_page") + "#decode")


if __name__ == "__main__":
    app.run(debug=True)
