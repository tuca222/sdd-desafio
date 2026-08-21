from datetime import date
from decimal import Decimal

from src.cambio import TabelaCambio
from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.motor import aplicar_filtros, aplicar_limites, calcular
from src.parser import carregar_despesas
from src.politica import Politica, TabelaLimites
from src.regras import (
    filtro_cambio_indisponivel,
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
)
from tests.conftest import CAMINHO_EXEMPLO, ExemploProcessado, construir_despesa
from tests.test_regras import CC_PADRAO, TETO_NOTA_FISCAL, tabela

CAMINHO_ENVELOPE = "exemplos/envelope/despesas-envelope.json"

PERIODO_JULHO_2026 = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))


def processar(
    despesas: list[Despesa],
    tabela_limites: TabelaLimites = CC_PADRAO,
    periodo: Periodo = PERIODO_JULHO_2026,
) -> list[ResultadoDespesa]:
    filtros = aplicar_filtros(despesas, periodo, tabela_limites, TETO_NOTA_FISCAL)
    return aplicar_limites(despesas, filtros.resultados, tabela_limites)


def test_pipeline_aplica_filtros_na_ordem_definida(exemplo: ExemploProcessado):
    despesas = exemplo.despesas
    resultados = exemplo.resultados_filtros
    tabela_do_lote = exemplo.tabela

    assert resultados["d-009"] == filtro_valor_negativo(despesas["d-009"])
    assert resultados["d-005"] == filtro_categoria_invalida(despesas["d-005"], tabela_do_lote)
    assert resultados["d-008"] == filtro_fora_periodo(despesas["d-008"], exemplo.periodo)
    assert resultados["d-007"] == filtro_duplicata(despesas["d-007"], [despesas["d-006"]])

    # d-004 tem nota fiscal ausente E o limite diario de d-003 ja consumido (AMB-004):
    # a justificativa tem de ser a da nota fiscal, nao a do limite diario.
    assert resultados["d-004"] == filtro_nota_fiscal(despesas["d-004"], exemplo.teto_nota_fiscal)

    # d-013 e hospedagem sem nota fiscal em CC-ENG-PLATAFORMA, que veda a categoria:
    # RN-008 e o passo 2 e RN-005 e o passo 6, entao quem responde e a categoria.
    assert resultados["d-013"] == filtro_categoria_invalida(despesas["d-013"], tabela_do_lote)
    assert resultados["d-013"] != filtro_nota_fiscal(despesas["d-013"], exemplo.teto_nota_fiscal)


def test_pipeline_poe_o_cambio_entre_a_duplicata_e_a_nota_fiscal(
    politica: Politica, cambio: TabelaCambio
):
    _, periodo, despesas = carregar_despesas(CAMINHO_ENVELOPE, cambio)
    por_id = {despesa.id: despesa for despesa in despesas}
    cc_comercial = politica.tabela_para("CC-COMERCIAL")

    filtros = aplicar_filtros(despesas, periodo, cc_comercial, TETO_NOTA_FISCAL)
    resultados = dict(zip(list(por_id), filtros.resultados, strict=True))

    # e-004 (EUR num sabado) e e-006 (GBP) sao negadas pelo passo 5.
    assert resultados["e-004"] == filtro_cambio_indisponivel(por_id["e-004"])
    assert resultados["e-006"] == filtro_cambio_indisponivel(por_id["e-006"])

    # e-005 (USD 40,00 = R$220,00, sem nota) tem taxa: passa do passo 5 para o 6.
    assert filtro_cambio_indisponivel(por_id["e-005"]) is None
    assert resultados["e-005"] == filtro_nota_fiscal(por_id["e-005"], TETO_NOTA_FISCAL)


def test_pipeline_deixa_sobreviventes_para_a_agregacao_de_limite(exemplo: ExemploProcessado):
    sobreviventes = [
        id_despesa
        for id_despesa, resultado in exemplo.resultados_filtros.items()
        if resultado is None
    ]

    # d-010 e d-013 sairam da lista com a v4: hospedagem e vedada em
    # CC-ENG-PLATAFORMA, entao as duas param no passo 2 e nem chegam ao limite.
    assert sobreviventes == [
        "d-001",
        "d-002",
        "d-003",
        "d-006",
        "d-011",
        "d-012",
        "d-014",
    ]


