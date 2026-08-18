from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo
from src.politica import LIMITE_ALIMENTACAO, LIMITE_HOSPEDAGEM, LIMITE_TRANSPORTE_URBANO
from src.regras import (
    aplicar_limite_diario,
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
        categoria_original="transporte_urbano",
        descricao="Estorno de corrida cancelada",
        fornecedor="TaxiApp",
        valor=Decimal("-45.00"),
        valor_original=Decimal("-45.00"),
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
        categoria_original="coworking",
        descricao="Diaria em espaco compartilhado",
        fornecedor="HubOffice",
        valor=Decimal("89.00"),
        valor_original=Decimal("89.00"),
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
        categoria_original="alimentacao",
        descricao="Almoco de abril lancado com atraso",
        fornecedor="Restaurante Tavola",
        valor=Decimal("41.00"),
        valor_original=Decimal("41.00"),
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
        categoria_original="alimentacao",
        descricao="Despesa no primeiro dia do periodo",
        fornecedor="Fornecedor Teste",
        valor=Decimal("10.00"),
        valor_original=Decimal("10.00"),
        tem_nota_fiscal=True,
    )
    despesa_no_fim = Despesa(
        id="d-101",
        data=PERIODO_JULHO_2026.fim,
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Despesa no ultimo dia do periodo",
        fornecedor="Fornecedor Teste",
        valor=Decimal("10.00"),
        valor_original=Decimal("10.00"),
        tem_nota_fiscal=True,
    )

    assert filtro_fora_periodo(despesa_no_inicio, PERIODO_JULHO_2026) is None
    assert filtro_fora_periodo(despesa_no_fim, PERIODO_JULHO_2026) is None


def test_rn007_duplicata_negada_primeira_mantida():
    d006 = Despesa(
        id="d-006",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        valor_original=Decimal("54.90"),
        tem_nota_fiscal=True,
    )
    d007 = Despesa(
        id="d-007",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        valor_original=Decimal("54.90"),
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


def test_rn007_duplicata_ignora_capitalizacao_da_categoria():
    lancada_em_minusculas = Despesa(
        id="d-600",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        valor_original=Decimal("54.90"),
        tem_nota_fiscal=True,
    )
    lancada_em_maiusculas = Despesa(
        id="d-601",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        categoria_original="ALIMENTACAO",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        valor_original=Decimal("54.90"),
        tem_nota_fiscal=True,
    )

    resultado = filtro_duplicata(lancada_em_maiusculas, [lancada_em_minusculas])

    assert resultado is not None
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "Almoco(d-600)" in resultado.justificativa


def test_rn005_nota_fiscal_obrigatoria_acima_de_100():
    d004 = Despesa(
        id="d-004",
        data=date(2026, 7, 6),
        categoria="transporte_urbano",
        categoria_original="transporte_urbano",
        descricao="Corrida hotel",
        fornecedor="TaxiApp",
        valor=Decimal("100.01"),
        valor_original=Decimal("100.01"),
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
        categoria_original="hospedagem",
        descricao="Hotel Rio - 2 diarias",
        fornecedor="Hotel Copa Sul",
        valor=Decimal("480.00"),
        valor_original=Decimal("480.00"),
        tem_nota_fiscal=True,
    )

    assert filtro_nota_fiscal(d010) is None


def test_rn005_valor_exatamente_100_nao_exige():
    d003 = Despesa(
        id="d-003",
        data=date(2026, 7, 6),
        categoria="transporte_urbano",
        categoria_original="transporte_urbano",
        descricao="Corrida aeroporto",
        fornecedor="TaxiApp",
        valor=Decimal("100.00"),
        valor_original=Decimal("100.00"),
        tem_nota_fiscal=False,
    )

    assert filtro_nota_fiscal(d003) is None


def test_rn001_limite_diario_alimentacao():
    d001 = Despesa(
        id="d-001",
        data=date(2026, 7, 3),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Almoco com cliente",
        fornecedor="Restaurante Tavola",
        valor=Decimal("72.50"),
        valor_original=Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    d002 = Despesa(
        id="d-002",
        data=date(2026, 7, 3),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Jantar apos reuniao",
        fornecedor="Cantina do Porto",
        valor=Decimal("38.00"),
        valor_original=Decimal("38.00"),
        tem_nota_fiscal=True,
    )

    resultado_d001 = aplicar_limite_diario(d001, LIMITE_ALIMENTACAO, [])

    assert resultado_d001.despesa_reembolsavel is True
    assert resultado_d001.tipo_reembolso == "parcial"
    assert resultado_d001.valor_reembolsavel == Decimal("60.00")
    assert "parcial" in resultado_d001.justificativa

    resultado_d002 = aplicar_limite_diario(
        d002, LIMITE_ALIMENTACAO, [(d001, resultado_d001.valor_reembolsavel)]
    )

    assert resultado_d002.despesa_reembolsavel is False
    assert resultado_d002.tipo_reembolso == "nenhum"
    assert resultado_d002.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado_d002.justificativa
    assert "Almoco com cliente(d-001)" in resultado_d002.justificativa


def test_rn002_limite_diario_transporte():
    d003 = Despesa(
        id="d-003",
        data=date(2026, 7, 6),
        categoria="transporte_urbano",
        categoria_original="transporte_urbano",
        descricao="Corrida aeroporto",
        fornecedor="TaxiApp",
        valor=Decimal("100.00"),
        valor_original=Decimal("100.00"),
        tem_nota_fiscal=False,
    )

    resultado = aplicar_limite_diario(d003, LIMITE_TRANSPORTE_URBANO, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == Decimal("80.00")
    assert "parcial" in resultado.justificativa


def test_rn004_valor_dentro_do_limite_reembolsa_total():
    d006 = Despesa(
        id="d-006",
        data=date(2026, 7, 9),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Almoco",
        fornecedor="Bistro Central",
        valor=Decimal("54.90"),
        valor_original=Decimal("54.90"),
        tem_nota_fiscal=True,
    )

    resultado = aplicar_limite_diario(d006, LIMITE_ALIMENTACAO, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "total"
    assert resultado.valor_reembolsavel == Decimal("54.90")
    assert "total" in resultado.justificativa


def test_rn003_limite_diario_hospedagem():
    d010 = Despesa(
        id="d-010",
        data=date(2026, 7, 14),
        categoria="hospedagem",
        categoria_original="hospedagem",
        descricao="Hotel Rio - 2 diarias",
        fornecedor="Hotel Copa Sul",
        valor=Decimal("480.00"),
        valor_original=Decimal("480.00"),
        tem_nota_fiscal=True,
    )

    resultado = aplicar_limite_diario(d010, LIMITE_HOSPEDAGEM, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == Decimal("250.00")
    assert "parcial" in resultado.justificativa


def test_rn012_sem_adicional_de_viagem():
    almoco_acima_do_limite = Despesa(
        id="d-400",
        data=date(2026, 7, 14),
        categoria="alimentacao",
        categoria_original="alimentacao",
        descricao="Almoco em viagem",
        fornecedor="Restaurante do Hotel",
        valor=Decimal("90.00"),
        valor_original=Decimal("90.00"),
        tem_nota_fiscal=True,
    )
    corrida_acima_do_limite = Despesa(
        id="d-401",
        data=date(2026, 7, 14),
        categoria="transporte_urbano",
        categoria_original="transporte_urbano",
        descricao="Corrida em viagem",
        fornecedor="TaxiApp",
        valor=Decimal("120.00"),
        valor_original=Decimal("120.00"),
        tem_nota_fiscal=True,
    )

    resultado_alimentacao = aplicar_limite_diario(almoco_acima_do_limite, LIMITE_ALIMENTACAO, [])
    resultado_transporte = aplicar_limite_diario(
        corrida_acima_do_limite, LIMITE_TRANSPORTE_URBANO, []
    )

    # Os valores sao os limites padrao ampliados em 50% (60 -> 90, 80 -> 120):
    # se o adicional fosse aplicado, ambos virariam reembolso total.
    assert resultado_alimentacao.tipo_reembolso == "parcial"
    assert resultado_alimentacao.valor_reembolsavel == Decimal("60.00")
    assert resultado_transporte.tipo_reembolso == "parcial"
    assert resultado_transporte.valor_reembolsavel == Decimal("80.00")


def test_rn003_hospedagem_dentro_do_limite_reembolsa_total():
    hospedagem_barata = Despesa(
        id="d-200",
        data=date(2026, 7, 14),
        categoria="hospedagem",
        categoria_original="hospedagem",
        descricao="Pousada 1 noite",
        fornecedor="Pousada Central",
        valor=Decimal("180.00"),
        valor_original=Decimal("180.00"),
        tem_nota_fiscal=True,
    )

    resultado = aplicar_limite_diario(hospedagem_barata, LIMITE_HOSPEDAGEM, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "total"
    assert resultado.valor_reembolsavel == Decimal("180.00")
    assert "total" in resultado.justificativa
