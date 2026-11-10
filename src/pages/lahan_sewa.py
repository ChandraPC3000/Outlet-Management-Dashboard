"""Halaman Lahan & Sewa: occupancy lahan dan portofolio kontrak sewa."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_all
from src.formatting import format_angka, format_rupiah
from src.map_spbu import render_spbu_map
from src.spbu_universe import brand_types, load_spbu_universe, spbu_ids_for_brands, universe_ringkasan

izin, lahan_mentah, sewa_mentah = load_all()
snapshot = an.snapshot_date(izin)
lahan = an.prepare_lahan(lahan_mentah, izin)
sewa = an.prepare_sewa(sewa_mentah, izin, snapshot)
universe = universe_ringkasan(load_spbu_universe())

st.title("Lahan & Sewa")
st.caption(
    f"Analisis {format_angka(len(lahan))} lahan dan {format_angka(len(sewa))} kontrak sewa "
    f"per snapshot {snapshot:%d %B %Y} · {format_angka(lahan['No. SPBU'].nunique())} SPBU "
    f"dengan lahan · total SPBU Pertamina {format_angka(universe['total'])}."
)

tab_lahan, tab_sewa = st.tabs(["Master Lahan", "Sewa Lahan"])

# ============================================================== MASTER LAHAN
with tab_lahan:
    f1, f2, f3 = st.columns(3)
    region = f1.multiselect(
        "Region", sorted(lahan["Region"].unique()), key="lahan_region"
    )
    status_sewa = f2.multiselect(
        "Status Sewa", sorted(lahan["Status Sewa"].dropna().unique()), key="lahan_status"
    )
    approval = f3.multiselect(
        "Status Approval",
        sorted(lahan["Status Approval"].dropna().unique()),
        key="lahan_approval",
    )

    f4, f5, f6 = st.columns(3)
    status_level = f4.multiselect(
        "Status Level",
        sorted(lahan["Status Level"].dropna().unique()),
        key="lahan_status_level",
    )
    tipe_spbu = f5.multiselect(
        "Tipe SPBU",
        sorted(lahan["Tipe SPBU"].dropna().unique()),
        key="lahan_tipe_spbu",
    )
    brand = f6.multiselect(
        "Tipe Brand (tenant SPBU)",
        brand_types(),
        key="lahan_brand",
        help="Memfilter SPBU yang memiliki tenant dengan tipe brand tersebut.",
    )

    tampil = lahan
    if region:
        tampil = tampil[tampil["Region"].isin(region)]
    if status_sewa:
        tampil = tampil[tampil["Status Sewa"].isin(status_sewa)]
    if approval:
        tampil = tampil[tampil["Status Approval"].isin(approval)]
    if status_level:
        tampil = tampil[tampil["Status Level"].isin(status_level)]
    if tipe_spbu:
        tampil = tampil[tampil["Tipe SPBU"].isin(tipe_spbu)]
    if brand:
        tampil = tampil[tampil["No. SPBU"].isin(spbu_ids_for_brands(brand))]

    if tampil.empty:
        st.warning("Tidak ada lahan yang cocok dengan filter.")
        st.stop()

    tersewa = int(tampil["Tersewa"].sum())
    tersedia = int(tampil["Tersedia"].sum())
    dasar = tersewa + tersedia
    occupancy = tersewa / dasar * 100 if dasar else 0

    kpi = st.columns(4)
    kpi[0].metric("Total Lahan", format_angka(len(tampil)))
    kpi[1].metric("Tersewa", f"{format_angka(tersewa)} lahan")
    kpi[2].metric("Tersedia", f"{format_angka(tersedia)} lahan")
    kpi[3].metric("Occupancy", f"{format_angka(occupancy, 1)}%")
    kpi2 = st.columns(2)
    kpi2[0].metric("Luas Total", f"{format_angka(tampil['Luas (M2)'].sum())} m²")
    kpi2[1].metric("Nilai Sewa Lahan", format_rupiah(tampil["Harga Sewa (Rp)"].sum()))

    st.subheader("Peta Lahan")
    st.caption("Warna titik = Tipe SPBU.")
    render_spbu_map(tampil, color_col="Tipe SPBU", region_col="Region", height=460)

    st.divider()

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Tersewa vs Tersedia per Region")
        st.plotly_chart(
            charts.occupancy_region(an.lahan_ringkasan(tampil)), use_container_width=True
        )
    with kanan:
        st.subheader("Status Approval Lahan")
        st.plotly_chart(charts.approval_lahan(tampil), use_container_width=True)

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Top 10 Tenant by Nilai Sewa")
        st.plotly_chart(charts.top_tenant_sewa(tampil), use_container_width=True)
    with kanan:
        st.subheader("Luas vs Nilai Sewa")
        st.plotly_chart(charts.scatter_luas_sewa(tampil), use_container_width=True)

    st.subheader("Detail Lahan")
    kolom = [
        "No. SPBU",
        "Region",
        "Kode Lahan",
        "Luas (M2)",
        "Tenant",
        "Status Sewa",
        "Status Approval",
        "Tanggal Mulai Sewa",
        "Tanggal Berakhir Sewa",
        "Harga Sewa (Rp)",
    ]
    tabel = tampil.loc[:, [k for k in kolom if k in tampil.columns]].sort_values(
        "Harga Sewa (Rp)", ascending=False
    )
    st.dataframe(
        tabel,
        hide_index=True,
        use_container_width=True,
        height=420,
        column_config={
            "Luas (M2)": st.column_config.NumberColumn("Luas (m²)", format="%.0f"),
            "Harga Sewa (Rp)": st.column_config.NumberColumn("Harga Sewa (Rp)", format="%.0f"),
            "Tanggal Mulai Sewa": st.column_config.DateColumn(
                "Mulai Sewa", format="DD/MM/YYYY"
            ),
            "Tanggal Berakhir Sewa": st.column_config.DateColumn(
                "Berakhir Sewa", format="DD/MM/YYYY"
            ),
        },
    )
    st.download_button(
        "Unduh data lahan (CSV)",
        data=tabel.to_csv(index=False).encode("utf-8-sig"),
        file_name="nfr_master_lahan.csv",
        mime="text/csv",
        use_container_width=True,
        key="unduh_lahan",
    )


# =============================================================== SEWA LAHAN
with tab_sewa:
    f1, f2, f3, f4 = st.columns(4)
    region_s = f1.multiselect(
        "Region", sorted(sewa["Region"].unique()), key="sewa_region"
    )
    status_s = f2.multiselect(
        "Status Sewa", sorted(sewa["Status Sewa"].dropna().unique()), key="sewa_status"
    )
    izin_s = f3.multiselect(
        "Status Izin Prinsip",
        sorted(sewa["Status Izin Prinsip"].dropna().unique()),
        key="sewa_izin",
    )
    kategori_s = f4.multiselect(
        "Kategori",
        sorted(sewa["Kategori Utama"].dropna().unique()),
        key="sewa_kategori",
    )

    f5, f6, f7 = st.columns(3)
    status_level_s = f5.multiselect(
        "Status Level",
        sorted(sewa["Status Level"].dropna().unique()),
        key="sewa_status_level",
    )
    tipe_spbu_s = f6.multiselect(
        "Tipe SPBU",
        sorted(sewa["Tipe SPBU"].dropna().unique()),
        key="sewa_tipe_spbu",
    )
    brand_s = f7.multiselect(
        "Tipe Brand",
        sorted(sewa["Jenis Brand"].dropna().unique()),
        key="sewa_brand",
    )

    tampil_s = sewa
    if region_s:
        tampil_s = tampil_s[tampil_s["Region"].isin(region_s)]
    if status_s:
        tampil_s = tampil_s[tampil_s["Status Sewa"].isin(status_s)]
    if izin_s:
        tampil_s = tampil_s[tampil_s["Status Izin Prinsip"].isin(izin_s)]
    if kategori_s:
        tampil_s = tampil_s[tampil_s["Kategori Utama"].isin(kategori_s)]
    if status_level_s:
        tampil_s = tampil_s[tampil_s["Status Level"].isin(status_level_s)]
    if tipe_spbu_s:
        tampil_s = tampil_s[tampil_s["Tipe SPBU"].isin(tipe_spbu_s)]
    if brand_s:
        tampil_s = tampil_s[tampil_s["Jenis Brand"].isin(brand_s)]

    if tampil_s.empty:
        st.warning("Tidak ada kontrak sewa yang cocok dengan filter.")
        st.stop()

    berjalan = tampil_s[tampil_s["Berjalan"]]
    segera = tampil_s[(tampil_s["Sisa Hari"] >= 0) & (tampil_s["Sisa Hari"] <= 90)]

    kpi = st.columns(4)
    kpi[0].metric("Jumlah Kontrak", format_angka(len(tampil_s)))
    kpi[1].metric("Kontrak Berjalan", format_angka(len(berjalan)))
    kpi[2].metric("Berakhir ≤90 Hari", format_angka(len(segera)))
    kpi[3].metric("Nilai Sewa", format_rupiah(tampil_s["Total Harga Sewa"].sum()))

    st.subheader("Peta Kontrak Sewa")
    st.caption("Warna titik = Tipe SPBU.")
    render_spbu_map(tampil_s, color_col="Tipe SPBU", region_col="Region", height=460)

    st.divider()

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Status Kontrak")
        st.plotly_chart(charts.sewa_status_donut(tampil_s), use_container_width=True)
    with kanan:
        st.subheader("Jadwal Berakhir 12 Bulan")
        st.plotly_chart(charts.expiry_timeline(tampil_s, snapshot), use_container_width=True)

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Nilai Sewa per Kategori")
        st.plotly_chart(charts.nilai_kategori_sewa(tampil_s), use_container_width=True)
    with kanan:
        st.subheader("Top 10 Brand by Nilai Sewa")
        st.plotly_chart(charts.top_brand_sewa(tampil_s), use_container_width=True)

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Nilai Sewa per Tipe Brand")
        st.plotly_chart(
            charts.pie_nilai(
                an.sewa_nilai_by(tampil_s, "Jenis Brand"),
                "Jenis Brand",
                "Nilai Sewa (Rp)",
                "Nilai sewa (Rp)",
            ),
            use_container_width=True,
        )
    with kanan:
        st.subheader("Top 10 Sub Kategori")
        st.plotly_chart(
            charts.bar_nilai(
                an.sewa_nilai_by(tampil_s, "Sub Kategori"),
                "Sub Kategori",
                "Nilai Sewa (Rp)",
                "Nilai sewa (Rp)",
                top_n=10,
                warna="#39c5cf",
            ),
            use_container_width=True,
        )

    st.subheader("Detail Kontrak Sewa")
    kolom_s = [
        "No. SPBU",
        "Region",
        "Nama Tenant",
        "Nama Brand",
        "Kategori/Sub Kategori",
        "Status Sewa",
        "Status Izin Prinsip",
        "Tanggal Mulai Sewa",
        "Tanggal Berakhir Sewa",
        "Sisa Hari",
        "Total Harga Sewa",
    ]
    tabel_s = tampil_s.loc[:, [k for k in kolom_s if k in tampil_s.columns]].copy()
    if "Nama Tenant" in tabel_s:
        tabel_s = tabel_s.sort_values(["Status Sewa", "Total Harga Sewa"], ascending=[True, False])
    st.dataframe(
        tabel_s,
        hide_index=True,
        use_container_width=True,
        height=440,
        column_config={
            "Total Harga Sewa": st.column_config.NumberColumn(
                "Total Harga Sewa (Rp)", format="%.0f"
            ),
            "Sisa Hari": st.column_config.NumberColumn("Sisa Hari", format="%d"),
            "Tanggal Mulai Sewa": st.column_config.DateColumn(
                "Mulai Sewa", format="DD/MM/YYYY"
            ),
            "Tanggal Berakhir Sewa": st.column_config.DateColumn(
                "Berakhir Sewa", format="DD/MM/YYYY"
            ),
        },
    )
    st.download_button(
        "Unduh kontrak sewa (CSV)",
        data=tabel_s.to_csv(index=False).encode("utf-8-sig"),
        file_name="nfr_sewa_lahan.csv",
        mime="text/csv",
        use_container_width=True,
        key="unduh_sewa",
    )
