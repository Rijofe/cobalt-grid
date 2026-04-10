# app.py
# ------------------------------------------------------------
# Ponto de entrada do app. Roda com: streamlit run app.py
# ------------------------------------------------------------

import streamlit as st
import datetime
from data.tickers import INDICES, UNIVERSOS
from data.csv_loader import carrega_csv, gera_exemplo_csv
from pathlib import Path
from engine.loader import load_prices, load_index_only, index_performance
from engine.rs_calc import (
    DEFAULT_RS_WINDOW, DEFAULT_MOM_WINDOW,
    DEFAULT_ZSCORE_LOOKBACK, DEFAULT_SMOOTHING, DEFAULT_NEUTRAL_BAND,
    compute_quadrants, compute_breadth,
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

    # Detecta CSVs na pasta data/
    DATA_DIR = Path(__file__).parent / "data"
    csvs_encontrados = sorted(DATA_DIR.glob("*.csv"))
    csv_opcoes = {f.stem: f for f in csvs_encontrados}  # nome sem extensão → path

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

    # Upload avulso
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
        help="Threshold do z-score que separa as zonas UP / NEUTRO / DOWN.",
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
            "🏭  Setorial",
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
        prices, index_series, index_volume_last = load_prices(tickers_list, indice_ticker)
        idx_perf = index_performance(index_series, indice_ticker)
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

# ── Caption de data dos dados ─────────────────────────────────
def _data_caption(series, volume_last=-1.0):
    import datetime
    import pytz
    tz_br = pytz.timezone("America/Sao_Paulo")
    agora_br = datetime.datetime.now(tz_br)
    hoje_str = agora_br.strftime("%d/%m/%Y")
    hora_carga = agora_br.strftime("%H:%M")
    # Apos 18h15 o fechamento ja foi processado pelo YF
    fechamento_confirmado = (agora_br.hour > 18) or (agora_br.hour == 18 and agora_br.minute >= 15)

    if fechamento_confirmado:
        return f"📅 Dados de {hoje_str} · fechamento · carregado as {hora_carga}"
    else:
        return f"📅 Dados de {hoje_str} · carregado as {hora_carga} · defasagem de ate 1h15min"

_caption_texto = _data_caption(index_series, index_volume_last)

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
    st.caption(_caption_texto)
    render(**params)

elif "Setorial" in slide:
    from views.sector_view import render
    st.caption(_caption_texto)
    render(**params)

elif "Breadth" in slide:
    from views.breadth_view import render
    st.caption(_caption_texto)
    render(**params)

elif "Líderes" in slide:
    from views.leaders_view import render
    st.caption(_caption_texto)
    render(**params)

elif "Individual" in slide:
    from views.ticker_view import render
    st.caption(_caption_texto)
    render(**params)

elif "Histórico" in slide:
    from views.history_view import render
    st.caption(_caption_texto)
    render(**params)

elif "Scanner" in slide:
    from views.scanner_view import render
    st.caption(_caption_texto)
    render(**params)

# ── Exportação ────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.markdown("#### Exportar slide atual")

    slide_ok = True  # todos os slides suportam exportação
    if slide_ok:
        col_e1, col_e2 = st.columns(2)

        def _gera_exports():
            from views.export_utils import (exporta_quadrantes, exporta_scanner,
                                             exporta_lideres, exporta_ativo,
                                             exporta_breadth, exporta_historico)
            exp_params = dict(rs_window=rs_window, mom_window=mom_window,
                              smoothing=smoothing, neutral_band=neutral_band)
            if "Quadrantes" in slide:
                sel = st.session_state.get("selected_ticker", None)
                breadth_ext = {**breadth, "idx_perf_21d": idx_perf.get("21d")}
                png, pdf = exporta_quadrantes(df, indice_nome, breadth_ext, exp_params,
                                              selected_ticker=sel,
                                              prices=prices, index_series=index_series)
                label = "quadrantes"
            elif "Scanner" in slide:
                from views.scanner_view import _scan
                janela_s = st.session_state.get("scanner_janela", 10)
                resultados = _scan(df, prices, index_series, tickers_dict, janela_s,
                                   rs_window, mom_window, smoothing, neutral_band, False)
                compras = resultados[resultados["tipo"] == "compra"] if not resultados.empty else pd.DataFrame()
                vendas  = resultados[resultados["tipo"] == "venda"]  if not resultados.empty else pd.DataFrame()
                png, pdf = exporta_scanner(compras, vendas, indice_nome, janela_s)
                label = "scanner"
            elif "Lideres" in slide:
                png, pdf = exporta_lideres(df, indice_nome)
                label = "lideres_laggards"
            elif "Individual" in slide:
                sel = st.session_state.get("ticker_individual", df["ticker"].iloc[0])
                row = df[df["ticker"] == sel].iloc[0] if not df[df["ticker"] == sel].empty else df.iloc[0]
                janela_i = st.session_state.get("janela_individual", 63)
                png, pdf = exporta_ativo(row, indice_nome, prices, index_series, janela_i)
                label = "ativo_individual"
            elif "Breadth" in slide:
                png, pdf = exporta_breadth(df, breadth, indice_nome, idx_perf)
                label = "market_breadth"
            elif "Historico" in slide or "Histórico" in slide:
                sel = st.session_state.get("ticker_historico", df["ticker"].iloc[0])
                janela_h = st.session_state.get("janela_historico", 126)
                from engine.rs_calc import compute_quadrant_history
                hist = compute_quadrant_history(
                    prices=prices, index_series=index_series, ticker=sel,
                    rs_window=rs_window, mom_window=mom_window,
                    smoothing=smoothing, neutral_band=neutral_band,
                )
                hist_sub = hist.iloc[-janela_h:].reset_index(drop=True) if not hist.empty else hist
                ticker_clean = sel.replace(".SA","")
                png, pdf = exporta_historico(hist_sub, ticker_clean, indice_nome, janela_h)
                label = "historico"
            else:
                png, pdf = exporta_lideres(df, indice_nome)
                label = "slide"
            return png, pdf, label

        if "export_cache" not in st.session_state:
            st.session_state.export_cache = None

        if st.button("⚙ Gerar exportação", use_container_width=True):
            with st.spinner("Gerando..."):
                try:
                    png, pdf, label = _gera_exports()
                    data_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                    st.session_state.export_cache = {
                        "png": png, "pdf": pdf,
                        "label": label, "data_str": data_str,
                    }
                except Exception as e:
                    st.error(f"Erro: {e}")
                    st.session_state.export_cache = None

        if st.session_state.export_cache:
            c = st.session_state.export_cache
            col_e1.download_button(
                "⬇ PNG", data=c["png"],
                file_name=f"{c['data_str']}_{c['label']}.png",
                mime="image/png", key="dl_png",
            )
            col_e2.download_button(
                "⬇ PDF", data=c["pdf"],
                file_name=f"{c['data_str']}_{c['label']}.pdf",
                mime="application/pdf", key="dl_pdf",
            )
