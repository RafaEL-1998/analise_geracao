---

description: "Task list for feature 006 — relatórios de desempenho para todos os tipos de usina com dados abertos do ONS"
---

# Tasks: Relatórios de Desempenho para Todos os Tipos de Usina com Dados Abertos do ONS

**Input**: Design documents from `/specs/006-ampliacao-tipos-de-geracao/`

**Prerequisites**: plan.md, spec.md, research.md (achados A1 a A14 e B1 a B7; decisões R1 a R30), data-model.md, contracts/ (cli-usinas.md, cli-perfil.md, cli-carteira.md, cli-referencias.md, perfil-multitipo.md), quickstart.md

**Prazo**: por decisão do usuário de 09/10/2026, a implementação começa antes da fiscalização de 14 a 16/10/2026. A T001 congela e confere a versão de fiscalização da São Domingos fora do projeto (FR-028). É ela a usada na fiscalização, com os próprios dados.

**Tests**:
- Incluídos: a constituição exige testes sem rede, uma usina fictícia por tipo e nenhuma perda de cobertura (Qualidade 1). O plano pede ainda os invariantes das hidrelétricas com EVT (decisão R29) e as etapas 2 a 5 com `data/raw/` vazio (decisão R22).
- Dentro de cada fase, os testes vêm antes e devem falhar antes da implementação, salvo os de invariantes, que passam desde o início e precisam continuar passando.
- Comando, sempre sem rede:

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:9"; $env:HTTPS_PROXY = "http://127.0.0.1:9"; $env:PYTHONIOENCODING = "utf-8"
python -m pytest tests -q -p no:cacheprovider
```

**Organization**:
- Uma fase do plano por história (decisão R27): A = US1, B = US2, C = US3, D = US4, E = US5, F = fechamento.
- A fase A se divide em duas partes:
  - a fundação de proteção e da Coleta (itens 1 a 4 do plano), que bloqueia tudo: Phase 2 deste arquivo;
  - o catálogo, o perfil e o relatório com as seções comuns (itens 5 a 10): Phase 3, a US1.
- **Início de toda fase**:
  - cópia de segurança;
  - rascunhos dos ajustes das specs das etapas em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/`, aprovados pelo usuário antes de qualquer código (decisão R26).
- **Fim de toda fase** (portão):
  - a suíte sem rede;
  - `pyflakes` de fora do `venv`, em `src/` e `tests/` (instalado com `pip install --target <pasta temporária> pyflakes` e usado com `PYTHONPATH` apontando para ela, sem entrar no `requirements.txt`);
  - `/speckit-converge`;
  - `python -m src comparar --todas --coleta` com código 0;
  - as aprovações do usuário da fase.
- Toda evidência (comando, data, resultado) vai para "Registro de execução", no fim deste arquivo.

**Nomenclatura**:
- **"decisão Rn"**: decisão do [research.md](research.md). **"regra Rn"**: regra de validação física R1 a R9 do Tratamento.
- **"achado An" ou "Bn"**: achados do research.
- **"Gn"**: conferências novas. **"Cn"**: regras da conclusão.

**Regras permanentes** (memória do projeto e constituição):
- **Git**: nunca fazer commit; sugerir a mensagem.
- **Cópias de segurança**: no máximo duas; nenhum `.bak` solto.
- **Figuras**: toda figura em seaborn, com a paleta central.
- **Relatório aprovado**: nenhuma mudança sem aprovação do usuário.
- **Fonte**: não citar o modelo de RF de 2026 como fonte.
- **Base local**: a base de EVT local é mantida, sem novo download, até a migração (T026).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem depender de tarefa pendente).
- **[Story]**: história da spec (US1 a US5).

## Path Conventions

- **Código**: `src/` e `tests/` na raiz do projeto. Os módulos novos e alterados estão no plan.md (Project Structure).
- **Documentos desta feature**: `specs/006-ampliacao-tipos-de-geracao/`.
- **Scripts de apoio**: no scratchpad da sessão, nunca em `src/`. Python sempre escrito com a ferramenta de arquivo, não com heredoc do bash.

---

## Phase 1: Setup (preparação da fase A)

**Purpose**: conferir as pré-condições, guardar o estado aprovado e aprovar os ajustes das specs da fase A antes de qualquer código.

- [X] T001 Congelar e conferir a versão de fiscalização (FR-028) e as pré-condições; registrar em `specs/006-ampliacao-tipos-de-geracao/tasks.md` ("Registro de execução"):
  - **pasta**: `C:\Users\rlazaro\Desktop\UHE_SAO_DOMINGOS_versao_fiscalizacao`, fora do projeto, com `src/` e `tests/` do commit aprovado `c82a64e` (sem mudanças pendentes), `usinas/sao_domingos/perfil.toml`, `data/raw/`, `data/usinas/sao_domingos/`, `reports/sao_domingos/`, `README.md`, `requirements.txt` e um `LEIA-ME.txt` com o uso;
  - **conferência**: nessa pasta, com o Python do `venv` do projeto, `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"` com código 0 e `python -m src comparar --usina sao_domingos --referencia <projeto>\_backup_2026-10-08_antes_ampliacao_tipos_de_geracao\linha_de_base` com "Nenhuma diferença.";
  - **projeto principal**: nenhuma coleta com o portal depois de 08/10/2026. Usar um script no scratchpad que lê todos os `_manifesto_ons.json` de `data/raw/`, inclusive os de `_dicionarios/`, e mostra o maior `registrado_em_utc` e o maior `obtido_em_utc`. Com registro posterior, parar e levar ao usuário (decisão R22).
- [X] T002 Criar a cópia de segurança com `python -m src copia-seguranca --motivo antes_fase_A`, ainda com o código de hoje.
  - Conferir que ficam duas cópias: `_backup_2026-10-08_antes_ampliacao_tipos_de_geracao/`, com `linha_de_base/`, e a nova.
  - `_backup_2026-10-08_antes_ajustes_t072/` sai pela poda.
