"""Master SPBU dan enrichment kolom kosong dari List Lembaga Penyalur."""

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from src.config import DATA_DIR

# Tidak bergantung pada konstanta baru di config agar tetap aman saat Streamlit
# Cloud memakai cache modul lama setelah redeploy.
SPBU_MASTER_PATH = DATA_DIR / "spbu_master.csv"
BVT_PATH = DATA_DIR / "bvt_spbu.csv"

EMPTY_TEXT = {
    "",
    "-",
    "#N/A",
    "#N/A N/A",
    "NULL",
    "NONE",
    "NAN",
    "TIDAK DIKETAHUI",
    "MISSING DATA",
    "NOT DEFINE",
}

KLAS_BVT_WARNA = {
    "Blue Ocean": "#3fb950",
    "Peluang Campuran": "#d29922",
    "Red Ocean": "#f85149",
}


def normalize_id(value) -> str | None:
    if pd.isna(value):
        return None
    teks = re.sub(r"\.0$", "", str(value).strip())
    teks = re.sub(r"\s+", "", teks)
    return teks or None


@st.cache_data(show_spinner=False)
def load_spbu_master() -> pd.DataFrame:
    df = pd.read_csv(SPBU_MASTER_PATH, dtype={"No. SPBU": str}, encoding="utf-8-sig")
    df["No. SPBU"] = df["No. SPBU"].map(normalize_id)
    df = df.dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU")
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["Reguler"] = df["Reguler"].astype(str).str.lower().isin(("true", "1", "yes"))
    for kolom in ("Nama SPBU", "Jenis Lembaga Penyalur", "Tipe SPBU", "Provinsi", "Kota/Kabupaten", "Kecamatan", "Desa/Kelurahan", "Alamat", "Status Operasi"):
        if kolom in df.columns:
            df[kolom] = df[kolom].fillna("Tidak diketahui")
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_bvt() -> pd.DataFrame:
    df = pd.read_csv(BVT_PATH, dtype={"No. SPBU": str}, encoding="utf-8-sig")
    df["No. SPBU"] = df["No. SPBU"].map(normalize_id)
    df = df.dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU")
    for kolom in ("Latitude", "Longitude", "Red Count", "Blue Count", "Blue Ocean Score (%)"):
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce")
    df["Reguler"] = df["Reguler"].astype(str).str.lower().isin(("true", "1", "yes"))
    for kolom in ("Nama SPBU", "Jenis Lembaga Penyalur", "Tipe SPBU", "Provinsi", "Kota/Kabupaten", "Kecamatan", "Desa/Kelurahan", "Alamat", "Road Type", "SES", "Red Ocean", "Blue Ocean", "Kelas BVT", "Sumber Tilok"):
        if kolom in df.columns:
            df[kolom] = df[kolom].fillna("Tidak diketahui")
    return df.reset_index(drop=True)


def _blank_mask(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series.isna()
    teks = series.astype("string").str.strip()
    return teks.isna() | teks.str.upper().isin(EMPTY_TEXT)


def _coordinate_valid(series: pd.Series, batas_bawah: float, batas_atas: float) -> pd.Series:
    nilai = pd.to_numeric(series, errors="coerce")
    return nilai.between(batas_bawah, batas_atas)


def enrich_with_master(df: pd.DataFrame, include_tipe: bool = True) -> pd.DataFrame:
    """Isi kolom kosong dari master SPBU. Nilai yang sudah ada tidak ditimpa.

    Kolom yang selalu ditambahkan: Nama SPBU, Jenis Lembaga Penyalur, Reguler,
    Latitude, Longitude. Tipe SPBU hanya jika include_tipe=True (mis. tidak untuk
    ketersediaan lahan yang menyembunyikan tipe SPBU).
    """
    if "No. SPBU" not in df.columns:
        return df

    master = load_spbu_master().set_index("No. SPBU").add_prefix("m_")
    hasil = df.merge(master, left_on="No. SPBU", right_index=True, how="left")

    pasangan_teks = {
        "Provinsi": "m_Provinsi",
        "Kota/Kab": "m_Kota/Kabupaten",
        "Kab./Kota": "m_Kota/Kabupaten",
        "Kecamatan": "m_Kecamatan",
        "Desa/Kelurahan": "m_Desa/Kelurahan",
        "Kelurahan": "m_Desa/Kelurahan",
        "Alamat": "m_Alamat",
    }
    for target, sumber in pasangan_teks.items():
        if target in hasil.columns and sumber in hasil.columns:
            mask = _blank_mask(hasil[target]) & hasil[sumber].notna()
            hasil.loc[mask, target] = hasil.loc[mask, sumber]

    for target, sumber in (
        ("Nama SPBU", "m_Nama SPBU"),
        ("Jenis Lembaga Penyalur", "m_Jenis Lembaga Penyalur"),
    ):
        if target not in hasil.columns:
            hasil[target] = hasil[sumber]
        else:
            mask = _blank_mask(hasil[target]) & hasil[sumber].notna()
            hasil.loc[mask, target] = hasil.loc[mask, sumber]

    if include_tipe:
        if "Tipe SPBU" not in hasil.columns:
            hasil["Tipe SPBU"] = hasil["m_Tipe SPBU"]
        else:
            mask = _blank_mask(hasil["Tipe SPBU"]) & hasil["m_Tipe SPBU"].notna()
            hasil.loc[mask, "Tipe SPBU"] = hasil.loc[mask, "m_Tipe SPBU"]

    if "Reguler" not in hasil.columns:
        hasil["Reguler"] = hasil["m_Reguler"]
    hasil["Reguler"] = hasil["Reguler"].astype("boolean").fillna(False).astype(bool)

    for target, sumber, bawah, atas in (
        ("Latitude", "m_Latitude", -12.0, 7.0),
        ("Longitude", "m_Longitude", 94.0, 142.0),
    ):
        if target not in hasil.columns:
            hasil[target] = hasil[sumber]
        else:
            valid = _coordinate_valid(hasil[target], bawah, atas)
            mask = (~valid) & hasil[sumber].notna()
            hasil.loc[mask, target] = hasil.loc[mask, sumber]

    hasil = hasil.drop(columns=[c for c in hasil.columns if c.startswith("m_")])
    return hasil


def top_kategori(df: pd.DataFrame, kolom: str, top_n: int = 10) -> pd.DataFrame:
    """Hitung kategori Red/Blue Ocean dari teks daftar yang dipisah koma."""
    hitung: dict[str, int] = {}
    for nilai in df[kolom].dropna():
        for item in str(nilai).split(","):
            item = item.strip()
            if item and item != "-":
                hitung[item] = hitung.get(item, 0) + 1
    hasil = pd.DataFrame(list(hitung.items()), columns=["Kategori", "Jumlah"])
    return hasil.nlargest(top_n, "Jumlah").reset_index(drop=True)
