# TODO — S&P 500 Completo

## Status
- [x] `Ações EUA — S&P 500 Top 100` — gerado e validado (mai/2026, fonte: stockanalysis.com)
- [ ] `Ações EUA — S&P 500 Completo` — pendente (~503 tickers)

## O que falta
Adicionar os ~400 tickers restantes (posições 101–503) ao universo
`"Ações EUA — S&P 500 Completo"` no `data/tickers.py`, com setores no `SETORES`.

## Como fazer
1. Baixar o CSV oficial: https://www.slickcharts.com/sp500 ou https://stockanalysis.com/list/sp-500-stocks/
2. Exportar para CSV com colunas: Symbol, Company Name, GICS Sector
3. Mapear setores GICS → nomenclatura do projeto:
   - Information Technology → Tecnologia
   - Financials → Financeiro
   - Health Care → Saude
   - Consumer Discretionary → Consumo Ciclico
   - Consumer Staples → Consumo nao Ciclico
   - Energy → Petroleo e Gas
   - Industrials → Industria
   - Materials → Materiais Basicos
   - Utilities → Energia Eletrica
   - Real Estate → Financeiro (ou criar Imobiliario)
   - Communication Services → Telecomunicacoes
4. Gerar bloco Python e adicionar ao tickers.py

## Referência
- Top 100 já gerado cobre ~80% do market cap do índice
- Posições 101-503 já disponíveis em stockanalysis.com/list/sp-500-stocks/
- Último rebalanceamento: Q1 2026 (Coinbase entrou, Intel saiu do top tier)
- Próximo rebalanceamento: junho 2026
