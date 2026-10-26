# Spec da Etapa 4: Análises

**Etapa**: 4 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-23

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

As Análises calculam, para uma usina de qualquer tipo coberto pelos dados abertos do ONS (UHE, PCH, CGH, UTE, UTN, EOL e UFV), tudo o que o relatório mostra. O caminho depende da série de referência da usina (FR-052):
- **hidrelétrica com EVT** (UHE, PCH ou CGH com a série da energia vertida turbinável): os indicadores anuais e do período, os eventos, as distribuições e os perfis da energia vertida turbinável (EVT) e o cruzamento com as bases complementares do ONS;
- **usina sem EVT** (as demais): as seções comuns, calculadas sobre a base horária comum do Tratamento, e as seções próprias do tipo: térmicas e nucleares, eólicas e solares, conjunto de usinas e afluência sem os cruzamentos com a EVT.

Nos dois caminhos, as Análises calculam também os dados de cada tabela e figura, as constatações, os itens da conclusão e os indicadores comparáveis que o relatório de carteira reúne. Partem só dos dados tratados, dos resultados da Conferência, do perfil da usina e dos registros da Coleta, e gravam um único arquivo de resultados, que a Geração do relatório apenas formata e desenha.

Cada número leva o nível em que o ONS o publica (usina, conjunto de usinas ou agregado), e nenhum número de conjunto é dividido entre as usinas. O que não tem base para a usina é omitido, com o motivo. Não há parecer: as constatações descrevem fatos dos dados, e a conclusão sai de regras declaradas por tipo, avaliadas só com dados da usina, que apontam indícios sem afirmar causa.

## Entradas e saídas

**Comando**: `python -m src analises --usina <slug>`, sem opções próprias. As regras comuns do fluxo (sintaxe, `--log-level`, perfil e código 4, `etapa.json`, pré-requisitos e `completo`) estão na spec da Coleta de dados.

**Entradas** (só leitura; nada das etapas anteriores é alterado; a etapa não lê nada de `data/raw/`):

| Entrada | Onde | O que as Análises usam |
|---|---|---|
| Perfil da usina | `usinas/<slug>/perfil.toml` | tipo, modalidade e `[cobertura]`; parâmetros técnicos, características da usina usadas nas análises, identificação (inclusive o conjunto e os códigos de programação) e fontes (FR-007) |
| Dados tratados | `data/usinas/<slug>/tratamento/` | **hidrelétrica com EVT**: base de EVT tratada, com as sinalizações R6 a R9, e o resultado das regras R1 a R9; séries horárias de disponibilidade, hidrologia e geração, com as sinalizações de qualidade, as ausências e as auditorias. **Usina sem EVT**: a base horária comum (`base_horaria.csv`) e as ausências da série de referência; na hidrelétrica, a hidrologia; nas térmicas, o despacho por hora e por unidade de planejamento e o CVU e o CMO semanais; nas eólicas e solares, o fator de capacidade horário, a restrição com detalhe por semi-hora (com a razão) e, quando a série de referência é a restrição com detalhe, a Geração por usina do conjunto. **Nos dois caminhos**: indicadores por unidade geradora (mensais e anuais), horas por estado operativo e TEIFa/TEIP mensais; programação horária e dias sem arquivo |
| Resultados da Conferência | `data/usinas/<slug>/conferencia/` | `conferencias.pkl`: das conferências aplicadas, as tabelas que seguem nos resultados (FR-005); nas usinas sem EVT, também `nao_aplicaveis.csv`, com as conferências que não se aplicam e o motivo |
| Registros da Coleta | `data/usinas/<slug>/coleta/` | auditoria da extração da EVT; `datas_obtencao.csv` (datas de obtenção dos conjuntos e resumo do manifesto da EVT, na cobertura); auditoria dos arquivos da programação diária; ficha do cadastro e auditoria da sua leitura; registro dos dicionários de dados. Nas usinas sem EVT, também o resumo do `etapa.json` (linhas próprias da usina sem valor e o período delas), `trechos.csv`, `composicao_conjunto.csv`, `capacidade_ficha.csv`, `capacidade_membros.csv` e `tipo_publicado.csv` |

**Saídas**:

| Arquivo | Conteúdo |
|---|---|
| `data/usinas/<slug>/analises/resultados.pkl` | resultados das análises (FR-005), com a versão do formato, que a Geração do relatório confere ao ler, no relatório da usina e no de carteira (FR-062); nenhuma outra etapa lê esse arquivo |
| `data/usinas/<slug>/analises/etapa.json` | manifesto da etapa; o `resumo` traz o período e as horas analisadas, a quantidade de constatações, os itens da conclusão por lista e as regras que dispararam, e as bases complementares analisadas ou ausentes; nas usinas sem EVT, também o tipo, as horas por nível e as seções e regras omitidas |

**Códigos de saída** (o código 4, de perfil inválido, é regra comum, na spec da Coleta de dados):

| Código | Quando |
|---|---|
| 0 | sucesso |
| 1 | erro, inclusive falha de gravação; o resultado anterior, se houver, fica como estava |
| 5 | Conferência sem resultados concluídos, com resultados desatualizados ou em outro formato; nada é gravado |

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

### User Story 7 - Seções comuns nas usinas sem EVT, com o nível de cada número (Priority: P2)

Como fiscal, quero que, numa usina sem a série da energia vertida turbinável (térmica, nuclear, eólica, solar ou hidrelétrica sem essa série), as Análises calculem as seções comuns sobre a base horária comum, cada número com o nível em que o ONS o publica, e omitam, com o motivo, o que não tem base para a usina. Assim analiso a geração, a disponibilidade e a programação de qualquer usina com dado próprio ou de conjunto.

**Why this priority**: É a base das seções e das regras de todos os tipos novos.

**Independent Test**: Executar as Análises com as usinas fictícias de cada tipo sem EVT e conferir as seções comuns, os níveis, as omissões e os campos de EVT vazios; executar com a hidrelétrica fictícia com EVT e conferir que os resultados não mudam.

**Acceptance Scenarios**:

1. **Given** a base horária comum de uma térmica, **When** as Análises rodam, **Then** os indicadores anuais, a série diária, a geração mensal e a sazonalidade, o perfil horário, a disponibilidade e a programação saem por ano e por nível, sem nenhuma seção de EVT (UTE William Arjona: 46.243 horas da Geração por usina, id ONS MSUTWI, de 10/07/2021 a 18/10/2026, todas no nível da usina).
2. **Given** uma série de referência com menos de 12 meses distintos, **When** as Análises rodam, **Then** a sazonalidade é omitida, com o motivo (UFV Seriemas 1: 3 meses distintos).
3. **Given** uma usina sem a Disponibilidade por usina ou sem os indicadores oficiais, **When** as Análises rodam, **Then** as seções que dependem dessas bases são omitidas, com o motivo.
4. **Given** uma térmica ou uma hidrelétrica sem EVT, **When** a conclusão é gerada, **Then** as regras comuns C2, C5, C8 e C10 são avaliadas sobre a base horária comum, só com dados da usina, e as que não têm base vão para as omissões, com o motivo (William Arjona: C8 e C10 com itens; C5 não avaliada, sem IP e TEIF de referência no perfil).
5. **Given** uma hidrelétrica com EVT, **When** as Análises rodam, **Then** os resultados de antes não mudam, e só entram o tipo, a modalidade e os indicadores da carteira (SC-001).

---

### User Story 8 - Térmicas e nucleares (Priority: P2)

Como fiscal, quero ver, numa térmica ou nuclear, como ela foi despachada por motivo, a inflexibilidade, se atendeu ao despacho, quanto tempo ficou disponível sem ser despachada e como o custo variável unitário (CVU) se compara ao custo marginal de operação (CMO), e quero as regras da conclusão próprias das térmicas. Assim preparo a fiscalização de uma térmica com o mesmo rigor da hidrelétrica.

**Why this priority**: As térmicas têm a cobertura mais completa depois das hidrelétricas, com indicadores oficiais por unidade.

**Independent Test**: Executar as Análises com a UTE fictícia (um ano inteiro sem geração e disponível, troca de unidade de planejamento, CVU com duas revisões por semana e um valor negativo, CMO com uma semana republicada) e conferir as seções de térmica e as regras C12 a C15 no limiar e abaixo dele.

**Acceptance Scenarios**:

1. **Given** o despacho tratado, **When** as Análises rodam, **Then** a geração de cada motivo sai por mês e por ano, com a parcela na geração total publicada.
2. **Given** a geração programada e a verificada, **When** comparadas, **Then** saem as horas e a energia abaixo e acima da programada além de 5 MW, os maiores desvios e as horas sem programação com a geração acima dela (William Arjona: 2.821 h abaixo da programada, com 112.233 MWh, e 114 h sem programação, com 3.028 MWh acima).
3. **Given** o CVU semanal e o CMO do subsistema, **When** comparados, **Then** cada semana e unidade fica abaixo, acima, igual ou sem comparação, com a geração da unidade, sem julgar o despacho; o CVU ausente, zero ou negativo fica sem comparação e é contado (William Arjona: CVU zero em 250 das 267 semanas da unidade 434).
4. **Given** uma térmica sem geração no período, **When** as Análises rodam, **Then** não há divisão por zero, e a constatação diz que a usina ficou disponível e não foi despachada, com as horas e a potência disponível.

---

### User Story 9 - Eólicas e solares (Priority: P3)

Como fiscal, quero ver, numa eólica ou solar, o fator de capacidade, a energia cortada por restrição de operação (constrained-off), com a razão da restrição, a relação entre o recurso (vento ou irradiância) e a geração e a aderência à programação, cada número identificado como da usina ou do conjunto. Assim avalio as usinas que mais crescem em MS.

**Why this priority**: O ONS publica as eólicas e solares quase sempre em conjunto, o que pede a regra de granularidade resolvida antes.

**Independent Test**: Executar as Análises com a EOL e a UFV fictícias (vento inválido, semi-horas restritas com as três razões, a UFV em conjunto com série curta) e conferir as seções, os níveis e as regras C16 a C19.

**Acceptance Scenarios**:

1. **Given** a restrição com detalhe da usina, **When** as Análises rodam, **Then** a energia cortada sai só das semi-horas com a marca de restrição, por mês e por razão, com as semi-horas sem a marca e as sem estimativa contadas à parte (EOL Praia Formosa: 184.769 MWh de 10/2021 a 10/2026, contra 355.038 MWh da diferença bruta).
2. **Given** o vento marcado como inválido pelo ONS ou acima do limite físico, **When** a relação recurso × geração é calculada, **Then** essas semi-horas ficam fora das faixas e são contadas (Praia Formosa: 13.157 semi-horas inválidas e 111 acima de 40 m/s).
3. **Given** a geração, o fator de capacidade e a programação publicados só para o conjunto, **When** as Análises rodam, **Then** esses números aparecem como do conjunto, nunca divididos entre as usinas, e as regras que pedem a base da usina não são avaliadas (UFV Seriemas 1: Conj. Inocência 230 kV, CJU_MS4FINO; C18 e C19 não avaliadas).
4. **Given** a geração programada e a verificada da usina, **When** comparadas, **Then** saem o desvio médio e os maiores desvios (Praia Formosa: desvio médio absoluto de 10,4 % da potência instalada, abaixo do limiar de 15 % da C19).

---

### User Story 10 - PCH e CGH em conjunto e hidrelétricas sem EVT (Priority: P4)

Como fiscal, quero, numa PCH ou CGH em conjunto de usinas, os números do conjunto identificados como tais, a composição do conjunto em cada período e o peso da usina na potência dele, sem conclusão tirada de dado que não é da usina; e, numa hidrelétrica sem EVT com dados hidrológicos, a afluência e o nível do reservatório. Assim não tiro conclusão de dado que não existe.

**Why this priority**: A maioria das PCH e todas as CGH de MS são Tipo III; mesmo as PCH em conjunto têm a geração da usina vazia no ONS.

**Independent Test**: Executar as Análises com a PCH fictícia em conjunto (entrada no conjunto no período, uma térmica que sai, conjunto publicado como "TÉRMICA") e com a CGH fictícia com geração própria e dados hidrológicos, e conferir a composição por trecho, o peso da usina, a divergência do tipo publicado, a conclusão sem itens e a afluência sem os cruzamentos com a EVT.

**Acceptance Scenarios**:

1. **Given** a PCH Bandeirante, **When** as Análises rodam, **Then** a geração do Conj. Chapadão sai por trecho de composição (três: até 26/09/2019; até 30/06/2025; desde 01/07/2025, só com as quatro PCH), com os tipos e a potência somada de cada trecho, sem fator de capacidade do conjunto e sem divisão entre as usinas.
2. **Given** a usina em conjunto, **When** as Análises rodam, **Then** o peso dela na potência do conjunto sai por trecho, sem estimar a geração dela (Bandeirante: 6,7 % de 27/09/2019 a 30/06/2025 e 35,7 % desde 01/07/2025).
3. **Given** o tipo publicado na série do conjunto diferente dos tipos da composição, **When** as constatações são montadas, **Then** a divergência aparece na qualidade dos dados, como fato (Bandeirante: "TÉRMICA" (Biomassa) de 01/07/2025 a 20/10/2026, com só PCH na composição).
4. **Given** a usina em conjunto sem base no nível da usina, **When** a conclusão é gerada, **Then** ela fica sem itens, com as regras nas omissões e a frase que explica a falta de base no nível da usina.
5. **Given** uma hidrelétrica sem EVT com os dados hidrológicos e a hora conferida pela geração da usina, **When** as Análises rodam, **Then** saem a tabela anual e as médias mensais da hidrologia, sem os cruzamentos com a EVT; sem a hora conferida, só a cobertura e o resultado da conferência.

---

### User Story 11 - Indicadores para o relatório de carteira (Priority: P5)

Como fiscal, quero que os resultados de cada usina tragam indicadores comparáveis e a quantidade de itens de cada lista da conclusão, com o nível de cada número. Assim a carteira compara e ordena as usinas sem refazer nenhuma etapa.

**Why this priority**: Depende das análises de todos os tipos; é a base do relatório de carteira.

**Independent Test**: Executar as Análises com as usinas fictícias dos sete tipos e conferir as chaves fixas dos indicadores da carteira, os vazios onde o indicador não se aplica e as contagens da conclusão.

**Acceptance Scenarios**:

1. **Given** os resultados de uma usina, **When** as Análises gravam, **Then** os indicadores da carteira trazem o ano (o último completo da série ou, sem ele, o parcial mais recente, marcado) e cada indicador com valor, nível e unidade, vazio quando não se aplica (William Arjona, 2025: disponibilidade de 20,9 %, TEIFa de 30,5 % e atendimento ao despacho de 6,25 %, com 2 de 32 horas com programação; fator de capacidade e energia cortada vazios).
2. **Given** uma usina sem nenhuma regra avaliada com dado da usina, **When** as Análises gravam, **Then** as contagens da conclusão ficam vazias, e não zero (PCH Bandeirante).
3. **Given** uma hidrelétrica com EVT, **When** as Análises gravam, **Then** só o campo dos indicadores da carteira muda; o relatório não muda.

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
- **Base complementar ausente**: as análises, as constatações e as regras que dependem dela não são feitas, e a conferência correspondente, registrada como "não aplicável" pela Conferência, não entra nos resultados (nas usinas sem EVT, entra só na lista das conferências não aplicáveis, com o motivo).
- **Constatações condicionais**: a do cadastro e a da conferência da geração só aparecem com divergência.
- **Nenhuma regra da conclusão dispara**: a conclusão fica sem itens; a frase mostrada nesse caso está na spec da Geração do relatório.
- **Mais de cinco itens numa lista**: todos ficam nos resultados, na ordem do catálogo; o corte em cinco é feito na Geração do relatório.
- **C7 e C8 disparam juntas**: a pergunta ao agente fica num só item, o da C7, que cita as horas da regra R7.
- **Mais de uma unidade atende à C2**: um item por lista para cada unidade, na ordem das unidades.

Nas usinas sem EVT:

- **Hidrelétrica sem a série da EVT**: segue o caminho sem EVT; as regras C1, C3, C4, C6, C7, C9 e C11, que dependem da base de EVT, não são avaliadas e vão para as omissões, com o motivo.
- **Série de referência em dois níveis** (da usina e do conjunto, em trechos): as tabelas por ano, por mês e por hora têm uma linha por nível; nenhum número mistura os dois.
- **Série de referência com menos de 12 meses distintos**: a sazonalidade é omitida, e a C18 não é avaliada; as tabelas por ano trazem o ano parcial, marcado.
- **Perfil sem IP e TEIF de referência**: a C5 não é avaliada, e a C2 só dispara pela limitação forçada recorrente. **Perfil sem garantia física**: a C18 não é avaliada.
- **Número do conjunto**: aparece identificado ("do conjunto <nome>"), nunca dividido entre as usinas, e não entra na conclusão da usina.
- **Usina em conjunto sem base no nível da usina**: a conclusão fica sem itens, com a frase que explica; as contagens da conclusão nos indicadores da carteira ficam vazias, e não zero.
- **Composição do conjunto que muda no período**: os números do conjunto saem por trecho de composição, com as usinas e os tipos de cada trecho.
- **Usina do conjunto sem unidade em operação no trecho, ou sem unidade cadastrada**: fica sem potência no trecho e é contada; o peso dela nesse trecho fica vazio.
- **Tipo publicado na série do conjunto diferente dos tipos da composição**: o tipo das usinas vem do CEG, e a divergência vai para a qualidade dos dados.
- **Térmica sem geração no período**: nenhuma divisão por zero; a constatação diz que a usina ficou disponível e não foi despachada.
- **CVU ausente, zero ou negativo**: a semana fica sem comparação com o CMO e é contada.
- **Estimativa ausente** (geração estimada 0 com a verificada acima de 1 MW): fica fora dos totais e das médias da estimada, e é contada; na semi-hora restrita sem estimativa, o corte não é calculado.
- **Recurso acima do limite físico** (vento acima de 40 m/s; irradiância acima de 1.500 W/m²), sem a marca do ONS: fica fora das faixas do recurso × geração e é contado.
- **Eólica ou solar com a série própria e a programação do conjunto**: a programação é comparada com a geração do conjunto, numa base à parte, identificada como do conjunto; a C19 não é avaliada.
- **Hidrelétrica sem EVT sem a hora dos dados hidrológicos confirmada pela geração**: só a cobertura e o resultado da conferência.
- **Ano dos indicadores da carteira sem a TEIFa de dezembro**: a TEIFa fica vazia; no ano parcial, vale a do último mês publicado.

---

## Requirements *(mandatory)*

### Functional Requirements

**Execução e resultados (US5)**

