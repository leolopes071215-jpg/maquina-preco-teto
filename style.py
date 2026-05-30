import streamlit as st


def aplicar_estilo():
    st.markdown(
        """
        <style>
            .main {
                background-color: #f8fafc;
            }

            h1 {
                font-size: 42px !important;
                font-weight: 800 !important;
                color: #0f172a !important;
            }

            h2, h3 {
                color: #1e293b !important;
                font-weight: 700 !important;
            }

            [data-testid="stSidebar"] {
                background-color: #eef2f7;
                border-right: 1px solid #dbe3ec;
            }

            [data-testid="stMetric"] {
                background-color: #ffffff;
                padding: 18px;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
                box-shadow: 0px 2px 8px rgba(15, 23, 42, 0.05);
            }

            [data-testid="stMetricLabel"] {
                color: #64748b;
                font-weight: 600;
            }

            [data-testid="stMetricValue"] {
                color: #0f172a;
                font-weight: 800;
            }

            .stAlert {
                border-radius: 12px;
            }

            div[data-testid="stButton"] button {
                background-color: #0f172a;
                color: white;
                border-radius: 10px;
                border: none;
                padding: 0.6rem 1rem;
                font-weight: 700;
            }

            div[data-testid="stButton"] button:hover {
                background-color: #1e293b;
                color: white;
                border: none;
            }

            div[data-testid="stDownloadButton"] button {
                background-color: #334155;
                color: white;
                border-radius: 10px;
                border: none;
                font-weight: 700;
            }

            div[data-testid="stDownloadButton"] button:hover {
                background-color: #475569;
                color: white;
                border: none;
            }

            .block-container {
                padding-top: 3rem;
                padding-bottom: 3rem;
                max-width: 1180px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )