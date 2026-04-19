import streamlit as st
import plotly.express as px
from src.processors import apply_spbu_filter

def render_summary(df):
    df_selection = apply_spbu_filter(df)
    
    if df_selection.empty:
        st.title("📊 Director Summary")
        st.info("👈 Silakan pilih Nomor SPBU pada dropdown di Filter Panel untuk menampilkan analisis.")
        return

    spbu_id = df_selection['No. SPBU'].iloc[0]
    st.title(f"📊 Analisis Izin Prinsip SPBU {spbu_id}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tenant", f"{len(df_selection)} Unit")
    c2.metric("Total Sewa", display_sewa)
    c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f}")
    c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Sewa per Brand")
        # TAMBAHKAN template="plotly_dark"
        fig = px.bar(df_selection, x='Total Harga Sewa', y='Nama Brand', 
                     orientation='h', color='Kategori', template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📋 Status")
        # TAMBAHKAN template="plotly_dark"
        fig_pie = px.pie(df_selection, names='Status', hole=0.3, template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📑 Detail Data")
    st.dataframe(df_selection, use_container_width=True)
