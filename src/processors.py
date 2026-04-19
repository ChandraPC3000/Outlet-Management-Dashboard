import streamlit as st

def apply_spbu_filter(df):
    st.sidebar.header("🎛️ Filter Panel")
    
    # 1. Ambil daftar No. SPBU yang unik dan urutkan
    # Kita pastikan datanya string agar tidak ada .0 di belakangnya
    list_spbu = sorted(df['No. SPBU'].unique().tolist())
    
    # 2. Gunakan selectbox agar No. SPBU muncul sebagai pilihan di navigasi
    selected_spbu = st.sidebar.selectbox(
        "Pilih No. SPBU:",
        options=["-- Pilih SPBU --"] + list_spbu,
        key="selector_spbu"
    )
    
    df_filtered = df.copy()
    
    # 3. Logika Filter
    if selected_spbu != "-- Pilih SPBU --":
        df_filtered = df_filtered[df_filtered['No. SPBU'] == selected_spbu]
        st.sidebar.success(f"Ditemukan {len(df_filtered)} data tenant.")
    else:
        # Jika belum pilih, buat dataframe kosong agar dashboard tidak render prematur
        df_filtered = df_filtered.iloc[0:0] 
        st.sidebar.info("Pilih nomor SPBU untuk melihat detail.")
    
    st.sidebar.divider()
    return df_filtered
