# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Baseado na spec:** 1.1

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.12.3, stdlib apenas (`argparse`, `json`, `decimal`, `dataclasses`) | Fixado em `CLAUDE.md`. Nenhuma dependência externa é necessária para o escopo do desafio (uma CLI de um único subcomando fixo, sem HTTP, sem banco). | Typer/Click para a CLI — dependência externa desnecessária para `calcular --input --output`, que não precisa de mais do que `argparse` oferece. |
| Testes | pytest | Biblioteca já conhecida pelo desenvolvedor. | Outras bibliotecas de testes, sem necessidade. |
| Parsing/validação | `json.load(f, parse_float=decimal.Decimal)` | Evita que qualquer valor monetário passe por `float`, mesmo que só na leitura — o valor chega em `Decimal` desde o primeiro instante em que existe no programa. | Pydantic/`jsonschema` para validar o schema de entrada — a spec.md §3 ("Fora de escopo") assume entrada bem formada; dado problemático (valor negativo, casas decimais em excesso) é tratado por regra de negócio, não rejeitado como erro de schema. |
| Aritmética monetária | `decimal.Decimal` do parse à escrita; truncamento com `Decimal.quantize(Decimal("0.01"), rounding=ROUND_DOWN)` | Decisão técnica; reforçado pela RN-010 (truncar, não arredondar). Ponto flutuante em dinheiro acumula erro de arredondamento. | `round()`/`float` em qualquer ponto do pipeline de cálculo. |

## 2. Arquitetura

```
despesas.json → parser.py (parse + Decimal + truncamento RN-010)
             → motor.py (orquestra a ordem de aplicação definida na
                          spec.md §8 "Ordem de aplicação das regras" +
                          agregação de limite diário, chamando
                          as funções puras de regras.py)
             → saida.py (monta o JSON de saída, Decimal → float)
             → resultado.json

cli.py orquestra as quatro etapas (parser → motor → saida → escrita).
```

