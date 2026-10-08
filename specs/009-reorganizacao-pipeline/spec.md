# Feature Specification: Reorganização do Projeto num Fluxo de Cinco Etapas, Reutilizável para Outras Usinas Hidrelétricas

**Feature Branch**: `009-reorganizacao-pipeline`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "Agora precisamos arrumar esse projeto, como eu não sabia exatamente como pedir a spec anteriormente, a constitution, specs e pipeline tem "remendos", vamos organizar para que tudo que precisou fazer para gerar esse relatorio_analise_estatistica.pdf tenha um fluxo mais limpo e lógico. Além disso, ficou tão bom esse projeto que quero usar essa mesma lógica para fazer análises com outras usinas hidrelétricas. - Sobre a constitution, sabendo tudo que sabe agora, melhore ela e não deixe emendas mais, tem que ser um arquivo simples mas que contemple tudo para que gere exatamente esse relatório final. - Os backups são importantes, mas não dá pra ficar com tantos, deve ter no MÁXIMO 2 versões backups sempre, então se criar um backup do projeto, excluir o antigo. No nosso caso pode excluir o 10-06 pra trás. - o pipeline deve seguir a lógica "Coleta de dados" --> "Tratamento de dados" --> "conferência" --> "análises" --> "geração de relatório". Ou seja, as specs que existem hoje precisam ser aglutinadas para seguir a mesma lógica do pipeline. Lembrando que no momento as bases de dados desse relatório final está excelente, então não tem mais o que adicionar. - Excluir arquivos que não servem para nada mais, que só ocupam espaço no projeto."

## Contexto

O relatório da UHE São Domingos aprovado em 07/10/2026 (`reports/relatorio_analise_estatistica.pdf`, 29 páginas) é a referência deste trabalho: o conteúdo dele não muda. O que muda é o caminho até ele, que cresceu por acréscimos.

**Specs**
- São oito specs, e várias revisam outras:
  - a 005 e a 006 revisam as anteriores;
  - a 007 revisa a 003;
  - a 008 revisa a 003, a 006 e a 007, e tem duas revisões próprias.
- Para saber como uma parte funciona hoje, é preciso ler várias delas, na ordem.

**Constituição**
- Está na versão 1.2.0.
- Tem três emendas registradas no próprio arquivo.
- Tem regras escritas só para a São Domingos: identificadores, potência e homônimos.

**Fluxo**
- São três comandos principais, além de módulos que também rodam sozinhos.
- Há cerca de vinte opções do tipo "só esta base" ou "sem esta base".
- As conferências entre fontes ficam espalhadas entre a extração das bases e as análises.

**Cópias e arquivos**
- Doze cópias datadas do projeto, com cerca de 120 MB.
- Cerca de cinquenta arquivos `.bak` soltos.
- A versão de 30/09/2026 dos relatórios.
- Arquivos que o fluxo não usa.

O fluxo passa a ter cinco etapas, cada uma com a sua spec:

| Etapa | O que faz | De onde vem hoje |
|---|---|---|
| 1. Coleta de dados | varre o portal do ONS, baixa e versiona os arquivos e os dicionários de dados, extrai a usina | spec 001; coleta das specs 004, 005 e 006 |
| 2. Tratamento de dados | padroniza, valida (consistência e plausibilidade), alinha os horários e grava os dados tratados | spec 002; tratamento das bases da spec 006 |
| 3. Conferência | confere as bases entre si e refaz os indicadores oficiais | spec 004 (DISPF × horas; TEIFa e TEIP); spec 006 (geração, disponibilidade, vazões, cadastro); spec 007 (resultados citados nas legendas) |
| 4. Análises | calcula indicadores, eventos, perfis, constatações e os dados de cada tabela e figura | spec 003; análises das specs 004 e 006 |
| 5. Geração do relatório | produz as figuras, o PDF, o Markdown e a planilha | relatório da spec 003; specs 007 e 008 |

Além disso, a mesma lógica passa a valer para outras usinas hidrelétricas: tudo o que é próprio de uma usina fica num **perfil da usina**, e a São Domingos é a primeira.

**Conclusão do relatório** (pedido do usuário em 07/10/2026, depois do plano):
- O relatório ganha uma seção de conclusão sucinta, com quatro partes:
  - pontos de atenção;
  - possíveis problemas, inclusive o indício de problema numa unidade geradora;
  - o que confirmar com o agente;
  - o que verificar em campo.
- É a única mudança de conteúdo desta spec (US6).
- Entra antes da reorganização, para constar do relatório usado na fiscalização. Depois de aprovada pelo usuário, passa a fazer parte do relatório de referência da não regressão.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar o relatório por um fluxo de cinco etapas (Priority: P1)

