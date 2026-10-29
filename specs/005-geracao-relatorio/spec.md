# Spec da Etapa 5: Geração do relatório

**Etapa**: 5 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-23

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

Produzir o relatório de uma usina — PDF, Markdown, planilha, CSV e figuras — e o resumo executivo dele, só a partir do que as etapas anteriores gravaram e do perfil da usina, sem calcular nada novo, numa estrutura fixa: capa com o panorama e o sumário, cada constatação uma única vez no início da sua seção, fonte e conferência abaixo de cada figura e tabela, conclusão por regras e notas metodológicas. A etapa também permite fixar a data de geração e comparar o relatório com uma versão guardada, para provar que ele não mudou.

O relatório vale para todos os tipos de usina que o fluxo atende (UHE, PCH, CGH, UTE, UTN, EOL e UFV), em dois caminhos:
- **hidrelétrica com EVT** (UHE, PCH ou CGH com série própria na Energia Vertida Turbinável): as 17 seções da FR-007, sem mudança;
- **usina sem EVT** (as demais): as seções comuns sobre a base horária comum e as seções próprias do tipo, com cada número identificado como da usina, do conjunto de usinas ou de um agregado, e as seções sem base omitidas, com o motivo nas notas.

Junto com o relatório, a etapa gera o **resumo executivo**, de até duas páginas, para a direção, com a conclusão do relatório copiada igual. Fora do relatório de uma usina, a etapa:
- gera o **relatório de carteira** de um estado, de um tipo ou dos dois, só com os resultados já gravados, sem refazer nenhuma etapa e sem atribuir nota nem parecer;
- registra os relatórios aprovados como **referência**, com a Coleta e o perfil congelados, e os refaz e compara num espaço isolado.

---

## Entradas e saídas

**Comando**

```text
python -m src relatorio --usina <slug> [--data-geracao "DD/MM/AAAA HH:MM"]
```

- `--data-geracao`: fixa a data e a hora de geração mostradas no relatório e no resumo executivo e torna os dois PDFs reproduzíveis byte a byte (FR-004). Sem ela, vale a data e a hora da execução.
- O comando `completo` repassa `--data-geracao` a esta etapa.
- As regras comuns a todas as etapas estão na spec da Coleta: sintaxe, `--log-level`, perfil da usina (código 4), campos do `etapa.json`, pré-requisitos e mensagens.

**Lê**

| Entrada | Onde |
|---|---|
| Resultados das Análises, com os resultados da Conferência: dados de cada tabela e figura, constatações, itens da conclusão e resultados das conferências | `data/usinas/<slug>/analises/resultados.pkl` |
| Data de obtenção de cada conjunto do ONS, registrada pela Coleta em `datas_obtencao.csv` e levada pelas Análises | dentro de `resultados.pkl` |
| Perfil da usina: nome, tipo, modalidade, identificadores, parâmetros e fontes | `usinas/<slug>/perfil.toml` |

**Grava**, em `reports/<slug>/`:

| Arquivo | Conteúdo |
|---|---|
| `relatorio_analise_estatistica.pdf` | relatório em PDF, A4 paisagem |
| `relatorio_analise_estatistica.md` | o mesmo relatório em Markdown |
| `perfil_estatistico_anual.xlsx` | planilha, uma aba por tabela (FR-038) |
| `perfil_estatistico_anual.csv` | indicadores anuais (FR-039) |
| `figures/` | as figuras em PNG: até oito na hidrelétrica com EVT e até 15 na usina sem EVT (FR-034) |
| `resumo_executivo.pdf` | resumo executivo em PDF, A4 retrato, até duas páginas (FR-052 a FR-055) |
| `resumo_executivo.md` | o mesmo resumo em Markdown |
| `etapa.json` | manifesto da etapa; o `resumo` está na FR-006 |

**Códigos de saída**

| Código | Quando |
|---|---|
| 0 | relatório e resumo executivo gerados |
| 1 | erro ao montar ou gravar qualquer saída, inclusive o PDF e o resumo executivo com mais de duas páginas mesmo sem a evolução anual |
| 2 | opção inválida, inclusive `--data-geracao` fora do formato; nada é executado |
| 4 | perfil da usina inválido; nada é gravado |
| 5 | Análises sem resultados concluídos, ou com resultados desatualizados; nada é gravado |

**Ferramenta `comparar`** (FR-040 e FR-043)

```text
python -m src comparar --usina <slug> --referencia <pasta>
python -m src comparar --todas [--coleta]
```

| Código | Quando |
|---|---|
| 0 | nenhuma diferença |
| 1 | erro, como pasta de referência inexistente, arquivo ilegível, nenhuma referência registrada, Coleta ou perfil congelados ausentes ou alterados, ou erro numa etapa refeita |
| 2 | opção inválida, como `--referencia` ausente, `--todas` com `--usina` ou `--coleta` sem `--todas` |
| 4 | perfil da usina inválido (com `--usina`) |
| 6 | há diferenças, listadas na saída |

**Comando `referencia`** (FR-042)

```text
python -m src referencia --usina <slug> --data-geracao "DD/MM/AAAA HH:MM" --aprovado-em "DD/MM/AAAA"
```

- **Lê**: o relatório em `reports/<slug>/` e o `etapa.json` dele, a Coleta da usina em `data/usinas/<slug>/coleta/` e o perfil.
- **Grava**: `relatorios_referencia/<slug>/`, com o relatório aprovado, a Coleta e o perfil congelados e o `referencia.json`.
- **Códigos**: 0 referência registrada; 1 relatório gerado com outra data, referência anterior fora do git ou falha de gravação ou de conferência; 2 opção inválida; 4 perfil inválido; 5 relatório ou Coleta ausente, não concluída, desatualizada ou em formato antigo.

**Comando `carteira`** (FR-049)

```text
python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao "DD/MM/AAAA HH:MM"]
```

- **Lê**: o catálogo de usinas em `data/catalogo/`, os perfis em `usinas/*/perfil.toml` e o `etapa.json` e o `resultados.pkl` das Análises de cada usina do recorte. Nenhuma etapa é executada, e o portal não é consultado.
- **Grava**, em `reports/carteiras/<nome>/`: `relatorio_carteira.pdf` (A4 retrato), `relatorio_carteira.md`, `carteira.xlsx` e `figures/`.
- **Códigos**: 0 carteira gerada; 1 erro; 2 opção inválida, inclusive sem `--estado` nem `--tipo`; 5 catálogo ausente ou nenhuma usina do recorte com resultado, sem gravar nada.

Os contratos estão em [contracts/](contracts/): linha de comando do relatório, resumo executivo, carteira e referências.

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
   - `reports/<slug>/` recebe o PDF, o Markdown, a planilha, o CSV, as figuras, o resumo executivo e o `etapa.json` concluído;
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

Como fiscal, quero comparar o relatório atual de uma usina com uma versão guardada e ver a lista de diferenças. Quero também guardar cada relatório aprovado como referência, com os dados e o perfil que o geraram, e refazer todas as referências a cada mudança do código. Assim provo que uma mudança no código não alterou nenhum relatório aprovado.

**Why this priority**: É a prova de não regressão da reorganização e de qualquer mudança futura (constituição, princípio IX).

**Independent Test**: Comparar duas gerações com a mesma data, que não devem ter diferença. Depois, alterar uma célula da planilha e retirar uma figura de uma das pastas. Registrar a referência de uma usina fictícia, refazê-la com `comparar --todas` e alterar a Coleta congelada.

**Acceptance Scenarios**:

1. **Given** o relatório gerado com os mesmos dados e a mesma `--data-geracao` da referência, **When** `comparar` é executado, **Then** não lista nenhuma diferença e termina com código 0.
2. **Given** uma célula diferente na planilha, **When** `comparar` é executado, **Then** lista a aba e a célula e termina com código 6.
3. **Given** uma figura presente só numa das pastas, **When** `comparar` é executado, **Then** lista o arquivo como diferença e termina com código 6.
4. **Given** a planilha regravada com os mesmos dados, **When** comparada, **Then** não há diferença, porque a planilha é comparada célula a célula.
5. **Given** o relatório de uma usina aprovado pelo usuário e gerado com `--data-geracao`, **When** `referencia` é executado com a mesma data e a data da aprovação, **Then** `relatorios_referencia/<slug>/` recebe o relatório, a Coleta congelada, o perfil e o `referencia.json`, e o log sugere o commit.
6. **Given** uma referência com mudanças fora do git, **When** `referencia` tenta substituí-la, **Then** a substituição é recusada com código 1, e a referência fica como estava.
7. **Given** as referências registradas, **When** `comparar --todas` é executado, **Then** cada relatório é refeito num espaço isolado a partir da Coleta e do perfil congelados e comparado com o aprovado, sem mudar `data/usinas/`, `reports/` nem `data/raw/`; o comando termina com código 0 sem diferença e 6 com diferença.
8. **Given** o perfil atual de uma usina diferente do congelado, **When** `comparar --todas` é executado, **Then** a saída traz o aviso, sem o código 6, e a comparação usa o perfil congelado.

---

### User Story 9 - O relatório para qualquer tipo de usina (Priority: P2)

Como fiscal, quero o relatório de uma térmica, de uma eólica, de uma solar, de uma PCH ou de uma CGH na mesma estrutura do da hidrelétrica: capa, seções comuns, seções próprias do tipo, conclusão e notas, cada número identificado como da usina, do conjunto de usinas ou de um agregado. Quero saber, nas notas, o que o ONS não publica sobre a usina. Assim preparo a fiscalização de qualquer usina com o mesmo rigor, sem tirar conclusão de dado que não existe.

**Why this priority**: A constituição pede o relatório para todos os tipos de usina que os dados abertos do ONS cobrem. O relatório da hidrelétrica com EVT não muda.

**Independent Test**: Gerar o relatório das usinas fictícias de cada tipo, sobre dados de teste, e o das usinas piloto. Conferir as seções de cada tipo, a numeração contínua, as omissões nas notas, o nível nas legendas e o relatório da hidrelétrica com EVT igual ao de referência.

**Acceptance Scenarios**:

1. **Given** uma térmica com o despacho, **When** o relatório é gerado, **Then** ele tem as seções comuns e as três seções de térmica (FR-044), e nenhuma seção de energia vertida turbinável.
2. **Given** a geração por motivo de despacho, a programada e a verificada, o CVU e o CMO de uma térmica, **When** o relatório é gerado, **Then** ele mostra a geração de cada motivo por ano, com a parcela no total, as horas e a energia abaixo e acima do despacho, os maiores desvios, as horas disponíveis sem despacho e, por semana, o CVU frente ao CMO, sem julgar o despacho.
3. **Given** uma eólica ou uma solar, **When** o relatório é gerado, **Then** ele mostra o fator de capacidade, a energia cortada por restrição de operação por mês e por razão e a geração por faixa de recurso, com os números do conjunto identificados como tais e nunca divididos entre as usinas.
4. **Given** uma PCH em conjunto sem série própria, **When** o relatório é gerado, **Then** ele tem duas partes: a usina, com o que o ONS publica dela e o peso dela na potência do conjunto, e a operação do conjunto, antes da conclusão; as notas dizem que o ONS não publica a geração da usina isolada.
5. **Given** uma seção comum sem base no nível da usina, **When** o relatório é gerado, **Then** a seção é omitida, e o motivo aparece nas notas.
6. **Given** a hidrelétrica com EVT, **When** o relatório é gerado com o código que atende os demais tipos, **Then** a comparação com a referência não acusa diferença.

---

### User Story 10 - Relatório de carteira (Priority: P3)

Como fiscal, quero um relatório que reúna as usinas de um estado, de um tipo ou de um tipo num estado, com a cobertura de dados de cada uma, indicadores comparáveis, a ordenação pela quantidade de indícios da conclusão de cada uma e o panorama das pequenas usinas e da MMGD do estado. Assim escolho onde fiscalizar.

**Why this priority**: Depende dos relatórios por usina das histórias anteriores. É o produto que leva a ferramenta do caso a caso para a gestão da fiscalização.

**Independent Test**: Com os resultados gravados das usinas fictícias e o catálogo de teste, gerar a carteira de um estado, a de um tipo e a dos dois. Conferir que ela não refaz etapas, lista as usinas sem resultado e não atribui nota nem parecer.

**Acceptance Scenarios**:

1. **Given** os resultados gravados das usinas do estado, **When** a carteira do estado é gerada, **Then** ela traz:
   - o quadro das usinas com resultado, com tipo, modalidade, potência, cobertura, nível da geração e período;
   - os indicadores comparáveis que se aplicam aos tipos do recorte, cada um com o nível;
   - a ordenação pelos itens de "Possíveis problemas" e "Pontos de atenção";
   - a lista das usinas do estado sem resultado, com o motivo e a cobertura.
2. **Given** os grupos de pequenas usinas e de MMGD do estado, **When** a carteira do estado é gerada, **Then** eles aparecem num panorama agregado, por modalidade, tipo e mês, identificados como agregado, com os valores Tipo III marcados como previsão do ONS.
3. **Given** qualquer texto da carteira, **When** ele é conferido, **Then** não há "satisfatório", "insatisfatório", "cumpre", "descumpre", nota nem equivalente.
4. **Given** uma usina do recorte sem resultado gravado, **When** a carteira é gerada, **Then** ela aparece na lista das usinas sem resultado, com o motivo, nunca com valores estimados.
5. **Given** a carteira só por tipo, **When** ela é gerada, **Then** o panorama é omitido, com o motivo nas notas.

---

### User Story 11 - Resumo executivo para a direção (Priority: P1)

