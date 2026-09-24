Saya sedang mengembangkan aplikasi steganografi bernama **StegoCrypt** menggunakan Python + Streamlit.

Tolong bantu saya **mendesain ulang dan mempercantik UI aplikasi ini**, tetapi jangan mengubah logic/fungsi utama aplikasi.

## Kondisi project

Struktur project:

```text
steganography-project/
│
├── app.py
│
├── components/
│   ├── __init__.py
│   ├── navbar.py
│   ├── home.py
│   ├── about.py
│   ├── encoder.py
│   └── footer.py
│
├── src/
│   ├── __init__.py
│   ├── steganography.py
│   ├── crypto.py
│   ├── key.py
│   ├── prng.py
│   └── analysis.py
│
└── tests/
```

Aplikasi menggunakan:

* Python
* Streamlit
* Pillow
* NumPy
* PyCryptodome
* Matplotlib

Fungsi utama aplikasi adalah:

1. Menyisipkan pesan ke gambar menggunakan LSB.
2. Enkripsi pesan menggunakan AES.
3. Randomisasi posisi penyisipan menggunakan PRNG.
4. Decode pesan menggunakan stego-key.
5. Analisis gambar seperti MSE, PSNR, histogram, dan LSB analysis.

## Struktur halaman yang saya inginkan

Saya ingin aplikasi terasa seperti **modern security/product web app**, bukan seperti dashboard Streamlit default.

Struktur navigasinya:

```text
Navbar
│
├── Beranda
├── Tentang
└── Encode / Decode
```

### Beranda

Beranda merupakan landing page panjang yang berisi:

1. Hero section
2. CTA "Mulai Sekarang"
3. Section Tentang
4. Penjelasan teknologi
5. Cara kerja StegoCrypt
6. Footer

Ketika user menekan **Tentang**, idealnya halaman melakukan scroll ke section Tentang pada halaman Beranda.

### Encode / Decode

Encode / Decode harus menjadi halaman terpisah.

Di dalamnya terdapat:

* Tab Encode
* Tab Decode
* Upload gambar
* Input pesan
* Password/stego-key
* Capacity information
* Preview cover image
* Preview stego image
* Download hasil
* Hasil extraction

## Gaya visual yang diinginkan

Gunakan gaya:

**Modern security application + clean minimal + premium**

Referensi visual:

* Clean minimal
* Dark/light mode friendly
* Banyak whitespace
* Typography modern
* Rounded card
* Border tipis
* Subtle shadow
* Tidak terlalu banyak warna
* Tidak terlihat seperti template admin dashboard
* Tidak terlalu ramai
* Tidak menggunakan gradient berlebihan
* Tidak menggunakan animasi yang berlebihan

Aplikasi harus terlihat seperti produk security/technology modern.

## Warna

Gunakan warna yang netral dan cocok dengan Streamlit dark/light mode.

Prioritaskan:

* background mengikuti theme Streamlit
* text mengikuti theme
* border abu-abu transparan
* accent secukupnya

Jangan hard-code background putih atau hitam yang membuat salah satu theme rusak.

## Typography

Buat hierarchy yang jelas:

* Brand
* Hero heading besar
* Section heading
* Card heading
* Body text
* Caption

Gunakan ukuran font yang proporsional dan jangan membuat semua teks terlihat terlalu besar.

## Navbar

Navbar harus terlihat seperti navbar aplikasi modern:

```text
🔐 StegoCrypt                     Beranda  Tentang  Encode / Decode
Secure image steganography
```

Navbar harus:

* clean
* tidak terlalu tinggi
* memiliki spacing yang bagus
* button terlihat konsisten
* tidak menutupi UI bawaan Streamlit
* tetap usable di layar kecil

Jangan membuat navbar menggunakan HTML yang kompleks jika Streamlit tidak merendernya dengan baik.

Gunakan komponen Streamlit native jika memungkinkan:

* st.columns
* st.button
* st.markdown
* st.caption
* st.divider
* st.container

## Hero

Hero harus menjadi bagian paling menarik dari landing page.

Konsep:

```text
        SECURE IMAGE STEGANOGRAPHY

        Sembunyikan Pesan Rahasia
        Di Balik Sebuah Gambar.

        StegoCrypt membantu Anda menyisipkan
        pesan rahasia ke dalam gambar menggunakan
        LSB, AES, dan PRNG.

              [ Mulai Sekarang → ]

             PNG · BMP · LSB · AES · PRNG
```

