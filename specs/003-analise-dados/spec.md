# Feature Specification: Análise Estatística, Indicadores Operacionais, Visualização Gráfica e Relatório - UHE São Domingos

**Feature Branch**: `003-analise-dados`

**Created**: 2026-09-30

**Status**: Implementado (revisado em 2026-10-05)

**Input**: User description: "Quero análises estatísticas baseado nesse dado tratado como: - avaliação anual de: val_geracao, val_disponibilidade, val_vazaoturbinada, val_vazaovertida, val_vazaovertidanaoturbinavel, val_produtividade, val_folgadegeracao, val_energiavertida, val_vazaovertidaturbinavel, val_energiavertidaturbinavel; - Valores mínimos e máximos e em qual ano/mês/dia; - Indicar se a performance está satisfatória; - avaliar quais gráficos são interessantes para visualização, criar com seaborn no python;"

> **Revisão retroativa (2026-10-05)**: esta especificação foi reescrita para descrever o sistema como está implementado (`src/analyzer.py`, `src/pdf_generator.py`, `src/formatacao.py` e `src/config.py`). As correções da auditoria de 30/09/2026 e os ajustes de 02/10/2026 foram feitos por prompt, sem atualização prévia da spec. Cada requisito ou critério alterado ou removido, inclusive os dois pedidos do texto original que não foram mantidos ("indicar se a performance está satisfatória" e "criar com seaborn"), está registrado na seção **Histórico de revisões**, ao final. O texto anterior está preservado em `spec.md.2026-10-05.bak`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Perfil Estatístico Anual e Extremos do Período (Priority: P1)

Como fiscal da AGEMS responsável pela análise de desempenho de usinas hidrelétricas, quero o perfil estatístico descritivo anual das 10 grandezas operacionais contínuas e os valores mínimos e máximos do período com data e hora de ocorrência, para conhecer a distribuição histórica e os picos de operação e vertimento da UHE São Domingos no período coberto pelos dados do ONS.

**Why this priority**: Média, desvio e extremos são a base de qualquer análise e permitem rastrear eventos (cheias, paradas de máquinas, picos de vertimento turbinável) até a hora em que ocorreram.

**Independent Test**: Calcular o perfil anual sobre a base tratada e verificar que, para cada ano presente na série e cada uma das 10 grandezas, há registros considerados, média, desvio-padrão, mediana, percentis 25% e 75%, soma, mínimo e máximo com data e hora, e que os registros sinalizados com anomalia (R6 a R9) não entram nesses cálculos.

**Acceptance Scenarios**:

1. **Given** a base tratada da Feature 002 (na versão atual, 70.895 registros horários de 28/08/2018 00h a 28/09/2026 23h), **When** o perfil anual for calculado, **Then** cada combinação ano × grandeza traz registros considerados, média, desvio-padrão amostral, mediana, percentis 25% e 75%, soma acumulada, mínimo e máximo com data e hora, calculados apenas sobre os registros sem sinalização de anomalia.
2. **Given** a necessidade de auditar os recordes do período, **When** os extremos forem consultados, **Then** o sistema informa, para cada grandeza, o máximo e o mínimo do período com data e hora, excluindo os registros sinalizados (um registro de geração acima da potência instalada, por exemplo, não aparece como máximo).

---

### User Story 2 - Indicadores de Desempenho Operacional e Constatações Baseadas nos Dados (Priority: P1)

Como fiscal da AGEMS, quero indicadores anuais e do período completo de disponibilidade declarada, geração, garantia física e energia vertida turbinável (EVT), os eventos de parada e de indisponibilidade e constatações em texto montadas a partir desses números, para fundamentar a fiscalização sem conclusões que os dados não sustentam.

**Why this priority**: A versão anterior do relatório trazia números e conclusões fixos no código que a auditoria de 30/09/2026 mostrou serem falsos (fator de disponibilidade de 96,1%, parecer "SATISFATÓRIO", vertimento atribuído à plena carga e ao 1º trimestre). Em um documento que apoia fiscalização oficial, cada número e cada frase precisam ser rastreáveis aos dados. Como o conjunto do ONS não informa a causa do vertimento nem das reduções de geração, o sistema descreve o que os dados mostram e deixa a atribuição de causa para os documentos do agente e do ONS.

**Independent Test**: Executar a análise sobre uma série sintética com fatos conhecidos (30 h de indisponibilidade total, 5 h de usina parada com EVT, mudança de classificação do vertimento em jan/2024 e um registro anômalo) e verificar que indicadores, eventos e constatações reproduzem esses fatos e que o texto não contém as afirmações removidas na auditoria.

**Acceptance Scenarios**:

