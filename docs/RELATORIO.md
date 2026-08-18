# Relatório — Desafio SDD

**Aluno:** `Arthur Lorenzetti da Rosa` · **Repositório:** `https://github.com/tuca222/sdd-desafio` · **Data:** `17–18/08/2026`

> Isto não é redação. São **evidências**. Toda afirmação deve vir acompanhada de
> arquivo, hash de commit ou trecho de sessão exportada. Um parágrafo bonito sem
> evidência vale menos que uma frase curta com um hash.
>
> Vale 20 dos 100 pontos, e é a seção que mais separa notas.

---

## Delegação

*O que você fez, o que o Claude fez, e por que dividiu assim.*

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades | Claude, com validação do usuário | Claude cruzou os 9 itens da política do RH com os 14 registros de `despesas-exemplo.json` e levantou 11 candidatas a ambiguidade (mais que as 8 mínimas do desafio); o usuário revisou a lista antes de qualquer decisão. |
| Decidir as ambiguidades | 100% usuário | Cada uma das 11 decisões (agregação diária, reembolso parcial, fronteira de R$100, ordem de regras, viagem, diária de hospedagem, duplicatas, estornos, categoria maiúscula, arredondamento, período de competência) foi escolhida pelo usuário entre opções apresentadas pelo Claude — inclusive uma 12ª decisão (exclusão de duplicatas do `valor_total_despesas`) que o próprio Claude não tinha enxergado como ambiguidade separada até o usuário apontar o número errado. |
| Escrever a spec | Em conjunto | Claude escreveu a primeira versão completa do `spec.md` (10 seções) a partir das decisões já tomadas; o usuário revisou linha a linha, editou trechos diretamente (cabeçalho, tabela de campos de entrada, exemplo de saída) e pediu ajustes pontuais, que o Claude aplicou. |
| Desenhar a arquitetura | Claude propôs, usuário verificou decisão por decisão | Claude leu a spec fechada e escreveu a primeira versão do `plan.md` em modo de planejamento — mas a primeira tentativa já saiu com 4 decisões técnicas (DT-001 a DT-004: arquitetura do pipeline de regras, onde truncar RN-010, serialização Decimal→float, separação `regras.py`/`motor.py`) decididas e escritas como se já estivessem fechadas, sem perguntar. Rejeitei o pedido de aprovação (`ExitPlanMode`) e exigi que toda decisão técnica ainda não fixada em `CLAUDE.md`/spec fosse verificada comigo antes de entrar no plano. Daí em diante, cada DT (mais CLI, onde a política mora, granularidade dos testes) virou pergunta estruturada com alternativas, não proposta pronta. |
| Revisar rastreabilidade das citações (`spec.md`/`plan.md`/`RELATORIO.md`) | Usuário identificou o risco, Claude revisou o projeto e aplicou | Perguntei se uma referência como `§8` era resolvível por um agente sem a spec carregada no contexto; a resposta honesta foi "não, só o número não". Pedi revisão do projeto inteiro. Claude achou, além da fragilidade genérica, um bug real: a mesma notação `§4` em `plan.md` apontava ora para `spec.md`, ora para o próprio `plan.md`, sem nada que diferenciasse os dois casos. |
| Fatiar `tasks.md` em tasks executáveis | Claude propôs, usuário validou 2 decisões de granularidade | Pedi explicitamente que "qualquer decisão seja avaliada comigo antes de ser tomada". Claude leu `spec.md` v1.2 e `plan.md` v1.0 em modo de planejamento e, antes de escrever qualquer task, parou em duas decisões de granularidade — task por RN isolado vs. por mecanismo de código (RN-004/RN-013 não têm função própria); task de scaffolding com ou sem RN associado — e perguntou via pergunta estruturada com prévia de cada opção, em vez de decidir sozinho. As 23 tasks (T-001 a T-023) só foram escritas depois da minha resposta. |
| Ajustar `CLAUDE.md` (disciplina de `tasks.md` + fluxo de git) | 100% eu decidi o conteúdo da regra, Claude redigiu e commitou | Pedi duas mudanças de processo depois de usar o projeto na prática: exigir marcação `[x]` progressiva e task do tamanho de um commit, com sinalização obrigatória de qualquer agente que perceber violação (commit `00ca134`); e documentar que todo commit vai direto em `main`, sem branch/PR — motivado por ser um projeto "desafio" e não um projeto real. |
| Implementar (T-001 a T-026) | Claude escreveu 100% do código, eu aprovei task a task | Pedi explicitamente "implemente task por task, e a cada task finalizada aguarde minha aprovação". Nenhuma linha de `src/` foi escrita por mim. O controle não veio de escrever junto, veio de revisar **antes** de virar commit — 19 commits `feat(...)` e 7 `test(...)`, cada um com aprovação minha registrada na sessão. |
| Escrever testes | Claude, 57 testes | Todos gerados pelo Claude a partir do critério de aceite escrito na task. Isso tem um limite sério que descobri na prática — ver Diligência: um teste escrito pelo mesmo agente que interpretou a regra errada afirma a regra errada com total confiança, e passa. |
| Mudar o fluxo de aprovação no meio do caminho | 100% eu | O `CLAUDE.md` original dizia "commit não espera aprovação prévia — eu reviso depois". Depois de usar isso por 6 tasks, não gostei: cada ajuste virava um commit de correção em cima de um commit que já nascia errado. Pedi a inversão (implementa → eu reviso sem nada commitado → aprovo → commita), commit `7367769`. O resto da sessão rodou assim. |
| Escolher o modelo por tipo de trabalho | 100% eu | Percebi no meio da sessão que estava rodando em Sonnet e pedi Opus para código. O Claude não conseguia trocar sozinho — deixei registrado no `CLAUDE.md` que código usa Opus e que a troca é ação minha (`db0e4a6`). Da T-010 em diante a implementação foi em Opus 5. |
| Absorver o envelope | — | Ainda não realizado — só ocorre no Dia 2. |

