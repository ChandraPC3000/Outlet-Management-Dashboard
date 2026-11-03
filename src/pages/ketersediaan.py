"""Halaman Ketersediaan Lahan: daftar lahan siap tawarkan ke mitra."""

from __future__ import annotations

import streamlit as st

from src import analytics as an
from src import charts
from src.config import KETERSEDIAAN_SNAPSHOT
from src.data_loader import load_ketersediaan_or_stop
from src.exports import KOLOM_MITRA, build_ketersediaan_excel
from src.formatting import format_angka
from src.spbu_universe import load_spbu_universe, universe_ringkasan

df_semua = load_ketersediaan_or_stop()
df = an.prepare_ketersediaan(df_semua)
universe = universe_ringkasan(load_spbu_universe())


@st.cache_data(show_spinner="Menyiapkan file Excel...")
def _excel_cached(data: object, deskripsi: str) -> bytes:
    return build_ketersediaan_excel(data, deskripsi)


st.title("🧭 Ketersediaan Lahan NFR")
st.caption(
    f"Daftar lahan **tersedia** untuk mitra yang mencari lokasi outlet baru di SPBU · "
    f"snapshot {KETERSEDIAAN_SNAPSHOT}."
)

st.info(
    "Kolom **harga sewa, tipe SPBU, kelas SPBU, GES, dan fasilitas EV tidak ditampilkan** "
    "(classified). Nomor PIC diambil dari *List Lembaga Penyalur 13 Oktober 2026*: "
    "kolom T (owner/manager) dan kolom V (kantor SPBU).",
    icon="🔒",
)

with st.expander("🔎 Filter lahan tersedia", expanded=True):
    f1, f2, f3 = st.columns(3)

    def _clear_kota() -> None:
        st.session_state.pop("ket_kota", None)

    provinsi = f1.multiselect(
        "Provinsi",
        sorted(df["Provinsi"].dropna().unique()),
        key="ket_prov",
        on_change=_clear_kota,
    )
    opsi_kota = sorted(
        df.loc[df["Provinsi"].isin(provinsi), "Kota/Kab"].dropna().unique()
    ) if provinsi else sorted(df["Kota/Kab"].dropna().unique())
    kota = f2.multiselect("Kota/Kab", opsi_kota, key="ket_kota")
    road = f3.multiselect(
        "Road Type", sorted(df["Road Type"].dropna().unique()), key="ket_road"
    )

    f4, f5, f6 = st.columns(3)
    ses = f4.multiselect(
        "SES Dominan",
        ["High", "Medium High", "Medium Low", "Low", "Tidak diketahui"],
        key="ket_ses",
    )
    min_luas = f5.number_input(
        "Luas minimum (m²)", min_value=0.0, value=0.0, step=10.0, key="ket_min_luas"
    )
    cari = f6.text_input(
        "Cari No SPBU / perusahaan / alamat",
        placeholder="contoh: Indomaret atau 3416421",
        key="ket_cari",
    )

    f7, f8, f9 = st.columns(3)
    hanya_pic = f7.checkbox("Hanya SPBU dengan PIC lengkap", value=False, key="ket_pic")
    tanpa_nol = f8.checkbox("Kecualikan lahan 0 m²", value=True, key="ket_nol")
    min_volume = f9.number_input(
        "Volume minimum (KL/bln)", min_value=0.0, value=0.0, step=1000.0, key="ket_volume"
    )

tampil = df.copy()
if provinsi:
    tampil = tampil[tampil["Provinsi"].isin(provinsi)]
if kota:
    tampil = tampil[tampil["Kota/Kab"].isin(kota)]
if road:
    tampil = tampil[tampil["Road Type"].isin(road)]
if ses:
    tampil = tampil[tampil["SES Dominan"].isin(ses)]
if min_luas > 0:
    tampil = tampil[tampil["Luas (M2)"] >= min_luas]
if cari.strip():
    kata = cari.strip()
    cocok = tampil["No. SPBU"].astype("string").str.contains(kata, case=False, na=False, regex=False)
    for kolom in ("Nama Perusahaan", "Alamat", "Kota/Kab", "Kecamatan"):
        cocok |= tampil[kolom].astype("string").str.contains(kata, case=False, na=False, regex=False)
    tampil = tampil[cocok]
if hanya_pic:
    tampil = tampil[tampil["PIC Lengkap"]]
if min_volume > 0:
    tampil = tampil[tampil["Total"].fillna(0) >= min_volume]

jumlah_nol = int((tampil["Luas (M2)"] <= 0).sum())
if tanpa_nol:
    tampil = tampil[tampil["Luas (M2)"] > 0]

if tampil.empty:
    st.warning("Tidak ada lahan yang cocok dengan filter. Longgarkan filter lalu coba lagi.")
    st.stop()

kpi = an.ketersediaan_kpi(tampil)
baris1 = st.columns(4)
baris1[0].metric("Lahan Tersedia", format_angka(kpi["lahan"]))
baris1[1].metric("SPBU dengan Lahan Tersedia", format_angka(kpi["spbu"]))
baris1[2].metric("Provinsi", format_angka(kpi["provinsi"]))
baris1[3].metric("Total Luas", f"{format_angka(kpi['luas'])} m²")

baris2 = st.columns(4)
baris2[0].metric("Median Luas", f"{format_angka(kpi['median_luas'], 1)} m²")
baris2[1].metric("Total Volume", f"{format_angka(kpi['volume'])} KL/bln")
baris2[2].metric("Rerata Volume/SPBU", f"{format_angka(kpi['rerata_volume'])} KL/bln")
baris2[3].metric("PIC Lengkap", f"{format_angka(kpi['pic_lengkap'], 1)}%")

