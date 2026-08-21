import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TabelaCambio:
    taxas: dict[date, dict[str, Decimal]]

    def taxa(self, moeda: str, data: date) -> Decimal | None:
        """Quantos BRL vale uma unidade de `moeda` em `data`, ou `None`.

        O `None` é o contrato: quem chama não precisa saber se faltou a data ou
        faltou a moeda naquela data, porque RN-016 trata os dois casos igual.
        """
        return self.taxas.get(data, {}).get(moeda)


def carregar_cambio(caminho: str) -> TabelaCambio:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo, parse_float=Decimal)

    return TabelaCambio(
        taxas={date.fromisoformat(dia): dict(cotacoes) for dia, cotacoes in dados["taxas"].items()}
    )
