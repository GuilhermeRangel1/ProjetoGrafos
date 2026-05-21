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
    fig, ax = _base_fig(13, 8)
 
    # agrupar por posição para detectar sobreposições
    from collections import defaultdict
    grupos: dict[tuple, list] = defaultdict(list)
    for iata, m in ego.items():
        key = (m["grau"], round(m["densidade_ego"], 4))
        grupos[key].append(iata)
 
    plotados = {}  # iata → (x_final, y_final)
 
    for (grau, dens), iatas_grupo in grupos.items():
        n = len(iatas_grupo)
        if n == 1:
            # sem sobreposição — posição exata
            offsets = [(0.0, 0.0)]
        else:
            # distribuir em arco ao redor do ponto original
            angulos = np.linspace(0, 2 * np.pi, n, endpoint=False)
            raio_x  = 0.35
            raio_y  = 0.012
            offsets = [(raio_x * np.cos(a), raio_y * np.sin(a)) for a in angulos]
 
        for iata, (ox, oy) in zip(iatas_grupo, offsets):
            x = grau + ox
            y = dens + oy
            plotados[iata] = (x, y)
            regiao = REGIOES_AEROPORTO.get(iata, "")
            color  = REGION_COLORS.get(regiao, "#aaaaaa")
 
            ax.scatter(x, y, color=color, s=180, zorder=3,
                       edgecolors="#ffffff", linewidths=0.8, alpha=0.95)
 
            # linha tracejada ligando ao ponto real se houve deslocamento
            if ox != 0.0 or oy != 0.0:
                ax.plot([grau, x], [dens, y],
                        color=color, linewidth=0.7, linestyle=":", alpha=0.5, zorder=2)
 
        # marcar ponto original com um 'x' discreto se houve sobreposição
        if n > 1:
            ax.scatter(grau, dens, marker="+", color="#ffffff",
                       s=60, zorder=4, linewidths=1.0, alpha=0.4)
 
    # rótulos com posições ajustadas
    for iata, (x, y) in plotados.items():
        ax.annotate(iata, (x, y),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=8, color=TEXT, fontfamily="monospace",
                    bbox=dict(boxstyle="round,pad=0.15",
                              facecolor=SURFACE, edgecolor="none", alpha=0.6))
 
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



def vis_expl1_bolhas(graus: dict, ego: dict, regioes: dict):
    """
    Cada bolha = uma região.    
    Eixo X  = grau médio dos aeroportos da região
    Eixo Y  = densidade média das ego-redes da região
    Tamanho = número de aeroportos (ordem)
    Cor     = região
    """
    # agregar por região
    por_regiao: dict[str, list] = {r: [] for r in REGION_COLORS}
    for iata, m in ego.items():
        r = REGIOES_AEROPORTO.get(iata, "")
        if r in por_regiao:
            por_regiao[r].append(m)
 
    regioes_list = list(REGION_COLORS.keys())
    grau_med  = [np.mean([m["grau"]          for m in por_regiao[r]]) for r in regioes_list]
    dens_med  = [np.mean([m["densidade_ego"] for m in por_regiao[r]]) for r in regioes_list]
    ordem     = [regioes[r]["ordem"] for r in regioes_list]
    cores     = [REGION_COLORS[r]    for r in regioes_list]
 
    # tamanho das bolhas proporcional à ordem
    sizes = [o * 320 for o in ordem]
 
    fig, ax = _base_fig(11, 7)
 
    scatter = ax.scatter(grau_med, dens_med, s=sizes, c=cores,
                         alpha=0.78, edgecolors="#ffffff", linewidths=1.2, zorder=3)
 
    # rótulos dentro das bolhas
    for x, y, r, o in zip(grau_med, dens_med, regioes_list, ordem):
        ax.text(x, y, f"{r}\n({o} aerop.)",
                ha="center", va="center",
                fontsize=8, color="#ffffff", fontfamily="monospace",
                fontweight="bold")
 
    # anotações de insight
    # Centro-Oeste: maior densidade, poucos aeroportos
    ax.annotate(
        "Alta densidade interna\nmas apenas 2 aeroportos",
        xy=(grau_med[regioes_list.index("Centro-Oeste")],
            dens_med[regioes_list.index("Centro-Oeste")]),
        xytext=(grau_med[regioes_list.index("Centro-Oeste")] - 3.5,
                dens_med[regioes_list.index("Centro-Oeste")] + 0.025),
        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2),
        fontsize=8, color=MUTED,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=SURFACE, edgecolor="#252535")
    )
    # Sudeste: maior grau médio
    ax.annotate(
        "Maior grau médio\n(hubs nacionais)",
        xy=(grau_med[regioes_list.index("Sudeste")],
            dens_med[regioes_list.index("Sudeste")]),
        xytext=(grau_med[regioes_list.index("Sudeste")] + 0.5,
                dens_med[regioes_list.index("Sudeste")] - 0.03),
        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2),
        fontsize=8, color=MUTED,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=SURFACE, edgecolor="#252535")
    )
 
    # legenda de tamanho
    for o_ref, label in [(2, "2 aeroportos"), (4, "4 aeroportos"), (6, "6 aeroportos")]:
        ax.scatter([], [], s=o_ref*320, c="#555566",
                   edgecolors="#ffffff", linewidths=0.8,
                   label=label, alpha=0.7)
    ax.legend(loc="lower left", framealpha=0.2, facecolor=SURFACE,
              edgecolor="#252535", labelcolor=TEXT, fontsize=8,
              title="Tamanho da bolha", title_fontsize=8)
 
    ax.set_xlabel("Grau médio dos aeroportos da região", fontsize=10)
    ax.set_ylabel("Densidade média das ego-redes", fontsize=10)
    ax.set_title(
        "EXPLANATÓRIA 1 — Perfil de Conectividade por Região\n"
        "Sudeste tem os aeroportos mais conectados; Centro-Oeste tem a maior coesão interna",
        fontsize=11, pad=14, color=TEXT
    )
 
    fig.tight_layout()
    path = OUT / "vis_expl1_bolhas_regioes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  ✓ {path.name}")



