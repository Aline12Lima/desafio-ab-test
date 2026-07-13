"""report.py — borda de saída: Recommendation -> relatório para gestor.

Renderiza Markdown (base) a partir de um template Jinja2 e, opcionalmente,
converte para HTML estilizado. Também constrói a narrativa da decisão em
linguagem humana (narrar) — a apresentação é responsabilidade desta camada.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import markdown as md_lib
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .decision import Recommendation
from .formatting import classificar_efeito, fmt_brl, fmt_p, fmt_pct

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

SELOS = {
    "ESCALAR": "ESCALAR",
    "ESCALAR_COM_CAUTELA": "ESCALAR COM CAUTELA",
    "INCONCLUSIVO": "INCONCLUSIVO",
}

_HTML_SHELL = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title><style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; line-height: 1.6;
    max-width: 820px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }}
  h1 {{ font-size: 1.6rem; border-bottom: 2px solid #eee; padding-bottom: .3em; }}
  h2 {{ font-size: 1.2rem; margin-top: 2em; color: #0F6E56; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .95rem; }}
  th, td {{ border: 1px solid #e2e2e2; padding: 8px 12px; text-align: right; }}
  th:first-child, td:first-child {{ text-align: left; }}
  th {{ background: #f6f8f7; }}
  hr {{ border: none; border-top: 1px solid #eee; margin: 1.5em 0; }}
  em {{ color: #666; }}
</style></head><body>
{corpo}
</body></html>"""


def narrar(rec: Recommendation) -> str:
    """Constrói a frase da decisão em linguagem humana, usando formatting.

    Reconstrói a narrativa a partir dos fatos estruturados da Recommendation —
    é aqui (apresentação) que os números viram texto formatado, não no núcleo.
    """
    c = rec.comparacao_decisiva
    if rec.decisao == "ESCALAR":
        return (
            f"{rec.campeao} tem a maior margem total e supera {rec.vice} em "
            f"{fmt_pct(c.dif_pct)} ao dia (p {fmt_p(c.p_wilcoxon)}, efeito "
            f"{classificar_efeito(c.d_cohen)}). Diferença real e material — "
            f"escalar {rec.campeao} a 100%."
        )
    if rec.decisao == "ESCALAR_COM_CAUTELA":
        return (
            f"{rec.campeao} vence {rec.vice} de forma estatisticamente real, mas "
            f"por margem modesta ({fmt_pct(c.dif_pct)}). Escalar é defensável, "
            f"porém o ganho pode não compensar o custo da troca."
        )
    return (
        f"A diferença entre {rec.campeao} e {rec.vice} não é estatisticamente "
        f"significativa (p {fmt_p(c.p_wilcoxon)}). Manter a variante de menor "
        f"custo ({rec.variante_mais_barata}) e estender o teste para ganhar poder."
    )


def _contexto(rec: Recommendation, agg: pd.DataFrame, nome_teste: str,
              periodo: str, alpha: float, limiar_pct: float) -> dict:
    linhas = []
    for grupo, row in agg.iterrows():
        linhas.append({
            "grupo": grupo,
            "marca": " ◄" if grupo == rec.vencedor else "",
            "cashback_pct": fmt_pct(row["cashback_pct_gmv"], casas=1).lstrip("+"),
            "compradores": f"{int(row['compradores']):,}".replace(",", "."),
            "gmv": fmt_brl(row["gmv"]),
            "margem": fmt_brl(row["margem"]),
            "margem_comp": fmt_brl(row["margem_por_comprador"], casas=2),
        })
    c = rec.comparacao_decisiva
    comp = {
        "campeao": c.campeao, "vice": c.desafiante, "n_dias": c.n_dias,
        "dif_dia": fmt_brl(c.dif_media), "dif_pct": fmt_pct(c.dif_pct),
        "p": fmt_p(c.p_wilcoxon),
        "ic": f"{fmt_brl(c.ic95[0])} a {fmt_brl(c.ic95[1])}",
        "efeito": classificar_efeito(c.d_cohen),
        "d": f"{c.d_cohen:.2f}".replace(".", ","),
    }
    titulo = {
        "ESCALAR": f"Escalar {rec.vencedor} para 100% do tráfego",
        "ESCALAR_COM_CAUTELA": f"Escalar {rec.vencedor} — com ressalvas",
        "INCONCLUSIVO": f"Manter {rec.variante_mais_barata} e estender o teste",
    }[rec.decisao]
    return {
        "nome_teste": nome_teste, "periodo": periodo, "n_grupos": len(agg),
        "selo": SELOS[rec.decisao], "titulo_decisao": titulo,
        "justificativa": narrar(rec), "linhas": linhas, "comp": comp,
        "limiar_pct": fmt_pct(limiar_pct).lstrip("+"),
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def gerar_markdown(rec, agg, nome_teste, periodo, alpha=0.05, limiar_pct=5.0,
                   templates_dir: Path = TEMPLATES_DIR) -> str:
    """Parte PURA: devolve o texto Markdown do relatório."""
    env = Environment(loader=FileSystemLoader(str(templates_dir)),
                      autoescape=select_autoescape([]), trim_blocks=True)
    tmpl = env.get_template("report.md.j2")
    return tmpl.render(**_contexto(rec, agg, nome_teste, periodo, alpha, limiar_pct))


def markdown_para_html(texto_md: str, titulo: str = "Relatório de Teste A/B") -> str:
    """Parte PURA: converte o Markdown em HTML estilizado."""
    corpo = md_lib.markdown(texto_md, extensions=["tables"])
    return _HTML_SHELL.format(corpo=corpo, titulo=titulo)


def salvar_relatorio(rec, agg, nome_teste, periodo, dir_saida="reports",
                     gerar_html=True, **kw) -> list[Path]:
    """Parte de I/O: escreve .md (sempre) e .html (opcional). Devolve caminhos."""
    dir_saida = Path(dir_saida)
    dir_saida.mkdir(parents=True, exist_ok=True)
    slug = nome_teste.lower().replace(" ", "_").replace("—", "-")

    md_txt = gerar_markdown(rec, agg, nome_teste, periodo, **kw)
    caminho_md = dir_saida / f"{slug}.md"
    caminho_md.write_text(md_txt, encoding="utf-8")
    caminhos = [caminho_md]

    if gerar_html:
        caminho_html = dir_saida / f"{slug}.html"
        caminho_html.write_text(markdown_para_html(md_txt, nome_teste), encoding="utf-8")
        caminhos.append(caminho_html)
    return caminhos