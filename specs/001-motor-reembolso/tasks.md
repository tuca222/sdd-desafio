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
  - **Atende:** spec.md §4
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
  - **Commit:** `<hash preenchido depois>`

- [ ] **T-007** — Filtro: valor negativo / estorno
  - **Atende:** RN-009
  - **Aceite:** `tests/test_regras.py::test_rn009_valor_negativo_ignorado` (`d-009`)
  - **Commit:**

- [ ] **T-008** — Filtro: categoria fora da política (usa a normalização de T-006)
  - **Atende:** RN-008, RN-011
  - **Aceite:** `tests/test_regras.py::test_rn008_categoria_fora_da_politica` (`d-005`, categoria `coworking`)
  - **Commit:**

- [ ] **T-009** — Filtro: fora do período de competência (limites inclusivos nos dois extremos)
  - **Atende:** RN-006
  - **Aceite:** `tests/test_regras.py::test_rn006_fora_do_periodo_negado` (`d-008`) + `test_rn006_data_no_extremo_do_periodo_aceita`
  - **Commit:**

- [ ] **T-010** — Filtro: duplicata (todos os campos idênticos exceto `id`)
  - **Atende:** RN-007
  - **Aceite:** `tests/test_regras.py::test_rn007_duplicata_negada_primeira_mantida` (`d-006`/`d-007`)
  - **Commit:**

- [ ] **T-011** — Filtro: nota fiscal obrigatória (estritamente maior que R$100,00)
  - **Atende:** RN-005
  - **Aceite:** `tests/test_regras.py::test_rn005_nota_fiscal_obrigatoria_acima_de_100` + `test_rn005_valor_exatamente_100_nao_exige` (`d-003`)
  - **Commit:**

- [ ] **T-012** — Pipeline de filtros em `motor.py`, aplicados na ordem da spec.md §8, uma única justificativa por despesa
  - **Atende:** RN-005, RN-006, RN-007, RN-008, RN-009, RN-013
  - **Aceite:** `tests/test_motor.py::test_pipeline_aplica_filtros_na_ordem_definida` (`d-004`: negado por nota fiscal ausente, não por limite diário já esgotado — AMB-004)
  - **Commit:**

- [ ] **T-013** — Agregação de limite diário: categorias `alimentacao` e `transporte_urbano` (soma por categoria+dia, ordem de entrada, corta excedente)
  - **Atende:** RN-001, RN-002, RN-004
  - **Aceite:** `tests/test_regras.py::test_rn001_limite_diario_alimentacao` (`d-001`/`d-002`) + `test_rn002_limite_diario_transporte` (`d-003`)
  - **Commit:**

- [ ] **T-014** — Limite de hospedagem por lançamento (sem dividir pelo número de diárias)
  - **Atende:** RN-003, RN-004
  - **Aceite:** `tests/test_regras.py::test_rn003_limite_hospedagem_por_lancamento` (`d-010`)
  - **Commit:**

- [ ] **T-015** — Confirma que o adicional de viagem não é aplicado em nenhuma circunstância
  - **Atende:** RN-012
  - **Aceite:** `tests/test_regras.py::test_rn012_sem_adicional_de_viagem`
  - **Commit:**

## Fase 3 — Casos de borda

- [ ] **T-016** — Limite exato de nota fiscal (`d-003`, R$100,00) e ordem nota-fiscal-antes-de-limite-diário (`d-004`)
  - **Atende:** RN-005, RN-013, AMB-003, AMB-004
  - **Aceite:** `tests/test_casos_borda.py::test_valor_exatamente_no_limite_nota_fiscal` + `test_ordem_nota_fiscal_antes_de_limite_diario`
  - **Commit:**

- [ ] **T-017** — Despesa em fim de semana, sem regra especial
  - **Atende:** (confirma ausência de regra — spec.md §7)
  - **Aceite:** `tests/test_casos_borda.py::test_despesa_fim_de_semana_sem_regra_especial` (`d-012`)
  - **Commit:**

- [ ] **T-018** — Hospedagem multi-diária sem campo estruturado de noites (`d-010` com nota fiscal, `d-013` sem nota fiscal)
  - **Atende:** RN-003, RN-005, AMB-006
  - **Aceite:** `tests/test_casos_borda.py::test_hospedagem_multi_diaria_sem_campo_estruturado`
  - **Commit:**

- [ ] **T-019** — Categoria em maiúsculas concorrendo normalmente ao limite diário
  - **Atende:** RN-011, AMB-009
  - **Aceite:** `tests/test_casos_borda.py::test_categoria_maiuscula_concorre_ao_limite_diario` (`d-014`)
  - **Commit:**

## Fase 4 — Saída e CLI

