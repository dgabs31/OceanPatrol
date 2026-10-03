"""Pembuat peta Folium untuk semua halaman."""

import copy
import json
from functools import lru_cache

import folium
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import HeatMap, MarkerCluster

from components import ui
from core.config import COLORS, DATA_DIR, JUMLAH_BOBOT, LEVEL_COLORS, MAP_CENTER, MAP_ZOOM
from core.geo import load_water_polygon

# Peta dasar gelap dari Esri (tanpa kunci API). Carto tidak dipakai lagi karena kini meminta kunci API.
TILE_GELAP = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
TILE_ATRIBUSI = "Tiles &copy; Esri"
TILE_CADANGAN = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


try:
    import pyarrow  # noqa: F401  dibutuhkan streamlit-folium
    from streamlit_folium import st_folium
    PETA_INTERAKTIF = True
except Exception:
    # Sebagian laptop Windows memblokir DLL pyarrow (Application Control).
    # Peta tetap tampil sebagai HTML biasa, hanya klik peta yang tidak terbaca.
    PETA_INTERAKTIF = False


def show(m, height, key, ambil_klik=False):
    """Menampilkan peta. Mengembalikan data klik jika tersedia, selain itu None."""
    if PETA_INTERAKTIF:
        objek = ["last_clicked"] if ambil_klik else []
        return st_folium(m, width="100%", height=height, returned_objects=objek, key=key)
    halaman = m.get_root().render()
    if hasattr(st, "iframe"):
        st.iframe(halaman, height=height)
    else:
        components.html(halaman, height=height)
    return None


# Tampilan peta yang bisa dipilih pengguna: pusat dan tingkat zoom awal.
VIEWS = {
    "Teluk Ambon": (MAP_CENTER, MAP_ZOOM),
    "Indonesia": ([-2.6, 118.0], 5),
    "Dunia": ([5.0, 110.0], 2),
}


def pilih_tampilan(key, default="Indonesia"):
    """Pilihan Teluk Ambon / Indonesia / Dunia di atas peta."""
    pilih = st.segmented_control("Tampilan peta", list(VIEWS), default=default, key=key,
                                 label_visibility="collapsed")
    return pilih or default


def base_map(center=None, zoom=MAP_ZOOM, view=None):
    if view in VIEWS:
        center, zoom = VIEWS[view]
    m = folium.Map(location=center or MAP_CENTER, zoom_start=zoom, tiles=None, control_scale=True,
                   min_zoom=2, zoom_snap=0.25 if view in ("Indonesia", "Dunia") else 1)
    folium.Element(ui.tpl("map_gaya")).add_to(m.get_root().html)
    # Batas tampilan dipasang agar seluruh Indonesia atau seluruh dunia selalu pas di layar berapa pun ukurannya.
    if view == "Indonesia":
        m.fit_bounds([[-11.5, 94.5], [6.5, 141.5]])
    elif view == "Dunia":
        m.fit_bounds([[-50, -170], [78, 178]])
    folium.TileLayer(TILE_GELAP, attr=TILE_ATRIBUSI, name="Peta gelap", max_zoom=19, max_native_zoom=16).add_to(m)
    folium.TileLayer(TILE_CADANGAN, attr="&copy; OpenStreetMap contributors", name="Peta jalan (cadangan)",
                     max_zoom=19, show=False, className="op-osm-gelap").add_to(m)
    return m


def add_water_outline(m):
    poly = load_water_polygon()
    folium.Polygon(
        locations=list(poly), color=COLORS["accent2"], weight=1, opacity=0.35,
        fill=True, fill_opacity=0.04, tooltip="Batas perairan Teluk Ambon",
    ).add_to(m)


def add_heatmap(m, reports_df, name="Hotspot laporan"):
    df = reports_df[reports_df["status"] != "Ditolak"]
    if df.empty:
        return
    pts = [[r.latitude, r.longitude, JUMLAH_BOBOT.get(r.estimasi_jumlah, 1)] for r in df.itertuples()]
    HeatMap(pts, name=name, radius=22, blur=16, min_opacity=0.35,
            gradient={0.4: COLORS["accent2"], 0.65: COLORS["accent"], 1: COLORS["danger"]}).add_to(m)


def add_reports(m, reports_df, name="Laporan warga"):
    if reports_df.empty:
        return
    g = folium.FeatureGroup(name=name)
    warna = {"Terverifikasi": "#ffffff", "Menunggu verifikasi": COLORS["warning"], "Ditolak": "#5a6478"}
    for r in reports_df.itertuples():
        c = warna.get(r.status, "#ffffff")
        folium.CircleMarker(
            [r.latitude, r.longitude], radius=6 if r.jenis == "Terapung" else 4,
            color=c, fill=True, fill_color=c, fill_opacity=0.85, weight=1,
            popup=folium.Popup(
                f"<b>{r.report_id}</b><br>{r.lokasi}<br>{r.kategori} ({r.jenis})<br>"
                f"Jumlah: {r.estimasi_jumlah}<br>Status: {r.status}<br>{r.timestamp}", max_width=220),
        ).add_to(g)
    g.add_to(m)


