import json
from datetime import date
from decimal import Decimal

import pytest

from src.cambio import TabelaCambio
from src.modelos import Colaborador, Despesa, Periodo, ResultadoDespesa, ResultadoFinal
from src.parser import carregar_despesas
from src.saida import montar_saida
from tests.conftest import CAMINHO_EXEMPLO, construir_despesa

CAMINHO_ENVELOPE = "exemplos/envelope/despesas-envelope.json"

COLABORADOR = Colaborador(id="c-0417", nome="Marina Volpi", centro_custo="CC-ENG-PLATAFORMA")
PERIODO = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))

DESPESA_MAIUSCULA = construir_despesa(
    "d-014",
    date(2026, 7, 31),
    "alimentacao",
    "Jantar de encerramento",
    "Restaurante Tavola",
    Decimal("61.00"),
    tem_nota_fiscal=True,
    categoria_original="ALIMENTACAO",
)
RESULTADO_PARCIAL = ResultadoDespesa(
    despesa_reembolsavel=True,
    tipo_reembolso="parcial",
    valor_reembolsavel=Decimal("60.00"),
    justificativa="A categoria alimentacao possui limite de reembolso de R$60,00 no dia.",
)


def montar_resultado_final(
    despesa: Despesa = DESPESA_MAIUSCULA,
    resultado: ResultadoDespesa = RESULTADO_PARCIAL,
) -> ResultadoFinal:
    return ResultadoFinal(
        colaborador=COLABORADOR,
        periodo=PERIODO,
        valor_total_despesas=Decimal("61.00"),
        valor_total_reembolsavel=Decimal("60.00"),
        detalhamento=[(despesa, resultado)],
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
        "taxa_cambio": None,
        "valor_convertido_brl": None,
        "justificativa": ("A categoria alimentacao possui limite de reembolso de R$60,00 no dia."),
    }


def test_saida_ecoa_a_categoria_como_veio_na_entrada():
    saida = montar_saida(montar_resultado_final())

    (item,) = saida["detalhamento_despesas"]

    assert item["categoria"] == "ALIMENTACAO"
    assert item["categoria"] == DESPESA_MAIUSCULA.categoria_original
    assert item["categoria"] != DESPESA_MAIUSCULA.categoria


def test_saida_ecoa_o_valor_como_veio_na_entrada(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)
    d011 = next(despesa for despesa in despesas if despesa.id == "d-011")

    assert d011.valor_original == Decimal("33.333")
    assert d011.valor == Decimal("33.33")

    resultado_final = montar_resultado_final(
        d011,
        ResultadoDespesa(
            despesa_reembolsavel=True,
            tipo_reembolso="total",
            valor_reembolsavel=d011.valor,
            justificativa="Reembolso total aprovado de acordo com a política vigente.",
        ),
    )

    (item,) = montar_saida(resultado_final)["detalhamento_despesas"]

    # O valor lancado sai inteiro; tudo que e calculado sai truncado em 2 casas.
    assert item["valor"] == Decimal("33.333")
    assert item["motor_reembolso_output"]["valor_reembolsavel"] == Decimal("33.33")


def test_saida_publica_taxa_e_valor_convertido(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_ENVELOPE, cambio)
    e002 = next(despesa for despesa in despesas if despesa.id == "e-002")

    resultado_final = montar_resultado_final(
        e002,
        ResultadoDespesa(
            despesa_reembolsavel=True,
            tipo_reembolso="parcial",
            valor_reembolsavel=Decimal("90.00"),
            justificativa="Reembolso parcial aprovado.",
        ),
    )

    (item,) = montar_saida(resultado_final)["detalhamento_despesas"]
    saida_do_motor = item["motor_reembolso_output"]

    # A conta tem de ser refazivel a partir da saida: valor x taxa = convertido.
    assert item["valor"] == Decimal("22.00")
    assert item["moeda"] == "EUR"
    assert saida_do_motor["taxa_cambio"] == Decimal("5.93")
    assert saida_do_motor["valor_convertido_brl"] == Decimal("130.46")

    # O valor lancado sai na moeda lancada, nunca convertido.
    assert item["valor"] != saida_do_motor["valor_convertido_brl"]


def test_saida_publica_taxa_e_convertido_nulos_para_despesa_em_brl(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_ENVELOPE, cambio)
    e001 = next(despesa for despesa in despesas if despesa.id == "e-001")

    (item,) = montar_saida(montar_resultado_final(e001))["detalhamento_despesas"]

    # e-001 tem valor em BRL (ela ja esta em BRL), e ainda assim os dois campos
    # saem nulos: nao houve conversao nenhuma para publicar.
    assert e001.valor_brl == Decimal("340.00")
    assert item["motor_reembolso_output"]["taxa_cambio"] is None
    assert item["motor_reembolso_output"]["valor_convertido_brl"] is None


def test_rn016_saida_publica_taxa_e_convertido_nulos_sem_cambio(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_ENVELOPE, cambio)
    e004 = next(despesa for despesa in despesas if despesa.id == "e-004")

    (item,) = montar_saida(montar_resultado_final(e004))["detalhamento_despesas"]

    assert item["moeda"] == "EUR"
    assert item["motor_reembolso_output"]["taxa_cambio"] is None
    assert item["motor_reembolso_output"]["valor_convertido_brl"] is None


def test_saida_omite_moeda_quando_a_entrada_nao_trouxe(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_ENVELOPE, cambio)
    por_id = {despesa.id: despesa for despesa in despesas}

    (sem_o_campo,) = montar_saida(montar_resultado_final(por_id["e-010"]))["detalhamento_despesas"]
    (com_brl_explicito,) = montar_saida(montar_resultado_final(por_id["e-001"]))[
        "detalhamento_despesas"
    ]

    # e-010 nao trouxe `moeda` e o motor assumiu BRL para decidir — inventar um
    # "moeda": "BRL" na saida seria reescrever a entrada.
    assert por_id["e-010"].moeda == "BRL"
    assert "moeda" not in sem_o_campo

    # e-001 trouxe o campo, e ele sai com a grafia exata que entrou.
    assert com_brl_explicito["moeda"] == "BRL"


def test_saida_entrega_decimal_sem_passar_por_float():
    saida = montar_saida(montar_resultado_final())

    assert isinstance(saida["valor_total_despesas"], Decimal)
    assert isinstance(saida["valor_total_reembolsavel"], Decimal)

    (item,) = saida["detalhamento_despesas"]
    assert isinstance(item["valor"], Decimal)
    assert isinstance(item["motor_reembolso_output"]["valor_reembolsavel"], Decimal)

    # float nao carrega escala: e por isso que a conversao nao acontece aqui.
    # Quem serializa e o CodificadorMonetario do cli.py (plan.md DT-004).
    with pytest.raises(TypeError):
        json.dumps(saida)


def test_saida_preserva_a_escala_dos_valores_monetarios():
    saida = montar_saida(montar_resultado_final())
    (item,) = saida["detalhamento_despesas"]

    assert str(saida["valor_total_despesas"]) == "61.00"
    assert str(item["valor"]) == "61.00"
    assert str(item["motor_reembolso_output"]["valor_reembolsavel"]) == "60.00"
