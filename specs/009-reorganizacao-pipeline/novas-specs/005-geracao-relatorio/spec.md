# Spec da Etapa 5: Geração do relatório

**Etapa**: 5 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-08

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

Produzir o relatório de uma usina — PDF, Markdown, planilha, CSV e figuras — só a partir do que as etapas anteriores gravaram e do perfil da usina, sem calcular nada novo, numa estrutura fixa: capa com o panorama e o sumário, cada constatação uma única vez no início da sua seção, fonte e conferência abaixo de cada figura e tabela, conclusão por regras e notas metodológicas. A etapa também permite fixar a data de geração e comparar o relatório com uma versão guardada, para provar que ele não mudou.

---

## Entradas e saídas

**Comando**

```text
python -m src relatorio --usina <slug> [--data-geracao "DD/MM/AAAA HH:MM"]
```

- `--data-geracao`: fixa a data e a hora de geração mostradas no relatório e torna o PDF reproduzível byte a byte (FR-004). Sem ela, vale a data e a hora da execução.
- O comando `completo` repassa `--data-geracao` a esta etapa.
- As regras comuns a todas as etapas estão na spec da Coleta: sintaxe, `--log-level`, perfil da usina (código 4), campos do `etapa.json`, pré-requisitos e mensagens.

**Lê**

| Entrada | Onde |
|---|---|
| Resultados das Análises, com os resultados da Conferência: dados de cada tabela e figura, constatações, itens da conclusão e resultados das conferências | `data/usinas/<slug>/analises/resultados.pkl` |
| Data de obtenção de cada conjunto do ONS, registrada pela Coleta | manifestos de versões em `data/raw/` |
| Perfil da usina: nome, identificadores, parâmetros e fontes | `usinas/<slug>/perfil.toml` |

**Grava**, em `reports/<slug>/`:

| Arquivo | Conteúdo |
|---|---|
| `relatorio_analise_estatistica.pdf` | relatório em PDF, A4 paisagem |
| `relatorio_analise_estatistica.md` | o mesmo relatório em Markdown |
| `perfil_estatistico_anual.xlsx` | planilha, uma aba por tabela (FR-038) |
| `perfil_estatistico_anual.csv` | indicadores anuais (FR-039) |
| `figures/` | as figuras em PNG, até oito (FR-034) |
| `etapa.json` | manifesto da etapa; o `resumo` está na FR-006 |

**Códigos de saída**

| Código | Quando |
|---|---|
| 0 | relatório gerado |
| 1 | erro ao montar ou gravar qualquer saída, inclusive o PDF |
| 2 | opção inválida, inclusive `--data-geracao` fora do formato; nada é executado |
| 4 | perfil da usina inválido; nada é gravado |
| 5 | Análises sem resultados concluídos, ou com resultados desatualizados; nada é gravado |

**Ferramenta `comparar`** (FR-040)

```text
python -m src comparar --usina <slug> --referencia <pasta>
```

| Código | Quando |
|---|---|
| 0 | nenhuma diferença |
| 1 | erro, como pasta de referência inexistente ou arquivo ilegível |
| 2 | opção inválida, como `--referencia` ausente |
| 4 | perfil da usina inválido |
| 6 | há diferenças, listadas na saída |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar o relatório a partir dos resultados das etapas anteriores (Priority: P1)

Como fiscal da AGEMS, quero gerar o relatório de uma usina com um comando, a partir só do que as etapas anteriores gravaram. Quero também refazê-lo com a mesma data, para conferir que nada mudou.

**Why this priority**: É a entrega da fiscalização e o ponto de chegada do fluxo.

**Independent Test**: Com os resultados das Análises e da Conferência gravados:
- executar a etapa duas vezes com a mesma `--data-geracao` e comparar as saídas;
- executar a etapa sem as Análises e conferir a recusa.

**Acceptance Scenarios**:

1. **Given** as Análises concluídas para a usina, **When** a etapa é executada, **Then**:
   - `reports/<slug>/` recebe o PDF, o Markdown, a planilha, o CSV, as figuras e o `etapa.json` concluído;
   - o comando termina com código 0.
2. **Given** as Análises ausentes, com falha ou desatualizadas, **When** a etapa é executada, **Then** ela termina com código 5, não grava nada e indica o comando das Análises.
3. **Given** duas execuções sobre os mesmos resultados com a mesma `--data-geracao`, **When** as saídas são comparadas, **Then** PDF, Markdown, CSV e figuras são idênticos byte a byte, e a planilha é idêntica célula a célula.
4. **Given** uma falha ao montar o PDF, **When** a etapa é executada, **Then** ela termina com código 1, registra o erro no log e marca o `etapa.json` com falha.
5. **Given** um relatório já gerado, **When** a etapa é executada de novo, **Then** os arquivos são regravados, sem cópia `.bak`.

---

### User Story 2 - Relatório enxuto: capa, sumário e constatações nas seções (Priority: P1)

Como fiscal, quero que a primeira página traga os dados básicos da usina, os indicadores principais, a data de geração e o sumário. Quero ler cada constatação uma única vez, no início da seção que a sustenta. Assim apresento o relatório começando pelo panorama e vou direto ao ponto.

**Why this priority**: É a estrutura aprovada pelo usuário e a parte mais visível do relatório.

**Independent Test**: Gerar o relatório com todos os conjuntos e só com a base de EVT. Conferir, no PDF e no Markdown, a capa, o sumário, a ordem das seções, o lugar de cada constatação e o rodapé.

**Acceptance Scenarios**:

1. **Given** o relatório gerado, **When** a página 1 do PDF é aberta, **Then**:
   - ela traz o título, o período, a data de geração, os blocos de identificação, de cadastro (se houver) e de parâmetros, os indicadores principais e o sumário com a página de cada seção;
   - não traz texto de constatação;
   - a seção 1 começa na página 2.
2. **Given** cada constatação gerada pelas Análises, **When** o relatório é lido, **Then** ela aparece uma única vez no PDF e uma no Markdown, no início da sua seção, com o título em destaque.
3. **Given** um conjunto do ONS ausente para a usina, **When** o relatório é gerado, **Then** a seção dele não aparece no corpo nem no sumário, e as demais são numeradas sem lacunas.
4. **Given** o PDF, **When** qualquer página é lida, **Then** o rodapé tem só "Página X de Y".
5. **Given** o Markdown, **When** comparado com o PDF, **Then** tem as mesmas seções, na mesma ordem e com os mesmos títulos, o mesmo sumário, as mesmas tabelas e as figuras no corpo das seções.

---

### User Story 3 - Fonte e conferência em cada figura, tabela e aba (Priority: P1)

Como fiscal, quero que cada figura e cada tabela digam, logo abaixo, de qual conjunto do ONS vieram os dados e com que outra fonte foram conferidos, com o resultado. Quero que a planilha diga o mesmo de cada aba. Assim mostro ao agente a origem de cada número sem procurar nas notas.

**Why this priority**: É a rastreabilidade exigida pela constituição e pedida pelo usuário. Sem ela, uma figura copiada para outro documento perde a origem.

**Independent Test**: Gerar o relatório com todos os conjuntos e só com a base de EVT. Conferir, figura a figura e tabela a tabela, a legenda de fonte, e conferir a aba FONTES.

**Acceptance Scenarios**:

