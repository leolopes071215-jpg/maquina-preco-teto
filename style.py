import streamlit as st


def aplicar_estilo():
    st.markdown(
        """
        <style>
        /* =========================
           DESIGN SYSTEM PREMIUM
           Máquina de Preço-Teto
           ========================= */

        :root {
            --bg-main: #050816;
            --bg-panel: rgba(15, 23, 42, 0.82);
            --bg-panel-soft: rgba(30, 41, 59, 0.58);
            --border-soft: rgba(148, 163, 184, 0.18);
            --border-strong: rgba(148, 163, 184, 0.30);

            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --text-soft: #94a3b8;

            --blue: #2563eb;
            --blue-soft: #60a5fa;
            --green: #10b981;
            --amber: #f59e0b;
            --red: #ef4444;
            --gold: #d4af37;

            --radius-lg: 22px;
            --radius-md: 16px;
            --shadow-card: 0 22px 55px rgba(0, 0, 0, 0.32);
            --shadow-soft: 0 14px 35px rgba(0, 0, 0, 0.22);
        }

        /* =========================
           Fundo geral
           ========================= */

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.20) 0, transparent 34%),
                radial-gradient(circle at top right, rgba(16, 185, 129, 0.10) 0, transparent 28%),
                linear-gradient(135deg, #020617 0%, #0f172a 48%, #111827 100%);
            color: var(--text-main);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* =========================
           Tipografia
           ========================= */

        html, body, [class*="css"] {
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }

        h1 {
            color: var(--text-main) !important;
            font-size: clamp(2.2rem, 5vw, 4.4rem) !important;
            font-weight: 850 !important;
            letter-spacing: -0.065em !important;
            line-height: 0.96 !important;
            margin-bottom: 0.75rem !important;
        }

        h2, h3, h4 {
            color: var(--text-main) !important;
            font-weight: 780 !important;
            letter-spacing: -0.035em !important;
        }

        h3 {
            color: #e5e7eb !important;
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

        a:hover {
            color: #bfdbfe !important;
            text-decoration: underline;
        }

        /* =========================
           Sidebar
           ========================= */

        section[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at top, rgba(37, 99, 235, 0.16) 0, transparent 32%),
                linear-gradient(180deg, #020617 0%, #0f172a 60%, #111827 100%);
            border-right: 1px solid var(--border-soft);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.25rem;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: var(--text-main) !important;
        }

        section[data-testid="stSidebar"] .stCaptionContainer p {
            color: var(--text-soft) !important;
        }

        /* =========================
           Cards de métricas
           ========================= */

        div[data-testid="stMetric"] {
            background:
                linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(30, 41, 59, 0.72));
            border: 1px solid var(--border-soft);
            border-radius: var(--radius-lg);
            padding: 1.15rem 1.25rem;
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(16px);
            position: relative;
            overflow: hidden;
        }

        div[data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(96, 165, 250, 0.10), transparent 45%),
                radial-gradient(circle at top right, rgba(212, 175, 55, 0.11), transparent 35%);
            pointer-events: none;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--text-soft) !important;
            font-size: 0.86rem !important;
            font-weight: 650 !important;
            letter-spacing: 0.01em;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text-main) !important;
            font-size: clamp(1.25rem, 2vw, 1.72rem) !important;
            font-weight: 850 !important;
            letter-spacing: -0.045em !important;
        }

        div[data-testid="stMetricDelta"] {
            font-weight: 760 !important;
        }

        /* =========================
           Alertas / caixas informativas
           ========================= */

        div[data-testid="stAlert"] {
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.74)) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-main) !important;
            box-shadow: 0 14px 34px rgba(0, 0, 0, 0.18);
        }

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div {
            color: var(--text-muted) !important;
        }

        /* =========================
           Abas
           ========================= */

        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid var(--border-soft);
            border-radius: 999px;
            color: var(--text-muted);
            padding: 0.55rem 1rem;
            margin-right: 0.35rem;
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

        /* =========================
           Inputs, selects e text areas
           ========================= */

        input, textarea {
            background: rgba(15, 23, 42, 0.92) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--border-soft) !important;
            border-radius: 14px !important;
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
            border-radius: 14px !important;
        }

        div[data-baseweb="popover"] {
            background: #0f172a !important;
            color: var(--text-main) !important;
        }

        label {
            color: var(--text-muted) !important;
            font-weight: 650 !important;
        }

        /* Number input buttons */
        button[title="Increment"],
        button[title="Decrement"] {
            background: rgba(30, 41, 59, 0.8) !important;
            border-color: var(--border-soft) !important;
        }

        /* =========================
           Sliders
           ========================= */

        div[data-testid="stSlider"] {
            color: var(--text-main);
        }

        div[data-testid="stSlider"] label {
            color: var(--text-muted) !important;
        }

        /* =========================
           Botões
           ========================= */

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 999px !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            background:
                linear-gradient(135deg, #2563eb 0%, #1d4ed8 55%, #1e40af 100%) !important;
            color: white !important;
            padding: 0.68rem 1.10rem !important;
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

        .stButton > button:active,
        .stDownloadButton > button:active {
            transform: translateY(0px);
        }

        /* =========================
           Dataframes e tabelas
           ========================= */

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

        /* =========================
           Separadores
           ========================= */

        hr {
            border: none;
            border-top: 1px solid rgba(148, 163, 184, 0.16);
            margin-top: 2rem;
            margin-bottom: 2rem;
        }

        /* =========================
           Scrollbar
           ========================= */

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

        /* =========================
           Ajustes mobile
           ========================= */

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            h1 {
                font-size: 2.35rem !important;
            }

            div[data-testid="stMetric"] {
                padding: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )