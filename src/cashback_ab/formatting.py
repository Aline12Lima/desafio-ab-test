"""formatting.py — camada de apresentação: número cru -> texto para humano.

Funções puras, sem dependência do resto do projeto. Fonte única da verdade
de "como mostrar dinheiro, %, p-valor e tamanho de efeito". Usada por
report.py, cli.py e sheets.py — conserta casos como 'inf%' em um lugar só.
"""
from __future__ import annotations

import math

TRACO = "—"  # placeholder para valor ausente (NaN)


def fmt_brl(x: float, casas: int = 0) -> str:
    """1234567.0 -> 'R$ 1.234.567'  (padrão brasileiro: '.' de milhar)."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return TRACO
    # formata no padrão US e troca os separadores para o BR
    us = f"{x:,.{casas}f}"                       # 1,234,567.00
    br = us.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {br}"


def fmt_pct(x: float, casas: int = 0) -> str:
    """13.2 -> '+13%'.  inf -> '>999%'.  NaN -> '—'.  Sempre com sinal."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return TRACO
    if math.isinf(x):
        return ">999%" if x > 0 else "<-999%"
    return f"{x:+.{casas}f}".replace(".", ",") + "%"


def fmt_p(p: float) -> str:
    """P-valor legível: 4e-05 -> '< 0,001';  0.045 -> '0,045'."""
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return TRACO
    if p < 0.001:
        return "< 0,001"
    return f"{p:.3f}".replace(".", ",")


def classificar_efeito(d: float) -> str:
    """Traduz o d de Cohen em rótulo (convenção clássica de Cohen)."""
    if d is None or (isinstance(d, float) and math.isnan(d)):
        return TRACO
    d = abs(d)
    if d < 0.2:
        return "desprezível"
    if d < 0.5:
        return "pequeno"
    if d < 0.8:
        return "médio"
    return "grande"