1. **Given** a base tratada, **When** os indicadores forem calculados, **Then** cada ano (com os anos parciais sinalizados) e o período completo trazem disponibilidade média declarada em % da potência instalada, diferença em pontos percentuais para a disponibilidade de referência da garantia física, (1 − IP) × (1 − TEIF), fator de capacidade, razão entre geração média e garantia física, energia gerada, EVT, parcela da EVT em horas de vertimento mínimo, índice EVT, horas com EVT, horas de usina parada com EVT e horas de indisponibilidade total.
2. **Given** a ocorrência de EVT, **When** ela for analisada junto com a geração e a disponibilidade da mesma hora, **Then** o sistema informa a parcela da EVT ocorrida com a usina próxima da plena carga, a parcela ocorrida com a usina parada (geração até 1 MW), a distribuição por faixa de geração e se a EVT ultrapassa a folga de geração em alguma hora, sem atribuir causa.
3. **Given** horas consecutivas de usina parada com EVT ou de disponibilidade zero, **When** os eventos forem identificados, **Then** cada evento traz início, fim e duração, uma lacuna de horário encerra o evento, e o relatório lista os eventos de indisponibilidade total com pelo menos 24 h e os 15 maiores eventos de parada por EVT (as listas completas vão para a planilha).
4. **Given** a mudança na forma como o ONS classifica o vertimento contínuo, **When** a série for analisada, **Then** o sistema detecta o mês da mudança (dez/2022 na série atual), informa os valores típicos antes e depois e registra que a série de EVT não é homogênea entre os dois períodos.
5. **Given** os resultados calculados, **When** as constatações forem montadas, **Then** são emitidas 12 constatações em texto (cobertura dos dados, disponibilidade, indisponibilidades, geração e garantia física, energia vertida turbinável, EVT e nível de geração, EVT com a usina parada, horas com geração zero, concentração diurna, distribuição ao longo do ano, mudança de classificação do vertimento e qualidade dos dados), todas montadas a partir dos números calculados e sem parecer categórico.

---

### User Story 3 - Visualização Gráfica (Priority: P2)

Como fiscal, quero 5 figuras em alta resolução que mostrem diretamente as grandezas citadas nas constatações (série temporal diária, EVT mensal, perfil horário por ano, disponibilidade e geração anuais frente às referências e vazões defluentes anuais), para apresentar os achados na fiscalização.

**Why this priority**: As figuras tornam visíveis padrões que as tabelas não evidenciam (indisponibilidades longas, a mudança de classificação do vertimento, a concentração diurna da EVT nos anos recentes), mas dependem dos resultados das histórias 1 e 2.

**Independent Test**: Gerar as figuras a partir da série sintética e verificar que os 5 arquivos PNG são gravados com os nomes do catálogo de figuras.

**Acceptance Scenarios**:

1. **Given** os resultados da análise, **When** o gerador de figuras for acionado, **Then** são gravadas 5 imagens PNG, por padrão a 300 DPI, cobrindo:
   - Médias diárias de disponibilidade declarada, geração e EVT, com faixas nos períodos de indisponibilidade total de pelo menos 24 h e linhas de referência da potência instalada e da garantia física.
   - EVT mensal em barras empilhadas, separando a EVT das horas de vertimento mínimo (vazão vertida até 6 m³/s) da EVT das demais horas, com marco vertical no mês da mudança de classificação do vertimento.
   - Perfil horário: mapas ano × hora do dia da geração média e da EVT média.
   - Disponibilidade média declarada e fator de capacidade por ano, em % da potência instalada, com as linhas da disponibilidade de referência da garantia física e da garantia física.
   - Vazões defluentes médias anuais (turbinada, vertida turbinável e vertida não turbinável) empilhadas, com a linha do engolimento máximo da usina (2 × 81,5 m³/s).
2. **Given** as figuras gravadas, **When** forem incorporadas ao relatório, **Then** têm título, eixos com unidades (MW, MWmed, MWh, m³/s, %), números no padrão brasileiro, anos parciais marcados com asterisco e legendas fora da área de dados.

---

### User Story 4 - Relatório em PDF e Markdown, Planilha e CSV Gerados a Partir dos Dados (Priority: P1)

Como fiscal, quero um relatório em PDF (A4 paisagem) e em Markdown, uma planilha com todas as tabelas calculadas e um CSV com os indicadores anuais, gerados a cada execução sem nenhum número ou conclusão fixo, para anexar ao processo de fiscalização (14 a 16/10/2026) e conferir qualquer valor na planilha.

**Why this priority**: É o produto entregue para a fiscalização. O PDF já existia na versão anterior, mas montava o texto com números e conclusões fixos; foi nele que a auditoria encontrou os erros.

**Independent Test**: Gerar o PDF e o Markdown a partir da série sintética, com e sem figuras, e verificar que o PDF é válido, que cada linha da tabela de indicadores anuais do Markdown corresponde aos valores calculados e que as afirmações removidas na auditoria não aparecem.

**Acceptance Scenarios**:

1. **Given** os resultados da análise, **When** o PDF for gerado, **Then** ele traz capa com identificação da usina nos dados do ONS, parâmetros técnicos e quadros-resumo dos principais indicadores, seguida de seções numeradas: principais constatações, fonte e cobertura dos dados, indicadores anuais, disponibilidade e geração por ano, série temporal, EVT mensal, perfil horário, EVT por nível de geração e eventos de usina parada, horas com geração zero por mês, vazões defluentes, qualidade dos dados e notas metodológicas com a tabela de parâmetros.
2. **Given** os mesmos resultados, **When** o Markdown for gerado, **Then** ele traz cabeçalho com período, identificação no ONS, agentes e características da usina, e seções numeradas automaticamente: constatações, indicadores anuais, eventos de indisponibilidade total, maiores eventos de usina parada com EVT, horas com geração zero por mês, EVT por nível de geração, registros sinalizados, extremos do período, notas metodológicas e lista de figuras.
3. **Given** que uma figura não está disponível, **When** o PDF for gerado, **Then** o documento traz um aviso no lugar da figura em vez de falhar.
4. **Given** que os dados opcionais definidos na spec 004 (`specs/004-conferencia-outros`) não estão disponíveis, **When** o relatório for gerado, **Then** ele sai apenas com a análise da base de EVT, com 12 constatações, sem as seções opcionais e com a numeração das seções sem lacunas.
5. **Given** a execução por linha de comando, **When** a geração das figuras for desligada, **Then** os relatórios usam as figuras já existentes; **When** qualquer etapa falhar, inclusive a geração do PDF, **Then** a execução termina com código de erro e a falha fica registrada no log.

