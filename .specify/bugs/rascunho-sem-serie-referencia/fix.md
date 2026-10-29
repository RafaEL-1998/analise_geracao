# Bug Fix: rascunho do perfil aceito para usina sem série de referência

- **Slug**: rascunho-sem-serie-referencia
- **Fixed**: 2026-10-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

O comando `perfil` passou a recusar (código 2, sem gravar) a usina sem a série de referência da Coleta, com a mesma regra: `serie_referencia.escolher_pela_cobertura(tipo, cobertura)`, usada pela Coleta (`escolher`, sobre o perfil) e pelo rascunho (sobre a cobertura do catálogo). A mensagem diz os conjuntos de série que o catálogo encontra e que a usina não tem relatório individual. A coluna da série de referência no catálogo ficou para a melhoria 5, como o usuário decidiu.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/coleta/registro.py` | modified | `conjuntos_pela_cobertura(tipo, cobertura)` e `nivel_na_cobertura(chave, cobertura)`; `conjuntos_da_usina` passa a usar a primeira, com o mesmo filtro do campo de `[usina]` |
| `src/coleta/serie_referencia.py` | modified | `escolher_pela_cobertura` (None sem série); `escolher` a chama e levanta o mesmo `ValueError` de hoje |
| `src/coleta/perfil_rascunho.py` | modified | `_cobertura(catalogo, ceg)`, usada por `_esperado` e por `_resolver_usina`; recusa nova em `_resolver_usina`; docstring |
| `tests/coleta/test_perfil_rascunho.py` | added tests | quatro casos (abaixo) |
| `specs/001-coleta-dados/spec.md` | modified | FR-053, tabela de códigos do `perfil` e linha nas decisões do usuário |
| `specs/001-coleta-dados/contracts/cli-perfil.md` | modified | passo 5, código 2 e a mensagem obrigatória nova |

## Diff Highlights

```python
cobertura = _cobertura(catalogo, u["ceg"])
if escolher_pela_cobertura(u["tipo"], cobertura) is None:  # a mesma regra da Coleta
    ...
    return None, CODIGO_INVALIDO, ("O ONS não publica a série de referência da usina ...")
```

## Tests Added or Updated

- `tests/coleta/test_perfil_rascunho.py::test_usina_so_com_a_programacao_e_recusada_no_rascunho` — UTE do catálogo fictício só com a programação: código 2, mensagem, nada gravado.
- `tests/coleta/test_perfil_rascunho.py::test_usina_com_a_geracao_do_conjunto_continua_com_rascunho` — PCH em conjunto sem série própria (como a Bandeirante): rascunho gravado.
- `tests/coleta/test_perfil_rascunho.py::test_solar_em_conjunto_com_a_restricao_com_detalhe_propria_continua_com_rascunho` — UFV em conjunto com a restrição com detalhe própria (como a Seriemas 1): rascunho gravado.
- `tests/coleta/test_perfil_rascunho.py::test_solar_so_com_a_razao_da_restricao_do_conjunto_e_recusada` — UFV sem geração nem restrição com detalhe: código 2, com "nem a restrição com detalhe da usina".
- Os testes da série de referência (`tests/coleta/test_serie_referencia.py`) e do registro (`tests/coleta/test_registro.py`) seguem iguais e passam: `escolher` tem o mesmo comportamento.

## Local Verification

- `pytest tests/coleta/test_perfil_rascunho.py tests/coleta/test_serie_referencia.py tests/coleta/test_registro.py` → aprovados.
- Com o catálogo real de 29/10/2026: UTE Suzano RRP1 e Amandina II (só a programação própria) e Fibria MS (só a programação do conjunto) recusadas com o código 2 e a mensagem nova; UTE Eldorado, Três Lagoas e UHE Ilha Solteira com o rascunho gravado (perfis gravados fora de `usinas/`).
- `python -m pytest tests` → 888 aprovados (29/10/2026, pandas 3.0.6; com os dados reais em `data/`, os 3 testes que antes eram pulados também rodam).
- `python -m pyflakes src tests anexos` → limpo.
- Princípio IX: a Coleta congelada das referências não existe nesta máquina (fora do git), e o `comparar --todas` não roda aqui; a cópia de segurança (`copia-seguranca`) também recusa, pelo mesmo motivo, e o estado anterior fica no git (commit `10b40ee`). No lugar, com os dados baixados do portal em 29/10/2026:
  - linha de base: `completo` das cinco usinas com referência, com o código do commit `10b40ee` e `--data-geracao "29/10/2026 08:00"`;
  - depois da correção: `completo --sem-portal` com a mesma data e `comparar --usina <slug> --referencia <linha de base>`;
  - São Domingos, William Arjona, Seriemas 1 e Praia Formosa: PDF, Markdown, CSV e figuras iguais; só a aba `DICIONARIOS` da planilha difere (situação e horário de obtenção dos dicionários, que as coletas das usinas seguintes obtiveram de novo em `data/raw/`; nenhuma correção mexe nela);
  - Bandeirante: só as duas células da tabela "Geração programada × verificada por mês" (jan/2025 e ago/2025), de "-0,0" para "0,0" (bug `zero-negativo-tabela`), no Markdown e no PDF.

## Deviations from Assessment

- Para a regra ser uma só sem o objeto `Perfil`, `conjuntos_da_usina` foi dividida: `conjuntos_pela_cobertura` (tipo e cobertura) e o filtro do campo de `[usina]` (o subsistema do CMO), que não afeta a série de referência.

## Follow-ups

- Recontar a cobertura do catálogo (1.911 usinas "próprias" no Brasil) só com as séries de referência, junto com a coluna `serie_referencia` da melhoria 5.
