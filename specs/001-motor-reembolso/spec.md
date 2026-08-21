# Spec — Motor de Cálculo de Reembolso

**Versão:** 2.4 · **Status:** implementada para a Política de Reembolso v4 — os itens A (limites por centro de custo, lidos de arquivo externo) e B (despesas internacionais em moeda estrangeira, convertidas pela taxa da data) estão ambos cobertos por código e teste; o item C (fila de aprovação manual) segue fora de escopo por decisão do usuário. A Fase 5 de `tasks.md` (T-028 a T-045) reescreveu o motor sob a v4, e os critérios de aceite da spec.md §9 ("Critérios de aceite") estão todos marcados, cada um coberto por um teste automatizado. RN-017 passou a dizer que a verificação de vigência antecede a **avaliação** das despesas, e não a leitura do arquivo — ver `DECISIONS.md` [[D-015]]. Os cinco campos dos arquivos de entrada que o motor não lê — `versao`, `fonte`, `observacao`, `moeda_base` e `acrescimo_em_viagem_percentual` — estão todos marcados como não obrigatórios na spec.md §4 ("Entrada e saída") · **Última alteração:** `21/08/2026`

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
- Não aplica o adicional de `acrescimo_em_viagem_percentual` da política para
  colaborador "em viagem" — a entrada não tem campo que identifique viagem; ver RN-012,
  AMB-005 e spec.md §10 ("O que fica em aberto").
- Não infere o número de diárias de uma hospedagem a partir de texto livre na
  descrição — a entrada não tem campo estruturado para isso; ver RN-003, AMB-006 e
  spec.md §10 ("O que fica em aberto").
- Não solicita nem sugere correção de dado ao usuário — despesas com dado
  problemático (valor com casas decimais em excesso, valor negativo) são tratadas
  automaticamente conforme as regras desta spec, não rejeitadas como erro.
- Não altera nem persiste o arquivo de entrada, nem o arquivo de política.
- Não descobre sozinho qual arquivo de política ou de câmbio aplicar, nem consulta um
  serviço para obtê-los — os arquivos são entregues ao motor como entrada, ver spec.md
  §4 ("Entrada e saída").
- Não busca cotação em fonte externa, não interpola, não extrapola e não repete a
  cotação de outra data: a única fonte de taxa é o arquivo de câmbio recebido, e uma
  data sem cotação publicada é tratada como ausência de taxa; ver RN-016 e AMB-015.
- Não valida se o código de `moeda` existe na norma ISO 4217. O que decide se uma moeda
  é conversível é a presença dela no arquivo de câmbio, não a norma; ver AMB-016.
- Não converte a saída de volta para a moeda lançada, nem emite qualquer valor em moeda
  estrangeira além do `valor` ecoado da entrada: tudo que o motor produz é em BRL.

## 4. Entrada e saída

O motor recebe **três entradas** e produz **uma saída**.

| Entrada | Arquivo de referência | O que traz |
|---|---|---|
| Despesas | `exemplos/despesas-exemplo.json` | O lote de despesas de um colaborador num período de competência |
| Política | `exemplos/envelope/politica-v4.json` | Os limites por centro de custo e os parâmetros gerais da política vigente |
| Câmbio | `exemplos/envelope/cambio.json` | As taxas de conversão para BRL, por data e por moeda |

A política era, até a spec 1.10, um conjunto de constantes do código. Ela passou a ser
entrada porque os limites variam por centro de custo e são mantidos pelo financeiro fora
do repositório, mudando sem aviso — trocar a tabela de limites não pode exigir uma nova
versão do motor. Ver `DECISIONS.md` D-010 e RN-014.

**Entrada 1 — despesas:** conforme `exemplos/despesas-exemplo.json`. Campos e
significado:

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
| `despesas[].valor` | número | Valor da despesa, na moeda do campo `moeda`; pode ter mais de 2 casas decimais (ver RN-010) ou ser negativo (ver RN-009) | Sim |
| `despesas[].moeda` | string (ISO 4217) | Moeda em que a despesa foi lançada. **Opcional**: quando ausente, assume-se `BRL`. É normalizada para maiúsculas na leitura da entrada, antes de qualquer regra — mesma mecânica de RN-011 para `categoria`. Ver RN-015 | Não |
| `despesas[].tem_nota_fiscal` | booleano | Se a despesa tem nota fiscal anexada | Sim |

**Entrada 2 — política:** conforme `exemplos/envelope/politica-v4.json`. Campos e
significado:

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `versao` | string | Versão da política. Não é lida pelo motor; serve para auditoria humana do arquivo | Não |
| `vigencia` | string (AAAA-MM-DD) | Data a partir da qual a política vale. É **validada** contra `periodo.competencia` antes de qualquer cálculo — ver RN-017 | Sim |
| `moeda_base` | string (ISO 4217) | Declaração de que os limites estão em BRL. **Não é lida pelo motor** — o BRL é fixado pelo texto da política, não por este campo; ver abaixo | Não |
| `padrao` | objeto | Tabela de limites aplicada a centro de custo que não tem entrada própria em `centros_custo` — ver RN-014 | Sim |
| `padrao.<categoria>` | objeto | Uma entrada por categoria reembolsável na política padrão. A chave é o nome da categoria, comparado com a `categoria` já normalizada da despesa (RN-011) | Sim |
| `padrao.<categoria>.limite` | número | Limite da categoria, em BRL. O valor `0.00` significa categoria **não reembolsável**, não orçamento zerado — ver RN-008 e AMB-013 | Sim |
| `padrao.<categoria>.periodicidade` | string | Unidade do limite. Ecoada e não interpretada: `"dia"` e `"diaria"` são ambos aplicados como dia de calendário, pela decisão de AMB-006 | Sim |
| `padrao.<categoria>.observacao` | string | Texto livre do financeiro. **Não é lido pelo motor** e não influencia nenhuma decisão | Não |
| `centros_custo` | objeto | Mapa de centro de custo para a sua tabela de limites | Sim |
| `centros_custo.<CC>` | objeto | Tabela do centro de custo, com a mesma estrutura de `padrao`. É a lista **completa** das categorias reembolsáveis daquele centro de custo — ver RN-014 e AMB-012 | Sim |
| `nota_fiscal_obrigatoria_acima_de` | número | Valor acima do qual a nota fiscal passa a ser exigida — ver RN-005. É único para toda a empresa, não varia por centro de custo | Sim |
| `acrescimo_em_viagem_percentual` | número | Percentual de ampliação de limite em viagem. **Não é lido pelo motor** — a entrada não tem campo que identifique viagem, então não há o que ampliar; ver RN-012 e AMB-005. Se vier, é aceito e ignorado; se não vier, nada muda | Não |

**Entrada 3 — câmbio:** conforme `exemplos/envelope/cambio.json`. Campos e significado:

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `moeda_base` | string (ISO 4217) | Declaração de que as taxas convertem para BRL. **Não é lida pelo motor**, pela mesma razão do campo homônimo da política; ver abaixo | Não |
| `fonte` | string | Origem das cotações. Não é lida pelo motor; serve para auditoria humana | Não |
| `observacao` | string | Texto livre. **Não é lida pelo motor** — em particular, a observação de que só há cotação em dia útil bancário não autoriza o motor a inferir a taxa de outro dia; ver AMB-015 | Não |
| `taxas` | objeto | Mapa de data para as cotações daquela data | Sim |
| `taxas.<AAAA-MM-DD>` | objeto | Cotações publicadas naquela data. A ausência de uma data é ausência de cotação, não erro do arquivo | Sim |
| `taxas.<AAAA-MM-DD>.<MOEDA>` | número | Quantas unidades de BRL vale uma unidade de `<MOEDA>` naquela data. A chave é o código ISO 4217 em maiúsculas | Sim |

**O BRL não é configurável.** Ele é fixado pelo texto da política — "Os limites da
política são sempre em BRL" e "quando ausente, assume-se `BRL`" (`exemplos/rh_politica_v4.md`)
— e as duas frases são categóricas. Os campos `moeda_base` dos dois arquivos declaram
esse fato para quem lê o JSON; eles não o decidem, e o motor não os consulta. O próprio
contrato de saída desta spec sustenta isso: o campo produzido em RN-015 se chama
`valor_convertido_brl`, com a moeda no nome. Um arquivo cujo `moeda_base` diga outra
coisa é entrada malformada, não caso de negócio — e entrada malformada está fora de
escopo (spec.md §3, "Fora de escopo").

O arquivo de câmbio é a **fonte da verdade sobre quais moedas existem** para efeito
desta spec (AMB-016). Uma moeda válida na norma ISO 4217 mas ausente do arquivo é
tratada exatamente como uma moeda desconhecida: não há taxa, logo não há conversão, logo
a despesa é negada por RN-016.

Nenhum campo da política nem do câmbio é ecoado na saída como campo de topo. O que a saída precisa comunicar sobre a
política é o **efeito** dela na decisão, e isso vive na `justificativa` de cada despesa:
como o limite passou a variar por centro de custo, toda justificativa que cite um limite
diário cita também o centro de custo a que ele pertence, sem o quê duas saídas idênticas
vindas de centros de custo diferentes ficariam inexplicáveis para quem confere.

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
| `detalhamento_despesas[].motor_reembolso_output.valor_reembolsavel` | número | Valor efetivamente reembolsável desta despesa, **sempre em BRL** |
| `detalhamento_despesas[].motor_reembolso_output.taxa_cambio` | número \| null | Taxa aplicada para converter a despesa em BRL. `null` quando a despesa já está em BRL, e `null` quando não havia taxa disponível (RN-016) |
| `detalhamento_despesas[].motor_reembolso_output.valor_convertido_brl` | número \| null | Valor da despesa em BRL, já truncado em 2 casas (RN-015). `null` nos mesmos dois casos de `taxa_cambio` |
| `detalhamento_despesas[].motor_reembolso_output.justificativa` | string | Explicação em português da decisão, citando a regra aplicada e, quando relevante, a despesa relacionada (ex.: duplicata, limite estourado por conta de outra despesa). Ver abaixo o formato obrigatório de referência a outra despesa |

