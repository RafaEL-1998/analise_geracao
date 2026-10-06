# Feature Specification: Fonte Explícita em Cada Figura e Tabela do Relatório - UHE São Domingos

**Feature Branch**: `007-fontes-por-figura-tabela`

**Created**: 2026-10-05

**Status**: Implementado (06/10/2026)

**Input**: User description: "Fonte explícita em cada figura e tabela do relatório (spec 007). Hoje o rodapé das páginas do PDF diz "Fonte: ONS – Dados Abertos, conjunto Energia Vertida Turbinável", como se todo o relatório viesse de uma fonte só, mas as figuras e tabelas cruzam 10 conjuntos do ONS (EVT; 4 de indicadores por unidade geradora e taxas TEIFa/TEIP; programação diária; disponibilidade por usina; dados hidrológicos horários; geração por usina; modalidade das usinas). Pedido do usuário: para cada gráfico e tabela, o rodapé deve trazer a fonte de onde os dados foram extraídos e, quando houver, a fonte com que foram validados, de forma bem explícita. (1) Cada figura e cada tabela do relatório, no PDF e no Markdown, ganha logo abaixo uma legenda de fonte com: o(s) conjunto(s) de onde os dados foram extraídos (nome do conjunto do ONS, identificador da usina e data de obtenção) e as conferências com outra fonte e o resultado; quando um dado não tiver outra fonte para conferência (ex.: a EVT), a legenda diz isso. Textos de fonte e de conferência gerados a partir dos dados e dos resultados das conferências, nunca fixos. (2) O rodapé das páginas do PDF deixa de citar uma fonte só e passa a ser genérico (ONS – Dados Abertos, N conjuntos, com N calculado das bases carregadas; fonte de cada figura e tabela na legenda; relação completa nas Notas metodológicas); o cabeçalho do Markdown ganha a mesma informação. (3) Planilha: aba com, para cada aba, os conjuntos de origem e as conferências. (4) Números, constatações, seções e abas existentes inalterados: só legendas, rodapé e a aba nova. Prazo: antes da fiscalização presencial de 14 a 16/10/2026."

## Contexto

O relatório da fiscalização (PDF, Markdown e planilha) cruza 10 conjuntos de dados abertos do ONS:

- Energia Vertida Turbinável (EVT), base de todas as séries de geração, disponibilidade declarada, vazões e EVT;
- 4 conjuntos de indicadores por unidade geradora e taxas TEIFa/TEIP (spec 004);
- programação diária (spec 004);
- disponibilidade por usina, dados hidrológicos horários, geração por usina e modalidade das usinas (spec 006).

O rodapé de todas as páginas do PDF, porém, ainda diz que a fonte é só o conjunto de EVT, como na primeira versão do relatório. A relação completa existe nas Notas metodológicas e na tabela de parâmetros, mas quem lê uma figura ou tabela isolada não sabe de onde vieram aqueles números nem se foram conferidos com outra fonte.

Algumas conferências entre fontes já são feitas pelo pipeline e podem ser citadas com o resultado:

| Dado | Fonte de extração | Conferido com | Resultado na base atual |
|---|---|---|---|
| Geração horária | EVT | Geração por usina | 100% das horas coincidentes |
| Disponibilidade declarada | EVT | Disponibilidade por usina (operacional) | 100% das horas coincidentes |
| Vazões turbinada e vertida | EVT | Dados hidrológicos | 100% das horas coincidentes (diferença até 0,5 m³/s) |
| TEIFa e TEIP recalculadas | Parâmetros das taxas | TEIFa e TEIP publicadas | reproduzidas nos meses publicados |
| Indicador DISPF | Indicadores por unidade | Horas por estado operativo (parâmetros das taxas) | 4 meses-unidade divergentes |
| Potência e estado | Cadastro (modalidade das usinas) | Parâmetros do projeto | sem divergência |

A EVT, a disponibilidade sincronizada, a afluência, os níveis, o volume útil e a programação não têm outra fonte pública para conferência.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fonte e conferência em cada figura e tabela (Priority: P1)

