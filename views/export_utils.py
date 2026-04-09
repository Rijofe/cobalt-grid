# views/export_utils.py
# ------------------------------------------------------------
# Geração de PNG e PDF para todos os slides do app.
# Usa matplotlib para composição visual e fpdf2 para PDF.
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

# ── Paleta ────────────────────────────────────────────────────
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


def _fig_header(fig, titulo, subtitulo=""):
    fig.patch.set_facecolor(BG)
    fig.text(0.5, 0.99, titulo, ha="center", va="top",
             color=TXT, fontsize=13, fontweight="bold")
    if subtitulo:
        fig.text(0.5, 0.965, subtitulo, ha="center", va="top",
                 color=MUTED, fontsize=8)
    fig.text(0.98, 0.005, _now(), ha="right", color=MUTED, fontsize=7)


def _fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _png_to_pdf(png, titulo):
    from PIL import Image as PILImage
    # Descobre dimensões reais do PNG
    img = PILImage.open(io.BytesIO(png))
    w_px, h_px = img.size
    dpi = 150
    w_mm = w_px / dpi * 25.4
    h_mm = h_px / dpi * 25.4 + 15  # +15mm para título e rodapé

    pdf = FPDF(orientation="L" if w_mm > h_mm else "P",
               unit="mm", format=(max(w_mm, h_mm), min(w_mm, h_mm))
               if w_mm > h_mm else (w_mm, h_mm))
    pdf.add_page()
    pdf.set_fill_color(17, 17, 17)
    pdf.rect(0, 0, w_mm, h_mm, "F")
    titulo_safe = titulo.replace("—","-").replace("–","-").replace("·",".")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(200, 200, 200)
    pdf.set_xy(5, 3)
    pdf.cell(0, 5, titulo_safe)
    pdf.image(io.BytesIO(png), x=4, y=10, w=w_mm - 8)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(80, 80, 80)
    pdf.set_xy(5, h_mm - 6)
    pdf.cell(0, 4, f"Gerado em {_now()} | RS Quadrants | cobalt-grid")
    return bytes(pdf.output())


# ── 1. QUADRANTES ─────────────────────────────────────────────

def exporta_quadrantes(df, indice_nome, breadth, params,
                       selected_ticker=None, prices=None, index_series=None):
    has_detail = (selected_ticker is not None and
                  not df[df["ticker"] == selected_ticker].empty)

    # Layout: cabeçalho fixo + cards topo + grade + (opcional) detalhe
    n_rows = 5 if has_detail else 4  # cards, grade(x3), detalhe
    height_ratios = [0.5, 1, 3, 3, 3] if not has_detail else [0.5, 1, 3, 3, 3, 2.5]
    height = 13 if not has_detail else 18

    fig = plt.figure(figsize=(18, height))
    fig.patch.set_facecolor(BG)

    n_gs = 5 if not has_detail else 6
    hr   = [0.5, 1, 3, 3, 3] if not has_detail else [0.5, 1, 3, 3, 3, 2.5]
    gs   = gridspec.GridSpec(n_gs, 1, figure=fig, height_ratios=hr,
                             hspace=0.08, top=0.97, bottom=0.02, left=0.04, right=0.98)

    # ── Título ──
    ax_title = fig.add_subplot(gs[0])
    ax_title.set_facecolor(BG); ax_title.axis("off")
    ax_title.text(0.5, 0.7, f"Quadrantes - vs {indice_nome}",
                  transform=ax_title.transAxes, ha="center", va="center",
                  color=TXT, fontsize=14, fontweight="bold")
    ax_title.text(0.5, 0.1,
                  f"RS {params.get('rs_window',21)}d  Mom {params.get('mom_window',5)}d  "
                  f"{params.get('smoothing','EMA')}  Banda +-{params.get('neutral_band',0.5)}s  |  {_now()}",
                  transform=ax_title.transAxes, ha="center", va="center",
                  color=MUTED, fontsize=8)

    # ── Cards de métricas do topo ──
    gs_cards = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=gs[1], wspace=0.06)
    score = breadth.get("breadth_score", 0)
    idx_p = breadth.get("idx_perf_21d", None)
    cards_top = [
        ("Breadth Score",    f"{score:+d}",                              score),
        ("Acima do indice",  f"{breadth.get('pct_up',0):.1f}%",         breadth.get("pct_up",0)-50),
        ("Neutros",          f"{breadth.get('pct_neut',0):.1f}%",       0),
        ("Abaixo do indice", f"{breadth.get('pct_down',0):.1f}%",      -(breadth.get("pct_down",0)-50)),
        (indice_nome[:20],   f"{idx_p:+.1f}%" if idx_p else "-",        idx_p or 0),
    ]
    for i, (lbl, val, v) in enumerate(cards_top):
        axc = fig.add_subplot(gs_cards[0, i])
        axc.set_facecolor(CARD)
        cor = GREEN if v > 0 else RED if v < 0 else MUTED
        axc.text(0.5, 0.62, val, transform=axc.transAxes,
                 ha="center", va="center", fontsize=16, fontweight="bold", color=cor)
        axc.text(0.5, 0.22, lbl, transform=axc.transAxes,
                 ha="center", va="center", fontsize=8, color=MUTED)
        axc.set_xticks([]); axc.set_yticks([])
        for sp in axc.spines.values(): sp.set_edgecolor("#2a2a2a"); sp.set_linewidth(0.5)

    # ── Grade 3x3 ──
    gs_grade = gridspec.GridSpecFromSubplotSpec(3, 3, subplot_spec=gs[2:5],
                                                hspace=0.06, wspace=0.04)
    col_labels = ["<- Perdendo forca", "Estavel", "Acelerando ->"]
    row_labels  = ["^ Acima", "-> Neutro", "v Abaixo"]
    row_colors  = [GREEN, AMBER, RED]

    for ri, quad_row in enumerate(GRID_LAYOUT):
        for ci, q in enumerate(quad_row):
            ax = fig.add_subplot(gs_grade[ri, ci])
            ax.set_facecolor(QUAD_BG[q])
            items = df[df["quadrant"] == q].sort_values("rs_ratio", ascending=False)
            n = len(items)
            ax.text(0.97, 0.97, str(q), transform=ax.transAxes,
                    ha="right", va="top", fontsize=20, color=QUAD_TX[q], alpha=0.2, fontweight="bold")
            ax.text(0.03, 0.97, f"n={n}", transform=ax.transAxes,
                    ha="left", va="top", fontsize=7.5, color=QUAD_TX[q], alpha=0.8)
            ax.text(0.5, 0.88, QUAD_LABEL[q], transform=ax.transAxes,
                    ha="center", va="top", fontsize=6.5, color=QUAD_TX[q], alpha=0.65, style="italic")
            y_c, x_c = 0.72, 0.04
            for idx2, (_, r) in enumerate(items.head(14).iterrows()):
                sign = "+" if r["rs_ratio"] >= 0 else ""
                chip = f"{r['ticker'].replace('.SA','')} {sign}{r['rs_ratio']:.1f}s"
                if x_c + 0.48 > 0.96:
                    x_c = 0.04; y_c -= 0.155
                if y_c < 0.04:
                    ax.text(0.96, 0.04, f"+{n-idx2}", transform=ax.transAxes,
                            ha="right", va="bottom", fontsize=6.5, color=QUAD_TX[q], alpha=0.6)
                    break
                ax.text(x_c, y_c, chip, transform=ax.transAxes,
                        ha="left", va="top", fontsize=6.5, color=QUAD_TX[q])
                x_c += 0.5
            if ri == 0:
                ax.set_title(col_labels[ci], color=MUTED, fontsize=7.5, pad=3)
            if ci == 0:
                ax.set_ylabel(row_labels[ri], color=row_colors[ri], fontsize=7.5, labelpad=3)
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_visible(False)

    # ── Painel de detalhe ──
    if has_detail:
        row_d = df[df["ticker"] == selected_ticker].iloc[0]
        q_d   = int(row_d["quadrant"])
        gs_det = gridspec.GridSpecFromSubplotSpec(1, 6, subplot_spec=gs[5], wspace=0.06)

        # Badge identificação
        ax0 = fig.add_subplot(gs_det[0, 0])
        ax0.set_facecolor(QUAD_BG[q_d])
        ax0.text(0.5, 0.72, selected_ticker.replace(".SA",""), transform=ax0.transAxes,
                 ha="center", va="center", fontsize=14, fontweight="bold", color=QUAD_TX[q_d])
        ax0.text(0.5, 0.47, row_d["nome"][:18], transform=ax0.transAxes,
                 ha="center", va="center", fontsize=8, color=QUAD_TX[q_d], alpha=0.85)
        ax0.text(0.5, 0.22, f"Q{q_d} - {QUAD_LABEL[q_d]}", transform=ax0.transAxes,
                 ha="center", va="center", fontsize=7, color=QUAD_TX[q_d], alpha=0.7)
        ax0.set_xticks([]); ax0.set_yticks([])
        for sp in ax0.spines.values(): sp.set_visible(False)

        # 4 métricas
        metrics = [
            ("RS Ratio (z-score)", f"{row_d['rs_ratio']:+.2f}s", row_d["rs_ratio"]),
            ("RS Momentum",        f"{row_d['rs_mom']:+.2f}s",   row_d["rs_mom"]),
            ("Perf. 21d",          f"{row_d['perf_21d']:+.1f}%", row_d["perf_21d"]),
            (f"vs {indice_nome[:10]} 21d", f"{row_d['perf_vs_index']:+.1f}%", row_d["perf_vs_index"]),
        ]
        for i, (lbl, val, v) in enumerate(metrics):
            axm = fig.add_subplot(gs_det[0, i+1])
            axm.set_facecolor(CARD)
            color = GREEN if v > 0 else RED if v < 0 else MUTED
            axm.text(0.5, 0.62, val, transform=axm.transAxes,
                     ha="center", va="center", fontsize=14, fontweight="bold", color=color)
            axm.text(0.5, 0.22, lbl, transform=axm.transAxes,
                     ha="center", va="center", fontsize=7.5, color=MUTED)
            axm.set_xticks([]); axm.set_yticks([])
            for sp in axm.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

        # Gráfico RS histórico
        ax_rs = fig.add_subplot(gs_det[0, 5])
        ax_rs.set_facecolor(CARD)
        rs_series = row_d.get("rs_series")
        if rs_series is not None and len(rs_series) > 0:
            color_line = GREEN if row_d["rs_ratio"] >= 0 else RED
            ax_rs.plot(range(len(rs_series)), rs_series.values,
                       color=color_line, linewidth=1.5)
            ax_rs.fill_between(range(len(rs_series)), rs_series.values,
                               0, alpha=0.15, color=color_line)
            ax_rs.axhline(0,    color=MUTED, linewidth=0.7, linestyle="--")
            ax_rs.axhline(0.5,  color=GREEN, linewidth=0.5, linestyle=":")
            ax_rs.axhline(-0.5, color=RED,   linewidth=0.5, linestyle=":")
        ax_rs.set_title(f"RS Ratio (z-score) - 63 pregoes", color=MUTED, fontsize=7.5, pad=2)
        ax_rs.tick_params(colors=MUTED, labelsize=6)
        for sp in ax_rs.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    png = _fig_to_bytes(fig)
    return png, _png_to_pdf(png, f"RS Quadrants - vs {indice_nome}")