**Por que `taxa_cambio` e `valor_convertido_brl` são campos, e não só texto na
justificativa:** o motivo declarado nesta seção para ecoar o `valor` como lançado é
auditoria — o relatório precisa bater com o comprovante que o colaborador anexou. Com
despesa internacional, bater com o comprovante deixou de ser suficiente: o comprovante
está em euro e o reembolso em real, e entre os dois existe um número — a taxa — que não
vem de nenhum dos dois arquivos que quem confere tem na mão. Sem ele, `EUR 22,00` virando
`R$90,00` é uma afirmação impossível de verificar. Os dois campos são o que torna a
conta refazível: `valor` × `taxa_cambio` = `valor_convertido_brl`, e é sobre
`valor_convertido_brl` que os limites são aplicados.

`taxa_cambio` é um valor **ecoado** do arquivo de câmbio e sai com a escala que tem lá
(`5.93`, não `5.9300`). `valor_convertido_brl` é **produzido** pelo motor e sai com
exatamente 2 casas, como os demais valores produzidos.

**O que "campos originais" significa (obrigatório):** os campos que
`detalhamento_despesas[]` repete da entrada saem **exatamente como entraram**, mesmo
quando o motor usou internamente uma versão tratada deles para decidir. São três os
casos em que entrada e uso interno divergem:

- `categoria` sai com a grafia exata que entrou (`ALIMENTACAO`), embora a decisão
  use a forma normalizada (RN-011).
- `valor` sai com o número exato que entrou (`33.333`), embora a decisão use o valor
  truncado em 2 casas (RN-010). "Exato" inclui a **quantidade de casas decimais
  lançada**: uma despesa que entra como `72.50` sai como `72.50`, não como `72.5`.
  O `valor` sai **na moeda em que foi lançado**, nunca convertido — o valor em BRL tem
  campo próprio, `valor_convertido_brl`.
- `moeda` sai com a grafia exata que entrou, embora a decisão use a forma normalizada
  em maiúsculas (RN-015). E "exatamente como entrou" inclui **não ter entrado**: se a
  despesa não trouxe o campo `moeda`, a saída também não o traz, mesmo que o motor
  tenha assumido `BRL` para decidir. Inventar um `"moeda": "BRL"` que o colaborador não
  lançou é reescrever a entrada, que é justamente o que esta regra existe para proibir.

A regra geral é: **o valor tratado serve para calcular, o valor lançado serve para
exibir.** Tudo que o motor *produz* — `valor_reembolsavel`, `valor_total_despesas` e
`valor_total_reembolsavel` — é derivado do valor truncado e sai com **exatamente 2
casas decimais**, inclusive quando a última é zero: `60.00`, nunca `60.0`; `0.00`,
nunca `0`. Só os campos ecoados da entrada podem ter mais de 2 casas, e esses saem
com a escala que tinham na entrada.

O motivo é auditoria: o relatório precisa bater com o comprovante que o colaborador
anexou. Se `valor` saísse truncado, a linha exibiria R$33,33 para uma nota de
R$33,333, e quem confere veria uma divergência que o sistema criou sozinho. A escala
decimal é parte da mesma exigência — `R$60,00` é como o financeiro lê dinheiro e é
como o comprovante está escrito; `R$60,0` obriga quem confere a parar e reinterpretar
o número. Por isso a escala da saída é contrato desta spec, e não detalhe de
formatação delegado à biblioteca de serialização: em JSON, `60.0` e `60.00` são o
mesmo número, então nenhuma comparação que passe por *parsing* consegue distinguir os
dois — a conformidade com esta regra só é verificável sobre o **texto** do arquivo
gerado.

**Formato de referência a outra despesa (obrigatório em toda a saída):** sempre que
uma `justificativa` citar outra despesa, a referência usa o formato
`descricao(id)` — ex.: `'Almoco com cliente(d-001)'`. Vale em qualquer regra, sem
exceção. A `descricao` sozinha é ambígua (duas despesas podem ter a mesma
descrição) e o `id` sozinho é ilegível para quem confere a decisão no financeiro;
os dois juntos são legíveis e verificáveis contra a entrada.

Exemplo pequeno. As duas despesas são de `alimentacao` no mesmo dia, e o colaborador é
de `CC-ENG-PLATAFORMA`, cujo limite de alimentação na política vigente é R$75,00 — não
os R$60,00 do `padrao`. Nenhuma das duas traz o campo `moeda`, então as duas são
tratadas como `BRL` e saem com `taxa_cambio` e `valor_convertido_brl` em `null`, sem que
a saída acrescente um campo `moeda` que a entrada não tinha.

As **três** entradas são obrigatórias e aparecem abaixo, na ordem em que o motor as
usa: a política e o câmbio são lidos antes das despesas, porque RN-017 precisa da
`vigencia` e do `periodo.competencia` antes de qualquer cálculo, e RN-015 precisa das
taxas para converter. Os dois arquivos estão reduzidos ao que este exemplo exercita —
os arquivos reais trazem mais centros de custo e mais datas.

Entrada 1 — despesas:

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

Entrada 2 — política:

```json
{
  "versao": "v4",
  "vigencia": "2026-07-01",
  "moeda_base": "BRL",
  "padrao": {
    "alimentacao": { "limite": 60.00, "periodicidade": "dia" },
    "transporte_urbano": { "limite": 80.00, "periodicidade": "dia" },
    "hospedagem": { "limite": 250.00, "periodicidade": "diaria" }
  },
  "centros_custo": {
    "CC-ENG-PLATAFORMA": {
      "alimentacao": { "limite": 75.00, "periodicidade": "dia" },
      "transporte_urbano": { "limite": 80.00, "periodicidade": "dia" },
      "hospedagem": { "limite": 0.00, "periodicidade": "diaria", "observacao": "nao reembolsavel" }
    }
  },
  "nota_fiscal_obrigatoria_acima_de": 100.00,
  "acrescimo_em_viagem_percentual": 50
}
```

`vigencia` é `2026-07-01`, competência `2026-07`, e o lote é de competência `2026-07`:
RN-017 passa e o processamento acontece. `CC-ENG-PLATAFORMA` tem entrada própria, então
a tabela dele é a aplicável **integralmente** — os R$60,00 do `padrao` não são usados
para este colaborador em categoria nenhuma (RN-014).

Entrada 3 — câmbio:

```json
{
  "moeda_base": "BRL",
  "fonte": "Banco Central - PTAX de fechamento",
  "observacao": "Cotacoes publicadas apenas em dias uteis bancarios.",
  "taxas": {
    "2026-07-03": { "USD": 5.38, "EUR": 5.85 }
  }
}
```

