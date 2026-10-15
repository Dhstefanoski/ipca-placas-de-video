"""Modelos supervisionados: estimativa de preco e verificacao das faixas."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
                             mean_absolute_error, mean_absolute_percentage_error, r2_score,
                             root_mean_squared_error)
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from exploracao import CORES, ROTULOS, estilo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def cam(*p): return os.path.join(RAIZ, *p)

SEMENTE = 42
CORTE_TESTE = "2026-05"


def dados():
    a = pd.read_csv(cam("dados", "produtos_atributos.csv"))
    a["mes"] = a["data"].str[:7]
    a["ano"] = a["data"].str[:4].astype(int)
    a["t"] = (a["ano"] - 2022) * 12 + a["data"].str[5:7].astype(int)
    a["grupo"] = a["faixa"].where(a["faixa"] % 10 == 0)
    a["log_preco"] = np.log(a["preco"])
    return a


def preparo(numericas, categoricas):
    return ColumnTransformer([
        ("num", StandardScaler(), numericas),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=15), categoricas),
    ])


# ---------------------------------------------------------------- 1. preco
def regressao(a):
    num, cat = ["vram", "faixa", "t"], ["marca", "fabricante"]
    d = a.dropna(subset=num + cat + ["preco"])
    treino, teste = d[d.mes <= CORTE_TESTE], d[d.mes > CORTE_TESTE]
    Xtr, ytr = treino[num + cat], treino["log_preco"]
    Xte, yte = teste[num + cat], teste["preco"]
    print(f"[preco] treino {len(treino)} ate {CORTE_TESTE} | teste {len(teste)} depois")

    candidatos = {
        "Média (linha de base)": DummyRegressor(strategy="mean"),
        "Regressão Ridge": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                               random_state=SEMENTE, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(random_state=SEMENTE),
    }
    linhas, ajustados = [], {}
    for nome, est in candidatos.items():
        pipe = Pipeline([("prep", preparo(num, cat)), ("est", est)])
        cv = -cross_val_score(pipe, Xtr, ytr, cv=5,
                              scoring="neg_mean_absolute_error").mean()
        pipe.fit(Xtr, ytr)
        pred = np.exp(pipe.predict(Xte))
        ajustados[nome] = (pipe, pred)
        linhas.append({"modelo": nome, "mae_cv_log": round(cv, 4),
                       "mae_teste": round(mean_absolute_error(yte, pred), 2),
                       "rmse_teste": round(root_mean_squared_error(yte, pred), 2),
                       "mape_teste": round(mean_absolute_percentage_error(yte, pred) * 100, 1),
                       "r2_teste": round(r2_score(yte, pred), 3)})
    com_chip = Pipeline([("prep", preparo(num, cat + ["chip"])),
                         ("est", GradientBoostingRegressor(random_state=SEMENTE))])
    Xtr2, Xte2 = treino[num + cat + ["chip"]], teste[num + cat + ["chip"]]
    cv2 = -cross_val_score(com_chip, Xtr2, ytr, cv=5, scoring="neg_mean_absolute_error").mean()
    com_chip.fit(Xtr2, ytr)
    pred2 = np.exp(com_chip.predict(Xte2))
    linhas.append({"modelo": "Gradient Boosting + chip", "mae_cv_log": round(cv2, 4),
                   "mae_teste": round(mean_absolute_error(yte, pred2), 2),
                   "rmse_teste": round(root_mean_squared_error(yte, pred2), 2),
                   "mape_teste": round(mean_absolute_percentage_error(yte, pred2) * 100, 1),
                   "r2_teste": round(r2_score(yte, pred2), 3)})
    ajustados["Gradient Boosting + chip"] = (com_chip, pred2)

    tab = pd.DataFrame(linhas).sort_values("mae_teste")
    melhor = tab.iloc[0]["modelo"]
    print(tab.to_string(index=False))
    print("melhor:", melhor)
    tab.to_csv(cam("dados", "modelo_preco_metricas.csv"), index=False)

    pipe, pred = ajustados[melhor]
    grafico_dispersao(yte.values, pred, teste["grupo"].values, melhor)
    grafico_importancia(pipe, num, melhor)
    return tab, melhor


def grafico_dispersao(real, pred, grupo, nome):
    fig, ax = plt.subplots(figsize=(6.4, 6.2))
    lim = [min(real.min(), pred.min()) * 0.85, max(real.max(), pred.max()) * 1.15]
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.plot(lim, lim, color="#9a9a9a", lw=1.2, zorder=1)
    for g in sorted({x for x in grupo if x in CORES}):
        m = grupo == g
        ax.scatter(real[m], pred[m], s=20, alpha=0.6, color=CORES[g], edgecolor="white",
                   linewidth=0.4, label=ROTULOS[g], zorder=2)
    fora = ~np.isin(grupo, list(CORES))
    if fora.any():
        ax.scatter(real[fora], pred[fora], s=16, alpha=0.4, color="#9a9a9a",
                   edgecolor="white", linewidth=0.3, label="Outras faixas", zorder=2)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_title(f"Preço previsto e preço real ({nome})")
    ax.set_xlabel("Preço real (R$)"); ax.set_ylabel("Preço previsto (R$)")
    for eixo in (ax.xaxis, ax.yaxis):
        eixo.set_major_formatter(lambda v, _: f"{v:,.0f}".replace(",", "."))
    ax.legend(loc="upper left")
    fig.savefig(cam("figuras", "mod_preco_dispersao.png")); plt.close(fig)
    print("gravado: mod_preco_dispersao.png")


def grafico_importancia(pipe, num, nome):
    est = pipe.named_steps["est"]
    if not hasattr(est, "feature_importances_"):
        return
    nomes = pipe.named_steps["prep"].get_feature_names_out()
    imp = (pd.Series(est.feature_importances_, index=nomes)
             .sort_values(ascending=False).head(10)[::-1])
    bonito = (imp.index.str.replace("num__", "", regex=False)
                 .str.replace("cat__", "", regex=False).str.replace("_", " "))
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ax.barh(range(len(imp)), imp.values, color="#6B3FA0", height=0.62)
    ax.set_yticks(range(len(imp))); ax.set_yticklabels(bonito, fontsize=9.5)
    ax.set_title(f"O que mais pesa na estimativa de preço ({nome})")
    ax.set_xlabel("Importância relativa")
    ax.grid(axis="y", visible=False)
    fig.savefig(cam("figuras", "mod_preco_importancia.png")); plt.close(fig)
    print("gravado: mod_preco_importancia.png")


# ---------------------------------------------------------------- 2. faixa
def classificacao(a):
    num, cat = ["log_preco", "vram", "t"], ["marca"]
    d = a[a["grupo"].isin(CORES)].dropna(subset=num + cat).copy()
    d["grupo"] = d["grupo"].astype(int)
    X, y = d[num + cat], d["grupo"]
    print(f"\n[faixa] {len(d)} anuncios | distribuicao: {y.value_counts().to_dict()}")

    Xtr, Xte, ytr, yte, dtr, dte = train_test_split(
        X, y, d, test_size=0.25, random_state=SEMENTE, stratify=y)

    candidatos = {
        "Classe majoritária (linha de base)": DummyClassifier(strategy="most_frequent"),
        "Regressão logística": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=400, min_samples_leaf=2,
                                                class_weight="balanced_subsample",
                                                random_state=SEMENTE, n_jobs=-1),
    }
    linhas, ajustados = [], {}
    for nome, est in candidatos.items():
        pipe = Pipeline([("prep", preparo(num, cat)), ("est", est)])
        cv = cross_val_score(pipe, Xtr, ytr, cv=5, scoring="f1_macro").mean()
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        ajustados[nome] = (pipe, pred)
        linhas.append({"modelo": nome, "f1_macro_cv": round(cv, 3),
                       "acuracia_teste": round((pred == yte).mean(), 3),
                       "f1_macro_teste": round(f1_score(yte, pred, average="macro"), 3)})
    tab = pd.DataFrame(linhas).sort_values("f1_macro_teste", ascending=False)
    melhor = tab.iloc[0]["modelo"]
    print(tab.to_string(index=False))
    tab.to_csv(cam("dados", "modelo_faixa_metricas.csv"), index=False)

    pipe, pred = ajustados[melhor]
    print(classification_report(yte, pred, target_names=[ROTULOS[g] for g in sorted(y.unique())]))
    grafico_confusao(yte, pred, sorted(y.unique()), melhor)
    divergencias(dte, pred)
    return tab, melhor


def grafico_confusao(yte, pred, classes, nome):
    m = confusion_matrix(yte, pred, labels=classes)
    fig, ax = plt.subplots(figsize=(5.8, 5))
    sns.heatmap(m, annot=True, fmt="d", cmap="Purples", cbar=False, ax=ax,
                linewidths=2, linecolor="white",
                xticklabels=[ROTULOS[c].split(" ")[0] for c in classes],
                yticklabels=[ROTULOS[c].split(" ")[0] for c in classes])
    ax.set_title(f"Faixa pela regra x faixa prevista pelo preço\n({nome})", fontsize=11.5)
    ax.set_xlabel("Prevista pelo modelo"); ax.set_ylabel("Atribuída pela regra")
    fig.savefig(cam("figuras", "mod_faixa_confusao.png")); plt.close(fig)
    print("gravado: mod_faixa_confusao.png")


def divergencias(dte, pred):
    d = dte.copy()
    d["prevista"] = pred
    erradas = d[d["prevista"] != d["grupo"]]
    t = (erradas.groupby(["chip", "grupo", "prevista"])
                .agg(casos=("preco", "size"), preco_mediano=("preco", "median"))
                .reset_index().sort_values("casos", ascending=False))
    t["preco_mediano"] = t["preco_mediano"].round(2)
    t.to_csv(cam("dados", "modelo_faixa_divergencias.csv"), index=False)
    print(f"divergencias: {len(erradas)} de {len(d)} anuncios do teste")
    print(t.head(8).to_string(index=False))


def main():
    estilo()
    a = dados()
    regressao(a)
    classificacao(a)


if __name__ == "__main__":
    main()
