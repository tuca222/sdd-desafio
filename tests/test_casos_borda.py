from dataclasses import replace
from datetime import date
from decimal import Decimal

from src.motor import aplicar_filtros, aplicar_limites
from src.politica import LimiteCategoria, TabelaLimites
from src.regras import aplicar_limite_diario, filtro_categoria_invalida, normalizar_categoria
from tests.conftest import ExemploProcessado

SABADO = 5

LIMITE_ALIMENTACAO_ENG = Decimal("75.00")
LIMITE_TRANSPORTE_ENG = Decimal("80.00")


def processar(despesas, exemplo: ExemploProcessado):
    filtros = aplicar_filtros(despesas, exemplo.periodo, exemplo.tabela, exemplo.teto_nota_fiscal)
    return aplicar_limites(despesas, filtros.resultados, exemplo.tabela)


def test_valor_exatamente_no_limite_nota_fiscal(exemplo: ExemploProcessado):
    d003 = exemplo.despesas["d-003"]

    assert d003.valor_brl == exemplo.teto_nota_fiscal
    assert d003.tem_nota_fiscal is False
    assert exemplo.resultados_filtros["d-003"] is None

    resultado = exemplo.resultados["d-003"]

    assert resultado.despesa_reembolsavel is True
    assert resultado.tipo_reembolso == "parcial"
    assert resultado.valor_reembolsavel == LIMITE_TRANSPORTE_ENG


def test_ordem_nota_fiscal_antes_de_limite_diario(exemplo: ExemploProcessado):
    d003 = exemplo.despesas["d-003"]
    d004 = exemplo.despesas["d-004"]

    assert d004.data == d003.data
    assert d004.categoria == d003.categoria
    assert exemplo.resultados["d-003"].valor_reembolsavel == LIMITE_TRANSPORTE_ENG

    resultado_d004 = exemplo.resultados["d-004"]
    reprovacao_por_limite_diario = aplicar_limite_diario(
        d004, exemplo.tabela, [(d003, LIMITE_TRANSPORTE_ENG)]
    )

    assert resultado_d004 != reprovacao_por_limite_diario
    assert "nota fiscal" in resultado_d004.justificativa
    assert "já foi atingido" not in resultado_d004.justificativa


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

    resultados = processar([no_fim_de_semana, em_dia_util], exemplo)

    assert resultados[0] == resultados[1]


def test_hospedagem_multi_diaria_sem_campo_estruturado(exemplo: ExemploProcessado):
    d010 = exemplo.despesas["d-010"]
    d013 = exemplo.despesas["d-013"]

    assert "2 diarias" in d010.descricao
    assert "3 noites" in d013.descricao

    # Em CC-ENG-PLATAFORMA a hospedagem e vedada (limite R$0,00): as duas param no
    # passo 2 da ordem, e o numero de noites do texto livre nao muda nada disso.
    assert exemplo.resultados["d-010"] == filtro_categoria_invalida(d010, exemplo.tabela)
    assert exemplo.resultados["d-013"] == filtro_categoria_invalida(d013, exemplo.tabela)

    variantes = [
        replace(d010, id="d-010-sem-mencao", descricao="Hotel Rio"),
        replace(d010, id="d-010-dez-diarias", descricao="Hotel Rio - 10 diarias"),
    ]
    resultados_variantes = [processar([variante], exemplo)[0] for variante in variantes]

    assert resultados_variantes[0].justificativa == resultados_variantes[1].justificativa
    assert resultados_variantes[0].valor_reembolsavel == Decimal("0.00")


def test_hospedagem_multi_diaria_disputa_o_limite_de_um_unico_dia(exemplo: ExemploProcessado):
    # O mesmo cenario num centro de custo que reembolsa hospedagem: f-002 cobre
    # uma diaria de R$310,00 contra o limite de R$250,00 do padrao (RN-003, AMB-006).
    padrao = TabelaLimites(
        centro_custo="CC-SUPORTE-N2",
        limites={"hospedagem": LimiteCategoria(limite=Decimal("250.00"), periodicidade="diaria")},
    )
    duas_noites = replace(
        exemplo.despesas["d-010"],
        id="d-010-duas-noites",
        valor=Decimal("480.00"),
        valor_brl=Decimal("480.00"),
    )

    resultado = aplicar_limite_diario(duas_noites, padrao, [])

    # O limite nunca e multiplicado pelo numero de noites.
    assert resultado.valor_reembolsavel == Decimal("250.00")
    assert resultado.valor_reembolsavel != 2 * Decimal("250.00")


def test_categoria_maiuscula_concorre_ao_limite_diario(exemplo: ExemploProcessado):
    d014 = exemplo.despesas["d-014"]

    assert d014.categoria_original == "ALIMENTACAO"
    assert d014.categoria == normalizar_categoria("ALIMENTACAO")

    resultado = exemplo.resultados["d-014"]

    # Sob o limite de R$75,00 de CC-ENG-PLATAFORMA os R$61,00 cabem inteiros.
    assert resultado.tipo_reembolso == "total"
    assert resultado.valor_reembolsavel == Decimal("61.00")

    lancada_em_minusculas = replace(
        d014,
        id="d-014-minuscula",
        categoria_original="alimentacao",
        descricao="Almoco",
        valor=Decimal("30.00"),
        valor_original=Decimal("30.00"),
        valor_brl=Decimal("30.00"),
    )
    resultados = processar([lancada_em_minusculas, d014], exemplo)

    assert resultados[0].tipo_reembolso == "total"
    assert resultados[0].valor_reembolsavel == Decimal("30.00")

    # Sem dividir o balde com a grafia minuscula, d-014 levaria os R$61,00 inteiros.
    assert resultados[1].tipo_reembolso == "parcial"
    assert resultados[1].valor_reembolsavel == LIMITE_ALIMENTACAO_ENG - Decimal("30.00")
    assert "alimentacao" in resultados[1].justificativa
