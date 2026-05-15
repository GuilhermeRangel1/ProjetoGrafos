from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np


ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "out"
OUT.mkdir(exist_ok=True)

REGION_COLORS = {
    "Norte":        "#00c2a8",
    "Nordeste":     "#f5a623",
    "Sudeste":      "#e84393",
    "Sul":          "#6c63ff",
    "Centro-Oeste": "#ff6b35",
}

REGIOES_AEROPORTO = {
    "REC": "Nordeste", "SSA": "Nordeste", "FOR": "Nordeste",
    "NAT": "Nordeste", "JPA": "Nordeste", "THE": "Nordeste",
    "GRU": "Sudeste",  "CGH": "Sudeste",  "GIG": "Sudeste",
    "CNF": "Sudeste",  "VIX": "Sudeste",
    "BSB": "Centro-Oeste", "GYN": "Centro-Oeste",
    "CWB": "Sul",      "FLN": "Sul",      "POA": "Sul",
    "MAO": "Norte",    "BEL": "Norte",    "PVH": "Norte",    "RBR": "Norte",
}

BG      = "#0d0d14"
SURFACE = "#13131f"
TEXT    = "#e0e0f0"
MUTED   = "#777799"


def _base_fig(w=12, h=7):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=TEXT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#252535")
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    ax.grid(color="#252535", linewidth=0.6, linestyle="--", alpha=0.7)
    return fig, ax


def load_graus() -> dict[str, int]:
    path = OUT / "graus.csv"
    graus = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            graus[row["aeroporto"].strip().upper()] = int(row["grau"])
    return graus


def load_ego() -> dict[str, dict]:
    path = OUT / "ego_aeroportos.csv"
    ego = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iata = row["aeroporto"].strip().upper()
            ego[iata] = {
                "grau":          int(row["grau"]),
                "ordem_ego":     int(row["ordem_ego"]),
                "tamanho_ego":   int(row["tamanho_ego"]),
                "densidade_ego": float(row["densidade_ego"]),
            }
    return ego


def load_regioes() -> dict[str, dict]:
    path = OUT / "regioes.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)



def vis_exp1_dispersao(ego: dict):
    fig, ax = _base_fig(11, 7)

    for iata, m in ego.items():
        regiao = REGIOES_AEROPORTO.get(iata, "")
        color  = REGION_COLORS.get(regiao, "#aaaaaa")
        ax.scatter(m["grau"], m["densidade_ego"],
                   color=color, s=160, zorder=3, edgecolors="#ffffff", linewidths=0.6, alpha=0.92)
        ax.annotate(iata,
                    (m["grau"], m["densidade_ego"]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=8, color=TEXT, fontfamily="monospace")

    # linha de tendência
    xs = np.array([m["grau"]          for m in ego.values()])
    ys = np.array([m["densidade_ego"] for m in ego.values()])
    z  = np.polyfit(xs, ys, 1)
    p  = np.poly1d(z)
    xr = np.linspace(xs.min(), xs.max(), 200)
    ax.plot(xr, p(xr), color="#ff6b35", linewidth=1.5, linestyle="--",
            alpha=0.7, label="Tendência")

    # legenda de regiões
    handles = [mpatches.Patch(color=v, label=k) for k, v in REGION_COLORS.items()]
    handles.append(plt.Line2D([0],[0], color="#ff6b35", linestyle="--", label="Tendência"))
    ax.legend(handles=handles, loc="upper right", framealpha=0.2,
              facecolor=SURFACE, edgecolor="#252535",
              labelcolor=TEXT, fontsize=8)

    ax.set_xlabel("Grau (número de conexões diretas)", fontsize=10)
    ax.set_ylabel("Densidade da Ego-rede", fontsize=10)
    ax.set_title(
        "EXPLORATÓRIA 1 — Grau × Densidade da Ego-rede por Aeroporto\n"
        "Aeroportos mais conectados tendem a ter menor densidade local",
        fontsize=11, pad=14, color=TEXT
    )

    fig.tight_layout()
    path = OUT / "vis_exp1_dispersao_grau_densidade.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  ✓ {path.name}")



def vis_exp2_boxplot_regioes(graus: dict):
    # agrupar graus por região
    por_regiao: dict[str, list[int]] = {r: [] for r in REGION_COLORS}
    for iata, g in graus.items():
        r = REGIOES_AEROPORTO.get(iata, "")
        if r in por_regiao:
            por_regiao[r].append(g)

    regioes = list(REGION_COLORS.keys())
    dados   = [por_regiao[r] for r in regioes]
    cores   = [REGION_COLORS[r] for r in regioes]

    fig, ax = _base_fig(11, 6)

    bp = ax.boxplot(dados, patch_artist=True, notch=False,
                    medianprops=dict(color="#ffffff", linewidth=2),
                    whiskerprops=dict(color=MUTED, linewidth=1.2),
                    capprops=dict(color=MUTED, linewidth=1.2),
                    flierprops=dict(marker="o", color=MUTED, markersize=5))

    for patch, cor in zip(bp["boxes"], cores):
        patch.set_facecolor(cor)
        patch.set_alpha(0.75)
        patch.set_edgecolor("#ffffff")

    # pontos individuais
    for i, (vals, cor) in enumerate(zip(dados, cores), 1):
        jitter = np.random.uniform(-0.12, 0.12, len(vals))
        ax.scatter([i + j for j in jitter], vals,
                   color=cor, s=55, zorder=4, edgecolors="#ffffff",
                   linewidths=0.5, alpha=0.9)

    ax.set_xticks(range(1, len(regioes)+1))
    ax.set_xticklabels(regioes, fontsize=9, color=TEXT)
    ax.set_ylabel("Grau (número de conexões)", fontsize=10)
    ax.set_title(
        "EXPLORATÓRIA 2 — Distribuição de Graus por Região\n"
        "Sudeste e Nordeste apresentam maior variabilidade e graus mais elevados",
        fontsize=11, pad=14, color=TEXT
    )

    fig.tight_layout()
    path = OUT / "vis_exp2_boxplot_graus_regiao.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  ✓ {path.name}")



