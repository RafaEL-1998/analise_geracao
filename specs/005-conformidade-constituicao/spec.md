# Feature Specification: Conformidade com a Constituição 1.1.0 - UHE São Domingos

**Feature Branch**: `005-conformidade-constituicao`

**Created**: 2026-10-05

**Status**: Implementado (05/10/2026)

**Input**: User description: "Conformidade com a constituição 1.1.0 (pendências das revisões das specs 001 a 004): (1) quando o ONS republicar um arquivo bruto já baixado (Energia Vertida Turbinável, indicadores ou programação diária), preservar a versão anterior em vez de sobrescrever, registrando datas de publicação e de arquivamento; (2) o nível de log escolhido na linha de comando deve valer para todos os módulos do pipeline (coleta, filtragem, consolidação, indicadores, programação, tratamento, análise e PDF); (3) linhas com campos insuficientes nos CSVs de Energia Vertida Turbinável devem ser registradas em log e contadas na auditoria (hoje são descartadas sem registro; a varredura de 05/10/2026 não encontrou nenhuma em 42 arquivos e ~15 milhões de linhas); (4) requirements.txt somente com as dependências usadas (incluir numpy e seaborn, retirar requests); (5) todos os gráficos do relatório devem ser produzidos com seaborn, mantendo o conteúdo, a paleta e a legibilidade das 5 figuras atuais."

---

## Contexto

A emenda 1.1.0 da constituição (05/10/2026) tornou explícitas regras que o pipeline ainda não cumpre: preservar a versão anterior de arquivos brutos republicados pelo ONS (princípio V), aplicar o nível de log a todos os módulos (princípio V), registrar linhas com formato irregular (princípio IV), manter só dependências usadas e produzir qualquer gráfico com seaborn (Requisitos Técnicos 1 e 5). As revisões das specs 001 a 004 apontaram essas lacunas. Esta feature as fecha sem alterar nenhum número ou texto do relatório.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Versões anteriores de arquivos republicados pelo ONS (Priority: P1)

Como fiscal, quero que, quando o ONS republicar um arquivo que o pipeline já tinha baixado, a versão anterior seja guardada junto com sua data de publicação, para poder demonstrar com que dados cada relatório foi gerado e comparar versões caso um número mude entre execuções.

**Why this priority**: O ONS revisa arquivos já publicados (ex.: o arquivo de ago/2026 da base de EVT foi republicado em 30/09/2026). Sem a versão anterior, um relatório entregue à fiscalização não pode ser reproduzido.

**Independent Test**: Simular a republicação de um arquivo com conteúdo diferente e conferir que a versão anterior foi preservada e registrada, que a nova versão substituiu a corrente e que a extração usa apenas a versão corrente.

**Acceptance Scenarios**:

1. **Given** um arquivo bruto local registrado no manifesto com uma data de publicação, **When** o catálogo do ONS informa nova data de publicação e o arquivo baixado tem conteúdo diferente, **Then** a cópia local anterior é preservada na área de versões anteriores com nome que identifica o arquivo e a versão, e o manifesto registra a data de publicação e o tamanho da versão preservada e a data do arquivamento.
2. **Given** um arquivo republicado cujo conteúdo baixado é idêntico ao local, **When** a coleta é executada, **Then** nenhuma cópia é criada e só o registro de versão do manifesto é atualizado.
3. **Given** versões anteriores preservadas, **When** a extração e o processamento são executados, **Then** elas não são lidas e os resultados dependem apenas das versões correntes.
4. **Given** sucessivas republicações do mesmo arquivo, **When** a coleta é executada após cada uma, **Then** todas as versões anteriores permanecem preservadas, sem sobrescrever umas às outras.

---

### User Story 2 - Gráficos produzidos com seaborn (Priority: P1)

Como fiscal, quero que todos os gráficos do relatório sejam produzidos com seaborn, conforme a regra do projeto, mantendo o conteúdo, a paleta e a legibilidade das figuras atuais, para que o relatório siga o padrão visual definido sem perder nenhuma informação.

**Why this priority**: É regra explícita do usuário incorporada à constituição (Requisitos Técnicos, item 5); as 5 figuras atuais não a cumprem.

**Independent Test**: Gerar as 5 figuras com a base atual e conferir, figura a figura, que os mesmos elementos estão presentes (séries, faixas, linhas de referência, rótulos, legendas e anos parciais) e que os arquivos têm os mesmos nomes e a mesma resolução.

**Acceptance Scenarios**:

