# views/export_utils.py
# ------------------------------------------------------------
# Exportação PNG (matplotlib) + PDF de dados estruturado (fpdf2)
# para todos os slides do app RS Quadrants.
# ------------------------------------------------------------

import io
import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from fpdf import FPDF

# ── Paleta matplotlib ─────────────────────────────────────────
QUAD_BG = {
    9: "#3B6D11", 8: "#97C459", 7: "#C0DD97",
    6: "#854F0B", 5: "#EF9F27", 4: "#FAC775",
    1: "#791F1F", 2: "#E24B4A", 3: "#F7C1C1",
}
QUAD_TX = {
    9: "#EAF3DE", 8: "#173404", 7: "#27500A",
    6: "#FAEEDA", 5: "#412402", 4: "#633806",
    1: "#FCEBEB", 2: "#FCEBEB", 3: "#791F1F",
}
QUAD_LABEL = {
    9: "Acima Acelerando",   8: "Acima Estavel",      7: "Acima Desacelerando",
    6: "Neutro Acelerando",  5: "Neutro Estavel",     4: "Neutro Perdendo",
    1: "Abaixo Piorando",    2: "Abaixo Estavel",     3: "Abaixo Recuperando",
}
GRID_LAYOUT = [[7, 8, 9], [4, 5, 6], [1, 2, 3]]
BG    = "#111111"
CARD  = "#1e1e1e"
TXT   = "#dddddd"
MUTED = "#888888"
GREEN = "#3B6D11"
RED   = "#791F1F"
AMBER = "#854F0B"


def _now():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M")


def _fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ── PDF estruturado base ──────────────────────────────────────

class RelatorioRS(FPDF):
    """PDF escuro com cabeçalho e rodapé padrão."""

    def __init__(self, titulo_slide, indice_nome):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.titulo_slide = titulo_slide.encode("latin-1", "replace").decode("latin-1")
        self.indice_nome  = indice_nome.encode("latin-1", "replace").decode("latin-1")
        self.set_auto_page_break(auto=True, margin=12)
        self.add_page()
        self._cabecalho()

    def _safe(self, s):
        """Converte string para latin-1 seguro."""
        return str(s).encode("latin-1", "replace").decode("latin-1")

    def _cabecalho(self):
        # Fundo do cabeçalho
        self.set_fill_color(20, 20, 20)
        self.rect(0, 0, 210, 22, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(220, 220, 220)
        self.set_xy(10, 5)
        self.cell(0, 7, self._safe(self.titulo_slide))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(140, 140, 140)
        self.set_xy(10, 13)
        self.cell(0, 5, f"vs {self._safe(self.indice_nome)}  |  {_now()}")
        self.set_y(26)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "", 6)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, f"RS Quadrants | cobalt-grid | Pagina {self.page_no()}", align="C")

    def secao(self, titulo, cor=(200, 200, 200)):
        """Título de seção."""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*cor)
        self.set_fill_color(30, 30, 30)
        self.cell(0, 7, self._safe(titulo), ln=True, fill=True)
        self.set_y(self.get_y() + 1)

    def linha_dados(self, cols, widths, negrito=False, cor_texto=(200, 200, 200)):
        """Linha de dados com colunas."""
        self.set_font("Helvetica", "B" if negrito else "", 8)
        self.set_text_color(*cor_texto)
        for txt, w in zip(cols, widths):
            self.cell(w, 5, self._safe(str(txt)), border=0)
        self.ln()

    def linha_cabecalho_tabela(self, cols, widths):
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(140, 140, 140)
        self.set_fill_color(25, 25, 25)
        for txt, w in zip(cols, widths):
            self.cell(w, 5, self._safe(str(txt)), fill=True)
        self.ln()
        self.set_draw_color(50, 50, 50)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_y(self.get_y() + 1)

    def linha_ativo(self, ticker, nome, q, rs, mom, perf21, vsidx):
        """Linha de ativo colorida por RS."""
        rs_v = float(rs) if rs not in (None, "") else 0
        if rs_v > 0.5:
            cor = (100, 180, 80)
        elif rs_v < -0.5:
            cor = (220, 80, 80)
        else:
            cor = (180, 180, 180)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*cor)

        def fmt(v, pct=False):
            try:
                f = float(v)
                return f"{f:+.2f}%" if pct else f"{f:+.2f}s"
            except Exception:
                return str(v)

        self.cell(18, 5, self._safe(str(ticker).replace(".SA","")))
        self.cell(42, 5, self._safe(str(nome)[:22]))
        self.cell(10, 5, self._safe(f"Q{int(q)}"))
        self.cell(18, 5, self._safe(fmt(rs)))
        self.cell(18, 5, self._safe(fmt(mom)))
        self.cell(18, 5, self._safe(fmt(perf21, pct=True)))
        self.cell(18, 5, self._safe(fmt(vsidx, pct=True)))
        self.ln()

    def metrica(self, label, valor, cor=(200, 200, 200)):
        """Par label: valor em linha."""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(140, 140, 140)
        self.cell(55, 6, self._safe(label + ":"))
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*cor)
        self.cell(0, 6, self._safe(str(valor)), ln=True)

    def espaco(self, h=3):
        self.set_y(self.get_y() + h)


# ── 1. QUADRANTES ─────────────────────────────────────────────

