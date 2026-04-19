import streamlit as st
from src.Pages_Content import render_quality_check

if 'main_df' in st.session_state and st.session_state['main_df'] is not None:
    render_quality_check(st.session_state['main_df'])
else:
    st.warning("⚠️ Data baseline belum dimuat. Silakan kembali ke halaman Home (app.py).")
