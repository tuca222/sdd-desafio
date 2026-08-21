# Motor de Cálculo de Reembolso

CLI que lê um JSON com as despesas de um colaborador num período de competência e
escreve um JSON dizendo **quanto de cada despesa é reembolsável e por quê**.

Cada despesa da saída carrega uma justificativa em português citando a regra que
decidiu o caso — a ideia é que alguém do financeiro consiga conferir a decisão sem
abrir o código.

---

## Como rodar

O motor usa **apenas a biblioteca padrão do Python**. Não há nada para instalar:

```bash
python3 -m src.cli calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

**Requisito:** Python 3.12 ou superior (`python3 --version`).

O arquivo de entrada não é alterado. Para usar suas próprias despesas, aponte
`--input` para um arquivo no mesmo formato de
[`exemplos/despesas-exemplo.json`](exemplos/despesas-exemplo.json).

### As três entradas

O motor lê **três** arquivos. Só o de despesas é obrigatório na linha de comando;
os outros dois têm caminho padrão e só precisam ser informados quando você quiser
usar outros:

| Entrada | Flag | Padrão | O que traz |
|---|---|---|---|
| Despesas | `--input` | — (obrigatório) | O lote de um colaborador num período de competência |
| Política | `--politica` | `exemplos/envelope/politica-v4.json` | Os limites por centro de custo e os parâmetros gerais |
| Câmbio | `--cambio` | `exemplos/envelope/cambio.json` | As taxas de conversão para BRL, por data e por moeda |

```bash
python3 -m src.cli calcular \
  --input exemplos/envelope/despesas-envelope.json \
  --output resultado.json \
  --politica exemplos/envelope/politica-v4.json \
  --cambio exemplos/envelope/cambio.json
```

**A política é entrada, não código.** Os limites variam por centro de custo e são
mantidos pelo financeiro fora do repositório — trocar a tabela de limites não pode
exigir uma versão nova do motor. Editar
[`exemplos/envelope/politica-v4.json`](exemplos/envelope/politica-v4.json) e rodar
de novo é o fluxo esperado.

## Como testar

Os testes precisam do `pytest`, que não vem com o Python. Em muitas distribuições o
Python do sistema é *externally managed* e recusa instalação direta, então use um
ambiente virtual:

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install --group dev

.venv/bin/pytest -v
```

As versões de `pytest` e `ruff` vêm do grupo `dev` do
[`pyproject.toml`](pyproject.toml). O `--upgrade pip` não é decorativo: um venv novo
costuma vir com pip 24, e a flag `--group` só existe a partir do pip 25.1.

Lint e formatação:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format .
```

## O que o motor decide

| Regra | Comportamento |
|---|---|
| Limites diários | Vêm do arquivo de política e **variam por centro de custo**. O limite é por categoria e por dia, somando todas as despesas daquela categoria naquela data |
| Centro de custo sem entrada própria | Usa o bloco `padrao` da política, **integralmente**. Um centro de custo que tem entrada própria não é complementado pelo `padrao` em categoria nenhuma |
| Acima do limite | Reembolsa o que resta do limite do dia e corta o excedente (reembolso parcial) |
| Categoria não reembolsável | Negada integralmente, em dois casos com justificativas distintas: a categoria não consta na tabela do centro de custo, ou consta com `limite` igual a `0.00` (proibição explícita) |
| Nota fiscal | Obrigatória acima do teto da política (`nota_fiscal_obrigatoria_acima_de`), **estritamente**: o valor exato do teto dispensa. O teto é único para a empresa e é comparado contra o valor **em BRL** |
| Moeda estrangeira | Convertida para BRL pela taxa **da data da despesa**. Sem o campo `moeda`, assume-se `BRL`. Todos os limites são aplicados sobre o valor convertido |
| Sem cotação na data | Despesa negada. Não se usa a taxa de outro dia, nem média, nem a mais próxima — e ela não consome limite nem entra no total de despesas |
| Vigência da política | Se a competência da `vigencia` for **posterior** à do lote, nada é processado: nenhum arquivo de saída é escrito e o motor encerra com código diferente de zero |
| Período de competência | Data fora do intervalo `inicio`–`fim` (inclusivo nos dois extremos) é negada |
| Duplicatas | Despesas idênticas em tudo menos o `id` contam uma vez só — e a repetida não entra no total de despesas. `moeda` entra na comparação, e o valor comparado é o **lançado** |
| Valores negativos | Estornos são ignorados e não entram em nenhum total |
| Valores com mais de 2 casas | Truncados (não arredondados) antes de qualquer cálculo — o valor lançado e, quando há conversão, também o valor convertido |
| Escala da saída | O que o motor produz sai com exatamente 2 casas (`60.00`); o que é ecoado da entrada sai com a escala lançada |

A ordem em que essas verificações se aplicam importa, e está definida em
`specs/001-motor-reembolso/spec.md` §8 ("Ordem de aplicação das regras"). Cada despesa
recebe **uma única** justificativa: a da primeira regra que a reprovar. Como o limite
passou a variar por centro de custo, toda justificativa que cite um limite diário cita
também o centro de custo a que ele pertence.

**Três sutilezas da saída**, todas propositais:

- `categoria`, `valor` e `moeda` saem **exatamente como entraram** (`ALIMENTACAO`,
  `33.333`, `72.50` — com a escala lançada, não `72.5`), mesmo que internamente o
  motor use a categoria normalizada e o valor truncado para decidir. O relatório
  precisa bater com o comprovante anexado. "Exatamente como entrou" inclui **não ter
  entrado**: despesa sem o campo `moeda` sai sem ele, e não com um `"BRL"` inventado.
- Tudo que o motor **produz** (`valor_reembolsavel` e os dois totais) é derivado do
  valor truncado e sai com exatamente 2 casas decimais, inclusive quando a última é
  zero: `60.00`, nunca `60.0`.
- `taxa_cambio` e `valor_convertido_brl` tornam a conta refazível — `valor` ×
  `taxa_cambio` = `valor_convertido_brl`, e é sobre esse último que os limites são
  aplicados. Os dois saem `null` quando a despesa já está em BRL e quando não havia
  taxa disponível.

## Estrutura

```
src/
  cli.py        # subcomando `calcular`, orquestra as etapas e a guarda de vigência
  parser.py     # lê o JSON; trunca, normaliza e converte para BRL na entrada
  cambio.py     # carrega as taxas e responde taxa(moeda, data)
  politica.py   # carrega a política e resolve a tabela do centro de custo
  modelos.py    # dataclasses imutáveis que trafegam entre as etapas
  regras.py     # uma função pura por regra de negócio, sem estado e sem I/O
  motor.py      # aplica as regras na ordem da spec e calcula os totais
  saida.py      # monta o dict de saída, com os valores ainda em Decimal
