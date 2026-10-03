"""Halaman Mikroplastik: hotspot sampah plastik sebagai petunjuk lokasi sampling."""

import pandas as pd
import streamlit as st

from components import maps, ui
from core import data, pipeline
from core.config import COLORS


def rencana_sampling():
    """Calon titik sampling dari hotspot laporan, zona akumulasi, dan data literatur."""
    rows = []
    hs = pipeline.hotspot()
    for r in hs[hs["tingkat"] == "Tinggi"].head(3).itertuples():
        rows.append({"lokasi": r.lokasi, "latitude": r.latitude, "longitude": r.longitude,
                     "alasan": f"Hotspot laporan, porsi plastik {r.porsi_plastik:.0%}",
                     "metode": "Air permukaan (jaring neuston/manta)", "urutan": 1})
    zones = pipeline.zona()
    for r in zones[(zones["prioritas"] == "Tinggi") & (zones["porsi_terapung"] < 1)].head(3).itertuples():
        rows.append({"lokasi": r.lokasi, "latitude": r.latitude, "longitude": r.longitude,
                     "alasan": f"Zona prioritas tinggi, ada sampah terdampar (skor {r.skor:.2f})",
                     "metode": "Sedimen pantai (kuadran dan saringan 5 mm)", "urutan": 2})
    sv = data.survey().dropna(subset=["latitude"])
    for r in sv.itertuples():
        if r.stasiun in ("Poka", "Tawiri"):
            rows.append({"lokasi": r.stasiun, "latitude": r.latitude, "longitude": r.longitude,
                         "alasan": "Stasiun pembanding literatur" if r.stasiun == "Tawiri" else "Kepadatan tertinggi pada literatur",
                         "metode": "Air permukaan dan sedimen", "urutan": 3})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.drop_duplicates(subset=["lokasi", "metode"]).sort_values("urutan").reset_index(drop=True)
    df.insert(0, "kode", [f"MP-{i + 1:02d}" for i in range(len(df))])
    return df


def render():
    ui.page_header("DARI MAKRO KE MIKRO", "PEMANTAUAN MIKROPLASTIK",
                   "Hotspot sampah plastik menjadi petunjuk awal lokasi pengambilan sampel mikroplastik.")

    ui.flow([
        ("SAMPAH MAKRO", "Terlihat di foto laporan"),
        ("FRAGMENTASI", "Sinar matahari, gelombang, abrasi"),
        ("MIKROPLASTIK", "Kurang dari 5 mm, perlu sampel lab"),
    ])
    ui.info_box("BATAS KEMAMPUAN APLIKASI",
                "OceanPatrol tidak mendeteksi mikroplastik lewat kamera. Aplikasi menunjukkan di mana sampah plastik menumpuk, "
                "lalu titik tersebut diusulkan sebagai lokasi sampling dan analisis laboratorium.", COLORS["warning"])

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        ui.fact("< 5 mm", "ukuran partikel mikroplastik", "Definisi umum", COLORS["accent"])
    with f2:
        ui.fact("4 bentuk", "fiber, fragmen, film, dan granul", "Poster OceanPatrol", COLORS["mint"])
    with f3:
        ui.fact("7,5x", "konsentrasi mikroplastik permukaan Teluk Ambon Dalam dibanding Teluk Ambon Luar",
                "Publikasi 2022", COLORS["danger"])
    with f4:
        ui.fact("Ikan budidaya", "serat dan film ditemukan pada Caranx sexfasciatus di Teluk Ambon Dalam",
                "Bukti keberadaan, bukan klaim risiko kesehatan", COLORS["warning"])

    st.markdown("<br>", unsafe_allow_html=True)
    rencana = rencana_sampling()
    peta, tabel = st.columns([1.2, 1])
    with peta:
        m = maps.base_map()
        maps.add_water_outline(m)
        maps.add_heatmap(m, data.reports())
        maps.add_sensitive(m, data.sensitive())
        if not rencana.empty:
            maps.add_sampling(m, rencana)
        maps.add_legend(m, "LEGENDA PETA", [(COLORS["accent"], "Calon titik sampling"), (COLORS["mint"], "Lokasi sensitif")])
        maps.show(maps.finish(m), 460, "map_mikro")
    with tabel:
        ui.panel_title("RENCANA SAMPLING YANG DIUSULKAN")
        if rencana.empty:
            st.caption("Belum ada hotspot tingkat tinggi.")
        else:
            ui.table(rencana[["kode", "lokasi", "alasan", "metode"]], width="stretch",
                         hide_index=True, height=380)
        ui.source_note("Urutan: hotspot laporan, zona prioritas dengan sampah terdampar, lalu stasiun literatur sebagai pembanding.")