1. **Given** a base tratada, **When** as figuras são geradas, **Then** as 5 figuras são produzidas com seaborn, com os mesmos nomes de arquivo, resolução de 300 DPI e um tema visual único definido em um só lugar.
2. **Given** o relatório gerado antes e depois da mudança, **When** os textos e tabelas são comparados, **Then** são idênticos; só a forma de produzir as figuras muda.
3. **Given** cada figura nova, **When** comparada à anterior, **Then** contém os mesmos elementos informativos: série temporal com faixas de indisponibilidade e referências de potência e garantia física; EVT mensal empilhada com marco da mudança de classificação; perfil horário ano × hora de geração e EVT; disponibilidade e geração anuais com referências; vazões defluentes anuais empilhadas com engolimento máximo.

---

### User Story 3 - Nível de log único para todos os módulos (Priority: P2)

Como operador do pipeline, quero que o nível de log escolhido na linha de comando valha para todos os módulos executados naquela chamada, para poder silenciar mensagens informativas ou depurar um problema em qualquer etapa.

**Why this priority**: Facilita a operação e a auditoria, mas não altera resultados.

**Independent Test**: Executar cada ponto de entrada com nível de aviso e conferir que nenhuma mensagem informativa de nenhum módulo aparece; com nível de depuração, conferir que mensagens de depuração podem aparecer em qualquer módulo.

**Acceptance Scenarios**:

1. **Given** a coleta executada com nível de aviso, **When** coleta, filtragem, consolidação, indicadores e programação rodam, **Then** nenhuma mensagem informativa é emitida por nenhum desses módulos.
2. **Given** o tratamento ou a análise executados com um nível escolhido, **When** rodam, **Then** o nível vale para todos os módulos que eles usam (validação, indicadores, programação e PDF).
3. **Given** os módulos de indicadores e de programação executados isoladamente, **When** chamados com um nível de log, **Then** aceitam e aplicam esse nível.

---

### User Story 4 - Registro de linhas com formato irregular (Priority: P3)

Como fiscal, quero que linhas dos arquivos de Energia Vertida Turbinável com número de campos diferente do cabeçalho sejam contadas na auditoria e avisadas no log, para que nenhum registro seja descartado em silêncio.

**Why this priority**: A varredura de 05/10/2026 não encontrou nenhuma linha irregular em 42 arquivos (~15 milhões de linhas); a regra protege contra arquivos futuros.

**Independent Test**: Processar um arquivo com uma linha curta e uma linha longa e conferir a contagem na auditoria e o aviso no log; processar os arquivos atuais e conferir contagem zero.

**Acceptance Scenarios**:

1. **Given** um arquivo com linhas de número de campos diferente do cabeçalho, **When** a filtragem é executada, **Then** essas linhas não são extraídas, são contadas por arquivo na auditoria e o log informa o arquivo, a quantidade e o número das primeiras linhas.
2. **Given** os arquivos atuais, **When** a filtragem é executada, **Then** a contagem é zero e a base extraída é idêntica à anterior.

---

### User Story 5 - Lista de dependências fiel ao uso (Priority: P3)

Como mantenedor, quero que a lista de dependências contenha exatamente os pacotes usados pelo código e pelos testes, para que uma instalação limpa funcione e não traga pacotes sem uso.

**Why this priority**: Higiene e reprodutibilidade; sem efeito nos resultados.

**Independent Test**: Comparar a lista de dependências com os pacotes importados pelo código e pelos testes.

**Acceptance Scenarios**:

1. **Given** a lista de dependências atualizada, **When** comparada aos pacotes importados, **Then** todo pacote importado (de terceiros) está listado e todo pacote listado é importado; o pacote de requisições HTTP sem uso é retirado e numpy e seaborn constam.

---

### Edge Cases

- **Primeira execução sem manifesto**: a cópia local aceita pelo tamanho publicado não gera versão anterior (não há versão anterior conhecida).
- **Republicação com o mesmo tamanho**: a comparação usa a data de publicação registrada e o conteúdo, não apenas o tamanho.
- **Download forçado** (`--force-download`): se o conteúdo baixado for idêntico, nada é preservado; se diferir, a versão anterior é preservada.
- **Falha no download da nova versão**: a versão corrente permanece intacta e nenhuma versão é movida.
- **Nomes de versões preservadas**: duas versões do mesmo arquivo nunca colidem (o nome inclui a data de publicação da versão; se ausente, a data de arquivamento).
- **Nível de log inválido**: rejeitado pela linha de comando com mensagem de erro, sem execução parcial.
- **Linha vazia**: continua ignorada (não é linha irregular).
- **Elementos gráficos sem equivalente direto em seaborn** (linhas de referência, faixas, rótulos): são aplicados sobre os eixos produzidos pelo seaborn, mantendo o seaborn como produtor das marcas de dados.

