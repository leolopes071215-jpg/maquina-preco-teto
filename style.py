import streamlit as st


# VALORIS
# v3.8.38 — Estilo premium mobile-first


def aplicar_estilo():
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #050816;
            --bg-panel: rgba(15, 23, 42, 0.86);
            --bg-panel-soft: rgba(30, 41, 59, 0.62);
            --border-soft: rgba(148, 163, 184, 0.18);
            --border-strong: rgba(148, 163, 184, 0.34);

            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --text-soft: #94a3b8;

            --blue: #2563eb;
            --blue-soft: #60a5fa;
            --green: #10b981;
            --amber: #f59e0b;
            --red: #ef4444;
            --gold: #d4af37;

            --radius-lg: 20px;
            --radius-md: 14px;
            --shadow-card: 0 20px 48px rgba(0, 0, 0, 0.28);
            --shadow-soft: 0 12px 28px rgba(0, 0, 0, 0.20);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.18) 0, transparent 32%),
                radial-gradient(circle at top right, rgba(16, 185, 129, 0.08) 0, transparent 28%),
                linear-gradient(135deg, #020617 0%, #0f172a 48%, #111827 100%);
            color: var(--text-main);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.25rem;
            padding-bottom: 4rem;
        }

        html, body, [class*="css"] {
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }

        h1 {
            color: var(--text-main) !important;
            font-size: clamp(2rem, 4vw, 3.3rem) !important;
            font-weight: 850 !important;
            letter-spacing: -0.055em !important;
            line-height: 1.02 !important;
            margin-bottom: 0.45rem !important;
        }

        h2, h3, h4 {
            color: var(--text-main) !important;
            font-weight: 780 !important;
            letter-spacing: -0.03em !important;
        }

        p, li, label, span {
            color: var(--text-muted);
        }

        strong {
            color: var(--text-main);
            font-weight: 750;
        }

        a {
            color: #93c5fd !important;
            text-decoration: none;
        }

        section[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at top, rgba(37, 99, 235, 0.14) 0, transparent 30%),
                linear-gradient(180deg, #020617 0%, #0f172a 60%, #111827 100%);
            border-right: 1px solid var(--border-soft);
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: var(--text-main) !important;
        }

        section[data-testid="stSidebar"] .stCaptionContainer p {
            color: var(--text-soft) !important;
        }

        div[data-testid="stMetric"] {
            background:
                linear-gradient(145deg, rgba(15, 23, 42, 0.96), rgba(30, 41, 59, 0.72));
            border: 1px solid var(--border-soft);
            border-radius: var(--radius-lg);
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(14px);
            position: relative;
            overflow: hidden;
        }

        div[data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(96, 165, 250, 0.08), transparent 48%),
                radial-gradient(circle at top right, rgba(212, 175, 55, 0.09), transparent 35%);
            pointer-events: none;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--text-soft) !important;
            font-size: 0.78rem !important;
            font-weight: 650 !important;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text-main) !important;
            font-size: clamp(1.10rem, 1.8vw, 1.55rem) !important;
            font-weight: 850 !important;
            letter-spacing: -0.04em !important;
        }

        div[data-testid="stMetricDelta"] {
            font-weight: 760 !important;
        }

        div[data-testid="stAlert"] {
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.74)) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-main) !important;
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.16);
        }

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div {
            color: var(--text-muted) !important;
        }

        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid var(--border-soft);
            border-radius: 999px;
            color: var(--text-muted);
            padding: 0.48rem 0.85rem;
            margin-right: 0.30rem;
            transition: all 0.18s ease-in-out;
        }

        div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
            background: rgba(30, 41, 59, 0.92);
            color: var(--text-main);
            border-color: var(--border-strong);
        }

        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.30);
        }

        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {
            color: white !important;
            font-weight: 750;
        }

        input, textarea {
            background: rgba(15, 23, 42, 0.92) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 13px !important;
            box-shadow: none !important;
        }

        input:focus, textarea:focus {
            border: 1px solid rgba(96, 165, 250, 0.72) !important;
            box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.14) !important;
        }

        div[data-baseweb="select"] > div {
            background: rgba(15, 23, 42, 0.92) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 13px !important;
        }

        div[data-baseweb="popover"] {
            background: #0f172a !important;
            color: var(--text-main) !important;
        }

        label {
            color: var(--text-muted) !important;
            font-weight: 650 !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 999px !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            background:
                linear-gradient(135deg, #2563eb 0%, #1d4ed8 55%, #1e40af 100%) !important;
            color: white !important;
            padding: 0.62rem 1.05rem !important;
            font-weight: 780 !important;
            letter-spacing: -0.015em;
            box-shadow: 0 14px 32px rgba(37, 99, 235, 0.30);
            transition: transform 0.16s ease-in-out, box-shadow 0.16s ease-in-out;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 42px rgba(37, 99, 235, 0.42);
            border-color: rgba(255, 255, 255, 0.28) !important;
        }

        div[data-testid="stDataFrame"] {
            border-radius: var(--radius-lg);
            overflow: hidden;
            border: 1px solid var(--border-soft);
            box-shadow: var(--shadow-card);
            background: rgba(15, 23, 42, 0.84);
        }

        table {
            border-radius: var(--radius-lg);
            overflow: hidden;
            background: rgba(15, 23, 42, 0.85);
            color: var(--text-main);
        }

        thead tr th {
            background: rgba(30, 41, 59, 0.94) !important;
            color: var(--text-main) !important;
            font-weight: 800 !important;
        }

        tbody tr td {
            color: var(--text-muted) !important;
            border-color: rgba(148, 163, 184, 0.10) !important;
        }

        tbody tr:hover td {
            background: rgba(37, 99, 235, 0.08) !important;
            color: var(--text-main) !important;
        }

        hr {
            border: none;
            border-top: 1px solid rgba(148, 163, 184, 0.16);
            margin-top: 1.6rem;
            margin-bottom: 1.6rem;
        }

        div[data-testid="stProgress"] > div {
            background-color: rgba(15, 23, 42, 0.92) !important;
            border-radius: 999px !important;
            border: 1px solid rgba(148, 163, 184, 0.16);
        }

        div[data-testid="stProgress"] div[role="progressbar"] {
            background: linear-gradient(90deg, #2563eb, #60a5fa) !important;
            border-radius: 999px !important;
        }

        pre, code {
            background: rgba(2, 6, 23, 0.88) !important;
            color: #e5e7eb !important;
            border-radius: 12px !important;
            border: 1px solid rgba(148, 163, 184, 0.16);
        }

        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: #020617;
        }

        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 999px;
            border: 2px solid #020617;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            h1 {
                font-size: 2.15rem !important;
            }

            div[data-testid="stMetric"] {
                padding: 0.95rem;
            }
        }
        

        /* =====================================================
           VALORIS v3.8.38 — Mobile-first premium refinements
           ===================================================== */

        div[data-testid="stVerticalBlock"] {
            gap: 0.85rem;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.95rem;
        }

        .stMarkdown {
            overflow-wrap: anywhere;
        }

        button[kind="secondary"],
        button[kind="primary"] {
            min-height: 2.55rem;
        }

        div[data-testid="stRadio"] > div {
            gap: 0.45rem;
        }

        div[data-testid="stRadio"] label {
            background: rgba(15, 23, 42, 0.70);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 999px;
            padding: 0.35rem 0.65rem;
            transition: all 0.18s ease-in-out;
        }

        div[data-testid="stRadio"] label:hover {
            background: rgba(30, 41, 59, 0.92);
            border-color: rgba(148, 163, 184, 0.32);
        }

        details {
            border-radius: 18px !important;
            border: 1px solid rgba(148, 163, 184, 0.14) !important;
            background: rgba(15, 23, 42, 0.58) !important;
        }

        details summary {
            color: var(--text-main) !important;
            font-weight: 780 !important;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-top: 0.85rem;
                padding-left: 0.82rem;
                padding-right: 0.82rem;
                padding-bottom: 2.6rem;
            }

            h1 {
                font-size: 2rem !important;
                letter-spacing: -0.05em !important;
            }

            h2 {
                font-size: 1.42rem !important;
            }

            h3 {
                font-size: 1.16rem !important;
            }

            p, li, label, span {
                font-size: 0.94rem;
                line-height: 1.48;
            }

            div[data-testid="stMetric"] {
                border-radius: 16px;
                padding: 0.82rem 0.86rem;
                box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.12rem !important;
            }

            div[data-testid="stAlert"] {
                border-radius: 15px !important;
            }

            .stButton > button,
            .stDownloadButton > button {
                width: 100%;
                min-height: 2.8rem;
            }

            div[data-testid="stTabs"] button[data-baseweb="tab"] {
                padding: 0.42rem 0.62rem;
                margin-right: 0.15rem;
                font-size: 0.84rem;
            }

            section[data-testid="stSidebar"] {
                border-right: none;
            }
        }

        @media (max-width: 520px) {
            .block-container {
                padding-left: 0.72rem;
                padding-right: 0.72rem;
            }

            h1 {
                font-size: 1.82rem !important;
            }

            h2 {
                font-size: 1.30rem !important;
            }

            h3 {
                font-size: 1.08rem !important;
            }

            div[data-testid="stMetric"] {
                margin-bottom: 0.35rem;
            }

            div[data-testid="stRadio"] > div {
                flex-direction: column;
                align-items: stretch;
            }

            div[data-testid="stRadio"] label {
                width: 100%;
                justify-content: center;
                border-radius: 16px;
                padding: 0.55rem 0.70rem;
            }

            hr {
                margin-top: 1rem;
                margin-bottom: 1rem;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )