# Data Model: Conferência

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-08

## 1. Entradas

A etapa só lê arquivos locais. Caminhos relativos a `data/usinas/<slug>/`, exceto o perfil.

| Arquivo | Gravado por | Lido por | Conferência | Colunas ou campos usados |
|---|---|---|---|---|
| `tratamento/etapa.json` | Tratamento de dados | `src/pipeline.etapa_anterior_concluida` | pré-requisito | `status` = `concluida` e `versao_formato` = 1; `concluida_em` vai para `etapa_anterior` |
| `tratamento/evt_tratado.parquet` | Tratamento | `etapa.conferir` (só `COLUNAS_EVT`) | geração, disponibilidade, vazões | `din_instante`, `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida` |
| `tratamento/geracao_horaria.csv` | Tratamento | `carregar_geracao_tratada` | geração | `din_instante`, `val_geracao`, `qualidade` (`OK` ou `G1`) |
| `tratamento/disponibilidade_horaria.csv` | Tratamento | `carregar_disponibilidade_tratada` | disponibilidade | `din_instante`, `val_dispoperacional`, `qualidade` (`OK` ou as regras D1 a D4) |
| `tratamento/hidrologia_horaria.csv` | Tratamento | `carregar_hidrologia_tratada` | vazões | `din_instante` (já na hora de início), `val_vazaoturbinada`, `val_vazaovertida` |
| `tratamento/indicadores_ug_mensal.csv` | Tratamento | `carregar_indicadores_tratados` (`ug_mensal`) | DISPF × horas | `mes`, `ug`, `indisppf`, `indispff` (% do mês) |
| `tratamento/horas_estado_mensal.csv` | Tratamento | idem (`horas_estado`) | DISPF × horas; TEIFa e TEIP | `mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HEDP`, `HEDF`, `potencia_mw` |
| `tratamento/teifa_teip_mensal.csv` | Tratamento | idem (`taxas`) | TEIFa e TEIP | `mes`, `teifa`, `teip` (frações de 0 a 1) |
| `tratamento/indicadores_ug_anual.csv` | Tratamento | idem (`ug_anual`) | nenhuma | o leitor exige o arquivo, mas a Conferência não usa a tabela |
| `coleta/cadastro_ficha.csv` | Coleta de dados | `etapa.carregar_ficha_cadastro` | cadastro | primeira linha: `val_potenciaautorizada`, `id_estado`, `id_ons`, `linhas_ceg` |
| `usinas/<slug>/perfil.toml` | fiscal | `carregar_perfil`, na linha de comando | cadastro; pastas | `usina.slug`, `parametros.potencia_instalada_mw` (por `Perfil.potencia_autorizada_esperada_mw`), `usina.estado`, `identificacao.id_ons` |

- **Leitores do Tratamento**: as séries são lidas como `SerieConjunto` (`horaria`, `ausencias`, `auditoria`), com
  `din_instante` convertido em data e hora; `<conjunto>_ausencias.csv` e `auditoria_<conjunto>.csv` também são lidos,
  quando existem, mas a Conferência só usa `horaria`. Os indicadores são lidos como `IndicadoresONS`.
- **Arquivo ausente**: série → `None`; indicadores → `None` quando falta qualquer um dos quatro CSV; ficha ausente ou
  sem linhas → tabela vazia. Em todos os casos a conferência correspondente fica não aplicável (seção 5.2). Sem
  `evt_tratado.parquet`, a etapa termina com código 1.
- **Ficha do cadastro**: lida com `keep_default_na=False`, de modo que um campo vazio continua texto vazio. A Coleta já
  reduz a ficha à primeira linha com o CEG do perfil e conta em `linhas_ceg` as linhas com esse CEG.
- **Limitações conhecidas da Coleta que chegam aqui**: um valor publicado com vírgula decimal chega vazio e sinalizado
  como não numérico, e a hora fica fora da comparação (na potência do cadastro, vira divergência); um conjunto horário
  sem a coluna de conferência tem as linhas da usina contadas como "só identificador", e a conferência dele fica não
  aplicável, em vez de a Coleta falhar.
