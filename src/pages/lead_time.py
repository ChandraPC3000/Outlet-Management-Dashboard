"""Halaman Lead Time: funnel tahapan, aging pending, dan kepatuhan SLA."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_data_or_stop
from src.formatting import format_angka, format_hari
from src.map_spbu import render_spbu_map

izin = load_data_or_stop()
snapshot = an.snapshot_date(izin)
ldf = an.prepare_leadtime(izin, snapshot)

st.title("Lead Time & Antrean Tahapan")
st.caption(
    f"Snapshot {snapshot:%d %B %Y}. Umur pengajuan dihitung dari tanggal pengajuan "
    "sampai tanggal snapshot; status menunjukkan tahapan berjalan."
)

st.info(
    "Dataset pengajuan tidak memuat timestamp transisi antar tahap. Karena itu angka di "
    "halaman ini adalah **lead time berjalan (aging)** per tahapan — bukan selisih tanggal "
    "masuk dan keluar tahap. Detail metode ada di file "
    "`Data/Data Lead Time NFR.xlsx` sheet **Metodologi**.",
)

# --- Filter -----------------------------------------------------------------
f1, f2, f3 = st.columns(3)
region = f1.multiselect("Region", sorted(ldf["Region"].dropna().unique()), key="lt_region")
tahap = f2.multiselect(
    "Tahapan", [t for t in an.TAHAPAN_ORDER if t in set(ldf["Tahapan"])], key="lt_tahap"
)
status = f3.multiselect("Status", sorted(ldf["Status"].dropna().unique()), key="lt_status")

f4, f5, f6 = st.columns(3)
brand = f4.multiselect(
    "Tipe Brand", sorted(ldf["Tipe Brand"].dropna().unique()), key="lt_brand"
)
tipe_spbu = f5.multiselect(
    "Tipe SPBU", sorted(ldf["Tipe SPBU"].dropna().unique()), key="lt_tipe_spbu"
)
status_level = f6.multiselect(
    "Status Level", sorted(ldf["Status Level"].dropna().unique()), key="lt_status_level"
)

tampil = ldf
if region:
    tampil = tampil[tampil["Region"].isin(region)]
if tahap:
    tampil = tampil[tampil["Tahapan"].isin(tahap)]
if status:
    tampil = tampil[tampil["Status"].isin(status)]
if brand:
    tampil = tampil[tampil["Tipe Brand"].isin(brand)]
if tipe_spbu:
    tampil = tampil[tampil["Tipe SPBU"].isin(tipe_spbu)]
if status_level:
    tampil = tampil[tampil["Status Level"].isin(status_level)]

if tampil.empty:
    st.warning("Tidak ada data yang cocok dengan filter.")
    st.stop()

pending = tampil[tampil["Kelompok"] == "Pending"]
funnel = an.leadtime_funnel(tampil)
stage = an.leadtime_stage_summary(tampil)
aging = an.leadtime_aging(tampil)
region_pending = an.pending_by_region(tampil)

kpi = st.columns(4)
kpi[0].metric("Pengajuan Pending", format_angka(len(pending)))
kpi[1].metric(
    "Median Umur Pending",
    format_hari(pending["Umur Pengajuan (hari)"].median()) if not pending.empty else "-",
)
kpi[2].metric(
    "Lewat Batas SLA",
    format_angka(int(pending["Lewat Batas"].sum())) if not pending.empty else "0",
)
kpi[3].metric(
    "Pending Terlama",
    format_hari(pending["Umur Pengajuan (hari)"].max()) if not pending.empty else "-",
)

st.subheader("Peta Pengajuan pada Filter Ini")
st.caption("Warna titik = Tipe SPBU.")
render_spbu_map(tampil, color_col="Tipe SPBU", region_col="Region", height=480)

st.divider()

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("Funnel Tahapan")
    st.plotly_chart(charts.funnel_tahapan(funnel), use_container_width=True)
with kanan:
    st.subheader("Aging per Tahapan")
    if stage.empty:
        st.info("Tidak ada pengajuan pending pada filter ini.")
    else:
        st.plotly_chart(charts.aging_tahapan(stage), use_container_width=True)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("Aging per Status Pending")
    if aging.empty:
        st.info("Tidak ada pengajuan pending pada filter ini.")
    else:
        st.plotly_chart(charts.aging_status(aging), use_container_width=True)
with kanan:
    st.subheader("Pending per Region")
    if region_pending.empty:
        st.info("Tidak ada pengajuan pending pada filter ini.")
    else:
        st.plotly_chart(charts.pending_region(region_pending), use_container_width=True)

st.divider()

st.subheader("Resume Lead Time per Tahapan")
if stage.empty:
    st.info("Tidak ada pengajuan pending pada filter ini.")
else:
    st.dataframe(
        stage,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Rerata Umur (hari)": st.column_config.NumberColumn(format="%.1f"),
            "Median Umur (hari)": st.column_config.NumberColumn(format="%.1f"),
            "P90 Umur (hari)": st.column_config.NumberColumn(format="%.1f"),
            "Umur Terlama (hari)": st.column_config.NumberColumn(format="%.1f"),
            "% Lewat Batas": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

st.subheader("Resume per Status Pending")
if aging.empty:
    st.info("Tidak ada pengajuan pending pada filter ini.")
else:
    st.dataframe(
        aging,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Rerata Umur (hari)": st.column_config.NumberColumn(format="%.1f"),
            "Median Umur (hari)": st.column_config.NumberColumn(format="%.1f"),
            "P90 Umur (hari)": st.column_config.NumberColumn(format="%.1f"),
            "Umur Terlama (hari)": st.column_config.NumberColumn(format="%.1f"),
            "% Lewat Batas": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

st.subheader("20 Pengajuan Pending Terlama")
terlama = an.oldest_pending(tampil, 20)
if terlama.empty:
    st.success("Tidak ada pengajuan pending")
else:
    st.dataframe(
        terlama,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Umur Pengajuan (hari)": st.column_config.NumberColumn(format="%.1f"),
            "Overdue (hari)": st.column_config.NumberColumn(format="%.0f"),
            "Tgl Pengajuan": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Batas": st.column_config.DateColumn(format="DD/MM/YYYY"),
        },
    )
    st.download_button(
        "Unduh daftar pending (CSV)",
        data=an.oldest_pending(tampil, len(pending))
        .to_csv(index=False)
        .encode("utf-8-sig"),
        file_name="nfr_lead_time_pending.csv",
        mime="text/csv",
        use_container_width=True,
        key="unduh_pending",
    )

with st.expander("Metodologi & batasan", expanded=False):
    st.markdown(
        """
        - **Pending** = status Menunggu Verifikasi SBM/SAM/MS3, Menunggu Verifikasi,
          Menunggu Pembayaran, Input Nominal, Revisi Pembayaran, Verifikasi Pembayaran.
        - **Umur pengajuan** = tanggal snapshot − `Tgl Pengajuan`. Untuk pengajuan yang
          masih pending, ini menunjukkan berapa lama pengajuan tertahan.
        - **Lewat Batas** hanya dapat dihitung untuk baris yang memiliki `Batas`
          (635 dari 46.523 baris).
        - **Tidak ada** timestamp transisi tahap di dataset sumber, sehingga lead time
          antar tahap (SBM → SAM → MS3 → fee → invoice) tidak bisa dihitung sebagai
          selisih tanggal. Bila file mentah workflow November tersedia, analisis tahap
          penuh bisa dibuat seperti versi 22 Oktober 2026.
        """
    )
