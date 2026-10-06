# Feature Specification: Conferência com Outras Fontes do ONS e Programação Diária - UHE São Domingos

**Feature Branch**: `004-conferencia-outros`

**Created**: 2026-10-05

**Status**: Implementado (US1 em 05/10/2026; US2 e US3 em 02/10/2026, formalizadas nesta spec)

**Input**: User description: "Vamos criar a spec 004-conferencia-outros elencando o que já baixou e fez baixando mais dados e principalmente insira no pipeline esses dados 'Dados dos Valores da Programação Diária' pois isso é de extrema importância para concatenar com o que já sabemos. pode manter."

---

## Contexto

A base de Energia Vertida Turbinável (EVT, specs 001 a 003) mostra quanto a usina gerou, quanto declarou disponível e quanto verteu de água que poderia ter sido turbinada, mas não diz **por que** a usina deixou de gerar. Em 02/10/2026, por solicitação direta (sem spec), foram conferidas outras fontes abertas do ONS e incluídos no pipeline os indicadores oficiais de disponibilidade por unidade geradora. Na mesma data, uma consulta exploratória mostrou que, de out/2024 a set/2026, em 91% das horas em que a usina ficou parada com vertimento turbinável a programação diária do ONS previa geração zero. Esta spec registra o que já foi feito (US2 e US3) e especifica a inclusão da programação diária no pipeline (US1).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operação verificada × programação diária do ONS (Priority: P1)

Como fiscal da AGEMS, quero saber, hora a hora, se a UHE São Domingos gerou o que o ONS programou para ela, para separar as paradas com vertimento turbinável que seguiram a programação do ONS das paradas que contrariaram a programação, e assim levar à fiscalização perguntas dirigidas ao responsável certo (agente ou ONS).

**Why this priority**: É o único dado aberto que aproxima a causa do vertimento turbinável com a usina disponível, o principal achado da análise de 2025–2026. Sem ele, o relatório só descreve o fenômeno; com ele, indica quem decidiu a parada.

**Independent Test**: Com os arquivos diários de programação já obtidos e a base de EVT existente, gerar a tabela mensal de horas paradas com EVT classificadas pela programação e conferir que a soma das classes é igual ao total de horas paradas com EVT no período comum.

**Acceptance Scenarios**:

1. **Given** o catálogo do ONS com um arquivo de programação por dia, **When** a coleta é executada, **Then** todos os arquivos diários que se sobrepõem ao período da base de EVT são obtidos (ou reaproveitados, se a versão local for a publicada), a usina é extraída com 48 patamares de 30 minutos por dia e os dias ausentes no portal são listados.
2. **Given** a programação horária e a base de EVT, **When** as duas são cruzadas nas horas comuns, **Then** cada hora é classificada (parada com EVT e programação zero; parada com EVT e programação positiva; parada sem EVT; gerando com programação; gerando sem programação) e os totais mensais de horas e de EVT por classe são calculados.
3. **Given** horas em que a usina ficou parada enquanto a programação previa geração acima do limiar de desvio, **When** a análise é executada, **Then** essas horas são agrupadas em eventos com início, fim, duração, programação média e EVT, listados por completo na planilha e os maiores no relatório.
4. **Given** os resultados do cruzamento, **When** o relatório é gerado, **Then** ele traz uma constatação e uma seção sobre a programação diária, com todos os números calculados a partir dos dados e com as ressalvas de que a programação diária não registra reprogramações em tempo real nem o motivo da programação.

---

### User Story 2 - Indicadores oficiais de disponibilidade por unidade geradora (Priority: P2) — *implementada em 02/10/2026*

Como fiscal, quero os indicadores de disponibilidade apurados pelo próprio ONS (DISPF, INDISPPF, INDISPFF, TEIFa, TEIP e horas por estado operativo de cada unidade geradora), no mesmo período da base de EVT, para comparar a disponibilidade da usina com a referência da garantia física usando os índices regulatórios em vez de aproximações.

**Why this priority**: Corrige a leitura de disponibilidade do relatório (a disponibilidade declarada não é o indicador regulatório) e identifica por unidade geradora a origem da TEIFa acima da referência.

**Independent Test**: Recalcular a TEIFa e a TEIP publicadas a partir das horas por estado operativo e conferir que coincidem em todos os meses com janela de 60 meses completa.

**Acceptance Scenarios**:

1. **Given** os quatro conjuntos de indicadores do ONS, **When** a coleta é executada, **Then** a usina é extraída pelo CEG, a versão mais recente de cada valor é mantida e os dados são recortados no período da base de EVT.
2. **Given** as horas por estado operativo, **When** a validação é executada, **Then** em cada mês-unidade as horas das parcelas somam as horas do período, e a TEIFa e a TEIP recalculadas reproduzem as publicadas.
3. **Given** o indicador DISPF e as horas usadas no TEIP, **When** os dois são comparados, **Then** os meses-unidade em que divergem em mais de 1 h são listados.
4. **Given** os indicadores, **When** o relatório é gerado, **Then** ele traz duas constatações e uma seção com disponibilidade por ano (declarada × DISPF), indicadores anuais por unidade, horas por estado, decomposição da TEIFa/TEIP e divergências.

