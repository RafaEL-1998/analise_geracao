# Data Model: Conferência

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-23

## 1. Entradas

A etapa só lê arquivos locais. Caminhos relativos a `data/usinas/<slug>/`, exceto o perfil. O caminho da usina sai da
série de referência (plano, decisão técnica D12): **com EVT** (hidrelétrica com série própria na Energia Vertida
Turbinável) ou **sem EVT** (as demais).

| Arquivo | Gravado por | Lido por | Caminho | Conferência | Colunas ou campos usados |
|---|---|---|---|---|---|
| `tratamento/etapa.json` | Tratamento de dados | `src/pipeline.etapa_anterior_concluida` | os dois | pré-requisito | `status` = `concluida` e `versao_formato` = 2; `concluida_em` vai para `etapa_anterior` |
| `tratamento/evt_tratado.parquet` | Tratamento | `etapa.conferir` (só `COLUNAS_EVT`) | com EVT | geração, disponibilidade, vazões | `din_instante`, `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida` |
| `tratamento/geracao_horaria.csv` | Tratamento | `carregar_geracao_tratada` | com EVT; sem EVT, quando a série de referência é a restrição com detalhe | geração; G1 e G2 | `din_instante`, `val_geracao`, `qualidade` (`OK` ou `G1`) |
| `tratamento/disponibilidade_horaria.csv` | Tratamento | `carregar_disponibilidade_tratada` | com EVT | disponibilidade | `din_instante`, `val_dispoperacional`, `qualidade` (`OK` ou as regras D1 a D4) |
| `tratamento/hidrologia_horaria.csv` | Tratamento | `carregar_hidrologia_tratada` | os dois | vazões; alinhamento da hidrologia | `din_instante` (já na hora de início), `val_vazaoturbinada`, `val_vazaovertida` |
| `tratamento/indicadores_ug_mensal.csv` | Tratamento | `carregar_indicadores_tratados` (`ug_mensal`) | os dois | DISPF × horas | `mes`, `ug`, `indisppf`, `indispff` (% do mês) |
| `tratamento/horas_estado_mensal.csv` | Tratamento | idem (`horas_estado`) | os dois | DISPF × horas; TEIFa e TEIP | `mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HEDP`, `HEDF`, `potencia_mw` |
| `tratamento/teifa_teip_mensal.csv` | Tratamento | idem (`taxas`) | os dois | TEIFa e TEIP | `mes`, `teifa`, `teip` (frações de 0 a 1) |
| `tratamento/indicadores_ug_anual.csv` | Tratamento | idem (`ug_anual`) | os dois | nenhuma | o leitor exige o arquivo, mas a Conferência não usa a tabela |
| `tratamento/base_horaria.csv` | Tratamento | `carregar_base_horaria` | sem EVT | G4; alinhamento da hidrologia; G1 e G2, quando a série de referência é a Geração por usina | `din_instante`, `geracao_mw`, `nivel` (`usina` ou `conjunto`) |
| `tratamento/programacao_horaria.csv` | Tratamento | `carregar_programacao_tratada` | sem EVT | G3, G5 | `din_instante`, `geracao_programada_mw` (média horária dos patamares, já somados os códigos) |
| `tratamento/despacho_horario.csv` | Tratamento | `carregar_despacho_tratado` | sem EVT | G3, G4 | `din_instante`, `val_proggeracao`, `val_verifgeracao` (soma das unidades de planejamento) |
| `tratamento/fator_capacidade_horario.csv` | Tratamento | `carregar_renovavel` | sem EVT | G1, G5 | `din_instante`, `val_geracaoverificada`, `val_geracaoprogramada`, `nivel` |
| `tratamento/restricao_horaria.csv` | Tratamento | idem | sem EVT | G1, G2 | `din_instante`, `val_geracaoverificada` (média das duas meias-horas; da usina) |
| `tratamento/restricao_razao_semi_horaria.csv` | Tratamento | idem | sem EVT | G1 | `din_instante`, `val_geracao`, `nivel` (semi-horária; levada à hora pela Conferência) |
| `tratamento/restricao_membros_horaria.csv` | Tratamento | idem | sem EVT | G2 | `din_instante`, `id_ons`, `val_geracaoverificada` (as outras usinas do conjunto, em hora cheia) |
| `coleta/cadastro_ficha.csv` | Coleta de dados | `etapa.carregar_ficha_cadastro` | os dois | cadastro | primeira linha: `val_potenciaautorizada`, `id_estado`, `id_ons`, `linhas_ceg` |
| `usinas/<slug>/perfil.toml` | fiscal | `carregar_perfil`, na linha de comando | os dois | catálogo; cadastro; G2; pastas | `usina.slug`, `usina.tipo` (sem ele, o prefixo do CEG), `[cobertura]`, `parametros.potencia_instalada_mw` (por `Perfil.potencia_autorizada_esperada_mw`), `usina.estado`, `identificacao.id_ons`, `identificacao.id_conjunto` e `[[identificacao.membros]]` (`id_ons`, `inicio`, `fim`) |

- **Leitores do Tratamento**: as séries são lidas como `SerieConjunto` (`horaria`, `ausencias`, `auditoria`), com
  `din_instante` convertido em data e hora; `<conjunto>_ausencias.csv` e `auditoria_<conjunto>.csv` também são lidos,
  quando existem, mas a Conferência só usa `horaria`. Os indicadores são lidos como `IndicadoresONS`. Os leitores da
  programação, do despacho e das renováveis leem também `programacao_dias_ausentes.csv`,
  `despacho_unidades_horario.csv`, `despacho_ausencias.csv`, `restricao_semi_horaria.csv` e `restricao_ausencias.csv`,
  sem uso nas conferências.
- **Arquivo ausente**: série, base horária, programação, despacho ou tabela das renováveis → `None`; indicadores → `None`
  quando falta qualquer um dos quatro CSV; ficha ausente ou sem linhas → tabela vazia. Em todos os casos a conferência
  correspondente fica não aplicável (seção 5.2). Sem `evt_tratado.parquet`, a hidrelétrica com EVT termina com código 1.
- **Ficha do cadastro**: lida com `keep_default_na=False`, de modo que um campo vazio continua texto vazio. A Coleta já
  reduz a ficha à primeira linha com o CEG do perfil e conta em `linhas_ceg` as linhas com esse CEG.
- **Correções da Coleta que chegam aqui**: a vírgula decimal é aceita em todos os conjuntos, inclusive na potência da
  ficha (FR-039 da spec da Coleta de dados), e a coluna de conferência ausente torna o arquivo `FALHA`, com o motivo
  (FR-036 da spec da Coleta de dados).
- **Conjuntos e níveis da usina**: a Conferência não lê arquivos da Coleta para isso. O registro dos conjuntos
  (`src/coleta/registro.py`, FR-049 da spec da Coleta de dados) diz, a partir do tipo e da `[cobertura]` do perfil, que
  conjuntos a Coleta obtém para a usina e em que nível (`usina` ou `conjunto`).
- O formato completo desses arquivos está no [data model do Tratamento](../002-tratamento-dados/data-model.md) e no
  [da Coleta](../001-coleta-dados/data-model.md).

## 2. Saídas

