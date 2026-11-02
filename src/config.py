"""Konstanta dan konfigurasi global aplikasi NFR Analytics Pro."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "Data" / "Pengajuan NFR Izin Prinsip 10-April-2026.xlsx"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_PATH = ASSETS_DIR / "style.css"
LOGO_PATH = ASSETS_DIR / "logo.png"

APP_TITLE = "NFR Analytics Pro"
APP_ICON = "🚀"

# Kolom yang wajib ada di dataset. Kalau salah satu hilang, aplikasi berhenti
# dengan pesan yang jelas alih-alih melempar KeyError di tengah dashboard.
REQUIRED_COLUMNS: tuple[str, ...] = (
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

# Kolom opsional: dikonversi hanya jika tersedia.
DATE_COLUMNS: tuple[str, ...] = (
    "Tgl Pengajuan",
    "Tgl Mulai Sewa Lahan",
    "Tgl Akhir Sewa Lahan",
    "Tgl Berakhir Izin Prinsip",
    "Batas",
)
NUMERIC_COLUMNS: tuple[str, ...] = ("Total Harga Sewa", "Nominal Fee", "SLA")
FALLBACK_TEXT_COLUMNS: tuple[str, ...] = ("Kategori", "Sub Kategori")
TEXT_COLUMNS: tuple[str, ...] = tuple(
    col
    for col in REQUIRED_COLUMNS
    if col not in NUMERIC_COLUMNS and col not in DATE_COLUMNS
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
