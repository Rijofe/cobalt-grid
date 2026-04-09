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
    "MSCI World (URTH)":               "URTH",
    "Total World — Vanguard (VT)":     "VT",
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

    "BDRs — Brasileiras no Exterior": {
        "INBR32.SA": "Inter&Co",
        "XPBR31.SA": "XP Inc.",
        "ROXO34.SA": "Nubank",
        "JBSS32.SA": "JBS",
        "PAGS34.SA": "PagSeguro",
        "STOC31.SA": "StoneCo",
        "MELI34.SA": "Mercado Libre",
        "A2FY34.SA": "Afya",
        "V2TX34.SA": "Vtex",
        "P2AX34.SA": "Patria Investimentos",
        "ARCE34.SA": "Arcos Dorados",
    },

    "ETFs Global — Bolsas por Pais": {
        "GREK":  "Greece 20 ETF",
        "GXG":   "Colombia 20 ETF",
        "EPU":   "Peru ETF",
        "EWO":   "Austria ETF",
        "EWK":   "Belgium ETF",
        "EWZ":   "Brazil ETF",
        "EWC":   "Canada ETF",
        "ECH":   "Chile ETF",
        "MCHI":  "China ETF",
        "EFNL":  "Finland ETF",
        "EWQ":   "France ETF",
        "EWH":   "Hong Kong ETF",
        "EIRL":  "Ireland ETF",
        "EIS":   "Israel ETF",
        "EWI":   "Italy ETF",
        "EWW":   "Mexico ETF",
        "EWN":   "Netherlands ETF",
        "EPOL":  "Poland ETF",
        "EZA":   "South Africa ETF",
        "EWY":   "South Korea ETF",
        "EWP":   "Spain ETF",
        "EWD":   "Sweden ETF",
        "EWL":   "Switzerland ETF",
        "UAE":   "UAE ETF",
        "EWU":   "United Kingdom ETF",
        "VNM":   "Vietnam ETF",
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

# ── Mapeamento de setores por ticker ─────────────────────────
# Usado pelo slide de Análise Setorial.
# Formato: { "TICKER.SA": "Setor" }

SETORES: dict[str, str] = {
    # Ibovespa
    "ITUB4.SA": "Financeiro", "ITUB3.SA": "Financeiro",
    "BBDC4.SA": "Financeiro", "BBDC3.SA": "Financeiro",
    "BBAS3.SA": "Financeiro", "SANB11.SA": "Financeiro",
    "BPAC11.SA": "Financeiro", "ITSA4.SA": "Financeiro",
    "BBSE3.SA": "Financeiro", "B3SA3.SA": "Financeiro",
    "PETR4.SA": "Petroleo e Gas", "PETR3.SA": "Petroleo e Gas",
    "PRIO3.SA": "Petroleo e Gas", "VBBR3.SA": "Petroleo e Gas",
    "UGPA3.SA": "Petroleo e Gas",
    "AXIA3.SA": "Energia Eletrica", "AXIA7.SA": "Energia Eletrica",
    "ENEV3.SA": "Energia Eletrica", "EGIE3.SA": "Energia Eletrica",
    "CPFE3.SA": "Energia Eletrica", "CPLE6.SA": "Energia Eletrica",
    "ENGI11.SA": "Energia Eletrica", "EQTL3.SA": "Energia Eletrica",
    "CMIG4.SA": "Energia Eletrica", "TAEE11.SA": "Energia Eletrica",
    "AURE3.SA": "Energia Eletrica",
    "SBSP3.SA": "Saneamento", "CSMG3.SA": "Saneamento",
    "VALE3.SA": "Mineracao e Siderurgia", "CSNA3.SA": "Mineracao e Siderurgia",
    "GGBR4.SA": "Mineracao e Siderurgia", "GOAU4.SA": "Mineracao e Siderurgia",
    "USIM5.SA": "Mineracao e Siderurgia", "BRAP4.SA": "Mineracao e Siderurgia",
    "SUZB3.SA": "Papel e Celulose", "KLBN11.SA": "Papel e Celulose",
    "CYRE3.SA": "Construcao Civil", "CYRE4.SA": "Construcao Civil",
    "MRVE3.SA": "Construcao Civil", "DIRR3.SA": "Construcao Civil",
    "CURY3.SA": "Construcao Civil",
    "LREN3.SA": "Consumo Ciclico", "MGLU3.SA": "Consumo Ciclico",
    "COGN3.SA": "Consumo Ciclico", "NATU3.SA": "Consumo Ciclico",
    "POMO4.SA": "Consumo Ciclico", "POMO3.SA": "Consumo Ciclico",
    "CEAB3.SA": "Consumo Ciclico", "SMFT3.SA": "Consumo Ciclico",
    "MULT3.SA": "Consumo Ciclico", "RENT3.SA": "Consumo Ciclico",
    "RENT4.SA": "Consumo Ciclico",
    "ABEV3.SA": "Alimentos e Bebidas", "MBRF3.SA": "Alimentos e Bebidas",
    "BEEF3.SA": "Alimentos e Bebidas", "ASAI3.SA": "Alimentos e Bebidas",
    "RDOR3.SA": "Saude", "HAPV3.SA": "Saude",
    "HYPE3.SA": "Saude", "QUAL3.SA": "Saude",
    "VIVT3.SA": "Telecomunicacoes", "TIMS3.SA": "Telecomunicacoes",
    "RAIL3.SA": "Logistica e Transporte",
    "SLCE3.SA": "Agronegocio",
    "TOTS3.SA": "Tecnologia",
    "WEGE3.SA": "Industria", "EMBJ3.SA": "Industria",
    "YDUQ3.SA": "Educacao",
    "BRKM5.SA": "Quimico",
    # SMLL adicionais
    "ALOS3.SA": "Consumo Ciclico", "CSAN3.SA": "Petroleo e Gas",
    "SAPR11.SA": "Saneamento", "BRAV3.SA": "Petroleo e Gas",
    "CXSE3.SA": "Financeiro", "FLRY3.SA": "Saude",
    "EZTC3.SA": "Construcao Civil", "DXCO3.SA": "Materiais Basicos",
    "CMIN3.SA": "Mineracao e Siderurgia", "IGTI11.SA": "Consumo Ciclico",
    "IRBR3.SA": "Financeiro", "ENBR3.SA": "Energia Eletrica",
    "CPLE3.SA": "Energia Eletrica", "CMIG3.SA": "Energia Eletrica",
    "BRSR6.SA": "Financeiro", "JHSF3.SA": "Consumo Ciclico",
    "GRND3.SA": "Consumo Ciclico", "MDIA3.SA": "Alimentos e Bebidas",
    "KEPL3.SA": "Industria", "LOGG3.SA": "Logistica e Transporte",
    "GMAT3.SA": "Alimentos e Bebidas", "VTRU3.SA": "Educacao",
    "ONCO3.SA": "Saude", "MYPK3.SA": "Industria",
    "TUPY3.SA": "Industria", "VIVA3.SA": "Consumo Ciclico",
    "TASA4.SA": "Industria", "VULC3.SA": "Consumo Ciclico",
    "LJQQ3.SA": "Consumo Ciclico", "DASA3.SA": "Saude",
    "ECOR3.SA": "Logistica e Transporte", "EVEN3.SA": "Construcao Civil",
    "FESA4.SA": "Mineracao e Siderurgia", "GGPS3.SA": "Servicos",
    "GUAR3.SA": "Consumo Ciclico", "HBOR3.SA": "Construcao Civil",
    "INTB3.SA": "Tecnologia", "JALL3.SA": "Agronegocio",
    "LAVV3.SA": "Construcao Civil", "LEVE3.SA": "Industria",
    "LOGN3.SA": "Logistica e Transporte", "MATD3.SA": "Saude",
    "MDNE3.SA": "Construcao Civil", "MEAL3.SA": "Consumo Ciclico",
    "MTRE3.SA": "Construcao Civil", "PCAR3.SA": "Alimentos e Bebidas",
    "PLPL3.SA": "Construcao Civil", "PTBL3.SA": "Petroleo e Gas",
    "RADL3.SA": "Saude", "ROMI3.SA": "Industria",
    "SBFG3.SA": "Consumo Ciclico", "SYNE3.SA": "Construcao Civil",
    "TEND3.SA": "Construcao Civil", "TRAD3.SA": "Tecnologia",
    "TRIS3.SA": "Construcao Civil", "TRPL4.SA": "Energia Eletrica",
    "TTEN3.SA": "Agronegocio", "WEST3.SA": "Consumo Ciclico",
    "ZAMP3.SA": "Alimentos e Bebidas", "CBAV3.SA": "Mineracao e Siderurgia",
    "CAML3.SA": "Alimentos e Bebidas", "CASH3.SA": "Tecnologia",
    "ENJU3.SA": "Tecnologia", "ESPA3.SA": "Saude",
    "IFCM3.SA": "Tecnologia", "LWSA3.SA": "Tecnologia",
    "ISAE4.SA": "Energia Eletrica",
    # BDRs Brasileiras no Exterior
    "INBR32.SA": "Financeiro",
    "XPBR31.SA": "Financeiro",
    "ROXO34.SA": "Financeiro",
    "JBSS32.SA": "Alimentos e Bebidas",
    "PAGS34.SA": "Financeiro",
    "STOC31.SA": "Financeiro",
    "MELI34.SA": "Tecnologia",
    "A2FY34.SA": "Educacao",
    "V2TX34.SA": "Tecnologia",
    "P2AX34.SA": "Financeiro",
    "ARCE34.SA": "Alimentos e Bebidas",
}
