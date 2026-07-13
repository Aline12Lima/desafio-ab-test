"""cli.py — orquestra o pipeline num comando único de linha de comando.

Uso: analyze <csv> [--nome ...] [--descricao ...] [--destino csv|sheets] ...
Carrega -> analisa -> decide -> gera relatório -> registra na planilha.
É a "borda" que amarra o núcleo puro às saídas; a lógica vive nos módulos.
"""
from __future__ import annotations

import os
from pathlib import Path

import typer

from .data_io import DadosInvalidosError, load_ab_test
from .decision import decidir
from .metrics import metricas_por_grupo
from .report import narrar, salvar_relatorio
from .sheets import registrar_teste

# carrega variáveis do .env, se disponível (SHEET_ID, GOOGLE_CREDENTIALS)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def analyze(
    csv: Path = typer.Argument(..., help="Caminho do CSV do teste A/B."),
    nome: str = typer.Option(None, "--nome", "-n", help="Nome do teste (default: nome do arquivo)."),
    descricao: str = typer.Option("", "--descricao", "-d", help="Descrição do teste."),
    destino: str = typer.Option("csv", "--destino", help="Onde registrar: 'csv' ou 'sheets'."),
    sheet_id: str = typer.Option(None, "--sheet-id", help="ID da planilha (ou SHEET_ID no .env)."),
    credencial: str = typer.Option(None, "--credencial", help="JSON da service account (ou GOOGLE_CREDENTIALS)."),
    reports_dir: Path = typer.Option("reports", "--reports-dir", help="Pasta de saída dos relatórios."),
    registrar: bool = typer.Option(True, "--registrar/--sem-registro", help="Registrar (ou não) na planilha."),
) -> None:
    """Analisa UM teste A/B de cashback e recomenda qual variante escalar."""
    nome = nome or csv.stem

    # 1) carrega e valida (erro de dados vira mensagem clara, não traceback)
    try:
        df = load_ab_test(csv)
    except (FileNotFoundError, DadosInvalidosError) as e:
        typer.secho(f"ERRO nos dados: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # 2) analisa
    agg = metricas_por_grupo(df)
    rec = decidir(df)
    periodo = f"{df['Data'].min():%d/%m/%Y} a {df['Data'].max():%d/%m/%Y}"

    # 3) resumo no terminal (o que o colaborador vê)
    cor = typer.colors.GREEN if rec.vencedor else typer.colors.YELLOW
    typer.secho(f"\n{nome}  ({periodo})", bold=True)
    typer.secho(f"Decisao: {rec.decisao}", fg=cor, bold=True)
    typer.echo(narrar(rec))

    # 4) relatório (md + html)
    caminhos = salvar_relatorio(rec, agg, nome, periodo, dir_saida=str(reports_dir))
    typer.echo("\nRelatorios gerados:")
    for c in caminhos:
        typer.echo(f"  - {c}")

    # 5) registro na planilha (com fallback seguro)
    if registrar:
        sid = sheet_id or os.environ.get("SHEET_ID")
        cred = credencial or os.environ.get("GOOGLE_CREDENTIALS", "secrets/service_account.json")
        if destino == "sheets" and not sid:
            typer.secho("AVISO: destino 'sheets' sem SHEET_ID; registrando em CSV.",
                        fg=typer.colors.YELLOW)
            destino = "csv"
        try:
            alvo = registrar_teste(rec, nome, descricao, destino=destino,
                                   sheet_id=sid, caminho_credencial=cred)
            typer.echo(f"\nRegistrado ({destino}): {alvo}")
        except Exception as e:
            typer.secho(f"AVISO: falha ao registrar em '{destino}': {e}",
                        fg=typer.colors.YELLOW, err=True)


def main() -> None:
    typer.run(analyze)


if __name__ == "__main__":
    main()