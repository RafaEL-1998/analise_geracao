# Bug Fix: código de programação exigido mesmo sem a programação na cobertura

- **Slug**: programacao-sem-cobertura
- **Fixed**: 2026-10-26
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

O código de programação passou a ser obrigatório só quando a Programação diária é coletada: sem a `[cobertura]` (a UHE de hoje, como a São Domingos) ou com a programação `proprio` ou `conjunto`. Com a programação `ausente`, o código não é exigido e, se informado, é aceito e não é usado (decisão do usuário de 26/10/2026).

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/comum/perfil_campos.py` | modified | `identificacao.cod_programacao` na tabela `CAMPOS`, com `_c("programacao")` em todos os grupos |
| `src/comum/perfil.py` | modified | `_programacao_exigida()`; o código é lido como obrigatório só nesses casos; o primeiro código vira `""` quando não há código (antes, `codigos_programacao[0]` quebraria) |
| `tests/comum/test_perfil.py` | added tests | quatro casos (abaixo) |
| `specs/001-coleta-dados/spec.md` | modified | regra do campo e linha nas decisões do usuário (26/10/2026) |
| `specs/001-coleta-dados/data-model.md` | modified | regra do campo |
| `specs/001-coleta-dados/contracts/perfil-usina.md` | modified | exigência por tipo: "O sem a `[cobertura]`; C: programação" na UHE e "C: programação" nos demais |

Antes da mudança: cópia de segurança `_backup_2026-10-26_antes_correcoes_homologacao` (540 arquivos; a de 23/10, `antes_fechamento`, saiu pela regra de no máximo duas).

## Diff Highlights

```python
def _programacao_exigida(le, tipo, cobertura) -> bool:
    if tipo is None or le.dados.get("cobertura") is None:
        return True
    return perfil_campos.exigido_pela_cobertura("identificacao.cod_programacao", tipo, cobertura) is not None
```

## Tests Added or Updated

- `tests/comum/test_perfil.py::test_sem_programacao_na_cobertura_o_codigo_nao_e_exigido` — programação `ausente` e sem código: perfil válido, `cod_programacao == ""`.
- `tests/comum/test_perfil.py::test_com_programacao_na_cobertura_o_codigo_continua_obrigatorio` — programação `proprio` sem código: a recusa de hoje.
- `tests/comum/test_perfil.py::test_codigo_informado_com_programacao_ausente_e_aceito` — a decisão do usuário: o código fica, sem uso.
- `tests/comum/test_perfil.py::test_uhe_sem_cobertura_continua_exigindo_o_codigo` — a UHE sem `[cobertura]` (São Domingos) continua exigindo o código.

## Local Verification

- `pytest tests/comum/test_perfil.py` → 52 aprovados.
- `pytest tests/comum tests/coleta` → 348 aprovados; `pytest tests/integracao tests/relatorio/test_invariantes_uhe.py` → 96 aprovados; `pyflakes src tests` → limpo.
- `python -m src comparar --todas` → código 0, as cinco referências sem diferença.
- Homologação refeita, num espaço isolado, nas três usinas do achado:
  - UTN Angra II e UTN Angra I: perfil válido e relatório gerado (código 0), sem a seção da programação.
  - UTE Três Lagoas: perfil válido; a execução segue até as Análises e para com outro defeito (abaixo).

## Deviations from Assessment

- Escopo ampliado em `src/comum/perfil.py`: o primeiro código (`codigos_programacao[0]`) quebraria com a lista vazia, que antes era impossível; passou a `""`. As etapas que usam o código já dependem de a programação ser coletada.
- O assessment não previa a UHE sem `[cobertura]`: nela a programação é coletada sem estar na cobertura (`CHAVES_SEM_COBERTURA`), e o código continua obrigatório.

## Follow-ups

- **Defeito novo, a avaliar à parte** (`/speckit-bug-assess`): a UTE Três Lagoas tem as unidades identificadas por letras e algarismos ("1A", "1B", "2A", "2B", "1C", "2C"); `numero_ug` (`src/tratamento/indicadores.py:98`) só aceita algarismos, e todas as 16 linhas ficam sem unidade. As tabelas por unidade juntam as unidades, e a regra C10 quebra em `_unidades_agrupadas` (`src/analises/conclusao.py:340`, `int(NaN)`). Atinge usinas a ciclo combinado; era escondido pela recusa do perfil.
- A ligação dos códigos "MSTLA - 618" etc. à Três Lagoas (melhoria 5) devolve a ela a seção da programação.
