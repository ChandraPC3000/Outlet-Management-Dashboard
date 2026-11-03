"""Peta LOKASI Intelligence memakai tile OpenStreetMap (Folium)."""

from __future__ import annotations

import html

import folium
import pandas as pd
from folium.plugins import FastMarkerCluster

WARNA = {
    "Blue Ocean": "#3fb950",
    "Peluang Campuran": "#d29922",
    "Red Ocean": "#f85149",
    "Tidak ada data BVT": "#8b949e",
}

CALLBACK = """
function (row) {
    var kelas = row[2];
    var warna = kelas === 'Blue Ocean' ? '#3fb950'
        : kelas === 'Peluang Campuran' ? '#d29922'
        : kelas === 'Red Ocean' ? '#f85149'
        : '#8b949e';
    var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {
        radius: 5,
        color: warna,
        weight: 1,
        fillColor: warna,
        fillOpacity: 0.85
    });
    if (row[3]) {
        marker.bindPopup(row[3]);
    }
    return marker;
}
"""


def _popup(row: pd.Series) -> str:
    maps = row.get("Google Maps") or ""
    tautan = f'<a href="{maps}" target="_blank" rel="noopener">Buka Google Maps</a>' if maps else ""
    skor = row.get("Blue Ocean Score (%)")
    skor_teks = "-" if pd.isna(skor) else f"{float(skor):.1f}%"
    return (
        f"<b>SPBU {html.escape(str(row.get('No. SPBU', '')))}</b><br>"
        f"{html.escape(str(row.get('Nama SPBU', '')))}<br>"
        f"{html.escape(str(row.get('Kota/Kabupaten', '')))}, "
        f"{html.escape(str(row.get('Provinsi', '')))}<br>"
        f"BVT: <b>{html.escape(str(row.get('Kelas BVT', '')))}</b> ({skor_teks})<br>"
        f"Red: {int(row.get('Red Count', 0) or 0)} · Blue: {int(row.get('Blue Count', 0) or 0)}<br>"
        f"{tautan}"
    )


def build_map(df: pd.DataFrame) -> folium.Map:
    data = df.dropna(subset=["Latitude", "Longitude"]).copy()

    peta = folium.Map(
        location=[-2.4, 118.0],
        zoom_start=4,
        min_zoom=3,
        max_zoom=18,
        tiles="OpenStreetMap",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        control_scale=True,
    )

    baris = [
        [
            float(row["Latitude"]),
            float(row["Longitude"]),
            str(row.get("Kelas BVT", "Tidak ada data BVT")),
            _popup(row),
        ]
        for _, row in data.iterrows()
    ]

    if baris:
        FastMarkerCluster(
            data=baris,
            callback=CALLBACK,
            options={"maxClusterRadius": 45, "disableClusteringAtZoom": 9},
        ).add_to(peta)

    return peta
