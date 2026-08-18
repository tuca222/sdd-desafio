from dataclasses import dataclass

import pytest

from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.motor import aplicar_filtros, aplicar_limites
from src.parser import carregar_despesas

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"


@dataclass(frozen=True)
class ExemploProcessado:
    periodo: Periodo
    despesas: dict[str, Despesa]
    resultados_filtros: dict[str, ResultadoDespesa | None]
    resultados: dict[str, ResultadoDespesa]


@pytest.fixture
def exemplo() -> ExemploProcessado:
    _, periodo, despesas = carregar_despesas(CAMINHO_EXEMPLO)
    filtros = aplicar_filtros(despesas, periodo)
    resultados_filtros = filtros.resultados
    resultados_finais = aplicar_limites(despesas, resultados_filtros)
    ids = [despesa.id for despesa in despesas]

    return ExemploProcessado(
        periodo=periodo,
        despesas={despesa.id: despesa for despesa in despesas},
        resultados_filtros=dict(zip(ids, resultados_filtros, strict=True)),
        resultados=dict(zip(ids, resultados_finais, strict=True)),
    )
