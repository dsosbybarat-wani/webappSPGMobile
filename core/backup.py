import json
import os
import tempfile
from datetime import date, datetime
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

from config.constants import (
    DB_FILE,
    DB_SUPERVISI_KONTAK_FILE,
    EXPECTED_COLUMNS,
    EXPECTED_SUPERVISI_COLUMNS,
    JADWAL_SPG_FILE,
    MASTER_AKSES_FILE,
    MASTER_BRAND_FILE,
    MASTER_HARGA_FILE,
    MASTER_LOKASI_FILE,
    MASTER_PLAT_FILE,
    MASTER_SPG_FILE,
    MASTER_TARGET_FILE,
    MASTER_TEAM_BRAND_FILE,
    MASTER_TEAM_NAME_FILE,
    WEB_APP_URL,
    WARKOP_VISIT_STATUS_FILE,
)
from core.storage import _read_json_safe
from schedule_entry import SCHEDULE_DETAIL_FILE


def df_to_sheet_rows(df: pd.DataFrame):
    if df is None:
        return []
    columns = [str(column) for column in df.columns]
    if df.empty:
        return [columns] if columns else []

    rows = []
    for row in df.itertuples(index=False, name=None):
        serialized_row = []
        for value in row:
            if pd.isna(value):
                serialized_row.append("")
            elif isinstance(value, (datetime, pd.Timestamp)):
                serialized_row.append(value.strftime("%Y-%m-%d %H:%M:%S"))
            elif isinstance(value, date):
                serialized_row.append(value.isoformat())
            else:
                serialized_row.append(str(value))
        rows.append(serialized_row)

    return [columns] + rows


def google_json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def sheet_rows_to_df(rows, expected_columns=None):
    if not rows:
        return pd.DataFrame(columns=expected_columns)

    columns = [str(column) for column in rows[0]]
    dataframe = pd.DataFrame(rows[1:], columns=columns)
    if expected_columns is not None:
        for column in expected_columns:
            if column not in dataframe.columns:
                dataframe[column] = ""
        return dataframe[expected_columns]
    return dataframe


def post_google_sheet(payload):
    payload_json = json.dumps(payload, ensure_ascii=False, default=google_json_default)
    response = requests.post(
        WEB_APP_URL,
        data=payload_json,
        headers={"Content-Type": "application/json"},
        timeout=(10, 120),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Google Apps Script mengembalikan HTTP {response.status_code} "
            f"(Content-Type: {response.headers.get('Content-Type', 'tidak diketahui')})."
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Google Apps Script tidak mengembalikan JSON "
            f"(HTTP {response.status_code}, "
            f"Content-Type: {response.headers.get('Content-Type', 'tidak diketahui')}). "
            "Periksa URL Web App, akses deployment, dan handler doPost."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError("Format respons Google Apps Script tidak valid.")
    return result


def get_supabase_config():
    try:
        supabase_url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL"))
        supabase_key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))
    except FileNotFoundError:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Konfigurasi SUPABASE_URL dan SUPABASE_KEY belum tersedia di Streamlit secrets atau environment."
        )

    return supabase_url.rstrip("/"), supabase_key


def post_supabase_backup(snapshot):
    supabase_url, supabase_key = get_supabase_config()
    response = requests.post(
        f"{supabase_url}/rest/v1/app_backups",
        json={"data": snapshot},
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        timeout=(10, 120),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Supabase mengembalikan HTTP {response.status_code}: {response.text[:500]}"
        ) from exc


def get_latest_supabase_backup():
    supabase_url, supabase_key = get_supabase_config()
    response = requests.get(
        f"{supabase_url}/rest/v1/app_backups",
        params={
            "select": "id,created_at,data",
            "order": "created_at.desc,id.desc",
            "limit": "1",
        },
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        },
        timeout=(10, 120),
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Supabase mengembalikan HTTP {response.status_code}: {response.text[:500]}"
        ) from exc

    try:
        backups = response.json()
    except ValueError as exc:
        raise RuntimeError("Supabase tidak mengembalikan JSON yang valid.") from exc

    if not isinstance(backups, list):
        raise RuntimeError("Format respons backup Supabase tidak valid.")
    if not backups:
        raise RuntimeError("Belum ada backup yang tersimpan di Supabase.")
    if not isinstance(backups[0], dict) or not isinstance(backups[0].get("data"), dict):
        raise RuntimeError("Isi backup terbaru di Supabase tidak valid.")
    return backups[0]


