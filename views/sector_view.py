# views/sector_view.py
# ------------------------------------------------------------
# Slide 2 — Análise Setorial
# Nível 1: ranking de setores por RS médio
# Nível 2: drill-down com ativos do setor selecionado
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.tickers import SETORES

SETOR_SEM_INFO = "Sem setor"


def _get_setor(ticker: str) -> str:
    return SETORES.get(ticker, SETOR_SEM_INFO)


def render(df, indice_nome, tickers_dict, **kwargs):
    st.markdown(f"### Analise Setorial — vs {indice_nome}")

    if df.empty:
        st.warning("Nenhum dado disponivel.")
        return

    # Adiciona coluna de setor
    df = df.copy()
    df["setor"] = df["ticker"].apply(_get_setor)

    # Remove ativos sem setor se a maioria tiver (CSV personalizado pode nao ter)
    tem_setor = df[df["setor"] != SETOR_SEM_INFO]
    sem_setor = df[df["setor"] == SETOR_SEM_INFO]

    if len(tem_setor) == 0:
        st.info(
            "Nenhum setor encontrado para este universo. "
            "O mapeamento de setores esta disponivel para os universos Ibovespa e SMLL. "
            "Para outros universos, adicione uma coluna 'setor' ao seu CSV."
        )
        return

    # ── Nível 1 — Ranking setorial ───────────────────────────
    resumo = (
        tem_setor.groupby("setor")
        .agg(
            n_ativos=("ticker", "count"),
            rs_medio=("rs_ratio", "mean"),
            mom_medio=("rs_mom", "mean"),
            pct_acima=("quadrant", lambda x: (x >= 7).mean() * 100),
            pct_neutro=("quadrant", lambda x: (x.between(4, 6)).mean() * 100),
            pct_abaixo=("quadrant", lambda x: (x <= 3).mean() * 100),
            perf_21d=("perf_21d", "mean"),
        )
        .reset_index()
        .sort_values("rs_medio", ascending=False)
    )

    st.markdown("#### Ranking de Setores por RS Medio")

    # Gráfico de barras horizontal
    colors = [
        "#4CAF50" if v > 0.5 else "#F44336" if v < -0.5 else "#EF9F27"
        for v in resumo["rs_medio"]
    ]

    fig_bar = go.Figure(go.Bar(
        y=resumo["setor"],
        x=resumo["rs_medio"].round(2),
        orientation="h",
        marker_color=colors,
        text=resumo["rs_medio"].round(2).apply(lambda v: f"{v:+.2f}s"),
        textposition="outside",
        customdata=resumo[["n_ativos", "pct_acima", "pct_abaixo", "perf_21d"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "RS Medio: %{x:+.2f}s<br>"
            "Ativos: %{customdata[0]}<br>"
            "Acima: %{customdata[1]:.1f}%<br>"
            "Abaixo: %{customdata[2]:.1f}%<br>"
            "Perf 21d: %{customdata[3]:+.1f}%<br>"
            "<extra></extra>"
        ),
    ))

    fig_bar.update_layout(
        height=max(300, len(resumo) * 38),
        margin=dict(l=10, r=80, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dddddd", size=12),
        xaxis=dict(
            gridcolor="#2a2a2a", zerolinecolor="#555555",
            title="RS Ratio Medio (z-score)"
        ),
        yaxis=dict(gridcolor="#2a2a2a"),
        showlegend=False,
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # Tabela resumo
    with st.expander("Ver tabela completa de setores"):
        display = resumo.copy()
        display["rs_medio"]   = display["rs_medio"].map("{:+.2f}s".format)
        display["mom_medio"]  = display["mom_medio"].map("{:+.2f}s".format)
        display["pct_acima"]  = display["pct_acima"].map("{:.1f}%".format)
        display["pct_neutro"] = display["pct_neutro"].map("{:.1f}%".format)
        display["pct_abaixo"] = display["pct_abaixo"].map("{:.1f}%".format)
        display["perf_21d"]   = display["perf_21d"].map("{:+.1f}%".format)
        display.columns = ["Setor", "Ativos", "RS Medio", "Mom Medio",
                           "% Acima", "% Neutro", "% Abaixo", "Perf 21d"]
        st.dataframe(display, use_container_width=True, hide_index=True)

    st.divider()

    # ── Nível 2 — Drill-down por setor ───────────────────────
    st.markdown("#### Drill-down por Setor")

    setores_disponiveis = ["— Selecione um setor —"] + resumo["setor"].tolist()
    setor_sel = st.selectbox(
        "Setor",
        options=setores_disponiveis,
        label_visibility="collapsed",
    )

    if setor_sel == "— Selecione um setor —":
        st.caption("Selecione um setor acima para ver os ativos individualmente.")
        return

    subset = tem_setor[tem_setor["setor"] == setor_sel].sort_values(
        "rs_ratio", ascending=False
    )

    if subset.empty:
        st.info("Nenhum ativo encontrado para este setor.")
        return

    # Métricas do setor
    rs_med  = subset["rs_ratio"].mean()
    mom_med = subset["rs_mom"].mean()
    p21_med = subset["perf_21d"].mean()
    n       = len(subset)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ativos", n)
    c2.metric("RS Medio", f"{rs_med:+.2f}σ")
    c3.metric("Mom Medio", f"{mom_med:+.2f}σ")
    c4.metric("Perf 21d Medio", f"{p21_med:+.1f}%")

    # Tabela de ativos do setor
    QUAD_COLORS = {
        9: "#3B6D11", 8: "#97C459", 7: "#C0DD97",
        6: "#854F0B", 5: "#EF9F27", 4: "#FAC775",
        1: "#791F1F", 2: "#E24B4A", 3: "#F7C1C1",
    }

    def color_rs(val):
        try:
            v = float(str(val).replace("s", "").replace("σ", ""))
            if v > 0.5:  return "color: #4CAF50; font-weight: 500"
            if v < -0.5: return "color: #F44336; font-weight: 500"
        except Exception:
            pass
        return ""

    def color_q(val):
        try:
            q = int(str(val).replace("Q", ""))
            bg = QUAD_COLORS.get(q, "#333333")
            return f"background-color: {bg}; color: white; font-weight: bold; border-radius: 4px"
        except Exception:
            return ""

    display2 = subset[["ticker", "nome", "quadrant", "rs_ratio",
                        "rs_mom", "perf_21d", "perf_vs_index"]].copy()
    display2["ticker"]   = display2["ticker"].str.replace(".SA", "", regex=False)
    display2["quadrant"] = display2["quadrant"].apply(lambda q: f"Q{int(q)}")
    display2["rs_ratio"] = display2["rs_ratio"].map("{:+.2f}s".format)
    display2["rs_mom"]   = display2["rs_mom"].map("{:+.2f}s".format)
    display2["perf_21d"] = display2["perf_21d"].map("{:+.1f}%".format)
    display2["perf_vs_index"] = display2["perf_vs_index"].map("{:+.1f}%".format)
    display2.columns = ["Ticker", "Nome", "Q", "RS Ratio", "RS Mom",
                        "Perf 21d", f"vs {indice_nome[:15]}"]

    styled = (
        display2.style
        .map(color_rs, subset=["RS Ratio", "RS Mom", "Perf 21d",
                                    f"vs {indice_nome[:15]}"])
        .map(color_q, subset=["Q"])
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    if len(sem_setor) > 0:
        st.caption(
            f"{len(sem_setor)} ativos sem mapeamento de setor nao aparecem neste slide."
        )