---

### User Story 3 - Registro das conferências com outras fontes (Priority: P3) — *realizada em 02/10/2026*

Como fiscal, quero um registro de quais fontes abertas foram consultadas, o que cada uma confirmou ou não e quais foram descartadas, para sustentar no relatório de fiscalização a confiabilidade dos dados e saber o que precisa ser pedido diretamente ao agente.

**Why this priority**: Dá rastreabilidade às conclusões, mas não altera os resultados do pipeline.

**Independent Test**: Conferir que o registro de pesquisa da feature lista cada fonte consultada com período, resultado da conferência e decisão (incluída, apenas consultada ou descartada).

**Acceptance Scenarios**:

1. **Given** as conferências feitas, **When** o registro é consultado, **Then** ele informa, para cada fonte, o resultado (ex.: "base local idêntica ao portal do ONS em todos os meses de ago/2018 a ago/2026").
2. **Given** a ausência de base pública com eventos individuais de desligamento de geração, **When** o registro é consultado, **Then** ele indica essa lacuna e o que deve ser solicitado ao agente.

---

### Edge Cases

- **Dias sem arquivo no portal**: há 20 dias sem arquivo entre 01/10/2024 e 02/10/2026; as horas desses dias ficam sem classificação e os dias são listados, sem interpolação.
- **Formato de data inconsistente**: a data interna dos arquivos aparece como `AAAA-MM-DD` em uns e `DD/MM/AAAA` em outros; a data do dia vem do nome do arquivo e a data interna é apenas conferida.
- **Dia incompleto**: arquivo com número de patamares diferente de 48 para a usina é registrado na auditoria e suas horas incompletas não são classificadas.
- **Campos sem preenchimento para hidráulicas**: disponibilidade programada, ordem de mérito, inflexibilidade e razão elétrica vêm vazios ou zerados para a usina; a análise não pode inferir o motivo da programação a partir deles.
- **Revisão de arquivos já publicados**: um arquivo republicado pelo ONS (versão diferente) é obtido novamente; os demais são reaproveitados.
- **Períodos sem sobreposição**: a programação começa em 01/10/2024 e avança além do fim da base de EVT; só as horas comuns às duas fontes são cruzadas.
- **Ausência do código da usina em algum dia**: o dia é listado na auditoria como sem registro da usina.

---

## Requirements *(mandatory)*

### Functional Requirements

**US1 — Programação diária (a implementar)**

- **FR-001**: O sistema DEVE obter do catálogo do ONS ("Dados dos Valores da Programação Diária") todos os arquivos diários publicados cujo dia esteja dentro do período da base de EVT, reaproveitando cópias locais que correspondam à versão publicada e preservando os arquivos brutos para auditoria.
- **FR-002**: O sistema DEVE extrair apenas as linhas da usina, identificada pelo código de exibição do ONS e conferida pelo nome e pelo estado, e registrar por arquivo: linhas lidas, linhas da usina, patamares distintos e situação (processado, sem registros, incompleto ou falha).
- **FR-003**: O sistema DEVE tomar a data do dia a partir do nome do arquivo, conferir a data interna aceitando os dois formatos publicados e registrar qualquer divergência.
- **FR-004**: O sistema DEVE converter os 48 patamares de 30 minutos em valores horários (média dos dois patamares de cada hora), alinhados à convenção da base de EVT (hora de início do intervalo).
- **FR-005**: O sistema DEVE listar os dias do período sem arquivo publicado e os dias com patamares incompletos.
- **FR-006**: O sistema DEVE cruzar a programação horária com a base de EVT nas horas comuns e classificar cada hora em: parada com EVT e programação zero; parada com EVT e programação positiva; parada sem EVT; gerando; gerando com programação zero. Usina parada usa o mesmo limiar da spec 003 (geração até 1 MW) e programação zero usa o mesmo limiar.
- **FR-007**: O sistema DEVE calcular, por mês e no período comum: horas e EVT por classe; percentual das horas paradas com EVT em que a programação era zero; percentual da EVT do período ocorrida nessas horas; disponibilidade declarada média nessas horas; distribuição dessas horas por hora do dia; correlação horária entre geração verificada e programada; desvio médio absoluto.
- **FR-008**: O sistema DEVE agrupar em eventos (horas consecutivas) as horas em que a usina ficou parada com programação acima do limiar de desvio, informando início, fim, duração, programação média, disponibilidade declarada média e EVT.
- **FR-009**: O relatório (PDF e Markdown) e a planilha DEVEM incluir uma constatação e uma seção sobre a programação diária, com números e frases gerados a partir dos dados, e as ressalvas: (a) a programação diária é o planejamento do dia e não registra reprogramações em tempo real; (b) o conjunto não informa o motivo da programação para usinas hidráulicas.
- **FR-010**: A etapa DEVE poder ser executada dentro do pipeline de coleta e também isoladamente, sem alterar a base de EVT existente, respeitando as pastas de dados configuradas e sem acesso à rede nos testes automatizados.

