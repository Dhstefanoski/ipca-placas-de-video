# O IPCA mede a inflação de quem compra tecnologia?

Relatório técnico do projeto. Placas de vídeo como caso de estudo, Kabum como fonte de preço,
IPCA e dólar como referência.

---

## Resultado em poucas linhas

- **De 2023 a 2026, o preço mediano da placa intermediária (xx60) subiu 16,5%**
  (R$ 2.524 → R$ 2.941). No mesmo período o IPCA de computadores subiu 8,4% e o IPCA geral 14,1%.
  A placa subiu **o dobro do IPCA de computadores e um pouco acima da inflação geral**.
- **O preço não anda junto com o índice, anda em ciclo próprio.** De 2022 a 2024 a mediana da
  xx60 caiu 29,6% (R$ 3.176 → R$ 2.235), no fim da escassez de placas. De 2024 a 2026 subiu 31,6%
  (R$ 2.235 → R$ 2.941). O IPCA não tem esse vai e vem.
- **O número exato depende de escolhas de método.** Entre 2023 e 2026, a variação da xx60 vai de
  +16,5% a +35,8% conforme a definição de faixa e o filtro de vendedor. Se o ponto de partida for
  2022, ela fica em −7,4%. A direção "acima do IPCA de computadores" aparece em todas as versões
  que começam em 2023.
- **Só a faixa intermediária tem dados suficientes.** As faixas de entrada (xx50) e mais forte
  (xx70) têm menos de 30 preços em 2023 e não sustentam conclusão.

A hipótese do projeto, de que o preço das placas não acompanha a inflação oficial, se confirma.
A versão "ficou muito mais caro que a inflação" não se sustenta: fica acima do IPCA de
computadores, mas perto da inflação geral.

---

## 1. Dados

| Base | Origem | Tamanho |
|---|---|---|
| `dados/precos_acervo.csv` | Página de placas de vídeo da Kabum no Internet Archive | 84 capturas, 2.160 preços, 43 meses (mar/2022–ago/2026) |
| `dados/precos_diarios.csv` | Coleta ao vivo na Kabum | 300 produtos por dia, iniciada em 13/09/2026 |
| `dados/ipca.csv` | IBGE/SIDRA, tabela 7060 | IPCA geral e "Computador pessoal" (47641) |
| `dados/dolar.csv` | Banco Central, SGS série 1 | 1.139 cotações diárias |

**Limpeza:**
- 55 preços fora de R$ 200–60.000 descartados.
- 26 anúncios sem chip ou memória identificáveis descartados, na maioria acessórios.
- 2.079 preços com chip identificado.
- Dentro de cada ano e faixa, preços fora de 1,5 intervalo interquartil removidos: 40 de 1.313
  na análise principal.

**Conferência das faixas:** os 52 chips encontrados foram revisados um a um
(`dados/conferencia_faixas.csv`). Um erro foi corrigido: a Intel Arc B580 estava na faixa 80
e é intermediária (60). A conferência nome a nome, anúncio por anúncio, ainda não foi feita.

## 2. Método principal: mediana por faixa

1. **Chip:** extraído do nome do anúncio (`src/hedonico.py`, função `atributos`).
2. **Faixa:** definida pelos dois últimos números do modelo. xx50 é entrada, xx60
   intermediária, xx70 mais forte. Na versão principal entram só os modelos base:
   RTX 3060, 4060 e 5060, RX 6600 e 7600.
3. **Mediana:** calculada por ano e faixa, depois de remover os preços fora do padrão.
4. **Comparação com o IPCA:** para cada ano, a média do IPCA nos meses em que há captura de
   preço, e a variação de um ano para o outro.

Script: `src/medianas.py`.

**Por que mediana e não média:** um anúncio com preço absurdo puxa a média e quase não mexe na
mediana.

**Por que comparar por faixa:** as placas à venda trocam de geração. Em 2022 a loja vendia
RTX 30, em 2026 vende RTX 50. Comparar o preço médio da loja inteira mediria troca de produto,
não variação de preço.

## 3. Resultados

![Mediana da faixa xx60 x IPCA](figuras/medianas_faixa.png)

### Preço mediano por ano

| Ano | xx50 | xx60 | xx70 |
|---|---|---|---|
| 2022 | R$ 2.118 (n=58) | R$ 3.176 (n=88) | R$ 5.412 (n=7) |
| 2023 | R$ 1.222 (n=23) | **R$ 2.524 (n=87)** | R$ 4.575 (n=7) |
| 2024 | R$ 1.386 (n=41) | R$ 2.235 (n=185) | sem dado |
| 2025 | R$ 1.451 (n=28) | R$ 2.353 (n=253) | R$ 5.294 (n=38) |
| 2026 (jan–ago) | R$ 2.353 (n=134) | **R$ 2.941 (n=263)** | R$ 7.059 (n=61) |

