import json
import os

import pandas as pd
import streamlit as st

from config.constants import (
    DB_FILE,
    DB_SUPERVISI_KONTAK_FILE,
    EXPECTED_COLUMNS,
    EXPECTED_SUPERVISI_COLUMNS,
    MASTER_LOKASI_FILE,
)


def _file_mtime(path: str) -> float:
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


@st.cache_data(show_spinner=False)
def _cached_read_csv(path: str, mtime: float) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def _cached_read_excel(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [str(column).strip() for column in df.columns]
    return df


@st.cache_data(show_spinner=False)
def _cached_read_json(path: str, mtime: float):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_text = file.read().strip()
        if not raw_text:
            return None
        return json.loads(raw_text)
    except (OSError, json.JSONDecodeError):
        return None


@st.cache_data(show_spinner=False)
def _cached_read_json_no_mtime(path: str, _mtime: float = 0.0) -> dict | list | None:
    """Read JSON safely while using the file modification time as the cache key."""
    return _cached_read_json(path, _mtime)


def _read_json_safe(path: str) -> dict | list | None:
    return _cached_read_json_no_mtime(path, _file_mtime(path))


@st.cache_data(show_spinner=False)
def _cached_load_db_transformed(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "Usia" in df.columns and "Range_Umur" not in df.columns:
        df = df.rename(columns={"Usia": "Range_Umur"})
    for column in EXPECTED_COLUMNS:
        if column not in df.columns:
            df[column] = "-"
    return df[EXPECTED_COLUMNS]


def load_database():
    if os.path.exists(DB_FILE):
        try:
            return _cached_load_db_transformed(DB_FILE, _file_mtime(DB_FILE)).copy()
        except Exception:
            return pd.DataFrame(columns=EXPECTED_COLUMNS)
    return pd.DataFrame(columns=EXPECTED_COLUMNS)


def save_database(df):
    df.to_csv(DB_FILE, index=False)


@st.cache_data(show_spinner=False)
def _cached_load_sup_transformed(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    for column in EXPECTED_SUPERVISI_COLUMNS:
        if column not in df.columns:
            df[column] = "-"
    return df[EXPECTED_SUPERVISI_COLUMNS]


def load_supervisi_database():
    if os.path.exists(DB_SUPERVISI_KONTAK_FILE):
        try:
            return _cached_load_sup_transformed(
                DB_SUPERVISI_KONTAK_FILE,
                _file_mtime(DB_SUPERVISI_KONTAK_FILE),
            ).copy()
        except Exception:
            return pd.DataFrame(columns=EXPECTED_SUPERVISI_COLUMNS)
    return pd.DataFrame(columns=EXPECTED_SUPERVISI_COLUMNS)


def save_supervisi_database(df):
    df.to_csv(DB_SUPERVISI_KONTAK_FILE, index=False)


def load_master_lokasi_excel():
    if os.path.exists(MASTER_LOKASI_FILE):
        try:
            return _cached_read_excel(MASTER_LOKASI_FILE, _file_mtime(MASTER_LOKASI_FILE)).copy()
        except Exception as exc:
            st.error(f"Gagal membaca file Excel {MASTER_LOKASI_FILE}: {exc}")
            return pd.DataFrame(columns=["Kota", "Kecamatan", "Nama Warkop / LKK", "Alamat Warkop / LKK"])
    return pd.DataFrame(
        columns=["Kota", "Kecamatan", "Nama Warkop / LKK", "Alamat Warkop / LKK"],
        data=[
            ["Surabaya", "Kecamatan Default", "Warkop Cak No", "-"],
            ["Surabaya", "Kecamatan Default", "Warkop Pitoe", "-"],
        ],
    )


def save_master_lokasi_excel(df_excel):
    try:
        df_excel.to_excel(MASTER_LOKASI_FILE, index=False)
        return True
    except Exception as exc:
        st.error(f"Gagal menyimpan file Excel: {exc}")
        return False
