# Idea Research: Eventos das unidades geradoras pelo SAGER do ONS

- **Slug**: sager-eventos-ug
- **Created**: 2026-10-23
- **Evidence confidence (overall)**: medium-high (alta no que vem do arquivo da São Domingos e do projeto; média nas regras oficiais, porque a revisão vigente do Submódulo 6.5 não pôde ser lida)

## Disponibilidade por meios públicos (diretriz do usuário de 23/10/2026)

- **Diretriz do usuário**: "esse projeto busca usar tudo e qualquer dado disponível pelos meios públicos"; a avaliação deve descobrir se o SAGER pode ser obtido assim; se não houver como, ele fica como **anexo, fora do pipeline** — [source: mensagem do usuário de 23/10/2026] (confidence: high)
- **Portal de dados abertos do ONS**: dos 79 conjuntos do catálogo, nenhum traz os eventos das unidades geradoras com horário e causa; a busca dirigida ("mudanças de estado operativo … causa … SAGER, SAMUG, SGI") não achou nenhum conjunto relevante — [source: MCP ons-dados, `listar_datasets` e `buscar_dataset`, 23/10/2026] (confidence: high)
- **O que há de público, agregado por mês**:
  - `taxa_teif_teip_parametro`: horas por estado operativo (HS, HRD, HDP, HDF, HDCE, HEDP, HEDF) por unidade e mês, desde 2020 — já usado pelo projeto; é a mesma apuração do SAGER, sem evento, horário nem causa;
  - `taxa_teif_teip_oper`: TEIFa e TEIP "operativas" por usina e mês, desde 06/2021, só Tipo I e II-A — ainda não usado; a diferença para as taxas regulatórias pode mostrar, em dado aberto, as horas desconsideradas pela regra (por exemplo, a franquia de modernização) — ASSUMPTION a conferir;
  - `ind_disponibilidade_fgeracao_uge_mensal` e `_anual` (DISPF, indisponibilidades programada e forçada por unidade) — já usados — [source: MCP ons-dados, `descrever_dataset`] (confidence: high)
- **SAGER**: o módulo de despacho térmico alimenta o portal aberto (a geração térmica por motivo de despacho, já usada); o módulo de apuração de disponibilidade, que gera o arquivo recebido, fica no SINtegre, com acesso só para agentes cadastrados — [source: notícia do manual do SAGER no site do ONS; apresentação "SAGER – Sistema de Apuração da Geração, janeiro de 2024", pelo resultado da busca] (confidence: medium)
- **ANEEL**: recebe do ONS os resultados da apuração dos estados operativos (Submódulo 10.13, item 5.1); não foi achado conjunto aberto da ANEEL com esses eventos; um pedido pela Lei de Acesso à Informação (Fala.BR) à ANEEL não foi testado — [source: Submódulo 10.13; busca de 23/10/2026] (confidence: medium) [NEEDS CLARIFICATION: se um pedido pela LAI à ANEEL devolve os eventos de uma usina]
- **Resultado**: o SAGER não está disponível por meio público aberto; os meios atuais são o ofício da AGEMS ao agente e, talvez, um pedido pela LAI. Pela diretriz do usuário, ele fica como anexo da fiscalização, fora do pipeline — [source: esta pesquisa] (confidence: medium-high)
- **Interpretação das origens**: segundo instruções de operação do ONS (pelo resultado da busca), a origem do evento separa as indisponibilidades de responsabilidade do empreendimento de geração das de responsabilidade do sistema (por exemplo, DPR com origem GAC para intervenção no ativo de conexão) — [source: IO-OI.S.GJR Rev.15 e IO-OI.SE.ROS Rev.30, pelos trechos da busca] (confidence: medium)

## Users & Demand

