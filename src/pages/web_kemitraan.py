"""Halaman Data Web Kemitraan: ringkasan lahan dari sheet Master Data kajian NFR EBT."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import PALETTE_GELAP
from src.config import PALETTE
from src.excel_export import build_excel
from src.formatting import format_angka
from src.web_kemitraan import (
    STATUS_TERSEWA,
    STATUS_VACANT,
    load_web_kemitraan,
    ringkasan_web_kemitraan,
)

df = load_web_kemitraan()
info = ringkasan_web_kemitraan(df)


def _gelap() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


GELAP = _gelap()
PALET = PALETTE_GELAP if GELAP else PALETTE
TEMPLATE = "plotly_dark" if GELAP else "plotly_white"
FONT = "#e5e7eb" if GELAP else "#111827"
GRID = "#374151" if GELAP else "#e5e7eb"

st.title("Data Web Kemitraan")
st.caption(
    "Ringkasan lahan dari file **List Kebutuhan Data Kajian NFR EBT** — "
    "sheet `Master Data` (data Web Kemitraan)."
)

# --- KPI utama ---------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Jumlah SPBU", format_angka(info["spbu"]))
k2.metric("Lahan Terdaftar", format_angka(info["total_lahan"]))
k3.metric("Tersewa NFR Aktif", format_angka(info["tersewa"]))
k4.metric("Lahan Vacant", format_angka(info["vacant"]))

st.caption(
    f"Tersewa **{info['occupancy']:.1f}%** dari total lahan · "
    f"vacant **{info['vacancy_rate']:.1f}%** · "
    f"{format_angka(info['kode_unik'])} kode lahan unik."
)

k5, k6, k7, k8 = st.columns(4)
k5.metric("Total Luas Lahan", f"{format_angka(info['total_luas'])} m²")
k6.metric("Median Luas", f"{format_angka(info['median_luas'], 1)} m²")
k7.metric("Tenant Terbanyak", info["top_tenant"])
k8.metric("Lahan Tenant Tersebut", format_angka(info["top_tenant_count"]))

with st.expander("Catatan data"):
    st.markdown(
        "- Sumber: `List Kebutuhan Data Kajian NFR EBT.xlsx` — sheet `Master Data`.\n"
        "- **Tersewa NFR aktif** = `Status Sewa = Tersewa`; "
        "**vacant (belum ada NFR)** = `Status Sewa = Tersedia`.\n"
        "- Satu baris = satu lahan/tenant; beberapa kode lahan bisa muncul lebih dari sekali "
        f"({format_angka(info['total_lahan'] - info['kode_unik'])} baris duplikat kode lahan).\n"
        f"- Jumlah SPBU dihitung dari `No SPBU` unik: **{format_angka(info['spbu'])}**."
    )

# --- Grafik ------------------------------------------------------------------
kol1, kol2 = st.columns(2)

with kol1:
    st.subheader("Status Lahan")
    fig = px.pie(
        names=[STATUS_TERSEWA, STATUS_VACANT],
        values=[info["tersewa"], info["vacant"]],
        hole=0.55,
        color_discrete_sequence=[PALET[1], PALET[3]],
    )
    fig.update_traces(textinfo="percent+label", textposition="outside")
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=FONT, size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True)

with kol2:
    st.subheader("Top 10 Tenant/Brand")
    tenant = df.loc[df["Tenant NFR"].ne("Tidak diketahui"), "Tenant NFR"]
    tenant = tenant.str.split("; ").explode().str.strip()
    tenant = tenant[tenant.ne("") & tenant.ne("-")]
    top = tenant.value_counts().head(10).sort_values()
    fig = px.bar(
        x=top.values,
        y=top.index,
        orientation="h",
        labels={"x": "Jumlah lahan", "y": ""},
        color_discrete_sequence=[PALET[1]],
    )
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=FONT, size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        xaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Top 10 Provinsi Berdasarkan Jumlah Lahan")
prov = df["Provinsi"].value_counts().head(10).sort_values()
fig = px.bar(
    x=prov.values,
    y=prov.index,
    orientation="h",
    labels={"x": "Jumlah lahan", "y": ""},
    color_discrete_sequence=[PALET[2]],
)
fig.update_layout(
    template=TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=FONT, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    height=340,
    xaxis=dict(gridcolor=GRID),
)
st.plotly_chart(fig, use_container_width=True)

# --- Filter ------------------------------------------------------------------
with st.expander("Filter data Web Kemitraan", expanded=True):
    f1, f2, f3 = st.columns(3)
    provinsi = f1.multiselect(
        "Provinsi",
        sorted(df["Provinsi"].dropna().unique()),
        key="web_prov",
    )
    opsi_kota = (
        sorted(df.loc[df["Provinsi"].isin(provinsi), "Kota/Kab"].dropna().unique())
        if provinsi
        else sorted(df["Kota/Kab"].dropna().unique())
    )
    kota = f2.multiselect("Kota/Kab", opsi_kota, key="web_kota")
    status = f3.multiselect(
        "Status", [STATUS_TERSEWA, STATUS_VACANT], key="web_status"
    )

    f4, f5 = st.columns(2)
    cari = f4.text_input(
        "Cari tenant / kode lahan / No SPBU",
        placeholder="contoh: Indomaret atau 3414407",
        key="web_cari",
    )
    max_luas = max(1.0, float(df["Luas (M2)"].max()))
    f6, f7 = st.columns(2)
    luas_min = f6.number_input(
        "Luas minimum (m²)",
        min_value=0.0,
        max_value=max_luas,
        value=0.0,
        step=1.0,
        format="%.1f",
        key="web_luas_min",
    )
    luas_max = f7.number_input(
        "Luas maksimum (m²)",
        min_value=0.0,
        max_value=max_luas,
        value=max_luas,
        step=1.0,
        format="%.1f",
        key="web_luas_max",
    )
    if luas_min > luas_max:
        luas_min, luas_max = luas_max, luas_min
        st.caption("Rentang dibalik otomatis: nilai minimum lebih besar dari maksimum.")

    if f5.button("Reset filter", key="web_reset"):
        for key in (
            "web_prov",
            "web_kota",
            "web_status",
            "web_cari",
            "web_luas_min",
            "web_luas_max",
        ):
            st.session_state.pop(key, None)
        st.rerun()

f = df.copy()
if provinsi:
    f = f[f["Provinsi"].isin(provinsi)]
if kota:
    f = f[f["Kota/Kab"].isin(kota)]
if status:
    f = f[f["Status"].isin(status)]
if cari:
    mask = f[["Tenant NFR", "Kode Lahan", "No SPBU"]].apply(
        lambda s: s.str.contains(cari, case=False, na=False)
    ).any(axis=1)
    f = f[mask]
f = f[(f["Luas (M2)"] >= luas_min) & (f["Luas (M2)"] <= luas_max)]

# --- Tabel -------------------------------------------------------------------
st.subheader("Detail Lahan")
st.caption(
    f"Menampilkan **{format_angka(len(f))}** dari **{format_angka(len(df))}** lahan "
    f"· {format_angka(f['No SPBU'].nunique())} SPBU pada hasil filter."
)

KOLOM = {
    "No SPBU": "No SPBU",
    "Kode Lahan": "Kode Lahan",
    "Tenant NFR": "Tenant NFR",
    "Provinsi": "Provinsi",
    "Kota/Kab": "Kota/Kab",
    "Luas (M2)": "Luas (m²)",
    "Status": "Status",
}
tabel = f[list(KOLOM)].rename(columns=KOLOM)

st.dataframe(
    tabel,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Luas (m²)": st.column_config.NumberColumn(format="%.1f"),
    },
)

st.download_button(
    "Unduh Excel hasil filter",
    data=build_excel(tabel, "Web Kemitraan"),
    file_name="web_kemitraan_lahan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="web_download",
)
