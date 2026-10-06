# Tasks: Análise Estatística, Indicadores Operacionais, Visualização Gráfica e Relatório - UHE São Domingos

**Feature**: `003-analise-dados` | **Branch**: `003-analise-dados` | **Spec**: [specs/003-analise-dados/spec.md](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/003-analise-dados/spec.md) | **Plan**: [specs/003-analise-dados/plan.md](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/003-analise-dados/plan.md)

> **Revisão retroativa (2026-10-05)**: as fases 1 a 6 são as tarefas originais de 30/09/2026, mantidas como registro. Marcadores acrescentados: **(substituída em 30/09/2026 — ver Fase 7)** = tarefa cujo resultado foi descartado e refeito na revisão pós-auditoria; **(ajustada em 30/09/2026 — ver Fase 7)** = tarefa mantida, mas alterada depois. A Fase 7 registra o que foi efetivamente feito por prompt entre 30/09 e 02/10/2026, sem spec; a Fase 8, a regularização da documentação e as pendências encontradas. Versão anterior em `tasks.md.2026-10-05.bak`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialização de dependências de visualização estatística e diretórios de relatórios

- [X] T001 Adicionar dependências analíticas `seaborn>=0.13.0` e `matplotlib>=3.8.0` em `requirements.txt` (substituída em 30/09/2026 — ver Fase 7: o seaborn deixou de ser usado, mas continua no `requirements.txt`)
- [X] T002 [P] Instalar novas dependências no ambiente virtual em `.\venv` via `pip install -r requirements.txt`
- [X] T003 [P] Atualizar caminhos de relatórios (`reports/`, `reports/figures/`) e parâmetros de plotagem em `src/config.py` (ajustada em 30/09/2026 — ver Fase 7)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura de ingestão da base tratada e preparação do ambiente analítico

**⚠️ CRITICAL**: Nenhuma tarefa de história de usuário pode iniciar antes da conclusão desta fase.

- [X] T004 Implementar carregador de dados tratados a partir de Parquet ou Excel em `src/analyzer.py` (ajustada em 30/09/2026 — ver Fase 7)
- [X] T005 [P] Configurar estrutura de logging, criação automática de diretórios e tratamento de exceções de I/O em `src/analyzer.py` (ajustada em 30/09/2026 — ver Fase 7)

**Checkpoint**: Base analítica carregada e módulo `src/analyzer.py` pronto para cálculo das histórias de usuário.

---

## Phase 3: User Story 1 - Avaliação Estatística Anual e Mapeamento de Extremos (Priority: P1) 🎯 MVP

**Goal**: Computar perfil estatístico anual completo para as 10 variáveis operacionais contínuas e mapear os valores mínimos e máximos com suas datas e horas exatas de ocorrência.

**Independent Test**: Executar a função de perfilamento sobre a base tratada e verificar que as tabelas resultantes contêm contagem, média, desvio, mediana, quartis, e valores mínimos e máximos acompanhados de timestamps exatos para todos os 9 exercícios.

### Tests for User Story 1 🧪
- [X] T006 [P] [US1] Criar testes unitários para perfilamento estatístico e mapeamento de extremos em `tests/test_analyzer.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 1
- [X] T007 [US1] Implementar cálculo de momentos estatísticos anuais (média, desvio, mediana, quartis, soma) para as 10 variáveis contínuas em `src/analyzer.py` (ajustada em 30/09/2026 — ver Fase 7)
- [X] T008 [US1] Implementar função de mapeamento de recordes mínimos e máximos com extração de timestamp exato (`din_instante`) em `src/analyzer.py` (ajustada em 30/09/2026 — ver Fase 7)
- [X] T009 [P] [US1] Implementar exportador de tabelas de perfilamento e extremos para Excel (`reports/perfil_estatistico_anual.xlsx`) e CSV em `src/analyzer.py` (ajustada em 30/09/2026 — ver Fase 7)

**Checkpoint**: User Story 1 completa e testável de forma independente (MVP analítico alcançado).

---

## Phase 4: User Story 2 - Diagnóstico Regulatório e Avaliação de Performance (Priority: P1)

**Goal**: Calcular indicadores setoriais da usina (Fator de Capacidade, Fator de Disponibilidade, Índice de Vertimento Turbinável) com benchmark de 48 MW e emitir parecer fundamentado sobre a performance. *(Objetivo substituído em 30/09/2026 — ver Fase 7: sem FID, sem parecer e sem atribuição de causa.)*

**Independent Test**: Confrontar os indicadores anuais calculados com as faixas normativas regulatórias e verificar que o relatório emite parecer objetivo (Satisfatório, Atenção ou Crítico) discriminando a causa do vertimento.

### Tests for User Story 2 🧪
- [X] T010 [P] [US2] Criar testes unitários para os índices regulatórios (FC, FID, FIT, IVT) e classificação de performance em `tests/test_analyzer.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 2
- [X] T011 [US2] Implementar cálculo dos índices de performance ($FC$, $FID$, $FIT$, $IVT$) com benchmark de 48 MW em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T012 [US2] Implementar motor de diagnóstico causal de vertimento (gargalo de 48 MW vs restrição ONS vs indisponibilidade) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T013 [US2] Implementar gerador do Relatório Executivo de Diagnóstico em Markdown (`reports/relatorio_analise_estatistica.md`) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)

**Checkpoint**: User Story 2 concluída com diagnóstico de performance e parecer regulatório auditável.

---

## Phase 5: User Story 3 - Visualização Gráfica Especializada com Seaborn (Priority: P2)

**Goal**: Gerar catálogo de figuras analíticas em alta resolução (300 DPI) cobrindo séries temporais, sazonalidade, dispersão de produtividade, boxplots e balanço hídrico. *(Catálogo substituído em 30/09/2026 — ver Fase 7: 5 figuras em matplotlib, sem seaborn.)*

**Independent Test**: Executar a suíte de plotagem e confirmar que os 5 arquivos de imagem PNG são gravados em `reports/figures/` com dimensões, títulos e eixos legíveis.

### Tests for User Story 3 🧪
- [X] T014 [P] [US3] Criar testes de geração e integridade das figuras gráficas em `tests/test_analyzer.py` (substituída em 30/09/2026 — ver Fase 7)

### Implementation for User Story 3
- [X] T015 [P] [US3] Implementar função de plotagem da Série Temporal Multi-Anual (`01_serie_temporal_geracao_vertimento.png`) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T016 [P] [US3] Implementar função de plotagem do Heatmap Sazonal Mês x Hora (`02_heatmap_sazonalidade_vertimento.png`) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T017 [P] [US3] Implementar função de plotagem do Scatterplot de Vazão vs Energia Turbinável (`03_dispersao_vazao_energia_produtividade.png`) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T018 [P] [US3] Implementar função de plotagem dos Boxplots Comparativos Anuais (`04_boxplots_distribuicao_anual.png`) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T019 [P] [US3] Implementar função de plotagem do Balanço Hídrico em Barras (`05_balanco_hidrico_anual_vazoes.png`) em `src/analyzer.py` (substituída em 30/09/2026 — ver Fase 7)
- [X] T020 [US3] Integrar rotinas gráficas e emissão de relatório à CLI (`python -m src.analyzer`) em `src/analyzer.py` (ajustada em 30/09/2026 — ver Fase 7)

**Checkpoint**: Todas as histórias de usuário funcionais e integradas.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificação final de qualidade, execução ponta a ponta e documentação

- [X] T021 [P] Atualizar documentação e novos comandos analíticos no `README.md` (substituída em 30/09/2026 — ver Fase 7)
- [X] T022 Executar validação de ponta a ponta gerando todos os relatórios e figuras conforme `specs/003-analise-dados/quickstart.md` (substituída em 30/09/2026 — ver Fase 7: os relatórios gerados nesta etapa continham informações incorretas e estão em `reports/_versao_anterior_2026-09-30/`)
- [X] T023 [P] Executar suíte completa de testes com `pytest tests/ -v` assegurando 100% de aprovação e zero regressões (substituída em 30/09/2026 — ver Fase 8, T062)