def add_survey(m, survey_df):
    g = folium.FeatureGroup(name="Data survei literatur")
    for r in survey_df.dropna(subset=["latitude"]).itertuples():
        info = []
        if r.kepadatan_item_m2 == r.kepadatan_item_m2:
            info.append(f"{r.kepadatan_item_m2} item/m2")
        if r.plastik_persen == r.plastik_persen:
            info.append(f"Plastik {r.plastik_persen}%")
        folium.Marker(
            [r.latitude, r.longitude],
            icon=folium.Icon(color="purple", icon="info-sign"),
            popup=folium.Popup(f"<b>{r.stasiun}</b><br>{'<br>'.join(info)}<br>{r.catatan}<br><i>{r.sumber}</i>", max_width=240),
        ).add_to(g)
    g.add_to(m)


def add_sensitive(m, sensitive_df):
    g = folium.FeatureGroup(name="Lokasi sensitif")
    for r in sensitive_df.itertuples():
        folium.CircleMarker(
            [r.latitude, r.longitude], radius=9, color=COLORS["mint"], weight=2, fill=False,
            dash_array="4 4", popup=folium.Popup(f"<b>{r.nama}</b><br>{r.jenis}<br>{r.keterangan}", max_width=220),
        ).add_to(g)
    g.add_to(m)


def add_zones(m, zones_df):
    if zones_df is None or zones_df.empty:
        return
    g = folium.FeatureGroup(name="Zona prioritas")
    for r in zones_df.itertuples():
        warna = LEVEL_COLORS.get(r.prioritas, COLORS["warning"])
        folium.Circle([r.latitude, r.longitude], radius=200 + 300 * r.skor, color=warna,
                      fill=True, fill_opacity=0.18, weight=1).add_to(g)
        folium.CircleMarker(
            [r.latitude, r.longitude], radius=11 + 9 * r.skor, color="#ffffff", weight=2,
            fill=True, fill_color=warna, fill_opacity=0.95,
            tooltip=f"{r.zone_id} {r.lokasi} ({r.prioritas})",
            popup=folium.Popup(
                f"<b>{r.zone_id} {r.lokasi}</b><br>Prioritas: {r.prioritas} (skor {r.skor:.2f})<br>"
                f"{r.jumlah_laporan} laporan, {r.menunggu} menunggu verifikasi", max_width=230),
        ).add_to(g)
    g.add_to(m)


def add_hotspot_cells(m, hs_df):
    """Hotspot sebagai lingkaran besar berwarna menurut tingkat, ukurannya mengikuti indeks kepadatan."""
    if hs_df is None or hs_df.empty:
        return
    g = folium.FeatureGroup(name="Peringkat hotspot")
    for r in hs_df.itertuples():
        warna = LEVEL_COLORS.get(r.tingkat, COLORS["accent"])
        folium.Circle([r.latitude, r.longitude], radius=450, color=warna, weight=1, fill=True,
                      fill_opacity=0.12).add_to(g)
        folium.CircleMarker(
            [r.latitude, r.longitude], radius=10 + 12 * r.indeks, color="#ffffff", weight=2,
            fill=True, fill_color=warna, fill_opacity=0.95,
            tooltip=f"#{r.peringkat} {r.lokasi} ({r.tingkat}), {r.jumlah_laporan} laporan",
        ).add_to(g)
    g.add_to(m)


@lru_cache(maxsize=None)
def _baca_geojson(nama):
    return json.loads((DATA_DIR / nama).read_text(encoding="utf-8"))


def add_dunia(m):
    """Daratan seluruh negara sebagai gambar vektor. Tetap tampil walau peta dasar online gagal dimuat."""
    folium.GeoJson(
        _baca_geojson("dunia_negara.geojson"), name="Negara",
        style_function=lambda f: {"fillColor": "#16304f", "color": "#2c4a73", "weight": 0.8, "fillOpacity": 1},
        tooltip=folium.GeoJsonTooltip(fields=["nama"], labels=False),
    ).add_to(m)


def add_provinsi_poligon(m, prov_df, klaster_df):
    """Peta Indonesia: tiap provinsi diwarnai menurut klaster IKLH. Maluku diberi garis putih tebal."""
    warna_k = dict(zip(klaster_df["klaster"], klaster_df["warna"]))
    info = {}
    for r in prov_df.itertuples():
        lisa = f" | LISA: {r.lisa_label}" if r.lisa_signifikan else ""
        info[r.provinsi] = {"warna": warna_k.get(r.klaster, "#8892b0"),
                            "teks": f"{r.provinsi}: {r.nama_zona}, IKLH {r.iklh:.2f}{lisa}"}
    data_geo = copy.deepcopy(_baca_geojson("indonesia_provinsi.geojson"))
    for f in data_geo["features"]:
        n = f["properties"]["provinsi"]
        f["properties"]["teks"] = info.get(n, {}).get("teks", f"{n}: tidak ada dalam dataset")
        f["properties"]["warna"] = info.get(n, {}).get("warna", "#3a4a63")
    def gaya(f):
        maluku = f["properties"]["provinsi"] == "Maluku"
        return {"fillColor": f["properties"]["warna"], "fillOpacity": 0.82,
                "color": "#ffffff" if maluku else "#0a192f", "weight": 3 if maluku else 0.9}
    folium.GeoJson(
        data_geo, name="Klaster IKLH provinsi", style_function=gaya,
        highlight_function=lambda f: {"weight": 2.5, "color": "#ffffff", "fillOpacity": 0.95},
        tooltip=folium.GeoJsonTooltip(fields=["teks"], labels=False, sticky=True),
    ).add_to(m)