def _png_quadrantes(df, indice_nome, breadth, params, selected_ticker=None):
    """PNG simples da grade 3x3."""
    has_detail = (selected_ticker is not None and
                  not df[df["ticker"] == selected_ticker].empty)
    height = 10 if not has_detail else 14
    fig = plt.figure(figsize=(18, height))
    fig.patch.set_facecolor(BG)

    n_gs = 4 if not has_detail else 5
    hr   = [0.4, 0.8, 3, 3, 3] if not has_detail else [0.4, 0.8, 3, 3, 3, 2.2]
    gs   = gridspec.GridSpec(n_gs + 1, 1, figure=fig, height_ratios=hr,
                             hspace=0.07, top=0.98, bottom=0.02, left=0.04, right=0.98)

    # Título
    ax_t = fig.add_subplot(gs[0]); ax_t.set_facecolor(BG); ax_t.axis("off")
    ax_t.text(0.5, 0.5, f"Quadrantes - vs {indice_nome}  |  "
              f"RS {params.get('rs_window',21)}d  Mom {params.get('mom_window',5)}d  "
              f"{params.get('smoothing','EMA')}  |  {_now()}",
              transform=ax_t.transAxes, ha="center", va="center",
              color=TXT, fontsize=11, fontweight="bold")

    # Cards métricas
    score = breadth.get("breadth_score", 0)
    gs_c  = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=gs[1], wspace=0.05)
    cards = [
        ("Breadth Score",    f"{score:+d}",                            score),
        ("Acima do indice",  f"{breadth.get('pct_up',0):.1f}%",      breadth.get("pct_up",0)-50),
        ("Neutros",          f"{breadth.get('pct_neut',0):.1f}%",    0),
        ("Abaixo do indice", f"{breadth.get('pct_down',0):.1f}%",   -(breadth.get("pct_down",0)-50)),
        ("Perf. indice 21d", f"{breadth.get('idx_perf_21d') or '-'}", breadth.get("idx_perf_21d") or 0),
    ]
    for i, (lbl, val, v) in enumerate(cards):
        axc = fig.add_subplot(gs_c[0, i]); axc.set_facecolor(CARD)
        cor = GREEN if v > 0 else RED if v < 0 else MUTED
        axc.text(0.5, 0.62, val, transform=axc.transAxes,
                 ha="center", va="center", fontsize=15, fontweight="bold", color=cor)
        axc.text(0.5, 0.20, lbl, transform=axc.transAxes,
                 ha="center", va="center", fontsize=7.5, color=MUTED)
        axc.set_xticks([]); axc.set_yticks([])
        for sp in axc.spines.values(): sp.set_edgecolor("#2a2a2a"); sp.set_linewidth(0.5)

    # Grade 3x3
    gs_g = gridspec.GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[2:5], hspace=0.05, wspace=0.04)
    col_labels = ["<- Perdendo forca", "Estavel", "Acelerando ->"]
    row_labels  = ["^ Acima", "-> Neutro", "v Abaixo"]
    row_colors  = [GREEN, AMBER, RED]

    for ri, quad_row in enumerate(GRID_LAYOUT):
        for ci, q in enumerate(quad_row):
            ax = fig.add_subplot(gs_g[ri, ci]); ax.set_facecolor(QUAD_BG[q])
            items = df[df["quadrant"] == q].sort_values("rs_ratio", ascending=False)
            n = len(items)
            ax.text(0.97, 0.97, str(q), transform=ax.transAxes,
                    ha="right", va="top", fontsize=18, color=QUAD_TX[q], alpha=0.2, fontweight="bold")
            ax.text(0.03, 0.97, f"n={n}", transform=ax.transAxes,
                    ha="left", va="top", fontsize=7, color=QUAD_TX[q], alpha=0.8)
            ax.text(0.5, 0.88, QUAD_LABEL[q], transform=ax.transAxes,
                    ha="center", va="top", fontsize=6, color=QUAD_TX[q], alpha=0.6, style="italic")
            y_c, x_c = 0.72, 0.04
            for idx2, (_, r) in enumerate(items.head(12).iterrows()):
                sign = "+" if r["rs_ratio"] >= 0 else ""
                chip = f"{r['ticker'].replace('.SA','')} {sign}{r['rs_ratio']:.1f}s"
                if x_c + 0.48 > 0.96: x_c = 0.04; y_c -= 0.16
                if y_c < 0.04:
                    ax.text(0.96, 0.04, f"+{n-idx2}", transform=ax.transAxes,
                            ha="right", va="bottom", fontsize=6, color=QUAD_TX[q], alpha=0.6)
                    break
                ax.text(x_c, y_c, chip, transform=ax.transAxes,
                        ha="left", va="top", fontsize=6.5, color=QUAD_TX[q])
                x_c += 0.5
            if ri == 0: ax.set_title(col_labels[ci], color=MUTED, fontsize=7, pad=2)
            if ci == 0: ax.set_ylabel(row_labels[ri], color=row_colors[ri], fontsize=7, labelpad=2)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_visible(False)

    # Detalhe do ativo
    if has_detail:
        row_d = df[df["ticker"] == selected_ticker].iloc[0]
        q_d   = int(row_d["quadrant"])
        gs_det = gridspec.GridSpecFromSubplotSpec(1, 6, subplot_spec=gs[5], wspace=0.05)
        ax0 = fig.add_subplot(gs_det[0, 0]); ax0.set_facecolor(QUAD_BG[q_d])
        ax0.text(0.5, 0.70, selected_ticker.replace(".SA",""), transform=ax0.transAxes,
                 ha="center", va="center", fontsize=13, fontweight="bold", color=QUAD_TX[q_d])
        ax0.text(0.5, 0.45, row_d["nome"][:18], transform=ax0.transAxes,
                 ha="center", va="center", fontsize=8, color=QUAD_TX[q_d], alpha=0.85)
        ax0.text(0.5, 0.22, f"Q{q_d} - {QUAD_LABEL[q_d]}", transform=ax0.transAxes,
                 ha="center", va="center", fontsize=7, color=QUAD_TX[q_d], alpha=0.7)
        ax0.set_xticks([]); ax0.set_yticks([])
        for sp in ax0.spines.values(): sp.set_visible(False)
        for i, (lbl, val, v) in enumerate([
            ("RS Ratio (z-score)", f"{row_d['rs_ratio']:+.2f}s", row_d["rs_ratio"]),
            ("RS Momentum",        f"{row_d['rs_mom']:+.2f}s",   row_d["rs_mom"]),
            ("Perf. 21d",          f"{row_d['perf_21d']:+.1f}%", row_d["perf_21d"]),
            (f"vs indice 21d",     f"{row_d['perf_vs_index']:+.1f}%", row_d["perf_vs_index"]),
        ]):
            axm = fig.add_subplot(gs_det[0, i+1]); axm.set_facecolor(CARD)
            color = GREEN if v > 0 else RED if v < 0 else MUTED
            axm.text(0.5, 0.62, val, transform=axm.transAxes,
                     ha="center", va="center", fontsize=14, fontweight="bold", color=color)
            axm.text(0.5, 0.22, lbl, transform=axm.transAxes,
                     ha="center", va="center", fontsize=7.5, color=MUTED)
            axm.set_xticks([]); axm.set_yticks([])
            for sp in axm.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)
        ax_rs = fig.add_subplot(gs_det[0, 5]); ax_rs.set_facecolor(CARD)
        rs_series = row_d.get("rs_series")
        if rs_series is not None and len(rs_series) > 0:
            color_line = GREEN if row_d["rs_ratio"] >= 0 else RED
            ax_rs.plot(range(len(rs_series)), rs_series.values, color=color_line, linewidth=1.5)
            ax_rs.fill_between(range(len(rs_series)), rs_series.values, 0, alpha=0.15, color=color_line)
            ax_rs.axhline(0, color=MUTED, linewidth=0.7, linestyle="--")
        ax_rs.set_title("RS Ratio (z-score)", color=MUTED, fontsize=7, pad=2)
        ax_rs.tick_params(colors=MUTED, labelsize=6)
        for sp in ax_rs.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    return _fig_to_bytes(fig)


