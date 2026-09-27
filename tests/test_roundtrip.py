from PIL import Image

from src.roundtrip import run_codec_case


def _cover(size=(64, 64)):
    return Image.new("RGB", size, color=(120, 150, 200))


def test_correct_key_recovers():
    out = run_codec_case(_cover(), b"pesan rahasia", "kunci", "kunci", "Benar")
    assert out["key_status"] == "Benar"
    assert out["fail_stage"] == "selesai"
    assert out["success"] is True
    assert out["error"] == "-"
    assert out["recovered"] == "Yes"


def test_wrong_key_fails_at_header():
    cover = _cover()
    first = run_codec_case(cover, b"pesan rahasia", "kunci", "kunci", "Benar")
    assert first["success"] is True
    # pakai ulang stego tidak bisa — helper menanam sendiri; untuk Salah,
    # encode dengan kunci benar lalu decode dengan kunci salah:
    from src.crypto import encrypt_message
    from src.prng import derive_prng_seed, generate_positions
    from src.steganography import HEADER_SIZE, embed_payload

    blob = encrypt_message(b"pesan rahasia", "kunci")
    total = 64 * 64 * 3
    seed = derive_prng_seed("kunci")
    positions = generate_positions(total, total, seed)
    stego = embed_payload(cover, blob, positions)

    out = run_codec_case(
        cover, b"pesan rahasia", "kunci", "kunci-salah", "Salah", stego=stego
    )
    assert out["key_status"] == "Salah"
    assert out["fail_stage"] == "ekstrak header"
    assert out["success"] is False
    assert "InvalidPayloadError" in out["error"]
    assert "Invalid steganography header" in out["error"]
    assert out["recovered"] == "No"


def test_over_capacity_fails_at_stage_one():
    tiny = Image.new("RGB", (4, 4))  # kapasitas plaintext = 0
    out = run_codec_case(tiny, b"x" * 10, "kunci", "kunci", "Benar")
    assert out["fail_stage"] == "cek kapasitas"
    assert out["success"] is False
    assert out["recovered"] == "No"
