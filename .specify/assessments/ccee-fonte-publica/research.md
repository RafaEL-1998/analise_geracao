# Idea Research: CCEE como fonte pública nova do pipeline

- **Slug**: ccee-fonte-publica
- **Created**: 2026-10-23
- **Evidence confidence (overall)**: medium-high — alta no que vem dos dois arquivos baixados pelo usuário e dos dados do projeto; baixa nos metadados do catálogo da CCEE (licença, termos de uso, início das séries, republicações), porque a API do CKAN respondeu 403 a todas as chamadas em 23/10/2026.

Cálculos desta pesquisa: scripts da sessão de 23/10/2026 em `scratchpad/ccee/` (fora do projeto): `explorar.py` (estrutura dos arquivos), `cobertura_ms.py` e `cobertura_ms2.py` (catálogo de MS × CCEE), `pilotos.py` (hora a hora, 08/2026), `mensal_ons.py` (mês a mês, 01 a 08/2026), `mscao.py` (composição do CJU_MSCAO). Os arquivos da CCEE foram só lidos, como dados não confiáveis. Convenção usada: "GCG" = `GERACAO_CENTRO_GRAVIDADE`; "FPI" = `FATOR_PERDA_INTERNA`; "GCG/FPI" = geração sem a perda interna.

## Users & Demand

- O usuário (fiscal da AGEMS) decidiu avaliar a CCEE em 22/10/2026 e confirmou em 23/10/2026, com o princípio "esse projeto busca usar tudo e qualquer dado disponível pelos meios públicos" — [source: `intake.md`; `propostas/2026-10-23-melhorias-futuras.md`, item 2] (confidence: high)
- Necessidade observada no relatório aprovado da PCH Bandeirante: ele só mostra o conjunto e diz que "a geração da usina isolada consta da medição da CCEE e dos registros do agente, que este relatório não usa" — [source: `reports/bandeirante/relatorio_analise_estatistica.md`, linha 107; `src/relatorio/comum.py:833`; `specs/005-geracao-relatorio/spec.md`, FR-048] (confidence: high)
- Perfis sem garantia física: a William Arjona e a Bandeirante foram completadas "só com dados do ONS", sem garantia física; sem ela, a regra C5 da conclusão não é avaliada — [source: `usinas/william_arjona/perfil.toml`, `usinas/bandeirante/perfil.toml`] (confidence: high)
- O usuário baixou à mão, em 23/10/2026, o horário de 08/2026 e o mensal de 2026 para esta avaliação — [source: `referencias/ccee/geracao_horaria_usina_202608.csv.gz` e `referencias/ccee/parcela_usina_montante_mensal_2026.csv`, gravados em 23/10/2026 13:04] (confidence: high)
- Outros usuários (equipe e direção da AGEMS) não foram consultados — ASSUMPTION (confidence: low)

## Prior Art

- **Conferência manual de 01/10/2026** (São Domingos, amostra de 07/2026): parcela 888272; período p ↔ hora p−1 do ONS; GCG = geração do ONS × FPI, com resíduo ≤ 0,14 MW; `GERACAO_VERIFICADA_ONS` e `DISPONIBILIDADE_VERIFICADA_UG` vazias; download por script bloqueado (Akamai 403). A spec registra que a amostra "confirma que o registro de 68,7 MW de 15/05/2019 é erro do ONS" — [source: `specs/003-conferencia/spec.md`, "Conferências manuais (fora do fluxo)"; memória do projeto, 01/10/2026] (confidence: high)
- **BI da ANEEL, 02/10/2026** (São Domingos): a série diária da CCEE vai de 02/2013 a 11/2024; "Bruta" ≈ ONS × 1,002 e "Líquida" ≈ ONS × 0,984 — [source: memória do projeto, 02/10/2026; `specs/003-conferencia/spec.md`, linha 452] (confidence: medium — arquivos de apoio excluídos em 07/10/2026)
- **Decisões anteriores**: 05/10/2026, CCEE e ANEEL fora do fluxo; 07/10/2026, exclusão de `data/ccee/` e `data/aneel_bi/`; 22/10/2026, a CCEE fica para uma avaliação própria e a Coleta continua só com o ONS — [source: `specs/003-conferencia/spec.md`, linhas 432 a 443; `specs/001-coleta-dados/spec.md`, linhas 842 e 860] (confidence: high)
- **Constituição 3.2.0** (aprovada em 23/10/2026): o princípio IV aceita outra fonte pública por mudança da spec da Coleta aprovada pelo usuário, que declara instituição, endereço, método de acesso, conjuntos, identificação da usina em cada um e termos de uso; as regras de varredura, ausências, download e versões, dicionários e extração valem para toda fonte; os dados brutos ficam numa pasta própria em `data/raw/`; a legenda cita a instituição (princípio VII) — [source: `.specify/memory/constitution.md`; `propostas/2026-10-23-emenda-constituicao-3.2.0.md`] (confidence: high)
- **Avaliação do SAGER** (mesmo dia): o SAGER não é público e ficou como anexo fora do fluxo; a CCEE é publicada para qualquer pessoa, por isso a via dela é a mudança da spec da Coleta — [source: `.specify/assessments/sager-eventos-ug/research.md`; constituição, princípios IV e X] (confidence: high)
- Usos externos dos dados da CCEE em fiscalização não foram pesquisados (nenhum outro host aberto) — [UNVERIFIED]

