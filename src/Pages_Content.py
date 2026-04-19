def render_summary(df):
    # PENTING: Jalankan filter dulu
    df_selection = apply_sidebar_filters(df)
    
    # Cek apakah hasil filter ada isinya
    if not df_selection.empty:
        st.subheader("📌 Ringkasan Data")
        c1, c2 = st.columns(2)
        c1.metric("Total Unit", f"{len(df_selection)} Unit")
        c2.metric("Total Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
        
        # Contoh chart
        import plotly.express as px
        fig = px.bar(df_selection['Region'].value_counts().reset_index(), x='Region', y='count')
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Jika kosong, beri peringatan yang jelas
        st.warning("⚠️ Tidak ada data yang sesuai dengan kombinasi filter tersebut. Coba kurangi filter.")
