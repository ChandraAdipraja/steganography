import io

import streamlit as st
from PIL import Image
from pathlib import Path

from src.steganography import (
    CapacityError,
    InvalidImageError,
    calculate_capacity,
    embed_payload,
    extract_payload,
)


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="Steganography App",
    page_icon="🔐",
    layout="wide",
)


# ============================================================
# Custom CSS
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #777;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1rem;
            margin-bottom: 0.7rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Header
# ============================================================

st.markdown(
    '<div class="main-title">🔐 Steganography App</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Secure message communication through images"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# Tabs
# ============================================================

encode_tab, decode_tab = st.tabs(
    [
        "🔐 Encode",
        "📥 Decode",
    ]
)


# ============================================================
# ENCODE TAB
# ============================================================

with encode_tab:

    st.header("Encode Message")

    st.write(
        "Hide a secret message inside a PNG or BMP image."
    )

    st.divider()

    # --------------------------------------------------------
    # Upload Cover Image
    # --------------------------------------------------------

    st.subheader("1. Cover Image")

    encode_file = st.file_uploader(
        "Upload the image you want to use as the cover",
        type=["png", "bmp"],
        key="encode_upload",
        help="Supported formats: PNG and BMP.",
    )

    cover_image = None
    capacity = None

    if encode_file is not None:

        try:
            cover_image = Image.open(encode_file)

            if cover_image.mode not in {"RGB", "RGBA"}:
                cover_image = cover_image.convert("RGB")

            capacity = calculate_capacity(
                cover_image
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Width",
                    f"{cover_image.width}px",
                )

            with col2:
                st.metric(
                    "Height",
                    f"{cover_image.height}px",
                )

            with col3:
                st.metric(
                    "Maximum Payload",
                    f"{capacity:,} bytes",
                )

            st.image(
                cover_image,
                caption="Cover Image",
                width="stretch",
            )

        except Exception as error:

            st.error(
                f"Failed to load image: {error}"
            )

    st.divider()

    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    st.subheader("2. Encryption Password")

    encode_password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter encryption password...",
        key="encode_password",
    )

    st.caption(
        "The password will be used for encryption and "
        "stego-key generation in the final version."
    )

    # --------------------------------------------------------
    # Message
    # --------------------------------------------------------

    st.subheader("3. Secret Message")

    encode_message = st.text_area(
        "Message",
        placeholder=(
            "Write the secret message you want to hide..."
        ),
        height=180,
        key="encode_message",
    )

    if encode_message:

        message_size = len(
            encode_message.encode("utf-8")
        )

        st.caption(
            f"Message size: {message_size:,} bytes"
        )

        if capacity is not None:

            if message_size > capacity:

                st.error(
                    "Message is too large for this image."
                )

            else:

                st.success(
                    "Message fits within the image capacity."
                )

    st.divider()

    # --------------------------------------------------------
    # Encode Button
    # --------------------------------------------------------

    encode_button = st.button(
        "🔐 Encode Message",
        type="primary",
        use_container_width=True,
    )

    if encode_button:

        if cover_image is None:

            st.warning(
                "Please upload a cover image first."
            )

        elif not encode_password:

            st.warning(
                "Please enter an encryption password."
            )

        elif not encode_message:

            st.warning(
                "Please enter a secret message."
            )

        else:

            try:

                # ------------------------------------------------
                # TEMPORARY IMPLEMENTATION
                #
                # AES encryption will be added later.
                # PRNG positions will also be added later.
                # ------------------------------------------------

                payload = encode_message.encode(
                    "utf-8"
                )

                positions = list(
                    range(
                        (capacity + 8) * 8
                    )
                )

                stego_image = embed_payload(
                    cover_image,
                    payload,
                    positions,
                )

                # ------------------------------------------------
                # Store image in memory
                # ------------------------------------------------

                output = io.BytesIO()

                stego_image.save(
                    output,
                    format="PNG",
                )

                output.seek(0)

                st.session_state[
                    "encoded_cover"
                ] = cover_image

                st.session_state[
                    "encoded_stego"
                ] = stego_image

                st.session_state[
                    "encoded_bytes"
                ] = output.getvalue()

                st.session_state[
                    "encoded_positions"
                ] = positions

                st.success(
                    "Message successfully encoded!"
                )

            except CapacityError:

                st.error(
                    "The message is too large "
                    "for this image."
                )

            except InvalidImageError as error:

                st.error(str(error))

            except Exception as error:

                st.error(
                    f"Encoding failed: {error}"
                )

    # --------------------------------------------------------
    # Encode Result
    # --------------------------------------------------------

    if "encoded_stego" in st.session_state:

        st.divider()

        st.subheader("4. Result")

        col1, col2 = st.columns(2)

        with col1:

            st.image(
                st.session_state["encoded_cover"],
                caption="Original / Cover Image",
                width="stretch",
            )

        with col2:

            st.image(
                st.session_state["encoded_stego"],
                caption="Stego Image",
                width="stretch",
            )

        st.info(
            "The stego image contains the hidden message. "
            "Download this image and send it to the receiver."
        )

        original_name = Path(
            encode_file.name
        ).stem

        output_filename = f"{original_name}_stego.png"

        st.download_button(
            label="⬇️ Download Stego Image",
            data=st.session_state[
                "encoded_bytes"
            ],
            file_name=output_filename,
            mime="image/png",
            use_container_width=True,
        )

