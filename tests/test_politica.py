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