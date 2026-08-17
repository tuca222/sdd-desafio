# Relatório — Desafio SDD

**Aluno:** `<nome>` · **Repositório:** `<link>` · **Data:** `<data>`

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
| Desenhar a arquitetura | — | Ainda não realizado — próxima etapa (`plan.md`), fora do escopo desta sessão. |
| Implementar | — | Ainda não realizado. |
| Escrever testes | — | Ainda não realizado. |
| Absorver o envelope | — | Ainda não realizado — só ocorre no Dia 2. |

**Onde deleguei e me arrependi:** Até agora, nenhum arrependimento — na fase de
spec, tudo que delegou (levantamento das ambiguidades, primeira versão do
`spec.md`) passou por revisão minha antes de virar decisão. Vou reavaliar
conforme o projeto avançar para implementação e testes.

**Onde não deleguei e deveria ter delegado:** Preenchi à mão o
`exemplos/resultado-exemplo.json` completo depois de fechar as
decisões. O cálculo dos totais eu faria de novo do mesmo jeito — foi
proposital, servindo de conferência cruzada independente do que o Claude
calculou (foi assim que peguei o erro do `valor_total_despesas`, ver
Discernimento). Mas preencher o `resultado-exemplo.json` inteiro à mão eu
poderia ter delegado: pedir para o Claude gerar o rascunho a partir da spec já
fechada e eu só validar linha a linha seria mais rápido do que escrever os 14
objetos `motor_reembolso_output` eu mesmo.

**Usei subagentes / skills / MCP / hooks?** Não. Toda a análise e a escrita da
spec foram feitas na conversa principal — leitura direta dos arquivos de exemplo
e perguntas estruturadas ao usuário (uma por ambiguidade, com opções de
interpretação) para cada decisão de negócio. Não valeria a pena paralelizar em
subagentes aqui: o gargalo não era pesquisa, era decisão humana sequencial —
cada ambiguidade só podia ser resolvida depois que a anterior estava fechada,
e só o usuário podia decidir.

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
histórico da conversa, exportado em `docs/sessions/planejamento_spec.txt`.

---

## Discernimento

*Onde o Claude errou e você pegou.*

> **Sem um caso concreto e verificável, esta seção vale zero.** Não existe projeto
> de dois dias em que o modelo acertou tudo. A ausência do caso não prova que o
> modelo foi perfeito — prova que ninguém estava conferindo.

### Caso 1

**O que ele propôs:** na primeira versão completa da spec, o Claude calculou
manualmente os totais esperados para o arquivo de exemplo e propôs, no
critério de aceite (§9), `valor_total_despesas = R$1.861,84`.

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
descrição do campo em §4 e os critérios de aceite em §9.

**Onde está a evidência:** `docs/sessions/planejamento_spec.txt`, linha ~1242,
minha mensagem: "O valor de R$1.861,84 estava incorreto, o certo é R$1.806,94
pois quando há duplicatas, ela não deve entrar para o calculo do valor total
de despesas."; correção aplicada no commit `47f18f9`.

### Caso 2 *(opcional)*

**Padrão que eu notei:** <em que tipo de tarefa ele erra mais? teve um sinal
recorrente que passou a te deixar em alerta?>

---

## Diligência

*O que você verificou antes de aceitar.*

**Meu procedimento de verificação:** li a spec completa, linha a linha, depois
que o Claude entregou a primeira versão — e não só li: fui alterando
diretamente no arquivo tudo que achei confuso, incompleto ou que dava para
melhorar (cabeçalho, tabela de campos de entrada, exemplo de saída, e a
correção do total que virou o Caso 1 de Discernimento), em vez de só listar
pedidos de ajuste para o Claude aplicar.

**Li o diff inteiro em que porcentagem das entregas?** 100% — até agora só
existe uma entrega (a spec), e foi lida por completo, linha a linha.

**O que aceitei sem verificar direito, e o que me custou:** nada até agora,
além do que já está registrado no Caso 1 de Discernimento. *(Esta é a primeira
versão do relatório — vou revisitar esta resposta conforme o projeto avançar
para implementação e testes.)*

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?**
Ainda não se aplica — a fase de implementação e testes ainda não começou.

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
