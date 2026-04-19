import streamlit as st
from src.data_loader import load_baseline_data
from src.Pages_Content import render_summary

# 1. HARUS PALING ATAS (Perintah Streamlit pertama)
st.set_page_config(page_title="NFR Analytics Pro", layout="wide")

# 2. Fungsi CSS ditaruh setelah config
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"File {file_name} tidak ditemukan. Pastikan folder assets sudah benar.")

# Panggil file CSS-nya
local_css("assets/style.css")

# 3. Load Data ke Session State
if 'main_df' not in st.session_state:
    with st.spinner('Memuat Data...'):
        st.session_state['main_df'] = load_baseline_data()

df = st.session_state['main_df']

# 4. Sidebar Menu
st.sidebar.title("📌 Menu Utama")
nav = st.sidebar.radio("Navigasi:", ["Home", "Director Summary"])
st.sidebar.divider()

if nav == "Home":
    st.title("🚀 NFR Management System")
    st.markdown("Cari No. SPBU melalui menu **Director Summary** untuk melihat analisis detail.")
    if df is not None:
        st.metric("Total Database", f"{len(df):,} Rows")
        
elif nav == "Director Summary":
    if df is not None:
        render_summary(df)
    else:
        st.error("Data gagal dimuat. Cek file Excel Anda.")