# ── 2. LIDERES & LAGGARDS ─────────────────────────────────────

def exporta_lideres(df, indice_nome):
    lideres  = df[df["quadrant"] >= 7].sort_values("rs_ratio", ascending=False)
    laggards = df[df["quadrant"] <= 3].sort_values("rs_ratio")
    todos    = df.sort_values("rs_ratio", ascending=False)
    grupos   = [
        ("Lideres - Q7, Q8, Q9",  lideres,  GREEN, ">>"),
        ("Laggards - Q1, Q2, Q3", laggards, RED,   "!!"),
        ("Todos",                  todos,    MUTED, "--"),
    ]
    total_rows = sum(len(g[1]) for g in grupos) + len(grupos) * 3
    height = max(8, total_rows * 0.26 + 3)
    fig, ax = plt.subplots(figsize=(18, height))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    _fig_header(fig, f"Lideres & Laggards - vs {indice_nome}")

    y = 0.94
    cols = ["Ticker","Nome","Q","RS (s)","Mom (s)","Perf 21d%",f"vs Idx%"]
    xs   = [0.02, 0.10, 0.30, 0.37, 0.46, 0.55, 0.64]

    for titulo, subset, cor, icone in grupos:
        ax.text(0.02, y, f"{icone} {titulo}  ({len(subset)} ativos)",
                transform=ax.transAxes, ha="left", va="top",
                color=cor, fontsize=10, fontweight="bold")
        y -= 0.024
        if subset.empty:
            ax.text(0.5, y, "Nenhum ativo", transform=ax.transAxes,
                    ha="center", color=MUTED, fontsize=8)
            y -= 0.025; continue
        for xi, col in zip(xs, cols):
            ax.text(xi, y, col, transform=ax.transAxes,
                    ha="left", va="top", color=MUTED, fontsize=7.5, fontweight="bold")
        y -= 0.02
        ax.axhline(y, color="#333333", linewidth=0.5, xmin=0.02, xmax=0.75,
                   transform=ax.transAxes)
        y -= 0.004
        for _, r in subset.iterrows():
            vals = [
                r["ticker"].replace(".SA",""),
                r["nome"][:22],
                f"Q{int(r['quadrant'])}",
                f"{r['rs_ratio']:+.2f}",
                f"{r['rs_mom']:+.2f}",
                f"{r['perf_21d']:+.1f}",
                f"{r['perf_vs_index']:+.1f}",
            ]
            for xi, val, col in zip(xs, vals, cols):
                c = TXT
                if col in ("RS (s)","Mom (s)","Perf 21d%","vs Idx%"):
                    try:
                        v = float(val); c = GREEN if v>0 else RED if v<0 else MUTED
                    except Exception: pass
                ax.text(xi, y, val, transform=ax.transAxes,
                        ha="left", va="top", color=c, fontsize=7)
            y -= 0.018
            if y < 0.02: break
        y -= 0.012

    fig.subplots_adjust(top=0.95, bottom=0.02, left=0.0, right=1.0)
    png = _fig_to_bytes(fig)
    return png, _png_to_pdf(png, f"Lideres & Laggards - vs {indice_nome}")


