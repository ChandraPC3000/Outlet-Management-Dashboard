import pandas as pd
import streamlit as st

def load_baseline_data():
    file_path = "Data/Pengajuan NFR Izin Prinsip 10-April-2026.xlsx"
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Bersihkan spasi di nama kolom
        df.columns = df.columns.str.strip()
        
        # CLEANING No. SPBU: Paksa jadi string dan hapus .0 jika ada
        if 'No. SPBU' in df.columns:
            df['No. SPBU'] = df['No. SPBU'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
        # Konversi Angka
        df['Total Harga Sewa'] = pd.to_numeric(df['Total Harga Sewa'], errors='coerce').fillna(0)
        df['SLA'] = pd.to_numeric(df['SLA'], errors='coerce').fillna(0)
        
        # Konversi Tanggal
        df['Tgl Pengajuan'] = pd.to_datetime(df['Tgl Pengajuan'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset: {e}")
        return None