---

## Phase 7: Revisão pós-auditoria (30/09/2026 a 02/10/2026)

**Purpose**: Registrar as correções feitas por prompt, sem spec, depois que a auditoria de 30/09/2026 encontrou números e conclusões falsos fixos no código (fator de disponibilidade de 96,1%, parecer "SATISFATÓRIO", "cumpre integralmente ANEEL", vertimento atribuído à plena carga e ao 1º trimestre, período 18/05/2018 a 30/09/2026, turbinas "Francis", engolimento de 154 m³/s), e os ajustes de 02/10/2026.

**Independent Test**: `tests/test_analyzer.py` e `tests/test_pdf_generator.py` sobre a série sintética de `tests/conftest.py`; conferência do relatório pelo Cenário 5 de `quickstart.md`.

### Preservação da versão anterior (30/09/2026)
- [X] T024 Preservar os relatórios incorretos em `reports/_versao_anterior_2026-09-30/` (PDF, Markdown, planilha, CSV, figuras antigas e arquivos de validação), com `LEIA-ME.txt` listando os erros encontrados
- [X] T025 [P] Preservar as versões anteriores à auditoria dos módulos reescritos: `src/analyzer.py.bak`, `src/pdf_generator.py.bak`, `src/config.py.bak`, `tests/test_analyzer.py.bak` (cópias de 30/09/2026)

### Parâmetros e formatação
- [X] T026 Reescrever os parâmetros da usina em `src/config.py` com a fonte `FONTE_PARAMETROS_USINA` (RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3): `TIPO_TURBINA` Kaplan de eixo vertical, `ENGOLIMENTO_NOMINAL_UG_M3S` 81,5 (máximo derivado de 163 m³/s), `IP_REFERENCIA`, `TEIF_REFERENCIA`, `QUEDA_BRUTA_M`, `PERDA_HIDRAULICA_M`, `RENDIMENTO_TURBINA_GERADOR`, `VAZAO_REMANESCENTE_M3S`, `ANO_INICIO_OPERACAO_COMERCIAL`, e as derivadas `DISPONIBILIDADE_REFERENCIA` (90,97%) e `PRODUTIVIDADE_NOMINAL_MW_M3S`
- [X] T027 [P] Incluir os limiares de análise em `src/config.py`: `LIMIAR_GERACAO_PARADA_MW`, `FRACAO_PLENA_CARGA`, `LIMIAR_VERTIMENTO_MINIMO_M3S`, `LIMIAR_INDISPONIBILIDADE_TOTAL_MW`, `DURACAO_MINIMA_EVENTO_RELATORIO_H`, `NUMERO_EVENTOS_RELATORIO`, `HORAS_DIURNAS`, `HORAS_NOTURNAS`
- [X] T028 [P] Criar `src/formatacao.py` com a formatação no padrão brasileiro (`fmt_num`, `fmt_int`, `fmt_pct`, `fmt_pp`, `fmt_data`, `fmt_data_hora`, `fmt_mes_ano`, `fmt_lista`, `plural`)

