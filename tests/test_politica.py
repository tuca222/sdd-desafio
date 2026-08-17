from decimal import Decimal

from src.politica import (
    CATEGORIAS_VALIDAS,
    LIMITE_ALIMENTACAO,
    LIMITE_HOSPEDAGEM,
    LIMITE_NOTA_FISCAL,
    LIMITE_TRANSPORTE_URBANO,
)


def test_limite_alimentacao_e_60_reais():
    assert LIMITE_ALIMENTACAO == Decimal("60.00")


def test_limite_transporte_urbano_e_80_reais():
    assert LIMITE_TRANSPORTE_URBANO == Decimal("80.00")


def test_limite_hospedagem_e_250_reais():
    assert LIMITE_HOSPEDAGEM == Decimal("250.00")


def test_limite_nota_fiscal_e_100_reais():
    assert LIMITE_NOTA_FISCAL == Decimal("100.00")


def test_categorias_validas_sao_alimentacao_transporte_hospedagem():
    assert CATEGORIAS_VALIDAS == {"alimentacao", "transporte_urbano", "hospedagem"}
