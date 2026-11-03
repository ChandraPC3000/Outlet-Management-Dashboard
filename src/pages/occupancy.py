"""Halaman Occupancy Rate: persentase lahan tersewa per SPBU."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.data_loader import load_data_or_stop, load_lahan_or_stop
from src.formatting import format_angka
from src.map_spbu import render_spbu_map
from src.spbu_universe import brand_types, load_spbu_universe, spbu_ids_for_brands, universe_ringkasan

izin = load_data_or_stop()
lahan = an.prepare_lahan(load_lahan_or_stop(), izin)
occ_semua = an.occupancy_per_spbu(lahan)
universe = universe_ringkasan(load_spbu_universe())

st.title("📈 Occupancy Rate Lahan")
st.caption(
    "Persentase lahan tersewa per SPBU. Rumus: **lahan tersewa ÷ (tersewa + tersedia)**, "
    "dihitung per SPBU lalu diagregasi sesuai level wilayah."
)

with st.expander("🔎 Filter wilayah & tampilan", expanded=True):
    f1, f2, f3 = st.columns(3)

    def _reset_provinsi() -> None:
        st.session_state.pop("occ_prov", None)
        st.session_state.pop("occ_kota", None)

    def _reset_kota() -> None:
        st.session_state.pop("occ_kota", None)

    region = f1.multiselect(
        "Region",
        sorted(occ_semua["Region"].dropna().unique()),
        key="occ_region",
        on_change=_reset_provinsi,
    )
    opsi_prov = sorted(
        occ_semua.loc[occ_semua["Region"].isin(region), "Provinsi"].dropna().unique()
    ) if region else sorted(occ_semua["Provinsi"].dropna().unique())
    provinsi = f2.multiselect(
        "Provinsi", opsi_prov, key="occ_prov", on_change=_reset_kota
    )
    dasar_kota = occ_semua
    if region:
        dasar_kota = dasar_kota[dasar_kota["Region"].isin(region)]
    if provinsi:
        dasar_kota = dasar_kota[dasar_kota["Provinsi"].isin(provinsi)]
    opsi_kota = sorted(dasar_kota["Kab./Kota"].dropna().unique())
    kota = f3.multiselect("Kab./Kota", opsi_kota, key="occ_kota")

    f4, f5 = st.columns([2, 1])
    level = f4.radio(
        "Agregasi tampilan",
        ["Region", "Provinsi", "Kab./Kota"],
        index=0,
        horizontal=True,
        key="occ_level",
    )
    min_total = f5.number_input(
        "Minimal total lahan per SPBU",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
        help="Dipakai untuk grafik Top/Bottom SPBU agar SPBU dengan 1 lahan tidak mendominasi.",
        key="occ_min_total",
    )

    f6, f7, f8 = st.columns(3)
    status_level = f6.multiselect(
        "Status Level",
        sorted(occ_semua["Status Level"].dropna().unique()),
        key="occ_status_level",
    )
    tipe_spbu = f7.multiselect(
        "Tipe SPBU",
        sorted(occ_semua["Tipe SPBU"].dropna().unique()),
        key="occ_tipe_spbu",
    )
    brand = f8.multiselect(
        "Tipe Brand (tenant SPBU)",
        brand_types(),
        key="occ_brand",
        help="Memfilter SPBU yang memiliki tenant dengan tipe brand tersebut.",
    )

occ = occ_semua
if region:
    occ = occ[occ["Region"].isin(region)]
if provinsi:
    occ = occ[occ["Provinsi"].isin(provinsi)]
if kota:
    occ = occ[occ["Kab./Kota"].isin(kota)]
if status_level:
    occ = occ[occ["Status Level"].isin(status_level)]
if tipe_spbu:
    occ = occ[occ["Tipe SPBU"].isin(tipe_spbu)]
if brand:
    occ = occ[occ["No. SPBU"].isin(spbu_ids_for_brands(brand))]

if occ.empty:
    st.warning("Tidak ada SPBU yang cocok dengan filter wilayah.")
    st.stop()

tersewa = int(occ["Tersewa"].sum())
tersedia = int(occ["Tersedia"].sum())
total = tersewa + tersedia
occupancy = tersewa / total * 100 if total else 0
rata_rata = occ["Occupancy (%)"].mean()
penuh = int((occ["Occupancy (%)"] >= 99.999).sum())
rendah = int((occ["Occupancy (%)"] < 50).sum())

baris1 = st.columns(4)
baris1[0].metric("Occupancy Total", f"{format_angka(occupancy, 1)}%")
baris1[1].metric("Rata-rata per SPBU", f"{format_angka(rata_rata, 1)}%")
baris1[2].metric("SPBU dengan Lahan", format_angka(len(occ)))
baris1[3].metric("Total Lahan", format_angka(total))

baris2 = st.columns(4)
baris2[0].metric("Lahan Tersewa", format_angka(tersewa))
baris2[1].metric("Lahan Tersedia", format_angka(tersedia))
baris2[2].metric("SPBU Penuh (100%)", format_angka(penuh))
baris2[3].metric("SPBU < 50%", format_angka(rendah))

st.caption(
    "**Occupancy Total** = total tersewa ÷ total lahan (weighted, sama dengan angka region). "
    "**Rata-rata per SPBU** = rata-rata persentase tiap SPBU."
)
st.caption(
    f"dari **{format_angka(universe['total'])} total SPBU universe** "
    f"({format_angka(universe['reguler'])} Reguler + "
    f"{format_angka(universe['existing_ekstra'])} existing); occupancy hanya untuk SPBU "
    "yang memiliki data lahan."
)

st.subheader("🗺️ Peta Occupancy per SPBU")
st.caption("Warna titik = Tipe SPBU; ukuran/zoom mengikuti filter.")
render_spbu_map(occ, color_col="Tipe SPBU", region_col="Region", height=480)

st.divider()

kiri, kanan = st.columns([1, 1])
with kiri:
    st.subheader("🎯 Occupancy Keseluruhan")
    st.plotly_chart(charts.occupancy_gauge(occupancy), use_container_width=True)
with kanan:
    st.subheader("🏷️ Sebaran SPBU")
    st.plotly_chart(charts.occupancy_status_donut(an.occupancy_status(occ)), use_container_width=True)

data_level = an.occupancy_by(occ, level)
data_chart = data_level.nlargest(30, "Total Lahan") if len(data_level) > 30 else data_level
if len(data_level) > 30:
    st.caption(f"Menampilkan 30 dari {len(data_level)} {level.lower()} dengan total lahan terbanyak.")

kiri, kanan = st.columns(2)
with kiri:
    st.subheader(f"📊 Occupancy per {level}")
    st.plotly_chart(charts.occupancy_bar(data_chart, level), use_container_width=True)
with kanan:
    st.subheader("🔥 Distribusi Occupancy per Wilayah")
    heat_data = an.occupancy_heatmap(occ, level)
    heat_data = heat_data.loc[heat_data.sum(axis=1).nlargest(20).index]
    st.plotly_chart(charts.occupancy_heatmap(heat_data), use_container_width=True)

st.subheader("🔵 Total Lahan vs Occupancy per SPBU")
st.plotly_chart(charts.occupancy_scatter(occ), use_container_width=True)

sub = occ[occ["Total Lahan"] >= min_total]
kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🏆 10 SPBU Occupancy Tertinggi")
    if sub.empty:
        st.info("Tidak ada SPBU dengan total lahan memenuhi ambang minimum.")
    else:
        st.plotly_chart(
            charts.occupancy_top_bar(an.occupancy_top(sub, 10, terendah=False)),
            use_container_width=True,
        )
with kanan:
    st.subheader("🚨 10 SPBU Occupancy Terendah")
    if sub.empty:
        st.info("Tidak ada SPBU dengan total lahan memenuhi ambang minimum.")
    else:
        st.plotly_chart(
            charts.occupancy_top_bar(an.occupancy_top(sub, 10, terendah=True)),
            use_container_width=True,
        )

st.divider()

st.subheader("📑 Detail Occupancy per SPBU")
kolom = ["No. SPBU", "Region", "Provinsi", "Kab./Kota", "Tersewa", "Tersedia", "Total Lahan", "Occupancy (%)"]
tabel = occ.loc[:, kolom].sort_values("Occupancy (%)", ascending=False)
st.dataframe(
    tabel,
    hide_index=True,
    use_container_width=True,
    height=420,
    column_config={
        "Occupancy (%)": st.column_config.NumberColumn("Occupancy (%)", format="%.1f%%"),
    },
)
st.download_button(
    "⬇️ Unduh occupancy per SPBU (CSV)",
    data=tabel.to_csv(index=False).encode("utf-8-sig"),
    file_name="nfr_occupancy_per_spbu.csv",
    mime="text/csv",
    use_container_width=True,
    key="unduh_occ",
)

with st.expander("ℹ️ Cara menghitung", expanded=False):
    st.markdown(
        """
        - **Per SPBU:** `Occupancy = lahan tersewa ÷ (lahan tersewa + lahan tersedia)`.
          Hanya lahan dengan `Status Sewa` Tersewa/Tersedia yang dihitung; baris
          berstatus lain tidak masuk penyebut.
        - **Agregasi wilayah:** total tersewa dibagi total lahan di wilayah tersebut
          (weighted). Ini sama dengan menjumlahkan pembilang dan penyebut seluruh
          SPBU, bukan merata-ratakan persentase.
        - **Rata-rata per SPBU** ditampilkan terpisah agar terlihat perbedaan antara
          perspektif lahan dan perspektif jumlah outlet.
        - Default tampilan adalah **Region**; ubah radio untuk melihat Provinsi atau
          Kab./Kota.
        """
    )