# ============================================================
# DECODE TAB
# ============================================================

with decode_tab:

    st.header("Decode Message")

    st.write(
        "Extract a hidden message from a stego image."
    )

    st.divider()

    # --------------------------------------------------------
    # Upload Stego Image
    # --------------------------------------------------------

    st.subheader("1. Received Stego Image")

    decode_file = st.file_uploader(
        "Upload the stego image you received",
        type=["png", "bmp"],
        key="decode_upload",
        help="Upload the PNG or BMP containing the hidden message.",
    )

    stego_image = None

    if decode_file is not None:

        try:

            stego_image = Image.open(
                decode_file
            )

            if stego_image.mode not in {
                "RGB",
                "RGBA",
            }:

                stego_image = stego_image.convert(
                    "RGB"
                )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Width",
                    f"{stego_image.width}px",
                )

            with col2:

                st.metric(
                    "Height",
                    f"{stego_image.height}px",
                )

            st.image(
                stego_image,
                caption="Received Stego Image",
                width="stretch",
            )

        except Exception as error:

            st.error(
                f"Failed to load stego image: {error}"
            )

    st.divider()

    # --------------------------------------------------------
    # Password
    # --------------------------------------------------------

    st.subheader("2. Stego-Key / Password")

    decode_password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter the password used by the sender...",
        key="decode_password",
    )

    st.caption(
        "The password must match the password used "
        "during encoding."
    )

    st.divider()

    # --------------------------------------------------------
    # Decode Button
    # --------------------------------------------------------

    decode_button = st.button(
        "📥 Decode Message",
        type="primary",
        use_container_width=True,
    )

    if decode_button:

        if stego_image is None:

            st.warning(
                "Please upload a stego image first."
            )

        elif not decode_password:

            st.warning(
                "Please enter the stego-key/password."
            )

        else:

            try:

                # ------------------------------------------------
                # TEMPORARY IMPLEMENTATION
                #
                # The final version will generate these positions
                # using the PRNG and stego-key.
                # ------------------------------------------------

                decode_capacity = calculate_capacity(
                    stego_image
                )

                positions = list(
                    range(
                        (decode_capacity + 8) * 8
                    )
                )

                extracted_payload = extract_payload(
                    stego_image,
                    positions,
                )

                # ------------------------------------------------
                # TEMPORARY:
                # Payload is currently plaintext bytes.
                #
                # Later:
                # extracted_payload
                #       ↓
                # AES Decryption
                #       ↓
                # plaintext message
                # ------------------------------------------------

                decoded_message = (
                    extracted_payload.decode(
                        "utf-8"
                    )
                )

                st.session_state[
                    "decoded_message"
                ] = decoded_message

                st.success(
                    "Message successfully extracted!"
                )

            except UnicodeDecodeError:

                st.error(
                    "Unable to decode the extracted "
                    "message. The password may be incorrect."
                )

            except Exception as error:

                st.error(
                    f"Decoding failed: {error}"
                )

    # --------------------------------------------------------
    # Decode Result
    # --------------------------------------------------------

    if "decoded_message" in st.session_state:

        st.divider()

        st.subheader("3. Extracted Message")

        st.text_area(
            "Secret Message",
            value=st.session_state[
                "decoded_message"
            ],
            height=180,
            disabled=True,
        )

        st.success(
            "The hidden message has been extracted "
            "from the stego image."
        )