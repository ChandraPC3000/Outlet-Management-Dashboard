"""Entry point: konfigurasi halaman, CSS global, dan navigasi aplikasi."""

from __future__ import annotations

import importlib
import streamlit as st

from src import analytics as _analytics
from src import charts as _charts
from src import map_lokasi as _map_lokasi
from src.config import APP_ICON, APP_TITLE, LOGO_PATH, STYLE_PATH
from src.data_loader import load_data_or_stop

# Streamlit Cloud kadang mempertahankan cache modul lama setelah redeploy,
# sehingga fungsi baru (mis. charts.bvt_map) belum terdaftar. Modul ini murni
# (tanpa cache data), jadi aman di-reload setiap run.
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
    st.logo(str(LOGO_PATH), size="large")

# Muat data sekali di awal; halaman lain memakai cache yang sama sehingga
# tetap aman walau dibuka langsung lewat URL.
load_data_or_stop()

navigation = st.navigation(
    {
        "Ringkasan": [
            st.Page("src/pages/home.py", title="Home", icon="🏠", default=True),
            st.Page("src/pages/director_summary.py", title="Director Summary", icon="📊"),
        ],
        "Lahan & Mitra": [
            st.Page("src/pages/ketersediaan.py", title="Ketersediaan Lahan", icon="🧭"),
            st.Page("src/pages/occupancy.py", title="Occupancy Rate", icon="📈"),
            st.Page("src/pages/lahan_sewa.py", title="Lahan & Sewa", icon="🏞️"),
        ],
        "Komersial": [
            st.Page("src/pages/nilai_sewa.py", title="Nilai Sewa", icon="💰"),
            st.Page("src/pages/management_fee.py", title="Management Fee", icon="💳"),
        ],
        "Lokasi & BVT": [
            st.Page("src/pages/lokasi.py", title="LOKASI Intelligence", icon="🗺️"),
        ],
        "Eksplorasi": [
            st.Page("src/pages/data_explorer.py", title="Data Explorer", icon="🔎"),
        ],
        "Operasional": [
            st.Page("src/pages/lead_time.py", title="Lead Time", icon="⏱️"),
        ],
    }
)
navigation.run()
