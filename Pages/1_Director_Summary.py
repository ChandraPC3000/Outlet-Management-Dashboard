import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

st.set_page_config(layout="wide")
st.title("📊 Director Summary")

if 'main_df' in st.session_state and st.session_state['main_df'] is not None:
    # Terapkan Filter
    df_selection = apply_sidebar_filters(st.session_state['main_df'])

    # KPI Utama
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Total Unit", f"{len(df_selection)} Unit")
    t2.metric("Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
    t3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f} Hari")
    t4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")

    st.divider()

    # Visualisasi Utama
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Tren Pengajuan")
        df_trend = df_selection.groupby(df_selection['Tgl Pengajuan'].dt.to_period('M')).size().reset_index(name='Jumlah')
        df_trend['Tgl Pengajuan'] = df_trend['Tgl Pengajuan'].astype(str)
        fig = px.line(df_trend, x='Tgl Pengajuan', y='Jumlah', markers=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💰 Kontribusi per Kategori")
        fig_pie = px.pie(df_selection, names='Kategori', values='Total Harga Sewa', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("Data tidak ditemukan. Harap kembali ke halaman utama.")
