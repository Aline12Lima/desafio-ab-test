# CLAUDE.md — Guia para agentes de IA (Claude Code, Cursor)

Este arquivo instrui assistentes de IA a operar o **cashback-ab-analyzer**.
Leia-o antes de responder a pedidos sobre análise de testes A/B neste projeto.

## O que este projeto faz

Analisa um teste A/B de cashback e recomenda **qual variante escalar para 100% do tráfego**.
Recebe um CSV, calcula métricas de negócio, roda testes estatísticos pareados, decide com
base em significância + materialidade, gera um relatório para gestor (Markdown + HTML) e
registra o resultado numa planilha de acompanhamento (Google Sheets ou CSV).

## Como rodar (comando principal)

O projeto instala um comando de terminal chamado `analyze`:

```bash
analyze <caminho-do-csv> [opções]
```

Opções úteis:
- `--nome "Parceiro X"`     nome do teste (default: nome do arquivo)
- `--descricao "..."`       descrição curta do teste
- `--destino sheets|csv`    onde registrar (default: csv; use `sheets` p/ Google Sheets)
- `--reports-dir <pasta>`   pasta de saída dos relatórios (default: `reports/`)

Os datasets ficam em `data/raw/`.

## Quando o usuário pedir para analisar um teste

1. Se o usuário não indicar o arquivo, liste os CSVs em `data/raw/` e pergunte qual.
2. Rode o comando `analyze` com o arquivo indicado (use `--destino sheets` para registrar
   na planilha, ou `--destino csv` para o fallback local).
3. Resuma em 3–4 linhas: a decisão (ESCALAR / ESCALAR_COM_CAUTELA / INCONCLUSIVO), a
   variante vencedora, a diferença de margem e o p-valor.
4. Confirme onde o relatório foi salvo e que a linha entrou na planilha.

**Não invente números.** Todos os resultados vêm do comando `analyze` (código
determinístico). Se precisar de um valor, rode o comando e leia a saída — nunca estime.

## Como interpretar o resultado (para explicar ao usuário)

- **Métrica de decisão:** margem líquida = comissão − cashback (o lucro do Méliuz).
  Volume (compradores, GMV) é diagnóstico, não objetivo — mais compradores à custa de
  margem menor não é crescimento sustentável.
- **Campeão:** a variante de maior margem total. É comparada, dia a dia (teste pareado),
  contra o 2º colocado — o desafiante mais forte. Vencer dele implica vencer todos.
- **Portão de decisão:** a diferença precisa ser *significativa* (p < 0,05) **e**
  *material* (≥ 5% de margem vs 2º colocado).
- **Decisões possíveis:**
  - `ESCALAR` — real e material: escalar o vencedor a 100%.
  - `ESCALAR_COM_CAUTELA` — real, mas ganho pequeno; avaliar o custo da troca.
  - `INCONCLUSIVO` — sem significância: manter a variante mais barata e estender o teste.
- **Ressalva:** os dados trazem compradores, não usuários expostos por variante. A leitura
  assume divisão de tráfego balanceada entre os grupos (padrão de A/B randomizado).

## Setup (primeira vez)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Para registrar no Google Sheets, crie um `.env` (modelo em `.env.example`) com:
- `SHEET_ID` — id da planilha de acompanhamento
- `GOOGLE_CREDENTIALS` — caminho do JSON da service account (em `secrets/`, fora do Git)

## Arquitetura (resumo)

Pipeline de sentido único, com o núcleo puro isolado das bordas de I/O:

`data_io` (carrega + valida) → `metrics` → `stats` → `decision` (núcleo puro,
determinístico) → `report` / `sheets` (saídas). `formatting` cuida da apresentação
(moeda, %, p-valor); `cli` orquestra tudo num comando único.

Princípio-chave: **o código faz os números (determinístico e auditável); a IA orquestra
e traduz o resultado para linguagem natural.**