- O formato completo desses arquivos está no [data model do Tratamento](../002-tratamento-dados/data-model.md) e no
  [da Coleta](../001-coleta-dados/data-model.md).

## 2. Saídas

Pasta: `data/usinas/<slug>/conferencia/`. Os CSV são gravados por `gravar_csv`: separador `;`, UTF-8, cabeçalho, sem
índice, datas `AAAA-MM-DD HH:MM:SS`, ponto decimal, lógicos como `True`/`False` e campo vazio para valor ausente. Nenhum
arquivo tem `.bak`; um arquivo de conteúdo idêntico ao novo não é regravado.

| Arquivo | Conferência e tabela (`CSV_CONFERENCIA`) | Gravado quando |
|---|---|---|
| `conferencias.pkl` | os seis resultados | sempre que a etapa roda |
| `geracao.csv` | `geracao` → `mensal` | geração aplicável |
| `geracao_divergencias.csv` | `geracao` → `divergencias` | geração aplicável; só o cabeçalho sem divergência |
| `disponibilidade.csv` | `disponibilidade` → `resumo` (uma linha) | disponibilidade aplicável |
| `disponibilidade_divergencias.csv` | `disponibilidade` → `divergencias` | disponibilidade aplicável; só o cabeçalho sem divergência |
| `vazoes.csv` | `vazoes` → `alinhamento` | vazões aplicáveis |
| `dispf_horas.csv` | `dispf_horas` → `divergencias` | DISPF × horas aplicável; só o cabeçalho sem divergência |
| `teifa_teip.csv` | `teifa_teip` → `recalculo` | horas e taxas presentes, mesmo sem mês de janela completa |
| `cadastro.csv` | `cadastro` → `campos` | cadastro aplicável |
| `etapa.json` | manifesto (seção 4) | sempre que a etapa passa do pré-requisito |

Quando a tabela não existe nesta execução, o CSV que sobrou de uma execução anterior é apagado (seção 5.7).

### 2.1 `conferencias.pkl`

Pickle (`pickle.HIGHEST_PROTOCOL`) de um dicionário `{"versao_formato": 1, "resultados": {<id>: ResultadoConferencia}}`,
com os seis ids na ordem de `CONFERENCIAS`. O objeto está na seção 3. Na São Domingos: 17.358 bytes.

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

Montados por `src/comum/periodos.periodos_continuos`. Na São Domingos, os dois têm só o cabeçalho.

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
| `ug` | inteiro | número da unidade geradora |
| `HP` | real | horas do período |
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
| `valor_perfil` | conforme o campo | `potencia_autorizada_esperada_mw`, `usina.estado`, `identificacao.id_ons` ou 1 |
| `situacao` | texto | `CONFERE` ou `DIVERGE` |
| `texto` | texto | frase do campo, usada quando ele diverge (seção 5.4) |

## 3. Objetos em memória e entre etapas

### 3.1 `ResultadoConferencia` (`src/conferencia/resultado.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `id` | `str` | um dos seis de `CONFERENCIAS`: `geracao`, `disponibilidade`, `vazoes`, `dispf_horas`, `teifa_teip`, `cadastro` |
| `bases` | `Tuple[str, str]` | as duas bases comparadas (seção 3.2) |
| `unidade` | `str` | `horas`, `meses-unidade`, `meses` ou `campos` |
| `aplicavel` | `bool` | padrão `True` |
| `motivo` | `str` | vazio quando aplicável (seção 5.2) |
| `periodo` | `Tuple[Timestamp, Timestamp]` ou `None` | primeira e última hora, ou primeiro e último mês, comparados; `None` no cadastro, quando nada é comparado e quando não aplicável |
| `comparados`, `coincidentes`, `divergentes` | `int` | quantidades na unidade da conferência; 0 quando não aplicável |
| `tolerancia` | `float` ou `None` | critério de coincidência (seção 5.1); preenchido também quando não aplicável |
| `meta` | `float` ou `None` | 99,0 nas vazões, inclusive quando não aplicáveis; `None` nas demais |
| `meta_atingida` | `bool` ou `None` | só nas vazões aplicáveis |
| `tabelas` | `Dict[str, Any]` | tabelas de detalhe (seção 3.3) |

