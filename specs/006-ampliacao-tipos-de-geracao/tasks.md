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
  - **pasta**: `C:\Users\rlazaro\Desktop\UHE_SAO_DOMINGOS_versao_fiscalizacao\`, fora do projeto, com `src/` e `tests/` do commit aprovado `c82a64e` (sem mudanças pendentes), `usinas/sao_domingos/perfil.toml`, `data/raw/`, `data/usinas/sao_domingos/`, `reports/sao_domingos/`, `README.md`, `requirements.txt` e um `LEIA-ME.txt` com o uso;
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
- [ ] T042 Portão do perfil:
  - suíte;
  - `python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"`;
  - `python -m src comparar --todas --coleta` com código 0.
  - Registrar em `specs/006-ampliacao-tipos-de-geracao/tasks.md`.

### Novo congelamento (item 4)

- [ ] T043 Conferir se o formato da Coleta mudou desde a T026: compare o `versao_formato` do `etapa.json` congelado com o atual.
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

- [ ] T044 [P] [US1] Escrever `tests/coleta/test_catalogo_usinas.py`, com catálogo CKAN e arquivos sintéticos:
  - **tipo pelo prefixo do CEG** (decisão R1): linha sem CEG = `conjunto`; prefixo fora da lista = `outro`; `divergencias` quando o tipo do ONS difere;
  - **cobertura** (decisão R3), no arquivo mais recente de cada conjunto: `proprio`, `conjunto` (inclusive com linhas próprias sem valor), `agregado` e `ausente`;
  - **arquivos e colunas** do data-model, seções 2.1 a 2.6: `usinas.csv`, com "Uma linha por linha do cadastro do ONS" e só unidades ativas, mais `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`;
  - **agregados**: escolhidos pelo estado e pela modalidade, nunca pelo nome ou pelo id (id vazio aceito); Tipo III com `previsao`; duplicatas tratadas e `horas_ausentes`;
  - **códigos de programação**: a regra de ligação com a usina (código igual ao id ONS ou prefixo do conjunto sem `CJU_`);
  - **listagem**: uma coluna por conjunto de série do tipo (`P`, `C`, `A` ou `-`) e o slug do perfil achado pelo CEG;
  - **`--sem-portal`**: sem rede;
  - **códigos**: 0, 1 e 2 (contracts/cli-usinas.md).
- [ ] T045 [P] [US1] Escrever `tests/coleta/test_perfil_rascunho.py` (contracts/cli-perfil.md):
  - **conteúdo do rascunho**:
    - `situacao = "rascunho"`, `pendentes`, comentários com a origem;
    - só as unidades ativas e o comentário de divergência de potência;
    - a `[cobertura]` só com os conjuntos já implementados, e os membros do conjunto;
    - código de programação sem ligação pendente, com a lista do estado;
  - **recusas**: catálogo ausente (5), CEG fora do catálogo (2), Tipo III ou só agregado (2), sem gravar nada;
  - **perfil existente**: nada gravado, com código 0 sem diferença e 6 com diferença;
  - **slug**: derivado do nome; `carteiras` reservado;
  - **leitura**: o comando não lê `data/raw/`.
- [ ] T046 [P] [US1] Escrever `tests/coleta/test_serie_referencia.py`:
  - **escolha da série** (linhas da fase A da decisão R6): EVT nas hidrelétricas com EVT; Geração por usina pelo id ONS com geração própria; Geração por usina pelo id do conjunto em conjunto sem série própria;
  - **varredura**: em todos os arquivos publicados;
  - **período**: da primeira à última hora com valor; com cobertura `["proprio", "conjunto"]`, a união das duas séries;
  - **`trechos.csv`** (data-model 5.2): mudança de modalidade, de composição e de código, com `mostrar` só quando muda o nível ou a composição;
  - **hidrelétrica com EVT**: o caminho de hoje, sem trechos.
- [ ] T047 [P] [US1] Escrever `tests/tratamento/test_base_horaria.py`:
  - `base_horaria.csv` nas usinas sem EVT, com as colunas `din_instante`, `geracao_mw`, `nivel`, `disponibilidade_operacional_mw`, `disponibilidade_sincronizada_mw`, `geracao_programada_mw`, `trecho` e `sinalizacoes`;
  - nível `conjunto` quando a série é do conjunto;
  - ausências listadas;
  - nenhum registro excluído (princípio V).
- [ ] T048 [P] [US1] Escrever `tests/conferencia/test_aplicabilidade.py`:
  - `nao_aplicaveis.csv` com `conferencia` e `motivo`, com todas as conferências do catálogo que não se aplicam, inclusive na UHE;
  - o relatório e a planilha da UHE não o leem (T011).
- [ ] T049 [P] [US1] Escrever `tests/analises/test_comum_tipos.py`, sobre a base horária comum de uma usina sem EVT:
  - indicadores anuais, série temporal, geração mensal e perfil horário;
  - a sazonalidade só com 12 meses distintos; abaixo disso, omitida e listada em `omitidos` com o motivo (decisão R17);
  - `ResultadosAnalise` com `VERSAO_FORMATO` 2, `tipo`, `modalidade`, `niveis`, `trechos`, `comum` e `omitidos`;
  - nas hidrelétricas com EVT, os campos de hoje com os mesmos valores.
- [ ] T050 [P] [US1] Ampliar `tests/relatorio/test_estrutura.py`:
  - **dois caminhos** (decisão R14):
    - a hidrelétrica com EVT tem exatamente as 17 seções de hoje;
    - a usina sem EVT segue a tabela da decisão R14, com numeração contínua e as seções sem base omitidas;
  - **título e capa por caminho** (data-model 6.5);
  - **legendas** com o identificador e, no conjunto e no agregado, o nível escrito (decisão R15);
  - **notas**: com as omissões, os níveis e as conferências não aplicáveis só nas usinas sem EVT.
- [ ] T051 [P] [US1] Ampliar `tests/analises/test_conclusao.py`:
  - **catálogo**: cada regra declara `codigo`, `tipos`, `listas`, `nivel_exigido`, `funcao`, `limiares`, `periodo_minimo_meses` e `secoes` (data-model 6.5);
  - **hidrelétricas com EVT**: C1 a C11 sem mudança, com a ordem por lista e por número;
  - **regra com entrada de nível conjunto**: não é avaliada e vai para `omitidos`;
  - **PCH em conjunto**: sem itens, com a frase que explica a falta de base no nível da usina;
  - **nota da conclusão**: nas usinas sem EVT, gerada do catálogo do tipo; nas hidrelétricas com EVT, o texto de hoje.
- [ ] T052 [P] [US1] Criar as usinas fictícias da decisão R23 em `tests/fixtures/usinas_ficticias/{uhe,pch,cgh,ute,utn,eol,ufv}/perfil.toml`:
  - valores inventados e nenhum valor de usina real;
  - os brutos sintéticos dos conjuntos da fase A em `tests/fixtures/brutos_ficticios.py`: geração da usina e do conjunto, programação, disponibilidade, indicadores, cadastro, composição e capacidade;
  - **a PCH**: composição que muda no período e linhas próprias sem valor;
  - **a UFV**: série curta.
- [ ] T053 [P] [US1] Escrever `tests/integracao/test_usinas_ficticias.py`:
  - cada uma das sete usinas fictícias roda `completo --sem-portal` sem rede, com código 0 e as seções comuns;
  - nenhuma saída tem valor de outra usina.
  - Ampliar `tests/comum/test_literais.py` com os identificadores das pilotos: `MSUTWI`, `MSSRI1`, `CJU_MS4FINO`, `CEUFM`, `MSBDT`, `CJU_MSCAO` e os CEGs da spec.

### Implementation for User Story 1

- [ ] T054 [US1] Acrescentar ao registro e às regras os conjuntos do catálogo e a geração do conjunto:
  - em `src/comum/regras.py`, os pacotes `usina_conjunto` e `capacidade-geracao`, com as pastas `usina_conjunto` e `capacidade_geracao`;
  - em `src/coleta/registro.py`, as entradas `composicao` e `capacidade` e o nível "usina ou conjunto" da `geracao`, com o identificador `id_conjunto` e a conferência pelo estado (decisão R9).
- [ ] T055 [US1] Criar `src/coleta/catalogo_usinas.py` (decisões R1 a R3; contracts/cli-usinas.md):
  - **sincronização** (sem `--sem-portal`), com o catálogo CKAN, o cache e as versões de hoje:
    - Modalidade das usinas, Composição dos conjuntos e Capacidade de geração;
    - o arquivo mais recente de cada conjunto de série já implementado;
    - a geração dos últimos 12 meses completos;
    - os dicionários desses conjuntos;
  - **montagem** de todos os arquivos de `data/catalogo/`, sem `.bak`, numa pasta temporária, com conferência e troca;
  - **listagem** filtrada;
  - **mensagens** obrigatórias do contrato.
- [ ] T056 [US1] Em `src/__main__.py`, o comando `usinas` com as opções do contrato (`--estado`, `--tipo`, `--modalidade`, `--sem-portal`, `--forcar-download`) e os códigos 0, 1 e 2.
- [ ] T057 [US1] Portão do item 5: suíte e `python -m src comparar --todas --coleta` com código 0. Registrar em `specs/006-ampliacao-tipos-de-geracao/tasks.md`.
- [ ] T058 [US1] Criar `src/coleta/perfil_rascunho.py` e o comando `perfil` em `src/__main__.py` (decisão R5; contracts/cli-perfil.md):
  - leitura só de `data/catalogo/`;
  - recusas e diferenças com os códigos 0, 1, 2, 5 e 6;
  - o rascunho no formato de contracts/perfil-multitipo.md;
  - gravação de arquivo novo, conferida no disco, sem nunca sobrescrever.
  - Portão: suíte e `comparar --todas --coleta` com código 0.
- [ ] T059 [US1] Criar `src/coleta/serie_referencia.py`: a escolha da série de referência (linhas da fase A da decisão R6), o período e os trechos (decisão R7), com o resumo do data-model 5.1.
- [ ] T060 [US1] Integrar a série de referência e os arquivos novos em `src/coleta/etapa.py`:
  - **série**: nas usinas sem EVT, o período vem da série de referência; nas hidrelétricas com EVT, o caminho de hoje;
  - **arquivos novos**, só fora da UHE com EVT: `trechos.csv`, `geracao_complemento.parquet` (`cod_modalidadeoperacao` e `nivel` por hora), `composicao_conjunto.csv` e `capacidade_ficha.csv`;
  - **resumo do `etapa.json`**: `tipo`, `modalidade`, `serie_referencia`, `trechos`, `conjuntos_nao_aplicaveis` e `linhas_usina_sem_valor`.
  - Portão do item 7: suíte e `comparar --todas --coleta` com código 0.
- [ ] T061 [US1] Criar `src/tratamento/base_horaria.py` com as colunas da T047 e chamá-lo em `src/tratamento/etapa.py` nas usinas sem EVT.
- [ ] T062 [P] [US1] Criar `src/conferencia/aplicabilidade.py`: a lista das conferências do catálogo com a condição de cada uma; grava `nao_aplicaveis.csv` em `src/conferencia/etapa.py`, para todas as usinas.
- [ ] T063 [US1] Ampliar as Análises:
  - `src/analises/resultados.py`: os campos novos e `VERSAO_FORMATO = 2`;
  - `src/analises/comum_tipos.py`, novo: as seções comuns sobre a base horária comum;
  - `src/analises/etapa.py`: escolhe o caminho pela presença da EVT;
  - `src/analises/constatacoes.py`: "do conjunto <nome>" quando o número é do conjunto.
- [ ] T064 [US1] Ampliar a estrutura do relatório em `src/relatorio/estrutura.py`:
  - `Secao` com `tipos`, título por tipo, `legenda` e `periodo_minimo_meses`;
  - as seções novas da tabela da decisão R14, fora do caminho da EVT;
  - `secoes_presentes` por caminho.
- [ ] T065 [US1] Título, capa, notas e legendas por caminho:
  - em `src/relatorio/conteudo.py`, `src/relatorio/pdf.py`, `src/relatorio/markdown.py` e `src/relatorio/planilha.py`:
    - o título e a capa do data-model 6.5;
    - as notas das usinas sem EVT: omissões, níveis e conferências não aplicáveis;
  - em `src/relatorio/fontes.py`: a legenda com o identificador e o nível (decisão R15).
  - Nas hidrelétricas com EVT, nada muda (T011).
  - Portão do item 8: suíte e `comparar --todas --coleta` com código 0.
- [ ] T066 [US1] Reescrever o catálogo da conclusão em `src/analises/conclusao.py` como lista de `RegraConclusao` (decisão R16), sem mudar C1 a C11:
  - avaliar só com entradas do nível da usina;
  - mandar o que não é avaliado para `omitidos`;
  - gerar a nota da conclusão das usinas sem EVT a partir do catálogo, em `src/relatorio/conteudo.py`, mantendo `nota_conclusao()` como está para as hidrelétricas com EVT.
  - Portão do item 9: suíte e `comparar --todas --coleta` com código 0.
- [ ] T067 [US1] Completar o item 10: rodar `tests/integracao/test_usinas_ficticias.py` com as sete usinas e corrigir o que faltar nos módulos da fase A, sem mudar os testes da T011.

### Validação real da User Story 1

- [ ] T068 [US1] Montar o catálogo com o portal: `python -m src usinas --estado MS`, e de novo com `--sem-portal` (quickstart 3.3).
  - Conferir: 171 usinas em MS (UHE 5, PCH 16, CGH 9, UTE 33, UFV 86 e 22 linhas de conjunto, ou a contagem atual do ONS, explicada); `usinas.csv` com todas as linhas do cadastro; `catalogo.json`.
  - Depois, `comparar --todas --coleta` com código 0, ou as diferenças da Coleta por republicação levadas ao usuário.
  - Registrar.
- [ ] T069 [US1] Gerar o rascunho da William Arjona: `python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona` (quickstart 3.4).
  - Medir o tempo (menos de 1 minuto, SC-003).
  - Conferir o conteúdo e rodar de novo: código 0 ou 6, com o arquivo igual byte a byte.
  - Registrar.
- [ ] T070 [US1] Conferir as recusas (quickstart 3.5):
  - `python -m src coleta --usina william_arjona` com o perfil em rascunho dá código 4, com a lista dos pendentes;
  - `perfil` de uma CGH Tipo III de MS dá código 2, sem criar pasta.
  - Registrar.
- [ ] T071 [US1] Levar ao usuário o catálogo de MS (`data/catalogo/usinas.csv`, filtrado por MS) e o rascunho `usinas/william_arjona/perfil.toml`.
  - O usuário confere e completa o perfil, com `situacao = "conferido"`.
  - Registrar a aprovação.
- [ ] T072 [US1] Rodar `python -m src completo --usina william_arjona` (quickstart 3.6) e conferir:
  - série de referência "geracao" desde 10/07/2021;
  - só as seções comuns, sem EVT nem hidrologia;
  - legendas com o identificador;
  - notas com o que não se aplica.
  - Registrar o tempo do `etapa.json`.
- [ ] T073 [US1] Conferir o código da fase A contra os rascunhos aprovados em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/`. Uma divergência necessária vira ajuste do rascunho, com aprovação do usuário.
- [ ] T074 [US1] Portão do fim da fase A: suíte sem rede; `pyflakes` de fora do `venv`; `/speckit-converge`; `python -m src comparar --todas --coleta` com código 0. Registrar.

**Checkpoint**: qualquer usina com dado próprio ou de conjunto tem catálogo, rascunho do perfil e relatório com as seções comuns; a São Domingos não mudou.

---

## Phase 4: User Story 2 - Relatório completo de térmica e nuclear (Priority: P2)

**Goal**: despacho por motivo, inflexibilidade, atendimento ao despacho, disponível sem despacho, CVU × CMO e as regras de térmica (fase B; decisões R9, R11, R13, R16 e R18).

**Independent Test** (quickstart 4): relatório da William Arjona com as seções e as regras de térmica, e as conferências G3, G4 e DISPF.

### Preparação da fase B

- [ ] T075 [US2] Criar a cópia de segurança `python -m src copia-seguranca --motivo antes_fase_B` e conferir `relatorios_referencia/` na cópia nova. Registrar.
- [ ] T076 [P] [US2] Acrescentar a fase B aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md`: despacho, CVU e CMO no registro, com a identificação da decisão R9; `planejamento.csv` no catálogo; `subsistema` e `[[identificacao.planejamento]]` no perfil;
  - `002-tratamento-dados.md`: despacho por hora e por unidade, CVU pela revisão mais recente, CMO sem duplicatas, semanais em hora e o sinal do CVU (decisão R11);
  - `003-conferencia.md`: G3, G4 e DISPF, TEIFa e TEIP das térmicas (decisão R13);
  - `004-analises.md`: decisão R18; C12 a C15; C2, C5, C8 e C10 sobre a base horária comum;
  - `005-geracao-relatorio.md`: seções, figuras e indicadores da capa de térmica.
- [ ] T077 [US2] Levar ao usuário os rascunhos da fase B em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase B antes disso.

### Tests for User Story 2

- [ ] T078 [P] [US2] Escrever `tests/coleta/test_conjuntos_termicos.py`, com brutos sintéticos:
  - **despacho**: pelo CEG, com o código de planejamento conferido como número e só no período de cada código; linha com código fora da lista conta como "só identificador";
  - **CVU**: pelos códigos do perfil e conferido pelo subsistema;
  - **CMO**: pelo subsistema, como agregado;
  - **catálogo**: `planejamento.csv`, com o primeiro e o último mês de cada código.
- [ ] T079 [P] [US2] Escrever `tests/tratamento/test_termica.py`:
  - `despacho_horario.csv`: a soma das unidades por hora, por motivo, programado e verificado;
  - `despacho_unidades_horario.csv`: o mesmo, por unidade;
  - `cvu_semanal.csv`: só a revisão mais recente, com `sinal_cvu` em CVU ausente ou negativo;
  - `cmo_semanal.csv`: sem duplicatas, contadas;
  - semanais levadas à hora pelo intervalo da semana operativa.
- [ ] T080 [P] [US2] Escrever `tests/conferencia/test_fontes_termica.py`:
  - G3 (programação diária × programado do despacho) e G4 (verificado do despacho × Geração por usina), com a tolerância de 0,01 MW;
  - DISPF × horas pelo CEG numa térmica;
  - TEIFa e TEIP como não aplicáveis, com o motivo, quando a usina falta nas taxas.
- [ ] T081 [P] [US2] Escrever `tests/analises/test_termica.py`:
  - geração por motivo, com as parcelas, e a inflexibilidade programada e verificada;
  - atendimento: horas e energia abaixo e acima, e os maiores desvios;
  - horas disponíveis sem despacho;
  - CVU × CMO por semana e por unidade, sem julgamento;
  - térmica sem geração no período: nenhuma divisão por zero, e a constatação de usina disponível e não despachada (US2-5).
- [ ] T082 [P] [US2] Ampliar `tests/analises/test_conclusao.py` com C12 a C15 e com C2, C5, C8 e C10 numa térmica:
  - cada regra dispara e não dispara;
  - sem IP e TEIF de referência, as partes de C2 e C5 que dependem deles vão para `omitidos`;
  - nenhum termo de parecer nos textos.
- [ ] T083 [P] [US2] Ampliar `tests/fixtures/brutos_ficticios.py` e as usinas fictícias `ute` e `utn` com despacho, CVU (com revisões), CMO e DISPF:
  - na `ute`, duas unidades de planejamento, com troca de código, e um ano sem geração;
  - em `tests/integracao/test_usinas_ficticias.py`, as seções de térmica nas duas.

### Implementation for User Story 2

- [ ] T084 [US2] Acrescentar os conjuntos de térmica:
  - em `src/comum/regras.py`, os pacotes `geracao-termica-despacho-2`, `cvu-usitermica` e `cmo-semanal` e as pastas `geracao_termica_despacho_2`, `cvu_usitermica` e `cmo_semanal`;
  - em `src/coleta/registro.py`, as entradas `despacho`, `cvu` e `cmo` (data-model 4), com as colunas de valor do data-model 6.1.
- [ ] T085 [US2] Na Coleta:
  - em `src/coleta/conjuntos.py`, a extração semanal (CVU e CMO) e a identificação por lista de códigos com período;
  - em `src/coleta/catalogo_usinas.py`, `planejamento.csv`, com todos os arquivos do despacho;
  - em `src/comum/perfil_campos.py`, `subsistema` e `planejamento` exigidos com `cvu` na cobertura.
- [ ] T086 [US2] Criar `src/tratamento/termica.py`, com os arquivos da T079, e chamá-lo em `src/tratamento/etapa.py`.
- [ ] T087 [P] [US2] Criar `src/conferencia/fontes.py` com G3 e G4, chamados em `src/conferencia/etapa.py`, e estender a DISPF × horas e as taxas refeitas às térmicas em `src/conferencia/indicadores.py`.
- [ ] T088 [US2] Criar `src/analises/termica.py` (decisão R18), integrado em `src/analises/etapa.py` e em `ResultadosAnalise.termica`.
- [ ] T089 [US2] Em `src/analises/conclusao.py`, C12 a C15 e a extensão de C2, C5, C8 e C10 às térmicas sobre a base horária comum:
  - a regra R7 e os eventos de indisponibilidade total calculados na base horária comum (decisão R30);
  - os limiares iniciais em constantes nomeadas em `src/comum/regras.py`, citados nas notas.
- [ ] T090 [US2] Criar `src/relatorio/secoes_termica.py` e as figuras de térmica em `src/relatorio/figuras.py`, em seaborn com a paleta central:
  - geração por motivo empilhada (atenção à ordem de empilhamento);
  - inflexibilidade;
  - desvios do despacho;
  - CVU × CMO.
  - Também os indicadores da capa de térmica (data-model 6.5) em `src/relatorio/conteudo.py`.

### Validação real da User Story 2

- [ ] T091 [US2] Rodar `python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona`:
  - código 6, com as chaves `despacho` e `cvu`, os códigos 34, 334 e 434 e o subsistema;
  - o usuário completa e confere o perfil.
  - Registrar.
- [ ] T092 [US2] Rodar `python -m src completo --usina william_arjona --data-geracao "<data>"` e conferir os itens do quickstart 4:
  - seções de térmica;
  - CVU por unidade de gás e de óleo;
  - G3, G4 e DISPF;
  - tempo de até 15 minutos pelo `etapa.json`.
  - Registrar.
- [ ] T093 [US2] Conferir o relatório piloto pelo quickstart 8: nenhum termo de parecer e nenhum identificador das outras pilotos em `reports/william_arjona/relatorio_analise_estatistica.md` (SC-004, SC-007). Registrar.
- [ ] T094 [US2] Calibrar com a piloto os limiares de C12 a C15 e levar ao usuário o relatório da William Arjona e os limiares.
  - Depois da aprovação: `python -m src referencia --usina william_arjona --data-geracao "<data>" --aprovado-em "<data>"`.
  - Pedir o commit ao usuário. Registrar.
- [ ] T095 [US2] Portão do fim da fase B: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0, com duas referências. Registrar.

**Checkpoint**: térmicas e nucleares com relatório completo; duas referências protegidas.

---

## Phase 5: User Story 3 - Relatório completo de eólica e solar (Priority: P3)

**Goal**: fator de capacidade, energia cortada por razão, recurso × geração e aderência, com o nível de cada número (fase C; decisões R12, R13, R17 e R19).

**Independent Test** (quickstart 5): relatórios da Seriemas 1 e da Praia Formosa com as seções e as regras de renováveis.

### Preparação da fase C

- [ ] T096 [US3] Criar a cópia `python -m src copia-seguranca --motivo antes_fase_C` e conferir as referências na cópia nova. Registrar.
- [ ] T097 [P] [US3] Acrescentar a fase C aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md`: fator de capacidade, restrição com detalhe e com razão (variantes eólica e fotovoltaica); o motor semi-horário; a linha da fase C da decisão R6; `[[identificacao.membros]]`;
  - `002-tratamento-dados.md`: semi-horárias e hora cheia, energia cortada e sinalizações (decisões R11, R12);
  - `003-conferencia.md`: G1, G2 e G5;
  - `004-analises.md`: decisão R19; C16 a C19; período mínimo;
  - `005-geracao-relatorio.md`: seções, figuras e indicadores da capa de renováveis.
- [ ] T098 [US3] Levar ao usuário os rascunhos da fase C em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase C antes disso.

### Tests for User Story 3

- [ ] T099 [P] [US3] Escrever `tests/coleta/test_conjuntos_renovaveis.py`:
  - **fator de capacidade**: pela usina (CEG) ou pelo conjunto (estado, CEG "-");
  - **restrição com detalhe**: semi-horária, pelo id ONS e pelo CEG; colunas ausentes de 05 a 12/2024 aceitas, sem servir de conferência;
  - **restrição com razão**: pela usina ou pelo conjunto;
  - **variantes**: a eólica e a fotovoltaica escolhidas pelo tipo;
  - **série de referência**: a restrição com detalhe (EOL e UFV em conjunto com série própria).
- [ ] T100 [P] [US3] Escrever `tests/tratamento/test_renovavel.py`:
  - **energia cortada** = máx(estimada − verificada, 0) × 0,5 h, só nas semi-horas com `flg_geracaorestrita = 1`;
  - **semi-horas sem a coluna da marca**: contadas e fora do total;
  - **diferença fora das semi-horas restritas**: não entra;
  - **hora cheia**: média das duas meias-horas, e a hora incompleta fica ausente e contada;
  - **sinalizações**: recurso inválido, fator de capacidade fora de 0 a 1 e geração acima da capacidade;
  - **razão** por semi-hora, com o nível.
- [ ] T101 [P] [US3] Escrever `tests/conferencia/test_fontes_renovaveis.py`:
  - G1 só com pares do mesmo nível;
  - G2 só com `[[identificacao.membros]]` e nos trechos com todas as usinas; sem os membros, não aplicável;
  - G5 (Programação diária × programada do fator de capacidade).
- [ ] T102 [P] [US3] Escrever `tests/analises/test_renovavel.py`:
  - fator de capacidade publicado (com o nível) e calculado ("calculado neste relatório");
  - energia cortada por razão, com a razão do conjunto e a energia da usina;
  - recurso × geração por faixa, sem as semi-horas inválidas e com a contagem delas;
  - aderência à programação: desvio médio e maiores desvios;
  - série curta: sazonalidade omitida com o motivo.
- [ ] T103 [P] [US3] Ampliar `tests/analises/test_conclusao.py` com C16 a C19:
  - C18 só com fator de capacidade próprio e garantia física no perfil;
  - C19 só com programação no nível da usina;
  - regras com período mínimo não avaliadas na série curta.
- [ ] T104 [P] [US3] Ampliar `tests/fixtures/brutos_ficticios.py` e as usinas fictícias:
  - **`eol`**: Tipo I, com vento inválido, razão da restrição e série desde 10/2021;
  - **`ufv`**: em conjunto, com membros, série curta e o esquema antigo sem as cinco colunas.
  - Em `tests/integracao/test_usinas_ficticias.py`, as seções de renováveis nas duas.

### Implementation for User Story 3

- [ ] T105 [US3] Acrescentar os conjuntos de renováveis:
  - em `src/comum/regras.py`, os pacotes `fator-capacidade-2`, `restricao_coff_eolica_detail`, `restricao_coff_fotovoltaica_detail`, `restricao_coff_eolica_usi` e `restricao_coff_fotovoltaica`, com as pastas;
  - em `src/coleta/registro.py`, as entradas `fator_capacidade`, `restricao_detalhe` e `restricao_razao`, com as variantes, e a linha da fase C da decisão R6 em `src/coleta/serie_referencia.py`.
- [ ] T106 [US3] Ampliar o motor de `src/coleta/conjuntos.py` para as séries semi-horárias e as colunas que faltam em parte dos arquivos, sem mudar a extração dos conjuntos horários de hoje. Portão: `comparar --todas --coleta` com código 0.
- [ ] T107 [US3] Criar `src/tratamento/renovavel.py`, com os arquivos do data-model 6.2, e chamá-lo em `src/tratamento/etapa.py`.
- [ ] T108 [P] [US3] Acrescentar G1, G2 e G5 a `src/conferencia/fontes.py`, com a aplicabilidade em `src/conferencia/aplicabilidade.py`.
- [ ] T109 [US3] Criar `src/analises/renovavel.py` (decisão R19), integrado em `src/analises/etapa.py` e em `ResultadosAnalise.renovavel`.
- [ ] T110 [US3] Acrescentar C16 a C19 a `src/analises/conclusao.py`, com os limiares iniciais em constantes nomeadas em `src/comum/regras.py`, citados nas notas.
- [ ] T111 [US3] Criar `src/relatorio/secoes_renovavel.py` e as figuras em `src/relatorio/figuras.py`, em seaborn:
  - fator de capacidade mensal;
  - energia cortada por razão;
  - recurso × geração por faixa;
  - desvio da programação.
  - Também os indicadores da capa de renováveis em `src/relatorio/conteudo.py`.

### Validação real da User Story 3

- [ ] T112 [US3] Gerar e conferir os perfis com `python -m src perfil`:
  - UFV Seriemas 1: `--ceg UFV.RS.MS.052257-0.01 --slug seriemas_1`, com os membros de `CJU_MS4FINO`;
  - EOL Praia Formosa: `--ceg EOL.CV.CE.028631-1.01 --slug praia_formosa`.
  - O usuário completa e confere os dois. Registrar.
- [ ] T113 [US3] Rodar `python -m src completo` das duas usinas com `--data-geracao "<data>"` e conferir os itens do quickstart 5:
  - na Seriemas 1: série desde 22/08/2026, sazonalidade omitida, números do conjunto identificados e energia cortada por razão do conjunto;
  - na Praia Formosa: energia cortada da ordem de 181 GWh contra cerca de 350 GWh de diferença bruta, vento inválido contado, G1 e G5.
  - Tempo de até 15 minutos cada. Registrar.
- [ ] T114 [US3] Conferir os dois relatórios piloto pelo quickstart 8 (SC-004, SC-007): `reports/seriemas_1/relatorio_analise_estatistica.md` e `reports/praia_formosa/relatorio_analise_estatistica.md`. Registrar.
- [ ] T115 [US3] Calibrar com as pilotos os limiares de C16 a C19 e levar ao usuário os dois relatórios e os limiares.
  - Depois da aprovação, `python -m src referencia` de cada uma; pedir o commit ao usuário.
  - Registrar.
- [ ] T116 [US3] Portão do fim da fase C: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0, com quatro referências. Registrar.

**Checkpoint**: eólicas e solares com relatório completo e granularidade declarada; quatro referências protegidas.

---

## Phase 6: User Story 4 - PCH e CGH com a granularidade que os dados permitem (Priority: P4)

**Goal**: relatório de PCH e CGH no nível do conjunto, por trecho de composição, com o aviso do que o ONS não publica (fase D; decisões R7 e R20).

**Independent Test** (quickstart 6): relatório da PCH Bandeirante com a geração do conjunto por trecho, as omissões nas notas e a conclusão sem itens.

### Preparação da fase D

- [ ] T117 [US4] Criar a cópia `python -m src copia-seguranca --motivo antes_fase_D` e conferir as referências na cópia nova. Registrar.
- [ ] T118 [P] [US4] Acrescentar a fase D aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/001-coleta-dados.md`: composição por trecho e linhas próprias sem valor;
  - `004-analises.md`: decisão R20;
  - `005-geracao-relatorio.md`: seções de conjunto e notas do nível de conjunto.
- [ ] T119 [US4] Levar ao usuário os rascunhos da fase D em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase D antes disso.

### Tests for User Story 4

- [ ] T120 [P] [US4] Escrever `tests/analises/test_conjunto.py`, com a PCH fictícia (térmicas saem do conjunto no meio do período):
  - geração do conjunto por trecho de composição, com os tipos de cada trecho;
  - nenhum número dividido entre as usinas;
  - linhas próprias sem valor contadas na qualidade dos dados;
  - disponibilidade e indicadores oficiais omitidos, com o motivo;
  - conclusão sem itens e com a frase.
- [ ] T121 [P] [US4] Ampliar `tests/integracao/test_usinas_ficticias.py` com as seções de conjunto na `pch` e na `cgh` fictícias e a nota de que o ONS não publica a geração da usina isolada.

### Implementation for User Story 4

- [ ] T122 [US4] Criar `src/analises/conjunto.py` (decisão R20), integrado em `src/analises/etapa.py` e em `ResultadosAnalise.conjunto`, usando `trechos.csv` e `composicao_conjunto.csv`.
- [ ] T123 [US4] Criar `src/relatorio/secoes_conjunto.py` e a figura da geração do conjunto por trecho em `src/relatorio/figuras.py`, em seaborn.
  - Também as notas do nível de conjunto em `src/relatorio/conteudo.py`.

