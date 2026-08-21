import argparse
import json
import re
from collections.abc import Iterator, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.cambio import carregar_cambio
from src.motor import calcular
from src.parser import carregar_despesas
from src.politica import carregar_politica
from src.saida import montar_saida

# Resolvidos a partir do próprio pacote, e não do diretório de trabalho: a
# invocação fixa do DESAFIO.md não passa `--politica` nem `--cambio`, e precisa
# funcionar de onde quer que o motor seja chamado.
_RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO_POLITICA = str(_RAIZ / "exemplos" / "envelope" / "politica-v4.json")
CAMINHO_PADRAO_CAMBIO = str(_RAIZ / "exemplos" / "envelope" / "cambio.json")

# Sorteado a cada execução: a substituição em iterencode() varre também os fragmentos
# de string, então um marcador fixo permitiria que uma descrição de despesa vinda da
# entrada fosse confundida com um valor e virasse número na saída.
_MARCADOR = f"@{uuid4().hex}@"
_VALOR_MARCADO = re.compile(rf'"{re.escape(_MARCADOR)}(-?\d+(?:\.\d+)?){re.escape(_MARCADOR)}"')


class CodificadorMonetario(json.JSONEncoder):
    # O `json` só consulta `default()` para tipos que não sabe serializar, e trata o
    # que ele devolve como um valor comum — uma `str` sai entre aspas. Por isso o
    # Decimal vira texto marcado em `default()` e as aspas em volta do marcador são
    # removidas em `iterencode()`, já sobre o JSON serializado. Ver plan.md DT-004
    # ("Serialização de `Decimal` na saída").
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return f"{_MARCADOR}{o}{_MARCADOR}"
        return super().default(o)

    def iterencode(self, o: Any, _one_shot: bool = False) -> Iterator[str]:
        for pedaco in super().iterencode(o, _one_shot):
            yield _VALOR_MARCADO.sub(r"\1", pedaco)


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description="Motor de cálculo de reembolso de despesas corporativas.",
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    calcular_cmd = subcomandos.add_parser(
        "calcular",
        help="Calcula o reembolso das despesas de um arquivo JSON de entrada.",
    )
    calcular_cmd.add_argument(
        "--input",
        dest="entrada",
        required=True,
        help="Caminho do JSON de despesas de entrada.",
    )
    calcular_cmd.add_argument(
        "--output",
        dest="saida",
        required=True,
        help="Caminho do JSON de resultado a ser escrito.",
    )
    calcular_cmd.add_argument(
        "--politica",
        dest="politica",
        default=CAMINHO_PADRAO_POLITICA,
        help="Caminho do JSON da política de reembolso vigente.",
    )
    calcular_cmd.add_argument(
        "--cambio",
        dest="cambio",
        default=CAMINHO_PADRAO_CAMBIO,
        help="Caminho do JSON com as taxas de câmbio por data e moeda.",
    )

    return parser


def executar_calculo(
    caminho_entrada: str,
    caminho_saida: str,
    caminho_politica: str = CAMINHO_PADRAO_POLITICA,
    caminho_cambio: str = CAMINHO_PADRAO_CAMBIO,
) -> int:
    politica = carregar_politica(caminho_politica)
    cambio = carregar_cambio(caminho_cambio)
    colaborador, periodo, despesas = carregar_despesas(caminho_entrada, cambio)

    resultado_final = calcular(
        colaborador,
        periodo,
        despesas,
        politica.tabela_para(colaborador.centro_custo),
        politica.nota_fiscal_obrigatoria_acima_de,
    )

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(
            montar_saida(resultado_final),
            arquivo,
            ensure_ascii=False,
            indent=4,
            cls=CodificadorMonetario,
        )
        arquivo.write("\n")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    argumentos = _construir_parser().parse_args(argv)
    return executar_calculo(
        argumentos.entrada,
        argumentos.saida,
        argumentos.politica,
        argumentos.cambio,
    )


if __name__ == "__main__":
    raise SystemExit(main())
