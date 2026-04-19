import streamlit as st
import plotly.express as px
from src.processors import apply_spbu_filter

def render_summary(df):
    df_selection = apply_spbu_filter(df)
    
    if df_selection.empty:
        st.title("📊 Director Summary")
        st.info("👈 Silakan pilih Nomor SPBU pada dropdown di Filter Panel untuk menampilkan analisis.")
        return

    info = df_selection.iloc[0]
    spbu_id = info['No. SPBU']
    region = info['Region']
    provinsi = info['Provinsi']
    kota = info['Kab./Kota']

    total_sewa = df_selection['Total Harga Sewa'].sum()
    if total_sewa >= 1_000_000_000:
        display_sewa = f"Rp {total_sewa / 1_000_000_000:.2f} M"
    elif total_sewa >= 1_000_000:
        display_sewa = f"Rp {total_sewa / 1_000_000:.1f} Jt"
    else:
        display_sewa = f"Rp {total_sewa:,.0f}"

    st.title(f"📊 Analisis Izin Prinsip SPBU {spbu_id}")

    # 1. BAGIAN LOKASI
    st.subheader("📍 Lokasi Operasional")
    loc1, loc2, loc3 = st.columns(3)
    with loc1:
        st.metric("REGION", region)
    with loc2:
        st.metric("PROVINSI", provinsi)
    with loc3:
        st.metric("KABUPATEN / KOTA", kota)

    st.divider()
    
    # 2. SCORECARDS KPI
    st.subheader("📈 Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tenant", f"{len(df_selection)} Unit")
    c2.metric("Total Sewa", display_sewa)
    c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f} Hari")
    c4.metric("Jumlah Brand", f"{df_selection['Nama Brand'].nunique()}")

    st.divider()

    # 3. VISUALISASI DENGAN ANIMASI SOROT
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Sewa per Brand")
        fig = px.bar(
            df_selection, 
            x='Total Harga Sewa', 
            y='Nama Brand', 
            orientation='h', 
            color='Kategori', 
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        # Menambahkan efek interaksi sorot (hover)
        fig.update_traces(
            marker_line_color='#58a6ff', 
            marker_line_width=1.5, 
            opacity=0.85,
            hoverlabel=dict(bgcolor="#1c2128", font_size=14, font_family="Inter")
        )
        fig.update_layout(
            hovermode='closest',
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📋 Status Pengajuan")
        fig_pie = px.pie(
            df_selection, 
            names='Status', 
            hole=0.4, 
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        # Menambahkan efek sorot pada pie chart
        fig_pie.update_traces(
            marker=dict(line=dict(color='#58a6ff', width=2)),
            hoverinfo='label+percent',
            textinfo='value'
        )
        fig_pie.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📑 Detail Data Transaksi")
    st.dataframe(df_selection, use_container_width=True)
