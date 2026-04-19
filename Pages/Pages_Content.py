# src/Pages_Content.py

import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

def render_summary(df):
    st.title("📊 Director Summary")
    df_selection = apply_sidebar_filters(df)
    # ... isi logika chart kamu ...

def render_explorer(df):
    st.title("🔍 Data Explorer")
    df_filtered = apply_sidebar_filters(df)
    # ... isi logika search kamu ...

def render_quality_check(df):
    st.title("🛠️ Data Quality Check")
    # Logika untuk menampilkan data yang 'ngaco' (misal: Harga Sewa 0)
    st.write("Daftar data yang memerlukan validasi ulang:")
    anomali = df[df['Total Harga Sewa'] == 0]
    st.dataframe(anomali)
