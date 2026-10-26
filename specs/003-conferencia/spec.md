# Spec da Etapa 3: Conferência

**Etapa**: 3 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-23

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

Comparar entre si as bases do ONS que trazem a mesma grandeza e refazer os indicadores oficiais que podem ser recalculados a partir dos dados publicados. As conferências formam um catálogo, em que cada uma declara os tipos de usina, as bases e o nível dos dados que exige (FR-019):
- na hidrelétrica com EVT (UHE, PCH ou CGH com série própria na Energia Vertida Turbinável), são as seis conferências da FR-002;
- nas demais usinas, são as do catálogo que os dados da usina permitem: os indicadores oficiais e o cadastro, as conferências das térmicas (G3 e G4), as das eólicas e solares (G1, G2 e G5) e o alinhamento da hidrologia pela geração, nas hidrelétricas sem EVT.

O resultado de cada conferência fica registrado do mesmo modo (bases, período, quantidade comparada, coincidências, divergências e tolerância), para que as Análises e as legendas do relatório citem resultados refeitos a cada execução. A conferência que não se aplica à usina fica registrada, com o motivo, em `nao_aplicaveis.csv`. A etapa não corrige dados nem escolhe entre as fontes, e interrompe o fluxo quando as vazões não confirmam o alinhamento dos horários.

## Entradas e saídas

**Comando**: `python -m src conferencia --usina <slug>`

- Sem opções próprias; vale a opção comum `--log-level`.
- Pré-requisito: Tratamento de dados concluído para a usina.
- As regras comuns do fluxo (sintaxe dos comandos, perfil da usina e código 4, inclusive o perfil em rascunho, `etapa.json`, pré-requisitos e código 5, comando `completo`) estão na spec da Coleta de dados.

**Lê** (só arquivos locais, nunca o portal do ONS):

| Pasta | Arquivo | Conferência |
|---|---|---|
| `data/usinas/<slug>/tratamento/` | `evt_tratado.parquet`, só na hidrelétrica com EVT: geração, disponibilidade declarada e vazões turbinada e vertida da base de EVT | geração, disponibilidade, vazões |
| | `geracao_horaria.csv` | geração; G1 e G2, quando a série de referência é a restrição com detalhe |
| | `disponibilidade_horaria.csv` | disponibilidade |
| | `hidrologia_horaria.csv` | vazões; alinhamento da hidrologia pela geração |
| | `indicadores_ug_mensal.csv` e `horas_estado_mensal.csv` | DISPF × horas |
| | `horas_estado_mensal.csv` e `teifa_teip_mensal.csv` | TEIFa e TEIP |
| | `base_horaria.csv`, só nas usinas sem EVT: a geração da série de referência, hora a hora, com o nível (usina ou conjunto) | G4; alinhamento da hidrologia pela geração; G1 e G2, quando a série de referência é a Geração por usina |
| | `programacao_horaria.csv` | G3, G5 |
| | `despacho_horario.csv` | G3, G4 |
| | `fator_capacidade_horario.csv` | G1, G5 |
| | `restricao_horaria.csv` | G1, G2 |
| | `restricao_razao_semi_horaria.csv` | G1 |
| | `restricao_membros_horaria.csv`: a restrição com detalhe das outras usinas do conjunto, em hora cheia | G2 |
| | `indicadores_ug_anual.csv`, `geracao_ausencias.csv`, `auditoria_geracao.csv`, `disponibilidade_ausencias.csv`, `auditoria_disponibilidade.csv`, `hidrologia_ausencias.csv`, `auditoria_hidrologia.csv`, `programacao_dias_ausentes.csv`, `despacho_unidades_horario.csv`, `despacho_ausencias.csv`, `restricao_semi_horaria.csv` e `restricao_ausencias.csv`: lidos com os indicadores e as séries, sem uso nas conferências | nenhuma |
| `data/usinas/<slug>/coleta/` | `cadastro_ficha.csv`, com a quantidade de linhas com o CEG; o cadastro não passa por tratamento | cadastro |
| `usinas/<slug>/perfil.toml` | `parametros.potencia_instalada_mw`, `usina.estado` e `identificacao.id_ons` | cadastro |
| | `usina.tipo`, `[cobertura]`, `identificacao.id_conjunto` e `[[identificacao.membros]]` | catálogo (FR-019); G2 |

**Grava** em `data/usinas/<slug>/conferencia/`:

| Arquivo | Conteúdo |
|---|---|
| `conferencias.pkl` | os resultados (FR-003), com a versão do formato: na hidrelétrica com EVT, os seis da FR-002; nas demais usinas, só os das conferências aplicadas (FR-018). É o que as Análises leem e repassam à Geração do relatório |
| `geracao.csv` | geração mês a mês: energia de cada fonte, diferença e horas só em cada fonte |
| `geracao_divergencias.csv` | horas divergentes da geração, em períodos contínuos |
| `disponibilidade.csv` | resumo da conferência da disponibilidade, numa linha |
| `disponibilidade_divergencias.csv` | horas divergentes da disponibilidade, em períodos contínuos |
| `vazoes.csv` | resumo do alinhamento das vazões, numa linha, com a meta e se foi atingida |
| `dispf_horas.csv` | meses-unidade divergentes, com as horas das duas fontes e as diferenças |
| `teifa_teip.csv` | taxas publicadas e recalculadas, mês a mês, com as diferenças |
| `cadastro.csv` | campos conferidos da ficha, com o valor do cadastro, o do perfil e a situação |
| `programacao_despacho.csv` | G3 mês a mês: energia de cada fonte nas horas comuns, diferença, horas comuns, divergentes e só em cada fonte |
| `verificada_despacho.csv` | G4 mês a mês, com as mesmas colunas |
| `geracao_fontes.csv` | G1 mês a mês, por par de fontes e nível, com as mesmas colunas |
| `soma_conjunto.csv` | G2 mês a mês, com as mesmas colunas |
| `programacao_renovaveis.csv` | G5 mês a mês, com as mesmas colunas |
| `alinhamento_hidrologia.csv` | alinhamento da hidrologia pela geração: horas comuns e correlação com cada deslocamento (−1, 0 e +1 h) |
| `nao_aplicaveis.csv` | as conferências do catálogo que não se aplicam à usina, com o motivo (FR-018) |
| `etapa.json` | manifesto da etapa, com o `resumo` |

- Sem divergência, os arquivos de divergências (`geracao_divergencias.csv`, `disponibilidade_divergencias.csv` e `dispf_horas.csv`) são gravados sem linhas. Numa conferência não aplicável, os CSV dela não são gravados; a exceção é a TEIFa e a TEIP da hidrelétrica com EVT sem mês de janela completa (FR-016).
- Os arquivos desta etapa não têm cópia `.bak`: são refeitos a partir dos dados tratados.
- **`resumo` do `etapa.json`**: para cada conferência registrada em `conferencias.pkl`, se é aplicável (ou o motivo), as quantidades comparada, coincidente e divergente, com a unidade, e, nas vazões, o percentual de coincidência e se a meta foi atingida; e a lista das conferências de `nao_aplicaveis.csv`.
- **Formato**: a etapa grava no formato 2, que inclui `nao_aplicaveis.csv`. As Análises recusam o formato anterior, com o código 5.

**Códigos de saída**:

| Código | Quando |
|---|---|
| 0 | as conferências da usina registradas; a meta das vazões atingida ou não aplicável |
| 1 | erro, inclusive falha de gravação e interrupção pelo usuário |
| 3 | só na hidrelétrica com EVT: meta das vazões não atingida (FR-013), com coincidência abaixo de 99 % das horas comuns, ou nenhuma hora comum; os seis resultados são gravados |
| 5 | Tratamento de dados sem resultados concluídos, com resultados desatualizados ou em formato antigo; nada é gravado |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conferir as bases numa etapa própria, com os resultados registrados (Priority: P1)

Como fiscal da AGEMS, quero que todas as conferências entre fontes fiquem numa etapa só, executada por um comando, e que o resultado de cada uma fique registrado do mesmo modo: bases, período, quantidade comparada, coincidências, divergências e tolerância. Assim as análises e as legendas do relatório citam resultados refeitos a cada execução, e eu sei onde encontrar cada divergência.

**Why this priority**: É o objetivo da etapa. Sem o registro único, as conferências voltam a ficar espalhadas entre a extração das bases e as análises.

**Independent Test**: Executar o comando sobre dados tratados de teste, sem rede, e conferir os resultados, os arquivos da pasta `conferencia/` e o `resumo` do `etapa.json`. Com o perfil da São Domingos e os dados locais, comparar com os resultados atuais (SC-001).

**Acceptance Scenarios**:

1. **Given** o Tratamento de dados concluído de uma hidrelétrica com EVT, **When** a etapa é executada, **Then** os seis resultados são gravados, cada um com bases, período, unidade, quantidades comparada, coincidente e divergente e tolerância, e o `resumo` do `etapa.json` traz a situação de cada conferência.
2. **Given** os dados atuais (perfil da São Domingos), **When** a etapa é executada, **Then**:
   - geração e disponibilidade: 70.895 de 70.895 horas coincidentes;
   - vazões: 70.731 de 70.731 horas coincidentes, com a meta atingida;
   - DISPF × horas: 4 meses-unidade divergentes;
   - TEIFa e TEIP: 21 de 21 meses reproduzidos;
   - cadastro: sem divergência;
   - a etapa termina com código 0.
3. **Given** uma hidrelétrica com EVT sem dados hidrológicos, **When** a etapa é executada, **Then** a conferência das vazões fica registrada como não aplicável, com o motivo, as outras cinco são feitas e a etapa termina com código 0.
4. **Given** o Tratamento de dados sem resultados concluídos, **When** a etapa é executada, **Then** ela para sem gravar nada, com código 5.
5. **Given** conferências feitas à mão fora do fluxo, **When** a etapa é executada, **Then** elas não entram nos resultados.

---

### User Story 2 - Conferir a base de EVT com as séries oficiais do ONS, hora a hora (Priority: P1)

Como fiscal, quero saber se a geração, a disponibilidade declarada e as vazões turbinada e vertida da base de EVT coincidem, hora a hora, com as séries oficiais do ONS. Quero também que o fluxo pare quando as vazões não coincidem, porque isso indica horários desalinhados e invalida os cruzamentos com a afluência.

**Why this priority**: A base de EVT sustenta quase todo o relatório. A coincidência com uma segunda fonte oficial dá confiança aos números, e o alinhamento das vazões protege os cruzamentos hidrológicos.

**Independent Test**: Com dados sintéticos (horas coincidentes, divergentes, só numa das fontes, sinalizadas e vazões desalinhadas), conferir a classificação de cada hora, as listas de divergências e o código de saída.

**Acceptance Scenarios**:

1. **Given** uma hora com 30,00 MW numa fonte e 30,02 MW na outra e outra hora com 30,000 MW e 30,005 MW, **When** a geração é conferida, **Then** a primeira é divergente e a segunda coincidente, e a divergência aparece num período contínuo, com a diferença média e a máxima.
2. **Given** horas presentes só numa das fontes, **When** conferidas, **Then** ficam fora da comparação e são contadas à parte, por fonte.
3. **Given** a geração das duas fontes, **When** conferida, **Then** a tabela mensal traz a energia de cada fonte, a diferença e as horas só em cada fonte.
4. **Given** horas de disponibilidade sinalizadas pelo Tratamento, **When** conferidas, **Then** ficam fora, e a quantidade excluída é registrada.
5. **Given** vazões turbinada e vertida coincidentes, com diferença de até 0,5 m³/s, em pelo menos 99 % das horas comuns, **When** conferidas, **Then** a meta é registrada como atingida e a etapa termina com código 0.
6. **Given** vazões coincidentes em menos de 99 % das horas comuns, **When** a etapa é executada, **Then** os seis resultados são gravados, a meta é registrada como não atingida, a etapa termina com código 3 e o comando `completo` para nela.

---

### User Story 3 - Refazer os indicadores oficiais de disponibilidade (Priority: P1)

Como fiscal, quero recalcular a TEIFa e a TEIP a partir das horas por estado operativo que o ONS publica e comparar com as taxas publicadas. Quero também conferir a indisponibilidade de cada unidade geradora (UG) com essas horas. Assim uso os índices oficiais sabendo que o cálculo se reproduz, e sei em que meses e unidades as duas apurações do ONS não batem.

**Why this priority**: TEIFa e TEIP são as taxas comparadas às referências da garantia física, e as divergências entre o DISPF e as horas são perguntas diretas ao agente.

**Independent Test**: Com horas sintéticas de mais de 60 meses e taxas calculadas à mão, conferir o recálculo, o critério de reprodução e a lista de meses-unidade divergentes.

**Acceptance Scenarios**:

1. **Given** um mês com a janela de 60 meses completa, **When** as taxas são recalculadas, **Then** o mês é comparado e conta como reproduzido se as duas diferenças são de até 0,001 p.p.
2. **Given** um mês sem a janela completa, **When** as taxas são recalculadas, **Then** as taxas recalculadas ficam vazias e o mês não entra na comparação.
3. **Given** nenhum mês com a janela completa, **When** a etapa é executada, **Then** a conferência da TEIFa e da TEIP fica não aplicável, com esse motivo.
4. **Given** um mês-unidade em que a indisponibilidade forçada, convertida em horas, difere das horas de desligamento forçado em mais de 1 h, **When** conferido, **Then** é listado como divergente, com as horas das duas fontes e as diferenças.
5. **Given** uma térmica com as horas por estado operativo e ausente das taxas TEIFa e TEIP publicadas, **When** a etapa é executada, **Then** a TEIFa e a TEIP ficam não aplicáveis, com esse motivo, e a DISPF × horas é feita.

---

### User Story 4 - Conferir a ficha do cadastro com o perfil da usina (Priority: P2)

Como fiscal, quero conferir a ficha da usina no cadastro do ONS com o perfil (potência, estado, id ONS e CEG único), para ter certeza de que o ONS identifica a usina como o perfil a descreve.

**Why this priority**: Confirma a identificação da usina. A divergência é rara, mas indica identificador errado no perfil ou mudança no cadastro.

**Independent Test**: Com fichas sintéticas (igual ao perfil, potência diferente, estado diferente e CEG em duas linhas), conferir as divergências registradas.

**Acceptance Scenarios**:

1. **Given** a ficha com potência autorizada igual à potência instalada do perfil, o estado e o id ONS do perfil e uma única linha com o CEG, **When** conferida, **Then** nenhuma divergência é registrada.
2. **Given** a potência autorizada 0,5 MW diferente da potência instalada do perfil, ou ausente, **When** conferida, **Then** a divergência é registrada com o valor do cadastro e o do perfil.
3. **Given** duas linhas do cadastro com o CEG do perfil, **When** conferida, **Then** vale a primeira, e a repetição é registrada como divergência.
4. **Given** uma usina sem ficha no cadastro, **When** a etapa é executada, **Then** a conferência do cadastro fica não aplicável, com o motivo.
5. **Given** um perfil sem id ONS (usina em conjunto sem id próprio) e a ficha também sem id ONS, **When** conferida, **Then** o id ONS não diverge, e os textos dizem "não informado".

---

### User Story 5 - Conferir as bases de qualquer tipo de usina, com as não aplicáveis registradas (Priority: P2)

Como fiscal, quero que a etapa faça, em qualquer tipo de usina (UHE, PCH, CGH, UTE, UTN, EOL e UFV), as conferências que os dados do ONS permitem, sempre comparando números do mesmo nível, e que registre com o motivo as que não se aplicam. Assim sei o que foi conferido em cada usina e por que o resto não foi, sem mudar o relatório das hidrelétricas com EVT.

**Why this priority**: As usinas dos outros tipos têm bases próprias (despacho térmico, fator de capacidade, restrição por constrained-off) que trazem a mesma grandeza que a Geração por usina e a Programação diária. Sem a conferência, os relatórios desses tipos citariam números sem segunda fonte.

**Independent Test**: Com uma usina fictícia de cada tipo, sem rede, conferir as conferências aplicadas, os motivos de `nao_aplicaveis.csv` e o código de saída; com o perfil da São Domingos, conferir que os seis resultados não mudam.

**Acceptance Scenarios**:

1. **Given** uma hidrelétrica com EVT, **When** a etapa é executada, **Then** `conferencias.pkl` traz os seis resultados de sempre e `nao_aplicaveis.csv` lista G1 a G5 e o alinhamento da hidrologia pela geração, com o motivo; o relatório e a planilha não leem o arquivo.
2. **Given** uma térmica com o despacho, a Programação diária e a Geração por usina no nível da usina, **When** a etapa é executada, **Then** a G3 e a G4 são registradas, com a tolerância de 0,01 MW e sem meta; sem o despacho, as duas ficam em `nao_aplicaveis.csv`, com o motivo.
3. **Given** a geração verificada do despacho que coincide mais com a Geração por usina deslocada de uma hora, **When** a G4 é feita, **Then** o log avisa que a convenção de hora deve ser corrigida, e nada é ajustado.
4. **Given** uma eólica ou solar com a Geração por usina e o Fator de capacidade no nível do conjunto e a restrição com detalhe no da usina, **When** a etapa é executada, **Then** a G1 só compara os pares do mesmo nível; sem duas fontes no mesmo nível, fica não aplicável.
5. **Given** uma eólica ou solar em conjunto, com os membros no perfil, **When** a G2 é feita, **Then** só as horas com todas as usinas da composição vigente com valor entram na soma, e as demais são contadas; sem os membros no perfil, a G2 fica não aplicável, com o motivo.
6. **Given** uma hidrelétrica sem EVT, com os Dados hidrológicos e a Geração por usina da própria usina, **When** a etapa é executada, **Then** o alinhamento da hidrologia é confirmado quando a correlação da vazão turbinada com a geração é maior sem deslocamento do que com −1 h e +1 h; sem a confirmação, ele é registrado, e a etapa termina com código 0.
7. **Given** uma PCH em conjunto, sem série própria com valor, **When** a etapa é executada, **Then** nenhuma conferência nova é feita, e as conferências da hidrelétrica e o alinhamento da hidrologia ficam em `nao_aplicaveis.csv`, com o motivo.

---

### Edge Cases

- **Base ausente para a usina**: a conferência fica não aplicável, com o motivo, e as demais são feitas. Sem dados hidrológicos, não há meta a cumprir nem código 3.
- **Dados hidrológicos sem nenhuma hora em comum com a base de EVT**: a meta conta como não atingida, e a etapa termina com código 3.
- **Registros sinalizados na base de EVT** (regras de plausibilidade do Tratamento): entram nas comparações, porque a conferência compara fontes e não julga a plausibilidade.
- **Valores sinalizados nos outros conjuntos**: na geração e na disponibilidade, a hora sinalizada sai inteira (na geração, conta como hora só na base de EVT; na disponibilidade, só entra na quantidade de horas sinalizadas); nas vazões, sai só o valor sinalizado, e a hora fica de fora se faltar a turbinada ou a vertida em alguma das fontes.
- **Horas só numa das fontes**: não são comparadas; são contadas à parte e citadas.
- **Mês de taxa sem a janela de 60 meses completa**: não é comparado, e as taxas recalculadas ficam vazias.
- **Divergências**: ficam registradas e, fora a meta das vazões, não mudam o código de saída; nenhum valor é corrigido.
- **Ficha do cadastro com potência não numérica ou com o CEG repetido**: registrada como divergência.
- **Potência autorizada do cadastro que não é a da usina** (por exemplo, a de um complexo de usinas solares, 2,5 MW no cadastro contra os 50 MW da usina no perfil): registrada como divergência; o perfil continua com a potência da usina, com a fonte.
- **Conferências feitas à mão fora do fluxo**: não entram nos resultados nem no relatório; ficam registradas em "Conferências manuais (fora do fluxo)".
- **Usina sem EVT**: só as conferências aplicadas entram nos resultados; as demais ficam só em `nao_aplicaveis.csv`, com o motivo.
- **Bases em níveis diferentes** (a usina numa base e o conjunto na outra): não são comparadas. A G1 sem duas fontes no mesmo nível e a G5 com a programação e o fator de capacidade em níveis diferentes ficam não aplicáveis.
- **Conferência G1 a G5 sem nenhuma hora comum entre as fontes**: fica não aplicável, com o motivo.
- **Usina que entra ou sai do conjunto no período** (G2): a usina só é exigida na soma entre a entrada e a saída declaradas no perfil; a hora em que falta o valor de alguma usina vigente fica fora da soma e é contada.
- **Convenção de hora do despacho errada** (G4 com coincidência maior com uma hora de deslocamento): aviso no log; a correção é feita no Tratamento, nunca por ajuste automático.
- **Térmica ausente das taxas TEIFa e TEIP publicadas**: a TEIFa e a TEIP ficam não aplicáveis, com o motivo; a DISPF × horas continua.
- **TEIFa e TEIP refeitas de térmica que não se reproduzem**: a divergência fica registrada, sem ajuste, até haver fonte publicada de uma regra própria das térmicas (FR-022).
- **PCH e CGH em conjunto**: nenhuma conferência nova. A usina não tem série própria com valor, e a soma das usinas do conjunto não existe, porque o ONS publica vazias as linhas próprias das PCH. As conferências da hidrelétrica ficam não aplicáveis, com o motivo.
- **Alinhamento da hidrologia com correlação indefinida** (menos de duas horas comuns ou série constante) ou com a correlação sem deslocamento igual ou menor que outra: não confirmado.

