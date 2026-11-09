"""Peta LOKASI Intelligence memakai tile OpenStreetMap (Folium)."""

from __future__ import annotations

import html
import math

import folium
import pandas as pd
from folium.plugins import FastMarkerCluster

WARNA = {
    "Blue Ocean": "#2f81f7",
    "Peluang Campuran": "#d29922",
    "Red Ocean": "#f85149",
    "Tidak ada data BVT": "#8b949e",
}

PRIORITAS_KELAS = ("Blue Ocean", "Peluang Campuran", "Red Ocean", "Tidak ada data BVT")

CALLBACK = """
function (row) {
    var kelas = row[2];
    var warna = kelas === 'Blue Ocean' ? '#2f81f7'
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


def _ringkasan_region(df: pd.DataFrame) -> list[dict]:
    if "Region" not in df.columns:
        return []
    data = df.dropna(subset=["Latitude", "Longitude"])
    hasil = []
    for region, grup in data.groupby("Region"):
        if pd.isna(region) or str(region).strip() in ("", "Tidak diketahui"):
            continue
        jumlah = len(grup)
        hitung = grup["Kelas BVT"].value_counts()
        dominan = max(PRIORITAS_KELAS, key=lambda k: int(hitung.get(k, 0)))
        skor = grup["Blue Ocean Score (%)"].mean()
        hasil.append(
            {
                "region": str(region),
                "lat": float(grup["Latitude"].median()),
                "lon": float(grup["Longitude"].median()),
                "jumlah": jumlah,
                "blue": int(hitung.get("Blue Ocean", 0)),
                "campuran": int(hitung.get("Peluang Campuran", 0)),
                "red": int(hitung.get("Red Ocean", 0)),
                "tanpa": int(hitung.get("Tidak ada data BVT", 0)),
                "dominan": dominan,
                "skor": None if pd.isna(skor) else round(float(skor), 1),
            }
        )
    hasil.sort(key=lambda x: x["jumlah"], reverse=True)
    if not hasil:
        return []
    maks = max(item["jumlah"] for item in hasil)
    for item in hasil:
        item["radius"] = 16 + 44 * math.sqrt(item["jumlah"] / maks)
    return hasil


def _popup_region(item: dict) -> str:
    skor = "-" if item["skor"] is None else f"{item['skor']:.1f}%"
    return (
        f"<div style='min-width:180px'>"
        f"<b>REGION {html.escape(item['region'])}</b><br>"
        f"<span style='font-size:18px'><b>{item['jumlah']:,}</b></span> SPBU<br>"
        f"Blue Ocean: {item['blue']:,}<br>"
        f"Peluang Campuran: {item['campuran']:,}<br>"
        f"Red Ocean: {item['red']:,}<br>"
        f"Tanpa data BVT: {item['tanpa']:,}<br>"
        f"Rata-rata Blue Score: {skor}"
        f"</div>"
    ).replace(",", ".")


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

    peta.get_root().header.add_child(
        folium.Element(
            """
            <style>
            .region-label {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #d1d5db;
                color: #111827;
                font-weight: 600;
                font-size: 11px;
                padding: 2px 5px;
                box-shadow: none;
            }
            .region-label::before { border-top-color: rgba(255, 255, 255, 0.95) !important; }
            </style>
            """
        )
    )

    # Level 1: 8 lingkaran region saat zoom out.
    grup_region = folium.FeatureGroup(name="Region (zoom out)")
    for item in _ringkasan_region(data):
        warna = WARNA.get(item["dominan"], "#8b949e")
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=item["radius"],
            color=warna,
            weight=2,
            fill=True,
            fill_color=warna,
            fill_opacity=0.55,
            tooltip=folium.Tooltip(
                f"<b>{html.escape(item['region'])}</b><br>{item['jumlah']:,} SPBU".replace(",", "."),
                permanent=True,
                direction="center",
                class_name="region-label",
            ),
            popup=folium.Popup(_popup_region(item), max_width=280),
        ).add_to(grup_region)
    grup_region.add_to(peta)

    # Level 2: titik/cluster SPBU saat zoom in.
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

    # Toggle layer berdasarkan zoom: <=5 region, >=6 detail.
    map_name = peta.get_name()
    script = f"""
        (function() {{
            var namaMap = "{map_name}";
            var percobaan = 0;
            function mulai() {{
                var map = window[namaMap];
                if (!map) {{
                    if (percobaan++ < 100) setTimeout(mulai, 100);
                    return;
                }}
                var regionLayer = null, detailLayer = null;
                function findLayers() {{
                    if (regionLayer && detailLayer) return;
                    map.eachLayer(function(layer) {{
                        var isCluster = (typeof L.MarkerClusterGroup !== 'undefined') && (layer instanceof L.MarkerClusterGroup);
                        if (isCluster && !detailLayer) {{
                            detailLayer = layer;
                        }} else if (layer instanceof L.FeatureGroup && !regionLayer) {{
                            var anak = layer.getLayers ? layer.getLayers() : [];
                            var semuaCircle = anak.length > 0 && anak.every(function(k) {{
                                return k instanceof L.CircleMarker;
                            }});
                            if (semuaCircle) regionLayer = layer;
                        }}
                    }});
                }}
                function syncZoom() {{
                    findLayers();
                    var showRegion = map.getZoom() <= 5 && !!regionLayer;
                    if (regionLayer) {{
                        if (showRegion) {{ if (!map.hasLayer(regionLayer)) map.addLayer(regionLayer); }}
                        else {{ map.removeLayer(regionLayer); }}
                    }}
                    if (detailLayer) {{
                        if (showRegion) {{ map.removeLayer(detailLayer); }}
                        else {{ if (!map.hasLayer(detailLayer)) map.addLayer(detailLayer); }}
                    }}
                }}
                map.on('zoomend', syncZoom);
                syncZoom();
            }}
            mulai();
        }})();
    """
    peta.get_root().script.add_child(folium.Element(script))

    return peta
