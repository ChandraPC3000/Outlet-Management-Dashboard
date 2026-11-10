"""Halaman LOKASI Intelligence: GIS SPBU + analisis BVT Red/Blue Ocean."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html

from src import analytics as an
from src import charts
from src.data_loader import load_data_or_stop
from src.formatting import format_angka
from src.map_lokasi import build_map
from src.master_data import load_bvt, load_spbu_master, top_kategori
from src.spbu_universe import brand_types, load_spbu_universe, spbu_ids_for_brands, universe_ringkasan

izin = load_data_or_stop()
master = load_spbu_master()
bvt = load_bvt()
universe = universe_ringkasan(load_spbu_universe())

# Basis = master SPBU (15.103) + data BVT; SPBU tanpa BVT tetap tampil.
bvt_fields = bvt[
    [
        "No. SPBU",
        "Road Type",
        "SES",
        "Red Ocean",
        "Blue Ocean",
        "Red Count",
        "Blue Count",
        "Blue Ocean Score (%)",
        "Kelas BVT",
    ]
]
bvt_semua = master.merge(bvt_fields, on="No. SPBU", how="left")

bvt_only = bvt[~bvt["No. SPBU"].isin(master["No. SPBU"])].copy()
for kolom in bvt_semua.columns:
    if kolom not in bvt_only.columns:
        bvt_only[kolom] = "Tidak diketahui"
bvt_only["Reguler"] = bvt_only["Reguler"].astype(bool)
bvt_semua = pd.concat([bvt_semua, bvt_only[bvt_semua.columns]], ignore_index=True)

for kolom, nilai in (
    ("Kelas BVT", "Tidak ada data BVT"),
    ("Road Type", "Tidak diketahui"),
    ("SES", "Tidak diketahui"),
    ("Red Ocean", "-"),
    ("Blue Ocean", "-"),
):
    bvt_semua[kolom] = bvt_semua[kolom].fillna(nilai)
for kolom in ("Red Count", "Blue Count"):
    bvt_semua[kolom] = bvt_semua[kolom].fillna(0).astype(int)

# Region tidak ada di file BVT: ambil dari peta SPBU, fallback dari provinsi.
peta_spbu = izin[["No. SPBU", "Region"]].drop_duplicates("No. SPBU")
bvt_semua = bvt_semua.merge(peta_spbu, on="No. SPBU", how="left")
prov_region = (
    izin.assign(Provinsi_key=izin["Provinsi"].astype("string").str.strip().str.title())
    .groupby("Provinsi_key")["Region"]
    .agg(lambda s: s.mode().iat[0] if not s.mode().empty else "Tidak diketahui")
)
bvt_semua["Provinsi_key"] = bvt_semua["Provinsi"].astype("string").str.strip().str.title()
bvt_semua["Region"] = (
    bvt_semua["Region"].fillna(bvt_semua["Provinsi_key"].map(prov_region)).fillna("Tidak diketahui")
)

st.title("LOKASI Intelligence")
st.caption(
    "Analisis lokasi SPBU + **BVT Red/Blue Ocean**. Rekomendasi untuk mitra adalah "
    "Blue Ocean, tetapi praktik lapangan boleh memakai Red Ocean. Titik peta memakai "
    "koordinat master Lembaga Penyalur/BVT; tautan Google Maps tersedia per SPBU."
)

with st.expander("Filter lokasi & BVT", expanded=True):
    f1, f2 = st.columns([2, 2])
    cakupan = f1.radio(
        "Cakupan jenis lembaga penyalur",
        ["Reguler", "Semua", "Non-Reguler"],
        index=0,
        horizontal=True,
        key="lok_cakupan",
        help="Reguler = 6.525 SPBU. Pilih Semua untuk menggabungkan PERTASHOP/Kompak/Mini/dll.",
    )
    jenis = f2.multiselect(
        "Jenis spesifik (opsional)",
        sorted(bvt_semua["Jenis Lembaga Penyalur"].dropna().unique()),
        key="lok_jenis",
        placeholder="Reguler, PERTASHOP, SPBU Kompak, ...",
    )

    f3, f4, f5 = st.columns(3)

    def _reset_provinsi() -> None:
        st.session_state.pop("lok_prov", None)
        st.session_state.pop("lok_kota", None)

    def _reset_kota() -> None:
        st.session_state.pop("lok_kota", None)

    region = f3.multiselect(
        "Region",
        sorted(bvt_semua["Region"].dropna().unique()),
        key="lok_region",
        on_change=_reset_provinsi,
    )
    opsi_prov = sorted(
        bvt_semua.loc[bvt_semua["Region"].isin(region), "Provinsi"].dropna().unique()
    ) if region else sorted(bvt_semua["Provinsi"].dropna().unique())
    provinsi = f4.multiselect(
        "Provinsi", opsi_prov, key="lok_prov", on_change=_reset_kota
    )
    dasar_kota = bvt_semua
    if region:
        dasar_kota = dasar_kota[dasar_kota["Region"].isin(region)]
    if provinsi:
        dasar_kota = dasar_kota[dasar_kota["Provinsi"].isin(provinsi)]
    kota = f5.multiselect(
        "Kab./Kota", sorted(dasar_kota["Kota/Kabupaten"].dropna().unique()), key="lok_kota"
    )

    f6, f7, f8 = st.columns(3)
    tipe = f6.multiselect(
        "Tipe SPBU", sorted(bvt_semua["Tipe SPBU"].dropna().unique()), key="lok_tipe"
    )
    road = f7.multiselect(
        "Road Type", sorted(bvt_semua["Road Type"].dropna().unique()), key="lok_road"
    )
    kelas = f8.multiselect(
        "Kelas BVT",
        ["Blue Ocean", "Peluang Campuran", "Red Ocean"],
        key="lok_kelas",
    )

    f9, f10 = st.columns(2)
    status_level = f9.multiselect(
        "Status Level",
        sorted(bvt_semua["Status Level"].dropna().unique()),
        key="lok_status_level",
    )
    brand = f10.multiselect(
        "Tipe Brand (tenant SPBU)",
        brand_types(),
        key="lok_brand",
        help="Memfilter SPBU yang memiliki tenant dengan tipe brand tersebut.",
    )

    cari = st.text_input(
        "Cari No SPBU / nama SPBU / kota / alamat",
        placeholder="contoh: 14233120 atau Banda Aceh",
        key="lok_cari",
    )

data = bvt_semua
if cakupan == "Reguler":
    data = data[data["Reguler"]]
elif cakupan == "Non-Reguler":
    data = data[~data["Reguler"]]
if jenis:
    data = data[data["Jenis Lembaga Penyalur"].isin(jenis)]
if region:
    data = data[data["Region"].isin(region)]
if provinsi:
    data = data[data["Provinsi"].isin(provinsi)]
if kota:
    data = data[data["Kota/Kabupaten"].isin(kota)]
if tipe:
    data = data[data["Tipe SPBU"].isin(tipe)]
if road:
    data = data[data["Road Type"].isin(road)]
if kelas:
    data = data[data["Kelas BVT"].isin(kelas)]
if status_level:
    data = data[data["Status Level"].isin(status_level)]
if brand:
    data = data[data["No. SPBU"].isin(spbu_ids_for_brands(brand))]
if cari.strip():
    kata = cari.strip()
    cocok = data["No. SPBU"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    for kolom in ("Nama SPBU", "Kota/Kabupaten", "Alamat", "Provinsi"):
        cocok |= data[kolom].astype("string").str.contains(kata, case=False, na=False, regex=False)
    data = data[cocok]

if data.empty:
    st.warning("Tidak ada SPBU yang cocok dengan filter.")
    st.stop()

blue = int((data["Kelas BVT"] == "Blue Ocean").sum())
red = int((data["Kelas BVT"] == "Red Ocean").sum())
campuran = int((data["Kelas BVT"] == "Peluang Campuran").sum())
tanpa_bvt = int((data["Kelas BVT"] == "Tidak ada data BVT").sum())
total = len(data)
bvt_coverage = (total - tanpa_bvt) / total * 100 if total else 0

kpi1 = st.columns(4)
kpi1[0].metric("Total SPBU", format_angka(total))
kpi1[1].metric("SPBU Reguler", format_angka(int(data["Reguler"].sum())))
kpi1[2].metric("Blue Ocean", format_angka(blue))
kpi1[3].metric("Blue Ocean Share", f"{format_angka(blue / total * 100, 1)}%")

kpi2 = st.columns(4)
kpi2[0].metric("Red Ocean", format_angka(red))
kpi2[1].metric("Peluang Campuran", format_angka(campuran))
kpi2[2].metric("Median Blue Score", f"{format_angka(data['Blue Ocean Score (%)'].median(), 1)}%")
kpi2[3].metric("BVT Coverage", f"{format_angka(bvt_coverage, 1)}%")

st.caption(
    f"Total SPBU Pertamina: **{format_angka(universe['total'])}** "
    f"({format_angka(universe['reguler'])} Reguler + "
    f"{format_angka(universe['existing_ekstra'])} existing). Halaman ini default "
    "menampilkan **Reguler**; pilih Semua untuk seluruh master."
)

top_red = top_kategori(data, "Red Ocean", 8)
top_blue = top_kategori(data, "Blue Ocean", 8)

kiri, kanan = st.columns(2)
with kiri:
    st.info(
        f"**Untuk Mitra NFR — rekomendasi Blue Ocean**\n\n"
        f"{format_angka(blue)} SPBU punya peluang usaha dengan pesaing minim "
        f"({format_angka(blue / total * 100, 1)}% dari filter). "
        "Prioritaskan kategori Blue Ocean di tabel/unduhan.",
    )
with kanan:
    st.warning(
        f"**Untuk SPBU Owner — Red Ocean sebagai pembanding**\n\n"
        f"{format_angka(red)} SPBU berada di area dengan bisnis sekitar yang sudah ramai. "
        "Tetap bisa dipakai bila pemilik ingin trafik/proven demand yang sudah ada.",
    )

tab_peta, tab_bvt, tab_tabel = st.tabs(
    ["Peta & Ringkasan", "Red/Blue Ocean", "Tabel & Unduh"]
)

with tab_peta:
    st.subheader("Peta Lokasi SPBU")
    st.caption(
        "Warna titik = kelas BVT. Peta memakai tile **OpenStreetMap**. Saat **zoom out "
        "(≤5)** hanya tampil 8 lingkaran besar per region; **zoom in** menampilkan "
        "titik/cluster SPBU. Koordinat berasal dari master Lembaga Penyalur (fallback BVT); "
        "gunakan tautan Google Maps di tabel untuk verifikasi posisi."
    )
    st.markdown(
        "**Blue Ocean** &nbsp;·&nbsp; **Peluang Campuran** &nbsp;·&nbsp; "
        "**Red Ocean** &nbsp;·&nbsp; **Tanpa data BVT**"
    )
    st_html(
        build_map(data).get_root().render(),
        height=620,
        scrolling=False,
    )
    st.caption("Peta: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).")

    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Komposisi BVT")
        st.plotly_chart(charts.bvt_donut(data), use_container_width=True)
    with kanan:
        st.subheader("BVT per Provinsi")
        st.plotly_chart(charts.bvt_provinsi(data), use_container_width=True)

with tab_bvt:
    kiri, kanan = st.columns(2)
    with kiri:
        st.subheader("Pesaing Sekitar (Red Ocean)")
        st.caption("Kategori usaha yang sudah banyak/jenuh di sekitar SPBU.")
        st.plotly_chart(
            charts.bar_hitung(top_red, "Kategori", "Jumlah", "Jumlah SPBU", warna="#f85149"),
            use_container_width=True,
        )
    with kanan:
        st.subheader("Peluang (Blue Ocean)")
        st.caption("Kategori usaha yang masih minim pesaing dan cocok dikembangkan.")
        st.plotly_chart(
            charts.bar_hitung(top_blue, "Kategori", "Jumlah", "Jumlah SPBU", warna="#2f81f7"),
            use_container_width=True,
        )

    st.subheader("Sebaran Blue Ocean Score")
    bins = [-0.01, 20, 40, 60, 80, 100]
    label = ["0–20", "20–40", "40–60", "60–80", "80–100"]
    skor = pd.cut(data["Blue Ocean Score (%)"], bins=bins, labels=label, include_lowest=True)
    tabel_skor = (
        skor.value_counts().reindex(label, fill_value=0).rename_axis("Rentang Skor").reset_index(name="Jumlah SPBU")
    )
    st.plotly_chart(
        charts.bar_jumlah(tabel_skor, "Rentang Skor", "Jumlah SPBU", "Jumlah SPBU"),
        use_container_width=True,
    )

    st.subheader("Top 20 Blue Ocean")
    top20 = (
        data[data["Kelas BVT"] == "Blue Ocean"]
        .nlargest(20, "Blue Ocean Score (%)")
        .loc[
            :,
            [
                "No. SPBU",
                "Nama SPBU",
                "Kota/Kabupaten",
                "Blue Ocean Score (%)",
                "Blue Ocean",
                "Google Maps",
            ],
        ]
    )
    st.dataframe(
        top20,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Blue Ocean Score (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Blue Ocean": st.column_config.TextColumn("Kategori Blue Ocean", width="large"),
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="Buka peta"),
        },
    )

with tab_tabel:
    st.subheader("Detail SPBU + BVT")
    kolom = [
        "No. SPBU",
        "Nama SPBU",
        "Jenis Lembaga Penyalur",
        "Tipe SPBU",
        "Region",
        "Provinsi",
        "Kota/Kabupaten",
        "Kecamatan",
        "Road Type",
        "SES",
        "Red Ocean",
        "Blue Ocean",
        "Red Count",
        "Blue Count",
        "Blue Ocean Score (%)",
        "Kelas BVT",
        "Sumber Tilok",
        "Latitude",
        "Longitude",
        "Google Maps",
    ]
    tabel = data.loc[:, [k for k in kolom if k in data.columns]].sort_values(
        ["Kelas BVT", "Blue Ocean Score (%)"], ascending=[True, False]
    )
    st.dataframe(
        tabel,
        hide_index=True,
        use_container_width=True,
        height=520,
        column_config={
            "Blue Ocean Score (%)": st.column_config.NumberColumn(format="%.1f%%"),
            "Latitude": st.column_config.NumberColumn(format="%.6f"),
            "Longitude": st.column_config.NumberColumn(format="%.6f"),
            "Red Ocean": st.column_config.TextColumn("Pesaing (Red Ocean)", width="medium"),
            "Blue Ocean": st.column_config.TextColumn("Peluang (Blue Ocean)", width="medium"),
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="Buka peta"),
        },
    )
    st.download_button(
        "Unduh data LOKASI Intelligence (CSV)",
        data=tabel.to_csv(index=False).encode("utf-8-sig"),
        file_name="nfr_lokasi_intelligence.csv",
        mime="text/csv",
        use_container_width=True,
        key="unduh_lokasi",
    )

    st.caption(
        f"Master referensi: {format_angka(len(master))} SPBU "
        f"({format_angka(int(master['Reguler'].sum()))} Reguler) · "
        f"BVT: {format_angka(len(bvt_semua))} SPBU. "
        "Kolom kosong pada tabel dashboard diisi dari master ini."
    )

with st.expander("Definisi BVT, sumber data & catatan tilok", expanded=False):
    st.markdown(
        """
        **Red Ocean** — usaha/bisnis di sekitar SPBU yang sudah jenuh atau banyak
        pesaingnya. **Blue Ocean** — kategori usaha yang masih minim pesaing dan
        cocok dikembangkan.

        **Blue Ocean Score** = `Blue Count ÷ (Red Count + Blue Count) × 100`.
        - `Blue Ocean`: skor ≥ 50
        - `Peluang Campuran`: skor 1–49
        - `Red Ocean`: tidak ada kategori Blue (skor 0)

        **Sumber BVT:** `SPBU_All_34_Provinces_20261016.xlsx` (6.787 SPBU, 34 provinsi).
        **Sumber master:** `List Lembaga Penyalur 13 Oktober 2026` (15.103 SPBU,
        6.525 Reguler). Nomor PIC tidak disertakan di halaman ini.

        **Tilok:** koordinat memakai master Lembaga Penyalur; jika tidak valid,
        fallback ke koordinat BVT. File BVT asli menukar kolom Longitude/Latitude,
        sudah dikoreksi. Peta memakai OpenStreetMap; tautan **Google Maps** per SPBU
        disediakan untuk verifikasi. Geocoding massal ke Google Maps membutuhkan API key.

        **Dua preferensi:** Blue Ocean direkomendasikan untuk mitra NFR; Red Ocean
        tetap disediakan sebagai pembanding karena praktik lapangan sering memilih
        area yang sudah ramai.
        """
    )
