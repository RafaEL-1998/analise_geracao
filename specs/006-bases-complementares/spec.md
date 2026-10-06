# Feature Specification: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança dos Dados Processados - UHE São Domingos

**Feature Branch**: `006-bases-complementares`

**Created**: 2026-10-05

**Status**: Implementado (05/10/2026)

**Input**: User description: "Bases complementares do ONS e backup dos dados processados (spec 006). (1) Antes de sobrescrever qualquer arquivo em data/processed/, guardar a versão anterior como <arquivo>.bak e validar fisicamente a nova gravação (Requisito Técnico 3 da constituição; reports/ continua dispensado de .bak). (2) Incluir no pipeline, com download local, extração somente da UHE São Domingos (MS) e recorte no período da base de Energia Vertida Turbinável: prioridade 1 — Disponibilidade horária por usina (disponibilidade_usina; id ONS MSUHSD e CEG UHE.PH.MS.028761-0.01; a usina aparece desde 01/2023; disponibilidade operacional e sincronizada), para conferir a disponibilidade declarada, e Dados hidrológicos horários (dados_hidrologicos_ho; cod_usina 153 e reservatório SAO DOMINGOS; vazão afluente, defluente, turbinada e vertida, níveis de montante e jusante; convenção de fim de hora), para explicar o vertimento (afluência versus capacidade de turbinamento); prioridade 2 — Geração por usina (geracao-usina-2; MSUHSD), para conferência independente da geração; prioridade 3 — Modalidade das usinas (modalidade-usina; cadastro sem série histórica), para identificar a usina no relatório. (3) Cruzamentos com a base EVT e a programação diária e seções novas no relatório (Markdown, planilha e PDF), com gráficos em seaborn. (4) Fora do escopo: Classificação de EVT (só agregado do SIN) e bases da CCEE/ANEEL. Manter a base EVT local sem novo download. Prazo: fiscalização presencial de 14 a 16/10/2026; a prioridade 1 deve estar pronta antes."

---

## Contexto

A base de Energia Vertida Turbinável (EVT, specs 001 a 003), os indicadores oficiais por unidade geradora e a programação diária (spec 004) mostram o que a usina gerou, o que declarou disponível, quanto verteu de água que poderia ter sido turbinada e se seguiu a programação do ONS. Ainda faltam respostas para três perguntas da fiscalização:

- quando a usina estava disponível e parada, as unidades estavam desligadas da rede ou sincronizadas sem gerar?
- quanta água chegou ao reservatório e como o nível se comportou nas horas de vertimento?
- a geração analisada confere com a série oficial de geração por usina?

Esta spec inclui no pipeline as quatro bases abertas do ONS que respondem a essas perguntas e identificam a usina no cadastro do ONS.

A spec também fecha duas lacunas de conformidade:

- **Cópia de segurança**: o Requisito Técnico 3 da constituição exige cópia `.bak` dos dados processados, mas hoje os arquivos de `data/processed/` são regravados sem cópia.
- **Dicionários de dados**: o pipeline não obtém os dicionários de dados que o ONS publica para cada conjunto.

**Decisões do usuário em 05/10/2026**, tomadas depois da primeira versão desta spec e já incorporadas à constituição 1.2.0:

1. A cópia `.bak` serve para recuperar o estado anterior se o código falhar. Por isso vale só para os arquivos de `data/processed/`; manifestos, dicionários e demais arquivos de controle de baixo impacto ficam dispensados.
2. Os dicionários de dados (PDF e JSON) de todos os conjuntos DEVEM ser obtidos sempre, a cada coleta, para consulta sem acesso ao portal.
3. A constituição foi emendada para incluir os identificadores dos três conjuntos novos (princípio IV).

**Sondagem de 05/10/2026**, na amostra de jan/2025 cruzada com a base EVT local:

- A disponibilidade operacional publicada pelo ONS é igual à disponibilidade declarada da base EVT em 744 de 744 horas. A informação nova do conjunto é a **disponibilidade sincronizada**.
- As vazões turbinada e vertida dos dados hidrológicos são iguais às da base EVT em 744 de 744 horas, depois da conversão da convenção de fim de hora para a de início de hora.
  - As informações novas são a **vazão afluente**, a **vazão defluente**, os **níveis de montante e jusante** e o **volume útil**.
  - Em 695 das 709 horas com EVT do mês (98%), a afluência estava abaixo do engolimento máximo da usina (163 m³/s).
