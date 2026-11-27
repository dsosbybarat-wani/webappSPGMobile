import hashlib
import hmac
import json
import os

import streamlit as st

from config.constants import DEFAULT_SPG_PIN, DEFAULT_SUPERVISI_PIN, MASTER_AKSES_FILE
from core.storage import _read_json_safe


def _hash_pin(pin_plain: str) -> str:
    return hashlib.sha256(str(pin_plain or "").strip().encode("utf-8")).hexdigest()


def load_master_akses() -> dict:
    """Load PIN/access settings by role and person."""
    data = _read_json_safe(MASTER_AKSES_FILE)
    base = {
        "supervisi_default_pin": DEFAULT_SUPERVISI_PIN,
        "spg_default_pin": DEFAULT_SPG_PIN,
        "require_spg_pin": False,
        "supervisi_pins": {},
        "spg_pins": {},
    }
    if isinstance(data, dict):
        base["supervisi_default_pin"] = str(data.get("supervisi_default_pin") or DEFAULT_SUPERVISI_PIN).strip()
        base["spg_default_pin"] = str(data.get("spg_default_pin") or DEFAULT_SPG_PIN).strip()
        base["require_spg_pin"] = bool(data.get("require_spg_pin", False))
        if isinstance(data.get("supervisi_pins"), dict):
            base["supervisi_pins"] = {
                str(key).strip(): str(value).strip()
                for key, value in data["supervisi_pins"].items()
                if str(key).strip() and str(value).strip()
            }
        if isinstance(data.get("spg_pins"), dict):
            base["spg_pins"] = {
                str(key).strip(): str(value).strip()
                for key, value in data["spg_pins"].items()
                if str(key).strip() and str(value).strip()
            }
    return base


def save_master_akses(akses_cfg: dict) -> bool:
    payload = {
        "supervisi_default_pin": str(akses_cfg.get("supervisi_default_pin") or DEFAULT_SUPERVISI_PIN).strip(),
        "spg_default_pin": str(akses_cfg.get("spg_default_pin") or DEFAULT_SPG_PIN).strip(),
        "require_spg_pin": bool(akses_cfg.get("require_spg_pin", False)),
        "supervisi_pins": {
            str(key).strip(): str(value).strip()
            for key, value in (akses_cfg.get("supervisi_pins") or {}).items()
            if str(key).strip() and str(value).strip()
        },
        "spg_pins": {
            str(key).strip(): str(value).strip()
            for key, value in (akses_cfg.get("spg_pins") or {}).items()
            if str(key).strip() and str(value).strip()
        },
    }
    with open(MASTER_AKSES_FILE, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    st.cache_data.clear()
    return True


def verify_user_pin(role: str, person_name: str, entered_pin: str, akses_cfg: dict | None = None) -> bool:
    cfg = akses_cfg if isinstance(akses_cfg, dict) else load_master_akses()
    pin_in = str(entered_pin or "").strip()
    if not pin_in:
        return False

    role_norm = str(role or "").strip().casefold()
    person_key = str(person_name or "").strip().casefold()

    if role_norm == "supervisi":
        expected = cfg.get("supervisi_default_pin", DEFAULT_SUPERVISI_PIN)
        for key, value in cfg.get("supervisi_pins", {}).items():
            if str(key).strip().casefold() == person_key and str(value).strip():
                expected = str(value).strip()
                break
        return hmac.compare_digest(_hash_pin(pin_in), _hash_pin(expected))

    if role_norm == "spg":
        expected = cfg.get("spg_default_pin", DEFAULT_SPG_PIN)
        for key, value in cfg.get("spg_pins", {}).items():
            if str(key).strip().casefold() == person_key and str(value).strip():
                expected = str(value).strip()
                break
        return hmac.compare_digest(_hash_pin(pin_in), _hash_pin(expected))

    return False


def verify_admin_password(entered_password: str) -> bool:
    try:
        expected = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", "admin123"))
    except FileNotFoundError:
        expected = os.environ.get("ADMIN_PASSWORD", "admin123")
    return hmac.compare_digest(str(entered_password or ""), str(expected or ""))


def reset_session_on_user_change():
    st.session_state["logged_in"] = False
    st.session_state["user_spg"] = st.session_state.get("selected_team_login", "")
    st.session_state["nama_supervisi_aktif"] = ""
    st.session_state["spg_terjadwal_list"] = []
    st.session_state["sektor_terjadwal_login"] = ""
    st.session_state["spg_authenticated_name"] = ""
    st.session_state["show_titik_lkk_spg"] = False
    st.session_state["draft_konsumen"] = ""
    st.session_state["draft_nohp"] = ""
    st.session_state["draft_ig"] = ""
    st.session_state["draft_bungkus"] = 0
    st.session_state["draft_bumo"] = ""
    st.session_state["draft_brand"] = ""
    st.session_state["draft_gender"] = "L"
    st.session_state["draft_range_umur"] = ""
    st.session_state["spg_form_nonce"] = st.session_state.get("spg_form_nonce", 0) + 1
    st.session_state["sup_kontak_nonce"] = st.session_state.get("sup_kontak_nonce", 0) + 1
