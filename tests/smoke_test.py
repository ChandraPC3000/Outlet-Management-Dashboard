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


if __name__ == "__main__":
    for test in (
        test_home,
        test_director_summary,
        test_data_explorer,
        test_lahan_sewa,
        test_lead_time,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("Semua smoke test lulus.")
