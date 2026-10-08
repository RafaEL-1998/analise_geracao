# Research: Reorganização do Projeto num Fluxo de Cinco Etapas

**Feature**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Date**: 2026-10-07

Levantamento feito no código e nos documentos em 07/10/2026; os números (linhas, tamanhos, quantidades) são dessa data.

---

## R1. Ordem da reorganização e redes de segurança

- **Decision**: oito fases, numeradas de 0 a 7, nesta ordem. Cada fase termina com a suíte de testes sem rede. A partir da fase 4, termina também com a comparação do relatório com a linha de base (R2).
  - **Fase 0, preparação**:
     - cópia `_backup_2026-10-07_antes_conclusao/`;
     - exclusão das cópias de 06/10 ou antes (FR-028) e poda para duas (FR-027);
     - inventário de limpeza (R15), aprovado e aplicado.
  - **Fase 1, conclusão** (R17): implementada no código atual e aprovada pelo usuário. Em seguida, cópia `_backup_2026-10-07_antes_reorganizacao/`, com a linha de base do relatório já com a conclusão.
  - **Fase 2, constituição 2.0.0** (R13), aprovada pelo usuário antes de qualquer mudança de organização do código.
  - **Fase 3, specs das cinco etapas e mapeamento** (R12), aprovados, ainda na área de preparação da 009.
  - **Fase 4, perfil da usina** (R5 e R6): o código passa a ler os valores da usina do perfil; nada muda no resultado.
  - **Fase 5, código por etapa** (R3, R4, R8, R9 e R10): pacotes, linha de comando, artefatos entre etapas e conferência como etapa. A migração é feita um conjunto por vez.
  - **Fase 6, generalização** (R11): faixas e textos derivados do perfil e usina fictícia nos testes.
  - **Fase 7, fechamento**:
     - planos de desenho das cinco specs conforme o código final;
     - README;
     - aprovação e remoção das specs antigas e da 009;
     - inventário final (pastas do layout antigo) e validação final.
- **Rationale**:
  - A conclusão vem primeiro porque precisa estar no relatório da fiscalização (14 a 16/10/2026), e a reorganização é longa. Com a conclusão aprovada antes da linha de base, a reorganização prova que reproduz o relatório final, já com ela.
  - A constituição atual restringe o projeto à São Domingos (princípio VI) e manda preservar toda versão anterior de arquivo bruto (princípio V). Os dois conflitam com a US3 e a FR-030, então a constituição muda antes do código.
  - As specs vêm antes do código (SDD).
  - O perfil vem antes da separação em etapas, para que cada módulo movido já leia o perfil e não seja mexido duas vezes.
  - A linha de base garante que o relatório aprovado continua reproduzível em todo ponto de parada.
- **Alternatives considered**:
  - Refatoração de uma vez só: rejeitada, porque não dá para saber qual mudança alterou o resultado.
  - Código antes e documentos depois: rejeitada, porque contraria o SDD e o princípio VI vigente.

## R2. Linha de base reproduzível e comparação byte a byte

- **Decision**: ao fim da fase 1, com a conclusão aprovada e antes de qualquer mudança de organização do código, gerar uma linha de base do relatório e guardá-la na cópia `antes_reorganizacao`:
  - a data de geração é fixada;
  - o gerador de PDF roda no modo invariante (`reportlab.rl_config.invariant`), que omite data de criação e identificador aleatório.

  A etapa de relatório ganha a opção `--data-geracao`, que fixa a data e liga o modo invariante. Com a mesma data, o fluxo novo deve reproduzir a linha de base assim:
  - PDF, Markdown, CSV e figuras idênticos byte a byte;
  - planilha idêntica célula a célula (o arquivo guarda a hora em que foi gravado).

  Os dados tratados regenerados são comparados com os de `data/processed/` atuais, conteúdo a conteúdo (FR-011).
- **Rationale**:
  - Prova o SC-001 sem uma biblioteca de leitura de PDF no projeto.
  - A opção é útil depois: regenerar o mesmo documento e conferir que uma mudança de código não alterou o relatório.
- **Alternatives considered**:
  - Comparar só o número de páginas e o Markdown: fraco, porque o PDF tem conteúdo próprio (capa em cartões, legendas).
  - Instalar um leitor de PDF no projeto: dependência nova só para teste.

