# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

---

## D-012 — `moeda_base` deixa de ser parâmetro: o BRL é fixado pelo texto da política · `19/08/2026`

**Gatilho:** a spec.md §10 ("O que fica em aberto") da versão 2.0 registrava, como
decisão pendente, que o motor não verifica se a `moeda_base` da política e a do
câmbio são a mesma — e sugeria que isso poderia virar uma RN-018. O usuário
questionou: a política nunca fala em `moeda_base`, ela diz "Os limites da política
são **sempre** em BRL" e "quando ausente, assume-se `BRL`"
(`exemplos/rh_politica_v4.md`), então não há o que validar.

**O que mudou na spec:**

- **Cabeçalho** — versão 2.0 → 2.1, com o **Status** registrando a mudança.
- **spec.md §4 ("Entrada e saída")** — as duas linhas de `moeda_base`, na tabela da
  política e na do câmbio, deixaram de dizer "moeda em que os limites estão
  expressos" / "moeda de destino de toda conversão" e passaram a dizer que o campo
  declara o BRL e **não é lido pelo motor**. As duas passaram de obrigatórias a não
  obrigatórias, porque o motor não precisa delas para funcionar. A linha de
  `padrao.<categoria>.limite` passou de "na `moeda_base`" para "em BRL", e a de
  `taxas.<data>.<MOEDA>` de "unidades de `moeda_base`" para "unidades de BRL".
  Entrou um parágrafo curto — "O BRL não é configurável" — com as duas frases do RH
  e a razão.
- **spec.md §10 ("O que fica em aberto")** — o item da consistência entre as duas
  `moeda_base` saiu. Ele descrevia um risco que não existe.

**Por quê:** as duas frases do RH são categóricas. "Sempre em BRL" não é "na moeda
declarada no arquivo", e "assume-se `BRL`" não é "assume-se a `moeda_base`". O
contrato de saída desta própria spec já sustentava isso e eu não tinha reparado: o
campo produzido por RN-015 se chama `valor_convertido_brl`, com a moeda no nome — se
`moeda_base` fosse parâmetro, esse nome estaria errado para qualquer política que não
fosse em real, e a spec teria uma contradição interna entre a §4 e o nome do campo.

**O que isso invalidou:** nada de código — a Fase 5 não começou. Invalidou parte da
própria spec 2.0: quatro células da §4 ("Entrada e saída") descreviam `moeda_base`
como se ele mandasse no cálculo, e um item da §10 ("O que fica em aberto") apresentava
como pendência uma decisão que não existe.

**Tasks afetadas:** T-028 e T-031 (`tasks.md`), no detalhe — nem `Politica` nem
`TabelaCambio` guardam `moeda_base`, pelo mesmo princípio que já mantinha `observacao`
fora de `LimiteCategoria` no `plan.md` §3 ("Modelo de dados"): campo que existe no
modelo acaba sendo lido por alguém. Nenhuma task muda de escopo ou de critério de
aceite.

**Custo:** `specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`.

---

## D-011 — Despesas internacionais: conversão pela taxa da data, e negação quando não há taxa · `19/08/2026`

**Gatilho:** item B do comunicado do RH da v4 (`exemplos/rh_politica_v4.md`):
*"A entrada agora pode trazer um campo `moeda` (ISO 4217). Quando ausente,
assume-se `BRL`. A conversão usa a taxa da data da despesa, não a taxa de hoje.
(...) Os limites da política são sempre em BRL."* O usuário trouxe três decisões
prontas (moeda estrangeira não amplia limite; data sem cotação é negada; o
arquivo de câmbio é a fonte da verdade sobre moedas) e três ambiguidades foram
levantadas na revisão da spec: em que valor o teto de nota fiscal é comparado,
como truncar o valor convertido, e se `moeda` entra na identidade de duplicata.

**O que mudou na spec:**

- **Cabeçalho** — versão 1.11 → 2.0, e **Status** passou a "especificada para a
  Política de Reembolso v4", com os itens A e B cobertos e o item C fora de
  escopo.
- **spec.md §3 ("Fora de escopo")** — quatro itens novos: não busca cotação em
  fonte externa e não infere taxa de outra data; não valida `moeda` contra a
  norma ISO 4217; não converte a saída de volta para a moeda lançada; e os
  arquivos de política e câmbio são entregues, não descobertos.
- **spec.md §4 ("Entrada e saída")** — o motor passou de duas para **três**
  entradas, com tabela de campos completa do arquivo de câmbio. O campo
  `despesas[].moeda` entrou na tabela de despesas como opcional.
  `motor_reembolso_output` ganhou `taxa_cambio` e `valor_convertido_brl`. O
  bloco "o que campos originais significa" passou de dois para três casos, e
  ganhou a regra de que despesa sem o campo `moeda` sai **sem** o campo, e não
  com um `BRL` inventado pelo motor.
- **spec.md §5 ("Regras de negócio")** — **RN-015** (conversão) e **RN-016**
  (câmbio indisponível) são novas. RN-004, RN-005 e RN-010 passaram a operar
  sobre o valor em BRL; RN-007 passou a incluir `moeda` na identidade de
  duplicata.
- **spec.md §6 ("Ambiguidades identificadas e decisões")** — **AMB-014** a
  **AMB-019** são novas.
- **spec.md §7 ("Casos de borda")** — sete linhas novas.
- **spec.md §8 ("Ordem de aplicação das regras")** — a ordem passou de 6 para 7
  passos, com "câmbio indisponível" entrando como passo 5.
- **spec.md §9 ("Critérios de aceite")** — bloco novo para
  `exemplos/envelope/despesas-envelope.json` e complemento do bloco de
  `despesas-envelope-cc-desconhecido.json`, com os totais dos dois arquivos.
- **spec.md §10 ("O que fica em aberto")** — cinco itens novos, sendo AMB-015 o
  mais provável de ser reaberto.

**Por quê:** as três decisões que não vinham prontas.

*AMB-017 — o teto de nota fiscal compara o valor convertido.* O teto está
escrito em reais; comparar contra ele um número em euro faz a exigência de nota
depender da moeda e não do gasto. A alternativa (comparar o valor lançado) abre
brecha concreta e verificável no próprio conjunto de despesas do envelope:
`e-005` são USD 40,00 sem nota fiscal, e 40 é menor que 100 — passaria pela
exigência valendo R$220,00.

