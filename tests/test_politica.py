from dataclasses import replace
from datetime import date
from decimal import Decimal

from src.politica import LimiteCategoria, carregar_politica

CAMINHO_POLITICA = "exemplos/envelope/politica-v4.json"


def test_carrega_politica_com_valores_decimais():
    politica = carregar_politica(CAMINHO_POLITICA)

    assert politica.vigencia == date(2026, 7, 1)

    assert politica.nota_fiscal_obrigatoria_acima_de == Decimal("100.00")
    assert isinstance(politica.nota_fiscal_obrigatoria_acima_de, Decimal)

    assert politica.tabela_padrao["alimentacao"] == LimiteCategoria(
        limite=Decimal("60.00"), periodicidade="dia"
    )
    assert politica.tabela_padrao["transporte_urbano"].limite == Decimal("80.00")
    assert politica.tabela_padrao["hospedagem"].limite == Decimal("250.00")

    eng = politica.tabela_por_centro_custo["CC-ENG-PLATAFORMA"]
    assert eng["alimentacao"].limite == Decimal("75.00")
    assert eng["hospedagem"].limite == Decimal("0.00")
    assert isinstance(eng["hospedagem"].limite, Decimal)

    comercial = politica.tabela_por_centro_custo["CC-COMERCIAL"]
    assert comercial["representacao"].limite == Decimal("300.00")


def test_observacao_da_politica_nao_entra_no_modelo():
    politica = carregar_politica(CAMINHO_POLITICA)

    hospedagem = politica.tabela_por_centro_custo["CC-ENG-PLATAFORMA"]["hospedagem"]

    # spec.md §4 ("Entrada e saída"): `observacao` não é lida pelo motor. plan.md §3
    # ("Modelo de dados"): campo que existe no modelo acaba sendo lido por alguém.
    assert not hasattr(hospedagem, "observacao")


def test_rn014_centro_custo_com_entrada_usa_a_propria_tabela():
    politica = carregar_politica(CAMINHO_POLITICA)

    tabela = politica.tabela_para("CC-ENG-PLATAFORMA")

    assert tabela.centro_custo == "CC-ENG-PLATAFORMA"
    assert tabela.limites["alimentacao"].limite == Decimal("75.00")
    # O padrão traz R$60,00 para a mesma categoria, e ele não é usado aqui.
    assert politica.tabela_padrao["alimentacao"].limite == Decimal("60.00")


def test_rn014_centro_custo_sem_entrada_cai_no_padrao():
    politica = carregar_politica(CAMINHO_POLITICA)

    tabela = politica.tabela_para("CC-SUPORTE-N2")

    assert tabela.centro_custo == "CC-SUPORTE-N2"
    assert tabela.limites == politica.tabela_padrao
    assert tabela.limites["alimentacao"].limite == Decimal("60.00")
    assert tabela.limites["hospedagem"].limite == Decimal("250.00")


def test_amb012_tabela_do_centro_custo_nao_e_complementada_pelo_padrao():
    politica = carregar_politica(CAMINHO_POLITICA)

    # CC-ADM existe em `centros_custo` e não lista `hospedagem`.
    tabela = politica.tabela_para("CC-ADM")

    assert "hospedagem" in politica.tabela_padrao
    assert "hospedagem" not in tabela.limites
    assert set(tabela.limites) == {"alimentacao", "transporte_urbano"}


def test_rn017_vigencia_da_competencia_do_lote_cobre():
    politica = carregar_politica(CAMINHO_POLITICA)

    assert politica.competencia_de_vigencia == "2026-07"
    assert politica.vigencia_cobre("2026-07") is True


def test_rn017_vigencia_de_competencia_anterior_cobre():
    politica = carregar_politica(CAMINHO_POLITICA)

    # A política de julho continua valendo em agosto se não houver política nova.
    assert politica.vigencia_cobre("2026-08") is True
    assert politica.vigencia_cobre("2027-01") is True


def test_rn017_vigencia_de_competencia_posterior_nao_cobre():
    politica = carregar_politica(CAMINHO_POLITICA)

    # Junho tem de ser processado com a política que valia em junho.
    assert politica.vigencia_cobre("2026-06") is False
    assert politica.vigencia_cobre("2025-12") is False


def test_rn017_vigencia_no_meio_do_mes_cobre_a_competencia_inteira():
    politica = carregar_politica(CAMINHO_POLITICA)
    quinze_de_julho = replace(politica, vigencia=date(2026, 7, 15))

    # AMB-020: a comparação é entre competências, não entre datas — uma vigência
    # de 15/07 cobre o lote de 2026-07 inteiro, inclusive as despesas anteriores.
    assert quinze_de_julho.competencia_de_vigencia == "2026-07"
    assert quinze_de_julho.vigencia_cobre("2026-07") is True
