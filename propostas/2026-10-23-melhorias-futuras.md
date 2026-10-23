# Melhorias futuras: SAGER, CCEE e pendências do fechamento da ampliação

**Situação**: lista para decisão do usuário (ainda não é spec) · **Data**: 23/10/2026

Itens anotados pelo usuário em 23/10/2026, no fechamento da ampliação para todos os tipos de usina, na ordem de prioridade que ele definiu: o SAGER primeiro. As specs das etapas descrevem o código como ele está hoje; cada item abaixo, quando for feito, começa por uma spec (ou pela revisão da spec da etapa) aprovada antes do código, como manda a constituição.

## 1. Eventos das unidades geradoras pelo SAGER (prioridade)

- **Decisão do usuário (23/10/2026)**: é a prioridade das melhorias, porque cobre as hidrelétricas e as térmicas, a maioria das usinas de MS com relatório próprio.
- **O que é**: o relatório "SAGER – Mudança de Estado Operativo de UGE" do ONS, uma linha por mudança de estado de cada unidade geradora, com:
  - o estado operativo: LIG (ligada), DCO (desligada por conveniência operativa, a reserva), DPR (desligamento programado), DAU (automático), DUR (de urgência), DEM (de emergência) e DCA;
  - a condição (NOR normal, RFO restrição forçada, RPR restrição programada, TST teste, NOT) e a origem (GUM, GAC, GIM — modernização —, GOT, GRE e outras);
  - a disponibilidade em MW, a data e a hora de início, o número ONS, a situação da consistência (CON, NAC — não acordado —, REV e outras) e o comentário com a causa e o SGI.
  - Não é dado aberto e o MCP do ONS não dá acesso: o arquivo da UHE São Domingos (`SAGER_MUG_20210101 a 20261010.xlsx`, de 01/01/2021 a 10/10/2026, 2.207 eventos das duas unidades) foi obtido pelo usuário junto ao ONS.
- **O que ele acrescentou ao relatório da São Domingos** (avaliação de 23/10/2026, sem mudar o relatório):
  - **confere com os dados abertos**: as horas em reserva batem com as horas de reserva desligada (HRD) e a restrição equivalente da UG2 com a HEDF dos parâmetros das taxas TEIFa e TEIP; o arquivo é confiável para explicar o que o relatório só mede;
  - **usina parada com EVT**: em 1.915 das 2.198 horas de usina parada com EVT de 2021 a 10/10/2026 (87 %), as duas unidades estavam em reserva por conveniência operativa (disponíveis), quase todas em 2025 e 2026, das 7h às 15h; só 0,6 % a 5,5 % da EVT de cada ano coincide com unidade em desligamento forçado. Os indícios da conclusão sobre parada com vertimento apontam para a operação do sistema, não para indisponibilidade da usina; o motivo da reserva não vem no SAGER (comentário vazio);
  - **limitação da UG2**: de equipamento e permanente (cerca de 22,3 a 22,8 MW de 24 MW; 19,6 MW por cerca de 2.000 horas em 2022), ligada ao SGI 74.146/2021 e, em 2024, à medição do perfil hidráulico para a substituição do rotor Kaplan;
  - **divergências DISPF × parâmetros das taxas**: os quatro meses que o relatório não explicava são paradas programadas de modernização (origem GIM), que o ONS conta como reserva, e não como manutenção programada, na TEIP;
  - **desligamento de urgência da UG1** (out–nov/2023, 454 horas, baixo nível de óleo da unidade hidráulica do regulador): contado como manutenção programada, fora da TEIFa;
  - **pista para a parada de 2019**: os pedidos de inspeção do canal de adução citam "sinistros no ano de 2019" por falhas na manta PEAD.
