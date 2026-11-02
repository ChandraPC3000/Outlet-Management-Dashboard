# NFR Izin Prinsip Dashboard

Dashboard **Streamlit** untuk menganalisis data pengajuan **Izin Prinsip** tenant
Non-Fuel Retail (NFR) di SPBU Pertamina.

## Fitur

- **Home** — ringkasan seluruh dataset: jumlah pengajuan, SPBU, tenant, nilai sewa,
  sebaran region, komposisi status, top kategori, dan tren pengajuan per bulan.
- **Director Summary** — analisis per nomor SPBU: lokasi operasional, KPI
  (tenant, sewa, SLA, brand), grafik sewa per brand, status pengajuan, tabel
  detail, dan unduh CSV.
- **Data Explorer** — filter Region, Kategori, Status, Tipe Brand, kata kunci
  tenant/brand, dan rentang tanggal pengajuan; lengkap dengan visualisasi, tabel,
  ringkasan per region/kategori, serta unduh CSV.
- Pencarian nomor SPBU pada panel filter (4.887 pilihan tetap mudah dicari).
- Data dibaca sekali lalu di-cache, sehingga navigasi antar halaman tetap cepat.
- Pesan error yang jelas bila file Excel hilang atau kolomnya berubah.

## Struktur proyek

```
app.py                          # entry point: page config, CSS, navigasi
src/
├── config.py                   # path file, kolom wajib, palet warna
├── data_loader.py              # baca + bersihkan Excel (cached)
├── filters.py                  # panel filter sidebar
├── formatting.py               # format rupiah/angka/tanggal
├── charts.py                   # builder grafik Plotly
└── pages/
    ├── home.py
    ├── director_summary.py
    └── data_explorer.py
assets/
├── style.css                   # tema gelap
└── logo.png
.streamlit/config.toml          # tema & konfigurasi server
Data/
└── Pengajuan NFR Izin Prinsip 10-April-2026.xlsx
```

## Menjalankan lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

Aplikasi terbuka di <http://localhost:8501>. Dataset dibaca dari
`Data/Pengajuan NFR Izin Prinsip 10-April-2026.xlsx`, jadi jalankan perintah di
root repo (bukan dari dalam folder `src/`).

## Format data

File Excel dibaca dari sheet pertama dengan kolom berikut:

| Kolom | Keterangan |
| --- | --- |
| `Tgl Pengajuan` | Tanggal & jam pengajuan |
| `ID Pengajuan` | ID unik pengajuan (bisa berulang pada data mentah) |
| `No. SPBU` | Nomor SPBU, dinormalisasi menjadi teks tanpa `.0` |
| `Region`, `Provinsi`, `Kab./Kota` | Lokasi outlet |
| `Nama Tenant`, `Nama Brand`, `Tipe Brand` | Identitas tenant |
| `Kategori`, `Sub Kategori` | Kategori NFR |
| `Total Harga Sewa`, `Nominal Fee` | Nilai kontrak (Rp) |
| `Tgl Mulai/Akhir Sewa Lahan`, `Tgl Berakhir Izin Prinsip`, `Batas` | Tanggal kontrak & tenggat |
| `Tahapan`, `Status`, `SLA` | Progres pengajuan |

Kolom wajib didefinisikan di `src/config.py`. Bila ada kolom yang hilang,
aplikasi berhenti dengan daftar kolom yang tidak ditemukan.

## Catatan kualitas data

- Sebagian `ID Pengajuan` duplikat (25.109 baris, 22.501 ID unik). Data **tidak**
  dideduplikasi otomatis agar angka tetap sesuai sumber.
- `Total Harga Sewa` kosong di 100 baris dan diperlakukan sebagai 0.
- `SLA` mayoritas bernilai 0.
- Dataset berisi data operasional; pertimbangkan ulang sebelum repo dijadikan
  publik.

## Deployment

Cocok untuk Streamlit Community Cloud / Codespaces. Repo sudah menyertakan
`.devcontainer/devcontainer.json` (Python 3.11, port 8501). Saat deploy, pilih
`app.py` sebagai main file dan biarkan `requirements.txt` terpasang otomatis.
