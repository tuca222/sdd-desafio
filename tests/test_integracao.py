import json
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

import pytest

from src.cli import main

CAMINHO_ENTRADA = "exemplos/despesas-exemplo.json"
CAMINHO_RESULTADO_ESPERADO = "exemplos/resultado-exemplo.json"
CAMINHO_ENVELOPE_CC_DESCONHECIDO = "exemplos/envelope/despesas-envelope-cc-desconhecido.json"
CAMINHO_ENVELOPE = "exemplos/envelope/despesas-envelope.json"

# Um item por linha da spec.md §9 ("Critérios de aceite"), primeiro bloco:
# (id, tipo_reembolso, valor_reembolsavel, trecho obrigatório da justificativa)
CRITERIOS_DE_ACEITE = [
    ("d-001", "total", 72.50, "Reembolso total aprovado"),
    ("d-002", "parcial", 2.50, "R$75,00 no dia para o centro de custo CC-ENG-PLATAFORMA"),
    ("d-003", "parcial", 80.00, "R$80,00 no dia para o centro de custo CC-ENG-PLATAFORMA"),
    ("d-004", "nenhum", 0.00, "nota fiscal"),
    ("d-005", "nenhum", 0.00, "'coworking' não é reembolsável para o centro de custo"),
    ("d-006", "total", 54.90, "Reembolso total aprovado"),
    ("d-007", "nenhum", 0.00, "duplicata da despesa 'Almoco(d-006)'"),
    ("d-008", "nenhum", 0.00, "fora do período de competência"),
    ("d-009", "nenhum", 0.00, "valor negativo"),
    ("d-010", "nenhum", 0.00, "'hospedagem' não é reembolsável para o centro de custo"),
    ("d-011", "total", 33.33, "Reembolso total aprovado"),
    ("d-012", "total", 47.20, "Reembolso total aprovado"),
    ("d-013", "nenhum", 0.00, "'hospedagem' não é reembolsável para o centro de custo"),
    ("d-014", "total", 61.00, "Reembolso total aprovado"),
]

# Segundo bloco: CC-SUPORTE-N2 não tem entrada em `centros_custo` e cai no `padrao`.
CRITERIOS_CC_DESCONHECIDO = [
    ("f-001", "total", 58.00, "Reembolso total aprovado"),
    ("f-002", "parcial", 250.00, "R$250,00 no dia para o centro de custo CC-SUPORTE-N2"),
    ("f-003", "nenhum", 0.00, "'representacao' não é reembolsável para o centro de custo"),
    ("f-004", "total", 65.76, "Reembolso total aprovado"),
]

# Terceiro bloco: CC-COMERCIAL, com as quatro categorias próprias e os quatro
# desfechos de câmbio (conversão, data sem cotação, moeda ausente, sem o campo).
CRITERIOS_COMERCIAL = [
    ("e-001", "parcial", 300.00, "R$300,00 no dia para o centro de custo CC-COMERCIAL"),
    ("e-002", "parcial", 90.00, "R$90,00 no dia para o centro de custo CC-COMERCIAL"),
    ("e-003", "total", 85.26, "Reembolso total aprovado"),
    ("e-004", "nenhum", 0.00, "taxa de câmbio de EUR publicada para 2026-07-18"),
    ("e-005", "nenhum", 0.00, "nota fiscal"),
    ("e-006", "nenhum", 0.00, "taxa de câmbio de GBP publicada para 2026-07-21"),
    ("e-007", "parcial", 400.00, "R$400,00 no dia para o centro de custo CC-COMERCIAL"),
    ("e-008", "parcial", 90.00, "R$90,00 no dia para o centro de custo CC-COMERCIAL"),
    ("e-009", "nenhum", 0.00, "'coworking' não é reembolsável para o centro de custo"),
    ("e-010", "total", 88.00, "Reembolso total aprovado"),
]


