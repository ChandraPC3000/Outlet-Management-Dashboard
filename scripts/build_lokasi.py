"""Bangun master SPBU dan dataset BVT untuk LOKASI Intelligence.

Sumber (lokal, tidak di-commit):
  - List Lembaga Penyalur 13 Oktober 2026.xlsx (sheet Authors)
  - SPBU_All_34_Provinces_20261016.xlsx

Output:
  - Data/spbu_master.csv   (tanpa nomor PIC/email/telepon)
  - Data/bvt_spbu.csv      (Red/Blue Ocean + skor + koordinat)

Jalankan: python scripts/build_lokasi.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAW_MASTER = Path(r"F:/List Lembaga Penyalur 13 Oktober 2026.xlsx")
RAW_BVT = Path(r"F:/SPBU_All_34_Provinces_20261016.xlsx")
OUT_MASTER = ROOT / "Data" / "spbu_master.csv"
OUT_BVT = ROOT / "Data" / "bvt_spbu.csv"

LRON = (94.0, 142.0)
LAT = (-12.0, 7.0)


def norm_id(value) -> str | None:
    if pd.isna(value):
        return None
    teks = re.sub(r"\.0$", "", str(value).strip())
    teks = re.sub(r"\s+", "", teks)
    return teks or None


def clean_lon(value) -> float:
    if pd.isna(value):
        return np.nan
    x = float(value)
    if abs(x) >= 1e8:
        return np.nan
    if 1_000 < abs(x) < 2_000:
        x = x / 10
    if -180 <= x < 90:
        x = abs(x)
    return x if LRON[0] <= x <= LRON[1] else np.nan


def clean_lat(value) -> float:
    if pd.isna(value):
        return np.nan
    x = float(value)
    if abs(x) >= 1e8:
        return np.nan
    return x if LAT[0] <= x <= LAT[1] else np.nan


def tipe_spbu(ownership) -> str:
    teks = "" if pd.isna(ownership) else str(ownership).strip().upper()
    if teks.startswith("COCO"):
        return "COCO"
    if teks.startswith("CODO"):
        return "CODO"
    if teks.startswith("DODO") or "DEALER OWNED" in teks:
        return "DODO"
    return "Lainnya"


def item_list(value) -> list[str]:
    if pd.isna(value):
        return []
    teks = str(value).strip()
    if teks in ("-", "#N/A", "Tidak Ada", ""):
        return []
    return [x.strip() for x in teks.split(",") if x.strip() and x.strip() != "-"]


def maps_link(lat, lon) -> str:
    if pd.isna(lat) or pd.isna(lon):
        return ""
    return f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"


def main() -> tuple[Path, Path]:
    if not RAW_MASTER.exists() or not RAW_BVT.exists():
        raise SystemExit("File sumber master/BVT tidak ditemukan di F:/")

    master = pd.read_excel(RAW_MASTER, sheet_name="Authors", engine="openpyxl")
    master.columns = [str(c).strip() for c in master.columns]
    master["No. SPBU"] = master["No. SPBU"].map(norm_id)
    master = master.dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU").copy()

    master["Nama SPBU"] = master["Nama SPBU"].fillna("Tidak diketahui")
    master["Jenis Lembaga Penyalur"] = master["Type Lembaga Penyalur"].fillna("Tidak diketahui")
    master["Reguler"] = master["Jenis Lembaga Penyalur"].eq("SPBU Reguler")
    master["Tipe SPBU"] = master["Ownership"].map(tipe_spbu)
    master["Ownership"] = master["Ownership"].fillna("Tidak diketahui")
    master["Status Operasi"] = master["Status Operasi"].fillna("Tidak diketahui")

    master["Latitude"] = master["Koordinat Y"].map(clean_lat)
    master["Longitude"] = master["Koordinat X"].map(clean_lon)
    master["Sumber Tilok"] = np.where(
        master["Latitude"].notna() & master["Longitude"].notna(),
        "Master Lembaga Penyalur",
        "Tidak tersedia",
    )

    for kolom in ("Provinsi", "Kota/Kabupaten", "Kecamatan", "Kelurahan", "Alamat"):
        if kolom not in master.columns:
            master[kolom] = "Tidak diketahui"
        master[kolom] = master[kolom].fillna("Tidak diketahui")

    # ------------------------------------------------------------------ BVT
    bvt = pd.read_excel(RAW_BVT, engine="openpyxl")
    bvt.columns = [str(c).strip() for c in bvt.columns]
    bvt["No. SPBU"] = bvt["SPBU Name"].map(norm_id)
    bvt = bvt.dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU").copy()

    # Kolom Longitude/Latitude pada file sumber tertukar.
    lat_sumber = pd.to_numeric(bvt["Longitude"], errors="coerce")  # sebenarnya latitude
    lon_sumber = pd.to_numeric(bvt["Latitude"], errors="coerce")  # sebenarnya longitude
    bvt["Latitude"] = lat_sumber
    bvt["Longitude"] = lon_sumber
    bvt["Road Type"] = bvt["Road Type"].replace({"Not Define": "Tidak diketahui", "#N/A": "Tidak diketahui"}).fillna("Tidak diketahui")
    bvt["SES"] = bvt["SES"].fillna("Tidak diketahui")

    bvt["Red List"] = bvt["Red Ocean"].map(item_list)
    bvt["Blue List"] = bvt["Blue Ocean"].map(item_list)
    bvt["Red Count"] = bvt["Red List"].str.len()
    bvt["Blue Count"] = bvt["Blue List"].str.len()
    bvt["Blue Ocean Score (%)"] = (
        bvt["Blue Count"] / (bvt["Red Count"] + bvt["Blue Count"]).replace(0, np.nan) * 100
    ).round(1)
    bvt["Kelas BVT"] = np.select(
        [bvt["Blue Count"] == 0, bvt["Blue Ocean Score (%)"] >= 50],
        ["Red Ocean", "Blue Ocean"],
        default="Peluang Campuran",
    )

    # Fallback koordinat: master valid -> pakai master; jika tidak, pakai BVT.
    info = (
        master.set_index("No. SPBU")[
            [
                "Latitude",
                "Longitude",
                "Nama SPBU",
                "Jenis Lembaga Penyalur",
                "Tipe SPBU",
                "Reguler",
                "Provinsi",
                "Kota/Kabupaten",
                "Kecamatan",
                "Kelurahan",
                "Alamat",
            ]
        ]
        .add_prefix("m_")
    )
    bvt = bvt.join(info, on="No. SPBU")

    master_valid = bvt["m_Latitude"].notna() & bvt["m_Longitude"].notna()
    bvt["Sumber Tilok"] = np.where(master_valid, "Master Lembaga Penyalur", "BVT")
    bvt["Latitude"] = bvt["m_Latitude"].where(master_valid, bvt["Latitude"])
    bvt["Longitude"] = bvt["m_Longitude"].where(master_valid, bvt["Longitude"])

    for target, sumber_bvt, sumber_master in (
        ("Provinsi", "Province", "m_Provinsi"),
        ("Kota/Kabupaten", "City", "m_Kota/Kabupaten"),
        ("Kecamatan", "District", "m_Kecamatan"),
        ("Kelurahan", "Village", "m_Kelurahan"),
        ("Alamat", "Address", "m_Alamat"),
    ):
        nilai_bvt = bvt[sumber_bvt] if sumber_bvt in bvt.columns else pd.Series(index=bvt.index, dtype="object")
        nilai_master = (
            bvt[sumber_master] if sumber_master in bvt.columns else pd.Series(index=bvt.index, dtype="object")
        )
        bvt[target] = nilai_bvt.fillna(nilai_master).fillna("Tidak diketahui")

    bvt["Nama SPBU"] = bvt["m_Nama SPBU"].fillna("Tidak diketahui")
    bvt["Jenis Lembaga Penyalur"] = bvt["m_Jenis Lembaga Penyalur"].fillna("Tidak diketahui")
    bvt["Tipe SPBU"] = bvt["m_Tipe SPBU"].fillna("Tidak diketahui")
    bvt["Reguler"] = bvt["m_Reguler"].astype("boolean").fillna(False).astype(bool)
    bvt["Google Maps"] = [maps_link(lat, lon) for lat, lon in zip(bvt["Latitude"], bvt["Longitude"])]
    bvt["Red Ocean"] = bvt["Red Ocean"].fillna("-")
    bvt["Blue Ocean"] = bvt["Blue Ocean"].fillna("-")

    master["Google Maps"] = [maps_link(lat, lon) for lat, lon in zip(master["Latitude"], master["Longitude"])]

    # Isi master yang koordinatnya tidak valid dari BVT.
    bvt_map = bvt.set_index("No. SPBU")[["Latitude", "Longitude"]]
    for idx, row in master.iterrows():
        if pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
            continue
        if row["No. SPBU"] in bvt_map.index:
            lat, lon = bvt_map.loc[row["No. SPBU"]]
            if pd.notna(lat) and pd.notna(lon):
                master.at[idx, "Latitude"] = lat
                master.at[idx, "Longitude"] = lon
                master.at[idx, "Sumber Tilok"] = "BVT"
    master["Google Maps"] = [maps_link(lat, lon) for lat, lon in zip(master["Latitude"], master["Longitude"])]

    master_out = master[
        [
            "No. SPBU",
            "Nama SPBU",
            "Jenis Lembaga Penyalur",
            "Reguler",
            "Tipe SPBU",
            "Ownership",
            "Provinsi",
            "Kota/Kabupaten",
            "Kecamatan",
            "Kelurahan",
            "Alamat",
            "Latitude",
            "Longitude",
            "Sumber Tilok",
            "Status Operasi",
            "Google Maps",
        ]
    ].rename(columns={"Kelurahan": "Desa/Kelurahan"})

    bvt_out = bvt[
        [
            "No. SPBU",
            "Nama SPBU",
            "Jenis Lembaga Penyalur",
            "Reguler",
            "Tipe SPBU",
            "Provinsi",
            "Kota/Kabupaten",
            "Kecamatan",
            "Kelurahan",
            "Alamat",
            "Latitude",
            "Longitude",
            "Sumber Tilok",
            "Road Type",
            "SES",
            "Red Ocean",
            "Blue Ocean",
            "Red Count",
            "Blue Count",
            "Blue Ocean Score (%)",
            "Kelas BVT",
            "Google Maps",
        ]
    ].rename(columns={"Kelurahan": "Desa/Kelurahan"})

    OUT_MASTER.parent.mkdir(parents=True, exist_ok=True)
    master_out.to_csv(OUT_MASTER, index=False, encoding="utf-8-sig")
    bvt_out.to_csv(OUT_BVT, index=False, encoding="utf-8-sig")

    print(f"Master : {len(master_out):,} SPBU | Reguler {int(master_out['Reguler'].sum()):,}")
    print(f"BVT    : {len(bvt_out):,} SPBU | Reguler {int(bvt_out['Reguler'].sum()):,}")
    print("Kelas BVT:", bvt_out["Kelas BVT"].value_counts().to_dict())
    print("Koordinat master valid:", int(master_out["Latitude"].notna().sum()), "/", len(master_out))
    print("Koordinat BVT valid:", int(bvt_out["Latitude"].notna().sum()), "/", len(bvt_out))
    print("Output:", OUT_MASTER, OUT_BVT)
    return OUT_MASTER, OUT_BVT


if __name__ == "__main__":
    main()
