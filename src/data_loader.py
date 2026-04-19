import pandas as pd
import streamlit as st

def load_baseline_data():
    file_path = "Data/Pengajuan NFR Izin Prinsip 10-April-2026.xlsx"
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # --- CLEANING GHAIB ---
        # 1. Buang spasi di awal/akhir untuk semua kolom teks
        str_cols = df.select_dtypes(include=['object']).columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
            
        # 2. Konversi Angka
        df['Total Harga Sewa'] = pd.to_numeric(df['Total Harga Sewa'], errors='coerce').fillna(0)
        df['SLA'] = pd.to_numeric(df['SLA'], errors='coerce').fillna(0)
        
        # 3. Konversi Tanggal
        df['Tgl Pengajuan'] = pd.to_datetime(df['Tgl Pengajuan'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset: {e}")
        return None
