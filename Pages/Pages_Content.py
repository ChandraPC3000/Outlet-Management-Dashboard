import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

def render_director_summary(df):
    st.title("📊 Director Summary")
    df_selection = apply_sidebar_filters(df)
    
    if not df_selection.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Pengajuan", f"{len(df_selection)} Unit")
        c2.metric("Total Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
        c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f}")
        c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")
        
        st.divider()
        # Masukkan chart tren & pie chart di sini (seperti sintaks awalmu)
        col1, col2 = st.columns(2)
        with col1:
             df_trend = df_selection.groupby(df_selection['Tgl Pengajuan'].dt.to_period('M')).size().reset_index(name='Jumlah')
             df_trend['Tgl Pengajuan'] = df_trend['Tgl Pengajuan'].astype(str)
             fig = px.line(df_trend, x='Tgl Pengajuan', y='Jumlah', markers=True, title="Tren Bulanan")
             st.plotly_chart(fig, use_container_width=True)
        with col2:
             fig_pie = px.pie(df_selection, names='Kategori', values='Total Harga Sewa', hole=0.4, title="Kontribusi Sewa")
             st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.error("Data tidak ditemukan untuk filter ini.")

def render_data_explorer(df):
    st.title("🔍 Data Explorer")
    df_filtered = apply_sidebar_filters(df)
    
    search_query = st.text_input("Global Search (No. SPBU, Brand, Tenant, dll):")
    if search_query:
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]
        
    st.dataframe(df_filtered, use_container_width=True)
