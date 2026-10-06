# Tasks: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança dos Dados Processados - UHE São Domingos

**Input**: Design documents from `/specs/006-bases-complementares/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (cli-contract.md, persistencia-contract.md), quickstart.md

**Tests**: incluídos. Cada história define um teste independente na spec, e a constituição 1.2.0 exige testes e validação de não regressão. Testes sempre sem rede: catálogo e download simulados com `unittest.mock`, arquivos sintéticos em `tmp_path`.

**Organization**: tarefas agrupadas por história. A persistência, o motor dos conjuntos horários e a extensão dos resultados da análise são pré-requisitos comuns (Phase 2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: paralelizável (arquivos diferentes, sem dependência de tarefa pendente)
- **[Story]**: história da spec (US1 a US6)

---

## Phase 1: Setup

**Purpose**: proteção do estado atual e referência de não regressão.

- [X] T001 Criar a cópia datada `_backup_AAAA-MM-DD_antes_spec006/` (data da execução), exigida pelo Requisito Técnico 3(b) da constituição 1.2.0.
  - Conteúdo: `src/`, `tests/`, `specs/`, `reports/`, `README.md`, `requirements.txt` e `.specify/`.
  - Acrescentar `conftest.py` com `collect_ignore_glob = ["*"]` e um `LEIA-ME.txt` com o motivo da cópia.
- [X] T002 Registrar a linha de base na seção "Registro de execução" de `specs/006-bases-complementares/tasks.md`:
  - executar `python -m pytest tests -q` (esperado: 87 aprovados);
  - registrar, numa seção "Registro de execução" ao final de `specs/006-bases-complementares/tasks.md`, o SHA-256 de cada arquivo atual de `data/processed/` e de `reports/relatorio_analise_estatistica.md`. Essa é a referência do SC-008;
  - a planilha `reports/perfil_estatistico_anual.xlsx` fica na cópia de T001 para a comparação aba a aba.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: persistência com cópia de segurança, motor comum dos conjuntos horários, constantes, loggers e pontos de extensão do relatório.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T003 [P] Acrescentar a `src/config.py` as constantes das bases novas.
  - **Ids do catálogo**:
    - `CONJUNTO_EVT = "energia-vertida-turbinavel"`;
    - `CONJUNTO_DISPONIBILIDADE = "disponibilidade_usina"`;
    - `CONJUNTO_HIDROLOGIA = "dados_hidrologicos_ho"`;
    - `CONJUNTO_GERACAO = "geracao-usina-2"`;
    - `CONJUNTO_CADASTRO = "modalidade-usina"`.
  - **Pastas brutas**: `DISPONIBILIDADE_RAW_DIR`, `HIDROLOGIA_RAW_DIR`, `GERACAO_RAW_DIR` e `CADASTRO_RAW_DIR` em `RAW_DATA_DIR / "disponibilidade_usina" | "dados_hidrologicos_ho" | "geracao_usina_2" | "modalidade_usina"`; `DIRETORIO_DICIONARIOS = "_dicionarios"`.
  - **`CONJUNTOS_PIPELINE: Dict[str, str]`**: id → subpasta relativa à raiz bruta, para os 10 conjuntos:
    - EVT → `""`;
    - os 4 de indicadores → `"indicadores_ons/<id>"`;
    - `programacao_diaria` → `"programacao_diaria"`;
    - os 4 novos → as suas pastas.
  - **Nomes dos arquivos processados**: os do data-model.md, seção 9.
  - **Identificação e limiares**:
    - `ID_RESERVATORIO_ONS = "PNUHSD"`;
    - `LIMIAR_SINCRONIZADA_MW = 1.0`;
    - `TOLERANCIA_COINCIDENCIA_MW = 0.01`;
    - `TOLERANCIA_COINCIDENCIA_VAZAO_M3S = 0.5`;
    - `META_ALINHAMENTO_HIDROLOGIA_PCT = 99.0`;
    - `TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW = 0.01`;
    - `POTENCIA_AUTORIZADA_ESPERADA_MW = NOMINAL_INSTALLED_CAPACITY_MW`.
- [X] T004 [P] Acrescentar a `LOGGERS_PIPELINE` em `src/logger.py` os loggers `persistencia`, `dicionarios_ons`, `conjuntos_ons`, `disponibilidade_ons`, `hidrologia_ons`, `geracao_ons` e `cadastro_ons`. Ajustar a lista esperada em `tests/test_conformidade.py`.
- [X] T005 [P] Escrever os testes de contrato da persistência em `tests/unit/test_persistencia.py`, conforme o contracts/persistencia-contract.md. Casos:
  - (1) gravar sem versão anterior → `NOVO`, sem `.bak`;
  - (2) conteúdo diferente → `ALTERADO`, com `<nome>.bak` igual à versão anterior;
  - (3) mesmo conteúdo → `INALTERADO`; destino e `.bak` sem alteração de hash nem de data de modificação;
  - (4) falha simulada na troca e na conferência → destino idêntico ao anterior, `<nome>.tmp` removido e `ErroPersistencia` levantado;
  - (5) planilha regravada com os mesmos dados → `INALTERADO`, apesar de os bytes do pacote mudarem;
  - (6) `gravar_linhas_csv` confere linhas = registros + 1 e cabeçalho;
  - (7) `gravar_parquet` → mesmo DataFrame duas vezes = `INALTERADO`.
- [X] T006 Implementar `src/persistencia.py` (depende de T005).
  - **Tipos**: `ResultadoGravacao` (Enum `NOVO` | `ALTERADO` | `INALTERADO`) e `ErroPersistencia(ONSError)`, com `destino` e `motivo`.
  - **Núcleo `_gravar_com_copia(destino, escrever, conferir, identico)`**, nesta ordem:
    1. grava `<nome>.tmp` na mesma pasta;
    2. faz a conferência física;
    3. se `identico(destino, tmp)`, apaga o `.tmp` e retorna `INALTERADO`;
    4. copia o atual para `<nome>.bak` com `shutil.copy2`;
    5. troca com `Path.replace`;
    6. confere se o SHA-256 do destino é igual ao do temporário;
    7. em falha depois do passo 4, restaura a partir do `.bak` (ou apaga o destino, se ele era novo), remove o `.tmp`, levanta `ErroPersistencia` e registra log de erro com o nome do arquivo.
  - **Funções públicas**:
    - `gravar_csv(df, destino, **opcoes)`: padrão `sep=";"`, `encoding="utf-8"`, `index=False`, `date_format="%Y-%m-%d %H:%M:%S"`; conferência por releitura (linhas e colunas; arquivo sem colunas = (0, 0));
    - `gravar_linhas_csv(cabecalho, linhas, destino, delimitador=";")`;
    - `gravar_parquet(df, destino)`: pyarrow, `index=False`; conferência por `pyarrow.parquet.read_metadata`;
    - `gravar_planilha(abas, destino, formatar=None)`: abas em ordem; propriedade personalizada `assinatura_dados` = SHA-256 de Σ (nome da aba + "\n" + CSV da aba sem índice); comparação lendo `docProps/custom.xml` via `zipfile`; conferência das abas e dimensões com openpyxl `read_only`;
    - `gravar_texto(texto, destino)`.
  - **Comparação "idêntico"**: por bytes, exceto nas planilhas (pela assinatura).
  - **Logs INFO**: o resultado e o número de registros.
- [X] T007 [P] Escrever os testes do motor em `tests/test_conjuntos_ons.py`. Casos:
  - período pelo nome com o padrão `_(\d{4})(?:_(\d{2}))?\.` (anual e mensal);
  - seleção dos arquivos que se sobrepõem a [início, fim];
  - formato por chave de período: Parquet quando publicado, senão CSV (mês só com CSV);
  - recurso duplicado no catálogo: "fica o recurso com `last_modified` preenchido e, em empate, o de maior tamanho"; duplicidade em `recursos_duplicados_catalogo`;
  - linhas com identificação parcial contadas em `linhas_so_identificador` e `linhas_so_conferencia`, não extraídas;
  - conversão numérica com contagem em `valores_invalidos`;
  - duplicatas: fica a hora do arquivo mais recente; `duplicatas_conflitantes` contadas;
  - ausências `MES_SEM_ARQUIVO`, `MES_SEM_USINA` e `HORAS`, sem interpolação;
  - CSV com releitura em Latin-1;
  - status `PROCESSADO`, `SEM_REGISTROS` e `FALHA`.
- [X] T008 Implementar o motor comum `src/conjuntos_ons.py` (depende de T003, T006 e T007).
  - **Tipos**: `DescricaoConjunto` (dataclass imutável: `pacote`, `pasta_raw`, `formatos_preferidos`, `identificador` (coluna, valor), `conferencias` (coluna → igual | contém), `convencao_hora` (`"inicio"` | `"fim"`), `colunas_valor`), `RecursoSelecionado` e `SerieConjunto(horaria, ausencias, auditoria)`.
  - **Funções**:
    - `periodo_do_arquivo(nome)`;
    - `selecionar_recursos(desc, metadados, inicio, fim)`;
    - `sincronizar_conjunto(desc, inicio, fim, pasta_raw, force=False)`: `download_resource`, manifesto da pasta e 8 downloads simultâneos, como em `src/programacao_ons.py`;
    - `ler_arquivo(desc, caminho)`: Parquet com projeção de colunas; CSV `;` com releitura em Latin-1; auditoria com as colunas do data-model.md, seção 3;
    - `montar_serie(desc, pasta_raw, inicio, fim, converter_hora=None)`: deduplicação, recorte no período e ausências;
    - `exportar_serie(serie, arquivos, pasta_saida)`, via `persistencia.gravar_csv`;
    - `carregar_serie_processada(arquivos, pasta)`: datas convertidas; ignora `.bak` e `.tmp`;
    - `data_obtencao(pasta_raw)`: maior `registrado_em_utc` do manifesto.
- [X] T009 [P] Preparar `src/analyzer.py` para as seções novas, sem mudar a saída atual.
  - `ResultadosAnalise` ganha os campos `disponibilidade`, `hidrologia`, `geracao_oficial`, `cadastro` e `dicionarios` (`Dict`, padrão vazio).
  - `analisar(...)` aceita `disponibilidade=None`, `hidrologia=None`, `geracao=None`, `cadastro=None` e `dicionarios=None`.
  - `NOMES_FIGURAS_OPCIONAIS = {"disponibilidade_sincronizada": "06_disponibilidade_operacional_sincronizada_mensal.png", "faixas_afluencia": "07_evt_por_faixa_de_afluencia.png", "perfil_hidrologico": "08_perfil_horario_nivel_vazoes.png"}`.
  - `gerar_graficos` só gera uma figura opcional quando o resultado correspondente não está vazio.
  - `tests/test_analyzer.py` continua exigindo as 5 figuras atuais quando não há dados novos.

**Checkpoint**: persistência e motor testados; `python -m pytest tests -q` aprovado.

---

## Phase 3: User Story 1 - Cópia de segurança dos dados processados (Priority: P1) 🎯 MVP

**Goal**: toda regravação em `data/processed/` guarda a versão anterior em `<nome>.bak`, confere a gravação e restaura em caso de falha (FR-008 a FR-012).

**Independent Test**: gravar o mesmo arquivo quatro vezes (sem versão anterior, alterado, idêntico, falha simulada) e conferir o arquivo e o `.bak`. Nas etapas reais, a segunda execução sem mudança informa `INALTERADO`.

### Tests for User Story 1

- [X] T010 [P] [US1] Escrever `tests/test_persistencia_gravadores.py`.
  - Cada gravador existente, executado duas vezes com os mesmos dados em `tmp_path`, informa `INALTERADO` na segunda vez e não cria `.bak`; com dados alterados, cria `.bak` igual à versão anterior. Gravadores:
    - `save_consolidated_records` e `save_audit_report`;
    - `exportar_csv`, `exportar_parquet` e `exportar_excel`;
    - `gerar_relatorio_validacao_md` e `gerar_relatorio_validacao_csv`;
    - `exportar_indicadores`;
    - `exportar_programacao`.
  - Teste do FR-011: com arquivos `*.bak` e `*.tmp` na pasta, `carregar_indicadores_processados`, `carregar_programacao_processada` e `periodo_base_evt` leem só os arquivos corretos.

### Implementation for User Story 1

- [X] T011 [P] [US1] Em `src/consolidator.py`, `save_consolidated_records` e `save_audit_report` passam a gravar via `persistencia.gravar_linhas_csv`, com as mesmas colunas, ordem e formatação de valores vazios. O retorno continua o caminho.
- [X] T012 [P] [US1] Em `src/processor.py`:
  - `exportar_csv` → `gravar_csv` (mesmas opções);
  - `exportar_parquet` → `gravar_parquet`;
  - `exportar_excel` → `gravar_planilha` com a aba `UHE_SAO_DOMINGOS` e `formatar` aplicando a largura das colunas e `freeze_panes = "A2"`.
- [X] T013 [P] [US1] Em `src/validator.py`: `gerar_relatorio_validacao_md` → `gravar_texto`; `gerar_relatorio_validacao_csv` → `gravar_csv`.
- [X] T014 [P] [US1] Em `src/indicadores_ons.py`, `exportar_indicadores` grava os 6 CSV via `gravar_csv` (mesmo `date_format`) e a planilha via `gravar_planilha`, com as abas na ordem atual e `freeze_panes = "A2"`.
- [X] T015 [P] [US1] Em `src/programacao_ons.py`, `exportar_programacao` grava os 3 CSV via `gravar_csv` (mesmo `date_format`).
- [X] T016 [US1] Validar a US1 na base real em `data/processed/`:
  - executar duas vezes `python -m src.main --filter-only --sem-indicadores --sem-programacao` e duas vezes `python -m src.processor`;
  - **1ª execução**: CSV, Parquet e Markdown `INALTERADO` com hashes iguais aos de T002; planilhas `ALTERADO` (passam a ter a assinatura), com `.bak` criado;
  - **2ª execução**: tudo `INALTERADO`; os `.bak` mantêm hash e data de modificação.
  - Registrar o resultado em "Registro de execução".

**Checkpoint**: US1 completa e verificável de forma independente; conformidade com o Requisito Técnico 3(a).

---

## Phase 4: User Story 2 - Dicionários de dados das fontes (Priority: P1)

**Goal**: a cada coleta, os dicionários (PDF e JSON) de cada conjunto são obtidos, comparados pelo conteúdo e guardados em `<pasta bruta>/_dicionarios/`, com versões anteriores preservadas (FR-013 a FR-015).

**Independent Test**: simular três coletas (dicionários novos, iguais e um alterado) e conferir os arquivos, a versão preservada e o registro.

### Tests for User Story 2

- [X] T017 [P] [US2] Escrever `tests/test_dicionarios_ons.py`. Casos:
  - seleção dos recursos de formato PDF ou JSON cujo nome, sem acentos, contém "dicionario";
  - sequência `NOVO` → `INALTERADO` → `ALTERADO`, com a versão anterior em `_dicionarios/_versoes_anteriores/`;
  - `FALHA` por erro de rede simulado: mantém a cópia válida, não levanta exceção e o retorno é 0;
  - `NAO_PUBLICADO` no registro quando falta um formato;
  - registro com uma linha por conjunto e formato, montado de todos os manifestos (uma execução parcial não apaga as linhas dos outros conjuntos);
  - obter o dicionário da EVT não chama `discover_and_download_all` nem altera `ENERGIA_VERTIDA_TURBINAVEL_*.csv`.

### Implementation for User Story 2

- [X] T018 [US2] Implementar `src/dicionarios_ons.py`.
  - `selecionar_dicionarios(metadados)`.
  - `sincronizar_dicionarios(conjuntos, raiz_raw=RAW_DATA_DIR)`:
    - pasta = `raiz_raw / CONJUNTOS_PIPELINE[id] / "_dicionarios"`;
    - `download_resource(..., force=True)` com o manifesto dessa pasta;
    - SHA-256 antes e depois → `NOVO` | `INALTERADO` | `ALTERADO`; exceção → `FALHA`, com log de aviso;
    - grava no manifesto `conjunto`, `formato`, `resultado_ultima_obtencao`, `obtido_em_utc` e `sha256`.
  - `montar_registro(raiz_raw)`: colunas `conjunto`, `pasta`, `formato`, `arquivo`, `url`, `resultado_ultima_obtencao`, `obtido_em_utc`, `sha256`, `tamanho_bytes`, `versoes_anteriores` e `ultima_versao_anterior`; 20 linhas esperadas; `NAO_PUBLICADO` quando falta um formato.
  - `executar_dicionarios_ons(conjuntos=None, pasta_raw=RAW_DATA_DIR, pasta_saida=PROCESSED_DATA_DIR) -> int`: grava `relatorio_dicionarios_ons.csv` via `gravar_csv`; retorna 0 mesmo com `FALHA`.
  - `main()` com `--conjuntos` e `--log-level`.
- [X] T019 [US2] Integrar a obtenção dos dicionários a cada coleta em `src/indicadores_ons.py`, `src/programacao_ons.py` e `src/main.py`.
  - `executar_indicadores_ons` e `executar_programacao_ons` ganham o parâmetro `dicionarios: bool = True`. Quando `baixar` e `dicionarios` forem verdadeiros, chamam `sincronizar_dicionarios` para os seus conjuntos, com `raiz_raw = pasta_raw.parent`, e regravam o registro.
  - Em `src/main.py`:
    - a etapa 1 obtém o dicionário de `CONJUNTO_EVT` depois de `discover_and_download_all`, sem tocar os dados;
    - modo novo `--dicionarios-only` (os 10 conjuntos);
    - opção `--sem-dicionarios`, com log de aviso.
  - Ajustar `tests/integration/test_pipeline.py`: a etapa 1 chama os dicionários da EVT com `raiz_raw = raw_dir`.
- [X] T020 [P] [US2] Em `src/analyzer.py`, carregar `relatorio_dicionarios_ons.csv` em `executar_pipeline_analise` (aviso se ausente), preencher `res.dicionarios` e exportar a aba `DICIONARIOS`.
- [X] T021 [US2] Validar a US2 na base real (`data/raw/**/_dicionarios/` e `data/processed/relatorio_dicionarios_ons.csv`):
  - executar duas vezes `python -m src.main --dicionarios-only`;
  - 1ª execução: 20 linhas `NOVO`; 2ª: `INALTERADO`;
  - as datas de modificação de `data/raw/ENERGIA_VERTIDA_TURBINAVEL_*.csv` não mudam.
  - Registrar em "Registro de execução".

**Checkpoint**: US2 completa; conformidade com o princípio IV (dicionários).

---

## Phase 5: User Story 3 - Disponibilidade operacional e sincronizada (Priority: P1)

**Goal**: série horária oficial de disponibilidade (operacional e sincronizada) no período da base EVT, conferida com a disponibilidade declarada, com as horas paradas classificadas e o resultado no relatório (FR-016 a FR-020 e FR-031 a FR-034).

**Independent Test**: com os arquivos obtidos e a base EVT, gerar a conferência e a classificação; a soma das classes deve ser igual ao total de horas paradas comuns.

### Tests for User Story 3

- [X] T022 [P] [US3] Escrever `tests/test_disponibilidade_ons.py`. Casos:
  - identificação por `id_ons` = `MSUHSD`, conferida por CEG `UHE.PH.MS.028761-0.01` e `id_estado` = `MS`;
  - formato por mês: CSV de 2018-08 a 2022-12 e Parquet de 2023-01 em diante, com catálogo simulado;
  - qualidade: "D1: sincronizada > operacional + 0,01 MW; D2: operacional > instalada + 0,01 MW; D3: algum valor negativo; D4: algum valor não numérico"; horas sinalizadas fora das análises;
  - conferência operacional × declarada: coincidente se |diferença| ≤ 0,01 MW; divergências agrupadas em períodos contínuos; horas presentes em só uma das fontes;
  - classificação das horas paradas: geração ≤ 1 MW; `SINCRONIZADA` se a sincronizada > 1 MW, senão `NAO_SINCRONIZADA`; `COM_EVT` ou `SEM_EVT`; classe da spec 004 ou `SEM_PROGRAMACAO`; soma das classes = total de horas paradas;
  - resumo mensal e anual com `capacidade_nao_sincronizada_media_mw`, `capacidade_nao_sincronizada_mwh`, `reserva_desligada_teif_mwh` = Σ(HRD × potência da unidade) e `diferenca_mwh`.

### Implementation for User Story 3

- [X] T023 [US3] Implementar `src/disponibilidade_ons.py` (etapa de dados).
  - `DESCRICAO`: pacote `disponibilidade_usina`; pasta `disponibilidade_usina`; formatos Parquet e CSV; identificador `id_ons` = `MSUHSD`; conferências `ceg` e `id_estado`; hora de início; colunas `val_potenciainstalada`, `val_dispoperacional` e `val_dispsincronizada`.
  - `qualidade(df)`, com as regras D1 a D4.
  - `executar_disponibilidade_ons(baixar=True, force=False, periodo=None, pasta_raw=DISPONIBILIDADE_RAW_DIR, pasta_saida=PROCESSED_DATA_DIR, dicionarios=True) -> int`:
    - retorna 0, 1 ou 2;
    - obtém os dicionários quando `baixar`;
    - grava via persistência `uhe_sao_domingos_ons_disponibilidade_horaria.csv` (colunas `din_instante`, `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada`, `qualidade` e `arquivo_origem`), `uhe_sao_domingos_ons_disponibilidade_ausencias.csv` e `relatorio_auditoria_disponibilidade_ons.csv`.
  - `carregar_disponibilidade_processada(pasta)`.
  - `main()` com `--no-download`, `--force-download` e `--log-level`.
- [X] T024 [US3] Acrescentar a `src/disponibilidade_ons.py` as funções de análise.
  - `conferir_com_evt(disp, df)`: resumo `horas_comuns`, `coincidentes`, `divergentes`, `so_ons_disponibilidade` e `so_base_evt`; divergências em períodos contínuos (`inicio`, `fim`, `horas`, `diferenca_media_mw`, `diferenca_maxima_mw`).
  - `classificar_horas_paradas(disp, df, classificadas_programacao)`.
  - `resumir(disp, df, horas_estado, freq)`, com as colunas do data-model.md, seção 4.
- [X] T025 [P] [US3] Em `src/main.py`, criar a etapa 5 (disponibilidade), depois da etapa 4.
  - Opções: `--disponibilidade-only`, `--sem-disponibilidade` e `--complementares-only`. Este último roda as etapas novas disponíveis e seus dicionários, sem tocar a base EVT.
  - Pasta `<raw-dir>/disponibilidade_usina`; período da base consolidada (ou de `periodo_base_evt` nos modos `-only`).
  - Atualizar `tests/integration/test_pipeline.py` para simular `executar_disponibilidade_ons` e conferir o período, `pasta_raw` e `pasta_saida`.
- [X] T026 [US3] Em `src/analyzer.py`:
  - `analisar_disponibilidade(...)` preenche `res.disponibilidade`: `conferencia`, `divergencias`, `horas_paradas`, `classes`, `mensal`, `anual`, `auditoria`, `ausencias`, `periodo` e `obtido_em`;
  - `_achado_disponibilidade_sincronizada(res)`, com números e frases gerados a partir dos dados: coincidência com a declarada, horas paradas sem unidade sincronizada e médias anuais da sincronizada;
  - `secao_disponibilidade_md(res, secao)`, depois da seção da programação;
  - abas `DISP_CONFERENCIA`, `DISP_DIVERGENCIAS`, `DISP_HORAS_PARADAS`, `DISP_MENSAL`, `DISP_ANUAL` e `DISP_AUDITORIA`;
  - linhas em `tabela_parametros`: fonte, identificador, período e data de obtenção; limiar da sincronizada de 1 MW; tolerância de 0,01 MW;
  - carga em `executar_pipeline_analise`, com aviso se o arquivo estiver ausente.
- [X] T027 [US3] Implementar a figura 06 em `src/analyzer.py`: `_grafico_disponibilidade_sincronizada(res, caminho, dpi)`.
  - Antes de escrever o código, **carregar a skill dataviz**.
  - Médias mensais de operacional, sincronizada e geração (MW), com `sns.lineplot`, num eixo único, com `_tema_graficos()` e as cores centrais.
  - Se precisar de uma cor nova, validá-la com o script da skill.
- [X] T028 [US3] Em `src/pdf_generator.py`, criar `_secao_disponibilidade_sincronizada`, depois de `_secao_programacao`, com a constatação, as tabelas mensal e anual resumidas e a figura 06.
- [X] T029 [US3] Validar a US3 na base real (`data/raw/disponibilidade_usina/` e `data/processed/`).
  - Executar `python -m src.main --disponibilidade-only` (download de cerca de 1,3 GB) e depois `python -m src.analyzer`.
  - Conferir:
    - auditoria sem `FALHA`;
    - meses de 2018-08 a 2026-09 obtidos ou listados;
    - coincidência operacional × declarada;
    - soma das classes = horas paradas (SC-005);
    - seção, aba e figura 06 presentes.
  - Registrar em "Registro de execução".

**Checkpoint**: US3 completa; seção e figura no relatório.

---

## Phase 6: User Story 4 - Afluência, vertimento e nível do reservatório (Priority: P1)

**Goal**: série hidrológica horária alinhada à base EVT, com faixas de afluência nas horas com EVT, perfil por hora do dia e resumo mensal no relatório (FR-021 a FR-026 e FR-031 a FR-034).

**Independent Test**: alinhar as horas, conferir a coincidência de turbinada e vertida (≥ 99%) e conferir que a soma das faixas é igual ao total de horas com EVT do período comum.

### Tests for User Story 4

- [X] T030 [P] [US4] Escrever `tests/test_hidrologia_ons.py`. Casos:
  - conversão de hora: "hora de início = (instante publicado arredondado para cima até a hora cheia) − 1 h". Exemplos: 01:00 → 00:00; 23:59 → 23:00 do mesmo dia; 15:00 → 14:00;
  - identificação por `cod_usina` = 153, conferida por "SAO DOMINGOS" e `PNUHSD`; homônimo contado e não extraído;
  - qualidade: H1 (vazão negativa), H2 (volume útil fora de 0 a 100%), H3 (não numérico); campo vazio continua vazio, não vira zero;
  - alinhamento: `meta_pct` = 99, `tolerancia_m3s` = 0,5, `deslocamento_aplicado_h` = −1;
    - ≥ 99% → `confirmado = True`;
    - < 99% → `confirmado = False` e código de saída 3;
  - faixas, com os limites exatos:
    - 163,01 → `ACIMA_ENGOLIMENTO_USINA`;
    - 163 → `ENTRE_UMA_E_DUAS_UNIDADES`;
    - 81,51 → `ENTRE_UMA_E_DUAS_UNIDADES`;
    - 81,5 → `ATE_UMA_UNIDADE`;
    - vazio → `SEM_DADO_HIDROLOGICO`;
    - soma das faixas = total de horas com EVT;
  - perfil por hora do dia (0 a 23) por grupo de dias (`COM_PARADA_EVT`, `DEMAIS`);
  - resumo mensal com as colunas do data-model.md, seção 5.

### Implementation for User Story 4

- [X] T031 [US4] Implementar `src/hidrologia_ons.py` (etapa de dados).
  - `DESCRICAO`: pacote `dados_hidrologicos_ho`; pasta `dados_hidrologicos_ho`; formatos Parquet e CSV; identificador `cod_usina` = 153; conferências `nom_reservatorio` contém "SAO DOMINGOS" e `id_reservatorio` = `PNUHSD`; hora de fim.
  - Grandezas: vazões afluente, defluente, turbinada, vertida, vertida não turbinável e por outras estruturas; níveis de montante e jusante; volume útil.
  - `hora_de_inicio(instantes)` e `qualidade(df)`, com as regras H1 a H3.
  - `alinhar_com_evt(hid, evt)`: lê da base tratada só `din_instante`, `val_vazaoturbinada` e `val_vazaovertida`; devolve uma linha com `horas_comuns`, `coincidentes_turbinada`, `coincidentes_vertida`, `coincidentes_ambas`, `pct_coincidencia`, `meta_pct`, `tolerancia_m3s`, `deslocamento_aplicado_h` e `confirmado`.
  - `executar_hidrologia_ons(baixar=True, force=False, periodo=None, pasta_raw=HIDROLOGIA_RAW_DIR, pasta_saida=PROCESSED_DATA_DIR, dicionarios=True) -> int`:
    - retorna 0, 1, 2 ou 3;
    - grava via persistência `uhe_sao_domingos_ons_hidrologia_horaria.csv` (com `din_instante_publicado`), `uhe_sao_domingos_ons_hidrologia_ausencias.csv`, `uhe_sao_domingos_ons_hidrologia_alinhamento.csv` e `relatorio_auditoria_hidrologia_ons.csv`.
  - `carregar_hidrologia_processada(pasta)` e `main()`.
- [X] T032 [US4] Acrescentar a `src/hidrologia_ons.py` as funções de análise:
  - `classificar_faixas(hid, df)`: horas com EVT > 0 do período comum;
  - `resumir_faixas(classificadas, freq)`: horas e EVT (MWh) por faixa, por mês e por ano;
  - `perfil_hora_do_dia(hid, df)`: médias de nível de montante, afluente, turbinada e vertida, para dias com ao menos uma hora de parada com EVT e para os demais;
  - `resumo_mensal(hid)`.
- [X] T033 [P] [US4] Em `src/main.py`, criar a etapa 6 (hidrologia), com `--hidrologia-only` e `--sem-hidrologia`, e incluí-la em `--complementares-only`.
  - O código 3 é propagado e encerra o pipeline com log de erro.
  - Atualizar `tests/integration/test_pipeline.py` (simular `executar_hidrologia_ons`; conferir período e pastas; código 3).
- [X] T034 [US4] Em `src/analyzer.py`:
  - `analisar_hidrologia(...)` preenche `res.hidrologia` só com `alinhamento.confirmado`. Caso contrário, o resultado guarda o alinhamento e o relatório informa apenas a falha (FR-022).
  - `_achado_afluencia(res)`: horas e EVT por faixa e comportamento do nível nos dias com parada com EVT.
  - `secao_hidrologia_md(res, secao)`, depois da seção da disponibilidade, com a ressalva "dados informados pelos agentes e não consistidos pelo ONS".
  - Abas `HID_ALINHAMENTO`, `HID_FAIXAS_AFLUENCIA`, `HID_MENSAL`, `HID_PERFIL_HORA_DO_DIA` e `HID_AUDITORIA`.
  - Parâmetros: fonte, identificador, faixas de 81,5 e 163 m³/s, tolerância de 0,5 m³/s e meta de 99%.
  - Carga em `executar_pipeline_analise`.
- [X] T035 [US4] Implementar em `src/analyzer.py` a figura 07 (`_grafico_faixas_afluencia`) e a figura 08 (`_grafico_perfil_hidrologico`). Carregar a skill dataviz antes do código.
  - **Figura 07**: barras anuais empilhadas de horas com EVT por faixa, com seaborn e `hue_order` invertido. O seaborn empilha a última categoria na base. `SEM_DADO_HIDROLOGICO` em `COR_CONTEXTO`.
  - **Figura 08**: dois painéis com seaborn (vazões em m³/s; nível de montante em m), por hora do dia, para os dois grupos de dias, **sem eixo duplo**.
  - Validar as cores novas com o script da skill.
- [X] T036 [US4] Em `src/pdf_generator.py`, criar `_secao_hidrologia`, depois de `_secao_disponibilidade_sincronizada`, com a constatação, as tabelas resumidas e as figuras 07 e 08 (ou só o aviso de falha de alinhamento).
- [X] T037 [US4] Validar a US4 na base real (`data/raw/dados_hidrologicos_ho/` e `data/processed/`).
  - Executar `python -m src.main --hidrologia-only` e `python -m src.analyzer`.
  - Conferir:
    - `pct_coincidencia` ≥ 99 e `confirmado = True` (SC-003);
    - soma das faixas = horas com EVT;
    - ausências listadas;
    - seção, abas e figuras 07 e 08.
  - Registrar em "Registro de execução".

**Checkpoint**: P1 completo (US1 a US4); pacote da fiscalização.

---

## Phase 7: User Story 5 - Conferência independente da geração (Priority: P2)

**Goal**: conferência reproduzível da geração da base EVT com a série oficial de geração por usina (FR-027 e FR-028).

**Independent Test**: comparação horária e mensal no período comum, com cada hora comum classificada como coincidente ou divergente.

### Tests for User Story 5

- [X] T038 [P] [US5] Escrever `tests/test_geracao_ons.py`. Casos:
  - arquivos anuais (até 2021) e mensais (a partir de 2022) selecionados pelo período;
  - identificação por `MSUHSD`, conferida por CEG e `MS`;
  - qualidade `G1` (não numérico);
  - coincidência se |diferença| ≤ 0,01 MW; horas em só uma das fontes; energia mensal (MWh) de cada fonte e diferença;
  - constatação só com horas divergentes.

### Implementation for User Story 5

- [X] T039 [US5] Implementar `src/geracao_ons.py`.
  - `DESCRICAO`: pacote `geracao-usina-2`; pasta `geracao_usina_2`; formatos Parquet e CSV; identificador `id_ons` = `MSUHSD`; conferências `ceg` e `id_estado`; hora de início; coluna `val_geracao`.
  - `executar_geracao_ons(...)`: grava via persistência `uhe_sao_domingos_ons_geracao_horaria.csv`, `uhe_sao_domingos_ons_geracao_ausencias.csv` e `relatorio_auditoria_geracao_ons.csv`.
  - `carregar_geracao_processada(pasta)`.
  - `conferir_geracao(ger, df)`: resumo, tabela mensal com `energia_base_evt_mwh`, `energia_ons_geracao_mwh`, `diferenca_mwh`, `horas_so_base_evt` e `horas_so_ons_geracao`, e divergências.
  - `main()`.
- [X] T040 [P] [US5] Em `src/main.py`, criar a etapa 7 (geração), com `--geracao-only` e `--sem-geracao`, e incluí-la em `--complementares-only`. Atualizar `tests/integration/test_pipeline.py`.
- [X] T041 [US5] Em `src/analyzer.py` e `src/pdf_generator.py`:
  - `analisar_geracao_oficial(...)`;
  - `_achado_conferencia_geracao(res)`, só com divergências;
  - `secao_geracao_oficial_md`, junto à seção de qualidade dos dados;
  - abas `GER_CONFERENCIA`, `GER_MENSAL` e `GER_DIVERGENCIAS`;
  - fonte em `tabela_parametros`;
  - seção correspondente no PDF.
- [X] T042 [US5] Validar a US5 na base real (`data/processed/uhe_sao_domingos_ons_geracao_horaria.csv`): `python -m src.main --geracao-only` e `python -m src.analyzer`. Esperado: igualdade hora a hora de 2018 a 2026 (conferência de 02/10/2026) ou divergências listadas. Registrar em "Registro de execução".

**Checkpoint**: US5 completa.

---

## Phase 8: User Story 6 - Identificação cadastral da usina no ONS (Priority: P3)

**Goal**: ficha cadastral da usina, com a data da consulta, os homônimos contados e as divergências sinalizadas (FR-029 e FR-030).

**Independent Test**: obter o cadastro e conferir que a ficha traz o CEG do projeto, o estado MS e a data da consulta.

### Tests for User Story 6

- [X] T043 [P] [US6] Escrever `tests/test_cadastro_ons.py`. Casos:
  - extração por CEG `UHE.PH.MS.028761-0.01`, conferida por `MSUHSD` e `MS`;
  - homônimos: linhas com "SAO DOMINGOS" no nome, sem acento, e CEG diferente;
  - divergências: potência ≠ 48 MW; estado ≠ MS;
  - `data_consulta_utc` tirada do manifesto;
  - cadastro republicado com conteúdo diferente → versão anterior preservada.

### Implementation for User Story 6

- [X] T044 [US6] Implementar `src/cadastro_ons.py`.
  - Recurso CSV único do pacote `modalidade-usina`, em `data/raw/modalidade_usina/`, com manifesto e versões anteriores.
  - Ficha com as colunas do data-model.md, seção 7, incluindo `homonimos` e `divergencias`, gravada via persistência em `uhe_sao_domingos_ons_cadastro.csv`.
  - `carregar_cadastro_processado(pasta)`, `executar_cadastro_ons(...)` e `main()`.
- [X] T045 [P] [US6] Em `src/main.py`, criar a etapa 8 (cadastro), com `--cadastro-only` e `--sem-cadastro`, e incluí-la em `--complementares-only`. Atualizar `tests/integration/test_pipeline.py`.
- [X] T046 [US6] Em `src/analyzer.py` e `src/pdf_generator.py`:
  - `analisar_cadastro(...)`;
  - `_achado_cadastro(res)`, só com divergência;
  - `secao_cadastro_md`, depois da seção de cobertura;
  - aba `CAD_FICHA`;
  - fonte em `tabela_parametros`;
  - tabela de identificação no PDF.
- [X] T047 [US6] Validar a US6 na base real (`data/processed/uhe_sao_domingos_ons_cadastro.csv`).
  - Executar `python -m src.main --cadastro-only` e `python -m src.analyzer`.
  - Ficha esperada: TIPO II-A, COSR-S, SE ÁGUA CLARA 138 KV, 48 MW, MS e mais de 20 homônimos contados.
  - Registrar em "Registro de execução".

**Checkpoint**: todas as histórias completas.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T048 [P] Ampliar `tests/test_conformidade.py`:
  - `--log-level` nos `main()` de `src/dicionarios_ons.py`, `src/disponibilidade_ons.py`, `src/hidrologia_ons.py`, `src/geracao_ons.py` e `src/cadastro_ons.py`, com execução simulada e sem rede;
  - as funções `_grafico_*` novas usam seaborn;
  - os imports dos módulos novos estão em `requirements.txt` (sem dependência nova).
- [X] T049 [P] Ampliar `tests/test_analyzer.py`:
  - as figuras 06 a 08 só são geradas com os dados correspondentes;
  - seções e abas novas só aparecem com os dados;
  - sem dados novos, saída igual à atual.
- [X] T050 [P] Atualizar `README.md`:
  - comandos `--complementares-only`, `--X-only`, `--dicionarios-only` e `--sem-X`;
  - bases novas e suas pastas;
  - dicionários;
  - cópia `.bak` em `data/processed/`;
  - código de saída 3;
  - histórico da spec 006.
- [X] T051 [P] Registrar no "Histórico de revisões" de `specs/001` a `specs/004` (`spec.md`) as mudanças desta feature, com cópia `.bak` antes de editar (constituição 1.2.0, Requisito Técnico 3(b)):
  - `specs/001-ons-coleta-sao-domingos/spec.md`: `.bak` da consolidação e dicionário da EVT;
  - `specs/002-tratamento-dados/spec.md`: `.bak` da base tratada e da validação física;
  - `specs/003-analise-dados/spec.md`: seções, constatações, abas e figuras 06 a 08;
  - `specs/004-conferencia-outros/spec.md`: `.bak` e dicionários nos indicadores e na programação.
- [X] T052 Executar `python -m pytest tests -q` sobre `tests/`. Esperado: suíte aprovada, sem rede e sem alterar arquivos do projeto.
- [X] T053 Executar o `specs/006-bases-complementares/quickstart.md` completo (passos 1 a 7).
  - Não regressão (SC-008):
    - Markdown das seções existentes igual ao de T002, ignorando a numeração;
    - abas existentes iguais célula a célula às da cópia de T001.
  - SC-009: menos de 10 min sem rede.
  - SC-010: até 13/10/2026.
  - Registrar tudo em "Registro de execução" e mudar o status de `specs/006-bases-complementares/spec.md` para "Implementado".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende da Phase 1 e **bloqueia todas as histórias**.
  - T006 depende de T005;
  - T008 depende de T003, T006 e T007.
- **Histórias (Phases 3 a 8)**: dependem da Phase 2.
- **Polish (Phase 9)**: depois das histórias desejadas. T053 é a última tarefa.

### User Story Dependencies

- **US1 (P1)**: só da Phase 2.
- **US2 (P1)**: só da Phase 2. Edita os mesmos `src/indicadores_ons.py`, `src/programacao_ons.py` e `src/main.py` que outras histórias, então essas edições são sequenciais, não paralelas.
- **US3 (P1)**: só da Phase 2. Usa a programação e os parâmetros TEIFa/TEIP já existentes (spec 004).
- **US4 (P1)**: só da Phase 2. Independe da US3. Se for implementada antes da US3, é ela quem cria `--complementares-only`.
- **US5 (P2)** e **US6 (P3)**: só da Phase 2.
- Arquivos compartilhados (`src/main.py`, `src/analyzer.py`, `src/pdf_generator.py`, `tests/integration/test_pipeline.py`): edições sequenciais na ordem das histórias.

### Within Each User Story

- Testes primeiro: devem falhar antes da implementação.
- Etapa de dados → funções de análise → CLI → relatório (`analyzer`) → PDF → validação real.

### Parallel Opportunities

- Phase 2: T003, T004, T005, T007 e T009 em paralelo (arquivos diferentes).
- US1: T011 a T015 em paralelo (cinco módulos diferentes), depois de T010.
- US2: T019 e T020 em paralelo (arquivos diferentes), depois de T018.
- US3: T025 em paralelo com T024. US4: T033 em paralelo com T032. US5: T040 em paralelo com T039. US6: T045 em paralelo com T044.
- Os testes de cada história (T010, T017, T022, T030, T038, T043) podem ser escritos em paralelo entre si.
- Polish: T048 a T051 em paralelo.

---

## Parallel Example: User Story 1

```text
Task: "T011 Gravação via persistência em src/consolidator.py"
Task: "T012 Gravação via persistência em src/processor.py"
Task: "T013 Gravação via persistência em src/validator.py"
Task: "T014 Gravação via persistência em src/indicadores_ons.py"
Task: "T015 Gravação via persistência em src/programacao_ons.py"
```

## Parallel Example: User Story 3

```text
Task: "T024 Funções de análise em src/disponibilidade_ons.py"
Task: "T025 Etapa 5 e modos novos em src/main.py + tests/integration/test_pipeline.py"
```

## Parallel Example: Phase 2

```text
Task: "T003 Constantes em src/config.py"
Task: "T004 Loggers em src/logger.py"
Task: "T005 Testes de contrato em tests/unit/test_persistencia.py"
Task: "T007 Testes do motor em tests/test_conjuntos_ons.py"
Task: "T009 Pontos de extensão em src/analyzer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 (cópia datada e linha de base) e Phase 2 (persistência, motor, constantes, loggers e pontos de extensão).
2. US1: todos os gravadores de `data/processed/` com `.bak`.
3. **Parar e validar**: T016. Execuções repetidas informam `INALTERADO` e não mudam hashes nem `.bak`.