---

## Requirements *(mandatory)*

### Functional Requirements

**Execução e registro dos resultados (US1)**

- **FR-001**: A Conferência DEVE fazer, numa única execução do comando `python -m src conferencia --usina <slug>`, as conferências do catálogo (FR-019) que se aplicam à usina, só com os arquivos listados em "Entradas e saídas": na hidrelétrica com EVT, as seis da FR-002; nas demais usinas, as aplicáveis ao tipo, à modalidade e ao nível dos dados. Ela NÃO DEVE acessar o portal do ONS nem alterar o perfil ou os arquivos das etapas anteriores.
- **FR-002**: Na hidrelétrica com EVT, as conferências DEVEM ser exatamente estas seis:

  | Conferência | Bases comparadas | Unidade | Coincide quando | Meta |
  |---|---|---|---|---|
  | `geracao` | geração da base de EVT × Geração por usina | horas | diferença de até 0,01 MW | n/a |
  | `disponibilidade` | disponibilidade declarada da base de EVT × disponibilidade operacional de Disponibilidade por usina | horas | diferença de até 0,01 MW | n/a |
  | `vazoes` | vazões turbinada e vertida da base de EVT × Dados hidrológicos horários | horas | as duas vazões com diferença de até 0,5 m³/s | 99 % das horas comuns |
  | `dispf_horas` | indisponibilidade programada e forçada (INDISPPF e INDISPFF) dos Indicadores de disponibilidade por unidade geradora, base mensal × horas de desligamento programado e forçado (HDP e HDF) dos Parâmetros das taxas TEIFa e TEIP | meses-unidade | as duas diferenças de até 1 h | n/a |
  | `teifa_teip` | TEIFa e TEIP recalculadas a partir das horas por estado operativo × Taxas TEIFa e TEIP publicadas | meses | as duas diferenças de até 0,001 p.p. | n/a |
  | `cadastro` | ficha de Modalidade das usinas × perfil da usina | campos | campo igual ao do perfil (na potência, diferença de até 0,001 MW) e CEG numa única linha | n/a |

  As três que comparam com a base de EVT (geração, disponibilidade e vazões) só se aplicam à hidrelétrica com EVT. As demais conferências do catálogo (FR-020 a FR-026) valem para os outros tipos e para as hidrelétricas sem EVT.
- **FR-003**: O resultado de cada conferência DEVE registrar:
  - a conferência (um dos nomes do catálogo da FR-019);
  - se é aplicável ou, se não for, o motivo;
  - as bases comparadas;
  - o período comparado: a primeira e a última hora, ou o primeiro e o último mês, comparados (no cadastro, que não tem série, e no alinhamento da hidrologia pela geração, que registra correlações, não se aplica);
  - a unidade;
  - as quantidades comparada, coincidente e divergente, sempre com comparada = coincidente + divergente;
  - a tolerância usada (o alinhamento da hidrologia pela geração não tem);
  - nas vazões, a meta e se foi atingida;
  - as tabelas de detalhe das FR-010 a FR-017 e FR-020 a FR-026.
- **FR-004**: Uma conferência DEVE ser registrada como não aplicável, com o motivo, quando alguma das suas bases não existe para a usina ou não tem dados no período, ou quando o tipo, a modalidade ou o nível dos dados da usina não a permitem (FR-019). O registro é o resultado da conferência e também a linha dela em `nao_aplicaveis.csv` (FR-018). Na geração e na disponibilidade, se as duas bases têm dados no período, mas nenhuma hora pode ser comparada, a conferência é aplicável, com 0 horas comparadas, e registra as horas só numa das fontes e, na disponibilidade, as sinalizadas. Nas conferências G1 a G5, sem nenhuma hora comum entre as fontes, a conferência é não aplicável, com o motivo. As demais conferências DEVEM ser feitas normalmente.
- **FR-005**: Os resultados DEVEM trazer os números que as legendas do relatório citam, para que nenhum resultado de conferência fique fixo no texto:
  - geração e disponibilidade: horas coincidentes, horas comuns, percentual de coincidência, horas divergentes e horas só numa das fontes;
  - vazões: horas coincidentes nas duas vazões, horas comuns, percentual de coincidência e a meta, quando não atingida;
  - DISPF × horas: meses-unidade divergentes;
  - TEIFa e TEIP: meses comparados, meses reproduzidos e a maior diferença, em p.p.;
  - cadastro: o texto de cada divergência;
  - G2, G3, G4 e G5: horas coincidentes, horas comuns, percentual de coincidência, horas divergentes e horas só numa das fontes; na G2, também as horas fora da soma por falta de alguma usina;
  - G1: horas coincidentes e comparadas no total dos pares, o percentual, as horas divergentes e a quantidade de pares de fontes;
  - alinhamento da hidrologia pela geração: horas comuns, a correlação de cada deslocamento e se o alinhamento foi confirmado;
  - conferência não aplicável: o motivo.

  A redação das legendas está na spec da Geração do relatório.
- **FR-006**: Só as conferências refeitas a cada execução DEVEM entrar nos resultados. Conferências feitas à mão fora do fluxo, como as registradas em "Conferências manuais (fora do fluxo)", NÃO DEVEM entrar nos resultados.
- **FR-007**: A Conferência NÃO DEVE corrigir valores, excluir registros nem escolher entre as fontes. As divergências ficam registradas, com os valores ou as diferenças das duas fontes.
- **FR-008**: A etapa DEVE gravar os arquivos listados em "Entradas e saídas", com o `resumo` do `etapa.json`, no formato 2:
  - na hidrelétrica com EVT, `conferencias.pkl` traz os seis resultados da FR-002, aplicáveis ou não;
  - nas demais usinas, `conferencias.pkl` traz só os resultados das conferências aplicadas, e as não aplicáveis ficam só em `nao_aplicaveis.csv` (FR-018);
  - as Análises recusam os resultados de um formato anterior, com o código 5.
- **FR-009**: A etapa DEVE terminar com os códigos de saída listados em "Entradas e saídas". Divergências NÃO DEVEM mudar o código de saída; só a meta das vazões não atingida o muda (FR-013).

**Geração, disponibilidade declarada e vazões (US2)**

- **FR-010**: A conferência da geração DEVE comparar, hora a hora, a geração da base de EVT com a de Geração por usina:
  - entram as horas de Geração por usina com valor válido (as sinalizadas pelo Tratamento ficam fora) e as horas da base de EVT com geração entre a primeira e a última dessas horas;
  - nas horas comuns, a hora coincide com diferença de até 0,01 MW; acima disso, é divergente;
  - as horas só em Geração por usina e as horas só na base de EVT são contadas à parte, uma fonte de cada vez; a hora sinalizada em Geração por usina conta como hora só na base de EVT;
  - registra a energia total de cada fonte e a tabela mensal com a energia de cada fonte, a diferença (Geração por usina menos base de EVT) e as horas só em cada fonte;
  - agrupa as horas divergentes em períodos contínuos, com início, fim, horas e a diferença média e a máxima.
