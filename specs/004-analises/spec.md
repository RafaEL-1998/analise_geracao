# Spec da Etapa 4: Análises

**Etapa**: 4 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-08

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

As Análises calculam, para uma usina, tudo o que o relatório mostra: os indicadores anuais e do período, os eventos, as distribuições e os perfis da energia vertida turbinável (EVT), o cruzamento com as bases complementares do ONS, os dados de cada tabela e figura, as constatações e os itens da conclusão. Partem só dos dados tratados, dos resultados da Conferência, do perfil da usina e dos registros da Coleta, e gravam um único arquivo de resultados, que a Geração do relatório apenas formata e desenha. Não há parecer: as constatações descrevem fatos dos dados, e a conclusão sai de regras declaradas, que apontam indícios sem afirmar causa.

## Entradas e saídas

**Comando**: `python -m src analises --usina <slug>`, sem opções próprias. As regras comuns do fluxo (sintaxe, `--log-level`, perfil e código 4, `etapa.json`, pré-requisitos e `completo`) estão na spec da Coleta de dados.

**Entradas** (só leitura; nada das etapas anteriores é alterado):

| Entrada | Onde | O que as Análises usam |
|---|---|---|
| Perfil da usina | `usinas/<slug>/perfil.toml` | parâmetros técnicos, características da usina usadas nas análises, identificação e fontes (FR-007) |
| Dados tratados | `data/usinas/<slug>/tratamento/` | base de EVT tratada, com as sinalizações R6 a R9, e o resultado das regras R1 a R9; indicadores por unidade geradora (mensais e anuais), horas por estado operativo e TEIFa/TEIP mensais; programação horária e dias sem arquivo; séries horárias de disponibilidade, hidrologia e geração, com as sinalizações de qualidade, as ausências e as auditorias |
| Resultados da Conferência | `data/usinas/<slug>/conferencia/conferencias.pkl` | as seis conferências entre fontes; das aplicáveis, as tabelas que seguem nos resultados (FR-005) |
| Registros da Coleta | `data/usinas/<slug>/coleta/` e `data/raw/` | auditoria da extração da EVT e manifesto de versões (cobertura); auditoria dos arquivos da programação diária; ficha do cadastro e auditoria da sua leitura; registro dos dicionários de dados; datas de obtenção dos conjuntos |

**Saídas**:

| Arquivo | Conteúdo |
|---|---|
| `data/usinas/<slug>/analises/resultados.pkl` | resultados das análises (FR-005), com a versão do formato, que a Geração do relatório confere ao ler; nenhuma outra etapa lê esse arquivo |
| `data/usinas/<slug>/analises/etapa.json` | manifesto da etapa; o `resumo` traz o período e as horas analisadas, a quantidade de constatações, os itens da conclusão por lista e as regras que dispararam, e as bases complementares analisadas ou ausentes |

**Códigos de saída** (o código 4, de perfil inválido, é regra comum, na spec da Coleta de dados):

| Código | Quando |
|---|---|
| 0 | sucesso |
| 1 | erro, inclusive falha de gravação; o resultado anterior, se houver, fica como estava |
| 5 | Conferência sem resultados concluídos, ou com resultados desatualizados; nada é gravado |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Indicadores, eventos e perfis da base de EVT (Priority: P1)

Como fiscal da AGEMS, quero os indicadores anuais e do período de disponibilidade declarada, geração, garantia física e EVT, os eventos de usina parada com EVT e de indisponibilidade total, as distribuições e os perfis horários, o perfil estatístico e os extremos, todos calculados a partir dos dados tratados. Assim fundamento a fiscalização com números rastreáveis até a hora em que ocorreram.

**Why this priority**: É a base do relatório; as seções, as constatações e as regras da conclusão partem desses números.

**Independent Test**: Executar as Análises sobre uma série sintética com fatos conhecidos (30 h de indisponibilidade total, 5 h de usina parada com EVT, mudança de classificação do vertimento em jan/2024 e um registro de 60 MW sinalizado) e conferir que indicadores, eventos e extremos reproduzem esses fatos e que os totais conferem com a base.

**Acceptance Scenarios**:

1. **Given** a base de EVT tratada, **When** as Análises rodam, **Then** cada ano, com a cobertura e a marca de ano parcial, e o período completo trazem os indicadores das FR-011 e FR-012, e a soma das horas dos anos é igual ao número de registros.
2. **Given** horas consecutivas de usina parada com EVT ou de indisponibilidade total, **When** os eventos são montados, **Then** cada evento tem início, fim e duração, e uma hora ausente encerra o evento.
3. **Given** registros sinalizados (R6 a R9), **When** o perfil estatístico e os extremos são calculados, **Then** esses registros ficam de fora, mas continuam nos totais e nos indicadores (perfil da São Domingos: os 68,7 MW de 15/05/2019 14h não aparecem como máximo da geração).
4. **Given** a série da usina, **When** a mudança de classificação do vertimento é procurada, **Then** o mês e os valores típicos antes e depois são informados (perfil da São Domingos: dez/2022, com cerca de 5 m³/s passando a não turbinável).
5. **Given** as horas com EVT, **When** distribuídas pela geração da mesma hora, **Then** as faixas seguem o perfil e a EVT das faixas soma a EVT total (perfil da São Domingos: até 1 MW; 1 a 10; 10 a 20; 20 a 30; 30 a 40; 40 a 43,2; 43,2 MW ou mais).

---

### User Story 2 - Cruzamento com as bases complementares do ONS (Priority: P1)

Como fiscal, quero cruzar a operação verificada com a programação diária, a disponibilidade sincronizada, a afluência e o nível do reservatório e os indicadores oficiais por unidade geradora. Assim sei se a usina parada seguia a programação do ONS, se as unidades estavam desligadas da rede, se a água que chegou cabia nas turbinas e qual unidade concentra a indisponibilidade forçada.

**Why this priority**: São as respostas que a base de EVT sozinha não dá, e delas saem os principais indícios da conclusão.

**Independent Test**: Com dados tratados e resultados de conferência sintéticos, conferir que todas as horas paradas com EVT do período comum recebem uma classe da programação, que todas as horas paradas com dado de disponibilidade recebem uma classe de sincronização e que todas as horas com EVT do período da hidrologia recebem uma faixa de afluência, com a soma das classes igual ao total em cada caso.

**Acceptance Scenarios**:

1. **Given** a programação horária, **When** cruzada com a base de EVT nas horas comuns, **Then** cada hora recebe uma das cinco classes da FR-026, e as horas paradas com EVT se dividem entre programação de até 1 MW e acima disso (perfil da São Domingos: 1.739 das 1.908 h, 91,1 %, com programação de até 1 MW).
2. **Given** horas paradas com programação acima de 5 MW, **When** agrupadas, **Then** formam eventos com início, fim, duração, programação média, disponibilidade média e EVT (perfil da São Domingos: 182 h em 68 eventos).
3. **Given** a disponibilidade operacional e a sincronizada, **When** resumidas por mês e por ano, **Then** trazem a capacidade não sincronizada e a comparação com a reserva desligada das horas por estado operativo.
4. **Given** os dados hidrológicos com a conferência das vazões na meta, **When** as horas com EVT são classificadas, **Then** as faixas usam o engolimento de uma unidade e o engolimento máximo calculados do perfil (perfil da São Domingos: 81,5 e 163 m³/s; em 92,9 % das horas com EVT a afluência cabia nas turbinas).
5. **Given** as horas por estado operativo, **When** a TEIFa e a TEIP mais recentes são decompostas, **Then** cada unidade e parcela tem a contribuição em pontos percentuais e a participação na taxa (perfil da São Domingos: 87 % da TEIFa de ago/2026 vem da limitação forçada de potência da UG2).

---

### User Story 3 - Constatações geradas dos dados, sem parecer (Priority: P1)

Como fiscal, quero constatações em texto, cada uma com título e texto montados só a partir dos resultados, que descrevam fatos sem parecer nem atribuição de causa. Assim o relatório não traz conclusão que os dados não sustentam.

