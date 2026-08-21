## O projeto

Motor de cálculo de reembolso de despesas corporativas. CLI que lê um JSON de
despesas e emite um JSON com o valor reembolsável e a justificativa de cada item.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que eu pedi não está coberto por nenhuma task, me avise em vez de implementar.

## Modelo do agente

Para desenvolvimento de código — implementar uma task (`src/`, `tests/`), corrigir
bug, refatorar — usar o modelo **Claude Opus**. Para o resto (conversa, revisão de
documento, planejamento, ajuste de `CLAUDE.md`/`spec.md`/`plan.md`/`tasks.md`) o
modelo padrão da sessão serve normalmente.

Isso é uma preferência de sessão, não algo que o próprio agente consegue aplicar
sozinho a partir deste arquivo — a troca de modelo é uma ação do usuário (ex.:
`/model opus` no Claude Code). Se uma sessão que não está no Opus for começar a
implementar uma task, ela deve dizer isso ao usuário antes de escrever código, em
vez de simplesmente implementar no modelo errado sem avisar.

## Regras de trabalho

- Toda regra de negócio vive na spec, não no chat e não em comentário de código.
- Se eu te explicar uma regra que não está na spec, **pare e me diga isso** antes
  de escrever código. Isso é um bug de spec.
- Todo commit referencia uma task: `feat(T-003): <descrição>`.
  Mudanças de documentação: `docs(spec):`, `docs(plan):`, `docs(tasks):`, `docs(claude):`.
- Nenhuma regra de negócio entra sem teste.
- **Toda alteração em `spec.md` é atômica em três partes, no mesmo commit — nenhuma
  delas é opcional, nem para mudança pequena de citação/referência que não muda
  regra de negócio:**
  1. A mudança em si no conteúdo de `spec.md`.
  2. Incremento de **Versão** e atualização de **Status** no cabeçalho de
     `spec.md` (a linha `**Versão:** X.Y · **Status:** ... · **Última
     alteração:** ...`).
  3. Uma nova entrada em `specs/001-motor-reembolso/DECISIONS.md` (gatilho, o
     que mudou, por quê, o que invalidou, tasks afetadas, custo).

  Antes de considerar concluída qualquer edição em `spec.md`, confira os três
  itens acima explicitamente. "Só mexi numa referência, não numa regra" não
  dispensa nenhum dos três — commit que toca `spec.md` sem versão/status
  atualizados e sem entrada em `DECISIONS.md` está incompleto.
- **Formato de uma entrada em `DECISIONS.md`.** Toda entrada usa os mesmos
  campos, nesta ordem, com o título `## D-NNN — <resumo> · \`DD/MM/AAAA\``:
  **Gatilho** (o que expôs o problema, e quem/o quê detectou), **O que mudou
  na spec** (o conteúdo alterado, seção por seção), **Por quê** (a razão da
  escolha, incluindo a alternativa descartada e o efeito colateral que ela
  teria), **O que isso invalidou** (código, testes e exemplos que deixaram de
  valer), **Tasks afetadas** e **Custo**. Campos extras (ex.: **Fica em
  aberto**, **Nota de processo**) entram no fim, quando houver.
- **O campo `Custo` lista, nominalmente, todos os arquivos alterados** — de
  produção, de spec, de exemplo e de teste, sem exceção e sem agrupar. Nada de
  "5 arquivos (...) + teste" ou "3 arquivos de teste": cada caminho aparece
  escrito. **Não escreva a contagem** ("7 arquivos") junto da lista — o número
  desencontra da lista na primeira revisão e vira ruído; a lista já é a
  contagem. A fonte da verdade é o `git`: antes de escrever o campo, rode
  `git status --short` (mudança ainda não commitada) ou
  `git show --name-only --format="" <hash>...` (já commitada) e transcreva o
  que aparecer. Custo subcontado dá a impressão de que a mudança de spec foi
  mais barata do que foi, que é exatamente o oposto do que este arquivo existe
  para registrar.
- Toda vez que `spec.md` mudar de versão, checar o campo `**Baseado na
  spec:**` no cabeçalho de `plan.md` e atualizá-lo para a nova versão. Esse
  ponteiro nunca deve ficar referenciando uma versão de spec mais antiga que
  a atual — se o `plan.md` ainda não foi revisado contra o que mudou, isso
  também precisa ficar registrado (não apenas o número da versão).
