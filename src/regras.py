from decimal import Decimal

from src.modelos import Despesa, ResultadoDespesa
from src.politica import CATEGORIAS_VALIDAS


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


def filtro_categoria_invalida(despesa: Despesa) -> ResultadoDespesa | None:
    if normalizar_categoria(despesa.categoria) not in CATEGORIAS_VALIDAS:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"A categoria '{despesa.categoria}' está fora da política de "
                "reembolso. Reembolso negado."
            ),
        )
    return None
