"""Halaman Pemetaan: laporan diubah menjadi peta hotspot dan peringkat."""

import pandas as pd
import plotly.express as px
import streamlit as st

from components import maps, ui
from core import data
from core.config import COLORS, KATEGORI_SAMPAH, LEVEL_COLORS
from core.hotspot import hitung_hotspot


def _kartu_peringkat(r):
    warna = LEVEL_COLORS.get(r["tingkat"], COLORS["accent"])
    ringkas = (f"{r['jumlah_laporan']} laporan, skor kepadatan {r['skor_kepadatan']:.0f}. "
               f"Dominan: {ui.esc(r['kategori_dominan'])}. Porsi plastik {r['porsi_plastik']:.0%}.")
    ui.tampil("rank_card", warna=warna, peringkat=r["peringkat"], lokasi=ui.esc(r["lokasi"]).upper(),
              tingkat=r["tingkat"].upper(), bar=ui.bar(r["indeks"], warna), ringkas=ringkas)


URUTAN = {
    "Peringkat": ("peringkat", True),
    "Skor kepadatan": ("skor_kepadatan", False),
    "Jumlah laporan": ("jumlah_laporan", False),
    "Porsi plastik": ("porsi_plastik", False),
    "Laporan terakhir": ("laporan_terakhir", False),
}


def _tabel_hotspot(hs):
    """Tabel hotspot bergaya dasbor: pencarian, urutan, status berwarna, angka bermonospasi."""
    ui.section_title("Tabel hotspot")
    a, b = st.columns([2, 1])
    cari = a.text_input("Cari lokasi", placeholder="Cari lokasi...", label_visibility="collapsed")
    urut = b.selectbox("Urutkan", list(URUTAN), label_visibility="collapsed")
    kolom, naik = URUTAN[urut]
    tabel = hs.sort_values(kolom, ascending=naik)
    if cari:
        tabel = tabel[tabel["lokasi"].str.contains(cari, case=False, na=False)]
    ui.tampil("tabel_info", tampil=len(tabel), total=len(hs))
    baris = []
    for _, r in tabel.iterrows():
        warna = LEVEL_COLORS.get(r["tingkat"], COLORS["accent"])
        baris.append(ui.tpl(
            "tabel_hotspot_baris", peringkat=r["peringkat"], lokasi=ui.esc(r["lokasi"]),
            terverifikasi=r["terverifikasi"], dominan=ui.esc(r["kategori_dominan"]),
            warna=warna, latar=ui._rgba(warna, 0.12), tingkat=r["tingkat"],
            laporan=r["jumlah_laporan"], skor=f"{r['skor_kepadatan']:.0f}",
            plastik=f"{r['porsi_plastik']:.0%}", indeks=f"{r['indeks']:.2f}",
            terakhir=ui.esc(r["laporan_terakhir"]),
        ))
    ui.tampil("tabel_hotspot", baris="".join(baris))
    ui.source_note("Skor kepadatan = jumlah bobot laporan dalam sel sekitar 900 m (Sedikit 1, Sedang 3, Banyak 6). "
                   "Laporan yang ditolak tidak dihitung.")