def _pdf_quadrantes(df, indice_nome, breadth, params, selected_ticker=None):
    """PDF de dados estruturado para slide Quadrantes."""
    pdf = RelatorioRS("Quadrantes", indice_nome)
    s = pdf._safe

    # Parâmetros
    pdf.secao("Parametros")
    pdf.linha_dados(
        [f"RS: {params.get('rs_window',21)}d",
         f"Momentum: {params.get('mom_window',5)}d",
         f"Tipo: {params.get('smoothing','EMA')}",
         f"Banda: +-{params.get('neutral_band',0.5)}s"],
        [45, 45, 45, 45]
    )
    pdf.espaco()

    # Breadth
    pdf.secao("Market Breadth")
    score = breadth.get("breadth_score", 0)
    cor_s = (100,180,80) if score>0 else (220,80,80) if score<0 else (180,180,180)
    pdf.metrica("Breadth Score", f"{score:+d}", cor_s)
    pdf.metrica("Acima do indice", f"{breadth.get('pct_up',0):.1f}%  ({breadth.get('up',0)} ativos)", (100,180,80))
    pdf.metrica("Neutros",        f"{breadth.get('pct_neut',0):.1f}%  ({breadth.get('neut',0)} ativos)")
    pdf.metrica("Abaixo do indice", f"{breadth.get('pct_down',0):.1f}%  ({breadth.get('down',0)} ativos)", (220,80,80))
    ip = breadth.get("idx_perf_21d")
    if ip is not None:
        pdf.metrica(f"Performance {indice_nome[:20]} 21d",
                    f"{ip:+.1f}%", (100,180,80) if ip>0 else (220,80,80))
    pdf.espaco()

    # Ativo selecionado
    if selected_ticker and not df[df["ticker"] == selected_ticker].empty:
        row_d = df[df["ticker"] == selected_ticker].iloc[0]
        q_d = int(row_d["quadrant"])
        pdf.secao(f"Ativo Selecionado: {selected_ticker.replace('.SA','')} — Q{q_d} {QUAD_LABEL[q_d]}", (180,180,80))
        pdf.metrica("RS Ratio (z-score)", f"{row_d['rs_ratio']:+.2f}s")
        pdf.metrica("RS Momentum",        f"{row_d['rs_mom']:+.2f}s")
        pdf.metrica("Performance 21d",    f"{row_d['perf_21d']:+.1f}%")
        pdf.metrica(f"vs {indice_nome[:15]} 21d", f"{row_d['perf_vs_index']:+.1f}%")
        pdf.espaco()

    # Ativos por quadrante
    pdf.secao("Ativos por quadrante")
    cabecalho = ["Ticker", "Nome", "Q", "RS (s)", "Mom (s)", "Perf 21d", "vs Idx"]
    widths    = [18, 42, 10, 18, 18, 18, 18]

    for q in [9, 8, 7, 6, 5, 4, 3, 2, 1]:
        subset = df[df["quadrant"] == q].sort_values("rs_ratio", ascending=False)
        if subset.empty:
            continue
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(0, 5, s(f"  Q{q} — {QUAD_LABEL[q]}  ({len(subset)} ativos)"), ln=True)
        pdf.linha_cabecalho_tabela(cabecalho, widths)
        for _, r in subset.iterrows():
            pdf.linha_ativo(r["ticker"], r["nome"], q,
                            r["rs_ratio"], r["rs_mom"],
                            r["perf_21d"], r["perf_vs_index"])
        pdf.espaco(2)

    return bytes(pdf.output())


