"""Smoke test ringan tanpa pytest: `python tests/smoke_test.py`.

Memakai `streamlit.testing.v1.AppTest` sehingga UI benar-benar dieksekusi
(tanpa browser) dan exception Streamlit muncul sebagai AssertionError.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

TOTAL_IZIN = "46.003"


def test_ketersediaan_data() -> None:
    from src.config import CLASSIFIED_LAHAN_COLUMNS
    from src.data_loader import load_ketersediaan
    from src.exports import build_ketersediaan_excel

    df = load_ketersediaan()
    assert not set(CLASSIFIED_LAHAN_COLUMNS) & set(df.columns), "kolom classified bocor"
    assert {"Kontak PIC SPBU", "No Kantor SPBU"} <= set(df.columns)
    assert len(df) > 5_000
    assert df["Kontak PIC SPBU"].dropna().astype(str).str.isdigit().all()

    import io

    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(build_ketersediaan_excel(df.head(20))))
    ws = wb["Ketersediaan Lahan"]
    header = [ws.cell(4, c).value for c in range(3, 26)]
    assert "No Kantor SPBU" in header
    assert not set(CLASSIFIED_LAHAN_COLUMNS) & set(header)
    assert [str(m) for m in ws.merged_cells.ranges] == ["T3:V3", "W3:Y3"]
    assert ws.freeze_panes == "T5"
    wb.close()


def _run(page: str) -> AppTest:
    app = AppTest.from_file(str(ROOT / page), default_timeout=240).run()
    assert not app.exception, f"{page} melempar exception: {[e.message for e in app.exception]}"
    assert not app.error, f"{page} menampilkan error: {[e.value for e in app.error]}"
    return app


def test_home() -> None:
    app = _run("src/pages/home.py")
    judul = [t.value for t in app.title]
    assert judul and "NFR Management System" in judul[0], judul
    metrics = {m.label: m.value for m in app.metric}
    assert metrics["Total Pengajuan Izin"] == f"{TOTAL_IZIN} baris", metrics
    assert len(app.get("plotly_chart")) >= 6


def test_director_summary() -> None:
    app = _run("src/pages/director_summary.py")
    assert any("Nomor SPBU" in info.value.replace("**", "") for info in app.info)

    selector = app.selectbox(key="spbu_select")
    assert len(selector.options) > 5_000

    selector.select(selector.options[0]).run()
    assert not app.exception
    headers = [h.value for h in app.header]
    assert any(header.startswith("SPBU ") for header in headers), headers
    assert [t.label for t in app.tabs] == [
        "📊 Izin Prinsip",
        "🏞️ Lahan & Sewa",
        "⏱️ Lead Time",
        "📑 Detail",
    ]

    metrics = {m.label: m.value for m in app.metric}
    assert "Total Tenant" in metrics and "Total Sewa" in metrics, metrics
    assert len(app.get("download_button")) >= 1


def test_data_explorer() -> None:
    app = _run("src/pages/data_explorer.py")
    awal = {m.label: m.value for m in app.metric}
    assert awal["Baris Data"] == TOTAL_IZIN, awal

    region = app.multiselect(key="explorer_region")
    region.select(region.options[0]).run()
    terfilter = {m.label: m.value for m in app.metric}
    assert terfilter["Baris Data"] != TOTAL_IZIN, terfilter

    app.button(key="explorer_reset").click().run()
    reset = {m.label: m.value for m in app.metric}
    assert reset["Baris Data"] == TOTAL_IZIN, reset


def test_lahan_sewa() -> None:
    app = _run("src/pages/lahan_sewa.py")
    assert [t.label for t in app.tabs] == ["🏞️ Master Lahan", "📄 Sewa Lahan"]
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Total Lahan", "Tersewa", "Tersedia", "Occupancy"):
        assert label in metrics, metrics
    assert "Jumlah Kontrak" in metrics, metrics
    assert len(app.get("plotly_chart")) >= 6


def test_lead_time() -> None:
    app = _run("src/pages/lead_time.py")
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Pengajuan Pending", "Median Umur Pending", "Lewat Batas SLA"):
        assert label in metrics, metrics
    assert len(app.get("plotly_chart")) >= 4
    assert len(app.dataframe) >= 2
    assert len(app.get("download_button")) >= 1


def test_ketersediaan_page() -> None:
    app = _run("src/pages/ketersediaan.py")
    judul = [t.value for t in app.title]
    assert judul and "Ketersediaan Lahan" in judul[0], judul
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Lahan Tersedia", "Jumlah SPBU", "Total Luas", "PIC Lengkap"):
        assert label in metrics, metrics
    assert metrics["Lahan Tersedia"] == "5.583", metrics
    assert len(app.get("plotly_chart")) >= 5
    assert len(app.get("download_button")) == 2

    prov = app.multiselect(key="ket_prov")
    prov.select(prov.options[0]).run()
    assert not app.exception
    assert int(app.metric[0].value.replace(".", "")) < 5_732


def test_occupancy_page() -> None:
    app = _run("src/pages/occupancy.py")
    judul = [t.value for t in app.title]
    assert judul and "Occupancy Rate" in judul[0], judul
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Occupancy Total", "Rata-rata per SPBU", "Jumlah SPBU", "Total Lahan"):
        assert label in metrics, metrics
    assert metrics["Occupancy Total"] == "83,1%", metrics
    assert len(app.get("plotly_chart")) >= 6
    assert len(app.dataframe) >= 1

    region = app.multiselect(key="occ_region")
    region.select(region.options[0]).run()
    assert not app.exception
    assert int(app.metric[2].value.replace(".", "")) < 5_916


def test_occupancy_formula() -> None:
    from src import analytics as an
    from src.data_loader import load_izin_prinsip, load_master_lahan

    izin = load_izin_prinsip()
    lahan = an.prepare_lahan(load_master_lahan(), izin)
    occ = an.occupancy_per_spbu(lahan)
    assert len(occ) > 5_000
    assert (occ["Tersewa"] + occ["Tersedia"] == occ["Total Lahan"]).all()
    assert occ["Occupancy (%)"].between(0, 100).all()
    weighted = occ["Tersewa"].sum() / occ["Total Lahan"].sum() * 100
    assert abs(weighted - 83.13) < 0.1, weighted


def test_nilai_sewa_page() -> None:
    app = _run("src/pages/nilai_sewa.py")
    judul = [t.value for t in app.title]
    assert judul and "Nilai Sewa" in judul[0], judul
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Total Nilai Sewa", "Jumlah Kontrak", "Brand Unik"):
        assert label in metrics, metrics
    assert len(app.get("plotly_chart")) >= 8
    assert len(app.dataframe) >= 1
    assert len(app.get("download_button")) >= 1


def test_management_fee_page() -> None:
    app = _run("src/pages/management_fee.py")
    judul = [t.value for t in app.title]
    assert judul and "Management Fee" in judul[0], judul
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Total Management Fee", "Transaksi Ber-fee", "Pengajuan Ber-fee"):
        assert label in metrics, metrics
    assert len(app.get("plotly_chart")) >= 8
    assert len(app.dataframe) >= 1
    assert len(app.get("download_button")) >= 1


def test_master_data() -> None:
    from src.master_data import load_bvt, load_spbu_master

    master = load_spbu_master()
    bvt = load_bvt()
    assert len(master) > 15_000
    assert int(master["Reguler"].sum()) == 6_525
    assert "PIC" not in " ".join(master.columns)
    assert len(bvt) > 6_500
    assert bvt["Latitude"].between(-12, 7).all()
    assert bvt["Longitude"].between(94, 142).all()
    assert set(bvt["Kelas BVT"]).issubset({"Blue Ocean", "Peluang Campuran", "Red Ocean"})
    assert bvt["Blue Ocean Score (%)"].between(0, 100).all()


def test_lokasi_page() -> None:
    app = _run("src/pages/lokasi.py")
    judul = [t.value for t in app.title]
    assert judul and "LOKASI Intelligence" in judul[0], judul
    metrics = {m.label: m.value for m in app.metric}
    for label in ("Total SPBU", "Blue Ocean", "Red Ocean", "Blue Ocean Share"):
        assert label in metrics, metrics
    assert metrics["Total SPBU"] == "6.525", metrics
    assert len(app.get("plotly_chart")) >= 6
    assert len(app.dataframe) >= 2
    assert len(app.get("download_button")) >= 1

    region = app.multiselect(key="lok_region")
    region.select(region.options[0]).run()
    assert not app.exception
    assert int(app.metric[0].value.replace(".", "")) < 6_525


if __name__ == "__main__":
    for test in (
        test_home,
        test_director_summary,
        test_data_explorer,
        test_lahan_sewa,
        test_lead_time,
        test_ketersediaan_data,
        test_ketersediaan_page,
        test_occupancy_formula,
        test_occupancy_page,
        test_nilai_sewa_page,
        test_management_fee_page,
        test_master_data,
        test_lokasi_page,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("Semua smoke test lulus.")