Como diretor da AGEMS, quero receber, junto com o relatório completo, um documento de no máximo duas páginas, sem gráficos, com:
- os indicadores-chave e a evolução por ano;
- em poucas linhas, até onde os dados vão;
- a conclusão do relatório, sem reescrita: os indícios, os possíveis problemas, o que será pedido ao agente e o que será verificado em campo.

Quero o mesmo formato para qualquer tipo de usina, com os blocos que o tipo permite. Assim entendo a situação da usina sem ler o relatório completo, leio exatamente os indícios e as hipóteses que o fiscal vai levar à fiscalização e sei em que seção aprofundar.

**Why this priority**: É o pedido central do resumo e entrega sozinho o valor esperado. A conclusão igual à do relatório completo é a garantia de que o resumo não diz algo diferente dele.

**Independent Test**: Gerar o relatório da São Domingos e o das usinas fictícias de cada tipo e conferir:
- o resumo tem no máximo duas páginas A4 e nenhuma figura;
- o bloco de conclusão do resumo é igual, caractere por caractere, à seção de conclusão do relatório completo da mesma execução;
- cada número das tabelas aparece igual no relatório completo;
- os blocos sem base para o tipo foram omitidos, e os números de conjunto ou de agregado vêm identificados como tais.

**Acceptance Scenarios**:

1. **Given** os resultados das Análises da São Domingos, **When** o relatório é gerado, **Then** o resumo executivo é gerado na mesma execução, em PDF e em Markdown, ao lado do relatório completo, com a mesma data de geração e o mesmo período.
2. **Given** o resumo gerado, **When** o diretor o lê, **Then** encontra os blocos na ordem fixa: cabeçalho, indicadores-chave, evolução anual, "Sobre os dados" e conclusão.
3. **Given** um número de uma tabela do resumo, **When** comparado com o relatório completo, **Then** tem o mesmo valor, a mesma unidade e o mesmo arredondamento.
4. **Given** os resultados já gravados, **When** o fiscal executa só a Geração do relatório, **Then** o relatório e o resumo são gerados juntos, sem refazer as etapas anteriores. Sem os resultados das Análises, a execução para sem gravar nada e indica a etapa a executar.
5. **Given** a conclusão do relatório completo, **When** o resumo é gerado, **Then** o bloco de conclusão tem a frase de abertura, as listas, os itens, a ordem e o texto da seção de conclusão, caractere por caractere.
6. **Given** uma lista sem itens no relatório completo, **When** o resumo é gerado, **Then** ela também não aparece no resumo.
7. **Given** uma usina em que nenhuma regra da conclusão dispara, **When** o resumo é gerado, **Then** o bloco traz a mesma frase do relatório completo para esse caso.
8. **Given** um item que cita seções, como "(seções 8 e 9)", **When** o diretor lê o resumo, **Then** uma linha logo abaixo do título do bloco informa que as seções e as notas metodológicas citadas são as do relatório completo.
9. **Given** uma térmica, **When** o resumo é gerado, **Then** os indicadores-chave e a evolução anual são os da térmica, sem nada de energia vertida turbinável, e a conclusão é a do relatório completo da térmica.
10. **Given** uma PCH com dados só do conjunto de usinas, **When** o resumo é gerado, **Then** cada número do conjunto aparece como do conjunto e nunca dividido entre as usinas.

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
  - sem nenhum item, a seção traz só a frase de "nenhum ponto de atenção" (FR-030), ou, na usina sem EVT, a frase que diz por que não há itens.
- **Data de obtenção sem registro na Coleta**: a legenda diz "data de obtenção não registrada".
- **Figura, tabela ou aba fora do mapa de fontes**: a legenda diz "origem não mapeada", com aviso no log.
- **Figura não disponível**: o PDF mostra "Figura não disponível (…)." no lugar dela, sem falhar; o Markdown a omite.
- **Auditoria da varredura ou datas de obtenção da Coleta ausentes**: o quadro da cobertura sai sem as linhas "Arquivos lidos" e "Versão dos arquivos".
- **`--data-geracao` em formato inválido**: o comando recusa antes de gravar qualquer arquivo.
- **Nova execução**: as saídas são regravadas sem `.bak`. Para guardar uma versão aprovada, usa-se o comando `referencia` (FR-042).
- **Usina sem EVT**:
  - seção sem base no nível da usina: omitida, com o motivo na tabela das seções e regras sem base, nas notas (FR-041);
  - série de referência com menos de 12 meses distintos: a sazonalidade sai, com a frase no lugar da figura e o motivo nas notas;
  - usina que mudou de modalidade ou de composição do conjunto no período: a tabela de trechos da seção 1 mostra cada trecho com o nível; os números do conjunto aparecem por trecho de composição (FR-046);
  - conjunto com usinas de tipos diferentes: os números são do conjunto, com a composição por tipo; a divergência entre o tipo publicado pelo ONS e os tipos da composição vai para a constatação da qualidade dos dados;
  - térmica com mais de uma unidade de planejamento, ou com o código trocado no tempo: a geração é a soma das unidades, e o CVU é mostrado por unidade (FR-044);
  - térmica sem geração no período: sem divisão por zero e sem a figura da geração por motivo; a constatação diz que a usina ficou disponível e não foi despachada;
  - usina nuclear: as seções de térmica;
  - conferência que não se aplica à usina: fica fora das legendas e aparece na tabela das conferências que não se aplicam, nas notas, com o motivo.
- **Resumo executivo**:
  - nenhuma regra da conclusão dispara: o bloco de conclusão traz a mesma frase do relatório completo para esse caso; os demais blocos aparecem normalmente;
  - conteúdo com mais de duas páginas: a conclusão nunca é cortada nem resumida; sai primeiro a evolução anual, com a remissão à seção de origem; se ainda não couber, a geração acusa erro em vez de entregar um resumo com mais de duas páginas, e nenhuma saída é trocada. Fonte e margens nunca ficam abaixo do mínimo;
  - anos parciais: aparecem marcados na evolução anual, como no relatório completo;
  - registros sinalizados: ficam fora dos extremos citados, como no relatório completo. Exemplo (perfil da São Domingos): a hora com 68,7 MW, acima da potência instalada, não aparece como geração máxima;
  - conferência com meta não atingida: se o fluxo completo for interrompido, o resumo também não é gerado; se as etapas forem executadas à parte, o resumo omite o que depende da conferência, como o relatório;
  - mais de um agente no período: o cabeçalho mostra cada agente com o seu período, como a capa (perfil da São Domingos: CGT Eletrosul e Axia Sul);
  - relatório gerado de novo: o resumo é sempre gerado de novo junto; um resumo nunca fica com data ou período diferente do relatório completo ao lado;
  - bloco sem base: é omitido, nunca preenchido com suposição.
- **Carteira**:
  - catálogo ausente, ou nenhuma usina do recorte com resultado: código 5, sem gravar nada;
  - dois perfis com o mesmo CEG: a usina fica sem resultado, como perfil inválido, com os dois slugs;
  - usina sem nenhuma regra da conclusão avaliada com dado da usina: fica no fim da ordenação, sem posição, com a frase de que a falta de itens não quer dizer falta de indício;
  - mês em que nenhum grupo de uma série do panorama tem hora com valor: "sem valor", e não zero;
  - carteira só por tipo: sem o panorama, com o motivo nas notas.
- **Referências**:
  - relatório gerado com outra data de geração: o `referencia` recusa, com o comando para gerar com a data pedida;
  - Coleta ou perfil congelados ausentes ou com SHA-256 diferente do `referencia.json`: erro naquela referência, código 1 no fim;
  - perfil atual diferente do congelado: aviso, sem o código 6;
  - diferença na Coleta refeita causada por arquivo republicado pelo ONS: aparece com o arquivo e a data de publicação, para o usuário decidir.

---

## Requirements *(mandatory)*

### Functional Requirements

**Entradas, saídas e execução (US1)**

- **FR-001**: A etapa DEVE gerar o relatório só a partir de:
  - resultados das Análises da usina, que trazem os resultados da Conferência e as datas de obtenção de cada conjunto do ONS, que as Análises leem de `datas_obtencao.csv`, gravado pela Coleta (FR-050 da spec da Coleta de dados);
  - perfil da usina.

  Ela NÃO DEVE recalcular indicadores, eventos, conferências, constatações ou itens da conclusão. Também NÃO DEVE ler nada de `data/raw/`, os arquivos de dados brutos ou tratados, nem acessar o portal do ONS.
- **FR-002**: Antes de gravar, a etapa DEVE conferir que as Análises da usina estão concluídas e não desatualizadas. Se não estiverem, DEVE sair com código 5, sem gravar nada, indicando o comando das Análises.
- **FR-003**: A etapa DEVE gravar em `reports/<slug>/` os arquivos da tabela "Grava", com esses nomes, e as figuras em `reports/<slug>/figures/`. Os arquivos de uma execução anterior DEVEM ser regravados sem cópia `.bak`; as versões aprovadas ficam guardadas como relatórios de referência (FR-042). As saídas DEVEM ser gravadas primeiro em arquivos temporários e só substituir as da execução anterior depois de todas geradas e conferidas; se algo falhar, as da execução anterior DEVEM ficar como estavam.
- **FR-004**: A opção `--data-geracao "DD/MM/AAAA HH:MM"` DEVE:
  - fixar a data e a hora de geração mostradas na capa do PDF, no cabeçalho do Markdown e no resumo executivo;
  - gerar o PDF do relatório e o do resumo sem data de criação nem identificador variáveis, para que as mesmas entradas com a mesma data produzam os mesmos arquivos.

  Sem a opção, vale a data e a hora da execução. Uma data em formato inválido DEVE ser recusada antes de qualquer gravação.
- **FR-005**: Com as mesmas entradas e a mesma `--data-geracao`, a etapa DEVE produzir PDF, Markdown, CSV, figuras e resumo executivo idênticos byte a byte e a planilha idêntica célula a célula.
- **FR-006**: A etapa DEVE sair com código 0 quando todas as saídas forem gravadas, e com código 1 quando qualquer saída falhar, inclusive o PDF e o resumo executivo, com o erro registrado no log. O `resumo` do `etapa.json` DEVE trazer:
  - a data de geração;
  - a quantidade de seções;
  - a quantidade de páginas do PDF;
  - a quantidade de figuras;
  - a quantidade de abas da planilha;
  - do resumo executivo, as páginas, a presença da evolução anual e as palavras fora das tabelas.

**Estrutura do relatório (US2)**

- **FR-007**: O relatório da hidrelétrica com EVT (UHE, PCH ou CGH com série própria na Energia Vertida Turbinável) DEVE ter exatamente as seções abaixo, nesta ordem e com estes títulos, no PDF e no Markdown. A usina sem EVT tem as seções da FR-041.
  - Seção cuja condição não é atendida fica fora do corpo e do sumário.
  - As seções presentes são numeradas 1, 2, 3… sem lacunas: são 17 com todos os conjuntos e 12 só com a base de EVT.

  | Seção | Presente | Conteúdo, nesta ordem |
  |---|---|---|
  | Fonte e cobertura dos dados | sempre | quadro da cobertura: conjunto de EVT; critério de extração; arquivos lidos e versão dos arquivos, quando a Coleta os registrou; período; registros e horas ausentes; anos parciais |
  | Indicadores anuais | sempre | indicadores por ano |
  | Disponibilidade e geração por ano | sempre | figura 04; períodos de indisponibilidade total de pelo menos 24 h |
  | Indicadores oficiais do ONS por unidade geradora | com os indicadores por unidade geradora | disponibilidade por ano (declarada × DISPF); TEIFa e TEIP mais recentes por unidade e parcela e as taxas operativas ao lado das oficiais (FR-071), com o resumo das taxas frente às referências; indicadores anuais por unidade; horas por estado operativo; meses com DISPF e horas divergentes |
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
- **FR-010**: Na hidrelétrica com EVT, cada constatação DEVE ser apresentada nesta seção (na usina sem EVT, vale o mapa da FR-041):

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
  - o título "<nome da usina> — Análise do desempenho operacional";
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

  Na usina sem EVT, a capa tem a mesma ordem e o mesmo título, com:
  - o subtítulo com o período, os registros horários da série de referência e a série com o identificador e o nível, por exemplo "Geração por usina (conjunto de usinas, id ONS CJU_…)";
  - no bloco de identificação, o tipo e a modalidade, o CEG, o id ONS, o conjunto de usinas, quando há, os códigos da programação diária, o estado e, nas térmicas com o despacho, o subsistema e os códigos de planejamento com o período de cada um; e o agente atual das unidades, proprietário e operador, como a Capacidade de geração do ONS o traz, sem o histórico dos agentes ("Agente atual");
  - o bloco do cadastro, como na hidrelétrica com EVT;
  - no bloco de parâmetros, os parâmetros do tipo, sem os hidráulicos: a potência instalada com as unidades (iguais ou não), o combustível, a garantia física e o IP e o TEIF de referência, quando o perfil os traz, e o início da operação comercial.
- **FR-012**: Com o cadastro do ONS carregado, a capa DEVE trazer o bloco "Cadastro no ONS", entre a identificação e os parâmetros, com:
  - usina, CEG e id ONS;
  - modalidade de operação;
  - centro de operação;
  - ponto de conexão;
  - potência autorizada;
  - estado e situação na ANEEL;
  - quantidade de homônimos excluídos pelo CEG.

  O bloco NÃO DEVE trazer a data da consulta, que fica na legenda de fonte e na aba CAD_FICHA. Sem o cadastro, a capa fica com os outros dois blocos.