1. **Given** uma figura, tabela ou bloco da capa, **When** o relatório é gerado, **Then** logo abaixo aparece a legenda com o nome de cada conjunto usado, o identificador da usina nele e a data de obtenção. Exemplo (perfil da São Domingos): "Fonte dos dados: Energia Vertida Turbinável (cod_usina 153), obtido em 30/09/2026."
2. **Given** dados conferidos com outra fonte, **When** a legenda é gerada, **Then** ela traz o resultado da conferência ou a quantidade de divergências e a aba onde estão. Exemplo (perfil da São Domingos): "geração conferida com Geração por usina: 70.895 de 70.895 horas coincidentes (100,0%)".
3. **Given** dados sem outra fonte pública, como a EVT, **When** a legenda é gerada, **Then** ela diz "Sem outra fonte para conferir: …".
4. **Given** um conjunto ausente que permitiria uma conferência, **When** a legenda é gerada, **Then** ela diz que a conferência não foi feita nesta execução.
5. **Given** a planilha, **When** aberta, **Then** a última aba, FONTES, tem uma linha para cada uma das outras abas, com os conjuntos de origem e as conferências.

---

### User Story 4 - Conclusão para a fiscalização (Priority: P1)

Como fiscal, quero que o relatório termine com uma conclusão de uma página, em quatro listas curtas, com cada item remetendo à seção que o sustenta. Assim levo à fiscalização presencial o que perguntar e o que conferir.

**Why this priority**: É o fecho pedido pelo usuário para a fiscalização.

**Independent Test**: Gerar o relatório e conferir o lugar da seção, as listas, o limite de itens, os rótulos das seções e a aba CONCLUSAO.

**Acceptance Scenarios**:

1. **Given** o relatório gerado, **When** a conclusão é lida, **Then**:
   - ela está depois de "Qualidade dos dados" e antes de "Notas metodológicas e limitações", no PDF e no Markdown;
   - consta do sumário;
   - cabe numa página do PDF.
2. **Given** itens gerados pelas Análises, **When** a conclusão é montada, **Then** ela traz a frase de abertura e as listas "Pontos de atenção", "Possíveis problemas", "A confirmar com o agente" e "A verificar em campo", nesta ordem, com até cinco itens cada, terminados por "(seção N)" ou "(seções N e M)".
3. **Given** uma lista com mais de cinco itens, **When** o relatório é gerado, **Then** ficam os cinco primeiros, e a aba CONCLUSAO traz todos.
4. **Given** nenhum item gerado, **When** o relatório é gerado, **Then** a seção traz só a frase "Os dados não indicaram pontos de atenção pelos critérios das regras da conclusão."

---

### User Story 5 - Figuras padronizadas (Priority: P2)

Como fiscal, quero figuras legíveis, no mesmo padrão visual, que mostrem as grandezas citadas nas constatações. As figuras de série longa devem ter o mesmo tamanho e ocupar a largura da página.

**Why this priority**: As figuras mostram padrões que as tabelas não mostram, mas dependem dos resultados das Análises.

**Independent Test**: Gerar as figuras com todos os conjuntos e conferir os nomes, a resolução, o padrão visual, os tamanhos e o desenho no PDF.

**Acceptance Scenarios**:

1. **Given** todos os conjuntos, **When** a etapa é executada, **Then** as oito figuras são gravadas com os nomes da FR-034, a 300 DPI, todas com seaborn e o mesmo padrão visual.
2. **Given** as figuras 01, 02, 05 e 06, **When** comparadas, **Then** têm o mesmo tamanho e, no PDF, ocupam a largura útil da página.
3. **Given** um ano parcial, **When** aparece numa figura, **Then** vem marcado com asterisco e com a nota "* ano parcial".
4. **Given** um conjunto ausente, **When** a etapa é executada, **Then** a figura que depende dele não é gerada.

---

### User Story 6 - Planilha completa e CSV (Priority: P2)

Como fiscal, quero uma planilha com todas as tabelas calculadas, em abas de nome fixo, e um CSV com os indicadores anuais. Assim confiro qualquer número do relatório ou entrego os dados a outro técnico.

**Why this priority**: É a versão completa dos resultados, mas o relatório se lê sem ela.

**Independent Test**: Gerar a planilha e conferir as abas, a ordem, o conteúdo da CONCLUSAO e da FONTES e os números citados no relatório.

**Acceptance Scenarios**:

1. **Given** os resultados, **When** a planilha é gravada, **Then** tem as abas da FR-038, nessa ordem, com CONCLUSAO logo depois de CONSTATACOES e FONTES por último.
2. **Given** um conjunto ausente ou uma tabela opcional sem linhas, **When** a planilha é gravada, **Then** a aba correspondente não existe e não aparece na FONTES.
3. **Given** um número citado numa tabela ou legenda do relatório, **When** procurado na planilha, **Then** está na aba correspondente, com o mesmo valor.
4. **Given** o perfil da São Domingos e os dados locais, **When** a planilha é gravada, **Then** tem 58 abas, sem DISP_DIVERGENCIAS e GER_DIVERGENCIAS, que não têm linhas (perfil da São Domingos).

---

### User Story 7 - O mesmo relatório para outra usina (Priority: P2)

Como fiscal, quero gerar o relatório de outra usina hidrelétrica só com o perfil dela, com a mesma estrutura e sem nenhuma menção à São Domingos.

**Why this priority**: Amplia o uso do projeto sem mudar o relatório da São Domingos.

**Independent Test**: Gerar o relatório de uma usina fictícia de três unidades, sobre dados de teste, com e sem alguns conjuntos, e procurar nele o nome, os identificadores e os parâmetros da São Domingos.

**Acceptance Scenarios**:

1. **Given** o perfil de outra usina, **When** o relatório é gerado, **Then** título, cabeçalho, capa, notas, legendas, rótulos das figuras e tabela de parâmetros trazem o nome, os identificadores, os parâmetros e as fontes dela.
2. **Given** uma usina de três unidades geradoras, **When** o relatório é gerado, **Then** os textos que dependem do número de unidades usam esse número, como "3 × …" e "cabia nas três".
3. **Given** uma usina sem programação diária, sem dados hidrológicos ou sem indicadores por unidade geradora, **When** o relatório é gerado, **Then**:
   - as seções, tabelas, figuras, abas e legendas que dependem desses conjuntos ficam de fora;
   - as conferências que dependem deles aparecem nas legendas como não feitas.

---

### User Story 8 - Conferir que o relatório não mudou (Priority: P2)

Como fiscal, quero comparar o relatório atual de uma usina com uma versão guardada e ver a lista de diferenças. Assim provo que uma mudança no código não alterou o relatório aprovado.

**Why this priority**: É a prova de não regressão da reorganização e de qualquer mudança futura.

**Independent Test**: Comparar duas gerações com a mesma data, que não devem ter diferença. Depois, alterar uma célula da planilha e retirar uma figura de uma das pastas.

**Acceptance Scenarios**:

1. **Given** o relatório gerado com os mesmos dados e a mesma `--data-geracao` da referência, **When** `comparar` é executado, **Then** não lista nenhuma diferença e termina com código 0.
2. **Given** uma célula diferente na planilha, **When** `comparar` é executado, **Then** lista a aba e a célula e termina com código 6.
3. **Given** uma figura presente só numa das pastas, **When** `comparar` é executado, **Then** lista o arquivo como diferença e termina com código 6.
4. **Given** a planilha regravada com os mesmos dados, **When** comparada, **Then** não há diferença, porque a planilha é comparada célula a célula.

---

### Edge Cases

- **Análises ausentes, com falha ou desatualizadas**: código 5, sem gravar nada (FR-002).
- **Só a base de EVT**:
  - 12 seções, numeradas de 1 a 12;
  - capa sem o bloco do cadastro e com quatro indicadores principais;
  - sem as figuras 06 a 08 e sem as abas dos conjuntos ausentes;
  - as legendas dizem que as conferências com os conjuntos ausentes não foram feitas.
