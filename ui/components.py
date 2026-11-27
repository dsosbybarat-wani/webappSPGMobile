from textwrap import dedent

import streamlit as st


def render_dashboard_card(content_html: str, label: str):
    content_html = dedent(content_html).strip()
    st.markdown(
        f'<div class="dashboard-card">{content_html}'
        f'<div class="card-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def render_address_box(
    kecamatan: str,
    warkop: str,
    status: str,
    alamat: str,
    warkop_fallback: str = "",
):
    markup = dedent(
        f"""
        <div class="address-box">
            📍 <b>Kecamatan:</b> {kecamatan} &nbsp;|&nbsp; <b>Warkop / LKK:</b> {warkop or warkop_fallback} &nbsp;|&nbsp; <b>Status:</b> {status}<br/>
            🏠 <b>Alamat:</b> {alamat}
        </div>
        """
    ).strip()
    st.markdown(
        markup,
        unsafe_allow_html=True,
    )
