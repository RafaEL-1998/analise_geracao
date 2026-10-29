# Bug Assessment: unidade geradora com letra no nome (ciclo combinado)

- **Slug**: unidade-com-letra
- **Created**: 2026-10-29
- **Source**: pasted text (achado 10 de `propostas/2026-10-26-homologacao-lote-1.md` e follow-up de `.specify/bugs/programacao-sem-cobertura/fix.md`)
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

> Unidade com letra no nome (bug, achado depois da correção do achado 3; UTE Três Lagoas). As unidades a ciclo combinado são publicadas como "1A", "1B", "2A", "2B", "1C" e "2C"; a leitura do número da unidade só aceita algarismos, as 16 linhas ficam sem unidade, as tabelas por unidade juntam as unidades e a regra C10 da conclusão quebra (`int(NaN)`). É o primeiro erro inesperado da homologação.

## Symptom

Na usina cujas unidades o ONS identifica com algarismo e letra, o número da unidade vira vazio (`<NA>`) nos indicadores por unidade e nas horas por estado operativo. As unidades se misturam nas tabelas e na decomposição das taxas, e as Análises param com exceção na regra C10 (`int(NaN)`), sem gerar o relatório.

Conferido nos dados de 29/10/2026 (`IND_DISPONIBILIDADE_FCGERACAO_UGE_MENSAL_2026.csv`), UTE Três Lagoas (CEG `UTE.GN.MS.027975-7.01`, id ONS `MSUTLG`):

| `cod_equipamento` | `num_unidadegeradora` | `nom_unidadegeradora` |
|---|---|---|
| `MSTLA-0UG1` | `1A` | `UG 58P3 MW TRES LAGOAS              1A MS` |
| `MSTLA-0UG2` | `1B` | `UG 58P1 MW TRES LAGOAS              1B MS` |
| `MSTLA-0UG5` | `2A` | `UG 57P8 MW TRES LAGOAS              2A MS` |
| `MSTLA-0UG6` | `2B` | `UG 60P9 MW TRES LAGOAS              2B MS` |
| `MSLCP-0UG1C` | `1C` | `UG 57P3 MW TRES LAGOAS              1C MS` |
| `MSLCP-0UG2C` | `2C` | `UG 57P3 MW TRES LAGOAS              2C MS` |

Nos parâmetros das taxas TEIFa e TEIP de 2026 (`TAXA_TEIF_TEIP_PARAM_2026.csv`, só `nom_unidadegeradora`), o mesmo padrão aparece em outras usinas do Brasil, todas hoje com a unidade vazia:

| Usina (nome publicado) | Rótulos das unidades |
|---|---|
| TRES LAGOAS | 1A, 1B, 1C, 2A, 2B, 2C |
| UT.CAM.GRANDE | 1A, 1B, 2A, 2B |
| UTE POVOACAO 1, JUIZ DE FORA, UTE B. BONITA I | com letra (não detalhado) |
| ITAIPU 60 HZ (e 50 HZ) | 10 a 18 e "G18A" (`UG  700 MW ITAIPU 60 HZ           G18A PR`): **misto**, com "18" e "18A" como unidades distintas |

## Reproduction

1. Perfil da UTE Três Lagoas pelo rascunho, aceito só com os dados do ONS (como na homologação de 26/10/2026).
2. `python -m src completo --usina ute_tres_lagoas`.
3. As Análises param com exceção na regra C10, no `int(u)` de `_unidades_agrupadas` sobre a unidade vazia (relato da homologação de 26/10/2026; a mensagem exata não foi reproduzida nesta avaliação).

## Suspected Code Paths

- `src/tratamento/indicadores.py:79` (`tratar_indicadores_ug`): `_numerico(df["num_unidadegeradora"]).astype("Int64")` — "1A" vira `<NA>`.
- `src/tratamento/indicadores.py:43` e `:98-101` (`_RE_NUMERO_UG`, `numero_ug`): `(\d+)\s+[A-Z]{2}$` só aceita algarismos antes da UF; usado em `tratar_horas_estado` (`:110`).
- Uso do número como inteiro depois do Tratamento:
  - `src/analises/indicadores.py:36` (decomposição das taxas, `int(ug)`);
  - `src/analises/conclusao.py:138-139` (C10, participação por unidade) e `:340` (`_unidades_agrupadas`, `int(u)`);
  - `src/analises/constatacoes.py:147`, `:196-216` (`ug: int`, `int(u)`, "UG{u}");
  - `src/relatorio/conteudo.py:365`, `:377`, `:391`, `:404` (`f"UG{int(r.ug)}"`).