- **Toda citação de seção carrega arquivo + número + título**, em qualquer
  documento do projeto (`spec.md`, `plan.md`, `tasks.md`, `DECISIONS.md`,
  `RELATORIO.md`, `CLAUDE.md`): `spec.md §9 ("Critérios de aceite")`, nunca
  só `§9` e nunca só `spec.md §9`. Vale inclusive quando a seção citada está
  no mesmo arquivo em que estou escrevendo — o leitor pode estar lendo um
  trecho isolado, sem saber em qual arquivo ele está.
  **Por quê:** `§9` sozinho só resolve para quem já tem o documento inteiro
  na cabeça, e quebra silenciosamente na primeira renumeração. Isso já foi um
  bug real aqui: a mesma notação `§4` no `plan.md` apontava ora para a
  `spec.md`, ora para o próprio `plan.md`, sem nada distinguindo os dois
  casos (ver `DECISIONS.md` D-001). O critério da `RUBRICA.md` para nota
  máxima em qualidade de spec é "um desenvolvedor que nunca viu o projeto
  implementaria a mesma coisa" — referência que exige contexto prévio
  carregado falha esse critério.
- **Disciplina de `tasks.md`:**
  - Marque `[x]` em cada task conforme ela é concluída — ao longo do caminho,
    nunca todas de uma vez no final. A correção lê o histórico de quando cada
    task foi marcada, não só o estado final do arquivo.
  - Toda task precisa ser pequena o bastante para virar **um commit**. Se o
    critério de aceite não dá pra descrever como "o teste X passa", a task
    está grande demais e precisa ser quebrada antes de ser implementada.
  - Qualquer agente que perceber uma task não marcada apesar de já concluída,
    ou uma task grande demais para um commit (critério de aceite vago, cobre
    mais de um teste/regra sem necessidade), **deve sinalizar isso
    imediatamente ao usuário e propor a correção** (marcar `[x]`, ou quebrar a
    task em tasks menores) antes de continuar o trabalho.
  - O campo **Commit** de cada task nunca fica com o placeholder `<hash
    preenchido depois>` além do momento em que a task é fechada. Como o
    hash só existe depois que o commit é criado, fechar uma task sempre
    exige dois commits em sequência — os dois só acontecem depois que eu
    aprovar a implementação (ver "Fluxo de git" → aprovação antes do
    commit):
    1. `feat(T-NNN):`/`test(T-NNN):` — a implementação, já com `[x]`
       marcado em `tasks.md` (o campo **Commit** ainda mostra o
       placeholder aqui — é inevitável).
    2. `docs(tasks): registra hash do commit da T-NNN` — pega o hash do
       commit anterior (`git log -1 --format=%h`) e troca o placeholder
       pelo hash real.
    O segundo commit é fechamento mecânico da mesma task já aprovada, não
    uma alteração nova — o agente cria os dois em sequência, sem pausar
    para aprovar de novo entre eles. Uma task não está encerrada — nem
    pronta para relatar ao usuário como concluída — enquanto o campo
    **Commit** ainda mostrar o placeholder. Nunca usar `git commit
    --amend` para resolver isso (proibido por regra geral de git deste
    ambiente); é sempre um commit novo.
