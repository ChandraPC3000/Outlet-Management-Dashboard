"""Peta SPBU generik (OpenStreetMap) untuk seluruh section."""

from __future__ import annotations

import html
import math

import folium
import pandas as pd
from folium.plugins import FastMarkerCluster
from streamlit.components.v1 import html as st_html

WARNA_TIPE = {
    "COCO": "#58a6ff",
    "CODO": "#d29922",
    "DODO": "#3fb950",
    "Lainnya": "#8b949e",
    "Tidak diketahui": "#8b949e",
}
WARNA_BVT = {
    "Blue Ocean": "#2f81f7",
    "Peluang Campuran": "#d29922",
    "Red Ocean": "#f85149",
    "Tidak ada data BVT": "#8b949e",
}

CALLBACK = """
function (row) {
    var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {
        radius: 5,
        color: row[2],
        weight: 1,
        fillColor: row[2],
        fillOpacity: 0.85
    });
    if (row[3]) { marker.bindPopup(row[3]); }
    return marker;
}
"""


def _warna(nilai: str, kolom: str) -> str:
    if kolom == "Kelas BVT":
        return WARNA_BVT.get(nilai, "#8b949e")
    return WARNA_TIPE.get(nilai, "#58a6ff")


def _popup(row: pd.Series, color_col: str) -> str:
    maps = row.get("Google Maps") or ""
    tautan = f'<a href="{maps}" target="_blank" rel="noopener">Buka Google Maps</a>' if maps else ""
    jumlah = row.get("_jumlah", 1)
    return (
        f"<b>SPBU {html.escape(str(row.get('No. SPBU', '')))}</b><br>"
        f"{html.escape(str(row.get('Nama SPBU', '')))}<br>"
        f"{html.escape(str(row.get('Kota/Kabupaten', row.get('Kab./Kota', ''))))}"
        f", {html.escape(str(row.get('Provinsi', '')))}<br>"
        f"{html.escape(color_col)}: <b>{html.escape(str(row.get(color_col, '-')))}</b><br>"
        f"Status Level: {html.escape(str(row.get('Status Level', '-')))}<br>"
        f"Baris data: {int(jumlah):,}".replace(",", ".")
        + f"<br>{tautan}"
    )


def _ringkasan_region(data: pd.DataFrame, region_col: str, color_col: str) -> list[dict]:
    if region_col not in data.columns:
        return []
    hasil = []
    for region, grup in data.groupby(region_col):
        if pd.isna(region) or str(region).strip() in ("", "Tidak diketahui"):
            continue
        nilai_warna = grup[color_col].dropna() if color_col in grup.columns else pd.Series(dtype="object")
        warna = nilai_warna.value_counts().index[0] if len(nilai_warna) else "Tidak diketahui"
        hasil.append(
            {
                "region": str(region),
                "lat": float(grup["Latitude"].median()),
                "lon": float(grup["Longitude"].median()),
                "jumlah": len(grup),
                "warna": _warna(str(warna), color_col),
                "dominan": str(warna),
            }
        )
    hasil.sort(key=lambda x: x["jumlah"], reverse=True)
    if not hasil:
        return []
    maks = max(x["jumlah"] for x in hasil)
    for item in hasil:
        item["radius"] = 16 + 44 * math.sqrt(item["jumlah"] / maks)
    return hasil


def _toggle_script(map_name: str) -> str:
    return f"""
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


def build_spbu_map(
    df: pd.DataFrame,
    color_col: str = "Tipe SPBU",
    region_col: str = "Region",
) -> folium.Map:
    data = df.dropna(subset=["Latitude", "Longitude"]).copy()
    if "No. SPBU" in data.columns:
        jumlah = data.groupby("No. SPBU").size().rename("_jumlah")
        data = data.drop_duplicates("No. SPBU").merge(jumlah, on="No. SPBU", how="left")
    data["_jumlah"] = data.get("_jumlah", 1)

    if color_col not in data.columns:
        data[color_col] = "Tidak diketahui"

    satu_spbu = len(data) == 1
    region_data = [] if satu_spbu else _ringkasan_region(data, region_col, color_col)

    if satu_spbu:
        lat = float(data.iloc[0]["Latitude"])
        lon = float(data.iloc[0]["Longitude"])
        peta = folium.Map(location=[lat, lon], zoom_start=12, tiles="OpenStreetMap", control_scale=True)
    else:
        peta = folium.Map(
            location=[-2.4, 118.0],
            zoom_start=4,
            min_zoom=3,
            max_zoom=18,
            tiles="OpenStreetMap",
            control_scale=True,
        )

    grup_region = folium.FeatureGroup(name="Region (zoom out)")
    for item in region_data:
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=item["radius"],
            color=item["warna"],
            weight=2,
            fill=True,
            fill_color=item["warna"],
            fill_opacity=0.55,
            tooltip=folium.Tooltip(
                f"<b>{html.escape(item['region'])}</b><br>{item['jumlah']:,} SPBU".replace(",", "."),
                permanent=True,
                direction="center",
                class_name="region-label",
            ),
            popup=folium.Popup(
                f"<b>REGION {html.escape(item['region'])}</b><br>"
                f"{item['jumlah']:,} SPBU<br>"
                f"Dominan: {html.escape(item['dominan'])}".replace(",", "."),
                max_width=240,
            ),
        ).add_to(grup_region)
    if region_data:
        grup_region.add_to(peta)

    baris = [
        [
            float(row["Latitude"]),
            float(row["Longitude"]),
            _warna(str(row.get(color_col, "Tidak diketahui")), color_col),
            _popup(row, color_col),
        ]
        for _, row in data.iterrows()
    ]
    if baris:
        FastMarkerCluster(
            data=baris,
            callback=CALLBACK,
            options={"maxClusterRadius": 45, "disableClusteringAtZoom": 9},
        ).add_to(peta)

    peta.get_root().header.add_child(
        folium.Element(
            """
            <style>
            .region-label {
                background: rgba(14, 17, 23, 0.88);
                border: 1px solid #30363d;
                color: #fafafa;
                font-weight: 600;
                font-size: 11px;
                padding: 2px 5px;
                box-shadow: none;
            }
            .region-label::before { border-top-color: rgba(14, 17, 23, 0.88) !important; }
            </style>
            """
        )
    )

    if region_data:
        peta.get_root().script.add_child(folium.Element(_toggle_script(peta.get_name())))

    return peta


def render_spbu_map(
    df: pd.DataFrame,
    color_col: str = "Tipe SPBU",
    region_col: str = "Region",
    height: int = 560,
) -> None:
    if df.dropna(subset=["Latitude", "Longitude"]).empty:
        st_html(
            "<div style='padding:24px;color:#8b949e;font-family:Inter,sans-serif'>"
            "Tidak ada koordinat SPBU pada filter ini.</div>",
            height=80,
            scrolling=False,
        )
        return
    peta = build_spbu_map(df, color_col=color_col, region_col=region_col)
    st_html(peta.get_root().render(), height=height, scrolling=False)