- **FR-013**: Na hidrelétrica com EVT, os indicadores principais DEVEM ser estes, nesta ordem, cada um com um complemento curto:
  - disponibilidade média declarada, em % da potência instalada, com a referência da garantia física;
  - disponibilidade apurada pelo ONS (DISPF), média das unidades, com a TEIFa e a TEIP mais recentes e o mês; só com os indicadores por unidade geradora;
  - fator de capacidade, com a geração média e a razão com a garantia física;
  - energia vertida turbinável, em GWh, com a parcela em geração + EVT e a % das horas com EVT;
  - EVT com a usina parada, em GWh, com a % da EVT e as horas.

  Abaixo deles vêm uma nota e a legenda de fonte. A nota depende dos indicadores por unidade geradora:
  - com eles, distingue os indicadores calculados no relatório dos apurados pelo ONS;
  - sem eles, diz que os indicadores são aproximações que não substituem os índices regulatórios.

  Na usina sem EVT, os indicadores principais DEVEM ser até quatro, nesta ordem, os de conjunto identificados como "do conjunto <nome>":
  - a geração média de cada nível da série de referência, com a energia e as horas com valor;
  - logo depois, o indicador do tipo: com a série da usina, nas eólicas e solares, o fator de capacidade e a energia cortada por restrição de operação, em % da energia estimada nas semi-horas com a marca de restrição, e, nas térmicas com o despacho, as horas com despacho; nos demais casos, as horas com geração até 1 MW, no nível da série;
  - a disponibilidade operacional média, com a Disponibilidade por usina;
  - a DISPF, média das unidades, com a TEIFa mais recente e o mês, com os indicadores por unidade geradora.

  A nota diz que os indicadores são calculados a partir da série de referência e da disponibilidade publicadas pelo ONS e não substituem os índices regulatórios; com números do conjunto, diz que eles são da soma das usinas do conjunto, como o ONS publica, e não são divididos entre elas.
- **FR-014**: No PDF, a capa DEVE ocupar só a página 1, e a primeira seção DEVE começar na página 2.

**PDF (US2)**

- **FR-015**: O PDF DEVE ser A4 paisagem, com:
  - cabeçalho a partir da página 2: "<nome da usina> — energia vertida turbinável (dados ONS) · <início> a <fim>"; na usina sem EVT, "<nome da usina> — desempenho operacional (dados ONS) · <início> a <fim>";
  - rodapé só com "Página X de Y", sem frase de fontes nem data;
  - título, assunto e autor do documento gerados do nome da usina (`usina.nome`) e do período;
  - fonte tipográfica que exibe ≤, ≥ e −.
- **FR-016**: A paginação do PDF DEVE seguir estas regras:
  - figura sempre junta das suas legendas e com no máximo 285 pt de altura; as padronizadas (FR-036) ficam fora desse limite;
  - tabela de até 12 linhas inteira numa página, com o subtítulo, a nota e a legenda;
  - tabela mais longa começa na página corrente se couberem o subtítulo e 6 linhas, e continua na seguinte com o cabeçalho repetido;
  - título da seção e constatações sempre juntos;
  - subseção (a parte do conjunto, FR-048) junto da figura seguinte, ou com espaço para o início da tabela seguinte;
  - figura ausente substituída pelo aviso "Figura não disponível (…).", sem falhar.

**Markdown (US2)**

- **FR-017**: O Markdown DEVE ter a mesma estrutura do PDF:
  - cabeçalho com o título "<nome da usina> — energia vertida turbinável e desempenho operacional (dados ONS)", o período com a quantidade de registros e "**Gerado em**: dd/mm/aaaa hh:mm", sem linha de fontes; na usina sem EVT, o título da capa (FR-011) e, no período, os registros horários da série de referência, com a série, o identificador e o nível;
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
- **FR-019**: Os textos do relatório NÃO DEVEM ter nome, identificador ou valor de usina que não venha do perfil ou dos dados, em nenhum tipo de usina. A regra vale para título, cabeçalho, metadados do PDF, capa, notas, legendas, rótulos das figuras e tabela de parâmetros. Os textos que dependem do número de unidades geradoras usam o número do perfil, escrito por extenso nas frases ("duas", para 2).
- **FR-020**: As notas metodológicas DEVEM trazer definições e limitações, sem valores de resultado, em itens. Na hidrelétrica com EVT, são estas, sem parágrafo novo:
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

  Na usina sem EVT, as notas DEVEM trazer:
  - a fonte e a série de referência, varrida em todos os arquivos publicados, com o período da primeira à última hora com valor e a possibilidade de revisão pelo ONS;
  - a base horária comum e a convenção da hora (a de início do intervalo, como o ONS publica);
  - que nenhum valor é preenchido: as horas ausentes ficam listadas na planilha, e as horas sinalizadas ficam na base e nos totais, com o código da regra;
  - o parágrafo de granularidade, só quando algum número do relatório é do conjunto: o que o ONS publica do conjunto e da usina, que os números do conjunto são identificados como tais e não são divididos entre as usinas e que a conclusão da usina não usa números do conjunto;
  - as notas das seções do tipo, da seção do conjunto e da afluência, só quando a seção aparece (FR-044 a FR-047);
  - a conclusão (FR-033);
  - as tabelas das seções e regras sem base para a usina e das conferências que não se aplicam a ela, cada uma com o motivo.
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

  Na usina sem EVT, a tabela traz:
  - o tipo e a modalidade e os parâmetros do tipo (potência instalada, unidades geradoras, combustível, garantia física e início da operação comercial), com a fonte do perfil;
  - os limiares de análise do caminho (geração até o limiar, indisponibilidade total, unidade sincronizada, desvio da programação e período mínimo da sazonalidade e, conforme o tipo, o desvio do despacho e a faixa e o limite físico do recurso) e a tolerância da regra R7, com a origem "Parâmetro de análise";
  - as fontes: a série de referência; a programação diária e a disponibilidade, com o nível e o identificador; a Modalidade das usinas, pelo CEG; e, conforme o tipo, o despacho (CEG e códigos de planejamento), o CVU (códigos de planejamento), o CMO (subsistema, agregado), o Fator de capacidade e a restrição com a razão, com o nível, e a restrição com detalhe (id ONS e CEG), cada uma com o endereço.

**Fonte e conferência (US3)**

- **FR-023**: Cada figura, tabela e bloco da capa DEVE ter, logo abaixo, uma legenda de fonte, no PDF e no Markdown. A legenda fica no texto, fora da imagem; na figura, vem depois da legenda descritiva.
- **FR-024**: A legenda DEVE seguir o formato:

  ```text
  Fonte dos dados: <conjunto> (<identificador>), obtido em <dd/mm/aaaa>; <conjunto> (…). Conferência: <resultado>; <resultado>. Sem outra fonte para conferir: <dados>.
  ```

  - valores calculados no relatório (taxas recalculadas, classificações, faixas, indicadores) começam com "Calculado neste relatório a partir de:" no lugar de "Fonte dos dados:";
  - os parâmetros do perfil aparecem como "parâmetros do projeto (origem na tabela de parâmetros)", e não como conjunto do ONS;
  - sem data registrada, aparece "data de obtenção não registrada";
  - "Conferência" e "Sem outra fonte para conferir" só aparecem quando se aplicam;
  - o identificador diz o nível do dado: o dado da usina cita o identificador da usina, como na hidrelétrica com EVT; o dado de conjunto ou de agregado cita o identificador dele, com o nível escrito, por exemplo "(conjunto de usinas, id ONS CJU_…)" ou "(subsistema SE, agregado)";
  - na usina sem EVT, as legendas das seções comuns citam o conjunto do ONS da série de referência no lugar da EVT.
- **FR-025**: Cada conjunto citado DEVE ter o nome e o identificador abaixo, com os valores do perfil. A data de obtenção é a mais recente registrada pela Coleta para o conjunto em `datas_obtencao.csv`, levada pelas Análises.

  | Conjunto | Identificador na legenda |
  |---|---|
  | Energia Vertida Turbinável | `cod_usina <identificacao.cod_usina>` |
  | Indicadores de disponibilidade por unidade geradora, base mensal | `CEG <identificacao.ceg>` |
  | Indicadores de disponibilidade por unidade geradora, base anual | `CEG <identificacao.ceg>` |
  | Taxas TEIFa e TEIP | `CEG <identificacao.ceg>` |
  | Taxas TEIFa Oper e TEIP Oper | `CEG <identificacao.ceg>` |
  | Parâmetros das taxas TEIFa e TEIP | `CEG <identificacao.ceg>` |
  | Programação diária | `<identificacao.cod_programacao>`; programação do conjunto: `conjunto de usinas, <códigos>` |
  | Disponibilidade por usina | `id ONS <identificacao.id_ons>` |
  | Dados hidrológicos horários | `cod_usina <identificacao.cod_usina>, reservatório <identificacao.id_reservatorio>` |
  | Geração por usina | `id ONS <identificacao.id_ons>`; geração do conjunto: `conjunto de usinas, id ONS <identificacao.id_conjunto>` |
  | Modalidade das usinas | `CEG <identificacao.ceg>` |
  | Composição dos conjuntos de usinas | `conjunto de usinas, id ONS <identificacao.id_conjunto>` |
  | Capacidade de geração | `CEG <identificacao.ceg>`; na seção do conjunto, `CEG das usinas do conjunto <identificacao.id_conjunto>` |
  | Geração térmica por motivo de despacho | `CEG <identificacao.ceg>; códigos de planejamento <códigos>` |
  | CVU das usinas térmicas | `códigos de planejamento <códigos>` |
  | CMO semanal | `subsistema <usina.subsistema>, agregado` |
  | Fator de capacidade | `id ONS <identificacao.id_ons>`; do conjunto: `conjunto de usinas, id ONS <identificador do conjunto>` |
  | Restrição com detalhe (constrained-off) | `id ONS <identificacao.id_ons>; CEG <identificacao.ceg>` |
  | Restrição com a razão (constrained-off) | `id ONS <identificacao.id_ons>`; do conjunto: `conjunto de usinas, id ONS <identificador do conjunto>` |

  Nas restrições, o conjunto do ONS é o da variante do tipo da usina, eólica ou fotovoltaica.
- **FR-026**: Na hidrelétrica com EVT, as legendas DEVEM citar só as seis conferências refeitas pela Conferência a cada execução, com o resultado que ela gravou:

  | Conferência | Texto na legenda |
  |---|---|
  | geração × Geração por usina | "geração conferida com Geração por usina: <c> de <n> horas coincidentes (<p>%)"; com divergências, a quantidade e a aba GER_DIVERGENCIAS; com horas só numa das fontes, a quantidade |
  | disponibilidade declarada × Disponibilidade por usina | "disponibilidade declarada conferida com Disponibilidade por usina (operacional): …", como a anterior, com a aba DISP_DIVERGENCIAS |
  | vazões × Dados hidrológicos horários | "vazões turbinada e vertida conferidas com Dados hidrológicos horários: <c> de <n> horas coincidentes (<p>%)"; abaixo da meta, ", abaixo da meta de 99%" |
  | TEIFa e TEIP recalculadas × publicadas | "TEIFa e TEIP recalculadas conferidas com as publicadas em Taxas TEIFa e TEIP: <m> de <n> meses reproduzidos (diferença máxima de <x> p.p.)" |
  | DISPF × horas por estado operativo | "DISPF conferido com as horas por estado operativo (Parâmetros das taxas TEIFa e TEIP): <n> divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS", ou "sem divergência" |
  | ficha do cadastro × perfil | "potência autorizada e estado conferidos com os parâmetros do projeto: sem divergência", ou as divergências |

  Sem o conjunto que permite a conferência, a legenda DEVE dizer "<dado>: conferência com <conjunto> não feita nesta execução". Conferências manuais com outras instituições NÃO DEVEM aparecer.

  Na usina sem EVT, as legendas DEVEM citar só as conferências aplicadas à usina, com o resultado gravado pela Conferência: a TEIFa e a TEIP, a DISPF e o cadastro, como acima, e, conforme o tipo e o nível dos dados, as conferências entre fontes:

  | Conferência | Texto na legenda |
  |---|---|
  | G1: geração da usina entre as fontes, duas a duas e no mesmo nível | "geração conferida entre as fontes, duas a duas e no mesmo nível (G1): <c> de <n> horas coincidentes (<p>%) em <k> pares de fontes, detalhados na aba CONF_G1_PARES"; com divergências, a quantidade e a aba CONF_G1_DIVERGENCIAS |
  | G2: soma das usinas do conjunto × geração do conjunto | "soma das usinas do conjunto (Restrição com detalhe) conferida com a Geração por usina do conjunto (G2): …", como a da geração, com a aba CONF_G2_DIVERGENCIAS e as horas sem todas as usinas, fora da soma |
  | G3: programação diária × programado do despacho | "programação diária conferida com o programado da Geração térmica por motivo de despacho (G3): …", com a aba CONF_G3_DIVERGENCIAS |
  | G4: verificada do despacho × Geração por usina | "geração verificada da Geração térmica por motivo de despacho conferida com Geração por usina (G4): …", com a aba CONF_G4_DIVERGENCIAS |
  | G5: programação diária × programado do Fator de capacidade | "programação diária conferida com o programado do Fator de capacidade (G5): …", com a aba CONF_G5_DIVERGENCIAS |
  | hora dos Dados hidrológicos × geração da usina | "hora dos Dados hidrológicos conferida pela geração da usina: correlação de <r0> sem deslocamento, <r−1> com −1 h e <r+1> com +1 h, em <n> horas comuns (confirmada)", ou "(não confirmada)" |

  A conferência que não se aplica à usina NÃO DEVE aparecer na legenda: ela fica na tabela das conferências que não se aplicam, nas notas, com o motivo.
