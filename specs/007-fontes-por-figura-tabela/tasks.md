# Tasks: Fonte Explícita em Cada Figura e Tabela do Relatório - UHE São Domingos

**Input**: Design documents from `/specs/007-fontes-por-figura-tabela/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/relatorio-fontes-contract.md, quickstart.md

**Tests**: incluídos. A constituição exige testes e não regressão, e o plano (research R9) define os testes de cobertura das legendas. Sempre sem rede, com `ResultadosAnalise` sintéticos e `tmp_path`.

**Organization**: o mapa de fontes (módulo novo) é pré-requisito comum (Phase 2). As histórias US1, US2 e US3 só dependem dele, mas mexem nos mesmos arquivos (`src/analyzer.py`, `src/pdf_generator.py`), por isso rodam em sequência.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: paralelizável (arquivos diferentes, sem dependência de tarefa pendente)
- **[Story]**: história da spec (US1 a US3)

---

## Phase 1: Setup

**Purpose**: proteção do estado atual e referência de não regressão.

- [X] T001 Criar a cópia datada `_backup_2026-10-06_antes_spec007/` com `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `README.md` e `requirements.txt`, mais `conftest.py` (`collect_ignore_glob = ["*"]`) e `LEIA-ME.txt` com o motivo (Requisito Técnico 3(b) da constituição 1.2.0). Não sobrescrever os `src/*.bak` antigos.
- [X] T002 Registrar a linha de base na seção "Registro de execução" ao final de `specs/007-fontes-por-figura-tabela/tasks.md`:
  - `python -m pytest tests -q` com a rede bloqueada (esperado: 174 aprovados);
  - SHA-256 de `reports/relatorio_analise_estatistica.md`, a quantidade de abas (56) de `reports/perfil_estatistico_anual.xlsx` e o número de páginas do PDF. A referência da não regressão é a cópia de T001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: catálogo dos conjuntos, conferências e mapa de fontes num único lugar (FR-008), e os dados de origem em `ResultadosAnalise`.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T003 [P] Escrever `tests/test_fontes_relatorio.py` (testes do módulo, antes da implementação):
  - catálogo com os 10 ids do data-model, seção 1 (`evt`, `dispf_mensal`, `dispf_anual`, `teif_teip`, `teif_teip_parametro`, `programacao`, `disponibilidade`, `hidrologia`, `geracao`, `cadastro`), mais `projeto`, que não conta em N;
  - toda entrada de `MAPA_FONTES` cita só conjuntos e conferências existentes no catálogo;
  - texto de conjunto: "<nome> (<identificador>), obtido em dd/mm/aaaa", ou "data de obtenção não registrada" sem registro;
  - conferência feita: "<coincidentes> de <comuns> horas coincidentes (<pct>%)", números no formato do relatório ("70.895", "100,0");
  - com divergências: "<n> divergências, listadas na aba <ABA>";
  - TEIFa/TEIP: "<m> de <n> meses reproduzidos (diferença máxima de <x> p.p.)";
  - base ausente: "conferência com <conjunto> não feita nesta execução";
  - prefixos "Fonte dos dados:" e, para cálculo, "Calculado neste relatório a partir de:"; dados sem outra fonte em "Sem outra fonte para conferir: …";
  - rodapé com N = 10 ("10 conjuntos") e N = 1 ("1 conjunto").
- [X] T004 Implementar `src/fontes_relatorio.py` (depende de T003), com docstrings e tipos:
  - `CONJUNTOS` (id → nome, identificador, pasta do manifesto, link `ONS_PORTAL_DATASET_URL + id do catálogo`), conforme a seção 1 do data-model;
  - `CONFERENCIAS` (id → dado, fonte A × fonte B, aba de divergências), conforme a seção 2;
  - `SEM_OUTRA_FONTE` com os dados sem outra fonte pública: EVT; disponibilidade sincronizada; afluência, níveis e volume útil; programação; DISPF publicado;
  - `MAPA_FONTES` (chave → `conjuntos`, `conferencias`, `sem_outra_fonte`, `calculado`), com as chaves da seção 3 do data-model;
  - `MAPA_ABAS`: nome ou prefixo da aba → chave ou entrada, conforme a seção 4;
  - funções:
    - `datas_obtencao(raiz_raw)`: data mais recente de `registrado_em_utc` de cada manifesto, usando `conjuntos_ons.data_obtencao`; para a EVT, o manifesto da raiz `data/raw`;
    - `conjuntos_carregados(res)`;
    - `texto_conferencia(res, id)`;
    - `legenda_fonte(res, chave) -> str`, no formato do contrato `contracts/relatorio-fontes-contract.md`;
    - `rodape_fontes(res, gerado_em) -> str` e `cabecalho_fontes(res) -> str`;
    - `tabela_fontes_abas(res, abas) -> pd.DataFrame`;
  - chave desconhecida: aviso no log e legenda "origem não mapeada" (o teste de cobertura impede que isso chegue ao relatório).