---

### Edge Cases

- **Anos civis incompletos**: na versão atual a série vai de 28/08/2018 00h a 28/09/2026 23h, então 2018 e 2026 são parciais. Um ano é parcial quando o primeiro registro é posterior a 1º de janeiro 00h ou o último é anterior a 31 de dezembro 23h. Anos parciais aparecem nas tabelas com asterisco e com a cobertura correspondente e ficam fora das comparações entre anos (as constatações de disponibilidade, geração e distribuição ao longo do ano usam só anos completos). Médias e somas usam as horas reais, sem extrapolação.
- **Horas ausentes e duplicadas**: a cobertura lista as horas ausentes (na versão atual, uma hora, 04/11/2018 00h, no início do horário de verão) e conta os horários duplicados; uma lacuna de horário encerra qualquer evento de horas consecutivas.
- **Registros fisicamente implausíveis (R6 a R9)**: são mantidos nos totais e indicadores, por serem os dados publicados pelo ONS, sinalizados na coluna `qualidade_registro`, excluídos dos extremos e do perfil estatístico e listados na planilha.
- **Mudança de classificação do vertimento contínuo**: a partir de dez/2022 o ONS passa a registrar cerca de 5 m³/s do vertimento contínuo como vazão vertida não turbinável; antes, esse vertimento era contado como turbinável na maior parte das horas. A EVT é separada entre horas de vertimento mínimo e demais horas, e as constatações registram que a série não é homogênea.
- **Excesso de zeros**: a EVT é nula em parte das horas; os indicadores contam explicitamente as horas com EVT positiva, e as horas com geração exatamente zero são contadas por mês, separando as horas com disponibilidade zero das horas com a usina declarada disponível.
- **Fator de capacidade reduzido com disponibilidade alta**: a usina pode estar declarada disponível e gerar pouco. O conjunto de dados não informa a causa (restrição interna da usina, restrição elétrica ou energética, ordem de despacho); o sistema quantifica as horas e a EVT nessas condições e não atribui causa.
- **Arquivos auxiliares ausentes**: sem o relatório de auditoria da varredura ou o manifesto de versões da Feature 001, a cobertura é calculada só a partir da base e o relatório omite essas informações.
- **Dados opcionais da spec 004 ausentes**: o relatório é gerado sem as seções e constatações correspondentes (12 constatações).
- **Figura ausente**: o PDF mostra um aviso no lugar da figura.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE consumir a base tratada da Feature 002 (`uhe_sao_domingos_energia_vertida_tratado.parquet`, preferencialmente, ou `.xlsx`; um `.csv` com separador `;` pode ser informado explicitamente), ordená-la por `din_instante`, criar as colunas de ano, mês e hora e, se ausentes, calcular as sinalizações de anomalia R6 a R9 e a coluna `qualidade_registro`. *(revisado em 30/09/2026)*
- **FR-002**: O sistema DEVE processar a agregação estatística anual, para cada ano civil presente na base (2018 a 2026 na versão atual), das 10 grandezas operacionais contínuas: `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`, considerando apenas os registros sem sinalização de anomalia. *(revisado em 30/09/2026)*
- **FR-003**: O sistema DEVE computar, para cada grandeza e cada ano: registros considerados, média, desvio-padrão amostral, mediana, percentis 25% e 75%, soma acumulada, mínimo com data/hora e máximo com data/hora; e, para o período completo, o máximo e o mínimo de cada grandeza com data/hora. Os dois cálculos excluem os registros sinalizados. *(revisado em 30/09/2026)*
- **FR-004**: O sistema DEVE calcular, para cada ano (com cobertura e indicação de ano parcial) e para o período completo:
  - Disponibilidade média declarada (MWmed) e disponibilidade relativa = disponibilidade média declarada ÷ 48 MW (indicador aproximado; não é o FID regulatório).
  - Diferença, em pontos percentuais, entre a disponibilidade relativa e a disponibilidade de referência da garantia física, (1 − IP) × (1 − TEIF) = 90,97%.
  - Geração média (MWmed), fator de capacidade = geração média ÷ 48 MW e razão entre geração média e garantia física.
  - Energia gerada e EVT (MWh); EVT nas horas de vertimento mínimo e nas demais horas, com a participação da primeira; índice EVT = EVT ÷ (geração + EVT).
  - Horas com EVT positiva (quantidade e % das horas); horas de usina parada com EVT e EVT nessas horas; horas de indisponibilidade total; horas com disponibilidade acima de zero e até metade da potência instalada.
  - EVT média e geração média nas janelas diurna (9h às 15h) e noturna (20h às 5h) e as razões diurna/noturna.
  - Horas com registro sinalizado.
  - Somente no período completo: folga média de geração nas horas com EVT; EVT com geração a partir de 90% da potência instalada (plena carga); horas em que a EVT ultrapassa a folga de geração; disponibilidade média nas horas de usina parada com EVT; horas com geração zero (total, com EVT positiva) e horas com geração entre 0 e 1 MW e EVT positiva; EVT nos registros sinalizados; maior geração registrada, com data e hora.

  *(revisado em 30/09/2026: Fator de Disponibilidade (FID) e Fator de Indisponibilidade Total (FIT) removidos; ver Histórico de revisões)*