- **FR-027**: Um mapa único DEVE dizer, para cada figura, tabela, bloco e aba:
  - os conjuntos de origem;
  - as conferências;
  - os dados sem outra fonte;
  - se o valor é calculado no relatório.

  O PDF, o Markdown e a planilha DEVEM usar esse mesmo mapa. Cada legenda DEVE citar exatamente os conjuntos carregados que alimentam a figura ou tabela. Os dados sem outra fonte pública conferida pelo fluxo são a EVT, a disponibilidade sincronizada, a afluência, os níveis e o volume útil do reservatório e a programação diária; na usina sem EVT, também a geração da série de referência, os motivos de despacho, o CVU e o CMO, a geração estimada e a marca de restrição e o vento ou a irradiância. A programação diária conferida pela G5 nesta execução deixa de ser dado sem outra fonte. Figura, tabela ou aba fora do mapa DEVE gerar "origem não mapeada", com aviso no log.
- **FR-028**: A aba FONTES DEVE ser a última da planilha. Ela tem uma linha para cada outra aba, na ordem da planilha, com as colunas:
  - `aba`;
  - `conjuntos_origem`;
  - `conferencias`, ou "—";
  - `sem_outra_fonte`, ou "—";
  - `calculado_no_relatorio`, com "sim" ou "não".

  Casos especiais:
  - CONSTATACOES e CONCLUSAO: todos os conjuntos carregados e todas as conferências aplicáveis, como cálculo do relatório; na usina sem EVT, só as conferências feitas nesta execução que não dependem da EVT;
  - PARAMETROS: os parâmetros do projeto e os conjuntos carregados;
  - DICIONARIOS: só os conjuntos do tipo e da cobertura da usina, cada conjunto do ONS uma vez; na hidrelétrica com EVT, os dez conjuntos da Energia Vertida Turbinável, dos indicadores por unidade geradora, da programação, da disponibilidade, da hidrologia, da geração e do cadastro, na mesma ordem.

**Conclusão (US4)**

- **FR-029**: A seção "Conclusão" DEVE estar sempre presente, depois de "Qualidade dos dados" (na usina em duas partes, depois da parte do conjunto, FR-048) e antes de "Notas metodológicas e limitações", no PDF, no Markdown e no sumário. É a mesma seção nos dois caminhos.
- **FR-030**: A conclusão DEVE trazer:
  - a frase de abertura "Indícios a confirmar, gerados pelas regras descritas nas notas metodológicas a partir dos resultados das seções indicadas; não afirmam causa nem avaliam o desempenho da usina.";
  - as listas "Pontos de atenção", "Possíveis problemas", "A confirmar com o agente" e "A verificar em campo", nesta ordem, cada uma com subtítulo e no máximo cinco itens, os primeiros na ordem das Análises;
  - em cada item, o texto gerado pelas Análises, seguido do rótulo das seções de origem presentes ("(seção N)", "(seções N e M)" ou "(seções N, M e P)") e de ponto final.

  Lista sem itens não aparece. Sem nenhum item, a seção traz só uma frase:
  - na hidrelétrica com EVT, "Os dados não indicaram pontos de atenção pelos critérios das regras da conclusão.";
  - na usina sem EVT, a frase gerada pelas Análises: a mesma, quando alguma regra do tipo foi avaliada; ou a que diz por que não há itens — as regras usam só dados do nível da usina, e o ONS publica para ela só os números do conjunto; ou nenhuma regra do tipo tem base para a usina, com os motivos nas notas.
- **FR-031**: No PDF, a conclusão DEVE caber numa página. A frase de abertura e as listas ficam juntas, e as notas metodológicas começam, no máximo, na página seguinte à do título da conclusão.
- **FR-032**: A aba CONCLUSAO, logo depois da CONSTATACOES, DEVE trazer todos os itens gerados, inclusive os que passam de cinco. As colunas são:
  - `lista`;
  - `ordem`;
  - `regra`;
  - `texto`;
  - `secoes`: número e título das seções de origem presentes, separados por "; ".
- **FR-033**: As notas metodológicas DEVEM ter um item sobre a conclusão:
  - na hidrelétrica com EVT, gerado das regras gerais, com o texto aprovado: descreve as regras C1 a C11 e os limiares da conclusão e informa que o relatório mostra até cinco itens por lista e que todos estão na aba CONCLUSAO;
  - na usina sem EVT, gerado do catálogo das regras do tipo (FR-055 da spec das Análises): as regras avaliadas para o tipo, só com dados do nível da usina, com os limiares; o limite de cinco itens por lista e a aba CONCLUSAO; e as regras não avaliadas nesta usina, com os motivos na tabela das notas.

**Figuras (US5)**

- **FR-034**: Na hidrelétrica com EVT, a etapa DEVE gerar estas figuras, com estes nomes:

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

  Na usina sem EVT, a etapa DEVE gerar estas, cada série com o nível no rótulo quando não é da usina ("Geração do conjunto <nome>"):

  | Arquivo | Mostra | Gerada |
  |---|---|---|
  | `01_serie_temporal_geracao_disponibilidade.png` | médias diárias da geração, por nível, e da disponibilidade operacional; linha da potência instalada, com a série da usina | sempre |
  | `02_geracao_mensal.png` | energia gerada por mês, em barras, por nível | sempre |
  | `03_geracao_por_mes_do_ano.png` | geração média por mês do ano | com pelo menos 12 meses distintos |
  | `04_perfil_horario_geracao.png` | geração média por hora do dia, no período | sempre |
  | `05_disponibilidade_operacional_sincronizada_mensal.png` | médias mensais das disponibilidades operacional e sincronizada e da geração da usina; linha da potência instalada | com a Disponibilidade por usina |
  | `06_despacho_por_motivo_mensal.png` | geração verificada mensal por motivo de despacho, empilhada, com a geração verificada total | térmicas com o despacho e com geração no período |
  | `07_inflexibilidade_mensal.png` | inflexibilidade programada e verificada por mês | térmicas com inflexibilidade |
  | `08_desvios_despacho_mensal.png` | energia mensal das horas com a verificada abaixo (para baixo) e acima (para cima) da programada | térmicas com desvio além do limiar |
  | `09_cvu_cmo_semanal.png` | CVU semanal de cada unidade de planejamento e CMO médio semanal do subsistema; a linha se interrompe na semana sem comparação | térmicas com o CVU e o CMO |
  | `10_fator_capacidade_mensal.png` | fator de capacidade mensal publicado, com o nível, e o calculado da série própria, tracejado | eólicas e solares com o Fator de capacidade |
  | `11_energia_cortada_por_razao_mensal.png` | energia cortada mensal por razão da restrição, empilhada | eólicas e solares com semi-hora restrita |
  | `12_geracao_por_faixa_de_recurso.png` | geração verificada média (barras) e estimada média (linha) por faixa de vento ou de irradiância | eólicas e solares com o recurso válido |
  | `13_desvio_programacao_mensal.png` | desvio médio absoluto mensal (barras) e desvio médio (pontos) entre a verificada e a programada | eólicas e solares com os maiores desvios da programação |
  | `14_geracao_do_conjunto_por_trecho.png` | geração média mensal do conjunto, uma cor por trecho de composição, com a potência somada de cada trecho tracejada e uma linha vertical em cada mudança de composição | usina com a seção do conjunto |
  | `15_vazoes_mensais.png` | vazões afluente, turbinada e vertida médias por mês; linha do engolimento máximo | hidrelétrica sem EVT com a hora da hidrologia confirmada |

- **FR-035**: Todas as figuras DEVEM ser produzidas com seaborn, com tema, paleta, tipografia e resolução definidos num único lugar:
  - 300 DPI;
  - cores fixas por grandeza, de uma paleta validada para acessibilidade: geração em azul, EVT em laranja, disponibilidade em verde, contexto em cinza, disponibilidade sincronizada em amarelo, afluência em violeta e faixas de afluência em tons de laranja; na usina sem EVT, a série do conjunto em azul escuro, e os motivos de despacho, as razões da restrição e os trechos de composição com cor fixa por categoria, na ordem categórica validada;
  - títulos à esquerda, grade leve, legenda e rótulos das linhas de referência fora da área dos dados;
  - números no padrão brasileiro, e anos parciais com asterisco e a nota "* ano parcial".

  Linhas de referência, faixas e anotações são desenhadas sobre os mesmos eixos. Níveis diferentes nunca são somados na mesma barra ou linha.
- **FR-036**: As figuras 01, 02, 05 e 06 da hidrelétrica com EVT DEVEM ter o mesmo tamanho de imagem. No PDF, elas DEVEM ocupar a largura útil da página, fora do limite de altura da FR-016. Na usina sem EVT, todas as figuras têm esse mesmo tamanho; as figuras 01 a 05 ocupam a largura útil, e as demais ficam no limite de altura da FR-016.
- **FR-037**: Cada figura DEVE ter, abaixo dela, uma legenda descritiva, igual no PDF e no Markdown, seguida da legenda de fonte. A legenda descritiva é gerada dos resultados e do perfil e diz o que mostra cada cor, linha e faixa, com os valores de referência.

**Planilha e CSV (US6)**

- **FR-038**: Na hidrelétrica com EVT, a planilha DEVE ter uma aba por tabela, com o cabeçalho fixo, nesta ordem:

  | Grupo | Abas | Presentes |
  |---|---|---|
  | Constatações e conclusão | CONSTATACOES (tema e texto, na ordem das Análises), CONCLUSAO (FR-032) | sempre |
  | Base de EVT | INDICADORES_ANUAIS, INDICADORES_GLOBAIS, COBERTURA_POR_ANO, AGENTES, EVT_MENSAL, EVT_MES_DO_ANO, EVT_POR_FAIXA_GERACAO, PERFIL_HORARIO_GERACAO, PERFIL_HORARIO_EVT, EVENTOS_PARADA_COM_EVT, HORAS_GERACAO_ZERO_MES, EVENTOS_INDISP_TOTAL, ANOMALIAS, RESUMO_ANOMALIAS, VALIDACAO_REGRAS, EXTREMOS, PERFIL_ESTATISTICO_ANUAL, PARAMETROS | sempre |
  | Indicadores por unidade geradora | ONS_DISP_ANUAL_USINA, ONS_UG_ANUAL, ONS_HORAS_UG_ANUAL, ONS_HORAS_UG_MENSAL, ONS_TEIFA_TEIP, ONS_DECOMPOSICAO_TAXAS, ONS_TAXAS_OPERATIVAS, ONS_DIVERGENCIAS | cada uma, se tiver linhas |
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

  Na usina sem EVT, a planilha DEVE ter as abas abaixo, nesta ordem, cada uma só com linhas (CONSTATACOES, CONCLUSAO, BASE_ANUAL e OMITIDOS sempre):

  | Grupo | Abas | Presentes |
  |---|---|---|
  | Constatações e conclusão | CONSTATACOES, CONCLUSAO (FR-032) | sempre |
  | Base horária comum | BASE_ANUAL, BASE_MENSAL, BASE_MES_DO_ANO, BASE_HORA_DO_DIA, BASE_SINALIZACOES, GER_AUSENCIAS, TRECHOS, OMITIDOS, CONF_NAO_APLICAVEIS, PARAMETROS | sempre, cada uma com linhas |
  | Disponibilidade por usina | DISP_MENSAL, DISP_ANUAL, DISP_EVENTOS_INDISP_TOTAL | com a Disponibilidade por usina |
  | Programação diária | PROG_RESUMO_MENSAL, PROG_EVENTOS_DESVIO | com a programação no mesmo nível da geração |
  | Térmicas | TERM_MOTIVOS_ANUAL, TERM_MOTIVOS_MENSAL, TERM_INFLEXIBILIDADE, TERM_ATENDIMENTO_ANUAL, TERM_ATENDIMENTO_MENSAL, TERM_MAIORES_DESVIOS, TERM_DISP_SEM_DESPACHO, TERM_CVU_CMO_SEMANAL, TERM_CVU_CMO_RESUMO, CONF_G3_MENSAL, CONF_G3_DIVERGENCIAS, CONF_G4_MENSAL, CONF_G4_DIVERGENCIAS | com as seções de térmica |
  | Eólicas e solares | REN_FC_ANUAL, REN_FC_MENSAL, REN_CORTE_ANUAL, REN_CORTE_MENSAL, REN_CORTE_RAZAO, REN_RECURSO_FAIXAS, REN_DESVIOS_PROGRAMACAO, CONF_G1_PARES, CONF_G1_MENSAL, CONF_G1_DIVERGENCIAS, CONF_G2_MENSAL, CONF_G2_DIVERGENCIAS, CONF_G5_MENSAL, CONF_G5_DIVERGENCIAS | com as seções de eólica e solar |
  | Conjunto de usinas | CONJ_TRECHOS, CONJ_COMPOSICAO, CONJ_MENSAL, CONJ_TIPO_PUBLICADO, CONJ_PESO_USINA (só no relatório em duas partes) | com a seção do conjunto |
  | Dados hidrológicos | HID_ALINHAMENTO, HID_MENSAL, HID_ANUAL, HID_AUSENCIAS, HID_AUDITORIA | hidrelétrica sem EVT, com os Dados hidrológicos |
  | Indicadores por unidade geradora, cadastro e dicionários | as mesmas abas ONS_*, CAD_FICHA, CAD_AUDITORIA e DICIONARIOS da hidrelétrica com EVT | como na hidrelétrica com EVT |
  | Fontes | FONTES (FR-028) | sempre, por último |

