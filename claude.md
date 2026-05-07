# RS Quadrants — Contexto do Projeto

App Streamlit de análise de Força Relativa (RS) de ativos da B3 e internacionais comparados a índices de referência.

---

## Caminhos

- **Local:** `C:\Users\rijof\OneDrive\Python\VS Code\Claude\RS_Quadrants\`
- **Repositório GitHub:** https://github.com/Rijofe/cobalt-grid (branch `main`)
- **App em produção:** https://cobalt-grid.streamlit.app
- **Ambiente Python:** `.venv` em `C:\Users\rijof\OneDrive\Python\VS Code\.venv`

---

## Estrutura de arquivos

```
RS_Quadrants/
├── app.py
├── requirements.txt
├── data/
│   ├── tickers.py       ← universos, índices, SETORES
│   ├── csv_loader.py
│   └── ativos.csv       ← ignorado pelo Git
├── engine/
│   ├── loader.py        ← load_prices retorna 4 valores
│   └── rs_calc.py
├── views/
│   ├── quadrant_view.py
│   ├── sector_view.py
│   ├── breadth_view.py
│   ├── leaders_view.py
│   ├── ticker_view.py
│   ├── history_view.py
│   ├── scanner_view.py
│   └── export_utils.py
└── docs/                ← ignorado pelo Git
```

---

## Slides de navegação

- 📊 Quadrantes
- 🏭 Setorial
- 🌡️ Market Breadth
- 🏆 Líderes & Laggards
- 🔍 Ativo Individual
- 📅 Histórico
- 🔄 Scanner de Ciclo

---

## Universos disponíveis

- Ibovespa — carteira Jan-Abr 2026
- Small Caps B3 — SMLL 2026
- FIIs — Fundos Imobiliários
- S&P 500 — Top 50
- Nasdaq 100
- S&P 500 — Dividend Aristocrats
- BDRs — Brasileiras no Exterior
- ETFs Global — Bolsas por País
- CSVs detectados automaticamente em `data/`

---

## Padrões de desenvolvimento

- Commits em português com prefixo: `feat:`, `fix:`, `chore:`, `revert:`
- Arquivos gerados devem substituir os locais antes do commit
- `threads=True` no yfinance (não usar `threads=False` — causa loop)
- `applymap` → usar `.map()` (pandas novo)
- `load_prices()` retorna: `prices, index_series, index_volume_last, index_series_full`

---

## Lógica de RS — parâmetros fixos vs sidebar

### Quadrantes (`quadrant_view.py` + `rs_calc.py`)

Os Quadrantes usam **janelas fixas hardcoded** em `rs_calc.py`, independente do slider da sidebar:

| Parâmetro | Valor | Função |
|---|---|---|
| `DEFAULT_RS_WINDOW` | 21 dias | Suavização EMA do ratio preço/índice |
| `DEFAULT_MOM_WINDOW` | 5 dias | ROC do RS suavizado (momentum) |
| `DEFAULT_ZSCORE_LOOKBACK` | **252 dias** | Normalização histórica — equivalente ao slider de pregões |

- O **zscore_lookback de 252 dias** é o equivalente ao slider de "número de pregões" que existe no Histórico
- O sparkline de detalhe dentro do Quadrante usa `iloc[-63:]` — últimos 63 pregões, também fixo
- Isso é intencional: janelas fixas garantem comparabilidade entre ativos

### Slides que respondem ao slider de pregões

- 📅 Histórico — profundidade da série plotada
- 🌡️ Market Breadth — janela da evolução temporal do breadth
- 🏆 Líderes & Laggards — período de retorno para ranking
- 🔍 Ativo Individual — profundidade da série exibida

---

## Grade de Quadrantes — estrutura HTML

A grade é montada em HTML puro dentro de `quadrant_view.py` com chips clicáveis via `query_params`.

### Labels de eixo (atual)

```python
ROW_LABELS = ["↑ Acima (> +0.5σ)", "→ Neutro (±0.5σ)", "↓ Abaixo (< -0.5σ)"]
COL_LABELS = ["← Perdendo força (< -0.5σ)", "Estável (±0.5σ)", "Acelerando ↗ (> +0.5σ)"]
```

- **"— Momentum —"** aparece centralizado acima da grade (eixo horizontal)
- **"— RS Ratio —"** aparece em `writing-mode: vertical-rl` à esquerda da grade (eixo vertical)
- O threshold `±0.5σ` vem de `DEFAULT_NEUTRAL_BAND = 0.5` em `rs_calc.py`

### Caption abaixo das métricas

```python
st.caption(
    "**Breadth Score** = (acima − abaixo) / total × 100  ·  "
    "**RS Ratio** = z-score do ratio preço/índice  ·  "
    "📅 Janela fixa: 252 pregões (~1 ano)  ·  "
    "Passe o mouse nos valores para mais detalhes."
)
```

---

## Upload de CSV — comportamento esperado

Quando o usuário seleciona "📂 Upload de CSV..." sem enviar arquivo:

- O app exibe mensagem orientativa e chama `st.stop()` — **não tenta carregar dados**
- Mensagem: *"⬅ Baixe o modelo do CSV à esquerda e faça upload do arquivo com seus ativos."*
- O erro `No objects to concatenate` do yfinance era causado por `tickers_list = []` sendo passado ao loader

Correção em `app.py`:
```python
if universo == OPCAO_UPLOAD and not tickers_list:
    st.markdown(...)
    st.stop()
```

---

## Histórico de commits relevantes

```
7f9f79a  feat: mensagem orientativa ao selecionar Upload CSV sem arquivo
12110a7  fix: evita erro ao selecionar Upload CSV sem arquivo enviado
65e259d  feat: adiciona janela fixa de 252 pregões no caption dos quadrantes
2667eb5  fix: writing-mode por span individual para exibir RS Ratio e label de linha na lateral
b761f04  fix: aumenta fonte e contraste dos labels de eixo RS Ratio e Momentum
b14245d  feat: labels de eixo RS e Momentum com ranges de sigma na grade de quadrantes
990bb42  feat: adiciona ranges de sigma e nome dos eixos nos labels da grade de quadrantes
```
