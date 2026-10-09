# Feature Specification: Relatórios de Desempenho para Todos os Tipos de Usina com Dados Abertos do ONS

**Feature Branch**: `006-ampliacao-tipos-de-geracao`

**Created**: 2026-10-09

**Status**: Aprovada pelo usuário em 2026-10-09, com os ajustes do plano

**Input**: User description: "meu sonho é que esse projeto possa virar uma ferramenta que acessa (download) dos dados da ONS e conseguirmos ter esses relatórios estatísticos de térmicas, UHE, PCH, CGH, Eólicas, GD, todas as frentes de geração que tenham nos dados, VAMOS ELEVAR O NÍVEL. [...] faça a nova constitution que aborde todos esses temas, e depois o plano para implantação conforme agentes speckit"

## Contexto

**Esta é uma spec de mudança temporária** (constituição 3.0.0, Governança 2). Ela organiza uma mudança que atinge as cinco etapas. Ao concluir:
- os requisitos passam para as specs das etapas (`specs/001-coleta-dados/` a `specs/005-geracao-relatorio/`);
- esta pasta é excluída.

**Ponto de partida**
- O fluxo de cinco etapas gera o relatório de uma usina hidrelétrica.
- O relatório da UHE São Domingos foi aprovado pelo usuário. A referência dele está em `_backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base/`.
- A constituição 3.0.0, de 09/10/2026, ampliou o escopo para todos os tipos de usina cobertos pelos dados abertos do ONS. Ela também criou dois princípios: granularidade declarada (VIII) e relatórios aprovados protegidos (IX).

**O que os dados do ONS cobrem**

Fontes: cadastro do ONS (Modalidade das usinas, 6.017 linhas, 171 em MS) e geração de setembro de 2026.

| Tipo | Nível em que o ONS publica | Conjuntos próprios do tipo |
|---|---|---|
| UHE | da usina (Tipo I, II-A e II-B) | Energia Vertida Turbinável, Dados hidrológicos horários |
| UTE e UTN | da usina (Tipo I, II-A e II-B); indicadores DISPF e TEIFa/TEIP de 87 a 95 UTE e das 2 UTN | geração térmica por motivo de despacho, CVU, CMO semanal |
| EOL e UFV | da usina nos conjuntos de restrição por constrained-off (eólica desde 10/2021); geração e fator de capacidade, em geral pelo conjunto de usinas (Tipo II-C) | restrição por constrained-off por usina e, com a razão da restrição, pela usina ou pelo conjunto; fator de capacidade; composição dos conjuntos |
| PCH e CGH | pelo conjunto de usinas (Tipo II-C), com a geração da usina vazia; a maioria é Tipo III e só tem agregado | composição dos conjuntos |
| MMGD e Tipo III | só agregado, em grupos por área, por exemplo "PQU MSMS MMGD", com 305,5 GWh em set/2026 | — |

**Usinas piloto**, escolhidas pela cobertura dos dados:

| Tipo | Usina | Estado | Identificadores | Modalidade |
|---|---|---|---|---|
| UHE | São Domingos | MS | perfil existente | Tipo II-A; já aprovada |
| UTE | William Arjona | MS | CEG `UTE.GN.MS.027075-0.01`, id ONS `MSUTWI` | Tipo I |
| UFV | Seriemas 1 | MS | CEG `UFV.RS.MS.052257-0.01`, id ONS `MSSRI1` | conjunto Inocência 230 kV |
| EOL | Praia Formosa | CE | CEG `EOL.CV.CE.028631-1.01`, id ONS `CEUFM` | Tipo I |
| PCH | Bandeirante | MS | CEG `PCH.PH.MS.032163-0.01`, id ONS `MSBDT` | Tipo II-C |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Escolher qualquer usina e obter o relatório com as seções comuns (Priority: P1)

Como fiscal da AGEMS, quero:
- consultar um catálogo com as usinas de um estado, o tipo de cada uma e o que o ONS publica sobre ela;
- gerar o rascunho do perfil de uma usina a partir do cadastro;
- conferir e completar o rascunho com os parâmetros técnicos;
- obter o relatório da usina com as seções que valem para qualquer tipo.

