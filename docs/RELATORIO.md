# Relatório — Desafio SDD

**Aluno:** `Arthur Lorenzetti da Rosa` · **Repositório:** `https://github.com/tuca222/sdd-desafio` · **Data:** `17–18/08/2026`

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
| Escrever testes | Claude, 125 testes (57 ao fim do Dia 1) | Todos gerados pelo Claude a partir do critério de aceite escrito na task. Isso tem um limite sério que descobri na prática — ver Diligência: um teste escrito pelo mesmo agente que interpretou a regra errada afirma a regra errada com total confiança, e passa. |
| Mudar o fluxo de aprovação no meio do caminho | 100% eu | O `CLAUDE.md` original dizia "commit não espera aprovação prévia — eu reviso depois". Depois de usar isso por 6 tasks, não gostei: cada ajuste virava um commit de correção em cima de um commit que já nascia errado. Pedi a inversão (implementa → eu reviso sem nada commitado → aprovo → commita), commit `7367769`. O resto da sessão rodou assim. |
| Escolher o modelo por tipo de trabalho | 100% eu | Percebi no meio da sessão que estava rodando em Sonnet e pedi Opus para código. O Claude não conseguia trocar sozinho — deixei registrado no `CLAUDE.md` que código usa Opus e que a troca é ação minha (`db0e4a6`). Da T-010 em diante a implementação foi em Opus 5. |
| Absorver o envelope (spec) | Eu absorvi sozinho, antes da sessão; Claude leu depois e levantou o que passou | **Li a v4 e os quatro arquivos do envelope por conta própria e abri a sessão com decisões já tomadas**, não com perguntas (`docs/sessions/07_spec_2.0.txt`, linhas 6–80). **Só depois disso o Claude leu o envelope**, validou uma a uma essas decisões e levantou seis ambiguidades que eu não tinha enxergado. **As seis decisões foram minhas**, escolhidas entre alternativas apresentadas com o efeito de cada uma. Porem, nesta mesma fase o Claude escreveu na spec uma decisão sobre o campo `vigencia` que ninguém tomou, e a validação que hoje é RN-017 existe porque eu peguei isso na revisão (ver Caso 7 de Discernimento). Saldo: 8 commits, `a5d6889`..`709031b`, +1840/−179 linhas, **zero** em `src/` e `tests/`. |
| Implementar o envelope (T-028 a T-050) | Claude escreveu 100% do código, eu revisei antes de cada commit | Pedi a Fase 5 inteira **num lote só** (`docs/sessions/08_tasks_implement_2.0.txt`, linha 6), e não task a task como no Dia 1: 18 tasks revisadas juntas antes do primeiro commit. Os três ajustes que emiti depois vieram de leitura minha do resultado, não de teste vermelho — duplicata comparando valor truncado (linha 1584), diagrama do `plan.md` fora da realidade do código (linha 1820) e as flags de política/câmbio opcionais (linha 2436, Caso 9). Saldo: 56 commits, `3524a9c`..`12676ba`, `41 arquivos, +3687/−642`. |

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
evidência de que estava certo (ver Caso 3). Se eu tivesse detalhado melhor, ou até mesmo escrito os testes das regras que eu mesmo desambiguei, provavelmente não aconteceria.

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
raciocínio foi o mesmo por outro motivo: Achei que seria melhor só deixar o claude seguir com a minha aprovação para cada task, um subagente
trabalhando em paralelo estaria produzindo código que eu ainda não revisei, o
que é exatamente o que eu estava tentando evitar. Acho que isso se dá também por ser minha primeira vez aplicando SDD na prática, então ainda estou aprendendo e me acostumando com o fluxo de trabalho.

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

**Como eu detectei:** lendo o resumo da task, percebi a asserção do teste dizendo que cada lançamento do tipo `hospedagem`, lançados no mesmo dia, recebem R$250,00 de reembolso — bati com o que eu tinha decidido quando desambiguei AMB-006 e não fechou.

