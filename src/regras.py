from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo, ResultadoDespesa
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


def filtro_fora_periodo(despesa: Despesa, periodo: Periodo) -> ResultadoDespesa | None:
    if despesa.data < periodo.inicio or despesa.data > periodo.fim:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                "Despesa lançada fora do período de competência "
                f"({periodo.inicio.isoformat()} a {periodo.fim.isoformat()}). "
                "Reembolso negado."
            ),
        )
    return None


def _identidade_duplicata(despesa: Despesa) -> tuple[date, str, str, str, Decimal, bool]:
    return (
        despesa.data,
        despesa.categoria,
        despesa.descricao,
        despesa.fornecedor,
        despesa.valor,
        despesa.tem_nota_fiscal,
    )


def filtro_duplicata(
    despesa: Despesa, despesas_anteriores: list[Despesa]
) -> ResultadoDespesa | None:
    for anterior in despesas_anteriores:
        if _identidade_duplicata(despesa) == _identidade_duplicata(anterior):
            return ResultadoDespesa(
                despesa_reembolsavel=False,
                tipo_reembolso="nenhum",
                valor_reembolsavel=Decimal("0.00"),
                justificativa=(
                    "Despesa identificada como duplicata da despesa "
                    f"'{anterior.descricao}({anterior.id})'. Reembolso negado."
                ),
            )
    return None