def exporta_quadrantes(df, indice_nome, breadth, params,
                       selected_ticker=None, prices=None, index_series=None):
    png = _png_quadrantes(df, indice_nome, breadth, params, selected_ticker)
    pdf = _pdf_quadrantes(df, indice_nome, breadth, params, selected_ticker)
    return png, pdf


# ── 2. LÍDERES & LAGGARDS ─────────────────────────────────────

def _pdf_lideres(df, indice_nome):
    pdf = RelatorioRS("Lideres & Laggards", indice_nome)
    cabecalho = ["Ticker", "Nome", "Q", "RS (s)", "Mom (s)", "Perf 21d", "vs Idx"]
    widths    = [18, 42, 10, 18, 18, 18, 18]

    grupos = [
        ("Lideres — Q7, Q8, Q9",  df[df["quadrant"] >= 7].sort_values("rs_ratio", ascending=False), (100,180,80)),
        ("Laggards — Q1, Q2, Q3", df[df["quadrant"] <= 3].sort_values("rs_ratio"),                  (220,80,80)),
        ("Todos",                  df.sort_values("rs_ratio", ascending=False),                       (160,160,160)),
    ]
    for titulo, subset, cor in grupos:
        pdf.secao(f"{titulo}  ({len(subset)} ativos)", cor)
        pdf.linha_cabecalho_tabela(cabecalho, widths)
        for _, r in subset.iterrows():
            pdf.linha_ativo(r["ticker"], r["nome"], int(r["quadrant"]),
                            r["rs_ratio"], r["rs_mom"],
                            r["perf_21d"], r["perf_vs_index"])
        pdf.espaco(3)

    return bytes(pdf.output())


def _png_lideres(df, indice_nome):
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    ax.text(0.5, 0.95, f"Lideres & Laggards - vs {indice_nome}  |  {_now()}",
            transform=ax.transAxes, ha="center", va="top",
            color=TXT, fontsize=11, fontweight="bold")
    lids = df[df["quadrant"] >= 7].sort_values("rs_ratio", ascending=False).head(15)
    lags = df[df["quadrant"] <= 3].sort_values("rs_ratio").head(15)
    for xi, (subset, cor, tit) in enumerate([(lids, GREEN, "Lideres Q7-Q9"), (lags, RED, "Laggards Q1-Q3")]):
        x0 = 0.03 + xi * 0.5
        ax.text(x0, 0.85, f"{tit} ({len(subset)})", transform=ax.transAxes,
                ha="left", va="top", color=cor, fontsize=9, fontweight="bold")
        y = 0.78
        for _, r in subset.iterrows():
            sign = "+" if r["rs_ratio"] >= 0 else ""
            line = f"{r['ticker'].replace('.SA','')}  {sign}{r['rs_ratio']:.2f}s  {r['rs_mom']:+.2f}s  {r['perf_21d']:+.1f}%"
            ax.text(x0, y, line, transform=ax.transAxes,
                    ha="left", va="top", color=TXT, fontsize=7.5)
            y -= 0.055
    return _fig_to_bytes(fig)


def exporta_lideres(df, indice_nome):
    png = _png_lideres(df, indice_nome)
    pdf = _pdf_lideres(df, indice_nome)
    return png, pdf


# ── 3. SCANNER DE CICLO ───────────────────────────────────────

def _pdf_scanner(compras, vendas, indice_nome, janela):
    pdf = RelatorioRS("Scanner de Ciclo", indice_nome)
    pdf.metrica("Janela de busca", f"{janela} pregoes")
    pdf.metrica("Total de sinais", f"{len(compras)} compra  |  {len(vendas)} venda")
    pdf.espaco()

    cabecalho = ["Ticker", "Nome", "Transicao", "Dias atras", "RS (s)", "Mom (s)"]
    widths    = [18, 35, 60, 18, 18, 18]

    for titulo, subset, cor in [
        ("Sinais de Compra", compras, (100,180,80)),
        ("Sinais de Venda",  vendas,  (220,80,80)),
    ]:
        pdf.secao(f"{titulo}  ({len(subset)} sinais)", cor)
        if subset.empty:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(140, 140, 140)
            pdf.cell(0, 5, "Nenhum sinal encontrado.", ln=True)
            pdf.espaco(2)
            continue
        pdf.linha_cabecalho_tabela(cabecalho, widths)
        cor_linha = (100,180,80) if "Compra" in titulo else (220,80,80)
        for _, r in subset.sort_values("dias_atrás").iterrows():
            dias = int(r["dias_atrás"])
            trans = r.get("transição", r.get("transicao", ""))
            trans_safe = str(trans).replace("→","->").replace("★","*")
            dias_str = "Hoje" if dias == 0 else f"{dias}d atras"
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*cor_linha)
            pdf.cell(18, 5, pdf._safe(r["ticker"]))
            pdf.cell(35, 5, pdf._safe(str(r["nome"])[:20]))
            pdf.cell(60, 5, pdf._safe(trans_safe[:35]))
            pdf.set_text_color(100,200,100) if dias==0 else pdf.set_text_color(180,180,180)
            pdf.cell(18, 5, pdf._safe(dias_str))
            pdf.set_text_color(*cor_linha)
            pdf.cell(18, 5, pdf._safe(f"{float(r['rs_atual']):+.2f}"))
            pdf.cell(18, 5, pdf._safe(f"{float(r['mom_atual']):+.2f}"))
            pdf.ln()
        pdf.espaco(3)

    return bytes(pdf.output())


