from datetime import date
from decimal import Decimal

from src.modelos import Despesa
from src.regras import filtro_categoria_invalida, filtro_valor_negativo, normalizar_categoria


def test_rn011_normaliza_categoria_case_insensitive():
    assert normalizar_categoria("ALIMENTACAO") == "alimentacao"


def test_rn009_valor_negativo_ignorado():
    d009 = Despesa(
        id="d-009",
        data=date(2026, 7, 11),
        categoria="transporte_urbano",
        descricao="Estorno de corrida cancelada",
        fornecedor="TaxiApp",
        valor=Decimal("-45.00"),
        tem_nota_fiscal=False,
    )

    resultado = filtro_valor_negativo(d009)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa


def test_rn008_categoria_fora_da_politica():
    d005 = Despesa(
        id="d-005",
        data=date(2026, 7, 7),
        categoria="coworking",
        descricao="Diaria em espaco compartilhado",
        fornecedor="HubOffice",
        valor=Decimal("89.00"),
        tem_nota_fiscal=True,
    )

    resultado = filtro_categoria_invalida(d005)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa
