# Feature Specification: Tratamento, Padronização e Validação Física dos Dados - UHE São Domingos

**Feature Branch**: `002-tratamento-dados`

**Created**: 2026-09-30

**Status**: Implementado (revisado em 2026-10-05)

**Input**: User description: "abri o csv no excel e vi que alguns dados na coluna val_geracao, val_disponibilidade, val_produtividade possuem dados em formato número e outros geral, precisa que seja tudo número, assim conseguimos seguir mais pra frente com análises estatísticas. além disso, as colunas val_energiavertida, val_vazaovertidaturbinavel e val_energiavertidaturbinavel são as mais importantes de todo dataset, os números estão certos mesmo? baixei o dicionário de dados .json na raiz do projeto, avalie se TODAS AS COLUNAS fazem sentido, inclusive se os dados não estão bizarros (numeros negativos, valores absurdos conforme dicionário)"

**Revisão retroativa (2026-10-05)**: esta especificação foi revisada para descrever o sistema como está implementado em `src/processor.py`, `src/validator.py` e `src/config.py`. As correções da auditoria de 30/09/2026 foram feitas diretamente no código, sem atualização prévia da spec; esta revisão as documenta. Cada requisito ou critério alterado, acrescentado ou removido está registrado em "Histórico de revisões", ao final. A versão anterior está preservada em `spec.md.2026-10-05.bak`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Padronização e Tipagem Estrita das Colunas Numéricas (Priority: P1)

Como analista de dados regulatórios e pesquisador estatístico, quero que todas as colunas de métricas operacionais (`val_*`) possuam tipagem numérica uniforme, sem mistura de formatos "número" e "geral/texto" nem divergências de separador decimal, e que um valor ausente na fonte continue ausente (nunca convertido em zero), de modo que os dados possam ser abertos diretamente no Excel sem perda de formato e importados sem falhas em bibliotecas de análise estatística (Pandas, Scipy, R, PowerBI).

**Why this priority**: A integridade de tipo é pré-requisito para modelagem estatística, regressões e qualquer agregação. Colunas com texto ou formatação inconsistente fazem somas e médias falharem silenciosamente no Excel. Converter um valor ausente em zero fabricaria uma medição (uma hora sem dado passaria a parecer usina parada) e distorceria totais e médias.

**Independent Test**: Pode ser testado com uma amostra que contenha vírgula decimal, espaços e célula vazia: as 10 colunas operacionais resultam em `float64`, `"30,500"` vira 30,5, `" 100.0 "` vira 100,0, a célula vazia permanece ausente (NaN) e os arquivos `.xlsx` (células numéricas nativas), `.parquet` (colunas `double`) e `.csv` (precisão integral) são gerados.

**Acceptance Scenarios**:

1. **Given** a base consolidada de registros da UHE São Domingos, **When** o pipeline de tratamento e tipagem for aplicado, **Then** todas as 10 colunas operacionais (`val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`) possuem tipagem numérica de ponto flutuante.
2. **Given** um valor com vírgula decimal ou espaços (ex.: `"30,500"`, `" 100.0 "`), **When** a tipagem é aplicada, **Then** o valor é convertido para o número correspondente (30,5; 100,0).
3. **Given** um valor ausente ou não numérico em uma coluna operacional, **When** a tipagem é aplicada, **Then** o valor permanece ausente (NaN), a quantidade de ausentes de cada coluna é registrada em log e nenhum valor é substituído por zero.
4. **Given** o campo `cod_usina`, **When** a tipagem é aplicada, **Then** ele é tratado como inteiro que admite ausência; um código inválido fica ausente e gera aviso, nunca vira 0.
5. **Given** um `din_instante` que não pode ser interpretado como data/hora, **When** a tipagem é aplicada, **Then** o processamento é interrompido com erro (código de saída 1) e nenhum arquivo é exportado.
6. **Given** a necessidade de análise direta em planilha e em ferramentas analíticas, **When** a exportação for concluída, **Then** são gerados arquivos em Excel nativo (`.xlsx`), formato colunar (`.parquet`) e CSV com delimitador `;`, ponto decimal e todas as casas decimais (sem arredondamento).

---

### User Story 2 - Validação de Consistência Interna, Plausibilidade Física e Auditoria (Priority: P1)

