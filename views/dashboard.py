"""Halaman Dashboard: ringkasan kondisi, peta, zona prioritas, dan pintu masuk ke setiap modul."""

import pandas as pd
import plotly.express as px
import streamlit as st

from components import maps, ui
from core import data, pipeline
from core.config import COLORS, LEVEL_COLORS

ALUR = [
    ("LAPOR", "Warga dan nelayan kirim foto, lokasi, waktu, jenis sampah"),
    ("PETAKAN", "Laporan jadi titik temuan dan hotspot"),
    ("PREDIKSI", "Arus, angin, pasang surut untuk perkiraan 24 jam. Menunggu data"),
    ("TINDAK", "Prioritas zona, koordinat, verifikasi lapangan"),
]

MODUL = [
    ("Lapor", "Warga dan nelayan mengirim foto, lokasi, dan waktu. Lokasi terisi otomatis dari perangkat.", COLORS["mint"]),
    ("Analisis", "AI mengenali jenis sampah dari foto, petugas menerima atau menolak laporan.", COLORS["accent"]),
    ("Pemetaan", "Laporan digabung menjadi hotspot dengan peringkat kepadatan per sel sekitar 900 m.", COLORS["warning"]),
    ("Prediksi", "Perkiraan gerak sampah 24 jam. Belum aktif, menunggu kerja sama data arus dan angin.", COLORS["warning"]),
    ("Prioritas", "Hotspot diberi skor agar petugas tahu lokasi mana yang ditangani lebih dulu.", COLORS["danger"]),
    ("Verifikasi", "Hasil cek lapangan kembali ke sistem dan memperbarui status laporan.", COLORS["mint"]),
    ("Mikroplastik", "Hotspot plastik menjadi petunjuk lokasi sampling mikroplastik untuk laboratorium.", COLORS["accent"]),
    ("Data IKLH", "Klaster dan analisis spasial 34 provinsi menunjukkan wilayah berisiko serupa.", COLORS["mint"]),
]


def _tabel_zona(zones):
    baris = []
    for _, r in zones.head(6).iterrows():
        warna = LEVEL_COLORS.get(r["prioritas"], COLORS["accent"])
        baris.append(ui.tpl(
            "tabel_zona_baris", zone_id=r["zone_id"], lokasi=ui.esc(r["lokasi"]),
            sensitif=ui.esc(r["objek_sensitif_terdekat"]), warna=warna, latar=ui._rgba(warna, 0.12),
            prioritas=r["prioritas"], skor=f"{r['skor']:.2f}", laporan=r["jumlah_laporan"],
            menunggu=r["menunggu"], rekomendasi=ui.esc(r["rekomendasi"]),
        ))
    ui.tampil("tabel_zona", baris="".join(baris))


