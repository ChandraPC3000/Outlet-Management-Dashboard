import streamlit as st
import plotly.express as px
from src.processors import apply_spbu_filter

def render_summary(df):
    st.title("📊 Director Summary per SPBU")
    
    # Ambil data berdasarkan filter No. SPBU di sidebar
    df_selection = apply_spbu_filter(df)
    
    if df_selection.empty:
        st.info("💡 Silakan masukkan No. SPBU di sidebar untuk melihat analisis.")
        return

    # Tampilkan info lokasi SPBU (diambil dari baris pertama hasil filter)
    row = df_selection.iloc[0]
    st.success(f"📍 Menampilkan data untuk SPBU: **{row['No. SPBU']}** - {row['Provinsi']}, {row['Kab./Kota']}")

    # Scorecards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tenant", f"{len(df_selection)} Unit")
    c2.metric("Total Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
    c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f} Hari")
    c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")

    st.divider()

    # Visualisasi Sederhana
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Kontribusi Sewa per Brand")
        fig_brand = px.bar(df_selection, x='Total Harga Sewa', y='Nama Brand', 
                           orientation='h', color='Kategori', text_auto='.2s')
        st.plotly_chart(fig_brand, use_container_width=True)

    with col2:
        st.subheader("📋 Status Pengajuan")
        fig_status = px.pie(df_selection, names='Status', hole=0.3)
        st.plotly_chart(fig_status, use_container_width=True)

    # Tabel Detail
    st.subheader("📑 Daftar Tenant di SPBU Ini")
    st.dataframe(df_selection[['Tgl Pengajuan', 'Nama Tenant', 'Nama Brand', 'Kategori', 'Total Harga Sewa', 'Status']], 
                 use_container_width=True)