Como auditor de engenharia de geração, quero confrontar 100% dos registros (a) com as identidades de cálculo entre as grandezas publicadas pelo ONS, em especial as mais críticas (`val_energiavertida`, `val_vazaovertidaturbinavel` e `val_energiavertidaturbinavel`), e (b) com os parâmetros técnicos da usina (potência instalada, engolimento das turbinas e produtividade nominal), de modo a identificar valores negativos, inconsistências entre grandezas e valores fisicamente implausíveis, sem remover nenhum registro da base.

**Why this priority**: As identidades do ONS (R1 a R5) mostram apenas que as colunas derivadas foram calculadas de forma coerente a partir das demais; não mostram que os valores medidos estão corretos. O registro de 15/05/2019 14h, com geração de 68,743 MW numa usina de 48 MW, satisfaz R1 a R5 e só é detectado pela comparação com os parâmetros da usina (R6). O dicionário de dados do ONS traz apenas a descrição e a unidade de cada coluna, sem faixas de valores; por isso os limites físicos vêm dos parâmetros técnicos da usina.

**Independent Test**: Pode ser testado executando a validação sobre os 70.895 registros horários e conferindo, para cada regra, a quantidade de registros violados:

*Consistência interna das grandezas do ONS (tolerância $\epsilon = 10^{-4}$):*
1. **R1** - Nenhuma das 10 grandezas negativa (valor $< -\epsilon$); conta registros, não células.
2. **R2** - $val\_energiavertida \ge val\_energiavertidaturbinavel$.
3. **R3** - $val\_vazaovertida \ge val\_vazaovertidaturbinavel + val\_vazaovertidanaoturbinavel$.
4. **R4** - $val\_energiavertidaturbinavel \approx val\_vazaovertidaturbinavel \times val\_produtividade$.
5. **R5** - $val\_folgadegeracao \approx \max(0, val\_disponibilidade - val\_geracao)$.

*Plausibilidade física frente aos parâmetros da usina:*
6. **R6** - Geração, disponibilidade, folga de geração e energia vertida turbinável $\le$ 50,4 MW (48 MW + 5%); vazão turbinada e vazão vertida turbinável $\le$ 171,2 m³/s (2 × 81,5 m³/s + 5%).
7. **R7** - Geração $\le$ disponibilidade + 1,0 MW.
8. **R8** - Quando a vazão turbinada é positiva, produtividade entre 0,214 e 0,398 MW/(m³/s) (70% a 130% da produtividade nominal teórica de 0,3063 MW/(m³/s)).
9. **R9** - Quando a vazão turbinada é nula, geração $\le$ 1,0 MW.

E conferindo que todo registro que viola R6 a R9 continua na base, marcado nas colunas de anomalia e no resumo de qualidade do registro.

**Acceptance Scenarios**:

1. **Given** a totalidade dos registros horários consolidados, **When** a validação é executada, **Then** o resultado de cada uma das 9 regras (registros avaliados, conformes, violações, taxa de conformidade e desvio máximo) é apurado e registrado, sem pressupor conformidade.
2. **Given** um registro que viola uma ou mais regras de R6 a R9, **When** a sinalização é aplicada, **Then** o registro é mantido na base tratada, a coluna de anomalia de cada regra violada fica verdadeira e a coluna de qualidade lista os códigos violados separados por `;` (ex.: `R6;R7;R8`); registros sem anomalia recebem `OK`.
3. **Given** ao menos um registro com valor negativo (violação de R1), **When** a validação é concluída, **Then** o processamento é interrompido com código de saída 3 (alerta crítico) antes da sinalização, dos relatórios e da exportação.
4. **Given** valores ausentes em qualquer grandeza, **When** a validação é executada, **Then** eles não contam como violação de nenhuma regra e o total de ausentes é registrado em log.
5. **Given** o dicionário de dados oficial, **When** o processamento é iniciado, **Then** as 10 colunas operacionais são conferidas contra os códigos do dicionário (ausência gera aviso em log) e a versão do dicionário é citada no relatório.
6. **Given** a validação concluída, **When** o relatório é gerado, **Then** são produzidos um relatório em Markdown e uma tabela em CSV com o resultado das 9 regras; todo o texto deriva dos números apurados, o relatório declara que R1 a R5 não atestam que os valores medidos estejam corretos e lista, em ordem cronológica, os primeiros 40 registros sinalizados.

---

