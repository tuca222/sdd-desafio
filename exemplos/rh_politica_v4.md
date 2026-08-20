> **Comunicado do RH — Política de Reembolso v4**
>
> Vigência imediata, retroativa à competência atual.
>
> Após auditoria interna, a política deixa de ser única para toda a empresa.
>
> **A. Limites passam a variar por centro de custo.**
> Os limites não são mais constantes. Cada centro de custo tem a sua tabela, mantida pelo financeiro num arquivo à parte, e ela muda sem aviso. O motor precisa ler a política de fora, não de dentro do código.
>
> A tabela vigente está em `politica-v4.json`.
>
> Observações que o financeiro fez questão de incluir:
> - `CC-COMERCIAL` tem uma categoria nova, `representacao`, que não existia na v3 — limite de R$ 300 por dia.
> - `CC-ENG-PLATAFORMA` não reembolsa `hospedagem` de forma alguma.
> - Alguns centros de custo não têm entrada na tabela. Nesse caso, aplica-se a política padrão.
>
> **B. Despesas internacionais.**
> Colaboradores em viagem internacional lançam despesas em moeda estrangeira. A entrada agora pode trazer um campo `moeda` (ISO 4217). Quando ausente, assume-se `BRL`.
>
> A conversão usa a **taxa da data da despesa**, não a taxa de hoje. As taxas estão em `cambio.json`.
>
> Os limites da política são sempre em BRL. Uma despesa em EUR é convertida antes de ser comparada ao limite.
>
> **C. (Opcional — só se sobrar tempo) Fila de aprovação manual.**
> Itens cujo valor reembolsável passe de R$ 500 não são mais aprovados automaticamente. Eles entram em estado de pendência aguardando aprovação do gestor. O resultado deixa de ser apenas um valor: cada item passa a ter um estado.
