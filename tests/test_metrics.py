"""Testes das fórmulas de negócio e do tratamento da divisão por zero (metrics)."""
import math

import pandas as pd

from cashback_ab.metrics import _div, enriquecer, metricas_por_grupo


def _df_limpo():
    # como o df sai do data_io: dinheiro já em float, Data como datetime
    return pd.DataFrame({
        "Data": pd.to_datetime(["2011-01-01", "2011-01-02", "2011-01-01", "2011-01-02"]),
        "Grupos de usuários": ["Grupo 1", "Grupo 1", "Grupo 2", "Grupo 2"],
        "compradores": [10, 10, 5, 5],
        "comissão": [200.0, 200.0, 100.0, 100.0],
        "cashback": [50.0, 50.0, 40.0, 40.0],
        "vendas totais": [1000.0, 1000.0, 500.0, 500.0],
    })


def test_div_por_zero_vira_nan():
    num = pd.Series([100.0, 50.0])
    den = pd.Series([10.0, 0.0])         # segundo denominador é zero
    r = _div(num, den)
    assert r.iloc[0] == 10.0
    assert math.isnan(r.iloc[1])         # 50/0 -> NaN, não infinito


def test_margem_e_comissao_menos_cashback():
    df = enriquecer(_df_limpo())
    # Grupo 1 dia 1: 200 - 50 = 150
    assert df["margem"].iloc[0] == 150.0


def test_margem_por_comprador_dia():
    df = enriquecer(_df_limpo())
    # dia 1 G1: margem 150 / 10 compradores = 15
    assert df["margem_por_comprador"].iloc[0] == 15.0


def test_agregacao_por_grupo():
    g = metricas_por_grupo(_df_limpo())
    # Grupo 1: margem total = 150 + 150 = 300
    assert g.loc["Grupo 1", "margem"] == 300.0
    # Grupo 2: margem total = 60 + 60 = 120
    assert g.loc["Grupo 2", "margem"] == 120.0


def test_margem_por_comprador_e_razao_de_somas():
    g = metricas_por_grupo(_df_limpo())
    # G1: margem total 300 / compradores totais 20 = 15 (razão de somas)
    assert g.loc["Grupo 1", "margem_por_comprador"] == 15.0