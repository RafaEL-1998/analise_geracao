# Bug Fix: unidade geradora com letra no nome (ciclo combinado)

- **Slug**: unidade-com-letra
- **Fixed**: 2026-10-29
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

A unidade geradora (`ug`) passa a ser o rótulo que o ONS publica. Ela continua inteira quando todos os rótulos da usina são só algarismos, como em todas as usinas com perfil, e por isso nenhuma referência muda. Quando algum rótulo tem letra, ela vira texto, como no ciclo combinado da UTE Três Lagoas ("1A" a "2C"). As Análises e o relatório usam o rótulo sem `int(...)`, na ordem natural. Abordagem aprovada pelo usuário em 29/10/2026: "siga com suas recomendações".

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/tratamento/indicadores.py` | modified | funções novas da unidade: `rotulo_ug`, `rotulo_no_nome` (no lugar de `numero_ug`), `tipar_ug`, `chave_ug` (ordem natural), `nome_ug` ("UG1", "UG1A", "UG TG10"), `ordenar_por_ug` e `em_ordem_ug`; as três tabelas por unidade com o mesmo tipo (`_mesmo_tipo_de_ug`), também na leitura do CSV; aviso das linhas sem rótulo. Ajuste da verificação: em `rotulo_ug`, "UG" seguido só de algarismos vale o número (`_RE_PREFIXO_UG`) |
| `src/analises/indicadores.py` | modified | decomposição das taxas e horas por ano na ordem natural, sem `int(ug)` |
| `src/analises/constatacoes.py` | modified | estados operativos: `nome_ug` e ordem natural |
| `src/analises/conclusao.py` | modified | C2 pelo rótulo; C10 e `_unidades_agrupadas` sem `int(u)`, na ordem natural |
| `src/relatorio/conteudo.py` | modified | as quatro tabelas por unidade com `nome_ug` |
| `specs/002-tratamento-dados/data-model.md` | modified | regra da unidade (seção 2.3), com "UG1" → "1", e tipo de `ug` |
| `specs/002-tratamento-dados/spec.md` | modified | FR-021, FR-022, FR-024 e as duas decisões do usuário de 29/10/2026 (a abordagem e o ajuste da verificação) |
| `specs/002-tratamento-dados/plan.md` | modified | `numero_ug` → `rotulo_no_nome` |
| `specs/003-conferencia/data-model.md` | modified | tipo de `ug` em `dispf_horas.csv` |
| `tests/tratamento/test_indicadores.py` | modified/added tests | rótulo, tipo, ordem, Três Lagoas, Itaipu (misto) e aviso |
| `tests/analises/test_indicadores.py` | modified/added test | auxiliares com os rótulos das unidades; teste de ponta a ponta com "2A" e "10A" |
| `tests/analises/test_conclusao.py` | added tests | C10 e `_unidades_agrupadas` com rótulo com letra |

## Diff Highlights

```python
_RE_ROTULO_UG = re.compile(r"(\S+)\s+[A-Z]{2}$")

_RE_PREFIXO_UG = re.compile(r"UG(\d+)")  # em rotulo_ug: 'UG1' → '1' (UHE Santa Branca)

def tipar_ug(valores: pd.Series, texto: bool = False) -> pd.Series:
    rotulos = valores.map(rotulo_ug)
    if not texto and all(r.isdigit() for r in rotulos.dropna()):
        return pd.to_numeric(rotulos).astype("Int64")
    return rotulos.astype(object)

def chave_ug(valor: Any) -> Optional[str]:
    rotulo = rotulo_ug(valor)
    return None if rotulo is None else _RE_ALGARISMOS.sub(lambda m: m.group().zfill(6), rotulo)
