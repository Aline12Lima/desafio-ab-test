"""decision.py — núcleo puro: a regra de decisão de negócio.

Junta métricas (metrics) e testes (stats) e responde à pergunta central:
"qual variante escalar para 100%?". Devolve uma Recommendation estruturada.
Não gera texto para humano nem formata números — isso é papel da apresentação.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .metrics import margem_diaria, metricas_por_grupo
from .stats import ComparacaoPareada, comparar_pareado

ALPHA = 0.05          # limite de significância
LIMIAR_PCT = 5.0      # diferença mínima (%) vs 2º colocado para ser "material"


@dataclass
class Recommendation:
    decisao: str                          # ESCALAR | ESCALAR_COM_CAUTELA | INCONCLUSIVO
    vencedor: str | None                  # grupo a escalar (None se inconclusivo)
    campeao: str                          # maior margem total
    vice: str                             # 2º colocado (desafiante mais forte)
    comparacao_decisiva: ComparacaoPareada
    variante_mais_barata: str             # menor cashback %GMV (default seguro)
    margem_total: dict[str, float]
    todas_comparacoes: list[ComparacaoPareada]


def decidir(df: pd.DataFrame, alpha: float = ALPHA, limiar_pct: float = LIMIAR_PCT) -> Recommendation:
    agg = metricas_por_grupo(df)
    md = margem_diaria(df)

    # 1) ranqueia por margem total; campeão = topo, vice = 2º (desafiante mais forte)
    ranking = agg["margem"].sort_values(ascending=False)
    campeao, vice = ranking.index[0], ranking.index[1]

    # 2) comparação decisiva (se o campeão vence o vice, vence todos) + as demais
    decisiva = comparar_pareado(md, campeao, vice)
    todas = [comparar_pareado(md, campeao, g) for g in ranking.index[1:]]

    # 3) default seguro: a variante de menor custo
    mais_barata = str(agg["cashback_pct_gmv"].idxmin())

    # 4) o portão: real (significativo) E relevante (material)?
    significativo = decisiva.p_wilcoxon < alpha
    material = abs(decisiva.dif_pct) >= limiar_pct

    if significativo and material:
        decisao, vencedor = "ESCALAR", campeao
    elif significativo and not material:
        decisao, vencedor = "ESCALAR_COM_CAUTELA", campeao
    else:
        decisao, vencedor = "INCONCLUSIVO", None

    return Recommendation(
        decisao, vencedor, campeao, vice, decisiva,
        mais_barata, ranking.to_dict(), todas,
    )