# ── 3. SCANNER DE CICLO ───────────────────────────────────────

def exporta_scanner(compras, vendas, indice_nome, janela):
    grupos = [
        ("Sinais de Compra", compras, GREEN, ">>"),
        ("Sinais de Venda",  vendas,  RED,   "!!"),
    ]
    total_rows = sum(len(g[1]) for g in grupos) + 6
    height = max(8, total_rows * 0.30 + 3)
    fig, ax = plt.subplots(figsize=(18, height))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    _fig_header(fig, f"Scanner de Ciclo - vs {indice_nome}",
                f"Janela de busca: {janela} pregoes")

    y = 0.93
    cols = ["Ticker","Nome","Transicao","Dias atras","RS atual (s)","Mom atual (s)"]
    xs   = [0.02, 0.10, 0.22, 0.52, 0.62, 0.73]

    for titulo, subset, cor, icone in grupos:
        ax.text(0.02, y, f"{icone} {titulo}  ({len(subset)} sinais)",
                transform=ax.transAxes, ha="left", va="top",
                color=cor, fontsize=10, fontweight="bold")
        y -= 0.026
        if subset.empty:
            ax.text(0.5, y, "Nenhum sinal encontrado", transform=ax.transAxes,
                    ha="center", color=MUTED, fontsize=8)
            y -= 0.035; continue
        for xi, col in zip(xs, cols):
            ax.text(xi, y, col, transform=ax.transAxes,
                    ha="left", va="top", color=MUTED, fontsize=7.5, fontweight="bold")
        y -= 0.02
        ax.axhline(y, color="#333333", linewidth=0.5, xmin=0.02, xmax=0.85,
                   transform=ax.transAxes)
        y -= 0.004
        for _, r in subset.sort_values("dias_atrás").iterrows():
            dias = int(r["dias_atrás"])
            trans_safe = r["transicao"].replace("→","->") if "transicao" in r else r.get("transição","").replace("→","->")
            vals = [
                r["ticker"],
                r["nome"][:20],
                trans_safe,
                "Hoje" if dias==0 else f"{dias}d",
                f"{r['rs_atual']:+.2f}",
                f"{r['mom_atual']:+.2f}",
            ]
            for xi, val, col in zip(xs, vals, cols):
                c = TXT
                if col in ("RS atual (s)","Mom atual (s)"):
                    try: v=float(val); c = GREEN if v>0 else RED if v<0 else MUTED
                    except Exception: pass
                elif col == "Dias atras":
                    c = GREEN if dias==0 else TXT if dias<=2 else MUTED
                ax.text(xi, y, val, transform=ax.transAxes,
                        ha="left", va="top", color=c, fontsize=7)
            y -= 0.019
            if y < 0.02: break
        y -= 0.018

    fig.subplots_adjust(top=0.95, bottom=0.02)
    png = _fig_to_bytes(fig)
    return png, _png_to_pdf(png, f"Scanner de Ciclo - vs {indice_nome} - Janela {janela}d")


