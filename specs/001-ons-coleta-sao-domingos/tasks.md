# Tasks: Coleta e Filtragem de Dados ONS - UHE São Domingos

**Feature**: Coleta e Filtragem de Dados ONS - UHE São Domingos  
**Branch**: `001-ons-coleta-sao-domingos`  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Revisão de 2026-10-05**: as tarefas originais (Phases 1 a 6) foram mantidas como executadas em 30/09/2026; as que foram substituídas pela revisão pós-auditoria estão anotadas com "(substituída em 30/09/2026 — ver Fase 7)". As Phases 7 e 8 registram o que foi efetivamente feito depois. A versão anterior está em `tasks.md.2026-10-05.bak` (e a de 30/09/2026, em `tasks.md.bak`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização da estrutura de diretórios, ambiente de execução e dependências.

- [X] T001 Create project directories `data/raw/`, `data/processed/`, `src/`, `tests/unit/`, and `tests/integration/`
- [X] T002 Create `.gitignore` at repository root ignoring `data/raw/`, `venv/`, `__pycache__/`, and `.pytest_cache/`
- [X] T003 [P] Create `requirements.txt` with dependencies (`requests>=2.31.0`, `pandas>=2.0.0`, `pytest>=7.0.0`)
- [X] T004 Install dependencies into `venv` via PowerShell in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura básica e compartilhada que bloqueia a implementação das histórias de usuário.

- [X] T005 [P] Implement global configuration in `src/config.py` (paths for `data/raw`, `data/processed`, ONS CKAN API endpoint `"https://dados.ons.org.br/api/3/action/package_show?id=energia-vertida-turbinavel"`, canonical filter key `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"`, and secondary search term `"SAO DOMINGOS"`) (substituída em 30/09/2026 — ver Fase 7)
- [X] T006 [P] Implement structured logging configuration and custom exceptions in `src/logger.py`
- [X] T007 Create pytest fixtures and synthetic ONS CSV generators in `tests/conftest.py` (substituída em 30/09/2026 — ver Fase 7)

**Checkpoint**: Fundação técnica estabelecida. As fases de histórias de usuário podem prosseguir.

---

## Phase 3: User Story 1 - Descoberta e Download Completo dos Conjuntos Históricos de Dados (Priority: P1) 🎯 MVP

**Goal**: Descobrir dinamicamente e baixar via streaming 100% dos arquivos CSV históricos de Energia Vertida Turbinável do ONS para `data/raw/` de forma idempotente e com tolerância a falhas de rede.

**Independent Test**: Executar teste automatizado do coletor contra mock da API CKAN do ONS, verificando mapeamento de todos os recursos CSV, download em chunks e verificação de cache local.

### Tests for User Story 1
- [X] T008 [P] [US1] Implement unit tests for CKAN resource discovery, URL extraction, and cached/resilient download in `tests/unit/test_collector.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 1
- [X] T009 [US1] Implement data entity `RecursoONS` in `src/models.py` with fields `id_recurso` (UUID não nulo), `nome_recurso` (não nulo), `url_download` (HTTPS válido), `formato` ("CSV"), `tamanho_bytes` (>= 0), `arquivo_local`, `status_sincronizacao` (`PENDING`, `DOWNLOADED`, `CACHED`, `FAILED`) (substituída em 30/09/2026 — ver Fase 7)
- [X] T010 [US1] Implement discovery and streaming download engine in `src/collector.py` (calling CKAN `package_show`, parsing all CSV resources, checking existing file size/Content-Length for idempotency, streaming in 1 MB chunks with retry logic) (substituída em 30/09/2026 — ver Fase 7)

**Checkpoint**: User Story 1 funcional de forma independente. Todos os arquivos CSV do ONS podem ser baixados e armazenados em `data/raw/`.

---

## Phase 4: User Story 2 - Filtragem Exaustiva e Consolidação de Registros da UHE São Domingos (Priority: P1)

**Goal**: Inspecionar 100% dos arquivos CSV baixados, aplicar o filtro canônico `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"` e o rastreio abrangente de `"SAO DOMINGOS"`, consolidando medições horárias em base única ordenada.

**Independent Test**: Fornecer arquivos CSV sintéticos com dados válidos da usina, períodos vazios (ex.: 2015) e variações cadastrais, comprovando extração exata, rastreabilidade (`arquivo_origem`, `tipo_match`) e ordenação temporal.

### Tests for User Story 2
- [X] T011 [P] [US2] Implement unit tests for streaming CSV filtering, canonical key matching, and date sorting in `tests/unit/test_filter.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 2
- [X] T012 [P] [US2] Implement data entity `RegistroEnergiaVertida` in `src/models.py` with categorical attributes (`id_subsistema`, `nom_subsistema`, `nom_bacia`, `nom_rio`, `nom_agente`, `nom_reservatorio`, `cod_usina`), timestamp `din_instante` (`YYYY-MM-DD HH:MM:SS`), numeric measurements (`val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`), `arquivo_origem`, and `tipo_match` (`CANONICAL` ou `SECONDARY`) (substituída em 30/09/2026 — ver Fase 7)
- [X] T013 [US2] Implement streaming filter engine in `src/filter.py` (reading line-by-line with UTF-8 / Latin-1 fallback, delimiter `;`, canonical key matching, secondary term matching on column 5 `nom_reservatorio`, and tracking provenance) (substituída em 30/09/2026 — ver Fase 7)
- [X] T014 [US2] Implement consolidation and deduplication logic in `src/consolidator.py` (merging filtered records, sorting ascending by `din_instante`, deduplicating overlapping monthly/annual intervals, writing to `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv`) (substituída em 30/09/2026 — ver Fase 7)

**Checkpoint**: User Stories 1 e 2 funcionais. Base de dados analítica completa da UHE São Domingos gerada com sucesso.

---

## Phase 5: User Story 3 - Relatório de Auditoria e Validação da Varredura (Priority: P2)

**Goal**: Gerar relatório consolidado e rastreável de auditoria atestando a inspeção de 100% dos arquivos CSV históricos do portal do ONS.

**Independent Test**: Verificar se `data/processed/relatorio_auditoria_varredura.csv` é gerado com uma linha para cada arquivo CSV verificado, contendo contagem de linhas totais e linhas de São Domingos encontradas.

### Tests for User Story 3
- [X] T015 [P] [US3] Implement unit tests for audit metric collection and report export in `tests/unit/test_audit.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 3
- [X] T016 [US3] Implement `AuditoriaArquivo` data model in `src/models.py` with fields `nome_arquivo`, `periodo_referencia`, `total_linhas_arquivo`, `registros_canonicos_encontrados`, `registros_secundarios_encontrados`, `status_processamento`, `data_hora_processamento` (substituída em 30/09/2026 — ver Fase 7)
- [X] T017 [US3] Integrate audit metrics generation into `src/consolidator.py` to write `data/processed/relatorio_auditoria_varredura.csv` with semicolon delimiter and ISO timestamps (substituída em 30/09/2026 — ver Fase 7)

**Checkpoint**: Todas as histórias de usuário funcionais e auditáveis.

---

## Phase 6: Orchestration, CLI & Polish (Final Phase)

**Purpose**: Unificar os componentes na interface de linha de comando, executar testes de integração e validar conformidade final.

- [X] T018 Implement CLI interface in `src/main.py` per `contracts/cli-contract.md` supporting `--full-pipeline`, `--download-only`, `--filter-only`, `--raw-dir`, `--processed-dir`, `--filter-key`, `--secondary-term`, `--force-download`, `--log-level` (substituída em 30/09/2026 — ver Fase 7)
- [X] T019 [P] Implement end-to-end integration test in `tests/integration/test_pipeline.py` executing full pipeline with mock ONS responses and synthetic CSV datasets (substituída em 30/09/2026 — ver Fase 7)
- [X] T020 Run complete test suite (`pytest -v tests/`) and validate execution checklist per `specs/001-ons-coleta-sao-domingos/quickstart.md` (substituída em 30/09/2026 — ver Fase 7)

---

## Phase 7: Revisão pós-auditoria (30/09/2026 a 02/10/2026)

**Purpose**: Registrar as correções feitas por prompt, sem spec prévia, na auditoria de 30/09/2026 e os ajustes e a conferência externa de 02/10/2026. Motivo principal: a chave canônica dependia do nome do agente (CGT ELETROSUL até 02/2026, AXIA SUL desde 03/2026) e não casava com nenhum registro de 08/2018 a 02/2026; o cache por tamanho não detectava revisões do ONS.

**Independent Test**: `pytest tests/unit tests/integration` (15 testes) e conferência da base com o relatório de auditoria (42 arquivos, 70.895 registros, nenhuma `FALHA`, nenhuma divergência).

### Diagnóstico e configuração
- [X] T021 Auditar a extração original: constatar, no relatório de auditoria da versão original (`reports/_versao_anterior_2026-09-30/data_processed/relatorio_auditoria_varredura.csv`), `registros_canonicos_encontrados = 0` em todos os arquivos de 2018 a 02/2026, com os registros encontrados só pela busca secundária
- [X] T022 Substituir `CANONICAL_FILTER_KEY` e `SECONDARY_SEARCH_TERM` por `COD_USINA_ONS = 153` e `NOME_RESERVATORIO_REFERENCIA = "SAO DOMINGOS"` e acrescentar `RAW_MANIFEST_FILE` (`data/raw/_manifesto_ons.json`) em `src/config.py` (substitui T005)

### User Story 1 - Cache sensível às revisões do ONS
- [X] T023 [US1] Acrescentar `ultima_modificacao` e o status `UPDATED` a `RecursoONS` em `src/models.py` (substitui T009)
- [X] T024 [US1] Implementar em `src/collector.py` a leitura de `last_modified` do catálogo (com recurso a `metadata_modified`/`created`), `load_manifest`/`save_manifest` (gravação atômica, também em caso de falha), `_is_local_copy_current`, `_register_version`, download em `.part` com troca atômica, aviso de tamanho baixado diferente do publicado e resumo por status (substitui T010)
- [X] T025 [P] [US1] Reescrever `tests/unit/test_collector.py` com 6 testes (catálogo com `last_modified` e tamanho; download novo registrado no manifesto; arquivo existente aceito sem manifesto por tamanho; novo download por `last_modified` diferente; novo download por tamanho diferente; ida e volta do manifesto) e incluir `last_modified` no mock CKAN de `tests/conftest.py` (substitui T008)

### User Story 2 - Extração por código e nome, deduplicação por usina e instante
- [X] T026 [US2] Em `src/models.py`, trocar `tipo_match` para `CODIGO_E_NOME` e os contadores de `AuditoriaArquivo` para `registros_extraidos`, `registros_codigo_sem_nome`, `registros_nome_sem_codigo`, acrescentando `codificacao` e o carimbo UTC por `datetime.now(timezone.utc)` (substitui T012, T016)
- [X] T027 [US2] Reescrever `src/filter.py`: `normalize_text`, colunas localizadas pelo nome no cabeçalho, extração por `cod_usina` + nome do reservatório normalizado, contagem e aviso de divergências, releitura integral em Latin-1, status `FALHA` para arquivo vazio, sem colunas de identificação (`FilterError`) ou com erro de leitura (substitui T013)
- [X] T028 [US2] Reescrever `consolidate_records` em `src/consolidator.py`: chave (`cod_usina`, `din_instante`), prevalência do último arquivo lido, contagem de duplicatas idênticas e conflitantes com aviso no log, ordenação por (`din_instante`, `cod_usina`) (substitui T014)
- [X] T029 [P] [US2] Acrescentar a `tests/conftest.py` as linhas sintéticas com agente antigo (`CGT ELETROSUL`), código 153 com outro reservatório e reservatório homônimo (`SAO DOMINGOS II`) com outro código; reescrever `tests/unit/test_filter.py` com 7 testes (conversão de linha; extração com os dois agentes e contagem de divergências; arquivo sem a usina; Latin-1; ordenação e deduplicação; duplicata conflitante; usinas diferentes no mesmo instante) (substitui T007, T011)

### User Story 3 - Relatório de auditoria
- [X] T030 [US3] Atualizar `AUDIT_CSV_COLUMNS` e `save_audit_report` em `src/consolidator.py` e `tests/unit/test_audit.py` para as 9 colunas do relatório (substitui T015, T017)

### CLI, integração e execução
- [X] T031 Em `src/main.py`, substituir `--filter-key`/`--secondary-term` por `--cod-usina`/`--nome-reservatorio`, deixando o resumo final com a lista de arquivos com `FALHA` e o total de linhas divergentes e o retorno 2 quando há `FALHA` (substitui T018)
- [X] T032 Reescrever `tests/integration/test_pipeline.py` para validar a extração por código e nome, a exclusão da linha de outro reservatório, a contagem de divergência e o status por arquivo (substitui T019)
- [X] T033 Reexecutar o pipeline em 30/09/2026 sobre `data/raw/`: 41 arquivos aceitos como versão atual (`ARQUIVO_EXISTENTE` em `data/raw/_manifesto_ons.json`) e 1 baixado novamente (`ENERGIA_VERTIDA_TURBINAVEL_2026_09.csv`, republicado pelo ONS); resultado em `data/processed/`: 42 arquivos auditados, 70.895 registros (28/08/2018 00h a 28/09/2026 23h), nenhuma `FALHA`, nenhuma divergência, nenhuma duplicata
- [X] T034 Rodar a suíte da feature (`pytest tests/unit tests/integration`): 15 testes aprovados (reverificado em 05/10/2026) (substitui T020)
- [X] T035 [P] Atualizar `README.md` com a metodologia de extração e de atualização, a cobertura (usina a partir de 28/08/2018; 2015 a 2017 sem registros) e o histórico de 30/09/2026

### Conferência e ajustes de 02/10/2026
- [X] T036 Conferir a base consolidada com os dados do ONS pelo servidor MCP `ons-dados` (`.mcp.json`): idêntica ao S3 do ONS em todos os meses de 08/2018 a 08/2026 (registrado em `research.md`, seção 7)
- [X] T037 Incluir a etapa 3 e as opções `--indicadores-only`/`--sem-indicadores` em `src/main.py` e simular `executar_indicadores_ons` em `tests/integration/test_pipeline.py`. Escopo de `specs/004-conferencia-outros`, citado aqui só porque altera arquivos desta feature.

**Checkpoint**: Pipeline da feature 001 alinhado aos fatos da fonte (troca de agente, revisões do ONS) e base conferida externamente.

---

## Phase 8: Revisão retroativa da documentação (05/10/2026)

**Purpose**: Alinhar os artefatos Spec Kit desta feature ao código em vigor (SDD retroativo).

- [X] T038 Revisar `spec.md` (status, requisitos e Histórico de revisões), `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/cli-contract.md`, `tasks.md` e `checklists/requirements.md`, com cópia prévia `*.2026-10-05.bak` de cada arquivo

### Pendências identificadas (não executadas nesta revisão)
- [X] T039 Emendar o princípio IV de `.specify/memory/constitution.md`, que ainda cita a chave `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"`, pelo processo de governança (justificativa, versão e Sync Impact Report) (resolvida em 05/10/2026: constituição 1.1.0)
- [X] T040 Registrar em log, em `src/filter.py`, as linhas descartadas por número insuficiente de campos (princípio IV) (resolvida em 05/10/2026: spec 005, US4)
- [X] T041 Preservar, em `src/collector.py`, a versão anterior de um arquivo bruto antes de substituí-lo por versão revisada pelo ONS, ou emendar a regra de preservação (princípio V) (resolvida em 05/10/2026: spec 005, US1)
- [X] T042 Propagar `--log-level` aos loggers `collector`, `filter` e `consolidator` (`src/main.py`, `src/logger.py`) ou ajustar o contrato (resolvida em 05/10/2026: spec 005, US3)
- [X] T043 Versionar script e saída reproduzíveis da conferência externa de 02/10/2026 (encerrada em 05/10/2026 por decisão do usuário: não necessária; o resultado da conferência de 02/10/2026 fica registrado em specs/004-conferencia-outros/research.md, Parte B)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Sem dependências, inicia imediatamente.
- **Phase 2 (Foundational)**: Depende da Phase 1. Bloqueia todas as User Stories.
- **Phase 3 (User Story 1 - P1)**: Depende da Phase 2.
- **Phase 4 (User Story 2 - P1)**: Depende da Phase 2 e consome dados de US1.
- **Phase 5 (User Story 3 - P2)**: Depende da Phase 4 para auditoria dos arquivos processados.
- **Phase 6 (Orchestration & Polish)**: Depende da conclusão de US1, US2 e US3.
- **Phase 7 (Revisão pós-auditoria)**: Depende das Phases 1 a 6. T022 antecede T023 a T031; T033 depende de T024, T027, T028 e T031; T036 depende de T033.
- **Phase 8 (Revisão da documentação)**: Depende da Phase 7. As pendências T039 a T043 são independentes entre si.

### Parallel Opportunities
- Setup: T003 e T004 podem ser preparados em paralelo à configuração inicial.
- Foundational: T005, T006 e T007 podem ser implementados em paralelo.
- User Stories:
  - Testes unitários (T008, T011, T015) podem ser desenvolvidos em paralelo aos seus respectivos modelos.
  - Modelos de dados (T009, T012, T016) residem em `src/models.py`.
- Revisão pós-auditoria: T025, T029 e T035 (testes e README) podem correr em paralelo às alterações de código da mesma história.

---

## Parallel Example: User Story 1 & 2 Tests

```bash
# Execução paralela de testes unitários:
pytest tests/unit/test_collector.py tests/unit/test_filter.py
```

---

## Implementation Strategy

### MVP First (User Story 1)
1. Concluir Setup (Phase 1) e Foundational (Phase 2).
2. Implementar Coletor e Download (Phase 3 - US1).
3. Validar download de amostras reais do ONS em `data/raw/`.

### Entrega Incremental
1. Adicionar Filtragem e Consolidação (Phase 4 - US2).
2. Validar integridade da base consolidada da UHE São Domingos.
3. Adicionar Relatório de Auditoria (Phase 5 - US3).
4. Concluir orquestrador CLI `src/main.py` e testes de integração (Phase 6).

### Correção pós-auditoria
1. Trocar o critério de identificação e o cache (Phase 7, T022 a T032).
2. Reexecutar sobre os brutos existentes e conferir a auditoria (T033, T034).
3. Conferir a base com uma fonte externa do ONS (T036).
4. Regularizar a documentação e registrar as pendências (Phase 8).
