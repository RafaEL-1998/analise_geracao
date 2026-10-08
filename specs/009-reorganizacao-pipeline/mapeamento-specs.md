# Mapeamento das specs antigas para as specs por etapa

Cada US, FR e SC das specs 001 a 009, com a situação e o destino: a spec nova e o item novo, a constituição ou o motivo de estar superado. As specs novas estão em `novas-specs/` até a aprovação; a constituição, em `constituicao-rascunho.md`.

Total: 280 itens.

## 001-ons-coleta-sao-domingos

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 001 US1 — descoberta e download completo da EVT, cópia local na versão publicada | em vigor | 001-coleta-dados US1 (cenários 1, 2 e 10); FR-016, FR-017, FR-023 a FR-027 | 02/10/2026: base de EVT local mantida, sem novo download |
| 001 US2 — extração exaustiva e consolidação da EVT pelo código e pelo reservatório | em vigor | 001-coleta-dados US1 (cenários 4 a 6); FR-034 a FR-036, FR-041 | 05/10/2026: identificação pelo código da usina conferido pelo reservatório, sem o nome do agente |
| 001 US3 — relatório de auditoria da varredura | em vigor | 001-coleta-dados US2; FR-046 |  |
| 001 FR-001 — catálogo do ONS e recursos CSV da EVT | em vigor | 001-coleta-dados FR-016, FR-023 |  |
| 001 FR-002 — download com manifesto, reaproveitamento pela versão publicada, retentativas e gravação… | em vigor | 001-coleta-dados FR-024, FR-025, FR-027 |  |
| 001 FR-003 — 100 % dos arquivos, sem premissa de início de operação | em vigor | 001-coleta-dados FR-017 |  |
| 001 FR-004 — extração por cod_usina e nome do reservatório, parametrizável na execução | em vigor (parte) | 001-coleta-dados FR-034 e FR-035 (regra); os valores vêm do perfil (FR-006), e `--cod-usina` e `--nome-reservatorio` deixam de existir (FR-002) | 05/10/2026: identificação sem o nome do agente |
| 001 FR-005 — contagem das linhas que conferem só em parte, com alerta | em vigor | 001-coleta-dados FR-036 |  |
| 001 FR-006 — arquivo de origem e critério em cada linha; data do processamento por arquivo; versão no… | em vigor | 001-coleta-dados FR-040, FR-041, FR-046, FR-027 |  |
| 001 FR-007 — consolidação sem duplicidade, em ordem, prevalecendo o último arquivo lido | em vigor | 001-coleta-dados FR-041 |  |
| 001 FR-008 — auditoria com uma linha por arquivo | em vigor | 001-coleta-dados FR-046 |  |
| 001 FR-009 — execução não interativa, log na saída padrão e códigos 0, 1 e 2 | em vigor | 001-coleta-dados FR-002, FR-004, FR-005 (o código 2 cobre também opção inválida; falha de download passa a código 2, FR-026) |  |
| 001 FR-010 — leitura com ;, UTF-8 e releitura em Latin-1; FALHA sem interromper | em vigor | 001-coleta-dados FR-037 |  |
| 001 SC-001 — 100 % dos arquivos da EVT baixados e inspecionados | em vigor | 001-coleta-dados SC-001; SC-014 (42 arquivos) |  |
| 001 SC-002 — nenhum registro da usina omitido | em vigor | 001-coleta-dados SC-002, SC-003, SC-014 | 05/10/2026: a conferência externa de 02/10/2026 não ganha script no projeto |
| 001 SC-003 — varredura em menos de 3 minutos | em vigor | 001-coleta-dados SC-012 |  |
| 001 SC-004 — base consolidada em ordem e sem duplicatas | em vigor | 001-coleta-dados SC-003 |  |
| 001 SC-005 — auditoria de 100 % dos arquivos, inclusive os sem registros | em vigor | 001-coleta-dados SC-001; SC-014 |  |
| 001 SC-006 — troca de agente sem perda; linhas divergentes contadas | em vigor | 001-coleta-dados SC-002; US1 cenário 5 |  |

## 002-tratamento-dados

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 002 US1 — padronização e tipagem das grandezas | em vigor | 002-tratamento-dados US2 | 30/09/2026: pedido do usuário ("precisa que seja tudo número") |
| 002 US2 — consistência interna, plausibilidade física e auditoria | em vigor | 002-tratamento-dados US3 | 30/09/2026: pedido do usuário (valores negativos ou absurdos em todas as colunas) |
| 002 US3 — perfil estatístico anual | superado | superado: saiu do Tratamento; o perfil estatístico anual é calculado nas Análises (004-analises) |  |
| 002 US3 — perfil estatístico anual | superado | retirado do tratamento; o perfil estatístico, sem os registros sinalizados, está na 004-analises FR-021 |  |
| 002 FR-001 — dicionário de dados | em vigor | 002-tratamento-dados FR-006 (o dicionário lido é o da EVT obtido pela Coleta, em `data/raw/_dicionarios/`, e não mais o da raiz) | 07/10/2026: inventário aprovado (dicionário da raiz excluído) |
| 002 FR-002 — dez grandezas numéricas, ausentes preservados | em vigor | 002-tratamento-dados FR-007 | 30/09/2026: pedido do usuário |
| 002 FR-003 — R1 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-004 — R3 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-005 — R2 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-006 — R4 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-007 — R5 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-008 — exportação em Parquet, planilha e CSV | em vigor (parte) | 002-tratamento-dados FR-008 (os três formatos, sempre); a escolha de formatos pelo usuário é superada: o comando `tratamento` não tem opções (FR-001) |  |
| 002 FR-009 — relatório de validação | em vigor | 002-tratamento-dados FR-014 |  |
| 002 FR-010 — ausentes não violam regras | em vigor | 002-tratamento-dados FR-011 |  |
| 002 FR-011 — tipos de cod_usina e din_instante | em vigor | 002-tratamento-dados FR-007 |  |
| 002 FR-012 — R6 | em vigor | 002-tratamento-dados FR-009 e FR-010 (limites calculados do perfil; os valores da São Domingos ficam no cenário US3-4 e na SC-001) |  |
| 002 FR-013 — R7 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-014 — R8 | em vigor | 002-tratamento-dados FR-009 e FR-010 |  |
| 002 FR-015 — R9 | em vigor | 002-tratamento-dados FR-009 |  |
| 002 FR-016 — sinalizar sem remover | em vigor | 002-tratamento-dados FR-013 e FR-008 (mesmos registros da base extraída) |  |
| 002 FR-017 — parâmetros centralizados, com a fonte; limites calculados | em vigor (parte) | 001-coleta-dados FR-006 e FR-007 (parâmetros da usina com a fonte no perfil; derivados calculados a partir dele); tolerâncias e limites de R6 a R9 → 002-tratamento-dados |  |
| 002 FR-017 — parâmetros centralizados, com a fonte; limites calculados | em vigor (parte) | 002-tratamento-dados FR-010 (limites calculados do perfil; tolerâncias como regras gerais); parâmetros e fontes no perfil da usina → 001-coleta-dados (regras comuns do perfil) |  |
| 002 FR-018 — código 3 quando R1 é violada | em vigor (parte) | 002-tratamento-dados FR-012: a parada sem gravar continua; o código passa de 3 a 1, porque a etapa só tem os códigos 0, 1 e 5 e o 3 é o da Conferência (contrato da linha de comando) |  |
| 002 FR-019 — validação e relatórios desligáveis | superado | superado: não há opção para pular parte de uma etapa (001-coleta-dados FR-002); a validação faz parte do Tratamento de dados |  |
| 002 FR-019 — validação e relatórios desligáveis | superado | superado: a validação e o relatório fazem sempre parte do Tratamento; `--no-validate-physics` e `--no-generate-report` saem com o comando de etapa (002-tratamento-dados FR-001) |  |
| 002 SC-001 — células numéricas ou vazias | em vigor | 002-tratamento-dados SC-002 |  |
| 002 SC-002 — 100 % dos registros avaliados por R1 a R9 | em vigor | 002-tratamento-dados SC-003; contagens da São Domingos na SC-001 |  |
| 002 SC-003 — planilha e Parquet sem problema de vírgula e ponto | em vigor | 002-tratamento-dados SC-002 |  |
| 002 SC-004 — relatório separa os grupos e traz a ressalva sobre R1 a R5 | em vigor | 002-tratamento-dados SC-003 e FR-014 |  |
| 002 SC-005 — mesmo número de registros da base extraída | em vigor | 002-tratamento-dados SC-003 |  |
| 002 SC-006 — registros sinalizados localizáveis | em vigor | 002-tratamento-dados SC-003 |  |