*AMB-018 — o valor convertido é truncado, `ROUND_DOWN`.* Mesma decisão de
AMB-010, pelo mesmo motivo, e por um motivo adicional: `valor_convertido_brl` é
publicado na saída, e um valor publicado com três casas decimais é o defeito de
escala que a [[D-008]] já resolveu para os demais valores produzidos.

*AMB-019 — `moeda` entra na identidade de duplicata.* Sem ela, EUR 22,00 e
BRL 22,00 seriam duplicatas uma da outra e o total do período perderia um gasto
real. Comparar o valor **convertido** em vez do lançado foi descartado porque
faria a detecção de duplicata depender da taxa do dia — a mesma entrada
produziria resultados diferentes se o arquivo de câmbio fosse corrigido.

A decisão que o usuário trouxe pronta e que mais custou registro é AMB-015:
negar a despesa internacional lançada em data sem cotação. A alternativa —
usar a cotação do último dia útil anterior — é a prática de mercado, e o próprio
arquivo de câmbio observa que só publica em dia útil. Ela foi descartada pelo
critério que já governa AMB-005 e AMB-008 aqui: aplicar a taxa de outra data
exige escolher sozinho qual data, quantos dias voltar e o que fazer no início do
arquivo. O custo é conhecido e está em spec.md §10 ("O que fica em aberto"):
`e-004`, um almoço de sábado em Lisboa, é uma despesa legítima negada por um
motivo alheio a ela.

**O que isso invalidou:**

- **`plan.md` §3 ("Modelo de dados")** — `ResultadoDespesa` deixou de ser
  espelho 1:1 de `motor_reembolso_output`: os dois campos novos de saída são
  propriedade da despesa, não da decisão, e `saida.py` passou a montar o objeto
  a partir de duas origens.
- **`src/parser.py`** — `Despesa` ganha `moeda`, `moeda_original`, `valor_brl`
  e `taxa_cambio`, e o parser passa a depender de um módulo de câmbio que ainda
  não existe.
- **`src/regras.py`** — `filtro_nota_fiscal` compara `despesa.valor`, que deixou
  de ser o valor comparável; `_identidade_duplicata` não inclui `moeda`;
  `aplicar_limite_diario` agrega `despesa.valor`, e não o valor em BRL.
- **`src/motor.py`** — `valor_total_despesas` soma `despesa.valor` e não exclui
  despesa sem câmbio.
- **`src/saida.py`** — `motor_reembolso_output` não tem os dois campos novos, e
  o dict de saída ecoa `categoria` e `valor` mas não `moeda`.
- **`src/cli.py`** — não tem por onde receber o arquivo de câmbio.
- **`exemplos/resultado-exemplo.json`** — além do que a [[D-010]] já invalidou,
  agora toda despesa precisa sair com `taxa_cambio` e `valor_convertido_brl` em
  `null`.
- **Testes** — todos os que constroem `Despesa` diretamente, porque a dataclass
  ganhou quatro campos: `tests/test_regras.py`, `tests/test_motor.py`,
  `tests/test_casos_borda.py`, `tests/test_parser.py`, `tests/test_saida.py`.

**Tasks afetadas:** nenhuma task fechada é reaberta. O trabalho entra na Fase 5
de `tasks.md`, de T-028 em diante, junto com o que a [[D-010]] gerou.

