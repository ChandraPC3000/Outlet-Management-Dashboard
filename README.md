# NFR Analytics Pro

Dashboard **Streamlit** untuk memantau ekosistem Non-Fuel Retail (NFR) di SPBU
Pertamina: pengajuan **Izin Prinsip**, **Master Lahan**, **Sewa Lahan**, dan
**lead time** proses perizinan.

Snapshot data: **2 November 2026**.

## Halaman & analisis

| Halaman | Yang bisa dilihat |
| --- | --- |
| **🏠 Home** | KPI lintas dataset (46.003 pengajuan, 5.616 SPBU, occupancy lahan 83,1%, nilai sewa lahan Rp 1,20 T), funnel tahapan, komposisi status, occupancy per region, tren pengajuan bulanan, jadwal kontrak berakhir, nilai sewa per kategori |
| **📊 Director Summary** | Analisis satu SPBU: lokasi, KPI izin, sewa per brand, status pengajuan, lahan & kontrak sewa outlet tersebut, aging/lead time, dan detail lengkap |
| **🔎 Data Explorer** | Telusuri seluruh pengajuan izin dengan filter Region, Kategori, Status, Tipe Brand, kata kunci, dan rentang tanggal; unduh CSV |
| **🏞️ Lahan & Sewa** | Occupancy lahan per region, status approval, top tenant by nilai sewa, sebaran luas vs harga, kontrak sewa berjalan, jadwal berakhir 12 bulan, nilai sewa per kategori/brand |
| **⏱️ Lead Time** | Funnel tahapan, aging pending per tahap/status, kepatuhan SLA (`Batas`), pending per region, daftar pending terlama, unduh CSV |

## Dataset

Semua file ada di folder `Data/` dan dibaca otomatis:

| File | Baris | Isi utama |
| --- | ---: | --- |
| `Pengajuan NFR Izin Prinsip 02-November-2026.xlsx` | 46.003 | 43.447 ID unik, 15 status, tahapan, SLA, nilai sewa |
| `NFR Master Lahan 02-November-2026.xlsx` | 35.845 | 32.837 lahan, 5.965 SPBU, status sewa & approval, luas, harga sewa |
| `Pengajuan NFR Sewa Lahan 02-November-2026.xlsx` | 26.704 | 21.091 kontrak berjalan, status izin, periode & nilai sewa |
| `Data Lead Time NFR 02112026.xlsx` | 10 sheet | Resume, funnel, aging per tahap/status, detail pending, dataset turunan, metodologi |

## Struktur proyek

```
app.py                          # page config, CSS, navigasi (st.navigation)
src/
├── config.py                   # path dataset, kolom wajib, palet warna
├── data_loader.py              # load + validasi + cache 3 dataset
├── analytics.py                # lead time, lahan, sewa, region mapping
├── charts.py                   # builder grafik Plotly
├── filters.py                  # filter sidebar
├── formatting.py               # format rupiah/angka/tanggal
└── pages/
    ├── home.py
    ├── director_summary.py
    ├── data_explorer.py
    ├── lahan_sewa.py
    └── lead_time.py
scripts/build_lead_time.py      # regenerasi file lead time Excel
tests/smoke_test.py             # smoke test AppTest
Data/                           # 4 file Excel
assets/style.css                # tema gelap
```

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka <http://localhost:8501>. Jalankan dari root repo agar path `Data/` benar.

### Regenerasi file Lead Time

```bash
python scripts/build_lead_time.py
```

Script membaca `Pengajuan NFR Izin Prinsip 02-November-2026.xlsx`, menulis ulang
`Data/Data Lead Time NFR 02112026.xlsx` (Resume, Funnel, Aging per tahap/status,
Pending per region, Detail pending, Top 50 pending terlama, Kualitas data,
Metodologi, Dataset).

### Smoke test

```bash
python tests/smoke_test.py
```

Menjalankan 5 halaman lewat `streamlit.testing.v1.AppTest` (tanpa browser) dan
menguji filter serta pemilihan SPBU.

## Metodologi lead time

Dataset pengajuan **tidak memuat timestamp transisi tahap** (SBM, SAM, MS3,
management fee, invoice). Karena itu:

- **Lead time berjalan (aging)** = tanggal snapshot − `Tgl Pengajuan`. Nilai ini
  menunjukkan berapa lama pengajuan sudah berjalan/tertahan pada tahap saat ini.
- **Status → tahap**: `Menunggu Verifikasi SBM/SAM` → Verifikasi Dokumen;
  `Menunggu Verifikasi MS3` → Verifikasi MS3; `Menunggu Pembayaran`, `Input
  Nominal`, `Revisi Pembayaran`, `Menunggu Verifikasi` → Management Fee;
  `Verifikasi Pembayaran` → Pembayaran Invoice; `Terbit` → Penerbitan.
- **SLA/Batas** hanya tersedia untuk 717 baris, sehingga persentase lewat batas
  dihitung dari subset tersebut.
- Lead time antar tahap sebagai selisih tanggal masuk-keluar tahap **tidak bisa**
  dihitung dari file ini. Jika tersedia export mentah workflow November (sheet
  `Dataset`, `Verifikasi SBM/SAM/MS3`, `Pembayaran`), analisis tahap penuh dapat
  dibuat seperti versi 22 Oktober 2026.

## Catatan kualitas data

- 4.222 baris memiliki `ID Pengajuan` duplikat (umumnya re-submission/revisi
  brand) — tidak dihapus otomatis.
- 14.732 baris `Total Harga Sewa` = 0; 7.662 izin tanpa `Tgl Berakhir Izin Prinsip`.
- 45.286 baris `SLA` = 0 (target SLA hanya terisi pada sebagian pengajuan berjalan).
- 544 baris Master Lahan tidak bisa dipetakan ke region karena `No. SPBU` tidak
  ada di dataset pengajuan.
- Dataset berisi data operasional; pertimbangkan ulang sebelum repo dijadikan
  publik.

## Deployment

Cocok untuk Streamlit Community Cloud / Codespaces (devcontainer Python 3.11,
port 8501). Pilih `app.py` sebagai main file; dependency terpasang dari
`requirements.txt`.
