"""Logika analisis lintas dataset: lead time, lahan, dan sewa lahan."""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- Pemetaan status ke tahapan ---------------------------------------------
STAGE_MAP: dict[str, str] = {
    "Menunggu Verifikasi SBM": "Verifikasi Dokumen",
    "Menunggu Verifikasi SAM": "Verifikasi Dokumen",
    "Menunggu Verifikasi MS3": "Verifikasi MS3",
    "Menunggu Verifikasi": "Management Fee",
    "Menunggu Pembayaran": "Management Fee",
    "Input Nominal": "Management Fee",
    "Revisi Pembayaran": "Management Fee",
    "Verifikasi Pembayaran": "Pembayaran Invoice",
    "Terbit": "Penerbitan Izin Prinsip",
    "Beroperasi": "Selesai (Beroperasi)",
    "Telah Berakhir": "Selesai (Telah Berakhir)",
    "Kadaluarsa": "Selesai (Kadaluarsa)",
    "Ditolak": "Ditolak",
    "Dibatalkan": "Dibatalkan",
    "Draft Izin prinsip": "Draft",
}

TAHAPAN_ORDER = (
    "Verifikasi Dokumen",
    "Verifikasi MS3",
    "Management Fee",
    "Persetujuan Prinsip",
)

PENDING_STATUSES = (
    "Menunggu Verifikasi SBM",
    "Menunggu Verifikasi SAM",
    "Menunggu Verifikasi MS3",
    "Menunggu Verifikasi",
    "Menunggu Pembayaran",
    "Input Nominal",
    "Revisi Pembayaran",
    "Verifikasi Pembayaran",
)
ISSUED_STATUSES = ("Terbit", "Beroperasi")
REJECTED_STATUSES = ("Ditolak", "Dibatalkan")
DRAFT_STATUSES = ("Draft Izin prinsip",)


def snapshot_date(izin: pd.DataFrame) -> pd.Timestamp:
    """Tanggal potret data: pengajuan terakhir di dataset."""
    terakhir = izin["Tgl Pengajuan"].max()
    if pd.isna(terakhir):
        return pd.Timestamp.today().normalize()
    return pd.Timestamp(terakhir).normalize()


def classify_status(status: str) -> str:
    if pd.isna(status):
        return "Lainnya"
    if status in PENDING_STATUSES:
        return "Pending"
    if status in ("Beroperasi", "Terbit"):
        return "Terbit / Beroperasi"
    if status == "Telah Berakhir":
        return "Telah Berakhir"
    if status in REJECTED_STATUSES:
        return "Ditolak / Batal"
    if status in DRAFT_STATUSES:
        return "Draft"
    return "Lainnya"