def rodar(entrada: str, tmp_path: Path) -> dict:
    destino = tmp_path / "resultado.json"
    assert main(["calcular", "--input", entrada, "--output", str(destino)]) == 0
    return json.loads(destino.read_text(encoding="utf-8"))


@pytest.fixture
def resultado(tmp_path: Path) -> dict:
    return rodar(CAMINHO_ENTRADA, tmp_path)


def despesas_por_id(resultado: dict) -> dict[str, dict]:
    return {item["id"]: item for item in resultado["detalhamento_despesas"]}


def conferir_criterios(resultado: dict, criterios: list[tuple]) -> None:
    por_id = despesas_por_id(resultado)

    assert list(por_id) == [id_esperado for id_esperado, _, _, _ in criterios]

    for id_despesa, tipo, valor, trecho in criterios:
        saida_do_motor = por_id[id_despesa]["motor_reembolso_output"]

        assert saida_do_motor["tipo_reembolso"] == tipo, id_despesa
        assert saida_do_motor["valor_reembolsavel"] == valor, id_despesa
        assert saida_do_motor["despesa_reembolsavel"] is (valor > 0), id_despesa
        assert trecho in saida_do_motor["justificativa"], id_despesa


def test_exemplo_completo_bate_com_criterios_de_aceite(resultado: dict):
    conferir_criterios(resultado, CRITERIOS_DE_ACEITE)

    assert resultado["valor_total_despesas"] == 1806.94
    assert resultado["valor_total_reembolsavel"] == 351.43


def test_saida_e_identica_ao_resultado_esperado(resultado: dict):
    esperado = json.loads(Path(CAMINHO_RESULTADO_ESPERADO).read_text(encoding="utf-8"))

    assert resultado == esperado


def test_saida_bate_com_o_exemplo_caractere_a_caractere(tmp_path: Path):
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_ENTRADA, "--output", str(destino)])

    # spec.md §9 ("Criterios de aceite"): a comparacao e sobre o texto, nao sobre o
    # resultado do parsing. Como dicts, 60.0 e 60.00 sao o mesmo valor — foi por
    # isso que test_saida_e_identica_ao_resultado_esperado deixou passar a escala
    # errada ate a T-027.
    assert destino.read_text(encoding="utf-8") == Path(CAMINHO_RESULTADO_ESPERADO).read_text(
        encoding="utf-8"
    )


def _truncado(valor: float) -> Decimal:
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def test_duplicata_e_estorno_ficam_fora_do_total_bruto(resultado: dict):
    por_id = despesas_por_id(resultado)

    # O total soma valores truncados (RN-010), embora a saida exiba os originais.
    soma_de_todos_os_lancamentos = sum(
        (_truncado(item["valor"]) for item in resultado["detalhamento_despesas"]),
        Decimal("0.00"),
    )
    excluidos = _truncado(por_id["d-007"]["valor"]) + _truncado(por_id["d-009"]["valor"])

    assert Decimal(str(resultado["valor_total_despesas"])) == (
        soma_de_todos_os_lancamentos - excluidos
    )


def test_rn010_valor_lancado_sai_inteiro_e_o_reembolso_sai_truncado(resultado: dict):
    d011 = despesas_por_id(resultado)["d-011"]

    assert d011["valor"] == 33.333
    assert d011["motor_reembolso_output"]["valor_reembolsavel"] == 33.33


def test_rn011_categoria_sai_com_a_grafia_da_entrada(resultado: dict):
    d014 = despesas_por_id(resultado)["d-014"]

    assert d014["categoria"] == "ALIMENTACAO"
    assert d014["motor_reembolso_output"]["valor_reembolsavel"] == 61.00


def test_rn015_exemplo_nao_tem_despesa_internacional(resultado: dict):
    for item in resultado["detalhamento_despesas"]:
        assert "moeda" not in item, item["id"]
        assert item["motor_reembolso_output"]["taxa_cambio"] is None, item["id"]
        assert item["motor_reembolso_output"]["valor_convertido_brl"] is None, item["id"]