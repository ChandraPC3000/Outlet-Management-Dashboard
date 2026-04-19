import streamlit as st

def apply_spbu_filter(df):
    st.sidebar.header("🔍 Cari SPBU")
    
    # Input teks untuk No. SPBU
    spbu_input = st.sidebar.text_input("Masukkan No. SPBU:", placeholder="Contoh: 2430198")
    
    df_filtered = df.copy()
    
    if spbu_input:
        # Filter berdasarkan No. SPBU (exact match atau contains)
        df_filtered = df_filtered[df_filtered['No. SPBU'].astype(str).str.contains(spbu_input)]
        
        if df_filtered.empty:
            st.sidebar.warning(f"No. SPBU {spbu_input} tidak ditemukan.")
    
    st.sidebar.divider()
    st.sidebar.metric("Data Ditemukan", f"{len(df_filtered)} Baris")
    
    return df_filtered
