import json
import os
import re

import geopandas as gpd
import pandas as pd
import streamlit as st

from config.constants import GEOJSON_INDEX_FILE, KECAMATAN_BY_KOTA
from core.storage import _cached_read_json, _file_mtime


@st.cache_data(ttl=3600, show_spinner=False)
def _get_kecamatan_filepath_map() -> dict:
    """Cache mapping kecamatan names to their GeoJSON files."""
    result = {}
    if os.path.exists(GEOJSON_INDEX_FILE):
        try:
            index = _cached_read_json(GEOJSON_INDEX_FILE, _file_mtime(GEOJSON_INDEX_FILE))
            if isinstance(index, dict):
                for key, value in index.items():
                    if isinstance(value, dict) and value.get("file"):
                        result[str(key).strip().casefold()] = value["file"]
        except Exception:
            pass
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def load_geojson_index(mtime: float = 0.0) -> dict:
    if os.path.exists(GEOJSON_INDEX_FILE):
        try:
            raw_index = _cached_read_json(GEOJSON_INDEX_FILE, _file_mtime(GEOJSON_INDEX_FILE))
            if isinstance(raw_index, dict):
                return {
                    str(key).strip().casefold(): {"nm_kecamatan": str(key).strip(), **value}
                    for key, value in raw_index.items()
                    if isinstance(value, dict)
                }
        except Exception:
            pass
    return {}


def _resolve_kecamatan_filepath(nm_kecamatan: str) -> str | None:
    if not nm_kecamatan:
        return None
    target = str(nm_kecamatan).strip()
    file_map = _get_kecamatan_filepath_map()
    candidate = file_map.get(target.casefold())
    if candidate:
        if os.path.exists(candidate):
            return candidate
        base_candidate = os.path.join("geojson_by_kecamatan", os.path.basename(candidate))
        if os.path.exists(base_candidate):
            return base_candidate
    slug = re.sub(r"[^a-z0-9]+", "_", target.lower()).strip("_")
    fallback_path = os.path.join("geojson_by_kecamatan", f"{slug}.geojson")
    if os.path.exists(fallback_path):
        return fallback_path
    return None


@st.cache_data(ttl=3600, max_entries=40, show_spinner=False)
def load_kecamatan_geojson(nm_kecamatan: str, mtime: float = 0.0) -> dict | None:
    filepath = _resolve_kecamatan_filepath(nm_kecamatan)
    if not filepath:
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        st.error(f"Gagal memuat GeoJSON kecamatan '{nm_kecamatan}': {exc}")
        return None


@st.cache_data(ttl=3600, max_entries=40, show_spinner=False)
def load_kecamatan_gdf(nm_kecamatan: str, mtime: float = 0.0):
    data = load_kecamatan_geojson(nm_kecamatan, mtime)
    if not data:
        return None
    try:
        gdf = gpd.GeoDataFrame.from_features(data)
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)
        return gdf
    except Exception as exc:
        st.error(f"Gagal memproses geometri kecamatan '{nm_kecamatan}': {exc}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def build_polygon_features(kecamatan_tuple: tuple) -> list:
    """Build combined PyDeck features for the selected districts."""
    gresik_set = {name.casefold() for name in KECAMATAN_BY_KOTA["Gresik"]}
    features = []
    for kecamatan_name in kecamatan_tuple:
        geojson = load_kecamatan_geojson(kecamatan_name)
        if not geojson or not isinstance(geojson.get("features"), list):
            continue
        is_gresik = kecamatan_name.strip().casefold() in gresik_set
        fill_color = [16, 185, 129, 35] if is_gresik else [30, 144, 255, 35]
        line_color = [5, 150, 105, 210] if is_gresik else [37, 99, 235, 210]
        city_label = "Gresik" if is_gresik else "Surabaya"
        for feature in geojson["features"]:
            properties = dict(feature.get("properties") or {})
            properties.setdefault("Kota_Wilayah", city_label)
            properties["fill_color"] = fill_color
            properties["line_color"] = line_color
            features.append({
                "type": "Feature",
                "properties": properties,
                "geometry": feature.get("geometry"),
            })
    return features


def load_master_wilayah(kota, kecamatan_list=None):
    city = str(kota or "").strip().casefold()
    if city == "surabaya":
        all_districts = KECAMATAN_BY_KOTA["Surabaya"]
    elif city == "gresik":
        all_districts = KECAMATAN_BY_KOTA["Gresik"]
    else:
        return None

    target_districts = (
        [str(name).strip() for name in kecamatan_list if str(name).strip()]
        if kecamatan_list is not None
        else all_districts
    )
    geodataframes = []
    for district in target_districts:
        geodataframe = load_kecamatan_gdf(district)
        if geodataframe is not None and not geodataframe.empty:
            geodataframe_copy = geodataframe.copy()
            if "nm_kecamatan" not in geodataframe_copy.columns:
                geodataframe_copy["nm_kecamatan"] = district
            geodataframes.append(geodataframe_copy)
    if not geodataframes:
        return None
    combined = pd.concat(geodataframes, ignore_index=True)
    return gpd.GeoDataFrame(combined, crs="EPSG:4326")


def is_point_within_city(kota, point) -> bool | None:
    """Check a GPS point against the combined district polygons for a city."""
    city_geodata = load_master_wilayah(kota)
    if city_geodata is None or city_geodata.empty:
        return None

    geometries = city_geodata.geometry.dropna()
    if geometries.empty:
        return None

    city_boundary = geometries.unary_union
    if city_boundary is None or city_boundary.is_empty:
        return None
    return bool(city_boundary.covers(point))


def get_geo_districts(kota: str) -> list[str]:
    """Get district names without loading all polygon data."""
    city = str(kota or "").strip().casefold()
    if city == "surabaya":
        return sorted(KECAMATAN_BY_KOTA["Surabaya"])
    if city == "gresik":
        return sorted(KECAMATAN_BY_KOTA["Gresik"])
    index = load_geojson_index(_file_mtime(GEOJSON_INDEX_FILE))
    return sorted(item["nm_kecamatan"] for item in index.values())
