# Feature Specification: Relatório Mais Enxuto, com Sumário na Capa e Constatações em Cada Seção - UHE São Domingos

**Feature Branch**: `008-relatorio-enxuto`

**Created**: 2026-10-06

**Status**: Implementado (06/10/2026; revisado em 07/10/2026)

**Input**: User description: "Relatório mais enxuto: capa com sumário e constatações dentro de cada seção (spec 008). Pedido do usuário em 06/10/2026, depois de aprovar o relatório da spec 007: hoje a lista "Principais constatações" no início traz o texto completo de cada constatação, e depois cada seção repete ou retoma a mesma explicação. (1) A página 1 (capa) mantém os dados básicos da usina, os percentuais importantes (indicadores da capa) e passa a ter um SUMÁRIO que só elenca os pontos abordados (seções), sem o texto das constatações. (2) Cada constatação passa a aparecer uma única vez, no início da seção correspondente, seguida das tabelas e figuras com as explicações e legendas atuais; constatações sem seção própria hoje vão para a seção mais próxima. (3) As legendas de fonte e conferência de cada figura e tabela (spec 007) continuam; o rodapé repetido em todas as páginas sai, porque cada figura e tabela já cita a sua fonte; o número da página continua e a data de geração vai para a capa; o mesmo vale para a linha "**Fontes**:" do cabeçalho do Markdown (revisão das FR-009 e FR-010 da spec 007). (4) Números, textos das constatações, tabelas, figuras, legendas de fonte e abas da planilha (inclusive CONSTATACOES e FONTES) inalterados; só a organização e o rodapé mudam. Dúvidas para o usuário: se o Markdown deve seguir a mesma estrutura do PDF e se as notas "Fonte: conjunto …" das seções das bases novas devem sair, mantendo as ressalvas. Prazo: antes da fiscalização presencial de 14 a 16/10/2026."

## Contexto

O relatório aprovado pelo usuário em 06/10/2026 (spec 007) começa por uma lista de 17 constatações, cada uma com o texto completo. Várias delas são repetidas, palavra por palavra, no início da seção correspondente, e as demais retomam a explicação que a seção já dá com tabelas e figuras. O leitor encontra o mesmo conteúdo duas vezes.

Além disso, o rodapé de todas as páginas repete "Fontes: ONS – Dados Abertos, 10 conjuntos; fonte de cada figura e tabela na legenda; relação completa nas Notas metodológicas. Gerado em …", informação que as legendas de cada figura e tabela já dão.

Esta spec reorganiza o relatório sem mudar nenhum número nem texto de análise:

- **Capa**: dados básicos da usina, percentuais principais, data de geração e sumário dos pontos abordados.
- **Seções**: cada constatação aparece uma única vez, no início da seção à qual se refere, seguida das tabelas e figuras.

**Lugar de cada constatação** (proposta; vale para as que existirem na execução):

| Constatação | Seção |
|---|---|
| Cobertura dos dados | Fonte e cobertura dos dados |
| Cadastro da usina no ONS (só com divergência) | Fonte e cobertura dos dados (revisão de 07/10/2026; antes, Identificação da usina no cadastro do ONS) |
| Disponibilidade | Indicadores anuais |
| Geração e garantia física; Indisponibilidades | Disponibilidade e geração por ano |
| Indicadores oficiais de disponibilidade (ONS); Estados operativos das unidades geradoras (ONS) | Indicadores oficiais do ONS por unidade geradora |
| Energia vertida turbinável; Distribuição ao longo do ano; Mudança de classificação do vertimento pelo ONS | Energia vertida turbinável mensal |
| Concentração diurna | Perfil horário da geração e da EVT |
| EVT e nível de geração; EVT com a usina parada | EVT por nível de geração e eventos de usina parada |
| Programação diária do ONS | Operação verificada e programação diária do ONS |
| Disponibilidade sincronizada | Disponibilidade operacional e sincronizada (ONS) |
| Afluência e vertimento | Afluência, vertimento e nível do reservatório (ONS) |
| Horas com geração zero | Horas com geração zero por mês |
| Conferência da geração (só com divergência) | Conferência da geração com a série oficial (ONS) |
| Qualidade dos dados | Qualidade dos dados |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capa com dados básicos, percentuais e sumário (Priority: P1)

