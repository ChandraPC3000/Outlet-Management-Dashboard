"""Entry point: konfigurasi halaman, CSS global, dan navigasi aplikasi."""

from __future__ import annotations

import importlib

import streamlit as st

# Streamlit Cloud kadang mempertahankan cache modul lama setelah redeploy.
# Reload config lebih dulu agar path dataset terbaru ikut terpakai, lalu modul
# lain yang mengimpor konstanta dari config.
import src.config as _config

importlib.reload(_config)
from src.config import APP_ICON, APP_TITLE, LOGO_PATH, STYLE_PATH  # noqa: E402

import src.wilayah as _wilayah  # noqa: E402

importlib.reload(_wilayah)

from src import analytics as _analytics  # noqa: E402
from src import charts as _charts  # noqa: E402
from src import data_loader as _data_loader  # noqa: E402
from src import filters as _filters  # noqa: E402
from src import map_lokasi as _map_lokasi  # noqa: E402
from src import master_data as _master_data  # noqa: E402
from src import spbu_universe as _spbu_universe  # noqa: E402

importlib.reload(_master_data)
importlib.reload(_data_loader)
importlib.reload(_spbu_universe)
importlib.reload(_filters)
importlib.reload(_analytics)
importlib.reload(_charts)
importlib.reload(_map_lokasi)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css(path) -> None:
    """Sisipkan file CSS kustom ke aplikasi."""
    try:
        st.markdown(f"<style>{path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"File style `{path}` tidak ditemukan. Tampilan memakai tema bawaan.")


inject_css(STYLE_PATH)

if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="medium")

load_data_or_stop = _data_loader.load_data_or_stop

# Muat data sekali di awal; halaman lain memakai cache yang sama sehingga
# tetap aman walau dibuka langsung lewat URL.
load_data_or_stop()

navigation = st.navigation(
    {
        "Ringkasan": [
            st.Page("src/pages/home.py", title="Home", default=True),
            st.Page("src/pages/director_summary.py", title="Director Summary"),
        ],
        "Lahan & Mitra": [
            st.Page("src/pages/ketersediaan.py", title="Ketersediaan Lahan"),
            st.Page("src/pages/occupancy.py", title="Occupancy Rate"),
            st.Page("src/pages/lahan_sewa.py", title="Lahan & Sewa"),
        ],
        "Komersial": [
            st.Page("src/pages/nilai_sewa.py", title="Nilai Sewa"),
            st.Page("src/pages/management_fee.py", title="Management Fee"),
        ],
        "Lokasi & BVT": [
            st.Page("src/pages/lokasi.py", title="LOKASI Intelligence"),
        ],
        "Eksplorasi": [
            st.Page("src/pages/data_explorer.py", title="Data Explorer"),
        ],
        "Operasional": [
            st.Page("src/pages/lead_time.py", title="Lead Time"),
        ],
    }
)
navigation.run()
