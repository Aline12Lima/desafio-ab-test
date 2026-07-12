"""io.py — a única porta de entrada de dados do pipeline.

Responsabilidade: receber o caminho de um CSV e devolver um DataFrame
limpo e validado — ou falhar com um erro claro. Nada de estatística
ou de decisão aqui: esta é uma "borda" (toca o disco), não o núcleo.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

# --- Contrato: como um dataset válido se parece ---
# (na versão final isto viveria em schema.py / config.py)
COLUNAS_ESPERADAS = [
    "Data",
    "Grupos de usuários",
    "Parceiro",
    "compradores",
    "comissão",
    "cashback",
    "vendas totais",
]
COLUNAS_MONETARIAS = ["comissão", "cashback", "vendas totais"]
COLUNAS_NUMERICAS = ["compradores", *COLUNAS_MONETARIAS]


class DadosInvalidosError(ValueError):
    """Erro de dados de entrada: schema ou valores fora do contrato."""


# Tudo que NÃO for dígito, vírgula ou sinal de menos é lixo de formatação
# ('R$', espaços, e o '.' de milhar do padrão brasileiro).
_NAO_NUMERICO = re.compile(r"[^\d,\-]")


def parse_brl(valor: str | float) -> float:
    """Converte 'R$ 1.234,56' (padrão BR) em 1234.56.

    No formato brasileiro '.' separa milhar e ',' separa centavos.
    Retorna NaN para células vazias ou impossíveis de converter —
    a validação a jusante decide o que fazer com esses NaN.
    """
    if pd.isna(valor):
        return float("nan")
    texto = _NAO_NUMERICO.sub("", str(valor)).replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return float("nan")


def load_ab_test(caminho: str | Path) -> pd.DataFrame:
    """Carrega um CSV de teste A/B, limpa e valida. Devolve DataFrame pronto."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(caminho)

    # 1) O schema bate?
    faltando = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
    if faltando:
        raise DadosInvalidosError(f"Colunas ausentes no CSV: {faltando}")

    # 2) Parse do dinheiro (string BR -> float)
    for col in COLUNAS_MONETARIAS:
        df[col] = df[col].map(parse_brl)

    # 3) Coerção dos outros tipos
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["compradores"] = pd.to_numeric(df["compradores"], errors="coerce")

    # 4) Sanidade
    _validar(df)

    return df


def _validar(df: pd.DataFrame) -> None:
    """Falha alto e claro se algo estiver fora do contrato ('fail fast')."""
    if df["Data"].isna().any():
        n = int(df["Data"].isna().sum())
        raise DadosInvalidosError(f"{n} linha(s) com data inválida.")

    for col in COLUNAS_NUMERICAS:
        if df[col].isna().any():
            raise DadosInvalidosError(f"Valores ausentes/inválidos em '{col}'.")
        if (df[col] < 0).any():
            raise DadosInvalidosError(f"Valores negativos em '{col}'.")

    n_grupos = df["Grupos de usuários"].nunique()
    if n_grupos < 2:
        raise DadosInvalidosError(
            f"Um teste A/B precisa de ao menos 2 grupos; encontrei {n_grupos}."
        )