- O usuário (fiscal da AGEMS) pediu o arquivo por ofício ao agente da UHE São Domingos e o recebeu em 23/10/2026; chamou-o de "o documento que queria" e o pôs como prioridade das melhorias, por cobrir hidrelétricas e térmicas — [source: mensagens do usuário de 23/10/2026; `propostas/2026-10-23-melhorias-futuras.md`, item 1] (confidence: high)
- A necessidade é anterior: desde 02/10/2026 o projeto registra que nenhum conjunto aberto do ONS ou da ANEEL traz os eventos individuais de desligamento das unidades (motivo, causa, início, fim) e que eles precisam ser pedidos ao agente; o relatório aprovado repete isso nas limitações ("os dados abertos do ONS não informam a causa das paradas nem os eventos individuais de desligamento") — [source: memória do projeto, registro de 02/10/2026; `src/relatorio/resumo.py`, `FRASE_LIMITES`; README, "Limitações"] (confidence: high)
- A conclusão aprovada da São Domingos tem itens "a confirmar com o agente" sobre a limitação da UG2 e as paradas com EVT, que o SAGER responde em parte — [source: `reports/sao_domingos/relatorio_analise_estatistica.md`, seção Conclusão; análise de 23/10/2026] (confidence: high)
- Usuários além do fiscal (equipe da AGEMS, direção) não foram consultados — ASSUMPTION (confidence: low)

## Prior Art

- **No projeto**:
  - a TEIFa e a TEIP são recalculadas pelos parâmetros das taxas (horas HS, HRD, HDP, HDF, HEDP, HEDF por unidade e mês, dados abertos), e a decomposição mostra a UG2 como responsável por cerca de 87 % da TEIFa — é a mesma informação do SAGER agregada por mês, sem causa nem horário — [source: specs/004-analises (indicadores oficiais); `data/usinas/sao_domingos/tratamento/horas_estado_mensal.csv`] (confidence: high)
  - a avaliação da CCEE como fonte nova (fora dos dados abertos do ONS) está registrada com a mesma exigência de emenda do princípio IV — [source: `propostas/2026-10-23-melhorias-futuras.md`, item 2] (confidence: high)
  - análise exploratória de 23/10/2026 sobre o arquivo da São Domingos (scripts e resultados em `scratchpad/sager/` da sessão: `eventos.py`, `causas.py`, `intervencoes.py`, `cruzamento.py`, `conferencia_ons.py`) — [source: sessão de 23/10/2026] (confidence: high)
