import streamlit as st
import plotly.express as px
from src.processors import apply_spbu_filter

def render_summary(df):
    # Panggil filter dari processors
    df_selection = apply_spbu_filter(df)
    
    if df_selection.empty:
        st.title("📊 Director Summary")
        st.info("👈 Silakan pilih Nomor SPBU pada dropdown di sidebar untuk melihat analisis.")
        return

    # Jika data ditemukan
    spbu_id = df_selection['No. SPBU'].iloc[0]
    st.title(f"📊 Analisis SPBU {spbu_id}")
    
    # Scorecards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tenant", f"{len(df_selection)} Unit")
    c2.metric("Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
    c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f} Hari")
    c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")

    st.divider()

    # Grafik
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Sewa per Brand")
        fig_brand = px.bar(df_selection, x='Total Harga Sewa', y='Nama Brand', 
                           orientation='h', color='Kategori', text_auto='.2s')
        st.plotly_chart(fig_brand, use_container_width=True)

    with col2:
        st.subheader("📋 Status")
        fig_status = px.pie(df_selection, names='Status', hole=0.3)
        st.plotly_chart(fig_status, use_container_width=True)

    st.subheader("📑 Detail Tabel")
    st.dataframe(df_selection, use_container_width=True)
