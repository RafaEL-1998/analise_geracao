# Feature Specification: Resumo Executivo do Relatório de Desempenho

**Feature Branch**: `007-resumo-executivo`

**Created**: 2026-10-13

**Status**: Aprovada pelo usuário em 2026-10-13, com a emenda 3.1.0 da constituição

**Input**: User description: "baseado nesse documento, crie uma spec para gerar um resumo executivo de no máximo 2 páginas apresentando os principais pontos de forma resumida com os insights, análises estatísticas importantes e as hipóteses do que pode estar causando problemas. A ideia é conseguir montar um documento em que um diretor/executivo consiga ler de forma resumida tudo que foi descoberto no relatório de 30 pág gerado. Nesse resumo executivo, não precisa de gráficos, no máximo usar tabelas desde que não ultrapasse 2 páginas."

## Contexto

**Esta é uma spec de mudança temporária** (constituição 3.0.0, Governança 2). A mudança atinge:
- a **Geração do relatório**, com o documento novo;
- a **constituição**, que passa a ter o resumo entre os produtos.

As Análises não mudam: o resumo só formata resultados que elas já gravam.

Ao concluir:
- os requisitos passam para `specs/005-geracao-relatorio/`;
- esta pasta é excluída.

**Ponto de partida**
- O fluxo gera, para uma usina, o relatório completo em PDF, Markdown e planilha. O da UHE São Domingos tem 17 seções e cerca de 30 páginas.
- A conclusão (seção 16) reúne os indícios em quatro listas, geradas pelo catálogo de regras C1 a C11: pontos de atenção, possíveis problemas, o que confirmar com o agente e o que verificar em campo.
- O relatório completo é escrito para o fiscal. Um diretor precisa de outra coisa: em poucos minutos, saber o que foi encontrado, o tamanho de cada problema, o que pode estar por trás dele e o que será verificado.

**Exemplo: o que o resumo da São Domingos traria.** Os dados abaixo vêm do relatório de referência de 07/10/2026. No resumo, tudo é gerado a partir dos resultados.

| Bloco do resumo | Conteúdo na São Domingos | Tamanho |
|---|---|---|
| Cabeçalho | UHE São Domingos, MS, Tipo II-A, 48,0 MW; CGT Eletrosul e Axia Sul, cada um com o seu período; período de 28/08/2018 a 28/09/2026; referência ao relatório completo | 4 linhas |
| Indicadores-chave | os cinco indicadores principais da capa: disponibilidade declarada, DISPF, fator de capacidade, EVT e EVT com a usina parada | tabela de 5 linhas |
| Evolução anual | 2018* a 2026*: disponibilidade, fator de capacidade, geração ÷ garantia física, EVT e horas paradas com EVT | tabela de 9 linhas |
| Sobre os dados | cobertura, com 2018 e 2026 parciais; geração e disponibilidade conferidas em 100% das horas; 0,74% dos registros sinalizados; os dados não informam a causa das paradas; fontes | cerca de 220 palavras |
| Conclusão | as quatro listas da seção 16, copiadas iguais: 5 pontos de atenção, 4 possíveis problemas, 5 itens a confirmar com o agente e 5 a verificar em campo | cerca de 600 palavras |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ler em duas páginas o que o relatório completo encontrou (Priority: P1)

Como diretor da AGEMS, quero receber, junto com o relatório completo, um documento de no máximo duas páginas, sem gráficos, com:
- a conclusão do relatório: os indícios, os possíveis problemas, o que será pedido ao agente e o que será verificado em campo;
- os indicadores-chave e a evolução por ano;
- em poucas linhas, até onde os dados vão.

Assim entendo a situação da usina sem ler as 30 páginas e sei em que seção aprofundar.

**Why this priority**: é o pedido central e entrega sozinho o valor esperado.

**Independent Test**: gerar o relatório da São Domingos e conferir:
- o resumo tem no máximo duas páginas A4 e nenhuma figura;
- a conclusão do resumo é igual à do relatório completo;
- cada número das tabelas aparece igual no relatório completo.

**Acceptance Scenarios**:

1. **Given** os resultados das Análises da São Domingos, **When** o relatório é gerado, **Then** o resumo executivo é gerado na mesma execução, em PDF e em Markdown, ao lado do relatório completo, com a mesma data de geração e o mesmo período.
2. **Given** o resumo gerado, **When** o diretor o lê, **Then** encontra os blocos na ordem fixa: cabeçalho, indicadores-chave, evolução anual, "Sobre os dados" e conclusão.
3. **Given** um número de uma tabela do resumo, **When** comparado com o relatório completo, **Then** tem o mesmo valor, a mesma unidade e o mesmo arredondamento.
4. **Given** os resultados já gravados, **When** o fiscal executa só a Geração do relatório, **Then** o relatório e o resumo são gerados juntos, sem refazer as etapas anteriores. Sem os resultados das Análises, a execução para sem gravar nada e indica a etapa a executar.

---

### User Story 2 - Conclusão igual à do relatório completo (Priority: P1)

Como diretor, quero ver no resumo a mesma conclusão do relatório completo, sem reescrita:
- os pontos de atenção;
- os possíveis problemas;
- o que confirmar com o agente;
- o que verificar em campo.

Assim leio exatamente os indícios e as hipóteses que o fiscal vai levar à fiscalização, sem risco de o resumo dizer algo diferente do relatório.

**Why this priority**: são as hipóteses pedidas para o resumo. O usuário decidiu que elas são a conclusão do relatório completo, copiada igual.

**Independent Test**: comparar o bloco de conclusão do resumo da São Domingos com a seção 16 do relatório completo da mesma execução: mesmas listas, mesmos itens, mesma ordem, mesmo texto.

**Acceptance Scenarios**:

1. **Given** a conclusão do relatório completo, **When** o resumo é gerado, **Then** o bloco de conclusão tem a frase de abertura, as listas, os itens, a ordem e o texto da seção de conclusão, caractere por caractere.
2. **Given** uma lista sem itens no relatório completo, **When** o resumo é gerado, **Then** ela também não aparece no resumo.
3. **Given** uma usina em que nenhuma regra da conclusão dispara, **When** o resumo é gerado, **Then** o bloco traz a mesma frase do relatório completo para esse caso.
4. **Given** um item que cita seções, como "(seções 8 e 9)", **When** o diretor lê o resumo, **Then** uma linha logo abaixo do título do bloco informa que as seções e as notas metodológicas citadas são as do relatório completo.

---

### User Story 3 - O mesmo resumo para qualquer tipo de usina (Priority: P2)

Como fiscal, quero que o resumo saia para qualquer tipo de usina que o fluxo atende, com os blocos que o tipo permite. Assim a direção recebe o mesmo formato para uma hidrelétrica, uma térmica ou uma solar.

**Why this priority**: a constituição exige que cada etapa valha para todos os tipos. O valor imediato está na São Domingos, por isso fica atrás das histórias 1 e 2.

**Independent Test**: gerar o resumo das usinas fictícias de cada tipo e conferir:
- os blocos sem base para o tipo foram omitidos;
- os números de conjunto ou de agregado vêm identificados como tais;
- o limite de duas páginas foi respeitado.

**Acceptance Scenarios**:

1. **Given** uma térmica, **When** o resumo é gerado, **Then** os indicadores-chave e a evolução anual são os da térmica, sem nada de energia vertida turbinável, e a conclusão é a do relatório completo da térmica.
2. **Given** uma PCH com dados só do conjunto de usinas, **When** o resumo é gerado, **Then** cada número do conjunto aparece como do conjunto e nunca dividido entre as usinas.

---

### Edge Cases