**Custo:** `exemplos/envelope/politica-v4.json`,
`exemplos/envelope/cambio.json`,
`exemplos/envelope/despesas-envelope.json`,
`exemplos/envelope/despesas-envelope-cc-desconhecido.json`,
`exemplos/rh_politica_v3.md`,
`exemplos/rh_politica_v4.md`,
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`.

As duas entradas compartilham este conjunto de arquivos porque os itens A e B do
comunicado foram especificados no mesmo movimento, contra a mesma spec 1.10 — não
há como atribuir um arquivo a uma e não à outra. O que está listado aqui é o custo
de **spec**; o custo de **código** ainda não foi pago e está dimensionado na Fase 5
de `tasks.md` (T-028 a T-045), que é a estimativa honesta do que estas duas decisões
vão custar em `src/` e `tests/`.

**Nota de processo:** o item B foi especificado em commit separado do item A
([[D-010]]) de propósito, embora os dois tenham vindo do mesmo envelope e do
mesmo dia. São duas mudanças com conjuntos de invalidação diferentes, e juntá-las
num commit só produziria uma entrada de `DECISIONS.md` com dois gatilhos e um
campo **Custo** que não distingue o que cada uma custou — que é exatamente a
informação que este arquivo existe para preservar.

---

## D-010 — A política sai do código e passa a variar por centro de custo · `19/08/2026`

**Gatilho:** o envelope do Dia 2 trouxe o comunicado do RH da Política de
Reembolso v4 (`exemplos/rh_politica_v4.md`), item A: *"Os limites não são mais
constantes. Cada centro de custo tem a sua tabela, mantida pelo financeiro num
arquivo à parte, e ela muda sem aviso. O motor precisa ler a política de fora,
não de dentro do código."* O usuário leu o comunicado, anotou as ambiguidades
que enxergou e pediu revisão antes de qualquer código. Duas das ambiguidades
desta entrada (AMB-012 e AMB-013) não estavam nas anotações e foram levantadas
na revisão; a decisão de cada uma foi do usuário.

**O que mudou na spec:**

- **Cabeçalho** — versão 1.10 → 1.11, e **Status** passou de "implementada"
  para "em migração para a Política de Reembolso v4", registrando que o item A
  está especificado e o item B (despesas internacionais) ainda não.
- **spec.md §3 ("Fora de escopo")** — dois itens novos: não descobre sozinho
  qual arquivo de política aplicar, e não altera nem persiste o arquivo de
  política. O item do adicional de viagem passou a citar
  `acrescimo_em_viagem_percentual` em vez de "50%".
- **spec.md §4 ("Entrada e saída")** — o motor deixou de ter uma entrada e
  passou a ter duas: despesas e **política**. Tabela de campos completa do
  arquivo de política, incluindo os três campos que existem e o motor **não**
  usa (`versao`, `observacao`, `acrescimo_em_viagem_percentual`) — dizer
  explicitamente que um campo é ignorado vale mais do que omiti-lo, porque
  omitir deixa a próxima pessoa achando que esqueceram. `vigencia` entrou como
  campo **obrigatório**, porque RN-017 depende dele. O exemplo pequeno da seção
  foi recalculado — o colaborador é de `CC-ENG-PLATAFORMA`, cujo limite de
  alimentação é R$75,00, então `d-001` passou de R$60,00 (parcial) para R$72,50
  (total) e `d-002` de R$0,00 para R$2,50 (parcial) — e passou a mostrar a
  política como entrada, e não só as despesas.
- **spec.md §5 ("Regras de negócio")** — RN-001, RN-002 e RN-003 deixaram de
  trazer o limite escrito e passaram a apontar para a tabela do centro de custo;
  RN-005 passou a ler o teto de `nota_fiscal_obrigatoria_acima_de`; RN-008 foi
  reescrita de "categorias fora da política" para "categorias não reembolsáveis
  para o centro de custo", com duas cláusulas e duas justificativas distintas;
  RN-012 passou a citar o campo da política que lê e ignora. **RN-014** é nova
  e define como a tabela aplicável é resolvida; **RN-017** é nova e valida a
  `vigencia` da política contra `periodo.competencia` antes de qualquer cálculo
  — é a única regra desta spec que não decide sobre uma despesa, e a única cuja
  reprovação impede a geração do arquivo de saída.
- **spec.md §6 ("Ambiguidades identificadas e decisões")** — **AMB-012**
  (granularidade de "aplica-se a política padrão"), **AMB-013** (categoria com
  limite `0.00`) e **AMB-020** (o que "retroativa à competência atual" exige do
  motor) são novas. AMB-005 e AMB-006 tiveram os valores fixos trocados por
  referência à tabela, sem mudar decisão.
- **spec.md §7 ("Casos de borda")** — dez linhas novas e duas reescritas; a
  legenda passou a distinguir `d-NNN`, `e-NNN` e `f-NNN` por arquivo de origem.
- **spec.md §8 ("Ordem de aplicação das regras")** — o passo 2 passou de
  "categoria fora da política" para "categoria não reembolsável para o centro de
  custo", cobrindo as duas cláusulas de RN-008. A ordem em si não mudou, mas a
  seção ganhou a precondição de RN-017, que roda antes do passo 1 e vale para o
  lote inteiro.
- **spec.md §9 ("Critérios de aceite")** — reescrita. Todos os critérios foram
  recalculados sob a v4 e **desmarcados**, porque o código ainda implementa a
  v3. Bloco novo para `exemplos/envelope/despesas-envelope-cc-desconhecido.json`.
- **spec.md §10 ("O que fica em aberto")** — três itens novos: `periodicidade`
  ecoada e não interpretada, centro de custo com tabela incompleta, e a
  ausência de `fim_vigencia` — RN-017 aceita indefinidamente uma política já
  revogada, porque o arquivo não tem como dizer que foi substituída.

**Por quê:** as duas decisões que não vinham prontas do comunicado foram
tomadas assim.

*AMB-012 — a tabela de um centro de custo é fechada.* A frase do RH nomeia
"centros de custo" que "não têm entrada", não categorias que faltam. A
alternativa descartada era o merge por categoria, em que o `padrao` completaria
as lacunas de um centro de custo que existe. Ela foi descartada pelo efeito
colateral: `CC-ADM` não lista `hospedagem`, e sob o merge herdaria R$250,00 do
padrão — reembolsando exatamente o gasto que a tabela foi escrita para não
cobrir, e sem nada no arquivo denunciando a herança. O preço da leitura fechada
é conhecido e ficou registrado em spec.md §10 ("O que fica em aberto"): centro
de custo cadastrado com categoria faltando nega despesa legítima.

*AMB-013 — `limite: 0.00` é proibição, não orçamento zerado.* O valor
reembolsado é o mesmo nas duas leituras; a justificativa não é. "Limite diário
de R$0,00 já atingido na despesa X" manda quem confere procurar uma despesa que
não existe, e o financeiro escreveu `"observacao": "nao reembolsavel"` ao lado
do zero. Mais grave, a leitura como orçamento zerado produziria justificativa
enganosa em combinação com RN-005: `d-013` (hospedagem sem nota fiscal em
`CC-ENG-PLATAFORMA`) seria negada citando a nota, sugerindo a quem lê que
anexar o comprovante resolveria — quando a categoria está vedada e não resolve.

*AMB-020 — a validação de vigência é uma só, no lote.* "Retroativa **à**
competência atual" fixa a fronteira da retroatividade, não abre uma reta, e o
dado corrobora: o comunicado é do meio de julho e `vigencia` vale `2026-07-01`,
ou seja, o RH já retroagiu até o início da competência e parou ali. Duas leituras
foram descartadas. A primeira, de que a política nova julgaria despesas de meses
anteriores, contraria a preposição e o campo. A segunda, de um check por despesa
negando `data < vigencia`, se contradiz: ele só tem efeito quando a vigência cai
no meio do período, e é exatamente nesse cenário que a frase do RH manda cobrir a
competência inteira; fora dele, é redundante com RN-006. O operador de RN-017 é
"igual ou anterior" porque um mês futuro pode não ter atualização de política — e
aí a corrente precisa continuar valendo — enquanto um mês anterior precisa ser
processado com a política que valia nele. O arquivo reforça: existe `vigencia` e
não existe `fim_vigencia`, e uma data de início sem data de fim é aberta por
construção.

**O que isso invalidou:**

- **`plan.md` §4 ("Como a política é representada"), na versão 1.9** — decidia
  explicitamente *"constantes em código, não config externo (JSON/YAML carregado
  em runtime). Nada na spec pede reconfiguração sem redeploy."* Revogada. A
  seção foi reescrita mantendo o texto antigo citado, não apagado.
- **`src/politica.py` inteiro** — `LIMITE_ALIMENTACAO`,
  `LIMITE_TRANSPORTE_URBANO`, `LIMITE_HOSPEDAGEM`, `LIMITE_NOTA_FISCAL`,
  `CATEGORIAS_VALIDAS` e `LIMITES_DIARIOS_POR_CATEGORIA` deixam de existir como
  constantes.
- **`src/regras.py`** — `filtro_categoria_invalida` e `filtro_nota_fiscal`
  dependiam das constantes; `aplicar_limite_diario` monta justificativa sem
  citar centro de custo.
- **`src/motor.py`** — lê `LIMITES_DIARIOS_POR_CATEGORIA` diretamente.
- **`src/cli.py`** — não tem por onde receber o arquivo de política.
- **`exemplos/resultado-exemplo.json`** — regravado por inteiro: quatro
  despesas mudam de valor ou de justificativa e `valor_total_reembolsavel` cai
  de R$585,43 para R$351,43. `valor_total_despesas` sobrevive em R$1.806,94,
  porque o total bruto não depende de limite.
- **Testes** — `tests/test_politica.py`, `tests/test_regras.py`,
  `tests/test_motor.py`, `tests/test_casos_borda.py` e
  `tests/test_integracao.py` afirmam limites que deixaram de valer.

**Tasks afetadas:** T-005 a T-022 permanecem fechadas — elas foram entregues
contra a spec vigente na época e o histórico não é reescrito. O trabalho novo
entra como Fase 5, de T-028 em diante, e a tabela **Cobertura** de `tasks.md`
passa a apontar RN-001, RN-002, RN-003, RN-005 e RN-008 para as tasks novas
além das antigas.

**Custo:** `exemplos/envelope/politica-v4.json`,
`exemplos/envelope/cambio.json`,
`exemplos/envelope/despesas-envelope.json`,
`exemplos/envelope/despesas-envelope-cc-desconhecido.json`,
`exemplos/rh_politica_v3.md`,
`exemplos/rh_politica_v4.md`,
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`.