- A geração por usina é igual à geração da base EVT em 744 de 744 horas, com a energia do mês idêntica (23,054 GWh). Uma consulta de 02/10/2026 ao servidor de dados do ONS já tinha mostrado igualdade hora a hora de 2018 a 2026. A US5 torna essa conferência parte reproduzível do pipeline.
- **Correção**: a usina consta dos arquivos de disponibilidade pelo menos desde 09/2018 (720 h em 09/2018 e em 06/2021).
  - A informação anterior ("a usina aparece desde 01/2023"), repetida na descrição acima, vinha do formato compacto do conjunto, que o ONS publica apenas para 01–02/2015 e a partir de 01/2023.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cópia de segurança dos dados processados (Priority: P1)

Como fiscal da AGEMS, quero que toda regravação de um arquivo em `data/processed/` guarde antes a versão anterior e confira a nova gravação. Assim posso voltar à base que sustentou uma conclusão se uma nova execução produzir resultado inesperado ou for interrompida.

**Why this priority**: É exigência da constituição e pré-condição das demais histórias, que gravarão novos arquivos na mesma pasta. A base processada sustenta o relatório da fiscalização de 14 a 16/10/2026.

**Independent Test**: Numa pasta de teste, gravar o mesmo arquivo quatro vezes (sem versão anterior, com conteúdo alterado, com conteúdo idêntico e com falha simulada na gravação) e conferir o arquivo e a cópia `.bak` depois de cada passo.

**Acceptance Scenarios**:

1. **Given** um arquivo processado existente, **When** uma etapa o regrava com conteúdo diferente, **Then**:
   - a versão atual é guardada antes como `<nome do arquivo>.bak` na mesma pasta, substituindo a cópia anterior;
   - a nova versão é gravada;
   - a gravação é conferida no disco.
2. **Given** conteúdo novo idêntico ao atual, **When** a etapa é executada, **Then** o arquivo não é regravado e a cópia `.bak` existente é mantida. Assim, execuções repetidas não apagam a versão anterior.
3. **Given** uma falha durante a gravação ou na conferência, **When** ela é detectada, **Then** a versão anterior é restaurada, o arquivo é informado no log e a execução termina com código de erro.
4. **Given** cópias `.bak` na pasta de dados processados, **When** qualquer etapa lê dados processados, **Then** nenhuma cópia `.bak` é lida como dado.
5. **Given** um arquivo gravado pela primeira vez, **When** a etapa é executada, **Then** nenhuma cópia é criada e a gravação é conferida.

---

### User Story 2 - Dicionários de dados das fontes (Priority: P1)

Como fiscal, quero que cada coleta obtenha sempre os dicionários de dados (PDF e JSON) de todos os conjuntos usados no pipeline e os guarde junto aos dados brutos. Assim consulto a definição de cada campo sem acessar o portal e sei se o ONS mudou alguma definição entre uma coleta e outra.

**Why this priority**: O custo é pequeno e os dicionários documentam as fontes citadas no relatório da fiscalização. O catálogo do ONS não informa data nem tamanho desses arquivos, de modo que a única forma de saber se mudaram é obtê-los a cada coleta.

**Independent Test**: Simular três coletas de um conjunto (dicionários novos, dicionários iguais e dicionário alterado) e conferir os arquivos guardados, a versão anterior preservada e o registro de cada obtenção.

**Acceptance Scenarios**:

1. **Given** qualquer conjunto do pipeline (EVT, os quatro de indicadores oficiais, programação diária e os quatro desta spec), **When** a coleta é executada, **Then** os dicionários publicados (PDF e JSON) são obtidos e guardados junto aos dados brutos do conjunto, com a data de obtenção registrada.
2. **Given** um dicionário igual à cópia local, **When** obtido de novo, **Then** nenhuma versão nova é criada e o registro indica "inalterado".
3. **Given** um dicionário com conteúdo diferente da cópia local, **When** obtido, **Then** a versão anterior é preservada e a mudança é informada no log e na auditoria.
4. **Given** o conjunto EVT, **When** seus dicionários são obtidos, **Then** os arquivos de dados da base EVT não são obtidos de novo.
5. **Given** uma falha ao obter um dicionário (ou um conjunto sem dicionário publicado), **When** ela ocorre, **Then** a falha é registrada no log e na auditoria e as demais etapas continuam.

---

### User Story 3 - Disponibilidade operacional e sincronizada (Priority: P1)

