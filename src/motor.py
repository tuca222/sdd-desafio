from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.modelos import Colaborador, Despesa, Periodo, ResultadoDespesa, ResultadoFinal
from src.politica import LIMITES_DIARIOS_POR_CATEGORIA
from src.regras import (
    aplicar_limite_diario,
    filtro_cambio_indisponivel,
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
)


@dataclass(frozen=True)
class ResultadoFiltros:
    resultados: list[ResultadoDespesa | None]
    ids_duplicatas: set[str]


def aplicar_filtros(despesas: list[Despesa], periodo: Periodo) -> ResultadoFiltros:
    resultados: list[ResultadoDespesa | None] = []
    ids_duplicatas: set[str] = set()
    despesas_ja_aceitas: list[Despesa] = []

    for despesa in despesas:
        reprovacao = (
            filtro_valor_negativo(despesa)
            or filtro_categoria_invalida(despesa)
            or filtro_fora_periodo(despesa, periodo)
        )

        if reprovacao is None:
            reprovacao = filtro_duplicata(despesa, despesas_ja_aceitas)
            if reprovacao is not None:
                ids_duplicatas.add(despesa.id)

        if reprovacao is not None:
            resultados.append(reprovacao)
            continue

        # A despesa entra no conjunto comparado por RN-007 assim que passa a
        # verificação 3, e continua nele mesmo que seja negada pelos passos 5 e 6
        # — ver spec.md §8 ("Ordem de aplicação das regras").
        despesas_ja_aceitas.append(despesa)
        resultados.append(filtro_cambio_indisponivel(despesa) or filtro_nota_fiscal(despesa))

    return ResultadoFiltros(resultados=resultados, ids_duplicatas=ids_duplicatas)


def aplicar_limites(
    despesas: list[Despesa], resultados: list[ResultadoDespesa | None]
) -> list[ResultadoDespesa]:
    finais: list[ResultadoDespesa] = []
    reembolsos_por_categoria_dia: dict[tuple[str, date], list[tuple[Despesa, Decimal]]] = {}

    for despesa, resultado in zip(despesas, resultados, strict=True):
        if resultado is not None:
            finais.append(resultado)
            continue

        categoria = despesa.categoria
        limite = LIMITES_DIARIOS_POR_CATEGORIA[categoria]
        reembolsos_do_dia = reembolsos_por_categoria_dia.setdefault((categoria, despesa.data), [])
        resultado_limite = aplicar_limite_diario(despesa, limite, reembolsos_do_dia)
        reembolsos_do_dia.append((despesa, resultado_limite.valor_reembolsavel))
        finais.append(resultado_limite)

    return finais


def calcular(colaborador: Colaborador, periodo: Periodo, despesas: list[Despesa]) -> ResultadoFinal:
    filtros = aplicar_filtros(despesas, periodo)
    resultados = aplicar_limites(despesas, filtros.resultados)

    valor_total_despesas = sum(
        (
            despesa.valor
            for despesa in despesas
            if despesa.valor >= 0 and despesa.id not in filtros.ids_duplicatas
        ),
        Decimal("0.00"),
    )
    valor_total_reembolsavel = sum(
        (resultado.valor_reembolsavel for resultado in resultados), Decimal("0.00")
    )

    return ResultadoFinal(
        colaborador=colaborador,
        periodo=periodo,
        valor_total_despesas=valor_total_despesas,
        valor_total_reembolsavel=valor_total_reembolsavel,
        detalhamento=list(zip(despesas, resultados, strict=True)),
    )