- `resumo()` devolve a situação para o `etapa.json` (seção 4).
- `nao_aplicavel(id, bases, unidade, motivo, tabelas=None, **campos)` monta o resultado não aplicável.
- `__post_init__` valida as invariantes da seção 5.5.
- No mesmo módulo, `diferenca_absoluta(diferenca)` devolve a diferença absoluta arredondada a `CASAS_COMPARACAO` (9)
  casas, para número, série ou tabela; é a base de toda comparação com tolerância (seção 5.1).

### 3.2 Bases, unidade e período de cada conferência

| `id` | `bases` (constantes `BASES`, `BASES_DISPF`, `BASES_TAXAS`) | `unidade` | `periodo` |
|---|---|---|---|
| `geracao` | `base de EVT (val_geracao)`; `Geração por usina (val_geracao)` | `horas` | primeira e última hora comum |
| `disponibilidade` | `base de EVT (val_disponibilidade)`; `Disponibilidade por usina (val_dispoperacional)` | `horas` | primeira e última hora comum |
| `vazoes` | `base de EVT (val_vazaoturbinada, val_vazaovertida)`; `Dados hidrológicos horários (mesmas vazões)` | `horas` | primeira e última hora comum |
| `dispf_horas` | `Indicadores por unidade geradora, base mensal (INDISPPF e INDISPFF)`; `Parâmetros das taxas TEIFa e TEIP (HDP e HDF)` | `meses-unidade` | primeiro e último mês dos meses-unidade comparados |
| `teifa_teip` | `TEIFa e TEIP recalculadas a partir das horas por estado operativo`; `Taxas TEIFa e TEIP publicadas` | `meses` | primeiro e último mês comparado (janela completa e as quatro taxas) |
| `cadastro` | `Modalidade das usinas (ficha da usina)`; `perfil da usina` | `campos` | `None` |

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

Resultado não aplicável: `tabelas` vazio, exceto a TEIFa e a TEIP sem mês de janela completa, que guardam `recalculo`.

### 3.4 Números citados nas legendas (FR-005)

| Conferência | Número | Campo |
|---|---|---|
| geração e disponibilidade | horas coincidentes, comuns e divergentes; percentual; horas só numa fonte | `coincidentes`, `comparados`, `divergentes`; em `tabelas["resumo"]`: `pct_coincidentes`, `so_ons_geracao` ou `so_ons_disponibilidade`, e `so_base_evt` |
| vazões | horas coincidentes nas duas vazões, comuns, percentual e meta | `tabelas["alinhamento"]`: `coincidentes_ambas`, `horas_comuns`, `pct_coincidencia`, `meta_pct`, `confirmado` |
| DISPF × horas | meses-unidade divergentes | `divergentes`; `tabelas["divergencias"]` |
| TEIFa e TEIP | meses comparados e reproduzidos; maior diferença | `comparados`, `coincidentes`; `tabelas["diferenca_maxima_pp"]` (levados pelas Análises em `recalculo_resumo`) |
| cadastro | texto de cada divergência | `tabelas["divergencias"]` |
| não aplicável | motivo | `motivo` |

### 3.5 `conferencias.pkl` entre as etapas

- **Gravação**: `salvar_conferencias(resultados, destino)`, por `gravar_bytes(..., copia=False)`.
- **Leitura**: só pelas Análises (`src/analises/etapa.carregar_entradas` → `carregar_conferencias`). Uma versão diferente
  de `VERSAO_FORMATO` levanta `ValueError` com `<arquivo>: formato diferente do atual (1); refaça a Conferência`, e as
  Análises terminam com código 1.
- A Geração do relatório não lê o arquivo: recebe os resultados dentro de `resultados.pkl`, pelas Análises.
- **Duas versões de formato**: a do pickle (`resultado.VERSAO_FORMATO`) e a do `etapa.json`
  (`src/pipeline.VERSAO_FORMATO["conferencia"]`), ambas 1. A do `etapa.json` é conferida no pré-requisito das Análises
  (código 5).

### 3.6 Objetos da função da etapa

- **Entrada**: `Perfil` (passado por `src/pipeline.executar_etapa`), `SerieConjunto` e `IndicadoresONS`, do Tratamento.
- **Saída**: `ResultadoEtapa(codigo, arquivos, resumo)`, de `src/pipeline.py`. `arquivos` lista o que foi gravado dentro
  de `registrar_gravacoes()`, inclusive os arquivos inalterados.

## 4. Manifesto da etapa (`etapa.json`)

Campos comuns às cinco etapas: `etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em` (UTC), `status`,
`codigo_saida`, `etapa_anterior`, `arquivos` e `resumo`. A definição deles, os estados e as transições estão na
[spec da Coleta de dados](../001-coleta-dados/spec.md) (FR-011 a FR-013) e no
[data model dela](../001-coleta-dados/data-model.md). Na Conferência:

| Campo | Valor |
|---|---|
| `etapa` | `conferencia` |
| `versao_formato` | 1 |
| `etapa_anterior` | `{"etapa": "tratamento", "concluida_em": <do etapa.json do Tratamento>}` |
| `status` e `codigo_saida` | `concluida` com 0 ou 3; `falha` com 1 |
| `arquivos` | `conferencias.pkl` e os CSV desta execução, na ordem de gravação, com `nome`, `bytes` e `sha256`; os inalterados entram, os apagados não |
| `resumo` | uma chave por conferência, na ordem de `CONFERENCIAS`, com o conteúdo abaixo; com código 1, `{"erro": "<mensagem>"}`, ou `{"erro": "interrompida pelo usuário"}` depois de Ctrl+C |

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

Exemplos: na São Domingos, `"vazoes": {"aplicavel": true, "unidade": "horas", "comparados": 70731, "coincidentes":
70731, "divergentes": 0, "pct_coincidencia": 100.0, "meta_pct": 99.0, "meta_atingida": true}` e `"dispf_horas":
{"aplicavel": true, "unidade": "meses-unidade", "comparados": 160, "coincidentes": 156, "divergentes": 4}`; na usina
fictícia dos testes, com dois meses de dados, `"teifa_teip": {"aplicavel": false, "motivo": "nenhum mês com a janela de
60 meses completa"}`.

## 5. Regras, estados e validações

### 5.1 Tolerâncias, meta e janela

| Regra | Valor | Constante | Onde |
|---|---|---|---|
| Coincidência da geração e da disponibilidade | diferença ≤ 0,01 MW | `TOLERANCIA_COINCIDENCIA_MW` | `src/comum/regras.py` |
| Coincidência de cada vazão | diferença ≤ 0,5 m³/s | `TOLERANCIA_COINCIDENCIA_VAZAO_M3S` | `src/comum/regras.py` |
| Meta das vazões | ≥ 99 % das horas comuns, com ao menos uma hora comum | `META_ALINHAMENTO_HIDROLOGIA_PCT` | `src/comum/regras.py` |
| DISPF × horas | cada diferença ≤ 1 h | `TOLERANCIA_DIVERGENCIA_HORAS` | `src/comum/regras.py` |
| Reprodução da TEIFa e da TEIP | as duas diferenças ≤ 0,001 p.p. | `TOLERANCIA_REPRODUCAO_TAXAS_PP` | `src/comum/regras.py` |
| Janela das taxas | 60 meses | `JANELA_TAXAS_MESES` | `src/comum/regras.py` |
| Potência autorizada × perfil | diferença ≤ 0,001 MW | `TOLERANCIA_POTENCIA_CADASTRO_MW` | `src/comum/regras.py` |
| Arredondamento da diferença antes da comparação | 9 casas | `CASAS_COMPARACAO` | `src/conferencia/resultado.py` |
| Deslocamento registrado nas vazões | −1 h | valor fixo em `alinhar_com_evt` | `src/conferencia/vazoes.py` |

