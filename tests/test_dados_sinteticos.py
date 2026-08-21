"""Validação do motor contra a massa sintética de `tests/dados/`.

Os arquivos de `tests/dados/` são independentes dos de `exemplos/`: outra política,
outro arquivo de câmbio, outras moedas, outros centros de custo e outro teto de nota
fiscal (R$150,00, não os R$100,00 dos exemplos). Isso é deliberado — um teste que só
roda contra os números do enunciado não distingue "o motor lê a política" de "o motor
tem os limites do enunciado embutidos".

Todo valor esperado abaixo foi calculado à mão a partir da política e do câmbio, e
está escrito por extenso no comentário de cada bloco. Nenhum número aqui foi copiado
da saída do motor, e nenhuma conta é refeita dentro do teste — plan.md §6
("Estratégia de testes").
"""

import json
from pathlib import Path

import pytest

from src.cli import main

DADOS = Path(__file__).parent / "dados"

POLITICA = str(DADOS / "politica-sintetica.json")
POLITICA_VIGENCIA_FUTURA = str(DADOS / "politica-vigencia-futura.json")
POLITICA_VIGENCIA_ANTERIOR = str(DADOS / "politica-vigencia-anterior.json")
CAMBIO = str(DADOS / "cambio-sintetico.json")
CAMBIO_VAZIO = str(DADOS / "cambio-vazio.json")

LIMITES_POR_CENTRO_DE_CUSTO = "despesas-01-limites-por-centro-de-custo.json"
CENTRO_DE_CUSTO_SEM_ENTRADA = "despesas-02-centro-de-custo-sem-entrada.json"
CAMBIO_MULTIPLOS_DESFECHOS = "despesas-03-cambio-multiplos-desfechos.json"
DUPLICATAS_E_MOEDA = "despesas-04-duplicatas-e-moeda.json"
BORDAS_E_TRUNCAMENTO = "despesas-05-bordas-e-truncamento.json"
COMPETENCIA_ANTERIOR = "despesas-06-competencia-anterior.json"
VALOR_INTEIRO = "despesas-07-valor-inteiro.json"
DUPLICATA_E_TRUNCAMENTO = "despesas-08-duplicata-e-truncamento.json"


def rodar(
    despesas: str,
    tmp_path: Path,
    politica: str = POLITICA,
    cambio: str = CAMBIO,
) -> dict:
    destino = tmp_path / "resultado.json"
    codigo = main(
        [
            "calcular",
            "--input",
            str(DADOS / despesas),
            "--output",
            str(destino),
            "--politica",
            politica,
            "--cambio",
            cambio,
        ]
    )

    assert codigo == 0
    return json.loads(destino.read_text(encoding="utf-8"))


def por_id(resultado: dict) -> dict[str, dict]:
    return {item["id"]: item for item in resultado["detalhamento_despesas"]}


def conferir(resultado: dict, esperado: list[tuple[str, str, float, str]]) -> None:
    despesas = por_id(resultado)

    assert list(despesas) == [id_esperado for id_esperado, _, _, _ in esperado]

    for id_despesa, tipo, valor, trecho in esperado:
        saida_do_motor = despesas[id_despesa]["motor_reembolso_output"]

        assert saida_do_motor["tipo_reembolso"] == tipo, id_despesa
        assert saida_do_motor["valor_reembolsavel"] == valor, id_despesa
        assert saida_do_motor["despesa_reembolsavel"] is (valor > 0), id_despesa
        assert trecho in saida_do_motor["justificativa"], id_despesa


