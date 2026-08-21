# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [x] **T-001** — Scaffolding do projeto (`pyproject.toml`, estrutura `src/` + `tests/`, config `pytest`/`ruff`)
  - **Atende:** infraestrutura (sem RN — setup de projeto)
  - **Aceite:** `pytest` roda (coleção vazia, sem erro) e `ruff check .` roda sem erro de configuração
  - **Commit:** `2312112`

- [x] **T-002** — Modelos de dados (`dataclasses` frozen: `Colaborador`, `Periodo`, `Despesa`, `ResultadoDespesa`, `ResultadoFinal`)
  - **Atende:** spec.md §4 ("Entrada e saída")
  - **Aceite:** `tests/test_modelos.py` — instancia cada dataclass e confirma imutabilidade (`frozen=True`)
  - **Commit:** `81e46b0`

- [x] **T-003** — Constantes de política (`src/politica.py`: `LIMITE_ALIMENTACAO`, `LIMITE_TRANSPORTE_URBANO`, `LIMITE_HOSPEDAGEM`, `LIMITE_NOTA_FISCAL`, `CATEGORIAS_VALIDAS`)
  - **Atende:** RN-001, RN-002, RN-003, RN-005, RN-008
  - **Aceite:** `tests/test_politica.py` — confirma o valor exato de cada constante
  - **Commit:** `bc88987`

- [x] **T-004** — Parser: leitura do JSON de entrada com `Decimal` (`parse_float=Decimal`) e construção dos dataclasses
  - **Atende:** spec.md §4 ("Entrada e saída")
  - **Aceite:** `tests/test_parser.py::test_parse_carrega_campos_da_entrada` — carrega `despesas-exemplo.json` e confirma tipos/valores
  - **Commit:** `accc227`

- [x] **T-005** — Truncamento RN-010 na borda do parser (aplicado no momento em que `Despesa` é construída)
  - **Atende:** RN-010
  - **Aceite:** `tests/test_parser.py::test_rn010_trunca_casas_decimais_excedentes` (`d-011`: `33.333` → `33.33`)
  - **Commit:** `97e4d09`

## Fase 2 — Regras de negócio

- [x] **T-006** — Normalização de categoria (comparação case-insensitive)
  - **Atende:** RN-011
  - **Aceite:** `tests/test_regras.py::test_rn011_normaliza_categoria_case_insensitive` (`d-014`: `ALIMENTACAO` → `alimentacao`)
  - **Commit:** `5defc0f`

- [x] **T-007** — Filtro: valor negativo / estorno
  - **Atende:** RN-009
  - **Aceite:** `tests/test_regras.py::test_rn009_valor_negativo_ignorado` (`d-009`)
  - **Commit:** `60fbd69`

- [x] **T-008** — Filtro: categoria fora da política (usa a normalização de T-006)
  - **Atende:** RN-008, RN-011
  - **Aceite:** `tests/test_regras.py::test_rn008_categoria_fora_da_politica` (`d-005`, categoria `coworking`)
  - **Commit:** `af28133`

- [x] **T-009** — Filtro: fora do período de competência (limites inclusivos nos dois extremos)
  - **Atende:** RN-006
  - **Aceite:** `tests/test_regras.py::test_rn006_fora_do_periodo_negado` (`d-008`) + `test_rn006_data_no_extremo_do_periodo_aceita`
  - **Commit:** `07e0e4f`

- [x] **T-010** — Filtro: duplicata (todos os campos idênticos exceto `id`)
  - **Atende:** RN-007
  - **Aceite:** `tests/test_regras.py::test_rn007_duplicata_negada_primeira_mantida` (`d-006`/`d-007`)
  - **Commit:** `5b80d86`

- [x] **T-011** — Filtro: nota fiscal obrigatória (estritamente maior que R$100,00)
  - **Atende:** RN-005
  - **Aceite:** `tests/test_regras.py::test_rn005_nota_fiscal_obrigatoria_acima_de_100` + `test_rn005_valor_exatamente_100_nao_exige` (`d-003`)
  - **Commit:** `3c15471`

- [x] **T-012** — Pipeline de filtros em `motor.py`, aplicados na ordem da spec.md §8 ("Ordem de aplicação das regras"), uma única justificativa por despesa
  - **Atende:** RN-005, RN-006, RN-007, RN-008, RN-009, RN-013
  - **Aceite:** `tests/test_motor.py::test_pipeline_aplica_filtros_na_ordem_definida` (`d-004`: negado por nota fiscal ausente, não por limite diário já esgotado — AMB-004)
  - **Commit:** `292a7ee`

- [x] **T-013** — Agregação de limite diário: categorias `alimentacao` e `transporte_urbano` (soma por categoria+dia, ordem de entrada, corta excedente)
  - **Atende:** RN-001, RN-002, RN-004
  - **Aceite:** `tests/test_regras.py::test_rn001_limite_diario_alimentacao` (`d-001`/`d-002`) + `test_rn002_limite_diario_transporte` (`d-003`)
  - **Commit:** `0c6fb7c`

- [x] **T-014** — Limite diário de hospedagem (agregado por dia, como RN-001/RN-002; noites do texto livre ignoradas)
  - **Atende:** RN-003, RN-004
  - **Aceite:** `tests/test_regras.py::test_rn003_limite_diario_hospedagem` (`d-010`) + `tests/test_motor.py::test_rn003_hospedagem_compartilha_limite_diario_no_mesmo_dia`
  - **Commit:** `0fc3bd2`