## Market & Context

- **Hoje**: na PCH em conjunto, o relatório tem duas partes e mostra o peso da usina na potência do conjunto (Bandeirante: 35,7 % desde 01/07/2025), sem estimar a geração — [source: `reports/bandeirante/relatorio_analise_estatistica.md`, linhas 105 a 115] (confidence: high)
- **Custo de não fazer, em MS** (catálogo de 23/10/2026, 149 usinas com CEG): 19 só têm geração do conjunto no ONS, 46 só do agregado e 77 nenhuma; a CCEE de 2026 traz a geração própria de 19, 37 e 7 delas — [source: `data/catalogo/usinas.csv`, `data/catalogo/cobertura.csv`; `cobertura_ms2.py`] (confidence: high)
- **Térmicas sem geração no ONS**: 7 UTE de MS (Amandina, Amandina II, Costa Rica, Iaco Agrícola e Suzano RRP1, Tipo II-B; Fibria MS e Fibria MS-II, Tipo II-C) somam 354,3 MWmed na CCEE em 08/2026. Na Geração por usina de 08/2026, o ONS publica linhas da Suzano, das duas Fibria e do Conj. Ivinhema 2 (de que a Amandina e a Amandina II saíram em 13/11/2025, pela composição dos conjuntos), todas sem valor — [source: mensal 2026; `data/raw/geracao_usina_2/GERACAO_USINA-2_2026_08.parquet`] (confidence: high)
- **Alternativas de hoje**: pedir a medição ao agente por ofício (não público, iria para anexo) ou exportar à mão do BI da ANEEL, como em 02/10/2026 — [source: constituição, princípio X; memória do projeto, 02/10/2026] (confidence: medium)

## Data & Constraints

### Os dois arquivos recebidos

- **Horário 08/2026**: 2.989.392 linhas = 4.018 parcelas × 744 períodos; 36 colunas; separador `;`, ponto decimal, UTF-8; 61,4 MB comprimido. `PERIODO_COMERCIALIZACAO` corre de 1 a 744 no mês, 24 por `DATA`, e `DATA` confere com o período em todas as linhas. Em 2 parcelas, `SIGLA_USINA` tem quebra de linha dentro do campo — [source: `explorar.py`, `pilotos.py`] (confidence: high)
- **Mensal 2026**: 31.460 linhas, 31 colunas, meses 202601 a 202608 (3.837 a 4.022 parcelas por mês), fora de ordem no arquivo. Duas linhas têm 36 campos (campos vazios a mais; parcelas 896708 São Simão e 1001124 CGH Osvaldo, 05/2026) — [source: `explorar.py`] (confidence: high)
- **Unidade do mensal**: o GCG mensal é a média das 744 horas do horário (diferença máxima de 5 × 10⁻¹³ nas 4.018 parcelas), isto é, MWmed — [source: `explorar.py`] (confidence: high)
- **Colunas vazias para a maioria**: `GERACAO_VERIFICADA_ONS` só tem valor em 133 parcelas (90 "Usinas com CVU" e 43 "Demais usinas"); `DISPONIBILIDADE_VERIFICADA_UG` em 80; nenhuma hidrelétrica tem as duas — [source: contagem no horário de 08/2026] (confidence: high)

### 1. Ligação parcela ↔ CEG ↔ usina do catálogo do ONS

