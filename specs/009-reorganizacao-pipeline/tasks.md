---

description: "Task list for feature 009 — reorganização em cinco etapas, perfil da usina e conclusão do relatório"
---

# Tasks: Reorganização do Projeto num Fluxo de Cinco Etapas, Reutilizável para Outras Usinas

**Input**: Design documents from `/specs/009-reorganizacao-pipeline/`

**Prerequisites**: plan.md, spec.md, research.md (R1 a R17), data-model.md, contracts/ (cli-etapas.md, perfil-usina.md), quickstart.md

**Tests**:
- Incluídos: a constituição exige testes, e a spec pede cobertura sem perda (FR-012, SC-007) e testes da conclusão (R17).
- Rodam sempre sem rede: `$env:HTTP_PROXY = "http://127.0.0.1:9"; $env:HTTPS_PROXY = "http://127.0.0.1:9"; python -m pytest tests -q`.
- Dentro de cada história, os testes vêm antes e devem falhar antes da implementação.

**Organization**:
- As tarefas são agrupadas por história. A ordem das fases segue a research R1, não a ordem das prioridades:
  - a US6 (conclusão) vem primeiro, por causa da fiscalização de 14 a 16/10/2026;
  - a US5 (inventário) é independente e foi adiantada;
  - a US2 (constituição e specs) precisa vir antes da base técnica, porque a constituição atual restringe o escopo à São Domingos.
- Toda fase que muda código termina com a suíte sem rede. A partir da fase 5, também com o `comparar` contra a linha de base.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem depender de tarefa pendente).
- **[Story]**: história da spec (US1 a US6).

## Path Conventions

- **Código**: `src/` e `tests/` na raiz do projeto. O layout final está no plan.md (Project Structure), e o destino de cada módulo, no data-model.md (seção 6).
- **Documentos desta feature**: `specs/009-reorganizacao-pipeline/`.
- **Scripts de apoio**: no scratchpad da sessão, nunca em `src/`.

---

## Phase 1: Setup (preparação)

**Purpose**: deixar a versão aprovada recuperável e aplicar a regra de duas cópias antes de qualquer mudança (research R1, fase 0; FR-027 e FR-028).

- [X] T001 Criar a cópia `_backup_2026-10-07_antes_conclusao/`.
  - Conteúdo: `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `README.md` e `requirements.txt`, mais `LEIA-ME.txt` e `conftest.py` com `collect_ignore_glob = ["*"]`.
  - Gravar `copia.json` com `{arquivo, bytes, sha256}` de cada arquivo e conferir a cópia contra a origem antes de seguir.
  - Feito com um script no scratchpad, porque a ferramenta `copia-seguranca` só existe na US4.
- [X] T002 Excluir as cópias datadas de 06/10/2026 ou antes (as dez `_backup_2026-10-0[2-6]_*`, por autorização do usuário em 07/10/2026, FR-028) e, para ficarem duas, a mais antiga entre as restantes (`_backup_2026-10-07_antes_revisao008`).
  - Conferir antes que `_backup_2026-10-07_antes_conclusao/` está completa (T001).
  - Esperado ao final: só `_backup_2026-10-07_antes_figuras/` e `_backup_2026-10-07_antes_conclusao/`.
- [X] T003 Registrar a linha de base em "Registro de execução", ao final de `specs/009-reorganizacao-pipeline/tasks.md`:
  - suíte sem rede (esperado: 244 aprovados);
  - páginas do PDF (29);
  - abas da planilha (57);
  - SHA-256 das 8 figuras de `reports/figures/`;
  - espaço liberado pela T002.

**Checkpoint**: duas cópias; versão aprovada recuperável pela cópia e pelo git (commit `a8315cc`).

---

## Phase 2: User Story 6 - Conclusão sucinta, com indícios e verificações (Priority: P1), entregue primeiro

**Goal**: seção "Conclusão" no relatório atual: quatro listas geradas pelo catálogo C1 a C11 (FR-036 a FR-043; research R17), aprovada pelo usuário antes da reorganização.

**Independent Test**: gerar o relatório da São Domingos e conferir:
- lugar, sumário, quatro listas, até cinco itens e uma página;
- a UG2 nomeada com os números;
- nenhum termo de avaliação de desempenho;
- a aba `CONCLUSAO` (quickstart, cenário 2).

### Tests for User Story 6

- [X] T004 [P] [US6] Escrever `tests/test_conclusao.py`, com `ResultadosAnalise` sintéticos (`conftest.py` e as bases sintéticas de `tests/test_relatorio_complementar.py`) e campos ajustados para cada caso:
  - cada regra C1 a C11 dispara quando a condição do catálogo da spec é atendida e não dispara quando não é, ou quando a base de que depende não existe;
  - `res.conclusao` traz itens `{lista, ordem, regra, texto, secoes}`, com `lista` em {`pontos_atencao`, `possiveis_problemas`, `confirmar_agente`, `verificar_campo`};
  - ordem do catálogo;
  - termos proibidos ausentes em todos os textos: "satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente", "culpa";
  - nenhum texto de constatação (`res.achados`) aparece num item (FR-041);
  - C2 nomeia a unidade, como o ONS a identifica, com a parcela da TEIFa e os meses;
  - os itens das regras C7 e C8 em `confirmar_agente` saem juntos num item só.
- [X] T005 [P] [US6] Acrescentar a `tests/test_estrutura_relatorio.py`:
  - `conclusao` entre `qualidade` e `notas` em `SECOES` (ajustar `CHAVES` e as contagens: só EVT, 12 seções; completo, 15);
  - Markdown com `## N. Conclusão`, a frase de abertura e os quatro subtítulos "Pontos de atenção", "Possíveis problemas", "A confirmar com o agente" e "A verificar em campo";
  - até cinco itens por lista, cada um terminando com "(seção N)" ou "(seções N e M)";
  - PDF com "Conclusão" em `titulos_secoes` antes das notas, e a seção das notas começando no máximo uma página depois da conclusão (`paginas_secoes`);
  - a aba `CONCLUSAO` em `exportar_tabelas`, com todos os itens, coberta pela aba `FONTES` (ajustar `tests/test_fontes_relatorio.py`);
  - um item das notas metodológicas descrevendo as regras e os limiares.

### Implementation for User Story 6

- [X] T006 [US6] Acrescentar os limiares da conclusão a `src/config.py`, com comentário apontando para o catálogo da spec 009 (data-model, seção 1):
  - `LIMIAR_CONCLUSAO_EVT_PARADA_PCT` = 10;
  - `LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT` = 50;
  - `LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT` = 80;
  - `LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA` = 2/3;
  - `LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT` = 50 (meses com limitação forçada de potência, HEDF);
  - `LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH` = 5;
  - `LIMIAR_CONCLUSAO_R7_HORAS` = 100;
  - `LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS` = 30;
  - `LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT` = 20;
  - `LIMIAR_CONCLUSAO_R9_HORAS` = 24;
  - `MAXIMO_ITENS_CONCLUSAO` = 5.
- [X] T007 [US6] Implementar em `src/analyzer.py` a função `montar_conclusao(res) -> List[Dict]`, com as regras C1 a C11 do catálogo da spec, e o campo `conclusao` em `ResultadosAnalise`, preenchido em `analisar` depois de `montar_achados`.
  - **Reuso**: aproveitar os cálculos que as constatações já fazem, extraindo para funções auxiliares o que for comum, sem mudar o texto das constatações:
    - C1: `_achado_paradas`, `_achado_evt_nivel_geracao` e `_achado_programacao`;
    - C2 e C10: `_achado_estados_operativos` e `res.ons` (decomposição, horas, anual por unidade);
    - C3: `_achado_afluencia`;
    - C4: `_achado_perfil_diurno`;
    - C5: `_achado_disponibilidade` e `_achado_indicadores_ons`;
    - C6: `_achado_programacao`;
    - C7: `_achado_disponibilidade_sincronizada` e `res.ons["divergencias"]`;
    - C8 e C11: `res.validacao` (R7 e R9) e as sinalizações de `res.hidrologia`;
    - C9: `_achado_geracao` e `_achado_evt`.
  - **Texto**: uma frase por item, com os formatadores de `src/formatacao.py` e vocabulário de indício (FR-039). `secoes` guarda as chaves de `estrutura_relatorio.SECOES`.
- [X] T008 [US6] Em `src/estrutura_relatorio.py`, inserir `Secao("conclusao", "Conclusão")`, sempre presente, entre `qualidade` e `notas`.
- [X] T009 [P] [US6] Em `src/analyzer.py`, completar a apresentação da conclusão:
  - **Markdown**: em `_md_conteudo_secao`, o ramo `conclusao` escreve a frase de abertura metodológica (indícios a confirmar, gerados pelas regras das notas metodológicas; não afirmam causa nem avaliam o desempenho) e as quatro listas, com até `MAXIMO_ITENS_CONCLUSAO` itens. As chaves de `secoes` viram "(seção N)" pelos números de `secoes_presentes(res)`.
  - **Planilha**: em `exportar_tabelas`, a aba `CONCLUSAO` com as colunas `lista`, `ordem`, `regra`, `texto` e `secoes` e todos os itens.
  - **Notas**: em `notas_metodologicas`, um item com as regras e os limiares, gerado a partir das constantes da T006.
- [X] T010 [P] [US6] Em `src/pdf_generator.py`, criar `_secao_conclusao`:
  - título, frase de abertura, subtítulos (estilo `subsecao`) e itens (estilo `nota`, com marcador), com o mesmo texto do Markdown;
  - a seção começa em página nova quando não couber inteira na página corrente;
  - ajustar `build_pdf` se preciso para a conferência das constatações emitidas.
- [X] T011 [P] [US6] Em `src/fontes_relatorio.py`, cobrir a aba `CONCLUSAO` nas regras das abas (`_ABAS_EXATAS`), como "calculado neste relatório a partir de" todos os conjuntos carregados.
- [X] T012 [US6] Executar a suíte sem rede (T004 e T005 devem passar, sem regressão nos demais) e gerar o relatório real em `reports/` com `python -m src.analyzer`. Conferir, com um script no scratchpad:
  - SC-009;
  - a UG2 em "Possíveis problemas", com os meses de limitação forçada e a participação na TEIFa;
  - nenhum termo proibido;
  - a página da conclusão renderizada em imagem (PyMuPDF instalado no scratchpad) e conferida a olho;
  - as demais seções, a planilha (fora a aba nova e a `FONTES`) e as figuras iguais à cópia de T001.
- [X] T013 [US6] Apresentar ao usuário o texto da conclusão gerada em `reports/relatorio_analise_estatistica.pdf` (as quatro listas) e o catálogo de limiares. Aguardar a aprovação, aplicar os ajustes pedidos (limiares ou redação dos modelos) e repetir a T012 até aprovar.

**Checkpoint**: relatório com a conclusão aprovada, pronto para a fiscalização.

---

## Phase 3: User Story 5 - Pasta do projeto só com o que é usado (Priority: P3), inventário inicial

**Goal**: inventário de limpeza aprovado e aplicado (FR-031 a FR-034; research R15). Fase independente, adiantada para que a aprovação vá junto com a da conclusão.

**Independent Test**: conferir a pasta contra o inventário aprovado (quickstart, cenário 8).

- [X] T014 [P] [US5] Gerar `specs/009-reorganizacao-pipeline/inventario-limpeza.md` com um script no scratchpad (formato do data-model, seção 8; colunas Item, Tamanho, Uso atual, Ação proposta, Motivo, Decisão do usuário). Itens:
  - `.bak` soltos (raiz, `src/`, `tests/`, `specs/`);
  - `reports/_versao_anterior_2026-09-30/`;
  - `.pytest_cache/` e `__pycache__/`;
  - `DicionarioDados_EnergiaVertidaTurbinavel.json` na raiz, com a comparação de conteúdo com `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json`;
  - `Docs_usina/Docs_usina.rar`, com a lista do conteúdo (`tar -tf`) comparada aos PDFs da pasta;
  - `Docs_usina/` (PDFs), para `usinas/sao_domingos/documentos/`;
  - ofício, RF 0009/2017 e modelo do RF 2026, para `usinas/sao_domingos/documentos/`;
  - resoluções da ANEEL, RFs SEI e imagens de tipos de despacho, para `referencias/`;
  - imagem do WhatsApp;
  - `data/ccee/` e `data/aneel_bi/`;
  - `.agents/skills/`.

  Ficam em "manter": `venv/`, `.mcp.json`, `.claude/` e `.specify/`. Tamanhos medidos na hora.
