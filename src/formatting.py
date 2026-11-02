"""Helper format angka, rupiah, dan tanggal dengan gaya Indonesia."""

from __future__ import annotations

import pandas as pd

BULAN_SINGKAT = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)


def format_tanggal(value, kosong: str = "-") -> str:
    """Format tanggal menjadi mis. `10 Apr 2026`."""
    if value is None or pd.isna(value):
        return kosong
    try:
        return f"{value.day:02d} {BULAN_SINGKAT[value.month - 1]} {value.year}"
    except (AttributeError, IndexError, TypeError):
        return str(value)


def format_angka(value: float | int | None, desimal: int = 0) -> str:
    """Format angka dengan pemisah ribuan titik, mis. 25.109."""
    if value is None:
        return "-"
    try:
        teks = f"{float(value):,.{desimal}f}"
    except (TypeError, ValueError):
        return str(value)
    return teks.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")


def format_rupiah(value: float | int | None, singkat: bool = True) -> str:
    """Format nilai rupiah, mis. Rp 517,12 M / Rp 20,0 Jt / Rp 750,0 rb."""
    if value is None:
        return "-"
    try:
        angka = float(value)
    except (TypeError, ValueError):
        return str(value)

    tanda = "-" if angka < 0 else ""
    angka = abs(angka)

    if singkat:
        for pembagi, satuan, desimal in (
            (1_000_000_000_000, " T", 2),
            (1_000_000_000, " M", 2),
            (1_000_000, " Jt", 1),
            (1_000, " rb", 1),
        ):
            if angka >= pembagi:
                return f"{tanda}Rp {format_angka(angka / pembagi, desimal)}{satuan}"

    return f"{tanda}Rp {format_angka(angka)}"


def format_hari(value: float | int | None) -> str:
    """Format durasi hari, mis. 0,3 hari."""
    if value is None:
        return "-"
    try:
        return f"{format_angka(float(value), 1)} hari"
    except (TypeError, ValueError):
        return str(value)
