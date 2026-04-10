# views/scanner_view.py
# ------------------------------------------------------------
# Slide 6 — Scanner de Ciclo
# Varre todos os ativos e identifica transições de quadrante
# recentes, classificando em sinais de compra ou venda.
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
from engine.rs_calc import compute_quadrant_history

# Transições relevantes
BUY_TRANSITIONS = {
    (1, 2): "Q1→Q2 — Estabilizando",
    (2, 3): "Q2→Q3 — Início de recuperação",
    (3, 6): "Q3→Q6 — Confirmação de rotação",
    (6, 9): "Q6→Q9 — Entrada na liderança ★",
    (4, 6): "Q4→Q6 — Neutro acelerando",
    (5, 6): "Q5→Q6 — Saindo do neutro para cima",
    (5, 8): "Q5→Q8 — Cruzou para acima estável",
    (3, 9): "Q3→Q9 — Salto direto (evento)",
}

SELL_TRANSITIONS = {
    (9, 8): "Q9→Q8 — Liderança desacelerando",
    (8, 7): "Q8→Q7 — Força perdendo tração",
    (7, 4): "Q7→Q4 — Perdeu a liderança",
    (4, 1): "Q4→Q1 — Deterioração confirmada",
    (9, 6): "Q9→Q6 — Caiu para neutro",
    (6, 4): "Q6→Q4 — Neutro desacelerando",
    (5, 4): "Q5→Q4 — Saindo do neutro para baixo",
    (5, 2): "Q5→Q2 — Cruzou para abaixo estável",
}

QUAD_COLORS = {
    9: "#3B6D11", 8: "#97C459", 7: "#C0DD97",
    6: "#854F0B", 5: "#EF9F27", 4: "#FAC775",
    1: "#791F1F", 2: "#E24B4A", 3: "#F7C1C1",
}