- [x] **T-015** — Confirma que o adicional de viagem não é aplicado em nenhuma circunstância
  - **Atende:** RN-012
  - **Aceite:** `tests/test_regras.py::test_rn012_sem_adicional_de_viagem` + `tests/test_motor.py::test_rn012_hospedagem_no_periodo_nao_amplia_limites` (cenário que AMB-005 proíbe inferir)
  - **Commit:** `57b8d27`

## Fase 3 — Casos de borda

- [x] **T-016** — Limite exato de nota fiscal (`d-003`, R$100,00) e ordem nota-fiscal-antes-de-limite-diário (`d-004`)
  - **Atende:** RN-005, RN-013, AMB-003, AMB-004
  - **Aceite:** `tests/test_casos_borda.py::test_valor_exatamente_no_limite_nota_fiscal` + `test_ordem_nota_fiscal_antes_de_limite_diario`
  - **Commit:** `a10891f`

- [x] **T-017** — Despesa em fim de semana, sem regra especial
  - **Atende:** (confirma ausência de regra — spec.md §7, "Casos de borda")
  - **Aceite:** `tests/test_casos_borda.py::test_despesa_fim_de_semana_sem_regra_especial` (`d-012`)
  - **Commit:** `f70db69`

- [x] **T-018** — Hospedagem multi-diária: noites do texto livre ignoradas, limite é o do dia (`d-010` com nota fiscal, `d-013` sem nota fiscal)
  - **Atende:** RN-003, RN-005, AMB-006
  - **Aceite:** `tests/test_casos_borda.py::test_hospedagem_multi_diaria_sem_campo_estruturado`
  - **Commit:** `274e21d`

- [x] **T-019** — Categoria em maiúsculas concorrendo normalmente ao limite diário
  - **Atende:** RN-011, AMB-009
  - **Aceite:** `tests/test_casos_borda.py::test_categoria_maiuscula_concorre_ao_limite_diario` (`d-014`)
  - **Commit:** `bfb4add`

## Correções de rota

> Tasks criadas **depois** do planejamento inicial, a partir de algo detectado
> durante a implementação. A numeração continua de T-023 — não reinicia e não se
> encaixa na numeração das fases, porque o eixo da rastreabilidade é o número da
> task, não a posição dela no arquivo.

- [x] **T-024** — Normalização de categoria na borda de entrada (`parser.py`), com a categoria original preservada para a saída
  - **Atende:** RN-011, RN-007, AMB-009
  - **Executar antes de:** T-020 (a saída depende de qual campo ecoar)
  - **Aceite:** `tests/test_parser.py::test_rn011_normaliza_categoria_na_borda_de_entrada` (`d-014`: `categoria == "alimentacao"` e `categoria_original == "ALIMENTACAO"`) + `tests/test_regras.py::test_rn007_duplicata_ignora_capitalizacao_da_categoria`
  - **Commit:** `ddc5f6f`

- [x] **T-025** — `motor.calcular()`: monta o `ResultadoFinal` computando `valor_total_despesas` e `valor_total_reembolsavel`
  - **Atende:** spec.md §4 ("Entrada e saída"), RN-007, RN-009
  - **Por que existe:** nenhuma task do planejamento original computava os dois
    totais. A T-020 (`saida.py`) apenas serializa o `ResultadoFinal`, e a T-021
    (`cli.py`) apenas orquestra — o cálculo ficou sem dono. Não é soma trivial:
    `valor_total_despesas` exclui negativos (RN-009) e duplicatas (RN-007), mas
    **inclui** despesas negadas por categoria fora da política (RN-008) e por
    período (RN-006). Saber quais foram duplicatas é conhecimento que só existe
    dentro de `aplicar_filtros`, e hoje é descartado quando a função retorna.
  - **Executar antes de:** T-021 e T-022 (sem os totais, a integração não fecha
    `valor_total_despesas = 1806.94`)
  - **Aceite:** `tests/test_motor.py::test_calcula_totais_do_periodo` — sobre
    `exemplos/despesas-exemplo.json`, `valor_total_despesas == 1806.94` (exclui
    `d-007` e `d-009`, inclui `d-005` e `d-008`) e
    `valor_total_reembolsavel == 585.43`
  - **Commit:** `147ce8d`

- [x] **T-026** — Saída ecoa o `valor` da despesa como veio na entrada, sem truncar
  - **Atende:** spec.md §4 ("Entrada e saída"), RN-010
  - **Por que existe:** detectado ao rodar `parser → motor → saida` completo
    contra o exemplo. `d-011` entra com `33.333`; o `resultado-exemplo.json`
    espera `"valor": 33.333` no detalhamento, mas `valor_reembolsavel: 33.33`.
    Hoje a saída emite o valor truncado nos dois lugares. A distinção é real e
    verificável: somar os truncados dá exatamente `1806.94` (o número da spec),
    somar os originais daria `1806.943`. Ou seja — **o truncado é para calcular,
    o original é para exibir**. Mesma classe de problema de [[T-024]]
    (`categoria`/`categoria_original`), que passou despercebida para `valor`.
  - **Escopo:** `Despesa` ganha `valor_original`; `saida.py` ecoa esse campo em
    `detalhamento_despesas[].valor`. Nada mais muda — `valor_reembolsavel` e os
    dois totais continuam truncados em 2 casas, porque são calculados a partir
    de `valor` (já truncado na borda por DT-002).
  - **Executar antes de:** T-022 (a integração compara a saída inteira)
  - **Aceite:** `tests/test_saida.py::test_saida_ecoa_o_valor_como_veio_na_entrada`
    (`d-011`: `valor == 33.333` e `motor_reembolso_output.valor_reembolsavel == 33.33`)
  - **Commit:** `4b11965`

