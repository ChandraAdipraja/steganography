import streamlit as st


def render_navbar():

    # =========================
    # NAVBAR STYLE — minimal premium
    # =========================

    st.markdown(
        """
        <style>
        .sc-navbar-wrap {
            padding: 0.2rem 0 0.9rem 0;
            margin-bottom: 0.2rem;
            border-bottom: 1px solid rgba(128,128,128,0.10);
        }
        .sc-brand {
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }
        .sc-brand-mark {
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 9px;
            font-size: 1.05rem;
            background: rgba(128,128,128,0.04);
            flex-shrink: 0;
        }
        .sc-brand-text { line-height: 1.1; }
        .sc-brand-name {
            font-size: 1.02rem;
            font-weight: 750;
            letter-spacing: -0.03em;
            margin: 0;
        }
        .sc-brand-sub {
            font-size: 0.78rem;
            opacity: 0.55;
            letter-spacing: 0.02em;
            margin-top: 2px;
        }
        /* mobile */
        .sc-mobile-bar {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .sc-mobile-menu {
            margin-top: 0.75rem;
            padding: 0.65rem;
            border: 1px solid rgba(128,128,128,0.14);
            border-radius: 12px;
            background: rgba(128,128,128,0.03);
        }
        /* hide/show logic — :has() targets the Streamlit horizontal block that contains our marker */
        @media (min-width: 769px) {
            div[data-testid="stHorizontalBlock"]:has(.sc-mobile-bar) {
                display: none !important;
            }
            div[data-testid="stVerticalBlock"]:has(.sc-mobile-menu) {
                display: none !important;
            }
        }
        @media (max-width: 768px) {
            div[data-testid="stHorizontalBlock"]:has(.sc-brand):not(:has(.sc-mobile-bar)) {
                display: none !important;
            }
            /* keep brand + hamburger on same row — prevent Streamlit columns stacking */
            div[data-testid="stHorizontalBlock"]:has(.sc-mobile-bar) {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: center !important;
                gap: 0.75rem;
            }
            div[data-testid="stHorizontalBlock"]:has(.sc-mobile-bar) > div[data-testid="stColumn"]:first-child {
                flex: 1 1 auto !important;
                min-width: 0 !important;
            }
            div[data-testid="stHorizontalBlock"]:has(.sc-mobile-bar) > div[data-testid="stColumn"]:last-child {
                flex: 0 0 52px !important;
                min-width: 52px !important;
                max-width: 52px !important;
            }
            .sc-brand-sub { display: none; }
        }
        @media (max-width: 640px) {
            .sc-brand-sub { display: none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # =========================
    # NAVBAR — desktop + mobile
    # =========================

    st.markdown('<div class="sc-navbar-wrap">', unsafe_allow_html=True)

    # --- DESKTOP (hidden on mobile via :has(.sc-brand)) ---
    col_brand, col_home, col_about, col_encoder = st.columns(
        [3.2, 1, 1, 1.35],
        vertical_alignment="center",
    )

    with col_brand:
        st.markdown(
            """
            <div class="sc-brand">
                <div class="sc-brand-mark">🔐</div>
                <div class="sc-brand-text">
                    <div class="sc-brand-name">StegoCrypt</div>
                    <div class="sc-brand-sub">Secure image steganography</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_home:
        if st.button("Beranda", use_container_width=True, key="nav_home"):
            st.session_state["navigation"] = "home"
            st.session_state["mobile_nav_open"] = False
            st.rerun()

    with col_about:
        if st.button("Tentang", use_container_width=True, key="nav_about"):
            st.session_state["navigation"] = "home"
            st.session_state["scroll_to"] = "tentang"
            st.session_state["mobile_nav_open"] = False
            st.rerun()

    with col_encoder:
        if st.button("Encode / Decode", use_container_width=True, key="nav_encoder"):
            st.session_state["navigation"] = "encoder"
            st.session_state["mobile_nav_open"] = False
            st.rerun()

    # --- MOBILE (hidden on desktop via :has(.sc-mobile-bar)) ---
    if "mobile_nav_open" not in st.session_state:
        st.session_state["mobile_nav_open"] = False

    m_brand, m_toggle = st.columns([4, 1], vertical_alignment="center")

    with m_brand:
        st.markdown(
            """
            <div class="sc-mobile-bar">
                <div class="sc-brand">
                    <div class="sc-brand-mark">🔐</div>
                    <div class="sc-brand-text">
                        <div class="sc-brand-name">StegoCrypt</div>
                        <div class="sc-brand-sub">Secure image steganography</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m_toggle:
        label = "✕" if st.session_state["mobile_nav_open"] else "☰"
        if st.button(label, use_container_width=True, key="nav_hamburger"):
            st.session_state["mobile_nav_open"] = not st.session_state["mobile_nav_open"]
            st.rerun()

    if st.session_state["mobile_nav_open"]:
        st.markdown('<div class="sc-mobile-menu">', unsafe_allow_html=True)
        if st.button("Beranda", use_container_width=True, key="m_nav_home"):
            st.session_state["navigation"] = "home"
            st.session_state["mobile_nav_open"] = False
            st.rerun()
        if st.button("Tentang", use_container_width=True, key="m_nav_about"):
            st.session_state["navigation"] = "home"
            st.session_state["scroll_to"] = "tentang"
            st.session_state["mobile_nav_open"] = False
            st.rerun()
        if st.button("Encode / Decode", use_container_width=True, key="m_nav_encoder"):
            st.session_state["navigation"] = "encoder"
            st.session_state["mobile_nav_open"] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # JS fallback for browsers without :has() — ensures hamburger only on mobile
    st.html(
        """
        <script>
        (function() {
            function applyNav() {
                try {
                    const win = window;
                    const pWin = (window.parent && window.parent.innerWidth !== undefined) ? window.parent : win;
                    const doc = (window.parent && window.parent.document && window.parent.document.querySelectorAll) ? window.parent.document : document;
                    const isMobile = pWin.innerWidth <= 768;
                    const hBlocks = doc.querySelectorAll('div[data-testid="stHorizontalBlock"]');
                    hBlocks.forEach(hb => {
                        const hasBrand = hb.querySelector('.sc-brand') && !hb.querySelector('.sc-mobile-bar');
                        const hasMobileBar = hb.querySelector('.sc-mobile-bar');
                        if (hasBrand) hb.style.display = isMobile ? 'none' : '';
                        if (hasMobileBar) {
                            hb.style.display = isMobile ? 'flex' : 'none';
                            if (isMobile) {
                                hb.style.flexDirection = 'row';
                                hb.style.flexWrap = 'nowrap';
                                hb.style.alignItems = 'center';
                            }
                        }
                    });
                    const menu = doc.querySelector('.sc-mobile-menu');
                    if (menu) {
                        const vb = menu.closest('div[data-testid="stVerticalBlock"]');
                        if (vb) vb.style.display = (pWin.innerWidth > 768) ? 'none' : '';
                    }
                } catch(e) {}
            }
            applyNav();
            try {
                const pWin = (window.parent && window.parent.addEventListener) ? window.parent : window;
                pWin.addEventListener('resize', applyNav);
            } catch(e) {}
            setTimeout(applyNav, 300);
            setTimeout(applyNav, 900);
        })();
        </script>
        """
    )

    st.markdown('</div>', unsafe_allow_html=True)