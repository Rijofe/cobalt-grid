# views/export_utils.py
# ------------------------------------------------------------
# Gera exportações PNG e PDF do slide atual.
# Usa matplotlib para PNG e fpdf2 para PDF.
# ------------------------------------------------------------

import io
import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from fpdf import FPDF

# Cores dos quadrantes
QUAD_COLORS = {
    9: ("#3B6D11", "#EAF3DE"),
    8: ("#97C459", "#173404"),
    7: ("#C0DD97", "#27500A"),
    6: ("#854F0B", "#FAEEDA"),
    5: ("#EF9F27", "#412402"),
    4: ("#FAC775", "#633806"),
    1: ("#791F1F", "#FCEBEB"),
    2: ("#E24B4A", "#FCEBEB"),
    3: ("#F7C1C1", "#791F1F"),
}

QUAD_LABELS = {
    9: "Acima · Acelerando",
    8: "Acima · Estável",
    7: "Acima · Desacelerando",
    6: "Neutro · Acelerando",
    5: "Neutro · Estável",
    4: "Neutro · Perdendo",
    1: "Abaixo · Piorando",
    2: "Abaixo · Estável",
    3: "Abaixo · Recuperando",
}

GRID_LAYOUT = [[7, 8, 9], [4, 5, 6], [1, 2, 3]]


# ── PNG — Grade de quadrantes ─────────────────────────────────

def gera_png_quadrantes(df: pd.DataFrame, indice_nome: str,
                         breadth: dict, params: dict) -> bytes:
    fig, axes = plt.subplots(3, 3, figsize=(16, 10))
    fig.patch.set_facecolor("#1a1a1a")

    titulo = f"RS Quadrants — vs {indice_nome}"
    subtitulo = (f"Breadth Score: {breadth.get('breadth_score', 0):+d}  |  "
                 f"Acima: {breadth.get('pct_up', 0):.1f}%  |  "
                 f"Neutros: {breadth.get('pct_neut', 0):.1f}%  |  "
                 f"Abaixo: {breadth.get('pct_down', 0):.1f}%  |  "
                 f"RS {params.get('rs_window', 21)}d · Mom {params.get('mom_window', 5)}d")
    data_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    fig.suptitle(titulo, color="white", fontsize=16, fontweight="bold", y=0.98)
    fig.text(0.5, 0.94, subtitulo, ha="center", color="#aaaaaa", fontsize=9)
    fig.text(0.98, 0.01, data_str, ha="right", color="#666666", fontsize=8)

    col_labels = ["← Perdendo força", "Estável", "Acelerando ↗"]
    row_labels = ["↑ Acima", "→ Neutro", "↓ Abaixo"]

    for row_idx, quad_row in enumerate(GRID_LAYOUT):
        for col_idx, q in enumerate(quad_row):
            ax = axes[row_idx][col_idx]
            bg_color, tx_color = QUAD_COLORS[q]
            ax.set_facecolor(bg_color)

            items = df[df["quadrant"] == q].sort_values("rs_ratio", ascending=False)
            count = len(items)

            # Número do quadrante
            ax.text(0.97, 0.97, str(q), transform=ax.transAxes,
                    ha="right", va="top", fontsize=22, color=tx_color,
                    alpha=0.25, fontweight="bold")

            # Contagem
            ax.text(0.03, 0.97, f"n={count}", transform=ax.transAxes,
                    ha="left", va="top", fontsize=8, color=tx_color,
                    alpha=0.8)

            # Label do quadrante
            ax.text(0.5, 0.88, QUAD_LABELS[q], transform=ax.transAxes,
                    ha="center", va="top", fontsize=7, color=tx_color,
                    alpha=0.7, style="italic")

            # Chips de ativos
            chips_text = []
            for _, r in items.head(12).iterrows():
                sign = "+" if r["rs_ratio"] >= 0 else ""
                chips_text.append(f"{r['ticker'].replace('.SA','')} {sign}{r['rs_ratio']:.1f}σ")

            y_pos = 0.72
            x_pos = 0.05
            for i, chip in enumerate(chips_text):
                if x_pos + 0.45 > 0.95:
                    x_pos = 0.05
                    y_pos -= 0.16
                if y_pos < 0.05:
                    break
                ax.text(x_pos, y_pos, chip, transform=ax.transAxes,
                        ha="left", va="top", fontsize=6.5, color=tx_color,
                        fontweight="500")
                x_pos += 0.48

            if count > 12:
                ax.text(0.97, 0.03, f"+{count-12}", transform=ax.transAxes,
                        ha="right", va="bottom", fontsize=7, color=tx_color, alpha=0.6)

            # Labels de eixo
            if row_idx == 0:
                ax.set_title(col_labels[col_idx], color="#888888",
                             fontsize=8, pad=4)
            if col_idx == 0:
                ax.set_ylabel(row_labels[row_idx], color="#888888",
                              fontsize=8, labelpad=4)

            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_xticks([])
            ax.set_yticks([])

    plt.tight_layout(rect=[0, 0.03, 1, 0.93])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ── PNG — Scanner de Ciclo ────────────────────────────────────

