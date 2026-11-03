# NFR Analytics Pro

Dashboard **Streamlit** untuk memantau ekosistem Non-Fuel Retail (NFR) di SPBU
Pertamina: pengajuan **Izin Prinsip**, **Master Lahan**, **Sewa Lahan**,
**occupancy rate**, **nilai sewa**, **management fee**, **lead time** perizinan,
dan **ketersediaan lahan** untuk mitra.

Snapshot data: **2 November 2026** · Ketersediaan lahan: **November 2026**.

## Halaman & analisis

| Halaman | Yang bisa dilihat |
| --- | --- |
| **🏠 Home** | KPI lintas dataset (46.003 pengajuan, 5.616 SPBU, occupancy lahan 83,1%, nilai sewa lahan Rp 1,20 T), funnel tahapan, komposisi status, occupancy per region, tren pengajuan bulanan, jadwal kontrak berakhir, nilai sewa per kategori |
| **📊 Director Summary** | Analisis satu SPBU: lokasi, KPI izin, sewa per brand, status pengajuan, lahan & kontrak sewa outlet tersebut, aging/lead time, dan detail lengkap |
| **🔎 Data Explorer** | Telusuri seluruh pengajuan izin dengan filter Region, Kategori, Status, Tipe Brand, kata kunci, dan rentang tanggal; unduh CSV |
| **🧭 Ketersediaan Lahan** | Daftar lahan tersedia untuk mitra: filter provinsi/kota/road type/SES/luas/volume/PIC, analisis sebaran, dan unduh Excel format mitra |
| **📈 Occupancy Rate** | Persentase lahan tersewa per SPBU (tersewa ÷ (tersewa + tersedia)), gauge, sebaran SPBU penuh/sebagian/kosong, occupancy per Region/Provinsi/Kab-Kota, heatmap, scatter, top/bottom SPBU |
| **💰 Nilai Sewa** | Nilai sewa per Region/Provinsi/Kab-Kota, kategori, sub kategori, tipe brand, brand, status, top SPBU, heatmap kategori × tipe brand, dan tren bulanan |
| **💳 Management Fee** | `Nominal Fee` per wilayah, kategori, tipe brand, brand, status, top SPBU, heatmap, tren bulanan, sebaran nilai fee, dan rasio fee terhadap harga sewa |
| **🗺️ LOKASI Intelligence** | Peta GIS SPBU + BVT Red/Blue Ocean, skor peluang, kategori pesaing/peluang, filter Reguler/Non-Reguler, tipe SPBU, wilayah, road type, SES, dan tautan Google Maps |
| **🏞️ Lahan & Sewa** | Occupancy lahan per region, status approval, top tenant by nilai sewa, sebaran luas vs harga, kontrak sewa berjalan, jadwal berakhir 12 bulan, nilai sewa per kategori/tipe brand |
| **⏱️ Lead Time** | Funnel tahapan, aging pending per tahap/status, kepatuhan SLA (`Batas`), pending per region, daftar pending terlama, unduh CSV |

## Dataset

File yang dibaca aplikasi ada di folder `Data/`:

| File | Baris | Isi utama |
| --- | ---: | --- |
| `Pengajuan NFR Izin Prinsip 02-November-2026.xlsx` | 46.003 | 43.447 ID unik, 15 status, tahapan, SLA, nilai sewa |
| `NFR Master Lahan 02-November-2026.xlsx` | 35.845 | 32.837 lahan, 5.965 SPBU, status sewa & approval, luas, harga sewa |
| `Pengajuan NFR Sewa Lahan 02-November-2026.xlsx` | 26.704 | 21.091 kontrak berjalan, status izin, periode & nilai sewa |
| `Data Lead Time NFR 02112026.xlsx` | 10 sheet | Resume, funnel, aging per tahap/status, detail pending, dataset turunan, metodologi |
| `Ketersediaan Lahan NFR - November 2026.xlsx` | 5.732 | Lahan tersedia + PIC (sanitized, tanpa kolom classified) |
| `spbu_master.csv` | 15.103 | Master SPBU dari List Lembaga Penyalur: jenis lembaga, tipe SPBU, wilayah, koordinat (tanpa PIC) |
| `bvt_spbu.csv` | 6.787 | BVT 34 provinsi: Red/Blue Ocean, skor, kelas, road type, SES, koordinat |

