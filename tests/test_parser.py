from datetime import date
from decimal import Decimal

from src.modelos import Colaborador, Despesa, Periodo
from src.parser import carregar_despesas

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"


def buscar_despesa(despesas: list[Despesa], id_despesa: str) -> Despesa:
    return next(despesa for despesa in despesas if despesa.id == id_despesa)


def test_parse_carrega_campos_da_entrada():
    colaborador, periodo, despesas = carregar_despesas(CAMINHO_EXEMPLO)

    assert isinstance(colaborador, Colaborador)
    assert colaborador.id == "c-0417"
    assert colaborador.nome == "Marina Volpi"
    assert colaborador.centro_custo == "CC-ENG-PLATAFORMA"

    assert isinstance(periodo, Periodo)
    assert periodo.competencia == "2026-07"
    assert periodo.inicio == date(2026, 7, 1)
    assert periodo.fim == date(2026, 7, 31)

    assert len(despesas) == 14

    d001 = despesas[0]
    assert isinstance(d001, Despesa)
    assert d001.id == "d-001"
    assert d001.data == date(2026, 7, 3)
    assert d001.categoria == "alimentacao"
    assert d001.descricao == "Almoco com cliente"
    assert d001.fornecedor == "Restaurante Tavola"
    assert d001.valor == Decimal("72.50")
    assert isinstance(d001.valor, Decimal)
    assert d001.tem_nota_fiscal is True

    d009 = buscar_despesa(despesas, "d-009")
    assert d009.valor == Decimal("-45.00")
    assert d009.tem_nota_fiscal is False


def test_rn010_trunca_casas_decimais_excedentes():
    _, _, despesas = carregar_despesas(CAMINHO_EXEMPLO)

    d011 = buscar_despesa(despesas, "d-011")

    assert d011.valor == Decimal("33.33")
