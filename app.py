import streamlit as st
from src.data_loader import load_baseline_data

st.set_page_config(page_title="NFR Analytics Pro", layout="wide", page_icon="📊")

# Load data ke session state
if 'main_df' not in st.session_state:
    st.session_state['main_df'] = load_baseline_data()

# Sidebar Header & Info Navigasi
st.sidebar.success("Pilih menu di atas untuk navigasi.")

st.title("🚀 Outlet Management Dashboard")
st.subheader("PT Pertamina Patra Niaga - Non-Fuel Retail (NFR)")
st.divider()

st.markdown("""
### Selamat Datang, Chan!
Dashboard ini menggunakan **Dataset Baseline** (Update: 10 April 2026).

**Gunakan menu di sidebar kiri untuk berpindah halaman:**
1. **Director Summary**: Untuk melihat angka makro dan KPI.
2. **Data Explorer**: Untuk mencari data spesifik (Global Search).
""")

if st.session_state['main_df'] is not None:
    df = st.session_state['main_df']
    col1, col2 = st.columns(2)
    col1.metric("Total Data Baseline", f"{len(df):,} Rows")
    col2.metric("Total Revenue", f"Rp {df['Total Harga Sewa'].sum():,.0f}")