Assim começo a análise de uma térmica, eólica, solar ou PCH sem escrever o perfil do zero e sem mexer no código.

**Why this priority**: é a fundação de todas as outras histórias e já entrega valor sozinha. Uma térmica ou uma solar já passa a ter relatório de geração, disponibilidade, programação, indicadores oficiais e conclusão comum. A história inclui as correções pendentes da Coleta, que afetam qualquer usina nova.

**Independent Test**:
- listar as usinas de MS;
- gerar o perfil da UTE William Arjona, completar os parâmetros e executar o fluxo completo;
- conferir que o relatório tem só as seções comuns, cada número com o nível dele;
- conferir que o relatório da São Domingos continua igual à referência.

**Acceptance Scenarios**:

1. **Given** os dados do ONS, **When** o fiscal pede o catálogo de MS, **Then** vê as 171 entradas do cadastro do estado, cada uma com:
   - nome, CEG, id ONS, tipo, modalidade, potência autorizada e conjunto de usinas;
   - para cada conjunto do ONS usado no projeto, se a usina tem dado próprio, só pelo conjunto, só em agregado ou nenhum.
2. **Given** a UTE William Arjona no catálogo, **When** o fiscal gera o perfil pelo CEG, **Then** o rascunho traz tipo, modalidade, nome, estado e os identificadores achados nos conjuntos do ONS. Os parâmetros técnicos ficam pendentes, cada um pedindo a fonte.
3. **Given** um perfil em rascunho, **When** o fiscal executa qualquer etapa, **Then** a execução é recusada antes da coleta, com a lista do que falta conferir ou preencher.
4. **Given** o perfil conferido de uma térmica, **When** o fluxo completo é executado, **Then** o relatório tem as seções comuns e nenhuma seção de energia vertida turbinável ou de hidrologia.
5. **Given** os dados da São Domingos, **When** o fluxo completo é executado depois da mudança, **Then** a comparação com a referência não acusa diferença.
6. **Given** uma usina Tipo III ou uma CGH sem dado próprio no ONS, **When** o fiscal tenta gerar o perfil, **Then** nenhum perfil é criado, e a mensagem explica que o ONS só publica o agregado e onde ele aparece (relatório de carteira).

---

### User Story 2 - Relatório completo de térmica e nuclear (Priority: P2)

Como fiscal, quero que o relatório de uma térmica mostre:
- como ela foi despachada: por ordem de mérito, inflexibilidade, restrição elétrica e outros motivos publicados;
- se atendeu ao despacho;
- quanto tempo ficou disponível sem ser despachada;
- como o custo variável (CVU) se compara ao custo marginal de operação (CMO);
- onde está a indisponibilidade forçada, unidade por unidade.

Assim preparo a fiscalização de uma térmica com o mesmo rigor da hidrelétrica.

**Why this priority**: as térmicas têm a cobertura mais completa depois das hidrelétricas, com indicadores oficiais por unidade, e incluem a usina citada pelo usuário.

**Independent Test**: executar o fluxo para a UTE William Arjona e conferir as seções próprias de térmica, a conclusão com as regras de térmica e as conferências aplicáveis.

**Acceptance Scenarios**:

1. **Given** a geração por motivo de despacho da usina, **When** o relatório é gerado, **Then** ele mostra a geração de cada motivo por mês e por ano e a parcela de cada motivo no total.
2. **Given** a geração programada e a verificada, **When** as horas são comparadas, **Then** o relatório mostra as horas e a energia abaixo e acima do despacho, os maiores desvios e as horas disponíveis sem despacho.
3. **Given** o CVU semanal e o CMO do subsistema, **When** o relatório é gerado, **Then** ele mostra, por semana, se o CVU ficou abaixo ou acima do CMO e a geração em cada caso, sem julgar o despacho.
4. **Given** os indicadores DISPF e TEIFa/TEIP da usina, **When** a Conferência é executada, **Then** as taxas são refeitas como nas hidrelétricas, e as divergências ficam registradas.
5. **Given** uma térmica sem geração no período, **When** o relatório é gerado, **Then** não há divisão por zero. A constatação diz que a usina ficou disponível e não foi despachada, com as horas e a potência disponível.

---

