import os


WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzk6tqiNonaArNjJt7X0IIhja_D7elgGLkNPE90xmDtvdHwNeq4VhZJQfUU2OE_jiA/exec"

DB_FILE = "rekap_laporan_spg.csv"
DB_SUPERVISI_KONTAK_FILE = "rekap_kontak_supervisi.csv"
MASTER_BRAND_FILE = "master_brand_rokok.json"
MASTER_TARGET_FILE = "master_target_brand.json"
MASTER_HARGA_FILE = "master_harga_konsumen.json"
STOK_SUPERVISI_FILE = "stok_rokok_supervisi.json"
MASTER_AKSES_FILE = "master_akses_user.json"
MASTER_LOKASI_FILE = "Master WarkopLKK.xlsx"
MASTER_SPG_FILE = "master_nama_spg.json"
MASTER_TEAM_BRAND_FILE = "master_team_brand.json"
MASTER_PLAT_FILE = "master_plat_kendaraan.json"
MASTER_TEAM_NAME_FILE = "master_nama_team.json"
JADWAL_SPG_FILE = "Jadwal SPG.xlsx"
LOCKED_LKK_POINT_FILE = "titik_lkk_aktif_team.json"
WARKOP_VISIT_STATUS_FILE = "status_warkop_kunjungan.json"
GEOJSON_INDEX_FILE = os.path.join("geojson_by_kecamatan", "_index.json")

DEFAULT_SUPERVISI_PIN = "1122"
DEFAULT_SPG_PIN = "2233"

DEFAULT_HARGA_KONSUMEN = {
    "Black Matcha K12": 22000,
    "D.Super 12": 24000,
    "D.Super Kretek": 16000,
    "D.76 Apel Royal": 18000,
    "D.76 Apel": 16000,
    "Djarum 76 Aksara": 16000,
    "Black Matcha Siro": 23000,
    "Black Matcha Kuro": 23000,
}

EXPECTED_COLUMNS = [
    "Waktu",
    "Promotor",
    "Plat_Mobil",
    "Nama_SPG",
    "Kota_Kab",
    "Kecamatan",
    "Warkop_LKK",
    "Alamat_Warkop",
    "Brand_Rokok",
    "Nama_Konsumen",
    "Gender",
    "Range_Umur",
    "No_HP",
    "Instagram",
    "Jumlah_Bungkus",
    "Rokok_Asal_BUMO",
    "Latitude",
    "Longitude",
]

EXPECTED_SUPERVISI_COLUMNS = [
    "Waktu",
    "Promotor",
    "Plat_Mobil",
    "Kota_Kab",
    "Kecamatan",
    "Warkop_LKK",
    "Alamat_Warkop",
    "Jumlah_Kontak_Manual",
]

VISIT_STATUS_WAJIB = "Wajib Kunjung"
VISIT_STATUS_TIDAK_WAJIB = "Opsional"
VISIT_STATUS_OPTIONS = [VISIT_STATUS_WAJIB, VISIT_STATUS_TIDAK_WAJIB]

KECAMATAN_BY_KOTA = {
    "Surabaya": [
        "Asem Rowo", "Benowo", "Bubutan", "Dukuh Pakis", "Genteng",
        "Karang Pilang", "Krembangan", "Lakarsantri", "Pabean Cantian",
        "Pakal", "Sambikerep", "Sawahan", "Sukomanunggal", "Tandes",
        "Tegalsari", "Wiyung",
    ],
    "Gresik": [
        "Balongpanggang", "Benjeng", "Bungah", "Cerme", "Driyorejo",
        "Duduksampeyan", "Dukun", "Gresik", "Kebomas", "Kedamean",
        "Manyar", "Menganti", "Panceng", "Sangkapura", "Sidayu",
        "Tambak", "Ujungpangkah", "Wringinanom",
    ],
}

DEFAULT_BRANDS = [
    "D.Super 12",
    "D.Super Kretek",
    "D.76 Apel",
    "D.76 Apel Royal",
    "Black Matcha K12",
    "Djarum 76 Aksara",
    "Black Matcha Siro",
    "Black Matcha Kuro",
]
DEFAULT_SPGS = ["Nanda"]
DEFAULT_PLATS = ["L 1234 ABC"]

DEFAULT_TARGET_RULES = {
    "Black Matcha K12": {"target_spg": 40, "target_team": 80, "group": "Black_Matcha"},
    "D.Super 12": {"target_spg": 40, "target_team": 80, "group": "D_Super"},
    "D.Super Kretek": {"target_spg": 40, "target_team": 80, "group": "D_Super"},
    "D.76 Apel Royal": {"target_spg": 40, "target_team": 80},
    "D.76 Apel": {"target_spg": 30, "target_team": 60},
    "Djarum 76 Aksara": {"target_spg": 30, "target_team": 60},
    "Black Matcha Siro": {"target_spg": 40, "target_team": 80, "group": "Black_Matcha"},
    "Black Matcha Kuro": {"target_spg": 40, "target_team": 80, "group": "Black_Matcha"},
}

TARGET_GROUP_LABELS = {
    "D_Super": "D. Super (Gabungan)",
    "Black_Matcha": "Black Matcha (Gabungan)",
    "Black_Siro_Kuro": "Black Matcha (Gabungan)",
}
TARGET_GROUP_OPTIONS = {
    "": "Tidak digabungkan",
    "D_Super": TARGET_GROUP_LABELS["D_Super"],
    "Black_Matcha": TARGET_GROUP_LABELS["Black_Matcha"],
}