Como fiscal, quero a disponibilidade horária da usina publicada pelo ONS (operacional e sincronizada) no período da base EVT. Com ela confirmo, por uma segunda fonte oficial, a disponibilidade declarada e sei, em cada hora com a usina parada, se havia unidade sincronizada à rede. Assim separo a usina disponível e desligada da usina sincronizada sem gerar.

**Why this priority**: Responde à pergunta sobre horas com disponibilidade declarada e geração zero, levantada para a fiscalização. A disponibilidade sincronizada não existe em nenhuma base já incluída.

**Independent Test**: Com os arquivos obtidos e a base EVT, gerar a conferência hora a hora e a classificação das horas paradas, e conferir que a soma das classes é igual ao total de horas paradas no período comum.

**Acceptance Scenarios**:

1. **Given** o catálogo com um arquivo por mês, publicado em mais de um formato e com o formato compacto ausente em parte dos meses, **When** a coleta é executada, **Then**:
   - todo mês que se sobrepõe ao período da base EVT é obtido num formato que o contém;
   - a usina é extraída;
   - os meses sem a usina são listados, nunca deduzidos de um formato que não cobre o mês.
2. **Given** a disponibilidade horária e a base EVT, **When** as duas são comparadas hora a hora, **Then** são informadas as horas comuns, coincidentes e divergentes entre a disponibilidade operacional e a declarada, e as divergentes ficam listadas na planilha.
3. **Given** as horas com a usina parada no período comum, **When** a análise é executada, **Then** cada hora é classificada por sincronização (nenhuma unidade ou alguma unidade sincronizada) e por presença de EVT. Nas horas cobertas pela programação diária, a hora também recebe a classe da spec 004.
4. **Given** a série horária, **When** é resumida por mês e por ano, **Then** são apresentadas:
   - as médias de disponibilidade operacional, de disponibilidade sincronizada e de geração;
   - a capacidade disponível não sincronizada;
   - a comparação mensal dessa capacidade com as horas em reserva desligada das unidades (parâmetros TEIFa/TEIP).
5. **Given** valores inconsistentes (sincronizada acima da operacional, operacional acima da instalada, negativos ou não numéricos), **When** encontrados, **Then** são contados na auditoria e excluídos das análises, sem correção.
6. **Given** os resultados, **When** o relatório é gerado, **Then** ele traz:
   - uma constatação e uma seção sobre a disponibilidade sincronizada;
   - a figura mensal de disponibilidade operacional, disponibilidade sincronizada e geração;
   - a fonte na relação de fontes.

---

### User Story 4 - Afluência, vertimento e nível do reservatório (Priority: P1)

Como fiscal, quero a vazão afluente e os níveis de montante e jusante da usina, hora a hora e alinhados à base EVT, para explicar cada vertimento. Preciso saber se a água que chegou excedia a capacidade das turbinas (vertimento inevitável) ou se cabia nelas e foi vertida porque a usina estava parada ou gerando abaixo do possível. Quero também mostrar como o reservatório, de pequena regularização, se comporta durante as paradas.

**Why this priority**: Responde às perguntas sobre vazões muito altas e sobre vertimento turbinável que não foi turbinado. A base EVT tem as vazões turbinada e vertida, mas não a afluência nem os níveis.

**Independent Test**: Com os arquivos obtidos e a base EVT, alinhar as convenções de hora, conferir a coincidência das vazões turbinada e vertida, classificar as horas com EVT por faixa de afluência e conferir que a soma das faixas é igual ao total de horas com EVT do período comum.

**Acceptance Scenarios**:

1. **Given** o catálogo com um arquivo por mês, **When** a coleta é executada, **Then** todo mês que se sobrepõe ao período da base EVT é obtido, a usina é extraída e as horas ausentes são listadas.
2. **Given** registros na convenção de fim de hora (inclusive a última hora do dia, marcada às 23:59), **When** convertidos, **Then** cada registro passa à hora de início usada na base EVT. O alinhamento é confirmado pela coincidência das vazões turbinada e vertida em pelo menos 99% das horas comuns; abaixo disso, a etapa informa a falha de alinhamento e não publica os cruzamentos.
3. **Given** as horas com EVT, **When** cruzadas com a afluência, **Then** cada uma recebe uma faixa, com horas e EVT por faixa, por mês e por ano. As faixas são:
   - afluência acima do engolimento máximo da usina;
   - acima do engolimento de uma unidade até o da usina;
   - até o engolimento de uma unidade;
   - sem dado hidrológico.
