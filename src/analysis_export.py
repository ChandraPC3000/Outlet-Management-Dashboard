"""Ekspor analisis lengkap (multi-sheet) untuk Data Web Kemitraan, Brightspace, dan pembanding."""

from __future__ import annotations

import pandas as pd

from src.brightspace import ringkasan_brightspace
from src.excel_export import build_workbook
from src.web_kemitraan import ringkasan_web_kemitraan


def build_web_kemitraan_excel(df: pd.DataFrame, info: dict | None = None) -> bytes:
    info = info or ringkasan_web_kemitraan(df)

    ringkasan = pd.DataFrame(
        [
            ("Jumlah SPBU", info["spbu"]),
            ("Lahan terdaftar", info["total_lahan"]),
            ("Tersewa NFR aktif", info["tersewa"]),
            ("Lahan vacant", info["vacant"]),
            ("Occupancy (%)", round(info["occupancy"], 2)),
            ("Vacancy (%)", round(info["vacancy_rate"], 2)),
            ("Kode lahan unik", info["kode_unik"]),
            ("Total luas (m²)", info["total_luas"]),
            ("Median luas (m²)", info["median_luas"]),
            ("Tenant terbanyak", info["top_tenant"]),
            ("Lahan tenant terbanyak", info["top_tenant_count"]),
        ],
        columns=["Metrik", "Nilai"],
    )

    status = (
        df["Status"].value_counts().rename_axis("Status").reset_index(name="Jumlah")
    )
    status["Persentase"] = (status["Jumlah"] / len(df) * 100).round(2)

    per_provinsi = (
        df.groupby(["Provinsi", "Status"]).size().unstack(fill_value=0).reset_index()
    )
    per_provinsi["Total"] = per_provinsi.drop(columns=["Provinsi"]).sum(axis=1)
    per_provinsi = per_provinsi.sort_values("Total", ascending=False)

    tenant = df.loc[df["Tenant NFR"].ne("Tidak diketahui"), "Tenant NFR"]
    tenant = tenant.str.split("; ").explode().str.strip()
    tenant = tenant[tenant.ne("") & tenant.ne("-")]
    top_tenant = (
        tenant.value_counts()
        .head(50)
        .rename_axis("Tenant/Brand")
        .reset_index(name="Jumlah")
    )

    data = df[
        [
            "No SPBU",
            "Kode Lahan",
            "Tenant NFR",
            "Provinsi",
            "Kota/Kab",
            "Luas (M2)",
            "Latitude",
            "Longitude",
            "Status Sewa",
        ]
    ].rename(columns={"Luas (M2)": "Luas (m²)"})

    return build_workbook(
        {
            "Ringkasan": ringkasan,
            "Data": data,
            "Per Status": status,
            "Per Provinsi": per_provinsi,
            "Top Tenant": top_tenant,
        }
    )