# ── 4. ATIVO INDIVIDUAL ───────────────────────────────────────

def exporta_ativo(row, indice_nome, prices, index_series, janela=63):
    ticker = row["ticker"].replace(".SA","")
    q = int(row["quadrant"])
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor(BG)
    gs = gridspec.GridSpec(2, 5, figure=fig, hspace=0.38, wspace=0.08,
                           top=0.90, bottom=0.06, left=0.04, right=0.98)
    _fig_header(fig, f"Ativo Individual - {ticker} ({row['nome']}) - vs {indice_nome}")

    # Card identificação
    ax0 = fig.add_subplot(gs[0, 0])
    ax0.set_facecolor(QUAD_BG[q])
    ax0.text(0.5, 0.65, ticker, transform=ax0.transAxes,
             ha="center", va="center", fontsize=18, fontweight="bold", color=QUAD_TX[q])
    ax0.text(0.5, 0.40, row["nome"][:18], transform=ax0.transAxes,
             ha="center", va="center", fontsize=8, color=QUAD_TX[q], alpha=0.85)
    ax0.text(0.5, 0.18, f"Q{q} - {QUAD_LABEL[q]}", transform=ax0.transAxes,
             ha="center", va="center", fontsize=7, color=QUAD_TX[q], alpha=0.7)
    ax0.set_xticks([]); ax0.set_yticks([])
    for sp in ax0.spines.values(): sp.set_visible(False)

    # 4 métricas
    metrics = [
        ("RS Ratio (z-score)", f"{row['rs_ratio']:+.2f}s", row["rs_ratio"]),
        ("RS Momentum",        f"{row['rs_mom']:+.2f}s",   row["rs_mom"]),
        ("Perf. 21d",          f"{row['perf_21d']:+.1f}%", row["perf_21d"]),
        (f"vs {indice_nome[:10]} 21d", f"{row['perf_vs_index']:+.1f}%", row["perf_vs_index"]),
    ]
    for i, (lbl, val, v) in enumerate(metrics):
        axm = fig.add_subplot(gs[0, i+1])
        axm.set_facecolor(CARD)
        color = GREEN if v>0 else RED if v<0 else MUTED
        axm.text(0.5, 0.62, val, transform=axm.transAxes,
                 ha="center", va="center", fontsize=15, fontweight="bold", color=color)
        axm.text(0.5, 0.25, lbl, transform=axm.transAxes,
                 ha="center", va="center", fontsize=7.5, color=MUTED)
        axm.set_xticks([]); axm.set_yticks([])
        for sp in axm.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    # Gráfico preço normalizado
    ax_price = fig.add_subplot(gs[1, :3])
    ax_price.set_facecolor(CARD)
    try:
        t_full = row["ticker"]
        if t_full in prices.columns and index_series is not None:
            ap = prices[t_full].dropna().iloc[-janela:]
            ip = index_series.reindex(ap.index).ffill().dropna()
            common = ap.index.intersection(ip.index)
            ap2, ip2 = ap.loc[common], ip.loc[common]
            an  = ap2 / ap2.iloc[0] * 100
            inp = ip2 / ip2.iloc[0] * 100
            ax_price.plot(range(len(an)), an.values, color="#378ADD", linewidth=1.5, label=ticker)
            ax_price.plot(range(len(inp)), inp.values, color=MUTED, linewidth=1.0,
                          linestyle="--", label=indice_nome[:12])
            ax_price.legend(fontsize=7.5, facecolor=CARD, labelcolor=TXT,
                            framealpha=0.5, loc="upper left")
    except Exception:
        ax_price.text(0.5, 0.5, "Dados indisponiveis", transform=ax_price.transAxes,
                      ha="center", color=MUTED)
    ax_price.set_title("Preco normalizado (base 100)", color=MUTED, fontsize=8, pad=3)
    ax_price.tick_params(colors=MUTED, labelsize=7)
    ax_price.set_facecolor(CARD)
    for sp in ax_price.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    # Gráfico RS histórico
    ax_rs = fig.add_subplot(gs[1, 3:])
    ax_rs.set_facecolor(CARD)
    rs_series = row.get("rs_series")
    if rs_series is not None and len(rs_series) > 0:
        color_line = GREEN if row["rs_ratio"] >= 0 else RED
        ax_rs.plot(range(len(rs_series)), rs_series.values, color=color_line, linewidth=1.5)
        ax_rs.fill_between(range(len(rs_series)), rs_series.values, 0, alpha=0.15, color=color_line)
        ax_rs.axhline(0,    color=MUTED, linewidth=0.6, linestyle="--")
        ax_rs.axhline(0.5,  color=GREEN, linewidth=0.5, linestyle=":")
        ax_rs.axhline(-0.5, color=RED,   linewidth=0.5, linestyle=":")
        n_pts = len(rs_series)
    else:
        n_pts = 0
    ax_rs.set_title(f"RS Ratio (z-score) - {n_pts} pregoes", color=MUTED, fontsize=8, pad=3)
    ax_rs.tick_params(colors=MUTED, labelsize=7)
    for sp in ax_rs.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    png = _fig_to_bytes(fig)
    return png, _png_to_pdf(png, f"Ativo Individual - {ticker} - vs {indice_nome}")