- **FR-039**: O CSV DEVE trazer os indicadores anuais, com as mesmas colunas da aba INDICADORES_ANUAIS (na usina sem EVT, as da aba BASE_ANUAL), separador ";", ponto decimal e codificação UTF-8.

**Comparação com uma referência e relatórios de referência (US8)**

- **FR-040**: A ferramenta `comparar` DEVE comparar o relatório de `reports/<slug>/` com o de uma pasta de referência de mesma estrutura:
  - PDF, Markdown, CSV e figuras, byte a byte;
  - planilha, célula a célula, aba a aba, exigindo a mesma ordem de abas; células numéricas são iguais quando coincidem até a 12ª casa relativa (diferença menor é resto de ponto flutuante e não muda nenhum texto nem nenhuma figura);
  - arquivo presente só numa das pastas conta como diferença;
  - o `etapa.json` fica fora da comparação.

  Ela DEVE listar as diferenças: cada arquivo diferente e, na planilha, a aba e a célula de até 20 células por aba, com uma linha para as demais e o total da aba; abas com nomes ou ordem diferentes DEVEM dar uma única linha, sem comparação de células. Ela DEVE sair com código 0 sem diferença e com código 6 com diferença. Ela NÃO DEVE gravar nada. O modo que refaz todas as referências está na FR-043.
- **FR-042** (relatórios de referência): `python -m src referencia --usina <slug> --data-geracao "DD/MM/AAAA HH:MM" --aprovado-em "DD/MM/AAAA"` DEVE registrar o relatório aprovado pelo usuário em `relatorios_referencia/<slug>/`:
  - **conteúdo**: os arquivos do relatório listados no `etapa.json` dele, inclusive o resumo executivo; o perfil (`perfil.toml`); a Coleta congelada (`coleta/`: só os arquivos do `etapa.json` da Coleta e o próprio `etapa.json`, sem `.bak`); o `referencia.json`, com `usina`, `data_geracao`, `aprovado_em`, `periodo`, `arquivos`, `perfil` e `coleta` (com o SHA-256 de cada arquivo);
  - **exige**: o relatório `concluida`, gerado com a data de `--data-geracao`, conferida no `resumo` do `etapa.json`; a Coleta `concluida` no formato atual;
  - **gravação**: numa pasta temporária, com os SHA-256 conferidos, também os de origem contra os `etapa.json`, antes da troca; se algo falhar, a referência anterior fica intacta;
  - **recusa**: substituir uma referência com mudanças fora do git, para que a anterior fique no histórico;
  - **git**: o relatório e o perfil entram no git, inclusive o PDF; a Coleta congelada não. O log termina com a sugestão de commit.
- **FR-043** (`comparar --todas [--coleta]`):
  - para cada referência de `relatorios_referencia/`, DEVE refazer o Tratamento, a Conferência, as Análises e o Relatório num espaço isolado, a partir da Coleta e do perfil congelados, com a data de geração do `referencia.json`, e comparar o relatório refeito com o aprovado, pelas regras da FR-040; `referencia.json`, `perfil.toml` e `coleta/` ficam fora da comparação;
  - as etapas refeitas não leem `data/raw/`;
  - DEVE avisar, sem o código 6, quando o perfil atual difere do congelado;
  - NÃO DEVE mudar `data/usinas/`, `reports/` nem `data/raw/`, e o resultado não depende de outras usinas;
  - com `--coleta`, DEVE refazer também a Coleta com `--sem-portal` e o perfil congelado, noutro espaço isolado, e compará-la com a congelada: as séries extraídas, linha a linha, só no período da referência; as auditorias, só nas contagens por arquivo, sem as colunas de execução; `dicionarios.csv`, `datas_obtencao.csv` e `dicionario_evt.json`, só como informação, sem o código 6; a diferença numa série, com a data de publicação no ONS dos arquivos de origem. As etapas 2 a 5 continuam partindo da Coleta congelada;
  - Coleta ou perfil congelados ausentes ou com SHA-256 diferente, ou erro numa etapa refeita: erro naquela referência, que não impede as demais, e código 1 no fim;
  - códigos: 0 sem diferença, 1 erro, 2 opção inválida, 6 com diferença.

**Usina sem EVT: estrutura (US9)**

- **FR-041** (seções da usina sem EVT): o relatório das demais usinas (UTE, UTN, EOL, UFV e as hidrelétricas sem série própria na Energia Vertida Turbinável) DEVE ter as seções abaixo, nesta ordem, no PDF e no Markdown, montadas sobre a base horária comum e as bases do tipo:
  - seção sem base para a usina fica fora do corpo e do sumário, com o motivo na tabela das seções e regras sem base, nas notas;
  - as seções presentes são numeradas 1, 2, 3… sem lacunas;
  - as seções da hidrelétrica com EVT não entram neste caminho, e as deste caminho não entram no dela.

  | Seção | Tipos | Presente | Conteúdo, nesta ordem |
  |---|---|---|---|
  | Fonte e cobertura dos dados | todos | sempre | quadro da cobertura (série de referência com o identificador, o nível e o endereço, período, registros, horas ausentes e sem valor, horas por nível, anos parciais e trechos); conjuntos do ONS usados, com o nível, o identificador e a data de obtenção; trechos do período, quando há mais de um ou a usina está em conjunto |
  | A usina no conjunto | usina em conjunto sem série própria | FR-048 | FR-048 |
  | Indicadores anuais | todos | fora do relatório em duas partes | indicadores por ano e nível: horas, horas com valor, geração média, energia, máxima, horas até 1 MW e, conforme o tipo, fator de capacidade, disponibilidade, horas disponíveis sem despacho e energia cortada |
  | Disponibilidade e geração por ano | UHE, PCH, CGH, UTE, UTN | com a Disponibilidade por usina | disponibilidade e geração da usina por ano; períodos de indisponibilidade total de pelo menos 24 h, ou "Nenhum período com essa duração." |
  | Indicadores oficiais do ONS por unidade geradora | UHE, PCH, CGH, UTE, UTN | com os indicadores por unidade geradora | disponibilidade da usina por ano (operacional × DISPF); TEIFa e TEIP mais recentes por unidade e parcela e as taxas operativas ao lado das oficiais (FR-071); indicadores anuais por unidade; horas por estado operativo; meses com DISPF e horas divergentes |
  | Série temporal da geração e da disponibilidade; nas eólicas e solares, "Série temporal da geração" | todos | fora do relatório em duas partes | figura 01 |
  | Geração mensal e sazonalidade | todos | fora do relatório em duas partes | figura 02; figura 03, com pelo menos 12 meses distintos, ou a frase da sazonalidade omitida |
  | Perfil horário da geração | todos | fora do relatório em duas partes | figura 04 |
  | Seções de térmica | UTE, UTN | com o despacho | FR-044 |
  | Seções de eólica e solar | EOL, UFV | com as bases | FR-045 |
  | Composição e geração do conjunto | usina em conjunto | com a geração do conjunto, fora do relatório em duas partes | FR-046 |
  | Programação diária × geração verificada | todos | com horas da programação e da geração no mesmo nível, fora do relatório em duas partes | texto com o nível, o período, as horas comuns, a correlação e os dias sem arquivo; geração programada × verificada por mês; maiores eventos de parada com programação acima de 5 MW; nas eólicas e solares, os maiores desvios (FR-045) |
  | Disponibilidade operacional e sincronizada (ONS) | UHE, PCH, CGH, UTE, UTN | com a Disponibilidade por usina | figura 05 |
  | Afluência, vertimento e nível do reservatório (ONS) | UHE, PCH, CGH | com os Dados hidrológicos | FR-047 |
  | Qualidade dos dados | todos | sempre | horas sinalizadas por código, ou "Nenhuma hora sinalizada."; intervalos ausentes da série de referência, ou "Nenhuma hora ausente." |
  | Operação do conjunto <nome> (<id>) | usina em conjunto sem série própria | FR-048 | FR-048 |
  | Conclusão | todos | sempre | FR-029 a FR-031 |
  | Notas metodológicas e limitações | todos | sempre | notas (FR-020); seções e regras sem base, com o motivo; conferências que não se aplicam, com o motivo; parâmetros utilizados (FR-022) |

  - A conferência da geração entre fontes não tem seção própria: os resultados das conferências aplicadas (FR-026) estão nas legendas de fonte e nas abas CONF_* da planilha, e a tabela das seções sem base a lista com esse motivo.
  - As tabelas seguem as regras da FR-008: subtítulo, nota e legenda; anos parciais com asterisco; listas longas resumidas em até 15 linhas, com a lista completa na planilha.
  - Cada constatação DEVE ser apresentada nesta seção (FR-009); fora do mapa, ou com a seção ausente, vai para a seção 1:

  | Constatação | Seção |
  |---|---|
  | Cobertura dos dados; Cadastro da usina no ONS | Fonte e cobertura dos dados |
  | A usina no conjunto | A usina no conjunto |
  | Geração | Indicadores anuais; no relatório em duas partes, Operação do conjunto |
  | Disponibilidade | Disponibilidade e geração por ano |
  | Despacho por motivo | Geração por motivo de despacho e inflexibilidade |
  | Atendimento ao despacho | Atendimento ao despacho |
  | Disponível sem despacho; CVU e CMO | Disponível sem despacho |
  | Fator de capacidade | Fator de capacidade |
  | Energia cortada | Energia cortada por restrição de operação (constrained-off) |
  | Recurso × geração | Recurso × geração |
  | Composição do conjunto | Composição e geração do conjunto; no relatório em duas partes, Operação do conjunto |
  | Programação diária do ONS | Programação diária × geração verificada; no relatório em duas partes, Operação do conjunto |
  | Afluência e vertimento | Afluência, vertimento e nível do reservatório (ONS) |
  | Qualidade dos dados | Qualidade dos dados |

**Usina sem EVT: seções do tipo e do conjunto (US9)**

- **FR-044** (seções de térmica): nas UTE e UTN com a Geração térmica por motivo de despacho, as seções abaixo DEVEM vir depois do perfil horário, em ordem fixa, montadas com o campo `termica` dos resultados (FR-056 da spec das Análises):
  1. **Geração por motivo de despacho e inflexibilidade**: o período do despacho e as unidades de planejamento; a geração programada e verificada de cada motivo no período, com a parcela na geração total publicada (os motivos podem se sobrepor, e a soma das parcelas pode diferir de 100 %); por ano, a geração programada e a verificada, as horas com despacho e a inflexibilidade programada e verificada; a figura 06, com geração no período, e a figura 07, com inflexibilidade.
  2. **Atendimento ao despacho**: por ano, nas horas com geração programada acima de 1 MW, as horas e a energia abaixo e acima da programada além do limiar de desvio (5 MW) e, sem programação, com geração; as 15 horas de maior desvio absoluto, com a figura 08, ou a frase "Nenhuma hora com desvio além de 5 MW.".
  3. **Disponível sem despacho** ("Disponível sem despacho e CVU × CMO", com o CVU × CMO): as horas disponíveis sem despacho por ano, com a potência disponível média nelas; com o CVU e o CMO, por unidade de planejamento, as semanas operativas com o CVU abaixo, acima e igual ao CMO médio semanal do subsistema, a geração nas semanas abaixo e acima e as semanas sem comparação (CVU ausente, zero ou negativo), sem julgar o despacho; a figura 09.
  - Sem o despacho, as três seções saem, com o motivo nas notas; sem o CVU ou sem o CMO, sai a parte do CVU × CMO, com o motivo.
  - **Capa**: FR-013. **Legendas**: o despacho cita o CEG e os códigos de planejamento; o CVU, os códigos de planejamento; o CMO, o subsistema com o nível escrito ("subsistema SE, agregado"); as tabelas e figuras do despacho citam a G3 e a G4 (FR-026).
  - **Notas**: o despacho pelo CEG, com os códigos de planejamento do perfil, somadas as unidades por hora, na hora de início do intervalo; o CVU da revisão mais recente de cada semana operativa, com o ausente, o zero e o negativo sinalizados, mantidos e sem comparação; o CMO como contexto do subsistema, dado agregado, e não da usina. Os limiares das regras C12 a C15 ficam na nota da conclusão (FR-033).
  - **Planilha**: as abas das térmicas da FR-038.
