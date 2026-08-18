import argparse
import json
from collections.abc import Sequence

from src.motor import calcular
from src.parser import carregar_despesas
from src.saida import montar_saida


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

    return parser


def executar_calculo(caminho_entrada: str, caminho_saida: str) -> None:
    colaborador, periodo, despesas = carregar_despesas(caminho_entrada)
    resultado_final = calcular(colaborador, periodo, despesas)

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(montar_saida(resultado_final), arquivo, ensure_ascii=False, indent=4)
        arquivo.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    argumentos = _construir_parser().parse_args(argv)
    executar_calculo(argumentos.entrada, argumentos.saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
