import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class LimiteCategoria:
    limite: Decimal
    periodicidade: str


@dataclass(frozen=True)
class TabelaLimites:
    centro_custo: str
    limites: dict[str, LimiteCategoria]


@dataclass(frozen=True)
class Politica:
    vigencia: date
    tabela_padrao: dict[str, LimiteCategoria]
    tabela_por_centro_custo: dict[str, dict[str, LimiteCategoria]]
    nota_fiscal_obrigatoria_acima_de: Decimal



def _tabela(bruto: dict[str, Any]) -> dict[str, LimiteCategoria]:
    return {
        categoria: LimiteCategoria(
            limite=item["limite"],
            periodicidade=item["periodicidade"],
        )
        for categoria, item in bruto.items()
    }


def carregar_politica(caminho: str) -> Politica:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo, parse_float=Decimal)

    return Politica(
        vigencia=date.fromisoformat(dados["vigencia"]),
        tabela_padrao=_tabela(dados["padrao"]),
        tabela_por_centro_custo={
            centro_custo: _tabela(tabela) for centro_custo, tabela in dados["centros_custo"].items()
        },
        nota_fiscal_obrigatoria_acima_de=dados["nota_fiscal_obrigatoria_acima_de"],
    )