4. **Given** os dias com ao menos uma hora de parada com EVT e os demais dias, **When** analisados, **Then** é produzido, para cada grupo, o perfil médio por hora do dia do nível de montante e das vazões afluente, turbinada e vertida.
5. **Given** valores fisicamente impossíveis (vazões negativas, volume útil fora de 0 a 100%) ou campos vazios, **When** encontrados, **Then** os valores impossíveis são contados e excluídos, e campo vazio não é tratado como zero.
6. **Given** a série alinhada, **When** resumida por mês, **Then** a planilha traz, para cada mês, afluência, vazões, níveis, volume útil e horas com afluência acima do engolimento máximo.
7. **Given** os resultados, **When** o relatório é gerado, **Then** ele traz:
   - uma constatação e uma seção sobre afluência e vertimento;
   - as figuras de horas com EVT por faixa de afluência e do perfil por hora do dia;
   - a fonte na relação de fontes, com a ressalva de dados não consistidos.

---

### User Story 5 - Conferência independente da geração (Priority: P2)

Como fiscal, quero comparar a geração da base EVT com a série oficial de geração por usina do ONS, hora a hora e por mês, para afirmar no relatório que a geração analisada confere com a estatística oficial ou listar onde não confere.

**Why this priority**: Reforça a confiabilidade dos números do relatório, mas não traz informação nova sobre a operação. A igualdade já foi constatada por consulta em 02/10/2026; esta história torna a conferência reproduzível no pipeline.

**Independent Test**: Gerar a comparação horária e mensal no período comum e conferir que cada hora comum é classificada como coincidente ou divergente.

**Acceptance Scenarios**:

1. **Given** o catálogo com arquivos anuais até 2021 e mensais a partir de 2022, **When** a coleta é executada, **Then** todos os arquivos que se sobrepõem ao período da base EVT são obtidos e a usina é extraída.
2. **Given** as duas séries, **When** comparadas, **Then** são informadas as horas comuns, coincidentes e divergentes, as horas presentes em só uma das fontes e a energia mensal de cada fonte, com a diferença.
3. **Given** os resultados, **When** o relatório é gerado, **Then** ele traz uma seção com a conferência e a fonte na relação de fontes. Se houver horas divergentes, traz também uma constatação.

---

### User Story 6 - Identificação cadastral da usina no ONS (Priority: P3)

Como fiscal, quero a ficha cadastral da usina no ONS, com a data da consulta, para identificar a usina no relatório sem ambiguidade com os homônimos. A ficha traz modalidade de operação, centro de operação, ponto de conexão, potência autorizada e situação na ANEEL.

**Why this priority**: Melhora a identificação no relatório, mas o conteúdo já é conhecido (Tipo II-A, COSR-S, SE Água Clara 138 kV, 48 MW).

**Independent Test**: Obter o cadastro, extrair a ficha da usina e conferir que ela traz o CEG do projeto, o estado MS e a data da consulta.

**Acceptance Scenarios**:

1. **Given** o cadastro publicado (sem série histórica), **When** a coleta é executada, **Then** a ficha da usina é extraída, a data da consulta é registrada e os homônimos são contados, não extraídos.
2. **Given** a ficha, **When** comparada com os parâmetros do projeto, **Then** são sinalizadas as divergências de potência autorizada (diferente de 48 MW) ou de estado (diferente de MS).
3. **Given** um cadastro republicado com conteúdo diferente, **When** obtido de novo, **Then** a versão anterior é preservada e a mudança é informada.
4. **Given** a ficha, **When** o relatório é gerado, **Then** ele traz a tabela de identificação da usina com a data da consulta e a fonte na relação de fontes. Se houver divergência com os parâmetros do projeto, traz também uma constatação.

---

### Edge Cases

- **Formato compacto incompleto**: na disponibilidade, o formato compacto só existe para 01–02/2015 e a partir de 01/2023. Os demais meses do período vêm do formato completo (cerca de 25 MB por mês). A ausência da usina num mês nunca é concluída a partir de um formato que não cobre o mês.
- **Recurso duplicado no catálogo**: o catálogo dos dados hidrológicos lista o arquivo de 10/2026 duas vezes, com tamanhos diferentes. Cada recurso deve ser identificado sem que um sobrescreva o outro, e a duplicidade fica registrada na auditoria.
- **Convenção de hora**:
  - os dados hidrológicos marcam o fim da hora; a primeira hora do dia aparece à 01:00 e a última às 23:59 (365 registros desse tipo em 2025);
  - a disponibilidade e a geração marcam o início da hora, como a base EVT.
