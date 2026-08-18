import json
from datetime import date
from decimal import Decimal

from src.modelos import Colaborador, Despesa, Periodo, ResultadoDespesa, ResultadoFinal
from src.parser import carregar_despesas
from src.saida import montar_saida

COLABORADOR = Colaborador(id="c-0417", nome="Marina Volpi", centro_custo="CC-ENG-PLATAFORMA")
PERIODO = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

DESPESA_MAIUSCULA = Despesa(
    id="d-014",
    data=date(2026, 7, 31),
    categoria="alimentacao",
    categoria_original="ALIMENTACAO",
    descricao="Jantar de encerramento",
    fornecedor="Restaurante Tavola",
    valor=Decimal("61.00"),
    valor_original=Decimal("61.00"),
    tem_nota_fiscal=True,
)
RESULTADO_PARCIAL = ResultadoDespesa(
    despesa_reembolsavel=True,
    tipo_reembolso="parcial",
    valor_reembolsavel=Decimal("60.00"),
    justificativa="A categoria alimentacao possui limite de reembolso de R$60,00 no dia.",
)


def montar_resultado_final() -> ResultadoFinal:
    return ResultadoFinal(
        colaborador=COLABORADOR,
        periodo=PERIODO,
        valor_total_despesas=Decimal("61.00"),
        valor_total_reembolsavel=Decimal("60.00"),
        detalhamento=[(DESPESA_MAIUSCULA, RESULTADO_PARCIAL)],
    )


def test_monta_saida_conforme_schema():
    saida = montar_saida(montar_resultado_final())

    assert set(saida) == {
        "colaborador",
        "periodo",
        "valor_total_despesas",
        "valor_total_reembolsavel",
        "detalhamento_despesas",
    }
    assert saida["colaborador"] == {
        "id": "c-0417",
        "nome": "Marina Volpi",
        "centro_custo": "CC-ENG-PLATAFORMA",
    }
    assert saida["periodo"] == {
        "competencia": "2026-07",
        "inicio": "2026-07-01",
        "fim": "2026-07-31",
    }
    assert saida["valor_total_despesas"] == 61.00
    assert saida["valor_total_reembolsavel"] == 60.00

    (item,) = saida["detalhamento_despesas"]

    assert set(item) == {
        "id",
        "data",
        "categoria",
        "descricao",
        "fornecedor",
        "valor",
        "tem_nota_fiscal",
        "motor_reembolso_output",
    }
    assert item["id"] == "d-014"
    assert item["data"] == "2026-07-31"
    assert item["descricao"] == "Jantar de encerramento"
    assert item["fornecedor"] == "Restaurante Tavola"
    assert item["valor"] == 61.00
    assert item["tem_nota_fiscal"] is True
    assert item["motor_reembolso_output"] == {
        "despesa_reembolsavel": True,
        "tipo_reembolso": "parcial",
        "valor_reembolsavel": 60.00,
        "justificativa": (
            "A categoria alimentacao possui limite de reembolso de R$60,00 no dia."
        ),
    }


def test_saida_ecoa_a_categoria_como_veio_na_entrada():
    saida = montar_saida(montar_resultado_final())

    (item,) = saida["detalhamento_despesas"]

    assert item["categoria"] == "ALIMENTACAO"
    assert item["categoria"] == DESPESA_MAIUSCULA.categoria_original
    assert item["categoria"] != DESPESA_MAIUSCULA.categoria


def test_saida_ecoa_o_valor_como_veio_na_entrada():
    _, _, despesas = carregar_despesas("exemplos/despesas-exemplo.json")
    d011 = next(despesa for despesa in despesas if despesa.id == "d-011")

    assert d011.valor_original == Decimal("33.333")
    assert d011.valor == Decimal("33.33")

    resultado_final = ResultadoFinal(
        colaborador=COLABORADOR,
        periodo=PERIODO,
        valor_total_despesas=d011.valor,
        valor_total_reembolsavel=d011.valor,
        detalhamento=[
            (
                d011,
                ResultadoDespesa(
                    despesa_reembolsavel=True,
                    tipo_reembolso="total",
                    valor_reembolsavel=d011.valor,
                    justificativa="Reembolso total aprovado de acordo com a política vigente.",
                ),
            )
        ],
    )

    (item,) = montar_saida(resultado_final)["detalhamento_despesas"]

    # O valor lancado sai inteiro; tudo que e calculado sai truncado em 2 casas.
    assert item["valor"] == 33.333
    assert item["motor_reembolso_output"]["valor_reembolsavel"] == 33.33


def test_saida_converte_decimal_para_numero_serializavel():
    saida = montar_saida(montar_resultado_final())

    assert isinstance(saida["valor_total_despesas"], float)
    assert isinstance(saida["valor_total_reembolsavel"], float)

    (item,) = saida["detalhamento_despesas"]
    assert isinstance(item["valor"], float)
    assert isinstance(item["motor_reembolso_output"]["valor_reembolsavel"], float)

    # json.dumps falharia com Decimal — e a prova de que a conversao aconteceu.
    assert json.loads(json.dumps(saida)) == saida