**Why this priority**: São o texto do relatório; um número fixo ou um parecer sem base compromete um documento de fiscalização.

**Independent Test**: Gerar as constatações sobre a série sintética, sem bases complementares, e conferir a quantidade, a ordem, os números citados e a ausência de termos de parecer.

**Acceptance Scenarios**:

1. **Given** só a base de EVT, numa série com mudança de classificação do vertimento, **When** as constatações são montadas, **Then** são exatamente 12, na ordem da FR-044.
2. **Given** todas as bases, sem divergência na conferência da geração nem na do cadastro, **When** as constatações são montadas, **Then** as constatações condicionais dessas duas não aparecem (perfil da São Domingos: 17 constatações).
3. **Given** qualquer constatação, **When** lida, **Then** os números são os dos resultados, e o texto não tem parecer nem as afirmações removidas na auditoria ("96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained").
4. **Given** uma série sem mudança de classificação do vertimento, **When** as constatações são montadas, **Then** a constatação dessa mudança não aparece.

---

### User Story 4 - Conclusão por regras declaradas (Priority: P1)

Como fiscal, quero que os itens da conclusão — pontos de atenção, possíveis problemas, o que confirmar com o agente e o que verificar em campo — sejam gerados por um catálogo de regras declaradas, aplicado aos resultados das análises e das conferências. Assim levo à fiscalização presencial uma lista objetiva e reproduzível do que perguntar e do que conferir.

**Why this priority**: É pedido do usuário para a fiscalização de 14 a 16/10/2026 e fecha o relatório.

**Independent Test**: Com resultados sintéticos, fazer cada regra C1 a C11 disparar e não disparar e conferir os itens, a ordem, as seções de origem, a linguagem de indício e a ausência de texto de constatação.

**Acceptance Scenarios**:

1. **Given** os resultados da usina, **When** a conclusão é gerada, **Then** cada item tem lista, ordem, regra, texto e seções de origem (perfil da São Domingos: 19 itens, 5, 4, 5 e 5 por lista, com as onze regras disparadas).
2. **Given** uma unidade com limitação forçada de potência em ≥ 50 % dos meses, ou com ≥ 2/3 da TEIFa acima da referência, **When** a regra C2 é aplicada, **Then** a unidade é nomeada como o ONS a identifica, com os números (perfil da São Domingos: "UG2: indício de problema na unidade, com limitação forçada de potência em 78 dos 80 meses (3.824 h equivalentes; UG1: 51 h); responde por 91% da TEIFa de ago/2026, que ficou em 4,11%, acima da referência de 2,333%").
3. **Given** uma regra cuja condição não é atendida, ou cuja base não existe para a usina, **When** a conclusão é gerada, **Then** a regra não gera item.
4. **Given** mais de cinco itens numa lista, **When** a conclusão é gerada, **Then** todos ficam nos resultados, na ordem do catálogo.
5. **Given** os itens e as constatações, **When** comparados, **Then** nenhum item repete frase de constatação nem usa termo de avaliação de desempenho.

---

### User Story 5 - Etapa executada sozinha, com resultados prontos para o relatório (Priority: P1)

Como fiscal, quero executar só as Análises, a partir do que a Conferência gravou, e obter um único arquivo de resultados com tudo o que o relatório mostra, inclusive os dados de cada figura. Assim regero o relatório sem refazer as análises, e a formatação não recalcula nada.

**Why this priority**: Separa as Análises do relatório no fluxo de cinco etapas e sustenta a prova de não regressão.

**Independent Test**: Executar `python -m src analises --usina <slug>` com a Conferência concluída e conferir o arquivo de resultados e o `etapa.json`; repetir sem a Conferência e conferir a recusa.

**Acceptance Scenarios**:

1. **Given** a Conferência concluída, **When** as Análises rodam, **Then** gravam `resultados.pkl` e o `etapa.json` concluído, com o resumo, e saem com código 0.
2. **Given** a Conferência ausente, com falha ou desatualizada, **When** as Análises rodam, **Then** saem com código 5, sem gravar nada, e indicam a Conferência como etapa a executar antes.
3. **Given** os resultados gravados, **When** a Geração do relatório roda, **Then** encontra neles os dados das oito figuras e de todas as tabelas, sem recalcular.
4. **Given** o perfil da São Domingos e os dados locais, **When** as Análises e a Geração do relatório rodam, **Then** o relatório é idêntico ao de referência (SC-001).

---

### User Story 6 - Mesmas análises para outra usina, ajustadas ao perfil (Priority: P2)

Como fiscal, quero que as análises de outra usina usem o número de unidades, o engolimento, a potência, as faixas de geração e o vertimento mínimo do perfil dela, e que as análises das bases que ela não tem sejam omitidas. Assim o relatório dela sai com a mesma lógica e o mesmo rigor.

**Why this priority**: Amplia o uso do projeto, mas não muda o relatório da São Domingos.

**Independent Test**: Executar as Análises com o perfil da usina fictícia dos testes (três unidades geradoras) e conferir as faixas de afluência, as faixas de geração e a ausência de valores da São Domingos nos textos; executar sem uma base complementar e conferir a omissão.

**Acceptance Scenarios**:

1. **Given** um perfil com três unidades, **When** as horas com EVT são classificadas por afluência, **Then** as faixas são "até uma unidade", "entre uma e três unidades" e "acima do engolimento máximo", com os limites calculados do perfil.
2. **Given** outras faixas de geração no perfil, **When** a EVT por nível de geração é calculada, **Then** as faixas intermediárias são as do perfil.
3. **Given** uma usina sem programação diária ou sem dados hidrológicos, **When** as Análises rodam, **Then** as análises, as constatações e as regras que dependem dessa base são omitidas, sem erro.
4. **Given** qualquer usina, **When** os textos são gerados, **Then** nenhum nome, identificador ou valor de usina vem de fora do perfil ou dos dados.

---

### Edge Cases

- **Anos parciais**: um ano é parcial quando o primeiro registro é posterior a 1º de janeiro 00h ou o último é anterior a 31 de dezembro 23h.
  - Aparece nas tabelas com a marca e a cobertura, e as médias e somas usam as horas reais, sem extrapolação.
  - Fica fora das comparações entre anos completos: constatações de disponibilidade, de geração e da distribuição ao longo do ano, e regra C9.
  - A regra C4 olha os dois últimos anos da série, mesmo parciais, e marca o parcial no item.
- **Horas ausentes e horários duplicados**: listados na cobertura, sem interpolação; uma hora ausente encerra qualquer evento.
- **Registros sinalizados (R6 a R9)**: ficam nos totais e indicadores, por serem os dados publicados pelo ONS, e saem do perfil estatístico e dos extremos.
- **Série sem mudança de classificação do vertimento**: nenhum mês é detectado e a constatação não aparece; a separação da EVT das horas de vertimento mínimo continua.
- **Sem anos completos com EVT**: a constatação da distribuição ao longo do ano diz que não há como avaliá-la; a parte de EVT da regra C9 exige ao menos dois anos completos.
- **Unidade sem potência no conjunto do ONS**: o peso dela no DISPF da usina é a potência unitária do perfil.
- **Janela de 60 meses incompleta no mês da TEIFa mais recente**: não há decomposição das taxas, e a regra C2 só dispara pelos meses com limitação forçada de potência.
- **Horas sem programação** (dia sem arquivo ou hora sem valor): ficam fora da classificação da programação e são contadas à parte, sem interpolação.
- **Horas de disponibilidade sinalizadas (D1 a D4)**: a hora inteira sai das análises da disponibilidade.
- **Valores hidrológicos sinalizados (H1, H2 e H4) e campos vazios**: saem só do campo afetado; vazio não é zero; a hora com EVT sem afluência válida entra na faixa "sem dado hidrológico".
- **Conferência das vazões abaixo da meta**: nenhum cruzamento hidrológico é feito (FR-034); a regra C3 não dispara; a regra C11 continua a considerar as sinalizações da hidrologia.
- **Base complementar ausente**: as análises, as constatações e as regras que dependem dela não são feitas, e a conferência correspondente, registrada como "não aplicável" pela Conferência, não entra nos resultados.
- **Constatações condicionais**: a do cadastro e a da conferência da geração só aparecem com divergência.
- **Nenhuma regra da conclusão dispara**: a conclusão fica sem itens; a frase mostrada nesse caso está na spec da Geração do relatório.
- **Mais de cinco itens numa lista**: todos ficam nos resultados, na ordem do catálogo; o corte em cinco é feito na Geração do relatório.
- **C7 e C8 disparam juntas**: a pergunta ao agente fica num só item, o da C7, que cita as horas da regra R7.
- **Mais de uma unidade atende à C2**: um item por lista para cada unidade, na ordem das unidades.

