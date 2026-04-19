import streamlit as st
from src.Pages_Content import render_summary

# Set config di setiap page agar layout tetap wide
st.set_page_config(layout="wide", page_title="Director Summary")

if 'main_df' in st.session_state and st.session_state['main_df'] is not None:
    render_summary(st.session_state['main_df'])
else:
    st.error("Data belum dimuat. Silakan buka halaman utama (app.py) terlebih dahulu.")