## Occupancy rate

Halaman **📈 Occupancy Rate** menghitung per SPBU:

```
Occupancy (%) = lahan tersewa ÷ (lahan tersewa + lahan tersedia) × 100
```

- Hanya lahan berstatus `Tersewa`/`Tersedia` yang masuk perhitungan; status lain
  tidak masuk pembilang maupun penyebut.
- Agregasi Region/Provinsi/Kab-Kota memakai **weighted** (total tersewa ÷ total
  lahan di wilayah itu), bukan rata-rata persentase. Rata-rata per SPBU
  ditampilkan terpisah sebagai pembanding.
- Default agregasi **Region**; filter wilayah bertingkat Region → Provinsi →
  Kab./Kota.
- Visual: gauge occupancy total, donut SPBU penuh/sebagian/kosong, bar per
  wilayah, heatmap distribusi occupancy, scatter total lahan vs occupancy, serta
  top/bottom 10 SPBU (dengan ambang minimum total lahan).
- Snapshot: 5.916 SPBU, occupancy weighted **83,1%**, rata-rata per SPBU 82,3%;
  3.070 SPBU penuh dan 470 SPBU di bawah 50%.

## Nilai sewa & management fee

**💰 Nilai Sewa** memakai `Total Harga Sewa` dari Pengajuan Sewa Lahan dan
menyediakan analisis per wilayah (Region/Provinsi/Kab-Kota), kategori, sub
kategori, tipe brand (`Jenis Brand`), brand, status sewa/izin, top SPBU,
heatmap kategori × tipe brand, dan tren nilai sewa per bulan mulai. Total nilai
sewa: **Rp 1,19 T** dari 26.704 kontrak.

**💳 Management Fee** memakai `Nominal Fee` dari Pengajuan Izin Prinsip dengan
dimensi yang sama: wilayah, kategori, tipe brand, brand, status, tahapan, top
SPBU, heatmap kategori × tipe brand, tren bulanan, serta sebaran nilai fee.
- Total fee: **Rp 53,53 M** dari 21.472 transaksi ber-fee.
- 24.531 pengajuan bernilai fee 0; tidak dihitung sebagai transaksi ber-fee,
  tetapi total fee tetap dihitung dari seluruh baris.
- `Fee Ratio (%) = Nominal Fee ÷ Total Harga Sewa × 100`; hanya indikasi karena
  rasio bisa ekstrem saat harga sewa 0.

## LOKASI Intelligence, master & BVT

Halaman **🗺️ LOKASI Intelligence** menggabungkan master SPBU, BVT 34 provinsi,
dan peta.

**Master SPBU** (`spbu_master.csv`) berasal dari *List Lembaga Penyalur
13 Oktober 2026*:
- 15.103 SPBU; **6.525 SPBU Reguler**; sisanya PERTASHOP, SPBU Kompak, Mini,
  Modular, SPBUN, SPBB, AMT, dan SPBU T.
- `Tipe SPBU` dinormalisasi: COCO, CODO, DODO; varian `CODO I`, `CODO II`,
  `CODO Lite` dilebur menjadi `CODO`.
- Nomor PIC/email/telepon **tidak** disertakan di master yang di-commit.

**Enrichment otomatis:** semua loader (Izin Prinsip, Master Lahan, Sewa Lahan,
Ketersediaan Lahan) mengisi kolom kosong/`#N/A`/`-`/`NULL` dari master:
Provinsi, Kota/Kabupaten, Kecamatan, Desa/Kelurahan, Alamat, Latitude, Longitude,
Nama SPBU, Jenis Lembaga Penyalur, Tipe SPBU, dan flag Reguler. Nilai yang sudah
ada tidak ditimpa.

