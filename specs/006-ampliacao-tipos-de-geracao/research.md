# Research: Relatórios de Desempenho para Todos os Tipos de Usina

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Data**: 2026-10-09

**Fontes**:
- consultas aos dados abertos do ONS em 09/10/2026: catálogo CKAN e conjuntos em Parquet;
- arquivos brutos locais (`data/raw/`);
- código atual (`src/`) e specs das cinco etapas;
- revisão cruzada dos documentos do plano, feita em 09/10/2026, cujos achados já estão incorporados.

Cada decisão traz a decisão, o motivo e as alternativas rejeitadas. Os números de usina citados são das usinas piloto da spec. Servem só para o plano e os testes de aceitação; nenhum entra no código.

**Numeração**:
- R1 a R30 são as decisões deste plano. Não confundir com as regras de validação física R1 a R9 do Tratamento, citadas no relatório. No tasks.md, escrever "decisão Rn" e "regra Rn".
- D12, D13, D15 e D16 são decisões do [plano da Coleta](../001-coleta-dados/plan.md).
- "Hidrelétrica com EVT" é a UHE, PCH ou CGH com série própria na Energia Vertida Turbinável. Ela segue o caminho de hoje, sem mudança (R6, R14, R16).

## Achados nos dados do ONS

| Nº | Conjunto | Achado |
|---|---|---|
| A1 | Modalidade das usinas | 6.017 linhas, 171 em MS: UHE 5, PCH 16, CGH 9, UTE 33, UFV 86 e 22 linhas de conjunto (Tipo II-C), sem CEG nem id ONS. **Não há coluna de tipo**: o tipo está no prefixo do CEG. Em MS, só 15 das 81 UFV Tipo II-C têm id ONS. |
| A2 | Composição dos conjuntos (`usina_conjunto`) | Traz as datas de entrada e de saída de cada usina no conjunto. Classifica PCH como "UHE". O conjunto Chapadão (`CJU_MSCAO`) tem quatro PCH (Indaiá Grande, Indaiazinho, Bandeirante, Areado) e teve cinco térmicas até 01/07/2025. |
| A3 | Geração por usina | Mudou de publicação em 01/05/2026: nomes ("William Arjona" virou "UT WILL. ARJONA"), grupos de MMGD sem id ONS ("PQU_MSMS_GD" virou vazio) e CEG "-" nos conjuntos. O conjunto Chapadão aparece como térmico e a biomassa até hoje. As PCH Tipo II-C têm linhas próprias desde 05/2026, todas sem valor. Nas usinas Tipo III, o valor é previsão, não medição. |
| A4 | Geração térmica por motivo de despacho | CEG em todas as linhas. A UTE William Arjona teve três códigos de planejamento: 34 (2013 a 08/2018), 334 desde 07/2021 e, de 08/2021 a 02/2026, a divisão em 334 (gás) e 434 (óleo). Nome com duas grafias ("Willian" e "William"). O código vem ora inteiro, ora decimal. |
| A5 | CVU das usinas térmicas | Sem CEG: só o código de planejamento. Até cinco revisões por semana operativa. |
| A6 | CMO semanal | Por subsistema e semana operativa; atualizações do DECOMP podem repetir a semana. |
| A7 | Restrição por constrained-off com detalhe por usina | Semi-horária. Fotovoltaica desde 04/2024 (cinco colunas ausentes de 05 a 12/2024), eólica desde 10/2021. Traz a marca de semi-hora restrita (`flg_geracaorestrita`) e a de recurso inválido. **Todas as UFV de MS só aparecem a partir de 21 a 27/08/2026.** Praia Formosa: 87.984 semi-horas, sem lacuna, 14,9 % com vento inválido. |
| A8 | Restrição por constrained-off sem detalhe (`restricao_coff_eolica_usi`, `restricao_coff_fotovoltaica`) | Só esta base traz a **razão da restrição** (REL, CNF, ENE) e os minutos de cada razão. Vem pela usina (Tipo I e II-B) ou pelo conjunto (Tipo II-C). |
| A9 | Fator de capacidade | Praia Formosa desde 07/2009 (151.310 horas). Os conjuntos solares de MS, só desde 08/2026, com o nome grafado de dois jeitos ("230kV" e "230 kV"). |
| A10 | Programação diária | Código de exibição por usina. O conjunto Chapadão é programado em quatro códigos, um por barra (`MSCAO-<barra>`); a UTE Três Lagoas, em nove unidades; a MMGD, por barra. |
| A11 | Disponibilidade por usina | Só usinas hidrelétricas, UTE e UTN; a UTE William Arjona está presente. |
| A12 | Indicadores DISPF e taxas TEIFa/TEIP | A UTE William Arjona está no DISPF, com as duas grafias do nome; nas taxas TEIFa/TEIP dos anos locais, não. |
| A13 | Capacidade de geração | Unidades geradoras com potência efetiva, combustível e datas de entrada em operação e de desativação, pelo CEG. A UTE William Arjona tem cinco unidades ativas desde 10/07/2021 (177,1 MW) e cinco antigas, desativadas em 2018. As unidades nem sempre têm a mesma potência (Seriemas 1: 21,43 e 28,57 MW). A potência autorizada do cadastro pode divergir da soma das unidades (Seriemas 1: 2,507 MW no cadastro e 50 MW nas unidades). |
| A14 | Volume publicado em Parquet | Despacho 0,14 GB; CVU e CMO, menos de 0,01 GB; fator de capacidade 0,32 GB; restrição eólica com detalhe 0,63 GB, sem detalhe 0,19 GB; fotovoltaica com detalhe 0,15 GB, sem detalhe 0,03 GB; geração por usina 0,73 GB (80 arquivos, de 2000 a 2026). Os mesmos dados em CSV passam de 20 GB. |

## Achados no código atual

| Nº | Achado | Consequência |
|---|---|---|
| B1 | As etapas 2 a 5 leem `data/raw/`, compartilhado por todas as usinas, em três pontos: as datas de obtenção nos manifestos (`analises/geracao.py`, `disponibilidade.py`, `hidrologia.py`, `relatorio/fontes.py`); o resumo do manifesto da EVT, na linha "Versão dos arquivos" da cobertura (`analises/cobertura.py`, `analises/etapa.py`); e o dicionário JSON da EVT, no Tratamento (`tratamento/validacao.py`). | A coleta de outra usina mudaria as datas e a contagem de arquivos do relatório da São Domingos, e o Tratamento não roda sem o dicionário em `data/raw/`. Também é leitura fora da etapa anterior (princípio I). |
| B2 | O registro dos dicionários (`dicionarios.csv`) tem duas linhas por pacote de `CONJUNTOS_PIPELINE`, seja qual for a usina. `CONJUNTOS_PIPELINE` também alimenta as datas de obtenção. | Ampliar a lista de conjuntos levaria a aba DICIONARIOS da São Domingos de 20 para 40 linhas. |
| B3 | A planilha traz as auditorias da Coleta e do Tratamento (abas `*_AUDITORIA`). | Coluna nova num desses arquivos muda a planilha da São Domingos. |
| B4 | As Análises partem da base de EVT (`evt_tratado.parquet`) para a cobertura, os indicadores anuais, o perfil horário e outras seções. As legendas comuns citam a EVT, e a nota da conclusão é um texto fixo de C1 a C11 (`nota_conclusao`). | Os tipos sem EVT precisam de uma base horária própria (R30). A nota da UHE não pode mudar. |
| B5 | As regras da conclusão geram itens em mais de uma lista (C1, C2, C6, C7, C8, C10). A ordem segue a lista e o número da regra. | O catálogo das regras declara as listas possíveis, e a ordem de hoje se mantém (R16). |
| B6 | Os dados brutos são compartilhados. Uma coleta com o portal, de qualquer usina, acrescenta meses e troca arquivos republicados dentro do período das outras. | Refazer a Coleta da São Domingos com `--sem-portal` deixa de reproduzir a referência depois que outra usina baixar dados (R22). |
| B7 | A capa já mostra a modalidade de operação, vinda da ficha do cadastro, e o nome traz o tipo ("UHE São Domingos"). | A capa da UHE atende à FR-024 sem mudança (R29). |

