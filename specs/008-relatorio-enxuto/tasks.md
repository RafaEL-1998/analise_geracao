# Tasks: Relatório Mais Enxuto, com Sumário na Capa e Constatações em Cada Seção - UHE São Domingos

**Input**: Design documents from `/specs/008-relatorio-enxuto/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/estrutura-relatorio-contract.md, quickstart.md

**Tests**: incluídos. A constituição exige testes e não regressão, e o plano define testes da estrutura (cada constatação uma vez; PDF e Markdown com as mesmas seções; sumário com as páginas certas). Sempre sem rede, com `ResultadosAnalise` sintéticos e `tmp_path`.

**Organization**: a estrutura única do relatório e o conteúdo compartilhado pelo PDF e pelo Markdown são pré-requisitos (Phase 2). As histórias mexem nos mesmos arquivos (`src/analyzer.py`, `src/pdf_generator.py`) e rodam em sequência.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: paralelizável (arquivos diferentes, sem dependência de tarefa pendente)
- **[Story]**: história da spec (US1 a US3)

---

## Phase 1: Setup

- [X] T001 Criar a cópia datada `_backup_2026-10-06_antes_spec008/` com `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `README.md` e `requirements.txt`, mais `conftest.py` (`collect_ignore_glob = ["*"]`) e `LEIA-ME.txt` (Requisito Técnico 3(b)). Não sobrescrever os `src/*.bak` antigos.
- [X] T002 Registrar a linha de base em "Registro de execução" ao final de `specs/008-relatorio-enxuto/tasks.md`: `python -m pytest tests -q` com a rede bloqueada (esperado: 231 aprovados); páginas do PDF (31); abas da planilha (57); SHA-256 das 8 figuras. A referência da não regressão é a cópia de T001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: estrutura única do relatório e conteúdo compartilhado pelos dois geradores.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T003 [P] Escrever `tests/test_estrutura_relatorio.py`:
  - `SECOES` com as 17 chaves e os títulos da seção 1 do data-model, na ordem;
  - `secoes_presentes(res)` numera 1, 2, 3, … sem lacunas, só com as seções presentes (com só a base de EVT: 11 seções; com todas: 17);
  - todo título de constatação gerado num `analisar` com todas as bases sintéticas está no mapa da seção 2 do data-model;
  - título fora do mapa vai para `cobertura`, com aviso no log;
  - `constatacoes_da_secao(res, chave)` segue a ordem de `res.achados`.
- [X] T004 Implementar `src/estrutura_relatorio.py` (depende de T003), com docstrings e tipos:
  - `Secao(chave, titulo, presente)`, `SECOES` (data-model, seção 1);
  - `MAPA_CONSTATACOES` título → chave (data-model, seção 2);
  - funções `secoes_presentes(res) -> List[Tuple[int, Secao]]`, `constatacoes_da_secao(res, chave) -> List[Tuple[str, str]]` e `sumario(res) -> List[Tuple[int, str]]`;
  - regra da constatação órfã: "vai para `cobertura`, com aviso no log; nenhuma constatação desaparece".
- [X] T005 Em `src/analyzer.py`, criar o conteúdo compartilhado (data-model, seção 4) a partir do que hoje está escrito em `src/pdf_generator.py`, e fazer o PDF usá-lo sem mudar a sua saída:
  - `indicadores_capa(res)` (rótulo, valor, complemento, mais a nota da capa);
  - `legenda_figura(res, chave)` para as 8 figuras;
  - `pares_cobertura(res)`, `pares_identificacao(res)` e `pares_parametros()`;
  - `linhas_tabela_perfil_diurno(res)`, `linhas_tabela_regras(res)`, `linhas_tabela_parametros(res)`, `linhas_tabela_registros_sinalizados(res)`;
  - `linhas_tabela_eventos_indisponibilidade(res)`, `linhas_tabela_evt_por_nivel(res)` e `linhas_tabela_eventos_parada(res)`, na versão do PDF (research R6).
- [X] T006 [P] Acrescentar o logger `estrutura_relatorio` a `LOGGERS_PIPELINE` em `src/logger.py`.

**Checkpoint**: estrutura testada; suíte aprovada; PDF igual ao anterior (mesmas páginas).