Pasta: `data/usinas/<slug>/conferencia/`. Os CSV são gravados por `gravar_csv`: separador `;`, UTF-8, cabeçalho, sem
índice, datas `AAAA-MM-DD HH:MM:SS`, ponto decimal, lógicos como `True`/`False` e campo vazio para valor ausente. Nenhum
arquivo tem `.bak`; um arquivo de conteúdo idêntico ao novo não é regravado.

| Arquivo | Conferência e tabela (`CSV_CONFERENCIA`) | Gravado quando |
|---|---|---|
| `conferencias.pkl` | os resultados (seção 2.1) | sempre que a etapa roda |
| `geracao.csv` | `geracao` → `mensal` | geração aplicável |
| `geracao_divergencias.csv` | `geracao` → `divergencias` | geração aplicável; só o cabeçalho sem divergência |
| `disponibilidade.csv` | `disponibilidade` → `resumo` (uma linha) | disponibilidade aplicável |
| `disponibilidade_divergencias.csv` | `disponibilidade` → `divergencias` | disponibilidade aplicável; só o cabeçalho sem divergência |
| `vazoes.csv` | `vazoes` → `alinhamento` | vazões aplicáveis |
| `dispf_horas.csv` | `dispf_horas` → `divergencias` | DISPF × horas aplicável; só o cabeçalho sem divergência |
| `teifa_teip.csv` | `teifa_teip` → `recalculo` | com EVT: horas e taxas presentes, mesmo sem mês de janela completa; sem EVT: TEIFa e TEIP aplicada |
| `cadastro.csv` | `cadastro` → `campos` | cadastro aplicável |
| `programacao_despacho.csv` | `programacao_despacho` (G3) → `mensal` | G3 aplicada |
| `verificada_despacho.csv` | `verificada_despacho` (G4) → `mensal` | G4 aplicada |
| `geracao_fontes.csv` | `geracao_fontes` (G1) → `mensal` | G1 aplicada |
| `soma_conjunto.csv` | `soma_conjunto` (G2) → `mensal` | G2 aplicada |
| `programacao_renovaveis.csv` | `programacao_renovaveis` (G5) → `mensal` | G5 aplicada |
| `alinhamento_hidrologia.csv` | `alinhamento_hidrologia` → `deslocamentos` | alinhamento da hidrologia aplicado |
| `nao_aplicaveis.csv` | catálogo (seção 2.12) | sempre que a etapa roda |
| `etapa.json` | manifesto (seção 4) | sempre que a etapa passa do pré-requisito |

Os CSV são gravados nesta ordem, depois de `conferencias.pkl`; `nao_aplicaveis.csv` é o último. Quando a tabela não
existe nesta execução, o CSV que sobrou de uma execução anterior é apagado (seção 5.7). Nas usinas sem EVT, a conferência
não aplicada não está em `conferencias.pkl` e não grava CSV.

### 2.1 `conferencias.pkl`

Pickle (`pickle.HIGHEST_PROTOCOL`) de um dicionário `{"versao_formato": 1, "resultados": {<id>: ResultadoConferencia}}`.
O objeto está na seção 3.
- **Com EVT**: os seis ids da FR-002, na ordem `geracao`, `disponibilidade`, `vazoes`, `dispf_horas`, `teifa_teip`,
  `cadastro`, aplicáveis ou não. Na São Domingos: 17.358 bytes.
- **Sem EVT**: só os resultados aplicáveis das conferências aplicáveis à usina, na ordem do catálogo (seção 3.7).

### 2.2 `geracao.csv` — uma linha por mês

| Coluna | Tipo | Descrição |
|---|---|---|
| `mes` | texto `AAAA-MM` | mês com horas comparadas ou presentes em só uma fonte |
| `energia_base_evt_mwh` | real | soma de `val_geracao` da base de EVT no mês, dentro do intervalo da conferência (MWh) |
| `energia_ons_geracao_mwh` | real | soma de `val_geracao` válida de Geração por usina no mês (MWh) |
| `diferenca_mwh` | real | `energia_ons_geracao_mwh` − `energia_base_evt_mwh` |
| `horas_so_base_evt` | inteiro | horas com geração só na base de EVT |
| `horas_so_ons_geracao` | inteiro | horas com geração válida só em Geração por usina |

Na São Domingos: 98 linhas (2018-08 a 2026-09).

### 2.3 `geracao_divergencias.csv` e `disponibilidade_divergencias.csv` — um período contínuo de horas divergentes por linha

| Coluna | Tipo | Descrição |
|---|---|---|
| `inicio` | data e hora | primeira hora do período (hora de início) |
| `fim` | data e hora | última hora do período |
| `horas` | inteiro | horas do período, consecutivas com passo de 1 h |
| `diferenca_media_mw` | real | média da diferença absoluta entre as fontes (MW) |
| `diferenca_maxima_mw` | real | maior diferença absoluta (MW) |

Montados por `src/comum/periodos.periodos_continuos`. Na São Domingos, os dois têm só o cabeçalho. As tabelas
`divergencias` de G1 a G5 (seção 3.3) têm as mesmas colunas.

### 2.4 `disponibilidade.csv` — uma linha

| Coluna | Tipo | Descrição |
|---|---|---|
| `horas_comuns` | inteiro | horas com `val_dispoperacional` válida e `val_disponibilidade` da base de EVT |
| `coincidentes` | inteiro | horas comuns com diferença absoluta de até 0,01 MW |
| `divergentes` | inteiro | horas comuns com diferença acima de 0,01 MW |
| `pct_coincidentes` | real | `coincidentes` ÷ `horas_comuns` × 100; vazio sem hora comum |
| `so_ons_disponibilidade` | inteiro | horas válidas de Disponibilidade por usina sem a declarada na base de EVT |
| `so_base_evt` | inteiro | horas da base de EVT, entre a primeira e a última hora válida de Disponibilidade por usina, que faltam nela (a hora sinalizada não conta aqui) |
| `horas_sinalizadas_excluidas` | inteiro | horas de Disponibilidade por usina com `qualidade` diferente de `OK` |
| `tolerancia_mw` | real | 0,01 |

### 2.5 `vazoes.csv` — uma linha

| Coluna | Tipo | Descrição |
|---|---|---|
| `horas_comuns` | inteiro | horas com turbinada e vertida nas duas fontes |
| `coincidentes_turbinada` | inteiro | horas comuns com a turbinada a até 0,5 m³/s |
| `coincidentes_vertida` | inteiro | horas comuns com a vertida a até 0,5 m³/s |
| `coincidentes_ambas` | inteiro | horas comuns com as duas coincidentes |
| `pct_coincidencia` | real | `coincidentes_ambas` ÷ `horas_comuns` × 100; vazio sem hora comum |
| `meta_pct` | real | 99,0 |
| `tolerancia_m3s` | real | 0,5 |
| `deslocamento_aplicado_h` | inteiro | −1: conversão da hora de fim para a de início, feita pelo Tratamento |
| `confirmado` | lógico | meta atingida: `pct_coincidencia` ≥ `meta_pct` e ao menos uma hora comum |

### 2.6 `dispf_horas.csv` — um mês-unidade divergente por linha

