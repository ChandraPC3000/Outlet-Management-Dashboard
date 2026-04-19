import streamlit as st

def apply_sidebar_filters(df):
    st.sidebar.header("🎛️ Filter Panel")
    df_filtered = df.copy()

    columns_to_filter = [
        'Region', 'Provinsi', 'Kab./Kota', 'Nama Brand', 
        'Tipe Brand', 'Kategori', 'Sub Kategori', 'Tahapan', 'Status'
    ]

    for col in columns_to_filter:
        # Hanya ambil opsi yang ada di df_filtered saat ini (Sinkron)
        available_options = sorted(df_filtered[col].unique().tolist())
        
        # Hapus 'nan' dari pilihan jika ada
        if 'nan' in available_options: available_options.remove('nan')
        
        selected = st.sidebar.multiselect(f"Pilih {col}:", options=available_options, key=f"filter_{col}")
        
        if selected:
            df_filtered = df_filtered[df_filtered[col].isin(selected)]
            # Jika setelah difilter data jadi 0, kasih peringatan langsung di sidebar
            if df_filtered.empty:
                st.sidebar.warning(f"⚠️ Data habis setelah filter {col}!")
                break # Berhenti filter jika data sudah kosong

    st.sidebar.divider()
    st.sidebar.metric("Data Terpilih", f"{len(df_filtered)} Baris")
    
    return df_filtered
