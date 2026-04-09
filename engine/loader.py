# engine/loader.py
# ------------------------------------------------------------
# Responsabilidade: baixar preços de fechamento ajustados via
# yfinance e devolver DataFrames limpos com cache do Streamlit.
# ------------------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


# ── Constantes ───────────────────────────────────────────────
LOOKBACK_DAYS = 400   # dias corridos para cobrir ~252 pregões + folga
MAX_RETRIES   = 2     # tentativas em caso de falha de rede

# Ticker virtual para IBOV dolarizado (calculado internamente)
IBOV_USD_TICKER = "__IBOV_USD__"


# ── Funções públicas ──────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(
    tickers: list[str],
    index_ticker: str,
    lookback_days: int = LOOKBACK_DAYS,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Baixa preços de fechamento ajustados para os ativos e para o índice.

    Parâmetros
    ----------
    tickers       : lista de tickers dos ativos (ex: ['WEGE3.SA', 'VALE3.SA'])
    index_ticker  : ticker do índice de referência (ex: '^BVSP')
    lookback_days : quantos dias corridos retroativos baixar

    Retorna
    -------
    prices : DataFrame  shape=(dias, n_ativos) — fechamento ajustado dos ativos
    index  : Series     shape=(dias,)           — fechamento ajustado do índice
    """
    end   = datetime.today()
    start = end - timedelta(days=lookback_days)

    # IBOV dolarizado: baixa ^BVSP e BRL=X separadamente
    if index_ticker == IBOV_USD_TICKER:
        raw = _download(list(set(tickers)), start, end)
        ibov_raw = _download(["^BVSP", "BRL=X"], start, end)
        if isinstance(ibov_raw.columns, pd.MultiIndex):
            bvsp = ibov_raw["Close"]["^BVSP"]
            brl  = ibov_raw["Close"]["BRL=X"]
        else:
            bvsp = ibov_raw["Close"]
            brl  = ibov_raw["Close"]
        bvsp = _clean_series(bvsp)
        brl  = _clean_series(brl)
        common_fx = bvsp.index.intersection(brl.index)
        ibov_usd  = (bvsp.loc[common_fx] / brl.loc[common_fx]).rename(IBOV_USD_TICKER)
    else:
        all_tickers = list(set(tickers + [index_ticker]))
        raw = _download(all_tickers, start, end)

    # Extrai coluna "Close" independente de versão do yfinance
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": all_tickers[0]})

    close = _clean(close)

    # Separa índice dos ativos
    if index_ticker == IBOV_USD_TICKER:
        index_series = ibov_usd
        prices       = close
    elif index_ticker in close.columns:
        index_series = close[index_ticker].rename(index_ticker)
        asset_cols   = [c for c in close.columns if c != index_ticker]
        prices       = close[asset_cols]
    else:
        raise ValueError(
            f"Índice '{index_ticker}' não encontrado nos dados baixados. "
            "Verifique o ticker e sua conexão."
        )

    # Remove ativos sem dados suficientes (< 30 pregões)
    prices = prices.loc[:, prices.count() >= 30]

    # Garante que índice e ativos têm datas em comum suficientes
    # (índices como SMLL.SA podem ter calendário ligeiramente diferente)
    common = prices.index.intersection(index_series.dropna().index)
    if len(common) < 30:
        raise ValueError(
            f"Índice '{index_ticker}' tem apenas {len(common)} datas em comum "
            "com os ativos. Tente outro índice de referência."
        )
    prices       = prices.reindex(common).ffill()
    index_series = index_series.reindex(common).ffill()

    return prices, index_series


@st.cache_data(ttl=3600, show_spinner=False)
def load_index_only(index_ticker: str, lookback_days: int = LOOKBACK_DAYS) -> pd.Series:
    """
    Baixa apenas o índice de referência — usado para calcular
    a performance absoluta do benchmark na tela de Market Breadth.
    """
    end   = datetime.today()
    start = end - timedelta(days=lookback_days)
    raw   = _download([index_ticker], start, end)

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"][index_ticker]
    else:
        close = raw["Close"]

    return _clean_series(close).rename(index_ticker)


def index_performance(index_series: pd.Series) -> dict[str, float]:
    """
    Calcula a performance percentual do índice em janelas fixas.

    Retorna dict com chaves: '5d', '21d', '63d', 'ytd'
    """
    s = index_series.dropna()
    if len(s) < 5:
        return {"5d": 0.0, "21d": 0.0, "63d": 0.0, "ytd": 0.0}

    last  = s.iloc[-1]
    perf  = {}

    for label, n in [("5d", 5), ("21d", 21), ("63d", 63)]:
        if len(s) > n:
            perf[label] = round((last / s.iloc[-(n + 1)] - 1) * 100, 2)
        else:
            perf[label] = None

    # YTD: primeiro pregão do ano corrente
    year_start = s[s.index.year == s.index[-1].year]
    if len(year_start) > 1:
        perf["ytd"] = round((last / year_start.iloc[0] - 1) * 100, 2)
    else:
        perf["ytd"] = None

    return perf


# ── Funções internas ──────────────────────────────────────────

def _download(tickers: list[str], start: datetime, end: datetime) -> pd.DataFrame:
    """Wrapper do yf.download com tratamento de erro."""
    for attempt in range(MAX_RETRIES):
        try:
            df = yf.download(
                tickers,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False,
                threads=True,
            )
            if not df.empty:
                return df
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise ConnectionError(
                    f"Falha ao baixar dados do Yahoo Finance após {MAX_RETRIES} tentativas. "
                    f"Erro: {e}"
                )
    return pd.DataFrame()


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas totalmente vazias e preenche gaps internos."""
    df = df.dropna(axis=1, how="all")
    df = df.ffill().dropna(how="all")
    return df


def _clean_series(s: pd.Series) -> pd.Series:
    return s.ffill().dropna()