| Coluna | Tipo | Descrição |
|---|---|---|
| `mes` | data | mês (dia 1, 00:00) |
| `ug` | inteiro ou texto | unidade geradora, como no Tratamento (o rótulo publicado; texto quando algum rótulo da usina tem letra) |
| `HP` | real | horas do período (nas térmicas, com as horas equivalentes, como o ONS publica) |
| `HS` | real | horas em serviço |
| `HRD` | real | horas em reserva desligada |
| `HDP` | real | horas de desligamento programado |
| `horas_programadas_indisppf` | real | INDISPPF × HP ÷ 100 |
| `HDF` | real | horas de desligamento forçado |
| `horas_forcadas_indispff` | real | INDISPFF × HP ÷ 100 |
| `diferenca_programada_h` | real | `horas_programadas_indisppf` − `HDP` |
| `diferenca_forcada_h` | real | `horas_forcadas_indispff` − `HDF` |

O mês-unidade sem algum dos valores comparados não entra na lista: é contado em `tabelas["sem_valor"]` (seção 3.3). Na
São Domingos: 4 linhas, de 160 meses-unidade comparados, nenhum sem valor.

### 2.7 `teifa_teip.csv` — uma linha por mês publicado no período

| Coluna | Tipo | Descrição |
|---|---|---|
| `mes` | data | mês da taxa (dia 1, 00:00) |
| `meses_na_janela` | inteiro | meses distintos com horas na janela de 60 meses que termina no mês |
| `teifa_publicada` | real | fração de 0 a 1 |
| `teifa_recalculada` | real | fração; vazia sem janela completa |
| `teip_publicada` | real | fração de 0 a 1 |
| `teip_recalculada` | real | fração; vazia sem janela completa |
| `diferenca_teifa_pp` | real | (recalculada − publicada) × 100, em p.p.; vazia sem janela completa |
| `diferenca_teip_pp` | real | idem para a TEIP |

Um mês de janela completa sem alguma das quatro taxas fica na tabela, com o valor vazio, e é contado em
`tabelas["sem_valor"]`. Na São Domingos: 61 linhas (08/2021 a 08/2026), 21 delas com janela completa (12/2024 a
08/2026), todas com as quatro taxas.

### 2.8 `cadastro.csv` — um campo conferido por linha (quatro linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `campo` | texto | `potência autorizada (MW)`, `estado`, `id ONS` ou `linhas com o CEG` |
| `valor_cadastro` | conforme o campo | valor da ficha; na potência, vazio quando falta ou não é numérico |
| `valor_perfil` | conforme o campo | `potencia_autorizada_esperada_mw`, `usina.estado`, `identificacao.id_ons` (vazio quando o perfil não o tem) ou 1 |
| `situacao` | texto | `CONFERE` ou `DIVERGE` |
| `texto` | texto | frase do campo, usada quando ele diverge (seção 5.4) |

### 2.9 `programacao_despacho.csv`, `verificada_despacho.csv`, `soma_conjunto.csv` e `programacao_renovaveis.csv` — uma linha por mês

Tabela mensal das conferências entre fontes, montada por `fontes.conferir_series` com as duas séries horárias da
conferência, a primeira (`a`) e a segunda (`b`):

| Arquivo | Fonte `a` | Fonte `b` |
|---|---|---|
| `programacao_despacho.csv` (G3) | Programação diária (`geracao_programada_mw`) | despacho, geração programada (`val_proggeracao`) |
| `verificada_despacho.csv` (G4) | despacho, geração verificada (`val_verifgeracao`) | Geração por usina da base horária, nível `usina` (`geracao_mw`) |
| `soma_conjunto.csv` (G2) | soma das usinas do conjunto (restrição com detalhe) | Geração por usina do conjunto |
| `programacao_renovaveis.csv` (G5) | Programação diária (`geracao_programada_mw`) | Fator de capacidade, geração programada (`val_geracaoprogramada`) |

| Coluna | Tipo | Descrição |
|---|---|---|
| `mes` | texto `AAAA-MM` | mês com horas comuns ou com valor só numa fonte |
| `energia_a_mwh` | real | soma da fonte `a` nas horas comuns do mês (MWh) |
| `energia_b_mwh` | real | soma da fonte `b` nas horas comuns do mês (MWh) |
| `diferenca_mwh` | real | `energia_a_mwh` − `energia_b_mwh` |
| `horas_comuns` | inteiro | horas com valor nas duas fontes |
| `horas_divergentes` | inteiro | horas comuns com diferença acima de 0,01 MW |
| `horas_so_a` | inteiro | horas com valor só na fonte `a` |
| `horas_so_b` | inteiro | horas com valor só na fonte `b` |

### 2.10 `geracao_fontes.csv` (G1) — uma linha por par de fontes, nível e mês

As colunas `fonte_a`, `fonte_b` e `nivel`, seguidas das colunas da seção 2.9.

| Coluna | Tipo | Descrição |
|---|---|---|
| `fonte_a` | texto | `Geração por usina`, `Fator de capacidade`, `Restrição com detalhe` ou `Restrição com a razão`: a que vem antes nessa ordem |
| `fonte_b` | texto | a outra fonte do par |
| `nivel` | texto | `usina` ou `conjunto`: o nível comum às duas fontes |

### 2.11 `alinhamento_hidrologia.csv` — uma linha por deslocamento (três linhas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `deslocamento_h` | inteiro | −1, 0 ou +1: a hidrologia (já na hora de início) deslocada dessa quantidade de horas |
| `horas_comuns` | inteiro | horas com a geração da usina e a vazão turbinada, com o deslocamento |
| `correlacao` | real | correlação de Pearson entre a geração e a vazão turbinada; vazia com menos de duas horas ou série constante |

### 2.12 `nao_aplicaveis.csv` — uma conferência não aplicável por linha

| Coluna | Tipo | Descrição |
|---|---|---|
| `conferencia` | texto | id da conferência (seção 3.7) |
| `motivo` | texto | motivo do catálogo ou do resultado sem base (seção 5.2) |

- As linhas seguem a ordem do catálogo. Entram as conferências que não se aplicam pelo catálogo e as que rodaram e
  ficaram não aplicáveis, com o motivo do resultado.
- O alinhamento da hidrologia pela geração só ganha linha nas hidrelétricas (`registrada_so_nos_tipos`).
- Na São Domingos: 6 linhas (`geracao_fontes`, `soma_conjunto`, `programacao_despacho`, `verificada_despacho`,
  `programacao_renovaveis` e `alinhamento_hidrologia`).
- Leitura: só as Análises, nas usinas sem EVT, para as notas do relatório (`res.comum["conferencias_nao_aplicaveis"]`,
  aba CONF_NAO_APLICAVEIS). Nenhum módulo do relatório lê o arquivo.

## 3. Objetos em memória e entre etapas

