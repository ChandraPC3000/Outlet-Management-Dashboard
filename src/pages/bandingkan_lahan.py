"""Perbandingan Data Web Kemitraan vs Data Brightspace."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.brightspace import load_brightspace, load_brightspace_summary, ringkasan_brightspace
from src.charts import PALETTE_GELAP
from src.config import PALETTE
from src.excel_export import build_excel
from src.formatting import format_angka
from src.web_kemitraan import load_web_kemitraan, ringkasan_web_kemitraan

web = load_web_kemitraan()
bright = load_brightspace()
web_info = ringkasan_web_kemitraan(web)
bright_info = ringkasan_brightspace(bright, load_brightspace_summary())


def _gelap() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


GELAP = _gelap()
PALET = PALETTE_GELAP if GELAP else PALETTE
TEMPLATE = "plotly_dark" if GELAP else "plotly_white"
FONT = "#e5e7eb" if GELAP else "#111827"
GRID = "#374151" if GELAP else "#e5e7eb"

st.title("Bandingkan Data Lahan")
st.caption(
    "Perbandingan **Data Web Kemitraan** (sheet `Master Data` kajian NFR EBT) "
    "dengan **Data Brightspace** (`Bright_detailspbu_lahan`)."
)

# --- Ringkasan angka ---------------------------------------------------------
comp = pd.DataFrame(
    [
        ("Jumlah SPBU", web_info["spbu"], bright_info["spbu"]),
        ("Lahan terdaftar", web_info["total_lahan"], bright_info["total_lahan"]),
        ("Tersewa NFR aktif", web_info["tersewa"], bright_info["tersewa"]),
        ("Lahan vacant", web_info["vacant"], bright_info["vacant"]),
    ],
    columns=["Metrik", "Web Kemitraan", "Brightspace"],
)
comp["Selisih (Bright − Web)"] = comp["Brightspace"] - comp["Web Kemitraan"]
comp["Bright vs Web (%)"] = (comp["Brightspace"] / comp["Web Kemitraan"] * 100).round(1)

tab_ringkas, tab_cocok, tab_beda = st.tabs(
    ["Ringkasan", "Kecocokan Lahan", "Status Berbeda"]
)

with tab_ringkas:
    st.subheader("Perbandingan KPI")
    st.dataframe(
        comp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Web Kemitraan": st.column_config.NumberColumn(format="%d"),
            "Brightspace": st.column_config.NumberColumn(format="%d"),
            "Selisih (Bright − Web)": st.column_config.NumberColumn(format="%d"),
            "Bright vs Web (%)": st.column_config.NumberColumn(format="%.1f"),
        },
    )

    st.caption(
        f"Tersewa: Web **{web_info['occupancy']:.1f}%** vs Brightspace "
        f"**{bright_info['occupancy']:.1f}%** · Vacant: Web "
        f"**{web_info['vacancy_rate']:.1f}%** vs Brightspace "
        f"**{bright_info['vacancy_rate']:.1f}%**. "
        "Jumlah SPBU dihitung dari identifier masing-masing sumber "
        "(`No SPBU` vs `IdAgent_FK`), jadi selisihnya bersifat indikatif."
    )

    melted = comp.melt(
        id_vars="Metrik",
        value_vars=["Web Kemitraan", "Brightspace"],
        var_name="Sumber",
        value_name="Jumlah",
    )
    fig = px.bar(
        melted,
        x="Metrik",
        y="Jumlah",
        color="Sumber",
        barmode="group",
        text="Jumlah",
        color_discrete_map={
            "Web Kemitraan": PALET[3],
            "Brightspace": PALET[1],
        },
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=FONT, size=12),
        margin=dict(l=10, r=10, t=30, b=10),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
        yaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Kecocokan tingkat lahan -------------------------------------------------
web_u = web.drop_duplicates("Kode Lahan")[["Kode Lahan", "No SPBU", "Status Sewa"]].copy()
bright_u = bright.drop_duplicates("LandCode")[
    ["LandCode", "IdAgent_FK", "RentStatName"]
].copy()

match = web_u.merge(
    bright_u,
    left_on="Kode Lahan",
    right_on="LandCode",
    how="outer",
    indicator=True,
)
match["Kategori"] = "Cocok — status sama"
both = match["_merge"] == "both"
match.loc[both & (match["Status Sewa"] != match["RentStatName"]), "Kategori"] = (
    "Cocok — status berbeda"
)
match.loc[match["_merge"] == "left_only", "Kategori"] = "Hanya Web Kemitraan"
match.loc[match["_merge"] == "right_only", "Kategori"] = "Hanya Brightspace"

kategori = match["Kategori"].value_counts()
union = len(match)
matched = int((match["_merge"] == "both").sum())
same = int(kategori.get("Cocok — status sama", 0))
beda = int(kategori.get("Cocok — status berbeda", 0))
only_web = int(kategori.get("Hanya Web Kemitraan", 0))
only_bright = int(kategori.get("Hanya Brightspace", 0))

with tab_cocok:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kode Lahan Cocok", format_angka(matched))
    m2.metric("Status Sama", format_angka(same))
    m3.metric("Status Berbeda", format_angka(beda))
    m4.metric("Hanya di Salah Satu", format_angka(only_web + only_bright))

    st.caption(
        f"Total kode lahan unik (gabungan): **{format_angka(union)}** · "
        f"cocok **{matched / union * 100:.1f}%** · "
        f"sama status **{same / matched * 100:.1f}%** dari yang cocok."
    )

    kat_df = (
        kategori.rename_axis("Kategori")
        .reset_index(name="Jumlah")
        .sort_values("Jumlah", ascending=True)
    )
    fig = px.bar(
        kat_df,
        x="Jumlah",
        y="Kategori",
        orientation="h",
        text="Jumlah",
        color="Kategori",
        color_discrete_sequence=[PALET[1], PALET[3], PALET[4], PALET[2]],
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(
        template=TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=FONT, size=12),
        margin=dict(l=10, r=10, t=20, b=10),
        height=340,
        showlegend=False,
        xaxis=dict(gridcolor=GRID),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"- Kode lahan unik Web Kemitraan: **{format_angka(len(web_u))}**\n"
        f"- Kode lahan unik Brightspace: **{format_angka(len(bright_u))}**\n"
        f"- Hanya di Web Kemitraan: **{format_angka(only_web)}**\n"
        f"- Hanya di Brightspace: **{format_angka(only_bright)}**"
    )
    st.caption(
        "Pencocokan memakai `Kode Lahan` (Web Kemitraan) = `LandCode` (Brightspace), "
        "dideduplikasi per kode; jika satu kode punya beberapa status, dipakai status pertama."
    )

# --- Tabel status berbeda ----------------------------------------------------
with tab_beda:
    mism = match[both & (match["Status Sewa"] != match["RentStatName"])].copy()
    mism = mism.rename(
        columns={
            "Kode Lahan": "Kode Lahan",
            "No SPBU": "No SPBU (Web)",
            "Status Sewa": "Status Web Kemitraan",
            "RentStatName": "Status Brightspace",
            "IdAgent_FK": "ID Agent (Brightspace)",
        }
    )
    kolom = [
        "Kode Lahan",
        "No SPBU (Web)",
        "Status Web Kemitraan",
        "Status Brightspace",
        "ID Agent (Brightspace)",
    ]
    st.subheader("Lahan dengan Status Berbeda")
    st.caption(
        f"**{format_angka(len(mism))}** kode lahan punya status berbeda antara "
        "Web Kemitraan dan Brightspace."
    )
    st.dataframe(
        mism[kolom].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Unduh Excel status berbeda",
        data=build_excel(mism[kolom], "Status Berbeda"),
        file_name="selisih_status_web_vs_brightspace.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="banding_download",
    )
