"""Generator Excel Occupancy Rate per SPBU (format occupancy_nfr_2026-09-04)."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st
import xlsxwriter

from src import analytics as an
from src.data_loader import (
    load_izin_prinsip,
    load_ketersediaan,
    load_master_lahan,
)
from src.master_data import load_bvt, load_spbu_master

REGION_LABEL = {
    "SUMBAGUT": "Sumbagut",
    "SUMBAGSEL": "Sumbagsel",
    "JBB": "JBB",
    "JBT": "JBT",
    "JTM BALINUS": "Jatimbalinus",
    "KALIMANTAN": "Kalimantan",
    "SULAWESI": "Sulawesi",
    "MALUKU PAPUA": "Maluku Papua",
}
REGION_ORDER = [
    "Sumbagut",
    "Sumbagsel",
    "JBB",
    "JBT",
    "Jatimbalinus",
    "Kalimantan",
    "Sulawesi",
    "Maluku Papua",
]

PROVINSI_REGION = {
    "Aceh": "Sumbagut",
    "Sumatera Utara": "Sumbagut",
    "Sumatera Barat": "Sumbagut",
    "Riau": "Sumbagut",
    "Kepulauan Riau": "Sumbagut",
    "Jambi": "Sumbagsel",
    "Bengkulu": "Sumbagsel",
    "Sumatera Selatan": "Sumbagsel",
    "Bangka Belitung": "Sumbagsel",
    "Kepulauan Bangka Belitung": "Sumbagsel",
    "Lampung": "Sumbagsel",
    "Dki Jakarta": "JBB",
    "Jakarta": "JBB",
    "Jawa Barat": "JBB",
    "Banten": "JBB",
    "Jawa Tengah": "JBT",
    "Di Yogyakarta": "JBT",
    "Yogyakarta": "JBT",
    "Jawa Timur": "Jatimbalinus",
    "Bali": "Jatimbalinus",
    "Nusa Tenggara Barat": "Jatimbalinus",
    "Nusa Tenggara Timur": "Jatimbalinus",
    "Kalimantan Barat": "Kalimantan",
    "Kalimantan Tengah": "Kalimantan",
    "Kalimantan Selatan": "Kalimantan",
    "Kalimantan Timur": "Kalimantan",
    "Kalimantan Utara": "Kalimantan",
    "Sulawesi Utara": "Sulawesi",
    "Gorontalo": "Sulawesi",
    "Sulawesi Tengah": "Sulawesi",
    "Sulawesi Barat": "Sulawesi",
    "Sulawesi Selatan": "Sulawesi",
    "Sulawesi Tenggara": "Sulawesi",
    "Maluku": "Maluku Papua",
    "Maluku Utara": "Maluku Papua",
    "Papua": "Maluku Papua",
    "Papua Barat": "Maluku Papua",
    "Papua Barat Daya": "Maluku Papua",
    "Papua Tengah": "Maluku Papua",
    "Papua Pegunungan": "Maluku Papua",
    "Papua Selatan": "Maluku Papua",
}

KOLOM = [
    "No SPBU",
    "Kode Lahan",
    "Nama Perusahaan",
    "Nama Tenant",
    "Region",
    "Provinsi",
    "Kota/Kab",
    "Kecamatan",
    "Desa/Kelurahan",
    "Alamat",
    "Tipe SPBU",
    "Kelas SPBU",
    "Luas (M2)",
    "Tanggal Mulai Sewa",
    "Tanggal Berakhir Sewa",
    "Harga (Rp)",
    "Harga Sewa (Rp)",
    "Latitude",
    "Longitude",
    "Road Type",
    "SES",
    "Red Ocean",
    "Blue Ocean",
    "Status Sewa",
    "Green Energy Station (GES)",
    "Fasilitas EV",
    "PSO",
    "Non PSO",
    "Total",
    "PSO2",
    "Non PSO2",
    "Total2",
]


def _provinsi_key(value) -> str:
    teks = "" if pd.isna(value) else str(value).strip().title()
    teks = " ".join(teks.replace("-", " ").replace("_", " ").split())
    if teks.startswith("Nanggroe Aceh") or teks.startswith("Nangroe Aceh"):
        return "Aceh"
    if teks.startswith("Dki"):
        return "Dki Jakarta"
    if teks.startswith("Daerah Istimewa Yogyakarta") or teks == "Di Yogyakarta":
        return "Di Yogyakarta"
    return teks


def _region_dari_provinsi(provinsi) -> str:
    return PROVINSI_REGION.get(_provinsi_key(provinsi), "Tidak diketahui")


@st.cache_data(show_spinner="Menyiapkan Excel Occupancy per SPBU...")
def build_occupancy_excel() -> bytes:
    izin = load_izin_prinsip()
    lahan = an.prepare_lahan(load_master_lahan(), izin)
    master = load_spbu_master()
    bvt = load_bvt()
    ketersediaan = load_ketersediaan()

    df = lahan[
        lahan["Reguler"].fillna(False)
        & lahan["Status Sewa"].isin(["Tersedia", "Tersewa"])
    ].copy()

    atribut = master[
        [
            "No. SPBU",
            "Nama SPBU",
            "Provinsi",
            "Kota/Kabupaten",
            "Kecamatan",
            "Desa/Kelurahan",
            "Alamat",
            "Latitude",
            "Longitude",
        ]
    ].rename(
        columns={
            "Nama SPBU": "Nama Perusahaan",
            "Provinsi": "Provinsi_master",
            "Kota/Kabupaten": "Kota_master",
            "Kecamatan": "Kecamatan_master",
            "Desa/Kelurahan": "Desa_master",
            "Alamat": "Alamat_master",
            "Latitude": "Lat_master",
            "Longitude": "Lon_master",
        }
    )
    df = df.merge(atribut, on="No. SPBU", how="left")

    # Lengkapi kolom lokasi dari master.
    for target, sumber in (
        ("Provinsi", "Provinsi_master"),
        ("Kab./Kota", "Kota_master"),
        ("Kecamatan", "Kecamatan_master"),
        ("Desa/Kelurahan", "Desa_master"),
        ("Alamat", "Alamat_master"),
        ("Latitude", "Lat_master"),
        ("Longitude", "Lon_master"),
    ):
        if target not in df.columns:
            df[target] = df[sumber]
        else:
            df[target] = df[target].replace({"Tidak diketahui": np.nan, "": np.nan})
            df[target] = df[target].fillna(df[sumber])

    df["Region"] = df["Region"].replace({"Tidak diketahui": np.nan, "": np.nan})
    df["Nama Perusahaan"] = df["Nama Perusahaan"].astype("string").str.strip()

    # Region: pakai Region existing, fallback provinsi -> region.
    region = df["Region"].replace({"Tidak diketahui": np.nan, "": np.nan})
    region = region.map(REGION_LABEL).fillna(region)
    fallback = df["Provinsi"].map(_region_dari_provinsi)
    df["Region"] = region.fillna(fallback).fillna("Tidak diketahui")

    # Atribut BVT per SPBU (road type, SES, red/blue ocean).
    bv = bvt[
        ["No. SPBU", "Road Type", "SES", "Red Ocean", "Blue Ocean"]
    ].drop_duplicates("No. SPBU")
    df = df.merge(bv, on="No. SPBU", how="left", suffixes=("", "_bvt"))
    for kolom in ("Road Type", "SES", "Red Ocean", "Blue Ocean"):
        if kolom in df.columns:
            df[kolom] = df[kolom].fillna("Tidak diketahui")

    # Volume/transaksi per SPBU (hanya tersedia untuk SPBU yang ada di file ketersediaan).
    volume = ketersediaan[
        ["No. SPBU", "PSO", "Non PSO", "Total", "PSO2", "Non PSO2", "Total2"]
    ].drop_duplicates("No. SPBU")
    df = df.merge(volume, on="No. SPBU", how="left")

    df["Nama Tenant"] = df["Tenant"].replace({"-": "", " - ": ""}).fillna("")
    df["Kelas SPBU"] = df["Status Level"]
    df["Tipe SPBU"] = df["Tipe SPBU"].replace({"Lainnya": "Missing Data"})
    df["Green Energy Station (GES)"] = "Tidak Diketahui"
    df["Fasilitas EV"] = "Tidak Diketahui"

    tabel = pd.DataFrame(
        {
            "No SPBU": df["No. SPBU"].astype("string"),
            "Kode Lahan": df["Kode Lahan"].astype("string"),
            "Nama Perusahaan": df["Nama Perusahaan"].fillna(""),
            "Nama Tenant": df["Nama Tenant"],
            "Region": df["Region"],
            "Provinsi": df["Provinsi"].fillna("Tidak diketahui"),
            "Kota/Kab": df["Kab./Kota"].fillna("Tidak diketahui"),
            "Kecamatan": df["Kecamatan"].fillna("Tidak diketahui"),
            "Desa/Kelurahan": df["Desa/Kelurahan"].fillna("Tidak diketahui"),
            "Alamat": df["Alamat"].fillna("Tidak diketahui"),
            "Tipe SPBU": df["Tipe SPBU"].fillna("Tidak diketahui"),
            "Kelas SPBU": df["Kelas SPBU"].fillna("Tidak diketahui"),
            "Luas (M2)": df["Luas (M2)"],
            "Tanggal Mulai Sewa": df["Tanggal Mulai Sewa"],
            "Tanggal Berakhir Sewa": df["Tanggal Berakhir Sewa"],
            "Harga (Rp)": df["Harga (Rp)"],
            "Harga Sewa (Rp)": df["Harga Sewa (Rp)"],
            "Latitude": df["Latitude"],
            "Longitude": df["Longitude"],
            "Road Type": df["Road Type"],
            "SES": df["SES"],
            "Red Ocean": df["Red Ocean"],
            "Blue Ocean": df["Blue Ocean"],
            "Status Sewa": df["Status Sewa"],
            "Green Energy Station (GES)": df["Green Energy Station (GES)"],
            "Fasilitas EV": df["Fasilitas EV"],
            "PSO": df["PSO"],
            "Non PSO": df["Non PSO"],
            "Total": df["Total"],
            "PSO2": df["PSO2"],
            "Non PSO2": df["Non PSO2"],
            "Total2": df["Total2"],
        }
    )
    tabel = tabel.loc[:, KOLOM]
    tabel = tabel.sort_values(["Region", "No SPBU", "Kode Lahan"], kind="stable")

    # Pivot OR_Lahan (count of Status Sewa per region).
    pivot = (
        tabel.groupby(["Region", "Status Sewa"]).size().unstack(fill_value=0)
    )
    for status in ("Tersedia", "Tersewa"):
        if status not in pivot.columns:
            pivot[status] = 0
    pivot = pivot[["Tersedia", "Tersewa"]]
    pivot["Grand Total"] = pivot.sum(axis=1)
    pivot["Occupancy Rate"] = pivot["Tersewa"] / pivot["Grand Total"].replace(0, np.nan)
    urutan = [r for r in REGION_ORDER if r in pivot.index] + [
        r for r in pivot.index if r not in REGION_ORDER
    ]
    pivot = pivot.loc[urutan]

    buffer = BytesIO()
    wb = xlsxwriter.Workbook(buffer, {"in_memory": True})
    ws = wb.add_worksheet("Data")
    ws2 = wb.add_worksheet("OR_Lahan")
    ws3 = wb.add_worksheet("Info")

    header = wb.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#0070C0",
            "border": 1,
            "border_color": "#BFBFBF",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    group = wb.add_format(
        {
            "bold": True,
            "bg_color": "#D9E1F2",
            "border": 1,
            "border_color": "#BFBFBF",
            "align": "center",
        }
    )
    body = wb.add_format({"font_size": 10, "border": 1, "border_color": "#D9D9D9"})
    date_fmt = wb.add_format(
        {"font_size": 10, "num_format": "DD-MMM-YYYY", "border": 1, "border_color": "#D9D9D9"}
    )
    money_fmt = wb.add_format(
        {"font_size": 10, "num_format": "#,##0", "border": 1, "border_color": "#D9D9D9"}
    )
    decimal_fmt = wb.add_format(
        {"font_size": 10, "num_format": "#,##0.00", "border": 1, "border_color": "#D9D9D9"}
    )
    coord_fmt = wb.add_format(
        {"font_size": 10, "num_format": "0.000000", "border": 1, "border_color": "#D9D9D9"}
    )

    # Data: baris 1-2 kosong, grup baris 3, header baris 4.
    pso_idx = KOLOM.index("PSO") + 2
    total2_idx = KOLOM.index("Total2") + 2
    ws.merge_range(2, pso_idx, 2, KOLOM.index("Total") + 2, "Volume (KL) / Month", group)
    ws.merge_range(2, KOLOM.index("PSO2") + 2, 2, total2_idx, "Transaksi / Month", group)

    widths = {
        "No SPBU": 12,
        "Kode Lahan": 18,
        "Nama Perusahaan": 32,
        "Nama Tenant": 30,
        "Region": 14,
        "Provinsi": 20,
        "Kota/Kab": 20,
        "Kecamatan": 22,
        "Desa/Kelurahan": 22,
        "Alamat": 60,
        "Tipe SPBU": 10,
        "Kelas SPBU": 12,
        "Luas (M2)": 12,
        "Tanggal Mulai Sewa": 16,
        "Tanggal Berakhir Sewa": 16,
        "Harga (Rp)": 16,
        "Harga Sewa (Rp)": 16,
        "Latitude": 14,
        "Longitude": 14,
        "Road Type": 24,
        "SES": 45,
        "Red Ocean": 50,
        "Blue Ocean": 50,
        "Status Sewa": 14,
        "Green Energy Station (GES)": 24,
        "Fasilitas EV": 22,
        "PSO": 12,
        "Non PSO": 12,
        "Total": 12,
        "PSO2": 12,
        "Non PSO2": 12,
        "Total2": 10,
    }
    for idx, nama in enumerate(KOLOM):
        ws.write(3, idx + 2, nama, header)
        ws.set_column(idx + 2, idx + 2, widths.get(nama, 14))

    for i, row in enumerate(tabel.itertuples(index=False), start=4):
        for j, value in enumerate(row):
            nama = KOLOM[j]
            col = j + 2
            if pd.isna(value):
                ws.write_blank(i, col, None, body)
            elif nama in ("Tanggal Mulai Sewa", "Tanggal Berakhir Sewa"):
                ws.write_datetime(i, col, pd.Timestamp(value).to_pydatetime(), date_fmt)
            elif nama in ("Harga (Rp)", "Harga Sewa (Rp)"):
                ws.write_number(i, col, float(value), money_fmt)
            elif nama in ("Latitude", "Longitude"):
                ws.write_number(i, col, float(value), coord_fmt)
            elif nama in ("PSO", "Non PSO", "Total", "PSO2", "Non PSO2", "Total2", "Luas (M2)"):
                ws.write_number(i, col, float(value), decimal_fmt)
            else:
                ws.write_string(i, col, str(value), body)

    last_row = 4 + len(tabel) - 1
    ws.freeze_panes(4, 3)
    ws.autofilter(3, 2, last_row, len(KOLOM) + 1)

    # OR_Lahan pivot.
    p_header = wb.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#0070C0",
            "border": 1,
            "border_color": "#BFBFBF",
            "align": "center",
        }
    )
    p_body = wb.add_format({"border": 1, "border_color": "#D9D9D9"})
    p_total = wb.add_format(
        {"bold": True, "border": 1, "border_color": "#BFBFBF", "bg_color": "#D9E1F2"}
    )
    p_pct = wb.add_format(
        {"num_format": "0.00%", "border": 1, "border_color": "#D9D9D9"}
    )
    p_pct_total = wb.add_format(
        {
            "num_format": "0.00%",
            "bold": True,
            "border": 1,
            "border_color": "#BFBFBF",
            "bg_color": "#D9E1F2",
        }
    )

    ws2.write(0, 0, "Count of Status Sewa", p_header)
    ws2.write(0, 1, "Status Sewa", p_header)
    for j, nama in enumerate(("Region", "Tersedia", "Tersewa", "Grand Total", "Occupancy Rate")):
        ws2.write(1, j, nama, p_header)
    for i, (region, row) in enumerate(pivot.iterrows(), start=2):
        ws2.write(i, 0, region, p_body)
        ws2.write_number(i, 1, int(row["Tersedia"]), p_body)
        ws2.write_number(i, 2, int(row["Tersewa"]), p_body)
        ws2.write_number(i, 3, int(row["Grand Total"]), p_body)
        ws2.write_number(i, 4, float(row["Occupancy Rate"]), p_pct)
    total_row = 2 + len(pivot)
    ws2.write(total_row, 0, "Grand Total", p_total)
    ws2.write_number(total_row, 1, int(pivot["Tersedia"].sum()), p_total)
    ws2.write_number(total_row, 2, int(pivot["Tersewa"].sum()), p_total)
    ws2.write_number(total_row, 3, int(pivot["Grand Total"].sum()), p_total)
    ws2.write_number(
        total_row,
        4,
        float(pivot["Tersewa"].sum()) / max(int(pivot["Grand Total"].sum()), 1),
        p_pct_total,
    )
    ws2.set_column(0, 0, 20)
    ws2.set_column(1, 3, 14)
    ws2.set_column(4, 4, 18)

    # Info.
    info_title = wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F4E78"})
    info_bold = wb.add_format({"bold": True})
    ws3.set_column(0, 0, 26)
    ws3.set_column(1, 1, 90)
    ws3.write("A1", "NFR OCCUPANCY PER SPBU", info_title)
    info = [
        ("Sumber", "Master Lahan + Izin Prinsip + Sewa Lahan + Ketersediaan Lahan + BVT + List Lembaga Penyalur"),
        ("Cakupan", f"{len(tabel):,} baris lahan; {tabel['No SPBU'].nunique():,} SPBU Reguler yang memiliki lahan".replace(",", ".")),
        ("SPBU Reguler", "6.525 SPBU (filter Jenis Lembaga Penyalur = SPBU Reguler)"),
        ("Status Sewa", "Tersedia + Tersewa (seluruh baris Master Lahan yang berstatus aktif)"),
        ("Verifikasi Tersewa", "Aktif di Sewa Lahan/Izin Prinsip sudah tercakup sebagai Tersewa di Master Lahan; 1 SPBU (3445602) masih Tersedia di master meski izinnya Beroperasi"),
        ("Pivot OR_Lahan", "Count Status Sewa per Region + Occupancy Rate = Tersewa / Grand Total"),
        ("Catatan volume", "PSO/Non PSO/Transaksi hanya tersedia untuk SPBU yang ada di file Ketersediaan Lahan"),
        ("Catatan GES/EV", "Tidak tersedia di file sanitized; ditandai Tidak Diketahui"),
        ("Catatan region", "Region kosong/Tidak diketahui diisi dari provinsi SPBU (master), lalu dipetakan ke 8 region"),
    ]
    for i, (k, v) in enumerate(info, start=3):
        ws3.write(i, 0, k, info_bold)
        ws3.write(i, 1, v)

    wb.close()
    return buffer.getvalue()
