import streamlit as st

st.set_page_config(
    page_title="Laporan Dirsell SPG",
    page_icon="📍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

from ui.application import run_app

run_app()
