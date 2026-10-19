"""Preco mediano por faixa comparado com o IPCA."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

FAIXAS = {50: "Entrada (xx50)", 60: "Intermediária (xx60)", 70: "Mais forte (xx70)"}
BASE, FIM = "2023", "2026"
MINIMO = 30


def carrega(com_variantes=False, so_kabum=False, campo="preco"):
    a = pd.read_csv(cam("dados", "produtos_atributos.csv"))
    if campo != "preco":
        a = a[a[campo].notna()].copy()
        a["preco"] = a[campo]
    a["ano"] = a["data"].str[:4]
    a["mes"] = a["data"].str[:7]
    if com_variantes:
        a["grupo"] = a["faixa"] // 10 * 10
    else:
        a["grupo"] = a["faixa"].where(a["faixa"] % 10 == 0)
    a = a[a["grupo"].isin(FAIXAS)].copy()
    a["grupo"] = a["grupo"].astype(int)
    if so_kabum:
        a = a[a["vendedor"].fillna("").str.upper().str.startswith("KABUM")]
    return a


def tira_fora_do_padrao(a):
    g = a.groupby(["ano", "grupo"])["preco"]
    q1, q3 = g.transform(lambda s: s.quantile(0.25)), g.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    antes = a.groupby(["ano", "grupo"]).size()
    b = a[(a["preco"] >= q1 - 1.5 * iqr) & (a["preco"] <= q3 + 1.5 * iqr)]
    depois = b.groupby(["ano", "grupo"]).size()
    return b, (antes - depois.reindex(antes.index, fill_value=0))


def medianas(a):
    t = (a.groupby(["ano", "grupo"])
          .agg(mediana=("preco", "median"), n=("preco", "size"), produtos=("codigo", "nunique"))
          .reset_index())
    return t


def ipca_anual(a):
    ind = pd.read_csv(cam("dados", "indices.csv"))
    meses = a.groupby("ano")["mes"].unique()
    linhas = []
    for ano, ms in meses.items():
        sel = ind[ind["mes"].isin(ms)]
        linhas.append({"ano": ano, "ipca_geral": sel["ipca_geral"].mean(),
                       "ipca_computador": sel["ipca_computador"].mean()})
    return pd.DataFrame(linhas)


def variacao(t, ip, base=BASE, fim=FIM):
    out = {}
    for f in FAIXAS:
        s = t[t["grupo"] == f].set_index("ano")
        if base in s.index and fim in s.index:
            out[f] = (s.loc[fim, "mediana"] / s.loc[base, "mediana"] - 1) * 100
        else:
            out[f] = np.nan
    ip = ip.set_index("ano")
    for c in ("ipca_geral", "ipca_computador"):
        out[c] = (ip.loc[fim, c] / ip.loc[base, c] - 1) * 100
    return out


LEGADOS = {"RX 550", "RX 560", "RX 570", "RX 580", "RX 590", "RX 5600", "GTX 750", "GTX 1050",
           "GTX 1060", "GTX 1650", "GTX 1660", "RTX 2060", "RTX 2070"}


def rodada(com_variantes=False, so_kabum=False, filtrar=True, base=BASE, sem_legado=False,
           campo="preco"):
    a = carrega(com_variantes, so_kabum, campo)
    if sem_legado:
        a = a[~a["chip"].isin(LEGADOS)]
    removidos = None
    if filtrar:
        a, removidos = tira_fora_do_padrao(a)
    t = medianas(a)
    return a, t, removidos, variacao(t, ipca_anual(a), base=base)


def grafico(t, ip):
    anos = [str(x) for x in range(int(BASE), int(FIM) + 1)]
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=200)
    ax.axhline(100, color="#bdbdbd", lw=1, zorder=1)
    finais = []
    s = t[t["grupo"] == 60].set_index("ano").reindex(anos)
    y = s["mediana"] / s.loc[BASE, "mediana"] * 100
    ax.plot(anos, y, color="#3A7CC4", lw=2.5, marker="o", ms=9, zorder=3,
            label="Placa intermediária (xx60), preço mediano")
    for i, (v, preco) in enumerate(zip(y, s["mediana"])):
        ax.annotate(f"R$ {preco:,.0f}".replace(",", "."), (i, v), textcoords="offset points",
                    xytext=(0, -22 if i == 0 else 14), ha="center", fontsize=10,
                    color="#1a1a1a", fontweight="bold")
    finais.append([y.iloc[-1], "Placa intermediária (xx60)", "#3A7CC4"])
    ipt = ip.set_index("ano").reindex(anos)
    for col, rot, cor in (("ipca_computador", "IPCA · computador pessoal", "#8E5BB5"),
                          ("ipca_geral", "IPCA · índice geral", "#C2590A")):
        v = ipt[col] / ipt.loc[BASE, col] * 100
        ax.plot(anos, v, color=cor, lw=2, marker="s", ms=8, zorder=3, label=rot)
        finais.append([v.iloc[-1], rot, cor])

    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0 - 3, y1 + 4)
    finais.sort(key=lambda x: x[0])
    passo = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.06
    for k in range(1, len(finais)):
        if finais[k][0] - finais[k - 1][0] < passo:
            finais[k][0] = finais[k - 1][0] + passo
    for yv, rot, cor in finais:
        ax.text(len(anos) - 1 + 0.08, yv, rot, va="center", fontsize=10.5, color="#1a1a1a")

    ax.set_xticks(range(len(anos)))
    ax.set_xticklabels([a if a != FIM else f"{a}\n(jan–ago)" for a in anos])
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#bdbdbd")
    ax.grid(axis="y", color="#e4e4e4", lw=0.8, zorder=0)
    ax.tick_params(colors="#5a5a5a", labelsize=10.5, length=0)
    ax.set_ylabel(f"preço mediano (base 100 = {BASE})", color="#5a5a5a", fontsize=10.5)
    ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor="#1a1a1a")
    fig.text(0.07, 0.95, "Placa de vídeo intermediária x IPCA, 2023 a 2026",
             fontsize=15, fontweight="bold", color="#1a1a1a")
    fig.text(0.07, 0.905, "RTX 3060, 4060 e 5060 e equivalentes AMD, preço mediano na Kabum",
             fontsize=10.5, color="#5a5a5a")
    fig.text(0.07, 0.02, "Faixas xx50 e xx70 fora do gráfico: menos de 30 preços em 2023. "
             "Preços fora do padrão (1,5 IQR) removidos.\n"
             "IPCA: média dos meses com captura de preço. Fontes: Kabum via Internet Archive, IBGE/SIDRA.",
             fontsize=8.5, color="#5a5a5a", linespacing=1.5)
    fig.subplots_adjust(left=0.08, right=0.76, top=0.84, bottom=0.14)
    os.makedirs(cam("figuras"), exist_ok=True)
    fig.savefig(cam("figuras", "medianas_faixa.png"), facecolor="white")
    plt.close(fig)


def main():
    todos = pd.read_csv(cam("dados", "produtos_atributos.csv"))
    conf = (todos.groupby(["marca", "chip", "faixa"])
                 .agg(precos=("preco", "size"), produtos=("codigo", "nunique"), exemplo=("nome", "first"))
                 .reset_index().sort_values(["faixa", "marca", "chip"]))
    conf["faixa_usada"] = (conf["faixa"] // 10 * 10).where((conf["faixa"] // 10 * 10).isin(FAIXAS))
    conf.to_csv(cam("dados", "conferencia_faixas.csv"), index=False)

    a, t, removidos, var = rodada()
    t["removidos_fora_do_padrao"] = [int(removidos.get((r.ano, r.grupo), 0)) for r in t.itertuples()]
    t["poucos_dados"] = t["n"] < MINIMO
    t.to_csv(cam("dados", "medianas_faixa.csv"), index=False, float_format="%.2f")

    ip = ipca_anual(a)
    grafico(t, ip)

    print("=== MEDIANA POR FAIXA (so modelos base, fora do padrao removido) ===")
    tab = t.pivot(index="ano", columns="grupo", values="mediana").round(0)
    n = t.pivot(index="ano", columns="grupo", values="n")
    for ano in tab.index:
        cel = "  ".join(f"xx{f}: R$ {tab.loc[ano, f]:>6,.0f} (n={int(n.loc[ano, f]):>3})"
                        if not np.isnan(tab.loc[ano, f]) else f"xx{f}: {'sem dado':>19}"
                        for f in FAIXAS)
        print(f"  {ano}  {cel}")
    print(f"  removidos por estarem fora do padrao: {int(removidos.sum())} de {int(removidos.sum()) + len(a)}")

    print(f"\n=== VARIACAO {BASE} -> {FIM} ===")
    for f, rot in FAIXAS.items():
        nb = int(n.loc[BASE, f]) if BASE in n.index and not np.isnan(n.loc[BASE, f]) else 0
        aviso = "  <- poucos dados no ano-base" if nb < MINIMO else ""
        print(f"  {rot:22} {var[f]:+6.1f}%{aviso}")
    print(f"  {'IPCA computador':22} {var['ipca_computador']:+6.1f}%")
    print(f"  {'IPCA geral':22} {var['ipca_geral']:+6.1f}%")

    variantes = [
        ("Principal", dict()),
        ("Com Ti/XT/Super", dict(com_variantes=True)),
        ("Sem remover fora do padrão", dict(filtrar=False)),
        ("Só vendedor Kabum", dict(so_kabum=True)),
        ("Base 2022 em vez de 2023", dict(base="2022")),
        ("Sem placas de geracoes antigas", dict(sem_legado=True)),
        ("Preco a vista em vez do cheio", dict(campo="preco_desconto")),
    ]
    linhas = []
    for nome, kw in variantes:
        _, tv, _, v = rodada(**kw)
        base = kw.get("base", BASE)
        nb = tv[tv.ano == base].set_index("grupo")["n"]
        linhas.append({"variante": nome, **{f"xx{f}": round(v[f], 1) for f in FAIXAS},
                       **{f"n_base_xx{f}": int(nb.get(f, 0)) for f in FAIXAS},
                       "ipca_computador": round(v["ipca_computador"], 1),
                       "ipca_geral": round(v["ipca_geral"], 1)})
    sens = pd.DataFrame(linhas)
    sens.to_csv(cam("dados", "medianas_sensibilidade.csv"), index=False)
    print("\n=== SENSIBILIDADE (variacao % ate 2026; n = precos no ano-base) ===")
    print(sens.to_string(index=False))


if __name__ == "__main__":
    main()
