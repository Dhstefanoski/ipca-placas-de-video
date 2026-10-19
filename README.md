# O IPCA reflete o preço real pago por quem compra tecnologia?

Trabalho da disciplina de Mineração de Dados, feito por Davi H. Stefanoski, Enon Demori T. M. e
Leonardo C. Cherini.

O IPCA aplica ajuste por qualidade aos bens de tecnologia. Se o produto novo entrega mais
desempenho pelo mesmo valor, parte da variação deixa de contar como inflação. Quem compra,
porém, paga o preço de etiqueta. A ideia aqui foi medir o tamanho dessa diferença, usando placas
de vídeo como caso de estudo.

API publicada: https://ipca-placas-de-video.onrender.com/docs.

## O que encontramos

De 2023 a 2026 o preço mediano da placa intermediária (RTX 3060, 4060, 5060 e equivalentes AMD)
subiu 18,9%, de R$ 2.524 para R$ 3.000. No mesmo período o IPCA de computadores subiu 8,4% e o
IPCA geral, 14,1%.

![Placa intermediária x IPCA](figuras/medianas_faixa.png)

Sobre essa base treinamos dois modelos. Um estima o preço de um anúncio a partir das
características da placa, e erra em média R$ 798, com R² de 0,868. O outro faz o caminho
inverso: tenta descobrir a faixa de mercado olhando só o preço e os atributos técnicos, sem ver
o nome do anúncio, e acerta 94% das vezes.

O segundo é mais interessante do que parece. Se o preço basta para reconstruir a faixa, é
porque a classificação que adotamos corresponde a uma divisão real do mercado, e não a um
rótulo que inventamos. E onde ele erra, aponta placas cuja posição no catálogo não combina com
o preço praticado, como a RTX 5050 sendo vendida a valor de intermediária.

Os números completos, as variantes de método e as limitações estão no [RELATORIO.md](RELATORIO.md).

## De onde vêm os dados

| Fonte | O que traz | Tamanho |
|---|---|---|
| Kabum, via Internet Archive | Histórico de preços da página de placas de vídeo | 2.160 preços, 84 capturas, 43 meses |
| Kabum, coleta diária | Preços correntes, desde 13/09/2026 | 15.147 preços, 36 dias |
| IBGE / SIDRA, tabela 7060 | IPCA geral e subitem "Computador pessoal" | 54 meses |
| Banco Central, SGS série 1 | Dólar PTAX diário | 1.139 cotações |

Depois da limpeza sobram 2.925 anúncios com chip identificado, em 70 modelos distintos.

## Estrutura

```
src/
  coleta_acervo.py     histórico de preços no Internet Archive
  retenta_acervo.py    repete as capturas que falharam
  coleta_diaria.py     preços do dia na Kabum
  coleta_oficial.py    IPCA e dólar
  hedonico.py          junta as fontes, extrai chip e faixa, regressão de verificação
  medianas.py          mediana por faixa comparada ao IPCA (método principal)
  exploracao.py        gráficos exploratórios
  modelo.py            modelos de preço e de faixa
  graficos.py          gráficos da regressão
  api.py               API de consulta
dados/                 bases coletadas e resultados
figuras/               gráficos
.github/workflows/     coleta diária e análise semanal
```

## Como rodar

```bash
pip install -r requirements.txt

python src/coleta_acervo.py     # histórico, leva uns 10 minutos
python src/retenta_acervo.py    # repete as capturas que falharam
python src/coleta_oficial.py    # IPCA e dólar
python src/hedonico.py          # atributos e regressão
python src/medianas.py          # método principal
python src/exploracao.py        # gráficos exploratórios
python src/modelo.py            # modelos de aprendizado de máquina
python src/graficos.py          # gráficos da regressão

uvicorn src.api:app --reload    # API em http://127.0.0.1:8000/docs
```

## Automação

A coleta diária roda quatro vezes por dia no GitHub Actions e grava os preços daquele dia. A
análise semanal roda toda segunda, refaz tudo e versiona gráficos e resultados. As duas comitam
no próprio repositório, então a base cresce sozinha. Para publicar a API, ver [DEPLOY.md](DEPLOY.md).

## Limitações

Os dados vêm de uma loja só, a Kabum, porque Terabyte e Pichau bloqueiam a coleta. Não existem
capturas de fevereiro a maio de 2023, e o dia 20/09/2026 ficou sem dado por um bloqueio
temporário. Apenas a faixa intermediária reúne anúncios suficientes em todos os anos. E o
subitem do IPCA cobre computadores completos, não placas de vídeo isoladas, de modo que a
comparação é de tendência e não de valor exato.