- [X] T003 Registrar a linha de base:
  - a suíte sem rede (esperado: 396 aprovados);
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base` com código 0;
  - as páginas do PDF (30), a quantidade de abas da planilha e o SHA-256 das figuras de `reports/sao_domingos/figures/`.
- [X] T004 [P] Escrever `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md` (fase A), já na redação final da spec da Coleta:
  - a Coleta no formato 2, com `datas_obtencao.csv` e `dicionario_evt.json` (decisão R22; data-model 6.1);
  - as correções P1 a P5 (decisão R10);
  - o registro dos conjuntos, os dicionários por usina e a UHE sem `[cobertura]` (decisão R8);
  - o perfil por tipo e a tabela `[cobertura]` (decisão R4; contracts/perfil-multitipo.md);
  - o catálogo e o comando `usinas` (decisões R1 a R3; contracts/cli-usinas.md);
  - o comando `perfil` (decisão R5; contracts/cli-perfil.md);
  - a série de referência e os trechos, com as linhas da fase A (decisões R6, R7);
  - os comandos comuns `referencia`, `comparar --todas [--coleta]` e a `copia-seguranca` com as referências (decisão R22; contracts/cli-referencias.md);
  - a tabela de aplicabilidade por tipo dos conjuntos da fase A (FR-002).
- [X] T005 [P] Escrever `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/002-tratamento-dados.md` (fase A):
  - o dicionário da EVT lido da Coleta (achado B1);
  - a base horária comum das usinas sem EVT, com as colunas da T055 (decisão R30);
  - as regras de duplicatas e ausências também no panorama dos agregados (decisão R11);
  - a tabela de aplicabilidade por tipo.
- [X] T006 [P] Escrever `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/003-conferencia.md` (fase A):
  - `nao_aplicaveis.csv`, com todas as conferências do catálogo que não se aplicam, inclusive na UHE, e fora do relatório dela (decisão R13);
  - a tabela de aplicabilidade por tipo.
- [X] T007 [P] Escrever `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/004-analises.md` (fase A):
  - as datas e o resumo do manifesto lidos da Coleta (achado B1);
  - os dois caminhos: hidrelétrica com EVT e usina sem EVT (decisão R14);
  - as seções comuns sobre a base horária comum (decisão R30);
  - o período mínimo (decisão R17);
  - o catálogo da conclusão com `tipos`, `listas` e `nivel_exigido` (decisão R16);
  - os campos novos de `ResultadosAnalise` da fase A (data-model 6.4).
- [X] T008 [P] Escrever `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/005-geracao-relatorio.md` (fase A):
  - a estrutura por caminho (decisão R14);
  - o título e a capa por caminho (data-model 6.5);
  - as legendas com o nível (decisão R15);
  - as notas com as omissões, os níveis e as conferências não aplicáveis;
  - os invariantes das hidrelétricas com EVT (decisão R29);
  - a ferramenta `comparar --todas [--coleta]` (decisão R22).
- [X] T009 Levar ao usuário os cinco rascunhos das T004 a T008 e registrar a aprovação, com a data, em `specs/006-ampliacao-tipos-de-geracao/tasks.md`.
  - Nenhum código da fase A antes disso.
  - Pedido de mudança: ajustar o rascunho e pedir a aprovação de novo.

**Checkpoint**: estado aprovado guardado; rascunhos da fase A aprovados.

---

## Phase 2: Foundational (fase A, itens 1 a 4 — proteção e Coleta)

**Purpose**: proteger os relatórios aprovados e preparar a Coleta antes de qualquer download de outra usina (decisão R22). Bloqueia todas as histórias.

**⚠️ CRITICAL**, no projeto principal (a versão de fiscalização é independente):
- Até a T026 (migração), nenhuma coleta com o portal.
- Até a T043 (novo congelamento), nenhum `usinas` nem coleta de outra usina.

### Testes da proteção (item 1)

- [X] T010 Gerar a fotografia dos invariantes, com o código de hoje, antes de qualquer mudança: `tests/fixtures/invariantes_uhe.json`.
  - O gerador é um script de teste em `tests/fixtures/gerar_invariantes_uhe.py`, sem `test_` no nome, que roda o fluxo completo da usina fictícia de `tests/fixtures/usina_ficticia/` sem rede e grava:
    - chaves, títulos e ordem das seções;
    - título e blocos da capa;
    - textos das legendas, com as datas trocadas por um marcador;
    - lista das notas;
    - texto de `nota_conclusao()`;
    - códigos, listas e ordem dos itens da conclusão;
    - abas da planilha com as colunas de cada uma;
    - conjuntos da aba DICIONARIOS, na ordem;
    - arquivos da Coleta com as colunas de cada um.
- [X] T011 [P] Escrever `tests/relatorio/test_invariantes_uhe.py`, com um teste por invariante da decisão R29, comparando a saída atual da usina fictícia com `tests/fixtures/invariantes_uhe.json`:
  - os nove invariantes da tabela da decisão R29;
  - a Coleta da UHE pode ganhar só `datas_obtencao.csv` e `dicionario_evt.json`.
  - Os testes passam com o código de hoje (são de regressão).
- [X] T012 [P] Escrever `tests/comum/test_referencias.py` para o comando `referencia` (contracts/cli-referencias.md). Casos:
  - **exige**: o relatório `concluida` e não `desatualizada`, gerado com a data de `--data-geracao`; e a Coleta `concluida` no formato atual;
  - **grava**: numa pasta temporária e depois troca. Congela só os arquivos listados no `etapa.json` da Coleta e o próprio `etapa.json`, sem `.bak`; copia `perfil.toml`;
  - **`referencia.json`**: campos `usina`, `data_geracao` ("DD/MM/AAAA HH:MM"), `aprovado_em`, `periodo`, `arquivos` (nome, bytes e SHA-256), `perfil` (SHA-256) e `coleta` (nome, bytes e SHA-256);
  - **recusa**: substituir uma referência com mudanças fora do git (função de conferência do git simulada no teste);
  - **códigos**: 0, 1, 2, 4 e 5.
- [X] T013 [P] Ampliar `tests/comum/test_comparacao.py` para `comparar --todas [--coleta]`, com a usina fictícia:
  - **`--todas`**:
    - refaz as etapas 2 a 5 num espaço isolado, a partir da Coleta e do perfil congelados;
    - ignora `referencia.json`, `perfil.toml` e `coleta/`;
    - avisa "perfil alterado" sem o código 6;
    - não muda nenhum arquivo de `data/usinas/`, `reports/` e `data/raw/` (SHA-256 e datas antes e depois).
  - **`--coleta`**:
    - compara as séries só no período da referência;
    - nas auditorias, compara só as contagens, sem as colunas de execução;
    - trata `dicionarios.csv` e `datas_obtencao.csv` só como informação;
    - as etapas 2 a 5 continuam partindo da Coleta congelada.
  - **Códigos**: 0, 1, 2 (`--usina` com `--todas`, ou nenhum dos dois) e 6.
- [X] T014 [P] Ampliar `tests/comum/test_copia_seguranca.py`:
  - `relatorios_referencia/` é copiada inteira e conferida pelos SHA-256 do `referencia.json`;
  - em falha, a cópia nova sai e nenhuma outra é excluída;
  - o `LEIA-ME.txt` lista as referências, com a data de geração e a de aprovação.
- [X] T015 [P] Escrever `tests/coleta/test_datas_obtencao.py`:
  - `datas_obtencao.csv` com as colunas `conjunto`, `arquivos_registrados`, `publicacao_mais_recente` e `obtencao_mais_recente`, calculadas só com os arquivos do escopo da usina (um arquivo fora do escopo no manifesto não muda nada);
  - `dicionario_evt.json` copiado para a pasta da Coleta;
  - `VERSAO_FORMATO["coleta"] == 2`;
  - o Tratamento recusa a Coleta no formato 1 com o código 5.
- [X] T016 [P] Escrever `tests/integracao/test_sem_raw.py`:
  - roda a Coleta da usina fictícia com `--sem-portal`;
  - esvazia `RAW_DATA_DIR` (pasta temporária);
  - roda o Tratamento, a Conferência, as Análises e o Relatório: código 0 e relatório igual ao gerado com `data/raw/` presente.

### Implementação da proteção (item 1)

- [X] T017 Em `src/comum/caminhos.py` e `src/comum/perfil.py`:
  - função ou contexto que troca, durante uma execução, as raízes `DATA_DIR`, `RAW_DATA_DIR`, `REPORTS_DIR`, `USINAS_DIR` e `perfil.RAIZ_PROJETO` por um espaço isolado (o mesmo redirecionamento que os testes já fazem);
  - as constantes `RELATORIOS_REFERENCIA_DIR` e `CATALOGO_DIR` (`data/catalogo/`), e `PASTA_CARTEIRAS` (`reports/carteiras/`);
  - em `ARQUIVOS_COLETA`, as chaves `datas_obtencao` e `dicionario_evt`.
- [X] T018 Passar a Coleta ao formato 2 em `src/coleta/etapa.py` e `src/coleta/conjuntos.py`, com `VERSAO_FORMATO["coleta"] = 2` em `src/pipeline.py`:
  - gravar `datas_obtencao.csv`. Por conjunto: os arquivos registrados no manifesto que estão no escopo da usina (os da auditoria), a maior `ultima_modificacao` e o maior `registrado_em_utc` desses arquivos;
  - copiar `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json` para `dicionario_evt.json`, nas usinas com EVT;
  - os dois pela `persistencia`, com `.bak`, como os demais arquivos da Coleta.
- [X] T019 Fazer o Tratamento ler o dicionário da Coleta: em `src/tratamento/validacao.py` (`carregar_dicionario_dados` e a função da linha 97 com o mesmo padrão), o caminho padrão passa a ser `data/usinas/<slug>/coleta/dicionario_evt.json`; ajustar `src/tratamento/evt.py` e `src/tratamento/etapa.py`.
- [X] T020 Fazer as Análises e o Relatório lerem as datas e o resumo do manifesto da Coleta, nunca de `data/raw/`:
  - `src/analises/geracao.py`, `disponibilidade.py` e `hidrologia.py`: `obtido_em` vindo de `datas_obtencao.csv`;
  - `src/analises/cobertura.py` (`_resumo_manifesto`) e `src/analises/etapa.py`: a linha "Versão dos arquivos" vinda de `datas_obtencao.csv`, conjunto da EVT;
  - `src/relatorio/fontes.py` (`datas_obtencao`, `origem_dos_dados`): as datas vindas das Análises.
  - Os valores da São Domingos têm de ficar iguais (T011 e T016).
- [X] T021 Criar `src/comum/referencias.py` com o comando `referencia` (contracts/cli-referencias.md):
  - as exigências e a gravação da T012;
  - a conferência do git com `git status --porcelain -- relatorios_referencia/<slug>`, chamado do Python;
  - a sugestão de commit no fim;
  - as mensagens obrigatórias do contrato.
- [X] T022 Implementar `comparar --todas [--coleta]` em `src/comum/comparacao.py`:
  - o espaço isolado da T017;
  - as etapas 2 a 5 por `src/pipeline.py`, com o perfil congelado e a data do `referencia.json`;
  - a comparação de hoje para o relatório;
  - as regras do `--coleta` da T013;
  - as mensagens obrigatórias do contrato.
- [X] T023 Em `src/comum/copia_seguranca.py`: copiar `relatorios_referencia/` para a cópia nova, conferir pelos `referencia.json` antes da poda e listar as referências no `LEIA-ME.txt` (T014).
- [X] T024 Em `src/__main__.py`:
  - o comando `referencia --usina --data-geracao --aprovado-em`;
  - em `comparar`, o modo `--todas [--coleta]`, exclusivo com `--usina`/`--referencia` (código 2 pelo argparse);
  - atualizar a docstring dos comandos.
- [X] T025 Atualizar `.gitignore`:
  - exceção `!relatorios_referencia/**/*.pdf`, para os PDFs aprovados;
  - exclusão de `relatorios_referencia/*/coleta/`.
  - Conferir com `git check-ignore -v` que o PDF entra e a Coleta congelada não.

### Migração da referência da São Domingos (item 2)

- [X] T026 Rodar a suíte (T010 a T016 aprovados) e, em seguida, a migração (decisão R22, quickstart 3.1):
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`;
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base` com código 0;
  - `python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "08/10/2026"`;
  - `python -m src comparar --todas --coleta` com código 0.
  - Conferir `relatorios_referencia/sao_domingos/`: relatório, `perfil.toml`, `coleta/` sem `.bak` e com `datas_obtencao.csv` e `dicionario_evt.json`, e `referencia.json`.
  - Registrar. Pedir ao usuário o commit de `relatorios_referencia/sao_domingos/`, sem fazê-lo.

### Correções P1 a P5 da Coleta (item 3; decisão R10)

- [X] T027 [P] Escrever `tests/coleta/test_correcoes_p1_p5.py`, com catálogo CKAN e arquivos sintéticos:
  - **P1**: EVT, indicadores e programação escolhem um recurso entre os repetidos, pela regra de `selecionar_recursos`, e o arquivo temporário leva o id do recurso;
  - **P2**: a vírgula decimal é aceita nos conjuntos horários e na potência da ficha;
  - **P3**: texto com acento, espaços e caixa diferentes é encontrado na EVT, na programação e no filtro do Parquet da geração;
  - **P4**: a coluna de conferência ausente torna o arquivo `FALHA`, com o motivo;
  - **P5**: o CSV vazio da EVT tem o motivo "arquivo vazio" na auditoria.
- [X] T028 P1 em `src/coleta/catalogo.py`, `src/coleta/evt.py`, `src/coleta/indicadores.py` e `src/coleta/programacao.py`:
  - aplicar a escolha de `selecionar_recursos` (`src/coleta/conjuntos.py`) antes dos downloads;
  - o `<arquivo>.part` passa a incluir o id do recurso.
- [X] T029 [P] P2: uma função comum de leitura numérica, que aceita vírgula e ponto, usada em `src/coleta/conjuntos.py` (`extrair_arquivo`) e em `src/coleta/cadastro.py` (potência autorizada).
- [X] T030 P3: uma normalização única (sem acento, sem espaços nas pontas, maiúsculas), aplicada:
  - ao pré-teste do nome em `src/coleta/evt.py`;
  - ao código e ao estado em `src/coleta/programacao.py`;
  - ao filtro do Parquet em `src/coleta/conjuntos.py`, que passa a usar o valor publicado e o normalizado.
- [X] T031 P4 em `src/coleta/conjuntos.py`: num conjunto com conferência declarada, a coluna ausente vira `FALHA` com a mensagem `coluna de conferência ausente: <coluna>`.
- [X] T032 P5 em `src/coleta/evt.py`: o CSV sem linhas de dados fica `FALHA` com a mensagem "arquivo vazio" na auditoria.
- [X] T033 Portão das correções: suíte; `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`; `python -m src comparar --todas --coleta` com código 0. Registrar.

### Registro dos conjuntos (item 3; decisão R8)

- [X] T034 [P] Escrever `tests/coleta/test_registro.py`:
  - **Registro**: as entradas dos dez conjuntos de hoje reproduzem as `DescricaoConjunto` atuais (identificador, conferências, colunas de valor, convenção de hora, filtro do Parquet);
  - **Filtro por tipo e cobertura** (FR-015);
  - **Derivados**: `CONJUNTOS_PIPELINE` sai do registro;
  - **Dicionários**: o registro dos dicionários de uma UHE sem `[cobertura]` tem exatamente os dez conjuntos de hoje, na mesma ordem (duas linhas por conjunto);
  - **Coleta da UHE sem `[cobertura]`**: não pede Composição nem Capacidade.
- [X] T035 Criar `src/coleta/registro.py`, com a `DescricaoConjunto` ampliada e as entradas de hoje:
  - campos novos: `chave`, `tipos`, `nivel` (usina, conjunto ou agregado), `resolucao` (`horaria`, `semi_horaria`, `semanal`, `mensal_anual`, `estatica`), `referencia` e `variantes`;
  - as entradas `evt`, `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao` e `cadastro`, com os tipos da tabela do data-model, seção 4;
  - ajustar `src/coleta/conjuntos.py` (`descricoes` passa a vir do registro) e `src/comum/regras.py` (`CONJUNTOS_PIPELINE` derivado).
- [X] T036 Usar o registro na Coleta e nos dicionários:
  - `src/coleta/etapa.py` percorre o registro filtrado pelo tipo e pela cobertura;
  - `src/coleta/dicionarios.py` (`montar_registro`) lista só os conjuntos da usina;
  - `src/relatorio/fontes.py` monta as abas DICIONARIOS e FONTES com os conjuntos da usina.
  - Para a UHE sem `[cobertura]`, tudo igual a hoje (T011).
- [X] T037 Portão do registro:
  - suíte;
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`;
  - `python -m src comparar --todas --coleta` com código 0.
  - Registrar em `specs/006-ampliacao-tipos-de-geracao/tasks.md`.

### Perfil por tipo (item 3; decisão R4)

- [X] T038 [P] Ampliar `tests/comum/test_perfil.py` com as regras do data-model, seções 3.1 a 3.3 (citadas aqui como estão):
  - "`usina.tipo` … obrigatório; igual ao prefixo do CEG";
  - "`TIPO III` e `TIPO III (EM DIT)` são recusadas";
  - "`rascunho` é recusado (código 4); ausente = `conferido`", com a lista `pendentes` na mensagem;
  - CEG no padrão `^(UHE|PCH|CGH|UTE|UTN|EOL|UFV)\.[A-Z]{2}\.[A-Z]{2}\.\d{6}-\d\.\d{2}$`;
  - "o slug não pode ser `carteiras`";
  - `[cobertura]` "obrigatória fora da UHE"; valores `proprio`, `conjunto`, `agregado`, `ausente` ou a lista `["proprio", "conjunto"]`; chave desconhecida ou que não serve ao tipo recusada;
  - `potencia_unitaria_mw` ou `potencias_unidades_mw`: "A soma tem de dar a potência instalada, com a tolerância de hoje (0,1 MW)", e a lista tem um valor por unidade;
  - campos por tipo (tabela da seção 3.2): obrigatório, obrigatório com a cobertura e "não se aplica (presença é recusada)";
  - `[[identificacao.planejamento]]`: "O mesmo código não pode ter períodos sobrepostos";
  - o perfil da São Domingos com só `tipo` e `modalidade` a mais continua válido e com os mesmos valores derivados.
- [X] T039 Criar `src/comum/perfil_campos.py` com a tabela de campos por tipo do data-model, seção 3.2 (exigência `O`, `C` ou `—` por campo e tipo, e o conjunto que torna o campo `C` obrigatório).
- [X] T040 Ampliar `src/comum/perfil.py`:
  - **campos**: `tipo`, `modalidade`, `situacao`, `pendentes`, `subsistema`, `id_conjunto`, `codigos_programacao` (com `cod_programacao` aceito), `planejamento`, `membros`, `cobertura`, `potencias_unidades_mw` e `combustivel`;
  - **estrutura**: campos hidráulicos e `[analises]` opcionais;
  - **validação**: pela tabela da T039;
  - **valores derivados** do data-model 3.5: os hidráulicos só nas hidrelétricas com EVT ou hidrologia, com erro claro nos demais; `potencias_das_unidades_mw` e `codigos_planejamento_em(data)`.
- [X] T041 Acrescentar `tipo = "UHE"` e `modalidade = "TIPO II-A"` a `usinas/sao_domingos/perfil.toml` (FR-011), e o tipo e a modalidade da usina fictícia a `tests/fixtures/usina_ficticia/perfil.toml`.
- [X] T042 Portão do perfil:
  - suíte;
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`;
  - `python -m src comparar --todas --coleta` com código 0.
  - Registrar em `specs/006-ampliacao-tipos-de-geracao/tasks.md`.

### Novo congelamento (item 4)

- [X] T043 Conferir se o formato da Coleta mudou desde a T026: compare o `versao_formato` do `etapa.json` congelado com o atual.
  - Se mudou: depois do commit da referência pelo usuário, rodar de novo `python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "08/10/2026"` e `comparar --todas --coleta` com código 0.
  - Registrar. A partir daqui, os downloads ficam liberados.

**Checkpoint**: referências protegidas e independentes de `data/raw/`; Coleta corrigida, com registro e perfil por tipo; relatório da São Domingos igual à referência.

---

## Phase 3: User Story 1 - Escolher qualquer usina e obter o relatório com as seções comuns (Priority: P1) 🎯 MVP

**Goal**: catálogo de usinas, rascunho do perfil, série de referência por tipo e relatório com as seções comuns para qualquer tipo, cada número com o nível (fase A, itens 5 a 10).

**Independent Test** (quickstart 3.3 a 3.6):
- listar as usinas de MS;
- gerar o rascunho da William Arjona, conferir as recusas e gerar o relatório com as seções comuns;
- `comparar --todas --coleta` com código 0.

### Tests for User Story 1

- [X] T044 [P] [US1] Escrever `tests/coleta/test_catalogo_usinas.py`, com catálogo CKAN e arquivos sintéticos:
  - **tipo pelo prefixo do CEG** (decisão R1): linha sem CEG = `conjunto`; prefixo fora da lista = `outro`; `divergencias` quando o tipo do ONS difere;
  - **cobertura** (decisão R3), no arquivo mais recente de cada conjunto: `proprio`, `conjunto` (inclusive com linhas próprias sem valor), `agregado` e `ausente`;
  - **arquivos e colunas** do data-model, seções 2.1 a 2.6: `usinas.csv`, com "Uma linha por linha do cadastro do ONS" e só unidades ativas, mais `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`;
  - **agregados**: escolhidos pelo estado e pela modalidade, nunca pelo nome ou pelo id (id vazio aceito); Tipo III com `previsao`; duplicatas tratadas e `horas_ausentes`;
  - **códigos de programação**: a regra de ligação com a usina (código igual ao id ONS ou prefixo do conjunto sem `CJU_`);
  - **listagem**: uma coluna por conjunto de série do tipo (`P`, `C`, `A` ou `-`) e o slug do perfil achado pelo CEG;
  - **`--sem-portal`**: sem rede;
  - **códigos**: 0, 1 e 2 (contracts/cli-usinas.md).
- [X] T045 [P] [US1] Escrever `tests/coleta/test_perfil_rascunho.py` (contracts/cli-perfil.md):
  - **conteúdo do rascunho**:
    - `situacao = "rascunho"`, `pendentes`, comentários com a origem;
    - só as unidades ativas e o comentário de divergência de potência;
    - a `[cobertura]` só com os conjuntos já implementados, e os membros do conjunto;
    - código de programação sem ligação pendente, com a lista do estado;
  - **recusas**: catálogo ausente (5), CEG fora do catálogo (2), Tipo III ou só agregado (2), sem gravar nada;
  - **perfil existente**: nada gravado, com código 0 sem diferença e 6 com diferença;
  - **slug**: derivado do nome; `carteiras` reservado;
  - **leitura**: o comando não lê `data/raw/`.
- [X] T046 [P] [US1] Escrever `tests/coleta/test_serie_referencia.py`:
  - **escolha da série** (linhas da fase A da decisão R6): EVT nas hidrelétricas com EVT; Geração por usina pelo id ONS com geração própria; Geração por usina pelo id do conjunto em conjunto sem série própria;
  - **varredura**: em todos os arquivos publicados;
  - **período**: da primeira à última hora com valor; com cobertura `["proprio", "conjunto"]`, a união das duas séries;
  - **`trechos.csv`** (data-model 5.2): mudança de modalidade, de composição e de código, com `mostrar` só quando muda o nível ou a composição;
  - **hidrelétrica com EVT**: o caminho de hoje, sem trechos.
- [X] T047 [P] [US1] Escrever `tests/tratamento/test_base_horaria.py`:
  - `base_horaria.csv` nas usinas sem EVT, com as colunas `din_instante`, `geracao_mw`, `nivel`, `disponibilidade_operacional_mw`, `disponibilidade_sincronizada_mw`, `geracao_programada_mw`, `trecho` e `sinalizacoes`;
  - nível `conjunto` quando a série é do conjunto;
  - ausências listadas;
  - nenhum registro excluído (princípio V).
- [X] T048 [P] [US1] Escrever `tests/conferencia/test_aplicabilidade.py`:
  - `nao_aplicaveis.csv` com `conferencia` e `motivo`, com todas as conferências do catálogo que não se aplicam, inclusive na UHE;
  - o relatório e a planilha da UHE não o leem (T011).
- [X] T049 [P] [US1] Escrever `tests/analises/test_comum_tipos.py`, sobre a base horária comum de uma usina sem EVT:
  - indicadores anuais, série temporal, geração mensal e perfil horário;
  - a sazonalidade só com 12 meses distintos; abaixo disso, omitida e listada em `omitidos` com o motivo (decisão R17);
  - `ResultadosAnalise` com `VERSAO_FORMATO` 3 (o 2 foi usado pela decisão R22), `tipo`, `modalidade`, `niveis`, `trechos`, `comum` e `omitidos`;
  - nas hidrelétricas com EVT, os campos de hoje com os mesmos valores.
- [X] T050 [P] [US1] Ampliar `tests/relatorio/test_estrutura.py`:
  - **dois caminhos** (decisão R14):
    - a hidrelétrica com EVT tem exatamente as 17 seções de hoje;
    - a usina sem EVT segue a tabela da decisão R14, com numeração contínua e as seções sem base omitidas;
  - **título e capa por caminho** (data-model 6.5);
  - **legendas** com o identificador e, no conjunto e no agregado, o nível escrito (decisão R15);
  - **notas**: com as omissões, os níveis e as conferências não aplicáveis só nas usinas sem EVT.
- [X] T051 [P] [US1] Ampliar `tests/analises/test_conclusao.py`:
  - **catálogo**: cada regra declara `codigo`, `tipos`, `listas`, `nivel_exigido`, `funcao`, `limiares`, `periodo_minimo_meses` e `secoes` (data-model 6.5);
  - **hidrelétricas com EVT**: C1 a C11 sem mudança, com a ordem por lista e por número;
  - **regra com entrada de nível conjunto**: não é avaliada e vai para `omitidos`;
  - **PCH em conjunto**: sem itens, com a frase que explica a falta de base no nível da usina;
  - **nota da conclusão**: nas usinas sem EVT, gerada do catálogo do tipo; nas hidrelétricas com EVT, o texto de hoje.
- [X] T052 [P] [US1] Criar as usinas fictícias da decisão R23 em `tests/fixtures/usinas_ficticias/{uhe,pch,cgh,ute,utn,eol,ufv}/perfil.toml`:
  - valores inventados e nenhum valor de usina real;
  - os brutos sintéticos dos conjuntos da fase A em `tests/fixtures/brutos_ficticios.py`: geração da usina e do conjunto, programação, disponibilidade, indicadores, cadastro, composição e capacidade;
  - **a PCH**: composição que muda no período e linhas próprias sem valor;
  - **a UFV**: série curta.
- [X] T053 [P] [US1] Escrever `tests/integracao/test_usinas_ficticias.py`:
  - cada uma das sete usinas fictícias roda `completo --sem-portal` sem rede, com código 0 e as seções comuns;
  - nenhuma saída tem valor de outra usina.
  - Ampliar `tests/comum/test_literais.py` com os identificadores das pilotos: `MSUTWI`, `MSSRI1`, `CJU_MS4FINO`, `CEUFM`, `MSBDT`, `CJU_MSCAO` e os CEGs da spec.

### Implementation for User Story 1

- [X] T054 [US1] Acrescentar ao registro e às regras os conjuntos do catálogo e a geração do conjunto:
  - em `src/comum/regras.py`, os pacotes `usina_conjunto` e `capacidade-geracao`, com as pastas `usina_conjunto` e `capacidade_geracao`;
  - em `src/coleta/registro.py`, as entradas `composicao` e `capacidade` e o nível "usina ou conjunto" da `geracao`, com o identificador `id_conjunto` e a conferência pelo estado (decisão R9).
- [X] T055 [US1] Criar `src/coleta/catalogo_usinas.py` (decisões R1 a R3; contracts/cli-usinas.md):
  - **sincronização** (sem `--sem-portal`), com o catálogo CKAN, o cache e as versões de hoje:
    - Modalidade das usinas, Composição dos conjuntos, Capacidade de geração e Reservatórios (decisão R31);
    - o arquivo mais recente de cada conjunto de série já implementado;
    - a geração dos últimos 12 meses completos;
    - os dicionários desses conjuntos;
  - **montagem** de todos os arquivos de `data/catalogo/`, sem `.bak`, numa pasta temporária, com conferência e troca;
  - **listagem** filtrada;
  - **mensagens** obrigatórias do contrato.
- [X] T056 [US1] Em `src/__main__.py`, o comando `usinas` com as opções do contrato (`--estado`, `--tipo`, `--modalidade`, `--sem-portal`, `--forcar-download`) e os códigos 0, 1 e 2.
- [X] T057 [US1] Portão do item 5: suíte e `python -m src comparar --todas --coleta` com código 0. Registrar em `specs/006-ampliacao-tipos-de-geracao/tasks.md`.
- [X] T058 [US1] Criar `src/coleta/perfil_rascunho.py` e o comando `perfil` em `src/__main__.py` (decisão R5; contracts/cli-perfil.md):
  - leitura só de `data/catalogo/`;
  - recusas e diferenças com os códigos 0, 1, 2, 5 e 6;
  - o rascunho no formato de contracts/perfil-multitipo.md;
  - gravação de arquivo novo, conferida no disco, sem nunca sobrescrever.
  - Portão: suíte e `comparar --todas --coleta` com código 0.
- [X] T059 [US1] Criar `src/coleta/serie_referencia.py`: a escolha da série de referência (linhas da fase A da decisão R6), o período e os trechos (decisão R7), com o resumo do data-model 5.1.
- [X] T060 [US1] Integrar a série de referência e os arquivos novos em `src/coleta/etapa.py`:
  - **série**: nas usinas sem EVT, o período vem da série de referência; nas hidrelétricas com EVT, o caminho de hoje;
  - **arquivos novos**, só fora da UHE com EVT: `trechos.csv`, `geracao_complemento.parquet` (`cod_modalidadeoperacao` e `nivel` por hora), `composicao_conjunto.csv` e `capacidade_ficha.csv`;
  - **resumo do `etapa.json`**: `tipo`, `modalidade`, `serie_referencia`, `trechos`, `conjuntos_nao_aplicaveis` e `linhas_usina_sem_valor`.
  - Portão do item 7: suíte e `comparar --todas --coleta` com código 0.
- [X] T061 [US1] Criar `src/tratamento/base_horaria.py` com as colunas da T047 e chamá-lo em `src/tratamento/etapa.py` nas usinas sem EVT.
- [X] T062 [P] [US1] Criar `src/conferencia/aplicabilidade.py`: a lista das conferências do catálogo com a condição de cada uma; grava `nao_aplicaveis.csv` em `src/conferencia/etapa.py`, para todas as usinas.
- [X] T063 [US1] Ampliar as Análises:
  - `src/analises/resultados.py`: os campos novos e `VERSAO_FORMATO = 3`;
  - `src/analises/comum_tipos.py`, novo: as seções comuns sobre a base horária comum;
  - `src/analises/etapa.py`: escolhe o caminho pela presença da EVT;
  - `src/analises/constatacoes.py`: "do conjunto <nome>" quando o número é do conjunto.
- [X] T064 [US1] Ampliar a estrutura do relatório em `src/relatorio/estrutura.py`:
  - `Secao` com `tipos`, título por tipo, `legenda` e `periodo_minimo_meses`;
  - as seções novas da tabela da decisão R14, fora do caminho da EVT;
  - `secoes_presentes` por caminho.
- [X] T065 [US1] Título, capa, notas e legendas por caminho:
  - em `src/relatorio/conteudo.py`, `src/relatorio/pdf.py`, `src/relatorio/markdown.py` e `src/relatorio/planilha.py`:
    - o título e a capa do data-model 6.5;
    - as notas das usinas sem EVT: omissões, níveis e conferências não aplicáveis;
  - em `src/relatorio/fontes.py`: a legenda com o identificador e o nível (decisão R15).
  - Nas hidrelétricas com EVT, nada muda (T011).
  - Portão do item 8: suíte e `comparar --todas --coleta` com código 0.
- [X] T066 [US1] Reescrever o catálogo da conclusão em `src/analises/conclusao.py` como lista de `RegraConclusao` (decisão R16), sem mudar C1 a C11:
  - avaliar só com entradas do nível da usina;
  - mandar o que não é avaliado para `omitidos`;
  - gerar a nota da conclusão das usinas sem EVT a partir do catálogo, em `src/relatorio/conteudo.py`, mantendo `nota_conclusao()` como está para as hidrelétricas com EVT.
  - Portão do item 9: suíte e `comparar --todas --coleta` com código 0.
- [X] T067 [US1] Completar o item 10: rodar `tests/integracao/test_usinas_ficticias.py` com as sete usinas e corrigir o que faltar nos módulos da fase A, sem mudar os testes da T011.

### Validação real da User Story 1

- [X] T068 [US1] Montar o catálogo com o portal: `python -m src usinas --estado MS`, e de novo com `--sem-portal` (quickstart 3.3).
  - Conferir: 171 usinas em MS (UHE 5, PCH 16, CGH 9, UTE 33, UFV 86 e 22 linhas de conjunto, ou a contagem atual do ONS, explicada); `usinas.csv` com todas as linhas do cadastro; `catalogo.json`.
  - Depois, `comparar --todas --coleta` com código 0, ou as diferenças da Coleta por republicação levadas ao usuário.
  - Registrar.
- [X] T069 [US1] Gerar o rascunho da William Arjona: `python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona` (quickstart 3.4).
  - Medir o tempo (menos de 1 minuto, SC-003).
  - Conferir o conteúdo e rodar de novo: código 0 ou 6, com o arquivo igual byte a byte.
  - Registrar.
- [X] T070 [US1] Conferir as recusas (quickstart 3.5):
  - `python -m src coleta --usina william_arjona` com o perfil em rascunho dá código 4, com a lista dos pendentes;
  - `perfil` de uma CGH Tipo III de MS dá código 2, sem criar pasta.
  - Registrar.
- [X] T071 [US1] Levar ao usuário o catálogo de MS (`data/catalogo/usinas.csv`, filtrado por MS) e o rascunho `usinas/william_arjona/perfil.toml`.
  - O usuário confere e completa o perfil, com `situacao = "conferido"`.
  - Registrar a aprovação.
- [X] T072 [US1] Rodar `python -m src completo --usina william_arjona` (quickstart 3.6) e conferir:
  - série de referência "geracao" desde 10/07/2021;
  - só as seções comuns, sem EVT nem hidrologia;
  - legendas com o identificador;
  - notas com o que não se aplica.
  - Registrar o tempo do `etapa.json`.
- [X] T073 [US1] Conferir o código da fase A contra os rascunhos aprovados em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/`. Uma divergência necessária vira ajuste do rascunho, com aprovação do usuário.
- [X] T074 [US1] Portão do fim da fase A: suíte sem rede; `pyflakes` de fora do `venv`; `/speckit-converge`; `python -m src comparar --todas --coleta` com código 0. Registrar.

**Checkpoint**: qualquer usina com dado próprio ou de conjunto tem catálogo, rascunho do perfil e relatório com as seções comuns; a São Domingos não mudou.

---

## Phase 4: User Story 2 - Relatório completo de térmica e nuclear (Priority: P2)

**Goal**: despacho por motivo, inflexibilidade, atendimento ao despacho, disponível sem despacho, CVU × CMO e as regras de térmica (fase B; decisões R9, R11, R13, R16 e R18).

**Independent Test** (quickstart 4): relatório da William Arjona com as seções e as regras de térmica, e as conferências G3, G4 e DISPF.

### Preparação da fase B

- [X] T075 [US2] Criar a cópia de segurança `python -m src copia-seguranca --motivo antes_fase_B` e conferir `relatorios_referencia/` na cópia nova. Registrar.
- [X] T076 [P] [US2] Acrescentar a fase B aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md`: despacho, CVU e CMO no registro, com a identificação da decisão R9; `planejamento.csv` no catálogo; `subsistema` e `[[identificacao.planejamento]]` no perfil;
  - `002-tratamento-dados.md`: despacho por hora e por unidade, CVU pela revisão mais recente, CMO sem duplicatas, semanais em hora e o sinal do CVU (decisão R11);
  - `003-conferencia.md`: G3, G4 e DISPF, TEIFa e TEIP das térmicas (decisão R13);
  - `004-analises.md`: decisão R18; C12 a C15; C2, C5, C8 e C10 sobre a base horária comum;
  - `005-geracao-relatorio.md`: seções, figuras e indicadores da capa de térmica.
- [X] T077 [US2] Levar ao usuário os rascunhos da fase B em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase B antes disso.

### Tests for User Story 2

- [X] T078 [P] [US2] Escrever `tests/coleta/test_conjuntos_termicos.py`, com brutos sintéticos:
  - **despacho**: pelo CEG, com o código de planejamento conferido como número e só no período de cada código; linha com código fora da lista conta como "só identificador";
  - **CVU**: pelos códigos do perfil e conferido pelo subsistema;
  - **CMO**: pelo subsistema, como agregado;
  - **catálogo**: `planejamento.csv`, com o primeiro e o último mês de cada código.
- [X] T079 [P] [US2] Escrever `tests/tratamento/test_termica.py`:
  - `despacho_horario.csv`: a soma das unidades por hora, por motivo, programado e verificado;
  - `despacho_unidades_horario.csv`: o mesmo, por unidade;
  - `cvu_semanal.csv`: só a revisão mais recente, com `sinal_cvu` em CVU ausente ou negativo;
  - `cmo_semanal.csv`: sem duplicatas, contadas;
  - semanais levadas à hora pelo intervalo da semana operativa.
- [X] T080 [P] [US2] Escrever `tests/conferencia/test_fontes_termica.py`:
  - G3 (programação diária × programado do despacho) e G4 (verificado do despacho × Geração por usina), com a tolerância de 0,01 MW;
  - DISPF × horas pelo CEG numa térmica;
  - TEIFa e TEIP como não aplicáveis, com o motivo, quando a usina falta nas taxas.
- [X] T081 [P] [US2] Escrever `tests/analises/test_termica.py`:
  - geração por motivo, com as parcelas, e a inflexibilidade programada e verificada;
  - atendimento: horas e energia abaixo e acima, e os maiores desvios;
  - horas disponíveis sem despacho;
  - CVU × CMO por semana e por unidade, sem julgamento;
  - térmica sem geração no período: nenhuma divisão por zero, e a constatação de usina disponível e não despachada (US2-5).
- [X] T082 [P] [US2] Ampliar `tests/analises/test_conclusao.py` com C12 a C15 e com C2, C5, C8 e C10 numa térmica:
  - cada regra dispara e não dispara;
  - sem IP e TEIF de referência, as partes de C2 e C5 que dependem deles vão para `omitidos`;
  - nenhum termo de parecer nos textos.
- [X] T083 [P] [US2] Ampliar `tests/fixtures/brutos_ficticios.py` e as usinas fictícias `ute` e `utn` com despacho, CVU (com revisões), CMO e DISPF:
  - na `ute`, duas unidades de planejamento, com troca de código, e um ano sem geração;
  - em `tests/integracao/test_usinas_ficticias.py`, as seções de térmica nas duas.

### Implementation for User Story 2

- [X] T084 [US2] Acrescentar os conjuntos de térmica:
  - em `src/comum/regras.py`, os pacotes `geracao-termica-despacho-2`, `cvu-usitermica` e `cmo-semanal` e as pastas `geracao_termica_despacho_2`, `cvu_usitermica` e `cmo_semanal`;
  - em `src/coleta/registro.py`, as entradas `despacho`, `cvu` e `cmo` (data-model 4), com as colunas de valor do data-model 6.1.
- [X] T085 [US2] Na Coleta:
  - em `src/coleta/conjuntos.py`, a extração semanal (CVU e CMO) e a identificação por lista de códigos com período;
  - em `src/coleta/catalogo_usinas.py`, `planejamento.csv`, com todos os arquivos do despacho;
  - em `src/comum/perfil_campos.py`, `subsistema` e `planejamento` exigidos com `cvu` na cobertura.
- [X] T086 [US2] Criar `src/tratamento/termica.py`, com os arquivos da T079, e chamá-lo em `src/tratamento/etapa.py`.
- [X] T087 [P] [US2] Criar `src/conferencia/fontes.py` com G3 e G4, chamados em `src/conferencia/etapa.py`, e estender a DISPF × horas e as taxas refeitas às térmicas em `src/conferencia/indicadores.py`.
- [X] T088 [US2] Criar `src/analises/termica.py` (decisão R18), integrado em `src/analises/etapa.py` e em `ResultadosAnalise.termica`.
- [X] T089 [US2] Em `src/analises/conclusao.py`, C12 a C15 e a extensão de C2, C5, C8 e C10 às térmicas sobre a base horária comum:
  - a regra R7 e os eventos de indisponibilidade total calculados na base horária comum (decisão R30);
  - os limiares iniciais em constantes nomeadas em `src/comum/regras.py`, citados nas notas.
- [X] T090 [US2] Criar `src/relatorio/secoes_termica.py` e as figuras de térmica em `src/relatorio/figuras.py`, em seaborn com a paleta central:
  - geração por motivo empilhada (atenção à ordem de empilhamento);
  - inflexibilidade;
  - desvios do despacho;
  - CVU × CMO.
  - Também os indicadores da capa de térmica (data-model 6.5) em `src/relatorio/conteudo.py`.

### Validação real da User Story 2

- [X] T091 [US2] Rodar `python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona`:
  - código 6, com as chaves `despacho` e `cvu`, os códigos 34, 334 e 434 e o subsistema;
  - o usuário completa e confere o perfil.
  - Registrar.
- [X] T092 [US2] Rodar `python -m src completo --usina william_arjona --data-geracao "<data>"` e conferir os itens do quickstart 4:
  - seções de térmica;
  - CVU por unidade de gás e de óleo;
  - G3, G4 e DISPF;
  - tempo de até 15 minutos pelo `etapa.json`.
  - Registrar.
- [X] T093 [US2] Conferir o relatório piloto pelo quickstart 8: nenhum termo de parecer e nenhum identificador das outras pilotos em `reports/william_arjona/relatorio_analise_estatistica.md` (SC-004, SC-007). Registrar.
- [X] T094 [US2] Calibrar com a piloto os limiares de C12 a C15 e levar ao usuário o relatório da William Arjona e os limiares.
  - Depois da aprovação: `python -m src referencia --usina william_arjona --data-geracao "<data>" --aprovado-em "<data>"`.
  - Pedir o commit ao usuário. Registrar.
- [X] T095 [US2] Portão do fim da fase B: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0, com duas referências. Registrar.

**Checkpoint**: térmicas e nucleares com relatório completo; duas referências protegidas.

---

## Phase 5: User Story 3 - Relatório completo de eólica e solar (Priority: P3)

**Goal**: fator de capacidade, energia cortada por razão, recurso × geração e aderência, com o nível de cada número (fase C; decisões R12, R13, R17 e R19).

**Independent Test** (quickstart 5): relatórios da Seriemas 1 e da Praia Formosa com as seções e as regras de renováveis.

### Preparação da fase C

- [X] T096 [US3] Criar a cópia `python -m src copia-seguranca --motivo antes_fase_C` e conferir as referências na cópia nova. Registrar.
- [X] T097 [P] [US3] Acrescentar a fase C aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md`: fator de capacidade, restrição com detalhe e com razão (variantes eólica e fotovoltaica); o motor semi-horário; a linha da fase C da decisão R6; `[[identificacao.membros]]`;
  - `002-tratamento-dados.md`: semi-horárias e hora cheia, energia cortada e sinalizações (decisões R11, R12);
  - `003-conferencia.md`: G1, G2 e G5;
  - `004-analises.md`: decisão R19; C16 a C19; período mínimo;
  - `005-geracao-relatorio.md`: seções, figuras e indicadores da capa de renováveis.
- [X] T098 [US3] Levar ao usuário os rascunhos da fase C em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase C antes disso.

### Tests for User Story 3

- [X] T099 [P] [US3] Escrever `tests/coleta/test_conjuntos_renovaveis.py`:
  - **fator de capacidade**: pela usina (CEG) ou pelo conjunto (estado, CEG "-");
  - **restrição com detalhe**: semi-horária, pelo id ONS e pelo CEG; colunas ausentes de 05 a 12/2024 aceitas, sem servir de conferência;
  - **restrição com razão**: pela usina ou pelo conjunto;
  - **variantes**: a eólica e a fotovoltaica escolhidas pelo tipo;
  - **série de referência**: a restrição com detalhe (EOL e UFV em conjunto com série própria).
- [X] T100 [P] [US3] Escrever `tests/tratamento/test_renovavel.py`:
  - **energia cortada** = máx(estimada − verificada, 0) × 0,5 h, só nas semi-horas com `flg_geracaorestrita = 1`;
  - **semi-horas sem a coluna da marca**: contadas e fora do total;
  - **diferença fora das semi-horas restritas**: não entra;
  - **hora cheia**: média das duas meias-horas, e a hora incompleta fica ausente e contada;
  - **sinalizações**: recurso inválido, fator de capacidade fora de 0 a 1 e geração acima da capacidade;
  - **razão** por semi-hora, com o nível.
- [X] T101 [P] [US3] Escrever `tests/conferencia/test_fontes_renovaveis.py`:
  - G1 só com pares do mesmo nível;
  - G2 só com `[[identificacao.membros]]` e nos trechos com todas as usinas; sem os membros, não aplicável;
  - G5 (Programação diária × programada do fator de capacidade).
- [X] T102 [P] [US3] Escrever `tests/analises/test_renovavel.py`:
  - fator de capacidade publicado (com o nível) e calculado ("calculado neste relatório");
  - energia cortada por razão, com a razão do conjunto e a energia da usina;
  - recurso × geração por faixa, sem as semi-horas inválidas e com a contagem delas;
  - aderência à programação: desvio médio e maiores desvios;
  - série curta: sazonalidade omitida com o motivo.
- [X] T103 [P] [US3] Ampliar `tests/analises/test_conclusao.py` com C16 a C19:
  - C18 só com fator de capacidade próprio e garantia física no perfil;
  - C19 só com programação no nível da usina;
  - regras com período mínimo não avaliadas na série curta.
- [X] T104 [P] [US3] Ampliar `tests/fixtures/brutos_ficticios.py` e as usinas fictícias:
  - **`eol`**: Tipo I, com vento inválido, razão da restrição e série desde 10/2021;
  - **`ufv`**: em conjunto, com membros, série curta e o esquema antigo sem as cinco colunas.
  - Em `tests/integracao/test_usinas_ficticias.py`, as seções de renováveis nas duas.

### Implementation for User Story 3

- [X] T105 [US3] Acrescentar os conjuntos de renováveis:
  - em `src/comum/regras.py`, os pacotes `fator-capacidade-2`, `restricao_coff_eolica_detail`, `restricao_coff_fotovoltaica_detail`, `restricao_coff_eolica_usi` e `restricao_coff_fotovoltaica`, com as pastas;
  - em `src/coleta/registro.py`, as entradas `fator_capacidade`, `restricao_detalhe` e `restricao_razao`, com as variantes, e a linha da fase C da decisão R6 em `src/coleta/serie_referencia.py`.
- [X] T106 [US3] Ampliar o motor de `src/coleta/conjuntos.py` para as séries semi-horárias e as colunas que faltam em parte dos arquivos, sem mudar a extração dos conjuntos horários de hoje. Portão: `comparar --todas --coleta` com código 0.
- [X] T107 [US3] Criar `src/tratamento/renovavel.py`, com os arquivos do data-model 6.2, e chamá-lo em `src/tratamento/etapa.py`.
- [X] T108 [P] [US3] Acrescentar G1, G2 e G5 a `src/conferencia/fontes.py`, com a aplicabilidade em `src/conferencia/aplicabilidade.py`.
- [X] T109 [US3] Criar `src/analises/renovavel.py` (decisão R19), integrado em `src/analises/etapa.py` e em `ResultadosAnalise.renovavel`.
- [X] T110 [US3] Acrescentar C16 a C19 a `src/analises/conclusao.py`, com os limiares iniciais em constantes nomeadas em `src/comum/regras.py`, citados nas notas.
- [X] T111 [US3] Criar `src/relatorio/secoes_renovavel.py` e as figuras em `src/relatorio/figuras.py`, em seaborn:
  - fator de capacidade mensal;
  - energia cortada por razão;
  - recurso × geração por faixa;
  - desvio da programação.
  - Também os indicadores da capa de renováveis em `src/relatorio/conteudo.py`.

### Validação real da User Story 3

- [X] T112 [US3] Gerar e conferir os perfis com `python -m src perfil`:
  - UFV Seriemas 1: `--ceg UFV.RS.MS.052257-0.01 --slug seriemas_1`, com os membros de `CJU_MS4FINO`;
  - EOL Praia Formosa: `--ceg EOL.CV.CE.028631-1.01 --slug praia_formosa`.
  - O usuário completa e confere os dois. Registrar.
- [X] T113 [US3] Rodar `python -m src completo` das duas usinas com `--data-geracao "<data>"` e conferir os itens do quickstart 5:
  - na Seriemas 1: série desde 22/08/2026, sazonalidade omitida, números do conjunto identificados e energia cortada por razão do conjunto;
  - na Praia Formosa: energia cortada da ordem de 181 GWh contra cerca de 350 GWh de diferença bruta, vento inválido contado, G1 e G5.
  - Tempo de até 15 minutos cada. Registrar.
- [X] T114 [US3] Conferir os dois relatórios piloto pelo quickstart 8 (SC-004, SC-007): `reports/seriemas_1/relatorio_analise_estatistica.md` e `reports/praia_formosa/relatorio_analise_estatistica.md`. Registrar.
- [X] T115 [US3] Calibrar com as pilotos os limiares de C16 a C19 e levar ao usuário os dois relatórios e os limiares.
  - Depois da aprovação, `python -m src referencia` de cada uma; pedir o commit ao usuário.
  - Registrar.
- [X] T116 [US3] Portão do fim da fase C: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0, com quatro referências. Registrar.

**Checkpoint**: eólicas e solares com relatório completo e granularidade declarada; quatro referências protegidas.

---

## Phase 6: User Story 4 - PCH e CGH com a granularidade que os dados permitem (Priority: P4)

**Goal**: relatório de PCH e CGH no nível do conjunto, por trecho de composição, com o aviso do que o ONS não publica (fase D; decisões R7 e R20).

**Independent Test** (quickstart 6): relatório da PCH Bandeirante com a geração do conjunto por trecho, as omissões nas notas e a conclusão sem itens.

### Preparação da fase D

- [X] T117 [US4] Criar a cópia `python -m src copia-seguranca --motivo antes_fase_D` e conferir as referências na cópia nova. Registrar.
- [X] T118 [P] [US4] Acrescentar a fase D aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md`: composição por trecho e linhas próprias sem valor;
  - `004-analises.md`: decisão R20;
  - `005-geracao-relatorio.md`: seções de conjunto e notas do nível de conjunto.
- [X] T119 [US4] Levar ao usuário os rascunhos da fase D em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase D antes disso.

### Tests for User Story 4

- [X] T120 [P] [US4] Escrever `tests/analises/test_conjunto.py`, com a PCH fictícia (térmicas saem do conjunto no meio do período):
  - geração do conjunto por trecho de composição, com os tipos de cada trecho;
  - nenhum número dividido entre as usinas;
  - linhas próprias sem valor contadas na qualidade dos dados;
  - disponibilidade e indicadores oficiais omitidos, com o motivo;
  - conclusão sem itens e com a frase.
- [X] T121 [P] [US4] Ampliar `tests/integracao/test_usinas_ficticias.py` com as seções de conjunto na `pch` e na `cgh` fictícias e a nota de que o ONS não publica a geração da usina isolada.

### Implementation for User Story 4

- [X] T122 [US4] Criar `src/analises/conjunto.py` (decisão R20), integrado em `src/analises/etapa.py` e em `ResultadosAnalise.conjunto`, usando `trechos.csv` e `composicao_conjunto.csv`.
- [X] T123 [US4] Criar `src/relatorio/secoes_conjunto.py` e a figura da geração do conjunto por trecho em `src/relatorio/figuras.py`, em seaborn.
  - Também as notas do nível de conjunto em `src/relatorio/conteudo.py`.

### Validação real da User Story 4

- [X] T124 [US4] Gerar o perfil da PCH Bandeirante com `python -m src perfil --ceg PCH.PH.MS.032163-0.01 --slug bandeirante`.
  - Conferir os quatro códigos de programação `MSCAO-*`.
  - O usuário completa e confere o perfil. Registrar.
- [X] T125 [US4] Rodar `python -m src completo --usina bandeirante --data-geracao "<data>"` e conferir os itens do quickstart 6. Conferir o relatório pelo quickstart 8. Registrar.
- [X] T126 [US4] Levar o relatório ao usuário. Depois da aprovação, `python -m src referencia --usina bandeirante`, com as datas, e o pedido de commit. Registrar.
- [X] T127 [US4] Portão do fim da fase D: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0, com cinco referências. Registrar.

**Checkpoint**: PCH e CGH em conjunto com relatório honesto sobre o nível dos dados; cinco referências protegidas.

---

## Phase 7: User Story 5 - Relatório de carteira do estado (Priority: P5)

**Goal**: carteira por estado, por tipo ou pelos dois, a partir dos resultados gravados, sem nota nem parecer (fase E; decisão R21; contracts/cli-carteira.md).

**Independent Test** (quickstart 7): carteira de MS com as quatro pilotos com resultado, as demais com o motivo, a ordenação e o panorama.

### Preparação da fase E

- [X] T128 [US5] Criar a cópia `python -m src copia-seguranca --motivo antes_fase_E` e conferir as referências na cópia nova. Registrar.
- [X] T129 [P] [US5] Acrescentar a fase E aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/004-analises.md`: `indicadores_carteira`;
  - `005-geracao-relatorio.md`: a carteira (decisão R21; contracts/cli-carteira.md).
- [X] T130 [US5] Levar ao usuário os rascunhos da fase E em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase E antes disso.

### Tests for User Story 5

- [X] T131 [P] [US5] Escrever `tests/analises/test_carteira.py`:
  - `indicadores_carteira` com as chaves fixas da decisão R21, cada indicador com valor, nível e unidade;
  - vazio, e não zero, quando não se aplica;
  - contagem de todos os itens de cada lista da conclusão.
- [X] T132 [P] [US5] Escrever `tests/relatorio/test_carteira.py`, com resultados gravados de usinas fictícias:
  - **recorte**: por estado, por tipo e pelos dois; sem nenhuma das duas opções, código 2;
  - **nome da pasta**: `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`;
  - **sem resultado**: os motivos "sem perfil", "perfil em rascunho", "perfil inválido", "Análises ausentes, com falha, desatualizadas ou em formato antigo" e "só agregado no ONS (ver o panorama)"; as linhas de conjunto não contam;
  - **ordenação** por possíveis problemas, pontos de atenção e nome;
  - **panorama**: só com `--estado`, com Tipo III marcado como previsão;
  - **planilha**: abas `USINAS`, `INDICADORES`, `ORDENACAO`, `SEM_RESULTADO`, `PANORAMA` e `FONTES`;
  - **textos**: nenhum termo de parecer;
  - **nenhuma etapa executada**: os `etapa.json` iguais;
  - **código 5**: catálogo ausente ou nenhuma usina com resultado.

### Implementation for User Story 5

- [X] T133 [US5] Criar `src/analises/carteira.py` (`indicadores_carteira`) e gravá-lo em `src/analises/etapa.py`. Nas hidrelétricas com EVT, só o campo novo muda; o relatório não (T011).
- [X] T134 [US5] Criar `src/relatorio/carteira.py`:
  - recorte, leitura dos perfis pelo CEG e dos resultados;
  - PDF, Markdown e planilha com os construtores de hoje;
  - figuras em seaborn, com atenção à ordem de empilhamento do panorama;
  - gravação em pasta temporária com conferência e troca;
  - `--data-geracao`.
- [X] T135 [US5] Em `src/__main__.py`, o comando `carteira` com as opções e os códigos do contrato.

### Validação real da User Story 5

- [X] T136 [US5] Rodar `python -m src carteira --estado MS --data-geracao "<data>"` e `python -m src carteira --tipo UTE` e conferir os itens do quickstart 7:
  - tempo de até 5 minutos;
  - as quatro pilotos com resultado;
  - motivos, ordenação, panorama e a busca de termos de parecer;
  - os `etapa.json` iguais.
  - Registrar.
- [X] T137 [US5] Levar ao usuário a carteira de MS em `reports/carteiras/ms/` e registrar a aprovação.
- [X] T138 [US5] Portão do fim da fase E: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0. Registrar.

**Checkpoint**: carteira por estado e por tipo, sem parecer; nenhuma etapa refeita.

---

## Phase 8: Polish & Cross-Cutting Concerns (fase F, fechamento)

**Purpose**: incorporar a mudança às specs das etapas, documentar e excluir a spec de mudança (FR-030, SC-008; decisão R26).

- [ ] T139 Criar a cópia `python -m src copia-seguranca --motivo antes_fechamento` e conferir as referências na cópia nova. Registrar.
- [ ] T140 [P] Incorporar `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md` à spec da Coleta:
  - `specs/001-coleta-dados/spec.md`, `plan.md`, `data-model.md` e `contracts/`;
  - os contratos de `specs/006-ampliacao-tipos-de-geracao/contracts/` que pertencem à Coleta: `cli-usinas.md`, `cli-perfil.md` e `perfil-multitipo.md`, como contratos dela;
  - a tabela de aplicabilidade por tipo.
- [ ] T141 [P] Incorporar `ajustes-specs/002-tratamento-dados.md` a `specs/002-tratamento-dados/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/`), com a tabela de aplicabilidade por tipo.
- [ ] T142 [P] Incorporar `ajustes-specs/003-conferencia.md` a `specs/003-conferencia/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/`), com a tabela de aplicabilidade por tipo.
- [ ] T143 [P] Incorporar `ajustes-specs/004-analises.md` a `specs/004-analises/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/`), com a tabela de aplicabilidade por tipo.
- [ ] T144 [P] Incorporar `ajustes-specs/005-geracao-relatorio.md` a `specs/005-geracao-relatorio/` (`spec.md`, `plan.md`, `data-model.md`, `contracts/`), com `cli-carteira.md`, `cli-referencias.md` e a tabela de aplicabilidade por tipo.
- [ ] T145 Trocar em `src/` e `tests/` as citações da spec de mudança (por exemplo "spec 006, FR-0xx") pelas FR das specs das etapas.
  - Conferir com `Get-ChildItem README.md, specs, src, tests, usinas, .specify -Recurse -Include *.md, *.py, *.toml | Select-String -Pattern "006-ampliacao|spec 006|specs/006" -List`, que só pode achar a própria pasta 006.
- [ ] T146 Reescrever o `README.md`:
  - os sete tipos e os níveis dos dados;
  - os comandos `usinas`, `perfil`, `carteira`, `referencia` e `comparar --todas [--coleta]`;
  - as pastas `data/catalogo/`, `reports/carteiras/` e `relatorios_referencia/`;
  - o fluxo de uma usina nova, do catálogo ao relatório aprovado.
- [ ] T147 Rodar o quickstart inteiro (seções 1 a 9), com `comparar --todas --coleta` com código 0 para as cinco referências e `/speckit-converge` sem pendência. Registrar.
- [ ] T148 Levar ao usuário o pedido de exclusão de `specs/006-ampliacao-tipos-de-geracao/` (FR-030), com a lista do que foi incorporado.
  - Depois da aprovação: excluir com `git rm -r specs/006-ampliacao-tipos-de-geracao` e apontar `.specify/feature.json` para `specs/005-geracao-relatorio`.
  - Conferir que `specs/` tem só as cinco specs das etapas (SC-008).
  - Pedir o commit ao usuário. Registrar.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa pela versão de fiscalização congelada e conferida (T001). Bloqueia tudo até a aprovação dos rascunhos (T009).
- **Foundational (Phase 2)**: depende da Phase 1. Ordem interna obrigatória (decisão R22):
  - testes e proteção (T010 a T025);
  - migração (T026);
  - correções P1 a P5, registro e perfil (T027 a T042);
  - novo congelamento (T043).
  - Bloqueia todas as histórias.
- **US1 (Phase 3)**: depende da Phase 2 inteira. Downloads só depois da T043.
- **US2 a US5 (Phases 4 a 7)**: cada uma depende da anterior. As referências se acumulam; as fases mexem nos mesmos módulos de registro, conclusão e relatório, e a spec exige a ordem (FR-028).
- **Fechamento (Phase 8)**: depende da US5.

### User Story Dependencies

- **US1 (P1)**: depois da Foundational; nenhuma dependência de outra história.
- **US2 (P2)**: usa o registro, o perfil, a base horária comum e o catálogo da conclusão da US1.
- **US3 (P3)**: usa o mesmo núcleo e amplia o motor da Coleta. A G2 usa os membros do perfil da US1.
- **US4 (P4)**: usa os trechos e a composição da US1 e o nível de conjunto da US3.
- **US5 (P5)**: usa os resultados gravados das pilotos das US1 a US4 e o `indicadores_carteira`.

### Within Each Phase

- Rascunhos aprovados antes do código.
- Testes antes da implementação, falhando antes; os de invariantes passam desde o início.
- Registro, regras e perfil antes da Coleta; Coleta antes do Tratamento, da Conferência, das Análises e do Relatório.
- Portão com `comparar --todas --coleta` depois de cada item da fase A e no fim de cada fase.

### Parallel Opportunities

- **Phase 1**: T004 a T008, um arquivo cada.
- **Phase 2**:
  - os testes T011 a T016, depois da T010;
  - na implementação, T019 e T020 tocam etapas diferentes, mas dependem da T018 (o formato 2);
  - a T029 (P2) é independente das outras correções.
- **Cada história**: os testes marcados [P]; em seguida, os módulos de etapas diferentes marcados [P] (por exemplo, a conferência T087 enquanto o Tratamento T086 é feito).
- **Fechamento**: T140 a T144, uma spec cada.

---

## Parallel Example: Foundational e User Story 1

```text
# Phase 2, depois da T010 (fotografia dos invariantes), os testes da proteção juntos:
Task: "T011 tests/relatorio/test_invariantes_uhe.py"
Task: "T012 tests/comum/test_referencias.py"
Task: "T013 tests/comum/test_comparacao.py"
Task: "T014 tests/comum/test_copia_seguranca.py"
Task: "T015 tests/coleta/test_datas_obtencao.py"
Task: "T016 tests/integracao/test_sem_raw.py"

# US1, os testes juntos:
Task: "T044 tests/coleta/test_catalogo_usinas.py"
Task: "T045 tests/coleta/test_perfil_rascunho.py"
Task: "T046 tests/coleta/test_serie_referencia.py"
Task: "T047 tests/tratamento/test_base_horaria.py"
Task: "T048 tests/conferencia/test_aplicabilidade.py"
Task: "T049 tests/analises/test_comum_tipos.py"
Task: "T050 tests/relatorio/test_estrutura.py"
Task: "T051 tests/analises/test_conclusao.py"
```

---

## Implementation Strategy

### MVP First (Foundational + User Story 1)

1. Phase 1: pré-condições, cópia e rascunhos aprovados.
2. Phase 2: proteção, migração, correções, registro, perfil e congelamento. É crítica e bloqueia tudo.
3. Phase 3 (US1): catálogo, rascunho, série de referência e relatório com as seções comuns.
4. **PARAR E VALIDAR**: o relatório da William Arjona com as seções comuns e `comparar --todas --coleta` com código 0. Já dá para analisar a geração, a disponibilidade e a programação de qualquer usina com dado próprio ou de conjunto.

### Incremental Delivery

1. Foundational + US1 → MVP, com a São Domingos protegida.
2. US2 → térmicas completas → referência da William Arjona.
3. US3 → eólicas e solares → referências da Seriemas 1 e da Praia Formosa.
4. US4 → PCH e CGH em conjunto → referência da Bandeirante.
5. US5 → carteira de MS.
6. Fechamento → specs das etapas atualizadas e spec 006 excluída.

Cada fase termina com o portão. Nenhuma mudança num relatório aprovado sem a aprovação do usuário.

---

## Notes

- [P] = arquivos diferentes, sem depender de tarefa pendente.
- O rótulo [USn] liga a tarefa à história da spec.
- Antes de escrever um teste ou um módulo, ler a decisão citada no research e a seção citada do data-model e dos contratos.
- Nunca fazer commit; pedir ao usuário, com a mensagem sugerida.
- Os limiares das regras novas só valem depois de aprovados pelo usuário.

---

## Registro de execução

(preencher durante a implementação: data, tarefa, comando, resultado e evidência)

### 09/10/2026 — T001 (versão de fiscalização e pré-condições)

- **Decisão do usuário (09/10/2026)**: começar a implementação já, "deixando os códigos salvos em uma pasta" (FR-028 ajustada).
- **Pasta**: `C:\Users\rlazaro\Desktop\UHE_SAO_DOMINGOS_versao_fiscalizacao` (4,1 GB), com:
  - `src/` e `tests/` do commit `c82a64e`, sem mudanças pendentes em `src/`, `tests/` e `usinas/`;
  - `usinas/sao_domingos/perfil.toml`, `data/raw/`, `data/usinas/sao_domingos/` e `reports/sao_domingos/`;
  - `README.md`, `requirements.txt`, `.gitignore` e o `LEIA-ME.txt` com o uso.
- **Conferência**, na pasta congelada, com o Python do `venv` do projeto:
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: código 0 (Coleta 11:59, demais etapas 12:00);
  - `python -m src comparar --usina sao_domingos --referencia ..\UHE_SAO_DOMINGOS\_backup_2026-10-08_antes_ampliacao_tipos_de_geracao\linha_de_base`: "Nenhuma diferença." (código 0).
- **Projeto principal**:
  - 20 manifestos lidos; maior `registrado_em_utc` 2026-10-05 15:14:39 e maior `obtido_em_utc` 2026-10-05 15:14:36, ambos no dicionário da Modalidade das usinas;
  - nenhuma coleta com o portal depois de 08/10/2026.
- **`/speckit-implement`**: checklist `requirements.md` com 16 itens, todos marcados (PASS); `.gitignore` com os padrões de Python; nenhum hook registrado.

### 09/10/2026 — T002 (cópia de segurança)

- `python -m src copia-seguranca --motivo antes_fase_A`: código 0. "Cópia _backup_2026-10-09_antes_fase_A criada e conferida: 212 arquivos."
- Poda: saiu `_backup_2026-10-08_antes_ajustes_t072`. Ficam `_backup_2026-10-08_antes_ampliacao_tipos_de_geracao` (com `linha_de_base/`) e `_backup_2026-10-09_antes_fase_A`.

### 09/10/2026 — T003 (linha de base do projeto principal)

- Suíte sem rede: 396 aprovados, em 84,7 s.
- `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base`: "Nenhuma diferença." (código 0).
- `reports/sao_domingos/`: PDF com 30 páginas; planilha com 58 abas.
- Figuras (SHA-256, 16 primeiros caracteres):

  | Figura | SHA-256 |
  |---|---|
  | `01_serie_temporal_disponibilidade_geracao_evt.png` | `bbebd29dc1cd3289` |
  | `02_evt_mensal.png` | `460c95479cfd44f8` |
  | `03_perfil_horario_geracao_evt.png` | `c7e627bf8a15c470` |
  | `04_disponibilidade_geracao_anual.png` | `0956b20eb0d6dbf4` |
  | `05_vazoes_defluentes_anuais.png` | `065a008cefc01244` |
  | `06_disponibilidade_operacional_sincronizada_mensal.png` | `5a76334c166a9fa5` |
  | `07_evt_por_faixa_de_afluencia.png` | `f5e336924fd8135a` |
  | `08_perfil_horario_nivel_vazoes.png` | `a000b0bfb69fb6f6` |

### 09/10/2026 — T004 a T008 (rascunhos da fase A)

- `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/`: `001-coleta-dados.md`, `002-tratamento-dados.md`, `003-conferencia.md`, `004-analises.md` e `005-geracao-relatorio.md`. Aguardam a aprovação do usuário (T009).

### 09/10/2026 — T009 (aprovação dos rascunhos da fase A)

- O usuário aprovou os cinco rascunhos de `ajustes-specs/`, sem mudança ("Aprovo os cinco").

### 09/10/2026 — T010 e T011 (invariantes das hidrelétricas com EVT)

- `python -m tests.fixtures.gerar_invariantes_uhe`, com o código de antes de qualquer mudança: `tests/fixtures/invariantes_uhe.json`, da usina fictícia de `tests/fixtures/usina_ficticia/`, sem rede. Só se refaz com a aprovação do usuário.
- `tests/relatorio/test_invariantes_uhe.py`: 10 testes, aprovados com o código de antes.

### 09/10/2026 — T012 a T016 (testes da proteção)

- `tests/comum/test_referencias.py`: a T012 (`referencia`) e a T013 (`comparar --todas [--coleta]`) ficaram juntas, porque usam a mesma execução da usina fictícia; `tests/comum/test_comparacao.py` não mudou.
- `tests/comum/test_copia_seguranca.py` (T014), `tests/coleta/test_datas_obtencao.py` (T015) e `tests/integracao/test_sem_raw.py` (T016).
- Antes do código, falhavam: módulo `referencias` inexistente, `datas_obtencao.csv` ausente, `VERSAO_FORMATO["coleta"] == 1`.

### 09/10/2026 — T017 a T025 (implementação da proteção)

- **T017** `src/comum/caminhos.py`:
  - `RELATORIOS_REFERENCIA_DIR`, `pasta_referencia()`, `PASTA_CARTEIRAS` e o catálogo como função, `pasta_catalogo()`, para valer também dentro do espaço isolado;
  - o contexto `espaco_isolado()`, que troca `DATA_DIR`, `RAW_DATA_DIR`, `REPORTS_DIR`, `USINAS_DIR` e `perfil.RAIZ_PROJETO`;
  - as chaves `datas_obtencao` e `dicionario_evt` em `ARQUIVOS_COLETA`.
- **T018** `src/coleta/etapa.py`, com `VERSAO_FORMATO["coleta"] = 2`:
  - `datas_obtencao.csv`: uma linha por conjunto, na ordem de `CONJUNTOS_PIPELINE`, só com os arquivos obtidos da auditoria;
  - `dicionario_evt.json`: cópia do dicionário de `data/raw/_dicionarios/`;
  - os dois pela `persistencia`. `src/coleta/conjuntos.py` não precisou mudar.
- **T019** `src/tratamento/evt.py`: o dicionário vem de `coleta/dicionario_evt.json`, ao lado da base extraída.
  - Ele é passado a `carregar_dicionario_dados` e, pelo parâmetro novo `dicionario`, a `gerar_relatorio_validacao_md`.
  - O padrão das duas funções de `validacao.py` continua em `data/raw/`, só para as chamadas diretas (`test_validacao.py`). Nenhuma chamada do Tratamento usa o padrão.
- **T020**:
  - `analisar(..., datas_obtencao=...)` no lugar de `caminho_manifesto`;
  - de `datas_obtencao.csv` vêm o `obtido_em` da geração, da disponibilidade e da hidrologia, o resumo do manifesto da cobertura (conjunto da EVT) e `fontes.datas_obtencao(res)`;
  - campo novo `ResultadosAnalise.datas_obtencao`; `resultados.VERSAO_FORMATO = 2` e `VERSAO_FORMATO["analises"] = 2`;
  - testes ajustados: os que passavam um manifesto inexistente deixaram de passá-lo; os que liam, sem dizer, o `data/raw/` real do projeto passaram a receber as datas ou o dicionário (`test_complementar.py`; `tests/tratamento/test_evt.py`, com `gravar_dicionario_evt` em `tests/fixtures/brutos_ficticios.py`).
- **Portão depois da T020**:
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: código 0;
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base`: "Nenhuma diferença." (código 0);
  - `datas_obtencao.csv` da São Domingos com os 10 conjuntos; na EVT, 42 arquivos, publicação 2026-09-30T15:06 e obtenção 2026-09-30 16:55:59.
- **T021** `src/comum/referencias.py`, `registrar_referencia`:
  - exige o relatório e a Coleta `concluida` no formato atual e confere a data de geração no `etapa.json` do relatório;
  - confere o git com `git status --porcelain -- relatorios_referencia/<slug>`;
  - grava em `.gravando_<slug>`, confere os SHA-256 (também os de origem, contra os `etapa.json`) e troca a anterior, que volta se a troca falhar.
- **T022** `src/comum/comparacao.py`, `executar_comparacao_todas(coleta)`:
  - as etapas 2 a 5 rodam por `pipeline.executar_etapa` num espaço isolado, com `RAW_DATA_DIR` vazio;
  - no `--coleta`, as séries são comparadas linha a linha, só nas linhas cujo intervalo (hora, dia, mês ou ano) toca o período da referência;
  - as auditorias, só nas colunas numéricas, por arquivo da Coleta congelada, sem `data_hora_processamento`;
  - `dicionarios.csv`, `datas_obtencao.csv` e também `dicionario_evt.json` só como informação. O `dicionario_evt.json` não está no contrato: levado ao usuário.
- **T023** `src/comum/copia_seguranca.py`: `relatorios_referencia/` copiada inteira, sem as pastas temporárias, e conferida por `referencias.conferir_referencia` antes da poda; o `LEIA-ME.txt` lista as referências.
- **T024** `src/__main__.py`: o comando `referencia` e o `comparar --todas [--coleta]`. As combinações inválidas saem com 2 já na leitura das opções.
- **T025** `.gitignore`: `!relatorios_referencia/**/*.pdf`, `relatorios_referencia/*/coleta/` e `relatorios_referencia/.*/` (pastas temporárias). Com `git check-ignore -v --no-index`:
  - o PDF da referência entra (exceção da linha 63);
  - `coleta/evt_extraido.csv` e `coleta/etapa.json` ficam fora (linha 64);
  - `perfil.toml`, `referencia.json` e as figuras entram;
  - os PDFs de `reports/` continuam fora (linha 55).
- **Suíte** sem rede: 431 aprovados, em 159,7 s.
- **pyflakes** de fora do `venv`, em `src/` e `tests/`: só os 6 avisos que já existiam em `tests/relatorio/test_markdown.py` (fixtures do pytest importadas pelo nome, iguais na cópia de 09/10).

### 09/10/2026 — T026 (migração da referência da São Domingos)

- Em sequência, das 12:41 às 12:52:
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: código 0;
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base`: "Nenhuma diferença." (código 0);
  - `python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "08/10/2026"`: código 0;
  - `python -m src comparar --todas --coleta`: "sao_domingos: nenhuma diferença" e "Referências comparadas: 1; com diferença: 0." (código 0).