Neste exemplo o arquivo de câmbio não é consultado nenhuma vez: as duas despesas estão
em BRL, e RN-015 só procura taxa para moeda diferente de `BRL`. Ele continua sendo
entrada obrigatória — o motor não sabe, antes de ler as despesas, que não vai precisar
dele.

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
    "valor_total_reembolsavel": 75.00,
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
                "tipo_reembolso": "total",
                "valor_reembolsavel": 72.50,
                "taxa_cambio": null,
                "valor_convertido_brl": null,
                "justificativa": "Reembolso total aprovado de acordo com a política vigente."
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
                "despesa_reembolsavel": true,
                "tipo_reembolso": "parcial",
                "valor_reembolsavel": 2.50,
                "taxa_cambio": null,
                "valor_convertido_brl": null,
                "justificativa": "A categoria alimentacao possui limite de reembolso de R$75,00 no dia para o centro de custo CC-ENG-PLATAFORMA. Reembolso parcial aprovado."
            }
        }
    ]
}
```

## 5. Regras de negócio

Cada regra recebe um ID (`RN-001`, ...). As tasks precisam referenciar esses IDs.

### RN-001 — Limite diário de alimentação

**Regra:** despesas de categoria `alimentacao` do mesmo dia são somadas, na ordem em
que aparecem na entrada; a soma é limitada ao `limite` de `alimentacao` na tabela
aplicável ao centro de custo do colaborador (RN-014); a(s) primeira(s) despesa(s) na
ordem consomem o limite, as seguintes recebem R$0,00 quando o limite já foi atingido.
O limite deixou de ser uma constante desta spec: ele varia por centro de custo e é lido
do arquivo de política — ver spec.md §4 ("Entrada e saída").
**Origem:** política do RH; desambiguado por AMB-001; parametrizado por centro de custo
pelo item A do comunicado da v4.
**Aceite:** com `d-001` (R$72,50) e `d-002` (R$38,00) no mesmo dia e o colaborador em
`CC-ENG-PLATAFORMA` (limite de alimentação R$75,00), `d-001` reembolsa R$72,50 (total)
e `d-002` reembolsa R$2,50 (parcial). O mesmo par num centro de custo com limite de
R$45,00 reembolsaria R$45,00 (parcial) e R$0,00 (nenhum) — mesma mecânica, limite
diferente.

### RN-002 — Limite diário de transporte urbano

**Regra:** mesma mecânica de RN-001, aplicada à categoria `transporte_urbano`, com o
`limite` de `transporte_urbano` na tabela aplicável ao centro de custo (RN-014).
**Origem:** política do RH; desambiguado por AMB-001; parametrizado por centro de custo
pelo item A do comunicado da v4.
**Aceite:** `d-003` (R$100,00, único sobrevivente às verificações anteriores no dia,
colaborador em `CC-ENG-PLATAFORMA`, cujo limite de transporte urbano é R$80,00)
reembolsa R$80,00 (parcial).

### RN-003 — Limite diário de hospedagem

**Regra:** mesma mecânica de RN-001, aplicada à categoria `hospedagem`, com o `limite`
de `hospedagem` na tabela aplicável ao centro de custo (RN-014). Ou seja: todas as
despesas de `hospedagem` de uma mesma `data` são somadas na ordem em que aparecem na
entrada e disputam **um único** limite daquele dia — a(s) primeira(s) consomem o limite,
as seguintes recebem R$0,00 quando ele já foi atingido.

O número de noites que um lançamento cobre **não entra na conta em nenhuma
hipótese**: a entrada não tem campo estruturado para isso e o sistema não extrai
essa informação do texto livre da `descricao` (ver AMB-006). Um lançamento que
cobre várias noites concorre ao limite de **um único dia** — o da sua `data` —,
exatamente como um lançamento de uma noite só. O limite nunca é multiplicado pelo
número de noites, e também nunca é aplicado "por lançamento": dois lançamentos de
`hospedagem` no mesmo dia dividem o mesmo limite. Isso vale igualmente quando a
`periodicidade` no arquivo de política é `"diaria"` — ver AMB-006.
**Origem:** política do RH; desambiguado por AMB-006; parametrizado por centro de custo
pelo item A do comunicado da v4.
**Aceite:** `f-002` (R$310,00, com nota fiscal, único lançamento de `hospedagem` em
`2026-07-17`, colaborador em `CC-SUPORTE-N2`, que não tem entrada na tabela e portanto
cai no `padrao`, com limite de R$250,00) reembolsa R$250,00 (parcial). Duas hospedagens
na mesma data, de R$480,00 e R$300,00 nessa ordem, sob um limite de R$250,00, reembolsam
R$250,00 (parcial) e R$0,00 (nenhum), respectivamente. Já `d-010` (R$480,00, colaborador
em `CC-ENG-PLATAFORMA`, cuja tabela traz `hospedagem` com `limite` igual a `0.00`) é
negada por RN-008, e nem chega a ser avaliada por esta regra.

### RN-004 — Reembolso parcial

**Regra:** quando uma despesa sobrevive a todos os filtros de negação — os passos 1 a 6
da spec.md §8 ("Ordem de aplicação das regras") — mas seu valor em BRL, somado ao das
despesas anteriores da mesma categoria e dia, excede o limite da categoria,
reembolsa-se exatamente o limite restante daquele dia/categoria; o excedente não é
reembolsado. Tanto o valor comparado quanto o valor reembolsado são em BRL (RN-015).
**Origem:** política do RH; desambiguado por AMB-002.
**Aceite:** ver RN-001, RN-002 e RN-003.

### RN-005 — Nota fiscal obrigatória

**Regra:** despesas cujo **valor em BRL** (RN-015) é estritamente maior que
`nota_fiscal_obrigatoria_acima_de` da política (spec.md §4, "Entrada e saída") exigem
`tem_nota_fiscal = true`; se ausente, a despesa é negada integralmente
(`valor_reembolsavel = 0,00`), independentemente de haver ou não limite de categoria
disponível naquele dia. Despesas cujo valor em BRL é **igual** ao teto não exigem nota
fiscal. Ao contrário dos limites de categoria, o teto é único para toda a empresa: ele
não varia por centro de custo.

O que a regra compara é o valor convertido, **nunca** o número lançado na moeda
estrangeira (ver AMB-017). O teto está em BRL, como todo limite desta política, e
comparar o número lançado faria a exigência de nota fiscal depender da moeda: uma
despesa de USD 19,00 vale mais de R$100,00 e escaparia da nota; uma de EUR 101,00
vale quase R$600,00 e a exigiria pelo motivo errado.
**Origem:** política do RH; desambiguado por AMB-003 e AMB-004; teto parametrizado pelo
item A do comunicado da v4.
**Aceite:** com o teto vigente de R$100,00, `d-003` (R$100,00, sem nota fiscal) não é
negado por este motivo; `d-004`
(R$100,01, sem nota fiscal, mesmo dia/categoria de `d-003` que já esgotou o limite
diário) é negado citando a nota fiscal ausente, não o limite diário. `e-005` (USD 40,00
em `2026-07-20`, taxa 5,50, sem nota fiscal) é negado citando a nota fiscal, porque
vale R$220,00 — embora 40,00 seja menor que 100,00. `e-003` (EUR 14,50, taxa 5,88, sem
nota fiscal) **não** é negado por este motivo, porque vale R$85,26.

### RN-006 — Período de competência

**Regra:** uma despesa só é elegível a reembolso se sua `data` estiver entre
`periodo.inicio` e `periodo.fim`, incluindo os dois extremos. Fora disso, é negada
integralmente.
**Origem:** política do RH; desambiguado por AMB-011.
**Aceite:** `d-008` (data `2026-04-15`, fora de `2026-07-01`–`2026-07-31`) é negado
citando o período de competência.

### RN-007 — Tratamento de duplicatas

**Regra:** duas despesas cujos campos `data`, `categoria`, `descricao`, `fornecedor`,
`valor`, `moeda` e `tem_nota_fiscal` são todos idênticos (o `id` é o único campo que
pode diferir) são consideradas o mesmo lançamento repetido. A comparação de `categoria`
usa a forma normalizada (RN-011) e a de `moeda` usa a forma normalizada de RN-015 —
`ALIMENTACAO` e `alimentacao` são a mesma categoria aqui, assim como `eur` e `EUR` são
a mesma moeda, e uma despesa sem o campo `moeda` é igual a uma com `"moeda": "BRL"`,
porque as duas significam a mesma coisa. Duas despesas que diferem só por
capitalização, ou só pela presença do campo `moeda` com valor `BRL`, **são** duplicatas.

A comparação é feita sobre o valor **lançado** e a moeda, nunca sobre o valor
convertido: EUR 22,00 e BRL 22,00, idênticas em todo o resto, não são duplicatas (ver
AMB-019). Apenas a primeira ocorrência
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

### RN-008 — Categorias não reembolsáveis para o centro de custo

**Regra:** uma despesa é integralmente negada quando a sua categoria, normalizada para
minúsculas (RN-011), não é reembolsável para o centro de custo do colaborador. Há duas
formas de isso acontecer, e **cada uma tem a sua justificativa**, porque são situações
diferentes para quem confere:

1. **Categoria ausente da tabela aplicável** (RN-014) — a categoria não aparece na
   tabela do centro de custo, ou seja, a política não cobre esse tipo de gasto para ele.
   A justificativa cita a categoria e o centro de custo.
2. **Categoria presente com `limite` igual a `0.00`** — a categoria existe na tabela, e o
   financeiro escreveu explicitamente que ela não é reembolsável naquele centro de custo.
   A justificativa cita a proibição, e **nunca** "limite diário atingido": nenhum limite
   foi consumido por despesa nenhuma, a categoria é que está vedada (ver AMB-013).

Nos dois casos o resultado é `valor_reembolsavel = 0,00` com
`tipo_reembolso = "nenhum"`, e a despesa **entra normalmente** em
`valor_total_despesas` — foi um gasto real do colaborador, apenas não reembolsável.
Qual é o conjunto de categorias reembolsáveis deixou de ser uma constante desta spec:
ele é derivado da tabela do centro de custo (RN-014), e a mesma categoria pode ser
reembolsável num centro de custo e não em outro.
**Origem:** política do RH; reformulada pelo item A do comunicado da v4; desambiguada
por AMB-012 e AMB-013.
**Aceite:** `d-005` (categoria `coworking`, colaborador em `CC-ENG-PLATAFORMA`) é negado
pela cláusula 1. `d-010` (`hospedagem` em `CC-ENG-PLATAFORMA`, cuja tabela traz
`hospedagem` com `limite` igual a `0.00`) é negado pela cláusula 2. `f-003`
(`representacao` em `CC-SUPORTE-N2`, que cai no `padrao`, onde `representacao` não
existe) é negado pela cláusula 1 — ainda que `representacao` seja reembolsável em
`CC-COMERCIAL`.

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

O truncamento acontece **duas vezes** quando há conversão de moeda, e nas duas vezes
com a mesma mecânica: uma no valor lançado, na leitura da entrada, e outra no produto
`valor × taxa`, que quase nunca cai redondo (ver RN-015 e AMB-018). Truncar só no fim
faria o motor decidir sobre um valor lançado que não é monetário; truncar só no começo
deixaria o valor em BRL com casas decimais a mais, que é o número comparado ao limite e
publicado em `valor_convertido_brl`.
**Origem:** dado de entrada; desambiguado por AMB-010 e AMB-018.
**Aceite:** `d-011` (valor `33.333`) é tratado como R$33,33. `e-003` (EUR 14,50 pela
taxa 5,88) é tratado como R$85,26 — o produto exato, `85.26`, não precisa de
truncamento, e o resultado é o mesmo.

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

**Regra:** o adicional percentual nos limites para colaborador "em viagem" — hoje o
campo `acrescimo_em_viagem_percentual` da política, valendo 50 — **não é aplicado nesta
versão**, em nenhuma circunstância. Toda despesa é avaliada pelo limite da sua categoria
na tabela do centro de custo (RN-001, RN-002, RN-003, RN-014), independentemente do que
o período ou outras despesas sugiram.
**Origem:** política do RH, e o campo `acrescimo_em_viagem_percentual` da política
(spec.md §4, "Entrada e saída"), que o motor não lê; desambiguado por AMB-005. Ver
limitação em spec.md §10 ("O que fica em aberto").
**Aceite:** nenhuma despesa do exemplo recebe reembolso acima do limite padrão de sua
categoria por conta deste item da política.

### RN-013 — Ordem de aplicação das regras de negação

**Regra:** ver `spec.md` §8 ("Ordem de aplicação das regras"). Cada despesa recebe
exatamente uma justificativa, correspondente à primeira regra da ordem definida em
`spec.md` §8 ("Ordem de aplicação das regras") que a reprovar. Se nenhuma reprovar, o
valor reembolsável é calculado pelo limite da categoria/dia (RN-001 a RN-004).
**Origem:** consequência das ambiguidades AMB-001 a AMB-020 combinadas. Não inclui
RN-017, que não decide sobre despesa e roda antes desta ordem começar.
**Aceite:** `d-004` é negado citando nota fiscal ausente (RN-005), não o limite diário
já esgotado por `d-003` — ver AMB-004.

### RN-014 — Tabela de limites aplicável ao centro de custo

**Regra:** os limites de categoria não são mais únicos para a empresa. Antes de avaliar
qualquer despesa, o motor resolve **uma** tabela de limites para o lote inteiro, a partir
de `colaborador.centro_custo` e do arquivo de política (spec.md §4, "Entrada e saída"):

- Se o centro de custo **tem** entrada em `centros_custo`, essa entrada é a tabela
  aplicável, integralmente. Ela é a lista completa das categorias reembolsáveis daquele
  centro de custo, e o bloco `padrao` **não** a complementa em categoria nenhuma.
- Se o centro de custo **não tem** entrada em `centros_custo`, a tabela aplicável é o
  bloco `padrao`, integralmente.

A tabela é resolvida uma única vez, na leitura da entrada, e daí em diante toda regra
enxerga apenas a tabela já resolvida — mesmo princípio de RN-010 e RN-011. Nenhuma regra
volta a consultar o arquivo de política por conta própria, e portanto nenhuma pode
divergir das outras sobre qual limite vale.
**Origem:** item A do comunicado da v4 ("Limites passam a variar por centro de custo");
desambiguado por AMB-012.
**Aceite:** `CC-COMERCIAL` tem entrada própria e usa alimentação R$90,00, transporte
urbano R$150,00, hospedagem R$400,00 e `representacao` R$300,00 — e nenhuma outra
categoria. `CC-SUPORTE-N2` não tem entrada e usa o `padrao`: alimentação R$60,00,
transporte urbano R$80,00 e hospedagem R$250,00 — e não tem `representacao`, por isso
`f-003` é negada por RN-008. Um centro de custo com entrada própria que não liste
`hospedagem` nega a hospedagem por RN-008; ele **não** herda os R$250,00 do `padrao`
(ver AMB-012).

### RN-015 — Conversão de despesa em moeda estrangeira

**Regra:** toda despesa tem um **valor em BRL**, e é sempre esse valor que as demais
regras usam — limite diário (RN-001 a RN-004), teto de nota fiscal (RN-005) e os dois
totais do período. Ele é obtido assim:

1. A `moeda` da despesa é normalizada para maiúsculas na leitura da entrada, junto com
   a `categoria` (RN-011). Despesa **sem** o campo `moeda` é tratada como `BRL`.
2. Se a moeda normalizada é `BRL`, o valor em BRL é o próprio `valor` já truncado
   (RN-010). Não há conversão, e `taxa_cambio` e `valor_convertido_brl` saem `null`.
3. Caso contrário, o motor procura no arquivo de câmbio a taxa daquela **moeda** na
   **data da despesa**. Se não existir, a despesa é negada por RN-016 e não tem valor
   em BRL. Se existir, o valor em BRL é `valor truncado × taxa`, truncado em 2 casas
   pela mecânica de RN-010, e a taxa e o resultado são publicados em `taxa_cambio` e
   `valor_convertido_brl`.

A data usada é a `data` da despesa, nunca a data de execução do motor e nunca outra
data do arquivo (ver AMB-015). Despesa em moeda estrangeira **não** amplia limite
nenhum: ela não caracteriza "em viagem", e RN-012 continua não aplicada (ver AMB-014).
**Origem:** item B do comunicado da v4 ("Despesas internacionais"); desambiguado por
AMB-014, AMB-017 e AMB-018.
**Aceite:** `e-002` (EUR 22,00 em `2026-07-14`, taxa 5,93) vale R$130,46 e concorre ao
limite de alimentação de `CC-COMERCIAL` (R$90,00), reembolsando R$90,00 (parcial).
`e-010` (R$88,00, **sem** o campo `moeda`) é tratada como BRL e reembolsa R$88,00
(total), com `taxa_cambio` e `valor_convertido_brl` em `null`. `e-001` (R$340,00 com
`"moeda": "BRL"` explícito) recebe o mesmo tratamento de `e-010`: o campo presente com
valor `BRL` não muda nada.

### RN-016 — Câmbio indisponível

**Regra:** uma despesa em moeda diferente de `BRL` para a qual o arquivo de câmbio não
tem taxa é negada integralmente. Há duas formas de não haver taxa, e as duas têm o mesmo
efeito:

1. A `data` da despesa não está em `taxas` — não houve cotação publicada naquele dia
   (fim de semana, feriado, ou data fora do intervalo que o arquivo cobre).
2. A `data` está em `taxas`, mas a `moeda` da despesa não está entre as cotações
   daquele dia — o arquivo simplesmente não publica aquela moeda.

A despesa negada por esta regra recebe `valor_reembolsavel = 0,00`,
`tipo_reembolso = "nenhum"`, `taxa_cambio` e `valor_convertido_brl` em `null`, **não
consome** limite diário de nenhuma categoria e **não entra** em `valor_total_despesas`
— pelo mesmo motivo de RN-009: `valor_total_despesas` é um total em BRL, e esta despesa
não tem valor em BRL para somar. Somar o número lançado seria somar euros a reais.

A justificativa cita a moeda e a data, para que quem confere saiba qual das duas coisas
faltou e possa reprocessar o lote quando o arquivo de câmbio for atualizado.
**Origem:** item B do comunicado da v4; desambiguado por AMB-015 e AMB-016.
**Aceite:** `e-004` (EUR 30,00 em `2026-07-18`, um sábado, sem cotação publicada) é
negada pela forma 1. `e-006` (GBP 55,00 em `2026-07-21`, data com cotação de USD e EUR
mas não de GBP) é negada pela forma 2. Nenhuma das duas soma em `valor_total_despesas`,
e a alimentação de `e-004` não consome nada do limite do dia `2026-07-18`.

### RN-017 — Vigência da política contra a competência do lote

**Regra:** antes de qualquer cálculo de reembolso — antes do primeiro passo da spec.md
§8 ("Ordem de aplicação das regras"), e antes de qualquer despesa ser **avaliada** —, o
motor verifica que a política recebida vale para o lote:

```
competência de `vigencia` <= `periodo.competencia`
```

A competência de `vigencia` é o ano e o mês da data (`2026-07-01` → `2026-07`). A
comparação é entre competências, não entre datas, e o operador é "igual ou anterior".

**A verificação não acontece antes da leitura do arquivo de despesas, e não tem como
acontecer.** Um dos dois lados da comparação é `periodo.competencia`, e esse campo vive
dentro do próprio arquivo de despesas (spec.md §4, "Entrada e saída") — o motor precisa
abrir e ler o arquivo para ter o dado com que decide. O que esta regra ordena é que
nenhuma despesa seja **avaliada** antes da verificação, não que o arquivo não seja lido:
quando ela reprova, o lote já foi lido e nada além disso aconteceu — nenhuma despesa
recebeu decisão ou justificativa, nenhum total foi somado e nenhum arquivo de saída foi
aberto.

Esta é a única regra desta spec que **não** produz uma decisão por despesa. Ela é uma
precondição do lote inteiro: ou a política vale para aquele mês de competência e o
processamento acontece normalmente, ou ela não vale e **nada é processado**.

**Quando a verificação reprova**, o motor não escreve arquivo de saída nenhum. Ele
imprime no terminal uma mensagem explicando o motivo — citando a competência de
vigência da política e a competência do lote — e encerra com código de saída diferente
de zero. Um `resultado.json` com todas as despesas zeradas seria pior do que nenhum
arquivo: ele tem a forma de um relatório válido e pode ser arquivado como se fosse um.
**Origem:** o campo `vigencia` da política, e a abertura do comunicado da v4
(`exemplos/rh_politica_v4.md`): "Vigência imediata, retroativa à competência atual";
desambiguado por AMB-020.
**Aceite:** com `vigencia: 2026-07-01` (competência `2026-07`), um lote de competência
`2026-07` é processado, e um lote de `2026-08` também — a política de julho continua
valendo em agosto se não houver política nova. Um lote de competência `2026-06`
reprova, sem arquivo de saída: junho tem que ser processado com a política que valia
em junho.

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
**Decisão:** o adicional — hoje o campo `acrescimo_em_viagem_percentual` da política,
valendo 50 — **não é aplicado em nenhuma circunstância** nesta versão.
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
hospedagem nem como lançamento. O limite de hospedagem vale para a `data` da despesa
e agrega todas as despesas de `hospedagem` daquela data, exatamente como os limites
de RN-001 e RN-002. O número de noites não é inferido nem usado em nenhum cálculo.
A v4 não reabriu esta decisão: ela trocou o **valor** do limite (que passou a variar
por centro de custo, RN-014) e manteve a `periodicidade` do arquivo — `"dia"` e
`"diaria"` — sem definir nada que distinga uma da outra, então as duas continuam sendo
lidas como dia de calendário.
**Justificativa:** duas leituras alternativas foram descartadas. (a) *Por noite*
exigiria extrair a quantidade de noites de texto livre não padronizado — parsing
frágil e sem garantia de estar presente, ou seja, interpretação de linguagem
natural em vez de regra determinística. (b) *Por lançamento* (cada despesa de
hospedagem com o seu próprio limite cheio) tem um efeito colateral inaceitável:
bastaria quebrar uma estadia em dois lançamentos na mesma data para receber o dobro do
limite no dia, transformando o limite em algo que o próprio lançador controla. Amarrar o limite ao
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

### AMB-012 — Granularidade de "aplica-se a política padrão"

**Texto original do RH:** "Alguns centros de custo não têm entrada na tabela. Nesse caso,
aplica-se a política padrão."
**O que não está claro:** "não têm entrada" admite duas granularidades. (a) *Por centro
de custo*: só o centro de custo inteiramente ausente de `centros_custo` cai no `padrao`.
(b) *Por categoria*: o `padrao` também preenche as categorias que faltam na tabela de um
centro de custo que existe — sob essa leitura, `CC-ADM`, que não lista `hospedagem`,
herdaria os R$250,00 do padrão. As duas leituras dão respostas opostas para a mesma
despesa: uma hospedagem em `CC-ADM` é negada sob (a) e reembolsada em R$250,00 sob (b).
**Decisão:** granularidade **por centro de custo**. A tabela de um centro de custo que
existe em `centros_custo` é a lista completa e fechada das suas categorias reembolsáveis;
o `padrao` só entra quando o centro de custo inteiro não está na tabela. Hospedagem em
`CC-ADM` é negada por RN-008.
**Justificativa:** a unidade que o RH nomeia na frase é "centros de custo" que "não têm
entrada", não categorias que faltam. A leitura por categoria transformaria a tabela de
cada centro de custo numa lista de *exceções* ao padrão, e não na política daquele centro
de custo — o comunicado não diz isso em lugar nenhum. Ela também tem efeito colateral
concreto: `CC-ADM` é administrativo e o financeiro deliberadamente não listou
`hospedagem` para ele; herdar R$250,00 do padrão silenciosamente reembolsaria justamente
o gasto que a tabela foi escrita para não cobrir, e o erro seria invisível — nada no
arquivo denunciaria a herança. A leitura fechada erra para o lado de negar e obriga o
financeiro a ser explícito, que é o comportamento auditável. O preço é conhecido e está
registrado em spec.md §10 ("O que fica em aberto"): um centro de custo novo cadastrado
com a tabela incompleta nega despesa legítima até alguém corrigir o arquivo.
**Regra afetada:** RN-008, RN-014.

### AMB-013 — Categoria com limite `0.00` na tabela do centro de custo

**Texto original do RH:** "`CC-ENG-PLATAFORMA` não reembolsa `hospedagem` de forma
alguma." No arquivo isso aparece como `"hospedagem": { "limite": 0.00, "periodicidade":
"diaria", "observacao": "nao reembolsavel" }`.
**O que não está claro:** um `limite` de `0.00` pode ser lido como (a) uma categoria
reembolsável cujo orçamento diário disponível é zero — a despesa passaria pelo cálculo de
limite diário e receberia R$0,00 —, ou (b) uma proibição explícita, verificada antes de
qualquer agregação. O **valor** reembolsado é o mesmo nas duas leituras; o que muda é a
justificativa que o financeiro lê e a posição da verificação na ordem da spec.md §8
("Ordem de aplicação das regras").
**Decisão:** proibição explícita. `limite: 0.00` é verificado junto com RN-008, no passo
2 da ordem, e produz justificativa citando a proibição para aquele centro de custo —
nunca "limite diário atingido".
**Justificativa:** "limite diário de R$0,00 já atingido na despesa X" é uma frase falsa:
nada foi atingido, nenhuma outra despesa consumiu nada, e não existe despesa X para
citar. Ela mandaria quem confere procurar um lançamento que não existe. O financeiro
também escreveu `"observacao": "nao reembolsavel"` ao lado do zero — a intenção declarada
é vedar a categoria, não orçá-la em zero. E a leitura (a) produziria justificativa
enganosa em combinação com outras regras: uma hospedagem sem nota fiscal em
`CC-ENG-PLATAFORMA` seria negada citando a nota, sugerindo a quem lê que anexar o
comprovante resolveria — quando não resolve, porque a categoria está vedada. É
exatamente o caso de `d-013`.
**Regra afetada:** RN-008, RN-014; ver ordem completa em spec.md §8 ("Ordem de aplicação
das regras").

### AMB-014 — Moeda estrangeira caracteriza colaborador "em viagem"?

**Texto original do RH:** "Colaboradores em viagem internacional lançam despesas em
moeda estrangeira." E, da v3, que a v4 não revogou: "Colaborador em viagem tem limites
ampliados em 50%."
**O que não está claro:** as duas frases postas lado a lado sugerem uma implicação que
nenhuma das duas afirma. Se colaborador em viagem lança em moeda estrangeira, uma
despesa em moeda estrangeira indica viagem — e portanto deveria receber o adicional de
`acrescimo_em_viagem_percentual`, que a v4 manteve no arquivo de política. O comunicado
não diz isso, e também não diz o contrário.
**Decisão:** moeda estrangeira **não** caracteriza viagem. RN-012 continua não aplicada,
em nenhuma circunstância, inclusive para despesa internacional.
**Justificativa:** a implicação não se sustenta na direção necessária. "Quem viaja lança
em moeda estrangeira" não é o mesmo que "quem lança em moeda estrangeira está em
viagem" — uma assinatura anual cobrada em dólar, uma compra online num fornecedor de
fora, um almoço pago em euro num evento no próprio país são todos gastos em moeda
estrangeira sem viagem nenhuma. Aplicar o adicional a partir da moeda ampliaria o limite
justamente na classe de despesa mais difícil de conferir. É a mesma decisão de AMB-005,
pelo mesmo motivo, e com a mesma consequência registrada em spec.md §10 ("O que fica em
aberto"): sem um campo explícito de viagem na entrada, o benefício não é aplicado.
**Regra afetada:** RN-012, RN-015.

### AMB-015 — "A taxa da data da despesa" quando a data não tem cotação

**Texto original do RH:** "A conversão usa a **taxa da data da despesa**, não a taxa de
hoje." E, no próprio arquivo de câmbio: `"observacao": "Cotacoes publicadas apenas em
dias uteis bancarios."`
**O que não está claro:** o RH define de que data a taxa vem, mas não o que fazer quando
aquela data não tem taxa. E isso não é caso raro: o arquivo só publica dia útil, cobre
apenas de `2026-07-13` a `2026-07-28`, e o próprio conjunto de despesas do envelope tem
uma despesa em euro num sábado (`e-004`, `2026-07-18`). Uma despesa fora do intervalo
publicado cai no mesmo buraco.
**Decisão:** sem cotação na data, a despesa é **negada** (RN-016). Não se usa a cotação
do dia útil anterior, nem a do posterior, nem média, nem a mais próxima.
**Justificativa:** a alternativa descartada — cotação do último dia útil anterior — é a
prática de mercado, é o que a PTAX significa no uso corrente, e a observação do próprio
arquivo de câmbio pode ser lida como um convite a implementá-la. Ela foi descartada
mesmo assim, pelo mesmo critério que já governa AMB-005 e AMB-008 neste projeto: usar a
taxa de outra data é aplicar uma regra que o RH não escreveu, e escrevê-la sozinho aqui
significa escolher também qual data (anterior? mais próxima?), quantos dias para trás
aceitar antes de desistir, e o que fazer no início do arquivo, onde não há dia anterior
nenhum — três decisões novas embutidas numa que parecia óbvia. Negar é determinístico,
é auditável, e o erro que produz é visível: uma despesa negada com justificativa
citando a data e a moeda faz o financeiro atualizar o arquivo de câmbio, enquanto uma
despesa convertida por uma taxa de outro dia é reembolsada em silêncio, com um número
que ninguém consegue refazer a partir dos arquivos entregues. Esta é a decisão mais
provável de ser revertida quando o RH for consultado, e está registrada como tal em
spec.md §10 ("O que fica em aberto").
**Regra afetada:** RN-015, RN-016.