Como fiscal da AGEMS, quero gerar o relatório por um fluxo único, em que cada etapa parte só do resultado das anteriores:

Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório.

Assim entendo e audito o caminho de cada número, e executo de novo só a etapa necessária.

**Why this priority**: É a base do pedido; as demais histórias dependem do fluxo organizado.

**Independent Test**: Executar as cinco etapas para a São Domingos com os dados já baixados, sem novidade no portal, e comparar o relatório com o aprovado em 07/10/2026.

**Acceptance Scenarios**:

1. **Given** os dados brutos já baixados, **When** o fluxo completo é executado sem novidade no portal, **Then** nenhum arquivo é baixado de novo e o relatório tem o mesmo conteúdo do aprovado, exceto a data de geração (PDF, Markdown, planilha e figuras).
2. **Given** os resultados das etapas anteriores, **When** uma etapa é executada sozinha, **Then** ela usa só esses resultados e não refaz o trabalho das outras.
3. **Given** uma etapa sem os resultados das anteriores, **When** é executada, **Then** para sem gravar nada e indica qual etapa executar antes.
4. **Given** a etapa de conferência, **When** executada, **Then** todas as conferências entre fontes ficam nela, com os resultados registrados; as análises e o relatório só leem esses resultados.

---

### User Story 2 - Constituição e specs limpas, na ordem do fluxo (Priority: P1)

Como fiscal, quero uma constituição simples e definitiva e uma spec por etapa, cada uma descrevendo como a etapa funciona hoje, sem emendas e sem remissões a revisões. Assim qualquer pessoa entende o projeto lendo seis documentos, na ordem do fluxo.

**Why this priority**: É o outro núcleo do pedido; sem ele os remendos continuam, e cada mudança futura cria outros.

**Independent Test**: Ler a constituição e as cinco specs e conferir, pelo mapeamento das specs antigas, que todo requisito em vigor está numa spec nova e que nenhuma delas remete a emendas ou revisões.

**Acceptance Scenarios**:

1. **Given** a constituição, **When** lida, **Then**:
   - é um documento único, sem histórico de emendas nem relatório de impacto;
   - não tem valores de uma usina específica;
   - cobre tudo o que é necessário para gerar o relatório aprovado.
2. **Given** a pasta de specs, **When** listada, **Then** tem exatamente cinco specs, uma por etapa, numeradas na ordem do fluxo.
3. **Given** cada requisito em vigor das oito specs atuais, **When** a consolidação termina, **Then** ele está em exatamente uma spec de etapa ou está marcado no mapeamento como superado, com o motivo.
4. **Given** um pedido de mudança futuro, **When** a governança é seguida, **Then** a mudança atualiza a spec da etapa afetada, em vez de criar uma spec que remenda outras.

---

### User Story 3 - Usar a mesma lógica com outras usinas hidrelétricas (Priority: P2)

Como fiscal, quero analisar outras usinas hidrelétricas com a mesma lógica, informando só o perfil da usina. O perfil traz os identificadores dela em cada conjunto do ONS e os parâmetros técnicos, com a fonte. O relatório sai com a mesma estrutura e o mesmo rigor.

**Why this priority**: Amplia o uso do projeto, mas depende do fluxo organizado (US1) e não muda o relatório da São Domingos.

**Independent Test**:
- Executar o fluxo com o perfil de uma usina fictícia, sobre dados de teste, e conferir o relatório gerado.
- Executar com um perfil incompleto e conferir a recusa.

**Acceptance Scenarios**:

1. **Given** o perfil da São Domingos, **When** o fluxo é executado, **Then** o relatório é o aprovado (US1).
2. **Given** o perfil de outra usina, **When** o fluxo é executado, **Then**:
   - só os registros dessa usina são extraídos, com os homônimos excluídos;
   - o relatório tem a mesma estrutura, com o nome, a identificação, os parâmetros e os textos dela;
   - nada no relatório menciona a São Domingos.
3. **Given** um perfil sem algum campo obrigatório, **When** o fluxo começa, **Then** para antes da coleta e lista os campos faltantes.
4. **Given** uma usina com outro número de unidades geradoras, ou sem algum conjunto (por exemplo, sem dados hidrológicos ou sem programação diária), **When** o fluxo é executado, **Then** as análises se ajustam ao perfil e as seções sem dados são omitidas, como já acontece hoje.
5. **Given** duas usinas analisadas, **When** os resultados são gravados, **Then**:
   - os dados brutos baixados uma vez servem às duas;
   - os dados tratados, os resultados e os relatórios de cada uma ficam separados, sem sobrescrever os da outra.

---

### User Story 4 - No máximo duas cópias de segurança (Priority: P2)

Como fiscal, quero no máximo duas cópias de segurança do projeto, sempre as mais recentes. Assim preservo as versões aprovadas sem acumular cópias.