- **FR-001**: A etapa DEVE ser executada por `python -m src analises --usina <slug>`, sem opções próprias, e terminar com os códigos 0, 1 ou 5 da tabela de Entradas e saídas.
- **FR-002**: Antes de gravar, a etapa DEVE conferir que a Conferência está concluída e atualizada. Se não estiver, DEVE sair com código 5, sem gravar nada, e indicar a Conferência como a etapa a executar antes.
- **FR-003**: As Análises DEVEM ler só as entradas de Entradas e saídas. NÃO DEVEM acessar o portal do ONS nem `data/raw/`, refazer o tratamento dos dados nem refazer conferências: os resultados de conferência são lidos como estão, e as tabelas das conferências aplicáveis seguem nos resultados sem alteração (FR-005). As datas de obtenção dos conjuntos e o resumo do manifesto da EVT vêm de `datas_obtencao.csv`, gravado pela Coleta.
- **FR-004**: A etapa DEVE gravar os resultados num único arquivo, `resultados.pkl`, com a versão do formato, que muda quando os campos mudam (hoje, a 3), e o `etapa.json` com o `resumo` de Entradas e saídas. Qualquer falha DEVE ser registrada no log e encerrar a etapa com código 1; numa falha de gravação, o arquivo anterior, se houver, fica como estava.
- **FR-005**: Os resultados DEVEM conter tudo o que o relatório mostra: números, tabelas, dados das figuras (FR-041), constatações (FR-044) e itens da conclusão (FR-045). A tabela de parâmetros é a exceção (FR-042). As tabelas de cada conferência aplicável DEVEM seguir, como estão, junto com os resultados da base a que se referem: resumo, comparação mensal e divergências da geração; resumo e divergências da disponibilidade; alinhamento das vazões; divergências entre o DISPF e as horas por estado operativo; recálculo da TEIFa e da TEIP; divergências do cadastro. Os demais campos de cada resultado de conferência, como a situação "não aplicável" e o motivo, ficam nos resultados da Conferência. Também DEVEM seguir, como estão, os dias sem arquivo e a auditoria dos arquivos da programação diária, as ausências e as auditorias da disponibilidade, da hidrologia e da geração e a auditoria da leitura do cadastro; a auditoria da extração dos indicadores oficiais não segue nos resultados. A Geração do relatório só formata e desenha, sem recalcular; faz apenas seleções e contagens simples sobre os resultados, como os eventos que lista, o maior valor citado numa legenda e o total de horas por ano numa figura.

  Os resultados DEVEM trazer também, para todos os tipos:
  - o tipo e a modalidade da usina, do perfil;
  - o nível (usina, conjunto ou agregado) e o identificador da série de referência e de cada base de nível variável (`niveis`);
  - os trechos do período, de `trechos.csv` da Coleta;
  - as seções comuns das usinas sem EVT (`comum`, FR-052) e as seções do tipo: térmica (FR-056), eólica e solar (FR-058), conjunto (FR-060) e afluência sem EVT (FR-061);
  - os indicadores da carteira (FR-062);
  - as seções e as regras não avaliadas, cada uma com o motivo (`omitidos`; FR-053 e FR-054).

  Nas usinas sem EVT, seguem também, junto das seções do tipo, os resultados das conferências G1 a G5 aplicadas e a hora dos dados hidrológicos conferida pela geração, e a lista das conferências não aplicáveis, com o motivo. Nas hidrelétricas com EVT, os campos de antes mantêm os mesmos valores, e dos campos novos só o tipo, a modalidade e os indicadores da carteira são preenchidos. Nas usinas sem EVT, os campos da base de EVT ficam vazios.

**Regras gerais e valores do perfil (US6)**

- **FR-006**: As regras gerais abaixo DEVEM ser as mesmas para qualquer usina; o perfil não as altera.

  | Regra geral | Valor |
  |---|---|
  | Usina parada | geração ≤ 1 MW |
  | Hora com EVT | EVT > 0 |
  | Indisponibilidade total | disponibilidade declarada ≤ 0,001 MW; nas usinas sem EVT, a disponibilidade operacional da Disponibilidade por usina |
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
  | Diferença entre a taxa operativa e a oficial (figura e C20) | 1 p.p. |
  | Identidade das horas por estado operativo | soma das parcelas igual às horas do período, com diferença ≤ 0,1 h |
  | Capacidade não sincronizada × reserva desligada (constatação) | coincidem no ano com diferença ≤ 0,1 GWh |
  | Distribuição ao longo do ano | só anos completos; maio a outubro × janeiro a abril; três meses de maior EVT |
  | Ano parcial | primeiro registro depois de 1º de janeiro 00h ou último antes de 31 de dezembro 23h |
  | Sazonalidade nas usinas sem EVT | 12 meses distintos na série do nível (FR-053) |
  | Atendimento ao despacho (térmicas) | nas horas com programação > 1 MW, desvio verificada − programada além de 5 MW, para baixo ou para cima; nas horas com programação ≤ 1 MW, geração mais de 5 MW acima da programada |
  | Disponível sem despacho (térmicas) | disponibilidade operacional > 0,001 MW, programação ≤ 1 MW e geração ≤ 1 MW |
  | Faixas do recurso (eólicas e solares) | 2 m/s de vento; 100 W/m² de irradiância |
  | Limite físico do recurso | vento ≤ 40 m/s; irradiância ≤ 1.500 W/m² |
  | Maiores desvios listados (térmicas, eólicas e solares) | 15 horas, de maior desvio absoluto |
  | Limiares da conclusão | catálogo C1 a C20 (FR-045) |

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
  | Tipo e modalidade | `usina.tipo`, `usina.modalidade` | caminho e seções do tipo (FR-052), regras do tipo, indicadores da carteira |
  | Cobertura | `[cobertura]` | nível de cada base e motivo das omissões |
  | CEG e conjunto | `identificacao.ceg`, `identificacao.id_conjunto` | composição do conjunto e peso da usina (FR-060) |
  | Códigos de programação | `identificacao.cod_programacao` ou `identificacao.codigos_programacao` | identificador da programação no nível dela |
  | Razão entre a garantia física e a potência instalada | `parametros.garantia_fisica_mwmed` ÷ P | regra C18 |

  Nas eólicas e solares, P é a capacidade instalada. Os campos de cada tipo estão na spec da Coleta de dados: fora da UHE, a garantia física e o IP e a TEIF de referência são opcionais (as eólicas e solares não têm IP nem TEIF), e os campos hidráulicos e de EVT só existem nas hidrelétricas que os pedem. Sem um campo, o que o usa não é avaliado e vai para as omissões, com o motivo (FR-054).

- **FR-008**: As análises que dependem das características da usina DEVEM ser derivadas do perfil:
  - faixas de afluência "até uma unidade", "entre uma e N unidades" e "acima do engolimento máximo", com N escrito por extenso de 1 a 10 ("duas" para 2) e em algarismos acima de 10;
  - faixas intermediárias da EVT por nível de geração;
  - limite do vertimento mínimo.
- **FR-009**: Os textos gerados nas Análises (constatações e itens da conclusão), em qualquer tipo de usina, NÃO DEVEM ter nome, identificador ou valor de usina que não venha do perfil ou dos dados. Os números DEVEM seguir o padrão brasileiro (milhar com ponto, decimal com vírgula), com datas "dd/mm/aaaa HHh", meses "mmm/aaaa" e "–" para valor ausente.

**Cobertura (US1)**

- **FR-010**: A cobertura da série de EVT DEVE trazer:
  - primeiro e último registro; horas observadas e esperadas, pela grade horária contínua entre os dois; horas ausentes, com a lista; horários duplicados;
  - por ano: primeiro e último registro, horas observadas, horas do ano civil (8.760 ou 8.784), cobertura em % e marca de ano parcial; a lista dos anos parciais e a dos completos;
  - os agentes, com o primeiro e o último registro e as horas de cada um;
  - a identificação da usina nos dados: código, reservatório, rio, bacia e subsistema;
  - quando existem, o resumo da auditoria da extração (arquivos lidos, com registros da usina, sem registros, com falha e linhas com identificação divergente) e o do manifesto de versões, da linha da EVT em `datas_obtencao.csv` da Coleta (arquivos registrados, publicação mais recente no portal e registro mais recente). Sem eles, a cobertura sai só da base.

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

**Dois caminhos e seções comuns das usinas sem EVT (US7)**

- **FR-052**: A etapa DEVE escolher o caminho pela série de referência da usina (FR-054 da spec da Coleta de dados):
  - **hidrelétrica com EVT** (UHE, PCH ou CGH com a Energia Vertida Turbinável na cobertura): as análises das FR-010 a FR-040 sobre a base de EVT, sem mudança;
  - **usina sem EVT** (as demais): as seções comuns, calculadas sobre a base horária comum do Tratamento (FR-035 da spec do Tratamento de dados), cada número com o nível em que o ONS o publica e com uma linha por nível nas tabelas:
    - **cobertura** da série de referência: período, horas observadas e esperadas, horas ausentes e sem valor, anos parciais e completos, meses distintos, horas por nível e quantidade de trechos;
    - **indicadores anuais**, por ano e nível: horas, horas com valor, geração média, energia, geração máxima, horas paradas (geração ≤ 1 MW) e o percentual delas; o fator de capacidade só nas eólicas e solares e só no nível da usina; a disponibilidade operacional média e relativa (÷ P), só da usina;
    - **série temporal**: médias diárias da geração, por nível, e da disponibilidade operacional da usina;
    - **geração mensal**, por mês e nível, e **sazonalidade** (geração média por mês do ano), com o período mínimo da FR-053;
    - **perfil horário** da geração, por hora do dia e nível;
    - **disponibilidade**, quando há a Disponibilidade por usina, sempre da usina e só comparada com a geração da usina: resumos mensal e anual (médias da disponibilidade operacional e sincronizada e da geração, capacidade não sincronizada, horas de indisponibilidade total, horas paradas com a usina disponível e com unidade sincronizada, horas com geração acima da disponibilidade declarada), os eventos de indisponibilidade total (base da C10) e as horas da regra R7 (base da C8);
    - **indicadores oficiais** por unidade geradora, quando há, como nas FR-023 a FR-025, com as horas da base horária comum no nível da usina no lugar das da base de EVT e a disponibilidade operacional no lugar da declarada;
    - **programação × verificada**, nas horas comuns do mesmo nível: geração e programação médias, desvio médio e desvio médio absoluto, correlação, horas e eventos de usina parada com programação acima de 5 MW e dias sem arquivo, no período e por mês;
    - **afluência, vertimento e nível**, nas hidrelétricas sem EVT com os Dados hidrológicos (FR-061);
    - **qualidade dos dados**: horas sinalizadas por código (G1, D1 a D4 e R7, FR-035 da spec do Tratamento de dados), horas sem valor, ausências listadas e as linhas próprias da usina sem valor na Geração por usina, com o período delas (FR-047 e FR-048 da spec da Coleta de dados);
    - **identificação**: os agentes proprietário e operador atuais das unidades ativas, da Capacidade de geração, sem o histórico, para a capa e o resumo executivo.

  Nas usinas sem EVT, os campos da base de EVT ficam vazios, e as seções do tipo vêm das FR-056, FR-058, FR-060 e FR-061. A ordem das seções no relatório está na FR-041 da spec da Geração do relatório.