# ── 5. MARKET BREADTH ─────────────────────────────────────────

def exporta_breadth(df, breadth, indice_nome, idx_perf):
    fig = plt.figure(figsize=(18, 11))
    fig.patch.set_facecolor(BG)
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.15,
                           top=0.92, bottom=0.05, left=0.05, right=0.97)
    _fig_header(fig, f"Market Breadth - vs {indice_nome}")

    # Score
    ax_g = fig.add_subplot(gs[0, 0])
    ax_g.set_facecolor(CARD)
    score = breadth.get("breadth_score", 0)
    cor_s = GREEN if score > 0 else RED if score < 0 else AMBER
    ax_g.barh(0, score, color=cor_s, height=0.4)
    ax_g.barh(0,  100, color="#2a2a2a", height=0.4)
    ax_g.barh(0, -100, color="#2a2a2a", height=0.4)
    ax_g.set_xlim(-105, 105)
    ax_g.text(0, 0, f"{score:+d}", ha="center", va="center",
              fontsize=18, fontweight="bold", color=cor_s)
    ax_g.set_title("Breadth Score", color=MUTED, fontsize=8, pad=3)
    ax_g.set_yticks([]); ax_g.set_xticks([-100,-50,0,50,100])
    ax_g.tick_params(colors=MUTED, labelsize=6)
    for sp in ax_g.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    # Performance índice
    ax_idx = fig.add_subplot(gs[0, 1])
    ax_idx.set_facecolor(CARD); ax_idx.axis("off")
    ax_idx.set_title(f"Performance {indice_nome[:14]}", color=MUTED, fontsize=8, pad=3)
    for i, (lbl, val) in enumerate([("5d", idx_perf.get("5d")), ("21d", idx_perf.get("21d")),
                                     ("63d", idx_perf.get("63d")), ("YTD", idx_perf.get("ytd"))]):
        v_str = f"{val:+.1f}%" if val is not None else "-"
        c = GREEN if (val or 0)>0 else RED if (val or 0)<0 else MUTED
        ax_idx.text(0.25, 0.82 - i*0.22, lbl, transform=ax_idx.transAxes, color=MUTED, fontsize=8)
        ax_idx.text(0.75, 0.82 - i*0.22, v_str, transform=ax_idx.transAxes,
                    color=c, fontsize=9, fontweight="bold", ha="right")

    # 7 métricas
    metricas = [
        ("Total",            breadth.get("total", 0),              TXT),
        ("Acima",            f"{breadth.get('pct_up', 0):.1f}%",   GREEN),
        ("Neutros",          f"{breadth.get('pct_neut', 0):.1f}%", AMBER),
        ("Abaixo",           f"{breadth.get('pct_down', 0):.1f}%", RED),
        ("Lideres Q9",       breadth.get("leaders_q9", 0),         GREEN),
        ("Turnarounds Q3",   breadth.get("turnarounds_q3", 0),     "#F7C1C1"),
        ("Potenciais Q6",    breadth.get("potential_q6", 0),       AMBER),
    ]
    positions = [(0,2),(1,2),(2,2),(0,3),(1,3),(2,3),(0,3)]
    for idx_m, (lbl, val, cor) in enumerate(metricas[:6]):
        r_m, c_m = positions[idx_m]
        axm = fig.add_subplot(gs[r_m, c_m])
        axm.set_facecolor(CARD)
        axm.text(0.5, 0.62, str(val), transform=axm.transAxes,
                 ha="center", va="center", fontsize=13, fontweight="bold", color=cor)
        axm.text(0.5, 0.25, lbl, transform=axm.transAxes,
                 ha="center", va="center", fontsize=7.5, color=MUTED)
        axm.set_xticks([]); axm.set_yticks([])
        for sp in axm.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    # Donut
    ax_d = fig.add_subplot(gs[1, 0])
    ax_d.set_facecolor(BG)
    up = breadth.get("up", 0); neut = breadth.get("neut", 0); dn = breadth.get("down", 0)
    if up + neut + dn > 0:
        ax_d.pie([up, neut, dn], colors=[GREEN, AMBER, RED],
                 wedgeprops=dict(width=0.5), startangle=90,
                 labels=[f"Acima\n{up}", f"Neutro\n{neut}", f"Abaixo\n{dn}"],
                 textprops={"color": TXT, "fontsize": 7})
    ax_d.set_title("Distribuicao por zona", color=MUTED, fontsize=8, pad=2)

    # Barras por quadrante
    ax_bar = fig.add_subplot(gs[1, 1:3])
    ax_bar.set_facecolor(CARD)
    qs = list(range(1, 10))
    counts = [len(df[df["quadrant"] == q]) for q in qs]
    bars = ax_bar.bar([f"Q{q}" for q in qs], counts,
                      color=[QUAD_BG[q] for q in qs], edgecolor="#333333", linewidth=0.5)
    for bar, cnt in zip(bars, counts):
        if cnt > 0:
            ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.2,
                        str(cnt), ha="center", va="bottom", fontsize=7.5, color=TXT)
    ax_bar.set_facecolor(CARD)
    ax_bar.set_title("Contagem por quadrante", color=MUTED, fontsize=8, pad=3)
    ax_bar.tick_params(colors=MUTED, labelsize=7.5)
    for sp in ax_bar.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    # Tabelas por zona
    zonas = [
        ("Acima (Q7-Q9)",   df[df["quadrant"] >= 7],           GREEN),
        ("Neutros (Q4-Q6)", df[df["quadrant"].between(4, 6)],  AMBER),
        ("Abaixo (Q1-Q3)",  df[df["quadrant"] <= 3],           RED),
    ]
    for zi, (ztit, zsub, zcor) in enumerate(zonas):
        ax_z = fig.add_subplot(gs[2, zi+1])
        ax_z.set_facecolor(CARD); ax_z.axis("off")
        ax_z.set_title(f"{ztit} ({len(zsub)})", color=zcor, fontsize=8, pad=3)
        y_t = 0.95
        for _, r in zsub.sort_values("rs_ratio", ascending=False).head(10).iterrows():
            sign = "+" if r["rs_ratio"] >= 0 else ""
            line = f"{r['ticker'].replace('.SA','')}  {sign}{r['rs_ratio']:.2f}s  {r['rs_mom']:+.2f}s  {r['perf_21d']:+.1f}%"
            ax_z.text(0.05, y_t, line, transform=ax_z.transAxes,
                      ha="left", va="top", color=TXT, fontsize=6.5)
            y_t -= 0.09
        for sp in ax_z.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    png = _fig_to_bytes(fig)
    return png, _png_to_pdf(png, f"Market Breadth - vs {indice_nome}")


