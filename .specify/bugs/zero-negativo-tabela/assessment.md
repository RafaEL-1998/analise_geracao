# Bug Assessment: zero negativo ("-0,0") nas tabelas

- **Slug**: zero-negativo-tabela
- **Created**: 2026-10-26
- **Source**: pasted text (achado 7 de `propostas/2026-10-26-homologacao-lote-1.md`)
- **Verdict**: valid
- **Severity**: low

## Report (verbatim or summarized)

> Tabela "Geração programada × verificada por mês" das PCH do conjunto de Chapadão: "| jan/2025 | 744 | 55,5 | 55,5 | -0,0 | 6,1 | 0 |" e "| ago/2025 | 720 | 41,1 | 41,1 | -0,0 | 2,2 | 0 |". As mesmas duas células estão na referência aprovada da PCH Bandeirante (`relatorios_referencia/bandeirante/relatorio_analise_estatistica.md`, linhas 243 e 250).

## Symptom

Um valor negativo pequeno, arredondado para zero, aparece como "-0,0"; o esperado é "0,0".

## Reproduction

1. `fmt_num(-0.04, 1)` devolve "-0,0" (o Python formata `f"{-0.04:,.1f}"` como "-0.0").
2. No relatório de qualquer usina com um desvio médio mensal entre −0,05 e 0 MW, a célula sai "-0,0".

## Suspected Code Paths

- `src/comum/formatacao.py:26-32` (`fmt_num`) — formata o valor com o sinal antes de saber se o arredondado é zero; `fmt_pct` usa `fmt_num`.
- Usos com sinal: `src/relatorio/comum.py:470` (desvio médio mensal da programação), `src/relatorio/secoes_termica.py:121` e `src/relatorio/secoes_renovavel.py:149` (desvio por hora).

## Root Cause Hypothesis

Comportamento padrão da formatação de ponto flutuante do Python, sem tratamento no formatador do projeto. Confiança: alta.

## Proposed Remediation

**Preferred**: em `fmt_num`, depois de formatar, tirar o sinal quando o texto arredondado é zero (só zeros e separadores). A correção vale para todo o projeto e não muda nenhum outro valor. A diferença de p.p. das taxas operativas já trata o mesmo caso (`_pp` em `src/relatorio/conteudo.py`); com a correção no `fmt_num`, aquele ajuste local continua necessário só para o sinal "+" do `fmt_pp`.

**Files likely to change**:
- `src/comum/formatacao.py`
- `tests/comum/test_formatacao.py` (novo: hoje não há teste dos formatadores)

**Tests to add or update**:
- `fmt_num(-0.04, 1) == "0,0"`, `fmt_num(-0.004, 2) == "0,00"`, `fmt_num(-0.06, 1) == "-0,1"`, `fmt_pct(-0.01, 1) == "0,0%"`.

## Risks & Considerations

- Princípio IX: muda a referência aprovada da PCH Bandeirante (duas células, jan/2025 e ago/2025, de "-0,0" para "0,0"); exige a aprovação do usuário e o novo registro da referência. Nenhuma outra referência tem zero negativo (conferido em 26/10/2026).

## Open Questions

- Nenhuma.