## 003-analise-dados

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 003 US1 — perfil estatístico anual e extremos | em vigor | 004-analises US1; FR-021, FR-022; SC-003 |  |
| 003 US1 — perfil estatístico anual e extremos | em vigor (parte) | apresentação: 005-geracao-relatorio FR-007 (extremos na seção "Qualidade dos dados") e FR-038 (abas PERFIL_ESTATISTICO_ANUAL e EXTREMOS); cálculo: 004-analises |  |
| 003 US2 — indicadores, eventos e constatações a partir dos dados | em vigor | 004-analises US1 (indicadores e eventos) e US3 (constatações); FR-011 a FR-013, FR-043, FR-044 | 30/09/2026: auditoria — sem parecer nem atribuição de causa |
| 003 US2 — indicadores, eventos e constatações a partir dos dados | em vigor (parte) | apresentação: 005-geracao-relatorio FR-007, FR-008 (listas de eventos), FR-009 (constatações nas seções); cálculos e textos das constatações: 004-analises |  |
| 003 US3 — visualização gráfica | em vigor (parte) | dados das figuras: 004-analises FR-041; desenho das figuras: 005-geracao-relatorio |  |
| 003 US3 — visualização gráfica | em vigor (parte) | 005-geracao-relatorio US5, FR-034 a FR-037 (agora oito figuras); dados das figuras: 004-analises | 05/10/2026: todo gráfico com seaborn |
| 003 US4 — relatório em PDF, Markdown, planilha e CSV | em vigor (parte) | cenário 4 (sem as bases complementares, 12 constatações): 004-analises SC-004; demais cenários: 005-geracao-relatorio |  |
| 003 US4 — relatório em PDF, Markdown, planilha e CSV | em vigor | 005-geracao-relatorio US1, US2, US6; FR-003, FR-007, FR-011, FR-017, FR-038, FR-039. Aplicadas as revisões: sem lista inicial de constatações (FR-009), capa com sumário (FR-011); as opções `--no-generate-*` saem (comando único) | 06/10/2026: relatório enxuto |
| 003 FR-001 — consumo da base tratada | em vigor (parte) | leitura da base tratada do Tratamento: 004-analises FR-003; escolha do arquivo de entrada (.parquet, .xlsx ou .csv) e recálculo das sinalizações ausentes: superado — a entrada é sempre a base tratada, que já traz as sinalizações R6 a R9 (002-tratamento-dados) |  |
| 003 FR-002 — agregação anual das 10 grandezas sem os sinalizados | em vigor | 004-analises FR-021 |  |
| 003 FR-003 — estatísticas anuais e extremos com data e hora | em vigor | 004-analises FR-021, FR-022 |  |
| 003 FR-004 — indicadores anuais e do período | em vigor | 004-analises FR-011, FR-012; potência, garantia física e referências vêm do perfil: FR-007 | 30/09/2026: FID e FIT substituídos pela disponibilidade relativa; 02/10/2026: garantia física de 36,4 MWmed |
| 003 FR-005 — constatações sem parecer nem causa | em vigor | redação nova: constatações descrevem fatos dos dados, sem parecer (004-analises FR-043, FR-044); a conclusão é gerada por regras declaradas e aponta indícios sem afirmar causa (FR-045 a FR-051) | 30/09/2026: auditoria — sem parecer; 07/10/2026: conclusão por regras |
| 003 FR-006 — cinco figuras | em vigor (parte) | dados das figuras: 004-analises FR-041; figuras: 005-geracao-relatorio |  |
| 003 FR-006 — cinco figuras | em vigor (parte) | 005-geracao-relatorio FR-034 e FR-035 (oito figuras, seaborn); dados das figuras: 004-analises | 05/10/2026: seaborn |
| 003 FR-007 — PDF, Markdown, planilha e CSV | em vigor | 005-geracao-relatorio FR-003 (pasta `reports/<slug>/`), FR-038 (lista de abas atual: 58 com todos os conjuntos da São Domingos), FR-039 |  |
| 003 FR-008 — cobertura da série | em vigor | 004-analises FR-010 |  |
| 003 FR-008 — cobertura da série | em vigor (parte) | quadro da seção "Fonte e cobertura dos dados": 005-geracao-relatorio FR-007 e Edge Cases (sem auditoria ou manifesto); cálculo: 004-analises |  |
| 003 FR-009 — eventos de usina parada com EVT e de indisponibilidade total | em vigor (parte) | eventos, com as listas completas: 004-analises FR-013; o que o relatório lista (≥ 24 h e 15 maiores): 005-geracao-relatorio |  |
| 003 FR-009 — eventos de usina parada com EVT e de indisponibilidade total | em vigor (parte) | limites de apresentação e lista completa na planilha: 005-geracao-relatorio FR-008; agrupamento em eventos: 004-analises |  |
| 003 FR-010 — EVT mensal, mês do ano e faixas de geração | em vigor | 004-analises FR-014 a FR-016; faixas intermediárias do perfil: FR-007, FR-008 |  |
| 003 FR-011 — mudança de classificação do vertimento | em vigor (parte) | detecção e valores: 004-analises FR-019; "informar quando não há mudança": superado — sem o fenômeno, a constatação não aparece (FR-019, FR-044) |  |
| 003 FR-012 — perfil horário e janelas diurna e noturna | em vigor | 004-analises FR-011, FR-017 |  |
| 003 FR-013 — horas com geração zero por mês | em vigor | 004-analises FR-018 | 02/10/2026: pedido do usuário |
| 003 FR-014 — registros sinalizados (R6 a R9) | em vigor (parte) | nos totais, fora dos extremos e do perfil, lista, resumo por regra e resultado de R1 a R9: 004-analises FR-020 a FR-022; apresentação: 005-geracao-relatorio | 30/09/2026: auditoria |
| 003 FR-014 — registros sinalizados (R6 a R9) | em vigor (parte) | resumo por regra, lista e regras R1 a R9 no relatório e na planilha: 005-geracao-relatorio FR-007, FR-038; manutenção nos totais e exclusão dos extremos: 004-analises |  |
| 003 FR-015 — notas metodológicas | em vigor | 005-geracao-relatorio FR-020 (com as notas dos conjuntos opcionais e da conclusão) | 02/10/2026: garantia física de 36,4 MWmed |
| 003 FR-016 — números e frases gerados dos dados, no padrão brasileiro | em vigor (parte) | textos gerados nas Análises: 004-analises FR-009, FR-043; textos e tabelas do relatório: 005-geracao-relatorio |  |
| 003 FR-016 — números e frases gerados dos dados, no padrão brasileiro | em vigor (parte) | tabelas, legendas, notas e capa: 005-geracao-relatorio FR-018; textos das constatações: 004-analises |  |
| 003 FR-017 — parâmetros com valor, unidade e origem | em vigor (parte) | nas Análises, só o período das bases complementares usado na tabela (004-analises FR-042); a tabela e a aba ficam na Geração do relatório (005-geracao-relatorio FR-022) |  |
| 003 FR-017 — parâmetros com valor, unidade e origem | em vigor | 005-geracao-relatorio FR-022 (hoje a tabela é montada dentro da análise; passa a ser requisito do relatório) | 30/09/2026: modelo de RF de 2026 não citado |
| 003 FR-018 — seções, constatações e abas opcionais; 12 constatações sem elas | em vigor (parte) | constatações condicionais e 12 sem as bases complementares: 004-analises FR-044, SC-004; seções, abas e numeração: 005-geracao-relatorio |  |
| 003 FR-018 — seções, constatações e abas opcionais; 12 constatações sem elas | em vigor (parte) | seções opcionais e numeração sem lacunas: 005-geracao-relatorio FR-007; 12 constatações: 004-analises |  |
| 003 FR-019 — linha de comando das análises; falha com código de erro | em vigor (parte) | nível de log e código de erro → 001-coleta-dados FR-004 e FR-005; opções de base de entrada, pastas, resolução e de desligar figuras superadas pela linha de comando única (FR-002); o restante → 005-geracao-relatorio |  |
| 003 FR-019 — linha de comando das análises; falha com código de erro | em vigor (parte) | comando da etapa e código 1 com registro no log: 004-analises FR-001, FR-004; opções de arquivo de entrada, pastas, DPI e desligamento de figuras ou relatórios: superado — linha de comando única (001-coleta-dados) e figuras na 005-geracao-relatorio |  |
| 003 FR-019 — linha de comando das análises; falha com código de erro | em vigor (parte) | falha, inclusive do PDF, com código 1: 005-geracao-relatorio FR-006; opções de base de entrada, pastas, DPI, `--no-generate-plots` e `--no-generate-report`: superadas pelo comando `relatorio --usina` |  |
| 003 SC-001 — perfil estatístico de 100 % das grandezas | em vigor | 004-analises SC-003 |  |
| 003 SC-002 — indicadores de todos os anos, sem parecer | em vigor (parte) | indicadores com anos parciais, sem parecer: 004-analises FR-011, FR-043, SC-001; forma de cálculo em legenda ou nota: 005-geracao-relatorio |  |
| 003 SC-002 — indicadores de todos os anos, sem parecer | em vigor (parte) | anos parciais marcados e cálculo explicado em nota: 005-geracao-relatorio FR-008, FR-020; ausência de parecer: 004-analises |  |
| 003 SC-003 — figuras a 300 DPI, legendas fora da área de dados | em vigor | 005-geracao-relatorio SC-008, FR-035 (oito figuras) |  |
| 003 SC-004 — estatísticas e figuras em 30 s | em vigor (parte) | processamento estatístico: 004-analises SC-010; figuras: 005-geracao-relatorio |  |
| 003 SC-004 — estatísticas e figuras em 30 s | em vigor (parte) | relatório em até 1 min (meta do plano da 009): 005-geracao-relatorio SC-012; tempo das análises: 004-analises |  |
| 003 SC-005 — afirmações removidas ausentes; tabela anual igual aos valores | em vigor (parte) | constatações sem as afirmações removidas: 004-analises US3 (cenário 3), SC-004; Markdown e tabela anual: 005-geracao-relatorio |  |
| 003 SC-005 — afirmações removidas ausentes; tabela anual igual aos valores | em vigor | afirmações: 005-geracao-relatorio SC-001; tabela anual igual aos valores calculados: SC-007 |  |
| 003 SC-006 — totais conferem com a base | em vigor | 004-analises SC-002 |  |
| 003 SC-007 — 12 constatações sem os dados opcionais | em vigor (parte) | 12 constatações: 004-analises SC-004; numeração das seções: 005-geracao-relatorio |  |
| 003 SC-007 — 12 constatações sem os dados opcionais | em vigor (parte) | 12 seções numeradas sem lacunas só com a EVT: 005-geracao-relatorio SC-010; 12 constatações: 004-analises |  |
| 003 SC-008 — PDF válido com e sem figuras | em vigor | 005-geracao-relatorio SC-010, FR-016 (aviso de figura ausente) |  |

