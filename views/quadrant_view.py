# views/quadrant_view.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

GRID_LAYOUT = [[7, 8, 9], [4, 5, 6], [1, 2, 3]]
ROW_LABELS  = ["↑ Acima (> +0.5σ)", "→ Neutro (±0.5σ)", "↓ Abaixo (< -0.5σ)"]
COL_LABELS  = ["← Perdendo força (< -0.5σ)", "Estável (±0.5σ)", "Acelerando ↗ (> +0.5σ)"]

METRIC_HELP = {
    "Breadth Score":    "Varia de −100 a +100. Calcula (% acima − % abaixo). Positivo = mercado favorece os líderes.",
    "Acima do índice":  "% de ativos com RS Ratio acima da banda neutra (+0.5σ). Estão superando o benchmark.",
    "Neutros":          "% de ativos dentro da banda neutra (entre −0.5σ e +0.5σ). RS alinhado ao índice.",
    "Abaixo do índice": "% de ativos com RS Ratio abaixo da banda neutra (−0.5σ). Underperformando o benchmark.",
}


def render(df, breadth, indice_nome, idx_perf, **kwargs):
    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = None

    # Lê ticker clicado via query_params
    qp = st.query_params.get("ticker", None)
    if qp and qp != st.session_state.selected_ticker:
        st.session_state.selected_ticker = qp

    st.markdown(f"### Quadrantes — vs {indice_nome}")

    # ── Métricas com legenda ──────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    score = breadth.get("breadth_score", 0)
    c1.metric("Breadth Score",    f"{score:+d}",
              help=METRIC_HELP["Breadth Score"])
    c2.metric("Acima do índice",  f"{breadth.get('pct_up',   0):.1f}%",
              help=METRIC_HELP["Acima do índice"])
    c3.metric("Neutros",          f"{breadth.get('pct_neut', 0):.1f}%",
              help=METRIC_HELP["Neutros"])
    c4.metric("Abaixo do índice", f"{breadth.get('pct_down', 0):.1f}%",
              help=METRIC_HELP["Abaixo do índice"])
    c5.metric(f"{indice_nome} 21d", f"{idx_perf.get('21d', 0):+.1f}%",
              help="Retorno percentual do índice de referência nos últimos 21 pregões.")

    st.caption(
        "**Breadth Score** = (acima − abaixo) / total × 100  ·  "
        "**RS Ratio** = z-score do ratio preço/índice  ·  "
        "Passe o mouse nos valores para mais detalhes."
    )

    st.divider()

    # ── Grade HTML com chips clicáveis via query_params ───────
    chips_js = []   # lista de (ticker_sem_sa, ticker_completo)

    # Label do eixo horizontal (Momentum) — acima da grade
    grid_html = (
        "<div style='text-align:center;font-size:11px;font-weight:600;"
        "color:#aaa;letter-spacing:.06em;text-transform:uppercase;"
        "margin-bottom:2px;padding-left:46px'>— Momentum —</div>"
    )

    # Grade principal
    grid_html += (
        "<div style='display:grid;grid-template-columns:40px repeat(3,1fr);"
        "gap:6px;align-items:stretch'>"
    )

    # Cabeçalhos de coluna
    grid_html += "<div></div>"
    for lbl in COL_LABELS:
        grid_html += (
            f"<div style='text-align:center;font-size:12px;font-weight:500;"
            f"color:#888;padding:3px 0'>{lbl}</div>"
        )

    row_colors = ["#3B6D11", "#854F0B", "#A32D2D"]
    for row_idx, quad_row in enumerate(GRID_LAYOUT):
        # Label lateral: inclui nome do eixo 'RS' na primeira linha
        axis_label = "RS &nbsp;" if row_idx == 0 else ""
        grid_html += (
            f"<div style='display:flex;align-items:center;justify-content:center;"
            f"font-size:12px;font-weight:500;color:{row_colors[row_idx]};"
            f"writing-mode:vertical-rl;transform:rotate(180deg)'>"
            f"{axis_label}{ROW_LABELS[row_idx]}</div>"
        )
        for q in quad_row:
            style  = QUAD_STYLE[q]
            bg, tx = style["bg"], style["tx"]
            items  = df[df["quadrant"] == q]
            count  = len(items)

            chips = ""
            for _, r in items.iterrows():
                t_short = r["ticker"].replace(".SA", "")
                t_full  = r["ticker"]
                sign    = "+" if r["rs_ratio"] >= 0 else ""
                chips_js.append((t_short, t_full))
                chips += (
                    f"<span id='chip_{t_short}' "
                    f"onclick=\"selectTicker('{t_short}','{t_full}')\" "
                    f"style='background:rgba(255,255,255,0.15);color:{tx};"
                    f"font-size:11px;font-weight:500;padding:2px 6px;"
                    f"border-radius:5px;margin:2px;display:inline-block;"
                    f"cursor:pointer;transition:opacity .15s' "
                    f"onmouseover=\"this.style.opacity='.7'\" "
                    f"onmouseout=\"this.style.opacity='1'\">"
                    f"{t_short} "
                    f"<span style='opacity:.7;font-size:10px'>{sign}{r['rs_ratio']:.1f}σ</span>"
                    f"</span>"
                )

            grid_html += (
                f"<div style='background:{bg};border-radius:10px;"
                f"padding:8px;min-height:90px'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"margin-bottom:5px'>"
                f"<span style='color:{tx};font-size:18px;font-weight:500;"
                f"opacity:.22'>{q}</span>"
                f"<span style='background:rgba(255,255,255,0.15);color:{tx};"
                f"font-size:9px;font-weight:500;padding:2px 6px;"
                f"border-radius:4px'>n={count}</span>"
                f"</div>"
                f"<div style='display:flex;flex-wrap:wrap;gap:2px'>{chips}</div>"
                f"</div>"
            )

    grid_html += "</div>"

    # JS: clique no chip → atualiza URL query param → Streamlit reroda
    js = """
<script>
function selectTicker(short, full) {
    window.parent.location.search = '?ticker=' + encodeURIComponent(full);
}
</script>
"""
    st.markdown(grid_html + js, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

    # ── Selectbox agrupado por quadrante ─────────────────────
    QUAD_ICONS = {
        9: "🟢 Q9 — Acima · Acelerando",
        8: "🟩 Q8 — Acima · Estável",
        7: "🟨 Q7 — Acima · Desacelerando",
        6: "🟠 Q6 — Neutro · Acelerando",
        5: "🟡 Q5 — Neutro · Estável",
        4: "🔶 Q4 — Neutro · Perdendo",
        1: "🔴 Q1 — Abaixo · Piorando",
        2: "🟥 Q2 — Abaixo · Estável",
        3: "🩷 Q3 — Abaixo · Recuperando",
    }

    SEPARADOR = "——————————————————————"

    todas_opcoes = ["— selecionar ativo —"]
    ticker_map   = {}

    for q in [9, 8, 7, 6, 5, 4, 3, 2, 1]:
        items = df[df["quadrant"] == q]
        if items.empty:
            continue
        # Cabeçalho do grupo
        header = f"{QUAD_ICONS[q]}  ({len(items)} ativos)"
        todas_opcoes.append(header)
        ticker_map[header] = None
        # Ativos do quadrante
        for _, r in items.sort_values("rs_ratio", ascending=False).iterrows():
            sign  = "+" if r["rs_ratio"] >= 0 else ""
            label = (
                f"    {r['ticker'].replace('.SA','')} — {r['nome']}"
                f"  |  RS {sign}{r['rs_ratio']:.2f}σ  ·  mom {r['rs_mom']:+.2f}σ"
            )
            todas_opcoes.append(label)
            ticker_map[label] = r["ticker"]

    # Pré-seleciona se já houver ticker no session_state
    sel_atual = st.session_state.selected_ticker
    idx_atual = 0
    if sel_atual:
        t_short = sel_atual.replace(".SA", "")
        for i, lbl in enumerate(todas_opcoes):
            if f"    {t_short} —" in lbl:
                idx_atual = i
                break

    sel_label = st.selectbox(
        "Selecionar ativo para detalhes",
        todas_opcoes,
        index=idx_atual,
        key="sel_global",
    )

    # Ignora seleção de cabeçalhos de grupo
    if sel_label != "— selecionar ativo —" and ticker_map.get(sel_label) is not None:
        novo = ticker_map[sel_label]
        if novo and st.session_state.selected_ticker != novo:
            st.session_state.selected_ticker = novo
            st.query_params["ticker"] = novo
    elif sel_label == "— selecionar ativo —":
        st.session_state.selected_ticker = None
        st.query_params.clear()

    # ── Painel de detalhe ─────────────────────────────────────
    sel = st.session_state.selected_ticker
    if sel is not None:
        row = df[df["ticker"] == sel]
        if not row.empty:
            st.divider()
            _render_detail(row.iloc[0], indice_nome)


def _render_detail(row: pd.Series, indice_nome: str):
    q      = int(row["quadrant"])
    style  = QUAD_STYLE[q]
    ticker = row["ticker"].replace(".SA", "")

    st.markdown(
        f"<span style='background:{style['bg']};color:{style['tx']};"
        f"font-size:12px;padding:4px 12px;border-radius:6px;font-weight:500'>"
        f"{style['label']}</span>&nbsp;&nbsp;"
        f"<span style='font-size:20px;font-weight:500'>{ticker}</span>&nbsp;"
        f"<span style='font-size:14px;color:#888'>{row['nome']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RS Ratio (z-score)", f"{row['rs_ratio']:+.2f}σ",
              help="Z-score do ratio preço/índice em 252 dias. Positivo = superando o benchmark.")
    c2.metric("RS Momentum",        f"{row['rs_mom']:+.2f}σ",
              help="Taxa de variação (ROC) do RS Ratio. Positivo = força relativa acelerando.")
    c3.metric("Perf. 21d",          f"{row['perf_21d']:+.1f}%",
              help="Retorno absoluto do ativo nos últimos 21 pregões, sem considerar o índice.")
    c4.metric(f"vs {indice_nome} 21d", f"{row['perf_vs_index']:+.1f}%",
              help="Alpha relativo: retorno do ativo menos o retorno do índice no mesmo período.")

    rs_series = row.get("rs_series")
    if rs_series is not None and len(rs_series) > 0:
        _sparkline(rs_series, ticker, float(row["rs_ratio"]))

    if st.button("✕  Fechar detalhe", key="close_detail"):
        st.session_state.selected_ticker = None
        st.session_state.pop("sel_global", None)
        st.query_params.clear()
        st.rerun()


def _sparkline(series: pd.Series, ticker: str, current_val: float):
    color      = "#3B6D11" if current_val >= 0 else "#A32D2D"
    fill_color = "rgba(59,109,17,0.13)" if current_val >= 0 else "rgba(163,45,45,0.13)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy", fillcolor=fill_color,
        hovertemplate="%{x|%d/%m}<br>RS: %{y:+.2f}σ<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#888", line_width=0.8)
    fig.update_layout(
        height=120, margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=10)),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"RS Ratio (z-score) — {len(series)} pregões mais recentes")
