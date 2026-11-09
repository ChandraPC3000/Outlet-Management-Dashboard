"""Bangun ulang 'Data Lead Time NFR.xlsx' dari dataset Izin Prinsip terbaru.

Jalankan: python scripts/build_lead_time.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from src import analytics as an  # noqa: E402
from src.config import IZIN_PATH, LEADTIME_PATH  # noqa: E402
from src.data_loader import load_izin_prinsip  # noqa: E402

HIJAU = "1F4E78"
BIRU_MUDA = "DDEBF7"
ABU = "F2F2F2"
BORDER = Border(
    left=Side(style="thin", color="BFBFBF"),
    right=Side(style="thin", color="BFBFBF"),
    top=Side(style="thin", color="BFBFBF"),
    bottom=Side(style="thin", color="BFBFBF"),
)

HEADER_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
BODY_FONT = Font(name="Calibri", size=10)
TITLE_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=13)

TRACKER: dict[int, int] = {}


def _track(column: int, value) -> None:
    teks = "" if value is None else str(value)
    TRACKER[column] = min(max(TRACKER.get(column, 10), len(teks) + 2), 46)


def _format_for(series: pd.Series, name: str) -> str | None:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DD-MMM-YYYY"
    if "%" in name:
        return '0.0"%"'
    if pd.api.types.is_integer_dtype(series):
        return "#,##0"
    if pd.api.types.is_float_dtype(series):
        if "(hari)" in name:
            return "#,##0.0"
        if "Rp" in name or "sewa" in name.lower():
            return "#,##0"
        return "#,##0.0"
    return None


def _format_value(value) -> str | None:
    if isinstance(value, (pd.Timestamp, datetime)):
        return "DD-MMM-YYYY"
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return "#,##0.0" if isinstance(value, float) else "#,##0"
    return None


def write_title(ws, row: int, text: str, ncols: int) -> int:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=max(ncols, 4))
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = TITLE_FONT
    cell.fill = PatternFill("solid", fgColor=HIJAU)
    cell.alignment = Alignment(vertical="center", horizontal="left")
    ws.row_dimensions[row].height = 24
    return row + 1


def write_table(
    ws,
    df: pd.DataFrame,
    row: int,
    title: str | None = None,
    zebra: bool = True,
    autofilter: bool = False,
    freeze: bool = True,
) -> int:
    if df.empty:
        return row
    if title:
        row = write_title(ws, row, title, len(df.columns))

    for idx, kolom in enumerate(df.columns, start=1):
        cell = ws.cell(row=row, column=idx, value=kolom)
        cell.font = HEADER_FONT
        cell.fill = PatternFill("solid", fgColor=HIJAU)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
        _track(idx, kolom)
    ws.row_dimensions[row].height = 30
    header_row = row

    formats = [_format_for(df[col], col) for col in df.columns]
    for i, record in enumerate(df.itertuples(index=False), start=1):
        excel_row = header_row + i
        for idx, value in enumerate(record, start=1):
            if isinstance(value, pd.Timestamp):
                value = value.to_pydatetime() if not pd.isna(value) else None
            elif pd.isna(value):
                value = None
            cell = ws.cell(row=excel_row, column=idx, value=value)
            cell.font = BODY_FONT
            cell.border = BORDER
            number_format = formats[idx - 1] or _format_value(value)
            if number_format:
                cell.number_format = number_format
            if isinstance(value, str) and len(value) > 40:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            if zebra and i % 2 == 0:
                cell.fill = PatternFill("solid", fgColor=ABU)
            _track(idx, value)

    last_row = header_row + len(df)
    if freeze:
        ws.freeze_panes = ws.cell(row=header_row + 1, column=1)
    if autofilter:
        ws.auto_filter.ref = f"A{header_row}:{get_column_letter(len(df.columns))}{last_row}"
    return last_row + 2


def write_paragraph(ws, row: int, text: str, ncols: int = 8, bold: bool = False) -> int:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name="Calibri", size=10, bold=bold, color="404040")
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[row].height = 30
    return row + 1


def write_sheet_notes(ws, judul: str, subjudul: str) -> int:
    row = write_title(ws, 1, judul, 8)
    row = write_paragraph(ws, row, subjudul, ncols=8)
    ws.sheet_view.showGridLines = False
    return row + 1


def apply_widths(ws) -> None:
    for column, width in TRACKER.items():
        ws.column_dimensions[get_column_letter(column)].width = width
    TRACKER.clear()


def build() -> Path:
    izin = load_izin_prinsip()
    snap = an.snapshot_date(izin)
    ldf = an.prepare_leadtime(izin, snap)

    funnel = an.leadtime_funnel(ldf)
    aging = an.leadtime_aging(ldf)
    stage = an.leadtime_stage_summary(ldf)
    quality = an.leadtime_quality(ldf)
    region = an.pending_by_region(ldf)
    oldest = an.oldest_pending(ldf, 50)

    pending_cols = [
        "ID Pengajuan",
        "No. SPBU",
        "Region",
        "Provinsi",
        "Kab./Kota",
        "Nama Tenant",
        "Nama Brand",
        "Kategori",
        "Tahap",
        "Status",
        "Tgl Pengajuan",
        "Umur Pengajuan (hari)",
        "SLA",
        "Batas",
        "Sisa Hari",
        "Overdue (hari)",
    ]
    pending = (
        ldf[ldf["Kelompok"] == "Pending"]
        .sort_values("Umur Pengajuan (hari)", ascending=False)
        .loc[:, pending_cols]
        .reset_index(drop=True)
        .rename(columns={"SLA": "SLA Target (hari)"})
    )
    pending.insert(0, "No", range(1, len(pending) + 1))

    ringkasan = pd.DataFrame(
        [
            ("Snapshot data", snap.to_pydatetime(), "Tanggal potret data"),
            ("Total baris", len(ldf), "Seluruh baris pengajuan"),
            ("ID pengajuan unik", ldf["ID Pengajuan"].nunique(), "Izin unik"),
            ("SPBU unik", ldf["No. SPBU"].nunique(), "Outlet"),
            ("Pending", int((ldf["Kelompok"] == "Pending").sum()), "Masih dalam proses"),
            ("Terbit / Beroperasi", int((ldf["Kelompok"] == "Terbit / Beroperasi").sum()), ""),
            ("Telah Berakhir", int((ldf["Kelompok"] == "Telah Berakhir").sum()), ""),
            ("Ditolak / Batal", int((ldf["Kelompok"] == "Ditolak / Batal").sum()), ""),
        ],
        columns=["Metrik", "Nilai", "Keterangan"],
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Resume"
    ws.sheet_view.showGridLines = False

    row = write_title(ws, 1, "RESUME ANALISIS LEAD TIME - PROSES PERIZINAN PRINSIP", 9)
    row = write_paragraph(
        ws,
        row,
        f"Snapshot {snap:%d %B %Y}  |  Sumber: {IZIN_PATH.name}  |  "
        "Basis: kolom Tahapan, Status, Tgl Pengajuan, SLA, dan Batas.",
        9,
    )
    row = write_paragraph(
        ws,
        row,
        "Catatan: dataset sumber tidak memuat timestamp transisi antar tahap. "
        "Lead time yang disajikan adalah umur pengajuan saat ini per tahapan (aging), "
        "bukan selisih tanggal masuk-keluar tahap. Baris pada kolom SLA/Batas hanya "
        "tersedia untuk pengajuan yang masih berjalan.",
        9,
    )
    row += 1

    row = write_table(ws, ringkasan, row, "1. RINGKASAN DATASET", freeze=False)
    row = write_table(ws, funnel, row, "2. FUNNEL PER TAHAPAN (posisi saat snapshot)", freeze=False)
    if stage is not None and not stage.empty:
        row = write_table(ws, stage, row, "3. LEAD TIME BERJALAN PER TAHAPAN", freeze=False)
    row = write_table(ws, aging, row, "4. LEAD TIME BERJALAN PER STATUS (pending)", freeze=False)
    row = write_table(ws, region, row, "5. PENDING PER REGION", freeze=False)
    row = write_table(ws, quality, row, "6. KUALITAS DATA", freeze=False)
    row += 1
    row = write_paragraph(
        ws,
        row,
        "Interpretasi: median umur pada tahap Management Fee dan Verifikasi Pembayaran "
        "menunjukkan antrean tertua. Gunakan sheet 'Detail - Pending' untuk daftar "
        "per izin dan sheet 'Top 50 Pending Terlama' untuk prioritas tindak lanjut.",
        9,
    )
    apply_widths(ws)

    # ------------------------------------------------------------------ detail
    ws_funnel = wb.create_sheet("Funnel Tahapan")
    r = write_sheet_notes(
        ws_funnel,
        "FUNNEL PER TAHAPAN",
        f"Snapshot {snap:%d %b %Y} - jumlah baris, izin unik, dan komposisi status tiap tahapan.",
    )
    write_table(ws_funnel, funnel, r, autofilter=True)
    apply_widths(ws_funnel)

    ws_stage = wb.create_sheet("Lead Time Tahapan")
    r = write_sheet_notes(
        ws_stage,
        "LEAD TIME BERJALAN PER TAHAPAN",
        "Umur dihitung dari Tgl Pengajuan sampai tanggal snapshot. Hanya pengajuan berstatus pending.",
    )
    write_table(ws_stage, stage, r, autofilter=True)
    for col in ("Median Umur (hari)", "P90 Umur (hari)"):
        if col in stage.columns:
            idx = list(stage.columns).index(col) + 1
            letter = get_column_letter(idx)
            ws_stage.conditional_formatting.add(
                f"{letter}{r + 1}:{letter}{r + len(stage)}",
                DataBarRule(start_type="num", start_value=0, end_type="max", color="F4B084"),
            )
    apply_widths(ws_stage)

    ws_status = wb.create_sheet("Lead Time per Status")
    r = write_sheet_notes(
        ws_status,
        "LEAD TIME BERJALAN PER STATUS",
        "Rincian aging per status pending, termasuk SLA target dan jumlah yang sudah lewat Batas.",
    )
    write_table(ws_status, aging, r, autofilter=True)
    if not aging.empty:
        idx = list(aging.columns).index("Median Umur (hari)") + 1
        letter = get_column_letter(idx)
        ws_status.conditional_formatting.add(
            f"{letter}{r + 1}:{letter}{r + len(aging)}",
            DataBarRule(start_type="num", start_value=0, end_type="max", color="F4B084"),
        )
        pct_idx = list(aging.columns).index("% Lewat Batas") + 1
        pct_letter = get_column_letter(pct_idx)
        ws_status.conditional_formatting.add(
            f"{pct_letter}{r + 1}:{pct_letter}{r + len(aging)}",
            CellIsRule(operator="greaterThan", formula=["50"], fill=PatternFill("solid", fgColor="FFC7CE")),
        )
    apply_widths(ws_status)

    ws_region = wb.create_sheet("Pending per Region")
    r = write_sheet_notes(
        ws_region,
        "PENDING PER REGION",
        "Jumlah pengajuan pending per region dan tahapan pada saat snapshot.",
    )
    write_table(ws_region, region, r, autofilter=True)
    if not region.empty:
        letter = get_column_letter(len(region.columns))
        ws_region.conditional_formatting.add(
            f"B{r + 1}:{letter}{r + len(region)}",
            ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="F4B084"),
        )
    apply_widths(ws_region)

    ws_detail = wb.create_sheet("Detail - Pending")
    ws_detail.sheet_view.showGridLines = False
    ws_detail["A1"] = "< Kembali ke Resume"
    ws_detail["A1"].hyperlink = "#'Resume'!A1"
    ws_detail["A1"].font = Font(name="Calibri", size=10, color="0563C1", underline="single")
    r = write_table(
        ws_detail,
        pending,
        3,
        title=f"DAFTAR DETAIL - {len(pending):,} pengajuan pending per {snap:%d %b %Y}".replace(",", "."),
        autofilter=True,
    )
    if len(pending):
        letter = get_column_letter(list(pending.columns).index("Umur Pengajuan (hari)") + 1)
        ws_detail.conditional_formatting.add(
            f"{letter}4:{letter}{3 + len(pending)}",
            DataBarRule(start_type="num", start_value=0, end_type="max", color="F4B084"),
        )
    apply_widths(ws_detail)

    ws_old = wb.create_sheet("Top 50 Pending Terlama")
    ws_old.sheet_view.showGridLines = False
    ws_old["A1"] = "< Kembali ke Resume"
    ws_old["A1"].hyperlink = "#'Resume'!A1"
    ws_old["A1"].font = Font(name="Calibri", size=10, color="0563C1", underline="single")
    write_table(ws_old, oldest, 3, title="50 PENGAJUAN PENDING TERLAMA", autofilter=True)
    apply_widths(ws_old)

    ws_quality = wb.create_sheet("Kualitas Data")
    r = write_sheet_notes(
        ws_quality,
        "KUALITAS DATA",
        "Temuan yang perlu diperhatikan sebelum memakai angka lead time untuk keputusan.",
    )
    write_table(ws_quality, quality, r)
    apply_widths(ws_quality)

    ws_method = wb.create_sheet("Metodologi")
    ws_method.sheet_view.showGridLines = False
    row = write_title(ws_method, 1, "METODOLOGI & BATASAN", 9)
    catatan = [
        ("Sumber", IZIN_PATH.name),
        ("Snapshot", f"{snap:%d %B %Y}"),
        ("Definisi pending", "Status: Menunggu Verifikasi SBM/SAM/MS3, Menunggu Verifikasi, "
         "Menunggu Pembayaran, Input Nominal, Revisi Pembayaran, Verifikasi Pembayaran."),
        ("Definisi selesai", "Beroperasi, Terbit, Telah Berakhir, Kadaluarsa."),
        ("Ukuran lead time", "Umur pengajuan = tanggal snapshot - Tgl Pengajuan. Untuk pengajuan "
         "pending, nilai ini menunjukkan berapa lama pengajuan sudah berjalan/tertahan."),
        ("SLA & Batas", "Kolom SLA adalah target hari pada tahap berjalan; Batas adalah tenggat "
         "yang dihitung sistem. Hanya 717 baris memiliki Batas."),
        ("Keterbatasan", "Dataset pengajuan tidak memuat timestamp masuk/keluar tiap tahap "
         "(SBM, SAM, MS3, management fee, invoice). Karena itu lead time antar tahap tidak dapat "
         "dihitung sebagai selisih tanggal; yang disajikan adalah aging per tahapan."),
        ("Data duplikat", "4.222 baris memiliki ID pengajuan yang sama. Umumnya re-submission "
         "atau revisi brand, bukan duplikasi data mentah. Tidak dihapus otomatis."),
        ("Nilai sewa 0", "14.732 baris memiliki Total Harga Sewa 0; bisa berarti gratis, "
         "belum diisi, atau bukan objek sewa."),
    ]
    row += 1
    for judul, isi in catatan:
        ws_method.cell(row=row, column=1, value=judul).font = Font(bold=True, size=10)
        cell = ws_method.cell(row=row, column=2, value=isi)
        cell.font = BODY_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws_method.merge_cells(start_row=row, start_column=2, end_row=row, end_column=9)
        ws_method.row_dimensions[row].height = 34
        row += 1
    ws_method.column_dimensions["A"].width = 22
    for col in "BCDEFGHI":
        ws_method.column_dimensions[col].width = 16

    # ------------------------------------------------------------------ dataset
    ws_data = wb.create_sheet("Dataset")
    kolom = [
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
        "Tgl Pengajuan",
        "Tgl Mulai Sewa Lahan",
        "Tgl Akhir Sewa Lahan",
        "Tgl Berakhir Izin Prinsip",
        "Tahapan",
        "Status",
        "SLA",
        "Batas",
        "Tahap",
        "Kelompok",
        "Umur Pengajuan (hari)",
        "Sisa Hari",
        "Overdue (hari)",
    ]
    data = ldf.loc[:, kolom].rename(columns={"SLA": "SLA Target (hari)"})
    ws_data.sheet_view.showGridLines = False
    ws_data["A1"] = "< Kembali ke Resume"
    ws_data["A1"].hyperlink = "#'Resume'!A1"
    ws_data["A1"].font = Font(name="Calibri", size=10, color="0563C1", underline="single")
    header_row = 3
    for idx, nama in enumerate(data.columns, start=1):
        cell = ws_data.cell(row=header_row, column=idx, value=nama)
        cell.font = HEADER_FONT
        cell.fill = PatternFill("solid", fgColor=HIJAU)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = BORDER
    ws_data.row_dimensions[header_row].height = 30

    formats = [_format_for(data[col], col) for col in data.columns]
    for i, record in enumerate(data.itertuples(index=False), start=1):
        excel_row = header_row + i
        for idx, value in enumerate(record, start=1):
            if isinstance(value, pd.Timestamp):
                value = value.to_pydatetime() if not pd.isna(value) else None
            elif pd.isna(value):
                value = None
            cell = ws_data.cell(row=excel_row, column=idx, value=value)
            if formats[idx - 1]:
                cell.number_format = formats[idx - 1]

    ws_data.freeze_panes = f"C{header_row + 1}"
    ws_data.auto_filter.ref = f"A{header_row}:{get_column_letter(len(data.columns))}{header_row + len(data)}"
    for idx, nama in enumerate(data.columns, start=1):
        lebar = min(max(len(nama) + 2, 12), 34)
        ws_data.column_dimensions[get_column_letter(idx)].width = lebar

    # ------------------------------------------------------------------ simpan
    wb.save(LEADTIME_PATH)
    return LEADTIME_PATH


if __name__ == "__main__":
    mulai = datetime.now()
    path = build()
    print(f"Selesai: {path} ({path.stat().st_size / 1e6:.2f} MB) dalam {(datetime.now() - mulai).seconds} detik")