def _png_scanner(compras, vendas, indice_nome, janela):
    total = max(len(compras), len(vendas), 5)
    fig, axes = plt.subplots(1, 2, figsize=(16, max(5, total * 0.28 + 2)))
    fig.patch.set_facecolor(BG)
    fig.suptitle(f"Scanner de Ciclo - vs {indice_nome} - Janela {janela}d  |  {_now()}",
                 color=TXT, fontsize=10, fontweight="bold", y=0.99)
    for ax, subset, tit, cor in [
        (axes[0], compras, f"Compra ({len(compras)})", GREEN),
        (axes[1], vendas,  f"Venda ({len(vendas)})",  RED),
    ]:
        ax.set_facecolor(BG); ax.axis("off")
        ax.set_title(tit, color=cor, fontsize=9, fontweight="bold", pad=4)
        if subset.empty:
            ax.text(0.5, 0.5, "Nenhum sinal", transform=ax.transAxes,
                    ha="center", color=MUTED, fontsize=9)
            continue
        y = 0.93
        for _, r in subset.sort_values("dias_atrás").iterrows():
            dias = int(r["dias_atrás"])
            trans = str(r.get("transição", r.get("transicao",""))).replace("→","->").replace("★","*")
            dias_s = "Hoje" if dias == 0 else f"{dias}d"
            line = f"{r['ticker']}  {trans[:28]}  {dias_s}  RS {float(r['rs_atual']):+.2f}s"
            c = GREEN if dias == 0 else TXT if dias <= 2 else MUTED
            ax.text(0.03, y, line, transform=ax.transAxes,
                    ha="left", va="top", color=c, fontsize=7.5)
            y -= 0.055
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    return _fig_to_bytes(fig)


def exporta_scanner(compras, vendas, indice_nome, janela):
    png = _png_scanner(compras, vendas, indice_nome, janela)
    pdf = _pdf_scanner(compras, vendas, indice_nome, janela)
    return png, pdf


# ── 4. ATIVO INDIVIDUAL ───────────────────────────────────────

def _pdf_ativo(row, indice_nome, prices, index_series, janela):
    ticker = row["ticker"].replace(".SA","")
    q = int(row["quadrant"])
    pdf = RelatorioRS(f"Ativo Individual — {ticker}", indice_nome)

    pdf.secao(f"{ticker} — {row['nome']}  |  Q{q} — {QUAD_LABEL[q]}")
    pdf.metrica("RS Ratio (z-score)", f"{row['rs_ratio']:+.2f}s",
                (100,180,80) if row["rs_ratio"]>0 else (220,80,80))
    pdf.metrica("RS Momentum",        f"{row['rs_mom']:+.2f}s",
                (100,180,80) if row["rs_mom"]>0 else (220,80,80))
    pdf.metrica("Performance 21d",    f"{row['perf_21d']:+.1f}%",
                (100,180,80) if row["perf_21d"]>0 else (220,80,80))
    pdf.metrica(f"vs {indice_nome[:20]} 21d", f"{row['perf_vs_index']:+.1f}%",
                (100,180,80) if row["perf_vs_index"]>0 else (220,80,80))
    pdf.espaco()

    # RS histórico em tabela
    rs_series = row.get("rs_series")
    if rs_series is not None and len(rs_series) > 0:
        pdf.secao(f"RS Ratio historico — ultimos {len(rs_series)} pregoes")
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(140,140,140)
        pdf.cell(20,5,"Pregao"); pdf.cell(25,5,"RS Ratio (s)"); pdf.ln()
        pdf.set_font("Helvetica","",7.5)
        for i, v in enumerate(rs_series.values[-30:]):
            c = (100,180,80) if v > 0 else (220,80,80)
            pdf.set_text_color(*c)
            pdf.cell(20,4,str(len(rs_series)-30+i+1))
            pdf.cell(25,4,f"{v:+.3f}s")
            pdf.ln()

    return bytes(pdf.output())