### Pacote da fiscalização (P1, até 13/10/2026)

1. US1 → US2 (dicionários) → US3 (disponibilidade) → US4 (hidrologia).
2. Cada história é validada na base real antes da próxima (T016, T021, T029, T037).
3. Regenerar o relatório e conferir a não regressão das seções existentes.

### Incremental Delivery

- US5 (geração) e US6 (cadastro) depois de 13/10/2026, ou antes se houver folga.
- Nenhuma delas altera conclusões; ambas reforçam a rastreabilidade.
- Phase 9 ao final de cada entrega relevante. T053 fecha a feature.

---

## Notes

- **[P]** = arquivos diferentes, sem dependência pendente.
- **[USx]** = rastreabilidade com a spec.
- A base EVT local não é baixada de novo em nenhuma tarefa (decisão do usuário). Os modos `-only` e `--complementares-only` não tocam os dados da EVT.
- Gráficos só em seaborn, carregando a skill dataviz antes do código (constituição 1.2.0, Requisito Técnico 5).
- Toda gravação nova em `data/processed/` passa por `src/persistencia.py`. `reports/`, manifestos e dicionários ficam fora da regra do `.bak`.

---

## Registro de execução

### 05/10/2026 — Phase 1

- T001: cópia `_backup_2026-10-05_antes_spec006/` (193 arquivos: src, tests, specs, reports, .specify, README.md, requirements.txt; `conftest.py` bloqueia a coleta; `LEIA-ME.txt`).
- T002: linha de base com 87 testes aprovados (10,9 s). SHA-256 (16 primeiros dígitos) de referência para o SC-008:

