import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

def render_summary(df):
    st.title("📊 Director Summary")
    df_selection = apply_sidebar_filters(df)
    
    if df_selection.empty:
        st.error("❌ Tidak ada data untuk kombinasi filter ini. Silakan reset filter di sidebar.")
        return # Keluar dari fungsi agar tidak error di bawah

    # Jika ada data, baru render scorecard & chart
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Unit", f"{len(df_selection)} Unit")
    c2.metric("Total Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
    c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f}")
    
    # Chart logic...
    fig = px.pie(df_selection, names='Kategori', values='Total Harga Sewa', hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
