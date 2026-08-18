# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.7 · **Status:** em implementação (Fase 2 — regras de negócio) · **Última alteração:** `18/08/2026`

---

## 1. Problema

Hoje o financeiro confere manualmente, item por item, se cada despesa lançada por um
colaborador respeita a política de reembolso — e devolve uma lista de aprovações e
recusas. É lento e sujeito a erro humano, especialmente em casos de borda (valores no
limite exato, despesas duplicadas, categorias fora da política).

## 2. Objetivo

Dado o conjunto de despesas de um colaborador num período de competência, o sistema
decide automaticamente quanto de cada despesa é reembolsável e produz uma justificativa
verificável para cada decisão, sem intervenção humana.

## 3. Fora de escopo

- Não persiste dados em banco — entrada e saída são arquivos JSON.
- Não expõe API HTTP nem faz autenticação.
- Não tem interface gráfica.
- Não aplica o adicional de 50% para colaborador "em viagem" —
  a entrada não tem campo que identifique viagem; ver RN-012, AMB-005 e §10 ("O que fica em aberto").
- Não infere o número de diárias de uma hospedagem a partir de texto livre na
  descrição — a entrada não tem campo estruturado para isso; ver RN-003, AMB-006 e §10 ("O que fica em aberto").
- Não solicita nem sugere correção de dado ao usuário — despesas com dado
  problemático (valor com casas decimais em excesso, valor negativo) são tratadas
  automaticamente conforme as regras desta spec, não rejeitadas como erro.
- Não altera nem persiste o arquivo de entrada.

## 4. Entrada e saída