| Arquivo | SHA-256 |
|---|---|
| data/processed/relatorio_auditoria_indicadores_ons.csv | 0723246975294c97 |
| data/processed/relatorio_auditoria_programacao_ons.csv | f6e16c18f2e885c7 |
| data/processed/relatorio_auditoria_varredura.csv | b4553ac0442248c8 |
| data/processed/relatorio_validacao_fisica.csv | 2e87e739e19b871e |
| data/processed/relatorio_validacao_fisica.md | bb297af6ef7d3e09 |
| data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv | a07f7d5fcac73225 |
| data/processed/uhe_sao_domingos_energia_vertida_tratado.csv | 0623a936ebd1e9f0 |
| data/processed/uhe_sao_domingos_energia_vertida_tratado.parquet | ebb59a26ac4815af |
| data/processed/uhe_sao_domingos_energia_vertida_tratado.xlsx | 68c69924fe6fc89d |
| data/processed/uhe_sao_domingos_indicadores_ons.xlsx | c4d2b0bce8802702 |
| data/processed/uhe_sao_domingos_ons_divergencias_indicadores.csv | 203adca34a7c5e4f |
| data/processed/uhe_sao_domingos_ons_programacao_dias_ausentes.csv | 4e0c39771060c675 |
| data/processed/uhe_sao_domingos_ons_programacao_horaria.csv | c13ef0c43aff7b20 |
| data/processed/uhe_sao_domingos_ons_teifa_teip_mensal.csv | f86c47b60856a7d3 |
| data/processed/uhe_sao_domingos_ons_ug_horas_estado_mensal.csv | b6c17b1d7dcd455a |
| data/processed/uhe_sao_domingos_ons_ug_indicadores_anual.csv | 30e646032fa2e974 |
| data/processed/uhe_sao_domingos_ons_ug_indicadores_mensal.csv | ad6da920024b6e04 |
| reports/relatorio_analise_estatistica.md | 6e9da09bd286510e |