- **No ONS**:
  - o SAGER (Sistema de Apuração da Geração) é a plataforma do ONS para a apuração; o módulo "Apuração de Disponibilidade" substituiu o SAMUG e registra as mudanças de estado operativo das unidades geradoras; os agentes de geração consistem os eventos pelo SINtegre — [source: https://www.ons.org.br/Paginas/Noticias/manual-SAGER-sistema-de-apuracao-da-geracao.aspx] (confidence: high)
  - a incorporação do SAMUG ao SAGER foi em novembro de 2022 (no arquivo, os eventos antigos trazem "Migrado do SAMUG … 14/11/2022") — [source: trecho de busca no site do ONS; arquivo SAGER da São Domingos] (confidence: medium)
  - o processo do SAMUG teve relatório de asseguração razoável de terceiro (2018) — [source: https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/2018%20SAMUG%20%20Asseguracao%20Razoavel.pdf, só pelo título no resultado da busca, não lido] (confidence: low)
- **Definições oficiais dos códigos** (Manual de Procedimentos da Operação, IO-CG.BR.01, Anexo 1 "Classificação de estado operativo, condição operativa e origens de restrições de unidades geradoras", pelo trecho da busca; o PDF da revisão 88 deu 404):
  - LIG: ligada como gerador; DCO: desligada por conveniência operativa do ONS ou por insuficiência de queda útil ou afluência (hidrelétricas); DPR: desligada para manutenção programada ou em intervenções para testes; DUR: desligada em urgência, após tratativas e autorização dos centros do ONS; DEM: desligada em emergência, manualmente, para evitar risco à vida ou dano; DAU: desligamento automático; RFO é condição operativa (restrição forçada); na hidrelétrica sem queda ou afluência, o registro é DCO com condição RFO, origem GRE e disponibilidade 0 — [source: busca em ons.org.br, IO-CG.BR.01 Rev.88] (confidence: medium)
  - as origens GUM, GAC, GIM, GOT, GRB, GGE, GOU, GHN e GAG e as situações CON, ESP, DDP, NAC, REV, DIS, ART e RRT não foram confirmadas em documento — [NEEDS CLARIFICATION]
- **Regras de contagem nas taxas** (Procedimentos de Rede, Submódulo 10.13, revisão 2019.08, lido; o vigente é o Submódulo 6.5, revisão 2025.06, que não abriu):
  - o ONS coleta e consiste as mudanças de estado, as condições e a disponibilidade das unidades de usinas despachadas centralizadamente e as entrega à ANEEL, à CCEE e aos agentes — [source: Submódulo 10.13, item 5.1] (confidence: high)
  - TEIP e TEIFa são calculadas para cada hidrelétrica e para cada termelétrica com CVU diferente de zero, despachadas centralizadamente, com 60 meses — [source: Submódulo 10.13, itens 6.13.1 a 6.13.3] (confidence: high)
  - HRD é "o período em que a unidade não está em serviço por interesse sistêmico"; HDCE, desligada por condições externas — [source: Submódulo 10.13, item 6.13.3] (confidence: high)
  - são desconsideradas nas taxas as intervenções de modernização ou reforma que tragam ganhos operativos, até 12 meses por unidade (a "franquia"), e as do início de operação comercial, até 960 horas — [source: Submódulo 10.13, item 6.13.5; REN ANEEL 1.033/2022, pelo resultado da busca; Nota Técnica 178/2025-SFT/ANEEL sobre a UHE Jacuí, pelo resultado da busca] (confidence: high na regra, medium na citação da ANEEL)
  - pedidos do agente para alterar evento já consistido só são analisados em até 90 dias do início, até 30 de novembro de cada ano — [source: Submódulo 10.13, item 7.2] (confidence: high)

## Market & Context

- Hoje, sem o SAGER, o fiscal tem as horas mensais por estado (dados abertos) e precisa perguntar ao agente a causa de cada limitação e de cada parada; na fiscalização de 14 a 16/10/2026 isso foi feito por ofício e pela agenda presencial — [source: memória do projeto; `usinas/sao_domingos/documentos/` (minuta do ofício da agenda da fiscalização)] (confidence: high)
- Custo de não fazer: o relatório continua dizendo "a confirmar com o agente" em itens que o SAGER responde (causa da restrição da UG2, natureza das paradas com EVT, modernizações), e as quatro divergências DISPF × parâmetros das taxas ficam sem explicação no relatório — [source: análise de 23/10/2026] (confidence: high)
- A ANEEL e a CCEE recebem do ONS os resultados da apuração dos estados operativos; a AGEMS atua na fiscalização por delegação da ANEEL — [source: Submódulo 10.13, item 5.1(c); ASSUMPTION quanto ao canal de acesso da AGEMS pela ANEEL] (confidence: medium / low)

## Data & Constraints

- **Arquivo da São Domingos**: uma aba, título na linha 1, cabeçalho na linha 6, 13 colunas, 2.207 eventos (UG1 1.207, UG2 1.000), de 01/01/2021 00:00 a 10/10/2026; estados LIG 1.009, DCO 842, DAU 144, DPR 114, DUR 52, DEM 43, DCA 3; disponibilidade com vírgula decimal; cada evento vale até o seguinte da mesma unidade — [source: arquivo, lido em 23/10/2026] (confidence: high)
- **Conferência com os dados abertos** (138 meses-unidade, 2021-01 a 2026-09): DCO ≈ HRD; a restrição forçada equivalente da UG2 = HEDF (529, 822, 541, 531 e 358 horas em 2021, 2022, 2023, 2025 e 2026; 731 × 619 em 2024); LIG = HS na UG1; na UG2, LIG passa de HS em 260 a 415 horas por ano, sem explicação — [source: `conferencia_ons.py`, 23/10/2026] (confidence: high; o desvio da UG2 em LIG: open question)
- **Regras observadas nos dados** (conferidas com as horas publicadas): as paradas programadas de origem GIM (1.613 horas na São Domingos) entram como HRD, e não como HDP; os desligamentos de urgência (DUR) entram como HDP, e não como HDF (UG1 em 2023: HDP 891 = 422 DPR + 469 DUR) — [source: `conferencia_ons.py`] (confidence: high na observação; a regra do DUR não foi achada em documento — NEEDS CLARIFICATION)
- **Achados da análise** (o valor da fonte): 87 % das 2.198 horas de usina parada com EVT de 2021 a 10/10/2026 tinham as duas unidades em DCO, das 7h às 15h, quase todas em 2025 e 2026; a limitação da UG2 é de equipamento, ligada ao SGI 74.146/2021 e ao estudo de troca do rotor Kaplan (03/2024); a UG1 teve 454 horas de urgência em 2023 fora da TEIFa — [source: `cruzamento.py`, `intervencoes.py`] (confidence: high)
- **Universo em MS**: usinas de modalidade Tipo I, II-A ou II-B, que o ONS apura no SAGER, são 4 UHE e 10 UTE; as PCH, CGH e UFV são Tipo II-C ou III (fora do despacho centralizado, provavelmente sem eventos no SAGER) — [source: `data/catalogo/usinas.csv`, catálogo de 22/10/2026; ASSUMPTION quanto à cobertura do SAGER para II-B e II-C] (confidence: high nas contagens, low na cobertura)
- **Período**: o arquivo começa em 01/01/2021; o usuário quer cruzar com toda a série dos dados abertos (São Domingos desde 2018); eventos de 2018 a 2020, se existirem, vêm do SAMUG migrado — [source: resposta do usuário de 23/10/2026; arquivo] (confidence: high / pedido anterior a 2021 — NEEDS CLARIFICATION)
- **Dados pessoais**: 2.074 dos 2.207 comentários (94 %) trazem nome, login ou e-mail de pessoas (operadores do ONS e do agente); a limpeza usada na análise deixa só o texto do evento, sem e-mail — [source: contagem de 23/10/2026] (confidence: high)
- **Constituição 3.1.0**:
  - princípio IV ("Fonte: a Coleta DEVE acessar só o portal de dados abertos do ONS"; varredura, versões e dicionários pensados para o portal) — exige emenda para aceitar um arquivo entregue pelo agente por ofício, com regras próprias de proveniência (ofício, data de recebimento, agente), versões e auditoria — [source: `.specify/memory/constitution.md`] (confidence: high)
  - princípio VII (legendas com o conjunto, o identificador e a data de obtenção) e VIII (nível do dado: o SAGER é por unidade geradora, abaixo do nível da usina) — pedem a forma de citar o arquivo e o nível da unidade — [source: constituição] (confidence: high)
  - princípio IX: seção nova nos relatórios aprovados da São Domingos e da William Arjona exige nova aprovação e novo registro das referências — [source: constituição] (confidence: high)
  - Governança 2 ("a spec de mudança é excluída" ao concluir): na mesma data, o usuário mandou excluir a spec 006 ("foi algo do projeto; o importante é ter consolidado o pipeline e partir para melhorias, futuramente homologação e produção") e manter a 007; a pasta 006 foi excluída em 23/10/2026 (no histórico do git); a 007 continua em conflito com a regra — [source: constituição; mensagens do usuário de 23/10/2026] (confidence: high)
  - a diretriz do usuário ("usar tudo e qualquer dado disponível pelos meios públicos") é mais ampla que o princípio IV de hoje (só o portal do ONS; ANEEL e CCEE com emenda) e pesa na avaliação da CCEE — [source: mensagem do usuário de 23/10/2026; constituição] (confidence: high)

## Evidence Against the Idea

- **Não é dado aberto e depende do agente**: cada atualização exige um ofício e a resposta do agente; não há download automático nem garantia de periodicidade — [source: resposta do usuário de 23/10/2026] (confidence: high)
- **O arquivo vem do próprio fiscalizado**: embora extraído do SAGER do ONS, ele chega pelo agente; a integridade precisa ser conferida com os dados abertos (na São Domingos, as horas conferem com as publicadas, o que mitiga o risco) — [source: análise de 23/10/2026] (confidence: medium)
- **Cobertura limitada**: só usinas despachadas centralizadamente (em MS, 4 UHE e 10 UTE); PCH, CGH, eólicas e solares em conjunto ou Tipo III provavelmente ficam de fora; e o período começa em 2021 no arquivo recebido — [source: Submódulo 10.13; catálogo] (confidence: medium)
- **Códigos sem documento público lido**: as origens e as situações não foram confirmadas; a revisão vigente do Submódulo 6.5 não foi lida — [source: esta pesquisa] (confidence: medium)
- **Custo de mudança**: emenda da constituição, spec de mudança nas cinco etapas, nova aprovação dos relatórios de referência das usinas afetadas; compete com a avaliação da CCEE — [source: constituição; proposta de melhorias] (confidence: high)
- **Alternativa mais barata**: as horas por estado já estão nos dados abertos; o SAGER poderia ficar como anexo da fiscalização (análise à parte, como a de 23/10/2026), sem entrar no pipeline — ASSUMPTION (confidence: low)

## Gaps & Open Questions

- [NEEDS CLARIFICATION: o significado oficial das origens (GUM, GAC, GIM, GOT, GRE, GRB, GGE, GOU, GHN, GAG) e das situações (CON, ESP, DDP, NAC, REV, DIS, ART, RRT) — pedir ao agente o anexo da IO-CG.BR.01 vigente ou o manual do SAGER]
- [NEEDS CLARIFICATION: a regra oficial que leva o desligamento de urgência (DUR) às horas programadas (HDP) — Submódulo 6.5 vigente]
- [NEEDS CLARIFICATION: se o agente consegue extrair do SAGER o período anterior a 2021 (SAMUG migrado), para cruzar com toda a série]
- [NEEDS CLARIFICATION: se o agente de uma térmica (William Arjona, Tipo I) e os de Tipo II-B entregam o mesmo relatório, com o mesmo formato]
- [NEEDS CLARIFICATION: por que, na UG2 da São Domingos, as horas ligadas do SAGER passam das horas em serviço (HS) publicadas em 260 a 415 horas por ano]
- [NEEDS CLARIFICATION: o motivo das reservas (DCO) sem comentário em 2025 e 2026 (energético ou elétrico) — não está no SAGER; pedir ao ONS]
- [NEEDS CLARIFICATION: como o relatório cita a fonte (ofício, data de recebimento, agente) e se nomes de pessoas nos comentários podem aparecer em algum lugar (planilha) ou devem ser sempre retirados]

## Sources

- MCP ons-dados (catálogo do portal de dados abertos do ONS: `listar_datasets`, `buscar_dataset`, `descrever_dataset` de `taxa_teif_teip_oper` e `taxa_teif_teip_parametro`), 23/10/2026
- https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/ApresentaçãoSAGERDespachoTermico-Agentes_versaofinal.pdf, IO-OI.S.GJR_Rev.15.pdf, IO-OI.SE.ROS_Rev.30.pdf (host: www.ons.org.br; só os trechos do resultado da busca, não abertos)
- https://www.ons.org.br/Paginas/Noticias/manual-SAGER-sistema-de-apuracao-da-geracao.aspx (host: www.ons.org.br, policy: confirmed-by-user)
- https://www.ons.org.br/ProcedimentosDeRede/Módulo 10/Submódulo 10.13/Submódulo 10.13 2019.08.pdf (host: www.ons.org.br, policy: confirmed-by-user; texto extraído localmente)
- https://www.ons.org.br/MPO/Documento Normativo/3. Instruções de Operação - SM 5.12/3.2. Controle da Geração/IO-CG.BR.01_Rev.88.pdf (host: www.ons.org.br, policy: confirmed-by-user; 404 ao abrir, usado só o trecho da busca)
- https://www.ons.org.br/MPO2/Documento Normativo/4. Rotinas Operacionais - SM 5.13/4.3. Rotinas Pós-Operação/4.3.2. Apuração de Dados/RO-AO.BR.08_Rev.17.pdf (host: www.ons.org.br, policy: confirmed-by-user; lido, mas trata da apuração do despacho e do intercâmbio, sem os estados das unidades)
- https://proxyportais.ons.org.br/ons.portalempregado.proxy/garapi/api/processo/retornarpdf (Submódulo 6.5-PR_2025.06; host: proxyportais.ons.org.br, policy: confirmed-by-user; falhou: certificado não verificado)
- https://www.ons.org.br/AcervoDigitalDocumentosEPublicacoes/2018 SAMUG Asseguracao Razoavel.pdf (host: www.ons.org.br; só citado pelo título no resultado da busca, não aberto)
- https://www2.aneel.gov.br/cedoc/ren20221033.html e https://www2.aneel.gov.br/cedoc/ndsp20252998.pdf (host: www2.aneel.gov.br; não abertos — só os trechos da busca; host não confirmado pelo usuário)
- Fontes internas: `usinas/sao_domingos/documentos/SAGER_MUG_20210101 a 20261010.xlsx`; `data/usinas/sao_domingos/tratamento/` (evt_tratado, programacao_horaria, horas_estado_mensal); `data/catalogo/usinas.csv`; `.specify/memory/constitution.md`; `propostas/2026-10-23-melhorias-futuras.md`; `reports/sao_domingos/`.