### 3.1 `ResultadoConferencia` (`src/conferencia/resultado.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `id` | `str` | um dos doze de `CONFERENCIAS`: `geracao`, `disponibilidade`, `vazoes`, `dispf_horas`, `teifa_teip`, `cadastro`, `programacao_despacho`, `verificada_despacho`, `geracao_fontes`, `soma_conjunto`, `programacao_renovaveis`, `alinhamento_hidrologia` |
| `bases` | `Tuple[str, str]` | as duas bases comparadas (seção 3.2) |
| `unidade` | `str` | `horas`, `meses-unidade`, `meses` ou `campos` |
| `aplicavel` | `bool` | padrão `True` |
| `motivo` | `str` | vazio quando aplicável (seção 5.2) |
| `periodo` | `Tuple[Timestamp, Timestamp]` ou `None` | primeira e última hora, ou primeiro e último mês, comparados; `None` no cadastro, no alinhamento da hidrologia, quando nada é comparado e quando não aplicável |
| `comparados`, `coincidentes`, `divergentes` | `int` | quantidades na unidade da conferência; 0 quando não aplicável |
| `tolerancia` | `float` ou `None` | critério de coincidência (seção 5.1); preenchido também quando não aplicável; `None` no alinhamento da hidrologia |
| `meta` | `float` ou `None` | 99,0 nas vazões, inclusive quando não aplicáveis; `None` nas demais |
| `meta_atingida` | `bool` ou `None` | só nas vazões aplicáveis |
| `tabelas` | `Dict[str, Any]` | tabelas de detalhe (seção 3.3) |

- `resumo()` devolve a situação para o `etapa.json` (seção 4).
- `nao_aplicavel(id, bases, unidade, motivo, tabelas=None, **campos)` monta o resultado não aplicável.
- `__post_init__` valida as invariantes da seção 5.5.
- No mesmo módulo, `diferenca_absoluta(diferenca)` devolve a diferença absoluta arredondada a `CASAS_COMPARACAO` (9)
  casas, para número, série ou tabela; é a base de toda comparação com tolerância (seção 5.1).

### 3.2 Bases, unidade e período de cada conferência

| `id` | `bases` (constantes `BASES`, `BASES_DISPF`, `BASES_TAXAS`, `BASES_G1` a `BASES_G5`, `BASES_ALINHAMENTO`) | `unidade` | `periodo` |
|---|---|---|---|
| `geracao` | `base de EVT (val_geracao)`; `Geração por usina (val_geracao)` | `horas` | primeira e última hora comum |
| `disponibilidade` | `base de EVT (val_disponibilidade)`; `Disponibilidade por usina (val_dispoperacional)` | `horas` | primeira e última hora comum |
| `vazoes` | `base de EVT (val_vazaoturbinada, val_vazaovertida)`; `Dados hidrológicos horários (mesmas vazões)` | `horas` | primeira e última hora comum |
| `dispf_horas` | `Indicadores por unidade geradora, base mensal (INDISPPF e INDISPFF)`; `Parâmetros das taxas TEIFa e TEIP (HDP e HDF)` | `meses-unidade` | primeiro e último mês dos meses-unidade comparados |
| `teifa_teip` | `TEIFa e TEIP recalculadas a partir das horas por estado operativo`; `Taxas TEIFa e TEIP publicadas` | `meses` | primeiro e último mês comparado (janela completa e as quatro taxas) |
| `cadastro` | `Modalidade das usinas (ficha da usina)`; `perfil da usina` | `campos` | `None` |
| `programacao_despacho` | `Programação diária (média horária dos patamares)`; `Geração térmica por motivo de despacho (val_proggeracao)` | `horas` | primeira e última hora comum |
| `verificada_despacho` | `Geração térmica por motivo de despacho (val_verifgeracao)`; `Geração por usina (val_geracao)` | `horas` | primeira e última hora comum |
| `geracao_fontes` | `Geração da usina em cada fonte (Geração por usina, Fator de capacidade e restrições)`; `a mesma geração em outra fonte, no mesmo nível` | `horas` | primeira e última hora comum de todos os pares |
| `soma_conjunto` | `Soma das usinas do conjunto (restrição com detalhe, média horária)`; `Geração por usina do conjunto` | `horas` | primeira e última hora comum |
| `programacao_renovaveis` | `Programação diária (média horária dos patamares)`; `Fator de capacidade (val_geracaoprogramada)` | `horas` | primeira e última hora comum |
| `alinhamento_hidrologia` | `Dados hidrológicos horários (val_vazaoturbinada)`; `Geração por usina (geração da usina)` | `horas` | `None` |

### 3.3 `tabelas` de cada conferência

| `id` | Chave | Tipo | Conteúdo | Uso nas etapas seguintes |
|---|---|---|---|---|
| `geracao` | `resumo` | `dict` | `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes`, `so_ons_geracao`, `so_base_evt`, `energia_ons_geracao_mwh`, `energia_base_evt_mwh`, `tolerancia_mw` | `res.geracao_oficial["conferencia"]`; aba GER_CONFERENCIA; legendas |
| | `mensal` | `DataFrame` | = `geracao.csv` | `res.geracao_oficial["mensal"]` (e o resumo anual das Análises); aba GER_MENSAL |
| | `divergencias` | `DataFrame` | = `geracao_divergencias.csv` | aba GER_DIVERGENCIAS |
| `disponibilidade` | `resumo` | `dict` | = `disponibilidade.csv` | `res.disponibilidade["conferencia"]`; aba DISP_CONFERENCIA; legendas |
| | `divergencias` | `DataFrame` | = `disponibilidade_divergencias.csv` | aba DISP_DIVERGENCIAS |
| `vazoes` | `alinhamento` | `DataFrame` (uma linha) | = `vazoes.csv` | `res.hidrologia["alinhamento"]` e `["publicado"]` (= `confirmado`); aba HID_ALINHAMENTO; legendas |
| `dispf_horas` | `divergencias` | `DataFrame` | = `dispf_horas.csv` | `IndicadoresONS.divergencias` → `res.ons["divergencias"]`; aba ONS_DIVERGENCIAS; legendas |
| | `sem_valor` | `int` | meses-unidade presentes nas duas bases sem algum dos valores de `VALORES_DISPF` | nenhum |
| `teifa_teip` | `recalculo` | `DataFrame` | = `teifa_teip.csv` | `res.ons["recalculo_taxas"]`; aba ONS_TEIFA_TEIP |
| | `diferenca_maxima_pp` | `float` | maior diferença absoluta (p.p.) dos meses comparados; vazia (NaN) sem mês comparado; só quando aplicável | com `comparados` e `coincidentes`, vai para `res.ons["recalculo_resumo"]` (`meses`, `reproduzidos`, `diferenca_maxima_pp`): constatação e legendas |
| | `sem_valor` | `int` | meses de janela completa sem alguma das taxas de `VALORES_TAXAS`; só quando aplicável | nenhum |
| `cadastro` | `campos` | `DataFrame` | = `cadastro.csv` | nenhum |
| | `divergencias` | `str` | textos dos campos divergentes, unidos por `"; "`; vazio sem divergência | coluna `divergencias` da ficha e `res.cadastro["divergencias"]`; aba CAD_FICHA; legendas |
| `programacao_despacho`, `verificada_despacho` (G3, G4) | `resumo` | `dict` | `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes` (NaN sem hora comum), `so_a`, `so_b`, `energia_a_mwh`, `energia_b_mwh`, `tolerancia_mw`; na G4, também `pct_coincidentes_deslocada` (`{"+1 h": …, "-1 h": …}`, `None` sem hora comum) | `res.termica["conferencias"][id]` (com os campos do `resumo`); legendas e resumo executivo |
| | `mensal` | `DataFrame` | = `programacao_despacho.csv` ou `verificada_despacho.csv` | abas CONF_G3_MENSAL e CONF_G4_MENSAL |
| | `divergencias` | `DataFrame` | períodos contínuos (colunas da seção 2.3) | abas CONF_G3_DIVERGENCIAS e CONF_G4_DIVERGENCIAS |
| `soma_conjunto`, `programacao_renovaveis` (G2, G5) | `resumo` | `dict` | como na G3; na G2, também `horas_incompletas` (horas com alguma usina vigente sem valor, fora da soma) | `res.renovavel["conferencias"][id]`; legendas |
| | `mensal` | `DataFrame` | = `soma_conjunto.csv` ou `programacao_renovaveis.csv` | abas CONF_G2_MENSAL e CONF_G5_MENSAL |
| | `divergencias` | `DataFrame` | períodos contínuos | abas CONF_G2_DIVERGENCIAS e CONF_G5_DIVERGENCIAS |
| `geracao_fontes` (G1) | `pares` | `DataFrame` | um par de fontes e nível por linha: `fonte_a`, `fonte_b`, `nivel`, `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes`, `so_a`, `so_b`, `energia_a_mwh`, `energia_b_mwh` | `res.renovavel["conferencias"]["geracao_fontes"]`; aba CONF_G1_PARES; legendas (quantidade de pares) |
| | `mensal` | `DataFrame` | = `geracao_fontes.csv` | aba CONF_G1_MENSAL |
| | `divergencias` | `DataFrame` | períodos contínuos, com `fonte_a`, `fonte_b` e `nivel` | aba CONF_G1_DIVERGENCIAS |
| `alinhamento_hidrologia` | `alinhamento` | `DataFrame` (uma linha) | `horas_comuns` (sem deslocamento), `correlacao_0h`, `correlacao_menos_1h`, `correlacao_mais_1h`, `deslocamento_aplicado_h` (−1, do Tratamento), `confirmado` | `res.hidrologia["alinhamento"]` e `["publicado"]` (= `confirmado`), na hidrelétrica sem EVT; aba HID_ALINHAMENTO; legendas |
| | `deslocamentos` | `DataFrame` | = `alinhamento_hidrologia.csv` | nenhum |

