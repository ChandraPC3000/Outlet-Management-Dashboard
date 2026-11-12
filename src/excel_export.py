"""Helper ekspor DataFrame ke Excel dengan format rapi (XlsxWriter)."""

from __future__ import annotations

import numbers
from io import BytesIO

import pandas as pd
import xlsxwriter

LEBAR = {
    "No SPBU": 12,
    "ID Agent": 12,
    "Kode Lahan": 18,
    "Brand/Tenant": 32,
    "Tenant NFR": 32,
    "Provinsi": 18,
    "Kota/Kab": 20,
    "Luas (m²)": 12,
    "Status": 26,
    "Status Web Kemitraan": 24,
    "Status Brightspace": 22,
    "ID Agent (Brightspace)": 20,
}


def build_excel(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    """Bangun file Excel (.xlsx) dari DataFrame, lengkap dengan header, filter, dan freeze."""
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    worksheet = workbook.add_worksheet((sheet_name or "Data")[:31])

    header = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#33334D",
            "font_color": "#FFFFFF",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    text = workbook.add_format({"border": 1, "valign": "top"})
    number = workbook.add_format(
        {"border": 1, "num_format": "#,##0.00", "valign": "top"}
    )
    integer = workbook.add_format({"border": 1, "num_format": "#,##0", "valign": "top"})

    for col_idx, col_name in enumerate(df.columns):
        name = str(col_name)
        worksheet.write(0, col_idx, name, header)
        worksheet.set_column(
            col_idx,
            col_idx,
            LEBAR.get(name, min(max(12, len(name) + 2), 40)),
        )

    for row_idx, row in enumerate(df.itertuples(index=False), start=1):
        for col_idx, value in enumerate(row):
            if pd.isna(value):
                worksheet.write_blank(row_idx, col_idx, None, text)
            elif isinstance(value, numbers.Integral) and not isinstance(value, bool):
                worksheet.write_number(row_idx, col_idx, int(value), integer)
            elif isinstance(value, numbers.Real) and not isinstance(value, bool):
                worksheet.write_number(row_idx, col_idx, float(value), number)
            else:
                worksheet.write_string(row_idx, col_idx, str(value), text)

    worksheet.freeze_panes(1, 0)
    if len(df.columns):
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    workbook.close()
    return buffer.getvalue()
