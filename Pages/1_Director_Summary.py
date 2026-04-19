import streamlit as st
import plotly.express as px
from src.processors import apply_sidebar_filters

st.set_page_config(layout="wide")
st.title("📊 Director Summary")

if 'main_df' in st.session_state:
    # Panggil fungsi filter berjenjang dari src
    df_selection = apply_sidebar_filters(st.session_state['main_df'])

    # Cek jika data kosong setelah difilter
    if not df_selection.empty:
        # Tampilkan Scorecards dan Chart seperti sintaks awalmu
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Pengajuan", f"{len(df_selection)} Unit")
        c2.metric("Total Nilai Sewa", f"Rp {df_selection['Total Harga Sewa'].sum():,.0f}")
        c3.metric("Rerata SLA", f"{df_selection['SLA'].mean():.1f}")

        # Tambahkan chart lainnya di bawah...
    else:
        st.error("Tidak ada data yang cocok dengan filter.")
