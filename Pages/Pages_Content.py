import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

def render_summary(df):
    st.title("📊 Director Summary")
    df_selection = apply_sidebar_filters(df)
    if not df_selection.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Unit", f"{len(df_selection)} Unit")
        c2.metric("Total Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
        c3.metric("Avg SLA", f"{df_selection['SLA'].mean():.1f} Hari")
        # ... (tambahkan chart sesuai sintaks lama)
    else:
        st.info("Pilih filter untuk melihat data.")

def render_explorer(df):
    st.title("🔍 Data Explorer")
    df_filtered = apply_sidebar_filters(df)
    search = st.text_input("Cari SPBU/Brand/Tenant:")
    if search:
        mask = df_filtered.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
        df_filtered = df_filtered[mask]
    st.dataframe(df_filtered, use_container_width=True)