---

## Phase 3: User Story 1 - Capa com dados básicos, percentuais e sumário (Priority: P1) 🎯 MVP

**Goal**: capa com identificação, parâmetros, indicadores, data de geração e sumário, sem texto de constatação (FR-001 a FR-004).

**Independent Test**: gerar o relatório e conferir a capa e o sumário (com as páginas no PDF).

### Tests for User Story 1

- [X] T007 [P] [US1] Testes da capa e do sumário:
  - em `tests/test_pdf_generator.py`: o gerador expõe `sumario_entradas` (número, título, página) e `paginas_secoes` (título → página real); as entradas cobrem todas as seções presentes, na ordem, e as páginas conferem; o subtítulo da capa tem "Gerado em";
  - em `tests/test_estrutura_relatorio.py`: o Markdown começa com o título, "**Gerado em**", a tabela "Indicadores principais" e "## Sumário" (lista numerada com links), e nenhum texto de constatação aparece antes da primeira seção.

### Implementation for User Story 1

- [X] T008 [US1] Em `src/pdf_generator.py`:
  - `SimpleDocTemplate` derivado que, no `afterFlowable`, avisa o `TableOfContents` e registra a página de cada título de seção (estilo "secao");
  - capa: subtítulo com "Gerado em dd/mm/aaaa hh:mm"; depois dos indicadores e da nota da capa, o subtítulo "Sumário" e o índice em estilo compacto (8,5 pt, entrelinha de 11 pt);
  - sai a seção "Principais constatações" (`_constatacoes`);
  - montagem com `multiBuild`.
- [X] T009 [US1] Em `src/analyzer.py` (`gerar_relatorio_md`), capa do Markdown conforme o contrato:
  - título; "**Período**"; "**Gerado em**";
  - blocos de identificação e de parâmetros em tabelas de duas colunas, com as legendas `bloco_identificacao` e `bloco_parametros`;
  - "Indicadores principais" (`indicadores_capa`), com a nota e a legenda `tab_capa_indicadores`;
  - "## Sumário" com os itens de `sumario(res)` como links para os títulos das seções;
  - sem a linha "**Fontes**:" e sem a lista de constatações.

**Checkpoint**: capa e sumário corretos no PDF e no Markdown.

---

## Phase 4: User Story 2 - Cada constatação uma única vez, no início da sua seção (Priority: P1)

**Goal**: constatações no início das seções, sem repetição; PDF e Markdown com a mesma estrutura (FR-005 a FR-008, FR-014).

**Independent Test**: cada constatação aparece uma vez em cada saída, na seção do mapa; as duas saídas têm as mesmas seções, na mesma ordem.

### Tests for User Story 2

- [X] T010 [P] [US2] Em `tests/test_estrutura_relatorio.py`, com e sem as bases novas sintéticas:
  - cada texto de constatação aparece exatamente uma vez no Markdown, dentro da seção do mapa e antes da primeira tabela ou figura dela;
  - no PDF, o gerador registra as constatações emitidas (`constatacoes_emitidas`), cada uma uma vez, na seção do mapa;
  - os títulos de seção do Markdown (`## n. título`) e os do PDF (`paginas_secoes`) são iguais e na mesma ordem;
  - o Markdown não tem a seção "Figuras" e tem `![…](figures/…)` para cada figura gerada;
  - o Markdown tem as tabelas "Regras de validação" e "Parâmetros utilizados", e o PDF emite as legendas `tab_registros_sinalizados` e `tab_hidrologia_perfil`.

### Implementation for User Story 2

- [X] T011 [US2] Em `src/pdf_generator.py`:
  - `build_pdf` percorre `secoes_presentes(res)` e chama o método da seção pela chave;
  - cada seção começa com `_constatacoes_secao(chave)` (parágrafos "achado" no formato "**Título.** texto");
  - saem as repetições dos textos de constatação dentro das seções (programação, disponibilidade sincronizada, hidrologia, os dois textos do ONS, mudança de classificação, geração zero e qualidade);
  - entram as tabelas de registros sinalizados (seção "Qualidade dos dados") e de vazões e nível por hora do dia (seção da hidrologia), com as legendas da spec 007;
  - o conteúdo compartilhado de T005 é usado em todas as seções.