**Por que nenhum teste pegou:** o arquivo de exemplo é **cego** para essa
distinção. As duas hospedagens (`d-010` e `d-013`) estão em datas diferentes, e
`d-013` morre antes por falta de nota fiscal (RN-005) — nenhum par de
hospedagens chega junto à etapa de limite. Agregado ou por lançamento, o total
dá os mesmos R$585,43. O único artefato onde a interpretação errada aparecia
era o teste do próprio Claude, que a afirmava com confiança.

**O que eu fiz:** reprovei a task e mandei corrigir — código, spec e documentação. RN-003 virou "Limite **diário** de hospedagem" e passou a declarar as duas negativas explicitamente; AMB-006 passou a registrar *por lançamento* como alternativa **descartada**.

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

### Caso 5 — especificação do custo em DECISIONS.md sem padronização e incorreta

**O que ele propôs:** o campo **Custo** da entrada D-005 dizia "6 arquivos de
produção/spec + 3 de teste".

**Por que estava errado:** foram **13** arquivos. E quando mandei conferir as
outras entradas, o padrão se repetia em todas: D-002 dizia 5 para 7 arquivos
reais, D-003 dizia 5 para 9, e D-004 dizia "7 arquivos" enquanto listava 8 na
própria frase — a contagem escrita já não fechava com a lista ao lado dela.
Nenhuma nomeava os arquivos de teste, todas escondiam atrás de "+ teste".

**Como eu detectei:** li o campo `Custo` e o número não bateu com o tamanho da
mudança que eu tinha acabado de revisar. Além de que estava totalmente diferente a forma de refereciar o custo em cada decisão descrita.

**O que eu fiz:** mandei listar **todos** os arquivos, nominalmente, e
padronizar isso no `CLAUDE.md` (`3e7662b`). A regra que ficou proíbe escrever a
contagem junto da lista — foi ela que desencontrou em D-004 — e exige tirar a
lista do `git status`/`git show`, não da memória. Motivo: custo incorreto e não padronizado não refelete a realidade da mudança na spec.

**Onde está a evidência:** `docs/sessions/05_tasks_implement.txt`, linha ~6224,
minha mensagem: "em 'Custo' só é citado 6 arquivos de produção/spec. Aqui você
deve citar exatamente todos os arquivos que sofreram alteração."

### Caso 6 — todos casos de testes verde, e o entregável visivelmente errado