def _grafik(reports):
    kiri, kanan = st.columns(2)
    with kiri:
        ui.panel_title("LAPORAN PER MINGGU")
        df = reports.copy()
        df["minggu"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.to_period("W").dt.start_time
        per = df.groupby("minggu").size().reset_index(name="jumlah")
        fig = px.area(per, x="minggu", y="jumlah", markers=True, color_discrete_sequence=[COLORS["accent"]])
        fig.update_traces(line_width=3, fillcolor="rgba(0,210,255,0.15)")
        fig.update_xaxes(title=None)
        fig.update_yaxes(title="laporan")
        st.plotly_chart(ui.style_fig(fig, 300), width="stretch")
    with kanan:
        ui.panel_title("JENIS SAMPAH DARI LAPORAN")
        komp = reports["kategori"].value_counts().reset_index()
        komp.columns = ["kategori", "jumlah"]
        fig = px.bar(komp, x="jumlah", y="kategori", orientation="h", color_discrete_sequence=[COLORS["mint"]])
        fig.update_yaxes(categoryorder="total ascending", title=None)
        fig.update_xaxes(title="jumlah laporan")
        st.plotly_chart(ui.style_fig(fig, 300), width="stretch")


def _tombol_hero():
    """Tiga tombol di bawah judul: laporan, hotspot, dan analisis nasional."""
    _, a, b, c, _ = st.columns([2.2, 1.5, 1.5, 1.5, 2.2])
    with a:
        if st.button("Buat Laporan", key="cta_lapor", width="stretch"):
            ui.go_to("Lapor")
    with b:
        if st.button("Lihat Hotspot", key="cta_hotspot", width="stretch"):
            ui.go_to("Pemetaan")
    with c:
        if st.button("Analisis IKLH", key="cta_iklh", width="stretch"):
            ui.go_to("Data IKLH")


def render():
    ui.tampil("hero")
    _tombol_hero()

    reports = data.reports()
    hs = pipeline.hotspot()
    zones = pipeline.zona()

    hotspot_aktif = int((hs["tingkat"] != "Rendah").sum()) if not hs.empty else 0
    zona_tinggi = int((zones["prioritas"] == "Tinggi").sum()) if not zones.empty else 0
    menunggu = int((reports["status"] == "Menunggu verifikasi").sum())
    terverifikasi = int((reports["status"] == "Terverifikasi").sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.dash_card("TOTAL LAPORAN", len(reports), f"Dari warga dan nelayan. {terverifikasi} sudah terverifikasi.", "green")
    with c2:
        ui.dash_card("HOTSPOT AKTIF", hotspot_aktif, "Area dengan kepadatan laporan sedang dan tinggi.", "purple")
    with c3:
        ui.dash_card("PRIORITAS TINGGI", zona_tinggi, "Lokasi yang diverifikasi dan ditangani lebih dulu.", "orange")
    with c4:
        ui.dash_card("MENUNGGU CEK", menunggu, "Laporan yang belum dicek petugas lapangan.", "green")

    ui.flow(ALUR)

    judul, pilih = st.columns([3, 2])
    with judul:
        ui.section_title("Peta Pemantauan Nasional")
    with pilih:
        view = maps.pilih_tampilan("view_dashboard", "Indonesia")

    map_col, stat_col = st.columns([3, 1])
    with map_col:
        if view == "Teluk Ambon":
            m = maps.base_map(view=view)
            maps.add_water_outline(m)
            maps.add_heatmap(m, reports)
            maps.add_reports(m, reports)
            maps.add_zones(m, zones[zones["prioritas"] != "Rendah"])
            maps.add_legend(m, "LEGENDA PETA", [
                ("#ffffff", "Laporan terverifikasi"),
                (COLORS["warning"], "Menunggu verifikasi dan zona sedang"),
                (COLORS["danger"], "Zona prioritas tinggi"),
            ])
            maps.show(maps.finish(m), 560, "map_dashboard_ambon")
        else:
            peta = maps.peta_luas(view, reports, data.baca_csv("iklh_provinsi.csv"), data.baca_csv("klaster_iklh.csv"))
            maps.show(peta, 560, f"map_dashboard_{view}")
        if view != "Teluk Ambon":
            ui.source_note("Warna provinsi: klaster IKLH dari analisis K-Means pada 34 provinsi (Maluku Utara tidak ada dalam dataset). "
                           "Garis putih tebal: Maluku, kelompok hotspot spasial. Gelembung biru: laporan OceanPatrol, "
                           "dekati untuk melihat titiknya.")

    with stat_col:
        iklh = data.baca_csv("iklh_provinsi.csv")
        maluku = iklh[iklh["provinsi"] == "Maluku"].iloc[0]
        timbulan = data.baca_csv("timbulan_maluku_sipsn2024.csv")
        ambon = timbulan[timbulan["kabkota"] == "Kota Ambon"].iloc[0]
        survei = data.baca_csv("survei_literatur.csv")
        poka = survei[survei["stasiun"] == "Poka"].iloc[0]
        isi = [
            ui.stat_row("IKLH Maluku", f"{maluku['iklh']:.2f}".replace(".", ","),
                        "Tampak aman, tetapi masuk kelompok hotspot spasial"),
            ui.stat_row("Timbulan sampah Kota Ambon", f"{ambon['timbulan_harian_ton']:.0f} ton/hari".replace(".", ","),
                        "SIPSN 2024"),
            ui.stat_row("Kepadatan sampah pesisir Poka", f"{poka['kepadatan_item_m2']:.2f} item/m2".replace(".", ","),
                        "Survei lapangan 2017, terbit 2021"),
        ]
        ui.tampil("kondisi_panel", isi="".join(isi))

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section_title("Zona Prioritas Teratas")
    if zones.empty:
        st.info("Belum ada laporan yang bisa dijadikan zona prioritas.")
    else:
        _tabel_zona(zones)
    _grafik(reports)

    ui.section_title("Jelajahi Modul")
    for awal in (0, 4):
        for i, col in enumerate(st.columns(4)):
            nama, isi, warna = MODUL[awal + i]
            with col:
                # Seluruh kotak bisa diklik: tombol transparan menutupi kartu (lihat .st-key-modul_* di style.css)
                with st.container(key=f"modul_{nama.replace(' ', '_')}"):
                    ui.tampil("modul_card", judul=nama, isi=ui.esc(isi), warna=warna)
                    if st.button(f"Buka {nama}", key=f"buka_{nama.replace(' ', '_')}"):
                        ui.go_to(nama)

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section_title("Dari Skala Nasional ke Titik Kritis Lokal")
    klaster = data.baca_csv("klaster_iklh.csv")
    kritis = int(klaster.loc[klaster["nama_zona"] == "Zona Kritis", "jumlah_provinsi"].iat[0])
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        ui.fact("34", "provinsi dianalisis dengan K-Means dan Moran's I", "Analisis IKLH, SIPSN, BPS 2024", COLORS["accent"])
    with f2:
        ui.fact(str(kritis), "provinsi masuk Zona Kritis, terpusat di Jawa dan Bali", "Klaster tipologi IKLH", COLORS["danger"])
    with f3:
        ui.fact("78,59", "IKLH Maluku tampak aman, tetapi berada di kelompok hotspot spasial", "LISA High-High", COLORS["warning"])
    with f4:
        ui.fact("68,74", "item/m2 sampah pesisir di Poka, Teluk Ambon, tersembunyi di data provinsi", "Survei 2017, terbit 2021", COLORS["mint"])
