import json
from datetime import date
from decimal import ROUND_DOWN, Decimal
from typing import Any

from src.modelos import Colaborador, Despesa, Periodo
from src.regras import normalizar_categoria

DUAS_CASAS_DECIMAIS = Decimal("0.01")

# Fixado pelo texto da política ("os limites da política são sempre em BRL"), não
# pelo campo `moeda_base` dos arquivos de entrada — ver spec.md §4 ("Entrada e saída").
MOEDA_BASE = "BRL"


def _truncar_valor(valor: Decimal) -> Decimal:
    return valor.quantize(DUAS_CASAS_DECIMAIS, rounding=ROUND_DOWN)


def normalizar_moeda(moeda: str) -> str:
    return moeda.upper()


def _construir_despesa(item: dict[str, Any]) -> Despesa:
    data = date.fromisoformat(item["data"])
    moeda_original = item.get("moeda")
    moeda = normalizar_moeda(moeda_original) if moeda_original is not None else MOEDA_BASE
    valor = _truncar_valor(item["valor"])

    return Despesa(
        id=item["id"],
        data=data,
        categoria=normalizar_categoria(item["categoria"]),
        categoria_original=item["categoria"],
        descricao=item["descricao"],
        fornecedor=item["fornecedor"],
        valor=valor,
        valor_original=item["valor"],
        moeda=moeda,
        moeda_original=moeda_original,
        tem_nota_fiscal=item["tem_nota_fiscal"],
        valor_brl=valor,
        taxa_cambio=None,
    )


def carregar_despesas(caminho: str) -> tuple[Colaborador, Periodo, list[Despesa]]:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo, parse_float=Decimal)

    colaborador = Colaborador(
        id=dados["colaborador"]["id"],
        nome=dados["colaborador"]["nome"],
        centro_custo=dados["colaborador"]["centro_custo"],
    )

    periodo = Periodo(
        competencia=dados["periodo"]["competencia"],
        inicio=date.fromisoformat(dados["periodo"]["inicio"]),
        fim=date.fromisoformat(dados["periodo"]["fim"]),
    )

    despesas = [_construir_despesa(item) for item in dados["despesas"]]

    return colaborador, periodo, despesas