- **FR-053**: A sazonalidade (distribuição por mês do ano) DEVE pedir 12 meses distintos na série de cada nível. Sem eles, é omitida e entra nas omissões, com o motivo. Uma regra nova com limiar anual só é avaliada com o período mínimo dela e nos anos completos: a C18 pede 12 meses distintos na série. As tabelas por ano aceitam o ano parcial, marcado. C1 a C11 não têm período mínimo.

**Térmicas e nucleares (US8)**

- **FR-056**: Nas UTE e UTN com o despacho, os resultados DEVEM trazer, no campo `termica`:
  - **geração por motivo**: energia verificada e programada de cada motivo publicado (ordem de mérito, inflexibilidade, razão elétrica, garantia energética, GFOM, reposição de perdas, exportação, reserva de potência, GSUB e unit commitment), por mês e por ano, com a parcela na geração total publicada; à parte, os detalhes que se sobrepõem a outros motivos (inflexibilidade pura e embutida no mérito, ordem de demérito e constrained-off); só os motivos com energia no período. A soma das parcelas pode diferir de 100 %, porque os motivos publicados não formam uma partição exata;
  - **inflexibilidade**: a programada e a verificada, por mês (tabela e figura), dentro da geração por motivo, com a parte programada não verificada (base da C14);
  - **atendimento ao despacho**: nas horas com geração programada acima de 1 MW, o desvio verificada − programada; as horas e a energia abaixo e acima além de 5 MW, por mês e por ano; os maiores desvios, até 15 horas; e, nas horas sem programação, as horas e a energia com a geração mais de 5 MW acima da programada (base da C15);
  - **disponível sem despacho**: horas com a disponibilidade operacional acima de 0,001 MW, sem programação e sem geração (até 1 MW), no período e por ano, com a potência disponível média;
  - **CVU × CMO**: por semana operativa, o CVU de cada unidade de planejamento e o CMO médio semanal do subsistema, levados à hora pelo intervalo da semana operativa para os cruzamentos (FR-040 da spec do Tratamento de dados); por unidade, as semanas com o CVU abaixo, acima e igual ao CMO, com a geração em cada caso, e as sem comparação, sem julgar o despacho. O CVU sinalizado (ausente, zero ou negativo; FR-038 da spec do Tratamento de dados) fica sem comparação e é contado;
  - **usina sem geração no período**: nenhuma divisão por zero; a constatação diz que a usina ficou disponível e não foi despachada, com as horas e a potência disponível;
  - as horas com despacho (programação acima de 1 MW), no período e por ano, e os resultados da G3 e da G4 (FR-020 e FR-021 da spec da Conferência), para as legendas.

  Sem o despacho, ou sem horas dele no período, as seções de térmica vão para as omissões, com o motivo; sem o CVU ou o CMO (o CMO pede o subsistema no perfil), ou sem semanas comuns, só o CVU × CMO.
- **FR-057**: Nas UTE e UTN, a conclusão DEVE usar, além das regras comuns C2, C5, C8 e C10 sobre a base horária comum, as regras C12 a C15 do catálogo, só com os dados da usina:
  - C12: geração abaixo da programada em horas recorrentes (possíveis problemas; a confirmar com o agente);
  - C13: horas disponíveis sem despacho em semanas com o CVU abaixo do CMO (a confirmar com o agente);
  - C14: geração por inflexibilidade abaixo da programada (pontos de atenção);
  - C15: geração acima da programada, sem programação correspondente, em horas recorrentes (a confirmar com o agente).

  Os limiares ficam em `src/comum/regras.py`, calibrados na UTE William Arjona e aprovados pelo usuário em 20/10/2026.

**Eólicas e solares (US9)**

- **FR-058**: Nas EOL e UFV, os resultados DEVEM trazer, no campo `renovavel`:
  - **fator de capacidade publicado**: Σ geração verificada ÷ Σ capacidade instalada nas horas com as duas, da usina ou do conjunto (com o nível), por mês e por ano, com a marca de ano parcial e as horas sinalizadas (fator fora de 0 a 1; geração acima da capacidade). Com série própria, o fator calculado da geração da usina e da capacidade do perfil fica nos indicadores anuais comuns (FR-052), identificado no relatório como "calculado neste relatório";
  - **energia cortada**: só nas semi-horas com a marca de restrição (FR-042 da spec do Tratamento de dados), por mês, por ano e por razão (REL, CNF, ENE e "sem razão publicada"), em MWh e em % da energia estimada nas semi-horas com a marca, e as horas restritas; a geração verificada e a estimada somadas nas mesmas semi-horas, as com estimativa; a diferença bruta (estimada − verificada em todas as semi-horas) à parte, para comparação. Com a razão do conjunto, a razão é do conjunto e a energia é da usina. Contadas à parte: as semi-horas sem a marca de restrição, fora do total, e as sem estimativa (estimada 0 com a geração verificada acima de 1 MW), em especial as restritas, em que o corte não pôde ser calculado;
  - **recurso × geração**: geração verificada média e estimada média (sem as estimativas ausentes) por faixa de vento (m/s) ou de irradiância (W/m²), sem as semi-horas com o recurso marcado como inválido pelo ONS nem as com o recurso fisicamente implausível (vento acima de 40 m/s; irradiância acima de 1.500 W/m²), contadas;
  - **aderência à programação**: na seção comum de programação (FR-052), o desvio médio absoluto (MW e % da potência instalada) e os maiores desvios, até 15 horas, no nível da programação. Na eólica ou solar com a série própria na restrição com detalhe e a programação do conjunto, a programação é comparada com a Geração por usina do conjunto, numa base à parte, identificada como do conjunto, fora da base horária da usina e sem a C19;
  - **série curta**: a seção ou parte com período mínimo declarado (a sazonalidade, 12 meses distintos; FR-053) é omitida, com o motivo;
  - os resultados da G1, da G2 e da G5 aplicadas (FR-023 a FR-025 da spec da Conferência), para as legendas.

  Sem a base, ou sem horas ou semi-horas dela no período, cada seção vai para as omissões, com o motivo.
- **FR-059**: Nas EOL e UFV, a conclusão DEVE usar as regras C16 a C19 do catálogo, só com os dados da usina:
  - C16: energia cortada da usina acima de um limiar da energia estimada (pontos de atenção);
  - C17: recurso (vento ou irradiância) inválido acima de um limiar das semi-horas da usina (a verificar em campo);
  - C18: fator de capacidade publicado da usina abaixo da razão entre a garantia física e a capacidade instalada, só com a garantia física no perfil (pontos de atenção);
  - C19: desvio médio entre a geração programada e a verificada da usina acima de um limiar, só com a programação no nível da usina (a confirmar com o agente).

  Os limiares ficam em `src/comum/regras.py`, calibrados na UFV Seriemas 1 e na EOL Praia Formosa e aprovados pelo usuário em 21/10/2026. As regras comuns C2, C5, C8 e C10 não valem para eólicas e solares, que não têm a Disponibilidade por usina nem os indicadores por unidade geradora no ONS.

**Conjunto de usinas e hidrelétricas sem EVT (US10)**

- **FR-060**: Em toda usina em conjunto com a geração do conjunto (a série de referência do conjunto ou, na eólica ou solar com série própria, a Geração por usina do conjunto), os resultados DEVEM trazer, no campo `conjunto`, a partir de `trechos.csv`, `composicao_conjunto.csv`, `capacidade_membros.csv` e `tipo_publicado.csv` da Coleta (FR-054, FR-060 e FR-061 da spec da Coleta de dados) e da base horária do Tratamento:
  - **trechos de composição**: os trechos consecutivos da Coleta com a mesma composição, juntos;
  - **composição por trecho**: as usinas de cada trecho, com o nome, o tipo (pelo CEG), o CEG, a entrada e a saída no conjunto e a potência no trecho (unidades da Capacidade de geração em operação em algum momento do trecho); a usina sem unidade cadastrada fica sem potência e é contada. A potência somada das usinas do trecho é identificada no relatório como "calculado neste relatório";
  - **geração do conjunto por trecho de composição**: horas, horas com valor, energia (MWh), média (MWmed) e máxima (MW) de cada trecho, com os tipos do trecho; e por mês e trecho, para a figura;
  - **tipo publicado**: o tipo e o combustível que o ONS publica na série do conjunto, por trecho, comparados com os tipos da composição. A divergência entra na constatação da qualidade dos dados, como fato (no Conj. Chapadão, "TÉRMICA" (Biomassa) também no trecho só com as quatro PCH);
  - **peso da usina na potência do conjunto**, por trecho de composição: a potência das unidades da usina em operação no trecho ÷ a potência somada das usinas do trecho. É fato da Capacidade de geração e nunca estima a geração da usina. Na Bandeirante: 6,7 % de 27/09/2019 a 30/06/2025 e 35,7 % desde 01/07/2025; antes, as unidades dela ainda não estavam em operação;
  - a constatação "Composição do conjunto" e, só no relatório em duas partes (usina em conjunto sem série própria; FR-048 da spec da Geração do relatório), a constatação "A usina no conjunto": o peso por composição e o que o ONS publica da usina isolada.

  Nenhum número do conjunto é dividido entre as usinas nem entra na conclusão (FR-054). A geração do conjunto não é dividida pela potência somada: nenhum fator de capacidade do conjunto é calculado. Na usina em conjunto sem série própria, a disponibilidade e os indicadores oficiais são omitidos, com o motivo, e a qualidade dos dados diz o período das linhas próprias sem valor (na Bandeirante, 4.152 linhas, de 01/05/2026 a 20/10/2026).
