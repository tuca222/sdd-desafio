from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.politica import CATEGORIAS_VALIDAS, LIMITE_NOTA_FISCAL


def normalizar_categoria(categoria: str) -> str:
    return categoria.lower()


def formatar_reais(valor: Decimal) -> str:
    return f"R${valor:.2f}".replace(".", ",")


def filtro_valor_negativo(despesa: Despesa) -> ResultadoDespesa | None:
    if despesa.valor < 0:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                "Despesa com valor negativo, identificada como estorno. Reembolso negado."
            ),
        )
    return None


def filtro_categoria_invalida(despesa: Despesa) -> ResultadoDespesa | None:
    if despesa.categoria not in CATEGORIAS_VALIDAS:
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


def filtro_cambio_indisponivel(despesa: Despesa) -> ResultadoDespesa | None:
    # RN-016: sem taxa não existe valor em BRL, e sem valor em BRL não há pergunta
    # a fazer sobre nota fiscal nem sobre limite — a despesa é inavaliável. A
    # justificativa cita moeda e data para que o financeiro saiba o que publicar.
    if despesa.valor_brl is None:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"Não há taxa de câmbio de {despesa.moeda} publicada para "
                f"{despesa.data.isoformat()}, e sem ela a despesa não pode ser "
                "convertida para BRL. Reembolso negado."
            ),
        )
    return None


def filtro_nota_fiscal(despesa: Despesa) -> ResultadoDespesa | None:
    if despesa.valor > LIMITE_NOTA_FISCAL and not despesa.tem_nota_fiscal:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"Despesas acima de {formatar_reais(LIMITE_NOTA_FISCAL)} necessitam "
                "de nota fiscal para reembolso. Esta despesa não possui nota "
                "fiscal. Reembolso negado."
            ),
        )
    return None


def _despesa_que_atingiu_limite(
    limite: Decimal, reembolsos_anteriores: list[tuple[Despesa, Decimal]]
) -> Despesa:
    acumulado = Decimal("0.00")
    for despesa, valor_reembolsado in reembolsos_anteriores:
        acumulado += valor_reembolsado
        if acumulado >= limite:
            return despesa
    return reembolsos_anteriores[-1][0]


def aplicar_limite_diario(
    despesa: Despesa,
    limite: Decimal,
    reembolsos_anteriores: list[tuple[Despesa, Decimal]],
) -> ResultadoDespesa:
    categoria = despesa.categoria
    consumido = sum((valor for _, valor in reembolsos_anteriores), Decimal("0.00"))
    disponivel = limite - consumido

    if disponivel <= 0:
        original = _despesa_que_atingiu_limite(limite, reembolsos_anteriores)
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"A categoria {categoria} possui limite de reembolso de "
                f"{formatar_reais(limite)} no dia. Este valor já foi atingido na "
                f"despesa '{original.descricao}({original.id})'. Reembolso negado."
            ),
        )

    if despesa.valor <= disponivel:
        return ResultadoDespesa(
            despesa_reembolsavel=True,
            tipo_reembolso="total",
            valor_reembolsavel=despesa.valor,
            justificativa="Reembolso total aprovado de acordo com a política vigente.",
        )

    return ResultadoDespesa(
        despesa_reembolsavel=True,
        tipo_reembolso="parcial",
        valor_reembolsavel=disponivel,
        justificativa=(
            f"A categoria {categoria} possui limite de reembolso de "
            f"{formatar_reais(limite)} no dia. Reembolso parcial aprovado."
        ),
    )