- [X] T015 [US5] Apresentar o inventário ao usuário (pode ir junto com a T013) e registrar a decisão de cada item na coluna "Decisão do usuário" de `specs/009-reorganizacao-pipeline/inventario-limpeza.md`.
- [X] T016 [US5] Aplicar só o que foi aprovado, com registro de cada exclusão ou movimentação em `specs/009-reorganizacao-pipeline/inventario-limpeza.md`.
  - **Dicionário na raiz**: se o conteúdo for igual ao baixado, apontar `DATA_DICTIONARY_JSON` em `src/config.py` para `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json`, rodar `tests/test_validator.py` e só então excluir o arquivo da raiz.
  - **Documentos**: são movidos, nunca excluídos, sem aprovação explícita (FR-033).
- [X] T017 [US5] Atualizar `.gitignore` com `usinas/*/documentos/` e `referencias/`, para que os documentos movidos continuem fora do git. Conferir o SC-008: cada exclusão consta do inventário aprovado; `data/raw/` está intacto; não há `.bak` soltos fora de `data/processed/`. Rodar a suíte sem rede.

**Checkpoint**: pasta limpa conforme o aprovado; relatório inalterado.

---

## Phase 4: User Story 2 - Constituição e specs limpas, na ordem do fluxo (Priority: P1)

**Goal**: constituição 2.0.0 em vigor e as cinco specs de etapa com o mapeamento, aprovados antes de qualquer mudança de organização do código (FR-013 a FR-019; research R12 e R13).

**Independent Test**: leitura da constituição e das cinco specs contra o mapeamento (quickstart, cenário 7).

- [X] T018 [P] [US2] Escrever o rascunho da constituição 2.0.0 em `specs/009-reorganizacao-pipeline/constituicao-rascunho.md`, conforme a research R13:
  - **Princípios**:
    - SDD com uma spec por etapa;
    - relatório fiel aos dados: constatações e conclusão por regras, sem parecer;
    - uma usina por perfil, com homônimos excluídos;
    - coleta completa e rastreável;
    - tratamento sem descarte;
    - conferência entre fontes;
    - relatório padronizado: estrutura, fonte em cada figura e tabela, seaborn e paleta validada, figuras padronizadas.
  - **Requisitos técnicos**:
    - Python ≥ 3.11 no `venv`;
    - Windows e PowerShell;
    - gravação segura com uma cópia `.bak` por arquivo de dados;
    - no máximo duas cópias do projeto;
    - no máximo duas versões anteriores por arquivo bruto;
    - testes sem rede;
    - um nível de log.
  - **Governança**: mudanças atualizam a spec da etapa; histórico no git; versionamento semântico.
  - **O que não entra**: histórico de emendas, valores de usina específica.
- [X] T019 [P] [US2] Escrever `specs/009-reorganizacao-pipeline/novas-specs/001-coleta-dados/spec.md` e `checklists/requirements.md`. Juntar os requisitos em vigor das specs 001, 004 (coleta da programação e dos indicadores), 005 (versões, linhas irregulares, nível de log) e 006 (coleta e extração das bases complementares, dicionários), mais os da reorganização:
  - perfil como entrada (contracts/perfil-usina.md);
  - `--sem-portal` e `--forcar-download`;
  - extração por identificador e conferência do perfil;
  - artefatos de `data/usinas/<slug>/coleta/` (data-model, seção 4);
  - poda das versões anteriores (FR-030);
  - `etapa.json`.
- [X] T020 [P] [US2] Escrever `specs/009-reorganizacao-pipeline/novas-specs/002-tratamento-dados/spec.md` e `checklists/requirements.md`. Juntar os requisitos em vigor das specs 002 e 006 (tratamento das bases complementares, convenção de hora da hidrologia, sinalizações, `.bak` dos dados tratados), mais a fronteira da research R3 e os artefatos de `tratamento/`.
- [X] T021 [P] [US2] Escrever `specs/009-reorganizacao-pipeline/novas-specs/003-conferencia/spec.md` e `checklists/requirements.md`, com as seis conferências da research R8, a meta e o código 3 da hidrologia, as tolerâncias, o resultado de conferência (data-model, seção 5) e "não aplicável". Registrar como fora do relatório as conferências manuais com CCEE e ANEEL de 01 e 02/10/2026, com os resultados guardados na research da spec 004.
- [X] T022 [P] [US2] Escrever `specs/009-reorganizacao-pipeline/novas-specs/004-analises/spec.md` e `checklists/requirements.md`. Juntar os requisitos em vigor das specs 003 e 004 e das análises da 006, mais:
  - a FR-005 da spec 003 com a redação nova (sem parecer; conclusão por regras);
  - as regras C1 a C11 e os limiares (spec 009, US6);
  - os dados das figuras;
  - os limiares gerais × perfil (data-model, seção 1).
- [X] T023 [P] [US2] Escrever `specs/009-reorganizacao-pipeline/novas-specs/005-geracao-relatorio/spec.md` e `checklists/requirements.md`. Juntar os requisitos em vigor do relatório da spec 003 e das specs 007 e 008, com as revisões já aplicadas e sem remissões:
  - capa com identificação, cadastro, parâmetros, indicadores e sumário;
  - constatações nas seções;
  - legendas de fonte e conferência;
  - rodapé com a numeração;
  - figuras padronizadas;
  - Markdown igual ao PDF;
  - seção "Conclusão";
  - planilha com `FONTES` e `CONCLUSAO`;
  - `--data-geracao`.
- [X] T024 [US2] Escrever `specs/009-reorganizacao-pipeline/mapeamento-specs.md` (formato do data-model, seção 9). Cada US, FR e SC das specs 001 a 009 entra com a situação (em vigor ou superado, com o motivo) e o destino (spec nova e requisito, ou a constituição). Conferir que 100 % dos itens em vigor têm destino (SC-003). Depende de T019 a T023.
- [X] T025 [US2] Apresentar ao usuário `specs/009-reorganizacao-pipeline/constituicao-rascunho.md`, as cinco specs de `novas-specs/` e `mapeamento-specs.md`. Aguardar a aprovação e aplicar os ajustes.
- [X] T026 [US2] Gravar a constituição aprovada em `.specify/memory/constitution.md` com `/speckit-constitution` (versão 2.0.0; ratificação 2026-09-30; última revisão na data da gravação). Depois:
  - remover o comentário "SYNC IMPACT REPORT";
  - conferir que não há "Emenda", "SYNC IMPACT" nem valores da São Domingos (153, MSUHSD, "São Domingos") no arquivo (quickstart, cenário 7).

**Checkpoint**: constituição 2.0.0 em vigor; o gate da fase 5 está liberado.

---

## Phase 5: Foundational (base técnica da reorganização; bloqueia US1, US3 e US4)

**Purpose**: linha de base reproduzível, comparação, perfil da usina e módulos comuns, antes de mover o código por etapa (research R2, R5, R6 e R10).

**⚠️ CRITICAL**: nenhuma tarefa da US1, US3 ou US4 começa antes desta fase.

- [X] T027 Acrescentar a opção `--data-geracao "DD/MM/AAAA HH:MM"` ao fluxo atual (`src/analyzer.py`, `main`, e `src/pdf_generator.py`). Ela:
  - fixa a data exibida na capa do PDF e no "**Gerado em**" do Markdown;
  - liga `reportlab.rl_config.invariant = 1` durante a montagem do PDF (research R2).

  Teste em `tests/test_pdf_generator.py`: dois PDFs gerados com a mesma data são idênticos byte a byte.

  Na mesma tarefa, antes da linha de base (decisão do usuário em 07/10/2026; spec 005, FR-021 e FR-022), reformular os dois textos do relatório que citam caminhos do código ou dos dados:
  - "Parâmetro de análise (src/config.py)" passa a "Parâmetro de análise", na tabela de parâmetros e na aba PARAMETROS;
  - "(coluna qualidade de data/processed/uhe_sao_domingos_ons_hidrologia_horaria.csv)" e o equivalente da disponibilidade passam a "(coluna qualidade da série horária tratada)".

  Conferir que o resto do relatório não muda.
- [X] T028 Criar a cópia `_backup_2026-10-07_antes_reorganizacao/`, no formato da T001.
  - Gravar em `linha_de_base/` o relatório gerado com `python -m src.analyzer --output-dir <cópia>\linha_de_base --figures-dir <cópia>\linha_de_base\figures --data-geracao "07/10/2026 08:53"`.
  - Conferir a cópia e excluir a mais antiga (`_backup_2026-10-07_antes_figuras`), deixando duas.
  - Depende das aprovações da T013 e da T025.
- [X] T029 [P] Criar `src/comum/__init__.py` e `src/comum/comparacao.py`, com `comparar(pasta_atual, pasta_referencia) -> List[str]`:
  - PDF, Markdown, CSV e PNG byte a byte;
  - planilha célula a célula, aba a aba, com a mesma ordem de abas;
  - devolve as diferenças;
  - execução temporária `python -m src.comum.comparacao <atual> <referencia>`, com código 6 se houver diferença.

  Testes em `tests/comum/test_comparacao.py`. Rodar contra `reports/` regerado com a mesma data (esperado: 0).
- [X] T030 [P] Escrever `tests/comum/test_perfil.py` a partir do data-model (seção 2) e do contrato do perfil. Casos:
  - leitura do perfil da São Domingos;
  - recusa de perfil sem campo obrigatório;
  - `usina.slug` fora de `[a-z0-9_]+` ou diferente do nome da pasta;
  - `usina.estado` fora de "2 letras maiúsculas";
  - `identificacao.ceg` fora do "padrão `UHE.PH.UF.NNNNNN-D.DD`";
  - `parametros.unidades_geradoras` < 1;
  - `parametros.potencia_unitaria_mw` × unidades ≠ potência instalada "(± 0,1)";
  - `parametros.ip_referencia` e `parametros.teif_referencia` fora de "0 ≤ x < 1";
  - `parametros.rendimento_turbina_gerador` fora de "0 < x ≤ 1";
  - `parametros.perda_hidraulica_m` ≥ queda bruta;
  - `analises.faixas_geracao_mw` não "crescente" ou fora de "> 1 MW (parada) e < plena carga";
  - a mensagem lista todos os problemas de uma vez;
  - valores derivados (engolimento máximo, potência autorizada esperada, disponibilidade de referência, produtividade nominal, limites físicos) iguais aos de `src/config.py`.
- [X] T031 Criar `usinas/sao_domingos/perfil.toml`, com o conteúdo do contrato `contracts/perfil-usina.md`, e `src/comum/perfil.py`, com:
  - `carregar_perfil(slug) -> Perfil` (dataclass congelada);
  - validação completa (mensagem com todos os problemas; exceção que a linha de comando converte no código 4);
  - valores derivados.

  A T030 deve passar.
- [X] T032 Criar `src/comum/regras.py` (regras gerais, data-model seção 1, inclusive os limiares da conclusão da T006, `FAIXAS_GERACAO_INTERMEDIARIAS_MW` sai para o perfil) e `src/comum/caminhos.py`. `caminhos.py` traz:
  - pastas compartilhadas de `data/raw/`;
  - `pasta_etapa(slug, etapa)` para `data/usinas/<slug>/<etapa>/`;
  - `pasta_relatorio(slug)` para `reports/<slug>/`;
  - nomes dos arquivos da seção 4 do data-model.

  Fazer `src/config.py` reexportar as regras e calcular os valores da usina a partir de `carregar_perfil("sao_domingos")`. É uma ponte temporária, removida na T060. Os módulos atuais seguem funcionando sem outra mudança.
- [X] T033 Mover `src/logger.py`, `src/formatacao.py`, `src/persistencia.py` e `src/models.py` para `src/comum/` (`logger.py`, `formatacao.py`, `persistencia.py`, `modelos.py`) e atualizar os imports em todos os módulos de `src/` e em `tests/`. Mover os testes correspondentes para `tests/comum/`.
- [X] T034 Rodar a suíte sem rede. Regerar com `python -m src.analyzer --data-geracao "07/10/2026 08:53"` e rodar `python -m src.comum.comparacao reports _backup_2026-10-07_antes_reorganizacao\linha_de_base` (esperado: 0 diferenças).

**Checkpoint**: perfil em uso; relatório idêntico à linha de base; base pronta para mover o código por etapa.

---

## Phase 6: User Story 1 - Gerar o relatório por um fluxo de cinco etapas (Priority: P1) 🎯 MVP da reorganização

**Goal**: pacotes por etapa, linha de comando única, `etapa.json`, pastas por usina, conferência como etapa, relatório idêntico à linha de base (FR-001 a FR-012; research R3, R4, R7, R8, R9 e R10).

