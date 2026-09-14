"""Coleta IPCA (IBGE/SIDRA) e dolar PTAX (Banco Central)."""
import json, gzip, csv, os, time, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

UA = {"User-Agent": "projeto academico de mineracao de dados", "Accept-Encoding": "gzip"}

SERIES = {
    "geral":       "7169",
    "tv_som_info": "7541",
    "computador":  "47641",
}
INICIO, FIM = "202203", "202608"


def baixa(url, tentativas=4, timeout=90):
    for i in range(tentativas):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
            b = r.read()
            if r.headers.get("Content-Encoding") == "gzip" or b[:2] == b"\x1f\x8b":
                b = gzip.decompress(b)
            return b
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(3 * (i + 1))


def ipca():
    linhas = {}
    for nome, cod in SERIES.items():
        url = (f"https://apisidra.ibge.gov.br/values/t/7060/n1/all/v/63"
               f"/p/{INICIO}-{FIM}/c315/{cod}")
        dados = json.loads(baixa(url).decode("utf-8", "replace"))
        for reg in dados[1:]:
            mes, valor = reg.get("D3C"), reg.get("V")
            if not mes:
                continue
            mes = f"{mes[:4]}-{mes[4:6]}"
            linhas.setdefault(mes, {"mes": mes})
            try:
                linhas[mes][nome] = float(valor)
            except (TypeError, ValueError):
                linhas[mes][nome] = None
        print(f"  IPCA {nome}: {len(dados)-1} meses", flush=True)

    saida = [linhas[m] for m in sorted(linhas)]
    with open(cam("dados", "ipca.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["mes"] + list(SERIES))
        w.writeheader(); w.writerows(saida)
    return saida


def dolar():
    url = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json"
           "&dataInicial=01/03/2022&dataFinal=30/09/2026")
    dados = json.loads(baixa(url).decode("utf-8", "replace"))
    saida = [{"data": d["data"], "cotacao": float(d["valor"])} for d in dados]
    with open(cam("dados", "dolar.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["data", "cotacao"])
        w.writeheader(); w.writerows(saida)
    print(f"  dolar: {len(saida)} cotacoes diarias "
          f"({saida[0]['data']} a {saida[-1]['data']})", flush=True)
    return saida


if __name__ == "__main__":
    print("baixando IPCA...", flush=True)
    i = ipca()
    print("baixando dolar...", flush=True)
    d = dolar()
    print(f"\nipca.csv: {len(i)} meses | dolar.csv: {len(d)} dias")
