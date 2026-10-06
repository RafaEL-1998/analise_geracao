# Feature Specification: Coleta e Filtragem de Dados ONS - UHE São Domingos

**Feature Branch**: `001-ons-coleta-sao-domingos`

**Created**: 2026-09-30

**Status**: Implementado (revisado em 2026-10-05)

**Input**: User description: "Preciso baixar todos os documentos em .csv disponíveis no site 'https://dados.ons.org.br/dataset/energia-vertida-turbinavel/resource/3167ef1a-12f1-43a5-9d29-6f6616bc7052'. O filtro que preciso é exatamente esse: 'SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;' é referente a UHE São Domingos. Eu não sei quando que entrou em operação, acredito que olhei uma vez nos arquivos do site de 2015 e não tinha nada referente a 'SAO DOMINGOS' mas o certo é verificar ao menos esse último nome em TODOS os arquivos. Quero todos os scripts em python."

**Nota de revisão**: revisão retroativa (SDD) para que a especificação reflita o sistema implementado após a auditoria de 30/09/2026 e a conferência externa de 02/10/2026. O texto de entrada acima é preservado como foi recebido; os requisitos e critérios alterados ou removidos estão justificados na seção "Histórico de revisões", ao final.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Descoberta e Download Completo dos Conjuntos Históricos de Dados (Priority: P1)

Como analista regulatório e de desempenho operacional da UHE São Domingos, quero identificar e baixar automaticamente todos os arquivos CSV de Energia Vertida Turbinável disponíveis no portal de dados abertos do ONS, mantendo a cópia local sincronizada com a versão publicada de cada arquivo, de modo que possua a série histórica integral armazenada localmente sem dependência de intervenção manual nem risco de omissão de arquivos históricos ou de uso de versões já revisadas pelo ONS.

**Why this priority**: A confiabilidade da análise regulatória e fiscalizatória depende da integridade completa da série histórica. Omitir qualquer arquivo histórico, ou trabalhar com uma versão que o ONS já substituiu, comprometeria a exatidão temporal e a rastreabilidade da geração e do vertimento da usina.

**Independent Test**: Pode ser testado de forma independente disparando a rotina de descoberta de recursos contra o catálogo público do ONS e verificando se todos os arquivos CSV publicados (um por ano de 2015 a 2023 e um por mês a partir de 01/2024) foram baixados para a pasta de dados brutos, e se o registro de versões local contém, para cada arquivo, a data de última modificação e o tamanho publicados.

**Acceptance Scenarios**:

1. **Given** que o portal de dados abertos do ONS disponibiliza múltiplos recursos CSV correspondentes aos períodos anuais e mensais da série de Energia Vertida Turbinável, **When** o processo de coleta é executado, **Then** todos os arquivos CSV são identificados, baixados e armazenados localmente no diretório de dados brutos preservando seus nomes e formatos originais.
2. **Given** que alguns arquivos já foram baixados em execuções anteriores e não foram alterados pelo ONS, **When** a rotina de coleta é reexecutada, **Then** o sistema reconhece que a cópia local corresponde à versão publicada (mesma data de última modificação e mesmo tamanho registrados no manifesto de versões) e não refaz o download.
3. **Given** que o ONS republicou um arquivo já baixado (data de última modificação diferente da registrada, ou, na ausência de registro, tamanho local diferente do publicado), **When** a rotina de coleta é reexecutada, **Then** o arquivo é baixado novamente, substitui a cópia local de forma atômica e a nova versão é registrada no manifesto.
4. **Given** uma falha de rede persistente ao baixar um arquivo, **When** as retentativas se esgotam, **Then** o sistema informa qual arquivo falhou, preserva o manifesto do que já foi sincronizado e encerra com código de erro.

---

### User Story 2 - Filtragem Exaustiva e Consolidação de Registros da UHE São Domingos (Priority: P1)

Como especialista de dados, quero inspecionar exaustivamente cada linha de cada arquivo CSV baixado e extrair os registros da UHE São Domingos identificando a usina pelo código que o ONS lhe atribui (`cod_usina` = 153), conferido pelo nome do reservatório (`SAO DOMINGOS`), de modo que todos os registros pertinentes sejam extraídos e consolidados em uma única base analítica, independentemente de mudanças no nome do agente proprietário.