- [X] T012 [US2] Em `src/analyzer.py`, reescrever `gerar_relatorio_md` pela estrutura:
  - para cada seção presente, `## n. título`, as constatações da seção e o conteúdo, numa função por chave, com as mesmas tabelas, subtítulos, notas, figuras e legendas do PDF;
  - figura: `![<título da seção>](figures/<arquivo>.png)`, a legenda descritiva (`legenda_figura`) e a legenda de fonte;
  - saem a seção "Constatações" e a seção "Figuras";
  - as legendas de fonte da spec 007 continuam em toda tabela e figura (o teste de cobertura da spec 007 segue valendo).
- [X] T013 [US2] Conferir na base real que nenhuma constatação fica órfã (sem aviso no log) e que o mapa da seção 2 do data-model corresponde ao conteúdo das seções; registrar em "Registro de execução".

**Checkpoint**: constatações uma vez só, PDF e Markdown com a mesma estrutura.

---

## Phase 5: User Story 3 - Sem rodapé de fontes repetido (Priority: P2)

**Goal**: rodapé só com a numeração; notas das bases novas sem a parte de fonte (FR-009 a FR-011, FR-013).

**Independent Test**: rodapé só com "Página X de Y"; legendas de fonte em 100% das figuras e tabelas; notas sem "Fonte: conjunto".

### Tests for User Story 3

- [X] T014 [P] [US3] Testes:
  - em `tests/test_pdf_generator.py`, `_canvas_numerado` recebe só o cabeçalho e a fonte (sem rodapé de texto), e o teste de cobertura das legendas da spec 007 continua aprovado;
  - em `tests/test_relatorio_complementar.py`, as notas da disponibilidade e da hidrologia e a nota do cadastro não começam com "Fonte: conjunto" e mantêm as ressalvas ("não são consistidos pelo ONS", "Cadastro sem série histórica"), e a seção da geração oficial não tem "- Fonte: conjunto Geração por usina";
  - ajustar os testes da spec 007 que esperavam o rodapé e a linha "**Fontes**:".

### Implementation for User Story 3

- [X] T015 [US3] Em `src/pdf_generator.py`, o rodapé passa a ter só "Página X de Y" (sai o texto de `rodape_fontes`).
- [X] T016 [US3] Notas sem a parte de fonte (data-model, seção 5): `notas_disponibilidade` e `notas_hidrologia` em `src/analyzer.py`, a nota da geração oficial no Markdown e `nota_identificacao_cadastro` em `src/pdf_generator.py`; o mesmo texto do cadastro no Markdown.
- [X] T017 [US3] Em `src/fontes_relatorio.py`, retirar `rodape_fontes` e `cabecalho_fontes`, que deixam de ser usados, e os testes correspondentes em `tests/test_fontes_relatorio.py`.

**Checkpoint**: rodapé e notas enxutos; legendas intactas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T018 [P] Atualizar `README.md`: estrutura do relatório (capa com sumário, constatações nas seções, rodapé) e histórico de 06/10/2026 (spec 008).
- [X] T019 [P] Registrar no "Histórico de revisões" de `specs/007-fontes-por-figura-tabela/spec.md` (FR-009 e FR-010 revistas pela spec 008) e de `specs/003-analise-dados/spec.md` (nova estrutura do relatório).
- [X] T020 Executar `python -m pytest tests -q` com a rede bloqueada. Esperado: suíte aprovada, sem alterar arquivos do projeto.
- [X] T021 Executar o `specs/008-relatorio-enxuto/quickstart.md` completo:
  - `python -m src.analyzer` sem aviso;
  - não regressão contra `_backup_2026-10-06_antes_spec008/reports/`, conteúdo a conteúdo (research R8):
    - toda tabela do relatório anterior presente no novo, com as mesmas linhas (versão do PDF nas tabelas da research R6);
    - cada constatação com o mesmo texto, uma vez;
    - notas iguais, exceto a parte de fonte da FR-013;
    - planilha com 57 abas idênticas;
    - figuras com o mesmo SHA-256;
  - PDF com menos de 31 páginas e sumário com as páginas certas;
  - registrar em "Registro de execução" e mudar o status de `specs/008-relatorio-enxuto/spec.md` para "Implementado".

