import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.cambio import TabelaCambio, carregar_cambio
from src.modelos import Colaborador, Despesa, Periodo
from src.parser import carregar_despesas

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"
CAMINHO_ENVELOPE = "exemplos/envelope/despesas-envelope.json"
CAMINHO_CAMBIO = "exemplos/envelope/cambio.json"


@pytest.fixture
def cambio() -> TabelaCambio:
    return carregar_cambio(CAMINHO_CAMBIO)


def buscar_despesa(despesas: list[Despesa], id_despesa: str) -> Despesa:
    return next(despesa for despesa in despesas if despesa.id == id_despesa)


def escrever_entrada(destino: Path, despesa: dict) -> str:
    entrada = json.loads(Path(CAMINHO_EXEMPLO).read_text(encoding="utf-8"))
    entrada["despesas"] = [entrada["despesas"][0] | despesa]
    destino.write_text(json.dumps(entrada), encoding="utf-8")
    return str(destino)


def test_parse_carrega_campos_da_entrada(cambio: TabelaCambio):
    colaborador, periodo, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)

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


def test_rn011_normaliza_categoria_na_borda_de_entrada(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)

    d014 = buscar_despesa(despesas, "d-014")

    assert d014.categoria == "alimentacao"
    assert d014.categoria_original == "ALIMENTACAO"

    # Nenhuma despesa chega ao motor com categoria fora da forma normalizada.
    assert all(despesa.categoria == despesa.categoria.lower() for despesa in despesas)


def test_rn010_trunca_casas_decimais_excedentes(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)

    d011 = buscar_despesa(despesas, "d-011")

    assert d011.valor == Decimal("33.33")


def test_rn015_moeda_ausente_assume_brl(cambio: TabelaCambio):
    _, _, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)

    d001 = buscar_despesa(despesas, "d-001")

    assert d001.moeda == "BRL"
    assert all(despesa.moeda == "BRL" for despesa in despesas)


def test_rn015_moeda_normalizada_para_maiusculas(tmp_path: Path, cambio: TabelaCambio):
    caminho = escrever_entrada(
        tmp_path / "despesas.json",
        {"data": "2026-07-14", "valor": 10.00, "moeda": "eur"},
    )

    _, _, despesas = carregar_despesas(caminho, cambio)

    assert despesas[0].moeda == "EUR"
    assert despesas[0].moeda_original == "eur"
    # A forma normalizada é a que decide: a taxa de EUR em 2026-07-14 foi encontrada.
    assert despesas[0].taxa_cambio == Decimal("5.93")


def test_rn015_moeda_original_preservada_como_none_quando_ausente(
    tmp_path: Path, cambio: TabelaCambio
):
    _, _, do_exemplo = carregar_despesas(CAMINHO_EXEMPLO, cambio)
    _, _, do_envelope = carregar_despesas(CAMINHO_ENVELOPE, cambio)

    # Nenhuma despesa do exemplo traz o campo `moeda`.
    assert buscar_despesa(do_exemplo, "d-001").moeda_original is None

    # e-010 também não traz; e-001 traz "BRL" explícito. As duas são tratadas
    # como BRL, e é `moeda_original` que separa o que a saída pode ecoar.
    e010 = buscar_despesa(do_envelope, "e-010")
    e001 = buscar_despesa(do_envelope, "e-001")

    assert e010.moeda == e001.moeda == "BRL"
    assert e010.moeda_original is None
    assert e001.moeda_original == "BRL"