**O que ele propôs:** o projeto fechado. As 26 tasks concluídas, 57 testes
passando, `ruff` limpo, os 14 critérios de aceite da spec.md §9 ("Critérios de
aceite") marcados, e o cabeçalho da spec em "implementada — todos os critérios
de aceite verificados por teste automatizado". A T-023 ia além e registrava, no
campo **Verificado em:**, que num checkout limpo "rodar sem instalar nada gerou
`resultado.json` idêntico ao exemplo".

**Por que estava errado:** o JSON de saída emitia os valores monetários com uma
casa decimal — `"valor": 72.5`, `"valor_reembolsavel": 60.0`, `0.0` — onde
`exemplos/resultado-exemplo.json` traz `72.50`, `60.00` e `0.00`. Para valor
monetário isso não é formato válido: `R$60,0` não é o que está escrito no
comprovante que o financeiro confere. A causa era `saida.py` fazendo
`float(Decimal)`: o `Decimal` carrega a escala, o `float` não carrega nada, e
`json.dump` serializa pelo `repr`, apagando a casa terminada em zero. E o
"idêntico ao exemplo" da T-023 nunca tinha sido idêntico — a comparação tinha
sido feita sobre o conteúdo interpretado, não sobre o texto do arquivo.

**Como eu detectei:** rodei o sistema eu mesmo, pelo comando do `README.md`, e
**li o arquivo de saída** conferindo valor por valor contra a entrada. Não
confiei na suíte verde nem no relato de que a saída batia com o exemplo.

Isso importa porque a suíte tinha um ponto cego sistemático, não uma lacuna de
cobertura: existia um teste de integração ponta a ponta
(`test_saida_e_identica_ao_resultado_esperado`) cuja função era exatamente
comparar a saída real contra `exemplos/resultado-exemplo.json`. Ele passava. Ele
comparava os dois lados **depois** de `json.loads`, e como estruturas de dados
`60.0` e `60.00` são o mesmo número. Nenhum teste automatizado do projeto era
capaz de enxergar esse defeito, porque todos olhavam o valor e o defeito estava
na representação. Só a leitura humana do artefato entregue pegava.

**O que eu fiz:** três coisas, e a ordem das duas primeiras é o que fez
diferença.

Primeiro, relatei com precisão em vez de dizer "os decimais estão errados":
apontei que `valor_total_despesas`, `valor_total_reembolsavel` e os dois valores
de `d-011` estavam **corretos**, e que o resto estava com uma casa só. Esses
contra-exemplos eram o diagnóstico — `1806.94`, `585.43`, `33.333` e `33.33` têm
o último dígito decimal diferente de zero, ou seja, não tinham nada a perder na
conversão para `float` (o mesmo vale para o `100.01` de `d-004`, que também saiu
intacto). Descrever o que estava certo levou direto ao mecanismo; um relato
genérico teria levado a procurar erro de cálculo, que não existia.

Segundo, pedi **análise e uma task**, não a correção. Isso forçou o fluxo a
passar pela spec, e foi aí que apareceu o problema de fundo: a spec.md §4
("Entrada e saída") dizia que os valores produzidos têm "no **máximo** 2 casas
decimais" — redação que o defeito satisfazia formalmente. Não havia regra que
sustentasse a correção. A spec foi para 1.9 trocando "máximo" por "exatamente"
(`D-008`), e ganhou um critério novo na spec.md §9 ("Critérios de aceite")
exigindo que o **texto** do arquivo seja idêntico ao do exemplo — o critério que
teria pego isso no primeiro dia. A `plan.md` DT-004 ("Serialização de `Decimal`
na saída") teve de ser reescrita: ela decidia exatamente o contrário, e
descartava a solução correta com o argumento de que "a representação textual do
`float` resultante é exata para esses valores" — verdadeiro quanto ao valor,
falso quanto à escala.

Terceiro, quando o Claude propôs resolver a formatação pendente de três arquivos
num commit `style:` separado, recusei: commit que altera código sem task
referenciada não existe neste projeto. Entrou no commit da T-027.

**Onde está a evidência:** `docs/sessions/06_bugfix.txt`, linha ~8, minha
mensagem: "Rodei o código desenvolvido como manda o @README.md (...) Encontrei
um bug no json de saída. (...) Porém todos os outros valores das outras
despesas, inclusive o valor reembolsável ficaram tudo com apenas 1 casa decimal.
Que para valor monetário fica errado e feio."; e linha ~336, a recusa do commit
sem task: "Não quero que você faça um commit alterando código, sem task."
Correção nos commits `2620c98` (spec 1.9, `D-008`), `1e3b66e` (T-027), `153ac4a`
(hash) e `2d0dc9d` (spec 1.10, `D-009`).

**O que isso me ensinou sobre confiar em suíte verde:** teste automatizado
verifica o que alguém pensou em verificar. Aqui, todo mundo — eu inclusive —
tinha aceitado "a saída bate com o exemplo" como fato verificado, quando o que
estava verificado era "a saída bate com o exemplo depois que os dois passam por
um parser que normaliza justamente a diferença". A lição prática que ficou é que
o artefato entregue precisa ser olhado como o usuário final o recebe — texto,
arquivo, tela — pelo menos uma vez, por alguém, antes de o projeto se declarar
pronto. Passei a tratar "rodei e li a saída" como etapa obrigatória, não como
redundância do `pytest`.

### Caso 7 — escreveu na spec uma decisão que ninguém tomou

**O que ele propôs:** na primeira escrita da spec da v4, três afirmações sobre o
campo `vigencia` do arquivo de política. Em spec.md §3 ("Fora de escopo"): "Não
valida o campo `vigencia` da política contra o `periodo` da entrada". Na tabela de
spec.md §4 ("Entrada e saída"): o campo marcado como não validado. Em spec.md §10
("O que fica em aberto"): a mesma coisa registrada como limitação conhecida, com a
observação de que um lote de julho processado com uma política de agosto "seria
calculado sem nenhum aviso".

**Por que estava errado:** nenhuma linha do comunicado da v4 sustenta isso. Não foi
decisão minha nem leitura de um texto do RH — havia um campo no arquivo sem uso
óbvio, e ele foi declarado ignorado. O `CLAUDE.md` exige o caminho inverso: regra
que não está na spec deve ser trazida a mim antes de virar código. Aqui uma
não-regra entrou na spec sem passar por mim, e vinha com a limitação já escrita na
§10, o que a fazia parecer decisão ponderada.

**Como eu detectei:** li a spec antes de aprovar e perguntei quando a decisão tinha
sido tomada.

**O que eu fiz:** determinei que a validação é obrigatória, em duas verificações —
uma no lote e uma por despesa. Na conversa seguinte a segunda caiu: a verificação
por despesa que eu queria já era RN-006, que confere a `data` contra
`periodo.inicio` e `periodo.fim`; e o comunicado abre com "Vigência imediata,
retroativa à competência atual", ou seja, a retroatividade vai até o começo da
competência corrente e para ali — dentro da competência que o lote cobre não há
despesa a negar por vigência.

Ficou uma verificação só, **RN-017**, no lote inteiro. Ela recusa o lote quando
`periodo.competencia` é **anterior** à competência da `vigencia`: despesa antiga
tem que ser processada com a política que valia na época, e aplicar a política nova
a despesa velha é exatamente o que a regra existe para impedir. Quando
`periodo.competencia` é igual ou posterior, o lote é processado — um mês seguinte
pode não ter política nova, e a corrente continua valendo. Recusando, nada é
processado e nenhum arquivo de saída é escrito. As leituras descartadas ficaram em
AMB-020, e a origem do erro na **Nota de processo** de `DECISIONS.md` D-010.

**Onde está a evidência:** `docs/sessions/07_spec_2.0.txt`, linhas 969–970, minha
mensagem: "Quando essa decisão foi tomada? Você só assumiu isso. Inclusive essa
validação deve ser obrigatória."; RN-017 e AMB-020 em `spec.md`, entregues no commit
`511f47b`. O texto errado **nunca existiu em `main`**: o fluxo de aprovar antes de
commitar (`7367769`) pegou antes do primeiro commit da sessão.

### Caso 8 — parametrizou uma constante e me trouxe o problema inventado como decisão pendente

**O que ele propôs:** `moeda_base` descrito como parâmetro em quatro células de
spec.md §4 ("Entrada e saída") — o limite de cada categoria "na `moeda_base`", as
taxas em "unidades de `moeda_base`", os dois campos obrigatórios. E, em spec.md §10
("O que fica em aberto"), um item afirmando que o motor não verifica se as duas
`moeda_base` são a mesma, que isso "produziria conversões erradas em silêncio", e
que "basta uma decisão para virar RN-018".

**Por que estava errado:** o comunicado diz "Os limites da política são **sempre** em
BRL" e "quando ausente, assume-se `BRL`". As duas frases são categóricas — o BRL é
constante da política, não configuração do arquivo. A spec já se contradizia sozinha
nisso: o campo que ela mesma define como saída de RN-015 se chama
`valor_convertido_brl`, com a moeda no nome. Tendo parametrizado o que era
constante, ele criou um ponto de decisão que não existe e me apresentou esse ponto
como pendência minha.

**Como eu detectei:** li o item da §10 e não reconheci o problema que ele descrevia.
A política não fala em `moeda_base` em lugar nenhum, só em BRL.

**O que eu fiz:** disse que não havia problema a resolver, porque a política não
fala em `moeda_base` em lugar nenhum — só em BRL. A correção seguiu daí: as quatro
células passaram a dizer "em BRL" e a marcar o campo como não lido pelo motor, e o
item da §10 saiu. Um arquivo com
`moeda_base` divergente passou a ser tratado como entrada malformada, que já estava
fora de escopo desde o `plan.md` §1 ("Stack"). Spec 2.1, registrada em
`DECISIONS.md` D-012.

**Onde está a evidência:** `docs/sessions/07_spec_2.0.txt`, linha 1387, minha
mensagem: "o motor nao deve verificar isso pois a politica não é explicita sobre o
campo moeda base da politica, só fala que Os limites da política são sempre em BRL".
Diferente do Caso 7, este **chegou ao `git`**: entrou em `511f47b` e só saiu em
`6b5d425`.

### Caso 9 — a CLI escolhia a política sozinha, e o relatório saía sem dizer qual

**O que ele propôs:** a T-032 fez `--politica` e `--cambio` **opcionais, com
default**, para que a invocação fixa do `DESAFIO.md` continuasse funcionando sem
elas. A T-049 documentou isso no `README.md` como recurso: "os outros dois têm
caminho padrão e só precisam ser informados quando você quiser usar outros".

**Por que estava errado:** `calcular --input despesas.json --output resultado.json`
rodava, escrevia `resultado.json` e saía com código zero — julgando o lote com
`exemplos/envelope/politica-v4.json`, escolhida por omissão e por caminho absoluto
resolvido a partir da pasta do pacote. A spec.md §4 ("Entrada e saída") já dizia o
contrário em duas frases: "O motor recebe **três entradas**" e "As **três** entradas
são obrigatórias". Não era detalhe de ergonomia: o mesmo almoço de R$130,00 é
reembolso total num centro de custo e parcial em outro, então um `resultado.json`
cuja política não é rastreável a partir do comando que o gerou não é conferível por
quem recebe.

**Como eu detectei:** li a seção "Como rodar" do `README.md`, rodei o comando, e
perguntei qual política ele tinha usado e como tinha lidado com câmbio.

**O que eu fiz:** determinei que os três arquivos são obrigatórios. Virou a T-050 —
`required=True` nas duas flags, constantes de caminho padrão removidas, e dois testes
novos: um exige as duas flags, outro retira cada uma das três entradas, uma por vez, e
confirma código 2 sem arquivo escrito. Nem `spec.md` nem `plan.md` mudaram, porque foi
o código que se alinhou ao que a spec já dizia. Aprovei a divergência da linha fixa do
`DESAFIO.md` porque ela foi escrita quando o motor tinha uma entrada só, e o envelope
do Dia 2 acrescentou duas.

**Onde está a evidência:** `docs/sessions/08_tasks_implement_2.0.txt`, linha 2436,
minha mensagem: "o problema do comando no readme em 'Como roda' é a falta do input do
arquivo da politica e de cambio. (...) Esses arquivos deveriam ser obrigatórios no
input."; a aprovação da divergência na linha 2566. Correção nos commits `5dabd11`
(T-050) e `12676ba` (`CLAUDE.md`).

**Padrão que eu notei:** o Claude segue regras de conteúdo (o que a spec deve
dizer) com mais disciplina do que regras de processo sobre o próprio ato de
commitar (versionar, registrar). Mudanças que "parecem pequenas" no conteúdo
são exatamente onde ele relaxa a disciplina de processo — o que é o oposto do
que deveria acontecer, já que é justamente aí que ninguém mais vai notar sem
uma auditoria explícita do `DECISIONS.md`. Passei a conferir esse arquivo
sempre que uma sessão mexe em `spec.md`, mesmo quando a mudança parece
cosmética.

É perceptivel que o Claude comete erros, as vezes repetidos, e que sempre que você aponta um erro, ele revisa, e muitas vezes, encontra mais problemas/inconsistencias.

**O padrão que a fase de implementação acrescentou:** ele é muito melhor em
seguir a spec do que em desconfiar dela. Nos Casos 3 e 4, e também nas
correções que viraram D-005 e D-006, o erro não foi contrariar o que estava
escrito — foi seguir fielmente um texto ambíguo ou incompleto sem sinalizar a
ambiguidade.

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

**Na implementação, o procedimento mudou de forma.** Comecei com o fluxo original do `CLAUDE.md` ("commit primeiro, eu reviso depois"). Depois de 6 tasks percebi o efeito colateral: todo ajuste virava um commit de correção empilhado sobre um commit que já
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
e que eu confiei no código em si mais do que na interpretação.

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
campo mostrar o placeholder. As 50 tasks terminaram com hash real — foi conferido com
`grep -c '^  - \*\*Commit:\*\*$'`, que dá zero.

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
Os 125 foram escritos pelo Claude. E a resposta honesta para a segunda parte é:
**Revisei todos os testes e asserts feitos pelo claude — e tenho prova disso nesta sessão.** O teste de hospedagem do Caso 3 estava verde, tinha nome descritivo, e afirmava o
comportamento errado com confiança. Um teste escrito pelo mesmo agente que interpretou a regra é uma repetição da interpretação dele, não uma verificação dela.

O que reduziu o risco, na prática, foram três coisas:

1. **Revisar a regra.** Foi o que pegou o Caso 3. O teste parecia ótimo; o que não fechava era a validação que ele afirmava.
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

O que hoje me dá mais confiança não é a contagem de 125, é o teste de integração
que roda a **CLI de verdade** (arquivo de entrada → arquivo de saída) e compara
o resultado inteiro com `exemplos/resultado-exemplo.json`, que eu preenchi à
mão a partir das minhas decisões.

**Pedi massa de dados própria, e ela achou o que os exemplos não achavam.** Ao fim
da Fase 5 mandei revisar o código e criar dados sintéticos
(`docs/sessions/08_tasks_implement_2.0.txt`, linha 1439). Saíram 12 arquivos JSON em
`tests/dados/`, sem nenhum número em comum com `exemplos/`: outros centros de custo,
teto de nota fiscal de R$150,00, moedas `JPY` e `GBP`, competência `2026-09`. Onze
testes passaram de primeira. O décimo segundo não: `"valor": 100` — número JSON
válido, e a spec.md §4 ("Entrada e saída") tipa o campo como "número" sem exigir
casas decimais — abortava o motor com `AttributeError`, porque `parse_float=Decimal`
não é consultado para inteiros e todo arquivo de `exemplos/` traz os valores com duas
casas. Virou a T-047 (`d2e588d`), e a correção fechou as três bordas de leitura, não
só a que quebrava. A mesma revisão apontou que a identidade de duplicata comparava o
valor já truncado, então `33.333` e `33.334` viravam o mesmo lançamento — eu decidi
que a comparação é sobre o valor lançado (linha 1584) e virou a T-048 (`2e7af32`).

**Pedi auditoria ao próprio agente, e isso rendeu.** Junto com a correção do Caso 7,
mandei procurar mais decisões tomadas sem minha aprovação
(`docs/sessions/07_spec_2.0.txt`, linha 976). Vieram **15** além daquela (linha 991),
agrupadas pelo próprio Claude em quatro tipos: campos declarados ignorados por conta
própria, contrato de saída alterado sozinho, ambiguidades listadas como "encontradas"
e decididas sem perguntar, e falhas de processo. O resultado honesto é que **13
continuaram exatamente como estavam** — a auditoria não reverteu decisões, tornou-as
visíveis para eu decidir sobre elas. Duas mudaram: `moeda_base`, que virou o Caso 8;
e a linha "Vigência imediata, retroativa à competência atual", que tinha ficado de
fora de `exemplos/rh_politica_v4.md` quando o Claude extraiu o comunicado do RH — ela
é a evidência que sustenta AMB-020, e entrou no commit `a5d6889`.

---

## O envelope

*A mudança de requisito do Dia 2.*

**Quantos arquivos toquei na mão:** 

`1` — `specs/001-motor-reembolso/DECISIONS.md`,
onde removi um parágrafo do **Por quê** de D-012. Escrito pelo Claude e achei confuso e sem necessidade.

`2` — `docs/RELATORIO.md`,
Exclui alguns trechos de texto pois estava muito longo, e escrevi algumas coisas que percebi que faltaram.

`3` — `specs/001-motor-reembolso/tasks.md`,
onde removi o campo **Custo declarado** que o Claude tinha escrito na T-050
(`docs/sessions/08_tasks_implement_2.0.txt`, linha 2623).


**Quanto tempo levou:** 2 dias. Os commits vão de `19/08 21:10` (`a5d6889`) a
`21/08 15:08` (`12676ba`), em quatro janelas de trabalho — duas de spec e duas de
implementação.

**Diff de absorção:** `49 arquivos, +7724/−742 linhas`
(`git diff 10170c9 12676ba --stat`), em 67 commits. Os 49 são arquivos **distintos** —
não a soma das fases. Por fase:

| Fase | Commits | Diff | `src/` e `tests/` |
|---|---|---|---|
| Spec (`a5d6889`..`709031b`) | 8 | `10 arquivos, +1840/−179` | **zero** |
| Exports e relatório (`709031b`..`3524a9c`) | 3 | `2 arquivos, +2293/−17` | **zero** |
| Implementação (`3524a9c`..`12676ba`) | 56 | `41 arquivos, +3687/−642` | `34 arquivos, +3171/−508` |

As três linhas somam 53 arquivos e o total é 49 porque `spec.md`, `plan.md`, `tasks.md` e
`DECISIONS.md` aparecem em mais de uma fase e contam uma vez só
(`git diff 10170c9 12676ba --name-only | wc -l`).

A `spec.md` respondeu por `+863/−127` da fase de spec
(`git diff 10170c9 709031b --numstat`), saindo de 649 para 1385 linhas. Na fase de
implementação ela mudou uma vez só, para 2.4, e por um motivo que não era de regra
(RN-017 dizia "antes de qualquer despesa ser **lida**", uma ordem impossível porque a
competência do lote vem de dentro do arquivo de despesas — `DECISIONS.md` D-015,
commit `3b7055b`).

**Absorveu de graça:** três apostas do `plan.md`, registradas com o que cada uma
rendeu na tabela de `plan.md` §7 ("Riscos"), reescrita para deixar de ser previsão.
DT-001 (a ordem das regras como lista explícita de filtros em `motor.py`): o passo
novo de câmbio entra na posição 5 editando uma sequência num lugar só, e a spec.md
§8 ("Ordem de aplicação das regras") foi de 6 para 7 passos sem que `parser.py`,
`saida.py` ou `cli.py` soubessem. DT-002 e DT-005 (tratamento de dado na borda de
entrada): o campo `moeda` e a conversão para BRL entraram pelo caminho já aberto
pelo truncamento e pela normalização de categoria, sem tocar em `regras.py` —
virou DT-007. O `Decimal` do parse à escrita: limite vindo de arquivo e
multiplicação por taxa entraram pelo mesmo `parse_float`, sem nenhum ponto novo de
conversão.

**Resistiu:** duas coisas, e a primeira era uma decisão explícita.
`plan.md` §4 ("Como a política é representada"), na versão 1.9, decidia *"constantes
em código, não config externo (JSON/YAML carregado em runtime). Nada na spec pede
reconfiguração sem redeploy"*. O item A do comunicado revogou isso em uma frase — "o
motor precisa ler a política de fora, não de dentro do código". A justificativa
original não estava mal raciocinada; a premissa é que era falsa, e só o envelope
mostrou isso. A seção foi reescrita mantendo o texto antigo **citado, não apagado**
(commit `059a078`), e a mudança atravessa `politica.py` inteiro, mais parâmetro novo
em `regras.py` e `motor.py` e entrada nova em `cli.py` — dimensionada em T-028 a
T-032. A segunda: `exemplos/resultado-exemplo.json` precisa ser regravado por
inteiro (T-043), porque o colaborador do exemplo é de um centro de custo cujos
limites mudaram. Nenhuma decisão de arquitetura teria evitado essa, porque é dado,
não estrutura.

**Ordem em que fiz:** `spec` → `DECISIONS.md` → `plan.md` → `tasks.md` → código. Os timestamps
provam sem depender da minha palavra: os 8 commits da absorção são todos `docs(...)`
e nenhum toca `src/` ou `tests/`. A `spec.md` foi de 1.10 a 2.2 em três movimentos
(`511f47b`, `6b5d425`, `6f9ee47`), cada um com bump de versão e entrada em
`DECISIONS.md` (D-010 a D-013), e o `plan.md` acompanhou em commits próprios
(`059a078`, `711b7e9`, `709031b`). As 18 tasks novas (T-028 a T-045) foram escritas
antes de qualquer implementação, com numeração continuando de T-027.

**Se eu tivesse escrito a spec original sabendo desta mudança:** duas coisas
mudariam, e as duas estão localizadas. A política seria entrada desde a v3 — o
`plan.md` §4 não teria decidido por constantes, e RN-001, RN-002 e RN-003 teriam
nascido apontando para uma tabela em vez de trazer R$60,00, R$80,00 e R$250,00
escritos no texto da regra. E `exemplos/despesas-exemplo.json` não seria de um único
centro de custo: um exemplo com dois colaboradores teria feito a variação de limite
aparecer como pergunta no Dia 1, em vez de aparecer como reescrita do golden file no
Dia 2. O que **não** mudaria é a estrutura de decisão — AMB-005 (não inferir viagem)
foi decidida na v3 e sustentou sozinha a AMB-014 da v4, sem precisar ser revista.

**O que a spec me poupou, em concreto:** o caso mais claro é o
`exemplos/despesas-exemplo.json`. Ele é de `CC-ENG-PLATAFORMA`, que na v4 passa a ter
alimentação de R$75,00 (era R$60,00) e `hospedagem` com limite `0.00`. Reler os
critérios de aceite da spec.md §9 ("Critérios de aceite") contra a tabela nova
mostrou, **antes de rodar uma linha de código**, que `d-001` vai de R$60,00 (parcial)
para R$72,50 (total), `d-002` de R$0,00 para R$2,50, `d-010` de R$250,00 para R$0,00,
`d-013` troca de motivo de negação — de nota fiscal ausente para categoria não
reembolsável, porque RN-008 é o passo 2 da ordem e RN-005 é o passo 6 — e
`valor_total_reembolsavel` cai de R$585,43 para R$351,43, enquanto
`valor_total_despesas` sobrevive em R$1.806,94 por não depender de limite. Sem a §9
escrita como lista de valores esperados, isso apareceria como suíte vermelha no meio
da implementação, sem ninguém saber se o número novo era o certo.

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?**

Para este, e o ganho foi **velocidade** — não só em escrever código. Foi rápido cruzar
os 9 itens da política do RH com os 14 registros de `exemplos/despesas-exemplo.json` e
levantar as 20 ambiguidades (AMB-001 a AMB-020), rápido escrever as 1396 linhas de
`spec.md`, as 518 de `tasks.md` e os 125 testes. A absorção do envelope inteira — spec
nova, 23 tasks e a implementação — levou 2 dias, de `19/08 21:10` (`a5d6889`) a
`21/08 15:08` (`12676ba`), em 67 commits.

O que sobrou para mim foi revisar e decidir, e foi aí que meu tempo foi. As 20 decisões
de ambiguidade foram todas minhas, e os 9 casos de Discernimento saíram de leitura
minha — spec, task, `DECISIONS.md`, saída do programa —, nenhum de teste vermelho.

**Para qual não valeria?**

**Não tenho evidência para responder isso pelo tipo de projeto.**
Mas deixo registrado que facilitou muito para implementar a nova poltica, mesmo precisando alterar parte significativa do projeto, e o lado bom é que fica tudo documentado e versionado.

**O que eu faria diferente:**

- **Escrever eu mesmo o teste da regra que eu desambiguei.** O critério de aceite é o
  contrato da minha decisão; deixar o mesmo agente que interpretou a regra escrever o
  teste dela transforma o teste em repetição da interpretação (Caso 3).

- **Tentaria usar subagentes, skills, hooks** Acredito que não utilizar essas ferramentas adicionais acabei perdendo grandes beneficios que eles podem trazer aplicados junto com SDD.


**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**

Que o método depende inteiramente de uma coisa que cansa: **ler texto**. A `spec.md`
tem 1396 linhas, o `DECISIONS.md` 1060, a `tasks.md` 518. Revisar isso sessão após
sessão é maçante — não é difícil, é demorado, e em alguns momentos foi a parte mais chata
do desafio.

O desconfortável é que esse cansaço tem consequência. A T-032 dizia "flags
**opcionais** `--politica` e `--cambio`, com default", contradizendo uma frase da
spec.md §4 ("Entrada e saída") que eu mesmo tinha aprovado: "As **três** entradas são
obrigatórias". Eu li a Fase 5 antes de mandar implementar
(`docs/sessions/08_tasks_implement_2.0.txt`, linha 6) e passou. O defeito entrou pela
parte que eu revisei com menos energia, e só apareceu duas fases depois, quando li o
`README.md` (Caso 9).