### AMB-016 — Moeda válida na ISO 4217 mas ausente do arquivo de câmbio

**Texto original do RH:** "A entrada agora pode trazer um campo `moeda` (ISO 4217)." E:
"Uma despesa em EUR é convertida antes de ser comparada ao limite."
**O que não está claro:** o RH descreve o campo pela norma ISO 4217, que tem mais de
150 moedas, e depois exemplifica com EUR. O arquivo de câmbio publica duas: USD e EUR.
`e-006` chega em GBP — um código perfeitamente válido na norma e inexistente no arquivo.
Não está dito se validar `moeda` é conferir a norma ou conferir o arquivo.
**Decisão:** o arquivo de câmbio é a fonte da verdade. Se a moeda tem taxa publicada
naquela data, a despesa é convertida; se não tem, é negada por RN-016 — sem nenhuma
distinção entre "moeda que não existe" e "moeda que existe e não foi publicada".
**Justificativa:** a norma ISO 4217 diz que um código é bem formado, não quanto ele vale
em real, e é o valor em real que esta spec precisa para decidir qualquer coisa. Validar
contra a norma exigiria embutir a lista de moedas no motor — um segundo cadastro, que
envelheceria por conta própria e ainda assim não permitiria converter nada. E a distinção
entre os dois casos não muda o que acontece com a despesa: nos dois falta a taxa, nos
dois o financeiro precisa fazer a mesma coisa, que é publicar a cotação. Uma
justificativa só, citando moeda e data, cobre os dois.
**Regra afetada:** RN-015, RN-016.

