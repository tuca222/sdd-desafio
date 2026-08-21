from datetime import date
from decimal import Decimal

from src.modelos import Periodo
from src.politica import LimiteCategoria, TabelaLimites
from src.regras import (
    aplicar_limite_diario,
    filtro_cambio_indisponivel,
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
    normalizar_categoria,
)
from tests.conftest import construir_despesa

PERIODO_JULHO_2026 = Periodo(
    competencia="2026-07",
    inicio=date(2026, 7, 1),
    fim=date(2026, 7, 31),
)

TETO_NOTA_FISCAL = Decimal("100.00")


def tabela(centro_custo: str, **limites: str) -> TabelaLimites:
    return TabelaLimites(
        centro_custo=centro_custo,
        limites={
            categoria: LimiteCategoria(limite=Decimal(limite), periodicidade="dia")
            for categoria, limite in limites.items()
        },
    )


# CC-ENG-PLATAFORMA da política vigente: alimentação R$75,00, transporte R$80,00,
# hospedagem vedada (limite R$0,00). Montada na mão — plan.md §6 ("Estratégia de
# testes") mantém os testes de `regras.py` sem I/O.
CC_ENG = tabela(
    "CC-ENG-PLATAFORMA",
    alimentacao="75.00",
    transporte_urbano="80.00",
    hospedagem="0.00",
)
CC_PADRAO = tabela(
    "CC-SUPORTE-N2",
    alimentacao="60.00",
    transporte_urbano="80.00",
    hospedagem="250.00",
)


def test_rn011_normaliza_categoria_case_insensitive():
    assert normalizar_categoria("ALIMENTACAO") == "alimentacao"


def test_rn009_valor_negativo_ignorado():
    d009 = construir_despesa(
        "d-009",
        date(2026, 7, 11),
        "transporte_urbano",
        "Estorno de corrida cancelada",
        "TaxiApp",
        Decimal("-45.00"),
        tem_nota_fiscal=False,
    )

    resultado = filtro_valor_negativo(d009)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa


def test_rn008_categoria_ausente_da_tabela_do_centro_custo():
    d005 = construir_despesa(
        "d-005",
        date(2026, 7, 7),
        "coworking",
        "Diaria em espaco compartilhado",
        "HubOffice",
        Decimal("89.00"),
        tem_nota_fiscal=True,
    )

    resultado = filtro_categoria_invalida(d005, CC_ENG)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa
    assert "coworking" in resultado.justificativa
    assert "CC-ENG-PLATAFORMA" in resultado.justificativa


def test_rn008_mesma_categoria_reembolsavel_em_outro_centro_de_custo():
    f003 = construir_despesa(
        "f-003",
        date(2026, 7, 17),
        "representacao",
        "Jantar com fornecedor",
        "Casa Trindade",
        Decimal("190.00"),
        tem_nota_fiscal=True,
        moeda_original="BRL",
    )
    cc_comercial = tabela("CC-COMERCIAL", representacao="300.00")

    # A mesma despesa é negada num centro de custo e aceita em outro (RN-014).
    assert filtro_categoria_invalida(f003, CC_PADRAO) is not None
    assert filtro_categoria_invalida(f003, cc_comercial) is None


def test_amb013_categoria_com_limite_zero_nega_citando_proibicao():
    d010 = construir_despesa(
        "d-010",
        date(2026, 7, 14),
        "hospedagem",
        "Hotel Rio - 2 diarias",
        "Hotel Copa Sul",
        Decimal("480.00"),
        tem_nota_fiscal=True,
    )

    resultado = filtro_categoria_invalida(d010, CC_ENG)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa
    assert "proíbe" in resultado.justificativa

    # A justificativa nunca é a de limite diário atingido: nada foi consumido por
    # despesa nenhuma, e não haveria despesa a citar.
    assert "já foi atingido" not in resultado.justificativa


def test_rn006_fora_do_periodo_negado():
    d008 = construir_despesa(
        "d-008",
        date(2026, 4, 15),
        "alimentacao",
        "Almoco de abril lancado com atraso",
        "Restaurante Tavola",
        Decimal("41.00"),
        tem_nota_fiscal=True,
    )

    resultado = filtro_fora_periodo(d008, PERIODO_JULHO_2026)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa


def test_rn006_data_no_extremo_do_periodo_aceita():
    despesa_no_inicio = construir_despesa(
        "d-100",
        PERIODO_JULHO_2026.inicio,
        "alimentacao",
        "Despesa no primeiro dia do periodo",
        "Fornecedor Teste",
        Decimal("10.00"),
        tem_nota_fiscal=True,
    )
    despesa_no_fim = construir_despesa(
        "d-101",
        PERIODO_JULHO_2026.fim,
        "alimentacao",
        "Despesa no ultimo dia do periodo",
        "Fornecedor Teste",
        Decimal("10.00"),
        tem_nota_fiscal=True,
    )

    assert filtro_fora_periodo(despesa_no_inicio, PERIODO_JULHO_2026) is None
    assert filtro_fora_periodo(despesa_no_fim, PERIODO_JULHO_2026) is None


def test_rn007_duplicata_negada_primeira_mantida():
    d006 = construir_despesa(
        "d-006",
        date(2026, 7, 9),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("54.90"),
        tem_nota_fiscal=True,
    )
    d007 = construir_despesa(
        "d-007",
        date(2026, 7, 9),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("54.90"),
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
    lancada_em_minusculas = construir_despesa(
        "d-600",
        date(2026, 7, 9),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("54.90"),
        tem_nota_fiscal=True,
    )
    lancada_em_maiusculas = construir_despesa(
        "d-601",
        date(2026, 7, 9),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("54.90"),
        tem_nota_fiscal=True,
        categoria_original="ALIMENTACAO",
    )

    resultado = filtro_duplicata(lancada_em_maiusculas, [lancada_em_minusculas])

    assert resultado is not None
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "Almoco(d-600)" in resultado.justificativa


def test_rn016_cambio_indisponivel_nega_despesa():
    e004 = construir_despesa(
        "e-004",
        date(2026, 7, 18),
        "alimentacao",
        "Jantar de sabado",
        "Cervejaria Ramiro",
        Decimal("30.00"),
        tem_nota_fiscal=True,
        moeda="EUR",
        moeda_original="EUR",
        valor_brl=None,
    )

    resultado = filtro_cambio_indisponivel(e004)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa
    assert "EUR" in resultado.justificativa
    assert "2026-07-18" in resultado.justificativa


def test_rn016_despesa_com_valor_em_brl_passa_pelo_filtro():
    e002 = construir_despesa(
        "e-002",
        date(2026, 7, 14),
        "alimentacao",
        "Almoco - Lisboa",
        "Taberna do Chiado",
        Decimal("22.00"),
        tem_nota_fiscal=True,
        moeda="EUR",
        moeda_original="EUR",
        valor_brl=Decimal("130.46"),
        taxa_cambio=Decimal("5.93"),
    )
    em_reais = construir_despesa(
        "e-001",
        date(2026, 7, 13),
        "representacao",
        "Jantar com prospect",
        "Casa Trindade",
        Decimal("340.00"),
        tem_nota_fiscal=True,
        moeda_original="BRL",
    )

    assert filtro_cambio_indisponivel(e002) is None
    assert filtro_cambio_indisponivel(em_reais) is None


def test_rn005_nota_fiscal_obrigatoria_acima_do_teto():
    d004 = construir_despesa(
        "d-004",
        date(2026, 7, 6),
        "transporte_urbano",
        "Corrida hotel",
        "TaxiApp",
        Decimal("100.01"),
        tem_nota_fiscal=False,
    )

    resultado = filtro_nota_fiscal(d004, TETO_NOTA_FISCAL)

    assert resultado is not None
    assert resultado.despesa_reembolsavel is False
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado.justificativa
    assert "nota fiscal" in resultado.justificativa


def test_rn005_valor_acima_do_teto_com_nota_fiscal_aceito():
    d010 = construir_despesa(
        "d-010",
        date(2026, 7, 14),
        "hospedagem",
        "Hotel Rio - 2 diarias",
        "Hotel Copa Sul",
        Decimal("480.00"),
        tem_nota_fiscal=True,
    )

    assert filtro_nota_fiscal(d010, TETO_NOTA_FISCAL) is None


def test_rn005_valor_exatamente_no_teto_nao_exige():
    d003 = construir_despesa(
        "d-003",
        date(2026, 7, 6),
        "transporte_urbano",
        "Corrida aeroporto",
        "TaxiApp",
        Decimal("100.00"),
        tem_nota_fiscal=False,
    )

    assert d003.valor_brl == TETO_NOTA_FISCAL
    assert filtro_nota_fiscal(d003, TETO_NOTA_FISCAL) is None


def test_amb017_teto_de_nota_fiscal_compara_valor_convertido():
    # e-005: USD 40,00 em 2026-07-20 pela taxa 5,50 = R$220,00.
    e005 = construir_despesa(
        "e-005",
        date(2026, 7, 20),
        "transporte_urbano",
        "Corridas do dia",
        "Bolt",
        Decimal("40.00"),
        tem_nota_fiscal=False,
        moeda="USD",
        moeda_original="USD",
        valor_brl=Decimal("220.00"),
        taxa_cambio=Decimal("5.50"),
    )
    # e-003: EUR 14,50 em 2026-07-15 pela taxa 5,88 = R$85,26.
    e003 = construir_despesa(
        "e-003",
        date(2026, 7, 15),
        "alimentacao",
        "Cafe e sanduiche",
        "Padaria Lisboa",
        Decimal("14.50"),
        tem_nota_fiscal=False,
        moeda="EUR",
        moeda_original="EUR",
        valor_brl=Decimal("85.26"),
        taxa_cambio=Decimal("5.88"),
    )

    # 40,00 é menor que o teto e R$220,00 não é: quem decide é o valor convertido.
    resultado_e005 = filtro_nota_fiscal(e005, TETO_NOTA_FISCAL)

    assert e005.valor < TETO_NOTA_FISCAL
    assert resultado_e005 is not None
    assert resultado_e005.tipo_reembolso == "nenhum"
    assert resultado_e005.valor_reembolsavel == Decimal("0.00")
    assert "negado" in resultado_e005.justificativa

    # E R$85,26 não cruza o teto, embora a despesa seja internacional.
    assert filtro_nota_fiscal(e003, TETO_NOTA_FISCAL) is None