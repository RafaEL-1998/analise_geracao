# Tasks: Conformidade com a Constituição 1.1.0 - UHE São Domingos

**Input**: Design documents from `/specs/005-conformidade-constituicao/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: incluídos — cada história define um teste independente na spec e a constituição exige validação de não regressão.

**Formato**: `[ID] [P?] [Story] Descrição` — `[P]` = paralelizável (arquivos diferentes, sem dependência pendente).

---

## Phase 1: Setup

- [X] T001 Confirmar a cópia integral pré-implementação em `_backup_2026-10-05_antes_spec005/` (src, tests, specs, reports, README, requirements, `.specify`, `.claude`) exigida pelo Requisito Técnico 3

---

## Phase 2: Foundational

**⚠️ CRITICAL**: US2 depende desta fase para a comparação de não regressão (FR-007).

- [X] T002 Usar `_backup_2026-10-05_antes_spec005/reports/relatorio_analise_estatistica.md` e `.../perfil_estatistico_anual.xlsx` como referência e registrar o hash da base consolidada `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv` antes das mudanças

---

## Phase 3: User Story 1 - Versões anteriores de arquivos republicados (Priority: P1) 🎯 MVP

**Goal**: arquivo republicado com conteúdo diferente tem a cópia anterior preservada em `_versoes_anteriores/` e registrada no manifesto.

**Independent Test**: simular republicação com conteúdo diferente e igual; conferir arquivo preservado, manifesto e que a extração lê só a versão corrente.

- [X] T003 [P] [US1] Testes em `tests/unit/test_collector.py`: (a) republicação com conteúdo diferente → cópia em `_versoes_anteriores/<stem>__pub_<AAAAMMDDTHHMMSS><sufixo>` e entrada `versoes_anteriores` com `arquivo_preservado`, `ultima_modificacao`, `tamanho_bytes`, `sha256`, `arquivado_em_utc`; (b) conteúdo idêntico → nenhuma cópia; (c) duas republicações → duas versões sem colisão; (d) falha no download → versão corrente intacta; (e) `--force-download` sem manifesto e conteúdo diferente → nome `__arq_<data>`; (f) `filter_all_raw_files` ignora `_versoes_anteriores/`
- [X] T004 [US1] Em `src/collector.py`: soma SHA-256, função de arquivamento (nome conforme research R2, sufixo `_2`, `_3` em colisão), integração em `download_resource` após o download bem-sucedido e antes de `temp_path.replace(local_path)`, `_register_version` preservando a lista `versoes_anteriores`, log "Versão anterior preservada"

**Checkpoint**: US1 testável de forma independente.

---

## Phase 4: User Story 2 - Gráficos produzidos com seaborn (Priority: P1)

**Goal**: as 5 figuras produzidas com seaborn, mesmos nomes, 300 DPI, mesmos elementos, paleta atual.

**Independent Test**: gerar as figuras na base atual, conferir nomes, resolução e elementos; Markdown e planilha idênticos à referência.

- [X] T005 [US2] Carregar a skill de visualização (dataviz) antes de escrever código de gráfico em `src/analyzer.py` e registrar as decisões aplicáveis (tema, paleta, rótulos)
- [X] T006 [P] [US2] Teste em `tests/test_conformidade.py`: toda função `_grafico_*` de `src/analyzer.py` usa seaborn; `tests/test_analyzer.py::test_gerar_graficos` continua exigindo os 5 arquivos
- [X] T007 [US2] Tema central em `src/analyzer.py`: `_estilo_graficos()` aplicado via seaborn (estilo + rc) e paleta atual (`COR_*`, `RAMPA_*`) fornecida ao seaborn
- [X] T008 [US2] `_grafico_serie_temporal` com `sns.lineplot` (disponibilidade, geração, EVT), mantendo faixas de indisponibilidade ≥ 24 h, preenchimento da EVT, referências de potência e garantia física e legenda
- [X] T009 [US2] `_grafico_evt_mensal` com `sns.histplot` ponderado e empilhado (parcela do vertimento mínimo × demais horas), mantendo o marco da mudança de classificação
- [X] T010 [US2] `_grafico_perfil_horario` com `sns.heatmap` (geração e EVT por ano × hora, rampas atuais, anos parciais com `*`)
- [X] T011 [US2] `_grafico_disponibilidade_anual` com `sns.barplot` e `hue` (disponibilidade declarada × fator de capacidade), referências da GF
- [X] T012 [US2] `_grafico_vazoes_defluentes` com `sns.histplot` empilhado e discreto por ano (turbinada, vertida turbinável, vertida não turbinável), engolimento máximo
- [X] T013 [US2] Gerar as figuras na base real e conferir visualmente cada uma contra a versão de `_backup_2026-10-05_antes_spec005/reports/figures/`

**Checkpoint**: US2 completa; relatório só com mudança nas figuras.

---

## Phase 5: User Story 3 - Nível de log único (Priority: P2)

**Goal**: `--log-level` aplicado a todos os loggers em todos os pontos de entrada.

**Independent Test**: com WARNING, nenhum INFO de nenhum módulo.

- [X] T014 [P] [US3] Testes em `tests/test_conformidade.py`: `configurar_nivel_log("WARNING")` ajusta todos os nomes de `LOGGERS_PIPELINE`; `src.main`, `src.processor`, `src.analyzer`, `src.indicadores_ons`, `src.programacao_ons` e `src.pdf_generator` aceitam `--log-level` e aplicam o nível a todos (execução simulada, sem rede)
- [X] T015 [US3] Em `src/logger.py`: `LOGGERS_PIPELINE` = `main`, `collector`, `filter`, `consolidator`, `indicadores_ons`, `programacao_ons`, `processor`, `validator`, `analyzer`, `uhe_sao_domingos.pdf_generator` e `configurar_nivel_log(nivel)`
- [X] T016 [US3] Aplicar `configurar_nivel_log` em `src/main.py`, `src/processor.py`, `src/analyzer.py` e acrescentar `--log-level` aos `main()` de `src/indicadores_ons.py`, `src/programacao_ons.py` e `src/pdf_generator.py`

---

## Phase 6: User Story 4 - Linhas com formato irregular (Priority: P3)

**Goal**: linhas não vazias com número de campos diferente do cabeçalho contadas, avisadas e não extraídas.

**Independent Test**: arquivo com 1 linha curta e 1 longa → 2 na auditoria; arquivos reais → 0, base idêntica.

- [X] T017 [P] [US4] Testes em `tests/unit/test_filter.py`: linha curta e linha longa → `registros_formato_irregular` = 2, não extraídas, aviso no log com arquivo e números das linhas; linha vazia continua ignorada
- [X] T018 [US4] Em `src/models.py`: campo `registros_formato_irregular: int = 0` ao final de `AuditoriaArquivo`
- [X] T019 [US4] Em `src/filter.py`: contagem e aviso (5 primeiras linhas) em `_scan_file`, sem extrair as linhas irregulares
- [X] T020 [US4] Em `src/consolidator.py`: coluna `registros_formato_irregular` em `AUDIT_CSV_COLUMNS` e no gravador
- [X] T021 [US4] Executar `python -m src.main --filter-only --sem-indicadores --sem-programacao --log-level WARNING` e conferir 0 irregulares, nenhum INFO e hash da base consolidada igual ao de T002

---

## Phase 7: User Story 5 - Dependências fiéis ao uso (Priority: P3)

- [X] T022 [P] [US5] Teste em `tests/test_conformidade.py`: pacotes de terceiros importados em `src/` e `tests/` (análise sintática) = pacotes de `requirements.txt`
- [X] T023 [US5] `requirements.txt`: pandas, numpy (≥ 1.26), pyarrow, openpyxl, matplotlib, seaborn, reportlab, pytest; retirar `requests`

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T024 [P] Atualizar `README.md` (nível de log, versões anteriores, linhas irregulares, gráficos com seaborn, dependências, histórico)
- [X] T025 [P] Registrar no "Histórico de revisões" de `specs/001-ons-coleta-sao-domingos/spec.md` (versões anteriores, linhas irregulares, log), `specs/002-tratamento-dados/spec.md` (log) e `specs/003-analise-dados/spec.md` (figuras com seaborn) as mudanças desta feature, com `.bak` antes de editar
- [X] T026 Executar `pytest tests/ -v`: suíte aprovada, sem rede e sem alterar arquivos do projeto
- [X] T027 Regenerar o relatório (`python -m src.analyzer`) e comparar Markdown e abas da planilha com a referência de T002 (FR-007, SC-005)

---

## Registro de execução (05/10/2026)

- T001–T002: cópia `_backup_2026-10-05_antes_spec005/` (164 arquivos); hash de referência da base consolidada `eae1ae7e65d7140e02d49e90104bf096`.
- US1 (T003–T004): 6 testes novos; versão anterior preservada só quando o SHA-256 difere; falha de download mantém a versão corrente; leitores ignoram `_versoes_anteriores/`.
- US2 (T005–T013): skill de visualização carregada antes do código; paleta categórica validada pelo script (`#2a78d6, #1baf7a, #eb6834`: todas as verificações aprovadas; contraste do verde < 3:1 compensado por legenda e tabelas); o cinza de contexto reprova o piso de croma por ser intencionalmente neutro. O seaborn empilha da última categoria (base) para a primeira — ordem invertida no código para manter a base das pilhas. Conferência visual das 5 figuras contra a versão anterior: todos os elementos mantidos.
- US3 (T014–T016): `configurar_nivel_log` em todos os pontos de entrada; com `--log-level WARNING`, 0 linhas de log na filtragem completa.
- US4 (T017–T021): 2 testes novos; base real: 0 linhas irregulares em 42 arquivos; hash da base consolidada idêntico.
- US5 (T022–T023): `requirements.txt` = pandas, numpy, pyarrow, openpyxl, matplotlib, seaborn, reportlab, pytest; `requests` retirado; teste de correspondência aprovado.
- T026: 87 testes aprovados, sem rede e sem alterar arquivos do projeto.
- T027: `relatorio_analise_estatistica.md`, as 32 abas de `perfil_estatistico_anual.xlsx` e o CSV idênticos à referência; PDF com 19 páginas; análise completa em 10,2 s.

## Dependencies & Execution Order

- Phase 1 → Phase 2 → histórias.
- US1, US3, US4 e US5 são independentes entre si; US2 depende de T002 (referência).
- Dentro de cada história: testes [P] → implementação → validação.
- Polish após todas as histórias.

### Parallel Opportunities

- T003, T006, T014, T017 e T022 (testes em arquivos diferentes) podem ser escritos em paralelo.
- US1 (`collector.py`), US4 (`filter.py`/`models.py`/`consolidator.py`) e US5 (`requirements.txt`) não compartilham arquivos.
- T024 e T025 em paralelo.

## Parallel Example: User Story 4

```text
Task: "Testes de linhas irregulares em tests/unit/test_filter.py"
Task: "Campo registros_formato_irregular em src/models.py"
```

## Implementation Strategy

1. Setup e Foundational (T001–T002).
2. MVP: US1 (preservação de versões) — maior impacto regulatório.
3. US2 (seaborn), depois US3, US4 e US5.
4. Polish (T024–T027).
