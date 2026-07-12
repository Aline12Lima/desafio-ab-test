"""decision.py — núcleo puro: a regra de decisão de negócio.

Junta métricas (metrics) e testes (stats) e responde à pergunta central:
"qual variante escalar para 100%?". Devolve uma Recommendation estruturada.
Sem I/O: quem imprime/salva é a camada de relatório.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .metrics import margem_diaria, metricas_por_grupo
from .stats import ComparacaoPareada, comparar_pareado

# --- Parâmetros da decisão (viveriam em config.py) ---
ALPHA = 0.05          # limite de significância
LIMIAR_PCT = 5.0      # diferença mínima (%) vs 2º colocado para ser "material"


@dataclass
class Recommendation:
    decisao: str                          # ESCALAR | ESCALAR_COM_CAUTELA | INCONCLUSIVO
    vencedor: str | None                  # grupo a escalar (None se inconclusivo)
    justificativa: str
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

    # 3) default seguro em caso de empate: a variante de menor custo
    mais_barata = str(agg["cashback_pct_gmv"].idxmin())

    # 4) o portão: real (significativo) E relevante (material)?
    significativo = decisiva.p_wilcoxon < alpha
    material = abs(decisiva.dif_pct) >= limiar_pct

    if significativo and material:
        decisao, vencedor = "ESCALAR", campeao
        just = (
            f"{campeao} tem a maior margem total e supera {vice} em "
            f"{decisiva.dif_pct:+.0f}% ao dia (p={decisiva.p_wilcoxon:.1e}, "
            f"d de Cohen={decisiva.d_cohen:.2f}). Diferença real e material — "
            f"escalar {campeao} a 100%."
        )
    elif significativo and not material:
        decisao, vencedor = "ESCALAR_COM_CAUTELA", campeao
        just = (
            f"{campeao} vence {vice} de forma estatisticamente real, mas por "
            f"margem modesta ({decisiva.dif_pct:+.0f}%). Escalar é defensável, "
            f"porém o ganho pode não compensar o custo da troca."
        )
    else:
        decisao, vencedor = "INCONCLUSIVO", None
        just = (
            f"A diferença entre {campeao} e {vice} não é estatisticamente "
            f"significativa (p={decisiva.p_wilcoxon:.2f}). Manter a variante de "
            f"menor custo ({mais_barata}) e estender o teste para ganhar poder."
        )

    return Recommendation(
        decisao, vencedor, just, campeao, vice, decisiva,
        mais_barata, ranking.to_dict(), todas,
    )