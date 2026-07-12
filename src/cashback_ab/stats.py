"""stats.py — núcleo puro: significância e tamanho de efeito.

Recebe uma tabela dia × grupo (ex.: a margem diária vinda de metrics)
e compara grupos com teste PAREADO. Sem I/O, sem regra de negócio:
responde "a diferença é real?" e "de que tamanho?", nada além disso. Sem tomar decisão. 
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ComparacaoPareada:
    campeao: str
    desafiante: str
    n_dias: int
    media_campeao: float
    media_desafiante: float
    dif_media: float          # média das diferenças diárias (campeão - desafiante)
    dif_pct: float            # essa diferença como % do desafiante  -> materialidade
    p_wilcoxon: float         # teste principal (não-paramétrico)
    p_t_pareado: float        # checagem cruzada (paramétrico)
    ic95: tuple[float, float] # intervalo de confiança 95% da dif média
    d_cohen: float            # tamanho de efeito padronizado (d pareado)


def comparar_pareado(tabela: pd.DataFrame, campeao: str, desafiante: str) -> ComparacaoPareada:
    """Compara duas colunas (grupos) dia a dia, de forma pareada."""
    par = tabela[[campeao, desafiante]].dropna()   # só dias com ambos presentes
    a = par[campeao].to_numpy()
    b = par[desafiante].to_numpy()
    n = len(par)
    dif = a - b

    media_a, media_b = a.mean(), b.mean()
    dif_media = dif.mean()
    dif_pct = dif_media / media_b * 100 if media_b != 0 else float("inf")

    # p-valores: Wilcoxon (principal) + t pareado (checagem)
    try:
        p_w = float(stats.wilcoxon(a, b).pvalue)
    except ValueError:
        p_w = float("nan")   # ocorre se todas as diferenças forem 0
    p_t = float(stats.ttest_rel(a, b).pvalue)

    # IC 95% da diferença média diária
    sd = dif.std(ddof=1)
    se = sd / np.sqrt(n)
    t_crit = stats.t.ppf(0.975, n - 1)
    ic = (dif_media - t_crit * se, dif_media + t_crit * se)

    # tamanho de efeito: Cohen's d pareado (dif média / desvio das diferenças)
    d = dif_media / sd if sd > 0 else float("nan")

    return ComparacaoPareada(
        campeao, desafiante, n, media_a, media_b,
        dif_media, dif_pct, p_w, p_t, ic, d,
    )


def campeao_por_media(tabela: pd.DataFrame) -> str:
    """Grupo com maior margem diária média (= maior margem total, dias alinhados)."""
    return str(tabela.mean().idxmax())


def comparar_campeao_vs_resto(tabela: pd.DataFrame) -> list[ComparacaoPareada]:
    """Elege o campeão e o compara, pareado, contra cada outro grupo."""
    campeao = campeao_por_media(tabela)
    desafiantes = [c for c in tabela.columns if c != campeao]
    return [comparar_pareado(tabela, campeao, d) for d in desafiantes]