### User Story 3 - Perfilamento Estatístico e Sumário Analítico de Vertimento (Priority: P2) — transferida para a Feature 003

> **Situação (revisão de 2026-10-05)**: esta história foi implementada na versão original da feature (seção 3 do relatório de validação, preservado em `reports/_versao_anterior_2026-09-30/data_processed/relatorio_validacao_fisica.md`) e retirada na auditoria de 30/09/2026. O perfil estatístico anual passou a ser produzido somente pela Feature 003 (`src/analyzer.py`, função `calcular_perfil_estatistico_anual`, saídas `reports/perfil_estatistico_anual.xlsx` e `.csv`), que exclui do perfil os registros sinalizados. O texto original é mantido abaixo apenas como registro; nenhum requisito desta feature depende dele.

Como especialista de desempenho operacional, quero visualizar um perfil estatístico das variáveis críticas de vertimento por ano de operação (2018 a 2026), de modo a identificar o comportamento sazonal de vertimento turbinável e a evolução da produtividade hidráulica da usina.

**Why this priority**: Fornece os subsídios quantitativos imediatos para a fiscalização regulatória da AGEMS / ANEEL e apoia tomadas de decisão sobre eficiência e perdas energéticas.

**Independent Test**: Pode ser testado gerando uma tabela de perfilamento com contagem, média, desvio-padrão, mínimos, quartis e máximos para cada ano civil disponível.

**Acceptance Scenarios**:

1. **Given** a base tratada, **When** o sumário estatístico for processado, **Then** é emitido um relatório consolidado com indicadores anuais de energia vertida total, energia vertida turbinável e horas de vertimento. *(Transferido para a Feature 003.)*

---

### Edge Cases

- Como o sistema trata instantes com geração nula ($val\_geracao = 0$)? R5 exige folga igual à disponibilidade; R9 sinaliza geração acima de 1,0 MW com vazão turbinada nula; R8 não é avaliada quando a vazão turbinada é nula, porque a produtividade não tem significado físico sem vazão.
- Como o sistema trata imprecisões de representação de ponto flutuante (ex.: $0.30000000000000004$)? As regras R1 a R5 aplicam tolerância $\epsilon = 10^{-4}$; em R1, valores entre $-10^{-4}$ e 0 não contam como negativos. As regras R6 a R9 usam folgas próprias (5% sobre os valores nominais, 1,0 MW em R7, faixa de 70% a 130% em R8 e 1,0 MW em R9).
- O que acontece se o usuário abrir o CSV gerado em um Excel com configuração PT-BR (vírgula decimal)? O CSV usa ponto decimal e pode ser mal interpretado nesse caso; para uso no Excel deve ser aberto o `.xlsx`, cujas células são numéricas nativas. O CSV e o `.parquet` destinam-se a ferramentas analíticas.
- Valor ausente ou não numérico em coluna operacional: permanece ausente (NaN), é contado em log e não viola nenhuma regra.
- `din_instante` inválido: o processamento é interrompido (código de saída 1) e nada é exportado.
- `cod_usina` inválido: fica ausente, com aviso em log; o processamento continua.
- Coluna obrigatória ausente na base consolidada (as 6 colunas de identificação, `cod_usina`, `din_instante` e as 10 colunas operacionais): erro e código de saída 1. Ausência das colunas de rastreabilidade (`arquivo_origem`, `tipo_match`) gera apenas aviso.
- Arquivo do dicionário de dados ausente: erro e código de saída 1. Coluna operacional que não consta do dicionário: apenas aviso.
- Registro que viola várias regras de plausibilidade: todas são sinalizadas. Ex.: 15/05/2019 14h (geração de 68,743 MW, disponibilidade de 22,817 MW, produtividade de 0,929 MW/(m³/s)) recebe `R6;R7;R8`.
- Violação de R1: o processamento é interrompido com código 3 antes de gravar qualquer arquivo, inclusive o relatório de validação; a análise do caso é feita pelo log.
- Violações de R2 a R9 não alteram o código de saída (0) nem impedem a exportação.
- Validação desligada pelo usuário: os relatórios de validação não são gerados e o código 3 não ocorre, mas as colunas de sinalização (R6 a R9) continuam sendo acrescentadas à base exportada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** *(revisado em 2026-10-05)*: O sistema DEVE ler `DicionarioDados_EnergiaVertidaTurbinavel.json`, conferir que as 10 colunas operacionais constam do dicionário (ausência gera aviso em log, sem interromper) e citar a versão do dicionário no relatório de validação. A falta do arquivo do dicionário DEVE interromper o processamento. O dicionário não contém faixas de valores e não é fonte de limites físicos.
- **FR-002** *(revisado em 2026-10-05)*: O sistema DEVE garantir que as 10 colunas operacionais (`val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`) sejam numéricas (`float64`), convertendo vírgula decimal em ponto e removendo espaços. Valores ausentes ou não numéricos DEVEM permanecer ausentes (NaN), contados em log por coluna, e NUNCA substituídos por zero.
- **FR-003** *(R1; revisado em 2026-10-05)*: O sistema DEVE validar que nenhuma das 10 grandezas contenha valor negativo ($val < -10^{-4}$), contando como violação cada registro com ao menos uma grandeza negativa.
- **FR-004** *(R3)*: O sistema DEVE checar e auditar a consistência entre vazão vertida total e suas parcelas ($val\_vazaovertida \ge val\_vazaovertidaturbinavel + val\_vazaovertidanaoturbinavel$, com tolerância $10^{-4}$).
- **FR-005** *(R2)*: O sistema DEVE checar e auditar a consistência de energia vertida ($val\_energiavertida \ge val\_energiavertidaturbinavel$, com tolerância $10^{-4}$).
- **FR-006** *(R4)*: O sistema DEVE verificar a identidade da energia vertida turbinável: $|val\_energiavertidaturbinavel - val\_vazaovertidaturbinavel \times val\_produtividade| \le 10^{-4}$.
- **FR-007** *(R5)*: O sistema DEVE verificar a identidade da folga de geração: $|val\_folgadegeracao - \max(0, val\_disponibilidade - val\_geracao)| \le 10^{-4}$.
- **FR-008** *(revisado em 2026-10-05)*: O sistema DEVE exportar a base tratada, com as colunas de sinalização, nos formatos escolhidos pelo usuário (por padrão os três):
  - Parquet (`.parquet`) com tipos binários estritos (`double` para as métricas, `timestamp` para o instante).
  - Excel (`.xlsx`) com células numéricas nativas, abertas sem conflito de locale.
  - CSV (`.csv`) com delimitador `;`, ponto decimal, codificação UTF-8 e precisão integral (sem arredondamento).
