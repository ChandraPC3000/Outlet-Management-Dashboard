import streamlit as st
from src.data_loader import load_baseline_data
from src.Pages_Content import render_summary

st.set_page_config(page_title="NFR Analytics Pro", layout="wide")

if 'main_df' not in st.session_state:
    with st.spinner('Memuat Data...'):
        st.session_state['main_df'] = load_baseline_data()

df = st.session_state['main_df']

# Sidebar Menu
st.sidebar.title("📌 Menu Utama")
nav = st.sidebar.radio("Navigasi:", ["Home", "Director Summary"])
st.sidebar.divider()

if nav == "Home":
    st.title("🚀 NFR Management System")
    st.markdown("Cari No. SPBU melalui menu **Director Summary** untuk melihat analisis detail.")
    if df is not None:
        st.metric("Total Database", f"{len(df):,} Rows")

elif nav == "Director Summary":
    render_summary(df)