**US2 — Indicadores oficiais (implementado em 02/10/2026)**

- **FR-011**: O sistema DEVE obter os conjuntos "Indicadores de Desempenho das Funções Geração por Unidade Geradora" (bases mensal e anual), "Taxas TEIFa e TEIP" e "Taxas TEIFa E TEIP - Parâmetros", filtrar a usina pelo CEG, manter a versão mais recente de cada valor e recortar no período da base de EVT.
- **FR-012**: O sistema DEVE validar a identidade das horas por estado operativo (horas do período = soma das parcelas), recalcular a TEIFa e a TEIP em janela de 60 meses e listar as divergências entre o DISPF e as horas do TEIP.
- **FR-013**: O relatório DEVE trazer disponibilidade por ano (declarada × DISPF), indicadores anuais por unidade, horas por estado, decomposição da TEIFa e da TEIP mais recentes por unidade e parcela, e divergências, além de duas constatações.

**US3 — Registro das conferências (realizado em 02/10/2026)**

- **FR-014**: A feature DEVE manter registro das fontes consultadas, com período, resultado e decisão de uso, incluindo as que não trazem o dado procurado (eventos individuais de desligamento com motivo).

### Key Entities *(include if feature involves data)*

- **Programação diária da usina**: valor de geração programada para cada patamar de 30 minutos de cada dia, com a origem (arquivo e versão).
- **Programação horária**: média dos dois patamares de cada hora, na convenção de hora de início.
- **Classificação horária**: para cada hora comum, situação da usina (parada ou gerando), presença de EVT e programação, com a classe resultante.
- **Evento de desvio da programação**: sequência de horas consecutivas com a usina parada e programação acima do limiar.
- **Auditoria de arquivos de programação**: por arquivo, linhas lidas, linhas da usina, patamares e situação; lista de dias ausentes.
- **Indicadores oficiais por unidade geradora** (US2): DISPF, INDISPPF, INDISPFF, DMDFF (mensal e anual), horas por estado operativo, TEIFa e TEIP, recálculo, decomposição e divergências.
- **Registro de conferências** (US3): fonte, período, resultado, decisão.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos dias do período comum têm a programação obtida ou aparecem na lista de dias ausentes; 100% dos dias obtidos têm 48 patamares ou estão marcados como incompletos.
- **SC-002**: 100% das horas em que a usina ficou parada com EVT no período comum recebem uma classe; a soma das classes é igual ao total de horas paradas com EVT.
- **SC-003**: Uma segunda execução sem mudança no portal não obtém nenhum arquivo de novo.
- **SC-004**: Os números citados na constatação e na seção do relatório são idênticos aos da planilha.
- **SC-005**: A etapa de programação completa leitura, cruzamento e exportação em menos de 2 minutos com os arquivos já obtidos.
- **SC-006**: A base de EVT e as saídas das specs 001 a 003 permanecem idênticas antes e depois da execução da etapa.
- **SC-007** (US2): A TEIFa e a TEIP recalculadas coincidem com as publicadas em 100% dos meses com janela completa (diferença inferior a 0,001 p.p.).

---

## Assumptions

- A programação diária publicada é o melhor registro público do que o ONS previa para a usina; reprogramações e ordens em tempo real do centro de operação não são públicas e ficam fora do escopo.
- O código de exibição da usina na programação é `PRUHSD` (verificado em todos os arquivos de out/2024 a out/2026); outras usinas "São Domingos" (MG, GO, SC e térmica em SP) são excluídas pelo código e pelo estado.
- Limiares: usina parada e programação zero = até 1 MW (o mesmo da spec 003); desvio relevante = programação acima de 5 MW com a usina parada. São parâmetros de análise, abertos à revisão do usuário.
- O ONS publica cada dia em três formatos; usa-se o mais compacto (cerca de 150 KB por dia, contra 37 MB do CSV).
- A base de EVT é mantida como está (decisão do usuário em 02/10/2026); a programação é recortada no período dessa base.
- O conjunto de classificação de EVT do SIN (razão energética × elétrica) é agregado para o sistema, sem usina, e tem lacunas; fica fora do pipeline e apenas registrado em US3.
- Os indicadores oficiais (US2) e o registro de conferências (US3) já foram entregues em 02/10/2026; esta spec os formaliza sem alterar o comportamento.

## Histórico de revisões

### 2026-10-05 — spec 006 (dicionários e cópia de segurança)

- Os indicadores oficiais e a programação diária passam a ser gravados por `src/persistencia.py`, com `<arquivo>.bak` da versão anterior; a planilha dos indicadores leva a assinatura dos dados.
- Quando baixam dados, as duas etapas obtêm também os dicionários de dados (PDF e JSON) dos seus conjuntos.
- Os leitores das tabelas tratadas passaram a aceitar tabela gravada sem colunas (ex.: nenhuma divergência).
- A disponibilidade horária (spec 006, US3) usa as classes horárias desta spec para classificar as horas paradas por sincronização.