Resultado não aplicável: `tabelas` vazio, exceto a TEIFa e a TEIP sem mês de janela completa, que guardam `recalculo`, e
G1 a G5 sem hora comum, que guardam o `resumo` (G2 a G5) ou os `pares` (G1). Nas usinas sem EVT, o resultado não
aplicável não vai para `conferencias.pkl`.

### 3.4 Números citados nas legendas (FR-005)

| Conferência | Número | Campo |
|---|---|---|
| geração e disponibilidade | horas coincidentes, comuns e divergentes; percentual; horas só numa fonte | `coincidentes`, `comparados`, `divergentes`; em `tabelas["resumo"]`: `pct_coincidentes`, `so_ons_geracao` ou `so_ons_disponibilidade`, e `so_base_evt` |
| vazões | horas coincidentes nas duas vazões, comuns, percentual e meta | `tabelas["alinhamento"]`: `coincidentes_ambas`, `horas_comuns`, `pct_coincidencia`, `meta_pct`, `confirmado` |
| DISPF × horas | meses-unidade divergentes | `divergentes`; `tabelas["divergencias"]` |
| TEIFa e TEIP | meses comparados e reproduzidos; maior diferença | `comparados`, `coincidentes`; `tabelas["diferenca_maxima_pp"]` (levados pelas Análises em `recalculo_resumo`) |
| cadastro | texto de cada divergência | `tabelas["divergencias"]` |
| G2, G3, G4 e G5 | horas coincidentes, comuns e divergentes; percentual; horas só numa fonte; na G2, horas fora da soma | `coincidentes`, `comparados`, `divergentes`; em `tabelas["resumo"]`: `pct_coincidentes`, `so_a`, `so_b`, `horas_incompletas` |
| G1 | horas coincidentes e comparadas no total; percentual; divergentes; quantidade de pares | `coincidentes`, `comparados`, `divergentes`; linhas de `tabelas["pares"]` |
| alinhamento da hidrologia | horas comuns; correlação de cada deslocamento; confirmado | `tabelas["alinhamento"]`: `horas_comuns`, `correlacao_0h`, `correlacao_menos_1h`, `correlacao_mais_1h`, `confirmado` |
| não aplicável | motivo | `motivo`; nas usinas sem EVT, `nao_aplicaveis.csv` |

### 3.5 `conferencias.pkl` entre as etapas

- **Gravação**: `salvar_conferencias(resultados, destino)`, por `gravar_bytes(..., copia=False)`.
- **Leitura**: só pelas Análises (`src/analises/etapa.carregar_entradas` → `carregar_conferencias`). Uma versão diferente
  de `VERSAO_FORMATO` levanta `ValueError` com `<arquivo>: formato diferente do atual (1); refaça a Conferência`, e as
  Análises terminam com código 1.
- A Geração do relatório não lê o arquivo: recebe os resultados dentro de `resultados.pkl`, pelas Análises.
- **Duas versões de formato**: a do pickle (`resultado.VERSAO_FORMATO`), 1, e a do `etapa.json`
  (`src/pipeline.VERSAO_FORMATO["conferencia"]`), 2, desde que as Análises passaram a exigir `nao_aplicaveis.csv`. A do
  `etapa.json` é conferida no pré-requisito das Análises (código 5).

### 3.6 Objetos da função da etapa

- **Entrada**: `Perfil` (passado por `src/pipeline.executar_etapa`), `SerieConjunto` e `IndicadoresONS`, do Tratamento;
  nas usinas sem EVT, também a base horária (`DataFrame`), a programação (`ProgramacaoONS`), o despacho
  (`DespachoTratado`) e as tabelas das renováveis (`Dict[str, DataFrame]`).
- **Saída**: `ResultadoEtapa(codigo, arquivos, resumo)`, de `src/pipeline.py`. `arquivos` lista o que foi gravado dentro
  de `registrar_gravacoes()`, inclusive os arquivos inalterados.

### 3.7 Catálogo das conferências (`src/conferencia/aplicabilidade.py`)

`ConferenciaCatalogo` (dataclass imutável):

| Campo | Tipo | Conteúdo |
|---|---|---|
| `id` | `str` | id da conferência (o mesmo de `ResultadoConferencia.id`) |
| `descricao` | `str` | descrição, usada pelo relatório na tabela das conferências não aplicáveis |
| `tipos` | `Tuple[str, ...]` | tipos de usina a que se aplica |
| `conjuntos` | `Tuple[str, ...]` | chaves do registro da Coleta que precisam ter sido coletadas para a usina |
| `geracao_da_usina` | `bool` | só com a Geração por usina no nível da usina |
| `exige_membros` | `bool` | só com a usina em conjunto (`identificacao.id_conjunto`) e os `[[identificacao.membros]]` no perfil |
| `programacao_da_usina` | `bool` | só com a Programação diária no nível da usina |
| `fontes_no_mesmo_nivel` | `bool` | só com duas fontes da geração (`FONTES_DA_GERACAO`) num mesmo nível |
| `geracao_do_conjunto` | `bool` | só com a Geração por usina no nível do conjunto |
| `programacao_no_nivel_do_fc` | `bool` | só com a Programação diária no nível do Fator de capacidade |
| `so_sem_evt` | `bool` | só na usina sem EVT |
| `registrada_so_nos_tipos` | `bool` | fora dos `tipos`, nenhuma linha em `nao_aplicaveis.csv` |

