from datetime import date, datetime, timedelta
import os

import pandas as pd
import streamlit as st

from config.constants import JADWAL_SPG_FILE
from core.storage import _cached_read_excel, _file_mtime


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_jadwal_spg():
    if os.path.exists(JADWAL_SPG_FILE):
        try:
            return _cached_read_excel(JADWAL_SPG_FILE, _file_mtime(JADWAL_SPG_FILE)).copy()
        except Exception as exc:
            st.error(f"Gagal membaca file Jadwal SPG {JADWAL_SPG_FILE}: {exc}")
            return pd.DataFrame()
    return pd.DataFrame()


def save_jadwal_spg(df):
    try:
        df.to_excel(JADWAL_SPG_FILE, index=False)
        return True
    except Exception as exc:
        st.error(f"Gagal menyimpan file Jadwal SPG {JADWAL_SPG_FILE}: {exc}")
        return False


def _is_same_team_reference(team_cell, team_name):
    normalized_cell = normalize_text(team_cell).lower()
    normalized_team = normalize_text(team_name).lower()
    if not normalized_cell or normalized_cell in {"nan", "none"}:
        return False
    if normalized_cell == "-":
        return normalized_cell == normalized_team
    return normalized_cell == normalized_team


def get_schedule_info_for_team(team_name):
    df_jadwal = load_jadwal_spg()
    if df_jadwal.empty:
        return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

    city_column = next((column for column in df_jadwal.columns if "kota" in str(column).lower()), None)
    district_column = next((column for column in df_jadwal.columns if "kecamatan" in str(column).lower()), None)
    if not city_column or not district_column:
        return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

    today = (datetime.utcnow() + timedelta(hours=7)).date()
    today_column = None
    for column in df_jadwal.columns:
        try:
            if pd.to_datetime(column).date() == today:
                today_column = column
                break
        except Exception:
            continue

    if not today_column:
        return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

    matched_rows = []
    for _, row in df_jadwal.iterrows():
        value = normalize_text(row.get(today_column, ""))
        if not value or value.lower() == "nan" or value == "-":
            continue
        if _is_same_team_reference(value, team_name):
            city_value = normalize_text(row.get(city_column, ""))
            district_value = normalize_text(row.get(district_column, ""))
            if city_value or district_value:
                matched_rows.append({"Kota": city_value, "Kecamatan": district_value})

    if not matched_rows:
        return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

    districts = sorted({row["Kecamatan"] for row in matched_rows if row["Kecamatan"]})
    cities = [row["Kota"] for row in matched_rows if row["Kota"]]
    city = cities[0] if cities else "Surabaya"
    return True, "", city, districts, pd.DataFrame(matched_rows)


def get_scheduled_slots_for_date(target_date: date | None = None) -> list[dict]:
    """Get schedule assignments (date, team, city, district) from the schedule workbook."""
    df_jadwal = load_jadwal_spg()
    if df_jadwal is None or df_jadwal.empty:
        return []

    city_column = next((column for column in df_jadwal.columns if "kota" in str(column).lower()), None)
    district_column = next((column for column in df_jadwal.columns if "kecamatan" in str(column).lower()), None)
    if not city_column or not district_column:
        return []

    reference_date = target_date or (datetime.utcnow() + timedelta(hours=7)).date()
    date_columns = []
    for column in df_jadwal.columns:
        if column in {city_column, district_column}:
            continue
        try:
            date_columns.append((column, pd.to_datetime(column).date()))
        except Exception:
            continue

    if target_date is not None:
        date_columns = [(column, parsed_date) for column, parsed_date in date_columns if parsed_date == reference_date]

    slots = []
    seen = set()
    for _, row in df_jadwal.iterrows():
        city_value = normalize_text(row.get(city_column, "")) or "Surabaya"
        district_value = normalize_text(row.get(district_column, ""))
        if not district_value:
            continue
        for column, parsed_date in date_columns:
            team_value = normalize_text(row.get(column, ""))
            if not team_value or team_value.lower() in {"nan", "none", "-"}:
                continue
            key = (
                parsed_date.isoformat(),
                team_value.casefold(),
                city_value.casefold(),
                district_value.casefold(),
            )
            if key in seen:
                continue
            seen.add(key)
            slots.append({
                "tanggal": parsed_date,
                "tanggal_str": parsed_date.strftime("%d %b %Y"),
                "team": team_value,
                "kota": city_value,
                "kecamatan": district_value,
            })

    slots.sort(key=lambda slot: (
        slot["tanggal"], slot["team"].casefold(), slot["kota"].casefold(), slot["kecamatan"].casefold()
    ))
    return slots