## R3. Fronteiras das etapas

- **Decision**: cada etapa lê só os resultados das anteriores e grava os seus.

| Etapa | Lê | Grava |
|---|---|---|
| Coleta | portal do ONS (ou só os arquivos locais, com `--sem-portal`) e perfil | brutos compartilhados em `data/raw/` (como hoje: arquivos, manifestos, dicionários, versões anteriores); por usina, linhas extraídas de cada conjunto, auditorias de extração e registro dos dicionários |
| Tratamento | extraídos da usina | séries tratadas (mesmos arquivos e formatos de hoje), validação física (R1 a R9), ausências e sinalizações de qualidade |
| Conferência | tratados e perfil | resultado das seis conferências |
| Análises | tratados e conferências | resultados das análises, inclusive os dados de cada figura e as constatações |
| Relatório | análises, conferências e datas de obtenção registradas pela coleta | figuras, PDF, Markdown, planilha e CSV |

- **Divisão da extração dos conjuntos complementares**: hoje `conjuntos_ons.ler_arquivo` identifica a usina, converte números, aplica a convenção de hora e audita, tudo junto, e `montar_serie` trata duplicatas, período e ausências. A divisão fica assim:
  - **Coleta**: identificação (identificador e conferência), leitura numérica sem arredondamento e auditoria por arquivo (linhas lidas, irregulares, da usina, só identificador, só conferência, valores inválidos).
  - **Tratamento**: convenção de hora (hora de fim para hora de início), duplicatas entre arquivos, recorte do período, ausências, sinalizações de qualidade e os campos finais da auditoria (horas da usina, duplicatas conflitantes).
  - **EVT**: a base consolidada de hoje já é o "extraído". A leitura e a consolidação de `filter` e `consolidator` ficam na coleta, e o `processor` fica no tratamento.
- **Rationale**: FR-002 a FR-008; a convenção de hora é "alinhar os horários entre as bases" (FR-005).
- **Alternatives considered**: manter extração e tratamento juntos nos complementares. Rejeitada: a spec da coleta passaria a descrever tratamento, e a da etapa de tratamento ficaria incompleta.

## R4. Persistência entre etapas

- **Decision**:
  - **Tratamento**: grava nos formatos de hoje (CSV com `;`; Parquet, XLSX e CSV da EVT), lidos do mesmo jeito que hoje. Assim os valores que chegam às análises não mudam.
  - **Extraídos dos conjuntos complementares**: Parquet, que preserva tipos e é rápido; a base de disponibilidade bruta tem 1,3 GB para todas as usinas.
  - **Conferências e análises**: um arquivo serializado do Python (pickle) por etapa, com versão de formato verificada na leitura e lido só pela etapa seguinte. As tabelas das conferências também são gravadas em CSV, para consulta.
  - **Manifesto da etapa** (`etapa.json`) em cada pasta, com data, arquivos, SHA-256 e resumo (data-model, seção 3).
- **Rationale**: o objeto gravado é o mesmo que hoje passa de uma função para outra na memória, o que garante o SC-001. A planilha continua sendo a versão legível e completa dos resultados.
- **Alternatives considered**:
  - JSON e Parquet campo a campo: muito código e risco de mudar tipos (datas, inteiros com ausentes).
  - Recalcular as análises na etapa de relatório: viola a FR-002.

## R5. Perfil da usina: formato e validação

- **Decision**: um arquivo TOML por usina, em `usinas/<slug>/perfil.toml`, lido pela biblioteca padrão (`tomllib`, Python ≥ 3.11). Ele tem as seções:
  - `usina`: nome exibido, estado e início da operação comercial;
  - `identificacao`: os valores dos identificadores; a regra de qual coluna de cada conjunto usa cada valor é geral e fica no código;
  - `parametros`: cada valor com a fonte;
  - `analises`: limiares próprios da usina.

  A validação na leitura confere:
  - campos obrigatórios e tipos;
  - faixas: unidades ≥ 1; potências e vazões > 0; IP e TEIF entre 0 e 1; estado com 2 letras; formato do CEG;
  - coerência: potência unitária × unidades = potência instalada (tolerância de 0,1 MW); slug igual ao nome da pasta.

  Um perfil inválido para o fluxo antes da coleta, com código 4 e a lista dos campos (FR-022).
