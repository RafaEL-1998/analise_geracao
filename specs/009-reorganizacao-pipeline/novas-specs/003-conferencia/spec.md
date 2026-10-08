# Spec da Etapa 3: Conferência

**Etapa**: 3 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-08

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

Comparar entre si as bases do ONS que trazem a mesma grandeza e refazer os indicadores oficiais que podem ser recalculados a partir dos dados publicados. São seis conferências, e o resultado de cada uma fica registrado do mesmo modo (bases, período, quantidade comparada, coincidências, divergências e tolerância), para que as Análises e as legendas do relatório citem resultados refeitos a cada execução. A etapa não corrige dados nem escolhe entre as fontes, e interrompe o fluxo quando as vazões não confirmam o alinhamento dos horários.

## Entradas e saídas

**Comando**: `python -m src conferencia --usina <slug>`

- Sem opções próprias; vale a opção comum `--log-level`.
- Pré-requisito: Tratamento de dados concluído para a usina.
- As regras comuns do fluxo (sintaxe dos comandos, perfil da usina e código 4, `etapa.json`, pré-requisitos e código 5, comando `completo`) estão na spec da Coleta de dados.

**Lê** (só arquivos locais, nunca o portal do ONS):

| Pasta | Arquivo | Conferência |
|---|---|---|
| `data/usinas/<slug>/tratamento/` | `evt_tratado.parquet`: geração, disponibilidade declarada e vazões turbinada e vertida da base de EVT | geração, disponibilidade, vazões |
| | `geracao_horaria.csv` | geração |
| | `disponibilidade_horaria.csv` | disponibilidade |
| | `hidrologia_horaria.csv` | vazões |
| | `indicadores_ug_mensal.csv` e `horas_estado_mensal.csv` | DISPF × horas |
| | `horas_estado_mensal.csv` e `teifa_teip_mensal.csv` | TEIFa e TEIP |
| | `indicadores_ug_anual.csv`, `geracao_ausencias.csv`, `auditoria_geracao.csv`, `disponibilidade_ausencias.csv`, `auditoria_disponibilidade.csv`, `hidrologia_ausencias.csv` e `auditoria_hidrologia.csv`: lidos com os indicadores e as séries, sem uso nas conferências | nenhuma |
| `data/usinas/<slug>/coleta/` | `cadastro_ficha.csv`, com a quantidade de linhas com o CEG; o cadastro não passa por tratamento | cadastro |
| `usinas/<slug>/perfil.toml` | `parametros.potencia_instalada_mw`, `usina.estado` e `identificacao.id_ons` | cadastro |

**Grava** em `data/usinas/<slug>/conferencia/`:

| Arquivo | Conteúdo |
|---|---|
| `conferencias.pkl` | os seis resultados (FR-003), com a versão do formato; é o que as Análises leem e repassam à Geração do relatório |
| `geracao.csv` | geração mês a mês: energia de cada fonte, diferença e horas só em cada fonte |
| `geracao_divergencias.csv` | horas divergentes da geração, em períodos contínuos |
| `disponibilidade.csv` | resumo da conferência da disponibilidade, numa linha |
| `disponibilidade_divergencias.csv` | horas divergentes da disponibilidade, em períodos contínuos |
| `vazoes.csv` | resumo do alinhamento das vazões, numa linha, com a meta e se foi atingida |
| `dispf_horas.csv` | meses-unidade divergentes, com as horas das duas fontes e as diferenças |
| `teifa_teip.csv` | taxas publicadas e recalculadas, mês a mês, com as diferenças |
| `cadastro.csv` | campos conferidos da ficha, com o valor do cadastro, o do perfil e a situação |
| `etapa.json` | manifesto da etapa, com o `resumo` |

- Sem divergência, os arquivos de divergências (`geracao_divergencias.csv`, `disponibilidade_divergencias.csv` e `dispf_horas.csv`) são gravados sem linhas. Numa conferência não aplicável por falta de base, os CSV dela não são gravados.
- Os arquivos desta etapa não têm cópia `.bak`: são refeitos a partir dos dados tratados.
- **`resumo` do `etapa.json`**: para cada conferência, se é aplicável (ou o motivo), as quantidades comparada, coincidente e divergente, com a unidade, e, nas vazões, o percentual de coincidência e se a meta foi atingida.

