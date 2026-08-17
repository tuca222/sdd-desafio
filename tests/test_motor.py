from src.motor import aplicar_filtros
from src.parser import carregar_despesas
from src.regras import (
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
)

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"


def resultados_por_id(caminho: str = CAMINHO_EXEMPLO):
    _, periodo, despesas = carregar_despesas(caminho)
    resultados = aplicar_filtros(despesas, periodo)
    return (
        {despesa.id: despesa for despesa in despesas},
        dict(zip((despesa.id for despesa in despesas), resultados, strict=True)),
        periodo,
    )


def test_pipeline_aplica_filtros_na_ordem_definida():
    despesas, resultados, periodo = resultados_por_id()

    assert resultados["d-009"] == filtro_valor_negativo(despesas["d-009"])
    assert resultados["d-005"] == filtro_categoria_invalida(despesas["d-005"])
    assert resultados["d-008"] == filtro_fora_periodo(despesas["d-008"], periodo)
    assert resultados["d-007"] == filtro_duplicata(despesas["d-007"], [despesas["d-006"]])

    # d-004 tem nota fiscal ausente E o limite diario de d-003 ja consumido (AMB-004):
    # a justificativa tem de ser a da nota fiscal, nao a do limite diario.
    assert resultados["d-004"] == filtro_nota_fiscal(despesas["d-004"])
    assert resultados["d-013"] == filtro_nota_fiscal(despesas["d-013"])


def test_pipeline_deixa_sobreviventes_para_a_agregacao_de_limite():
    _, resultados, _ = resultados_por_id()

    sobreviventes = [
        id_despesa for id_despesa, resultado in resultados.items() if resultado is None
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


def test_pipeline_da_uma_unica_justificativa_por_despesa():
    despesas, resultados, _ = resultados_por_id()

    assert len(resultados) == len(despesas)
    for resultado in resultados.values():
        if resultado is not None:
            assert resultado.tipo_reembolso == "nenhum"
            assert "negado" in resultado.justificativa
