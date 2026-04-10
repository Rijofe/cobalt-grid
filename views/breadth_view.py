# views/breadth_view.py
# ------------------------------------------------------------
# Slide 2 — Market Breadth: gauges, distribuição por quadrante,
# performance do índice e evolução histórica do breadth score.
# ------------------------------------------------------------

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


QUAD_COLORS = {
    9: "#3B6D11", 8: "#97C459", 7: "#C0DD97",
    6: "#854F0B", 5: "#EF9F27", 4: "#FAC775",
    1: "#791F1F", 2: "#E24B4A", 3: "#F7C1C1",
}

QUAD_LABELS = {
    9: "Q9 Acima·Acel", 8: "Q8 Acima·Est", 7: "Q7 Acima·Perd",
    6: "Q6 Neutro·Acel", 5: "Q5 Neutro·Est", 4: "Q4 Neutro·Perd",
    1: "Q1 Abaixo·Pior", 2: "Q2 Abaixo·Est", 3: "Q3 Abaixo·Rec",
}


def render(df, breadth, indice_nome, idx_perf, **kwargs):
    st.markdown(f"### Market Breadth — vs {indice_nome}")

    # ── Linha 1: Breadth Score + Performance do índice ───────
    col_gauge, col_idx = st.columns([1.4, 1])

    with col_gauge:
        _gauge(breadth.get("breadth_score", 0))
        pct_up   = breadth.get("pct_up",   0)
        pct_down = breadth.get("pct_down", 0)
        st.caption(
            f"**Breadth Score = % Acima − % Abaixo** "
            f"= {pct_up:.1f}% − {pct_down:.1f}% = **{pct_up - pct_down:+.1f}**  "
            f"· Varia de −100 (todos abaixo) a +100 (todos acima)"
        )

    with col_idx:
        st.markdown(f"**{indice_nome} — performance**")
        m1, m2 = st.columns(2)
        m1.metric("5 dias",  _fmt(idx_perf.get("5d")))
        m2.metric("21 dias", _fmt(idx_perf.get("21d")))
        m3, m4 = st.columns(2)
        m3.metric("63 dias", _fmt(idx_perf.get("63d")))
        m4.metric("YTD",     _fmt(idx_perf.get("ytd")))

    st.divider()

    # ── Linha 2: métricas de breadth ─────────────────────────
    st.markdown("**Distribuição dos ativos**")
    cols = st.columns(7)
    metrics = [
        ("Total",          breadth.get("total", 0),          None),
        ("↑ Acima",        f"{breadth.get('pct_up',0):.1f}%", None),
        ("→ Neutros",      f"{breadth.get('pct_neut',0):.1f}%", None),
        ("↓ Abaixo",       f"{breadth.get('pct_down',0):.1f}%", None),
        ("Líderes Q9",     breadth.get("leaders_q9", 0),     None),
        ("Turnarounds Q3", breadth.get("turnarounds_q3", 0), None),
        ("Potenciais Q6",  breadth.get("potential_q6", 0),   None),
    ]
    for col, (label, val, delta) in zip(cols, metrics):
        col.metric(label, val, delta)

    st.divider()

    # ── Linha 3: barra proporcional + donut ───────────────────
    col_bar, col_donut = st.columns([1.5, 1])

    with col_bar:
        st.markdown("**Contagem por quadrante**")
        _bar_chart(df)

    with col_donut:
        st.markdown("**Zonas UP / NEUTRO / DOWN**")
        _donut(breadth)

    st.divider()

    # ── Linha 4: tabela de ativos por zona ───────────────────
    st.markdown("**Ativos por zona**")
    tab_up, tab_neut, tab_down = st.tabs([
        f"↑ Acima ({breadth.get('up',0)})",
        f"→ Neutros ({breadth.get('neut',0)})",
        f"↓ Abaixo ({breadth.get('down',0)})",
    ])

    with tab_up:
        _zone_table(df[df["quadrant"] >= 7])
    with tab_neut:
        _zone_table(df[df["quadrant"].between(4, 6)])
    with tab_down:
        _zone_table(df[df["quadrant"] <= 3])


# ── Sub-componentes ───────────────────────────────────────────

def _gauge(score: int):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"font": {"size": 44, "color": "#4CAF50" if score >= 0 else "#F44336"}},
        title={"text": "Breadth Score", "font": {"size": 15, "color": "#aaaaaa"}},
        gauge={
            "axis": {
                "range": [-100, 100],
                "tickwidth": 1,
                "tickfont": {"size": 12},
                "tickvals": [-100, -50, 0, 50, 100],
            },
            "bar": {"color": "#4CAF50" if score >= 0 else "#F44336", "thickness": 0.3},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [-100, -50], "color": "#7B2020"},
                {"range": [-50,    0], "color": "#4A2020"},
                {"range": [0,     50], "color": "#1E3A1E"},
                {"range": [50,   100], "color": "#2A5A2A"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
        domain={"x": [0, 1], "y": [0.1, 1]},
    ))
    fig.update_layout(
        height=260,
        margin=dict(l=30, r=30, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#aaaaaa"},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _bar_chart(df: pd.DataFrame):
    counts = df.groupby("quadrant").size().reset_index(name="count")
    all_qs = pd.DataFrame({"quadrant": list(range(1, 10))})
    counts = all_qs.merge(counts, on="quadrant", how="left").fillna(0)
    counts["label"] = counts["quadrant"].map(QUAD_LABELS)
    counts["color"] = counts["quadrant"].map(QUAD_COLORS)

    fig = go.Figure(go.Bar(
        x=counts["label"],
        y=counts["count"],
        marker_color=counts["color"].tolist(),
        text=counts["count"].astype(int),
        textposition="outside",
        hovertemplate="%{x}<br>%{y} ativos<extra></extra>",
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(size=9), tickangle=-30),
        yaxis=dict(showgrid=False, visible=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _donut(breadth: dict):
    labels = ["↑ Acima", "→ Neutros", "↓ Abaixo"]
    values = [breadth.get("up", 0), breadth.get("neut", 0), breadth.get("down", 0)]
    colors = ["#4CAF50", "#EF9F27", "#A32D2D"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker_colors=colors,
        textfont=dict(size=11),
        hovertemplate="%{label}: %{value} ativos (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(font=dict(size=11), orientation="h", y=-0.1),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _zone_table(subset: pd.DataFrame):
    if subset.empty:
        st.caption("Nenhum ativo nesta zona.")
        return
    show = subset[["ticker", "nome", "quadrant", "rs_ratio", "rs_mom", "perf_21d", "perf_vs_index"]].copy()
    show.columns = ["Ticker", "Nome", "Q", "RS Ratio (σ)", "RS Mom (σ)", "Perf 21d %", "vs Índice %"]
    show["Ticker"] = show["Ticker"].str.replace(".SA", "", regex=False)
    st.dataframe(
        show.sort_values("RS Ratio (σ)", ascending=False).reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )


def _fmt(val) -> str:
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"