### 05/10/2026 — Phase 2, US1 e US2

- Phase 2: `src/persistencia.py` (13 testes de contrato) e `src/conjuntos_ons.py` (14 testes); suíte com 114 testes aprovados.
- Defeito encontrado pelos testes e corrigido: `filecmp.cmp` guarda em cache o resultado por caminho, tamanho e data de modificação. Duas gravações do mesmo tamanho no mesmo instante eram dadas como "INALTERADO". A comparação passou a ser byte a byte, sem cache.
- T010–T015: os 5 gravadores passaram para a persistência. Os leitores de indicadores e programação passaram a aceitar tabela gravada sem colunas (antes levantavam `EmptyDataError`).
- T016, na base real (sem rede), com duas execuções da consolidação, do tratamento, dos indicadores e da programação:
  - os 14 arquivos determinísticos ficaram `INALTERADO`, com hash idêntico ao de T002;
  - as 2 planilhas ficaram `ALTERADO` só na 1ª execução (ganharam a assinatura) e `INALTERADO` na 2ª;
  - `relatorio_auditoria_varredura.csv` sai `ALTERADO` em toda execução, porque registra a data e hora do processamento (comportamento esperado);
  - nenhum `.tmp` ficou na pasta.
- T021: `python -m src.main --dicionarios-only`, duas vezes:
  - 1ª execução: 20 dicionários `NOVO` (148 KB só na EVT); 2ª: 20 `INALTERADO`;
  - a data de modificação dos CSV da EVT não mudou;
  - o registro tem 20 linhas.