- **FR-045** (seções de eólica e solar): nas EOL e UFV com as bases, as seções abaixo DEVEM vir depois do perfil horário, em ordem fixa, montadas com o campo `renovavel` dos resultados (FR-058 da spec das Análises):
  1. **Fator de capacidade**: por ano e nível, o fator publicado pelo ONS (Σ geração verificada ÷ Σ capacidade instalada, nas horas com os dois dados, no nível publicado) e, com série própria da usina, o calculado neste relatório (geração média da usina ÷ potência instalada do perfil), com as horas com o fator fora de 0 a 1 e acima da capacidade; a figura 10.
  2. **Energia cortada por restrição de operação (constrained-off)**: o período da restrição com detalhe, as semi-horas e as restritas; por ano, a verificada e a estimada nas semi-horas com estimativa, a cortada, a % da estimada, as horas restritas, as restritas sem estimativa, as semi-horas sem a marca e a diferença bruta; a energia cortada por razão da restrição (REL, CNF, ENE e sem razão publicada), com a figura 11, ou a frase "Nenhuma semi-hora com a marca de restrição.". Com a razão publicada pelo conjunto, o texto diz que a razão é do conjunto e a energia cortada é da usina.
  3. **Recurso × geração**: a geração verificada e a estimada médias por faixa de vento (m/s) ou de irradiância (W/m²), só nas semi-horas com o recurso válido e até o limite físico (40 m/s; 1.500 W/m²); a figura 12.
  - A aderência à programação fica na seção comum de programação: as 15 horas de maior desvio absoluto, no nível da programação, e a figura 13. Na eólica ou solar com série própria, com a programação e a geração publicadas pelo conjunto, a comparação é a do conjunto, identificada como tal, e não entra na base horária da usina.
  - Seção sem base é omitida, com o motivo nas notas; na série com menos de 12 meses distintos, a sazonalidade sai, com o motivo.
  - **Capa**: FR-013. **Legendas**: a restrição com detalhe cita o id ONS e o CEG da usina; o Fator de capacidade e a razão da restrição publicados pelo conjunto citam "conjunto de usinas, id ONS CJU_…"; as tabelas e figuras citam a G1, a G2 e a G5, quando aplicadas (FR-026).
  - **Notas**: a energia cortada só nas semi-horas com a marca de restrição, pela estimada menos a verificada, sem valores negativos; a semi-hora sem a marca (arquivo publicado sem a coluna, como a fotovoltaica de 05 a 12/2024) fica fora do total e é contada; a estimada 0 com a usina gerando é estimativa ausente: fica fora dos totais e das médias da estimada e, nas semi-horas restritas, o corte não é calculado; as semi-horas são levadas à hora cheia pela média das duas meias-horas só nos cruzamentos com séries horárias; o recurso inválido ou acima do limite físico fica fora das faixas. Os limiares das regras C16 a C19 ficam na nota da conclusão (FR-033).
  - **Planilha**: as abas das eólicas e solares da FR-038.
- **FR-046** (seção "Composição e geração do conjunto"): em toda usina em conjunto com a geração do conjunto (FR-060 da spec das Análises), inclusive a eólica ou solar com série própria, a seção DEVE vir depois das seções do tipo:
  - **Texto**: a constatação "Composição do conjunto", no início da seção, com a composição de cada trecho e a geração do conjunto, sempre "do conjunto <nome>". A divergência entre o tipo publicado pelo ONS na série do conjunto e os tipos da composição fica na constatação da qualidade dos dados.
  - **Tabelas**:
    - geração do conjunto por trecho de composição: trecho, início, fim, usinas, tipos, horas com valor, energia (MWh), média (MWmed), máxima (MW) e, com as unidades das usinas, a potência somada das usinas do trecho (MW);
    - usinas da composição no período: usina, tipo, CEG, entrada e saída no conjunto e, com as unidades, a potência (MW).
  - **Figura 14**: a geração média mensal do conjunto, uma cor por trecho de composição (do sexto trecho em diante, cinza, "Demais composições"), com a potência somada de cada trecho tracejada e uma linha vertical em cada mudança de composição.
  - **Legendas**: "Geração por usina (conjunto de usinas, id ONS CJU_…)", "Composição dos conjuntos de usinas (conjunto de usinas, id ONS CJU_…)" e "Capacidade de geração (CEG das usinas do conjunto CJU_…)"; a potência somada é calculada neste relatório.
  - **Seção 1**: na usina com esta seção, a tabela de trechos fica sem a coluna "Composição (CEG)", que passa a esta seção, com os nomes das usinas, e a tabela dos conjuntos do ONS ganha a linha da Capacidade de geração das usinas do conjunto. Na usina sem conjunto, as tabelas não mudam.
  - **Notas** (só com esta seção): fora da série própria, o período começa na entrada da usina no conjunto (FR-054 da spec da Coleta de dados), e antes dela a geração do conjunto não inclui a usina; a composição de cada trecho vem da Composição dos conjuntos e a potência, das unidades da Capacidade de geração, pelo CEG de cada usina; a geração do conjunto não é dividida pela potência somada nem entre as usinas.
  - **Planilha**: as abas do conjunto da FR-038.
- **FR-047** (seção "Afluência, vertimento e nível do reservatório (ONS)" na hidrelétrica sem EVT): com os Dados hidrológicos (FR-061 da spec das Análises), a seção DEVE trazer:
  - **com a hora da hidrologia confirmada** pela geração da usina (FR-026 da spec da Conferência): a constatação "Afluência e vertimento", com a cobertura e o resultado do alinhamento; a tabela anual de afluência, vazões, nível e volume útil, com as colunas da tabela da hidrelétrica com EVT; a figura 15;
  - **sem a hora confirmada**: só a constatação, com a cobertura e o resultado da conferência;
  - **legendas**: "Dados hidrológicos horários (cod_usina …, reservatório …)", com a conferência da hora pela geração da usina;
  - sem a tabela e a figura das faixas de afluência da EVT e sem o perfil por hora do dia, que comparam os dias com parada com EVT;
  - **notas** (só com a seção): dados informados pelos agentes e não consistidos pelo ONS; a hora de fim convertida para a de início, conferida pela correlação entre a vazão turbinada e a geração da usina, e não pela EVT, que a usina não tem; valores fora da faixa física sinalizados e retirados só do campo afetado; campo vazio não é zero;
  - **planilha**: as abas dos Dados hidrológicos da usina sem EVT da FR-038.
- **FR-048** (relatório em duas partes): na usina em conjunto sem série própria, em que todos os números de operação são do conjunto (série de referência = Geração por usina do conjunto), com a seção do conjunto, o relatório DEVE ter duas partes:
  1. **a usina**: a seção "A usina no conjunto", logo depois da fonte e cobertura dos dados, com:
     - o que o ONS publica da usina isolada (a ficha do cadastro, na capa; as unidades geradoras e a entrada no conjunto; as linhas próprias na Geração por usina, todas sem valor, com o período) e o que não publica (a geração, a disponibilidade e os indicadores);
     - onde a geração da usina isolada pode ser obtida: a medição da CCEE e os registros do agente, que o relatório não usa, porque se limita aos dados abertos do ONS;
     - a tabela do peso da usina na potência do conjunto, por composição: composição, início, fim, potência da usina, potência das usinas do conjunto e peso, com "—" enquanto as unidades da usina não estão em operação. É um fato do cadastro, não uma estimativa da geração da usina;
     - a constatação "A usina no conjunto" (FR-060 da spec das Análises).

     As seções com base própria da usina, quando há, continuam no lugar delas.
  2. **o conjunto**: a seção "Operação do conjunto <nome> (<id>)", depois da qualidade dos dados e antes da conclusão, com as subseções "Indicadores anuais do conjunto", "Série temporal da geração do conjunto", "Geração mensal e sazonalidade do conjunto", "Perfil horário da geração do conjunto", a composição e a geração por trecho (FR-046) e "Programação diária × geração verificada do conjunto", quando há. As constatações dos números do conjunto (geração, programação e composição) ficam no início dela.
  - As seções dos números do conjunto saem do corpo principal: aparecem só como subseções da parte do conjunto.
  - A eólica ou solar em conjunto com série própria mantém a estrutura da FR-046.
  - **Planilha**: a aba CONJ_PESO_USINA. **Resumo executivo**: remete à seção da operação do conjunto para a evolução anual (FR-061).

**Relatório de carteira (US10)**

- **FR-049** (relatório de carteira): `python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao "DD/MM/AAAA HH:MM"]`, com pelo menos uma das duas opções, DEVE gerar o relatório em `reports/carteiras/<nome>/` (`<nome>` = `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`, em minúsculas) só com o que já está gravado: o catálogo, os perfis e os resultados das Análises. Nenhuma etapa é executada, e o portal não é consultado.
  - **Recorte**: as linhas do catálogo (`usinas.csv`) do estado, do tipo ou dos dois. As linhas de conjunto não contam como usina.
  - **Com resultado**: a usina com perfil achado pelo CEG, conferido e válido, e com as Análises `concluida` no formato atual, com `indicadores_carteira` (FR-062 da spec das Análises).
  - **Sem resultado**: um motivo por usina, o primeiro desta ordem:
    1. só agregado no ONS (ver o panorama): cobertura `agregado` no catálogo;
    2. sem perfil;
    3. perfil em rascunho;
    4. perfil inválido, inclusive dois perfis com o mesmo CEG (com os dois slugs);
    5. Análises ausentes, em formato antigo (inclusive sem os indicadores da carteira), com falha ou desatualizadas, com o slug da usina.
    - A lista traz também a cobertura do catálogo (própria, conjunto, agregado ou ausente), que mostra quais usinas têm série no ONS para um perfil.
  - **Conteúdo**, nesta ordem, no PDF e no Markdown:
    1. **capa**: título "Relatório de carteira — <recorte>", o recorte, a data do catálogo, as linhas de conjunto que não contam como usina, a quantidade de usinas com e sem resultado e a data de geração;
    2. **usinas com resultado**: nome (e a UF, na carteira sem estado), tipo, modalidade, potência, cobertura, nível da geração e período da série;
    3. **indicadores comparáveis** (FR-062 da spec das Análises): uma linha por usina, com o ano dos indicadores, o último ano completo da série (o ano parcial, marcado, quando não há). Entram só as colunas que se aplicam a algum tipo do recorte (fator de capacidade, disponibilidade, TEIFa, energia cortada e atendimento ao despacho), com "—" onde não se aplica ou falta a base; o valor de conjunto ou de agregado vem identificado ("(do conjunto)"); a TEIFa traz o mês quando não é a de dezembro, e o atendimento, as horas;
    4. **ordenação pelos itens da conclusão**: possíveis problemas (decrescente), pontos de atenção (decrescente) e nome, com a posição, as quatro contagens de todos os itens de cada lista e as regras avaliadas ("n de m"). As usinas sem regra avaliada com dado da usina vêm no fim, sem posição, com a frase de que a conclusão delas não tem base no nível da usina e de que a falta de itens não quer dizer falta de indício; a figura 1;
    5. **usinas sem resultado**: nome (e a UF), tipo, modalidade, cobertura e motivo de cada uma, com a quantidade por motivo;
    6. **panorama** (só com `--estado`): os agregados do estado (`agregados.csv`) dos 12 últimos meses completos do catálogo, por modalidade e tipo do ONS e por mês, com a energia (MWh); "sem valor" no mês em que nenhum grupo da série tem hora com valor, e não zero; as horas com valor, as sem valor e as ausentes, por grupo; a figura 2. Os agregados vêm identificados como agregado, com os valores das usinas Tipo III marcados como previsão do ONS, e não são atribuídos a nenhuma usina. Com `--estado` e `--tipo`, só o tipo do ONS correspondente: hidrelétrica (UHE, PCH e CGH, que o agregado não separa), térmica (UTE e UTN), fotovoltaica ou eólica. Sem agregado publicado no período, uma frase diz isso;
    7. **notas**: as fontes (o catálogo, com a data, e os resultados das Análises de cada usina, com a data de conclusão), as definições dos indicadores, os níveis dos dados, o motivo da omissão do panorama na carteira só por tipo e a frase de que a carteira não atribui nota nem parecer: a ordenação só conta os itens da conclusão de cada usina, que dependem das regras avaliadas e do período de cada uma.
  - **Legendas**: logo abaixo de cada tabela e de cada figura, "Fonte dos dados: …" ou "Calculado neste relatório a partir de: …", com a mesma origem da aba FONTES.
  - **Figuras em seaborn**:
    - `01_itens_da_conclusao_por_usina.png`: itens da conclusão por usina, na ordem da ordenação, em barras horizontais empilhadas pelas quatro listas, na ordem da conclusão, com legenda;
    - `02_panorama_agregados_mensal.png` (com o panorama): energia mensal dos agregados em barras empilhadas por modalidade e tipo, com a previsão Tipo III identificada na legenda.
  - **Planilha** `carteira.xlsx`: abas `USINAS`, `INDICADORES` (valor, nível e unidade de cada indicador), `ORDENACAO`, `SEM_RESULTADO`, `PANORAMA` (na carteira só por tipo, só com o motivo da omissão) e `FONTES`, com as colunas da aba FONTES do relatório da usina (FR-028).
  - **Gravação**: pasta temporária, conferência e troca, como no relatório da usina, sem `.bak`; a figura de uma execução anterior que não tem mais base é apagada. O PDF é A4 retrato e, com `--data-geracao`, reproduzível byte a byte.
  - **Textos**: nenhum termo de parecer ("satisfatório", "insatisfatório", "cumpre", "descumpre" ou equivalente), conferido por teste.
  - **Códigos e mensagens**: os do [contrato](contracts/cli-carteira.md) (0, 1, 2 e 5).

**Resumo executivo: geração e formato (US11)**

- **FR-050**: Cada execução que gera o relatório completo de uma usina DEVE gerar também o resumo executivo dela. O resumo usa os mesmos resultados das Análises e tem a mesma data de geração e o mesmo período do relatório.
- **FR-051**: Executar só a Geração do relatório DEVE gerar o relatório e o resumo a partir dos resultados já gravados, sem refazer as etapas anteriores. Não há comando que gere só o resumo, para que ele nunca fique ao lado de um relatório de outra execução. Sem os resultados das Análises, a execução DEVE parar sem gravar nada e indicar a etapa a executar.
- **FR-052**: O resumo DEVE sair em PDF e em Markdown, com o mesmo conteúdo na mesma ordem, na pasta de relatórios da usina, ao lado do relatório completo.
- **FR-053**: O PDF do resumo DEVE ter no máximo duas páginas A4, em retrato. Ele usa a identidade visual do relatório completo, com texto em corpo mínimo de 10 pt e tabelas em corpo mínimo de 9 pt.
- **FR-054**: O resumo NÃO DEVE ter figuras. Pode ter no máximo duas tabelas: os indicadores-chave e a evolução anual.
- **FR-055**: Quando o conteúdo passar de duas páginas, o resumo DEVE omitir a evolução anual, informando a seção de origem no relatório completo. Se ainda não couber, a geração DEVE acusar o erro e não gravar o resumo. A conclusão nunca é cortada, e fonte e margens nunca ficam abaixo do mínimo da FR-053.