---

## Requirements *(mandatory)*

### Functional Requirements

**Execução e resultados (US5)**

- **FR-001**: A etapa DEVE ser executada por `python -m src analises --usina <slug>`, sem opções próprias, e terminar com os códigos 0, 1 ou 5 da tabela de Entradas e saídas.
- **FR-002**: Antes de gravar, a etapa DEVE conferir que a Conferência está concluída e atualizada. Se não estiver, DEVE sair com código 5, sem gravar nada, e indicar a Conferência como a etapa a executar antes.
- **FR-003**: As Análises DEVEM ler só as entradas de Entradas e saídas. NÃO DEVEM acessar o portal do ONS, refazer o tratamento dos dados nem refazer conferências: os resultados de conferência são lidos como estão, e as tabelas das conferências aplicáveis seguem nos resultados sem alteração (FR-005).
- **FR-004**: A etapa DEVE gravar os resultados num único arquivo, `resultados.pkl`, com a versão do formato, e o `etapa.json` com o `resumo` de Entradas e saídas. Qualquer falha DEVE ser registrada no log e encerrar a etapa com código 1; numa falha de gravação, o arquivo anterior, se houver, fica como estava.
- **FR-005**: Os resultados DEVEM conter tudo o que o relatório mostra: números, tabelas, dados das figuras (FR-041), constatações (FR-044) e itens da conclusão (FR-045). A tabela de parâmetros é a exceção (FR-042). As tabelas de cada conferência aplicável DEVEM seguir, como estão, junto com os resultados da base a que se referem: resumo, comparação mensal e divergências da geração; resumo e divergências da disponibilidade; alinhamento das vazões; divergências entre o DISPF e as horas por estado operativo; recálculo da TEIFa e da TEIP; divergências do cadastro. Os demais campos de cada resultado de conferência, como a situação "não aplicável" e o motivo, ficam nos resultados da Conferência. Também DEVEM seguir, como estão, os dias sem arquivo e a auditoria dos arquivos da programação diária, as ausências e as auditorias da disponibilidade, da hidrologia e da geração e a auditoria da leitura do cadastro; a auditoria da extração dos indicadores oficiais não segue nos resultados. A Geração do relatório só formata e desenha, sem recalcular; faz apenas seleções e contagens simples sobre os resultados, como os eventos que lista, o maior valor citado numa legenda e o total de horas por ano numa figura.

**Regras gerais e valores do perfil (US6)**

- **FR-006**: As regras gerais abaixo DEVEM ser as mesmas para qualquer usina; o perfil não as altera.

  | Regra geral | Valor |
  |---|---|
  | Usina parada | geração ≤ 1 MW |
  | Hora com EVT | EVT > 0 |
  | Indisponibilidade total | disponibilidade declarada ≤ 0,001 MW |
  | Disponibilidade até a metade | disponibilidade > 0,001 MW e ≤ 50 % da potência instalada |
  | Plena carga | geração ≥ 90 % da potência instalada |
  | EVT acima da folga de geração | EVT − folga > 10⁻⁶ MW |
  | Janelas horárias (hora de início) | diurna das 9h às 15h; noturna das 20h às 5h |
  | Concentração diurna | razão entre a EVT média diurna e a noturna ≥ 2 |
  | Evento | horas consecutivas, de hora em hora; uma hora ausente encerra o evento |
  | Indisponibilidade longa (constatação e série temporal) | evento de indisponibilidade total com ≥ 24 h |
  | Programação zero e desvio da programação | programação ≤ 1 MW; usina parada com programação > 5 MW |
  | Unidade sincronizada | disponibilidade sincronizada > 1 MW |
  | Janela da TEIFa e da TEIP | 60 meses |
  | Identidade das horas por estado operativo | soma das parcelas igual às horas do período, com diferença ≤ 0,1 h |
  | Capacidade não sincronizada × reserva desligada (constatação) | coincidem no ano com diferença ≤ 0,1 GWh |
  | Distribuição ao longo do ano | só anos completos; maio a outubro × janeiro a abril; três meses de maior EVT |
  | Ano parcial | primeiro registro depois de 1º de janeiro 00h ou último antes de 31 de dezembro 23h |
  | Limiares da conclusão | catálogo C1 a C11 (FR-045) |

- **FR-007**: Os valores próprios da usina DEVEM vir do perfil, cujos campos e validação estão na spec da Coleta de dados, e os derivados DEVEM ser calculados a partir dele:

  | Valor | Campo do perfil ou cálculo | Uso nas Análises |
  |---|---|---|
  | Potência instalada (P) | `parametros.potencia_instalada_mw` | disponibilidade relativa, fator de capacidade, plena carga, metade da potência, constatação de qualidade |
  | Potência unitária | `parametros.potencia_unitaria_mw` | peso do DISPF quando o ONS não informa a potência da unidade |
  | Unidades geradoras (N) e engolimento por unidade | `parametros.unidades_geradoras`, `parametros.engolimento_nominal_ug_m3s` | faixas de afluência |
  | Engolimento máximo | N × engolimento por unidade | faixas de afluência, regra C3 |
  | Garantia física | `parametros.garantia_fisica_mwmed` | geração ÷ garantia física, regra C9 |
  | IP e TEIF de referência | `parametros.ip_referencia`, `parametros.teif_referencia` | regras C2 e C5, constatação dos indicadores oficiais |
  | Disponibilidade de referência | (1 − IP) × (1 − TEIF) | distância da disponibilidade declarada e do DISPF, regra C5 |
  | Vertimento mínimo | `analises.vertimento_minimo_m3s` | EVT das horas de vertimento mínimo, mudança de classificação |
  | Faixas de geração | `analises.faixas_geracao_mw` | EVT por nível de geração |
  | Início da operação comercial | `usina.inicio_operacao_comercial` | constatação de cobertura |
  | Nome, estado, identificadores, demais parâmetros e fontes | `usina`, `identificacao` e `parametros` | textos das constatações e da conclusão |

- **FR-008**: As análises que dependem das características da usina DEVEM ser derivadas do perfil:
  - faixas de afluência "até uma unidade", "entre uma e N unidades" e "acima do engolimento máximo", com N escrito por extenso de 1 a 10 ("duas" para 2) e em algarismos acima de 10;
  - faixas intermediárias da EVT por nível de geração;
  - limite do vertimento mínimo.
- **FR-009**: Os textos gerados nas Análises (constatações e itens da conclusão) NÃO DEVEM ter nome, identificador ou valor de usina que não venha do perfil ou dos dados. Os números DEVEM seguir o padrão brasileiro (milhar com ponto, decimal com vírgula), com datas "dd/mm/aaaa HHh", meses "mmm/aaaa" e "–" para valor ausente.

**Cobertura (US1)**

- **FR-010**: A cobertura da série de EVT DEVE trazer:
  - primeiro e último registro; horas observadas e esperadas, pela grade horária contínua entre os dois; horas ausentes, com a lista; horários duplicados;
  - por ano: primeiro e último registro, horas observadas, horas do ano civil (8.760 ou 8.784), cobertura em % e marca de ano parcial; a lista dos anos parciais e a dos completos;
  - os agentes, com o primeiro e o último registro e as horas de cada um;
  - a identificação da usina nos dados: código, reservatório, rio, bacia e subsistema;
  - quando existem, o resumo da auditoria da extração (arquivos lidos, com registros da usina, sem registros, com falha e linhas com identificação divergente) e o do manifesto de versões (arquivos registrados, publicação mais recente no portal e registro mais recente). Sem eles, a cobertura sai só da base.