- **Conferência das vazões abaixo da meta** (cruzamentos hidrológicos não publicados):
  - a seção da hidrologia traz só a constatação e as notas;
  - as figuras 07 e 08 não são geradas, e nenhuma legenda fica sem a sua figura ou tabela.
- **Tabela sem linhas**: não aparece, exceto as duas que mostram uma frase no lugar (FR-008).
- **Constatação fora do mapa da FR-010, ou com a seção ausente**: vai para a seção 1, com aviso no log; nenhuma constatação desaparece.
- **Várias constatações na mesma seção**: seguem a ordem em que as Análises as geraram.
- **Conferência da geração sem divergência**: não há constatação; o texto da conferência abre a seção.
- **Conclusão**:
  - lista sem itens não aparece;
  - seção de origem ausente não entra no rótulo "(seção N)";
  - sem nenhum item, a seção traz só a frase de "nenhum ponto de atenção" (FR-030).
- **Data de obtenção sem registro na Coleta**: a legenda diz "data de obtenção não registrada".
- **Figura, tabela ou aba fora do mapa de fontes**: a legenda diz "origem não mapeada", com aviso no log.
- **Figura não disponível**: o PDF mostra "Figura não disponível (…)." no lugar dela, sem falhar; o Markdown a omite.
- **Auditoria da varredura ou manifesto da Coleta ausentes**: o quadro da cobertura sai sem as linhas "Arquivos lidos" e "Versão dos arquivos".
- **`--data-geracao` em formato inválido**: o comando recusa antes de gravar qualquer arquivo.
- **Nova execução**: as saídas são regravadas sem `.bak`. Para guardar uma versão aprovada, usa-se a cópia de segurança do projeto antes de mudar o código.

---

## Requirements *(mandatory)*

### Functional Requirements

**Entradas, saídas e execução (US1)**

- **FR-001**: A etapa DEVE gerar o relatório só a partir de:
  - resultados das Análises da usina, que trazem os resultados da Conferência;
  - datas de obtenção registradas pela Coleta;
  - perfil da usina.

  Ela NÃO DEVE recalcular indicadores, eventos, conferências, constatações ou itens da conclusão. Também NÃO DEVE ler os arquivos de dados brutos ou tratados — dos brutos, só os manifestos de versões, para as datas de obtenção — nem acessar o portal do ONS.
- **FR-002**: Antes de gravar, a etapa DEVE conferir que as Análises da usina estão concluídas e não desatualizadas. Se não estiverem, DEVE sair com código 5, sem gravar nada, indicando o comando das Análises.
- **FR-003**: A etapa DEVE gravar em `reports/<slug>/` os arquivos da tabela "Grava", com esses nomes, e as figuras em `reports/<slug>/figures/`. Os arquivos de uma execução anterior DEVEM ser regravados sem cópia `.bak`; as versões aprovadas ficam guardadas nas cópias de segurança do projeto. As saídas DEVEM ser gravadas primeiro em arquivos temporários e só substituir as da execução anterior depois de todas geradas e conferidas; se algo falhar, as da execução anterior DEVEM ficar como estavam.
- **FR-004**: A opção `--data-geracao "DD/MM/AAAA HH:MM"` DEVE:
  - fixar a data e a hora de geração mostradas na capa do PDF e no cabeçalho do Markdown;
  - gerar o PDF sem data de criação nem identificador variáveis, para que as mesmas entradas com a mesma data produzam o mesmo arquivo.

  Sem a opção, vale a data e a hora da execução. Uma data em formato inválido DEVE ser recusada antes de qualquer gravação.
- **FR-005**: Com as mesmas entradas e a mesma `--data-geracao`, a etapa DEVE produzir PDF, Markdown, CSV e figuras idênticos byte a byte e a planilha idêntica célula a célula.
- **FR-006**: A etapa DEVE sair com código 0 quando todas as saídas forem gravadas, e com código 1 quando qualquer saída falhar, inclusive o PDF, com o erro registrado no log. O `resumo` do `etapa.json` DEVE trazer:
  - a data de geração;
  - a quantidade de seções;
  - a quantidade de páginas do PDF;
  - a quantidade de figuras;
  - a quantidade de abas da planilha.

**Estrutura do relatório (US2)**

- **FR-007**: O relatório DEVE ter as seções abaixo, nesta ordem, no PDF e no Markdown.
  - Seção cuja condição não é atendida fica fora do corpo e do sumário.
  - As seções presentes são numeradas 1, 2, 3… sem lacunas: são 17 com todos os conjuntos e 12 só com a base de EVT.

  | Seção | Presente | Conteúdo, nesta ordem |
  |---|---|---|
  | Fonte e cobertura dos dados | sempre | quadro da cobertura: conjunto de EVT; critério de extração; arquivos lidos e versão dos arquivos, quando a Coleta os registrou; período; registros e horas ausentes; anos parciais |
  | Indicadores anuais | sempre | indicadores por ano |
  | Disponibilidade e geração por ano | sempre | figura 04; períodos de indisponibilidade total de pelo menos 24 h |
  | Indicadores oficiais do ONS por unidade geradora | com os indicadores por unidade geradora | disponibilidade por ano (declarada × DISPF); TEIFa e TEIP mais recentes por unidade e parcela, com o resumo das taxas frente às referências; indicadores anuais por unidade; horas por estado operativo; meses com DISPF e horas divergentes |
  | Série temporal de disponibilidade, geração e EVT | sempre | figura 01 |
  | Energia vertida turbinável mensal | sempre | figura 02 |
  | Perfil horário da geração e da EVT | sempre | figura 03; EVT e geração nas janelas diurna e noturna, por ano |
  | EVT por nível de geração e eventos de usina parada | sempre | horas com EVT por nível de geração; maiores eventos de usina parada com EVT |
  | Operação verificada e programação diária do ONS | com a programação diária | horas paradas com EVT, por mês e programação; as mesmas horas por hora do dia; maiores eventos de parada com programação acima de 5 MW; dias sem arquivo no portal |
  | Disponibilidade operacional e sincronizada (ONS) | com a disponibilidade por usina | disponibilidade média por ano; figura 06; horas paradas por sincronização, EVT e programação; maiores períodos de divergência; notas |
  | Afluência, vertimento e nível do reservatório (ONS) | com os dados hidrológicos | horas e EVT por faixa de afluência, por ano; figura 07; afluência, vazões, nível e volume útil por ano; vazões e nível por hora do dia, de 3 em 3 h; figura 08; notas |
  | Horas com geração zero por mês | sempre | horas por ano e mês, com o total e a divisão entre disponibilidade zero e usina disponível |
  | Vazões defluentes por ano | sempre | figura 05 |
  | Conferência da geração com a série oficial (ONS) | com a geração por usina | texto da conferência, quando não há a constatação dela; energia anual nas duas fontes |
  | Qualidade dos dados | sempre | regras de validação R1 a R9; registros sinalizados por regra; extremos do período sem os registros sinalizados |
  | Conclusão | sempre | FR-029 a FR-031 |
  | Notas metodológicas e limitações | sempre | notas (FR-020); parâmetros utilizados (FR-022) |