Como fiscal da AGEMS, quero que a primeira página traga os dados básicos da usina, os percentuais mais importantes, a data de geração e um sumário com os pontos abordados, sem o texto das constatações. Assim apresento o relatório na fiscalização começando pelo panorama e vou direto ao ponto que interessa.

**Why this priority**: É o pedido central do usuário e a mudança mais visível; a capa é a página mais lida.

**Independent Test**: Gerar o relatório e conferir que a primeira página tem os blocos de identificação e de parâmetros, os indicadores da capa, a data de geração e o sumário com todas as seções, e nenhum texto de constatação.

**Acceptance Scenarios**:

1. **Given** o relatório gerado, **When** a capa é aberta, **Then** ela mostra:
   - os blocos de identificação da usina e de parâmetros técnicos, como hoje, e a ficha do cadastro do ONS, quando carregado (revisão de 07/10/2026);
   - os indicadores da capa (percentuais e totais principais), como hoje;
   - a data e a hora de geração do relatório;
   - o sumário, com o número e o título de cada seção, na ordem em que aparecem.
2. **Given** o PDF, **When** o sumário é lido, **Then** cada item traz a página em que a seção começa.
3. **Given** uma seção que não existe nesta execução (base ausente), **When** o relatório é gerado, **Then** ela não aparece no sumário.
4. **Given** a capa, **When** comparada com o relatório anterior, **Then** nenhum texto completo de constatação aparece nela.

---

### User Story 2 - Cada constatação uma única vez, no início da sua seção (Priority: P1)

Como fiscal, quero ler cada constatação no início da seção a que ela se refere, logo antes das tabelas e figuras que a sustentam, sem a mesma explicação repetida em outro lugar do relatório.

**Why this priority**: Elimina a repetição apontada pelo usuário e deixa o relatório mais curto sem perder conteúdo.

**Independent Test**: Gerar o relatório e conferir que cada constatação aparece exatamente uma vez, no início da seção indicada na tabela do Contexto, com o texto idêntico ao atual.

**Acceptance Scenarios**:

1. **Given** cada constatação gerada nesta execução, **When** o relatório é gerado, **Then** o seu texto aparece exatamente uma vez, no início da seção indicada, antes das tabelas e figuras dela.
2. **Given** as constatações condicionais (cadastro e conferência da geração, só com divergência), **When** não há divergência, **Then** elas não aparecem, como hoje.
3. **Given** os textos das constatações, **When** comparados com o relatório anterior, **Then** são idênticos; muda só o lugar.
4. **Given** a aba CONSTATACOES da planilha, **When** a planilha é gerada, **Then** ela continua com todas as constatações, na mesma ordem e com o mesmo texto.

---

### User Story 3 - Sem rodapé de fontes repetido (Priority: P2)

Como fiscal, quero que o rodapé das páginas não repita a frase sobre as fontes, já que cada figura e tabela traz a sua; o número da página continua.

**Why this priority**: Pedido explícito do usuário; reduz ruído em todas as páginas.

**Independent Test**: Gerar o PDF e conferir que o rodapé tem só a numeração de páginas e que todas as legendas de fonte continuam.

**Acceptance Scenarios**:

1. **Given** o PDF, **When** gerado, **Then** o rodapé de cada página mostra o número da página e o total, e não mostra a frase de fontes nem a data de geração.
2. **Given** o Markdown, **When** gerado, **Then** o cabeçalho não tem mais a linha "**Fontes**:", e a data de geração aparece no cabeçalho.
3. **Given** as figuras e tabelas, **When** o relatório é gerado, **Then** 100% continuam com a legenda de fonte e conferência (spec 007).

---

### Edge Cases

- **Seções opcionais ausentes** (indicadores, programação, bases novas): não aparecem no sumário nem na numeração; as constatações delas também não existem.
- **Constatação sem seção correspondente na execução** (ex.: seção removida por falta de dados): a constatação vai para a seção mais próxima indicada no plano; nenhuma constatação pode desaparecer.
- **Seção com duas ou mais constatações**: aparecem na ordem atual da lista de constatações.
- **Sumário longo**: a capa continua cabendo numa página no PDF (A4 paisagem); se não couber, o sumário passa para a página 2, logo depois da capa.
- **Notas "Fonte: conjunto …" das seções das bases novas (spec 006)**: a parte que cita o conjunto, o identificador e a data de obtenção sai, porque as legendas da spec 007 já dão essa informação; as ressalvas ficam (dados não consistidos pelo ONS, cadastro sem histórico, versões anteriores preservadas, critério de coincidência). Decisão do usuário em 06/10/2026 (FR-013).
- **Markdown**: passa a seguir a mesma estrutura do PDF: mesmas seções, na mesma ordem, com as figuras no corpo da seção a que pertencem, e não numa lista no final. Decisão do usuário em 06/10/2026 (FR-014).