### Análise em `src/analyzer.py`
- [X] T029 [US1] Criar `preparar_dados` e estender `carregar_dados_tratados` (aceita `.csv`; recalcula as sinalizações R6 a R9 com `sinalizar_anomalias` quando ausentes)
- [X] T030 [US1] Excluir os registros sinalizados de `calcular_perfil_estatistico_anual` e `mapear_extremos_historicos` (`_registros_validos`); renomear a contagem para `registros_considerados` e incluir `unidade`
- [X] T031 [US2] Implementar `analisar_cobertura` (horas ausentes e duplicadas, anos parciais, agentes, identificação, `_resumo_auditoria`, `_resumo_manifesto`)
- [X] T032 [US2] Reescrever os indicadores em `calcular_indicadores_anuais` e `calcular_indicadores_globais`: remover FID, FIT, parecer e causa do vertimento; incluir disponibilidade relativa, desvio para a disponibilidade de referência, razão com a garantia física, parcelas da EVT, horas por condição operativa e janelas diurna/noturna
- [X] T033 [US2] Implementar eventos de horas consecutivas: `identificar_eventos`, `listar_eventos_parada_com_evt`, `listar_eventos_indisponibilidade_total`
- [X] T034 [US2] Implementar `detectar_mudanca_classificacao` (mudança de classificação do vertimento contínuo pelo ONS; dez/2022 na série atual)
- [X] T035 [US2] Implementar as distribuições da EVT: `calcular_evt_mensal`, `calcular_distribuicao_mes_do_ano`, `calcular_evt_por_faixa_geracao`, `calcular_perfil_horario`
- [X] T036 [US2] Implementar `listar_anomalias`, `tabela_parametros` e o uso de `validar_regras_fisicas` (`src/validator.py`) nos resultados
- [X] T037 [US2] Substituir o parecer por constatações geradas dos dados (`_achado_cobertura`, `_achado_disponibilidade`, `_achado_indisponibilidade`, `_achado_geracao`, `_achado_evt`, `_achado_evt_nivel_geracao`, `_achado_paradas`, `_achado_perfil_diurno`, `_achado_sazonalidade`, `_achado_mudanca_classificacao`, `_achado_qualidade`, reunidas em `montar_achados`) e criar `notas_metodologicas`
- [X] T038 [US2] Criar a dataclass `ResultadosAnalise` e a função `analisar`, que calcula todos os resultados usados por planilha, Markdown e PDF

### Figuras
- [X] T039 [US3] Substituir os gráficos seaborn por 5 figuras em matplotlib (`_estilo_graficos`, `_grafico_serie_temporal`, `_grafico_evt_mensal`, `_grafico_perfil_horario`, `_grafico_disponibilidade_anual`, `_grafico_vazoes_defluentes`, `gerar_graficos`), com os nomes em `NOMES_FIGURAS` e 300 DPI por padrão; remover o import do seaborn

### Relatórios e CLI
- [X] T040 [US4] Reescrever `exportar_tabelas`: uma aba por tabela de `ResultadosAnalise` e CSV com os indicadores anuais
- [X] T041 [US4] Reescrever `gerar_relatorio_md` a partir de `ResultadosAnalise`, com a tabela anual formatada por `linhas_tabela_anual` (compartilhada com o PDF)
- [X] T042 [US4] Reescrever `src/pdf_generator.py`: `PDFReportGenerator(resultados, figuras, output_pdf)` montado a partir de `ResultadosAnalise` (antes lia a planilha e tinha textos fixos), A4 paisagem, fontes Arial ou DejaVu Sans, cabeçalho, rodapé e "Página X de Y", capa com quadros-resumo, seções numeradas, aviso no lugar de figura ausente e `main()` para regenerar só o PDF
- [X] T043 [US4] Corrigir a CLI em `src/analyzer.py`: `--generate-plots` e `--generate-report` com `argparse.BooleanOptionalAction` (`--no-generate-*`), reaproveitamento das figuras existentes e falha do PDF propagada para o código de saída 1 em `executar_pipeline_analise`

### Testes e documentação
- [X] T044 [P] Criar a série sintética `gerar_df_sintetico` / `df_sintetico` em `tests/conftest.py` (indisponibilidade de 30 h, parada de 5 h com EVT, mudança de classificação em jan/2024, registro anômalo)
- [X] T045 [P] Reescrever `tests/test_analyzer.py`: `test_identificar_eventos_quebra_em_lacunas`, `test_cobertura_e_eventos`, `test_mudanca_de_classificacao`, `test_indicadores_anuais`, `test_evt_por_faixa_soma_o_total`, `test_extremos_excluem_registros_sinalizados`, `test_texto_do_relatorio_usa_os_valores_calculados` (sem "96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained"), `test_gerar_graficos`, `test_integracao_base_real`
- [X] T046 [P] Reescrever `tests/test_pdf_generator.py`: `test_pdf_gerado_a_partir_dos_resultados`, `test_pdf_sem_figuras_nao_falha`
- [X] T047 [P] Reescrever o `README.md` (visão geral, estrutura, execução, metodologia e seção Histórico com as correções de 30/09/2026)

