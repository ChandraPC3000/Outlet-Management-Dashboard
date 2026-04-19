import streamlit as st

def apply_spbu_filter(df):
    st.sidebar.header("🔍 Filter SPBU")
    
    # Ambil list No. SPBU yang unik
    list_spbu = sorted(df['No. SPBU'].unique().tolist())
    
    # Menampilkan dropdown di sidebar
    selected_spbu = st.sidebar.selectbox(
        "Pilih No. SPBU:",
        options=["-- Pilih SPBU --"] + list_spbu,
        key="select_spbu_sidebar"
    )
    
    df_filtered = df.copy()
    
    if selected_spbu != "-- Pilih SPBU --":
        # Filter ketat (exact match)
        df_filtered = df_filtered[df_filtered['No. SPBU'] == selected_spbu]
        st.sidebar.success(f"Terpilih: {len(df_filtered)} baris")
    else:
        # Jika belum pilih, buat dataframe kosong agar dashboard tidak render dulu
        df_filtered = pd.DataFrame(columns=df.columns)
    
    return df_filtered
