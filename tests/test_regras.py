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


def test_amb019_moedas_diferentes_nao_sao_duplicatas():
    em_euro = construir_despesa(
        "d-700",
        date(2026, 7, 14),
        "alimentacao",
        "Almoco",
        "Taberna do Chiado",
        Decimal("22.00"),
        tem_nota_fiscal=True,
        moeda="EUR",
        moeda_original="EUR",
        valor_brl=Decimal("130.46"),
        taxa_cambio=Decimal("5.93"),
    )
    em_reais = construir_despesa(
        "d-701",
        date(2026, 7, 14),
        "alimentacao",
        "Almoco",
        "Taberna do Chiado",
        Decimal("22.00"),
        tem_nota_fiscal=True,
        moeda_original="BRL",
    )

    # EUR 22,00 e BRL 22,00 são gastos de valores completamente diferentes.
    assert filtro_duplicata(em_reais, [em_euro]) is None
    assert filtro_duplicata(em_euro, [em_reais]) is None


def test_amb019_moeda_ausente_e_brl_explicito_sao_duplicatas():
    sem_o_campo = construir_despesa(
        "d-710",
        date(2026, 7, 27),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("88.00"),
        tem_nota_fiscal=True,
    )
    com_brl_explicito = construir_despesa(
        "d-711",
        date(2026, 7, 27),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("88.00"),
        tem_nota_fiscal=True,
        moeda_original="BRL",
    )

    assert sem_o_campo.moeda_original is None
    assert com_brl_explicito.moeda_original == "BRL"

    resultado = filtro_duplicata(com_brl_explicito, [sem_o_campo])

    assert resultado is not None
    assert resultado.tipo_reembolso == "nenhum"
    assert resultado.valor_reembolsavel == Decimal("0.00")
    assert "Almoco(d-710)" in resultado.justificativa


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