- `relatorios_referencia/sao_domingos/`:
  - os 12 arquivos do relatório (PDF, Markdown, planilha, CSV e 8 figuras), `perfil.toml` e `referencia.json` (período de 2018-08-28 00:00 a 2026-09-28 23:00);
  - `coleta/` com 18 arquivos: os 17 do `etapa.json`, inclusive `datas_obtencao.csv` e `dicionario_evt.json`, e o próprio `etapa.json`, sem `.bak`.
- `git add --dry-run relatorios_referencia/sao_domingos`: entram o relatório (com o PDF), as figuras, `perfil.toml` e `referencia.json`; a `coleta/` fica fora.
- Durante o `comparar --todas --coleta`, o `src/coleta/catalogo.py` já tinha as funções da P1 (T028). Elas só atuam no download, que não roda com `--sem-portal`; nenhum outro arquivo de `src/` mudou durante a migração.
- **Pendente**: o commit de `relatorios_referencia/sao_domingos/`, pedido ao usuário.

### 09/10/2026 — T027 a T033 (correções P1 a P5 da Coleta)

- **T027** `tests/coleta/test_correcoes_p1_p5.py`, 13 testes. Antes do código: 12 falhavam pelo motivo esperado; o nome com acento no perfil já funcionava.
- **T028 (P1)** `src/coleta/catalogo.py`:
  - `recurso_preferido`, `escolher_entre_repetidos` e `registrar_repetidos`, usados na EVT, nos indicadores, na programação e nos conjuntos horários;
  - o arquivo temporário passa a ser `<arquivo>.<id do recurso>.part`.