### User Story 3 - Relatório completo de eólica e solar (Priority: P3)

Como fiscal, quero ver, para uma eólica ou solar:
- o fator de capacidade;
- a energia cortada por restrição de operação (constrained-off), com o tipo de restrição;
- a relação entre o recurso (vento ou irradiância) e a geração;
- a aderência à programação.

Cada número vem identificado como da usina ou do conjunto. Assim avalio as usinas que mais crescem em MS.

**Why this priority**: são 86 usinas solares em MS. Os dados vêm quase sempre por conjunto, o que pede a regra de granularidade bem resolvida antes.

**Independent Test**: executar o fluxo para a UFV Seriemas 1 e para a EOL Praia Formosa e conferir as seções próprias, a granularidade de cada número e a conclusão com as regras do tipo.

**Acceptance Scenarios**:

1. **Given** a série da usina nos conjuntos de restrição, **When** o relatório é gerado, **Then** ele mostra:
   - a geração verificada e a estimada sem restrição;
   - a energia cortada por mês e por tipo de restrição;
   - as horas restritas.
2. **Given** a geração e o fator de capacidade publicados só para o conjunto, **When** o relatório é gerado, **Then** esses números aparecem como do conjunto, com as usinas que o compõem, e nunca divididos entre elas.
3. **Given** dados de vento com a marca de inválido do ONS, **When** a relação vento × geração é calculada, **Then** essas horas ficam fora e são contadas.
4. **Given** a geração programada e a verificada da usina ou do conjunto, **When** comparadas, **Then** o relatório mostra o desvio médio e os maiores desvios.

---

### User Story 4 - PCH e CGH com a granularidade que os dados permitem (Priority: P4)

Como fiscal, quero o relatório de uma PCH em conjunto de usinas, com:
- os números do conjunto identificados como tais;
- a composição do conjunto;
- o aviso claro do que o ONS não publica sobre a usina isolada.

Assim não tiro conclusão de dado que não existe.

**Why this priority**: a maioria das PCH e todas as CGH de MS são Tipo III. Mesmo as PCH em conjunto têm a geração da usina vazia no ONS, então o ganho é menor que nas outras histórias.

**Independent Test**: executar o fluxo para a PCH Bandeirante e conferir que o relatório usa só dados do conjunto, com a composição e a explicação nas notas.

**Acceptance Scenarios**:

1. **Given** a PCH Bandeirante, **When** o relatório é gerado, **Then** as séries de geração aparecem como do conjunto. As notas explicam que o ONS não publica a geração da usina isolada.
2. **Given** uma seção comum sem base no nível da usina, **When** o relatório é gerado, **Then** a seção é omitida e o motivo aparece nas notas.

---

### User Story 5 - Relatório de carteira do estado (Priority: P5)

Como fiscal, quero um relatório que reúna as usinas de MS, ou de um tipo, com:
- a cobertura de dados de cada uma;
- indicadores comparáveis;
- as usinas ordenadas pela quantidade de indícios da conclusão de cada uma;
- o panorama das pequenas usinas e da MMGD do estado.

Assim escolho onde fiscalizar.

**Why this priority**: depende dos relatórios por usina das histórias anteriores. É o produto que leva a ferramenta do caso a caso para a gestão da fiscalização.

**Independent Test**: com os resultados gravados das usinas piloto de MS, gerar a carteira de MS. Conferir que ela não refaz etapas, lista as usinas sem resultado e não atribui nota nem parecer.

**Acceptance Scenarios**:

1. **Given** os resultados gravados das usinas de MS, **When** a carteira de MS é gerada, **Then** ela traz:
   - o quadro das usinas, com tipo, modalidade, potência e cobertura;
   - os indicadores comparáveis por tipo;
   - a ordenação pelos itens de "Possíveis problemas" e "Pontos de atenção";
   - a lista das usinas do estado sem resultado.
2. **Given** os grupos de pequenas usinas e de MMGD do estado, **When** a carteira é gerada, **Then** eles aparecem num panorama agregado, por tipo e por mês, identificados como agregado.
3. **Given** qualquer texto da carteira, **When** ele é conferido, **Then** não há "satisfatório", "insatisfatório", "cumpre", "descumpre", nota nem equivalente.

