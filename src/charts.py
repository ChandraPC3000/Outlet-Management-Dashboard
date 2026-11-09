"""Builder grafik Plotly yang dipakai bersama oleh semua halaman."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import PALETTE, PLOTLY_TEMPLATE
from src.formatting import BULAN_SINGKAT, format_rupiah

KELOMPOK_WARNA = {
    "Pending": "#b45309",
    "Terbit / Beroperasi": "#4d7c0f",
    "Telah Berakhir": "#1d4ed8",
    "Ditolak / Batal": "#b91c1c",
    "Draft": "#6b7280",
    "Lainnya": "#6b7280",
}

PALETTE_GELAP = (
    "#f3f4f6",
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#f87171",
    "#a78bfa",
    "#38bdf8",
    "#a3e635",
    "#9ca3af",
    "#fb923c",
)

SKALA_ABU_TERANG = ["#e5e7eb", "#9ca3af", "#4b5563", "#111827"]
SKALA_ABU_GELAP = ["#374151", "#6b7280", "#9ca3af", "#e5e7eb"]


def _gelap() -> bool:
    """True bila pengguna memakai tema gelap Streamlit."""
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def _gaya_tema() -> dict:
    if _gelap():
        return {
            "template": "plotly_dark",
            "font": "#e5e7eb",
            "grid": "#374151",
            "line": "#4b5563",
            "hover_bg": "#111827",
            "hover_border": "#4b5563",
            "hover_font": "#f3f4f6",
            "colorway": list(PALETTE_GELAP),
            "skala_abu": SKALA_ABU_GELAP,
        }
    return {
        "template": PLOTLY_TEMPLATE,
        "font": "#111827",
        "grid": "#e5e7eb",
        "line": "#d1d5db",
        "hover_bg": "#ffffff",
        "hover_border": "#d1d5db",
        "hover_font": "#111827",
        "colorway": list(PALETTE),
        "skala_abu": SKALA_ABU_TERANG,
    }


def _finalize(
    fig: go.Figure,
    height: int = 360,
    showlegend: bool = True,
) -> go.Figure:
    """Terapkan gaya sesuai tema aktif (light/dark)."""
    gaya = _gaya_tema()
    fig.update_layout(
        template=gaya["template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=gaya["colorway"],
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color=gaya["font"]),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        showlegend=showlegend,
        separators=".,",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
        hoverlabel=dict(
            bgcolor=gaya["hover_bg"],
            bordercolor=gaya["hover_border"],
            font_size=12,
            font_color=gaya["hover_font"],
        ),
    )
    fig.update_xaxes(gridcolor=gaya["grid"], zeroline=False, linecolor=gaya["line"])
    fig.update_yaxes(gridcolor=gaya["grid"], zeroline=False, linecolor=gaya["line"])
    return fig


# --- Izin prinsip ------------------------------------------------------------
def sewa_per_brand(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Bar horizontal total harga sewa per brand."""
    data = (
        df.groupby(["Nama Brand", "Kategori"], as_index=False, observed=True)[
            "Total Harga Sewa"
        ]
        .sum()
        .nlargest(top_n, "Total Harga Sewa")
    )
    fig = px.bar(
        data,
        x="Total Harga Sewa",
        y="Nama Brand",
        orientation="h",
        color="Kategori",
        color_discrete_sequence=list(PALETTE),
        labels={"Total Harga Sewa": "Total harga sewa (Rp)", "Nama Brand": ""},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(marker_line_width=0)
    return _finalize(fig, height=max(340, 30 * len(data) + 90))


def status_donut(df: pd.DataFrame) -> go.Figure:
    """Donut komposisi status pengajuan."""
    data = df["Status"].value_counts().rename_axis("Status").reset_index(name="Jumlah")
    fig = px.pie(
        data,
        names="Status",
        values="Jumlah",
        hole=0.45,
        color_discrete_sequence=list(PALETTE),
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,} pengajuan<extra></extra>",
    )
    return _finalize(fig, height=360)


