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
    # Membersihkan kolom uang dan tanggal
    df['Total Harga Sewa'] = pd.to_numeric(df['Total Harga Sewa'], errors='coerce').fillna(0)
    df['Nominal Fee'] = pd.to_numeric(df['Nominal Fee'], errors='coerce').fillna(0)
    df['Tgl Pengajuan'] = pd.to_datetime(df['Tgl Pengajuan'], errors='coerce')
    df['SLA'] = pd.to_numeric(df['SLA'], errors='coerce').fillna(0)

    # --- 2. Dynamic Sidebar Filters ---
    st.sidebar.header("🎛️ Filter Panel")
    
    # Dictionary untuk menyimpan hasil filter
    filters = {}
    
    # Kita loop semua kolom untuk jadi filter (kecuali kolom angka/tanggal yang terlalu unik)
    columns_to_filter = [
        'Region', 'Provinsi', 'Kab./Kota', 'Nama Brand', 
        'Tipe Brand', 'Kategori', 'Sub Kategori', 'Tahapan', 'Status'
    ]
    
    for col in columns_to_filter:
        if col in df.columns:
            selected = st.sidebar.multiselect(
                f"Pilih {col}:", 
                options=sorted(df[col].dropna().unique()),
                default=[] # Biar awalnya bersih, kalau kosong berarti pilih semua
            )
            if selected:
                filters[col] = selected

    # Apply Filters secara dinamis
    df_selection = df.copy()
    for col, values in filters.items():
        df_selection = df_selection[df_selection[col].isin(values)]

    # --- 3. Scorecards ---
    st.subheader("📌 Ringkasan Data Terfilter")
    c1, c2, c3, c4 = st.columns(4)
    
    total_pengajuan = len(df_selection)
    total_rev = df_selection['Total Harga Sewa'].sum()
    avg_sla = df_selection['SLA'].mean()
    unique_brands = df_selection['Nama Brand'].nunique()

    c1.metric("Total Pengajuan", f"{total_pengajuan} Unit")
    c2.metric("Total Nilai Sewa", f"Rp {total_rev:,.0f}")
    c3.metric("Rerata SLA (Hari)", f"{avg_sla:.1f}")
    c4.metric("Jumlah Brand", f"{unique_brands}")

    st.divider()

    # --- 4. Analisis Tambahan (Analisis Jagoan) ---
    col_row1_1, col_row1_2 = st.columns(2)

    with col_row1_1:
        # Analisis Tren Pengajuan
        st.subheader("📈 Tren Pengajuan Bulanan")
        if not df_selection.empty:
            df_trend = df_selection.copy()
            df_trend = df_trend.dropna(subset=['Tgl Pengajuan'])
            
            if not df_trend.empty:
                df_trend['Bulan'] = df_trend['Tgl Pengajuan'].dt.to_period('M').astype(str)
                df_trend = df_trend.groupby('Bulan').size().reset_index(name='Jumlah')
                
                fig_trend = px.line(df_trend, x='Bulan', y='Jumlah', markers=True, 
                                   title="Volume Pengajuan per Bulan",
                                   labels={'Bulan': 'Bulan Pengajuan', 'Jumlah': 'Total Unit'})
                st.plotly_chart(fig_trend, use_container_width=True)
                st.info("Insight: Grafik ini menunjukkan fluktuasi minat mitra setiap bulannya.")
            else:
                st.warning("Tidak ada data tanggal yang valid untuk ditampilkan.")
                
    with col_row1_2:
        # VISUALISASI TAMBAHAN: Top Tenant per Region dengan Angka
        st.subheader("🏆 Top Brand per Region Terpilih")
        if not df_selection.empty:
            df_brand_reg = df_selection.groupby(['Region', 'Nama Brand']).size().reset_index(name='Jumlah')
            df_brand_reg = df_brand_reg.sort_values(['Region', 'Jumlah'], ascending=[True, False]).groupby('Region').head(10)
            
            fig_top_reg = px.bar(
                df_brand_reg, x='Jumlah', y='Nama Brand', color='Region',
                orientation='h', text='Jumlah', title="Top Brand & Jumlah Unit per Wilayah",
                barmode='group'
            )
            fig_top_reg.update_traces(textposition='outside')
            st.plotly_chart(fig_top_reg, use_container_width=True)

        # Analisis SLA per Region
        st.subheader("⏱️ Analisis Kecepatan (SLA) per Region")
        fig_sla = px.box(df_selection, x='Region', y='SLA', color='Region',
                        title="Distribusi SLA per Wilayah")
        st.plotly_chart(fig_sla, use_container_width=True)
        st.info("Insight: Kotak yang lebih rendah menunjukkan region tersebut lebih cepat memproses izin.")

    # Ringkasan Tabel
    st.subheader("🔝 Ringkasan Top 5 Brand per Region")
    if not df_selection.empty:
        summary_df = df_selection.groupby(['Region', 'Nama Brand']).size().reset_index(name='Unit')
        summary_df = summary_df.sort_values(['Region', 'Unit'], ascending=[True, False]).groupby('Region').head(5)
        st.table(summary_df)
    
    st.divider()

    col_row2_1, col_row2_2 = st.columns(2)

    with col_row2_1:
        st.subheader("🏆 Top 10 Brand Paling Aktif")
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

    # --- 5. Detail Tabel ---
    st.subheader("📑 Detail Data (Bisa di-sort)")
    st.dataframe(df_selection, use_container_width=True)

    # Fitur Download
    csv = df_selection.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Hasil Analisis (CSV)", data=csv, file_name="nfr_analysis_filtered.csv", mime="text/csv")

else:
    st.info("Silakan unggah file Excel 'Izin Prinsip' untuk memulai analisis.")
