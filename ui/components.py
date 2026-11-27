import math
import numbers
from textwrap import dedent

import pandas as pd
import streamlit as st


_SALES_NUMBER_MARKERS = (
    "bungkus",
    "omset",
    "terjual",
    "stok",
    "uang",
    "harga",
    "transaksi",
    "konsumen_beli",
    "target",
)


def format_indonesian_number(value):
    """Format a numeric table value with Indonesian thousands separators."""
    if value is None or pd.isna(value):
        return "-"

    if isinstance(value, numbers.Integral):
        return f"{int(value):,}".replace(",", ".")

    try:
        number = float(value)
    except (TypeError, ValueError):
        return value

    if not math.isfinite(number):
        return "-"
    if number.is_integer():
        return f"{int(number):,}".replace(",", ".")

    whole, decimal = f"{number:,.2f}".split(".")
    return f"{whole.replace(',', '.')},{decimal.rstrip('0')}"


def format_sales_table(data, columns=None):
    """Return a Styler that formats sales-related numeric columns for display."""
    if isinstance(data, pd.DataFrame):
        dataframe = data
        styler = data.style
    else:
        styler = data
        dataframe = data.data

    if columns is None:
        columns = [
            column
            for column in dataframe.columns
            if any(marker in str(column).casefold() for marker in _SALES_NUMBER_MARKERS)
            and pd.api.types.is_numeric_dtype(dataframe[column])
        ]
    else:
        columns = [column for column in columns if column in dataframe.columns]

    return styler.format({column: format_indonesian_number for column in columns})


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