def build_brightspace_excel(
    df: pd.DataFrame,
    summary: dict | None = None,
    info: dict | None = None,
) -> bytes:
    info = info or ringkasan_brightspace(df, summary or {})

    ringkasan = pd.DataFrame(
        [
            ("Jumlah SPBU", info["spbu"]),
            ("Lahan terdaftar", info["total_lahan"]),
            ("Tersewa NFR aktif", info["tersewa"]),
            ("Lahan vacant", info["vacant"]),
            ("Occupancy (%)", round(info["occupancy"], 2)),
            ("Vacancy (%)", round(info["vacancy_rate"], 2)),
            ("Total luas (m²)", info["total_luas"]),
            ("Median luas (m²)", info["median_luas"]),
            ("Brand terbanyak", info["top_brand"]),
            ("Lahan brand terbanyak", info["top_brand_count"]),
            ("Baris detail", info["total_detail"]),
            ("Tersewa (detail)", info["tersewa_detail"]),
            ("Vacant (detail)", info["vacant_detail"]),
        ],
        columns=["Metrik", "Nilai"],
    )

    status = (
        df["Status"].value_counts().rename_axis("Status").reset_index(name="Jumlah")
    )
    status["Persentase"] = (status["Jumlah"] / len(df) * 100).round(2)

    posisi = (
        df.groupby(["PosisiLahan_Description", "Status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    posisi["Total"] = posisi.drop(columns=["PosisiLahan_Description"]).sum(axis=1)

    brand = (
        df.loc[df["BrandName"].ne("Tidak diketahui"), "BrandName"]
        .value_counts()
        .head(50)
        .rename_axis("Brand/Tenant")
        .reset_index(name="Jumlah")
    )

    data = df[
        [
            "IdAgent_FK",
            "LandCode",
            "BrandName",
            "LandArea",
            "PosisiLahan_Description",
            "RentalPeriodName",
            "Lat",
            "Lng",
            "Status",
            "LandDescription",
        ]
    ].rename(
        columns={
            "IdAgent_FK": "ID Agent",
            "LandCode": "Kode Lahan",
            "BrandName": "Brand/Tenant",
            "LandArea": "Luas (m²)",
            "PosisiLahan_Description": "Posisi Lahan",
            "RentalPeriodName": "Periode Sewa",
            "LandDescription": "Keterangan",
        }
    )

    return build_workbook(
        {
            "Ringkasan": ringkasan,
            "Data": data,
            "Per Status": status,
            "Posisi Lahan": posisi,
            "Top Brand": brand,
        }
    )


def spbu_nfr_stats(
    web: pd.DataFrame,
    bright: pd.DataFrame,
    universe_ids: set[str] | None = None,
) -> dict:
    """Hitung SPBU tanpa NFR aktif/data terhadap universe SPBU (6.594)."""
    if universe_ids is None:
        from src.spbu_universe import load_spbu_universe

        universe_ids = set(load_spbu_universe()["No. SPBU"].astype(str))
    total = len(universe_ids)

    web_ids = set(web["No SPBU"].dropna().astype(str)) & universe_ids
    web_aktif = (
        set(web.loc[web["Status Sewa"].eq("Tersewa"), "No SPBU"].dropna().astype(str))
        & universe_ids
    )

    bright_prefix = (
        bright["LandCode"].dropna().astype(str).str.split("-").str[0].str.strip()
    )
    bright_ids = set(bright_prefix) & universe_ids
    bright_aktif = (
        set(
            bright.loc[bright["RentStatName"].eq("Tersewa"), "LandCode"]
            .dropna()
            .astype(str)
            .str.split("-")
            .str[0]
            .str.strip()
        )
        & universe_ids
    )

    return {
        "universe": total,
        "web_tanpa_aktif": total - len(web_aktif),
        "bright_tanpa_aktif": total - len(bright_aktif),
        "web_tanpa_data": total - len(web_ids),
        "bright_tanpa_data": total - bright["IdAgent_FK"].nunique(),
    }


def build_banding_excel(
    web: pd.DataFrame,
    bright: pd.DataFrame,
    web_info: dict | None = None,
    bright_info: dict | None = None,
    universe_total: int = 6594,
    universe_ids: set[str] | None = None,
) -> bytes:
    web_info = web_info or ringkasan_web_kemitraan(web)
    bright_info = bright_info or ringkasan_brightspace(bright, {})

    spbu_stats = spbu_nfr_stats(web, bright, universe_ids)

    comp = pd.DataFrame(
        [
            ("Jumlah SPBU", web_info["spbu"], bright_info["spbu"]),
            ("Lahan terdaftar", web_info["total_lahan"], bright_info["total_lahan"]),
            ("Tersewa NFR aktif", web_info["tersewa"], bright_info["tersewa"]),
            ("Lahan vacant", web_info["vacant"], bright_info["vacant"]),
            (
                "SPBU tanpa NFR aktif",
                spbu_stats["web_tanpa_aktif"],
                spbu_stats["bright_tanpa_aktif"],
            ),
            (
                "SPBU tanpa data NFR",
                spbu_stats["web_tanpa_data"],
                spbu_stats["bright_tanpa_data"],
            ),
        ],
        columns=["Metrik", "Web Kemitraan", "Brightspace"],
    )
    comp["Selisih (Bright - Web)"] = comp["Brightspace"] - comp["Web Kemitraan"]
    comp["Bright vs Web (%)"] = (
        comp["Brightspace"] / comp["Web Kemitraan"] * 100
    ).round(1)
    definisi = {
        "Jumlah SPBU": "SPBU unik yang punya data lahan di sumber.",
        "Lahan terdaftar": "Jumlah baris lahan (row-level), termasuk multi-tenant/duplikat.",
        "Tersewa NFR aktif": "Baris dengan Status Sewa = Tersewa.",
        "Lahan vacant": "Baris dengan Status Sewa = Tersedia; bukan ukuran fisik kosong.",
        "SPBU tanpa NFR aktif": "SPBU universe yang tidak punya minimal 1 lahan Tersewa; termasuk SPBU tanpa data.",
        "SPBU tanpa data NFR": "SPBU universe yang tidak muncul di sumber (tidak punya baris lahan).",
    }
    comp["Definisi"] = comp["Metrik"].map(definisi)

    metodologi = pd.DataFrame(
        [
            ("Definisi", "Penjelasan"),
            ("Universe SPBU", "6.594 SPBU = 6.525 SPBU Reguler + 69 SPBU existing di luar Reguler."),
            ("Jumlah SPBU", "SPBU unik yang punya data lahan di sumber. Web: No SPBU; Brightspace: IdAgent_FK."),
            ("Lahan terdaftar", "Jumlah baris lahan (row-level), termasuk multi-tenant/duplikat. Bukan jumlah bidang tanah unik."),
            ("Tersewa NFR aktif", "Baris dengan Status Sewa = Tersewa."),
            ("Lahan vacant", "Baris dengan Status Sewa = Tersedia. Status administratif, bukan ukuran fisik lahan kosong."),
            ("SPBU tanpa NFR aktif", "SPBU universe yang tidak punya minimal 1 lahan Tersewa. Termasuk SPBU tanpa data lahan."),
            ("SPBU tanpa data NFR", "SPBU universe yang tidak muncul di sumber (tidak punya baris lahan)."),
            ("Basis kecocokan lahan", "Kode Lahan (Web) = LandCode (Brightspace), dideduplikasi per kode."),
            ("Catatan Web", "5.291 dari 5.802 baris Tersedia masih punya string tenant/brand; status Sewa tetap otoritatif."),
            ("Catatan Brightspace", "5.843 agent; 5.842 prefix SPBU cocok ke universe; 1 agent tidak terpetakan. Untuk KPI tanpa data dipakai 6.594 - 5.843 = 751."),
            ("Basis KPI vs kecocokan", "Ringkasan KPI memakai basis baris; sheet Kecocokan Lahan memakai basis kode unik. Jangan dicampur saat menyimpulkan."),
        ],
        columns=["Definisi", "Penjelasan"],
    )

    web_u = web.drop_duplicates("Kode Lahan")[
        ["Kode Lahan", "No SPBU", "Status Sewa"]
    ].copy()
    bright_u = bright.drop_duplicates("LandCode")[
        ["LandCode", "IdAgent_FK", "RentStatName"]
    ].copy()

    match = web_u.merge(
        bright_u,
        left_on="Kode Lahan",
        right_on="LandCode",
        how="outer",
        indicator=True,
    )
    match["Kategori"] = "Cocok - status sama"
    both = match["_merge"] == "both"
    match.loc[both & (match["Status Sewa"] != match["RentStatName"]), "Kategori"] = (
        "Cocok - status berbeda"
    )
    match.loc[match["_merge"] == "left_only", "Kategori"] = "Hanya Web Kemitraan"
    match.loc[match["_merge"] == "right_only", "Kategori"] = "Hanya Brightspace"

    kategori = (
        match["Kategori"]
        .value_counts()
        .rename_axis("Kategori")
        .reset_index(name="Jumlah")
    )
    kategori["Persentase"] = (kategori["Jumlah"] / len(match) * 100).round(2)

    mism = match[both & (match["Status Sewa"] != match["RentStatName"])].copy()
    mism = mism[
        [
            "Kode Lahan",
            "No SPBU",
            "Status Sewa",
            "RentStatName",
            "IdAgent_FK",
        ]
    ].rename(
        columns={
            "No SPBU": "No SPBU (Web)",
            "Status Sewa": "Status Web Kemitraan",
            "RentStatName": "Status Brightspace",
            "IdAgent_FK": "ID Agent (Brightspace)",
        }
    )

    semua = match[
        [
            "Kode Lahan",
            "No SPBU",
            "Status Sewa",
            "IdAgent_FK",
            "RentStatName",
            "Kategori",
        ]
    ].rename(
        columns={
            "No SPBU": "No SPBU (Web)",
            "Status Sewa": "Status Web Kemitraan",
            "IdAgent_FK": "ID Agent (Brightspace)",
            "RentStatName": "Status Brightspace",
        }
    )

    return build_workbook(
        {
            "Ringkasan KPI": comp,
            "Metodologi": metodologi,
            "Kecocokan Lahan": kategori,
            "Status Berbeda": mism,
            "Semua Kode Lahan": semua,
        }
    )