## Decisões

### R1 — Tipo da usina pelo prefixo do CEG

- **Decisão**:
  - O tipo são as três primeiras letras do CEG: UHE, PCH, CGH, UTE, UTN, EOL ou UFV.
  - A linha do cadastro sem CEG é de conjunto de usinas (tipo "conjunto"), e o tipo do conjunto vem da composição.
  - Prefixo fora da lista vira "outro": aparece no catálogo e não recebe perfil.
  - Os tipos publicados pelo ONS (`nom_tipousina`, `id_tipousina`) só são conferidos; a divergência vai para a qualidade dos dados.
- **Motivo**: o cadastro não tem coluna de tipo (A1). Os tipos do ONS juntam PCH e UHE (A2) e já publicaram um conjunto hidráulico como térmico (A3).
- **Alternativas rejeitadas**:
  - `nom_tipousina` da geração: instável e não separa PCH e CGH de UHE.
  - Capacidade de geração: também não separa, e só cobre usinas com unidade geradora cadastrada.

### R2 — Catálogo de usinas na Coleta

- **Decisão**:
  - O comando `python -m src usinas` é da Coleta (`src/coleta/catalogo_usinas.py`). Sem `--sem-portal`, sincroniza com o portal, com o mesmo catálogo CKAN, cache e versões de hoje:
    - os conjuntos cadastrais: Modalidade das usinas, Composição dos conjuntos e Capacidade de geração;
    - o arquivo mais recente de cada conjunto de série usado na cobertura (R3);
    - todos os arquivos do despacho térmico, para os códigos de planejamento (a partir da fase B);
    - os arquivos de geração dos últimos 12 meses completos, para o panorama dos agregados (R21);
    - os dicionários de dados de todos esses conjuntos (princípio IV).
  - Grava `data/catalogo/` (sem `.bak`, RT3):
    - `usinas.csv`, `conjuntos.csv`, `cobertura.csv` e `agregados.csv`;
    - `planejamento.csv`, com os códigos de planejamento por CEG, com o primeiro e o último mês de cada um;
    - `programacao.csv`, com os códigos de exibição da programação por usina e por conjunto;
    - `catalogo.json`, com as datas e os arquivos usados (FR-004).
  - Lista na tela as usinas do filtro (estado, tipo, modalidade), sempre a partir dos arquivos gravados, com a cobertura de cada conjunto do ONS (FR-003).
  - Os downloads vão para as pastas compartilhadas de `data/raw/`. Por isso, as referências usam a Coleta congelada (R22), e o primeiro `usinas` só roda depois do congelamento (R27).
- **Motivo**:
  - Princípio I: só a Coleta acessa o portal, e o catálogo é dela. FR-005 manda reaproveitar os arquivos baixados.
  - O rascunho do perfil precisa dos códigos sem ler os brutos (R5).
  - O cadastro é pequeno (6.017 linhas), e o despacho inteiro tem 0,14 GB (A14).
- **Alternativas rejeitadas**:
  - Montar o catálogo a cada `perfil`: repetiria a consulta ao portal fora da Coleta.
  - Catálogo no git: muda todo dia. Os dados ficam em `data/`.

### R3 — Cobertura de cada conjunto do ONS

- **Decisão**:
  - Para cada usina e cada conjunto do ONS usado no projeto, o nível é um destes:
    - **próprio**: linhas com o identificador da usina e valor preenchido;
    - **conjunto**: o conjunto da usina tem linhas com valor. Vale também quando a usina tem linhas próprias sem valor, como as PCH Tipo II-C na geração (A3);
    - **agregado**: usina Tipo III e MMGD, que só existem no grupo do estado;
    - **ausente**.
  - A verificação usa o arquivo mais recente publicado de cada conjunto de série e o arquivo único dos estáticos. O identificador de cada conjunto é o da R9.
  - `cobertura.csv` grava, por usina e conjunto: o nível, o identificador usado, as linhas, as linhas sem valor, o arquivo e a data de publicação.
  - A cobertura só lista os conjuntos já implementados. A cada fase, um novo `usinas` acrescenta os conjuntos da fase.
- **Motivo**:
  - Um arquivo por conjunto mantém o catálogo do Brasil em minutos.
  - A Coleta da usina escolhida confirma depois o período inteiro.
- **Alternativas rejeitadas**:
  - Varrer todos os arquivos de cada conjunto para todas as usinas: vários GB, e é o que a Coleta já faz para a usina escolhida.
  - Deduzir a cobertura só pelo tipo e pela modalidade: erraria nas PCH em conjunto (A3) e nas usinas que mudam de modalidade.

### R4 — Perfil multitipo, compatível com o perfil atual

- **Decisão**:
  - Continua o mesmo `usinas/<slug>/perfil.toml`, lido com `tomllib`.
  - Em `[usina]`:
    - entram `tipo` e `modalidade`, obrigatórios. Tipo III é recusado: a usina só tem agregado no ONS (FR-001, FR-009);
    - entra `situacao` (`"rascunho"` ou `"conferido"`). Sem o campo, o perfil conta como conferido;
    - nas térmicas, entra `subsistema`, exigido a partir da fase B, com o CVU e o CMO. O rascunho o traz da Capacidade de geração.
  - Em `[identificacao]`:
    - os campos de hoje passam a ser exigidos conforme o tipo e a cobertura (tabela no [data-model](data-model.md)). Em EOL e UFV, o id ONS só é exigido quando um conjunto com cobertura `proprio` o usa (A1);
    - entram `id_conjunto`, `codigos_programacao` (lista, com `cod_programacao` ainda aceito) e `[[identificacao.planejamento]]`, com código, início e fim (UTE e UTN);
    - entra `[[identificacao.membros]]`, opcional: o id ONS e o CEG de cada usina do conjunto, com o período. É usado só na conferência G2 (R13).
  - Em `[parametros]`:
    - ficam os comuns: potência instalada (a capacidade instalada, em EOL e UFV), unidades, garantia física (opcional fora da UHE) e a potência das unidades;
    - a potência das unidades pode vir como `potencia_unitaria_mw`, quando são iguais, ou como a lista `potencias_unidades_mw`, quando diferem (A13). Nos dois casos, a soma tem de dar a potência instalada;
    - entram os do tipo: os de hoje nas usinas hidrelétricas com EVT ou hidrologia, e `combustivel` em UTE e UTN;
    - cada valor tem fonte em `[parametros.fontes]`.
  - `[analises]` é exigida onde há EVT. `[textos]` é opcional.
  - A tabela `[cobertura]` declara o nível de cada conjunto de série que cobre a usina. É o que a Coleta obtém (FR-015).
    - O valor pode ser uma lista, como `["proprio", "conjunto"]`, quando a usina muda de nível no período (caso de borda da spec). A Coleta obtém as duas séries, e os trechos dizem qual vale em cada hora (R7).
    - Os conjuntos cadastrais e o CMO são sempre obtidos para os tipos que os usam.
  - A validação passa a usar uma tabela de campos por tipo (`src/comum/perfil_campos.py`). O padrão do CEG aceita os sete prefixos.
  - O perfil da São Domingos ganha só `tipo = "UHE"` e `modalidade = "TIPO II-A"` (FR-011).
- **Motivo**:
  - A São Domingos fica sem mudança no relatório.
  - O TOML já foi aprovado (D2 do plano da Coleta).
  - O princípio III manda o perfil declarar os conjuntos que cobrem a usina, conferidos pelo fiscal.
- **Alternativas rejeitadas**:
  - Um formato de perfil por tipo: duplicaria a leitura.
  - Classes por tipo: mais código para a mesma regra.
  - Campos de UHE opcionais para todos: perderia a validação da UHE.
  - Ler a cobertura do catálogo a cada execução: uma atualização do ONS mudaria o fluxo sem o fiscal saber.

### R5 — Rascunho do perfil a partir do catálogo

