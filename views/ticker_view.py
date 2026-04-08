# views/ticker_view.py
# ------------------------------------------------------------
# Slide 4 — Análise individual: gráfico de RS histórico,
# preço vs índice normalizado e métricas detalhadas.
# ------------------------------------------------------------

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


QUAD_STYLE = {
    9: {"bg": "#3B6D11", "tx": "#EAF3DE", "label": "Q9 — Acima · Acelerando"},
    8: {"bg": "#97C459", "tx": "#173404", "label": "Q8 — Acima · Estável"},
    7: {"bg": "#C0DD97", "tx": "#27500A", "label": "Q7 — Acima · Desacelerando"},
    6: {"bg": "#854F0B", "tx": "#FAEEDA", "label": "Q6 — Neutro · Acelerando"},
    5: {"bg": "#EF9F27", "tx": "#412402", "label": "Q5 — Neutro · Estável"},
    4: {"bg": "#FAC775", "tx": "#633806", "label": "Q4 — Neutro · Perdendo"},
    1: {"bg": "#791F1F", "tx": "#FCEBEB", "label": "Q1 — Abaixo · Piorando"},
    2: {"bg": "#E24B4A", "tx": "#FCEBEB", "label": "Q2 — Abaixo · Estável"},
    3: {"bg": "#F7C1C1", "tx": "#791F1F", "label": "Q3 — Abaixo · Recuperando"},
}


def render(df, prices, index_series, indice_nome, tickers_dict, **kwargs):
    st.markdown(f"### Ativo Individual — vs {indice_nome}")

    if df.empty:
        st.warning("Nenhum dado disponível.")
        return

    # ── Seletor de ativo ──────────────────────────────────────
    opcoes = {
        f"{r['ticker'].replace('.SA','')} — {r['nome']} (Q{r['quadrant']})": r["ticker"]
        for _, r in df.sort_values("rs_ratio", ascending=False).iterrows()
    }

    escolha = st.selectbox("Selecione o ativo", options=list(opcoes.keys()))
    ticker  = opcoes[escolha]
    row     = df[df["ticker"] == ticker].iloc[0]
    q       = int(row["quadrant"])
    style   = QUAD_STYLE[q]

    # ── Cabeçalho ─────────────────────────────────────────────
    st.markdown(
        f"<span style='background:{style['bg']};color:{style['tx']};"
        f"font-size:12px;padding:4px 12px;border-radius:6px;font-weight:500'>"
        f"{style['label']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    # ── Métricas ──────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("RS Ratio",     f"{row['rs_ratio']:+.2f}σ",
              help="Z-score do ratio ativo/índice. Positivo = superando o benchmark.")
    c2.metric("RS Momentum",  f"{row['rs_mom']:+.2f}σ",
              help="Taxa de variação do RS Ratio. Positivo = acelerando.")
    c3.metric("Perf 21d",     f"{row['perf_21d']:+.1f}%",
              help="Retorno absoluto do ativo nos últimos 21 pregões.")
    c4.metric(f"vs {indice_nome}", f"{row['perf_vs_index']:+.1f}%",
              help="Retorno do ativo menos o retorno do índice no mesmo período.")
    c5.metric("Quadrante",    f"Q{q}",
              help=style["label"])

    st.divider()

    # ── Janela de análise ────────────────────────────────────
    janela = st.select_slider(
        "Período do gráfico (pregões)",
        options=[21, 42, 63, 126, 252],
        value=63,
        format_func=lambda v: f"{v}d (~{v//21}m)",
    )

    # ── Dados para os gráficos ────────────────────────────────
    if ticker not in prices.columns:
        st.warning(f"Preço de {ticker} não disponível.")
        return

    asset_px = prices[ticker].dropna().iloc[-janela:]
    idx_px   = index_series.reindex(asset_px.index).ffill().dropna()
    common   = asset_px.index.intersection(idx_px.index)
    asset_px = asset_px.loc[common]
    idx_px   = idx_px.loc[common]

    # Normaliza base 100 no primeiro ponto
    asset_norm = asset_px / asset_px.iloc[0] * 100
    idx_norm   = idx_px   / idx_px.iloc[0]   * 100

    # RS série do dataframe
    rs_series = row.get("rs_series")
    if rs_series is not None:
        rs_plot = rs_series.iloc[-janela:]
    else:
        rs_plot = (asset_px / idx_px)
        rs_plot = (rs_plot - rs_plot.mean()) / rs_plot.std()

    # ── Gráfico duplo: preço normalizado + RS ─────────────────
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.45],
        vertical_spacing=0.04,
    )

    # Painel superior: preço normalizado
    fig.add_trace(go.Scatter(
        x=asset_norm.index, y=asset_norm.values,
        name=ticker.replace(".SA", ""),
        line=dict(color="#185FA5", width=1.8),
        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f}<extra>" + ticker.replace(".SA", "") + "</extra>",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=idx_norm.index, y=idx_norm.values,
        name=indice_nome,
        line=dict(color="#888", width=1.2, dash="dot"),
        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f}<extra>" + indice_nome + "</extra>",
    ), row=1, col=1)

    # Painel inferior: RS Ratio
    rs_color = "#3B6D11" if row["rs_ratio"] >= 0 else "#A32D2D"
    fig.add_trace(go.Scatter(
        x=rs_plot.index, y=rs_plot.values,
        name="RS Ratio (z-score)",
        line=dict(color=rs_color, width=1.5),
        fill="tozeroy",
        fillcolor=("rgba(59,109,17,0.13)" if row["rs_ratio"] >= 0 else "rgba(163,45,45,0.13)"),
        hovertemplate="%{x|%d/%m/%Y}<br>RS: %{y:+.2f}σ<extra></extra>",
    ), row=2, col=1)

    fig.add_hline(y=0,    line_dash="dot", line_color="#888", line_width=0.8, row=2, col=1)
    fig.add_hline(y=0.5,  line_dash="dash", line_color="#3B6D11", line_width=0.6, row=2, col=1)
    fig.add_hline(y=-0.5, line_dash="dash", line_color="#A32D2D", line_width=0.6, row=2, col=1)

    fig.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.04, font=dict(size=11)),
        hovermode="x unified",
    )
    fig.update_yaxes(showgrid=False, row=1, col=1, title_text="Base 100")
    fig.update_yaxes(showgrid=False, row=2, col=1, title_text="RS (σ)")
    fig.update_xaxes(showgrid=False)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(
        "Painel superior: ativo e índice normalizados (base 100 no início do período). "
        "Painel inferior: RS Ratio em z-score — linhas tracejadas marcam a banda neutra ±0.5σ."
    )