- **O que exige**:
  - uma emenda do princípio IV da constituição, para aceitar um arquivo do ONS fornecido pelo usuário, fora dos dados abertos (a mesma discussão da CCEE, abaixo);
  - uma spec de mudança, com os ajustes das etapas:
    - Coleta: ler o arquivo entregue pelo usuário (por exemplo, numa pasta da usina), com a identificação pela unidade (`MSUHSD_13P8_UG1`: id ONS e número da UG) e a auditoria;
    - Tratamento: os intervalos de cada unidade (cada evento vale até o seguinte da mesma unidade) e as horas por estado, condição e origem;
    - Conferência: SAGER × horas por estado operativo dos parâmetros das taxas TEIFa e TEIP (HS, HRD, HDP, HDF, HEDF);
    - Análises: horas e causas por estado, restrições por SGI, a situação das unidades nas horas com EVT e nas paradas, e os itens da conclusão que isso permite, sem parecer;
    - Geração do relatório: a seção nova, as legendas com a fonte e o nível da unidade;
  - **leitura do arquivo**: o cabeçalho está na linha 6; a data e a hora vêm em colunas separadas; a disponibilidade, com vírgula decimal; o comentário traz marcas de migração (SAMUG), de consistência e de inclusão a limpar antes de ler a causa;
  - **pilotos**: a São Domingos (arquivo já recebido) e uma térmica, por exemplo a William Arjona, com o arquivo pedido ao ONS.

## 2. Avaliação da CCEE como fonte nova

- **Decisão do usuário (22/10/2026)**: avaliar depois do fechamento da ampliação, pelo `/speckit-assess-intake`. Usar a CCEE pede uma emenda do princípio IV da constituição, que hoje limita a coleta aos dados abertos do ONS.
- **Para que serve**: a geração medida da usina isolada onde o ONS só publica o conjunto ou o agregado. O maior ganho é para PCH e CGH em conjunto (a PCH Bandeirante, piloto proposta), usinas Tipo III e UFV sem série própria no ONS.
- **Conjuntos úteis do catálogo aberto da CCEE** (`dadosabertos.ccee.org.br`, lido pela API do CKAN):
  - `geracao_horaria_usina`: geração horária por parcela de usina, desde 03/2024, sem o CEG;
  - `parcela_usina_montante_mensal`: mensal por usina, desde 2024, com o CEG, a geração, a garantia física e o MRE;
  - garantia física definida, por fonte;
  - CVU, sem o CEG.
  - Não há conjunto de restrição de operação (constrained-off).
- **Ponto de partida**: o usuário baixa um mês dos dois primeiros conjuntos (a CCEE bloqueia o download por script) para avaliar a ligação das parcelas com o CEG e com a usina do ONS.

## 3. Seção "Conferência da geração entre fontes" nas usinas sem EVT

- **Hoje**: a seção estava prevista no relatório das usinas sem EVT, mas nunca foi gerada. Ela aparece na tabela das seções omitidas com o motivo "seção ainda não gerada pelo pipeline", e os resultados das conferências G1 a G5 ficam só nas legendas das tabelas e figuras e nas abas `CONF_*` da planilha.
- **O que fazer**: decidir se a seção é gerada (com as conferências da geração por fonte, como a seção equivalente das hidrelétricas com EVT) ou se sai da lista de seções.
- **Efeito**: muda os relatórios aprovados da William Arjona, da Seriemas 1, da Praia Formosa e da Bandeirante, que precisam ser aprovados e registrados de novo.

## 4. Ausências e auditoria da restrição por razão

- **Hoje**: o Tratamento grava a série semi-horária da restrição com a razão, mas não grava as ausências nem a auditoria que o rascunho aprovado previa. A chave `auditoria_restricao_razao` existe em `src/comum/caminhos.py`, mas o arquivo nunca é gravado. Repetições da mesma semi-hora são resolvidas sem contagem.
- **O que fazer**: gravar as ausências e a auditoria da restrição por razão como as dos outros conjuntos (contagens e mensagem), nas eólicas e solares.
- **Efeito**: arquivos novos no Tratamento; o relatório não deve mudar, salvo se a qualidade dos dados passar a citar essas ausências.

## 5. Ligação dos códigos de programação no catálogo

- **Hoje**: o catálogo só liga à usina o código de programação igual ao id ONS ou com o prefixo do conjunto. Ficam de fora o da São Domingos (`PRUHSD`, id ONS `MSUHSD`) e dois da William Arjona (`MSUTWI - 334` e `MSUTWI - 434`, até 11/02/2026). O catálogo mostra a programação dessas usinas como "ausente".
- **Efeito hoje**: os relatórios não são afetados, porque o perfil traz os códigos certos. O `perfil` da São Domingos devolve o código 6 (perfil diferente do catálogo em `cobertura.programacao`), e o rascunho de uma usina nova com código assim vem sem o código e com a programação "ausente".
- **O que fazer**: ampliar a regra de ligação (por exemplo, pelo nome publicado e pelo estado, ou pelo código com sufixo) e conferir as usinas de MS antes de mudar.
