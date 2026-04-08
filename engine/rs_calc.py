# engine/rs_calc.py
# ------------------------------------------------------------
# Motor matemático: calcula RS Ratio, RS Momentum, z-score,
# classifica cada ativo em um dos 9 quadrantes e retorna um
# DataFrame consolidado pronto para as views do Streamlit.
# ------------------------------------------------------------

import numpy as np
import pandas as pd
from dataclasses import dataclass


# ── Parâmetros padrão (usados quando nenhum é passado) ───────
DEFAULT_RS_WINDOW      = 21   # dias — janela da média do RS Ratio
DEFAULT_MOM_WINDOW     = 5    # dias — janela do ROC do RS Ratio
DEFAULT_ZSCORE_LOOKBACK = 252 # dias — normalização histórica
DEFAULT_SMOOTHING      = "EMA"  # "EMA" ou "SMA"
DEFAULT_NEUTRAL_BAND   = 0.5  # z-score que separa UP / NEUTRO / DOWN


# ── Dataclass de resultado por ativo ─────────────────────────
@dataclass
class AssetResult:
    ticker:    str
    nome:      str
    quadrant:  int          # 1–9
    rs_ratio:  float        # z-score do RS Ratio
    rs_mom:    float        # z-score do RS Momentum
    perf_21d:  float        # retorno % absoluto do ativo em 21d
    perf_vs:   float        # retorno % do ativo menos o índice em 21d
    rs_series: pd.Series    # série histórica do RS Ratio (para gráficos)


# ── Função principal pública ──────────────────────────────────

