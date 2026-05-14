# engine/loader.py
# ------------------------------------------------------------
# Responsabilidade: baixar preços de fechamento ajustados via
# yfinance (principal) com fallback para brapi.dev (BDRs sem
# dados no Yahoo). Devolve DataFrames limpos com cache Streamlit.
# ------------------------------------------------------------

import requests
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


# ── Constantes ───────────────────────────────────────────────
LOOKBACK_DAYS   = 400   # dias corridos para cobrir ~252 pregões + folga
MAX_RETRIES     = 2     # tentativas em caso de falha de rede
BRAPI_BASE_URL  = "https://brapi.dev/api/quote"

# Ticker virtual para IBOV dolarizado (calculado internamente)
IBOV_USD_TICKER = "__IBOV_USD__"


# ── Funções públicas ──────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(
    tickers: list[str],
    index_ticker: str,
    lookback_days: int = LOOKBACK_DAYS,
) -> tuple[pd.DataFrame, pd.Series, float, pd.Series]:
    """
    Baixa preços de fechamento ajustados para os ativos e para o índice.
    Tenta Yahoo Finance primeiro; para ativos sem dados usa brapi como fallback.

    Parâmetros
    ----------
    tickers       : lista de tickers dos ativos (ex: ['WEGE3.SA', 'VALE3.SA'])
    index_ticker  : ticker do índice de referência (ex: '^BVSP')
    lookback_days : quantos dias corridos retroativos baixar

    Retorna
    -------
    prices            : DataFrame shape=(dias, n_ativos)
    index_series      : Series shape=(dias,)
    index_volume_last : float — volume do último dia do índice
    index_series_full : Series — série completa do índice (para YTD)
    """
    end   = datetime.today()
    start = end - timedelta(days=lookback_days)

    # IBOV dolarizado: baixa ^BVSP e BRL=X separadamente
    if index_ticker == IBOV_USD_TICKER:
        raw      = _download(list(set(tickers)), start, end)
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
        raw       = _download(list(set(tickers)), start, end)
        raw_index = _download([index_ticker], start, end)

    # Extrai coluna "Close" independente de versão do yfinance
    tickers_set = list(set(tickers))
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers_set[0]})

    close = _clean(close)

    # Fallback brapi para ativos sem dados no Yahoo
    tickers_sem_dados = [t for t in tickers_set if t not in close.columns or close[t].count() < 30]
    if tickers_sem_dados:
        brapi_close = _download_brapi_batch(tickers_sem_dados, start, end)
        if not brapi_close.empty:
            # Alinha índice de datas e mescla
            close = close.reindex(close.index.union(brapi_close.index)).ffill()
            for col in brapi_close.columns:
                close[col] = brapi_close[col]

    # Separa índice dos ativos
    if index_ticker == IBOV_USD_TICKER:
        index_series = ibov_usd
        prices       = close
    else:
        if isinstance(raw_index.columns, pd.MultiIndex):
            idx_close = raw_index["Close"]
        else:
            idx_close = raw_index[["Close"]].rename(columns={"Close": index_ticker})
        idx_close = _clean(idx_close)
        if index_ticker in idx_close.columns:
            index_series = idx_close[index_ticker].rename(index_ticker)
        elif len(idx_close.columns) > 0:
            index_series = idx_close.iloc[:, 0].rename(index_ticker)
        else:
            raise ValueError(
                f"Índice '{index_ticker}' não encontrado nos dados baixados. "
                "Verifique o ticker e sua conexão."
            )
        prices = close

    # Remove ativos sem dados suficientes (< 30 pregões)
    prices = prices.loc[:, prices.count() >= 30]

    # Garante datas em comum suficientes entre ativos e índice
    common = prices.index.intersection(index_series.dropna().index)
    if len(common) < 30:
        raise ValueError(
            f"Índice '{index_ticker}' tem apenas {len(common)} datas em comum "
            "com os ativos. Tente outro índice de referência."
        )
    index_series_full = index_series.copy()
    prices       = prices.reindex(common).ffill()
    index_series = index_series.reindex(common).ffill()

    # Volume do último dia do índice (para detectar fechamento)
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            if index_ticker in raw["Volume"].columns:
                index_volume_last = float(raw["Volume"][index_ticker].iloc[-1])
            else:
                index_volume_last = -1.0
        else:
            index_volume_last = -1.0
    except Exception:
        index_volume_last = -1.0

    return prices, index_series, index_volume_last, index_series_full


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


def index_performance(index_series: pd.Series, index_ticker: str = "") -> dict[str, float]:
    """
    Calcula a performance percentual do índice em janelas fixas.
    Retorna dict com chaves: '5d', '21d', '63d', 'ytd'
    """
    s = index_series.dropna()
    if len(s) < 5:
        return {"5d": 0.0, "21d": 0.0, "63d": 0.0, "ytd": 0.0}

    last = s.iloc[-1]
    perf = {}

    for label, n in [("5d", 5), ("21d", 21), ("63d", 63)]:
        if len(s) > n:
            perf[label] = round((last / s.iloc[-(n + 1)] - 1) * 100, 2)
        else:
            perf[label] = None

    # YTD: último pregão de dezembro do ano anterior
    ano_atual    = s.index[-1].year
    ano_anterior = s[s.index.year == ano_atual - 1]
    if len(ano_anterior) > 0:
        base_ytd    = float(ano_anterior.iloc[-1])
        perf["ytd"] = round((last / base_ytd - 1) * 100, 2)
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


def _get_brapi_token() -> str | None:
    """Lê o token da brapi do secrets.toml ou retorna None."""
    try:
        return st.secrets.get("BRAPI_TOKEN", None)
    except Exception:
        return None


def _download_brapi_single(ticker_sa: str, start: datetime, end: datetime) -> pd.Series:
    """
    Baixa série histórica de um ticker via brapi.dev.
    ticker_sa: formato 'BDVE39.SA' — remove o .SA para a chamada.
    Retorna Series com índice DatetimeIndex ou Series vazia.
    """
    token = _get_brapi_token()
    if not token:
        return pd.Series(dtype=float)

    ticker = ticker_sa.replace(".SA", "")
    url    = f"{BRAPI_BASE_URL}/{ticker}"
    params = {
        "range":    "1y",
        "interval": "1d",
        "token":    token,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        hist = data.get("results", [{}])[0].get("historicalDataPrice", [])
        if not hist:
            return pd.Series(dtype=float)

        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"], unit="s", utc=True).dt.tz_convert("America/Sao_Paulo").dt.normalize()
        df = df.set_index("date")[["close"]].rename(columns={"close": ticker_sa})
        df = df[df.index >= pd.Timestamp(start).tz_localize("America/Sao_Paulo")]
        df = df.sort_index()
        return df[ticker_sa]

    except Exception:
        return pd.Series(dtype=float)


def _download_brapi_batch(tickers_sa: list[str], start: datetime, end: datetime) -> pd.DataFrame:
    """Baixa múltiplos tickers via brapi e retorna DataFrame consolidado."""
    frames = {}
    for ticker in tickers_sa:
        s = _download_brapi_single(ticker, start, end)
        if not s.empty and s.count() >= 30:
            frames[ticker] = s

    if not frames:
        return pd.DataFrame()

    return pd.DataFrame(frames)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Remove colunas totalmente vazias e preenche gaps internos."""
    df = df.dropna(axis=1, how="all")
    df = df.ffill().dropna(how="all")
    return df


def _clean_series(s: pd.Series) -> pd.Series:
    return s.ffill().dropna()
