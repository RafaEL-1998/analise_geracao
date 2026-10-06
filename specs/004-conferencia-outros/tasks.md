# Tasks: Conferência com Outras Fontes do ONS e Programação Diária - UHE São Domingos

**Feature**: `004-conferencia-outros` | **Branch**: `004-conferencia-outros` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Formato**: `[ID] [P?] [Story] Descrição` — `[P]` = pode rodar em paralelo (arquivos diferentes, sem dependência).

---

## Phase 1: Setup

**Purpose**: Parâmetros e infraestrutura compartilhada

- [X] T001 Adicionar a `src/config.py` os parâmetros da programação diária: identificador do conjunto, código de exibição `PRUHSD`, estado `MS`, pasta bruta `data/raw/programacao_diaria`, caminhos das saídas tratadas e o limiar de desvio de 5 MW
- [X] T002 [P] Ajustar `_local_filename` em `src/collector.py` para preservar a extensão do formato compacto (Parquet) e permitir a seleção de recursos por formato em `parse_ckan_resources`, sem alterar o comportamento para CSV; cobrir em `tests/unit/test_collector.py`

---

## Phase 2: Foundational

**Purpose**: Dados de entrada disponíveis

**⚠️ CRITICAL**: US1 depende desta fase.

- [X] T003 Reaproveitar os 712 arquivos diários obtidos na exploração de 02/10/2026, copiando-os para `data/raw/programacao_diaria/` para que o manifesto os aceite pelo tamanho publicado (sem novo download)

**Checkpoint**: arquivos brutos da programação disponíveis localmente.

---

## Phase 3: User Story 1 - Operação verificada × programação diária do ONS (Priority: P1) 🎯 MVP

**Goal**: Programação horária da usina cruzada com a base de EVT, com classificação das horas de usina parada com EVT, eventos de desvio e seção no relatório.

**Independent Test**: Gerar o resumo mensal com os arquivos reais e conferir que a soma das classes das horas paradas com EVT é igual ao total dessas horas no período comum.

### Tests for User Story 1 🧪

- [X] T004 [P] [US1] Criar `tests/test_programacao_ons.py` com arquivos diários sintéticos (formatos de data `AAAA-MM-DD` e `DD/MM/AAAA`, homônimos, dia incompleto): extração e auditoria, data pelo nome do arquivo, conversão para horas, dias ausentes, classificação, resumo mensal, eventos de desvio e execução completa em pastas temporárias sem rede

### Implementation for User Story 1

- [X] T005 [US1] Criar `src/programacao_ons.py`: sincronização dos arquivos do período pelo catálogo CKAN com manifesto (reutilizando `src/collector.py`)
- [X] T006 [US1] Em `src/programacao_ons.py`, extração da usina com conferência de nome e estado, data pelo nome do arquivo, conferência da data interna e auditoria por arquivo
- [X] T007 [US1] Em `src/programacao_ons.py`, programação horária (média dos patamares), lista de dias ausentes, recorte no período da base de EVT, exportação para `data/processed/` e leitura das tabelas tratadas
- [X] T008 [US1] Em `src/programacao_ons.py`, funções de análise: classificação horária, resumo mensal, eventos de desvio e perfil por hora do dia
- [X] T009 [US1] Integrar a etapa 4 em `src/main.py` (`--programacao-only`, `--sem-programacao`, pastas configuradas) e atualizar `tests/integration/test_pipeline.py` com a etapa simulada
- [X] T010 [US1] Em `src/analyzer.py`: carregar a programação, calcular o resumo, gerar a constatação "Programação diária do ONS", notas metodológicas, parâmetros, abas `PROG_*` e seção no Markdown
- [X] T011 [US1] Em `src/pdf_generator.py`: seção "Operação verificada e programação diária do ONS" com tabela mensal, perfil por hora e maiores eventos de desvio
- [X] T012 [US1] Executar com os arquivos reais e validar SC-001 a SC-006 conforme `quickstart.md`

**Checkpoint**: US1 funcional e testável de forma independente.

---

## Phase 4: User Story 2 - Indicadores oficiais por unidade geradora (Priority: P2) — implementada em 02/10/2026

- [X] T013 [US2] Parâmetros (CEG, id ONS, conjuntos, pastas, saídas, tolerância de 1 h) em `src/config.py`
- [X] T014 [US2] Módulo `src/indicadores_ons.py`: download por ano no período, filtro por CEG, versão mais recente, identidade das horas, divergências DISPF × TEIP, recálculo e decomposição de TEIFa/TEIP, exportação CSV e planilha
- [X] T015 [US2] Etapa 3 em `src/main.py` (`--indicadores-only`, `--sem-indicadores`), respeitando `--raw-dir`/`--processed-dir`
- [X] T016 [US2] Constatações, seção, notas e abas `ONS_*` em `src/analyzer.py`; seção e indicador da capa em `src/pdf_generator.py`
- [X] T017 [US2] Testes em `tests/test_indicadores_ons.py` e etapa simulada em `tests/integration/test_pipeline.py` (correção de 02/10/2026: o teste de integração gravava nas pastas reais e acessava a rede)

---

## Phase 5: User Story 3 - Registro das conferências (Priority: P3) — realizada em 02/10/2026

- [X] T018 [US3] Conferências via servidor MCP do ONS (EVT no S3, geração por usina, dados hidrológicos, modalidade, catálogo) e busca no portal da ANEEL
- [X] T019 [US3] Registro consolidado em `specs/004-conferencia-outros/research.md` (Parte B), com lacunas a solicitar ao agente

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T020 [P] Revisar as specs 001, 002 e 003 para o estado implementado (mudanças de 30/09 e 02/10/2026 feitas sem spec), com `.2026-10-05.bak` e histórico de revisões
- [X] T021 [P] Atualizar `README.md` (fontes, saídas, comandos, histórico)
- [X] T022 Executar `pytest tests/ -v` com 100% de aprovação e sem alterar arquivos do projeto
- [X] T023 Regenerar planilha, Markdown e PDF e conferir visualmente a seção nova

---

## Registro de execução (05/10/2026)

- T003: 712 arquivos reaproveitados da exploração; na sincronização, os 708 arquivos do período foram aceitos pelo manifesto (`CACHED`), sem novo download.
- T012: SC-001 — 708 dias com arquivo, 20 dias ausentes listados, 0 dias incompletos, 708 datas internas conferidas; SC-002 — 1.908 h paradas com EVT = 1.739 (programação ≤ 1 MW) + 169 (> 1 MW); SC-003 — 2ª execução: 708 `CACHED`, 0 downloads; SC-004 — números da constatação conferidos com a aba `PROG_RESUMO_MENSAL`; SC-005 — ~20 s com os arquivos locais (a 1ª versão levava 7,5 min e foi otimizada); SC-006 — hash da base de EVT idêntico antes e depois.
- T022: 70 testes aprovados, sem rede.

## Dependencies & Execution Order

- Phase 1 → Phase 2 → Phase 3 (US1).
- US2 e US3 já concluídas; não bloqueiam US1.
- T004 pode ser escrito em paralelo a T005–T008; T009–T011 dependem de T008.
- T020 e T021 podem rodar em paralelo a US1; T022 e T023 por último.

## Implementation Strategy

1. Setup e Foundational (T001–T003).
2. US1 completa (T004–T012) — MVP desta feature.
3. Polish (T020–T023).