- [x] **T-027** — Valores monetários da saída preservam a escala do `Decimal`: serialização deixa de passar por `float`
  - **Atende:** spec.md §4 ("Entrada e saída") — os campos ecoados da entrada
    saem "exatamente como entraram" e os valores produzidos pelo motor saem com
    2 casas decimais
  - **Depende de:** mudança em `spec.md` §4 ("Entrada e saída") trocando "sempre
    tem no máximo 2 casas decimais" por "sempre sai com exatamente 2 casas
    decimais" para `valor_reembolsavel`, `valor_total_despesas` e
    `valor_total_reembolsavel`. A redação atual ("no máximo") permite `60.0`, que
    é justamente o defeito — sem esse ajuste a task não tem regra que a sustente.
    Mudança atômica em três partes (conteúdo + versão/status + entrada em
    `DECISIONS.md`), feita **antes** desta task.
  - **Por que existe:** detectado rodando o README ponta a ponta contra
    `exemplos/despesas-exemplo.json`. A saída emite `"valor": 72.5` e
    `"valor_reembolsavel": 60.0` onde `exemplos/resultado-exemplo.json` traz
    `72.50` e `60.00`. A causa é `saida.py::_valor`, que faz `float(Decimal)`:
    `Decimal("72.50")` carrega a escala (dois dígitos após a vírgula), `float`
    não carrega nada — `json.dump` serializa pelo `repr` do `float` e a casa
    decimal terminada em zero desaparece. Só escapam os valores cujo último
    dígito não é zero (`1806.94`, `585.43`, `33.333`, `33.33`), o que fez o
    defeito parecer localizado quando é geral.
    O pipeline **já está correto**: `parser.py` lê com
    `parse_float=Decimal`, `valor_original` guarda o texto exato da entrada
    (`Decimal("72.50")`, `Decimal("33.333")`) e todo valor produzido pelo motor
    já chega em `saida.py` com escala 2 (`Decimal("60.00")`,
    `Decimal("0.00")`). Nenhum `quantize` novo é necessário — o defeito nasce e
    morre na conversão para `float`.
    Mesma classe de problema de [[T-024]] (`categoria`/`categoria_original`) e
    [[T-026]] (`valor`/`valor_original`): o que o motor calcula e o que o
    relatório exibe não são a mesma coisa. Aqui a diferença não é de valor, é de
    **escala** — e a escala também é informação de auditoria: `R$60,00` é o que
    o financeiro confere contra o comprovante, `R$60,0` não é formato de dinheiro.
  - **Escopo:** `saida.py` deixa de converter para `float` e entrega o `Decimal`
    intacto no dict; `cli.py` ganha um `json.JSONEncoder` que serializa `Decimal`
    como número literal (via `default()` + substituição no `iterencode()`, já que
    o encoder padrão não tem gancho para números fora de `int`/`float`). Nada
    mais muda: nenhuma regra de negócio, nenhum limite, nenhum total.
    Revisar também `plan.md` DT-004 ("Serialização de `Decimal` na saída"), que
    hoje decide o contrário desta task e descarta explicitamente o encoder
    customizado com a justificativa "a representação textual do `float`
    resultante é exata para esses valores" — verdadeira quanto ao *valor*, falsa
    quanto à *escala*. DT-004 precisa ser reescrita e `plan.md` ter a versão
    incrementada no mesmo commit.
  - **Achado durante a execução:** a primeira versão do encoder usava um
    marcador fixo (`@decimal@`). Como a substituição varre todos os fragmentos
    serializados, inclusive os de string, uma `descricao` da entrada contendo
    esse texto era convertida em número na saída — o arquivo continuava sendo
    JSON válido, então a corrupção seria silenciosa. O marcador passou a ser
    sorteado a cada execução (`uuid4`), com regressão coberta por
    `tests/test_cli.py::test_cli_nao_confunde_texto_da_entrada_com_valor_monetario`.
  - **Aceite:** dois testes, ambos sobre o **texto** do arquivo gerado (a
    comparação atual em `tests/test_integracao.py` faz `json.loads` dos dois
    lados e compara dicts, então `72.5 == 72.50` passa — foi por isso que o
    defeito atravessou a T-022):
    1. `tests/test_cli.py::test_cli_escreve_valores_monetarios_com_duas_casas` —
       no texto do `resultado.json` gerado, `"valor": 72.50`,
       `"valor_reembolsavel": 60.00` e `"valor_reembolsavel": 0.00` aparecem
       literalmente, e `d-011` mantém `"valor": 33.333` com
       `"valor_reembolsavel": 33.33`
    2. `tests/test_integracao.py::test_saida_bate_com_o_exemplo_caractere_a_caractere` —
       o texto gerado é idêntico ao de `exemplos/resultado-exemplo.json`
       (verificado: com a correção o `diff` acusa apenas a ausência de newline
       final no arquivo de exemplo)
  - **Commit:** `1e3b66e`