- **Horas ausentes**: as fontes têm horas faltantes. Por exemplo: 4 h em 2025 nos dados hidrológicos; 1 h em 2018 na geração, a mesma de 04/11/2018 que falta na base EVT. Essas horas são listadas, sem interpolação.
- **Horas duplicadas**: o ONS pode publicar a mesma hora em versões diferentes. Mantém-se um valor por hora (o do arquivo mais recente) e contam-se as duplicatas com valores conflitantes.
- **Tipos variáveis**: campos numéricos aparecem como texto em alguns arquivos e como número em outros; valores não conversíveis são contados como inválidos.
- **Dados não consistidos**: os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS. Valores fisicamente impossíveis são contados e excluídos, nunca corrigidos.
- **Campos vazios**: nível de jusante, vazão vertida não turbinável e vazão por outras estruturas podem vir vazios; vazio não é zero.
- **Homônimos**: o cadastro tem mais de 20 usinas "São Domingos" (CGH em SC e no RS, PCH em GO, eólicas no RN, solares no Nordeste). Só o CEG `UHE.PH.MS.028761-0.01` é extraído; as linhas em que só o nome confere são contadas.
- **Períodos além da base EVT**: disponibilidade, dados hidrológicos e geração seguem além de 28/09/2026. Só as horas dentro do período da base EVT são extraídas e cruzadas.
- **Republicação**: arquivo republicado pelo ONS tem a versão anterior preservada (spec 005). O cadastro não tem série histórica e depende dessa preservação para registrar mudanças.
- **Dicionários**:
  - o catálogo não informa data nem tamanho dos dicionários, então a mudança só é detectável pelo conteúdo;
  - um conjunto pode ter só um dos formatos ou nenhum dicionário publicado, o que é registrado sem falha.
- **Cópia de segurança**:
  - casos a tratar: arquivo sem versão anterior; conteúdo idêntico (sem regravação); execução interrompida no meio da gravação; disco cheio;
  - planilhas cujo conteúdo binário muda a cada gravação, mesmo com os mesmos dados, são comparadas pelos dados.

---

## Requirements *(mandatory)*

### Functional Requirements

**Geral — bases novas (US3 a US6)**

- **FR-001**: As novas etapas DEVEM usar a base EVT local existente, sem obter de novo seus arquivos, e recortar cada conjunto no período dessa base (hoje de 28/08/2018 00h a 28/09/2026 23h).
- **FR-002**: Para cada conjunto novo, o sistema DEVE:
  - inspecionar todos os arquivos publicados que se sobrepõem ao período;
  - preservar os arquivos brutos;
  - registrar no manifesto a versão, a data de publicação e a data de obtenção;
  - preservar a versão anterior quando o ONS republicar um arquivo;
  - reaproveitar a cópia local que corresponda à versão publicada.
- **FR-003**: Quando um conjunto for publicado em mais de um formato, o sistema DEVE obter cada mês num formato que o contenha e só concluir a ausência da usina num mês a partir de um arquivo que cubra esse mês.
- **FR-004**: O sistema DEVE extrair somente a UHE São Domingos (MS), pelo identificador declarado e conferido de cada conjunto (princípio IV da constituição 1.2.0). DEVE também contar na auditoria, sem extrair, as linhas em que só o identificador ou só a conferência casa:

  | Conjunto do ONS | Identificador de extração | Conferência |
  |---|---|---|
  | Disponibilidade por usina | id ONS `MSUHSD` | CEG `UHE.PH.MS.028761-0.01` e estado `MS` |
  | Dados hidrológicos horários | `cod_usina` 153 | nome do reservatório "SAO DOMINGOS" e código do reservatório `PNUHSD` |
  | Geração por usina | id ONS `MSUHSD` | CEG e estado `MS` |
  | Modalidade das usinas | CEG `UHE.PH.MS.028761-0.01` | id ONS `MSUHSD` e estado `MS` |

- **FR-005**: O sistema DEVE registrar, por arquivo: linhas lidas, linhas da usina, linhas com identificação parcial, horas da usina, valores inválidos e situação (processado, sem registros da usina ou falha). DEVE também listar os meses e as horas ausentes do período, sem interpolar.
- **FR-006**: O sistema DEVE manter um único valor por hora da usina, o do arquivo mais recente, e contar as duplicatas com valores conflitantes.
- **FR-007**: Cada etapa nova DEVE poder ser executada dentro do pipeline completo e isoladamente, ser desligável, respeitar o nível de log escolhido e ser testável sem acesso à rede.

