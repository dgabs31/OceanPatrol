"""Potongan tampilan yang dipakai berulang di banyak halaman.

Kerangka HTML tidak ditulis di sini. Semua ada di assets/templates/*.html,
gayanya di assets/style.css. File ini hanya membaca template dan mengisi nilainya.
"""

import html
from functools import lru_cache

import streamlit as st

from core.config import ASSETS_DIR, COLORS

TEMPLATE_DIR = ASSETS_DIR / "templates"

try:
    import pyarrow  # noqa: F401
    ADA_PYARROW = True
except Exception:
    ADA_PYARROW = False


def load_css():
    css = (ASSETS_DIR / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@lru_cache(maxsize=None)
def _baca_template(nama):
    return (TEMPLATE_DIR / f"{nama}.html").read_text(encoding="utf-8")


def tpl(nama, **nilai):
    """Mengisi template. Penanda {{kunci}} diganti dengan nilainya. Nilai tidak di-escape otomatis."""
    isi = _baca_template(nama)
    for kunci, v in nilai.items():
        isi = isi.replace("{{" + kunci + "}}", str(v))
    return isi


def md(s):
    """Menampilkan HTML. Baris kosong dibuang agar blok HTML tidak terpotong."""
    s = "\n".join(line.strip() for line in str(s).splitlines() if line.strip())
    st.markdown(s, unsafe_allow_html=True)


def tampil(nama, **nilai):
    """Isi template lalu tampilkan di halaman."""
    md(tpl(nama, **nilai))


def esc(x):
    return html.escape(str(x))


def page_header(eyebrow, title, subtitle=""):
    tampil("page_head", eyebrow=esc(eyebrow), title=esc(title), subtitle=esc(subtitle))


def panel_title(teks, style=""):
    tampil("panel_title", teks=teks, style=style)


def section_title(teks, style=""):
    tampil("section_title", teks=teks, style=style)


def badge(text, color=COLORS["warning"]):
    return tpl("badge", teks=esc(text), color=color)


def dash_card(title, value, desc, variant="green"):
    tampil("dash_card", title=esc(title), value=esc(value), desc=esc(desc), variant=variant)


def fact(num, label, source="", color=COLORS["accent"]):
    sumber = tpl("fact_sumber", teks=esc(source)) if source else ""
    tampil("fact", num=esc(num), label=esc(label), sumber=sumber, color=color)


def stat_row(label, value, sub=""):
    s = tpl("stat_sub", teks=esc(sub)) if sub else ""
    return tpl("stat_row", label=esc(label), value=esc(value), sub=s)


def info_box(title, body, color=COLORS["mint"]):
    tampil("info_box", title=esc(title), body=body, color=color, latar=_rgba(color, 0.1))


def flow(steps, active=None):
    """steps: list (judul, keterangan)."""
    bagian = []
    for i, (judul, ket) in enumerate(steps):
        kelas = "flow-step active" if judul == active else "flow-step"
        bagian.append(tpl("flow_step", kelas=kelas, judul=esc(judul), ket=esc(ket)))
        if i < len(steps) - 1:
            bagian.append(tpl("flow_arrow"))
    tampil("flow", isi="".join(bagian))


def legend(items):
    """items: list (warna, label)."""
    isi = "".join(tpl("legend_item", warna=c, teks=esc(t)) for c, t in items)
    tampil("legend", isi=isi)


def bar(fraction, color=COLORS["accent"]):
    lebar = max(0, min(1, float(fraction))) * 100
    return tpl("bar", lebar=f"{lebar:.0f}", warna=color)


def source_note(text):
    tampil("source_note", teks=esc(text))


def style_fig(fig, height=320):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text"],
        margin=dict(l=0, r=0, t=10, b=0),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, x=0),
    )
    fig.update_xaxes(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"])
    fig.update_yaxes(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"])
    return fig


def go_to(page):
    st.session_state["page"] = page
    st.rerun()


def _rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _format_angka(x):
    return ("%.5f" % x).rstrip("0").rstrip(".")


def table(df, height=420, **_):
    """Tabel data. Memakai st.dataframe bila pyarrow tersedia, bila tidak memakai tabel HTML bergaya gelap."""
    if ADA_PYARROW:
        st.dataframe(df, width="stretch", hide_index=True, height=min(height, 38 + 35 * (len(df) + 1)))
        return
    html_tabel = df.to_html(index=False, escape=True, border=0, na_rep="-", classes="op-table",
                            float_format=_format_angka)
    md(f'<div class="op-table-wrap" style="max-height:{height}px;">{html_tabel}</div>')
