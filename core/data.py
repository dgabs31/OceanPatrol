"""Membaca data CSV dan menyimpan data sesi (laporan baru, verifikasi)."""

import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from core.config import DATA_DIR

WIT = timezone(timedelta(hours=9))  # zona waktu Ambon


@st.cache_data
def baca_csv(nama):
    path = DATA_DIR / nama
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


@st.cache_data
def baca_geojson(nama):
    with open(DATA_DIR / nama, encoding="utf-8") as f:
        return json.load(f)


def sekarang_wit():
    return datetime.now(WIT)


def init_state():
    """Mengisi session_state sekali di awal sesi."""
    if "reports" not in st.session_state:
        st.session_state["reports"] = baca_csv("reports.csv").copy()
    if "verification" not in st.session_state:
        st.session_state["verification"] = baca_csv("verification.csv").copy()
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"


def reports():
    return st.session_state["reports"]


def places():
    return baca_csv("lokasi.csv")


def sensitive():
    return baca_csv("lokasi_sensitif.csv")


def survey():
    return baca_csv("survei_literatur.csv")


def tambah_laporan(data):
    df = st.session_state["reports"]
    nomor = len(df) + 1
    data = {"report_id": f"RPT-{nomor:03d}", **data}
    st.session_state["reports"] = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    return data["report_id"]


def ubah_status_laporan(report_id, status):
    df = st.session_state["reports"]
    df.loc[df["report_id"] == report_id, "status"] = status


def tambah_verifikasi(data):
    df = st.session_state["verification"]
    data = {"verification_id": f"V-{len(df) + 1:03d}", **data}
    st.session_state["verification"] = pd.concat([df, pd.DataFrame([data])], ignore_index=True)


def reset_demo():
    st.session_state["reports"] = baca_csv("reports.csv").copy()
    st.session_state["verification"] = baca_csv("verification.csv").copy()
    for k in ["lapor_lat", "lapor_lon", "laporan_demo", "hasil_lapor"]:
        st.session_state.pop(k, None)