- **Rationale**: o fiscal lê e preenche, com comentários para a fonte de cada valor. Não há dependência nova e o arquivo fica no controle de versões.
- **Alternatives considered**:
  - YAML: dependência nova.
  - JSON: sem comentários.
  - Módulo Python: mistura dado com código.
  - Planilha: difícil de versionar e de validar.

## R6. Regras gerais × valores da usina

- **Decision**: a classificação das constantes de `src/config.py` está no data-model (seção 1). Em resumo:
  - **Vão para o perfil**: identificadores (`cod_usina`, nome do reservatório, CEG, id ONS, código de programação, código do reservatório, estado), parâmetros técnicos com as fontes (`FONTE_PARAMETROS_USINA`, `FONTE_GARANTIA_FISICA`), início da operação comercial, vertimento mínimo (patamar contínuo da série) e faixas de geração da análise de EVT por nível (`FAIXAS_GERACAO_INTERMEDIARIAS_MW` = 10, 20, 30 e 40 MW, próprias de uma usina de 48 MW).
  - **Ficam como regras gerais**: tolerâncias, limiares de classificação iguais para qualquer usina (parada ≤ 1 MW, sincronizada ≥ 1 MW, desvio de programação > 5 MW, plena carga ≥ 90 % da potência), duração mínima de evento, horas diurnas e noturnas, meta de alinhamento de 99 %, desvio máximo de nível de 10 m, faixa de produtividade de 70 a 130 %, janela TEIFa/TEIP de 60 meses, conjuntos e endereços do ONS, resolução das figuras.
  - **Saem dos valores do perfil, por cálculo**: engolimento máximo, potência autorizada esperada, disponibilidade de referência, produtividade nominal e limites físicos.
  - O perfil **não** sobrepõe limiares gerais, para que os relatórios de usinas diferentes sejam comparáveis. As exceções são o vertimento mínimo e as faixas de geração, que descrevem a própria usina.
- **Rationale**: o que é critério do projeto fica na constituição e nas specs; o que descreve a usina fica no perfil.
- **Alternatives considered**: tudo no perfil. Rejeitada: perfis longos e critérios diferentes entre usinas.

## R7. Pastas por usina

- **Decision**:

```text
data/raw/                       # compartilhado por todas as usinas (inalterado, ~4,1 GB)
data/usinas/<slug>/coleta/      # extraídos, auditorias de extração, registro dos dicionários, etapa.json
data/usinas/<slug>/tratamento/  # séries tratadas (+ .bak), validação física, etapa.json
data/usinas/<slug>/conferencia/ # conferencias.pkl, CSV das conferências, etapa.json
data/usinas/<slug>/analises/    # resultados.pkl, etapa.json
reports/<slug>/                 # relatorio_analise_estatistica.pdf/.md, perfil_estatistico_anual.xlsx/.csv, figures/
usinas/<slug>/perfil.toml       # perfil (no git)
usinas/<slug>/documentos/       # documentos de referência da usina (fora do git)
referencias/                    # documentos gerais (resoluções da ANEEL, RFs de monitoramento), fora do git
```

  `data/processed/` e os arquivos soltos de `reports/` ficam até a comparação final (R2) e saem pelo inventário final, com aprovação.
- **Rationale**:
  - FR-025: o bruto é compartilhado e o resto fica separado por usina.
  - As pastas com o nome das etapas tornam o fluxo visível nos dados.
  - Perfil e documentos da usina ficam juntos.
- **Alternatives considered**:
  - Tudo da usina numa pasta só, com dados e relatório: mistura arquivos grandes, fora do git, com o perfil, que fica no git.
  - Prefixo da usina no nome dos arquivos, numa pasta comum: é o que já existe e não escala.

## R8. Conferência como etapa

- **Decision**: um módulo por conferência, cada um com uma função que recebe os dados tratados e o perfil e devolve o resultado. Conferências de bases ausentes ficam "não aplicáveis".