**Independent Test**: `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`, seguido de `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-07_antes_reorganizacao\linha_de_base`, com 0 diferenças; e etapa sem a anterior saindo com o código 5 (quickstart, cenários 3 e 4).

**Método**:
- Os módulos antigos continuam funcionando como oráculo até a T060.
- Cada etapa nova é conferida contra os arquivos ou objetos que o fluxo antigo produz.
- As funções são movidas sem reescrever a lógica (research R10). Os testes de cada módulo movido vão para `tests/<etapa>/`.

### Tests for User Story 1

- [X] T035 [P] [US1] Escrever `tests/comum/test_pipeline.py`, conforme o data-model (seção 3):
  - `etapa.json` com `etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status` ∈ {`concluida`, `falha`, `desatualizada`}, `codigo_saida`, `etapa_anterior`, `arquivos` (`{nome, bytes, sha256}`) e `resumo`;
  - etapa sem a anterior `concluida` sai com 5 sem gravar nada;
  - etapa concluída marca as seguintes como `desatualizada`;
  - falha grava `falha` com o código.
- [X] T036 [P] [US1] Escrever `tests/integracao/test_cli.py`, conforme `contracts/cli-etapas.md`:
  - comandos `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio`, `completo`, `copia-seguranca` e `comparar`;
  - `--usina` obrigatório nos de etapa;
  - opções `--sem-portal`, `--forcar-download`, `--data-geracao` e `--log-level`;
  - opções retiradas inexistentes;
  - perfil inválido sai com 4;
  - mensagens obrigatórias do contrato;
  - `completo` para na primeira etapa com código diferente de 0.

### Implementation for User Story 1

- [X] T037 [US1] Criar os pacotes `src/coleta/`, `src/tratamento/`, `src/conferencia/`, `src/analises/` e `src/relatorio/` (`__init__.py`), mais:
  - `src/pipeline.py`: ordem das etapas, leitura e gravação de `etapa.json`, pré-requisito com código 5, invalidação das seguintes, códigos 0 a 6;
  - `src/__main__.py`: argparse conforme o contrato, carregando o perfil (código 4) e chamando `pipeline`.

  Comandos ligados a funções de etapa ainda vazias. A T035 deve passar.
- [X] T038 [US1] Mover `src/collector.py` para `src/coleta/catalogo.py` e `src/dicionarios_ons.py` para `src/coleta/dicionarios.py`. O registro dos dicionários passa a `data/usinas/<slug>/coleta/dicionarios.csv`. Portar `tests/unit/test_collector.py` e `tests/test_dicionarios_ons.py` para `tests/coleta/`.
- [X] T039 [US1] Mover `src/filter.py` e `src/consolidator.py` para `src/coleta/evt.py`. A extração passa a usar `perfil.identificacao.cod_usina` e `perfil.identificacao.nome_ons`, e grava `evt_extraido.csv` e `auditoria_evt.csv` em `data/usinas/<slug>/coleta/`. Portar `tests/unit/test_filter.py` e `tests/unit/test_audit.py`.
- [X] T040 [US1] Criar `src/coleta/conjuntos.py` a partir de `src/conjuntos_ons.py` (research R3). Ele reúne:
  - `Regra`, `DescricaoConjunto`, `selecionar_recursos`, `sincronizar_conjunto`, `linhas_formato_irregular`, `ler_csv_texto` e `avisar_linhas_irregulares`;
  - `extrair_arquivo`: identificação, leitura numérica e auditoria da extração, sem convenção de hora e sem duplicatas;
  - as descrições de disponibilidade, hidrologia e geração montadas com os valores do perfil (tabela de identificadores do contrato do perfil);
  - gravação de `<conjunto>_extraido.parquet` e `auditoria_<conjunto>.csv`.

  Portar os casos de extração de `tests/test_conjuntos_ons.py`.
- [X] T041 [US1] Criar `src/coleta/indicadores.py`, `src/coleta/programacao.py` e `src/coleta/cadastro.py` com as partes de seleção, sincronização, leitura e extração (data-model, seção 6). O cadastro grava `cadastro_ficha.csv` sem as divergências, que vão para a conferência. Portar os casos correspondentes de `tests/test_indicadores_ons.py`, `tests/test_programacao_ons.py` e `tests/test_cadastro_ons.py`.
- [X] T042 [US1] Criar `src/coleta/etapa.py` com `executar_coleta(perfil, sem_portal, forcar_download)`:
  - ordem: EVT, período, indicadores, programação, disponibilidade, hidrologia, geração, cadastro e dicionários;
  - `--sem-portal` sem consulta ao catálogo;
  - código 2 para arquivo não obtido ou não lido;
  - `resumo` do `etapa.json`.

  Ligar ao comando `coleta`.
- [X] T043 [US1] Validar a coleta em `data/usinas/sao_domingos/coleta/` com `python -m src coleta --usina sao_domingos --sem-portal` e um script no scratchpad:
  - `evt_extraido.csv` igual a `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv`;
  - `auditoria_evt.csv` igual a `relatorio_auditoria_varredura.csv`;
  - contagens de extração de cada conjunto iguais às colunas correspondentes das auditorias atuais;
  - nenhum download.
- [X] T044 [US1] Criar `src/tratamento/series.py` com o restante de `montar_serie`:
  - convenção de hora (`hora_de_inicio`);
  - duplicatas entre arquivos (conflitantes contadas na auditoria);
  - recorte do período;
  - `listar_ausencias`;
  - campos finais da auditoria;
  - gravação e leitura (`exportar_serie` e `carregar_serie_processada`).

  `periodos_continuos` vai para `src/comum/`. Portar os casos de série de `tests/test_conjuntos_ons.py`.
- [X] T045 [US1] Mover `src/processor.py` para `src/tratamento/evt.py` e `src/validator.py` para `src/tratamento/validacao.py`. O dicionário vem de `data/raw/_dicionarios/`. Saídas: `evt_tratado.parquet`, `.csv` e `.xlsx` e `validacao_fisica.csv` e `.md`, em `data/usinas/<slug>/tratamento/`. Portar `tests/test_processor.py` e `tests/test_validator.py`.
- [X] T046 [US1] Criar `src/tratamento/indicadores.py`, `programacao.py`, `disponibilidade.py`, `hidrologia.py` e `geracao.py` com as partes de tratamento (qualidade, nível implausível, montar, gravar e ler; data-model, seção 6). Portar os casos de tratamento dos testes dos módulos `*_ons`.
- [X] T047 [US1] Criar `src/tratamento/etapa.py` com `executar_tratamento(perfil)`, que lê só `data/usinas/<slug>/coleta/` e grava `tratamento/` e `etapa.json`. Ligar ao comando `tratamento`.
- [X] T048 [US1] Validar o tratamento (FR-011): cada arquivo de `data/usinas/sao_domingos/tratamento/` tem o mesmo conteúdo do arquivo correspondente de `data/processed/` (mapa de nomes do data-model, seção 4), conferido com DataFrames por um script no scratchpad.
- [X] T049 [P] [US1] Escrever `tests/conferencia/`, com:
  - os testes de `conferir_geracao`, `conferir_com_evt`, `alinhar_com_evt`, `comparar_indicadores_e_horas` e `recalcular_taxas`, portados;
  - as divergências do cadastro com o perfil;
  - o resultado de conferência (data-model, seção 5): `aplicavel` falso com `motivo` sem a base; `meta` e `meta_atingida` nas vazões; código 3 abaixo da meta.
- [X] T050 [US1] Criar `src/conferencia/resultado.py` (`ResultadoConferencia`) e `src/conferencia/geracao.py`, `disponibilidade.py`, `vazoes.py`, `indicadores.py` e `cadastro.py` (research R8), mais `src/conferencia/etapa.py` com `executar_conferencia(perfil)`:
  - grava `conferencias.pkl` (com `versao_formato`) e os CSV da seção 4 do data-model;
  - sai com código 3 se as vazões ficarem abaixo da meta.

  Ligar ao comando `conferencia`. A T049 deve passar.
- [X] T051 [US1] Criar `src/analises/resultados.py`, com:
  - `ResultadosAnalise`: os campos atuais, mais `conclusao`, `serie_diaria` (médias diárias da figura 01) e `vazoes_anuais` (médias anuais da figura 05);
  - `salvar_resultados` e `carregar_resultados` (pickle com `versao_formato` conferida).
- [X] T052 [US1] Mover para `src/analises/` a parte de análise de `src/analyzer.py` e dos módulos `*_ons` (data-model, seção 6), nos arquivos:
  - `cobertura.py`;
  - `evt.py`;
  - `indicadores.py` (decomposição e `analisar_indicadores_ons`);
  - `programacao.py`;
  - `disponibilidade.py`;
  - `hidrologia.py`;
  - `geracao.py`;
  - `cadastro.py`;
  - `constatacoes.py`;
  - `conclusao.py` (da T007).

  `analisar` (em `src/analises/etapa.py`) passa a receber os resultados de conferência em vez de calculá-los e os coloca nos mesmos campos de hoje, para que fontes e relatório não mudem. Portar `tests/test_analyzer.py`, `tests/test_conclusao.py` e os casos de análise dos testes `*_ons` para `tests/analises/`.
- [X] T053 [US1] Completar `src/analises/etapa.py` com `executar_analises(perfil)`, que lê `tratamento/` e `conferencias.pkl` e grava `resultados.pkl` e `etapa.json`. Ligar ao comando `analises`. Validar com um script no scratchpad: cada campo de `resultados.pkl` é igual (`DataFrame.equals` e igualdade de dicts) ao `ResultadosAnalise` do fluxo antigo.
- [X] T054 [US1] Mover `src/fontes_relatorio.py` para `src/relatorio/fontes.py` e `src/estrutura_relatorio.py` para `src/relatorio/estrutura.py`. A conferência passa a ler os resultados da etapa de conferência. Portar `tests/test_fontes_relatorio.py` e `tests/test_estrutura_relatorio.py` para `tests/relatorio/`.
- [X] T055 [US1] Criar `src/relatorio/figuras.py`, com os gráficos de `src/analyzer.py` desenhados só a partir de `ResultadosAnalise` (`serie_diaria` e `vazoes_anuais` no lugar do `df`), mesma paleta e mesmos tamanhos (`TAMANHO_FIGURA_PADRONIZADA`). As 8 figuras devem sair byte a byte iguais.
- [X] T056 [US1] Mover para `src/relatorio/`:
  - `conteudo.py`: `linhas_tabela_*`, `textos_tabelas`, `indicadores_capa`, `pares_*`, `legenda_figura` e `notas_*`;
  - `planilha.py`: `exportar_tabelas`;
  - `markdown.py`: `gerar_relatorio_md` e `_md_*`;
  - `pdf.py`: de `src/pdf_generator.py`, com `--data-geracao`.

  Portar `tests/test_pdf_generator.py` e `tests/test_relatorio_complementar.py`.
- [X] T057 [US1] Criar `src/relatorio/etapa.py` com `executar_relatorio(perfil, data_geracao)`, que lê `resultados.pkl` e grava `reports/<slug>/` e `etapa.json`. Ligar ao comando `relatorio`. Ligar `comparar` à linha de comando (`python -m src comparar --usina <slug> --referencia <pasta>`).
- [X] T058 [US1] Ligar o comando `completo` em `src/pipeline.py` (cinco etapas em ordem; para no primeiro código diferente de 0) e passar as T035 e T036.
- [X] T059 [US1] Validar o fluxo completo e o relatório em `reports/sao_domingos/` (SC-001 e SC-002):
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`;
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-07_antes_reorganizacao\linha_de_base`, com 0 diferenças;
  - `python -m src relatorio --usina sao_domingos` sozinho;
  - etapa sem a anterior, com código 5;
  - tempo do `completo` dentro de 15 min.
- [X] T060 [US1] Remover de `src/` os módulos antigos e a ponte, e atualizar as dependências:
  - **Módulos antigos**: `src/main.py`, `src/analyzer.py`, `src/pdf_generator.py`, `src/processor.py`, `src/validator.py`, `src/collector.py`, `src/filter.py`, `src/consolidator.py`, `src/conjuntos_ons.py`, `src/dicionarios_ons.py`, `src/indicadores_ons.py`, `src/programacao_ons.py`, `src/disponibilidade_ons.py`, `src/hidrologia_ons.py`, `src/geracao_ons.py`, `src/cadastro_ons.py`, `src/fontes_relatorio.py` e `src/estrutura_relatorio.py`.
  - **Ponte**: `src/config.py` (T032).
  - **Testes antigos**: os de `tests/` já portados, inclusive `tests/unit/` e `tests/integration/`.
  - **Conformidade**: `tests/test_conformidade.py` vai para `tests/comum/test_conformidade.py`, com dependências, loggers e ponto de entrada únicos.
  - **Logger**: `LOGGERS_PIPELINE` em `src/comum/logger.py` com os nomes dos módulos novos.

  Rodar a suíte sem rede e repetir o `comparar` da T059 (esperado: 0).

