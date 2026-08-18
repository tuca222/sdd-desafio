from dataclasses import replace
from datetime import date
from decimal import Decimal

from src.motor import aplicar_filtros, aplicar_limites
from src.politica import LIMITE_NOTA_FISCAL, LIMITE_TRANSPORTE_URBANO
from src.regras import aplicar_limite_diario, filtro_nota_fiscal
from tests.conftest import ExemploProcessado

SABADO = 5


def test_valor_exatamente_no_limite_nota_fiscal(exemplo: ExemploProcessado):
    d003 = exemplo.despesas["d-003"]

    assert d003.valor == LIMITE_NOTA_FISCAL
    assert d003.tem_nota_fiscal is False
    assert filtro_nota_fiscal(d003) is None

    resultado = exemplo.resultados["d-003"]

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == Decimal("80.00")


def test_ordem_nota_fiscal_antes_de_limite_diario(exemplo: ExemploProcessado):
    d003 = exemplo.despesas["d-003"]
    d004 = exemplo.despesas["d-004"]

    assert d004.data == d003.data
    assert d004.categoria == d003.categoria
    assert exemplo.resultados["d-003"].valor_reembolsavel == LIMITE_TRANSPORTE_URBANO

    resultado_d004 = exemplo.resultados["d-004"]
    reprovacao_por_limite_diario = aplicar_limite_diario(
        d004, LIMITE_TRANSPORTE_URBANO, [(d003, LIMITE_TRANSPORTE_URBANO)]
    )

    assert resultado_d004 == filtro_nota_fiscal(d004)
    assert resultado_d004 != reprovacao_por_limite_diario
    assert "nota fiscal" in resultado_d004.justificativa


def test_despesa_fim_de_semana_sem_regra_especial(exemplo: ExemploProcessado):
    d012 = exemplo.despesas["d-012"]

    assert d012.data.weekday() >= SABADO

    resultado = exemplo.resultados["d-012"]

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "total"
    assert resultado.valor_reembolsavel == d012.valor

    no_fim_de_semana = replace(d012, id="d-012-sabado")
    em_dia_util = replace(d012, id="d-012-quinta", data=date(2026, 7, 16))
    assert em_dia_util.data.weekday() < SABADO

    despesas = [no_fim_de_semana, em_dia_util]
    resultados = aplicar_limites(despesas, aplicar_filtros(despesas, exemplo.periodo))

    assert resultados[0] == resultados[1]
