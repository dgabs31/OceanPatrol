"""Halaman Tentang: deskripsi solusi, stakeholder, manfaat, SWOT, dan keterbatasan."""

import pandas as pd
import streamlit as st

from components import ui
from core.config import COLORS

FITUR = [
    ("Citizen Report", "Masyarakat pesisir melaporkan sampah lewat foto, lokasi, waktu, dan keterangan.", COLORS["mint"]),
    ("AI Image Analysis", "AI mengidentifikasi kategori sampah yang terlihat dan membantu karakterisasi laporan.", COLORS["accent"]),
    ("Hotspot Mapping", "Laporan digabung berdasarkan lokasi dan riwayat untuk menampilkan area konsentrasi tinggi.", COLORS["warning"]),
    ("Priority Zone", "Hotspot diubah menjadi zona prioritas agar petugas tidak mencari secara acak.", COLORS["danger"]),
]

STAKEHOLDER = [
    ("Nelayan dan masyarakat pesisir", "Citizen sensor yang melaporkan keberadaan sampah laut."),
    ("Tim relawan dan pembersih pantai", "Verifikasi dan intervensi berdasarkan zona prioritas."),
    ("Pemerintah daerah dan KKP", "Memakai informasi hotspot untuk monitoring dan perencanaan intervensi."),
    ("BMKG, BIG, dan peneliti oseanografi", "Berpotensi menyediakan data angin, arus, pasang surut, dan spasial untuk memperkaya analisis."),
]

MANFAAT = [
    ("Dari reaktif menjadi preventif", "Hotspot ditemukan dan diprioritaskan sebelum sampah terdampar dan terfragmentasi."),
    ("Efisiensi intervensi", "Tim pembersih bergerak berdasarkan data laporan dan persebaran hotspot, bukan pencarian acak."),
    ("Monitoring berkelanjutan", "Riwayat lokasi, waktu, jenis sampah, frekuensi laporan, dan hasil verifikasi tersimpan."),
    ("Dasar monitoring mikroplastik", "Hotspot marine debris menjadi petunjuk lokasi sampling mikroplastik."),
]

SWOT = {
    "STRENGTHS": (COLORS["mint"], [
        "Partisipatif: masyarakat pesisir berperan sebagai citizen sensor.",
        "Berbasis lokasi: setiap laporan punya koordinat sehingga dapat dipetakan.",
        "AI-assisted: AI membantu menganalisis dan mengklasifikasikan laporan visual.",
        "Hotspot-based: laporan individual menjadi gambaran spasial area akumulasi.",
        "Efisiensi intervensi: zona prioritas menentukan lokasi yang diverifikasi lebih dulu.",
    ]),
    "WEAKNESSES": (COLORS["danger"], [
        "Bergantung pada kualitas foto dan informasi dari masyarakat.",
        "Tidak semua laporan memiliki koordinat yang akurat.",
        "Membutuhkan validasi lapangan.",
        "Membutuhkan koneksi internet untuk pelaporan langsung.",
        "AI tidak dapat memastikan mikroplastik hanya dari foto.",
    ]),
    "OPPORTUNITIES": (COLORS["accent"], [
        "Integrasi dengan data oseanografi.",
        "Kolaborasi dengan pemerintah daerah, peneliti, dan kelompok masyarakat pesisir.",
        "Pengembangan menjadi sistem monitoring di berbagai teluk Indonesia.",
        "Hotspot marine debris sebagai dasar penentuan lokasi sampling mikroplastik.",
        "Pengembangan citizen science untuk monitoring lingkungan pesisir.",
    ]),
    "THREATS": (COLORS["warning"], [
        "Perubahan kondisi laut yang dinamis.",
        "Laporan duplikat atau tidak akurat.",
        "Keterbatasan data di wilayah pesisir tertentu.",
        "Karakteristik antarwilayah berbeda sehingga model perlu disesuaikan.",
        "Validasi mikroplastik tetap membutuhkan sampling dan analisis laboratorium.",
    ]),
}