### 05/10/2026 — US3 e US4 (P1 concluído)

- **US3** (`python -m src.main --disponibilidade-only`):
  - 98 arquivos baixados em cerca de 7 min: 53 CSV de 08/2018 a 12/2022 e 45 Parquet de 2023 em diante;
  - 70.895 horas, de 28/08/2018 a 28/09/2026;
  - nenhuma identificação parcial, nenhum valor inválido, nenhuma hora sinalizada;
  - 1 hora ausente (04/11/2018 00h, horário de verão, a mesma que falta na EVT).
- **Resultados da US3**:
  - a operacional coincide com a declarada da EVT em 100% das 70.895 horas;
  - das 5.443 horas paradas, 5.415 (99,5%) não tinham unidade sincronizada;
  - das 1.739 horas paradas com EVT e programação zero, 1.723 tinham as unidades desligadas;
  - a capacidade não sincronizada coincide com a reserva desligada TEIFa/TEIP (HRD × potência) de 2020 a 2023 e diverge em 2024 (−11,7 GWh), 2025 (−12,4 GWh) e 2026* (+4,1 GWh).
- **Figura 06**:
  - a skill dataviz foi carregada antes do código;
  - paleta validada pelo script: aqua, amarelo (posição 4) e azul passam em todos os critérios; o aviso de contraste abaixo de 3:1 é compensado com rótulo direto e tabela;
  - os rótulos diretos são omitidos quando as séries terminam próximas, e fica a legenda.