tests/          # espelha src/, mais casos de borda e integração ponta a ponta
  dados/        # massa sintética: outra política, outro câmbio, oito lotes
exemplos/
  despesas-exemplo.json     # o lote do enunciado
  resultado-exemplo.json    # a saída esperada para ele
  envelope/                 # política v4, câmbio e os lotes do segundo dia
specs/001-motor-reembolso/
  spec.md       # o QUÊ e o PORQUÊ — regras, ambiguidades resolvidas, critérios
  plan.md       # o COMO — stack, arquitetura, decisões técnicas
  tasks.md      # T-001..T-049, cada uma com critério de aceite e commit
  DECISIONS.md  # log de toda mudança de spec, com o gatilho e o custo
docs/
  RELATORIO.md  # o relatório final
  sessions/     # exports das sessões de trabalho
```

Valores monetários usam `decimal.Decimal` de ponta a ponta e **nunca** viram `float`:
os três arquivos de entrada são lidos com `parse_float=Decimal` e `parse_int=Decimal`,
e `cli.py` serializa o `Decimal` como número JSON com um encoder próprio. A razão está
em `specs/001-motor-reembolso/plan.md` DT-004 ("Serialização de `Decimal` na saída") —
`float` não carrega escala, e `R$60,00` virava `60.0` na saída.

## Limitações conhecidas

Estão todas registradas em `specs/001-motor-reembolso/spec.md` §10 ("O que fica em
aberto"), com a razão de cada uma. As de maior impacto:

- **Cotação de dia não útil.** O arquivo de câmbio só publica em dia útil bancário, e
  toda despesa internacional lançada num dia sem cotação é negada. A prática de
  mercado é usar a cotação do último dia útil anterior; implementá-la exigiria
  escolher sozinho qual data usar e quantos dias aceitar voltar, decisões que a
  política não sustenta hoje. É o item mais provável de ser revisto.
- **Adicional de viagem.** A política prevê limites 50% maiores para colaborador em
  viagem, mas a entrada não tem campo que identifique viagem. O adicional não é
  aplicado em nenhuma circunstância — nem para despesa em moeda estrangeira, que não
  caracteriza viagem por si só.
- **Hospedagem por noite.** O limite de hospedagem é aplicado **por dia**, não por
  noite, porque o número de noites só aparece em texto livre na descrição
  (`"Hotel Rio - 2 diarias"`). Isso é mais restritivo do que a política provavelmente
  pretende em estadias de várias noites.
- **Centro de custo com tabela incompleta.** Como a tabela de um centro de custo que
  existe é fechada, um centro de custo cadastrado com uma categoria faltando nega
  despesa legítima até alguém corrigir o arquivo de política.
- **Fim de vigência.** A política tem data de início e não tem data de fim, então uma
  política revogada continua sendo aceita indefinidamente — o motor não tem como saber
  que ela foi substituída.
