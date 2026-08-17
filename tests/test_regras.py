from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo
from src.regras import (
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
    normalizar_categoria,
)

PERIODO_JULHO_2026 = Periodo(
    competencia="2026-07",
    inicio=date(2026, 7, 1),
    fim=date(2026, 7, 31),
)


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


def test_rn006_fora_do_periodo_negado():
    d008 = Despesa(
        id="d-008",
        data=date(2026, 4, 15),
        categoria="alimentacao",
        descricao="Almoco de abril lancado com atraso",
        fornecedor="Restaurante Tavola",
        valor=Decimal("41.00"),
        tem_nota_fiscal=True,
    )

    resultado = filtro_fora_periodo(d008, PERIODO_JULHO_2026)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa


def test_rn006_data_no_extremo_do_periodo_aceita():
    despesa_no_inicio = Despesa(
        id="d-100",
        data=PERIODO_JULHO_2026.inicio,
        categoria="alimentacao",
        descricao="Despesa no primeiro dia do periodo",
        fornecedor="Fornecedor Teste",
        valor=Decimal("10.00"),
        tem_nota_fiscal=True,
    )
    despesa_no_fim = Despesa(
        id="d-101",
        data=PERIODO_JULHO_2026.fim,
        categoria="alimentacao",
        descricao="Despesa no ultimo dia do periodo",
        fornecedor="Fornecedor Teste",
        valor=Decimal("10.00"),
        tem_nota_fiscal=True,
    )

    assert filtro_fora_periodo(despesa_no_inicio, PERIODO_JULHO_2026) is None
    assert filtro_fora_periodo(despesa_no_fim, PERIODO_JULHO_2026) is None


def test_rn007_duplicata_negada_primeira_mantida():
    d006 = Despesa(
        id="d-006",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        tem_nota_fiscal=True,
    )
    d007 = Despesa(
        id="d-007",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        tem_nota_fiscal=True,
    )

    assert filtro_duplicata(d006, []) is None

    resultado = filtro_duplicata(d007, [d006])

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa
    assert "Almoco(d-006)" in resultado.justificativa


def test_rn005_nota_fiscal_obrigatoria_acima_de_100():
    d004 = Despesa(
        id="d-004",
        data=date(2026, 7, 6),
        categoria="transporte_urbano",
        descricao="Corrida hotel",
        fornecedor="TaxiApp",
        valor=Decimal("100.01"),
        tem_nota_fiscal=False,
    )

    resultado = filtro_nota_fiscal(d004)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa


def test_rn005_valor_acima_de_100_com_nota_fiscal_aceito():
    d010 = Despesa(
        id="d-010",
        data=date(2026, 7, 14),
        categoria="hospedagem",
        descricao="Hotel Rio - 2 diarias",
        fornecedor="Hotel Copa Sul",
        valor=Decimal("480.00"),
        tem_nota_fiscal=True,
    )

    assert filtro_nota_fiscal(d010) is None


def test_rn005_valor_exatamente_100_nao_exige():
    d003 = Despesa(
        id="d-003",
        data=date(2026, 7, 6),
        categoria="transporte_urbano",
        descricao="Corrida aeroporto",
        fornecedor="TaxiApp",
        valor=Decimal("100.00"),
        tem_nota_fiscal=False,
    )

    assert filtro_nota_fiscal(d003) is None