def test_rn001_limite_diario_alimentacao():
    d001 = construir_despesa(
        "d-001",
        date(2026, 7, 3),
        "alimentacao",
        "Almoco com cliente",
        "Restaurante Tavola",
        Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    d002 = construir_despesa(
        "d-002",
        date(2026, 7, 3),
        "alimentacao",
        "Jantar apos reuniao",
        "Cantina do Porto",
        Decimal("38.00"),
        tem_nota_fiscal=True,
    )

    resultado_d001 = aplicar_limite_diario(d001, CC_ENG, [])

    assert resultado_d001.despesa_reembolsavel is True
    assert resultado_d001.tipo_reembolso == "total"
    assert resultado_d001.valor_reembolsavel == Decimal("72.50")
    assert "total" in resultado_d001.justificativa

    resultado_d002 = aplicar_limite_diario(
        d002, CC_ENG, [(d001, resultado_d001.valor_reembolsavel)]
    )

    # Sobram R$2,50 do limite de R$75,00 de CC-ENG-PLATAFORMA.
    assert resultado_d002.despesa_reembolsavel is True
    assert resultado_d002.tipo_reembolso == "parcial"
    assert resultado_d002.valor_reembolsavel == Decimal("2.50")
    assert "parcial" in resultado_d002.justificativa
    assert "CC-ENG-PLATAFORMA" in resultado_d002.justificativa


def test_rn014_limite_varia_por_centro_de_custo():
    almoco = construir_despesa(
        "d-800",
        date(2026, 7, 3),
        "alimentacao",
        "Almoco com cliente",
        "Restaurante Tavola",
        Decimal("72.50"),
        tem_nota_fiscal=True,
    )
    cc_adm = tabela("CC-ADM", alimentacao="45.00", transporte_urbano="60.00")

    # A mesma despesa, na mesma data: só o centro de custo muda.
    em_eng = aplicar_limite_diario(almoco, CC_ENG, [])
    no_padrao = aplicar_limite_diario(almoco, CC_PADRAO, [])
    em_adm = aplicar_limite_diario(almoco, cc_adm, [])

    assert em_eng.tipo_reembolso == "total"
    assert em_eng.valor_reembolsavel == Decimal("72.50")

    assert no_padrao.tipo_reembolso == "parcial"
    assert no_padrao.valor_reembolsavel == Decimal("60.00")
    assert "CC-SUPORTE-N2" in no_padrao.justificativa

    assert em_adm.tipo_reembolso == "parcial"
    assert em_adm.valor_reembolsavel == Decimal("45.00")
    assert "CC-ADM" in em_adm.justificativa


def test_rn002_limite_diario_transporte():
    d003 = construir_despesa(
        "d-003",
        date(2026, 7, 6),
        "transporte_urbano",
        "Corrida aeroporto",
        "TaxiApp",
        Decimal("100.00"),
        tem_nota_fiscal=False,
    )

    resultado = aplicar_limite_diario(d003, CC_ENG, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == Decimal("80.00")
    assert "parcial" in resultado.justificativa


def test_rn004_valor_dentro_do_limite_reembolsa_total():
    d006 = construir_despesa(
        "d-006",
        date(2026, 7, 9),
        "alimentacao",
        "Almoco",
        "Bistro Central",
        Decimal("54.90"),
        tem_nota_fiscal=True,
    )

    resultado = aplicar_limite_diario(d006, CC_PADRAO, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "total"
    assert resultado.valor_reembolsavel == Decimal("54.90")
    assert "total" in resultado.justificativa


def test_rn003_limite_diario_hospedagem():
    f002 = construir_despesa(
        "f-002",
        date(2026, 7, 17),
        "hospedagem",
        "Pousada - 1 diaria",
        "Pousada do Vale",
        Decimal("310.00"),
        tem_nota_fiscal=True,
    )

    resultado = aplicar_limite_diario(f002, CC_PADRAO, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == Decimal("250.00")
    assert "parcial" in resultado.justificativa


def test_rn003_hospedagem_dentro_do_limite_reembolsa_total():
    hospedagem_barata = construir_despesa(
        "d-200",
        date(2026, 7, 14),
        "hospedagem",
        "Pousada 1 noite",
        "Pousada Central",
        Decimal("180.00"),
        tem_nota_fiscal=True,
    )

    resultado = aplicar_limite_diario(hospedagem_barata, CC_PADRAO, [])

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "total"
    assert resultado.valor_reembolsavel == Decimal("180.00")
    assert "total" in resultado.justificativa


def test_rn015_limite_diario_agrega_o_valor_em_brl():
    # EUR 22,00 pela taxa 5,93 = R$130,46, contra o limite de R$90,00 de CC-COMERCIAL.
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
    cc_comercial = tabela("CC-COMERCIAL", alimentacao="90.00")

    resultado = aplicar_limite_diario(e002, cc_comercial, [])

    # Se o limite fosse comparado com o valor lançado, 22,00 caberia em R$90,00
    # e a despesa reembolsaria "total" — o que sairia em euros.
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == Decimal("90.00")


def test_rn012_sem_adicional_de_viagem():
    almoco_acima_do_limite = construir_despesa(
        "d-400",
        date(2026, 7, 14),
        "alimentacao",
        "Almoco em viagem",
        "Restaurante do Hotel",
        Decimal("90.00"),
        tem_nota_fiscal=True,
    )
    corrida_acima_do_limite = construir_despesa(
        "d-401",
        date(2026, 7, 14),
        "transporte_urbano",
        "Corrida em viagem",
        "TaxiApp",
        Decimal("120.00"),
        tem_nota_fiscal=True,
    )

    resultado_alimentacao = aplicar_limite_diario(almoco_acima_do_limite, CC_PADRAO, [])
    resultado_transporte = aplicar_limite_diario(corrida_acima_do_limite, CC_PADRAO, [])

    # Os valores sao os limites do padrao ampliados em 50% (60 -> 90, 80 -> 120):
    # se o adicional fosse aplicado, ambos virariam reembolso total.
    assert resultado_alimentacao.tipo_reembolso == "parcial"
    assert resultado_alimentacao.valor_reembolsavel == Decimal("60.00")
    assert resultado_transporte.tipo_reembolso == "parcial"
    assert resultado_transporte.valor_reembolsavel == Decimal("80.00")


def test_amb014_despesa_internacional_nao_amplia_limite():
    # USD 12,00 em 2026-07-21 pela taxa 5,48 = R$65,76, e um almoço em BRL de
    # mesmo valor no mesmo dia e categoria.
    internacional = construir_despesa(
        "d-900",
        date(2026, 7, 21),
        "alimentacao",
        "Almoco no exterior",
        "Fornecedor Teste",
        Decimal("12.00"),
        tem_nota_fiscal=True,
        moeda="USD",
        moeda_original="USD",
        valor_brl=Decimal("65.76"),
        taxa_cambio=Decimal("5.48"),
    )
    nacional = construir_despesa(
        "d-901",
        date(2026, 7, 21),
        "alimentacao",
        "Almoco no pais",
        "Fornecedor Teste",
        Decimal("65.76"),
        tem_nota_fiscal=True,
    )

    resultado_internacional = aplicar_limite_diario(internacional, CC_PADRAO, [])
    resultado_nacional = aplicar_limite_diario(nacional, CC_PADRAO, [])

    # Moeda estrangeira não caracteriza viagem: o limite é o mesmo R$60,00 nos
    # dois casos, e nenhum dos dois recebe os R$90,00 do adicional.
    assert resultado_internacional.valor_reembolsavel == Decimal("60.00")
    assert resultado_nacional.valor_reembolsavel == Decimal("60.00")
    assert resultado_internacional.tipo_reembolso == resultado_nacional.tipo_reembolso == "parcial"