- **FR-008**: As tabelas DEVEM seguir estas regras:
  - cada uma vem com o subtítulo (exceto o quadro da cobertura e as tabelas dos indicadores anuais, da EVT e da geração nas janelas diurna e noturna, das horas com geração zero e da energia anual nas duas fontes, apresentadas pelo título da seção ou pela legenda da figura), a nota que explica colunas e símbolos (quando houver) e a legenda de fonte;
  - tabela sem linhas não aparece, exceto duas, que mantêm o subtítulo e mostram uma frase no lugar: os períodos de indisponibilidade total ("Nenhum período com essa duração.") e os eventos de parada com EVT ("Nenhum evento.");
  - anos parciais aparecem com asterisco;
  - listas longas aparecem resumidas, e a lista completa fica na planilha:
    - períodos de indisponibilidade total de pelo menos 24 h;
    - os 15 maiores eventos de parada com EVT, pela EVT;
    - os 15 maiores eventos de parada com programação acima de 5 MW, pela duração;
    - os 15 maiores períodos de divergência de disponibilidade, pelas horas, em ordem cronológica;
  - tabelas e figuras de cruzamento hidrológico só aparecem quando a conferência das vazões atingiu a meta.
- **FR-009**: Cada constatação das Análises DEVE aparecer exatamente uma vez no PDF e uma no Markdown:
  - no início da seção indicada na FR-010, logo depois do título e antes das tabelas e figuras;
  - no formato "**Título.** texto";
  - na ordem em que as Análises as geraram, quando houver mais de uma na seção.

  Constatação fora do mapa, ou cuja seção não está presente, DEVE ir para a seção 1, com aviso no log. O relatório NÃO DEVE ter lista de constatações no início. A capa e o sumário NÃO DEVEM ter texto de constatação.
- **FR-010**: Cada constatação DEVE ser apresentada nesta seção:

  | Constatação | Seção |
  |---|---|
  | Cobertura dos dados; Cadastro da usina no ONS | Fonte e cobertura dos dados |
  | Disponibilidade | Indicadores anuais |
  | Indisponibilidades; Geração e garantia física | Disponibilidade e geração por ano |
  | Indicadores oficiais de disponibilidade (ONS); Estados operativos das unidades geradoras (ONS) | Indicadores oficiais do ONS por unidade geradora |
  | Energia vertida turbinável; Distribuição ao longo do ano; Mudança de classificação do vertimento pelo ONS | Energia vertida turbinável mensal |
  | Concentração diurna | Perfil horário da geração e da EVT |
  | EVT e nível de geração; EVT com a usina parada | EVT por nível de geração e eventos de usina parada |
  | Programação diária do ONS | Operação verificada e programação diária do ONS |
  | Disponibilidade sincronizada | Disponibilidade operacional e sincronizada (ONS) |
  | Afluência e vertimento | Afluência, vertimento e nível do reservatório (ONS) |
  | Horas com geração zero | Horas com geração zero por mês |
  | Conferência da geração | Conferência da geração com a série oficial (ONS) |
  | Qualidade dos dados | Qualidade dos dados |

**Capa (US2)**

- **FR-011**: A capa DEVE ter, nesta ordem:
  - o título "<nome da usina> — energia vertida turbinável e desempenho operacional";
  - o subtítulo "Análise dos dados abertos do ONS · <início> a <fim> · <N> registros horários · Gerado em dd/mm/aaaa hh:mm";
  - os blocos "Identificação nos dados do ONS", "Cadastro no ONS" (FR-012) e "Parâmetros técnicos da usina", lado a lado no PDF, cada um com a sua legenda de fonte;
  - os indicadores principais (FR-013);
  - o "Sumário", com o número e o título de cada seção presente, na ordem do relatório: no PDF, em duas colunas, com a página em que cada seção começa; no Markdown, em lista, com link para cada seção.

  O nome da usina é o `usina.nome` do perfil. O bloco de identificação traz o código da usina nos dados do ONS, o reservatório, o rio e a bacia, o subsistema e cada agente com o seu período, como constam dos dados. O bloco de parâmetros traz, do perfil (`parametros`):
  - a potência instalada, com as unidades × potência unitária;
  - o tipo de turbina;
  - o engolimento nominal, com as unidades × engolimento por unidade e o total;
  - a garantia física, com o órgão que a define: o texto de `parametros.fontes.garantia_fisica` até a primeira vírgula;
  - o IP e o TEIF de referência, com a disponibilidade de referência.
- **FR-012**: Com o cadastro do ONS carregado, a capa DEVE trazer o bloco "Cadastro no ONS", entre a identificação e os parâmetros, com:
  - usina, CEG e id ONS;
  - modalidade de operação;
  - centro de operação;
  - ponto de conexão;
  - potência autorizada;
  - estado e situação na ANEEL;
  - quantidade de homônimos excluídos pelo CEG.

  O bloco NÃO DEVE trazer a data da consulta, que fica na legenda de fonte e na aba CAD_FICHA. Sem o cadastro, a capa fica com os outros dois blocos.
- **FR-013**: Os indicadores principais DEVEM ser estes, nesta ordem, cada um com um complemento curto:
  - disponibilidade média declarada, em % da potência instalada, com a referência da garantia física;
  - disponibilidade apurada pelo ONS (DISPF), média das unidades, com a TEIFa e a TEIP mais recentes e o mês; só com os indicadores por unidade geradora;
  - fator de capacidade, com a geração média e a razão com a garantia física;
  - energia vertida turbinável, em GWh, com a parcela em geração + EVT e a % das horas com EVT;
  - EVT com a usina parada, em GWh, com a % da EVT e as horas.

  Abaixo deles vêm uma nota e a legenda de fonte. A nota depende dos indicadores por unidade geradora:
  - com eles, distingue os indicadores calculados no relatório dos apurados pelo ONS;
  - sem eles, diz que os indicadores são aproximações que não substituem os índices regulatórios.
- **FR-014**: No PDF, a capa DEVE ocupar só a página 1, e a primeira seção DEVE começar na página 2.

**PDF (US2)**

- **FR-015**: O PDF DEVE ser A4 paisagem, com:
  - cabeçalho a partir da página 2: "<nome da usina> — energia vertida turbinável (dados ONS) · <início> a <fim>";
  - rodapé só com "Página X de Y", sem frase de fontes nem data;
  - título, assunto e autor do documento gerados do nome da usina (`usina.nome`) e do período;
  - fonte tipográfica que exibe ≤, ≥ e −.
- **FR-016**: A paginação do PDF DEVE seguir estas regras:
  - figura sempre junta das suas legendas e com no máximo 285 pt de altura; as padronizadas (FR-036) ficam fora desse limite;
  - tabela de até 12 linhas inteira numa página, com o subtítulo, a nota e a legenda;
  - tabela mais longa começa na página corrente se couberem o subtítulo e 6 linhas, e continua na seguinte com o cabeçalho repetido;
  - título da seção e constatações sempre juntos;
  - figura ausente substituída pelo aviso "Figura não disponível (…).", sem falhar.

**Markdown (US2)**

- **FR-017**: O Markdown DEVE ter a mesma estrutura do PDF:
  - cabeçalho com o título "<nome da usina> — energia vertida turbinável e desempenho operacional (dados ONS)", o período com a quantidade de registros e "**Gerado em**: dd/mm/aaaa hh:mm", sem linha de fontes;
  - em seguida, os blocos da capa e os indicadores principais em tabelas, com a nota e as legendas, e o sumário;
  - as mesmas seções, na mesma ordem, com os mesmos títulos e números ("## N. Título");
  - as mesmas tabelas do PDF, com as mesmas colunas;
  - cada figura no corpo da sua seção, com a imagem, a legenda descritiva e a legenda de fonte, sem lista de figuras no fim.

**Textos, notas e parâmetros (US2 e US7)**