**Why this priority**: É a entrega de valor central para a análise operacional da UHE São Domingos. É mandatório garantir que nenhum registro seja perdido, independentemente do ano em que a usina tenha passado a ter medição reportada e de alterações cadastrais do agente (CGT ELETROSUL até 02/2026, AXIA SUL a partir de 03/2026).

**Independent Test**: Pode ser testado fornecendo amostras de arquivos históricos (arquivos sem a usina, arquivos com a usina sob os dois nomes de agente, linhas em que só o código ou só o nome do reservatório conferem e instantes repetidos entre arquivos) e verificando se as linhas da usina são extraídas com fidelidade de colunas, ordenadas cronologicamente e consolidadas sem duplicidades, e se as linhas divergentes são contadas sem serem extraídas.

**Acceptance Scenarios**:

1. **Given** um arquivo CSV contendo registros horários com `cod_usina` 153 e reservatório `SAO DOMINGOS`, seja o agente `CGT ELETROSUL` ou `AXIA SUL`, **When** a rotina de filtragem é aplicada, **Then** todas as linhas correspondentes são extraídas com todas as grandezas horárias preservadas.
2. **Given** um arquivo CSV de anos iniciais (por exemplo, 2015) no qual a UHE São Domingos não possui registros, **When** a varredura é concluída sobre o arquivo, **Then** o sistema registra zero ocorrências para aquele arquivo (status `SEM_REGISTROS`) e avança normalmente para os próximos arquivos sem gerar falha ou interrupção.
3. **Given** registros consolidados ao final de toda a série histórica, **When** a base final é gerada, **Then** cada registro contém o nome do arquivo de origem e o critério de identificação aplicado, para fins de rastreabilidade e auditoria.
4. **Given** uma linha em que apenas um dos critérios confere (código 153 com outro reservatório, ou reservatório `SAO DOMINGOS` com outro código), **When** a varredura é concluída, **Then** a linha não é extraída, é contabilizada no relatório de auditoria em contador próprio para cada caso e gera alerta no log para verificação de mudança de cadastro no ONS.
5. **Given** o mesmo instante da mesma usina presente em mais de um arquivo, **When** a base é consolidada, **Then** permanece um único registro por par (`cod_usina`, `din_instante`), prevalecendo o do arquivo lido por último (arquivos anuais antes dos mensais), e as duplicatas com valores diferentes são contadas e registradas em log.

---

### User Story 3 - Relatório de Auditoria e Validação da Varredura (Priority: P2)

Como auditor técnico, quero visualizar um relatório sumarizado de cada arquivo CSV avaliado (nome do arquivo, total de linhas lidas, registros extraídos da UHE São Domingos, linhas com identificação divergente, codificação de leitura e status de processamento), de modo a comprovar documentalmente que 100% dos arquivos públicos foram verificados.

**Why this priority**: Fornece a garantia e a evidência de conformidade exigida para processos fiscalizatórios e relatórios de desempenho operacional, eliminando incertezas sobre a abrangência da varredura.

**Independent Test**: Pode ser testado avaliando o relatório de auditoria gerado após uma varredura completa e validando se o total de arquivos listados confere com o total de recursos CSV do portal do ONS e se a soma dos registros extraídos confere com a base consolidada.

**Acceptance Scenarios**:

1. **Given** a conclusão do processamento de todos os arquivos do diretório de dados brutos, **When** o relatório de auditoria é gerado, **Then** ele lista todos os arquivos verificados com data e hora do processamento (UTC), linhas totais lidas, registros extraídos, linhas em que só o código confere, linhas em que só o nome do reservatório confere, codificação usada na leitura e status (`PROCESSADO`, `SEM_REGISTROS` ou `FALHA`).
2. **Given** um arquivo que não pode ser lido (vazio, corrompido ou sem as colunas de identificação da usina), **When** a varredura é concluída, **Then** o arquivo recebe status `FALHA` no relatório, a varredura dos demais arquivos prossegue, as saídas são gravadas e a execução termina com código de saída 2, sinalizando que a base consolidada está incompleta.

---

### Edge Cases

