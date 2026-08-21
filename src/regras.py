from datetime import date
from decimal import Decimal

from src.modelos import Despesa, Periodo, ResultadoDespesa
from src.politica import TabelaLimites


def normalizar_categoria(categoria: str) -> str:
    return categoria.lower()


def formatar_reais(valor: Decimal) -> str:
    return f"R${valor:.2f}".replace(".", ",")


def filtro_valor_negativo(despesa: Despesa) -> ResultadoDespesa | None:
    if despesa.valor < 0:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                "Despesa com valor negativo, identificada como estorno. Reembolso negado."
            ),
        )
    return None


def filtro_categoria_invalida(despesa: Despesa, tabela: TabelaLimites) -> ResultadoDespesa | None:
    limite_categoria = tabela.limites.get(despesa.categoria)

    # RN-008, cláusula 1: a política não cobre esse tipo de gasto para o centro
    # de custo. A tabela dele é fechada — o `padrao` não a complementa (AMB-012).
    if limite_categoria is None:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"A categoria '{despesa.categoria}' não é reembolsável para o centro "
                f"de custo {tabela.centro_custo}: ela não consta na política vigente. "
                "Reembolso negado."
            ),
        )

    # RN-008, cláusula 2: a categoria existe na tabela com limite R$0,00. Isso é
    # proibição explícita, nunca "limite diário atingido" — nada foi consumido por
    # despesa nenhuma, e não haveria despesa a citar (AMB-013).
    if limite_categoria.limite == 0:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"A categoria '{despesa.categoria}' não é reembolsável para o centro "
                f"de custo {tabela.centro_custo}: a política vigente a proíbe "
                f"explicitamente, com limite de {formatar_reais(limite_categoria.limite)}. "
                "Reembolso negado."
            ),
        )

    return None


def filtro_fora_periodo(despesa: Despesa, periodo: Periodo) -> ResultadoDespesa | None:
    if despesa.data < periodo.inicio or despesa.data > periodo.fim:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                "Despesa lançada fora do período de competência "
                f"({periodo.inicio.isoformat()} a {periodo.fim.isoformat()}). "
                "Reembolso negado."
            ),
        )
    return None


def _identidade_duplicata(despesa: Despesa) -> tuple[date, str, str, str, Decimal, str, bool]:
    # RN-007/AMB-019: a comparação é sobre o valor **lançado** e a `moeda`
    # normalizada, nunca sobre o valor convertido — senão a decisão passaria a
    # depender da taxa do dia.
    #
    # "Lançado" é `valor_original`, e não `valor`: este último já passou pelo
    # truncamento de RN-010, que a spec aplica antes das verificações de limite e
    # de nota fiscal — não antes desta. Comparar o truncado faria `33.333` e
    # `33.334`, que são gastos diferentes, virarem o mesmo lançamento.
    return (
        despesa.data,
        despesa.categoria,
        despesa.descricao,
        despesa.fornecedor,
        despesa.valor_original,
        despesa.moeda,
        despesa.tem_nota_fiscal,
    )


def filtro_duplicata(
    despesa: Despesa, despesas_anteriores: list[Despesa]
) -> ResultadoDespesa | None:
    for anterior in despesas_anteriores:
        if _identidade_duplicata(despesa) == _identidade_duplicata(anterior):
            return ResultadoDespesa(
                despesa_reembolsavel=False,
                tipo_reembolso="nenhum",
                valor_reembolsavel=Decimal("0.00"),
                justificativa=(
                    "Despesa identificada como duplicata da despesa "
                    f"'{anterior.descricao}({anterior.id})'. Reembolso negado."
                ),
            )
    return None


def filtro_cambio_indisponivel(despesa: Despesa) -> ResultadoDespesa | None:
    # RN-016: sem taxa não existe valor em BRL, e sem valor em BRL não há pergunta
    # a fazer sobre nota fiscal nem sobre limite — a despesa é inavaliável. A
    # justificativa cita moeda e data para que o financeiro saiba o que publicar.
    if despesa.valor_brl is None:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"Não há taxa de câmbio de {despesa.moeda} publicada para "
                f"{despesa.data.isoformat()}, e sem ela a despesa não pode ser "
                "convertida para BRL. Reembolso negado."
            ),
        )
    return None


def filtro_nota_fiscal(despesa: Despesa, teto: Decimal) -> ResultadoDespesa | None:
    # AMB-017: o teto está em BRL, então quem é comparado com ele é o valor
    # convertido, nunca o número lançado na moeda estrangeira.
    if despesa.valor_brl is not None and despesa.valor_brl > teto and not despesa.tem_nota_fiscal:
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"Despesas acima de {formatar_reais(teto)} necessitam "
                "de nota fiscal para reembolso. Esta despesa não possui nota "
                "fiscal. Reembolso negado."
            ),
        )
    return None


def _despesa_que_atingiu_limite(
    limite: Decimal, reembolsos_anteriores: list[tuple[Despesa, Decimal]]
) -> Despesa:
    acumulado = Decimal("0.00")
    for despesa, valor_reembolsado in reembolsos_anteriores:
        acumulado += valor_reembolsado
        if acumulado >= limite:
            return despesa
    return reembolsos_anteriores[-1][0]


def aplicar_limite_diario(
    despesa: Despesa,
    tabela: TabelaLimites,
    reembolsos_anteriores: list[tuple[Despesa, Decimal]],
) -> ResultadoDespesa:
    categoria = despesa.categoria
    # A categoria está na tabela e tem limite maior que zero: `filtro_categoria_invalida`
    # é o passo 2 da ordem e já reprovou os dois casos contrários.
    limite = tabela.limites[categoria].limite
    # E `valor_brl` não é None: `filtro_cambio_indisponivel` é o passo 5 e já
    # reprovou toda despesa sem taxa. Só o valor em BRL disputa limite (RN-015).
    valor_em_brl = despesa.valor_brl

    consumido = sum((valor for _, valor in reembolsos_anteriores), Decimal("0.00"))
    disponivel = limite - consumido

    if disponivel <= 0:
        original = _despesa_que_atingiu_limite(limite, reembolsos_anteriores)
        return ResultadoDespesa(
            despesa_reembolsavel=False,
            tipo_reembolso="nenhum",
            valor_reembolsavel=Decimal("0.00"),
            justificativa=(
                f"A categoria {categoria} possui limite de reembolso de "
                f"{formatar_reais(limite)} no dia para o centro de custo "
                f"{tabela.centro_custo}. Este valor já foi atingido na "
                f"despesa '{original.descricao}({original.id})'. Reembolso negado."
            ),
        )

    if valor_em_brl <= disponivel:
        return ResultadoDespesa(
            despesa_reembolsavel=True,
            tipo_reembolso="total",
            valor_reembolsavel=valor_em_brl,
            justificativa="Reembolso total aprovado de acordo com a política vigente.",
        )

    return ResultadoDespesa(
        despesa_reembolsavel=True,
        tipo_reembolso="parcial",
        valor_reembolsavel=disponivel,
        justificativa=(
            f"A categoria {categoria} possui limite de reembolso de "
            f"{formatar_reais(limite)} no dia para o centro de custo "
            f"{tabela.centro_custo}. Reembolso parcial aprovado."
        ),
    )