---

### Edge Cases

- **Usina que mudou de modalidade ou de conjunto no período** (por exemplo, de Tipo II-C para Tipo I): o período é dividido nos trechos de cada modalidade, e o relatório diz em que nível está cada trecho.
- **Identificador ausente no cadastro** (id ONS vazio, como em parte das solares de MS): o rascunho do perfil traz o que existe e lista o que falta. A usina só segue com os identificadores confirmados pelo fiscal.
- **Nomes parecidos** (por exemplo, "UT WILL. ARJONA" e "UHE UHE WILLY FALLE"): a identificação é sempre pelos códigos, nunca pelo nome.
- **Classificação ou identificador instável no ONS** (por exemplo, um conjunto hidráulico publicado como térmico, ou os grupos de MMGD sem id ONS desde 05/2026): o tipo vem do CEG e da composição do conjunto, e os agregados são selecionados pelo estado e pela modalidade. A divergência vai para a qualidade dos dados.
- **Conjunto com usinas de tipos diferentes**: os números do conjunto aparecem como do conjunto, com a composição por tipo.
- **Conjunto cuja composição mudou no período** (por exemplo, térmicas que saíram de um conjunto de PCH): os números do conjunto são apresentados por trecho de composição, com as usinas de cada trecho.
- **Usina nuclear**: segue as seções de térmica.
- **Térmica com mais de uma unidade de planejamento ou com o código trocado no tempo** (por exemplo, uma unidade por combustível): o perfil traz cada código com o período. A geração da usina é a soma das unidades, e o CVU é mostrado por unidade.
- **Usina com série de referência mais curta que a dos outros conjuntos** (restrição eólica desde 10/2021): o período é o da série de referência, e os outros conjuntos são recortados nele.
- **Série de referência com menos de 12 meses** (caso das solares de MS, publicadas por usina desde 08/2026): as seções e as regras da conclusão que pedem um ano ou mais são omitidas, com o motivo nas notas.
- **Séries semi-horárias e horárias juntas**: as semi-horárias são tratadas na sua resolução e levadas à hora pela média de potência para os cruzamentos.
- **Usina sem nenhum resultado gravado na carteira**: ela aparece na lista de usinas sem resultado, nunca com valores estimados.
- **Perfil existente quando se pede um rascunho novo**: nada é sobrescrito. O comando mostra as diferenças entre o perfil e o cadastro.
- **Diferença no relatório de uma usina já aprovada**: a fase não termina até o usuário aprovar a diferença ou o código ser corrigido.

## Requirements *(mandatory)*

### Functional Requirements

**Escopo**

- **FR-001**: O fluxo DEVE atender usinas dos tipos UHE, PCH, CGH, UTE, UTN, EOL e UFV que tenham dado próprio ou de conjunto no ONS. A MMGD e as usinas Tipo III DEVEM aparecer só como panorama agregado, na carteira. Relatório por usina de geração distribuída ou de usina Tipo III está fora do escopo.
- **FR-002**: O tipo e a modalidade da usina DEVEM definir os conjuntos coletados, as conferências, as seções do relatório e as regras da conclusão. A spec de cada etapa DEVE ter a tabela de aplicabilidade por tipo.

**Catálogo de usinas (US1)**

- **FR-003**: O comando `python -m src usinas [--estado <UF>] [--tipo <tipo>] [--modalidade <modalidade>]` DEVE listar as usinas do cadastro do ONS. Para cada usina:
  - nome, CEG, id ONS, tipo, modalidade, estado, potência autorizada e conjunto de usinas;
  - a cobertura de cada conjunto do ONS usado no projeto: dado próprio, pelo conjunto, agregado ou ausente.
- **FR-004**: O catálogo DEVE ser gravado em `data/catalogo/`, com:
  - a data do cadastro usado e a data da verificação da cobertura de cada conjunto;
  - o arquivo do conjunto que serviu à verificação.
- **FR-005**: A montagem do catálogo é parte da Coleta. Ela DEVE reaproveitar os arquivos já baixados e baixar só o que é novo ou mudou.

**Perfil (US1)**

