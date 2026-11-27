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
    normalized_cell = " ".join(normalize_text(team_cell).casefold().split())
    normalized_team = " ".join(normalize_text(team_name).casefold().split())
    if not normalized_cell or normalized_cell in {"nan", "none"}:
        return False
    if normalized_cell == "-":
        return normalized_cell == normalized_team
    return normalized_cell == normalized_team


def _named_column(frame, *names):
    normalized_names = {" ".join(name.casefold().split()) for name in names}
    for column in frame.columns:
        normalized_column = " ".join(str(column).strip().casefold().split())
        if normalized_column in normalized_names:
            return column
    return None


def _location_columns(frame):
    city_column = next(
        (column for column in frame.columns if "kota" in str(column).casefold()),
        None,
    )
    district_column = next(
        (
            column
            for column in frame.columns
            if "kecamatan" in str(column).casefold()
        ),
        None,
    ) or _named_column(frame, "sektor")
    return city_column, district_column


def _parsed_schedule_date(value):
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def get_schedule_info_for_team(team_name, target_date=None):
    df_jadwal = load_jadwal_spg()
    if df_jadwal.empty:
        return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

    city_column, district_column = _location_columns(df_jadwal)
    if not city_column or not district_column:
        return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

    reference_date = target_date or (datetime.utcnow() + timedelta(hours=7)).date()
    date_column = _named_column(df_jadwal, "tanggal")
    team_column = _named_column(df_jadwal, "nama team", "nama tim", "team", "tim")

    if date_column and team_column:
        matched_rows = []
        for _, row in df_jadwal.iterrows():
            if _parsed_schedule_date(row.get(date_column)) != reference_date:
                continue
            if not _is_same_team_reference(row.get(team_column, ""), team_name):
                continue
            district = normalize_text(row.get(district_column, ""))
            if not district:
                continue
            matched_row = row.to_dict()
            matched_row.setdefault("Kota", normalize_text(row.get(city_column, "")))
            matched_row.setdefault("Kecamatan", district)
            matched_rows.append(matched_row)

        if not matched_rows:
            return False, "Tidak Ada Jadwal Team Tersebut Untuk Hari Ini", "Surabaya", [], pd.DataFrame()

        districts = sorted({normalize_text(row.get("Kecamatan", "")) for row in matched_rows if row.get("Kecamatan")})
        cities = [normalize_text(row.get("Kota", "")) for row in matched_rows if row.get("Kota")]
        city = cities[0] if cities else "Surabaya"
        return True, "", city, districts, pd.DataFrame(matched_rows)

    today_column = None
    for column in df_jadwal.columns:
        if _parsed_schedule_date(column) == reference_date:
            today_column = column
            break

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


def get_schedule_team_names() -> list[str]:
    df_jadwal = load_jadwal_spg()
    if df_jadwal is None or df_jadwal.empty:
        return []

    date_column = _named_column(df_jadwal, "tanggal")
    team_column = _named_column(df_jadwal, "nama team", "nama tim", "team", "tim")
    if date_column and team_column:
        team_cells = df_jadwal[team_column].tolist()
    else:
        city_column, district_column = _location_columns(df_jadwal)
        if not city_column or not district_column:
            return []
        date_columns = [
            column
            for column in df_jadwal.columns
            if column not in {city_column, district_column}
            and _parsed_schedule_date(column) is not None
        ]
        team_cells = df_jadwal[date_columns].to_numpy().ravel().tolist()

    names = []
    seen = set()
    for cell in team_cells:
        name = normalize_text(cell)
        if not name or name.casefold() in {"nan", "none", "-"}:
            continue
        if name.casefold() not in seen:
            seen.add(name.casefold())
            names.append(name)
    return names


def get_scheduled_slots_for_date(target_date: date | None = None) -> list[dict]:
    """Get schedule assignments (date, team, city, district) from the schedule workbook."""
    df_jadwal = load_jadwal_spg()
    if df_jadwal is None or df_jadwal.empty:
        return []

    city_column, district_column = _location_columns(df_jadwal)
    if not city_column or not district_column:
        return []

    reference_date = target_date or (datetime.utcnow() + timedelta(hours=7)).date()
    flat_date_column = _named_column(df_jadwal, "tanggal")
    flat_team_column = _named_column(df_jadwal, "nama team", "nama tim", "team", "tim")
    if flat_date_column and flat_team_column:
        slots = []
        seen = set()
        for _, row in df_jadwal.iterrows():
            parsed_date = _parsed_schedule_date(row.get(flat_date_column))
            team_value = normalize_text(row.get(flat_team_column, ""))
            district_value = normalize_text(row.get(district_column, ""))
            if (
                parsed_date is None
                or (target_date is not None and parsed_date != reference_date)
                or not team_value
                or team_value.casefold() in {"nan", "none", "-"}
                or not district_value
            ):
                continue
            city_value = normalize_text(row.get(city_column, "")) or "Surabaya"
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

    date_columns = []
    for column in df_jadwal.columns:
        if column in {city_column, district_column}:
            continue
        parsed_date = _parsed_schedule_date(column)
        if parsed_date is not None:
            date_columns.append((column, parsed_date))

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
