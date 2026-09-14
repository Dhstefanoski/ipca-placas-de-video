"""API de consulta dos indices e do historico de precos."""
import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

app = FastAPI(title="Indice de precos de placas de video x IPCA",
              description="Indices hedonicos construidos a partir de precos de e-commerce, "
                          "comparados com o IPCA e o dolar.")


def _indices():
    return pd.read_csv(cam("dados", "indices.csv"))


def _produtos():
    frames = [pd.read_csv(cam("dados", "produtos_atributos.csv"))]
    diario = cam("dados", "precos_diarios.csv")
    if os.path.exists(diario):
        frames.append(pd.read_csv(diario))
    return pd.concat(frames, ignore_index=True)


def _limpo(df):
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


@app.get("/indices")
def indices(inicio: str | None = Query(None, description="AAAA-MM"),
            fim: str | None = Query(None, description="AAAA-MM")):
    """Serie mensal: indices de GPU, subitens do IPCA e dolar (base 100 = primeiro mes)."""
    df = _indices()
    if inicio:
        df = df[df.mes >= inicio]
    if fim:
        df = df[df.mes <= fim]
    return _limpo(df)


@app.get("/comparacao")
def comparacao(inicio: str | None = None, fim: str | None = None):
    """Variacao acumulada de cada serie entre dois meses com dado de GPU."""
    df = _indices().dropna(subset=["qualidade_constante"])
    if inicio:
        df = df[df.mes >= inicio]
    if fim:
        df = df[df.mes <= fim]
    if len(df) < 2:
        raise HTTPException(404, "periodo sem pelo menos dois meses com dado")
    a, b = df.iloc[0], df.iloc[-1]
    series = ["qualidade_constante", "faixa_constante", "ipca_computador",
              "ipca_tv_som_info", "ipca_geral", "dolar"]
    return {"inicio": a.mes, "fim": b.mes,
            "variacao_percentual": {s: round((b[s] / a[s] - 1) * 100, 1) for s in series}}


@app.get("/produtos")
def produtos(busca: str = Query(..., min_length=2, description="trecho do nome, ex: 4060"),
             limite: int = Query(50, le=500)):
    """Produtos cujo nome contem o trecho buscado, com o ultimo preco visto."""
    df = _produtos()
    achados = df[df["nome"].str.contains(busca, case=False, na=False, regex=False)]
    ult = achados.sort_values("data").groupby("codigo").tail(1)
    cols = [c for c in ["codigo", "nome", "fabricante", "chip", "data", "preco"] if c in ult]
    return _limpo(ult[cols].head(limite))


@app.get("/produtos/{codigo}")
def historico(codigo: int):
    """Historico de preco de um produto pelo codigo da loja."""
    df = _produtos()
    h = df[df["codigo"] == codigo].sort_values("data")
    if h.empty:
        raise HTTPException(404, "codigo nao encontrado")
    return {"codigo": codigo, "nome": h["nome"].iloc[-1],
            "historico": _limpo(h[["data", "preco"]])}
