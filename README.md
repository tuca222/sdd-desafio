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
| Limites diários | R$60,00 alimentação · R$80,00 transporte urbano · R$250,00 hospedagem. O limite é **por categoria e por dia**, somando todas as despesas daquela categoria naquela data |
| Acima do limite | Reembolsa o que resta do limite do dia e corta o excedente (reembolso parcial) |
| Nota fiscal | Obrigatória para despesas **estritamente acima** de R$100,00. R$100,00 exatos dispensam |
| Período de competência | Data fora do intervalo `inicio`–`fim` (inclusivo nos dois extremos) é negada |
| Duplicatas | Despesas idênticas em tudo menos o `id` contam uma vez só — e a repetida não entra no total de despesas |
| Categoria fora da política | Negada integralmente |
| Valores negativos | Estornos são ignorados e não entram em nenhum total |
| Valores com mais de 2 casas | Truncados (não arredondados) antes de qualquer cálculo |

A ordem em que essas verificações se aplicam importa, e está definida em
`specs/001-motor-reembolso/spec.md` §8 ("Ordem de aplicação das regras"). Cada despesa
recebe **uma única** justificativa: a da primeira regra que a reprovar.

**Duas sutilezas da saída**, ambas propositais:

- `categoria` e `valor` saem **exatamente como entraram** (`ALIMENTACAO`, `33.333`),
  mesmo que internamente o motor use a categoria normalizada e o valor truncado para
  decidir. O relatório precisa bater com o comprovante anexado.
- Tudo que o motor **produz** (`valor_reembolsavel` e os dois totais) é derivado do
  valor truncado e nunca passa de 2 casas decimais.

## Estrutura

```
src/
  cli.py        # subcomando `calcular`, orquestra as etapas
  parser.py     # lê o JSON; trunca valores e normaliza categorias na entrada
  modelos.py    # dataclasses imutáveis que trafegam entre as etapas
  regras.py     # uma função pura por regra de negócio, sem estado e sem I/O
  motor.py      # aplica as regras na ordem da spec e calcula os totais
  saida.py      # monta o dict de saída; único ponto que converte Decimal → float
  politica.py   # os limites e as categorias válidas, em um lugar só
tests/          # espelha src/, mais casos de borda e integração ponta a ponta
specs/001-motor-reembolso/
  spec.md       # o QUÊ e o PORQUÊ — regras, ambiguidades resolvidas, critérios
  plan.md       # o COMO — stack, arquitetura, decisões técnicas
  tasks.md      # T-001..T-026, cada uma com critério de aceite e commit
  DECISIONS.md  # log de toda mudança de spec, com o gatilho e o custo
docs/
  RELATORIO.md  # o relatório final
  sessions/     # exports das sessões de trabalho
```

Valores monetários usam `decimal.Decimal` do início ao fim do cálculo — `float` só
aparece no momento de escrever o JSON.

## Limitações conhecidas

Duas coisas ficaram deliberadamente de fora, ambas por falta de dado estruturado na
entrada. Estão registradas em `specs/001-motor-reembolso/spec.md` §10 ("O que fica em
aberto"):

- **Adicional de viagem.** A política do RH prevê limites 50% maiores para
  colaborador em viagem, mas a entrada não tem campo que identifique viagem. O
  adicional não é aplicado em nenhuma circunstância — inferir viagem a partir de
  outro dado seria criar uma regra que ninguém pediu.
- **Hospedagem por noite.** O limite de R$250,00 é aplicado **por dia**, não por
  noite, porque o número de noites só aparece em texto livre na descrição
  (`"Hotel Rio - 2 diarias"`). Isso é mais restritivo do que a política provavelmente
  pretende em estadias de várias noites.