def tren_pengajuan(df: pd.DataFrame) -> go.Figure:
    """Area chart jumlah pengajuan per bulan."""
    valid = df.dropna(subset=["Periode"])
    data = valid.groupby("Periode").size().reset_index(name="Jumlah").sort_values("Periode")
    data["Label"] = data["Periode"].dt.month.map(
        lambda bulan: BULAN_SINGKAT[bulan - 1]
    ) + " " + data["Periode"].dt.year.astype(str)

    fig = px.area(
        data,
        x="Label",
        y="Jumlah",
        markers=True,
        labels={"Label": "Bulan pengajuan", "Jumlah": "Jumlah pengajuan"},
        color_discrete_sequence=[PALETTE[0]],
    )
    fig.update_traces(
        line=dict(width=2),
        fillcolor="rgba(88,166,255,0.15)",
        hovertemplate="%{x}<br>%{y:,} pengajuan<extra></extra>",
    )
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=data["Label"].tolist(),
    )
    return _finalize(fig, height=340, showlegend=False)


def region_bar(df: pd.DataFrame) -> go.Figure:
    """Bar horizontal jumlah pengajuan per region."""
    data = df["Region"].value_counts().rename_axis("Region").reset_index(name="Jumlah")
    fig = px.bar(
        data,
        x="Jumlah",
        y="Region",
        orientation="h",
        text="Jumlah",
        color_discrete_sequence=[PALETTE[0]],
        labels={"Jumlah": "Jumlah pengajuan", "Region": ""},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=340, showlegend=False)


