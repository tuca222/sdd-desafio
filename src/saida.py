from typing import Any

from src.modelos import Colaborador, Despesa, Periodo, ResultadoDespesa, ResultadoFinal


def _colaborador_para_dict(colaborador: Colaborador) -> dict[str, Any]:
    return {
        "id": colaborador.id,
        "nome": colaborador.nome,
        "centro_custo": colaborador.centro_custo,
    }


def _periodo_para_dict(periodo: Periodo) -> dict[str, Any]:
    return {
        "competencia": periodo.competencia,
        "inicio": periodo.inicio.isoformat(),
        "fim": periodo.fim.isoformat(),
    }


def _despesa_para_dict(despesa: Despesa, resultado: ResultadoDespesa) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": despesa.id,
        "data": despesa.data.isoformat(),
        "categoria": despesa.categoria_original,
        "descricao": despesa.descricao,
        "fornecedor": despesa.fornecedor,
        "valor": despesa.valor_original,
    }

    # "Exatamente como entrou" inclui **não ter entrado**: uma despesa que não
    # trouxe `moeda` sai sem o campo, ainda que o motor tenha assumido BRL para
    # decidir — ver spec.md §4 ("Entrada e saída").
    if despesa.moeda_original is not None:
        item["moeda"] = despesa.moeda_original

    item["tem_nota_fiscal"] = despesa.tem_nota_fiscal

    # `valor_convertido_brl` é `null` nos dois casos em que não houve conversão:
    # despesa já em BRL e despesa sem taxa disponível (RN-015, RN-016). É a
    # presença da taxa que separa os dois de uma conversão real.
    houve_conversao = despesa.taxa_cambio is not None
    item["motor_reembolso_output"] = {
        "despesa_reembolsavel": resultado.despesa_reembolsavel,
        "tipo_reembolso": resultado.tipo_reembolso,
        "valor_reembolsavel": resultado.valor_reembolsavel,
        "taxa_cambio": despesa.taxa_cambio,
        "valor_convertido_brl": despesa.valor_brl if houve_conversao else None,
        "justificativa": resultado.justificativa,
    }

    return item


def montar_saida(resultado_final: ResultadoFinal) -> dict[str, Any]:
    return {
        "colaborador": _colaborador_para_dict(resultado_final.colaborador),
        "periodo": _periodo_para_dict(resultado_final.periodo),
        "valor_total_despesas": resultado_final.valor_total_despesas,
        "valor_total_reembolsavel": resultado_final.valor_total_reembolsavel,
        "detalhamento_despesas": [
            _despesa_para_dict(despesa, resultado)
            for despesa, resultado in resultado_final.detalhamento
        ],
    }