- **FR-009** *(revisado em 2026-10-05)*: O sistema DEVE gerar um relatório de validação em Markdown e uma tabela em CSV com o resultado de R1 a R9 (registros avaliados, conformes, violações, taxa de conformidade, desvio máximo, desvio médio e situação). Todo o texto do relatório DEVE ser derivado dos resultados apurados, sem conclusões fixas; o relatório DEVE declarar que R1 a R5 não atestam a correção dos valores medidos e listar, em ordem cronológica, os primeiros 40 registros sinalizados. O perfil estatístico anual não faz parte deste relatório (ver User Story 3).
- **FR-010** *(novo em 2026-10-05)*: Valores ausentes NÃO DEVEM ser contados como violação em nenhuma regra; o total de valores ausentes nas métricas DEVE ser informado em log.
- **FR-011** *(novo em 2026-10-05)*: O sistema DEVE tratar `cod_usina` como inteiro que admite ausência (código inválido fica ausente, com aviso) e `din_instante` como data/hora; um `din_instante` que não possa ser interpretado DEVE interromper o processamento.
- **FR-012** *(R6; novo em 2026-10-05)*: O sistema DEVE sinalizar registros em que geração, disponibilidade, folga de geração ou energia vertida turbinável superem a potência instalada acrescida de 5% (50,4 MW), ou em que a vazão turbinada ou a vazão vertida turbinável superem o engolimento máximo da usina acrescido de 5% (171,2 m³/s).
- **FR-013** *(R7; novo em 2026-10-05)*: O sistema DEVE sinalizar registros em que a geração supere a disponibilidade declarada em mais de 1,0 MW.
- **FR-014** *(R8; novo em 2026-10-05)*: O sistema DEVE sinalizar registros com vazão turbinada positiva cuja produtividade esteja fora da faixa de 70% a 130% da produtividade nominal teórica da usina.
- **FR-015** *(R9; novo em 2026-10-05)*: O sistema DEVE sinalizar registros com vazão turbinada nula e geração acima de 1,0 MW.
- **FR-016** *(novo em 2026-10-05)*: Registros que violam R6 a R9 DEVEM ser mantidos na base tratada (não removidos) e sinalizados em uma coluna booleana por regra e em uma coluna-resumo de qualidade (`OK` ou os códigos violados). A base tratada DEVE ter o mesmo número de registros da base consolidada.
- **FR-017** *(novo em 2026-10-05)*: Os parâmetros técnicos da usina, as tolerâncias e os limites derivados DEVEM estar centralizados em um único ponto de configuração, com a fonte dos parâmetros indicada (RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3). Os limites DEVEM ser calculados a partir dos parâmetros, não digitados.
- **FR-018** *(novo em 2026-10-05)*: O sistema DEVE encerrar com código de saída 3, sem exportar, quando R1 for violada. Violações de R2 a R9 DEVEM ser registradas nos relatórios e no log, sem alterar o código de saída.
- **FR-019** *(novo em 2026-10-05)*: A validação e a geração de relatórios DEVEM estar ativadas por padrão e poder ser desligadas explicitamente pelo usuário.