def test_limites_vem_da_tabela_do_centro_de_custo(tmp_path: Path):
    """CC-VENDAS-LATAM: alimentação R$120, transporte R$90, hospedagem R$500,
    representação R$250. Teto de nota fiscal R$150,00.

    s1-001 R$130,00 estoura os R$120,00 do dia e leva R$120,00; s1-002 chega com o
    balde vazio. s1-003 é R$250,00 contra um limite de R$250,00 — cabe inteiro, é
    reembolso **total**, não parcial. s1-005 é R$149,99 sem nota: não cruza o teto
    e é avaliada pelo limite, virando parcial de R$90,00; s1-006 é R$150,01 sem
    nota, um centavo acima, e para na nota fiscal. s1-008 é `coworking`, que não
    existe na tabela deste centro de custo.
    """
    resultado = rodar(LIMITES_POR_CENTRO_DE_CUSTO, tmp_path)

    conferir(
        resultado,
        [
            ("s1-001", "parcial", 120.00, "R$120,00 no dia para o centro de custo"),
            ("s1-002", "nenhum", 0.00, "Almoco de fechamento(s1-001)"),
            ("s1-003", "total", 250.00, "Reembolso total aprovado"),
            ("s1-004", "nenhum", 0.00, "Jantar com distribuidor(s1-003)"),
            ("s1-005", "parcial", 90.00, "R$90,00 no dia para o centro de custo"),
            ("s1-006", "nenhum", 0.00, "Despesas acima de R$150,00 necessitam"),
            ("s1-007", "total", 480.00, "Reembolso total aprovado"),
            ("s1-008", "nenhum", 0.00, "'coworking' não é reembolsável"),
        ],
    )

    # 130,00 + 30,00 + 250,00 + 10,00 + 149,99 + 150,01 + 480,00 + 90,00
    assert resultado["valor_total_despesas"] == 1290.00
    # 120,00 + 250,00 + 90,00 + 480,00
    assert resultado["valor_total_reembolsavel"] == 940.00


def test_teto_de_nota_fiscal_vem_da_politica_e_nao_de_uma_constante(tmp_path: Path):
    resultado = por_id(rodar(LIMITES_POR_CENTRO_DE_CUSTO, tmp_path))

    # As duas despesas passariam do teto de R$100,00 dos exemplos; sob o teto de
    # R$150,00 desta política só a segunda é negada.
    assert resultado["s1-005"]["motor_reembolso_output"]["tipo_reembolso"] == "parcial"
    assert "R$150,00" in resultado["s1-006"]["motor_reembolso_output"]["justificativa"]
    assert "R$100,00" not in resultado["s1-006"]["motor_reembolso_output"]["justificativa"]


def test_centro_de_custo_sem_entrada_usa_o_padrao(tmp_path: Path):
    """CC-MARKETING não está em `centros_custo` e cai no `padrao`: alimentação
    R$50, transporte R$70, hospedagem R$200 — e **sem** `representacao`.

    O limite de alimentação de 2026-09-14 é dividido por três lançamentos na ordem
    da entrada: s2-001 leva R$45,00, s2-002 leva os R$5,00 que sobraram, e s2-003
    chega com zero. Quem esgotou o limite foi s2-002, e é ela que a justificativa
    de s2-003 tem de citar — não a primeira despesa do dia.
    """
    resultado = rodar(CENTRO_DE_CUSTO_SEM_ENTRADA, tmp_path)

    conferir(
        resultado,
        [
            ("s2-001", "total", 45.00, "Reembolso total aprovado"),
            ("s2-002", "parcial", 5.00, "R$50,00 no dia para o centro de custo CC-MARKETING"),
            ("s2-003", "nenhum", 0.00, "Almoco(s2-002)"),
            ("s2-004", "parcial", 200.00, "R$200,00 no dia para o centro de custo CC-MARKETING"),
            ("s2-005", "nenhum", 0.00, "'representacao' não é reembolsável"),
            ("s2-006", "total", 70.00, "Reembolso total aprovado"),
        ],
    )

    # 45,00 + 20,00 + 12,00 + 350,00 + 100,00 + 70,00
    assert resultado["valor_total_despesas"] == 597.00
    # 45,00 + 5,00 + 200,00 + 70,00
    assert resultado["valor_total_reembolsavel"] == 320.00

    # A justificativa cita o centro de custo do colaborador mesmo quando o limite
    # veio do `padrao` — quem confere precisa saber de quem é a despesa.
    assert resultado["colaborador"]["centro_custo"] == "CC-MARKETING"