- **FR-061**: Na hidrelétrica sem EVT com os Dados hidrológicos, os resultados DEVEM trazer, no campo `hidrologia`:
  - **com a hora confirmada** pela conferência do alinhamento da hidrologia pela geração (FR-026 da spec da Conferência):
    - a tabela anual: horas, afluência média e máxima, vazões turbinada, vertida e vertida não turbinável, nível de montante mínimo, médio e máximo, nível de jusante, volume útil e horas acima do engolimento máximo, com a marca de ano parcial;
    - a mesma tabela por mês, com as médias mensais da afluência e das vazões turbinada e vertida, para a figura;
    - no resumo, as médias do período e as horas com afluência acima do engolimento máximo;
  - **sem a hora confirmada**, ou sem a conferência: só a cobertura e o resultado da conferência, com o motivo, como a FR-034 faz na hidrelétrica com EVT;
  - **sem os cruzamentos com a EVT**: ficam de fora as horas e a EVT por faixa de afluência, o perfil por hora do dia nos dias com parada com EVT e as regras C3 e C11, que continuam só na hidrelétrica com EVT.

  Os valores sinalizados saem só do campo afetado, como na FR-035.

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

  Nas usinas sem EVT, os dados das figuras são as tabelas das seções comuns e das seções do tipo (FR-052, FR-056, FR-058, FR-060 e FR-061), cada uma com o nível; a lista das figuras de cada tipo está na spec da Geração do relatório.
- **FR-042**: A tabela de parâmetros NÃO DEVE ser montada nas Análises. Ela sai do perfil, das regras gerais e das datas de obtenção registradas pela Coleta, e é montada na Geração do relatório; das Análises, ela usa só o período de cada base complementar, que já está nos resumos das FR-033, FR-038 e FR-039.

**Constatações (US3)**

- **FR-043**: Cada constatação DEVE ter um título fixo e um texto montado só a partir dos resultados, do perfil e das regras gerais. As constatações DEVEM descrever fatos dos dados:
  - NÃO DEVEM emitir parecer de desempenho, como "satisfatório", "insatisfatório", "cumpre", "descumpre" e equivalentes;
  - NÃO DEVEM atribuir causa ao vertimento, às reduções de geração ou às paradas; quando a base não informa a causa, o texto diz isso;
  - um número do conjunto DEVE vir escrito "do conjunto <nome>", e nenhum número do conjunto é dividido entre as usinas.
- **FR-044**: As constatações DEVEM ser geradas nesta ordem, cada uma no máximo uma vez, e só nas condições indicadas. Onde cada uma aparece no relatório é definido na spec da Geração do relatório. Na hidrelétrica com EVT:

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

  Na usina sem EVT:

  | # | Título | Aparece quando | O que informa |
  |---|---|---|---|
  | 1 | Cobertura dos dados | sempre | série de referência, com o conjunto do ONS e o identificador (e o nível), período, horas com registro sobre as esperadas, horas ausentes e quantidade de trechos, quando há mais de um |
  | 2 | Cadastro da usina no ONS | a conferência da ficha do cadastro com o perfil aponta divergência | a ficha, a data de obtenção e as divergências |
  | 3 | A usina no conjunto | relatório em duas partes (usina em conjunto sem série própria) | o que o ONS publica do conjunto e não da usina isolada; o peso da usina na potência do conjunto por composição, que não estima a geração dela |
  | 4 | Geração | sempre | por nível: geração média, energia, horas com valor e horas até 1 MW; entre os anos completos, a maior e a menor média |
  | 5 | Disponibilidade | há a Disponibilidade por usina | disponibilidade operacional (MW e % da potência) e sincronizada médias; indisponibilidade total (horas e eventos); horas com geração acima da disponibilidade declarada |
  | 6 | Programação diária do ONS | há programação no mesmo nível da geração | horas comuns, com o nível; geração e programação médias, desvio médio absoluto e correlação; horas paradas com programação acima de 5 MW |
  | 7 a 10 | Despacho por motivo; Atendimento ao despacho; Disponível sem despacho; CVU e CMO | térmicas com o despacho; a 9 só com geração no período; a 10 com o CVU × CMO | geração verificada e motivo principal, ou que a usina não gerou e ficou disponível; horas e energia abaixo e acima da programada e sem programação; horas disponíveis sem despacho e a potência média; semanas com o CVU abaixo e acima do CMO, por unidade, e as horas disponíveis sem despacho nelas |
  | 11 a 13 | Fator de capacidade; Energia cortada; Recurso × geração | eólicas e solares com a base; a 13 só com recurso inválido ou acima do limite físico | fator publicado, período e nível; energia cortada e a % da estimada, a diferença bruta e as semi-horas sem a marca e sem estimativa; semi-horas com o recurso inválido e acima do limite físico |
  | 14 | Composição do conjunto | usina em conjunto com a geração do conjunto | as composições do período, com as usinas, os tipos e a geração média do conjunto de cada uma (até cinco; as demais na planilha), sem divisão entre as usinas |
  | 15 | Afluência e vertimento | hidrelétrica sem EVT com os Dados hidrológicos | cobertura; a hora conferida pela geração, com as correlações, ou que não pôde ser conferida; com ela, afluência, vazões e horas acima do engolimento máximo; ressalva de que os dados não são consistidos pelo ONS |
  | 16 | Qualidade dos dados | sempre | horas sinalizadas por código, ou que não há; horas sem valor; linhas próprias da usina sem valor, com o período; tipo publicado na série do conjunto diferente dos tipos da composição |

**Conclusão (US4)**

- **FR-045**: Os itens da conclusão DEVEM ser gerados pelas regras do catálogo abaixo, aplicadas aos resultados das análises e das conferências; nenhum item é escrito à mão nem fica fixo no texto.
  - O catálogo é uma lista de regras declaradas. Cada regra declara: o código; os tipos em que é avaliada; as listas em que pode gerar itens (cada item traz a sua); o nível exigido, só dado da usina (FR-054); os limiares, em `src/comum/regras.py`; o período mínimo, quando há (FR-053); e as seções de origem.
  - Na hidrelétrica com EVT, C1 a C11 continuam com a mesma ordem, os mesmos textos, limiares e listas, sem período mínimo, e a nota da conclusão continua o texto de antes. Nas usinas sem EVT, são avaliadas as regras do tipo: as comuns C2, C5, C8 e C10 sobre a base horária comum (hidrelétricas sem EVT, térmicas), C12 a C15 nas térmicas (FR-057) e C16 a C19 nas eólicas e solares (FR-059). Nas hidrelétricas e térmicas, com ou sem EVT, também a C20 (FR-063).
  - As listas são quatro: pontos de atenção, possíveis problemas, a confirmar com o agente e a verificar em campo.
  - Os itens são ordenados pela lista, nessa ordem, e, dentro dela, pelo número da regra (na C2, pela unidade).
  - Todos os itens gerados ficam nos resultados; o limite de cinco itens por lista é aplicado na Geração do relatório.
- **FR-046**: Cada item DEVE ter:
  - lista e ordem na lista, a partir de 1;
  - regra (C1 a C20);
  - texto de uma frase, sem ponto final, com o número que sustenta o item;
  - seções de origem, guardadas pelo identificador da seção; o número da seção é resolvido na Geração do relatório, conforme as seções presentes.
- **FR-047**: Os itens NÃO DEVEM afirmar causa nem avaliar o desempenho da usina. O vocabulário é de indício ("indício", "possível", "a confirmar"), e nenhum item tem os termos "satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente" ou "culpa".
- **FR-048**: Quando a regra C2 dispara, os itens DEVEM nomear a unidade geradora como o ONS a identifica (UG e o número) e trazer os números que sustentam o indício.
- **FR-049**: Os itens NÃO DEVEM repetir o texto das constatações: nenhuma frase de constatação com 40 caracteres ou mais aparece num item.
- **FR-050**: Uma regra cuja condição não é atendida, ou cuja base não existe para a usina, NÃO DEVE gerar item. Sem nenhuma regra disparada, a conclusão fica sem itens.
- **FR-051**: O catálogo e os limiares DEVEM ser regras gerais, iguais para todas as usinas do mesmo tipo; as regras comuns são as mesmas em todos os tipos que têm a base no nível da usina. Os limiares das regras novas foram calibrados nas usinas piloto e aprovados pelo usuário.
- **FR-054**: Uma regra cujas entradas são do nível do conjunto ou do agregado NÃO DEVE gerar item: ela entra nas omissões, com o motivo, e nenhum número do conjunto entra na conclusão. Nas usinas sem EVT, também vão para as omissões, com o motivo, as regras do tipo sem nenhuma das bases delas no nível da usina, sem o IP e a TEIF de referência no perfil (C5), sem a garantia física no perfil (C18), abaixo do período mínimo (FR-053) ou que dependem da base de EVT. Na usina em conjunto sem base própria, a conclusão não tem itens e traz a frase que explica a falta de base no nível da usina; sem nenhuma regra do tipo com base, a frase diz isso. Na hidrelétrica com EVT, a frase da conclusão sem itens continua a de antes.
- **FR-055**: Nas usinas sem EVT, a nota da conclusão DEVE ser gerada do catálogo das regras do tipo, com os limiares. Na hidrelétrica com EVT, ela continua o texto de antes.