As duas entradas compartilham este conjunto de arquivos porque os itens A e B do
comunicado foram especificados no mesmo movimento, contra a mesma spec 1.10 — não
há como atribuir um arquivo a uma e não à outra. O que está listado aqui é o custo
de **spec**; o custo de **código** ainda não foi pago e está dimensionado na Fase 5
de `tasks.md` (T-028 a T-045), que é a estimativa honesta do que estas duas decisões
vão custar em `src/` e `tests/`.

**Fica em aberto:** o item B do comunicado (despesas internacionais) e o item C
(fila de aprovação manual, opcional). O item B entra na próxima versão desta
spec; o item C foi deixado fora por decisão do usuário.

**Nota de processo:** RN-017 e AMB-020 não estavam na primeira versão desta
entrada. Na primeira versão, a spec.md §3 ("Fora de escopo") declarava que o
motor "não valida o campo `vigencia`", e a spec.md §10 ("O que fica em aberto")
registrava isso como limitação conhecida. **Ninguém decidiu isso.** O agente
encontrou um campo sem uso óbvio no arquivo de política e o declarou ignorado,
porque declarar era mais barato do que perguntar — o mesmo movimento que este
arquivo existe para tornar impossível. O usuário detectou na revisão, antes de
qualquer commit, e determinou que a validação é obrigatória.

