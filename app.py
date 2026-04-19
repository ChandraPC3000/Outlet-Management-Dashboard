import streamlit as st
from src.data_loader import load_baseline_data
from src.pages_content import render_director_summary, render_data_explorer

# Konfigurasi
st.set_page_config(page_title="NFR Analytics Pro", layout="wide")

# Load Data
if 'main_df' not in st.session_state:
    st.session_state['main_df'] = load_baseline_data()

df = st.session_state['main_df']

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("📌 Main Menu")
menu = st.sidebar.radio(
    "Pilih Halaman:",
    ("Home", "Director Summary", "Data Explorer")
)

st.sidebar.divider() # Pemisah antara Menu dan Filter nantinya

# --- LOGIKA NAVIGASI ---
if menu == "Home":
    st.title("🚀 Outlet Management Dashboard")
    st.subheader("PT Pertamina Patra Niaga - Non-Fuel Retail")
    st.markdown("""
    Selamat datang di dashboard analitik NFR. 
    Silakan pilih menu di samping untuk melihat ringkasan eksekutif atau mencari data detail.
    """)
    if df is not None:
        st.metric("Total Database", f"{len(df):,} Rows")

elif menu == "Director Summary":
    if df is not None:
        render_director_summary(df)

elif menu == "Data Explorer":
    if df is not None:
        render_data_explorer(df)