def render():
    ui.page_header("LANGKAH 3", "PEMETAAN HOTSPOT",
                   "Laporan warga dipetakan menjadi titik temuan dan hotspot konsentrasi sampah.")

    semua = data.reports()
    f1, f2, f3 = st.columns([2, 1, 1])
    kategori = f1.multiselect("Jenis sampah", KATEGORI_SAMPAH, default=KATEGORI_SAMPAH)
    jenis = f2.multiselect("Kondisi", ["Terapung", "Terdampar"], default=["Terapung", "Terdampar"])
    status = f3.multiselect("Status", ["Terverifikasi", "Menunggu verifikasi", "Ditolak"],
                            default=["Terverifikasi", "Menunggu verifikasi"])
    df = semua[semua["kategori"].isin(kategori) & semua["jenis"].isin(jenis) & semua["status"].isin(status)]

    hs = hitung_hotspot(df, data.places())

    _, pilih = st.columns([3, 2])
    with pilih:
        view = maps.pilih_tampilan("view_pemetaan", "Teluk Ambon")

    if view != "Teluk Ambon":
        peta = maps.peta_luas(view, df, data.baca_csv("iklh_provinsi.csv"), data.baca_csv("klaster_iklh.csv"))
        maps.show(peta, 560, f"map_petakan_{view}")
    else:
        m = maps.base_map(view=view)
        maps.add_water_outline(m)
        maps.add_heatmap(m, df)
        maps.add_hotspot_cells(m, hs.head(6))
        maps.add_reports(m, df)
        maps.add_survey(m, data.survey())
        maps.add_sensitive(m, data.sensitive())
        maps.add_legend(m, "LEGENDA HOTSPOT", [
            (COLORS["danger"], "Hotspot tinggi"),
            (COLORS["warning"], "Hotspot sedang"),
            (COLORS["accent"], "Hotspot rendah"),
            ("#ffffff", "Laporan terverifikasi"),
            ("#a18cd1", "Data survei literatur"),
            (COLORS["mint"], "Lokasi sensitif"),
        ])
        maps.show(maps.finish(m), 560, "map_petakan")

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section_title("Peringkat hotspot")
    if st.button("LANJUT KE ZONA PRIORITAS"):
        ui.go_to("Prioritas")
    if hs.empty:
        st.info("Tidak ada laporan yang cocok dengan filter.")
        return
    cols = st.columns(3)
    for i, (_, r) in enumerate(hs.head(3).iterrows()):
        with cols[i]:
            _kartu_peringkat(r)

    _tabel_hotspot(hs)

    kiri, kanan = st.columns(2)
    with kiri:
        ui.panel_title("KOMPOSISI SAMPAH DARI LAPORAN")
        komp = df["kategori"].value_counts().reset_index()
        komp.columns = ["kategori", "jumlah"]
        fig = px.bar(komp, x="jumlah", y="kategori", orientation="h", color_discrete_sequence=[COLORS["accent"]])
        fig.update_yaxes(categoryorder="total ascending", title=None)
        st.plotly_chart(ui.style_fig(fig, 300), width="stretch")
    with kanan:
        ui.panel_title("BUKTI SURVEI LAPANGAN (LITERATUR)")
        sv = data.survey().dropna(subset=["kepadatan_item_m2"])
        sv = sv[sv["sumber"].str.contains("Omni")]
        fig = px.bar(sv, x="stasiun", y="kepadatan_item_m2", text="kepadatan_item_m2",
                     color="stasiun", color_discrete_sequence=[COLORS["danger"], COLORS["accent2"], COLORS["accent"]])
        fig.update_layout(showlegend=False)
        fig.update_yaxes(title="item/m2")
        fig.update_xaxes(title=None)
        st.plotly_chart(ui.style_fig(fig, 300), width="stretch")
        ui.source_note("Sampel 2017, terbit 2021. Seluruh stasiun berkategori Very Dirty. "
                       "Nilai Tawiri diturunkan dari rasio sekitar 10 kali terhadap Poka.")

    ui.panel_title("RIWAYAT LAPORAN PER MINGGU", "margin-top:10px;")
    riwayat = df.copy()
    riwayat["minggu"] = pd.to_datetime(riwayat["timestamp"], errors="coerce").dt.to_period("W").dt.start_time
    per_minggu = riwayat.groupby(["minggu", "lokasi"]).size().reset_index(name="jumlah")
    fig = px.bar(per_minggu, x="minggu", y="jumlah", color="lokasi",
                 color_discrete_sequence=[COLORS["accent"], COLORS["mint"], COLORS["warning"], COLORS["danger"],
                                          "#a18cd1", "#fbc2eb", "#9FACE6", COLORS["accent2"]])
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="jumlah laporan")
    fig.update_layout(legend_title_text="")
    st.plotly_chart(ui.style_fig(fig, 300), width="stretch")
    ui.source_note("Riwayat menjadi basis data monitoring: lokasi, waktu, jenis sampah, frekuensi, dan hasil verifikasi.")