- **FR-018**: Todo número, data e frase das tabelas, legendas, notas e capa DEVE ser gerado dos resultados, do perfil e das regras gerais; nenhum resultado é escrito à mão. Os números DEVEM seguir o padrão brasileiro:
  - milhar com "." e decimal com ",";
  - "–" para valor ausente;
  - diferenças em p.p. com sinal ("+" ou "−");
  - datas dd/mm/aaaa, horas "dd/mm/aaaa HHh" e meses "mmm/aaaa";
  - listas no formato "a, b e c".
- **FR-019**: Os textos do relatório NÃO DEVEM ter nome, identificador ou valor de usina que não venha do perfil ou dos dados. A regra vale para título, cabeçalho, metadados do PDF, capa, notas, legendas, rótulos das figuras e tabela de parâmetros. Os textos que dependem do número de unidades geradoras usam o número do perfil, escrito por extenso nas frases ("duas", para 2).
- **FR-020**: As notas metodológicas DEVEM trazer definições e limitações, sem valores de resultado, em itens:
  - fonte da base de EVT, base horária, convenção da hora e possibilidade de revisão pelo ONS;
  - horário legal e hora ausente no início do horário de verão;
  - disponibilidade relativa, diferença para o FID regulatório e disponibilidade de referência, (1 − IP) × (1 − TEIF);
  - garantia física usada e origem do IP e do TEIF de referência, com a ressalva de que podem ter sido revistos;
  - fator de capacidade e caráter indicativo da comparação com a garantia física;
  - cálculo da EVT pelo ONS e ausência de informação de causa;
  - definições e limiares: usina parada, plena carga, vertimento mínimo, janelas diurna e noturna;
  - tratamento dos registros sinalizados (R6 a R9) e faixa de produtividade aceita;
  - anos parciais, quando houver;
  - as notas de cada conjunto opcional carregado:
    - indicadores por unidade geradora: conjuntos e identificação, definições do DISPF, siglas e identidade das horas por estado operativo, fórmulas da TEIFa e da TEIP, ausência de causa e de eventos individuais;
    - programação diária: conjunto, conversão dos patamares, classificação das horas e as ressalvas de que é o planejamento do dia, sem reprogramações, e de que não informa o motivo para usinas hidráulicas;
    - disponibilidade, dados hidrológicos, geração e cadastro: conjunto com o endereço, identificador e conferência, período e data de obtenção; nos dados hidrológicos, "não consistidos pelo ONS"; no cadastro, "sem série histórica";
  - a conclusão (FR-033).
- **FR-021**: As notas das seções de disponibilidade e de hidrologia DEVEM trazer só ressalvas e definições da seção. Conjunto, identificador e data de obtenção NÃO DEVEM ser repetidos ali, porque estão nas legendas.
  - **Disponibilidade**:
    - a operacional é a mesma informação da disponibilidade declarada;
    - definições de usina parada, unidade sincronizada, capacidade não sincronizada e reserva desligada, que são comparadas sem meta;
    - horas com valores inconsistentes excluídas, quando houver;
    - meses sem a usina e horas ausentes, sem interpolação.
  - **Hidrologia**:
    - dados informados pelos agentes e não consistidos pelo ONS; sinalizações excluídas só no campo afetado; campo vazio não é zero;
    - conversão da hora de fim para a de início, com o resultado do alinhamento;
    - definição das faixas de afluência;
    - ressalva sobre o volume útil;
    - sinalizações por regra (H1 a H4) e por ano, quando houver;
    - picos isolados de afluência, quando a maior passa do dobro do engolimento máximo;
    - meses sem a usina e horas ausentes, sem interpolação.

  A nota de sinalizações cita a "coluna qualidade da série horária tratada", sem caminho de arquivo. A ressalva de que o cadastro não tem série histórica fica só nas notas metodológicas.
- **FR-022**: A tabela "Parâmetros utilizados", no fim das notas, e a aba PARAMETROS DEVEM listar, com valor, unidade e origem:
  - os parâmetros técnicos do perfil, cada um com a fonte registrada no perfil (`parametros.fontes`);
  - as grandezas derivadas deles, com a fórmula: engolimento máximo, disponibilidade de referência e produtividade nominal;
  - os limiares de análise e de validação, com a origem "Parâmetro de análise", sem caminho de arquivo, e, quando houver, a base do limiar (por exemplo, "Parâmetro de análise: 90% da potência instalada");
  - cada conjunto do ONS carregado, com o endereço; o identificador da usina na linha da programação diária e na de cada base complementar e, para os quatro conjuntos de indicadores, numa linha de identificação própria, com o CEG e o id ONS; nas bases complementares, também o período (no cadastro, "cadastro sem série histórica") e a data de obtenção. A linha da EVT não traz o identificador, que está no critério de extração do quadro da cobertura.

  As linhas dos conjuntos opcionais só aparecem com o conjunto carregado.

**Fonte e conferência (US3)**

- **FR-023**: Cada figura, tabela e bloco da capa DEVE ter, logo abaixo, uma legenda de fonte, no PDF e no Markdown. A legenda fica no texto, fora da imagem; na figura, vem depois da legenda descritiva.
- **FR-024**: A legenda DEVE seguir o formato:

  ```text
  Fonte dos dados: <conjunto> (<identificador>), obtido em <dd/mm/aaaa>; <conjunto> (…). Conferência: <resultado>; <resultado>. Sem outra fonte para conferir: <dados>.
  ```

  - valores calculados no relatório (taxas recalculadas, classificações, faixas, indicadores) começam com "Calculado neste relatório a partir de:" no lugar de "Fonte dos dados:";
  - os parâmetros do perfil aparecem como "parâmetros do projeto (origem na tabela de parâmetros)", e não como conjunto do ONS;
  - sem data registrada, aparece "data de obtenção não registrada";
  - "Conferência" e "Sem outra fonte para conferir" só aparecem quando se aplicam.
- **FR-025**: Cada conjunto citado DEVE ter o nome e o identificador abaixo, com os valores do perfil. A data de obtenção é a mais recente registrada pela Coleta para o conjunto.

  | Conjunto | Identificador na legenda |
  |---|---|
  | Energia Vertida Turbinável | `cod_usina <identificacao.cod_usina>` |
  | Indicadores de disponibilidade por unidade geradora, base mensal | `CEG <identificacao.ceg>` |
  | Indicadores de disponibilidade por unidade geradora, base anual | `CEG <identificacao.ceg>` |
  | Taxas TEIFa e TEIP | `CEG <identificacao.ceg>` |
  | Parâmetros das taxas TEIFa e TEIP | `CEG <identificacao.ceg>` |
  | Programação diária | `<identificacao.cod_programacao>` |
  | Disponibilidade por usina | `id ONS <identificacao.id_ons>` |
  | Dados hidrológicos horários | `cod_usina <identificacao.cod_usina>, reservatório <identificacao.id_reservatorio>` |
  | Geração por usina | `id ONS <identificacao.id_ons>` |
  | Modalidade das usinas | `CEG <identificacao.ceg>` |