- **FR-005**: O sistema DEVE emitir constatações em texto, cada uma com tema e texto montados exclusivamente a partir dos resultados calculados, nesta ordem: cobertura dos dados; disponibilidade; indisponibilidades; geração e garantia física; energia vertida turbinável; EVT e nível de geração; EVT com a usina parada; horas com geração zero; concentração diurna; distribuição ao longo do ano; mudança de classificação do vertimento pelo ONS; qualidade dos dados (as constatações opcionais da spec 004 são intercaladas conforme aquela spec). O sistema NÃO DEVE emitir parecer categórico de desempenho nem atribuir causa ao vertimento ou às reduções de geração. *(substituído em 30/09/2026; tema "horas com geração zero" incluído em 02/10/2026)*
- **FR-006**: O sistema DEVE gerar 5 figuras PNG, por padrão a 300 DPI:
  1. `01_serie_temporal_disponibilidade_geracao_evt.png`: médias diárias de disponibilidade declarada, geração e EVT, com os períodos de indisponibilidade total de pelo menos 24 h destacados e linhas da potência instalada e da garantia física.
  2. `02_evt_mensal.png`: EVT mensal empilhada (parcela das horas de vertimento mínimo e parcela das demais horas), com marco no mês da mudança de classificação do vertimento.
  3. `03_perfil_horario_geracao_evt.png`: geração média e EVT média por ano × hora do dia.
  4. `04_disponibilidade_geracao_anual.png`: disponibilidade média declarada e fator de capacidade por ano, em % da potência instalada, com as linhas da disponibilidade de referência da garantia física e da garantia física.
  5. `05_vazoes_defluentes_anuais.png`: vazões médias anuais turbinada, vertida turbinável e vertida não turbinável, empilhadas, com a linha do engolimento máximo.

  *(substituído em 30/09/2026)*
- **FR-007**: O sistema DEVE consolidar os resultados em: relatório em PDF A4 paisagem (`reports/relatorio_analise_estatistica.pdf`); relatório em Markdown (`reports/relatorio_analise_estatistica.md`) com seções numeradas automaticamente; planilha Excel (`reports/perfil_estatistico_anual.xlsx`) com uma aba por tabela calculada (constatações, indicadores anuais e globais, cobertura por ano, agentes, EVT mensal, EVT por mês do ano, EVT por faixa de geração, perfis horários, eventos, horas com geração zero por mês, anomalias, resumo das anomalias, regras de validação, extremos, perfil estatístico anual e parâmetros); e CSV (`reports/perfil_estatistico_anual.csv`) com os indicadores anuais. *(revisado em 30/09/2026 e em 02/10/2026)*
- **FR-008**: O sistema DEVE informar a cobertura da série: primeiro e último registro, horas observadas e esperadas, horas ausentes, horários duplicados, cobertura de cada ano e anos parciais, agentes com o período de cada um, identificação da usina nos dados do ONS (código, reservatório, rio, bacia e subsistema) e, quando disponíveis, o resumo da auditoria da varredura (arquivos lidos, arquivos sem registros da usina, falhas e linhas com identificação divergente) e do manifesto de versões dos arquivos (Feature 001). *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-009**: O sistema DEVE agrupar horas consecutivas em eventos, encerrando o evento em qualquer lacuna de horário: (a) usina parada com EVT (geração até 1 MW e EVT positiva), com duração, geração média, disponibilidade média, vazão vertida média e EVT; (b) indisponibilidade total (disponibilidade declarada igual a zero, até 0,001 MW), com duração, vazão vertida média e geração média. O relatório DEVE listar os eventos de indisponibilidade total com pelo menos 24 h e os 15 maiores eventos de parada por EVT; as listas completas vão para a planilha. *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-010**: O sistema DEVE calcular a EVT por mês da série (com energia gerada, geração média, disponibilidade média e a separação entre EVT das horas de vertimento mínimo e EVT das demais horas), a participação de cada mês do ano na EVT somando apenas os anos completos, e a distribuição das horas com EVT por faixa de geração na mesma hora (até 1 MW; 1 a 10; 10 a 20; 20 a 30; 30 a 40; 40 a 43,2; 43,2 MW ou mais), com horas, EVT, participação, geração média e disponibilidade média. *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-011**: O sistema DEVE detectar o mês a partir do qual a mediana mensal de `val_vazaovertidanaoturbinavel` passa a ser positiva em todos os meses seguintes, sendo nula no mês anterior, e informar a vazão típica registrada como não turbinável depois da mudança, a vazão turbinável típica, a EVT média e o percentual de horas de vertimento mínimo contadas como turbináveis antes da mudança. Se não houver mudança, o sistema DEVE informar isso. *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-012**: O sistema DEVE calcular a geração média e a EVT média por ano e hora do dia e comparar, em cada ano, as janelas diurna (9h às 15h) e noturna (20h às 5h). *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-013**: O sistema DEVE contar, por ano e mês, as horas com geração exatamente zero, deixando vazios os meses sem dados na série, com o total anual e a separação entre horas com disponibilidade zero e horas com a usina declarada disponível. *(incluído em 05/10/2026; implementado em 02/10/2026)*
- **FR-014**: O sistema DEVE manter nos totais e indicadores os registros que violam as regras de plausibilidade física R6 a R9 (Feature 002), excluí-los dos extremos e do perfil estatístico e apresentar o resumo por regra (horas, primeira e última ocorrência, EVT), a lista cronológica dos registros sinalizados e o resultado das regras de validação R1 a R9. *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-015**: O relatório DEVE trazer notas metodológicas com definições e limitações, sem valores de resultado: fonte, granularidade horária e possibilidade de revisão dos dados pelo ONS; horário legal; definição da disponibilidade relativa e sua diferença para o FID regulatório; origem da garantia física e do IP e TEIF de referência; caráter indicativo da comparação com a garantia física; cálculo da EVT pelo ONS e ausência de informação de causa; limiares de análise; tratamento dos registros sinalizados; anos parciais. *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-016**: Todo número, data e frase dos relatórios (PDF, Markdown e planilha) DEVE ser gerado a partir dos resultados calculados na execução; os únicos valores fixos admitidos são os parâmetros documentados com fonte (FR-017). Os números DEVEM seguir o padrão brasileiro (milhar com ".", decimal com ","). *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-017**: Os parâmetros técnicos da usina, as grandezas derivadas deles e os limiares de análise e de validação DEVEM ser listados no relatório e na planilha com valor, unidade e origem. *(incluído em 05/10/2026; implementado em 30/09/2026)*
- **FR-018**: O relatório DEVE aceitar seções, constatações e abas opcionais definidas na spec 004 (`specs/004-conferencia-outros`). Sem esses dados, ele DEVE ser gerado apenas com a análise da base de EVT, com 12 constatações, sem as seções opcionais e com a numeração das seções sem lacunas. *(incluído em 05/10/2026; seções opcionais implementadas em 02/10/2026, sem spec)*
- **FR-019**: O sistema DEVE poder ser executado por linha de comando, com opções para indicar a base de entrada, as pastas de saída, a resolução das figuras e o nível de log, e para desligar a geração das figuras (reaproveitando as existentes) ou dos relatórios. Qualquer falha, inclusive na geração do PDF, DEVE encerrar a execução com código de erro e registro em log. *(incluído em 05/10/2026; corrigido em 30/09/2026)*

