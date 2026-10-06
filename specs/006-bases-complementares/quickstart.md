# Quickstart: validação da feature 006

**Feature**: [spec.md](spec.md) · **Contratos**: [cli-contract.md](contracts/cli-contract.md), [persistencia-contract.md](contracts/persistencia-contract.md) · **Dados**: [data-model.md](data-model.md)

## Pré-requisitos

- Ambiente virtual do projeto ativo (`venv\Scripts\Activate.ps1`), PowerShell, na raiz do projeto.
- Base EVT local já tratada em `data/processed/`. Ela não é baixada de novo.
- Cópia de referência do relatório anterior em `_backup_AAAA-MM-DD_antes_spec006/reports/`, para a não regressão.
- Cerca de 2 GB livres em disco para o primeiro download das bases novas.

## 1. Testes automatizados (sem rede)

```powershell
python -m pytest tests -q
```

**Esperado**: toda a suíte aprovada, incluindo os testes novos:
- `tests/unit/test_persistencia.py`: os seis testes do contrato;
- `tests/test_dicionarios_ons.py`: NOVO, INALTERADO, ALTERADO, FALHA, NAO_PUBLICADO, sem baixar dados da EVT;
- `tests/test_conjuntos_ons.py`: período pelo nome, formato por mês, recurso duplicado, identificação parcial, duplicatas, ausências;
- `tests/test_disponibilidade_ons.py`, `tests/test_hidrologia_ons.py` (conversão do 23:59 e alinhamento), `tests/test_geracao_ons.py`, `tests/test_cadastro_ons.py`;
- `tests/integration/test_pipeline.py`: etapas 5 a 8 simuladas, pastas e período corretos;
- `tests/test_conformidade.py`: loggers novos, `--log-level` nos `main()` novos, figuras novas com seaborn.

## 2. Cópia de segurança (US1)

```powershell
python -m src.main --programacao-only --log-level INFO
python -m src.main --programacao-only --log-level INFO
```

**Esperado**:
- Na primeira execução, o log informa `ALTERADO` (ou `NOVO`) para cada arquivo regravado, e `data/processed/*.csv.bak` contém a versão anterior.
- Na segunda execução, sem mudança no portal, o log informa `INALTERADO`. O `.bak` não muda: a data de modificação e o hash continuam os mesmos.

## 3. Dicionários (US2)

```powershell
python -m src.main --dicionarios-only
```

**Esperado**:
- Para cada conjunto, `data/raw/**/_dicionarios/` contém o PDF e o JSON.
- `data/processed/relatorio_dicionarios_ons.csv` tem 20 linhas, com resultado `NOVO` na primeira execução e `INALTERADO` na segunda.
- Nenhum arquivo `ENERGIA_VERTIDA_TURBINAVEL_*.csv` muda (data de modificação).

## 4. Bases complementares (US3 a US6)

```powershell
python -m src.main --complementares-only --log-level INFO
```

**Esperado**:
- Código de saída 0.
- Base EVT intacta.
- Em `data/processed/`, os arquivos listados no [data-model.md](data-model.md), seção 9.
- **Auditorias**:
  - disponibilidade: arquivos CSV de 2018-08 a 2022-12 e Parquet de 2023-01 em diante, sem nenhum mês com status `FALHA`;
  - hidrologia: `uhe_sao_domingos_ons_hidrologia_alinhamento.csv` com `confirmado = True` e `pct_coincidencia` ≥ 99 (SC-003);
  - nenhum registro com identificador diferente do declarado (SC-002).
- **Tempo**: uma segunda execução, sem rede (`--filter-only`) ou com cache, termina em menos de 10 minutos (SC-009).

## 5. Relatório

```powershell
python -m src.analyzer
```

**Esperado**:
- **Seções novas** no Markdown e no PDF, com uma constatação para disponibilidade sincronizada e outra para afluência. Constatação de geração ou de cadastro só se houver divergência.
- **Figuras** 06, 07 e 08 em `reports/figures/`.
- **Abas** `DISP_*`, `HID_*`, `GER_*`, `CAD_FICHA` e `DICIONARIOS` na planilha.
- **Conferências**:
  - a soma das faixas de afluência é igual ao total de horas com EVT do período comum;
  - a soma das classes das horas paradas é igual ao total de horas paradas (SC-005);
  - os números citados nas seções novas são iguais aos da planilha (SC-008).

## 6. Não regressão (SC-008)

Comparar com a cópia de referência:
- **Markdown**: o texto das seções existentes, ignorando a numeração das seções.
- **Planilha**: as abas existentes, célula a célula.

**Esperado**: nenhuma diferença fora das seções e abas novas e da numeração.

## 7. Prazo (SC-010)

US1 a US4 implementadas, relatório regenerado e passos 1 a 6 conferidos até 13/10/2026.