def test_cambio_cobre_os_quatro_desfechos(tmp_path: Path):
    """CC-VENDAS-LATAM de novo (alimentação R$120, transporte R$90, repr. R$250).

    As contas, todas conferidas à mão contra `cambio-sintetico.json`:

    * s3-001 — EUR 20,00 × 6,00 = R$120,00, que é o limite do dia inteiro.
    * s3-002 — USD 5,00 × 5,00 = R$25,00, e o balde de 14/09 já está vazio.
    * s3-003 — JPY 1.000,00 × 0,035 = R$35,00 (taxa menor que 1).
    * s3-004 — JPY em 15/09: a data existe no arquivo, a moeda não. RN-016.
    * s3-005 — USD 30,00 × 5,25 = R$157,50, acima do teto de R$150,00 e sem nota.
      O número lançado (30,00) está muito abaixo do teto: quem decide é o convertido.
    * s3-006 — EUR 7,77 × 6,40 = R$49,728, truncado para R$49,72. Arredondado
      seria R$49,73.
    * s3-007 — R$88,00 sem o campo `moeda`.
    * s3-008 — GBP nunca é publicado. RN-016.
    * s3-009 — 19/09 é sábado e não está no arquivo. RN-016.
    """
    resultado = rodar(CAMBIO_MULTIPLOS_DESFECHOS, tmp_path)

    conferir(
        resultado,
        [
            ("s3-001", "total", 120.00, "Reembolso total aprovado"),
            ("s3-002", "nenhum", 0.00, "Almoco - Porto(s3-001)"),
            ("s3-003", "total", 35.00, "Reembolso total aprovado"),
            ("s3-004", "nenhum", 0.00, "taxa de câmbio de JPY publicada para 2026-09-15"),
            ("s3-005", "nenhum", 0.00, "Despesas acima de R$150,00 necessitam"),
            ("s3-006", "total", 49.72, "Reembolso total aprovado"),
            ("s3-007", "total", 88.00, "Reembolso total aprovado"),
            ("s3-008", "nenhum", 0.00, "taxa de câmbio de GBP publicada para 2026-09-18"),
            ("s3-009", "nenhum", 0.00, "taxa de câmbio de EUR publicada para 2026-09-19"),
        ],
    )

    despesas = por_id(resultado)

    # A conta tem de ser refazível a partir da saída: valor × taxa = convertido.
    assert despesas["s3-001"]["motor_reembolso_output"]["taxa_cambio"] == 6.00
    assert despesas["s3-001"]["motor_reembolso_output"]["valor_convertido_brl"] == 120.00
    assert despesas["s3-003"]["motor_reembolso_output"]["taxa_cambio"] == 0.035
    assert despesas["s3-003"]["motor_reembolso_output"]["valor_convertido_brl"] == 35.00
    assert despesas["s3-005"]["motor_reembolso_output"]["valor_convertido_brl"] == 157.50
    assert despesas["s3-006"]["motor_reembolso_output"]["valor_convertido_brl"] == 49.72

    # Sem taxa não há valor em BRL para publicar nem para somar.
    for id_despesa in ("s3-004", "s3-008", "s3-009"):
        saida_do_motor = despesas[id_despesa]["motor_reembolso_output"]
        assert saida_do_motor["taxa_cambio"] is None, id_despesa
        assert saida_do_motor["valor_convertido_brl"] is None, id_despesa

    # 120,00 + 25,00 + 35,00 + 157,50 + 49,72 + 88,00. As três sem taxa ficam fora.
    assert resultado["valor_total_despesas"] == 475.22
    # 120,00 + 35,00 + 49,72 + 88,00
    assert resultado["valor_total_reembolsavel"] == 292.72


def test_despesa_sem_cambio_nao_consome_limite_do_dia(tmp_path: Path):
    despesas = por_id(rodar(CAMBIO_MULTIPLOS_DESFECHOS, tmp_path))

    # s3-009 é a única alimentação de 19/09 e foi negada por câmbio; s3-004 é o
    # único transporte de 15/09. Se qualquer uma tivesse consumido limite, a
    # justificativa seria a de limite atingido.
    for id_despesa in ("s3-004", "s3-009"):
        assert (
            "já foi atingido" not in despesas[id_despesa]["motor_reembolso_output"]["justificativa"]
        ), id_despesa


