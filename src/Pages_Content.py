import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

def render_summary(df):
    st.title("📊 Director Summary")
    
    # 1. Jalankan Filter
    df_selection = apply_sidebar_filters(df)
    
    # 2. Cek apakah data kosong
    if df_selection.empty:
        st.warning("⚠️ Data kosong setelah difilter. Silakan sesuaikan kembali filter Anda.")
        return

    # 3. Scorecards (Angka yang kamu lihat 7 baris itu berasal dari sini)
    c1, c2, c3, c4 = st.columns(4)
    total_unit = len(df_selection)
    total_sewa = df_selection['Total Harga Sewa'].sum()
    
    c1.metric("Total Pengajuan", f"{total_unit} Unit")
    c2.metric("Total Nilai Sewa", f"Rp {total_sewa:,.0f}")
    c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f}")
    c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")

    st.divider()

    # 4. Logika Grafik (Penyebab grafik ngga muncul biasanya di sini)
    col_row1_1, col_row1_2 = st.columns(2)

    with col_row1_1:
        st.subheader("📈 Tren Pengajuan Bulanan")
        # Pastikan kolom tanggal tidak banyak yang NaT (Not a Time)
        df_trend = df_selection.dropna(subset=['Tgl Pengajuan']).copy()
        if not df_trend.empty:
            df_trend['Bulan'] = df_trend['Tgl Pengajuan'].dt.to_period('M').astype(str)
            df_trend = df_trend.groupby('Bulan').size().reset_index(name='Jumlah')
            
            fig_trend = px.line(df_trend, x='Bulan', y='Jumlah', markers=True, text='Jumlah')
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data tanggal tidak tersedia untuk grafik tren.")

    with col_row1_2:
        st.subheader("💰 Kontribusi Sewa per Kategori")
        # Pastikan nilai sewa tidak semuanya 0 agar Pie Chart muncul
        if df_selection['Total Harga Sewa'].sum() > 0:
            fig_pie = px.pie(df_selection, names='Kategori', values='Total Harga Sewa', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nilai sewa 0, tidak dapat menampilkan Pie Chart.")

    # 5. Tabel Detail (Untuk kroscek kenapa grafiknya ngga muncul)
    st.subheader("📑 Detail Data Terpilih")
    st.dataframe(df_selection, use_container_width=True)