**Checkpoint**: fluxo de cinco etapas em uso; relatório idêntico à linha de base; nenhum módulo antigo.

---

## Phase 7: User Story 3 - Usar a mesma lógica com outras usinas (Priority: P2)

**Goal**: análises e textos derivados do perfil; usina fictícia gerando relatório completo sem menção à São Domingos (FR-020 a FR-026; research R11).

**Independent Test**: teste de integração da usina fictícia e recusa de perfil incompleto (quickstart, cenário 5).

### Tests for User Story 3

- [X] T061 [P] [US3] Criar `tests/fixtures/usina_ficticia/perfil.toml`: três unidades de 30 MW, Francis, identificadores próprios (ex.: `cod_usina` 999, `nome_ons` "USINA FICTICIA", `ceg` "UHE.PH.GO.000001-0.01", `id_ons` "GOUHFI", `cod_programacao` "PRUHFI", `id_reservatorio` "PNUHFI", estado "GO") e parâmetros coerentes. Criar também `tests/fixtures/brutos_ficticios.py`, que gera, numa pasta temporária, arquivos brutos sintéticos de EVT, indicadores, disponibilidade, hidrologia, geração e cadastro. Os arquivos trazem uma linha de homônimo com só o identificador conferindo e não têm programação diária (seção omitida).
- [X] T062 [P] [US3] Escrever `tests/integracao/test_usina_ficticia.py`, que executa as cinco etapas com `--sem-portal` sobre as pastas temporárias e confere:
  - relatório completo;
  - nenhuma ocorrência de "São Domingos", "SAO DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD" ou "028761" no Markdown nem nos textos do PDF;
  - faixas de afluência com "entre uma e três unidades";
  - homônimo fora dos extraídos e contado na auditoria;
  - seção de programação ausente.
- [X] T063 [P] [US3] Escrever `tests/comum/test_literais.py`: nenhum arquivo de `src/` contém "Domingos", "DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD", "028761", "Kaplan" ou "AGEPAN". Esses valores ficam só em `usinas/sao_domingos/perfil.toml` e nos testes.

### Implementation for User Story 3

- [X] T064 [US3] Generalizar as faixas de afluência para N unidades em `src/analises/hidrologia.py` e `src/relatorio/figuras.py`:
  - rótulos "até uma unidade", "entre uma e {N por extenso} unidades" e "acima do engolimento máximo";
  - chave interna neutra no lugar de `ENTRE_UMA_E_DUAS_UNIDADES`;
  - função de número por extenso em `src/comum/formatacao.py`, com 2 virando "duas";
  - o texto da São Domingos não muda.
- [X] T065 [US3] Fazer `src/analises/evt.py` usar `perfil.analises.faixas_geracao_mw` e `perfil.analises.vertimento_minimo_m3s`. Fazer `src/relatorio/` (`conteudo.py`, `pdf.py` e `markdown.py`) usar nome, estado e parâmetros do perfil no título, na capa e nas notas. Remover os literais restantes encontrados pela T063.
- [X] T066 [US3] Rodar a suíte sem rede em `tests/` (T061 a T063 devem passar) e o `comparar` da T059 para `reports/sao_domingos/` (esperado: 0).

**Checkpoint**: outra usina pode ser analisada preenchendo só o perfil.

---

## Phase 8: User Story 4 - No máximo duas cópias de segurança (Priority: P2)

**Goal**: ferramenta `copia-seguranca` com conferência e poda; versões anteriores de brutos limitadas a duas (FR-027 a FR-030; research R14).

**Independent Test**: criar uma cópia numa pasta temporária com duas existentes e conferir a poda só depois da conferência (quickstart, cenário 6).

### Tests for User Story 4

- [X] T067 [P] [US4] Escrever `tests/comum/test_copia_seguranca.py` (data-model, seção 7):
  - a cópia traz `LEIA-ME.txt`, `conftest.py` e `copia.json` conferido;
  - as cópias mais antigas além de duas são excluídas só depois da conferência;
  - uma falha simulada na cópia remove a cópia incompleta e não toca nas outras;
  - dados brutos e `usinas/*/documentos/` ficam fora.
- [X] T068 [P] [US4] Escrever `tests/coleta/test_versoes_anteriores.py`: ao republicar, a coleta mantém no máximo as duas versões anteriores mais recentes de cada arquivo em `_versoes_anteriores/` e registra a poda no manifesto.

### Implementation for User Story 4

- [X] T069 [US4] Criar `src/comum/copia_seguranca.py`, com `criar_copia(motivo, raiz)` conforme a research R14. Ligar a `python -m src copia-seguranca --motivo <texto>`. A T067 deve passar.
- [X] T070 [US4] Acrescentar a poda das versões anteriores à preservação de versões em `src/coleta/catalogo.py`, com o registro no manifesto. A T068 deve passar.
- [X] T071 [US4] Conferir em `src/comum/persistencia.py` e nas pastas de dados:
  - `src/comum/persistencia.py` guarda só a versão anterior (`.bak`) de cada arquivo de dados (teste existente portado);
  - não há `.bak` soltos fora das pastas de dados das etapas (FR-029);
  - a suíte sem rede passa.

**Checkpoint**: regra de duas cópias e duas versões automatizada.

---

## Phase 9: Polish & fechamento

**Purpose**: documentação no estado final, limpeza do layout antigo, troca das specs e validação final (research R1, fase 7).

- [X] T072 [P] Escrever `plan.md` e `data-model.md` de cada spec nova em `specs/009-reorganizacao-pipeline/novas-specs/`, conforme o código final: módulos, artefatos e decisões técnicas reunidas das `research.md` das specs antigas, como a convenção de hora da hidrologia, a ponderação do DISPF, a fórmula da TEIFa e da TEIP e a paleta das figuras. Copiar:
  - `contracts/cli-etapas.md`, com a seção do comando de cada etapa, para o `contracts/` de cada spec;
  - `contracts/perfil-usina.md` para `001-coleta-dados/contracts/`.
- [X] T073 [P] Reescrever `README.md` no estado final, sem o histórico de mudanças (FR-035 e FR-026):
  - fluxo de cinco etapas e comandos (`python -m src ...`);
  - estrutura de pastas;
  - perfil e guia curto para incluir uma usina;
  - política de cópias e versões;
  - testes sem rede;
  - códigos de saída.
- [X] T074 Gerar o inventário final do layout antigo e acrescentá-lo a `specs/009-reorganizacao-pipeline/inventario-limpeza.md`: `data/processed/`, arquivos soltos de `reports/` (fora de `reports/sao_domingos/`) e sobras. Apresentar ao usuário e aplicar só o aprovado (SC-008).
- [X] T075 Validar todos os cenários de `specs/009-reorganizacao-pipeline/quickstart.md` (1 a 8) e registrar os resultados em "Registro de execução" deste arquivo.
- [ ] T076 Pedir ao usuário a aprovação para trocar as specs de `specs/` (FR-019) e sugerir um commit antes, para que a 009 e as antigas fiquem no histórico. Com a aprovação:
  - mover as cinco specs de `specs/009-reorganizacao-pipeline/novas-specs/` para `specs/`;
  - excluir `specs/001-ons-coleta-sao-domingos/` a `specs/008-relatorio-enxuto/` e `specs/009-reorganizacao-pipeline/`;
  - apontar `.specify/feature.json` para `specs/005-geracao-relatorio`;
  - conferir que `specs/` tem exatamente cinco pastas (SC-003).
- [ ] T077 Atualizar a memória do projeto (`memory/project-sao-domingos-fiscalizacao.md` e `memory/MEMORY.md`): estrutura nova, comandos, perfil, regra de duas cópias e governança das mudanças pela spec da etapa.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: sem dependências.
- **Phase 2 (US6)**: depende da Phase 1. Entrega primeiro, pela fiscalização.
- **Phase 3 (US5)**: depende da Phase 1. É independente das demais e pode correr junto com a Phase 2. A T015 pode ir na mesma rodada de aprovação da T013.
- **Phase 4 (US2)**: depende da Phase 2, porque as specs novas já descrevem a conclusão. A T026 libera o gate constitucional.
- **Phase 5 (Foundational)**:
  - depende da aprovação da conclusão (T013), para a linha de base, e da T026, por causa do gate (princípios V e VI);
  - bloqueia as US1, US3 e US4.
- **Phase 6 (US1)**: depende da Phase 5.
- **Phase 7 (US3)**: depende da US1, porque os módulos já precisam estar no layout novo.
- **Phase 8 (US4)**: depende da Phase 5 (`src/comum/`) e da T038 (`src/coleta/catalogo.py`). Pode correr junto com a Phase 7.
- **Phase 9 (Polish)**: depende de todas as histórias.

### User Story Dependencies

- **US6 (P1)**: independente; só exige o código atual.
- **US5 (P3)**: independente; o inventário final fica na Phase 9.
- **US2 (P1)**: depende do conteúdo da US6, para as specs novas.
- **US1 (P1)**: depende da Phase 5 (perfil, linha de base, comparação e `src/comum/`).
- **US3 (P2)**: depende da US1.
- **US4 (P2)**: depende da Phase 5 e da T038.

### Within Each User Story

- Testes antes, falhando, e depois a implementação.
- Na US1, cada etapa é conferida contra o fluxo antigo antes de passar para a próxima: T043 (coleta), T048 (tratamento), T053 (análises) e T059 (relatório completo).
- Os módulos antigos só saem na T060.
- Aprovações do usuário: T013, T015, T025, T074 e T076. Nenhuma exclusão ou troca de spec acontece antes da aprovação correspondente.

### Parallel Opportunities

- T004 e T005 (testes da US6); T009, T010 e T011 (apresentação da conclusão em arquivos diferentes).
- T014, que corre junto com a Phase 2.
- T018 a T023 (rascunho da constituição e as cinco specs, em arquivos diferentes).
- T029 e T030 (comparação e testes do perfil).
- T035 e T036; T049 (testes da conferência).
- T061, T062 e T063; T067 e T068; Phases 7 e 8.
- T072 e T073.

---

## Parallel Example: User Story 2

```text
Task: "T018 Rascunho da constituição 2.0.0 em specs/009-reorganizacao-pipeline/constituicao-rascunho.md"
Task: "T019 Spec da coleta em specs/009-reorganizacao-pipeline/novas-specs/001-coleta-dados/spec.md"
Task: "T020 Spec do tratamento em specs/009-reorganizacao-pipeline/novas-specs/002-tratamento-dados/spec.md"
Task: "T021 Spec da conferência em specs/009-reorganizacao-pipeline/novas-specs/003-conferencia/spec.md"
Task: "T022 Spec das análises em specs/009-reorganizacao-pipeline/novas-specs/004-analises/spec.md"
Task: "T023 Spec do relatório em specs/009-reorganizacao-pipeline/novas-specs/005-geracao-relatorio/spec.md"
```

## Parallel Example: User Story 6

```text
Task: "T004 Testes das regras C1 a C11 em tests/test_conclusao.py"
Task: "T005 Testes de estrutura, Markdown, PDF e planilha em tests/test_estrutura_relatorio.py"
# depois de T006 a T008:
Task: "T009 Markdown, planilha e nota em src/analyzer.py"
Task: "T010 Seção da conclusão em src/pdf_generator.py"
Task: "T011 Aba CONCLUSAO no mapa de fontes em src/fontes_relatorio.py"
```

---

## Implementation Strategy

### Primeira entrega: conclusão para a fiscalização

1. Phase 1 (cópias).
2. Phase 2 (US6): conclusão no relatório atual.
3. **PARAR E VALIDAR**: aprovação do texto pelo usuário (T013).
4. O relatório com a conclusão está pronto para a fiscalização de 14 a 16/10/2026, mesmo que a reorganização continue depois.

### MVP da reorganização (US1)

1. Phases 3 e 4: limpeza aprovada; constituição e specs aprovadas.
2. Phase 5: linha de base, comparação e perfil.
3. Phase 6 (US1): fluxo de cinco etapas.
4. **PARAR E VALIDAR**: `comparar` = 0 (T059 e T060).

### Entrega incremental

