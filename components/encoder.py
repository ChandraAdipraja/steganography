import io
from pathlib import Path

import streamlit as st
from PIL import Image

from src.steganography import (
    CapacityError,
    InvalidImageError,
    calculate_capacity,
    embed_payload,
    extract_payload,
    HEADER_SIZE,
)


def render_encoder():
    # Clean stray #tentang from URL when entering Encode/Decode — keeps URL clean
    st.html(
        """
        <script>
        (function(){
            try {
                const loc = window.location;
                const pLoc = (window.parent && window.parent.location && window.parent.location.hash !== undefined) ? window.parent.location : loc;
                const hist = (window.parent && window.parent.history) ? window.parent.history : window.history;
                if (pLoc.hash === "#tentang") hist.replaceState(null, "", pLoc.pathname + pLoc.search);
            } catch(e) {}
        })();
        </script>
        """
    )
    st.markdown(
        """
        <style>
            .sc-page-head {
                max-width: 760px;
                padding: 1.2rem 0 0.8rem 0;
            }
            .sc-page-head h2 {
                font-size: clamp(1.8rem, 3.6vw, 2.6rem);
                font-weight: 800;
                letter-spacing: -0.045em;
                line-height: 1.05;
                margin: 0 0 0.6rem 0;
            }
            .sc-page-head p {
                font-size: 0.98rem;
                line-height: 1.7;
                opacity: 0.65;
                margin: 0;
                max-width: 560px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sc-page-head">
            <div class="sc-eyebrow">StegoCrypt Tool</div>
            <h2>Encode & Decode</h2>
            <p>Sembunyikan pesan ke dalam gambar atau ekstrak kembali pesan yang telah disisipkan — satu alur, dua mode.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    encode_tab, decode_tab = st.tabs(
        [
            "Encode",
            "Decode",
        ]
    )

    with encode_tab:
        render_encode()

    with decode_tab:
        render_decode()


def render_encode():
    st.write("")
    st.markdown(
        '<div class="sc-eyebrow">Encode</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Sembunyikan Pesan")
    st.markdown(
        '<div class="sc-muted">Upload PNG atau BMP, tulis pesan, lalu encode menjadi stego image yang siap dibagikan.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    # 1. Cover Image
    with st.container(border=True):
        st.markdown("**01 — Cover Image**")
        st.markdown(
            '<div class="sc-caption" style="margin-bottom:0.7rem">Format yang didukung: PNG dan BMP. Gambar tidak diubah kecuali pada bit LSB.</div>',
            unsafe_allow_html=True,
        )
        encode_file = st.file_uploader(
            "Upload gambar yang akan digunakan sebagai cover",
            type=["png", "bmp"],
            key="encode_upload",
            help="Format yang didukung: PNG dan BMP.",
            label_visibility="collapsed",
        )

        cover_image = None
        capacity = None

        if encode_file is not None:
            try:
                cover_image = Image.open(encode_file)

                if cover_image.mode not in {"RGB", "RGBA"}:
                    cover_image = cover_image.convert("RGB")

                capacity = calculate_capacity(cover_image)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Width", f"{cover_image.width}px")
                with col2:
                    st.metric("Height", f"{cover_image.height}px")
                with col3:
                    st.metric("Capacity", f"{capacity:,} bytes")

                st.image(cover_image, caption="Cover Image", width="stretch")

            except Exception as error:
                st.error(f"Gagal memuat gambar: {error}")
        else:
            st.markdown(
                '<div class="sc-caption">Belum ada gambar. Upload untuk melihat kapasitas dan preview.</div>',
                unsafe_allow_html=True,
            )

    # We need to keep cover_image/capacity accessible for later logic.
    # Re-evaluate if file was not uploaded above, variables already set.
    # But after container, logic below needs them — we re-derive from session? Keep as defined.
    # To avoid scope issue, re-open logic: if encode_file is None, cover_image stays None.
    # Variables are in function scope, so we keep them.

    st.write("")

    # 2. Password + 3. Message in two columns for cleaner layout
    with st.container(border=True):
        st.markdown("**02 — Keamanan**")
        encode_password = st.text_input(
            "Password",
            type="password",
            placeholder="Masukkan password...",
            key="encode_password",
        )
        st.markdown(
            '<div class="sc-caption">Password digunakan untuk enkripsi dan pembuatan stego-key pada versi final.</div>',
            unsafe_allow_html=True,
        )

    st.write("")

    with st.container(border=True):
        st.markdown("**03 — Secret Message**")
        encode_message = st.text_area(
            "Pesan",
            placeholder="Tulis pesan rahasia yang ingin disembunyikan...",
            height=160,
            key="encode_message",
        )

        if encode_message:
            message_size = len(encode_message.encode("utf-8"))
            st.caption(f"Ukuran pesan: {message_size:,} bytes")

            if capacity is not None:
                if message_size > capacity:
                    st.error("Pesan terlalu besar untuk gambar ini.")
                else:
                    st.success("Pesan masih berada dalam kapasitas gambar.")
            else:
                st.caption("Upload cover image untuk cek kapasitas.")
        else:
            st.caption("Pesan akan dienkripsi sebelum disisipkan.")

    st.write("")

    encode_button = st.button(
        "Encode Message →",
        type="primary",
        use_container_width=True,
        key="encode_button",
    )

    if encode_button:

        if cover_image is None:
            st.warning("Silakan upload cover image terlebih dahulu.")

        elif not encode_password:
            st.warning("Silakan masukkan encryption password.")

        elif not encode_message:
            st.warning("Silakan masukkan pesan rahasia.")

        elif capacity is not None and (len(encode_message.encode("utf-8")) > capacity):
            st.error("Pesan terlalu besar untuk gambar yang dipilih.")

        else:

            try:
                # -------------------------------------------------
                # TEMPORARY PAYLOAD
                # -------------------------------------------------
                #
                # Saat ini payload masih berupa plaintext.
                #
                # Nanti:
                #
                # message
                #     ↓
                # AES
                #     ↓
                # ciphertext
                #     ↓
                # embed_payload()
                #
                # -------------------------------------------------

                payload = encode_message.encode("utf-8")

                # Temporary sequential positions.
                #
                # Nanti bagian ini akan digantikan
                # oleh PRNG berdasarkan stego-key.

                positions = list(range((capacity + HEADER_SIZE) * 8))

                stego_image = embed_payload(
                    cover_image,
                    payload,
                    positions,
                )

                output = io.BytesIO()

                stego_image.save(output, format="PNG")

                output.seek(0)

                st.session_state["encoded_cover"] = cover_image

                st.session_state["encoded_stego"] = stego_image

                st.session_state["encoded_bytes"] = output.getvalue()

                st.session_state["encoded_positions"] = positions

                st.success("Pesan berhasil disisipkan ke dalam gambar!")

            except CapacityError:
                st.error("Pesan terlalu besar untuk gambar.")

            except InvalidImageError as error:
                st.error(str(error))

            except Exception as error:
                st.error(f"Encoding gagal: {error}")

    if "encoded_stego" in st.session_state:

        st.write("")
        st.divider()
        st.markdown("**04 — Result**")
        st.markdown(
            '<div class="sc-muted" style="margin-bottom:0.8rem">Bandingkan cover dan stego. Perbedaan visual dirancang minimal.</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.image(
                st.session_state["encoded_cover"],
                caption="Cover Image",
                width="stretch",
            )

        with col2:
            st.image(
                st.session_state["encoded_stego"],
                caption="Stego Image",
                width="stretch",
            )

        st.info(
            "Stego image berisi pesan tersembunyi. Download dan kirim gambar ini kepada penerima."
        )

        # Use encode_file name if available, else fallback
        try:
            original_name = Path(encode_file.name).stem
        except Exception:
            original_name = "stegocrypt"

        output_filename = f"{original_name}_stego.png"

        st.download_button(
            label="⬇  Download Stego Image",
            data=st.session_state["encoded_bytes"],
            file_name=output_filename,
            mime="image/png",
            use_container_width=True,
        )


def render_decode():
    st.write("")
    st.markdown('<div class="sc-eyebrow">Decode</div>', unsafe_allow_html=True)
    st.markdown("#### Ekstrak Pesan")
    st.markdown(
        '<div class="sc-muted">Upload stego image yang berisi pesan, masukkan password yang sama, lalu ekstrak.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    with st.container(border=True):
        st.markdown("**01 — Stego Image**")
        st.markdown(
            '<div class="sc-caption" style="margin-bottom:0.7rem">Upload PNG atau BMP yang berisi pesan tersembunyi.</div>',
            unsafe_allow_html=True,
        )
        decode_file = st.file_uploader(
            "Upload stego image",
            type=["png", "bmp"],
            key="decode_upload",
            help="Upload PNG atau BMP yang berisi pesan tersembunyi.",
            label_visibility="collapsed",
        )

        stego_image = None

        if decode_file is not None:

            try:
                stego_image = Image.open(decode_file)

                if stego_image.mode not in {"RGB", "RGBA"}:
                    stego_image = stego_image.convert("RGB")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Width", f"{stego_image.width}px")
                with col2:
                    st.metric("Height", f"{stego_image.height}px")

                st.image(stego_image, caption="Received Stego Image", width="stretch")

            except Exception as error:
                st.error(f"Gagal memuat gambar: {error}")
        else:
            st.markdown(
                '<div class="sc-caption">Belum ada gambar. Upload stego image untuk melanjutkan.</div>',
                unsafe_allow_html=True,
            )

    st.write("")

    with st.container(border=True):
        st.markdown("**02 — Stego-Key / Password**")
        decode_password = st.text_input(
            "Password",
            type="password",
            placeholder="Masukkan password pengirim...",
            key="decode_password",
        )
        st.markdown(
            '<div class="sc-caption">Harus sama dengan password yang digunakan saat encoding.</div>',
            unsafe_allow_html=True,
        )

    st.write("")

    decode_button = st.button(
        "Decode Message →",
        type="primary",
        use_container_width=True,
        key="decode_button",
    )

    if decode_button:

        if stego_image is None:
            st.warning("Silakan upload stego image terlebih dahulu.")

        elif not decode_password:
            st.warning("Silakan masukkan stego-key/password.")

        else:

            try:
                decode_capacity = calculate_capacity(stego_image)

                # Temporary sequential positions.
                #
                # Nanti akan diganti dengan PRNG
                # berdasarkan stego-key.

                positions = list(range((decode_capacity + HEADER_SIZE) * 8))

                extracted_payload = extract_payload(stego_image, positions)

                # Temporary:
                # payload masih plaintext UTF-8.
                #
                # Nanti:
                #
                # ciphertext
                #     ↓
                # AES decrypt
                #     ↓
                # plaintext message

                decoded_message = extracted_payload.decode("utf-8")

                st.session_state["decoded_message"] = decoded_message

                st.success("Pesan berhasil diekstrak!")

            except UnicodeDecodeError:
                st.error(
                    "Payload tidak dapat dibaca. Password atau stego-key mungkin salah."
                )

            except Exception as error:
                st.error(f"Decoding gagal: {error}")

    if "decoded_message" in st.session_state:

        st.write("")
        st.divider()
        st.markdown("**03 — Extracted Message**")

        st.text_area(
            "Secret Message",
            value=st.session_state["decoded_message"],
            height=160,
            disabled=True,
        )

        st.success("Pesan tersembunyi berhasil diekstrak dari stego image.")
