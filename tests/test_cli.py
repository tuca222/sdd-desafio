import json
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

    assert json.loads(destino.read_text(encoding="utf-8")) == esperado


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
