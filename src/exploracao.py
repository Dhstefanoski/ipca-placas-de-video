"""Graficos exploratorios do conjunto de precos (artigo, secao de entendimento dos dados)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

CORES = {50: "#1D6FD8", 60: "#6B3FA0", 70: "#C2590A"}
ROTULOS = {50: "Entrada (xx50)", 60: "Intermediária (xx60)", 70: "Mais forte (xx70)"}
TINTA, TINTA2 = "#1a1a1a", "#5a5a5a"


def estilo():
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "axes.edgecolor": "#d4d4d4", "axes.labelcolor": TINTA,
        "grid.color": "#e8e8e8", "grid.linewidth": 0.8,
        "text.color": TINTA, "xtick.color": TINTA2, "ytick.color": TINTA2,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlepad": 14,
        "axes.labelsize": 11, "legend.frameon": False, "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })


def base():
    a = pd.read_csv(cam("dados", "produtos_atributos.csv"))
    a["ano"] = a["data"].str[:4]
    a["mes"] = a["data"].str[:7]
    a["grupo"] = a["faixa"].where(a["faixa"] % 10 == 0)
    return a


def grava(fig, nome):
    caminho = cam("figuras", nome)
    fig.savefig(caminho)
    plt.close(fig)
    print("gravado:", nome)


def precos_por_faixa(a):
    d = a[a["grupo"].isin(CORES)].copy()
    d["grupo"] = d["grupo"].astype(int)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(data=d, x="ano", y="preco", hue="grupo", ax=ax, width=0.7,
                palette={k: v for k, v in CORES.items()}, linewidth=1.2, fliersize=2)
    ax.set_title("Distribuição dos preços por faixa e ano")
    ax.set_xlabel(""); ax.set_ylabel("Preço (R$)")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    leg = ax.legend(title="")
    for t, g in zip(leg.get_texts(), sorted(d["grupo"].unique())):
        t.set_text(ROTULOS[g])
    grava(fig, "exp_precos_por_faixa.png")


def volume_por_faixa(a):
    d = a[a["grupo"].isin(CORES)].copy()
    d["grupo"] = d["grupo"].astype(int)
    t = d.groupby(["ano", "grupo"]).size().reset_index(name="n")
    fig, ax = plt.subplots(figsize=(9, 4.4))
    sns.barplot(data=t, x="ano", y="n", hue="grupo", ax=ax,
                palette={k: v for k, v in CORES.items()}, width=0.72, edgecolor="white")
    ax.set_title("Quantidade de anúncios por faixa e ano")
    ax.set_xlabel(""); ax.set_ylabel("Anúncios")
    for cont in ax.containers:
        ax.bar_label(cont, fontsize=8.5, color=TINTA2, padding=2)
    leg = ax.legend(title="")
    for t_, g in zip(leg.get_texts(), sorted(t["grupo"].unique())):
        t_.set_text(ROTULOS[g])
    grava(fig, "exp_volume_por_faixa.png")


def cobertura(a):
    t = a.groupby(["mes", "fonte"]).size().reset_index(name="n")
    meses = pd.period_range(a["mes"].min(), a["mes"].max(), freq="M").astype(str)
    t = (t.pivot(index="mes", columns="fonte", values="n")
           .reindex(meses).fillna(0))
    fig, ax = plt.subplots(figsize=(11, 4))
    base_acervo = t.get("acervo", pd.Series(0, index=t.index))
    ax.bar(t.index, base_acervo, color="#6B3FA0", width=0.75, label="Internet Archive")
    if "diario" in t:
        ax.bar(t.index, t["diario"], bottom=base_acervo, color="#1D6FD8", width=0.75,
               label="Coleta diária")
    ax.set_title("Anúncios classificados por mês e origem")
    ax.set_xlabel(""); ax.set_ylabel("Anúncios")
    ax.set_xticks(range(0, len(t.index), 3))
    ax.set_xticklabels(t.index[::3], rotation=45, ha="right", fontsize=9)
    vazios = int((t.sum(axis=1) == 0).sum())
    ax.legend(loc="upper left")
    ax.annotate(f"{vazios} meses sem nenhum anúncio no período", xy=(0.012, 0.70),
                xycoords="axes fraction", fontsize=9.5, color=TINTA2)
    grava(fig, "exp_cobertura_mensal.png")


def preco_memoria(a):
    d = a[a["grupo"].isin(CORES) & a["vram"].notna()].copy()
    d["grupo"] = d["grupo"].astype(int)
    fig, ax = plt.subplots(figsize=(8.6, 5))
    for g in sorted(d["grupo"].unique()):
        s = d[d["grupo"] == g]
        ax.scatter(s["vram"], s["preco"], s=14, alpha=0.45, color=CORES[g],
                   edgecolor="white", linewidth=0.3, label=ROTULOS[g])
    ax.set_title("Preço e memória de vídeo, por faixa")
    ax.set_xlabel("Memória (GB)"); ax.set_ylabel("Preço (R$)")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    ax.legend()
    grava(fig, "exp_preco_memoria.png")


def main():
    estilo()
    os.makedirs(cam("figuras"), exist_ok=True)
    a = base()
    print(f"anuncios classificados: {len(a)} | periodo: {a.mes.min()} a {a.mes.max()}")
    precos_por_faixa(a)
    volume_por_faixa(a)
    cobertura(a)
    preco_memoria(a)


if __name__ == "__main__":
    main()
