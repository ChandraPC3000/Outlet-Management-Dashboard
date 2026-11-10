"""Konstanta dan konfigurasi global aplikasi NFR Analytics Pro."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_PATH = ASSETS_DIR / "style.css"
LOGO_PATH = ASSETS_DIR / "logo_dark.png"
LOGO_LIGHT_PATH = ASSETS_DIR / "logo_light.png"
FAVICON_PATH = ASSETS_DIR / "favicon.png"

# --- Dataset -----------------------------------------------------------------
_BULAN = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def _tanggal_dari_nama(path: Path) -> date | None:
    """Ambil tanggal dari nama file, mis. '09-November-2026'."""
    cocok = re.search(r"(\d{1,2})-([A-Za-z]+)-(\d{4})", path.stem)
    if not cocok:
        return None
    hari, bulan, tahun = cocok.groups()
    nomor_bulan = _BULAN.get(bulan.lower())
    if not nomor_bulan:
        return None
    try:
        return date(int(tahun), nomor_bulan, int(hari))
    except ValueError:
        return None


def _file_terbaru(pola: str, fallback: str) -> Path:
    """Pilih file dengan tanggal terbaru pada nama; fallback bila tidak ada."""
    kandidat = list(DATA_DIR.glob(pola))
    if not kandidat:
        return DATA_DIR / fallback
    return max(
        kandidat,
        key=lambda p: (_tanggal_dari_nama(p) or date.min, p.name),
    )


IZIN_PATH = _file_terbaru(
    "Pengajuan NFR Izin Prinsip *.xlsx",
    "Pengajuan NFR Izin Prinsip 09-November-2026.xlsx",
)
LAHAN_PATH = _file_terbaru(
    "NFR Master Lahan *.xlsx",
    "NFR Master Lahan 09-November-2026.xlsx",
)
SEWA_PATH = _file_terbaru(
    "Pengajuan NFR Sewa Lahan *.xlsx",
    "Pengajuan NFR Sewa Lahan 09-November-2026.xlsx",
)
LEADTIME_PATH = DATA_DIR / "Data Lead Time NFR.xlsx"
KETERSEDIAAN_PATH = DATA_DIR / "Ketersediaan Lahan NFR - November 2026.xlsx"
KETERSEDIAAN_SNAPSHOT = "November 2026"
SPBU_MASTER_PATH = DATA_DIR / "spbu_master.csv"
BVT_PATH = DATA_DIR / "bvt_spbu.csv"

APP_TITLE = "NFR Analytics Pro"
APP_ICON = str(FAVICON_PATH)

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

# Palet warna profesional dengan latar terang.
PALETTE: tuple[str, ...] = (
    "#111827",
    "#1d4ed8",
    "#0f766e",
    "#b45309",
    "#b91c1c",
    "#4338ca",
    "#0369a1",
    "#4d7c0f",
    "#6b7280",
    "#9a3412",
)

PLOTLY_TEMPLATE = "plotly_white"
