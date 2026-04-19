import streamlit as st
from src.data_loader import load_baseline_data

# 1. Konfigurasi Halaman (Harus di paling atas)
st.set_page_config(page_title="NFR Analytics Dashboard", layout="wide", page_icon="📊")

# 2. Load data ke session state agar tidak reload terus menerus
if 'main_df' not in st.session_state:
    with st.spinner('Memuat Dataset Baseline...'):
        st.session_state['main_df'] = load_baseline_data()

# 3. Sidebar Navigation (Manual Guide)
st.sidebar.image("assets/logo.png", width=200) # Pastikan ada file logo di folder assets
st.sidebar.title("📌 Menu Navigasi")
st.sidebar.info("""
Pilih halaman di atas untuk memulai:
1. **Director Summary**: Analisis Makro
2. **Data Explorer**: Pencarian Global
3. **Data Quality**: Cek Validitas
""")

# 4. Konten Utama Landing Page
st.title("🚀 Outlet Management Dashboard")
st.markdown("### PT Pertamina Patra Niaga - Non-Fuel Retail (NFR)")
st.divider()

st.markdown("""
Selamat datang, **Chan**. Dashboard ini dirancang untuk mempermudah pemantauan izin prinsip tenant di seluruh SPBU Pertamina. 

**Cara Menggunakan Dashboard:**
- Gunakan menu di sidebar kiri untuk berpindah halaman.
- Halaman **Director Summary** fokus pada KPI (Nilai Sewa, SLA, Jumlah Unit).
- Halaman **Data Explorer** memungkinkan Anda mencari data spesifik (No. SPBU/Brand).
""")

# 5. Quick Stats Badge
if st.session_state['main_df'] is not None:
    df = st.session_state['main_df']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Dataset Size", f"{len(df):,} Rows")
    with col2:
        st.metric("Total Revenue", f"Rp {df['Total Harga Sewa'].sum():,.0f}")
    with col3:
        st.metric("Data Status", "Internal Baseline")