- **Decisão**:
  - `python -m src perfil --ceg <CEG> [--slug <slug>]` lê só `data/catalogo/`, sem portal e sem os brutos.
  - Recusa sem gravar:
    - o CEG fora do catálogo (código 2);
    - a usina Tipo III, ou só com cobertura agregada ou ausente (código 2), com a mensagem da FR-009;
    - o catálogo ainda não montado ou em formato antigo (código 5).
  - O slug vem do nome sem acento, em minúsculas e com `_`, quando não é informado.
  - O rascunho traz `situacao = "rascunho"` e:
    - os identificadores achados: CEG, id ONS (quando há) e conjunto;
    - os códigos de programação de `programacao.csv`: o código igual ao id ONS da usina, ou os que começam pelo id do conjunto sem o prefixo `CJU_` (A10). Sem nenhum dos dois, o campo fica pendente, com a lista dos códigos do estado para o fiscal escolher. A São Domingos, por exemplo, tem o código `PRUHSD` para o id `MSUHSD`;
    - os códigos de planejamento de `planejamento.csv`, com o primeiro e o último mês de cada um (A4);
    - os membros do conjunto, da composição vigente, como `[[identificacao.membros]]`;
    - a `[cobertura]`, do catálogo.
  - Parâmetros publicados pelo ONS, como unidades, potência efetiva, combustível e data de entrada em operação (A13), entram preenchidos. Cada um traz a fonte ("ONS, Capacidade de geração, publicado em dd/mm/aaaa") e fica a conferir.
    - Só contam as unidades ativas, sem data de desativação passada.
    - Divergência entre a potência autorizada do cadastro e a soma das unidades vai para um comentário do rascunho, para o fiscal decidir com a fonte. A Conferência do cadastro continua comparando a potência do perfil com a autorizada.
  - Os demais parâmetros ficam pendentes, como comentário com o campo de fonte, e entram na lista `pendentes`.
  - Perfil existente: nada é gravado. O comando mostra as diferenças entre o perfil e o catálogo e sai com 6, ou com 0 sem diferença.
  - Perfil em rascunho é recusado por qualquer etapa com o código 4 e a lista do que falta, como os demais problemas do perfil.
- **Motivo**:
  - SC-003: o fiscal completa só os parâmetros técnicos.
  - Nada é sobrescrito (FR-007).
  - Os códigos mudam no tempo (A4, A10). O fiscal precisa vê-los para conferir.
- **Alternativas rejeitadas**:
  - Ler os brutos no `perfil`: acessaria dados fora da Coleta.
  - Deixar a Coleta descobrir os códigos sozinha: a extração passaria a depender de identificadores que não estão no perfil (princípio IV).
  - Preencher a garantia física e o IP/TEIF de referência: não vêm do ONS.

### R6 — Série de referência e período

- **Decisão**: a Coleta escolhe a série de referência pelo tipo e pela cobertura:

  | Situação | Série de referência | Identificador | Fase |
  |---|---|---|---|
  | UHE, PCH ou CGH com Energia Vertida Turbinável | EVT (como hoje) | código da usina | A |
  | UTE, UTN, e UHE, PCH, CGH, EOL ou UFV com geração própria (Tipo I, II-A ou II-B) | Geração por usina | id ONS da usina | A |
  | PCH, CGH, EOL ou UFV em conjunto, sem série própria | Geração por usina, do conjunto | id do conjunto | A |
  | EOL ou UFV em conjunto, com série própria na restrição com detalhe | Restrição com detalhe | id ONS da usina | C |

  - Cada linha só vale a partir da fase que implementa o conjunto dela.
  - A série de referência é varrida em todos os arquivos publicados, com o filtro do identificador na leitura do Parquet (princípio IV).
  - O período vai da primeira à última hora com valor preenchido. Linha sem valor não conta.
  - Com a cobertura `["proprio", "conjunto"]` no conjunto da série de referência, o período é a união das duas séries, e cada trecho diz o nível (R7).
  - Nos demais conjuntos, entram os arquivos que se sobrepõem ao período, como hoje.
  - A hidrelétrica com EVT segue o caminho de hoje sem mudança.
- **Motivo**:
  - FR-012 e princípio IV.
  - A geração por usina inteira em Parquet tem 0,73 GB (A14), e a leitura filtra pelo identificador.
- **Alternativas rejeitadas**:
  - Período fixo, como os últimos cinco anos: viola o princípio IV.
  - Período pela data de entrada em operação do cadastro: não reflete os dados publicados.

### R7 — Trechos dentro do período

- **Decisão**:
  - Fora das hidrelétricas com EVT, o período é dividido em trechos quando muda:
    - a modalidade da usina, lida hora a hora na coluna de modalidade da geração;
    - a composição do conjunto, pelas datas da Composição dos conjuntos (A2);
    - o código de planejamento da térmica, pelos períodos do perfil (A4).
  - A Coleta grava `trechos.csv`.
  - O relatório só mostra os trechos que mudam o nível do dado (usina ou conjunto) ou a composição do conjunto. Os números de conjunto são calculados e apresentados por trecho de composição, com as usinas de cada trecho.
  - Mudança de modalidade sem mudança de nível vai só para a planilha.
  - Nas hidrelétricas com EVT, o caminho de hoje não calcula trechos (R29).
- **Motivo**: casos de borda da spec e princípio VIII. O conjunto da PCH piloto teve térmicas até 07/2025 (A2).
- **Alternativas rejeitadas**:
  - Usar a composição atual em todo o período: atribuiria às PCH a geração das térmicas que saíram.
  - Mostrar todos os trechos: na UHE, mudaria o relatório aprovado sem ganho de informação.

### R8 — Registro declarativo dos conjuntos do ONS

- **Decisão**:
  - A `DescricaoConjunto` de `src/coleta/conjuntos.py` vira um registro único (`src/coleta/registro.py`). Para cada conjunto, ele declara:
    - pacote e pasta;
    - tipos de usina;
    - nível: usina, conjunto ou agregado;
    - resolução: horária, semi-horária (inclusive os 48 patamares da programação), semanal, mensal e anual, ou estática;
    - formatos preferidos (Parquet, depois CSV);
    - identificador e conferências, montados a partir do perfil;
    - colunas de valor e convenção de hora;
    - se pode ser série de referência.
  - A Coleta percorre o registro filtrado pelo tipo e pela cobertura da usina (FR-015).
  - EVT, indicadores, programação e cadastro mantêm os módulos próprios, mas também ficam registrados, para o filtro por tipo e os dicionários.
  - **Dicionários e fontes por usina**: o registro dos dicionários e as abas DICIONARIOS e FONTES de cada usina listam só os conjuntos do tipo e da cobertura dela (B2). Na UHE sem `[cobertura]`, são exatamente os dez de hoje, na mesma ordem.
  - **UHE sem `[cobertura]`**: não coleta Composição nem Capacidade. A Coleta dela grava os mesmos arquivos de hoje, mais os dois da R22 (`datas_obtencao.csv` e a cópia do dicionário da EVT).
  - **Arquivos e colunas**: coluna nova só entra em arquivo novo, nunca num arquivo que o relatório da UHE já usa (B3).
  - **Formato**: o `VERSAO_FORMATO` de uma etapa sobe quando muda um arquivo que ela já grava, ou quando a etapa seguinte passa a exigir um arquivo novo. Assim, a etapa seguinte recusa a versão antiga com o código 5 e indica a etapa a refazer (princípio I). Arquivo novo opcional não muda o formato. A Coleta passa ao formato 2 no item 1 da fase A, com os arquivos da R22.
- **Motivo**:
  - Um só lugar diz o que se coleta para cada tipo: é a tabela de aplicabilidade da FR-002.
  - Reaproveita o motor dos conjuntos horários: seleção por período e formato, cache e auditoria.
  - B2 e B3: sem as três regras acima, a planilha da São Domingos mudaria.
- **Alternativas rejeitadas**:
  - Um módulo por conjunto novo: repetiria o motor.
  - Um `if tipo` em cada etapa: espalharia a regra pelo código.

### R9 — Identificação nos conjuntos novos