| Conferência | Onde está hoje | Vai para |
|---|---|---|
| Geração × Geração por usina | `geracao_ons.conferir_geracao`, chamada em `analyzer.analisar_geracao_oficial` | `conferencia/geracao.py` |
| Disponibilidade declarada × Disponibilidade por usina | `disponibilidade_ons.conferir_com_evt`, chamada em `analyzer.analisar_disponibilidade` | `conferencia/disponibilidade.py` |
| Vazões × Dados hidrológicos | `hidrologia_ons.alinhar_com_evt`, chamada na extração (código 3) | `conferencia/vazoes.py` (o código 3 passa a sair desta etapa) |
| DISPF × horas por estado operativo | `indicadores_ons.comparar_indicadores_e_horas`, na montagem dos indicadores | `conferencia/indicadores.py` |
| TEIFa e TEIP recalculadas × publicadas | `indicadores_ons.recalcular_taxas`, chamada em `analyzer.analisar_indicadores_ons` | `conferencia/indicadores.py` (a decomposição por unidade fica nas análises) |
| Ficha do cadastro × parâmetros | divergências calculadas em `cadastro_ons.extrair_ficha` | `conferencia/cadastro.py` |

- **Rationale**: FR-006. Hoje as conferências ficam em quatro módulos de dados e na análise. O mapa de fontes (`fontes_relatorio.CONFERENCIAS`) passa a ler os resultados desta etapa.

## R9. Linha de comando única e pré-requisitos

- **Decision**: um único ponto de entrada, `python -m src <comando> --usina <slug>`. O contrato completo está em [contracts/cli-etapas.md](contracts/cli-etapas.md).
  - **Comandos de etapa**: `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio` e `completo`.
  - **Ferramentas**: `copia-seguranca` e `comparar`.
  - **Opções**:
    - `--sem-portal`: a coleta só extrai dos arquivos locais;
    - `--forcar-download`;
    - `--data-geracao` (R2);
    - `--log-level`.
  - **Pré-requisito**: cada etapa confere, antes de gravar, o `etapa.json` concluído da etapa anterior; sem ele, sai com código 5.
  - **Códigos de saída**:
    - 0, 1, 2 e 3: como hoje;
    - 4: perfil inválido;
    - 5: etapa anterior sem resultados.
- **Opções retiradas**:
  - `--full-pipeline`: substituída por `completo`;
  - `--indicadores-only`, `--programacao-only`, `--complementares-only`, `--disponibilidade-only`, `--hidrologia-only`, `--geracao-only`, `--cadastro-only` e `--dicionarios-only`: a coleta cobre os dez conjuntos de uma vez e, sem novidade no portal, não baixa nada;
  - as dez `--sem-*`;
  - `--filter-only`: substituída por `--sem-portal`;
  - `--download-only`;
  - `--cod-usina` e `--nome-reservatorio`: substituídas pelo perfil;
  - `--no-validate-physics`;
  - `--no-generate-plots`;
  - os `main()` de `analyzer`, `processor`, `pdf_generator`, `indicadores_ons`, `programacao_ons`, `cadastro_ons`, `dicionarios_ons`, `disponibilidade_ons`, `hidrologia_ons` e `geracao_ons`.
- **Rationale**: FR-003 e FR-009. Hoje são três comandos principais, dez módulos que também rodam sozinhos e cerca de vinte opções.

## R10. Organização do código e migração

- **Decision**: o código passa a ser organizado em pacotes por etapa, mais `src/comum/`:
  - `src/coleta/`;
  - `src/tratamento/`;
  - `src/conferencia/`;
  - `src/analises/`;
  - `src/relatorio/`.

  A migração **move** funções sem reescrever a lógica, um conjunto por vez, e mantém os testes e a comparação com a linha de base a cada passo. Ao final não resta módulo antigo. A tabela de destino de cada módulo está no data-model (seção 6).
- **Rationale**:
  - O código passa a espelhar o fluxo e as specs.
  - Mover sem reescrever preserva o resultado.
  - O `analyzer.py`, com 3.823 linhas, deixa de concentrar análise, figuras, planilha e Markdown.
- **Alternatives considered**: manter os módulos e só acrescentar um orquestrador. Rejeitada: as specs por etapa apontariam para módulos que misturam etapas, e o "remendo" continuaria no código.

