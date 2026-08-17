from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.regras import (
    filtro_categoria_invalida,
    filtro_duplicata,
    filtro_fora_periodo,
    filtro_nota_fiscal,
    filtro_valor_negativo,
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
