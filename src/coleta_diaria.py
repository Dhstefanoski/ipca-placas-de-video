"""Coleta diaria de precos de placas de video na Kabum."""
import csv, json, os, re, sys, time, datetime, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "dados", "precos_diarios.csv")
BASE = "https://www.kabum.com.br/hardware/placa-de-video-vga"
PAGINAS = 5
PAUSA = 4
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"}
CAMPOS = ["data", "codigo", "nome", "fabricante", "preco", "preco_desconto",
          "preco_antigo", "disponivel", "vendedor"]


def pagina(n):
    url = BASE if n == 1 else f"{BASE}?page_number={n}&page_size=60"
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise RuntimeError("estrutura da pagina mudou: __NEXT_DATA__ ausente")
    interno = json.loads(json.loads(m.group(1))["props"]["pageProps"]["data"])
    return interno["catalogServer"]["data"]


def main():
    hoje = datetime.date.today().isoformat()
    linhas, vistos = [], set()
    for n in range(1, PAGINAS + 1):
        try:
            produtos = pagina(n)
        except Exception as e:
            print(f"pagina {n}: falhou ({e})", file=sys.stderr)
            break
        if not produtos:
            break
        for p in produtos:
            cod = p.get("code")
            if cod in vistos:
                continue
            vistos.add(cod)
            fab = p.get("manufacturer")
            linhas.append({
                "data": hoje, "codigo": cod, "nome": (p.get("name") or "").strip(),
                "fabricante": (fab.get("name") if isinstance(fab, dict) else fab) or "",
                "preco": p.get("price"), "preco_desconto": p.get("priceWithDiscount"),
                "preco_antigo": p.get("oldPrice"), "disponivel": p.get("available"),
                "vendedor": p.get("sellerName") or "",
            })
        time.sleep(PAUSA)

    if not linhas:
        print("nenhum produto coletado", file=sys.stderr)
        sys.exit(1)

    novo = not os.path.exists(SAIDA)
    with open(SAIDA, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        w.writerows(linhas)
    print(f"{hoje}: {len(linhas)} produtos gravados")


if __name__ == "__main__":
    main()