- **T029 (P2)** `numero_publicado` em `src/coleta/conjuntos.py`, usada nos conjuntos horários, na programação e na potência da ficha.
- **T030 (P3)**:
  - uma normalização, `normalizar_texto`, hoje em `src/coleta/registro.py`, ao lado da `Regra`;
  - na EVT, o pré-teste pela última palavra deu lugar ao nome normalizado uma vez por valor distinto;
  - na programação, o filtro do pyarrow usa os valores publicados cuja forma normalizada confere;
  - no Parquet da geração, o filtro usa o valor do perfil e a forma normalizada;
  - o cadastro passou a usar a mesma normalização.
- **T031 (P4)**: coluna de conferência ausente torna o arquivo `FALHA`, com "coluna de conferência ausente: <coluna>".
- **T032 (P5)**: o CSV vazio da EVT (sem cabeçalho) fica `FALHA` com "arquivo vazio". O CSV só com o cabeçalho continua `SEM_REGISTROS`, como hoje: a decisão R10 só acrescenta o motivo.
- A função `data_obtencao` de `src/coleta/conjuntos.py`, sem uso depois da T020, saiu, com a linha de teste que a exercitava.
- **T033**, das 12:53 às 13:02: suíte com 444 aprovados; `completo` com código 0; `comparar --todas --coleta` com "sao_domingos: nenhuma diferença" (código 0).

### 09/10/2026 — T034 a T037 (registro dos conjuntos)

- **T034** `tests/coleta/test_registro.py`.
- **T035** `src/coleta/registro.py`:
  - `Regra`, `DescricaoConjunto` ampliada (`chave`, `tipos`, `nivel`, `resolucao`, `referencia`, `variantes`) e as sete entradas de hoje, com os tipos da tabela do data-model;
  - `CONJUNTOS_PIPELINE` saiu de `src/comum/regras.py` e passou a ser derivado do registro;
  - `src/coleta/conjuntos.py` busca as descrições no registro.
- **T036**:
  - a Coleta percorre o registro filtrado. Uma usina sem a EVT sai com o código 1 e a mensagem, até a série de referência do tipo (decisão R6);
  - os dicionários e a aba DICIONARIOS da FONTES ficam só com os conjuntos da usina;
  - o Tratamento lê as descrições e as vazões do registro.
- **T037**, das 13:05 às 13:14: suíte com 459 aprovados; `completo` com código 0; `comparar --todas --coleta` com "sao_domingos: nenhuma diferença" (código 0).

### 09/10/2026 — T038 a T041 (perfil por tipo)

- **T038** `tests/comum/test_perfil.py` ampliado, com perfis fictícios de UTE, PCH em conjunto e UFV.
- **T039** `src/comum/perfil_campos.py`: a tabela do data-model 3.2.
- **T040** `src/comum/perfil.py`:
  - campos novos e validação pela tabela, com as mensagens do contrato;
  - valores hidráulicos com erro claro fora das hidrelétricas com EVT ou hidrologia;
  - `potencias_das_unidades_mw` e `codigos_planejamento_em(data)`;
  - as enumerações de tipo, modalidade, subsistema e cobertura em `src/comum/regras.py`.
- **Registro** ajustado ao data-model 3.3 (`conjuntos_da_usina`): sem `[cobertura]`, só na UHE, os dez de hoje; com ela, os conjuntos de série com `proprio` ou `conjunto` e, sempre, os cadastrais. O teste do registro foi ajustado a essa regra.
- **T041**: `tipo = "UHE"` e `modalidade = "TIPO II-A"` em `usinas/sao_domingos/perfil.toml` e no perfil da usina fictícia.
- Suíte sem rede: 487 aprovados. pyflakes: só os 6 avisos de antes.
- **Efeito na referência**: o `perfil.toml` congelado em `relatorios_referencia/sao_domingos/` não tem `tipo` nem `modalidade` e passa a ser recusado. Por isso, o `comparar --todas` só volta a funcionar depois de um novo congelamento (T043). O congelamento exige que a referência atual esteja commitada.

### 09/10/2026 — T042 (portão do perfil; em aberto até a T043)

- Das 13:18 às 13:22:
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`: código 0;
  - `python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base`: "Nenhuma diferença." (código 0). O relatório da São Domingos não mudou;
  - `python -m src comparar --todas --coleta`: código 1, com "usina.tipo: campo obrigatório ausente" e "usina.modalidade: campo obrigatório ausente" no perfil congelado. É o efeito previsto acima.
- **Falta**, depois do commit da referência pelo usuário (T043):
  - `python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "08/10/2026"`, que congela o perfil com `tipo` e `modalidade`;
  - `python -m src comparar --todas --coleta` com código 0.
- **Ajuste da T043**: o plano previa um novo congelamento só se o formato da Coleta mudasse; ele também é necessário quando a validação do perfil muda.

### 19/10/2026 — T042 e T043 (portão do perfil e novo congelamento)

- **Congelamento novo**: o perfil congelado em `relatorios_referencia/sao_domingos/` já tem `tipo` e `modalidade` (commit `a098792`, de 13/10/2026). O formato da Coleta continua o 2.
- **Relatório aprovado em 19/10/2026**: o de 13/10/2026, com o resumo executivo (spec 007) e as edições do usuário no título da capa e nos títulos das figuras 02 e 06 ("esse relatório está aprovado").
- `python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"`: código 0 (30 páginas; resumo executivo com 2).
- `python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "19/10/2026"`: código 0. Sugestão de commit: `docs: relatório de referência de sao_domingos (gerado em 07/10/2026 08:53, aprovado em 19/10/2026)`.
- `python -m src comparar --todas --coleta`: código 0, "sao_domingos: nenhuma diferença". A partir daqui, os downloads ficam liberados (catálogo e outras usinas).

### 19/10/2026 — decisão R31 do usuário e cópia de segurança

- **Decisão R31** (pergunta ao usuário, resposta "Usar 'reservatorio'"): o conjunto cadastral Reservatórios entra no catálogo para ligar o CEG ao `cod_usina` e ao reservatório da EVT e dos dados hidrológicos. Conferido na São Domingos: CEG `UHE.PH.MS.028761-0.01` → `cod_resplanejamento` 153 e `res_id` PNUHSD. Registrada no research (R31), no data-model (seções 2.1, 2.2 e 4), nos contratos `cli-usinas.md` e `cli-perfil.md` e no rascunho `ajustes-specs/001-coleta-dados.md`.
- `python -m src copia-seguranca --motivo antes_fase_A_catalogo`: código 0, 271 arquivos; excluída a `_backup_2026-10-09_antes_fase_A`. Ficam `_backup_2026-10-13_antes_resumo_executivo` e `_backup_2026-10-19_antes_fase_A_catalogo`.

### 19/10/2026 — itens 5 e 6 (T044, T045 e T054 a T058)

- **T054**: `src/comum/regras.py` com os pacotes e pastas de Composição, Capacidade e Reservatórios e as regras do catálogo (modalidades agregadas da geração, prefixo `CJU_`, tipos do ONS, datas sentinela); `src/comum/caminhos.py` com `ARQUIVOS_CATALOGO`; `src/coleta/registro.py` com as entradas `composicao`, `capacidade` e `reservatorio` (esta `so_catalogo`, nunca obtida pela Coleta da usina) e `descricao_geracao(perfil, nivel)`, com a geração do conjunto pelo id do conjunto e pelo estado (decisão R9). A UHE sem `[cobertura]` continua com os dez conjuntos de hoje. Testes do registro e dos dicionários ajustados (13 pacotes no registro).
- **T044 e T055**: `tests/fixtures/brutos_catalogo.py` (um Brasil fictício em GO e MT) e `tests/coleta/test_catalogo_usinas.py` (29 testes, escritos antes do código); `src/coleta/catalogo_usinas.py`. Dois ajustes no desenho, registrados no data-model 2.2:
  - coluna `potencias_unidades_mw` em `usinas.csv` (potência de cada unidade ativa, separada por `;`), necessária para o rascunho com unidades diferentes, que lê só o catálogo;
  - nos indicadores, a cobertura é verificada no DISPF mensal mais recente; nas séries, os formatos que a Coleta já lê (EVT e indicadores em CSV, programação em Parquet).
  - O catálogo grava pela persistência (`gravar_csv` e `gravar_bytes` sem `.bak`), numa pasta temporária conferida antes da troca (`test_conformidade.py`).
- **T056**: comando `usinas` em `src/__main__.py` (`--estado`, `--tipo`, `--modalidade`, `--sem-portal`, `--forcar-download`).
- **T057** (portão do item 5): suíte com 545 aprovados e 1 falha de conformidade (gravação direta do catálogo), corrigida; `comparar --todas --coleta`: código 0.
- **T045 e T058**: `tests/coleta/test_perfil_rascunho.py` (19 testes, escritos antes do código) e `src/coleta/perfil_rascunho.py`, com o comando `perfil` (`--ceg`, `--slug`). O rascunho traz a origem de cada valor em comentário e os pendentes como linhas comentadas; completado pelo fiscal, passa na validação do perfil (testado com a UTE e a PCH fictícias).
- **Portão do item 6** (T058): suíte com 564 aprovados; `python -m src comparar --todas --coleta`: código 0, sem diferença.

### 19/10/2026 — item 7 (T046, T059 e T060)

- **T046**: `tests/coleta/test_serie_referencia.py` (15 testes, escritos antes do código): escolha da série pelas linhas da fase A da decisão R6, varredura de todos os arquivos, período da primeira à última hora com valor (união com `["proprio", "conjunto"]`), `trechos.csv` com `mostrar` só quando muda o nível ou a composição, e a hidrelétrica com EVT no caminho de hoje.
- **T059**: `src/coleta/serie_referencia.py` (escolha, extração, período, complemento horário, combinação e trechos). Na extração genérica, `colunas_texto` na descrição do conjunto (`src/coleta/registro.py` e `src/coleta/conjuntos.py`) mantém a modalidade por hora como texto; vazia nos conjuntos de hoje, cujos arquivos extraídos não mudam (decisão R8).
- **T060**: `src/coleta/etapa.py` com a série de referência antes dos demais conjuntos nas usinas sem EVT e os arquivos `geracao_complemento.parquet`, `trechos.csv`, `composicao_conjunto.csv` e `capacidade_ficha.csv`; o resumo do `etapa.json` com `tipo`, `modalidade`, `serie_referencia`, `trechos`, `conjuntos_nao_aplicaveis` e `linhas_usina_sem_valor`. A Programação diária aceita vários códigos (`cod_exibicaousina` em cada linha; a soma por patamar fica com o Tratamento) e, fora das hidrelétricas, confere só pelo estado. Testes: `tests/coleta/test_coleta_sem_evt.py` (3, com a UTE e a PCH fictícias) e o de vários códigos em `tests/coleta/test_programacao.py`.
- **Portão do item 7**: suíte com 583 aprovados; `python -m src comparar --todas --coleta`: código 0, "sao_domingos: nenhuma diferença".

### 19/10/2026 — item 8 (T047 a T050 e T061 a T065)

- **Testes escritos antes do código**, sobre a UTE e a PCH fictícias dos brutos do catálogo (`tests/fixtures/sem_evt.py`, que roda as etapas numa pasta temporária; `tests/coleta/test_coleta_sem_evt.py` passou a usá-la):
  - **T047** `tests/tratamento/test_base_horaria.py` (9): colunas da base horária, nível `conjunto`, disponibilidade com a regra R7 sinalizada e mantida, horas ausentes listadas e não preenchidas, soma dos códigos da programação por patamar;
  - **T048** `tests/conferencia/test_aplicabilidade.py` (8): catálogo com as seis conferências de hoje e G1 a G5, `nao_aplicaveis.csv` em todas as usinas (na UHE, com as seis de hoje em `conferencias.pkl`), e o relatório sem ler o arquivo;
  - **T049** `tests/analises/test_comum_tipos.py` (10): indicadores anuais por ano e nível, fator de capacidade só em EOL e UFV no nível da usina, sazonalidade só com 12 meses distintos (omitida e listada abaixo disso), programação e disponibilidade só no mesmo nível, `ResultadosAnalise` com os campos novos e o caminho da UHE sem as seções comuns;
  - **T050** `tests/relatorio/test_estrutura.py` (+6): a UHE com as 17 seções de hoje; a UTE e a PCH com as seções da decisão R14, numeração contínua; título, capa, legendas com o nível e notas por caminho.
- **T061** `src/tratamento/base_horaria.py` e o caminho sem EVT em `src/tratamento/etapa.py`: período da série de referência (do `etapa.json` da Coleta), só os conjuntos coletados, `base_horaria.csv` com G1, D1 a D4 e R7 (R7 só com a geração e a disponibilidade da usina). Na programação com vários códigos, a soma por patamar só existe quando todos os códigos da extração têm valor (princípio V).
- **T062** `src/conferencia/aplicabilidade.py` (catálogo das conferências, com tipos, conjuntos e condições) e `src/conferencia/etapa.py`: nas hidrelétricas com EVT, as seis de hoje como hoje; nas demais, só as aplicáveis (por ora, cadastro e, com os indicadores, DISPF × horas e TEIFa e TEIP). `nao_aplicaveis.csv` para todas as usinas, com o motivo.
- **T063** Análises: `src/analises/resultados.py` com `tipo`, `modalidade`, `niveis`, `trechos`, `comum`, `termica`, `renovavel`, `conjunto`, `indicadores_carteira` e `omitidos`; `src/analises/comum_tipos.py` (seções comuns e omissões); `src/analises/etapa.py` escolhe o caminho pela série de referência; `src/analises/constatacoes.py` com as constatações das usinas sem EVT ("do conjunto <nome>"). O construtor dos indicadores do ONS aceita perfil sem IP e TEIF de referência.
- **T064** `src/relatorio/estrutura.py`: `Secao` com `caminhos`, `tipos`, título por tipo, `legenda` e `periodo_minimo_meses`; as seções do caminho sem EVT numa lista única com as de hoje.
- **T065** `src/relatorio/comum.py` (capa, tabelas, legendas, notas e os blocos de cada seção), `src/relatorio/figuras_comum.py` (cinco figuras em seaborn), e os dois caminhos no PDF, no Markdown, na planilha, nas figuras, na tabela de parâmetros e em `src/relatorio/fontes.py` (legenda com o nível: "conjunto de usinas, id ONS CJU_..."; conferências sem base fora da legenda). Nas hidrelétricas com EVT, nada muda.
- **Ajustes no desenho**, registrados no data-model:
  - `VERSAO_FORMATO` das Análises 3, porque o 2 já foi usado pela decisão R22 no item 4; Tratamento e Conferência passam ao 2 (`src/pipeline.py`);
  - título das usinas sem EVT igual ao da capa da UHE aprovada em 19/10/2026 ("<nome> — Análise do desempenho operacional"), que já não cita a EVT;
  - seções do caminho sem EVT com chave própria (sufixo `_comum` ou nome novo), para que o PDF e o Markdown da UHE não mudem de código.
- **Pendências registradas**:
  - a conclusão das usinas sem EVT sai com uma frase provisória ("Sem itens: ..."), até o catálogo de regras do item 9 (T066);
  - o resumo executivo das usinas sem EVT não é gerado (aviso no log; `resumo_executivo: null` no `etapa.json`), até a US3 da spec 007 (T027 a T030);
  - nas hidrelétricas sem EVT, a seção de afluência e vertimento e a conferência da geração entre fontes ficam omitidas, com o motivo nas notas (fases B a D).
- **Portão do item 8** (T065): suíte com 636 aprovados; `python -m src comparar --todas --coleta`: código 0, "sao_domingos: nenhuma diferença".

### 19/10/2026 — item 9 (T051 e T066)

- **T051** `tests/analises/test_conclusao.py` (+5, escritos antes do código): o catálogo declara os campos de cada regra (limiares que existem em `src/comum/regras.py`, sem período mínimo novo em C1 a C11); nas hidrelétricas com EVT, itens só nas listas declaradas e na ordem de hoje, sem regra omitida; a UTE fictícia com as regras comuns sobre a base horária (C8 com 720 h da regra R7; C2 e C5 omitidas, com o motivo); a PCH em conjunto sem itens, com as regras não avaliadas por falta de base no nível da usina e a frase que explica; a nota da conclusão por caminho.
- **T066** `src/analises/conclusao.py`: `RegraConclusao` (código, tipos, listas, função, seções, limiares, nível exigido, período mínimo e, nas regras comuns, a função sobre a base comum, as bases da usina de que precisa, a exigência do IP e da TEIF de referência e o texto da nota) e o catálogo `CATALOGO_CONCLUSAO` com C1 a C11, sem mudar as funções de hoje (só a C2 aceita perfil sem TEIF de referência, avaliando então só a limitação recorrente; a C10 recebe os eventos por parâmetro). Nas usinas sem EVT: C2, C5, C8 e C10 sobre a base horária comum, com as seções do caminho sem EVT; as não avaliadas vão para `omitidos` (tipo `regra`), com o motivo; `frase_sem_itens` explica a conclusão vazia (na PCH em conjunto, a falta de base no nível da usina, decisão R20).
- **Relatório**: a seção "Conclusão" passa a ser a mesma nos dois caminhos (`caminhos=("evt", "sem_evt")`), com a frase de hoje nas hidrelétricas com EVT; `nota_conclusao_catalogo` em `src/relatorio/conteudo.py` gera a nota das usinas sem EVT a partir do catálogo, e `nota_conclusao()` continua como está. A frase provisória do item 8 saiu.
- **Portão do item 9**: suíte com 641 aprovados; `python -m src comparar --todas --coleta`: código 0, "sao_domingos: nenhuma diferença".

### 19/10/2026 — item 10 (T052, T053 e T067)

- **T052**: `tests/fixtures/usinas_ficticias/{uhe,pch,cgh,ute,utn,eol,ufv}/perfil.toml` (a UHE é a usina fictícia de hoje, com outro slug) e `gerar_brutos_tipos` em `tests/fixtures/brutos_ficticios.py`, que acrescenta aos brutos da UHE fictícia: a geração das seis usinas sem EVT e do conjunto (a PCH com as linhas próprias sem valor), a disponibilidade da UTE (com 140 h acima da geração declarada e uma parada de 72 h) e da UTN, os indicadores e taxas da UTN, três dias de Programação diária (o conjunto por dois códigos e a UTE), o cadastro, a Composição (com um membro que entra em 02/2024) e a Capacidade. A UFV tem série curta (a partir de 10/02/2024). Valores inventados.
- **T053**: `tests/integracao/test_usinas_ficticias.py` (25): as sete usinas com `completo --sem-portal` e código 0, as seções comuns nas usinas sem EVT, a UHE no caminho de hoje (16 seções e o resumo executivo), nenhuma saída com o identificador de outra usina, os trechos e as linhas sem valor da PCH, a programação e a regra C8 da UTE, os indicadores da UTN e a série curta da UFV. `tests/comum/test_literais.py` com os identificadores do ONS e os CEGs das usinas piloto.
- **T067**, o que faltava nos módulos da fase A, achado ao rodar as sete:
  - perfis fictícios: o contrato do perfil exige o código de programação em todo tipo, mesmo com a programação `ausente` (CGH, EOL e UFV corrigidas no fixture; a validação não mudou);
  - título por tipo da série temporal ("Série temporal da geração" nas eólicas e solares, que não têm a disponibilidade no ONS), com `titulo_da_secao` também na aba CONCLUSAO;
  - eixo do tempo das figuras das usinas sem EVT: marcas por ano a partir de 3 anos, por mês abaixo disso e por dia nas séries diárias de até dois meses; as figuras mensais nunca por dia.
  - Os testes da T011 (invariantes da UHE) não mudaram.
- **Portão do item 10** (T067): suíte com 676 aprovados; `python -m src comparar --todas --coleta`: código 0, "sao_domingos: nenhuma diferença".

### 19/10/2026 — validação real da fase A (T068 a T070)

- **T068** `python -m src usinas --estado MS`: código 0, em 112 s, com o portal. Cadastro de 6.024 linhas (Modalidade das usinas publicada em 18/10/2026 22:04); **171 usinas em MS**: UHE 5, PCH 16, CGH 9, UTE 33, UFV 86 e 22 linhas de conjunto, a contagem prevista. `data/catalogo/` com `catalogo.json`, `usinas.csv` (todas as linhas do cadastro), `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv` e `agregados.csv`. De novo com `--sem-portal`: código 0, mesmas 171 usinas.
  - A William Arjona (UTE.GN.MS.027075-0.01, id ONS MSUTWI, TIPO I, 177,1 MW) aparece com cobertura própria em indicadores, programação, disponibilidade e geração; a São Domingos, com o perfil `sao_domingos`.
- **T069** `python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona`: código 0, em 1,1 s (meta de 1 minuto, SC-003). Rascunho com 18 campos do ONS e 4 pendentes (fonte dos parâmetros, garantia física, IP e TEIF de referência, estes três opcionais): cinco unidades ativas (39,16; 39,16; 33,0; 33,1 e 32,696 MW), combustível GÁS, início da operação em 2021 (primeira unidade ativa em 10/07/2021) e o código de programação MSUTWI. Segunda execução: código 0 ("sem diferença em relação ao catálogo"), com o arquivo igual byte a byte (SHA-256 `4a6cdc87…432c`).
- **T070** recusas: `python -m src coleta --usina william_arjona --sem-portal` com o rascunho dá código 4, com a situação e os quatro pendentes listados; `python -m src perfil --ceg CGH.PH.MS.030451-4.01` (CGH Bela Miragem, TIPO III, só agregado) dá código 2, com a mensagem que remete ao panorama da carteira, sem criar pasta em `usinas/`.
- **`comparar --todas --coleta` depois do catálogo** (T068): código 6, "sao_domingos: 2 diferenças", só na Coleta refeita: `cadastro_ficha.csv` (1 linha) e `auditoria_cadastro.csv` (1 arquivo), mais `datas_obtencao.csv` e `dicionarios.csv` (informação). Causa: o catálogo baixou a Modalidade das usinas republicada pelo ONS em 18/10/2026. A ficha da São Domingos tem o mesmo conteúdo; mudaram só `data_consulta_utc` (05/10 → 19/10/2026), a data de publicação e as linhas lidas do cadastro nacional (6.017 → 6.024). O relatório de referência não muda (usa a Coleta congelada). Levado ao usuário com a T071, para decidir entre aceitar a diferença como republicação ou refazer o congelamento.

### 19/10/2026 — decisão do usuário sobre a republicação do cadastro e o pyflakes

- **Decisão (a)** do usuário: aceitar como republicação as diferenças da Coleta refeita da São Domingos depois do catálogo (`cadastro_ficha.csv` e `auditoria_cadastro.csv`, pela Modalidade das usinas republicada em 18/10/2026; ficha com o mesmo conteúdo). A referência não é congelada de novo agora; nos próximos portões, `comparar --todas --coleta` com essas diferenças da Coleta (e só elas) conta como aprovado, até o próximo congelamento.
- **pyflakes** 4.0.3 instalado no Python 3.14 do sistema, fora do `venv` (`py -3.14 -m pyflakes src tests`), para a T074. Primeira execução: um import não usado em `src/coleta/perfil_rascunho.py` (`PREFIXO_CONJUNTO`, sobra do item 6), retirado; e as fixtures importadas de outros módulos de teste em `tests/relatorio/test_markdown.py` (padrão anterior à spec 006), a tratar na T074.

### 19/10/2026 — validação real da fase A (T071 a T073)

- **T071**: catálogo de MS e rascunho levados ao usuário. O usuário pediu para seguir ("ok, continue") sem completar ele mesmo o perfil; o perfil foi completado só com dados do ONS: fonte dos parâmetros "ONS, dados abertos: Capacidade de geração e Modalidade das usinas, publicados em 18/10/2026"; nome "UTE William Arjona" (curto "William Arjona"); sem garantia física, IP e TEIF de referência, que não têm fonte nos dados abertos (a C5 não é avaliada); `situacao = "conferido"`. O usuário pode acrescentar esses valores com a fonte a qualquer momento.
- **T072** `python -m src completo --usina william_arjona` (com o portal): código 0, em 311 s (meta de 15 minutos, SC-006). Tempos dos `etapa.json`: Coleta 4 min 59 s (varredura de toda a Geração por usina e a programação desde 2021), Tratamento 6 s, Conferência < 1 s, Análises 1 s, Relatório 5 s.
  - Série de referência "geracao" (id ONS MSUTWI) de 10/07/2021 00h a 17/10/2026 23h: 46.219 horas, 5 ausentes; trecho único, nível usina.
  - Relatório com 12 seções, só as comuns (sem EVT nem hidrologia; a EVT só aparece na tabela das conferências que não se aplicam), 18 páginas, 5 figuras e 28 abas; legendas com o identificador ("Geração por usina (id ONS MSUTWI), obtido em 19/10/2026"); notas com as omissões e as conferências não aplicáveis. Resumo executivo não gerado (US3 da spec 007).
  - Achados dos dados: geração até 1 MW em 92,8% das horas; disponibilidade operacional média de 21,6% da potência instalada e DISPF de 39,7%; indisponibilidade total de 30/01/2023 a 27/08/2025 (22.558 h); 1.322 h com geração acima da disponibilidade declarada (regra R7). Conclusão com C8 e C10; C5 omitida (sem IP e TEIF de referência).
  - Conferência: DISPF × horas com 52 divergências em 309 meses-unidade; TEIFa e TEIP refeitas não reproduzem nenhum dos 4 meses com a janela completa (diferenças de 0,08 a 2,07 p.p. na TEIFa e de cerca de 1 p.p. na TEIP), ao contrário da São Domingos. A causa provável (fórmula ou ponderação das taxas das térmicas) fica para a fase B (decisão R18); o relatório registra a divergência.
  - Corrigido ao ler o relatório: a C10 das usinas sem EVT agrupa as unidades e os anos ("de todas as unidades em 2022, 2023, 2024 e 2025"), em vez de repetir "da UG1 e da UG2 e …" a cada ano; o texto das hidrelétricas com EVT não muda. Teste novo em `tests/analises/test_conclusao.py`.
- **T073**: código da fase A conferido contra os rascunhos de `ajustes-specs/`. Oito divergências necessárias, aprovadas pelo usuário ("aprovado, siga") e aplicadas aos rascunhos: formato 3 das Análises; regras comuns C2, C5, C8 e C10 nas usinas sem EVT; afluência e nível das hidrelétricas sem EVT na fase D; título das usinas sem EVT igual ao da capa aprovada, conclusão única nos dois caminhos, título por tipo da série temporal e resumo executivo só com a US3 da spec 007; base horária por hora da série, soma estrita dos códigos de programação e formato 2 do Tratamento; regra dos agregados aplicada pelo catálogo; vários códigos de programação e conferência só pelo estado fora das hidrelétricas; formato 2 da Conferência, com só as conferências aplicadas nas usinas sem EVT.

## Phase 9: Convergence

- [X] T149 Gerar o resumo executivo das usinas sem EVT executando a US3 da spec 007 (T027 a T030), cuja dependência (a tabela anual da base horária comum) a fase A cumpriu, antes de levar o relatório da William Arjona à aprovação per Constituição, Produtos (partial)
- [X] T150 Implementar na fase D a seção "Afluência, vertimento e nível do reservatório" das hidrelétricas sem EVT com Dados hidrológicos (análise sem os cruzamentos com a EVT, seção e figura em seaborn, teste com uma hidrelétrica fictícia sem EVT e com hidrologia), hoje omitida com o motivo per FR-020 e decisão R14, seção 13 (missing)
- [X] T151 Tratar na conferência do cadastro (`src/conferencia/cadastro.py`) o perfil sem id ONS (PCH, CGH, EOL e UFV em conjunto): "não informado" no texto, no lugar de "None", e divergência só quando o cadastro e o perfil diferem de fato, com teste per FR-019 e FR-025 (partial)
- [X] T152 Usar `Secao.legenda` nas legendas das seções do caminho sem EVT ou retirá-lo de `src/relatorio/estrutura.py`, ajustando o data-model 6.5 per data-model 6.5 (partial)
- [ ] T153 Registrar na incorporação (fase F) os desvios do plano aprovados na fase A: `VERSAO_FORMATO` 3 das Análises e os módulos `src/relatorio/comum.py` e `src/relatorio/figuras_comum.py` per plan.md, estrutura de módulos (contradicts)

### 19/10/2026 — T074 (portão do fim da fase A), convergência (T151 e T152) e decisão sobre as republicações

- **pyflakes** (Python 3.14 do sistema, fora do `venv`): o import não usado em `src/coleta/perfil_rascunho.py` saiu antes; as fixtures que `tests/relatorio/test_markdown.py` importava de outros testes passaram a fixtures locais, sobre as funções `montar_resultados_com_indicadores` e `montar_resultados_com_programacao` (em `tests/analises/`). Resultado: nenhum aviso em `src/` e `tests/`.
- **`/speckit-converge`** (limitado à fase A, a pedido): 5 achados, anexados como Phase 9: Convergence (T149 a T153). T149 (resumo executivo das usinas sem EVT, pela US3 da spec 007), T150 (afluência das hidrelétricas sem EVT, fase D) e T153 (desvios do plano, fase F) ficam para as fases deles. Já cobertos: TEIFa e TEIP das térmicas (T087) e as seções de térmica, eólica/solar e conjunto (fases B a D).
- **T151**: a conferência do cadastro trata o perfil sem id ONS ("não informado", nunca "None"; sem divergência quando o cadastro e o perfil não informam), com teste em `tests/conferencia/test_conferencias.py`.
- **T152**: `Secao` sem o campo `legenda`: a legenda de fonte é de cada tabela e figura (chave declarada com o bloco da seção), como já era; data-model 6.5 ajustado.
- **Primeiro portão**: suíte com 677 aprovados; `comparar --todas --coleta` com código 6, só na Coleta refeita: além do cadastro (decisão de 19/10), o ONS publicou em 18/10/2026 setembro/2026 nas horas por estado operativo (`taxa_teif_teip_parametro`, 16 linhas) e nas taxas TEIFa/TEIP (`taxa_teif_teip`, 2 linhas). O relatório refeito a partir da Coleta congelada não mudou.
- **Decisão do usuário** (pergunta, resposta "Aceitar também esta"): as diferenças da Coleta causadas por republicação do ONS (cadastro e indicadores/taxas) contam como aprovadas até o próximo congelamento da referência; o relatório refeito a partir da Coleta congelada continua tendo de dar "nenhuma diferença".
- **Portão do fim da fase A** (depois da T151 e da T152): suíte com 678 aprovados, sem rede; pyflakes sem aviso; `python -m src comparar --todas --coleta`: código 6 com as mesmas 4 diferenças da Coleta refeita aceitas pelo usuário (`auditoria_cadastro.csv`, `cadastro_ficha.csv`, `auditoria_indicadores.csv` e `indicadores_extraido.parquet`, por republicação do ONS em 18/10/2026) e nenhuma no relatório refeito a partir da Coleta congelada. **Fase A concluída.**

### 19/10/2026 — T149 (resumo executivo das usinas sem EVT)

- Feita pela US3 da spec 007 (T027 a T030, registradas no `tasks.md` da 007): o resumo sai para todas as usinas, com os indicadores e a tabela anual do caminho de cada uma e os números do conjunto identificados. Resumo da William Arjona: 2 páginas, 399 palavras.
- Portão: suíte com 687 aprovados; pyflakes sem aviso; `comparar --todas --coleta` só com as diferenças da Coleta aceitas pelo usuário (republicação do ONS); relatório e resumo da São Domingos sem diferença.

### 19/10/2026 — preparação da fase B (T075 e T076)

- **T075** `python -m src copia-seguranca --motivo antes_fase_B`: código 0; `_backup_2026-10-19_antes_fase_B` criada e conferida (309 arquivos), com `relatorios_referencia/sao_domingos/` (`referencia.json` com o mesmo SHA-256 do projeto) e o `LEIA-ME.txt` listando a referência. Excluída a mais antiga, `_backup_2026-10-13_antes_resumo_executivo`; ficam `_backup_2026-10-19_antes_fase_A_catalogo` e `_backup_2026-10-19_antes_fase_B`. Antes da cópia, o portão: suíte com 687 aprovados, pyflakes sem aviso e `comparar --todas --coleta` só com as diferenças da Coleta aceitas pelo usuário.
- **T076**: seção "Fase B — térmicas e nucleares" acrescentada aos cinco rascunhos de `ajustes-specs/`:
  - Coleta: FR-055 (despacho pelo CEG com o código de planejamento como conferência; CVU pelo código e pelo subsistema; CMO pelo subsistema, nível agregado), FR-056 (`usina.subsistema` e `[[identificacao.planejamento]]` no perfil), FR-051 e FR-053 ajustadas (`planejamento.csv` no catálogo e no rascunho);
  - Tratamento: FR-037 a FR-040 (despacho por hora e por unidade, CVU pela revisão mais recente com o sinal, CMO sem duplicatas, semanais em hora);
  - Conferência: FR-020 (G3), FR-021 (G4) e FR-022 (DISPF, TEIFa e TEIP das térmicas, com a apuração da divergência da William Arjona);
  - Análises: FR-056 (seções de térmica, decisão R18) e FR-057 (C12 a C15, limiares calibrados na William Arjona);
  - Geração do relatório: FR-044 (três seções de térmica e as figuras), capa, legendas, notas e o resumo executivo das térmicas (indicador de perda e termos CVU e CMO).
- **T077**: rascunhos levados ao usuário; nenhum código da fase B antes da aprovação.
### 19/10/2026 — decisões do usuário (T077, agentes e encerramento da 007)

- **T077**: rascunhos da fase B aprovados pelo usuário ("aprovado T077"). O código da fase B pode começar (T078 em diante).
- **Agente atual** (T043 da spec 007, "Mostrar agente atual"): nas usinas sem EVT, a capa e o resumo mostram o agente atual das unidades ativas, da Capacidade de geração (a Coleta passou a gravar o agente proprietário e o operador em `capacidade_ficha.csv`); data-model 6.5 e rascunho 005 ajustados.
- **Encerramento da 007** ("faça o item 3 como achar melhor"): a incorporação da 007 à spec 005 e a exclusão da pasta (T037 e T038 da 007) entram no fechamento desta spec (fase F), junto com os ajustes da 006 na spec 005.

### 20/10/2026 — fase B, código e testes (T078 a T090)

- **Contratos do ONS conferidos antes do código** (dados abertos, consulta de 19/10/2026):
  - despacho: arquivos anuais (2013 a 2024) e mensais (desde 01/2022), com 2022 a 2024 nos dois; CEG em todas as linhas; `cod_usinaplanejamento` DOUBLE em todos os Parquet; William Arjona com 34 (2013-01 a 2018-08), 334 (desde 2021-07) e 434 (2021-08 a 2026-01);
  - os motivos não formam uma partição exata: em cerca de 8 % das horas de 2026, a ordem de demérito acima da inflexibilidade toma o lugar da ordem de mérito na soma. As análises usam os totais publicados (`val_proggeracao`, `val_verifgeracao`) e mostram a parcela de cada motivo sobre eles, com a nota de que a soma das parcelas pode diferir de 100 %;
  - CVU: uma linha por semana operativa e código em cada arquivo anual (a revisão é a da semana); valores 0,0 na William Arjona (434 desde 2023; 334 em 2023 e em semanas de 2024), não sinalizados pela regra aprovada (só ausente ou negativo): levar ao usuário na calibração (T094);
  - CMO: `din_instante` é a sexta-feira que fecha a semana operativa (sábado a sexta), embora a descrição do contrato diga "início"; o Tratamento põe o CMO na semana operativa que contém a data, o que vale nos dois casos.
- **T078** `tests/coleta/test_conjuntos_termicos.py` (6 testes) e ajustes em `test_catalogo_usinas.py`, `test_registro.py`, `test_dicionarios.py`, `test_coleta_sem_evt.py` e `test_perfil_rascunho.py`; fixture do catálogo com despacho (um anual antigo e dois mensais) e CVU.
- **T079** `tests/tratamento/test_termica.py` (4 testes). **T080** `tests/conferencia/test_fontes_termica.py` (4 testes). **T081** `tests/analises/test_termica.py` (5 testes). **T082** `tests/analises/test_conclusao.py`: catálogo C1 a C15 e dois testes novos (C12 a C15 no limiar e abaixo dele; C10 numa térmica, C2 e C5 omitidas sem IP e TEIF).
- **T083** `tests/fixtures/brutos_ficticios.py`: a UTE fictícia com 2023 inteiro sem geração e disponível (código 901), trocado em 01/2024 pelas unidades 902 (gás) e 903 (óleo), o anual de 2024 repetindo os mensais, CVU com duas revisões por semana e um valor negativo, CMO com uma semana republicada; a UTN com o código 950. Perfis fictícios com `subsistema`, `[[identificacao.planejamento]]` e `despacho`/`cvu` na cobertura. Três testes novos em `tests/integracao/test_usinas_ficticias.py`.
- **T084** `src/comum/regras.py` (pacotes, pastas e os limiares iniciais de C12 a C15 e do desvio do despacho), `src/comum/caminhos.py` (arquivos de cada etapa) e `src/coleta/registro.py` (entradas `despacho`, `cvu` e `cmo`; o CMO só com o subsistema no perfil).
- **T085** `src/coleta/conjuntos.py` (data publicada configurável para o CVU, código comparado como número com vírgula ou ponto, código no período dele, "só conferência" zerada sem conferência declarada); `src/coleta/catalogo_usinas.py` (todos os arquivos do despacho na sincronização, `planejamento.csv`, cobertura do despacho pelo CEG e do CVU pelos códigos vigentes); `src/coleta/perfil_rascunho.py` (planejamento no rascunho e nas diferenças, com o subsistema, só nas térmicas). `perfil_campos.py` já trazia as exigências desde a fase A.
- **T086** `src/tratamento/termica.py`, chamado em `src/tratamento/etapa.py`.
- **T087** `src/conferencia/fontes.py` (G3 e G4, com a coincidência deslocada de uma hora e o aviso no log); catálogo e etapa da Conferência; TEIFa e TEIP não aplicáveis com o motivo próprio quando a usina falta nas taxas. A DISPF × horas e as taxas já rodavam nas térmicas desde a fase A; a apuração da divergência da William Arjona fica para a T092, com os dados reais.
- **T088** `src/analises/termica.py`, integrado em `src/analises/etapa.py` (com o resumo de G3 e G4 para as legendas) e nas constatações; omissões por tipo em `src/analises/comum_tipos.py`.
- **T089** C12 a C15 em `src/analises/conclusao.py` (só no caminho sem EVT; `REGRAS_CONCLUSAO` continua com C1 a C11).
- **T090** `src/relatorio/secoes_termica.py` e as quatro figuras em seaborn (paleta validada com o script da skill de visualização; empilhamento com a ordem invertida). Desvio do plano: as figuras ficaram em `src/relatorio/figuras_comum.py` e os indicadores da capa em `src/relatorio/comum.py`, os módulos do caminho sem EVT desde a fase A. Também a coluna "Disp. sem despacho (h)" na tabela anual (o indicador de perda do resumo executivo), a identificação com o subsistema e os códigos de planejamento, a nota, os parâmetros, as legendas de fonte (com G3 e G4), as abas TERM_* e CONF_G3/G4 da planilha. Termos CVU e CMO no glossário do resumo com texto provisório, a aprovar pelo usuário na T094.
- **Portão**: suíte com 725 aprovados; pyflakes sem aviso; `comparar --todas --coleta` com código 6 só pelas quatro diferenças da Coleta aceitas pelo usuário (republicação do ONS de 18/10/2026), sem diferença no relatório da São Domingos.

### 20/10/2026 — T091 (perfil da William Arjona com o despacho e o CVU)

- `python -m src usinas --estado MS --tipo UTE` (com o portal): código 0; todos os arquivos do despacho baixados; `planejamento.csv` com 220 códigos; a William Arjona com despacho e CVU próprios (`P`). O ONS republicou a Modalidade das usinas em 19/10/2026 22:04.
- `python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona`: código 6, com `identificacao.planejamento` (34 de 2013-01 a 2018-08; 334 desde 2021-07; 434 de 2021-08 a 2026-01), `cobertura.despacho` e `cobertura.cvu`. O subsistema (SE) já estava no perfil desde a fase A.
- Com a aprovação do usuário ("Aplicar como está"), o perfil ganhou os três códigos e as duas chaves, com a origem em comentário; o `perfil` de novo: código 0, sem diferença.

### 20/10/2026 — T092 e T093 (relatório da William Arjona com as seções de térmica)

- **T092** `python -m src completo --usina william_arjona --data-geracao "20/10/2026 09:00"` (com o portal): código 0 nas cinco etapas, em 4,2 minutos (limite de 15). Período de 10/07/2021 00h a 18/10/2026 23h (46.243 horas com valor). Relatório com 15 seções, 27 páginas, 9 figuras; as três seções de térmica entre o perfil horário e a programação diária.
  - Quickstart 4: seções de térmica presentes; CVU por unidade de gás (334) e de óleo (434) na tabela e na figura; G3 com 5.760 de 5.760 horas coincidentes; G4 com 46.121 de 46.243 (99,7 %; as 122 divergentes na entrada em operação, em 07/2021), que cai para 92,9 % com uma hora de deslocamento, o que confirma a hora de início do intervalo; DISPF × horas com 52 divergências em 309 meses-unidade.
  - Conclusão real: C8, C10, C12 (2.821 h abaixo da programada), C13 (10.520 h em 67 semanas) e C15 (114 h sem programação); C14 sem item (inflexibilidade programada nula); C5 omitida (sem IP e TEIF de referência).
  - Achado: o CVU publicado é zero em 250 das 267 semanas da unidade 434 (todas desde 2022) e em 116 das 274 da 334 (2022 a 2024). Pela regra aprovada (sinal só para o CVU ausente ou negativo), o zero entra na comparação como "abaixo do CMO" e responde por toda a base da C13: sem ele, 0 h. Também 57 semanas da 334 e 66 da 434 com o CVU igual ao CMO (os dois em zero), que a tabela não mostra.
  - FR-022 (TEIFa e TEIP da William Arjona, 0 de 4 meses reproduzidos): a diferença cai mês a mês (−2,07; −0,92; −0,53; −0,08 p.p. na TEIFa de 06 a 09/2026) à medida que os meses iniciais saem da janela; as taxas publicadas começam em 09/2021 com TEIFa de 4,0 % e TEIP de 1,8 % e sobem aos poucos, embora as horas reais dos primeiros meses tenham muita indisponibilidade forçada; a UG5 não tem parâmetros de 09/2025 a 01/2026; nas térmicas, o HP soma também as horas equivalentes (HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF). O padrão é compatível com a janela completada por valores de referência nos meses sem histórico, mas não há fonte publicada em mãos nem os valores de referência da usina: pela FR-022, a divergência continua registrada como hoje, sem ajuste.
- **T093** quickstart 8 no relatório e no resumo da William Arjona: nenhuma ocorrência de termos de parecer ("satisfat", "cumpre", "descumpr", "deficien", "culpa") nem de identificadores das outras pilotos (MSUHSD, PRUHSD, CEUFM, MSSRI1, CJU_MS4FINO, MSBDT, CJU_MSCAO); o CMO identificado como "subsistema SE, agregado" nas legendas.

### 20/10/2026 — T094 (calibração e decisões do usuário; em aberto até a aprovação do relatório)

- **Limiares de C12 a C15**: mantidos os iniciais, com a aprovação do usuário (desvio do despacho de 5 MW; C12 ≥ 24 h; C13 ≥ 168 h; C14 ≥ 5 % da inflexibilidade programada; C15 ≥ 24 h). Na William Arjona: C12 com 2.821 h, C15 com 114 h, C14 sem base (inflexibilidade programada nula no período).
- **CVU zero** (decisão do usuário: "Zero fica fora"): `sinal_cvu = "zero"`, mantido na base e fora da comparação com o CMO, como o ausente e o negativo; FR-038 (rascunho 002) e FR-056 (rascunho 004) ajustadas. A tabela CVU × CMO ganhou a coluna das semanas com o CVU igual ao CMO, para as colunas fecharem o total de semanas. Na William Arjona, a C13 deixa de gerar item (sem o zero, nenhuma semana com CVU abaixo do CMO e horas disponíveis sem despacho).
- **Glossário do resumo**: textos de CVU e CMO aprovados pelo usuário como estão.
- Relatório refeito (`completo --usina william_arjona --sem-portal --data-geracao "20/10/2026 09:00"`): código 0; 15 seções, 27 páginas; resumo executivo com 2 páginas e 564 palavras. Suíte com 725 aprovados; pyflakes sem aviso.
- Falta: a aprovação do relatório pelo usuário, o registro da referência (`python -m src referencia --usina william_arjona ...`) e o commit.
- **T094 concluída** (20/10/2026): o usuário aprovou o relatório e o resumo executivo da William Arjona ("aprovo o relatório e o sumário executivo"), depois de conferir três horas da série com uma fonte própria (os valores batem com a base horária na hora de início do intervalo; a fonte dele usa a data no formato mês/dia). `python -m src referencia --usina william_arjona --data-geracao "20/10/2026 09:00" --aprovado-em "20/10/2026"`: código 0; referência em `relatorios_referencia/william_arjona/` (15 arquivos do relatório, o perfil e 23 arquivos da Coleta congelada; período de 10/07/2021 a 18/10/2026). Commit pedido ao usuário.

## Phase 10: Convergence

- [X] T154 Acrescentar a `tests/conferencia/test_fontes_termica.py` (ou à integração da UTN fictícia) a asserção do resultado da DISPF × horas pelo CEG numa térmica (meses-unidade comparados, coincidentes e divergentes), não só a aplicabilidade, per T080 e FR-018 (partial)
- [X] T155 Usar `semanal_em_horas` (`src/tratamento/termica.py`) no cruzamento horário do CVU e do CMO com o despacho e a disponibilidade em `src/analises/termica.py`, ou retirá-la e registrar no rascunho 002 que as horas são levadas à semana operativa que as contém, per FR-040 do rascunho 002 (partial)
- [ ] T156 Registrar na incorporação (fase F), junto com a T153, os desvios aprovados na fase B: o CVU zero sinalizado (decisão do usuário de 20/10/2026) no FR-017 e as figuras e a capa de térmica em `src/relatorio/figuras_comum.py` e `src/relatorio/comum.py`, per FR-017 e T090 (contradicts)

### 20/10/2026 — T095 (portão do fim da fase B), T154 e T155

- `/speckit-converge` (fase B): 3 achados LOW, acrescentados na Phase 10 (T154 a T156); nenhuma violação da constituição.
- **T154**: teste novo em `tests/conferencia/test_fontes_termica.py` com o resultado da DISPF × horas numa térmica (4 meses-unidade, 1 divergente), com o HP somando as horas equivalentes, como nas térmicas do ONS.
- **T155**: `src/analises/termica.py` passa a levar a relação semanal do CVU × CMO à hora com `semanal_em_horas` (FR-040 do rascunho 002) para os cruzamentos com o despacho e a disponibilidade; mesmos números nos testes e na referência da William Arjona.
- **T095**: suíte com 726 aprovados; pyflakes sem aviso; `comparar --todas --coleta` com duas referências: william_arjona sem nenhuma diferença; sao_domingos só com as quatro diferenças da Coleta pela republicação do ONS (cadastro e indicadores, agora publicados em 19/10/2026), aceitas pelo usuário até o próximo congelamento da São Domingos, sem diferença no relatório. Código 6 por essas diferenças aceitas. A T156 fica para o fechamento (fase F).
- **Fase B concluída**; commit pedido ao usuário (código da fase B e referência da William Arjona).

### 20/10/2026 — T096 (cópia de segurança da fase C)

- `python -m src copia-seguranca --motivo antes_fase_C`: código 0; `_backup_2026-10-20_antes_fase_C` criada e conferida (361 arquivos), com `relatorios_referencia/sao_domingos/` e `relatorios_referencia/william_arjona/` (cada `referencia.json` com o mesmo SHA-256 do projeto). Excluída a mais antiga, `_backup_2026-10-19_antes_fase_A_catalogo`; ficam `_backup_2026-10-19_antes_fase_B` e `_backup_2026-10-20_antes_fase_C`.

### 20/10/2026 — T097 (rascunhos da fase C)

- Contratos conferidos nos dados abertos antes dos rascunhos: Fator de capacidade horário (`fator_capacidade_2_di`, arquivos mensais); restrição com detalhe e com a razão semi-horárias (dois instantes por hora, arquivos mensais); na Seriemas 1, o Fator de capacidade e a razão só do conjunto `CJU_MS4FINO` (CEG "-") e a restrição com detalhe das oito usinas do conjunto, cada uma com o seu CEG.
- Seção "Fase C — eólicas e solares" acrescentada aos cinco rascunhos de `ajustes-specs/`:
  - Coleta: FR-051 e FR-053 ajustadas (cobertura e rascunho das bases de renováveis); FR-057 (Fator de capacidade, restrição com detalhe e com a razão, com as variantes e as linhas dos membros para a G2), FR-058 (motor semi-horário, colunas ausentes contadas sem falha) e FR-059 (linha da fase C da decisão R6);
  - Tratamento: FR-041 a FR-044 (semi-horárias e hora cheia, energia cortada só nas semi-horas restritas, razão por semi-hora com o nível, fator de capacidade com as sinalizações) e o recurso inválido sinalizado;
  - Conferência: FR-023 (G1), FR-024 (G2) e FR-025 (G5), sem meta;
  - Análises: FR-058 (seções de renováveis, decisão R19) e FR-059 (C16 a C19, limiares calibrados nas pilotos);
  - Geração do relatório: FR-045 (três seções e quatro figuras), capa, legendas, notas e o resumo executivo das renováveis (energia cortada como indicador de perda; termos novos com o texto a aprovar).
- **T098**: rascunhos levados ao usuário; nenhum código da fase C antes da aprovação.

### 20/10/2026 — T098 (aprovação dos rascunhos da fase C)

- Rascunhos da fase C aprovados pelo usuário ("aprovo"). O código da fase C pode começar (T099 em diante).

### 21/10/2026 — T099, T100, T101, T105 e T106 (Coleta das renováveis e testes da fase C)

- **T105**: em `src/comum/regras.py`, os cinco pacotes e as pastas; em `src/coleta/registro.py`, as entradas `fator_capacidade` (horária, usina ou conjunto), `restricao_detalhe` (semi-horária, só da usina, pelo id ONS e conferida pelo CEG; o id do conjunto fica como texto, sem conferir) e `restricao_razao` (semi-horária, usina ou conjunto), com as variantes eólica e fotovoltaica escolhidas pelo tipo (`registro.pacotes(entradas, tipo)`). A linha da fase C da decisão R6 está em `src/coleta/serie_referencia.py`: EOL e UFV sem a geração própria e com a restrição com detalhe da usina usam esta como série de referência. A Coleta grava a série semi-horária no período, o complemento por hora cheia e, com `[[identificacao.membros]]`, a restrição com detalhe das outras usinas do conjunto (`restricao_membros_extraido.parquet`, só para a G2). O catálogo de usinas ganhou as colunas FC, RDT e RRZ, com a cobertura por variante.
- **T106**: o motor aceita as colunas que faltam em parte dos arquivos (fotovoltaica de 05 a 12/2024) quando a descrição pede (`avisar_colunas_ausentes`): a coluna fica vazia, o arquivo é processado e a auditoria registra "colunas ausentes no arquivo: ...". Achado no caminho: nesses arquivos a marca de irradiância inválida é booleana, e o motor a lia como texto não numérico; `numero_publicado` passou a ler marcas booleanas como 1 e 0 (sem efeito nos conjuntos de hoje, que não têm colunas booleanas). Portão: suíte com 733 aprovados; `comparar --todas --coleta` com william_arjona sem nenhuma diferença e sao_domingos só com as quatro diferenças da Coleta já aceitas (republicação do ONS); código 6 por elas.
- **T099**: `tests/coleta/test_conjuntos_renovaveis.py` (6 testes) e ajustes em `test_registro.py`, `test_dicionarios.py`, `test_perfil.py`, `test_catalogo_usinas.py` e `brutos_catalogo.py`.
- **T100**: `tests/tratamento/test_renovavel.py` (8 testes): energia cortada só nas semi-horas restritas, semi-hora sem a marca contada e fora do total, hora cheia pela média das duas meias-horas com a hora incompleta ausente e contada, recurso inválido, fator de capacidade com nível e sinalizações, razão com o nível, restrição como série de referência, membros em hora cheia e gravação/leitura. Confirmado nos dados do ONS que o instante das semi-horas é o do início (00:00 a 23:30).
- **T101**: `tests/conferencia/test_fontes_renovaveis.py` (6 testes): G1 só com pares do mesmo nível; G2 só nas horas com toda a composição vigente, com as horas incompletas contadas; G5; aplicabilidade pelos níveis (G1 sem par, G2 sem os membros ou sem a geração do conjunto, G5 com níveis diferentes).

### 21/10/2026 — T102 a T104 e T107 a T111 (implementação da fase C)

- **T107** (`src/tratamento/renovavel.py`, chamado em `src/tratamento/etapa.py`): os arquivos do data-model 6.2. Restrição com detalhe por semi-hora (a do arquivo publicado por último, duplicatas conflitantes contadas), com `sinal_recurso_invalido`, `restrita`, `sem_marca_restricao` e `energia_cortada_mwh` = máx(estimada − verificada, 0) × 0,5 h só nas semi-horas com `flg_geracaorestrita = 1` (vazia sem a marca); a razão (REL, CNF, ENE) e o nível dela na mesma semi-hora; a hora cheia pela média das duas meias-horas, com a hora incompleta ausente e contada; o fator de capacidade horário com o nível, `sinal_fc_fora_0_1` e `sinal_acima_capacidade` (folga de 1 MW); os membros do conjunto em hora cheia, só para a G2. Na série de referência da restrição com detalhe, a base horária comum vem dela, com a disponibilidade e a programação só quando estão no nível da usina (a base é da usina; números do conjunto não entram nela).
- **T108** (`src/conferencia/fontes.py`, `aplicabilidade.py`, `etapa.py`, `resultado.py`): G1 compara as fontes da geração (Geração por usina, Fator de capacidade e as duas restrições em hora cheia) duas a duas e só no mesmo nível; G2 soma a restrição com detalhe da usina e dos membros só nas horas com toda a composição vigente (horas incompletas contadas) e compara com a Geração por usina do conjunto; G5 compara a Programação diária com o programado do Fator de capacidade. Aplicabilidade pelos níveis das bases (G1 sem duas fontes no mesmo nível; G2 fora de conjunto, sem os membros ou sem a geração do conjunto; G5 com níveis diferentes), com o motivo em `nao_aplicaveis.csv`. As bases da fase C saíram de "ainda não coletadas pelo pipeline".
- **T109** (`src/analises/renovavel.py`, em `analisar_sem_evt` e em `ResultadosAnalise.renovavel`): fator de capacidade publicado (Σ verificada ÷ Σ capacidade, com o nível) por mês e por ano; energia cortada por mês, por ano e por razão, com a estimada das semi-horas com a marca como base do percentual, as semi-horas sem a marca contadas e a diferença bruta à parte; recurso × geração por faixa (2 m/s; 100 W/m²) sem as semi-horas inválidas, contadas; os maiores desvios da programação (só EOL e UFV); omissões com o motivo (sem a base na cobertura, ou sem horas no período). As horas ausentes da série de referência vêm da restrição quando ela é a referência.
- **T110** (`src/analises/conclusao.py`): C16 (energia cortada ≥ 5 % da estimada, pontos de atenção), C17 (recurso inválido ≥ 10 % das semi-horas, a verificar em campo), C18 (fator de capacidade publicado da usina, por ano completo, abaixo de GF ÷ potência; só com a garantia física no perfil e período mínimo de 12 meses) e C19 (desvio médio absoluto ≥ 10 % da potência, só com a programação da usina; a confirmar com o agente). Limiares iniciais em `regras.py`, citados na nota da conclusão gerada do catálogo; as regras comuns da fase A continuam fora das eólicas e solares (achado A11).
- **T111** (`src/relatorio/secoes_renovavel.py` e integração): as três seções em ordem fixa depois do perfil horário (fator de capacidade, energia cortada por restrição de operação, recurso × geração) e os maiores desvios na seção de programação; quatro figuras em seaborn (fator de capacidade mensal, energia cortada mensal por razão empilhada, geração por faixa de recurso, desvio da programação), com a paleta validada pelo script da skill de visualização (azul, laranja e verde da ordem categórica; o calculado tracejado para não sumir sob o publicado); a capa com a energia cortada (% da estimada); a coluna "Energia cortada (MWh, % est.)" nos indicadores anuais e no resumo executivo (até seis colunas); legendas com o id ONS e o CEG na restrição com detalhe e "conjunto de usinas, id ONS CJU_…" nos dados do conjunto; G1, G2 e G5 nas legendas e nas abas CONF_G1/G2/G5; abas REN_*; notas enxutas. Na série de referência da restrição com detalhe, o relatório cita essa base (conjunto `referencia` no mapa de fontes) e as notas de conjunto da capa, das figuras e da tabela anual passaram a depender do nível da base horária, não de qualquer número do conjunto. Conferências das eólicas e solares só entram nas legendas, na aba FONTES e no resumo quando aplicadas (as demais ficam nas notas, decisão R13). Nenhum termo novo entra no resumo executivo, e o glossário não mudou.
- **T102** (`tests/analises/test_renovavel.py`, 7 testes), **T103** (C16 a C19 em `tests/analises/test_conclusao.py`, com o catálogo C1 a C19) e **T104** (EOL e UFV fictícias com o fator de capacidade e as restrições em `brutos_ficticios.py`; perfis com a cobertura da fase C; a UFV num conjunto com um membro, a restrição como série de referência desde 25/01/2024 e o arquivo de janeiro no esquema antigo; a EOL com vento inválido, semi-horas restritas com REL, CNF e ENE e a programação de três dias; quatro testes novos em `tests/integracao/test_usinas_ficticias.py`). Desvio registrado da T104: a série "desde 10/2021" da EOL ficou como restrição desde 15/01/2024, dentro do período sintético de jan e fev/2024.
- Achados no caminho: a correlação da programação com série constante agora é ausente sem a divisão por zero do numpy (saída igual); a Coleta passou a gravar o `nivel` no fator de capacidade e na razão extraídos, como no data-model 6.1.
- Portão: suíte com 773 aprovados; pyflakes sem aviso; `comparar --todas --coleta` com william_arjona sem nenhuma diferença e sao_domingos só com as quatro diferenças da Coleta já aceitas (código 6 por elas): o relatório das duas referências não mudou.

### 21/10/2026 — T112 (perfis da Seriemas 1 e da Praia Formosa)

