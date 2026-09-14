"""Coleta o historico de precos da Kabum no Internet Archive."""
import re, json, csv, sys, time, urllib.request, collections
from concurrent.futures import ThreadPoolExecutor

import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)


ALVO = "www.kabum.com.br/hardware/placa-de-video-vga"
CDX = ("http://web.archive.org/cdx/search/cdx?url=" + ALVO +
       "&output=json&collapse=timestamp:8&from=20220301&to=20260930&filter=statuscode:200")
UA = {"User-Agent": "Mozilla/5.0 (projeto academico de mineracao de dados)"}


def baixa(url, timeout=60, tentativas=3):
    for i in range(tentativas):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(4 * (i + 1))


def lista_capturas():
    d = json.loads(baixa(CDX))
    col = d[0].index("timestamp")
    return sorted({linha[col] for linha in d[1:]})


def extrai(ts):
    url = f"http://web.archive.org/web/{ts}/https://{ALVO}"
    try:
        pagina = baixa(url, timeout=55, tentativas=2).decode("utf-8", "replace")
    except Exception as e:
        return ts, "erro-rede", []
    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', pagina, re.S)
    if not m:
        return ts, "sem-next-data", []
    try:
        interno = json.loads(json.loads(m.group(1))["props"]["pageProps"]["data"])
        produtos = interno["catalogServer"]["data"]
    except Exception:
        return ts, "estrutura-antiga", []

    linhas = []
    for p in produtos:
        fab = p.get("manufacturer")
        linhas.append({
            "data": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
            "codigo": p.get("code"),
            "nome": (p.get("name") or "").strip(),
            "fabricante": (fab.get("name") if isinstance(fab, dict) else fab) or "",
            "preco": p.get("price"),
            "preco_desconto": p.get("priceWithDiscount"),
            "preco_antigo": p.get("oldPrice"),
            "disponivel": p.get("available"),
            "vendedor": p.get("sellerName") or "",
        })
    return ts, "ok", linhas


def main():
    caps = lista_capturas()
    print(f"capturas no indice: {len(caps)}", flush=True)

    todas, status = [], collections.Counter()
    with ThreadPoolExecutor(max_workers=4) as ex:
        for i, (ts, st, linhas) in enumerate(ex.map(extrai, caps), 1):
            status[st] += 1
            todas.extend(linhas)
            if i % 10 == 0:
                print(f"  {i}/{len(caps)}  linhas={len(todas)}", flush=True)

    campos = ["data", "codigo", "nome", "fabricante", "preco",
              "preco_desconto", "preco_antigo", "disponivel", "vendedor"]
    with open(cam("dados", "precos_acervo.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(todas)

    print("\n--- resultado da coleta")
    for st, n in status.most_common():
        print(f"  {st}: {n}")
    print(f"  linhas gravadas: {len(todas)}")
    datas = sorted({l['data'] for l in todas})
    print(f"  datas com dado: {len(datas)} ({datas[0]} a {datas[-1]})")
    print(f"  produtos distintos: {len({l['codigo'] for l in todas})}")


if __name__ == "__main__":
    main()