1. US3 (outras usinas) e US4 (cópias), em paralelo.
2. Polish: documentação final, inventário do layout antigo e troca das specs, com aprovação.
3. Cada fase termina com a suíte sem rede e, a partir da Phase 5, com o `comparar` = 0. O relatório da São Domingos fica reproduzível em todo ponto de parada.

---

## Notes

- [P] = arquivos diferentes, sem dependência pendente.
- Os commits ficam com o usuário. Sugerir commit nos pontos de controle, principalmente antes da T076.
- Nenhum download novo: as validações usam `--sem-portal`.
- Os scripts de apoio ficam no scratchpad. O que precisar durar vira código em `src/` com testes, como a comparação e a cópia de segurança.

---

## Registro de execução

### 07/10/2026 — Phase 1 (preparação)

- **Projeto**: `.gitignore` ganhou `.venv/`, `.DS_Store` e `*.tmp`. O arquivo não terminava em quebra de linha, e a primeira gravação colou `.venv/` em `*.doc`; foi corrigido na hora e conferido com `git check-ignore`.
- **T001**: cópia `_backup_2026-10-07_antes_conclusao/` com 247 arquivos (16,0 MB), cada um conferido por SHA-256 contra a origem; `copia.json`, `LEIA-ME.txt` e `conftest.py` gravados.
- **T002**: excluídas as dez cópias de 02 a 06/10/2026 (FR-028) e `_backup_2026-10-07_antes_revisao008` (FR-027), com 101,5 MB liberados. Ficaram `_backup_2026-10-07_antes_conclusao/` e `_backup_2026-10-07_antes_figuras/`.
- **T003**, linha de base antes da conclusão:
  - 244 testes aprovados sem rede (58 s), sem alterar nenhum dos 128 arquivos vigiados;
  - PDF com 29 páginas e planilha com 57 abas;
  - SHA-256 das figuras (16 primeiros caracteres): 01 `bbebd29dc1cd3289`, 02 `460c95479cfd44f8`, 03 `c7e627bf8a15c470`, 04 `0956b20eb0d6dbf4`, 05 `065a008cefc01244`, 06 `5a76334c166a9fa5`, 07 `f5e336924fd8135a`, 08 `a000b0bfb69fb6f6`.

### 07/10/2026 — Phase 2 (US6, conclusão) e inventário da Phase 3

- **T004, T005**: testes da conclusão.
  - `tests/test_conclusao.py` tem 15 testes: as regras C1 a C11 disparando e não disparando, a ordem e o limite por lista, a linguagem de indício e a regra de não repetir as constatações.
  - `test_conclusao_no_relatorio` (em `tests/test_estrutura_relatorio.py`) cobre a seção antes das notas no PDF, no Markdown e no sumário, a aba CONCLUSAO, a linha da FONTES e o item das notas.
  - O teste de apresentação usa as bases sintéticas completas (`_completo`), com números que disparam as quatro listas. Os resultados montados só para as regras não têm dados para as figuras.
- **T006**: dez limiares e o máximo de itens em `src/config.py` (`LIMIAR_CONCLUSAO_*` e `MAXIMO_ITENS_CONCLUSAO`).
- **T007**: em `src/analyzer.py`:
  - as regras `_regra_c1` a `_regra_c11` e `montar_conclusao`, guardada em `res.conclusao`;
  - `listas_conclusao`, com o título da lista, até cinco itens e as seções pelo número;
  - `tabela_conclusao` e `nota_conclusao`.
- **T008 a T011**:
  - seção `conclusao` em `src/estrutura_relatorio.py`;
  - Markdown com a frase de abertura e as quatro listas;
  - aba CONCLUSAO logo após a CONSTATACOES;
  - item "Conclusão:" nas notas, com as regras C1 a C11 e os limiares;
  - `_secao_conclusao` no PDF, com o título junto do bloco;
  - CONCLUSAO como aba calculada em `src/fontes_relatorio.py`.
- **T012**: 260 testes aprovados sem rede. Conferência em `scratchpad/t012_validar.py`:
  - **Itens**: 19 (5, 4, 5 e 5), todos com regra e seção e sem termos de avaliação.
  - **UG2**: aparece em "Possíveis problemas", com a limitação forçada em 78 dos 80 meses e 91% da TEIFa de ago/2026.
  - **Página**: a conclusão inteira fica na página 27.
  - **Não regressão**: o corpo das 15 seções anteriores, a capa, as 56 abas anteriores e as 8 figuras são idênticos aos da cópia da T001. As páginas do PDF diferem só no total do rodapé.
  - **Redação**: os modelos foram ajustados para não terminar em dois parênteses seguidos, como "(… 13 h) (seção 9)".
  - **Paginação**: a última página da versão aprovada já estava cheia, e o item novo das notas empurrava a última linha da tabela de parâmetros para uma 31ª página quase vazia.
    - As larguras das colunas dessa tabela passaram de 60/200/110/60/340 para 55/190/170/50/305. A coluna "Valor" leva as descrições dos conjuntos de dados, e a "Origem" continua cabendo a maior URL.
    - A tabela caiu de 876 para cerca de 725 pt, e o PDF ficou com 30 páginas (29 mais a da conclusão). Só a disposição mudou; o texto é o mesmo.
- **T014**: `inventario-limpeza.md`, com 26 itens. Se tudo for aprovado, 209,9 MB são excluídos e 165,8 MB movidos.
  - `Docs_usina.rar`: os 23 arquivos têm o mesmo SHA-256 dos PDFs soltos. O .rar foi lido em sequência, sem extrair para o disco.
  - Dicionário da raiz: idêntico byte a byte ao baixado.
  - `.bak` soltos: 64 fora de `data/processed/`.
  - Duas cópias idênticas do Anexo 6 (outorga).
- **Aguardando o usuário**:
  - T013: aprovação do texto da conclusão e dos limiares;
  - T015: decisão de cada item do inventário.

### 07/10/2026 — Aprovações (T013, T015) e Phase 3 (US5, limpeza)

- **T013**: o usuário aprovou o texto da conclusão e o catálogo de limiares sem ajustes ("aprovo os textos de conclusão"). O relatório com a conclusão é a versão de referência para a fiscalização.
- **T015**: o usuário aprovou o inventário inteiro como proposto ("aprovo o inventário"). A decisão está na última coluna de `inventario-limpeza.md`.
- **T016**: aplicação registrada na seção "Aplicação" do inventário.
  - 76 exclusões (209,9 MB) e 35 movimentações (165,8 MB), cada uma conferida por SHA-256 no destino.
  - Os documentos foram para `usinas/sao_domingos/documentos/` (25) e `referencias/` (10).
  - O dicionário da raiz saiu depois de `DATA_DICTIONARY_JSON` passar a apontar para `data/raw/_dicionarios/`, com `tests/test_validator.py` aprovado antes.
  - O README perdeu a linha da versão anterior dos relatórios. A seção de cópias de segurança passou ao estado atual: duas cópias, e `.bak` só em `data/processed/`. Ganhou a seção dos documentos fora do git.
  - **Correção do inventário**: os `.bak` não estavam no git, que os ignora. Das 64 cópias, 61 continuam em `_backup_2026-10-07_antes_conclusao/`, inclusive o código de 30/09 anterior à auditoria. As outras três eram versões antigas do README e do `requirements.txt`.
- **T017**: `.gitignore` com `usinas/*/documentos/` e `referencias/`, no lugar de `Docs_usina/`. Conferência em `scratchpad/t016_limpeza.py`:
  - SC-008 cumprido: cada exclusão consta do inventário aprovado e nenhum documento foi excluído sem aprovação;
  - `data/raw/` intacto: 1.071 arquivos com o mesmo tamanho e a mesma data;
  - nenhum `.bak` solto fora de `data/processed/`;
  - 260 testes aprovados sem rede;
  - relatório regerado igual ao de antes da limpeza: Markdown, 58 abas, 8 figuras e texto do PDF página a página.

### 07/10/2026 — Phase 4 (US2): rascunhos da constituição, das cinco specs e do mapeamento

- **T018**: `constituicao-rascunho.md`, versão 2.0.0.
  - Sete princípios, requisitos técnicos, qualidade e governança.
  - Sem histórico de emendas e sem valores de usina.
  - Duas redações acertadas na reconciliação: o princípio V passou a dizer que cada spec declara o que um registro sinalizado deixa de alimentar; o VI, que a meta não atingida para o fluxo completo.
- **T019 a T023**: as cinco specs em `novas-specs/`, escritas em paralelo a partir de um roteiro comum, cada uma com o checklist completo:
  - Coleta: 6 US, 48 FR e 14 SC;
  - Tratamento: 6 US, 34 FR e 10 SC;
  - Conferência: 4 US, 17 FR e 6 SC;
  - Análises: 6 US, 51 FR e 10 SC;
  - Geração do relatório: 8 US, 40 FR e 12 SC.
- **Reconciliação entre as specs**:
  - O código 3 grava a etapa como `concluida`: o `completo` para, e a etapa seguinte, executada à parte, aceita a anterior e omite os cruzamentos hidrológicos.
  - A Coleta grava as auditorias que as outras etapas usam: CEG do cadastro, arquivos dos indicadores, período e data de publicação por arquivo, marca de valor não numérico e um dia por linha na programação.
  - O perfil ganhou `usina.nome_curto` e cinco textos opcionais, para que os trechos próprios da usina saiam do código sem mudar o relatório.
  - A tabela de parâmetros ficou só na Geração do relatório.
  - As abas de auditoria da planilha mantêm as colunas atuais.
  - A conferência linha a linha do id ONS nos indicadores por unidade foi checada nos dados: as 214 linhas da São Domingos têm MSUHSD, então nada muda.
- **T024**: `mapeamento-specs.md`, gerado por `scratchpad/t024_mapa.py` a partir dos mapeamentos parciais.
  - Os 280 itens das specs 001 a 009 têm destino, em 412 linhas: em vigor 181, em vigor em parte 194, ampliados 2, superados 21 (mais 1 em parte), cumpridos 7 (mais 1 em parte) e a cumprir no fechamento 5.
  - Nenhuma spec nova remete a specs antigas, revisões ou emendas.
- **Pendente (T025)**: aprovação do usuário, com as decisões listadas na apresentação. A principal é reformular, antes da linha de base, os dois textos do relatório que citam caminhos do código.

### 07/10/2026 — Aprovação da Phase 4 (T025)

- **Aprovações**: o usuário aprovou a constituição e o mapeamento ("Aprovo a constitution e mapeamento") e respondeu às três decisões apresentadas. As cinco specs foram tomadas como aprovadas com o mapeamento e as decisões 2 e 3, e continuam editáveis até o fechamento (T076).
- **Decisão 1 (relatório "idêntico")**: o que deve se manter é o conteúdo do relatório (tabelas, figuras, identificação e conclusão), e mudança só de caminho não é problema.
  - Os dois textos que citam caminhos do código passam a ter redação neutra na T027, antes da cópia de referência.
  - Assim, a comparação automática continua exata, com só a data de geração diferente.
  - Registrado na spec 005 (FR-021, FR-022, SC-001, Assumptions e Decisões do usuário) e na T027.
- **Decisão 2**: aprovados os campos novos do perfil: `usina.nome_curto` e cinco textos opcionais com os trechos próprios da usina.
- **Decisão 3**: aprovadas as mudanças de comportamento que não afetam a São Domingos:
  - códigos 1 e 2 da coleta;
  - código 1 para a R1;
  - código 3 com a etapa concluída;
  - id ONS conferido nos indicadores por unidade;
  - constatação da mudança de classificação omitida quando não há mudança;
  - legenda do DISPF "não feita" sem o conjunto das horas.

- **T026**: constituição 2.0.0 gravada em `.specify/memory/constitution.md` com `/speckit-constitution`.
  - Ratificação em 2026-09-30 e última revisão em 2026-10-07.
  - O relatório de impacto gerado pela skill foi removido em seguida.
  - O arquivo é idêntico ao rascunho aprovado e não tem "Emenda", "SYNC IMPACT" nem valores da São Domingos (153, MSUHSD, o nome da usina, 028761, PRUHSD, PNUHSD).
  - Sem hooks registrados em `.specify/extensions.yml`. O gate da fase 5 está liberado.

### 07/10/2026 — Phase 5 (base técnica da reorganização)