def kategori_bar(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Bar horizontal jumlah pengajuan per kategori."""
    data = (
        df["Kategori"]
        .value_counts()
        .rename_axis("Kategori")
        .reset_index(name="Jumlah")
        .nlargest(top_n, "Jumlah")
    )
    fig = px.bar(
        data,
        x="Jumlah",
        y="Kategori",
        orientation="h",
        text="Jumlah",
        color_discrete_sequence=[PALETTE[5]],
        labels={"Jumlah": "Jumlah pengajuan", "Kategori": ""},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=max(340, 32 * len(data) + 80), showlegend=False)


def brand_terbanyak(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Bar horizontal brand dengan jumlah pengajuan terbanyak."""
    data = (
        df["Nama Brand"]
        .value_counts()
        .rename_axis("Nama Brand")
        .reset_index(name="Jumlah")
        .nlargest(top_n, "Jumlah")
    )
    fig = px.bar(
        data,
        x="Jumlah",
        y="Nama Brand",
        orientation="h",
        text="Jumlah",
        color_discrete_sequence=[PALETTE[2]],
        labels={"Jumlah": "Jumlah pengajuan", "Nama Brand": ""},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=max(340, 32 * len(data) + 80), showlegend=False)


# --- Lead time ---------------------------------------------------------------
def funnel_tahapan(funnel: pd.DataFrame) -> go.Figure:
    """Bar bertumpuk komposisi status tiap tahapan."""
    kolom = [c for c in KELOMPOK_WARNA if c in funnel.columns]
    data = funnel.melt(
        id_vars="Tahapan",
        value_vars=kolom,
        var_name="Kelompok",
        value_name="Jumlah",
    )
    fig = px.bar(
        data,
        x="Tahapan",
        y="Jumlah",
        color="Kelompok",
        barmode="stack",
        color_discrete_map=KELOMPOK_WARNA,
        labels={"Tahapan": "", "Jumlah": "Jumlah pengajuan"},
    )
    fig.update_xaxes(tickangle=-15)
    return _finalize(fig, height=380)


def aging_tahapan(stage: pd.DataFrame) -> go.Figure:
    """Bar horizontal median & P90 umur pengajuan per tahapan."""
    data = stage.melt(
        id_vars="Tahap",
        value_vars=["Median Umur (hari)", "P90 Umur (hari)"],
        var_name="Ukuran",
        value_name="Hari",
    )
    fig = px.bar(
        data,
        x="Hari",
        y="Tahap",
        color="Ukuran",
        barmode="group",
        orientation="h",
        text="Hari",
        color_discrete_sequence=[PALETTE[0], PALETTE[3]],
        labels={"Tahap": "", "Hari": "Hari"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=max(320, 60 * len(stage) + 80))


def aging_status(aging: pd.DataFrame) -> go.Figure:
    """Bar horizontal median umur per status pending."""
    data = aging.sort_values("Median Umur (hari)")
    fig = px.bar(
        data,
        x="Median Umur (hari)",
        y="Status",
        orientation="h",
        color="Tahap",
        text="Median Umur (hari)",
        color_discrete_sequence=list(PALETTE),
        labels={"Status": "", "Median Umur (hari)": "Median umur (hari)"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=max(360, 42 * len(data) + 90))


def pending_region(region: pd.DataFrame) -> go.Figure:
    """Bar bertumpuk jumlah pending per region."""
    tahap = [c for c in region.columns if c not in ("Region", "TOTAL")]
    data = region.melt(id_vars="Region", value_vars=tahap, var_name="Tahap", value_name="Jumlah")
    fig = px.bar(
        data,
        x="Jumlah",
        y="Region",
        orientation="h",
        color="Tahap",
        barmode="stack",
        color_discrete_sequence=list(PALETTE),
        labels={"Region": "", "Jumlah": "Jumlah pending"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    return _finalize(fig, height=max(340, 42 * len(region) + 90))


# --- Lahan & sewa ------------------------------------------------------------
def occupancy_region(lahan_region: pd.DataFrame) -> go.Figure:
    """Bar bertumpuk lahan tersewa vs tersedia per region."""
    data = lahan_region.melt(
        id_vars="Region",
        value_vars=["Tersewa", "Tersedia"],
        var_name="Status",
        value_name="Jumlah",
    )
    fig = px.bar(
        data,
        x="Jumlah",
        y="Region",
        orientation="h",
        color="Status",
        barmode="stack",
        color_discrete_map={"Tersewa": PALETTE[1], "Tersedia": PALETTE[7]},
        labels={"Region": "", "Jumlah": "Jumlah lahan"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    return _finalize(fig, height=380)


def approval_lahan(lahan: pd.DataFrame) -> go.Figure:
    data = (
        lahan["Status Approval"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Jumlah")
        .nlargest(8, "Jumlah")
    )
    fig = px.bar(
        data,
        x="Jumlah",
        y="Status",
        orientation="h",
        text="Jumlah",
        color_discrete_sequence=[PALETTE[4]],
        labels={"Status": "", "Jumlah": "Jumlah lahan"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=360, showlegend=False)


def top_tenant_sewa(lahan: pd.DataFrame, top_n: int = 10) -> go.Figure:
    data = (
        lahan.groupby("Tenant", as_index=False)["Harga Sewa (Rp)"]
        .sum()
        .nlargest(top_n, "Harga Sewa (Rp)")
    )
    fig = px.bar(
        data,
        x="Harga Sewa (Rp)",
        y="Tenant",
        orientation="h",
        text="Harga Sewa (Rp)",
        color_discrete_sequence=[PALETTE[5]],
        labels={"Tenant": "", "Harga Sewa (Rp)": "Nilai sewa (Rp)"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=400, showlegend=False)


def scatter_luas_sewa(lahan: pd.DataFrame) -> go.Figure:
    data = lahan[lahan["Harga Sewa (Rp)"] > 0]
    if len(data) > 3000:
        data = data.sample(3000, random_state=42)
    fig = px.scatter(
        data,
        x="Luas (M2)",
        y="Harga Sewa (Rp)",
        color="Status Sewa",
        hover_name="Tenant",
        hover_data={"No. SPBU": True, "Kode Lahan": True},
        color_discrete_map={"Tersewa": PALETTE[1], "Tersedia": PALETTE[7]},
        labels={"Luas (M2)": "Luas (m²)", "Harga Sewa (Rp)": "Nilai sewa (Rp)"},
        opacity=0.55,
        log_x=True,
        log_y=True,
    )
    fig.update_traces(marker=dict(size=6, line=dict(width=0)))
    return _finalize(fig, height=400)


def sewa_status_donut(sewa: pd.DataFrame) -> go.Figure:
    data = sewa["Status Sewa"].value_counts().rename_axis("Status").reset_index(name="Jumlah")
    fig = px.pie(
        data,
        names="Status",
        values="Jumlah",
        hole=0.45,
        color_discrete_sequence=list(PALETTE),
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,} kontrak<extra></extra>",
    )
    return _finalize(fig, height=360)


def expiry_timeline(sewa: pd.DataFrame, snapshot: pd.Timestamp, bulan: int = 12) -> go.Figure:
    akhir = snapshot + pd.DateOffset(months=bulan)
    data = sewa[
        (sewa["Tanggal Berakhir Sewa"] >= snapshot) & (sewa["Tanggal Berakhir Sewa"] <= akhir)
    ]
    urutan = pd.period_range(snapshot, akhir, freq="M")
    label = [f"{BULAN_SINGKAT[p.month - 1]} {p.year}" for p in urutan]
    hitung = (
        data["Tanggal Berakhir Sewa"].dt.to_period("M").value_counts().reindex(urutan, fill_value=0)
    )
    fig = px.bar(
        x=label,
        y=list(hitung.values),
        labels={"x": "Bulan berakhir", "y": "Jumlah kontrak"},
        color_discrete_sequence=[PALETTE[2]],
        text=list(hitung.values),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=340, showlegend=False)


def nilai_kategori_sewa(sewa: pd.DataFrame, top_n: int = 10) -> go.Figure:
    data = (
        sewa.groupby("Kategori Utama", as_index=False)["Total Harga Sewa"]
        .sum()
        .nlargest(top_n, "Total Harga Sewa")
    )
    fig = px.bar(
        data,
        x="Total Harga Sewa",
        y="Kategori Utama",
        orientation="h",
        text="Total Harga Sewa",
        color_discrete_sequence=[PALETTE[3]],
        labels={"Kategori Utama": "", "Total Harga Sewa": "Nilai sewa (Rp)"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=400, showlegend=False)


def top_brand_sewa(sewa: pd.DataFrame, top_n: int = 10) -> go.Figure:
    data = (
        sewa.groupby("Nama Brand", as_index=False)["Total Harga Sewa"]
        .sum()
        .nlargest(top_n, "Total Harga Sewa")
    )
    fig = px.bar(
        data,
        x="Total Harga Sewa",
        y="Nama Brand",
        orientation="h",
        text="Total Harga Sewa",
        color_discrete_sequence=[PALETTE[0]],
        labels={"Nama Brand": "", "Total Harga Sewa": "Nilai sewa (Rp)"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=400, showlegend=False)


# --- Ketersediaan lahan ------------------------------------------------------
def top_provinsi_lahan(ringkasan: pd.DataFrame, top_n: int = 10) -> go.Figure:
    data = ringkasan.nlargest(top_n, "Jumlah Lahan").sort_values("Jumlah Lahan")
    fig = px.bar(
        data,
        x="Jumlah Lahan",
        y="Provinsi",
        orientation="h",
        text="Jumlah Lahan",
        color_discrete_sequence=[PALETTE[0]],
        labels={"Provinsi": "", "Jumlah Lahan": "Jumlah lahan tersedia"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=380, showlegend=False)


def road_type_bar(df: pd.DataFrame) -> go.Figure:
    data = (
        df["Road Type"]
        .value_counts()
        .rename_axis("Road Type")
        .reset_index(name="Jumlah")
    )
    fig = px.bar(
        data,
        x="Jumlah",
        y="Road Type",
        orientation="h",
        text="Jumlah",
        color_discrete_sequence=[PALETTE[5]],
        labels={"Road Type": "", "Jumlah": "Jumlah lahan"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=340, showlegend=False)


def ses_bar(df: pd.DataFrame) -> go.Figure:
    urutan = ["High", "Medium High", "Medium Low", "Low", "Tidak diketahui"]
    data = (
        df["SES Dominan"]
        .value_counts()
        .reindex(urutan, fill_value=0)
        .rename_axis("SES Dominan")
        .reset_index(name="Jumlah")
    )
    fig = px.bar(
        data,
        x="SES Dominan",
        y="Jumlah",
        text="Jumlah",
        color="SES Dominan",
        color_discrete_sequence=list(PALETTE),
        labels={"SES Dominan": "", "Jumlah": "Jumlah lahan"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=340, showlegend=False)


def volume_spbu_bar(spbu: pd.DataFrame, top_n: int = 10) -> go.Figure:
    data = spbu.nlargest(top_n, "Total").sort_values("Total")
    fig = px.bar(
        data,
        x="Total",
        y="Label",
        orientation="h",
        text="Total",
        color_discrete_sequence=[PALETTE[1]],
        labels={"Label": "", "Total": "Volume (KL/bulan)"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=380, showlegend=False)


def luas_bar(kategori: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        kategori,
        x="Kelompok Luas (m²)",
        y="Jumlah Lahan",
        text="Jumlah Lahan",
        color_discrete_sequence=[PALETTE[4]],
        labels={"Jumlah Lahan": "Jumlah lahan"},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=340, showlegend=False)


# --- Occupancy rate ----------------------------------------------------------
def occupancy_gauge(value: float) -> go.Figure:
    gelap = _gelap()
    teks = "#f3f4f6" if gelap else "#111827"
    tick = "#9ca3af" if gelap else "#6b7280"
    langkah = "255,255,255" if gelap else "17,24,39"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%", "valueformat": ".1f", "font": {"size": 40, "color": teks}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": tick},
                "bar": {"color": teks, "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": f"rgba({langkah},0.10)"},
                    {"range": [50, 75], "color": f"rgba({langkah},0.18)"},
                    {"range": [75, 90], "color": f"rgba({langkah},0.26)"},
                    {"range": [90, 100], "color": f"rgba({langkah},0.34)"},
                ],
                "threshold": {
                    "line": {"color": teks, "width": 2},
                    "thickness": 0.75,
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(
        template="plotly_dark" if gelap else PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=teks),
        height=300,
        margin=dict(l=20, r=20, t=20, b=10),
    )
    return fig


def occupancy_status_donut(status: pd.DataFrame) -> go.Figure:
    warna = {"Penuh (100%)": PALETTE[1], "Sebagian": PALETTE[2], "Kosong (0%)": PALETTE[3]}
    fig = px.pie(
        status,
        names="Status",
        values="Jumlah SPBU",
        hole=0.5,
        color="Status",
        color_discrete_map=warna,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,} SPBU<extra></extra>",
    )
    return _finalize(fig, height=300)


def occupancy_bar(data: pd.DataFrame, level: str) -> go.Figure:
    data = data.sort_values("Occupancy (%)")
    teks = [f"{nilai:.1f}%".replace(".", ",") for nilai in data["Occupancy (%)"]]
    fig = px.bar(
        data,
        x="Occupancy (%)",
        y=level,
        orientation="h",
        text=teks,
        custom_data=["Jumlah SPBU", "Total Lahan", "Tersewa"],
        color="Occupancy (%)",
        color_continuous_scale=_gaya_tema()["skala_abu"],
        range_color=(0, 100),
        labels={level: "", "Occupancy (%)": "Occupancy (%)"},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "%{y}<br>Occupancy: %{x:.1f}%<br>SPBU: %{customdata[0]:,}"
            "<br>Total lahan: %{customdata[1]:,}<br>Tersewa: %{customdata[2]:,}<extra></extra>"
        ),
    )
    return _finalize(fig, height=max(360, 34 * len(data) + 100), showlegend=False)


def occupancy_heatmap(pivot: pd.DataFrame) -> go.Figure:
    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Greys",
        labels={"x": "Rentang occupancy", "y": "", "color": "Jumlah SPBU"},
        text_auto=True,
    )
    fig.update_xaxes(side="top")
    fig.update_coloraxes(showscale=False)
    return _finalize(fig, height=max(340, 32 * len(pivot) + 120), showlegend=False)


def occupancy_scatter(occ: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        occ,
        x="Total Lahan",
        y="Occupancy (%)",
        size="Tersewa",
        color="Occupancy (%)",
        color_continuous_scale=_gaya_tema()["skala_abu"],
        range_color=(0, 100),
        hover_name="No. SPBU",
        hover_data={"Region": True, "Kab./Kota": True, "Tersewa": True, "Tersedia": True},
        labels={"Total Lahan": "Total lahan per SPBU", "Occupancy (%)": "Occupancy (%)"},
        opacity=0.7,
    )
    fig.update_traces(
        marker=dict(line=dict(width=0.5, color="rgba(17,24,39,0.15)")),
        hovertemplate=(
            "SPBU %{hovertext}<br>%{customdata[0]} · %{customdata[1]}"
            "<br>Total lahan: %{x}<br>Occupancy: %{y:.1f}%"
            "<br>Tersewa: %{customdata[2]} · Tersedia: %{customdata[3]}<extra></extra>"
        ),
    )
    return _finalize(fig, height=400, showlegend=False)


def occupancy_top_bar(data: pd.DataFrame, terendah: bool = False) -> go.Figure:
    data = data.sort_values("Occupancy (%)", ascending=not terendah)
    warna = PALETTE[3] if terendah else PALETTE[1]
    teks = [f"{nilai:.1f}%".replace(".", ",") for nilai in data["Occupancy (%)"]]
    fig = px.bar(
        data,
        x="Occupancy (%)",
        y="Label",
        orientation="h",
        text=teks,
        color_discrete_sequence=[warna],
        labels={"Occupancy (%)": "Occupancy (%)", "Label": ""},
        custom_data=["Total Lahan", "Tersewa", "Tersedia"],
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "%{y}<br>Occupancy: %{x:.1f}%<br>Total lahan: %{customdata[0]}"
            "<br>Tersewa: %{customdata[1]} · Tersedia: %{customdata[2]}<extra></extra>"
        ),
    )
    return _finalize(fig, height=380, showlegend=False)


# --- Nilai (sewa & fee) ------------------------------------------------------
def bar_nilai(
    data: pd.DataFrame,
    dimensi: str,
    nilai: str,
    label: str,
    top_n: int | None = None,
    warna: str | None = None,
) -> go.Figure:
    tabel = data.nlargest(top_n, nilai) if top_n else data
    tabel = tabel.sort_values(nilai)
    teks = [format_rupiah(n) for n in tabel[nilai]]
    fig = px.bar(
        tabel,
        x=nilai,
        y=dimensi,
        orientation="h",
        text=teks,
        color_discrete_sequence=[warna or PALETTE[0]],
        labels={dimensi: "", nilai: label},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=max(340, 38 * len(tabel) + 90), showlegend=False)


def pie_nilai(data: pd.DataFrame, dimensi: str, nilai: str, label: str) -> go.Figure:
    fig = px.pie(
        data,
        names=dimensi,
        values=nilai,
        hole=0.45,
        color_discrete_sequence=list(PALETTE),
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,.0f}<extra></extra>",
    )
    return _finalize(fig, height=360)


def heatmap_nilai(pivot: pd.DataFrame, label: str) -> go.Figure:
    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "", "y": "", "color": label},
    )
    fig.update_xaxes(side="top")
    return _finalize(fig, height=max(380, 30 * len(pivot) + 120), showlegend=False)


def tren_nilai(data: pd.DataFrame, x: str, y: str, label: str) -> go.Figure:
    fig = px.area(
        data,
        x=x,
        y=y,
        markers=True,
        color_discrete_sequence=[PALETTE[0]],
        labels={x: "Bulan", y: label},
    )
    fig.update_traces(
        line=dict(width=2),
        fillcolor="rgba(88,166,255,0.15)",
        hovertemplate="%{x|%b %Y}<br>%{y:,.0f}<extra></extra>",
    )
    return _finalize(fig, height=340, showlegend=False)


def bar_jumlah(data: pd.DataFrame, x: str, y: str, label: str, warna: str | None = None) -> go.Figure:
    fig = px.bar(
        data,
        x=x,
        y=y,
        text=y,
        color_discrete_sequence=[warna or PALETTE[2]],
        labels={x: "", y: label},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=340, showlegend=False)


# --- LOKASI Intelligence -----------------------------------------------------
def bvt_map(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        color="Kelas BVT",
        color_discrete_map={
            "Blue Ocean": "#2f81f7",
            "Peluang Campuran": "#d29922",
            "Red Ocean": "#f85149",
            "Tidak ada data BVT": "#8b949e",
            "Tidak diketahui": "#8b949e",
        },
        hover_name="No. SPBU",
        hover_data={
            "Nama SPBU": True,
            "Kota/Kabupaten": True,
            "Road Type": True,
            "Blue Ocean Score (%)": ":.1f",
            "Red Count": True,
            "Blue Count": True,
            "Latitude": False,
            "Longitude": False,
        },
        zoom=3.15,
        center={"lat": -2.4, "lon": 118.0},
        mapbox_style="open-street-map",
        opacity=0.78,
        height=620,
        labels={"Kelas BVT": "Kelas"},
    )
    fig.update_traces(marker=dict(size=7, opacity=0.8))
    gaya = _gaya_tema()
    fig.update_layout(
        template=gaya["template"],
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", size=11, color=gaya["font"]),
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            x=0.01,
            bgcolor=gaya["hover_bg"],
        ),
    )
    return fig


def bvt_donut(df: pd.DataFrame) -> go.Figure:
    urutan = ["Blue Ocean", "Peluang Campuran", "Red Ocean", "Tidak ada data BVT"]
    data = (
        df["Kelas BVT"]
        .value_counts()
        .reindex(urutan, fill_value=0)
        .rename_axis("Kelas BVT")
        .reset_index(name="Jumlah")
    )
    fig = px.pie(
        data,
        names="Kelas BVT",
        values="Jumlah",
        hole=0.45,
        color="Kelas BVT",
        color_discrete_map={
            "Blue Ocean": "#2f81f7",
            "Peluang Campuran": "#d29922",
            "Red Ocean": "#f85149",
            "Tidak ada data BVT": "#8b949e",
        },
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,} SPBU<extra></extra>",
    )
    return _finalize(fig, height=340)


def bvt_provinsi(df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    total = df["Provinsi"].value_counts().nlargest(top_n).index
    data = (
        df[df["Provinsi"].isin(total)]
        .groupby(["Provinsi", "Kelas BVT"])
        .size()
        .reset_index(name="Jumlah")
    )
    urutan = total[::-1].tolist()
    fig = px.bar(
        data,
        x="Jumlah",
        y="Provinsi",
        orientation="h",
        color="Kelas BVT",
        barmode="stack",
        color_discrete_map={
            "Blue Ocean": "#2f81f7",
            "Peluang Campuran": "#d29922",
            "Red Ocean": "#f85149",
            "Tidak ada data BVT": "#8b949e",
        },
        labels={"Provinsi": "", "Jumlah": "Jumlah SPBU"},
    )
    fig.update_yaxes(categoryorder="array", categoryarray=urutan)
    return _finalize(fig, height=max(380, 34 * len(total) + 100))


def bar_hitung(data: pd.DataFrame, dimensi: str, nilai: str, label: str, warna: str | None = None) -> go.Figure:
    tabel = data.sort_values(nilai)
    fig = px.bar(
        tabel,
        x=nilai,
        y=dimensi,
        orientation="h",
        text=nilai,
        color_discrete_sequence=[warna or PALETTE[0]],
        labels={dimensi: "", nilai: label},
    )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_traces(textposition="outside", cliponaxis=False)
    return _finalize(fig, height=max(340, 36 * len(tabel) + 90), showlegend=False)