**US1 — Cópia de segurança dos dados processados**

- **FR-008**: Antes de regravar qualquer arquivo em `data/processed/`, o sistema DEVE guardar a versão atual como `<nome do arquivo>.bak` na mesma pasta, substituindo a cópia anterior.
- **FR-009**: Se o conteúdo novo for idêntico ao atual, o sistema NÃO DEVE regravar o arquivo nem substituir a cópia `.bak`.
- **FR-010**: Depois de cada gravação, o sistema DEVE conferir no disco que o arquivo existe, pode ser lido e tem o conteúdo pretendido (mesmos registros e colunas). Em caso de falha, DEVE restaurar a versão anterior, registrar o erro com o nome do arquivo e encerrar a execução com código de erro.
- **FR-011**: Nenhuma etapa DEVE ler uma cópia `.bak` como dado de entrada.
- **FR-012**: FR-008 a FR-011 DEVEM valer para todos os arquivos gravados em `data/processed/`, tanto pelas etapas existentes (consolidação e auditoria da varredura, tratamento e validação física, indicadores oficiais, programação diária) quanto pelas novas.
  - Ficam fora da regra, por decisão do usuário (constituição 1.2.0, Requisito Técnico 3): os relatórios em `reports/`, os manifestos de versões, os dicionários de dados e os demais arquivos de controle.

**US2 — Dicionários de dados**

- **FR-013**: A cada coleta, o sistema DEVE obter os dicionários de dados publicados (PDF e JSON) de todos os conjuntos do pipeline e guardá-los junto aos dados brutos de cada conjunto. Os conjuntos são: EVT; os quatro de indicadores oficiais; programação diária; disponibilidade; dados hidrológicos; geração por usina; modalidade.
- **FR-014**: O sistema DEVE comparar cada dicionário obtido com a cópia local pelo conteúdo, preservar a versão anterior quando houver diferença e registrar a data de obtenção e o resultado: novo, inalterado, alterado ou falha.
- **FR-015**: A obtenção dos dicionários NÃO DEVE obter de novo os arquivos de dados da base EVT e, em caso de falha, NÃO DEVE interromper as demais etapas.

**US3 — Disponibilidade operacional e sincronizada**

- **FR-016**: O sistema DEVE extrair, hora a hora, a potência instalada, a disponibilidade operacional e a disponibilidade sincronizada da usina.
- **FR-017**: O sistema DEVE comparar hora a hora a disponibilidade operacional com a disponibilidade declarada da base EVT e informar as horas comuns, coincidentes (diferença até a tolerância de arredondamento) e divergentes. As divergentes DEVEM ser listadas, agrupadas em períodos contínuos.
- **FR-018**: O sistema DEVE contar na auditoria e excluir das análises os valores inconsistentes: sincronizada acima da operacional, operacional acima da instalada, negativos ou não numéricos.
- **FR-019**: O sistema DEVE classificar cada hora comum com a usina parada (geração até 1 MW, o mesmo limiar das specs 003 e 004) por três critérios. A soma das classes DEVE ser igual ao total de horas paradas.
  - Sincronização: alguma unidade sincronizada quando a disponibilidade sincronizada passa de 1 MW; nenhuma, caso contrário.
  - Presença de EVT.
  - Nas horas cobertas pela programação diária, a classe da spec 004.
- **FR-020**: O sistema DEVE resumir por mês e por ano:
  - as médias de disponibilidade operacional, de disponibilidade sincronizada e de geração;
  - a capacidade disponível não sincronizada (operacional menos sincronizada), em MW médio e em MWh;
  - a comparação mensal dessa capacidade com as horas em reserva desligada das unidades multiplicadas pela potência unitária (parâmetros TEIFa/TEIP, spec 004).

**US4 — Afluência, vertimento e nível do reservatório**

- **FR-021**: O sistema DEVE extrair, hora a hora, as vazões afluente, defluente, turbinada, vertida, vertida não turbinável e por outras estruturas, os níveis de montante e de jusante e o volume útil.
- **FR-022**: O sistema DEVE converter a convenção de fim de hora (inclusive a última hora do dia, marcada às 23:59) para a de início de hora da base EVT e confirmar o alinhamento pela coincidência das vazões turbinada e vertida nas horas comuns. Se a coincidência ficar abaixo de 99%, a etapa DEVE informar a falha de alinhamento e não publicar os cruzamentos.
- **FR-023**: O sistema DEVE classificar cada hora com EVT do período comum por faixa de afluência e informar horas e EVT por faixa, por mês e por ano. As faixas são:
  - acima do engolimento máximo da usina (163 m³/s);
  - acima do engolimento de uma unidade (81,5 m³/s) até o da usina;
  - até o engolimento de uma unidade;
  - sem dado hidrológico.
