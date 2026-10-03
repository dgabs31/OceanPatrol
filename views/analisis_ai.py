"""Halaman Analisis: hasil klasifikasi AI dan pemeriksaan laporan oleh petugas."""

import plotly.express as px
import streamlit as st

from components import ui
from core import data
from core.config import COLORS, KATEGORI_SAMPAH


def _antrean(df):
    """Laporan yang menunggu diperiksa. Petugas bisa menerima atau menolak."""
    tunggu = df[df["status"] == "Menunggu verifikasi"].sort_values("timestamp", ascending=False)
    if tunggu.empty:
        st.caption("Tidak ada laporan yang menunggu pemeriksaan.")
        return
    for r in tunggu.head(6).itertuples():
        cocok = r.kategori == r.ai_kategori
        warna = COLORS["mint"] if cocok else COLORS["warning"]
        keterangan = "AI dan pelapor sepakat" if cocok else "AI dan pelapor berbeda, periksa foto"
        kiri, kanan = st.columns([4, 1.3])
        with kiri:
            ui.tampil("antrean_card", warna=warna, report_id=r.report_id, lokasi=ui.esc(r.lokasi),
                      waktu=r.timestamp, pelapor=r.pelapor,
                      ai=f"{ui.esc(r.ai_kategori)} ({r.confidence:.0%})", kategori=ui.esc(r.kategori),
                      kondisi=f"{r.jenis}, {r.estimasi_jumlah.lower()}", keterangan=keterangan)
        with kanan:
            if st.button("TERIMA", key=f"ok_{r.report_id}", width="stretch"):
                data.ubah_status_laporan(r.report_id, "Terverifikasi")
                st.rerun()
            if st.button("TOLAK", key=f"no_{r.report_id}", width="stretch"):
                data.ubah_status_laporan(r.report_id, "Ditolak")
                st.rerun()


def render():
    ui.page_header("LANGKAH 1: LAPOR (PEMERIKSAAN FOTO)", "ANALISIS FOTO DENGAN AI",
                   "AI mengklasifikasi jenis sampah yang terlihat. Petugas memeriksa laporan sebelum masuk peta.")

    df = data.reports()
    sepakat = (df["kategori"] == df["ai_kategori"]).mean()
    plastik = df["ai_kategori"].str.contains("lastik|Styrofoam").mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.fact(len(df), "foto dianalisis", color=COLORS["accent"])
    with c2:
        ui.fact(f"{df['confidence'].mean():.0%}", "rata-rata keyakinan AI", color=COLORS["mint"])
    with c3:
        ui.fact(f"{sepakat:.0%}", "hasil AI sama dengan pilihan pelapor", color=COLORS["warning"])
    with c4:
        ui.fact(f"{plastik:.0%}", "laporan berisi plastik atau styrofoam", color=COLORS["danger"])

    kiri, kanan = st.columns([1, 1.25])
    with kiri:
        ui.panel_title("JENIS SAMPAH MENURUT AI")
        komp = df["ai_kategori"].value_counts().reindex(KATEGORI_SAMPAH, fill_value=0).reset_index()
        komp.columns = ["kategori", "jumlah"]
        fig = px.bar(komp, x="jumlah", y="kategori", orientation="h", color_discrete_sequence=[COLORS["accent"]])
        fig.update_yaxes(categoryorder="total ascending", title=None)
        fig.update_xaxes(title="jumlah laporan")
        st.plotly_chart(ui.style_fig(fig, 300), width="stretch")
        ui.info_box("BATAS ANALISIS FOTO",
                    "AI hanya mengenali sampah yang terlihat (makro). Mikroplastik tidak bisa dipastikan dari foto dan "
                    "tetap membutuhkan sampling serta analisis laboratorium.", COLORS["warning"])
        ui.source_note("Hasil Terima atau Tolak dari petugas dicatat sebagai data untuk memperbaiki klasifikasi AI.")
    with kanan:
        ui.panel_title("ANTREAN PEMERIKSAAN LAPORAN")
        _antrean(df)