- O que acontece se a conexão com o portal do ONS oscilar ou sofrer timeout durante o download de arquivos pesados? O sistema aplica retentativas com recuo exponencial e informa com precisão qual arquivo falhou. Esgotadas as tentativas, a sincronização é interrompida (os arquivos seguintes não são baixados nessa execução), o manifesto do que já foi sincronizado é gravado e a execução termina com código 1.
- O que acontece se o ONS revisar um arquivo já baixado? O arquivo é baixado novamente na próxima execução (ver US1, cenário 3). A versão anterior não é preservada (limitação registrada no Histórico de revisões).
- O que acontece se algum arquivo CSV histórico apresentar variações no cabeçalho ou na ordem das colunas? As colunas são localizadas pelo nome no cabeçalho, não pela posição. Se faltarem as colunas de identificação (`cod_usina` ou `nom_reservatorio`), o arquivo recebe status `FALHA` e o erro é registrado no log.
- O que acontece se o nome do agente, da bacia ou do rio mudar em algum ano? Esses campos não são usados na identificação; a série continua íntegra (caso real: troca de CGT ELETROSUL para AXIA SUL em 03/2026). Se mudar o código da usina ou o nome do reservatório, as linhas em que só um critério confere são contadas no relatório de auditoria e geram alerta no log, para auditoria humana.
- O que acontece se o arquivo baixado estiver vazio ou com formato corrompido? O arquivo recebe status `FALHA`, o erro é registrado no log e a execução termina com código 2.
- O que acontece se o arquivo não estiver em UTF-8? O arquivo é relido integralmente em Latin-1 e a codificação efetivamente usada é registrada no relatório de auditoria.
- O que acontece com linhas com menos campos do que o necessário para identificar a usina? São contadas no total de linhas lidas e descartadas, sem registro em log (limitação registrada no Histórico de revisões).
- O que acontece com horas ausentes na série publicada? O sistema não preenche nem cria horas: reproduz o que o ONS publica. Caso real: 04/11/2018 00h, hora inexistente pelo início do horário de verão.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE consultar o catálogo de dados abertos do ONS e identificar dinamicamente todos os recursos em formato CSV disponíveis no conjunto de dados "Energia Vertida Turbinável".
- **FR-002**: O sistema DEVE baixar todos os arquivos CSV mapeados para a pasta designada de dados brutos (`raw`), mantendo um manifesto local com a data de última modificação e o tamanho publicados de cada arquivo. Uma cópia local só DEVE ser reaproveitada se corresponder à versão publicada (mesma data de última modificação e mesmo tamanho registrados no manifesto; na ausência de registro no manifesto, tamanho local igual ao publicado). Arquivos revisados pelo ONS DEVEM ser baixados novamente. O download DEVE ter retentativas com recuo exponencial e gravação atômica (o arquivo final só é substituído após o download completo).
- **FR-003**: O sistema DEVE processar 100% dos arquivos CSV baixados, sem pular nenhum exercício ou ano histórico com base em premissas de início de operação.
- **FR-004**: O sistema DEVE extrair um registro somente quando o código da usina no ONS (`cod_usina`) for 153 E o nome do reservatório, normalizado (sem acentos e em maiúsculas), contiver `SAO DOMINGOS`. O nome do agente e os demais campos cadastrais (subsistema, bacia, rio) NÃO DEVEM ser usados como critério de extração. O código e o nome de referência DEVEM ser parametrizáveis na execução.
- **FR-005**: O sistema DEVE contar, por arquivo, as linhas em que apenas um dos dois critérios do FR-004 confere (código 153 com outro reservatório; reservatório `SAO DOMINGOS` com outro código), sem extraí-las, registrando as contagens no relatório de auditoria e emitindo alerta no log.
- **FR-006**: O sistema DEVE preservar em cada linha extraída o nome do arquivo de origem e o critério de identificação aplicado. A data e hora do processamento DEVEM ser registradas por arquivo no relatório de auditoria, e a versão publicada de cada arquivo (data de última modificação e tamanho), no manifesto de versões.
- **FR-007**: O sistema DEVE consolidar todos os registros extraídos em um arquivo estruturado único (CSV consolidado), sem duplicidade do par (`cod_usina`, `din_instante`) e ordenado cronologicamente pelo instante da medição. Em caso de duplicata, DEVE prevalecer o registro do arquivo lido por último (arquivos lidos em ordem de nome: anuais antes dos mensais), e as duplicatas com valores diferentes DEVEM ser contadas e registradas em log.
- **FR-008**: O sistema DEVE gerar, ao término da varredura, um relatório de auditoria com uma linha por arquivo inspecionado, contendo: nome do arquivo, período de referência, total de linhas lidas, registros extraídos, linhas só com o código, linhas só com o nome do reservatório, codificação usada na leitura, status de processamento e data e hora do processamento.
- **FR-009**: O sistema DEVE operar de forma totalmente não interativa quando acionado, emitindo na saída padrão logs detalhados de cada etapa (recursos descobertos, arquivos baixados ou reaproveitados, linhas lidas e extraídas por arquivo, divergências, duplicatas, resumo final) e terminando com código de saída que distinga sucesso (0), erro de execução ou de rede (1) e base incompleta por arquivo não lido (2); argumentos inválidos também resultam em código 2 (ver `contracts/cli-contract.md`).
- **FR-010**: O sistema DEVE ler os arquivos linha a linha, com separador ponto e vírgula, tentando UTF-8 e relendo o arquivo em Latin-1 em caso de erro de decodificação. Um arquivo que não puder ser lido DEVE receber status `FALHA` sem interromper a varredura dos demais.

