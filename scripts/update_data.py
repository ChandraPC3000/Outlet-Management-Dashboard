"""Salin tiga file NFR terbaru ke folder Data/ dan bangun ulang lead time.

Contoh pemakaian (Windows PowerShell):

    python scripts/update_data.py --source "C:\\Users\\acer\\Downloads"
    python scripts/update_data.py --source "C:\\Users\\acer\\Downloads" --push

File yang dicari (tanggal pada nama menentukan versi terbaru):
- Pengajuan NFR Izin Prinsip <tanggal>.xlsx
- NFR Master Lahan <tanggal>.xlsx
- Pengajuan NFR Sewa Lahan <tanggal>.xlsx
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, _tanggal_dari_nama  # noqa: E402

POLA = {
    "Pengajuan NFR Izin Prinsip": "Pengajuan NFR Izin Prinsip *.xlsx",
    "NFR Master Lahan": "NFR Master Lahan *.xlsx",
    "Pengajuan NFR Sewa Lahan": "Pengajuan NFR Sewa Lahan *.xlsx",
}


def _pilih_terbaru(folder: Path, awalan: str) -> Path:
    kandidat = [
        p
        for p in folder.glob(f"{awalan} *.xlsx")
        if p.is_file() and _tanggal_dari_nama(p) is not None
    ]
    if not kandidat:
        raise SystemExit(
            f"Tidak menemukan '{awalan} <tanggal>.xlsx' di {folder}. "
            "Unduh file terbaru terlebih dahulu atau ganti --source."
        )
    return max(kandidat, key=lambda p: (_tanggal_dari_nama(p) or date.min, p.name))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path.home() / "Downloads",
        help="Folder tempat file baru diunduh (default: ~/Downloads).",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit dan push perubahan Data/ ke origin main setelah update.",
    )
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"Folder sumber tidak ditemukan: {source}")

    dipilih = {awalan: _pilih_terbaru(source, awalan) for awalan in POLA}
    tanggal = max(_tanggal_dari_nama(p) for p in dipilih.values())
    print(f"Sumber : {source}")
    print(f"Tanggal: {tanggal:%d %B %Y}")

    for awalan, path in dipilih.items():
        for lama in DATA_DIR.glob(POLA[awalan]):
            if lama.name != path.name:
                lama.unlink()
        tujuan = DATA_DIR / path.name
        shutil.copy2(path, tujuan)
        print(f"  + {tujuan.name} ({tujuan.stat().st_size / 1e6:.2f} MB)")

    print("Membangun ulang Data Lead Time NFR.xlsx ...")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_lead_time.py")],
        cwd=ROOT,
        check=True,
    )

    if not args.push:
        print("\nSelesai. Jalankan dengan --push untuk commit & push otomatis.")
        return

    pesan = f"data: update NFR {tanggal:%d-%B-%Y}"
    subprocess.run(["git", "add", "Data"], cwd=ROOT, check=True)
    commit = subprocess.run(["git", "commit", "-m", pesan], cwd=ROOT)
    if commit.returncode != 0:
        print("Tidak ada perubahan untuk di-commit.")
        return
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
    print("Selesai: Data/ sudah di-commit dan di-push ke origin/main.")


if __name__ == "__main__":
    main()
