from src.regras import normalizar_categoria


def test_rn011_normaliza_categoria_case_insensitive():
    assert normalizar_categoria("ALIMENTACAO") == "alimentacao"
