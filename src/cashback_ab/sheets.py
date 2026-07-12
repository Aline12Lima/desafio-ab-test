"""sheets.py — borda de saída: registra cada teste numa planilha de acompanhamento.

Uma interface (registrar_teste) com dois destinos plugáveis:
  - CSV local (fallback, sempre funciona) — o mínimo aceito pelo case.
  - Google Sheets (via API) — o diferencial, exige credencial.
O resto do sistema não sabe qual está em uso: só chama registrar_teste().
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .decision import Recommendation
from .formatting import fmt_brl, fmt_pct

# Cada coluna tem um nome INTERNO (chave estável, usada no código) e um
# RÓTULO de exibição (o que o gestor lê na planilha). Separar os dois deixa
# o cabeçalho bonito sem quebrar a ligação valor<->coluna.
COLUNAS = [
    ("data_registro",        "Data"),
    ("teste",                "Teste"),
    ("descricao",            "Descrição"),
    ("variantes",            "Variantes"),
    ("resultado",            "Resultado"),
    ("decisao",              "Decisão"),
    ("detalhe_estatistico",  "Detalhe estatístico"),
]
CAMPOS = [chave for chave, _ in COLUNAS]       # chaves internas (ordem)
CABECALHO = [rotulo for _, rotulo in COLUNAS]  # rótulos exibidos


def montar_linha(rec: Recommendation, nome_teste: str, descricao: str) -> dict[str, str]:
    """Transforma a Recommendation numa linha legível da planilha (sem I/O)."""
    c = rec.comparacao_decisiva
    if rec.decisao == "INCONCLUSIVO":
        resultado = f"Inconclusivo — manter {rec.variante_mais_barata}"
    else:
        resultado = f"{rec.vencedor} vence ({fmt_pct(c.dif_pct)} de margem vs {rec.vice})"
    return {
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "teste": nome_teste,
        "descricao": descricao,
        "variantes": ", ".join(rec.margem_total.keys()),
        "resultado": resultado,
        "decisao": rec.decisao,
        "detalhe_estatistico": (
            f"dif {fmt_brl(c.dif_media)}/dia; p Wilcoxon "
            f"{'<0,001' if c.p_wilcoxon < 0.001 else round(c.p_wilcoxon, 3)}; "
            f"d={c.d_cohen:.2f}; n={c.n_dias} dias"
        ),
    }


def registrar_csv(linha: dict[str, str], caminho: str | Path = "reports/acompanhamento.csv") -> Path:
    """Anexa a linha ao CSV (cria com cabeçalho de rótulos bonitos se não existir)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo = not caminho.exists()
    with caminho.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo:
            writer.writerow(CABECALHO)               # rótulos humanos no topo
        writer.writerow([linha[c] for c in CAMPOS])  # valores na ordem interna
    return caminho


def registrar_teste(rec: Recommendation, nome_teste: str, descricao: str,
                    destino: str = "csv", **kwargs) -> Path | str:
    """Interface única. destino='csv' (padrão) ou 'sheets' (requer credencial)."""
    linha = montar_linha(rec, nome_teste, descricao)
    if destino == "csv":
        return registrar_csv(linha, kwargs.get("caminho", "reports/acompanhamento.csv"))
    if destino == "sheets":
        from .sheets_google import registrar_google_sheets  # import tardio
        return registrar_google_sheets(linha, CAMPOS, CABECALHO, **kwargs)
    raise ValueError(f"destino desconhecido: {destino!r} (use 'csv' ou 'sheets')")
