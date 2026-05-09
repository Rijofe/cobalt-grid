# views/scanner_view.py
# ------------------------------------------------------------
# Slide 6 â Scanner de Ciclo
# Varre todos os ativos e identifica transiÃ§Ãµes de quadrante
# recentes, classificando em sinais de compra ou venda.
# ------------------------------------------------------------

import pandas as pd
import streamlit as st

from engine.rs_calc import compute_quadrant_history

# ââ Tipo de sinal de compra âââââââââââââââââââââââââââââââââââ
# Cada transiÃ§Ã£o tem: (label_tabela, tipo_sinal)
# tipo_sinal: "recuperacao" | "entrada" | "continuacao"

BUY_TRANSITIONS = {
    (1, 2): ("Q1âQ2 â Estabilizando", "recuperacao"),
    (2, 3): ("Q2âQ3 â InÃ­cio de recuperaÃ§Ã£o", "recuperacao"),
    (3, 6): ("Q3âQ6 â ConfirmaÃ§Ã£o de rotaÃ§Ã£o", "recuperacao"),
    (6, 9): ("Q6âQ9 â Entrada na lideranÃ§a â", "entrada"),
    (4, 7): ("Q4âQ7 â Neutro direto Ã  forÃ§a", "entrada"),
    (4, 6): ("Q4âQ6 â Neutro acelerando", "entrada"),
    (5, 6): ("Q5âQ6 â Saindo do neutro para cima", "entrada"),
    (5, 8): ("Q5âQ8 â Cruzou para acima estÃ¡vel", "entrada"),
    (3, 9): ("Q3âQ9 â Salto direto (evento)", "entrada"),
    (7, 8): ("Q7âQ8 â Acelerando na lideranÃ§a", "continuacao"),
    (8, 9): ("Q8âQ9 â Consolidando lideranÃ§a â", "continuacao"),
}

SELL_TRANSITIONS = {
    (9, 8): "Q9âQ8 â LideranÃ§a desacelerando",
    (8, 7): "Q8âQ7 â ForÃ§a perdendo traÃ§Ã£o",
    (7, 4): "Q7âQ4 â Perdeu a lideranÃ§a",
    (4, 1): "Q4âQ1 â DeterioraÃ§Ã£o confirmada",
    (9, 6): "Q9âQ6 â Caiu para neutro",
    (6, 4): "Q6âQ4 â Neutro desacelerando",
    (5, 4): "Q5âQ4 â Saindo do neutro para baixo",
    (5, 2): "Q5âQ2 â Cruzou para abaixo estÃ¡vel",
}

TIPO_SINAL_LABEL = {
    "recuperacao": "ð RecuperaÃ§Ã£o",
    "entrada": "ð Entrada",
    "continuacao": "â ContinuaÃ§Ã£o",
}

QUAD_COLORS = {
    9: "#3B6D11",
    8: "#97C459",
    7: "#C0DD97",
    6: "#854F0B",
    5: "#EF9F27",
    4: "#FAC775",
    1: "#791F1F",
    2: "#E24B4A",
    3: "#F7C1C1",
}