**Why this priority**: É pedido explícito do usuário; libera espaço e evita confusão entre versões.

**Independent Test**: Criar uma cópia de segurança quando já existem duas e conferir que a mais antiga só foi excluída depois de a nova estar completa e conferida.

**Acceptance Scenarios**:

1. **Given** a situação atual, **When** a reorganização começa, **Then** as cópias datadas de 06/10/2026 ou antes são excluídas.
2. **Given** duas cópias existentes, **When** uma nova é criada e conferida, **Then** a mais antiga é excluída e ficam duas.
3. **Given** uma falha ao criar a nova cópia, **When** a criação é interrompida, **Then** nenhuma cópia existente é excluída.
4. **Given** os arquivos `.bak` soltos de código, testes, specs, README e dependências, **When** a limpeza termina, **Then** não resta nenhum; nos dados tratados, cada arquivo mantém só a cópia da versão imediatamente anterior.

---

### User Story 5 - Pasta do projeto só com o que é usado (Priority: P3)

Como fiscal, quero que a pasta do projeto tenha só o que o fluxo usa e o que eu preciso consultar, organizado. Assim encontro as coisas rápido e não ocupo espaço à toa.

**Why this priority**: Melhora a manutenção, mas não afeta o relatório.

**Independent Test**: Conferir a pasta, depois da limpeza, contra o inventário aprovado.

**Acceptance Scenarios**:

1. **Given** os arquivos que o fluxo, os testes, as specs, a constituição e o relatório não usam, **When** o inventário é apresentado, **Then** cada item traz a ação proposta (excluir, mover ou manter) e o motivo, e nada é excluído antes da aprovação.
2. **Given** o inventário aprovado, **When** aplicado, **Then** saem a versão de 30/09/2026 dos relatórios, os caches de execução e os arquivos duplicados ou legados aprovados.
3. **Given** os documentos de referência do usuário (ofício, relatórios de fiscalização, resoluções e documentos da usina), **When** a limpeza é aplicada, **Then** eles só saem com aprovação explícita; os mantidos ficam numa pasta de documentos de referência da usina.
4. **Given** os dados brutos e os dados tratados usados pelo relatório, **When** a limpeza é aplicada, **Then** nenhum deles é excluído.

---

### User Story 6 - Conclusão sucinta, com indícios e verificações para a fiscalização (Priority: P1)

Como fiscal, quero que o relatório termine com uma conclusão sucinta, tirada de todos os dados, com quatro partes:
- os pontos de atenção;
- os possíveis problemas, inclusive o indício de problema numa unidade geradora específica;
- o que convém confirmar com o agente;
- o que verificar em campo, se possível.

Assim levo para a fiscalização presencial uma lista objetiva do que perguntar e do que conferir.

**Why this priority**: É pedido explícito do usuário e serve à fiscalização de 14 a 16/10/2026. Por isso é implementada antes da reorganização.

**Independent Test**: Gerar o relatório da São Domingos e conferir:
- a seção de conclusão tem as quatro listas, cabe numa página e cada item remete à seção de origem;
- o indício na unidade geradora aparece com os números que o sustentam.

**Acceptance Scenarios**:

1. **Given** o relatório gerado, **When** a conclusão é lida, **Then**:
   - está entre a última seção de análise e as notas metodológicas, no PDF e no Markdown, e consta do sumário;
   - tem as quatro listas, nesta ordem, com no máximo cinco itens cada, de uma frase;
   - cada item traz o número que o sustenta e a seção de origem.
2. **Given** uma unidade geradora que concentra a taxa de indisponibilidade forçada, ou que registra limitação forçada de potência na maioria dos meses, **When** a conclusão é gerada, **Then** ela nomeia a unidade como possível problema, com os números, e inclui o que confirmar com o agente e o que verificar em campo sobre ela.
3. **Given** os itens da conclusão, **When** comparados com os critérios, **Then**:
   - cada um vem de uma regra do catálogo (FR-038), aplicada aos resultados das análises e das conferências;
   - nenhum afirma causa nem avalia o desempenho da usina.
4. **Given** uma regra cujas condições não são atendidas, ou cuja base não existe para a usina, **When** a conclusão é gerada, **Then** o item dela não aparece.
5. **Given** a conclusão e as constatações, **When** comparadas, **Then** a conclusão não repete o texto das constatações: resume em uma frase e remete à seção.

---

### Edge Cases

- **Etapa sem os resultados das anteriores**: para sem gravar nada e indica a etapa a executar antes (US1).
- **ONS republica um arquivo entre duas execuções**:
  - a coleta preserva a versão anterior, até o limite da FR-030;
  - as etapas seguintes refazem o que depende do arquivo;
  - a mudança no relatório é esperada e não conta como regressão.
