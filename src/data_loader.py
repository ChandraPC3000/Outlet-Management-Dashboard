import pandas as pd
import streamlit as st

def load_baseline_data():
    # Mengarah ke folder Data/ di repositori kamu
    file_path = "Data/Pengajuan NFR Izin Prinsip 10-April-2026.xlsx"
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Preprocessing Dasar
        df['Total Harga Sewa'] = pd.to_numeric(df['Total Harga Sewa'], errors='coerce').fillna(0)
        df['Nominal Fee'] = pd.to_numeric(df['Nominal Fee'], errors='coerce').fillna(0)
        df['Tgl Pengajuan'] = pd.to_datetime(df['Tgl Pengajuan'], errors='coerce')
        df['SLA'] = pd.to_numeric(df['SLA'], errors='coerce').fillna(0)

# Membersihkan spasi liar di nama kategori
for col in ['Region', 'Provinsi', 'Nama Brand', 'Status']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset baseline: {e}")
        return None