`CATALOGO_CONFERENCIAS`, nesta ordem:

| `id` | `descricao` | `tipos` | `conjuntos` | Condições |
|---|---|---|---|---|
| `geracao` | geração da base de EVT × Geração por usina | UHE, PCH, CGH | `evt`, `geracao` | `geracao_da_usina` |
| `disponibilidade` | disponibilidade declarada da base de EVT × Disponibilidade por usina | UHE, PCH, CGH | `evt`, `disponibilidade` | — |
| `vazoes` | vazões da base de EVT × Dados hidrológicos | UHE, PCH, CGH | `evt`, `hidrologia` | — |
| `dispf_horas` | DISPF × horas por estado operativo | UHE, PCH, CGH, UTE, UTN | `indicadores` | — |
| `teifa_teip` | TEIFa e TEIP refeitas a partir das horas | UHE, PCH, CGH, UTE, UTN | `indicadores` | — |
| `cadastro` | ficha do cadastro × perfil da usina | os sete tipos | `cadastro` | — |
| `geracao_fontes` | G1. geração da usina entre fontes | EOL, UFV | — | `fontes_no_mesmo_nivel` |
| `soma_conjunto` | G2. soma das usinas do conjunto × geração do conjunto | EOL, UFV | `geracao`, `restricao_detalhe` | `exige_membros`, `geracao_do_conjunto` |
| `programacao_despacho` | G3. Programação diária × geração programada do despacho | UTE, UTN | `programacao`, `despacho` | `programacao_da_usina` |
| `verificada_despacho` | G4. geração verificada do despacho × Geração por usina | UTE, UTN | `geracao`, `despacho` | `geracao_da_usina` |
| `programacao_renovaveis` | G5. Programação diária × geração programada do Fator de capacidade | EOL, UFV | `programacao`, `fator_capacidade` | `programacao_no_nivel_do_fc` |
| `alinhamento_hidrologia` | hora dos Dados hidrológicos conferida pela geração da usina | UHE, PCH, CGH | `hidrologia`, `geracao` | `geracao_da_usina`, `so_sem_evt`, `registrada_so_nos_tipos` |

- **Fontes da geração** (`FONTES_DA_GERACAO`, G1): `geracao`, `fator_capacidade`, `restricao_detalhe`,
  `restricao_razao`. `niveis_coletados(perfil, chave)` dá os níveis em que a Coleta obtém cada uma (os dois, com a
  cobertura `["proprio", "conjunto"]`).
- **Ordem das verificações** (`_motivo_estatico`), a primeira que falha dá o motivo: tipo; `so_sem_evt`; `exige_membros`
  (conjunto, depois membros); `conjuntos` coletados, na ordem declarada; `geracao_da_usina`; `programacao_da_usina`;
  `fontes_no_mesmo_nivel`; `geracao_do_conjunto`; `programacao_no_nivel_do_fc`.
- `aplicaveis(perfil)` dá os ids que passam em todas, na ordem do catálogo. `tabela_nao_aplicaveis(perfil, resultados)`
  dá `nao_aplicaveis.csv` (seção 2.12).

## 4. Manifesto da etapa (`etapa.json`)

Campos comuns às cinco etapas: `etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em` (UTC), `status`,
`codigo_saida`, `etapa_anterior`, `arquivos` e `resumo`. A definição deles, os estados e as transições estão na
[spec da Coleta de dados](../001-coleta-dados/spec.md) (FR-011 a FR-013) e no
[data model dela](../001-coleta-dados/data-model.md). Na Conferência:

| Campo | Valor |
|---|---|
| `etapa` | `conferencia` |
| `versao_formato` | 2 |
| `etapa_anterior` | `{"etapa": "tratamento", "concluida_em": <do etapa.json do Tratamento>}` |
| `status` e `codigo_saida` | `concluida` com 0 ou 3; `falha` com 1 |
| `arquivos` | `conferencias.pkl`, os CSV desta execução e `nao_aplicaveis.csv`, na ordem de gravação, com `nome`, `bytes` e `sha256`; os inalterados entram, os apagados não |
| `resumo` | uma chave por resultado de `conferencias.pkl`, na mesma ordem, com o conteúdo abaixo, e a chave `nao_aplicaveis`; com código 1, `{"erro": "<mensagem>"}`, ou `{"erro": "interrompida pelo usuário"}` depois de Ctrl+C |

Conteúdo de cada conferência no `resumo` (`ResultadoConferencia.resumo()`):

| Campo | Quando | Significado |
|---|---|---|
| `aplicavel` | sempre | `true` ou `false` |
| `motivo` | não aplicável | motivo (seção 5.2); os outros campos não aparecem |
| `unidade` | aplicável | `horas`, `meses-unidade`, `meses` ou `campos` |
| `comparados`, `coincidentes`, `divergentes` | aplicável | quantidades |
| `pct_coincidencia` | vazões aplicáveis | `coincidentes` ÷ `comparados` × 100; `null` sem hora comum |
| `meta_pct` | vazões aplicáveis | 99.0 |
| `meta_atingida` | vazões aplicáveis | `true` ou `false` |

A chave `nao_aplicaveis` traz a lista dos ids de `nao_aplicaveis.csv`, na ordem do arquivo.

Exemplos: na São Domingos, `"vazoes": {"aplicavel": true, "unidade": "horas", "comparados": 70731, "coincidentes":
70731, "divergentes": 0, "pct_coincidencia": 100.0, "meta_pct": 99.0, "meta_atingida": true}`, `"dispf_horas":
{"aplicavel": true, "unidade": "meses-unidade", "comparados": 160, "coincidentes": 156, "divergentes": 4}` e
`"nao_aplicaveis": ["geracao_fontes", "soma_conjunto", "programacao_despacho", "verificada_despacho",
"programacao_renovaveis", "alinhamento_hidrologia"]`; na usina fictícia dos testes, com dois meses de dados,
`"teifa_teip": {"aplicavel": false, "motivo": "nenhum mês com a janela de 60 meses completa"}`; numa térmica fictícia
sem os indicadores nem o despacho, só `cadastro` e `nao_aplicaveis`.

## 5. Regras, estados e validações

### 5.1 Tolerâncias, meta e janela