## 004-conferencia-outros

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 004 US1 — operação verificada × programação diária | em vigor (parte) | 001-coleta-dados US1 e FR-043 (obtenção e extração da programação); programação horária e dias ausentes → 002-tratamento-dados; cruzamento com a EVT, seção e constatação → 004-analises e 005-geracao-relatorio |  |
| 004 US1 — operação verificada × programação diária | em vigor (parte) | 002-tratamento-dados US5 (programação horária e dias sem arquivo); coleta dos arquivos → 001-coleta-dados; classificação das horas, eventos e perfil → 004-analises; seção e ressalvas → 005-geracao-relatorio | 02/10/2026: base de EVT mantida; a programação é recortada no período dela |
| 004 US1 — operação verificada × programação diária | em vigor (parte) | cruzamento, eventos e constatação: 004-analises US2, FR-026 a FR-029, FR-044; obtenção e extração: 001-coleta-dados; programação horária e dias ausentes: 002-tratamento-dados; seção: 005-geracao-relatorio |  |
| 004 US1 — operação verificada × programação diária | em vigor (parte) | cenário 4 (seção, tabelas e ressalvas): 005-geracao-relatorio FR-007, FR-020; coleta, cruzamento e constatação: 001-coleta-dados, 002-tratamento-dados e 004-analises |  |
| 004 US2 — indicadores oficiais por unidade geradora | em vigor (parte) | 001-coleta-dados US1 e FR-042 (obtenção e extração); tipagem, versão mais recente e recorte → 002-tratamento-dados; DISPF × horas e TEIFa/TEIP recalculadas → 003-conferencia; decomposição, seção e constatações → 004-analises e 005 |  |
| 004 US2 — indicadores oficiais por unidade geradora | em vigor (parte) | 002-tratamento-dados US5 (tabelas tratadas, versão mais recente, identidade das horas, recorte); coleta → 001-coleta-dados; recálculo da TEIFa e da TEIP e divergências DISPF × horas → 003-conferencia; decomposição, seção e constatações → 004-analises e 005-geracao-relatorio |  |
| 004 US2 — indicadores oficiais por unidade geradora | em vigor (parte) | 003-conferencia US3, FR-014 a FR-016 (cenários 2 e 3: TEIFa e TEIP recalculadas reproduzem as publicadas; meses-unidade com DISPF e horas divergentes em mais de 1 h); cenário 1 (obter os quatro conjuntos pelo CEG, versão mais recente, recorte) → 001-coleta-dados e 002-tratamento-dados; identidade das horas do cenário 2 → 002-tratamento-dados; cenário 4 (seção e constatações) → 004-analises e 005-geracao-relatorio |  |
| 004 US2 — indicadores oficiais por unidade geradora | em vigor (parte) | DISPF por ano, indicadores anuais, horas por estado, decomposição e as duas constatações: 004-analises US2, FR-023 a FR-025, FR-044; obtenção: 001-coleta-dados; tratamento: 002-tratamento-dados; recálculo da TEIFa e da TEIP e divergências DISPF × horas: 003-conferencia; seção: 005-geracao-relatorio |  |
| 004 US2 — indicadores oficiais por unidade geradora | em vigor (parte) | cenário 4 (seção e tabelas): 005-geracao-relatorio FR-007, FR-013 (DISPF na capa); coleta, conferências e constatações: 001-coleta-dados, 003-conferencia e 004-analises |  |
| 004 US3 — Registro das conferências com outras fontes | em vigor (parte) | 003-conferencia, seção "Conferências manuais (fora do fluxo)" (CCEE, BI da ANEEL e S3 do ONS) e FR-006; as fontes do ONS consultadas em 02/10/2026 que entraram no fluxo viraram conferências (003-conferencia FR-002) ou bases da coleta (001-coleta-dados); as fontes descartadas (classificação de EVT do SIN, interrupção de carga) e a lacuna dos eventos individuais de desligamento ficam só no histórico do git | 05/10/2026: bases da CCEE e da ANEEL fora do fluxo; 06/10/2026: conferências manuais fora do relatório; 07/10/2026: arquivos de apoio excluídos, resultados registrados na spec da Conferência |
| 004 FR-001 — arquivos diários da programação no período da EVT, com reaproveitamento | em vigor | 001-coleta-dados FR-016 a FR-018, FR-024 | 02/10/2026: demais bases no período da EVT |
| 004 FR-002 — extração pelo código de exibição, conferida pelo nome e pelo estado; auditoria por arquivo | em vigor | 001-coleta-dados FR-034, FR-036, FR-043, FR-046 (com a contagem "só conferência" acrescentada) |  |
| 004 FR-003 — dia pelo nome do arquivo; data interna conferida nos dois formatos | em vigor | 001-coleta-dados FR-043 |  |
| 004 FR-004 — 48 patamares em valores horários, na hora de início | em vigor | 002-tratamento-dados FR-026 |  |
| 004 FR-005 — dias sem arquivo e dias incompletos | em vigor (parte) | 001-coleta-dados FR-043 e FR-046 (dia `INCOMPLETO` na auditoria); lista de dias sem arquivo → 002-tratamento-dados |  |
| 004 FR-005 — dias sem arquivo e dias incompletos | em vigor (parte) | 002-tratamento-dados FR-027 (dias sem arquivo); dias com patamares incompletos → auditoria da 001-coleta-dados |  |
| 004 FR-006 — classificação das horas comuns pela programação | em vigor | 004-analises FR-026 |  |
| 004 FR-007 — resumo por mês e no período comum | em vigor | 004-analises FR-027, FR-028 |  |
| 004 FR-008 — eventos de usina parada com programação acima do limiar | em vigor | 004-analises FR-029 |  |
| 004 FR-009 — constatação e seção da programação, com as ressalvas | em vigor (parte) | constatação com as ressalvas: 004-analises FR-044; seção: 005-geracao-relatorio |  |
| 004 FR-009 — constatação e seção da programação, com as ressalvas | em vigor (parte) | seção, tabelas e ressalvas nas notas: 005-geracao-relatorio FR-007, FR-020; constatação: 004-analises |  |
| 004 FR-010 — etapa executável no pipeline e isolada, sem alterar a EVT, sem rede nos testes | superado | superado: não há execução por conjunto; a coleta cobre os dez conjuntos (001-coleta-dados FR-002) e, sem novidade, não baixa nada (SC-004); testes sem rede ficam na constituição |  |
| 004 FR-011 — quatro conjuntos de indicadores, filtro pelo CEG, versão mais recente e recorte | em vigor (parte) | 001-coleta-dados FR-016, FR-017, FR-034, FR-042 (obtenção e extração pelo CEG, conferida pelo id ONS nos indicadores por UG); versão mais recente e recorte → 002-tratamento-dados |  |
| 004 FR-011 — quatro conjuntos de indicadores, filtro pelo CEG, versão mais recente e recorte | em vigor (parte) | 002-tratamento-dados FR-021 a FR-024 (versão mais recente e recorte no período); obtenção e filtro pelo CEG → 001-coleta-dados |  |
| 004 FR-012 — identidade das horas, recálculo e divergências | em vigor (parte) | 002-tratamento-dados FR-022 (identidade das horas, resíduo e aviso acima de 0,1 h); recálculo da TEIFa e da TEIP e divergências DISPF × horas → 003-conferencia |  |
| 004 FR-012 — identidade das horas, recálculo e divergências | em vigor (parte) | recálculo em janela de 60 meses → 003-conferencia FR-015 e FR-016; divergências entre DISPF e horas do TEIP → 003-conferencia FR-014; identidade das horas (HP = soma das parcelas, tolerância de 0,1 h) → 002-tratamento-dados |  |
| 004 FR-013 — relatório com os indicadores oficiais e duas constatações | em vigor (parte) | dados e as duas constatações: 004-analises FR-023 a FR-025, FR-044; divergências: 003-conferencia; seção e tabelas: 005-geracao-relatorio |  |
| 004 FR-013 — relatório com os indicadores oficiais e duas constatações | em vigor (parte) | tabelas da seção: 005-geracao-relatorio FR-007; constatações e cálculos: 004-analises |  |
| 004 FR-014 — registro das fontes consultadas, inclusive as que não trazem o dado procurado | em vigor (parte) | como na 004 US3: conferências manuais → 003-conferencia, seção "Conferências manuais (fora do fluxo)"; o restante do registro de 02/10/2026 fica só no histórico do git | 05/10/2026, 06/10/2026 e 07/10/2026, como na 004 US3 |
| 004 SC-001 — dias obtidos ou listados; 48 patamares ou incompletos | em vigor (parte) | 001-coleta-dados SC-001 e FR-043 (obtenção e `INCOMPLETO`); lista de dias ausentes → 002-tratamento-dados |  |
| 004 SC-001 — dias obtidos ou listados; 48 patamares ou incompletos | em vigor (parte) | 002-tratamento-dados SC-005 (dias); patamares → 001-coleta-dados |  |
| 004 SC-002 — 100 % das horas paradas com EVT classificadas | em vigor | 004-analises SC-005 |  |
| 004 SC-003 — segunda execução sem mudança não baixa nada | em vigor | 001-coleta-dados SC-004 |  |
| 004 SC-004 — números da constatação e da seção iguais aos da planilha | em vigor (parte) | números das constatações e da conclusão: 004-analises SC-009; seção: 005-geracao-relatorio |  |
| 004 SC-004 — números da constatação e da seção iguais aos da planilha | em vigor (parte) | números das tabelas e legendas iguais aos da planilha: 005-geracao-relatorio SC-007; constatação: 004-analises |  |
| 004 SC-005 — programação em menos de 2 minutos | em vigor (parte) | 001-coleta-dados SC-012 (leitura e extração, no tempo da coleta); cruzamento → 004-analises |  |
| 004 SC-005 — programação em menos de 2 minutos | superado (parte) | superado na parte do Tratamento: a programação deixa de ser uma etapa própria e o tempo passa a valer para o Tratamento inteiro (002-tratamento-dados SC-010); leitura → 001-coleta-dados e cruzamento → 004-analises decidem a sua parte |  |
| 004 SC-005 — programação em menos de 2 minutos | em vigor (parte) | cruzamento: 004-analises SC-010; leitura e montagem: 002-tratamento-dados |  |
| 004 SC-006 — EVT e saídas anteriores inalteradas pela etapa da programação | superado | superado: não há etapa isolada por conjunto; sem novidade, a extração da EVT se repete igual (001-coleta-dados SC-004 e SC-014) |  |
| 004 SC-007 — TEIFa e TEIP recalculadas iguais às publicadas nos meses com janela completa | em vigor | 003-conferencia SC-001 (21 de 21 meses) e FR-016 (critério "até 0,001 p.p.", como no código; a spec antiga dizia "inferior a") |  |

## 005-conformidade-constituicao

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 005 US1 — versões anteriores de arquivos republicados | em vigor (parte) | 001-coleta-dados US5 (cenários 1 a 3 e 5); FR-028, FR-030. O cenário "todas as versões preservadas" é superado pelo limite de duas (FR-029) | 07/10/2026: no máximo duas versões anteriores por arquivo |
| 005 US2 — gráficos com seaborn | em vigor | 005-geracao-relatorio US5, FR-035 | 05/10/2026: regra do usuário (seaborn) |
| 005 US3 — nível de log único | em vigor | 001-coleta-dados US4 (cenários 6 e 7); FR-004 |  |
| 005 US4 — linhas com formato irregular | em vigor | 001-coleta-dados US2 (cenário 4); FR-038 |  |
| 005 US5 — lista de dependências fiel ao uso | em vigor | constituição: Requisito Técnico 1 (só as dependências efetivamente usadas, versionadas em `requirements.txt`) |  |
| 005 FR-001 — preservar a cópia anterior em área própria | em vigor | 001-coleta-dados FR-028 |  |
| 005 FR-002 — registro da versão preservada no manifesto | em vigor | 001-coleta-dados FR-027, FR-028 |  |
| 005 FR-003 — conteúdo idêntico não gera versão | em vigor | 001-coleta-dados FR-028 |  |
| 005 FR-004 — versões anteriores nunca lidas | em vigor | 001-coleta-dados FR-030 |  |
| 005 FR-004 — versões anteriores nunca lidas | em vigor (parte) | 002-tratamento-dados FR-002 (o Tratamento não lê brutos nem versões anteriores); extração → 001-coleta-dados |  |
| 005 FR-005 — regra para EVT, indicadores e programação | em vigor (ampliada) | 001-coleta-dados FR-028 a FR-030 (vale para os dez conjuntos e para os dicionários) |  |
| 005 FR-006 — figuras com seaborn; tema, paleta e tipografia centrais; 300 DPI | em vigor | 005-geracao-relatorio FR-035 (oito figuras) | 05/10/2026: seaborn |
| 005 FR-007 — textos e tabelas idênticos aos da versão anterior | superado | não regressão pontual da troca para seaborn; a não regressão geral está em 005-geracao-relatorio SC-001 |  |
| 005 FR-008 — nível de log em todos os módulos | em vigor | 001-coleta-dados FR-004 |  |
| 005 FR-009 — linhas irregulares contadas, avisadas e não extraídas | em vigor (ampliada) | 001-coleta-dados FR-038 (todos os CSV) |  |
| 005 FR-010 — requirements.txt com exatamente os pacotes importados | em vigor | constituição: Requisito Técnico 1 |  |
| 005 SC-001 — teste de republicação | em vigor | 001-coleta-dados SC-005 (com o limite de duas) | 07/10/2026: no máximo duas versões |
| 005 SC-002 — nenhuma mensagem informativa com nível de aviso | em vigor | 001-coleta-dados SC-008 |  |
| 005 SC-003 — 2 linhas irregulares no teste; 0 nos arquivos atuais | em vigor | 001-coleta-dados SC-007 |  |
| 005 SC-004 — 100 % dos pacotes importados listados, e só eles | em vigor | constituição: Requisito Técnico 1 |  |
| 005 SC-005 — mesmos nomes e 300 DPI; textos iguais antes e depois | em vigor (parte) | nomes e 300 DPI: 005-geracao-relatorio FR-034, SC-008; comparação antes e depois: superada pela não regressão geral (SC-001) |  |
| 005 SC-006 — suíte aprovada sem rede e sem alterar arquivos do projeto | em vigor | constituição: Fluxo de Desenvolvimento e Qualidade 1 (testes sem rede) |  |