Vale registrar o padrão, e não só o caso: a spec descreve **três** campos como
"lidos e ignorados" (`versao`, `observacao`, `acrescimo_em_viagem_percentual`) e
declara, na spec.md §10 ("O que fica em aberto"), que a consistência entre a
`moeda_base` da política e a do câmbio não é verificada. Cada um desses é a mesma
forma de decisão que o `vigencia` foi. Três deles têm justificativa que se
sustenta sozinha (`versao` e `observacao` não afetam cálculo;
`acrescimo_em_viagem_percentual` cai em AMB-005, que é decisão antiga e
registrada). O da `moeda_base` não tem, e está em spec.md §10 ("O que fica em
aberto") aguardando decisão, não como omissão silenciosa.

---

## D-009 — Critério de escala decimal da §9 marcado como atendido · `18/08/2026`

**Gatilho:** a [[D-008]] criou um critério novo na spec.md §9 ("Critérios de
aceite") — o texto do JSON de saída idêntico ao de
`exemplos/resultado-exemplo.json` — deixando-o em `- [ ]` porque, naquele
commit, o teste que o verifica ainda não existia. Com a T-027 fechada, o teste
existe e passa, e o checkbox virou a única parte da spec desatualizada.

**O que mudou na spec:** o critério da spec.md §9 ("Critérios de aceite")
passou a `- [x]`, e o **Status** do cabeçalho voltou de "em correção" para
"implementada", agora dizendo também que a escala decimal é verificada sobre o
texto do JSON gerado. Nenhuma regra, nenhum limite e nenhum campo mudaram.

**Por quê:** vale aqui a mesma razão registrada em [[D-007]] — a marcação nesta
spec não afirma "alguém conferiu uma vez", afirma "existe teste que verifica".
`tests/test_integracao.py::test_saida_bate_com_o_exemplo_caractere_a_caractere`
roda a CLI de verdade e compara os dois arquivos como texto, então se a escala
regredir o teste quebra antes de o checkbox virar mentira. A alternativa
descartada foi marcar o critério já na [[D-008]], junto da mudança da §4: o
efeito colateral é um commit em que a spec afirma "verificado por teste" antes
de o teste existir, ou seja, exatamente a mentira de cabeçalho que a [[D-007]]
foi criada para desfazer.

**O que isso invalidou:** nada. Nenhum código, teste ou exemplo muda de sentido.

**Tasks afetadas:** nenhuma. A T-027 já estava fechada quando esta entrada foi
escrita.

**Custo:** `specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`.

---

## D-008 — A escala decimal da saída vira contrato da spec, não detalhe de serialização · `18/08/2026`

**Gatilho:** o usuário rodou o comando do `README.md` contra
`exemplos/despesas-exemplo.json` e leu o `resultado.json` gerado. Onde
`exemplos/resultado-exemplo.json` traz `"valor": 72.50` e
`"valor_reembolsavel": 60.00`, a saída real trazia `72.5` e `60.0` — uma casa
decimal só, que para valor monetário não é formato válido. Quatro valores
pareciam corretos (`1806.94`, `585.43`, `33.333`, `33.33`), o que fez o defeito
parecer localizado em algumas despesas; na verdade eram os únicos cujo último
dígito não é zero, ou seja, os únicos que não tinham nada a perder.

**O que mudou na spec:**

- spec.md §4 ("Entrada e saída"), regra geral dos campos produzidos: "sempre
  tem no **máximo** 2 casas decimais" passou a "sai com **exatamente 2 casas
  decimais**, inclusive quando a última é zero: `60.00`, nunca `60.0`; `0.00`,
  nunca `0`". O parágrafo ganhou também a razão de a escala ser contrato de
  spec e não detalhe delegado à biblioteca de serialização, e o registro de que
  a conformidade só é verificável sobre o **texto** do arquivo.
- spec.md §4 ("Entrada e saída"), campos ecoados: `"exato"` passou a incluir
  explicitamente a quantidade de casas decimais lançada — `72.50` entra e sai
  `72.50`, não `72.5`.
- spec.md §9 ("Critérios de aceite"): novo critério exigindo que o texto do
  JSON de saída seja idêntico ao de `exemplos/resultado-exemplo.json`.

**Por quê:** a redação antiga era formalmente satisfeita pelo defeito — `60.0`
tem "no máximo 2 casas decimais". Sem trocar "máximo" por "exatamente" não
havia regra que sustentasse a correção, e a T-027 seria código sem spec. A
razão de fundo é a mesma da §4 inteira, auditoria: `R$60,00` é como o
comprovante está escrito e como o financeiro lê dinheiro; `R$60,0` obriga quem
confere a parar e reinterpretar o número.
A alternativa descartada foi tratar a escala como formatação — detalhe de
apresentação fora da spec, resolvido no código. O efeito colateral seria que
nenhum critério de aceite cobriria a escala e a próxima regressão passaria de
novo pela suíte inteira sem quebrar nada, que é exatamente o que aconteceu
aqui. Também foi descartado emitir os valores como string (`"60.00"`): resolve
a escala, mas a spec.md §4 ("Entrada e saída") tipa esses campos como `número`,
e mudar o tipo do contrato de saída para contornar limitação de biblioteca é o
rabo abanando o cachorro.

**O que isso invalidou:**

- `plan.md` DT-004 ("Serialização de `Decimal` na saída") decidia o oposto:
  converter `Decimal → float` em `saida.py`, descartando o encoder customizado
  sob o argumento de que "a representação textual do `float` resultante é exata
  para esses valores". Verdadeiro quanto ao *valor*, falso quanto à *escala* —
  `float` não carrega escala. DT-004 foi reescrita.
- `tests/test_saida.py::test_saida_converte_decimal_para_numero_serializavel`
  afirmava o contrato antigo (`isinstance(..., float)`) e deixou de valer;
  virou `test_saida_entrega_decimal_sem_passar_por_float`.
- `tests/test_integracao.py::test_saida_e_identica_ao_resultado_esperado`
  continua válido mas não era suficiente: compara os dois lados depois de
  `json.loads`, e como estruturas de dados `60.0` e `60.00` são o mesmo valor.
  Foi por isso que o defeito atravessou a T-022 sem quebrar nada.
- `README.md` descrevia `saida.py` como "único ponto que converte Decimal →
  float" e dizia que `float` aparece na escrita do JSON. Nenhuma das duas coisas
  é mais verdade.

**Tasks afetadas:** T-027, criada para esta mudança. T-020 e T-022 não são
reabertas — o que elas entregaram continua valendo, o defeito estava na
serialização, não no que elas cobriam.

**Custo:** resolvido dentro da própria T-027. Arquivos alterados:
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`,
`README.md`,
`exemplos/resultado-exemplo.json`,
`src/cli.py`, `src/saida.py`, `src/motor.py`, `src/regras.py`,
`tests/test_cli.py`, `tests/test_integracao.py`, `tests/test_saida.py`.

**Nota de processo:** `exemplos/resultado-exemplo.json` não tinha newline
final; o usuário acrescentou uma durante esta mudança. Sem ela o novo critério
da spec.md §9 ("Critérios de aceite") teria de ser redigido como "idêntico
exceto pela newline final", que é o tipo de ressalva que envelhece mal. A
mudança não altera nenhum valor do arquivo.

`src/motor.py` e `src/regras.py` estavam fora do `ruff format` desde antes
desta mudança (o `ruff check` sempre passou; era só formatação). Foram
reformatados dentro da T-027, a pedido do usuário, em vez de num commit `style:`
separado: commit que altera código sem task referenciada não existe neste
projeto (ver `CLAUDE.md`, "Regras de trabalho").

---

## D-007 — §9 marcada como atendida e status da spec atualizado · `18/08/2026`

**Gatilho:** com a T-023 fechada, todas as 26 tasks estavam concluídas, mas
`spec.md` continuava com os 14 critérios de aceite da §9 em `- [ ]` e com o
**Status** dizendo "em implementação (Fase 2 — regras de negócio)" — uma fase
que tinha terminado várias tasks antes. O cabeçalho estava mentindo sobre o
estado do projeto.

**O que mudou na spec:** os 14 itens da §9 ("Critérios de aceite") passaram a
`- [x]`; o **Status** do cabeçalho passou a "implementada — todos os critérios
de aceite da §9 verificados por teste automatizado". A §9 ganhou também uma
nota curta explicando **por que** os itens estão marcados: cada um tem um
teste em `tests/test_integracao.py`, que roda a CLI de verdade (arquivo de
entrada → arquivo de saída) e percorre a lista item a item.

**Por quê:** a hesitação registrada aqui foi se valia a pena editar a spec só
para marcar checkbox — o argumento contra é que checkbox fica desatualizado e
teste não. A nota resolve isso mudando o que a marcação significa: ela não
afirma "alguém conferiu uma vez", afirma "existe teste que verifica". Se um
critério deixar de valer, a suíte quebra antes de o checkbox virar mentira.
O bump de versão se justifica sozinho pelo **Status**, que estava
factualmente errado.

**O que isso invalidou:** nada de comportamento. Antes de marcar, os 14
critérios foram verificados um a um contra a saída real da CLI, num script à
parte da suíte — para não marcar na confiança de que o teste que eu mesmo
escrevi cobre o que diz cobrir.

**Tasks afetadas:** nenhuma. Todas (T-001 a T-026) já estavam fechadas.

**Custo:** `specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`.

---

## D-006 — A saída ecoa o `valor` lançado, não o truncado · `18/08/2026`

**Gatilho:** ao fechar a T-025, o agente rodou pela primeira vez o pipeline
inteiro (`parser → motor → saida`) contra `exemplos/despesas-exemplo.json` e
comparou o dicionário gerado com `exemplos/resultado-exemplo.json` campo a
campo. Apareceu uma divergência que nenhum teste unitário tinha como pegar:
`d-011` entra com `33.333`, o arquivo de exemplo espera `"valor": 33.333` no
detalhamento, e o motor estava emitindo `33.33`.

**O que mudou na spec:** §4 ("Entrada e saída") ganhou a seção **"O que
'campos originais' significa"**, que substitui a nota que existia só sobre
`categoria`. A seção agora enuncia a regra geral — **o valor tratado serve
para calcular, o valor lançado serve para exibir** — e lista os dois casos em
que entrada e uso interno divergem (`categoria` por RN-011, `valor` por
RN-010). Declara também que tudo que o motor *produz* (`valor_reembolsavel` e
os dois totais) deriva do valor truncado e por isso nunca passa de 2 casas
decimais; só campos ecoados da entrada podem ter mais.

**Por quê:** que o truncado é o correto para calcular estava provado pelo
próprio número da spec — somar os truncados dá exatamente `1806.94`, somar os
originais daria `1806.943`. O que faltava era dizer o que exibir. Exibir o
truncado quebraria a auditoria: a linha mostraria R$33,33 para uma nota de
R$33,333, e quem confere veria uma divergência criada pelo sistema. A spec
tinha essa informação implícita no arquivo de exemplo, mas em lugar nenhum
por escrito — um desenvolvedor lendo só a spec emitiria o truncado, como o
agente emitiu.

**O que isso invalidou:** `Despesa` ganhou `valor_original: Decimal` e
`saida.py` passou a ecoar esse campo em `detalhamento_despesas[].valor`.
Nenhum cálculo mudou: `valor` continua truncado e continua sendo o único que
as regras leem. As construções de `Despesa` nos testes passaram a informar
`valor_original`.

**Por que os testes não pegaram antes:** todo teste até aqui exercitava ou uma
regra isolada (`regras.py`), ou o motor (`motor.py`), ou a serialização com um
`ResultadoFinal` montado à mão (`saida.py`). Nenhum atravessava
`parser → motor → saida` com o arquivo real, que é o único caminho em que
`valor_original` e `valor` divergem. É a mesma lição de [[D-004]], por outro
ângulo: o erro só aparece na junção, e a junção não tinha teste. A T-022
existe justamente para fechar isso.

**Tasks afetadas:** T-026, criada para esta mudança. T-022 (integração ponta a
ponta) depende dela — sem isso, a comparação da saída inteira falharia em
`d-011`.

**Custo:** resolvido dentro da própria T-026. Arquivos alterados:
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`,
`src/modelos.py`, `src/parser.py`, `src/saida.py`,
`tests/test_modelos.py`, `tests/test_regras.py`, `tests/test_motor.py`,
`tests/test_casos_borda.py`, `tests/test_saida.py`.

---

## D-005 — Normalização de categoria migra para a borda de entrada · `18/08/2026`

**Gatilho:** ao escrever o teste da T-019, o agente precisou dar descrições
diferentes às duas despesas do cenário para evitar que elas colidissem como
duplicatas, e ao explicar por quê percebeu — e reportou — uma inconsistência:
`filtro_duplicata` comparava `categoria` **crua**, enquanto RN-008 e o limite
diário comparavam a versão **normalizada**. Consequência: duas despesas
idênticas em tudo, diferindo só por `alimentacao` vs `ALIMENTACAO`, não eram
detectadas como duplicata. A decisão do usuário foi normalizar na entrada,
para que nenhuma verificação do motor precise se preocupar com isso.

**O que mudou na spec:**
- RN-011 deixou de ser "a comparação ignora maiúsculas/minúsculas" e passou a
  dizer **onde** a normalização acontece: uma única vez, na leitura da
  entrada, antes de qualquer regra. Lista explicitamente as regras que passam
  a enxergar só a forma normalizada — RN-008, RN-001/002/003 e RN-007.
- RN-007 passou a declarar que a comparação de `categoria` usa a forma
  normalizada, e que duas despesas diferindo só pela capitalização **são**
  duplicatas. É mudança de comportamento, não só de redação.
- AMB-009 teve a decisão estendida (normalizar na borda, não regra a regra) e
  a justificativa passou a citar o bug real como evidência.
- §4 ("Entrada e saída") ganhou, nos dois lados: na entrada, que `categoria` é
  normalizada na leitura; na saída, que `categoria` sai com a **grafia exata
  que entrou**.
- §7 ("Casos de borda") ganhou a linha da duplicata que difere só por
  capitalização.

**Por quê:** a forma antiga distribuía a mesma decisão por N pontos de
chamada, e bastava um deles esquecer para a regra divergir de si mesma — que
é exatamente o que aconteceu. Normalizar na borda transforma "toda regra
precisa lembrar de normalizar" em "é impossível uma regra ver o valor não
normalizado". A classe inteira de bug desaparece, em vez de ser corrigida
caso a caso.

**A parte não óbvia — por que a grafia original sobrevive:** §4 exige que
`detalhamento_despesas[]` devolva "os mesmos campos originais", e
`exemplos/resultado-exemplo.json` mostra `d-014` saindo com `ALIMENTACAO`.
Normalizar destrutivamente na entrada quebraria isso. Por isso `Despesa`
passou a ter **dois** campos: `categoria` (normalizada, é o que toda regra
usa) e `categoria_original` (crua, existe só para a saída ecoar). A
alternativa — `saida.py` reler o JSON de entrada para recuperar a grafia —
foi descartada: faria a camada de saída depender do formato bruto do arquivo,
furando a fronteira que o `plan.md` §2 ("Arquitetura") estabelece.

**O que isso invalidou:** `normalizar_categoria` deixou de ser chamada em
`filtro_categoria_invalida`, `aplicar_limite_diario` e `motor.py` — continua
existindo, mas só o `parser.py` a chama. As construções de `Despesa` nos
testes passaram a informar `categoria_original`.

**Tasks afetadas:** T-024, criada para esta mudança (a numeração continua de
T-023; ela não pertence a nenhuma fase do planejamento original). T-020 tinha
de ser executada depois desta, porque a saída depende de qual dos dois campos
ecoar — registrado na própria task.

**Custo:** resolvido antes de a Fase 4 começar. Arquivos alterados:
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`,
`src/modelos.py`, `src/parser.py`, `src/regras.py`, `src/motor.py`,
`tests/test_modelos.py`, `tests/test_parser.py`, `tests/test_regras.py`,
`tests/test_motor.py`, `tests/test_casos_borda.py`.

---

## D-004 — Hospedagem: limite de R$250,00 é diário e agregado, não por lançamento · `18/08/2026`

**Gatilho:** o agente implementou a T-014 tratando cada lançamento de
`hospedagem` como tendo seu próprio limite de R$250,00 — e escreveu um teste,
`test_rn003_hospedagem_nao_acumula_limite_entre_lancamentos_do_mesmo_dia`,
afirmando que duas hospedagens no mesmo dia recebem R$250,00 **cada**. O
usuário reprovou na revisão: a intenção sempre foi que os R$250,00 valem para
**o dia**, agregando todas as hospedagens daquela data, igual a RN-001 e
RN-002.

**A spec estava errada, não só o código.** RN-003 dizia "cada despesa de
categoria `hospedagem` é tratada como uma diária única e limitada a R$250,00"
e a decisão de AMB-006 dizia "o limite de R$250,00 é aplicado ao valor total
do lançamento". As duas frases descrevem literalmente o comportamento
por-lançamento que foi implementado. Um desenvolvedor lendo só a spec chegaria
ao mesmo resultado errado — que é o critério de qualidade que a `RUBRICA.md`
usa.

A origem da confusão: a frase "sem dividir o valor pelo número de noites"
resolvia corretamente uma pergunta (*não fazer parsing de texto livre para
achar quantas noites*) e, no mesmo fôlego, respondia sem querer a outra
pergunta (*qual é a unidade do limite*) com a resposta errada. Eram duas
decisões distintas coladas numa frase só.

**O que mudou na spec:**
- RN-003 mudou de título ("Limite de hospedagem por lançamento" → "Limite
  diário de hospedagem") e passou a declarar a mecânica por referência a
  RN-001, dizendo explicitamente as duas negativas: o limite **nunca** é
  multiplicado pelo número de noites e **nunca** é aplicado por lançamento.
  O aceite ganhou o caso de duas hospedagens na mesma data.
- AMB-006 passou a decidir o que "diária" significa (**dia de calendário**) e
  a registrar a alternativa *por lançamento* como descartada, com o motivo:
  bastaria quebrar uma estadia em dois lançamentos na mesma data para receber
  R$500,00 no dia — o limite viraria algo que o próprio lançador controla.
- §7 ("Casos de borda") teve a linha de hospedagem corrigida e ganhou uma
  linha nova para duas hospedagens na mesma data.
- §10 ("O que fica em aberto") teve a limitação reescrita: continua sendo mais
  restritivo que a política provavelmente pretende, mas pela razão certa.

**Redação da justificativa unificada:** hospedagem usava "R$250,00 **diário**"
enquanto as outras categorias usavam "R$250,00 **no dia**". Com a mecânica
agora idêntica nas três, a redação passou a ser "no dia" para todas. Não é
cosmético: "diário" foi exatamente a palavra que sugeriu unidade de tempo
própria e ajudou a sustentar a leitura por-lançamento.

**O que isso invalidou:** `src/regras.py` perdeu `aplicar_limite_hospedagem`
(hospedagem agora entra em `LIMITES_DIARIOS_POR_CATEGORIA` e usa
`aplicar_limite_diario`, como as outras); `src/motor.py` perdeu o desvio de
hospedagem; `src/politica.py` perdeu `CATEGORIA_HOSPEDAGEM`, que só existia
para esse desvio. `exemplos/resultado-exemplo.json` teve a justificativa de
`d-010` ajustada ("diário" → "no dia").

**Por que os testes não pegaram:** o arquivo de exemplo tem duas hospedagens
(`d-010` e `d-013`), mas em datas diferentes — e `d-013` é barrada antes, por
nota fiscal (RN-005). Nenhum par de hospedagens chega junto à etapa de limite,
então agregado e por-lançamento produzem exatamente os mesmos totais
(R$585,43). O exemplo é cego para essa distinção. O único artefato onde a
interpretação errada ficava visível era o teste do agente — que afirmava o
comportamento errado com confiança. Lição registrada: teste escrito pelo mesmo
agente que interpretou a regra não é verificação independente da
interpretação.

**Tasks afetadas:** T-014 (reimplementada antes do commit; nada errado chegou
a entrar no histórico). T-018 (caso de borda de hospedagem multi-diária) teve
a descrição ajustada para a regra correta antes de ser executada.

**Custo:** resolvido dentro da própria T-014. Arquivos alterados:
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`,
`exemplos/resultado-exemplo.json`,
`src/politica.py`, `src/motor.py`,
`tests/test_regras.py`, `tests/test_motor.py`.

---

## D-003 — `descricao(id)` vira o formato único de referência a despesa · `17/08/2026`

**Gatilho:** ao implementar a T-013 (limite diário), o agente notou que a
justificativa de limite estourado citava a despesa que consumiu o limite só
pela `descricao` (`'Almoco com cliente'`), enquanto a duplicata — decidida em
[[D-002]] duas tasks antes — citava `descricao(id)`. Diferente do caso da
D-002, aqui **não havia conflito**: `spec.md` §4 ("Entrada e saída") e
`exemplos/resultado-exemplo.json` concordavam entre si no formato só-descrição.
Era inconsistência interna, não bug. O agente reportou em vez de padronizar por
conta própria, e a decisão do usuário foi padronizar.

**O que mudou na spec:**
- `spec.md` §4 ("Entrada e saída") ganhou uma regra geral, logo abaixo da
  tabela de saída: **toda** referência a outra despesa em qualquer
  `justificativa` usa `descricao(id)`, sem exceção.
- RN-007 deixou de repetir o formato e passou a apontar para §4 — antes a
  regra estava escrita em dois lugares, que é como duas versões divergem.
- O exemplo de saída em §4 (`d-002`) passou a mostrar
  `'Almoco com cliente(d-001)'`.

**Por quê:** a decisão vale para o formato em si (`descricao` sozinha é
ambígua, `id` sozinho é ilegível para quem confere no financeiro) e para o
lugar onde ela mora. Regra de formatação de saída que vive dentro de uma `RN`
específica só é descoberta por quem lê aquela regra — a próxima regra que
citar uma despesa vai reinventar o formato, que foi exatamente o que
aconteceu entre a T-010 e a T-013. Em §4, junto do schema de saída, ela é
encontrada por qualquer um que vá gerar saída.

**O que isso invalidou:** `exemplos/resultado-exemplo.json` (justificativa de
`d-002`) e a asserção de `test_rn001_limite_diario_alimentacao`, ambos
corrigidos na mesma leva. Nenhum teste quebrou sem ser corrigido junto.

**Tasks afetadas:** T-013 (ajustada antes do commit, sem retrabalho). T-010 já
estava no formato certo. Qualquer task futura que cite despesa na
justificativa passa a ter a regra em um lugar só.

**Custo:** resolvido dentro da própria T-013. Arquivos alterados:
`specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`,
`exemplos/resultado-exemplo.json`,
`src/politica.py`, `src/regras.py`, `src/motor.py`,
`tests/test_regras.py`.

---

## D-002 — Formato da justificativa de duplicata: `descricao(id)` · `17/08/2026`

**Gatilho:** durante a implementação da T-010 (filtro de duplicata), o agente
detectou que `spec.md` e `exemplos/resultado-exemplo.json` discordavam sobre o
conteúdo da justificativa de uma despesa negada como duplicata, e parou para
reportar antes de commitar:
- RN-007 exigia "justificativa citando o `id` da despesa original" (e
  `spec.md` §9, "Critérios de aceite": "citando `d-006`").
- `resultado-exemplo.json` (`d-007`) trazia `"Despesa identificada como
  duplicada da despesa 'Almoco' do dia 2026-07-09."` — citava `descricao` e
  data, **sem** citar o `id`.

Um desenvolvedor implementando só a partir da spec produziria uma saída que
não bate com o arquivo de exemplo do próprio projeto — exatamente a falha de
rastreabilidade que este repositório existe para evitar.

**O que mudou na spec:** RN-007 passou a definir o formato explicitamente — a
justificativa cita a `descricao` **e** o `id` da despesa original, no formato
`descricao(id)`. O critério de aceite de RN-007 passou a citar o valor
concreto esperado (`Almoco(d-006)`) em vez de só "citando `d-006`".

Na mesma leva, RN-013 teve suas duas citações a `§8` corrigidas para o formato
completo `spec.md §8 ("Ordem de aplicação das regras")` — a segunda delas não
tinha nem arquivo nem título. Isso é reincidência do problema que D-001 já
havia corrigido em outras seções, e a causa raiz foi identificada: a convenção
existia só como relato histórico **aqui**, no log, e não como regra no
`CLAUDE.md` — que é o arquivo que todo agente lê no início de cada sessão. A
regra foi promovida para `CLAUDE.md` (seção "Regras de trabalho") na mesma
sessão, e as citações incompletas de `tasks.md` (`§4`, `§7`, `§8`, `§9` sem
título) foram completadas junto.

**Por quê:** a decisão do usuário foi manter os dois dados em vez de escolher
um lado. A `descricao` é o que um humano do financeiro reconhece ao ler a
justificativa ("qual almoço?"); o `id` é o que torna a referência não ambígua
e verificável contra a entrada (duas despesas podem ter a mesma descrição).
Citar só o `id` é preciso mas ilegível; citar só a `descricao` é legível mas
ambíguo. `descricao(id)` resolve os dois sem custo.

**O que isso invalidou:** `exemplos/resultado-exemplo.json` foi corrigido na
mesma mudança (justificativa de `d-007`). Nenhum teste quebrou —
`test_rn007_duplicata_negada_primeira_mantida` foi escrito na mesma sessão e
já valida o formato novo (`"Almoco(d-006)" in resultado.justificativa`).

**Tasks afetadas:** T-010 (implementada com o formato final, sem retrabalho).
T-022 (integração ponta a ponta) passa a ter um alvo consistente entre spec e
exemplo para este item.

**Custo:** resolvido dentro da própria T-010, sem reabrir task anterior.
Arquivos alterados: `specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/DECISIONS.md`,
`specs/001-motor-reembolso/plan.md`,
`specs/001-motor-reembolso/tasks.md`,
`exemplos/resultado-exemplo.json`,
`src/regras.py`, `tests/test_regras.py`.

**Fica em aberto:** as demais justificativas de `resultado-exemplo.json`
(`d-005` categoria, `d-008` período, `d-009` estorno) ainda diferem
textualmente das produzidas por `regras.py`. Isso **não** foi resolvido nesta
entrada e precisa de decisão antes da T-022 — ou o teste de integração trata
`justificativa` de forma flexível, ou os textos são alinhados um a um.

---

## D-001 — Referências a seções tornadas resolvíveis sem contexto prévio · `17/08/2026`

**Gatilho:** o usuário perguntou se uma referência como `§8` no `plan.md` é
resolvível por um agente que não tenha a `spec.md` carregada no contexto no
momento da leitura. A resposta honesta foi "só com o número, não" — `§N`
sozinho depende de correlacionar o número com o título do cabeçalho
correspondente, o que só funciona se quem lê já souber a estrutura atual da
spec, e quebra silenciosamente se a spec for renumerada. Pedido explícito do
usuário: revisar o projeto inteiro e corrigir.

**O que mudou na spec:** nenhuma regra de negócio (`RN-NNN`) nem ambiguidade
(`AMB-NNN`) mudou de conteúdo. Mudou só a forma da citação:
- Toda referência `§N` (em §3, §7, §8, §9, §10) passou a vir acompanhada do
  título exato da seção entre parênteses — ex.: `§8` → `§8 ("Ordem de
  aplicação das regras")`.
- As 9 linhas `**Origem:**` de RN-001 a RN-012 deixaram de citar "política do
  RH, item N" (referência posicional a uma numeração que vive fora da spec,
  em `DESAFIO.md`) e passaram a citar só "política do RH" — a regra já
  reescreve o texto por extenso na própria linha `**Regra:**`, então a
  numeração externa não tinha valor de navegação.
- O bullet de RN-012 em §3 e a entrada de RN-012 em §10 ("O que fica em
  aberto") removeram a citação redundante "(política, item 6)" — RN-012 já
  está citada na mesma frase.

**Por quê:** a spec (e o `plan.md`, e o `RELATORIO.md`) precisam ser
navegáveis por qualquer agente ou pessoa que não tenha o documento inteiro
memorizado — é literalmente o critério que a `RUBRICA.md` usa para nota
máxima em qualidade de spec ("um desenvolvedor que nunca viu o projeto
implementaria a mesma coisa"). Uma referência que só resolve com contexto
prévio carregado falha esse critério, mesmo que o conteúdo da regra em si
esteja correto.

**O que isso invalidou:** nada de substância — nenhum critério de aceite,
regra ou decisão de ambiguidade mudou de sentido. Nenhum teste existe ainda
(projeto não chegou à fase de implementação), então nada quebrou.

**Tasks afetadas:** nenhuma — `tasks.md` ainda é só o template, a
implementação não começou.

**Custo:** ~30 linhas alteradas, resolvido em uma sessão. Commits `60995ad` e
`fea2cc8`. Arquivos alterados: `specs/001-motor-reembolso/spec.md`,
`specs/001-motor-reembolso/plan.md`, `docs/RELATORIO.md`.
(`specs/001-motor-reembolso/DECISIONS.md` não entra na lista: esta entrada foi
escrita depois, num commit à parte — ver a nota de processo abaixo.)

**Nota de processo:** esta entrada foi escrita depois que o usuário apontou,
corretamente, que a mudança de spec tinha sido commitada sem bump de versão
e sem entrada aqui — uma violação direta da regra do `CLAUDE.md` ("Qualquer
alteração na spec deve ser apontada em DECISIONS.MD"). Registrado aqui
também como lembrete: nenhuma edição em `spec.md`, por menor que pareça
(mesmo só citação/referência, sem mudar regra de negócio), sai sem passar
por este arquivo.
