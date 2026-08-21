from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from src.cambio import TabelaCambio, carregar_cambio
from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.motor import aplicar_filtros, aplicar_limites
from src.parser import carregar_despesas
from src.politica import Politica, TabelaLimites, carregar_politica

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"
CAMINHO_POLITICA = "exemplos/envelope/politica-v4.json"
CAMINHO_CAMBIO = "exemplos/envelope/cambio.json"

# Distingue "não informei `valor_brl`" de "informei `None`", que é o caso real de
# despesa sem taxa de câmbio (RN-016).
_NAO_INFORMADO: Any = object()


@dataclass(frozen=True)
class ExemploProcessado:
    periodo: Periodo
    tabela: TabelaLimites
    teto_nota_fiscal: Decimal
    despesas: dict[str, Despesa]
    resultados_filtros: dict[str, ResultadoDespesa | None]
    resultados: dict[str, ResultadoDespesa]


@pytest.fixture
def politica() -> Politica:
    return carregar_politica(CAMINHO_POLITICA)


@pytest.fixture
def cambio() -> TabelaCambio:
    return carregar_cambio(CAMINHO_CAMBIO)


@pytest.fixture
def exemplo(politica: Politica, cambio: TabelaCambio) -> ExemploProcessado:
    colaborador, periodo, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)
    tabela = politica.tabela_para(colaborador.centro_custo)
    teto = politica.nota_fiscal_obrigatoria_acima_de

    filtros = aplicar_filtros(despesas, periodo, tabela, teto)
    resultados_filtros = filtros.resultados
    resultados_finais = aplicar_limites(despesas, resultados_filtros, tabela)
    ids = [despesa.id for despesa in despesas]

    return ExemploProcessado(
        periodo=periodo,
        tabela=tabela,
        teto_nota_fiscal=teto,
        despesas={despesa.id: despesa for despesa in despesas},
        resultados_filtros=dict(zip(ids, resultados_filtros, strict=True)),
        resultados=dict(zip(ids, resultados_finais, strict=True)),
    )


def construir_despesa(
    id_despesa: str,
    data: date,
    categoria: str,
    descricao: str,
    fornecedor: str,
    valor: Decimal,
    tem_nota_fiscal: bool,
    *,
    categoria_original: str | None = None,
    valor_original: Decimal | None = None,
    moeda: str = "BRL",
    moeda_original: str | None = None,
    valor_brl: Decimal | None = _NAO_INFORMADO,
    taxa_cambio: Decimal | None = None,
) -> Despesa:
    """Monta uma `Despesa` como o `parser.py` a entregaria, sem ler arquivo nenhum.

    Os padrões descrevem a despesa em BRL: `moeda_original` é `None` (o campo não
    veio na entrada), `taxa_cambio` é `None` e `valor_brl` é o próprio valor
    (RN-015). Despesa internacional informa os três explicitamente — plan.md §6
    ("Estratégia de testes") exige `valor_brl` já preenchido nos testes de regra.
    """
    return Despesa(
        id=id_despesa,
        data=data,
        categoria=categoria,
        categoria_original=categoria if categoria_original is None else categoria_original,
        descricao=descricao,
        fornecedor=fornecedor,
        valor=valor,
        valor_original=valor if valor_original is None else valor_original,
        moeda=moeda,
        moeda_original=moeda_original,
        tem_nota_fiscal=tem_nota_fiscal,
        valor_brl=valor if valor_brl is _NAO_INFORMADO else valor_brl,
        taxa_cambio=taxa_cambio,
    )