- **FR-006**: O comando `python -m src perfil --ceg <CEG> [--slug <slug>]` DEVE criar `usinas/<slug>/perfil.toml` em rascunho, com:
  - tipo, modalidade, nome, nome curto, estado e conjunto de usinas;
  - os identificadores de extração e de conferência achados nos conjuntos do tipo;
  - os parâmetros técnicos marcados como pendentes, cada um com o campo de fonte.
- **FR-007**: O comando NÃO DEVE sobrescrever um perfil existente. Nesse caso, mostra as diferenças entre o perfil e o cadastro.
- **FR-008**: Um perfil em rascunho DEVE ser recusado por qualquer etapa (código 4), com a lista do que falta. Ele só segue depois de marcado como conferido pelo fiscal.
- **FR-009**: Para usina sem dado próprio nem de conjunto no ONS, o comando NÃO DEVE criar perfil. Ele explica que o ONS só publica agregado e indica o panorama da carteira.
- **FR-010**: O perfil DEVE ter os campos comuns a todos os tipos (os de hoje, mais tipo e modalidade) e os campos próprios do tipo, cada parâmetro técnico com fonte e data:

  | Tipo | Campos próprios obrigatórios |
  |---|---|
  | UHE | os de hoje: unidades e potência unitária, turbina, engolimento, garantia física, IP e TEIF de referência, queda, perda hidráulica, rendimento, vazão remanescente, vertimento mínimo e faixas de geração |
  | PCH e CGH | potência e unidades; os campos de UHE só quando a usina tiver série própria de energia vertida turbinável ou de hidrologia |
  | UTE e UTN | potência e unidades, combustível; garantia física e IP e TEIF de referência, quando houver |
  | EOL e UFV | capacidade instalada e conjunto de usinas; garantia física, quando houver |

- **FR-011**: O perfil da São Domingos DEVE ganhar só o tipo (UHE) e a modalidade (Tipo II-A), sem mudar o relatório dela.

**Período e coleta (US1 a US4)**

- **FR-012**: O período da análise DEVE ser o da série de referência do tipo e da modalidade:

  | Tipo e modalidade | Série de referência |
  |---|---|
  | UHE, PCH ou CGH com Energia Vertida Turbinável | a energia vertida turbinável (como hoje) |
  | UTE, UTN e demais usinas com geração própria | a geração verificada da usina |
  | EOL e UFV em conjunto | a série da própria usina nos conjuntos de restrição por constrained-off; sem ela, a do conjunto |
  | PCH e CGH em conjunto | a geração do conjunto |

- **FR-013**: A Coleta DEVE obter, além dos conjuntos de hoje, os conjuntos próprios de cada tipo. Cada um tem o identificador de extração e o campo de conferência declarados na spec da Coleta:

  | Conjunto do ONS | Tipos |
  |---|---|
  | Geração térmica por motivo de despacho | UTE, UTN |
  | CVU das usinas térmicas | UTE, UTN |
  | CMO semanal (contexto do subsistema) | UTE, UTN |
  | Fator de capacidade | EOL, UFV |
  | Restrição por constrained-off com detalhe por usina, eólica e fotovoltaica | EOL, UFV |
  | Restrição por constrained-off com a razão da restrição, eólica e fotovoltaica (pela usina ou pelo conjunto) | EOL, UFV |
  | Composição dos conjuntos de usinas | todos os tipos em conjunto |
  | Capacidade de geração, por unidade geradora | todos os tipos, no catálogo e no rascunho do perfil |

- **FR-014**: A Coleta DEVE corrigir os defeitos que só aparecem com outras usinas:
  - recursos repetidos no catálogo tratados em todos os conjuntos, sem downloads simultâneos no mesmo arquivo temporário;
  - vírgula decimal aceita em todos os conjuntos;
  - códigos e nomes normalizados igualmente na extração e no pré-filtro;
  - coluna de conferência ausente tratada como falha do arquivo;
  - CSV vazio da energia vertida turbinável com o motivo na auditoria.
- **FR-015**: A Coleta DEVE baixar só os conjuntos do tipo da usina e os arquivos que se sobrepõem ao período, além dos conjuntos comuns.

**Tratamento (US2 a US4)**