Como fiscal da AGEMS, quero que cada figura e cada tabela do relatório diga, logo abaixo dela, de qual conjunto do ONS os dados foram extraídos e com qual outra fonte foram conferidos, com o resultado. Assim posso mostrar ao agente, na fiscalização, a origem de cada número sem procurar nas notas.

**Why this priority**: É a rastreabilidade pedida pelo usuário e pela constituição (princípio IV). Sem ela, uma figura copiada para outro documento perde a origem.

**Independent Test**: Gerar o relatório com todas as bases e conferir que cada figura e cada tabela, no PDF e no Markdown, tem a legenda de fonte, e que cada legenda cita conjuntos que de fato alimentam aquela figura ou tabela.

**Acceptance Scenarios**:

1. **Given** uma figura ou tabela, **When** o relatório é gerado, **Then** logo abaixo dela aparece a legenda de fonte com:
   - o nome de cada conjunto do ONS usado, o identificador da usina nesse conjunto e a data de obtenção;
   - cada conferência com outra fonte que se aplica aos dados mostrados, com o resultado (ex.: "100% das horas coincidentes" ou o número de divergências).
2. **Given** dados que não têm outra fonte para conferência (ex.: a EVT), **When** a legenda é gerada, **Then** ela diz explicitamente que não há outra fonte pública para conferir esse dado.
3. **Given** uma conferência com divergências, **When** a legenda é gerada, **Then** ela informa a quantidade de divergências e onde estão listadas (aba da planilha), sem esconder o resultado.
4. **Given** uma base que não foi carregada nesta execução, **When** a legenda de uma figura ou tabela que poderia ser conferida com ela é gerada, **Then** a legenda diz que a conferência não foi feita nesta execução, em vez de omiti-la.
5. **Given** os números citados nas legendas, **When** comparados com a planilha, **Then** são idênticos (texto gerado a partir dos resultados das conferências).

---

### User Story 2 - Rodapé e cabeçalho fiéis às fontes (Priority: P1)

Como fiscal, quero que o rodapé das páginas do PDF e o cabeçalho do Markdown digam que o relatório usa vários conjuntos do ONS e onde encontrar a fonte de cada figura e tabela, para que o rodapé não induza o leitor a achar que tudo veio de uma fonte só.

**Why this priority**: O rodapé atual está errado desde a inclusão das bases das specs 004 e 006 e aparece em todas as páginas.

**Independent Test**: Gerar o PDF com todas as bases e com só a base de EVT e conferir que o rodapé cita a quantidade certa de conjuntos em cada caso.

**Acceptance Scenarios**:

1. **Given** o relatório com N conjuntos carregados, **When** o PDF é gerado, **Then** o rodapé de cada página diz "ONS – Dados Abertos", a quantidade N de conjuntos, que a fonte de cada figura e tabela está na legenda e que a relação completa está nas Notas metodológicas, além da data e hora de geração.
2. **Given** o relatório só com a base de EVT, **When** o PDF é gerado, **Then** o rodapé cita 1 conjunto.
3. **Given** o Markdown, **When** gerado, **Then** o cabeçalho traz a mesma informação de fontes.

---

### User Story 3 - Origem de cada aba da planilha (Priority: P2)

Como fiscal, quero uma aba na planilha que diga, para cada aba, de quais conjuntos vieram os dados e com quais fontes foram conferidos, para poder entregar a planilha ao agente ou a outro técnico sem explicações adicionais.

**Why this priority**: A planilha é usada para conferência detalhada; a origem das abas hoje só se deduz pelo prefixo do nome.

**Independent Test**: Gerar a planilha e conferir que a aba nova tem uma linha para cada uma das demais abas, com conjuntos e conferências preenchidos.

**Acceptance Scenarios**:

1. **Given** a planilha gerada, **When** aberta, **Then** a aba de fontes lista todas as outras abas, cada uma com os conjuntos de origem (nome, identificador da usina, data de obtenção) e as conferências com o resultado, ou a indicação de que não há conferência.
2. **Given** uma aba que não é criada nesta execução (base ausente ou aba sem linhas), **When** a planilha é gerada, **Then** ela não aparece na aba de fontes.