- Catálogo nacional remontado com o portal (`python -m src usinas --tipo UFV --estado MS`), já com as colunas FC, RDT e RRZ: Seriemas 1 com programação, geração, fator de capacidade e razão da restrição do conjunto CJU_MS4FINO e restrição com detalhe própria (MSSRI1).
- Achado no rascunho da Praia Formosa: o cadastro publica o id ONS com espaço no fim ("CEUFM "), e o catálogo não ligava o código de programação CEUFM à usina (programação "ausente"). Corrigido em `src/coleta/catalogo_usinas.py` (o id sem os espaços das pontas, também no id do conjunto), com o caso no `brutos_catalogo.py`; a programação passou a "proprio".
- Rascunhos gerados com `python -m src perfil` e completados com o usuário:
  - **Seriemas 1** (`usinas/seriemas_1/perfil.toml`): potência da UFV de 50 MW (Capacidade de geração, 2 unidades); a potência autorizada de 2,507 MW do cadastro do ONS é uma agregação do complexo, segundo o usuário, e os relatórios são por UFV. Garantia física de 16,1 MWmed, a da própria UFV pelo CEG (cada Seriemas 1 a 8 tem a sua), da Portaria nº 3.141, de 16 de junho de 2026, na base de garantias físicas vigentes da EPE (planilha de 07/2026, referência 30/06/2026). Oito membros do conjunto desde 13/04/2026.
  - **Praia Formosa** (`usinas/praia_formosa/perfil.toml`): 105 MW em 6 unidades; programação própria CEUFM; sem garantia física, porque a usina não consta da base da EPE, que não traz as parcelas do PROINFA (a C18 não é avaliada sem ela).
- Nomes do relatório ajustados como no perfil da William Arjona ("UFV Seriemas 1", "EOL Praia Formosa"); os dois perfis com `situacao = "conferido"`, carregados sem erro e sem diferença em relação ao catálogo.

### 21/10/2026 — T113 e T114 (relatórios piloto da fase C) e decisões da T115

- **T113**: `python -m src completo --usina <slug> --data-geracao "21/10/2026 10:00"` com o portal: Seriemas 1 em 1,8 min e Praia Formosa em 8,1 min, código 0 nas duas. Itens do quickstart 5:
  - **Seriemas 1**: série de referência da usina (restrição com detalhe, MSSRI1) de 22/08/2026 a 19/10/2026; sazonalidade omitida (3 meses distintos); geração, fator de capacidade, razão da restrição e programação identificados como do Conj. Inocência 230 kV (CJU_MS4FINO), com a composição de 8 usinas, nunca divididos; energia cortada da usina (1.127 MWh, 16,3 % da estimada) com a razão do conjunto (ENE); C18 e C19 não avaliadas, com o motivo. G1 com 100 % de coincidência; G5 com 100 %; G2 com 1.105 de 1.296 horas coincidentes: as 191 divergências estão em ago e set/2026, quase todas das 5h às 8h, e em out/2026 a soma das 8 usinas e a geração do conjunto coincidem em todas as horas (achado de dado, sem ajuste); 120 horas sem a Seriemas 8, que começa em 27/08/2026, contadas fora da soma. O cadastro diverge na potência (2,5 MW autorizados × 50 MW do perfil, a agregação do complexo explicada pelo usuário na T112).
  - **Praia Formosa**: fator de capacidade desde 07/2009; energia cortada só nas semi-horas restritas, 184.769 MWh de 10/2021 a 10/2026 contra 355.038 MWh da diferença bruta (o quickstart esperava cerca de 181 e 350 GWh); 13.157 semi-horas com vento inválido fora das faixas e contadas; desvio médio e maiores desvios da programação; G1 (98,3 %) e G5 (94,5 %) registradas.
- **Achado da T113 e decisão do usuário (estimativa ausente)**: o ONS publica geração estimada 0 em semi-horas em que a usina gerou (Seriemas 1: 341 das 609 semi-horas com irradiância acima de 200 W/m², nos primeiros meses; Praia Formosa: cerca de 14 % das semi-horas com vento acima de 6 m/s, raras desde 2025). Decisão de 21/10/2026: estimada 0 com geração verificada acima de 1 MW é estimativa ausente, sinalizada (`sinal_estimada_ausente`), contada, fora dos totais e das médias da estimada; na semi-hora restrita, o corte não é calculado, e a tabela anual compara a verificada e a estimada nas mesmas semi-horas, com a coluna "Restritas sem estimativa" (385 na Seriemas 1; 441 na Praia Formosa). O total cortado e o percentual não mudaram. Rascunhos 002 (FR-042), 004 (FR-058) e 005 (notas) ajustados.
- **Decisões da T115 (21/10/2026)**: (1) limite físico do recurso: vento acima de 40 m/s e irradiância acima de 1.500 W/m² ficam fora das faixas e são contados (a Praia Formosa tem 111 semi-horas com vento de até 246 m/s, em mar e abr/2024, sem a marca do ONS); (2) limiares: C16 em 5 %, C17 em 10 % e C18 como propostos; C19 sobe para 15 % da potência (a Praia Formosa, com 10,4 %, deixa de ter o item); (3) glossário: "constrained-off: redução da geração da usina por comando do ONS, por razão externa a ela (indisponibilidade externa, confiabilidade elétrica ou razão energética)". Constantes em `regras.py`, rascunhos 004 e 005 ajustados, testes novos (estimativa ausente, limite físico) e as fictícias com os dois casos.
- **T114**: nas duas pilotos, nenhum termo de parecer ("satisfat", "cumpre") e nenhum identificador das outras pilotos no relatório e no resumo; nenhum "nan"; todo número do conjunto identificado nas legendas ("conjunto de usinas, id ONS CJU_MS4FINO"). Seriemas 1: 11 seções, 15 páginas, resumo de 1 página; Praia Formosa: 12 seções, 20 páginas, resumo de 2 páginas.
- Portão intermediário: suíte com 775 aprovados antes das decisões da T115 e os testes afetados verdes depois delas; `comparar --todas --coleta`: relatórios das duas referências sem diferença; na Coleta, a São Domingos com as quatro diferenças já aceitas e, agora, também a William Arjona com diferenças de dados publicados pelo ONS depois do congelamento (geração, disponibilidade e despacho republicados em 20/10/2026 e um dia a mais, 19/10/2026, baixados pelas pilotos), a levar ao usuário.

### 21/10/2026 — T115 (calibração, aprovação e referências da fase C)

- Limiares calibrados nas pilotos e aprovados pelo usuário (decisões registradas na T113/T114): C16 em 5 %, C17 em 10 %, C18 como proposta e C19 em 15 %; limite físico do recurso (40 m/s; 1.500 W/m²); glossário com "constrained-off".
- Relatórios e resumos da Seriemas 1 e da Praia Formosa aprovados pelo usuário em 21/10/2026 ("estão excelentes"), gerados com `--data-geracao "21/10/2026 10:00"`.
- Referências registradas com `python -m src referencia --usina <slug> --data-geracao "21/10/2026 10:00" --aprovado-em "21/10/2026"`: `relatorios_referencia/seriemas_1/` e `relatorios_referencia/praia_formosa/`, código 0 nas duas. Ainda sem commit: pedido ao usuário no fim do portão (T116).

## Phase 11: Convergence

- [X] T157 Comparar a Programação diária com a geração verificada no nível do conjunto quando as duas estão nele e a série de referência é a restrição com detalhe da usina (UFV ou EOL em conjunto, como a Seriemas 1): desvio médio e maiores desvios do conjunto, identificados como do conjunto, na seção de programação, sem entrar na base horária da usina e sem a C19 (só com a programação da usina), per US3/AC4 e FR-021 (partial)
- [ ] T158 Registrar na incorporação (fase F), junto com a T153 e a T156, os desvios aprovados na fase C: as figuras e a capa das renováveis em `src/relatorio/figuras_comum.py` e `src/relatorio/comum.py`; a estimativa ausente (`sinal_estimada_ausente`) no data-model 6.2 e o limite físico do recurso no FR-017 (decisões do usuário de 21/10/2026); a restrição da EOL fictícia desde 15/01/2024 na T104, per plan.md, data-model 6.2 e FR-017 (contradicts)

### 21/10/2026 — T116 em curso: convergência da fase C e T157

- **Portão (primeira passada)**: suíte com 776 aprovados; pyflakes sem aviso; `comparar --todas --coleta` com quatro referências: seriemas_1 e praia_formosa sem nenhuma diferença; sao_domingos com as quatro diferenças da Coleta já aceitas; william_arjona com diferenças só da Coleta, de dados publicados pelo ONS depois do congelamento (republicação de 20/10/2026 e o dia 19/10/2026); relatórios das duas idênticos.
- **`/speckit-converge` (fase C)**: 2 achados, acrescentados na Phase 11: T157 (HIGH, partial: US3/AC4, a aderência à programação no nível do conjunto) e T158 (LOW: desvios da fase C a registrar na incorporação, com a T153 e a T156). Nenhuma violação da constituição. O usuário pediu para executar as tarefas.
- **T157**: com a série de referência na restrição com detalhe da usina e a programação e a Geração por usina no nível do conjunto, as Análises comparam a programação com a geração do conjunto numa base à parte (`base_programacao_conjunto` em `src/analises/comum_tipos.py`), fora da base horária da usina; a seção "Programação diária × geração verificada" e os maiores desvios aparecem identificados como do conjunto, e a C19 continua só com a programação da usina. Nas legendas, o apelido `geracao_programacao` cita a Geração por usina do conjunto nesse caso. Junto, a programação conferida pela G5 deixou de constar como "sem outra fonte" nas tabelas comuns de programação das eólicas e solares (`_sem_outra_fonte` em `src/relatorio/fontes.py`). Testes: unitário da base do conjunto e asserções na UFV fictícia.
- Efeito nas pilotos (regeradas com `--sem-portal --data-geracao "21/10/2026 10:00"`): a Seriemas 1 ganha a seção 9 (1.296 horas de 27/08 a 19/10/2026; programação do conjunto de 0 MW de 27 a 31/08 com 82 MW gerados em média), a figura 13 e as abas PROG_* e REN_DESVIOS_PROGRAMACAO, e o resumo passa de 15 para 17 páginas do relatório citado; a Praia Formosa muda só as legendas das duas tabelas comuns de programação (e as linhas da aba FONTES). As referências das duas, registradas antes da T157 e ainda sem commit, precisam da aprovação do usuário para serem refeitas. São Domingos e William Arjona sem diferença no relatório.

### 21/10/2026 — T116 (portão do fim da fase C)

- O usuário aprovou as mudanças da T157 nos dois relatórios piloto. As duas referências, ainda sem commit, foram removidas e registradas de novo com `python -m src referencia --usina <slug> --data-geracao "21/10/2026 10:00" --aprovado-em "21/10/2026"`, iguais aos relatórios atuais.
- Portão final: suíte com 777 aprovados; pyflakes sem aviso; `/speckit-converge` feito (Phase 11: T157 concluída, T158 para a fase F); `comparar --todas --coleta` com quatro referências: seriemas_1 e praia_formosa sem nenhuma diferença; relatórios da sao_domingos e da william_arjona idênticos; na Coleta, a sao_domingos com as quatro diferenças já aceitas (republicação do ONS de 19/10/2026) e a william_arjona com as diferenças de dados publicados depois do congelamento dela (republicação de 20/10/2026 e o dia 19/10/2026), propostas ao usuário para o mesmo tratamento. Código 6 só por essas diferenças da Coleta.
- Fase C fechada no código; falta o commit do usuário (código, testes, rascunhos, perfis e as duas referências novas).

### 22/10/2026 — T117 (cópia de segurança da fase D)

- Pré-condição: o código, os rascunhos e as referências da fase C já estavam no commit 03b0b7e (árvore limpa).
- `python -m src copia-seguranca --motivo antes_fase_D`: código 0; `_backup_2026-10-22_antes_fase_D` criada e conferida (472 arquivos), com as quatro referências (`sao_domingos`, `william_arjona`, `seriemas_1` e `praia_formosa`; cada `referencia.json` com o mesmo SHA-256 do projeto) e o `LEIA-ME.txt` listando-as. Excluída a mais antiga, `_backup_2026-10-19_antes_fase_B`; ficam `_backup_2026-10-20_antes_fase_C` e `_backup_2026-10-22_antes_fase_D`.

### 22/10/2026 — T118 (rascunhos da fase D)

- Contratos conferidos nos arquivos do ONS já baixados (Geração por usina de 2000 a 10/2026, Programação diária de 10/2024 a 10/2026, Composição dos conjuntos, catálogo):
  - a geração do Conj. Chapadão (`CJU_MSCAO`) vai de 01/08/2012 a 19/10/2026, sempre publicada como "TÉRMICA"/"Biomassa", com outubro/2021 ausente; a Bandeirante só entra no conjunto em 22/08/2019;
  - as linhas próprias das quatro PCH existem desde 01/05/2026, todas sem valor;
  - a programação do conjunto trocou os quatro códigos em 07/2025 (`MSCAO-9761/9762/9763/9766` até 02/07/2025; `MSCAO-9764/9765/9784/10205` desde 05/07/2025), e o catálogo de hoje só conhece os quatro atuais;
  - nenhuma usina de MS tem Dados hidrológicos sem a EVT (no Brasil, só a UHE Pimental e a UHE Canastra).
- Seção "Fase D" acrescentada a quatro rascunhos de `ajustes-specs/` (o Tratamento não muda):
  - Coleta: FR-051 e FR-053 (códigos de programação de todo o período, com o primeiro e o último dia); FR-054 (período da usina em conjunto recortado pela entrada e saída dela na composição; trechos sem mudança); FR-047/FR-048 (período das linhas próprias sem valor); FR-060 (`capacidade_membros.csv`) e FR-061 (`tipo_publicado.csv`);
  - Conferência: FR-026 (alinhamento da hidrologia pela geração na hidrelétrica sem EVT; tarefa T150);
  - Análises: FR-060 (composição e geração do conjunto por trecho, tipo publicado na qualidade dos dados, nada dividido nem na conclusão) e FR-061 (afluência sem a EVT; tarefa T150);
  - Geração do relatório: FR-046 (seção do conjunto, com tabela, figura e legendas; a tabela de trechos da seção 1 sem a coluna de composição nas usinas em conjunto) e FR-047 (seção de afluência sem a EVT), notas e o efeito nas referências (a Seriemas 1 ganha a seção do conjunto e terá a referência refeita com a aprovação do usuário).
- Pontos levados ao usuário com a T119: o recorte do período pela composição, a seção do conjunto também na Seriemas 1, a potência das usinas da composição e o alinhamento da hidrologia pela geração.

### 22/10/2026 — T119 em curso (decisões do usuário sobre os rascunhos da fase D)

- Quatro pontos levados ao usuário, todos decididos pela opção proposta:
  1. **período da usina em conjunto**: recortado pela entrada e saída da usina na composição (Bandeirante desde 22/08/2019, e não desde 01/08/2012);
  2. **seção do conjunto**: em toda usina em conjunto, inclusive a Seriemas 1, cuja referência será refeita com a aprovação do usuário na T126;
  3. **potência das usinas da composição**: incluída (`capacidade_membros.csv`), sem dividir número do conjunto e sem fator de capacidade do conjunto;
  4. **hidrologia sem EVT** (T150): hora conferida pela correlação da vazão turbinada com a geração da usina (−1, 0 e +1 h), sem meta.
- Decisões anotadas nos rascunhos 001 (FR-054, FR-060), 003 (FR-026) e 005 (FR-046). Falta a aprovação dos rascunhos da fase D como um todo; nenhum código antes dela.

### 22/10/2026 — T119 (aprovação dos rascunhos da fase D) e republicação na Coleta da William Arjona

- Rascunhos da fase D aprovados pelo usuário ("aprovado os rascunhos"), com as quatro decisões já anotadas. O código da fase D pode começar (T120 em diante), com a T150 e os itens novos da Coleta (FR-051, FR-053, FR-054, FR-060 e FR-061 do rascunho 001).
- Decisão do usuário ("OK para tratativas William Arjona"): as diferenças da Coleta da William Arjona causadas por dados que o ONS publicou depois do congelamento dela (republicação de 20/10/2026 e dias novos) contam como aprovadas em `comparar --todas --coleta`, como as da São Domingos, até o próximo congelamento; o relatório refeito a partir da Coleta congelada continua tendo de dar "nenhuma diferença".

### 22/10/2026 — fase D, código e testes (T120 a T123, T150 e os itens novos da Coleta)

- **Coleta** (rascunho 001):
  - FR-051 e FR-053: o catálogo lê todos os arquivos da Programação diária (733 em 22/10/2026), e `programacao.csv` ganha `primeiro_dia` e `ultimo_dia`; o nível da cobertura continua pelo arquivo mais recente (R3). O rascunho do perfil traz todos os códigos ligados, com os períodos em comentário (Bandeirante: os quatro `MSCAO-976x` até 02/07/2025 e os quatro atuais desde 05/07/2025).
  - FR-054: na usina em conjunto sem série própria, a Composição dos conjuntos é coletada antes da série de referência, e as horas do conjunto só contam com a usina na composição (`intervalos_da_usina` e `no_intervalo` em `src/coleta/serie_referencia.py`; resumo `composicao_da_usina`); usina fora da composição: código 2, com a mensagem.
  - FR-047/FR-048: as linhas próprias sem valor contadas só no período (antes, o mês inteiro do arquivo) e com a primeira e a última hora (`linhas_usina_sem_valor_periodo`).
  - FR-060: `capacidade_membros.csv` (as unidades de cada usina da composição no período, pelo CEG, sem conferir o estado); FR-061: `tipo_publicado.csv` (tipo e combustível publicados na série do conjunto, por trecho).
- **Conferência** (rascunho 003, FR-026): `alinhamento_hidrologia` em `src/conferencia/vazoes.py` (correlação da vazão turbinada com a geração da usina com −1, 0 e +1 h; confirmada quando a de 0 h é a maior; sem meta; CSV com os três deslocamentos). Precisão anotada no rascunho 003: fora das hidrelétricas, sem linha em `nao_aplicaveis.csv`, para os relatórios aprovados da William Arjona e da Praia Formosa não mudarem.
- **T122** (`src/analises/conjunto.py`, rascunho 004, FR-060): trechos de composição (os trechos da Coleta com a mesma composição juntos), a geração do conjunto por trecho e por mês, a composição com a potência das unidades em operação em algum momento do trecho (a usina sem unidade cadastrada fica sem potência e é contada), o tipo publicado comparado com os tipos da composição e a constatação "Composição do conjunto"; integrado em `analisar_sem_evt` (a geração do conjunto vem da base horária, quando é a série de referência, ou da Geração por usina do conjunto, na eólica ou solar com série própria). A omissão "seção ainda não gerada pelo pipeline" saiu.
- **T150** (rascunho 004, FR-061): `analisar_hidrologia_sem_evt` em `src/analises/hidrologia.py` (tabela anual e médias mensais, sem as faixas de afluência nem os dias com parada com EVT; sem a hora confirmada, só a cobertura e o resultado da conferência) e a constatação "Afluência e vertimento" das usinas sem EVT.
- **T123** (`src/relatorio/secoes_conjunto.py`, rascunho 005, FR-046 e FR-047): seção "Composição e geração do conjunto" depois das seções do tipo (tabela por trecho, figura 14 `14_geracao_do_conjunto_por_trecho.png` e a composição, uma linha por usina, com a potência), a tabela de trechos da seção 1 sem a coluna dos CEGs nas usinas com a seção, a linha da capacidade das usinas do conjunto na tabela dos conjuntos do ONS, a seção "Afluência, vertimento e nível do reservatório (ONS)" das hidrelétricas sem EVT (tabela anual e figura 15 `15_vazoes_mensais.png`), notas, legendas e as abas CONJ_* e HID_*. As figuras ficam em `src/relatorio/figuras_comum.py`, como nas fases B e C (desvio a registrar na fase F, com a T153); paleta dos trechos validada com o script da skill de visualização (todas as verificações passam; aviso de contraste compensado pela legenda e pela tabela), um eixo só em cada figura.
- **Achado no caminho (fase C), corrigido**: no resumo executivo, a linha "Fontes" usava sempre o identificador da usina; na Seriemas 1, a Geração por usina, o Fator de capacidade e a Restrição com a razão apareciam como "(id ONS MSSRI1)", sendo do conjunto. Agora usa o identificador com o nível, como as legendas (decisão R15). Não muda a São Domingos, a William Arjona nem a Praia Formosa.
- **Testes**: T120 em `tests/analises/test_conjunto.py` (11), T150 em `tests/analises/test_hidrologia_sem_evt.py` (4) e em `tests/conferencia/test_conferencias.py` (3); T121 em `tests/integracao/test_usinas_ficticias.py`: a PCH fictícia entra no conjunto em 10/01/2024 (período recortado), uma térmica sai em 15/02/2024 e o conjunto é publicado como "TÉRMICA" (três trechos de composição, a divergência na constatação, 1.224 linhas próprias sem valor de 10/01 a 29/02/2024, omissões e a frase da conclusão); a CGH fictícia (geração própria) ganhou os Dados hidrológicos e é a hidrelétrica sem EVT da T150, sem a seção do conjunto; a UFV fictícia em conjunto ganha a seção, sem a nota do período. Desvio registrado da T121: a CGH fictícia tem geração própria, por isso não tem a seção do conjunto; o caso da CGH em conjunto é o mesmo caminho da PCH, cujo conjunto fictício tem uma CGH. Ajustes nos testes do catálogo, do rascunho, da série de referência, da aplicabilidade, das fontes e da estrutura. Suíte: 810 aprovados; pyflakes sem aviso.
- **Portão intermediário** (`comparar --todas --coleta`): a primeira passada achou a conferência nova citada na aba FONTES e no resumo da São Domingos (caminho da EVT); corrigido (`conferencia_feita` só a aceita no resultado da hidrelétrica sem EVT, com teste). Na segunda passada: São Domingos, relatório sem diferença e só as quatro diferenças aceitas da Coleta; William Arjona, relatório sem diferença e só as diferenças da Coleta aceitas pelo usuário hoje; Praia Formosa sem diferença; Seriemas 1 com as mudanças decididas (seção do conjunto, três abas, `capacidade_membros.csv` na Coleta) e a linha "Fontes" do resumo corrigida, a levar ao usuário na T126.

### 22/10/2026 — T124 (perfil da PCH Bandeirante)

- Catálogo remontado com os arquivos locais (`python -m src usinas --sem-portal --estado MS --tipo PCH`), já com os códigos de programação de todo o período: `CJU_MSCAO` com `MSCAO-9761`, `-9762`, `-9763` e `-9766` de 01/10/2024 a 02/07/2025 e `MSCAO-9764`, `-9765`, `-9784` e `-10205` desde 05/07/2025.
- Rascunho com `python -m src perfil --ceg PCH.PH.MS.032163-0.01 --slug bandeirante`: 20 campos do ONS e 4 pendentes (a fonte; garantia física, IP e TEIF opcionais). Os quatro códigos `MSCAO-*` pedidos na tarefa são agora oito, com os períodos em comentário.
- Decisão do usuário (22/10/2026): perfil completado só com os dados do ONS, como o da William Arjona: nome "PCH Bandeirante", nome curto "Bandeirante", 3 unidades de 9,3333 MW (Capacidade de geração), início em 2019, sem garantia física, IP e TEIF de referência. `situacao = "conferido"`; o `perfil` não mostra diferença em relação ao catálogo.

### 22/10/2026 — T125 (relatório da PCH Bandeirante)