- **Nenhuma regra da conclusão dispara**: o bloco de conclusão traz a mesma frase do relatório completo para esse caso. Os demais blocos aparecem normalmente.
- **Conteúdo passa de duas páginas**: a conclusão nunca é cortada nem resumida. Sai primeiro a evolução anual, com a remissão à seção de origem; se ainda não couber, a geração acusa erro em vez de entregar um resumo com mais de duas páginas. Fonte e margens nunca ficam abaixo do mínimo.
- **Anos parciais**: aparecem marcados na evolução anual, como no relatório completo.
- **Registros sinalizados**: ficam fora dos extremos citados, como no relatório completo. Na São Domingos, por exemplo, a hora com 68,7 MW, acima da potência instalada, não aparece como geração máxima.
- **Conferência com meta não atingida**: se o fluxo completo for interrompido, o resumo também não é gerado. Se as etapas forem executadas à parte, o resumo omite o que depende da conferência, como o relatório.
- **Mais de um agente no período**: o cabeçalho mostra cada agente com o seu período, como a São Domingos (CGT Eletrosul e Axia Sul).
- **Relatório gerado de novo**: o resumo é sempre gerado de novo junto. Um resumo nunca fica com data ou período diferente do relatório completo ao lado.
- **Blocos sem base**: um bloco que não se aplica à usina é omitido, nunca preenchido com suposição.

## Requirements *(mandatory)*

### Functional Requirements

**Geração e formato**

- **FR-001**: Cada execução que gera o relatório completo de uma usina DEVE gerar também o resumo executivo dela. O resumo usa os mesmos resultados das Análises e tem a mesma data de geração e o mesmo período do relatório.
- **FR-002**: Executar só a Geração do relatório DEVE gerar o relatório e o resumo a partir dos resultados já gravados, sem refazer as etapas anteriores. Não há comando que gere só o resumo, para que ele nunca fique ao lado de um relatório de outra execução. Sem os resultados das Análises, a execução DEVE parar sem gravar nada e indicar a etapa a executar.
- **FR-003**: O resumo DEVE sair em PDF e em Markdown, com o mesmo conteúdo na mesma ordem, na pasta de relatórios da usina, ao lado do relatório completo.
- **FR-004**: O PDF do resumo DEVE ter no máximo duas páginas A4, em retrato. Ele usa a identidade visual do relatório completo, com texto em corpo mínimo de 10 pt e tabelas em corpo mínimo de 9 pt.
- **FR-005**: O resumo NÃO DEVE ter figuras. Pode ter no máximo duas tabelas: os indicadores-chave e a evolução anual.
- **FR-006**: Quando o conteúdo passar de duas páginas, o resumo DEVE omitir a evolução anual, informando a seção de origem no relatório completo. Se ainda não couber, a geração DEVE acusar o erro e não gravar o resumo. A conclusão nunca é cortada, e fonte e margens nunca ficam abaixo do mínimo da FR-004.

**Estrutura**

- **FR-007**: O resumo DEVE ter os blocos nesta ordem fixa:
  1. cabeçalho;
  2. indicadores-chave;
  3. evolução anual;
  4. "Sobre os dados";
  5. conclusão.

  Um bloco sem base para a usina é omitido (constituição II).
- **FR-008**: O **cabeçalho** DEVE trazer:
  - nome, tipo, estado, modalidade de operação e potência da usina;
  - os agentes, cada um com o seu período; nas usinas sem EVT, cujos dados não trazem o histórico dos agentes, o agente atual de cada unidade como a Capacidade de geração do ONS o traz, identificado como tal (decisão do usuário de 19/10/2026);
  - o período analisado e a data de geração;
  - a referência ao relatório completo: título, data e número de páginas.
- **FR-009**: A **conclusão** DEVE ser a da seção de conclusão do relatório completo da mesma execução, copiada igual: a frase de abertura, as listas, os itens, a ordem e o texto, caractere por caractere. O resumo NÃO DEVE resumir, reescrever, reordenar, acrescentar ou retirar itens da conclusão. Uma lista sem itens no relatório completo também não aparece no resumo.
- **FR-010**: Logo abaixo do título da conclusão, o resumo DEVE informar, numa linha, que as seções e as notas metodológicas citadas são as do relatório completo.
- **FR-011**: Os **indicadores-chave** DEVEM ser os indicadores principais da capa do relatório completo para o tipo da usina, em uma tabela, com o valor e, quando houver, a referência e a diferença para ela, sem juízo.
- **FR-012**: A **evolução anual** DEVE ser uma tabela com uma linha por ano e no máximo seis colunas, com os indicadores anuais do tipo da usina. Na UHE: disponibilidade, fator de capacidade, geração ÷ garantia física, EVT e horas paradas com EVT. Os anos parciais vêm marcados. A tabela indica a seção de origem no relatório completo.
- **FR-013**: **"Sobre os dados"** DEVE ter no máximo 250 palavras, com:
  - a cobertura e os anos parciais;
  - o resultado resumido das conferências;
  - a quantidade e a parcela de registros sinalizados;
  - o que os dados não informam, como a causa das paradas e os eventos individuais;
  - numa linha, as fontes: os conjuntos do ONS e as datas de obtenção.

  Esse bloco substitui a legenda de fonte de cada tabela.