---

### Key Entities *(include if feature involves data)*

- **Cobertura dos Dados**: período da série, horas observadas, esperadas e ausentes, anos parciais, agentes e identificação da usina, com o resumo dos arquivos de origem quando disponível.
- **Perfil Estatístico Anual**: momentos estatísticos e extremos com data/hora de cada grandeza por ano, sem os registros sinalizados.
- **Extremos do Período**: máximo e mínimo de cada grandeza no período completo, com data/hora, sem os registros sinalizados.
- **Indicadores Anuais e Globais**: disponibilidade relativa e diferença para a referência da garantia física, fator de capacidade, razão com a garantia física, EVT e suas parcelas, horas por condição operativa e comparação diurno/noturno (substitui "Indicadores de Performance Energética").
- **Eventos**: sequências de horas consecutivas de usina parada com EVT ou de indisponibilidade total.
- **Distribuições de EVT**: por mês da série, por mês do ano (anos completos), por faixa de geração e por hora do dia.
- **Mudança de Classificação do Vertimento**: mês detectado e valores típicos antes e depois.
- **Registros Sinalizados**: registros que violam as regras R6 a R9 e o resumo por regra.
- **Constatações**: pares tema/texto montados a partir das entidades acima (substitui "Diagnóstico Técnico de Operação").
- **Parâmetros**: características da usina, grandezas derivadas e limiares, com valor, unidade e origem.
- **Catálogo de Figuras**: as 5 figuras e seus arquivos.
- **Resultados da Análise**: conjunto único que alimenta planilha, Markdown e PDF; inclui, quando presentes, os dados opcionais definidos na spec 004.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das 10 grandezas operacionais possuem perfil estatístico anual, para todos os anos da série, com mínimos, máximos e respectivos data e hora, calculados sem os registros sinalizados. *(revisado em 30/09/2026)*
- **SC-002**: O relatório apresenta os indicadores anuais de todos os anos da série (2018 a 2026 na versão atual), com os anos parciais sinalizados e a forma de cálculo de cada indicador explicada em legenda ou nota metodológica; nenhum parecer categórico é emitido. *(revisado em 30/09/2026)*
- **SC-003**: 100% das 5 figuras são geradas e salvas a 300 DPI (resolução padrão), com legendas fora da área de dados. *(revisado em 30/09/2026)*
- **SC-004**: O processamento estatístico e a geração das figuras para os 70.895 registros não ultrapassam 30 segundos. *(mantido; não foi medido novamente após as mudanças de 30/09 e 02/10/2026)*
- **SC-005**: O relatório Markdown gerado não contém nenhuma das afirmações removidas na auditoria ("96,1%", "Francis", "18/05/2018", "SATISFAT", "cumpre integralmente", "constrained"), e cada linha da tabela de indicadores anuais do Markdown é idêntica à linha formatada a partir dos valores calculados. *(incluído em 05/10/2026)*
- **SC-006**: Os totais conferem com a base: a soma das horas dos indicadores anuais é igual ao número de registros; a EVT total é igual à soma de `val_energiavertidaturbinavel`; a EVT por faixa de geração soma a EVT total e as participações somam 100%; a soma das horas com geração zero é igual à contagem na base. *(incluído em 05/10/2026)*
- **SC-007**: Sem os dados opcionais da spec 004, a análise produz exatamente 12 constatações e o Markdown numera as seções sem lacunas. *(incluído em 05/10/2026)*
- **SC-008**: O PDF é gerado como arquivo PDF válido com e sem as figuras disponíveis. *(incluído em 05/10/2026)*