## Fase 4 — Saída e CLI

- [x] **T-020** — `saida.py`: monta o dict de saída completo (`valor_total_despesas`, `valor_total_reembolsavel`, `detalhamento_despesas[].motor_reembolso_output`), conversão `Decimal → float` só na borda
  - **Atende:** spec.md §4 ("Entrada e saída")
  - **Aceite:** `tests/test_saida.py::test_monta_saida_conforme_schema`
  - **Commit:** `5c090ad`

- [x] **T-021** — `cli.py`: subcomando `calcular --input --output`, orquestra parser → motor → saida → escrita em arquivo
  - **Atende:** interface fixa do desafio (`DESAFIO.md`), spec.md §4 ("Entrada e saída"), spec.md §3 ("Fora de escopo" — não altera a entrada)
  - **Aceite:** `tests/test_cli.py::test_cli_calcular_gera_arquivo_de_saida`
  - **Commit:** `62714b8`

- [x] **T-022** — Teste de integração ponta a ponta contra todos os critérios de aceite da spec.md §9 ("Critérios de aceite")
  - **Atende:** spec.md §9 ("Critérios de aceite") — todos os itens, incluindo `valor_total_despesas = 1806.94` e `valor_total_reembolsavel = 585.43`
  - **Aceite:** `tests/test_integracao.py::test_exemplo_completo_bate_com_criterios_de_aceite`
  - **Commit:** `d397c72`

- [x] **T-023** — `README.md` com instruções de rodar (`python -m src.cli calcular --input despesas.json --output resultado.json`) e testar (`pytest -v`)
  - **Atende:** estrutura de entrega exigida pelo desafio
  - **Aceite:** seguir os passos do README do zero produz `resultado.json` sem intervenção manual
  - **Verificado em:** checkout limpo via `git archive` (sem `.venv`), venv novo com pip 24.0 — rodar sem instalar nada gerou `resultado.json` idêntico ao exemplo; os passos de teste levaram a 57 testes passando e `ruff` limpo
  - **Commit:** `cb7121c`

---

## Fase 5 — Envelope (Política de Reembolso v4)

Origem: `exemplos/rh_politica_v4.md`, itens A e B. Decisões de spec em
`DECISIONS.md` [[D-010]] e [[D-011]]. A numeração continua de T-027; nada das
fases anteriores é renumerado.

A ordem abaixo é a de execução, e é também a numérica. Ela não é arbitrária:
T-028 a T-031 constroem os dados de que todas as regras dependem, T-032 e T-033
fecham a entrada pela CLI (RN-017 precisa da política já carregada para poder
recusar o lote), e T-043 é o ponto em que a suíte volta a ficar verde por
inteiro. Até lá é esperado que os testes de RN-001, RN-002, RN-003, RN-005 e
RN-008 estejam quebrados.

- [x] **T-028** — `politica.py`: substitui as constantes por um carregador que lê o JSON da política com `parse_float=Decimal` e devolve `Politica`, `TabelaLimites` e `LimiteCategoria`
  - **Atende:** spec.md §4 ("Entrada e saída"), plan.md §4 ("Como a política é representada"), plan.md DT-006
  - **Aceite:** `tests/test_politica.py::test_carrega_politica_com_valores_decimais`
  - **Commit:** `e848ff8`

- [x] **T-029** — `politica.py`: `Politica.tabela_para(centro_custo)` resolve a tabela aplicável — entrada própria integral, ou `padrao` integral, sem merge
  - **Atende:** RN-014, AMB-012
  - **Aceite:** `tests/test_politica.py::test_rn014_centro_custo_com_entrada_usa_a_propria_tabela`, `::test_rn014_centro_custo_sem_entrada_cai_no_padrao`, `::test_amb012_tabela_do_centro_custo_nao_e_complementada_pelo_padrao`
  - **Commit:** `e844b8a`

- [x] **T-030** — `politica.py`: `Politica.vigencia_cobre(competencia)`, comparando a competência da `vigencia` com a do lote pelo operador "igual ou anterior"
  - **Atende:** RN-017, AMB-020, plan.md DT-008
  - **Aceite:** `tests/test_politica.py::test_rn017_vigencia_da_competencia_do_lote_cobre`, `::test_rn017_vigencia_de_competencia_anterior_cobre`, `::test_rn017_vigencia_de_competencia_posterior_nao_cobre`
  - **Commit:** `88d6681`

- [x] **T-031** — `cambio.py`: carrega `cambio.json` e expõe `TabelaCambio.taxa(moeda, data) -> Decimal | None`, devolvendo `None` tanto para data ausente quanto para moeda ausente na data
  - **Atende:** spec.md §4 ("Entrada e saída"), RN-015, RN-016
  - **Aceite:** `tests/test_cambio.py::test_taxa_existente_na_data`, `::test_rn016_data_sem_cotacao_devolve_none`, `::test_rn016_moeda_ausente_na_data_devolve_none`
  - **Commit:** `be07c05`

