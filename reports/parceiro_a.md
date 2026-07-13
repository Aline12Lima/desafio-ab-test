# Relatório de Teste A/B — Parceiro A

**Período:** 01/01/2011 a 02/04/2011  ·  **Variantes:** 3  ·  **Gerado em:** 13/07/2026 10:58

---

## Decisão: ESCALAR

**Escalar Grupo 1 para 100% do tráfego**

Grupo 1 tem a maior margem total e supera Grupo 2 em +13% ao dia (p < 0,001, efeito pequeno). Diferença real e material — escalar Grupo 1 a 100%.

---

## Métricas por variante

| Variante | Cashback (% GMV) | Compradores | GMV | Margem total | Margem/comprador |
|---|---|---|---|---|---|
| Grupo 1 ◄ | 4,2% | 9.633 | R$ 5.605.173 | R$ 404.711 | R$ 42,01 |
| Grupo 2 | 5,8% | 10.814 | R$ 6.423.096 | R$ 357.519 | R$ 33,06 |
| Grupo 3 | 7,4% | 11.410 | R$ 6.785.856 | R$ 264.287 | R$ 23,16 |

_A variante recomendada está marcada com ◄._

---

## Comparação decisiva — Grupo 1 vs Grupo 2

O confronto contra o 2º colocado (o desafiante mais forte) decide o teste: vencer aqui implica vencer todos os demais.

- **Diferença de margem:** R$ 513/dia (+13% vs Grupo 2)
- **Significância:** p < 0,001 — Wilcoxon pareado, 92 dias
- **Intervalo de confiança 95%:** R$ 282 a R$ 744 por dia
- **Tamanho de efeito:** pequeno (d de Cohen = 0,46)

---

## Como ler / ressalvas

- **Métrica de decisão:** margem líquida (comissão − cashback). Volume (compradores, GMV) é diagnóstico, não objetivo — mais compradores à custa de margem menor não é crescimento sustentável.
- **Premissa:** os dados trazem compradores, não usuários expostos por variante. A leitura assume divisão de tráfego balanceada entre os grupos (padrão de A/B randomizado).
- **Materialidade:** exige-se diferença mínima de 5% vs 2º colocado para recomendar a troca; abaixo disso, o resultado é sinalizado como ganho modesto.