**BVT** (`bvt_spbu.csv`) dari *SPBU_All_34_Provinces_20261016*:
- 6.787 SPBU, 34 provinsi; Red Ocean 3.176, Blue Ocean 2.517, Peluang Campuran
  1.094.
- **Red Ocean** = bisnis sekitar yang sudah jenuh/banyak pesaing; **Blue Ocean**
  = kategori usaha yang masih minim pesaing.
- `Blue Ocean Score (%) = Blue Count ÷ (Red Count + Blue Count) × 100`;
  ≥50 Blue Ocean, 1–49 Peluang Campuran, 0 Red Ocean.
- Rekomendasi utama untuk mitra adalah **Blue Ocean**; **Red Ocean** tetap
  disediakan sebagai pilihan praktik lapangan/owner.
- Cakupan default **Reguler** (6.525 SPBU), bisa diganti **Semua** atau
  **Non-Reguler**.

**Peta & tilok:** peta memakai **Folium + tile OpenStreetMap** (marker cluster).
Saat zoom out (≤5) hanya tampil **8 lingkaran besar per region** (Sumbagut s/d
Maluku Papua) dengan label dan komposisi BVT; zoom in menampilkan titik/cluster
SPBU. Koordinat diambil dari master Lembaga Penyalur; jika tidak valid, fallback
ke BVT. Kolom Longitude/Latitude pada file BVT asli tertukar dan sudah dikoreksi.
Setiap SPBU punya tautan **Google Maps** (`https://www.google.com/maps?q=lat,lon`)
untuk verifikasi. Geocoding massal ke Google Maps membutuhkan API key.

## Ketersediaan lahan untuk mitra

Halaman **🧭 Ketersediaan Lahan** dipakai saat mitra meminta daftar lahan NFR
yang masih tersedia untuk outlet baru.

- **Sumber:** `Ketersediaan Lahan NFR - November 2026.xlsx` (hanya
  `Status Sewa = Tersedia`), 5.732 lahan di 2.846 SPBU.
- **Duplikat:** satu `Kode Lahan` yang terdiri dari beberapa pecahan luas
  digabung menjadi satu baris; luasnya dijumlahkan (total luas tidak berubah).
- **PIC lengkap:** `Kontak PIC SPBU` = nomor owner/manager (kolom **T** *List
  Lembaga Penyalur 13 Oktober 2026*), `No Kantor SPBU` = nomor kantor (kolom
  **V**). Tersedia untuk 5.678 baris (98,6% SPBU).
- **Lahan 0 m²** disembunyikan secara default (149 baris) dan bisa dimunculkan
  lewat checkbox filter.
- **Kolom classified tidak pernah ditampilkan/diekspor:** harga sewa, tipe
  SPBU, kelas SPBU, GES, dan fasilitas EV.

**Format unduhan** mengikuti contoh `Ketersediaan Lahan NFR Buat Momoyo -
November 2026.xlsx`: header biru di baris 4, grup `Volume (KL) / Month` dan
`Transaksi / Month` di baris 3, autofilter, freeze pane, plus sheet **Catatan**.
Filter yang aktif di halaman ikut diterapkan ke file yang diunduh.

> **Privasi:** nomor PIC dan data lokasi ikut tampil di aplikasi publik. File
> mentah yang memuat kolom classified **tidak** di-commit; yang masuk repo hanya
> versi sanitized. Pertimbangkan repo/app privat atau autentikasi bila nomor PIC
> tidak boleh diakses publik.

## Struktur proyek