- [ ] **T-020** — `saida.py`: monta o dict de saída completo (`valor_total_despesas`, `valor_total_reembolsavel`, `detalhamento_despesas[].motor_reembolso_output`), conversão `Decimal → float` só na borda
  - **Atende:** spec.md §4
  - **Aceite:** `tests/test_saida.py::test_monta_saida_conforme_schema`
  - **Commit:**

- [ ] **T-021** — `cli.py`: subcomando `calcular --input --output`, orquestra parser → motor → saida → escrita em arquivo
  - **Atende:** interface fixa do desafio (`DESAFIO.md`), spec.md §4
  - **Aceite:** `tests/test_cli.py::test_cli_calcular_gera_arquivo_de_saida`
  - **Commit:**

- [ ] **T-022** — Teste de integração ponta a ponta contra todos os critérios de aceite da spec.md §9
  - **Atende:** spec.md §9 (todos os itens, incluindo `valor_total_despesas = 1806.94` e `valor_total_reembolsavel = 585.43`)
  - **Aceite:** `tests/test_integracao.py::test_exemplo_completo_bate_com_criterios_de_aceite`
  - **Commit:**

- [ ] **T-023** — `README.md` com instruções de rodar (`python -m src.cli calcular --input despesas.json --output resultado.json`) e testar (`pytest -v`)
  - **Atende:** estrutura de entrega exigida pelo desafio
  - **Aceite:** seguir os passos do README do zero produz `resultado.json` sem intervenção manual
  - **Commit:**

---

## Fase 5 — Envelope (criar no Dia 2)

<Novas tasks a partir da mudança de requisito. Numeração continua de onde parou —
não reinicie e não renumere as antigas: a numeração é o eixo da rastreabilidade.>

---

## Cobertura

Preencha ao fechar cada fase. É a sua própria checagem de rastreabilidade — e é
exatamente a matriz que a correção vai montar.

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-013 | `test_rn001_limite_diario_alimentacao` |
| RN-002 | T-013 | `test_rn002_limite_diario_transporte` |
| RN-003 | T-014, T-018 | `test_rn003_limite_hospedagem_por_lancamento`, `test_hospedagem_multi_diaria_sem_campo_estruturado` |
| RN-004 | T-013, T-014 | (definição validada pelos testes de RN-001/002/003) |
| RN-005 | T-011, T-012, T-016, T-018 | `test_rn005_nota_fiscal_obrigatoria_acima_de_100`, `test_rn005_valor_exatamente_100_nao_exige`, `test_ordem_nota_fiscal_antes_de_limite_diario` |
| RN-006 | T-009 | `test_rn006_fora_do_periodo_negado`, `test_rn006_data_no_extremo_do_periodo_aceita` |
| RN-007 | T-010 | `test_rn007_duplicata_negada_primeira_mantida` |
| RN-008 | T-008 | `test_rn008_categoria_fora_da_politica` |
| RN-009 | T-007 | `test_rn009_valor_negativo_ignorado` |
| RN-010 | T-005 | `test_rn010_trunca_casas_decimais_excedentes` |
| RN-011 | T-006, T-008, T-019 | `test_rn011_normaliza_categoria_case_insensitive`, `test_categoria_maiuscula_concorre_ao_limite_diario` |
| RN-012 | T-015 | `test_rn012_sem_adicional_de_viagem` |
| RN-013 | T-012, T-016 | `test_pipeline_aplica_filtros_na_ordem_definida`, `test_ordem_nota_fiscal_antes_de_limite_diario` |
| AMB-001 | T-013 | `test_rn001_limite_diario_alimentacao` |
| AMB-002 | T-013, T-014 | (mesmos testes de RN-004) |
| AMB-003 | T-016 | `test_valor_exatamente_no_limite_nota_fiscal` |
| AMB-004 | T-012, T-016 | `test_pipeline_aplica_filtros_na_ordem_definida`, `test_ordem_nota_fiscal_antes_de_limite_diario` |
| AMB-005 | T-015 | `test_rn012_sem_adicional_de_viagem` |
| AMB-006 | T-014, T-018 | `test_rn003_limite_hospedagem_por_lancamento`, `test_hospedagem_multi_diaria_sem_campo_estruturado` |
| AMB-007 | T-010 | `test_rn007_duplicata_negada_primeira_mantida` |
| AMB-008 | T-007 | `test_rn009_valor_negativo_ignorado` |
| AMB-009 | T-006, T-019 | `test_rn011_normaliza_categoria_case_insensitive`, `test_categoria_maiuscula_concorre_ao_limite_diario` |
| AMB-010 | T-005 | `test_rn010_trunca_casas_decimais_excedentes` |
| AMB-011 | T-009 | `test_rn006_data_no_extremo_do_periodo_aceita` |
