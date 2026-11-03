"""Halaman Management Fee: analisis Nominal Fee pengajuan izin prinsip."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_data_or_stop
from src.formatting import format_angka, format_rupiah
from src.spbu_universe import load_spbu_universe, universe_ringkasan

izin = load_data_or_stop()
fee_semua = an.prepare_fee(izin)
universe = universe_ringkasan(load_spbu_universe())

st.title("💳 Management Fee")
st.caption(
    "Analisis **Nominal Fee** pengajuan izin prinsip: per wilayah, kategori, tipe brand, "
    "brand, status, tren bulanan, dan sebaran nilai."
)

with st.expander("🔎 Filter management fee", expanded=True):
    f1, f2, f3 = st.columns(3)

    def _reset_provinsi() -> None:
        st.session_state.pop("mf_prov", None)
        st.session_state.pop("mf_kota", None)

    def _reset_kota() -> None:
        st.session_state.pop("mf_kota", None)

    region = f1.multiselect(
        "Region",
        sorted(fee_semua["Region"].dropna().unique()),
        key="mf_region",
        on_change=_reset_provinsi,
    )
    opsi_prov = sorted(
        fee_semua.loc[fee_semua["Region"].isin(region), "Provinsi"].dropna().unique()
    ) if region else sorted(fee_semua["Provinsi"].dropna().unique())
    provinsi = f2.multiselect(
        "Provinsi", opsi_prov, key="mf_prov", on_change=_reset_kota
    )
    dasar_kota = fee_semua
    if region:
        dasar_kota = dasar_kota[dasar_kota["Region"].isin(region)]
    if provinsi:
        dasar_kota = dasar_kota[dasar_kota["Provinsi"].isin(provinsi)]
    kota = f3.multiselect(
        "Kab./Kota", sorted(dasar_kota["Kab./Kota"].dropna().unique()), key="mf_kota"
    )

    f4, f5, f6 = st.columns(3)
    kategori = f4.multiselect(
        "Kategori", sorted(fee_semua["Kategori"].dropna().unique()), key="mf_kategori"
    )
    tipe_brand = f5.multiselect(
        "Tipe Brand", sorted(fee_semua["Tipe Brand"].dropna().unique()), key="mf_tipe"
    )
    status = f6.multiselect(
        "Status", sorted(fee_semua["Status"].dropna().unique()), key="mf_status"
    )

    f7, f8 = st.columns([1, 2])
    tahapan = f7.multiselect(
        "Tahapan", sorted(fee_semua["Tahapan"].dropna().unique()), key="mf_tahapan"
    )
    cari = f8.text_input(
        "Cari tenant / brand / No SPBU", placeholder="contoh: Alfamart", key="mf_cari"
    )

    f9, f10 = st.columns([1, 2])
    hanya_fee = f9.checkbox(
        "Hanya transaksi ber-fee", value=True, key="mf_hanya_fee"
    )
    level = f10.radio(
        "Agregasi wilayah",
        ["Region", "Provinsi", "Kab./Kota"],
        index=0,
        horizontal=True,
        key="mf_level",
    )

dasar = fee_semua
if region:
    dasar = dasar[dasar["Region"].isin(region)]
if provinsi:
    dasar = dasar[dasar["Provinsi"].isin(provinsi)]
if kota:
    dasar = dasar[dasar["Kab./Kota"].isin(kota)]
if kategori:
    dasar = dasar[dasar["Kategori"].isin(kategori)]
if tipe_brand:
    dasar = dasar[dasar["Tipe Brand"].isin(tipe_brand)]
if status:
    dasar = dasar[dasar["Status"].isin(status)]
if tahapan:
    dasar = dasar[dasar["Tahapan"].isin(tahapan)]
if cari.strip():
    kata = cari.strip()
    cocok = dasar["Nama Tenant"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    cocok |= dasar["Nama Brand"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    cocok |= dasar["No. SPBU"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    dasar = dasar[cocok]

if dasar.empty:
    st.warning("Tidak ada pengajuan yang cocok dengan filter.")
    st.stop()

tampil = dasar[dasar["Nominal Fee"] > 0] if hanya_fee else dasar
ber_fee = int((dasar["Nominal Fee"] > 0).sum())
if ber_fee == 0:
    st.warning("Tidak ada transaksi ber-fee pada kombinasi filter ini.")
    st.stop()
total = dasar["Nominal Fee"].sum()
persen_ber_fee = ber_fee / len(dasar) * 100 if len(dasar) else 0

kpi1 = st.columns(4)
kpi1[0].metric("Total Management Fee", format_rupiah(total))
kpi1[1].metric("Transaksi Ber-fee", format_angka(ber_fee))
kpi1[2].metric("Rata-rata Fee", format_rupiah(dasar.loc[dasar["Nominal Fee"] > 0, "Nominal Fee"].mean()))
kpi1[3].metric("Median Fee", format_rupiah(dasar.loc[dasar["Nominal Fee"] > 0, "Nominal Fee"].median()))

kpi2 = st.columns(3)
kpi2[0].metric("Brand Unik", format_angka(dasar["Nama Brand"].nunique()))
kpi2[1].metric("SPBU dengan Fee", format_angka(dasar["No. SPBU"].nunique()))
kpi2[2].metric("Pengajuan Ber-fee", f"{format_angka(persen_ber_fee, 1)}%")

st.caption(
    f"dari **{format_angka(universe['total'])} total SPBU universe** "
    f"({format_angka(universe['reguler'])} Reguler + "
    f"{format_angka(universe['existing_ekstra'])} existing)."
)

if hanya_fee:
    st.caption(
        f"{format_angka(len(dasar) - len(tampil))} pengajuan tanpa fee disembunyikan dari tabel/analisis. "
        "Angka total fee tetap dihitung dari seluruh pengajuan."
    )

st.divider()

data_level = an.fee_by(tampil, level)
kiri, kanan = st.columns(2)
with kiri:
    st.subheader(f"🗺️ Fee per {level}")
    st.plotly_chart(
        charts.bar_nilai(data_level, level, "Total Fee (Rp)", "Total fee (Rp)"),
        use_container_width=True,
    )
with kanan:
    st.subheader("🏷️ Fee per Tipe Brand")
    st.plotly_chart(
        charts.pie_nilai(
            an.fee_by(tampil, "Tipe Brand"), "Tipe Brand", "Total Fee (Rp)", "Total fee (Rp)"
        ),
        use_container_width=True,
    )

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("📦 Fee per Kategori")
    st.plotly_chart(
        charts.bar_nilai(
            an.fee_by(tampil, "Kategori"),
            "Kategori",
            "Total Fee (Rp)",
            "Total fee (Rp)",
            top_n=10,
            warna="#d29922",
        ),
        use_container_width=True,
    )
with kanan:
    st.subheader("🏢 Top 10 Brand by Fee")
    st.plotly_chart(
        charts.bar_nilai(
            an.fee_by(tampil, "Nama Brand"),
            "Nama Brand",
            "Total Fee (Rp)",
            "Total fee (Rp)",
            top_n=10,
            warna="#a371f7",
        ),
        use_container_width=True,
    )

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("📋 Fee per Status")
    st.plotly_chart(
        charts.bar_nilai(
            an.fee_by(tampil, "Status"),
            "Status",
            "Total Fee (Rp)",
            "Total fee (Rp)",
            warna="#39c5cf",
        ),
        use_container_width=True,
    )
with kanan:
    st.subheader("🏆 Top 10 SPBU by Fee")
    st.plotly_chart(
        charts.bar_nilai(
            an.fee_spbu(tampil),
            "No. SPBU",
            "Total Fee (Rp)",
            "Total fee (Rp)",
            warna="#3fb950",
        ),
        use_container_width=True,
    )

st.subheader("🔥 Kategori × Tipe Brand")
st.plotly_chart(
    charts.heatmap_nilai(an.fee_heatmap(tampil), "Total fee (Rp)"),
    use_container_width=True,
)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("📈 Tren Fee per Bulan Pengajuan")
    st.plotly_chart(
        charts.tren_nilai(
            an.fee_tren(tampil), "Periode", "Total Fee (Rp)", "Total fee (Rp)"
        ),
        use_container_width=True,
    )
with kanan:
    st.subheader("📊 Sebaran Nilai Fee")
    st.plotly_chart(
        charts.bar_jumlah(
            an.fee_distribution(dasar),
            "Rentang Fee",
            "Jumlah Transaksi",
            "Jumlah transaksi",
        ),
        use_container_width=True,
    )

st.divider()

st.subheader("📑 Detail Transaksi Management Fee")
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
    "Status",
    "Tahapan",
    "Tgl Pengajuan",
    "Nominal Fee",
    "Total Harga Sewa",
    "Fee Ratio (%)",
]
tabel = tampil.loc[:, [k for k in kolom if k in tampil.columns]].sort_values(
    "Nominal Fee", ascending=False
)
st.dataframe(
    tabel,
    hide_index=True,
    use_container_width=True,
    height=460,
    column_config={
        "Nominal Fee": st.column_config.NumberColumn("Nominal Fee (Rp)", format="%.0f"),
        "Total Harga Sewa": st.column_config.NumberColumn(
            "Total Harga Sewa (Rp)", format="%.0f"
        ),
        "Fee Ratio (%)": st.column_config.NumberColumn("Fee Ratio (%)", format="%.2f%%"),
        "Tgl Pengajuan": st.column_config.DateColumn("Tgl Pengajuan", format="DD/MM/YYYY"),
    },
)
st.download_button(
    "⬇️ Unduh management fee (CSV)",
    data=tabel.to_csv(index=False).encode("utf-8-sig"),
    file_name="nfr_management_fee.csv",
    mime="text/csv",
    use_container_width=True,
    key="unduh_fee",
)

with st.expander("ℹ️ Tentang management fee", expanded=False):
    st.markdown(
        """
        - Sumber: kolom **`Nominal Fee`** pada `Pengajuan NFR Izin Prinsip 02-November 2026`.
        - **24.531 pengajuan** memiliki `Nominal Fee = 0`; baris ini tidak dihitung
          sebagai transaksi ber-fee, tetapi total fee tetap dihitung dari seluruh baris
          (nilai 0 tidak mengubah total).
        - **Fee Ratio** = `Nominal Fee ÷ Total Harga Sewa × 100`. Rasio bisa sangat besar
          bila harga sewa 0; gunakan hanya sebagai indikasi, bukan dasar keputusan.
        - Tipe brand mengikuti kolom `Tipe Brand`: Nasional, Lokal, UMKM, Internasional,
          Pameran.
        - Region/Provinsi/Kab-Kota berasal dari data pengajuan yang sama.
        """
    )