- **FR-011**: A conferência da disponibilidade DEVE comparar, hora a hora, a disponibilidade declarada da base de EVT com a disponibilidade operacional de Disponibilidade por usina:
  - as horas de Disponibilidade por usina sinalizadas pelo Tratamento (regras D1 a D4) ficam fora, e a quantidade delas é registrada;
  - nas horas com as duas disponibilidades, a hora coincide com diferença de até 0,01 MW;
  - são contadas à parte as horas só em Disponibilidade por usina e as horas da base de EVT que faltam nela, dentro do intervalo que ela cobre;
  - agrupa as horas divergentes em períodos contínuos, com início, fim, horas e a diferença média e a máxima.
- **FR-012**: A conferência das vazões DEVE comparar, hora a hora, as vazões turbinada e vertida da base de EVT com as de Dados hidrológicos horários, já convertidas pelo Tratamento para a hora de início:
  - entram as horas em que as duas fontes têm as duas vazões; a vazão negativa, sinalizada pelo Tratamento, não entra;
  - cada vazão coincide com diferença de até 0,5 m³/s, e a hora coincide quando as duas vazões coincidem;
  - registra as horas comuns, as coincidentes na turbinada, na vertida e nas duas, o percentual de coincidência (horas coincidentes nas duas ÷ horas comuns × 100) e o deslocamento de hora aplicado pelo Tratamento (−1 h).
- **FR-013**: A meta das vazões é de 99 % das horas comuns:
  - é atingida quando o percentual de coincidência é de pelo menos 99 % e há ao menos uma hora comum;
  - quando não é atingida, a etapa DEVE gravar os seis resultados, registrar a meta como não atingida e terminar com o código 3, que interrompe o comando `completo`;
  - o `etapa.json` DEVE registrar a etapa como concluída, com o código 3, para que as etapas seguintes possam ser executadas à parte, com a meta não atingida registrada.

**Indicadores oficiais de disponibilidade (US3)**

- **FR-014**: A conferência DISPF × horas DEVE comparar, em cada mês e UG presentes nas duas bases, a indisponibilidade publicada nos indicadores com as horas de desligamento dos parâmetros das taxas:
  - a indisponibilidade programada (INDISPPF) e a forçada (INDISPFF), percentuais do mês, são convertidas em horas: percentual × horas do período (HP) ÷ 100;
  - são comparadas com as horas de desligamento programado (HDP) e forçado (HDF);
  - o mês-unidade diverge quando alguma das duas diferenças passa de 1 h, em valor absoluto;
  - o mês-unidade em que falta algum desses valores (INDISPPF, INDISPFF, HP, HDP ou HDF) não é comparado: fica fora das quantidades comparada, coincidente e divergente e é contado à parte;
  - registra a lista dos meses-unidade divergentes, com as horas das duas fontes e as duas diferenças.
- **FR-015**: A conferência da TEIFa e da TEIP DEVE recalcular as duas taxas para cada mês publicado, com as horas por estado operativo da janela móvel de 60 meses que termina nesse mês, ponderadas pela potência de cada UG (peso 1 quando a potência não é conhecida):
  - TEIFa = Σ P × (HDF + HEDF) ÷ Σ P × (HP − HDP − HEDP);
  - TEIP = Σ P × (HDP + HEDP) ÷ Σ P × HP.

  O recálculo só é feito com a janela completa, isto é, quando o primeiro mês da janela (59 meses antes do mês da taxa) não é anterior ao primeiro mês das horas por estado operativo. Nos demais meses, as taxas recalculadas ficam vazias e o mês não é comparado.
- **FR-016**: Um mês DEVE contar como reproduzido quando as duas diferenças (recalculada menos publicada, em pontos percentuais) são de até 0,001 p.p., em valor absoluto. Um mês com a janela completa em que falta a taxa publicada ou a recalculada não é comparado: fica fora das quantidades e é contado à parte. A conferência registra:
  - mês a mês: os meses na janela, as taxas publicadas e recalculadas e as duas diferenças;
  - os meses comparados (os de janela completa), os reproduzidos (coincidentes), os não reproduzidos (divergentes) e a maior diferença.

  Sem nenhum mês com a janela completa, a conferência é não aplicável, com esse motivo. Na hidrelétrica com EVT, a tabela mês a mês continua registrada, com as taxas recalculadas vazias; nas demais usinas, a conferência fica só em `nao_aplicaveis.csv` (FR-018).

**Cadastro (US4)**

- **FR-017**: A conferência do cadastro DEVE comparar a ficha da usina extraída pela Coleta de dados com o perfil:

  | Campo da ficha | Comparado com | Diverge quando |
  |---|---|---|
  | potência autorizada | `parametros.potencia_instalada_mw` | a diferença passa de 0,001 MW, ou o valor falta ou não é numérico |
  | estado | `usina.estado` | é diferente |
  | id ONS | `identificacao.id_ons` | é diferente; o perfil sem id ONS (usina em conjunto sem id próprio) só diverge da ficha com id ONS |
  | CEG | uma única linha do cadastro com o CEG | há mais de uma linha; vale a primeira |

  Cada divergência DEVE ser registrada com o valor do cadastro e o do perfil (no CEG, com a quantidade de linhas). O id ONS ausente, no cadastro ou no perfil, aparece no texto como "não informado". Sem divergência, a lista de divergências fica vazia.

**Catálogo das conferências e conferências não aplicáveis (US1 e US5)**

- **FR-018**: A etapa DEVE gravar `nao_aplicaveis.csv`, com `conferencia` e `motivo`, com todas as conferências do catálogo (FR-019) que não se aplicam à usina, inclusive na hidrelétrica com EVT:
  - entram as que não se aplicam ao tipo, à modalidade ou ao nível dos dados da usina, com o motivo do catálogo, e as que rodaram sem base, com o motivo do resultado;
  - a exceção é o alinhamento da hidrologia pela geração (FR-026) fora das hidrelétricas: ele não ganha linha, porque a conferência das vazões já registra que a hidrologia não se aplica ao tipo;
  - o arquivo é só registro (constituição, princípio VI). Na hidrelétrica com EVT, `conferencias.pkl` continua com os seis resultados da FR-002, e o relatório e a planilha dela não leem o arquivo;
  - nas demais usinas, as notas do relatório citam as conferências não aplicáveis, com o motivo (spec da Geração do relatório).
- **FR-019**: Cada conferência do catálogo DEVE declarar:
  - a condição de aplicação: os tipos de usina, as bases (os conjuntos do ONS que a Coleta precisa ter obtido para a usina) e o nível exigido de cada base (usina ou conjunto);
  - o motivo escrito quando não se aplica.

  Regras de todas as conferências do catálogo:
  - as comparações entre fontes são sempre no mesmo nível (usina com usina, conjunto com conjunto); par de níveis diferentes não é comparado;
  - só a conferência das vazões tem meta (FR-013). As demais só registram o resultado e nunca mudam o código de saída; uma meta para elas só entra nesta spec com a aprovação do usuário;
  - nas conferências entre fontes G1 a G5 (FR-020, FR-021 e FR-023 a FR-025), a hora coincide com diferença de até 0,01 MW; só as horas com valor nas duas fontes são comparadas, e as horas só numa fonte são contadas à parte, por fonte; a tabela mensal traz a energia de cada fonte nas horas comuns, a diferença (a primeira fonte menos a segunda) e as horas comuns, divergentes e só em cada fonte; as horas divergentes são agrupadas em períodos contínuos, com início, fim, horas e a diferença média e a máxima.

  O catálogo, com a aplicabilidade de cada conferência, está em "Aplicabilidade por tipo".

