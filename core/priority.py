"""Zona prioritas: hotspot diubah menjadi urutan lokasi yang diverifikasi lebih dulu."""

import pandas as pd

from core.geo import haversine_m

BOBOT = {
    "kepadatan": 0.45,   # skor kepadatan hotspot dibanding hotspot tertinggi
    "terbaru": 0.20,     # banyaknya laporan 7 hari terakhir dibanding zona teraktif
    "plastik": 0.15,     # porsi sampah plastik dan styrofoam
    "sensitif": 0.20,    # kedekatan dengan keramba, mangrove, permukiman, pasar
}

LABEL = {
    "kepadatan": "Kepadatan laporan",
    "terbaru": "Laporan 7 hari terakhir",
    "plastik": "Porsi plastik",
    "sensitif": "Dekat lokasi sensitif",
}

AKSI = {
    "Tinggi": "Verifikasi dan pembersihan kurang dari 24 jam. Koordinasi DLH dan kelompok nelayan.",
    "Sedang": "Jadwalkan verifikasi lapangan dalam 3 hari.",
    "Rendah": "Pantau laporan berikutnya. Masukkan ke patroli rutin.",
}


def zona_prioritas(hotspot_df, sensitive_df):
    """Menambahkan skor, tingkat prioritas, dan rekomendasi pada setiap hotspot."""
    if hotspot_df is None or hotspot_df.empty:
        return pd.DataFrame()
    z = hotspot_df.copy()

    s_sensitif, objek = [], []
    for _, r in z.iterrows():
        terdekat, jarak = None, None
        for _, s in sensitive_df.iterrows():
            d = haversine_m(r["latitude"], r["longitude"], s["latitude"], s["longitude"])
            if jarak is None or d < jarak:
                terdekat, jarak = s["nama"], d
        s_sensitif.append(max(0.0, 1 - (jarak or 9999) / 1500))
        objek.append(f"{terdekat} ({jarak:.0f} m)" if terdekat else "-")

    z["s_kepadatan"] = z["indeks"]
    maks_baru = z["laporan_7_hari"].max() or 1
    z["s_terbaru"] = z["laporan_7_hari"] / maks_baru
    z["s_plastik"] = z["porsi_plastik"]
    z["s_sensitif"] = s_sensitif
    z["objek_sensitif_terdekat"] = objek
    z["skor"] = sum(BOBOT[k] * z[f"s_{k}"] for k in BOBOT).round(3)
    z["prioritas"] = pd.cut(z["skor"], bins=[-0.01, 0.4, 0.65, 1.01], labels=["Rendah", "Sedang", "Tinggi"]).astype(str)
    z["rekomendasi"] = z["prioritas"].map(AKSI)
    z = z.sort_values("skor", ascending=False).reset_index(drop=True)
    z.insert(0, "zone_id", [f"Z-{i + 1:02d}" for i in range(len(z))])
    return z
