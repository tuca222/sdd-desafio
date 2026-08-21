import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from src.cambio import TabelaCambio
from src.cli import main
from src.motor import calcular
from src.parser import carregar_despesas
from src.politica import Politica
from src.saida import montar_saida

CAMINHO_EXEMPLO = "exemplos/despesas-exemplo.json"
CAMINHO_POLITICA = "exemplos/envelope/politica-v4.json"
CAMINHO_CAMBIO = "exemplos/envelope/cambio.json"

# As tres entradas sao obrigatorias (spec.md §4, "Entrada e saida"), entao toda
# invocacao da CLI informa as tres.
ENVELOPE = ["--politica", CAMINHO_POLITICA, "--cambio", CAMINHO_CAMBIO]


def escrever_politica(destino: Path, **campos) -> str:
    politica = json.loads(Path(CAMINHO_POLITICA).read_text(encoding="utf-8")) | campos
    destino.write_text(json.dumps(politica), encoding="utf-8")
    return str(destino)


def escrever_lote(destino: Path, competencia: str, inicio: str, fim: str) -> str:
    entrada = json.loads(Path(CAMINHO_EXEMPLO).read_text(encoding="utf-8"))
    entrada["periodo"] = {"competencia": competencia, "inicio": inicio, "fim": fim}
    destino.write_text(json.dumps(entrada), encoding="utf-8")
    return str(destino)


def test_cli_calcular_gera_arquivo_de_saida(tmp_path: Path):
    destino = tmp_path / "resultado.json"

    codigo = main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino), *ENVELOPE])

    assert codigo == 0
    assert destino.exists()

    resultado = json.loads(destino.read_text(encoding="utf-8"))

    assert resultado["valor_total_despesas"] == 1806.94
    assert resultado["valor_total_reembolsavel"] == 351.43
    assert len(resultado["detalhamento_despesas"]) == 14


def test_cli_escreve_exatamente_o_que_o_motor_produz(
    tmp_path: Path, politica: Politica, cambio: TabelaCambio
):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino), *ENVELOPE])

    colaborador, periodo, despesas = carregar_despesas(CAMINHO_EXEMPLO, cambio)
    esperado = montar_saida(
        calcular(
            colaborador,
            periodo,
            despesas,
            politica.tabela_para(colaborador.centro_custo),
            politica.nota_fiscal_obrigatoria_acima_de,
        )
    )

    # parse_float=Decimal na releitura: o motor produz Decimal e e assim que o
    # arquivo tem de reparsear, sem passar por float em ponto nenhum do caminho.
    escrito = json.loads(destino.read_text(encoding="utf-8"), parse_float=Decimal)

    assert escrito == esperado


def test_cli_escreve_valores_monetarios_com_duas_casas(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino), *ENVELOPE])

    texto = destino.read_text(encoding="utf-8")

    # spec.md §4 ("Entrada e saida"): o que o motor produz sai com exatamente 2
    # casas decimais, inclusive quando a ultima e zero.
    assert '"valor_total_despesas": 1806.94' in texto
    assert '"valor_reembolsavel": 2.50' in texto
    assert '"valor_reembolsavel": 0.00' in texto
    assert '"valor_reembolsavel": 80.00' in texto

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
    main(["calcular", "--input", str(arquivo), "--output", str(destino), *ENVELOPE])

    escrito = json.loads(destino.read_text(encoding="utf-8"), parse_float=Decimal)

    assert escrito["detalhamento_despesas"][0]["descricao"] == entrada["despesas"][0]["descricao"]


def test_cli_nao_altera_o_arquivo_de_entrada(tmp_path: Path):
    entrada = tmp_path / "despesas.json"
    entrada.write_text(Path(CAMINHO_EXEMPLO).read_text(encoding="utf-8"), encoding="utf-8")
    conteudo_antes = entrada.read_bytes()

    main(
        [
            "calcular",
            "--input",
            str(entrada),
            "--output",
            str(tmp_path / "resultado.json"),
            *ENVELOPE,
        ]
    )

    assert entrada.read_bytes() == conteudo_antes


def test_cli_grava_acentuacao_sem_escapar(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino), *ENVELOPE])

    texto = destino.read_text(encoding="utf-8")

    assert "política vigente" in texto
    assert "não é reembolsável" in texto
    assert "período de competência" in texto
    assert "\\u00" not in texto


def test_cli_exige_input_e_output(tmp_path: Path):
    with pytest.raises(SystemExit) as erro:
        main(["calcular", "--input", CAMINHO_EXEMPLO])

    assert erro.value.code == 2