- **Decisão**:

  | Conjunto | Identificador | Conferência | Observação |
  |---|---|---|---|
  | Geração térmica por motivo de despacho | CEG | código de planejamento entre os do perfil, no período de cada um | código comparado como número; linha com o CEG e código fora da lista conta como "só identificador" |
  | CVU das usinas térmicas | código de planejamento entre os do perfil | subsistema do perfil | revisão mais recente de cada semana, no Tratamento |
  | CMO semanal | subsistema do perfil | nenhuma: é contexto do subsistema | nível agregado |
  | Fator de capacidade | id ONS da usina ou do conjunto | CEG (usina) ou estado (conjunto, de CEG "-") | |
  | Restrição com detalhe por usina | id ONS da usina | CEG | o id do conjunto falta de 05 a 12/2024 na fotovoltaica e não é usado como conferência |
  | Restrição com a razão | id ONS da usina ou do conjunto | CEG (usina) ou estado (conjunto) | |
  | Geração por usina, do conjunto | id do conjunto | estado | CEG "-" desde 05/2026 |
  | Composição dos conjuntos | id do conjunto | CEG de cada usina | estático |
  | Capacidade de geração | CEG | estado | estático |

  - Nomes nunca identificam nem conferem: mudam de grafia (A3, A4, A9).
- **Motivo**: princípio IV, com identificador e conferência, nunca o nome; homônimos excluídos pelos códigos (princípio III).
- **Alternativas rejeitadas**:
  - Nome normalizado como conferência: falha com "Willian/William" e "230kV/230 kV".
  - CVU pelo nome: o CVU não tem CEG (A5).

### R10 — Correções P1 a P5 da Coleta (FR-014)

- **Decisão**: as limitações conhecidas do plano da Coleta são corrigidas na fase A, antes dos conjuntos novos e antes de qualquer download de outra usina (R27):

  | Correção | Limitação de hoje | Correção |
  |---|---|---|
  | P1 | Só os conjuntos horários escolhem entre recursos repetidos no catálogo. A EVT, os indicadores e a programação baixam cada repetição; a programação, em paralelo e com o mesmo `<arquivo>.part` (D13). | A regra de `selecionar_recursos` vale para todos os conjuntos (`evt.py`, `indicadores.py`, `programacao.py`). O arquivo temporário leva o id do recurso. |
  | P2 | Vírgula decimal não aceita nos conjuntos horários e na potência da ficha (D16). | Uma leitura numérica comum aceita vírgula e ponto em todos os conjuntos. |
  | P3 | O pré-teste da EVT usa o texto com acento; a programação só tira espaços; o filtro do Parquet da geração usa o valor como publicado (D12). | Uma normalização única, aplicada à extração e ao pré-filtro. O filtro do Parquet passa a usar as duas formas do valor. |
  | P4 | Num conjunto horário sem a coluna de conferência, as linhas contam como "só identificador", sem `FALHA` (D12). | A coluna de conferência ausente torna o arquivo `FALHA`, com o motivo. |
  | P5 | O CSV vazio da EVT fica `FALHA` sem o motivo (D15). | O motivo ("arquivo vazio") vai para a auditoria. |

- **Motivo**:
  - Com outras usinas, os casos aparecem: os nomes e códigos dos conjuntos novos têm acentos e grafias variadas (A3, A4).
  - O plano da Coleta registra que hoje não afetam a São Domingos. O `comparar` confirma.
- **Alternativas rejeitadas**: corrigir junto com cada conjunto novo. Misturaria a correção com o conjunto e dificultaria isolar uma diferença no relatório da São Domingos.

### R11 — Tratamento das séries novas

- **Decisão**:
  - **Semi-horárias**: gravadas na resolução de 30 minutos e também em hora cheia, pela média das duas meias-horas (FR-016). Hora com uma só meia-hora fica ausente e é contada.
  - **Convenção de hora**: início do intervalo, como na geração por usina. A conferência com a geração horária (R13) confirma. Se a coincidência melhorar com uma hora de deslocamento, a convenção declarada está errada e vira correção, nunca ajuste automático.
  - **CVU**: um valor por unidade de planejamento e semana operativa, o da revisão mais recente.
  - **CMO**: um valor por subsistema e semana, o da publicação mais recente. As duplicatas são contadas.
  - **Semanais levadas à hora**: pelo intervalo da semana operativa, para os cruzamentos.
  - **Sinalizações, sem descarte (FR-017)**:
    - vento ou irradiância marcados como inválidos pelo ONS;
    - fator de capacidade fora de 0 a 1;
    - geração acima da capacidade instalada, com a folga de hoje;
    - CVU ausente ou negativo.
  - Duplicatas entre arquivos e ausências seguem as regras de hoje (princípio V), também no panorama dos agregados (R21).
- **Motivo**: FR-016 e FR-017; princípio V.
- **Alternativas rejeitadas**: converter tudo para hora na Coleta. Perderia a resolução publicada e misturaria etapas.

### R12 — Energia cortada e razão da restrição

- **Decisão**:
  - **Energia cortada da usina**: soma de máx(estimada − verificada, 0) × 0,5 h nas semi-horas com a marca de restrição (`flg_geracaorestrita = 1`).
  - **Semi-horas sem a coluna da marca** (fotovoltaica de 05 a 12/2024, A7): contadas, fora do total e explicadas nas notas.
  - **Diferença fora das semi-horas restritas**: é erro da estimativa, não corte, e não entra.
  - **Razão (REL, CNF, ENE)**: vem da base sem detalhe (A8), na mesma semi-hora. Quando a razão é do conjunto (Tipo II-C), a energia cortada da usina aparece por razão do conjunto. A tabela diz que a razão é do conjunto e a energia é da usina.
- **Motivo**:
  - Na Praia Formosa, a diferença bruta é de 350,5 GWh e, nas semi-horas restritas, de 181,0 GWh. Somar a bruta quase dobraria o corte.
  - A razão só existe na base sem detalhe (A8): por isso o ajuste da FR-013 (R25).
- **Alternativas rejeitadas**:
  - Diferença bruta em todas as semi-horas: superestima o corte.
  - `val_geracaoreferenciafinal`: só nas restrições REL já apuradas, nula na maior parte das linhas.

### R13 — Conferências novas e não aplicáveis

- **Decisão**:

  | Conferência | Bases | Tipos | Meta |
  |---|---|---|---|
  | G1. Geração da usina entre fontes | Geração por usina, Fator de capacidade, Restrição com detalhe (média horária) e Restrição com a razão (`val_geracao`), sempre dois a dois **no mesmo nível** | EOL, UFV | sem meta |
  | G2. Soma das usinas × conjunto | soma das usinas do conjunto (restrição com detalhe) × geração do conjunto, nos trechos com todas as usinas da composição | EOL, UFV em conjunto, com `[[identificacao.membros]]` no perfil | sem meta |
  | G3. Programação | Programação diária (média horária dos patamares) × geração programada do despacho | UTE, UTN | sem meta |
  | G4. Geração verificada | despacho × Geração por usina | UTE, UTN | sem meta |
  | G5. Programação de renováveis | Programação diária × geração programada do Fator de capacidade, no mesmo nível | EOL, UFV | sem meta |
  | DISPF × horas; TEIFa e TEIP refeitas | as de hoje, pelo CEG | UHE, PCH, CGH, UTE, UTN, quando há os indicadores | as de hoje |

  - A tolerância é a de hoje (0,01 MW).
  - G2 sem os membros no perfil fica não aplicável. As séries das outras usinas só entram como contexto identificado (princípio III).
  - Conferência sem base para a usina, o tipo, a modalidade ou o nível vai para `nao_aplicaveis.csv`, com o motivo (FR-019, princípio VI). Exemplos: vazões fora das hidrelétricas; G2 numa usina Tipo I; TEIFa e TEIP de usina ausente das taxas (A12); G1 a G5 numa UHE.
  - O arquivo é novo e registra todas as conferências do catálogo que não se aplicam, inclusive na UHE. O relatório e a planilha da UHE não o leem e continuam com as conferências de hoje (R29). Nos demais tipos, as notas citam as não aplicáveis do tipo, com o motivo.
  - As conferências novas começam sem meta e só registram. Depois das usinas piloto, o usuário pode aprovar uma meta.
