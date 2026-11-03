"""Total SPBU universe: Reguler + SPBU existing dari seluruh dataset operasional."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data_loader import (
    load_izin_prinsip,
    load_ketersediaan,
    load_master_lahan,
    load_sewa_lahan,
)
from src.master_data import load_spbu_master

KOLOM = [
    "No. SPBU",
    "Nama SPBU",
    "Jenis Lembaga Penyalur",
    "Tipe SPBU",
    "Reguler",
    "Provinsi",
    "Kota/Kabupaten",
    "Latitude",
    "Longitude",
    "Status Level",
    "Sumber",
]


@st.cache_data(show_spinner=False)
def load_spbu_universe() -> pd.DataFrame:
    """Union SPBU Reguler (master) + SPBU yang muncul di file operasional."""
    master = load_spbu_master()
    izin = load_izin_prinsip()
    lahan = load_master_lahan()
    sewa = load_sewa_lahan()
    ketersediaan = load_ketersediaan()

    reguler = master.loc[master["Reguler"], KOLOM[:-1]].copy()
    reguler["Sumber"] = "Reguler"
    reguler_ids = set(reguler["No. SPBU"])

    existing_ids: set[str] = set()
    for df in (izin, lahan, sewa, ketersediaan):
        existing_ids |= set(df["No. SPBU"].dropna().astype(str))
    extra_ids = existing_ids - reguler_ids

    extra_master = master.loc[master["No. SPBU"].isin(extra_ids), KOLOM[:-1]].copy()
    extra_master["Sumber"] = "Existing"
    sudah_ada = set(extra_master["No. SPBU"])

    sisa = extra_ids - sudah_ada
    if sisa:
        # SPBU existing yang tidak ada di master: ambil atribut seadanya.
        sumber = pd.concat(
            [
                izin[["No. SPBU", "Provinsi", "Kab./Kota"]].rename(
                    columns={"Kab./Kota": "Kota/Kabupaten"}
                ),
                ketersediaan[["No. SPBU", "Provinsi", "Kota/Kab"]].rename(
                    columns={"Kota/Kab": "Kota/Kabupaten"}
                ),
            ],
            ignore_index=True,
        )
        sumber = sumber.dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU")
        tambahan = pd.DataFrame(
            {
                "No. SPBU": sorted(sisa),
                "Nama SPBU": "Tidak diketahui",
                "Jenis Lembaga Penyalur": "Tidak diketahui",
                "Tipe SPBU": "Tidak diketahui",
                "Reguler": False,
                "Provinsi": "Tidak diketahui",
                "Kota/Kabupaten": "Tidak diketahui",
                "Latitude": pd.NA,
                "Longitude": pd.NA,
                "Sumber": "Existing",
                "Status Level": "Tidak diketahui",
            }
        )
        info = tambahan.merge(
            sumber[["No. SPBU", "Provinsi", "Kota/Kabupaten"]],
            on="No. SPBU",
            how="left",
            suffixes=("", "_sumber"),
        )
        tambahan["Provinsi"] = info["Provinsi_sumber"].fillna(tambahan["Provinsi"])
        tambahan["Kota/Kabupaten"] = info["Kota/Kabupaten_sumber"].fillna(tambahan["Kota/Kabupaten"])
        extra_master = pd.concat([extra_master, tambahan], ignore_index=True)

    universe = pd.concat([reguler, extra_master], ignore_index=True)
    universe = universe.drop_duplicates("No. SPBU").reset_index(drop=True)
    universe["Reguler"] = universe["Reguler"].astype(bool)
    return universe


def universe_ringkasan(universe: pd.DataFrame) -> dict:
    reguler = int(universe["Reguler"].sum())
    total = len(universe)
    return {
        "total": total,
        "reguler": reguler,
        "existing_ekstra": total - reguler,
    }


@st.cache_data(show_spinner=False)
def load_spbu_brand_types() -> pd.DataFrame:
    """Peta SPBU -> tipe brand tenant (Nasional/Lokal/UMKM/Internasional/Pameran)."""
    izin = load_izin_prinsip()[["No. SPBU", "Tipe Brand"]].rename(
        columns={"Tipe Brand": "Tipe Brand"}
    )
    sewa = load_sewa_lahan()[["No. SPBU", "Jenis Brand"]].rename(
        columns={"Jenis Brand": "Tipe Brand"}
    )
    data = pd.concat([izin, sewa], ignore_index=True)
    data["No. SPBU"] = data["No. SPBU"].astype("string").str.strip()
    data["Tipe Brand"] = data["Tipe Brand"].astype("string").str.strip()
    data = data.dropna(subset=["No. SPBU", "Tipe Brand"])
    data = data[data["Tipe Brand"] != ""].drop_duplicates()
    return data.reset_index(drop=True)


def brand_types() -> list[str]:
    data = load_spbu_brand_types()
    return sorted(data["Tipe Brand"].unique().tolist())


def spbu_ids_for_brands(brands: list[str]) -> set[str]:
    if not brands:
        return set()
    data = load_spbu_brand_types()
    return set(data.loc[data["Tipe Brand"].isin(brands), "No. SPBU"].unique())