def _png_ativo(row, indice_nome, prices, index_series, janela):
    ticker = row["ticker"].replace(".SA","")
    q = int(row["quadrant"])
    fig = plt.figure(figsize=(16, 8))
    fig.patch.set_facecolor(BG)
    gs = gridspec.GridSpec(2, 5, figure=fig, hspace=0.4, wspace=0.08,
                           top=0.90, bottom=0.06, left=0.04, right=0.98)
    fig.suptitle(f"{ticker} ({row['nome']}) - vs {indice_nome}  |  {_now()}",
                 color=TXT, fontsize=10, fontweight="bold")

    ax0 = fig.add_subplot(gs[0,0]); ax0.set_facecolor(QUAD_BG[q])
    ax0.text(0.5,0.65,ticker,transform=ax0.transAxes,ha="center",va="center",
             fontsize=16,fontweight="bold",color=QUAD_TX[q])
    ax0.text(0.5,0.40,row["nome"][:16],transform=ax0.transAxes,ha="center",va="center",
             fontsize=7.5,color=QUAD_TX[q],alpha=0.85)
    ax0.text(0.5,0.20,f"Q{q}",transform=ax0.transAxes,ha="center",va="center",
             fontsize=9,color=QUAD_TX[q],alpha=0.7)
    ax0.set_xticks([]); ax0.set_yticks([])
    for sp in ax0.spines.values(): sp.set_visible(False)

    for i,(lbl,val,v) in enumerate([
        ("RS Ratio",f"{row['rs_ratio']:+.2f}s",row["rs_ratio"]),
        ("RS Mom",  f"{row['rs_mom']:+.2f}s",  row["rs_mom"]),
        ("Perf 21d",f"{row['perf_21d']:+.1f}%",row["perf_21d"]),
        ("vs Idx",  f"{row['perf_vs_index']:+.1f}%",row["perf_vs_index"]),
    ]):
        axm = fig.add_subplot(gs[0,i+1]); axm.set_facecolor(CARD)
        c = GREEN if v>0 else RED if v<0 else MUTED
        axm.text(0.5,0.62,val,transform=axm.transAxes,ha="center",va="center",
                 fontsize=14,fontweight="bold",color=c)
        axm.text(0.5,0.22,lbl,transform=axm.transAxes,ha="center",va="center",
                 fontsize=7.5,color=MUTED)
        axm.set_xticks([]); axm.set_yticks([])
        for sp in axm.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    ax_p = fig.add_subplot(gs[1,:3]); ax_p.set_facecolor(CARD)
    try:
        t_full = row["ticker"]
        ap = prices[t_full].dropna().iloc[-janela:]
        ip = index_series.reindex(ap.index).ffill().dropna()
        cm = ap.index.intersection(ip.index)
        an = ap.loc[cm]/ap.loc[cm].iloc[0]*100
        inp= ip.loc[cm]/ip.loc[cm].iloc[0]*100
        ax_p.plot(range(len(an)),an.values,color="#378ADD",linewidth=1.5,label=ticker)
        ax_p.plot(range(len(inp)),inp.values,color=MUTED,linewidth=1.0,linestyle="--",label=indice_nome[:10])
        ax_p.legend(fontsize=7,facecolor=CARD,labelcolor=TXT,framealpha=0.5)
    except Exception: pass
    ax_p.set_title("Preco normalizado (base 100)",color=MUTED,fontsize=7.5,pad=2)
    ax_p.tick_params(colors=MUTED,labelsize=6)
    for sp in ax_p.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    ax_rs = fig.add_subplot(gs[1,3:]); ax_rs.set_facecolor(CARD)
    rs_s = row.get("rs_series")
    if rs_s is not None and len(rs_s)>0:
        cl = GREEN if row["rs_ratio"]>=0 else RED
        ax_rs.plot(range(len(rs_s)),rs_s.values,color=cl,linewidth=1.5)
        ax_rs.fill_between(range(len(rs_s)),rs_s.values,0,alpha=0.15,color=cl)
        ax_rs.axhline(0,color=MUTED,linewidth=0.7,linestyle="--")
    ax_rs.set_title("RS Ratio (z-score)",color=MUTED,fontsize=7.5,pad=2)
    ax_rs.tick_params(colors=MUTED,labelsize=6)
    for sp in ax_rs.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    return _fig_to_bytes(fig)


def exporta_ativo(row, indice_nome, prices, index_series, janela=63):
    png = _png_ativo(row, indice_nome, prices, index_series, janela)
    pdf = _pdf_ativo(row, indice_nome, prices, index_series, janela)
    return png, pdf


# ── 5. MARKET BREADTH ─────────────────────────────────────────

def _pdf_breadth(df, breadth, indice_nome, idx_perf):
    pdf = RelatorioRS("Market Breadth", indice_nome)
    score = breadth.get("breadth_score", 0)
    cor_s = (100,180,80) if score>0 else (220,80,80) if score<0 else (180,180,180)

    pdf.secao("Resumo")
    pdf.metrica("Breadth Score", f"{score:+d}", cor_s)
    pdf.metrica("Total de ativos", str(breadth.get("total",0)))
    pdf.metrica("Acima do indice", f"{breadth.get('pct_up',0):.1f}%  ({breadth.get('up',0)} ativos)", (100,180,80))
    pdf.metrica("Neutros",         f"{breadth.get('pct_neut',0):.1f}%  ({breadth.get('neut',0)} ativos)")
    pdf.metrica("Abaixo do indice",f"{breadth.get('pct_down',0):.1f}%  ({breadth.get('down',0)} ativos)", (220,80,80))
    pdf.metrica("Lideres Q9",      str(breadth.get("leaders_q9",0)))
    pdf.metrica("Turnarounds Q3",  str(breadth.get("turnarounds_q3",0)))
    pdf.metrica("Potenciais Q6",   str(breadth.get("potential_q6",0)))
    pdf.espaco()

    pdf.secao(f"Performance {indice_nome[:25]}")
    for lbl, k in [("5 dias","5d"),("21 dias","21d"),("63 dias","63d"),("YTD","ytd")]:
        v = idx_perf.get(k)
        if v is not None:
            c = (100,180,80) if v>0 else (220,80,80)
            pdf.metrica(lbl, f"{v:+.1f}%", c)
    pdf.espaco()

    cabecalho = ["Ticker","Nome","Q","RS (s)","Mom (s)","Perf 21d","vs Idx"]
    widths    = [18,42,10,18,18,18,18]

    for tit, subset, cor in [
        ("Acima do indice — Q7, Q8, Q9", df[df["quadrant"]>=7].sort_values("rs_ratio",ascending=False), (100,180,80)),
        ("Neutros — Q4, Q5, Q6",         df[df["quadrant"].between(4,6)].sort_values("rs_ratio",ascending=False), (200,140,40)),
        ("Abaixo do indice — Q1, Q2, Q3",df[df["quadrant"]<=3].sort_values("rs_ratio"),  (220,80,80)),
    ]:
        pdf.secao(f"{tit}  ({len(subset)} ativos)", cor)
        pdf.linha_cabecalho_tabela(cabecalho, widths)
        for _, r in subset.iterrows():
            pdf.linha_ativo(r["ticker"],r["nome"],int(r["quadrant"]),
                            r["rs_ratio"],r["rs_mom"],r["perf_21d"],r["perf_vs_index"])
        pdf.espaco(3)

    return bytes(pdf.output())