### Validação real da User Story 4

- [ ] T124 [US4] Gerar o perfil da PCH Bandeirante com `python -m src perfil --ceg PCH.PH.MS.032163-0.01 --slug bandeirante`.
  - Conferir os quatro códigos de programação `MSCAO-*`.
  - O usuário completa e confere o perfil. Registrar.
- [ ] T125 [US4] Rodar `python -m src completo --usina bandeirante --data-geracao "<data>"` e conferir os itens do quickstart 6. Conferir o relatório pelo quickstart 8. Registrar.
- [ ] T126 [US4] Levar o relatório ao usuário. Depois da aprovação, `python -m src referencia --usina bandeirante`, com as datas, e o pedido de commit. Registrar.
- [ ] T127 [US4] Portão do fim da fase D: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0, com cinco referências. Registrar.

**Checkpoint**: PCH e CGH em conjunto com relatório honesto sobre o nível dos dados; cinco referências protegidas.

---

## Phase 7: User Story 5 - Relatório de carteira do estado (Priority: P5)

**Goal**: carteira por estado, por tipo ou pelos dois, a partir dos resultados gravados, sem nota nem parecer (fase E; decisão R21; contracts/cli-carteira.md).

**Independent Test** (quickstart 7): carteira de MS com as quatro pilotos com resultado, as demais com o motivo, a ordenação e o panorama.

### Preparação da fase E

- [ ] T128 [US5] Criar a cópia `python -m src copia-seguranca --motivo antes_fase_E` e conferir as referências na cópia nova. Registrar.
- [ ] T129 [P] [US5] Acrescentar a fase E aos rascunhos:
  - `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/004-analises.md`: `indicadores_carteira`;
  - `005-geracao-relatorio.md`: a carteira (decisão R21; contracts/cli-carteira.md).
- [ ] T130 [US5] Levar ao usuário os rascunhos da fase E em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/` e registrar a aprovação. Nenhum código da fase E antes disso.

### Tests for User Story 5

- [ ] T131 [P] [US5] Escrever `tests/analises/test_carteira.py`:
  - `indicadores_carteira` com as chaves fixas da decisão R21, cada indicador com valor, nível e unidade;
  - vazio, e não zero, quando não se aplica;
  - contagem de todos os itens de cada lista da conclusão.
- [ ] T132 [P] [US5] Escrever `tests/relatorio/test_carteira.py`, com resultados gravados de usinas fictícias:
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

- [ ] T133 [US5] Criar `src/analises/carteira.py` (`indicadores_carteira`) e gravá-lo em `src/analises/etapa.py`. Nas hidrelétricas com EVT, só o campo novo muda; o relatório não (T011).
- [ ] T134 [US5] Criar `src/relatorio/carteira.py`:
  - recorte, leitura dos perfis pelo CEG e dos resultados;
  - PDF, Markdown e planilha com os construtores de hoje;
  - figuras em seaborn, com atenção à ordem de empilhamento do panorama;
  - gravação em pasta temporária com conferência e troca;
  - `--data-geracao`.
- [ ] T135 [US5] Em `src/__main__.py`, o comando `carteira` com as opções e os códigos do contrato.

### Validação real da User Story 5

- [ ] T136 [US5] Rodar `python -m src carteira --estado MS --data-geracao "<data>"` e `python -m src carteira --tipo UTE` e conferir os itens do quickstart 7:
  - tempo de até 5 minutos;
  - as quatro pilotos com resultado;
  - motivos, ordenação, panorama e a busca de termos de parecer;
  - os `etapa.json` iguais.
  - Registrar.
- [ ] T137 [US5] Levar ao usuário a carteira de MS em `reports/carteiras/ms/` e registrar a aprovação.
- [ ] T138 [US5] Portão do fim da fase E: suíte; `pyflakes`; `/speckit-converge`; `comparar --todas --coleta` com código 0. Registrar.

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
- **Pasta**: `C:\Users\rlazaro\Desktop\UHE_SAO_DOMINGOS_versao_fiscalizacao\` (4,1 GB), com:
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