## 006-bases-complementares

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 006 US1 — cópia de segurança dos dados processados | em vigor (parte) | 002-tratamento-dados US6 (dados tratados); arquivos da Coleta → 001-coleta-dados | 05/10/2026: pedido do usuário |
| 006 US2 — dicionários de dados | em vigor | 001-coleta-dados US5 (cenários 6 e 7); FR-031 a FR-033 | 05/10/2026: dicionários obtidos sempre, a cada coleta |
| 006 US3 — disponibilidade operacional e sincronizada | em vigor (parte) | 001-coleta-dados US1 (cenário 7) e FR-044 (obtenção num formato que cobre o mês e extração); série horária e qualidade D1 a D4 → 002-tratamento-dados; conferência → 003-conferencia; classes, resumos, seção e figura → 004-analises e 005 |  |
| 006 US3 — disponibilidade operacional e sincronizada | em vigor (parte) | 002-tratamento-dados US4 (série horária, D1 a D4 e ausências; cenário 5); coleta → 001-coleta-dados; conferência com a declarada → 003-conferencia; horas paradas, resumos e seção → 004-analises e 005-geracao-relatorio |  |
| 006 US3 — disponibilidade operacional e sincronizada | em vigor (parte) | cenário 2 (conferência hora a hora com a disponibilidade declarada, divergências listadas) → 003-conferencia US2 e FR-011; cenários 1 e 5 → 001-coleta-dados e 002-tratamento-dados; cenários 3, 4 e 6 → 004-analises e 005-geracao-relatorio |  |
| 006 US3 — disponibilidade operacional e sincronizada | em vigor (parte) | classificação das horas paradas, resumos, reserva desligada e constatação: 004-analises US2, FR-030 a FR-033, FR-044; obtenção e extração: 001-coleta-dados; qualidade D1 a D4: 002-tratamento-dados; conferência com a declarada: 003-conferencia; seção e figura: 005-geracao-relatorio |  |
| 006 US3 — disponibilidade operacional e sincronizada | em vigor (parte) | cenário 6 (seção, figura 06, fonte): 005-geracao-relatorio FR-007, FR-034, FR-020; demais cenários: 001-coleta-dados, 002-tratamento-dados, 003-conferencia e 004-analises |  |
| 006 US4 — afluência, vertimento e nível | em vigor (parte) | 001-coleta-dados FR-044 (obtenção e extração); hora de início, ausências e qualidade H1 a H4 → 002-tratamento-dados; alinhamento e código 3 → 003-conferencia; faixas e perfis → 004-analises |  |
| 006 US4 — afluência, vertimento e nível | em vigor (parte) | 002-tratamento-dados US4 (hora de início com o 23:59, H1 a H4 e horas ausentes; cenários 1, 2 e 5, em parte); confirmação do alinhamento → 003-conferencia; faixas, perfil e resumos → 004-analises; seção e figuras → 005-geracao-relatorio |  |
| 006 US4 — afluência, vertimento e nível | em vigor (parte) | cenário 2, confirmação do alinhamento (vazões coincidentes em pelo menos 99 % das horas comuns; abaixo disso, falha) → 003-conferencia US2, FR-012 e FR-013; conversão de fim para início de hora → 002-tratamento-dados; não publicar os cruzamentos → 004-analises; demais cenários → 001-coleta-dados, 002-tratamento-dados, 004-analises e 005-geracao-relatorio |  |
| 006 US4 — afluência, vertimento e nível | em vigor (parte) | faixas, perfil, resumos e constatação: 004-analises US2, FR-034 a FR-038, FR-044; obtenção: 001-coleta-dados; convenção de hora e qualidade H1 a H4: 002-tratamento-dados; alinhamento e meta: 003-conferencia; seção e figuras: 005-geracao-relatorio |  |
| 006 US4 — afluência, vertimento e nível | em vigor (parte) | cenário 7 (seção, figuras 07 e 08, fonte com a ressalva de dados não consistidos): 005-geracao-relatorio FR-007, FR-034, FR-020, FR-021; demais cenários: etapas 001 a 004 |  |
| 006 US5 — conferência da geração | em vigor (parte) | 001-coleta-dados FR-044 (obtenção e extração); comparação → 003-conferencia; seção → 004-analises e 005 |  |
| 006 US5 — conferência da geração | em vigor (parte) | 002-tratamento-dados US4 (série horária, G1 e ausências); coleta → 001-coleta-dados; conferência → 003-conferencia |  |
| 006 US5 — conferência da geração | em vigor (parte) | cenário 2 → 003-conferencia US2 e FR-010; cenário 1 (coleta) → 001-coleta-dados; cenário 3 (seção e constatação só com divergência) → 004-analises e 005-geracao-relatorio | 02/10/2026: série de Geração por usina não estendida a 2015; conferência no período da base de EVT |
| 006 US5 — conferência da geração | em vigor (parte) | totais anuais e constatação só com divergência: 004-analises FR-039, FR-044; conferência: 003-conferencia; obtenção: 001-coleta-dados; seção: 005-geracao-relatorio |  |
| 006 US5 — conferência da geração | em vigor (parte) | cenário 3 (seção, texto e fonte): 005-geracao-relatorio FR-007, FR-020; conferência: 003-conferencia; constatação: 004-analises |  |
| 006 US6 — identificação cadastral | em vigor (parte) | 001-coleta-dados US1 (cenário 9), US5 (republicação) e FR-045; divergências com o perfil → 003-conferencia; ficha na capa → 005 |  |
| 006 US6 — identificação cadastral | em vigor (parte) | cenário 2 (divergências com o perfil) → 003-conferencia US4 e FR-017; cenários 1 e 3 (ficha, data da consulta, homônimos, versões) → 001-coleta-dados; cenário 4 (ficha na capa, constatação) → 004-analises e 005-geracao-relatorio |  |
| 006 US6 — identificação cadastral | em vigor (parte) | ficha e divergências nos resultados e constatação só com divergência: 004-analises FR-040, FR-044; extração: 001-coleta-dados; divergências: 003-conferencia; ficha na capa: 005-geracao-relatorio |  |
| 006 US6 — identificação cadastral | em vigor (parte) | cenário 4, já revisto: ficha na capa, sem a data da consulta: 005-geracao-relatorio FR-012; extração: 001-coleta-dados; divergências: 003-conferencia | 07/10/2026: cadastro na capa, sem a data da consulta |
| 006 FR-001 — EVT local sem novo download; recorte no período da EVT | em vigor (parte) | 001-coleta-dados FR-017 (arquivos do período) e FR-021 (`--sem-portal`); recorte das linhas → 002-tratamento-dados | 02/10/2026: base de EVT mantida |
| 006 FR-001 — EVT local sem novo download; recorte no período da EVT | em vigor (parte) | 002-tratamento-dados FR-004 (recorte); EVT sem novo download → 001-coleta-dados | 02/10/2026: base de EVT mantida; extensão da geração a 2015 recusada |
| 006 FR-002 — arquivos do período; brutos preservados; manifesto; versões; reaproveitamento | em vigor | 001-coleta-dados FR-017, FR-024, FR-027 a FR-030 |  |
| 006 FR-003 — cada mês num formato que o contém; ausência só de arquivo que cobre o mês | em vigor (parte) | 001-coleta-dados FR-018; conclusão de ausência → 002-tratamento-dados |  |
| 006 FR-004 — identificador e conferência por conjunto; parciais contadas | em vigor | 001-coleta-dados FR-034 a FR-036 (valores do perfil) |  |
| 006 FR-005 — auditoria por arquivo; meses e horas ausentes | em vigor (parte) | 001-coleta-dados FR-046 (linhas lidas, da usina, parciais, valores inválidos e situação); horas da usina, duplicatas e ausências → 002-tratamento-dados |  |
| 006 FR-005 — auditoria por arquivo; meses e horas ausentes | em vigor (parte) | 002-tratamento-dados FR-018 (ausências) e FR-020 (horas da usina na auditoria completa); demais contagens → 001-coleta-dados |  |
| 006 FR-006 — um valor por hora; duplicatas conflitantes | em vigor | 002-tratamento-dados FR-016 |  |
| 006 FR-007 — etapa no pipeline e isolada, desligável, com nível de log e testável sem rede | em vigor (parte) | nível de log → 001-coleta-dados FR-004; execução por conjunto e opção de desligar superadas (FR-002); testes sem rede → constituição |  |
| 006 FR-008 — .bak antes de regravar | em vigor (parte) | 002-tratamento-dados FR-028 (dados tratados); arquivos da Coleta → 001-coleta-dados | 05/10/2026: pedido do usuário; 07/10/2026: só a versão imediatamente anterior |
| 006 FR-009 — conteúdo idêntico não regravado | em vigor (parte) | 002-tratamento-dados FR-029; arquivos da Coleta → 001-coleta-dados |  |
| 006 FR-010 — conferência física da gravação e restauração | em vigor (parte) | 002-tratamento-dados FR-030; arquivos da Coleta → 001-coleta-dados |  |
| 006 FR-011 — nenhuma etapa lê .bak | em vigor (parte) | 002-tratamento-dados FR-002 e FR-032 (pasta do Tratamento); demais pastas → spec da etapa que as grava |  |
| 006 FR-012 — gravação segura de todos os dados processados; fora da regra: relatórios, manifestos,… | em vigor (parte) | 001-coleta-dados FR-030 (brutos, manifestos e dicionários sem `.bak`) e FR-047 (arquivos da coleta com gravação segura); regra dos dados tratados → 002-tratamento-dados; relatórios → 005 | 05/10/2026: `.bak` só nos dados; arquivos de controle dispensados |
| 006 FR-012 — gravação segura de todos os dados processados; fora da regra: relatórios, manifestos,… | em vigor (parte) | 002-tratamento-dados FR-032 (dados tratados; `etapa.json` fora); arquivos da Coleta → 001-coleta-dados | 05/10/2026: decisão do usuário (cópia só nos dados) |
| 006 FR-012 — gravação segura de todos os dados processados; fora da regra: relatórios, manifestos,… | em vigor (parte) | relatório regravado sem `.bak`: 005-geracao-relatorio FR-003; `.bak` dos dados: 002-tratamento-dados | 05/10/2026: sem `.bak` em `reports/` |
| 006 FR-013 — dicionários de todos os conjuntos a cada coleta | em vigor | 001-coleta-dados FR-031 | 05/10/2026: dicionários sempre |
| 006 FR-014 — comparação pelo conteúdo, versão anterior e registro | em vigor | 001-coleta-dados FR-032 |  |
| 006 FR-015 — dicionários sem novo download de dados e sem interromper | em vigor | 001-coleta-dados FR-033 |  |
| 006 FR-016 — extrair potência instalada e disponibilidades operacional e sincronizada | em vigor (parte) | 001-coleta-dados FR-044 (extração); série horária → 002-tratamento-dados |  |
| 006 FR-016 — extrair potência instalada e disponibilidades operacional e sincronizada | em vigor (parte) | 002-tratamento-dados Entradas e saídas (`disponibilidade_horaria.csv`) e FR-015 a FR-019; extração → 001-coleta-dados |  |
| 006 FR-017 — disponibilidade operacional × declarada, hora a hora, divergências em períodos contínuos | em vigor | 003-conferencia FR-011 (tolerância de 0,01 MW, como no código) |  |
| 006 FR-018 — valores inconsistentes da disponibilidade | em vigor | 002-tratamento-dados FR-019 (D1 a D4, hora inteira fora do uso) e FR-033 (contagem) |  |
| 006 FR-018 — valores inconsistentes da disponibilidade | em vigor (parte) | exclusão das análises: 004-analises FR-030; contagem e sinalização: 002-tratamento-dados |  |
| 006 FR-019 — classificação das horas paradas | em vigor | 004-analises FR-031 |  |
| 006 FR-020 — resumos por mês e por ano e reserva desligada | em vigor | 004-analises FR-032 |  |
| 006 FR-021 — extrair vazões, níveis e volume útil | em vigor (parte) | 001-coleta-dados FR-044 (extração); série horária → 002-tratamento-dados |  |
| 006 FR-021 — extrair vazões, níveis e volume útil | em vigor (parte) | 002-tratamento-dados Entradas e saídas (`hidrologia_horaria.csv`) e FR-015 a FR-019; extração → 001-coleta-dados |  |
| 006 FR-022 — hora de fim para hora de início; alinhamento de 99 % | em vigor (parte) | 002-tratamento-dados FR-015 (convenção de hora, inclusive o 23:59); confirmação do alinhamento e código 3 → 003-conferencia |  |
| 006 FR-022 — hora de fim para hora de início; alinhamento de 99 % | em vigor (parte) | confirmação do alinhamento, meta de 99 % e código 3 → 003-conferencia FR-012 e FR-013; conversão de fim para início de hora → 002-tratamento-dados; não publicar os cruzamentos → 004-analises |  |
| 006 FR-022 — hora de fim para hora de início; alinhamento de 99 % | em vigor (parte) | sem a meta, sem cruzamentos: 004-analises FR-034; conversão da hora: 002-tratamento-dados; alinhamento e meta: 003-conferencia |  |
| 006 FR-023 — faixas de afluência | em vigor | 004-analises FR-036; limites do perfil: FR-007, FR-008 |  |
| 006 FR-024 — perfil por hora do dia | em vigor | 004-analises FR-037 |  |
| 006 FR-025 — resumo mensal da hidrologia | em vigor | 004-analises FR-038 |  |
| 006 FR-026 — valores impossíveis excluídos; vazio não é zero | em vigor | 002-tratamento-dados FR-019 (H1 a H4; o valor sai só do próprio campo) |  |
| 006 FR-026 — valores impossíveis excluídos; vazio não é zero | em vigor (parte) | exclusão campo a campo nas análises: 004-analises FR-035; contagem e sinalização: 002-tratamento-dados |  |
| 006 FR-027 — extrair a geração horária oficial | em vigor (parte) | 001-coleta-dados FR-044 (extração); série horária → 002-tratamento-dados |  |
| 006 FR-027 — extrair a geração horária oficial | em vigor (parte) | 002-tratamento-dados Entradas e saídas (`geracao_horaria.csv`) e FR-015 a FR-019 (G1); extração → 001-coleta-dados |  |
| 006 FR-028 — geração da base de EVT × Geração por usina | em vigor | 003-conferencia FR-010 | 02/10/2026: conferência no período da base de EVT |
| 006 FR-029 — ficha cadastral com a data da consulta e os homônimos | em vigor | 001-coleta-dados FR-045 |  |
| 006 FR-030 — potência autorizada e estado da ficha × parâmetros | em vigor | 003-conferencia FR-017, com os campos do perfil; segue o código, que confere também o id ONS e o CEG em linha única |  |
| 006 FR-031 — seções e constatações das bases novas | em vigor (parte) | constatações (sempre ou só com divergência) e ressalvas: 004-analises FR-044; seções: 005-geracao-relatorio |  |
| 006 FR-031 — seções e constatações das bases novas | em vigor (parte) | seções e ressalvas: 005-geracao-relatorio FR-007, FR-020, FR-021 (sem a seção do cadastro, cuja ficha foi para a capa, FR-012); regras das constatações: 004-analises | 07/10/2026: cadastro na capa |
| 006 FR-032 — figuras novas | em vigor (parte) | dados: 004-analises FR-041; figuras: 005-geracao-relatorio |  |
| 006 FR-032 — figuras novas | em vigor | 005-geracao-relatorio FR-034 (figuras 06 a 08), FR-035 |  |
| 006 FR-033 — números de seções, constatações e abas mantidos | superado | a não regressão passa a ser a do relatório de referência: 004-analises SC-001 e 005-geracao-relatorio |  |
| 006 FR-033 — números de seções, constatações e abas mantidos | superado | não regressão pontual da inclusão das bases; a geral está em 005-geracao-relatorio SC-001 |  |
| 006 FR-034 — relação de fontes com as bases novas | em vigor | 005-geracao-relatorio FR-020 (notas) e FR-022 (tabela de parâmetros) |  |
| 006 SC-001 — meses obtidos ou listados como ausentes | em vigor (parte) | 001-coleta-dados SC-001 e FR-018 (obtenção); lista de ausentes → 002-tratamento-dados |  |
| 006 SC-001 — meses obtidos ou listados como ausentes | em vigor (parte) | 002-tratamento-dados SC-004 e FR-018 (mês sem arquivo × mês sem a usina); obtenção num formato que cobre o mês → 001-coleta-dados |  |
| 006 SC-002 — nenhum registro de outra usina | em vigor | 001-coleta-dados SC-002 |  |
| 006 SC-003 — vazões coincidentes em pelo menos 99 % das horas comuns | em vigor | 003-conferencia FR-013 (meta) e SC-001 (70.731 de 70.731 horas) |  |
| 006 SC-004 — 100 % das horas comuns classificadas, divergentes listadas | em vigor | 003-conferencia SC-002 |  |
| 006 SC-005 — 100 % das horas classificadas (faixas e sincronização) | em vigor | 004-analises SC-005 |  |
| 006 SC-006 — teste das quatro gravações | em vigor (parte) | 002-tratamento-dados SC-006; arquivos da Coleta → 001-coleta-dados |  |
| 006 SC-007 — dicionários dos 10 conjuntos; versão anterior preservada | em vigor | 001-coleta-dados SC-006 |  |
| 006 SC-008 — números existentes iguais; números das seções novas iguais aos da planilha | em vigor (parte) | números citados iguais aos da planilha: 004-analises SC-009; primeira parte superada pela não regressão (004-analises SC-001); seções: 005-geracao-relatorio |  |
| 006 SC-008 — números existentes iguais; números das seções novas iguais aos da planilha | em vigor (parte) | igualdade com a planilha: 005-geracao-relatorio SC-007; comparação antes e depois: superada (SC-001) |  |
| 006 SC-009 — menos de 10 min; segunda execução sem download; EVT nunca baixada de novo | em vigor (parte) | 001-coleta-dados SC-012 e SC-004; "EVT nunca baixada de novo" passa a: sem novidade nada é baixado, e `--sem-portal` mantém a base local (FR-021) | 02/10/2026: base de EVT mantida |
| 006 SC-009 — menos de 10 min; segunda execução sem download; EVT nunca baixada de novo | em vigor (parte) | 002-tratamento-dados SC-010 (tempo do Tratamento); downloads → 001-coleta-dados |  |
| 006 SC-010 — P1 entregue até 13/10/2026 | superado | prazo cumprido: relatório entregue em 05/10/2026 e aprovado em 07/10/2026 |  |

