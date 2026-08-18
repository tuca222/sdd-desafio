# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

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

**Custo:** 7 arquivos (`spec.md`, `DECISIONS.md`, `plan.md`, `tasks.md`,
`exemplos/resultado-exemplo.json`, `src/politica.py`, `src/regras.py`,
`src/motor.py` + 2 arquivos de teste), resolvido dentro da própria T-014.

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

**Custo:** 5 arquivos (`spec.md`, `DECISIONS.md`, `plan.md`,
`exemplos/resultado-exemplo.json`, `src/regras.py` + teste), resolvido dentro
da própria T-013.

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

**Custo:** 5 arquivos (`spec.md`, `DECISIONS.md`, `plan.md`,
`exemplos/resultado-exemplo.json`, `src/regras.py` + teste), resolvido dentro
da própria T-010, sem reabrir task anterior.

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

**Custo:** 3 arquivos tocados (`spec.md`, `plan.md`, `docs/RELATORIO.md`),
~30 linhas alteradas, resolvido em uma sessão. Commits `60995ad` e `fea2cc8`.

**Nota de processo:** esta entrada foi escrita depois que o usuário apontou,
corretamente, que a mudança de spec tinha sido commitada sem bump de versão
e sem entrada aqui — uma violação direta da regra do `CLAUDE.md` ("Qualquer
alteração na spec deve ser apontada em DECISIONS.MD"). Registrado aqui
também como lembrete: nenhuma edição em `spec.md`, por menor que pareça
(mesmo só citação/referência, sem mudar regra de negócio), sai sem passar
por este arquivo.
