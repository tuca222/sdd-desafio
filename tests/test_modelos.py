from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest

from src.modelos import Colaborador, Despesa, Periodo, ResultadoDespesa, ResultadoFinal


def test_colaborador_e_imutavel():
    colaborador = Colaborador(id="c-0417", nome="Marina Volpi", centro_custo="CC-ENG-PLATAFORMA")

    assert colaborador.id == "c-0417"
    with pytest.raises(FrozenInstanceError):
        colaborador.nome = "Outro Nome"


def test_periodo_e_imutavel():
    periodo = Periodo(
        competencia="2026-07",
        inicio=date(2026, 7, 1),
        fim=date(2026, 7, 31),
    )

    assert periodo.inicio == date(2026, 7, 1)
    with pytest.raises(FrozenInstanceError):
        periodo.fim = date(2026, 8, 1)


def test_despesa_e_imutavel():
    despesa = Despesa(
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

    assert despesa.valor == Decimal("72.50")
    with pytest.raises(FrozenInstanceError):
        despesa.valor = Decimal("0.00")


def test_resultado_despesa_e_imutavel():
    resultado = ResultadoDespesa(
        despesa_reembolsavel=True,
        tipo_reembolso="parcial",
        valor_reembolsavel=Decimal("60.00"),
        justificativa="A categoria alimentacao possui limite de reembolso de R$60,00 no dia.",
    )

    assert resultado.tipo_reembolso == "parcial"
    with pytest.raises(FrozenInstanceError):
        resultado.tipo_reembolso = "total"


def test_resultado_final_e_imutavel():
    colaborador = Colaborador(id="c-0417", nome="Marina Volpi", centro_custo="CC-ENG-PLATAFORMA")
    periodo = Periodo(competencia="2026-07", inicio=date(2026, 7, 1), fim=date(2026, 7, 31))
    despesa = Despesa(
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
    resultado_despesa = ResultadoDespesa(
        despesa_reembolsavel=True,
        tipo_reembolso="parcial",
        valor_reembolsavel=Decimal("60.00"),
        justificativa="Reembolso parcial aprovado.",
    )
    resultado_final = ResultadoFinal(
        colaborador=colaborador,
        periodo=periodo,
        valor_total_despesas=Decimal("72.50"),
        valor_total_reembolsavel=Decimal("60.00"),
        detalhamento=[(despesa, resultado_despesa)],
    )

    assert resultado_final.valor_total_reembolsavel == Decimal("60.00")
    with pytest.raises(FrozenInstanceError):
        resultado_final.valor_total_reembolsavel = Decimal("0.00")
