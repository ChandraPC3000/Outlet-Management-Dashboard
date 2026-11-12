"""Halaman Data Brightspace: ringkasan lahan SPBU dari Brightspace."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.brightspace import (
    STATUS_TERSEWA,
    STATUS_VACANT,
    load_brightspace,
    load_brightspace_summary,
    ringkasan_brightspace,
)
from src.charts import PALETTE_GELAP
from src.config import PALETTE
from src.excel_export import build_excel
from src.formatting import format_angka

df = load_brightspace()
summary = load_brightspace_summary()
info = ringkasan_brightspace(df, summary)


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

st.title("Data Brightspace")
st.caption(
    "Ringkasan lahan SPBU dari file **request_data_lahan_luas** "
    "(sheet `Bright_detailspbu_lahan` dan `request_data_lahan_luas`)."
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
    f"{format_angka(info['spbu'])} SPBU memiliki data lahan."
)

k5, k6, k7, k8 = st.columns(4)
k5.metric("Total Luas Lahan", f"{format_angka(info['total_luas'])} m²")
k6.metric("Median Luas", f"{format_angka(info['median_luas'], 1)} m²")
k7.metric("Brand Terbanyak", info["top_brand"])
k8.metric("Lahan Brand Tersebut", format_angka(info["top_brand_count"]))

with st.expander("Catatan data"):
    st.markdown(
        f"- Sumber: `request_data_lahan_luas.xlsx` — sheet `Bright_detailspbu_lahan` "
        f"({format_angka(info['total_detail'])} baris) dan sheet `request_data_lahan_luas` "
        f"({format_angka(info['total_lahan'])} lahan; {format_angka(info['vacant'])} tersedia).\n"
        f"- Rincian detail: **{format_angka(info['tersewa_detail'])} tersewa** + "
        f"**{format_angka(info['vacant_detail'])} tersedia** "
        f"(selisih {format_angka(info['total_lahan'] - info['total_detail'])} baris terhadap sheet ringkasan).\n"
        "- **Tersewa NFR aktif** = status `Tersewa`; **vacant (belum ada NFR)** = status `Tersedia`.\n"
        f"- `IdAgent_FK` dipakai sebagai identitas SPBU; **{format_angka(info['spbu'])} SPBU** "
        "memiliki data lahan di Brightspace."
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
    st.subheader("Top 10 Brand Berdasarkan Jumlah Lahan")
    top = (
        df.loc[df["BrandName"].ne("Tidak diketahui"), "BrandName"]
        .value_counts()
        .head(10)
        .sort_values()
    )
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

st.subheader("Posisi Lahan per Status")
posisi = (
    df.groupby(["PosisiLahan_Description", "Status"])
    .size()
    .reset_index(name="Jumlah")
)
fig = px.bar(
    posisi,
    x="PosisiLahan_Description",
    y="Jumlah",
    color="Status",
    barmode="stack",
    labels={"PosisiLahan_Description": "", "Jumlah": "Jumlah lahan"},
    color_discrete_map={STATUS_TERSEWA: PALET[1], STATUS_VACANT: PALET[3]},
)
fig.update_layout(
    template=TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=FONT, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    height=320,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    yaxis=dict(gridcolor=GRID),
)
st.plotly_chart(fig, use_container_width=True)

# --- Filter ------------------------------------------------------------------
with st.expander("Filter data Brightspace", expanded=True):
    f1, f2, f3 = st.columns(3)
    status = f1.multiselect(
        "Status", [STATUS_TERSEWA, STATUS_VACANT], key="bright_status"
    )
    posisi_sel = f2.multiselect(
        "Posisi Lahan",
        sorted(df["PosisiLahan_Description"].dropna().unique()),
        key="bright_posisi",
    )
    periode = f3.multiselect(
        "Periode Sewa",
        sorted(df["RentalPeriodName"].dropna().unique()),
        key="bright_periode",
    )

    f4, f5 = st.columns(2)
    cari = f4.text_input(
        "Cari brand / kode lahan / keterangan",
        placeholder="contoh: Indomaret atau 64793001",
        key="bright_cari",
    )
    max_luas = max(1.0, float(df["LandArea"].max()))
    f6, f7 = st.columns(2)
    luas_min = f6.number_input(
        "Luas minimum (m²)",
        min_value=0.0,
        max_value=max_luas,
        value=0.0,
        step=1.0,
        format="%.1f",
        key="bright_luas_min",
    )
    luas_max = f7.number_input(
        "Luas maksimum (m²)",
        min_value=0.0,
        max_value=max_luas,
        value=max_luas,
        step=1.0,
        format="%.1f",
        key="bright_luas_max",
    )
    if luas_min > luas_max:
        luas_min, luas_max = luas_max, luas_min
        st.caption("Rentang dibalik otomatis: nilai minimum lebih besar dari maksimum.")

    if f5.button("Reset filter", key="bright_reset"):
        for key in (
            "bright_status",
            "bright_posisi",
            "bright_periode",
            "bright_cari",
            "bright_luas_min",
            "bright_luas_max",
        ):
            st.session_state.pop(key, None)
        st.rerun()

f = df.copy()
if status:
    f = f[f["Status"].isin(status)]
if posisi_sel:
    f = f[f["PosisiLahan_Description"].isin(posisi_sel)]
if periode:
    f = f[f["RentalPeriodName"].isin(periode)]
if cari:
    mask = f[["BrandName", "LandCode", "LandDescription"]].apply(
        lambda s: s.str.contains(cari, case=False, na=False)
    ).any(axis=1)
    f = f[mask]
f = f[(f["LandArea"] >= luas_min) & (f["LandArea"] <= luas_max)]

# --- Tabel -------------------------------------------------------------------
st.subheader("Detail Lahan")
st.caption(
    f"Menampilkan **{format_angka(len(f))}** dari **{format_angka(len(df))}** lahan "
    f"· {format_angka(f['IdAgent_FK'].nunique())} SPBU pada hasil filter."
)

KOLOM = {
    "IdAgent_FK": "ID Agent",
    "LandCode": "Kode Lahan",
    "BrandName": "Brand/Tenant",
    "LandArea": "Luas (m²)",
    "PosisiLahan_Description": "Posisi Lahan",
    "RentalPeriodName": "Periode Sewa",
    "Status": "Status",
    "LandDescription": "Keterangan",
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
    data=build_excel(tabel, "Brightspace"),
    file_name="brightspace_lahan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="bright_download",
)