KELEBIHAN = [
    "Preventif: hotspot ditangani sebelum terfragmentasi",
    "Berbasis lokasi, mudah ditindaklanjuti",
    "Human + AI dengan pemeriksaan petugas",
    "Zona prioritas: tidak lagi mencari secara acak",
    "Didukung data nyata (K-Means, LISA, SEM)",
    "Modular, bisa dikembangkan ke teluk lain",
]
KEKURANGAN = [
    ("Prediksi pergerakan belum aktif", "Kerja sama data BMKG dan Copernicus, diuji dengan laporan lapangan"),
    ("Belum ada mode offline", "Laporan disimpan di ponsel, terkirim saat ada sinyal"),
    ("Bias pelapor di area ramai", "Patroli rutin dan penanda area data kurang"),
    ("Belum ada deteksi laporan ganda", "Gabung laporan berjarak kurang dari 100 m dan 2 jam"),
    ("Data belum permanen, belum ada akun", "Basis data serta peran warga, petugas, dan DLH"),
    ("Bobot skor belum dikalibrasi", "Kalibrasi dari hasil verifikasi lapangan"),
    ("Belum ada insentif dan SOP", "Poin pelapor dan SOP bersama DLH"),
]
KETERBATASAN = [
    "Prediksi pergerakan belum aktif karena data arus dan angin resmi belum tersedia",
    "Laporan warga dan klasifikasi foto pada tampilan ini masih berupa data peragaan",
    "Mikroplastik tetap butuh sampling dan laboratorium",
    "Analisis IKLH masih tingkat provinsi",
    "Survei sampah pesisir dari 2017; data SIPSN Ambon tidak lengkap",
    "Zona prioritas adalah rekomendasi dan tetap perlu verifikasi lapangan",
    "Data lokasi baru lengkap untuk Teluk Ambon",
]

SUMBER_DATA = [
    ("Posisi sampah aktual", "Laporan OceanPatrol", "Dasar hotspot dan zona prioritas"),
    ("Ground truth", "Verifikasi dan survei lapangan", "Mengukur ketepatan zona prioritas"),
    ("IKLH dan faktor penentu", "KLHK, SIPSN 2024, BPS 2024", "Analisis klaster dan spasial provinsi"),
    ("Angin, arus, gelombang, pasang surut", "BMKG, Copernicus Marine", "Rencana: input prediksi pergerakan"),
    ("Curah hujan", "NASA GPM IMERG", "Rencana: penanda kiriman sampah setelah hujan"),
    ("Garis pantai dan batimetri", "BIG atau OpenStreetMap", "Peta dasar dan batas teluk"),
]

STATUS_DATA = [
    ("Lapor, pemetaan hotspot, zona prioritas, verifikasi", "Berfungsi"),
    ("Analisis foto", "Klasifikasi berbasis ciri gambar, akan diganti model deteksi objek terlatih"),
    ("Prediksi pergerakan 24 jam", "Belum aktif, menunggu data arus dan angin resmi"),
    ("Laporan warga", "Data peragaan, laporan lapangan masuk setelah pilot berjalan"),
    ("IKLH 34 provinsi, klaster, LISA, SEM, SIPSN", "Data nyata dari analisis tim"),
    ("Survei sampah pesisir Teluk Ambon", "Data nyata dari literatur"),
]


def _daftar(items, warna):
    li = "".join(f"<li style='margin-bottom:6px;'>{ui.esc(x)}</li>" for x in items)
    return f"<ul style='margin:6px 0 0 0; padding-left:18px; color:#ccd6f6;'>{li}</ul>"


def _daftar_perbaikan(items, warna):
    li = "".join(
        f"<li style='margin-bottom:10px;'><b style='color:{warna};'>{ui.esc(a)}</b><br>"
        f"<span style='color:#8892b0;'>Rencana: {ui.esc(b)}</span></li>" for a, b in items)
    return f"<ul style='margin:6px 0 0 0; padding-left:18px; color:#ccd6f6;'>{li}</ul>"


CAKUPAN = [
    ("Skala nasional: menemukan wilayah berisiko", "Analisis IKLH 34 provinsi dengan K-Means dan Moran's I mengelompokkan wilayah dan menunjukkan "
     "kelompok hotspot spasial. Maluku masuk kelompok hotspot, tetapi data provinsi tidak memperlihatkan titik kritis di dalamnya."),
    ("Skala lokal: membongkar titik kritis", "OceanPatrol bekerja di tingkat teluk. Teluk Ambon dipilih sebagai wilayah awal karena "
     "kepadatan sampah pesisirnya, 68,74 item/m2 di Poka, hampir tidak terlihat pada data agregat."),
    ("Dirancang untuk seluruh pesisir Indonesia", "Alur lapor, analisis, pemetaan, prediksi, prioritas, dan verifikasi tidak terikat satu lokasi. "
     "Laporan dari wilayah lain tetap dapat diterima dan dipetakan dengan koordinatnya."),
    ("Yang perlu disiapkan untuk wilayah baru", "Daftar lokasi acuan dan lokasi sensitif, batas perairan, sumber data kondisi perairan setempat, "
     "serta kalibrasi bobot skor dari hasil verifikasi di wilayah itu."),
]