def test_cambio_vazio_nega_toda_despesa_internacional(tmp_path: Path):
    """O mesmo lote de s3, com um arquivo de câmbio sem nenhuma cotação.

    Só s3-007 sobrevive — é a única em BRL. É o teste de que a decisão vem do
    arquivo de câmbio entregue, e não de qualquer tabela embutida no motor.
    """
    resultado = rodar(CAMBIO_MULTIPLOS_DESFECHOS, tmp_path, cambio=CAMBIO_VAZIO)
    despesas = por_id(resultado)

    internacionais = [id_ for id_ in despesas if id_ != "s3-007"]
    for id_despesa in internacionais:
        saida_do_motor = despesas[id_despesa]["motor_reembolso_output"]
        assert saida_do_motor["tipo_reembolso"] == "nenhum", id_despesa
        assert "taxa de câmbio" in saida_do_motor["justificativa"], id_despesa

    assert despesas["s3-007"]["motor_reembolso_output"]["valor_reembolsavel"] == 88.00
    assert resultado["valor_total_despesas"] == 88.00
    assert resultado["valor_total_reembolsavel"] == 88.00


def test_moeda_entra_na_identidade_de_duplicata(tmp_path: Path):
    """CC-MARKETING (padrão: alimentação R$50, transporte R$70).

    * s4-001 sem `moeda` e s4-002 com `"moeda": "BRL"` são o mesmo lançamento.
    * s4-003 é idêntica às duas em todo o resto e está em EUR: **não** é duplicata,
      porque EUR 22,00 e BRL 22,00 são gastos de valores diferentes. Ela vale
      22,00 × 6,00 = R$132,00 e disputa o que sobrou dos R$50,00 do dia — R$28,00,
      porque s4-001 já levou R$22,00.
    * s4-004 (`"usd"`) e s4-005 (`"USD"`) são duplicatas: a comparação usa a forma
      normalizada. s4-004 vale 15,00 × 5,10 = R$76,50 e leva os R$70,00 do limite.
    * s4-006 (`ALIMENTACAO`) e s4-007 (`alimentacao`) também são duplicatas.
    """
    resultado = rodar(DUPLICATAS_E_MOEDA, tmp_path)

    conferir(
        resultado,
        [
            ("s4-001", "total", 22.00, "Reembolso total aprovado"),
            ("s4-002", "nenhum", 0.00, "duplicata da despesa 'Almoco no bistro(s4-001)'"),
            ("s4-003", "parcial", 28.00, "R$50,00 no dia para o centro de custo CC-MARKETING"),
            ("s4-004", "parcial", 70.00, "R$70,00 no dia para o centro de custo CC-MARKETING"),
            ("s4-005", "nenhum", 0.00, "duplicata da despesa 'Corrida ao aeroporto(s4-004)'"),
            ("s4-006", "total", 30.00, "Reembolso total aprovado"),
            ("s4-007", "nenhum", 0.00, "duplicata da despesa 'Jantar de equipe(s4-006)'"),
        ],
    )

    despesas = por_id(resultado)

    # A moeda sai com a grafia lançada, embora a decisão use a normalizada.
    assert despesas["s4-004"]["moeda"] == "usd"
    assert despesas["s4-004"]["motor_reembolso_output"]["taxa_cambio"] == 5.10
    assert despesas["s4-004"]["motor_reembolso_output"]["valor_convertido_brl"] == 76.50

    # E a categoria também.
    assert despesas["s4-006"]["categoria"] == "ALIMENTACAO"

    # 22,00 + 132,00 + 76,50 + 30,00. As três duplicatas ficam fora do bruto.
    assert resultado["valor_total_despesas"] == 260.50
    # 22,00 + 28,00 + 70,00 + 30,00
    assert resultado["valor_total_reembolsavel"] == 150.00