---

## Assumptions

- Parâmetros técnicos da usina conforme o RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3: potência instalada de 48,00 MW, em 2 unidades geradoras de 24 MW com turbinas Kaplan de eixo vertical; engolimento nominal de 81,5 m³/s por unidade (163 m³/s na usina); indisponibilidade programada (IP) de 6,861% e taxa equivalente de indisponibilidade forçada (TEIF) de 2,333% de referência da garantia física; queda bruta de 35,24 m; perda hidráulica de 0,747 m; rendimento turbina-gerador de 90,53%; vazão remanescente de 4,78 m³/s. Operação comercial das 2 unidades liberada em 2013 (Despachos ANEEL nº 377/2013 e nº 2.692/2013, citados no RF). O modelo de RF de 2026 da AGEMS não é usado como fonte.
- Garantia física de 36,4 MWmed (ANEEL, valor vigente consultado em 02/10/2026); o RF de 2017 trazia 36,9 MWmed. O IP e o TEIF de referência são os do cálculo de garantia física registrado em 2017; a revisão posterior pode tê-los alterado, o que é informado nas notas metodológicas.
- Limiares de análise (parâmetros de trabalho, não normativos, listados no relatório): usina parada = geração até 1 MW; plena carga = geração a partir de 90% da potência instalada (43,2 MW); vertimento mínimo = vazão vertida até 6 m³/s (patamar contínuo observado na série, da ordem da vazão remanescente); indisponibilidade total = disponibilidade até 0,001 MW; eventos de indisponibilidade listados a partir de 24 h; 15 maiores eventos de parada no relatório; janela diurna das 9h às 15h e noturna das 20h às 5h; razão diurna/noturna a partir de 2 destacada no texto.
- O FID regulatório (razão IDv/ID, calculada com TEIP e TEIFa apurados) não consta do conjunto de Energia Vertida Turbinável; a disponibilidade relativa calculada aqui é uma aproximação.
- O conjunto de dados não informa a causa do vertimento, das reduções de geração nem dos desligamentos; a atribuição de causa depende de documentos do agente e do ONS.
- Os anos parciais são processados com as horas reais de amostragem, sem extrapolação de meses ausentes.
- Os horários são os publicados pelo ONS (horário legal).

---

## Histórico de revisões

### 2026-10-05 - Revisão retroativa (SDD)

Motivo: alinhar a spec ao sistema implementado. As correções de 30/09/2026 e os ajustes de 02/10/2026 foram feitos por prompt, sem atualização prévia da spec, contrariando o Princípio I da constituição; esta revisão os registra. Texto anterior preservado em `spec.md.2026-10-05.bak`.

| Item | O que mudou | Por quê |
| :--- | :--- | :--- |
| Título | De "Análise Estatística, Diagnóstico de Performance Operacional e Visualização Gráfica" para "Análise Estatística, Indicadores Operacionais, Visualização Gráfica e Relatório". | O sistema não emite diagnóstico nem parecer de desempenho (ver FR-005) e entrega um relatório PDF que não constava da spec. |
| Status | De "Draft" para "Implementado (revisado em 2026-10-05)". | Feature implementada e em uso. |
| Personas (US1 a US4) | "Engenheiro de planejamento energético e pesquisador regulatório", "gestor de ativos" e "analista técnico" passaram a "fiscal da AGEMS". | Uso real: apoio à fiscalização de 14 a 16/10/2026. |
| US2 | "Diagnóstico Regulatório e Avaliação de Performance" (parecer Satisfatório/Atenção/Crítico e identificação da causa do vertimento) substituída por "Indicadores de Desempenho Operacional e Constatações Baseadas nos Dados". | Ver FR-004 e FR-005. |
| US3 | Gráficos listados substituídos pelas 5 figuras implementadas. | Ver FR-006. |
| US4 | Incluída (relatório PDF e Markdown, planilha e CSV). | O PDF é o produto entregue e não constava da spec. |
| Edge cases | Início de 2018 corrigido de "18 de maio" para 28/08/2018 e fim de 2026 de "setembro" para 28/09/2026; incluídos horas ausentes, registros sinalizados, mudança de classificação do vertimento, arquivos auxiliares ausentes, dados opcionais da spec 004 ausentes e figura ausente. | A data de 18/05/2018 era falsa: a usina só aparece no conjunto do ONS a partir de 28/08/2018. Os demais casos já eram tratados no código. |
| FR-008 a FR-019 | Incluídos. | Registram comportamentos implementados em 30/09/2026 e 02/10/2026 sem spec. |
| SC-004 | Mantido, com a observação de que não foi medido novamente. | A execução passou a gerar também o PDF; o tempo não foi remedido nesta revisão. |
| SC-005 a SC-008 | Incluídos. | Formalizam verificações que já existem nos testes (`tests/test_analyzer.py`, `tests/test_pdf_generator.py` e, para a numeração sem os dados opcionais, `tests/test_indicadores_ons.py`). |
| Key Entities | "Indicadores de Performance Energética" (FC, FID, FIT, IVT) e "Diagnóstico Técnico de Operação" substituídos; incluídas Cobertura, Extremos, Eventos, Distribuições de EVT, Mudança de Classificação, Registros Sinalizados, Constatações, Parâmetros e Resultados da Análise. | Correspondem às estruturas efetivamente calculadas. |

