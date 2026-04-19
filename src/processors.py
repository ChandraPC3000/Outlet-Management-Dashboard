import streamlit as st

def apply_sidebar_filters(df):
    st.sidebar.header("🎛️ Filter Panel")
    
    # Copy dataframe asli
    df_filtered = df.copy()

    columns_to_filter = [
        'Region', 'Provinsi', 'Kab./Kota', 'Nama Brand', 
        'Tipe Brand', 'Kategori', 'Sub Kategori', 'Tahapan', 'Status'
    ]

    for col in columns_to_filter:
        if col in df_filtered.columns:
            # Ambil opsi yang tersedia dari data yang SUDAH terfilter sebelumnya
            available_options = sorted(df_filtered[col].dropna().unique().tolist())
            
            selected = st.sidebar.multiselect(
                f"Pilih {col}:", 
                options=available_options,
                key=f"filter_{col}" # Tambahkan key unik agar state terjaga
            )
            
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]

    # Debugging: Tampilkan jumlah data di paling bawah sidebar
    st.sidebar.write(f"---")
    st.sidebar.caption(f"Data terpilih: {len(df_filtered)} baris")
    
    return df_filtered