def render(df, prices, index_series, indice_nome, tickers_dict,
           rs_window, mom_window, smoothing, neutral_band, **kwargs):

    st.markdown(f"### Scanner de Ciclo — vs {indice_nome}")

    if df.empty:
        st.warning("Nenhum dado disponível.")
        return

    # ── Controles ─────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        janela_scan = st.select_slider(
            "Janela de busca (pregões)",
            options=[3, 5, 10, 21],
            value=10,
            help="Quantos pregões para trás procurar transições.",
        )

    with col2:
        tipo = st.radio(
            "Tipo de transição",
            options=["🟢  Compra", "🔴  Venda", "Todas"],
            horizontal=True,
        )

    with col3:
        apenas_hoje = st.checkbox(
            "Somente hoje",
            value=False,
            help="Mostra apenas transições ocorridas no último pregão.",
        )

    with st.expander("ℹ️ Como funciona o scanner"):
        st.markdown("""
**O que o scanner faz:**
- Calcula o histórico de quadrante de cada ativo do universo selecionado
- Detecta todas as transições ocorridas nos últimos N pregões (janela de busca)
- Classifica cada transição como sinal de **compra** (rotação positiva) ou **venda** (rotação negativa)
- Ordena pela recência — transições de hoje aparecem primeiro em **verde**

**Sinais de compra monitorados:** Q1→Q2, Q2→Q3, Q3→Q6, Q6→Q9 e variações

**Sinais de venda monitorados:** Q9→Q8, Q8→Q7, Q7→Q4, Q4→Q1 e variações

**Dica:** use janela de 5 dias para ver o que mudou essa semana. Use 21 dias para contexto mais amplo.
        """)

    st.divider()

    # ── Varredura ─────────────────────────────────────────────
    with st.spinner(f"Varrendo {len(df)} ativos..."):
        resultados = _scan(
            df=df,
            prices=prices,
            index_series=index_series,
            tickers_dict=tickers_dict,
            janela=janela_scan,
            rs_window=rs_window,
            mom_window=mom_window,
            smoothing=smoothing,
            neutral_band=neutral_band,
            apenas_hoje=apenas_hoje,
        )

    if resultados.empty:
        st.info(f"Nenhuma transição encontrada nos últimos {janela_scan} pregões.")
        return

    # ── Filtra por tipo ───────────────────────────────────────
    if "Compra" in tipo:
        resultados = resultados[resultados["tipo"] == "compra"]
    elif "Venda" in tipo:
        resultados = resultados[resultados["tipo"] == "venda"]

    if resultados.empty:
        st.info("Nenhuma transição do tipo selecionado encontrada.")
        return

    # ── Métricas resumidas ────────────────────────────────────
    n_compra = len(resultados[resultados["tipo"] == "compra"])
    n_venda  = len(resultados[resultados["tipo"] == "venda"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Sinais de compra", n_compra)
    c2.metric("Sinais de venda",  n_venda)
    c3.metric("Total de transições", len(resultados))

    st.divider()

    # ── Tabelas por tipo ──────────────────────────────────────
    compras = resultados[resultados["tipo"] == "compra"].sort_values("dias_atrás")
    vendas  = resultados[resultados["tipo"] == "venda"].sort_values("dias_atrás")

    if not compras.empty and "Venda" not in tipo:
        st.markdown("#### 🟢 Sinais de compra")
        _render_table(compras, indice_nome)

    if not vendas.empty and "Compra" not in tipo:
        st.markdown("#### 🔴 Sinais de venda")
        _render_table(vendas, indice_nome)


# ── Lógica de varredura ───────────────────────────────────────

def _scan(df, prices, index_series, tickers_dict, janela,
          rs_window, mom_window, smoothing, neutral_band, apenas_hoje):

    rows = []

    for ticker in df["ticker"].tolist():
        hist = compute_quadrant_history(
            prices=prices,
            index_series=index_series,
            ticker=ticker,
            rs_window=rs_window,
            mom_window=mom_window,
            smoothing=smoothing,
            neutral_band=neutral_band,
        )

        if hist.empty or len(hist) < 2:
            continue

        # Últimos N pregões
        recente = hist.iloc[-janela:].reset_index(drop=True)

        # Detecta transições
        for i in range(1, len(recente)):
            q_ant = int(recente.loc[i - 1, "quadrant"])
            q_now = int(recente.loc[i, "quadrant"])

            if q_ant == q_now:
                continue

            dias_atras = len(recente) - 1 - i  # 0 = hoje

            if apenas_hoje and dias_atras > 0:
                continue

            par = (q_ant, q_now)
            nome = tickers_dict.get(ticker, ticker.replace(".SA", ""))
            rs_atual  = float(df[df["ticker"] == ticker]["rs_ratio"].iloc[0])
            mom_atual = float(df[df["ticker"] == ticker]["rs_mom"].iloc[0])

            if par in BUY_TRANSITIONS:
                rows.append({
                    "tipo":       "compra",
                    "ticker":     ticker.replace(".SA", ""),
                    "nome":       nome,
                    "transição":  BUY_TRANSITIONS[par],
                    "de":         q_ant,
                    "para":       q_now,
                    "dias_atrás": dias_atras,
                    "rs_atual":   rs_atual,
                    "mom_atual":  mom_atual,
                })
            elif par in SELL_TRANSITIONS:
                rows.append({
                    "tipo":       "venda",
                    "ticker":     ticker.replace(".SA", ""),
                    "nome":       nome,
                    "transição":  SELL_TRANSITIONS[par],
                    "de":         q_ant,
                    "para":       q_now,
                    "dias_atrás": dias_atras,
                    "rs_atual":   rs_atual,
                    "mom_atual":  mom_atual,
                })

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).drop_duplicates(
        subset=["ticker", "de", "para"]
    ).reset_index(drop=True)


def _render_table(subset: pd.DataFrame, indice_nome: str):
    if subset.empty:
        return

    display = subset[["ticker", "nome", "transição", "dias_atrás",
                       "rs_atual", "mom_atual"]].copy()
    display.columns = ["Ticker", "Nome", "Transição",
                        "Dias atrás", "RS atual (σ)", "Mom atual (σ)"]

    def color_rs(val):
        try:
            v = float(val)
            if v > 0.5:  return "color: #4CAF50; font-weight: 600"
            if v < -0.5: return "color: #F44336; font-weight: 600"
        except Exception:
            pass
        return ""

    def color_dias(val):
        try:
            v = int(val)
            if v == 0: return "font-weight: 500; color: #3B6D11"
            if v <= 2: return "font-weight: 500"
        except Exception:
            pass
        return "color: #888"

    styled = (
        display.style
        .map(color_rs,   subset=["RS atual (σ)", "Mom atual (σ)"])
        .map(color_dias, subset=["Dias atrás"])
        .format({
            "RS atual (σ)":  "{:+.2f}",
            "Mom atual (σ)": "{:+.2f}",
        })
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)