| Regra | Valor | Constante | Onde |
|---|---|---|---|
| Coincidência da geração e da disponibilidade | diferença ≤ 0,01 MW | `TOLERANCIA_COINCIDENCIA_MW` | `src/comum/regras.py` |
| Coincidência das conferências entre fontes G1 a G5 | diferença ≤ 0,01 MW | `TOLERANCIA_COINCIDENCIA_MW` | `src/comum/regras.py` |
| Coincidência de cada vazão | diferença ≤ 0,5 m³/s | `TOLERANCIA_COINCIDENCIA_VAZAO_M3S` | `src/comum/regras.py` |
| Meta das vazões | ≥ 99 % das horas comuns, com ao menos uma hora comum | `META_ALINHAMENTO_HIDROLOGIA_PCT` | `src/comum/regras.py` |
| DISPF × horas | cada diferença ≤ 1 h | `TOLERANCIA_DIVERGENCIA_HORAS` | `src/comum/regras.py` |
| Reprodução da TEIFa e da TEIP | as duas diferenças ≤ 0,001 p.p. | `TOLERANCIA_REPRODUCAO_TAXAS_PP` | `src/comum/regras.py` |
| Janela das taxas | 60 meses | `JANELA_TAXAS_MESES` | `src/comum/regras.py` |
| Potência autorizada × perfil | diferença ≤ 0,001 MW | `TOLERANCIA_POTENCIA_CADASTRO_MW` | `src/comum/regras.py` |
| Arredondamento da diferença antes da comparação | 9 casas | `CASAS_COMPARACAO` | `src/conferencia/resultado.py` |
| Deslocamento registrado nas vazões e no alinhamento da hidrologia | −1 h | valor fixo em `alinhar_com_evt` e em `conferencia_alinhamento_hidrologia` | `src/conferencia/vazoes.py` |
| Deslocamentos do alinhamento da hidrologia | −1, 0 e +1 h | `DESLOCAMENTOS_ALINHAMENTO_H` | `src/conferencia/vazoes.py` |
| Deslocamentos medidos na G4 | +1 h e −1 h | valores fixos em `conferir_series` | `src/conferencia/fontes.py` |

- Toda comparação usa `diferenca_absoluta`: a diferença absoluta, arredondada a 9 casas, coincide quando é menor ou igual
  à tolerância. O limite está incluído: 30,01 MW × 30,00 MW coincide, embora a subtração em ponto flutuante dê
  0,010000000000001563. Um valor ausente continua ausente depois do arredondamento (seção 5.3).
- As colunas de diferença gravadas (`diferenca_media_mw`, `diferenca_maxima_mw`, `diferenca_*_h`, `diferenca_*_pp`,
  `diferenca_mwh`) não são arredondadas; o arredondamento vale só para a comparação.
- Nenhum desses valores vem do perfil; são iguais para qualquer usina.
- Só as vazões têm meta. As conferências G1 a G5 e o alinhamento da hidrologia não têm meta e nunca mudam o código.

### 5.2 Aplicabilidade e motivos

**Motivos do catálogo** (`_motivo_estatico`, antes de rodar; só para as conferências que não rodam):

| Conferência | Não aplicável quando | `motivo` |
|---|---|---|
| qualquer | tipo da usina fora de `tipos` | `não se aplica a <tipo>: conferência de <tipos>` (por exemplo, `não se aplica a UHE: conferência de EOL e UFV`) |
| `alinhamento_hidrologia` | hidrelétrica com EVT | `na hidrelétrica com EVT, a hora da hidrologia é conferida pelas vazões da base de EVT` |
| `soma_conjunto` | perfil sem `identificacao.id_conjunto` | `a usina não está em conjunto de usinas` |
| `soma_conjunto` | perfil sem `[[identificacao.membros]]` | `sem os membros do conjunto no perfil` |
| qualquer | conjunto de `conjuntos` não coletado para a usina | `conjunto <nome> não coletado para a usina (cobertura: <valor declarado ou "não declarada">)`, com o nome de `NOMES_CONJUNTOS` (por exemplo, `Energia Vertida Turbinável`, `Indicadores de desempenho do ONS`, `Geração térmica por motivo de despacho`) |
| `geracao`, `verificada_despacho`, `alinhamento_hidrologia` | Geração por usina coletada só no nível do conjunto | `Geração por usina só no nível do conjunto: não se compara com uma série da usina` |
| `programacao_despacho` | Programação diária coletada no nível do conjunto | `Programação diária só no nível do conjunto: não se compara com o despacho da usina` |
| `geracao_fontes` | menos de duas fontes da geração num mesmo nível | `sem duas fontes da geração no mesmo nível (Geração por usina, Fator de capacidade e restrições): par de níveis diferentes não se compara` |
| `soma_conjunto` | Geração por usina sem o nível do conjunto | `Geração por usina sem o nível do conjunto: a soma das usinas não tem com o que se comparar` |
| `programacao_renovaveis` | Programação diária e Fator de capacidade em níveis diferentes | `Programação diária (<nível>) e Fator de capacidade (<nível>) em níveis diferentes: não se comparam` |

**Motivos dos resultados** (a conferência rodou e ficou sem base):

| Conferência | Não aplicável quando | `motivo` |
|---|---|---|
| `geracao` | série de Geração por usina ausente ou sem linhas | `Geração por usina sem dados da usina no período` |
| `disponibilidade` | série de Disponibilidade por usina ausente ou sem linhas | `Disponibilidade por usina sem dados da usina no período` |
| `vazoes` | série hidrológica ausente ou sem linhas | `Dados hidrológicos horários sem dados da usina no período` |
| `dispf_horas` | indicadores ausentes, ou `ug_mensal` ou `horas_estado` vazios | `indicadores mensais por unidade ou horas por estado operativo sem dados no período` |
| `teifa_teip` | `horas_estado` com linhas e `taxas` vazias (usina ausente das taxas publicadas) | `a usina não consta das taxas TEIFa e TEIP publicadas pelo ONS no período` |
| `teifa_teip` | indicadores ausentes ou `horas_estado` vazio | `horas por estado operativo ou taxas TEIFa e TEIP sem dados no período` |
| `teifa_teip` | nenhum mês com janela completa (a tabela `recalculo` fica registrada) | `nenhum mês com a janela de 60 meses completa` |
| `cadastro` | ficha ausente ou sem linhas | `a usina não tem ficha no cadastro do ONS` |
| `programacao_despacho` | programação ou despacho sem horas | `Programação diária ou despacho sem horas no período` |
| `programacao_despacho` | nenhuma hora comum | `nenhuma hora com a Programação diária e o programado do despacho` |
| `verificada_despacho` | base horária ou despacho sem horas | `Geração por usina ou despacho sem horas no período` |
| `verificada_despacho` | nenhuma hora comum | `nenhuma hora com o verificado do despacho e a Geração por usina` |
| `geracao_fontes` | nenhuma hora comum em nenhum par | `nenhuma hora com duas fontes da geração no mesmo nível` |
| `soma_conjunto` | nenhuma hora com todas as usinas, ou sem a geração do conjunto | `nenhuma hora com todas as usinas do conjunto e a Geração por usina do conjunto` |
| `soma_conjunto` | nenhuma hora comum entre a soma e a geração do conjunto | `nenhuma hora com a soma das usinas e a Geração por usina do conjunto` |
| `programacao_renovaveis` | programação ou fator de capacidade sem horas | `Programação diária ou Fator de capacidade sem horas no período` |
| `programacao_renovaveis` | nenhuma hora comum | `nenhuma hora com a Programação diária e o programado do Fator de capacidade` |
| `alinhamento_hidrologia` | série hidrológica ausente ou sem linhas | `Dados hidrológicos horários sem dados da usina no período` |
| `alinhamento_hidrologia` | base horária sem horas no nível da usina | `sem a geração no nível da usina no período` |