def test_bordas_de_periodo_truncamento_e_as_duas_clausulas_de_categoria(tmp_path: Path):
    """CC-JURIDICO: alimentação R$40,00, `transporte_urbano` com limite R$0,00 e
    **sem** `hospedagem` na tabela.

    * s5-001 cai no primeiro dia do período e s5-002 no último: os dois extremos
      são inclusivos. s5-002 entra como 39,999 e é tratada como R$39,99.
    * s5-003 (um dia antes) e s5-004 (um dia depois) são negadas por período, e
      **somam** no bruto: foram gastos reais.
    * s5-005 e s5-008 são `transporte_urbano`, que a tabela traz com limite R$0,00
      — proibição explícita, não "limite atingido". s5-008 ainda está sem nota
      fiscal e acima do teto: a justificativa tem de ser a da categoria, porque
      RN-008 é o passo 2 e a nota fiscal é o passo 6.
    * s5-006 é `hospedagem`, que o `padrao` tem e a tabela de CC-JURIDICO não —
      e o `padrao` não complementa tabela de centro de custo que existe (AMB-012).
    * s5-007 é estorno: fica fora dos dois totais.
    """
    resultado = rodar(BORDAS_E_TRUNCAMENTO, tmp_path)

    conferir(
        resultado,
        [
            ("s5-001", "total", 40.00, "Reembolso total aprovado"),
            ("s5-002", "total", 39.99, "Reembolso total aprovado"),
            ("s5-003", "nenhum", 0.00, "fora do período de competência"),
            ("s5-004", "nenhum", 0.00, "fora do período de competência"),
            ("s5-005", "nenhum", 0.00, "a política vigente a proíbe explicitamente"),
            ("s5-006", "nenhum", 0.00, "'hospedagem' não é reembolsável"),
            ("s5-007", "nenhum", 0.00, "valor negativo"),
            ("s5-008", "nenhum", 0.00, "a política vigente a proíbe explicitamente"),
        ],
    )

    despesas = por_id(resultado)

    # O valor lançado sai inteiro; o que o motor calcula sai truncado.
    assert despesas["s5-002"]["valor"] == 39.999

    # s5-006 é negada pela cláusula 1 (ausente da tabela) e s5-005 pela cláusula 2
    # (limite R$0,00): situações diferentes, justificativas diferentes.
    assert "não consta na política" in despesas["s5-006"]["motor_reembolso_output"]["justificativa"]
    assert "R$0,00" in despesas["s5-005"]["motor_reembolso_output"]["justificativa"]

    # E nenhuma das duas diz "limite diário atingido": nada foi consumido.
    for id_despesa in ("s5-005", "s5-006", "s5-008"):
        assert (
            "já foi atingido" not in despesas[id_despesa]["motor_reembolso_output"]["justificativa"]
        ), id_despesa

    # A nota fiscal ausente de s5-008 não é a justificativa dela.
    assert "nota fiscal" not in despesas["s5-008"]["motor_reembolso_output"]["justificativa"]

    # 40,00 + 39,99 + 25,00 + 25,00 + 60,00 + 180,00 + 200,00. O estorno fica fora.
    assert resultado["valor_total_despesas"] == 569.99
    # 40,00 + 39,99
    assert resultado["valor_total_reembolsavel"] == 79.99


def test_rn017_recusa_lote_de_competencia_anterior_a_vigencia(tmp_path: Path, capsys):
    """O lote é de 2026-08 e `politica-sintetica.json` vigora a partir de 2026-09."""
    destino = tmp_path / "resultado.json"

    codigo = main(
        [
            "calcular",
            "--input",
            str(DADOS / COMPETENCIA_ANTERIOR),
            "--output",
            str(destino),
            "--politica",
            POLITICA,
            "--cambio",
            CAMBIO,
        ]
    )

    assert codigo != 0
    assert not destino.exists()

    erro = capsys.readouterr().err
    assert "2026-09" in erro
    assert "2026-08" in erro


def test_rn017_recusa_lote_anterior_a_uma_politica_de_outubro(tmp_path: Path, capsys):
    """O mesmo lote de 2026-09 que passa na política de setembro é recusado pela de
    outubro. Só a `vigencia` muda entre os dois arquivos."""
    destino = tmp_path / "resultado.json"

    codigo = main(
        [
            "calcular",
            "--input",
            str(DADOS / LIMITES_POR_CENTRO_DE_CUSTO),
            "--output",
            str(destino),
            "--politica",
            POLITICA_VIGENCIA_FUTURA,
            "--cambio",
            CAMBIO,
        ]
    )

    assert codigo != 0
    assert not destino.exists()
    assert "2026-10" in capsys.readouterr().err