**Térmicas e nucleares (US5)**

- **FR-020**: Em UTE e UTN, com o despacho e a Programação diária no nível da usina, a conferência `programacao_despacho` (G3) DEVE comparar, hora a hora, a Programação diária (média horária dos patamares) com a geração programada do despacho (Geração térmica por motivo de despacho, `val_proggeracao`), com a tolerância de 0,01 MW e sem meta.
- **FR-021**: Em UTE e UTN, com o despacho e a Geração por usina no nível da usina, a conferência `verificada_despacho` (G4) DEVE comparar, hora a hora, a geração verificada do despacho (`val_verifgeracao`) com a Geração por usina, com a mesma tolerância e sem meta. A G4 confere também a convenção de hora do despacho: mede ainda a coincidência com a Geração por usina deslocada de +1 h e de −1 h. Se ela melhorar com o deslocamento, o log avisa que a convenção declarada está errada; a correção é feita no Tratamento, nunca por ajuste automático (FR-037 da spec do Tratamento de dados).
- **FR-022**: Nas térmicas, a DISPF × horas por estado operativo e a TEIFa e a TEIP refeitas DEVEM seguir as FR-014 a FR-016, com os indicadores obtidos pelo CEG:
  - as horas do período (HP) que o ONS publica para as térmicas somam também as horas equivalentes (HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF); a conferência usa o HP publicado, sem refazê-lo;
  - a usina com as horas por estado operativo e ausente das taxas TEIFa e TEIP publicadas tem a TEIFa e a TEIP não aplicáveis, com esse motivo;
  - uma regra de cálculo própria das térmicas só entra nesta spec com a fonte publicada pelo ONS. Sem fonte, a divergência entre as taxas refeitas e as publicadas fica registrada, sem ajuste.

**Eólicas e solares (US5)**

- **FR-023**: Em EOL e UFV, a conferência `geracao_fontes` (G1) DEVE comparar a geração da usina entre as fontes que a trazem, sempre duas a duas, no mesmo nível e hora a hora, com a tolerância de 0,01 MW e sem meta:
  - as fontes: Geração por usina, Fator de capacidade (`val_geracaoverificada`), restrição com detalhe (geração verificada) e restrição com a razão (`val_geracao`);
  - as duas restrições, semi-horárias, entram em hora cheia, pela média das duas meias-horas; a hora sem as duas meias-horas fica fora;
  - cada par é comparado em cada nível que as duas fontes têm; par de níveis diferentes não é comparado;
  - registra, por par e nível, as horas comuns, coincidentes e divergentes, as horas só em cada fonte e a energia de cada fonte, e a tabela mensal; as quantidades do resultado são a soma dos pares.
- **FR-024**: Em EOL e UFV em conjunto, com os `[[identificacao.membros]]` no perfil e a Geração por usina do conjunto, a conferência `soma_conjunto` (G2) DEVE comparar, hora a hora, a soma das usinas do conjunto (restrição com detalhe da usina e dos membros, em hora cheia) com a geração do conjunto (Geração por usina do conjunto), com a tolerância de 0,01 MW e sem meta:
  - só entram as horas com valor em todas as usinas da composição vigente; cada membro vale do dia de entrada ao de saída declarados no perfil, e a usina do relatório vale sempre;
  - as horas com alguma usina vigente sem valor ficam fora da soma e são contadas;
  - as séries das outras usinas do conjunto só entram aqui, como contexto identificado (constituição, princípio III).

  Fora de conjunto ou sem os membros no perfil, a G2 fica não aplicável, com o motivo.
- **FR-025**: Em EOL e UFV, com a Programação diária e o Fator de capacidade no mesmo nível, a conferência `programacao_renovaveis` (G5) DEVE comparar, hora a hora, a Programação diária (média horária dos patamares) com a geração programada do Fator de capacidade (`val_geracaoprogramada`), com a tolerância de 0,01 MW e sem meta.

**Hidrelétricas sem EVT (US5)**

- **FR-026**: Na hidrelétrica sem EVT, com os Dados hidrológicos e a Geração por usina no nível da usina, a conferência `alinhamento_hidrologia` DEVE conferir a hora da hidrologia pela geração, porque não há a base de EVT para a conferência das vazões (FR-012 e FR-013):
  - o cálculo: a correlação entre a vazão turbinada (já na hora de início, deslocada −1 h pelo Tratamento; a vazão negativa sinalizada não entra) e a geração da usina, com a hidrologia deslocada de −1, 0 e +1 hora;
  - o alinhamento é confirmado quando a correlação sem deslocamento é maior que a de cada outro deslocamento com correlação definida. Correlação indefinida (menos de duas horas comuns ou série constante) não confirma;
  - registra as horas comuns e a correlação de cada deslocamento; as quantidades do resultado são as horas comuns sem deslocamento, todas coincidentes quando o alinhamento é confirmado e todas divergentes quando não é;
  - sem a confirmação, as Análises publicam só a cobertura e o resultado desta conferência, como a FR-034 da spec das Análises faz com as vazões, mas sem a meta (FR-061 da spec das Análises);
  - sem meta e sem o código 3: a conferência só registra o resultado. A convenção de hora nunca é ajustada automaticamente;
  - sem a hidrologia ou sem a geração no nível da usina (hidrelétrica em conjunto), a conferência fica não aplicável, com o motivo. Na hidrelétrica com EVT, ela também não se aplica, porque vale a conferência das vazões; fora das hidrelétricas, não é registrada (FR-018).

### Key Entities

- **Resultado de conferência**: uma das conferências do catálogo, com a aplicabilidade (ou o motivo), as bases, o período, a unidade, as quantidades comparada, coincidente e divergente, a tolerância, a meta (só nas vazões) e as tabelas de detalhe. É refeito a cada execução e lido pelas Análises, que o repassam à Geração do relatório.
- **Catálogo das conferências**: as doze conferências (as seis da FR-002, G1 a G5 e o alinhamento da hidrologia pela geração), cada uma com os tipos de usina, as bases, o nível exigido e o motivo quando não se aplica.
- **Conferência não aplicável**: linha de `nao_aplicaveis.csv`, com a conferência e o motivo.
- **Divergência**: o que não coincide, na unidade da conferência: período contínuo de horas (geração, disponibilidade e G1 a G5), mês-unidade (DISPF × horas), mês não reproduzido (TEIFa e TEIP) ou campo da ficha (cadastro), sempre com os valores ou as diferenças das duas fontes.
- **Recálculo das taxas**: para cada mês publicado, os meses na janela, a TEIFa e a TEIP publicadas e recalculadas e as diferenças em p.p.
- **Resumo da etapa**: a situação das conferências registradas e a lista das não aplicáveis, no `etapa.json`.