- **FR-026**: As legendas DEVEM citar só as seis conferências refeitas pela Conferência a cada execução, com o resultado que ela gravou:

  | Conferência | Texto na legenda |
  |---|---|
  | geração × Geração por usina | "geração conferida com Geração por usina: <c> de <n> horas coincidentes (<p>%)"; com divergências, a quantidade e a aba GER_DIVERGENCIAS; com horas só numa das fontes, a quantidade |
  | disponibilidade declarada × Disponibilidade por usina | "disponibilidade declarada conferida com Disponibilidade por usina (operacional): …", como a anterior, com a aba DISP_DIVERGENCIAS |
  | vazões × Dados hidrológicos horários | "vazões turbinada e vertida conferidas com Dados hidrológicos horários: <c> de <n> horas coincidentes (<p>%)"; abaixo da meta, ", abaixo da meta de 99%" |
  | TEIFa e TEIP recalculadas × publicadas | "TEIFa e TEIP recalculadas conferidas com as publicadas em Taxas TEIFa e TEIP: <m> de <n> meses reproduzidos (diferença máxima de <x> p.p.)" |
  | DISPF × horas por estado operativo | "DISPF conferido com as horas por estado operativo (Parâmetros das taxas TEIFa e TEIP): <n> divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS", ou "sem divergência" |
  | ficha do cadastro × perfil | "potência autorizada e estado conferidos com os parâmetros do projeto: sem divergência", ou as divergências |

  Sem o conjunto que permite a conferência, a legenda DEVE dizer "<dado>: conferência com <conjunto> não feita nesta execução". Conferências manuais com outras instituições NÃO DEVEM aparecer.
- **FR-027**: Um mapa único DEVE dizer, para cada figura, tabela, bloco e aba:
  - os conjuntos de origem;
  - as conferências;
  - os dados sem outra fonte;
  - se o valor é calculado no relatório.

  O PDF, o Markdown e a planilha DEVEM usar esse mesmo mapa. Cada legenda DEVE citar exatamente os conjuntos carregados que alimentam a figura ou tabela. Os dados sem outra fonte pública conferida pelo fluxo são a EVT, a disponibilidade sincronizada, a afluência, os níveis e o volume útil do reservatório e a programação diária. Figura, tabela ou aba fora do mapa DEVE gerar "origem não mapeada", com aviso no log.
- **FR-028**: A aba FONTES DEVE ser a última da planilha. Ela tem uma linha para cada outra aba, na ordem da planilha, com as colunas:
  - `aba`;
  - `conjuntos_origem`;
  - `conferencias`, ou "—";
  - `sem_outra_fonte`, ou "—";
  - `calculado_no_relatorio`, com "sim" ou "não".

  Casos especiais:
  - CONSTATACOES e CONCLUSAO: todos os conjuntos carregados e todas as conferências aplicáveis, como cálculo do relatório;
  - PARAMETROS: os parâmetros do projeto e os conjuntos carregados;
  - DICIONARIOS: os dez conjuntos.

**Conclusão (US4)**

- **FR-029**: A seção "Conclusão" DEVE estar sempre presente, depois de "Qualidade dos dados" e antes de "Notas metodológicas e limitações", no PDF, no Markdown e no sumário.
- **FR-030**: A conclusão DEVE trazer:
  - a frase de abertura "Indícios a confirmar, gerados pelas regras descritas nas notas metodológicas a partir dos resultados das seções indicadas; não afirmam causa nem avaliam o desempenho da usina.";
  - as listas "Pontos de atenção", "Possíveis problemas", "A confirmar com o agente" e "A verificar em campo", nesta ordem, cada uma com subtítulo e no máximo cinco itens, os primeiros na ordem das Análises;
  - em cada item, o texto gerado pelas Análises, seguido do rótulo das seções de origem presentes ("(seção N)", "(seções N e M)" ou "(seções N, M e P)") e de ponto final.

  Lista sem itens não aparece. Sem nenhum item, a seção traz só a frase "Os dados não indicaram pontos de atenção pelos critérios das regras da conclusão."
- **FR-031**: No PDF, a conclusão DEVE caber numa página. A frase de abertura e as listas ficam juntas, e as notas metodológicas começam, no máximo, na página seguinte à do título da conclusão.
- **FR-032**: A aba CONCLUSAO, logo depois da CONSTATACOES, DEVE trazer todos os itens gerados, inclusive os que passam de cinco. As colunas são:
  - `lista`;
  - `ordem`;
  - `regra`;
  - `texto`;
  - `secoes`: número e título das seções de origem presentes, separados por "; ".
- **FR-033**: As notas metodológicas DEVEM ter um item, gerado das regras gerais, que:
  - descreve as regras C1 a C11 e os limiares da conclusão;
  - informa que o relatório mostra até cinco itens por lista e que todos estão na aba CONCLUSAO.

**Figuras (US5)**

- **FR-034**: A etapa DEVE gerar estas figuras, com estes nomes:

  | Arquivo | Mostra | Gerada |
  |---|---|---|
  | `01_serie_temporal_disponibilidade_geracao_evt.png` | médias diárias de disponibilidade declarada, geração e EVT (área); faixas nos períodos de indisponibilidade total de pelo menos 24 h; linhas da potência instalada e da garantia física | sempre |
  | `02_evt_mensal.png` | EVT mensal em barras empilhadas, separando as horas de vertimento mínimo das demais; marco no mês da mudança de classificação do vertimento, se houver | sempre |
  | `03_perfil_horario_geracao_evt.png` | mapas ano × hora do dia da geração média e da EVT média | sempre |
  | `04_disponibilidade_geracao_anual.png` | barras por ano da disponibilidade média declarada e do fator de capacidade, em % da potência instalada; linhas da disponibilidade de referência e da garantia física | sempre |
  | `05_vazoes_defluentes_anuais.png` | vazões médias anuais empilhadas (turbinada, vertida turbinável e vertida não turbinável); linha do engolimento máximo | sempre |
  | `06_disponibilidade_operacional_sincronizada_mensal.png` | médias mensais das disponibilidades operacional e sincronizada e da geração; linha da potência instalada | com a disponibilidade por usina |
  | `07_evt_por_faixa_de_afluencia.png` | horas com EVT por faixa de afluência, por ano, empilhadas, com o total no topo | com os cruzamentos hidrológicos publicados |
  | `08_perfil_horario_nivel_vazoes.png` | vazões afluente, turbinada e vertida e nível de montante médios por hora do dia, nos dias com parada com EVT e nos demais; faixa da janela diurna | com os cruzamentos hidrológicos publicados |

- **FR-035**: Todas as figuras DEVEM ser produzidas com seaborn, com tema, paleta, tipografia e resolução definidos num único lugar:
  - 300 DPI;
  - cores fixas por grandeza, de uma paleta validada para acessibilidade: geração em azul, EVT em laranja, disponibilidade em verde, contexto em cinza, disponibilidade sincronizada em amarelo, afluência em violeta e faixas de afluência em tons de laranja;
  - títulos à esquerda, grade leve, legenda e rótulos das linhas de referência fora da área dos dados;
  - números no padrão brasileiro, e anos parciais com asterisco e a nota "* ano parcial".

  Linhas de referência, faixas e anotações são desenhadas sobre os mesmos eixos.
- **FR-036**: As figuras 01, 02, 05 e 06 DEVEM ter o mesmo tamanho de imagem. No PDF, elas DEVEM ocupar a largura útil da página, fora do limite de altura da FR-016.
- **FR-037**: Cada figura DEVE ter, abaixo dela, uma legenda descritiva, igual no PDF e no Markdown, seguida da legenda de fonte. A legenda descritiva é gerada dos resultados e do perfil e diz o que mostra cada cor, linha e faixa, com os valores de referência.

**Planilha e CSV (US6)**