- **T027**: opção `--data-geracao "DD/MM/AAAA HH:MM"` em `src/analyzer.py` (função `ler_data_geracao`, `executar_pipeline_analise`, Markdown) e em `src/pdf_generator.py` (capa e linha de comando).
  - Com a data fixa, o PDF é montado com `rl_config.invariant`, restaurado ao fim da montagem.
  - Dois testes novos em `tests/test_pdf_generator.py`: PDFs idênticos byte a byte com a mesma data; data no Markdown; formato inválido recusado.
  - Na mesma tarefa, os dois textos que citavam caminhos ficaram sem caminho (decisão do usuário em 07/10/2026): "Parâmetro de análise" (15 células da aba PARAMETROS e as linhas da tabela) e "(coluna qualidade da série horária tratada)".
  - Conferido contra o relatório anterior: o resto não mudou (Markdown, 58 abas e 30 páginas do PDF).
- **T028**: cópia `_backup_2026-10-07_antes_reorganizacao/`, com 186 arquivos conferidos e a linha de base em `linha_de_base/`.
  - A linha de base tem 12 arquivos e foi gerada com `--data-geracao "07/10/2026 08:53"`; o SHA-256 de cada um está em `linha_de_base.json`.
  - Os 11 arquivos que não são planilha saíram idênticos, byte a byte, aos gerados antes com a mesma data, o que prova a reprodutibilidade.
  - A cópia mais antiga (`antes_figuras`) foi excluída depois da conferência; ficaram `antes_conclusao` e `antes_reorganizacao`.
- **T029**: `src/comum/comparacao.py` (`comparar` e `python -m src.comum.comparacao <atual> <referencia>`, com códigos 0, 6 e 1). Compara byte a byte o PDF, o Markdown, o CSV e as figuras, e a planilha célula a célula na mesma ordem de abas; o `etapa.json` fica fora. Sete testes em `tests/comum/test_comparacao.py`.
- **T030 e T031**: `usinas/sao_domingos/perfil.toml`, com os campos do contrato, mais `usina.nome_curto` e os cinco textos opcionais aprovados.
  - `src/comum/perfil.py` lê o perfil com `tomllib`, valida, junta todos os problemas em `PerfilInvalido` (código 4) e calcula os valores derivados.
  - Vinte testes em `tests/comum/test_perfil.py`.
- **T032**: `src/comum/regras.py` (regras gerais, inclusive os limiares da conclusão, `RAZAO_DIURNA_RELEVANTE` e `TAMANHO_FIGURA_PADRONIZADA`) e `src/comum/caminhos.py` (pastas compartilhadas, `pasta_etapa`, `pasta_relatorio` e nomes de arquivo por etapa).
  - `src/config.py` virou ponte: reexporta as regras e tira os valores da usina do perfil. Os 130 nomes que ele exportava têm o mesmo valor e o mesmo tipo de antes.
  - `FAIXAS_GERACAO_INTERMEDIARIAS_MW` saiu do `analyzer` para o perfil.
- **T033**: `logger.py`, `formatacao.py`, `persistencia.py` e `models.py` foram para `src/comum/` (este último como `modelos.py`), com `git mv`; os imports foram atualizados em 31 arquivos. Os testes de persistência foram para `tests/comum/`.
- **T034**: 289 testes aprovados sem rede. O relatório regerado com a data fixa não tem nenhuma diferença da linha de base (`comparar`, código 0).

### 07/10/2026 — Phase 6 (US1): pipeline, linha de comando e Coleta de dados (T035 a T043; T067 e T069 antecipadas)

- **T035 e T036**: `tests/comum/test_pipeline.py` (manifesto da etapa, código 5 sem gravar nada, invalidação das seguintes e falha registrada) e `tests/integracao/test_cli.py` (comandos, `--usina` obrigatório, opções, opções retiradas, perfil inválido com código 4, mensagens do contrato e `completo` parando na primeira etapa com código diferente de 0).
- **T037**: pacotes `src/coleta/`, `src/tratamento/`, `src/conferencia/`, `src/analises/` e `src/relatorio/`, `src/pipeline.py` (ordem, `etapa.json` gravado de forma atômica, pré-requisito, códigos 0 a 6) e `src/__main__.py` (argparse do contrato, perfil validado antes de tudo).
- **T067 e T069 (antecipadas)**: `src/comum/copia_seguranca.py`, com `criar_copia(motivo, raiz)` ligado a `python -m src copia-seguranca --motivo <texto>`.
  - A cópia é conferida contra `copia.json` (SHA-256) e só depois as mais antigas são podadas até ficarem duas.
  - Em falha, a cópia incompleta é apagada e nenhuma outra é excluída.
  - Testes em `tests/comum/test_copia_seguranca.py`.
- **T038**: `collector.py` → `src/coleta/catalogo.py` e `dicionarios_ons.py` → `src/coleta/dicionarios.py` (`git mv`), sem a ponte `src.config`. O registro passa a `dicionarios.csv` na pasta da coleta; o fluxo antigo continua gravando o nome antigo em `data/processed/` até a T060. Testes em `tests/coleta/`.
- **T039**: `filter.py` e `consolidator.py` → `src/coleta/evt.py`, com a identificação recebida do perfil (sem valores padrão da usina). Testes `test_evt.py` e `test_auditoria_evt.py`.
- **T040**: `src/coleta/conjuntos.py`: descrições dos três conjuntos horários montadas com o perfil, seleção, sincronização (falha por arquivo), leitura numérica sem convenção de hora e sem juntar duplicatas, auditoria da extração com período, data de publicação e `obtido`. Os arquivos são lidos em ordem de publicação. Doze testes em `tests/coleta/test_conjuntos.py`.
- **T041**: `src/coleta/indicadores.py`, `programacao.py` e `cadastro.py`.
  - Indicadores: arquivos do período (ano) e únicos; nos indicadores por unidade, conferência pelo id ONS. Um só `indicadores_extraido.parquet`, com a coluna `conjunto`, que `separar_conjuntos` desfaz.
  - Programação: as linhas são pré-filtradas pelo código ou pelo estado com o pyarrow. Sem isso, a conferência por nome em todas as linhas levava cerca de 400 s; com o filtro, cerca de 20 s, praticamente o tempo do fluxo antigo. A auditoria passa a contar também as linhas só com a conferência e os valores inválidos.
  - Cadastro: a ficha sai sem as divergências (agora da Conferência) e com `linhas_ceg`.
  - Conferido no smoke test: os quatro conjuntos extraídos são iguais aos lidos pelo fluxo antigo; o tratamento antigo aplicado ao extraído novo reproduz as tabelas tratadas; a programação horária e a ficha também ficam iguais.
  - Vinte e um testes novos em `tests/coleta/`.
- **Auditoria da EVT (FR-046)**: quatro colunas acrescentadas no fim (`formato`, `data_publicacao`, `obtido` e `mensagem`); as dez anteriores continuam iguais e na mesma ordem.
- **T042**: `src/coleta/etapa.py` com `executar_coleta(perfil, sem_portal, forcar_download)`.
  - Ordem da FR-016; para no primeiro conjunto com falha (código 2) depois de gravar o que leu.
  - A EVT ganhou `sincronizar_evt`, com falha por arquivo (FR-026). Com `--sem-portal`, nada é consultado.
  - Os dicionários são obtidos só com o portal; o registro é sempre remontado a partir dos manifestos.
  - O resumo segue a FR-048, com as contagens de download tiradas dos manifestos.
- **T043**: `python -m src coleta --usina sao_domingos --sem-portal`: código 0 em 235 s. Conferido por `scratchpad/t043_validar_coleta.py`, com 19 verificações e nenhuma diferença:
  - `evt_extraido.csv` e `dicionarios.csv` idênticos, byte a byte, aos arquivos antigos;
  - `auditoria_evt.csv` igual à auditoria antiga, exceto `data_hora_processamento`;
  - contagens de indicadores, programação, disponibilidade, hidrologia, geração e cadastro iguais às auditorias antigas;
  - nenhum download, nenhum arquivo alterado em `data/raw/`; período de 28/08/2018 00:00 a 28/09/2026 23:00.

### 08/10/2026 — Phase 6 (US1): Tratamento de dados (T044 a T048)

- **T044**: `src/tratamento/series.py`, com a montagem das séries a partir da extração da Coleta.
  - Convenção de hora de início (`hora_de_inicio`, com o instante publicado guardado na hidrologia).
  - Uma hora por instante, a do arquivo publicado por último; as conflitantes são contadas em `duplicatas_conflitantes`.
  - Recorte do período, `listar_ausencias` e auditoria final (14 colunas, com `horas_usina`). A ordem dos arquivos vem da auditoria da Coleta.
  - `periodos_continuos` foi para `src/comum/periodos.py`.
  - Seis testes em `tests/tratamento/test_series.py`, que compõem a extração da Coleta com a montagem.
- **T045**: `src/tratamento/validacao.py` e `src/tratamento/evt.py`, copiados de `validator.py` e `processor.py`, que ficam como oráculo até a T060.
  - Os limites de R6 e R8, o nome e o `cod_usina` do relatório de validação vêm do perfil.
  - A aba da planilha tratada é o nome da usina normalizado (`UHE_SAO_DOMINGOS`).
  - Violação da R1 sai com código 1, sem gravar (decisão 3 da T025).
  - `tratar_evt` devolve o resumo e o período.
  - Vinte e quatro testes portados em `tests/tratamento/`.
- **T046**: `src/tratamento/indicadores.py` (`IndicadoresONS`, tratamento, recorte, potência nas horas, identidade HP; quatro CSV e `indicadores.xlsx` com cinco abas), `programacao.py` (`ProgramacaoONS`, base horária, dias ausentes, colunas da auditoria mostradas no relatório), `disponibilidade.py`, `hidrologia.py` (`limpos` e `nivel_implausivel` públicos, para a Conferência e as Análises) e `geracao.py`.
- **T047**: `src/tratamento/etapa.py`, com `executar_tratamento(perfil)`.
  - Lê só a pasta da Coleta e o dicionário da EVT.
  - O resumo segue a FR-033, com as gravações contadas por `registrar_gravacoes`, um registro opcional novo em `src/comum/persistencia.py`.
- **T048**: `python -m src tratamento --usina sao_domingos`: código 0 em 43 s. Conferido por `scratchpad/t048_validar_tratamento.py`:
  - os 21 arquivos de `tratamento/` são iguais aos de `data/processed/`: CSV, Markdown e Parquet byte a byte; `evt_tratado.xlsx` e as cinco abas de `indicadores.xlsx` célula a célula;
  - uma segunda execução deixa os 21 arquivos `INALTERADO`, sem cópia `.bak` (FR-034);
  - a suíte sem rede tem 397 testes aprovados.

### 08/10/2026 — Phase 6 (US1): Conferência (T049 e T050)

- **T049**: `tests/conferencia/test_conferencias.py`, com 16 testes:
  - testes portados de `conferir_geracao`, `conferir_com_evt`, `alinhar_com_evt`, `comparar_indicadores_e_horas` e `recalcular_taxas`;
  - divergências do cadastro com o perfil;
  - não aplicável com motivo sem a base, e tabela do recálculo registrada mesmo sem janela completa;
  - vazão negativa fora do alinhamento;
  - meta e meta atingida nas vazões;
  - etapa com código 3 abaixo da meta, sem `.bak` e com o CSV de execução anterior removido quando a conferência deixa de ser aplicável.
- **T050**: pacote `src/conferencia/`:
  - `resultado.py`: `ResultadoConferencia`, `nao_aplicavel`, `salvar_conferencias` e `carregar_conferencias`, com a versão do formato conferida na leitura;
  - `geracao.py`, `disponibilidade.py`, `vazoes.py`, `indicadores.py` (com `janela` e `peso` públicos, para a decomposição das taxas nas Análises) e `cadastro.py` (divergências com o perfil, no mesmo texto da ficha antiga);
  - `etapa.py`, com `executar_conferencia(perfil)`, que grava `conferencias.pkl` e oito CSV.
  - Na persistência: gravação sem cópia (`copia=False`) e `gravar_bytes`. Em `regras.py`: `JANELA_TAXAS_MESES` (60 meses).
  - `python -m src conferencia --usina sao_domingos`: código 0 em 2 s.
    - Resultados: geração e disponibilidade com 70.895 de 70.895 horas; vazões com 70.731 de 70.731 horas e a meta atingida; DISPF × horas com 4 de 160 meses-unidade divergentes; TEIFa e TEIP com 21 de 21 meses reproduzidos; cadastro sem divergência.
    - `vazoes.csv` e `dispf_horas.csv` são idênticos, byte a byte, ao alinhamento e às divergências antigos.
    - As tabelas e os resumos são iguais aos que a análise antiga calcula a partir de `data/processed/` (`scratchpad/t050_validar_conferencia.py`).

### 08/10/2026 — Phase 6 (US1): Análises (T051 a T053)

