"""Ekspor daftar ketersediaan lahan ke Excel dengan format mitra (contoh Momoyo)."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd
import xlsxwriter

KOLOM_MITRA = [
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

LEBAR = {
    "No. SPBU": 12,
    "Nama Perusahaan": 40,
    "Provinsi": 17,
    "Kota/Kab": 20,
    "Kecamatan": 25,
    "Desa/Kelurahan": 24,
    "Alamat": 65,
    "Luas (M2)": 12,
    "Latitude": 13,
    "Longitude": 13,
    "Road Type": 22,
    "SES": 50,
    "Red Ocean": 55,
    "Blue Ocean": 55,
    "Status Sewa": 14,
    "Kontak PIC SPBU": 18,
    "No Kantor SPBU": 18,
    "PSO": 12,
    "Non PSO": 12,
    "Total": 12,
    "PSO2": 12,
    "Non PSO2": 12,
    "Total2": 10,
}


def _num_format(kolom: str) -> str:
    if kolom == "Luas (M2)":
        return "#,##0.00"
    if kolom in ("Latitude", "Longitude"):
        return "0.000000"
    if kolom in ("PSO", "Non PSO", "Total", "PSO2", "Non PSO2", "Total2"):
        return "#,##0.00"
    return "@"


def build_ketersediaan_excel(df: pd.DataFrame, filter_desc: str = "") -> bytes:
    """Bangun workbook format mitra. Kolom classified tidak pernah disertakan."""
    tabel = df.loc[:, [k for k in KOLOM_MITRA if k in df.columns]].copy()
    tabel = tabel.rename(columns={"No. SPBU": "No SPBU"})
    tabel = tabel.sort_values(
        ["Provinsi", "Kota/Kab", "No SPBU", "Luas (M2)"],
        ascending=[True, True, True, False],
    )
    kolom = list(tabel.columns)

    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})

    ws = workbook.add_worksheet("Ketersediaan Lahan")
    ws.hide_gridlines(2)

    header_fmt = workbook.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#0070C0",
            "border": 1,
            "border_color": "#BFBFBF",
            "font_name": "Calibri",
            "font_size": 11,
            "valign": "vcenter",
        }
    )
    group_fmt = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9E1F2",
            "border": 1,
            "border_color": "#BFBFBF",
            "align": "center",
            "valign": "vcenter",
            "font_name": "Calibri",
            "font_size": 11,
        }
    )
    col_formats = []
    for nama in kolom:
        col_formats.append(
            workbook.add_format(
                {
                    "font_name": "Calibri",
                    "font_size": 11,
                    "border": 1,
                    "border_color": "#BFBFBF",
                    "valign": "vcenter",
                    "num_format": _num_format(nama),
                }
            )
        )

    def col_index(nama: str) -> int:
        return 2 + kolom.index(nama)

    # Baris 1-2 kosong mengikuti contoh; baris 3 header grup.
    for label, anggota in (
        ("Volume (KL) / Month", ["PSO", "Non PSO", "Total"]),
        ("Transaksi / Month", ["PSO2", "Non PSO2", "Total2"]),
    ):
        awal = col_index(anggota[0])
        ws.merge_range(2, awal, 2, awal + len(anggota) - 1, label, group_fmt)

    for offset, nama in enumerate(kolom):
        ws.write(3, 2 + offset, nama, header_fmt)
        ws.set_column(2 + offset, 2 + offset, LEBAR.get(nama, 14))

    for baris, record in enumerate(tabel.itertuples(index=False), start=4):
        for offset, value in enumerate(record):
            fmt = col_formats[offset]
            kolom_c = 2 + offset
            if pd.isna(value):
                ws.write_blank(baris, kolom_c, None, fmt)
            elif isinstance(value, str):
                ws.write_string(baris, kolom_c, value, fmt)
            else:
                ws.write_number(baris, kolom_c, float(value), fmt)

    last_row = 4 + len(tabel) - 1
    last_col = 2 + len(kolom) - 1
    ws.freeze_panes(4, 19)  # T5: kolom C-S dan 4 baris teratas tetap terlihat
    ws.autofilter(3, 2, last_row, last_col)

    # --------------------------------------------------------------- catatan
    cat = workbook.add_worksheet("Catatan")
    cat.hide_gridlines(2)
    cat.set_column(0, 0, 24)
    cat.set_column(1, 5, 22)
    judul_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E78"})
    label_fmt = workbook.add_format({"bold": True, "font_size": 10, "valign": "top"})
    isi_fmt = workbook.add_format({"font_size": 10, "text_wrap": True, "valign": "top"})

    cat.write("A1", "CATATAN - KETERSEDIAAN LAHAN NFR", judul_fmt)
    catatan = [
        ("Sumber data", "Ketersediaan Lahan NFR - November 2026"),
        ("Snapshot", "November 2026"),
        ("Baris diekspor", f"{len(tabel):,}".replace(",", ".")),
        ("Jumlah SPBU", f"{tabel['No SPBU'].nunique():,}".replace(",", ".")),
        ("Filter aktif", filter_desc or "Tanpa filter (seluruh lahan tersedia)"),
        (
            "Kolom tidak ditampilkan",
            "Harga Sewa, Tipe SPBU, Kelas SPBU, GES, dan Fasilitas EV "
            "(classified - tidak dibagikan ke mitra).",
        ),
        (
            "Nomor PIC",
            "Kontak PIC SPBU = Nomor Owner/Manager SPBU (kolom T List Lembaga "
            "Penyalur 13 Oktober 2026); No Kantor SPBU = Nomor Kantor SPBU "
            "(kolom V).",
        ),
        (
            "Penggunaan",
            "Daftar ini untuk mitra yang mencari lokasi outlet baru di area SPBU. "
            "Nomor PIC hanya untuk koordinasi resmi.",
        ),
        ("Dibuat", datetime.now().strftime("%d %B %Y %H:%M")),
    ]
    for i, (label, nilai) in enumerate(catatan, start=2):
        cat.write(i, 0, label, label_fmt)
        cat.merge_range(i, 1, i, 5, nilai, isi_fmt)
        cat.set_row(i, 32)

    workbook.close()
    return buffer.getvalue()
