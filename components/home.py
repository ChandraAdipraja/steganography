import streamlit as st


def render_home():

    st.markdown(
        """
        <style>
        .sc-hero {
            text-align: center;
            max-width: 740px;
            margin: 0 auto;
            padding: 2.8rem 0 1.2rem 0;
        }
        .sc-hero-label {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            opacity: 0.52;
            margin-bottom: 1.1rem;
        }
        .sc-hero-label::before,
        .sc-hero-label::after {
            content: "";
            width: 22px;
            height: 1px;
            background: rgba(128,128,128,0.28);
        }
        .sc-hero h1 {
            font-size: clamp(2.0rem, 4.6vw, 3.35rem);
            font-weight: 800;
            letter-spacing: -0.05em;
            line-height: 0.98;
            margin: 0 0 1rem 0;
        }
        .sc-hero h1 em {
            font-style: normal;
            font-weight: 800;
            opacity: 0.38;
        }
        .sc-hero-desc {
            font-size: 1.02rem;
            line-height: 1.75;
            opacity: 0.66;
            max-width: 560px;
            margin: 0 auto;
        }
        .sc-hero-cta {
            margin: 1.7rem auto 0 auto;
            max-width: 220px;
        }
        .sc-hero-meta {
            margin-top: 1.5rem;
            font-size: 0.74rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            opacity: 0.42;
            font-weight: 600;
        }
        .sc-hero-divider {
            margin: 2.2rem auto 0 auto;
            width: 32px;
            height: 2px;
            background: rgba(128,128,128,0.18);
            border-radius: 999px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sc-hero">
            <div class="sc-hero-label">Secure Image Steganography</div>
            <h1>Sembunyikan Pesan Rahasia<br><em>Di Balik Sebuah Gambar.</em></h1>
            <div class="sc-hero-desc">
                StegoCrypt membantu Anda menyisipkan pesan rahasia ke dalam gambar
                menggunakan kombinasi <b>LSB</b>, enkripsi <b>AES</b>, dan
                pengacakan posisi <b>PRNG</b>  tanpa jejak visual.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 1.05, 1])
    with c2:
        if st.button(
            "Mulai Sekarang →",
            type="primary",
            use_container_width=True,
            key="home_cta",
        ):
            st.session_state["navigation"] = "encoder"
            st.rerun()

    st.markdown(
        '<div class="sc-hero" style="padding-top:0.2rem"><div class="sc-hero-meta">PNG · BMP · LSB · AES · PRNG</div><div class="sc-hero-divider"></div></div>',
        unsafe_allow_html=True,
    )