- **Perfil ativo**: `src/comum/perfil.py` ganhou `definir_perfil_ativo` e `perfil_ativo()`.
  - `src/pipeline.py` define o perfil antes de chamar a função da etapa e o limpa ao fim.
  - Nas Análises e no relatório, os valores da usina são lidos dele (ex.: `perfil_ativo().parametros.potencia_instalada_mw`), sem repassar o perfil a cada função.
  - Nos testes, uma fixture automática em `tests/conftest.py` ativa o perfil da São Domingos.
- **T051**: `src/analises/resultados.py`.
  - `ResultadosAnalise` com os campos atuais, mais `serie_diaria` e `vazoes_anuais` (dados das figuras 01 e 05). `conclusao` já existia desde a fase 2.
  - `parametros` e `fontes` passam a ser montados na Geração do relatório (spec das Análises, FR-042).
  - `salvar_resultados` e `carregar_resultados`, com a versão do formato conferida e sem cópia `.bak`.
- **T052**: `scratchpad/t052_divisor.py` divide `src/analyzer.py` e a parte de análise dos módulos `*_ons` pela árvore sintática.
  - Cada nó de topo tem um destino declarado.
  - Os valores da usina viram `perfil_ativo()...` só nos nomes do código.
  - Os imports são calculados, e os nomes que colidiriam são renomeados (`perfil_hidrologico`, `resumir_hidrologia`, `resumir_disponibilidade`).
  - Ajustes à mão em `scratchpad/t052_ajustes.py`:
    - as conferências entram prontas (geração, disponibilidade e recálculo das taxas);
    - `DESCRICAO_FAIXAS`, sem uso, foi removido;
    - o perfil foi passado às funções do Tratamento.
  - Módulos novos: `comum.py`, `cobertura.py`, `evt.py`, `indicadores.py` (com `decompor_taxas`), `programacao.py`, `disponibilidade.py`, `hidrologia.py`, `geracao.py`, `cadastro.py`, `constatacoes.py`, `conclusao.py` e `etapa.py`. O pyflakes não aponta nome indefinido.
  - Testes portados por `scratchpad/t052_portar_testes.py`:
    - `tests/analises/`: evt, conclusão, programação, disponibilidade, hidrologia, indicadores e resultados;
    - `tests/tratamento/` (casos que faltavam da T046): indicadores, programação e qualidade.
  - O teste do limite de itens por lista usa `listas_conclusao` (apresentação) e fica para a T056.
- **T053**: `src/analises/etapa.py`, com `analisar` (recebe as conferências) e `executar_analises(perfil)`.
  - `python -m src analises --usina sao_domingos`: código 0 em 4 s, com 17 constatações e 19 itens da conclusão (5/4/5/5) pelas regras C1 a C11.
  - `scratchpad/t053_validar_analises.py`: os 26 campos do `resultados.pkl` são iguais ao `ResultadosAnalise` do fluxo antigo, com tabelas de mesmo tipo (`assert_frame_equal` estrito).
    - Ficam de fora só `parametros` e `fontes`, que passaram ao relatório; a T059 os confere no relatório final.
  - Suíte sem rede: 456 testes aprovados.

### 08/10/2026 — Phase 6 (US1): Geração do relatório e fluxo completo (T054 a T059)

- **T054**: `src/relatorio/fontes.py` e `src/relatorio/estrutura.py`, copiados de `fontes_relatorio.py` e `estrutura_relatorio.py`, que ficam como oráculo até a T060.
  - Os identificadores da usina em `CONJUNTOS` viraram modelos (`"cod_usina {cod_usina}"`), preenchidos com o perfil ativo por `identificador_da_usina`.
  - As regras e os caminhos vêm de `src.comum`.
  - Testes portados para `tests/relatorio/test_fontes.py` e `test_estrutura.py`.
- **T055**: `src/relatorio/figuras.py`, gerado pelo divisor.
  - As figuras 01 e 05 desenham a partir de `res.serie_diaria` e `res.vazoes_anuais`, e `gerar_graficos(res, pasta, dpi)` não recebe mais a base horária.
  - As 8 figuras saem idênticas, byte a byte, às da linha de base.
- **T056**: `src/relatorio/conteudo.py`, `planilha.py`, `markdown.py` e `parametros.py`, gerados pelo divisor, e `pdf.py`, convertido de `pdf_generator.py` por `scratchpad/t056_relatorio.py`.
  - Os caminhos de saída passam a ser obrigatórios.
  - `faixa_produtividade` recebe o perfil.
  - Os rótulos curtos das faixas de afluência viram uma função, porque dependem do perfil.
  - Ajustes reproduzíveis em `scratchpad/t056_relatorio_fim.py`.
  - Testes portados por `scratchpad/t056_portar_testes.py` para `tests/relatorio/`: `test_complementar.py`, `test_pdf.py` e `test_markdown.py`.
    - O apoio `tests/relatorio/apoio.py` (`analisar_com_bases`) monta as conferências a partir das mesmas bases sintéticas e completa parâmetros e fontes.
    - O `analisar` volta a avaliar as regras R1 a R9 quando a validação do Tratamento não é informada (chamada direta, nos testes).
- **T057**: `src/relatorio/etapa.py`.
  - `completar_resultados`: tabela de parâmetros e origem dos dados, montadas no relatório (FR-042).
  - `executar_relatorio(perfil, data_geracao)` grava `reports/<slug>/`; o resumo traz a data de geração, 17 seções, 30 páginas, 8 figuras e 58 abas.
  - **Decisão técnica (comparar)**: a primeira comparação apontou 2 células da aba `ONS_DIVERGENCIAS` diferentes no 17º algarismo. No fluxo antigo, essas divergências passavam por um CSV, e o leitor padrão do pandas perde o último algarismo de alguns números; no novo, a análise recebe o valor exato da Conferência.
    - O `comparar` passou a considerar iguais as células numéricas que coincidem até a 12ª casa relativa.
    - FR-040 da spec da Geração do relatório atualizada; teste em `tests/comum/test_comparacao.py`.
    - PDF, Markdown, CSV e figuras continuam comparados byte a byte, e são idênticos.