**Indicadores da base de EVT (US1)**

- **FR-011**: Para cada ano civil, com todos os registros, inclusive os sinalizados, os indicadores DEVEM ser:
  - marca de ano parcial, horas observadas e cobertura;
  - geração média e disponibilidade média declarada (MWmed);
  - fator de capacidade = geração média ÷ P;
  - disponibilidade relativa = disponibilidade média ÷ P, uma aproximação que não é o FID regulatório, e a diferença dela, em pontos percentuais, para a disponibilidade de referência;
  - geração média ÷ garantia física;
  - energia gerada e EVT (MWh); EVT das horas de vertimento mínimo (vazão vertida ≤ vertimento mínimo do perfil) e das demais horas, com a participação da primeira; índice EVT = EVT ÷ (energia gerada + EVT);
  - horas com EVT (quantidade e % das horas); horas de usina parada com EVT e a EVT nelas; horas de indisponibilidade total; horas com disponibilidade até a metade;
  - EVT média e geração média nas janelas diurna e noturna, e as razões diurna ÷ noturna;
  - horas com registro sinalizado.
- **FR-012**: Para o período completo, em que cada hora tem o mesmo peso, os indicadores DEVEM ser:
  - horas; geração média; disponibilidade média; fator de capacidade; disponibilidade relativa; disponibilidade de referência e a diferença para ela; geração média ÷ garantia física;
  - energia gerada; EVT; índice EVT; horas com EVT (quantidade e %); folga média de geração nas horas com EVT;
  - limiar de plena carga e EVT com geração em plena carga (MWh e % da EVT); horas com EVT acima da folga de geração;
  - horas de usina parada com EVT, a EVT nelas e a % da EVT; disponibilidade média nessas horas;
  - horas com geração exatamente zero, total e com EVT; horas com geração acima de zero e até 1 MW, com EVT;
  - horas com registro sinalizado e a EVT nelas; maior geração registrada, com data e hora.

**Eventos (US1)**

- **FR-013**: As horas consecutivas DEVEM ser agrupadas em eventos, e uma hora ausente encerra o evento:
  - usina parada com EVT: início, fim, duração, geração média, disponibilidade média, vazão vertida média e EVT;
  - indisponibilidade total: início, fim, duração, vazão vertida média e geração média.

  As listas completas ficam nos resultados; o que o relatório lista é definido na spec da Geração do relatório.

**Distribuições e perfis (US1)**

- **FR-014**: A EVT mensal DEVE trazer, para cada mês da série: horas, energia gerada, geração média, disponibilidade média, EVT, EVT das horas de vertimento mínimo e EVT das demais horas.
- **FR-015**: A participação de cada mês do ano (janeiro a dezembro) na EVT DEVE somar só os anos completos.
- **FR-016**: As horas com EVT DEVEM ser distribuídas pela geração na mesma hora, nestas faixas:
  - até 1 MW (usina parada);
  - acima de 1 MW e até o primeiro limite das faixas de geração do perfil; acima de cada limite e até o seguinte;
  - acima do último limite e abaixo da plena carga;
  - plena carga ou mais.

  Cada faixa traz horas, EVT, participação na EVT, geração média e disponibilidade média; a faixa sem horas aparece com zero horas e zero EVT.
- **FR-017**: O perfil horário DEVE trazer a geração média e a EVT média por ano e hora do dia (0 a 23).
- **FR-018**: As horas com geração exatamente zero DEVEM ser contadas por ano e mês, com o mês sem registros na série vazio, e não zero, e o total do ano separado entre horas com disponibilidade zero (indisponibilidade total) e horas com a usina declarada disponível.

**Mudança de classificação do vertimento (US1)**

- **FR-019**: A etapa DEVE procurar o mês a partir do qual a mediana mensal da vazão vertida não turbinável é positiva em todos os meses até o fim da série, sendo não positiva no mês anterior. Quando há esse mês, DEVE informar:
  - o mês e a quantidade de meses antes dele e a partir dele;
  - a vazão não turbinável típica depois, pela mediana nas horas de vertimento mínimo;
  - antes do mês: a vazão turbinável típica (mediana nas horas de vertimento mínimo), a EVT média nessas horas e o percentual das horas anteriores com vertimento mínimo e vazão turbinável positiva.

  Sem esse mês, nenhuma mudança é informada, e a constatação correspondente não aparece.

**Registros sinalizados, perfil estatístico e extremos (US1)**

- **FR-020**: Os registros sinalizados no Tratamento (R6 a R9) DEVEM ficar nos totais e nos indicadores e sair do perfil estatístico e dos extremos. Os resultados DEVEM trazer:
  - a lista cronológica desses registros: instante, regras violadas, geração, disponibilidade, vazão turbinada, produtividade, energia vertida e EVT;
  - o resumo por regra: descrição, horas, primeira e última ocorrência e EVT;
  - o resultado das regras R1 a R9 apurado no Tratamento.
- **FR-021**: O perfil estatístico DEVE trazer, para cada ano e cada uma das 10 grandezas operacionais da base de EVT (geração, disponibilidade, vazões turbinada, vertida, vertida não turbinável e vertida turbinável, produtividade, folga de geração, energia vertida e EVT), só com os registros sem sinalização e com valor:
  - registros considerados, média, desvio-padrão amostral (zero com um só registro), mediana, percentis 25 % e 75 % e soma;
  - mínimo e máximo, com data e hora;
  - os valores com 4 casas decimais, e a soma com 2.
- **FR-022**: Os extremos do período DEVEM trazer o máximo e o mínimo de cada grandeza, com data e hora e 4 casas decimais, com a mesma exclusão da FR-021.

**Indicadores oficiais por unidade geradora (US2)**

- **FR-023**: A disponibilidade da usina pelo DISPF DEVE ser a média das unidades ponderada pela potência de cada unidade (a potência unitária do perfil, quando o ONS não a informa) e pelas horas da base de EVT em cada mês, só nos meses presentes na base de EVT. Por ano e no período, os resultados DEVEM trazer:
  - DISPF, INDISPPF e INDISPFF assim ponderados;
  - por ano, a disponibilidade declarada (FR-011), a diferença do DISPF para a disponibilidade de referência e a marca de ano parcial;
  - no período, o primeiro e o último mês e a quantidade de unidades.
- **FR-024**: Os resultados DEVEM trazer:
  - os indicadores anuais de cada unidade publicados pelo ONS (DISPF, INDISPPF, INDISPFF e DMDFF), com a marca de ano parcial da cobertura;
  - as horas por estado operativo (HP, HS, HRD, HDP, HDF, HDCE, HEDP e HEDF), por mês e somadas por ano e unidade, com a quantidade de meses e a marca de ano parcial quando há menos de 12 meses;
  - no período, o primeiro e o último mês, os meses-unidade e quantos deles ficam fora da identidade das horas (FR-006).
- **FR-025**: A TEIFa e a TEIP mais recentes publicadas DEVEM ser informadas com o mês e com (1 − TEIFa) × (1 − TEIP). Quando as horas por estado cobrem toda a janela de 60 meses desse mês, as duas taxas DEVEM ser decompostas por unidade e parcela (TEIFa: HDF e HEDF; TEIP: HDP e HEDP), com as horas da janela ponderadas pela potência de cada unidade (peso 1 quando o ONS não a informa):
  - horas da parcela na janela;
  - contribuição, em pontos percentuais = horas ponderadas da parcela ÷ denominador da taxa (TEIFa: Σ potência × (HP − HDP − HEDP); TEIP: Σ potência × HP);
  - participação na taxa (%).

  O recálculo das taxas, com a quantidade de meses reproduzidos, e as divergências entre o DISPF e as horas por estado são resultados da Conferência, lidos como estão.

**Programação diária do ONS (US2)**