---

## Requirements *(mandatory)*

### Functional Requirements

**Capa e sumário (US1)**

- **FR-001**: A capa DEVE manter os blocos de identificação da usina e de parâmetros técnicos e os indicadores da capa, como hoje. Com o cadastro do ONS carregado, DEVE trazer também a ficha cadastral (FR-015).
- **FR-002**: A capa DEVE mostrar a data e a hora de geração do relatório.
- **FR-003**: O relatório DEVE ter um sumário, logo após a capa ou nela, com o número e o título de cada seção presente nesta execução, na ordem do relatório; no PDF, com a página de início de cada seção.
- **FR-004**: A capa e o sumário NÃO DEVEM conter o texto das constatações.

**Constatações nas seções (US2)**

- **FR-005**: Cada constatação gerada DEVE aparecer exatamente uma vez no relatório (PDF e Markdown), no início da seção indicada na tabela do Contexto, antes das tabelas e figuras.
- **FR-006**: O título da constatação DEVE aparecer junto ao texto, destacado, para que o leitor a identifique dentro da seção.
- **FR-007**: A lista "Principais constatações"/"Constatações" do início do relatório DEVE ser substituída pelo sumário.
- **FR-008**: As regras de existência das constatações NÃO mudam (as condicionais continuam aparecendo só com divergência).

**Rodapé e cabeçalho (US3)**

- **FR-009**: O rodapé das páginas do PDF DEVE conter só a numeração ("Página X de Y"); a frase de fontes e a data de geração saem do rodapé. Revisa a FR-009 da spec 007.
- **FR-010**: O cabeçalho do Markdown DEVE perder a linha "**Fontes**:" e ganhar a data de geração. Revisa a FR-010 da spec 007.
- **FR-011**: As legendas de fonte e conferência de cada figura e tabela (spec 007) DEVEM continuar em 100% das figuras e tabelas.

**Não regressão**

- **FR-012**: Números, textos das constatações, textos das seções, tabelas, figuras, legendas de fonte e abas da planilha (inclusive CONSTATACOES e FONTES) NÃO DEVEM mudar; muda só o lugar das constatações, a capa, o sumário, o rodapé, o cabeçalho, as notas de fonte da FR-013, a organização do Markdown da FR-014 e a ficha do cadastro da FR-015.

**Decisões do usuário (06/10/2026)**

- **FR-013**: Nas notas das seções das bases novas (disponibilidade, hidrologia, geração e cadastro), a parte "Fonte: conjunto … (identificador), obtido em …" DEVE sair, no PDF e no Markdown; as ressalvas dessas notas DEVEM ficar, com o mesmo texto. A relação completa de fontes nas Notas metodológicas continua. Exceção (revisão de 07/10/2026): a ressalva do cadastro sem série histórica fica só nas Notas metodológicas, onde já está (FR-015).
- **FR-014**: O Markdown DEVE seguir a estrutura do PDF: as mesmas seções, na mesma ordem e com os mesmos títulos, cada figura no corpo da sua seção (imagem com a legenda descritiva e a legenda de fonte), sem a lista de figuras no final. Tabelas que hoje só existem no PDF ou só no Markdown passam a existir nos dois.

**Revisão do usuário (07/10/2026)**

- **FR-016** (revisão 2, 07/10/2026): As figuras das seções "Série temporal de disponibilidade, geração e EVT", "Energia vertida turbinável mensal", "Disponibilidade operacional e sincronizada (ONS)" e "Vazões defluentes por ano" DEVEM ter o mesmo tamanho, no PNG e no PDF, e ocupar a largura útil da página no PDF. O conteúdo das figuras (dados, séries, cores e textos) não muda.
- **FR-015**: A seção "Identificação da usina no cadastro do ONS" DEVE sair. A ficha do cadastro DEVE ir para a capa, como bloco "Cadastro no ONS" ao lado dos blocos de identificação e de parâmetros, com a sua legenda de fonte e conferência e com os mesmos itens de antes, exceto a data da consulta. A constatação "Cadastro da usina no ONS" (só com divergência) DEVE ir para a seção "Fonte e cobertura dos dados". A capa DEVE continuar cabendo numa página (SC-002).