def compute_quadrants(
    prices:          pd.DataFrame,
    index_series:    pd.Series,
    nomes:           dict[str, str],
    rs_window:       int   = DEFAULT_RS_WINDOW,
    mom_window:      int   = DEFAULT_MOM_WINDOW,
    zscore_lookback: int   = DEFAULT_ZSCORE_LOOKBACK,
    smoothing:       str   = DEFAULT_SMOOTHING,
    neutral_band:    float = DEFAULT_NEUTRAL_BAND,
) -> pd.DataFrame:
    """
    Calcula RS Ratio, RS Momentum, z-scores e quadrante para cada ativo.

    Parâmetros
    ----------
    prices          : DataFrame(dias × ativos) — fechamentos ajustados
    index_series    : Series(dias) — fechamento do índice de referência
    nomes           : dict {ticker: nome legível}
    rs_window       : janela (dias) para suavização do RS Ratio
    mom_window      : janela (dias) para o ROC do RS Ratio suavizado
    zscore_lookback : janela histórica para cálculo do z-score
    smoothing       : "EMA" ou "SMA"
    neutral_band    : threshold do z-score para zona neutra (default ±0.5)

    Retorna
    -------
    DataFrame com colunas:
        ticker, nome, quadrant, rs_ratio, rs_mom,
        perf_21d, perf_vs_index, rs_series (objeto Series em cada linha)
    """
    # Alinha índice e preços na mesma grade temporal
    idx = index_series.reindex(prices.index).ffill().dropna()
    prices = prices.reindex(idx.index).ffill()

    results = []
    for ticker in prices.columns:
        asset = prices[ticker].dropna()
        if len(asset) < max(rs_window, mom_window, 30):
            continue  # dados insuficientes

        # Alinha com o índice
        common = asset.index.intersection(idx.index)
        a = asset.loc[common]
        b = idx.loc[common]

        try:
            result = _calc_asset(
                ticker, nomes.get(ticker, ticker), a, b,
                rs_window, mom_window, zscore_lookback, smoothing, neutral_band,
            )
            results.append(result)
        except Exception:
            continue  # ignora ativos com erro pontual

    if not results:
        return pd.DataFrame()

    rows = []
    for r in results:
        rows.append({
            "ticker":         r.ticker,
            "nome":           r.nome,
            "quadrant":       r.quadrant,
            "rs_ratio":       r.rs_ratio,
            "rs_mom":         r.rs_mom,
            "perf_21d":       r.perf_21d,
            "perf_vs_index":  r.perf_vs,
            "rs_series":      r.rs_series,
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("rs_ratio", ascending=False).reset_index(drop=True)
    return df


# ── Cálculo por ativo ─────────────────────────────────────────

def _calc_asset(
    ticker: str,
    nome: str,
    asset: pd.Series,
    index: pd.Series,
    rs_window: int,
    mom_window: int,
    zscore_lookback: int,
    smoothing: str,
    neutral_band: float,
) -> AssetResult:

    # 1. RS bruto: ratio diário ativo / índice
    ratio = asset / index

    # 2. Suavização do ratio
    rs_smooth = _smooth(ratio, rs_window, smoothing)

    # 3. Z-score do RS Ratio (normalização histórica)
    rs_z = _zscore(rs_smooth, zscore_lookback)

    # 4. RS Momentum: ROC do RS suavizado
    mom_raw = rs_smooth.pct_change(mom_window)
    rs_mom_z = _zscore(mom_raw, zscore_lookback)

    # Valores mais recentes
    rs_ratio_val = float(rs_z.iloc[-1])
    rs_mom_val   = float(rs_mom_z.iloc[-1])

    # 5. Perfomance absoluta 21d
    perf_21d = _perf(asset, 21)
    perf_idx = _perf(index, 21)
    perf_vs  = round(perf_21d - perf_idx, 2)

    # 6. Classificação no quadrante
    quadrant = _classify(rs_ratio_val, rs_mom_val, neutral_band)

    # 7. Série histórica do RS z-score para o gráfico de detalhe
    rs_series = rs_z.iloc[-63:].round(3)  # últimos 63 pregões

    return AssetResult(
        ticker=ticker,
        nome=nome,
        quadrant=quadrant,
        rs_ratio=round(rs_ratio_val, 2),
        rs_mom=round(rs_mom_val, 2),
        perf_21d=round(perf_21d, 2),
        perf_vs=perf_vs,
        rs_series=rs_series,
    )


# ── Classificação Q1–Q9 ───────────────────────────────────────

def _classify(rs_z: float, mom_z: float, band: float) -> int:
    """
    Grade 3×3:
        Eixo Y (RS Ratio z-score):  UP(>+band) | NEUTRO | DOWN(<-band)
        Eixo X (RS Momentum z-score): PERDENDO(<-band) | ESTAVEL | ACELERANDO(>+band)

    Mapeamento:
        UP    + PERDENDO    → 7
        UP    + ESTAVEL     → 8
        UP    + ACELERANDO  → 9
        NEUTRO + PERDENDO   → 4
        NEUTRO + ESTAVEL    → 5
        NEUTRO + ACELERANDO → 6
        DOWN  + PERDENDO    → 1
        DOWN  + ESTAVEL     → 2
        DOWN  + ACELERANDO  → 3
    """
    # Zona do eixo Y
    if rs_z > band:
        row = "UP"
    elif rs_z < -band:
        row = "DOWN"
    else:
        row = "NEUTRO"

    # Zona do eixo X
    if mom_z > band:
        col = "ACEL"
    elif mom_z < -band:
        col = "PERD"
    else:
        col = "ESTAV"

    grid = {
        ("UP",    "PERD"):  7,
        ("UP",    "ESTAV"): 8,
        ("UP",    "ACEL"):  9,
        ("NEUTRO","PERD"):  4,
        ("NEUTRO","ESTAV"): 5,
        ("NEUTRO","ACEL"):  6,
        ("DOWN",  "PERD"):  1,
        ("DOWN",  "ESTAV"): 2,
        ("DOWN",  "ACEL"):  3,
    }
    return grid[(row, col)]


# ── Métricas de Market Breadth ────────────────────────────────

def compute_breadth(df: pd.DataFrame) -> dict:
    """
    Recebe o DataFrame de resultado de compute_quadrants e retorna
    um dicionário com todos os indicadores de Market Breadth.
    """
    if df.empty:
        return {}

    total = len(df)
    up    = len(df[df["quadrant"] >= 7])
    neut  = len(df[df["quadrant"].between(4, 6)])
    down  = len(df[df["quadrant"] <= 3])
    q9    = len(df[df["quadrant"] == 9])
    q1    = len(df[df["quadrant"] == 1])
    q3    = len(df[df["quadrant"] == 3])   # turnarounds
    q6    = len(df[df["quadrant"] == 6])   # potenciais

    # Breadth Score: varia de -100 (todos em Q1-Q3) a +100 (todos em Q7-Q9)
    breadth_score = round((up - down) / total * 100)

    # Momentum Score: % de ativos em fase de aceleração (Q3, Q6, Q9)
    acel = len(df[df["quadrant"].isin([3, 6, 9])])
    momentum_score = round(acel / total * 100)

    return {
        "total":           total,
        "up":              up,
        "neut":            neut,
        "down":            down,
        "pct_up":          round(up   / total * 100, 1),
        "pct_neut":        round(neut / total * 100, 1),
        "pct_down":        round(down / total * 100, 1),
        "breadth_score":   breadth_score,
        "momentum_score":  momentum_score,
        "leaders_q9":      q9,
        "laggards_q1":     q1,
        "turnarounds_q3":  q3,
        "potential_q6":    q6,
    }


# ── Histórico de quadrantes (para history_view) ───────────────

def compute_quadrant_history(
    prices:          pd.DataFrame,
    index_series:    pd.Series,
    ticker:          str,
    rs_window:       int   = DEFAULT_RS_WINDOW,
    mom_window:      int   = DEFAULT_MOM_WINDOW,
    zscore_lookback: int   = DEFAULT_ZSCORE_LOOKBACK,
    smoothing:       str   = DEFAULT_SMOOTHING,
    neutral_band:    float = DEFAULT_NEUTRAL_BAND,
) -> pd.DataFrame:
    """
    Calcula quadrante dia a dia para um único ativo.
    Retorna DataFrame com colunas: date, quadrant, rs_ratio, rs_mom.
    """
    if ticker not in prices.columns:
        return pd.DataFrame()

    idx = index_series.reindex(prices.index).ffill().dropna()
    asset = prices[ticker].reindex(idx.index).ffill().dropna()
    common = asset.index.intersection(idx.index)
    a, b = asset.loc[common], idx.loc[common]

    ratio     = a / b
    rs_smooth = _smooth(ratio, rs_window, smoothing)
    rs_z      = _zscore(rs_smooth, zscore_lookback)
    mom_raw   = rs_smooth.pct_change(mom_window)
    rs_mom_z  = _zscore(mom_raw, zscore_lookback)

    hist = pd.DataFrame({
        "date":     rs_z.index,
        "rs_ratio": rs_z.values.round(2),
        "rs_mom":   rs_mom_z.values.round(2),
    }).dropna()

    hist["quadrant"] = hist.apply(
        lambda row: _classify(row["rs_ratio"], row["rs_mom"], neutral_band), axis=1
    )

    return hist.reset_index(drop=True)


# ── Helpers matemáticos ───────────────────────────────────────

def _smooth(series: pd.Series, window: int, method: str) -> pd.Series:
    if method == "EMA":
        return series.ewm(span=window, adjust=False).mean()
    return series.rolling(window).mean()


def _zscore(series: pd.Series, lookback: int) -> pd.Series:
    """Z-score rolling com janela de `lookback` períodos."""
    mu  = series.rolling(lookback, min_periods=30).mean()
    std = series.rolling(lookback, min_periods=30).std()
    return (series - mu) / std.replace(0, np.nan)


def _perf(series: pd.Series, n: int) -> float:
    """Retorno percentual simples em n períodos."""
    s = series.dropna()
    if len(s) <= n:
        return 0.0
    return round((s.iloc[-1] / s.iloc[-(n + 1)] - 1) * 100, 2)