- **Arquivos do portal sem registros da usina** (2015 a 2017, no caso da São Domingos): continuam guardados, porque servem a outras usinas, e continuam citados na cobertura.
- **Homônimos e troca de agente**:
  - a extração usa o identificador e o campo de conferência do perfil, nunca o nome do agente;
  - as linhas em que só um dos dois confere vão para a auditoria, como hoje.
- **Usina sem algum conjunto do ONS**: a seção e as legendas que dependem dele ficam fora do relatório, e a conferência correspondente fica registrada como não aplicável.
- **Fenômenos próprios de uma usina** (como a mudança de classificação do vertimento pelo ONS em dez/2022, na São Domingos): continuam detectados nos dados; se não ocorrem em outra usina, a constatação não aparece no relatório dela.
- **Parâmetros técnicos que o ONS não publica** (garantia física, IP e TEIF de referência, engolimento, tipo de turbina):
  - vêm do perfil, com a fonte e a data;
  - sem eles, o perfil é recusado.
- **Falha no meio da reorganização**: o estado aprovado é recuperável pela cópia de segurança e pelo controle de versões do projeto.
- **Limpeza diante das cópias mais recentes**: as duas cópias de segurança mais recentes nunca são excluídas pela limpeza.
- **Conclusão sem nenhuma regra disparada**: a seção continua no relatório, com uma frase dizendo que os dados não indicaram pontos de atenção pelos critérios do catálogo.
- **Mais de cinco itens numa lista**: ficam os cinco primeiros na ordem do catálogo, e a lista completa fica na aba CONCLUSAO da planilha.
- **Base ausente para a usina** (sem indicadores por unidade, sem programação ou sem dados hidrológicos): as regras que dependem dela não disparam, e os itens delas não aparecem.

---

## Requirements *(mandatory)*

### Functional Requirements

**Fluxo de cinco etapas (US1)**

- **FR-001**: O projeto DEVE ter um único fluxo, com cinco etapas nesta ordem: Coleta de dados, Tratamento de dados, Conferência, Análises e Geração do relatório.
- **FR-002**: Cada etapa DEVE usar só os resultados gravados pelas etapas anteriores e gravar os seus para as seguintes. Nenhuma etapa refaz o trabalho de outra, e só a coleta acessa o portal do ONS.
- **FR-003**: O usuário DEVE poder executar, para uma usina, o fluxo completo de uma vez ou cada etapa isoladamente. Uma etapa sem os resultados das anteriores DEVE parar sem gravar nada e indicar a etapa a executar antes.
- **FR-004**: A **Coleta de dados** DEVE fazer o que hoje fazem a coleta e a extração das dez bases do ONS, sem baixar de novo o que não mudou no portal:
  - varrer todos os arquivos publicados de cada conjunto no período;
  - registrar as versões dos arquivos;
  - obter os dicionários de dados;
  - extrair a usina pelos identificadores do perfil, com conferência;
  - auditar as linhas irregulares e as que conferem só em parte.
- **FR-005**: O **Tratamento de dados** DEVE:
  - padronizar as bases;
  - aplicar as regras de consistência e de plausibilidade, sinalizando os registros sem excluí-los;
  - alinhar os horários entre as bases;
  - gravar os dados tratados com cópia da versão anterior e conferência da gravação.
- **FR-006**: A **Conferência** DEVE reunir todas as conferências entre fontes que o projeto faz hoje e registrar o resultado de cada uma: período e quantidade comparados, coincidências, divergências e tolerância. As conferências são:
  - geração × Geração por usina;
  - disponibilidade declarada × Disponibilidade por usina;
  - vazões turbinada e vertida × Dados hidrológicos horários;
  - DISPF × horas por estado operativo;
  - TEIFa e TEIP recalculadas × publicadas;
  - ficha do cadastro × parâmetros do perfil.
- **FR-007**: As **Análises** DEVEM calcular indicadores, eventos, perfis, constatações e os dados de cada tabela e figura só a partir dos dados tratados e dos resultados da conferência.
- **FR-008**: A **Geração do relatório** DEVE produzir as figuras, o PDF, o Markdown e a planilha só a partir dos resultados das análises e da conferência, com a estrutura aprovada:
  - capa com identificação, cadastro, parâmetros, indicadores e sumário;
  - constatações no início de cada seção;
  - legendas de fonte e de conferência;
  - rodapé só com a numeração;
  - figuras padronizadas.
- **FR-009**: Os pontos de entrada e as opções de hoje que não se encaixam no fluxo (comandos separados por base, opções "só esta base" e "sem esta base") DEVEM ser substituídos pelas etapas. As opções que continuarem existindo e os códigos de saída de cada etapa DEVEM estar documentados na spec da etapa e no README.