- **FR-016**: As séries semi-horárias DEVEM ser tratadas na sua resolução e levadas à hora pela média de potência, para os cruzamentos com as séries horárias.
- **FR-017**: O Tratamento DEVE sinalizar, sem descartar:
  - o vento marcado como inválido pelo ONS;
  - o fator de capacidade fora de 0 a 1;
  - a geração acima da capacidade instalada;
  - o CVU ausente ou negativo.

**Conferência (US2 a US4)**

- **FR-018**: A Conferência DEVE comparar, sempre no mesmo nível (usina com usina, conjunto com conjunto), as bases que trazem a mesma grandeza:
  - a geração verificada da usina em Geração por usina e nos conjuntos de fator de capacidade ou de restrição (EOL, UFV);
  - a soma das usinas do conjunto e a geração do conjunto, quando as duas existem;
  - a geração programada da programação diária e a do despacho térmico (UTE, UTN);
  - a geração verificada do despacho térmico e a da Geração por usina (UTE, UTN);
  - a geração programada da programação diária e a do fator de capacidade (EOL, UFV);
  - o DISPF com as horas por estado operativo e a TEIFa e a TEIP refeitas (UTE, UTN, como nas UHE).
- **FR-019**: Uma conferência sem base para o tipo, a modalidade ou o nível dos dados da usina DEVE ser registrada como não aplicável, com o motivo.

**Análises e conclusão (US1 a US4)**

- **FR-020**: As Análises DEVEM calcular, para todos os tipos, as seções comuns:
  - identificação e cadastro;
  - geração (série, perfil por hora do dia, sazonalidade e anos);
  - disponibilidade e indisponibilidade, quando o ONS publica;
  - indicadores oficiais por unidade, quando houver;
  - programação comparada com a geração verificada;
  - qualidade dos dados.
- **FR-021**: As Análises DEVEM calcular as seções próprias de cada tipo:

  | Tipo | Seções próprias |
  |---|---|
  | UHE | as de hoje: energia vertida turbinável, usina parada, hidrologia e afluência |
  | UTE e UTN | geração por motivo de despacho, inflexibilidade, atendimento ao despacho, horas disponíveis sem despacho, CVU comparado com o CMO |
  | EOL e UFV | fator de capacidade, energia cortada por tipo de restrição, recurso (vento ou irradiância) comparado com a geração, aderência à programação |
  | PCH e CGH em conjunto | geração do conjunto e composição |

- **FR-022**: A conclusão DEVE usar as regras comuns a todos os tipos e as regras próprias do tipo, declaradas em catálogo, com os limiares nas notas metodológicas. Uma regra só é avaliada com dados do nível da usina. Ela mantém as quatro listas de hoje, com no máximo 5 itens cada. Exemplos de regra:
  - comum: indisponibilidade forçada recorrente;
  - UTE: geração abaixo do despacho em horas recorrentes;
  - UFV: energia cortada acima de um limiar do total estimado.
- **FR-023**: Cada número calculado DEVE levar o nível dele (usina, conjunto ou agregado). Nenhum número de conjunto DEVE ser dividido entre as usinas.

**Relatório (US1 a US4)**

- **FR-024**: O relatório de cada usina DEVE ter:
  - a capa de hoje, com o tipo e a modalidade;
  - as seções comuns e as próprias do tipo, numeradas em ordem fixa;
  - a conclusão e as notas metodológicas.

  Seção sem base é omitida, com o motivo nas notas. A legenda de cada figura e tabela DEVE identificar o nível do dado pelo identificador que cita: o da usina ou, num dado de conjunto ou de agregado, o identificador dele com o nível escrito.
- **FR-025**: Os textos do relatório NÃO DEVEM ter nome, identificador ou valor de usina que não venha do perfil ou dos dados, em nenhum tipo.

**Relatório de carteira (US5)**

- **FR-026**: O comando `python -m src carteira [--estado <UF>] [--tipo <tipo>]`, com pelo menos uma das duas opções, DEVE gerar o relatório de carteira em `reports/carteiras/<nome>/` (PDF, Markdown e planilha):
  - a partir dos resultados já gravados das usinas do recorte, sem refazer nenhuma etapa;
  - com a lista das usinas do recorte que não têm resultado.