### AMB-017 — O teto de nota fiscal compara o valor lançado ou o convertido?

**Texto original do RH:** "Nota fiscal é obrigatória acima de R$ 100" (v3, não revogada)
e "Os limites da política são sempre em BRL. Uma despesa em EUR é convertida antes de
ser comparada ao limite" (v4).
**O que não está claro:** a v4 diz que a conversão vem antes da comparação com "o
limite", e o teto de nota fiscal é um limiar, não um limite de categoria. Não está dito
se ele entra nessa frase.
**Decisão:** entra. O teto é comparado contra o valor em BRL, como todo limiar desta
política.
**Justificativa:** o teto está escrito em reais — "acima de R$ 100" —, então comparar
com ele um número em euro é comparar grandezas diferentes, e o resultado depende de qual
moeda o colaborador usou, não de quanto ele gastou. O efeito prático é uma brecha:
`e-005` (USD 40,00 = R$220,00, sem nota fiscal) passaria pela exigência porque 40 é menor
que 100, quando é justamente o tipo de despesa que a regra existe para cobrir. Na direção
oposta, uma despesa de EUR 101,00 exigiria nota por um motivo aritmético falso. A leitura
por valor convertido é a única em que a exigência depende do gasto.
**Regra afetada:** RN-005, RN-015.

### AMB-018 — Precisão do valor convertido

