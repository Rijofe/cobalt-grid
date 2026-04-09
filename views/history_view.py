# views/history_view.py
# ------------------------------------------------------------
# Slide 5 — Histórico de quadrante: heatmap de migração e
# linha do tempo de quadrante para um ativo selecionado.
# ------------------------------------------------------------

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from engine.rs_calc import compute_quadrant_history


QUAD_COLORS = {
    9: "#3B6D11", 8: "#97C459", 7: "#C0DD97",
    6: "#854F0B", 5: "#EF9F27", 4: "#FAC775",
    1: "#791F1F", 2: "#E24B4A", 3: "#F7C1C1",
}

QUAD_LABELS = {
    9: "Q9", 8: "Q8", 7: "Q7",
    6: "Q6", 5: "Q5", 4: "Q4",
    1: "Q1", 2: "Q2", 3: "Q3",
}


def render(df, prices, index_series, indice_nome, tickers_dict,
           rs_window, mom_window, smoothing, neutral_band, **kwargs):
    st.markdown(f"### Histórico de Quadrantes — vs {indice_nome}")

    if df.empty:
        st.warning("Nenhum dado disponível.")
        return

    # ── Seletor de ativo ──────────────────────────────────────
    opcoes = {
        f"{r['ticker'].replace('.SA','')} — {r['nome']}": r["ticker"]
        for _, r in df.sort_values("rs_ratio", ascending=False).iterrows()
    }

    col1, col2 = st.columns([2, 1])
    with col1:
        escolha = st.selectbox("Ativo para análise histórica", options=list(opcoes.keys()))
        st.session_state["ticker_historico"] = opcoes.get(escolha, escolha)
    with col2:
        janela = st.select_slider(
            "Período (pregões)",
            options=[42, 63, 126, 252],
            value=126,
            format_func=lambda v: f"{v}d (~{v//21}m)",
        )
        st.session_state["janela_historico"] = janela

    ticker = opcoes[escolha]
    nome   = tickers_dict.get(ticker, ticker)

    # ── Calcula histórico ─────────────────────────────────────
    with st.spinner("Calculando histórico..."):
        hist = compute_quadrant_history(
            prices=prices,
            index_series=index_series,
            ticker=ticker,
            rs_window=rs_window,
            mom_window=mom_window,
            neutral_band=neutral_band,
            smoothing=smoothing,
        )

    if hist.empty:
        st.warning("Histórico insuficiente para este ativo.")
        return

    hist = hist.iloc[-janela:].reset_index(drop=True)
    hist["date"] = pd.to_datetime(hist["date"])

    # ── Quadrante atual ───────────────────────────────────────
    q_atual = int(hist["quadrant"].iloc[-1])
    q_ant   = int(hist["quadrant"].iloc[-2]) if len(hist) > 1 else q_atual
    st.markdown(
        f"**Quadrante atual:** "
        f"<span style='background:{QUAD_COLORS[q_atual]};color:white;"
        f"padding:2px 10px;border-radius:5px;font-size:12px'>Q{q_atual}</span>"
        + (f" &nbsp;←&nbsp; Q{q_ant} no pregão anterior" if q_ant != q_atual else ""),
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Gráfico 1: linha do tempo de quadrante ────────────────
    st.markdown("**Evolução do quadrante ao longo do tempo**")
    _timeline_chart(hist, ticker.replace(".SA", ""))

    st.divider()

    # ── Gráfico 2: RS Ratio e Momentum históricos ─────────────
    st.markdown("**RS Ratio e Momentum (z-score)**")
    _rs_chart(hist)

    st.divider()

    # ── Tabela de frequência por quadrante ────────────────────
    st.markdown("**Tempo em cada quadrante**")
    _freq_table(hist, janela)


# ── Sub-componentes ───────────────────────────────────────────

def _timeline_chart(hist: pd.DataFrame, ticker_label: str):
    """Linha do tempo colorida por quadrante."""
    fig = go.Figure()

    # Faixas de fundo por zona
    fig.add_hrect(y0=6.5, y1=9.5, fillcolor="#3B6D11", opacity=0.08, line_width=0)
    fig.add_hrect(y0=3.5, y1=6.5, fillcolor="#EF9F27", opacity=0.08, line_width=0)
    fig.add_hrect(y0=0.5, y1=3.5, fillcolor="#A32D2D", opacity=0.08, line_width=0)

    # Linha do quadrante
    fig.add_trace(go.Scatter(
        x=hist["date"],
        y=hist["quadrant"],
        mode="lines+markers",
        line=dict(width=1.5, color="#185FA5"),
        marker=dict(
            size=6,
            color=[QUAD_COLORS[q] for q in hist["quadrant"]],
            line=dict(color="white", width=0.5),
        ),
        hovertemplate="%{x|%d/%m/%Y}<br>Q%{y}<extra></extra>",
        name="Quadrante",
    ))

    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(
            tickvals=list(range(1, 10)),
            ticktext=[f"Q{i}" for i in range(1, 10)],
            range=[0.5, 9.5],
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
        ),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )

    # Anotações de zona
    for y, label in [(8.2, "↑ Acima"), (5.0, "→ Neutro"), (1.8, "↓ Abaixo")]:
        fig.add_annotation(
            x=hist["date"].iloc[0], y=y,
            text=label, showarrow=False,
            font=dict(size=10, color="#888"),
            xanchor="left",
        )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _rs_chart(hist: pd.DataFrame):
    """RS Ratio e Momentum sobrepostos."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["rs_ratio"],
        name="RS Ratio",
        line=dict(color="#185FA5", width=1.8),
        hovertemplate="%{x|%d/%m}<br>RS: %{y:+.2f}σ<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["rs_mom"],
        name="RS Momentum",
        line=dict(color="#EF9F27", width=1.2, dash="dot"),
        hovertemplate="%{x|%d/%m}<br>Mom: %{y:+.2f}σ<extra></extra>",
    ))

    fig.add_hline(y=0,    line_dash="dot",  line_color="#888", line_width=0.8)
    fig.add_hline(y=0.5,  line_dash="dash", line_color="#3B6D11", line_width=0.6)
    fig.add_hline(y=-0.5, line_dash="dash", line_color="#A32D2D", line_width=0.6)

    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=False, title_text="z-score"),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=1.1, font=dict(size=11)),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _freq_table(hist: pd.DataFrame, janela: int):
    freq = (
        hist.groupby("quadrant")
        .size()
        .reset_index(name="pregões")
    )
    freq["% do período"] = (freq["pregões"] / janela * 100).round(1)
    freq["Quadrante"]    = freq["quadrant"].map(lambda q: f"Q{q}")
    freq = freq[["Quadrante", "pregões", "% do período"]].sort_values(
        "pregões", ascending=False
    )
    st.dataframe(freq, use_container_width=True, hide_index=True)
