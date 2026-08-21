from datetime import date
from decimal import Decimal

from src.cambio import carregar_cambio

CAMINHO_CAMBIO = "exemplos/envelope/cambio.json"


def test_taxa_existente_na_data():
    cambio = carregar_cambio(CAMINHO_CAMBIO)

    taxa = cambio.taxa("EUR", date(2026, 7, 14))

    assert taxa == Decimal("5.93")
    assert isinstance(taxa, Decimal)
    assert cambio.taxa("USD", date(2026, 7, 21)) == Decimal("5.48")


def test_rn016_data_sem_cotacao_devolve_none():
    cambio = carregar_cambio(CAMINHO_CAMBIO)

    # 2026-07-18 é sábado: o arquivo não publica cotação nesse dia.
    assert cambio.taxa("EUR", date(2026, 7, 18)) is None
    # E 2026-07-05 está fora do intervalo coberto pelo arquivo.
    assert cambio.taxa("USD", date(2026, 7, 5)) is None


def test_rn016_moeda_ausente_na_data_devolve_none():
    cambio = carregar_cambio(CAMINHO_CAMBIO)

    # A data tem cotação de USD e EUR — o que falta é a moeda, não a data.
    assert cambio.taxa("USD", date(2026, 7, 21)) == Decimal("5.48")
    assert cambio.taxa("GBP", date(2026, 7, 21)) is None


def test_amb016_arquivo_de_cambio_e_a_fonte_da_verdade_sobre_moedas():
    cambio = carregar_cambio(CAMINHO_CAMBIO)

    moedas_publicadas = {moeda for cotacoes in cambio.taxas.values() for moeda in cotacoes}

    # GBP é um código válido na ISO 4217 e não existe para efeito desta spec.
    assert moedas_publicadas == {"USD", "EUR"}