- **US4** (`python -m src.main --hidrologia-only`):
  - 98 arquivos: 97 Parquet e 1 CSV (07/2024 sem Parquet no catálogo);
  - 2024_05 aparece duplicado no catálogo; ficou o recurso com data de publicação;
  - 70.760 horas e 48 intervalos ausentes (136 h, listados);
  - alinhamento confirmado: 100% de 70.731 horas comuns.
- **Decisões tomadas sobre dados reais (US4)**:
  - **Exclusão campo a campo, não da hora inteira (FR-026)**. O volume útil negativo (2.319 h em 2019, na parada total com o reservatório rebaixado até cerca de 342 m) é rebaixamento real; excluir a hora inteira distorceria 2019.
  - **Regra nova H4**: nível de montante ou de jusante a mais de 10 m da mediana da série (`DESVIO_MAXIMO_NIVEL_M`). Ela pegou 13 leituras trocadas: montante de 308,67 m; jusante de 3,09, 395,9 e 730,9 m. Uma única leitura dessas criava um mergulho falso no perfil das 15h.
  - **Picos isolados de afluência** (2.270 m³/s em 20/11/2020, com defluência de 106 m³/s): registrados em nota; nenhuma regra inventada.
- **Resultados da US4**:
  - em 92,9% das 61.067 horas com EVT, a afluência cabia nas turbinas: 24,0% até uma unidade e 68,9% entre uma e duas;
  - nos 335 dias com parada com EVT, o nível ficou em 344,279 m e não subiu na janela das 9h às 15h, contra 344,321 m nos demais dias.
