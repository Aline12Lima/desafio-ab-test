"""metrics.py — núcleo puro: do DataFrame limpo às métricas de negócio.

Sem I/O e sem estatística inferencial. Só fórmulas determinísticas.
Recebe o DataFrame já validado por data_io.load_ab_test.
"""
from __future__ import annotations

import pandas as pd

COL_GRUPO = "Grupos de usuários"


def _div(num: pd.Series, den: pd.Series) -> pd.Series:
    """Divisão elemento a elemento; devolve NaN onde o denominador é 0.

    Um dia com 0 compradores não tem 'margem por comprador' definida —
    o valor certo ali é 'ausente' (NaN), não infinito nem erro.
    """
    return num / den.mask(den == 0)


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas derivadas por linha (dia × grupo)."""
    df = df.copy()
    df["margem"] = df["comissão"] - df["cashback"]
    df["margem_por_comprador"] = _div(df["margem"], df["compradores"])
    return df


def metricas_por_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega o período inteiro por grupo e devolve os KPIs de decisão."""
    df = enriquecer(df)
    g = df.groupby(COL_GRUPO).agg(
        dias=("Data", "nunique"),
        compradores=("compradores", "sum"),
        comissao=("comissão", "sum"),
        cashback=("cashback", "sum"),
        gmv=("vendas totais", "sum"),
        margem=("margem", "sum"),
    )
    # derivadas a partir dos totais (razão de somas, não média de razões)
    g["ticket_medio"] = _div(g["gmv"], g["compradores"])
    g["margem_por_comprador"] = _div(g["margem"], g["compradores"])
    g["cashback_pct_gmv"] = _div(g["cashback"], g["gmv"]) * 100
    g["comissao_pct_gmv"] = _div(g["comissao"], g["gmv"]) * 100
    return g


def margem_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela dia × grupo da margem diária — insumo dos testes pareados. [Quem vendeu mais ou qual variante gera melhor para o negócio?]"""
    df = enriquecer(df)
    return df.pivot(index="Data", columns=COL_GRUPO, values="margem")