- **FR-027**: A carteira DEVE trazer:
  - o quadro das usinas, com tipo, modalidade, potência e cobertura de dados;
  - os indicadores comparáveis de cada tipo: fator de capacidade, disponibilidade, indisponibilidade forçada, energia cortada e atendimento ao despacho, quando aplicáveis;
  - a ordenação das usinas pela quantidade de itens em "Possíveis problemas" e, no empate, em "Pontos de atenção";
  - o panorama agregado das pequenas usinas e da MMGD do estado, por tipo e por mês.

  Ela NÃO DEVE atribuir nota nem parecer.

**Proteção, fases e encerramento (todas as histórias)**

- **FR-028**: A implementação DEVE seguir as histórias em ordem de prioridade (US1 a US5). Ela só começa com a versão de fiscalização da São Domingos congelada numa pasta fora do projeto, com o próprio código, os próprios dados e o relatório aprovado, e conferida: o fluxo completo dela reproduz o relatório aprovado sem diferença. Essa versão é a usada na fiscalização de 14 a 16/10/2026. Cada fase:
  - começa com uma cópia de segurança do projeto;
  - termina com a convergência do Spec Kit e com a comparação de todos os relatórios de referência sem diferença não aprovada.
- **FR-029**: O relatório de cada usina piloto aprovado pelo usuário DEVE passar a ser a referência dela, guardado junto às cópias de segurança.
- **FR-030**: Ao concluir a mudança:
  - os requisitos desta spec DEVEM estar nas specs das cinco etapas, com as tabelas de aplicabilidade por tipo;
  - o README descreve todos os tipos;
  - esta spec de mudança é excluída, e `specs/` volta a ter só as cinco specs das etapas.

### Key Entities

- **Catálogo de usinas**: as usinas do cadastro do ONS, com tipo, modalidade, estado, potência, conjunto e a cobertura de cada conjunto do ONS, além da data do cadastro e da verificação.
- **Cobertura**: para uma usina e um conjunto do ONS, o nível em que o conjunto a cobre (próprio, conjunto, agregado ou ausente).
- **Perfil da usina**: os campos de hoje, mais tipo, modalidade, conjunto de usinas, campos próprios do tipo e situação (rascunho ou conferido).
- **Série de referência**: a série que define o período da análise, conforme o tipo e a modalidade.
- **Seção do relatório**: comum a todos os tipos ou própria de um tipo, com as condições de omissão.
- **Regra da conclusão**: comum ou própria de um tipo, com limiar declarado.
- **Relatório de carteira**: as usinas de um estado ou tipo, com indicadores comparáveis, ordenação por indícios e panorama agregado.
- **Usina piloto**: a usina de validação de cada tipo, cujo relatório aprovado vira referência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O relatório da UHE São Domingos fica sem nenhuma diferença em relação à referência ao fim de cada fase. Uma diferença só é aceita se aprovada pelo usuário.
- **SC-002**: O catálogo de MS lista 100 % das 171 entradas do cadastro do ONS para o estado, cada uma com tipo, modalidade e cobertura dos conjuntos usados. O catálogo do Brasil lista 100 % das linhas do cadastro.
- **SC-003**: O rascunho do perfil de uma usina com dado próprio sai em menos de 1 minuto, com 100 % dos identificadores que o ONS publica para ela. O fiscal completa só os parâmetros técnicos e a conferência.
- **SC-004**: Cada uma das quatro usinas piloto novas tem o relatório completo gerado pelo fluxo, com zero valores de outra usina, e o relatório é aprovado pelo usuário. Todo número de conjunto ou de agregado aparece identificado como tal.
- **SC-005**: Cada um dos sete tipos tem uma usina fictícia testada de ponta a ponta, sem rede e sem valores de usina real no código.
- **SC-006**: Com os dados já baixados, o fluxo completo de uma usina piloto termina em até 15 minutos. A carteira de MS sai em até 5 minutos a partir dos resultados gravados.
- **SC-007**: Nenhum termo de parecer ("satisfatório", "insatisfatório", "cumpre", "descumpre" e equivalentes) aparece nos relatórios piloto nem na carteira.
- **SC-008**: Ao fim da mudança, `specs/` tem exatamente as cinco specs das etapas, e nenhum arquivo do projeto cita esta spec de mudança.

