import streamlit as st
from src.data_loader import load_baseline_data

# Konfigurasi Halaman
st.set_page_config(page_title="NFR Analytics Dashboard", layout="wide", page_icon="📊")

# Load data ke session state agar tidak reload terus menerus
if 'main_df' not in st.session_state:
    st.session_state['main_df'] = load_baseline_data()

st.title("🚀 Outlet Management Dashboard")
st.subheader("PT Pertamina Patra Niaga - Non-Fuel Retail (NFR)")

st.markdown("""
### Selamat Datang di Pusat Analisis Izin Prinsip NFR.
Sistem ini telah memuat **Dataset Baseline** secara otomatis untuk mendukung pengambilan keputusan yang cepat.

**Navigasi Menu (Cek Sidebar Kiri):**
1. **📊 Director Summary**: Ringkasan performa makro untuk level manajemen.
2. **🔍 Data Explorer**: Pencarian detail berdasarkan No. SPBU, Brand, atau Tenant.
3. **🛠️ Data Quality**: Laporan validitas data untuk memantau input yang tidak sesuai.

---
*Gunakan menu di samping untuk mulai mengeksplorasi data.*
""")

# Menampilkan statistik singkat di landing page
if st.session_state['main_df'] is not None:
    df = st.session_state['main_df']
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Data Baseline", f"{len(df):,} Unit")
    c2.metric("Total Revenue Terdata", f"Rp {df['Total Harga Sewa'].sum():,.0f}")
    c3.metric("Update Terakhir", "10 April 2026")
