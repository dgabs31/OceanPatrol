"""Hotspot dari laporan warga: kepadatan laporan per sel grid."""

import pandas as pd

from core.config import JUMLAH_BOBOT
from core.geo import grid_key, nama_lokasi

SEL_DERAJAT = 0.008  # sekitar 900 m


def hitung_hotspot(reports_df, places_df, sel_derajat=SEL_DERAJAT):
    """Mengelompokkan laporan ke sel grid dan memberi peringkat.

    Bobot laporan: estimasi jumlah (Sedikit 1, Sedang 3, Banyak 6).
    Laporan berstatus Ditolak tidak dihitung.
    """
    if reports_df is None or reports_df.empty:
        return pd.DataFrame()
    df = reports_df[reports_df["status"] != "Ditolak"].copy()
    if df.empty:
        return pd.DataFrame()
    df["bobot"] = df["estimasi_jumlah"].map(JUMLAH_BOBOT).fillna(1)
    df["sel"] = [grid_key(a, b, sel_derajat) for a, b in zip(df["latitude"], df["longitude"])]
    df["waktu"] = pd.to_datetime(df["timestamp"], errors="coerce")
    acuan = df["waktu"].max()

    rows = []
    for _, g in df.groupby("sel"):
        lat, lon = g["latitude"].mean(), g["longitude"].mean()
        nama, _ = nama_lokasi(lat, lon, places_df)
        baru = (g["waktu"] >= acuan - pd.Timedelta(days=7)).sum()
        rows.append({
            "latitude": lat,
            "longitude": lon,
            "lokasi": nama,
            "jumlah_laporan": len(g),
            "skor_kepadatan": g["bobot"].sum(),
            "kategori_dominan": g["kategori"].mode().iat[0],
            "porsi_plastik": g["kategori"].str.contains("lastik|Styrofoam").mean(),
            "porsi_terapung": (g["jenis"] == "Terapung").mean(),
            "laporan_7_hari": int(baru),
            "terverifikasi": int((g["status"] == "Terverifikasi").sum()),
            "menunggu": int((g["status"] == "Menunggu verifikasi").sum()),
            "laporan_terakhir": g["timestamp"].max(),
            "report_ids": ", ".join(g["report_id"]),
        })
    hs = pd.DataFrame(rows).sort_values("skor_kepadatan", ascending=False).reset_index(drop=True)
    maks = hs["skor_kepadatan"].max()
    hs["indeks"] = hs["skor_kepadatan"] / maks if maks else 0
    hs["tingkat"] = pd.cut(hs["indeks"], bins=[-0.01, 0.35, 0.65, 1.01], labels=["Rendah", "Sedang", "Tinggi"]).astype(str)
    hs.insert(0, "peringkat", range(1, len(hs) + 1))
    return hs