st.caption(
    f"dari **{format_angka(universe['total'])} total SPBU universe** "
    f"({format_angka(universe['reguler'])} Reguler + "
    f"{format_angka(universe['existing_ekstra'])} existing); KPI SPBU menghitung outlet "
    "yang memiliki lahan tersedia pada filter ini."
)

if tanpa_nol and jumlah_nol:
    st.caption(f"{format_angka(jumlah_nol)} lahan berluas 0 m² disembunyikan oleh filter.")
if hanya_pic:
    st.caption(
        "Filter PIC lengkap aktif: hanya SPBU yang punya nomor owner/manager dan nomor kantor."
    )

st.divider()

ringkasan = an.ketersediaan_ringkasan(tampil)
spbu = an.volume_per_spbu(tampil)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("🗺️ Top 10 Provinsi")
    st.plotly_chart(charts.top_provinsi_lahan(ringkasan), use_container_width=True)
with kanan:
    st.subheader("🛣️ Road Type")
    st.plotly_chart(charts.road_type_bar(tampil), use_container_width=True)

kiri, kanan = st.columns(2)
with kiri:
    st.subheader("📊 SES Dominan")
    st.plotly_chart(charts.ses_bar(tampil), use_container_width=True)
with kanan:
    st.subheader("⛽ Top 10 SPBU by Volume")
    st.plotly_chart(charts.volume_spbu_bar(spbu), use_container_width=True)

st.subheader("📐 Distribusi Luas Lahan")
st.plotly_chart(charts.luas_bar(an.luas_kategori(tampil)), use_container_width=True)

st.divider()

st.subheader("📑 Daftar Lahan untuk Mitra")
st.caption(
    f"{format_angka(len(tampil))} lahan · {format_angka(tampil['No. SPBU'].nunique())} SPBU · "
    "kolom classified tidak ditampilkan."
)

kolom_tabel = [k for k in KOLOM_MITRA if k in tampil.columns]
tabel = tampil.loc[:, kolom_tabel].rename(columns={"No. SPBU": "No SPBU"})
st.dataframe(
    tabel,
    hide_index=True,
    use_container_width=True,
    height=480,
    column_config={
        "Luas (M2)": st.column_config.NumberColumn("Luas (m²)", format="%.2f"),
        "Latitude": st.column_config.NumberColumn(format="%.6f"),
        "Longitude": st.column_config.NumberColumn(format="%.6f"),
        "PSO": st.column_config.NumberColumn(format="%.2f"),
        "Non PSO": st.column_config.NumberColumn(format="%.2f"),
        "Total": st.column_config.NumberColumn(format="%.2f"),
        "PSO2": st.column_config.NumberColumn(format="%.2f"),
        "Non PSO2": st.column_config.NumberColumn(format="%.2f"),
        "Total2": st.column_config.NumberColumn(format="%.2f"),
    },
)

deskripsi_filter = []
if provinsi:
    deskripsi_filter.append("Provinsi: " + ", ".join(provinsi))
if kota:
    deskripsi_filter.append("Kota/Kab: " + ", ".join(kota))
if road:
    deskripsi_filter.append("Road Type: " + ", ".join(road))
if ses:
    deskripsi_filter.append("SES Dominan: " + ", ".join(ses))
if min_luas:
    deskripsi_filter.append(f"Luas minimum: {min_luas:,.0f} m²".replace(",", "."))
if min_volume:
    deskripsi_filter.append(f"Volume minimum: {min_volume:,.0f} KL/bln".replace(",", "."))
if cari.strip():
    deskripsi_filter.append(f"Pencarian: {cari.strip()}")
if hanya_pic:
    deskripsi_filter.append("Hanya PIC lengkap")
if tanpa_nol:
    deskripsi_filter.append("Kecualikan luas 0 m²")
filter_desc = "; ".join(deskripsi_filter)

unduh1, unduh2 = st.columns(2)
with unduh1:
    st.download_button(
        "⬇️ Unduh Excel (format mitra)",
        data=_excel_cached(tampil, filter_desc),
        file_name="Ketersediaan Lahan NFR - November 2026.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="unduh_ketersediaan_xlsx",
    )
with unduh2:
    st.download_button(
        "⬇️ Unduh CSV",
        data=tabel.to_csv(index=False).encode("utf-8-sig"),
        file_name="Ketersediaan Lahan NFR - November 2026.csv",
        mime="text/csv",
        use_container_width=True,
        key="unduh_ketersediaan_csv",
    )

with st.expander("ℹ️ Tentang data & format unduhan", expanded=False):
    st.markdown(
        """
        - **Sumber:** `Ketersediaan Lahan NFR - November 2026.xlsx` (hanya baris
          `Status Sewa = Tersedia`).
        - **Duplikat:** satu kode lahan yang terdiri dari beberapa pecahan luas
          digabung menjadi satu baris; luasnya dijumlahkan.
        - **PIC:** `Kontak PIC SPBU` = nomor owner/manager (kolom T *List Lembaga
          Penyalur 13 Oktober 2026*), `No Kantor SPBU` = nomor kantor (kolom V).
        - **Format unduhan:** mengikuti contoh *Buat Momoyo* — header biru, grup
          `Volume (KL) / Month` dan `Transaksi / Month`, freeze pane, autofilter,
          plus lembar **Catatan**.
        - **Tidak pernah diekspor:** harga sewa, tipe SPBU, kelas SPBU, GES,
          fasilitas EV.
        - **Volume** adalah volume SPBU, bukan per lahan; angka pada beberapa lahan
          di SPBU yang sama akan berulang.
        """
    )