- **Motivo**:
  - FR-018 e FR-019; princípio VI.
  - Comparar níveis diferentes, como a usina e o conjunto, não confere nada.
  - Sem histórico, uma meta agora seria arbitrária e poderia parar o fluxo (princípio VI) sem motivo.
- **Alternativas rejeitadas**: usar a meta de 99 % das vazões. É outra grandeza, de outra fonte.

### R14 — Seções do relatório por tipo, em ordem fixa

- **Decisão**:
  - `Secao` (em `src/relatorio/estrutura.py`) ganha `tipos`, um título por tipo e a chave de legenda por tipo. Continua uma única lista, em ordem fixa; cada usina vê só as seções do seu caminho.
  - **Hidrelétrica com EVT** (UHE, PCH ou CGH): `secoes_presentes` devolve exatamente as 17 seções de hoje, na ordem de hoje, com os mesmos títulos e as mesmas legendas (R29). As seções novas ficam fora desse caminho.
  - **Usina sem EVT**: as seções comuns usam a base horária comum (R30), nesta ordem:

  | Nº | Seção | Tipos | Base | Observação |
  |---|---|---|---|---|
  | 1 | Fonte e cobertura dos dados | todos | catálogo, série de referência, trechos | inclui o nível de cada conjunto |
  | 2 | Indicadores anuais | todos | base horária comum | geração, horas paradas, fator de capacidade (EOL, UFV), disponibilidade (quando há) |
  | 3 | Disponibilidade e geração por ano | hidrelétricas, UTE, UTN com disponibilidade | base horária comum | |
  | 4 | Indicadores oficiais do ONS por unidade geradora | hidrelétricas, UTE, UTN com indicadores | indicadores | construtor de hoje |
  | 5 | Série temporal da geração e da disponibilidade | todos | base horária comum | |
  | 6 | Geração mensal e sazonalidade | todos | base horária comum | a sazonalidade pede 12 meses (R17) |
  | 7 | Perfil horário da geração | todos | base horária comum | |
  | 8 | Seções de térmica | UTE, UTN | despacho, CVU, CMO, disponibilidade | R18 |
  | 9 | Seções de eólica e solar | EOL, UFV | fator de capacidade, restrição | R19 |
  | 10 | Composição e geração do conjunto | usinas em conjunto | geração do conjunto, composição | R20 |
  | 11 | Programação diária × verificada | todos com programação | programação, base horária comum | construtor de hoje, com o nível |
  | 12 | Disponibilidade operacional e sincronizada | com disponibilidade | disponibilidade | construtor de hoje |
  | 13 | Afluência, vertimento e nível do reservatório | hidrelétricas sem EVT, com hidrologia | hidrologia | construtor de hoje, sem os cruzamentos com a EVT |
  | 14 | Conferência da geração entre fontes | todos | conferências | G1, G4 ou a de hoje |
  | 15 | Qualidade dos dados | todos | auditorias, sinalizações | |
  | 16 | Conclusão | todos | regras do tipo (R16) | |
  | 17 | Notas metodológicas e limitações | todos | | com as omissões, os níveis e as conferências não aplicáveis |

  - Os números das seções presentes são contínuos, como hoje.
  - O título, a capa e as legendas de cada caminho estão no data-model (seção 6.5).
  - Seção sem base é omitida, com o motivo nas notas (FR-024).
- **Motivo**: FR-020, FR-024 (ordem fixa), SC-001 e princípio VII.
- **Alternativas rejeitadas**:
  - Um relatório por tipo em módulos separados: duplicaria o PDF e o Markdown.
  - Numeração própria por tipo: dá no mesmo e é mais difícil de testar.

### R15 — Granularidade nos números, nas legendas e nas notas

- **Decisão**:
  - Todo dado de tabela e de figura leva o nível (`usina`, `conjunto` ou `agregado`) e o identificador.
  - **Legenda**: a de hoje cita o identificador da usina ("Geração por usina (id ONS …), obtido em …"). Num dado de conjunto ou de agregado, cita o identificador dele com o nível escrito, por exemplo "(conjunto de usinas, id ONS CJU_…)" (FR-024, ajustada na R25).
  - **Constatações**: com número de conjunto, dizem "do conjunto <nome>".
  - **Notas**: o parágrafo de granularidade só entra quando algum número não é da usina. A São Domingos não muda.
  - Nenhum número de conjunto é dividido entre as usinas (FR-023).
- **Motivo**: princípio VIII, FR-023, FR-024 e SC-001.
- **Alternativas rejeitadas**: escrever "nível: usina" em todas as legendas. Mudaria todas as legendas da São Domingos sem acrescentar informação, porque o identificador já diz o nível.

### R16 — Catálogo da conclusão por tipo

- **Decisão**:
  - Cada regra declara:
    - código;
    - tipos;
    - listas possíveis: a regra pode gerar itens em mais de uma, e cada item traz a sua (B5);
    - limiares, em `src/comum/regras.py`;
    - nível exigido: só dado da usina;
    - período mínimo;
    - seções de origem.
  - **Regra só com dado da usina** (princípio VIII):
    - uma regra só é avaliada quando as entradas dela são do nível da usina;
    - número de conjunto não gera item na conclusão da usina. O que ele mostra fica na seção do conjunto, como constatação identificada, e a carteira não o conta;
    - o que não é avaliado vai para as notas, com o motivo.
  - **Hidrelétricas com EVT** (UHE, PCH, CGH): C1 a C11 sem mudança de ordem, de texto, de limiar ou de período mínimo. A nota da conclusão continua o texto de hoje (B4, R29).
  - **Regras comuns** (FR-022): valem para todo tipo que tem a base no nível da usina. Nas usinas sem EVT, são calculadas sobre a base horária comum (R30):
    - C2: TEIFa por unidade;
    - C5: disponibilidade e taxas contra a referência;
    - C8: geração acima da disponibilidade declarada;
    - C10: indisponibilidade total.
    - Sem IP e TEIF de referência no perfil, as partes de C2 e C5 que dependem deles não são avaliadas.
  - **Regras novas**, com os limiares calibrados nas usinas piloto e aprovados pelo usuário no fim de cada fase, como foi feito com C1 a C11:

  | Código | Tipos | Indício | Listas |
  |---|---|---|---|
  | C12 | UTE, UTN | geração abaixo da programada em horas recorrentes | possíveis problemas; a confirmar com o agente |
  | C13 | UTE, UTN | horas disponíveis sem despacho em semanas com CVU abaixo do CMO | a confirmar com o agente |
  | C14 | UTE, UTN | geração por inflexibilidade abaixo da programada | pontos de atenção |
  | C15 | UTE, UTN | geração acima da programada, sem programação correspondente, em horas recorrentes | a confirmar com o agente |
  | C16 | EOL, UFV | energia cortada da usina acima de um limiar da energia estimada | pontos de atenção |
  | C17 | EOL, UFV | recurso (vento ou irradiância) inválido acima de um limiar das semi-horas da usina | a verificar em campo |
  | C18 | EOL, UFV | fator de capacidade próprio abaixo da razão entre a garantia física e a capacidade, quando o perfil traz a garantia física | pontos de atenção |
  | C19 | EOL, UFV | desvio médio entre a geração programada e a verificada da usina acima de um limiar | a confirmar com o agente |

  - **PCH e CGH em conjunto**: sem base no nível da usina, a conclusão diz isso numa frase e não tem itens.
  - **Ordem dos itens**: a de hoje, por lista e depois pelo número da regra.
  - **Nota da conclusão**: nas usinas sem EVT, gerada do catálogo do tipo, com os limiares.
  - Os textos das regras novas seguem o princípio II: fatos, sem parecer nem causa.
- **Motivo**:
  - Princípio II: catálogo declarado, regras iguais para o mesmo tipo.
  - Princípio VIII: indício só com dado da usina.
  - FR-022: no máximo 5 itens por lista.
  - Limiares sem as pilotos seriam palpite.
- **Alternativas rejeitadas**:
  - Avaliar regras com dado do conjunto: atribuiria à usina números de outras, inclusive de térmicas que saíram do conjunto (A2).
  - Prefixos novos por tipo: os códigos R, D e H já são das regras de qualidade.
  - Limiares fixados agora, sem dados.

