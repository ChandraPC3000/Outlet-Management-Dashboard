"""Pemuatan, validasi, dan pembersihan keempat dataset NFR."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import (
    IZIN_DATE_COLUMNS,
    IZIN_FALLBACK_TEXT,
    IZIN_NUMERIC_COLUMNS,
    IZIN_PATH,
    IZIN_REQUIRED,
    IZIN_TEXT_COLUMNS,
    LAHAN_DATE_COLUMNS,
    LAHAN_NUMERIC_COLUMNS,
    LAHAN_PATH,
    LAHAN_REQUIRED,
    SEWA_DATE_COLUMNS,
    SEWA_NUMERIC_COLUMNS,
    SEWA_PATH,
    SEWA_REQUIRED,
)


class DataLoadError(RuntimeError):
    """Kesalahan yang pesannya aman ditampilkan ke pengguna."""


def _read_excel(path: Path, required: tuple[str, ...]) -> pd.DataFrame:
    if not path.exists():
        raise DataLoadError(
            f"Dataset tidak ditemukan di `{path}`. Pastikan file Excel ada di folder `Data/`."
        )

    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001 - pesan asli diteruskan ke pengguna
        raise DataLoadError(f"Dataset `{path.name}` gagal dibaca: {exc}") from exc

    df.columns = [str(col).strip() for col in df.columns]
    # Samakan nama kolom kunci antar dataset ("No SPBU" vs "No. SPBU").
    if "No SPBU" in df.columns and "No. SPBU" not in df.columns:
        df = df.rename(columns={"No SPBU": "No. SPBU"})
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise DataLoadError(
            f"Kolom wajib tidak ditemukan di `{path.name}`: "
            + ", ".join(f"`{col}`" for col in missing)
            + ". Periksa kembali format file Excel."
        )
    return df


def _clean_text(df: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for col in columns:
        if col in df.columns:
            teks = df[col].astype("string").str.strip()
            df[col] = teks.mask(teks.str.fullmatch(r"-", na=False), pd.NA)


def _normalize_spbu(df: pd.DataFrame, column: str = "No. SPBU") -> None:
    df[column] = (
        df[column].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    )


def _to_numeric(df: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


def _to_datetime(df: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")


@st.cache_data(show_spinner="Memuat data Izin Prinsip...")
def load_izin_prinsip(path: str | None = None) -> pd.DataFrame:
    df = _read_excel(Path(path) if path else IZIN_PATH, IZIN_REQUIRED)
    _clean_text(df, IZIN_TEXT_COLUMNS)
    _normalize_spbu(df)
    _to_numeric(df, IZIN_NUMERIC_COLUMNS)
    _to_datetime(df, IZIN_DATE_COLUMNS)

    for col in IZIN_FALLBACK_TEXT:
        df[col] = df[col].fillna("Tidak Diketahui")

    df["Periode"] = df["Tgl Pengajuan"].dt.to_period("M").dt.to_timestamp()
    return df


@st.cache_data(show_spinner="Memuat Master Lahan...")
def load_master_lahan(path: str | None = None) -> pd.DataFrame:
    df = _read_excel(Path(path) if path else LAHAN_PATH, LAHAN_REQUIRED)
    text_cols = tuple(
        col for col in LAHAN_REQUIRED if col not in LAHAN_NUMERIC_COLUMNS and col not in LAHAN_DATE_COLUMNS
    )
    _clean_text(df, text_cols)
    _normalize_spbu(df)
    _to_numeric(df, LAHAN_NUMERIC_COLUMNS)
    _to_datetime(df, LAHAN_DATE_COLUMNS)

    df["Status Sewa"] = df["Status Sewa"].fillna("Tidak Diketahui")
    df["Status Approval"] = df["Status Approval"].fillna("Tidak Diketahui")
    df["Tenant"] = df["Tenant"].fillna("-")
    return df


@st.cache_data(show_spinner="Memuat Pengajuan Sewa Lahan...")
def load_sewa_lahan(path: str | None = None) -> pd.DataFrame:
    df = _read_excel(Path(path) if path else SEWA_PATH, SEWA_REQUIRED)
    text_cols = tuple(
        col for col in SEWA_REQUIRED if col not in SEWA_NUMERIC_COLUMNS and col not in SEWA_DATE_COLUMNS
    )
    _clean_text(df, text_cols)
    _normalize_spbu(df)
    _to_numeric(df, SEWA_NUMERIC_COLUMNS)
    _to_datetime(df, SEWA_DATE_COLUMNS)

    for col in ("Status Sewa", "Status Izin Prinsip"):
        if col in df.columns:
            df[col] = df[col].fillna("Tidak Diketahui")
    return df


def _load_or_stop(loader, label: str) -> pd.DataFrame:
    try:
        return loader()
    except DataLoadError as exc:
        st.error(f"❌ {exc}")
        if st.button("🔄 Muat ulang data", key=f"reload_{label}"):
            st.cache_data.clear()
            st.rerun()
        st.stop()


def load_data_or_stop() -> pd.DataFrame:
    """Muat dataset Izin Prinsip atau berhenti dengan pesan yang jelas."""
    return _load_or_stop(load_izin_prinsip, "izin")


def load_lahan_or_stop() -> pd.DataFrame:
    return _load_or_stop(load_master_lahan, "lahan")


def load_sewa_or_stop() -> pd.DataFrame:
    return _load_or_stop(load_sewa_lahan, "sewa")


def load_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Muat ketiga dataset sekaligus (untuk halaman yang butuh semuanya)."""
    return load_data_or_stop(), load_lahan_or_stop(), load_sewa_or_stop()
