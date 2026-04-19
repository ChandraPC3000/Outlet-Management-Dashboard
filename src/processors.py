import streamlit as st

def apply_sidebar_filters(df):
    st.sidebar.header("🎛️ Filter Panel")
    df_filtered = df.copy()
    
    columns_to_filter = [
        'Region', 'Provinsi', 'Kab./Kota', 'Nama Brand', 
        'Tipe Brand', 'Kategori', 'Sub Kategori', 'Tahapan', 'Status'
    ]

    for col in columns_to_filter:
        if col in df_filtered.columns:
            available_options = sorted(df_filtered[col].dropna().unique().tolist())
            selected = st.sidebar.multiselect(f"Pilih {col}:", options=available_options)
            
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]
    
    return df_filtered
