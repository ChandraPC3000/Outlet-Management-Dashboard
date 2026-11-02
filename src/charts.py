"""Builder grafik Plotly yang dipakai bersama oleh semua halaman."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import PALETTE, PLOTLY_TEMPLATE
from src.formatting import BULAN_SINGKAT


def _finalize(
    fig: go.Figure,
    height: int = 360,
    showlegend: bool = True,
) -> go.Figure:
    """Terapkan gaya gelap transparan agar menyatu dengan kartu CSS."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=list(PALETTE),
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#c9d1d9"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        showlegend=showlegend,
        separators=".,",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d", font_size=12),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False, linecolor="#30363d")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False, linecolor="#30363d")
    return fig


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
