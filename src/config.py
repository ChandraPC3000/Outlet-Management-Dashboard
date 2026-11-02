"""Konstanta dan konfigurasi global aplikasi NFR Analytics Pro."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_PATH = ASSETS_DIR / "style.css"
LOGO_PATH = ASSETS_DIR / "logo.png"

# --- Dataset -----------------------------------------------------------------
IZIN_PATH = DATA_DIR / "Pengajuan NFR Izin Prinsip 02-November-2026.xlsx"
LAHAN_PATH = DATA_DIR / "NFR Master Lahan 02-November-2026.xlsx"
SEWA_PATH = DATA_DIR / "Pengajuan NFR Sewa Lahan 02-November-2026.xlsx"
LEADTIME_PATH = DATA_DIR / "Data Lead Time NFR 02112026.xlsx"
KETERSEDIAAN_PATH = DATA_DIR / "Ketersediaan Lahan NFR - November 2026.xlsx"
KETERSEDIAAN_SNAPSHOT = "November 2026"

APP_TITLE = "NFR Analytics Pro"
APP_ICON = "🚀"

IZIN_REQUIRED: tuple[str, ...] = (
    "Tgl Pengajuan",
    "ID Pengajuan",
    "No. SPBU",
    "Region",
    "Provinsi",
    "Kab./Kota",
    "Nama Tenant",
    "Nama Brand",
    "Tipe Brand",
    "Kategori",
    "Sub Kategori",
    "Total Harga Sewa",
    "Nominal Fee",
    "Tahapan",
    "Status",
    "SLA",
)

LAHAN_REQUIRED: tuple[str, ...] = (
    "No. SPBU",
    "Kode Lahan",
    "Luas (M2)",
    "Harga (Rp)",
    "Tenant",
    "Tanggal Mulai Sewa",
    "Tanggal Berakhir Sewa",
    "Harga Sewa (Rp)",
    "Status Sewa",
    "Status Approval",
)

SEWA_REQUIRED: tuple[str, ...] = (
    "No. SPBU",
    "ID Tenant",
    "Nama Tenant",
    "Nama Brand",
    "Jenis Brand",
    "Kategori/Sub Kategori",
    "Total Harga Sewa",
    "Tanggal Mulai Sewa",
    "Tanggal Berakhir Sewa",
    "Status Sewa",
    "Status Izin Prinsip",
)

IZIN_DATE_COLUMNS: tuple[str, ...] = (
    "Tgl Pengajuan",
    "Tgl Mulai Sewa Lahan",
    "Tgl Akhir Sewa Lahan",
    "Tgl Berakhir Izin Prinsip",
    "Batas",
)
IZIN_NUMERIC_COLUMNS: tuple[str, ...] = ("Total Harga Sewa", "Nominal Fee", "SLA")
IZIN_FALLBACK_TEXT = ("Kategori", "Sub Kategori")
IZIN_TEXT_COLUMNS: tuple[str, ...] = tuple(
    col
    for col in IZIN_REQUIRED
    if col not in IZIN_NUMERIC_COLUMNS and col not in IZIN_DATE_COLUMNS
)

LAHAN_NUMERIC_COLUMNS = ("Luas (M2)", "Harga (Rp)", "Harga Sewa (Rp)")
LAHAN_DATE_COLUMNS = ("Tanggal Mulai Sewa", "Tanggal Berakhir Sewa")

SEWA_NUMERIC_COLUMNS = ("Total Harga Sewa",)
SEWA_DATE_COLUMNS = (
    "Tanggal Mulai Sewa",
    "Tanggal Berakhir Sewa",
    "Tanggal Berakhir Izin Prinsip",
)

KETERSEDIAAN_REQUIRED: tuple[str, ...] = (
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
)
KETERSEDIAAN_NUMERIC_COLUMNS = (
    "Luas (M2)",
    "Latitude",
    "Longitude",
    "PSO",
    "Non PSO",
    "Total",
    "PSO2",
    "Non PSO2",
    "Total2",
)
KETERSEDIAAN_TEXT_COLUMNS = tuple(
    col for col in KETERSEDIAAN_REQUIRED if col not in KETERSEDIAAN_NUMERIC_COLUMNS
)
# Kolom yang tidak boleh tampil / ter-commit (classified).
CLASSIFIED_LAHAN_COLUMNS = (
    "Tipe SPBU",
    "Kelas SPBU",
    "Harga Sewa (Rp)",
    "Green Energy Station (GES)",
    "Fasilitas EV",
)

# Palet warna senada tema gelap GitHub.
PALETTE: tuple[str, ...] = (
    "#58a6ff",
    "#3fb950",
    "#d29922",
    "#f85149",
    "#a371f7",
    "#39c5cf",
    "#db6d28",
    "#8b949e",
    "#ff7b72",
    "#7ee787",
)

PLOTLY_TEMPLATE = "plotly_dark"
