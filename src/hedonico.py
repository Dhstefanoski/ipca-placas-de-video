"""Extrai chip e faixa dos anuncios e estima os indices por regressao."""
import os, re
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)


def atributos(nome):
    n = nome.upper().replace("GEFORCE", " ").replace("RADEON", " ")
    n = re.sub(r"\s+", " ", n)

    marca = linha = numero = sufixo = None
    m = re.search(r"\b(RTX|GTX|GT)\s?-?(\d{3,4})\s?(TI|SUPER)?\b", n)
    if m:
        marca, linha, numero, sufixo = "NVIDIA", m.group(1), int(m.group(2)), m.group(3)
    else:
        m = re.search(r"\bRX\s?-?(\d{3,4})\s?(XTX|XT|GRE)?\b", n)
        if m:
            marca, linha, numero, sufixo = "AMD", "RX", int(m.group(1)), m.group(2)
        else:
            m = re.search(r"\bARC\s?([AB])\s?(\d{3})\b", n)
            if m:
                marca, linha, numero, sufixo = "INTEL", "ARC " + m.group(1), int(m.group(2)), None
    if marca is None:
        return None

    sep = "" if marca == "INTEL" else " "
    chip = f"{linha}{sep}{numero}" + (f" {sufixo}" if sufixo else "")

    if marca == "AMD" and numero >= 9000:
        faixa = numero % 100
    elif marca == "AMD" and numero >= 1000:
        faixa = (numero // 100) % 10 * 10
    elif marca == "AMD":
        faixa = {550: 50, 560: 50, 570: 60, 580: 60, 590: 60}.get(numero, 50)
    elif marca == "INTEL":
        faixa = {3: 50, 5: 60, 7: 70}.get(numero // 100, 50)
    else:
        faixa = numero % 100
    if sufixo in ("TI", "SUPER", "XT", "XTX", "GRE"):
        faixa += 5

    vram = None
    m = re.search(r"(\d{1,2})\s?GB\b", n) or re.search(r"\b[O]?(\d{1,2})G\b", n)
    if m:
        v = int(m.group(1))
        if v in (2, 3, 4, 6, 8, 10, 11, 12, 16, 20, 24, 32):
            vram = v
    return {"marca": marca, "chip": chip, "faixa": faixa, "vram": vram}


def prepara():
    df = pd.read_csv(cam("dados", "precos_acervo.csv"))
    n0 = len(df)
    df = df[(df.preco >= 200) & (df.preco <= 60000)].copy()
    attrs = df["nome"].apply(atributos)
    df = df[attrs.notna()].copy()
    df = pd.concat([df, pd.DataFrame(list(attrs.dropna()), index=df.index)], axis=1)
    df["vram"] = df.groupby("chip")["vram"].transform(lambda s: s.fillna(s.median()))
    df = df.dropna(subset=["vram"])
    df["fabricante"] = df["fabricante"].fillna("").str.upper().str.strip().replace("", "OUTRO")
    raros = df["fabricante"].value_counts()
    df.loc[df["fabricante"].isin(raros[raros < 20].index), "fabricante"] = "OUTRO"
    df["mes"] = df["data"].str[:7]
    df["log_preco"] = np.log(df["preco"])
    return df, n0


def indice(df, formula, nome):
    modelo = smf.ols(formula, data=df).fit(cov_type="HC1")
    X = modelo.model.exog
    posto = np.linalg.matrix_rank(X)
    print(f"  [{nome}] n={len(df)} colunas={X.shape[1]} posto={posto}"
          f"{'' if posto == X.shape[1] else '  <-- DEFICIENTE'}")
    meses = sorted(df["mes"].unique())
    base = meses[0]
    valores, ic_inf, ic_sup = [], [], []
    for m in meses:
        if m == base:
            b, se = 0.0, 0.0
        else:
            chave = f"C(mes)[T.{m}]"
            b, se = modelo.params[chave], modelo.bse[chave]
        valores.append(100 * np.exp(b))
        ic_inf.append(100 * np.exp(b - 1.96 * se))
        ic_sup.append(100 * np.exp(b + 1.96 * se))
    out = pd.DataFrame({"mes": meses, f"{nome}": valores,
                        f"{nome}_ic_inf": ic_inf, f"{nome}_ic_sup": ic_sup})
    return out, modelo


def main():
    df, n0 = prepara()
    print(f"linhas no acervo: {n0} | usadas na regressao: {len(df)} "
          f"({len(df)/n0:.0%}) | chips distintos: {df.chip.nunique()}")

    df_qc = df[df.groupby("chip")["mes"].transform("nunique") > 1]
    qc, m_qc = indice(df_qc, "log_preco ~ C(mes) + C(chip) + np.log(vram) + C(fabricante)",
                      "qualidade_constante")
    fx, m_fx = indice(df, "log_preco ~ C(mes) + C(faixa) + C(marca) + np.log(vram) + C(fabricante)",
                      "faixa_constante")
    print(f"R2 qualidade constante: {m_qc.rsquared:.3f} | R2 faixa constante: {m_fx.rsquared:.3f}")

    ipca = pd.read_csv(cam("dados", "ipca.csv"))
    ipca = ipca[ipca.mes >= qc.mes.min()].copy()
    for col in ("geral", "tv_som_info", "computador"):
        ipca[f"ipca_{col}"] = 100 * np.cumprod(1 + ipca[col].fillna(0) / 100)
        ipca[f"ipca_{col}"] /= ipca[f"ipca_{col}"].iloc[0] / 100

    dolar = pd.read_csv(cam("dados", "dolar.csv"))
    dolar["mes"] = pd.to_datetime(dolar["data"], dayfirst=True).dt.strftime("%Y-%m")
    dm = dolar.groupby("mes")["cotacao"].mean().reset_index(name="dolar")

    tab = (ipca[["mes", "ipca_geral", "ipca_tv_som_info", "ipca_computador"]]
           .merge(qc, on="mes", how="left").merge(fx, on="mes", how="left")
           .merge(dm, on="mes", how="left"))
    tab.to_csv(cam("dados", "indices.csv"), index=False, float_format="%.2f")

    d23 = df[df.mes >= "2023-01"]
    qc23, _ = indice(d23[d23.groupby("chip")["mes"].transform("nunique") > 1],
                     "log_preco ~ C(mes) + C(chip) + np.log(vram) + C(fabricante)",
                     "qualidade_constante")
    fx23, _ = indice(d23, "log_preco ~ C(mes) + C(faixa) + C(marca) + np.log(vram) + C(fabricante)",
                     "faixa_constante")
    ip23 = ipca[ipca.mes >= "2023-01"].copy()
    for col in ("geral", "tv_som_info", "computador"):
        ip23[f"ipca_{col}"] = ip23[f"ipca_{col}"] / ip23[f"ipca_{col}"].iloc[0] * 100
    (ip23[["mes", "ipca_geral", "ipca_tv_som_info", "ipca_computador"]]
     .merge(qc23, on="mes", how="left").merge(fx23, on="mes", how="left")
     .merge(dm, on="mes", how="left")
     .to_csv(cam("dados", "indices_desde_2023.csv"), index=False, float_format="%.2f"))

    df.drop(columns=["log_preco"]).to_csv(cam("dados", "produtos_atributos.csv"), index=False)
    with open(cam("dados", "modelo_resumo.txt"), "w", encoding="utf-8") as f:
        f.write("=== QUALIDADE CONSTANTE ===\n")
        f.write(m_qc.summary().as_text())
        f.write("\n\n=== FAIXA CONSTANTE ===\n")
        f.write(m_fx.summary().as_text())

    ult = tab.dropna(subset=["qualidade_constante"]).iloc[-1]
    print(f"\n=== {tab.mes.iloc[0]} a {ult.mes} (base 100) ===")
    for col, rot in [("qualidade_constante", "GPU, qualidade constante"),
                     ("faixa_constante", "GPU, faixa constante"),
                     ("ipca_computador", "IPCA Computador pessoal"),
                     ("ipca_tv_som_info", "IPCA TV, som e informatica"),
                     ("ipca_geral", "IPCA geral")]:
        print(f"  {rot:28} {ult[col]:7.1f}  ({ult[col]-100:+.1f}%)")
    d0 = dm.loc[dm.mes == tab.mes.iloc[0], "dolar"].iloc[0]
    print(f"  {'Dolar PTAX (media do mes)':28} R$ {d0:.2f} -> R$ {ult['dolar']:.2f} "
          f"({(ult['dolar']/d0-1)*100:+.1f}%)")


if __name__ == "__main__":
    main()
