# Bug Fix: UHE sem EVT recusada pelos campos da trilha da EVT

- **Slug**: uhe-sem-evt-campos-evt
- **Fixed**: 2026-10-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Na UHE com a `[cobertura]`, os campos da trilha da EVT passaram a seguir a cobertura, como na PCH e na CGH: garantia física, IP e TEIF de referência e `[analises]` obrigatórios só com a EVT (opcionais sem ela, decisão do usuário de 26/10/2026); parâmetros hidráulicos, `cod_usina` e `nome_ons` com a EVT ou a hidrologia; `id_reservatorio` com a hidrologia. A UHE sem `[cobertura]` (São Domingos) continua com todos os campos obrigatórios e as mesmas mensagens.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/comum/perfil_campos.py` | modified | grupo `"UHE"` da tabela `CAMPOS` com `_EVT_OU_HIDROLOGIA`, `_c("hidrologia")` e `_c("evt")`; docstring |
| `src/comum/perfil.py` | modified | `_campo_por_tipo`: na UHE sem `[cobertura]`, o campo `C` conta como `O` |
| `tests/comum/test_perfil.py` | added tests | seis casos (abaixo) |
| `specs/001-coleta-dados/spec.md` | modified | tabela de exigência por tipo, texto abaixo dela, cenário de aceitação 2 e linha nas decisões do usuário |
| `specs/001-coleta-dados/data-model.md` | modified | tabela da seção 5.1 |
| `specs/001-coleta-dados/contracts/perfil-usina.md` | modified | colunas da UHE em `[identificacao]` e `[parametros]`; texto de `[analises]` |

## Diff Highlights

```python
e = perfil_campos.exigencia(campo, tipo)
if e.nivel == COM_COBERTURA and tipo == "UHE" and le.dados.get("cobertura") is None:
    e = perfil_campos.O  # UHE sem a [cobertura] (a de hoje): coleta os conjuntos de hoje, com a EVT
```

## Tests Added or Updated

- `tests/comum/test_perfil.py::test_uhe_sem_evt_nem_hidrologia_dispensa_os_campos_da_trilha_da_evt` — perfil válido sem os hidráulicos, sem `[analises]` e sem garantia física, IP e TEIF.
- `tests/comum/test_perfil.py::test_uhe_sem_evt_com_hidrologia_exige_os_hidraulicos_e_o_reservatorio` — exige hidráulicos, `cod_usina` e `id_reservatorio`; não exige `[analises]` nem garantia física, IP e TEIF.
- `tests/comum/test_perfil.py::test_uhe_com_evt_na_cobertura_exige_todos_os_campos_da_trilha_da_evt` — com `evt = "proprio"`, todos exigidos.
- `tests/comum/test_perfil.py::test_uhe_sem_cobertura_continua_exigindo_os_campos_da_trilha_da_evt` (três casos) — São Domingos sem `queda_bruta_m`, `ip_referencia` ou `vertimento_minimo_m3s`: a mensagem de hoje ("campo obrigatório ausente").

## Local Verification

- `pytest tests/comum/test_perfil.py` → 58 aprovados.
- Com o catálogo real de 29/10/2026 e o código corrigido (perfis gravados fora de `usinas/`), rascunho aceito só com os dados do ONS:
  - UHE Canastra (`UHE.PH.RS.000635-1.01`) e UHE Pimental (`UHE.PH.PA.030354-2.01`), sem EVT e com hidrologia: recusadas só pelos seis parâmetros hidráulicos; garantia física, IP, TEIF e `[analises]` não são mais exigidos;
  - UHE Anta (`UHE.PH.MG.029458-6.02`), sem EVT nem hidrologia: recusada só pelo cadastro que o ONS não publica (início, potência, unidades) e pelo código de programação que o catálogo não liga (melhoria 5).
- `python -m pytest tests` → 888 aprovados (29/10/2026, pandas 3.0.6; com os dados reais em `data/`, os 3 testes que antes eram pulados também rodam).
- `python -m pyflakes src tests anexos` → limpo.
- Princípio IX: a Coleta congelada das referências não existe nesta máquina (fora do git), e o `comparar --todas` não roda aqui; a cópia de segurança (`copia-seguranca`) também recusa, pelo mesmo motivo, e o estado anterior fica no git (commit `10b40ee`). No lugar, com os dados baixados do portal em 29/10/2026:
  - linha de base: `completo` das cinco usinas com referência, com o código do commit `10b40ee` e `--data-geracao "29/10/2026 08:00"`;
  - depois da correção: `completo --sem-portal` com a mesma data e `comparar --usina <slug> --referencia <linha de base>`;
  - São Domingos, William Arjona, Seriemas 1 e Praia Formosa: PDF, Markdown, CSV e figuras iguais; só a aba `DICIONARIOS` da planilha difere (situação e horário de obtenção dos dicionários, que as coletas das usinas seguintes obtiveram de novo em `data/raw/`; nenhuma correção mexe nela);
  - Bandeirante: só as duas células da tabela "Geração programada × verificada por mês" (jan/2025 e ago/2025), de "-0,0" para "0,0" (bug `zero-negativo-tabela`), no Markdown e no PDF.

## Deviations from Assessment

- A avaliação não previa a UHE sem `[cobertura]`: sem a tabela, os campos `C` não seriam disparados por nenhuma cobertura, e a São Domingos deixaria de exigir, por exemplo, a garantia física. A regra explícita em `_campo_por_tipo` mantém o comportamento e as mensagens de hoje, como `_programacao_exigida` já faz para o código de programação.

## Follow-ups

- Canastra e Pimental (UHE sem EVT com hidrologia) continuam exigindo os seis parâmetros hidráulicos, porque a trilha com hidrologia usa o engolimento; rodá-las só com dados do ONS depende do achado 2 da homologação (decisão de desenho à parte).