**Texto original do RH:** o comunicado não menciona arredondamento em nenhum ponto.
**O que não está claro:** `valor × taxa` quase nunca cai em duas casas decimais — EUR
22,00 pela taxa 5,93 dá exatos R$130,46, mas EUR 22,50 pela mesma taxa daria
R$133,425. Não está dito se o motor arredonda, trunca, ou compara o limite contra o
número cheio.
**Decisão:** trunca em 2 casas, `ROUND_DOWN`, exatamente como RN-010 faz com o valor
lançado.
**Justificativa:** é a mesma decisão de AMB-010 pelo mesmo motivo — truncar não depende
de convenção de arredondamento e nunca reembolsa um centavo a mais do que o valor real.
Aplicar duas mecânicas diferentes de precisão no mesmo pipeline, uma para valor lançado e
outra para valor convertido, criaria uma diferença sem razão de existir e um segundo
lugar para errar. Comparar o limite contra o número cheio foi descartado por um motivo a
mais: `valor_convertido_brl` é publicado na saída, e um valor publicado com três casas
decimais é o mesmo defeito de escala que a spec.md §4 ("Entrada e saída") já resolveu
para os demais valores produzidos.
**Regra afetada:** RN-010, RN-015.

### AMB-019 — `moeda` entra na identidade de duplicata?

**Texto original do RH:** "Duplicatas devem ser tratadas" (v3), sem menção a moeda.
**O que não está claro:** RN-007 define duplicata como identidade em todos os campos
exceto `id`. `moeda` é um campo novo, e não está dito se ele entra nessa lista — nem o
que fazer com a despesa que não traz o campo.
**Decisão:** entra, na forma normalizada, e comparado sobre o valor **lançado**. Despesa
sem o campo `moeda` é idêntica a uma com `"moeda": "BRL"`, porque as duas significam a
mesma coisa (RN-015).
**Justificativa:** deixar `moeda` fora tornaria EUR 22,00 e BRL 22,00 duplicatas uma da
outra — dois gastos de valores completamente diferentes, e o segundo seria negado
citando o primeiro, com o total do período subtraindo um gasto real. Comparar o valor
convertido em vez do lançado tem o defeito simétrico: duas despesas de moedas diferentes
que por acidente convertem para o mesmo valor em BRL virariam duplicatas, e a decisão
passaria a depender da taxa do dia, o que faria a mesma entrada produzir resultados
diferentes se o arquivo de câmbio fosse corrigido. Tratar campo ausente como `BRL` é
consequência direta de RN-015: se o motor decide igual nos dois casos, RN-007 não pode
enxergar uma diferença que nenhuma outra regra enxerga.
**Regra afetada:** RN-007, RN-015.

### AMB-020 — O que "retroativa à competência atual" exige do motor

**Texto original do RH:** a abertura do comunicado da v4
(`exemplos/rh_politica_v4.md`): "Vigência imediata, retroativa à competência atual." E o
campo `vigencia: 2026-07-01` no arquivo de política.
**O que não está claro:** o comunicado chegou no meio de julho e o campo diz `01/07`.
Três leituras cabem no texto. (a) *A retroatividade alcança meses anteriores*: a
política nova julgaria também despesas de junho e maio. (b) *A retroatividade é uma
regra por despesa*: o motor deveria negar despesa anterior à `vigencia`, e "retroativa"
seria a exceção que salva as despesas da competência corrente. (c) *A retroatividade já
está aplicada no dado*: o RH datou o campo no primeiro dia da competência justamente
para cobrir o mês inteiro, e o motor não precisa fazer nada além de respeitar o campo.
**Decisão:** leitura (c). A verificação de vigência existe, é obrigatória, e é **uma
só**, no lote inteiro (RN-017). **Não** existe verificação de vigência por despesa — a
verificação por despesa que o motor faz é a de período (RN-006), que já valida a `data`
contra `periodo.inicio` e `periodo.fim`.
**Justificativa:** "retroativa **à** competência atual" fixa a fronteira da
retroatividade, não abre uma reta — é o mesmo uso de "válido até dezembro". Isso
descarta (a). O dado corrobora: o comunicado é do meio de julho e o campo vale
`2026-07-01`, ou seja, o RH já retroagiu até o início da competência e parou ali; se a
intenção alcançasse junho, o campo traria uma data de junho, porque é ele que codifica
até onde a retroatividade vai. A leitura (b) foi descartada por se contradizer: um
check `data >= vigencia` só tem efeito quando a vigência cai no meio do período — e é
exatamente nesse cenário que a frase do RH manda cobrir o mês inteiro assim mesmo. Fora
dele, o check é redundante com RN-006. Ou seja, ou não faz nada, ou faz o contrário do
que o comunicado pede.

O operador de RN-017 é "igual ou anterior", e não "igual", por duas razões práticas do
processo: um mês futuro pode não ter atualização de política, e nesse caso a política
corrente precisa continuar valendo; e um mês anterior precisa ser processado com a
política que valia nele, e não com uma posterior. Há também um argumento no próprio
arquivo — existe `vigencia` e não existe `fim_vigencia`. Uma data de início sem data de
fim é, por construção, aberta; sob "igual", cada arquivo de política serviria para
exatamente uma competência na vida, e `vigencia` passaria a se comportar como etiqueta
de mês, não como início de vigência.

**Nota de processo:** esta decisão nasceu de um erro. A versão anterior desta spec
declarava, na spec.md §3 ("Fora de escopo"), que o motor "não valida o campo `vigencia`"
— uma decisão que ninguém tomou e que nenhuma linha do comunicado sustenta; ela foi
escrita porque havia um campo sem uso óbvio no arquivo e declará-lo ignorado era mais
barato do que perguntar. O usuário detectou na revisão e determinou que a validação é
obrigatória. Ver `DECISIONS.md` [[D-010]].
**Regra afetada:** RN-017, RN-006, RN-012.

---

## 7. Casos de borda

Casos citados por `d-NNN` são despesas de `exemplos/despesas-exemplo.json`
(`CC-ENG-PLATAFORMA`); por `f-NNN`, de
`exemplos/envelope/despesas-envelope-cc-desconhecido.json` (`CC-SUPORTE-N2`); por
`e-NNN`, de `exemplos/envelope/despesas-envelope.json` (`CC-COMERCIAL`).

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Valor exatamente no limite de nota fiscal | `d-003`, valor R$100,00, sem nota fiscal | Não exige nota fiscal (limite exclusivo); segue para o limite diário | RN-005, AMB-003 |
| Valor logo acima do limite de nota fiscal, mesmo dia/categoria de despesa que já esgotou o limite diário | `d-004`, valor R$100,01, sem nota fiscal | Negado por falta de nota fiscal, não por limite diário esgotado | RN-005, RN-013, AMB-004 |
| Duas despesas idênticas exceto `id` | `d-006`/`d-007` | Primeira avaliada normalmente; segunda negada como duplicata | RN-007 |
| Despesa fora do período de competência | `d-008`, data em abril, período é julho | Negada por período de competência | RN-006 |
| Valor negativo (estorno) | `d-009`, valor -R$45,00 | Ignorada; não soma em nenhum total | RN-009 |
| Categoria ausente da tabela do centro de custo | `d-005`, categoria `coworking` em `CC-ENG-PLATAFORMA` | Negada citando que a categoria não é reembolsável para aquele centro de custo | RN-008 (cláusula 1) |
| Centro de custo sem entrada na tabela de política | `f-001`, colaborador em `CC-SUPORTE-N2` | Usa o bloco `padrao` inteiro — alimentação R$60,00 | RN-014, AMB-012 |
| Categoria reembolsável em outro centro de custo, mas ausente no do colaborador | `f-003`, `representacao` em `CC-SUPORTE-N2` | Negada — o `padrao` não tem `representacao`, e o `padrao` de um centro de custo sem entrada não é complementado por nenhuma outra tabela | RN-008, RN-014, AMB-012 |
| Categoria presente na tabela com `limite` igual a `0.00` | `d-010`, `hospedagem` em `CC-ENG-PLATAFORMA` | Negada citando a proibição explícita para o centro de custo — nunca "limite diário atingido" | RN-008 (cláusula 2), AMB-013 |
| Categoria com `limite` `0.00` **e** sem nota fiscal | `d-013`, `hospedagem` R$690,00 sem nota, em `CC-ENG-PLATAFORMA` | Negada pela categoria (passo 2), não pela nota fiscal (passo 6) — anexar a nota não mudaria o resultado | RN-008, RN-013, AMB-013 |
| Categoria de política que existe em um único centro de custo | `e-001`, `representacao` em `CC-COMERCIAL` | Tratada como qualquer outra categoria com limite diário — R$300,00 | RN-001, RN-014 |
| Despesa sem o campo `moeda` | `e-010`, R$88,00 sem `moeda` | Tratada como BRL; sai sem campo `moeda`, e com `taxa_cambio` e `valor_convertido_brl` em `null` | RN-015 |
| Despesa com `moeda` explicitamente `BRL` | `e-001`, `"moeda": "BRL"` | Idêntica ao caso acima em tudo que decide; sai com o campo `moeda` porque ele veio na entrada | RN-015 |
| Despesa internacional em data sem cotação publicada | `e-004`, EUR 30,00 em `2026-07-18` (sábado) | Negada citando moeda e data; não consome limite e não soma em `valor_total_despesas` | RN-016, AMB-015 |
| Despesa em moeda ausente do arquivo de câmbio | `e-006`, GBP 55,00 numa data que tem USD e EUR | Negada pelo mesmo motivo e com o mesmo efeito do caso acima | RN-016, AMB-016 |
| Conversão que cruza o teto de nota fiscal | `e-005`, USD 40,00 sem nota, valendo R$220,00 | Negada por nota fiscal ausente — o teto compara o valor convertido, não os 40,00 lançados | RN-005, AMB-017 |
| Conversão que **não** cruza o teto de nota fiscal | `e-003`, EUR 14,50 sem nota, valendo R$85,26 | Segue normalmente para o limite diário | RN-005, AMB-017 |
| Duas despesas idênticas exceto pela moeda | EUR 22,00 e BRL 22,00, iguais em todo o resto | **Não** são duplicatas — a identidade inclui `moeda` e compara o valor lançado | RN-007, AMB-019 |
| Política da competência do lote | `vigencia: 2026-07-01`, lote de competência `2026-07` | Processa normalmente | RN-017 |
| Política de competência anterior à do lote | `vigencia: 2026-07-01`, lote de competência `2026-08` | Processa normalmente — mês futuro pode não ter política nova, e a corrente continua valendo | RN-017, AMB-020 |
| Política de competência posterior à do lote | `vigencia: 2026-08-01`, lote de competência `2026-07` | Nada é processado: mensagem no terminal citando as duas competências, nenhum arquivo de saída, código de saída diferente de zero | RN-017 |
| Vigência no meio do período de competência | `vigencia: 2026-07-15`, lote de competência `2026-07` | Processa normalmente, e **nenhuma** despesa é negada por ser anterior a `2026-07-15` — a retroatividade cobre a competência inteira | RN-017, AMB-020 |
| Hospedagem multi-diária sem campo estruturado de noites | `f-002` ("1 diária" no texto), em centro de custo que reembolsa hospedagem | Limite do **dia** da despesa; as noites citadas no texto livre são ignoradas | RN-003, AMB-006 |
| Duas hospedagens na mesma data | dois lançamentos de `hospedagem` com a mesma `data` | Dividem o mesmo limite do dia — não recebem o limite cheio cada uma | RN-003, AMB-006 |
| Valor com mais de 2 casas decimais | `d-011`, valor `33.333` | Truncado para R$33,33 antes de qualquer verificação | RN-010 |
| Despesa em fim de semana | `d-012`, sábado, "plantão" | Tratada normalmente — a política não distingue dia útil de fim de semana | (confirma ausência de regra especial) |
| Categoria com grafia em maiúsculas | `d-014`, categoria `ALIMENTACAO` | Normalizada e tratada como `alimentacao` para decidir; devolvida como `ALIMENTACAO` na saída | RN-011, AMB-009 |
| Duas despesas idênticas exceto pela capitalização da categoria | duas despesas iguais em tudo, uma com `alimentacao` e outra com `ALIMENTACAO` | São duplicatas — a comparação de RN-007 usa a categoria já normalizada | RN-007, RN-011, AMB-009 |
| Despesa datada exatamente no primeiro ou último dia do período | qualquer despesa com `data == periodo.inicio` ou `data == periodo.fim` | Dentro do período (inclusivo) | RN-006, AMB-011 |