## 007-fontes-por-figura-tabela

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 007 US1 — Fonte e conferência em cada figura e tabela | em vigor (parte) | resultados que as legendas citam → 003-conferencia FR-005; legenda → 005-geracao-relatorio | 06/10/2026: só as conferências refeitas a cada execução entram nas legendas |
| 007 US1 — Fonte e conferência em cada figura e tabela | em vigor | 005-geracao-relatorio US3; FR-023 a FR-027 | 06/10/2026: só as conferências refeitas pelo fluxo |
| 007 US2 — rodapé e cabeçalho fiéis às fontes | superado | rodapé só com a numeração e cabeçalho do Markdown com a data de geração: 005-geracao-relatorio FR-015, FR-017 | 06/10/2026: rodapé só com a numeração |
| 007 US3 — origem de cada aba da planilha | em vigor | 005-geracao-relatorio US3, FR-028 |  |
| 007 FR-001 — legenda abaixo de cada figura e tabela | em vigor | 005-geracao-relatorio FR-023 |  |
| 007 FR-002 — conjunto, identificador e data de obtenção | em vigor | 005-geracao-relatorio FR-024, FR-025 (identificadores do perfil) |  |
| 007 FR-003 — legenda cita cada conferência com o resultado | em vigor (parte) | números citados (coincidências, proporção, divergências, horas só numa fonte) → 003-conferencia FR-005; texto e aba onde estão listadas → 005-geracao-relatorio |  |
| 007 FR-003 — legenda cita cada conferência com o resultado | em vigor | 005-geracao-relatorio FR-026 |  |
| 007 FR-004 — dado sem outra fonte | em vigor | 005-geracao-relatorio FR-024, FR-027 |  |
| 007 FR-005 — conferência não feita dita na legenda | em vigor (parte) | registro "não aplicável" com o motivo → 003-conferencia FR-004; texto da legenda → 005-geracao-relatorio |  |
| 007 FR-005 — conferência não feita dita na legenda | em vigor | 005-geracao-relatorio FR-026 |  |
| 007 FR-006 — legendas geradas dos resultados das conferências, nada fixo | em vigor (parte) | resultados refeitos e registrados a cada execução → 003-conferencia FR-005; geração do texto → 005-geracao-relatorio |  |
| 007 FR-006 — legendas geradas dos resultados das conferências, nada fixo | em vigor | 005-geracao-relatorio FR-026, FR-018 |  |
| 007 FR-007 — valores calculados no relatório | em vigor | 005-geracao-relatorio FR-024 |  |
| 007 FR-008 — mapa único para PDF, Markdown e planilha | em vigor | 005-geracao-relatorio FR-027 |  |
| 007 FR-009 — rodapé com N conjuntos e data | superado | rodapé só com "Página X de Y"; data de geração na capa: 005-geracao-relatorio FR-015, FR-011 | 06/10/2026: rodapé só com a numeração |
| 007 FR-010 — linha de fontes no cabeçalho do Markdown | superado | cabeçalho sem linha de fontes, com "Gerado em": 005-geracao-relatorio FR-017 | 06/10/2026 |
| 007 FR-011 — aba de fontes | em vigor | 005-geracao-relatorio FR-028 |  |
| 007 FR-012 — números, constatações, seções e abas inalterados | superado | não regressão pontual da inclusão das legendas; a geral está em 005-geracao-relatorio SC-001 |  |
| 007 FR-013 — figuras não redesenhadas; legenda fora da imagem | em vigor (parte) | legenda no texto, fora da imagem: 005-geracao-relatorio FR-023; "não redesenhar": superado pelas figuras padronizadas (FR-036) | 07/10/2026: figuras padronizadas |
| 007 SC-001 — 100 % com legenda; todas as abas na FONTES | em vigor | 005-geracao-relatorio SC-002 |  |
| 007 SC-002 — conjuntos citados corretos | em vigor | 005-geracao-relatorio SC-002 |  |
| 007 SC-003 — resultados das legendas iguais aos das abas | em vigor | 005-geracao-relatorio SC-007 |  |
| 007 SC-004 — nada existente muda | superado | não regressão pontual; a geral está em 005-geracao-relatorio SC-001 |  |
| 007 SC-005 — rodapé com a quantidade certa de conjuntos | superado | rodapé só com a numeração: 005-geracao-relatorio SC-004 | 06/10/2026 |
| 007 SC-006 — entregue até 13/10/2026 | superado | prazo cumprido (06/10/2026) |  |

