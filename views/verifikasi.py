"""Halaman Verifikasi: cek lapangan di zona prioritas, hasilnya kembali ke sistem."""

import plotly.express as px
import streamlit as st

from components import ui
from core import data, pipeline
from core.config import COLORS, LEVEL_COLORS


def _form(r):
    with st.form(f"verif_{r['zone_id']}", clear_on_submit=True):
        a, b = st.columns(2)
        ada = a.radio("Sampah ditemukan?", ["Ya", "Tidak"], horizontal=True)
        kepadatan = b.select_slider("Kepadatan", ["Rendah", "Sedang", "Tinggi"], value="Sedang")
        a, b = st.columns(2)
        berat = a.number_input("Berat terkumpul (kg)", 0.0, 2000.0, 0.0, 0.5)
        petugas = b.text_input("Nama tim", placeholder="Contoh: Tim DLH Kota Ambon")
        catatan = st.text_area("Catatan lapangan", placeholder="Contoh: sampah menumpuk di bawah dermaga")
        if st.form_submit_button("SIMPAN VERIFIKASI"):
            data.tambah_verifikasi({
                "zone_id": r["zone_id"],
                "timestamp": data.sekarang_wit().strftime("%Y-%m-%d %H:%M"),
                "lokasi": r["lokasi"],
                "latitude": round(r["latitude"], 5),
                "longitude": round(r["longitude"], 5),
                "sampah_ditemukan": ada,
                "kepadatan": kepadatan,
                "berat_kg": berat,
                "petugas": petugas or "-",
                "catatan": catatan,
            })
            for rid in str(r["report_ids"]).split(", "):
                data.ubah_status_laporan(rid, "Terverifikasi" if ada == "Ya" else "Ditolak")
            st.success("Verifikasi tersimpan. Status laporan di zona ini ikut diperbarui.")


def render():
    ui.page_header("LANGKAH 5", "VERIFIKASI LAPANGAN",
                   "Tim atau relawan mengecek zona prioritas. Hasilnya kembali ke sistem sebagai feedback dan data monitoring.")

    zones = pipeline.zona()
    ver = st.session_state["verification"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.fact(len(ver), "verifikasi tercatat", color=COLORS["accent"])
    with c2:
        tepat = f"{(ver['sampah_ditemukan'] == 'Ya').mean():.0%}" if len(ver) else "-"
        ui.fact(tepat, "zona prioritas terbukti ada sampah", color=COLORS["mint"])
    with c3:
        berat = f"{ver['berat_kg'].astype(float).sum():.0f} kg" if len(ver) else "0 kg"
        ui.fact(berat, "sampah terkumpul", color=COLORS["warning"])
    with c4:
        ui.fact(int((data.reports()["status"] == "Menunggu verifikasi").sum()), "laporan masih menunggu", color=COLORS["danger"])

    if zones.empty:
        st.info("Belum ada zona prioritas.")
        return

    kiri, kanan = st.columns([1, 1])
    with kiri:
        ui.panel_title("PILIH ZONA YANG DICEK")
        opsi = zones[zones["prioritas"] != "Rendah"]["zone_id"].tolist() or zones["zone_id"].tolist()
        label = {r.zone_id: f"{r.zone_id} {r.lokasi} (prioritas {r.prioritas.lower()})" for r in zones.itertuples()}
        pilih = st.selectbox("Zona", opsi, format_func=lambda x: label[x], label_visibility="collapsed")
        r = zones[zones["zone_id"] == pilih].iloc[0]
        warna = LEVEL_COLORS.get(r["prioritas"], COLORS["warning"])
        ui.tampil("zona_ringkas", warna=warna, zone_id=r["zone_id"], lokasi=ui.esc(r["lokasi"]),
                  koordinat=f"{r['latitude']:.4f}, {r['longitude']:.4f}", laporan=r["jumlah_laporan"],
                  dominan=ui.esc(r["kategori_dominan"]), id_laporan=ui.esc(r["report_ids"]))
        _form(r)

    with kanan:
        ui.panel_title("RIWAYAT VERIFIKASI")
        if len(ver):
            ui.table(ver[["verification_id", "timestamp", "zone_id", "lokasi", "sampah_ditemukan",
                              "kepadatan", "berat_kg", "petugas"]], width="stretch", hide_index=True)
        else:
            st.caption("Belum ada verifikasi. Isi formulir di samping.")

        ui.panel_title("STATUS SEMUA LAPORAN", "margin-top:16px;")
        status = data.reports()["status"].value_counts().reset_index()
        status.columns = ["status", "jumlah"]
        fig = px.pie(status, values="jumlah", names="status", hole=0.5, color="status",
                     color_discrete_map={"Terverifikasi": COLORS["mint"], "Menunggu verifikasi": COLORS["warning"],
                                         "Ditolak": "#5a6478"})
        st.plotly_chart(ui.style_fig(fig, 260), width="stretch")

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section_title("Ekspor data monitoring")
    a, b, c = st.columns(3)
    tabel = zones[["zone_id", "lokasi", "prioritas", "skor", "latitude", "longitude", "jumlah_laporan",
                   "objek_sensitif_terdekat", "rekomendasi"]]
    a.download_button("UNDUH ZONA PRIORITAS (CSV)", tabel.to_csv(index=False), "zona_prioritas.csv", "text/csv")
    b.download_button("UNDUH LAPORAN (CSV)", data.reports().to_csv(index=False), "laporan.csv", "text/csv")
    c.download_button("UNDUH VERIFIKASI (CSV)", ver.to_csv(index=False), "verifikasi.csv", "text/csv")
    ui.source_note("Data baru tersimpan selama sesi berjalan. Penyimpanan permanen membutuhkan basis data pada tahap berikutnya.")
