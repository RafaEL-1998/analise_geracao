# Bug Assessment: código de programação exigido mesmo sem a programação na cobertura

- **Slug**: programacao-sem-cobertura
- **Created**: 2026-10-26
- **Source**: pasted text (achado 3 de `propostas/2026-10-26-homologacao-lote-1.md`)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

> UTE Três Lagoas (MS), UTN Angra I e UTN Angra II (RJ): perfil recusado com um único problema, "identificacao.cod_programacao: campo obrigatório ausente", embora a `[cobertura]` do rascunho traga `programacao = "ausente"`.

## Symptom

A conferência do perfil exige `identificacao.cod_programacao` de toda usina, mesmo quando a cobertura diz que a Programação diária não tem a usina; o esperado é exigir o código só quando a programação é coletada (`proprio` ou `conjunto`), como os demais identificadores.

## Reproduction

1. `python -m src perfil --ceg UTE.GN.MS.027975-7.01 --slug ute_tres_lagoas`: o rascunho deixa `codigos_programacao` pendente ("nenhum código ligado pelo id ONS nem pelo conjunto") e grava `programacao = "ausente"`.
2. Aceitar o rascunho só com os dados do ONS (`situacao = "conferido"`, `pendentes = []`, fonte preenchida).
3. `python -m src completo --usina ute_tres_lagoas`: perfil recusado por `identificacao.cod_programacao`.

## Suspected Code Paths

- `src/comum/perfil.py:461-471` — sem `codigos_programacao`, `le.texto("identificacao.cod_programacao")` é chamado como obrigatório, sem olhar a cobertura (`c["cobertura"]`, calculada na linha 460).
- `src/comum/perfil_campos.py:CAMPOS` — os outros identificadores (`id_ons`, `cod_usina`, `id_reservatorio`, `id_conjunto`) passam por `_campo_por_tipo`, com a exigência pela cobertura; o código de programação não está na tabela.
- Relacionado, não é este bug: `src/coleta/perfil_rascunho.py` liga os códigos só pelo id ONS ou pelo id do conjunto; os códigos publicados como "MSTLA - 618" (Três Lagoas, id ONS MSUTLG) não são ligados (melhoria 5 de `propostas/2026-10-23-melhorias-futuras.md`).

## Root Cause Hypothesis

O código de programação ficou obrigatório desde a São Domingos, que sempre teve a programação; quando a cobertura passou a declarar cada conjunto (fase A), os identificadores foram para a tabela por tipo e cobertura, mas o código de programação continuou fora dela. Confiança: alta.

## Proposed Remediation

**Preferred**: acrescentar `identificacao.cod_programacao` à tabela `CAMPOS` com a exigência `_c("programacao")` em todos os grupos, e, em `perfil.py`, ler o código como obrigatório só quando a cobertura da programação é `proprio` ou `conjunto` (`le.texto(..., obrigatorio=...)`); com a programação `ausente`, o código é opcional e, se vier, é recusado como os demais campos que não se aplicam (ou aceito: ver a pergunta abaixo).

Com isso, Três Lagoas e Angra I e II rodam sem a seção da programação. A ligação dos códigos "MSTLA - 618" (melhoria 5) devolve a programação a essas usinas depois.

**Files likely to change**:
- `src/comum/perfil_campos.py`, `src/comum/perfil.py`
- `specs/001-coleta-dados/spec.md` e `data-model.md` (campos do perfil)
- `tests/comum/test_perfil.py`

**Tests to add or update**:
- Perfil com `programacao = "ausente"` e sem código: válido.
- Perfil com `programacao = "proprio"` e sem código: recusado, com a mensagem de hoje.
- As fictícias e as referências seguem iguais (todas têm a programação).

## Risks & Considerations

- Conferir que nenhuma etapa lê `identificacao.cod_programacao` sem antes olhar a cobertura (registro dos conjuntos, parâmetros e notas do relatório); um código vazio não pode virar texto "None" no relatório.
- Princípio IX: as cinco referências têm a programação; `comparar --todas` deve dar código 0.

## Open Questions

- Respondida pelo usuário em 26/10/2026 ("I find that reasonable"): com a programação `ausente`, um código informado no perfil é aceito e não é usado.