def vis_expl1_ranking(graus: dict):
    ordenado = sorted(graus.items(), key=lambda x: x[1], reverse=True)
    iatas    = [x[0] for x in ordenado]
    vals     = [x[1] for x in ordenado]
    cores    = [REGION_COLORS.get(REGIOES_AEROPORTO.get(i, ""), "#aaaaaa") for i in iatas]

    fig, ax = _base_fig(12, 8)

    bars = ax.barh(iatas, vals, color=cores, edgecolor="#0d0d14",
                   linewidth=0.5, height=0.7)

    # rótulos nas barras
    for bar, val in zip(bars, vals):
        ax.text(val + 0.15, bar.get_y() + bar.get_height()/2,
                str(val), va="center", ha="left",
                fontsize=9, color=TEXT, fontfamily="monospace")

    # destaque nos top 3
    for i in range(3):
        bars[i].set_edgecolor("#ffffff")
        bars[i].set_linewidth(1.5)
        ax.text(0.5, bars[i].get_y() + bars[i].get_height()/2,
                "★", va="center", ha="left",
                fontsize=10, color="#fff200")

    # legenda de regiões
    handles = [mpatches.Patch(color=v, label=k) for k, v in REGION_COLORS.items()]
    ax.legend(handles=handles, loc="lower right", framealpha=0.2,
              facecolor=SURFACE, edgecolor="#252535",
              labelcolor=TEXT, fontsize=8)

    ax.set_xlabel("Número de conexões diretas (grau)", fontsize=10)
    ax.set_title(
        "EXPLANATÓRIA 1 — Ranking de Conectividade dos Aeroportos Brasileiros\n"
        "CNF e BSB lideram com 19 conexões; PVH e RBR são os menos conectados (4)",
        fontsize=11, pad=14, color=TEXT
    )
    ax.invert_yaxis()
    ax.set_xlim(0, max(vals) + 2.5)

    # anotação explicativa
    ax.annotate(
        "Hubs nacionais concentram-se\nno Sudeste e Centro-Oeste",
        xy=(19, 1.5), xytext=(14, 5),
        arrowprops=dict(arrowstyle="->", color=MUTED),
        fontsize=8, color=MUTED,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=SURFACE, edgecolor="#252535")
    )

    fig.tight_layout()
    path = OUT / "vis_expl1_ranking_conectividade.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  ✓ {path.name}")



def vis_expl2_radar(regioes: dict):
    categorias = ["Aeroportos\n(ordem)", "Conexões\ninternas", "Densidade\ninterna (×10)"]
    regioes_list = list(regioes.keys())
    N = len(categorias)

    # normalizar para o radar
    def get_vals(r):
        d = regioes[r]
        return [
            d["ordem"],
            d["tamanho"],
            d["densidade"] * 10,   # × 10 para ficar na mesma escala
        ]

    angulos = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angulos += angulos[:1]  # fechar o polígono

    fig, ax = plt.subplots(figsize=(9, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, size=9, color=TEXT)
    ax.tick_params(colors=MUTED)
    ax.yaxis.set_tick_params(labelcolor=MUTED, labelsize=7)
    ax.spines["polar"].set_color("#252535")
    ax.grid(color="#252535", linewidth=0.7)

    for regiao in regioes_list:
        vals = get_vals(regiao)
        vals += vals[:1]
        cor  = REGION_COLORS.get(regiao, "#aaaaaa")
        ax.plot(angulos, vals, color=cor, linewidth=2, linestyle="solid")
        ax.fill(angulos, vals, color=cor, alpha=0.12)
        # rótulo no ponto máximo
        idx_max = np.argmax(vals[:-1])
        ax.annotate(regiao,
                    xy=(angulos[idx_max], vals[idx_max]),
                    xytext=(angulos[idx_max], vals[idx_max] + 0.8),
                    fontsize=8, color=cor, ha="center",
                    fontfamily="monospace")

    ax.set_title(
        "EXPLANATÓRIA 2 — Perfil Comparativo das Regiões Brasileiras\n"
        "Centro-Oeste lidera em densidade interna; Nordeste em quantidade de aeroportos",
        fontsize=10, pad=20, color=TEXT
    )

    # legenda
    handles = [mpatches.Patch(color=REGION_COLORS[r], label=r) for r in regioes_list]
    ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.35, 1.1),
              framealpha=0.2, facecolor=SURFACE, edgecolor="#252535",
              labelcolor=TEXT, fontsize=8)

    fig.tight_layout()
    path = OUT / "vis_expl2_radar_regioes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  ✓ {path.name}")



def main():
    print("[1/4] Carregando dados…")
    graus   = load_graus()
    ego     = load_ego()
    regioes = load_regioes()

    print("[2/4] Gerando visualizações exploratórias…")
    vis_exp1_dispersao(ego)
    vis_exp2_boxplot_regioes(graus)

    print("[3/4] Gerando visualizações explanatórias…")
    vis_expl1_ranking(graus)
    vis_expl2_radar(regioes)

    print("\n✅  Etapa 10 concluída. Arquivos gerados em out/:")
    for f in ["vis_exp1_dispersao_grau_densidade.png",
              "vis_exp2_boxplot_graus_regiao.png",
              "vis_expl1_ranking_conectividade.png",
              "vis_expl2_radar_regioes.png"]:
        print(f"     {f}")


if __name__ == "__main__":
    main()