- **`RELATORIO.md` é evidência, não redação.** Toda afirmação do relatório vem
  acompanhada de arquivo, hash de commit ou trecho de sessão exportada. Um
  parágrafo bonito sem evidência vale menos que uma frase curta com um hash.
  Este arquivo é o único lugar onde essa regra mora — o relatório não a repete
  como epígrafe, então não a reintroduza lá. Na prática:
  - **Toda afirmação carrega a evidência na própria frase:** caminho de
    arquivo, hash de commit, ou `docs/sessions/<arquivo>.txt` com o número da
    linha. Parágrafo que não cita nenhum dos três não entra, por mais correto
    que seja.
  - **Nada de parágrafo interpretativo.** Lição generalizada, moral da
    história, análise do que o episódio "ensina", reformulação com outras
    palavras do que já foi dito: é redação, corta. Quem lê tira a conclusão do
    fato citado — o que precisa estar no arquivo é o fato.
  - **Um caso de `RELATORIO.md` ("Discernimento") cabe em ~40 linhas**, com os
    cinco campos (**O que ele propôs**, **Por que estava errado**, **Como eu
    detectei**, **O que eu fiz**, **Onde está a evidência**) em um parágrafo
    curto cada. Não cabendo, o que sobra é quase sempre explicação, não prova.
  - Explicar o mecanismo técnico de um bug é trabalho do `DECISIONS.md`, da
    mensagem de commit e da sessão exportada — no relatório basta a conclusão
    e o ponteiro para onde está a explicação.
  - Antes de dar por pronta qualquer edição no relatório, releia parágrafo por
    parágrafo perguntando "que arquivo, hash ou linha de sessão isto cita?".
    Se a resposta for nenhum, o parágrafo sai.

  **Por quê:** o Caso 6 nasceu com 79 linhas contra 23 a 43 dos Casos 1 a 5, e
  quase todo o excedente era explicação do mecanismo do bug e uma conclusão
  sobre o valor de testar — nada disso é evidência, e tudo isso já estava no
  `git log` e na sessão exportada. A `RUBRICA.md` §4 ("Relatório e
  discernimento") vale 20 pontos e põe "relatório narrativo sem evidência" na
  faixa de 6–12, contra 18–20 para "commits citados, trechos de sessão
  referenciados": texto a mais não soma e dilui o que soma.

## Fluxo de git

Desafio individual de 2 dias — sem branch de feature, sem PR, sem processo de
merge. Todo trabalho, meu ou de um agente, é direto na `main`.

- **Nunca isolar em worktree neste projeto.** `.claude/settings.json` já tem
  `"worktree": {"bgIsolation": "none"}` — isso desliga, para este repositório,
  o isolamento automático que o harness aplicaria a sessões de agente em
  background. Nenhum agente deve chamar `EnterWorktree` aqui por conta
  própria (nem em sessão interativa, nem em background). Toda ação de agente
  — commit, edição, exclusão, criação de arquivo, e também `/export` de
  sessão para `docs/sessions/` — acontece direto no checkout local, na branch
  `main`, no diretório que eu já estou olhando.
  **Por quê:** um worktree isolado já causou dois problemas reais aqui — um
  `/export` de sessão foi gravar dentro do worktree em vez do repositório
  local (o arquivo não existia onde eu esperava até um push manual), e um
  commit meu no checkout principal divergiu de um commit do agente feito no
  worktree, exigindo merge manual pra reconciliar depois. Nenhum dos dois
  problemas existe se o agente nunca sai do checkout local.
- **Todo commit vai direto em `main`.** Nenhuma alteração deve ficar
  pendurada num branch separado esperando merge manual.
- **Toda alteração espera minha aprovação antes de virar commit.** Fluxo:
  o agente implementa (código, teste, doc) → eu reviso **sem nenhum commit
  novo no histórico ainda** → aprovo ou peço ajuste → só depois da minha
  aprovação o agente commita. Se eu pedir ajuste, o agente corrige e volta
  a aguardar aprovação antes de commitar — nunca commita "para já deixar
  registrado" e ajusta depois.
  **Por quê:** o modelo anterior (commit primeiro, revisão depois) sujava
  o histórico do `git log` toda vez que algo precisava de ajuste — ficavam
  commits que já nasciam errados, exigindo mais commits de correção em
  cima. Aprovar antes do commit mantém o histórico limpo: todo commit que
  existe já é o resultado final revisado, não um rascunho.
  **Única exceção:** o commit de registro de hash que fecha uma task
  (`docs(tasks): registra hash do commit da T-NNN`, mecânica descrita em
  "Disciplina de `tasks.md`", acima) não espera uma nova rodada de
  aprovação — é continuação mecânica da mesma task já aprovada.
- Isso não dispensa nenhuma outra regra deste arquivo (task referenciada no
  commit, `spec.md` atômica em três partes, etc.) — só define que o destino
  de todo commit é sempre `main`.
- **Todo commit feito por um agente leva assinatura no rodapé da mensagem:**
  `Co-Authored-By: <nome do modelo> <noreply@anthropic.com>` (ex.:
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`). É o que
  diferencia, no `git log`, o que foi commitado por mim do que foi gerado por
  um agente — sem essa linha, a distinção se perde. Nenhuma exceção, nem para
  commit pequeno de doc. Antes de criar qualquer commit, o agente confere se
  a mensagem já inclui a assinatura; se não incluir, é bug de processo, igual
  a esquecer o prefixo `docs(...)`/`feat(T-NNN)`.

## Stack e comandos

- Linguagem: Python 3.12.3
- Rodar — **as três entradas são obrigatórias** (`spec.md` §4, "Entrada e saída"):

  ```
  python -m src.cli calcular \
    --input despesas.json \
    --output resultado.json \
    --politica exemplos/envelope/politica-v4.json \
    --cambio exemplos/envelope/cambio.json
  ```

  Nenhuma das três tem valor padrão. Elas tiveram, entre a T-032 e a T-050, e o
  efeito era um `resultado.json` julgado por uma política que quem rodou não
  escolheu e não via — ver a T-050 em `tasks.md`. Isso difere da linha fixada em
  `DESAFIO.md` ("Interface (esta parte é fixa)"), que foi escrita quando o motor
  tinha uma entrada só; o envelope do dia 2 acrescentou duas, e o usuário aprovou
  a divergência.
- Testes: `pytest -v`
- Lint/format: `ruff check . && ruff format .`

## Convenções de código

- snake_case para funções e variáveis; type hints obrigatórios em funções públicas.
- Estrutura: `src/` com módulos separados por responsabilidade; `tests/` espelhando `src/`.
- Valores monetários: `decimal.Decimal`, nunca `float`. Cálculo financeiro com
  float acumula erro de arredondamento — decisão não negociável.

## Fora de escopo

- Sem persistência em banco de dados (entrada e saída são arquivos JSON).
- Sem API HTTP/autenticação.
- Sem interface gráfica.