- [x] **T-032** — `cli.py`: flags opcionais `--politica` e `--cambio`, com default; carrega os dois arquivos e os passa adiante. A invocação fixa do `DESAFIO.md` continua funcionando sem elas
  - **Atende:** spec.md §4 ("Entrada e saída"), interface fixa do desafio (`DESAFIO.md`), plan.md DT-006
  - **Aceite:** `tests/test_cli.py::test_cli_calcular_gera_arquivo_de_saida`, `::test_cli_aceita_politica_e_cambio_alternativos`
  - **Commit:** `90d428b`

- [x] **T-033** — `cli.py`: quando `vigencia_cobre` reprova, imprime em `stderr` o motivo citando as duas competências, **não escreve arquivo de saída** e encerra com código diferente de zero
  - **Atende:** RN-017, plan.md DT-008
  - **Aceite:** `tests/test_cli.py::test_rn017_lote_de_competencia_anterior_nao_gera_saida`, `::test_rn017_lote_coberto_gera_saida_normalmente`
  - **Commit:** `58d36ff`

- [x] **T-034** — `modelos.py`/`parser.py`: `Despesa` ganha `moeda` e `moeda_original`; a moeda é normalizada para maiúsculas na borda e assume `BRL` quando o campo não vem
  - **Atende:** RN-015, plan.md DT-005
  - **Aceite:** `tests/test_parser.py::test_rn015_moeda_ausente_assume_brl`, `::test_rn015_moeda_normalizada_para_maiusculas`, `::test_rn015_moeda_original_preservada_como_none_quando_ausente`
  - **Commit:** `81c6e6b`

- [x] **T-035** — `parser.py`: converte a despesa para BRL na borda, preenchendo `valor_brl` e `taxa_cambio` (ou os dois com `None` quando não há taxa); trunca o valor convertido em 2 casas
  - **Atende:** RN-015, RN-010, AMB-018, plan.md DT-007
  - **Aceite:** `tests/test_parser.py::test_rn015_converte_pela_taxa_da_data_da_despesa`, `::test_amb018_valor_convertido_e_truncado_nao_arredondado`, `::test_rn015_despesa_em_brl_nao_tem_taxa`
  - **Commit:** `b6c0e20`

- [x] **T-036** — `regras.py` + `motor.py`: `filtro_cambio_indisponivel` entra na posição 5 da ordem, entre duplicata e nota fiscal
  - **Atende:** RN-016, RN-013, AMB-015, AMB-016, spec.md §8 ("Ordem de aplicação das regras")
  - **Aceite:** `tests/test_regras.py::test_rn016_cambio_indisponivel_nega_despesa`, `tests/test_motor.py::test_pipeline_aplica_filtros_na_ordem_definida`
  - **Commit:** `be1f28a`

- [x] **T-037** — `regras.py`: `filtro_categoria_invalida` passa a receber a `TabelaLimites` e a cobrir as duas cláusulas de RN-008 (categoria ausente, categoria com limite `0.00`), com justificativas distintas
  - **Atende:** RN-008, AMB-013, RN-014
  - **Aceite:** `tests/test_regras.py::test_rn008_categoria_ausente_da_tabela_do_centro_custo`, `::test_amb013_categoria_com_limite_zero_nega_citando_proibicao`
  - **Commit:** `b7fcfec`

- [x] **T-038** — `regras.py`: `filtro_nota_fiscal` compara o valor em BRL contra o teto vindo da política, não a constante nem o valor lançado
  - **Atende:** RN-005, AMB-017, AMB-003
  - **Aceite:** `tests/test_regras.py::test_amb017_teto_de_nota_fiscal_compara_valor_convertido`, `::test_rn005_valor_exatamente_no_teto_nao_exige`
  - **Commit:** `608b8a6`

- [x] **T-039** — `regras.py`/`motor.py`: o limite diário vem da `TabelaLimites` do centro de custo e agrega o valor em BRL; a justificativa passa a citar o centro de custo
  - **Atende:** RN-001, RN-002, RN-003, RN-004, RN-014, RN-015
  - **Aceite:** `tests/test_regras.py::test_rn001_limite_diario_alimentacao`, `::test_rn002_limite_diario_transporte`, `::test_rn003_limite_diario_hospedagem`, `::test_rn014_limite_varia_por_centro_de_custo`
  - **Commit:** `9419e32`

- [x] **T-040** — `regras.py`: `moeda` entra na identidade de duplicata, na forma normalizada e sobre o valor lançado
  - **Atende:** RN-007, AMB-019
  - **Aceite:** `tests/test_regras.py::test_amb019_moedas_diferentes_nao_sao_duplicatas`, `::test_amb019_moeda_ausente_e_brl_explicito_sao_duplicatas`
  - **Commit:** `b8118ec`

- [x] **T-041** — `motor.py`: `valor_total_despesas` exclui despesa sem valor em BRL, além da duplicata e do estorno que já excluía
  - **Atende:** RN-016, RN-007, RN-009
  - **Aceite:** `tests/test_motor.py::test_rn016_despesa_sem_cambio_fora_do_total_bruto`, `::test_calcula_totais_do_periodo`
  - **Commit:** `a812cad`