**Onde deleguei e me arrependi:** Na fase de spec, nenhum arrependimento — tudo
que delegou (levantamento das ambiguidades, primeira versão do `spec.md`)
passou por revisão minha antes de virar decisão. Na fase de `plan.md`, quase
me arrependi: deixei o Claude escrever a primeira versão completa do plano, e
ele decidiu sozinho 4 decisões técnicas (DT-001 a DT-004) e já as escreveu
como fechadas, sem perguntar — só pedi as duas primeiras confirmações (CLI,
onde a política mora) antes dele escrever. Peguei antes de aprovar, rejeitando
o `ExitPlanMode` e exigindo verificação de toda decisão técnica ainda não
fixada. Não custou nada porque peguei a tempo, mas é sinal de que "propor e já
escrever como decidido" é o modo padrão do Claude — cabe a mim interromper
antes, não só revisar depois.

**Na fase de implementação, o arrependimento foi outro:** deixei o Claude
escrever código *e* os testes que provam esse código. Parece óbvio em
retrospecto, mas o efeito só ficou visível na T-014: ele interpretou a regra de
hospedagem errado, implementou errado, e escreveu um teste chamado
`test_rn003_hospedagem_nao_acumula_limite_entre_lancamentos_do_mesmo_dia` que
afirmava o comportamento errado — verde, confiante, e me apresentado como
evidência de que estava certo (ver Caso 3). Se eu tivesse escrito ao menos os
testes das regras que eu mesmo desambiguei, teria pego na hora. Não mudei o
processo no meio porque o custo de revisar a *regra* (em vez do teste) se
mostrou suficiente — mas foi sorte de eu ler a regra, não desenho.

**Onde não deleguei e deveria ter delegado:** Preenchi à mão o
`exemplos/resultado-exemplo.json` completo depois de fechar as
decisões. O cálculo dos totais eu faria de novo do mesmo jeito — foi
proposital, servindo de conferência cruzada independente do que o Claude
calculou (foi assim que peguei o erro do `valor_total_despesas`, ver
Discernimento). Mas preencher o `resultado-exemplo.json` inteiro à mão eu
poderia ter delegado: pedir para o Claude gerar o rascunho a partir da spec já
fechada e eu só validar linha a linha seria mais rápido do que escrever os 14
objetos `motor_reembolso_output` eu mesmo.