- **FR-026**: Cada hora comum à base de EVT e à programação horária, com valor programado, DEVE receber uma classe:

  | Classe | Condição |
  |---|---|
  | parada com EVT e programação de até 1 MW | geração ≤ 1 MW, EVT > 0 e programação ≤ 1 MW |
  | parada com EVT e programação acima de 1 MW | geração ≤ 1 MW, EVT > 0 e programação > 1 MW |
  | parada sem EVT | geração ≤ 1 MW e EVT = 0 |
  | gerando com programação de até 1 MW | geração > 1 MW e programação ≤ 1 MW |
  | gerando com programação acima de 1 MW | geração > 1 MW e programação > 1 MW |

  A hora também é marcada como desvio quando a usina está parada com programação acima de 5 MW. As horas da base de EVT no período da programação sem valor programado ficam fora da classificação e são contadas à parte.
- **FR-027**: Por mês, os resultados DEVEM trazer: horas comuns; horas de cada classe; horas paradas com EVT; EVT; EVT das horas paradas com EVT e programação de até 1 MW e a participação dela na EVT do mês; horas de desvio; disponibilidade declarada média nas horas paradas com EVT e programação de até 1 MW; desvio médio absoluto entre geração e programação. Por hora do dia (0 a 23), as horas paradas com EVT e programação de até 1 MW e a EVT delas, com zero nas horas sem ocorrência.
- **FR-028**: No período comum, os resultados DEVEM trazer:
  - primeiro e último dia da programação, dias com arquivo e dias sem arquivo, com a lista;
  - horas comuns e horas da base de EVT, no período da programação, que ficaram sem programação;
  - horas paradas com EVT; quantas delas tinham programação de até 1 MW, com o percentual, e a disponibilidade declarada média nelas;
  - EVT das horas comuns e EVT das horas paradas com EVT e programação de até 1 MW, com o percentual;
  - percentual dessas horas na janela diurna;
  - horas de desvio, quantidade de eventos de desvio e o evento mais longo;
  - horas gerando com programação de até 1 MW;
  - correlação horária entre a geração verificada e a programada, e o desvio médio absoluto.
- **FR-029**: As horas consecutivas de desvio DEVEM formar eventos, com início, fim, duração, programação média, disponibilidade declarada média e EVT. A lista completa fica nos resultados.

**Disponibilidade operacional e sincronizada (US2)**

- **FR-030**: As horas sinalizadas no Tratamento (D1 a D4: sincronizada acima da operacional, operacional acima da instalada, valor negativo ou valor não numérico) DEVEM sair inteiras de todas as análises da disponibilidade.
- **FR-031**: Cada hora comum com a usina parada DEVE ser classificada por:
  - sincronização: alguma unidade sincronizada, se a sincronizada passa de 1 MW; nenhuma, caso contrário;
  - EVT: com ou sem;
  - programação: a classe da FR-026, nas horas classificadas pela programação; "sem programação: fora do período ou sem valor programado", nas demais (horas fora do período da programação ou, dentro dele, sem valor programado, como as dos dias sem arquivo no portal).

  Os resultados DEVEM trazer a lista das horas classificadas e as horas e a EVT de cada combinação. A soma das combinações é o total de horas paradas comuns.
- **FR-032**: Por mês e por ano, com a marca de ano parcial, os resultados DEVEM trazer, nas horas comuns:
  - médias de disponibilidade operacional, declarada e sincronizada e de geração;
  - capacidade não sincronizada (operacional − sincronizada), em MW médio e em MWh;
  - horas paradas, sem unidade sincronizada e com unidade sincronizada;
  - reserva desligada = Σ (HRD × potência da unidade), das horas por estado operativo;
  - diferença = capacidade não sincronizada − reserva desligada, vazia quando não há horas por estado no período.
- **FR-033**: O resumo da disponibilidade DEVE trazer:
  - período, horas, horas sinalizadas, meses sem a usina e horas ausentes;
  - horas paradas comuns, sem e com unidade sincronizada, e o percentual sem sincronização;
  - horas paradas com EVT e quantas delas com as unidades desligadas;
  - no período da programação, as horas paradas com EVT e programação de até 1 MW e quantas delas com as unidades desligadas.

**Afluência, vertimento e nível do reservatório (US2)**

- **FR-034**: Os cruzamentos hidrológicos — faixas de afluência (FR-036), perfil por hora do dia (FR-037) e resumos mensais e anuais (FR-038) — só DEVEM ser feitos quando a conferência das vazões atingiu a meta. Sem a meta, os resultados trazem só o resumo da série sem as partes que dependem da meta (FR-038) e o resultado da conferência.
- **FR-035**: Os valores sinalizados no Tratamento como vazão negativa (H1), volume útil fora de 0 a 100 % (H2) ou nível implausível (H4) DEVEM sair só do campo afetado; a hora continua nos demais campos. Valores não numéricos (H3) e campos vazios ficam vazios, nunca zero. Nenhum valor é corrigido.
- **FR-036**: Cada hora com EVT dentro do período da hidrologia DEVE receber uma faixa de afluência:
  - até uma unidade: afluência ≤ engolimento por unidade;
  - entre uma e N unidades: afluência acima do engolimento por unidade e até o engolimento máximo;
  - acima do engolimento máximo;
  - sem dado hidrológico: afluência vazia, sinalizada ou hora ausente.

  Os resultados DEVEM trazer a lista das horas classificadas e as horas e a EVT por faixa, por mês e por ano, com todas as faixas em cada período (zero quando vazias) e a marca de ano parcial, e também no período. A soma das faixas é o total de horas com EVT do período da hidrologia.
- **FR-037**: O perfil por hora do dia (0 a 23) do nível de montante e das vazões afluente, turbinada e vertida DEVE separar os dias com ao menos uma hora de usina parada com EVT dos demais dias, com a quantidade de dias de cada grupo e, por grupo, o mínimo, o máximo e a amplitude do nível médio ao longo do dia.
- **FR-038**: Por mês e por ano, com a marca de ano parcial, os resultados DEVEM trazer: horas; afluência média e máxima; vazões turbinada, vertida e vertida não turbinável médias; nível de montante mínimo, médio e máximo; nível de jusante médio; volume útil médio; horas com afluência acima do engolimento máximo. O resumo da hidrologia DEVE trazer:
  - sempre: período, horas, horas sinalizadas no total e por regra (H1 a H4) e ano, meses sem a usina e horas ausentes;
  - com a meta da conferência das vazões: horas com afluência acima do engolimento máximo e pico de afluência (instante, afluência e defluência), além dos totais da FR-036 e dos grupos de dias da FR-037.

**Geração oficial e cadastro (US2)**

- **FR-039**: Com a série de geração por usina, os resultados DEVEM trazer o resumo da série (período, horas, horas sinalizadas, meses sem a usina e horas ausentes) e os totais por ano da comparação mensal feita na Conferência: energia da base de EVT e da série oficial, diferença e horas presentes em só uma das fontes, com a marca de ano parcial.
- **FR-040**: Com o cadastro, os resultados DEVEM trazer a ficha da usina e a auditoria da sua leitura, ambas da Coleta, e as divergências apontadas pela Conferência.

**Dados das tabelas e figuras (US5)**

- **FR-041**: Os dados de cada figura do relatório DEVEM ser calculados nas Análises; a Geração do relatório só desenha:

  | Figura | Dados |
  |---|---|
  | Série temporal de disponibilidade, geração e EVT | médias diárias (dia civil) da disponibilidade declarada, da geração e da EVT; eventos de indisponibilidade total (lista completa da FR-013), dos quais a figura marca os de ≥ 24 h |
  | EVT mensal | EVT de cada mês nas horas de vertimento mínimo e nas demais horas (FR-014); mês da mudança de classificação, se houver |
  | Perfil horário da geração e da EVT | médias por ano e hora do dia (FR-017) |
  | Disponibilidade e geração por ano | disponibilidade relativa e fator de capacidade por ano, com a marca de ano parcial (FR-011) |
  | Vazões defluentes por ano | médias anuais das vazões turbinada, vertida turbinável e vertida não turbinável |
  | Disponibilidade operacional e sincronizada | médias mensais (FR-032) |
  | Horas com EVT por faixa de afluência | horas por faixa e ano (FR-036) |
  | Perfil horário do nível e das vazões | médias por hora do dia e grupo de dias (FR-037) |

  As linhas de referência das figuras (potência instalada, garantia física, disponibilidade de referência e engolimento máximo) vêm do perfil e dos valores derivados (FR-007). Os dados das três últimas figuras só existem com a base correspondente; os das duas de hidrologia, só quando a conferência das vazões atingiu a meta.