```

## Tests Added or Updated

- `tests/tratamento/test_indicadores.py::test_rotulo_da_unidade_no_nome`: "1", "2A", "G18A", "07" → "7", "UG1" → "1", e nome sem rótulo → None.
- `::test_unidade_com_prefixo_ug_no_nome_e_o_numero` (ajuste da verificação): UHE Santa Branca, com "UG1" e "UG2" em 2025 e "1" e "2" em 2026 nos parâmetros. Ficam duas unidades inteiras, e as quatro linhas juntam com os indicadores.
- `::test_ug_inteiro_quando_os_rotulos_sao_so_algarismos`: `Int64`, como hoje; as referências não mudam.
- `::test_ordem_natural_e_nome_da_unidade`: 2 antes de 10, 18 antes de 18A e de G18A, TG4 antes de TG10; "UG2", "UG1A", "UG TG10".
- `::test_unidades_com_letra_ficam_separadas_em_ordem_natural`: as seis unidades da Três Lagoas, nas duas bases, e a junção por mês e unidade.
- `::test_unidade_com_o_mesmo_tipo_em_todas_as_tabelas_gravadas`: caso misto de Itaipu; a tabela só com algarismos volta como texto na leitura, e a junção não quebra.
- `::test_linha_sem_rotulo_da_unidade_e_avisada`: aviso no log.
- `tests/analises/test_indicadores.py::test_unidades_com_letra_ficam_separadas_e_em_ordem_natural`: Análises completas com "2A" e "10A". Cobre a decomposição, as horas por ano, as tabelas do relatório, os estados operativos e a C2, sem exceção e em ordem natural.
- `tests/analises/test_conclusao.py::test_c10_com_unidades_de_rotulo_com_letra` e a linha nova de `test_c10_das_usinas_sem_evt_agrupa_unidades_e_anos`: o rótulo na C10 (antes, `int` do rótulo).

## Local Verification

- `pytest tests/tratamento/test_indicadores.py tests/analises/test_indicadores.py tests/analises/test_conclusao.py tests/conferencia tests/relatorio/test_markdown.py` → aprovados.
- `python -m pytest tests` → 895 aprovados (888 de antes e 7 novos; 29/10/2026, pandas 3.0.6).
- `python -m pyflakes src tests anexos` → limpo.
- **Princípio IX**: o `comparar --todas` não roda nesta máquina, pela falta da Coleta congelada. No lugar:
  - antes da correção, guardei `reports/<slug>/` e as tabelas por unidade (`indicadores_ug_mensal`, `indicadores_ug_anual`, `horas_estado_mensal`, `teifa_teip_mensal`, `dispf_horas` e `teifa_teip`) das cinco usinas com referência;
  - depois, rodei `completo --sem-portal --data-geracao "29/10/2026 08:00"`, comparei as tabelas byte a byte e rodei `comparar --usina <slug> --referencia <cópia>`;
  - resultado nas cinco usinas: tabelas iguais e relatório idêntico em PDF, Markdown, CSV, figuras e planilha, inclusive a aba `DICIONARIOS`.
- **UTE Três Lagoas real**: perfil pelo rascunho, aceito só com os dados do ONS, como na homologação. Rodou num espaço isolado (`espaco_isolado`, brutos de `data/raw/`), com `completo --sem-portal`:
  - código 0, relatório de 12 seções e 28 páginas; antes, o fluxo parava com exceção na C10;
  - seis unidades separadas nas duas bases (1A, 1B, 1C, 2A, 2B e 2C), nenhuma linha sem rótulo;
  - as tabelas por unidade em ordem natural ("UG1A" … "UG2C");
  - a UG1B tem 64 meses nos parâmetros das taxas, e as outras 81, exatamente como nos arquivos brutos do ONS.
- **Ajuste do prefixo "UG"** (29/10/2026, depois do `/speckit-bug-test`):
  - `python -m pytest tests` → 896 aprovados (o teste novo da Santa Branca) e pyflakes limpo;
  - junção dos parâmetros das taxas com os indicadores mensais, por (CEG, mês, unidade), em todos os 246 CEG das duas bases: nenhuma das 81.754 chaves sem par (antes do ajuste, 144, todas da Santa Branca; no código de antes da correção, 456, de três térmicas com rótulo com letra);
  - UHE Santa Branca no Tratamento: as unidades 1 e 2, inteiras, e a junção de 162 em 162 meses-unidade;
  - Três Lagoas e as cinco referências refeitas num espaço isolado: o mesmo resultado de antes do ajuste.

## Deviations from Assessment

- **Expressão do rótulo no nome**: ficou `(\S+)\s+[A-Z]{2}$`, o último termo antes da UF, e não `(\d+[A-Z]?)`. Nos dados de 29/10/2026 há rótulos que a expressão da avaliação não pega: "ST1", "TG10", "V1", "R1", "ST", "A" e "1X". Em Itaipu, ela cortaria o "G" de "G18A", e a Conferência não juntaria os indicadores ("G18A") com os parâmetros ("18A"). Nos indicadores, o último termo do nome é igual ao `num_unidadegeradora` nas 126.307 linhas.
- **Zeros à esquerda**: o rótulo só de algarismos perde os zeros ("07" → "7", Aparecida e Belo Monte), como o número de hoje. Assim, inteiro e texto dão o mesmo rótulo.
- **Mesmo tipo nas três tabelas** (`_mesmo_tipo_de_ug`): é um requisito novo, não previsto na avaliação. Numa usina mista, uma tabela pode ter só algarismos no período e voltar do CSV como inteiro, enquanto outra volta como texto, e aí a junção da Conferência quebraria. A escolha do tipo é refeita na leitura (`carregar_indicadores_tratados`).
- **Nome no texto**: com espaço quando o rótulo começa por letra ("UG TG10" em vez de "UGTG10"). Nenhuma usina com perfil tem esse caso.
- **Prefixo "UG"** (ajuste depois do `/speckit-bug-test`). A primeira versão lia "UG1" como rótulo. Assim, a UHE Santa Branca deixava 144 chaves (CEG, mês, unidade) dos parâmetros de 2020 a 2025 sem par nos indicadores ("1" e "2"); o código antigo as juntava por acaso da expressão `(\d+)`. A conferência do número com o nome, feita só nos indicadores, não pegava o caso. Agora entra também a junção dos parâmetros com os indicadores em todo o Brasil. Ajuste aprovado pelo usuário em 29/10/2026: "vamos com suas recomendações".
- **Escopo ampliado**: entrou `specs/003-conferencia/data-model.md` (tipo de `ug` em `dispf_horas.csv`). A Conferência não precisou de mudança no código, porque já juntava por (`mes`, `ug`) sem converter.

## Follow-ups

- **Programação da UTE Três Lagoas**: a seção continua ausente enquanto os códigos "MSTLA - 618" etc. não forem ligados à usina (melhoria 5 da proposta de 23/10/2026).
- **Repetir a homologação**: o lote de 26/10/2026, para medir de novo.