**Não regressão (US1)**

- **FR-010**: Com o perfil da São Domingos e os dados já existentes, o fluxo reorganizado DEVE gerar o relatório de referência (PDF, Markdown, planilha e figuras) com o mesmo conteúdo, exceto a data de geração. O relatório de referência é o aprovado em 07/10/2026 acrescido da conclusão (US6), depois de aprovada pelo usuário e antes da reorganização.
- **FR-011**: A reorganização NÃO DEVE baixar de novo nem alterar os dados brutos. Os dados tratados regenerados a partir deles DEVEM coincidir com os atuais.
- **FR-012**: Todo comportamento coberto hoje pelos testes automatizados DEVE continuar coberto, com os testes organizados pelas etapas e executados sem rede.

**Constituição (US2)**

- **FR-013**: A constituição DEVE ser reescrita como documento único e simples, sem histórico de emendas nem relatório de impacto, organizada por princípios e pelas etapas do fluxo. Ela DEVE cobrir tudo o que é necessário para gerar o relatório aprovado:
  - fontes e identificação da usina em cada conjunto;
  - varredura completa e versões dos arquivos;
  - dicionários de dados;
  - regras de qualidade dos dados;
  - conferências entre fontes;
  - relatório só com números e textos gerados dos dados, com constatações e sem parecer;
  - conclusão gerada por regras declaradas, com indícios, confirmações e verificações e sem afirmar causa;
  - fonte de cada figura e tabela;
  - estrutura do relatório e padrão das figuras;
  - ambiente de execução e testes sem rede;
  - cópias de segurança;
  - governança das specs.
- **FR-014**: A constituição DEVE deixar de restringir o projeto à São Domingos. Ela DEVE exigir que cada execução trate de uma única usina, definida pelo seu perfil, com exclusão dos homônimos. Os valores da São Domingos passam para o perfil dessa usina.
- **FR-015**: A governança DEVE determinar que uma mudança futura atualize a spec da etapa afetada, e a constituição quando for o caso, sem criar specs que remendem outras. O histórico das mudanças fica no controle de versões do projeto.

**Specs por etapa (US2)**

- **FR-016**: As oito specs atuais DEVEM ser consolidadas em cinco, uma por etapa, numeradas na ordem do fluxo. Cada uma DEVE descrever o funcionamento atual completo da etapa:
  - objetivo;
  - entradas e saídas;
  - requisitos e critérios de aceitação;
  - decisões já tomadas pelo usuário.
- **FR-017**: Cada requisito em vigor nas specs atuais DEVE estar em exatamente uma spec de etapa. Requisitos superados, como o rodapé com a quantidade de conjuntos ou a seção própria do cadastro, NÃO DEVEM ser levados. Um mapeamento das specs antigas para as novas DEVE ser apresentado ao usuário antes de as antigas saírem.
- **FR-018**: As decisões do usuário registradas nas specs atuais DEVEM ser preservadas na spec da etapa ou no perfil da usina, entre elas:
  - conferências manuais com CCEE e ANEEL fora do relatório;
  - garantia física de 36,4 MWmed;
  - modelo de RF de 2026 não citado como fonte;
  - notas enxutas;
  - ficha do cadastro na capa, sem a data da consulta;
  - figuras padronizadas;
  - base de EVT mantida sem novo download.
- **FR-019**: Ao final, depois da aprovação do usuário, as specs antigas e esta spec de reorganização DEVEM sair da pasta de specs. Os registros de execução das specs antigas não são levados para as novas; tudo continua no histórico de versões do projeto.

**Perfil da usina (US3)**

- **FR-020**: Todo valor próprio de uma usina DEVE estar no perfil da usina, separado das regras gerais. O perfil reúne:
  - nome e estado;
  - identificador de extração e campo de conferência em cada conjunto do ONS;
  - códigos do reservatório e da programação;
  - parâmetros técnicos (potência e unidades geradoras, tipo de turbina, engolimento, garantia física, IP e TEIF de referência, vazão remanescente), cada um com a fonte e a data;
  - limiares das análises que dependem da usina.
- **FR-021**: O fluxo DEVE receber o perfil da usina como entrada. Com o perfil da São Domingos, o resultado é o da FR-010.
- **FR-022**: Um perfil incompleto ou inconsistente DEVE ser recusado antes da coleta, com a lista dos campos faltantes ou inválidos.
- **FR-023**: Os textos do relatório (título, capa, constatações, notas e legendas) NÃO DEVEM ter nome, identificador ou valor de usina que não venha do perfil ou dos dados.
- **FR-024**: As análises que hoje supõem características da São Domingos, como as faixas de afluência para duas unidades geradoras, DEVEM se ajustar ao perfil, sem mudar o resultado da São Domingos.
- **FR-025**: Os dados brutos baixados uma vez DEVEM servir a qualquer usina. Os dados tratados, os resultados da conferência e das análises, as figuras e os relatórios DEVEM ficar separados por usina.
- **FR-026**: O README DEVE ter um guia curto para incluir uma nova usina:
  - preencher o perfil;
  - onde obter cada identificador e cada parâmetro;
  - executar o fluxo;
  - conferir a auditoria de identificação.