- **Horário ↔ mensal**: as 4.018 parcelas do horário estão no mensal de 08/2026 pelo código (`CODIGO_PARCELA_USINA` = `COD_PARCELA_USINA`); o mensal tem 4 a mais, nenhuma de MS; a sigla confere em 4.016 (as 2 restantes só diferem pela quebra de linha) — [source: `explorar.py`] (confidence: high)
- **Parcela → CEG** (08/2026, Brasil): 3.980 parcelas com um CEG; 4 com uma lista de CEG no mesmo campo (até 5); 38 sem CEG. Em MS, nenhuma linha de 2026 sem CEG ou com lista — [source: `explorar.py`; contagem no mensal 2026] (confidence: high)
- **CEG → parcelas**: 3.488 CEG; 3.263 com uma parcela e 225 com mais de uma (até 21). Nas 66 usinas de MS do catálogo ligadas pelo CEG exato em 08/2026 (79 parcelas, com a Ilha Solteira): 55 com uma parcela, 10 com duas e 1 com quatro. Pela UF da parcela, a CCEE tem em MS 68 CEG e 80 parcelas, todas com um CEG só — [source: `explorar.py`, `cobertura_ms.py`] (confidence: high)
- **Por que há várias parcelas** (MS): consórcio (CGH Córrego: 4 parcelas de 4 perfis de agente, com `CAP_T` de 0,474 + 1,102 + 1,326 + 1,274 = 4,176 MW, igual à potência do catálogo); combustível (William Arjona: gás 367 e óleo 947449); contrato (Ilha Solteira: cotas 224 e ACL 896145; Fótons de São George e São Paulino: parcela da usina e parcela "SABESP PIE", desde 08/2026); P1 e P2 (Iaco Agrícola) — [source: `cobertura_ms2.py`] (confidence: high)
- **Como somar à usina**: a usina é a soma das parcelas do mesmo CEG no mês. Isso confere na potência da CGH Córrego e na Ilha Solteira (2 parcelas; correlação horária 0,99994 com o ONS); que valha para toda usina é ASSUMPTION — [source: `cobertura_ms2.py`, `pilotos.py`] (confidence: medium)
- **Parcelas mudam no tempo**: as Seriemas 1 a 8 só aparecem em 08/2026; as Fótons de São George ganharam parcela nova em 08/2026; a parcela de óleo da William Arjona existe desde 09/2021. A ligação precisa ser lida mês a mês no mensal, que é o único com o CEG — [source: `cobertura_ms2.py`; intake] (confidence: high)
- **CEG da CCEE × catálogo do ONS** (Brasil, 2026): 3.499 CEG distintos; 3.313 iguais a um CEG do catálogo; 121 só pelo número central (estado, número e dígito), com prefixo de tipo ou sufixo diferente; 65 sem correspondência. Em MS, 3 só pelo número: PCH Aquarius (catálogo `PCH.PH.MS.000859-1.01`, CCEE `CGH.PH.MS.000859-1.02`), UFV Calcário Bela Vista e UFV Planacon (sufixo `.01` × `.00`). O número central se repete em 19 grupos de CEG do catálogo e em 2 da CCEE — [source: `cobertura_ms2.py`] (confidence: high)
- **Homônimos**: em 08/2026, 8 parcelas têm "São Domingos" na sigla (GO, SP, MS, RN, SC, RS); só a 888272 tem o CEG `UHE.PH.MS.028761-0.01`. No Brasil, 13 siglas de parcela se repetem — [source: `explorar.py`] (confidence: high)
- **Estado**: a UF da parcela pode diferir do estado do CEG (São Simão: CEG de GO, UF MG). Em MS, as 80 parcelas têm UF MS e CEG `.MS.`. O catálogo do ONS põe em MS a UHE Ilha Solteira (CEG de SP; na Geração por usina, `SPILS`, SP) e a UFV Maravilhas III (CEG de PE) — [source: `cobertura_ms.py`; `data/catalogo/usinas.csv`] (confidence: high)
- **Modalidade**: o tipo de despacho da CCEE não segue a modalidade do ONS em 8 usinas de MS: 3 Tipo II-B do ONS são "IIC" na CCEE (Amandina II, Costa Rica, Iaco), as 2 Fibria (Tipo II-C) são "IIB" e 3 Tipo III são "IIB" — [source: `cobertura_ms.py`] (confidence: high)

### 2. Cobertura das usinas de MS do catálogo

Catálogo de 23/10/2026: 171 linhas de MS, 149 com CEG e 22 sem CEG (UFV Jaraguari I a XXII). Ligação pelo CEG exato ou pelo número central; "2026" = em algum mês de 01 a 08/2026 — [source: `cobertura_ms.py`, `cobertura_ms2.py`] (confidence: high)

| Modalidade (ONS) | Usinas | Na CCEE em 2026 | Em 08/2026 |
|---|---|---|---|
| Tipo I | 3 | 3 | 3 |
| Tipo II-A | 2 | 2 | 2 |
| Tipo II-B | 9 | 5 | 5 |
| Tipo II-C | 89 | 23 | 23 |
| Tipo III (2 "em DIT") | 46 | 37 | 36 |
| **Total** | **149** | **70** | **69** |

| Tipo | Usinas | Na CCEE em 2026 |
|---|---|---|
| CGH | 9 | 5 |
| PCH | 16 | 15 |
| UFV | 86 | 18 |
| UHE | 5 | 3 |
| UTE | 33 | 29 |

| Nível da geração no ONS (`cobertura.csv`) | Usinas | Na CCEE em 2026 | GCG em 08/2026 (MWmed) |
|---|---|---|---|
| próprio | 7 | 7 | 1.339,1 (1.209,3 da Ilha Solteira) |
| conjunto | 19 | 19 | 78,4 |
| agregado (Tipo III) | 46 | 37 | 364,9 |
| ausente | 77 | 7 | 354,3 |

- **Em conjunto, 19 de 19**: as 4 PCH do CJU_MSCAO (Bandeirante), as 8 UFV do CJU_MS4FINO (Seriemas 1 a 8) e as 7 UFV do CJU_MS4FRBE (Fótons de São George 01 a 05 e de São Paulino 01 e 02), todas com série própria na CCEE. As 15 UFV entram na CCEE entre 05 e 08/2026 e têm início de operação comercial de 01/08 a 22/08/2026 — [source: `cobertura_ms2.py`] (confidence: high)
- **Tipo III, 37 de 46**: ficam de fora CGH Bela Miragem, CGH Cachoeira Branca, CGH São João I e II, CGH Vitor Andrade de Brito (0,4 a 0,9 MW), UFV Cergrand Itaporã e Santa Terezinha (0,18 e 0,24 MW), UTE Sidrolândia e UTE Vetorial Ribas do Rio Pardo (3,5 MW); a UTE Vista Alegre II só vai até 07/2026 — [source: `cobertura_ms2.py`] (confidence: high)
- **UFV sem série própria no ONS**: o ganho são as 15 em conjunto e 3 das 5 Tipo III. As 66 UFV Tipo II-C sem geração no ONS (Chapadão 1 a 19, Cassilândia 1 a 8, Paranaíba 1 a 11, Talismã, Verdão 1 a 6, Fótons de Santa Marta 01 a 08 e outras) também não estão na CCEE de 2026, nem as 22 Jaraguari sem CEG (busca pelo nome) — [source: `cobertura_ms2.py`] (confidence: high); que estejam sem operação comercial é ASSUMPTION (confidence: low)
- **Tipo II-B fora da CCEE**: UHE Baixo Verde I e III, UTE Star 3 e UTE Sucuriú, também sem geração no ONS — [source: `cobertura_ms2.py`] (confidence: high)
- **Universo da CCEE em MS** (08/2026): 68 CEG e 80 parcelas; só os 3 do número central não batem pelo CEG exato com o catálogo — [source: `cobertura_ms.py`] (confidence: high)

### 3. As quatro pilotos em 08/2026

Comparação hora a hora com a geração tratada pelo pipeline (`data/usinas/<slug>/tratamento/geracao_horaria.csv`, hora de início, FR-015 da spec do Tratamento) e, no mês inteiro, com o arquivo bruto do ONS. Deslocamentos de −2 a +2 h testados — [source: `pilotos.py`, `mensal_ons.py`] (confidence: high)

- **São Domingos** (usina × usina; parcela 888272):
  - horário confirmado: período p ↔ hora p−1 do ONS; correlação 0,999988 sem deslocamento, contra 0,855 e 0,857 com −1 e +1 h;
  - perdas confirmadas com correção do limite: |GCG/FPI − ONS| tem média de 0,036 MW e máximo de 0,28 MW (não 0,14 MW, como na amostra de 07/2026); 50 das 744 horas passam de 0,1 MW e nenhuma de 1 MW;
  - energia: GCG/ONS = 0,9869 em 08/2026 e de 0,9835 a 0,9869 em cada mês de 01 a 08/2026; GCG/FPI ÷ ONS = 1,0018. Os dois valores lembram a "Líquida" (0,984) e a "Bruta" (1,002) do BI da ANEEL;
  - FPI horário de 0,630 a 1,000 (516 valores); `GERACAO_VERIFICADA_ONS` e `DISPONIBILIDADE_VERIFICADA_UG` vazias, como em 01/10;
  - no mensal: garantia física 36,4 MWmed e `CAP_T` 48,0 MW, iguais ao perfil — [source: `pilotos.py`, `mensal_ons.py`; mensal 2026] (confidence: high)
- **William Arjona** (usina × usina; parcelas 367 gás e 947449 óleo, esta zerada em 08/2026):
  - só 8 horas com geração no mês (31/08, 16h a 23h);
  - `GERACAO_VERIFICADA_ONS` da parcela 367 é igual à série tratada do ONS nas 744 horas (diferença máxima 0,0005 MW) com p ↔ p−1: a CCEE repete a geração verificada do ONS dessa usina;
  - o GCG difere nas rampas: 16h, ONS 0,4 e GCG 18,3 MW; 22h, ONS 144,5 e GCG 34,0 MW; 23h, ONS 5,7 e GCG 0. Diferença máxima de 110 MW numa hora; correlação 0,921 sem deslocamento e 0,986 com +1 h;
  - energia: GCG/ONS = 0,943 em 08/2026, 0,9986 em 03/2026 (7.010 MWh) e 0,63 em 02/2026 (0,84 com a `GERACAO_TESTE` de 176 MWh);
  - `DISPONIBILIDADE_VERIFICADA_UG` = disponibilidade operacional tratada do ONS (diferença máxima 0,052 MW; a CCEE tem uma casa decimal);
  - no mensal: garantia física 11,4 MWmed, que o perfil não tem — [source: `pilotos.py`, `mensal_ons.py`] (confidence: high)
- **Bandeirante** (soma das 4 PCH do CJU_MSCAO × conjunto do ONS; uma parcela cada, FPI = 1):
  - hora a hora: correlação 0,34; diferença média 13,9 MW e máxima 28,4 MW; nenhum deslocamento melhora;
  - energia: 24.721 MWh na CCEE × 29.220 MWh no ONS (0,846). Por dia, a razão vai de 0,6 (01 a 11/08) a 1,4 (20 a 31/08);
  - por mês em 2026: 0,95 a 0,98 de 01 a 03; 0,61 a 0,70 de 04 a 07; 0,85 em 08;
  - o conjunto do ONS repete o mesmo valor por 3 horas ou mais em 26 trechos (210 horas), como 59,07 MW por 22 horas, enquanto as 4 PCH variam na CCEE; o ONS publica linhas das 4 PCH sem valor e classifica o conjunto como "TÉRMICA";
  - as 5 UTE que saíram do conjunto em 07/2025 não explicam a diferença (a correlação cai para 0,28 com elas);
  - série própria da Bandeirante na CCEE: 744 horas, 11,98 MWmed, máximo de 27,08 MW, 8.913 MWh, 36,0 % da energia do conjunto na CCEE (o peso na potência no relatório é 35,7 %); no mensal, garantia física 19,02 MWmed e `CAP_T` 28,0 MW — [source: `pilotos.py`, `mensal_ons.py`, `mscao.py`; relatório da Bandeirante] (confidence: high)
- **Seriemas 1** (soma das 8 UFV do CJU_MS4FINO × conjunto do ONS; uma parcela cada, FPI = 1):
  - de 22/08 a 31/08 (as 240 horas que o pipeline tratou): correlação 0,9945; diferença média 3,5 MW e máxima 94,6 MW numa hora; energia CCEE/ONS = 1,0049; melhor sem deslocamento;
  - mês inteiro: o ONS tem 43.527 MWh no conjunto e valores desde 05/2026 (3.004, 32.632 e 16.631 MWh em 05, 06 e 07); na CCEE, o GCG horário das 8 é zero até 22/08 05h (primeira hora com geração no período 511). A energia anterior à operação comercial (22/08/2026) só aparece no mensal, como `GERACAO_TESTE`: GCG + teste = 0,993 do ONS em 08/2026. Antes de 08/2026 não há parcela das Seriemas no mensal;
  - série própria da Seriemas 1: 1.804 MWh em 08/2026, 126 horas com geração, máximo de 46,9 MW, 12,7 % do conjunto na CCEE; garantia física 16,1 MWmed, igual ao perfil; `FATOR_OPERACAO_COMERCIAL` 0,3226 (10 de 31 dias) — [source: `pilotos.py`, `mensal_ons.py`] (confidence: high)
- **Outras de MS com valor no ONS em 08/2026** (p ↔ p−1; diferença hora a hora de GCG/FPI × ONS; razão de energia GCG/ONS):
  - Três Lagoas (UTE, Tipo I): média 0,10 MW, máxima 0,20 MW; 0,972 (GCG/FPI: 0,997);
  - Onça Pintada (UTE, Tipo II-A): 0,015 e 0,24 MW; 0,865 (GCG/FPI: 0,999); de 01 a 08/2026, 0,865 a 0,886;
  - Eldorado (UTE, Tipo II-C): 0,67 e 5,97 MW; 1,016 (de 01 a 08/2026, 1,002 a 1,018);
  - Santa Luzia I (UTE, Tipo II-C): 0,29 e 1,83 MW; 1,007 (0,997 a 1,008);
  - CJU_MS4FRBE (7 UFV): 0,416 em 08/2026; com a `GERACAO_TESTE`, 0,977, 0,915 e 0,910 em 06, 07 e 08 — [source: `pilotos.py`, `mensal_ons.py`] (confidence: high)
- **Agregados Tipo III de MS** (indicativo): as 16 hidrelétricas Tipo III na CCEE (108,7 MWmed) somam 0,966 do agregado "PQU MSMS HID" do ONS; as 16 térmicas Tipo III (256,0 MWmed) somam 5,2 vezes o "PQU MSMS TERM". A composição dos agregados do ONS não é conhecida — [source: `pilotos.py`; `cobertura_ms.csv`] (confidence: medium)

### 4. Metadados, acesso por script e versões

- **API do CKAN em 23/10/2026**: `package_show` dos dois conjuntos, `package_list` e `datastore_search` com `limit=1` responderam HTTP 403 com a página "Acesso bloqueado — seu acesso foi bloqueado por não atender às políticas de segurança da CCEE", que manda abrir chamado com o código de erro e o IP. Chamadas com o curl padrão, sem cabeçalho nem user-agent trocados, ligadas ao endereço público do servidor de borda, sem seguir redirecionamento; nada foi feito para contornar. No `datastore_search`, o identificador do recurso foi o nome do conjunto, porque o `package_show`, que o daria, estava bloqueado; o 403 veio da borda, antes do CKAN — [source: chamadas de 23/10/2026] (confidence: high)
- **Resultado**: hoje não há leitura por script nem dos metadados; o download de arquivos já era bloqueado em 01/10/2026. A proposta de 23/10/2026 diz que o catálogo foi lido antes pela API do CKAN — [source: memória do projeto, 01/10/2026; `propostas/2026-10-23-melhorias-futuras.md`, item 2] (confidence: high no bloqueio de hoje; medium na leitura anterior)
- **Metadados conhecidos só da leitura anterior** (não reconfirmados): horário desde 03/2024, sem o CEG; mensal desde 2024, com o CEG; garantia física por fonte; CVU sem o CEG; nenhum conjunto de restrição de operação (constrained-off) — [source: `intake.md`; proposta, item 2] (confidence: medium)
- **Periodicidade vista nos arquivos**: horário em um arquivo por mês; mensal em um arquivo por ano, com os meses acumulados; em 23/10/2026, o mensal ia até 08/2026 e não tinha 09/2026, isto é, a defasagem ficava entre 23 e 53 dias depois do fim do mês. Que essa defasagem seja a regra é ASSUMPTION — [source: arquivos recebidos] (confidence: medium)
- **Licença e termos de uso**: não lidos (bloqueio) — [UNVERIFIED]
- **Versões e recontabilizações**: os arquivos não têm data de publicação nem número de versão, só `MES_REFERENCIA`; uma republicação só seria vista pelo conteúdo (por exemplo, pelo hash). Que a CCEE republique meses após recontabilização é ASSUMPTION — [source: colunas dos arquivos] (confidence: high na ausência do campo; low na republicação)
- **Dicionário de dados**: não obtido; unidades e definições (GCG, FPI, `FATOR_RATEIO_PERDA_GERACAO`, `GERACAO_TESTE`) foram inferidas dos números — [source: esta pesquisa] (confidence: medium)
- **Volume**: 61,4 MB comprimido por mês no horário; de 03/2024 a 08/2026 (30 meses), cerca de 1,8 GB se os meses forem parecidos — ASSUMPTION (confidence: medium)

### 5. Nível do dado (princípio VIII) e o que a spec da Coleta declararia (princípio IV)

- **Nível**: a CCEE publica por parcela de usina, abaixo da usina; a usina é a soma das parcelas do mesmo CEG, sem divisão. Cada parcela traz o agente (`COD_PERF_AGENTE`, `SIGLA_PERFIL`, `NOME_EMPRESARIAL`) e o submercado. Nas usinas em conjunto no ONS, a CCEE dá a usina, e o conjunto do ONS segue como outro número — [source: arquivos; `cobertura_ms2.py`] (confidence: high)
- **Grandeza**: o GCG é a energia referida ao centro de gravidade do submercado, depois da perda interna. Nas usinas com FPI ≠ 1 (São Domingos, Três Lagoas, Onça Pintada), GCG/FPI fica perto da geração do ONS; nas PCH e UFV vistas, FPI = 1. A "geração" da CCEE não é a mesma grandeza que a geração verificada do ONS — [source: `pilotos.py`; nomes das colunas] (confidence: medium na interpretação; high nos números)
- **Princípio VIII**: o texto fala dos três níveis em que o ONS publica (usina, conjunto, agregado). A parcela da CCEE e a usina somada a partir dela não estão nessa lista — [source: constituição, princípio VIII] (confidence: high)
- **O que a spec da Coleta teria de declarar** (princípio IV, 3.2.0), pelo que se viu:
  - instituição: CCEE; endereço: `dadosabertos.ccee.org.br`, conjuntos `geracao_horaria_usina` e `parcela_usina_montante_mensal` (e os de garantia física e CVU, se usados);
  - método de acesso: hoje, só o download manual pelo usuário (API e download por script com 403);
  - identificação da usina: o CEG no mensal → os códigos de parcela de cada mês → o horário; com regra para CEG em lista, parcela sem CEG e CEG que só bate pelo número central;
  - termos de uso: não conhecidos;
  - o que a fonte não oferece: dicionário de dados, data de publicação e versão, listagem por script para a varredura;
  - extração e auditoria: as 2 linhas com campos a mais no mensal de 2026, as quebras de linha na sigla, as parcelas fora do CEG;
  - pasta própria em `data/raw/` (Requisitos Técnicos, item 6) — [source: constituição; esta pesquisa] (confidence: high)
- **Outros princípios atingidos**: III (o perfil já tem o CEG; os códigos de parcela mudam por mês); V (convenção p ↔ p−1 e soma das parcelas, no Tratamento); VI (conferência CCEE × ONS onde as duas existem, com tolerância a definir); VII (legenda com a CCEE como instituição); IX (os relatórios de referência que mudarem precisam de nova aprovação) — [source: constituição] (confidence: high)

## Evidence Against the Idea

- **Sem acesso por script**: a API do CKAN e o download dão 403; a varredura de todos os arquivos e o "baixar só o novo ou o que mudou" do princípio IV dependeriam do download manual mensal pelo usuário (61 MB por mês no horário), sem listagem automática — [source: chamadas de 23/10/2026; constituição, princípio IV] (confidence: high)
- **Termos de uso, licença e início das séries não confirmados**: a constituição pede que a spec declare os termos de uso, e eles não puderam ser lidos — [source: esta pesquisa] (confidence: high)
- **Série horária curta**: o horário começa em 03/2024 (leitura anterior), e as séries do ONS da São Domingos e da Bandeirante começam em 2018 e 2019; o período de análise da usina seria maior que a série horária da CCEE — [source: intake; `data/usinas/*/tratamento/geracao_horaria.csv`] (confidence: medium)
- **Grandeza diferente da do ONS**: o GCG inclui a perda interna e é referido ao centro de gravidade; na William Arjona, a hora a hora difere em até 110 MW nas rampas; na Eldorado e na Santa Luzia I, a CCEE fica até 1,8 % acima do ONS por mês. A conferência entre fontes não é de identidade — [source: `pilotos.py`, `mensal_ons.py`] (confidence: high)
- **O conjunto da Bandeirante não fecha**: a soma das 4 PCH na CCEE fica entre 0,61 e 0,98 do conjunto do ONS por mês em 2026, com correlação horária de 0,34 em 08/2026. A conferência diz que as fontes não coincidem, não qual está certa; uma conferência com meta interromperia o fluxo (princípio VI) — [source: `mensal_ons.py`; spec da Conferência, Assumptions] (confidence: high no fato; medium na consequência)
- **UFV em operação de teste**: antes da operação comercial, a geração só está no mensal (`GERACAO_TESTE`), não no horário; a Seriemas 1 só tem horário desde 22/08/2026, e os meses de teste (05 a 07/2026) não estão nos arquivos — [source: `pilotos.py`, `mensal_ons.py`] (confidence: high)
- **Ganho em UFV menor que o esperado**: as 66 UFV Tipo II-C de MS sem geração no ONS também não estão na CCEE; o ganho em UFV são as 15 em conjunto e 3 Tipo III — [source: `cobertura_ms2.py`] (confidence: high)
- **Ligação com pontos frágeis**: 121 CEG da CCEE (Brasil) só batem com o catálogo pelo número central, 3 deles em MS; 38 parcelas sem CEG e 4 com lista; códigos de parcela que mudam de um mês para outro — [source: `explorar.py`, `cobertura_ms2.py`] (confidence: high)
- **Custo de mudança**: spec da Coleta e ajustes no Tratamento, na Conferência, nas Análises e na Geração do relatório; nova aprovação dos relatórios de referência afetados (princípio IX), como os da Bandeirante e da Seriemas 1 — [source: constituição] (confidence: high)
- **O bloqueio cresceu**: em 01/10/2026 só o download era bloqueado; em 23/10/2026, também a API de metadados, que antes respondeu — [source: memória do projeto; proposta, item 2; chamadas de 23/10/2026] (confidence: medium)

## Gaps & Open Questions