- **FR-042**: A tabela de parâmetros NÃO DEVE ser montada nas Análises. Ela sai do perfil, das regras gerais e das datas de obtenção registradas pela Coleta, e é montada na Geração do relatório; das Análises, ela usa só o período de cada base complementar, que já está nos resumos das FR-033, FR-038 e FR-039.

**Constatações (US3)**

- **FR-043**: Cada constatação DEVE ter um título fixo e um texto montado só a partir dos resultados, do perfil e das regras gerais. As constatações DEVEM descrever fatos dos dados:
  - NÃO DEVEM emitir parecer de desempenho, como "satisfatório", "insatisfatório", "cumpre", "descumpre" e equivalentes;
  - NÃO DEVEM atribuir causa ao vertimento, às reduções de geração ou às paradas; quando a base não informa a causa, o texto diz isso.
- **FR-044**: As constatações DEVEM ser geradas nesta ordem, cada uma no máximo uma vez, e só nas condições indicadas. Onde cada uma aparece no relatório é definido na spec da Geração do relatório.

  | # | Título | Aparece quando | O que informa |
  |---|---|---|---|
  | 1 | Cobertura dos dados | sempre | período da série, com o identificador da usina; registros e horas ausentes, até cinco listadas; arquivos sem registros da usina; período anterior à série não coberto, quando a série começa depois do ano de início da operação comercial; anos parciais e o aviso de que as comparações usam só anos completos |
  | 2 | Cadastro da usina no ONS | a conferência da ficha do cadastro com o perfil aponta divergência | a ficha, a data de obtenção, os homônimos excluídos e as divergências |
  | 3 | Disponibilidade | sempre | disponibilidade média declarada (MW e % da potência), distância à referência e anos completos abaixo dela, ou que nenhum ficou |
  | 4 | Indicadores oficiais de disponibilidade (ONS) | há indicadores mensais por unidade | DISPF médio das unidades, com as indisponibilidades programada e forçada, e a distância à referência; a disponibilidade declarada e a diferença entre as duas medidas; anos completos abaixo da referência pelo DISPF; com as taxas, a TEIFa e a TEIP mais recentes frente às referências e (1 − TEIFa) × (1 − TEIP) |
  | 5 | Estados operativos das unidades geradoras (ONS) | há horas por estado operativo | período; meses-unidade fora da identidade das horas, se houver; meses com a TEIFa e a TEIP reproduzidas na Conferência, sobre os meses com janela de 60 meses completa, e a maior diferença ("nos N meses", quando todos são reproduzidos; "em X dos N meses", quando não); maior parcela da TEIFa mais recente e a TEIFa sem ela; unidade com mais horas equivalentes de limitação forçada; horas em reserva desligada por ano e unidade; desligamentos por causa externa, se houver; meses-unidade com DISPF e horas divergentes e se a diferença cabe nas horas de reserva desligada, com a tolerância de 1 h da Conferência; a ressalva de que os conjuntos não informam causa nem eventos |
  | 6 | Indisponibilidades | sempre | períodos de indisponibilidade total com ≥ 24 h (quantidade, horas e o mais longo), ou que não houve; horas com disponibilidade até a metade e o ano com mais horas assim |
  | 7 | Geração e garantia física | sempre | geração média, fator de capacidade e % da garantia física; variação entre os anos completos; o último ano, quando parcial |
  | 8 | Energia vertida turbinável | sempre | EVT total, índice EVT, % das horas com EVT, folga média nessas horas e EVT por ano |
  | 9 | EVT e nível de geração | sempre | % da EVT em plena carga; se a EVT supera a folga de geração em alguma hora; EVT com a usina parada (GWh, % e horas) e a disponibilidade média nessas horas |
  | 10 | EVT com a usina parada | sempre | horas paradas com EVT por ano e o ano com mais EVT nessas horas |
  | 11 | Programação diária do ONS | há programação | cobertura e horas fora do cruzamento; parcela das horas paradas com EVT com programação de até 1 MW, com a disponibilidade, a EVT e a parte na janela diurna; desvios acima de 5 MW (horas, eventos e o mais longo), ou que não houve; horas gerando com programação de até 1 MW; correlação; ressalva de que a programação não registra reprogramações em tempo real nem o motivo |
  | 12 | Disponibilidade sincronizada | há disponibilidade por usina | cobertura; resultado da conferência com a disponibilidade declarada; horas paradas sem e com unidade sincronizada; horas paradas com EVT com as unidades desligadas, também nas horas com programação de até 1 MW; variação da sincronizada média nos anos completos e, se o último ano é parcial, a média dele, quando há ao menos dois anos completos; anos em que a capacidade não sincronizada coincide com a reserva desligada e anos em que diverge, com a diferença; ressalva de que a sincronização não mostra o motivo da parada |
  | 13 | Afluência e vertimento | há dados hidrológicos | cobertura e resultado da conferência das vazões; sem a meta, só que os dados não foram cruzados; com a meta, horas com EVT por faixa, as sem dado e o % em que a água cabia nas turbinas, e o nível de montante nos dias com parada com EVT frente aos demais dias, inclusive nas três horas antes da janela diurna e dentro dela; ressalvas de que os dados não são consistidos pelo ONS e não mostram o motivo das paradas |
  | 14 | Horas com geração zero | sempre | total, com disponibilidade zero e com a usina disponível, por ano, e a diferença para as horas paradas com EVT |
  | 15 | Concentração diurna | sempre | razão diurna ÷ noturna da EVT por ano; nos anos com razão ≥ 2, a geração diurna em % da noturna, e a faixa dessa relação nos demais |
  | 16 | Distribuição ao longo do ano | sempre | nos anos completos, % da EVT de maio a outubro e de janeiro a abril e os três meses de maior EVT; sem anos completos com EVT, que não há como avaliar |
  | 17 | Mudança de classificação do vertimento pelo ONS | a mudança é detectada (FR-019) | o mês, as vazões típicas antes e depois, a % das horas e a EVT média antes; com anos completos antes e depois, a participação do vertimento mínimo na EVT nos dois períodos e que a série de EVT não é homogênea |
  | 18 | Conferência da geração | a conferência da geração aponta horas divergentes ou horas presentes em só uma fonte | o resultado da conferência e a energia das duas fontes |
  | 19 | Qualidade dos dados | sempre | registros sinalizados (quantidade, % e horas por regra), ou que não há; maior geração registrada, quando acima da potência instalada; EVT nos registros sinalizados, mantidos nos totais e fora dos extremos |

**Conclusão (US4)**

- **FR-045**: Os itens da conclusão DEVEM ser gerados pelas regras do catálogo abaixo, aplicadas aos resultados das análises e das conferências; nenhum item é escrito à mão nem fica fixo no texto.
  - As listas são quatro: pontos de atenção, possíveis problemas, a confirmar com o agente e a verificar em campo.
  - Os itens são ordenados pela lista, nessa ordem, e, dentro dela, pelo número da regra (na C2, pela unidade).
  - Todos os itens gerados ficam nos resultados; o limite de cinco itens por lista é aplicado na Geração do relatório.
- **FR-046**: Cada item DEVE ter:
  - lista e ordem na lista, a partir de 1;
  - regra (C1 a C11);
  - texto de uma frase, sem ponto final, com o número que sustenta o item;
  - seções de origem, guardadas pelo identificador da seção; o número da seção é resolvido na Geração do relatório, conforme as seções presentes.