- `python -m src completo --usina bandeirante --data-geracao "22/10/2026 10:00"` com o portal: 3 min, código 0 em todas as etapas. Período de 22/08/2019 (entrada da usina no conjunto) a 20/10/2026, 62.064 horas do conjunto; outubro/2021 ausente (744 h, listadas).
- **Achado e correção na primeira execução**: a seção de programação saiu omitida ("sem horas com a programação e a geração verificada no mesmo nível"), porque a soma por patamar do Tratamento pedia todos os oito códigos no mesmo dia, e o conjunto trocou os quatro códigos em 07/2025. Corrigido em `src/tratamento/programacao.py` (`somar_codigos`: cada código vale do primeiro ao último dia em que aparece; o código vigente sem valor ainda deixa a soma ausente), com teste; precisão anotada no rascunho 001 (FR-053). Nenhuma referência aprovada tem mais de um código. Refeito com `--sem-portal`.
- **Quickstart 6**: geração do Conj. Chapadão por trecho de composição (três: 8 usinas, PCH e UTE, até 26/09/2019; 9 usinas até 30/06/2025; só as 4 PCH desde 01/07/2025, 47,0 MWmed contra 78,5 MW somados); a nota de que o ONS não publica a geração da usina isolada; a disponibilidade e os indicadores oficiais omitidos, com o motivo; as 4.152 linhas próprias sem valor, de 01/05/2026 a 20/10/2026, na qualidade dos dados; a conclusão sem itens, com a frase. Também a divergência do tipo publicado, na constatação: o ONS publica a série do conjunto como "TÉRMICA (Biomassa)" de 01/07/2025 a 20/10/2026, quando a composição tem só PCH (nas duas primeiras composições, com as UTE, o tipo corresponde).
- **Seção 8 do quickstart**: nenhuma ocorrência de "satisfat" ou "cumpre" no relatório e no resumo; nenhum identificador das outras pilotos (MSUHSD, CEUFM, MSSRI1, PRUHSD, MSUTWI); nenhum "nan"; todo número do conjunto identificado nas legendas ("conjunto de usinas, id ONS CJU_MSCAO").
- Relatório com 10 seções, 14 páginas, 5 figuras e 20 abas; resumo executivo de 1 página (263 palavras). Programação do conjunto × geração do conjunto: 17.472 horas comuns de 01/10/2024 a 20/10/2026, correlação de 0,92, 20 dias sem arquivo.
- Suíte com 811 aprovados; pyflakes sem aviso.

### 22/10/2026 — decisões do usuário sobre o relatório da Bandeirante e o relatório em duas partes

- **Pergunta do usuário** (ao ver o relatório da Bandeirante): e os dados da usina especificamente? A parte do conjunto ficaria melhor só antes da conclusão, para ver quanto a PCH pesa no todo.
- **Conferido nos dados abertos do ONS**: nada da operação da Bandeirante isolada. Só a ficha do cadastro, as unidades (3 × 9,33 MW, em operação desde 12/10/2019), a entrada no conjunto (22/08/2019) e as linhas próprias na Geração por usina desde 05/2026, todas sem valor. Os quatro códigos `MSCAO-*` da Programação diária têm o mesmo valor em 100 % dos patamares (o programado do conjunto dividido em partes iguais), em cada um dos dois grupos de códigos: não são da usina.
- **Decisões** (perguntas com as opções recomendadas escolhidas):
  1. relatório em **duas partes** na usina em conjunto sem série própria: a usina, logo depois da fonte e cobertura, e a operação do conjunto, logo antes da conclusão (rascunho 005, FR-048); a Seriemas 1 (série própria) fica com a estrutura da FR-046;
  2. o **peso da usina na potência do conjunto**, por composição, só a potência, sem estimar a geração (rascunho 004, FR-060): Bandeirante com 6,7 % de 27/09/2019 a 30/06/2025 e 35,7 % desde 01/07/2025;
  3. a geração da usina pela **CCEE** (download manual) fica registrada como proposta para uma spec futura; o relatório diz onde a geração da usina pode ser obtida.
- **Implementação**: `peso_da_usina`, `em_duas_partes` e a constatação "A usina no conjunto" em `src/analises/conjunto.py`; em `src/relatorio/estrutura.py`, as seções "A usina no conjunto" e "Operação do conjunto <nome> (<id>)" e as seções dos números do conjunto fora do relatório em duas partes (viram subseções da parte do conjunto), com o mapa das constatações desse caso; em `src/relatorio/comum.py`, os blocos das duas partes e a tabela do peso; bloco `subtitulo` no Markdown e no PDF (no PDF, a subseção vai junto com a figura seguinte, ou com espaço para o início da tabela); aba CONJ_PESO_USINA; o resumo executivo remete à parte do conjunto para a evolução anual. A proposta de título da seção 3 ("Série temporal da geração", sem a disponibilidade) ficou resolvida pela reestruturação: na Bandeirante, a subseção é "Série temporal da geração do conjunto".
- **Bandeirante refeita** (`--sem-portal`, "22/10/2026 10:00"): 6 seções (fonte e cobertura; a usina no conjunto; qualidade dos dados; operação do Conj. Chapadão, com seis subseções; conclusão; notas), 13 páginas, conferidas página a página.
- **Testes**: a PCH fictícia em duas partes (o peso de 34,8 %, 34,8 % e 100 % nas três composições, a última só com a PCH e a CGH membro sem unidade cadastrada); unitários do peso e da condição; estrutura da `pch_alfa`. Suíte com 814 aprovados; pyflakes sem aviso.

## Phase 12: Convergence

- [X] T159 CRITICAL: conferir as unidades das usinas do conjunto em `capacidade_membros.csv` (`_gravar_capacidade_membros`, `src/coleta/etapa.py`) com um campo de conferência, o subsistema da linha da composição (o estado não serve: o Conj. Chapadão teve UTE de GO), e contar na auditoria as linhas em que só o CEG confere, com teste per Constitution IV (contradicts)
- [X] T160 Levar a divergência do tipo publicado (`tipo_publicado.csv` × tipos da composição) para a constatação da qualidade dos dados, sem repetir a frase na seção do conjunto, com o teste ajustado per rascunho 004, FR-060, e caso de borda da spec 006 (partial)
- [X] T161 Testar a Coleta da usina em conjunto ausente da composição do conjunto declarado no perfil: código 2, com a mensagem que cita o id do conjunto e o CEG per rascunho 001, FR-054 (partial)
- [ ] T162 Registrar na incorporação (fase F), com a T153, a T156 e a T158, os desvios e acréscimos da fase D: figuras em `figuras_comum.py` e blocos e notas em `comum.py` e `secoes_conjunto.py` (a T123 citava `figuras.py` e `conteudo.py`); os arquivos novos (`capacidade_membros.csv`, `tipo_publicado.csv`, `alinhamento_hidrologia.csv`) e os campos novos de `ResultadosAnalise` (`conjunto`, `hidrologia` das usinas sem EVT) no data-model; o relatório em duas partes (FR-048) na tabela da decisão R14; o bloco `subtitulo`; as abas CONJ_* e HID_*; a linha "Fontes" do resumo com o nível; os desvios da T121 (CGH fictícia com geração própria) e da T124 (oito códigos de programação) per plan.md, data-model e research R14 (contradicts)

### 22/10/2026 — T126 (aprovação e referências) e convergência da fase D (T159 a T161)

- **Aprovação do usuário** ("o resto está ok"): o relatório e o resumo da PCH Bandeirante em duas partes, as mudanças da Seriemas 1 (seção do conjunto e a linha "Fontes" do resumo) e as diferenças da Coleta da Praia Formosa causadas por dados que o ONS publicou depois do congelamento dela (cadastro republicado e o dia 20/10/2026, baixados pela Coleta da Bandeirante com o portal), contadas como aprovadas até o próximo congelamento, como as da São Domingos e da William Arjona. O usuário observou que a conclusão da PCH fica sem itens porque o ONS só publica o conjunto: é a regra da decisão R16 (indício só com dado da usina); a geração da usina pela CCEE ficou como proposta para uma spec futura.
- **Referências**: etapas 2 a 5 refeitas das duas usinas a partir da Coleta de cada uma; `python -m src referencia` da Bandeirante ("22/10/2026 10:00", aprovada em 22/10/2026) e da Seriemas 1 ("21/10/2026 10:00", aprovada em 22/10/2026), código 0. Cinco referências.
- **`/speckit-converge`** (fase D): 4 achados, na Phase 12 (T159 a T162): T159 CRITICAL (princípio IV: as unidades das usinas do conjunto sem campo de conferência nem contagem na auditoria), T160 (a divergência do tipo publicado na qualidade dos dados, como pede o caso de borda da spec), T161 (teste da usina fora da composição) e T162 (desvios a registrar na fase F).
- **T159**: as unidades de `capacidade_membros.csv` conferidas pelo subsistema da linha da usina na composição (o estado não serve: o Conj. Chapadão teve UTE de GO), com `auditoria_capacidade_membros.csv` (linhas da usina, linhas só com o CEG e a mensagem com as usinas da composição e as com unidades) e o aviso no log; teste com uma unidade da térmica do conjunto em outro subsistema.
- **T160**: a frase do tipo publicado divergente saiu da constatação "Composição do conjunto" e entrou na constatação da qualidade dos dados (`frases_tipo_publicado`); testes ajustados.
- **T161**: teste da Coleta com a PCH fictícia fora da composição: código 2, a mensagem com o CEG e o id do conjunto, e nenhum outro conjunto coletado.
- **Efeito nas referências ainda sem commit**: a Bandeirante refeita (`--sem-portal`, mesmos brutos) mudou só a frase do tipo publicado (da seção 4 para a 3) e ganhou o arquivo de auditoria; a referência dela foi removida e registrada de novo, como na T157. A Seriemas 1 não muda o relatório (não tem o tipo publicado: a série de referência é a da usina), mas a Coleta dela é anterior à T159: refazê-la agora traria os 45 valores da geração do conjunto que o ONS republicou em 21/10/2026 e mudaria números aprovados. Fica como registrada; a Coleta refeita dela terá `auditoria_capacidade_membros.csv` a mais até o próximo congelamento.
- Suíte com 816 aprovados; pyflakes sem aviso.

### 22/10/2026 — T127 (portão do fim da fase D)

- Suíte com 816 aprovados; pyflakes sem aviso; `/speckit-converge` feito (Phase 12: T159 a T161 concluídas; T162 para a fase F, com a T153, a T156 e a T158).
- `python -m src comparar --todas --coleta` com cinco referências: os **cinco relatórios idênticos aos aprovados**; bandeirante sem nenhuma diferença; na Coleta, sao_domingos, william_arjona e praia_formosa só com as diferenças de dados publicados pelo ONS depois do congelamento (aceitas pelo usuário até o próximo congelamento); seriemas_1 com as mesmas diferenças de publicação (45 valores da geração do conjunto republicados em 21/10/2026 e o cadastro) e `auditoria_capacidade_membros.csv` só na Coleta refeita (arquivo da T159, posterior ao congelamento dela). Código 6 só por essas diferenças da Coleta.
- **Fase D concluída**; commit pedido ao usuário (código, testes, rascunhos, perfil e referência da Bandeirante, referência da Seriemas 1).

### 22/10/2026 — decisão do usuário sobre a CCEE

- Catálogo de dados abertos da CCEE conferido (metadados, não os arquivos): `geracao_horaria_usina` (geração horária por parcela de usina desde 03/2024, com os componentes do despacho; sem CEG), `parcela_usina_montante_mensal` (por usina e mês desde 2024, **com o CEG**, geração, garantia física, capacidade e MRE), `pch_cgh_gf_definida`, `eolica_gf_definida`, `fotovoltaica_gf_definida` e os CVU (sem CEG). Nenhum conjunto de constrained-off. Ganho maior nas PCH e CGH em conjunto ou Tipo III e nas UFV sem série própria no ONS; menor nas UTE; pouco nas UHE.
- Decisão: a avaliação da CCEE como fonte nova (`/speckit-assess-intake`; pede mudança do princípio IV da constituição) fica **para depois das fases E e F**, com a PCH Bandeirante como piloto e um mês de `geracao_horaria_usina` e de `parcela_usina_montante_mensal` baixado pelo usuário para confirmar a identificação.

### 22/10/2026 — Fase E: cópia de segurança (T128) e rascunhos (T129)

- **T128**: depois do commit da fase D pelo usuário, `python -m src copia-seguranca --motivo antes_fase_E` criou `_backup_2026-10-22_antes_fase_E` (524 arquivos), com o SHA-256 dos cinco `referencia.json` igual ao do projeto. A cópia `_backup_2026-10-20_antes_fase_C` foi apagada: ficam a `antes_fase_D` e a `antes_fase_E`.
- **T129**: a fase E nos rascunhos, a partir dos resultados gravados das pilotos e do catálogo de 22/10/2026:
  - `ajustes-specs/004-analises.md`: FR-062 (`indicadores_carteira`): chaves fixas; indicadores do último ano completo da série (sem ano completo, o ano parcial mais recente, marcado), cada um com valor, nível e unidade e vazio quando não se aplica; origem de cada um na tabela anual do relatório da usina; atendimento ao despacho como razão das horas dentro de 5 MW da programada; contagens de todos os itens de cada lista e das regras avaliadas, vazias quando nenhuma regra foi avaliada com dado da usina (Bandeirante); aplicabilidade por tipo;
  - `ajustes-specs/005-geracao-relatorio.md`: FR-049 (carteira, decisão R21 e contrato): recorte, com e sem resultado, a ordem dos motivos (só agregado primeiro) com a cobertura do catálogo, o conteúdo em sete partes, as duas figuras em seaborn, a planilha, a gravação, o panorama pelo tipo do ONS na carteira por estado e tipo; aplicabilidade por recorte.
- **Achado da preparação**: as etapas gravadas da São Domingos em `data/usinas/` são de 09/10/2026 (Análises no formato 2). Para entrar na carteira com resultado (quickstart 7), as etapas dela precisam ser refeitas antes da T136; a referência aprovada não muda.
- **T130**: rascunhos da fase E aprovados pelo usuário ("aprovado"), com as escolhas apresentadas: indicadores do último ano completo da série; atendimento ao despacho pelas horas a até 5 MW da programada; contagens vazias, e não zero, quando nenhuma regra foi avaliada com dado da usina; fator de capacidade só onde o relatório da usina o calcula; "só agregado no ONS" como primeiro motivo, com a cobertura do catálogo; duas figuras; e as etapas da São Domingos refeitas com `--sem-portal` antes da T136.

### 22 e 23/10/2026 — Fase E: código, testes e validação real (T131 a T136)

- **T133**: `src/analises/carteira.py` (`indicadores_carteira`, FR-062 do rascunho 004), gravado nos dois caminhos de `src/analises/etapa.py` (no da EVT, depois do tipo e da modalidade). O formato dos resultados continua o 3: o campo já existia, vazio.
- **T134**: `src/relatorio/carteira.py` (recorte, perfis pelo CEG, motivos, ordenação, panorama, documento em blocos, Markdown, planilha, gravação em pasta temporária com conferência e troca, sem `.bak`), `src/relatorio/carteira_pdf.py` (A4 retrato, estilos do resumo executivo, tabelas em 8 pt) e `src/relatorio/carteira_figuras.py` (as duas figuras em seaborn; paletas de 4 e de 7 cores da ordem categórica, validadas com o script da skill de visualização: todas as checagens aprovadas, contraste abaixo de 3:1 em algumas cores, compensado pela legenda e pela tabela). `caminhos.ARQUIVOS_CARTEIRA` e `caminhos.pasta_carteira`.
- **T135**: comando `carteira` em `src/__main__.py`, com `--estado`, `--tipo` (só os sete tipos de usina) e `--data-geracao`; sem nenhuma das duas opções, código 2 pelo argparse; códigos 0, 1 e 5 e as mensagens do contrato.
- **T131 e T132**: os testes foram escritos depois do código, na mesma sessão (desvio da ordem das tarefas, a registrar na fase F): `tests/analises/test_carteira.py` (6), `tests/relatorio/test_carteira.py` (13, sobre o catálogo e os resultados fictícios de `tests/fixtures/carteira_ficticia.py`) e dois testes em `tests/integracao/test_usinas_ficticias.py` (o campo nas sete usinas fictícias e a carteira de GO sobre os resultados gravados delas). Os testes acharam a frase "As 1 linhas de conjunto", corrigida.
- **Ajustes vistos no PDF do ensaio**: cabeçalhos quebrados no meio da palavra (tabelas em 8 pt e larguras revistas), figuras largas demais para a página retrato (7,5 polegadas), rótulos de mês sobrepostos no panorama ("out/25", no centro da barra) e o grupo publicado sem valor, que aparecia como zero: no panorama, o mês de uma série sem nenhuma hora com valor sai como "sem valor", e as horas sem valor são listadas por grupo.
- **Suíte**: 837 aprovados (816 + 21); pyflakes sem aviso.
- **T136**:
  - As Análises e o relatório da William Arjona, da Seriemas 1, da Bandeirante e da Praia Formosa refeitos com a data de geração de cada referência, para gravar o campo novo: PDF, Markdown, CSV e figuras iguais byte a byte aos de antes; na planilha, só a data de gravação muda; o `comparar` com cada referência não acha diferença nas saídas do relatório (só os arquivos que existem só na referência: Coleta congelada, perfil e `referencia.json`).
  - São Domingos: `completo --sem-portal --data-geracao "07/10/2026 08:53"` (código 0, 3 min 16 s), como aprovado na T130. **Achado**: os brutos de hoje têm a série até 19/10/2026 (baixada pelas Coletas das outras pilotos), e a referência vai até 28/09/2026. Por isso o relatório em `reports/sao_domingos/` mudou além das republicações do ONS: 49 horas ausentes em vez de 1, disponibilidade média de 87,9 % em vez de 87,8 % e as figuras com outubro. A referência aprovada em `relatorios_referencia/` não mudou. A decisão entre manter o relatório atualizado ou voltar ao estado aprovado (Coleta congelada e etapas 2 a 5) fica com o usuário, na T137.
  - `python -m src carteira --estado MS --data-geracao "22/10/2026 14:00"`: código 0 em 2,9 s; 149 usinas, as quatro pilotos com resultado e 145 sem resultado (46 só agregado no ONS e 99 sem perfil). `python -m src carteira --tipo UTE`: código 0 em 3,1 s; 617 usinas, só a William Arjona com resultado. Nenhum `etapa.json` mudou; a busca de termos de parecer não acha nada nas duas carteiras.
  - Ordenação de MS: São Domingos (4 possíveis problemas e 5 pontos de atenção; 11 de 11 regras avaliadas), William Arjona (2 e 0; 7 de 8), Seriemas 1 (0 e 1; 2 de 4) e Bandeirante no fim, sem regra avaliada. Os 5 itens em três listas da São Domingos são todos os itens dela (a aba CONCLUSAO tem 5, 5, 5 e 4), e não o limite de exibição.
  - Correções nos rascunhos aprovados: o atendimento da William Arjona é 6,25 %, exibido como 6,2 % pelo arredondamento do projeto (o rascunho 004 dizia 6,3 %); e as duas térmicas Tipo III publicadas uma a uma em MS têm zero de 10/2025 a 04/2026 e nenhum valor de 05/2026 a 09/2026 (o rascunho 005 dizia "zero em todos os meses").

### 23/10/2026 — T137 (aprovação) e portão da fase E (T138)

- **T137**: o usuário aprovou a carteira de MS em `reports/carteiras/ms/` ("aprovo a carteira de MS") e decidiu manter o relatório atualizado da São Domingos em `reports/sao_domingos/` ("manter atualizado São Domingos, aprovado tbm"), com a série até 19/10/2026. A referência em `relatorios_referencia/sao_domingos/` continua a de 07/10/2026.
- **Achado sobre o relatório atualizado da São Domingos**: as 48 horas ausentes novas (29 e 30/09/2026) vêm da cópia local do arquivo de 09/2026 da EVT, baixada em 30/09/2026 (publicação do ONS de 30/09 15:05, até 28/09 23h) e nunca atualizada, porque as execuções seguintes da São Domingos foram com `--sem-portal`. A ONS já publica o mês completo (720 horas da usina 153, consulta ao dataset energia-vertida-turbinavel em 23/10/2026). Fechar a lacuna pede a Coleta da São Domingos com o portal; fica com o usuário.

## Phase 13: Convergence

- [X] T163 CRITICAL: Pôr, logo abaixo de cada tabela e de cada figura do relatório de carteira (PDF e Markdown, `src/relatorio/carteira.py`), a legenda com a fonte dos dados ("Fonte dos dados: …", com os conjuntos do ONS, o identificador e a data de obtenção, ou "Calculado neste relatório a partir de: …", com os resultados das Análises de cada usina), como no relatório da usina, per Constitution VII (missing)
- [X] T164 Gravar a aba FONTES da carteira com as colunas da aba FONTES da usina (`aba`, `conjuntos_origem`, `conferencias`, `sem_outra_fonte`, `calculado_no_relatorio`) em `src/relatorio/carteira.py`, per R21 (partial)
- [X] T165 Usar só a TEIFa de dezembro no ano completo, vazia sem dezembro, e a do último mês publicado só no ano parcial, em `src/analises/carteira.py`, per FR-062 do rascunho 004 (partial)
- [X] T166 Levar a largura das figuras da carteira para `src/comum/regras.py`, ao lado de `TAMANHO_FIGURA_PADRONIZADA`, per plan: VII (partial)
- [ ] T167 Registrar na fase F, com T153, T156, T158 e T162, os desvios da fase E: os módulos `carteira_pdf.py` e `carteira_figuras.py`, não nomeados na T134, e os testes T131 e T132 escritos depois do código, per tasks T131, T132 e T134 (unrequested)

### 23/10/2026 — Convergência da fase E (T163 a T166)

- **Portão, primeira rodada** (antes da convergência): `comparar --todas --coleta` com código 6, com exatamente as mesmas diferenças do portão final da fase D (os cinco relatórios iguais; na Coleta, só as republicações do ONS aceitas e o `auditoria_capacidade_membros.csv` da Seriemas 1).
- **`/speckit-converge`** (fase E): 5 achados, na Phase 13 (T163 a T167): T163 CRITICAL (princípio VII: a carteira segue as regras de legenda do relatório da usina, e as tabelas e figuras dela só tinham as fontes no parágrafo das notas), T164 (aba FONTES com as colunas da usina, R21), T165 (TEIFa só de dezembro no ano completo, FR-062), T166 (largura das figuras em `regras.py`) e T167 (desvios da fase E a registrar na fase F).
- **T163**: `origens()` em `src/relatorio/carteira.py` dá a origem de cada tabela, a mesma da aba FONTES; a legenda ("Fonte dos dados: …" ou "Calculado neste relatório a partir de: …") sai logo abaixo de cada tabela e de cada figura, no PDF e no Markdown. Com a publicação da Modalidade das usinas e a data do catálogo; os indicadores remetem à legenda da tabela anual do relatório de cada usina, que tem o identificador e a data de obtenção de cada conjunto.
- **T164**: a aba FONTES com `aba`, `conjuntos_origem`, `conferencias`, `sem_outra_fonte` e `calculado_no_relatorio` (`COLUNAS_FONTES` da usina).
- **T165**: no ano completo, a TEIFa de dezembro, vazia sem dezembro; no ano parcial, a do último mês publicado. Nas pilotos, nada muda (as que têm TEIFa têm dezembro de 2025).
- **T166**: `LARGURA_FIGURA_CARTEIRA` em `src/comum/regras.py`.
- Testes: 3 novos (legendas, FONTES e TEIFa de dezembro); suíte com 840 aprovados; pyflakes sem aviso. A carteira de MS e a `brasil_ute` refeitas com a data de 22/10/2026 14:00: 7 legendas na de MS (5 tabelas e 2 figuras), os `etapa.json` iguais e nenhum termo de parecer.

### 23/10/2026 — T138: portão do fim da fase E

- Suíte com 840 aprovados; pyflakes sem aviso; `/speckit-converge` feita (T163 a T166 resolvidas; T167 fica para a fase F).
- `comparar --todas --coleta` refeito com o código final: código 6, com as mesmas diferenças do portão final da fase D, linha por linha. Os cinco relatórios de referência sem nenhuma diferença; na Coleta, só as republicações do ONS aceitas pelo usuário e o `auditoria_capacidade_membros.csv` da Seriemas 1.
- **Fase E fechada.** Pendências: a Coleta da São Domingos com o portal, para fechar as 48 horas de 29 e 30/09/2026 do relatório atualizado (decisão do usuário); o commit da fase E pelo usuário; depois, a fase F (T139 a T148, com T153, T156, T158, T162 e T167 e a fusão da spec 007).