Nas seis conferências da FR-002, com as bases presentes e nada comparável, a conferência continua aplicável, com 0
comparados: série cujas horas não encontram par na outra fonte ou estão sinalizadas, pares de DISPF × horas sem algum
valor, meses de janela completa sem alguma taxa. Nas vazões, isso conta como meta não atingida (código 3). No
alinhamento da hidrologia, com as duas bases presentes e nenhuma hora comum, a conferência também é aplicável, com 0
horas e o alinhamento não confirmado. Nas conferências G1 a G5, sem hora comum, ela é não aplicável.

### 5.3 O que entra em cada comparação

| Conferência | Entra | Fica fora da comparação (os dados não mudam) |
|---|---|---|
| `geracao` | horas de Geração por usina com `qualidade` `OK` e valor; horas da base de EVT com valor, entre a primeira e a última dessas horas | horas `G1`, que contam como só na base de EVT quando a base tem a hora; horas só numa fonte, contadas por fonte |
| `disponibilidade` | horas `OK` com `val_dispoperacional` × horas da base de EVT com `val_disponibilidade` | horas sinalizadas (D1 a D4), contadas só em `horas_sinalizadas_excluidas`; horas só numa fonte, contadas por fonte |
| `vazoes` | horas com turbinada e vertida nas duas fontes, depois de `limpos` | vazão negativa (H1), só no campo; hora em que falta alguma das quatro vazões |
| `dispf_horas` | pares (`mes`, `ug`) presentes nas duas tabelas e com os cinco valores de `VALORES_DISPF` (HP, HDP, HDF, `indisppf`, `indispff`) | par sem algum desses valores: fora das quantidades e do período, contado em `tabelas["sem_valor"]` |
| `teifa_teip` | meses publicados com janela completa e as quatro taxas de `VALORES_TAXAS` (publicadas e recalculadas) | meses sem janela completa, com as taxas recalculadas vazias, sem contagem; meses de janela completa sem alguma taxa (publicada ausente, ou recalculada vazia por soma nula das horas da base), contados em `tabelas["sem_valor"]` |
| `cadastro` | primeira linha da ficha | — |
| G1 a G5 | horas com valor nas duas fontes, em hora cheia | horas só numa fonte, contadas por fonte (`so_a`, `so_b`) |
| `geracao_fontes` (G1) | cada par de fontes em cada nível que as duas têm; a restrição com a razão só nas horas com as duas meias-horas | pares de níveis diferentes, não comparados |
| `soma_conjunto` (G2) | horas em que toda usina vigente (a do relatório, sempre; cada membro, do dia de `inicio` ao de `fim`) tem valor | horas incompletas, fora da soma e contadas em `horas_incompletas` |
| `verificada_despacho` (G4) | horas da base horária no nível `usina` | horas do conjunto |
| `alinhamento_hidrologia` | horas com a geração da base horária no nível `usina` e a vazão turbinada, depois de `limpos` | vazão negativa (H1); horas do conjunto |

Os registros sinalizados da base de EVT (regras R1 a R9 do Tratamento) entram em todas as comparações. Nas conferências
G1 a G5 e no alinhamento da hidrologia, os valores sinalizados pelo Tratamento também entram; só o valor ausente fica
fora.

**Janela completa** (`janela_completa(mes, primeiro_mes, janela_meses)`): o primeiro mês da janela (59 meses antes do
mês da taxa) não é anterior ao primeiro mês de `horas_estado`. O critério não procura lacunas dentro da janela;
`meses_na_janela` mostra quantos meses entraram. `reproducao_das_taxas(recalculo, primeiro_mes)` devolve os meses de
janela completa (`completos`), os comparáveis (`comparaveis`, `meses`), os reproduzidos, os `sem_valor` e a
`diferenca_maxima_pp`.

**Alinhamento confirmado**: a correlação sem deslocamento é definida e maior que a de cada outro deslocamento com
correlação definida. Os resultados contam as horas comuns sem deslocamento: todas em `coincidentes` se confirmado, todas
em `divergentes` se não.

### 5.4 Textos do cadastro

| Campo | Diverge quando | `texto` |
|---|---|---|
| `potência autorizada (MW)` | valor ausente ou não numérico, ou diferença acima de 0,001 MW | `potência autorizada de <cadastro, 1 casa> MW (projeto: <perfil, sem casas se inteira; senão, 1 casa> MW)` |
| `estado` | `id_estado` em maiúsculas ≠ `usina.estado` | `estado <id_estado ou "não informado"> (projeto: <usina.estado>)` |
| `id ONS` | `id_ons` da ficha em maiúsculas ≠ `identificacao.id_ons` (vazio quando o perfil não o tem) | `id ONS <id_ons ou "não informado"> (projeto: <id ONS do perfil ou "não informado">)` |
| `linhas com o CEG` | `linhas_ceg` > 1; ausente ou não numérico vale 1 | `<linhas_ceg> linhas com o CEG do projeto (usada a primeira)` |

Os números seguem o padrão brasileiro (`fmt_num`), com `–` para valor ausente. `tabelas["divergencias"]` junta os
textos dos campos com `DIVERGE`.

### 5.5 Invariantes

- `id` fora de `CONFERENCIAS` → `ValueError("conferência desconhecida: …")`.
- Conferência aplicável com `comparados ≠ coincidentes + divergentes` → `ValueError`.
- Nas conferências hora a hora, cada hora comum é coincidente ou divergente, e cada hora divergente cai num único
  período contínuo: a soma de `horas` dos períodos é igual a `divergentes` (na G1, somados os pares).

### 5.6 Código de saída e `status`

| Situação | Código | `status` no `etapa.json` | Etapas seguintes |
|---|---|---|---|
| resultados gravados; vazões na meta, não aplicáveis ou fora do caminho (usinas sem EVT) | 0 | `concluida` | as já executadas ficam `desatualizada` |
| hidrelétrica com EVT com as vazões aplicáveis sem a meta, inclusive sem hora comum; os seis resultados gravados | 3 | `concluida`, com `codigo_saida` 3 | idem; o `completo` para; as Análises, executadas à parte, omitem os cruzamentos hidrológicos |
| erro de leitura, de gravação ou inesperado, ou interrupção pelo usuário (Ctrl+C) | 1 | `falha` | a seguinte recusa, com código 5 |
| Tratamento ausente, com falha, desatualizado ou em formato antigo | 5 | nada é gravado | nada muda |
| perfil inválido, inclusive em rascunho; opção inválida | 4; 2 | nada é gravado | nada muda |

As divergências nunca mudam o código. O alinhamento da hidrologia não confirmado também não.

### 5.7 Arquivos da pasta

| Situação | Efeito |
|---|---|
| tabela presente, conteúdo novo ou diferente | gravado (NOVO ou ALTERADO no log), conferido no disco; em falha ou interrupção, a versão anterior volta e a etapa termina com 1 |
| tabela presente, conteúdo idêntico | não é regravado (INALTERADO no log), mas entra em `arquivos` |
| tabela ausente nesta execução | o CSV de uma execução anterior é apagado e não entra em `arquivos` |
| `nao_aplicaveis.csv` | passa pela gravação em toda execução (NOVO, ALTERADO ou INALTERADO) e sempre entra em `arquivos` |
| qualquer caso | nenhum `.bak`; os temporários `.tmp` são removidos |