- **FR-038**: A planilha DEVE ter uma aba por tabela, com o cabeçalho fixo, nesta ordem:

  | Grupo | Abas | Presentes |
  |---|---|---|
  | Constatações e conclusão | CONSTATACOES (tema e texto, na ordem das Análises), CONCLUSAO (FR-032) | sempre |
  | Base de EVT | INDICADORES_ANUAIS, INDICADORES_GLOBAIS, COBERTURA_POR_ANO, AGENTES, EVT_MENSAL, EVT_MES_DO_ANO, EVT_POR_FAIXA_GERACAO, PERFIL_HORARIO_GERACAO, PERFIL_HORARIO_EVT, EVENTOS_PARADA_COM_EVT, HORAS_GERACAO_ZERO_MES, EVENTOS_INDISP_TOTAL, ANOMALIAS, RESUMO_ANOMALIAS, VALIDACAO_REGRAS, EXTREMOS, PERFIL_ESTATISTICO_ANUAL, PARAMETROS | sempre |
  | Indicadores por unidade geradora | ONS_DISP_ANUAL_USINA, ONS_UG_ANUAL, ONS_HORAS_UG_ANUAL, ONS_HORAS_UG_MENSAL, ONS_TEIFA_TEIP, ONS_DECOMPOSICAO_TAXAS, ONS_DIVERGENCIAS | cada uma, se tiver linhas |
  | Programação diária | PROG_RESUMO_MENSAL, PROG_EVENTOS_DESVIO, PROG_HORA_DO_DIA, PROG_DIAS_AUSENTES, PROG_AUDITORIA_ARQUIVOS, PROG_HORAS_CLASSIFICADAS | cada uma, se tiver linhas |
  | Disponibilidade por usina | DISP_CONFERENCIA, DISP_DIVERGENCIAS, DISP_CLASSES_PARADA, DISP_HORAS_PARADAS, DISP_MENSAL, DISP_ANUAL, DISP_AUSENCIAS, DISP_AUDITORIA | cada uma, se tiver linhas |
  | Dados hidrológicos | HID_ALINHAMENTO, HID_FAIXAS_AFLUENCIA, HID_FAIXAS_ANUAL, HID_HORAS_EVT, HID_MENSAL, HID_ANUAL, HID_PERFIL_HORA_DO_DIA, HID_AUSENCIAS, HID_AUDITORIA | cada uma, se tiver linhas |
  | Geração por usina | GER_CONFERENCIA, GER_MENSAL, GER_ANUAL, GER_DIVERGENCIAS, GER_AUSENCIAS, GER_AUDITORIA | cada uma, se tiver linhas |
  | Cadastro | CAD_FICHA; CAD_AUDITORIA | com o cadastro; a auditoria, se tiver linhas |
  | Dicionários de dados | DICIONARIOS | com o registro dos dicionários |
  | Fontes | FONTES (FR-028) | sempre, por último |

  As abas de auditoria DEVEM manter estas colunas, nesta ordem, mesmo que as auditorias gravadas pela Coleta e pelo Tratamento tragam outras:
  - PROG_AUDITORIA_ARQUIVOS: `arquivo`, `dia`, `linhas_lidas`, `linhas_usina`, `linhas_codigo_sem_conferencia`, `patamares`, `data_interna_confere`, `status`;
  - DISP_AUDITORIA, HID_AUDITORIA e GER_AUDITORIA: `arquivo`, `formato`, `periodo`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia`, `horas_usina`, `valores_invalidos`, `duplicatas_conflitantes`, `recursos_duplicados_catalogo`, `status`, `mensagem`;
  - CAD_AUDITORIA: `arquivo`, `formato`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia`, `status`, `mensagem`.

- **FR-039**: O CSV DEVE trazer os indicadores anuais, com as mesmas colunas da aba INDICADORES_ANUAIS, separador ";", ponto decimal e codificação UTF-8.

**Comparação com uma referência (US8)**

- **FR-040**: A ferramenta `comparar` DEVE comparar o relatório de `reports/<slug>/` com o de uma pasta de referência de mesma estrutura:
  - PDF, Markdown, CSV e figuras, byte a byte;
  - planilha, célula a célula, aba a aba, exigindo a mesma ordem de abas; células numéricas são iguais quando coincidem até a 12ª casa relativa (diferença menor é resto de ponto flutuante e não muda nenhum texto nem nenhuma figura);
  - arquivo presente só numa das pastas conta como diferença;
  - o `etapa.json` fica fora da comparação.

  Ela DEVE listar as diferenças: cada arquivo diferente e, na planilha, a aba e a célula de até 20 células por aba, com uma linha para as demais e o total da aba; abas com nomes ou ordem diferentes DEVEM dar uma única linha, sem comparação de células. Ela DEVE sair com código 0 sem diferença e com código 6 com diferença. Ela NÃO DEVE gravar nada.

### Key Entities

- **Relatório da usina**: PDF, Markdown, planilha, CSV, figuras e `etapa.json`, em `reports/<slug>/`, com a data de geração.
- **Seção**: título, ordem, condição de presença, número entre as presentes, conteúdo e constatações.
- **Constatação**: título e texto gerados pelas Análises, e a seção em que aparece.
- **Capa**: título, subtítulo, blocos de identificação, cadastro e parâmetros, indicadores principais e sumário.
- **Legenda de fonte**: conjuntos de origem (nome, identificador e data de obtenção), conferências com o resultado, dados sem outra fonte e indicação de cálculo do relatório.
- **Mapa de fontes**: para cada figura, tabela, bloco e aba, os elementos da legenda.
- **Conferência citada**: dado conferido, conjunto que permite a conferência e resultado gravado pela Conferência.
- **Item da conclusão, na apresentação**: lista, ordem, regra, texto e seções de origem, com o rótulo "(seção N)".
- **Figura**: arquivo, conteúdo, condição de geração e se é padronizada.
- **Aba da planilha**: nome, grupo, condição de presença e linha na FONTES.
- **Diferença do `comparar`**: arquivo e, na planilha, aba e célula.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (não regressão): Com o perfil da São Domingos e os dados locais, o relatório gerado é idêntico ao relatório de referência, exceto a data de geração. A referência é o relatório aprovado em 07/10/2026, com a conclusão aprovada, os dois textos que citavam caminhos do código já reformulados e o rótulo das horas paradas sem programação corrigido em 08/10/2026 (Decisões do usuário):
  - PDF com 30 páginas e o mesmo texto;
  - Markdown idêntico;
  - planilha com as 58 abas idênticas célula a célula;
  - as 8 figuras e o CSV idênticos byte a byte;
  - nenhuma destas afirmações, contraditas pelos dados: "96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained".

  Com a mesma data de geração da referência, o `comparar` não aponta nenhuma outra diferença.
- **SC-002**: 100 % das figuras, tabelas e blocos do PDF e do Markdown têm legenda de fonte, e 100 % das abas aparecem na FONTES. Numa conferência completa das legendas, cada conjunto citado alimenta a figura ou tabela, e nenhum conjunto que a alimenta fica de fora.
- **SC-003**: Cada constatação aparece exatamente 1 vez no PDF e 1 vez no Markdown, no início da sua seção. A capa e o sumário não têm nenhum texto de constatação.
- **SC-004**: A capa do PDF cabe na página 1. O sumário lista 100 % das seções presentes, com a página real de cada uma. O rodapé de 100 % das páginas tem só a numeração.
- **SC-005**: O Markdown e o PDF têm as mesmas seções, na mesma ordem, o mesmo sumário e as mesmas tabelas, e 100 % das figuras do Markdown estão no corpo das seções.
- **SC-006**: A conclusão:
  - cabe em uma página do PDF;
  - tem até 4 listas, com no máximo 5 itens cada;
  - tem 100 % dos itens terminados pelo rótulo de seções presentes.

  A aba CONCLUSAO traz 100 % dos itens gerados.
