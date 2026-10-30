# Bug Verification: código de programação exigido mesmo sem a programação na cobertura

- **Slug**: programacao-sem-cobertura
- **Tested**: 2026-10-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

O sintoma não se repete. Com o código de antes da correção (commit `bdddeff`, pai de `10b40ee`, onde a correção entrou), UTN Angra I, UTN Angra II e UTE Três Lagoas são recusadas por um único problema, `identificacao.cod_programacao: campo obrigatório ausente`. Com o código atual, as três geram o relatório completo, sem a seção da programação e sem nenhum "None" no texto. As cinco referências saem idênticas antes e depois da correção. Nenhuma regressão.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reprodução antes da correção | código de `bdddeff` num espaço isolado: `perfil --ceg <CEG>`, rascunho aceito só com os dados do ONS, `completo --sem-portal` | pass (reproduz) | as três: perfil recusado (código 4), com o único problema `identificacao.cod_programacao: campo obrigatório ausente` |
| Reprodução depois da correção | o mesmo, com o código atual, num espaço isolado novo | pass | as três: código 0. Angra I e II com 14 seções e 23 páginas; Três Lagoas com 12 seções e 28 páginas. A "Programação diária × geração verificada" aparece entre as omitidas |
| Código vazio no texto (risco da avaliação) | busca de "None" nos Markdown e CSV gerados das três | pass | nenhuma ocorrência |
| Testes novos e alterados | `pytest tests/comum/test_perfil.py` (dentro da suíte) | pass | os quatro casos do `fix.md` aprovados |
| Suíte de regressão | `python -m pytest tests` no commit `ff0e449` | pass | 896 aprovados (pandas 3.0.6) |
| Lint | `python -m pyflakes src tests anexos` | pass | limpo |
| Princípio IX, só esta correção | as cinco referências com o código de `bdddeff` e com o de `10b40ee`, num espaço isolado, `completo --sem-portal` e `comparar` | pass | as cinco sem nenhuma diferença |
| Princípio IX, código atual | as cinco referências com o código de `10b40ee` e com o atual | pass | só as duas células da Bandeirante do bug `zero-negativo-tabela` (aprovadas em 29/10/2026). Na correção, em 26/10/2026, o `comparar --todas` contra as referências congeladas deu código 0 (`fix.md`) |
| Rascunho de usinas com a programação | `perfil --ceg` das cinco referências, com os dois códigos | pass | código 0; as cinco têm a programação, e o código continua obrigatório nelas |

Scripts e logs no scratchpad da sessão: `C:\Users\PICHAU\AppData\Local\Temp\claude\c--Users-PICHAU-analise-geracao-analise-geracao\7763ea5b-483c-4e7a-a4a5-045980cb5d12\scratchpad\teste\rodar_bugs.sh` (logs em `casos\`, saída em `resultado_bugs.txt`) e `resultado_pre_prog.txt` (referências com o código de `bdddeff`).

## Output Excerpts

Código de antes (`bdddeff`), as três usinas:

```
pre_prog utn_angra_i     perfil=0 rascunho=sim completo=4   - identificacao.cod_programacao: campo obrigatório ausente
pre_prog utn_angra_ii    perfil=0 rascunho=sim completo=4   - identificacao.cod_programacao: campo obrigatório ausente
pre_prog ute_tres_lagoas perfil=0 rascunho=sim completo=4   - identificacao.cod_programacao: campo obrigatório ausente
```

Código atual:

```
novo utn_angra_i  completo=0  "programacao": false  "omitidos": ["Programação diária × geração verificada", ...]  "secoes": 14, "paginas_pdf": 23
novo utn_angra_ii completo=0  (idem)
novo ute_tres_lagoas completo=0  "secoes": 12, "paginas_pdf": 28
None no relatório/resumo/CSV: 0 (nas três)
```

Referências, código de `bdddeff` × `10b40ee`: `Nenhuma diferença.` nas cinco.

## Residual Risks

- A Três Lagoas, a Angra I e a Angra II ficam sem a seção da programação até a ligação dos códigos publicados como "MSTLA - 618" (melhoria 5).
- A Três Lagoas só gera o relatório inteiro com a correção do bug `unidade-com-letra`, que veio depois e está verificada à parte.
- Nesta máquina, o princípio IX foi conferido contra o código anterior, e não contra as referências congeladas. Na correção, o `comparar --todas` rodou na outra máquina e deu código 0.

## Recommendation

Fechar o bug: está verificado com as três usinas reais da homologação, antes e depois, e a correção isolada não muda nenhuma referência.
