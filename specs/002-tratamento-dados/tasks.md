# Tasks: Tratamento, Padronização e Validação Física dos Dados - UHE São Domingos

**Feature**: `002-tratamento-dados` | **Branch**: `002-tratamento-dados` | **Spec**: [specs/002-tratamento-dados/spec.md](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/002-tratamento-dados/spec.md) | **Plan**: [specs/002-tratamento-dados/plan.md](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/002-tratamento-dados/plan.md)

**Revisão retroativa (2026-10-05)**: as tarefas originais (T001 a T025) foram mantidas. As superadas pela auditoria de 30/09/2026 estão marcadas com "(substituída em 30/09/2026 — ver Fase N)". As tarefas efetivamente realizadas na auditoria estão na Phase 7 e as da regularização documental na Phase 8. A versão anterior está em `tasks.md.2026-10-05.bak`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização de dependências analíticas e constantes de configuração

- [X] T001 Atualizar dependências analíticas adicionando `openpyxl>=3.1.0` e `pyarrow>=14.0.0` em `requirements.txt`
- [X] T002 [P] Instalar novas dependências no ambiente virtual em `.\venv` via `pip install -r requirements.txt`
- [X] T003 [P] Atualizar caminhos de exportação (`.xlsx`, `.parquet`, `.csv`), mapeamento de schemas e tolerância matemática (`10^-4`) em `src/config.py` (parcialmente substituída em 30/09/2026 — ver Fase 7: as faixas `EXPECTED_PHYSICAL_BOUNDS` deram lugar aos parâmetros da usina e aos limites de R6 a R9, T030)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura de leitura do dicionário de dados oficial e integridade de carregamento

**⚠️ CRITICAL**: Nenhuma tarefa de história de usuário pode iniciar antes da conclusão desta fase.

- [X] T004 Criar leitor e parser do esquema oficial `DicionarioDados_EnergiaVertidaTurbinavel.json` em `src/validator.py`
- [X] T005 [P] Implementar carregador de dados com validação de colunas obrigatórias e metadados de rastreabilidade (`arquivo_origem`, `tipo_match`) em `src/validator.py`
- [X] T006 [P] Configurar estrutura de logging e tratamento de exceções de I/O em `src/processor.py`

**Checkpoint**: Base foundational validada e pronta para implementação das histórias de usuário.

---

## Phase 3: User Story 1 - Padronização e Tipagem Estrita das Colunas Numéricas (Priority: P1) 🎯 MVP

**Goal**: Garantir que as 10 colunas operacionais (`val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`) possuam tipo numérico contínuo (`float64`) e exportar em `.xlsx`, `.parquet` e `.csv`.

**Independent Test**: Inspecionar o schema e os dtypes do DataFrame processado comprovando 100% de tipos `float64` nas 10 colunas, e verificar a integridade física dos arquivos exportados em `data/processed/uhe_sao_domingos_energia_vertida_tratado.xlsx`, `.parquet` e `.csv`.