---

## Phase 7: Revisão de 07/10/2026 — ficha do cadastro na capa (FR-015)

**Goal**: pedido do usuário em 07/10/2026: retirar a seção "Identificação da usina no cadastro do ONS" e levar a ficha para a capa, sem a data da consulta.

**Independent Test**: capa com o bloco "Cadastro no ONS" (sem "Data da consulta") e numa página só; nenhuma seção do cadastro; constatação do cadastro, quando houver, na seção "Fonte e cobertura dos dados".

- [X] T022 Cópia datada `_backup_2026-10-07_antes_revisao008/` da versão aprovada, com `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `README.md`, `requirements.txt`, `conftest.py` e `LEIA-ME.txt` (Requisito Técnico 3(b)).
- [X] T023 Revisar `specs/008-relatorio-enxuto/spec.md` (FR-001, FR-012, FR-013, FR-015, SC-005, US1, tabela do Contexto, histórico de revisões), `data-model.md` (seções 1, 2, 4 e 5), o contrato (capa) e `research.md` (R10).
- [X] T024 [P] Testes, que devem falhar antes de T025 a T027:
  - `tests/test_estrutura_relatorio.py`: 16 chaves, sem `cadastro`; com as bases sintéticas, 14 seções; "Cadastro da usina no ONS" → `cobertura`; capa do Markdown e do PDF com o bloco "Cadastro no ONS" quando houver cadastro, sem "Data da consulta"; nenhuma seção "Identificação da usina no cadastro do ONS";
  - `tests/test_relatorio_complementar.py`: `pares_identificacao_cadastro` sem a data da consulta; ressalva "cadastro sem série histórica" nas Notas metodológicas.
- [X] T025 Em `src/estrutura_relatorio.py`, retirar a seção `cadastro` e mapear "Cadastro da usina no ONS" para `cobertura`.
- [X] T026 Em `src/analyzer.py`:
  - `pares_identificacao_cadastro` sem a data da consulta;
  - sai `nota_identificacao_cadastro`;
  - capa do Markdown com o bloco "Cadastro no ONS" e a legenda `bloco_cadastro`;
  - sai o conteúdo da seção do cadastro.
- [X] T027 Em `src/pdf_generator.py`, capa com três blocos lado a lado (identificação, cadastro, parâmetros) quando houver cadastro, e sai `_secao_cadastro`. A capa continua numa página.
- [X] T028 [P] Atualizar `README.md` e o histórico de `specs/003-analise-dados/spec.md`.
- [X] T029 Executar `python -m pytest tests -q` com a rede bloqueada. Esperado: suíte aprovada, sem alterar arquivos vigiados.
- [X] T030 Validar na base real:
  - `python -m src.analyzer` sem aviso; capa numa página; 16 seções;
  - não regressão contra `_backup_2026-10-07_antes_revisao008/reports/`: mudam só a capa, a seção retirada, a numeração das seções, a data da consulta e a nota da ficha;
  - planilha e figuras idênticas;
  - registro de execução e status da spec.

---

## Phase 8: Revisão 2 de 07/10/2026 — figuras maiores e padronizadas (FR-016)

**Goal**: pedido do usuário: aumentar e padronizar os gráficos das seções de série temporal, EVT mensal, disponibilidade sincronizada e vazões defluentes.

**Independent Test**: no PDF, as quatro figuras têm a mesma largura e altura, na largura útil da página; os PNG têm o mesmo tamanho.

- [X] T031 Cópia datada `_backup_2026-10-07_antes_figuras/` (Requisito Técnico 3(b)).
- [X] T032 Revisar `spec.md` (FR-016, histórico), `research.md` (R11) e este arquivo.
- [X] T033 [P] Teste em `tests/test_estrutura_relatorio.py`, que deve falhar antes de T034 e T035: as quatro figuras com o mesmo tamanho de PNG e, no PDF, com a mesma largura e altura, na largura útil; as demais continuam com a altura máxima da R9.
- [X] T034 Em `src/analyzer.py`, figuras 01, 02, 05 e 06 com 11 × 4,3 polegadas, sem outra mudança no gráfico (seaborn, cores e textos iguais).
- [X] T035 Em `src/pdf_generator.py`, essas quatro figuras na largura útil, fora do limite de altura.
- [X] T036 Executar `python -m pytest tests -q` com a rede bloqueada.
- [X] T037 Validar na base real:
  - `python -m src.analyzer` sem aviso; capa numa página;
  - Markdown e planilha idênticos aos da cópia de T031, fora a data de geração;
  - figuras 03, 04, 07 e 08 com o mesmo SHA-256;
  - imagens das quatro figuras conferidas a olho (legendas e rótulos sem sobreposição);
  - registro de execução.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **US1** → **US2** → **US3** → **Polish**.
- As histórias dependem só da Phase 2, mas alteram os mesmos arquivos e rodam em sequência. Dentro de cada história: testes antes (devem falhar), depois a implementação.
- T013 depois de T011 e T012. T021 é a última tarefa.

### Parallel Opportunities

- T003 e T006.
- Os testes de cada história (T007, T010, T014), se escritos antes das implementações.
- T018 e T019.

---

## Parallel Example: Phase 2

```text
T003 Testes da estrutura em tests/test_estrutura_relatorio.py
T006 Logger estrutura_relatorio em src/logger.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 e Phase 2.
2. US1: capa com dados básicos, percentuais, data e sumário.
3. Validar a capa no PDF.