**Entrada:** conforme `exemplos/despesas-exemplo.json`. Campos e significado:

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador` | objeto | Objeto com os dados do colaborador | Sim |
| `colaborador.id` | string | Identificador do colaborador | Sim |
| `colaborador.nome` | string | Nome do colaborador | Sim |
| `colaborador.centro_custo` | string | Centro de custo do colaborador | Sim |
| `periodo.competencia` | string (`AAAA-MM`) | Mês/ano de competência do lote de despesas | Sim |
| `periodo.inicio` | string (data) | Primeiro dia do período de competência | Sim |
| `periodo.fim` | string (data) | Último dia do período de competência | Sim |
| `despesas[]`  | array | Lista de despesas do colaborador lançadas naquele período. Cada elemento da lista é um objeto com os dados da despesa | Sim |
| `despesas[].id` | string | Identificador único da despesa | Sim |
| `despesas[].data` | string (AAAA-MM-DD) | Data em que a despesa ocorreu | Sim |
| `despesas[].categoria` | string | Categoria da despesa. É normalizada para minúsculas na leitura da entrada, antes de qualquer regra — ver RN-011 | Sim |
| `despesas[].descricao` | string | Descrição livre da despesa | Sim |
| `despesas[].fornecedor` | string | Fornecedor/estabelecimento | Sim |
| `despesas[].valor` | número | Valor da despesa em R$; pode ter mais de 2 casas decimais (ver RN-010) ou ser negativo (ver RN-009) | Sim |
| `despesas[].tem_nota_fiscal` | booleano | Se a despesa tem nota fiscal anexada | Sim |

**Saída:** definida por esta spec. Estrutura e significado de cada campo:

| Campo | Tipo | Significado |
|---|---|---|
| `colaborador` | objeto | Copiado da entrada, sem alteração |
| `periodo` | objeto | Copiado da entrada, sem alteração |
| `valor_total_despesas` | número | Soma do `valor` (já truncado, ver RN-010) de todas as despesas da entrada, **exceto** as ignoradas por valor negativo (RN-009) e as identificadas como duplicata (RN-007) |
| `valor_total_reembolsavel` | número | Soma do campo `valor_reembolsavel` de todas as despesas dentro de detalhamento_despesas |
| `detalhamento_despesas[]` | array | Lista com os mesmos objetos da lista `despesas` de entrada, na mesma ordem, com os mesmos campos originais, porém com a adição do objeto `motor_reembolso_output`. Ver abaixo o que "campos originais" significa |
| `detalhamento_despesas[].motor_reembolso_output` | objeto | Objeto com os dados de saída gerados pelo motor para cada despesa |
| `detalhamento_despesas[].motor_reembolso_output.despesa_reembolsavel` | booleano | `true` se `valor_reembolsavel > 0`. Ou seja, se reembolso parcial `despesa_reembolsavel == true`|
| `detalhamento_despesas[].motor_reembolso_output.tipo_reembolso` | string (`total`\|`parcial`\|`nenhum`) | Definição do tipo do reembolso. Sendo `total` se reembolsa o valor cheio, `parcial` se reembolsa apenas uma parte do valor da despesa, `nenhum` se nada é reembolsado |
| `detalhamento_despesas[].motor_reembolso_output.valor_reembolsavel` | número | Valor efetivamente reembolsável desta despesa |
| `detalhamento_despesas[].motor_reembolso_output.justificativa` | string | Explicação em português da decisão, citando a regra aplicada e, quando relevante, a despesa relacionada (ex.: duplicata, limite estourado por conta de outra despesa). Ver abaixo o formato obrigatório de referência a outra despesa |

**O que "campos originais" significa (obrigatório):** os campos que
`detalhamento_despesas[]` repete da entrada saem **exatamente como entraram**, mesmo
quando o motor usou internamente uma versão tratada deles para decidir. São dois os
casos em que entrada e uso interno divergem:

- `categoria` sai com a grafia exata que entrou (`ALIMENTACAO`), embora a decisão
  use a forma normalizada (RN-011).
- `valor` sai com o número exato que entrou (`33.333`), embora a decisão use o valor
  truncado em 2 casas (RN-010).

A regra geral é: **o valor tratado serve para calcular, o valor lançado serve para
exibir.** Tudo que o motor *produz* — `valor_reembolsavel`, `valor_total_despesas` e
`valor_total_reembolsavel` — é derivado do valor truncado e, portanto, sempre tem no
máximo 2 casas decimais. Só os campos ecoados da entrada podem ter mais.

O motivo é auditoria: o relatório precisa bater com o comprovante que o colaborador
anexou. Se `valor` saísse truncado, a linha exibiria R$33,33 para uma nota de
R$33,333, e quem confere veria uma divergência que o sistema criou sozinho.

**Formato de referência a outra despesa (obrigatório em toda a saída):** sempre que
uma `justificativa` citar outra despesa, a referência usa o formato
`descricao(id)` — ex.: `'Almoco com cliente(d-001)'`. Vale em qualquer regra, sem
exceção. A `descricao` sozinha é ambígua (duas despesas podem ter a mesma
descrição) e o `id` sozinho é ilegível para quem confere a decisão no financeiro;
os dois juntos são legíveis e verificáveis contra a entrada.

Exemplo pequeno:

Entrada:

```json
{
  "colaborador": {
    "id": "c-0417",
    "nome": "Marina Volpi",
    "centro_custo": "CC-ENG-PLATAFORMA"
  },
  "periodo": {
    "competencia": "2026-07",
    "inicio": "2026-07-01",
    "fim": "2026-07-31"
  },
  "despesas": [
    {
      "id": "d-001",
      "data": "2026-07-03",
      "categoria": "alimentacao",
      "descricao": "Almoco com cliente",
      "fornecedor": "Restaurante Tavola",
      "valor": 72.50,
      "tem_nota_fiscal": true
    },
    {
      "id": "d-002",
      "data": "2026-07-03",
      "categoria": "alimentacao",
      "descricao": "Jantar apos reuniao",
      "fornecedor": "Cantina do Porto",
      "valor": 38.00,
      "tem_nota_fiscal": true
    }
  ]
}
```

Saída:

```json
{
    "colaborador": {
        "id": "c-0417",
        "nome": "Marina Volpi",
        "centro_custo": "CC-ENG-PLATAFORMA"
    },
    "periodo": {
        "competencia": "2026-07",
        "inicio": "2026-07-01",
        "fim": "2026-07-31"
    },
    "valor_total_despesas": 110.50,
    "valor_total_reembolsavel": 60.00,
    "detalhamento_despesas": [
        {
            "id": "d-001",
            "data": "2026-07-03",
            "categoria": "alimentacao",
            "descricao": "Almoco com cliente",
            "fornecedor": "Restaurante Tavola",
            "valor": 72.50,
            "tem_nota_fiscal": true,
            "motor_reembolso_output": {
                "despesa_reembolsavel": true,
                "tipo_reembolso": "parcial",
                "valor_reembolsavel": 60.00,
                "justificativa": "A categoria alimentacao possui limite de reembolso de R$60,00 no dia. Reembolso parcial aprovado."
            }
        },
        {
            "id": "d-002",
            "data": "2026-07-03",
            "categoria": "alimentacao",
            "descricao": "Jantar apos reuniao",
            "fornecedor": "Cantina do Porto",
            "valor": 38.00,
            "tem_nota_fiscal": true,
            "motor_reembolso_output": {
                "despesa_reembolsavel": false,
                "tipo_reembolso": "nenhum",
                "valor_reembolsavel": 0.00,
                "justificativa": "A categoria alimentacao possui limite de reembolso de R$60,00 no dia. Este valor já foi atingido na despesa 'Almoco com cliente(d-001)'. Reembolso negado."
            }
        }
    ]
}
```

## 5. Regras de negócio

Cada regra recebe um ID (`RN-001`, ...). As tasks precisam referenciar esses IDs.

### RN-001 — Limite diário de alimentação

**Regra:** despesas de categoria `alimentacao` do mesmo dia são somadas, na ordem em
que aparecem na entrada; a soma é limitada a R$60,00/dia; a(s) primeira(s) despesa(s)
na ordem consomem o limite, as seguintes recebem R$0,00 quando o limite já foi atingido.
**Origem:** política do RH; desambiguado por AMB-001.
**Aceite:** com `d-001` (R$72,50) e `d-002` (R$38,00) no mesmo dia, `d-001` reembolsa
R$60,00 (parcial) e `d-002` reembolsa R$0,00 (nenhum).

### RN-002 — Limite diário de transporte urbano

**Regra:** mesma mecânica de RN-001, aplicada à categoria `transporte_urbano`, com
limite de R$80,00/dia.
**Origem:** política do RH; desambiguado por AMB-001.
**Aceite:** `d-003` (R$100,00, único sobrevivente às verificações anteriores no dia)
reembolsa R$80,00 (parcial).

### RN-003 — Limite diário de hospedagem

**Regra:** mesma mecânica de RN-001, aplicada à categoria `hospedagem`, com limite
de R$250,00/dia. Ou seja: todas as despesas de `hospedagem` de uma mesma `data` são
somadas na ordem em que aparecem na entrada e disputam **um único** limite de
R$250,00 daquele dia — a(s) primeira(s) consomem o limite, as seguintes recebem
R$0,00 quando ele já foi atingido.

O número de noites que um lançamento cobre **não entra na conta em nenhuma
hipótese**: a entrada não tem campo estruturado para isso e o sistema não extrai
essa informação do texto livre da `descricao` (ver AMB-006). Um lançamento que
cobre várias noites concorre ao limite de R$250,00 de **um único dia** — o da sua
`data` —, exatamente como um lançamento de uma noite só. O limite nunca é
multiplicado pelo número de noites, e também nunca é aplicado "por lançamento":
dois lançamentos de `hospedagem` no mesmo dia dividem os mesmos R$250,00.
**Origem:** política do RH; desambiguado por AMB-006.
**Aceite:** `d-010` (R$480,00, com nota fiscal, único lançamento de `hospedagem`
em `2026-07-14`) reembolsa R$250,00 (parcial). Duas hospedagens na mesma data, de
R$480,00 e R$300,00 nessa ordem, reembolsam R$250,00 (parcial) e R$0,00 (nenhum),
respectivamente.

### RN-004 — Reembolso parcial

**Regra:** quando uma despesa passa por todas as verificações de RN-005 a RN-009 (ou
seja, não foi negada por nenhuma delas) mas seu valor — somado ao de despesas
anteriores da mesma categoria e dia — excede o limite da categoria, reembolsa-se
exatamente o limite restante daquele dia/categoria; o excedente não é reembolsado.
**Origem:** política do RH; desambiguado por AMB-002.
**Aceite:** ver RN-001, RN-002 e RN-003.

### RN-005 — Nota fiscal obrigatória

**Regra:** despesas com `valor` estritamente maior que R$100,00 exigem
`tem_nota_fiscal = true`; se ausente, a despesa é negada integralmente
(`valor_reembolsavel = 0,00`), independentemente de haver ou não limite de categoria
disponível naquele dia. Despesas com `valor` igual a R$100,00 **não** exigem nota
fiscal.
**Origem:** política do RH; desambiguado por AMB-003 e AMB-004.
**Aceite:** `d-003` (R$100,00, sem nota fiscal) não é negado por este motivo; `d-004`
(R$100,01, sem nota fiscal, mesmo dia/categoria de `d-003` que já esgotou o limite
diário) é negado citando a nota fiscal ausente, não o limite diário.

### RN-006 — Período de competência

**Regra:** uma despesa só é elegível a reembolso se sua `data` estiver entre
`periodo.inicio` e `periodo.fim`, incluindo os dois extremos. Fora disso, é negada
integralmente.
**Origem:** política do RH; desambiguado por AMB-011.
**Aceite:** `d-008` (data `2026-04-15`, fora de `2026-07-01`–`2026-07-31`) é negado
citando o período de competência.

### RN-007 — Tratamento de duplicatas

**Regra:** duas despesas cujos campos `data`, `categoria`, `descricao`, `fornecedor`,
`valor` e `tem_nota_fiscal` são todos idênticos (o `id` é o único campo que pode
diferir) são consideradas o mesmo lançamento repetido. A comparação de `categoria`
usa a forma normalizada (RN-011): `ALIMENTACAO` e `alimentacao` são a mesma
categoria também aqui, então duas despesas que diferem só pela capitalização **são**
duplicatas. Apenas a primeira ocorrência
(pela ordem em que aparece na entrada) é avaliada normalmente pelas demais regras; as
ocorrências seguintes são negadas integralmente, com a justificativa citando a
despesa original (formato em `spec.md` §4, "Entrada e saída"). As
ocorrências negadas como duplicata também **não entram** em
`valor_total_despesas` — contá-las infla o total bruto de despesas do período com um
valor que nunca representou um gasto adicional real, apenas o mesmo lançamento
relatado mais de uma vez.
**Origem:** política do RH; desambiguado por AMB-007.
**Aceite:** `d-006` e `d-007` são idênticos em todos os campos exceto `id`; `d-006`
(primeiro na entrada) é avaliado normalmente; `d-007` é negado como duplicata de
`d-006` — justificativa citando `Almoco(d-006)` — e seu valor (R$54,90) não é somado
em `valor_total_despesas`.

### RN-008 — Categorias fora da política

**Regra:** despesas cuja categoria, normalizada para minúsculas (RN-011), não é
`alimentacao`, `transporte_urbano` nem `hospedagem`, são integralmente negadas.
**Origem:** política do RH.
**Aceite:** `d-005` (categoria `coworking`) é negado citando categoria fora da
política.

### RN-009 — Estornos e valores negativos

**Regra:** despesas com `valor` negativo são ignoradas: recebem
`valor_reembolsavel = 0,00`, `tipo_reembolso = "nenhum"`, e **não** entram na soma de
`valor_total_despesas` nem de `valor_total_reembolsavel` do período. Não consomem nem
liberam limite diário de nenhuma categoria.
**Origem:** dado de entrada; a política do RH não menciona valores negativos ou
estornos em nenhum item — desambiguado por AMB-008.
**Aceite:** `d-009` (valor `-45,00`) aparece em `detalhamento_despesas` com
`valor_reembolsavel = 0,00`, mas não é somado em `valor_total_despesas` nem em
`valor_total_reembolsavel`.

### RN-010 — Truncamento de valores com casas decimais em excesso

**Regra:** valores de despesa com mais de 2 casas decimais são truncados (não
arredondados) para 2 casas decimais antes de qualquer verificação de limite ou nota
fiscal.
**Origem:** dado de entrada; desambiguado por AMB-010.
**Aceite:** `d-011` (valor `33.333`) é tratado como R$33,33.

### RN-011 — Normalização de categoria

**Regra:** a `categoria` de cada despesa é normalizada para minúsculas **uma única
vez, na leitura da entrada**, antes de qualquer regra ser avaliada. Daí em diante,
toda regra desta spec — comparação com as categorias da política (RN-008),
agrupamento por categoria+dia para o limite diário (RN-001, RN-002, RN-003) e
comparação de campos para duplicata (RN-007) — enxerga apenas a forma normalizada.
Nenhuma regra normaliza por conta própria, e portanto nenhuma pode divergir das
outras nesse ponto.

A grafia original **não é descartada**: ela é preservada e devolvida sem alteração
no campo `categoria` de `detalhamento_despesas[]` (ver §4, "Entrada e saída"). A
normalização existe para decidir, não para reescrever o que o colaborador lançou.
**Origem:** dado de entrada; desambiguado por AMB-009.
**Aceite:** `d-014` (categoria `ALIMENTACAO`) é tratado como `alimentacao` e concorre
normalmente ao limite diário da categoria, mas aparece na saída com a `categoria`
ainda em `ALIMENTACAO`.

### RN-012 — Adicional de viagem (não implementado)

**Regra:** o adicional de 50% nos limites de alimentação e transporte urbano para
colaborador "em viagem" **não é aplicado nesta versão**, em nenhuma
circunstância. Toda despesa é avaliada pelos limites padrão (RN-001, RN-002),
independentemente do que o período ou outras despesas sugiram.
**Origem:** política do RH; desambiguado por AMB-005. Ver limitação em §10 ("O que fica em aberto").
**Aceite:** nenhuma despesa do exemplo recebe reembolso acima do limite padrão de sua
categoria por conta deste item da política.

### RN-013 — Ordem de aplicação das regras de negação

**Regra:** ver `spec.md` §8 ("Ordem de aplicação das regras"). Cada despesa recebe
exatamente uma justificativa, correspondente à primeira regra da ordem definida em
`spec.md` §8 ("Ordem de aplicação das regras") que a reprovar. Se nenhuma reprovar, o
valor reembolsável é calculado pelo limite da categoria/dia (RN-001 a RN-004).
**Origem:** consequência das ambiguidades AMB-001 a AMB-011 combinadas.
**Aceite:** `d-004` é negado citando nota fiscal ausente (RN-005), não o limite diário
já esgotado por `d-003` — ver AMB-004.

---

## 6. Ambiguidades identificadas e decisões

### AMB-001 — Unidade de aplicação do limite diário

**Texto original do RH:** "Alimentação tem limite de R$ 60 por dia." / "Transporte
urbano tem limite de R$ 80 por dia."
**O que não está claro:** "por dia" pode significar um limite por despesa individual
(cada lançamento até R$60/R$80, mesmo havendo várias no mesmo dia) ou um limite
agregado por categoria e dia (soma de todas as despesas daquela categoria naquele dia).
E, se agregado, qual despesa recebe o valor "cheio" quando o total excede o limite —
não há campo de horário no dado, só a ordem em que as despesas aparecem na entrada.
**Decisão:** o limite é agregado por categoria e dia. As despesas daquele
categoria/dia são processadas na ordem em que aparecem na entrada; a(s) primeira(s)
consomem o limite até esgotá-lo, as seguintes recebem R$0,00.
**Justificativa:** a política fala em "limite... por dia", não "por despesa" — o
exemplo do RH com dois almoços no mesmo dia (`d-001`/`d-002`) só faz sentido como
ambiguidade real se o limite for agregado. A ordem de entrada é o único critério de
desempate disponível no dado (não há horário).
**Regra afetada:** RN-001, RN-002, RN-003, RN-013.

### AMB-002 — Significado de "reembolso parcial"

**Texto original do RH:** "Despesas acima do limite são reembolsadas parcialmente."
**O que não está claro:** "parcialmente" pode significar (a) paga-se até o limite e
corta-se o excedente, (b) recusa-se a despesa inteira quando excede o limite (e
"parcial" seria só um rótulo para outro cenário), ou (c) reembolsa-se um percentual
fixo do valor total.
**Decisão:** paga-se até o limite da categoria/dia e nega-se o excedente.
**Justificativa:** é a leitura mais literal de "parcialmente" — reembolsa uma parte
(o limite), não a despesa inteira nem um percentual arbitrário sem base na política.
**Regra afetada:** RN-004.

### AMB-003 — Fronteira do limite de nota fiscal (R$100,00 exato)

**Texto original do RH:** "Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** se uma despesa de exatamente R$100,00 já exige nota fiscal
("acima de" incluindo o limite) ou só valores estritamente maiores.
**Decisão:** só valores estritamente maiores que R$100,00 exigem nota fiscal;
R$100,00 exato dispensa.
**Justificativa:** "acima de X" em português, no uso comum e no de outras políticas
fiscais, é lido como estritamente maior que X — "a partir de X" seria a formulação
para incluir o próprio valor.
**Regra afetada:** RN-005.

### AMB-004 — Ordem entre nota fiscal ausente e limite diário esgotado

**Texto original do RH:** política não trata do caso de duas regras de negação
incidirem sobre a mesma despesa.
**O que não está claro:** `d-004` (R$100,01, sem nota fiscal) está no mesmo dia e
categoria de `d-003`, que já esgota o limite diário de R$80,00 de transporte. Duas
razões de negação se aplicam: falta de nota fiscal e limite diário já consumido. Qual
determina a justificativa (e, em outros casos hipotéticos, teria efeito no valor)?
**Decisão:** a verificação de nota fiscal é feita antes da agregação do limite
diário; despesas negadas por falta de nota fiscal não chegam a competir pelo limite
diário da categoria.
**Justificativa:** nota fiscal é uma condição de elegibilidade da despesa em si
(dado ausente inviabiliza a análise), enquanto o limite diário é uma questão de
quanto reembolsar entre despesas já elegíveis — faz sentido filtrar a elegibilidade
antes de calcular quanto do orçamento diário sobra para as demais.
**Regra afetada:** RN-005, RN-013; ver ordem completa em §8 ("Ordem de aplicação das regras").

### AMB-005 — O que caracteriza colaborador "em viagem" (dado ausente)

**Texto original do RH:** "Colaborador em viagem tem limites ampliados em 50%."
**O que não está claro:** a entrada não tem nenhum campo que indique se o colaborador
está em viagem. Não há como aplicar este item sem inventar um critério não pedido
pelo RH (ex.: inferir viagem pela presença de despesas de hospedagem no período).
**Decisão:** o adicional de 50% **não é aplicado em nenhuma circunstância** nesta
versão.
**Justificativa:** inferir "em viagem" a partir de outro dado (como presença de
hospedagem) seria criar uma regra de negócio nova que o RH não escreveu, e que teria
efeito colateral incorreto em casos legítimos (ex.: colaborador que se hospeda perto
de casa por motivo alheio a viagem a trabalho). Sem um campo explícito, a decisão mais
segura e auditável é não aplicar o benefício, documentando isso como limitação
conhecida em vez de arriscar um critério arbitrário.
**Regra afetada:** RN-012.

### AMB-006 — Quantidade de diárias em hospedagem (dado ausente)

**Texto original do RH:** "Hospedagem tem limite de R$ 250 por diária."
**O que não está claro:** a entrada não tem campo estruturado para número de noites
— ele só aparece, às vezes, em texto livre na descrição (`d-010`: "Hotel Rio - 2
diarias"; `d-013`: "Airbnb 3 noites"). Aplicar o limite "por diária" exigiria extrair
essa quantidade de texto não padronizado.
**Decisão:** "diária" é lida como **dia de calendário**, não como noite de
hospedagem nem como lançamento. O limite de R$250,00 vale para a `data` da despesa
e agrega todas as despesas de `hospedagem` daquela data, exatamente como os limites
de RN-001 e RN-002. O número de noites não é inferido nem usado em nenhum cálculo.
**Justificativa:** duas leituras alternativas foram descartadas. (a) *Por noite*
exigiria extrair a quantidade de noites de texto livre não padronizado — parsing
frágil e sem garantia de estar presente, ou seja, interpretação de linguagem
natural em vez de regra determinística. (b) *Por lançamento* (cada despesa de
hospedagem com seus próprios R$250,00) tem um efeito colateral inaceitável: bastaria
quebrar uma estadia em dois lançamentos na mesma data para receber R$500,00 no dia,
transformando o limite em algo que o próprio lançador controla. Amarrar o limite ao
único campo temporal estruturado que a entrada tem (`data`) é a leitura que usa o
dado real disponível, não deixa brecha de fracionamento e mantém a mecânica
idêntica à das outras duas categorias.
**Regra afetada:** RN-003.

### AMB-007 — Critério de duplicata e qual ocorrência prevalece

**Texto original do RH:** "Duplicatas devem ser tratadas."
**O que não está claro:** a política não define o que torna duas despesas
"duplicatas" (mesmo valor e data? categoria e fornecedor também? descrição?), nem qual
das ocorrências deve ser mantida.
**Decisão:** duas despesas são duplicatas quando todos os campos são idênticos exceto
`id` (`data`, `categoria`, `descricao`, `fornecedor`, `valor`, `tem_nota_fiscal`). A
primeira ocorrência (pela ordem de entrada) é avaliada normalmente; as demais são
negadas. Além de negadas para fins de reembolso, as ocorrências duplicadas também não
entram em `valor_total_despesas`.
**Justificativa:** um critério mais frouxo (ex.: só valor e data) arriscaria negar
despesas legítimas e coincidentes (dois almoços de mesmo valor em dias diferentes de
fornecedores diferentes não deveriam colidir); exigir todos os campos exceto `id`
minimiza falso positivo mantendo o caso real do exemplo (`d-006`/`d-007`) coberto. Pela
mesma razão, somar o valor da duplicata ao total bruto de despesas do período
distorceria quanto o colaborador efetivamente gastou — `valor_total_despesas` deve
refletir gastos reais, não lançamentos repetidos do mesmo gasto.
**Regra afetada:** RN-007.

### AMB-008 — Tratamento de valores negativos / estornos

**Texto original do RH:** a política não menciona valores negativos ou estornos em
nenhum item.
**O que não está claro:** `d-009` tem valor `-45,00` ("Estorno de corrida
cancelada"). A política não diz se isso deve ser ignorado, se deve abater o total
reembolsável do período, ou se é um dado inválido a rejeitar.
**Decisão:** despesas com valor negativo são ignoradas — não geram reembolso e não
entram em nenhum dos totais do período.
**Justificativa:** um estorno não é uma despesa reembolsável nem uma dedução prevista
pela política; tratá-lo como abatimento criaria uma regra de compensação financeira que
o RH não pediu. Ignorá-lo é a opção que menos extrapola o texto da política.
**Regra afetada:** RN-009.

### AMB-009 — Sensibilidade a maiúsculas/minúsculas na categoria

**Texto original do RH:** a política nomeia as categorias em minúsculas
("Alimentação", "Transporte urbano", "Hospedagem"), mas não define como comparar
grafias diferentes.
**O que não está claro:** `d-014` chega com categoria `ALIMENTACAO` (maiúsculo).
Comparação estrita trataria isso como categoria desconhecida (igual a `d-005`,
`coworking`); comparação normalizada trataria como `alimentacao`.
**Decisão:** a comparação de categoria é normalizada (case-insensitive), e a
normalização acontece **na borda de entrada**, não dentro de cada regra: o valor já
chega normalizado a todas as verificações, inclusive à comparação de duplicata
(RN-007). A grafia original é preservada e ecoada na saída.
**Justificativa:** a variação de maiúsculas/minúsculas é um problema de formatação de
dado, não uma categoria de negócio diferente; negar reembolso legítimo por causa de
capitalização seria um efeito colateral não intencional de uma regra pensada para
filtrar categorias realmente fora da política. Normalizar na borda, e não regra a
regra, elimina a classe inteira de bug em que uma regra normaliza e outra esquece —
que já apareceu aqui: enquanto a normalização era responsabilidade de cada regra,
duas despesas idênticas exceto pela capitalização da categoria **não** eram
detectadas como duplicata, porque RN-007 comparava a grafia crua. Preservar a grafia
original para a saída mantém o relatório fiel ao que foi lançado, o que é o que
permite conferir a decisão contra o comprovante.
**Regra afetada:** RN-007, RN-008, RN-011.

### AMB-010 — Arredondamento de valores com mais de 2 casas decimais

**Texto original do RH:** a política não menciona formato numérico dos valores.
**O que não está claro:** `d-011` tem valor `33.333` (3 casas decimais), que não é um
valor monetário válido em reais. Não está claro se o sistema deve arredondar,
truncar, ou rejeitar a despesa como dado inválido.
**Decisão:** valores com mais de 2 casas decimais são truncados (não arredondados)
para 2 casas antes de qualquer cálculo.
**Justificativa:** truncar é a operação mais previsível e auditável (não depende de
regra de arredondamento bancário) e nunca reembolsa um centavo a mais do que o valor
realmente lançado — o que é mais seguro do ponto de vista financeiro do que
arredondar para cima.
**Regra afetada:** RN-010.

### AMB-011 — Fronteira do período de competência

**Texto original do RH:** "Despesas devem ser lançadas dentro do período de
competência."
**O que não está claro:** se uma despesa datada exatamente em `periodo.inicio` ou
`periodo.fim` conta como "dentro" do período (limites inclusivos) ou fica de fora
(limites exclusivos).
**Decisão:** o período é inclusivo nos dois extremos —
`periodo.inicio <= data <= periodo.fim`.
**Justificativa:** "dentro do período" de `AAAA-MM-01` a `AAAA-MM-31` naturalmente
inclui o primeiro e o último dia do mês de competência; excluir os extremos negaria
despesas legítimas do primeiro ou último dia do mês sem nenhuma indicação da política
de que isso seria intencional.
**Regra afetada:** RN-006.

---

## 7. Casos de borda

Casos citados (`d-003`, `d-004`, etc.) são despesas de `exemplos/despesas-exemplo.json`.

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Valor exatamente no limite de nota fiscal | `d-003`, valor R$100,00, sem nota fiscal | Não exige nota fiscal (limite exclusivo); segue para o limite diário | RN-005, AMB-003 |
| Valor logo acima do limite de nota fiscal, mesmo dia/categoria de despesa que já esgotou o limite diário | `d-004`, valor R$100,01, sem nota fiscal | Negado por falta de nota fiscal, não por limite diário esgotado | RN-005, RN-013, AMB-004 |
| Duas despesas idênticas exceto `id` | `d-006`/`d-007` | Primeira avaliada normalmente; segunda negada como duplicata | RN-007 |
| Despesa fora do período de competência | `d-008`, data em abril, período é julho | Negada por período de competência | RN-006 |
| Valor negativo (estorno) | `d-009`, valor -R$45,00 | Ignorada; não soma em nenhum total | RN-009 |
| Categoria fora da política | `d-005`, categoria `coworking` | Negada por categoria fora da política | RN-008 |
| Hospedagem multi-diária sem campo estruturado de noites | `d-010` (2 diárias no texto), `d-013` (3 noites no texto) | Limite de R$250,00 do **dia** da despesa; as noites citadas no texto livre são ignoradas | RN-003, AMB-006 |
| Duas hospedagens na mesma data | dois lançamentos de `hospedagem` com a mesma `data` | Dividem o mesmo limite de R$250,00 do dia — não recebem R$250,00 cada | RN-003, AMB-006 |
| Valor com mais de 2 casas decimais | `d-011`, valor `33.333` | Truncado para R$33,33 antes de qualquer verificação | RN-010 |
| Despesa em fim de semana | `d-012`, sábado, "plantão" | Tratada normalmente — a política não distingue dia útil de fim de semana | (confirma ausência de regra especial) |
| Categoria com grafia em maiúsculas | `d-014`, categoria `ALIMENTACAO` | Normalizada e tratada como `alimentacao` para decidir; devolvida como `ALIMENTACAO` na saída | RN-011, AMB-009 |
| Duas despesas idênticas exceto pela capitalização da categoria | duas despesas iguais em tudo, uma com `alimentacao` e outra com `ALIMENTACAO` | São duplicatas — a comparação de RN-007 usa a categoria já normalizada | RN-007, RN-011, AMB-009 |
| Despesa datada exatamente no primeiro ou último dia do período | qualquer despesa com `data == periodo.inicio` ou `data == periodo.fim` | Dentro do período (inclusivo) | RN-006, AMB-011 |

## 8. Ordem de aplicação das regras

Quando mais de uma regra de negação poderia se aplicar à mesma despesa, a ordem
abaixo define qual prevalece — cada despesa recebe **uma única justificativa**,
correspondente à primeira regra desta lista que a reprovar. Se nenhuma reprovar, o
valor reembolsável é calculado pelo limite da categoria/dia (RN-001 a RN-004).

1. **Valor negativo / estorno** (RN-009) — ignorada, nem chega a ser avaliada pelas
   regras seguintes.
2. **Categoria fora da política** (RN-008) — verificada com a categoria já
   normalizada (RN-011).
3. **Fora do período de competência** (RN-006).
4. **Duplicata** (RN-007) — comparação feita entre despesas que já passaram pelas
   verificações 1–3.
5. **Nota fiscal obrigatória ausente** (RN-005).
6. **Limite diário da categoria** (RN-001, RN-002, RN-003, RN-004) — só entram nesta
   agregação as despesas que sobreviveram às verificações 1–5, na ordem em que
   aparecem na entrada.

**Justificativa da ordem:** os quatro primeiros filtros descartam despesas que não
são, estruturalmente, elegíveis a reembolso (dado inválido, categoria não coberta,
fora do período, lançamento repetido). Nota fiscal vem antes do limite diário porque é
uma condição da despesa em si (RN-005, AMB-004). O limite diário é calculado por
último porque só faz sentido competir pelo orçamento do dia entre despesas que já
passaram por todos os outros filtros — uma despesa duplicada ou fora de política não
deve "gastar" limite de outra despesa legítima do mesmo dia.

## 9. Critérios de aceite

O sistema está pronto quando, rodando `exemplos/despesas-exemplo.json`:

- [ ] `d-001` reembolsa R$60,00 (parcial); `d-002` reembolsa R$0,00 (nenhum) — RN-001.
- [ ] `d-003` reembolsa R$80,00 (parcial), sem exigir nota fiscal — RN-002, RN-005.
- [ ] `d-004` reembolsa R$0,00, com justificativa citando nota fiscal ausente (não
      limite diário) — RN-005, RN-013.
- [ ] `d-005` reembolsa R$0,00, com justificativa citando categoria fora da política —
      RN-008.
- [ ] `d-006` reembolsa R$54,90 (total); `d-007` reembolsa R$0,00, com justificativa
      citando `d-006` como duplicata original, e o valor de `d-007` não é somado em
      `valor_total_despesas` — RN-007.
- [ ] `d-008` reembolsa R$0,00, com justificativa citando período de competência —
      RN-006.
- [ ] `d-009` aparece no detalhamento com R$0,00, mas não é somado em
      `valor_total_despesas` nem em `valor_total_reembolsavel` — RN-009.
- [ ] `d-010` reembolsa R$250,00 (parcial) — RN-003.
- [ ] `d-011` reembolsa R$33,33 (total, valor truncado de `33.333`) — RN-010.
- [ ] `d-012` reembolsa R$47,20 (total), sem nenhuma restrição por ser fim de semana.
- [ ] `d-013` reembolsa R$0,00, com justificativa citando nota fiscal ausente —
      RN-005.
- [ ] `d-014` reembolsa R$60,00 (parcial), com a categoria `ALIMENTACAO` tratada como
      `alimentacao` — RN-011.
- [ ] `valor_total_despesas` = R$1.806,94 (exclui a duplicata `d-007` e o estorno
      `d-009`) e `valor_total_reembolsavel` = R$585,43 para o arquivo de exemplo padrão
      (soma manual documentada nesta spec) — RN-007, RN-009.
- [ ] Nenhuma despesa recebe o adicional de 50% por "viagem" em nenhuma circunstância —
      RN-012.

## 10. O que fica em aberto

- **Adicional de viagem (RN-012 / AMB-005):** não implementado.
  A entrada não tem campo que identifique viagem, e qualquer inferência seria uma
  regra de negócio nova não solicitada pelo RH. Se um campo explícito de viagem for
  adicionado à entrada no futuro, esta regra precisa ser reaberta.
- **Limite de hospedagem por noite real (RN-003 / AMB-006):** o sistema aplica o
  limite de R$250,00 por **dia de calendário**, porque a entrada não tem campo
  estruturado de número de noites. Isso é mais restritivo do que a política
  provavelmente pretende quando um lançamento cobre várias noites (ex.: `d-010`,
  R$480,00 por 2 noites reais — taxa real de R$240,00/noite, dentro do limite de
  R$250,00 por noite, mas reembolsado como se fosse uma diária só, cortando em
  R$250,00). Se a entrada ganhar um campo estruturado de número de diárias, esta
  regra precisa ser reaberta.