- [X] T005 Em `src/analyzer.py`:
  - `ResultadosAnalise` ganha o campo `fontes: Dict` (padrão vazio), com `obtencao` (id → data UTC) e `carregados` (lista de ids);
  - `analisar(...)` preenche `res.fontes` ao final (datas lidas uma vez dos manifestos) e, quando há indicadores, `res.ons["recalculo"] = recalcular_taxas(indicadores.horas_estado, indicadores.taxas)` (de `src/indicadores_ons.py`), sem ler arquivo bruto;
  - nenhuma saída existente muda.
- [X] T006 [P] Acrescentar o logger `fontes_relatorio` a `LOGGERS_PIPELINE` em `src/logger.py` e à lista esperada em `tests/test_conformidade.py`.

**Checkpoint**: `python -m pytest tests -q` aprovado; mapa e textos testados.

---

## Phase 3: User Story 1 - Fonte e conferência em cada figura e tabela (Priority: P1) 🎯 MVP

**Goal**: toda figura, tabela e bloco do PDF e do Markdown com a linha "Fonte dos dados: …", gerada do mapa e dos resultados (FR-001 a FR-008, FR-013).

**Independent Test**: gerar o relatório com todas as bases e sem as bases novas; toda tabela e figura tem legenda e os conjuntos citados são os que a alimentam.

### Tests for User Story 1

- [X] T007 [P] [US1] Em `tests/test_relatorio_complementar.py`, teste de cobertura do Markdown, com todas as bases sintéticas e sem as bases novas:
  - cada tabela (linha `| --- |`) é seguida, antes da próxima tabela ou do próximo título `##`/`###`, de uma linha que começa com "Fonte dos dados:" ou "Calculado neste relatório a partir de:";
  - cada figura listada na seção "Figuras" é seguida da sua legenda.
- [X] T008 [P] [US1] Em `tests/test_pdf_generator.py`: o gerador conta tabelas, blocos e figuras desenhados e legendas de fonte emitidas, e as duas contagens são iguais, com e sem as bases novas.
- [X] T009 [P] [US1] Em `tests/test_fontes_relatorio.py`, conteúdo das legendas a partir de `ResultadosAnalise` sintéticos:
  - figura `serie_temporal` cita a EVT e as conferências `geracao` e `disponibilidade`, com os números de `res.geracao_oficial["conferencia"]` e `res.disponibilidade["conferencia"]`;
  - figura `evt_mensal` diz "Sem outra fonte para conferir: EVT";
  - sem a geração por usina, a legenda diz "conferência com Geração por usina não feita nesta execução";
  - `tab_ons_divergencias` cita as divergências e a aba `ONS_DIVERGENCIAS`.

### Implementation for User Story 1

- [X] T010 [US1] Em `src/analyzer.py`, Markdown:
  - acrescentar a linha `legenda_fonte(res, chave)` depois de cada tabela (cada chamada de `_tabela_md` nas funções `secao_*_md` e em `gerar_relatorio_md`), depois da nota já existente, com a chave da seção 3 do data-model;
  - na seção "Figuras", depois de cada item, a legenda da figura correspondente;
  - fechar a lista de chaves de tabela a partir dos pontos de emissão e atualizar `MAPA_FONTES` e a seção 3 do data-model se surgir tabela não prevista.
- [X] T011 [US1] Em `src/pdf_generator.py`:
  - método `_legenda_fonte(chave)` (estilo "legenda") acrescentado depois de cada `self._tabela(...)`, de cada `self._bloco_chave_valor(...)` (capa: `bloco_identificacao` e `bloco_parametros`; cadastro: `bloco_cadastro`) e de cada `self._figura(...)`;
  - contadores `self._desenhados` e `self._legendas`, com aviso no log se diferirem ao final de `build_pdf`;
  - a legenda fica fora da imagem; figuras inalteradas (FR-013).
- [X] T012 [US1] Revisão do conteúdo (SC-002): conferir cada entrada de `MAPA_FONTES` contra o código que monta a figura ou tabela (quais colunas e quais bases entram), corrigir divergências e registrar o resultado em "Registro de execução".

**Checkpoint**: legendas em 100% das figuras e tabelas (SC-001), com o conteúdo conferido.

---

## Phase 4: User Story 2 - Rodapé e cabeçalho fiéis às fontes (Priority: P1)

**Goal**: rodapé do PDF e cabeçalho do Markdown com "ONS – Dados Abertos, N conjuntos" (FR-009, FR-010).