- **Figuras 07 e 08**:
  - 07 usa a rampa ordinal de laranja (validada com `--ordinal`);
  - 08 tem dois painéis, sem eixo duplo;
  - a vazão afluente ficou com violeta (posição 7), porque o magenta (posição 5) reprova o piso de visão normal contra o laranja em todos os pares (12,9 < 15);
  - o nível ficou em tinta neutra.
- **Planilha**: abas `DISP_CLASSES_PARADA`, `DISP_AUSENCIAS`, `HID_HORAS_EVT`, `HID_ANUAL` e `HID_AUSENCIAS`, além das previstas no contrato (atualizado na Phase 9).

### 05/10/2026 — US5, US6, Polish e validação final (feature concluída)

- **US5** (`python -m src.main --geracao-only`):
  - 61 arquivos Parquet (anuais de 2018 a 2021 e mensais de 01/2022 em diante);
  - a geração coincide com a da base de EVT em 100% das 70.895 horas comuns, sem divergência;
  - energia do período: 1.919,577 GWh nas duas fontes (diferença de 0,019 MWh, arredondamento);
  - sem divergência, a conferência aparece só como seção, sem constatação.
- **US6** (`python -m src.main --cadastro-only`):
  - ficha: UHE SÃO DOMINGOS, CEG UHE.PH.MS.028761-0.01, id ONS MSUHSD, TIPO II-A, COSR-S, SE ÁGUA CLARA 138 KV, 48 MW, MS, situação "A";
  - 20 homônimos excluídos pelo CEG; nenhuma divergência com os parâmetros do projeto, por isso sem constatação.
- **Polish** (T048 a T051): testes de conformidade e do analyzer ampliados, `README.md` atualizado e histórico das specs 001 a 004 registrado, com `.bak`.
- **T052**: 167 testes aprovados em 24 s, com a rede bloqueada (proxy inexistente). Nenhum dos 124 arquivos vigiados mudou (`data/processed/`, `reports/`, manifestos e EVT bruta).
- **T053, passos do quickstart**:
  - passo 1: igual à T052;
  - passo 2 (`--programacao-only`, duas vezes, 26 s e 28 s):
    - 708 arquivos do cache; as 3 saídas da programação `INALTERADO` nas duas execuções, com os `.bak` intactos (data e hash);
    - o registro de dicionários sai `ALTERADO` a cada coleta, porque guarda a hora da obtenção. É o comportamento esperado, como na auditoria da varredura;
  - passo 3 (`--dicionarios-only`, 36 s): 20 dicionários `INALTERADO`; EVT bruta intacta;
  - passo 4 (`--complementares-only`, 181 s, saída 0):
    - base EVT intacta;
    - auditorias com todos os arquivos `PROCESSADO`: disponibilidade com 53 CSV (2018-08 a 2022-12) e 45 Parquet (2023-01 a 2026-09); hidrologia com 97 Parquet e 1 CSV (2024-07); geração com 61 Parquet;
    - nenhuma linha com identificação parcial em nenhuma base (SC-002); alinhamento hidrológico de 100% em 70.731 horas (SC-003);
    - o cadastro saiu `ALTERADO` porque o ONS republicou `MODALIDADE_USINA.csv` em 05/10/2026 às 15:05 UTC (4 linhas a mais e linhas reordenadas, de outras usinas). A versão anterior ficou em `data/raw/modalidade_usina/_versoes_anteriores/MODALIDADE_USINA__pub_20261004T220450.csv`; na ficha da usina, só a data da consulta mudou;
    - um arquivo da hidrologia voltou republicado (`UPDATED`) com conteúdo idêntico (mesmo SHA-256), por isso nenhuma versão anterior foi preservada;
  - SC-009 (`--filter-only`, com a rede bloqueada): 219 s (3 min 39 s), saída 0. As 22 saídas ficaram `INALTERADO`; só a auditoria da varredura saiu `ALTERADO` (hora do processamento);
  - passo 5 (`python -m src.analyzer`, 21 s): 16 seções, 17 constatações (2 novas: disponibilidade sincronizada e afluência), 8 figuras e 54 abas, com o PDF regenerado:
    - soma das classes das horas paradas = 5.443 = linhas de `DISP_HORAS_PARADAS` = horas paradas de `DISP_ANUAL` = horas com geração até 1 MW na base tratada (SC-005);
    - soma das faixas de afluência = 61.067 = linhas de `HID_HORAS_EVT` = horas com EVT da base tratada no período da hidrologia;
    - 33 trechos com números e dados cadastrais das seções novas conferidos com a planilha, sem diferença (SC-008);
  - passo 6 (não regressão contra `_backup_2026-10-05_antes_spec006/reports/`, numeração ignorada):
    - Markdown: cabeçalho e 10 das 12 seções existentes com texto idêntico; em "Constatações", as 15 anteriores idênticas; em "Figuras", só o acréscimo das figuras 06 a 08;
    - planilha: as 32 abas existentes idênticas célula a célula (em `PARAMETROS`, as linhas novas vêm depois das anteriores; em `CONSTATACOES`, as 15 anteriores estão presentes);
  - passo 7 (SC-010): P1 (US1 a US4), US5 e US6 concluídas em 05/10/2026, antes do prazo de 13/10/2026.
- **Status**: `spec.md` passou a "Implementado (05/10/2026)", com cópia `spec.md.2026-10-05-impl.bak`.

### 05/10/2026 — Convergência (T054 a T061)

- **Cópia datada**: `_backup_2026-10-05_antes_convergencia006/` (220 arquivos), antes de alterar código, testes e documentos.
- **T054**: `linhas_formato_irregular` e `ler_csv_texto` em `src/conjuntos_ons.py`, com o mesmo critério da EVT (spec 005):
  - as linhas não vazias com nº de campos diferente do cabeçalho ficam fora da leitura, são contadas na coluna nova `linhas_formato_irregular` da auditoria e são avisadas no log (arquivo, quantidade e primeiras linhas);
  - o cadastro usa o mesmo leitor e não falha mais por uma linha longa de outra usina;
  - na base real, 0 linhas irregulares nas auditorias de disponibilidade (98 arquivos), hidrologia (98) e geração (61) e no cadastro.
- **T055**: tabela anual de EVT (MWh) por faixa no Markdown e no PDF, com a mesma estrutura da tabela de horas, e aba `HID_FAIXAS_ANUAL`. Na base real:
  - 147.651 MWh de EVT nas 61.067 horas com EVT; 137.691 MWh (93,3%) com afluência que cabia nas turbinas;
  - em 2025 e 2026*, mais da metade da EVT ocorreu com afluência de até uma unidade (15.950 de 30.690 MWh e 16.189 de 25.972 MWh).