**Cópias de segurança (US4)**

- **FR-027**: O projeto DEVE ter no máximo duas cópias de segurança. Ao criar uma nova, depois de conferida, a mais antiga DEVE ser excluída; se a criação falhar, nenhuma cópia é excluída.
- **FR-028**: As cópias datadas de 06/10/2026 ou antes DEVEM ser excluídas no início da reorganização, por autorização do usuário em 07/10/2026.
- **FR-029**: Os arquivos `.bak` soltos de código, testes, specs, README e dependências DEVEM ser excluídos. Nos dados tratados, cada arquivo DEVE manter só a cópia da versão imediatamente anterior.
- **FR-030**: As versões anteriores de arquivos brutos republicados pelo ONS DEVEM seguir o mesmo limite: no máximo duas por arquivo, as mais recentes.

**Limpeza e organização (US5)**

- **FR-031**: Antes de excluir ou mover qualquer arquivo, DEVE ser apresentado ao usuário o inventário do que o fluxo, os testes, as specs, a constituição e o relatório não usam. Cada item traz o tamanho, a ação proposta (excluir, mover ou manter) e o motivo. Nada sai sem aprovação.
- **FR-032**: Com a aprovação, DEVEM sair:
  - a versão de 30/09/2026 dos relatórios;
  - os caches de execução;
  - os arquivos legados ou duplicados, como o dicionário de dados na raiz, já guardado com os dados brutos;
  - os arquivos de apoio às conferências manuais que não alimentam o relatório.
- **FR-033**: Documentos de referência do usuário (ofício, relatórios de fiscalização, resoluções e documentos da usina) NÃO DEVEM ser excluídos sem aprovação explícita. Os mantidos DEVEM ficar numa pasta de documentos de referência da usina.
- **FR-034**: Os dados brutos e os dados tratados usados pelo relatório NÃO DEVEM ser excluídos.
- **FR-035**: O README DEVE descrever o projeto como fica ao final, sem o histórico de mudanças, que passa a ficar no controle de versões. Ele cobre:
  - o fluxo de cinco etapas;
  - como executar cada etapa e o fluxo completo;
  - como incluir uma usina;
  - a estrutura de pastas;
  - a política de cópias.

**Conclusão do relatório (US6)**

- **FR-036**: O relatório DEVE ter a seção "Conclusão", entre a última seção de análise e as notas metodológicas, no PDF e no Markdown, com entrada no sumário. No PDF, ela DEVE caber em uma página.
- **FR-037**: A conclusão DEVE ter uma frase de abertura e quatro listas, nesta ordem:
  - "Pontos de atenção";
  - "Possíveis problemas";
  - "A confirmar com o agente";
  - "A verificar em campo".

  A frase de abertura diz que os itens são indícios a confirmar, gerados por regras a partir dos dados. Cada lista tem no máximo cinco itens, de uma frase cada, com o número que sustenta o item e a seção de origem.
- **FR-038**: Cada item DEVE ser gerado por uma regra do catálogo abaixo, aplicada aos resultados das análises e das conferências. Nenhum item é escrito à mão nem fica fixo no texto. As listas seguem a ordem do catálogo; quando uma lista passa de cinco itens, ficam os cinco primeiros.
- **FR-039**: Os itens NÃO DEVEM afirmar causa nem avaliar o desempenho da usina. Ficam de fora termos como "satisfatório", "insatisfatório", "descumprimento" e equivalentes. Os itens apontam indícios, perguntas e verificações.
- **FR-040**: Quando a regra C2 disparar, a conclusão DEVE nomear a unidade geradora, como o ONS a identifica, e trazer os números que sustentam o indício.
- **FR-041**: A conclusão NÃO DEVE repetir o texto das constatações.
- **FR-042**: A planilha DEVE ganhar a aba CONCLUSAO, com todos os itens gerados (lista, ordem, regra, texto e seções de origem), inclusive os que passarem do limite de cinco. A aba FONTES DEVE cobri-la. As notas metodológicas DEVEM descrever, em um item, as regras e os limiares da conclusão.
- **FR-043**: O catálogo e os limiares são regras gerais do projeto, iguais para qualquer usina. A conclusão gerada para a São Domingos DEVE ser apresentada ao usuário antes de virar referência (FR-010), e o catálogo pode ser ajustado nessa aprovação.