### R17 — Série de referência curta

- **Decisão**:
  - Seções e regras novas declaram o período mínimo.
  - **Sazonalidade** (distribuição por mês do ano): pede 12 meses distintos.
  - **Tabela por ano**: aceita ano parcial, identificado, como hoje.
  - **Regra nova com limiar anual**: só é avaliada nos anos com o período mínimo dela.
  - C1 a C11 continuam como hoje, sem período mínimo novo (R29).
  - O que fica de fora é listado nas notas, com o motivo.
- **Motivo**:
  - As UFV de MS têm série por usina desde 08/2026 (A7). A Seriemas 1 terá um relatório de cerca de 1,5 mês.
  - FR-024.
- **Alternativas rejeitadas**:
  - Recusar o relatório abaixo de 12 meses: deixaria de fora quase toda a geração solar de MS.
  - Trocar a piloto: a spec permite, mas a usina de MS é a que interessa à AGEMS (ver R25).

### R18 — Térmicas e nucleares

- **Decisão**:
  - **Geração por motivo**:
    - energia verificada e programada de cada motivo, por mês e por ano, com a parcela no total;
    - a soma das unidades de planejamento por hora dá a usina.
  - **Inflexibilidade**: tabela e figura próprias da inflexibilidade programada e verificada, por mês, dentro da seção de geração por motivo (FR-021).
  - **Atendimento ao despacho**:
    - nas horas com geração programada, o desvio verificado − programado;
    - horas e energia abaixo e acima, além do limiar de desvio de `regras.py`;
    - os maiores desvios, na quantidade de hoje (`NUMERO_EVENTOS_RELATORIO`).
  - **Disponível sem despacho**: horas com disponibilidade operacional acima do limiar, sem programação e sem geração, com a potência disponível média.
  - **CVU × CMO**:
    - por semana operativa, o CVU de cada unidade de planejamento comparado com o CMO médio semanal do subsistema;
    - semanas com o CVU abaixo e acima do CMO, com a geração em cada caso;
    - sem julgar o despacho (US2-3).
  - **Usina sem geração no período**: nenhuma divisão por zero. A constatação diz que a usina ficou disponível e não foi despachada, com as horas e a potência disponível (US2-5).
  - **DISPF, TEIFa e TEIP**: o código de hoje, pelo CEG.
- **Motivo**: US2 e FR-021. A usina piloto despacha pouco: cerca de 304 GWh verificados de 07/2021 a 10/2026, média de cerca de 7 MW para 177 MW (A3, A4).
- **Alternativas rejeitadas**: CMO semi-horário. O CVU é semanal (A5), e comparar resoluções diferentes criaria falsos cruzamentos.

### R19 — Eólicas e solares

- **Decisão**:
  - **Fator de capacidade**: o publicado, da usina ou do conjunto, por mês e por ano. Com série própria, o relatório também mostra o fator calculado a partir da geração da usina e da capacidade do perfil, identificado como "calculado neste relatório".
  - **Recurso × geração**: geração verificada por faixa de vento (m/s) ou de irradiância (W/m²). As semi-horas com o recurso inválido ficam fora e são contadas (US3-3).
  - **Aderência à programação**: na seção comum de programação, com o desvio médio e os maiores desvios (US3-4). As duas programações publicadas, a diária e a do fator de capacidade, são conferidas pela G5.
  - Figuras em seaborn, com a paleta central (princípio VII).
- **Motivo**: US3, FR-020 e FR-021.
- **Alternativas rejeitadas**: curva de potência ajustada. Seria um modelo, não um dado.

### R20 — PCH e CGH em conjunto

- **Decisão**:
  - O relatório usa o conjunto: a composição por trecho (R7), a geração do conjunto por trecho, com os tipos de cada trecho identificados, e a programação do conjunto (soma dos códigos do perfil).
  - Não há disponibilidade nem indicadores oficiais da usina: as seções são omitidas, com o motivo nas notas.
  - As linhas próprias sem valor (A3) são contadas no resumo da Coleta e aparecem na qualidade dos dados.
  - As notas dizem que o ONS não publica a geração da usina isolada (US4-1).
  - A conclusão segue a R16: sem itens, com a frase que explica a falta de base no nível da usina.
- **Motivo**: US4 e princípio VIII.
- **Alternativas rejeitadas**: ratear a geração do conjunto pela potência. Viola o princípio VIII.

### R21 — Relatório de carteira

- **Decisão**:
  - **Comando**: `python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao ...]` (`src/relatorio/carteira.py`), da Geração do relatório.
    - Pelo menos uma das duas opções, como a constituição prevê: carteira de um estado ou de um tipo (FR-026, ajustada na R25).
  - **Entradas, só gravadas** (princípio I):
    - o catálogo;
    - e, de cada usina do recorte, o perfil achado pelo CEG em `usinas/*/perfil.toml`, o `etapa.json` e o `resultados.pkl` das Análises.
    - Nenhuma etapa é refeita.
  - **Usinas sem resultado**: listadas com o motivo:
    - sem perfil;
    - perfil em rascunho;
    - perfil inválido;
    - Análises ausentes, com falha, desatualizadas ou em formato antigo;
    - só agregado no ONS (ver o panorama).
    - As linhas de conjunto do catálogo não contam como usina.
  - **Indicadores comparáveis**: as Análises passam a gravar `indicadores_carteira`, com chaves fixas, cada indicador com o nível dele:
    - tipo e período;
    - fator de capacidade, disponibilidade e TEIFa;
    - energia cortada (%) e atendimento ao despacho (%);
    - quantidade de itens em cada lista da conclusão.
  - **Contagem**: todos os itens de cada lista, como a aba CONCLUSAO, e não só os 5 exibidos.
  - **Ordenação**: pela quantidade de "possíveis problemas", depois de "pontos de atenção", depois pelo nome (FR-027).
  - **Panorama**: vem de `data/catalogo/agregados.csv`, com os 12 últimos meses completos, por tipo e por mês. Só entra na carteira com `--estado`: os agregados são publicados por área do estado. Na carteira só por tipo (`brasil_<tipo>`), é omitido, com o motivo nas notas.
    - Os agregados são selecionados pelo estado e pela modalidade (MMGD, Pequenas Usinas Tipo III, TIPO III), nunca pelo nome ou pelo id, que sumiu em 05/2026 (A3).
    - A soma segue as regras de duplicatas e de ausências do Tratamento (R11), e as horas ausentes são listadas.
    - Os valores das usinas Tipo III são identificados como previsão do ONS (A3).
  - **Saída**: `reports/carteiras/<nome>/`, com `<nome>` = `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`, em minúsculas: PDF, Markdown, planilha com a aba FONTES (como a da usina) e figuras em seaborn.
  - **Textos**: nenhum termo de parecer (SC-007), conferido por teste.
- **Motivo**: princípios III, VII e VIII; FR-026, FR-027.
- **Alternativas rejeitadas**:
  - Ler os dados tratados de cada usina: refaria cálculos fora das Análises.
  - Panorama lido dos brutos pela própria carteira: acessaria dados fora das etapas.

### R22 — Relatórios de referência reproduzíveis

- **Problema**:
  - Hoje a referência da São Domingos está dentro das cópias de segurança (`linha_de_base/`). Com no máximo duas cópias e uma nova antes de cada fase, ela seria excluída na segunda fase.
  - Os brutos são compartilhados (B6), e as Análises e o Relatório leem datas em `data/raw/` (B1). Depois que outra usina baixar dados, refazer a São Domingos com `--sem-portal` já não reproduz a referência, mesmo sem mudança de código.
