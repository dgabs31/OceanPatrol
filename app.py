"""OceanPatrol | SeaTracker Hybrid

File utama yang dijalankan Streamlit. Tugasnya hanya:
1. mengatur halaman dan memuat CSS,
2. menampilkan navbar,
3. memanggil halaman yang dipilih dari folder views.
"""

import streamlit as st

from components import ui
from core import data
from core.config import NAV_ITEMS
from views import (
    analisis_ai,
    dashboard,
    data_iklh,
    lapor,
    mikroplastik,
    pemetaan,
    prediksi,
    prioritas,
    tentang,
    verifikasi,
)

st.set_page_config(
    page_title="OceanPatrol | SeaTracker Hybrid",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ui.load_css()
data.init_state()

HALAMAN = {
    "Dashboard": dashboard.render,
    "Lapor": lapor.render,
    "Analisis": analisis_ai.render,
    "Pemetaan": pemetaan.render,
    "Prediksi": prediksi.render,
    "Prioritas": prioritas.render,
    "Verifikasi": verifikasi.render,
    "Mikroplastik": mikroplastik.render,
    "Data IKLH": data_iklh.render,
    "Tentang": tentang.render,
}


def muat_skenario_demo():
    """Mengembalikan data demo lalu menambah tiga laporan baru di Pasar Mardika."""
    data.reset_demo()
    now = data.sekarang_wit()
    titik = [(-3.6872, 128.1798, "Kantong plastik", "Banyak"),
             (-3.6880, 128.1810, "Plastik kemasan", "Banyak"),
             (-3.6866, 128.1822, "Styrofoam", "Sedang")]
    baru = []
    for i, (lat, lon, kat, jml) in enumerate(titik):
        baru.append(data.tambah_laporan({
            "timestamp": now.strftime("%Y-%m-%d %H:%M"),
            "latitude": lat,
            "longitude": lon,
            "lokasi": "Pasar Mardika",
            "jenis": "Terapung" if i < 2 else "Terdampar",
            "kategori": kat,
            "ai_kategori": kat,
            "estimasi_jumlah": jml,
            "pelapor": "Nelayan",
            "confidence": 0.9 - i * 0.03,
            "status": "Menunggu verifikasi",
            "foto": "foto_lapangan.jpg",
        }))
    st.session_state["laporan_demo"] = baru
    st.session_state["page"] = "Prioritas"


with st.container(key="navbar"):
    col_logo, col_nav, col_demo = st.columns([2.2, 8.3, 2.0])
    with col_logo:
        ui.tampil("brand")
    with col_nav:
        with st.container(key="navlinks"):
            for item in NAV_ITEMS:
                if st.button(item, key=f"nav_{item.replace(' ', '_')}"):
                    st.session_state["page"] = item
    with col_demo:
        if st.button("LAPORAN BARU", width="stretch"):
            muat_skenario_demo()

page = st.session_state["page"]
ui.tampil("nav_aktif", kunci=page.replace(" ", "_"))

HALAMAN.get(page, dashboard.render)()

ui.tampil("footer")