def render():
    ui.page_header("TENTANG", "SEATRACKER HYBRID",
                   "Mengubah laporan masyarakat pesisir menjadi sistem pemantauan hotspot sampah laut berbasis lokasi.")

    ui.tampil("intro_tentang")

    cols = st.columns(4)
    for i, (judul, isi, warna) in enumerate(FITUR):
        with cols[i]:
            ui.tampil("fitur_card", warna=warna, judul=judul, isi=ui.esc(isi))

    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["Cakupan", "Stakeholder", "Manfaat", "SWOT", "Evaluasi", "Sumber dan status data"])

    with tab0:
        cols = st.columns(2)
        for i, (judul, isi) in enumerate(CAKUPAN):
            with cols[i % 2]:
                ui.info_box(judul.upper(), ui.esc(isi), [COLORS["accent"], COLORS["mint"], COLORS["warning"], COLORS["danger"]][i])


    with tab1:
        cols = st.columns(2)
        for i, (judul, isi) in enumerate(STAKEHOLDER):
            with cols[i % 2]:
                ui.info_box(judul.upper(), ui.esc(isi), [COLORS["mint"], COLORS["accent"], COLORS["warning"], COLORS["danger"]][i])

    with tab2:
        cols = st.columns(2)
        for i, (judul, isi) in enumerate(MANFAAT):
            with cols[i % 2]:
                ui.info_box(f"{i + 1}. {judul.upper()}", ui.esc(isi), COLORS["accent"])
        ui.flow([
            ("MARINE DEBRIS", "Terlihat di laporan"),
            ("HOTSPOT", "Area akumulasi"),
            ("PRIORITAS SAMPLING", "Lokasi terpilih"),
            ("SAMPLING", "Air dan sedimen"),
            ("ANALISIS LAB", "Konfirmasi mikroplastik"),
        ])

    with tab3:
        nama = list(SWOT)
        for baris in (nama[:2], nama[2:]):
            cols = st.columns(2)
            for col, k in zip(cols, baris):
                warna, items = SWOT[k]
                with col:
                    ui.tampil("daftar_card", warna=warna, judul=k, isi=_daftar(items, warna))

    with tab4:
        cols = st.columns([1, 1.5, 1])
        with cols[0]:
            ui.tampil("daftar_card", warna=COLORS["mint"], judul="KELEBIHAN", isi=_daftar(KELEBIHAN, COLORS["mint"]))
        with cols[1]:
            ui.tampil("daftar_card", warna=COLORS["danger"], judul="KEKURANGAN DAN PERBAIKAN",
                      isi=_daftar_perbaikan(KEKURANGAN, COLORS["danger"]))
        with cols[2]:
            ui.tampil("daftar_card", warna=COLORS["warning"], judul="KETERBATASAN", isi=_daftar(KETERBATASAN, COLORS["warning"]))

    with tab5:
        kiri, kanan = st.columns(2)
        with kiri:
            ui.panel_title("SUMBER DATA")
            ui.table(pd.DataFrame(SUMBER_DATA, columns=["Kebutuhan", "Sumber", "Penggunaan"]),
                         width="stretch", hide_index=True)
        with kanan:
            ui.panel_title("STATUS DATA")
            ui.table(pd.DataFrame(STATUS_DATA, columns=["Bagian", "Status"]),
                         width="stretch", hide_index=True)
        ui.md("<p>Kontribusi SDGs: SDG 3 Kehidupan Sehat dan Sejahtera, SDG 12 Konsumsi dan Produksi yang Bertanggung "
              "Jawab, SDG 14 Ekosistem Lautan.</p>")

    ui.info_box("KESIMPULAN",
                "Masalah sampah laut bukan hanya tentang jumlahnya, tetapi tentang mengetahui lokasi mana yang harus "
                "ditangani lebih dulu. OceanPatrol mengubah laporan warga menjadi peta dan prioritas agar penanganan "
                "lebih cepat, tepat, dan terarah.", COLORS["accent"])