### Tests for User Story 1 🧪
- [X] T007 [P] [US1] Criar testes unitários de coerção e exportação multi-formato em `tests/test_processor.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 1
- [X] T008 [US1] Implementar função de coerção de tipos estrita `padronizar_tipagem_numerica(df)` com `pd.to_numeric(errors='coerce')` em `src/processor.py` (substituída em 30/09/2026 — ver Fase 7: ausentes deixaram de ser convertidos em zero)
- [X] T009 [P] [US1] Implementar exportador nativo Excel (`.xlsx`) via `openpyxl` garantindo formato numérico de ponto flutuante em `src/processor.py`
- [X] T010 [P] [US1] Implementar exportador Apache Parquet (`.parquet`) via `pyarrow` com schema binário estrito `DOUBLE` e `TIMESTAMP_MICROS` em `src/processor.py`
- [X] T011 [P] [US1] Implementar exportador CSV padronizado (`.csv`) com delimitador `;` e ponto decimal em `src/processor.py` (substituída em 30/09/2026 — ver Fase 7: precisão integral, sem arredondamento)
- [X] T012 [US1] Integrar pipeline de padronização e exportação com CLI flags (`--input-file`, `--output-dir`, `--export-formats`) em `src/processor.py`

**Checkpoint**: User Story 1 completa e testável de forma independente (MVP alcançado).

---

## Phase 4: User Story 2 - Validação Física, Regulatória e Auditoria de Consistência (Priority: P1)

**Goal**: Auditar 100% dos 70.895 registros contra as 5 regras físicas e equações do `DicionarioDados_EnergiaVertidaTurbinavel.json`, atestando a inexistência de números negativos ou valores absurdos.

**Independent Test**: Executar a suíte de validação física sobre a base consolidada e emitir relatório de auditoria comprovando taxa de conformidade de 100% em todas as regras.

> **Revisão (2026-10-05)**: meta e teste independente substituídos em 30/09/2026 — ver Fase 7. A história passou a ter 9 regras (R1 a R5 de consistência interna e R6 a R9 de plausibilidade física), com o resultado apurado e não pressuposto; as faixas de valores não vêm do dicionário, que não as contém.

### Tests for User Story 2 🧪
- [X] T013 [P] [US2] Criar testes unitários e de tolerância matemática das 5 regras físicas em `tests/test_validator.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 2
- [X] T014 [US2] Implementar regra R1 de Não-Negatividade: `val_x >= 0, para toda coluna val_*` e limites físicos esperados em `src/validator.py` (parcialmente substituída em 30/09/2026 — ver Fase 7: R1 passou a contar registros com tolerância `-10^-4`; os "limites físicos esperados" deram lugar a R6)
- [X] T015 [US2] Implementar regras R2 e R3 de Conservação: `val_energiavertida >= val_energiavertidaturbinavel` e `val_vazaovertida >= val_vazaovertidaturbinavel + val_vazaovertidanaoturbinavel - 10^-4` em `src/validator.py`
- [X] T016 [US2] Implementar regra R4 de Potência Hidráulica Turbinável: `|val_energiavertidaturbinavel - (val_vazaovertidaturbinavel * val_produtividade)| <= 10^-4` em `src/validator.py`
- [X] T017 [US2] Implementar regra R5 de Folga Operacional: `|val_folgadegeracao - max(0, val_disponibilidade - val_geracao)| <= 10^-4` em `src/validator.py`
- [X] T018 [US2] Implementar gerador de relatório de auditoria física em `data/processed/relatorio_validacao_fisica.md` e `data/processed/relatorio_validacao_fisica.csv` em `src/validator.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T019 [US2] Integrar validação física e emissão de relatório à CLI (`--validate-physics`, `--generate-report`) em `src/processor.py` (substituída em 30/09/2026 — ver Fase 7: as opções não podiam ser desligadas)

**Checkpoint**: User Story 2 concluída com validação hidrotécnica auditável.

---

## Phase 5: User Story 3 - Perfilamento Estatístico e Sumário Analítico de Vertimento (Priority: P2)

**Goal**: Gerar perfilamento estatístico das variáveis críticas de vertimento por ano de operação (2018 a 2026), com métricas descritivas e indicadores de horas de vertimento.

**Independent Test**: Gerar a tabela agregada anual contendo total de horas, energia vertida turbinável (soma MWh e pico MWmed), energia vertida total e produtividade média, validando consistência temporal.

> **Revisão (2026-10-05)**: história transferida para a Feature 003 em 30/09/2026 — ver Fase 7 (T039). O perfil anual é produzido por `calcular_perfil_estatistico_anual` em `src/analyzer.py`.

### Tests for User Story 3 🧪
- [X] T020 [P] [US3] Criar testes para agregação e perfilamento estatístico anual em `tests/test_processor.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 3
- [X] T021 [US3] Implementar cálculo de agregados estatísticos anuais (horas com vertimento > 0, soma MWh, média, quartis, desvio-padrão) em `src/processor.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T022 [US3] Integrar a seção de perfilamento estatístico anual ao relatório executivo `data/processed/relatorio_validacao_fisica.md` e CSV em `src/processor.py` (substituída em 30/09/2026 — ver Fase 7)

**Checkpoint**: Todas as histórias de usuário funcionais e testáveis.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificação final de qualidade, execução ponta a ponta e documentação

- [X] T023 [P] Atualizar documentação e instruções de execução em `README.md` (substituída em 30/09/2026 — ver Fase 7)
- [X] T024 Executar validação de ponta a ponta gerando os arquivos tratados em `data/processed/` conforme `specs/002-tratamento-dados/quickstart.md` (substituída em 30/09/2026 — ver Fase 7)
- [X] T025 [P] Executar suíte completa de testes com `pytest tests/ -v` assegurando 100% de aprovação e zero regressões (substituída em 30/09/2026 — ver Fase 8: os testes foram reescritos depois desta execução)

---

## Phase 7: Revisão pós-auditoria (30/09/2026 a 02/10/2026)

**Purpose**: Correções identificadas na auditoria de 30/09/2026, implementadas por prompt diretamente no código e registradas retroativamente em 2026-10-05.

**Independent Test**: `data/processed/relatorio_validacao_fisica.md` de 30/09/2026 com o resultado de R1 a R9 sobre 70.895 registros e base tratada com 25 colunas e 526 registros sinalizados.

### Tipagem e exportação (US1)
- [X] T026 [US1] Remover o preenchimento de ausentes com zero em `padronizar_tipagem_numerica`: métricas em `float64` com NaN preservado e contagem de ausentes por coluna em log, em `src/processor.py`
- [X] T027 [US1] Converter vírgula decimal e remover espaços nas métricas lidas como texto antes de `pd.to_numeric`, em `src/processor.py`
- [X] T028 [US1] Tipar `cod_usina` como `Int64` (aviso para código inválido) e interromper com `ValueError` quando houver `din_instante` inválido, em `src/processor.py`
- [X] T029 [P] [US1] Gravar o CSV tratado com precisão integral, `;`, UTF-8 e datas `%Y-%m-%d %H:%M:%S` em `exportar_csv`, em `src/processor.py`

### Parâmetros da usina
- [X] T030 [P] Substituir `EXPECTED_PHYSICAL_BOUNDS` pelos parâmetros técnicos da usina com fonte (`FONTE_PARAMETROS_USINA = "RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3"`), grandezas derivadas (`ENGOLIMENTO_MAXIMO_USINA_M3S`, `PRODUTIVIDADE_NOMINAL_MW_M3S`) e limites de R6 a R8 (`TOLERANCIA_LIMITES_FISICOS`, `FAIXA_PRODUTIVIDADE_RELATIVA`, `TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW`, `LIMITES_FISICOS_SUPERIORES`) em `src/config.py`; R9 usa `LIMIAR_GERACAO_PARADA_MW`, definido no mesmo arquivo na seção da Feature 003

### Validação e sinalização (US2)
- [X] T031 [US2] Reorganizar `validar_regras_fisicas` em dois grupos (`GRUPO_CONSISTENCIA` para R1 a R5, `GRUPO_PLAUSIBILIDADE` para R6 a R9), com retorno `(DataFrame, List[RegraResultado])` e R1 contando registros em vez de células, em `src/validator.py`
- [X] T032 [US2] Implementar R6 a R9 em `mascaras_plausibilidade` (fonte única para contagem e sinalização) e `faixa_produtividade`, em `src/validator.py`
- [X] T033 [US2] Não contar valores ausentes como violação (`_coagir_metricas` sem preenchimento) e registrar o total de ausentes em log, em `src/validator.py`
- [X] T034 [US2] Implementar `sinalizar_anomalias` (colunas de `COLUNAS_ANOMALIA` e `qualidade_registro`) em `src/validator.py` e aplicá-la antes dos relatórios e da exportação em `src/processor.py`
- [X] T035 [US2] Conferir as colunas métricas com o dicionário (`verificar_colunas_no_dicionario`) e citar a versão (`versao_dicionario_dados`) no relatório, em `src/validator.py` e `src/processor.py`
- [X] T036 [US2] Reescrever `gerar_relatorio_validacao_md` e `gerar_relatorio_validacao_csv` (texto derivado de `df_res`, ressalva sobre R1 a R5, primeiros 40 registros sinalizados), com números e datas no padrão brasileiro de `src/formatacao.py`, em `src/validator.py`
- [X] T037 [US2] Restringir o código de saída 3 às violações de R1 em `executar_pipeline_tratamento`, em `src/processor.py`
- [X] T038 Trocar `--validate-physics` e `--generate-report` por `argparse.BooleanOptionalAction` e aplicar `--log-level` aos loggers `processor` e `validator`, em `src/processor.py`

### Perfil anual (US3)
- [X] T039 [US3] Retirar o perfil estatístico anual de `src/processor.py` e do relatório de validação; o perfil passa a ser produzido pela Feature 003 (`calcular_perfil_estatistico_anual` em `src/analyzer.py`, saídas `reports/perfil_estatistico_anual.xlsx` e `.csv`)

### Testes
- [X] T040 [P] [US1] Reescrever `tests/test_processor.py` (6 testes): ausentes não viram zero, instante inválido rejeitado, células numéricas no `.xlsx`, `double` no `.parquet`, precisão integral no `.csv` e pipeline sobre base sintética com 1 registro sinalizado (20/02/2024 10h)
- [X] T041 [P] [US2] Reescrever `tests/test_validator.py` (15 casos): dicionário e versão, linha conforme nas 9 regras, R1 por registro, R2 a R5, R6 (68,7 MW), tolerância de R7, R8 só com vazão turbinada, R9, ausentes, sinalização (`R6;R7;R8`), texto do relatório e `test_base_real_estrutura` (substitui `test_validacao_base_real_100_pct_conforme`, sem fixar contagens da série)
- [X] T042 [P] Implementar `gerar_df_sintetico` e a fixture `df_sintetico` em `tests/conftest.py` (nov/2023 a fev/2024, identidades do ONS respeitadas, 1 registro anômalo), usadas também pelos testes da Feature 003

### Saídas, preservação e documentação
- [X] T043 Preservar os relatórios de validação anteriores em `reports/_versao_anterior_2026-09-30/data_processed/`, com aviso em `reports/_versao_anterior_2026-09-30/LEIA-ME.txt`
- [X] T044 Regenerar as saídas com `python -m src.processor` (30/09/2026): `data/processed/uhe_sao_domingos_energia_vertida_tratado.xlsx`, `.parquet` e `.csv` (70.895 registros, 25 colunas) e `data/processed/relatorio_validacao_fisica.md` e `.csv` (R1 a R5 sem violação; R6 = 1, R7 = 293, R8 = 185, R9 = 63; 526 registros sinalizados)
- [X] T045 [P] Atualizar `README.md` (estrutura de artefatos, metodologia de validação R1 a R9 e histórico de 30/09/2026 e 02/10/2026)
- [X] T046 Gravar cópia de segurança do código e dos testes aprovados, incluindo `src/processor.py`, `src/validator.py`, `src/config.py`, `tests/test_processor.py` e `tests/test_validator.py`, em `_backup_2026-10-02_relatorio_aprovado/` (02/10/2026)

**Checkpoint**: Implementação corrigida; documentação da feature ainda descrevia a versão original.

---

## Phase 8: Regularização da documentação (05/10/2026)

**Purpose**: SDD retroativo: alinhar os documentos da feature ao código.

- [X] T047 Copiar os 8 documentos da feature para `*.2026-10-05.bak` antes de editá-los, em `specs/002-tratamento-dados/`
- [X] T048 Revisar `spec.md` (Status, FR-001 a FR-019, SC-001 a SC-006 e Histórico de revisões), `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/cli-contract.md`, `tasks.md` e `checklists/requirements.md` conforme `src/processor.py`, `src/validator.py`, `src/config.py`, os testes e `data/processed/relatorio_validacao_fisica.md`
- [X] T049 Conferir que as alterações posteriores em `src/config.py` (garantia física em 02/10/2026; constantes da spec 004 em 05/10/2026) não mudaram os parâmetros de R6 a R9: os limites do relatório de 30/09/2026 (50,4 MW; 171,2 m³/s; 0,214 a 0,398 MW/(m³/s)) coincidem com os valores atuais
- [X] T050 Executar `pytest tests/test_processor.py tests/test_validator.py -v` e registrar o resultado (não executado nesta revisão; o único registro em `.pytest_cache` é de 30/09/2026 12:24, anterior à reescrita dos testes, com os nomes de teste antigos) (resolvida em 05/10/2026: 87 testes aprovados (spec 005, T026))

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Sem dependências — execução imediata.
- **Foundational (Phase 2)**: Depende de Phase 1 — BLOQUEIA todas as histórias de usuário.
- **User Stories (Phases 3, 4, 5)**:
  - US1 (Phase 3) pode iniciar imediatamente após Foundational.
  - US2 (Phase 4) depende de US1 para obter o DataFrame estritamente tipado.
  - US3 (Phase 5) depende de US1 e US2 para agregar os dados validados.
- **Polish (Phase 6)**: Depende de todas as histórias de usuário concluídas.
- **Revisão pós-auditoria (Phase 7)**: Depende das Phases 1 a 6. Dentro dela: T030 (parâmetros) antes de T032; T031 a T034 antes de T036 e T044; T040 a T042 em paralelo com a implementação; T044 depois de todas as mudanças de código.
- **Regularização da documentação (Phase 8)**: Depende da Phase 7. T047 antes de T048.

### Parallel Opportunities
- **Setup**: `T002` (pip install) e `T003` (config.py) podem rodar em paralelo após `T001`.
- **Foundational**: `T005` (loader) e `T006` (logger) podem ser implementados em paralelo após `T004`.
- **User Story 1**: Exportadores `T009` (.xlsx), `T010` (.parquet) e `T011` (.csv) podem ser implementados em paralelo após `T008`.
- **User Story 2**: Testes `T013` e regras de validação física `T014`, `T015`, `T016`, `T017` podem ser desenvolvidas em paralelo.
- **Polish**: `T023` (documentação) e `T025` (testes automatizados) podem executar em paralelo.
- **Revisão pós-auditoria**: `T029` (CSV) e `T030` (config.py) em arquivos/funções independentes; `T040`, `T041` e `T042` (testes) em paralelo; `T045` (README) em paralelo com `T044`.

---

## Parallel Example: User Story 1

```powershell
# Execução paralela dos exportadores de saída (arquivos e responsabilidades isoladas):
Task: "Implementar exportador nativo Excel (.xlsx) via openpyxl em src/processor.py"
Task: "Implementar exportador Apache Parquet (.parquet) via pyarrow em src/processor.py"
Task: "Implementar exportador CSV padronizado (.csv) em src/processor.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Concluir Setup (Phase 1) e Foundational (Phase 2).
2. Concluir User Story 1 (Phase 3).
3. **VALIDAR MVP**: Abrir `uhe_sao_domingos_energia_vertida_tratado.xlsx` no Excel e verificar que todas as colunas métricas aparecem nativamente como números, sem erros de formatação.
4. Prosseguir para User Story 2 (Auditoria Física) e User Story 3 (Perfilamento Estatístico).

### Correção pós-auditoria (registrada em 2026-10-05)
1. Corrigir a tipagem (ausentes preservados) e a exportação (CSV com precisão integral) — T026 a T029.
2. Introduzir os parâmetros da usina e as regras R6 a R9 com sinalização sem remoção — T030 a T035.
3. Reescrever o relatório e ajustar código de saída e CLI — T036 a T038.
4. Transferir o perfil anual para a Feature 003 — T039.
5. Reescrever os testes, regenerar as saídas e atualizar o README — T040 a T046.
6. Regularizar a documentação Spec Kit — T047 a T049; pendente T050.
