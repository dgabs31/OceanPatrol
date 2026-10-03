"""Fungsi geografi sederhana tanpa library tambahan."""

import json
import math
from functools import lru_cache

from core.config import DATA_DIR

METER_PER_DERAJAT = 111_320.0


@lru_cache(maxsize=1)
def load_water_polygon():
    """Membaca polygon perairan Teluk Ambon sebagai list (lat, lon)."""
    with open(DATA_DIR / "teluk_ambon_perairan.geojson", encoding="utf-8") as f:
        gj = json.load(f)
    ring = gj["features"][0]["geometry"]["coordinates"][0]
    return tuple((lat, lon) for lon, lat in ring)


def point_in_polygon(lat, lon, polygon=None):
    """Ray casting: True jika titik berada di dalam polygon."""
    polygon = polygon or load_water_polygon()
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        yi, xi = polygon[i]
        yj, xj = polygon[j]
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_cross:
                inside = not inside
        j = i
    return inside


def haversine_m(lat1, lon1, lat2, lon2):
    """Jarak dua titik dalam meter."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def move(lat, lon, v_east, v_north, dt_s):
    """Menggeser posisi berdasarkan kecepatan (m/s) selama dt detik."""
    dlat = v_north * dt_s / METER_PER_DERAJAT
    dlon = v_east * dt_s / (METER_PER_DERAJAT * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def vector_from_bearing(speed, bearing_deg):
    """Arah menuju (0 = utara, 90 = timur) menjadi komponen timur dan utara."""
    r = math.radians(bearing_deg)
    return speed * math.sin(r), speed * math.cos(r)


def grid_key(lat, lon, cell_deg):
    """Kunci sel grid untuk mengelompokkan titik."""
    return (round(lat / cell_deg), round(lon / cell_deg))


def nearest_place(lat, lon, places_df):
    """Nama lokasi terdekat dari tabel lokasi."""
    if places_df is None or places_df.empty:
        return "-", None
    best_name, best_d = "-", None
    for _, row in places_df.iterrows():
        d = haversine_m(lat, lon, row["latitude"], row["longitude"])
        if best_d is None or d < best_d:
            best_name, best_d = row["nama"], d
    return best_name, best_d


RADIUS_AREA_PILOT_M = 40000   # titik dalam 40 km dari pusat Teluk Ambon dianggap area pilot
JARAK_NAMA_MAKS_M = 25000     # lebih jauh dari ini, lokasi dinamai dengan koordinat


def di_area_pilot(lat, lon):
    """True bila titik berada di sekitar Teluk Ambon (area pilot dengan data lokasi lengkap)."""
    from core.config import MAP_CENTER
    return haversine_m(lat, lon, MAP_CENTER[0], MAP_CENTER[1]) <= RADIUS_AREA_PILOT_M


def nama_lokasi(lat, lon, places_df):
    """Nama lokasi terdekat. Di luar area data lokasi, dinamai dengan koordinat agar laporan dari wilayah lain tetap bisa dipetakan."""
    nama, jarak = nearest_place(lat, lon, places_df)
    if jarak is None or jarak > JARAK_NAMA_MAKS_M:
        return f"Titik {lat:.3f}, {lon:.3f}", jarak
    return nama, jarak


def compass(bearing_deg):
    """Derajat menjadi nama mata angin singkat."""
    names = ["U", "TL", "T", "TG", "S", "BD", "B", "BL"]
    return names[int(((bearing_deg % 360) + 22.5) // 45) % 8]
