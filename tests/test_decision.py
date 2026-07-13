"""Testes da regra de decisão com datasets sintéticos de vencedor conhecido."""
import pandas as pd

from cashback_ab.decision import decidir


def _sintetico(dias, grupos):
    """Constrói um df no formato limpo. `grupos` = {nome: (comissao, cashback, compradores)}."""
    linhas = []
    for d in range(dias):
        data = pd.Timestamp("2011-01-01") + pd.Timedelta(days=d)
        for nome, (com, cash, comp) in grupos.items():
            ruido = d % 3  # pequena variação diária para o teste ter variância
            linhas.append({
                "Data": data,
                "Grupos de usuários": nome,
                "compradores": comp,
                "comissão": float(com + ruido),
                "cashback": float(cash),
                "vendas totais": float(com * 10),
            })
    return pd.DataFrame(linhas)


def test_escalar_vencedor_claro():
    # Grupo 1 tem margem ~150/dia; Grupo 2 ~50/dia. Grupo 1 deve vencer.
    df = _sintetico(20, {
        "Grupo 1": (200, 50, 10),
        "Grupo 2": (150, 100, 10),
    })
    rec = decidir(df)
    assert rec.decisao == "ESCALAR"
    assert rec.vencedor == "Grupo 1"


def test_inconclusivo_quando_grupos_identicos():
    # Grupos idênticos dia a dia -> diferença nula -> sem significância.
    df = _sintetico(20, {
        "Grupo 1": (150, 50, 10),
        "Grupo 2": (150, 50, 10),
    })
    rec = decidir(df)
    assert rec.decisao == "INCONCLUSIVO"
    assert rec.vencedor is None


def test_generaliza_para_dois_ou_tres_grupos():
    # a mesma regra funciona com 3 grupos, sem mudar código
    df = _sintetico(20, {
        "Grupo 1": (300, 50, 10),
        "Grupo 2": (200, 80, 10),
        "Grupo 3": (150, 100, 10),
    })
    rec = decidir(df)
    assert rec.vencedor == "Grupo 1"
    assert len(rec.todas_comparacoes) == 2   # campeão vs os outros 2