def render(
    df,
    prices,
    index_series,
    indice_nome,
    tickers_dict,
    rs_window,
    mom_window,
    smoothing,
    neutral_band,
    **kwargs,
):

    st.markdown(f"### Scanner de Ciclo â vs {indice_nome}")

    if df.empty:
        st.warning("Nenhum dado disponÃ­vel.")
        return

    # ââ Controles âââââââââââââââââââââââââââââââââââââââââââââ
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        janela_scan = st.select_slider(
            "Janela de busca (pregÃµes)",
            options=[3, 5, 10, 21],
            value=10,
            help="Quantos pregÃµes para trÃ¡s procurar transiÃ§Ãµes.",
        )

    with col2:
        tipo = st.radio(
            "Tipo de transiÃ§Ã£o",
            options=["ð¢  Compra", "ð´  Venda", "Todas"],
            horizontal=True,
        )

    with col3:
        apenas_hoje = st.checkbox(
            "Somente hoje",
            value=False,
            help="Mostra apenas transiÃ§Ãµes ocorridas no Ãºltimo pregÃ£o.",
        )

    with st.expander("â¹ï¸ Como funciona o scanner"):
        st.markdown("""
**O que o scanner faz:**
- Calcula o histÃ³rico de quadrante de cada ativo do universo selecionado
- Detecta todas as transiÃ§Ãµes ocorridas nos Ãºltimos N pregÃµes (janela de busca)
- Classifica cada transiÃ§Ã£o como sinal de **compra** (rotaÃ§Ã£o positiva) ou **venda** (rotaÃ§Ã£o negativa)
- Ordena pela recÃªncia â transiÃ§Ãµes de hoje aparecem primeiro em **verde**

**Sinais de compra monitorados:** Q1âQ2, Q2âQ3, Q3âQ6, Q6âQ9, Q4âQ7, Q7âQ8, Q8âQ9 e variaÃ§Ãµes

**Sinais de venda monitorados:** Q9âQ8, Q8âQ7, Q7âQ4, Q4âQ1 e variaÃ§Ãµes

**Dica:** use janela de 5 dias para ver o que mudou essa semana. Use 21 dias para contexto mais amplo.
        """)

    # ââ Legenda de tipos de sinal ââââââââââââââââââââââââââââââ
    st.markdown(
        """
<div style="display:flex; gap:24px; margin: 8px 0 4px 0; flex-wrap:wrap;">
  <div style="display:flex; align-items:center; gap:6px;">
    <span style="font-size:18px;">ð</span>
    <div>
      <span style="font-weight:600;">RecuperaÃ§Ã£o</span>
      <span style="color:#888; font-size:12px; margin-left:4px;">Q1âQ2 Â· Q2âQ3 Â· Q3âQ6</span>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:6px;">
    <span style="font-size:18px;">ð</span>
    <div>
      <span style="font-weight:600;">Entrada</span>
      <span style="color:#888; font-size:12px; margin-left:4px;">Q6âQ9 Â· Q4âQ7 Â· Q4âQ6 Â· Q5âQ6 Â· Q5âQ8</span>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:6px;">
    <span style="font-size:18px;">â</span>
    <div>
      <span style="font-weight:600;">ContinuaÃ§Ã£o</span>
      <span style="color:#888; font-size:12px; margin-left:4px;">Q7âQ8 Â· Q8âQ9</span>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ââ Varredura âââââââââââââââââââââââââââââââââââââââââââââ
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
        st.info(f"Nenhuma transiÃ§Ã£o encontrada nos Ãºltimos {janela_scan} pregÃµes.")
        return

    # ââ Filtra por tipo âââââââââââââââââââââââââââââââââââââââ
    if "Compra" in tipo:
        resultados = resultados[resultados["tipo"] == "compra"]
    elif "Venda" in tipo:
        resultados = resultados[resultados["tipo"] == "venda"]

    if resultados.empty:
        st.info("Nenhuma transiÃ§Ã£o do tipo selecionado encontrada.")
        return

    # ââ MÃ©tricas resumidas ââââââââââââââââââââââââââââââââââââ
    n_compra = len(resultados[resultados["tipo"] == "compra"])
    n_venda = len(resultados[resultados["tipo"] == "venda"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Sinais de compra", n_compra)
    c2.metric("Sinais de venda", n_venda)
    c3.metric("Total de transiÃ§Ãµes", len(resultados))

    st.divider()

    # ââ Tabelas por tipo ââââââââââââââââââââââââââââââââââââââ
    compras = resultados[resultados["tipo"] == "compra"].sort_values("dias_atrÃ¡s")
    vendas = resultados[resultados["tipo"] == "venda"].sort_values("dias_atrÃ¡s")

    if not compras.empty and "Venda" not in tipo:
        st.markdown("#### ð¢ Sinais de compra")
        _render_table(compras, indice_nome, is_compra=True)

    if not vendas.empty and "Compra" not in tipo:
        st.markdown("#### ð´ Sinais de venda")
        _render_table(vendas, indice_nome, is_compra=False)


# ââ LÃ³gica de varredura âââââââââââââââââââââââââââââââââââââââ


def _scan(
    df,
    prices,
    index_series,
    tickers_dict,
    janela,
    rs_window,
    mom_window,
    smoothing,
    neutral_band,
    apenas_hoje,
):

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

        # Ãltimos N pregÃµes
        recente = hist.iloc[-janela:].reset_index(drop=True)

        # Detecta transiÃ§Ãµes
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
            rs_atual = float(df[df["ticker"] == ticker]["rs_ratio"].iloc[0])
            mom_atual = float(df[df["ticker"] == ticker]["rs_mom"].iloc[0])

            if par in BUY_TRANSITIONS:
                label, tipo_sinal = BUY_TRANSITIONS[par]
                rows.append(
                    {
                        "tipo": "compra",
                        "tipo_sinal": TIPO_SINAL_LABEL[tipo_sinal],
                        "ticker": ticker.replace(".SA", ""),
                        "nome": nome,
                        "transiÃ§Ã£o": label,
                        "de": q_ant,
                        "para": q_now,
                        "dias_atrÃ¡s": dias_atras,
                        "rs_atual": rs_atual,
                        "mom_atual": mom_atual,
                    }
                )
            elif par in SELL_TRANSITIONS:
                rows.append(
                    {
                        "tipo": "venda",
                        "tipo_sinal": "â",
                        "ticker": ticker.replace(".SA", ""),
                        "nome": nome,
                        "transiÃ§Ã£o": SELL_TRANSITIONS[par],
                        "de": q_ant,
                        "para": q_now,
                        "dias_atrÃ¡s": dias_atras,
                        "rs_atual": rs_atual,
                        "mom_atual": mom_atual,
                    }
                )

    if not rows:
        return pd.DataFrame()

    df_result = (
        pd.DataFrame(rows)
        .drop_duplicates(subset=["ticker", "de", "para"])
        .reset_index(drop=True)
    )
    # MantÃ©m apenas a transiÃ§Ã£o mais recente por ticker
    df_result = (
        df_result.sort_values("dias_atrÃ¡s")
        .drop_duplicates(subset=["ticker"], keep="first")
        .reset_index(drop=True)
    )
    return df_result


def _render_table(subset: pd.DataFrame, indice_nome: str, is_compra: bool = True):
    if subset.empty:
        return

    if is_compra:
        cols_sel = [
            "ticker",
            "nome",
            "transiÃ§Ã£o",
            "tipo_sinal",
            "dias_atrÃ¡s",
            "rs_atual",
            "mom_atual",
        ]
        col_names = [
            "Ticker",
            "Nome",
            "TransiÃ§Ã£o",
            "Tipo de sinal",
            "Dias atrÃ¡s",
            "RS atual (Ï)",
            "Mom atual (Ï)",
        ]
    else:
        cols_sel = [
            "ticker",
            "nome",
            "transiÃ§Ã£o",
            "dias_atrÃ¡s",
            "rs_atual",
            "mom_atual",
        ]
        col_names = [
            "Ticker",
            "Nome",
            "TransiÃ§Ã£o",
            "Dias atrÃ¡s",
            "RS atual (Ï)",
            "Mom atual (Ï)",
        ]

    display = subset[cols_sel].copy()
    display.columns = col_names

    def color_rs(val):
        try:
            v = float(val)
            if v > 0.5:
                return "color: #4CAF50; font-weight: 600"
            if v < -0.5:
                return "color: #F44336; font-weight: 600"
        except Exception:
            pass
        return ""

    def color_dias(val):
        try:
            v = int(val)
            if v == 0:
                return "font-weight: 500; color: #3B6D11"
            if v <= 2:
                return "font-weight: 500"
        except Exception:
            pass
        return "color: #888"

    styled = (
        display.style.map(color_rs, subset=["RS atual (Ï)", "Mom atual (Ï)"])
        .map(color_dias, subset=["Dias atrÃ¡s"])
        .format(
            {
                "RS atual (Ï)": "{:+.2f}",
                "Mom atual (Ï)": "{:+.2f}",
            }
        )
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)