### Key Entities *(include if feature involves data)*

- **Dicionário de Variáveis ONS**: Metadados oficiais das grandezas horárias contidos em `DicionarioDados_EnergiaVertidaTurbinavel.json` (código, descrição e unidade de cada coluna; versão 2.0 de 06-06-2024). Não contém faixas de valores.
- **Parâmetros Técnicos da Usina**: Potência instalada (2 × 24 MW), engolimento nominal por unidade (81,5 m³/s), queda bruta, perda hidráulica e rendimento turbina-gerador (RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3), e os limites e faixas deles derivados para R6 a R9.
- **Registro Operacional Tratado**: Medição horária com tipagem garantida, valores ausentes preservados e sinalização de anomalias (uma coluna por regra R6 a R9 e a coluna-resumo `qualidade_registro`).
- **Resultado de Regra**: Para cada regra R1 a R9, o grupo (consistência interna ONS ou plausibilidade física), a expressão avaliada, registros avaliados, conformes, violações, taxa de conformidade, desvios máximo e médio e situação (`CONFORME` ou `VIOLADA`).
- **Relatório de Validação**: Documento em Markdown e CSV com o resultado das regras, a leitura de cada uma e a lista dos registros sinalizados.
- **Sumário Estatístico Anual**: *(transferido para a Feature 003 em 30/09/2026)* Conjunto de indicadores estatísticos consolidados por ano operacional.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** *(revisado em 2026-10-05)*: 100% das células nas 10 colunas operacionais são numéricas ou ausentes; nenhuma é textual e nenhum valor ausente é convertido em zero.
- **SC-002** *(revisado em 2026-10-05)*: 100% dos registros são avaliados contra as 9 regras (R1 a R9), com a quantidade de violações de cada regra documentada. Resultado da execução de 30/09/2026 sobre 70.895 registros: R1 a R5 sem violação; R6 com 1 registro; R7 com 293; R8 com 185; R9 com 63; 526 registros distintos sinalizados (0,74%).
- **SC-003**: A base tratada é disponibilizada em formato Excel (`.xlsx`) e Parquet (`.parquet`), eliminando 100% dos problemas de interpretação de ponto/vírgula regional no Excel.
- **SC-004** *(substituído em 2026-10-05)*: O relatório de validação distingue consistência interna (R1 a R5) de plausibilidade física (R6 a R9) e declara expressamente que R1 a R5 não atestam que os valores medidos estejam corretos.
- **SC-005** *(novo em 2026-10-05)*: A base tratada tem exatamente o mesmo número de registros da base consolidada (70.895 em 30/09/2026); nenhum registro é removido por anomalia.
- **SC-006** *(novo em 2026-10-05)*: Todo registro sinalizado pode ser localizado pela coluna de qualidade e pelos códigos das regras (ex.: 15/05/2019 14h, `R6;R7;R8`).

## Assumptions