def _png_breadth(df, breadth, indice_nome, idx_perf):
    fig = plt.figure(figsize=(16,8))
    fig.patch.set_facecolor(BG)
    gs = gridspec.GridSpec(2,3,figure=fig,hspace=0.4,wspace=0.15,
                           top=0.92,bottom=0.05,left=0.05,right=0.97)
    fig.suptitle(f"Market Breadth - vs {indice_nome}  |  {_now()}",
                 color=TXT,fontsize=10,fontweight="bold")

    score = breadth.get("breadth_score",0)
    cor_s = GREEN if score>0 else RED if score<0 else AMBER
    ax_g = fig.add_subplot(gs[0,0]); ax_g.set_facecolor(CARD)
    ax_g.barh(0,score,color=cor_s,height=0.4)
    ax_g.barh(0,100,color="#2a2a2a",height=0.4)
    ax_g.barh(0,-100,color="#2a2a2a",height=0.4)
    ax_g.set_xlim(-105,105)
    ax_g.text(0,0,f"{score:+d}",ha="center",va="center",
              fontsize=16,fontweight="bold",color=cor_s)
    ax_g.set_title("Breadth Score",color=MUTED,fontsize=8,pad=3)
    ax_g.set_yticks([]); ax_g.set_xticks([-100,-50,0,50,100])
    ax_g.tick_params(colors=MUTED,labelsize=6)
    for sp in ax_g.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    ax_d = fig.add_subplot(gs[0,1]); ax_d.set_facecolor(BG)
    up=breadth.get("up",0); neut=breadth.get("neut",0); dn=breadth.get("down",0)
    if up+neut+dn>0:
        ax_d.pie([up,neut,dn],colors=[GREEN,AMBER,RED],wedgeprops=dict(width=0.5),
                 startangle=90,labels=[f"Acima\n{up}",f"Neutro\n{neut}",f"Abaixo\n{dn}"],
                 textprops={"color":TXT,"fontsize":7})
    ax_d.set_title("Distribuicao",color=MUTED,fontsize=8,pad=2)

    ax_b = fig.add_subplot(gs[0,2]); ax_b.set_facecolor(CARD)
    qs=list(range(1,10)); counts=[len(df[df["quadrant"]==q]) for q in qs]
    bars=ax_b.bar([f"Q{q}" for q in qs],counts,color=[QUAD_BG[q] for q in qs],
                  edgecolor="#333",linewidth=0.5)
    for bar,cnt in zip(bars,counts):
        if cnt>0: ax_b.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.2,
                            str(cnt),ha="center",va="bottom",fontsize=7,color=TXT)
    ax_b.set_facecolor(CARD); ax_b.set_title("Por quadrante",color=MUTED,fontsize=8,pad=3)
    ax_b.tick_params(colors=MUTED,labelsize=7)
    for sp in ax_b.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    for zi,(ztit,zsub,zcor) in enumerate([
        ("Acima (Q7-Q9)",  df[df["quadrant"]>=7],          GREEN),
        ("Neutros (Q4-Q6)",df[df["quadrant"].between(4,6)],AMBER),
        ("Abaixo (Q1-Q3)", df[df["quadrant"]<=3],          RED),
    ]):
        ax_z=fig.add_subplot(gs[1,zi]); ax_z.set_facecolor(CARD); ax_z.axis("off")
        ax_z.set_title(f"{ztit} ({len(zsub)})",color=zcor,fontsize=8,pad=3)
        y_t=0.93
        for _,r in zsub.sort_values("rs_ratio",ascending=False).head(10).iterrows():
            s="+" if r["rs_ratio"]>=0 else ""
            line=f"{r['ticker'].replace('.SA','')}  {s}{r['rs_ratio']:.2f}s  {r['rs_mom']:+.2f}s  {r['perf_21d']:+.1f}%"
            ax_z.text(0.04,y_t,line,transform=ax_z.transAxes,ha="left",va="top",color=TXT,fontsize=6.5)
            y_t-=0.09
        for sp in ax_z.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    return _fig_to_bytes(fig)


def exporta_breadth(df, breadth, indice_nome, idx_perf):
    png = _png_breadth(df, breadth, indice_nome, idx_perf)
    pdf = _pdf_breadth(df, breadth, indice_nome, idx_perf)
    return png, pdf


# ── 6. HISTÓRICO ─────────────────────────────────────────────

