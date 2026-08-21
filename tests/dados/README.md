# Massa sintética de teste

Arquivos de entrada reais — despesas, política e câmbio — usados por
`tests/test_dados_sinteticos.py`. Eles rodam a CLI de verdade, arquivo de entrada →
arquivo de saída, como os de `exemplos/`.

**Por que não usar os de `exemplos/`.** Os arquivos daqui não compartilham nenhum
número com o enunciado: outros centros de custo, outros limites, outras moedas,
outro teto de nota fiscal (R$150,00, não R$100,00) e outra competência (2026-09,
não 2026-07). Um motor que tivesse os limites do enunciado embutidos no código
passaria nos testes de `exemplos/` e quebraria em todos os daqui — é isso que esta
pasta existe para detectar.

Os dados são inventados. As taxas de câmbio foram escolhidas redondas
(`USD 5,00`, `EUR 6,00`, `JPY 0,035`) para que cada conversão possa ser conferida
de cabeça contra o valor esperado escrito em `tests/test_dados_sinteticos.py`.

## Política e câmbio

| Arquivo | O que traz |
|---|---|
| `politica-sintetica.json` | A política base. Vigora a partir de `2026-09-01`. Teto de nota fiscal R$150,00. Quatro tabelas: `padrao` (alimentação R$50, transporte R$70, hospedagem R$200), `CC-VENDAS-LATAM` (alimentação R$120, transporte R$90, hospedagem R$500 e `representacao` R$250), `CC-JURIDICO` (alimentação R$40 e `transporte_urbano` com limite **R$0,00**, sem `hospedagem`) e `CC-ESTAGIO` (só `alimentacao`, R$25). |
| `politica-vigencia-futura.json` | Idêntica à base, **exceto** `vigencia: 2026-10-05`. Existe para que a recusa de RN-017 seja atribuível só à vigência. |
| `politica-vigencia-anterior.json` | Idêntica à base, **exceto** `vigencia: 2026-07-01`. Mostra que uma política antiga continua valendo em competências posteriores. |
| `cambio-sintetico.json` | Cobre `2026-09-14` a `2026-09-18` (segunda a sexta). `JPY` só é publicado em 14/09 e 16/09; `GBP` nunca; o fim de semana de 19–20/09 não existe no arquivo. |
| `cambio-vazio.json` | `"taxas": {}`. Toda despesa internacional cai em RN-016. |

## Lotes de despesas

| Arquivo | Centro de custo | O que exercita |
|---|---|---|
| `despesas-01-limites-por-centro-de-custo.json` | `CC-VENDAS-LATAM` | Limites próprios do centro de custo; valor exatamente **igual** ao limite reembolsando `total`; teto de nota fiscal em R$149,99 (passa) e R$150,01 (nega); categoria ausente da tabela de um centro de custo que existe. |
| `despesas-02-centro-de-custo-sem-entrada.json` | `CC-MARKETING` | Queda no `padrao` (RN-014); um limite diário dividido por **três** lançamentos; qual despesa a justificativa cita quando o limite esgota na segunda, e não na primeira. |
| `despesas-03-cambio-multiplos-desfechos.json` | `CC-VENDAS-LATAM` | Os quatro desfechos de câmbio na mesma entrada: conversão normal, moeda ausente na data, data ausente do arquivo e despesa sem o campo `moeda`. Taxa menor que 1 (`JPY`), truncamento que difere do arredondamento (`EUR 7,77 × 6,40 = 49,728 → 49,72`) e teto de nota fiscal comparado contra o valor **convertido**. |
| `despesas-04-duplicatas-e-moeda.json` | `CC-MARKETING` | AMB-019 nas duas direções: sem `moeda` e `"BRL"` são duplicatas, `"EUR"` não é. Moeda em minúsculas (`"usd"`) e categoria em maiúsculas (`ALIMENTACAO`) entrando na identidade já normalizadas. |
| `despesas-05-bordas-e-truncamento.json` | `CC-JURIDICO` | Primeiro e último dia do período (inclusivos) e um dia de cada lado (negados); `39.999` truncado; as **duas** cláusulas de RN-008 lado a lado (limite `0.00` vs. categoria ausente); AMB-012 (o `padrao` não completa tabela existente); estorno fora dos totais; e a ordem RN-008 (passo 2) antes de RN-005 (passo 6). |
| `despesas-06-competencia-anterior.json` | `CC-ESTAGIO` | Lote de competência `2026-08`. Recusado pela política de setembro, aceito pela de julho. Também exercita um centro de custo com **uma única** categoria. |
| `despesas-07-valor-inteiro.json` | `CC-MARKETING` | `"valor": 100` — número JSON válido, sem casas decimais. **Hoje o motor aborta com este arquivo**; o teste correspondente está marcado `xfail(strict=True)` e vira `XPASS` no instante em que o defeito for corrigido. Ver a nota abaixo. |

## Defeito conhecido reproduzido por `despesas-07`

`parser.py` lê a entrada com `json.load(..., parse_float=Decimal)`, e `parse_float`
não é consultado para números **inteiros** do JSON: `"valor": 100` chega como `int`,
e `_truncar_valor` chama `.quantize` nele, o que estoura com
`AttributeError: 'int' object has no attribute 'quantize'` — traceback não tratado,
código de saída 1, nenhum arquivo escrito.

A spec.md §4 ("Entrada e saída") tipa `despesas[].valor` como "número" e não exige
casas decimais, então a entrada é válida e o código é o bug. Nenhuma task cobre isso
ainda.