### Key Entities

- **Sumário**: lista das seções presentes, com número, título e, no PDF, página de início.
- **Constatação**: título e texto gerados a partir dos dados (spec 003 e seguintes), com a seção à qual pertence.
- **Mapa constatação → seção**: associação da tabela do Contexto, usada pelo PDF e pelo Markdown.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada constatação aparece exatamente 1 vez no PDF e 1 vez no Markdown (hoje, até 2 vezes).
- **SC-002**: A capa do PDF cabe numa página e contém dados básicos, indicadores, data de geração e sumário; nenhum texto completo de constatação.
- **SC-003**: O sumário lista 100% das seções presentes, e no PDF a página indicada de cada seção confere com a página real.
- **SC-004**: O rodapé de 100% das páginas do PDF tem só a numeração; 100% das figuras e tabelas mantêm a legenda de fonte.
- **SC-005**: Nenhum número, texto de constatação, tabela, figura ou aba muda em relação ao relatório anterior (comparação ignorando só a posição das constatações e das seções, a capa, o sumário, o rodapé, o cabeçalho, a parte de fonte das notas da FR-013 e a ficha do cadastro da FR-015).
- **SC-008**: O Markdown e o PDF têm as mesmas seções, na mesma ordem, e o mesmo sumário.
- **SC-006**: O relatório fica mais curto que o anterior (31 páginas no PDF), sem perder conteúdo.
- **SC-007**: Entregue e com o relatório regenerado até 13/10/2026.

---

## Assumptions

- Escopo exclusivo da UHE São Domingos (MS); nenhum dado novo é baixado ou reprocessado.
- O conteúdo das constatações, das seções e das legendas continua gerado pelos módulos das specs 003 a 007; esta spec só reorganiza a apresentação.
- A planilha não muda: a aba CONSTATACOES continua listando todas as constatações (é a visão "tudo junto" para quem quiser).
- O título do relatório e o cabeçalho das páginas do PDF (nome da usina e período) continuam.
- O mapa constatação → seção da tabela do Contexto é a proposta inicial, aberta a ajuste do usuário.
- Prazo: fiscalização presencial de 14 a 16/10/2026.

---

## Histórico de revisões

### 2026-10-07 — ficha do cadastro na capa

Pedido do usuário em 07/10/2026, depois de aprovar o relatório: retirar a seção 2 (Identificação da usina no cadastro do ONS) e complementar a capa com essas informações, sem a data da consulta. Cópia da versão aprovada em `_backup_2026-10-07_antes_revisao008/`.

| Item | O que mudou |
| :--- | :--- |
| FR-001, US1 | A capa ganha o bloco "Cadastro no ONS" quando o cadastro está carregado. |
| FR-015 (nova) | Sai a seção do cadastro; ficha na capa, sem a data da consulta; constatação do cadastro na seção "Fonte e cobertura dos dados". |
| FR-012, SC-005 | A ficha do cadastro na capa entra nas mudanças permitidas. |
| FR-013 | A ressalva do cadastro sem série histórica fica só nas Notas metodológicas, onde já estava; sai a nota abaixo da ficha. |
| Tabela do Contexto | Constatação do cadastro → Fonte e cobertura dos dados. |

### 2026-10-07 (revisão 2) — figuras maiores e padronizadas

Pedido do usuário em 07/10/2026: aumentar e padronizar os gráficos das seções 5, 6, 10 e 13 (série temporal, EVT mensal, disponibilidade sincronizada e vazões defluentes). Cópia anterior em `_backup_2026-10-07_antes_figuras/`.

| Item | O que mudou |
| :--- | :--- |
| FR-016 (nova) | As quatro figuras com o mesmo tamanho (PNG de 11 × 4,3 polegadas) e, no PDF, na largura útil da página. |
| FR-012, SC-005 | O tamanho dessas quatro figuras entra nas mudanças permitidas; o conteúdo continua o mesmo. |