**Resumo executivo: estrutura (US11)**

- **FR-056**: O resumo DEVE ter os blocos nesta ordem fixa:
  1. cabeçalho;
  2. indicadores-chave;
  3. evolução anual;
  4. "Sobre os dados";
  5. conclusão.

  Um bloco sem base para a usina é omitido (constituição, princípio II).
- **FR-057**: O **cabeçalho** DEVE trazer:
  - nome, tipo, estado, modalidade de operação e potência da usina;
  - os agentes, cada um com o seu período; nas usinas sem EVT, cujos dados não trazem o histórico dos agentes, o agente atual de cada unidade como a Capacidade de geração do ONS o traz, identificado como tal ("Agente atual (Capacidade de geração do ONS)");
  - o período analisado e a data de geração;
  - a referência ao relatório completo: título, data e número de páginas.
- **FR-058**: A **conclusão** DEVE ser a da seção de conclusão do relatório completo da mesma execução, copiada igual: a frase de abertura, as listas, os itens, a ordem e o texto, caractere por caractere. O resumo NÃO DEVE resumir, reescrever, reordenar, acrescentar ou retirar itens da conclusão. Uma lista sem itens no relatório completo também não aparece no resumo.
- **FR-059**: Logo abaixo do título da conclusão, o resumo DEVE informar, numa linha, que as seções e as notas metodológicas citadas são as do relatório completo.
- **FR-060**: Os **indicadores-chave** DEVEM ser os indicadores principais da capa do relatório completo para o tipo da usina, em uma tabela, com o valor e, quando houver, a referência e a diferença para ela, sem juízo.
- **FR-061**: A **evolução anual** DEVE ser uma tabela com uma linha por ano e no máximo seis colunas, com os indicadores anuais do tipo da usina, tirados da tabela anual do relatório completo:
  - na hidrelétrica com EVT: disponibilidade, fator de capacidade, geração ÷ garantia física, EVT e horas paradas com EVT;
  - na usina sem EVT, as que a tabela anual da usina tem, nesta ordem: o nível, a geração média, a energia, o fator de capacidade (eólicas e solares), a disponibilidade (quando o ONS a publica) e o principal indicador de perda do tipo: nas térmicas, as horas disponíveis sem despacho; nas eólicas e solares, a energia cortada, em MWh e em % da estimada.

  Os anos parciais vêm marcados. A tabela indica a seção de origem no relatório completo; no relatório em duas partes, a seção da operação do conjunto.
- **FR-062**: **"Sobre os dados"** DEVE ter no máximo 250 palavras, com:
  - a cobertura e os anos parciais; na usina sem EVT, a série de referência, com o identificador e o nível, e as horas ausentes;
  - o resultado resumido das conferências feitas; na usina sem EVT, só as aplicadas à usina;
  - a quantidade e a parcela de registros sinalizados;
  - o que os dados não informam, como a causa das paradas e os eventos individuais;
  - numa linha, as fontes: os conjuntos do ONS, com o identificador e o nível, como nas legendas (FR-024), e as datas de obtenção.

  Esse bloco substitui a legenda de fonte de cada tabela.

**Resumo executivo: fidelidade e linguagem (US11)**

- **FR-063**: Todo número do resumo DEVE ser idêntico, em valor, unidade e arredondamento, a um número do relatório completo. O resumo NÃO DEVE trazer número que não esteja no relatório completo.
- **FR-064**: Nenhum nome, número ou frase própria de uma usina DEVE ficar fixo. Tudo vem dos resultados, do perfil da usina e das regras gerais (constituição, princípio II).
- **FR-065**: Todo número de conjunto de usinas ou de agregado DEVE vir identificado pelo nível em que é publicado. Nenhum número de conjunto é apresentado como da usina (constituição, princípio VIII).
- **FR-066**: Fora da conclusão, que é copiada igual, o texto do resumo DEVE ser legível por quem não é especialista em operação:
  - siglas por extenso na primeira ocorrência;
  - uma linha de termos que explica as grandezas técnicas citadas, como a energia vertida turbinável, só com os termos que aparecem no resumo, na ordem da primeira ocorrência, com o texto do glossário das regras gerais aprovado pelo usuário (inclusive CVU, CMO e constrained-off);
  - frases curtas, na voz ativa.
- **FR-067**: Os números DEVEM seguir o padrão do relatório completo: milhar com ponto, decimal com vírgula, datas "dd/mm/aaaa HHh", meses "mmm/aaaa" e "–" para valor ausente.

**Resumo executivo: tipos de usina e referência (US11)**

- **FR-068**: O resumo DEVE ser gerado para todos os tipos de usina que o fluxo atende. Cada tipo usa os seus indicadores-chave, os seus indicadores anuais e a conclusão do seu relatório completo.
- **FR-069**: O resumo aprovado pelo usuário DEVE fazer parte da referência da usina (FR-042). A comparação dos relatórios de referência DEVE incluir o resumo (constituição, princípio IX).
- **FR-070**: A geração do resumo NÃO DEVE mudar o relatório completo nem a planilha. A comparação com a referência da São Domingos não pode acusar diferença neles por causa do resumo.
- **FR-071** (taxas operativas): Com a comparação das taxas (FR-063 da spec das Análises), a seção dos indicadores oficiais do ONS DEVE trazer, logo depois da decomposição das taxas, nas duas trilhas:
  - a tabela "TEIFa e TEIP mais recentes: taxas oficiais e operativas do ONS" (taxa, oficial, operativa e diferença em p.p., com o sinal do valor arredondado), com a frase da série como introdução; com as diferenças nulas em todos os meses, a frase diz que as taxas coincidem;
  - a figura `09_taxas_oficiais_e_operativas.png` (trilha da EVT) ou `16_taxas_oficiais_e_operativas.png` (trilha sem EVT), só com algum mês com diferença de pelo menos 1 p.p.: dois painéis, TEIFa e TEIP, a oficial em linha cheia e a operativa tracejada;
  - as legendas com os dois conjuntos, a aba `ONS_TAXAS_OPERATIVAS` e a linha dela na aba FONTES;
  - nas notas, a descrição das taxas operativas pelo dicionário do ONS, que não publica a diferença de regra; na usina com as taxas oficiais e sem as operativas, a nota de que elas não constam dos dados coletados, sem tabela.

  O conjunto das taxas operativas entra entre os carregados (rodapé) só quando há a comparação.

### Key Entities

- **Relatório da usina**: PDF, Markdown, planilha, CSV, figuras, resumo executivo e `etapa.json`, em `reports/<slug>/`, com a data de geração.
- **Caminho do relatório**: hidrelétrica com EVT ou usina sem EVT; define as seções, a capa, as legendas, as notas e as figuras.
- **Seção**: título (fixo, por tipo ou pelos resultados), ordem, caminhos e tipos em que existe, condição de presença, número entre as presentes, conteúdo e constatações.
- **Constatação**: título e texto gerados pelas Análises, e a seção em que aparece.
- **Capa**: título, subtítulo, blocos de identificação, cadastro e parâmetros, indicadores principais e sumário.
- **Nível do dado**: usina, conjunto de usinas ou agregado, escrito com o identificador nas legendas e nos rótulos.
- **Legenda de fonte**: conjuntos de origem (nome, identificador com o nível e data de obtenção), conferências com o resultado, dados sem outra fonte e indicação de cálculo do relatório.
- **Mapa de fontes**: para cada figura, tabela, bloco e aba, os elementos da legenda.
- **Conferência citada**: dado conferido, conjunto que permite a conferência e resultado gravado pela Conferência.
- **Item da conclusão, na apresentação**: lista, ordem, regra, texto e seções de origem, com o rótulo "(seção N)".
- **Figura**: arquivo, conteúdo, condição de geração e se é padronizada.
- **Aba da planilha**: nome, grupo, condição de presença e linha na FONTES.
- **Diferença do `comparar`**: arquivo e, na planilha, aba e célula.
- **Relatório de referência**: relatório aprovado de uma usina, com a Coleta e o perfil congelados e o `referencia.json`, em `relatorios_referencia/<slug>/`.
- **Resumo executivo**: o documento de até duas páginas de uma usina, gerado junto com o relatório completo e com a mesma data e o mesmo período, formado pelos blocos da FR-056.
- **Indicadores-chave**: os indicadores principais da capa do relatório completo para o tipo da usina.
- **Evolução anual**: os indicadores anuais do tipo da usina, um ano por linha.
- **Relatório de carteira**: as usinas de um estado, de um tipo ou dos dois, com o quadro, os indicadores comparáveis, a ordenação pelos itens da conclusão, as usinas sem resultado com o motivo e o panorama agregado do estado.

---

## Aplicabilidade por tipo

**Relatório da usina**

"Hidrelétrica com EVT" é a UHE, PCH ou CGH com série própria na Energia Vertida Turbinável. "Usina em conjunto sem série própria" é a que o ONS publica só pela geração do conjunto de usinas (as PCH e CGH Tipo II-C).

| Elemento | Hidrelétrica com EVT | UHE, PCH, CGH sem EVT | UTE, UTN | EOL, UFV |
|---|---|---|---|---|
| Estrutura e numeração | as 17 seções da FR-007 | FR-041 | FR-041 | FR-041 |
| Título e capa | FR-011 a FR-013 | mesmo título; identificação com tipo, modalidade e agente atual; parâmetros do tipo | os mesmos, com o subsistema e os códigos de planejamento | os mesmos |
| Indicadores da capa | os cinco da FR-013 | geração média, horas até 1 MW, disponibilidade, DISPF | geração média, horas com despacho, disponibilidade, DISPF com a TEIFa | geração média, fator de capacidade, energia cortada |
| Seções do tipo | EVT, eventos de parada, vazões, horas com geração zero | afluência sem a EVT (FR-047), com os Dados hidrológicos | térmica (FR-044), com o despacho | eólica e solar (FR-045), com as bases |
| Seção do conjunto (FR-046) | não se aplica | usina em conjunto com a geração do conjunto | não se aplica | usina em conjunto com a geração do conjunto |
| Relatório em duas partes (FR-048) | não se aplica | usina em conjunto sem série própria | não se aplica | não se aplica: a usina com série própria mantém a FR-046 |
| Tabela de trechos da seção 1 | não há trechos | com a coluna de composição; sem ela na usina com a seção do conjunto | com a coluna de composição | sem a coluna de composição na usina com a seção do conjunto |
| Legendas | identificador da usina (FR-025) | com o nível quando o dado é de conjunto ou de agregado (FR-024) | idem, com o CMO "subsistema, agregado" | idem |
| Conferências nas legendas | as seis da FR-026 | TEIFa e TEIP, DISPF, cadastro e a hora da hidrologia pela geração | TEIFa e TEIP, DISPF, cadastro, G3 e G4 | cadastro, G1, G2 e G5, as aplicadas |
| Conclusão | C1 a C11, com a frase da FR-030 | regras comuns C2, C5, C8 e C10; na usina em conjunto sem série própria, sem itens, com a frase | C2, C5, C8, C10 e C12 a C15 | C16 a C19, só com dado da usina |
| Nota da conclusão | o texto da FR-033 | gerada do catálogo do tipo | gerada do catálogo do tipo | gerada do catálogo do tipo |
| Notas metodológicas | FR-020, sem parágrafo novo | FR-020, com as omissões, os níveis e as conferências não aplicáveis | idem, com a nota das térmicas | idem, com a nota das eólicas e solares |
| Figuras | 01 a 08 (FR-034) | 01 a 05, 14 e 15, conforme as bases | 01 a 05 e 06 a 09 | 01 a 04, 10 a 13 e 14, conforme as bases |
| Planilha | as abas da FR-038 (58 na São Domingos); DICIONARIOS com os dez conjuntos | abas do caminho sem EVT, com HID_* e CONJ_* | idem, com TERM_* e CONF_G3/G4_* | idem, com REN_*, CONF_G1/G2/G5_* e CONJ_* |
| Resumo executivo: evolução anual | Ano, Disp. média, fator de capacidade, geração ÷ GF, EVT, horas paradas com EVT | Ano, nível, geração média, energia, disponibilidade | Ano, nível, geração média, energia, disponibilidade, horas disponíveis sem despacho | Ano, nível, geração média, energia, fator de capacidade, energia cortada |

**Relatório de carteira, por recorte**

| Elemento | `--estado` | `--estado` e `--tipo` | `--tipo` |
|---|---|---|---|
| Pasta | `<uf>` | `<uf>_<tipo>` | `brasil_<tipo>` |
| Quadro, indicadores, ordenação e sem resultado | todas as usinas do estado | as usinas do tipo no estado | as usinas do tipo no Brasil |
| Indicadores | os que se aplicam a algum tipo do estado | os do tipo | os do tipo |
| Panorama | todos os tipos do ONS | o tipo do ONS correspondente | omitido, com o motivo nas notas |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (não regressão): Com o perfil e a Coleta congelados da São Domingos (`relatorios_referencia/sao_domingos/`), o relatório refeito é idêntico ao de referência. A referência é o relatório gerado com a data "07/10/2026 08:53" e aprovado pelo usuário em 19/10/2026: o aprovado em 07/10/2026, com a conclusão aprovada, os dois textos que citavam caminhos do código já reformulados, o rótulo das horas paradas sem programação corrigido em 08/10/2026, as edições do usuário no título da capa e nos títulos das figuras 02 e 06 e o resumo executivo (Decisões do usuário):
  - PDF com 30 páginas e o mesmo texto;
  - Markdown idêntico;
  - planilha com as 58 abas idênticas célula a célula;
  - as 8 figuras e o CSV idênticos byte a byte;
  - o resumo executivo, em PDF e em Markdown, idêntico byte a byte;
  - nenhuma destas afirmações, contraditas pelos dados: "96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained".

  O `comparar --todas` não aponta nenhuma diferença no relatório refeito.
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
  - o PDF é válido com e sem as figuras;
  - as usinas fictícias dos sete tipos têm o relatório e o resumo completos, cada uma com as seções do seu caminho, sem o identificador de outra usina.