## 8. Ordem de aplicação das regras

Antes desta ordem começar, e antes de qualquer despesa ser avaliada, RN-017 verifica que
a política recebida vale para a competência do lote. O arquivo de despesas já foi lido
nesse ponto — é dele que sai a `periodo.competencia` que RN-017 compara —, mas nenhuma
despesa recebeu decisão ainda. Se a política não valer, nada abaixo acontece: não há
saída, e o motor encerra com mensagem no terminal. A ordem a seguir só se aplica a um
lote que passou por essa precondição.

Quando mais de uma regra de negação poderia se aplicar à mesma despesa, a ordem
abaixo define qual prevalece — cada despesa recebe **uma única justificativa**,
correspondente à primeira regra desta lista que a reprovar. Se nenhuma reprovar, o
valor reembolsável é calculado pelo limite da categoria/dia (RN-001 a RN-004).

1. **Valor negativo / estorno** (RN-009) — ignorada, nem chega a ser avaliada pelas
   regras seguintes.
2. **Categoria não reembolsável para o centro de custo** (RN-008) — a categoria, já
   normalizada (RN-011), é confrontada com a tabela aplicável ao centro de custo
   (RN-014). Cobre as duas cláusulas de RN-008: categoria ausente da tabela e categoria
   presente com `limite` igual a `0.00` (AMB-013).
3. **Fora do período de competência** (RN-006).
4. **Duplicata** (RN-007) — comparação feita entre despesas que já passaram pelas
   verificações 1–3, sobre o valor lançado e a `moeda` normalizada. Uma despesa entra
   no conjunto comparado assim que passa a verificação 3, e **continua nele mesmo que
   seja negada depois** por câmbio (passo 5), nota fiscal (passo 6) ou limite (passo 7).
   Uma despesa lançada duas vezes é o mesmo lançamento repetido independentemente de a
   primeira ocorrência ter sido reembolsada ou não; remover a primeira do conjunto por
   ela ter sido negada faria a segunda ser avaliada como se fosse original, e as duas
   somariam em `valor_total_despesas`.
5. **Câmbio indisponível** (RN-016) — só se aplica a despesa cuja `moeda` normalizada
   não é `BRL`.
6. **Nota fiscal obrigatória ausente** (RN-005) — o teto é comparado com o valor em BRL
   (RN-015).
7. **Limite diário da categoria** (RN-001, RN-002, RN-003, RN-004) — só entram nesta
   agregação as despesas que sobreviveram às verificações 1–6, na ordem em que
   aparecem na entrada, e o que se agrega é o valor em BRL.

A **conversão** de RN-015 não é um passo desta lista, porque não reprova ninguém: ela
acontece entre os passos 5 e 6 e é o que produz o valor que 6 e 7 comparam.

**Justificativa da ordem:** os quatro primeiros filtros descartam despesas que não
são, estruturalmente, elegíveis a reembolso (dado inválido, categoria não coberta pelo
centro de custo, fora do período, lançamento repetido). Nota fiscal vem antes do limite diário porque é
uma condição da despesa em si (RN-005, AMB-004). O limite diário é calculado por
último porque só faz sentido competir pelo orçamento do dia entre despesas que já
passaram por todos os outros filtros — uma despesa duplicada ou fora de política não
deve "gastar" limite de outra despesa legítima do mesmo dia.

A posição do passo 5 é **forçada, não escolhida**. Ele vem depois da duplicata porque
RN-007 compara o valor lançado e a moeda, e não precisa de conversão nenhuma para
decidir. E vem antes da nota fiscal e do limite diário porque esses dois comparam o
valor em BRL — sem taxa não existe valor em BRL, e portanto não existe pergunta a
fazer. Uma despesa sem câmbio não é "negada por nota fiscal" nem "negada por limite":
ela é inavaliável, e é isso que a justificativa precisa dizer.

## 9. Critérios de aceite

Todos os critérios abaixo são avaliados com a política de
`exemplos/envelope/politica-v4.json` e as taxas de `exemplos/envelope/cambio.json`. Os
checkboxes voltaram a ficar **marcados** quando a Fase 5 de `tasks.md` (T-028 a T-045)
reescreveu o motor sob a v4, e cada marcação corresponde a um teste automatizado, não a
conferência manual.

> A cobertura fica em `tests/test_integracao.py`, que roda a CLI de verdade (arquivo de
> entrada → arquivo de saída) e percorre esta lista item a item. Se um critério deixar de
> valer, o teste quebra antes de o checkbox ficar desatualizado.

**Precondição de todos os blocos abaixo (RN-017).** A política vigente tem
`vigencia: 2026-07-01`, competência `2026-07`, e os três arquivos de exemplo são de
competência `2026-07` — logo os três passam.

- [x] Um lote de competência `2026-08` processado com esta mesma política é aceito, e
      produz saída — RN-017, AMB-020.
- [x] Um lote de competência `2026-06` processado com esta mesma política é recusado:
      **nenhum** arquivo de saída é escrito, o terminal recebe uma mensagem citando a
      competência de vigência (`2026-07`) e a do lote (`2026-06`), e o código de saída é
      diferente de zero — RN-017.
- [x] Uma política com `vigencia: 2026-07-15` processando um lote de competência
      `2026-07` é aceita, e **nenhuma** despesa anterior a `2026-07-15` é negada por
      causa disso — RN-017, AMB-020.

**Rodando `exemplos/despesas-exemplo.json`** — colaborador em `CC-ENG-PLATAFORMA`, que
tem entrada própria na política: alimentação R$75,00, transporte urbano R$80,00 e
`hospedagem` com `limite` igual a `0.00`.

- [x] `d-001` reembolsa R$72,50 (total) e `d-002` reembolsa R$2,50 (parcial) — RN-001,
      RN-014. O limite aplicado é o R$75,00 do centro de custo, não os R$60,00 que a v3
      usava para toda a empresa.
- [x] `d-003` reembolsa R$80,00 (parcial), sem exigir nota fiscal — RN-002, RN-005.
- [x] `d-004` reembolsa R$0,00, com justificativa citando nota fiscal ausente (não
      limite diário) — RN-005, RN-013.
- [x] `d-005` reembolsa R$0,00, com justificativa citando que `coworking` não é
      reembolsável para `CC-ENG-PLATAFORMA` — RN-008 (cláusula 1).
- [x] `d-006` reembolsa R$54,90 (total); `d-007` reembolsa R$0,00, com justificativa
      citando `d-006` como duplicata original, e o valor de `d-007` não é somado em
      `valor_total_despesas` — RN-007.
- [x] `d-008` reembolsa R$0,00, com justificativa citando período de competência —
      RN-006.
- [x] `d-009` aparece no detalhamento com R$0,00, mas não é somado em
      `valor_total_despesas` nem em `valor_total_reembolsavel` — RN-009.
- [x] `d-010` reembolsa R$0,00, com justificativa citando que `hospedagem` não é
      reembolsável para `CC-ENG-PLATAFORMA` — RN-008 (cláusula 2), AMB-013. Seu valor
      (R$480,00) **continua** somando em `valor_total_despesas`: foi gasto real.
- [x] `d-011` reembolsa R$33,33 (total, valor truncado de `33.333`) — RN-010.
- [x] `d-012` reembolsa R$47,20 (total), sem nenhuma restrição por ser fim de semana.
- [x] `d-013` reembolsa R$0,00, com justificativa citando a categoria não reembolsável —
      RN-008 (cláusula 2), RN-013. A nota fiscal ausente **não** é a justificativa:
      RN-008 é o passo 2 da ordem e RN-005 é o passo 6.
- [x] `d-014` reembolsa R$61,00 (total), com a categoria `ALIMENTACAO` tratada como
      `alimentacao` — RN-011, RN-014. Sob o limite de R$75,00 do centro de custo o valor
      cabe inteiro; sob os R$60,00 da v3 era parcial.