### Key Entities *(include if feature involves data)*

- **Recurso ONS**: Entidade que representa um arquivo da série histórica no portal ONS (identificador do recurso, nome, URL de download, tamanho e data de última modificação publicados, caminho local e status de sincronização: pendente, baixado, atualizado, reaproveitado ou falho).
- **Manifesto de Versões**: Registro local, por arquivo bruto, da versão publicada que foi baixada ou reconhecida (URL, data de última modificação, tamanho publicado, tamanho local, data e hora do registro e origem do registro: download ou arquivo já existente).
- **Registro Horário de Vertimento**: Entidade representativa de cada observação horária, contendo atributos de localização e cadastro (`id_subsistema`, `nom_subsistema`, `nom_bacia`, `nom_rio`, `nom_agente`, `nom_reservatorio`, `cod_usina`), instante temporal (`din_instante`), grandezas operacionais (`val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`) e metadados de rastreabilidade (arquivo de origem e critério de identificação).
- **Base Consolidada UHE São Domingos**: Conjunto ordenado e deduplicado, por par (`cod_usina`, `din_instante`), de todas as medições históricas extraídas da UHE São Domingos.
- **Registro de Auditoria de Arquivo**: Entidade de controle que armazena para cada arquivo processado o nome do arquivo, o período de referência, o total de linhas lidas, os registros extraídos, as linhas com identificação divergente (só código; só nome), a codificação de leitura, o status e a data e hora do processamento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos arquivos CSV catalogados na página de Energia Vertida Turbinável do ONS são baixados e inspecionados.
  - *Verificação (30/09/2026)*: 42 de 42 arquivos (9 anuais, 2015 a 2023; 33 mensais, 01/2024 a 09/2026) sincronizados e presentes no relatório de auditoria.
- **SC-002**: Zero registros da UHE São Domingos são omitidos ao longo de toda a série temporal disponível nos arquivos do ONS.
  - *Verificação (02/10/2026)*: conferência externa com os dados do ONS: a base local é idêntica à publicada no S3 do ONS em todos os meses de 08/2018 a 08/2026 (ver research.md, seção 7). O mês 09/2026 não fez parte dessa conferência.
- **SC-003**: A rotina de filtragem e consolidação local é capaz de inspecionar a totalidade dos arquivos baixados em menos de 3 minutos em ambiente padrão de execução.
  - *Verificação (30/09/2026)*: cerca de 45 segundos para os 42 arquivos (cerca de 15 milhões de linhas), segundo os carimbos de horário do relatório de auditoria.
- **SC-004**: O arquivo consolidado gerado possui 100% de consistência cronológica, sem linhas duplicadas para o mesmo par (`cod_usina`, `din_instante`).
  - *Verificação (05/10/2026)*: 70.895 registros em ordem crescente e zero duplicatas.
- **SC-005**: 100% dos arquivos verificados possuem registro detalhado no relatório de auditoria, comprovando a conferência inclusive nos períodos sem registros da usina (ex.: 2015).
  - *Verificação (30/09/2026)*: 42 linhas no relatório; 2015, 2016 e 2017 com status `SEM_REGISTROS`; nenhum arquivo com `FALHA`.