**Catálogo de regras da conclusão**

Regras, tipos e listas:

| Regra | Tipos | Listas em que pode gerar item |
|---|---|---|
| C1 | UHE, PCH, CGH, só com a base de EVT | pontos de atenção, a confirmar com o agente, a verificar em campo |
| C2 | UHE, PCH, CGH, UTE, UTN | possíveis problemas, a confirmar com o agente, a verificar em campo |
| C3 | UHE, PCH, CGH, só com a base de EVT | pontos de atenção |
| C4 | UHE, PCH, CGH, só com a base de EVT | pontos de atenção |
| C5 | UHE, PCH, CGH, UTE, UTN | pontos de atenção |
| C6 | UHE, PCH, CGH, só com a base de EVT | possíveis problemas, a confirmar com o agente, a verificar em campo |
| C7 | UHE, PCH, CGH, só com a base de EVT | possíveis problemas, a confirmar com o agente |
| C8 | UHE, PCH, CGH, UTE, UTN | possíveis problemas, a confirmar com o agente |
| C9 | UHE, PCH, CGH, só com a base de EVT | pontos de atenção |
| C10 | UHE, PCH, CGH, UTE, UTN | a confirmar com o agente, a verificar em campo |
| C11 | UHE, PCH, CGH, só com a base de EVT | a verificar em campo |
| C12 | UTE, UTN | possíveis problemas, a confirmar com o agente |
| C13 | UTE, UTN | a confirmar com o agente |
| C14 | UTE, UTN | pontos de atenção |
| C15 | UTE, UTN | a confirmar com o agente |
| C16 | EOL, UFV | pontos de atenção |
| C17 | EOL, UFV | a verificar em campo |
| C18 | EOL, UFV | pontos de atenção |
| C19 | EOL, UFV | a confirmar com o agente |
| C20 | UHE, PCH, CGH, UTE, UTN | a confirmar com o agente |

Seções citadas pelos itens:

| Seção citada | Título da seção no relatório |
|---|---|
| eventos | EVT por nível de geração e eventos de usina parada |
| programação | Operação verificada e programação diária do ONS; nas usinas sem EVT, Programação diária × geração verificada |
| indicadores por UG | Indicadores oficiais do ONS por unidade geradora |
| hidrologia | Afluência, vertimento e nível do reservatório (ONS) |
| perfil horário | Perfil horário da geração e da EVT |
| indicadores anuais | Indicadores anuais |
| disponibilidade e geração | Disponibilidade e geração por ano |
| disponibilidade sincronizada | Disponibilidade operacional e sincronizada (ONS) |
| qualidade | Qualidade dos dados |
| geração por motivo | Geração por motivo de despacho e inflexibilidade |
| atendimento ao despacho | Atendimento ao despacho |
| disponível sem despacho | Disponível sem despacho, ou Disponível sem despacho e CVU × CMO |
| fator de capacidade | Fator de capacidade |
| energia cortada | Energia cortada por restrição de operação (constrained-off) |
| recurso × geração | Recurso × geração |

Nas usinas sem EVT, os itens das regras comuns citam as seções de mesmo título do caminho sem EVT.

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

**Regras comuns nas usinas sem EVT**

Nas hidrelétricas sem EVT e nas térmicas, C2, C5, C8 e C10 são avaliadas sobre a base horária comum, só com dados da usina, com os mesmos limiares:
- **C2**: como acima, sobre as horas por estado operativo e as taxas; sem a TEIF de referência no perfil, dispara só pela limitação forçada recorrente (b).
- **C5**: a disponibilidade operacional média da usina no lugar da declarada, o DISPF médio e as taxas mais recentes, contra as referências; sem o IP e a TEIF de referência no perfil, não é avaliada.
- **C8**: ≥ 100 h com a geração da usina acima da disponibilidade declarada (regra R7 da base horária comum); gera sempre os dois itens, porque a C7 não é avaliada.
- **C10**: evento de indisponibilidade total (disponibilidade operacional ≤ 0,001 MW) com ≥ 30 dias, ou unidade com INDISPPF ≥ 20 % num ano completo; o item junta os anos seguidos com as mesmas unidades ("de todas as unidades em 2022, 2023, 2024 e 2025"), em vez de repetir as unidades a cada ano.
- **Bases**: a Disponibilidade por usina (C5, C8 e C10) e os indicadores do ONS (C2, C5 e C10), no nível da usina; sem nenhuma das bases da regra, ela vai para as omissões, com o motivo.

**C12. Geração abaixo da programada** (UTE, UTN)
- **Dispara**: a geração verificada fica mais de 5 MW abaixo da programada em ≥ 24 h, nas horas com programação acima de 1 MW.
- **Bases**: despacho da usina.
- **Possíveis problemas** (atendimento ao despacho): as horas e a energia abaixo da programada.
- **A confirmar com o agente** (atendimento ao despacho): o motivo da geração abaixo da programada, com as horas e a energia.

**C13. Disponível sem despacho com o CVU abaixo do CMO** (UTE, UTN)
- **Dispara**: ≥ 168 h disponíveis sem despacho (disponibilidade operacional acima de 0,001 MW, programação e geração até 1 MW) em horas de semanas operativas com o CVU de alguma unidade abaixo do CMO do subsistema; o CVU sinalizado (ausente, zero ou negativo) não entra na comparação.
- **Bases**: despacho, Disponibilidade por usina, CVU e CMO.
- **A confirmar com o agente** (disponível sem despacho): a condição de despacho da usina nessas semanas, com as semanas e as horas.

**C14. Inflexibilidade não verificada** (UTE, UTN)
- **Dispara**: a inflexibilidade programada não verificada (soma, hora a hora, da programada menos a verificada, quando positiva) é ≥ 5 % da inflexibilidade programada.
- **Bases**: despacho da usina.
- **Pontos de atenção** (geração por motivo): a energia não verificada, a % e a inflexibilidade programada.

**C15. Geração sem programação** (UTE, UTN)
- **Dispara**: a geração verificada fica mais de 5 MW acima da programada, nas horas com programação até 1 MW, em ≥ 24 h.
- **Bases**: despacho da usina.
- **A confirmar com o agente** (atendimento ao despacho): a programação do ONS correspondente a essa geração, com as horas e a energia acima da programada.

**C16. Energia cortada** (EOL, UFV)
- **Dispara**: a energia cortada por restrição de operação no período é ≥ 5 % da energia estimada nas semi-horas com a marca de restrição.
- **Bases**: restrição com detalhe da usina.
- **Pontos de atenção** (energia cortada): a energia cortada e a %.

**C17. Recurso inválido** (EOL, UFV)
- **Dispara**: o recurso (vento ou irradiância) é marcado como inválido pelo ONS em ≥ 10 % das semi-horas da usina.
- **Bases**: restrição com detalhe da usina, com o recurso.
- **A verificar em campo** (recurso × geração): a medição do recurso, com as semi-horas inválidas e a %.

**C18. Fator de capacidade abaixo da garantia física** (EOL, UFV)
- **Dispara**: o fator de capacidade publicado da usina, num ano completo, fica abaixo da razão entre a garantia física e a potência instalada.
- **Bases**: fator de capacidade no nível da usina e a garantia física no perfil; período mínimo de 12 meses distintos (FR-053).
- **Pontos de atenção** (fator de capacidade): os anos e o fator de cada um, com a razão.

**C19. Desvio da programação** (EOL, UFV)
- **Dispara**: o desvio médio absoluto entre a geração programada e a verificada é ≥ 15 % da potência instalada.
- **Bases**: programação diária no nível da usina.
- **A confirmar com o agente** (programação): a diferença entre a geração programada e a verificada, com o desvio médio absoluto em MW e em % da potência e as horas.

**Indicadores da carteira (US11)**