**Catálogo de regras da conclusão** (limiares iniciais):

| Regra | Dispara quando | Pontos de atenção | Possíveis problemas | Confirmar com o agente | Verificar em campo |
|---|---|---|---|---|---|
| C1. Paradas com EVT | EVT com a usina parada ≥ 10 % da EVT total | energia, parcela, horas e anos de maior volume; com programação diária, a parcela das horas com programação de até 1 MW | n/a | motivo das paradas (ordens do ONS, restrições elétricas ou energéticas), com os registros dos maiores eventos | livro de operação e supervisório nas datas dos maiores eventos: ordens recebidas, comandos de parada e abertura do vertedouro |
| C2. Unidade geradora | uma unidade responde por ≥ 2/3 da TEIFa mais recente, com a TEIFa acima da referência; ou registra limitação forçada de potência (HEDF) em ≥ 50 % dos meses | n/a | indício de problema na unidade: parcela da TEIFa, meses com registro e horas | causa, histórico e situação atual (ocorrências, ordens de serviço, correção prevista) | potência máxima que a unidade alcança hoje e registros de limitação |
| C3. Afluência que cabia nas turbinas | ≥ 80 % das horas com EVT tinham afluência até o engolimento máximo | parcela dessas horas: o vertimento turbinável não se explica por afluência acima do engolimento | n/a | n/a | n/a |
| C4. Concentração diurna | razão entre a EVT média das 9h às 15h e a das 20h às 5h ≥ 2 em algum dos dois últimos anos | os anos e a geração diurna em relação à noturna | n/a | n/a | n/a |
| C5. Disponibilidade e taxas | disponibilidade média declarada ou DISPF médio abaixo da referência da garantia física; ou TEIFa ou TEIP mais recentes acima das referências | as medidas e a distância de cada uma à referência | n/a | n/a | n/a |
| C6. Parada com geração programada | ≥ 1 evento de usina parada com programação acima de 5 MW | n/a | horas, eventos e o maior evento | ocorrências nesses eventos | registros de ocorrência no livro de operação |
| C7. Classificação de estados | diferença ≥ 5 GWh, num ano, entre a capacidade não sincronizada e a reserva desligada; ou ≥ 1 mês-unidade com DISPF e TEIP divergentes | n/a | os anos e as diferenças | classificação dos estados e declarações de disponibilidade informadas ao ONS, num item único com a C8 | n/a |
| C8. Geração acima da disponibilidade declarada | ≥ 100 h na regra R7 | n/a | as horas | entra no item da C7 | n/a |
| C9. Geração e garantia física | geração média abaixo da garantia física; ou EVT do último ano completo é a maior da série | razão entre geração e garantia física; ano de maior EVT | n/a | n/a | n/a |
| C10. Indisponibilidade longa | indisponibilidade total ≥ 30 dias; ou unidade com indisponibilidade programada ≥ 20 % num ano completo | n/a | n/a | causa e documentação dos períodos | plano e registros de manutenção preventiva e corretiva |
| C11. Instrumentação e medição | dados hidrológicos com valores sinalizados; ou geração com vazão turbinada nula (R9) ≥ 24 h | n/a | n/a | n/a | instrumentação de nível e de vazão e medição da vazão turbinada |

### Key Entities

- **Etapa do fluxo**: nome, ordem, entradas (resultados das etapas anteriores), saídas e spec correspondente.
- **Perfil da usina**: nome, estado, identificador e campo de conferência em cada conjunto, parâmetros técnicos com fonte e data, e limiares das análises.
- **Resultado de conferência**: conferência, bases comparadas, período, quantidade comparada, coincidências, divergências e tolerância. É lido pelas análises e pelo relatório.
- **Cópia de segurança**: data, motivo, conteúdo e conferência; no máximo duas.
- **Inventário de limpeza**: item, tamanho, uso atual, ação proposta, motivo e aprovação.
- **Mapeamento de requisitos**: requisito da spec antiga e o seu destino (spec e requisito novos, ou "superado", com o motivo).
- **Regra da conclusão**: identificador (C1 a C11), condição e limiar, listas em que gera item e o que cada item diz.
- **Item da conclusão**: lista, ordem, regra que o gerou, texto de uma frase e seções de origem.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O relatório da São Domingos gerado pelo fluxo reorganizado é idêntico ao relatório de referência (FR-010: o aprovado em 07/10/2026 com a conclusão aprovada), exceto a data de geração:
  - PDF com o mesmo número de páginas e o mesmo texto;
  - Markdown idêntico;
  - planilha com as 57 abas idênticas célula a célula;
  - as 8 figuras idênticas byte a byte.
