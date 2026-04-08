# app.py
# ------------------------------------------------------------
# Ponto de entrada do app. Roda com: streamlit run app.py
# ------------------------------------------------------------

from pathlib import Path

import streamlit as st
from data.csv_loader import carrega_csv, gera_exemplo_csv
from data.tickers import INDICES, UNIVERSOS
from engine.loader import index_performance, load_prices
from engine.rs_calc import (
    DEFAULT_MOM_WINDOW,
    DEFAULT_NEUTRAL_BAND,
    DEFAULT_RS_WINDOW,
    DEFAULT_ZSCORE_LOOKBACK,
    compute_breadth,
    compute_quadrants,
)

st.set_page_config(
    page_title="RS Quadrants",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## RS Quadrants")
    st.markdown("Análise de Força Relativa")
    st.divider()

    st.markdown("#### Universo de ativos")

    DATA_DIR = Path(__file__).parent / "data"
    csvs_encontrados = sorted(DATA_DIR.glob("*.csv"))
    csv_opcoes = {f.stem: f for f in csvs_encontrados}

    SEPARADOR = "─────────────────────"
    OPCAO_UPLOAD = "📂  Upload de CSV..."

    opcoes_universo = (
        list(UNIVERSOS.keys())
        + ([SEPARADOR] if csv_opcoes else [])
        + [f"📄  {nome}" for nome in csv_opcoes.keys()]
        + [SEPARADOR, OPCAO_UPLOAD]
    )

    universo = st.selectbox(
        "Lista de ativos",
        options=opcoes_universo,
        label_visibility="collapsed",
    )

    tickers_csv = None
    if universo == OPCAO_UPLOAD:
        uploaded = st.file_uploader(
            "Upload CSV (ticker, nome)",
            type=["csv"],
            help="Colunas: ticker (obrigatório) e nome (opcional). "
            "Tickers BR sem .SA são normalizados automaticamente.",
        )
        st.download_button(
            "⬇ Baixar modelo CSV",
            data=gera_exemplo_csv(),
            file_name="modelo_carteira.csv",
            mime="text/csv",
        )
        if uploaded:
            tickers_csv = carrega_csv(uploaded)
            st.caption(f"{len(tickers_csv)} ativos carregados")
        else:
            st.info("Selecione um arquivo CSV para carregar.")

    elif universo.startswith("📄  "):
        nome_csv = universo.replace("📄  ", "")
        if nome_csv in csv_opcoes:
            tickers_csv = carrega_csv(csv_opcoes[nome_csv])
            st.caption(f"{len(tickers_csv)} ativos · {nome_csv}.csv")

    st.markdown("#### Índice de referência")
    indice_nome = st.selectbox(
        "Índice",
        options=list(INDICES.keys()),
        label_visibility="collapsed",
    )
    indice_ticker = INDICES[indice_nome]

    st.divider()
    st.markdown("#### Parâmetros")

    rs_window = st.select_slider(
        "Janela RS (dias)",
        options=[5, 10, 14, 21, 42, 63],
        value=DEFAULT_RS_WINDOW,
        help="Período de suavização do RS Ratio. Mais curto = mais reativo. Mais longo = mais estável.",
    )

    mom_window = st.select_slider(
        "Janela Momentum (dias)",
        options=[3, 5, 7, 10, 14],
        value=DEFAULT_MOM_WINDOW,
        help="ROC do RS Ratio. Captura se a força relativa está acelerando ou freando.",
    )

    smoothing = st.radio(
        "Tipo de média",
        options=["EMA", "SMA"],
        index=0,
        horizontal=True,
        help="EMA reage mais rápido a mudanças recentes. SMA trata todos os dias igualmente.",
    )

    neutral_band = st.slider(
        "Banda neutra (z-score ±)",
        min_value=0.2,
        max_value=1.0,
        value=DEFAULT_NEUTRAL_BAND,
        step=0.1,
        format="%.1f",
        help="Threshold do z-score que sepera as zonas UP / NEUTRO / DOWN.",
    )

    with st.expander("ℹ️ Sobre os parâmetros"):
        st.markdown("""
**Janela RS — 21 dias**
Equivale a 1 mês de pregões. Padrão para swing trade — filtra ruído sem perder rotações setoriais.

**Janela Momentum — 5 dias**
Captura se o RS está acelerando ou freando na margem da semana. Mais curto = mais ruído; mais longo = mais lag.

**EMA vs SMA**
EMA dá mais peso aos dias recentes. Recomendado para RS pois mudanças recentes devem pesar mais.

**Banda neutra ±0.5σ**
Com ±0.5σ, ~38% dos ativos ficam no neutro em condições normais. Abaixo de ±0.3 gera rotação excessiva; acima de ±1.0 deixa quase tudo neutro.
        """)

    st.divider()
    st.markdown("#### Navegação")
    slide = st.radio(
        "Slide",
        options=[
            "📊  Quadrantes",
            "🌡️  Market Breadth",
            "🏆  Líderes & Laggards",
            "🔍  Ativo Individual",
            "📅  Histórico",
            "🔄  Scanner de Ciclo",
        ],
        label_visibility="collapsed",
    )

# ── Carregamento de dados ────────────────────────────────────
if universo in (OPCAO_UPLOAD,) or universo.startswith("📄  ") or universo == SEPARADOR:
    tickers_dict = tickers_csv or {}
else:
    tickers_dict = UNIVERSOS.get(universo, {})
tickers_list = list(tickers_dict.keys())

with st.spinner("Baixando preços..."):
    try:
        prices, index_series = load_prices(tickers_list, indice_ticker)
        idx_perf = index_performance(index_series)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

with st.spinner("Calculando RS..."):
    df = compute_quadrants(
        prices=prices,
        index_series=index_series,
        nomes=tickers_dict,
        rs_window=rs_window,
        mom_window=mom_window,
        zscore_lookback=DEFAULT_ZSCORE_LOOKBACK,
        smoothing=smoothing,
        neutral_band=neutral_band,
    )
    breadth = compute_breadth(df)

if df.empty:
    st.error("Nenhum dado disponível para os parâmetros selecionados.")
    st.stop()

# ── Roteamento de slides ──────────────────────────────────────
params = dict(
    df=df,
    breadth=breadth,
    index_series=index_series,
    prices=prices,
    indice_nome=indice_nome,
    idx_perf=idx_perf,
    universo=universo,
    tickers_dict=tickers_dict,
    rs_window=rs_window,
    mom_window=mom_window,
    smoothing=smoothing,
    neutral_band=neutral_band,
)

if "Quadrantes" in slide:
    from views.quadrant_view import render

    render(**params)

elif "Breadth" in slide:
    from views.breadth_view import render

    render(**params)

elif "Líderes" in slide:
    from views.leaders_view import render

    render(**params)

elif "Individual" in slide:
    from views.ticker_view import render

    render(**params)

elif "Histórico" in slide:
    from views.history_view import render

    render(**params)

elif "Scanner" in slide:
    from views.scanner_view import render

    render(**params)
