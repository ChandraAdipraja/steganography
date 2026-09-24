import streamlit as st

from components.navbar import render_navbar
from components.home import render_home
from components.about import render_about
from components.encoder import render_encoder
from components.footer import render_footer


st.set_page_config(
    page_title="StegoCrypt",
    page_icon="🔐",
    layout="wide",
)


# =========================
# GLOBAL STYLE — StegoCrypt premium minimal
# =========================

st.markdown(
    """
    <style>
        /* Layout */
        .block-container {
            max-width: 1120px;
            padding-top: 1.6rem;
            padding-bottom: 0;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
        }

        /* Base typography - respect Streamlit theme */
        html, body, [class*="st-"] {
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        h1, h2, h3, h4 {
            letter-spacing: -0.03em;
            line-height: 1.15;
        }

        p, li {
            line-height: 1.7;
        }

        /* Eyebrow / label */
        .sc-eyebrow {
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            opacity: 0.55;
            margin-bottom: 0.9rem;
        }

        .sc-muted {
            opacity: 0.68;
            font-size: 0.95rem;
            line-height: 1.7;
        }

        .sc-caption {
            font-size: 0.82rem;
            opacity: 0.55;
            letter-spacing: 0.02em;
        }

        /* Cards */
        .sc-card {
            border: 1px solid rgba(128, 128, 128, 0.16);
            border-radius: 14px;
            padding: 1.35rem 1.3rem;
            background: transparent;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.92rem;
            min-height: 2.7rem;
            letter-spacing: -0.01em;
            border: 1px solid rgba(128,128,128,0.18);
            transition: all 0.16s ease;
        }

        .stButton > button[kind="primary"] {
            border-color: transparent;
            box-shadow: 0 1px 2px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.06);
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(128,128,128,0.28);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea {
            border-radius: 10px;
            border: 1px solid rgba(128,128,128,0.18) !important;
            font-size: 0.94rem;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: rgba(128,128,128,0.32) !important;
            box-shadow: 0 0 0 3px rgba(128,128,128,0.08) !important;
        }

        [data-testid="stFileUploader"] {
            border-radius: 12px;
            border: 1px dashed rgba(128,128,128,0.22);
            padding: 0.6rem;
            background: rgba(128,128,128,0.03);
        }

        [data-testid="stFileUploader"]:hover {
            border-color: rgba(128,128,128,0.32);
            background: rgba(128,128,128,0.05);
        }

        /* Metrics - keep theme friendly */
        [data-testid="stMetric"] {
            padding: 1rem 1.1rem;
            border: 1px solid rgba(128, 128, 128, 0.14);
            border-radius: 12px;
            background: rgba(128,128,128,0.03);
        }

        [data-testid="stMetric"] label {
            opacity: 0.6;
            font-size: 0.78rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            font-weight: 600;
        }

        /* Tabs */
        [data-testid="stTabs"] button {
            font-weight: 600;
            font-size: 0.92rem;
            letter-spacing: -0.01em;
        }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: rgba(128,128,128,0.55) !important;
        }

        /* Divider */
        hr {
            border: none;
            border-top: 1px solid rgba(128,128,128,0.13);
            margin: 1.8rem 0;
        }

        /* Images */
        [data-testid="stImage"] img {
            border-radius: 12px;
            border: 1px solid rgba(128,128,128,0.13);
        }

        /* Alerts - more subtle */
        [data-testid="stAlert"] {
            border-radius: 10px;
            border-left-width: 3px;
            font-size: 0.92rem;
        }

        /* Reduce motion */
        @media (prefers-reduced-motion: reduce) {
            .stButton > button { transition: none; }
        }

        /* Mobile */
        @media (max-width: 640px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# NAVBAR
# =========================

render_navbar()


# =========================
# NAVIGATION
# =========================

navigation = st.session_state.get(
    "navigation",
    "home",
)


# =========================
# HOME + ABOUT
# =========================

if navigation == "home":

    render_home()

    render_about()

    render_footer()


# =========================
# ENCODE / DECODE
# =========================

elif navigation == "encoder":

    render_encoder()

    render_footer()