def load_supabase_backup_data():
    df_rekap = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame(columns=EXPECTED_COLUMNS)
    df_sup = pd.read_csv(DB_SUPERVISI_KONTAK_FILE) if os.path.exists(DB_SUPERVISI_KONTAK_FILE) else pd.DataFrame(columns=EXPECTED_SUPERVISI_COLUMNS)
    df_jadwal = pd.read_excel(JADWAL_SPG_FILE) if os.path.exists(JADWAL_SPG_FILE) else pd.DataFrame()
    df_lokasi = pd.read_excel(MASTER_LOKASI_FILE) if os.path.exists(MASTER_LOKASI_FILE) else pd.DataFrame()

    def read_json_file(file_path):
        return _read_json_safe(file_path)

    return {
        "backup_version": 1,
        "datasets": {
            "rekap_laporan": df_to_sheet_rows(df_rekap),
            "rekap_supervisi": df_to_sheet_rows(df_sup),
            "jadwal_spg": df_to_sheet_rows(df_jadwal),
            "master_warkop": df_to_sheet_rows(df_lokasi),
        },
        "master_data": {
            "nama_spg": read_json_file(MASTER_SPG_FILE),
            "nama_team": read_json_file(MASTER_TEAM_NAME_FILE),
            "team_brand": read_json_file(MASTER_TEAM_BRAND_FILE),
            "brand_rokok": read_json_file(MASTER_BRAND_FILE),
            "target_brand": read_json_file(MASTER_TARGET_FILE),
            "harga_konsumen": read_json_file(MASTER_HARGA_FILE),
            "plat_kendaraan": read_json_file(MASTER_PLAT_FILE),
            "jadwal_detail": read_json_file(SCHEDULE_DETAIL_FILE),
            "akses_user": read_json_file(MASTER_AKSES_FILE),
            "status_warkop": read_json_file(WARKOP_VISIT_STATUS_FILE),
        },
    }


def restore_supabase_backup(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("backup_version") != 1:
        raise RuntimeError("Versi atau format backup Supabase tidak didukung.")

    datasets = snapshot.get("datasets")
    master_data = snapshot.get("master_data")
    if not isinstance(datasets, dict) or not isinstance(master_data, dict):
        raise RuntimeError("Struktur data backup Supabase tidak lengkap.")

    dataset_specs = {
        "rekap_laporan": (DB_FILE, EXPECTED_COLUMNS, "csv"),
        "rekap_supervisi": (DB_SUPERVISI_KONTAK_FILE, EXPECTED_SUPERVISI_COLUMNS, "csv"),
        "jadwal_spg": (JADWAL_SPG_FILE, None, "excel"),
        "master_warkop": (MASTER_LOKASI_FILE, None, "excel"),
    }
    file_contents = {}
    for dataset_name, (file_path, expected_columns, file_type) in dataset_specs.items():
        rows = datasets.get(dataset_name)
        if not isinstance(rows, list):
            raise RuntimeError(f"Data `{dataset_name}` tidak ditemukan pada backup Supabase.")
        dataframe = sheet_rows_to_df(rows, expected_columns)
        if file_type == "csv":
            file_contents[file_path] = dataframe.to_csv(index=False).encode("utf-8")
        else:
            excel_buffer = BytesIO()
            dataframe.to_excel(excel_buffer, index=False)
            file_contents[file_path] = excel_buffer.getvalue()

    master_file_paths = {
        "nama_spg": MASTER_SPG_FILE,
        "nama_team": MASTER_TEAM_NAME_FILE,
        "team_brand": MASTER_TEAM_BRAND_FILE,
        "brand_rokok": MASTER_BRAND_FILE,
        "target_brand": MASTER_TARGET_FILE,
        "harga_konsumen": MASTER_HARGA_FILE,
        "plat_kendaraan": MASTER_PLAT_FILE,
        "jadwal_detail": SCHEDULE_DETAIL_FILE,
    }
    files_to_remove = []
    for master_name, file_path in master_file_paths.items():
        if master_name not in master_data:
            raise RuntimeError(f"Data master `{master_name}` tidak ditemukan pada backup Supabase.")
        master_value = master_data[master_name]
        if master_value is None:
            files_to_remove.append(file_path)
        else:
            file_contents[file_path] = json.dumps(
                master_value, ensure_ascii=False, indent=2
            ).encode("utf-8")

    if "akses_user" in master_data and master_data["akses_user"] is not None:
        file_contents[MASTER_AKSES_FILE] = json.dumps(
            master_data["akses_user"], ensure_ascii=False, indent=2
        ).encode("utf-8")

    if "status_warkop" in master_data and master_data["status_warkop"] is not None:
        file_contents[WARKOP_VISIT_STATUS_FILE] = json.dumps(
            master_data["status_warkop"], ensure_ascii=False, indent=2
        ).encode("utf-8")

    staged_files = {}
    try:
        for file_path, content in file_contents.items():
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=os.path.dirname(os.path.abspath(file_path)),
                prefix=f".{os.path.basename(file_path)}.",
                suffix=".tmp",
                delete=False,
            ) as staged_file:
                staged_file.write(content)
                staged_files[file_path] = staged_file.name

        for file_path, staged_path in staged_files.items():
            os.replace(staged_path, file_path)
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
    finally:
        for staged_path in staged_files.values():
            if os.path.exists(staged_path):
                os.remove(staged_path)