**Códigos de saída**:

| Código | Quando |
|---|---|
| 0 | as seis conferências registradas; a meta das vazões atingida ou não aplicável |
| 1 | erro, inclusive falha de gravação e interrupção pelo usuário |
| 3 | meta das vazões não atingida (FR-013): coincidência abaixo de 99 % das horas comuns, ou nenhuma hora comum; os seis resultados são gravados |
| 5 | Tratamento de dados sem resultados concluídos, com resultados desatualizados ou em formato antigo; nada é gravado |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conferir as bases numa etapa própria, com os resultados registrados (Priority: P1)

Como fiscal da AGEMS, quero que todas as conferências entre fontes fiquem numa etapa só, executada por um comando, e que o resultado de cada uma fique registrado do mesmo modo: bases, período, quantidade comparada, coincidências, divergências e tolerância. Assim as análises e as legendas do relatório citam resultados refeitos a cada execução, e eu sei onde encontrar cada divergência.

**Why this priority**: É o objetivo da etapa. Sem o registro único, as conferências voltam a ficar espalhadas entre a extração das bases e as análises.

**Independent Test**: Executar o comando sobre dados tratados de teste, sem rede, e conferir os seis resultados, os arquivos da pasta `conferencia/` e o `resumo` do `etapa.json`. Com o perfil da São Domingos e os dados locais, comparar com os resultados atuais (SC-001).

**Acceptance Scenarios**:

1. **Given** o Tratamento de dados concluído, **When** a etapa é executada, **Then** os seis resultados são gravados, cada um com bases, período, unidade, quantidades comparada, coincidente e divergente e tolerância, e o `resumo` do `etapa.json` traz a situação de cada conferência.
2. **Given** os dados atuais (perfil da São Domingos), **When** a etapa é executada, **Then**:
   - geração e disponibilidade: 70.895 de 70.895 horas coincidentes;
   - vazões: 70.731 de 70.731 horas coincidentes, com a meta atingida;
   - DISPF × horas: 4 meses-unidade divergentes;
   - TEIFa e TEIP: 21 de 21 meses reproduzidos;
   - cadastro: sem divergência;
   - a etapa termina com código 0.
3. **Given** uma usina sem dados hidrológicos, **When** a etapa é executada, **Then** a conferência das vazões fica registrada como não aplicável, com o motivo, as outras cinco são feitas e a etapa termina com código 0.
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
- **Conferências feitas à mão fora do fluxo**: não entram nos resultados nem no relatório; ficam registradas em "Conferências manuais (fora do fluxo)".

---

## Requirements *(mandatory)*

### Functional Requirements

**Execução e registro dos resultados (US1)**

- **FR-001**: A Conferência DEVE fazer as seis conferências da FR-002 numa única execução do comando `python -m src conferencia --usina <slug>`, só com os arquivos listados em "Entradas e saídas". Ela NÃO DEVE acessar o portal do ONS nem alterar o perfil ou os arquivos das etapas anteriores.
- **FR-002**: As conferências DEVEM ser exatamente estas seis:

  | Conferência | Bases comparadas | Unidade | Coincide quando | Meta |
  |---|---|---|---|---|
  | `geracao` | geração da base de EVT × Geração por usina | horas | diferença de até 0,01 MW | n/a |
  | `disponibilidade` | disponibilidade declarada da base de EVT × disponibilidade operacional de Disponibilidade por usina | horas | diferença de até 0,01 MW | n/a |
  | `vazoes` | vazões turbinada e vertida da base de EVT × Dados hidrológicos horários | horas | as duas vazões com diferença de até 0,5 m³/s | 99 % das horas comuns |
  | `dispf_horas` | indisponibilidade programada e forçada (INDISPPF e INDISPFF) dos Indicadores de disponibilidade por unidade geradora, base mensal × horas de desligamento programado e forçado (HDP e HDF) dos Parâmetros das taxas TEIFa e TEIP | meses-unidade | as duas diferenças de até 1 h | n/a |
  | `teifa_teip` | TEIFa e TEIP recalculadas a partir das horas por estado operativo × Taxas TEIFa e TEIP publicadas | meses | as duas diferenças de até 0,001 p.p. | n/a |
  | `cadastro` | ficha de Modalidade das usinas × perfil da usina | campos | campo igual ao do perfil (na potência, diferença de até 0,001 MW) e CEG numa única linha | n/a |

