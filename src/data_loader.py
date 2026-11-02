"""Pemuatan dan pembersihan dataset pengajuan NFR."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import (
    DATA_PATH,
    DATE_COLUMNS,
    FALLBACK_TEXT_COLUMNS,
    NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
    TEXT_COLUMNS,
)


class DataLoadError(RuntimeError):
    """Kesalahan yang pesannya aman ditampilkan ke pengguna."""


@st.cache_data(show_spinner="Memuat data pengajuan NFR...")
def load_baseline_data(path: str | Path | None = None) -> pd.DataFrame:
    """Baca file Excel dan kembalikan DataFrame yang sudah dibersihkan.

    Hasil di-cache Streamlit, jadi file hanya dibaca sekali per proses.
    """
    file_path = Path(path) if path is not None else DATA_PATH

    if not file_path.exists():
        raise DataLoadError(
            f"Dataset tidak ditemukan di `{file_path}`. "
            "Pastikan file Excel berada di folder `Data/`."
        )

    try:
        raw = pd.read_excel(file_path, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001 - pesan asli diteruskan ke pengguna
        raise DataLoadError(f"Dataset gagal dibaca: {exc}") from exc

    return _clean(raw)


def _clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataLoadError(
            "Kolom wajib tidak ditemukan di dataset: "
            + ", ".join(f"`{col}`" for col in missing)
            + ". Periksa kembali format file Excel."
        )

    # Rapikan spasi liar dan samakan tipe kolom teks menjadi string agar
    # aman saat difilter maupun dikirim ke frontend (Arrow).
    for col in df.columns:
        if col in TEXT_COLUMNS or df[col].dtype == "object":
            df[col] = df[col].astype("string").str.strip()

    # No. SPBU harus string murni tanpa akhiran .0 agar konsisten saat difilter.
    df["No. SPBU"] = (
        df["No. SPBU"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    )

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in FALLBACK_TEXT_COLUMNS:
        df[col] = df[col].fillna("Tidak Diketahui")

    # Kolom turunan untuk grafik tren bulanan.
    df["Periode"] = df["Tgl Pengajuan"].dt.to_period("M").dt.to_timestamp()

    return df


def load_data_or_stop() -> pd.DataFrame:
    """Muat data atau tampilkan error yang bisa ditindaklanjuti lalu berhenti."""
    try:
        return load_baseline_data()
    except DataLoadError as exc:
        st.error(f"❌ {exc}")
        if st.button("🔄 Muat ulang data", key="reload_data"):
            st.cache_data.clear()
            st.rerun()
        st.stop()