- **SC-007**: 100 % dos números das tabelas e das legendas do relatório são iguais aos da planilha. Os resultados de conferência citados nas legendas são iguais aos gravados pela Conferência.
- **SC-008**: Com todos os conjuntos, as 8 figuras são gravadas a 300 DPI, no padrão visual único da FR-035. As figuras 01, 02, 05 e 06 têm o mesmo tamanho e ocupam a largura útil no PDF; nenhuma outra passa de 285 pt de altura.
- **SC-009**: Duas gerações com as mesmas entradas e a mesma `--data-geracao` dão 0 diferença no `comparar` (código 0). Uma célula ou um byte alterado dá código 6, com a diferença listada.
- **SC-010**: Com o perfil de uma usina fictícia, sobre dados de teste:
  - o relatório sai completo, com a mesma estrutura;
  - nenhum texto, rótulo ou aba cita o nome, os identificadores ou os parâmetros da São Domingos;
  - só com a base de EVT, sai com 12 seções numeradas sem lacunas;
  - o PDF é válido com e sem as figuras.
- **SC-011**: Em 100 % das tentativas de gerar o relatório sem as Análises concluídas, a etapa sai com código 5 e não grava nada.
- **SC-012**: Com os resultados das Análises já gravados, a etapa termina em até 1 minuto para uma série horária de oito anos com todos os conjuntos.

---

## Decisões do usuário

| Data | Decisão | Onde se aplica |
|---|---|---|
| 30/09/2026 | Os parâmetros técnicos citam a fonte registrada, o RF 0009/2017-AGEPAN-SFG; o modelo de RF de 2026 da AGEMS não é citado como fonte. | FR-011, FR-022 |
| 02/10/2026 | Garantia física de 36,4 MWmed (ANEEL, valor vigente), no lugar dos 36,9 MWmed do RF de 2017; o relatório mostra o valor do perfil. | FR-011, FR-013, FR-020, FR-022 |
| 02/10/2026 | Horas com geração zero contadas por mês, com seção própria e aba HORAS_GERACAO_ZERO_MES. | FR-007, FR-038 |
| 05/10/2026 | Sem cópia `.bak` do relatório: a etapa regrava as saídas, e as versões aprovadas ficam nas cópias de segurança do projeto. | FR-003 |
| 05/10/2026 | Todo gráfico é feito com seaborn, com paleta, tipografia e resolução definidas num só lugar. | FR-035 |
| 06/10/2026 | Só as conferências refeitas pelo fluxo entram nas legendas; as conferências manuais com a CCEE e o BI da ANEEL, de 01 e 02/10/2026, ficam fora do relatório. | FR-026 |
| 06/10/2026 | A capa traz dados básicos, indicadores principais, data de geração e sumário, no lugar da lista inicial de constatações. Cada constatação aparece uma única vez, no início da sua seção. Fica a ordem das seções do PDF aprovado. | FR-007, FR-009, FR-011 |
| 06/10/2026 | Rodapé só com a numeração das páginas. A data de geração vai para a capa e para o cabeçalho do Markdown, que perde a linha de fontes. | FR-011, FR-015, FR-017 |
| 06/10/2026 | O Markdown segue a estrutura do PDF, com as figuras no corpo das seções. | FR-017 |
| 06/10/2026 | Notas enxutas: nas seções das bases complementares sai a parte "Fonte: conjunto … obtido em …" e ficam as ressalvas; ressalva já coberta pelas notas gerais de fonte não se repete. | FR-021 |
| 07/10/2026 | A ficha do cadastro vai para a capa, no bloco "Cadastro no ONS", sem a data da consulta. Sai a seção própria do cadastro. A constatação do cadastro vai para "Fonte e cobertura dos dados". A ressalva do cadastro sem série histórica fica só nas notas metodológicas. | FR-010, FR-012, FR-021 |
| 07/10/2026 | Figuras 01, 02, 05 e 06 maiores e padronizadas: mesmo tamanho (11 × 4,3 polegadas) e largura útil da página no PDF. | FR-036 |
| 07/10/2026 | Seção "Conclusão", com quatro listas geradas por regras. O texto gerado para a São Domingos foi aprovado. | FR-029 a FR-033 |
| 07/10/2026 | O relatório de referência da não regressão é o aprovado em 07/10/2026, com a conclusão aprovada. | SC-001 |
| 07/10/2026 | O que deve se manter é o conteúdo do relatório: tabelas, figuras, identificação e conclusão. Mudança só de caminho não é problema; os dois textos que citavam caminhos do código foram reformulados antes da cópia de referência, e o relatório deixou de citar caminhos de arquivo. | FR-021, FR-022, SC-001 |
| 07/10/2026 | Os trechos próprios da usina que estavam fixos no código passam a vir do perfil, palavra por palavra. | FR-019 |
| 08/10/2026 | O rótulo das horas paradas sem programação passa a "sem programação: fora do período ou sem valor programado", e o relatório de referência da não regressão passa a ser o gerado com essa mudança. As saídas são gravadas primeiro em arquivos temporários e só então substituem as anteriores, que ficam como estavam se algo falhar (constituição, Requisito Técnico 3). | SC-001, FR-003 |

---

## Assumptions

- **Entradas prontas**:
  - Os resultados das Análises trazem os dados de cada tabela e figura, inclusive as médias diárias da figura 01 e as médias anuais das vazões da figura 05, além das constatações e dos itens da conclusão.
  - Os resultados de conferência chegam dentro dos resultados das Análises, como a Conferência os grava.
  - Esta etapa só formata e organiza.
- **Fronteira com as outras etapas**:
  - **Análises**: textos das constatações e dos itens da conclusão, catálogo C1 a C11, limiares e termos proibidos.
  - **Conferência**: as seis conferências e as suas tolerâncias.
  - **Coleta**: perfil da usina, regras comuns, comando `completo` e ferramenta `copia-seguranca`.
- **Textos próprios da usina**: hoje, quatro trechos descrevem a usina sem vir do perfil nem dos dados:
  - a garantia física da época do documento de origem do IP e do TEIF, nas notas;
  - a fonte do início da operação comercial, na tabela de parâmetros;
  - a descrição do patamar de vertimento mínimo, nas notas e na tabela de parâmetros;
  - a ressalva sobre o volume útil, nas notas da hidrologia.

  Para valer a FR-019 sem mudar o relatório, esses trechos passam a vir do perfil, palavra por palavra, nos campos opcionais definidos na spec da Coleta de dados (aprovados pelo usuário em 07/10/2026).
- **Textos sem caminho de arquivo**: até 07/10/2026, dois textos citavam locais do código ou dos dados que mudam com a nova organização:
  - a nota de sinalizações da hidrologia (e a da disponibilidade, quando há horas inconsistentes), que citava o arquivo de dados tratados;
  - a origem dos limiares, na tabela de parâmetros e na aba PARAMETROS, que citava o arquivo das regras gerais.

  Os dois foram reformulados antes da cópia de referência (FR-021 e FR-022), e o relatório não cita mais caminhos de arquivo.
- **Referência**: o relatório de referência é gerado pelo código atual com a data de geração fixada e guardado na cópia de segurança feita antes da reorganização. O `comparar` usa essa cópia.
- **Ambiente**: o ambiente é o mesmo da referência, com Windows, fonte Arial e as mesmas versões das dependências. Em outro ambiente, os bytes do PDF e das figuras podem mudar sem mudar o conteúdo.
- **Desempenho**: o limite de 1 minuto supõe os resultados das Análises já gravados e não inclui as etapas anteriores.