**Usei subagentes / skills / MCP / hooks?** Não, em nenhuma das fases. Na spec,
o gargalo não era pesquisa, era decisão humana sequencial — cada ambiguidade só
podia ser resolvida depois que a anterior estava fechada, e só eu podia decidir;
paralelizar em subagentes não teria o que paralelizar. Na implementação, o
raciocínio foi o mesmo por outro motivo: com aprovação a cada task, um subagente
trabalhando em paralelo estaria produzindo código que eu ainda não revisei, o
que é exatamente o que eu estava tentando evitar. O que usei foi mais simples e
funcionou melhor: **troca de modelo por tipo de trabalho** (Opus para código,
ver tabela acima) e o `CLAUDE.md` como memória de processo — quatro commits
`docs(claude)` nesta sessão (`587d864`, `7367769`, `db0e4a6`, `3e7662b`), todos
nascidos de um erro concreto que eu peguei e quis impedir de repetir.

---

## Descrição

*Como você transformou requisito ambíguo em requisito verificável.*

Pegue **um** requisito ambíguo da política do RH e mostre a evolução:

O requisito é o item 8 da política: **"Duplicatas devem ser tratadas."**

**Versão 1 (minha primeira escrita, decisão de AMB-007 no `spec.md`):**
> ```
> duas despesas são duplicatas quando todos os campos são idênticos exceto
> `id` (`data`, `categoria`, `descricao`, `fornecedor`, `valor`,
> `tem_nota_fiscal`). A primeira ocorrência (pela ordem de entrada) é avaliada
> normalmente; as demais são negadas.
> ```

**Versão final:**
> ```
> duas despesas são duplicatas quando todos os campos são idênticos exceto
> `id` (`data`, `categoria`, `descricao`, `fornecedor`, `valor`,
> `tem_nota_fiscal`). A primeira ocorrência (pela ordem de entrada) é avaliada
> normalmente; as demais são negadas. Além de negadas para fins de reembolso,
> as ocorrências duplicadas também não entram em `valor_total_despesas`.
> ```

**O que estava ambíguo:** a política resolve "o que é duplicata" e "o que
acontece com o reembolso dela" só implicitamente — "devem ser tratadas" não diz
como. Minha primeira versão da spec respondia duas das três perguntas que a
frase esconde (o que conta como duplicata; qual ocorrência é negada), mas
ficou muda sobre a terceira: o valor de uma despesa duplicada entra ou não no
total bruto de despesas do período (`valor_total_despesas`)? Essa pergunta nem
tinha virado uma `AMB` separada — estava sendo decidida em silêncio dentro do
cálculo, exatamente o tipo de coisa que o desafio pune.

**Como percebi:** não foi um teste quebrando nem o Claude perguntando — fui eu
recalculando os totais do exemplo à mão, como conferência independente do que
o Claude tinha calculado. Cheguei em R$1.806,94 contra os R$1.861,84 que
constavam na spec; a diferença é exatamente o valor de `d-007` (R$54,90), a
despesa duplicada. A divergência entre os dois números foi o sinal de que a
regra estava incompleta.

**Commit da mudança:** pedi para o Claude já aplicar a correção na spec antes
de eu mandar comitar, então as duas versões acima não ficaram em commits
separados — só existe o commit `47f18f9` (`docs(spec): Retirando
ambiguidades...`), que já sai com a versão final. A versão 1 só existe no
histórico da conversa, exportado em `docs/sessions/02_planejamento_spec.txt`.

---

## Discernimento

*Onde o Claude errou e você pegou.*

> **Sem um caso concreto e verificável, esta seção vale zero.** Não existe projeto
> de dois dias em que o modelo acertou tudo. A ausência do caso não prova que o
> modelo foi perfeito — prova que ninguém estava conferindo.

### Caso 1