- **SC-006**: Mudanças no nome do agente não provocam perda nem descontinuidade da série, e toda linha com identificação divergente (só código ou só nome) aparece contabilizada no relatório de auditoria.
  - *Verificação (30/09/2026)*: série contínua com 65.807 registros sob CGT ELETROSUL (28/08/2018 a 28/02/2026) e 5.088 sob AXIA SUL (01/03/2026 a 28/09/2026); zero linhas divergentes nos 42 arquivos.

## Assumptions

- O portal de dados abertos do ONS segue a especificação CKAN e permite a descoberta e o download público direto dos recursos, sem autenticação, informando para cada recurso o tamanho e a data de última modificação.
- O catálogo publica um CSV por ano até 2023 e um CSV por mês a partir de 2024, e o ONS revisa arquivos já publicados (caso real: o arquivo de 09/2026 foi republicado em 30/09/2026 e baixado novamente).
- O formato de codificação dos arquivos CSV do ONS é UTF-8 ou Latin-1, com separador ponto e vírgula (`;`). Na execução de 30/09/2026, os 42 arquivos foram lidos em UTF-8.
- A UHE São Domingos é identificada nos arquivos do ONS pelo `cod_usina` 153, estável ao longo da série, e pelo reservatório `SAO DOMINGOS`; está no subsistema `SE`/`SUDESTE`, bacia `PARANA`, rio `VERDE`. O agente é `CGT ELETROSUL` até 02/2026 e `AXIA SUL` a partir de 03/2026.
- A usina só aparece no conjunto de dados a partir de 28/08/2018 00h; os arquivos de 2015, 2016 e 2017 não a contêm. O período entre o início da operação comercial (2013) e essa data não é coberto por esta fonte. A série local vai até 28/09/2026 23h (70.895 registros horários, com 1 hora ausente em 04/11/2018 00h, por causa do início do horário de verão).
- Os arquivos brutos baixados são retidos localmente para permitir reprocessamentos sem novos downloads; quando o ONS revisa um arquivo, a cópia local é substituída pela nova versão.
- As grandezas numéricas usam ponto decimal; a vírgula decimal também é aceita na conversão. Campos vazios ou não numéricos tornam-se valores ausentes, nunca zero.
- Fora do escopo desta feature: a etapa 3 de `python -m src.main` (indicadores oficiais do ONS por unidade geradora) e as opções `--indicadores-only` e `--sem-indicadores`; ver `specs/004-conferencia-outros`.

## Histórico de revisões

### 2026-10-05 - Revisão retroativa (SDD) após a auditoria de 30/09/2026 e a conferência de 02/10/2026

**Contexto**: em 30/09/2026 o pipeline foi auditado e corrigido por prompt, sem atualização prévia desta especificação; em 02/10/2026 a base gerada foi conferida externamente com os dados do ONS e o `src/main.py` recebeu a etapa 3 (escopo da spec 004). Esta revisão alinha a especificação ao código em vigor. A versão anterior deste arquivo está preservada em `spec.md.2026-10-05.bak`.

**Alterações**:

- **Status**: "Draft" passou a "Implementado (revisado em 2026-10-05)", porque o código existe, foi testado e gerou a base usada na fiscalização.
- **FR-004** (alterado): a chave de filtragem por linha textual com o nome do agente (`SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;`) foi substituída por `cod_usina` 153 + nome do reservatório normalizado contendo `SAO DOMINGOS`, porque o agente mudou de CGT ELETROSUL para AXIA SUL em mar/2026. Na versão original, nenhum registro de 08/2018 a 02/2026 casava com a chave canônica: só eram encontrados pela busca secundária, e a chave só passou a casar em 03/2026 (relatório de auditoria da versão original, preservado em `reports/_versao_anterior_2026-09-30/data_processed/relatorio_auditoria_varredura.csv`). Auditoria de 30/09/2026.
- **FR-005** (alterado): a "verificação secundária" por `SAO DOMINGOS` no reservatório, que também extraía as linhas encontradas (marcadas `SECONDARY`), foi substituída pela contagem, sem extração, das linhas em que só o código ou só o nome confere. Motivo: o nome isolado pode capturar reservatórios homônimos e o código isolado não detecta mudança de cadastro; exigir os dois e contar os casos parciais torna qualquer mudança visível sem contaminar a base. Auditoria de 30/09/2026.
- **FR-002** (alterado): "armazenando-os de forma persistente e idempotente" passou a exigir cache sensível às revisões do ONS (manifesto com data de última modificação e tamanho publicados), gravação atômica e retentativas, porque a conferência apenas pelo tamanho não detecta revisões do ONS de mesmo tamanho e o ONS republica arquivos (o de 09/2026 foi republicado no próprio dia 30/09/2026). Auditoria de 30/09/2026.
- **FR-006** (alterado): a data do processamento deixou de ser exigida em cada linha extraída e passou a ser registrada por arquivo no relatório de auditoria; a versão publicada do arquivo passou a ficar no manifesto; foi acrescentado o critério de identificação em cada linha. Motivo: reflete o que o código grava; uma data por linha repetiria o mesmo valor para todas as linhas do arquivo. Revisão de 05/10/2026.
- **FR-007** (alterado): a deduplicação passou a ser explícita pelo par (`cod_usina`, `din_instante`), com prevalência do arquivo lido por último e contagem das duplicatas conflitantes. A regra anterior (data-model: "prevalecer o arquivo com data de emissão mais recente ou o registro canônico mais completo") deixou de ser aplicável, porque não há mais distinção canônico/secundário e a ordem de leitura é determinística. Auditoria de 30/09/2026.
- **FR-008** (alterado): o conteúdo do relatório passou a ser enumerado com os campos reais (registros extraídos, só código, só nome, codificação), no lugar de "linhas totais e linhas encontradas". Auditoria de 30/09/2026.
- **FR-009** (alterado): "gravando logs detalhados" passou a "emitindo na saída padrão", porque o pipeline não grava arquivo de log; foram acrescentados os códigos de saída implementados. Revisão de 05/10/2026.
- **FR-010** (novo): leitura linha a linha com UTF-8 e releitura em Latin-1, com status `FALHA` sem interromper a varredura. Antes, isso constava apenas como premissa e como caso-limite; agora é requisito, porque o código em vigor desde a auditoria de 30/09/2026 se comporta assim e sinaliza a base incompleta com o código de saída 2.
- **US1** (alterada): descrição e cenário 2 passaram a tratar da versão publicada; cenários 3 (arquivo revisado pelo ONS) e 4 (falha persistente de rede) acrescentados.
- **US2** (alterada): a descrição e o cenário 1 deixaram de citar a chave canônica e passaram a citar código + reservatório, com os dois nomes de agente; cenários 4 (identificação divergente) e 5 (duplicatas entre arquivos) acrescentados. O cenário 3 passou a incluir o critério de identificação.
- **US3** (alterada): o cenário 1 passou a listar os campos reais do relatório; cenário 2 (arquivo ilegível, código de saída 2) acrescentado.
- **Edge Cases** (alterados): o caso de alteração do agente deixou de prever "correspondência secundária" e passou a descrever a contagem de divergências; o caso de cabeçalho passou a descrever a localização das colunas por nome (não por posição); o caso de arquivo corrompido passou a usar o status `FALHA` ("pendente de revisão" não existe no código). Acrescentados: revisão de arquivo pelo ONS, codificação, linhas com campos insuficientes e hora ausente (horário de verão).
- **SC-004** (alterado): "mesmo instante temporal (`din_instante`)" passou a "mesmo par (`cod_usina`, `din_instante`)", que é a chave efetivamente aplicada (equivalente na prática, pois a base contém uma única usina).
- **SC-001 a SC-005**: acrescentadas as verificações com a evidência de cada critério, sem alterar o texto dos critérios (exceto SC-004).
- **SC-006** (novo): estabilidade da série diante da troca de agente e contabilização das divergências.
- **Key Entities** (alteradas): Recurso ONS ganhou data de última modificação e o status "atualizado"; Registro de Auditoria passou a ter os campos reais; nova entidade Manifesto de Versões; a Base Consolidada passou a citar a chave (`cod_usina`, `din_instante`).
- **Assumptions** (alteradas): a premissa "agente Axia Sul (ou correlato histórico)" foi substituída pela identificação por `cod_usina` 153 e pelos dois agentes com as respectivas datas; acrescentadas a estrutura do catálogo (anual até 2023, mensal desde 2024), as revisões do ONS, a cobertura real (a partir de 28/08/2018; 2015 a 2017 sem a usina; 1 hora ausente em 04/11/2018) e a exclusão de escopo da etapa 3 (spec 004).
- **Validação externa (02/10/2026)**: conferência pelo servidor MCP de dados do ONS: a base local bate exatamente com o S3 do ONS em todos os meses de 08/2018 a 08/2026. Nenhum requisito foi alterado por ela; registrada como evidência do SC-002 e em research.md.