- Toda comparação usa `diferenca_absoluta`: a diferença absoluta, arredondada a 9 casas, coincide quando é menor ou igual
  à tolerância. O limite está incluído: 30,01 MW × 30,00 MW coincide, embora a subtração em ponto flutuante dê
  0,010000000000001563. Um valor ausente continua ausente depois do arredondamento (seção 5.3).
- As colunas de diferença gravadas (`diferenca_media_mw`, `diferenca_maxima_mw`, `diferenca_*_h`, `diferenca_*_pp`) não
  são arredondadas; o arredondamento vale só para a comparação.
- Nenhum desses valores vem do perfil; são iguais para qualquer usina.

### 5.2 Aplicabilidade e motivos

| Conferência | Não aplicável quando | `motivo` |
|---|---|---|
| `geracao` | série de Geração por usina ausente ou sem linhas | `Geração por usina sem dados da usina no período` |
| `disponibilidade` | série de Disponibilidade por usina ausente ou sem linhas | `Disponibilidade por usina sem dados da usina no período` |
| `vazoes` | série hidrológica ausente ou sem linhas | `Dados hidrológicos horários sem dados da usina no período` |
| `dispf_horas` | indicadores ausentes, ou `ug_mensal` ou `horas_estado` vazios | `indicadores mensais por unidade ou horas por estado operativo sem dados no período` |
| `teifa_teip` | indicadores ausentes, ou `horas_estado` ou `taxas` vazios | `horas por estado operativo ou taxas TEIFa e TEIP sem dados no período` |
| `teifa_teip` | nenhum mês com janela completa (a tabela `recalculo` fica registrada) | `nenhum mês com a janela de 60 meses completa` |
| `cadastro` | ficha ausente ou sem linhas | `a usina não tem ficha no cadastro do ONS` |

Com as bases presentes e nada comparável, a conferência continua aplicável, com 0 comparados: série cujas horas não
encontram par na outra fonte ou estão sinalizadas, pares de DISPF × horas sem algum valor, meses de janela completa
sem alguma taxa. Nas vazões, isso conta como meta não atingida (código 3).

### 5.3 O que entra em cada comparação

| Conferência | Entra | Fica fora da comparação (os dados não mudam) |
|---|---|---|
| `geracao` | horas de Geração por usina com `qualidade` `OK` e valor; horas da base de EVT com valor, entre a primeira e a última dessas horas | horas `G1`, que contam como só na base de EVT quando a base tem a hora; horas só numa fonte, contadas por fonte |
| `disponibilidade` | horas `OK` com `val_dispoperacional` × horas da base de EVT com `val_disponibilidade` | horas sinalizadas (D1 a D4), contadas só em `horas_sinalizadas_excluidas`; horas só numa fonte, contadas por fonte |
| `vazoes` | horas com turbinada e vertida nas duas fontes, depois de `limpos` | vazão negativa (H1), só no campo; hora em que falta alguma das quatro vazões |
| `dispf_horas` | pares (`mes`, `ug`) presentes nas duas tabelas e com os cinco valores de `VALORES_DISPF` (HP, HDP, HDF, `indisppf`, `indispff`) | par sem algum desses valores: fora das quantidades e do período, contado em `tabelas["sem_valor"]` |
| `teifa_teip` | meses publicados com janela completa e as quatro taxas de `VALORES_TAXAS` (publicadas e recalculadas) | meses sem janela completa, com as taxas recalculadas vazias, sem contagem; meses de janela completa sem alguma taxa (publicada ausente, ou recalculada vazia por soma nula das horas da base), contados em `tabelas["sem_valor"]` |
| `cadastro` | primeira linha da ficha | — |