n = número de preços no ano. As medianas com n menor que 30 são pouco confiáveis.

### Variação de 2023 a 2026

| Série | Variação |
|---|---|
| **Placa intermediária (xx60)** | **+16,5%** |
| IPCA computador pessoal | +8,4% |
| IPCA geral | +14,1% |
| Placa de entrada (xx50) | +92,5% (poucos dados em 2023) |
| Placa mais forte (xx70) | +54,3% (poucos dados em 2023) |

## 4. Sensibilidade

Variação da mediana até 2026, conforme a escolha de método (`dados/medianas_sensibilidade.csv`):

| Versão | xx60 | IPCA computador | IPCA geral |
|---|---|---|---|
| **Principal** (modelos base, desde 2023) | **+16,5%** | +8,4% | +14,1% |
| Sem remover preços fora do padrão | +17,4% | +8,4% | +14,1% |
| Incluindo variantes Ti/XT/Super na faixa | +35,8% | +8,4% | +14,1% |
| Só produtos vendidos pela própria Kabum | +31,1% | +8,4% | +14,1% |
| Começando em 2022 | −7,4% | −2,9% | +18,6% |

**Leitura:**
- **Remover preços fora do padrão quase não muda nada.** Bom sinal: o resultado não depende de
  meia dúzia de anúncios estranhos.
- **Incluir as variantes Ti dobra a subida**, porque em 2026 a prateleira está cheia de
  RTX 5060 Ti e RX 9060 XT, placas mais caras dentro da mesma faixa. A versão principal fica sem
  elas para comparar sempre o mesmo tipo de placa.
- **O ano de partida muda a conclusão.** 2022 foi o fim de um período de preços muito altos.
  Começando nele, a placa fica abaixo da inflação; começando em 2023, fica acima. É exatamente o
  "ciclo próprio" da hipótese.

## 5. Checagem por regressão

Como segunda opinião, os preços foram modelados por regressão (`src/hedonico.py`), controlando
chip, memória e fabricante. De jan/2023 a ago/2026:

| Medida | Variação | IC 95% |
|---|---|---|
| Mesmo chip | −2,8% | −7,7 a +2,4 |
| Mesma faixa, qualquer geração | +42,1% | +31,8 a +53,2 |
| IPCA computador pessoal | +8,9% | |
| IPCA geral | +17,3% | |

A regressão aponta na mesma direção da mediana: **a mesma faixa ficou mais cara que o IPCA,
e o mesmo chip ficou estável.** O número da regressão (+42%) fica perto da versão da mediana com
variantes Ti (+36%), porque a regressão também inclui essas placas. (Os valores do IPCA diferem
um pouco dos da seção 3 porque aqui a comparação é mês contra mês, e lá é média anual.)

Gráficos: `figuras/indices_periodo_completo.png` e `figuras/indices_desde_2023.png`.

## 6. Limitações

- **Uma loja.** O resultado descreve a Kabum, não o mercado inteiro. Pichau e Terabyte
  bloquearam a coleta.
- **Primeira página da categoria.** Cada captura antiga traz 20 produtos, na ordem padrão do
  site. Não é uma amostra aleatória.
- **Só a faixa xx60 tem dados suficientes** em todos os anos.
- **2026 vai só até agosto**, e 2022 começa em março.
- **Meses sem captura:** não há cópias de fevereiro a maio de 2023.
- **Produtos esgotados não aparecem.** O histórico só guarda placas disponíveis. Não dá para
  medir o efeito de produtos que saíram do catálogo.
- **O IPCA de computadores cobre computadores inteiros**, não placas de vídeo. A comparação é
  de tendência, não de valor exato.

## 7. O que não foi feito

- **Modelo de previsão de preço.** Precisa de uns 90 dias de coleta diária. O coletor existe
  (`src/coleta_diaria.py`) e o agendamento está pronto (`.github/workflows/coleta_diaria.yml`),
  mas só roda sozinho com o projeto no GitHub.
- **API publicada.** A API existe e funciona localmente, mas não está na internet.
- **Conferência manual nome a nome.** A revisão foi por chip, não anúncio por anúncio.

## 8. Como reproduzir

```bash
pip install -r requirements.txt

python src/coleta_acervo.py      # histórico do Internet Archive (~10 min)
python src/retenta_acervo.py     # repete as capturas que falharam
python src/coleta_oficial.py     # IPCA e dólar
python src/hedonico.py           # extrai chip e faixa + regressão (gera produtos_atributos.csv)
python src/medianas.py           # MÉTODO PRINCIPAL: mediana por faixa, sensibilidade, gráfico
python src/graficos.py           # gráficos da regressão
python src/coleta_diaria.py      # coleta do dia; agendar diariamente

uvicorn src.api:app --reload     # API em http://127.0.0.1:8000/docs
```