def _pdf_historico(hist, ticker, indice_nome, janela):
    pdf = RelatorioRS(f"Historico — {ticker}", indice_nome)
    q_atual = int(hist["quadrant"].iloc[-1])

    pdf.secao(f"Quadrante atual: Q{q_atual} — {QUAD_LABEL[q_atual]}  |  Periodo: {janela} pregoes")
    pdf.espaco()

    pdf.secao("Tempo em cada quadrante")
    freq = hist.groupby("quadrant").size().reset_index(name="n")
    freq["pct"] = (freq["n"]/janela*100).round(1)
    freq = freq.sort_values("n", ascending=False)
    pdf.set_font("Helvetica","B",7.5); pdf.set_text_color(140,140,140)
    pdf.cell(30,5,"Quadrante"); pdf.cell(35,5,"Descricao"); pdf.cell(25,5,"Pregoes"); pdf.cell(25,5,"% periodo"); pdf.ln()
    pdf.set_draw_color(50,50,50); pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.set_y(pdf.get_y()+1)
    for _,r in freq.iterrows():
        q_f=int(r["quadrant"])
        pdf.set_font("Helvetica","",8); pdf.set_text_color(180,180,180)
        pdf.cell(30,5,pdf._safe(f"Q{q_f}"))
        pdf.cell(35,5,pdf._safe(QUAD_LABEL[q_f]))
        pdf.cell(25,5,str(int(r["n"])))
        pdf.cell(25,5,f"{r['pct']:.1f}%"); pdf.ln()
    pdf.espaco()

    pdf.secao("RS Ratio e Momentum — ultimos 30 pregoes")
    pdf.set_font("Helvetica","B",7.5); pdf.set_text_color(140,140,140)
    pdf.cell(20,5,"Pregao"); pdf.cell(15,5,"Q"); pdf.cell(25,5,"RS Ratio (s)"); pdf.cell(25,5,"RS Mom (s)"); pdf.ln()
    pdf.set_draw_color(50,50,50); pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.set_y(pdf.get_y()+1)
    for i,(_,r) in enumerate(hist.iloc[-30:].iterrows()):
        q_r = int(r["quadrant"])
        c = (100,180,80) if r["rs_ratio"]>0 else (220,80,80)
        pdf.set_font("Helvetica","",8); pdf.set_text_color(*c)
        pdf.cell(20,4,str(len(hist)-30+i+1))
        pdf.cell(15,4,f"Q{q_r}")
        pdf.cell(25,4,f"{r['rs_ratio']:+.3f}s")
        pdf.cell(25,4,f"{r['rs_mom']:+.3f}s"); pdf.ln()

    return bytes(pdf.output())


def _png_historico(hist, ticker, indice_nome, janela):
    q_atual = int(hist["quadrant"].iloc[-1])
    fig = plt.figure(figsize=(16,8))
    fig.patch.set_facecolor(BG)
    gs = gridspec.GridSpec(2,3,figure=fig,hspace=0.38,wspace=0.12,
                           top=0.91,bottom=0.07,left=0.06,right=0.97)
    fig.suptitle(f"Historico — {ticker} — Q{q_atual} {QUAD_LABEL[q_atual]} — vs {indice_nome}  |  {_now()}",
                 color=TXT,fontsize=9,fontweight="bold")

    ax1=fig.add_subplot(gs[0,:]); ax1.set_facecolor(CARD)
    ax1.axhspan(6.5,9.5,color=GREEN,alpha=0.07); ax1.axhspan(3.5,6.5,color=AMBER,alpha=0.07)
    ax1.axhspan(0.5,3.5,color=RED,alpha=0.07)
    ax1.plot(range(len(hist)),hist["quadrant"].values,color="#378ADD",linewidth=1.2,zorder=2)
    ax1.scatter(range(len(hist)),hist["quadrant"].values,
                c=[QUAD_BG[int(q)] for q in hist["quadrant"]],s=18,zorder=3,edgecolors="none")
    ax1.set_yticks(range(1,10)); ax1.set_yticklabels([f"Q{i}" for i in range(1,10)],color=MUTED,fontsize=7)
    ax1.set_ylim(0.5,9.5); ax1.set_title("Evolucao do quadrante",color=MUTED,fontsize=8,pad=3)
    ax1.tick_params(colors=MUTED,labelsize=7)
    for sp in ax1.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    ax2=fig.add_subplot(gs[1,:2]); ax2.set_facecolor(CARD)
    ax2.plot(range(len(hist)),hist["rs_ratio"].values,color="#378ADD",linewidth=1.5,label="RS Ratio")
    ax2.plot(range(len(hist)),hist["rs_mom"].values,color=AMBER,linewidth=1.0,linestyle="--",label="RS Mom")
    ax2.axhline(0,color=MUTED,linewidth=0.6,linestyle="--")
    ax2.legend(fontsize=7,facecolor=CARD,labelcolor=TXT,framealpha=0.5)
    ax2.set_title("RS Ratio e Momentum",color=MUTED,fontsize=8,pad=3)
    ax2.tick_params(colors=MUTED,labelsize=7)
    for sp in ax2.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    ax3=fig.add_subplot(gs[1,2]); ax3.set_facecolor(CARD); ax3.axis("off")
    ax3.set_title(f"Frequencia ({janela} pregoes)",color=MUTED,fontsize=8,pad=3)
    freq=hist.groupby("quadrant").size().reset_index(name="n")
    freq["pct"]=(freq["n"]/janela*100).round(1); freq=freq.sort_values("n",ascending=False)
    y_t=0.93
    for _,r in freq.iterrows():
        q_f=int(r["quadrant"])
        ax3.text(0.05,y_t,f"Q{q_f} — {QUAD_LABEL[q_f][:14]}",transform=ax3.transAxes,
                 color=QUAD_TX.get(q_f,TXT),fontsize=7,
                 bbox=dict(boxstyle="round,pad=0.2",facecolor=QUAD_BG.get(q_f,"#333"),alpha=0.4,linewidth=0))
        ax3.text(0.62,y_t,str(int(r["n"])),transform=ax3.transAxes,color=TXT,fontsize=7)
        ax3.text(0.80,y_t,f"{r['pct']:.1f}%",transform=ax3.transAxes,color=TXT,fontsize=7)
        y_t-=0.09
    for sp in ax3.spines.values(): sp.set_edgecolor("#333"); sp.set_linewidth(0.5)

    return _fig_to_bytes(fig)


def exporta_historico(hist, ticker, indice_nome, janela):
    if hist is None or (hasattr(hist,"empty") and hist.empty):
        return None, None
    png = _png_historico(hist, ticker, indice_nome, janela)
    pdf = _pdf_historico(hist, ticker, indice_nome, janela)
    return png, pdf