---

### Edge Cases

- **Figura ou tabela com várias bases**: a legenda cita todas (ex.: disponibilidade sincronizada usa a disponibilidade por usina, a geração da base de EVT, a programação diária e os parâmetros das taxas).
- **Tabela derivada de cálculo do projeto** (ex.: TEIFa e TEIP recalculadas, faixas de afluência): a legenda cita os conjuntos de entrada e diz que o valor é calculado neste relatório, com o critério resumido ou a referência às Notas metodológicas.
- **Dados com sinalização de qualidade** (registros excluídos das médias): a legenda não repete as regras; elas continuam nas notas da seção.
- **Alinhamento hidrológico abaixo da meta**: as figuras e tabelas de cruzamento não são publicadas (spec 006); nenhuma legenda órfã aparece.
- **Data de obtenção desconhecida** (manifesto sem registro): a legenda diz "data de obtenção não registrada".
- **Parâmetros do projeto** (potência, engolimento, garantia física): quando usados numa tabela, a legenda cita a origem já registrada na tabela de parâmetros, sem apresentá-los como dado do ONS.
- **Conferências manuais com outras instituições**: as conferências feitas manualmente em 01–02/10/2026 com a CCEE e com o BI da ANEEL (registradas na spec 004, fora do pipeline) não entram nas legendas; só entram as conferências que o pipeline refaz a cada execução (decisão do usuário em 06/10/2026).

---

## Requirements *(mandatory)*

### Functional Requirements

**Legendas de fonte (US1)**

- **FR-001**: Cada figura e cada tabela do relatório, no PDF e no Markdown, DEVE ter logo abaixo uma legenda de fonte.
- **FR-002**: A legenda DEVE citar, para cada conjunto do ONS cujos dados aparecem na figura ou tabela:
  - o nome do conjunto;
  - o identificador da usina naquele conjunto (o da constituição, princípio IV);
  - a data de obtenção registrada no manifesto.
- **FR-003**: A legenda DEVE citar cada conferência com outra fonte que se aplica aos dados mostrados, com o resultado da execução: proporção de horas ou meses coincidentes, ou a quantidade de divergências e a aba onde estão listadas.
- **FR-004**: Quando um dado mostrado não tiver outra fonte pública para conferência, a legenda DEVE dizer isso explicitamente.
- **FR-005**: Quando uma conferência aplicável não puder ser feita nesta execução (base ausente), a legenda DEVE dizer que a conferência não foi feita, em vez de omiti-la.
- **FR-006**: Os textos das legendas DEVEM ser gerados a partir das bases carregadas e dos resultados das conferências; nenhum resultado de conferência pode ser fixo no texto.
- **FR-007**: Valores calculados neste relatório (ex.: TEIFa e TEIP recalculadas, classificações, faixas) DEVEM ser identificados como cálculo do relatório na legenda, com os conjuntos de entrada.
- **FR-008**: O mapeamento entre cada figura ou tabela e os seus conjuntos e conferências DEVE ser declarado num único lugar e usado pelo PDF, pelo Markdown e pela planilha, para que as três saídas não divirjam.

**Rodapé e cabeçalho (US2)**

- **FR-009**: O rodapé das páginas do PDF NÃO DEVE citar um único conjunto como fonte do relatório. DEVE dizer "ONS – Dados Abertos", a quantidade de conjuntos carregados (calculada), que a fonte de cada figura e tabela está na legenda e que a relação completa está nas Notas metodológicas, além da data e hora de geração. *(Revisto pela spec 008 em 06/10/2026; ver Histórico de revisões.)*
- **FR-010**: O cabeçalho do Markdown DEVE trazer a mesma informação de fontes do rodapé do PDF. *(Revisto pela spec 008 em 06/10/2026; ver Histórico de revisões.)*

**Planilha (US3)**

- **FR-011**: A planilha DEVE ganhar uma aba de fontes com uma linha para cada aba exportada, com os conjuntos de origem (nome, identificador da usina e data de obtenção) e as conferências com o resultado, ou a indicação de que não há conferência.

