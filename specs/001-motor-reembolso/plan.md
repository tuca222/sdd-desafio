# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.13 · **Baseado na spec:** 2.2

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
politica-v4.json → politica.py (parse + Decimal + resolve a tabela do centro
                                de custo, RN-014 → TabelaLimites)
cambio.json      → cambio.py   (parse + Decimal → TabelaCambio, que responde
                                taxa(moeda, data) -> Decimal | None)
                                              ↓
                 RN-017: vigencia da politica × periodo.competencia.
                 Reprovou → cli.py imprime o motivo e encerra sem escrever
                 arquivo nenhum; nada abaixo desta linha roda.
                                              ↓
despesas.json → parser.py (parse + Decimal + truncamento RN-010 +
                          normalização de categoria RN-011 e de moeda RN-015 +
                          conversão para BRL, consultando a TabelaCambio)
             → motor.py (recebe a TabelaLimites já resolvida; orquestra a
                          ordem de aplicação definida na spec.md §8 "Ordem de
                          aplicação das regras" + agregação de limite diário,
                          chamando as funções puras de regras.py; devolve um
                          ResultadoFinal já com os dois totais do período
                          calculados)
             → saida.py (monta o dict de saída; Decimal segue Decimal)
             → resultado.json

cli.py orquestra as etapas (politica + cambio + parser → motor → saida →
escrita) e é onde o Decimal vira texto, no encoder de DT-004.
```

Os totais do período são calculados no `motor.py`, não no `saida.py`: decidir
o que entra em `valor_total_despesas` é regra de negócio (exclui RN-009 e
RN-007, inclui RN-006 e RN-008), e depende de saber qual filtro reprovou cada
despesa — informação que só existe dentro do pipeline. `saida.py` recebe os
totais prontos e só os serializa.

**Fronteiras:** `regras.py` (uma função pura por RN, sem estado, sem I/O) e
`motor.py` (orquestração da ordem definida na spec.md §8, "Ordem de aplicação
das regras", da agregação de limite diário e do cálculo dos totais) são
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
  `fornecedor`, `tem_nota_fiscal`), com `valor: Decimal` já truncado (RN-010),
  `categoria` já normalizada (RN-011) e `moeda: str` já normalizada em
  maiúsculas, com `"BRL"` quando o campo não veio (RN-015) — tudo no momento em
  que a instância é criada em `parser.py`. Mantém em paralelo
  `categoria_original: str`, `valor_original: Decimal` e
  `moeda_original: str | None`, com os dados como vieram na entrada — usados
  **apenas** por `saida.py`, porque a spec.md §4 ("Entrada e saída") exige que
  a saída ecoe os campos originais. `moeda_original` é `None` quando a despesa
  não trouxe o campo, e é isso que faz a saída não inventar um `"moeda": "BRL"`
  que ninguém lançou. A divisão é sempre a mesma: os campos tratados
  (`categoria`, `valor`, `moeda`) alimentam as regras e os totais; os campos
  `_original` só são exibidos. Nenhuma regra lê um campo `_original`.
  Carrega também o resultado da conversão (DT-007): `valor_brl: Decimal | None`
  e `taxa_cambio: Decimal | None`, ambos `None` quando não houve taxa
  disponível — o que é exatamente a condição que `filtro_cambio_indisponivel`
  testa (RN-016). Para despesa em BRL, `valor_brl` é o próprio `valor` e
  `taxa_cambio` é `None`.
- `ResultadoDespesa` — `despesa_reembolsavel: bool`, `tipo_reembolso: str`,
  `valor_reembolsavel: Decimal`, `justificativa: str`. **Não** ganha
  `taxa_cambio` nem `valor_convertido_brl`: os dois são propriedade da despesa,
  não da decisão, e já vivem em `Despesa`. `saida.py` os lê de lá ao montar
  `motor_reembolso_output`, que continua correspondendo 1:1 à spec.md §4
  ("Entrada e saída") mesmo com os dois campos vindo de origens diferentes.
- `TabelaCambio` — `taxas: dict[date, dict[str, Decimal]]`, com um único método
  `taxa(moeda, data) -> Decimal | None`. O `None` é o contrato: quem chama não
  precisa saber se faltou a data ou faltou a moeda naquela data, porque a
  spec.md §5 (RN-016) trata os dois casos igual.
- `ResultadoFinal` — `colaborador`, `periodo`, `valor_total_despesas`,
  `valor_total_reembolsavel`, lista de pares `(Despesa, ResultadoDespesa)` na
  ordem de entrada.
- `LimiteCategoria` — `limite: Decimal`, `periodicidade: str`. A `observacao`
  do arquivo de política **não** entra: a spec.md §4 ("Entrada e saída") diz
  que ela não é lida pelo motor, e um campo que existe no modelo acaba sendo
  lido por alguém.
- `TabelaLimites` — `centro_custo: str` e `limites: dict[str, LimiteCategoria]`.
  É o resultado de RN-014 já resolvido: quem a recebe não sabe (nem precisa
  saber) se ela veio de `centros_custo` ou do `padrao`. Carrega o
  `centro_custo` porque as justificativas de RN-008 e do limite diário precisam
  citá-lo.
- `Politica` — `tabela_por_centro_custo`, `tabela_padrao`,
  `nota_fiscal_obrigatoria_acima_de: Decimal` e `vigencia: date`. Expõe
  `tabela_para(centro_custo) -> TabelaLimites`, que é RN-014 em uma função, e
  `vigencia_cobre(competencia) -> bool`, que é RN-017 em outra.
  `acrescimo_em_viagem_percentual` **não** entra, pelo mesmo motivo que já
  mantinha `observacao` fora de `LimiteCategoria`: campo que existe no modelo
  acaba sendo lido por alguém, e este é mais perigoso que a `observacao`, porque
  parece aplicável. Como a spec.md §4 ("Entrada e saída") o marca como não
  obrigatório, modelá-lo também exigiria um valor padrão para o caso de ele não
  vir — um padrão inventado para um número que nenhuma regra consulta.

## 4. Como a política é representada

**Esta seção registrava, até o plan 1.9, a decisão oposta à atual.** Ela dizia:
*"constantes em código, não config externo (JSON/YAML carregado em runtime).
Nada na spec pede reconfiguração sem redeploy; mudar um valor é uma linha
versionada com o resto do projeto, testável do mesmo jeito que qualquer outra
regra."* O item A do comunicado da v4 revogou isso em uma frase — *"o motor
precisa ler a política de fora, não de dentro do código"* — e a decisão fica
registrada aqui, e não apagada, porque saber que ela existiu e por que caiu é
mais útil do que fingir que sempre foi assim (ver `DECISIONS.md` [[D-010]]).

O que estava errado na justificativa original não era o raciocínio, era a
premissa: "nada na spec pede reconfiguração sem redeploy" era verdade sobre a
spec 1.10 e falso sobre o problema. A tabela de limites é mantida pelo
financeiro, fora do repositório, e muda sem aviso — nenhuma dessas três coisas
aparecia na v3 da política.

**Como é agora.** `src/politica.py` deixa de ter constantes e passa a ser o
carregador: lê o JSON da política com `parse_float=Decimal` (mesmo cuidado do
`parser.py`, ver `plan.md` §1, "Stack") e devolve um objeto `Politica`
imutável. Quem consome limites nunca vê o JSON nem o caminho do arquivo — vê
uma `TabelaLimites` já resolvida por RN-014.

O conjunto de categorias válidas some como constante: ele passa a ser as chaves
da `TabelaLimites` do colaborador, o que é literalmente RN-008 depois da v4.
`LIMITE_NOTA_FISCAL` também some — o teto vem de
`nota_fiscal_obrigatoria_acima_de`.

A política não vira estado global nem *singleton*: ela é carregada uma vez no
`cli.py` e passada adiante como argumento, do mesmo jeito que o `Periodo` já
era. Um módulo com a política em variável de módulo economizaria alguns
parâmetros e custaria a testabilidade de `regras.py`, que hoje é o que permite
testar toda regra de negócio sem tocar em disco (ver `plan.md` §2,
"Arquitetura").

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

### DT-005 — Normalização de categoria (RN-011) na borda, como o truncamento

**Contexto:** RN-011 normaliza `categoria` antes de qualquer regra. A versão
anterior deixava cada regra chamar `normalizar_categoria` por conta própria.
**Decisão:** o `parser.py` normaliza no momento em que constrói `Despesa`,
guardando a grafia crua em `categoria_original`. `regras.py` e `motor.py` leem
`despesa.categoria` direto, sem normalizar. Mesmo princípio de DT-002.
**Alternativa descartada:** manter a normalização espalhada nas regras. Não é
hipotética: enquanto era assim, `filtro_duplicata` comparava a grafia crua e
duas despesas idênticas exceto pela capitalização não eram detectadas como
duplicata (ver `DECISIONS.md` D-005).
**Consequência:** não existe mais caminho pelo qual uma regra veja a categoria
não normalizada, então o bug não pode voltar por esquecimento. O custo é o
campo extra em `Despesa`, que só a saída lê.

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
monetários como números, e a spec.md §4 ("Entrada e saída") exige que a
**escala decimal** sobreviva até o arquivo: valor produzido pelo motor sai com
exatamente 2 casas (`60.00`), valor ecoado da entrada sai com a escala lançada
(`72.50`, `33.333`).
**Decisão:** `saida.py` entrega o `Decimal` intacto no dict — não converte
para `float` em ponto nenhum. `cli.py` serializa com um `json.JSONEncoder`
próprio que emite o texto do `Decimal` como número literal do JSON.
**Como o encoder funciona:** `json` não oferece gancho para números fora de
`int`/`float` — `default()` só é consultado para tipos que ele não sabe
serializar, e o que `default()` devolve volta pelo caminho normal (uma `str`
devolvida sai entre aspas, virando string no JSON). O encoder contorna isso em
dois passos: `default()` embrulha o texto do `Decimal` num marcador
(`@decimal@60.00@decimal@`) e `iterencode()` remove, dos fragmentos já
serializados, as aspas em volta do marcador. O resultado reparseia como número
JSON. O marcador é escolhido entre caracteres que o `json` não escapa, para que
o texto emitido seja o mesmo que o padrão procura, e é **sorteado a cada
execução** (`uuid4`): a substituição varre todos os fragmentos, inclusive os de
string, então um marcador fixo permitiria que uma `descricao` vinda da entrada
imitasse um valor e virasse número na saída — corrupção silenciosa, porque o
arquivo resultante continua sendo JSON válido.
**Alternativa descartada:** manter `float(Decimal)` na borda, como esta DT
decidia até a spec 1.9. A justificativa era que "a representação textual do
`float` resultante é exata para esses valores" — verdadeira quanto ao *valor* e
falsa quanto à *escala*. `float` não carrega escala: `Decimal("72.50")` sabe que
tem duas casas, `float` só sabe que vale 72,5, e `json.dump` serializa pelo
`repr`, produzindo `72.5`. Foi exatamente o defeito que a T-027 corrigiu.
**Alternativa descartada:** emitir os valores monetários como string
(`"60.00"`). Resolveria a escala, mas a spec.md §4 ("Entrada e saída") tipa
esses campos como `número` — trocar o tipo do contrato de saída para contornar
uma limitação da biblioteca de serialização é o rabo abanando o cachorro.
**Consequência:** `Decimal` atravessa o pipeline inteiro, do `parse_float` do
`parser.py` até o `json.dump` do `cli.py`, sem nunca virar `float`. `cli.py`
passa a ser o único lugar do código que sabe como um `Decimal` vira texto.

### DT-006 — Política carregada na borda e passada como argumento

**Contexto:** a v4 exige ler a política de um arquivo externo (spec.md §4,
"Entrada e saída"), e RN-014 exige resolver a tabela do centro de custo antes
de qualquer regra ser avaliada.
**Decisão:** `cli.py` carrega o arquivo, `politica.py` o transforma em
`Politica` e resolve a `TabelaLimites` do colaborador, e o `motor.py` recebe a
tabela pronta como argumento. `regras.py` recebe o limite ou a tabela por
parâmetro e continua sem I/O, sem estado e sem `import` de configuração.
**Alternativa descartada:** `politica.py` ler o arquivo no `import` e expor a
política como variável de módulo, mantendo as assinaturas atuais de
`regras.py`. Teria custo zero de refatoração e três problemas: o `import`
passaria a fazer I/O (um teste que só quer `formatar_reais` abriria arquivo),
não haveria como testar dois centros de custo no mesmo processo, e a política
viraria estado global mutável na prática — exatamente o que a fronteira do
`plan.md` §2 ("Arquitetura") existe para evitar.
**Consequência:** as funções de `regras.py` que dependem de limite ganham um
parâmetro. É a mudança que mais arquivos toca nesta migração, e é o custo real
de ter escolhido constantes em código na versão anterior deste plano — está
contabilizado em `DECISIONS.md` [[D-010]].

### DT-007 — Conversão para BRL na borda; a negação é que é regra

**Contexto:** RN-015 converte a despesa para BRL e RN-016 nega a despesa que
não tem taxa. A spec.md §8 ("Ordem de aplicação das regras") põe a negação como
passo 5 e diz explicitamente que a conversão não é um passo da lista.
**Decisão:** a conversão acontece em `parser.py`, no mesmo lugar e pelo mesmo
motivo que o truncamento (DT-002) e a normalização (DT-005): é tratamento de
dado de entrada. `Despesa` nasce com `valor_brl` e `taxa_cambio` preenchidos,
ou com os dois em `None` quando não havia taxa. `filtro_cambio_indisponivel`,
em `regras.py`, é uma função de uma linha — `despesa.valor_brl is None` — e
continua pura, sem conhecer arquivo de câmbio nenhum.
**Alternativa descartada:** converter dentro do pipeline, entre os filtros 5 e
6 do `motor.py`. É a leitura literal da spec.md §8, e foi descartada porque
obrigaria `motor.py` ou `regras.py` a carregar a `TabelaCambio` para consultar
no meio da passada — quebrando a fronteira do `plan.md` §2 ("Arquitetura") pelo
mesmo motivo que DT-002 rejeitou truncar dentro de cada regra. A ordem da spec
continua respeitada: o que importa para o resultado é que a **negação** por
câmbio venha depois da duplicata e antes da nota fiscal, e isso é decidido pela
posição do filtro na lista de DT-001, não por onde a multiplicação acontece.
**Consequência:** `parser.py` passa a receber a `TabelaCambio` como argumento e
vira o único ponto do código que sabe converter moeda. `regras.py` continua sem
I/O e sem saber que câmbio existe. O custo é que `Despesa` carrega dois campos
que só fazem sentido para despesa internacional — aceito porque a alternativa
era espalhar a consulta de taxa por dois módulos.

### DT-008 — RN-017 é uma guarda no `cli.py`, não um filtro do pipeline

**Contexto:** RN-017 valida a `vigencia` da política contra
`periodo.competencia` antes de qualquer cálculo, e a reprovação impede a
geração do arquivo de saída (spec.md §5, RN-017).
**Decisão:** `politica.py` expõe a pergunta como função pura —
`vigencia_cobre(competencia) -> bool` — e `cli.py` é quem age sobre a resposta:
imprime a mensagem em `stderr`, não chama `motor.calcular`, não chama
`saida.montar_saida`, não abre o arquivo de saída para escrita, e encerra com
código diferente de zero. `motor.py` não sabe que RN-017 existe.
**Alternativa descartada:** tratar RN-017 como o passo 0 da lista de filtros de
DT-001, negando toda despesa com uma justificativa de vigência. Foi descartada
porque o desfecho de RN-017 não é uma decisão sobre despesa — é a ausência de
resultado. Um `resultado.json` com todas as despesas em R$0,00 tem a forma de um
relatório válido e pode ser arquivado como se fosse um; a spec pede
explicitamente que nada seja escrito.
**Alternativa descartada:** `politica.py` levantar exceção ao carregar o
arquivo. Ele não tem o `periodo` na mão nesse momento, e passá-lo ao carregador
só para essa verificação acoplaria o carregamento da política ao lote — o mesmo
arquivo deixaria de poder ser carregado uma vez e usado para vários lotes.
**Consequência:** o único ponto do código que decide "não vai haver saída" é o
`cli.py`, que já é o único que escreve arquivo. A regra em si continua testável
sem I/O, como todas as outras.

## 6. Estratégia de testes

- **Nível:** majoritariamente unitário — uma função de regra em `regras.py` é
  testada isoladamente, com testes de integração ponta a ponta rodando cada
  arquivo de exemplo completo e comparando o resultado contra os critérios de
  aceite da spec.md §9 ("Critérios de aceite"):
  `exemplos/despesas-exemplo.json` (`CC-ENG-PLATAFORMA`, com
  `valor_total_despesas = 1806.94` e `valor_total_reembolsavel = 351.43`, além
  da comparação caractere a caractere contra
  `exemplos/resultado-exemplo.json`) e
  `exemplos/envelope/despesas-envelope-cc-desconhecido.json` (`CC-SUPORTE-N2`,
  exercitando o fallback para o `padrao` de RN-014) e
  `exemplos/envelope/despesas-envelope.json` (`CC-COMERCIAL`, exercitando as
  quatro categorias do centro de custo e os quatro desfechos de câmbio:
  conversão bem-sucedida, moeda ausente do arquivo, data sem cotação e despesa
  sem o campo `moeda`).
- **Política e câmbio nos testes:** os testes unitários de `regras.py` montam a
  `TabelaLimites` na mão e recebem `Despesa` já com `valor_brl` preenchido, sem
  ler arquivo nenhum — é o que mantém as fronteiras de DT-006 e DT-007
  verificáveis. Só os testes de `politica.py`, de `cambio.py`, de `parser.py` e
  os de integração leem `exemplos/envelope/politica-v4.json` e
  `exemplos/envelope/cambio.json`.
- **RN-017 em teste:** a função pura de `politica.py` é testada com pares
  (competência de vigência, competência do lote) cobrindo anterior, igual e
  posterior. O comportamento de "não escreve arquivo" é testado em
  `tests/test_cli.py`, e o que se afirma é a **ausência** do arquivo de saída
  no disco mais o código de saída — nunca só a mensagem impressa, que é texto e
  muda sem que a regra mude.
- **Aritmética de conversão:** todo teste de RN-015 confere o valor convertido
  contra um número escrito por extenso no próprio teste (`EUR 22,00 × 5,93 =
  R$130,46`), nunca recalculando a multiplicação dentro do teste — um teste que
  repete a conta do código passa mesmo quando a conta está errada.
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
- **Validação de `ResultadoDespesa` em teste de regra/filtro:** aplica-se a
  todo teste cujo alvo retorna um `ResultadoDespesa` (as funções de
  `regras.py` que decidem reembolso — `filtro_valor_negativo`,
  `filtro_categoria_invalida` e as demais que vierem) — **não** se aplica a
  teste de função auxiliar sem esse retorno, como
  `test_rn011_normaliza_categoria_case_insensitive` (que testa
  `normalizar_categoria`, uma `str -> str`). Nesses testes, valida-se o
  objeto inteiro, campo a campo — `despesa_reembolsavel`,
  `tipo_reembolso`, `valor_reembolsavel` e `justificativa` — nunca só um
  subconjunto. Para `justificativa` especificamente, o teste nunca compara
  a string inteira nem faz busca case-insensitive (`.lower()`) por uma
  palavra de conteúdo do texto (ex.: `"política"`, `"negativo"`) — frágil,
  quebra a cada reescrita de frase que não muda a decisão, e não valida o
  desfecho real. Em vez disso, verifica, com a capitalização exata usada em
  `regras.py`, a presença da palavra que corresponde ao `tipo_reembolso` já
  validado no mesmo teste: `"negado" in resultado.justificativa` para
  `"nenhum"`, `"total" in resultado.justificativa` para `"total"`,
  `"parcial" in resultado.justificativa` para `"parcial"`. Padrão de
  referência: `test_rn008_categoria_fora_da_politica` e
  `test_rn009_valor_negativo_ignorado` em `tests/test_regras.py`.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Mudança de requisito do dia 2 (envelope) exigir novo filtro, reordenar a ordem definida na spec.md §8 ("Ordem de aplicação das regras"), ou mudar um limite | **Aconteceu.** Ver o que segue. | — |

**O que o envelope cobrou, e o que cada aposta deste plano rendeu.** Registrado
aqui enquanto está fresco, porque é o insumo do `docs/RELATORIO.md`:

| Aposta | Como se saiu |
|---|---|
| DT-001 — ordem como lista explícita de filtros em `motor.py` | **Absorveu.** Reordenar e acrescentar passo na spec.md §8 ("Ordem de aplicação das regras") é editar uma sequência num lugar só; `parser.py`, `saida.py` e `cli.py` não sabem que a ordem mudou. |
| DT-002 / DT-005 — tratamento de dado na borda de entrada | **Absorveu.** Todo campo novo que precisa de normalização entra pelo mesmo caminho já existente em `parser.py`, e nenhuma regra precisa saber disso. |
| `Decimal` do parse à escrita (`plan.md` §1, "Stack") | **Absorveu.** Limite vindo de arquivo entra como `Decimal` pelo mesmo `parse_float`, sem nenhum ponto novo de conversão. |
| DT-001 — lista de filtros como ponto único de ordem | **Absorveu de novo, no item B.** `filtro_cambio_indisponivel` entrou na posição 5 editando uma sequência; nenhum outro filtro soube. |
| `plan.md` §4 (versão 1.9) — política como constantes em código | **Resistiu.** Foi a única decisão deste plano que o envelope revogou por inteiro, e a que mais arquivos custou: `politica.py` foi reescrito, `regras.py` e `motor.py` ganharam parâmetro, `cli.py` ganhou entrada nova. Ver `DECISIONS.md` [[D-010]]. |
| `parser.py` como borda única de tratamento de dado | **Absorveu, e cobrou juros.** `moeda` e a conversão entraram pelo caminho já aberto por DT-002/DT-005, sem tocar em `regras.py`. Em troca, `parser.py` passou a depender de `cambio.py`, e é hoje o módulo com mais responsabilidades do projeto. |
| `ResultadoDespesa` como espelho 1:1 de `motor_reembolso_output` | **Resistiu.** Os dois campos novos de saída são propriedade da despesa, não da decisão, e o espelho 1:1 deixou de valer: `saida.py` agora monta o objeto a partir de duas origens. Ver `plan.md` §3 ("Modelo de dados"). |
| Constante de limite embutida nos exemplos e nos testes | **Resistiu.** `exemplos/resultado-exemplo.json` teve de ser regravado inteiro porque o colaborador do exemplo é de um centro de custo cujos limites mudaram — custo que nenhuma decisão de arquitetura teria evitado, já que é dado, não estrutura. |
