from decimal import Decimal

LIMITE_ALIMENTACAO = Decimal("60.00")
LIMITE_TRANSPORTE_URBANO = Decimal("80.00")
LIMITE_HOSPEDAGEM = Decimal("250.00")
LIMITE_NOTA_FISCAL = Decimal("100.00")

CATEGORIAS_VALIDAS = {"alimentacao", "transporte_urbano", "hospedagem"}

LIMITES_DIARIOS_POR_CATEGORIA = {
    "alimentacao": LIMITE_ALIMENTACAO,
    "transporte_urbano": LIMITE_TRANSPORTE_URBANO,
    "hospedagem": LIMITE_HOSPEDAGEM,
}
