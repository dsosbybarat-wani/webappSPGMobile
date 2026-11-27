from datetime import date, datetime, timedelta
from io import BytesIO
import json
import os
import re
import tempfile
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import requests
from shapely.geometry import Point
import streamlit as st
from functools import lru_cache
from streamlit_js_eval import get_geolocation
from config.constants import (
    DEFAULT_BRANDS,
    DEFAULT_HARGA_KONSUMEN,
    DEFAULT_PLATS,
    DEFAULT_SPGS,
    DEFAULT_SPG_PIN,
    DEFAULT_SUPERVISI_PIN,
    EXPECTED_COLUMNS,
    EXPECTED_SUPERVISI_COLUMNS,
    GEOJSON_INDEX_FILE,
    KECAMATAN_BY_KOTA,
    LOCKED_LKK_POINT_FILE,
    MASTER_AKSES_FILE,
    MASTER_BRAND_FILE,
    MASTER_HARGA_FILE,
    MASTER_PLAT_FILE,
    MASTER_SPG_FILE,
    MASTER_TARGET_FILE,
    MASTER_TEAM_BRAND_FILE,
    MASTER_TEAM_NAME_FILE,
    STOK_SUPERVISI_FILE,
    TARGET_GROUP_OPTIONS,
    VISIT_STATUS_OPTIONS,
    VISIT_STATUS_TIDAK_WAJIB,
    VISIT_STATUS_WAJIB,
    WARKOP_VISIT_STATUS_FILE,
    WEB_APP_URL,
)
from core.auth import (
    load_master_akses,
    reset_session_on_user_change,
    save_master_akses,
    verify_admin_password,
    verify_user_pin,
)
from core.backup import (
    df_to_sheet_rows,
    get_latest_supabase_backup,
    get_supabase_config,
    google_json_default,
    load_supabase_backup_data,
    post_google_sheet,
    post_supabase_backup,
    restore_supabase_backup,
    sheet_rows_to_df,
)
from core.storage import (
    _cached_read_excel,
    _cached_read_json,
    _file_mtime,
    _read_json_safe,
    load_database,
    load_master_lokasi_excel,
    load_supervisi_database,
    save_database,
    save_master_lokasi_excel,
    save_supervisi_database,
    write_json_atomic,
)
from domain.target import (
    TARGET_RULES,
    clean_brand_target_name,
    get_brand_target_rule,
    get_group_target,
    get_target_for_brand,
    load_target_rules,
    normalize_brand_key,
    refresh_target_rules,
    save_target_rules,
    style_status_target,
)
from domain.schedule import (
    get_schedule_info_for_team,
    get_schedule_team_names,
    get_scheduled_slots_for_date,
    load_jadwal_spg,
    normalize_text,
    save_jadwal_spg,
)
from geo.loader import (
    _resolve_kecamatan_filepath,
    build_polygon_features,
    get_geo_districts,
    load_geojson_index,
    load_kecamatan_gdf,
    load_kecamatan_geojson,
    load_master_wilayah,
)
from ui.theme import apply_team_theme_css, get_team_theme, render_global_styles
from ui.components import format_sales_table, render_address_box, render_dashboard_card

try:
    from schedule_entry import (
        SCHEDULE_DETAIL_FILE,
        get_scheduled_personnel_for_team,
        get_scheduled_spg_names,
        get_scheduled_vehicles,
        render_schedule_entry,
    )
except ImportError:
    from schedule_entry import (
        SCHEDULE_DETAIL_FILE,
        get_scheduled_spg_names,
        get_scheduled_vehicles,
        render_schedule_entry,
    )

    def get_scheduled_personnel_for_team(team_name, target_date=None, selected_kecamatan=""):
        return {
            "found": False,
            "supervisi": [],
            "spg_1": [],
            "spg_2": [],
            "spg_all": [],
            "vehicles": [],
            "records": [],
        }

from team_brand_sync import (
    match_brands_by_team_name,
    resolve_team_allowed_brands,
)

# ====================================================
# KONFIGURASI HALAMAN STREAMLIT
# ====================================================





# ====================================================
# CUSTOM CSS UNTUK UI MODERN & MOBILE-FRIENDLY
# ====================================================




# ====================================================
# DEFINISI FILE DATABASE LOKAL & KONFIGURASI GOOGLE SHEET
# ====================================================
























def _stok_sup_key(tanggal_str: str, team_name: str, brand_name: str) -> str:
    return "|".join([
        str(tanggal_str or "").strip(),
        str(team_name or "").strip().casefold(),
        str(brand_name or "").strip().casefold(),
    ])


def load_stok_supervisi() -> dict:
    data = _read_json_safe(STOK_SUPERVISI_FILE)
    return data if isinstance(data, dict) else {}


def save_stok_supervisi(stok_map: dict) -> bool:
    cleaned = {}
    for k, v in (stok_map or {}).items():
        try:
            cleaned[str(k)] = max(0, int(float(v)))
        except (ValueError, TypeError):
            cleaned[str(k)] = 0
    write_json_atomic(STOK_SUPERVISI_FILE, cleaned)
    return True


def get_stok_awal_supervisi(tanggal_str: str, team_name: str, brand_name: str, stok_map: dict | None = None) -> int:
    smap = stok_map if isinstance(stok_map, dict) else load_stok_supervisi()
    key = _stok_sup_key(tanggal_str, team_name, brand_name)
    val = smap.get(key, 0)
    try:
        return max(0, int(float(val)))
    except (ValueError, TypeError):
        return 0




def load_harga_konsumen() -> dict:
    data = _read_json_safe(MASTER_HARGA_FILE)
    if isinstance(data, dict) and data:
        cleaned = {}
        for k, v in data.items():
            label = str(k or "").strip()
            if label:
                try:
                    cleaned[label] = max(0, int(float(v)))
                except (ValueError, TypeError):
                    cleaned[label] = 0
        if cleaned:
            return cleaned
    return dict(DEFAULT_HARGA_KONSUMEN)


def save_harga_konsumen(harga_map: dict) -> bool:
    cleaned = {}
    for k, v in (harga_map or {}).items():
        label = str(k or "").strip()
        if label:
            try:
                cleaned[label] = max(0, int(float(v)))
            except (ValueError, TypeError):
                cleaned[label] = 0
    write_json_atomic(MASTER_HARGA_FILE, cleaned)
    return True


def get_harga_konsumen_brand(brand: str, harga_map: dict | None = None) -> int:
    hmap = harga_map if isinstance(harga_map, dict) else load_harga_konsumen()
    b_key = normalize_brand_key(brand)
    if not b_key:
        return 0
    for k, v in hmap.items():
        if normalize_brand_key(k) == b_key:
            try:
                return max(0, int(float(v)))
            except (ValueError, TypeError):
                return 0
    return 0








def _warkop_status_key(kota: str, kecamatan: str, warkop: str) -> str:
    return "|".join([
        str(kota or "").strip().casefold(),
        str(kecamatan or "").strip().casefold(),
        str(warkop or "").strip().casefold(),
    ])


def load_warkop_visit_status_map() -> dict:
    data = _read_json_safe(WARKOP_VISIT_STATUS_FILE)
    return data if isinstance(data, dict) else {}


def save_warkop_visit_status_map(status_map: dict) -> bool:
    try:
        cleaned = {}
        for k, v in (status_map or {}).items():
            val = str(v or "").strip()
            if val in VISIT_STATUS_OPTIONS:
                cleaned[str(k)] = val
            elif "tidak" in val.casefold() or "opsional" in val.casefold():
                cleaned[str(k)] = VISIT_STATUS_TIDAK_WAJIB
            else:
                cleaned[str(k)] = VISIT_STATUS_WAJIB
        write_json_atomic(WARKOP_VISIT_STATUS_FILE, cleaned)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan status warkop wajib/tidak wajib: {e}")
        return False


def get_warkop_visit_status(kota: str, kecamatan: str, warkop: str, status_map: dict | None = None) -> str:
    smap = status_map if isinstance(status_map, dict) else load_warkop_visit_status_map()
    key = _warkop_status_key(kota, kecamatan, warkop)
    raw_val = smap.get(key)
    if raw_val in VISIT_STATUS_OPTIONS:
        return raw_val
    suffix = f"|{str(kecamatan or '').strip().casefold()}|{str(warkop or '').strip().casefold()}"
    for k, v in smap.items():
        if str(k).endswith(suffix) and v in VISIT_STATUS_OPTIONS:
            return v
    return VISIT_STATUS_TIDAK_WAJIB


def build_warkop_status_dataframe(df_lokasi: pd.DataFrame, status_map: dict | None = None) -> pd.DataFrame:
    smap = status_map if isinstance(status_map, dict) else load_warkop_visit_status_map()
    empty_cols = ["Kota", "Kecamatan", "Nama Warkop / LKK", "Alamat Warkop / LKK", "Status Kunjungan"]
    if df_lokasi is None or df_lokasi.empty:
        return pd.DataFrame(columns=empty_cols)

    c_kota = next((c for c in df_lokasi.columns if "kota" in str(c).lower()), None)
    c_kec = next((c for c in df_lokasi.columns if "kec" in str(c).lower() or "wilayah" in str(c).lower()), None)
    c_wrk = next((c for c in df_lokasi.columns if "warkop" in str(c).lower() or "lkk" in str(c).lower() or "nama" in str(c).lower()), None)
    c_alm = next((c for c in df_lokasi.columns if "alamat" in str(c).lower() or "address" in str(c).lower()), None)

    out = pd.DataFrame({
        "Kota": df_lokasi[c_kota].astype(str).str.strip().replace("", "Surabaya") if c_kota else "Surabaya",
        "Kecamatan": df_lokasi[c_kec].astype(str).str.strip() if c_kec else "",
        "Nama Warkop / LKK": df_lokasi[c_wrk].astype(str).str.strip() if c_wrk else "",
        "Alamat Warkop / LKK": (df_lokasi[c_alm].astype(str).str.strip().replace("", "-") if c_alm else "-"),
    })
    out = out[out["Nama Warkop / LKK"] != ""].reset_index(drop=True)

    out["Status Kunjungan"] = [
        get_warkop_visit_status(k, kc, w, smap)
        for k, kc, w in zip(out["Kota"], out["Kecamatan"], out["Nama Warkop / LKK"])
    ]
    return out[empty_cols]


def load_locked_lkk_points() -> dict:
    data = _read_json_safe(LOCKED_LKK_POINT_FILE)
    return data if isinstance(data, dict) else {}


def save_locked_lkk_point(team_name: str, point_info: dict) -> bool:
    today_str = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d")
    all_locked = load_locked_lkk_points()
    key = str(team_name or "").strip().casefold()
    payload = dict(point_info)
    payload["status_kunjungan"] = str(payload.get("status_kunjungan") or VISIT_STATUS_WAJIB).strip()
    payload["tanggal"] = today_str
    payload["locked_at"] = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    all_locked[key] = payload
    try:
        write_json_atomic(LOCKED_LKK_POINT_FILE, all_locked)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan titik LKK aktif: {e}")
        return False


def clear_locked_lkk_point(team_name: str) -> bool:
    """Membuka kunci titik LKK aktif setelah Supervisi menyelesaikan kunjungan & menyimpan kontak konsumen."""
    all_locked = load_locked_lkk_points()
    key = str(team_name or "").strip().casefold()
    if key in all_locked:
        all_locked.pop(key, None)
        try:
            write_json_atomic(LOCKED_LKK_POINT_FILE, all_locked)
            return True
        except Exception:
            return False
    return True


def get_active_locked_lkk_point_today(team_name: str, fallback_kota: str = "") -> dict | None:
    """Mengambil titik LKK yang sudah di-save / di-lock oleh Supervisi untuk team hari ini (WIB)."""
    today_str = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d")
    all_locked = load_locked_lkk_points()
    key = str(team_name or "").strip().casefold()
    entry = all_locked.get(key)
    if not isinstance(entry, dict):
        return None
    if str(entry.get("tanggal", "")).strip() != today_str:
        return None
    warkop = str(entry.get("warkop", "") or "").strip()
    if not warkop:
        return None
    kota = str(entry.get("kota", fallback_kota) or fallback_kota).strip()
    if fallback_kota and kota and kota.casefold() != str(fallback_kota).strip().casefold():
        return None
    kec = str(entry.get("kecamatan", "") or "").strip()
    status_kunjungan = str(entry.get("status_kunjungan") or "").strip()
    if status_kunjungan not in VISIT_STATUS_OPTIONS:
        status_kunjungan = get_warkop_visit_status(kota, kec, warkop)
    return {
        "kota": kota,
        "kecamatan": kec,
        "warkop": warkop,
        "alamat": str(entry.get("alamat", "-") or "-").strip() or "-",
        "status_kunjungan": status_kunjungan,
        "locked_at": str(entry.get("locked_at", "") or "").strip(),
    }


def get_saved_contact_warkops_on_date(
    team_name: str,
    target_date_str: str,
    df_sup: pd.DataFrame | None = None,
) -> set[tuple[str, str]]:
    """Mengambil himpunan (kecamatan_casefold, warkop_casefold) yang sudah disimpan datanya lewat Save Jumlah Kontak Konsumen pada tanggal tertentu."""
    if df_sup is None:
        df_sup = load_supervisi_database()
    if df_sup is None or df_sup.empty:
        return set()

    mask = (
        df_sup["Promotor"].astype(str).str.strip().str.casefold()
        == str(team_name or "").strip().casefold()
    ) & (
        df_sup["Waktu"].astype(str).str.startswith(str(target_date_str or "").strip())
    )
    saved_pairs = set()
    for _, row in df_sup[mask].iterrows():
        w_val = str(row.get("Warkop_LKK", "") or "").strip().casefold()
        kc_val = str(row.get("Kecamatan", "") or "").strip().casefold()
        if w_val:
            saved_pairs.add((kc_val, w_val))
    return saved_pairs




















