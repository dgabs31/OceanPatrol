"""Halaman Prediksi: langkah 3 dari alur OceanPatrol.

Halaman ini sengaja tidak menampilkan angka atau peta prediksi. Data arus, angin, pasang surut, dan hujan
yang resmi belum menjadi bagian dari sistem, sehingga halaman ini menjelaskan cara kerja, kebutuhan data,
calon mitra, dan keluaran yang akan dihasilkan setelah data tersedia.
"""

import pandas as pd
import streamlit as st

from components import ui
from core import pipeline
from core.config import COLORS

ALUR_PREDIKSI = [
    ("DATA LAUT", "Arus, angin, pasang surut, hujan"),
    ("POSISI AWAL", "Hotspot dari laporan warga"),
    ("MODEL GERAK", "Sampah dianggap partikel yang terbawa"),
    ("PERKIRAAN 24 JAM", "Ke mana sampah bergerak"),
    ("PRIORITAS", "Masuk ke skor zona"),
]

KEBUTUHAN_DATA = [
    ("Arus permukaan", "BMKG Ocean Forecast System, Copernicus Marine", "Membawa sampah mengikuti massa air", "Belum tersedia"),
    ("Angin dan gelombang", "BMKG", "Mendorong sampah yang mengapung dan mengubah arah", "Belum tersedia"),
    ("Pasang surut", "BMKG, BIG", "Mendorong sampah masuk atau keluar teluk", "Belum tersedia"),
    ("Curah hujan", "NASA GPM IMERG", "Penanda kiriman sampah dari sungai setelah hujan", "Belum tersedia"),
    ("Posisi sampah aktual", "Laporan OceanPatrol", "Titik awal perhitungan dan bahan uji hasil", "Tersedia di aplikasi"),
    ("Pengamatan lapangan", "Verifikasi petugas dan survei", "Pembanding antara perkiraan dan kenyataan", "Tersedia di aplikasi"),
]

KELUARAN = [
    (COLORS["accent"], "ARAH DAN JARAK GERAK",
     "Perkiraan ke arah mana hotspot bergerak dalam 24 jam dan seberapa jauh, ditampilkan di peta bersama titik laporan."),
    (COLORS["warning"], "ZONA TUJUAN AKUMULASI",
     "Area teluk tempat sampah cenderung berkumpul, sehingga bisa dibersihkan sebelum menyebar atau terfragmentasi."),
    (COLORS["mint"], "WAKTU PATROLI",
     "Petugas tahu kapan dan di mana patroli paling efektif, bukan hanya di mana sampah terlihat hari ini."),
]

KERJA_SAMA = [
    ("BMKG", "Data arus, angin, gelombang, dan pasang surut resmi untuk perairan Maluku."),
    ("Universitas Pattimura dan BRIN", "Pengalaman riset Teluk Ambon, termasuk ekspedisi dan penelitian mikroplastik, untuk kalibrasi model."),
    ("Dinas Lingkungan Hidup dan kelompok nelayan", "Verifikasi lapangan yang menguji apakah perkiraan sesuai kenyataan."),
]

TAHAPAN = [
    "Menyambungkan data arus, angin, pasang surut, dan hujan dari sumber resmi",
    "Menjalankan model pergerakan partikel dari titik hotspot selama 24 jam",
    "Membandingkan hasil dengan laporan dan verifikasi lapangan, lalu mengkalibrasi",
    "Memasukkan arah gerak dan zona tujuan sebagai faktor tambahan skor prioritas",
]


def _daftar(items, warna):
    li = "".join(f"<li style='margin-bottom:8px;'>{ui.esc(x)}</li>" for x in items)
    return f"<ul style='margin:6px 0 0 0; padding-left:18px; color:#ccd6f6;'>{li}</ul>"


def _daftar_mitra(items, warna):
    li = "".join(
        f"<li style='margin-bottom:10px;'><b style='color:{warna};'>{ui.esc(a)}</b><br>"
        f"<span style='color:#8892b0;'>{ui.esc(b)}</span></li>" for a, b in items)
    return f"<ul style='margin:6px 0 0 0; padding-left:18px; color:#ccd6f6;'>{li}</ul>"