Os registros sinalizados da base de EVT (regras R1 a R9 do Tratamento) entram em todas as comparações.

**Janela completa** (`janela_completa(mes, primeiro_mes, janela_meses)`): o primeiro mês da janela (59 meses antes do
mês da taxa) não é anterior ao primeiro mês de `horas_estado`. O critério não procura lacunas dentro da janela;
`meses_na_janela` mostra quantos meses entraram. `reproducao_das_taxas(recalculo, primeiro_mes)` devolve os meses de
janela completa (`completos`), os comparáveis (`comparaveis`, `meses`), os reproduzidos, os `sem_valor` e a
`diferenca_maxima_pp`.

### 5.4 Textos do cadastro

| Campo | Diverge quando | `texto` |
|---|---|---|
| `potência autorizada (MW)` | valor ausente ou não numérico, ou diferença acima de 0,001 MW | `potência autorizada de <cadastro, 1 casa> MW (projeto: <perfil, sem casas se inteira; senão, 1 casa> MW)` |
| `estado` | `id_estado` em maiúsculas ≠ `usina.estado` | `estado <id_estado ou "não informado"> (projeto: <usina.estado>)` |
| `id ONS` | `id_ons` da ficha em maiúsculas ≠ `identificacao.id_ons` | `id ONS <id_ons ou "não informado"> (projeto: <id ONS do perfil>)` |
| `linhas com o CEG` | `linhas_ceg` > 1; ausente ou não numérico vale 1 | `<linhas_ceg> linhas com o CEG do projeto (usada a primeira)` |

Os números seguem o padrão brasileiro (`fmt_num`), com `–` para valor ausente. `tabelas["divergencias"]` junta os
textos dos campos com `DIVERGE`.

### 5.5 Invariantes

- `id` fora de `CONFERENCIAS` → `ValueError("conferência desconhecida: …")`.
- Conferência aplicável com `comparados ≠ coincidentes + divergentes` → `ValueError`.
- Nas conferências hora a hora, cada hora comum é coincidente ou divergente, e cada hora divergente cai num único
  período contínuo: a soma de `horas` dos períodos é igual a `divergentes`.

### 5.6 Código de saída e `status`

| Situação | Código | `status` no `etapa.json` | Etapas seguintes |
|---|---|---|---|
| seis resultados gravados; vazões na meta ou não aplicáveis | 0 | `concluida` | as já executadas ficam `desatualizada` |
| vazões aplicáveis sem a meta, inclusive sem hora comum; os seis resultados gravados | 3 | `concluida`, com `codigo_saida` 3 | idem; o `completo` para; as Análises, executadas à parte, omitem os cruzamentos hidrológicos |
| erro de leitura, de gravação ou inesperado, ou interrupção pelo usuário (Ctrl+C) | 1 | `falha` | a seguinte recusa, com código 5 |
| Tratamento ausente, com falha, desatualizado ou em formato antigo | 5 | nada é gravado | nada muda |
| perfil inválido; opção inválida | 4; 2 | nada é gravado | nada muda |

As divergências nunca mudam o código.

### 5.7 Arquivos da pasta

| Situação | Efeito |
|---|---|
| tabela presente, conteúdo novo ou diferente | gravado (NOVO ou ALTERADO no log), conferido no disco; em falha ou interrupção, a versão anterior volta e a etapa termina com 1 |
| tabela presente, conteúdo idêntico | não é regravado (INALTERADO no log), mas entra em `arquivos` |
| tabela ausente nesta execução | o CSV de uma execução anterior é apagado e não entra em `arquivos` |
| qualquer caso | nenhum `.bak`; os temporários `.tmp` são removidos |
