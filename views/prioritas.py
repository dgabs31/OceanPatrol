"""Halaman Prioritas: hotspot diubah menjadi urutan lokasi yang ditangani lebih dulu."""

import plotly.graph_objects as go
import streamlit as st

from components import maps, ui
from core import data, pipeline
from core.config import COLORS, LEVEL_COLORS
from core.priority import BOBOT, LABEL

WARNA_FAKTOR = {
    "kepadatan": COLORS["danger"], "terbaru": COLORS["warning"], "plastik": COLORS["accent"],
    "sensitif": COLORS["mint"],
}


def rincian_skor(r):
    kunci = list(BOBOT)
    fig = go.Figure(go.Bar(
        x=[BOBOT[k] * r[f"s_{k}"] for k in kunci], y=[LABEL[k] for k in kunci], orientation="h",
        marker_color=[WARNA_FAKTOR[k] for k in kunci],
    ))
    fig.update_xaxes(range=[0, 0.45], title="kontribusi skor")
    fig.update_yaxes(autorange="reversed")
    return ui.style_fig(fig, 210)


def kartu_zona(r, baru=False):
    warna = LEVEL_COLORS.get(r["prioritas"], COLORS["warning"])
    tanda = ui.badge("ADA LAPORAN BARU", COLORS["mint"]) if baru else ""
    ui.tampil("zona_card", warna=warna, tanda=tanda, zone_id=r["zone_id"], lokasi=ui.esc(r["lokasi"]),
              prioritas=r["prioritas"].upper(), skor=f"{r['skor']:.2f}",
              koordinat=f"{r['latitude']:.4f}, {r['longitude']:.4f}",
              laporan=f"{r['jumlah_laporan']} ({r['menunggu']} menunggu)", tujuh_hari=r["laporan_7_hari"],
              dominan=ui.esc(r["kategori_dominan"]), rekomendasi=ui.esc(r["rekomendasi"]),
              sensitif=ui.esc(r["objek_sensitif_terdekat"]))


def render():
    ui.page_header("LANGKAH 4", "ZONA PRIORITAS",
                   "Hotspot diberi skor agar petugas tahu lokasi mana yang diverifikasi lebih dulu, bukan mencari secara acak.")

    zones = pipeline.zona()
    if zones.empty:
        st.info("Belum ada laporan yang bisa dijadikan zona prioritas.")
        return

    demo = set(st.session_state.get("laporan_demo", []))
    if demo:
        ui.info_box("LAPORAN BARU MASUK",
                    "Tiga laporan baru masuk dari Pasar Mardika. Lihat bagaimana zona tersebut naik peringkat.",
                    COLORS["mint"])

    c1, c2, c3 = st.columns(3)
    with c1:
        ui.fact(int((zones["prioritas"] == "Tinggi").sum()), "zona prioritas tinggi", color=COLORS["danger"])
    with c2:
        ui.fact(int((zones["prioritas"] == "Sedang").sum()), "zona prioritas sedang", color=COLORS["warning"])
    with c3:
        ui.fact(int(zones["menunggu"].sum()), "laporan di zona yang menunggu verifikasi", color=COLORS["accent"])

    peta, daftar = st.columns([1.15, 1])
    with peta:
        m = maps.base_map()
        maps.add_water_outline(m)
        maps.add_sensitive(m, data.sensitive())
        maps.add_reports(m, data.reports())
        maps.add_zones(m, zones)
        maps.add_legend(m, "LEGENDA ZONA PRIORITAS", [
            (COLORS["danger"], "Prioritas tinggi"),
            (COLORS["warning"], "Prioritas sedang"),
            (COLORS["accent"], "Prioritas rendah"),
            (COLORS["mint"], "Lokasi sensitif"),
        ])
        maps.show(maps.finish(m), 600, "map_prioritas")
        ui.source_note("Skor = 0,45 kepadatan + 0,20 laporan 7 hari terakhir + 0,15 porsi plastik + 0,20 kedekatan "
                       "lokasi sensitif. Tinggi bila di atas 0,65, sedang di atas 0,40.")

    with daftar:
        for _, r in zones.head(5).iterrows():
            baru = bool(demo & set(str(r["report_ids"]).split(", ")))
            kartu_zona(r, baru)
            with st.expander(f"Kenapa {r['zone_id']} diprioritaskan?"):
                st.plotly_chart(rincian_skor(r), width="stretch", key=f"skor_{r['zone_id']}")

    with st.expander("Lihat semua zona"):
        ui.table(zones[["zone_id", "lokasi", "prioritas", "skor", "jumlah_laporan", "menunggu",
                            "laporan_7_hari", "kategori_dominan", "objek_sensitif_terdekat"]],
                     width="stretch", hide_index=True)
    if st.button("LANJUT KE VERIFIKASI LAPANGAN"):
        ui.go_to("Verifikasi")
