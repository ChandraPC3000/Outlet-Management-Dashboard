import streamlit as st
from src.data_loader import load_baseline_data
# Import fungsi dari file Pages_Content.py di folder src
from src.Pages_Content import render_summary, render_explorer

st.set_page_config(page_title="NFR Analytics Pro", layout="wide")

if 'main_df' not in st.session_state:
    st.session_state['main_df'] = load_baseline_data()

df = st.session_state['main_df']

# --- Navigasi Menu di Sidebar ---
st.sidebar.title("📌 Menu Utama")
nav_choice = st.sidebar.radio("Navigasi:", ["Home", "Director Summary", "Data Explorer"])
st.sidebar.divider()

if nav_choice == "Home":
    st.title("🚀 NFR Management System")
    st.markdown("Selamat datang di sistem automasi data Pertamina Patra Niaga.")
    if df is not None:
        st.metric("Total Data Terload", f"{len(df):,} Baris")

elif nav_choice == "Director Summary":
    render_summary(df)

elif nav_choice == "Data Explorer":
    render_explorer(df)
