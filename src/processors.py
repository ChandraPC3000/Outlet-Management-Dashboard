import streamlit as st

def apply_sidebar_filters(df):
    st.sidebar.header("🎛️ Filter Panel")
    
    # Copy dataframe asli untuk filter berjenjang
    df_filtered = df.copy()

    # List kolom filter sesuai referensi kamu
    columns_to_filter = [
        'Region', 'Provinsi', 'Kab./Kota', 'Nama Brand', 
        'Tipe Brand', 'Kategori', 'Sub Kategori', 'Tahapan', 'Status'
    ]

    filters = {}
    
    # LOGIKA SINKRONISASI: Setiap filter mempengaruhi pilihan di bawahnya
    for col in columns_to_filter:
        if col in df_filtered.columns:
            # Pilihan hanya yang tersedia di data yang sudah terfilter sebelumnya
            available_options = sorted(df_filtered[col].dropna().unique().tolist())
            
            selected = st.sidebar.multiselect(
                f"Pilih {col}:", 
                options=available_options,
                default=[]
            )
            
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]
                filters[col] = selected

    return df_filtered