# ── 6. HISTORICO ─────────────────────────────────────────────

def exporta_historico(hist, ticker, indice_nome, janela):
    if hist.empty:
        return None, None
    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor(BG)
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.38, wspace=0.12,
                           top=0.91, bottom=0.07, left=0.06, right=0.97)
    q_atual = int(hist["quadrant"].iloc[-1])
    _fig_header(fig,
                f"Historico de Quadrantes - {ticker} - vs {indice_nome}",
                f"Quadrante atual: Q{q_atual} - {QUAD_LABEL[q_atual]}  |  Periodo: {janela} pregoes")

    # Evolução quadrante
    ax1 = fig.add_subplot(gs[0, :])
    ax1.set_facecolor(CARD)
    ax1.axhspan(6.5, 9.5, color=GREEN, alpha=0.07)
    ax1.axhspan(3.5, 6.5, color=AMBER, alpha=0.07)
    ax1.axhspan(0.5, 3.5, color=RED,   alpha=0.07)
    ax1.plot(range(len(hist)), hist["quadrant"].values, color="#378ADD", linewidth=1.2, zorder=2)
    ax1.scatter(range(len(hist)), hist["quadrant"].values,
                c=[QUAD_BG[int(q)] for q in hist["quadrant"]], s=20, zorder=3, edgecolors="none")
    ax1.set_yticks(range(1, 10))
    ax1.set_yticklabels([f"Q{i}" for i in range(1, 10)], color=MUTED, fontsize=7.5)
    ax1.set_ylim(0.5, 9.5)
    ax1.set_title("Evolucao do quadrante ao longo do tempo", color=MUTED, fontsize=8, pad=3)
    ax1.tick_params(colors=MUTED, labelsize=7)
    for sp in ax1.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)
    for y_pos, lbl, cor in [(8.2,"^ Acima",GREEN),(5.0,"-> Neutro",AMBER),(1.8,"v Abaixo",RED)]:
        ax1.text(len(hist)*0.5, y_pos, lbl, color=cor, fontsize=7.5, alpha=0.4, ha="center")

    # RS + Momentum
    ax2 = fig.add_subplot(gs[1, :2])
    ax2.set_facecolor(CARD)
    ax2.plot(range(len(hist)), hist["rs_ratio"].values, color="#378ADD", linewidth=1.5, label="RS Ratio")
    ax2.plot(range(len(hist)), hist["rs_mom"].values, color=AMBER, linewidth=1.0,
             linestyle="--", label="RS Momentum")
    ax2.axhline(0,    color=MUTED, linewidth=0.6, linestyle="--")
    ax2.axhline(0.5,  color=GREEN, linewidth=0.5, linestyle=":")
    ax2.axhline(-0.5, color=RED,   linewidth=0.5, linestyle=":")
    ax2.legend(fontsize=7.5, facecolor=CARD, labelcolor=TXT, framealpha=0.5)
    ax2.set_title("RS Ratio e Momentum (z-score)", color=MUTED, fontsize=8, pad=3)
    ax2.tick_params(colors=MUTED, labelsize=7)
    for sp in ax2.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    # Tabela de frequência
    ax3 = fig.add_subplot(gs[1, 2])
    ax3.set_facecolor(CARD); ax3.axis("off")
    ax3.set_title(f"Tempo em cada quadrante (total: {janela} pregoes)",
                  color=MUTED, fontsize=8, pad=3)
    freq = hist.groupby("quadrant").size().reset_index(name="n")
    freq["pct"] = (freq["n"] / janela * 100).round(1)
    freq = freq.sort_values("n", ascending=False)
    y_t = 0.93
    for col_lbl, x_pos in [("Quadrante", 0.05), ("Pregoes", 0.60), ("% periodo", 0.82)]:
        ax3.text(x_pos, y_t, col_lbl, transform=ax3.transAxes,
                 color=MUTED, fontsize=7.5, fontweight="bold")
    y_t -= 0.10
    for _, r in freq.iterrows():
        q_f = int(r["quadrant"])
        ax3.text(0.05, y_t, f"Q{q_f} - {QUAD_LABEL[q_f][:14]}",
                 transform=ax3.transAxes, color=QUAD_TX.get(q_f, TXT), fontsize=7,
                 bbox=dict(boxstyle="round,pad=0.2", facecolor=QUAD_BG.get(q_f,"#333"), alpha=0.4, linewidth=0))
        ax3.text(0.62, y_t, str(int(r["n"])), transform=ax3.transAxes, color=TXT, fontsize=7.5)
        ax3.text(0.85, y_t, f"{r['pct']:.1f}%", transform=ax3.transAxes, color=TXT, fontsize=7.5)
        y_t -= 0.09
    for sp in ax3.spines.values(): sp.set_edgecolor("#333333"); sp.set_linewidth(0.5)

    png = _fig_to_bytes(fig)
    return png, _png_to_pdf(png, f"Historico - {ticker} - vs {indice_nome} - {janela}d")
