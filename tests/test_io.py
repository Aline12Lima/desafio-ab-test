"""Testes do carregamento e da robustez a dados ruins (data_io)."""
import math

import pandas as pd
import pytest

from cashback_ab.data_io import DadosInvalidosError, load_ab_test, parse_brl


class TestParseBrl:
    """O parser de moeda BR é o coração da robustez — testamos os casos-limite."""

    def test_separador_de_milhar(self):
        assert parse_brl("R$ 1.234") == 1234.0

    def test_centavos_com_virgula(self):
        assert parse_brl("R$ 1.234,56") == 1234.56

    def test_zero(self):
        assert parse_brl("R$ 0") == 0.0

    def test_ignora_espacos(self):
        assert parse_brl("  R$ 2.079  ") == 2079.0

    def test_preserva_negativo(self):
        assert parse_brl("R$ -100") == -100.0

    def test_nan_continua_nan(self):
        assert math.isnan(parse_brl(float("nan")))

    def test_vazio_vira_nan(self):
        assert math.isnan(parse_brl(""))

    def test_lixo_vira_nan_sem_quebrar(self):
        assert math.isnan(parse_brl("R$ abc"))


def _escreve_csv(tmp_path, df):
    caminho = tmp_path / "teste.csv"
    df.to_csv(caminho, index=False)
    return caminho


def _df_valido():
    return pd.DataFrame({
        "Data": ["2011-01-01", "2011-01-02", "2011-01-01", "2011-01-02"],
        "Grupos de usuários": ["Grupo 1", "Grupo 1", "Grupo 2", "Grupo 2"],
        "Parceiro": ["X"] * 4,
        "compradores": [10, 12, 8, 9],
        "comissão": ["R$ 100", "R$ 120", "R$ 80", "R$ 90"],
        "cashback": ["R$ 50", "R$ 60", "R$ 40", "R$ 45"],
        "vendas totais": ["R$ 1.000", "R$ 1.200", "R$ 800", "R$ 900"],
    })


class TestLoadAbTest:
    def test_carrega_e_converte_dinheiro(self, tmp_path):
        df = load_ab_test(_escreve_csv(tmp_path, _df_valido()))
        assert df.shape == (4, 7)
        assert df["comissão"].dtype == float
        assert df["comissão"].iloc[0] == 100.0

    def test_coluna_faltando(self, tmp_path):
        ruim = _df_valido().drop(columns=["cashback"])
        with pytest.raises(DadosInvalidosError):
            load_ab_test(_escreve_csv(tmp_path, ruim))

    def test_valor_negativo(self, tmp_path):
        ruim = _df_valido()
        ruim.loc[0, "comissão"] = "R$ -100"
        with pytest.raises(DadosInvalidosError):
            load_ab_test(_escreve_csv(tmp_path, ruim))

    def test_menos_de_dois_grupos(self, tmp_path):
        ruim = _df_valido()
        ruim["Grupos de usuários"] = "Grupo 1"
        with pytest.raises(DadosInvalidosError):
            load_ab_test(_escreve_csv(tmp_path, ruim))

    def test_arquivo_inexistente(self):
        with pytest.raises(FileNotFoundError):
            load_ab_test("/nao/existe.csv")