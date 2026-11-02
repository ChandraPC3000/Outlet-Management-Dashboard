"""Panel filter sidebar untuk halaman Director Summary dan Data Explorer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.formatting import format_angka

SPBU_COLUMN = "No. SPBU"
SPBU_PLACEHOLDER = "-- Pilih SPBU --"


def _urut_unik(df: pd.DataFrame, column: str) -> list[str]:
    return sorted(df[column].dropna().astype(str).unique().tolist())


def spbu_selector(df: pd.DataFrame, key: str = "spbu") -> str | None:
    """Selectbox No. SPBU dengan pencarian cepat. Mengembalikan None bila kosong."""
    with st.sidebar:
        st.header("🎛️ Filter Panel")
        keyword = st.text_input(
            "Cari No. SPBU",
            key=f"{key}_search",
            placeholder="contoh: 2430198",
            help="Ketik sebagian nomor untuk mempersempit pilihan.",
        )

        options = _urut_unik(df, SPBU_COLUMN)
        kata = keyword.strip()
        if kata:
            options = [spbu for spbu in options if kata in spbu]

        if not options:
            st.warning("No. SPBU tidak ditemukan. Coba kata kunci lain.")
            return None

        selected = st.selectbox(
            f"Pilih No. SPBU ({format_angka(len(options))} tersedia)",
            options=options,
            index=None,
            placeholder=SPBU_PLACEHOLDER,
            key=f"{key}_select",
        )

        if selected is None:
            st.info("Pilih nomor SPBU untuk menampilkan detail.")
        else:
            jumlah = int((df[SPBU_COLUMN] == selected).sum())
            st.success(f"Ditemukan {format_angka(jumlah)} data tenant.")

    return selected


def global_filters(df: pd.DataFrame, key: str = "explorer") -> pd.DataFrame:
    """Filter Region/Kategori/Status/Tipe Brand/pencarian/rentang tanggal."""
    with st.sidebar:
        st.header("🎛️ Filter Data")

        region = st.multiselect("Region", _urut_unik(df, "Region"), key=f"{key}_region")
        kategori = st.multiselect(
            "Kategori", _urut_unik(df, "Kategori"), key=f"{key}_kategori"
        )
        status = st.multiselect("Status", _urut_unik(df, "Status"), key=f"{key}_status")
        tipe_brand = st.multiselect(
            "Tipe Brand", _urut_unik(df, "Tipe Brand"), key=f"{key}_tipe"
        )
        keyword = st.text_input(
            "Cari tenant / brand",
            key=f"{key}_keyword",
            placeholder="contoh: Indomaret",
        )

        tanggal = df["Tgl Pengajuan"].dropna()
        batasi_tanggal = st.checkbox(
            "Batasi rentang tanggal",
            key=f"{key}_pakai_tanggal",
            disabled=tanggal.empty,
        )

        start = end = None
        if batasi_tanggal and not tanggal.empty:
            min_date = tanggal.min().date()
            max_date = tanggal.max().date()
            start = st.date_input(
                "Dari tanggal",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key=f"{key}_start",
            )
            end = st.date_input(
                "Sampai tanggal",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key=f"{key}_end",
            )
            if start > end:
                start, end = end, start
                st.caption("Rentang dibalik otomatis: tanggal awal > tanggal akhir.")

        if st.button("↺ Reset filter", use_container_width=True, key=f"{key}_reset"):
            for suffix in ("region", "kategori", "status", "tipe", "keyword", "pakai_tanggal"):
                st.session_state.pop(f"{key}_{suffix}", None)
            st.rerun()

    hasil = df

    if region:
        hasil = hasil[hasil["Region"].isin(region)]
    if kategori:
        hasil = hasil[hasil["Kategori"].isin(kategori)]
    if status:
        hasil = hasil[hasil["Status"].isin(status)]
    if tipe_brand:
        hasil = hasil[hasil["Tipe Brand"].isin(tipe_brand)]

    kata = keyword.strip()
    if kata:
        cocok = hasil["Nama Tenant"].str.contains(kata, case=False, na=False, regex=False)
        cocok |= hasil["Nama Brand"].str.contains(kata, case=False, na=False, regex=False)
        hasil = hasil[cocok]

    if start is not None and end is not None:
        tanggal_pengajuan = hasil["Tgl Pengajuan"].dt.date
        hasil = hasil[(tanggal_pengajuan >= start) & (tanggal_pengajuan <= end)]

    return hasil