- **FR-024**: O sistema DEVE produzir o perfil médio por hora do dia (0 a 23 h) do nível de montante e das vazões afluente, turbinada e vertida, separando os dias com ao menos uma hora de parada com EVT dos demais dias.
- **FR-025**: O sistema DEVE resumir por mês:
  - afluência média e máxima;
  - vazões turbinada, vertida e vertida não turbinável médias;
  - níveis de montante mínimo, médio e máximo e nível de jusante médio;
  - volume útil médio;
  - horas com afluência acima do engolimento máximo.
- **FR-026**: O sistema DEVE contar e excluir os valores fisicamente impossíveis e NÃO DEVE tratar campo vazio como zero.

**US5 — Conferência da geração**

- **FR-027**: O sistema DEVE extrair a geração horária da usina na série oficial de geração por usina.
- **FR-028**: O sistema DEVE comparar essa série com a geração da base EVT e informar as horas comuns, coincidentes e divergentes, as horas presentes em só uma das fontes e a energia mensal de cada fonte, com a diferença.

**US6 — Identificação cadastral**

- **FR-029**: O sistema DEVE extrair a ficha cadastral da usina com a data da consulta e contar os homônimos. A ficha traz nome, CEG, id ONS, modalidade de operação, centro de operação, ponto de conexão, potência autorizada, estado e situação na ANEEL.
- **FR-030**: O sistema DEVE comparar a potência autorizada e o estado com os parâmetros do projeto (48 MW, MS) e sinalizar as divergências.

**Relatório**

- **FR-031**: O relatório (PDF e Markdown) e a planilha DEVEM ganhar uma seção para cada história entregue entre US3 e US6.
  - US3 e US4 DEVEM ter sempre uma constatação.
  - US5 e US6 DEVEM ter constatação só quando houver divergência: horas divergentes na conferência da geração ou ficha cadastral diferente dos parâmetros do projeto.
  - Números e frases DEVEM ser gerados a partir dos dados.
  - As ressalvas da fonte DEVEM acompanhar o texto: dados hidrológicos não consistidos pelo ONS; cadastro sem histórico; nenhuma das bases informa o motivo das paradas.
- **FR-032**: As figuras novas DEVEM seguir o padrão gráfico da constituição (Requisito Técnico 5: seaborn, com tema e paleta centrais). No mínimo, DEVEM incluir:
  - horas com EVT por faixa de afluência, por ano;
  - perfil por hora do dia do nível de montante e das vazões;
  - disponibilidade operacional, disponibilidade sincronizada e geração, por mês.
- **FR-033**: As seções, constatações e abas já existentes DEVEM manter seus números; só a numeração das seções pode mudar.
- **FR-034**: A relação de fontes do relatório DEVE incluir cada base nova, com o período coberto, o identificador da usina e a data de obtenção.

### Key Entities *(include if feature involves data)*

