# data/tickers.py
# ------------------------------------------------------------
# Edite estas listas para adicionar ou remover ativos.
# Os tickers devem ser exatamente como aparecem no Yahoo Finance.
# Ações BR: sufixo .SA  (ex: WEGE3.SA)
# Ações US: sem sufixo  (ex: AAPL)
# ------------------------------------------------------------

# --- Índices de referência disponíveis no seletor ---
# Índices de referência — tickers válidos no Yahoo Finance
# Índices BR não têm histórico diário no YF; usamos ETFs equivalentes:
#   BOVA11 = ETF Ibovespa | SMAL11 = ETF Small Cap | BRAX11 = ETF IBrX-100
#   DIVO11 = ETF Dividendos | XFIX11 = ETF FIIs
INDICES = {
    "IBOV — Ibovespa (^BVSP)":          "^BVSP",
    "IBrX-100 — ETF BRAX11":            "BRAX11.SA",
    "SMLL — ETF Small Cap (SMAL11)":    "SMAL11.SA",
    "IDIV — ETF Dividendos (DIVO11)":   "DIVO11.SA",
    "IFIX — ETF FIIs (XFIX11)":         "XFIX11.SA",
    "S&P 500":                           "^GSPC",
    "Nasdaq 100":                        "^NDX",
    "Russell 2000":                      "^RUT",
}

# --- Universos de ativos ---
# Cada entrada é um dicionário: { "TICKER.SA": "Nome da empresa" }
# Você pode ter quantos universos quiser — basta adicionar uma nova chave.

