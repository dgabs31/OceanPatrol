"""Halaman Data IKLH: hasil analisis 34 provinsi dan bukti titik kritis tersembunyi di Maluku."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components import ui
from core import data
from core.config import ASSETS_DIR, COLORS

SUMBER = ("Sumber: data_final_34_provinsi (analisis Tim IRIS PRETTY), SIPSN KLHK 2024, BPS 2024. "
          "Maluku Utara tidak tersedia dalam dataset.")


def _warna_klaster(klaster_df):
    return {r.nama_zona: r.warna for r in klaster_df.itertuples()}


def _kartu_klaster(klaster_df):
    varian = ["green", "purple", "orange"]
    cols = st.columns(3)
    for i, r in enumerate(klaster_df.itertuples()):
        with cols[i]:
            median = f"{r.median_kepadatan:,}".replace(",", ".")
            ui.dash_card(f"KLASTER {r.klaster}: {r.nama_zona.upper()}", f"{r.rata_rata_iklh:.2f}".replace(".", ","),
                         f"Rata-rata IKLH dari {r.jumlah_provinsi} provinsi. Median kepadatan {median} jiwa/km2. "
                         f"{r.wilayah_dominan}.", varian[i])


def _penjelajah(prov):
    ui.section_title("Jelajahi provinsi")
    nama = prov["provinsi"].tolist()
    pilih = st.selectbox("Pilih provinsi", nama, index=nama.index("Maluku"))
    r = prov[prov["provinsi"] == pilih].iloc[0]
    rata_klaster = prov[prov["klaster"] == r["klaster"]]
    peringkat = int(prov["iklh"].rank(ascending=False, method="min")[prov["provinsi"] == pilih].iloc[0])
    sig = "signifikan" if r["lisa_signifikan"] else "tidak signifikan"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.fact(f"{r['iklh']:.2f}", f"IKLH, peringkat {peringkat} dari 34", f"Rata-rata klaster {rata_klaster['iklh'].mean():.2f}", COLORS["accent"])
    with c2:
        ui.fact(f"{r['kepadatan']:,.0f}".replace(",", "."), "jiwa/km2 kepadatan penduduk",
                f"Median nasional {prov['kepadatan'].median():,.0f}".replace(",", "."), COLORS["mint"])
    with c3:
        ui.fact(f"{r['komposisi_plastik']:.1f}%", "komposisi sampah plastik", f"Rata-rata 34 provinsi {prov['komposisi_plastik'].mean():.1f}%", COLORS["warning"])
    with c4:
        ui.fact(r["nama_zona"], f"LISA: {r['lisa_label']}", f"p = {r['lisa_p']:.3f} ({sig})", COLORS["danger"])


def _grafik_provinsi(prov, warna):
    p = prov.sort_values("iklh")
    fig = px.bar(p, x="iklh", y="provinsi", orientation="h", color="nama_zona", color_discrete_map=warna,
                 hover_data={"kepadatan": True, "komposisi_plastik": ":.1f", "lisa_label": True})
    garis = ["#ffffff" if x == "Maluku" else "rgba(0,0,0,0)" for x in p["provinsi"]]
    fig.update_traces(marker_line_width=2)
    for tr in fig.data:
        tr.marker.line.color = [g for g, z in zip(garis, p["nama_zona"]) if z == tr.name]
    fig.update_yaxes(title=None, tickfont=dict(size=10))
    fig.update_xaxes(title="IKLH", range=[50, 86])
    fig.update_layout(legend_title_text="")
    return ui.style_fig(fig, 760)


def _analisis_spasial():
    ui.section_title("Analisis spasial")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.fact("0,3396", "Silhouette K-Means (k = 3)", "Klaster cukup terpisah", COLORS["accent"])
    with c2:
        ui.fact("0,6202", "Moran's I (p = 0,001)", "IKLH mengelompok secara spasial", COLORS["mint"])
    with c3:
        ui.fact("0,7318", "Pseudo R2 model SEM", "Menjelaskan sekitar 73% variasi IKLH", COLORS["warning"])
    with c4:
        ui.fact("165,55", "AIC model SEM", "Terendah dibanding OLS dan SAR", COLORS["danger"])

    kiri, kanan = st.columns([1, 1.2])
    with kiri:
        ui.panel_title("PERBANDINGAN MODEL")
        m = data.baca_csv("model_spasial.csv")
        fig = go.Figure(go.Bar(x=m["model"], y=m["aic"], text=m["aic"], textposition="outside",
                               marker_color=[COLORS["accent2"], COLORS["accent2"], COLORS["mint"]]))
        fig.update_yaxes(title="AIC (makin kecil makin baik)", range=[150, 180])
        st.plotly_chart(ui.style_fig(fig, 260), width="stretch")
        ui.table(m.rename(columns={"r2": "R2 / Pseudo R2", "aic": "AIC", "rmse": "RMSE"}),
                     width="stretch", hide_index=True)
    with kanan:
        ui.panel_title("KOEFISIEN SPATIAL ERROR MODEL")
        for r in data.baca_csv("koefisien_sem.csv").itertuples():
            warna = COLORS["danger"] if r.arah == "Negatif" else COLORS["mint"]
            if r.signifikan != "Ya":
                warna = COLORS["muted"]
            ket = "signifikan" if r.signifikan == "Ya" else "tidak signifikan"
            ui.tampil("koef_card", warna=warna, variabel=ui.esc(r.variabel), koefisien=f"{r.koefisien:+.4f}",
                      p_value=f"{r.p_value:.4f}", ket=ket, keterangan=ui.esc(r.keterangan))


def _lisa(prov):
    ui.panel_title("LISA: KELOMPOK PROVINSI YANG SIGNIFIKAN (p &lt; 0,05)")
    sig = prov[prov["lisa_signifikan"]]
    hh = ", ".join(sig[sig["lisa_label"].str.startswith("HH")]["provinsi"])
    ll = ", ".join(sig[sig["lisa_label"].str.startswith("LL")]["provinsi"])
    a, b = st.columns(2)
    with a:
        ui.info_box("HOT SPOT (IKLH TINGGI BERKELOMPOK)", hh, COLORS["mint"])
    with b:
        ui.info_box("COLD SPOT (IKLH RENDAH BERKELOMPOK)", ll, COLORS["danger"])


def _maluku():
    ui.section_title("Titik kritis tersembunyi: Maluku dan Teluk Ambon")
    kiri, kanan = st.columns([1, 1.1])
    with kiri:
        ui.info_box("DI TINGKAT PROVINSI MALUKU TERLIHAT AMAN",
                    "IKLH Maluku 78,59, masuk Zona Pengawasan, dan menjadi bagian hot spot IKLH tinggi (LISA, p = 0,001). "
                    "Kepadatan provinsinya hanya 42 jiwa/km2.", COLORS["mint"])
        ui.info_box("DI TINGKAT LOKAL CERITANYA BERBEDA",
                    "Kota Ambon menyumbang sekitar 34% timbulan sampah Maluku yang tercatat di SIPSN 2024 "
                    "(247,84 ton per hari), tetapi data komposisi sampahnya kosong. Artinya angka plastik provinsi tidak "
                    "memasukkan Ambon. Di lapangan, Poka di Teluk Ambon Dalam mencapai 68,74 item/m2.", COLORS["danger"])
        ui.source_note("SIPSN 2024 hanya memuat 6 kabupaten/kota Maluku. Data survei Poka: sampel 2017, terbit 2021.")
    with kanan:
        ui.panel_title("TIMBULAN SAMPAH HARIAN MALUKU (SIPSN 2024)")
        t = data.baca_csv("timbulan_maluku_sipsn2024.csv").sort_values("timbulan_harian_ton")
        warna = [COLORS["danger"] if k == "Kota Ambon" else COLORS["accent2"] for k in t["kabkota"]]
        fig = go.Figure(go.Bar(x=t["timbulan_harian_ton"], y=t["kabkota"], orientation="h", marker_color=warna,
                               text=t["timbulan_harian_ton"].map(lambda v: f"{v:.1f}"), textposition="outside"))
        fig.update_xaxes(title="ton per hari", range=[0, 300])
        fig.update_yaxes(title=None)
        st.plotly_chart(ui.style_fig(fig, 300), width="stretch")


def render():
    ui.page_header("ANALISIS DATA", "MEMBONGKAR TITIK KRITIS TERSEMBUNYI",
                   "K-Means, Moran's I, LISA, dan Spatial Error Model pada IKLH 34 provinsi Indonesia.")

    prov = data.baca_csv("iklh_provinsi.csv")
    klaster = data.baca_csv("klaster_iklh.csv")
    warna = _warna_klaster(klaster)

    _kartu_klaster(klaster)

    peta, grafik = st.columns([1.35, 1])
    with peta:
        ui.panel_title("PETA KLASTER IKLH")
        st.image(str(ASSETS_DIR / "peta_klaster.png"), width="stretch")
        _lisa(prov)
    with grafik:
        ui.panel_title("IKLH PER PROVINSI (MALUKU DIBERI GARIS PUTIH)")
        st.plotly_chart(_grafik_provinsi(prov, warna), width="stretch")

    _penjelajah(prov)
    _analisis_spasial()
    _maluku()

    ui.section_title("Biaya yang harus dibayar")
    c1, c2, c3 = st.columns(3)
    with c1:
        ui.fact("23,7%", "PDRB Maluku berasal dari sektor perikanan dan pertanian", "Poster OceanPatrol", COLORS["mint"])
    with c2:
        ui.fact("US$ 0,3 - 0,8 miliar", "kerugian ekonomi nasional per tahun di sektor perikanan dan pariwisata",
                "Poster OceanPatrol", COLORS["danger"])
    with c3:
        ui.fact("67,1%", "sampah di BTN Passo Indah, Negeri Lama didominasi plastik", "Poster OceanPatrol", COLORS["warning"])

    with st.expander("Lihat dan unduh data 34 provinsi"):
        ui.table(prov, width="stretch", hide_index=True)
        st.download_button("UNDUH DATA IKLH (CSV)", prov.to_csv(index=False), "iklh_34_provinsi.csv", "text/csv")
    ui.source_note(SUMBER)