- **SC-011**: Em 100 % das tentativas de gerar o relatório sem as Análises concluídas, a etapa sai com código 5 e não grava nada.
- **SC-012**: Com os resultados das Análises já gravados, a etapa termina em até 1 minuto para uma série horária de oito anos com todos os conjuntos. A carteira de MS sai em até 5 minutos a partir dos resultados gravados.
- **SC-013**: As hidrelétricas com EVT passam nos testes dos invariantes do relatório (decisão técnica D17 do plano): seções, títulos, ordem e numeração; capa e título; legendas; conferências citadas; conclusão e nota; nenhum trecho nem parágrafo de granularidade; notas; abas, colunas e dicionários da planilha; arquivos e colunas da Coleta; Markdown completo.
- **SC-014**: Depois de cada mudança do código, `comparar --todas --coleta` não aponta diferença em nenhum relatório refeito a partir da Coleta congelada. Na Coleta refeita, só contam como aprovadas, até o próximo congelamento da referência, as diferenças de dados republicados ou acrescentados pelo ONS depois do congelamento, aceitas pelo usuário.
- **SC-015**: 100 % dos resumos gerados têm no máximo duas páginas A4 e nenhuma figura. Isso vale para a São Domingos, para as usinas fictícias de cada tipo e para o caso de teste com cinco itens em cada lista da conclusão.
- **SC-016**: 100 % das conclusões dos resumos são iguais, caractere por caractere, às dos relatórios completos da mesma execução, por verificação automática.
- **SC-017**: 100 % dos números das tabelas e do texto do resumo conferem com o relatório completo da mesma execução, em valor, unidade e arredondamento, por verificação automática.
- **SC-018**: O resumo é lido em até 5 minutos: no máximo 1.000 palavras fora das tabelas.
- **SC-019**: Só com o resumo da São Domingos, um leitor que não leu o relatório completo responde a cinco perguntas:
  - quais são os principais indícios;
  - qual o tamanho de cada um;
  - desde quando ocorrem;
  - o que pode estar por trás deles;
  - o que será pedido ou verificado.

  O usuário aprova o resumo como representação fiel do relatório de referência.
- **SC-020**: A comparação com a referência da São Domingos não acusa diferença no relatório completo nem na planilha por causa do resumo executivo.

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
| 09/10/2026 | O fluxo passa a atender todos os tipos de usina que os dados abertos do ONS cobrem (UHE, PCH, CGH, UTE, UTN, EOL e UFV), com os indícios da conclusão só com dado da usina. Os relatórios aprovados ficam guardados com a Coleta e o perfil congelados e são comparados num espaço isolado. | FR-007, FR-041 a FR-043, SC-001, SC-013, SC-014 |
| 13/10/2026 | As hipóteses do resumo executivo são a conclusão do relatório completo, copiada igual; não há catálogo de hipóteses próprio do resumo. | FR-058 |
| 13/10/2026 | Não há comando só do resumo: executar a Geração do relatório gera o relatório e o resumo. "Sobre os dados" tem no máximo 250 palavras, porque a constituição exige nele as mesmas informações de fonte e de conferência das legendas. | FR-051, FR-062 |
| 13/10/2026 | Depois de ver o resumo da São Domingos ("ficou EXCELENTE!"), a conclusão passa para o fim: cabeçalho, indicadores-chave, evolução anual, "Sobre os dados" e conclusão. | FR-056 |
| 13/10/2026 | O resumo executivo é implementado antes de concluída a ampliação para todos os tipos; a conferência de que o relatório completo não mudou é feita contra o relatório gerado pelo código anterior ao resumo. | FR-070, SC-020 |
| 19/10/2026 | Relatório da São Domingos aprovado ("esse relatório está aprovado"), com o resumo executivo, as edições do usuário no título da capa ("<nome da usina> — Análise do desempenho operacional") e nos títulos das figuras 02 e 06 e o texto da linha de termos; registrado como referência, com a data de geração "07/10/2026 08:53" e aprovado em 19/10/2026. | FR-011, FR-066, FR-069, SC-001 |
| 19/10/2026 | Ajustes da conferência do código contra os requisitos, aprovados ("aprovado, siga"): na usina sem EVT, o mesmo título da capa aprovada, que não cita a EVT; a mesma conclusão nos dois caminhos; o título da série temporal por tipo; a afluência das hidrelétricas sem EVT numa seção própria, sem os cruzamentos com a EVT. | FR-011, FR-029, FR-030, FR-041, FR-047 |
| 19/10/2026 | Nas usinas sem EVT, cujos dados não trazem o histórico dos agentes, a capa e o resumo mostram o agente atual (proprietário e operador) das unidades ativas, da Capacidade de geração, identificado como tal ("Mostrar agente atual"). | FR-011, FR-057 |
| 19/10/2026 | As diferenças da Coleta refeita causadas por republicação do ONS (cadastro; indicadores e taxas) contam como aprovadas no `comparar --todas --coleta` até o próximo congelamento da referência; o relatório refeito a partir da Coleta congelada continua tendo de dar "nenhuma diferença". | FR-043, SC-014 |
| 19/10/2026 | O resumo executivo entra nesta spec junto com a ampliação para todos os tipos, numa edição só. | FR-050 a FR-070 |
| 20/10/2026 | CVU zero sinalizado como o ausente e o negativo, mantido e fora da comparação com o CMO ("Zero fica fora"); a tabela CVU × CMO mostra também as semanas com o CVU igual ao CMO. Textos do glossário do resumo para CVU e CMO aprovados como estão. | FR-044, FR-066 |
| 20/10/2026 | Relatório e resumo executivo da UTE William Arjona aprovados ("aprovo o relatório e o sumário executivo") e registrados como referência. | FR-042, FR-044 |
| 21/10/2026 | Geração estimada 0 com a usina gerando acima de 1 MW é estimativa ausente: sinalizada, contada, fora dos totais e das médias da estimada; na semi-hora restrita, o corte não é calculado, e a tabela anual mostra as restritas sem estimativa. | FR-045 |
| 21/10/2026 | Limite físico do recurso: vento acima de 40 m/s e irradiância acima de 1.500 W/m² ficam fora das faixas e são contados. Glossário do resumo: "constrained-off: redução da geração da usina por comando do ONS, por razão externa a ela (indisponibilidade externa, confiabilidade elétrica ou razão energética)". | FR-045, FR-066 |
| 21/10/2026 | Na eólica ou solar com série própria, com a programação e a geração publicadas pelo conjunto, a programação é comparada com a geração do conjunto, identificada como tal. Relatórios e resumos da UFV Seriemas 1 e da EOL Praia Formosa aprovados ("estão excelentes") e registrados como referência. | FR-041, FR-042, FR-045 |
| 22/10/2026 | A seção do conjunto entra em toda usina em conjunto, inclusive com série própria; a potência das usinas da composição entra, sem dividir número do conjunto e sem fator de capacidade do conjunto. A hora dos Dados hidrológicos da hidrelétrica sem EVT é conferida pela geração da usina (−1, 0 e +1 h), sem meta. | FR-046, FR-047 |
| 22/10/2026 | Depois de ver o relatório da PCH Bandeirante: relatório em duas partes na usina em conjunto sem série própria (a usina, logo depois da fonte e cobertura; a operação do conjunto, logo antes da conclusão), com o peso da usina na potência do conjunto por composição, só a potência, sem estimar a geração. A geração da usina isolada pela medição da CCEE fica como proposta para uma mudança futura; o relatório diz onde ela pode ser obtida. | FR-048 |
| 22/10/2026 | Relatório e resumo da PCH Bandeirante aprovados ("o resto está ok"), com as mudanças da Seriemas 1 (seção do conjunto e a linha "Fontes" do resumo com o nível); as duas referências registradas de novo. As diferenças da Coleta da William Arjona e da Praia Formosa por dados que o ONS publicou depois do congelamento contam como aprovadas, como as da São Domingos. | FR-042, FR-043, FR-046, FR-048, FR-062 |
| 22/10/2026 | Carteira: indicadores do último ano completo da série; atendimento ao despacho pelas horas a até 5 MW da programada; contagens vazias, e não zero, quando nenhuma regra foi avaliada com dado da usina; fator de capacidade só onde o relatório da usina o calcula; "só agregado no ONS" como primeiro motivo, com a cobertura do catálogo; duas figuras. | FR-049 |
| 23/10/2026 | Carteira de MS aprovada ("aprovo a carteira de MS"). O relatório atualizado da São Domingos fica em `reports/sao_domingos/`, com a série até 19/10/2026; a referência continua a aprovada. | FR-049, SC-001 |
| 23/10/2026 | Taxas operativas no relatório: tabela, frase, figura com diferença de pelo menos 1 p.p., notas e aba; carteira sem coluna nova (aprovado pelo usuário). | FR-071 |
| 26/10/2026 | Aprovados os relatórios da São Domingos e da William Arjona com as taxas operativas, a mudança da PCH Bandeirante (C20 entre as regras não avaliadas e o PDF de 13 para 14 páginas) e a fotografia nova da hidrelétrica fictícia; referências das três usinas registradas de novo. | FR-071, princípio IX |
| 29/10/2026 | Diferença aprovada na referência da PCH Bandeirante ("aceito suas recomendações"): duas células da tabela "Geração programada × verificada por mês", de jan/2025 e ago/2025, passam de "-0,0" a "0,0" (bug `zero-negativo-tabela`). O novo registro é feito na máquina que tem a Coleta congelada, com a data de geração de 22/10/2026 (passos em `.specify/bugs/zero-negativo-tabela/fix.md`). | FR-042, princípio IX |

---

## Assumptions

- **Entradas prontas**:
  - Os resultados das Análises trazem os dados de cada tabela e figura, inclusive as médias diárias da figura 01 e as médias anuais das vazões da figura 05, além das constatações, dos itens da conclusão, das seções comuns e do tipo das usinas sem EVT, das seções e regras sem base, com o motivo, e dos indicadores da carteira.
  - Os resultados de conferência chegam dentro dos resultados das Análises, como a Conferência os grava, com as conferências que não se aplicam à usina.
  - Esta etapa só formata e organiza.
- **Fronteira com as outras etapas**:
  - **Análises**: textos das constatações e dos itens da conclusão, catálogo das regras por tipo, limiares, termos proibidos, níveis dos dados, seções omitidas e indicadores da carteira.
  - **Conferência**: as seis conferências da hidrelétrica com EVT, a G1 a G5 e a hora da hidrologia pela geração, com as tolerâncias, e as conferências que não se aplicam, com o motivo.
  - **Coleta**: perfil da usina, regras comuns, comando `completo`, ferramenta `copia-seguranca` (que leva os relatórios de referência), catálogo de usinas e datas de obtenção de cada conjunto.
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
- **Referência**: os relatórios de referência ficam em `relatorios_referencia/<slug>/`, com a Coleta e o perfil congelados (FR-042), e são copiados para cada cópia de segurança do projeto. O `comparar --todas` os refaz a partir deles; o `comparar --usina --referencia` compara com qualquer pasta de mesma estrutura.
- **Ambiente**: o ambiente é o mesmo da referência, com Windows, fonte Arial e as mesmas versões das dependências. Em outro ambiente, os bytes do PDF e das figuras podem mudar sem mudar o conteúdo.
- **Desempenho**: o limite de 1 minuto supõe os resultados das Análises já gravados e não inclui as etapas anteriores.
- **Granularidade**: o ONS publica as eólicas e solares quase sempre em conjunto; a série da própria usina existe nos conjuntos de restrição. A geração das PCH em conjunto vem vazia no ONS, e o relatório usa a do conjunto. As pequenas usinas e a MMGD aparecem em grupos por área do estado, usados no panorama da carteira. As usinas nucleares são tratadas como térmicas.
- **Leitor do resumo**: diretor ou executivo da AGEMS, sem formação específica em operação de usinas, que lê o resumo em PDF ou impresso.
- **Ordem dos blocos do resumo**: primeiro os números (indicadores, evolução anual e limites dos dados), depois a conclusão, que fecha o documento, como no relatório completo. A linha de termos fica no cabeçalho, antes de todos os blocos.
- **Sem bloco de mensagens-chave nem de próximos passos no resumo**: os pontos de atenção da conclusão já são os principais achados, com os números. As listas "A confirmar com o agente" e "A verificar em campo" já são os próximos passos. Blocos à parte repetiriam a conclusão e ocupariam o espaço das duas páginas.
- **Formatos do resumo**: PDF e Markdown, como o relatório completo, em A4 retrato, com a identidade visual do relatório. Word e planilha própria do resumo ficam fora.
- **Origem automática do resumo**: o resumo é gerado inteiramente pelo fluxo. Não há campo de texto livre do fiscal, porque a constituição (princípio II) exige que todo texto venha dos dados, do perfil ou das regras gerais.
- **Carteira**: não tem resumo executivo próprio; ele pode entrar numa mudança futura.
- **Idioma**: português do Brasil.