UNIVERSOS: dict[str, dict[str, str]] = {

    # Carteira Ibovespa Jan–Abr 2026 — 85 papéis de 79 empresas
    # Fonte: B3 (05/01/2026). Próxima revisão: maio/2026.
    "Ibovespa — carteira Jan-Abr 2026": {
        # Financeiro
        "ITUB4.SA":  "Itaú Unibanco PN",
        "ITUB3.SA":  "Itaú Unibanco ON",
        "BBDC4.SA":  "Bradesco PN",
        "BBDC3.SA":  "Bradesco ON",
        "BBAS3.SA":  "Banco do Brasil",
        "SANB11.SA": "Santander BR",
        "BPAC11.SA": "BTG Pactual",
        "ITSA4.SA":  "Itaúsa",
        "BBSE3.SA":  "BB Seguridade",
        "B3SA3.SA":  "B3",
        # Petróleo e Gás
        "PETR4.SA":  "Petrobras PN",
        "PETR3.SA":  "Petrobras ON",
        "PRIO3.SA":  "PetroRio",
        "VBBR3.SA":  "Vibra Energia",
        "UGPA3.SA":  "Ultrapar",
        # Energia Elétrica
        "AXIA3.SA":  "Axia Energia ON",
        "AXIA7.SA":  "Axia Energia",
        "ENEV3.SA":  "Eneva",
        "EGIE3.SA":  "Engie Brasil",
        "CPFE3.SA":  "CPFL Energia",
        "CPLE6.SA":  "Copel",
        "ENGI11.SA": "Energisa",
        "EQTL3.SA":  "Equatorial",
        "CMIG4.SA":  "Cemig PN",
        "TAEE11.SA": "Taesa",
        "AURE3.SA":  "Auren Energia",
        # Saneamento
        "SBSP3.SA":  "Sabesp",
        "CSMG3.SA":  "Copasa",
        # Mineração e Siderurgia
        "VALE3.SA":  "Vale",
        "CSNA3.SA":  "CSN",
        "GGBR4.SA":  "Gerdau PN",
        "GOAU4.SA":  "Gerdau Metalúrgica",
        "USIM5.SA":  "Usiminas",
        "BRAP4.SA":  "Bradespar",
        # Papel e Celulose
        "SUZB3.SA":  "Suzano",
        "KLBN11.SA": "Klabin",
        # Construção Civil
        "CYRE3.SA":  "Cyrela",
        "CYRE4.SA":  "Cyrela PN",
        "MRVE3.SA":  "MRV",
        "DIRR3.SA":  "Direcional",
        "CURY3.SA":  "Cury",
        # Consumo Cíclico
        "LREN3.SA":  "Lojas Renner",
        "MGLU3.SA":  "Magazine Luiza",
        "COGN3.SA":  "Cogna",
        "NATU3.SA":  "Natura",
        "POMO4.SA":  "Marcopolo PN",
        "POMO3.SA":  "Marcopolo ON",
        "CEAB3.SA":  "C&A Modas",
        "SMFT3.SA":  "Smart Fit",
        "MULT3.SA":  "Multiplan",
        "RENT3.SA":  "Localiza",
        "RENT4.SA":  "Localiza PN",
        # Consumo não Cíclico / Alimentos
        "ABEV3.SA":  "Ambev",
                "MBRF3.SA":  "MBRF (Marfrig+BRF)",
                "BEEF3.SA":  "Minerva",
        "ASAI3.SA":  "Assaí",
        # Saúde
        "RDOR3.SA":  "Rede D'Or",
        "HAPV3.SA":  "Hapvida",
        "HYPE3.SA":  "Hypera",
        "QUAL3.SA":  "Qualicorp",
        # Telecomunicações
        "VIVT3.SA":  "Telefônica",
        "TIMS3.SA":  "TIM",
        # Logística e Transporte
        "RAIL3.SA":  "Rumo",
                        # Agronegócio
        "SLCE3.SA":  "SLC Agrícola",
        # Tecnologia
        "TOTS3.SA":  "Totvs",
        # Indústria
        "WEGE3.SA":  "WEG",
        "EMBJ3.SA":  "Embraer",
        # Educação
        "YDUQ3.SA":  "Yduqs",
        # Químico
        "BRKM5.SA":  "Braskem",
    },

    # SMLL — Small Caps B3 (Jan 2026, ~115 ativos)
    # Fonte: statusinvest + B3. Ordenado por peso no índice.
    "Small Caps B3 — SMLL 2026": {
        "LREN3.SA":  "Lojas Renner",
        "ALOS3.SA":  "Allos",
        "CSMG3.SA":  "Copasa",
        "MULT3.SA":  "Multiplan",
        "CSAN3.SA":  "Cosan",
        "TAEE11.SA": "Taesa",
        "SMFT3.SA":  "Smart Fit",
        "SAPR11.SA": "Sanepar",
        "BRAV3.SA":  "Brava Energia",
        "NATU3.SA":  "Natura",
        "HYPE3.SA":  "Hypera",
        "CXSE3.SA":  "Caixa Seguridade",
        "FLRY3.SA":  "Fleury",
        "EZTC3.SA":  "EzTec",
        "DXCO3.SA":  "Dexco",
        "CMIN3.SA":  "CSN Mineração",
        "IGTI11.SA": "Iguatemi",
        "IRBR3.SA":  "IRB Brasil",
        "ENBR3.SA":  "EDP Brasil",
        "CPLE3.SA":  "Copel ON",
        "CMIG3.SA":  "Cemig ON",
        "CMIG4.SA":  "Cemig PN",
        "BRSR6.SA":  "Banrisul",
        "JHSF3.SA":  "JHSF",
        "GRND3.SA":  "Grendene",
        "MDIA3.SA":  "M. Dias Branco",
        "KEPL3.SA":  "Kepler Weber",
        "POMO4.SA":  "Marcopolo PN",
        "POMO3.SA":  "Marcopolo ON",
        "LOGG3.SA":  "Log Commercial",
        "HAPV3.SA":  "Hapvida",
        "CURY3.SA":  "Cury",
        "DIRR3.SA":  "Direcional",
        "CEAB3.SA":  "C&A Modas",
        "GMAT3.SA":  "Grupo Mateus",
        "VTRU3.SA":  "Vitru",
        "ONCO3.SA":  "Oncoclínicas",
        "MYPK3.SA":  "Iochpe-Maxion",
        "TUPY3.SA":  "Tupy",
        "VIVA3.SA":  "Vivara",
        "TASA4.SA":  "Taurus Armas",
        "VULC3.SA":  "Vulcabras",
        "LJQQ3.SA":  "Quero-Quero",
        "COGN3.SA":  "Cogna",
        "DASA3.SA":  "Dasa",
        "ECOR3.SA":  "Ecorodovias",
        "EVEN3.SA":  "Even",
        "FESA4.SA":  "Ferbasa",
        "GGPS3.SA":  "GPS",
                "GUAR3.SA":  "Guararapes",
        "HBOR3.SA":  "Helbor",
        "INTB3.SA":  "Intelbras",
        "JALL3.SA":  "Jalles Machado",
        "KLBN11.SA": "Klabin",
        "LAVV3.SA":  "Lavvi",
        "LEVE3.SA":  "Metal Leve",
        "LOGN3.SA":  "Log-In",
        "MATD3.SA":  "Mater Dei",
        "MBRF3.SA":  "Marfrig",
        "MDNE3.SA":  "Moura Dubeux",
        "MEAL3.SA":  "International Meal",
        "MGLU3.SA":  "Magazine Luiza",
        "MRVE3.SA":  "MRV",
        "MTRE3.SA":  "Mitre",
        "PCAR3.SA":  "GPA",
        "PLPL3.SA":  "Plano&Plano",
        "PTBL3.SA":  "PetroTal",
        "QUAL3.SA":  "Qualicorp",
        "RADL3.SA":  "Raia Drogasil",
        "RDOR3.SA":  "Rede D'Or",
        "ROMI3.SA":  "Romi",
        "SBFG3.SA":  "SBF Group",
        "SLCE3.SA":  "SLC Agrícola",
        "SYNE3.SA":  "Syn Prop",
        "TEND3.SA":  "Tenda",
        "TRAD3.SA":  "Tradersclub",
        "TRIS3.SA":  "Trisul",
        "TRPL4.SA":  "CTEEP",
        "TTEN3.SA":  "3Tentos",
        "USIM5.SA":  "Usiminas",
        "WEST3.SA":  "Westwing",
        "YDUQ3.SA":  "Yduqs",
        "ZAMP3.SA":  "Zamp",
        "CBAV3.SA":  "CBA",
        "CAML3.SA":  "Camil",
        "CASH3.SA":  "Méliuz",
        "ENJU3.SA":  "Enjoei",
        "ESPA3.SA":  "Espaçolaser",
        "IFCM3.SA":  "Infracommerce",
        "LWSA3.SA":  "Locaweb",
        "EMBJ3.SA":  "Embraer (units)",
        "IRBR3.SA":  "IRB Brasil",
        "ISAE4.SA":  "Isa Cteep PN",
        "DXCO3.SA":  "Dexco",
    },

    "FIIs — Fundos Imobiliários": {
        "BCFF11.SA": "BTG Fundo de Fundos",
        "BTLG11.SA": "BTG Logística",
        "CPTS11.SA": "Capitânia Securities",
        "HGLG11.SA": "CSHG Logística",
        "HGRU11.SA": "CSHG Renda Urbana",
        "HSML11.SA": "HSI Mall",
        "IRDM11.SA": "Iridium Recebíveis",
        "KNRI11.SA": "Kinea Renda Imobiliária",
        "MXRF11.SA": "Maxi Renda",
        "RBRD11.SA": "RBR Desenvolvimento",
        "RBRR11.SA": "RBR Recebíveis",
        "RECT11.SA": "REC Renda Imobiliária",
        "VILG11.SA": "Vinci Logística",
        "VISC11.SA": "Vinci Shopping Centers",
        "XPML11.SA": "XP Malls",
    },

    "Big Techs EUA": {
        "AAPL":  "Apple",
        "AMZN":  "Amazon",
        "GOOGL": "Alphabet",
        "META":  "Meta",
        "MSFT":  "Microsoft",
        "NFLX":  "Netflix",
        "NVDA":  "Nvidia",
        "TSLA":  "Tesla",
    },
}


def get_tickers(universo: str) -> dict[str, str]:
    """Retorna dicionário {ticker: nome} do universo selecionado."""
    return UNIVERSOS.get(universo, {})


def get_ticker_list(universo: str) -> list[str]:
    """Retorna apenas a lista de tickers (sem nomes)."""
    return list(UNIVERSOS.get(universo, {}).keys())


def get_nome(universo: str, ticker: str) -> str:
    """Retorna o nome legível de um ticker."""
    return UNIVERSOS.get(universo, {}).get(ticker, ticker)