**Independent Test**: PDF e Markdown com todas as bases (N = 10) e só com a EVT (N = 1).

### Tests for User Story 2

- [X] T013 [P] [US2] Em `tests/test_relatorio_complementar.py`: o Markdown tem a linha "**Fontes**: ONS – Dados Abertos, 10 conjuntos; fonte de cada figura e tabela na legenda; relação completa nas notas metodológicas." com todas as bases e "1 conjunto" só com a EVT; em `tests/test_pdf_generator.py`, o texto do rodapé usado por `build_pdf` vem de `rodape_fontes` e não contém "conjunto Energia Vertida Turbinável".

### Implementation for User Story 2

- [X] T014 [US2] Em `src/pdf_generator.py` (`build_pdf`), trocar o rodapé atual (EVT e "publicação mais recente") por `rodape_fontes(res, agora)`: "Fontes: ONS – Dados Abertos, <N> conjuntos; fonte de cada figura e tabela na legenda; relação completa nas Notas metodológicas. Gerado em <dd/mm/aaaa hh:mm>." Conferir que cabe numa linha em A4 paisagem.
- [X] T015 [US2] Em `src/analyzer.py` (`gerar_relatorio_md`), acrescentar ao cabeçalho, depois das linhas atuais, `cabecalho_fontes(res)`.

**Checkpoint**: rodapé e cabeçalho corretos com N = 10 e N = 1 (SC-005).

---

## Phase 5: User Story 3 - Origem de cada aba da planilha (Priority: P2)

**Goal**: aba `FONTES` com a origem e as conferências de cada aba (FR-011).

**Independent Test**: a planilha tem `FONTES` como última aba, com uma linha para cada outra aba.

### Tests for User Story 3

- [X] T016 [P] [US3] Em `tests/test_relatorio_complementar.py`:
  - `exportar_tabelas` gera `FONTES` como última aba, com as colunas exatas `aba`, `conjuntos_origem`, `conferencias`, `sem_outra_fonte`, `calculado_no_relatorio` (valores "sim" ou "não");
  - uma linha para cada outra aba, na ordem da planilha, nenhuma com "origem não mapeada";
  - aba não criada (base ausente) não aparece.

### Implementation for User Story 3

- [X] T017 [US3] Em `src/analyzer.py` (`exportar_tabelas`): depois de montar o dicionário `abas`, acrescentar `abas["FONTES"] = tabela_fontes_abas(res, list(abas))`. `MAPA_ABAS` deve cobrir as 56 abas atuais (seção 4 do data-model); a ordem e o conteúdo das demais abas não mudam.

**Checkpoint**: aba `FONTES` completa (SC-001 para a planilha).

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T018 [P] Atualizar `README.md`: legenda de fonte em cada figura e tabela, rodapé, aba `FONTES` e histórico de 06/10/2026 (spec 007).
- [X] T019 [P] Registrar no "Histórico de revisões" de `specs/003-analise-dados/spec.md` a troca do rodapé do PDF e as legendas de fonte (a cópia de T001 cobre o Requisito Técnico 3(b)).
- [X] T020 Executar `python -m pytest tests -q` com a rede bloqueada. Esperado: suíte aprovada, sem alterar arquivos do projeto.
- [X] T021 Executar o `specs/007-fontes-por-figura-tabela/quickstart.md` completo (passos 1 a 5):
  - `python -m src.analyzer`;
  - não regressão contra `_backup_2026-10-06_antes_spec007/reports/`, ignorando as linhas "Fonte dos dados:", "Calculado neste relatório a partir de:" e "**Fontes**:": seções, constatações e as 56 abas idênticas (SC-004);
  - resultados citados iguais aos de `GER_CONFERENCIA`, `DISP_CONFERENCIA`, `HID_ALINHAMENTO` e `ONS_DIVERGENCIAS` (SC-003);
  - rodapé com 10 conjuntos (SC-005);
  - registrar tudo em "Registro de execução" e mudar o status de `specs/007-fontes-por-figura-tabela/spec.md` para "Implementado".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depois do Setup; bloqueia as histórias. T003 antes de T004; T005 depois de T004.
- **US1 (Phase 3)**, **US2 (Phase 4)** e **US3 (Phase 5)**: dependem só da Phase 2. Como alteram os mesmos arquivos, rodam em sequência: US1 → US2 → US3.
- **Polish (Phase 6)**: depois das histórias. T021 é a última tarefa.

### Within Each User Story

- Testes primeiro (devem falhar), depois a implementação.
- Em US1, T012 (revisão do conteúdo) depois de T010 e T011.

### Parallel Opportunities

