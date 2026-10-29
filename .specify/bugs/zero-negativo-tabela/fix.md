# Bug Fix: zero negativo ("-0,0") nas tabelas

- **Slug**: zero-negativo-tabela
- **Fixed**: 2026-10-29
- **Assessment**: ./assessment.md
- **Status**: partial (código e testes aplicados; a diferença na referência da PCH Bandeirante foi aprovada pelo usuário em 29/10/2026, e falta o novo registro, que depende da Coleta congelada)

## Summary

`fmt_num` tira o sinal quando o número arredondado é zero ("0,0", e não "-0,0"). Vale para todo o projeto (`fmt_int` e `fmt_pct` usam `fmt_num`) e não muda nenhum outro valor.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/comum/formatacao.py` | modified | `fmt_num`: texto só com "-", "0", "." e "," perde o "-" |
| `tests/comum/test_formatacao.py` | added | primeiro teste dos formatadores |

## Diff Highlights

```python
texto = f"{v:,.{casas}f}"
if set(texto) <= set("-0.,"):
    texto = texto.lstrip("-")
```

## Tests Added or Updated

- `tests/comum/test_formatacao.py::test_fmt_num_sem_zero_negativo` — `-0.04` → "0,0", `-0.004` (2 casas) → "0,00", `-0.06` → "-0,1", milhares com sinal mantidos.
- `tests/comum/test_formatacao.py::test_fmt_pct_e_fmt_int_sem_zero_negativo` — `fmt_pct(-0.01, 1)` → "0,0%".
- `tests/comum/test_formatacao.py::test_fmt_num_sem_valor` — ausente, NaN, infinito e texto → "–".

## Local Verification

- `pytest tests/comum/test_formatacao.py` → 13 aprovados.
- `python -m pytest tests` → 888 aprovados (29/10/2026, pandas 3.0.6; com os dados reais em `data/`, os 3 testes que antes eram pulados também rodam).
- `python -m pyflakes src tests anexos` → limpo.
- Princípio IX: a Coleta congelada das referências não existe nesta máquina (fora do git), e o `comparar --todas` não roda aqui; a cópia de segurança (`copia-seguranca`) também recusa, pelo mesmo motivo, e o estado anterior fica no git (commit `10b40ee`). No lugar, com os dados baixados do portal em 29/10/2026:
  - linha de base: `completo` das cinco usinas com referência, com o código do commit `10b40ee` e `--data-geracao "29/10/2026 08:00"`;
  - depois da correção: `completo --sem-portal` com a mesma data e `comparar --usina <slug> --referencia <linha de base>`;
  - São Domingos, William Arjona, Seriemas 1 e Praia Formosa: PDF, Markdown, CSV e figuras iguais; só a aba `DICIONARIOS` da planilha difere (situação e horário de obtenção dos dicionários, que as coletas das usinas seguintes obtiveram de novo em `data/raw/`; nenhuma correção mexe nela);
  - Bandeirante: só as duas células da tabela "Geração programada × verificada por mês" (jan/2025 e ago/2025), de "-0,0" para "0,0" (bug `zero-negativo-tabela`), no Markdown e no PDF.

## Deviations from Assessment

- `fmt_pp` continua escrevendo "−0,0 p.p." para uma diferença negativa que arredonda a zero (o sinal vem de `v < 0`, antes do arredondamento); o relatório usa `_pp` em `src/relatorio/conteudo.py`, que já trata o caso. Fora do escopo da avaliação.

## Follow-ups

- **Referência da PCH Bandeirante**: duas células da tabela "Geração programada × verificada por mês" (jan/2025 e ago/2025) passam de "-0,0" a "0,0".
  - **Aprovação**: diferença aprovada pelo usuário em 29/10/2026 ("aceito suas recomendações"; princípio IX).
  - **Pendente**: o novo registro. O `referencia` congela a Coleta que está em `data/usinas/bandeirante/coleta/`. Para manter os dados de 22/10/2026, o registro precisa partir da Coleta congelada de hoje, que não está nesta máquina. Na máquina que tem a Coleta congelada, depois de atualizar o código:
    1. copiar `relatorios_referencia/bandeirante/coleta/` para `data/usinas/bandeirante/coleta/`;
    2. rodar `tratamento`, `conferencia`, `analises` e `relatorio --data-geracao "22/10/2026 10:00"` da usina;
    3. rodar `comparar --usina bandeirante --referencia relatorios_referencia/bandeirante`, que deve mostrar só o Markdown e o PDF diferentes, pelas duas células;
    4. registrar com `referencia --usina bandeirante --data-geracao "22/10/2026 10:00" --aprovado-em "29/10/2026"`;
    5. conferir com `comparar --todas`, que deve terminar com código 0.