```
app.py                          # page config, CSS, navigasi (st.navigation)
src/
├── config.py                   # path dataset, kolom wajib, palet warna
├── data_loader.py              # load + validasi + cache seluruh dataset
├── analytics.py                # lead time, lahan, sewa, ketersediaan, PIC
├── master_data.py              # master SPBU, BVT, enrichment kolom kosong
├── charts.py                   # builder grafik Plotly
├── filters.py                  # filter sidebar
├── formatting.py               # format rupiah/angka/tanggal
├── exports.py                  # export Excel format mitra (XlsxWriter)
└── pages/
    ├── home.py
    ├── director_summary.py
    ├── data_explorer.py
    ├── ketersediaan.py
    ├── occupancy.py
    ├── lahan_sewa.py
    ├── nilai_sewa.py
    ├── management_fee.py
    ├── lokasi.py
    └── lead_time.py
scripts/
├── build_lead_time.py          # regenerasi file lead time Excel
├── build_ketersediaan.py       # sanitasi + gabung PIC ketersediaan lahan
└── build_lokasi.py             # master SPBU + dataset BVT
tests/smoke_test.py             # smoke test AppTest
Data/                           # dataset yang dipakai aplikasi
assets/style.css                # tema gelap
```

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka <http://localhost:8501>. Jalankan dari root repo agar path `Data/` benar.

### Regenerasi file turunan

```bash
python scripts/build_lead_time.py
python scripts/build_ketersediaan.py
```

`build_ketersediaan.py` membutuhkan dua file mentah lokal (tidak di-commit):
`Ketersediaan Lahan NFR - November 2026.xlsx` dan `List Lembaga Penyalur
13 Oktober 2026.xlsx`. Output-nya adalah versi sanitized di `Data/`.

### Smoke test

```bash
python tests/smoke_test.py
```

Menjalankan 10 halaman lewat `streamlit.testing.v1.AppTest` (tanpa browser),
termasuk uji kolom classified tidak bocor, rumus occupancy, master/BVT, dan
struktur file Excel mitra.

## Metodologi lead time

Dataset pengajuan **tidak memuat timestamp transisi tahap** (SBM, SAM, MS3,
management fee, invoice). Karena itu:

- **Lead time berjalan (aging)** = tanggal snapshot − `Tgl Pengajuan`.
- **Status → tahap**: `Menunggu Verifikasi SBM/SAM` → Verifikasi Dokumen;
  `Menunggu Verifikasi MS3` → Verifikasi MS3; `Menunggu Pembayaran`, `Input
  Nominal`, `Revisi Pembayaran`, `Menunggu Verifikasi` → Management Fee;
  `Verifikasi Pembayaran` → Pembayaran Invoice; `Terbit` → Penerbitan.
- **SLA/Batas** hanya tersedia untuk 717 baris.
- Lead time antar tahap sebagai selisih tanggal masuk-keluar tahap **tidak bisa**
  dihitung dari file ini. Jika tersedia export mentah workflow November (sheet
  `Dataset`, `Verifikasi SBM/SAM/MS3`, `Pembayaran`), analisis tahap penuh dapat
  dibuat seperti versi 22 Oktober 2026.

## Catatan kualitas data

- 4.222 baris memiliki `ID Pengajuan` duplikat (umumnya re-submission/revisi
  brand) — tidak dihapus otomatis.
- 14.732 baris `Total Harga Sewa` = 0; 7.662 izin tanpa `Tgl Berakhir Izin Prinsip`.
- 45.286 baris `SLA` = 0.
- 544 baris Master Lahan tidak bisa dipetakan ke region karena `No. SPBU` tidak
  ada di dataset pengajuan.
- Ketersediaan lahan: 54 baris tanpa nomor PIC; 149 lahan berluas 0 m².
- Dataset berisi data operasional; pertimbangkan ulang sebelum repo dijadikan
  publik.

## Deployment

Cocok untuk Streamlit Community Cloud / Codespaces (devcontainer Python 3.11,
port 8501). Pilih `app.py` sebagai main file; dependency terpasang dari
`requirements.txt`.
