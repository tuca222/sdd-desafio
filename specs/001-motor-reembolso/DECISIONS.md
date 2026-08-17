# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

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