---

## Requirements *(mandatory)*

### Functional Requirements

**US1 — Versões anteriores**

- **FR-001**: Antes de substituir um arquivo bruto por uma versão republicada pelo ONS com conteúdo diferente, o sistema DEVE preservar a cópia local anterior em uma área de versões anteriores da mesma pasta, com nome que identifique o arquivo e a versão.
- **FR-002**: O manifesto DEVE registrar, para cada versão preservada: nome do arquivo, data de publicação e tamanho da versão preservada, data e hora do arquivamento e local da cópia.
- **FR-003**: Se o conteúdo baixado for idêntico ao local, nenhuma versão DEVE ser criada.
- **FR-004**: Versões anteriores NÃO DEVEM ser lidas pela extração, pelo tratamento nem pela análise.
- **FR-005**: A regra DEVE valer para os três conjuntos coletados: Energia Vertida Turbinável, indicadores oficiais e programação diária.

**US2 — Gráficos com seaborn**

- **FR-006**: As 5 figuras do relatório DEVEM ser produzidas com seaborn, com tema, paleta e tipografia definidos em um único ponto, mantendo nomes de arquivo, resolução de 300 DPI e todos os elementos informativos listados na US2.
- **FR-007**: Textos e tabelas do relatório (PDF, Markdown e planilha) DEVEM permanecer idênticos aos da versão anterior.

**US3 — Nível de log**

- **FR-008**: O nível de log escolhido em cada ponto de entrada (coleta, tratamento, análise, indicadores e programação isolados) DEVE ser aplicado a todos os módulos executados naquela chamada.

**US4 — Linhas irregulares**

- **FR-009**: Na filtragem da base de EVT, linhas não vazias com número de campos diferente do cabeçalho DEVEM ser contadas por arquivo na auditoria, avisadas no log (arquivo, quantidade e número das primeiras linhas) e não extraídas.

**US5 — Dependências**

- **FR-010**: A lista de dependências DEVE conter exatamente os pacotes de terceiros importados pelo código e pelos testes, com versão mínima.

### Key Entities *(include if feature involves data)*

- **Versão preservada de arquivo bruto**: cópia de uma versão anterior de um arquivo do ONS, com arquivo de origem, data de publicação, tamanho, data de arquivamento e local.
- **Registro de auditoria de filtragem**: passa a incluir a contagem de linhas com formato irregular por arquivo.
- **Tema visual das figuras**: paleta, tipografia, resolução e estilo comuns às 5 figuras.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em teste de republicação, 100% das versões anteriores com conteúdo diferente ficam preservadas e registradas, e a base extraída é idêntica à obtida só com as versões correntes.
- **SC-002**: Com nível de aviso, 0 mensagens informativas são emitidas em qualquer ponto de entrada.
- **SC-003**: Em arquivo de teste com 1 linha curta e 1 longa, a auditoria registra 2 linhas irregulares; nos 42 arquivos atuais, 0, e a base extraída não muda.
- **SC-004**: 100% dos pacotes de terceiros importados estão na lista de dependências e 100% dos listados são importados.
- **SC-005**: As 5 figuras são geradas com os mesmos nomes e 300 DPI, e a comparação dos textos e tabelas do relatório antes e depois não mostra diferença.
- **SC-006**: A suíte de testes completa é aprovada sem acesso à rede e sem alterar arquivos do projeto.

---

## Assumptions

- A área de versões anteriores fica dentro de cada pasta de dados brutos, em subpasta própria, que os processos de leitura não percorrem.
- A comparação de conteúdo usa uma soma de verificação do arquivo; a data de publicação vem do catálogo do ONS.
- Os arquivos brutos atuais não serão baixados novamente nesta feature (a base de EVT é mantida como está, por decisão do usuário em 02/10/2026); a preservação de versões vale a partir das próximas coletas.
- seaborn produz as marcas de dados (linhas, barras, mapas de calor); anotações e linhas de referência são aplicadas sobre os mesmos eixos, pois seaborn é construído sobre matplotlib.
- A paleta atual (validada para acessibilidade) é mantida e passa a ser fornecida ao seaborn.
- seaborn e matplotlib já estão instalados no ambiente; nenhuma figura nova é criada nesta feature.