def render_google_sheet_backup_controls():
    with st.expander("☁️ Backup & Load Data", expanded=False):
        st.caption("Backup data aplikasi ke Google Spreadsheet atau Supabase.")

        col_backup_gs, col_backup_supabase = st.columns(2)
        with col_backup_gs:
            btn_backup_gs = st.button(
                "⬆️ Backup ke Sheet",
                use_container_width=True,
                key="backup_google_sheet",
            )
        with col_backup_supabase:
            btn_backup_supabase = st.button(
                "⬆️ Backup ke Supabase",
                use_container_width=True,
                key="backup_supabase",
            )
        col_load_gs, col_load_supabase = st.columns(2)
        with col_load_gs:
            btn_load_gs = st.button(
                "⬇️ Load dari Sheet",
                use_container_width=True,
                key="load_google_sheet",
            )
        with col_load_supabase:
            btn_load_supabase = st.button(
                "⬇️ Load dari Supabase",
                use_container_width=True,
                key="load_supabase",
            )

        if btn_backup_gs:
            try:
                with st.spinner("Mem-backup data ke Google Sheet..."):
                    snapshot = load_supabase_backup_data()
                    ds = snapshot["datasets"]
                    payload = {
                        "action": "backup",
                        "rekap_laporan": ds["rekap_laporan"],
                        "rekap_supervisi": ds["rekap_supervisi"],
                        "jadwal_spg": ds["jadwal_spg"],
                        "master_warkop": ds["master_warkop"],
                    }
                    res_json = post_google_sheet(payload)
                    if res_json.get("status") == "success":
                        st.success("✅ " + res_json.get("message", "Backup berhasil!"))
                    else:
                        st.error("❌ " + res_json.get("message", "Gagal backup."))
            except Exception as e:
                st.error(f"Error backup: {e}")
        if btn_backup_supabase:
            try:
                with st.spinner("Mem-backup data ke Supabase..."):
                    snapshot = load_supabase_backup_data()
                    post_supabase_backup(snapshot)
                    st.success("✅ Backup berhasil disimpan ke Supabase.")
            except Exception as e:
                st.error(f"Error backup Supabase: {e}")

        if btn_load_supabase:
            try:
                with st.spinner("Memuat backup terbaru dari Supabase..."):
                    backup = get_latest_supabase_backup()
                    restore_supabase_backup(backup["data"])
                    st.success(
                        f"✅ Backup Supabase {backup.get('created_at', '')} "
                        "berhasil dimuat. Data lokal telah diganti."
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Error load Supabase: {e}")

        if btn_load_gs:
            try:
                with st.spinner("Memuat data dari Google Sheet..."):
                    res_json = post_google_sheet({"action": "load"})
                    if res_json.get("status") == "success":
                        data_gs = res_json.get("data", {})

                        if "rekap_laporan" in data_gs and len(data_gs["rekap_laporan"]) > 0:
                            save_database(sheet_rows_to_df(data_gs["rekap_laporan"], EXPECTED_COLUMNS))
                        if "rekap_supervisi" in data_gs and len(data_gs["rekap_supervisi"]) > 0:
                            save_supervisi_database(
                                sheet_rows_to_df(data_gs["rekap_supervisi"], EXPECTED_SUPERVISI_COLUMNS)
                            )
                        if "jadwal_spg" in data_gs and len(data_gs["jadwal_spg"]) > 0:
                            if not save_jadwal_spg(sheet_rows_to_df(data_gs["jadwal_spg"])):
                                raise RuntimeError("Gagal menyimpan jadwal dari Google Sheet.")
                        if "master_warkop" in data_gs and len(data_gs["master_warkop"]) > 0:
                            if not save_master_lokasi_excel(sheet_rows_to_df(data_gs["master_warkop"])):
                                raise RuntimeError("Gagal menyimpan master warkop dari Google Sheet.")

                        st.success("✅ Data berhasil dimuat dari Google Sheet!")
                        st.rerun()
                    else:
                        st.error("❌ " + res_json.get("message", "Gagal load."))
            except Exception as e:
                st.error(f"Error load: {e}")


# ====================================================
# FUNGSI BANTUAN UMUM
# ====================================================


def get_custom_week_info(dt):
    if pd.isna(dt):
        return "-", "-"
    d = pd.to_datetime(dt).date()
    wd = d.weekday()

    if wd == 5:
        fri_date = d + timedelta(days=6)
    elif wd == 6:
        fri_date = d + timedelta(days=5)
    else:
        fri_date = d + timedelta(days=(4 - wd))

    _, iso_w, _ = fri_date.isocalendar()
    periode_label = f"Minggu ke-{iso_w}"
    return periode_label, iso_w


def add_custom_week_columns(df, date_col="Waktu_Dt"):
    if df.empty or date_col not in df.columns:
        df["Periode_Minggu"] = "-"
        return df
    periods = []
    for val in df[date_col]:
        p_label, _ = get_custom_week_info(val)
        periods.append(p_label)
    df["Periode_Minggu"] = periods
    return df


# ====================================================
# DATABASE TRANSAKSI & SUPERVISI
# ====================================================












def get_latest_supervisi_point_today(
    team_name: str,
    fallback_kota: str = "",
    fallback_kec: str = "",
    df_sup: pd.DataFrame | None = None,
) -> dict | None:
    """Mengambil titik LKK terbaru yang sudah diinput & disimpan oleh Supervisi hari ini untuk team tersebut."""
    today_str = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d")
    if df_sup is None:
        df_sup = load_supervisi_database()
    if df_sup is None or df_sup.empty:
        return None

    mask = (
        df_sup["Promotor"].astype(str).str.strip().str.casefold()
        == str(team_name or "").strip().casefold()
    ) & (
        df_sup["Waktu"].astype(str).str.startswith(today_str)
    )
    if fallback_kota:
        mask = mask & (
            df_sup["Kota_Kab"].astype(str).str.strip().str.casefold()
            == str(fallback_kota).strip().casefold()
        )

    df_today = df_sup[mask].copy()
    if df_today.empty:
        return None

    parsed = pd.to_datetime(df_today["Waktu"], errors="coerce")
    if parsed.notna().any():
        df_today = df_today.assign(_dt=parsed).sort_values("_dt", ascending=False)
    else:
        df_today = df_today.iloc[::-1]

    for _, row in df_today.iterrows():
        warkop = str(row.get("Warkop_LKK", "") or "").strip()
        if warkop:
            return {
                "kota": str(row.get("Kota_Kab", fallback_kota) or fallback_kota).strip(),
                "kecamatan": str(row.get("Kecamatan", fallback_kec) or fallback_kec).strip(),
                "warkop": warkop,
                "alamat": str(row.get("Alamat_Warkop", "-") or "-").strip() or "-",
                "kontak": int(pd.to_numeric(row.get("Jumlah_Kontak_Manual", 0), errors="coerce") or 0),
                "waktu": str(row.get("Waktu", "") or "").strip(),
            }
    return None


def get_supervisi_points_today(
    team_name: str,
    fallback_kota: str = "",
    fallback_kec: str = "",
    df_sup: pd.DataFrame | None = None,
) -> list[dict]:
    """Mengambil daftar titik LKK unik yang sudah diinput Supervisi hari ini (terbaru di atas)."""
    today_str = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d")
    if df_sup is None:
        df_sup = load_supervisi_database()
    if df_sup is None or df_sup.empty:
        return []

    mask = (
        df_sup["Promotor"].astype(str).str.strip().str.casefold()
        == str(team_name or "").strip().casefold()
    ) & (
        df_sup["Waktu"].astype(str).str.startswith(today_str)
    )
    if fallback_kota:
        mask = mask & (
            df_sup["Kota_Kab"].astype(str).str.strip().str.casefold()
            == str(fallback_kota).strip().casefold()
        )

    df_today = df_sup[mask].copy()
    if df_today.empty:
        return []

    parsed = pd.to_datetime(df_today["Waktu"], errors="coerce")
    if parsed.notna().any():
        df_today = df_today.assign(_dt=parsed).sort_values("_dt", ascending=False)
    else:
        df_today = df_today.iloc[::-1]

    points = []
    seen = set()
    for _, row in df_today.iterrows():
        warkop = str(row.get("Warkop_LKK", "") or "").strip()
        if not warkop:
            continue
        kec = str(row.get("Kecamatan", fallback_kec) or fallback_kec).strip()
        key = (kec.casefold(), warkop.casefold())
        if key in seen:
            continue
        seen.add(key)
        points.append({
            "kota": str(row.get("Kota_Kab", fallback_kota) or fallback_kota).strip(),
            "kecamatan": kec,
            "warkop": warkop,
            "alamat": str(row.get("Alamat_Warkop", "-") or "-").strip() or "-",
            "kontak": int(pd.to_numeric(row.get("Jumlah_Kontak_Manual", 0), errors="coerce") or 0),
            "waktu": str(row.get("Waktu", "") or "").strip(),
        })
    return points


# ====================================================
# MASTER WILAYAH / GEOJSON (ON-DEMAND PER KECAMATAN)
# ====================================================





















# ====================================================
# MASTER BRAND / TARGET / TEAM / PLAT / NAMA TEAM (CACHED)
# ====================================================


def load_master_team_names():
    default_teams = {f"Team SPG {i}": f"Team SPG {i}" for i in range(1, 21)}
    data = _read_json_safe(MASTER_TEAM_NAME_FILE)
    uses_placeholder_names = not isinstance(data, dict) or all(
        str(data.get(key, key)).strip() == key for key in default_teams
    )
    scheduled_teams = get_schedule_team_names()[:20] if uses_placeholder_names else []
    if uses_placeholder_names and scheduled_teams:
        data = {
            f"Team SPG {i}": scheduled_teams[i - 1] if i <= len(scheduled_teams) else ""
            for i in range(1, 21)
        }
        save_master_team_names(data)
        return data
    if not isinstance(data, dict):
        save_master_team_names(default_teams)
        return default_teams
    for i in range(1, 21):
        key = f"Team SPG {i}"
        if key not in data:
            data[key] = key
        else:
            data[key] = str(data[key]).strip()
    return data


def save_master_team_names(team_names_dict):
    active_names = [str(name).strip() for name in team_names_dict.values() if str(name).strip()]
    if not active_names:
        st.error("Minimal satu nama team harus diisi. Unggah jadwal SPG untuk mengatur nama team otomatis.")
        return False
    if len({name.casefold() for name in active_names}) != len(active_names):
        st.error("Nama team tidak boleh duplikat.")
        return False
    try:
        write_json_atomic(
            MASTER_TEAM_NAME_FILE,
            {
                f"Team SPG {i}": str(team_names_dict.get(f"Team SPG {i}", "")).strip()
                for i in range(1, 21)
            },
        )
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan master nama team: {e}")
        return False


def load_master_brands():
    data = _read_json_safe(MASTER_BRAND_FILE)
    return data if isinstance(data, list) else DEFAULT_BRANDS


def save_master_brands(brands):
    try:
        write_json_atomic(MASTER_BRAND_FILE, brands)
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan file master_brand_rokok.json: {e}")
        return False


def load_master_team_brands():
    current_brands = load_master_brands()
    team_map = load_master_team_names()
    active_team_names = [team_map[f"Team SPG {i}"] for i in range(1, 21) if team_map[f"Team SPG {i}"]]
    default_teams = {
        team_name: match_brands_by_team_name(team_name, current_brands)
        for team_name in active_team_names
    }
    data = _read_json_safe(MASTER_TEAM_BRAND_FILE)
    if not isinstance(data, dict):
        save_master_team_brands(default_teams)
        return default_teams
    for i, t_name in enumerate(active_team_names, start=1):
        t_key = f"Team SPG {i}"
        if t_name not in data and t_key not in data:
            data[t_name] = match_brands_by_team_name(t_name, current_brands)
    return data


def save_master_team_brands(team_brands):
    try:
        cleaned_data = {
            str(team): [str(b).strip() for b in brands]
            for team, brands in team_brands.items()
        }
        write_json_atomic(MASTER_TEAM_BRAND_FILE, cleaned_data)
        return True
    except Exception as e:
        st.error(f"❌ Gagal menyimpan ke `{MASTER_TEAM_BRAND_FILE}`: {e}")
        return False


def load_master_plat_kendaraan():
    data = _read_json_safe(MASTER_PLAT_FILE)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return list(data.values())
    return DEFAULT_PLATS


def save_master_plat_kendaraan(plat_list):
    write_json_atomic(MASTER_PLAT_FILE, plat_list)


def load_master_spgs():
    data = _read_json_safe(MASTER_SPG_FILE)
    return data if isinstance(data, list) else get_scheduled_spg_names() or DEFAULT_SPGS


def save_master_spgs(spgs):
    write_json_atomic(MASTER_SPG_FILE, spgs)






# ====================================================
# JADWAL SPG
# ====================================================








# ====================================================
# TARGET BRAND PER SPG / TEAM
# ====================================================























# ====================================================
# FUNGSI REPORT REKAPITULASI PENJUALAN & KONTROL STOK ROKOK
# ====================================================
def render_rekapitulasi_penjualan_report(team_name: str, target_date_str: str, allow_edit_stok: bool = True):
    """Menampilkan komponen laporan:
    1. Rekap Penjualan 2 SPG & Kontrol Stok Rokok
    2. Breakdown Penjualan Per Nama SPG Hari Ini
    3. Rekap Stok Dibawa, Terjual 2 SPG & Sisa Stok Per Merk
    4. Rekap Kunjungan Warkop / LKK Hari Ini (4A Wajib Kunjung Belum Dikunjungi & 4B Semua Warkop Dikunjungi)
    """
    df_all_db = load_database()
    df_all_sup_db = load_supervisi_database()
    harga_konsumen_map = load_harga_konsumen()
    stok_sup_map = load_stok_supervisi()
    status_map_report = load_warkop_visit_status_map()
    df_warkop_master = build_warkop_status_dataframe(load_master_lokasi_excel(), status_map_report)

    df_team_spg_today = pd.DataFrame()
    if not df_all_db.empty and "Promotor" in df_all_db.columns:
        df_team_spg_today = df_all_db[
            (df_all_db["Promotor"].astype(str).str.strip().str.casefold() == str(team_name).strip().casefold())
            & (df_all_db["Waktu"].astype(str).str.startswith(str(target_date_str).strip()))
        ].copy()

    if not df_team_spg_today.empty:
        df_team_spg_today["Jumlah_Bungkus"] = pd.to_numeric(
            df_team_spg_today["Jumlah_Bungkus"], errors="coerce"
        ).fillna(0)
        df_team_spg_today["Harga_Konsumen"] = df_team_spg_today["Brand_Rokok"].apply(
            lambda b: get_harga_konsumen_brand(b, harga_konsumen_map)
        )
        df_team_spg_today["Total_Uang_Rp"] = (
            df_team_spg_today["Jumlah_Bungkus"] * df_team_spg_today["Harga_Konsumen"]
        ).astype(int)

    df_team_sup_today = pd.DataFrame()
    if not df_all_sup_db.empty and "Promotor" in df_all_sup_db.columns:
        df_team_sup_today = df_all_sup_db[
            (df_all_sup_db["Promotor"].astype(str).str.strip().str.casefold() == str(team_name).strip().casefold())
            & (df_all_sup_db["Waktu"].astype(str).str.startswith(str(target_date_str).strip()))
        ].copy()
        if not df_team_sup_today.empty:
            df_team_sup_today["Jumlah_Kontak_Manual"] = pd.to_numeric(
                df_team_sup_today["Jumlah_Kontak_Manual"], errors="coerce"
            ).fillna(0).astype(int)

    all_brands_sup = load_master_brands()
    team_brands_sup_map = load_master_team_brands()
    team_names_sup_map = load_master_team_names()
    allowed_brands_sup = resolve_team_allowed_brands(
        team_name=team_name,
        all_brands=all_brands_sup,
        team_brands_map=team_brands_sup_map,
        team_names_map=team_names_sup_map,
        prefer_keyword_match=True,
    )
    if not allowed_brands_sup:
        allowed_brands_sup = all_brands_sup

    sold_brands_today = (
        df_team_spg_today["Brand_Rokok"].dropna().astype(str).str.strip().unique().tolist()
        if not df_team_spg_today.empty
        else []
    )
    brand_list_sup_stok = list(
        dict.fromkeys([b for b in allowed_brands_sup if b] + [b for b in sold_brands_today if b])
    )

    try:
        parsed_target_date = datetime.strptime(str(target_date_str).strip(), "%Y-%m-%d").date()
    except ValueError:
        parsed_target_date = (datetime.utcnow() + timedelta(hours=7)).date()

    locked_point_today = get_active_locked_lkk_point_today(team_name=team_name)
    sched_spg_today = get_scheduled_personnel_for_team(
        team_name,
        parsed_target_date,
        selected_kecamatan=locked_point_today["kecamatan"] if locked_point_today else "",
    ).get("spg_all", [])
    tx_spg_today = (
        df_team_spg_today["Nama_SPG"].dropna().astype(str).str.strip().unique().tolist()
        if not df_team_spg_today.empty
        else []
    )
    spg_2_list = list(dict.fromkeys([s for s in sched_spg_today if s] + [s for s in tx_spg_today if s]))
    if not spg_2_list:
        spg_2_list = ["SPG 1", "SPG 2"]

    total_bks_2spg_today = int(df_team_spg_today["Jumlah_Bungkus"].sum()) if not df_team_spg_today.empty else 0
    total_uang_2spg_today = int(df_team_spg_today["Total_Uang_Rp"].sum()) if not df_team_spg_today.empty else 0

    # --- 1. REKAP PENJUALAN 2 SPG & KONTROL STOK ROKOK ---
    st.markdown(f"### 1️⃣ Rekap Penjualan 2 SPG & Kontrol Stok Rokok ({team_name})")
    st.caption("Dashboard Monitoring")

    st.info(
        f"💵 **Jumlah Uang Terkumpul ({target_date_str}) — Penjualan 2 SPG:** "
        f"**Rp {total_uang_2spg_today:,}** ({total_bks_2spg_today:,} bungkus • "
        f"SPG: {', '.join(tx_spg_today) if tx_spg_today else 'Belum ada penjualan'})"
    )

    if allow_edit_stok:
        with st.form(f"form_input_stok_supervisi_{team_name}_{target_date_str}"):
            st.markdown("#### 📥 Input Jumlah Stok Rokok yang Dibawa (Per Merk)")
            st.caption(f"Tanggal: **{target_date_str}** • Team: **{team_name}**")
            stok_input_dict = {}
            if not brand_list_sup_stok:
                st.info("Belum ada daftar merk rokok untuk tim ini.")
            else:
                for idx_b, b_name in enumerate(brand_list_sup_stok):
                    existing_stok = get_stok_awal_supervisi(target_date_str, team_name, b_name, stok_sup_map)
                    col_sb1, col_sb2 = st.columns([0.6, 0.4])
                    with col_sb1:
                        st.markdown(f"**🚬 {b_name}**")
                        st.caption(f"Harga konsumen: Rp {get_harga_konsumen_brand(b_name, harga_konsumen_map):,} / bks")
                    with col_sb2:
                        stok_input_dict[b_name] = st.number_input(
                            f"Stok dibawa {b_name}",
                            min_value=0,
                            step=1,
                            value=int(existing_stok),
                            label_visibility="collapsed",
                            key=f"inp_stok_sup_{team_name}_{target_date_str}_{idx_b}_{b_name}",
                        )
            btn_save_stok_sup = st.form_submit_button("💾 Simpan Stok Dibawa Supervisi", type="primary", use_container_width=True)
            if btn_save_stok_sup:
                for b_name, qty_val in stok_input_dict.items():
                    k_stok = _stok_sup_key(target_date_str, team_name, b_name)
                    stok_sup_map[k_stok] = int(qty_val)
                if save_stok_supervisi(stok_sup_map):
                    st.success("✅ Jumlah stok rokok yang dibawa Supervisi berhasil disimpan!")
                    st.rerun()

    st.markdown("---")
    # --- 2. BREAKDOWN PENJUALAN PER NAMA SPG HARI INI ---
    st.markdown("### 2️⃣ Breakdown Penjualan Per Nama SPG Hari Ini")
    spg_cols = st.columns(min(2, len(spg_2_list)) if spg_2_list else 1)
    for idx_s, spg_nm in enumerate(spg_2_list[:2]):
        df_s = (
            df_team_spg_today[
                df_team_spg_today["Nama_SPG"].astype(str).str.strip().str.casefold() == spg_nm.strip().casefold()
            ]
            if not df_team_spg_today.empty
            else pd.DataFrame()
        )
        bks_s = int(df_s["Jumlah_Bungkus"].sum()) if not df_s.empty else 0
        uang_s = int(df_s["Total_Uang_Rp"].sum()) if not df_s.empty else 0
        trx_s = int(len(df_s)) if not df_s.empty else 0
        with spg_cols[idx_s % len(spg_cols)]:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-person-name" style="font-size:0.85rem;font-weight:700;">👩‍💼 {spg_nm}</div>
                    <div class="card-value" style="margin-top:6px;">{bks_s:,} bks</div>
                    <div class="card-subtext">Rp {uang_s:,} • {trx_s} transaksi</div>
                </div>
                """,
                f"Penjualan SPG #{idx_s + 1} Hari Ini",
            )

    if not df_team_spg_today.empty:
        df_breakdown_spg_merk = (
            df_team_spg_today.groupby(["Nama_SPG", "Brand_Rokok"])
            .agg(
                Transaksi=("Nama_Konsumen", "count"),
                Terjual_Bungkus=("Jumlah_Bungkus", "sum"),
                Total_Uang_Rp=("Total_Uang_Rp", "sum"),
            )
            .reset_index()
        )
        df_breakdown_spg_merk["Terjual_Bungkus"] = df_breakdown_spg_merk["Terjual_Bungkus"].astype(int)
        df_breakdown_spg_merk["Total_Uang_Rp"] = df_breakdown_spg_merk["Total_Uang_Rp"].astype(int)
        st.dataframe(format_sales_table(df_breakdown_spg_merk), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada penjualan SPG tercatat pada tanggal ini.")

    st.markdown("---")
    # --- 3. REKAP STOK DIBAWA, TERJUAL 2 SPG & SISA STOK PER MERK ---
    st.markdown("### 3️⃣ Rekap Stok Dibawa, Terjual 2 SPG & Sisa Stok Per Merk")
    rows_stok_rekap = []
    for b_name in brand_list_sup_stok:
        stok_dibawa = get_stok_awal_supervisi(target_date_str, team_name, b_name, stok_sup_map)
        df_b = (
            df_team_spg_today[
                df_team_spg_today["Brand_Rokok"].astype(str).str.strip().str.casefold() == b_name.strip().casefold()
            ]
            if not df_team_spg_today.empty
            else pd.DataFrame()
        )
        terjual_spg_b = int(df_b["Jumlah_Bungkus"].sum()) if not df_b.empty else 0
        sisa_stok_b = stok_dibawa - terjual_spg_b
        uang_b = int(df_b["Total_Uang_Rp"].sum()) if not df_b.empty else 0

        r_detail = {"Merk_Rokok": b_name, "Stok_Dibawa": stok_dibawa}
        for spg_nm in spg_2_list[:2]:
            col_key = f"Terjual_{spg_nm}"
            if not df_b.empty:
                val_spg_b = int(
                    df_b[df_b["Nama_SPG"].astype(str).str.strip().str.casefold() == spg_nm.strip().casefold()][
                        "Jumlah_Bungkus"
                    ].sum()
                )
            else:
                val_spg_b = 0
            r_detail[col_key] = val_spg_b

        r_detail["Total_Terjual_SPG"] = terjual_spg_b
        r_detail["Sisa_Stok"] = sisa_stok_b
        r_detail["Uang_Merk_Rp"] = uang_b
        rows_stok_rekap.append(r_detail)

    if rows_stok_rekap:
        df_stok_rekap = pd.DataFrame(rows_stok_rekap)
        st.dataframe(format_sales_table(df_stok_rekap), use_container_width=True, hide_index=True)

        total_stok_dibawa_all = int(df_stok_rekap["Stok_Dibawa"].sum())
        total_terjual_all = int(df_stok_rekap["Total_Terjual_SPG"].sum())
        total_sisa_stok_all = int(df_stok_rekap["Sisa_Stok"].sum())
        st.info(
            f"📦 **Ringkasan Stok ({target_date_str}):** Stok Dibawa: **{total_stok_dibawa_all:,} bks** • "
            f"Terjual 2 SPG: **{total_terjual_all:,} bks** • "
            f"**Sisa Stok: {total_sisa_stok_all:,} bks**"
        )
    else:
        st.info("Belum ada data stok atau merk untuk direkap.")

    st.markdown("---")
    # --- 4. REKAP KUNJUNGAN WARKOP / LKK HARI INI ---
    st.markdown(f"### 4️⃣ Rekap Kunjungan Warkop / LKK ({target_date_str})")

    # Kumpulkan data kunjungan dari log Supervisi dan transaksi SPG pada tanggal tersebut
    visited_records_map = {}

    if not df_team_sup_today.empty:
        for _, r_sup in df_team_sup_today.iterrows():
            w_nm = str(r_sup.get("Warkop_LKK", "") or "").strip()
            if not w_nm:
                continue
            kc_nm = str(r_sup.get("Kecamatan", "") or "").strip()
            kt_nm = str(r_sup.get("Kota_Kab", "Surabaya") or "Surabaya").strip()
            alm_nm = str(r_sup.get("Alamat_Warkop", "-") or "-").strip() or "-"
            wkt_nm = str(r_sup.get("Waktu", "") or "").strip()
            knt_val = int(pd.to_numeric(r_sup.get("Jumlah_Kontak_Manual", 0), errors="coerce") or 0)
            key_pair = (kc_nm.casefold(), w_nm.casefold())
            if key_pair not in visited_records_map:
                visited_records_map[key_pair] = {
                    "Kota": kt_nm,
                    "Kecamatan": kc_nm,
                    "Warkop_LKK": w_nm,
                    "Alamat_Warkop": alm_nm,
                    "Status_Kunjungan": get_warkop_visit_status(kt_nm, kc_nm, w_nm, status_map_report),
                    "Waktu_Kunjungan": wkt_nm,
                    "Jumlah_Kontak_Tim": knt_val,
                    "Jumlah_Konsumen_Beli": 0,
                    "Total_Bungkus_Terjual": 0,
                }
            else:
                visited_records_map[key_pair]["Jumlah_Kontak_Tim"] += knt_val
                if wkt_nm and (
                    not visited_records_map[key_pair]["Waktu_Kunjungan"]
                    or wkt_nm > visited_records_map[key_pair]["Waktu_Kunjungan"]
                ):
                    visited_records_map[key_pair]["Waktu_Kunjungan"] = wkt_nm

    if not df_team_spg_today.empty:
        for _, r_spg in df_team_spg_today.iterrows():
            w_nm = str(r_spg.get("Warkop_LKK", "") or "").strip()
            if not w_nm:
                continue
            kc_nm = str(r_spg.get("Kecamatan", "") or "").strip()
            kt_nm = str(r_spg.get("Kota_Kab", "Surabaya") or "Surabaya").strip()
            alm_nm = str(r_spg.get("Alamat_Warkop", "-") or "-").strip() or "-"
            wkt_nm = str(r_spg.get("Waktu", "") or "").strip()
            bks_val = int(pd.to_numeric(r_spg.get("Jumlah_Bungkus", 0), errors="coerce") or 0)
            key_pair = (kc_nm.casefold(), w_nm.casefold())
            if key_pair not in visited_records_map:
                visited_records_map[key_pair] = {
                    "Kota": kt_nm,
                    "Kecamatan": kc_nm,
                    "Warkop_LKK": w_nm,
                    "Alamat_Warkop": alm_nm,
                    "Status_Kunjungan": get_warkop_visit_status(kt_nm, kc_nm, w_nm, status_map_report),
                    "Waktu_Kunjungan": wkt_nm,
                    "Jumlah_Kontak_Tim": 0,
                    "Jumlah_Konsumen_Beli": 1,
                    "Total_Bungkus_Terjual": bks_val,
                }
            else:
                visited_records_map[key_pair]["Jumlah_Konsumen_Beli"] += 1
                visited_records_map[key_pair]["Total_Bungkus_Terjual"] += bks_val
                if wkt_nm and (
                    not visited_records_map[key_pair]["Waktu_Kunjungan"]
                    or wkt_nm > visited_records_map[key_pair]["Waktu_Kunjungan"]
                ):
                    visited_records_map[key_pair]["Waktu_Kunjungan"] = wkt_nm

    visited_keys_set = set(visited_records_map.keys())
    visited_warkop_names_only = {w for _, w in visited_keys_set}

    # Tentukan kecamatan yang relevan pada tanggal tersebut (jadwal tanggal tsb + warkop yang sudah dikunjungi)
    slots_for_date = get_scheduled_slots_for_date(parsed_target_date)
    active_kec_set = {
        str(s.get("kecamatan", "") or "").strip().casefold()
        for s in slots_for_date
        if str(s.get("team", "") or "").strip().casefold() == str(team_name or "").strip().casefold()
        and str(s.get("kecamatan", "") or "").strip()
    }
    for kc_k, _ in visited_keys_set:
        if kc_k:
            active_kec_set.add(kc_k)

    # --- 4A. DAFTAR WARKOP WAJIB KUNJUNG YANG BELUM DIKUNJUNGI ---
    st.markdown("#### 4A. Daftar Warkop Wajib Kunjung yang Belum Dikunjungi")
    unvisited_wajib_rows = []
    if not df_warkop_master.empty:
        wajib_df = df_warkop_master[df_warkop_master["Status Kunjungan"] == VISIT_STATUS_WAJIB].copy()
        if active_kec_set:
            wajib_df = wajib_df[
                wajib_df["Kecamatan"].astype(str).str.strip().str.casefold().isin(active_kec_set)
            ]
        for _, rw in wajib_df.iterrows():
            kt_w = str(rw.get("Kota", "") or "").strip()
            kc_w = str(rw.get("Kecamatan", "") or "").strip()
            nm_w = str(rw.get("Nama Warkop / LKK", "") or "").strip()
            alm_w = str(rw.get("Alamat Warkop / LKK", "-") or "-").strip() or "-"
            pair_w = (kc_w.casefold(), nm_w.casefold())
            if pair_w not in visited_keys_set and nm_w.casefold() not in visited_warkop_names_only:
                unvisited_wajib_rows.append({
                    "Kota": kt_w,
                    "Kecamatan": kc_w,
                    "Nama Warkop / LKK": nm_w,
                    "Alamat Warkop / LKK": alm_w,
                    "Status Kunjungan": VISIT_STATUS_WAJIB,
                })

    if unvisited_wajib_rows:
        df_4a = pd.DataFrame(unvisited_wajib_rows).sort_values(
            by=["Kecamatan", "Nama Warkop / LKK"]
        ).reset_index(drop=True)
        st.dataframe(df_4a, use_container_width=True, hide_index=True)
        st.warning(f"⚠️ Terdapat **{len(df_4a)}** warkop **Wajib Kunjung** yang belum dikunjungi pada {target_date_str}.")
    else:
        st.success(f"✅ Seluruh warkop **Wajib Kunjung** pada wilayah aktif ({target_date_str}) sudah dikunjungi!")

    # --- 4B. SEMUA WARKOP YANG DIKUNJUNGI HARI INI ---
    st.markdown("#### 4B. Semua Warkop yang Dikunjungi Hari Ini")
    if visited_records_map:
        df_4b = pd.DataFrame(list(visited_records_map.values())).sort_values(
            by=["Waktu_Kunjungan", "Kecamatan", "Warkop_LKK"],
            ascending=[False, True, True],
        ).reset_index(drop=True)
        st.dataframe(format_sales_table(df_4b), use_container_width=True, hide_index=True)
        st.info(
            f"📍 **Ringkasan Kunjungan ({target_date_str}):** **{len(df_4b)}** warkop dikunjungi • "
            f"Total Kontak Tim: **{int(df_4b['Jumlah_Kontak_Tim'].sum()):,}** • "
            f"Konsumen Beli: **{int(df_4b['Jumlah_Konsumen_Beli'].sum()):,}** • "
            f"Terjual: **{int(df_4b['Total_Bungkus_Terjual'].sum()):,} bks**"
        )
    else:
        st.info(f"Belum ada warkop yang tercatat dikunjungi pada tanggal {target_date_str}.")


# ====================================================


def run_app():
    render_global_styles()
    # SESSION STATE
    # ====================================================


    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user_spg" not in st.session_state:
        st.session_state["user_spg"] = ""
    if "plat_mobil" not in st.session_state:
        st.session_state["plat_mobil"] = ""
    if "kota_kab" not in st.session_state:
        st.session_state["kota_kab"] = ""
    if "nama_supervisi_aktif" not in st.session_state:
        st.session_state["nama_supervisi_aktif"] = ""
    if "spg_terjadwal_list" not in st.session_state:
        st.session_state["spg_terjadwal_list"] = []
    if "sektor_terjadwal_login" not in st.session_state:
        st.session_state["sektor_terjadwal_login"] = ""
    if "spg_authenticated_name" not in st.session_state:
        st.session_state["spg_authenticated_name"] = ""
    if "show_titik_lkk_spg" not in st.session_state:
        st.session_state["show_titik_lkk_spg"] = False
    if "login_mode" not in st.session_state:
        st.session_state["login_mode"] = "SPG"
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False
    if "admin_view" not in st.session_state:
        st.session_state["admin_view"] = "Dashboard"
    if "draft_konsumen" not in st.session_state:
        st.session_state["draft_konsumen"] = ""
    if "draft_nohp" not in st.session_state:
        st.session_state["draft_nohp"] = ""
    if "draft_ig" not in st.session_state:
        st.session_state["draft_ig"] = ""
    if "draft_bungkus" not in st.session_state:
        st.session_state["draft_bungkus"] = 0
    if "draft_bumo" not in st.session_state:
        st.session_state["draft_bumo"] = ""
    if "draft_brand" not in st.session_state:
        st.session_state["draft_brand"] = ""
    if "draft_gender" not in st.session_state:
        st.session_state["draft_gender"] = "L"
    if "draft_range_umur" not in st.session_state:
        st.session_state["draft_range_umur"] = ""
    if "spg_form_nonce" not in st.session_state:
        st.session_state["spg_form_nonce"] = 0
    if "sup_kontak_nonce" not in st.session_state:
        st.session_state["sup_kontak_nonce"] = 0

    # ====================================================
    # AKSES TERPISAH HALAMAN ADMIN VIA QUERY PARAM (?page=admin)
    # ====================================================
    _qp_page = str(st.query_params.get("page", "")).strip().lower()
    _admin_portal_requested = (_qp_page == "admin")

    if not _admin_portal_requested and st.session_state.get("admin_logged_in"):
        st.session_state["admin_logged_in"] = False

    # ====================================================
    # SIDEBAR ADMIN (HANYA TAMPIL SAAT ?page=admin AKTIF)
    # ====================================================
    if _admin_portal_requested and not st.session_state["logged_in"]:
        from pages.admin.sidebar import render as render_admin_sidebar
        render_admin_sidebar()

    # ====================================================
    # HALAMAN ADMIN
    # ====================================================
    if _admin_portal_requested and not st.session_state["logged_in"] and st.session_state["admin_logged_in"]:
        from pages.admin.router import render_admin_page
        render_admin_page(st.session_state.get("admin_view", "Dashboard"))
        st.stop()

    # ====================================================
    # PORTAL LOGIN KHUSUS ADMIN (?page=admin)
    # ====================================================
    if _admin_portal_requested and not st.session_state["logged_in"] and not st.session_state["admin_logged_in"]:
        from pages.admin.login import render as render_admin_login
        render_admin_login()
        st.stop()

    # ====================================================
    # HALAMAN LOGIN UTAMA (SPG, SUPERVISI & REKAPITULASI PENJUALAN)
    # ====================================================
    if not st.session_state["logged_in"]:
        st.markdown(
            """
            <div class="login-header">
                <div style="font-size: 2.2rem; margin-bottom: 4px;">📝</div>
                <span class="login-kicker">AYU AGENCY</span>
                <h1>APLIKASI LAPORAN &amp; MONITORING SPG</h1>
                <p>Pantau aktivitas lapangan, jadwal tim, dan laporan penjualan dalam satu ruang kerja.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">1️⃣ Pilih Peran Masuk</div>', unsafe_allow_html=True)
        col_btn_mode1, col_btn_mode2, col_btn_mode3 = st.columns(3)
        with col_btn_mode1:
            if st.button(
                "📝 Masuk sebagai SPG",
                use_container_width=True,
                type="primary" if st.session_state["login_mode"] == "SPG" else "secondary",
            ):
                st.session_state["login_mode"] = "SPG"
                st.session_state["spg_authenticated_name"] = ""
                st.session_state["show_titik_lkk_spg"] = False
                st.rerun()

        with col_btn_mode2:
            if st.button(
                "👀 Masuk sebagai Supervisi",
                use_container_width=True,
                type="primary" if st.session_state["login_mode"] == "Supervisi" else "secondary",
            ):
                st.session_state["login_mode"] = "Supervisi"
                st.session_state["spg_authenticated_name"] = ""
                st.rerun()

        with col_btn_mode3:
            if st.button(
                "📊 Rekapitulasi Penjualan",
                use_container_width=True,
                type="primary" if st.session_state["login_mode"] == "Rekapitulasi" else "secondary",
            ):
                st.session_state["login_mode"] = "Rekapitulasi"
                st.session_state["spg_authenticated_name"] = ""
                st.rerun()

        team_name_mapping = load_master_team_names()
        list_team = [
            team_name_mapping[f"Team SPG {i}"]
            for i in range(1, 21)
            if team_name_mapping[f"Team SPG {i}"]
        ]
        akses_cfg_login = load_master_akses()

        if st.session_state["login_mode"] == "Rekapitulasi":
            st.markdown('<div class="section-title">2️⃣ Pilih Tim &amp; Tanggal Rekapitulasi</div>', unsafe_allow_html=True)
            with st.container(border=True):
                today_wib_rek = (datetime.utcnow() + timedelta(hours=7)).date()
                c_rek1, c_rek2 = st.columns([0.65, 0.35])
                with c_rek1:
                    pilihan_user_rek = st.selectbox(
                        "👤 Nama Team Operasional",
                        list_team,
                        key="selected_team_rekapitulasi",
                    )
                with c_rek2:
                    tgl_rekap_input = st.date_input(
                        "📅 Tanggal Laporan",
                        value=today_wib_rek,
                        key="selected_date_rekapitulasi",
                    )

            apply_team_theme_css(pilihan_user_rek)
            st.markdown("---")
            render_rekapitulasi_penjualan_report(
                team_name=pilihan_user_rek,
                target_date_str=tgl_rekap_input.strftime("%Y-%m-%d"),
                allow_edit_stok=False,
            )

            st.markdown(
                """
                <div class="footer-note">
                    © 2026 Tumarso Monitoring System
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.stop()

        st.markdown('<div class="section-title">2️⃣ Pilih Tim, Identitas &amp; Verifikasi Jadwal</div>', unsafe_allow_html=True)
        with st.container(border=True):
            pilihan_user = st.selectbox(
                "👤 Nama Team Operasional",
                list_team,
                key="selected_team_login",
                on_change=reset_session_on_user_change,
            )

            schedule_ok, schedule_warning_msg, auto_detected_kota, auto_kecamatan_list, matched_schedule_rows = get_schedule_info_for_team(pilihan_user)
            today_wib = (datetime.utcnow() + timedelta(hours=7)).date()

            selected_sektor_login = ""
            if schedule_ok and len(auto_kecamatan_list) > 1:
                selected_sektor_login = st.selectbox(
                    "📍 Pilih Sektor / Kecamatan Terjadwal Hari Ini",
                    options=auto_kecamatan_list,
                    key="login_select_sektor_team",
                )
            elif schedule_ok and len(auto_kecamatan_list) == 1:
                selected_sektor_login = auto_kecamatan_list[0]

            personnel_info = (
                get_scheduled_personnel_for_team(pilihan_user, today_wib, selected_kecamatan=selected_sektor_login)
                if schedule_ok
                else {"found": False, "supervisi": [], "spg_1": [], "spg_2": [], "spg_all": [], "vehicles": [], "records": []}
            )

            if schedule_ok and personnel_info.get("records"):
                auto_detected_kota = personnel_info["records"][0].get("kota") or auto_detected_kota

            scheduled_vehicles = personnel_info.get("vehicles", []) if personnel_info.get("found") else []
            if schedule_ok and not scheduled_vehicles:
                scheduled_vehicles = get_scheduled_vehicles(matched_schedule_rows, today_wib)

            spv_names = personnel_info.get("supervisi", [])
            spg1_names = personnel_info.get("spg_1", [])
            spg2_names = personnel_info.get("spg_2", [])
            spg_all_names = personnel_info.get("spg_all", [])

            spg_login_selected = ""
            pin_login_input = ""

            if not schedule_ok:
                st.error("⚠️ **Tidak Ada Jadwal Team Tersebut Untuk Hari Ini**")
            else:
                spv_label = ", ".join(spv_names) if spv_names else "Belum diatur di jadwal"
                spg1_label = ", ".join(spg1_names) if spg1_names else "-"
                spg2_label = ", ".join(spg2_names) if spg2_names else "-"
                sektor_tampil = selected_sektor_login or (", ".join(auto_kecamatan_list) if auto_kecamatan_list else "-")
                st.success(
                    f"✅ **Jadwal Aktif Ditemukan**\n\n"
                    f"- **Wilayah / Sektor:** {auto_detected_kota} — **{sektor_tampil}**\n"
                    f"- **Supervisi:** **{spv_label}**\n"
                    f"- **SPG 1:** **{spg1_label}** | **SPG 2:** **{spg2_label}**"
                )
                if st.session_state["login_mode"] == "Supervisi":
                    if len(scheduled_vehicles) == 1:
                        st.info(f"🚗 Plat Kendaraan Terjadwal: **{scheduled_vehicles[0]}**")
                    elif not scheduled_vehicles:
                        st.warning("Plat kendaraan belum diatur pada jadwal team hari ini.")
                    else:
                        st.error(f"Terdapat lebih dari satu plat kendaraan ({', '.join(scheduled_vehicles)}). Samakan plat pada jadwal.")

                    pin_login_input = st.text_input(
                        f"🔐 PIN Supervisi ({spv_label})",
                        type="password",
                        placeholder="Masukkan PIN Supervisi",
                        key="login_pin_supervisi",
                    )
                else:
                    opsi_spg_login = spg_all_names if spg_all_names else load_master_spgs()
                    if opsi_spg_login:
                        spg_login_selected = st.selectbox(
                            "👩‍💼 Pilih Identitas Nama SPG Anda (Terkunci Selama Sesi)",
                            options=opsi_spg_login,
                            key="login_select_spg_identity",
                        )
                    if akses_cfg_login.get("require_spg_pin", False):
                        pin_login_input = st.text_input(
                            f"🔐 PIN SPG ({spg_login_selected or 'SPG'})",
                            type="password",
                            placeholder="Masukkan PIN SPG",
                            key="login_pin_spg",
                        )

            st.markdown("")
            btn_login = st.button(f"🚀 Lanjut Masuk ({st.session_state['login_mode']})", type="primary", use_container_width=True)

            if btn_login:
                if not schedule_ok:
                    st.error("❌ Akses ditolak: Tidak Ada Jadwal Team Tersebut Untuk Hari Ini.")
                elif st.session_state["login_mode"] == "Supervisi" and len(scheduled_vehicles) != 1:
                    st.error("❌ Akses Supervisi ditolak: plat kendaraan pada jadwal belum tersedia atau tidak konsisten.")
                elif st.session_state["login_mode"] == "Supervisi" and not verify_user_pin(
                    "Supervisi", spv_names[0] if spv_names else pilihan_user, pin_login_input, akses_cfg_login
                ):
                    st.error("❌ PIN Supervisi salah! Masukkan PIN yang sesuai agar data Supervisi tidak tertukar.")
                elif (
                    st.session_state["login_mode"] == "SPG"
                    and akses_cfg_login.get("require_spg_pin", False)
                    and not verify_user_pin("SPG", spg_login_selected, pin_login_input, akses_cfg_login)
                ):
                    st.error("❌ PIN SPG salah! Masukkan PIN SPG yang sesuai.")
                else:
                    st.session_state["logged_in"] = True
                    st.session_state["user_spg"] = pilihan_user
                    st.session_state["plat_mobil"] = scheduled_vehicles[0] if len(scheduled_vehicles) == 1 else "-"
                    st.session_state["kota_kab"] = auto_detected_kota
                    st.session_state["nama_supervisi_aktif"] = spv_names[0] if spv_names else ""
                    st.session_state["spg_terjadwal_list"] = spg_all_names
                    st.session_state["sektor_terjadwal_login"] = selected_sektor_login
                    st.session_state["spg_authenticated_name"] = spg_login_selected
                    st.session_state["show_titik_lkk_spg"] = False
                    st.rerun()

        st.markdown(
            """
            <div class="footer-note">
                © 2026 Tumarso Monitoring System
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ====================================================
    # APLIKASI UTAMA SETELAH LOGIN (TEMA DINAMIS PER TEAM)
    # ====================================================
    apply_team_theme_css(st.session_state["user_spg"])

    # --- GPS & GEOFENCING ---
    daftar_kecamatan = get_geo_districts(st.session_state["kota_kab"]) or ["Kecamatan Default"]
    schedule_ok, _, _, daftar_kecamatan_terjadwal, _ = get_schedule_info_for_team(
        st.session_state["user_spg"]
    )
    loc = get_geolocation()
    detected_kecamatan = None

    if loc is None or not isinstance(loc, dict) or "coords" not in loc:
        user_lat = -7.2575
        user_lon = 112.7521
        akurasi_meter = 0.0
        is_inside_geofence = True
    else:
        user_lat = float(loc["coords"]["latitude"])
        user_lon = float(loc["coords"]["longitude"])
        akurasi_meter = round(float(loc["coords"].get("accuracy", 0)), 1)
        point_user = Point(user_lon, user_lat)
        is_inside_geofence = False

        kandidat_kec_gps = (
            [k for k in (daftar_kecamatan_terjadwal or []) if k]
            if schedule_ok
            else []
        )
        if not kandidat_kec_gps:
            kandidat_kec_gps = [k for k in daftar_kecamatan if k != "Kecamatan Default"]

        checked_any_geom = False
        for kc_cand in kandidat_kec_gps:
            fp_cand = _resolve_kecamatan_filepath(kc_cand)
            gdf_cand = load_kecamatan_gdf(kc_cand, _file_mtime(fp_cand) if fp_cand else 0.0)
            if gdf_cand is not None and not gdf_cand.empty:
                checked_any_geom = True
                col_kec_cand = next(
                    (c for c in ["nm_kecamatan", "KECAMATAN", "kecamatan", "Name", "NAME"] if c in gdf_cand.columns),
                    None,
                )
                for _, row_geom in gdf_cand.iterrows():
                    geom = row_geom.geometry
                    if geom is not None and (geom.contains(point_user) or geom.intersects(point_user)):
                        is_inside_geofence = True
                        detected_kecamatan = (
                            str(row_geom[col_kec_cand]).strip()
                            if col_kec_cand and pd.notna(row_geom[col_kec_cand])
                            else kc_cand
                        )
                        break
            if is_inside_geofence:
                break
        if not checked_any_geom:
            is_inside_geofence = True

    # --- JADWAL & TITIK KUNJUNGAN TERKUNCI ---
    if not schedule_ok:
        daftar_kecamatan_terjadwal = daftar_kecamatan if daftar_kecamatan else ["Kecamatan Umum"]
    else:
        daftar_kecamatan_terjadwal = sorted(set(daftar_kecamatan_terjadwal))

    df_sup_today_all = load_supervisi_database()
    locked_point_today = get_active_locked_lkk_point_today(
        team_name=st.session_state["user_spg"],
        fallback_kota=st.session_state.get("kota_kab", ""),
    )
    latest_sup_contact = get_latest_supervisi_point_today(
        team_name=st.session_state["user_spg"],
        fallback_kota=st.session_state.get("kota_kab", ""),
        df_sup=df_sup_today_all,
    )

    df_master_excel = load_master_lokasi_excel()
    col_kec_excel = next(
        (c for c in df_master_excel.columns if "kec" in c.lower() or "wilayah" in c.lower()),
        None,
    ) if not df_master_excel.empty else None
    col_warkop_excel = next(
        (c for c in df_master_excel.columns if "warkop" in c.lower() or "lkk" in c.lower() or "nama" in c.lower()),
        None,
    ) if not df_master_excel.empty else None
    col_alamat_excel = next(
        (c for c in df_master_excel.columns if "alamat" in c.lower() or "address" in c.lower()),
        None,
    ) if not df_master_excel.empty else None

    # ====================================================
    # MODE SUPERVISI (2 MENU SAVE: SAVE TITIK LKK & SAVE JUMLAH KONTAK)
    # ====================================================
    if st.session_state["login_mode"] == "Supervisi":
        today_str_sup_hdr = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d")
        saved_contact_pairs_today = get_saved_contact_warkops_on_date(
            team_name=st.session_state["user_spg"],
            target_date_str=today_str_sup_hdr,
            df_sup=df_sup_today_all,
        )
        saved_contact_warkops_names = {w_n for _, w_n in saved_contact_pairs_today}

        # Jika titik yang sedang di-lock sudah disimpan kontaknya hari ini, lepas lock-nya agar tidak mengunci warkop yang sudah selesai
        if locked_point_today:
            lp_kc = str(locked_point_today.get("kecamatan", "") or "").strip().casefold()
            lp_w = str(locked_point_today.get("warkop", "") or "").strip().casefold()
            if (lp_kc, lp_w) in saved_contact_pairs_today or lp_w in saved_contact_warkops_names:
                clear_locked_lkk_point(st.session_state["user_spg"])
                locked_point_today = None

        col_banner, col_logout = st.columns([0.8, 0.2])
        with col_banner:
            spv_aktif = st.session_state.get("nama_supervisi_aktif", "").strip()
            st.markdown(
                f"""
                <div class="user-banner">
                    <div class="user-banner-title">
                        <span>👤 {st.session_state['user_spg']}</span>
                        <span class="badge-mode">👀 Supervisi</span>
                    </div>
                    <div class="user-banner-sub">
                        🚗 Plat: <b>{st.session_state['plat_mobil']}</b> &nbsp;•&nbsp; 🏙️ Wilayah: <b>{st.session_state['kota_kab']}</b> &nbsp;•&nbsp; 🧑‍💼 SPV: <b>{spv_aktif or '-'}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_logout:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            if st.button("🚪 Keluar", use_container_width=True):
                st.session_state["logged_in"] = False
                st.session_state["spg_authenticated_name"] = ""
                st.rerun()

        if is_inside_geofence:
            st.success(
                f"📍 **GPS Aktif:** `{user_lat:.6f}`, `{user_lon:.6f}` (±{akurasi_meter}m) — **{st.session_state['kota_kab']}**"
            )
        else:
            st.warning(
                f"⚠️ **Info GPS:** Posisi Anda terdeteksi di luar poligon zona "
                f"{st.session_state['kota_kab']} (Lat: `{user_lat:.6f}`, Lon: `{user_lon:.6f}`)."
            )

        st.markdown('<div class="section-title">📍 Titik Kunjungan Lapangan</div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_sync_1, col_sync_2 = st.columns([0.78, 0.22])
            status_map_sup = load_warkop_visit_status_map()
            with col_sync_1:
                if locked_point_today:
                    st_lock = locked_point_today.get("status_kunjungan", VISIT_STATUS_WAJIB)
                    st.success(
                        f"🔒 **Titik LKK Terkunci Hari Ini:** **{locked_point_today['warkop']}** "
                        f"({locked_point_today['kecamatan']}) • **{st_lock}** • SPG sudah diizinkan menginput di titik ini."
                    )
                else:
                    st.warning(
                        "⚠️ **Titik LKK Belum Di-Save / Di-Lock.** Pilih Kecamatan & Warkop/LKK di bawah, "
                        "lalu klik **🔒 Save Titik LKK** agar SPG dapat mulai menginput."
                    )
            with col_sync_2:
                st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 Refresh", key="btn_refresh_sup_points", use_container_width=True):
                    st.rerun()

            default_kec_idx = 0
            if locked_point_today and locked_point_today.get("kecamatan") in daftar_kecamatan_terjadwal:
                default_kec_idx = daftar_kecamatan_terjadwal.index(locked_point_today["kecamatan"])

            kecamatan_pilihan = st.selectbox(
                f"Kecamatan Tujuan ({st.session_state['kota_kab']})",
                options=daftar_kecamatan_terjadwal,
                index=default_kec_idx,
                help="Kecamatan difilter otomatis sesuai penugasan jadwal hari ini yang dikelola di menu admin.",
            )

            filter_kategori_w = st.radio(
                "Filter Kategori Warkop",
                options=["Semua", VISIT_STATUS_WAJIB, VISIT_STATUS_TIDAK_WAJIB],
                horizontal=True,
                key="sup_filter_kategori_warkop",
            )

            filtered_warkop_list = []
            if not df_master_excel.empty and col_kec_excel and col_warkop_excel:
                mask = (
                    df_master_excel[col_kec_excel].astype(str).str.strip().str.lower()
                    == str(kecamatan_pilihan).strip().lower()
                )
                filtered_df_warkop = df_master_excel[mask]
                if filtered_df_warkop.empty:
                    filtered_df_warkop = df_master_excel.copy()
                raw_wrk_names = filtered_df_warkop[col_warkop_excel].dropna().astype(str).str.strip().tolist()
                seen_w = set()
                kc_cf = str(kecamatan_pilihan).strip().casefold()
                for w_item in raw_wrk_names:
                    w_cf = w_item.casefold()
                    if not w_item or w_cf in seen_w:
                        continue
                    seen_w.add(w_cf)
                    # Hilangkan warkop yang sudah disimpan datanya lewat Save Jumlah Kontak Konsumen hari ini
                    if (kc_cf, w_cf) in saved_contact_pairs_today or w_cf in saved_contact_warkops_names:
                        continue
                    st_item = get_warkop_visit_status(st.session_state["kota_kab"], kecamatan_pilihan, w_item, status_map_sup)
                    if filter_kategori_w != "Semua" and st_item != filter_kategori_w:
                        continue
                    filtered_warkop_list.append(w_item)

            if not filtered_warkop_list:
                st.info(
                    f"ℹ️ Semua warkop pada kategori **{filter_kategori_w}** di **{kecamatan_pilihan}** "
                    "sudah disimpan jumlah kontaknya hari ini (atau belum ada titik tersisa)."
                )
                nama_warkop_manual = ""
                status_warkop_terpilih = "-"
                alamat_warkop_terpilih = "-"
            else:
                default_w_idx = 0
                if locked_point_today and locked_point_today.get("warkop") in filtered_warkop_list:
                    default_w_idx = filtered_warkop_list.index(locked_point_today["warkop"])

                nama_warkop_manual = st.selectbox(
                    f"Warkop / LKK di {kecamatan_pilihan}",
                    options=filtered_warkop_list,
                    index=default_w_idx,
                    format_func=lambda w_name: f"[{'WAJIB' if get_warkop_visit_status(st.session_state['kota_kab'], kecamatan_pilihan, w_name, status_map_sup) == VISIT_STATUS_WAJIB else 'OPSI'}] {w_name}",
                    help="Menampilkan warkop yang belum dikunjungi & disimpan kontaknya hari ini.",
                )
                status_warkop_terpilih = get_warkop_visit_status(
                    st.session_state["kota_kab"], kecamatan_pilihan, nama_warkop_manual, status_map_sup
                )
                alamat_warkop_terpilih = "-"
                if not df_master_excel.empty and col_warkop_excel and col_alamat_excel:
                    match_row = df_master_excel[
                        df_master_excel[col_warkop_excel].astype(str).str.strip() == str(nama_warkop_manual).strip()
                    ]
                    if not match_row.empty:
                        alamat_warkop_terpilih = str(match_row.iloc[0][col_alamat_excel])

                if st.button("🔒 Save Titik LKK (Buka Akses Input SPG)", type="primary", use_container_width=True, key="btn_save_lock_lkk"):
                    saved_lock = save_locked_lkk_point(
                        team_name=st.session_state["user_spg"],
                        point_info={
                            "kota": st.session_state["kota_kab"],
                            "kecamatan": str(kecamatan_pilihan).strip(),
                            "warkop": str(nama_warkop_manual).strip(),
                            "alamat": alamat_warkop_terpilih,
                            "status_kunjungan": status_warkop_terpilih,
                        },
                    )
                    if saved_lock:
                        st.success(
                            f"✅ Titik LKK **{str(nama_warkop_manual).strip()}** ({kecamatan_pilihan} • **{status_warkop_terpilih}**) berhasil di-save & di-lock! "
                            "SPG kini dapat menginput laporan di titik ini."
                        )
                        st.rerun()

            render_address_box(
                kecamatan_pilihan,
                nama_warkop_manual,
                status_warkop_terpilih,
                alamat_warkop_terpilih,
                "(Tidak ada warkop tersisa / belum dipilih)",
            )

        st.markdown("---")
        st.markdown(f"### 👀 Dashboard Monitoring & Entry Supervisi: {st.session_state['user_spg']} (Plat Mobil: {st.session_state['plat_mobil']})")

        sup_nonce = st.session_state.get("sup_kontak_nonce", 0)
        with st.form(f"form_entry_kontak_supervisi_{sup_nonce}"):
            st.markdown("#### 📝 Save Jumlah Kontak Konsumen Tim (Setelah SPG Selesai Jualan)")
            if not str(nama_warkop_manual).strip():
                st.warning("Pilih dan save Titik LKK terlebih dahulu sebelum menyimpan jumlah kontak konsumen.")
            jumlah_kontak_input = st.number_input(
                f"Jumlah Kontak Konsumen Tim di {nama_warkop_manual or 'Titik LKK'}",
                min_value=0,
                step=1,
                value=0,
                key=f"input_jumlah_kontak_sup_{sup_nonce}",
                help="Masukkan jumlah total kontak konsumen tim di titik LKK ini setelah SPG selesai jualan (bersifat tim, tidak dipecah per SPG/brand).",
            )
            btn_simpan_kontak = st.form_submit_button("💾 Save Jumlah Kontak Konsumen", type="primary")

            if btn_simpan_kontak:
                if not str(nama_warkop_manual).strip():
                    st.error("❌ Gagal menyimpan kontak: Titik LKK belum dipilih/disimpan.")
                else:
                    df_sup_db = load_supervisi_database()
                    waktu_wib = datetime.utcnow() + timedelta(hours=7)
                    warkop_saved_clean = str(nama_warkop_manual).strip()
                    new_sup_row = {
                        "Waktu": waktu_wib.strftime("%Y-%m-%d %H:%M:%S"),
                        "Promotor": st.session_state["user_spg"],
                        "Plat_Mobil": st.session_state["plat_mobil"],
                        "Kota_Kab": st.session_state["kota_kab"],
                        "Kecamatan": kecamatan_pilihan,
                        "Warkop_LKK": warkop_saved_clean,
                        "Alamat_Warkop": alamat_warkop_terpilih,
                        "Jumlah_Kontak_Manual": int(jumlah_kontak_input),
                    }
                    df_sup_db = pd.concat([df_sup_db, pd.DataFrame([new_sup_row])], ignore_index=True)
                    save_supervisi_database(df_sup_db)
                    clear_locked_lkk_point(st.session_state["user_spg"])
                    st.session_state["sup_kontak_nonce"] = sup_nonce + 1
                    st.session_state["sup_last_saved_msg"] = (
                        f"✅ Berhasil menyimpan **{jumlah_kontak_input} kontak tim** untuk titik "
                        f"**{warkop_saved_clean}**! Warkop otomatis dihapus dari daftar pilihan hari ini."
                    )
                    st.rerun()

        if st.session_state.get("sup_last_saved_msg"):
            st.success(st.session_state.pop("sup_last_saved_msg"))

        # --- LIST WARKOP WAJIB KUNJUNG YANG BELUM DIKUNJUNGI DI BAWAH DASHBOARD SUPERVISI ---
        st.markdown("#### 📌 List Warkop Wajib Kunjung yang Belum Dikunjungi Hari Ini")
        df_wrk_all_sup = build_warkop_status_dataframe(df_master_excel, status_map_sup)
        unvisited_wajib_sup_rows = []
        if not df_wrk_all_sup.empty:
            wajib_sup_df = df_wrk_all_sup[
                (df_wrk_all_sup["Status Kunjungan"] == VISIT_STATUS_WAJIB)
                & (
                    df_wrk_all_sup["Kecamatan"].astype(str).str.strip().str.casefold()
                    == str(kecamatan_pilihan).strip().casefold()
                )
            ]
            for _, rw in wajib_sup_df.iterrows():
                nm_w = str(rw.get("Nama Warkop / LKK", "") or "").strip()
                kc_w = str(rw.get("Kecamatan", "") or "").strip()
                if (kc_w.casefold(), nm_w.casefold()) in saved_contact_pairs_today or nm_w.casefold() in saved_contact_warkops_names:
                    continue
                unvisited_wajib_sup_rows.append({
                    "Kota": rw.get("Kota", ""),
                    "Kecamatan": kc_w,
                    "Nama Warkop / LKK": nm_w,
                    "Alamat Warkop / LKK": rw.get("Alamat Warkop / LKK", "-"),
                    "Status Kunjungan": VISIT_STATUS_WAJIB,
                })

        if unvisited_wajib_sup_rows:
            st.dataframe(pd.DataFrame(unvisited_wajib_sup_rows), use_container_width=True, hide_index=True)
        else:
            st.success(f"✅ Semua warkop **Wajib Kunjung** di **{kecamatan_pilihan}** hari ini sudah dikunjungi & disimpan kontaknya.")

        st.markdown("---")

        df_all_db = load_database()
        df_sup_db = load_supervisi_database()

        df_current_team_spg = pd.DataFrame()
        if not df_all_db.empty and "Promotor" in df_all_db.columns:
            df_current_team_spg = df_all_db[df_all_db["Promotor"] == st.session_state["user_spg"]].copy()

        df_current_team_sup = pd.DataFrame()
        if not df_sup_db.empty and "Promotor" in df_sup_db.columns:
            df_current_team_sup = df_sup_db[df_sup_db["Promotor"] == st.session_state["user_spg"]].copy()

        today_str_sup = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d")
        harga_konsumen_map = load_harga_konsumen()

        df_team_spg_today = pd.DataFrame()
        if not df_current_team_spg.empty:
            df_current_team_spg["Jumlah_Bungkus"] = pd.to_numeric(
                df_current_team_spg["Jumlah_Bungkus"], errors="coerce"
            ).fillna(0)
            df_current_team_spg["Harga_Konsumen"] = df_current_team_spg["Brand_Rokok"].apply(
                lambda b: get_harga_konsumen_brand(b, harga_konsumen_map)
            )
            df_current_team_spg["Total_Uang_Rp"] = (
                df_current_team_spg["Jumlah_Bungkus"] * df_current_team_spg["Harga_Konsumen"]
            ).astype(int)
            df_team_spg_today = df_current_team_spg[
                df_current_team_spg["Waktu"].astype(str).str.startswith(today_str_sup)
            ].copy()

        df_lkk_active_spg = pd.DataFrame()
        if not df_team_spg_today.empty and str(nama_warkop_manual).strip():
            df_lkk_active_spg = df_team_spg_today[
                df_team_spg_today["Warkop_LKK"].astype(str).str.strip() == str(nama_warkop_manual).strip()
            ]

        kontak_supervisi_team_lkk = 0
        if not df_current_team_sup.empty and str(nama_warkop_manual).strip():
            df_lkk_active_sup = df_current_team_sup[
                (df_current_team_sup["Warkop_LKK"].astype(str).str.strip() == str(nama_warkop_manual).strip())
                & (df_current_team_sup["Waktu"].astype(str).str.startswith(today_str_sup))
            ]
            if not df_lkk_active_sup.empty:
                kontak_supervisi_team_lkk = int(
                    pd.to_numeric(df_lkk_active_sup["Jumlah_Kontak_Manual"], errors="coerce").fillna(0).sum()
                )

        total_bks_2spg_today = int(df_team_spg_today["Jumlah_Bungkus"].sum()) if not df_team_spg_today.empty else 0
        total_uang_2spg_today = int(df_team_spg_today["Total_Uang_Rp"].sum()) if not df_team_spg_today.empty else 0
        spg_2spg_today_list = (
            df_team_spg_today["Nama_SPG"].dropna().astype(str).str.strip().unique().tolist()
            if not df_team_spg_today.empty else []
        )

        st.info(
            f"💵 **Jumlah Uang Terkumpul Hari Ini ({today_str_sup}) — Penjualan 2 SPG:** "
            f"**Rp {total_uang_2spg_today:,}** ({total_bks_2spg_today:,} bungkus • "
            f"SPG: {', '.join(spg_2spg_today_list) if spg_2spg_today_list else 'Belum ada penjualan'})"
        )

        col_mon1, col_mon2, col_mon3, col_mon4 = st.columns(4)
        with col_mon1:
            render_dashboard_card(f'<div class="card-value">{kontak_supervisi_team_lkk}</div>', "Kontak Supervisi Team")
        with col_mon2:
            total_konsumen_beli = len(df_lkk_active_spg)
            render_dashboard_card(f'<div class="card-value">{total_konsumen_beli}</div>', "Konsumen Beli (LKK Ini)")
        with col_mon3:
            render_dashboard_card(
                f'<div class="card-value-green">Rp {total_uang_2spg_today:,}</div>',
                "Uang Terkumpul 2 SPG Hari Ini",
            )
        with col_mon4:
            spg_list_str = ", ".join(spg_2spg_today_list) if spg_2spg_today_list else "Belum ada SPG"
            render_dashboard_card(
                f'<div class="card-value" style="font-size: 1.05rem; padding-top: 6px;">{spg_list_str}</div>',
                "SPG Bertugas Hari Ini",
            )

        st.markdown("---")
        render_rekapitulasi_penjualan_report(
            team_name=st.session_state["user_spg"],
            target_date_str=today_str_sup,
            allow_edit_stok=True,
        )

        st.markdown("---")
        st.markdown(f"#### 📊 Rekapitulasi Combine Per Titik LKK ({st.session_state['user_spg']})")

        df_rekap_sup = pd.DataFrame(columns=["Kecamatan", "Warkop_LKK", "Kontak_Supervisi_Team"])
        if not df_current_team_sup.empty:
            df_current_team_sup["Jumlah_Kontak_Manual"] = pd.to_numeric(df_current_team_sup["Jumlah_Kontak_Manual"], errors="coerce").fillna(0).astype(int)
            df_rekap_sup = (
                df_current_team_sup.groupby(["Kecamatan", "Warkop_LKK"])
                .agg(Kontak_Supervisi_Team=("Jumlah_Kontak_Manual", "sum"))
                .reset_index()
            )

        df_rekap_spg = pd.DataFrame(columns=["Kecamatan", "Warkop_LKK", "Alamat_Warkop", "Jumlah_SPG_Bertugas", "Konsumen_Beli", "Total_Omset_Bungkus", "Total_Uang_Rp"])
        if not df_current_team_spg.empty:
            if "Total_Uang_Rp" not in df_current_team_spg.columns:
                hmap_rekap = load_harga_konsumen()
                df_current_team_spg["Jumlah_Bungkus"] = pd.to_numeric(df_current_team_spg["Jumlah_Bungkus"], errors="coerce").fillna(0)
                df_current_team_spg["Total_Uang_Rp"] = (
                    df_current_team_spg["Jumlah_Bungkus"]
                    * df_current_team_spg["Brand_Rokok"].apply(lambda b: get_harga_konsumen_brand(b, hmap_rekap))
                ).astype(int)
            df_rekap_spg = (
                df_current_team_spg.groupby(["Kecamatan", "Warkop_LKK", "Alamat_Warkop"])
                .agg(
                    Jumlah_SPG_Bertugas=("Nama_SPG", lambda x: ", ".join(x.dropna().unique())),
                    Konsumen_Beli=("Nama_Konsumen", "count"),
                    Total_Omset_Bungkus=("Jumlah_Bungkus", "sum"),
                    Total_Uang_Rp=("Total_Uang_Rp", "sum"),
                )
                .reset_index()
            )

        if not df_rekap_sup.empty:
            if df_rekap_spg.empty:
                df_combine_rekap = df_rekap_sup.copy()
                df_combine_rekap["Jumlah_SPG_Bertugas"] = "-"
                df_combine_rekap["Konsumen_Beli"] = 0
                df_combine_rekap["Total_Omset_Bungkus"] = 0
                df_combine_rekap["Total_Uang_Rp"] = 0
                df_combine_rekap["Alamat_Warkop"] = "-"
            else:
                df_combine_rekap = pd.merge(df_rekap_sup, df_rekap_spg, on=["Kecamatan", "Warkop_LKK"], how="left").fillna({
                    "Kontak_Supervisi_Team": 0,
                    "Konsumen_Beli": 0,
                    "Total_Omset_Bungkus": 0,
                    "Total_Uang_Rp": 0,
                    "Jumlah_SPG_Bertugas": "-",
                    "Alamat_Warkop": "-",
                })

            df_combine_rekap["Kontak_Supervisi_Team"] = df_combine_rekap["Kontak_Supervisi_Team"].astype(int)
            df_combine_rekap["Konsumen_Beli"] = df_combine_rekap["Konsumen_Beli"].astype(int)
            df_combine_rekap["Total_Omset_Bungkus"] = df_combine_rekap["Total_Omset_Bungkus"].astype(int)
            df_combine_rekap["Total_Uang_Rp"] = df_combine_rekap["Total_Uang_Rp"].astype(int)
            df_combine_rekap = df_combine_rekap[
                ["Kecamatan", "Warkop_LKK", "Alamat_Warkop", "Jumlah_SPG_Bertugas", "Kontak_Supervisi_Team", "Konsumen_Beli", "Total_Omset_Bungkus", "Total_Uang_Rp"]
            ].sort_values(by="Total_Omset_Bungkus", ascending=False)
            st.dataframe(format_sales_table(df_combine_rekap), use_container_width=True)
        else:
            st.info("Titik LKK akan tampil di rekap setelah Supervisi menginput jumlah kontak.")

        st.markdown("#### 📑 Log Detail Transaksi Konsumen Beli (SPG) di Warkop Ini")
        if not df_lkk_active_spg.empty:
            st.dataframe(
                format_sales_table(df_lkk_active_spg.drop(columns=["Waktu", "Promotor", "Plat_Mobil"], errors="ignore")),
                use_container_width=True,
            )
        else:
            st.info(f"Belum ada data konsumen beli masuk untuk titik Warkop / LKK '{nama_warkop_manual or '-'}'.")

        st.stop()

    # ====================================================
    # MODE SPG (HEADER DI ATAS SENDIRI, FORM INPUT, TITIK LKK HIDE/UNHIDE DEFAULT HIDE)
    # ====================================================
    today_wib_spg = (datetime.utcnow() + timedelta(hours=7)).date()
    today_str_spg = today_wib_spg.strftime("%Y-%m-%d")
    sektor_aktif_spg = locked_point_today["kecamatan"] if locked_point_today else st.session_state.get("sektor_terjadwal_login", "")
    personnel_spg_today = get_scheduled_personnel_for_team(
        st.session_state["user_spg"],
        today_wib_spg,
        selected_kecamatan=sektor_aktif_spg,
    )
    daftar_spg_terjadwal = personnel_spg_today.get("spg_all", []) or st.session_state.get("spg_terjadwal_list", [])
    spg_locked_session = str(st.session_state.get("spg_authenticated_name") or "").strip()

    if spg_locked_session:
        nama_spg_manual = spg_locked_session
    elif daftar_spg_terjadwal:
        nama_spg_manual = daftar_spg_terjadwal[0]
    else:
        daftar_master_spg = load_master_spgs()
        nama_spg_manual = daftar_master_spg[0] if daftar_master_spg else "SPG"

    if locked_point_today:
        kecamatan_pilihan = locked_point_today["kecamatan"] or "-"
        nama_warkop_manual = locked_point_today["warkop"]
        alamat_warkop_terpilih = locked_point_today["alamat"]
        status_warkop_terpilih = locked_point_today.get("status_kunjungan", VISIT_STATUS_WAJIB)
    else:
        kecamatan_pilihan = "-"
        nama_warkop_manual = ""
        alamat_warkop_terpilih = "-"
        status_warkop_terpilih = "-"

    has_locked_lkk = locked_point_today is not None and str(nama_warkop_manual).strip() != ""

    # --- 1. HEADER TETAP DI ATAS SENDIRI ---
    col_banner, col_logout = st.columns([0.8, 0.2])
    with col_banner:
        spg_sesi_aktif = st.session_state.get("spg_authenticated_name", "").strip()
        spg_list_aktif = st.session_state.get("spg_terjadwal_list", [])
        personel_badge = f" &nbsp;•&nbsp; 👩‍💼 SPG Terkunci: <b>{spg_sesi_aktif or (', '.join(spg_list_aktif) if spg_list_aktif else nama_spg_manual)}</b>"
        st.markdown(
            f"""
            <div class="user-banner">
                <div class="user-banner-title">
                    <span>👤 {st.session_state['user_spg']}</span>
                    <span class="badge-mode">📝 SPG</span>
                </div>
                <div class="user-banner-sub">
                    🚗 Plat: <b>{st.session_state['plat_mobil']}</b> &nbsp;•&nbsp; 🏙️ Wilayah: <b>{st.session_state['kota_kab']}</b>{personel_badge}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_logout:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["spg_authenticated_name"] = ""
            st.session_state["show_titik_lkk_spg"] = False
            st.rerun()

    # --- 2. FORM INPUT KONSUMEN ---
    if not has_locked_lkk:
        st.error(
            "🔒 **Form Input SPG Terkunci:** Supervisi belum memilih dan menyimpan (**Save Titik LKK**) titik lokasi LKK hari ini. "
            "Silakan tunggu Supervisi me-lock titik LKK lalu tampilkan **📍 Titik Kunjungan Lapangan** di bawah untuk menekan **🔄 Refresh**."
        )
    elif is_inside_geofence and str(nama_spg_manual).strip() != "":
        if st.session_state.get("spg_last_saved_msg"):
            st.balloons()
            st.success(st.session_state.pop("spg_last_saved_msg"))

        spg_nonce = st.session_state.get("spg_form_nonce", 0)
        with st.form(f"form_laporan_spg_{spg_nonce}"):
            st.markdown("### 📝 Form Input Laporan Konsumen")
            st.caption(
                f"Team: **{st.session_state['user_spg']}** • SPG: **{str(nama_spg_manual).strip()}** • "
                f"Titik Terkunci: **{str(nama_warkop_manual).strip()}**"
            )

            all_master_brands = load_master_brands()
            team_brands_map = load_master_team_brands()
            team_names_map = load_master_team_names()
            allowed_brands_for_team = resolve_team_allowed_brands(
                team_name=st.session_state["user_spg"],
                all_brands=all_master_brands,
                team_brands_map=team_brands_map,
                team_names_map=team_names_map,
                prefer_keyword_match=True,
            )
            if not allowed_brands_for_team:
                allowed_brands_for_team = all_master_brands

            default_brand_idx = (
                allowed_brands_for_team.index(st.session_state["draft_brand"])
                if st.session_state.get("draft_brand") in allowed_brands_for_team
                else 0
            )
            gender_options = ["L", "P"]
            default_gender_idx = (
                gender_options.index(st.session_state["draft_gender"])
                if st.session_state.get("draft_gender") in gender_options
                else 0
            )
            age_options = ["", "18-24", "25-30", "31-35", "36-44", "45+"]
            default_age_idx = (
                age_options.index(st.session_state["draft_range_umur"])
                if st.session_state.get("draft_range_umur") in age_options
                else 0
            )

            col_f1, col_f2 = st.columns([1.3, 0.7])
            with col_f1:
                brand_entry = st.selectbox(
                    "🚬 Brand Rokok",
                    options=allowed_brands_for_team,
                    index=default_brand_idx,
                    key=f"spg_brand_{spg_nonce}",
                    help="Daftar merek rokok disesuaikan dengan alokasi Master Team Admin",
                )
            with col_f2:
                jumlah_bungkus = st.number_input(
                    "📦 Jumlah Bungkus",
                    min_value=0,
                    step=1,
                    value=int(st.session_state.get("draft_bungkus", 0) or 0),
                    key=f"spg_bungkus_{spg_nonce}",
                )

            nama_konsumen = st.text_input(
                "👤 Nama Konsumen",
                value=st.session_state["draft_konsumen"],
                placeholder="Masukkan nama konsumen",
                key=f"spg_konsumen_{spg_nonce}",
            )

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                gender_entry = st.radio(
                    "⚧️ Gender",
                    gender_options,
                    index=default_gender_idx,
                    horizontal=True,
                    key=f"spg_gender_{spg_nonce}",
                )
            with col_g2:
                range_umur_entry = st.selectbox(
                    "🎂 Range Umur",
                    options=age_options,
                    index=default_age_idx,
                    format_func=lambda x: "-- Pilih Range Umur --" if x == "" else x,
                    key=f"spg_umur_{spg_nonce}",
                )

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nohp_entry = st.text_input(
                    "📱 No HP",
                    value=st.session_state["draft_nohp"],
                    placeholder="081234567890",
                    key=f"spg_nohp_{spg_nonce}",
                )
            with col_c2:
                instagram_input = st.text_input(
                    "📸 Instagram",
                    value=st.session_state["draft_ig"],
                    placeholder="username_ig",
                    key=f"spg_ig_{spg_nonce}",
                )

            rokok_asal_bumo = st.text_input(
                "🔄 Rokok Asal (BUMO)",
                value=st.session_state["draft_bumo"],
                placeholder="Merk rokok yang biasa dikonsumsi sebelumnya",
                key=f"spg_bumo_{spg_nonce}",
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_save_draft = st.form_submit_button("💾 Simpan Draft", type="secondary", use_container_width=True)
            with col_btn2:
                btn_kirim = st.form_submit_button("🚀 Kirim Laporan", type="primary", use_container_width=True)

            if btn_save_draft:
                st.session_state["draft_brand"] = brand_entry
                st.session_state["draft_gender"] = gender_entry
                st.session_state["draft_range_umur"] = range_umur_entry
                st.session_state["draft_konsumen"] = nama_konsumen
                st.session_state["draft_nohp"] = nohp_entry
                st.session_state["draft_ig"] = instagram_input
                st.session_state["draft_bungkus"] = jumlah_bungkus
                st.session_state["draft_bumo"] = rokok_asal_bumo
                st.info("💾 Draft laporan berhasil diamankan ke memori sesi sementara!")

            if btn_kirim:
                if not nama_konsumen.strip():
                    st.warning("Mohon isi nama konsumen.")
                elif int(jumlah_bungkus) <= 0:
                    st.warning("Jumlah bungkus harus lebih dari 0.")
                else:
                    ig_formatted = f"@{instagram_input.strip().lstrip('@')}" if instagram_input.strip() else "-"
                    waktu_wib = datetime.utcnow() + timedelta(hours=7)
                    data_baru = {
                        "Waktu": waktu_wib.strftime("%Y-%m-%d %H:%M:%S"),
                        "Promotor": st.session_state["user_spg"],
                        "Plat_Mobil": st.session_state["plat_mobil"],
                        "Nama_SPG": str(nama_spg_manual).strip(),
                        "Kota_Kab": st.session_state["kota_kab"],
                        "Kecamatan": kecamatan_pilihan,
                        "Warkop_LKK": str(nama_warkop_manual).strip(),
                        "Alamat_Warkop": alamat_warkop_terpilih,
                        "Brand_Rokok": brand_entry,
                        "Nama_Konsumen": nama_konsumen.strip(),
                        "Gender": gender_entry,
                        "Range_Umur": range_umur_entry,
                        "No_HP": nohp_entry.strip(),
                        "Instagram": ig_formatted,
                        "Jumlah_Bungkus": int(jumlah_bungkus),
                        "Rokok_Asal_BUMO": rokok_asal_bumo.strip(),
                        "Latitude": user_lat,
                        "Longitude": user_lon,
                    }
                    df_all = load_database()
                    df_new_row = pd.DataFrame([data_baru])
                    df_all = pd.concat([df_all, df_new_row], ignore_index=True)
                    save_database(df_all)

                    st.session_state["draft_konsumen"] = ""
                    st.session_state["draft_nohp"] = ""
                    st.session_state["draft_ig"] = ""
                    st.session_state["draft_bungkus"] = 0
                    st.session_state["draft_bumo"] = ""
                    st.session_state["draft_brand"] = ""
                    st.session_state["draft_gender"] = "L"
                    st.session_state["draft_range_umur"] = ""
                    st.session_state["spg_form_nonce"] = spg_nonce + 1
                    st.session_state["spg_last_saved_msg"] = (
                        f"Laporan konsumen '{nama_konsumen.strip()}' ({jumlah_bungkus} bks {brand_entry}) berhasil disimpan!"
                    )
                    st.rerun()

    # --- 3. BLOK TITIK KUNJUNGAN LAPANGAN (DEFAULT HIDE / UNHIDE) ---
    st.markdown("---")
    col_titik_hdr, col_titik_toggle = st.columns([0.65, 0.35])
    with col_titik_hdr:
        st.markdown('<div class="section-title" style="margin:0;">📍 Titik Kunjungan Lapangan</div>', unsafe_allow_html=True)
    with col_titik_toggle:
        is_titik_shown = bool(st.session_state.get("show_titik_lkk_spg", False))
        toggle_label = "🙈 Hide Titik LKK" if is_titik_shown else "👁️ Unhide Titik LKK"
        if st.button(toggle_label, key="btn_toggle_titik_lkk_spg", use_container_width=True):
            st.session_state["show_titik_lkk_spg"] = not is_titik_shown
            st.rerun()

    if st.session_state.get("show_titik_lkk_spg", False):
        with st.container(border=True):
            col_spg_ref1, col_spg_ref2 = st.columns([0.78, 0.22])
            with col_spg_ref1:
                if has_locked_lkk:
                    st.success(
                        f"🔒 **Titik LKK Terkunci oleh Supervisi:** **{nama_warkop_manual}** "
                        f"({kecamatan_pilihan} • **{status_warkop_terpilih}**)"
                    )
                else:
                    st.warning(
                        "⚠️ **Belum ada Titik LKK yang di-save / di-lock Supervisi hari ini.** "
                        "Klik **🔄 Refresh** setelah Supervisi menyimpan Titik LKK."
                    )
            with col_spg_ref2:
                st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 Refresh", key="btn_refresh_spg_locked_lkk", use_container_width=True):
                    st.rerun()

            render_address_box(
                kecamatan_pilihan,
                nama_warkop_manual,
                status_warkop_terpilih,
                alamat_warkop_terpilih,
                "(Belum di-lock Supervisi)",
            )

    # --- 4. RINGKASAN PERFORMA ---
    st.markdown("---")
    st.markdown(f"### 📈 Ringkasan Performa: {st.session_state['user_spg']} ({nama_spg_manual or 'Semua SPG'})")

    df_all = load_database()
    if not df_all.empty and "Promotor" in df_all.columns:
        df_user = df_all[df_all["Promotor"] == st.session_state["user_spg"]].copy()
    else:
        df_user = pd.DataFrame(columns=EXPECTED_COLUMNS)

    if not df_user.empty:
        df_user["Waktu_Dt"] = pd.to_datetime(df_user["Waktu"], errors="coerce")
        df_user["Tanggal"] = df_user["Waktu_Dt"].dt.strftime("%d-%m-%Y")
        df_user = add_custom_week_columns(df_user, "Waktu_Dt")
        df_user["Jumlah_Bungkus"] = pd.to_numeric(df_user["Jumlah_Bungkus"], errors="coerce").fillna(0)

        today_dt = datetime.utcnow() + timedelta(hours=7)
        today_str = today_dt.strftime("%d-%m-%Y")
        current_week_label, _ = get_custom_week_info(today_dt)
        current_month_str = today_dt.strftime("%m-%Y")

        df_today_u = df_user[df_user["Tanggal"] == today_str].copy()
        omset_hari_ini_u = int(df_today_u["Jumlah_Bungkus"].sum())
        konsumen_hari_ini_u = len(df_today_u)

        if not df_today_u.empty:
            df_today_u_lb = (
                df_today_u.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok"])
                .agg(Total_Omset_Team=("Jumlah_Bungkus", "sum"))
                .reset_index()
            )
            df_today_u_lb["Brand_Rokok_Clean"] = df_today_u_lb["Brand_Rokok"].apply(clean_brand_target_name)
            df_today_u_lb = (
                df_today_u_lb.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok_Clean"])
                .agg(Total_Omset_Team=("Total_Omset_Team", "sum"))
                .reset_index()
                .rename(columns={"Brand_Rokok_Clean": "Brand_Rokok"})
            )
            df_today_u_lb["Target_Team"] = df_today_u_lb["Brand_Rokok"].apply(
                lambda brand: get_target_for_brand(brand, "target_team", 50)
            )
            target_hari_ini_u = int(df_today_u_lb["Target_Team"].sum())
        else:
            target_hari_ini_u = 100

        if target_hari_ini_u <= 0:
            target_hari_ini_u = 100

        persen_pencapaian_u = int((omset_hari_ini_u / target_hari_ini_u) * 100) if target_hari_ini_u > 0 else 0

        df_week_u = df_user[df_user["Periode_Minggu"] == current_week_label]
        omset_minggu_ini_u = int(df_week_u["Jumlah_Bungkus"].sum())
        konsumen_minggu_ini_u = len(df_week_u)

        df_user["Bulan_Tahun"] = df_user["Waktu_Dt"].dt.strftime("%m-%Y")
        df_month_u = df_user[df_user["Bulan_Tahun"] == current_month_str]
        omset_bulan_ini_u = int(df_month_u["Jumlah_Bungkus"].sum())
        konsumen_bulan_ini_u = len(df_month_u)

        kpi_u1, kpi_u2, kpi_u3 = st.columns(3)
        with kpi_u1:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{omset_hari_ini_u:,} bks</div>
                    <div class="card-subtext">dari {target_hari_ini_u} target bks</div>
                </div>""",
                "Omset Hari Ini",
            )
        with kpi_u2:
            bar_w_u = min(persen_pencapaian_u, 100)
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value-green">{persen_pencapaian_u}%</div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: {bar_w_u}%;"></div>
                    </div>
                </div>""",
                "Pencapaian Omset Hari Ini",
            )
        with kpi_u3:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{konsumen_hari_ini_u:,}</div>
                    <div class="card-subtext" style="opacity: 0;">-</div>
                </div>""",
                "Konsumen Beli Hari Ini",
            )

        kpi_u4, kpi_u5, kpi_u6 = st.columns(3)
        with kpi_u4:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{omset_minggu_ini_u:,} bks</div>
                    <div class="card-subtext">{konsumen_minggu_ini_u:,} Konsumen Minggu Ini</div>
                </div>""",
                "Omset Minggu Ini",
            )
        with kpi_u5:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{omset_bulan_ini_u:,} bks</div>
                    <div class="card-subtext" style="opacity: 0;">-</div>
                </div>""",
                "Omset Bulan Ini",
            )
        with kpi_u6:
            render_dashboard_card(
                f"""
                <div>
                    <div class="card-value">{konsumen_bulan_ini_u:,}</div>
                    <div class="card-subtext" style="opacity: 0;">-</div>
                </div>""",
                "Konsumen Beli Bulan Ini",
            )

        all_weeks_u = sorted(df_user["Periode_Minggu"].dropna().unique().tolist(), reverse=True)
        all_dates_u = sorted(df_user["Tanggal"].dropna().unique().tolist(), reverse=True)
        all_spgs_u = sorted(df_user["Nama_SPG"].dropna().unique().tolist())

        st.markdown("---")
        st.markdown("### 👩‍💼 Pencapaian Per SPG (Berdasarkan Target SPG)")

        col_spg_w, col_spg_tgl, col_spg_nm = st.columns(3)
        with col_spg_w:
            filter_spg_week = st.multiselect("Filter Periode Minggu (Pencapaian SPG)", options=all_weeks_u, default=all_weeks_u, key="user_spg_week")
        with col_spg_tgl:
            filter_spg_tgl = st.multiselect("Filter Tanggal (Pencapaian SPG)", options=all_dates_u, default=all_dates_u, key="user_spg_tgl")
        with col_spg_nm:
            filter_spg_nm = st.multiselect("Filter Nama SPG (Pencapaian SPG)", options=all_spgs_u, default=all_spgs_u, key="user_spg_nm")

        df_spg_filtered = df_user.copy()
        if filter_spg_week:
            df_spg_filtered = df_spg_filtered[df_spg_filtered["Periode_Minggu"].isin(filter_spg_week)]
        if filter_spg_tgl:
            df_spg_filtered = df_spg_filtered[df_spg_filtered["Tanggal"].isin(filter_spg_tgl)]
        if filter_spg_nm:
            df_spg_filtered = df_spg_filtered[df_spg_filtered["Nama_SPG"].isin(filter_spg_nm)]

        if not df_spg_filtered.empty:
            df_spg_achievement = (
                df_spg_filtered.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Nama_SPG", "Kota_Kab", "Brand_Rokok"])
                .agg(Total_Omset_SPG=("Jumlah_Bungkus", "sum"), Total_Konsumen_Beli=("Nama_Konsumen", "count"))
                .reset_index()
            )
            df_spg_achievement["Brand_Rokok_Clean"] = df_spg_achievement["Brand_Rokok"].apply(clean_brand_target_name)
            df_spg_achievement = (
                df_spg_achievement.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Nama_SPG", "Kota_Kab", "Brand_Rokok_Clean"])
                .agg(Total_Omset_SPG=("Total_Omset_SPG", "sum"), Total_Konsumen_Beli=("Total_Konsumen_Beli", "sum"))
                .reset_index()
                .rename(columns={"Brand_Rokok_Clean": "Brand_Rokok"})
            )
            df_spg_achievement["Target_SPG"] = df_spg_achievement["Brand_Rokok"].apply(
                lambda brand: get_target_for_brand(brand, "target_spg", 25)
            )
            df_spg_achievement["Status_Target_SPG"] = df_spg_achievement.apply(
                lambda r: "Achieved" if r["Total_Omset_SPG"] >= r["Target_SPG"] else "Not Achieved",
                axis=1
            )
            cols_spg_order = ["Tanggal", "Periode_Minggu", "Promotor", "Nama_SPG", "Kota_Kab", "Brand_Rokok", "Total_Omset_SPG", "Total_Konsumen_Beli", "Target_SPG", "Status_Target_SPG"]
            df_spg_achievement = df_spg_achievement[[c for c in cols_spg_order if c in df_spg_achievement.columns]]

            st.dataframe(
                format_sales_table(
                    df_spg_achievement.style.map(style_status_target, subset=["Status_Target_SPG"])
                ),
                use_container_width=True,
            )
        else:
            st.info("Tidak ada data untuk filter Pencapaian SPG yang dipilih.")

        st.markdown("---")
        st.markdown("### 🏆 Pencapaian Team SPG (Berdasarkan Target Team)")

        col_tm_w, col_tm_tgl = st.columns(2)
        with col_tm_w:
            filter_tm_week = st.multiselect("Filter Periode Minggu (Pencapaian Team)", options=all_weeks_u, default=all_weeks_u, key="user_tm_week")
        with col_tm_tgl:
            filter_tm_tgl = st.multiselect("Filter Tanggal (Pencapaian Team)", options=all_dates_u, default=all_dates_u, key="user_tm_tgl")

        df_tm_filtered = df_user.copy()
        if filter_tm_week:
            df_tm_filtered = df_tm_filtered[df_tm_filtered["Periode_Minggu"].isin(filter_tm_week)]
        if filter_tm_tgl:
            df_tm_filtered = df_tm_filtered[df_tm_filtered["Tanggal"].isin(filter_tm_tgl)]

        if not df_tm_filtered.empty:
            df_tm_achievement = (
                df_tm_filtered.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok"])
                .agg(Total_Omset_Team=("Jumlah_Bungkus", "sum"), Total_Konsumen_Beli=("Nama_Konsumen", "count"))
                .reset_index()
            )
            df_tm_achievement["Brand_Rokok_Clean"] = df_tm_achievement["Brand_Rokok"].apply(clean_brand_target_name)
            df_tm_achievement = (
                df_tm_achievement.groupby(["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok_Clean"])
                .agg(Total_Omset_Team=("Total_Omset_Team", "sum"), Total_Konsumen_Beli=("Total_Konsumen_Beli", "sum"))
                .reset_index()
                .rename(columns={"Brand_Rokok_Clean": "Brand_Rokok"})
            )
            df_tm_achievement["Target_Team"] = df_tm_achievement["Brand_Rokok"].apply(
                lambda brand: get_target_for_brand(brand, "target_team", 50)
            )
            df_tm_achievement["Status_Target_Team"] = df_tm_achievement.apply(
                lambda r: "Achieved" if r["Total_Omset_Team"] >= r["Target_Team"] else "Not Achieved",
                axis=1
            )
            cols_tm_order = ["Tanggal", "Periode_Minggu", "Promotor", "Kota_Kab", "Brand_Rokok", "Total_Omset_Team", "Total_Konsumen_Beli", "Target_Team", "Status_Target_Team"]
            df_tm_achievement = df_tm_achievement[[c for c in cols_tm_order if c in df_tm_achievement.columns]]

            st.dataframe(
                format_sales_table(
                    df_tm_achievement.style.map(style_status_target, subset=["Status_Target_Team"])
                ),
                use_container_width=True,
            )
        else:
            st.info("Tidak ada data untuk filter Pencapaian Team yang dipilih.")

        st.markdown("---")
        st.markdown("### 📑 Riwayat Laporan Anda")
        st.dataframe(
            format_sales_table(
                df_user.drop(
                    columns=["Waktu_Dt", "Periode_Minggu", "Tanggal", "Bulan_Tahun"],
                    errors="ignore",
                ).tail(20)
            ),
            use_container_width=True,
        )
    else:
        st.info("Belum ada data laporan untuk akun ini.")

    st.markdown("""
    <div class="footer-note">
        © 2026 Tumarso Monitoring System
    </div>
    """, unsafe_allow_html=True)
