"""Data Web Kemitraan: ringkasan lahan dari sheet Master Data (kajian NFR EBT)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import WEB_KEMITRAAN_PATH

STATUS_TERSEWA = "Tersewa (NFR aktif)"
STATUS_VACANT = "Vacant (belum ada NFR)"


@st.cache_data(show_spinner="Memuat data Web Kemitraan...")
def load_web_kemitraan() -> pd.DataFrame:
    df = pd.read_csv(WEB_KEMITRAAN_PATH)

    df["No SPBU"] = (
        df["No SPBU"].astype("string").str.replace(r"\.0$", "", regex=True).str.strip()
    )
    df["Kode Lahan"] = df["Kode Lahan"].astype("string").str.strip()
    df["Luas (M2)"] = pd.to_numeric(df["Luas (M2)"], errors="coerce").fillna(0.0)
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    for col in ("Tenant NFR", "Provinsi", "Kota/Kab", "Status Sewa"):
        df[col] = df[col].fillna("Tidak diketahui").astype("string").str.strip()
        df[col] = df[col].mask(df[col].eq(""), "Tidak diketahui")

    df["Status"] = df["Status Sewa"].map(
        {"Tersewa": STATUS_TERSEWA, "Tersedia": STATUS_VACANT}
    ).fillna(df["Status Sewa"])
    return df


def ringkasan_web_kemitraan(df: pd.DataFrame) -> dict:
    total = int(len(df))
    tersewa = int((df["Status Sewa"] == "Tersewa").sum())
    vacant = int((df["Status Sewa"] == "Tersedia").sum())

    tenant = df.loc[df["Tenant NFR"].ne("Tidak diketahui"), "Tenant NFR"]
    tenant_split = tenant.str.split("; ").explode().str.strip()
    tenant_split = tenant_split[tenant_split.ne("") & tenant_split.ne("-")]
    top = tenant_split.value_counts().head(1)

    return {
        "spbu": int(df["No SPBU"].nunique()),
        "total_lahan": total,
        "tersewa": tersewa,
        "vacant": vacant,
        "kode_unik": int(df["Kode Lahan"].nunique()),
        "occupancy": (tersewa / total * 100) if total else 0.0,
        "vacancy_rate": (vacant / total * 100) if total else 0.0,
        "total_luas": float(df["Luas (M2)"].sum()),
        "median_luas": float(df["Luas (M2)"].median()),
        "top_tenant": top.index[0] if len(top) else "-",
        "top_tenant_count": int(top.iloc[0]) if len(top) else 0,
    }
