"""Halaman Lapor: warga dan nelayan mengirim foto, lokasi, waktu, dan jenis sampah."""

import folium
import streamlit as st

from components import maps, ui
from core import data
from core.classifier import analisis_foto
from core.config import COLORS, KATEGORI_SAMPAH
from core.geo import di_area_pilot, nama_lokasi, point_in_polygon

try:
    from streamlit_js_eval import get_geolocation
    ADA_GPS = ui.ADA_PYARROW  # komponen Streamlit memerlukan pyarrow
except Exception:
    ADA_GPS = False

LAT_AWAL, LON_AWAL = -3.6560, 128.2030


def _terapkan_gps():
    """Membaca lokasi perangkat dari browser dan mengisinya sekali ke formulir dan peta."""
    if not ADA_GPS:
        return None
    hasil = get_geolocation()
    koordinat = (hasil or {}).get("coords") if isinstance(hasil, dict) else None
    if not koordinat:
        return None
    lat, lon = round(koordinat["latitude"], 5), round(koordinat["longitude"], 5)
    sidik = (lat, lon)
    if st.session_state.get("gps_terpakai") != sidik:
        st.session_state["gps_terpakai"] = sidik
        st.session_state["lapor_lat"], st.session_state["lapor_lon"] = lat, lon
        st.session_state["in_lat"], st.session_state["in_lon"] = lat, lon
        st.session_state["gps_akurasi"] = koordinat.get("accuracy")
        st.rerun()
    return sidik


def _peta_pilih_lokasi():
    lat = st.session_state.get("lapor_lat", LAT_AWAL)
    lon = st.session_state.get("lapor_lon", LON_AWAL)
    m = maps.base_map(center=[lat, lon], zoom=15)
    maps.add_water_outline(m)
    folium.Marker([lat, lon], icon=folium.Icon(color="lightblue", icon="map-marker"), tooltip="Lokasi laporan").add_to(m)
    out = maps.show(m, 430, "map_lapor", ambil_klik=True)
    klik = (out or {}).get("last_clicked")
    if klik:
        baru = (round(klik["lat"], 5), round(klik["lng"], 5))
        if baru != (round(lat, 5), round(lon, 5)):
            st.session_state["lapor_lat"], st.session_state["lapor_lon"] = baru
            st.session_state["in_lat"], st.session_state["in_lon"] = baru
            st.rerun()


def _pakai_lokasi_daftar():
    """Mengisi koordinat dari daftar lokasi (cadangan bila klik peta tidak tersedia)."""
    nama = st.session_state.get("pilih_tempat")
    tempat = data.places()
    baris = tempat[tempat["nama"] == nama]
    if not baris.empty:
        lat, lon = float(baris["latitude"].iat[0]), float(baris["longitude"].iat[0])
        st.session_state["lapor_lat"], st.session_state["lapor_lon"] = lat, lon
        st.session_state["in_lat"], st.session_state["in_lon"] = lat, lon


def _tampilkan_hasil(h):
    ui.info_box("HASIL ANALISIS FOTO",
                f"Sampah laut terlihat pada foto. Laporan <b>{h['report_id']}</b> masuk antrean verifikasi.",
                COLORS["mint"])
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Kategori AI**<br><span style='font-size:1.4rem; color:#00d2ff;'>{h['label']}</span>", unsafe_allow_html=True)
    c2.markdown(f"**Keyakinan**<br><span style='font-size:1.4rem; color:#64ffda;'>{h['keyakinan']:.0%}</span>", unsafe_allow_html=True)
    c3.markdown(f"**Konfirmasi pelapor**<br><span style='font-size:1.4rem; color:#e6f1ff;'>{h['kategori']}</span>", unsafe_allow_html=True)
    bars = "".join(ui.tpl("kandidat_bar", label=f"{k} {v:.0%}", bar=ui.bar(v / h["kandidat"][0][1]))
                   for k, v in h["kandidat"])
    ui.tampil("kandidat_card", bars=bars)
    if st.button("LIHAT DI HALAMAN ANALISIS", key="ke_analisis"):
        ui.go_to("Analisis")