- **Cópia de segurança**: versão anterior de um arquivo em `data/processed/` (`<nome>.bak`), mantida até a próxima alteração de conteúdo.
- **Dicionário de dados**: documento publicado pelo ONS para cada conjunto (PDF e JSON), com a data de obtenção e as versões anteriores, se houver.
- **Disponibilidade horária da usina**: potência instalada, disponibilidade operacional e disponibilidade sincronizada por hora, com a origem (arquivo e versão).
- **Classificação das horas paradas**: para cada hora comum com a usina parada, a sincronização, a presença de EVT e, quando houver, a classe da programação.
- **Série hidrológica horária**: vazões, níveis e volume útil por hora, já na convenção de início de hora, com a origem.
- **Faixa de afluência**: classe de cada hora com EVT segundo a afluência e o engolimento das unidades.
- **Perfil horário**: médias por hora do dia do nível de montante e das vazões, por grupo de dias.
- **Geração horária oficial**: geração da série de geração por usina, com a origem.
- **Ficha cadastral**: dados de identificação da usina no cadastro do ONS, com a data da consulta.
- **Conferência entre fontes**: para cada par de séries, as horas comuns, coincidentes e divergentes e a lista de divergências.
- **Auditoria por arquivo**: para cada arquivo de cada conjunto, linhas lidas, linhas da usina, identificação parcial, valores inválidos e situação; também os meses e as horas ausentes.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para cada conjunto novo, 100% dos meses do período da base EVT estão obtidos ou listados como ausentes, e nenhuma ausência foi concluída a partir de arquivo que não cobre o mês.
- **SC-002**: Nenhum registro de outra usina é extraído: 100% dos registros extraídos têm o identificador e a conferência declarados.
- **SC-003**: Depois do alinhamento das horas, as vazões turbinada e vertida das duas fontes coincidem em pelo menos 99% das horas comuns (amostra de jan/2025: 100%).
- **SC-004**: Em cada conferência (disponibilidade e geração), 100% das horas comuns são classificadas como coincidentes ou divergentes, e as divergentes ficam listadas.
- **SC-005**: Recebem classe 100% das horas com EVT que têm dado hidrológico (faixa de afluência) e 100% das horas paradas que têm dado de disponibilidade (sincronização). Nos dois casos, a soma das classes é igual ao total.
- **SC-006**: No teste das quatro gravações (sem versão anterior, conteúdo alterado, conteúdo idêntico e falha simulada), a versão anterior à última alteração está sempre recuperável e, após a falha, o arquivo volta idêntico ao que era.
- **SC-007**: Depois de cada coleta, cada um dos 10 conjuntos do pipeline tem seus dicionários publicados obtidos ou a falha registrada. No teste com dicionário alterado, a versão anterior fica preservada em 100% dos casos.
- **SC-008**: Os números das seções, constatações e abas existentes são idênticos antes e depois da feature, e os números citados nas seções novas são idênticos aos da planilha.
- **SC-009**: Com os arquivos já obtidos, as novas etapas terminam em menos de 10 minutos, sem acesso à rede. Uma segunda execução sem mudança no portal não obtém nenhum arquivo de dados de novo, e nenhuma execução obtém de novo os arquivos de dados da base EVT.
- **SC-010**: As histórias de prioridade P1 (US1 a US4) estão entregues e o relatório está regenerado até 13/10/2026, véspera da fiscalização.

---

## Assumptions

- Escopo exclusivo da UHE São Domingos (MS), CEG `UHE.PH.MS.028761-0.01` (princípio VI). As fontes usam os identificadores do FR-004, conferidos na sondagem de 05/10/2026 e incluídos na constituição 1.2.0.
- A base EVT é mantida como está (decisão do usuário em 02/10/2026) e define o período de todas as bases novas. A geração por usina tem dados desde 18/06/2015, mas o trecho anterior a 28/08/2018 fica fora do recorte.
- Limiares de análise, abertos à revisão do usuário:
  - usina parada: geração até 1 MW (specs 003 e 004);
  - unidade sincronizada: disponibilidade sincronizada acima de 1 MW;
  - engolimento nominal: 81,5 m³/s por unidade e 163 m³/s para a usina (parâmetros do projeto);
  - coincidência entre fontes: tolerância de arredondamento dos valores publicados, fixada no plano em no máximo 0,1 MW e 0,5 m³/s.
- Formatos: usa-se o formato compacto quando ele cobre o mês. Volume estimado a obter:
  - dados hidrológicos: cerca de 130 MB;
  - geração por usina: cerca de 410 MB;
  - disponibilidade: cerca de 1,3 GB no formato completo (08/2018 a 12/2022) e cerca de 10 MB no compacto (2023 em diante);
  - cadastro: menos de 1 MB;
  - dicionários: dois arquivos pequenos por conjunto (20 no total).
- Os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS; o relatório traz essa ressalva.
- A cópia de segurança vale só para `data/processed/` (decisão do usuário em 05/10/2026). A preservação das versões anteriores dos arquivos brutos e dos dicionários segue o mecanismo da spec 005.
- Fora do escopo:
  - classificação de EVT (agregado do SIN);
  - bases da CCEE e da ANEEL. Já houve comparação manual com a CCEE e com o BI da ANEEL em 01–02/10/2026, e o portal da CCEE bloqueia download automatizado;
  - extensão das séries para antes do período da base EVT;
  - o motivo de cada parada, que nenhuma base aberta do ONS informa e que deve ser pedido ao agente.
- Prazo: fiscalização presencial de 14 a 16/10/2026; P1 (US1 a US4) até 13/10/2026. P2 e P3 podem ser entregues depois, sem prejuízo das demais.
