"""Bangun dataset Ketersediaan Lahan NFR yang aman dibagikan ke mitra.

Sumber (lokal, TIDAK di-commit karena memuat kolom classified):
  - Ketersediaan Lahan NFR - November 2026.xlsx
  - List Lembaga Penyalur 13 Oktober 2026.xlsx (sheet Authors, kolom T & V)

Output:
  - Data/Ketersediaan Lahan NFR - November 2026.xlsx  (tanpa kolom classified)

Jalankan: python scripts/build_ketersediaan.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

RAW_AVAIL = Path(r"F:/Ketersediaan Lahan NFR - November 2026.xlsx")
RAW_PIC = Path(r"F:/List Lembaga Penyalur 13 Oktober 2026.xlsx")
OUTPUT = ROOT / "Data" / "Ketersediaan Lahan NFR - November 2026.xlsx"

# Kolom yang tidak boleh keluar dari repo / tampil di dashboard.
CLASSIFIED = (
    "Tipe SPBU",
    "Kelas SPBU",
    "Harga Sewa (Rp)",
    "Green Energy Station (GES)",
    "Fasilitas EV",
)

FINAL_COLUMNS = [
    "No. SPBU",
    "Nama Perusahaan",
    "Provinsi",
    "Kota/Kab",
    "Kecamatan",
    "Desa/Kelurahan",
    "Alamat",
    "Luas (M2)",
    "Latitude",
    "Longitude",
    "Road Type",
    "SES",
    "Red Ocean",
    "Blue Ocean",
    "Status Sewa",
    "Kontak PIC SPBU",
    "No Kantor SPBU",
    "PSO",
    "Non PSO",
    "Total",
    "PSO2",
    "Non PSO2",
    "Total2",
]

NUMERIC = ["Luas (M2)", "Latitude", "Longitude", "PSO", "Non PSO", "Total", "PSO2", "Non PSO2", "Total2"]


def normalize_id(value) -> str | None:
    if pd.isna(value):
        return None
    teks = re.sub(r"\.0$", "", str(value).strip())
    teks = re.sub(r"\s+", "", teks)
    return teks or None


def normalize_phone(value) -> str | None:
    if pd.isna(value):
        return None
    teks = str(value).strip()
    if teks.endswith(".0"):
        teks = teks[:-2]
    teks = re.sub(r"[^\d+]", "", teks)
    return teks or None


def main() -> Path:
    if not RAW_AVAIL.exists():
        raise SystemExit(f"File sumber tidak ditemukan: {RAW_AVAIL}")
    if not RAW_PIC.exists():
        raise SystemExit(f"File PIC tidak ditemukan: {RAW_PIC}")

    df = pd.read_excel(RAW_AVAIL, header=3, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if not c.startswith("Unnamed")]]
    df = df.drop(columns=[c for c in CLASSIFIED if c in df.columns])

    df["No. SPBU"] = df["No SPBU"].map(normalize_id)
    df = df.drop(columns=["No SPBU"])
    df["Kode Lahan"] = df["Kode Lahan"].astype("string").str.strip()
    df["Kontak PIC SPBU"] = df["Kontak PIC SPBU"].map(normalize_phone)

    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Satu baris per (SPBU, Kode Lahan). Duplikat berasal dari pecahan luas
    # lahan yang sama, jadi luasnya dijumlahkan (total luas tidak berubah).
    df = df.sort_values("Luas (M2)", ascending=False, na_position="last")
    total_luas = df.groupby(["No. SPBU", "Kode Lahan"])["Luas (M2)"].sum()
    df = df.drop_duplicates(["No. SPBU", "Kode Lahan"], keep="first").set_index(
        ["No. SPBU", "Kode Lahan"]
    )
    df["Luas (M2)"] = total_luas
    df = df.reset_index().drop(columns=["Kode Lahan"])

    # PIC: kolom T = Nomor Owner/Manager, kolom V = Nomor Kantor SPBU.
    pic = pd.read_excel(RAW_PIC, sheet_name="Authors", engine="openpyxl")
    pic.columns = [str(c).strip() for c in pic.columns]
    pic["No. SPBU"] = pic["No. SPBU"].map(normalize_id)
    pic["No Owner/Manager"] = pic["No Kontak PIC"].map(normalize_phone)
    pic["No Kantor"] = pic["No Telp"].map(normalize_phone)
    pic = pic.dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU")

    df = df.merge(
        pic[["No. SPBU", "No Owner/Manager", "No Kantor"]],
        on="No. SPBU",
        how="left",
    )
    df["Kontak PIC SPBU"] = df["Kontak PIC SPBU"].fillna(df["No Owner/Manager"])
    df["No Kantor SPBU"] = df["No Kantor"]
    df = df.drop(columns=["No Owner/Manager", "No Kantor"])

    # Teks yang kosong / "#N/A" diberi label netral.
    for col in ("Provinsi", "Kota/Kab", "Kecamatan", "Desa/Kelurahan", "Road Type", "SES", "Red Ocean", "Blue Ocean"):
        df[col] = df[col].replace({"#N/A": pd.NA})
        df[col] = df[col].fillna("Tidak diketahui")
    for col in ("Nama Perusahaan", "Alamat", "Status Sewa"):
        df[col] = df[col].fillna("Tidak diketahui")

    df = df.loc[:, FINAL_COLUMNS]
    df = df.sort_values(["Provinsi", "Kota/Kab", "No. SPBU", "Luas (M2)"], ascending=[True, True, True, False])

    sisa_classified = [c for c in CLASSIFIED if c in df.columns]
    if sisa_classified:
        raise SystemExit(f"Kolom classified masih ada: {sisa_classified}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT, index=False, sheet_name="Ketersediaan Lahan", engine="openpyxl")

    print(f"Baris: {len(df):,} | SPBU: {df['No. SPBU'].nunique():,} | Provinsi: {df['Provinsi'].nunique()}")
    print(f"PIC owner: {df['Kontak PIC SPBU'].notna().sum():,} | PIC kantor: {df['No Kantor SPBU'].notna().sum():,}")
    print(f"Output: {OUTPUT} ({OUTPUT.stat().st_size / 1e6:.2f} MB)")
    return OUTPUT


if __name__ == "__main__":
    main()
