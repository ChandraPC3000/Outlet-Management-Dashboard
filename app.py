import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(page_title="NFR Analytics Pro", layout="wide")

st.title("📊 NFR Izin Prinsip Analytics - Super Dashboard")
st.markdown("Automasi Analisis Data Kemitraan - PT Pertamina Patra Niaga")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload file Excel (Izin Prinsip)", type=["xlsx"])

if uploaded_file is not None:
    # Membaca data
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    
    # --- Preprocessing ---
    df['Total Harga Sewa'] = pd.to_numeric(df['Total Harga Sewa'], errors='coerce').fillna(0)
    df['Nominal Fee'] = pd.to_numeric(df['Nominal Fee'], errors='coerce').fillna(0)
    df['Tgl Pengajuan'] = pd.to_datetime(df['Tgl Pengajuan'], errors='coerce')
    df['SLA'] = pd.to_numeric(df['SLA'], errors='coerce').fillna(0)

    # --- 2. Dynamic Sidebar Filters (SINKRON/BERJENJANG) ---
    st.sidebar.header("🎛️ Filter Panel")
    
    # Copy dataframe asli untuk filter berjenjang
    df_filtered = df.copy()

    # List kolom filter
    columns_to_filter = [
        'Region', 'Provinsi', 'Kab./Kota', 'Nama Brand', 
        'Tipe Brand', 'Kategori', 'Sub Kategori', 'Tahapan', 'Status'
    ]

    filters = {}
    
    # LOGIKA SINKRONISASI: Setiap filter akan mempengaruhi pilihan di filter bawahnya
    for col in columns_to_filter:
        if col in df_filtered.columns:
            # Pilihan yang muncul HANYA yang tersedia di data yang sudah terfilter sebelumnya
            available_options = sorted(df_filtered[col].dropna().unique().tolist())
            
            selected = st.sidebar.multiselect(
                f"Pilih {col}:", 
                options=available_options,
                default=[]
            )
            
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]
                filters[col] = selected

    # Data Akhir untuk Visualisasi
    df_selection = df_filtered

    # --- 3. Scorecards ---
    st.subheader("📌 Ringkasan Data Terfilter")
    if not df_selection.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Pengajuan", f"{len(df_selection)} Unit")
        c2.metric("Total Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
        c3.metric("Rerata SLA (Hari)", f"{df_selection['SLA'].mean():.1f}")
        c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")
    else:
        st.error("⚠️ Tidak ada data yang cocok dengan kombinasi filter tersebut.")

    st.divider()

    # --- 4. Analisis Tambahan ---
    if not df_selection.empty:
        col_row1_1, col_row1_2 = st.columns(2)

        with col_row1_1:
            st.subheader("📈 Tren Pengajuan Bulanan")
            df_trend = df_selection.dropna(subset=['Tgl Pengajuan']).copy()
            if not df_trend.empty:
                df_trend['Bulan'] = df_trend['Tgl Pengajuan'].dt.to_period('M').astype(str)
                df_trend = df_trend.groupby('Bulan').size().reset_index(name='Jumlah')
                fig_trend = px.line(df_trend, x='Bulan', y='Jumlah', markers=True, 
                                   text='Jumlah', title="Volume Pengajuan per Bulan")
                fig_trend.update_traces(textposition="top center")
                st.plotly_chart(fig_trend, use_container_width=True)

        with col_row1_2:
            st.subheader("🏆 Top Brand per Region Terpilih")
            df_brand_reg = df_selection.groupby(['Region', 'Nama Brand']).size().reset_index(name='Jumlah')
            df_brand_reg = df_brand_reg.sort_values(['Region', 'Jumlah'], ascending=[True, False]).groupby('Region').head(10)
            fig_top_reg = px.bar(df_brand_reg, x='Jumlah', y='Nama Brand', color='Region',
                                 orientation='h', text='Jumlah', barmode='group')
            fig_top_reg.update_traces(textposition='outside')
            st.plotly_chart(fig_top_reg, use_container_width=True)

        # Ringkasan Tabel
        st.subheader("🔝 Ringkasan Top 5 Brand per Region")
        summary_df = df_selection.groupby(['Region', 'Nama Brand']).size().reset_index(name='Unit')
        summary_df = summary_df.sort_values(['Region', 'Unit'], ascending=[True, False]).groupby('Region').head(5)
        st.table(summary_df)
        
        st.divider()

        col_row2_1, col_row2_2 = st.columns(2)
        with col_row2_1:
            st.subheader("🏆 Top 10 Brand Paling Aktif (Global Filter)")
            brand_count = df_selection['Nama Brand'].value_counts().head(10).reset_index()
            brand_count.columns = ['Nama Brand', 'Jumlah']
            fig_brand = px.bar(brand_count, x='Jumlah', y='Nama Brand', orientation='h', 
                               color='Jumlah', color_continuous_scale='Reds', text='Jumlah')
            fig_brand.update_traces(textposition='outside')
            st.plotly_chart(fig_brand, use_container_width=True)

        with col_row2_2:
            st.subheader("💰 Kontribusi Sewa per Kategori")
            fig_pie = px.pie(df_selection, names='Kategori', values='Total Harga Sewa', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📑 Detail Data (Bisa di-sort)")
        st.dataframe(df_selection, use_container_width=True)

        csv = df_selection.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Hasil Analisis (CSV)", data=csv, file_name="nfr_analysis_filtered.csv", mime="text/csv")
    else:
        st.info("Gunakan filter di samping untuk melihat analisis spesifik.")

else:
    st.info("Silakan unggah file Excel 'Izin Prinsip' untuk memulai analisis.")
