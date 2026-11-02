"""Halaman Home: ringkasan cepat seluruh dataset."""

from __future__ import annotations

import streamlit as st

from src import charts
from src.data_loader import load_data_or_stop
from src.formatting import format_angka, format_rupiah

df = load_data_or_stop()

st.title("🚀 NFR Management System")
st.caption(
    "Dashboard pengajuan **Izin Prinsip** tenant Non-Fuel Retail (NFR) di SPBU Pertamina."
)

kolom = st.columns(4)
kolom[0].metric("Total Pengajuan", f"{format_angka(len(df))} baris")
kolom[1].metric("Jumlah SPBU", format_angka(df["No. SPBU"].nunique()))
kolom[2].metric("Jumlah Tenant", format_angka(df["Nama Tenant"].nunique()))
kolom[3].metric("Total Nilai Sewa", format_rupiah(df["Total Harga Sewa"].sum()))

st.divider()

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🗺️ Sebaran per Region")
    st.plotly_chart(charts.region_bar(df), use_container_width=True)
with kanan:
    st.subheader("📋 Komposisi Status")
    st.plotly_chart(charts.status_donut(df), use_container_width=True)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🏷️ Top 10 Kategori")
    st.plotly_chart(charts.kategori_bar(df, top_n=10), use_container_width=True)
with kanan:
    st.subheader("📈 Tren Pengajuan per Bulan")
    st.plotly_chart(charts.tren_pengajuan(df), use_container_width=True)

st.divider()

with st.expander("ℹ️ Cara pakai & informasi dataset", expanded=False):
    st.markdown(
        """
        **Cara pakai**

        1. Buka **📊 Director Summary** untuk melihat analisis satu SPBU.
           Pilih nomor SPBU pada panel filter di sidebar.
        2. Buka **🔎 Data Explorer** untuk menelusuri seluruh data dengan filter
           Region, Kategori, Status, Tipe Brand, kata kunci, dan rentang tanggal.
        3. Setiap halaman menyediakan tombol unduh CSV sesuai hasil filter.

        **Sumber data**

        File `Data/Pengajuan NFR Izin Prinsip 10-April-2026.xlsx` yang dibaca
        otomatis saat aplikasi pertama kali dibuka. Data di-cache, jadi file
        hanya dibaca sekali per proses.

        **Catatan kualitas data**

        - Sebagian baris memiliki `ID Pengajuan` duplikat (data mentah tidak
          dihapus otomatis agar angka tetap sesuai sumber).
        - `Total Harga Sewa` kosong di sebagian kecil baris dan dihitung sebagai 0.
        - `SLA` mayoritas bernilai 0.
        """
    )
