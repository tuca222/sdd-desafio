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
    return {
        "id": despesa.id,
        "data": despesa.data.isoformat(),
        "categoria": despesa.categoria_original,
        "descricao": despesa.descricao,
        "fornecedor": despesa.fornecedor,
        "valor": despesa.valor_original,
        "tem_nota_fiscal": despesa.tem_nota_fiscal,
        "motor_reembolso_output": {
            "despesa_reembolsavel": resultado.despesa_reembolsavel,
            "tipo_reembolso": resultado.tipo_reembolso,
            "valor_reembolsavel": resultado.valor_reembolsavel,
            "justificativa": resultado.justificativa,
        },
    }


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