**O que ele propôs:** na primeira versão completa da spec, o Claude calculou
manualmente os totais esperados para o arquivo de exemplo e propôs, no
critério de aceite (spec.md §9, "Critérios de aceite"), `valor_total_despesas = R$1.861,84`.

**Por que estava errado:** o Claude já tinha escrito a regra RN-007
(duplicatas), que dizia que a ocorrência duplicada (`d-007`) não gera
reembolso. Mas, ao somar o total bruto de despesas do período, incluiu o valor
de `d-007` (R$54,90) do mesmo jeito — aplicou a lógica de "duplicata não
conta" só para `valor_reembolsavel`, sem estender a mesma lógica para
`valor_total_despesas`. Não foi erro de aritmética (a soma de R$1.861,84
estava certa para o conjunto de despesas que ele somou) — foi erro de escopo:
somou o conjunto errado de despesas, uma decisão de negócio que tomou sozinho
e nunca registrou como ambiguidade.

**Como eu detectei:** recalculei os totais à mão, de forma independente, como
conferência do que o Claude tinha calculado. Cheguei em R$1.806,94; a
diferença exata (R$54,90) apontava direto para `d-007`.

**O que eu fiz:** pedi para o Claude incluir a decisão explicitamente na spec.
Ele corrigiu RN-007 e AMB-007 para deixar a regra escrita ("as ocorrências
duplicadas também não entram em `valor_total_despesas`"), atualizou a
descrição do campo em spec.md §4 ("Entrada e saída") e os critérios de aceite em spec.md §9 ("Critérios de aceite").

**Onde está a evidência:** `docs/sessions/02_planejamento_spec.txt`, linha ~1242,
minha mensagem: "O valor de R$1.861,84 estava incorreto, o certo é R$1.806,94
pois quando há duplicatas, ela não deve entrar para o calculo do valor total
de despesas."; correção aplicada no commit `47f18f9`.

### Caso 2

**O que ele propôs:** pedi ao Claude para revisar o projeto inteiro e corrigir
as citações `§N` que dependiam de contexto prévio para serem resolvidas
(detalhado na tabela de Delegação). Ele revisou `spec.md`, `plan.md` e
`RELATORIO.md`, aplicou a correção certa, e commitou (`60995ad`) — mas o
commit alterou o conteúdo de `spec.md` sem incrementar a **Versão**/**Status**
no cabeçalho e sem nenhuma entrada em `DECISIONS.md`.

**Por que estava errado:** o próprio `CLAUDE.md`, que o Claude tinha lido no
início da sessão, já dizia explicitamente "Qualquer alteração na spec deve
ser apontada em DECISIONS.MD." Não foi uma regra nova que ele não conhecia —
foi uma regra que ele tinha na cabeça e não aplicou no momento de commitar,
provavelmente porque a mudança "parecia pequena" (só citação, nenhuma regra
de negócio mudou de sentido). É exatamente o tipo de coisa que a `RUBRICA.md`
pune diretamente: "`DECISIONS.md` ausente tendo havido mudança de spec: −5".

**Como eu detectei:** reli o diff e o `DECISIONS.md` depois do commit e notei
os dois problemas ao mesmo tempo: cabeçalho de `spec.md` ainda em `1.1` (igual
antes da mudança) e nenhuma entrada nova no arquivo de decisões.

**O que eu fiz:** apontei os dois problemas explicitamente ("erros graves").
Pedi a correção retroativa — o Claude incrementou `spec.md` para `1.2`,
atualizou o `Status` e escreveu a entrada `D-001` em `DECISIONS.md`
(commit `18442c6`). Fui além: pedi para ele revisar e corrigir o próprio
`CLAUDE.md`, para que a regra deixasse de ser uma frase solta e virasse um
checklist de três partes obrigatórias no mesmo commit (mudança + versão/status
+ `DECISIONS.md`), e que passasse a existir também uma regra explícita de
manter `plan.md` sincronizado com a versão de `spec.md` que ele referencia
(commit `49601e1`) — o que revelou, na hora, um segundo drift real: `plan.md`
ainda apontava para a spec `1.1`, corrigido no mesmo commit seguinte
(`dd76911`).

**Onde está a evidência:** `docs/sessions/03_plan.txt`, linha ~1823, minha
mensagem: "Você cometeu dois erros graves: 1. A spec foi atualizada porém a
versão não foi incrementada e nem o status foi alterado. 2. Este foi o maior
erro de todos, a spec foi alterada e NADA foi escrito no DECISIONS.md."; e a
sequência de commits `60995ad` (erro), `18442c6` (correção retroativa) e
`49601e1` (correção sistêmica no `CLAUDE.md`).

### Caso 3 — o mais grave: implementou a regra errada, e o teste dele confirmava

**O que ele propôs:** na T-014, implementou o limite de hospedagem **por
lançamento** — cada despesa de hospedagem com seus próprios R$250,00. E
escreveu um teste,
`test_rn003_hospedagem_nao_acumula_limite_entre_lancamentos_do_mesmo_dia`,
afirmando que duas hospedagens no mesmo dia recebem R$250,00 **cada**. Me
apresentou verde, junto com o argumento de que aquele teste era justamente "o
que separa RN-003 de RN-001/002".

**Por que estava errado:** o limite é diário e agregado — duas hospedagens no
mesmo dia dividem os mesmos R$250,00, igual às outras categorias.

**Mas o erro não era só dele: a spec estava errada.** RN-003 dizia "cada
despesa de categoria `hospedagem` é tratada como uma diária única e limitada a
R$250,00", e a decisão de AMB-006 dizia "o limite é aplicado ao valor total do
lançamento". Isso descreve literalmente o que ele implementou. Um
desenvolvedor lendo só a spec chegaria ao mesmo resultado — que é exatamente o
critério que a `RUBRICA.md` usa para nota máxima em qualidade de spec. A
origem da confusão foi uma frase só: *"sem dividir o valor pelo número de
noites"* respondia certo a uma pergunta (não fazer parsing de texto livre) e,
no mesmo fôlego, respondia errado a outra (qual é a unidade do limite). Eram
duas decisões coladas.

**Como eu detectei:** lendo o resumo da task, não o teste. O que me fez parar
foi a asserção do teste dizendo que cada lançamento recebe R$250,00 — bati com
o que eu tinha decidido quando desambiguei AMB-006 e não fechou.

**Por que nenhum teste pegou:** o arquivo de exemplo é **cego** para essa
distinção. As duas hospedagens (`d-010` e `d-013`) estão em datas diferentes, e
`d-013` morre antes por falta de nota fiscal (RN-005) — nenhum par de
hospedagens chega junto à etapa de limite. Agregado ou por lançamento, o total
dá os mesmos R$585,43. O único artefato onde a interpretação errada aparecia
era o teste do próprio Claude, que a afirmava com confiança.

**O que eu fiz:** reprovei a task e mandei corrigir os três lados — código,
spec e documentação. RN-003 virou "Limite **diário** de hospedagem" e passou a
declarar as duas negativas explicitamente (o limite nunca é multiplicado por
noites e nunca é por lançamento); AMB-006 passou a registrar *por lançamento*
como alternativa **descartada**, com o motivo que fecha a porta: bastaria
quebrar uma estadia em dois lançamentos na mesma data para receber R$500,00 no
dia. O teste que afirmava o errado virou o que prova o certo.

**Onde está a evidência:** `docs/sessions/05_tasks_implement.txt`, linha ~4002,
minha mensagem: "Não aprovado. Houve uma confusão para essa regra de
hospedagem... se tem duas despesas dessa categoria no mesmo dia, os 250,00
reais vale para aquele dia. Então o seu
test_rn003_hospedagem_nao_acumula_limite_entre_lancamentos_do_mesmo_dia, por
exemplo, o valor reembolsável da segunda despesa deveria ser '0.00'"; correção
em `b4332c3` (spec) e `0fc3bd2` (código), registrada em `DECISIONS.md` D-004.

### Caso 4 — repetiu exatamente o erro que uma decisão anterior já tinha corrigido

**O que ele propôs:** escreveu a entrada D-002 no `DECISIONS.md` citando
"(e §9, ...)" — o número da seção sem dizer de qual arquivo.

**Por que estava errado:** a sessão anterior tinha gerado a decisão **D-001**,
que existe **exatamente** para isso: tornar toda citação `§N` resolvível sem
contexto prévio. Ele repetiu, no próprio arquivo que documenta a correção, o
erro que a correção eliminou.

**Como eu detectei:** li a entrada nova do `DECISIONS.md` antes de aprovar o
commit e a citação me pareceu solta.

**O que eu fiz:** mandei revisar e, principalmente, **descobrir por que
repetiu**. A causa raiz foi boa: a convenção existia só como relato histórico
em D-001 — um log do que foi consertado uma vez — e **nunca tinha entrado no
`CLAUDE.md`**, que é o arquivo que todo agente lê no início de cada sessão.
Uma regra registrada no log não é uma regra em vigor. Promovi a convenção para
o `CLAUDE.md` (`db0e4a6`), e a varredura que pedi junto achou mais duas
citações incompletas em RN-013 e seis em `tasks.md`.

**Onde está a evidência:** `docs/sessions/05_tasks_implement.txt`, linha ~2442,
minha mensagem: "Você referenciou §9 em decisions.md mas nao colocou para qual
arquivo ele deve referenciar. Isso já foi discutido em outra sessão, isso
deveria estar claro."

### Caso 5 — o autorrelato de custo era sistematicamente otimista

**O que ele propôs:** o campo **Custo** da entrada D-005 dizia "6 arquivos de
produção/spec + 3 de teste".

**Por que estava errado:** foram **13** arquivos. E quando mandei conferir as
outras entradas, o padrão se repetia em todas: D-002 dizia 5 para 7 arquivos
reais, D-003 dizia 5 para 9, e D-004 dizia "7 arquivos" enquanto listava 8 na
própria frase — a contagem escrita já não fechava com a lista ao lado dela.
Nenhuma nomeava os arquivos de teste, todas escondiam atrás de "+ teste".

**Como eu detectei:** li o campo `Custo` e o número não bateu com o tamanho da
mudança que eu tinha acabado de revisar.

**O que eu fiz:** mandei listar **todos** os arquivos, nominalmente, e
padronizar isso no `CLAUDE.md` (`3e7662b`). A regra que ficou proíbe escrever a
contagem junto da lista — foi ela que desencontrou em D-004 — e exige tirar a
lista do `git status`/`git show`, não da memória. Motivo: custo subcontado faz
a mudança de spec parecer mais barata do que foi, que é o oposto do que o
`DECISIONS.md` existe para registrar.

**Onde está a evidência:** `docs/sessions/05_tasks_implement.txt`, linha ~6224,
minha mensagem: "em 'Custo' só é citado 6 arquivos de produção/spec. Aqui você
deve citar exatamente todos os arquivos que sofreram alteração."

**Padrão que eu notei:** o Claude segue regras de conteúdo (o que a spec deve
dizer) com mais disciplina do que regras de processo sobre o próprio ato de
commitar (versionar, registrar). Mudanças que "parecem pequenas" no conteúdo
são exatamente onde ele relaxa a disciplina de processo — o que é o oposto do
que deveria acontecer, já que é justamente aí que ninguém mais vai notar sem
uma auditoria explícita do `DECISIONS.md`. Passei a conferir esse arquivo
sempre que uma sessão mexe em `spec.md`, mesmo quando a mudança parece
cosmética.

**O padrão que a fase de implementação acrescentou:** ele é muito melhor em
seguir a spec do que em desconfiar dela. Nos Casos 3 e 4, e também nas
correções que viraram D-005 e D-006, o erro não foi contrariar o que estava
escrito — foi seguir fielmente um texto ambíguo ou incompleto sem sinalizar a
ambiguidade. E o autorrelato dele é otimista de forma consistente (Caso 5): o
custo declarado era sempre menor que o real, nunca maior. As duas coisas
juntas significam que revisar **o resultado que ele apresenta** não basta; o
que pegou os erros de verdade foi eu reler **a regra** e comparar com o que eu
tinha decidido.

---

## Diligência

*O que você verificou antes de aceitar.*

**Meu procedimento de verificação:** li a spec completa, linha a linha, depois
que o Claude entregou a primeira versão — e não só li: fui alterando
diretamente no arquivo tudo que achei confuso, incompleto ou que dava para
melhorar (cabeçalho, tabela de campos de entrada, exemplo de saída, e a
correção do total que virou o Caso 1 de Discernimento), em vez de só listar
pedidos de ajuste para o Claude aplicar. No `plan.md`, mantive o mesmo hábito:
editei diretamente duas células da tabela de Stack e o diagrama de arquitetura
em vez de só pedir ajuste — e isso quase colidiu com uma correção que o Claude
estava aplicando em paralelo num worktree isolado; a sessão parou, me
perguntou como reconciliar, e eu disse explicitamente o que manter de cada
lado em vez de deixar ele decidir sozinho.

**Na implementação, o procedimento mudou de forma — e a mudança foi a coisa
mais útil que fiz.** Comecei com o fluxo original do `CLAUDE.md` ("commit
primeiro, eu reviso depois"). Depois de 6 tasks percebi o efeito colateral:
todo ajuste virava um commit de correção empilhado sobre um commit que já
nascia errado, e o `git log` — que é justamente o que a correção do desafio
vai ler — ficava contando a história dos meus rascunhos em vez das minhas
decisões. Inverti (`7367769`): o Claude implementa, eu reviso **sem nada
commitado ainda**, aprovo, e só então ele commita. Foi assim que os Casos 3, 4
e 5 foram pegos *antes* de entrar no histórico — o código errado de hospedagem
nunca chegou a existir em `main`.

**Li o diff inteiro em que porcentagem das entregas?** 100% das entregas de
spec/plan — inclusive achei, no `plan.md`, dois itens da tabela de Riscos que
não faziam sentido (erro de arredondamento já prevenido por arquitetura; ordem
de regras já fechada na spec) e pedi para tirar.

Na implementação, a revisão foi de **outra natureza**, e o que a sessão
registra é isto: as 26 tasks passaram por aprovação explícita minha, e as
reprovações/correções que eu emiti foram sobre a **regra** e sobre os
**documentos**, não sobre a forma do código — hospedagem (Caso 3), citação `§N`
(Caso 4), campo `Custo` (Caso 5), placeholder de hash, legibilidade de teste,
`modelos.py` ausente no README, `pyproject.toml` decorativo e `egg-info` fora
do `.gitignore`. Nenhuma correção minha foi de estilo ou de implementação
interna. Isso diz duas coisas: que a revisão de regra é onde meu tempo rendeu,
e que eu confiei no código em si mais do que na interpretação — o que é
defensável, mas é uma aposta, não uma verificação.

**O que aceitei sem verificar direito na spec/plan, e o que me custou:**
aceitei, sem conferir na hora, um commit do Claude que alterava `spec.md`
(correção de citações `§N`) sem incrementar versão/status e sem entrada em
`DECISIONS.md` — apesar de essa regra já estar escrita no `CLAUDE.md` desde o
início do projeto. Só percebi ao reler o `DECISIONS.md` depois, não durante o
commit em si (ver Caso 2 de Discernimento). O custo foi baixo porque peguei
antes do fim da sessão, mas é o tipo de lacuna que, numa sessão mais corrida
ou sem essa releitura específica, ficaria sem registro até a correção do
projeto notar.

**O que aceitei sem verificar direito na implementação:** o campo **Commit** de
`tasks.md`. Na T-001, o Claude marcou a task como `[x]` e deixou o campo com o
placeholder `<hash preenchido depois>` — e eu aprovei o commit. Só notei
depois, relendo o arquivo (`docs/sessions/05_tasks_implement.txt`, linha ~327).
Custo baixo porque peguei na task seguinte, mas se tivesse passado, a
rastreabilidade task → commit — que é 25 dos 100 pontos — teria ficado furada
logo na primeira task. A correção virou regra no `CLAUDE.md` (`587d864`): como
o hash não existe no momento em que a task é marcada, fechar uma task passou a
exigir **dois** commits em sequência, e uma task não está encerrada enquanto o
campo mostrar o placeholder. As 26 tasks terminaram com hash real — conferi com
`grep -c '^  - \*\*Commit:\*\*$'`, que dá zero.

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
Os 57 foram escritos pelo Claude. E a resposta honesta para a segunda parte é:
**pelo teste sozinho, eu não sei — e tenho prova disso nesta sessão.** O teste
de hospedagem do Caso 3 estava verde, tinha nome descritivo, e afirmava o
comportamento errado com confiança. Um teste escrito pelo mesmo agente que
interpretou a regra é uma repetição da interpretação dele, não uma verificação
dela.

O que reduziu o risco, na prática, foram três coisas:

1. **Revisar a regra, não o teste.** Foi o que pegou o Caso 3. O teste parecia
   ótimo; o que não fechava era a regra que ele afirmava.
2. **Exigir que teste de ausência construa o cenário que acionaria a coisa.**
   Em RN-012 (adicional de viagem) e no caso de fim de semana, um teste do tipo
   "não tem bônus" passaria mesmo se o bônus existisse. Os que ficaram usam
   valores que são exatamente os limites ampliados em 50% (R$90 e R$120) e
   montam o cenário que AMB-005 proíbe inferir — hospedagem no mesmo dia. O
   Claude chegou a rodar a simulação com os limites ampliados para mostrar que
   as asserções quebrariam de fato, em vez de só afirmar que o teste era bom.
3. **Teste na junção, não só nas peças.** O bug do `valor` truncado aparecendo
   na saída (D-006) era invisível para todo teste unitário: cada um exercitava
   ou uma regra, ou o motor, ou a serialização com dados montados à mão. Só
   apareceu quando rodei `parser → motor → saida` com o arquivo real, na T-025.
   Bug de borda mora na costura, e a costura não tinha teste até a T-022.

O que hoje me dá mais confiança não é a contagem de 57, é o teste de integração
que roda a **CLI de verdade** (arquivo de entrada → arquivo de saída) e compara
o resultado inteiro com `exemplos/resultado-exemplo.json`, que eu preenchi à
mão a partir das minhas decisões.

**Mas preciso ser honesto sobre o limite disso.** Esse arquivo começou como
oráculo independente — foi ele que pegou o erro de R$1.861,84 no Dia 1 (Caso
1). Ao longo da implementação, porém, eu **alinhei o exemplo ao código** quatro
vezes: o formato `descricao(id)` (D-002 e D-003), a redação de hospedagem
(D-004) e, no fim, as três últimas justificativas de `d-005`, `d-008` e `d-009`
na T-022. Cada alinhamento foi decisão consciente minha e com motivo — num
deles o exemplo é que estava errado, com "extorno" no lugar de "estorno" — mas
o efeito acumulado é que o exemplo perdeu parte da independência que o tornava
valioso. **O que continua independente são os números:** nenhum valor, nem os
dois totais, mudou desde que eu os calculei à mão; o que convergiu para o
código foi só texto de justificativa. Se eu refizesse, manteria os textos
divergindo e faria o teste de integração comparar valores de forma estrita e
justificativa de forma semântica — assim o oráculo continua sendo meu, não do
código.

---

## O envelope

*A mudança de requisito do Dia 2.*

**Quantos arquivos toquei na mão:** `<n>`
**Quanto tempo levou:** `<...>`
**Diff de absorção:** `<n> arquivos, +<n>/-<n> linhas` (`git diff <hash-antes> HEAD --stat`)

**Absorveu de graça:** <o que a arquitetura já suportava e por quê>

**Resistiu:** <o que teve que ser quebrado e por quê>

**Ordem em que fiz:** <spec → tasks → código? ou código → spec? seja honesto:
a correção vê os timestamps dos commits de qualquer forma>

**Se eu tivesse escrito a spec original sabendo desta mudança:**

**O que a spec me poupou, em concreto:**

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?**

**Para qual não valeria?**

**O que eu faria diferente:**

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