- **FR-003**: O resultado de cada conferência DEVE registrar:
  - a conferência (um dos seis nomes da FR-002);
  - se é aplicável ou, se não for, o motivo;
  - as bases comparadas;
  - o período comparado: a primeira e a última hora, ou o primeiro e o último mês, comparados (no cadastro, que não tem série, não se aplica);
  - a unidade;
  - as quantidades comparada, coincidente e divergente, sempre com comparada = coincidente + divergente;
  - a tolerância usada;
  - nas vazões, a meta e se foi atingida;
  - as tabelas de detalhe das FR-010 a FR-017.
- **FR-004**: Uma conferência DEVE ser registrada como não aplicável, com o motivo, quando alguma das suas bases não existe para a usina ou não tem dados no período. Na geração e na disponibilidade, se as duas bases têm dados no período, mas nenhuma hora pode ser comparada, a conferência é aplicável, com 0 horas comparadas, e registra as horas só numa das fontes e, na disponibilidade, as sinalizadas. As demais conferências DEVEM ser feitas normalmente.
- **FR-005**: Os resultados DEVEM trazer os números que as legendas do relatório citam, para que nenhum resultado de conferência fique fixo no texto:
  - geração e disponibilidade: horas coincidentes, horas comuns, percentual de coincidência, horas divergentes e horas só numa das fontes;
  - vazões: horas coincidentes nas duas vazões, horas comuns, percentual de coincidência e a meta, quando não atingida;
  - DISPF × horas: meses-unidade divergentes;
  - TEIFa e TEIP: meses comparados, meses reproduzidos e a maior diferença, em p.p.;
  - cadastro: o texto de cada divergência;
  - conferência não aplicável: o motivo.

  A redação das legendas está na spec da Geração do relatório.
- **FR-006**: Só as seis conferências refeitas a cada execução DEVEM entrar nos resultados. Conferências feitas à mão fora do fluxo, como as registradas em "Conferências manuais (fora do fluxo)", NÃO DEVEM entrar nos resultados.
- **FR-007**: A Conferência NÃO DEVE corrigir valores, excluir registros nem escolher entre as fontes. As divergências ficam registradas, com os valores ou as diferenças das duas fontes.
- **FR-008**: A etapa DEVE gravar os arquivos listados em "Entradas e saídas", com o `resumo` do `etapa.json`.
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

  Sem nenhum mês com a janela completa, a conferência é não aplicável, com esse motivo, e a tabela mês a mês continua registrada, com as taxas recalculadas vazias.

**Cadastro (US4)**

- **FR-017**: A conferência do cadastro DEVE comparar a ficha da usina extraída pela Coleta de dados com o perfil:

  | Campo da ficha | Comparado com | Diverge quando |
  |---|---|---|
  | potência autorizada | `parametros.potencia_instalada_mw` | a diferença passa de 0,001 MW, ou o valor falta ou não é numérico |
  | estado | `usina.estado` | é diferente |
  | id ONS | `identificacao.id_ons` | é diferente |
  | CEG | uma única linha do cadastro com o CEG | há mais de uma linha; vale a primeira |

  Cada divergência DEVE ser registrada com o valor do cadastro e o do perfil (no CEG, com a quantidade de linhas). Sem divergência, a lista de divergências fica vazia.

### Key Entities

