import streamlit as st
from src.processors import apply_sidebar_filters

st.set_page_config(layout="wide")
st.title("🔍 Data Explorer & Global Search")

if 'main_df' in st.session_state:
    df = st.session_state['main_df']
    
    # Global Search Bar
    search_query = st.text_input("Masukkan No. SPBU, Nama Tenant, atau Nama Brand:", placeholder="Contoh: 31.XXXXX atau Alfamart")
    
    df_filtered = apply_sidebar_filters(df)
    
    if search_query:
        # Logika Search di semua kolom
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]

    st.subheader(f"Ditemukan {len(df_filtered)} baris data")
    st.dataframe(df_filtered, use_container_width=True)
    
    # Download Button
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Hasil Pencarian (CSV)", data=csv, file_name="nfr_search_results.csv")