- **SC-002**: O fluxo completo roda com um único comando, e cada uma das cinco etapas roda isoladamente. Em 100% das tentativas de rodar uma etapa sem as anteriores, ela para e indica a etapa que falta.
- **SC-003**: A pasta de specs tem exatamente cinco specs. 100% dos requisitos em vigor das oito specs antigas aparecem no mapeamento com o seu destino, e nenhuma spec nova remete a revisões de outras.
- **SC-004**: A constituição não tem histórico de emendas nem valores de uma usina específica. Toda regra que define o relatório aprovado está nela (princípio) ou numa spec de etapa (detalhe), sem contradição entre as duas.
- **SC-005**: Com o perfil de uma usina fictícia, sobre dados de teste:
  - o fluxo gera um relatório completo, com a mesma estrutura e nenhuma menção à São Domingos;
  - um perfil incompleto é recusado antes da coleta em 100% dos casos testados.
- **SC-006**: Ao final:
  - existem no máximo duas cópias de segurança do projeto;
  - não há nenhum arquivo `.bak` solto fora dos dados tratados;
  - não restam as cópias de 06/10/2026 ou antes nem a versão de 30/09/2026 dos relatórios, o que libera cerca de 95 MB.
- **SC-007**: A suíte de testes cobre as cinco etapas e o perfil da usina, roda sem rede, e nenhum teste de hoje é removido sem outro que cubra o mesmo comportamento.
- **SC-008**: Nenhum arquivo é excluído sem constar do inventário aprovado, e nenhum documento de referência do usuário é excluído sem aprovação explícita.
- **SC-009**: A conclusão da São Domingos:
  - cabe em uma página do PDF;
  - tem as quatro listas, com no máximo cinco itens cada;
  - 100 % dos itens remetem a uma regra do catálogo e a uma seção;
  - nenhum item usa termos de avaliação de desempenho;
  - o indício na unidade geradora aparece com os números que o sustentam;
  - o usuário aprova o texto antes da reorganização.

---

## Assumptions

- **Dados**:
  - As dez bases do ONS de hoje bastam; nenhuma base nova é incluída (decisão do usuário em 07/10/2026).
  - A base de EVT local é mantida, sem novo download.
  - Os dados brutos do ONS trazem todas as usinas do SIN e por isso são compartilhados entre os perfis.
- **Controle de versões**:
  - O relatório aprovado, o código e as specs atuais estão no controle de versões do projeto (commit "versão 1.0 pré relatório Usinas Hidrelétricas").
  - Specs, emendas e cópias removidas continuam recuperáveis por ele.
  - Os commits ficam a cargo do usuário.
- **Outras usinas**:
  - Ao final, a São Domingos é a única usina com perfil real; a análise de outra usina é uso futuro, com o perfil preenchido pelo usuário.
  - A generalidade é verificada agora com uma usina fictícia, nos testes.
  - Os parâmetros técnicos que o ONS não publica (garantia física, IP e TEIF de referência, engolimento, tipo de turbina) são informados pelo usuário no perfil, com a fonte. Para a São Domingos, valem os atuais: garantia física de 36,4 MWmed (ANEEL) e demais parâmetros do RF 0009/2017-AGEPAN-SFG.
- **Cópias de segurança**: as cópias do projeto não incluem os dados brutos (cerca de 4 GB), como hoje.
- **Pasta e ferramentas**:
  - O nome da pasta do projeto (`UHE_SAO_DOMINGOS`) não muda nesta spec; renomeá-la é decisão do usuário.
  - As skills do Spec Kit para outro agente (`.agents/`) entram no inventário de limpeza, com ação proposta e aprovação do usuário.
  - O servidor de consulta aos dados do ONS configurado no projeto é mantido, porque serve a consultas interativas, fora do fluxo.
- **Spec Kit**: o desenvolvimento continua com o Spec Kit. Uma mudança futura usa a spec da etapa afetada como pasta da feature.
- **Prazo**: a fiscalização presencial é de 14 a 16/10/2026, e o relatório aprovado continua disponível e reproduzível durante toda a reorganização.
- **Conclusão**:
  - Organiza indícios e verificações a partir dos dados abertos do ONS e não substitui a avaliação do fiscal.
  - O catálogo inicial (FR-038) pode ser ajustado na aprovação.
  - A spec 003 (FR-005) proíbe diagnóstico e parecer. Esta spec mantém a proibição e acrescenta a conclusão por regras, que aponta indícios sem afirmar causa. No mapeamento, a FR-005 vai para a spec das análises com essa redação.
- **Ordem**: a conclusão é implementada no código atual, antes da reorganização, para estar pronta antes da fiscalização. Depois, a reorganização a leva para as etapas de análises e de relatório, como o resto do código.