## Decisões do usuário

| Data | Decisão | Onde se aplica |
|---|---|---|
| 08/10/2026 | Transformar o projeto numa ferramenta de relatórios para todas as frentes de geração que os dados do ONS cobrem ("VAMOS ELEVAR O NÍVEL"). | FR-001, todas as histórias |
| 08/10/2026 | O relatório da São Domingos está impecável e não pode mudar; cópia de segurança antes da ampliação. | FR-011, FR-028, SC-001 |
| 08/10/2026 | Os defeitos da Coleta que só afetam outras usinas (P1 a P5) são corrigidos depois da fiscalização. | FR-014, FR-028 |
| 09/10/2026 | Constituição 3.0.0 com todos os temas da proposta; plano de implantação pelo fluxo do Spec Kit. | todo o documento |
| 09/10/2026 | Aprovados a constituição 3.0.0 (com a redação do princípio VIII sobre a MMGD), esta spec com os ajustes do plano (research, R25) e o plano. A UFV Seriemas 1 continua como piloto de MS, mesmo com a série curta. Nenhuma coleta com o portal até a migração da referência da São Domingos (fase A), inclusive durante a fiscalização. | FR-012, FR-013, FR-018, FR-022, FR-024, FR-026, FR-028, casos de borda, Assumptions |
| 09/10/2026 | Começar a implementação já, antes da fiscalização, "deixando os códigos salvos em uma pasta": a versão aprovada da São Domingos fica congelada em `C:\Users\rlazaro\Desktop\UHE_SAO_DOMINGOS_versao_fiscalizacao\`, com os próprios dados, e é a usada na fiscalização. A regra de não coletar com o portal passa a valer só no projeto principal. | FR-028, Assumptions |

## Assumptions

- **Ordem das fases**: segue a proposta de 08/10/2026 (fundação, térmicas, eólicas e solares, PCH e CGH, carteira). A avaliação de fontes da ANEEL fica fora, porque a constituição só a admite com emenda.
- **Usinas piloto**: foram escolhidas pela cobertura dos dados no ONS. O usuário pode trocá-las sem mudar os requisitos. O que o ONS publica de cada uma, conferido em 09/10/2026:
  - **UTE William Arjona**: geração da usina desde 10/07/2021. O despacho por motivo vem desde 2013, sem dados de 08/2018 a 07/2021, com três códigos de planejamento (um até 2018; de 08/2021 a 02/2026, um para gás e outro para óleo).
  - **UFV Seriemas 1**: no conjunto Inocência 230 kV desde 13/04/2026. A geração do conjunto vem desde 05/05/2026; a série da usina e o fator de capacidade, desde 22/08/2026. O relatório piloto terá menos de 12 meses.
  - **EOL Praia Formosa**: fator de capacidade desde 07/2009 e restrição por usina desde 10/2021.
  - **PCH Bandeirante**: no conjunto Chapadão desde 22/08/2019. O conjunto teve cinco térmicas até 01/07/2025, e a geração da própria usina vem vazia.
- **Granularidade**: o ONS publica as eólicas e solares quase sempre em conjunto. A série da própria usina existe nos conjuntos de restrição, desde 10/2021 para as eólicas. Quando ela falta, o relatório usa o conjunto.
- **PCH em conjunto**: a geração da usina vem vazia no ONS (conferido em set/2026 para Bandeirante, Indaiá Grande, Indaiazinho e Areado). O relatório usa o conjunto.
- **Pequenas usinas e MMGD**: o ONS as publica em grupos por área, por exemplo "PQU MSMS MMGD" e "PQU MSMS HID". O panorama da carteira usa esses grupos.
- **Usinas nucleares**: são tratadas como térmicas, com o tipo UTN.
- **Prazo**: por decisão do usuário de 09/10/2026, o código começa antes da fiscalização. A fiscalização usa a versão congelada (FR-028), que não muda com o projeto principal.
- **Dados brutos**: continuam compartilhados por todas as usinas. Os conjuntos novos aumentam o volume em disco, mas cada usina baixa só o período e os conjuntos do seu tipo.
