# StegoCrypt — Secure Image Steganography

Aplikasi web untuk menyembunyikan pesan rahasia di dalam gambar. Pesan dienkripsi dengan **AES-256-GCM**, disisipkan memakai **LSB 1/2/3-bit**, dan posisi sisipannya diacak **PRNG** dari stego-key (password) — dengan header penanda `STG1`. Dibangun dengan **Python + Flask + Tailwind CSS**.

**Fitur utama:** Encode/Decode (varian m-bit, decode auto-detect 1→3) · Analysis (histogram cover vs stego, bidang LSB, uji dataset 1–10 citra + laporan XLSX: PSNR/MSE, Histogram, Steganalisis_LSB, Serangan_JPEG, Encode_Decode, Varian_mbit) · `scripts/benchmark.py` (pengujian 5 citra × 3 ukuran pesan).

## 1. Cara Instalasi

Prasyarat: **Python 3.10+**, **pip**, **Git** (dan Node.js + npx hanya bila ingin mengubah CSS).

```bash
# 1. clone repo (ganti dengan URL repo kelompok)
git clone [URL-repo]
cd steganography

# 2. instal dependensi
pip install -r requirements.txt
```

Opsional — compile ulang Tailwind (hanya bila mengedit file di `tailwind/` atau class di `templates/`):

```bash
npx @tailwindcss/cli -i ./tailwind/input.css -o ./static/css/output.css --minify
```

## 2. Cara Menjalankan

```bash
# development
python app.py
# buka browser: http://127.0.0.1:5000

# menjalankan pengujian otomatis + benchmark
python -m pytest tests/ -q
python scripts/benchmark.py   # hasil di docs/results/
```

## 3. Contoh Penggunaan

**Encode (sisipkan pesan):**

1. Buka halaman Encode → upload cover (PNG/BMP).
2. Isi password → tulis pesan.
3. Pilih varian LSB: 1-bit (bawaan) / 2-bit (kapasitas ×2) / 3-bit (kapasitas ×3).
4. Klik Encode Message → bandingkan Cover vs Stego + MSE/PSNR → download stego PNG.
5. Bagikan sebagai **PNG**.

**Decode (baca pesan):**

1. Tab Decode → upload stego + password yang sama → Decode Message.
2. Varian m-bit terdeteksi otomatis.

**Uji Dataset (laporan XLSX):**

1. Buka `/analysis` → tab Uji Dataset → upload 1–10 PNG + 1 password → Generate.
2. Pilih citra via dropdown (+ pills payload & varian) → lihat histogram + steganalisis (Cover vs Stego, bidang LSB keduanya).
3. Klik Download XLSX Lengkap.

## 4. Anggota Kelompok

| Nama | NPM |
|---|---|
| Muhammad Fadhlan Aminullah | 247006111151 |
| Angga Nurdiansyah | 247006111184 |
| Chandra Adipraja | 247006111194 |