def vis_expl2_mini_heatmap(regioes: dict):
    """
    Heatmap simplificado por região.
    Apenas 5 regiões × 3 métricas agregadas.
    """

    ordem_regioes = [
        "Norte",
        "Nordeste",
        "Centro-Oeste",
        "Sul",
        "Sudeste"
    ]

    metricas = [
        "Ordem",
        "Tamanho",
        "Densidade"
    ]

    # matriz de dados
    dados_raw = []

    for r in ordem_regioes:

        dados_raw.append([
            regioes[r]["ordem"],
            regioes[r]["tamanho"],
            regioes[r]["densidade"]
        ])

    dados_raw = np.array(dados_raw, dtype=float)

    # normalização coluna a coluna
    dados_norm = np.zeros_like(dados_raw)

    for col in range(dados_raw.shape[1]):

        mn = dados_raw[:, col].min()
        mx = dados_raw[:, col].max()

        if mx > mn:
            dados_norm[:, col] = (
                dados_raw[:, col] - mn
            ) / (mx - mn)
        else:
            dados_norm[:, col] = 0.5

    # figura
    fig, ax = plt.subplots(figsize=(7, 5.5))

    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)

    im = ax.imshow(
        dados_norm,
        cmap="YlOrRd",
        aspect="auto",
        vmin=0,
        vmax=1
    )

    # ticks
    ax.set_xticks(range(len(metricas)))
    ax.set_xticklabels(
        metricas,
        fontsize=10,
        color=TEXT
    )

    ax.set_yticks(range(len(ordem_regioes)))
    ax.set_yticklabels(
        ordem_regioes,
        fontsize=10,
        fontweight="bold"
    )

    # colorir nomes das regiões
    for tick, regiao in zip(ax.get_yticklabels(), ordem_regioes):

        tick.set_color(
            REGION_COLORS.get(regiao, TEXT)
        )

    # valores dentro das células
    for i in range(len(ordem_regioes)):
        for j in range(len(metricas)):

            valor = dados_raw[i, j]

            if j == 2:
                texto = f"{valor:.3f}"
            else:
                texto = f"{valor:.1f}"

            brilho = dados_norm[i, j]

            cor_txt = "#000000" if brilho > 0.45 else "#000000"

            ax.text(
                j,
                i,
                texto,
                ha="center",
                va="center",
                fontsize=11,
                color=cor_txt,
                fontfamily="monospace"
            )

    # bordas das células
    ax.set_xticks(
        np.arange(-0.5, len(metricas), 1),
        minor=True
    )

    ax.set_yticks(
        np.arange(-0.5, len(ordem_regioes), 1),
        minor=True
    )

    ax.grid(
        which="minor",
        color="#252535",
        linestyle="-",
        linewidth=1.2
    )

    ax.tick_params(which="minor", bottom=False, left=False)

    # colorbar
    cbar = fig.colorbar(
        im,
        ax=ax,
        fraction=0.045,
        pad=0.04
    )

    cbar.ax.tick_params(colors=MUTED)
    cbar.outline.set_edgecolor("#252535")

    cbar.ax.set_ylabel(
        "Valor normalizado",
        color=MUTED,
        fontsize=8
    )

    # título
    ax.set_title(
        "EXPLANATÓRIA 2 — Perfil Regional da Rede Aérea\n"
        "Sudeste lidera em conectividade; Centro-Oeste apresenta maior coesão local",
        fontsize=11,
        pad=14,
        color=TEXT
    )

    # bordas
    for spine in ax.spines.values():
        spine.set_edgecolor("#252535")

    fig.tight_layout()

    path = OUT / "vis_expl2_mini_heatmap_regioes.png"

    fig.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
        facecolor=BG
    )

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
    vis_expl1_bolhas(graus, ego, regioes)
    vis_expl2_mini_heatmap(regioes)

    print("\n✅  Etapa 10 concluída. Arquivos gerados em out/:")
    for f in ["vis_exp1_dispersao_grau_densidade.png",
              "vis_exp2_boxplot_graus_regiao.png",
              "vis_expl1_bolhas_regioes.png",
              "vis_expl2_mini_heatmap_regioes.png"]:
        print(f"     {f}")


if __name__ == "__main__":
    main()