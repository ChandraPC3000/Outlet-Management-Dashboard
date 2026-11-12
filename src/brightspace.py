"""Data Brightspace: ringkasan lahan SPBU dari file request_data_lahan_luas."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import BRIGHTSPACE_PATH, BRIGHTSPACE_SUMMARY_PATH

STATUS_TERSEWA = "Tersewa (NFR aktif)"
STATUS_VACANT = "Vacant (belum ada NFR)"


@st.cache_data(show_spinner="Memuat data Brightspace...")
def load_brightspace() -> pd.DataFrame:
    df = pd.read_csv(BRIGHTSPACE_PATH)

    df["IdAgent_FK"] = (
        df["IdAgent_FK"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    )
    df["LandCode"] = df["LandCode"].astype("string").str.strip()
    df["LandArea"] = pd.to_numeric(df["LandArea"], errors="coerce").fillna(0.0)
    df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
    df["Lng"] = pd.to_numeric(df["Lng"], errors="coerce")

    for col in ("PosisiLahan_Description", "RentalPeriodName", "RentStatName"):
        df[col] = df[col].fillna("Tidak diketahui").astype("string").str.strip()

    df["BrandName"] = df["BrandName"].fillna("").astype("string").str.strip()
    df["BrandName"] = df["BrandName"].mask(df["BrandName"].eq(""), "Tidak diketahui")
    df["LandDescription"] = df["LandDescription"].fillna("").astype("string").str.strip()

    df["Status"] = df["RentStatName"].map(
        {"Tersewa": STATUS_TERSEWA, "Tersedia": STATUS_VACANT}
    ).fillna(df["RentStatName"])
    return df


@st.cache_data(show_spinner=False)
def load_brightspace_summary() -> dict:
    df = pd.read_csv(BRIGHTSPACE_SUMMARY_PATH)
    return {str(k): int(v) for k, v in df.iloc[0].to_dict().items()}


def ringkasan_brightspace(df: pd.DataFrame, summary: dict) -> dict:
    """Angka utama Brightspace.

    Total & vacant memakai sheet ringkasan `request_data_lahan_luas`
    (34.012 lahan, 5.924 tersedia); jumlah SPBU dan rincian status dihitung
    dari sheet `Bright_detailspbu_lahan`.
    """
    total_detail = int(len(df))
    total = int(summary.get("total_lahan", total_detail))
    vacant = int(
        summary.get("total_tersedia", int((df["RentStatName"] == "Tersedia").sum()))
    )
    tersewa = max(total - vacant, 0)

    top_brand = (
        df.loc[df["BrandName"].ne("Tidak diketahui"), "BrandName"]
        .value_counts()
        .head(1)
    )

    return {
        "spbu": int(df["IdAgent_FK"].nunique()),
        "total_lahan": total,
        "tersewa": tersewa,
        "vacant": vacant,
        "total_detail": total_detail,
        "tersewa_detail": int((df["RentStatName"] == "Tersewa").sum()),
        "vacant_detail": int((df["RentStatName"] == "Tersedia").sum()),
        "occupancy": (tersewa / total * 100) if total else 0.0,
        "vacancy_rate": (vacant / total * 100) if total else 0.0,
        "total_luas": float(df["LandArea"].sum()),
        "median_luas": float(df["LandArea"].median()),
        "top_brand": top_brand.index[0] if len(top_brand) else "-",
        "top_brand_count": int(top_brand.iloc[0]) if len(top_brand) else 0,
    }