- T003 e T006 (arquivos diferentes).
- T007, T008 e T009 (testes em arquivos diferentes).
- T013 e T016, se escritos antes das implementações das suas histórias.
- T018 e T019.

---

## Parallel Example: User Story 1

```text
T007 Teste de cobertura do Markdown em tests/test_relatorio_complementar.py
T008 Teste de contagem do PDF em tests/test_pdf_generator.py
T009 Teste de conteúdo das legendas em tests/test_fontes_relatorio.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 e Phase 2.
2. Phase 3 (US1): legendas em todas as figuras e tabelas.
3. Validar: cobertura de 100% e conteúdo conferido.

### Incremental Delivery

1. US1 (legendas) → US2 (rodapé e cabeçalho) → US3 (aba FONTES).
2. Phase 6 com o relatório regenerado até 13/10/2026 (SC-006).

---

## Notes

- Nenhum dado é baixado nem reprocessado; só a apresentação muda.
- Nenhum gráfico novo ou alterado (constituição, Requisito Técnico 5).
- Só conferências refeitas pelo pipeline (decisão A do usuário em 06/10/2026).

---

## Registro de execução

### 06/10/2026 — implementação completa

- **T001**: cópia `_backup_2026-10-06_antes_spec007/` (228 arquivos).
- **T002**: linha de base com 174 testes aprovados; relatório Markdown SHA-256 `dc4a62298810cae9`; 56 abas; PDF com 27 páginas; SHA-256 das 8 figuras guardado para a FR-013.
- **Phase 2**:
  - `src/fontes_relatorio.py` com o catálogo, as conferências, o mapa (39 chaves), as regras das abas e os textos; `res.fontes` preenchido em `analisar`; logger `fontes_relatorio`;
  - o recálculo da TEIFa/TEIP já existia em `res.ons["recalculo_taxas"]` (spec 004) e foi só usado;
  - tolerância de "mês reproduzido": `TOLERANCIA_REPRODUCAO_TAXAS_PP` = 0,001 p.p. (`src/config.py`);
  - `tests/test_conformidade.py` usa o próprio `LOGGERS_PIPELINE`, sem lista à parte para ajustar.
- **US1**:
  - Markdown: legenda depois de cada tabela (mapa função → chave para as tabelas dos laços de seção) e de cada figura;
  - PDF: `_figura` e `_bloco_chave_valor` emitem a legenda; cada `_tabela` (24) e as 2 tabelas montadas à mão (capa e cobertura) recebem a legenda pela chave; contadores conferidos em `build_pdf`;
  - testes de cobertura: Markdown com e sem as bases novas; PDF sem as bases novas (`tests/test_pdf_generator.py`) e com elas, com e sem alinhamento hidrológico (`tests/test_relatorio_complementar.py`);
  - **T012 (SC-002)**, revisão do mapa contra o código: figura 01 passou a "Calculado neste relatório" (médias diárias); indicadores da capa ganharam a conferência da TEIFa/TEIP; chaves a mais `tab_capa_indicadores` e `tab_perfil_horario`. Toda chave usada no PDF e no Markdown existe no mapa, e nenhuma do mapa ficou sem uso.
- **US2**: rodapé "Fontes: ONS – Dados Abertos, N conjuntos; …" (538 pt, cabe com o número de página em 770 pt); cabeçalho `**Fontes**:` no Markdown.
- **US3**: aba `FONTES`, a última, com uma linha por aba.
- **T018 e T019**: `README.md` e histórico de `specs/003-analise-dados/spec.md`.
- **T020**: 231 testes aprovados (57 novos) em 37 s, com a rede bloqueada; nenhum dos 128 arquivos vigiados mudou.
- **T021, base real** (`python -m src.analyzer`, 21 s, sem aviso):
  - Markdown: 22 tabelas e 8 figuras, 30 legendas; PDF: legendas iguais a tabelas, blocos e figuras; cabeçalho e rodapé com 10 conjuntos;
  - aba `FONTES` com 56 linhas, nenhuma "origem não mapeada";
  - SC-003: as legendas citam os mesmos números de `GER_CONFERENCIA` e `DISP_CONFERENCIA` (70.895 de 70.895 horas), `HID_ALINHAMENTO` (70.731 de 70.731) e `ONS_DIVERGENCIAS` (4); TEIFa/TEIP com 21 de 21 meses reproduzidos;
  - SC-004: Markdown idêntico ao de T001 fora das linhas novas (372 linhas de conteúdo); as 56 abas idênticas célula a célula; nova só `FONTES`;
  - FR-013: as 8 figuras com o mesmo SHA-256 de antes;
  - PDF com 31 páginas (27 antes), pelas legendas;
  - SC-006: entregue em 06/10/2026, antes de 13/10/2026.
