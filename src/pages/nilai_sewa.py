"""Halaman Nilai Sewa Lahan: analisis nilai sewa per dimensi."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_data_or_stop, load_sewa_or_stop
from src.formatting import format_angka, format_rupiah

izin = load_data_or_stop()
snapshot = an.snapshot_date(izin)
sewa_semua = an.prepare_sewa(load_sewa_or_stop(), izin, snapshot)

st.title("💰 Nilai Sewa Lahan")
st.caption(
    "Analisis nilai sewa dari **Pengajuan NFR Sewa Lahan**: per wilayah, kategori, "
    "tipe brand, brand, sub kategori, status, dan tren bulanan."
)

with st.expander("🔎 Filter nilai sewa", expanded=True):
    f1, f2, f3 = st.columns(3)

    def _reset_provinsi() -> None:
        st.session_state.pop("ns_prov", None)
        st.session_state.pop("ns_kota", None)

    def _reset_kota() -> None:
        st.session_state.pop("ns_kota", None)

    region = f1.multiselect(
        "Region",
        sorted(sewa_semua["Region"].dropna().unique()),
        key="ns_region",
        on_change=_reset_provinsi,
    )
    opsi_prov = sorted(
        sewa_semua.loc[sewa_semua["Region"].isin(region), "Provinsi"].dropna().unique()
    ) if region else sorted(sewa_semua["Provinsi"].dropna().unique())
    provinsi = f2.multiselect(
        "Provinsi", opsi_prov, key="ns_prov", on_change=_reset_kota
    )
    dasar_kota = sewa_semua
    if region:
        dasar_kota = dasar_kota[dasar_kota["Region"].isin(region)]
    if provinsi:
        dasar_kota = dasar_kota[dasar_kota["Provinsi"].isin(provinsi)]
    kota = f3.multiselect(
        "Kab./Kota", sorted(dasar_kota["Kab./Kota"].dropna().unique()), key="ns_kota"
    )

    f4, f5, f6 = st.columns(3)
    kategori = f4.multiselect(
        "Kategori", sorted(sewa_semua["Kategori Utama"].dropna().unique()), key="ns_kategori"
    )
    tipe_brand = f5.multiselect(
        "Tipe Brand", sorted(sewa_semua["Jenis Brand"].dropna().unique()), key="ns_tipe"
    )
    status_sewa = f6.multiselect(
        "Status Sewa", sorted(sewa_semua["Status Sewa"].dropna().unique()), key="ns_status"
    )

    f7, f8 = st.columns([1, 2])
    status_izin = f7.multiselect(
        "Status Izin Prinsip",
        sorted(sewa_semua["Status Izin Prinsip"].dropna().unique()),
        key="ns_status_izin",
    )
    cari = f8.text_input(
        "Cari tenant / brand / No SPBU", placeholder="contoh: Indomaret", key="ns_cari"
    )

    level = st.radio(
        "Agregasi wilayah",
        ["Region", "Provinsi", "Kab./Kota"],
        index=0,
        horizontal=True,
        key="ns_level",
    )

tampil = sewa_semua
if region:
    tampil = tampil[tampil["Region"].isin(region)]
if provinsi:
    tampil = tampil[tampil["Provinsi"].isin(provinsi)]
if kota:
    tampil = tampil[tampil["Kab./Kota"].isin(kota)]
if kategori:
    tampil = tampil[tampil["Kategori Utama"].isin(kategori)]
if tipe_brand:
    tampil = tampil[tampil["Jenis Brand"].isin(tipe_brand)]
if status_sewa:
    tampil = tampil[tampil["Status Sewa"].isin(status_sewa)]
if status_izin:
    tampil = tampil[tampil["Status Izin Prinsip"].isin(status_izin)]
if cari.strip():
    kata = cari.strip()
    cocok = tampil["Nama Tenant"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    cocok |= tampil["Nama Brand"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    cocok |= tampil["No. SPBU"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    tampil = tampil[cocok]

if tampil.empty:
    st.warning("Tidak ada kontrak sewa yang cocok dengan filter.")
    st.stop()

total = tampil["Total Harga Sewa"].sum()
kpi = st.columns(6)
kpi[0].metric("Total Nilai Sewa", format_rupiah(total))
kpi[1].metric("Jumlah Kontrak", format_angka(len(tampil)))
kpi[2].metric("Rata-rata / Kontrak", format_rupiah(total / len(tampil)))
kpi[3].metric("Median / Kontrak", format_rupiah(tampil["Total Harga Sewa"].median()))
kpi[4].metric("Brand Unik", format_angka(tampil["Nama Brand"].nunique()))
kpi[5].metric("Tenant Unik", format_angka(tampil["Nama Tenant"].nunique()))

st.divider()

data_level = an.sewa_nilai_by(tampil, level)
kiri, kanan = st.columns(2)
with kiri:
    st.subheader(f"🗺️ Nilai Sewa per {level}")
    st.plotly_chart(
        charts.bar_nilai(data_level, level, "Nilai Sewa (Rp)", "Nilai sewa (Rp)"),
        use_container_width=True,
    )
with kanan:
    st.subheader("🏷️ Nilai Sewa per Tipe Brand")
    st.plotly_chart(
        charts.pie_nilai(
            an.sewa_nilai_by(tampil, "Jenis Brand"),
            "Jenis Brand",
            "Nilai Sewa (Rp)",
            "Nilai sewa (Rp)",
        ),
        use_container_width=True,
    )

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("📦 Nilai Sewa per Kategori")
    st.plotly_chart(
        charts.bar_nilai(
            an.sewa_nilai_by(tampil, "Kategori Utama"),
            "Kategori Utama",
            "Nilai Sewa (Rp)",
            "Nilai sewa (Rp)",
            top_n=10,
        ),
        use_container_width=True,
    )
with kanan:
    st.subheader("🏢 Top 10 Brand by Nilai Sewa")
    st.plotly_chart(
        charts.bar_nilai(
            an.sewa_nilai_by(tampil, "Nama Brand"),
            "Nama Brand",
            "Nilai Sewa (Rp)",
            "Nilai sewa (Rp)",
            top_n=10,
            warna="#a371f7",
        ),
        use_container_width=True,
    )

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🧩 Top 10 Sub Kategori")
    st.plotly_chart(
        charts.bar_nilai(
            an.sewa_nilai_by(tampil, "Sub Kategori"),
            "Sub Kategori",
            "Nilai Sewa (Rp)",
            "Nilai sewa (Rp)",
            top_n=10,
            warna="#39c5cf",
        ),
        use_container_width=True,
    )
with kanan:
    st.subheader("🏆 Top 10 SPBU by Nilai Sewa")
    st.plotly_chart(
        charts.bar_nilai(
            an.sewa_nilai_spbu(tampil),
            "No. SPBU",
            "Nilai Sewa (Rp)",
            "Nilai sewa (Rp)",
            warna="#3fb950",
        ),
        use_container_width=True,
    )

st.subheader("🔥 Kategori × Tipe Brand")
st.plotly_chart(
    charts.heatmap_nilai(an.sewa_nilai_heatmap(tampil), "Nilai sewa (Rp)"),
    use_container_width=True,
)

st.subheader("📈 Tren Nilai Sewa per Bulan Mulai")
st.plotly_chart(
    charts.tren_nilai(
        an.sewa_nilai_tren(tampil), "Bulan Mulai", "Nilai Sewa (Rp)", "Nilai sewa (Rp)"
    ),
    use_container_width=True,
)

st.divider()

st.subheader("📑 Detail Kontrak Sewa")
kolom = [
    "No. SPBU",
    "Region",
    "Provinsi",
    "Kab./Kota",
    "Nama Tenant",
    "Nama Brand",
    "Jenis Brand",
    "Kategori/Sub Kategori",
    "Status Sewa",
    "Status Izin Prinsip",
    "Tanggal Mulai Sewa",
    "Tanggal Berakhir Sewa",
    "Total Harga Sewa",
]
tabel = tampil.loc[:, [k for k in kolom if k in tampil.columns]].sort_values(
    "Total Harga Sewa", ascending=False
)
st.dataframe(
    tabel,
    hide_index=True,
    use_container_width=True,
    height=440,
    column_config={
        "Total Harga Sewa": st.column_config.NumberColumn(
            "Total Harga Sewa (Rp)", format="%.0f"
        ),
        "Tanggal Mulai Sewa": st.column_config.DateColumn(
            "Mulai Sewa", format="DD/MM/YYYY"
        ),
        "Tanggal Berakhir Sewa": st.column_config.DateColumn(
            "Berakhir Sewa", format="DD/MM/YYYY"
        ),
    },
)
st.download_button(
    "⬇️ Unduh nilai sewa (CSV)",
    data=tabel.to_csv(index=False).encode("utf-8-sig"),
    file_name="nfr_nilai_sewa.csv",
    mime="text/csv",
    use_container_width=True,
    key="unduh_nilai_sewa",
)

with st.expander("ℹ️ Tentang data nilai sewa", expanded=False):
    st.markdown(
        """
        - Sumber: `Pengajuan NFR Sewa Lahan 02-November-2026.xlsx`.
        - `Jenis Brand` adalah tipe brand: Nasional, Lokal, UMKM, Internasional, Pameran.
        - `Kategori/Sub Kategori` dipecah menjadi kolom **Kategori** dan **Sub Kategori**.
        - Region/Provinsi/Kab-Kota dipetakan dari `No. SPBU` menggunakan dataset Izin Prinsip.
        - Nilai sewa adalah `Total Harga Sewa` pada kontrak; kontrak yang telah
          berakhir tetap dihitung sesuai filter Status Sewa.
        """
    )