- **Decisão**:
  - **Etapas 2 a 5 sem `data/raw/`** (princípio I, B1): a Coleta passa a gravar, no formato 2:
    - `datas_obtencao.csv`: por conjunto, os arquivos registrados no escopo da usina, a publicação mais recente e a obtenção mais recente. Substitui a leitura dos manifestos nas Análises e no Relatório, inclusive a linha "Versão dos arquivos" da cobertura;
    - `dicionario_evt.json`: a cópia do dicionário da EVT, que o Tratamento passa a ler daqui.
    - As etapas 2 a 5 leem só esses arquivos, o `dicionarios.csv` e os demais resultados da Coleta. Um teste roda as etapas 2 a 5 com `data/raw/` vazio.
  - **Onde ficam as referências**: em `relatorios_referencia/<slug>/`, na raiz do projeto. Cada uma traz:
    - os arquivos do relatório aprovado;
    - a Coleta congelada (`coleta/`): só os arquivos listados no `etapa.json` da Coleta e o próprio `etapa.json`, sem `.bak`;
    - a cópia do perfil usado (`perfil.toml`);
    - o `referencia.json`, com a data de geração fixa, a data da aprovação, o período e o SHA-256 de cada arquivo.
  - **Controle de versões**:
    - os arquivos do relatório e a cópia do perfil entram no git, com uma exceção no `.gitignore` para o PDF aprovado; a Coleta congelada fica fora do git, como `data/`;
    - a referência substituída continua no histórico do git (princípio IX). Por isso, o `referencia` recusa substituir uma referência que ainda não foi commitada.
  - **Cópias de segurança**: `copia-seguranca` passa a copiar `relatorios_referencia/` inteira para cada cópia nova e a conferi-la pelos SHA-256 (RT5).
  - **`python -m src referencia --usina <slug> --data-geracao "<data>" --aprovado-em "<data>"`**:
    - registra o relatório aprovado pelo usuário e congela a Coleta e o perfil atuais da usina;
    - grava numa pasta temporária, confere e só então troca a referência anterior (RT3);
    - no fim, sugere o commit.
  - **`python -m src comparar --todas`**:
    - para cada referência, refaz o Tratamento, a Conferência, as Análises e o Relatório num espaço isolado, sempre a partir da Coleta congelada e do perfil congelado, com a data de geração da referência;
    - compara o relatório refeito com o aprovado. `referencia.json`, `coleta/` e `perfil.toml` ficam fora da comparação;
    - avisa à parte, sem código 6, quando o perfil atual da usina difere do congelado;
    - não toca em `data/usinas/` nem em `reports/`, e o resultado não depende de `data/raw/` nem de outras usinas.
  - **`comparar --todas --coleta`**: além disso, refaz a Coleta da usina com `--sem-portal` e o perfil congelado, no espaço isolado, e a compara com a congelada:
    - as séries extraídas, linha a linha, só no período da referência;
    - as auditorias, só nas contagens por arquivo, sem as colunas de execução (como a data e a hora do processamento);
    - `dicionarios.csv` e `datas_obtencao.csv` aparecem como informação e não geram o código 6;
    - uma diferença por arquivo republicado pelo ONS aparece com o arquivo e a data de publicação, para o usuário decidir;
    - as etapas 2 a 5 continuam partindo da Coleta congelada.
  - **Regra para as fases**: `comparar --todas --coleta` no fim de toda fase (R27). Quando o formato da Coleta muda, a Coleta da referência é congelada de novo pelo `referencia`, depois do `comparar` com código 0.
  - **Ordem na fase A** (R27):
    1. referências, `comparar --todas [--coleta]`, Coleta no formato 2 e testes dos invariantes;
    2. migração: a São Domingos refeita com o código novo e `--sem-portal`, sobre os mesmos brutos de 08/10/2026; o `comparar` com `linha_de_base/` dá código 0; o `referencia` registra o relatório, a Coleta e o perfil, com a data "07/10/2026 08:53" e a aprovação de 08/10/2026. `linha_de_base/` continua na cópia de 08/10;
    3. P1 a P5, o registro e o perfil por tipo, cada um com `comparar --todas --coleta`;
    4. novo congelamento, se o formato da Coleta mudou;
    5. só então o primeiro `usinas` ou a primeira coleta de outra usina.
  - **Até o item 2 da fase A**: nenhuma coleta com o portal no projeto principal. A fiscalização usa a versão congelada da São Domingos, fora do projeto e com os próprios dados (FR-028); uma coleta feita nela não afeta o projeto. Se o projeto principal precisar de dados novos antes da migração, o relatório refeito passa pela aprovação do usuário e vira a referência (princípio IX).
- **Motivo**:
  - Princípio IX: referência guardada junto às cópias de segurança, comparação a cada fase e referência anterior no controle de versões.
  - RT5: cópias com os relatórios de referência.
  - FR-028, FR-029 e SC-001.
  - Princípio I: cada etapa lê só a anterior.
- **Alternativas rejeitadas**:
  - Referências só dentro das cópias: a anterior sairia na poda e não ficaria no git (o `.gitignore` exclui `_backup_*/` e `*.pdf`).
  - Refazer a Coleta a cada comparação: depende dos brutos compartilhados (B6).
  - Congelar os brutos: vários GB por usina.

### R23 — Uma usina fictícia por tipo (SC-005)

- **Decisão**: sete usinas fictícias em `tests/fixtures/usinas_ficticias/<tipo>/`, com brutos sintéticos no formato de cada conjunto (`tests/fixtures/brutos_ficticios.py`):

  | Tipo | O que exercita |
  |---|---|
  | UHE | a de hoje |
  | PCH | em conjunto, com mudança de composição e linhas próprias sem valor |
  | CGH | em conjunto, só o nível do conjunto |
  | UTE | duas unidades de planejamento, com troca de código; CVU com revisões; CMO; DISPF; sem geração num ano |
  | UTN | uma unidade; nuclear como térmica |
  | EOL | Tipo I; vento inválido; razão da restrição; série desde 10/2021 |
  | UFV | em conjunto; série curta; colunas ausentes no esquema antigo |

  - Cada uma roda `completo --sem-portal` sem rede. Na fase A, só com as seções comuns; cada fase completa a usina do seu tipo.
  - `tests/comum/test_literais.py` passa a procurar também os identificadores das usinas piloto no código.
- **Motivo**: SC-005 e constituição (Qualidade 1).
- **Alternativas rejeitadas**: recortes dos brutos reais nos testes. Poriam valores de usina real no código.

### R24 — Linha de comando e códigos de saída

- **Decisão**: os comandos novos reaproveitam os códigos 0 a 6 (contratos em [contracts/](contracts/)):

  | Comando | 0 | 1 | 2 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|
  | `usinas` | catálogo montado e listado | erro, inclusive o catálogo do ONS inacessível | opção inválida; Modalidade, Composição ou Capacidade não obtida | — | — | — |
  | `perfil` | rascunho criado, ou perfil igual ao catálogo | erro | opção inválida; CEG fora do catálogo; usina Tipo III ou só com agregado | — | catálogo ausente ou em formato antigo | perfil existente com diferenças (nada gravado) |
  | `carteira` | carteira gerada | erro | opção inválida, inclusive sem `--estado` nem `--tipo` | — | catálogo ausente, ou nenhuma usina do recorte com Análises concluídas | — |
  | `referencia` | referência registrada | erro; relatório gerado com outra data; falha na gravação ou na conferência | opção inválida | perfil inválido | relatório ou Coleta da usina ausente ou não concluída | — |
  | `comparar --todas` | nenhuma diferença | erro, inclusive sem referências ou com a Coleta congelada ausente | opção inválida | — | — | alguma diferença |
  | etapas | como hoje | | | também o perfil em rascunho | | |

- **Motivo**: os códigos de hoje já cobrem os casos. O fiscal e os testes leem um único significado por código.
- **Alternativas rejeitadas**: códigos novos (7 em diante). Não há caso que os de hoje não cubram.

### R25 — Ajustes na spec 006 feitos durante o plano