- **Resultado de conferência**: uma das seis conferências, com a aplicabilidade (ou o motivo), as bases, o período, a unidade, as quantidades comparada, coincidente e divergente, a tolerância, a meta (só nas vazões) e as tabelas de detalhe. É refeito a cada execução e lido pelas Análises, que o repassam à Geração do relatório.
- **Divergência**: o que não coincide, na unidade da conferência: período contínuo de horas (geração e disponibilidade), mês-unidade (DISPF × horas), mês não reproduzido (TEIFa e TEIP) ou campo da ficha (cadastro), sempre com os valores ou as diferenças das duas fontes.
- **Recálculo das taxas**: para cada mês publicado, os meses na janela, a TEIFa e a TEIP publicadas e recalculadas e as diferenças em p.p.
- **Resumo da etapa**: a situação das seis conferências no `etapa.json`.

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
- **SC-004**: Com o perfil de uma usina fictícia sem algum conjunto, sobre dados de teste, 100 % das conferências sem base ficam registradas como não aplicáveis, com o motivo, e as demais são feitas.
- **SC-005**: A execução da etapa não acessa a rede e não altera nenhum arquivo das etapas anteriores (mesmo SHA-256 antes e depois).
- **SC-006**: 100 % dos seis resultados trazem os campos da FR-003 e os números da FR-005, ou o motivo de não serem aplicáveis.

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

## Conferências manuais (fora do fluxo)

Conferências feitas à mão para a UHE São Domingos. Não são refeitas a cada execução nem citadas no relatório. Os arquivos de apoio das conferências com a CCEE e com o BI da ANEEL foram excluídos em 07/10/2026, com aprovação do usuário.

| Data | Fonte | Período | O que foi comparado | Resultado |
|---|---|---|---|---|
| 01/10/2026 | CCEE (amostra) | jul/2026 | geração no centro de gravidade × geração do ONS | geração no centro de gravidade = geração do ONS × fator de perda interna; confirma que o registro de 68,7 MW de 15/05/2019 é erro do ONS |
| 02/10/2026 | BI da ANEEL (exportações) | 2013 a 2025 | geração "Verificada" × geração do ONS | geração "Verificada" idêntica à do ONS; série da CCEE desde 2013 |
| 02/10/2026 | Energia Vertida Turbinável no S3 do ONS, pelo servidor de consulta aos dados do ONS | ago/2018 a set/2026 | totais mensais publicados × base de EVT local | idênticos em todos os meses de ago/2018 a ago/2026 e de 01 a 28/09/2026; o portal já tinha dados até 30/09 |

## Assumptions

- **Entradas**: o Tratamento entrega as séries na hora de início, no período da base de EVT, com um valor por hora e com as sinalizações de qualidade. Nos indicadores e nas taxas, vale a versão mais recente publicada. A Conferência não refaz nada disso.
- **Tolerâncias e meta**: 0,01 MW, 0,5 m³/s, 1 h, 0,001 p.p. e 0,001 MW acompanham o arredondamento dos valores publicados. Elas e a meta de 99 % são regras gerais, iguais para qualquer usina; o perfil não as altera.
- **Fora desta etapa**:
  - a identidade das horas por estado operativo (horas do período iguais à soma das parcelas, com tolerância de 0,1 h) é regra de consistência do Tratamento;
  - a decomposição da TEIFa e da TEIP por UG e parcela, a capacidade não sincronizada × reserva desligada, a disponibilidade declarada × DISPF por ano e o cruzamento com a programação diária ficam nas Análises, porque não conferem a mesma grandeza em duas fontes.
- **Leitura dos resultados**: a conferência diz se as fontes coincidem, não qual está certa. As divergências viram constatações, itens da conclusão e legendas nas etapas seguintes; com a meta das vazões não atingida, as Análises não publicam os cruzamentos hidrológicos.
- **Bases**: as seis conferências são as que o projeto faz hoje; nenhuma base nova entra (decisão do usuário em 07/10/2026).
- **Formato**: `conferencias.pkl` serve às etapas seguintes; os CSV são a versão para consulta, e a planilha do relatório continua sendo a versão completa e legível.