- O arquivo `DicionarioDados_EnergiaVertidaTurbinavel.json` na raiz do repositório é a versão de referência (Versão 2.0, 06-06-2024). Ele traz apenas código, descrição e unidade das colunas.
- Flutuações de arredondamento da ordem de $10^{-4}$ são toleradas nas identidades R1 a R5, por decorrerem da precisão com que o ONS publica as grandezas.
- Parâmetros técnicos da usina (RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3): 2 unidades geradoras de 24 MW (48 MW), turbinas Kaplan de eixo vertical, engolimento nominal de 81,5 m³/s por unidade, queda bruta de 35,24 m, perda hidráulica de 0,747 m e rendimento turbina-gerador de 0,9053. A produtividade nominal teórica é $1000 \times 9{,}81 \times (35{,}24 - 0{,}747) \times 0{,}9053 / 10^6 \approx 0{,}3063$ MW/(m³/s).
- A folga de 5% sobre os valores nominais, a faixa de 70% a 130% da produtividade nominal, a tolerância de 1,0 MW em R7 e o limiar de 1,0 MW em R9 são critérios de triagem adotados na auditoria, não valores normativos. Um registro sinalizado é indício a verificar, não erro confirmado.
- Vazão vertida total, vazão vertida não turbinável e energia vertida total não têm limite físico definido pela usina (dependem da cheia) e são verificadas apenas por R1 a R3.
- A base de entrada é a consolidada pela Feature 001: 70.895 registros horários de 28/08/2018 00h a 28/09/2026 23h, de uma única usina (`cod_usina` 153), sem horários duplicados.
- O registro de 15/05/2019 14h (68,743 MW) é o único que viola R6 e foi classificado como erro na publicação do ONS, confirmado pela CCEE. Essa confirmação foi obtida pela fiscalização, fora do pipeline; o pipeline apenas sinaliza o registro.
- Os arquivos processados são armazenados em `data/processed/`, preservando os dados brutos em `data/raw/`.

## Histórico de revisões