- **Decisão**: o rascunho da spec foi ajustado em 09/10/2026, e os ajustes foram aprovados pelo usuário no mesmo dia:
  - **FR-013**:
    - entram a restrição por constrained-off com a razão da restrição (R12) e a capacidade de geração por unidade geradora (R5);
    - CVU e CMO valem também para UTN (R28).
  - **FR-012**: a série de EVT vale para a UHE, a PCH ou a CGH que a tiver, como diz a FR-010 sobre os campos de UHE (R6).
  - **FR-018**: as comparações são sempre no mesmo nível, e entram a geração verificada do despacho × a da Geração por usina (G4) e a programação diária × a programada do fator de capacidade (G5) (R13).
  - **FR-022**: uma regra só é avaliada com dados do nível da usina (R16).
  - **FR-024**: a legenda identifica o nível pelo identificador citado (R15). Sem isso, a FR-024 contrariava a SC-001.
  - **FR-026**: a carteira sai por estado, por tipo ou pelos dois, como a constituição prevê (R21).
  - **Casos de borda**: quatro novos:
    - classificação ou identificador instável no ONS;
    - composição do conjunto que muda;
    - térmica com várias unidades de planejamento;
    - série de referência com menos de 12 meses.
  - **Assumptions**: o que o ONS publica de cada usina piloto, conferido em 09/10/2026.
- **Ajuste na constituição 3.0.0**, aprovado pelo usuário em 09/10/2026: no princípio VIII, a MMGD aparece como panorama agregado "do subsistema ou da área em que o ONS a publica". O ONS a publica em grupos por área do estado (A3), e a carteira de um estado usa esses grupos (R21).
- **Usina piloto solar**: a série da UFV Seriemas 1 é curta (A7). Por decisão do usuário (09/10/2026), ela continua como piloto de MS, e a EOL Praia Formosa cobre a série longa das renováveis. Uma UFV de série longa (fora de MS, Tipo II-B) pode ser acrescentada depois, sem mudar os requisitos.

### R26 — Spec de mudança e specs das etapas

- **Decisão**:
  - Os ajustes de cada spec de etapa são escritos em `specs/006-ampliacao-tipos-de-geracao/ajustes-specs/<NNN-etapa>.md`, já na redação final: requisitos, tabelas de aplicabilidade por tipo e decisões.
  - **Antes do código de cada fase**: os rascunhos da fase são escritos e aprovados pelo usuário. É a primeira tarefa da fase, e as demais dependem dela (Governança 2: a mudança começa pela spec).
  - No fechamento, os rascunhos são incorporados às specs 001 a 005 (`spec.md`, `plan.md`, `data-model.md` e contratos). O README passa a descrever todos os tipos, e a pasta da spec 006 é excluída (FR-030, SC-008).
  - As citações da spec 006 no código e nos testes (por exemplo, "spec 006, FR-0xx") são trocadas pelas FR das specs das etapas no fechamento.
  - As specs das etapas não são tocadas antes do fechamento, como na spec 009.
- **Motivo**:
  - Governança 2 da constituição e o padrão aprovado na spec 009.
  - Pedido do usuário: "rascunhos das alterações das specs das etapas dentro da pasta da spec, incorporados ao fim".
- **Alternativas rejeitadas**:
  - Alterar as specs das etapas a cada fase: misturaria texto aprovado e em construção.
  - Escrever os rascunhos junto com o código: o código viria antes da spec.

### R27 — Fases e pontos de controle

- **Decisão**: uma fase por história, na ordem da spec (FR-028), a partir da versão de fiscalização da São Domingos congelada e conferida (decisão do usuário de 09/10/2026):

  | Fase | História | Início | Fim |
  |---|---|---|---|
  | A | US1, fundação | cópia `antes_fase_A`; rascunhos das specs da fase aprovados | catálogo de MS e rascunho da William Arjona conferidos pelo usuário |
  | B | US2, térmicas | cópia `antes_fase_B`; rascunhos aprovados | relatório da William Arjona aprovado e registrado como referência |
  | C | US3, eólicas e solares | cópia `antes_fase_C`; rascunhos aprovados | Seriemas 1 e Praia Formosa aprovadas e registradas |
  | D | US4, PCH e CGH | cópia `antes_fase_D`; rascunhos aprovados | Bandeirante aprovada e registrada |
  | E | US5, carteira | cópia `antes_fase_E`; rascunhos aprovados | carteira de MS aprovada |
  | F | fechamento | cópia `antes_fechamento` | rascunhos incorporados às specs 001 a 005; README; pasta 006 excluída com aprovação; SC-008 |

  - **Fim de toda fase**, além do ponto de controle da tabela: a suíte; a análise estática (`pyflakes`, rodado de fora do `venv`, como hoje, sem entrar no `requirements.txt`); `/speckit-converge`; e `comparar --todas --coleta` com código 0.
  - **Na fase A**, a ordem interna segue a R22, e o `comparar --todas --coleta` roda depois de cada item. O primeiro `usinas` e a primeira coleta de outra usina só vêm depois do congelamento.
  - Em toda fase, uma diferença no relatório de uma usina já aprovada só é aceita com a aprovação do usuário.
- **Motivo**: FR-028 e princípio IX.
- **Alternativas rejeitadas**: entregar tudo de uma vez. Sem ponto de controle, uma diferença na São Domingos seria difícil de isolar.

### R28 — Outros casos

- **UTN**: segue as seções e regras de térmica, com o combustível "nuclear". CVU, CMO, DISPF e TEIFa entram quando o ONS os publica para a usina.
- **Usina com intervalo longo sem dados** (como a William Arjona de 08/2018 a 07/2021 no despacho): o intervalo é listado nas ausências (princípio IV), nunca preenchido.
- **Desempenho (SC-006)**: as leituras são em Parquet, com filtro e só o período da usina. A série de referência inteira é o que mais pesa: 0,73 GB na geração por usina; menos na restrição. A meta de 15 minutos é conferida nas pilotos, no `etapa.json`.

### R29 — Invariantes do relatório das hidrelétricas com EVT

- **Decisão**: cada item abaixo tem um teste de regressão próprio, além do `comparar --todas`. Valem para o relatório e a planilha da UHE e das demais hidrelétricas com EVT:

  | Invariante | Como se mantém |
  |---|---|
  | Seções, títulos, ordem e numeração | o caminho de hoje (R14) |
  | Capa e título | sem linha nova; a modalidade já vem da ficha do cadastro (B7) |
  | Legendas | identificador da usina, como hoje (R15); datas de obtenção e contagem de arquivos lidas da Coleta, iguais às de hoje (R22) |
  | Conferências | no relatório e na planilha, as de hoje, sem G1 a G5; a do cadastro sem a modalidade. As não aplicáveis ficam só em `nao_aplicaveis.csv`, que o relatório não lê (R13) |
  | Conclusão | C1 a C11 com a mesma ordem, texto, limiares e listas, sem período mínimo novo; nota da conclusão com o texto de hoje (R16, R17) |
  | Trechos | não calculados nem mostrados (R7) |
  | Planilha | as mesmas abas e colunas; DICIONARIOS com os dez conjuntos de hoje; auditorias sem colunas novas (R8) |
  | Notas | sem o parágrafo de granularidade (R15) |
  | Coleta | os arquivos de hoje com as mesmas colunas, mais `datas_obtencao.csv` e `dicionario_evt.json` (R8, R22) |

- **Motivo**: SC-001 e princípio IX. Um teste por invariante aponta a causa de uma diferença antes do `comparar`.
- **Alternativas rejeitadas**: confiar só no `comparar`. Ele mostra que algo mudou, mas não por quê.

### R30 — Base horária comum dos tipos sem EVT

- **Decisão**:
  - Nas usinas sem EVT, o Tratamento grava `base_horaria.csv`, a base das seções comuns (R14) e das regras comuns (R16). Cada hora traz:
    - a geração da série de referência tratada (a da usina, ou a do conjunto, com o nível);
    - a disponibilidade operacional e a sincronizada, quando há cobertura;
    - a geração programada, quando há;
    - o trecho e as sinalizações.
  - **Base das regras comuns**: a regra de qualidade "geração acima da disponibilidade declarada" (base da C8) e os eventos de indisponibilidade total (base da C10) são calculados sobre ela.
  - **Análises**: os campos de EVT de `ResultadosAnalise` ficam vazios nas usinas sem EVT. O caminho das hidrelétricas com EVT não muda.
- **Motivo**: B4. As Análises de hoje partem da base de EVT, que os outros tipos não têm.
- **Alternativas rejeitadas**: simular uma base de EVT com colunas vazias. Esconderia o tipo da usina nas Análises e arriscaria textos de UHE em outros tipos.