## 008-relatorio-enxuto

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 008 US1 — capa com dados básicos, percentuais e sumário | em vigor | 005-geracao-relatorio US2; FR-011 a FR-014, com a ficha do cadastro (FR-012) | 06/10/2026: capa com sumário; 07/10/2026: cadastro na capa |
| 008 US2 — cada constatação uma única vez, no início da seção | em vigor (parte) | existência, ordem e texto das constatações (cenários 2 e 4): 004-analises FR-044; lugar no relatório: 005-geracao-relatorio |  |
| 008 US2 — cada constatação uma única vez, no início da seção | em vigor | 005-geracao-relatorio US2; FR-009, FR-010 | 06/10/2026 |
| 008 US3 — sem rodapé de fontes repetido | em vigor | 005-geracao-relatorio FR-015 | 06/10/2026 |
| 008 FR-001 — blocos e indicadores da capa; ficha do cadastro | em vigor | 005-geracao-relatorio FR-011, FR-012, FR-013 | 07/10/2026: cadastro na capa |
| 008 FR-002 — data e hora de geração na capa | em vigor | 005-geracao-relatorio FR-011; data fixável por `--data-geracao`: FR-004 | 06/10/2026 |
| 008 FR-003 — sumário com a página de cada seção | em vigor | 005-geracao-relatorio FR-011 |  |
| 008 FR-004 — capa e sumário sem constatações | em vigor | 005-geracao-relatorio FR-009 |  |
| 008 FR-005 — constatação uma vez, no início da seção | em vigor | 005-geracao-relatorio FR-009, FR-010 |  |
| 008 FR-006 — título da constatação destacado | em vigor | 005-geracao-relatorio FR-009 |  |
| 008 FR-007 — sumário no lugar da lista de constatações | em vigor | 005-geracao-relatorio FR-009, FR-011 |  |
| 008 FR-008 — regras de existência das constatações mantidas | em vigor | 004-analises FR-044 |  |
| 008 FR-008 — regras de existência das constatações mantidas | em vigor (parte) | o relatório apresenta só as constatações geradas: 005-geracao-relatorio FR-009; condições de cada constatação: 004-analises |  |
| 008 FR-009 — rodapé só com a numeração | em vigor | 005-geracao-relatorio FR-015 | 06/10/2026 |
| 008 FR-010 — cabeçalho do Markdown sem fontes, com a data | em vigor | 005-geracao-relatorio FR-017 | 06/10/2026 |
| 008 FR-011 — legendas de fonte mantidas | em vigor | 005-geracao-relatorio FR-023 |  |
| 008 FR-012 — nada além da organização muda | superado | não regressão pontual da reorganização do relatório; a geral está em 005-geracao-relatorio SC-001 |  |
| 008 FR-013 — notas das bases novas sem a parte de fonte | em vigor | 005-geracao-relatorio FR-021 | 06/10/2026: notas enxutas; 07/10/2026: ressalva do cadastro só nas notas metodológicas |
| 008 FR-014 — Markdown com a estrutura do PDF | em vigor | 005-geracao-relatorio FR-017 | 06/10/2026 (decisão 1A) |
| 008 FR-015 — ficha do cadastro na capa; sem seção própria | em vigor | 005-geracao-relatorio FR-012, FR-010 (constatação do cadastro na cobertura), FR-021 | 07/10/2026 |
| 008 FR-016 — figuras 01, 02, 05 e 06 padronizadas | em vigor | 005-geracao-relatorio FR-036 | 07/10/2026: 11 × 4,3 polegadas, largura útil |
| 008 SC-001 — cada constatação 1 vez | em vigor | 005-geracao-relatorio SC-003 |  |
| 008 SC-002 — capa numa página | em vigor | 005-geracao-relatorio SC-004, FR-014 |  |
| 008 SC-003 — sumário completo, com as páginas certas | em vigor | 005-geracao-relatorio SC-004 |  |
| 008 SC-004 — rodapé só com a numeração; legendas mantidas | em vigor | 005-geracao-relatorio SC-004, SC-002 |  |
| 008 SC-005 — nada mais muda | superado | não regressão pontual; a geral está em 005-geracao-relatorio SC-001 |  |
| 008 SC-006 — relatório mais curto (menos de 31 páginas) | superado | atingido: 30 páginas, número fixado na referência (005-geracao-relatorio SC-001) |  |
| 008 SC-007 — entregue até 13/10/2026 | superado | prazo cumprido (06 e 07/10/2026) |  |
| 008 SC-008 — Markdown e PDF com as mesmas seções e sumário | em vigor | 005-geracao-relatorio SC-005 |  |

## 009-reorganizacao-pipeline

