# Idea Intake: Eventos das unidades geradoras pelo SAGER do ONS

- **Slug**: sager-eventos-ug
- **Created**: 2026-10-23
- **Source**: pasted text (pedido do usuário) e repo path `propostas/2026-10-23-melhorias-futuras.md` (item 1); arquivo de exemplo em `usinas/sao_domingos/documentos/SAGER_MUG_20210101 a 20261010.xlsx` (fora do git)
- **Type**: new-capability

## Idea (as captured)

> Eventos das unidades geradoras pelo SAGER do ONS (item 1, prioridade, de propostas/2026-10-23-melhorias-futuras.md). Usar o relatório "SAGER – Mudança de Estado Operativo de UGE" (um arquivo xlsx por usina, pedido pelo usuário ao ONS; não é dado aberto) como fonte nova do pipeline, para as hidrelétricas e as térmicas (a maioria das usinas de MS com relatório próprio). Ele traz cada mudança de estado de cada unidade geradora (LIG, DCO, DPR, DAU, DUR, DEM, DCA), a condição (NOR, RFO, RPR, TST, NOT), a origem (GUM, GAC, GIM...), a disponibilidade em MW, a data e a hora, o número ONS, a situação da consistência e o comentário com a causa e o SGI. A avaliação de 23/10/2026 com o arquivo da UHE São Domingos (usinas/sao_domingos/documentos/SAGER_MUG_20210101 a 20261010.xlsx, 2.207 eventos de 2021 a 10/10/2026) mostrou: as horas conferem com os parâmetros das taxas TEIFa e TEIP; 87 % das horas de usina parada com EVT tinham as duas unidades em reserva por conveniência operativa; a limitação da UG2 é de equipamento (SGI 74.146/2021, estudo de troca do rotor Kaplan); as divergências DISPF × parâmetros são modernizações (origem GIM) contadas como reserva; o desligamento de urgência da UG1 em 2023 ficou fora da TEIFa. Exige emenda do princípio IV da constituição (arquivo fora dos dados abertos, fornecido pelo usuário) e uma spec de mudança. Pilotos: São Domingos e uma térmica (William Arjona), com o arquivo a pedir ao ONS.

Contexto registrado na proposta (`propostas/2026-10-23-melhorias-futuras.md`, item 1): decisão do usuário de 23/10/2026 de tornar o SAGER a prioridade das melhorias, "pois pega tanto UHE quanto térmicas, a maioria aqui no estado".

Estrutura observada no arquivo de exemplo (só leitura): uma aba ("Planilha 1"); título "SAGER - Mudança de Estado Operativo de UGE" na linha 1 e cabeçalho na linha 6, com as colunas Unidade Geradora (`MSUHSD_13P8_UG1`), Estado Operativo, Condição Operativa, Origem, Disponibilidade (vírgula decimal), Data Início Verificada, Hora Início Verificada, Excluir?, Novo Comentário ONS, Número ONS, Status, Comentários e Mensagens.

## Restated

Passar a ler, para cada usina hidrelétrica ou térmica, o arquivo de eventos das unidades geradoras do SAGER do ONS, que o agente fiscalizado entrega à AGEMS por ofício, para que o relatório mostre os estados, as restrições e as causas dos desligamentos de cada unidade, hoje ausentes dos dados abertos, cruzados com toda a série dos dados abertos. A ideia depende de mudar a regra da constituição que limita a coleta aos dados abertos do ONS.

## Origin & Context

- **Raised by**: o usuário (fiscal da AGEMS responsável pelas análises de desempenho das usinas de MS).
- **Obtenção do arquivo** (resposta do usuário de 23/10/2026): pedido por ofício da AGEMS diretamente ao agente fiscalizado, que o extraiu do SAGER do ONS; não veio do ONS nem do portal de dados abertos. O mesmo canal vale para as outras usinas fiscalizadas, inclusive as térmicas.
- **Uso no relatório** (resposta do usuário de 23/10/2026): não há problema em citar o SAGER no relatório de fiscalização.
- **Período** (resposta do usuário de 23/10/2026): cruzar com toda a série dos dados abertos ("quanto mais dados, melhor").
- **Trigger**: em 23/10/2026 o usuário recebeu o arquivo SAGER da UHE São Domingos ("é o documento que queria", não disponível pelo MCP dos dados abertos do ONS). A comparação com o relatório aprovado da usina mostrou informações que os dados abertos não têm (causas, SGIs, reserva por conveniência operativa, regras de contagem das taxas). O relatório e a constituição registram, desde 02/10/2026, que nenhum conjunto aberto do ONS informa os eventos individuais de desligamento com a causa.

## First-Glance Unknowns

- Respondido em 23/10/2026: o canal é o ofício da AGEMS ao agente fiscalizado. [NEEDS CLARIFICATION: prazo e frequência possíveis dos pedidos; se o agente de uma térmica (a William Arjona como piloto), de uma usina em conjunto (Tipo II-C), de uma eólica ou de uma solar tem o mesmo relatório no SAGER; se o pedido pode cobrir o período anterior a 2021 — o arquivo da São Domingos traz eventos "migrados do SAMUG", o sistema anterior ao SAGER, de 14/11/2022 —, já que o usuário quer cruzar com toda a série]
- [NEEDS CLARIFICATION: se o formato (aba, linha do cabeçalho, colunas, códigos) é o mesmo para outras usinas e outros pedidos, ou muda com o tipo de usina ou com o tempo]
- [NEEDS CLARIFICATION: o significado oficial de cada código — estados (LIG, DCO, DPR, DAU, DUR, DEM, DCA), condições (NOR, RFO, RPR, TST, NOT), origens (GUM, GAC, GIM, GOT, GRE, GRB, GGE, GOU, GHN, GAG) e situações (CON, ESP, DDP, NAC, REV, DIS, ART, RRT) — e o documento do ONS que os define]
- [NEEDS CLARIFICATION: a convenção de horário dos eventos (fuso, início verificado) e como o arquivo trata eventos revisados, excluídos ou ainda em consistência]
- [NEEDS CLARIFICATION: o que a emenda do princípio IV deve permitir (arquivos de sistemas do ONS entregues pelo agente por ofício? também a CCEE?) e como registrar a origem (ofício, data de recebimento, agente) de um arquivo que não vem do portal]
- Respondido em 23/10/2026: o SAGER pode ser citado no relatório de fiscalização. [NEEDS CLARIFICATION: como tratar os nomes de pessoas e os endereços de e-mail que aparecem nos comentários]
- [NEEDS CLARIFICATION: o que muda nos relatórios aprovados (princípio IX) — seção nova, conferência nova, itens novos na conclusão — e nos invariantes do relatório das hidrelétricas com EVT]
- Respondido em 23/10/2026: cruzar com toda a série dos dados abertos. [NEEDS CLARIFICATION: como o relatório trata os anos da série sem eventos do SAGER (na São Domingos, 2018 a 2020)]