def render():
    ui.page_header("LANGKAH 3: PREDIKSI", "PREDIKSI PERGERAKAN SAMPAH",
                   "Perkiraan ke mana sampah bergerak selama 24 jam, agar penanganan dilakukan sebelum sampah menyebar.")

    ui.flow(ALUR_PREDIKSI)

    ui.info_box("STATUS FITUR INI",
                "Prediksi belum aktif di versi ini dan tidak menampilkan angka perkiraan. Fitur ini membutuhkan data arus, "
                "angin, pasang surut, dan hujan yang resmi, serta kerja sama dengan pemilik data. Halaman ini menjelaskan "
                "cara kerjanya, apa yang dibutuhkan, dan apa yang akan dihasilkan.", COLORS["warning"])

    ui.section_title("Gambaran Jika Data Lengkap")
    zona = pipeline.zona()
    nama = [str(x) for x in zona["lokasi"].head(3)] + ["Hotspot", "Hotspot", "Hotspot"]
    ui.tampil("prediksi_ilustrasi", hotspot_1=ui.esc(nama[0]), hotspot_2=ui.esc(nama[1]), hotspot_3=ui.esc(nama[2]))
    ui.info_box("YANG BERUBAH DI ZONA PRIORITAS",
                "Setiap zona akan memiliki arah gerak dan estimasi kedatangan sampah, dan skor prioritas ditambah faktor zona tujuan "
                "akumulasi. Halaman Zona Prioritas sudah menyiapkan tempat untuk keterangan ini.", COLORS["accent"])

    ui.section_title("Kenapa Sampah Laut Perlu Diperkirakan")
    ui.md("<p>Sampah tidak diam di tempat laporan dibuat. Hujan membawa sampah dari daratan lewat sungai, angin mengubah arah "
          "sampah yang mengapung, dan pasang surut mendorongnya masuk atau keluar teluk. Tanpa perkiraan gerak, petugas hanya "
          "bisa mengejar sampah yang sudah terlihat. Dengan perkiraan, hotspot dapat ditangani sebelum menyebar dan "
          "terurai menjadi mikroplastik.</p>")

    ui.section_title("Data yang Dibutuhkan")
    ui.table(pd.DataFrame(KEBUTUHAN_DATA, columns=["Kebutuhan", "Calon sumber", "Fungsi", "Status"]),
             width="stretch", hide_index=True)
    ui.source_note("Resolusi data arus global sekitar 1/12 derajat terlalu kasar untuk Teluk Ambon Dalam yang sempit. "
                   "Karena itu hasil prediksi baru layak dipakai setelah data diperhalus atau dicocokkan dengan pengamatan lapangan.")

    ui.section_title("Yang Akan Dihasilkan")
    kolom = st.columns(3)
    for col, (warna, judul, isi) in zip(kolom, KELUARAN):
        with col:
            ui.tampil("fitur_card", warna=warna, judul=judul, isi=ui.esc(isi))

    ui.section_title("Jika Kerja Sama Data Terjalin")
    kiri, kanan = st.columns(2)
    with kiri:
        ui.tampil("daftar_card", warna=COLORS["accent"], judul="CALON MITRA DATA DAN RISET",
                  isi=_daftar_mitra(KERJA_SAMA, COLORS["accent"]))
    with kanan:
        ui.tampil("daftar_card", warna=COLORS["mint"], judul="TAHAP PENGEMBANGAN",
                  isi=_daftar(TAHAPAN, COLORS["mint"]))

    ui.info_box("HUBUNGAN DENGAN ALUR UTAMA",
                "Laporan warga dan verifikasi lapangan yang sudah berjalan di OceanPatrol menjadi titik awal sekaligus bahan uji "
                "bagi prediksi. Karena itu prediksi adalah kelanjutan alami dari sistem ini, bukan komponen yang terpisah.",
                COLORS["accent"])

    if st.button("LANJUT KE ZONA PRIORITAS"):
        ui.go_to("Prioritas")
