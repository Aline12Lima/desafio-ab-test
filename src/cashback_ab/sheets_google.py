"""sheets_google.py — destino Google Sheets da interface de registro.

Isolado do sheets.py de propósito: as libs do Google só são importadas
aqui, e só carregam quando destino='sheets' é usado (import tardio).
Autentica como service account e anexa uma linha à planilha.
"""
from __future__ import annotations

from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

ESCOPOS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Rosa claro no tom Méliuz (#FBD9EC), em RGB 0-1 como o Google exige
ROSA_MELIUZ = {"red": 0.984, "green": 0.851, "blue": 0.925}


def _abrir_planilha(sheet_id: str, caminho_credencial: str):
    """Autentica como service account e devolve a primeira aba da planilha."""
    cred = Credentials.from_service_account_file(caminho_credencial, scopes=ESCOPOS)
    cliente = gspread.authorize(cred)
    return cliente.open_by_key(sheet_id).sheet1


def registrar_google_sheets(
    linha: dict[str, str],
    campos: list[str],
    cabecalho: list[str],
    sheet_id: str,
    caminho_credencial: str = "secrets/service_account.json",
    **_,
) -> str:
    """Anexa a linha à planilha, garantindo o cabeçalho formatado na linha 1."""
    if not Path(caminho_credencial).exists():
        raise FileNotFoundError(
            f"Credencial não encontrada em {caminho_credencial}. "
            "Rode com destino='csv' ou configure a service account."
        )
    aba = _abrir_planilha(sheet_id, caminho_credencial)

    # GARANTE o cabeçalho: se a linha 1 não for o esperado, insere no topo
    # e o pinta no tom Méliuz. Só roda quando o cabeçalho é (re)criado.
    primeira_linha = aba.row_values(1)
    if primeira_linha != cabecalho:
        aba.insert_row(cabecalho, index=1, value_input_option="USER_ENTERED")
        aba.format("1:1", {"backgroundColor": ROSA_MELIUZ})

    valores = [linha.get(chave, "") for chave in campos]
    aba.append_row(valores, value_input_option="USER_ENTERED")

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"