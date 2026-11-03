"""Halaman Home: ringkasan seluruh ekosistem data NFR."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_all
from src.formatting import format_angka, format_rupiah
from src.spbu_universe import load_spbu_universe, universe_ringkasan

izin, lahan_mentah, sewa_mentah = load_all()
universe = load_spbu_universe()
info_universe = universe_ringkasan(universe)
snapshot = an.snapshot_date(izin)
ldf = an.prepare_leadtime(izin, snapshot)
lahan = an.prepare_lahan(lahan_mentah, izin)
sewa = an.prepare_sewa(sewa_mentah, izin, snapshot)

tersewa = int(lahan["Tersewa"].sum())
tersedia = int(lahan["Tersedia"].sum())
occupancy = tersewa / (tersewa + tersedia) * 100 if (tersewa + tersedia) else 0
pending = int((ldf["Kelompok"] == "Pending").sum())
berjalan = int(sewa["Berjalan"].sum())

st.title("🚀 NFR Management System")
st.caption(
    "Dashboard gabungan **Izin Prinsip**, **Lahan**, **Sewa**, **Occupancy**, "
    "**Nilai Sewa**, **Management Fee**, dan **Lead Time** · "
    f"snapshot data {snapshot:%d %B %Y}."
)

baris1 = st.columns(3)
baris1[0].metric("Total Pengajuan Izin", f"{format_angka(len(izin))} baris")
baris1[1].metric("Jumlah SPBU", format_angka(info_universe["total"]))
baris1[2].metric("Izin Pending", format_angka(pending))

st.caption(
    f"**{format_angka(info_universe['reguler'])} SPBU Reguler** + "
    f"**{format_angka(info_universe['existing_ekstra'])} SPBU existing** di luar Reguler "
    "(dari file izin, lahan, sewa, dan ketersediaan) = "
    f"**{format_angka(info_universe['total'])} total SPBU universe**."
)

baris2 = st.columns(3)
baris2[0].metric("Lahan Tersewa", f"{format_angka(tersewa)} lahan")
baris2[1].metric("Occupancy Lahan", f"{format_angka(occupancy, 1)}%")
baris2[2].metric("Nilai Sewa Lahan", format_rupiah(lahan["Harga Sewa (Rp)"].sum()))

baris3 = st.columns(3)
baris3[0].metric("Kontrak Sewa Berjalan", format_angka(berjalan))
baris3[1].metric("Nilai Sewa Berjalan", format_rupiah(sewa.loc[sewa["Berjalan"], "Total Harga Sewa"].sum()))
baris3[2].metric(
    "Kontrak Berakhir ≤90 Hari",
    format_angka(int(((sewa["Sisa Hari"] >= 0) & (sewa["Sisa Hari"] <= 90)).sum())),
)

st.divider()

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🏗️ Posisi Tahapan Izin Prinsip")
    st.plotly_chart(charts.funnel_tahapan(an.leadtime_funnel(ldf)), use_container_width=True)
with kanan:
    st.subheader("📋 Komposisi Status Pengajuan")
    st.plotly_chart(charts.status_donut(izin), use_container_width=True)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🏞️ Occupancy Lahan per Region")
    st.plotly_chart(charts.occupancy_region(an.lahan_ringkasan(lahan)), use_container_width=True)
with kanan:
    st.subheader("📈 Tren Pengajuan per Bulan")
    st.plotly_chart(charts.tren_pengajuan(izin), use_container_width=True)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("⏳ Kontrak Sewa Berakhir 12 Bulan")
    st.plotly_chart(charts.expiry_timeline(sewa, snapshot), use_container_width=True)
with kanan:
    st.subheader("💰 Nilai Sewa per Kategori")
    st.plotly_chart(charts.nilai_kategori_sewa(sewa), use_container_width=True)

st.divider()

with st.expander("ℹ️ Panduan & sumber data", expanded=False):
    st.markdown(
        f"""
        **Halaman**

        - **📍 Director Summary** — analisis satu SPBU: izin prinsip, lahan, sewa,
          dan lead time outlet tersebut.
        - **🔎 Data Explorer** — telusuri seluruh pengajuan izin dengan filter.
        - **🧭 Ketersediaan Lahan** — daftar lahan siap tawarkan ke mitra + unduh Excel.
        - **📈 Occupancy Rate** — persentase lahan tersewa per SPBU dan per wilayah.
        - **🏞️ Lahan & Sewa** — occupancy lahan, nilai sewa, kontrak yang segera berakhir.
        - **💰 Nilai Sewa** — analisis nilai sewa per wilayah, kategori, tipe brand, brand, tren.
        - **💳 Management Fee** — analisis Nominal Fee per wilayah, kategori, brand, status, tren.
        - **🗺️ LOKASI Intelligence** — peta SPBU + BVT Red/Blue Ocean dan tautan Google Maps.
        - **⏱️ Lead Time** — funnel tahapan, aging pending, SLA, dan prioritas tindak lanjut.

        **Sumber data (snapshot {snapshot:%d %B %Y})**

        | Dataset | Baris |
        |---|---:|
        | Pengajuan NFR Izin Prinsip | {format_angka(len(izin))} |
        | NFR Master Lahan | {format_angka(len(lahan_mentah))} |
        | Pengajuan NFR Sewa Lahan | {format_angka(len(sewa_mentah))} |

        Data dimuat sekali per sesi lalu di-cache. File Excel berada di folder `Data/`.
        """
    )
