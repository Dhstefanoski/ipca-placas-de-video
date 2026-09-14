"""Indices simples usados no diagnostico inicial."""
import csv, os, math, statistics, collections

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)


def carrega_precos():
    bruto = collections.defaultdict(list)
    descartados = collections.Counter()
    total = 0
    for l in csv.DictReader(open(cam("dados", "precos_acervo.csv"), encoding="utf-8")):
        total += 1
        cod = (l["codigo"] or "").strip()
        if not cod:
            descartados["sem codigo"] += 1; continue
        try:
            preco = float(l["preco"])
        except (TypeError, ValueError):
            descartados["preco ausente"] += 1; continue
        if not (200 <= preco <= 60000):
            descartados["fora de faixa"] += 1; continue
        bruto[(l["data"][:7], cod)].append(preco)

    por_mes = collections.defaultdict(dict)
    for (mes, cod), precos in bruto.items():
        por_mes[mes][cod] = statistics.median(precos)
    return por_mes, total, descartados


def indice_pareado(por_mes):
    meses = sorted(por_mes)
    indice = {meses[0]: 100.0}
    elos = []
    atual = 100.0
    for ant, prox in zip(meses, meses[1:]):
        comuns = set(por_mes[ant]) & set(por_mes[prox])
        if len(comuns) < 3:
            indice[prox] = atual
            elos.append((ant, prox, len(comuns), None))
            continue
        logs = [math.log(por_mes[prox][c] / por_mes[ant][c])
                for c in comuns if por_mes[ant][c] > 0]
        razao = math.exp(sum(logs) / len(logs))
        atual *= razao
        indice[prox] = atual
        elos.append((ant, prox, len(comuns), razao))
    return indice, elos


def ipca_encadeado():
    linhas = list(csv.DictReader(open(cam("dados", "ipca.csv"), encoding="utf-8")))
    series = {}
    for col in ("geral", "tv_som_info", "computador"):
        idx, atual = {}, 100.0
        for l in linhas:
            try:
                var = float(l[col])
            except (TypeError, ValueError):
                var = 0.0
            atual *= (1 + var / 100)
            idx[l["mes"]] = atual
        series[col] = idx
    return series


def main():
    por_mes, total, desc = carrega_precos()
    print(f"linhas lidas: {total}")
    for m, n in desc.most_common():
        print(f"  descartadas ({m}): {n}")
    print(f"meses com dado: {len(por_mes)}")

    idx, elos = indice_pareado(por_mes)
    validos = [e for e in elos if e[3]]
    print(f"\nelos do encadeamento: {len(elos)} | com pareamento suficiente: {len(validos)}")
    pares = [e[2] for e in validos]
    if pares:
        print(f"produtos pareados por elo: mediana {statistics.median(pares):.0f}, "
              f"min {min(pares)}, max {max(pares)}")

    ipca = ipca_encadeado()
    meses = sorted(idx)
    ini, fim = meses[0], meses[-1]

    def norm(serie):
        base = serie.get(ini)
        return {m: v / base * 100 for m, v in serie.items()} if base else {}

    ipca_n = {k: norm(v) for k, v in ipca.items()}

    print(f"\n=== RESULTADO  ({ini} a {fim}) ===")
    gpu_var = idx[fim] - 100
    print(f"  GPU (nosso indice, modelo pareado) : {gpu_var:+7.1f}%")
    for nome, rot in (("computador", "IPCA Computador pessoal"),
                      ("tv_som_info", "IPCA TV, som e informatica"),
                      ("geral", "IPCA geral")):
        s = ipca_n.get(nome, {})
        if fim in s:
            print(f"  {rot:34}: {s[fim]-100:+7.1f}%")
    if "computador" in ipca_n and fim in ipca_n["computador"]:
        dif = gpu_var - (ipca_n["computador"][fim] - 100)
        print(f"\n  diferenca GPU x IPCA Computador   : {dif:+7.1f} pontos percentuais")

    with open(cam("dados", "resultado.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mes", "indice_gpu", "ipca_computador", "ipca_tv_som_info", "ipca_geral"])
        for m in meses:
            w.writerow([m, round(idx[m], 2),
                        round(ipca_n["computador"].get(m, float("nan")), 2),
                        round(ipca_n["tv_som_info"].get(m, float("nan")), 2),
                        round(ipca_n["geral"].get(m, float("nan")), 2)])
    print(f"\ngravado: dados/resultado.csv ({len(meses)} meses)")


if __name__ == "__main__":
    main()