def prepare_leadtime(izin: pd.DataFrame, snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    """Tambahkan kolom turunan untuk analisis lead time dan aging."""
    df = izin.copy()
    snap = snapshot or snapshot_date(df)

    df["Tahap"] = df["Status"].map(STAGE_MAP).fillna("Lainnya")
    df["Kelompok"] = df["Status"].map(classify_status)

    umur = (snap - df["Tgl Pengajuan"]).dt.total_seconds() / 86_400
    df["Umur Pengajuan (hari)"] = umur.round(1)

    batas = df["Batas"]
    df["Sisa Hari"] = (batas - snap).dt.days
    df["Overdue (hari)"] = (-df["Sisa Hari"]).clip(lower=0).fillna(0)
    df["Lewat Batas"] = (df["Sisa Hari"] < 0) & batas.notna()

    df["Snapshot"] = snap
    return df


def leadtime_funnel(ldf: pd.DataFrame) -> pd.DataFrame:
    """Ringkasan posisi tiap tahapan pada saat snapshot."""
    grouped = (
        ldf.groupby("Tahapan")
        .agg(
            **{
                "Jumlah Baris": ("ID Pengajuan", "size"),
                "Izin Unik": ("ID Pengajuan", "nunique"),
                "Pending": ("Kelompok", lambda s: int((s == "Pending").sum())),
                "Terbit / Beroperasi": (
                    "Kelompok",
                    lambda s: int((s == "Terbit / Beroperasi").sum()),
                ),
                "Telah Berakhir": ("Kelompok", lambda s: int((s == "Telah Berakhir").sum())),
                "Ditolak / Batal": (
                    "Kelompok",
                    lambda s: int((s == "Ditolak / Batal").sum()),
                ),
            }
        )
        .reindex(TAHAPAN_ORDER)
        .reset_index()
    )
    total = grouped["Jumlah Baris"].replace(0, np.nan)
    grouped["% Pending"] = (grouped["Pending"] / total * 100).round(1)
    return grouped


def leadtime_aging(ldf: pd.DataFrame) -> pd.DataFrame:
    """Aging pengajuan yang masih pending, dikelompokkan per status tahapan."""
    pending = ldf[ldf["Kelompok"] == "Pending"]
    if pending.empty:
        return pd.DataFrame()

    grouped = (
        pending.groupby(["Tahap", "Status"], observed=True)
        .agg(
            **{
                "Jumlah": ("ID Pengajuan", "size"),
                "Izin Unik": ("ID Pengajuan", "nunique"),
                "Rerata Umur (hari)": ("Umur Pengajuan (hari)", "mean"),
                "Median Umur (hari)": ("Umur Pengajuan (hari)", "median"),
                "P90 Umur (hari)": ("Umur Pengajuan (hari)", lambda s: s.quantile(0.9)),
                "Umur Terlama (hari)": ("Umur Pengajuan (hari)", "max"),
                "SLA Target (hari)": ("SLA", "median"),
                "Lewat Batas": ("Lewat Batas", "sum"),
            }
        )
        .reset_index()
    )
    grouped["% Lewat Batas"] = (
        grouped["Lewat Batas"] / grouped["Jumlah"].replace(0, np.nan) * 100
    ).round(1)

    urutan = (
        grouped.groupby("Tahap")["Median Umur (hari)"]
        .median()
        .reindex([t for t in TAHAPAN_ORDER])
        .dropna()
        .index
        .tolist()
    )
    grouped["_tahap"] = pd.Categorical(grouped["Tahap"], categories=urutan, ordered=True)
    return grouped.sort_values(["_tahap", "Median Umur (hari)"], ascending=[True, False]).drop(
        columns="_tahap"
    )


def leadtime_stage_summary(ldf: pd.DataFrame) -> pd.DataFrame:
    """Ringkas aging per tahapan (gabungan seluruh status pending di tahap itu)."""
    pending = ldf[ldf["Kelompok"] == "Pending"]
    if pending.empty:
        return pd.DataFrame()

    grouped = (
        pending.groupby("Tahap", observed=True)
        .agg(
            **{
                "Jumlah Pending": ("ID Pengajuan", "size"),
                "Izin Unik": ("ID Pengajuan", "nunique"),
                "Rerata Umur (hari)": ("Umur Pengajuan (hari)", "mean"),
                "Median Umur (hari)": ("Umur Pengajuan (hari)", "median"),
                "P90 Umur (hari)": ("Umur Pengajuan (hari)", lambda s: s.quantile(0.9)),
                "Umur Terlama (hari)": ("Umur Pengajuan (hari)", "max"),
                "Lewat Batas": ("Lewat Batas", "sum"),
            }
        )
        .reset_index()
    )
    grouped["% Lewat Batas"] = (
        grouped["Lewat Batas"] / grouped["Jumlah Pending"].replace(0, np.nan) * 100
    ).round(1)
    for col in ("Rerata Umur (hari)", "Median Umur (hari)", "P90 Umur (hari)", "Umur Terlama (hari)"):
        grouped[col] = grouped[col].round(1)
    return grouped.sort_values("Median Umur (hari)", ascending=False)


def leadtime_quality(ldf: pd.DataFrame) -> pd.DataFrame:
    """Temuan kualitas data yang memengaruhi perhitungan lead time."""
    dup_mask = ldf.duplicated("ID Pengajuan", keep=False)
    baris = [
        ("Total baris dataset", len(ldf)),
        ("ID pengajuan unik", ldf["ID Pengajuan"].nunique()),
        ("Baris dengan ID duplikat", int(dup_mask.sum())),
        ("Izin tanpa Tgl Berakhir Izin Prinsip", int(ldf["Tgl Berakhir Izin Prinsip"].isna().sum())),
        ("Baris punya Batas/SLA", int(ldf["Batas"].notna().sum())),
        ("Total sewa bernilai 0", int((ldf["Total Harga Sewa"] == 0).sum())),
        ("SLA bernilai 0", int((ldf["SLA"] == 0).sum())),
    ]
    return pd.DataFrame(baris, columns=["Metrik", "Nilai"])


def pending_by_region(ldf: pd.DataFrame) -> pd.DataFrame:
    pending = ldf[ldf["Kelompok"] == "Pending"]
    if pending.empty:
        return pd.DataFrame()
    pivot = pd.crosstab(pending["Region"], pending["Tahap"])
    pivot["TOTAL"] = pivot.sum(axis=1)
    return pivot.sort_values("TOTAL", ascending=False).reset_index()


def oldest_pending(ldf: pd.DataFrame, limit: int = 50) -> pd.DataFrame:
    cols = [
        "ID Pengajuan",
        "No. SPBU",
        "Region",
        "Nama Tenant",
        "Nama Brand",
        "Kategori",
        "Tahap",
        "Status",
        "Tgl Pengajuan",
        "Umur Pengajuan (hari)",
        "SLA",
        "Batas",
        "Overdue (hari)",
    ]
    pending = ldf[ldf["Kelompok"] == "Pending"].sort_values(
        "Umur Pengajuan (hari)", ascending=False
    )
    return pending.loc[:, [c for c in cols if c in pending.columns]].head(limit)


# --- Lahan & sewa ------------------------------------------------------------
def spbu_region_map(izin: pd.DataFrame) -> pd.DataFrame:
    """Peta No. SPBU -> Region/Provinsi/Kab-Kota dari dataset pengajuan."""
    kolom = ["No. SPBU", "Region", "Provinsi", "Kab./Kota"]
    peta = izin.loc[:, kolom].dropna(subset=["No. SPBU"]).drop_duplicates("No. SPBU")
    return peta.set_index("No. SPBU")


def attach_region(df: pd.DataFrame, izin: pd.DataFrame) -> pd.DataFrame:
    peta = spbu_region_map(izin)
    hasil = df.merge(peta, left_on="No. SPBU", right_index=True, how="left")
    for col in ("Region", "Provinsi", "Kab./Kota"):
        hasil[col] = hasil[col].fillna("Tidak diketahui")
    return hasil


def prepare_lahan(lahan: pd.DataFrame, izin: pd.DataFrame) -> pd.DataFrame:
    df = attach_region(lahan, izin)
    df["Status Sewa"] = df["Status Sewa"].replace({" - ": "Tidak Diketahui"})
    df["Tersewa"] = df["Status Sewa"].eq("Tersewa")
    df["Tersedia"] = df["Status Sewa"].eq("Tersedia")
    return df


def prepare_sewa(sewa: pd.DataFrame, izin: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    df = attach_region(sewa, izin)
    df["Sisa Hari"] = (df["Tanggal Berakhir Sewa"] - snapshot).dt.days
    df["Berjalan"] = df["Status Sewa"].eq("Berjalan")
    df["Kategori Utama"] = (
        df["Kategori/Sub Kategori"].astype("string").str.split("/").str[0].str.strip()
    )
    df["Berakhir Bulan"] = df["Tanggal Berakhir Sewa"].dt.to_period("M").dt.to_timestamp()
    return df


def lahan_ringkasan(lahan: pd.DataFrame) -> pd.DataFrame:
    """Agregasi lahan per region: tersewa, tersedia, occupancy, nilai sewa."""
    grouped = (
        lahan.groupby("Region")
        .agg(
            **{
                "Jumlah Lahan": ("Kode Lahan", "size"),
                "Tersewa": ("Tersewa", "sum"),
                "Tersedia": ("Tersedia", "sum"),
                "Luas (M2)": ("Luas (M2)", "sum"),
                "Nilai Sewa (Rp)": ("Harga Sewa (Rp)", "sum"),
            }
        )
        .reset_index()
    )
    dasar = (grouped["Tersewa"] + grouped["Tersedia"]).replace(0, np.nan)
    grouped["Occupancy (%)"] = (grouped["Tersewa"] / dasar * 100).round(1)
    return grouped.sort_values("Nilai Sewa (Rp)", ascending=False)


def sewa_ringkasan(sewa: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        sewa.groupby("Region")
        .agg(
            **{
                "Kontrak": ("No. SPBU", "size"),
                "Berjalan": ("Berjalan", "sum"),
                "Tenant Unik": ("Nama Tenant", "nunique"),
                "Nilai Sewa (Rp)": ("Total Harga Sewa", "sum"),
                "Berakhir ≤90 Hari": ("Sisa Hari", lambda s: int(((s >= 0) & (s <= 90)).sum())),
            }
        )
        .reset_index()
    )
    return grouped.sort_values("Nilai Sewa (Rp)", ascending=False)
