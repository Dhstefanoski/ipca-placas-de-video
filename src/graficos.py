"""Graficos dos indices da regressao comparados com o IPCA."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

SERIES = [
    ("qualidade_constante", "GPU · qualidade constante", "#3A7CC4"),
    ("faixa_constante",     "GPU · faixa constante",     "#C2590A"),
    ("ipca_computador",     "IPCA · computador pessoal", "#2E8B57"),
    ("ipca_geral",          "IPCA · índice geral",       "#8E5BB5"),
]
TINTA, TINTA2, GRADE = "#1a1a1a", "#5a5a5a", "#e4e4e4"


def linha_com_lacunas(ax, x, y, cor):
    ok = ~np.isnan(y)
    xs, ys = x[ok], y[ok]
    ax.plot(xs, ys, color=cor, lw=2, ls=(0, (1.5, 2)), solid_capstyle="round", zorder=2)
    seg = np.split(np.arange(len(y)), np.where(~ok)[0])
    for s in seg:
        s = s[ok[s]]
        if len(s) > 1:
            ax.plot(x[s], y[s], color=cor, lw=2, solid_capstyle="round", zorder=3)


def figura(tab, arquivo, titulo, subtitulo, destacar_2022):
    x = pd.to_datetime(tab["mes"] + "-01").to_numpy()
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=200)
    fig.patch.set_facecolor("white")

    if destacar_2022:
        ax.axvspan(pd.Timestamp("2022-03-01"), pd.Timestamp("2022-12-31"),
                   color="#f2f2f2", zorder=0)
        ax.text(pd.Timestamp("2022-07-20"), 0.985, "fim da escassez\nde placas",
                transform=ax.get_xaxis_transform(), ha="center", va="top",
                fontsize=9, color=TINTA2)

    ic = tab[["qualidade_constante_ic_inf", "qualidade_constante_ic_sup"]].to_numpy()
    ok = ~np.isnan(ic[:, 0])
    ax.fill_between(x[ok], ic[ok, 0], ic[ok, 1], color="#3A7CC4", alpha=0.14,
                    lw=0, zorder=1)

    ax.axhline(100, color="#bdbdbd", lw=1, zorder=1)
    finais = []
    for col, rotulo, cor in SERIES:
        y = tab[col].to_numpy(dtype=float)
        linha_com_lacunas(ax, x, y, cor)
        i = np.where(~np.isnan(y))[0][-1]
        finais.append([y[i], x[i], rotulo, cor])

    finais.sort(key=lambda f: f[0])
    minimo = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.055
    for k in range(1, len(finais)):
        if finais[k][0] - finais[k - 1][0] < minimo:
            finais[k][0] = finais[k - 1][0] + minimo
    xmax = pd.Timestamp(tab["mes"].iloc[-1] + "-01")
    for yv, xv, rotulo, cor in finais:
        ax.plot([xmax + pd.Timedelta(days=22)], [yv], "s", ms=6, color=cor, clip_on=False)
        ax.text(xmax + pd.Timedelta(days=42), yv, rotulo, va="center", fontsize=10,
                color=TINTA, clip_on=False)

    ax.set_xlim(x[0], xmax)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#bdbdbd")
    ax.grid(axis="y", color=GRADE, lw=0.8, zorder=0)
    ax.tick_params(colors=TINTA2, labelsize=10, length=0)
    ax.set_ylabel(f"índice (base 100 = {tab['mes'].iloc[0]})", color=TINTA2, fontsize=10)

    fig.text(0.07, 0.95, titulo, fontsize=15, fontweight="bold", color=TINTA)
    fig.text(0.07, 0.905, subtitulo, fontsize=10.5, color=TINTA2)
    fig.text(0.07, 0.02, "Faixa azul: intervalo de 95% do índice a qualidade constante. "
             "Pontilhado: meses sem captura no acervo.  Fontes: Kabum via Internet Archive, "
             "IBGE/SIDRA, BCB.", fontsize=8.5, color=TINTA2)
    fig.subplots_adjust(left=0.07, right=0.76, top=0.84, bottom=0.10)
    os.makedirs(cam("figuras"), exist_ok=True)
    fig.savefig(cam("figuras", arquivo), facecolor="white")
    plt.close(fig)
    print("gravado:", arquivo)


def carrega(arquivo):
    tab = pd.read_csv(cam("dados", arquivo))
    return tab[tab.mes <= tab.dropna(subset=["qualidade_constante"]).mes.iloc[-1]].reset_index(drop=True)


def main():
    tab = carrega("indices.csv")
    figura(tab, "indices_periodo_completo.png",
           "Preço de placas de vídeo x IPCA, 2022 a 2026",
           "O mesmo chip ficou bem mais barato; a inflação geral subiu 21%",
           destacar_2022=True)
    figura(carrega("indices_desde_2023.csv"), "indices_desde_2023.png",
           "A partir de 2023: mesmo chip estável, mesma faixa bem mais cara",
           "A distância entre as duas linhas de GPU é o efeito do ajuste por qualidade",
           destacar_2022=False)


if __name__ == "__main__":
    main()
