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
- Toda vez que `spec.md` mudar de versão, checar o campo `**Baseado na
  spec:**` no cabeçalho de `plan.md` e atualizá-lo para a nova versão. Esse
  ponteiro nunca deve ficar referenciando uma versão de spec mais antiga que
  a atual — se o `plan.md` ainda não foi revisado contra o que mudou, isso
  também precisa ficar registrado (não apenas o número da versão).

## Stack e comandos

- Linguagem: Python 3.12.3
- Rodar: `python -m src.cli calcular --input despesas.json --output resultado.json`
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