## R11. Generalização das análises

- **Decision**:
  1. **Faixas de afluência** (`hidrologia_ons.DESCRICAO_FAIXAS` e figura 07): "até uma unidade", "entre uma e N unidades" e "acima do engolimento máximo". N vem do perfil, por extenso, e para 2 o texto continua "duas", igual ao aprovado. As chaves internas (`ENTRE_UMA_E_DUAS_UNIDADES`) passam a um nome neutro sem mudar os rótulos exibidos.
  2. **EVT por nível de geração**: as faixas intermediárias vêm do perfil (R6).
  3. **Título, capa, notas e legendas**: nome, estado e parâmetros vêm do perfil e dos dados.
  4. **Mudança de classificação do vertimento**: já é detectada nos dados (`detectar_mudanca_classificacao`); sem o fenômeno, a constatação não aparece.
  5. **Varredura de literais**: um teste procura no código (fora do perfil e dos testes) o nome, os identificadores e os parâmetros da São Domingos e falha se encontrar algum.
- **Rationale**: FR-023 e FR-024; o resultado da São Domingos não muda.

## R12. Specs por etapa e governança

- **Decision**:
  - **Pastas**: cinco, `specs/001-coleta-dados/`, `002-tratamento-dados/`, `003-conferencia/`, `004-analises/` e `005-geracao-relatorio/`. Cada uma tem:
    - `spec.md`: requisitos em vigor, critérios de aceitação e decisões do usuário;
    - `plan.md`: desenho atual (módulos, artefatos e decisões técnicas reunidas das `research.md` antigas);
    - `data-model.md`: entradas e saídas da etapa;
    - `contracts/`, quando a etapa tem interface;
    - `checklists/requirements.md`.
  - **O que não entra**: `tasks.md`, `quickstart.md` e registros de execução, que ficam no histórico do git.
  - **Preparação**: as cinco são escritas em `specs/009-reorganizacao-pipeline/novas-specs/` até a aprovação. As antigas continuam como referência durante a migração. No fechamento, as antigas e a 009 saem e as novas vão para `specs/`.
  - **Mapeamento**: `mapeamento-specs.md` traz cada US, FR e SC das oito specs com o destino (spec e requisito novos) ou "superado", com o motivo.
  - **Mudanças futuras**:
    1. apontar `.specify/feature.json` para a pasta da etapa;
    2. atualizar a `spec.md`;
    3. rodar `/speckit-plan`, que não sobrescreve `plan.md` existente (verificado em `setup-plan.ps1`), `/speckit-tasks` e `/speckit-implement`;
    4. ao concluir, a `tasks.md` sai e o histórico fica no git.

    `/speckit-specify` só cria spec para uma etapa nova, o que deve ser raro.
- **Rationale**: FR-015 a FR-019; uma spec por etapa, sempre no estado atual.
- **Alternatives considered**:
  - Manter a 009 como registro permanente: quebra a correspondência de uma spec por etapa.
  - Arquivar as antigas numa pasta: a pasta de specs continuaria com remendos; o git já guarda tudo.

## R13. Constituição 2.0.0

- **Decision**:
  - **Escrita**: reescrever com `/speckit-constitution`, versão 2.0.0. É MAJOR porque o princípio VI é redefinido (uma usina por perfil) e a governança muda.
  - **Relatório de impacto**: o comentário que a skill gera sai depois de escrito; a própria skill o trata como temporário.
  - **Datas**: ratificação em 2026-09-30; última revisão na data da reescrita.
  - **Histórico**: sem seção de emendas.

  Conteúdo previsto:
  - **Princípios**:
    - I. SDD com uma spec por etapa;
    - II. Relatório fiel aos dados: todo número e frase gerado dos dados, constatações sem parecer, cada constatação uma vez;
    - III. Uma usina por execução, definida pelo perfil, com homônimos excluídos;
    - IV. Coleta completa e rastreável: varredura de todos os arquivos, versões, dicionários, identificador com conferência e auditoria das linhas irregulares e parciais;
    - V. Tratamento sem descarte: regras de consistência e plausibilidade sinalizam e não excluem;
    - VI. Conferência entre fontes: conferências registradas e citadas nas legendas;
    - VII. Relatório padronizado: estrutura, fonte em cada figura e tabela, figuras em seaborn com paleta validada, PDF, Markdown e planilha.
  - **Requisitos técnicos**:
    - Python ≥ 3.11 em `venv`, com dependências mínimas;
    - Windows e PowerShell;
    - gravação segura com uma cópia `.bak` por arquivo de dados;
    - no máximo duas cópias de segurança do projeto;
    - no máximo duas versões anteriores por arquivo bruto;
    - testes sem rede;
    - um nível de log.
  - **Governança**: precedência, mudanças pela spec da etapa, versionamento semântico e histórico no controle de versões.