def add_provinsi(m, prov_df, klaster_df):
    """Satu lingkaran per provinsi, warnanya mengikuti klaster IKLH. Maluku diberi lingkaran lebih besar."""
    warna_k = dict(zip(klaster_df["klaster"], klaster_df["warna"]))
    g = folium.FeatureGroup(name="Klaster IKLH provinsi")
    for r in prov_df.itertuples():
        warna = warna_k.get(r.klaster, "#8892b0")
        maluku = r.provinsi == "Maluku"
        lisa = f"<br>LISA: {r.lisa_label}" if r.lisa_signifikan else ""
        folium.CircleMarker(
            [r.lat, r.lon], radius=26 if maluku else 10, color="#ffffff", weight=3 if maluku else 2,
            fill=True, fill_color=warna, fill_opacity=0.5 if maluku else 0.92,
            tooltip=folium.Tooltip(r.provinsi, permanent=maluku, direction="top"),
            popup=folium.Popup(
                f"<b>{r.provinsi}</b><br>{r.nama_zona}<br>IKLH {r.iklh:.2f}<br>"
                f"Kepadatan {r.kepadatan:,.0f} jiwa/km2{lisa}".replace(",", "."), max_width=230),
        ).add_to(g)
    g.add_to(m)


def add_laporan_klaster(m, reports_df, name="Laporan OceanPatrol"):
    """Laporan dikelompokkan otomatis: jadi satu gelembung saat jauh, terurai saat didekati."""
    df = reports_df[reports_df["status"] != "Ditolak"]
    if df.empty:
        return
    ikon = ("function(c){var n=c.getChildCount();var s=n<10?38:(n<100?46:54);"
            "return L.divIcon({html:'<div style=\"width:'+s+'px;height:'+s+'px;line-height:'+(s-6)+'px;\">'+n+'</div>',"
            "className:'op-cluster',iconSize:L.point(s,s)});}")
    g = MarkerCluster(name=name, icon_create_function=ikon, options={"maxClusterRadius": 55})
    for r in df.itertuples():
        folium.CircleMarker(
            [r.latitude, r.longitude], radius=7, color="#ffffff", weight=2, fill=True,
            fill_color=COLORS["accent"], fill_opacity=0.95,
            popup=folium.Popup(f"<b>{r.report_id}</b><br>{r.lokasi}<br>{r.kategori} ({r.jenis})<br>"
                               f"Status: {r.status}<br>{r.timestamp}", max_width=220),
        ).add_to(g)
    g.add_to(m)


def add_legend_nasional(m, klaster_df):
    items = [(r.warna, f"{r.nama_zona} ({r.jumlah_provinsi} provinsi)") for r in klaster_df.itertuples()]
    items.append(("#3a4a63", "Tidak ada dalam dataset"))
    items.append((COLORS["accent"], "Laporan OceanPatrol"))
    add_legend(m, "KLASTER IKLH PROVINSI", items)


def peta_luas(view, reports_df, prov_df, klaster_df):
    """Peta tingkat Indonesia atau dunia: klaster IKLH provinsi dan sebaran laporan."""
    m = base_map(view=view)
    add_dunia(m)
    add_provinsi_poligon(m, prov_df, klaster_df)
    add_laporan_klaster(m, reports_df)
    add_legend_nasional(m, klaster_df)
    return finish(m)


def add_legend(m, judul, items):
    """Kartu legenda di dalam peta (pojok kiri bawah). items: list (warna, label)."""
    isi = "".join(ui.tpl("map_legend_item", warna=c, teks=ui.esc(t)) for c, t in items)
    html = ui.tpl("map_legend", judul=ui.esc(judul), isi=isi)
    folium.Element(html).add_to(m.get_root().html)


def add_sampling(m, sampling_df):
    g = folium.FeatureGroup(name="Rencana sampling mikroplastik")
    for r in sampling_df.itertuples():
        folium.CircleMarker([r.latitude, r.longitude], radius=8, color=COLORS["accent"], fill=True,
                            fill_color=COLORS["accent"], fill_opacity=0.6,
                            popup=folium.Popup(f"<b>{r.kode}</b> {r.lokasi}<br>{r.alasan}<br>Metode: {r.metode}", max_width=240)).add_to(g)
    g.add_to(m)


def finish(m):
    folium.LayerControl(collapsed=True).add_to(m)
    return m