- **FR-047**: Os itens NÃO DEVEM afirmar causa nem avaliar o desempenho da usina. O vocabulário é de indício ("indício", "possível", "a confirmar"), e nenhum item tem os termos "satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente" ou "culpa".
- **FR-048**: Quando a regra C2 dispara, os itens DEVEM nomear a unidade geradora como o ONS a identifica (UG e o número) e trazer os números que sustentam o indício.
- **FR-049**: Os itens NÃO DEVEM repetir o texto das constatações: nenhuma frase de constatação com 40 caracteres ou mais aparece num item.
- **FR-050**: Uma regra cuja condição não é atendida, ou cuja base não existe para a usina, NÃO DEVE gerar item. Sem nenhuma regra disparada, a conclusão fica sem itens.
- **FR-051**: O catálogo e os limiares DEVEM ser regras gerais, iguais para qualquer usina.

**Catálogo de regras da conclusão**

Seções citadas pelos itens:

| Seção citada | Título da seção no relatório |
|---|---|
| eventos | EVT por nível de geração e eventos de usina parada |
| programação | Operação verificada e programação diária do ONS |
| indicadores por UG | Indicadores oficiais do ONS por unidade geradora |
| hidrologia | Afluência, vertimento e nível do reservatório (ONS) |
| perfil horário | Perfil horário da geração e da EVT |
| indicadores anuais | Indicadores anuais |
| disponibilidade e geração | Disponibilidade e geração por ano |
| disponibilidade sincronizada | Disponibilidade operacional e sincronizada (ONS) |
| qualidade | Qualidade dos dados |

**C1. Paradas com EVT**
- **Dispara**: EVT com a usina parada ≥ 10 % da EVT do período.
- **Bases**: EVT; a programação diária só para a parcela de programação zero.
- **Pontos de atenção** (eventos; e programação, quando a parcela é citada): EVT com a usina parada, em GWh e em % da EVT, as horas e os anos que, somados do maior para o menor, chegam a pelo menos metade dessa EVT; quando ≥ 50 % das horas paradas com EVT do período comum com a programação tinham programação de até 1 MW, esse percentual.
- **A confirmar com o agente** (mesmas seções): motivo das paradas com vertimento turbinável, e com programação de até 1 MW quando a parcela é citada (ordens do ONS, restrições elétricas ou energéticas), com os registros dos maiores eventos.
- **A verificar em campo** (eventos): livro de operação e supervisório nas datas dos maiores eventos de parada com EVT: ordens recebidas, comandos de parada e abertura do vertedouro.

**C2. Unidade geradora**
- **Dispara**, para cada unidade, quando ao menos uma:
  - (a) a TEIFa mais recente está acima da TEIF de referência e a unidade responde por ≥ 2/3 dela, somadas as parcelas HDF e HEDF da decomposição (FR-025);
  - (b) a unidade registra limitação forçada de potência (HEDF > 0) em ≥ 50 % dos meses com horas por estado; desligamentos forçados (HDF) não contam para (b).
- **Bases**: horas por estado operativo; para (a), também a TEIFa publicada e a decomposição do mês mais recente.
- **Possíveis problemas** (indicadores por UG): "UGn: indício de problema na unidade"; com (b), os meses com limitação forçada sobre os meses com dado e as horas equivalentes dela e das demais unidades; com (a), a participação na TEIFa do mês, o valor da TEIFa e a referência, e, sem (b), a parcela que mais pesa.
- **A confirmar com o agente** (indicadores por UG): causa, histórico e situação atual da limitação forçada de potência da unidade (ou dos desligamentos forçados, quando a unidade dispara só por (a) e a parcela que mais pesa não é HEDF): ocorrências, ordens de serviço e correção prevista.
- **A verificar em campo** (indicadores por UG): com limitação forçada, a potência máxima que a unidade alcança hoje e os registros de limitação no supervisório e no livro de operação; sem ela, os registros dos desligamentos forçados no supervisório e no livro de operação.

**C3. Afluência que cabia nas turbinas**
- **Dispara**: as horas com EVT nas faixas "até uma unidade" e "entre uma e N unidades" somam ≥ 80 % das horas com EVT do período da hidrologia, inclusive as sem dado hidrológico.
- **Bases**: dados hidrológicos, com a conferência das vazões na meta.
- **Pontos de atenção** (hidrologia): esse percentual e o engolimento máximo da usina.

**C4. Concentração diurna**
- **Dispara**: a razão entre a EVT média diurna e a noturna é ≥ 2 em pelo menos um dos dois últimos anos da série, mesmo parcial.
- **Bases**: EVT.
- **Pontos de atenção** (perfil horário): os anos que atendem, com a marca de parcial, a janela diurna e a geração diurna em % da noturna em cada um.

**C5. Disponibilidade e taxas**
- **Dispara** quando ao menos uma:
  - disponibilidade declarada média do período abaixo da disponibilidade de referência;
  - DISPF médio do período abaixo da disponibilidade de referência;
  - TEIFa mais recente acima da TEIF de referência;
  - TEIP mais recente acima do IP de referência.
- **Bases**: EVT; os indicadores do ONS para as três últimas condições.
- **Pontos de atenção** (indicadores anuais, quando cita a disponibilidade declarada; indicadores por UG, quando cita o DISPF ou as taxas): num só item, cada medida que atende, nessa ordem, com o valor e a referência; a disponibilidade declarada também com a distância em pontos percentuais, e as taxas com o mês.

**C6. Parada com geração programada**
- **Dispara**: ≥ 1 evento de desvio da programação (usina parada com programação > 5 MW).
- **Bases**: programação diária.
- **Possíveis problemas** (programação): horas e eventos de desvio e o evento mais longo (início, fim e duração).
- **A confirmar com o agente** (programação): ocorrências nesses eventos, listados na aba PROG_EVENTOS_DESVIO da planilha.
- **A verificar em campo** (programação): registros de ocorrência no livro de operação nesses eventos.

**C7. Classificação de estados**
- **Dispara** quando ao menos uma:
  - num ano, a diferença entre a capacidade não sincronizada e a reserva desligada (FR-032) é ≥ 5 GWh, em módulo; anos sem horas por estado não entram;
  - ≥ 1 mês-unidade com o DISPF e as horas por estado divergentes, segundo a Conferência.
- **Bases**: disponibilidade por usina e horas por estado operativo, para a primeira; indicadores mensais e horas por estado, para a segunda.
- **Possíveis problemas** (disponibilidade sincronizada, quando cita os anos; indicadores por UG, quando cita os meses-unidade): os anos com a diferença, com sinal e em GWh, e a quantidade de meses-unidade divergentes.
- **A confirmar com o agente** (mesmas seções; e qualidade, quando junta a C8): classificação dos estados das unidades (reserva desligada e desligamento programado) informada ao ONS; quando a C8 também dispara, o item inclui as declarações de disponibilidade informadas ao ONS e as horas com geração acima da disponibilidade declarada.

**C8. Geração acima da disponibilidade declarada**
- **Dispara**: ≥ 100 h sinalizadas pela regra R7 no Tratamento.
- **Bases**: EVT.
- **Possíveis problemas** (qualidade): as horas, segundo a regra R7.
- **A confirmar com o agente** (qualidade), só quando a C7 não dispara: critério e horário da declaração de disponibilidade ao ONS, com as horas.

**C9. Geração e garantia física**
- **Dispara** quando ao menos uma:
  - geração média do período abaixo de 100 % da garantia física;
  - com ao menos dois anos completos, a EVT do último ano completo é a maior entre os anos completos.
- **Bases**: EVT.
- **Pontos de atenção** (indicadores anuais): a razão entre a geração média e a garantia física, com o valor da garantia física; o ano e a EVT dele.

**C10. Indisponibilidade longa**
- **Dispara** quando ao menos uma:
  - evento de indisponibilidade total com ≥ 30 dias (720 h);
  - unidade com INDISPPF ≥ 20 % num ano completo, nos indicadores anuais do ONS.
