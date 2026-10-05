# Publicar a API no Render

A API é um serviço Python (FastAPI) que lê os CSV de `dados/`. Não precisa de banco de dados
nem de variável secreta.

## Passo a passo

1. Criar conta em <https://render.com> com a conta do GitHub (a mesma que tem o repositório).
2. No painel: **New → Web Service → Build and deploy from a Git repository**.
3. Autorizar o Render a ler o repositório `Dhstefanoski/ipca-placas-de-video`. Como ele é
   privado, o Render pede permissão explícita; pode liberar só esse repositório.
4. O Render lê o `render.yaml` e preenche sozinho:

   | Campo | Valor |
   |---|---|
   | Runtime | Python |
   | Build command | `pip install -r requirements-api.txt` |
   | Start command | `uvicorn src.api:app --host 0.0.0.0 --port $PORT` |
   | Plan | Free |

5. Clicar em **Create Web Service**. A primeira publicação leva uns 3 a 5 minutos.
6. A API fica em `https://ipca-placas-api.onrender.com` (o nome pode mudar se já estiver em uso).
   A documentação interativa fica em `/docs`.

## Como testar depois de publicar

```
https://SEU-ENDERECO.onrender.com/docs
https://SEU-ENDERECO.onrender.com/indices?inicio=2026-01
https://SEU-ENDERECO.onrender.com/comparacao?inicio=2023-01
https://SEU-ENDERECO.onrender.com/produtos?busca=5060
```

## O que esperar do plano gratuito

- **O serviço dorme depois de 15 minutos sem acesso.** A primeira chamada depois disso demora
  de 40 a 60 segundos. Nas seguintes responde normal.
  **Na apresentação, abrir o `/docs` um minuto antes.**
- **Cada commit no `main` republica a API.** Como o robô da coleta comita todo dia, a API é
  atualizada sozinha com os dados novos. Se isso incomodar, dá para desligar em
  Settings → Auto-Deploy.
- 750 horas por mês de uso, bem mais do que este projeto precisa.

## Por que não Netlify

O Netlify hospeda site estático e funções em JavaScript/TypeScript ou Go. Não executa um
servidor Python, então não roda FastAPI. Serviria para uma alternativa diferente: gerar os
dados como JSON estático no GitHub Actions e servir os arquivos prontos — mais robusto, porém
sem os parâmetros de consulta e sem o `/docs`.

## Quando o modelo de previsão ficar pronto

Acrescentar o endpoint em `src/api.py`, comitar e dar push. O Render republica sozinho; não há
nada a refazer aqui.
