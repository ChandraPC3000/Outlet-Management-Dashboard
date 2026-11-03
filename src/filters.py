"""Panel filter sidebar untuk halaman Director Summary dan Data Explorer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.formatting import format_angka

SPBU_COLUMN = "No. SPBU"
SPBU_PLACEHOLDER = "-- Pilih SPBU --"


def status_level_filter(df: pd.DataFrame, key: str):
    """Multiselect Status Level dari master/DDMS."""
    if "Status Level" not in df.columns:
        return []
    opsi = sorted(df["Status Level"].dropna().astype(str).unique().tolist())
    if not opsi:
        return []
    return st.multiselect("Status Level", opsi, key=f"{key}_status_level")


def tipe_brand_filter(df: pd.DataFrame, key: str, column: str = "Tipe Brand", label: str = "Tipe Brand"):
    """Multiselect Tipe Brand langsung dari kolom dataset."""
    if column not in df.columns:
        return []
    opsi = sorted(df[column].dropna().astype(str).unique().tolist())
    return st.multiselect(label, opsi, key=f"{key}_brand")


def spbu_brand_filter(key: str):
    """Multiselect Tipe Brand berdasarkan tenant yang ada di SPBU."""
    from src.spbu_universe import brand_types

    return st.multiselect(
        "Tipe Brand (tenant SPBU)",
        brand_types(),
        key=f"{key}_brand",
        help="Memfilter SPBU yang memiliki tenant dengan tipe brand tersebut.",
    )


def apply_status_level(df: pd.DataFrame, levels: list[str]) -> pd.DataFrame:
    if not levels or "Status Level" not in df.columns:
        return df
    return df[df["Status Level"].isin(levels)]


def apply_spbu_brands(df: pd.DataFrame, brands: list[str]) -> pd.DataFrame:
    if not brands:
        return df
    from src.spbu_universe import spbu_ids_for_brands

    ids = spbu_ids_for_brands(brands)
    return df[df["No. SPBU"].isin(ids)]


def _urut_unik(df: pd.DataFrame, column: str) -> list[str]:
    return sorted(df[column].dropna().astype(str).unique().tolist())


def spbu_selector(df: pd.DataFrame, key: str = "spbu", show_header: bool = True) -> str | None:
    """Selectbox No. SPBU dengan pencarian cepat. Mengembalikan None bila kosong."""
    with st.sidebar:
        if show_header:
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
        status_level = status_level_filter(df, key)
        tipe_spbu = st.multiselect(
            "Tipe SPBU", _urut_unik(df, "Tipe SPBU"), key=f"{key}_tipe_spbu"
        )
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
    if status_level:
        hasil = apply_status_level(hasil, status_level)
    if tipe_spbu:
        hasil = hasil[hasil["Tipe SPBU"].isin(tipe_spbu)]
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