- **FR-062**: Nos dois caminhos, as Análises DEVEM gravar o campo `indicadores_carteira`, que reúne números que elas já calculam para o relatório da usina; o único cálculo novo é a razão do atendimento ao despacho. O campo não muda a versão do formato.
  - **Chaves fixas**:
    - `tipo`;
    - `periodo`: início e fim da série de referência;
    - `ano` e `ano_parcial`: o ano dos indicadores, que é o último ano completo da série; sem ano completo, o ano parcial mais recente, marcado como parcial;
    - `fator_capacidade`, `disponibilidade`, `teifa`, `energia_cortada` e `atendimento_despacho`, cada um com `valor`, `nivel` (o do dado de origem: usina, conjunto ou agregado) e `unidade`. Quando o indicador não se aplica ao tipo ou falta a base, fica vazio, e nunca zero;
    - `conclusao`: a quantidade de todos os itens de cada lista (possíveis problemas, pontos de atenção, a confirmar com o agente, a verificar em campo), contados como na aba CONCLUSAO, e não só os cinco exibidos, e a quantidade de regras avaliadas e de não avaliadas.
  - **Origem**: cada indicador é o número da tabela anual do relatório da usina, no ano escolhido.

    | Indicador | Origem | Aplica-se a |
    |---|---|---|
    | Fator de capacidade (%) | geração média ÷ potência instalada, dos indicadores anuais | hidrelétrica com EVT; EOL e UFV com série da usina (como nos indicadores anuais da FR-052) |
    | Disponibilidade (%) | disponibilidade média ÷ potência instalada, dos indicadores anuais: a declarada na hidrelétrica com EVT (disponibilidade relativa, FR-011); a operacional da usina nas demais (FR-052) | usinas com a disponibilidade no nível da usina |
    | TEIFa (%) | taxa publicada pelo ONS para dezembro do ano (janela de 60 meses), vazia sem dezembro; no ano parcial, a do último mês publicado | usinas com os indicadores oficiais do ONS |
    | Energia cortada (%) | energia cortada ÷ energia estimada nas semi-horas com a marca de restrição, da tabela anual da energia cortada (FR-058) | EOL e UFV com a restrição |
    | Atendimento ao despacho (%) | horas com programação (acima de 1 MW) em que a geração ficou a até 5 MW da programada ÷ horas com programação, da tabela anual do atendimento (FR-056) | UTE e UTN com o despacho; vazio no ano sem hora com programação |

  - **Conclusão sem regra avaliada**: quando nenhuma regra foi avaliada com dado da usina (todas nas omissões, como na usina em conjunto sem série própria), as contagens das listas ficam vazias, e não zero. Aí a falta de itens não quer dizer falta de indício (FR-054).
  - **Hidrelétricas com EVT**: só o campo novo muda; o relatório não muda.
  - **Nas usinas piloto de MS**, com os resultados gravados:
    - UHE São Domingos (2025): fator de capacidade de 49,2 %, disponibilidade de 91,2 % e TEIFa de 4,2 % (12/2025); energia cortada e atendimento vazios; 5 pontos de atenção, 4 possíveis problemas, 5 itens a confirmar com o agente e 5 a verificar em campo; 11 de 11 regras avaliadas.
    - UTE William Arjona (2025): disponibilidade de 20,9 %, TEIFa de 30,5 % (12/2025) e atendimento ao despacho de 6,25 %, exibido como 6,2 % pelo arredondamento do projeto (2 de 32 horas com programação); fator de capacidade e energia cortada vazios; 0 pontos de atenção, 2 possíveis problemas, 4 itens a confirmar com o agente e 1 a verificar em campo; 7 de 8 regras avaliadas.
    - UFV Seriemas 1 (2026 parcial, de 22/08 a 19/10/2026): fator de capacidade de 17,2 % e energia cortada de 16,3 %; disponibilidade, TEIFa e atendimento vazios; 1 ponto de atenção e 1 item a verificar em campo; 2 de 4 regras avaliadas.
    - PCH Bandeirante (em conjunto, sem série própria): indicadores e contagens vazios; nenhuma das 11 regras avaliada.
- **FR-063** (taxas operativas × oficiais): Com as taxas operativas na tabela mensal (FR-045 da spec do Tratamento de dados), as Análises DEVEM gravar a comparação:
  - o mês mais recente das taxas oficiais, as duas oficiais e as duas operativas desse mês e as diferenças (operativa − oficial, em p.p.);
  - os meses com as quatro taxas, os meses com diferença absoluta de pelo menos 1 p.p. em cada taxa e a maior diferença de cada taxa, com o mês;
  - a série mensal (dados da figura e da aba) e se há a figura (algum mês com diferença de pelo menos 1 p.p.).

  Sem mês com as quatro taxas, não há comparação. A regra C20 (lista a confirmar com o agente, seção dos indicadores oficiais) dispara quando a TEIFa ou a TEIP operativa do mês mais recente está a pelo menos 1 p.p. da oficial e cita só as taxas que diferem; sem as taxas operativas, fica entre as não avaliadas, com o motivo.

### Key Entities

- **Resultados das análises**: arquivo único da etapa, com a versão do formato; reúne a cobertura, os indicadores, os eventos, as distribuições, os perfis, as análises das bases complementares com os resultados das conferências correspondentes, as seções comuns e as do tipo nas usinas sem EVT, os níveis, as omissões, os dados das figuras, as constatações, os itens da conclusão e os indicadores da carteira.
- **Caminho**: hidrelétrica com EVT ou usina sem EVT, pela série de referência da usina (FR-052).
- **Base horária comum**: a base das usinas sem EVT, gravada pelo Tratamento: geração da série de referência com o nível, disponibilidade, programação, trecho e sinalizações de cada hora.
- **Nível do dado**: usina, conjunto de usinas ou agregado, com o identificador; cada número leva o seu.
- **Trecho de composição**: intervalo do período sem mudança das usinas do conjunto, com os tipos e a potência delas.
- **Omissão**: seção ou regra não avaliada para a usina, com o motivo.
- **Indicador anual e do período**: valores da FR-011 e da FR-012, por ano civil ou no período completo; nas usinas sem EVT, os indicadores anuais por ano e nível da FR-052.
- **Evento**: sequência de horas consecutivas numa condição (usina parada com EVT, indisponibilidade total ou desvio da programação), com início, fim, duração e médias.
- **Classe horária**: classe de uma hora segundo a programação, a sincronização das unidades ou a faixa de afluência.
- **Constatação**: título fixo, texto gerado e condição de existência.
- **Regra da conclusão**: identificador (C1 a C20), tipos em que é avaliada, condição e limiares, listas em que gera item e o que cada item diz, nível exigido, período mínimo, seções citadas e bases necessárias.
- **Item da conclusão**: lista, ordem, regra, texto de uma frase e seções de origem.
- **Indicadores da carteira**: chaves fixas, com o ano, os indicadores comparáveis (valor, nível e unidade) e as contagens da conclusão.
- **Dados de figura**: séries e tabelas que a Geração do relatório desenha, sem recalcular.

---

## Aplicabilidade por tipo

"Hidrelétrica com EVT" é a UHE, PCH ou CGH com a série da energia vertida turbinável; "hidrelétrica sem EVT", a que não a tem. O nível de cada base (da usina, do conjunto ou ausente) vem da `[cobertura]` do perfil.

**Análises e seções**

| Análise | Hidrelétrica com EVT | Hidrelétrica sem EVT | UTE, UTN | EOL, UFV |
|---|---|---|---|---|
| Caminho (FR-052) | base de EVT (FR-010 a FR-040) | base horária comum | base horária comum | base horária comum |
| EVT, eventos de parada, perfis da EVT, faixas de afluência, mudança de classificação | sim | não se aplica | não se aplica | não se aplica |
| Seções comuns: indicadores anuais, série temporal, geração mensal, perfil horário, programação × verificada, qualidade dos dados (FR-052) | não se aplica (o caminho da EVT já as tem) | sim, conforme a cobertura | sim, conforme a cobertura | sim, conforme a cobertura |
| Sazonalidade (FR-053) | distribuição da EVT pelos meses do ano completos (FR-015) | com 12 meses distintos | com 12 meses distintos | com 12 meses distintos |
| Fator de capacidade nos indicadores anuais | sim (FR-011) | não se aplica | não se aplica | só no nível da usina |
| Disponibilidade e geração por ano; disponibilidade operacional e sincronizada | com a disponibilidade (FR-030 a FR-033) | com a Disponibilidade por usina | com a Disponibilidade por usina | não se aplica (o ONS não a publica) |
| Indicadores oficiais por unidade geradora (FR-023 a FR-025) | com os indicadores | com os indicadores | com os indicadores | não se aplica (o ONS não os publica) |
| Seções de térmica (FR-056) | não se aplica | não se aplica | com o despacho; CVU × CMO com o CVU e o CMO | não se aplica |
| Seções de eólica e solar (FR-058) | não se aplica | não se aplica | não se aplica | com as bases; números do conjunto identificados |
| Composição e geração do conjunto (FR-060) | não se aplica | PCH e CGH em conjunto, com a geração do conjunto | não se aplica | em conjunto, com a geração do conjunto, também com série própria |
| Afluência, vertimento e nível | com os cruzamentos com a EVT (FR-034 a FR-038) | com a hora conferida pela geração, sem os cruzamentos com a EVT (FR-061) | não se aplica | não se aplica |
| Conclusão | C1 a C11, como antes | C2, C5, C8 e C10 sobre a base horária comum, só com dado da usina; C1, C3, C4, C6, C7, C9 e C11 não avaliadas; PCH e CGH em conjunto sem base própria: sem itens, com a frase | C2, C5, C8 e C10 sobre a base horária comum e C12 a C15, só com dado da usina | C16 a C19, só com dado da usina; as regras comuns não se aplicam |
| Nota da conclusão (FR-055) | o texto de antes | gerada do catálogo do tipo | gerada do catálogo do tipo | gerada do catálogo do tipo |
| Indicadores da carteira (FR-062) | sim | sim | sim | sim |

**Indicadores da carteira (FR-062)**