| Origem | Situação | Destino | Decisão do usuário |
|---|---|---|---|
| 009 US1 — fluxo de cinco etapas | em vigor (parte) | 001-coleta-dados US4 (comando único, etapa isolada, pré-requisito) e US1 cenário 2 (nada baixado sem novidade); relatório igual ao aprovado → 005-geracao-relatorio; conferências numa etapa → 003-conferencia |  |
| 009 US1 — fluxo de cinco etapas | em vigor (parte) | cenário 4 (todas as conferências entre fontes na etapa de Conferência, com os resultados registrados) → 003-conferencia US1; demais cenários → 001-coleta-dados (regras comuns) e 005-geracao-relatorio |  |
| 009 US1 — fluxo de cinco etapas | em vigor (parte) | cenários 2 e 3, nas Análises: 004-analises US5, FR-002, FR-003, SC-007; fluxo e regras comuns: 001-coleta-dados |  |
| 009 US1 — fluxo de cinco etapas | em vigor (parte) | relatório gerado só dos resultados anteriores, executável sozinho: 005-geracao-relatorio US1, FR-001, FR-002 | 07/10/2026: pedido do usuário |
| 009 US1 — fluxo de cinco etapas | em vigor (parte) | constituição: introdução (as cinco etapas) e princípio I (cada etapa só lê as anteriores); os comandos de cada etapa ficam nas specs 001 a 005 | 07/10/2026: pedido do usuário |
| 009 US2 — constituição e specs limpas | em vigor (parte) | constituição: princípio I e Governança 2 e 3; a consolidação em si é cumprida pela reorganização (cinco specs novas e este mapeamento) | 07/10/2026: pedido do usuário |
| 009 US3 — mesma lógica para outras usinas | em vigor (parte) | 001-coleta-dados US3 (recusa do perfil) e US1 (cenários 4 e 11: só a usina; brutos compartilhados); estrutura do relatório e omissão de seções → 004-analises e 005 | 07/10/2026: outras usinas pelo perfil |
| 009 US3 — mesma lógica para outras usinas | em vigor (parte) | conferência sem base registrada como não aplicável → 003-conferencia FR-004, US1 (cenário 3) e SC-004; demais → 001-coleta-dados, 004-analises e 005-geracao-relatorio |  |
| 009 US3 — mesma lógica para outras usinas | em vigor (parte) | cenário 4 (análises ajustadas ao perfil; bases ausentes omitidas): 004-analises US6; demais cenários: 001-coleta-dados e 005-geracao-relatorio |  |
| 009 US3 — mesma lógica para outras usinas | em vigor (parte) | relatório de outra usina: 005-geracao-relatorio US7, FR-019, SC-010 | 07/10/2026: pedido do usuário |
| 009 US3 — mesma lógica para outras usinas | em vigor (parte) | constituição: princípio III; o perfil e a recusa ficam na Coleta, e o ajuste das análises ao perfil, nas Análises | 07/10/2026: pedido do usuário |
| 009 US4 — no máximo duas cópias de segurança | em vigor (parte) | 001-coleta-dados US6 (cenários 2 e 3 da origem); exclusão das cópias de 06/10/2026 ou antes e dos `.bak` soltos: ações únicas da reorganização | 07/10/2026: no máximo duas cópias |
| 009 US4 — no máximo duas cópias de segurança | em vigor | constituição: Requisito Técnico 5 | 07/10/2026: "no MÁXIMO 2 versões backups" |
| 009 US5 — pasta só com o que é usado | cumprido | inventário aprovado e aplicado em 07/10/2026 (T014 a T017); a regra das pastas e dos documentos fora do git fica no Requisito Técnico 6 | 07/10/2026: inventário aprovado |
| 009 US6 — conclusão sucinta | em vigor (parte) | regras e itens: 004-analises US4; seção no relatório: 005-geracao-relatorio | 07/10/2026: pedido do usuário; texto aprovado |
| 009 US6 — conclusão sucinta | em vigor (parte) | apresentação: 005-geracao-relatorio US4, FR-029 a FR-033; regras: 004-analises | 07/10/2026: texto aprovado |
| 009 US6 — conclusão sucinta | em vigor (parte) | constituição: princípio II; as regras ficam nas Análises e a apresentação, na Geração do relatório | 07/10/2026: texto e limiares aprovados |
| 009 FR-001 — fluxo único de cinco etapas | em vigor | 001-coleta-dados FR-001 |  |
| 009 FR-001 — fluxo único de cinco etapas | em vigor | constituição: introdução (tabela das cinco etapas) |  |
| 009 FR-002 — cada etapa usa só os resultados anteriores; só a coleta acessa o portal | em vigor | 001-coleta-dados FR-001 (regra comum); as entradas de cada etapa ficam na spec dela |  |
| 009 FR-002 — cada etapa usa só os resultados anteriores; só a coleta acessa o portal | em vigor (parte) | entradas da Conferência e proibição de acessar o portal → 003-conferencia FR-001 e "Entradas e saídas"; regra comum → 001-coleta-dados |  |
| 009 FR-002 — cada etapa usa só os resultados anteriores; só a coleta acessa o portal | em vigor (parte) | nas Análises: 004-analises FR-003; regra comum: 001-coleta-dados |  |
| 009 FR-002 — cada etapa usa só os resultados anteriores; só a coleta acessa o portal | em vigor | constituição: princípio I |  |
| 009 FR-003 — fluxo completo ou etapa isolada; parada sem a anterior | em vigor | 001-coleta-dados FR-002, FR-003, FR-012, FR-013 (situação do `etapa.json` por código de saída; o código 3 fica `concluida`) |  |
| 009 FR-003 — fluxo completo ou etapa isolada; parada sem a anterior | em vigor (parte) | nas Análises: 004-analises FR-002, SC-007; regra comum: 001-coleta-dados |  |
| 009 FR-003 — fluxo completo ou etapa isolada; parada sem a anterior | em vigor (parte) | constituição: princípio I (parar sem gravar e indicar a etapa anterior); os comandos e o código 5 ficam nas regras comuns da Coleta |  |
| 009 FR-004 — o que a Coleta de dados faz | em vigor | 001-coleta-dados FR-016 a FR-046 |  |
| 009 FR-005 — Tratamento de dados | em vigor | 002-tratamento-dados Objetivo e FR-001 a FR-034 |  |
| 009 FR-006 — Conferência reúne as seis conferências e registra os resultados | em vigor | 003-conferencia FR-001 a FR-003 e FR-010 a FR-017 |  |
| 009 FR-007 — Análises | em vigor | 004-analises Objetivo, FR-003, FR-005, FR-041 |  |
| 009 FR-008 — geração do relatório com a estrutura aprovada | em vigor | 005-geracao-relatorio FR-001, FR-007, FR-009, FR-011 a FR-017, FR-023 a FR-028, FR-036 |  |
| 009 FR-009 — pontos de entrada e opções antigas substituídos; opções e códigos documentados | em vigor (parte) | 001-coleta-dados FR-002 e FR-005; documentação no README → fechamento da reorganização |  |
| 009 FR-009 — pontos de entrada e opções antigas substituídos; opções e códigos documentados | em vigor (parte) | 002-tratamento-dados Entradas e saídas (comando sem opções; códigos 0, 1 e 5); regras comuns → 001-coleta-dados; README fora das specs |  |
| 009 FR-009 — pontos de entrada e opções antigas substituídos; opções e códigos documentados | em vigor (parte) | comando, opções e códigos da Conferência → 003-conferencia "Entradas e saídas" e FR-009; tabela comum → 001-coleta-dados; demais etapas → specs delas |  |
| 009 FR-009 — pontos de entrada e opções antigas substituídos; opções e códigos documentados | em vigor (parte) | `relatorio`, `--data-geracao`, códigos 0, 1 e 5 e `comparar`: 005-geracao-relatorio Entradas e saídas, FR-004, FR-006, FR-040; regras comuns: 001-coleta-dados |  |
| 009 FR-009 — pontos de entrada e opções antigas substituídos; opções e códigos documentados | em vigor (parte) | README no estado final (T073); os comandos e as opções ficam nas regras comuns da Coleta e em cada spec |  |
| 009 FR-010 — não regressão do relatório | em vigor (parte) | seis resultados iguais aos atuais → 003-conferencia SC-001; relatório → 005-geracao-relatorio |  |
| 009 FR-010 — não regressão do relatório | em vigor (parte) | resultados das Análises: 004-analises SC-001; relatório: 005-geracao-relatorio |  |
| 009 FR-010 — não regressão do relatório | em vigor (parte) | 005-geracao-relatorio SC-001; ver em Assumptions as duas citações de local de arquivo que mudam com a reorganização | 07/10/2026: conclusão aprovada |
| 009 FR-010 — não regressão do relatório | em vigor (parte) | critério de não regressão da Geração do relatório; a prova da reorganização é feita no fechamento (T059 e T075) | 07/10/2026: conclusão aprovada |
| 009 FR-011 — reorganização sem novo download nem alteração dos brutos; tratados iguais aos atuais | em vigor (parte) | 001-coleta-dados FR-021 e SC-014 (`--sem-portal` não toca `data/raw/`); tratados iguais → 002-tratamento-dados |  |
| 009 FR-011 — reorganização sem novo download nem alteração dos brutos; tratados iguais aos atuais | em vigor (parte) | 002-tratamento-dados SC-001 e FR-034 (tratados iguais aos atuais); FR-002 (o Tratamento não lê nem altera brutos); brutos intactos → 001-coleta-dados | 07/10/2026: bases completas, nenhuma base nova |
| 009 FR-011 — reorganização sem novo download nem alteração dos brutos; tratados iguais aos atuais | em vigor (parte) | critério de não regressão do Tratamento; a prova é feita na T048 |  |
| 009 FR-012 — comportamento coberto pelos testes | em vigor | constituição: Fluxo de Desenvolvimento e Qualidade 1 |  |
| 009 FR-013 — constituição única e simples | em vigor | constituição (o próprio documento) | 07/10/2026: "sem emendas" |
| 009 FR-014 — uma usina por perfil, homônimos excluídos | em vigor | constituição: princípio III |  |
| 009 FR-015 — governança das mudanças | em vigor | constituição: Governança 2 e 3 |  |
| 009 FR-016 — cinco specs, uma por etapa | em vigor (parte) | constituição: princípio I (uma spec por etapa, com o conteúdo exigido); a consolidação é cumprida pelas cinco specs novas |  |
| 009 FR-017 — requisito em exatamente uma spec; mapeamento | cumprido | este mapeamento, apresentado ao usuário antes da remoção das specs antigas (T024 e T025) |  |
| 009 FR-018 — decisões do usuário preservadas | em vigor (parte) | conferências manuais com CCEE e ANEEL fora do relatório → 003-conferencia "Decisões do usuário" e "Conferências manuais (fora do fluxo)"; demais decisões → outras specs e perfil | 06/10/2026 e 07/10/2026 |
| 009 FR-018 — decisões do usuário preservadas | em vigor | seção "Decisões do usuário" de cada spec nova; os valores da usina vão para o perfil |  |
| 009 FR-019 — specs antigas e a 009 saem | a cumprir | no fechamento, com a aprovação do usuário (T076) |  |
| 009 FR-020 — conteúdo do perfil da usina | em vigor | 001-coleta-dados FR-006, FR-007 | 07/10/2026: outras usinas pelo perfil; 30/09/2026: fonte RF 0009/2017-AGEPAN-SFG, sem o modelo de RF de 2026; 02/10/2026: garantia física de 36,4 MWmed |
| 009 FR-020 — conteúdo do perfil da usina | em vigor (parte) | uso dos valores do perfil: 004-analises FR-007; campos e validação do perfil: 001-coleta-dados |  |
| 009 FR-020 — conteúdo do perfil da usina | em vigor (parte) | constituição: princípio III; os campos do perfil ficam nas regras comuns da Coleta |  |
| 009 FR-021 — perfil como entrada do fluxo | em vigor | 001-coleta-dados FR-006, FR-008; resultado da São Domingos → SC-014 e specs seguintes |  |
| 009 FR-022 — perfil incompleto recusado antes da coleta, com a lista | em vigor | 001-coleta-dados FR-008, FR-009 |  |
| 009 FR-022 — perfil incompleto recusado antes da coleta, com a lista | em vigor (parte) | constituição: princípio III; a recusa com código 4 fica nas regras comuns da Coleta |  |
| 009 FR-023 — textos do relatório sem nome, identificador ou valor de usina fora do perfil ou dos dados | em vigor (parte) | 001-coleta-dados FR-006 (campos novos do perfil: `usina.nome_curto`, `parametros.fontes.inicio_operacao_comercial`, `parametros.fontes.ip_teif`, `analises.fontes.vertimento_minimo`, `analises.descricao_vertimento_minimo` e `textos.ressalva_volume_util`); o uso nos textos → 005-geracao-relatorio |  |
| 009 FR-023 — textos do relatório sem nome, identificador ou valor de usina fora do perfil ou dos dados | em vigor (parte) | textos gerados nas Análises: 004-analises FR-009; textos do relatório: 005-geracao-relatorio |  |
| 009 FR-023 — textos do relatório sem nome, identificador ou valor de usina fora do perfil ou dos dados | em vigor | 005-geracao-relatorio FR-019; trechos que hoje não vêm do perfil: Assumptions (campos a acrescentar ao perfil, 001-coleta-dados) |  |
| 009 FR-023 — textos do relatório sem nome, identificador ou valor de usina fora do perfil ou dos dados | em vigor (parte) | constituição: princípio II; a regra dos textos fica na Geração do relatório |  |
| 009 FR-024 — análises ajustadas ao perfil | em vigor | 004-analises FR-008, US6, SC-008 |  |
| 009 FR-024 — análises ajustadas ao perfil | em vigor (parte) | textos e rótulos que dependem do número de unidades (figura 07, notas): 005-geracao-relatorio FR-019; faixas: 004-analises |  |
| 009 FR-025 — brutos compartilhados; resultados separados por usina | em vigor | 001-coleta-dados FR-010, FR-030 |  |
| 009 FR-025 — brutos compartilhados; resultados separados por usina | em vigor (parte) | 002-tratamento-dados Entradas e saídas (`data/usinas/<slug>/tratamento/`); brutos compartilhados → 001-coleta-dados; regra geral → constituição |  |
| 009 FR-025 — brutos compartilhados; resultados separados por usina | em vigor (parte) | resultados da conferência em `data/usinas/<slug>/conferencia/` → 003-conferencia FR-008 e "Entradas e saídas"; demais → 001-coleta-dados, 002-tratamento-dados, 004-analises e 005-geracao-relatorio |  |
| 009 FR-025 — brutos compartilhados; resultados separados por usina | em vigor (parte) | pasta da etapa: 004-analises Entradas e saídas, FR-004; regra comum: 001-coleta-dados |  |
| 009 FR-025 — brutos compartilhados; resultados separados por usina | em vigor (parte) | relatório em `reports/<slug>/`: 005-geracao-relatorio FR-003; demais pastas: 001-coleta-dados e constituição |  |
| 009 FR-025 — brutos compartilhados; resultados separados por usina | em vigor (parte) | constituição: Requisito Técnico 6; os brutos compartilhados ficam na Coleta |  |
| 009 FR-026 — guia de nova usina no README | a cumprir | README no estado final (T073) |  |
| 009 FR-027 — no máximo duas cópias de segurança | em vigor | 001-coleta-dados FR-014, FR-015 | 07/10/2026: no máximo duas cópias |
| 009 FR-027 — no máximo duas cópias de segurança | em vigor | constituição: Requisito Técnico 5; a ferramenta `copia-seguranca` fica nas regras comuns da Coleta | 07/10/2026: pedido do usuário |
| 009 FR-028 — excluir as cópias de 06/10 ou antes | cumprido | excluídas em 07/10/2026 (T002) | 07/10/2026: autorização do usuário |
| 009 FR-029 — sem .bak soltos; uma cópia nos dados tratados | em vigor (parte) | 002-tratamento-dados FR-028 (só a versão imediatamente anterior); `.bak` soltos → cumprido no inventário aplicado em 07/10/2026 e constituição | 07/10/2026: pedido do usuário ("no MÁXIMO 2 versões") |
| 009 FR-029 — sem .bak soltos; uma cópia nos dados tratados | em vigor (parte) | constituição: Requisitos Técnicos 3 e 5; os `.bak` soltos saíram em 07/10/2026 (T016) | 07/10/2026: inventário aprovado |
| 009 FR-030 — no máximo duas versões anteriores por arquivo bruto | em vigor | 001-coleta-dados FR-029 | 07/10/2026: mesmo limite das cópias |
| 009 FR-030 — no máximo duas versões anteriores por arquivo bruto | em vigor (parte) | constituição: Requisito Técnico 4; a poda fica na Coleta |  |
| 009 FR-031 — inventário antes de excluir | cumprido | inventário apresentado e aprovado em 07/10/2026 (T014 e T015); a regra de aprovação fica na Governança 2 | 07/10/2026: inventário aprovado |
| 009 FR-032 — o que sai com a aprovação | cumprido | aplicado em 07/10/2026 (T016) | 07/10/2026: inventário aprovado |
| 009 FR-033 — documentos do usuário só com aprovação | em vigor (parte) | constituição: Requisito Técnico 6 (documentos fora do git) e Governança 2 (exclusão de arquivos do usuário só com aprovação); a movimentação foi cumprida em 07/10/2026 | 07/10/2026: inventário aprovado |
| 009 FR-034 — brutos e tratados não excluídos | cumprido | conferido em 07/10/2026 (T017: `data/raw/` intacto) |  |
| 009 FR-035 — README no estado final | a cumprir | README no estado final (T073) |  |
| 009 FR-036 — seção "Conclusão" antes das notas, numa página | em vigor | 005-geracao-relatorio FR-029, FR-031 |  |
| 009 FR-037 — frase de abertura e quatro listas | em vigor (parte) | quatro listas e conteúdo dos itens (uma frase, número e seções): 004-analises FR-045, FR-046; frase de abertura, títulos e até cinco itens por lista: 005-geracao-relatorio |  |
| 009 FR-037 — frase de abertura e quatro listas | em vigor (parte) | apresentação, limite de cinco e rótulo das seções: 005-geracao-relatorio FR-030; texto e número de cada item: 004-analises |  |
| 009 FR-038 — catálogo C1 a C11 | em vigor (parte) | regras, limiares, ordem e todos os itens: 004-analises FR-045 e catálogo; corte nos cinco primeiros itens: 005-geracao-relatorio | 07/10/2026: catálogo aprovado sem ajustes |
| 009 FR-038 — catálogo C1 a C11 | em vigor (parte) | corte em cinco no PDF e no Markdown: 005-geracao-relatorio FR-030; regras e ordem: 004-analises |  |
| 009 FR-039 — sem afirmar causa nem avaliar desempenho | em vigor | 004-analises FR-047 |  |
| 009 FR-039 — sem afirmar causa nem avaliar desempenho | em vigor (parte) | constituição: princípio II; os termos proibidos ficam nas Análises |  |
| 009 FR-040 — C2 nomeia a unidade geradora | em vigor | 004-analises FR-048 |  |
| 009 FR-041 — conclusão não repete as constatações | em vigor | 004-analises FR-049 |  |
| 009 FR-042 — aba CONCLUSAO, FONTES e nota das regras | em vigor (parte) | todos os itens com lista, ordem, regra, texto e seções: 004-analises FR-045, FR-046; aba, FONTES e nota metodológica: 005-geracao-relatorio |  |
| 009 FR-042 — aba CONCLUSAO, FONTES e nota das regras | em vigor | 005-geracao-relatorio FR-032, FR-028, FR-033 |  |
| 009 FR-043 — catálogo como regra geral; aprovação antes da referência | em vigor | 004-analises FR-051; aprovação em Decisões do usuário | 07/10/2026: texto e catálogo aprovados sem ajustes |
| 009 FR-043 — catálogo como regra geral; aprovação antes da referência | em vigor (parte) | constituição: princípios II e III (regras gerais iguais para qualquer usina); o catálogo fica nas Análises | 07/10/2026: catálogo aprovado |
| 009 SC-001 — relatório da São Domingos idêntico ao de referência | em vigor (parte) | resultados das Análises (17 constatações, 19 itens da conclusão): 004-analises SC-001; PDF, Markdown, planilha e figuras: 005-geracao-relatorio | 07/10/2026: conclusão aprovada |
| 009 SC-001 — relatório da São Domingos idêntico ao de referência | em vigor (parte) | 005-geracao-relatorio SC-001 (58 abas: as 57 da época da 009 mais a CONCLUSAO) |  |
| 009 SC-001 — relatório da São Domingos idêntico ao de referência | em vigor (parte) | critério de não regressão da Geração do relatório; prova no fechamento (T059) |  |
| 009 SC-002 — comando único; etapas isoladas; 100 % de recusas sem a anterior | em vigor | 001-coleta-dados SC-010 |  |
| 009 SC-002 — comando único; etapas isoladas; 100 % de recusas sem a anterior | em vigor (parte) | nas Análises: 004-analises SC-007; restante: 001-coleta-dados |  |
| 009 SC-002 — comando único; etapas isoladas; 100 % de recusas sem a anterior | em vigor (parte) | relatório isolado e recusa com código 5: 005-geracao-relatorio SC-011; `completo`: 001-coleta-dados |  |
| 009 SC-003 — cinco specs; 100 % mapeado | a cumprir | no fechamento (T075 e T076) |  |
| 009 SC-004 — constituição sem emendas nem valores de usina | a cumprir | conferido ao gravar a constituição (T026) |  |
| 009 SC-005 — usina fictícia; perfil incompleto recusado | em vigor (parte) | 001-coleta-dados SC-009 (recusa) e SC-013 (coleta da usina fictícia); relatório completo da usina fictícia → 005-geracao-relatorio |  |
| 009 SC-005 — usina fictícia; perfil incompleto recusado | em vigor (parte) | análises: 004-analises SC-008; recusa do perfil: 001-coleta-dados; relatório: 005-geracao-relatorio |  |
| 009 SC-005 — usina fictícia; perfil incompleto recusado | em vigor (parte) | relatório completo, sem menção à São Domingos: 005-geracao-relatorio SC-010; recusa do perfil: 001-coleta-dados |  |
| 009 SC-005 — usina fictícia; perfil incompleto recusado | em vigor (parte) | testes da usina fictícia (T061 e T062); a recusa do perfil fica na Coleta |  |
| 009 SC-006 — no máximo duas cópias; sem .bak soltos; cópias antigas e versão de 30/09 excluídas | em vigor (parte) | 001-coleta-dados SC-011 (duas cópias); demais itens: ações únicas da reorganização |  |
| 009 SC-006 — no máximo duas cópias; sem .bak soltos; cópias antigas e versão de 30/09 excluídas | cumprido (parte) | conferido em 07/10/2026 (T017); a regra continua nos Requisitos Técnicos 3 e 5 |  |
| 009 SC-007 — testes cobrem as etapas, sem rede | em vigor | constituição: Fluxo de Desenvolvimento e Qualidade 1 |  |
| 009 SC-008 — exclusões só do inventário aprovado | cumprido | conferido em 07/10/2026 (T017) |  |
| 009 SC-009 — conclusão da São Domingos | em vigor (parte) | itens, regras, seções, termos e UG2: 004-analises SC-001, SC-006; uma página e até cinco itens por lista: 005-geracao-relatorio | 07/10/2026: texto aprovado |
| 009 SC-009 — conclusão da São Domingos | em vigor (parte) | uma página, quatro listas, até cinco itens, item com a seção: 005-geracao-relatorio SC-006; regras, termos e unidade geradora: 004-analises; aprovação do texto: cumprida | 07/10/2026: texto aprovado |
| 009 SC-009 — conclusão da São Domingos | em vigor (parte) | aprovada pelo usuário em 07/10/2026; os critérios de apresentação ficam na Geração do relatório e os das regras, nas Análises | 07/10/2026: texto aprovado |