def test_rn017_politica_mais_antiga_continua_valendo(tmp_path: Path):
    """`politica-vigencia-anterior.json` vigora desde 2026-07 e processa o lote de
    2026-08 normalmente — não há política nova para agosto.

    CC-ESTAGIO só tem `alimentacao`, com limite R$25,00: s6-002 (R$30,00) vira
    parcial de R$25,00 e s6-003 (`transporte_urbano`) é negada por categoria.
    """
    resultado = rodar(COMPETENCIA_ANTERIOR, tmp_path, politica=POLITICA_VIGENCIA_ANTERIOR)

    conferir(
        resultado,
        [
            ("s6-001", "total", 20.00, "Reembolso total aprovado"),
            ("s6-002", "parcial", 25.00, "R$25,00 no dia para o centro de custo CC-ESTAGIO"),
            ("s6-003", "nenhum", 0.00, "'transporte_urbano' não é reembolsável"),
        ],
    )

    # 20,00 + 30,00 + 18,00
    assert resultado["valor_total_despesas"] == 68.00
    # 20,00 + 25,00
    assert resultado["valor_total_reembolsavel"] == 45.00


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Defeito conhecido, ainda sem task: `parse_float=Decimal` não cobre inteiros "
        'do JSON, então `"valor": 100` chega como `int` e `_truncar_valor` estoura '
        "com AttributeError. Ver a revisão de 21/08/2026."
    ),
)
def test_valor_inteiro_no_json_e_aceito(tmp_path: Path):
    """`"valor": 100` é um número JSON válido, e a spec.md §4 ("Entrada e saída")
    tipa o campo como "número" — sem exigir casas decimais.

    Sob CC-MARKETING (padrão: alimentação R$50, transporte R$70), s7-001 deveria
    virar parcial de R$50,00 e s7-002 total de R$40,00.
    """
    resultado = rodar(VALOR_INTEIRO, tmp_path)

    conferir(
        resultado,
        [
            ("s7-001", "parcial", 50.00, "R$50,00 no dia para o centro de custo CC-MARKETING"),
            ("s7-002", "total", 40.00, "Reembolso total aprovado"),
        ],
    )

    assert resultado["valor_total_despesas"] == 140.00
    assert resultado["valor_total_reembolsavel"] == 90.00


def test_duplicata_compara_o_valor_lancado(tmp_path: Path):
    """CC-MARKETING (padrão: alimentação R$50,00).

    s8-001 e s8-002 diferem só na terceira casa decimal — `33.333` contra
    `33.334` —, e as duas chegam ao limite diário valendo R$33,33. **Não** são o
    mesmo lançamento: RN-007 compara os campos da entrada e AMB-019 diz que a
    comparação é sobre o valor lançado. s8-001 leva R$33,33 e s8-002 leva os
    R$16,67 que sobraram dos R$50,00 do dia.

    s8-003 e s8-004 são `20.005` as duas: valor lançado idêntico, duplicata de
    verdade, e o valor de s8-004 fica fora do total bruto.
    """
    resultado = rodar(DUPLICATA_E_TRUNCAMENTO, tmp_path)

    conferir(
        resultado,
        [
            ("s8-001", "total", 33.33, "Reembolso total aprovado"),
            ("s8-002", "parcial", 16.67, "R$50,00 no dia para o centro de custo CC-MARKETING"),
            ("s8-003", "total", 20.00, "Reembolso total aprovado"),
            ("s8-004", "nenhum", 0.00, "duplicata da despesa 'Jantar de equipe(s8-003)'"),
        ],
    )

    despesas = por_id(resultado)

    # O valor lançado sai inteiro na saída, e é ele que separa s8-001 de s8-002.
    assert despesas["s8-001"]["valor"] == 33.333
    assert despesas["s8-002"]["valor"] == 33.334

    # 33,33 + 33,33 + 20,00. Só a duplicata de verdade fica fora do bruto.
    assert resultado["valor_total_despesas"] == 86.66
    # 33,33 + 16,67 + 20,00 — os dois primeiros somam exatamente o limite do dia.
    assert resultado["valor_total_reembolsavel"] == 70.00