### Ajustes de 02/10/2026
- [X] T048 Atualizar a garantia física para 36,4 MWmed em `src/config.py` (`GARANTIA_FISICA_MWMED`, `FONTE_GARANTIA_FISICA`) e registrar em `notas_metodologicas` que o IP e o TEIF de referência são do cálculo de 2017, quando a garantia física era de 36,9 MWmed
- [X] T049 Incluir a contagem mensal de horas com geração zero: `calcular_horas_geracao_zero`, `linhas_tabela_geracao_zero`, `_achado_geracao_zero` (as constatações passam a ser 12), aba `HORAS_GERACAO_ZERO_MES`, seção no Markdown e `_secao_geracao_zero` no PDF
- [X] T050 [P] Testar as horas com geração zero: `test_horas_geracao_zero_por_mes` e as verificações de 12 constatações e do total de horas em `test_integracao_base_real` (`tests/test_analyzer.py`)
- [X] T051 Preservar a versão aprovada em `_backup_2026-10-02_relatorio_aprovado/` (`src/`, `tests/`, `reports/`, `README.md`, `requirements.txt` e `LEIA-ME.txt`)
- [X] T052 Numerar automaticamente as seções do Markdown (função `secao()` em `gerar_relatorio_md`) e criar os pontos de extensão para seções opcionais (`analisar(..., indicadores=None)`, campo `ons` de `ResultadosAnalise`); o conteúdo dessas seções é especificado em `specs/004-conferencia-outros`
- [X] T053 Registrar os ajustes de 02/10/2026 na seção Histórico do `README.md`
- [X] T054 Regenerar relatórios, planilha, CSV e figuras em `reports/` (arquivos de 02/10/2026 13:01)

**Checkpoint**: Relatório sem números fixos, com 12 constatações quando não há os dados opcionais da spec 004.

---

## Phase 8: Regularização da documentação (05/10/2026)

**Purpose**: Revisão retroativa da spec 003 e registro das pendências encontradas.

- [X] T055 Copiar os arquivos da spec antes da edição para `*.2026-10-05.bak` (spec, plan, research, data-model, quickstart, contracts/cli-contract, tasks, checklists/requirements)
- [X] T056 Revisar `spec.md`: Status "Implementado (revisado em 2026-10-05)", histórias, requisitos FR-001 a FR-019, critérios SC-001 a SC-008 e Histórico de revisões
- [X] T057 [P] Revisar `plan.md` (dependências reais, estrutura de arquivos real, Constitution Check reavaliado e Complexity Tracking)
- [X] T058 [P] Revisar `research.md` (decisões atuais e decisões revogadas) e `data-model.md` (estruturas de `ResultadosAnalise`, abas, figuras e campos removidos)
- [X] T059 [P] Revisar `quickstart.md` e `contracts/cli-contract.md` (comandos, opções `--no-generate-*`, PDF e conferência do relatório)
- [X] T060 Revisar este `tasks.md` e revalidar `checklists/requirements.md`