- **T056**: `notas_bases_complementares` acrescenta à relação de fontes (notas metodológicas do Markdown e do PDF) as 4 bases, com link, identificador, período e data de obtenção; as 17 notas anteriores ficaram idênticas e na mesma ordem.
- **T057**: legenda da tabela anual da hidrologia e docstrings de `resumo_mensal` e `resumir` corrigidas (exclusão só no campo afetado).
- **T058**: tabela de identificação do PDF com a data da consulta (05/10/2026 15:07 UTC) e nota da fonte mantida quando há divergência (`pares_identificacao_cadastro` e `nota_identificacao_cadastro`).
- **T059**: `relatorio_auditoria_cadastro_ons.csv` (`NOVO`: `PROCESSADO`, 6.017 linhas lidas, 1 da usina, 0 irregulares, identificação parcial 0/0) e aba `CAD_AUDITORIA`; a falha de leitura do cadastro passou a dar código 2, como nas demais etapas.
- **T060 e T061**: data-model (seções 2, 3, 5, 7, 8, 9 e 10), `contracts/cli-contract.md` e `README.md` atualizados. O PDF da disponibilidade fica com a tabela anual e a figura 06 mensal; o estado `NAO_OBTIDO` está documentado.
- **Testes**: 174 aprovados (7 novos) em 24 s, com a rede bloqueada.
- **Base real** (`python -m src.main --filter-only`, com a rede bloqueada): saída 0 em 238 s (antes, 219 s; a varredura das linhas irregulares acrescentou cerca de 19 s).
  - 19 saídas `INALTERADO`;
  - `ALTERADO` só nas 3 auditorias (coluna nova) e na da varredura (hora do processamento);
  - `NOVO` na auditoria do cadastro.
- **Relatório** (`python -m src.analyzer`, 22 s): 16 seções, 17 constatações, 8 figuras e 56 abas; PDF com 27 páginas (26 antes).
  - Não regressão contra `_backup_2026-10-05_antes_spec006/`: constatações, notas e abas existentes idênticas.
  - Conferências do passo 5 do quickstart e da convergência sem diferença.

### 05/10/2026 — Segunda convergência (T062)

- **Cópia datada**: `_backup_2026-10-05_antes_t062/` (arquivos alterados e relatório vigente).
- **T062**: a constatação de afluência (`_achado_afluencia`) passou a terminar com a ressalva de que a afluência e o nível mostram a água disponível e o comportamento do reservatório, mas não o motivo das paradas, que depende de informação do agente (FR-031), como o texto da disponibilidade. A frase não entra no texto de falha de alinhamento, que não trata de paradas.
  - Teste primeiro (falhou como esperado) e depois o código; 174 testes aprovados com a rede bloqueada.
  - Relatório regenerado (`python -m src.analyzer`, 22 s): a ressalva aparece nas Constatações, na seção da hidrologia, no PDF e na aba `CONSTATACOES`. Não regressão e conferências sem diferença.

---

## Phase 10: Convergence

- [X] T054 CRITICAL: Contar na auditoria, avisar no log e não extrair as linhas não vazias com número de campos diferente do cabeçalho nos CSV das bases novas, em `src/conjuntos_ons.py` (`_ler_csv` e `ler_arquivo`) e em `src/cadastro_ons.py` (`ler_cadastro`) per Constitution IV (contradicts)
  - Hoje, no motor comum, a linha curta entra com os campos que faltam vazios e o campo excedente é descartado sem aviso; no cadastro, a linha curta entra sem aviso e a longa derruba a etapa com `ParserError` (código 1).
  - Seguir a filtragem da EVT (spec 005, FR-009): coluna nova de contagem por arquivo em `relatorio_auditoria_<conjunto>_ons.csv` (no cadastro, na auditoria criada pela T059) e aviso no log com o arquivo, a quantidade e o número das primeiras linhas; a etapa do cadastro não deve falhar por uma linha irregular de outra usina.
  - Testes sem rede com uma linha curta e uma longa. Nos 55 CSV atuais (9,3 milhões de linhas, conferidos em 05/10/2026) a contagem esperada é zero, sem mudança nos números do relatório (SC-008).
- [X] T055 Apresentar a EVT (MWh) por faixa de afluência e por ano: acrescentar a EVT por faixa à tabela anual de faixas (`linhas_tabela_faixas_afluencia` em `src/analyzer.py`, no Markdown e no PDF) e exportar `faixas_anual` numa aba nova `HID_FAIXAS_ANUAL` per FR-023 (partial)
  - Hoje `faixas_anual` é calculada em `analisar_hidrologia`, mas a tabela anual e a figura 07 mostram só horas, e a planilha só traz as faixas mensais (`HID_FAIXAS_AFLUENCIA`); a US4/AC3 pede horas e EVT por faixa, por mês e por ano.
  - Teste: em cada ano, a soma da EVT das faixas é igual à EVT das horas com EVT do período comum. Atualizar a lista de abas em `contracts/cli-contract.md`. Números existentes inalterados (SC-008).
- [X] T056 Incluir as quatro bases novas na relação de fontes do Markdown (seção "Notas metodológicas e limitações", `notas_metodologicas` em `src/analyzer.py`), cada uma com o link do conjunto, o identificador da usina, o período coberto e a data de obtenção, só quando a base estiver carregada per FR-034 (partial)
  - No PDF e na aba `PARAMETROS` elas já constam (tabela "Parâmetros utilizados"); no Markdown, que não tem essa tabela, a fonte aparece só dentro de cada seção e sem o link, ao contrário de EVT, indicadores e programação.
- [X] T057 Corrigir os textos que ainda descrevem a exclusão da hora inteira na hidrologia: a legenda "Médias das horas sem sinalização" da tabela anual no Markdown (`src/analyzer.py`, seção da hidrologia) e as docstrings de `resumo_mensal` e `resumir` (`src/hidrologia_ons.py`), pois os valores sinalizados saem só do campo afetado (`_limpos`; data-model, seção 10) per FR-026 (contradicts)
- [X] T058 Mostrar a data da consulta na tabela de identificação da usina do PDF (`_secao_cadastro` em `src/pdf_generator.py`) e manter a ressalva "cadastro sem série histórica" também quando houver divergência (hoje a nota da divergência substitui a da fonte) per US6/AC4 (partial)
- [X] T059 Gravar pela persistência a auditoria da leitura do cadastro, `relatorio_auditoria_cadastro_ons.csv` (arquivo, linhas lidas, linhas da usina, identificação parcial, linhas irregulares da T054, situação `PROCESSADO` | `SEM_REGISTROS` | `FALHA` e mensagem), em `src/cadastro_ons.py`, com a aba `CAD_AUDITORIA` em `src/analyzer.py` e o data-model (seções 7 e 9) e o `contracts/cli-contract.md` atualizados per FR-005 (partial)
- [X] T060 Registrar no data-model (seção 10) que a seção de disponibilidade do PDF traz a tabela anual e a figura 06 (mensal), com o detalhe mensal na aba `DISP_MENSAL`, no lugar da tabela mensal prevista na T028 — ou, se o usuário preferir, incluir a tabela mensal em `_secao_disponibilidade_sincronizada` (`src/pdf_generator.py`) per T028 (partial)
- [X] T061 Documentar no data-model (seção 2) o resultado `NAO_OBTIDO` do registro de dicionários (conjunto ainda não consultado), produzido por `montar_registro` em `src/dicionarios_ons.py` e ausente da FR-014, das tarefas e do data-model per FR-014 (unrequested)

---

## Phase 11: Convergence

- [X] T062 Acrescentar ao texto da constatação de afluência (`_achado_afluencia` em `src/analyzer.py`, que aparece nas Constatações, na seção da hidrologia do Markdown e no PDF) a ressalva de que os dados hidrológicos mostram a água que chegou e o nível do reservatório, mas não o motivo das paradas, que depende de informação do agente, com teste em `tests/test_relatorio_complementar.py` per FR-031 (partial)
  - Hoje a constatação fala dos "dias com parada com EVT" e conclui que a água "cabia nas turbinas", terminando só com a ressalva de dados não consistidos; o texto da disponibilidade já traz a dele ("a sincronização mostra se as unidades estavam ligadas à rede, mas não o motivo da parada").
  - Só no caso publicado (alinhamento confirmado), sem mudança nos números das seções existentes (SC-008).
