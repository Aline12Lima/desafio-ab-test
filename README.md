<div align="center">

# Cashback A/B Analyzer — Teste Técnico Méliuz

**Uma solução reutilizável que analisa testes A/B de cashback e recomenda qual variante escalar para 100% do tráfego.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![CI](https://github.com/Aline12Lima/desafio-ab-test/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

📊 **[Planilha de acompanhamento (Google Sheets)](https://docs.google.com/spreadsheets/d/11lOqNc4Ov6bZlBSK5BQ2aV7m3NwThW3AqO4TUm5dwfQ/edit?usp=sharing)**

</div>

---

## O que essa ferramenta resolve

O time de Growth da Méliuz roda dezenas de testes A/B de cashback por mês. Hoje, cada análise leva de 2 a 4 horas e depende de quem está olhando — o que gera inconsistência e vira gargalo.

Esta ferramenta automatiza esse processo: recebe o CSV de um teste A/B, valida os dados (robusta a formatos ruins), calcula as métricas de negócio, roda testes estatísticos, toma uma decisão acionável e entrega o resultado em relatório para gestor (Markdown + HTML) e numa planilha de acompanhamento (Google Sheets, com fallback em CSV). A mesma solução processa qualquer teste novo **sem alteração de código** — basta apontar o novo arquivo.

---

## O planejamento

**Entendimento do negócio.** O primeiro passo foi compreender o produto da Méliuz e o contexto do problema. A Méliuz é uma plataforma de cashback: o usuário recebe de volta parte do valor gasto em compras nas lojas parceiras, e a Méliuz recebe uma comissão do parceiro por venda. O equilíbrio entre número de compradores, volume de vendas (GMV) e **margem** é o que sustenta o negócio.

**O problema.** O desafio não é só analisar um conjunto de dados, mas construir uma solução **reutilizável** que automatize um processo hoje manual (2 a 4 horas por teste, gerando inconsistência e gargalo).

**A estratégia.** Depois de mapear os requisitos, optei por uma **arquitetura modular**, com uma responsabilidade por etapa: leitura de dados, validação, cálculo de métricas, análise estatística, decisão, geração de relatórios, registro do resultado e testes. O objetivo final é transformar uma análise de horas num processo de segundos, respondendo à pergunta central: **qual variante escalar?**

---

## Resultados

### Pergunta central

> Dado esse teste A/B, qual variante de cashback deve ser escalada para 100% do tráfego?

A resposta **não** pode se basear apenas em qual grupo gerou mais compradores ou maior volume de vendas. O objetivo é identificar a variante que gera o melhor resultado para o negócio, equilibrando crescimento e rentabilidade.

### Decisão nos três parceiros

| Parceiro | Decisão | Justificativa |
|---|---|---|
| **A** | Escalar **Grupo 1** | Embora o Grupo 3 tenha mais compradores, o cashback maior derrubou a margem. O Grupo 1 (menor cashback) teve o melhor equilíbrio entre receita e custo — maior lucro para a Méliuz. |
| **B** | Escalar **Grupo 1** | O Grupo 1 teve margem líquida muito superior, com diferença estatisticamente significativa e material. Aqui, cashback maior foi lose-lose: menos compradores **e** menos margem. |
| **C** | Escalar **Grupo 1** | O Grupo 2 zerou a margem (cashback = comissão) sem trazer compradores a mais. O Grupo 1 mantém a rentabilidade sem precisar aumentar o cashback. |

### A armadilha (o coração da análise)

No Parceiro A, subir o cashback **realmente** traz mais compradores e mais GMV. Quem olhar só "conversão" ou "vendas totais" escolheria o Grupo 3 — e estaria escolhendo a pior opção para o negócio, porque a margem por comprador desaba e a margem total cai. Volume que não se paga não é crescimento: é subsídio. Por isso a métrica de decisão é a **margem**, não o volume.

---

## Metodologia da decisão

A ferramenta decide combinando critérios **financeiros** e **estatísticos**, aproximando o processo de uma equipe de Growth em experimentação.

**1. Métrica de decisão — margem líquida.**
```
Margem = Comissão − Cashback
```
É o retorno financeiro efetivo da Méliuz. Número de compradores e GMV entram como indicadores de apoio (diagnóstico), pois não refletem diretamente a lucratividade.

**2. Comparação pareada, dia a dia.** Dentro de cada parceiro, os mesmos dias aparecem em todos os grupos, então comparo grupo contra grupo **no mesmo dia** (teste pareado). Isso cancela o efeito de dia da semana e sazonalidade, dando mais poder para detectar diferenças reais. O campeão (maior margem total) é comparado contra o 2º colocado — o desafiante mais forte; vencer dele implica vencer todos.

**3. O portão de decisão — real E relevante.** Uma diferença só vira recomendação se for:
- **Significativa** (teste de Wilcoxon pareado, com t pareado como checagem cruzada; p < 0,05), e
- **Material** (diferença de margem ≥ 5% vs o 2º colocado).

Reporto também o **tamanho de efeito** (d de Cohen) e o **intervalo de confiança 95%**, porque significância diz "é real" e o tamanho do efeito diz "vale agir".

**4. As três saídas possíveis:**
- **ESCALAR** — diferença real e material: escalar o vencedor a 100%.
- **ESCALAR COM CAUTELA** — real, mas ganho pequeno; avaliar o custo da troca.
- **INCONCLUSIVO** — sem significância: manter a variante de menor custo e estender o teste.

O ramo INCONCLUSIVO existe de propósito, mesmo nenhum dos três datasets caindo nele: prova que a solução é uma ferramenta de análise honesta, que não "chuta" um vencedor quando não há diferença.

---

## Arquitetura

A solução é um **pipeline de sentido único**, com o núcleo de decisão (puro e determinístico) isolado das bordas de entrada/saída:

```
CSV → data_io → metrics → stats → decision → report / sheets
      (borda)   └──── núcleo puro ────┘        (bordas)
```

- **`data_io`** — única porta de entrada: carrega o CSV, faz o parse de `R$` no padrão brasileiro e valida contra o schema (é onde mora a robustez a dados ruins).
- **`metrics`** — métricas de negócio por grupo e a série diária de margem.
- **`stats`** — testes pareados, intervalo de confiança e tamanho de efeito.
- **`decision`** — a regra de decisão (campeão, portão, saída). Núcleo puro: não faz I/O nem formata texto.
- **`formatting`** — camada de apresentação (moeda, %, p-valor) em um lugar só.
- **`report`** — gera o relatório do gestor em Markdown (base) e HTML (derivado).
- **`sheets` / `sheets_google`** — registra o teste em CSV (fallback) ou Google Sheets (via service account).
- **`cli`** — orquestra tudo num comando único (`analyze`), com Typer.

**Princípio-chave:** o código determinístico faz os números (auditáveis e reproduzíveis); a camada de IA orquestra e traduz o resultado para linguagem natural.

### Camada AI-Native (`CLAUDE.md`)

O arquivo `CLAUDE.md` instrui assistentes como o Claude Code a operar a solução em linguagem natural. Um colaborador pode pedir *"analisa o teste do Parceiro C e registra na planilha"* e o assistente roda o comando `analyze`, resume a decisão e confirma o registro — sem tocar no código. É o que torna a solução verdadeiramente reutilizável.

---

## Stack técnico

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Dados | pandas |
| Estatística | scipy |
| Relatórios | jinja2, markdown |
| Google Sheets | gspread, google-auth |
| CLI | typer |
| Config | python-dotenv |
| Testes / qualidade | pytest, ruff, mypy |
| CI | GitHub Actions |

---

## Como rodar

**Pré-requisitos:** Python 3.10+.

```bash
# 1. clone o repositório e entre na pasta
git clone https://github.com/Aline12Lima/desafio-ab-test.git
cd desafio-ab-test

# 2. crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. instale o projeto e as dependências
pip install -e .
```

**Analisar um teste** (o comando é o mesmo para qualquer dataset — só troca o arquivo):

```bash
analyze data/raw/dataset_01_parceiroA.csv --nome "Parceiro A" --destino csv
```

Opções úteis: `--nome`, `--descricao`, `--destino csv|sheets`, `--reports-dir`. Rode `analyze --help` para a lista completa.

**Registrar no Google Sheets** (opcional): crie um `.env` a partir do `.env.example` com `SHEET_ID` e `GOOGLE_CREDENTIALS` (caminho do JSON da service account, guardado em `secrets/`, fora do Git) e use `--destino sheets`.

**Via linguagem natural:** abra o projeto no Claude Code e peça, por exemplo, *"analisa o teste do Parceiro B e registra na planilha"*.

---

## Como testar

```bash
pip install -e ".[dev]"    # instala pytest, ruff e mypy
pytest
```

A suíte cobre as peças críticas: o parser de `R$` e a validação (`test_io`), as fórmulas e a divisão por zero (`test_metrics`), e a regra de decisão com datasets sintéticos de vencedor conhecido (`test_decision`). Os testes rodam automaticamente a cada push via GitHub Actions (badge de CI no topo).

---

## Decisões de design e trade-offs

- **Margem como métrica de decisão** — e não GMV ou nº de compradores. Volume que reduz a margem não é crescimento sustentável.
- **Fail-fast na validação** — dados ruins abortam com mensagem clara, em vez de seguir com números silenciosamente corrompidos. Para uma ferramenta que embasa decisão de negócio, abortar é mais seguro que "limpar e continuar".
- **Limiar de materialidade de 5%** — é uma escolha de negócio (trocar a variante tem custo operacional), exposta como parâmetro, não como número mágico no código.
- **Núcleo puro vs. bordas** — o cálculo e a decisão são funções puras e testáveis; só as bordas (`data_io`, `report`, `sheets`) tocam disco/rede. Isso torna os números auditáveis.
- **CSV de acompanhamento fora do Git** — é um artefato gerado (fallback); a planilha oficial é a do Google Sheets. Versiona-se a capacidade de gerar, não o arquivo gerado.
- **YAGNI** — módulos que ficariam vazios (config/schema) foram removidos; as constantes vivem em quem as usa.

---

## Limitações e próximos passos

- **Compradores, não usuários expostos.** Os dados trazem compradores, não o total de usuários expostos por variante. A leitura assume divisão de tráfego balanceada entre os grupos (padrão de A/B randomizado). Com o total de expostos, seria possível calcular a taxa de conversão real.
- **Sem LTV / retenção.** A decisão otimiza a margem do período do teste. Um cashback maior pode fazer sentido estrategicamente se aumentar retenção/LTV — algo que estes dados não capturam.
- **Correção de múltiplas comparações.** Com 3 grupos há comparações par a par; uma correção (Holm/Bonferroni) tornaria o critério mais rigoroso. Aqui os p-valores são tão baixos que não alteraria a decisão, mas é uma melhoria natural.
- **Próximos passos:** dashboard interativo, suporte a mais de um teste por execução (lote) e alertas automáticos.

---

## Estrutura de pastas

```
cashback-ab-analyzer/
├── README.md
├── CLAUDE.md                  # camada AI-native
├── pyproject.toml             # dependências + comando `analyze`
├── .env.example
├── .gitignore
├── .github/workflows/ci.yml   # integração contínua
├── data/raw/                  # os 3 datasets (parceiros A, B, C)
├── reports/                   # relatórios gerados (md + html)
├── src/cashback_ab/
│   ├── data_io.py             # carrega, faz parse de R$ e valida
│   ├── metrics.py             # métricas por grupo e série diária
│   ├── stats.py               # testes pareados, IC, tamanho de efeito
│   ├── decision.py            # regra de decisão (núcleo puro)
│   ├── formatting.py          # apresentação (moeda, %, p-valor)
│   ├── report.py              # relatório md + html
│   ├── sheets.py              # registro (interface)
│   ├── sheets_google.py       # registro no Google Sheets
│   └── cli.py                 # orquestração (Typer)
├── templates/report.md.j2
└── tests/                     # test_io, test_metrics, test_decision
```

---

<div align="center">

Desenvolvido por **Aline Lima** · Teste técnico Méliuz — Estágio de Growth (IA e Automação)

</div>