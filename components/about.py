import streamlit as st


def render_about():

    # =========================
    # ANCHOR + STYLE
    # =========================

    st.markdown('<div id="tentang"></div>', unsafe_allow_html=True)

    # Auto-scroll when navbar "Tentang" was clicked — no #tentang left in URL
    if st.session_state.get("scroll_to") == "tentang":
        st.html(
            """
            <script>
            (function(){
                const doc = document;
                const win = window;
                const target = doc.getElementById("tentang") || (window.parent && window.parent.document ? window.parent.document.getElementById("tentang") : null);
                if (target) target.scrollIntoView({behavior: "smooth", block: "start"});
                try {
                    const loc = win.location;
                    const pLoc = (window.parent && window.parent.location && window.parent.location.hash !== undefined) ? window.parent.location : loc;
                    const hist = (window.parent && window.parent.history) ? window.parent.history : win.history;
                    if (pLoc.hash === "#tentang") hist.replaceState(null, "", pLoc.pathname + pLoc.search);
                } catch(e) {}
            })();
            </script>
            """
        )
        # clear flag so it doesn't re-scroll on next rerun
        st.session_state["scroll_to"] = None

    # Also clean stray #tentang if user landed with old hash (no button press)
    st.html(
        """
        <script>
        (function(){
            try {
                const win = window;
                const loc = win.location;
                const pLoc = (window.parent && window.parent.location && window.parent.location.hash !== undefined) ? window.parent.location : loc;
                const hist = (window.parent && window.parent.history) ? window.parent.history : win.history;
                if (pLoc.hash === "#tentang") hist.replaceState(null, "", pLoc.pathname + pLoc.search);
            } catch(e) {}
        })();
        </script>
        """
    )

    st.markdown(
        """
        <style>
        .sc-section { padding: 2.4rem 0 0.6rem 0; }
        .sc-section-head { max-width: 640px; margin-bottom: 1.6rem; }
        .sc-section-head h2 { font-size: 1.7rem; font-weight: 780; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; }
        .sc-section-head p { margin: 0; opacity: 0.66; line-height: 1.7; font-size: 0.97rem; }
        .sc-tech-icon {
            width: 40px; height: 40px;
            display: flex; align-items: center; justify-content: center;
            border: 1px solid rgba(128,128,128,0.16);
            border-radius: 11px;
            background: rgba(128,128,128,0.04);
            font-size: 1.15rem;
            margin-bottom: 0.9rem;
        }
        .sc-step-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 34px; height: 34px;
            border: 1px solid rgba(128,128,128,0.16);
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            opacity: 0.7;
            margin-bottom: 0.7rem;
            background: rgba(128,128,128,0.04);
        }
        .sc-card-title {
            font-size: 1.04rem;
            font-weight: 730;
            letter-spacing: -0.025em;
            line-height: 1.3;
            margin: 0 0 0.5rem 0;
        }
        .sc-card-desc {
            font-size: 0.9rem;
            line-height: 1.66;
            opacity: 0.70;
            margin: 0;
        }
        .sc-card-caption {
            font-size: 0.71rem;
            font-weight: 650;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            opacity: 0.46;
            margin-top: 0.85rem;
        }
        .sc-step-title {
            font-size: 0.98rem;
            font-weight: 700;
            letter-spacing: -0.015em;
            margin: 0 0 0.35rem 0;
        }
        .sc-step-desc {
            font-size: 0.88rem;
            line-height: 1.6;
            opacity: 0.68;
            margin: 0;
        }
        .sc-security-label {
            font-size: 0.72rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.48;
            margin-bottom: 0.45rem;
        }
        .sc-security-title {
            font-size: 1.02rem;
            font-weight: 720;
            letter-spacing: -0.02em;
            margin: 0 0 0.45rem 0;
        }
        .sc-security-desc {
            font-size: 0.9rem;
            line-height: 1.66;
            opacity: 0.70;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # =========================
    # HEADER
    # =========================

    st.markdown(
        """
        <div class="sc-section">
            <div class="sc-eyebrow">Tentang StegoCrypt</div>
            <div class="sc-section-head">
                <h2>Keamanan pesan dalam sebuah gambar</h2>
                <p>
                    StegoCrypt menggabungkan penyisipan data pada citra, enkripsi, dan
                    pengacakan posisi data untuk menjaga kerahasiaan pesan — dirancang
                    agar tetap natural di mata, kuat di lapisan data.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =========================
    # TECHNOLOGY — 3 cards
    # =========================

    st.markdown(
        '<div class="sc-eyebrow" style="margin-bottom:1rem">Teknologi Utama</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        with st.container(border=True):
            st.markdown('<div class="sc-tech-icon">◧</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-title">LSB Steganografi</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-desc">Pesan disisipkan ke bit paling rendah piksel. Perubahan dirancang agar tetap sulit terlihat secara visual.</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-caption">Least Significant Bit</div>', unsafe_allow_html=True)

    with col2:
        with st.container(border=True):
            st.markdown('<div class="sc-tech-icon">⬢</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-title">Enkripsi AES</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-desc">Pesan dienkripsi dulu sebelum disisipkan — data yang tertanam bukan lagi pesan asli.</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-caption">Advanced Encryption Standard</div>', unsafe_allow_html=True)

    with col3:
        with st.container(border=True):
            st.markdown('<div class="sc-tech-icon">⬣</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-title">PRNG &amp; Stego-Key</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-desc">Posisi penyisipan diacak pseudo-random dari stego-key, tidak berurutan dan tidak mudah ditebak.</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-card-caption">Pseudo-Random Number Generator</div>', unsafe_allow_html=True)

    st.write("")
    st.divider()

    # =========================
    # PROCESS — 4 steps
    # =========================

    st.markdown(
        """
        <div class="sc-section" style="padding-top:0.6rem">
            <div class="sc-eyebrow">Cara Kerja</div>
            <div class="sc-section-head">
                <h2>Bagaimana StegoCrypt bekerja?</h2>
                <p>Empat tahap berurutan — dari pesan hingga stego image yang siap dibagikan.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    step1, step2, step3, step4 = st.columns(4, gap="medium")

    with step1:
        with st.container(border=True):
            st.markdown('<div class="sc-step-num">01</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-title">Pesan</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-desc">Anda menulis pesan rahasia yang ingin disembunyikan.</div>', unsafe_allow_html=True)

    with step2:
        with st.container(border=True):
            st.markdown('<div class="sc-step-num">02</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-title">Enkripsi</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-desc">Pesan diubah menjadi ciphertext via AES.</div>', unsafe_allow_html=True)

    with step3:
        with st.container(border=True):
            st.markdown('<div class="sc-step-num">03</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-title">Randomisasi</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-desc">PRNG menentukan posisi piksel penyisipan.</div>', unsafe_allow_html=True)

    with step4:
        with st.container(border=True):
            st.markdown('<div class="sc-step-num">04</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-title">LSB Embedding</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-step-desc">Ciphertext ditanam ke bit LSB gambar.</div>', unsafe_allow_html=True)

    st.write("")
    st.divider()

    # =========================
    # SECURITY — 2 layers
    # =========================

    st.markdown(
        """
        <div class="sc-section" style="padding-top:0.6rem">
            <div class="sc-eyebrow">Dua Lapisan</div>
            <div class="sc-section-head">
                <h2>Mengapa beberapa lapisan?</h2>
                <p>Tidak hanya menyembunyikan keberadaan pesan, tapi juga melindungi isinya. Enkripsi + steganografi = dua proteksi yang berbeda.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    security_col1, security_col2 = st.columns(2, gap="medium")

    with security_col1:
        with st.container(border=True):
            st.markdown('<div class="sc-security-label">Lapisan 01</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-security-title">Kerahasiaan pesan</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-security-desc">Enkripsi membuat isi tidak dapat dibaca langsung bahkan jika ciphertext berhasil diambil.</div>', unsafe_allow_html=True)

    with security_col2:
        with st.container(border=True):
            st.markdown('<div class="sc-security-label">Lapisan 02</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-security-title">Penyembunyian pesan</div>', unsafe_allow_html=True)
            st.markdown('<div class="sc-security-desc">Steganografi menanam data di dalam gambar sehingga pesan tidak terlihat secara langsung.</div>', unsafe_allow_html=True)
