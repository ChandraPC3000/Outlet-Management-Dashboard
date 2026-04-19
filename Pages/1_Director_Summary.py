import streamlit as st
from src.Pages_Content import render_summary

# Pastikan data sudah ter-load di session state
if 'main_df' in st.session_state and st.session_state['main_df'] is not None:
    # Memanggil fungsi render dari file src/Pages_Content.py
    render_summary(st.session_state['main_df'])
else:
    st.warning("⚠️ Data baseline belum dimuat. Silakan kembali ke halaman Home (app.py).")
