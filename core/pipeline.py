"""Alur utama: Lapor, Analisis, Pemetaan, Prioritas, Verifikasi."""

import streamlit as st

from core import data
from core.hotspot import hitung_hotspot
from core.priority import zona_prioritas


@st.cache_data(show_spinner=False)
def _hotspot(reports_df, places_df):
    return hitung_hotspot(reports_df, places_df)


@st.cache_data(show_spinner=False)
def _zona(hotspot_df, sensitive_df):
    return zona_prioritas(hotspot_df, sensitive_df)


def hotspot(reports_df=None):
    df = data.reports() if reports_df is None else reports_df
    return _hotspot(df, data.places())


def zona():
    return _zona(hotspot(), data.sensitive())
