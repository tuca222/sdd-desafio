from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Colaborador:
    id: str
    nome: str
    centro_custo: str


@dataclass(frozen=True)
class Periodo:
    competencia: str
    inicio: date
    fim: date


@dataclass(frozen=True)
class Despesa:
    id: str
    data: date
    categoria: str
    descricao: str
    fornecedor: str
    valor: Decimal
    tem_nota_fiscal: bool


@dataclass(frozen=True)
class ResultadoDespesa:
    despesa_reembolsavel: bool
    tipo_reembolso: str
    valor_reembolsavel: Decimal
    justificativa: str


@dataclass(frozen=True)
class ResultadoFinal:
    colaborador: Colaborador
    periodo: Periodo
    valor_total_despesas: Decimal
    valor_total_reembolsavel: Decimal
    detalhamento: list[tuple[Despesa, ResultadoDespesa]]