### 2026-10-02 - Ajustes no relatório (feitos por prompt, sem spec)

| Item | O que mudou | Por quê |
| :--- | :--- | :--- |
| Assumptions (garantia física) | Garantia física de 36,9 MWmed substituída por 36,4 MWmed. | 36,4 MWmed é o valor vigente na ANEEL; 36,9 MWmed era o valor do RF de 2017. |
| FR-013 e FR-005 | Incluída a contagem mensal de horas com geração zero (aba `HORAS_GERACAO_ZERO_MES`, seção do relatório e constatação "Horas com geração zero"). | Pedido do usuário; distingue as horas com geração zero com a usina indisponível das horas com a usina declarada disponível. |
| FR-007 | A numeração das seções do Markdown, antes escrita no código, passou a ser automática. | Permitir seções opcionais sem quebrar a numeração. |
| FR-018 | O relatório passou a aceitar seções e constatações opcionais com os indicadores oficiais do ONS por unidade geradora. | Conteúdo especificado na spec 004 (`specs/004-conferencia-outros`); na 003 fica registrado apenas o ponto de extensão. |
| Cópia de segurança | Versão aprovada em 02/10/2026 (já com a garantia física de 36,4 MWmed e as horas com geração zero) preservada em `_backup_2026-10-02_relatorio_aprovado/`, antes da inclusão dos indicadores oficiais. | Permitir regenerar o relatório aprovado. |

### 2026-09-30 - Correções após a auditoria (feitas por prompt, sem spec)

A versão anterior tinha números e conclusões falsos fixos no código (relatórios preservados em `reports/_versao_anterior_2026-09-30/`, marcados como incorretos).

| Item | Texto anterior | O que mudou | Por quê |
| :--- | :--- | :--- | :--- |
| FR-001 | Consumir o Parquet ou o `.xlsx` tratado. | Aceita também `.csv` informado explicitamente; recalcula as sinalizações R6 a R9 se ausentes. | A análise passou a depender das sinalizações R6 a R9 introduzidas na Feature 002 em 30/09/2026; o recálculo permite usar bases que não têm essas colunas. |
| FR-002 e FR-003 | Estatísticas sobre todos os registros; "contagem de horas". | Estatísticas e extremos excluem os registros sinalizados; "contagem de horas" passou a "registros considerados". | Registros fisicamente implausíveis (ex.: geração acima da potência instalada) distorciam máximos e médias do perfil. |
| FR-004 | FC; FID = disponibilidade média ÷ 48 MW; FIT = 1 − FID; perda por vertimento turbinável; taxa de ocorrência de vertimento (horas com vertimento > 0). | FID e FIT removidos; a mesma razão passou a se chamar "disponibilidade relativa", tratada como aproximação e comparada com a disponibilidade de referência da garantia física (90,97%); incluídas a razão com a garantia física e as demais métricas; a taxa de ocorrência passou a contar horas com EVT positiva. | O FID regulatório é a razão IDv/ID calculada com TEIP e TEIFa apurados e não pode ser obtido deste conjunto. A versão anterior publicava "FID de 96,1%"; o valor calculado a partir dos dados é 87,8%. |
| FR-005 | Parecer categorizado (Satisfatório, Atenção, Insatisfatório) com justificativa das causas (hidrologia, restrição elétrica ou parada de unidades). | Substituído por constatações em texto geradas dos dados, sem parecer e sem atribuição de causa. | Pedido do texto original ("indicar se a performance está satisfatória") não mantido. Os limiares de classificação (FID ≥ 90%, 80% a 90%, < 80%) não tinham base regulatória; o conjunto não informa a causa; as conclusões fixas ("SATISFATÓRIO", "cumpre integralmente ANEEL", vertimento na plena carga e no 1º trimestre) eram contraditas pelos dados: no relatório de 02/10/2026, só 4,6% da EVT ocorreu com a usina próxima da plena carga, 28,4% com a usina parada, e maio a outubro concentraram 59,4% da EVT dos anos completos, contra 23,0% de janeiro a abril. |
| FR-006 | 5 gráficos com seaborn: série temporal horária, heatmap mês × hora, dispersão vazão × EVT com produtividade, boxplots anuais e balanço hídrico anual. | Substituídos pelas 5 figuras atuais, feitas diretamente em matplotlib, 300 DPI. O seaborn deixou de ser usado. | Pedido do texto original ("criar com seaborn") não mantido. As figuras passaram a mostrar as grandezas citadas nas constatações (disponibilidade frente às referências, EVT mensal com a mudança de classificação, perfil horário por ano); o texto que acompanhava o heatmap anterior afirmava concentração do vertimento turbinável no 1º trimestre, contradita pelos dados. |
| FR-007 | Relatório executivo em Markdown com tabelas em `.xlsx` e CSV. | Incluído o PDF A4 paisagem, montado a partir dos resultados (antes lia a planilha e tinha textos fixos); a planilha passou a ter uma aba por tabela calculada; o CSV contém os indicadores anuais. | O PDF existia sem spec e concentrava a maior parte das afirmações falsas ("96,1%", "Francis", "SATISFATÓRIO", "cumpre integralmente", 154 m³/s). |
| FR-019 (CLI) | `--generate-plots` e `--generate-report` sem forma de desligar; falha do PDF apenas registrada como aviso. | Opções com `--no-generate-plots` e `--no-generate-report`; falha do PDF encerra com código 1. | Parâmetros que não podiam ser desligados e falha silenciosa do PDF. |
| Edge cases | 2018 iniciando em 18 de maio. | 28/08/2018 00h; fim em 28/09/2026 23h. | O período 18/05/2018 a 30/09/2026 era falso. |
| Assumptions | 48 MW em 2 unidades de 24 MW com turbinas Kaplan de eixo vertical, "conforme Tabelas 1 a 3 do modelo do RF xxx/2026-AGEMS-SFT". | Fonte passou a ser o RF 0009/2017-AGEPAN-SFG; incluídos engolimento (2 × 81,5 = 163 m³/s), IP, TEIF, queda, perda, rendimento e vazão remanescente. | O usuário pediu para não citar o modelo de RF de 2026 como fonte. A versão anterior do relatório trazia turbinas "Francis" (são Kaplan) e engolimento de 154 m³/s (são 163 m³/s). |
| SC-002 | Diagnóstico de performance com cálculo dos índices regulatórios para os 9 exercícios. | Indicadores anuais com cálculo explicado e anos parciais sinalizados, sem parecer. | Consequência das mudanças em FR-004 e FR-005. |
| SC-003 | 5 gráficos a 300 DPI "sem cortes de legendas ou sobreposição de rótulos". | 5 figuras a 300 DPI com legendas fora da área de dados. | Critério reescrito conforme a montagem das figuras (legendas abaixo do gráfico e rótulos das linhas de referência à direita). |

