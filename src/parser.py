import json
from datetime import date
from decimal import ROUND_DOWN, Decimal

from src.modelos import Colaborador, Despesa, Periodo
from src.regras import normalizar_categoria

DUAS_CASAS_DECIMAIS = Decimal("0.01")


def _truncar_valor(valor: Decimal) -> Decimal:
    return valor.quantize(DUAS_CASAS_DECIMAIS, rounding=ROUND_DOWN)


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

    despesas = [
        Despesa(
            id=item["id"],
            data=date.fromisoformat(item["data"]),
            categoria=normalizar_categoria(item["categoria"]),
            categoria_original=item["categoria"],
            descricao=item["descricao"],
            fornecedor=item["fornecedor"],
            valor=_truncar_valor(item["valor"]),
            tem_nota_fiscal=item["tem_nota_fiscal"],
        )
        for item in dados["despesas"]
    ]

    return colaborador, periodo, despesas
