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


def test_pipeline_da_uma_unica_justificativa_por_despesa(exemplo: ExemploProcessado):
    assert len(exemplo.resultados_filtros) == len(exemplo.despesas)
    for resultado in exemplo.resultados_filtros.values():
        if resultado is not None:
            assert resultado.tipo_reembolso == "nenhum"
            assert "negado" in resultado.justificativa