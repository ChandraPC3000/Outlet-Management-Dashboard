import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="NFR Analytics Dashboard", layout="wide")

st.title("📊 NFR Izin Prinsip Analytics")
st.markdown("Automasi Analisis Data Kemitraan - PT Pertamina Patra Niaga")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload file Excel (Izin Prinsip)", type=["xlsx"])

if uploaded_file is not None:
    # Membaca data
    df = pd.read_excel(uploaded_file)
    
    # Preprocessing Data
    df['Total Harga Sewa'] = pd.to_numeric(df['Total Harga Sewa'], errors='coerce').fillna(0)
    df['Tgl Pengajuan'] = pd.to_datetime(df['Tgl Pengajuan'], errors='coerce')

    # 2. Sidebar Filters
    st.sidebar.header("Filter Analisis")
    
    region = st.sidebar.multiselect("Pilih Region:", options=df['Region'].unique(), default=df['Region'].unique())
    kategori = st.sidebar.multiselect("Pilih Kategori:", options=df['Kategori'].unique(), default=df['Kategori'].unique())
    status = st.sidebar.multiselect("Pilih Status:", options=df['Status'].unique(), default=df['Status'].unique())
    
    # Filter DataFrame
    df_selection = df[
        (df['Region'].isin(region)) &
        (df['Kategori'].isin(kategori)) &
        (df['Status'].isin(status))
    ]

    # 3. Scorecards - Angka Utama
    st.subheader("📌 Ringkasan Data")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric("Total Tenant", f"{len(df_selection)} Unit")
    with c2:
        total_rev = df_selection['Total Harga Sewa'].sum()
        st.metric("Total Nilai Sewa", f"Rp {total_rev:,.0f}")
    with c3:
        # Menghitung Top Kategori
        if not df_selection.empty:
            top_cat = df_selection['Kategori'].mode()[0]
            st.metric("Kategori Terbanyak", top_cat)

    st.divider()

    # 4. Visualisasi
    col_kiri, col_kanan = st.columns(2)

    with col_kiri:
        st.subheader("Top 10 Brand Beroperasi/Terdaftar")
        brand_count = df_selection['Nama Brand'].value_counts().head(10).reset_index()
        brand_count.columns = ['Nama Brand', 'Jumlah']
        fig_brand = px.bar(brand_count, x='Jumlah', y='Nama Brand', orientation='h', 
                           color='Jumlah', color_continuous_scale='Reds')
        st.plotly_chart(fig_brand, use_container_width=True)

    with col_kanan:
        st.subheader("Proporsi Berdasarkan Kategori")
        fig_pie = px.pie(df_selection, names='Kategori', values='Total Harga Sewa', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # 5. Detail Tabel
    st.subheader("📑 Data Terfilter")
    st.dataframe(df_selection, use_container_width=True)

else:
    st.info("Silakan unggah file Excel 'Izin Prinsip' untuk melihat analisis.")