Gunakan whitespace yang cukup.

Jangan membuat hero terlalu ramai.

## Section Teknologi

Buat 3 card:

```text
┌─────────────────┐
│ 🖼️              │
│ LSB             │
│ Steganografi    │
│                 │
│ Penjelasan...   │
└─────────────────┘

┌─────────────────┐
│ 🔒              │
│ AES             │
│ Enkripsi        │
│                 │
│ Penjelasan...   │
└─────────────────┘

┌─────────────────┐
│ 🎲              │
│ PRNG            │
│ Stego-Key       │
│                 │
│ Penjelasan...   │
└─────────────────┘
```

Card harus memiliki:

* border tipis
* radius konsisten
* padding cukup
* typography hierarchy
* hover effect hanya jika aman dilakukan di Streamlit

## Process Section

Tampilkan proses:

```text
Pesan
  ↓
Enkripsi
  ↓
Randomisasi
  ↓
LSB Embedding
  ↓
Stego Image
```

Buat tampilannya seperti process flow modern.

## Encode / Decode UI

Halaman Encode / Decode harus menjadi bagian paling fungsional.

Prioritaskan:

* visual hierarchy
* input yang jelas
* status/error yang mudah dibaca
* preview gambar
* metrics
* hasil encode/decode

Contohnya:

```text
Encode

[ Upload Cover Image ]

Image Information
┌──────────┬──────────┬──────────┐
│ Format   │ Size     │ Capacity │
└──────────┴──────────┴──────────┘

Message
┌──────────────────────────────┐
│                              │
│                              │
└──────────────────────────────┘

Stego-Key
[ ********************** ]

              [ Encode ]

────────────────────────────────

Cover Image              Stego Image
┌──────────────┐         ┌──────────────┐
│              │         │              │
│    IMAGE     │         │    IMAGE     │
│              │         │              │
└──────────────┘         └──────────────┘

PSNR: XX dB
MSE: XX
```

## Penting: jangan merusak logic

Ini sangat penting.

Jangan mengubah:

* fungsi LSB
* payload format
* AES
* PRNG
* capacity calculation
* extraction
* test
* struktur `src/`
* nama fungsi yang sudah digunakan
* import yang sudah diperlukan

UI redesign harus hanya mengubah **presentation layer**.

Kalau perlu perubahan pada `app.py`, `components/`, atau CSS, lakukan seminimal mungkin.

## Sangat penting tentang Streamlit

Saya sebelumnya mengalami masalah ketika HTML seperti:

```html
<div class="hero">
    ...
</div>
```

justru tampil sebagai teks Markdown di halaman.

Karena itu:

1. Prioritaskan komponen Streamlit native.
2. Jangan menggunakan HTML kompleks kecuali benar-benar diperlukan.
3. Jangan menggunakan `<a>`, `<div>`, `<section>`, `<h1>`, dan struktur HTML kompleks untuk komponen utama.
4. CSS boleh digunakan melalui `st.markdown(..., unsafe_allow_html=True)` jika memang aman.
5. Jangan membuat seluruh UI bergantung pada HTML custom.
6. Pastikan setelah perubahan tidak ada raw HTML yang tampil sebagai teks.

## Responsiveness

UI harus tetap nyaman pada:

* desktop
* laptop
* tablet
* mobile

Gunakan `st.columns()` secara bijak.

Jangan membuat layout terlalu lebar.

## Coding requirement

Sebelum mengubah kode:

1. Baca struktur project.
2. Baca `app.py`.
3. Baca seluruh file dalam `components/`.
4. Jangan langsung menulis ulang seluruh aplikasi.
5. Pertahankan logic yang sudah berjalan.
6. Identifikasi bagian yang hanya UI/presentation.
7. Lakukan perubahan bertahap.

Setelah selesai:

* jelaskan file apa saja yang diubah
* tampilkan full code untuk setiap file yang diubah
* jangan menghilangkan fungsi yang sudah ada
* pastikan aplikasi tetap bisa dijalankan dengan:

```bash
streamlit run app.py
```

Target akhirnya adalah **StegoCrypt yang terlihat seperti aplikasi security modern dan profesional, tetapi tetap terasa natural sebagai aplikasi Streamlit dan tidak memaksakan Streamlit menjadi React.**