- **T058**: `completo` já ligado em `src/pipeline.py` (T037); passa pelas T035 e T036.
- **T059**: validação do fluxo:
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: código 0 em 314 s (coleta 249 s, tratamento 40 s, conferência 1 s, análises 2 s, relatório 20 s); o único aviso é a sinalização da hidrologia, a mesma de antes;
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-07_antes_reorganizacao/linha_de_base`: nenhuma diferença;
  - `python -m src relatorio --usina sao_domingos` sozinho: código 0;
  - Análises com a Conferência desatualizada, depois de refazer o Tratamento: código 5, com a mensagem do contrato, sem gravar nada;
  - refeitas as etapas, `comparar` continua sem diferença;
  - suíte sem rede: 546 testes aprovados.

### 08/10/2026 — Phase 6 (US1): remoção do fluxo antigo (T060)

- **Removidos** (`git rm`; o conteúdo continua no histórico e em `_backup_2026-10-07_antes_reorganizacao`):
  - módulos: `src/main.py`, `analyzer.py`, `pdf_generator.py`, `processor.py`, `validator.py`, `conjuntos_ons.py`, `indicadores_ons.py`, `programacao_ons.py`, `disponibilidade_ons.py`, `hidrologia_ons.py`, `geracao_ons.py`, `cadastro_ons.py`, `fontes_relatorio.py` e `estrutura_relatorio.py`;
  - a ponte `src/config.py`;
  - as suítes antigas de `tests/`, `tests/integration/` e a pasta vazia `tests/unit/`.
  - `collector.py`, `filter.py`, `consolidator.py` e `dicionarios_ons.py` já tinham ido para `src/coleta/` nas T038 e T039.
- **Ponto de entrada único**:
  - `src/comum/comparacao.py` troca a linha de comando própria por `executar_comparacao(atual, referencia)`, chamada por `python -m src comparar`;
  - `src/coleta/dicionarios.py` perde `main`, `executar_dicionarios_ons`, `atualizar_dicionarios` e os valores padrão do fluxo antigo; o registro é sempre `dicionarios.csv` da pasta informada.
- **Logger**: `LOGGERS_PIPELINE` = `pipeline`, `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio` e `persistencia`.
- **Conformidade**: `tests/comum/test_conformidade.py` substitui o antigo. Ele confere:
  - figuras em seaborn;
  - nível de log aplicado pela linha de comando a todos os loggers;
  - loggers do código declarados em `LOGGERS_PIPELINE`;
  - nenhum `__main__`/argparse fora de `src/__main__.py`;
  - `requirements.txt` igual aos imports;
  - Coleta, Tratamento, Conferência e Análises gravando dados só pela persistência.
- Testes que usavam a API antiga foram ajustados: dicionários, perfil (sem a ponte), gravadores da persistência e um import do teste de estrutura.
- **Validação**:
  - suíte sem rede: 342 testes aprovados; o pyflakes não aponta problema em `src/`;
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: código 0 em 322 s;
  - `comparar` com a linha de base: nenhuma diferença.

### 08/10/2026 — Phase 7 (US3): outras usinas (T061 a T066)

- **T061**: `tests/fixtures/usina_ficticia/perfil.toml` e `tests/fixtures/brutos_ficticios.py`.
  - Perfil: UHE Fictícia (GO), três unidades de 30 MW, Francis, identificadores próprios (`cod_usina` 999, "USINA FICTICIA", `GOUHFI`, `PRUHFI`, `PNUHFI`, CEG `UHE.PH.GO.000001-0.01`), sem os textos opcionais.
  - Gerador de jan e fev/2024 de EVT, indicadores e taxas, disponibilidade, hidrologia (fim de hora), geração e cadastro, com o dicionário da EVT.
  - Cada conjunto traz um homônimo em que só o identificador confere. Não há programação diária.
- **T062**: `tests/integracao/test_usina_ficticia.py` executa `python -m src completo --usina usina_ficticia --sem-portal` sobre pastas temporárias e confere:
  - as cinco etapas concluídas e o relatório completo, com 8 figuras;
  - nenhum "São Domingos", "SAO DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD" ou "028761" no Markdown, nos parágrafos do PDF e nos bytes do PDF;
  - "entre uma e três unidades" e o código `ENTRE_UMA_E_TRES_UNIDADES` na aba `HID_FAIXAS_AFLUENCIA`;
  - homônimos fora dos extraídos e contados nas auditorias e na ficha;
  - 16 seções, sem a de programação.
- **T063**: `tests/comum/test_literais.py`: nenhum "Domingos", "DOMINGOS", "MSUHSD", "PRUHSD", "PNUHSD", "028761", "Kaplan" ou "AGEPAN" em `src/`; esses valores estão no perfil.
- **T064**: faixas de afluência para N unidades.
  - `numero_por_extenso` em `src/comum/formatacao.py` (2 → "duas").
  - Em `src/analises/hidrologia.py`, `entre_unidades()` e `faixas_afluencia()` substituem `ENTRE_UMA_E_DUAS_UNIDADES` e `FAIXAS_AFLUENCIA`.
  - **Decisão técnica**: o código da faixa intermediária é montado com o número de unidades do perfil (`ENTRE_UMA_E_<N por extenso>_UNIDADES`). Esse código aparece como dado nas abas da hidrologia; um código fixo e neutro mudaria a planilha da São Domingos. Com duas unidades, ele continua `ENTRE_UMA_E_DUAS_UNIDADES`, e o relatório não muda.
  - Textos com N: constatação ("entre uma e {N} unidades"), notas ("nas {N}") e legenda da figura 07 ("cabia nas {N}").
- **T065**: textos do relatório tirados do perfil.
  - Títulos do Markdown e do PDF, cabeçalho e metadados do PDF com `usina.nome`; homônimos do cadastro com `usina.nome_curto`.
  - Os cinco textos opcionais do perfil substituem os trechos fixos, nos modelos da FR-006 da spec da Coleta: IP e TEIF, descrição do vertimento mínimo e ressalva do volume útil nas notas; origem do início da operação e do vertimento mínimo na tabela de parâmetros. Sem o campo, o trecho é omitido.
  - User-Agent da coleta e docstring do pacote sem o nome da usina.
  - Os caminhos de `data/raw` passam a ser lidos na hora da chamada: datas de obtenção nas Análises e nas fontes do relatório, e o dicionário da EVT (`caminhos.dicionario_evt()`). Assim outra pasta de dados funciona, como no teste da usina fictícia.
  - `faixas_geracao_mw` e `vertimento_minimo_m3s` já vinham do perfil desde a T052.
- **T066**: suíte sem rede com 356 testes aprovados (T061 a T063 passam); o pyflakes não aponta problema em `src/`. Análises e Relatório da São Domingos refeitos: o `comparar` com a linha de base não acusa diferença.

### 08/10/2026 — Phase 8 (US4): duas versões anteriores (T068, T070 e T071)

- **T068**: `tests/coleta/test_versoes_anteriores.py`, com 10 testes:
  - até duas versões anteriores, nada é excluído;
  - na terceira, a mais antiga é excluída e a exclusão fica no manifesto (`versoes_excluidas`: arquivo, data de publicação, SHA-256 e `excluido_em_utc`);
  - exclusões sucessivas ficam todas registradas;
  - conteúdo idêntico não gera versão nem exclui;
  - falha no download não exclui nada;
  - a poda não toca versões de outros arquivos;
  - um registro com mais de duas versões, de antes da regra, é ajustado na próxima preservação;
  - um registro adulterado no manifesto não leva à exclusão de arquivo fora de `_versoes_anteriores/`;
  - os dicionários também ficam com duas versões, e o registro `dicionarios.csv` mostra 2.
- **T070**: poda das versões anteriores.
  - `MAXIMO_VERSOES_ANTERIORES = 2` em `src/comum/regras.py`.
  - Em `src/coleta/catalogo.py`, `_register_version` recebe a pasta no download e, acima do limite, chama `_excluir_versoes`. Essa função usa só o nome registrado, dentro de `_versoes_anteriores/`, e devolve o registro de cada exclusão.
  - A poda acontece depois de a nova versão substituir a corrente. Os dicionários passam pelo mesmo `download_resource`, então a regra vale para eles também (FR-029 da spec da Coleta).
  - Estado atual da base: uma única versão anterior (`modalidade_usina/_versoes_anteriores/MODALIDADE_USINA__pub_20261004T220450.csv`), dentro do limite.
  - O teste `test_republicacoes_sucessivas_preservam_todas_as_versoes` passou a se chamar `..._preservam_as_versoes_ate_o_limite`.
- **T071**: conferência dos `.bak`.
  - `src/comum/persistencia.py` guarda só a versão imediatamente anterior. Novo teste com três gravações diferentes: o `.bak` é a penúltima versão e a pasta tem só o arquivo e o `.bak`.
  - Conferência e Análises gravam sem `.bak` (`copia=False`), e o Relatório não usa a persistência; os testes de cada etapa já cobrem isso.
  - Novo teste em `tests/comum/test_conformidade.py`: nenhum `.bak` em `src/`, `tests/`, `specs/`, `.specify/`, `usinas/`, `reports/` e na raiz.
  - Nas pastas de dados há só `data/usinas/sao_domingos/coleta/auditoria_evt.csv.bak`, da Coleta (correto), e os 10 `.bak` de `data/processed/`, layout antigo que entra no inventário da T074.
  - Suíte sem rede: 368 testes aprovados. O pyflakes não aponta problema em `src/`; em `tests/` restam só as fixtures importadas de propósito em `tests/relatorio/test_markdown.py`. Um import sem uso foi retirado de `tests/coleta/test_dicionarios.py`.

### 08/10/2026 — Phase 9: README e limpeza final (T073 e T074)

- **T073**: `README.md` reescrito no estado final, sem o histórico de mudanças, que fica no git. Seções:
  - visão geral, com o perfil e o Spec Kit;
  - fluxo de cinco etapas, com comando, saída e spec de cada uma;
  - conjuntos do ONS, com o identificador e a conferência de cada um;
  - instalação (Python 3.11 ou mais recente, por causa do `tomllib`);
  - como executar: comandos, opções, ferramentas e códigos de saída 0 a 6;
  - estrutura de pastas;
  - perfil da usina e guia para incluir uma usina: preencher o perfil, onde obter cada identificador e parâmetro, executar e conferir a auditoria de identificação;
  - cópias de segurança, versões e `.bak`;
  - testes e metodologia resumida.

  O README já descreve `specs/` depois da troca das specs (T076). Ajustes junto:
  - `requirements.txt`: o cabeçalho cita `tests/comum/test_conformidade.py`;
  - `src/comum/persistencia.py`: docstrings sem `data/processed/`.
- **Referências às specs antigas no código**: comentários e docstrings de `src/` e `tests/` citavam as specs 004 a 009, tarefas (T0xx) e versões antigas da constituição.
  - Agora citam as specs por etapa pelo nome (por exemplo, "spec da Coleta de dados, FR-029"), com os destinos do `mapeamento-specs.md`. Assim continuam válidas antes e depois da troca das pastas.
  - Foram 100 trocas em 34 arquivos.
  - As docstrings das Análises que citavam a US3 ou a US4 para disponibilidade, hidrologia, programação e indicadores passaram para a US2 da spec das Análises.
  - Suíte: 368 testes aprovados; o pyflakes não aponta problema em `src/`.
- **T074**: inventário final acrescentado a `inventario-limpeza.md` (itens 27 e 28) e aprovado pelo usuário em 08/10/2026.
  - **Item 27**: `data/processed/`, 30 arquivos e 10 `.bak` (76,0 MB), excluído. Antes da exclusão, cada arquivo foi conferido contra o equivalente em `data/usinas/sao_domingos/`: 20 são idênticos byte a byte e 10 trazem os mesmos dados, reorganizados entre as etapas (tabela no inventário).
  - **Item 28**: relatório solto em `reports/` (6,7 MB), excluído. O PDF ficou fora do git; os 11 arquivos rastreados saíram com `git rm`. O `comparar` com a linha de base não acusava diferença nesses arquivos.
  - **Estado final**: `data/` tem só `raw/` e `usinas/`, e `reports/` tem só `sao_domingos/`.

### 08/10/2026 — T075: validação dos cenários do quickstart

| Cenário | Resultado |
|---|---|
| 1. Testes sem rede | Suíte aprovada (368 testes antes da revisão da T072; 384 depois). Uma fotografia de `data/`, `reports/` e `usinas/` antes e depois da suíte mostrou os 1.213 arquivos sem nenhuma criação, remoção ou alteração. |
| 2. Conclusão | Validada na fase 1 (T012), com o texto aprovado pelo usuário em 07/10/2026 (T013). A seção continua no relatório, igual à linha de base. |
| 3. Relatório igual ao de referência | `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: as cinco etapas com código 0, em 5 min 34 s. `comparar` com `_backup_2026-10-07_antes_reorganizacao/linha_de_base`: "Nenhuma diferença." (PDF com 30 páginas, 58 abas e 8 figuras). A planilha tem 58 abas: as 57 de antes da conclusão mais `CONCLUSAO`. Os dados tratados foram conferidos com os de `data/processed/` antes da exclusão (T074): 20 arquivos idênticos byte a byte e 10 com os mesmos dados, reorganizados entre as etapas. |
| 4. Etapas isoladas e pré-requisito | O relatório foi refeito sozinho a partir das análises gravadas (código 0) e ficou igual à linha de base (T066). `python -m src tratamento` com um perfil válido sem coleta terminou com código 5 e a mensagem "Execute antes: python -m src coleta …", sem gravar nada. A marcação `desatualizada` das etapas seguintes está coberta pelos testes do pipeline. |
| 5. Perfil | Um perfil sem `garantia_fisica_mwmed` e com potência unitária × unidades diferente da instalada foi recusado com código 4, com os dois problemas listados e nada gravado. A usina fictícia (três unidades, Francis, GO) gera o relatório completo sem nenhuma menção à São Domingos, com "entre uma e três unidades" (teste de integração), e os arquivos de texto das quatro primeiras etapas também não mencionam a São Domingos. Os perfis temporários foram apagados depois do teste. |
| 6. Cópias de segurança | `criar_copia` foi executada numa raiz temporária com o conteúdo real do projeto e duas cópias existentes. A nova cópia foi conferida (267 arquivos, com o SHA-256 em `copia.json`, `LEIA-ME.txt` e `conftest.py`), e a mais antiga só saiu depois. Dados brutos e documentos ficaram fora. A ferramenta não foi executada no projeto real, para não excluir `_backup_2026-10-07_antes_conclusao`, que guarda o código anterior à auditoria. |
| 7. Specs e constituição | A constituição não tem "SYNC IMPACT", emendas, `153`, `MSUHSD` nem "São Domingos". As specs novas não têm remissão a revisões. O mapeamento dá destino a 100 % dos itens em vigor. A contagem de cinco pastas em `specs/` fica para a troca das specs (T076), adiada pelo usuário em 08/10/2026. |
| 8. Pasta do projeto | Cada exclusão e movimentação consta do inventário aprovado (itens 1 a 28). Os documentos estão em `usinas/sao_domingos/documentos/` (25) e `referencias/` (10). `data/raw/` está intacto: 1.071 arquivos, com os mesmos tamanhos e datas. O único `.bak` fora das cópias de segurança é `data/usinas/sao_domingos/coleta/auditoria_evt.csv.bak`, cópia exigida dos dados da Coleta. |

### 08/10/2026 — T072: plano, modelo de dados e contratos das cinco specs; revisão spec × código

- **Documentos**: em `novas-specs/<etapa>/`, `plan.md`, `data-model.md` e `contracts/cli-<etapa>.md`, escritos a partir do código final por cinco subagentes com um brief comum. A Coleta também recebeu `contracts/perfil-usina.md`, atualizado para o perfil final.
  - O conteúdo cobre os módulos, os artefatos com as colunas reais, os objetos entre etapas, o resumo do `etapa.json` e as decisões técnicas reunidas das `research.md` antigas, sem remissão às specs antigas.
  - A Coleta guarda as regras comuns do fluxo.
- **Revisão spec × código**: ao escrever, cada subagente comparou a spec com o código.
  - **20 correções no código**, onde a spec estava certa, com 17 testes novos:
    - Ctrl+C dá código 1 com o `etapa.json` em falha, e a gravação interrompida volta à versão anterior;
    - `--log-level` vale para os módulos carregados durante a etapa;
    - Coleta: valores ilegíveis da EVT contados na auditoria e no resumo; dicionários também no código 2; aviso das linhas parciais da programação; mais casos cobertos pelas tentativas do catálogo;
    - Conferência: diferença igual à tolerância coincide; hora de disponibilidade sinalizada não conta como ausente; potência do perfil com casa decimal;
    - Análises: constatação da mudança de classificação só quando detectada;
    - Relatório: limiares e órgão da garantia física tirados das regras e do perfil; uma data de geração; figura opcional antiga apagada; DICIONARIOS com os dez conjuntos; `comparar` com mensagem para planilha ilegível;
    - duas tolerâncias levadas para `src/comum/regras.py`.
  - **Comparação**: o relatório da São Domingos ficou igual à linha de base ("Nenhuma diferença.").
- **Aprovação do usuário (08/10/2026)**: o pacote `ajustes-specs.md` foi aprovado em todos os itens.
  - **Specs**: 65 trocas, com os 57 ajustes de redação e as opções escolhidas. Status "aprovada · 2026-10-08", e uma linha em "Decisões do usuário" de cada spec.
  - **Código das decisões**, com 12 testes novos:
    - D1: valor ausente fica fora das conferências mensais e é contado em `sem_valor`;
    - D3: nome da aba sem caracteres proibidos e com no máximo 31 caracteres;
    - D5: meses reproduzidos da TEIFa e da TEIP vindos da Conferência, com "em X dos N meses" na constatação e na legenda;
    - D7: relatório gerado em `.gravando/`, conferido e só então trocado, com restauração arquivo a arquivo;
    - R1: rótulo "sem programação: fora do período ou sem valor programado".
  - **D2, D4 e D6** mantêm o comportamento do código.
  - **Pendências P1 a P5 da Coleta** (só afetam outras usinas): ficam para depois da fiscalização, registradas no plano da Coleta.
- **Cópia de segurança**: `_backup_2026-10-08_antes_ajustes_t072`, criada antes da mudança do relatório (272 arquivos conferidos). A cópia mais antiga, `_backup_2026-10-07_antes_conclusao`, saiu.
- **Validação**:
  - suíte sem rede com 396 testes aprovados; o pyflakes não aponta problema;
  - `completo --sem-portal --data-geracao "07/10/2026 08:53"`: código 0 em 5 min 35 s;
  - o `comparar` com a linha de base de 07/10 mostra só o Markdown e o PDF, e o diff de texto confirma que mudaram apenas as 3 linhas do rótulo, na página 17 do PDF. O PDF continua com 30 páginas; planilha, CSV e 8 figuras ficaram idênticos.
  - Novo relatório de referência em `_backup_2026-10-08_antes_ajustes_t072/linha_de_base/`, com `comparar` "Nenhuma diferença.".
