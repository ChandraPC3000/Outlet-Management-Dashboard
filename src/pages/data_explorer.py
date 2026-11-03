"""Halaman Data Explorer: telusuri seluruh dataset dengan filter dinamis."""

from __future__ import annotations

import streamlit as st

from src import charts
from src.data_loader import load_data_or_stop
from src.filters import global_filters
from src.formatting import format_angka, format_rupiah
from src.map_spbu import render_spbu_map
from src.spbu_universe import load_spbu_universe, universe_ringkasan

df = load_data_or_stop()
universe = universe_ringkasan(load_spbu_universe())

st.title("🔎 Data Explorer")
st.caption(
    "Telusuri seluruh pengajuan. Gunakan panel filter di sidebar; "
    "hasil filter langsung terlihat di KPI, grafik, dan tabel."
)

filtered = global_filters(df)

if filtered.empty:
    st.warning(
        "Tidak ada data yang cocok dengan kombinasi filter. "
        "Kurangi filter atau tekan **↺ Reset filter** di sidebar."
    )
    st.stop()

st.caption(
    f"Menampilkan **{format_angka(len(filtered))}** dari "
    f"**{format_angka(len(df))}** baris data."
)

kpi = st.columns(4)
kpi[0].metric("Baris Data", format_angka(len(filtered)))
kpi[1].metric("SPBU di Data", format_angka(filtered["No. SPBU"].nunique()))
kpi[2].metric("Brand Unik", format_angka(filtered["Nama Brand"].nunique()))
kpi[3].metric("Total Nilai Sewa", format_rupiah(filtered["Total Harga Sewa"].sum()))

st.caption(
    f"Total SPBU universe: **{format_angka(universe['total'])}** "
    f"({format_angka(universe['reguler'])} Reguler + "
    f"{format_angka(universe['existing_ekstra'])} existing). "
    "KPI **SPBU di Data** menghitung SPBU yang punya baris pada hasil filter."
)

st.subheader("🗺️ Peta SPBU Hasil Filter")
st.caption("Warna titik = Tipe SPBU.")
render_spbu_map(filtered, color_col="Tipe SPBU", region_col="Region", height=500)

tab_visual, tab_tabel, tab_ringkasan = st.tabs(
    ["📈 Visualisasi", "📑 Tabel", "🧾 Ringkasan"]
)

with tab_visual:
    st.subheader("Tren Pengajuan per Bulan")
    st.plotly_chart(charts.tren_pengajuan(filtered), use_container_width=True)

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("🏷️ Kategori Teratas")
        st.plotly_chart(charts.kategori_bar(filtered), use_container_width=True)
    with kanan:
        st.subheader("📋 Komposisi Status")
        st.plotly_chart(charts.status_donut(filtered), use_container_width=True)

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("🗺️ Sebaran Region")
        st.plotly_chart(charts.region_bar(filtered), use_container_width=True)
    with kanan:
        st.subheader("💰 Brand dengan Sewa Terbesar")
        st.plotly_chart(charts.sewa_per_brand(filtered, top_n=10), use_container_width=True)

with tab_tabel:
    st.dataframe(
        filtered.drop(columns=["Periode"], errors="ignore"),
        hide_index=True,
        use_container_width=True,
        height=560,
        column_config={
            "Total Harga Sewa": st.column_config.NumberColumn(
                "Total Harga Sewa (Rp)", format="%.0f"
            ),
            "Nominal Fee": st.column_config.NumberColumn("Nominal Fee (Rp)", format="%.0f"),
            "Tgl Pengajuan": st.column_config.DateColumn(
                "Tgl Pengajuan", format="DD/MM/YYYY"
            ),
            "Tgl Mulai Sewa Lahan": st.column_config.DateColumn(
                "Mulai Sewa", format="DD/MM/YYYY"
            ),
            "Tgl Akhir Sewa Lahan": st.column_config.DateColumn(
                "Akhir Sewa", format="DD/MM/YYYY"
            ),
            "Tgl Berakhir Izin Prinsip": st.column_config.DateColumn(
                "Berakhir Izin", format="DD/MM/YYYY"
            ),
            "Batas": st.column_config.DateColumn("Batas", format="DD/MM/YYYY"),
        },
    )

    st.download_button(
        "⬇️ Unduh hasil filter (CSV)",
        data=filtered.drop(columns=["Periode"], errors="ignore")
        .to_csv(index=False)
        .encode("utf-8-sig"),
        file_name="nfr_data_explorer.csv",
        mime="text/csv",
        use_container_width=True,
    )

with tab_ringkasan:
    ringkasan_region = (
        filtered.groupby("Region")
        .agg(
            **{
                "Jumlah Pengajuan": ("ID Pengajuan", "count"),
                "Jumlah SPBU": ("No. SPBU", "nunique"),
                "Total Sewa (Rp)": ("Total Harga Sewa", "sum"),
                "Rerata SLA": ("SLA", "mean"),
            }
        )
        .reset_index()
        .sort_values("Total Sewa (Rp)", ascending=False)
    )
    st.subheader("Ringkasan per Region")
    st.dataframe(
        ringkasan_region,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Total Sewa (Rp)": st.column_config.NumberColumn(
                "Total Sewa (Rp)", format="%.0f"
            ),
            "Rerata SLA": st.column_config.NumberColumn("Rerata SLA", format="%.2f"),
        },
    )

    ringkasan_kategori = (
        filtered.groupby("Kategori")
        .agg(
            **{
                "Jumlah Pengajuan": ("ID Pengajuan", "count"),
                "Jumlah Brand": ("Nama Brand", "nunique"),
                "Total Sewa (Rp)": ("Total Harga Sewa", "sum"),
            }
        )
        .reset_index()
        .sort_values("Jumlah Pengajuan", ascending=False)
    )
    st.subheader("Ringkasan per Kategori")
    st.dataframe(
        ringkasan_kategori,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Total Sewa (Rp)": st.column_config.NumberColumn(
                "Total Sewa (Rp)", format="%.0f"
            ),
        },
    )
