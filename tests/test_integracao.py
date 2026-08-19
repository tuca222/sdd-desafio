import json
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

import pytest

from src.cli import main
from src.politica import (
    LIMITE_ALIMENTACAO,
    LIMITE_HOSPEDAGEM,
    LIMITE_TRANSPORTE_URBANO,
)

CAMINHO_ENTRADA = "exemplos/despesas-exemplo.json"
CAMINHO_RESULTADO_ESPERADO = "exemplos/resultado-exemplo.json"

# Um item por linha da spec.md §9 ("Critérios de aceite"):
# (id, tipo_reembolso, valor_reembolsavel, trecho obrigatório da justificativa)
CRITERIOS_DE_ACEITE = [
    ("d-001", "parcial", 60.00, "limite de reembolso de R$60,00 no dia"),
    ("d-002", "nenhum", 0.00, "Almoco com cliente(d-001)"),
    ("d-003", "parcial", 80.00, "limite de reembolso de R$80,00 no dia"),
    ("d-004", "nenhum", 0.00, "nota fiscal"),
    ("d-005", "nenhum", 0.00, "fora da política de reembolso"),
    ("d-006", "total", 54.90, "Reembolso total aprovado"),
    ("d-007", "nenhum", 0.00, "duplicata da despesa 'Almoco(d-006)'"),
    ("d-008", "nenhum", 0.00, "fora do período de competência"),
    ("d-009", "nenhum", 0.00, "valor negativo"),
    ("d-010", "parcial", 250.00, "limite de reembolso de R$250,00 no dia"),
    ("d-011", "total", 33.33, "Reembolso total aprovado"),
    ("d-012", "total", 47.20, "Reembolso total aprovado"),
    ("d-013", "nenhum", 0.00, "nota fiscal"),
    ("d-014", "parcial", 60.00, "categoria alimentacao"),
]

LIMITE_POR_CATEGORIA = {
    "alimentacao": float(LIMITE_ALIMENTACAO),
    "transporte_urbano": float(LIMITE_TRANSPORTE_URBANO),
    "hospedagem": float(LIMITE_HOSPEDAGEM),
}


@pytest.fixture
def resultado(tmp_path: Path) -> dict:
    destino = tmp_path / "resultado.json"
    main(["calcular", "--input", CAMINHO_ENTRADA, "--output", str(destino)])
    return json.loads(destino.read_text(encoding="utf-8"))


def despesas_por_id(resultado: dict) -> dict[str, dict]:
    return {item["id"]: item for item in resultado["detalhamento_despesas"]}


def test_exemplo_completo_bate_com_criterios_de_aceite(resultado: dict):
    por_id = despesas_por_id(resultado)

    assert list(por_id) == [id_esperado for id_esperado, _, _, _ in CRITERIOS_DE_ACEITE]

    for id_despesa, tipo, valor, trecho in CRITERIOS_DE_ACEITE:
        saida_do_motor = por_id[id_despesa]["motor_reembolso_output"]

        assert saida_do_motor["tipo_reembolso"] == tipo, id_despesa
        assert saida_do_motor["valor_reembolsavel"] == valor, id_despesa
        assert saida_do_motor["despesa_reembolsavel"] is (valor > 0), id_despesa
        assert trecho in saida_do_motor["justificativa"], id_despesa

    assert resultado["valor_total_despesas"] == 1806.94
    assert resultado["valor_total_reembolsavel"] == 585.43


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
    assert "categoria alimentacao" in d014["motor_reembolso_output"]["justificativa"]


def test_rn012_nenhuma_despesa_passa_do_limite_padrao_da_categoria(resultado: dict):
    for item in resultado["detalhamento_despesas"]:
        limite = LIMITE_POR_CATEGORIA.get(item["categoria"].lower())
        if limite is None:
            continue

        assert item["motor_reembolso_output"]["valor_reembolsavel"] <= limite, item["id"]