def test_rn003_hospedagem_compartilha_limite_diario_no_mesmo_dia():
    primeira = construir_despesa(
        "d-300",
        date(2026, 7, 14),
        "hospedagem",
        "Hotel noite 1",
        "Hotel Copa Sul",
        Decimal("480.00"),
        tem_nota_fiscal=True,
    )
    segunda = construir_despesa(
        "d-301",
        date(2026, 7, 14),
        "hospedagem",
        "Hotel noite 2",
        "Outro Hotel",
        Decimal("300.00"),
        tem_nota_fiscal=True,
    )

    resultados = processar([primeira, segunda])

    assert resultados[0].tipo_reembolso == "parcial"
    assert resultados[0].valor_reembolsavel == Decimal("250.00")
    assert resultados[1].tipo_reembolso == "nenhum"
    assert resultados[1].valor_reembolsavel == Decimal("0.00")
    assert "Hotel noite 1(d-300)" in resultados[1].justificativa


def test_rn003_hospedagem_em_dias_diferentes_tem_limite_proprio():
    despesas = [
        construir_despesa(
            "d-310",
            date(2026, 7, 14),
            "hospedagem",
            "Hotel dia 14",
            "Hotel Copa Sul",
            Decimal("480.00"),
            tem_nota_fiscal=True,
        ),
        construir_despesa(
            "d-311",
            date(2026, 7, 15),
            "hospedagem",
            "Hotel dia 15",
            "Hotel Copa Sul",
            Decimal("480.00"),
            tem_nota_fiscal=True,
        ),
    ]

    resultados = processar(despesas)

    assert resultados[0].valor_reembolsavel == Decimal("250.00")
    assert resultados[1].valor_reembolsavel == Decimal("250.00")


def test_rn014_o_mesmo_lote_muda_de_resultado_com_a_tabela_do_centro_de_custo():
    despesas = [
        construir_despesa(
            "d-320",
            date(2026, 7, 14),
            "alimentacao",
            "Almoco",
            "Bistro Central",
            Decimal("72.50"),
            tem_nota_fiscal=True,
        )
    ]

    no_padrao = processar(despesas, CC_PADRAO)
    em_comercial = processar(despesas, tabela("CC-COMERCIAL", alimentacao="90.00"))

    assert no_padrao[0].valor_reembolsavel == Decimal("60.00")
    assert em_comercial[0].valor_reembolsavel == Decimal("72.50")


def test_rn012_hospedagem_no_periodo_nao_amplia_limites():
    despesas = [
        construir_despesa(
            "d-500",
            date(2026, 7, 14),
            "hospedagem",
            "Hotel - viagem a trabalho",
            "Hotel Copa Sul",
            Decimal("200.00"),
            tem_nota_fiscal=True,
        ),
        construir_despesa(
            "d-501",
            date(2026, 7, 14),
            "alimentacao",
            "Jantar durante a viagem",
            "Restaurante do Hotel",
            Decimal("90.00"),
            tem_nota_fiscal=True,
        ),
        construir_despesa(
            "d-502",
            date(2026, 7, 14),
            "transporte_urbano",
            "Corrida durante a viagem",
            "TaxiApp",
            Decimal("120.00"),
            tem_nota_fiscal=True,
        ),
    ]

    resultados = processar(despesas)

    assert resultados[1].valor_reembolsavel == Decimal("60.00")
    assert resultados[2].valor_reembolsavel == Decimal("80.00")


def test_pipeline_da_uma_unica_justificativa_por_despesa(exemplo: ExemploProcessado):
    assert len(exemplo.resultados_filtros) == len(exemplo.despesas)
    for resultado in exemplo.resultados_filtros.values():
        if resultado is not None:
            assert resultado.tipo_reembolso == "nenhum"
            assert "negado" in resultado.justificativa