- [x] `valor_total_despesas` = R$1.806,94 (exclui a duplicata `d-007` e o estorno
      `d-009`) e `valor_total_reembolsavel` = R$351,43 — RN-007, RN-009, RN-014. O total
      bruto **não mudou** com a v4, porque não depende de limite; o reembolsável caiu de
      R$585,43 para R$351,43.
- [x] Nenhuma despesa recebe o adicional de `acrescimo_em_viagem_percentual` por
      "viagem" em nenhuma circunstância — RN-012.
- [x] Toda despesa deste arquivo sai com `taxa_cambio` e `valor_convertido_brl` em
      `null`, e nenhuma ganha um campo `moeda` que não veio na entrada — RN-015,
      spec.md §4 ("Entrada e saída").
- [x] O **texto** do JSON de saída é idêntico ao de `exemplos/resultado-exemplo.json`:
      `valor_reembolsavel` e os dois totais saem com exatamente 2 casas decimais
      (`72.50`, `0.00`), e os campos ecoados saem com a escala lançada (`72.50`,
      `33.333`) — spec.md §4 ("Entrada e saída"). Este critério é sobre o texto, não
      sobre o resultado do *parsing*: comparar os dois arquivos como estruturas de dados
      não distingue `60.0` de `60.00`.

**Rodando `exemplos/envelope/despesas-envelope-cc-desconhecido.json`** — colaborador em
`CC-SUPORTE-N2`, que **não** tem entrada em `centros_custo` e portanto cai no `padrao`:
alimentação R$60,00, transporte urbano R$80,00 e hospedagem R$250,00.

- [x] `f-001` (alimentação R$58,00) reembolsa R$58,00 (total) — RN-001, RN-014.
- [x] `f-002` (hospedagem R$310,00) reembolsa R$250,00 (parcial) — RN-003, RN-014.
- [x] `f-003` (`representacao` R$190,00) reembolsa R$0,00, com justificativa citando que
      `representacao` não é reembolsável para `CC-SUPORTE-N2` — RN-008 (cláusula 1),
      RN-014, AMB-012. O valor **soma** em `valor_total_despesas`.
- [x] `f-004` (USD 12,00 em `2026-07-21`, taxa 5,48) reembolsa R$65,76 (total), com
      `taxa_cambio` = `5.48` e `valor_convertido_brl` = `65.76` — RN-015. O limite de
      transporte urbano do `padrao` é R$80,00 e o valor cabe inteiro.
- [x] `valor_total_despesas` = R$623,76 e `valor_total_reembolsavel` = R$373,76 —
      RN-014, RN-015.

**Rodando `exemplos/envelope/despesas-envelope.json`** — colaborador em `CC-COMERCIAL`,
com entrada própria na política: alimentação R$90,00, transporte urbano R$150,00,
hospedagem R$400,00 e `representacao` R$300,00.

- [x] `e-001` (`representacao` R$340,00, `"moeda": "BRL"`) reembolsa R$300,00 (parcial),
      com `taxa_cambio` e `valor_convertido_brl` em `null` — RN-001, RN-014, RN-015.
- [x] `e-002` (alimentação EUR 22,00 em `2026-07-14`) tem `taxa_cambio` = `5.93` e
      `valor_convertido_brl` = `130.46`, e reembolsa R$90,00 (parcial) — RN-015, RN-001.
      O `valor` sai como `22.00`, na moeda lançada.
- [x] `e-003` (alimentação EUR 14,50 em `2026-07-15`, **sem** nota fiscal) tem
      `valor_convertido_brl` = `85.26` e reembolsa R$85,26 (total): não cruza o teto de
      nota fiscal, que é comparado contra os R$85,26 — RN-005, RN-015, AMB-017.
- [x] `e-004` (alimentação EUR 30,00 em `2026-07-18`, sábado sem cotação) reembolsa
      R$0,00, com `taxa_cambio` e `valor_convertido_brl` em `null` e justificativa
      citando a moeda `EUR` e a data `2026-07-18`. **Não** soma em
      `valor_total_despesas` e **não** consome limite de alimentação daquele dia —
      RN-016, AMB-015.
- [x] `e-005` (transporte USD 40,00 em `2026-07-20`, **sem** nota fiscal) tem
      `valor_convertido_brl` = `220.00` e reembolsa R$0,00, com justificativa citando
      nota fiscal ausente. Soma R$220,00 em `valor_total_despesas` — RN-005, RN-015,
      AMB-017.
- [x] `e-006` (`representacao` GBP 55,00 em `2026-07-21`) reembolsa R$0,00, com
      justificativa citando a moeda `GBP` e a data. **Não** soma em
      `valor_total_despesas` — RN-016, AMB-016. A data tem cotação de USD e EUR, e ainda
      assim a despesa é negada: o que falta é a moeda, não a data.
- [x] `e-007` (hospedagem R$1.200,00) reembolsa R$400,00 (parcial) — RN-003, RN-014.
- [x] `e-008` (alimentação R$95,00) reembolsa R$90,00 (parcial) — RN-001, RN-014.
- [x] `e-009` (`coworking` R$120,00) reembolsa R$0,00, com justificativa citando que
      `coworking` não é reembolsável para `CC-COMERCIAL` — RN-008 (cláusula 1). Soma em
      `valor_total_despesas`.
- [x] `e-010` (alimentação R$88,00, **sem** o campo `moeda`) reembolsa R$88,00 (total),
      e sai **sem** campo `moeda` — RN-015.
- [x] `valor_total_despesas` = R$2.278,72 e `valor_total_reembolsavel` = R$1.053,26 —
      RN-014, RN-015, RN-016. O total bruto exclui `e-004` e `e-006`, as duas despesas
      sem valor em BRL, e inclui `e-005` e `e-009`, que têm valor em BRL e foram negadas
      por outros motivos.

## 10. O que fica em aberto

- **Adicional de viagem (RN-012 / AMB-005):** não implementado.
  A entrada não tem campo que identifique viagem, e qualquer inferência seria uma
  regra de negócio nova não solicitada pelo RH. Se um campo explícito de viagem for
  adicionado à entrada no futuro, esta regra precisa ser reaberta.
- **Limite de hospedagem por noite real (RN-003 / AMB-006):** o sistema aplica o
  limite de hospedagem do centro de custo por **dia de calendário**, porque a entrada
  não tem campo estruturado de número de noites. Isso é mais restritivo do que a
  política provavelmente pretende quando um lançamento cobre várias noites (ex.:
  `f-002`, R$310,00 numa diária, contra o limite de R$250,00 do `padrao`; ou um
  lançamento de R$480,00 por 2 noites reais, cuja taxa de R$240,00/noite caberia no
  limite se ele fosse por noite). Se a entrada ganhar um campo estruturado de número de
  diárias, esta regra precisa ser reaberta.
- **Fim de vigência da política (RN-017):** a política tem `vigencia` de início e não
  tem data de fim. RN-017 aceita toda política cuja competência de vigência seja igual
  ou anterior à do lote, então uma política revogada continua sendo aceita
  indefinidamente — o motor não tem como saber que ela foi substituída. Se o arquivo
  ganhar um `fim_vigencia`, ou se o financeiro passar a manter mais de uma política
  vigente em paralelo, RN-017 precisa ser reaberta.
- **Periodicidade da política (RN-003 / AMB-006):** o campo `periodicidade` é ecoado e
  não interpretado — `"dia"` e `"diaria"` são ambos aplicados como dia de calendário. Um
  valor novo nesse campo (ex.: `"mes"`) seria silenciosamente tratado como diário. Se a
  política passar a usar mais de uma periodicidade de verdade, esta regra precisa ser
  reaberta.
- **Centro de custo com tabela incompleta (RN-014 / AMB-012):** como a tabela de um
  centro de custo que existe é fechada, um centro de custo cadastrado com uma categoria
  faltando nega despesa legítima até alguém corrigir o arquivo de política. É o preço
  conhecido da decisão de AMB-012, e o motor não tem como distinguir "faltou cadastrar"
  de "não é reembolsável mesmo".
- **Cotação de dia não útil (RN-016 / AMB-015) — o item mais provável de ser
  reaberto.** O arquivo de câmbio só publica em dia útil bancário, e o motor nega toda
  despesa internacional lançada num dia sem cotação. `e-004` (um almoço de sábado em
  Lisboa) é uma despesa legítima negada por um motivo que não tem nada a ver com ela.
  A prática de mercado é usar a cotação do último dia útil anterior, e é bem possível
  que seja isso que o RH quer. A decisão de negar foi tomada porque a alternativa exige
  escolher sozinho qual data usar, quantos dias aceitar voltar e o que fazer no início
  do arquivo — decisões que a política não sustenta hoje. **Basta o RH responder uma
  pergunta** ("qual taxa usar quando não há cotação na data?") para que RN-016 seja
  reaberta e AMB-015 revista.
- **Intervalo coberto pelo arquivo de câmbio (RN-016 / AMB-015):** as taxas vão de
  `2026-07-13` a `2026-07-28`, e o período de competência dos exemplos é o mês inteiro.
  Uma despesa internacional em `2026-07-05` seria negada por ausência de cotação, e não
  há nada no arquivo que distinga "data que o arquivo não cobre" de "data sem cotação
  publicada". Enquanto a fonte de câmbio for um arquivo entregue junto do lote, esse
  risco é do processo, não do motor.
- **Moedas publicadas (RN-016 / AMB-016):** o arquivo cobre USD e EUR. Qualquer outra
  moeda é negada, incluindo `e-006` em GBP, que é uma despesa perfeitamente legítima. A
  correção é do lado do financeiro (publicar a cotação), não do motor.
- **Item C do comunicado da v4 (fila de aprovação manual):** itens com valor
  reembolsável acima de R$500,00 deixarem de ser aprovados automaticamente, passando a
  ter um **estado** além do valor. Está fora de escopo por decisão do usuário, e não
  por falta de clareza. Implementá-lo mudaria o contrato de saída da spec.md §4
  ("Entrada e saída"), acrescentando um campo de estado a
  `motor_reembolso_output` — não é uma regra que se encaixe sem tocar no contrato.