**Fidelidade e linguagem**

- **FR-014**: Todo número do resumo DEVE ser idêntico, em valor, unidade e arredondamento, a um número do relatório completo. O resumo NÃO DEVE trazer número que não esteja no relatório completo.
- **FR-015**: Nenhum nome, número ou frase própria de uma usina DEVE ficar fixo. Tudo vem dos resultados, do perfil da usina e das regras gerais (constituição II).
- **FR-016**: Todo número de conjunto de usinas ou de agregado DEVE vir identificado pelo nível em que é publicado. Nenhum número de conjunto é apresentado como da usina (constituição VIII).
- **FR-017**: Fora da conclusão, que é copiada igual, o texto do resumo DEVE ser legível por quem não é especialista em operação:
  - siglas por extenso na primeira ocorrência;
  - uma linha de termos que explica as grandezas técnicas citadas, como a energia vertida turbinável;
  - frases curtas, na voz ativa.
- **FR-018**: Os números DEVEM seguir o padrão do relatório completo: milhar com ponto, decimal com vírgula, datas "dd/mm/aaaa HHh", meses "mmm/aaaa" e "–" para valor ausente.

**Tipos de usina e referência**

- **FR-019**: O resumo DEVE ser gerado para todos os tipos de usina que o fluxo atende. Cada tipo usa os seus indicadores-chave, os seus indicadores anuais e a conclusão do seu relatório completo.
- **FR-020**: O resumo aprovado pelo usuário DEVE passar a fazer parte da referência da usina. A comparação dos relatórios de referência DEVE incluir o resumo (constituição IX).
- **FR-021**: O relatório completo e a planilha NÃO DEVEM mudar com esta mudança. A comparação com a referência da São Domingos não pode acusar diferença neles.

### Ajustes previstos na constituição e nas specs das etapas

| Documento | Ajuste |
|---|---|
| Constituição (MINOR, 3.0.0 → 3.1.0) | inclui o resumo executivo entre os produtos; em VII, aceita no resumo o bloco único de fontes ("Sobre os dados") no lugar da legenda por tabela, com a seção de origem em cada tabela |
| `specs/005-geracao-relatorio/` | o produto "resumo executivo": estrutura, conclusão copiada igual, limite de duas páginas, formatos, omissão da evolução anual quando não couber, fontes e inclusão na comparação de referência |
| `specs/004-analises/` | nenhum: o resumo usa só resultados que as Análises já gravam |

### Key Entities

- **Resumo executivo**: o documento de até duas páginas de uma usina, gerado junto com o relatório completo e com a mesma data e o mesmo período. É formado pelos blocos da FR-007.
- **Conclusão**: as quatro listas da seção de conclusão do relatório completo. No resumo, aparecem copiadas iguais.
- **Indicadores-chave**: os indicadores principais da capa do relatório completo para o tipo da usina.
- **Evolução anual**: os indicadores anuais do tipo da usina, um ano por linha.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos resumos gerados têm no máximo duas páginas A4 e nenhuma figura. Isso vale para a São Domingos, para as usinas fictícias de cada tipo e para o caso de teste com cinco itens em cada lista da conclusão.
- **SC-002**: 100% das conclusões dos resumos são iguais, caractere por caractere, às dos relatórios completos da mesma execução, por verificação automática.
- **SC-003**: 100% dos números das tabelas e do texto do resumo conferem com o relatório completo da mesma execução, em valor, unidade e arredondamento, por verificação automática.
- **SC-004**: O resumo é lido em até 5 minutos: no máximo 1.000 palavras fora das tabelas.
- **SC-005**: Só com o resumo da São Domingos, um leitor que não leu o relatório completo responde a cinco perguntas:
  - quais são os principais indícios;
  - qual o tamanho de cada um;
  - desde quando ocorrem;
  - o que pode estar por trás deles;
  - o que será pedido ou verificado.

  O usuário aprova o resumo como representação fiel do relatório de referência.