### Pendências (fora do escopo desta revisão; dependem de decisão do usuário)
- [X] T061 [P] Remover `seaborn>=0.13.0` do `requirements.txt`, já que nenhum módulo o importa (superada em 05/10/2026: a constituição 1.1.0 exige seaborn e as figuras foram migradas (spec 005, US2))
- [X] T062 Executar `pytest tests/ -v` e registrar o resultado (o cache do pytest no projeto é de 30/09/2026 12:24, anterior à reescrita; os `LEIA-ME.txt` das cópias de segurança citam 47 testes em 02/10/2026 e 60 em 05/10/2026, sem registro de aprovação) (resolvida em 05/10/2026: 87 testes aprovados)
- [X] T063 Medir o tempo de execução de `python -m src.analyzer` e confirmar ou revisar SC-004 (resolvida em 05/10/2026: 10,2 s)
- [X] T064 Decidir se o analisador deve criar `.bak` dos relatórios antes de regravá-los (diretriz de persistência segura da constituição) ou se as cópias datadas manuais bastam (decidido pelo usuário em 05/10/2026: não haverá `.bak` de relatórios; exceção registrada na constituição 1.1.1, Requisito Técnico 3)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Sem dependências — execução imediata.
- **Foundational (Phase 2)**: Depende de Phase 1 — BLOQUEIA todas as histórias de usuário.
- **User Stories (Phases 3, 4, 5)**:
  - US1 (Phase 3) inicia após Foundational.
  - US2 (Phase 4) depende dos dados agregados em US1.
  - US3 (Phase 5) pode ser implementado em paralelo com US2, consumindo a base tratada.
- **Polish (Phase 6)**: Depende de todas as histórias de usuário concluídas.
- **Revisão pós-auditoria (Phase 7)**: Depende da Feature 002 revisada (sinalizações R6 a R9 em `src/validator.py`). Dentro da fase: parâmetros e formatação (T026 a T028) antes da análise (T029 a T038); `ResultadosAnalise` (T038) antes das figuras (T039) e dos relatórios (T040 a T043); US4 (relatórios) depende de US1 a US3.
- **Regularização da documentação (Phase 8)**: Depende da Phase 7. As pendências T061 a T064 são independentes entre si.

### Parallel Opportunities
- **Setup**: `T002` (pip install) e `T003` (config.py) podem rodar em paralelo após `T001`.
- **User Story 1**: Exportadores de tabela `T009` (.xlsx e .csv) e testes `T006`.
- **User Story 2**: Testes `T010` e relatórios Markdown `T013`.
- **User Story 3**: Cada uma das 5 funções de plotagem `T015`, `T016`, `T017`, `T018`, `T019` é independente e pode ser desenvolvida/testada em paralelo.
- **Polish**: `T021` (documentação) e `T023` (testes automatizados) em paralelo.
- **Revisão pós-auditoria**: `T027` e `T028`; os testes `T044` a `T046` e o README `T047`, depois da análise.
- **Documentação**: `T057` a `T059`.

---

## Parallel Example: User Story 3

Exemplo original (as tarefas citadas foram substituídas em 30/09/2026; ver T039):

```powershell
# Funções de plotagem operando sobre o mesmo dataset tratado de forma isolada:
Task: "Implementar função de plotagem do Heatmap Sazonal Mês x Hora em src/analyzer.py"
Task: "Implementar função de plotagem do Scatterplot de Vazão vs Energia Turbinável em src/analyzer.py"
Task: "Implementar função de plotagem dos Boxplots Comparativos Anuais em src/analyzer.py"
Task: "Implementar função de plotagem do Balanço Hídrico em Barras em src/analyzer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Concluir Setup (Phase 1) e Foundational (Phase 2).
2. Concluir User Story 1 (Phase 3).
3. **VALIDAR MVP**: Inspecionar `reports/perfil_estatistico_anual.xlsx` e verificar se todas as 10 variáveis possuem médias, desvios e extremos com datas exatas.
4. Prosseguir para User Story 2 (Diagnóstico Regulatório) e User Story 3 (Gráficos Seaborn).

### Situação atual (2026-10-05)
1. US1 a US4 implementadas pela Phase 7; o relatório é validado pelos testes de `tests/test_analyzer.py` e `tests/test_pdf_generator.py` e pelo Cenário 5 de `quickstart.md`.
2. Antes de alterar o código ou regenerar um relatório aprovado, guardar uma cópia datada de `src/`, `tests/` e `reports/`.
3. Seções opcionais do relatório (spec 004) entram pelos pontos de extensão de T052, sem alterar as 12 constatações desta feature.