**Fronteiras:** `regras.py` (uma função pura por RN, sem estado, sem I/O) e
`motor.py` (orquestração da ordem definida na spec.md §8, "Ordem de aplicação
das regras", e da agregação de limite diário) são
o núcleo de regra de negócio puro — recebem dados já parseados e devolvem
decisão + justificativa, nunca tocam em filesystem. `parser.py`, `saida.py` e
`cli.py` são I/O. Essa linha é o que permite testar toda regra de negócio sem
tocar em arquivo em disco, e é o que absorve mudança de requisito sem
reescrever a CLI.

## 3. Modelo de dados

`dataclasses` com type hints (`frozen=True`, já que nenhuma delas muda depois
de criada):

- `Colaborador` — `id`, `nome`, `centro_custo`.
- `Periodo` — `competencia`, `inicio`, `fim` (datas).
- `Despesa` — campos da entrada (`id`, `data`, `categoria`, `descricao`,
  `fornecedor`, `tem_nota_fiscal`) e `valor: Decimal` já truncado (RN-010) no
  momento em que a instância é criada em `parser.py`.
- `ResultadoDespesa` — `despesa_reembolsavel: bool`, `tipo_reembolso: str`,
  `valor_reembolsavel: Decimal`, `justificativa: str`. Corresponde 1:1 ao
  `motor_reembolso_output` da spec.
- `ResultadoFinal` — `colaborador`, `periodo`, `valor_total_despesas`,
  `valor_total_reembolsavel`, lista de pares `(Despesa, ResultadoDespesa)` na
  ordem de entrada.

## 4. Como a política é representada

`src/politica.py`: constantes `Decimal` nomeadas — `LIMITE_ALIMENTACAO`,
`LIMITE_TRANSPORTE_URBANO`, `LIMITE_HOSPEDAGEM`, `LIMITE_NOTA_FISCAL` — e o
conjunto `CATEGORIAS_VALIDAS = {"alimentacao", "transporte_urbano",
"hospedagem"}`.

Decisão: constantes em código, não config externo (JSON/YAML carregado em
runtime). Nada na spec pede reconfiguração sem redeploy; mudar um valor é uma
linha versionada com o resto do projeto, testável do mesmo jeito que qualquer
outra regra.

## 5. Decisões técnicas

### DT-001 — Ordem de aplicação como pipeline sequencial de funções puras

**Contexto:** a spec.md §8 ("Ordem de aplicação das regras") define uma ordem estrita de 6 verificações; cada
despesa para na primeira que a reprovar.
**Decisão:** `motor.py` mantém uma lista ordenada de funções-filtro
(`filtro_valor_negativo`, `filtro_categoria_invalida`, `filtro_fora_periodo`,
`filtro_duplicata`, `filtro_nota_fiscal`), definidas em `regras.py` e
aplicadas em sequência a cada despesa; as sobreviventes vão para a etapa de
agregação de limite diário (RN-001 a RN-004).
**Alternativa descartada:** objetos/Strategy por regra (interface comum +
registro). Cerimônia desnecessária para 6 filtros fixos definidos numa spec
fechada — não há requisito de plugar regras em runtime.
**Consequência:** adicionar ou reordenar um filtro é editar uma lista em um
lugar só; testar um filtro isoladamente não exige montar o pipeline inteiro.

### DT-002 — Truncamento (RN-010) acontece uma única vez, na borda de entrada

**Contexto:** RN-010 trunca valores com mais de 2 casas decimais antes de
qualquer verificação.
**Decisão:** o truncamento acontece dentro de `parser.py`, no momento em que
`Despesa` é construída a partir do JSON bruto. Nenhum código depois desse
ponto (regras, motor, saída) volta a tocar em precisão decimal do valor de
entrada.
**Alternativa descartada:** truncar dentro de cada regra que compara valor a
limite — repete a lógica em vários pontos e arrisca esquecer um deles quando
uma nova regra for adicionada (ex.: no envelope do dia 2).
**Consequência:** toda regra em `regras.py` pode assumir que `despesa.valor`
já está correto; simplifica cada função de regra individual.

### DT-003 — Duplicata é detectada antes da agregação de limite diário

Decorre diretamente da ordem definida em RN-013 / spec.md §8 ("Ordem de
aplicação das regras"), não é uma escolha técnica
livre: `filtro_duplicata` compara cada despesa sobrevivente das verificações
1–3 às despesas anteriores já aceitas (mesmos `data`, `categoria`,
`descricao`, `fornecedor`, `valor`, `tem_nota_fiscal`), na ordem em que
aparecem na entrada, mantendo um acumulador das despesas já aceitas ao longo
da passada do pipeline.

### DT-004 — Serialização de `Decimal` na saída

**Contexto:** o JSON de saída (`resultado.json`) precisa representar valores
monetários como números.
**Decisão:** `saida.py` converte `Decimal` para `float` só no momento de
montar o dict final, imediatamente antes de `json.dump` — nunca antes disso
no pipeline.
**Alternativa descartada:** `json.JSONEncoder` customizado que emite o texto
do `Decimal` diretamente como número (via override de `iterencode`) — resolve
o mesmo problema com mais complexidade. Desnecessário aqui porque todo valor
de saída já foi truncado/somado em no máximo 2 casas decimais antes desse
ponto: não há mais aritmética depois da conversão, logo não há acúmulo de
erro, e a representação textual do `float` resultante é exata para esses
valores.
**Consequência:** `saida.py` é o único lugar do código que sabe que `Decimal`
vira `float`; todo o resto do pipeline (parser, regras, motor) trabalha só
com `Decimal`.

## 6. Estratégia de testes

- **Nível:** majoritariamente unitário — uma função de regra em `regras.py` é
  testada isoladamente, com um teste de integração ponta a ponta rodando
  `exemplos/despesas-exemplo.json` completo e comparando o resultado contra
  `exemplos/resultado-exemplo.json` e os critérios de aceite da spec.md §9
  ("Critérios de aceite") (incluindo `valor_total_despesas = 1806.94` e
  `valor_total_reembolsavel = 585.43`).
- **Cada `RN-NNN` tem teste?** Sim — `tests/test_regras.py` tem uma função de
  teste por RN, nomeada `test_rn001_...`, `test_rn002_...` etc., cada uma
  usando o(s) caso(s) de aceite descrito(s) na própria spec para aquela regra.
- **Casos de borda da spec.md §7 ("Casos de borda"):** cobertos em `tests/test_casos_borda.py`,
  um teste por linha da tabela (ex.: `test_valor_exatamente_no_limite_nota_fiscal`,
  `test_ordem_nota_fiscal_antes_de_limite_diario` para AMB-004,
  `test_despesa_fim_de_semana_sem_regra_especial`).
- **Estrutura:** espelha `src/` — `tests/test_parser.py`, `tests/test_regras.py`,
  `tests/test_motor.py`, `tests/test_saida.py`, `tests/test_cli.py`, mais
  `tests/test_casos_borda.py` e `tests/test_integracao.py` para os cenários
  que cruzam módulos.
- **Nomenclatura:** todo teste que cobre uma `RN-NNN` ou `AMB-NNN` carrega o
  ID no nome da função — é isso que fecha a rastreabilidade spec → teste que
  a `tasks.md` e a correção vão seguir.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Valor monetário passa por `float` em algum ponto do pipeline e acumula erro de arredondamento | Baixa | `Decimal` do parse (DT-002) até a borda de saída (DT-004); o teste de integração compara contra os totais exatos da spec e pega qualquer desvio de centavo. |
| Mudança de requisito do dia 2 (envelope) exigir novo filtro, reordenar a ordem definida na spec.md §8 ("Ordem de aplicação das regras"), ou mudar um limite | Alta — é o próprio desafio | DT-001 isola a ordem numa lista explícita em `motor.py`; este plan.md §4 ("Como a política é representada") isola os valores em `politica.py`. Ambos são pontos de alteração únicos, sem precisar tocar em `parser.py`, `saida.py` ou `cli.py`. |
| Ordem entre nota fiscal ausente e limite diário esgotado (AMB-004) implementada errada | Média | Teste de integração usa exatamente `d-003`/`d-004` do exemplo — é o caso de aceite que a própria spec define para essa ordem (RN-013). |
