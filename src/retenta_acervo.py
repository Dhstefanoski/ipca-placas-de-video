"""Repete a coleta das capturas do acervo que falharam."""
import csv, json, time, collections
from concurrent.futures import ThreadPoolExecutor

import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

from coleta_acervo import lista_capturas, extrai

CAMPOS = ["data", "codigo", "nome", "fabricante", "preco",
          "preco_desconto", "preco_antigo", "disponivel", "vendedor"]

existentes = list(csv.DictReader(open(cam("dados", "precos_acervo.csv"), encoding="utf-8")))
ja = {l["data"] for l in existentes}
caps = lista_capturas()
faltam = [ts for ts in caps if f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" not in ja]
print(f"ja coletadas: {len(ja)} | faltam: {len(faltam)}", flush=True)

novas, status = [], collections.Counter()
with ThreadPoolExecutor(max_workers=2) as ex:
    for i, (ts, st, linhas) in enumerate(ex.map(extrai, faltam), 1):
        status[st] += 1
        novas.extend(linhas)
        if i % 8 == 0:
            print(f"  {i}/{len(faltam)} novas={len(novas)}", flush=True)

todas = existentes + novas
todas.sort(key=lambda l: (l["data"], l["codigo"] or ""))
with open(cam("dados", "precos_acervo.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(todas)

print("\n--- retentativa")
for st, n in status.most_common():
    print(f"  {st}: {n}")
datas = sorted({l["data"] for l in todas})
print(f"  total de linhas: {len(todas)}")
print(f"  datas com dado: {len(datas)} de {len(caps)} capturas")
print(f"  produtos distintos: {len({l['codigo'] for l in todas})}")
meses = sorted({d[:7] for d in datas})
print(f"  meses cobertos: {len(meses)} ({meses[0]} a {meses[-1]})")
