import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from src.cli import main
from src.motor import calcular
from src.parser import carregar_despesas
from src.saida import montar_saida

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"


def test_cli_calcular_gera_arquivo_de_saida(tmp_path: Path):
    destino = tmp_path / "resultado.json"

    codigo = main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino)])

    assert codigo == 0
    assert destino.exists()

    resultado = json.loads(destino.read_text(encoding="utf-8"))

    assert resultado["valor_total_despesas"] == 1806.94
    assert resultado["valor_total_reembolsavel"] == 585.43
    assert len(resultado["detalhamento_despesas"]) == 14


def test_cli_escreve_exatamente_o_que_o_motor_produz(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino)])

    colaborador, periodo, despesas = carregar_despesas(CAMINHO_EXEMPLO)
    esperado = montar_saida(calcular(colaborador, periodo, despesas))

    # parse_float=Decimal na releitura: o motor produz Decimal e e assim que o
    # arquivo tem de reparsear, sem passar por float em ponto nenhum do caminho.
    escrito = json.loads(destino.read_text(encoding="utf-8"), parse_float=Decimal)

    assert escrito == esperado


def test_cli_escreve_valores_monetarios_com_duas_casas(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino)])

    texto = destino.read_text(encoding="utf-8")

    # spec.md §4 ("Entrada e saida"): o que o motor produz sai com exatamente 2
    # casas decimais, inclusive quando a ultima e zero.
    assert '"valor_total_despesas": 1806.94' in texto
    assert '"valor_reembolsavel": 60.00' in texto
    assert '"valor_reembolsavel": 0.00' in texto
    assert '"valor_reembolsavel": 250.00' in texto

    # E os campos ecoados saem com a escala lancada, nem truncada nem esticada.
    assert '"valor": 72.50' in texto
    assert '"valor": 33.333' in texto
    assert '"valor": -45.00' in texto

    # Nenhum valor monetario sai com 1 casa decimal so.
    assert not re.search(r'"(valor|valor_reembolsavel|valor_total_\w+)": -?\d+\.\d(,|\n)', texto)


def test_cli_nao_confunde_texto_da_entrada_com_valor_monetario(tmp_path: Path):
    # O encoder de plan.md DT-004 marca os Decimal com um delimitador e o remove
    # varrendo o JSON ja serializado — inclusive os fragmentos de string. Uma
    # descricao que imitasse o delimitador viraria numero na saida se ele fosse fixo.
    entrada = json.loads(Path(CAMINHO_EXEMPLO).read_text(encoding="utf-8"))
    entrada["despesas"][0]["descricao"] = f"@{'a' * 32}@999.99@{'a' * 32}@"
    arquivo = tmp_path / "despesas.json"
    arquivo.write_text(json.dumps(entrada), encoding="utf-8")

    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", str(arquivo), "--output", str(destino)])

    escrito = json.loads(destino.read_text(encoding="utf-8"), parse_float=Decimal)

    assert escrito["detalhamento_despesas"][0]["descricao"] == entrada["despesas"][0]["descricao"]


def test_cli_nao_altera_o_arquivo_de_entrada(tmp_path: Path):
    entrada = tmp_path / "despesas.json"
    entrada.write_text(Path(CAMINHO_EXEMPLO).read_text(encoding="utf-8"), encoding="utf-8")
    conteudo_antes = entrada.read_bytes()

    main(["calcular", "--input", str(entrada), "--output", str(tmp_path / "resultado.json")])

    assert entrada.read_bytes() == conteudo_antes


def test_cli_grava_acentuacao_sem_escapar(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino)])

    texto = destino.read_text(encoding="utf-8")

    assert "já foi atingido" in texto
    assert "\\u00e1" not in texto


def test_cli_exige_input_e_output(tmp_path: Path):
    with pytest.raises(SystemExit) as erro:
        main(["calcular", "--input", CAMINHO_EXEMPLO])

    assert erro.value.code == 2
