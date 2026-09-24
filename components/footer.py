import streamlit as st


def render_footer():
    st.markdown(
        """
        <style>
            .site-footer {
                margin-top: 4.5rem;
                padding: 2.2rem 0 1.2rem 0;
                border-top: 1px solid rgba(128,128,128,0.13);
            }
            .footer-content {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 2rem;
                padding-bottom: 1.6rem;
            }
            .footer-brand { max-width: 420px; }
            .footer-logo {
                display: flex; align-items: center; gap: 0.55rem;
                font-size: 0.98rem;
                font-weight: 750;
                letter-spacing: -0.03em;
                margin-bottom: 0.45rem;
            }
            .footer-mark {
                width: 28px; height: 28px;
                display: flex; align-items: center; justify-content: center;
                border: 1px solid rgba(128,128,128,0.14);
                border-radius: 7px;
                font-size: 0.9rem;
                background: rgba(128,128,128,0.04);
            }
            .footer-brand p {
                margin: 0;
                font-size: 0.86rem;
                line-height: 1.65;
                opacity: 0.58;
            }
            .footer-info {
                display: flex; align-items: center; gap: 0.55rem;
                font-size: 0.82rem; opacity: 0.52;
                white-space: nowrap;
            }
            .footer-bottom {
                display: flex; align-items: center; justify-content: space-between;
                gap: 1rem;
                padding-top: 1.1rem;
                border-top: 1px solid rgba(128,128,128,0.08);
                font-size: 0.78rem;
                opacity: 0.48;
            }
            @media (max-width: 768px) {
                .footer-content { flex-direction: column; gap: 1rem; }
                .footer-bottom { flex-direction: column; align-items: flex-start; }
                .footer-info { flex-wrap: wrap; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <footer class="site-footer">
            <div class="footer-content">
                <div class="footer-brand">
                    <div class="footer-logo">
                        <span class="footer-mark">🔐</span>
                        StegoCrypt
                    </div>
                    <p>Aplikasi steganografi untuk menyembunyikan pesan rahasia di dalam gambar — LSB · AES · PRNG.</p>
                </div>
                <div class="footer-info">
                    <span>Steganography</span>
                    <span>•</span>
                    <span>Informatika</span>
                    <span>•</span>
                    <span>2026</span>
                </div>
            </div>
            <div class="footer-bottom">
                <span>© 2026 StegoCrypt. All rights reserved.</span>
                <span>Built with Python & Streamlit</span>
            </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )