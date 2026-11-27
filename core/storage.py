import json
import os
import tempfile

import pandas as pd
import streamlit as st

from config.constants import (
    DB_FILE,
    DB_SUPERVISI_KONTAK_FILE,
    EXPECTED_COLUMNS,
    EXPECTED_SUPERVISI_COLUMNS,
    MASTER_LOKASI_FILE,
)


def _file_mtime(path: str) -> int:
    return os.stat(path).st_mtime_ns if os.path.exists(path) else 0


def _write_atomically(path: str, writer) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(
        dir=directory,
        prefix=f".{os.path.basename(path)}.",
        suffix=os.path.splitext(path)[1] or ".tmp",
    )
    os.close(descriptor)
    try:
        writer(temporary_path)
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def write_json_atomic(path: str, data) -> None:
    def write(temporary_path):
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    _write_atomically(path, write)


def write_dataframe_atomic(df: pd.DataFrame, path: str) -> None:
    extension = os.path.splitext(path)[1].lower()
    if extension == ".csv":
        writer = lambda temporary_path: df.to_csv(temporary_path, index=False)
    elif extension == ".xlsx":
        writer = lambda temporary_path: df.to_excel(temporary_path, index=False)
    else:
        raise ValueError(f"Format file tidak didukung untuk penulisan atomik: {extension}")
    _write_atomically(path, writer)


@st.cache_data(show_spinner=False)
def _cached_read_csv(path: str, mtime: int) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def _cached_read_excel(path: str, mtime: int) -> pd.DataFrame:
    df = pd.read_excel(path)
    df.columns = [str(column).strip() for column in df.columns]
    return df


@st.cache_data(show_spinner=False)
def _cached_read_json(path: str, mtime: int):
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


def _read_json_safe(path: str) -> dict | list | None:
    return _cached_read_json(path, _file_mtime(path))


@st.cache_data(show_spinner=False)
def _cached_load_db_transformed(path: str, mtime: int) -> pd.DataFrame:
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
    write_dataframe_atomic(df, DB_FILE)


@st.cache_data(show_spinner=False)
def _cached_load_sup_transformed(path: str, mtime: int) -> pd.DataFrame:
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
    write_dataframe_atomic(df, DB_SUPERVISI_KONTAK_FILE)


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
        write_dataframe_atomic(df_excel, MASTER_LOKASI_FILE)
        return True
    except Exception as exc:
        st.error(f"Gagal menyimpan file Excel: {exc}")
        return False
