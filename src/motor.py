from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.politica import LIMITES_DIARIOS_POR_CATEGORIA
from src.regras import (
    aplicar_limite_diario,
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
    normalizar_categoria,
)


def aplicar_filtros(despesas: list[Despesa], periodo: Periodo) -> list[ResultadoDespesa | None]:
    resultados: list[ResultadoDespesa | None] = []
    despesas_ja_aceitas: list[Despesa] = []

    for despesa in despesas:
        reprovacao_estrutural = (
            filtro_valor_negativo(despesa)
            or filtro_categoria_invalida(despesa)
            or filtro_fora_periodo(despesa, periodo)
            or filtro_duplicata(despesa, despesas_ja_aceitas)
        )
        if reprovacao_estrutural is not None:
            resultados.append(reprovacao_estrutural)
            continue

        despesas_ja_aceitas.append(despesa)
        resultados.append(filtro_nota_fiscal(despesa))

    return resultados


def aplicar_limites(
    despesas: list[Despesa], resultados: list[ResultadoDespesa | None]
) -> list[ResultadoDespesa]:
    finais: list[ResultadoDespesa] = []
    reembolsos_por_categoria_dia: dict[tuple[str, date], list[tuple[Despesa, Decimal]]] = {}

    for despesa, resultado in zip(despesas, resultados, strict=True):
        if resultado is not None:
            finais.append(resultado)
            continue

        categoria = normalizar_categoria(despesa.categoria)
        limite = LIMITES_DIARIOS_POR_CATEGORIA[categoria]
        reembolsos_do_dia = reembolsos_por_categoria_dia.setdefault((categoria, despesa.data), [])
        resultado_limite = aplicar_limite_diario(despesa, limite, reembolsos_do_dia)
        reembolsos_do_dia.append((despesa, resultado_limite.valor_reembolsavel))
        finais.append(resultado_limite)

    return finais