| Indicador | Hidrelétrica com EVT | Hidrelétrica sem EVT | UTE, UTN | EOL, UFV | Usina em conjunto sem série própria |
|---|---|---|---|---|---|
| Fator de capacidade | sim | vazio | vazio | sim | vazio |
| Disponibilidade | sim | com a disponibilidade da usina | com a disponibilidade da usina | vazio (o ONS não a publica) | vazio |
| TEIFa | com os indicadores oficiais | com os indicadores oficiais | com os indicadores oficiais | vazio | vazio |
| Energia cortada | vazio | vazio | vazio | com a restrição | vazio |
| Atendimento ao despacho | vazio | vazio | com o despacho | vazio | vazio |
| Contagens da conclusão | sim | sim | sim | sim | vazias |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o perfil e a Coleta congelados da São Domingos, os resultados das Análises são os de hoje:
  - o relatório gerado a partir deles é idêntico ao de referência (`relatorios_referencia/sao_domingos/`, conferido por `python -m src comparar --todas`), gerado com a data de 07/10/2026 08:53, com a conclusão aprovada em 07/10/2026, e aprovado em 19/10/2026: PDF com 30 páginas e o mesmo texto, Markdown idêntico, planilha com as 58 abas idênticas célula a célula e as 8 figuras idênticas byte a byte;
  - são 17 constatações e 19 itens da conclusão (5, 4, 5 e 5 por lista), com as onze regras disparadas e a UG2 nomeada em "Possíveis problemas".
- **SC-002**: Os totais conferem com a base: a soma das horas dos anos é o número de registros; a EVT do período é a soma da EVT horária; a EVT por nível de geração soma a EVT total, e as participações somam 100 %; as horas com geração zero somam a contagem na base.
- **SC-003**: 100 % das 10 grandezas têm perfil estatístico em todos os anos da série, com mínimo e máximo e as respectivas data e hora, e nenhum registro sinalizado entra no perfil nem nos extremos.
- **SC-004**: Na série sintética, sem as bases complementares, as Análises produzem exatamente 12 constatações, que reproduzem os fatos conhecidos (30 h de indisponibilidade total, 5 h de usina parada com EVT, mudança em jan/2024 e o registro de 60 MW fora dos extremos), sem parecer e sem nenhuma das afirmações removidas na auditoria.
- **SC-005**: Recebem classe 100 % das horas comuns com programação, 100 % das horas paradas com dado de disponibilidade e 100 % das horas com EVT do período da hidrologia; em cada caso, a soma das classes é igual ao total, e as horas paradas com EVT se dividem exatamente entre as duas classes de programação.
- **SC-006**: Nos testes, cada regra C1 a C20 dispara e deixa de disparar conforme a condição; 100 % dos itens têm regra e ao menos uma seção de origem; nenhum item tem termo de avaliação de desempenho nem repete frase de constatação; os itens estão ordenados por lista e por regra; nas usinas sem EVT, as regras sem base no nível da usina ficam nas omissões, com o motivo.
- **SC-007**: Em 100 % das tentativas de executar as Análises sem a Conferência concluída e atualizada, a etapa sai com código 5 e não grava nada.
- **SC-008**: Com o perfil da usina fictícia dos testes, as faixas de afluência dizem "entre uma e três unidades", as faixas de geração são as do perfil, nenhum texto gerado menciona a São Domingos nem os valores dela, e as análises das bases ausentes são omitidas.
- **SC-009**: 100 % dos números citados nas constatações e nos itens da conclusão vêm dos resultados gravados e são iguais aos das tabelas do relatório e das abas da planilha.
- **SC-010**: Com os dados locais da São Domingos, a cobertura, os indicadores, os eventos, as distribuições, os perfis, o perfil estatístico e os extremos da base de EVT são calculados em menos de 30 s, e o cruzamento com a programação diária, em menos de 2 min.
- **SC-011**: Com a usina fictícia de cada um dos sete tipos, testada de ponta a ponta sem rede, as Análises seguem o caminho do tipo, com as seções comuns e as do tipo, as omissões com o motivo, os indicadores da carteira com as chaves fixas e nenhum texto com o nome, o identificador ou os valores de outra usina.
- **SC-012**: Nas usinas piloto aprovadas (UTE William Arjona, UFV Seriemas 1, EOL Praia Formosa e PCH Bandeirante), todo número do conjunto aparece identificado como do conjunto, nenhum número do conjunto é dividido entre as usinas nem entra na conclusão, nenhum texto gerado tem termo de parecer, e os resultados refeitos a partir da Coleta e do perfil congelados reproduzem os relatórios de referência (`python -m src comparar --todas`).

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
| 09/10/2026 | Ampliação do fluxo para todos os tipos de usina cobertos pelos dados abertos do ONS (UHE, PCH, CGH, UTE, UTN, EOL e UFV), com o relatório da São Domingos sem mudança. Os indícios da conclusão usam só dados da usina. | FR-005, FR-045, FR-052, FR-054, SC-001 |
| 19/10/2026 | Ajustes aprovados na conferência do código das usinas sem EVT ("aprovado, siga"): resultados no formato 3; regras comuns C2, C5, C8 e C10 sobre a base horária comum; afluência e nível das hidrelétricas sem EVT. | FR-004, FR-005, FR-045, FR-052, FR-061 |
| 19/10/2026 | O agente atual das unidades ativas, da Capacidade de geração, sem o histórico, entra na capa e no resumo das usinas sem EVT. | FR-052 |
| 20/10/2026 | Limiares de C12 a C15 mantidos como propostos: desvio do despacho de 5 MW; C12 com ≥ 24 h; C13 com ≥ 168 h; C14 com ≥ 5 % da inflexibilidade programada; C15 com ≥ 24 h. | FR-006, FR-057, catálogo C12 a C15 |
| 20/10/2026 | O CVU zero fica fora da comparação com o CMO, como o ausente e o negativo ("Zero fica fora"); a tabela CVU × CMO ganha as semanas com o CVU igual ao CMO, para fechar o total de semanas. | FR-056, C13 |
| 21/10/2026 | Estimativa ausente: a geração estimada 0 com a verificada acima de 1 MW fica fora dos totais e das médias da estimada e é contada; na semi-hora restrita sem estimativa, o corte não é calculado. | FR-058 |
| 21/10/2026 | Limite físico do recurso: vento acima de 40 m/s e irradiância acima de 1.500 W/m² ficam fora das faixas e são contados (a EOL Praia Formosa tem 111 semi-horas com vento de até 246 m/s, sem a marca do ONS). | FR-006, FR-058 |
| 21/10/2026 | Limiares de C16 a C19: C16 em 5 % da energia estimada, C17 em 10 % das semi-horas e C18 como proposta; C19 em 15 % da potência instalada, porque os 10 % iniciais apontavam desvios usuais da previsão de vento (10,4 % na EOL Praia Formosa). | FR-059, catálogo C16 a C19 |
| 21/10/2026 | Na eólica ou solar com a série própria e a programação do conjunto, a programação é comparada com a geração do conjunto, identificada como do conjunto, fora da base da usina e sem a C19. | FR-058 |
| 22/10/2026 | A seção do conjunto vale para toda usina em conjunto, inclusive a eólica ou solar com série própria; a potência das usinas da composição entra, sem dividir número do conjunto e sem fator de capacidade do conjunto. Na hidrelétrica sem EVT, a hora dos dados hidrológicos é conferida pela geração da usina, sem meta. | FR-060, FR-061 |
| 22/10/2026 | O peso da usina na potência do conjunto, por composição, entra na usina em conjunto, só com a potência, sem estimar a geração dela; na usina em conjunto sem série própria, o relatório sai em duas partes. | FR-060 |
| 22/10/2026 | Indicadores da carteira do último ano completo da série; atendimento ao despacho pelas horas a até 5 MW da programada; contagens vazias, e não zero, quando nenhuma regra é avaliada com dado da usina; fator de capacidade só onde o relatório da usina o calcula. | FR-062 |
| 23/10/2026 | Taxas operativas comparadas às oficiais, com o limiar de 1 p.p. para a figura e para a regra C20, na lista a confirmar com o agente; a carteira não ganha coluna (decisões recomendadas, aprovadas pelo usuário). | FR-063, C20 |

---

## Assumptions

- **Causa**: os conjuntos do ONS não informam a causa do vertimento, das reduções de geração nem dos desligamentos; as Análises quantificam as condições, e a atribuição de causa depende de documentos do agente e do ONS.
- **Limiares**: as regras gerais (FR-006) e os limiares da conclusão são parâmetros de trabalho, não normativos; os principais aparecem na tabela de parâmetros do relatório, e os da conclusão, nas notas metodológicas do relatório.
- **Conclusão**: organiza indícios e verificações a partir dos dados abertos do ONS e não substitui a avaliação do fiscal.
- **Conferência**: as tolerâncias, a meta e a situação "não aplicável" de cada conferência estão na spec da Conferência; as Análises usam os resultados como estão.
- **Vazões abaixo da meta**: pela spec da Conferência, essa etapa sai com código 3 quando a conferência das vazões fica abaixo da meta. A FR-034 vale sempre que as Análises recebem esse resultado.
- **Registros da Coleta**: a cobertura usa a auditoria da extração da EVT e o resumo do manifesto de versões, de `datas_obtencao.csv`, gravados pela Coleta, que é etapa anterior; sem eles, a cobertura sai só da base.
- **Níveis dos dados**: o ONS publica as eólicas e solares quase sempre em conjunto, com a série da própria usina nos conjuntos de restrição, e as PCH e CGH em conjunto com a geração da usina vazia; as Análises usam o nível publicado e nunca o dividem.
- **Limiares das regras novas**: como os de C1 a C11, são parâmetros de trabalho, calibrados nas usinas piloto e aprovados pelo usuário; não são normativos.
- **Usinas nucleares**: são tratadas como térmicas (UTN), com as mesmas seções e regras.
- **Distribuição ao longo do ano**: a comparação de maio a outubro com janeiro a abril é a mesma para qualquer usina.
- **Horários**: os do ONS, já na hora de início e alinhados entre as bases pelo Tratamento.
- **Resultados**: o arquivo de resultados é interno ao fluxo; a versão legível dos resultados é a planilha do relatório.