def render():
    ui.page_header("LANGKAH 1: LAPOR", "LAPOR SAMPAH LAUT",
                   "Warga dan nelayan menjadi sensor pesisir: kirim foto, lokasi, waktu, dan jenis sampah.")

    st.session_state.setdefault("in_lat", st.session_state.get("lapor_lat", LAT_AWAL))
    st.session_state.setdefault("in_lon", st.session_state.get("lapor_lon", LON_AWAL))

    # Lokasi perangkat diminta saat halaman dibuka (browser menampilkan izin lokasi sekali).
    gps = _terapkan_gps()

    kiri, kanan = st.columns([1.1, 1])
    with kanan:
        ui.panel_title("LOKASI LAPORAN")
        if gps:
            akurasi = st.session_state.get("gps_akurasi")
            ket = f" (akurasi sekitar {akurasi:.0f} m)" if akurasi else ""
            ui.info_box("LOKASI TERDETEKSI", f"Koordinat diambil dari perangkat Anda{ket}. Klik peta untuk memindahkan titik.",
                        COLORS["mint"])
        else:
            ui.source_note("Izinkan akses lokasi di browser agar titik laporan terisi otomatis, "
                           "atau klik peta, atau pilih lokasi dari daftar.")
        st.selectbox("Atau pilih lokasi terdekat dari daftar", data.places()["nama"].tolist(), index=None,
                     placeholder="Pilih lokasi", key="pilih_tempat", on_change=_pakai_lokasi_daftar)
        _peta_pilih_lokasi()
        nama, jarak = nama_lokasi(st.session_state["in_lat"], st.session_state["in_lon"], data.places())
        ui.source_note(f"Lokasi terdekat: {nama}" + (f" ({jarak / 1000:.1f} km)." if jarak and jarak > 1000 else f" ({jarak:.0f} m)."))

    with kiri:
        with st.form("form_lapor", clear_on_submit=False):
            foto = st.file_uploader("Foto sampah (wajib)", type=["jpg", "jpeg", "png"])
            a, b = st.columns(2)
            jenis = a.radio("Kondisi sampah", ["Terapung", "Terdampar"], horizontal=True)
            jumlah = b.select_slider("Perkiraan jumlah", ["Sedikit", "Sedang", "Banyak"], value="Sedang")
            kategori = st.selectbox("Jenis sampah menurut pelapor", KATEGORI_SAMPAH)
            with st.expander("Koordinat (terisi otomatis, bisa diubah)"):
                a, b = st.columns(2)
                lat = a.number_input("Latitude", format="%.5f", key="in_lat")
                lon = b.number_input("Longitude", format="%.5f", key="in_lon")
            a, b = st.columns(2)
            now = data.sekarang_wit()
            tgl = a.date_input("Tanggal", value=now.date())
            jam = b.time_input("Waktu (WIT)", value=now.time().replace(second=0, microsecond=0))
            pelapor = st.selectbox("Pelapor", ["Nelayan", "Warga", "Petugas DLH"])
            st.text_area("Catatan (opsional)", placeholder="Contoh: sampah mengumpul di dekat keramba")
            kirim = st.form_submit_button("KIRIM DAN ANALISIS")

        if kirim:
            if foto is None:
                st.error("Unggah foto terlebih dahulu agar sampah bisa dianalisis.")
            elif jenis == "Terapung" and di_area_pilot(lat, lon) and not point_in_polygon(lat, lon):
                st.warning("Titik berada di luar batas perairan. Untuk sampah terapung, pilih titik di laut.")
            else:
                with st.spinner("Menganalisis foto..."):
                    hasil = analisis_foto(foto.getvalue())
                nama, _ = nama_lokasi(lat, lon, data.places())
                rid = data.tambah_laporan({
                    "timestamp": f"{tgl:%Y-%m-%d} {jam:%H:%M}",
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "lokasi": nama,
                    "jenis": jenis,
                    "kategori": kategori,
                    "ai_kategori": hasil["label"],
                    "estimasi_jumlah": jumlah,
                    "pelapor": pelapor,
                    "confidence": hasil["keyakinan"],
                    "status": "Menunggu verifikasi",
                    "foto": foto.name,
                })
                st.session_state["hasil_lapor"] = {**hasil, "report_id": rid, "kategori": kategori, "jenis": jenis}

        if "hasil_lapor" in st.session_state:
            _tampilkan_hasil(st.session_state["hasil_lapor"])

    st.markdown("<br>", unsafe_allow_html=True)
    ui.section_title("Laporan terbaru")
    df = data.reports().sort_values("timestamp", ascending=False).head(8)
    ui.table(
        df[["report_id", "timestamp", "lokasi", "jenis", "kategori", "estimasi_jumlah", "pelapor", "status"]],
        width="stretch", hide_index=True,
    )