- **Bases**: EVT, para a primeira; indicadores anuais do ONS, para a segunda.
- **A confirmar com o agente** (disponibilidade e geração, quando cita o evento; indicadores por UG, quando cita as unidades): causa e documentação do evento mais longo (datas de início e fim e duração em horas) e das paradas programadas longas, por unidade e ano.
- **A verificar em campo** (mesmas seções): plano e registros de manutenção preventiva e corretiva das unidades geradoras, em especial dos anos citados.

**C11. Instrumentação e medição**
- **Dispara** quando ao menos uma:
  - dados hidrológicos com alguma hora sinalizada (H1 a H4), mesmo sem a meta da conferência das vazões;
  - ≥ 24 h sinalizadas pela regra R9 no Tratamento (geração com vazão turbinada nula).
- **Bases**: dados hidrológicos, para a primeira; EVT, para a segunda.
- **A verificar em campo** (hidrologia, para a primeira; qualidade, para a segunda): num só item, a instrumentação de nível e de vazão (réguas e sensores) que gera os dados hidrológicos informados ao ONS e a medição da vazão turbinada, com as horas da regra R9.

### Key Entities

- **Resultados das análises**: arquivo único da etapa, com a versão do formato; reúne a cobertura, os indicadores, os eventos, as distribuições, os perfis, as análises das bases complementares com os resultados das conferências correspondentes, os dados das figuras, as constatações e os itens da conclusão.
- **Indicador anual e do período**: valores da FR-011 e da FR-012, por ano civil ou no período completo.
- **Evento**: sequência de horas consecutivas numa condição (usina parada com EVT, indisponibilidade total ou desvio da programação), com início, fim, duração e médias.
- **Classe horária**: classe de uma hora segundo a programação, a sincronização das unidades ou a faixa de afluência.
- **Constatação**: título fixo, texto gerado e condição de existência.
- **Regra da conclusão**: identificador (C1 a C11), condição e limiares, listas em que gera item e o que cada item diz, seções citadas e bases necessárias.
- **Item da conclusão**: lista, ordem, regra, texto de uma frase e seções de origem.
- **Dados de figura**: séries e tabelas que a Geração do relatório desenha, sem recalcular.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o perfil da São Domingos e os dados locais, os resultados das Análises são os de hoje:
  - o relatório gerado a partir deles é idêntico ao de referência, o aprovado em 07/10/2026 com a conclusão aprovada: PDF com 30 páginas e o mesmo texto, Markdown idêntico, planilha com as 58 abas idênticas célula a célula e as 8 figuras idênticas byte a byte;
  - são 17 constatações e 19 itens da conclusão (5, 4, 5 e 5 por lista), com as onze regras disparadas e a UG2 nomeada em "Possíveis problemas".
- **SC-002**: Os totais conferem com a base: a soma das horas dos anos é o número de registros; a EVT do período é a soma da EVT horária; a EVT por nível de geração soma a EVT total, e as participações somam 100 %; as horas com geração zero somam a contagem na base.
- **SC-003**: 100 % das 10 grandezas têm perfil estatístico em todos os anos da série, com mínimo e máximo e as respectivas data e hora, e nenhum registro sinalizado entra no perfil nem nos extremos.
- **SC-004**: Na série sintética, sem as bases complementares, as Análises produzem exatamente 12 constatações, que reproduzem os fatos conhecidos (30 h de indisponibilidade total, 5 h de usina parada com EVT, mudança em jan/2024 e o registro de 60 MW fora dos extremos), sem parecer e sem nenhuma das afirmações removidas na auditoria.
- **SC-005**: Recebem classe 100 % das horas comuns com programação, 100 % das horas paradas com dado de disponibilidade e 100 % das horas com EVT do período da hidrologia; em cada caso, a soma das classes é igual ao total, e as horas paradas com EVT se dividem exatamente entre as duas classes de programação.
- **SC-006**: Nos testes, cada regra C1 a C11 dispara e deixa de disparar conforme a condição; 100 % dos itens têm regra e ao menos uma seção de origem; nenhum item tem termo de avaliação de desempenho nem repete frase de constatação; os itens estão ordenados por lista e por regra.
- **SC-007**: Em 100 % das tentativas de executar as Análises sem a Conferência concluída e atualizada, a etapa sai com código 5 e não grava nada.
- **SC-008**: Com o perfil da usina fictícia dos testes, as faixas de afluência dizem "entre uma e três unidades", as faixas de geração são as do perfil, nenhum texto gerado menciona a São Domingos nem os valores dela, e as análises das bases ausentes são omitidas.
- **SC-009**: 100 % dos números citados nas constatações e nos itens da conclusão vêm dos resultados gravados e são iguais aos das tabelas do relatório e das abas da planilha.
- **SC-010**: Com os dados locais da São Domingos, a cobertura, os indicadores, os eventos, as distribuições, os perfis, o perfil estatístico e os extremos da base de EVT são calculados em menos de 30 s, e o cruzamento com a programação diária, em menos de 2 min.

---

## Decisões do usuário

| Data | Decisão | Onde se aplica |
|---|---|---|
| 30/09/2026 | Auditoria do relatório: nenhum parecer de desempenho (satisfatório, atenção ou crítico) nem atribuição de causa ao vertimento ou às reduções de geração; FID e FIT deixam de ser calculados, e a disponibilidade declarada ÷ potência instalada passa a ser a "disponibilidade relativa", uma aproximação comparada com a disponibilidade de referência da garantia física; registros sinalizados fora dos extremos e do perfil estatístico | FR-011, FR-020 a FR-022, FR-043 |
| 02/10/2026 | Garantia física de 36,4 MWmed (ANEEL, valor vigente), no lugar dos 36,9 MWmed do RF de 2017; o valor fica no perfil da São Domingos | FR-007, FR-011, FR-012, regra C9 |
| 02/10/2026 | Contar as horas com geração exatamente zero por mês, separando as com disponibilidade zero das com a usina declarada disponível | FR-018; constatação "Horas com geração zero" |
| 07/10/2026 | Conclusão sucinta, com pontos de atenção, possíveis problemas (inclusive o indício de problema numa unidade geradora), o que confirmar com o agente e o que verificar em campo | FR-045 a FR-051 |
| 07/10/2026 | Texto da conclusão da São Domingos e catálogo de limiares aprovados sem ajustes ("aprovo os textos de conclusão") | FR-051, catálogo C1 a C11, SC-001 |
| 08/10/2026 | As horas paradas sem classe da programação formam o grupo "sem programação: fora do período ou sem valor programado" (57 delas, na São Domingos, estão dentro do período, em dias sem valor programado). A constatação dos indicadores cita quantos meses a Conferência reproduziu, com "em X dos N meses" quando nem todos são reproduzidos. | FR-025, FR-031, FR-044 |

---

## Assumptions

- **Causa**: os conjuntos do ONS não informam a causa do vertimento, das reduções de geração nem dos desligamentos; as Análises quantificam as condições, e a atribuição de causa depende de documentos do agente e do ONS.
- **Limiares**: as regras gerais (FR-006) e os limiares da conclusão são parâmetros de trabalho, não normativos; os principais aparecem na tabela de parâmetros do relatório, e os da conclusão, nas notas metodológicas do relatório.
- **Conclusão**: organiza indícios e verificações a partir dos dados abertos do ONS e não substitui a avaliação do fiscal.
- **Conferência**: as tolerâncias, a meta e a situação "não aplicável" de cada conferência estão na spec da Conferência; as Análises usam os resultados como estão.
- **Vazões abaixo da meta**: pela spec da Conferência, essa etapa sai com código 3 quando a conferência das vazões fica abaixo da meta. A FR-034 vale sempre que as Análises recebem esse resultado.
- **Registros da Coleta**: a cobertura usa a auditoria da extração da EVT e o manifesto de versões, gravados pela Coleta, que é etapa anterior; sem eles, a cobertura sai só da base.
- **Distribuição ao longo do ano**: a comparação de maio a outubro com janeiro a abril é a mesma para qualquer usina.
- **Horários**: os do ONS, já na hora de início e alinhados entre as bases pelo Tratamento.
- **Resultados**: o arquivo de resultados é interno ao fluxo; a versão legível dos resultados é a planilha do relatório.