- [x] **T-042** — `saida.py`: `motor_reembolso_output` ganha `taxa_cambio` e `valor_convertido_brl`; o dict de saída ecoa `moeda` só quando ela veio na entrada
  - **Atende:** spec.md §4 ("Entrada e saída"), RN-015
  - **Aceite:** `tests/test_saida.py::test_saida_publica_taxa_e_valor_convertido`, `::test_saida_omite_moeda_quando_a_entrada_nao_trouxe`
  - **Commit:** `2d1db8b`

- [x] **T-043** — Regrava `exemplos/resultado-exemplo.json` sob a v4 e atualiza `tests/test_integracao.py` para o primeiro bloco da spec.md §9 ("Critérios de aceite")
  - **Atende:** spec.md §9 ("Critérios de aceite"), primeiro bloco — `valor_total_despesas = 1806.94`, `valor_total_reembolsavel = 351.43`
  - **Aceite:** `tests/test_integracao.py::test_exemplo_completo_bate_com_criterios_de_aceite`, `::test_saida_bate_com_o_exemplo_caractere_a_caractere`
  - **Commit:** `4eacf1f`

- [x] **T-044** — Teste de integração de `exemplos/envelope/despesas-envelope-cc-desconhecido.json`
  - **Atende:** spec.md §9 ("Critérios de aceite"), segundo bloco — `valor_total_despesas = 623.76`, `valor_total_reembolsavel = 373.76`
  - **Aceite:** `tests/test_integracao.py::test_envelope_cc_desconhecido_bate_com_criterios_de_aceite`
  - **Commit:** `439b5da`

- [x] **T-045** — Teste de integração de `exemplos/envelope/despesas-envelope.json`
  - **Atende:** spec.md §9 ("Critérios de aceite"), terceiro bloco — `valor_total_despesas = 2278.72`, `valor_total_reembolsavel = 1053.26`
  - **Aceite:** `tests/test_integracao.py::test_envelope_comercial_bate_com_criterios_de_aceite`
  - **Commit:** `8202a04`

---

## Fase 6 — Validação com massa de dados própria