def gera_png_scanner(compras: pd.DataFrame, vendas: pd.DataFrame,
                      indice_nome: str, janela: int) -> bytes:
    fig, axes = plt.subplots(1, 2, figsize=(16, max(6, max(len(compras), len(vendas)) * 0.35 + 2)))
    fig.patch.set_facecolor("#1a1a1a")

    data_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    fig.suptitle(f"Scanner de Ciclo — vs {indice_nome} — Janela {janela}d",
                 color="white", fontsize=14, fontweight="bold", y=0.99)
    fig.text(0.98, 0.01, data_str, ha="right", color="#666666", fontsize=8)

    for ax, subset, titulo, cor in [
        (axes[0], compras, "🟢 Sinais de Compra", "#3B6D11"),
        (axes[1], vendas,  "🔴 Sinais de Venda",  "#791F1F"),
    ]:
        ax.set_facecolor("#1a1a1a")
        ax.set_title(titulo, color=cor, fontsize=11, fontweight="bold", pad=8)

        if subset.empty:
            ax.text(0.5, 0.5, "Nenhum sinal", transform=ax.transAxes,
                    ha="center", va="center", color="#888888", fontsize=10)
        else:
            cols = ["Ticker", "Transição", "Dias atrás", "RS atual (σ)", "Mom atual (σ)"]
            data = subset[["ticker", "transição", "dias_atrás", "rs_atual", "mom_atual"]].copy()
            data.columns = cols
            data["RS atual (σ)"] = data["RS atual (σ)"].map("{:+.2f}".format)
            data["Mom atual (σ)"] = data["Mom atual (σ)"].map("{:+.2f}".format)

            table = ax.table(
                cellText=data.values,
                colLabels=cols,
                cellLoc="left",
                loc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.4)

            for (r, c), cell in table.get_celld().items():
                cell.set_facecolor("#1a1a1a" if r > 0 else "#2a2a2a")
                cell.set_text_props(color="white" if r > 0 else "#aaaaaa")
                cell.set_edgecolor("#333333")

        ax.axis("off")

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ── PNG — Líderes & Laggards ──────────────────────────────────

def gera_png_lideres(df: pd.DataFrame, indice_nome: str) -> bytes:
    lideres  = df[df["quadrant"] >= 7].sort_values("rs_ratio", ascending=False).head(20)
    laggards = df[df["quadrant"] <= 3].sort_values("rs_ratio").head(20)

    fig, axes = plt.subplots(1, 2, figsize=(16, max(6, max(len(lideres), len(laggards)) * 0.35 + 2)))
    fig.patch.set_facecolor("#1a1a1a")
    data_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    fig.suptitle(f"Líderes & Laggards — vs {indice_nome}", color="white",
                 fontsize=14, fontweight="bold", y=0.99)
    fig.text(0.98, 0.01, data_str, ha="right", color="#666666", fontsize=8)

    for ax, subset, titulo, cor in [
        (axes[0], lideres,  "🏆 Líderes (Q7-Q9)", "#3B6D11"),
        (axes[1], laggards, "⚠️ Laggards (Q1-Q3)", "#791F1F"),
    ]:
        ax.set_facecolor("#1a1a1a")
        ax.set_title(titulo, color=cor, fontsize=11, fontweight="bold", pad=8)

        if subset.empty:
            ax.text(0.5, 0.5, "Nenhum ativo", transform=ax.transAxes,
                    ha="center", va="center", color="#888888", fontsize=10)
        else:
            display = subset[["ticker", "nome", "quadrant", "rs_ratio", "rs_mom",
                               "perf_21d", "perf_vs_index"]].copy()
            display["ticker"] = display["ticker"].str.replace(".SA", "", regex=False)
            display["quadrant"] = display["quadrant"].map(lambda q: f"Q{q}")
            display.columns = ["Ticker", "Nome", "Q", "RS (σ)", "Mom (σ)", "Perf 21d%", "vs Idx%"]
            display["RS (σ)"]    = display["RS (σ)"].map("{:+.2f}".format)
            display["Mom (σ)"]   = display["Mom (σ)"].map("{:+.2f}".format)
            display["Perf 21d%"] = display["Perf 21d%"].map("{:+.1f}".format)
            display["vs Idx%"]   = display["vs Idx%"].map("{:+.1f}".format)

            table = ax.table(cellText=display.values, colLabels=display.columns,
                             cellLoc="left", loc="center")
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.4)

            for (r, c), cell in table.get_celld().items():
                cell.set_facecolor("#1a1a1a" if r > 0 else "#2a2a2a")
                cell.set_text_props(color="white" if r > 0 else "#aaaaaa")
                cell.set_edgecolor("#333333")

        ax.axis("off")

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ── PDF genérico a partir do PNG ──────────────────────────────

def png_para_pdf(png_bytes: bytes, titulo: str) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_fill_color(26, 26, 26)
    pdf.rect(0, 0, 297, 210, "F")

    # Salva PNG temporário
    img_buf = io.BytesIO(png_bytes)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(200, 200, 200)
    pdf.set_xy(5, 5)
    pdf.cell(0, 6, titulo, ln=True)

    pdf.image(img_buf, x=5, y=12, w=287)

    data_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(5, 203)
    pdf.cell(0, 5, f"Gerado em {data_str} · RS Quadrants · cobalt-grid")

    return bytes(pdf.output())


# ── Funções públicas por slide ────────────────────────────────

def exporta_quadrantes(df, indice_nome, breadth, params):
    png = gera_png_quadrantes(df, indice_nome, breadth, params)
    pdf = png_para_pdf(png, f"RS Quadrants — vs {indice_nome}")
    return png, pdf


def exporta_scanner(compras, vendas, indice_nome, janela):
    png = gera_png_scanner(compras, vendas, indice_nome, janela)
    pdf = png_para_pdf(png, f"Scanner de Ciclo — vs {indice_nome}")
    return png, pdf


def exporta_lideres(df, indice_nome):
    png = gera_png_lideres(df, indice_nome)
    pdf = png_para_pdf(png, f"Líderes & Laggards — vs {indice_nome}")
    return png, pdf
