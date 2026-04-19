import streamlit as st
from src.processors import apply_sidebar_filters

st.set_page_config(layout="wide")
st.title("🔍 Data Explorer")

if 'main_df' in st.session_state:
    # Filter Berjenjang di Sidebar
    df_filtered = apply_sidebar_filters(st.session_state['main_df'])

    # Global Search Bar di Body
    search_query = st.text_input("Cari kata kunci (No. SPBU, Brand, Tenant):")

    if search_query:
        mask = df_filtered.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]

    st.dataframe(df_filtered, use_container_width=True)