Origem: pedido do usuário em `21/08/2026` ("revise o código implementado; crie
dados sintéticos para validar a implementação"). Não veio de mudança de spec —
nenhuma regra de negócio nova entra aqui. A numeração continua de T-045.

- [x] **T-046** — Massa sintética em `tests/dados/` (política, câmbio e sete lotes
  de despesas) mais os testes que rodam a CLI contra ela
  - **Atende:** spec.md §9 ("Critérios de aceite") — por outro caminho: os
    critérios da spec fixam o resultado para **um** conjunto de dados, e esta task
    fixa o resultado para dados que o motor nunca viu.
  - **Por que existe:** todo teste de integração até aqui roda contra
    `exemplos/`, cujos limites e teto de nota fiscal são os do enunciado. Um motor
    que tivesse esses números embutidos no código passaria em todos eles. A massa
    de `tests/dados/` usa outros centros de custo, outros limites, outro teto
    (R$150,00), outras moedas (`JPY`, `GBP`) e outra competência (`2026-09`), e é
    o que separa "o motor lê a política" de "o motor conhece o enunciado".
  - **Aceite:** `tests/test_dados_sinteticos.py` — 11 testes, todos com o valor
    esperado calculado à mão e escrito por extenso no próprio teste
  - **Commit:** `9e5e02d`

- [x] **T-047** — `parser.py`: `despesas[].valor` lançado como inteiro do JSON
  (`100`, sem casas decimais) deixa de abortar o motor
  - **Atende:** spec.md §4 ("Entrada e saída") — o campo é tipado como "número",
    e a spec não exige casas decimais em nenhum ponto
  - **Por que existe:** detectado na revisão de `21/08/2026`, a partir da massa de
    [[T-046]]. `json.load(..., parse_float=Decimal)` não é consultado para números
    inteiros do JSON, então `"valor": 100` chega como `int` e `_truncar_valor`
    chama `.quantize` nele — `AttributeError` não tratado, código de saída 1,
    nenhum arquivo escrito. Todos os arquivos de `exemplos/` trazem os valores com
    duas casas, e por isso o defeito nunca apareceu. Nada de regra de negócio muda:
    é a borda de leitura que perde o tipo.
  - **Escopo:** acrescentar `parse_int=Decimal` ao `json.load` de `parser.py`, e
    remover o `xfail` de `tests/test_dados_sinteticos.py::test_valor_inteiro_no_json_e_aceito`.
    Verificado antes de abrir a task: com essa única mudança o teste passa e os
    outros 119 continuam passando.
  - **Achado durante a execução:** o escopo acima cobre a borda que **quebra**, e
    não a classe do defeito. São três os carregadores que leem número do JSON —
    `parser.py`, `politica.py` e `cambio.py` — e os três perdiam o tipo do mesmo
    jeito. Só o `parser.py` estourava, porque só ele chama `.quantize` no valor
    cru; os outros dois seguiam adiante entregando `int` onde
    `LimiteCategoria.limite` e `TabelaCambio.taxa` prometem `Decimal`, e o erro
    ficava latente (`f"{60:.2f}"` funciona, `Decimal * int` funciona). Corrigir
    apenas um dos três deixaria o mesmo bug de pé em dois lugares esperando a
    primeira operação que não tolerasse `int`, então o `parse_int=Decimal` entrou
    nos três. Cobertura em
    `tests/test_dados_sinteticos.py::test_politica_e_cambio_com_numeros_inteiros`.
  - **Aceite:** `tests/test_dados_sinteticos.py::test_valor_inteiro_no_json_e_aceito`
    passa sem `xfail`, sobre `tests/dados/despesas-07-valor-inteiro.json`, e
    `::test_politica_e_cambio_com_numeros_inteiros` cobre as outras duas bordas
  - **Commit:** `d2e588d`

- [x] **T-048** — `regras.py`: a identidade de duplicata compara o `valor_original`,
  não o valor já truncado
  - **Atende:** RN-007, AMB-019, RN-010
  - **Por que existe:** detectado na revisão de `21/08/2026`. `_identidade_duplicata`
    compara `despesa.valor`, que já passou pelo truncamento de RN-010 na borda de
    entrada — então duas despesas lançadas com valores **diferentes**, `33.333` e
    `33.334`, viram o mesmo centavo e são tratadas como o mesmo lançamento, e a
    segunda é negada citando a primeira. A spec já dizia o contrário em dois pontos:
    a spec.md §5 (RN-007) lista `valor` entre os campos da entrada que precisam ser
    idênticos, e a spec.md §6 (AMB-019) diz que a comparação é "sobre o valor
    **lançado**". A spec.md §5 (RN-010) também não inclui a duplicata na lista do que
    o truncamento antecede ("antes de qualquer verificação de limite ou nota fiscal").
    Nenhuma mudança de spec: o código é o bug.
  - **Escopo:** `_identidade_duplicata` passa a ler `despesa.valor_original`. Entra um
    lote novo em `tests/dados/`, porque nenhum arquivo de `exemplos/` tem duas
    despesas que difiram só a partir da terceira casa decimal. Nenhum resultado
    existente muda: em todas as duplicatas dos exemplos e da massa sintética o valor
    lançado já era idêntico.
  - **Aceite:** `tests/test_regras.py::test_rn007_valores_que_truncam_no_mesmo_centavo_nao_sao_duplicatas`
    e `tests/test_dados_sinteticos.py::test_duplicata_compara_o_valor_lancado`
  - **Commit:** `2e7af32`

- [ ] **T-049** — `README.md` atualizado para a v4
  - **Atende:** estrutura de entrega exigida pelo desafio (`DESAFIO.md`), spec.md
    §4 ("Entrada e saída")
  - **Por que existe:** o `README.md` foi escrito na T-023, sob a v3, e descreve um
    motor que não existe mais: uma entrada em vez de três, limites fixos de R$60,00
    / R$80,00 / R$250,00 iguais para toda a empresa, teto de nota fiscal como
    constante, `politica.py` descrito como "os limites e as categorias válidas, em
    um lugar só", e nenhuma menção a centro de custo, moeda, câmbio ou vigência. É
    o primeiro arquivo que alguém abre, e hoje ele contradiz a spec.
  - **Escopo:** as três entradas e as flags `--politica`/`--cambio` na seção "Como
    rodar"; a tabela de "O que o motor decide" reescrita sob a v4; os campos novos
    de saída (`moeda`, `taxa_cambio`, `valor_convertido_brl`); `cambio.py` e
    `tests/dados/` na árvore; e as limitações da v4 em "Limitações conhecidas".
    Nenhuma regra de negócio muda — é documentação alinhando-se ao que já existe.
  - **Aceite:** seguir os passos do README do zero produz `resultado.json` sem
    intervenção manual, e nenhuma afirmação da tabela de regras contradiz a
    spec.md §5 ("Regras de negócio")
  - **Commit:** `<hash preenchido depois>`

---

## Cobertura

Preencha ao fechar cada fase. É a sua própria checagem de rastreabilidade — e é
exatamente a matriz que a correção vai montar.

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-013, T-039 | `test_rn001_limite_diario_alimentacao`, `test_rn014_limite_varia_por_centro_de_custo` |
| RN-002 | T-013, T-039 | `test_rn002_limite_diario_transporte` |
| RN-003 | T-014, T-018, T-039 | `test_rn003_limite_diario_hospedagem`, `test_rn003_hospedagem_compartilha_limite_diario_no_mesmo_dia`, `test_hospedagem_multi_diaria_sem_campo_estruturado` |
| RN-004 | T-013, T-014, T-039 | (definição validada pelos testes de RN-001/002/003) |
| RN-005 | T-011, T-012, T-016, T-018, T-038 | `test_rn005_nota_fiscal_obrigatoria_acima_de_100`, `test_rn005_valor_exatamente_no_teto_nao_exige`, `test_ordem_nota_fiscal_antes_de_limite_diario`, `test_amb017_teto_de_nota_fiscal_compara_valor_convertido` |
| RN-006 | T-009 | `test_rn006_fora_do_periodo_negado`, `test_rn006_data_no_extremo_do_periodo_aceita` |
| RN-007 | T-010, T-024, T-025, T-040, T-041 | `test_rn007_duplicata_negada_primeira_mantida`, `test_rn007_duplicata_ignora_capitalizacao_da_categoria`, `test_calcula_totais_do_periodo` |
| RN-008 | T-008, T-037 | `test_rn008_categoria_ausente_da_tabela_do_centro_custo`, `test_amb013_categoria_com_limite_zero_nega_citando_proibicao` |
| RN-009 | T-007, T-025, T-041 | `test_rn009_valor_negativo_ignorado`, `test_calcula_totais_do_periodo` |
| RN-010 | T-005, T-026, T-027, T-035 | `test_rn010_trunca_casas_decimais_excedentes`, `test_saida_ecoa_o_valor_como_veio_na_entrada`, `test_cli_escreve_valores_monetarios_com_duas_casas`, `test_saida_bate_com_o_exemplo_caractere_a_caractere` |
| RN-011 | T-006, T-008, T-019, T-024 | `test_rn011_normaliza_categoria_case_insensitive`, `test_categoria_maiuscula_concorre_ao_limite_diario` |
| RN-012 | T-015 | `test_rn012_sem_adicional_de_viagem`, `test_rn012_hospedagem_no_periodo_nao_amplia_limites` |
| RN-013 | T-012, T-016, T-036 | `test_pipeline_aplica_filtros_na_ordem_definida`, `test_ordem_nota_fiscal_antes_de_limite_diario` |
| RN-014 | T-028, T-029, T-037, T-039 | `test_rn014_centro_custo_com_entrada_usa_a_propria_tabela`, `test_rn014_centro_custo_sem_entrada_cai_no_padrao`, `test_rn014_limite_varia_por_centro_de_custo` |
| RN-015 | T-031, T-034, T-035, T-039, T-042 | `test_rn015_moeda_ausente_assume_brl`, `test_rn015_moeda_normalizada_para_maiusculas`, `test_rn015_converte_pela_taxa_da_data_da_despesa`, `test_saida_publica_taxa_e_valor_convertido` |
| RN-016 | T-031, T-036, T-041 | `test_rn016_data_sem_cotacao_devolve_none`, `test_rn016_moeda_ausente_na_data_devolve_none`, `test_rn016_cambio_indisponivel_nega_despesa`, `test_rn016_despesa_sem_cambio_fora_do_total_bruto` |
| RN-017 | T-030, T-033 | `test_rn017_vigencia_da_competencia_do_lote_cobre`, `test_rn017_vigencia_de_competencia_anterior_cobre`, `test_rn017_vigencia_de_competencia_posterior_nao_cobre`, `test_rn017_lote_de_competencia_anterior_nao_gera_saida`, `test_rn017_lote_coberto_gera_saida_normalmente` |
| AMB-001 | T-013 | `test_rn001_limite_diario_alimentacao` |
| AMB-002 | T-013, T-014 | (mesmos testes de RN-004) |
| AMB-003 | T-016 | `test_valor_exatamente_no_limite_nota_fiscal` |
| AMB-004 | T-012, T-016 | `test_pipeline_aplica_filtros_na_ordem_definida`, `test_ordem_nota_fiscal_antes_de_limite_diario` |
| AMB-005 | T-015, T-039 | `test_rn012_sem_adicional_de_viagem`, `test_rn012_hospedagem_no_periodo_nao_amplia_limites`, `test_amb014_despesa_internacional_nao_amplia_limite` |
| AMB-006 | T-014, T-018 | `test_rn003_limite_diario_hospedagem`, `test_rn003_hospedagem_compartilha_limite_diario_no_mesmo_dia`, `test_hospedagem_multi_diaria_sem_campo_estruturado` |
| AMB-007 | T-010, T-040 | `test_rn007_duplicata_negada_primeira_mantida` |
| AMB-008 | T-007 | `test_rn009_valor_negativo_ignorado` |
| AMB-009 | T-006, T-019 | `test_rn011_normaliza_categoria_case_insensitive`, `test_categoria_maiuscula_concorre_ao_limite_diario` |
| AMB-010 | T-005, T-035 | `test_rn010_trunca_casas_decimais_excedentes` |
| AMB-011 | T-009 | `test_rn006_data_no_extremo_do_periodo_aceita` |
| AMB-012 | T-029 | `test_amb012_tabela_do_centro_custo_nao_e_complementada_pelo_padrao`, `test_rn014_centro_custo_sem_entrada_cai_no_padrao` |
| AMB-013 | T-037 | `test_amb013_categoria_com_limite_zero_nega_citando_proibicao` |
| AMB-014 | T-039 | `test_rn012_sem_adicional_de_viagem`, `test_amb014_despesa_internacional_nao_amplia_limite` |
| AMB-015 | T-031, T-036 | `test_rn016_data_sem_cotacao_devolve_none`, `test_rn016_cambio_indisponivel_nega_despesa` |
| AMB-016 | T-031, T-036 | `test_rn016_moeda_ausente_na_data_devolve_none` |
| AMB-017 | T-038 | `test_amb017_teto_de_nota_fiscal_compara_valor_convertido` |
| AMB-018 | T-035 | `test_amb018_valor_convertido_e_truncado_nao_arredondado` |
| AMB-019 | T-040 | `test_amb019_moedas_diferentes_nao_sao_duplicatas`, `test_amb019_moeda_ausente_e_brl_explicito_sao_duplicatas` |
| AMB-020 | T-030, T-033 | `test_rn017_vigencia_de_competencia_posterior_nao_cobre`, `test_rn017_lote_de_competencia_anterior_nao_gera_saida` |
