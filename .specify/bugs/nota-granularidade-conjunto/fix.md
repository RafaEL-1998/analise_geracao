# Bug Fix: nota de granularidade errada na usina de conjunto com série própria

- **Slug**: nota-granularidade-conjunto
- **Fixed**: 2026-10-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

A nota de granularidade das usinas sem EVT separa os dois casos: com a geração (série de referência) no nível do conjunto, o texto de hoje; com a geração da usina e outra série no nível do conjunto (a Programação diária, o fator de capacidade ou a razão da restrição), uma nota que diz que a geração é a da própria usina e cita cada série do conjunto com o identificador dela. O texto de hoje com "()" não sai mais.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/relatorio/comum.py` | modified | `SERIES_DO_CONJUNTO`; ramo novo em `notas`, condicionado a `niveis_da_base` |
| `tests/relatorio/test_estrutura.py` | added test | UTE fictícia com a programação do conjunto |

A spec da Geração do relatório não muda: ela já pede "o que o ONS publica do conjunto e da usina" no parágrafo de granularidade (FR da seção de notas); o texto errado contrariava a spec.

## Diff Highlights

```python
elif "conjunto" in niveis_da_base(res):  # a geração (série de referência) é a do conjunto
    ...  # texto de hoje
elif com_conjunto(res):  # a geração é a da usina; outra série, como a Programação diária, é a do conjunto
    series = fmt_lista(f"{SERIES_DO_CONJUNTO.get(chave, chave)} ({n.get('identificador', '')})" ...)
```

Texto novo: "Granularidade: a geração é a da própria usina, mas o ONS publica a Programação diária (MSCRBR-9561; MSCRBR-9582) do conjunto <nome>, e não da usina isolada. Esses números são identificados como do conjunto e não são divididos entre as usinas; a conclusão da usina não usa números do conjunto."

## Tests Added or Updated

- `tests/relatorio/test_estrutura.py::test_granularidade_com_a_geracao_da_usina_e_a_programacao_do_conjunto` — cita a Programação diária com os códigos; não diz que a geração é do conjunto; sem "()".
- `tests/relatorio/test_estrutura.py::test_notas_com_omissoes_niveis_e_nao_aplicaveis` (existente) — a PCH em conjunto sem série própria mantém o texto de hoje; a UTE com tudo próprio, sem o parágrafo.

## Local Verification

- `pytest tests/relatorio/test_estrutura.py` → aprovados.
- Nenhuma referência tem a geração da usina com outra série do conjunto: as notas da Bandeirante (geração do conjunto) e da Seriemas 1 (restrição com detalhe) não mudam, como a comparação abaixo confirma.
- `python -m pytest tests` → 888 aprovados (29/10/2026, pandas 3.0.6; com os dados reais em `data/`, os 3 testes que antes eram pulados também rodam).
- `python -m pyflakes src tests anexos` → limpo.
- Princípio IX: a Coleta congelada das referências não existe nesta máquina (fora do git), e o `comparar --todas` não roda aqui; a cópia de segurança (`copia-seguranca`) também recusa, pelo mesmo motivo, e o estado anterior fica no git (commit `10b40ee`). No lugar, com os dados baixados do portal em 29/10/2026:
  - linha de base: `completo` das cinco usinas com referência, com o código do commit `10b40ee` e `--data-geracao "29/10/2026 08:00"`;
  - depois da correção: `completo --sem-portal` com a mesma data e `comparar --usina <slug> --referencia <linha de base>`;
  - São Domingos, William Arjona, Seriemas 1 e Praia Formosa: PDF, Markdown, CSV e figuras iguais; só a aba `DICIONARIOS` da planilha difere (situação e horário de obtenção dos dicionários, que as coletas das usinas seguintes obtiveram de novo em `data/raw/`; nenhuma correção mexe nela);
  - Bandeirante: só as duas células da tabela "Geração programada × verificada por mês" (jan/2025 e ago/2025), de "-0,0" para "0,0" (bug `zero-negativo-tabela`), no Markdown e no PDF.

## Deviations from Assessment

- Nenhuma.

## Follow-ups

- O bloco "Sobre os dados" do resumo executivo não repete a granularidade (conferido em `src/relatorio/resumo.py`).
