"""Halaman Director Summary: analisis detail per nomor SPBU."""

from __future__ import annotations

import streamlit as st

from src import charts
from src.data_loader import load_data_or_stop
from src.filters import SPBU_COLUMN, spbu_selector
from src.formatting import format_angka, format_hari, format_rupiah, format_tanggal

KOLOM_TABEL = (
    "ID Pengajuan",
    "Nama Tenant",
    "Nama Brand",
    "Tipe Brand",
    "Kategori",
    "Sub Kategori",
    "Total Harga Sewa",
    "Nominal Fee",
    "Tgl Pengajuan",
    "Tgl Mulai Sewa Lahan",
    "Tgl Akhir Sewa Lahan",
    "Status",
    "Tahapan",
    "SLA",
)

df = load_data_or_stop()

st.title("📊 Director Summary")
st.caption("Pilih nomor SPBU di panel filter untuk melihat analisis detail outlet.")

selected = spbu_selector(df)

if selected is None:
    st.info(
        "👈 Pilih **Nomor SPBU** pada dropdown di sidebar untuk menampilkan "
        "analisis lokasi, KPI, dan detail tenant."
    )
    st.subheader("SPBU dengan tenant terbanyak")
    top_spbu = (
        df[SPBU_COLUMN]
        .value_counts()
        .head(10)
        .rename_axis("No. SPBU")
        .reset_index(name="Jumlah Tenant")
    )
    st.dataframe(top_spbu, hide_index=True, use_container_width=True)
    st.stop()

data = df[df[SPBU_COLUMN] == selected].copy()
info = data.iloc[0]

st.header(f"SPBU {selected}")
st.caption(
    f"Pengajuan terakhir: {format_tanggal(data['Tgl Pengajuan'].max())} · "
    f"{format_angka(len(data))} data tenant"
)

# --- Lokasi ---------------------------------------------------------------
st.subheader("📍 Lokasi Operasional")
lokasi = st.columns(3)
lokasi[0].metric("REGION", info["Region"])
lokasi[1].metric("PROVINSI", info["Provinsi"])
lokasi[2].metric("KABUPATEN / KOTA", info["Kab./Kota"])

# --- KPI ------------------------------------------------------------------
st.subheader("📈 Key Performance Indicators")
kpi = st.columns(4)
kpi[0].metric("Total Tenant", f"{format_angka(len(data))} unit")
kpi[1].metric("Total Sewa", format_rupiah(data["Total Harga Sewa"].sum()))
kpi[2].metric("Rerata SLA", format_hari(data["SLA"].mean()))
kpi[3].metric("Jumlah Brand", format_angka(data["Nama Brand"].nunique()))

st.divider()

# --- Visualisasi ----------------------------------------------------------
kiri, kanan = st.columns(2)
with kiri:
    st.subheader("💰 Sewa per Brand")
    st.plotly_chart(
        charts.sewa_per_brand(data, top_n=min(len(data), 20)),
        use_container_width=True,
    )
    if data["Nama Brand"].nunique() > 20:
        st.caption("Menampilkan 20 brand dengan nilai sewa terbesar.")
with kanan:
    st.subheader("📋 Status Pengajuan")
    st.plotly_chart(charts.status_donut(data), use_container_width=True)

st.divider()

# --- Tabel detail ---------------------------------------------------------
st.subheader("📑 Detail Data Transaksi")
tabel = data.loc[:, [kolom for kolom in KOLOM_TABEL if kolom in data.columns]]
tabel = tabel.sort_values("Total Harga Sewa", ascending=False)

st.dataframe(
    tabel,
    hide_index=True,
    use_container_width=True,
    height=420,
    column_config={
        "Total Harga Sewa": st.column_config.NumberColumn(
            "Total Harga Sewa (Rp)", format="%.0f"
        ),
        "Nominal Fee": st.column_config.NumberColumn("Nominal Fee (Rp)", format="%.0f"),
        "Tgl Pengajuan": st.column_config.DateColumn("Tgl Pengajuan", format="DD/MM/YYYY"),
        "Tgl Mulai Sewa Lahan": st.column_config.DateColumn(
            "Mulai Sewa", format="DD/MM/YYYY"
        ),
        "Tgl Akhir Sewa Lahan": st.column_config.DateColumn(
            "Akhir Sewa", format="DD/MM/YYYY"
        ),
    },
)

st.download_button(
    "⬇️ Unduh data SPBU ini (CSV)",
    data=data.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"nfr_spbu_{selected}.csv",
    mime="text/csv",
    use_container_width=True,
)