**Pendências (não resolvidas nesta revisão)**:

1. **Constituição, princípio IV**: `.specify/memory/constitution.md` (v1.0.0) ainda exige "aplicar estritamente a chave canônica definida `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"`", o que diverge do FR-004 e do FR-005 desta revisão. Também pede metadados de "data do arquivo" e "data de ingestão" em toda linha filtrada, que o sistema guarda por arquivo (manifesto e relatório de auditoria), não por linha. Pendente de emenda da constituição pelo processo de governança (justificativa, versionamento semântico e Sync Impact Report); a constituição não foi alterada nesta revisão.
2. **Constituição, princípio IV (log de linhas malformadas)**: linhas com menos campos do que o necessário são descartadas sem registro em log. Pendente de ajuste no código.
3. **Constituição, princípio V, e regra de imutabilidade dos dados brutos**: quando o ONS revisa um arquivo, a cópia local é substituída e a versão anterior não é preservada. Pendente de decisão: guardar a versão anterior ou emendar a regra.
4. **Opção `--log-level`**: só altera o nível do logger `main`; os módulos de coleta, filtragem e consolidação continuam em INFO. Pendente de ajuste no código ou no contrato.
5. **Evidência da conferência de 02/10/2026**: a conferência foi feita de forma interativa e não há script nem arquivo de saída dela no repositório. Pendente de registro reproduzível.
6. **Princípio I (SDD)**: as alterações de 30/09/2026 e 02/10/2026 foram feitas sem atualização prévia da especificação. Esta revisão regulariza a situação retroativamente.

### 2026-10-05 — spec 005 (conformidade com a constituição 1.1.0)

- Constituição emendada para 1.1.0: o princípio IV vincula a chave canônica `SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;` ao conjunto Energia Vertida Turbinável como referência de localização e adota `cod_usina` 153 + nome do reservatório como regra de extração; o novo princípio VI restringe o projeto à UHE São Domingos (MS). Resolve a pendência T039.
- `src/collector.py`: arquivo republicado pelo ONS com conteúdo diferente tem a cópia anterior preservada em `_versoes_anteriores/` e registrada no manifesto (`versoes_anteriores`). Resolve T041.
- `src/filter.py`: linhas não vazias com número de campos diferente do cabeçalho deixam de ser descartadas em silêncio: são contadas em `registros_formato_irregular` (nova coluna da auditoria) e avisadas no log. Varredura de 05/10/2026: 0 em 42 arquivos. Resolve T040.
- `src/logger.py`/`src/main.py`: `--log-level` aplica-se a todos os loggers do pipeline. Resolve T042.
- Pendência T043 (evidência reproduzível da conferência de 02/10/2026, item 5 das pendências acima): encerrada sem implementação por decisão do usuário em 05/10/2026 (não necessária). O resultado da conferência fica registrado em `research.md` (seção 7) e em `specs/004-conferencia-outros/research.md` (Parte B); a base local continua conferível a qualquer momento pelo servidor MCP de dados do ONS.

### 2026-10-05 — spec 006 (bases complementares, dicionários e cópia de segurança)

- A base consolidada e o relatório de auditoria da varredura passam a ser gravados por `src/persistencia.py`:
  - a versão anterior fica em `<arquivo>.bak`;
  - conteúdo idêntico não é regravado;
  - a gravação é conferida no disco e, em falha, o arquivo volta à versão anterior (constituição 1.2.0, Requisito Técnico 3).
  - O relatório de auditoria muda a cada execução, porque registra a data e a hora do processamento.
- O dicionário de dados da EVT (PDF e JSON) é obtido a cada coleta em `data/raw/_dicionarios/`, sem novo download dos arquivos de dados (constituição 1.2.0, princípio IV).
