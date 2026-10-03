"""Konstanta yang dipakai di seluruh aplikasi."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets"

# Warna dasar mengikuti versi sebelumnya
COLORS = {
    "bg": "#05162a",
    "bg2": "#0a2e5c",
    "panel": "#112240",
    "border": "#233554",
    "accent": "#00d2ff",
    "accent2": "#3a7bd5",
    "mint": "#64ffda",
    "text": "#e6f1ff",
    "soft": "#ccd6f6",
    "muted": "#8892b0",
    "danger": "#ff4b4b",
    "warning": "#f5a623",
}

LEVEL_COLORS = {"Tinggi": COLORS["danger"], "Sedang": COLORS["warning"], "Rendah": COLORS["accent"]}

MAP_CENTER = [-3.668, 128.185]
MAP_ZOOM = 13

NAV_ITEMS = [
    "Dashboard",
    "Lapor",
    "Analisis",
    "Pemetaan",
    "Prediksi",
    "Prioritas",
    "Verifikasi",
    "Mikroplastik",
    "Data IKLH",
    "Tentang",
]

KATEGORI_SAMPAH = [
    "Plastik kemasan",
    "Botol plastik",
    "Kantong plastik",
    "Styrofoam",
    "Alat tangkap",
    "Sampah campuran",
]

JUMLAH_BOBOT = {"Sedikit": 1, "Sedang": 3, "Banyak": 6}