- **SC-006**: A comparação com a referência da São Domingos não acusa diferença no relatório completo nem na planilha.

## Decisões do usuário

- **2026-10-13, Q1 — hipóteses do resumo**: as hipóteses do resumo executivo são a conclusão do relatório completo, copiada igual. Não há catálogo de hipóteses próprio do resumo.
- **2026-10-13, ajustes do plano**: aprovados o A1 (FR-002 e cenário 4 da US1: sem comando só do resumo; a Geração do relatório gera os dois) e o A2 (FR-013: "Sobre os dados" com no máximo 250 palavras, porque a constituição 3.1.0 exige nele as mesmas informações de fonte e de conferência das legendas).
- **2026-10-13, revisão 1 — ordem dos blocos**: depois de ver o resumo da São Domingos ("ficou EXCELENTE!"), o usuário pediu a conclusão por último. A ordem passa a ser cabeçalho, indicadores-chave, evolução anual, "Sobre os dados" e conclusão (FR-007 e cenário 2 da US1).
- **2026-10-19, agentes nas usinas sem EVT (T043)**: o cabeçalho mostra o agente atual (proprietário e operador) das unidades ativas, da Capacidade de geração, identificado como "Agente atual (Capacidade de geração do ONS)", também na capa do relatório completo (FR-008).
- **2026-10-19, encerramento**: a incorporação à spec 005 e a exclusão desta pasta (T037 e T038) ficam para o fechamento da spec 006 (fase F), junto com os ajustes da 006 na spec 005, para que a spec 005 seja editada uma vez só.
- **2026-10-13, início da implementação**: o usuário pediu a implementação antes do portão da fase A da 006 (ajuste da decisão R13 do plano). A conferência de que o relatório completo não muda passa a ser feita contra o relatório gerado pelo código de antes da mudança.

## Assumptions

- **Leitor**: diretor ou executivo da AGEMS, sem formação específica em operação de usinas, que lê o resumo em PDF ou impresso.
- **Ordem dos blocos** (revisão 1, decisão do usuário): primeiro os números (indicadores, evolução anual e limites dos dados), depois a conclusão, que fecha o documento, como no relatório completo. A linha de termos continua no cabeçalho, antes de todos os blocos.
- **Sem bloco de mensagens-chave nem de próximos passos**: os pontos de atenção da conclusão já são os principais achados, com os números. As listas "A confirmar com o agente" e "A verificar em campo" já são os próximos passos. Blocos à parte repetiriam a conclusão e ocupariam o espaço das duas páginas.
- **Página**: A4 em retrato, com a identidade visual do relatório completo.
- **Formatos**: PDF e Markdown, como o relatório completo. Word e planilha própria do resumo ficam fora.
- **Origem automática**: o resumo é gerado inteiramente pelo fluxo. Não há campo de texto livre do fiscal, porque a constituição (II) exige que todo texto venha dos dados, do perfil ou das regras gerais.
- **Relatório de carteira**: fica fora desta mudança e pode ganhar um resumo próprio em mudança futura.
- **Idioma**: português do Brasil.
- **Constituição**: a emenda MINOR 3.1.0 descrita acima foi aprovada pelo usuário e aplicada em 2026-10-13.
- **Spec 006**: na fase A, a spec 006 refaz a estrutura do relatório e os indicadores da capa por tipo de usina, que o resumo reaproveita. Por isso, a implementação desta mudança começa depois dessa fase. O plano e as tarefas podem ser feitos antes.
