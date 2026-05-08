# data/csv_loader.py
# ------------------------------------------------------------
# Carrega uma lista personalizada de ativos a partir de um CSV.
#
# Formato aceito (uma coluna obrigatória, uma opcional):
#   ticker          → obrigatório (ex: WEGE3 ou WEGE3.SA ou AAPL)
#   nome            → opcional (se ausente, usa o próprio ticker)
#
# Regras de normalização:
#   - Tickers de 4-6 letras/dígitos sem ponto → assume BR, adiciona .SA
#   - Tickers com ponto ou > 6 chars → assume EUA, mantém como está
#   - Case insensitive: wege3 → WEGE3.SA
# ------------------------------------------------------------

import pandas as pd
import io
from pathlib import Path

DEFAULT_CSV = Path(__file__).parent / "ativos.csv"

EXEMPLO_CSV = """ticker,nome
WEGE3,WEG
VALE3,Vale
PETR4,Petrobras PN
AAPL,Apple
MSFT,Microsoft
"""


def _normaliza_ticker(t: str) -> str:
    """Adiciona .SA a tickers brasileiros sem sufixo."""
    t = t.strip().upper()
    if not t:
        return ""
    if "." in t:
        return t
    # Tickers BR: letras + dígito(s), até 7 chars (ex: BPAC11, TAEE11)
    if len(t) <= 7 and t[-1].isdigit():
        return t + ".SA"
    return t


def carrega_csv(source) -> dict[str, str]:
    """
    Carrega CSV de tickers e retorna dict {ticker_normalizado: nome}.

    source pode ser:
    - str ou Path: caminho do arquivo
    - bytes ou BytesIO: conteúdo do upload do Streamlit
    - None: tenta carregar o arquivo padrão
    """
    try:
        if source is None:
            if not DEFAULT_CSV.exists():
                return {}
            df = pd.read_csv(DEFAULT_CSV, dtype=str, encoding="utf-8-sig", sep=None, engine="python")
        elif isinstance(source, (str, Path)):
            df = pd.read_csv(source, dtype=str, encoding="utf-8-sig", sep=None, engine="python")
        else:
            # Upload do Streamlit (UploadedFile ou bytes)
            # seek(0) garante leitura do início mesmo após re-renders
            if hasattr(source, "seek"):
                source.seek(0)
            content = source.read() if hasattr(source, "read") else source
            if not content:
                raise ValueError("Arquivo vazio ou já consumido.")
            df = pd.read_csv(io.BytesIO(content), dtype=str, encoding="utf-8-sig", sep=None, engine="python")

        df.columns = [c.strip().lower() for c in df.columns]

        # Aceita variações de nome de coluna
        ticker_col = next(
            (c for c in df.columns if c in ["ticker", "tickers", "ativo", "codigo", "symbol"]),
            df.columns[0]  # fallback: primeira coluna
        )
        nome_col = next(
            (c for c in df.columns if c in ["nome", "name", "empresa", "company"]),
            None
        )

        resultado = {}
        for _, row in df.iterrows():
            t = _normaliza_ticker(str(row[ticker_col]))
            if not t:
                continue
            nome = str(row[nome_col]).strip() if nome_col and pd.notna(row[nome_col]) else t.replace(".SA", "")
            resultado[t] = nome

        return resultado

    except Exception as e:
        # Propaga o erro para que o app.py possa exibi-lo ao usuário
        raise RuntimeError(f"Erro ao ler CSV: {e}") from e


def gera_exemplo_csv() -> bytes:
    """Retorna o conteúdo do CSV de exemplo para download."""
    return EXEMPLO_CSV.encode("utf-8")


def salva_csv_padrao(tickers_dict: dict[str, str]):
    """Salva o dicionário atual como arquivo padrão."""
    rows = [{"ticker": k.replace(".SA", ""), "nome": v} for k, v in tickers_dict.items()]
    df = pd.DataFrame(rows)
    df.to_csv(DEFAULT_CSV, index=False)
