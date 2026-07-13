# Relatório de Teste A/B — Parceiro C

**Período:** 01/07/2011 a 14/08/2011  ·  **Variantes:** 2  ·  **Gerado em:** 13/07/2026 10:58

---

## Decisão: ESCALAR

**Escalar Grupo 1 para 100% do tráfego**

Grupo 1 tem a maior margem total e supera Grupo 2 em >999% ao dia (p < 0,001, efeito grande). Diferença real e material — escalar Grupo 1 a 100%.

---

## Métricas por variante

| Variante | Cashback (% GMV) | Compradores | GMV | Margem total | Margem/comprador |
|---|---|---|---|---|---|
| Grupo 1 ◄ | 5,0% | 4.549 | R$ 1.738.460 | R$ 34.769 | R$ 7,64 |
| Grupo 2 | 7,0% | 4.522 | R$ 1.685.235 | R$ 0 | R$ 0,00 |

_A variante recomendada está marcada com ◄._

---

## Comparação decisiva — Grupo 1 vs Grupo 2

O confronto contra o 2º colocado (o desafiante mais forte) decide o teste: vencer aqui implica vencer todos os demais.

- **Diferença de margem:** R$ 773/dia (>999% vs Grupo 2)
- **Significância:** p < 0,001 — Wilcoxon pareado, 45 dias
- **Intervalo de confiança 95%:** R$ 713 a R$ 833 por dia
- **Tamanho de efeito:** grande (d de Cohen = 3,87)

---

## Como ler / ressalvas

- **Métrica de decisão:** margem líquida (comissão − cashback). Volume (compradores, GMV) é diagnóstico, não objetivo — mais compradores à custa de margem menor não é crescimento sustentável.
- **Premissa:** os dados trazem compradores, não usuários expostos por variante. A leitura assume divisão de tráfego balanceada entre os grupos (padrão de A/B randomizado).
- **Materialidade:** exige-se diferença mínima de 5% vs 2º colocado para recomendar a troca; abaixo disso, o resultado é sinalizado como ganho modesto.