- **Rationale**: FR-013 a FR-015; documento único, sem emendas e sem valores de usina.

## R14. Cópias de segurança e versões

- **Decision**:
  - **Comando `copia-seguranca --motivo <texto>`**:
    - copia `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, os perfis de `usinas/` (sem `documentos/`), o README e o `requirements.txt` para `_backup_<AAAA-MM-DD>_<motivo>/`;
    - acrescenta `LEIA-ME.txt` e `conftest.py` (que impede a coleta pelo pytest);
    - confere a cópia (quantidade de arquivos e SHA-256 de cada um);
    - só depois exclui as cópias mais antigas além de duas;
    - se a criação ou a conferência falhar, apaga a cópia incompleta e não toca nas outras.
  - **Fora das cópias**: dados brutos, dados derivados e documentos.
  - **`.bak` por arquivo**: a gravação segura já guarda só a versão anterior; vale para coleta e tratamento.
  - **Versões anteriores de brutos**: a coleta poda para as duas mais recentes por arquivo e registra a poda no manifesto.
- **Rationale**: FR-027 a FR-030.

## R15. Inventário de limpeza

- **Decision**: `inventario-limpeza.md` lista cada item com tamanho, uso, ação proposta e motivo, mais uma coluna para a decisão do usuário. O inventário é aplicado só depois da aprovação (FR-031). Critério: o item é usado pelo fluxo, pelos testes, pelas specs, pela constituição ou pelo relatório? Se não é, a ação proposta é excluir, mover para documentos ou manter, com o motivo.

| Item | Tamanho | Ação proposta | Observação |
|---|---|---|---|
| 10 cópias `_backup_*` de 06/10 ou antes | ~87 MB | excluir | autorizado (FR-028) |
| `_backup_2026-10-07_antes_revisao008` e, depois, `_backup_2026-10-07_antes_figuras` | 16 MB cada | excluir ao criar as cópias `antes_conclusao` e `antes_reorganizacao` | regra de duas cópias |
| `.bak` soltos: raiz (3), `src` (4), `tests` (1), `specs` (39) | < 1 MB | excluir | FR-029; o git guarda o histórico |
| `reports/_versao_anterior_2026-09-30/` | 6,3 MB | excluir | versão com informações incorretas, guardada só para comparação |
| `.pytest_cache/` e `__pycache__/` | pequeno | excluir | regenerados |
| `DicionarioDados_EnergiaVertidaTurbinavel.json` na raiz | 4 KB | excluir depois de o validador passar a usar o dicionário baixado em `data/raw/_dicionarios/` | só se o conteúdo for igual; senão, fica no inventário como pendência |
| `Docs_usina/Docs_usina.rar` | 150 MB | excluir | provável cópia compactada dos PDFs da mesma pasta (161 MB); conferir antes |
| `Docs_usina/` (PDFs) | 161 MB | mover para `usinas/sao_domingos/documentos/` | documentos da usina |
| Ofício, RF 0009/2017, modelo do RF 2026 (raiz) | ~2,6 MB | mover para `usinas/sao_domingos/documentos/` | o RF 0009/2017 é a fonte dos parâmetros |
| Resoluções da ANEEL, RFs SEI de monitoramento, imagens de tipos de despacho (raiz) | ~3,4 MB | mover para `referencias/` | documentos gerais |
| Imagem do WhatsApp (raiz) | 180 KB | decisão do usuário | conteúdo não usado pelo fluxo |
| `data/ccee/` e `data/aneel_bi/` | 59 MB | decisão do usuário (proposta: excluir) | conferências manuais de 01–02/10, fora do relatório; os resultados ficam registrados na spec da conferência |
| `.agents/skills/` | 156 KB | decisão do usuário (proposta: excluir se o Antigravity não é mais usado) | cópias do Spec Kit para outro agente |
| `data/processed/` e arquivos soltos de `reports/` (layout antigo) | ~90 MB | excluir no inventário final, depois da comparação | substituídos por `data/usinas/` e `reports/<slug>/` |
| `venv/`, `.mcp.json`, `.claude/`, `.specify/` | n/a | manter | ambiente e ferramentas |

- **Rationale**: FR-031 a FR-034.
  - O que está fora do git, como documentos e dados, é exclusão irreversível e precisa de aprovação.
  - Mover os documentos, em vez de excluir, preserva o material da fiscalização.

## R16. Testes

- **Decision**:
  - **Organização**: `tests/` espelha os pacotes (`coleta/`, `tratamento/`, `conferencia/`, `analises/`, `relatorio/` e `comum/`) e tem uma `integracao/`.
  - **Dados de teste**: os dados sintéticos de hoje continuam (`conftest.py`). Em `tests/fixtures/` entram um perfil fictício (três unidades, Francis, identificadores próprios) e arquivos brutos sintéticos dessa usina.
  - **Testes novos**:
    - fluxo completo da usina fictícia, sem rede e com `--sem-portal`;
    - recusa de perfil incompleto;
    - pré-requisito entre etapas (código 5);
    - poda das cópias e das versões;
    - varredura de literais da São Domingos (R11).
  - **Rede**: bloqueada, como hoje, com proxy inválido nas variáveis de ambiente.
  - **Testes que saem**: os das opções retiradas, substituídos pelos testes da linha de comando nova. Nenhum comportamento perde cobertura (SC-007).
- **Rationale**: FR-012, SC-005 e SC-007.

## R17. Conclusão por regras declaradas (US6)

- **Decision**:
  - **Lugar**: seção `conclusao` ("Conclusão"), sempre presente, depois de "Qualidade dos dados" e antes de "Notas metodológicas e limitações", na estrutura única do relatório (`estrutura_relatorio.SECOES`). Por isso entra no PDF, no Markdown e no sumário pelo mesmo caminho das outras seções.
  - **Geração**:
    - `montar_conclusao(res)` aplica as regras C1 a C11 (catálogo da spec) aos resultados já calculados em `ResultadosAnalise`. Hoje fica no `analyzer`; depois da reorganização, em `src/analises/conclusao.py`.
    - Os resultados usados são: EVT por nível e com usina parada; programação; faixas de afluência; perfil diurno; disponibilidade, DISPF, TEIFa e TEIP com a decomposição por unidade; horas por estado; divergências; capacidade não sincronizada × reserva desligada; validação (R7 e R9); eventos de indisponibilidade; indicadores anuais por unidade; sinalizações da hidrologia.
    - Cada regra gera no máximo um item por lista: lista, ordem, regra, texto e seções de origem. Os itens vão para `res.conclusao`.
  - **Seções de origem**: o item guarda as chaves das seções. O número ("seções 8 e 9") é resolvido na montagem do relatório, porque a numeração depende das seções presentes.
  - **Texto**:
    - Cada item tem uma frase, com os números formatados como no resto do relatório.
    - O vocabulário é de indício: "indício", "possível", "a confirmar".
    - Uma lista de termos proibidos é conferida nos testes ("satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente", "culpa").
    - A frase de abertura é metodológica, como os títulos das seções, e não traz números.
  - **Limite**:
    - O PDF e o Markdown mostram até cinco itens por lista, na ordem do catálogo.
    - A aba CONCLUSAO tem todos os itens e fica coberta pela aba FONTES, como "calculado neste relatório".
    - Os itens da C8 em "A confirmar com o agente" se juntam ao item da C7.
  - **Nota metodológica**: um item com as regras e os limiares, gerado a partir das constantes.
  - **Limiares**: são regras gerais, novas constantes ao lado das atuais:
    - EVT com usina parada ≥ 10 % da EVT;
    - programação de até 1 MW em ≥ 50 % dessas horas, só para a frase;
    - afluência até o engolimento em ≥ 80 % das horas com EVT;
    - razão diurna ≥ 2, a de hoje;
    - unidade com ≥ 2/3 da TEIFa, ou limitação forçada de potência (HEDF) em ≥ 50 % dos meses. Desligamentos forçados curtos não entram nessa contagem: na base real, a UG1 tem algum registro forçado em 61 dos 80 meses, quase todos curtos, e seria apontada sem motivo;
    - programação acima de 5 MW com a usina parada, o limiar de hoje;
    - diferença ≥ 5 GWh entre a capacidade não sincronizada e a reserva desligada;
    - R7 ≥ 100 h;
    - indisponibilidade total ≥ 30 dias;
    - indisponibilidade programada da unidade ≥ 20 % num ano completo;
    - R9 ≥ 24 h.
  - **Testes**:
    - cada regra dispara e não dispara com dados sintéticos;
    - limite de cinco itens e ordem;
    - termos proibidos;
    - nenhum texto de constatação repetido;
    - seção antes das notas, também no sumário;
    - Markdown igual ao PDF;
    - aba CONCLUSAO e cobertura na FONTES;
    - a conclusão cabe numa página do PDF (a seção das notas começa no máximo uma página depois);
    - na base real, a UG2 nomeada.
- **Prévia para a São Domingos**, calculada com os números do relatório aprovado. O texto final sai da implementação e passa pela aprovação do usuário.
  - **Pontos de atenção**:
    - C1: 41,9 GWh de EVT (28,4 %) com a usina parada, em 2.141 h, sobretudo em 2025 e 2026; 91,1 % das horas com programação do ONS de até 1 MW;
    - C3: em 92,9 % das horas com EVT a afluência cabia nas turbinas;
    - C4: concentração da EVT entre 9h e 15h em 2025 e 2026;
    - C5: disponibilidade declarada de 87,8 % (3,2 p.p. abaixo da referência) e TEIFa de 4,11 % (referência 2,333 %);
    - C9: geração média de 74,4 % da garantia física, e EVT de 2025 como a maior da série.
  - **Possíveis problemas**:
    - C2: UG2, limitação forçada de potência em 78 de 80 meses (3.824 h equivalentes; UG1, 51 h), 87 % da TEIFa;
    - C6: 182 h em 68 eventos com a usina parada e programação acima de 5 MW;
    - C7: capacidade não sincronizada diferente da reserva desligada em 2024 (−11,7 GWh) e 2025 (−12,4 GWh), e 4 meses-unidade com DISPF e TEIP divergentes;
    - C8: geração acima da disponibilidade declarada em 293 h.
  - **A confirmar com o agente**:
    - C1: motivo das paradas com EVT e programação zero;
    - C2: causa e situação da limitação da UG2;
    - C6: ocorrências nas 68 paradas com programação;
    - C7 e C8: classificação dos estados e declarações de disponibilidade informadas ao ONS;
    - C10: causa da indisponibilidade de 25/09 a 24/12/2019 e das paradas programadas longas (UG2 em 2022).
  - **A verificar em campo**:
    - C1: livro de operação, supervisório e vertedouro nas datas dos maiores eventos;
    - C2: potência máxima atual da UG2 e registros de limitação;
    - C6: registros de ocorrência;
    - C10: plano e registros de manutenção;
    - C11: instrumentação de nível e vazão e medição da vazão turbinada.
- **Rationale**:
  - O usuário pediu a conclusão.
  - Gerar por regras declaradas mantém o princípio de que todo texto do relatório vem dos dados. Também a torna reproduzível e aplicável a outras usinas.
  - O vocabulário de indício separa a conclusão de um parecer, o que preserva a FR-005 da spec 003.
- **Alternatives considered**:
  - Texto escrito à mão: rejeitado, porque não vem dos dados, não se reproduz e não serve a outras usinas.
  - Resumo automático das constatações: rejeitado, porque repetiria texto, e o usuário já rejeitou a repetição (spec 008).
  - Nota ou classificação de desempenho: rejeitada, porque seria parecer.
  - Conclusão na capa: rejeitada, porque a capa tem só dados básicos e sumário, e o usuário pediu uma seção de conclusão.