---

## Aplicabilidade por tipo

"Hidrelétrica com EVT" é a UHE, PCH ou CGH com série própria na Energia Vertida Turbinável; ela segue as seis conferências da FR-002. Nas células, "sim" quer dizer aplicada sempre que as bases têm dados no período (FR-004); "não aplicável" quer dizer registrada em `nao_aplicaveis.csv`, com o motivo.

| Conferência | Hidrelétrica com EVT | UHE, PCH, CGH sem EVT | UTE, UTN | EOL, UFV |
|---|---|---|---|---|
| `geracao`: base de EVT × Geração por usina (FR-010) | sim | não aplicável: sem EVT | não aplicável: tipo | não aplicável: tipo |
| `disponibilidade`: base de EVT × Disponibilidade por usina (FR-011) | sim | não aplicável: sem EVT | não aplicável: tipo | não aplicável: tipo |
| `vazoes`: base de EVT × Dados hidrológicos, com a meta (FR-012 e FR-013) | sim | não aplicável: sem EVT | não aplicável: tipo | não aplicável: tipo |
| `dispf_horas`: DISPF × horas por estado operativo (FR-014) | com os indicadores | com os indicadores | com os indicadores (FR-022) | não aplicável: tipo |
| `teifa_teip`: TEIFa e TEIP refeitas (FR-015 e FR-016) | com as taxas | com as taxas | com as taxas (FR-022) | não aplicável: tipo |
| `cadastro`: ficha do cadastro × perfil (FR-017) | sim | sim | sim | sim |
| `geracao_fontes`: G1, geração entre fontes (FR-023) | não aplicável: tipo | não aplicável: tipo | não aplicável: tipo | só os pares do mesmo nível; sem duas fontes no mesmo nível, não aplicável |
| `soma_conjunto`: G2, soma das usinas × conjunto (FR-024) | não aplicável: tipo | não aplicável: tipo | não aplicável: tipo | em conjunto, com os membros no perfil e a Geração por usina do conjunto; fora de conjunto ou sem os membros, não aplicável |
| `programacao_despacho`: G3, programação × despacho (FR-020) | não aplicável: tipo | não aplicável: tipo | com o despacho e a Programação diária da usina; sem eles, não aplicável | não aplicável: tipo |
| `verificada_despacho`: G4, verificada do despacho × Geração por usina (FR-021) | não aplicável: tipo | não aplicável: tipo | com o despacho e a Geração por usina da usina; sem eles, não aplicável | não aplicável: tipo |
| `programacao_renovaveis`: G5, programação × fator de capacidade (FR-025) | não aplicável: tipo | não aplicável: tipo | não aplicável: tipo | com as duas bases no mesmo nível; sem uma delas ou em níveis diferentes, não aplicável |
| `alinhamento_hidrologia`: hidrologia pela geração (FR-026) | não aplicável: vale a conferência das vazões | com a hidrologia e a geração no nível da usina; sem uma das duas, não aplicável | sem linha em `nao_aplicaveis.csv` | sem linha em `nao_aplicaveis.csv` |

- **PCH e CGH em conjunto**: nenhuma conferência nova (ver "Edge Cases"). As conferências da hidrelétrica ficam não aplicáveis; o alinhamento da hidrologia, sem a geração no nível da usina, também.
- **Usina Tipo III e MMGD**: não têm perfil nem relatório por usina (spec da Coleta de dados); a Conferência não roda para elas.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com o perfil da São Domingos e os dados tratados atuais, os seis resultados são iguais aos de hoje:
  - geração: 70.895 de 70.895 horas coincidentes (100,0 %), nenhuma hora divergente e nenhuma hora só numa das fontes;
  - disponibilidade: 70.895 de 70.895 horas coincidentes (100,0 %), nenhuma hora só numa das fontes e nenhuma hora sinalizada excluída;
  - vazões: 70.731 de 70.731 horas coincidentes nas duas vazões (100,0 %), meta atingida;
  - DISPF × horas: 4 meses-unidade divergentes (UG2 em 03/2024 e 08/2025; UG1 em 04/2025 e 08/2026);
  - TEIFa e TEIP: 21 de 21 meses com janela completa reproduzidos (12/2024 a 08/2026), com diferença máxima inferior a 0,0001 p.p.;
  - cadastro: sem divergência.

  As tabelas registradas são iguais, célula a célula, às abas atuais da planilha (GER_CONFERENCIA, GER_MENSAL, DISP_CONFERENCIA, HID_ALINHAMENTO, ONS_DIVERGENCIAS e ONS_TEIFA_TEIP) e à coluna de divergências da aba CAD_FICHA.
- **SC-002**: Em 100 % das conferências aplicáveis, a quantidade comparada é a soma das coincidentes e das divergentes. Nas conferências hora a hora, 100 % das horas comuns são classificadas como coincidentes ou divergentes, e a soma das horas dos períodos divergentes é igual à quantidade de horas divergentes.
- **SC-003**: Em testes com dados sintéticos, sem rede:
  - com vazões coincidentes em menos de 99 % das horas comuns, a etapa termina com código 3 em 100 % dos casos, com os seis resultados gravados;
  - com 99 % ou mais, termina com código 0;
  - sem dados hidrológicos, a conferência das vazões fica não aplicável, e a etapa termina com código 0.
- **SC-004**: Com o perfil de uma usina fictícia sem algum conjunto, sobre dados de teste, 100 % das conferências sem base ficam registradas como não aplicáveis, com o motivo, em `nao_aplicaveis.csv`, e as demais são feitas.
- **SC-005**: A execução da etapa não acessa a rede e não altera nenhum arquivo das etapas anteriores (mesmo SHA-256 antes e depois).
- **SC-006**: 100 % dos resultados gravados trazem os campos da FR-003 e os números da FR-005, ou o motivo de não serem aplicáveis.
- **SC-007**: Na hidrelétrica com EVT, `conferencias.pkl` traz os seis resultados, iguais aos de antes da ampliação para todos os tipos, e `nao_aplicaveis.csv` lista G1 a G5 e o alinhamento da hidrologia pela geração, com o motivo. Nenhum arquivo do relatório lê `nao_aplicaveis.csv` (teste próprio).
- **SC-008**: Com uma usina fictícia de cada tipo (UHE, PCH, CGH, UTE, UTN, EOL e UFV), sem rede, a etapa termina com código 0 em 100 % dos casos; `conferencias.pkl` traz só as conferências aplicadas (na UHE, as seis), e `nao_aplicaveis.csv`, todas as do catálogo que não se aplicam, com o motivo, salvo o alinhamento da hidrologia fora das hidrelétricas.
- **SC-009**: Nas usinas piloto aprovadas (UTE William Arjona, UFV Seriemas 1, EOL Praia Formosa e PCH Bandeirante), a Conferência refeita a partir da Coleta e do perfil congelados de cada referência leva ao relatório aprovado, sem diferença (`comparar --todas`, spec da Geração do relatório).

---

## Decisões do usuário