def test_cli_aceita_politica_e_cambio_alternativos(tmp_path: Path):
    # Mesma entrada, política com um limite de alimentação diferente: o resultado
    # tem de mudar, e é isso que prova que a flag foi usada.
    politica_alternativa = json.loads(Path(CAMINHO_POLITICA).read_text(encoding="utf-8"))
    politica_alternativa["centros_custo"]["CC-ENG-PLATAFORMA"]["alimentacao"]["limite"] = 40.00
    caminho_politica = tmp_path / "politica.json"
    caminho_politica.write_text(json.dumps(politica_alternativa), encoding="utf-8")

    destino = tmp_path / "resultado.json"
    codigo = main(
        [
            "calcular",
            "--input",
            CAMINHO_EXEMPLO,
            "--output",
            str(destino),
            "--politica",
            str(caminho_politica),
            "--cambio",
            CAMINHO_CAMBIO,
        ]
    )

    assert codigo == 0

    resultado = json.loads(destino.read_text(encoding="utf-8"))
    por_id = {item["id"]: item for item in resultado["detalhamento_despesas"]}

    # d-001 (R$72,50) deixa de caber no limite e vira parcial de R$40,00.
    assert por_id["d-001"]["motor_reembolso_output"]["valor_reembolsavel"] == 40.00
    assert "R$40,00" in por_id["d-001"]["motor_reembolso_output"]["justificativa"]


def test_cli_exige_politica_e_cambio(tmp_path: Path):
    """spec.md §4 ("Entrada e saída"): as **três** entradas são obrigatórias.

    Antes da [[T-050]] as duas flags tinham default, e a invocação abaixo rodava e
    escrevia `resultado.json` — julgando o lote com a política de
    `exemplos/envelope/`, que quem rodou não escolheu e não viu. Um relatório de
    reembolso cujos limites não são rastreáveis a partir do comando que o gerou não
    é auditável, que é o oposto do que a spec pede.
    """
    destino = tmp_path / "resultado.json"

    with pytest.raises(SystemExit) as erro:
        main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino)])

    assert erro.value.code == 2
    assert not destino.exists()


def test_cli_exige_cada_uma_das_tres_entradas(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    completo = ["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(destino), *ENVELOPE]

    # Retirar qualquer um dos três caminhos de entrada derruba a invocação.
    for flag in ("--input", "--politica", "--cambio"):
        indice = completo.index(flag)
        incompleto = completo[:indice] + completo[indice + 2 :]

        with pytest.raises(SystemExit) as erro:
            main(incompleto)

        assert erro.value.code == 2, flag
        assert not destino.exists(), flag


def test_rn017_lote_de_competencia_anterior_nao_gera_saida(tmp_path: Path, capsys):
    entrada = escrever_lote(tmp_path / "junho.json", "2026-06", "2026-06-01", "2026-06-30")
    destino = tmp_path / "resultado.json"

    codigo = main(["calcular", "--input", entrada, "--output", str(destino), *ENVELOPE])

    # O que se afirma é a ausência do arquivo mais o código de saída — um
    # resultado.json com tudo zerado tem a forma de um relatório válido.
    assert codigo != 0
    assert not destino.exists()

    erro = capsys.readouterr().err

    assert "2026-07" in erro
    assert "2026-06" in erro


def test_rn017_lote_coberto_gera_saida_normalmente(tmp_path: Path):
    # A política de julho continua valendo em agosto se não houver política nova.
    entrada = escrever_lote(tmp_path / "agosto.json", "2026-08", "2026-07-01", "2026-08-31")
    destino = tmp_path / "resultado.json"

    codigo = main(["calcular", "--input", entrada, "--output", str(destino), *ENVELOPE])

    assert codigo == 0
    assert destino.exists()
    assert json.loads(destino.read_text(encoding="utf-8"))["periodo"]["competencia"] == "2026-08"


def test_rn017_vigencia_no_meio_do_mes_nao_nega_despesa_anterior(tmp_path: Path):
    # AMB-020: não existe verificação de vigência por despesa. Uma política que
    # vigora de 15/07 processa o lote de 2026-07 inteiro, igual à de 01/07.
    caminho_politica = escrever_politica(tmp_path / "politica.json", vigencia="2026-07-15")
    de_quinze = tmp_path / "de-quinze.json"
    de_primeiro = tmp_path / "de-primeiro.json"

    codigo = main(
        [
            "calcular",
            "--input",
            CAMINHO_EXEMPLO,
            "--output",
            str(de_quinze),
            "--politica",
            caminho_politica,
            "--cambio",
            CAMINHO_CAMBIO,
        ]
    )
    main(["calcular", "--input", CAMINHO_EXEMPLO, "--output", str(de_primeiro), *ENVELOPE])

    assert codigo == 0
    assert de_quinze.read_text(encoding="utf-8") == de_primeiro.read_text(encoding="utf-8")