### Incremental Delivery

1. US1 → US2 (constatações nas seções e Markdown com a estrutura do PDF) → US3 (rodapé e notas).
2. Polish com o relatório regenerado até 13/10/2026.

---

## Notes

- Nenhum dado é baixado nem reprocessado; a planilha não muda.
- Nenhum gráfico novo ou alterado.
- Decisões do usuário em 06/10/2026: notas de fonte saem e as ressalvas ficam (1A); o Markdown segue a estrutura do PDF (2A).

---

## Registro de execução

### 06/10/2026 — implementação completa

- **T001**: cópia `_backup_2026-10-06_antes_spec008/` com `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `README.md`, `requirements.txt`, `conftest.py` e `LEIA-ME.txt`; os `src/*.bak` antigos não foram tocados.
- **T002**: linha de base com 231 testes aprovados (T020 da spec 007, mesmo código da cópia); PDF com 31 páginas; 57 abas; SHA-256 das 8 figuras (16 primeiros caracteres): 01 `efadabefac05aab7`, 02 `af449c20afada1b2`, 03 `c7e627bf8a15c470`, 04 `0956b20eb0d6dbf4`, 05 `14ce585b7a05d845`, 06 `a90d5cd6d78ad5c1`, 07 `f5e336924fd8135a`, 08 `a000b0bfb69fb6f6`.
- **Phase 2**:
  - `src/estrutura_relatorio.py` com as 17 seções e o mapa dos 19 títulos de constatação. A numeração não tem lacunas, e a constatação órfã vai para a seção 1, com aviso no log; logger `estrutura_relatorio`.
  - **T003**: com só a base de EVT são 11 seções, não 12 como dizia a tarefa (corrigido acima). Com as bases sintéticas do teste são 15; na base real, 17.
  - **T005**: o conteúdo compartilhado ficou em `src/analyzer.py`, porque o `analyzer` não pode importar o `pdf_generator`. Foi aplicado no PDF junto com a T011, na reescrita do gerador.
- **US1**:
  - PDF: capa com "Gerado em", indicadores, nota e sumário. O sumário usa `TableOfContents` com `multiBuild`, e as páginas são registradas no `afterFlowable`.
  - Markdown: capa com período, data, identificação, parâmetros, indicadores e sumário com links.
- **US2**:
  - PDF e Markdown percorrem `secoes_presentes`, e cada seção começa com as suas constatações.
  - Saíram a lista inicial de constatações, a seção "Figuras" do Markdown e as repetições dentro das seções.
  - Entraram no PDF as tabelas de registros sinalizados e de vazões e nível por hora do dia. O Markdown recebeu as tabelas que só o PDF tinha (R6).
  - Foram retiradas as antigas `secao_*_md` e o mapa função → chave da spec 007.
- **US3**:
  - rodapé só com "Página X de Y";
  - `rodape_fontes` e `cabecalho_fontes` retirados (T017);
  - notas das bases novas sem a parte de fonte, com as ressalvas.
- **Paginação (research R9)**:
  - Problema: na base real, o PDF ficou com 33 páginas e o sumário de 17 seções não cabia na capa.
  - Ajustes de leiaute:
    - sumário em duas colunas, com quebra de página depois da capa;
    - figuras com até 285 pt de altura no PDF (o PNG não muda);
    - tabelas com mais de 12 linhas podem continuar na página seguinte, com o cabeçalho repetido;
    - título e constatações sempre juntos e, se curtos, junto do primeiro bloco.
  - Teste novo: `test_pdf_capa_numa_pagina_e_paginacao_enxuta`.
- **T014**: testes antigos ajustados à nova numeração das seções (`tests/test_indicadores_ons.py`) e ao título das notas, que agora também aparece no sumário (`tests/test_relatorio_complementar.py`).
- **T018 e T019**:
  - `README.md` atualizado;
  - histórico de revisões de `specs/007-fontes-por-figura-tabela/spec.md` (FR-009, FR-010 e SC-005, com nota nos requisitos);
  - histórico de revisões de `specs/003-analise-dados/spec.md`.
- **T020**: 242 testes aprovados (12 novos, 1 retirado) em 49 s, com a rede bloqueada; nenhum dos 128 arquivos vigiados mudou.
- **T013 e T021**, na base real (`python -m src.analyzer`, 24 s, sem aviso no log):
  - **Constatações**: nenhuma órfã. As 17 aparecem uma vez cada, no início da sua seção, no PDF e no Markdown:
    - cobertura → 1;
    - disponibilidade → 3;
    - indisponibilidades e geração → 4;
    - as duas do ONS → 5;
    - as três da EVT → 7;
    - concentração diurna → 8;
    - as duas de EVT por nível e parada → 9;
    - programação → 10;
    - disponibilidade sincronizada → 11;
    - afluência → 12;
    - geração zero → 13;
    - qualidade → 16.
  - **Sumário**: 17 seções, com os mesmos números e títulos no PDF e no Markdown. No PDF, cada página confere com a registrada na montagem (seção 1 na p. 2, seção 17 na p. 28).
  - **PDF**: 30 páginas (31 antes), com a capa só na página 1.
  - **PDF e Markdown**: mesmos títulos de seção, parágrafos e linhas de tabela. Os indicadores da capa são cartões no PDF e tabela no Markdown, com o mesmo conteúdo.
  - **Não regressão** contra a cópia de T001:
    - as 17 constatações com o mesmo texto;
    - as 22 tabelas anteriores com as mesmas linhas. As 2 da R6 foram comparadas nas colunas comuns; na tabela de extremos, só saíram as crases dos nomes das variáveis;
    - todo parágrafo e nota anterior está presente, exceto as 4 notas de fonte da FR-013, cujas ressalvas ficaram;
    - 10 linhas passaram à forma do PDF (capa e cadastro em tabelas; notas das tabelas com o texto do PDF), conferidas fato a fato.
  - **Legendas**: 30 tabelas e 8 figuras no Markdown, todas com legenda de fonte; PDF com 38 legendas para 38 tabelas, blocos e figuras.
  - **Planilha e figuras**: 57 abas idênticas célula a célula; as 8 figuras com o mesmo SHA-256.
  - **Tamanho do Markdown**: de 517 para 737 linhas, por receber as tabelas que só o PDF tinha e as figuras no corpo (decisão 2A).
  - **SC-007**: entregue em 06/10/2026, antes de 13/10/2026.

### 07/10/2026 — revisão: ficha do cadastro na capa (FR-015)

- **T022**: cópia `_backup_2026-10-07_antes_revisao008/` da versão aprovada (240 arquivos; ignorada pelo git).
- **T023**: spec (FR-001, FR-012, FR-013, FR-015 nova, SC-005, US1, tabela do Contexto, histórico de revisões), data-model, contrato e research R10.
- **T024**: testes novos ou revistos falharam antes da implementação (7 falhas): estrutura com 16 chaves, ficha na capa sem a data da consulta, constatação do cadastro na seção de cobertura, ressalva do cadastro só nas notas.
- **T025 a T027**:
  - sai a seção do cadastro; a constatação do cadastro (só com divergência) vai para "Fonte e cobertura dos dados";
  - `pares_identificacao_cadastro` sem a data da consulta, com o rótulo "Homônimos excluídos pelo CEG" (antes, "Homônimos no cadastro (excluídos pelo CEG)"), para caber numa linha da capa;
  - sai `nota_identificacao_cadastro`;
  - capa do PDF com três blocos de largura própria (26%, 38% e 36%; colunas de chaves de 62, 112 e 88 pt), escolhidas por medição na base real, e capa do Markdown com a tabela "Cadastro no ONS".
- **Capa numa página**: com o bloco do cadastro, a capa passou da página (o sumário ia para a página 2). Ajustes de leiaute, sem mudar texto:
  - células vazias do sumário com fonte pequena: elas ditavam 12,8 pt por linha, em vez de 10,3;
  - sumário em 8 pt;
  - nota e legendas da capa em 7,5 pt (estilo `legenda_capa`);
  - menos espaço depois do subtítulo, nos cartões dos indicadores e no topo dos blocos.
  - Resultado: a capa termina a 32 pt da margem inferior.
- **T028**: `README.md` e históricos das specs 003 e 006. Na spec 006 (US6, cenário 4), a linha "Data da consulta" saiu do relatório; a data de obtenção continua na legenda do bloco e nas notas, e a data e hora continuam na aba `CAD_FICHA`.
- **T029**: 243 testes aprovados (1 novo) em 58 s, com a rede bloqueada; nenhum dos 128 arquivos vigiados mudou.
- **T030**, na base real (`python -m src.analyzer`, 23 s, sem aviso):
  - 16 seções, numeradas sem lacunas; o corpo de todas elas é idêntico ao da versão aprovada;
  - a ficha na capa é a mesma de antes, sem a data da consulta (7 itens), e a legenda de fonte e conferência do bloco é igual;
  - o resto da capa é idêntico;
  - 17 constatações, uma vez cada, com o mesmo texto;
  - PDF com 29 páginas (30 antes) e capa numa página, conferida na imagem da página 1; seção 1 na p. 2 e seção 16 na p. 27;
  - 38 legendas para 38 tabelas, blocos e figuras;
  - planilha com as 57 abas idênticas célula a célula; as 8 figuras com o mesmo SHA-256;
  - Markdown de 737 para 730 linhas.

### 07/10/2026 — revisão 2: figuras maiores e padronizadas (FR-016)

- **T031**: cópia `_backup_2026-10-07_antes_figuras/` (240 arquivos; ignorada pelo git).
- **T032**: FR-016 e histórico na spec, R11 no research, Phase 8 neste arquivo.
- **T033**: teste novo (`test_figuras_padronizadas_na_largura_util`) falhou antes da implementação; o teste de paginação passou a conferir o limite de altura numa figura não padronizada (perfil horário).
- **T034 e T035**:
  - figuras 01, 02, 05 e 06 com `TAMANHO_FIGURA_PADRONIZADA` = 11 × 4,3 polegadas (antes, 11 × 5,0 nas 01 e 02 e 11 × 4,6 nas 05 e 06); nada mais mudou nos gráficos;
  - no PDF, as quatro na largura útil (`FIGURAS_PADRONIZADAS`), cerca de 760 × 297 pt (antes, 627 a 682 pt de largura).
- **T036**: 244 testes aprovados com a rede bloqueada; nenhum dos 128 arquivos vigiados mudou.
- **T037**, na base real (`python -m src.analyzer`, sem aviso):
  - capa numa página; PDF com 29 páginas, como antes; a seção de EVT mensal (título, três constatações, figura e legendas) cabe numa página, com 21 pt de folga;
  - Markdown idêntico ao da cópia de T031, fora a data de geração; planilha com as 57 abas idênticas;
  - figuras 03, 04, 07 e 08 com o mesmo SHA-256; as 01, 02, 05 e 06 com 3300 × 1290 px;
  - páginas 8, 9, 16 e 24 conferidas na imagem: legendas, rótulos e anotações sem sobreposição.