- A Conferência junta as duas bases por (`mes`, `ug`) (`src/conferencia/indicadores.py:35` e `:126`): as duas leituras precisam dar o mesmo identificador.

## Root Cause Hypothesis

O número da unidade foi modelado como inteiro a partir das hidrelétricas e térmicas de MS da fase A e B, todas com unidades numeradas. O ONS identifica as unidades das térmicas a ciclo combinado com algarismo e letra (turbinas a gás "A" e "B" e a vapor "C" de cada bloco). Confiança: alta.

## Proposed Remediation

**Preferred**: o identificador da unidade passa a ser o rótulo publicado pelo ONS, sem perder o inteiro onde ele existe.

- No Tratamento, uma função única lê o rótulo da unidade (`num_unidadegeradora` sem espaços; no nome, o último termo antes da UF, com `(\d+[A-Z]?)\s+[A-Z]{2}$`) e monta a coluna `ug`: `Int64`, como hoje, quando todos os rótulos da usina são só algarismos; texto (por exemplo, "1A"), quando algum tem letra. As duas leituras (indicadores e parâmetros das taxas) usam a mesma função, para a junção da Conferência.
- Nas Análises e no relatório, o rótulo é usado como está ("UG1A", "UG1"), sem `int(...)`, e a ordem das unidades segue a ordem natural do rótulo (1A, 1B, 1C, 2A, …).
- Linha nova sem rótulo (vazio ou fora do padrão) fica com `ug` vazio e é contada no log do Tratamento, como hoje as linhas com chave repetida, em vez de seguir em silêncio.

Efeito: as usinas de hoje (unidades numeradas, inclusive as cinco referências) continuam com `ug` inteiro, sem diferença nos relatórios nem na planilha; a Três Lagoas passa a ter as seis unidades separadas.

**Alternatives**:
- Identificador inteiro de posição (1 a 6) com uma coluna nova de rótulo: mantém o tipo inteiro em todo o código, mas acrescenta uma coluna às tabelas por unidade de todas as usinas (a planilha das referências muda) e cria um número que o ONS não publica.
- Usar o `cod_equipamento` como identificador: é único, mas não aparece nos parâmetros das taxas (que trazem só o nome da unidade) e é longo para as tabelas.

**Files likely to change**:
- `src/tratamento/indicadores.py`
- `src/analises/indicadores.py`, `src/analises/conclusao.py`, `src/analises/constatacoes.py`
- `src/relatorio/conteudo.py`
- `specs/002-tratamento-dados/data-model.md` (tipo da coluna `ug`) e `spec.md` (leitura do identificador da unidade)
- `tests/tratamento/test_indicadores.py`, `tests/analises/test_indicadores.py`, `tests/analises/test_conclusao.py`

**Tests to add or update**:
- `numero_ug` / rótulo: "UG   24 MW USINA              1 MS" → 1; "UG 57P8 MW TRES LAGOAS              2A MS" → "2A".
- Indicadores e horas por estado de uma usina com unidades "1A", "1B", "1C": seis linhas separadas por mês, a junção da Conferência com todas as unidades.
- C10 e a decomposição das taxas com unidades com letra: sem exceção, com "UG1A" no texto.
- Usina com unidades numeradas: `ug` continua `Int64` (as referências não mudam).

## Risks & Considerations

- Princípio IX: as cinco referências têm unidades numeradas; a correção não deve mudar nenhuma. Conferir com a comparação dos relatórios.
- Tipo misto (algarismos e letras na mesma usina, como Itaipu: 10 a 18 e 18A) vira texto para todas as unidades da usina; a ordem natural evita "10" antes de "2" e põe "18A" depois de "18". O prefixo de letra antes do número ("G18A") fica fora do rótulo pela expressão `(\d+[A-Z]?)\s+[A-Z]{2}$`; conferir com o `num_unidadegeradora` dos indicadores de Itaipu na implementação.
- Outras usinas do Brasil com unidades com letra (Campo Grande, Povoação 1, Juiz de Fora, B. Bonita I, Itaipu) seguem a mesma regra; nenhuma tem perfil hoje.

## Open Questions

- [NEEDS CLARIFICATION] Aprovação do usuário para a abordagem preferida (rótulo publicado, inteiro quando só algarismos), que muda o tipo da coluna `ug` no data-model do Tratamento.