| Data | Item | Mudança | Motivo |
| :--- | :--- | :--- | :--- |
| 2026-09-30 | Documento | Criação da especificação (Status: Draft). | Pedido original do usuário. |
| 2026-10-05 | Status | "Draft" → "Implementado (revisado em 2026-10-05)". | A feature está implementada; as correções da auditoria de 30/09/2026 foram feitas por prompt, direto no código, e só agora documentadas (SDD retroativo). |
| 2026-10-05 | User Story 1 | Texto, teste independente e cenários ampliados: ausentes preservados, vírgula decimal, `cod_usina` inteiro anulável, `din_instante` inválido interrompe, CSV com precisão integral (cenários 2 a 6). | A versão original convertia ausentes em zero e arredondava o CSV; a auditoria corrigiu ambos em `src/processor.py`. |
| 2026-10-05 | User Story 2 | Título alterado de "Validação Física, Regulatória e Auditoria de Consistência" para "Validação de Consistência Interna, Plausibilidade Física e Auditoria"; regras R6 a R9 acrescentadas ao teste independente. | As 5 regras originais só verificam identidades de cálculo do ONS; não detectam valores fisicamente impossíveis (ex.: 68,743 MW em 15/05/2019 14h). |
| 2026-10-05 | User Story 2, cenário 1 | Original: "nenhuma linha viola a conservação de energia e vazão ou apresenta valores negativos". Novo: o resultado de cada regra é apurado e registrado, sem pressupor conformidade. | O critério original fixava o resultado antes da execução; o relatório passou a refletir o que os dados mostram. |
| 2026-10-05 | User Story 2, cenário 2 | Original: relatório "atestando a coerência dos dados". Novo (cenário 6): relatório derivado dos números, com a ressalva de que R1 a R5 não atestam a correção dos valores. | A conformidade em R1 a R5 não comprova a correção das medições. |
| 2026-10-05 | User Story 2, cenários 2 a 5 | Acrescentados: sinalização sem remoção, código de saída 3 para R1, ausentes não violam regras, conferência das colunas com o dicionário. | Comportamentos implementados em `src/validator.py` e `src/processor.py` na auditoria. |
| 2026-10-05 | User Story 3 | Marcada como transferida para a Feature 003; texto original mantido. | O perfil anual foi retirado do relatório de validação na auditoria e é produzido apenas por `src/analyzer.py` (Feature 003), evitando duas fontes para as mesmas estatísticas. |
| 2026-10-05 | Edge Cases | Casos 1 a 3 reescritos (R8/R9 na geração nula, tolerâncias próprias de R6 a R9, CSV no Excel PT-BR); 9 casos acrescentados. | O caso 3 original afirmava que o `.xlsx` e o `.parquet` "eliminam completamente" o risco, mas o CSV continua sujeito ao locale; os demais casos descrevem o tratamento de erros implementado. |
| 2026-10-05 | FR-001 | Original: ler o dicionário "como parâmetro de validação". Novo: conferir as colunas e citar a versão; o dicionário não é fonte de limites. | O dicionário não contém faixas de valores; os limites vêm dos parâmetros da usina (FR-017). |
| 2026-10-05 | FR-002 | Acrescentado: vírgula decimal, espaços e preservação de ausentes (nunca zero). | Converter ausente em zero fabrica medição e distorce totais e médias. |
| 2026-10-05 | FR-003 | Explicitados a tolerância ($-10^{-4}$) e a contagem por registro. | Comportamento implementado; o teste `test_r1_conta_registros_e_nao_celulas` o verifica. |
| 2026-10-05 | FR-004 a FR-007 | Associados aos códigos R3, R2, R4 e R5 e com a tolerância explicitada; conteúdo mantido. | Rastreabilidade entre requisito, regra e relatório. |
| 2026-10-05 | FR-008 | Acrescentados: colunas de sinalização, escolha de formatos, UTF-8 e precisão integral do CSV. | O CSV original arredondava as métricas; a auditoria passou a gravar todas as casas. |
| 2026-10-05 | FR-009 | Original: relatório "com métricas descritivas e auditoria de equações". Novo: resultado de R1 a R9, texto derivado dos números, ressalva sobre R1 a R5, lista dos registros sinalizados; sem perfil estatístico. | O relatório original continha parecer fixo ("rigorosamente satisfeita") e o perfil anual, que foi para a Feature 003. |
| 2026-10-05 | FR-010 a FR-019 | Acrescentados. | Requisitos implementados na auditoria de 30/09/2026 sem registro na spec (ausentes, tipos de identificação, R6 a R9, sinalização, parâmetros com fonte, código de saída, opções desligáveis). |
| 2026-10-05 | Key Entities | Acrescentadas "Parâmetros Técnicos da Usina" e "Resultado de Regra"; "Relatório de Consistência Física" renomeada "Relatório de Validação"; "Sumário Estatístico Anual" marcada como transferida. | Refletir as entidades implementadas. |
| 2026-10-05 | SC-001 | Acrescentado "ou ausentes" e a proibição de conversão de ausentes em zero. | Coerência com FR-002. |
| 2026-10-05 | SC-002 | "5 regras de consistência física" → 9 regras; incluído o resultado de 30/09/2026. | Inclusão de R6 a R9. |
| 2026-10-05 | SC-004 | Original: "O relatório de validação física comprova documentalmente a legitimidade dos valores de energia vertida turbinável e vazão vertida turbinável." Substituído pela distinção entre consistência e plausibilidade e pela ressalva sobre R1 a R5. | O critério original não é atingível: identidades de cálculo não comprovam a legitimidade de valores medidos. |
| 2026-10-05 | SC-005, SC-006 | Acrescentados. | Verificar que nenhum registro é removido e que os sinalizados são localizáveis. |
| 2026-10-05 | Assumptions | Acrescentados: conteúdo do dicionário, parâmetros da usina e fonte, natureza de triagem das tolerâncias, grandezas sem limite, período da base e o registro de 15/05/2019. | Premissas da implementação que não estavam escritas. |

### 2026-10-05 — spec 005 (conformidade com a constituição 1.1.0)

- `src/processor.py`: `--log-level` passa a valer para todos os loggers do pipeline (`configurar_nivel_log`), não só `processor` e `validator`.
- Suíte completa executada em 05/10/2026: 87 testes aprovados (inclui `tests/test_processor.py` e `tests/test_validator.py`). Resolve T050.

### 2026-10-05 — spec 006 (cópia de segurança dos dados processados)

- A base tratada e o relatório de validação física passam a ser gravados por `src/persistencia.py`, com `<arquivo>.bak` da versão anterior.
  - Arquivos: base tratada em CSV, Parquet e planilha; relatório de validação física em CSV e Markdown.
  - A planilha leva a propriedade `assinatura_dados` (SHA-256 dos dados), para que uma regravação com os mesmos dados não substitua a cópia.
  - Na base real, CSV, Parquet e Markdown ficaram byte a byte iguais aos anteriores.