| Data | Decisão | Onde se aplica |
|---|---|---|
| 02/10/2026 | As conferências ficam no período da base de EVT; a série de Geração por usina anterior a ele (desde 18/06/2015) não é conferida. | FR-010 |
| 05/10/2026 | A conferência da base de EVT com os dados publicados no S3 do ONS, feita em 02/10/2026, não ganha versão reproduzível no fluxo; o resultado fica registrado, e a base continua conferível pelo servidor de consulta aos dados do ONS. | FR-006; Conferências manuais (fora do fluxo) |
| 05/10/2026 | As bases da CCEE e da ANEEL ficam fora do fluxo; já tinham sido comparadas manualmente em 01 e 02/10/2026. | FR-006; Conferências manuais (fora do fluxo) |
| 06/10/2026 | Só as conferências refeitas a cada execução entram nas legendas; as manuais, com a CCEE e com o BI da ANEEL, ficam fora do relatório. | FR-005, FR-006 |
| 07/10/2026 | Os arquivos de apoio às conferências manuais (`data/ccee/` e `data/aneel_bi/`) saem do projeto, e os resultados ficam registrados na spec da Conferência. | Conferências manuais (fora do fluxo) |
| 08/10/2026 | O mês (ou mês-unidade) com valor ausente fica fora da comparação e é contado à parte, no DISPF × horas e na TEIFa e TEIP; sem hora comparável, as conferências da geração e da disponibilidade continuam aplicáveis, com 0 horas comparadas. | FR-004, FR-014, FR-016 |
| 09/10/2026 | Ampliação do fluxo para todos os tipos de usina. As conferências do catálogo que não se aplicam à usina ficam registradas em `nao_aplicaveis.csv`, com o motivo, inclusive na UHE, sem mudar o relatório dela. | FR-001, FR-002, FR-018, FR-019; Aplicabilidade por tipo |
| 09/10/2026 | As comparações entre fontes são sempre no mesmo nível (usina com usina, conjunto com conjunto); entram a geração verificada do despacho × Geração por usina (G4) e a Programação diária × geração programada do Fator de capacidade (G5). | FR-019, FR-021, FR-023 a FR-025 |
| 19/10/2026 | Ajustes do código aos requisitos aprovados: a Conferência passa ao formato 2, e nas usinas sem EVT `conferencias.pkl` traz só as conferências aplicadas. | FR-008, FR-018 |
| 19/10/2026 | Aprovadas as conferências das térmicas: G3 e G4, sem meta, e a DISPF × horas e a TEIFa e a TEIP pelo CEG, com a apuração da divergência das taxas refeitas da UTE piloto. | FR-020 a FR-022 |
| 20/10/2026 | Aprovadas as conferências das eólicas e solares: G1, G2 e G5, sem meta. | FR-023 a FR-025 |
| 20/10/2026 | Aprovado o relatório da UTE William Arjona com a TEIFa e a TEIP refeitas sem reproduzir nenhum dos 4 meses de janela completa (diferenças de 0,08 a 2,07 p.p. na TEIFa): sem fonte publicada de uma regra própria das térmicas, a divergência fica registrada, sem ajuste. | FR-022 |
| 22/10/2026 | Na hidrelétrica sem EVT, a hora dos Dados hidrológicos é conferida pela correlação da vazão turbinada com a geração da usina, com −1, 0 e +1 h, sem meta. | FR-026 |
| 22/10/2026 | A CCEE como fonte nova (geração das PCH e CGH em conjunto) fica para uma avaliação própria, depois da ampliação para todos os tipos; até lá, continua fora do fluxo. | FR-006; Assumptions (Bases) |
| 23/10/2026 | As taxas operativas não são conferidas com as oficiais: as regras de apuração diferem, e o ONS não publica a diferença; a comparação entre as duas é das Análises (aprovado pelo usuário). | conferência `teifa_teip` |

## Conferências manuais (fora do fluxo)

Conferências feitas à mão para a UHE São Domingos. Não são refeitas a cada execução nem citadas no relatório. Os arquivos de apoio das conferências com a CCEE e com o BI da ANEEL foram excluídos em 07/10/2026, com aprovação do usuário.

| Data | Fonte | Período | O que foi comparado | Resultado |
|---|---|---|---|---|
| 01/10/2026 | CCEE (amostra) | jul/2026 | geração no centro de gravidade × geração do ONS | geração no centro de gravidade = geração do ONS × fator de perda interna; confirma que o registro de 68,7 MW de 15/05/2019 é erro do ONS |
| 02/10/2026 | BI da ANEEL (exportações) | 2013 a 2025 | geração "Verificada" × geração do ONS | geração "Verificada" idêntica à do ONS; série da CCEE desde 2013 |
| 02/10/2026 | Energia Vertida Turbinável no S3 do ONS, pelo servidor de consulta aos dados do ONS | ago/2018 a set/2026 | totais mensais publicados × base de EVT local | idênticos em todos os meses de ago/2018 a ago/2026 e de 01 a 28/09/2026; o portal já tinha dados até 30/09 |

## Assumptions

- **Entradas**: o Tratamento entrega as séries na hora de início, no período da série de referência, com um valor por hora e com as sinalizações de qualidade. Nas usinas sem EVT, a base horária comum traz a geração da série de referência com o nível (FR-035 da spec do Tratamento de dados), e as séries semi-horárias chegam também em hora cheia (FR-041 da spec do Tratamento de dados). Nos indicadores e nas taxas, vale a versão mais recente publicada. A Conferência não refaz nada disso.
- **Tolerâncias e meta**: 0,01 MW, 0,5 m³/s, 1 h, 0,001 p.p. e 0,001 MW acompanham o arredondamento dos valores publicados; as conferências G1 a G5 usam os 0,01 MW da geração. Elas e a meta de 99 %, só das vazões, são regras gerais, iguais para qualquer usina; o perfil não as altera.
- **Fora desta etapa**:
  - a identidade das horas por estado operativo (horas do período iguais à soma das parcelas, com tolerância de 0,1 h) é regra de consistência do Tratamento;
  - a decomposição da TEIFa e da TEIP por UG e parcela, a capacidade não sincronizada × reserva desligada, a disponibilidade declarada × DISPF por ano e o cruzamento com a programação diária ficam nas Análises, porque não conferem a mesma grandeza em duas fontes.
- **Leitura dos resultados**: a conferência diz se as fontes coincidem, não qual está certa. As divergências viram constatações, itens da conclusão e legendas nas etapas seguintes; com a meta das vazões não atingida, as Análises não publicam os cruzamentos hidrológicos, e, na hidrelétrica sem EVT, sem o alinhamento da hidrologia confirmado, publicam só a cobertura da hidrologia.
- **Bases**: só bases do ONS, as que a Coleta obtém conforme o tipo e a `[cobertura]` do perfil. Na hidrelétrica com EVT, as seis conferências de sempre, sem base nova. As bases de fora do ONS (CCEE, ANEEL) ficam fora do fluxo (decisões do usuário de 05, 07 e 22/10/2026).
- **Formato**: `conferencias.pkl` serve às etapas seguintes; os CSV são a versão para consulta, e a planilha do relatório continua sendo a versão completa e legível. `nao_aplicaveis.csv` é lido pelas Análises nas usinas sem EVT, para as notas do relatório.