### 2026-10-05 — spec 005 (conformidade com a constituição 1.1.0)

- As 5 figuras voltam a ser produzidas com seaborn (Requisito Técnico 5 da constituição 1.1.0, regra do usuário): `lineplot`, `histplot` ponderado e empilhado, `heatmap` e `barplot`, com tema único (`_tema_graficos`) e a paleta validada. Mesmos nomes de arquivo, 300 DPI e mesmos elementos; Markdown, planilha (32 abas) e CSV idênticos aos anteriores. A pendência T061 (retirar seaborn) fica superada.
- `src/analyzer.py`/`src/pdf_generator.py`: `--log-level` aplicado a todos os loggers.
- Suíte completa: 87 testes aprovados em 05/10/2026 (resolve T062). Tempo da análise completa (estatísticas, 5 figuras, planilha, Markdown e PDF): 10,2 s, dentro do SC-004 (resolve T063).
- Decisão do usuário (05/10/2026, pendência T064): o analisador não cria `.bak` dos relatórios em `reports/` antes de regravá-los; as versões aprovadas são preservadas por cópia datada antes de mudanças no pipeline. Exceção registrada na constituição 1.1.1 (Requisito Técnico 3).

### 2026-10-05 — spec 006 (bases complementares no relatório)

- **Seções novas**:
  - Identificação da usina no cadastro do ONS;
  - Disponibilidade operacional e sincronizada (ONS);
  - Afluência, vertimento e nível do reservatório (ONS);
  - Conferência da geração com a série oficial (ONS).
- **Constatações novas**: disponibilidade sincronizada e afluência; geração e cadastro só quando houver divergência.
- **Abas novas**: `DISP_*`, `HID_*`, `GER_*`, `CAD_FICHA` e `DICIONARIOS`.
- **Figuras novas**: 06 a 08, com seaborn e cores validadas pelo script da skill de visualização.
- As seções, constatações e abas que já existiam mantêm os números; só a numeração das seções mudou.

### 2026-10-06 — spec 007 (fonte de cada figura e tabela)

- O rodapé do PDF deixou de dizer que o relatório vem só do conjunto de EVT: cita a quantidade de conjuntos carregados e remete à legenda de cada figura e tabela.
- Cada figura, tabela e bloco do PDF e do Markdown tem a legenda "Fonte dos dados" (ou "Calculado neste relatório a partir de"), com conjuntos, identificador da usina, data de obtenção e conferências.
- Planilha: aba `FONTES`, a última. Números, constatações, seções, abas e figuras existentes inalterados.

### 2026-10-06 — spec 008 (relatório mais enxuto)

- Saiu a seção de constatações do início. A capa traz identificação, parâmetros, indicadores principais, data de geração e sumário; no PDF, com a página de cada seção e só na página 1.
- Cada constatação aparece uma única vez, no início da seção correspondente; o mapa constatação → seção fica em `src/estrutura_relatorio.py`, usado pelo PDF e pelo Markdown.
- O Markdown passou a ter a mesma estrutura do PDF: seções na mesma ordem, figuras no corpo, sem a seção "Figuras". As tabelas que só existiam num dos dois passaram aos dois.
- O rodapé do PDF ficou só com a numeração. As notas das bases complementares perderam a parte de fonte e mantiveram as ressalvas.
- Números, textos das constatações, abas e figuras inalterados.
