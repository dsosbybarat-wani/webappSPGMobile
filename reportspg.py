import streamlit as st

st.set_page_config(
    page_title="Ayu Agency | Laporan & Monitoring SPG",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from ui.application import run_app

run_app()