- [NEEDS CLARIFICATION: os termos de uso e a licença dos conjuntos da CCEE, e se permitem coleta automatizada]
- [NEEDS CLARIFICATION: se o 403 é permanente; e, se a CCEE liberar o acesso por chamado (a página de bloqueio pede para abrir chamado com o código de erro e o IP), se esse acesso ainda conta como "sem pedido" no princípio IV]
- [NEEDS CLARIFICATION: o início real do horário (03/2024?) e do mensal (01/2024?), a defasagem de publicação e se a CCEE republica meses após recontabilização]
- [NEEDS CLARIFICATION: o dicionário de dados da CCEE: definição e unidade de GCG, FPI, `FATOR_RATEIO_PERDA_GERACAO` e `GERACAO_TESTE`]
- [NEEDS CLARIFICATION: qual grandeza o relatório mostraria (GCG ou GCG/FPI) e com que tolerância seria a conferência CCEE × ONS]
- [NEEDS CLARIFICATION: por que a soma das 4 PCH na CCEE e o conjunto CJU_MSCAO do ONS divergem em 2026 (valores repetidos por até 22 horas; conjunto classificado como "TÉRMICA"); pergunta ao ONS ou ao agente]
- [NEEDS CLARIFICATION: o que compõe o agregado térmico Tipo III de MS no ONS ("PQU MSMS TERM"), 5,2 vezes menor que a soma das térmicas Tipo III na CCEE]
- [NEEDS CLARIFICATION: se as 66 UFV Tipo II-C sem geração e as 22 Jaraguari sem CEG estão sem operação comercial]
- [NEEDS CLARIFICATION: se existe base horária pública da geração em teste, antes da operação comercial]
- [NEEDS CLARIFICATION: se a garantia física do mensal da CCEE pode ser a fonte dos parâmetros que faltam nos perfis da William Arjona e da Bandeirante (princípio III: parâmetro com fonte e data)]
- [NEEDS CLARIFICATION: como o princípio VIII trataria a parcela da CCEE e a usina somada a partir dela, já que o texto lista só os níveis do ONS]

## Sources

- https://dadosabertos.ccee.org.br/api/3/action/package_show?id=geracao_horaria_usina (host: dadosabertos.ccee.org.br, policy: confirmed-by-user em 23/10/2026; resultado: HTTP 403 "Acesso bloqueado")
- https://dadosabertos.ccee.org.br/api/3/action/package_show?id=parcela_usina_montante_mensal (host: dadosabertos.ccee.org.br, policy: confirmed-by-user; HTTP 403)
- https://dadosabertos.ccee.org.br/api/3/action/package_list (host: dadosabertos.ccee.org.br, policy: confirmed-by-user; HTTP 403)
- https://dadosabertos.ccee.org.br/api/3/action/datastore_search?resource_id=geracao_horaria_usina&limit=1 (host: dadosabertos.ccee.org.br, policy: confirmed-by-user; HTTP 403; uma única tentativa)
- Arquivos da CCEE baixados pelo usuário em 23/10/2026 (dados não confiáveis, só leitura): `referencias/ccee/geracao_horaria_usina_202608.csv.gz`, `referencias/ccee/parcela_usina_montante_mensal_2026.csv`
- Dados do projeto (só leitura): `data/catalogo/usinas.csv`, `cobertura.csv`, `conjuntos.csv`, `catalogo.json` (montado em 23/10/2026 13:51 UTC); `data/raw/geracao_usina_2/GERACAO_USINA-2_2026_01.parquet` a `_2026_08.parquet`; `data/usinas/{sao_domingos,william_arjona,bandeirante,seriemas_1}/tratamento/geracao_horaria.csv`; `data/usinas/william_arjona/tratamento/disponibilidade_horaria.csv`; `usinas/*/perfil.toml`
- Documentos do projeto: `.specify/memory/constitution.md` (3.2.0); `.specify/assessments/ccee-fonte-publica/intake.md`; `.specify/assessments/sager-eventos-ug/research.md`; `propostas/2026-10-23-melhorias-futuras.md`; `propostas/2026-10-23-emenda-constituicao-3.2.0.md`; `specs/001-coleta-dados/spec.md`; `specs/002-tratamento-dados/spec.md` (FR-015); `specs/003-conferencia/spec.md`; `specs/005-geracao-relatorio/spec.md`; `reports/bandeirante/relatorio_analise_estatistica.md`; memória do projeto (registros de 01 e 02/10/2026)
- Scripts desta pesquisa: `scratchpad/ccee/` da sessão de 23/10/2026 (`explorar.py`, `cobertura_ms.py`, `cobertura_ms2.py`, `pilotos.py`, `mensal_ons.py`, `mscao.py`)