**Não regressão**

- **FR-012**: Números, textos das constatações, seções, tabelas e abas existentes NÃO DEVEM mudar; só podem ser acrescentadas as legendas, o rodapé, a linha do cabeçalho e a aba de fontes.
- **FR-013**: As figuras existentes NÃO DEVEM ser redesenhadas; a legenda de fonte fica no texto abaixo da figura, não dentro da imagem.

### Key Entities

- **Conjunto de origem**: conjunto do ONS usado no relatório, com nome, identificador da usina, data de obtenção e link.
- **Conferência entre fontes**: par de fontes comparadas para um mesmo dado, com o critério de coincidência e o resultado da execução (coincidentes, divergentes, onde estão listadas).
- **Legenda de fonte**: texto abaixo de uma figura ou tabela, composto dos conjuntos de origem e das conferências aplicáveis.
- **Mapa de fontes**: associação entre cada figura, tabela ou aba e os seus conjuntos de origem e conferências.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das figuras e tabelas do PDF e do Markdown têm legenda de fonte, e 100% das abas exportadas aparecem na aba de fontes.
- **SC-002**: Em 100% das legendas, cada conjunto citado alimenta de fato a figura ou tabela, e nenhum conjunto que a alimenta fica de fora (conferência por amostra completa das figuras e tabelas).
- **SC-003**: Os resultados de conferência citados nas legendas são idênticos aos das abas de conferência da planilha.
- **SC-004**: Nenhum número, constatação, seção, tabela ou aba existente muda (comparação com o relatório anterior à feature).
- **SC-005**: O rodapé do PDF cita a quantidade correta de conjuntos com todas as bases e com só a base de EVT. *(Revisto pela spec 008 em 06/10/2026; ver Histórico de revisões.)*
- **SC-006**: Entregue e com o relatório regenerado até 13/10/2026, véspera da fiscalização.

---

## Assumptions

- Escopo exclusivo da UHE São Domingos (MS), com os identificadores da constituição 1.2.0 (princípio IV).
- As conferências citadas são as já feitas pelo pipeline (specs 004 e 006); esta spec não cria conferência nova. As conferências manuais com CCEE e ANEEL continuam só no registro da spec 004 (decisão do usuário em 06/10/2026).
- As bases continuam as atuais; esta spec não baixa nem reprocessa dados, só altera a apresentação do relatório.
- A EVT, a disponibilidade sincronizada, a afluência, os níveis, o volume útil, a programação diária e os indicadores DISPF publicados não têm outra fonte pública conferida pelo pipeline; a legenda diz isso.
- As legendas seguem o estilo das legendas já existentes nas tabelas (texto curto abaixo da figura ou tabela); as notas metodológicas e a tabela de parâmetros continuam como estão.
- Gráficos: nenhum gráfico novo; as figuras atuais não são alteradas (constituição, Requisito Técnico 5, continua atendido).
- Prazo: fiscalização presencial de 14 a 16/10/2026.

---

## Histórico de revisões

### 2026-10-06 — revisão pela spec 008 (relatório mais enxuto)

| Item | O que mudou | Por quê |
| :--- | :--- | :--- |
| FR-009 | O rodapé do PDF passou a ter só a numeração ("Página X de Y"). Saíram a frase de fontes e a data de geração; a data foi para a capa. | Pedido do usuário em 06/10/2026: cada figura e tabela já cita a sua fonte na legenda, e a frase repetida em todas as páginas virou ruído. |
| FR-010 | O cabeçalho do Markdown não tem mais a linha "**Fontes**:"; passou a ter "**Gerado em**". | Mesmo motivo; o Markdown segue a estrutura do PDF (spec 008). |
| SC-005 | Deixa de se aplicar: o rodapé não cita mais a quantidade de conjuntos. | Consequência da FR-009 revista. |
| Legendas de fonte e conferência, aba `FONTES` | Sem mudança. | Continuam em 100% das figuras e tabelas e em todas as abas. |
