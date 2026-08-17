from decimal import Decimal

from src.modelos import Despesa, ResultadoDespesa


def normalizar_categoria(categoria: str) -> str:
    return categoria.lower()


def filtro_valor_negativo(despesa: Despesa) -> ResultadoDespesa | None:
    if despesa.valor < 0:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                "Despesa com valor negativo, identificada como estorno. "
                "Reembolso negado."
            ),
        )
    return None
