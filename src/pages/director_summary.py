"""Halaman Director Summary: analisis satu SPBU lintas dataset."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_all
from src.filters import SPBU_COLUMN, spbu_selector
from src.formatting import format_angka, format_hari, format_rupiah, format_tanggal
from src.map_spbu import render_spbu_map
from src.spbu_universe import brand_types, spbu_ids_for_brands

izin, lahan_mentah, sewa_mentah = load_all()
snapshot = an.snapshot_date(izin)
ldf = an.prepare_leadtime(izin, snapshot)
lahan = an.prepare_lahan(lahan_mentah, izin)
sewa = an.prepare_sewa(sewa_mentah, izin, snapshot)

st.title("Director Summary")
st.caption("Pilih nomor SPBU di panel filter untuk melihat analisis outlet secara menyeluruh.")

with st.sidebar:
    st.header("Filter Panel")
    status_level = st.multiselect(
        "Status Level",
        sorted(izin["Status Level"].dropna().unique()),
        key="ds_status_level",
    )
    tipe_spbu = st.multiselect(
        "Tipe SPBU",
        sorted(izin["Tipe SPBU"].dropna().unique()),
        key="ds_tipe_spbu",
    )
    brand = st.multiselect(
        "Tipe Brand (tenant SPBU)",
        brand_types(),
        key="ds_brand",
        help="Membatasi pilihan SPBU yang memiliki tenant dengan tipe brand tersebut.",
    )

izin_pilih = izin
if status_level:
    izin_pilih = izin_pilih[izin_pilih["Status Level"].isin(status_level)]
if tipe_spbu:
    izin_pilih = izin_pilih[izin_pilih["Tipe SPBU"].isin(tipe_spbu)]
if brand:
    izin_pilih = izin_pilih[izin_pilih["No. SPBU"].isin(spbu_ids_for_brands(brand))]

selected = spbu_selector(izin_pilih, show_header=False)

if selected is None:
    st.info(
        "Pilih **Nomor SPBU** pada dropdown di sidebar untuk menampilkan analisis "
        "izin prinsip, lahan, sewa, dan lead time outlet tersebut."
    )
    st.subheader("SPBU dengan tenant terbanyak")
    top_spbu = (
        izin_pilih[SPBU_COLUMN]
        .value_counts()
        .head(10)
        .rename_axis("No. SPBU")
        .reset_index(name="Jumlah Tenant")
    )
    st.dataframe(top_spbu, hide_index=True, use_container_width=True)
    st.stop()

data = izin[izin[SPBU_COLUMN] == selected].copy()
info = data.iloc[0]
lahan_spbu = lahan[lahan["No. SPBU"] == selected].copy()
sewa_spbu = sewa[sewa["No. SPBU"] == selected].copy()
lt_spbu = ldf[ldf["No. SPBU"] == selected].copy()

st.header(f"SPBU {selected}")
st.caption(
    f"{info['Region']} · {info['Provinsi']} · {info['Kab./Kota']} — "
    f"{format_angka(len(data))} data izin, {format_angka(len(lahan_spbu))} lahan, "
    f"{format_angka(len(sewa_spbu))} kontrak sewa."
)

st.subheader("Lokasi SPBU")
render_spbu_map(data, color_col="Tipe SPBU", region_col=None, height=380)

tab_izin, tab_lahan, tab_lead, tab_detail = st.tabs(
    ["Izin Prinsip", "Lahan & Sewa", "Lead Time", "Detail"]
)

# ================================================================ IZIN PRINSIP
with tab_izin:
    lokasi = st.columns(3)
    lokasi[0].metric("REGION", info["Region"])
    lokasi[1].metric("PROVINSI", info["Provinsi"])
    lokasi[2].metric("KABUPATEN / KOTA", info["Kab./Kota"])

    kpi = st.columns(4)
    kpi[0].metric("Total Tenant", f"{format_angka(len(data))} unit")
    kpi[1].metric("Total Sewa", format_rupiah(data["Total Harga Sewa"].sum()))
    kpi[2].metric("Rerata SLA", format_hari(data["SLA"].mean()))
    kpi[3].metric("Jumlah Brand", format_angka(data["Nama Brand"].nunique()))

    st.caption(
        f"Pengajuan terakhir: {format_tanggal(data['Tgl Pengajuan'].max())} · "
        f"{format_angka(data['ID Pengajuan'].nunique())} ID pengajuan unik"
    )
    st.divider()

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Sewa per Brand")
        st.plotly_chart(
            charts.sewa_per_brand(data, top_n=min(len(data), 20)),
            use_container_width=True,
        )
        if data["Nama Brand"].nunique() > 20:
            st.caption("Menampilkan 20 brand dengan nilai sewa terbesar.")
    with kanan:
        st.subheader("Status Pengajuan")
        st.plotly_chart(charts.status_donut(data), use_container_width=True)

    st.subheader("Detail Izin Prinsip")
    kolom = [
        "ID Pengajuan",
        "Nama Tenant",
        "Nama Brand",
        "Tipe Brand",
        "Kategori",
        "Total Harga Sewa",
        "Tgl Pengajuan",
        "Status",
        "Tahapan",
        "SLA",
    ]
    tabel = data.loc[:, [k for k in kolom if k in data.columns]].sort_values(
        "Total Harga Sewa", ascending=False
    )
    st.dataframe(
        tabel,
        hide_index=True,
        use_container_width=True,
        height=360,
        column_config={
            "Total Harga Sewa": st.column_config.NumberColumn(
                "Total Harga Sewa (Rp)", format="%.0f"
            ),
            "Tgl Pengajuan": st.column_config.DateColumn("Tgl Pengajuan", format="DD/MM/YYYY"),
        },
    )
    st.download_button(
        "Unduh data izin SPBU ini (CSV)",
        data=data.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"nfr_izin_spbu_{selected}.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"unduh_izin_{selected}",
    )

# ================================================================= LAHAN & SEWA
with tab_lahan:
    if lahan_spbu.empty and sewa_spbu.empty:
        st.info("Tidak ada data lahan maupun kontrak sewa untuk SPBU ini.")
    else:
        tersewa = int(lahan_spbu["Tersewa"].sum())
        tersedia = int(lahan_spbu["Tersedia"].sum())
        dasar = tersewa + tersedia
        occupancy = tersewa / dasar * 100 if dasar else 0
        berjalan = int(sewa_spbu["Berjalan"].sum())
        segera = int(((sewa_spbu["Sisa Hari"] >= 0) & (sewa_spbu["Sisa Hari"] <= 90)).sum())

        kpi = st.columns(4)
        kpi[0].metric("Jumlah Lahan", format_angka(len(lahan_spbu)))
        kpi[1].metric("Lahan Tersewa", format_angka(tersewa))
        kpi[2].metric("Occupancy", f"{format_angka(occupancy, 1)}%")
        kpi[3].metric("Nilai Sewa Lahan", format_rupiah(lahan_spbu["Harga Sewa (Rp)"].sum()))

        kpi2 = st.columns(4)
        kpi2[0].metric("Kontrak Sewa", format_angka(len(sewa_spbu)))
        kpi2[1].metric("Kontrak Berjalan", format_angka(berjalan))
        kpi2[2].metric("Berakhir ≤90 Hari", format_angka(segera))
        kpi2[3].metric("Nilai Sewa Berjalan", format_rupiah(sewa_spbu["Total Harga Sewa"].sum()))

        st.divider()

        kiri, kanan = st.columns(2)
        with kiri:
            st.subheader("Tenant by Nilai Sewa Lahan")
            if lahan_spbu.empty:
                st.info("Belum ada data lahan.")
            else:
                st.plotly_chart(charts.top_tenant_sewa(lahan_spbu), use_container_width=True)
        with kanan:
            st.subheader("Kontrak Berakhir 12 Bulan")
            if sewa_spbu.empty:
                st.info("Belum ada data kontrak sewa.")
            else:
                st.plotly_chart(
                    charts.expiry_timeline(sewa_spbu, snapshot), use_container_width=True
                )

        st.subheader("Detail Lahan")
        if lahan_spbu.empty:
            st.info("Belum ada data lahan untuk SPBU ini.")
        else:
            kolom_lahan = [
                "Kode Lahan",
                "Luas (M2)",
                "Tenant",
                "Status Sewa",
                "Status Approval",
                "Tanggal Mulai Sewa",
                "Tanggal Berakhir Sewa",
                "Harga Sewa (Rp)",
            ]
            tabel_lahan = lahan_spbu.loc[
                :, [k for k in kolom_lahan if k in lahan_spbu.columns]
            ].sort_values("Harga Sewa (Rp)", ascending=False)
            st.dataframe(
                tabel_lahan,
                hide_index=True,
                use_container_width=True,
                height=300,
                column_config={
                    "Luas (M2)": st.column_config.NumberColumn("Luas (m²)", format="%.0f"),
                    "Harga Sewa (Rp)": st.column_config.NumberColumn(
                        "Harga Sewa (Rp)", format="%.0f"
                    ),
                    "Tanggal Mulai Sewa": st.column_config.DateColumn(
                        "Mulai Sewa", format="DD/MM/YYYY"
                    ),
                    "Tanggal Berakhir Sewa": st.column_config.DateColumn(
                        "Berakhir Sewa", format="DD/MM/YYYY"
                    ),
                },
            )

        st.subheader("Detail Kontrak Sewa")
        if sewa_spbu.empty:
            st.info("Belum ada kontrak sewa untuk SPBU ini.")
        else:
            kolom_sewa = [
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
            tabel_sewa = sewa_spbu.loc[
                :, [k for k in kolom_sewa if k in sewa_spbu.columns]
            ].sort_values("Total Harga Sewa", ascending=False)
            st.dataframe(
                tabel_sewa,
                hide_index=True,
                use_container_width=True,
                height=300,
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
                "Unduh kontrak sewa SPBU ini (CSV)",
                data=sewa_spbu.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"nfr_sewa_spbu_{selected}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"unduh_sewa_spbu_{selected}",
            )

# ==================================================================== LEAD TIME
with tab_lead:
    pending_spbu = lt_spbu[lt_spbu["Kelompok"] == "Pending"]
    kpi = st.columns(4)
    kpi[0].metric("Total Pengajuan", format_angka(len(lt_spbu)))
    kpi[1].metric("Pending", format_angka(len(pending_spbu)))
    kpi[2].metric(
        "Median Umur Pending",
        format_hari(pending_spbu["Umur Pengajuan (hari)"].median())
        if not pending_spbu.empty
        else "-",
    )
    kpi[3].metric(
        "Lewat Batas SLA",
        format_angka(int(pending_spbu["Lewat Batas"].sum())) if not pending_spbu.empty else "0",
    )

    if pending_spbu.empty:
        st.success("Tidak ada pengajuan pending untuk SPBU ini")
    else:
        st.divider()
        kiri, kanan = st.columns(2)
        with kiri:
            st.subheader("Status Pengajuan")
            st.plotly_chart(charts.status_donut(lt_spbu), use_container_width=True)
        with kanan:
            st.subheader("Aging per Status")
            aging_spbu = an.leadtime_aging(lt_spbu)
            if aging_spbu.empty:
                st.info("Tidak ada data aging.")
            else:
                st.plotly_chart(charts.aging_status(aging_spbu), use_container_width=True)

        st.subheader("Pengajuan Pending")
        tabel_pending = pending_spbu.loc[
            :,
            [
                "ID Pengajuan",
                "Nama Tenant",
                "Nama Brand",
                "Tahap",
                "Status",
                "Tgl Pengajuan",
                "Umur Pengajuan (hari)",
                "SLA",
                "Batas",
                "Overdue (hari)",
            ],
        ].sort_values("Umur Pengajuan (hari)", ascending=False)
        st.dataframe(
            tabel_pending,
            hide_index=True,
            use_container_width=True,
            height=320,
            column_config={
                "Tgl Pengajuan": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Batas": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Umur Pengajuan (hari)": st.column_config.NumberColumn(format="%.1f"),
                "Overdue (hari)": st.column_config.NumberColumn(format="%.0f"),
            },
        )
        st.download_button(
            "Unduh pending SPBU ini (CSV)",
            data=pending_spbu.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"nfr_pending_spbu_{selected}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"unduh_pending_spbu_{selected}",
        )

# ======================================================================= DETAIL
with tab_detail:
    st.subheader("Seluruh Data Izin Prinsip SPBU Ini")
    st.dataframe(
        data.drop(columns=["Periode"], errors="ignore"),
        hide_index=True,
        use_container_width=True,
        height=480,
        column_config={
            "Total Harga Sewa": st.column_config.NumberColumn(
                "Total Harga Sewa (Rp)", format="%.0f"
            ),
            "Nominal Fee": st.column_config.NumberColumn("Nominal Fee (Rp)", format="%.0f"),
            "Tgl Pengajuan": st.column_config.DateColumn("Tgl Pengajuan", format="DD/MM/YYYY"),
            "Tgl Mulai Sewa Lahan": st.column_config.DateColumn(
                "Mulai Sewa", format="DD/MM/YYYY"
            ),
            "Tgl Akhir Sewa Lahan": st.column_config.DateColumn(
                "Akhir Sewa", format="DD/MM/YYYY"
            ),
            "Tgl Berakhir Izin Prinsip": st.column_config.DateColumn(
                "Berakhir Izin", format="DD/MM/YYYY"
            ),
            "Batas": st.column_config.DateColumn("Batas", format="DD/MM/YYYY"),
        },
    )
