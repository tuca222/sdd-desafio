from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo
from src.motor import aplicar_filtros, aplicar_limites, calcular
from src.parser import carregar_despesas
from src.regras import (
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
)
from tests.conftest import ExemploProcessado


def test_pipeline_aplica_filtros_na_ordem_definida(exemplo: ExemploProcessado):
    despesas = exemplo.despesas
    resultados = exemplo.resultados_filtros

    assert resultados["d-009"] == filtro_valor_negativo(despesas["d-009"])
    assert resultados["d-005"] == filtro_categoria_invalida(despesas["d-005"])
    assert resultados["d-008"] == filtro_fora_periodo(despesas["d-008"], exemplo.periodo)
    assert resultados["d-007"] == filtro_duplicata(despesas["d-007"], [despesas["d-006"]])

    # d-004 tem nota fiscal ausente E o limite diario de d-003 ja consumido (AMB-004):
    # a justificativa tem de ser a da nota fiscal, nao a do limite diario.
    assert resultados["d-004"] == filtro_nota_fiscal(despesas["d-004"])
    assert resultados["d-013"] == filtro_nota_fiscal(despesas["d-013"])


def test_pipeline_deixa_sobreviventes_para_a_agregacao_de_limite(exemplo: ExemploProcessado):
    sobreviventes = [
        id_despesa
        for id_despesa, resultado in exemplo.resultados_filtros.items()
        if resultado is None
    ]

    assert sobreviventes == [
        "d-001",
        "d-002",
        "d-003",
        "d-006",
        "d-010",
        "d-011",
        "d-012",
        "d-014",
    ]


def test_rn003_hospedagem_compartilha_limite_diario_no_mesmo_dia():
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    primeira = Despesa(
        id="d-300",
        data=date(2026, 7, 14),
        categoria="hospedagem",
        categoria_original="hospedagem",
        descricao="Hotel noite 1",
        fornecedor="Hotel Copa Sul",
        valor=Decimal("480.00"),
        valor_original=Decimal("480.00"),
        tem_nota_fiscal=True,
    )
    segunda = Despesa(
        id="d-301",
        data=date(2026, 7, 14),
        categoria="hospedagem",
        categoria_original="hospedagem",
        descricao="Hotel noite 2",
        fornecedor="Outro Hotel",
        valor=Decimal("300.00"),
        valor_original=Decimal("300.00"),
        tem_nota_fiscal=True,
    )
    despesas = [primeira, segunda]

    resultados = aplicar_limites(despesas, aplicar_filtros(despesas, periodo).resultados)

    assert resultados[0].tipo_reembolso == "parcial"
    assert resultados[0].valor_reembolsavel == Decimal("250.00")
    assert resultados[1].tipo_reembolso == "nenhum"
    assert resultados[1].valor_reembolsavel == Decimal("0.00")
    assert "Hotel noite 1(d-300)" in resultados[1].justificativa


def test_rn003_hospedagem_em_dias_diferentes_tem_limite_proprio():
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    despesas = [
        Despesa(
            id="d-310",
            data=date(2026, 7, 14),
            categoria="hospedagem",
            categoria_original="hospedagem",
            descricao="Hotel dia 14",
            fornecedor="Hotel Copa Sul",
            valor=Decimal("480.00"),
            valor_original=Decimal("480.00"),
            tem_nota_fiscal=True,
        ),
        Despesa(
            id="d-311",
            data=date(2026, 7, 15),
            categoria="hospedagem",
            categoria_original="hospedagem",
            descricao="Hotel dia 15",
            fornecedor="Hotel Copa Sul",
            valor=Decimal("480.00"),
            valor_original=Decimal("480.00"),
            tem_nota_fiscal=True,
        ),
    ]

    resultados = aplicar_limites(despesas, aplicar_filtros(despesas, periodo).resultados)

    assert resultados[0].valor_reembolsavel == Decimal("250.00")
    assert resultados[1].valor_reembolsavel == Decimal("250.00")


def test_rn012_hospedagem_no_periodo_nao_amplia_limites():
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    despesas = [
        Despesa(
            id="d-500",
            data=date(2026, 7, 14),
            categoria="hospedagem",
            categoria_original="hospedagem",
            descricao="Hotel - viagem a trabalho",
            fornecedor="Hotel Copa Sul",
            valor=Decimal("200.00"),
            valor_original=Decimal("200.00"),
            tem_nota_fiscal=True,
        ),
        Despesa(
            id="d-501",
            data=date(2026, 7, 14),
            categoria="alimentacao",
            categoria_original="alimentacao",
            descricao="Jantar durante a viagem",
            fornecedor="Restaurante do Hotel",
            valor=Decimal("90.00"),
            valor_original=Decimal("90.00"),
            tem_nota_fiscal=True,
        ),
        Despesa(
            id="d-502",
            data=date(2026, 7, 14),
            categoria="transporte_urbano",
            categoria_original="transporte_urbano",
            descricao="Corrida durante a viagem",
            fornecedor="TaxiApp",
            valor=Decimal("120.00"),
            valor_original=Decimal("120.00"),
            tem_nota_fiscal=True,
        ),
    ]

    resultados = aplicar_limites(despesas, aplicar_filtros(despesas, periodo).resultados)

    assert resultados[1].valor_reembolsavel == Decimal("60.00")
    assert resultados[2].valor_reembolsavel == Decimal("80.00")


def test_pipeline_da_uma_unica_justificativa_por_despesa(exemplo: ExemploProcessado):
    assert len(exemplo.resultados_filtros) == len(exemplo.despesas)
    for resultado in exemplo.resultados_filtros.values():
        if resultado is not None:
            assert resultado.tipo_reembolso == "nenhum"
            assert "negado" in resultado.justificativa


def test_calcula_totais_do_periodo():
    colaborador, periodo, despesas = carregar_despesas("exemplos/despesas-exemplo.json")

    resultado_final = calcular(colaborador, periodo, despesas)

    assert resultado_final.valor_total_despesas == Decimal("1806.94")
    assert resultado_final.valor_total_reembolsavel == Decimal("585.43")

    por_id = {despesa.id: despesa for despesa in despesas}
    soma_de_todas = sum((despesa.valor for despesa in despesas), Decimal("0.00"))

    # O bruto exclui exatamente a duplicata (RN-007) e o estorno (RN-009) — e so eles.
    assert resultado_final.valor_total_despesas == (
        soma_de_todas - por_id["d-007"].valor - por_id["d-009"].valor
    )

    # d-005 (categoria fora da politica) e d-008 (fora do periodo) continuam no bruto.
    assert resultado_final.valor_total_despesas > por_id["d-005"].valor + por_id["d-008"].valor

    assert resultado_final.valor_total_reembolsavel == sum(
        (resultado.valor_reembolsavel for _, resultado in resultado_final.detalhamento),
        Decimal("0.00"),
    )


def test_calcular_preserva_colaborador_periodo_e_ordem_da_entrada():
    colaborador, periodo, despesas = carregar_despesas("exemplos/despesas-exemplo.json")

    resultado_final = calcular(colaborador, periodo, despesas)

    assert resultado_final.colaborador == colaborador
    assert resultado_final.periodo == periodo
    assert [despesa.id for despesa, _ in resultado_final.detalhamento] == [
        despesa.id for despesa in despesas
    ]
