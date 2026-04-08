# views/leaders_view.py
# ------------------------------------------------------------
# Slide 3 — Tabela ranqueada: líderes (Q9→Q7) e laggards (Q1→Q3)
# com filtros por quadrante e exportação CSV.
# ------------------------------------------------------------

import streamlit as st
import pandas as pd


QUAD_STYLE = {
    9: {"bg": "#3B6D11", "tx": "#EAF3DE"},
    8: {"bg": "#97C459", "tx": "#173404"},
    7: {"bg": "#C0DD97", "tx": "#27500A"},
    6: {"bg": "#854F0B", "tx": "#FAEEDA"},
    5: {"bg": "#EF9F27", "tx": "#412402"},
    4: {"bg": "#FAC775", "tx": "#633806"},
    1: {"bg": "#791F1F", "tx": "#FCEBEB"},
    2: {"bg": "#E24B4A", "tx": "#FCEBEB"},
    3: {"bg": "#F7C1C1", "tx": "#791F1F"},
}

QUAD_LABELS = {
    9: "Q9 — Acima · Acelerando",
    8: "Q8 — Acima · Estável",
    7: "Q7 — Acima · Desacelerando",
    6: "Q6 — Neutro · Acelerando",
    5: "Q5 — Neutro · Estável",
    4: "Q4 — Neutro · Perdendo",
    3: "Q3 — Abaixo · Recuperando",
    2: "Q2 — Abaixo · Estável",
    1: "Q1 — Abaixo · Piorando",
}


def render(df, indice_nome, breadth, **kwargs):
    st.markdown(f"### Líderes & Laggards — vs {indice_nome}")

    # ── Filtros ───────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

    with col_f1:
        quads_sel = st.multiselect(
            "Filtrar por quadrante",
            options=list(range(9, 0, -1)),
            default=list(range(9, 0, -1)),
            format_func=lambda q: QUAD_LABELS[q],
        )

    with col_f2:
        sort_by = st.selectbox(
            "Ordenar por",
            options=["RS Ratio", "RS Momentum", "Perf 21d", "vs Índice 21d"],
        )

    with col_f3:
        ordem = st.radio("Ordem", ["↓ Maior", "↑ Menor"], horizontal=True)

    sort_col = {
        "RS Ratio":     "rs_ratio",
        "RS Momentum":  "rs_mom",
        "Perf 21d":     "perf_21d",
        "vs Índice 21d":"perf_vs_index",
    }[sort_by]

    ascending = (ordem == "↑ Menor")

    # ── Dados filtrados ───────────────────────────────────────
    filtered = df[df["quadrant"].isin(quads_sel)].copy()
    filtered = filtered.sort_values(sort_col, ascending=ascending).reset_index(drop=True)

    st.caption(f"{len(filtered)} ativos exibidos de {len(df)} total")
    st.divider()

    # ── Tabs Líderes / Laggards / Todos ──────────────────────
    tab_lid, tab_lag, tab_all = st.tabs([
        f"🏆 Líderes — Q7, Q8, Q9  ({breadth.get('up', 0)})",
        f"⚠️  Laggards — Q1, Q2, Q3  ({breadth.get('down', 0)})",
        f"📋 Todos  ({len(filtered)})",
    ])

    with tab_lid:
        lid = filtered[filtered["quadrant"] >= 7]
        _render_table(lid, indice_nome, show_top=True)

    with tab_lag:
        lag = filtered[filtered["quadrant"] <= 3].sort_values(
            sort_col, ascending=not ascending
        )
        _render_table(lag, indice_nome, show_top=False)

    with tab_all:
        _render_table(filtered, indice_nome)
        _export_button(filtered, indice_nome)


# ── Sub-componentes ───────────────────────────────────────────

def _render_table(subset: pd.DataFrame, indice_nome: str, show_top: bool = None):
    if subset.empty:
        st.caption("Nenhum ativo nesta seleção.")
        return

    display = subset[["ticker", "nome", "quadrant", "rs_ratio", "rs_mom",
                       "perf_21d", "perf_vs_index"]].copy()
    display.columns = ["Ticker", "Nome", "Q", "RS Ratio (σ)", "RS Mom (σ)",
                        "Perf 21d %", f"vs {indice_nome} 21d %"]
    display["Ticker"] = display["Ticker"].str.replace(".SA", "", regex=False)
    display["Q"] = display["Q"].map(QUAD_LABELS)

    def color_rs(val):
        try:
            v = float(val)
            if v > 0.5:   return "color: #27500A; font-weight: 500"
            if v < -0.5:  return "color: #791F1F; font-weight: 500"
        except Exception:
            pass
        return ""

    def color_perf(val):
        try:
            v = float(val)
            if v > 0: return "color: #27500A"
            if v < 0: return "color: #791F1F"
        except Exception:
            pass
        return ""

    styled = (
        display.style
        .applymap(color_rs,   subset=["RS Ratio (σ)", "RS Mom (σ)"])
        .applymap(color_perf, subset=["Perf 21d %", f"vs {indice_nome} 21d %"])
        .format({
            "RS Ratio (σ)":           "{:+.2f}",
            "RS Mom (σ)":             "{:+.2f}",
            "Perf 21d %":             "{:+.1f}",
            f"vs {indice_nome} 21d %":"{:+.1f}",
        })
    )

    st.dataframe(styled, use_container_width=True, hide_index=True, height=420)


def _export_button(df: pd.DataFrame, indice_nome: str):
    export = df[["ticker", "nome", "quadrant", "rs_ratio", "rs_mom",
                  "perf_21d", "perf_vs_index"]].copy()
    export.columns = ["Ticker", "Nome", "Quadrante", "RS Ratio", "RS Momentum",
                       "Perf 21d %", f"vs {indice_nome} 21d %"]
    export["Ticker"] = export["Ticker"].str.replace(".SA", "", regex=False)

    csv = export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Exportar CSV",
        data=csv,
        file_name=f"rs_quadrants_{indice_nome.replace(' ','_')}.csv",
        mime="text/csv",
    )
