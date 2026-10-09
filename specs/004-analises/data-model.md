# Data Model: Análises

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-08

Pastas relativas a `data/usinas/<slug>/`, salvo indicação. Tipos: `int`, `float`, `bool`, `str`, `datetime` (coluna de data e hora), `Timestamp` (valor de data e hora), `Period[M]` (mês), `list`, `dict` e `DataFrame` (tabela pandas).

## 1. Entradas

### 1.1 Arquivos lidos

Todos lidos por `src/analises/etapa.carregar_entradas`, salvo indicação. As Análises não alteram nenhum deles.

| Arquivo | Gravado por | Lido por | O que as Análises usam |
|---|---|---|---|
| `tratamento/evt_tratado.parquet` | Tratamento | `pd.read_parquet` | base de EVT: as 18 colunas do ONS, `arquivo_origem`, `tipo_match`, `anomalia_*` (R6 a R9) e `qualidade_registro` |
| `tratamento/validacao_fisica.csv` | Tratamento | `pd.read_csv` | resultado das regras R1 a R9 (→ `validacao`) |
| `tratamento/indicadores_ug_mensal.csv`, `indicadores_ug_anual.csv`, `horas_estado_mensal.csv`, `teifa_teip_mensal.csv` | Tratamento | `carregar_indicadores_tratados` (`None` se faltar algum) | `IndicadoresONS` |
| `tratamento/programacao_horaria.csv`, `programacao_dias_ausentes.csv` | Tratamento | `carregar_programacao_tratada` (`None` sem a horária) | `ProgramacaoONS` |
| `tratamento/<base>_horaria.csv`, `<base>_ausencias.csv`, `auditoria_<base>.csv`, com `<base>` = `disponibilidade`, `hidrologia` ou `geracao` | Tratamento | `carregar_<base>_tratada` (`None` sem a horária) | `SerieConjunto` de cada base |
| `conferencia/conferencias.pkl` | Conferência | `carregar_conferencias` (recusa outra `versao_formato`) | os seis `ResultadoConferencia` (seção 1.2) |
| `coleta/auditoria_evt.csv` | Coleta | `cobertura._resumo_auditoria` | `nome_arquivo`, `status_processamento`, `registros_codigo_sem_nome`, `registros_nome_sem_codigo` |
| `coleta/auditoria_programacao.csv` | Coleta | `carregar_entradas` → `auditoria_relatorio` | auditoria dos arquivos diários, nas colunas mostradas no relatório |
| `coleta/cadastro_ficha.csv` | Coleta | `ficha_do_cadastro` | ficha da usina, sem `linhas_ceg`, com as divergências da conferência do cadastro |
| `coleta/auditoria_cadastro.csv` | Coleta | `carregar_entradas` | colunas `COLUNAS_AUDITORIA_CADASTRO` |
| `coleta/dicionarios.csv` | Coleta | `carregar_entradas` | registro dos dicionários de dados (→ `dicionarios`) |
| `data/raw/_manifesto_ons.json` | Coleta | `cobertura._resumo_manifesto` | `ultima_modificacao` e `registrado_em_utc` de cada arquivo da EVT |
| `data/raw/{disponibilidade_usina,dados_hidrologicos_ho,geracao_usina_2}/_manifesto_ons.json` | Coleta | `coleta.conjuntos.data_obtencao` | data de obtenção (maior `registrado_em_utc`) |

Campos e formatos desses arquivos: [Coleta](../001-coleta-dados/data-model.md), [Tratamento](../002-tratamento-dados/data-model.md) e [Conferência](../003-conferencia/data-model.md).

### 1.2 Resultados da Conferência usados

| Conferência (`id`) | Tabela de `tabelas` | Vai para |
|---|---|---|
| `geracao` | `resumo` (dict), `mensal`, `divergencias` | `geracao_oficial["conferencia"]`, `["mensal"]`, `["divergencias"]`; `["anual"]` soma a mensal por ano |
| `disponibilidade` | `resumo` (dict), `divergencias` | `disponibilidade["conferencia"]`, `["divergencias"]` |
| `vazoes` | `alinhamento` | `hidrologia["alinhamento"]`; `publicado` = `confirmado` |
| `dispf_horas` | `divergencias` | `ons["divergencias"]` (vazio quando não há) |
| `teifa_teip` | `recalculo`; com a conferência aplicável, também `comparados`, `coincidentes` e `diferenca_maxima_pp` | `ons["recalculo_taxas"]` e a condição da decomposição; `ons["recalculo_resumo"]` (`meses`, `reproduzidos`, `diferenca_maxima_pp`) |
| `cadastro` | `divergencias` (texto) | `cadastro["ficha"]["divergencias"]` e `cadastro["divergencias"]` |

Esses itens são usados só quando a base correspondente tem dados, e só eles seguem nos resultados. Os demais campos de cada `ResultadoConferencia`, como a situação "não aplicável", o motivo e os meses sem valor, ficam em `conferencias.pkl`.

### 1.3 Campos do perfil usados

Lidos de `perfil_ativo()` ([perfil da usina](../001-coleta-dados/contracts/perfil-usina.md)).

| Campo ou valor derivado | Uso nas Análises |
|---|---|
| `parametros.potencia_instalada_mw` (P) | fator de capacidade, disponibilidade relativa, plena carga, metade da potência, constatações de indisponibilidade e de qualidade |
| `parametros.potencia_unitaria_mw` | peso do DISPF quando o ONS não informa a potência da unidade |
| `parametros.unidades_geradoras` (N) | nome da faixa de afluência intermediária |
| `parametros.engolimento_nominal_ug_m3s` | limite da faixa "até uma unidade" |
| `engolimento_maximo_m3s` = N × engolimento por unidade | limite da faixa "acima do engolimento máximo", resumos da hidrologia, regra C3 |
| `parametros.garantia_fisica_mwmed` | geração ÷ garantia física, regra C9 |
| `parametros.ip_referencia`, `parametros.teif_referencia` | regras C2 e C5, constatação dos indicadores oficiais |
| `disponibilidade_referencia` = (1 − IP) × (1 − TEIF) | distância da disponibilidade declarada e do DISPF, regra C5 |
| `analises.vertimento_minimo_m3s` | EVT do vertimento mínimo e mudança de classificação |
| `analises.faixas_geracao_mw` | faixas intermediárias da EVT por nível de geração |
| `usina.inicio_operacao_comercial` | constatação de cobertura (período anterior não coberto) |
| `usina.nome_curto`, `identificacao.cod_usina`, `identificacao.id_ons` | textos das constatações de cadastro, cobertura e conferência da geração |

Numa chamada direta de `analisar` sem as sinalizações do Tratamento, o perfil inteiro vai para `sinalizar_anomalias` e `validar_regras_fisicas` (limites das regras R1 a R9).

## 2. Saídas

### 2.1 `analises/resultados.pkl`

- **Formato**: pickle (`pickle.HIGHEST_PROTOCOL`) de um dicionário; uma gravação por execução, da usina do perfil.
- **Gravação**: `salvar_resultados` → `gravar_bytes(..., copia=False)`:
  - temporário `resultados.pkl.tmp` conferido byte a byte;
  - conteúdo idêntico ao atual não é regravado;
  - troca atômica e SHA-256 conferido;
  - em falha, a versão anterior é restaurada;
  - sem `.bak`.
- **Leitura**: `carregar_resultados` (Geração do relatório), que recusa outra versão com `ValueError`.

| Chave | Tipo | Descrição |
|---|---|---|
| `versao_formato` | `int` | `resultados.VERSAO_FORMATO` = 1; muda quando os campos mudam |
| `resultados` | `ResultadosAnalise` | seção 3.2 |

Na São Domingos: 6,1 MB.

### 2.2 `analises/etapa.json`

Manifesto da etapa (seção 4).

## 3. Objetos em memória e entre etapas

### 3.1 Estruturas recebidas

| Estrutura | Módulo | Campos | Uso |
|---|---|---|---|
| `SerieConjunto` | `src/tratamento/series.py` | `horaria`; `ausencias` (`tipo`, `inicio`, `fim`, `horas`; `tipo` = `MES_SEM_ARQUIVO`, `MES_SEM_USINA` ou `HORAS`); `auditoria` (14 colunas) | disponibilidade, hidrologia e geração |
| `IndicadoresONS` | `src/tratamento/indicadores.py` | `ug_mensal`, `ug_anual`, `horas_estado`, `taxas`; `divergencias` (preenchido em `analisar` com a tabela da conferência `dispf_horas`); `auditoria` (vazio) | indicadores oficiais |
| `ProgramacaoONS` | `src/tratamento/programacao.py` | `horaria` (`din_instante`, `geracao_programada_mw`, `patamares`); `dias_ausentes` (`dia`); `auditoria` | programação |
| `ResultadoConferencia` | `src/conferencia/resultado.py` | ver o [data-model da Conferência](../003-conferencia/data-model.md) | seção 1.2 |

### 3.2 `ResultadosAnalise` (`src/analises/resultados.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `cobertura` | `dict` | cobertura da base de EVT (3.3) |
| `globais` | `dict` | indicadores do período (3.3) |
| `indicadores_anuais` | `DataFrame` | indicadores por ano (3.3) |
| `evt_mensal`, `distribuicao_mes_do_ano`, `evt_por_faixa_geracao` | `DataFrame` | distribuições da EVT (3.3) |
| `perfil_horario_geracao`, `perfil_horario_evt` | `DataFrame` | médias por ano × hora (3.3) |
| `eventos_parada_com_evt`, `eventos_indisponibilidade_total` | `DataFrame` | listas completas de eventos (3.3) |
| `mudanca_classificacao` | `dict` | mudança de classificação do vertimento (3.3) |
| `anomalias`, `resumo_anomalias` | `DataFrame` | registros sinalizados e resumo por regra (3.3) |
| `extremos`, `perfil_estatistico` | `DataFrame` | sem os registros sinalizados (3.3) |
| `parametros` | `DataFrame` | vazio no arquivo; montado pela Geração do relatório |
| `validacao` | `DataFrame` | resultado das regras R1 a R9, do Tratamento |
| `horas_geracao_zero` | `DataFrame` | horas com geração zero por ano e mês (3.3) |
| `achados` | `list[tuple[str, str]]` | constatações (título, texto) (3.10) |
| `conclusao` | `list[dict]` | itens da conclusão (3.11) |
| `ons` | `dict` | indicadores oficiais por unidade geradora (3.4); `{}` sem a base |
| `programacao` | `dict` | programação diária (3.5); `{}` sem a base |
| `disponibilidade` | `dict` | disponibilidade operacional e sincronizada (3.6); `{}` sem a base |
| `hidrologia` | `dict` | afluência, vertimento e nível (3.7); `{}` sem a base |
| `geracao_oficial` | `dict` | geração por usina (3.8); `{}` sem a base |
| `cadastro` | `dict` | ficha do cadastro (3.9); `{}` sem a ficha |
| `dicionarios` | `dict` | `{"registro": DataFrame}` (3.9); `{}` sem o registro |
| `fontes` | `dict` | vazio no arquivo; montado pela Geração do relatório |
| `serie_diaria`, `vazoes_anuais` | `DataFrame` | dados das figuras 01 e 05 (3.3) |

### 3.3 Base de EVT

**`cobertura`** (`analisar_cobertura`):

| Chave | Tipo | Descrição |
|---|---|---|
| `inicio`, `fim` | `Timestamp` | primeiro e último registro |
| `horas_observadas` | `int` | registros |
| `horas_esperadas` | `int` | horas da grade horária contínua entre `inicio` e `fim` |
| `horas_faltantes` | `list[Timestamp]` | horas da grade sem registro |
| `duplicadas` | `int` | instantes repetidos |
| `por_ano` | `DataFrame` | uma linha por ano: `ano` (int), `primeiro_registro`, `ultimo_registro` (datetime), `horas_observadas` (int), `horas_calendario` (8.760 ou 8.784), `cobertura_pct` (float), `ano_parcial` (bool) |
| `anos_parciais`, `anos_completos` | `list[int]` | anos com e sem a marca de parcial |
| `agentes` | `DataFrame` | uma linha por agente, na ordem do primeiro registro: `nom_agente`, `primeiro_registro`, `ultimo_registro`, `horas` |
| `identificacao` | `dict[str, str]` | `id_subsistema`, `nom_subsistema`, `nom_bacia`, `nom_rio`, `nom_reservatorio`, `cod_usina`: valores distintos unidos por " / " |
| `arquivos` | `dict` | resumo da auditoria da extração (`{}` sem ela): `total`; `com_registros` (status `PROCESSADO`); `sem_registros` (períodos dos arquivos `SEM_REGISTROS`, como "2015" ou "01/2024"); `falhas` (nomes dos arquivos `FALHA`); `divergencias` (soma de `registros_codigo_sem_nome` e `registros_nome_sem_codigo`) |
| `manifesto` | `dict` | resumo do manifesto da EVT (`{}` sem ele): `arquivos`, `ultima_modificacao_mais_recente`, `registro_mais_recente_utc` (str) |

**`globais`** (`calcular_indicadores_globais`), com todos os registros, cada hora com o mesmo peso. As somas de MW horários são MWh.

| Chave | Tipo | Descrição |
|---|---|---|
| `horas` | `int` | registros |
| `geracao_media_mwmed`, `disponibilidade_media_mwmed` | `float` | médias de `val_geracao` e `val_disponibilidade` |
| `fator_capacidade_pct`, `disponibilidade_relativa_pct` | `float` | geração média e disponibilidade média ÷ P × 100 |
| `disponibilidade_referencia_pct`, `desvio_disponibilidade_referencia_pp` | `float` | (1 − IP) × (1 − TEIF) × 100 e a diferença da disponibilidade relativa para ela, em p.p. |
| `geracao_sobre_garantia_fisica_pct` | `float` | geração média ÷ garantia física × 100 |
| `energia_gerada_mwh`, `evt_mwh`, `indice_evt_pct` | `float` | Σ geração, Σ EVT e EVT ÷ (geração + EVT) × 100 |
| `horas_com_evt`, `horas_com_evt_pct` | `int`, `float` | horas com EVT > 0 e % das horas |
| `folga_media_com_evt_mw` | `float` | média de `val_folgadegeracao` nas horas com EVT |
| `limiar_plena_carga_mw`, `evt_plena_carga_mwh`, `evt_plena_carga_pct` | `float` | 0,90 × P; EVT nas horas com geração ≥ esse limiar, em MWh e % da EVT |
| `horas_evt_acima_folga` | `int` | horas com EVT − folga > 10⁻⁶ MW |
| `horas_parada_com_evt`, `evt_parada_mwh`, `evt_parada_pct` | `int`, `float` | horas com geração ≤ 1 MW e EVT > 0; EVT nelas, em MWh e % da EVT |
| `disponibilidade_media_nas_paradas_mw` | `float` | disponibilidade média nessas horas |
| `horas_geracao_zero`, `horas_geracao_zero_com_evt` | `int` | horas com geração igual a zero, total e com EVT |
| `horas_geracao_ate_limiar_positiva_com_evt` | `int` | horas paradas com EVT e geração acima de zero |
| `horas_com_anomalia`, `evt_em_registros_anomalos_mwh` | `int`, `float` | registros com `qualidade_registro` ≠ "OK" e a EVT neles |
| `geracao_maxima_registrada_mw`, `instante_geracao_maxima` | `float`, `Timestamp` | maior geração da série (com os sinalizados) e o instante |

**`indicadores_anuais`** (`calcular_indicadores_anuais`): uma linha por ano civil, com todos os registros.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano`, `ano_parcial` | `int`, `bool` | ano civil e marca de parcial (da cobertura) |
| `horas_observadas`, `cobertura_pct` | `int`, `float` | registros e % das horas do ano civil |
| `geracao_media_mwmed`, `disponibilidade_media_mwmed` | `float` | médias do ano |
| `fator_capacidade_pct`, `disponibilidade_relativa_pct` | `float` | ÷ P × 100 |
| `desvio_disponibilidade_referencia_pp` | `float` | disponibilidade relativa − disponibilidade de referência, em p.p. |
| `geracao_sobre_garantia_fisica_pct` | `float` | geração média ÷ garantia física × 100 |
| `energia_gerada_mwh`, `evt_mwh` | `float` | Σ geração e Σ EVT |
| `evt_vertimento_minimo_mwh`, `evt_demais_horas_mwh`, `participacao_vertimento_minimo_pct` | `float` | EVT nas horas com `val_vazaovertida` ≤ vertimento mínimo, nas demais e a parte da primeira |
| `indice_evt_pct` | `float` | EVT ÷ (geração + EVT) × 100 |
| `horas_com_evt`, `horas_com_evt_pct` | `int`, `float` | horas com EVT > 0 e % das horas |
| `horas_parada_com_evt`, `evt_parada_mwh` | `int`, `float` | usina parada com EVT e a EVT nessas horas |
| `horas_indisponibilidade_total`, `horas_disponibilidade_ate_metade` | `int` | disponibilidade ≤ 0,001 MW; disponibilidade acima de 0,001 MW e até P ÷ 2 |
| `evt_media_diurna_mw`, `evt_media_noturna_mw`, `razao_evt_diurna_noturna` | `float` | EVT média nas janelas diurna e noturna e a razão (vazia com denominador zero) |
| `geracao_media_diurna_mw`, `geracao_media_noturna_mw`, `razao_geracao_diurna_noturna` | `float` | idem para a geração |
| `horas_com_anomalia` | `int` | registros sinalizados no ano |

**Distribuições e perfis**:

| Tabela | Linha | Colunas |
|---|---|---|
| `evt_mensal` | mês com registros | `mes` (datetime, dia 1), `horas`, `energia_gerada_mwh`, `geracao_media_mw`, `disponibilidade_media_mw`, `evt_mwh`, `evt_vertimento_minimo_mwh`, `evt_demais_horas_mwh` |
| `distribuicao_mes_do_ano` | mês do ano (12 linhas) | `mes` (1 a 12), `mes_nome` (por extenso), `evt_mwh` (só anos completos), `participacao_pct` |
| `evt_por_faixa_geracao` | faixa de geração, na ordem crescente | `faixa_geracao` (rótulo, seção 5.4), `horas` (0 na faixa vazia), `evt_mwh`, `geracao_media_mw`, `disponibilidade_media_mw`, `participacao_evt_pct` |
| `perfil_horario_geracao`, `perfil_horario_evt` | ano (índice `ano`) | colunas `0` a `23` (hora do dia): médias de `val_geracao` e de `val_energiavertidaturbinavel` |
| `horas_geracao_zero` | ano | `ano`; `jan` a `dez` (horas com geração igual a zero; vazio no mês sem registros); `total`; `com_disponibilidade_zero` (disponibilidade ≤ 0,001 MW); `com_usina_disponivel` (`total` − `com_disponibilidade_zero`) |
| `serie_diaria` | dia civil (índice `din_instante`) | médias diárias de `val_disponibilidade`, `val_geracao` e `val_energiavertidaturbinavel` (figura 01) |
| `vazoes_anuais` | ano (índice `ano`) | médias de `val_vazaoturbinada`, `val_vazaovertidaturbinavel` e `val_vazaovertidanaoturbinavel` (figura 05) |

**Eventos** (`identificar_eventos`): uma linha por evento, em ordem cronológica.

| Tabela | Condição da hora | Colunas |
|---|---|---|
| `eventos_parada_com_evt` | geração ≤ 1 MW e EVT > 0 | `inicio`, `fim` (datetime), `duracao_h` (int), `geracao_media_mw`, `disponibilidade_media_mw`, `vazao_vertida_media_m3s`, `evt_mwh` |
| `eventos_indisponibilidade_total` | disponibilidade ≤ 0,001 MW | `inicio`, `fim`, `duracao_h`, `vazao_vertida_media_m3s`, `geracao_media_mw` |

**`mudanca_classificacao`** (`detectar_mudanca_classificacao`): sem mês detectado, só `{"mes": None}`.

| Chave | Tipo | Descrição |
|---|---|---|
| `mes` | `Period[M]` | mês seguinte ao último mês com mediana de `val_vazaovertidanaoturbinavel` não positiva |
| `meses_antes`, `meses_depois` | `int` | meses da série antes do mês e a partir dele |
| `turbinavel_tipica_antes_m3s` | `float` | mediana de `val_vazaovertidaturbinavel` nas horas de vertimento mínimo antes do mês |
| `nao_turbinavel_tipica_depois_m3s` | `float` | mediana de `val_vazaovertidanaoturbinavel` nas horas de vertimento mínimo a partir do mês |
| `evt_media_vertimento_minimo_antes_mw` | `float` | EVT média nas horas de vertimento mínimo antes do mês |
| `pct_horas_vertimento_minimo_turbinavel_antes` | `float` | % das horas anteriores com vertimento mínimo e vazão turbinável positiva |

**Registros sinalizados, perfil estatístico e extremos**:

| Tabela | Linha | Colunas |
|---|---|---|
| `anomalias` | registro sinalizado, em ordem cronológica | `din_instante`, `qualidade_registro` (regras violadas), `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_produtividade`, `val_energiavertida`, `val_energiavertidaturbinavel` |
| `resumo_anomalias` | regra R6 a R9 | `regra`, `descricao`, `horas`, `primeira_ocorrencia`, `ultima_ocorrencia` (vazias sem horas), `evt_mwh` |
| `validacao` | regra R1 a R9 | colunas de `validacao_fisica.csv` (`codigo_regra`, `grupo`, `nome_regra`, `expressao`, `total_linhas`, `conformes`, `violacoes`, `taxa_conformidade_pct`, `desvio_maximo`, `desvio_medio`, `status`) |
| `perfil_estatistico` | ano × grandeza com valor | `ano`, `variavel`, `unidade`, `registros_considerados`, `media`, `desvio_padrao` (amostral; 0 com um registro), `mediana`, `percentil_25`, `percentil_75`, `soma_acumulada`, `valor_minimo`, `data_hora_min`, `valor_maximo`, `data_hora_max`; valores com 4 casas, soma com 2, datas em texto "AAAA-MM-DD HH:MM:SS" |
| `extremos` | grandeza | `variavel`, `unidade`, `maximo_historico`, `data_hora_max`, `minimo_historico`, `data_hora_min`; valores com 4 casas, datas em texto |

As grandezas são as 10 de `OPERATIONAL_METRIC_COLUMNS`. A unidade vem de `evt.UNIDADES`: MWmed para geração, disponibilidade, folga, energia vertida e EVT; m³/s para as vazões; MW/(m³/s) para a produtividade.

### 3.4 Indicadores oficiais (`ons`, `analisar_indicadores_ons`)

| Chave | Tipo | Quando | Conteúdo |
|---|---|---|---|
| `disp_anual` | `DataFrame` | há `ug_mensal` | por ano: `ano`, `ano_parcial`, `disponibilidade_declarada_pct` (disponibilidade relativa do ano), `dispf_pct`, `indisppf_pct`, `indispff_pct` (médias ponderadas), `desvio_dispf_referencia_pp` |
| `disp_periodo` | `dict` | há `ug_mensal` | `mes_inicio`, `mes_fim` (Timestamp), `unidades` (int), `dispf_pct`, `indisppf_pct`, `indispff_pct` |
| `ug_anual` | `DataFrame` | há `ug_anual` | colunas do Tratamento (`ano`, `ug`, `cod_equipamento`, `potencia_mw`, `dispf`, `indisppf`, `indispff`, `dmdff`, `fdff`, `tdff`, `id_usina`, `agente`, `modalidade`, `arquivo_origem`) + `ano_parcial` (da cobertura da base de EVT) |
| `horas_mensal` | `DataFrame` | há `horas_estado` | colunas do Tratamento (`mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HDCE`, `HEDP`, `HEDF`, `num_versao`, `residuo_identidade_h`, `potencia_mw`) + `ano` |
| `horas_anual` | `DataFrame` | há `horas_estado` | por ano e unidade: `ano`, `ug`, somas de `HP` a `HEDF`, `meses` (int), `ano_parcial` (menos de 12 meses) |
| `horas_periodo` | `dict` | há `horas_estado` | `mes_inicio`, `mes_fim`, `identidade_fora` (meses-unidade com \|`residuo_identidade_h`\| > 0,1 h), `meses_unidade` |
| `taxas` | `DataFrame` | há `taxas` | `mes`, `teifa`, `teip` (frações), `num_versao`, `din_calculo` |
| `taxa_ultima` | `dict` | há `taxas` | `mes` (o mais recente), `teifa_pct`, `teip_pct`, `disponibilidade_verificada_pct` = (1 − TEIFa) × (1 − TEIP) × 100 |
| `recalculo_taxas` | `DataFrame` | há `taxas`, horas e a tabela `recalculo` da conferência `teifa_teip` | tabela `recalculo` da Conferência: `mes`, `meses_na_janela`, `teifa_publicada`, `teifa_recalculada`, `teip_publicada`, `teip_recalculada`, `diferenca_teifa_pp`, `diferenca_teip_pp` |
| `recalculo_resumo` | `dict` | idem | contagem da conferência `teifa_teip`: `meses` (`comparados`: janela de 60 meses completa e as quatro taxas com valor), `reproduzidos` (`coincidentes`: as duas diferenças ≤ 0,001 p.p.) e `diferenca_maxima_pp` (maior \|diferença\|). Numa chamada direta, ou com a conferência não aplicável, vem de `conferencia.indicadores.reproducao_das_taxas`, com a mesma regra |
| `decomposicao` | `DataFrame` | o mês de `taxa_ultima` tem recálculo | uma linha por taxa × unidade × parcela: `taxa` (`TEIFa`, `TEIP`), `ug`, `parcela`, `horas` (soma na janela, sem ponderar), `contribuicao_pp`, `participacao_pct` |
| `divergencias` | `DataFrame` | sempre (vazio sem divergência) | tabela da conferência `dispf_horas`: `mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `horas_programadas_indisppf`, `HDF`, `horas_forcadas_indispff`, `diferenca_programada_h`, `diferenca_forcada_h` |

Ponderações:
- **DISPF** (`_media_ponderada`): peso = horas da base de EVT no mês × `potencia_mw` (sem potência, `parametros.potencia_unitaria_mw`); só os meses presentes na base de EVT.
- **Decomposição**: janela de `JANELA_TAXAS_MESES` meses (`conferencia.indicadores.janela`); peso = `potencia_mw`, ou 1 sem potência (`peso`). Contribuição em p.p. = Σ peso × horas da parcela ÷ base × 100, com base Σ peso × (HP − HDP − HEDP) na TEIFa e Σ peso × HP na TEIP. Participação = contribuição ÷ soma das contribuições da taxa × 100.

### 3.5 Programação (`programacao`, `analisar_programacao`)

| Chave | Tipo | Conteúdo |
|---|---|---|
| `periodo` | `dict` | resumo do período comum (tabela abaixo) |
| `mensal` | `DataFrame` | por mês: `mes` (datetime), `horas_comuns`, `horas_parada_evt_programacao_zero`, `horas_parada_evt_programacao_positiva`, `horas_parada_sem_evt`, `horas_gerando_programacao_zero`, `horas_gerando_com_programacao`, `horas_parada_com_evt`, `evt_mwh`, `evt_parada_programacao_zero_mwh`, `participacao_evt_programacao_zero_pct`, `horas_desvio_programacao`, `disponibilidade_media_parada_programacao_zero_mw`, `desvio_medio_absoluto_mw` |
| `eventos` | `DataFrame` | eventos de desvio: `inicio`, `fim`, `duracao_h`, `programacao_media_mw`, `disponibilidade_media_mw`, `evt_mwh` |
| `perfil` | `DataFrame` | 24 linhas: `hora`, `horas` e `evt_mwh` das horas paradas com EVT e programação de até 1 MW (zero sem ocorrência) |
| `dias_ausentes` | `DataFrame` | `dia` |
| `auditoria` | `DataFrame` | da Coleta: `arquivo`, `dia`, `linhas_lidas`, `linhas_usina`, `linhas_codigo_sem_conferencia`, `patamares`, `data_interna_confere`, `status` |
| `classificadas` | `DataFrame` | uma linha por hora comum: `din_instante`, `val_geracao`, `val_energiavertidaturbinavel`, `val_disponibilidade`, `geracao_programada_mw`, `classe`, `desvio_programacao` (bool) |

`periodo`:

| Chave | Tipo | Descrição |
|---|---|---|
| `primeiro_dia`, `ultimo_dia` | `Timestamp` | dias da primeira e da última hora programada |
| `dias_com_arquivo` | `int` | dias distintos na programação horária |
| `dias_ausentes`, `lista_dias_ausentes` | `int`, `list[Timestamp]` | dias sem arquivo |
| `horas_comuns` | `int` | horas classificadas (base de EVT ∩ programação com valor) |
| `horas_base_sem_programacao` | `int` | horas da base de EVT no período da programação sem valor programado |
| `horas_parada_com_evt`, `horas_parada_evt_programacao_zero`, `pct_horas_programacao_zero` | `int`, `int`, `float` | horas paradas com EVT, as com programação de até 1 MW e o percentual |
| `disponibilidade_media_programacao_zero_mw` | `float` | disponibilidade declarada média nessas horas |
| `evt_horas_comuns_mwh`, `evt_programacao_zero_mwh`, `pct_evt_programacao_zero` | `float` | EVT das horas comuns, das paradas com programação de até 1 MW e o percentual |
| `pct_horas_zero_janela_diurna` | `float` | parte dessas horas na janela diurna |
| `horas_desvio`, `eventos_desvio` | `int` | horas e eventos de desvio |
| `maior_evento` | linha de `eventos` ou `None` | o evento de desvio mais longo |
| `horas_gerando_programacao_zero` | `int` | geração > 1 MW com programação de até 1 MW |
| `correlacao_geracao_programacao`, `desvio_medio_absoluto_mw` | `float` | correlação de Pearson horária e média de \|geração − programação\| |

### 3.6 Disponibilidade (`disponibilidade`, `analisar_disponibilidade`)

| Chave | Tipo | Conteúdo |
|---|---|---|
| `resumo` | `dict` | `inicio`, `fim`, `horas`, `horas_sinalizadas` (qualidade ≠ "OK"), `meses_sem_usina` (início de cada mês inteiro ausente), `horas_ausentes`; `horas_paradas`, `horas_paradas_sem_sincronizacao`, `horas_paradas_sincronizadas`, `pct_paradas_sem_sincronizacao`; `horas_parada_evt`, `horas_parada_evt_sem_sincronizacao`; `horas_parada_evt_programacao_zero`, `horas_parada_evt_programacao_zero_sem_sincronizacao` |
| `conferencia` | `dict` | da Conferência: `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes`, `so_ons_disponibilidade`, `so_base_evt`, `horas_sinalizadas_excluidas`, `tolerancia_mw` |
| `divergencias` | `DataFrame` | da Conferência, períodos contínuos: `inicio`, `fim`, `horas`, `diferenca_media_mw`, `diferenca_maxima_mw` |
| `horas_paradas` | `DataFrame` | uma linha por hora comum parada: `din_instante`, `val_geracao`, `val_dispoperacional`, `val_dispsincronizada`, `val_energiavertidaturbinavel`, `sincronizacao`, `evt`, `classe_programacao` |
| `classes` | `DataFrame` | por combinação `sincronizacao` × `evt` × `classe_programacao`: `horas`, `evt_mwh` |
| `mensal` | `DataFrame` | por mês (`periodo` = "AAAA-MM"), tabela abaixo |
| `anual` | `DataFrame` | por ano (`periodo` = "AAAA"), tabela abaixo + `ano_parcial` |
| `auditoria`, `ausencias` | `DataFrame` | do Tratamento, como estão |
| `obtido_em` | `str` | data de obtenção (UTC) do manifesto do conjunto; vazio sem registro |

`mensal` e `anual` (horas comuns, sem as horas sinalizadas):

| Coluna | Tipo | Descrição |
|---|---|---|
| `periodo` | `str` | mês ou ano |
| `horas_comuns` | `int` | horas na base de EVT e na disponibilidade |
| `disp_operacional_media_mw`, `disp_declarada_media_mw`, `disp_sincronizada_media_mw`, `geracao_media_mw` | `float` | médias |
| `capacidade_nao_sincronizada_media_mw`, `capacidade_nao_sincronizada_mwh` | `float` | operacional − sincronizada: média e soma |
| `horas_paradas`, `horas_paradas_sem_sincronizacao`, `horas_paradas_sincronizadas` | `int` | geração ≤ 1 MW; sincronizada ≤ 1 MW ou > 1 MW |
| `reserva_desligada_teif_mwh` | `float` | Σ (HRD × `potencia_mw`) das horas por estado; vazio sem horas por estado no período |
| `diferenca_mwh` | `float` | capacidade não sincronizada − reserva desligada; vazio sem reserva |

### 3.7 Hidrologia (`hidrologia`, `analisar_hidrologia`)

Sempre presentes (com a série):

| Chave | Tipo | Conteúdo |
|---|---|---|
| `resumo` | `dict` | `inicio`, `fim`, `horas`, `horas_sinalizadas`, `meses_sem_usina`, `horas_ausentes`; `sinalizadas_por_regra`: `{H1 a H4: {"horas": int, "anos": {ano: horas}}}` |
| `alinhamento` | `DataFrame` | da Conferência (uma linha): `horas_comuns`, `coincidentes_turbinada`, `coincidentes_vertida`, `coincidentes_ambas`, `pct_coincidencia`, `meta_pct`, `tolerancia_m3s`, `deslocamento_aplicado_h`, `confirmado` |
| `auditoria`, `ausencias` | `DataFrame` | do Tratamento |
| `obtido_em` | `str` | data de obtenção do conjunto |
| `publicado` | `bool` | `confirmado` do alinhamento; falso → nenhum dos itens abaixo |

Só com `publicado`:

| Chave | Tipo | Conteúdo |
|---|---|---|
| `faixas` | `DataFrame` | uma linha por hora com EVT no período da hidrologia: `din_instante`, `val_vazaoafluente`, `faixa_afluencia`, `val_energiavertidaturbinavel`, `val_geracao` |
| `faixas_mensal`, `faixas_anual` | `DataFrame` | `periodo` × `faixa_afluencia` (todas as faixas, zero quando vazias): `horas`, `evt_mwh`; a anual tem `ano_parcial` |
| `perfil` | `DataFrame` | `grupo_dias` × `hora`: `dias`, `nivel_montante_medio_m`, `afluencia_media_m3s`, `turbinada_media_m3s`, `vertida_media_m3s` |
| `mensal`, `anual` | `DataFrame` | por `mes` ou `periodo`: `horas`, `afluencia_media_m3s`, `afluencia_maxima_m3s`, `turbinada_media_m3s`, `vertida_media_m3s`, `vertida_nao_turbinavel_media_m3s`, `nivel_montante_min_m`, `nivel_montante_medio_m`, `nivel_montante_max_m`, `nivel_jusante_medio_m`, `volume_util_medio_pct`, `horas_afluencia_acima_engolimento`; a anual tem `ano_parcial` |
| `resumo` (acréscimos) | `dict` | `horas_evt`, `evt_mwh`, `horas_por_faixa` e `evt_por_faixa_mwh` (faixa → valor), `horas_afluencia_acima_engolimento`, `dias_com_parada_evt`, `nivel_min_m`, `nivel_max_m`, `nivel_amplitude_m` (grupo de dias → nível médio horário mínimo, máximo e amplitude), `pico_afluencia` (`instante`, `afluencia_m3s`, `defluencia_m3s`, ou `None`) |

Valores sinalizados: `tratamento.hidrologia.limpos` apaga só o campo afetado. Vazão negativa (H1) apaga a vazão; volume útil fora de 0 a 100 % (H2) apaga o volume; nível a mais de 10 m da mediana da série (H4) apaga o nível. As faixas, o perfil e os resumos mensal e anual usam essa cópia; `horas_afluencia_acima_engolimento` e `pico_afluencia` do `resumo` usam a série como está, em que só afluências não negativas podem passar do engolimento ou ser o pico.

### 3.8 Geração oficial (`geracao_oficial`, `analisar_geracao_oficial`)

| Chave | Tipo | Conteúdo |
|---|---|---|
| `resumo` | `dict` | `inicio`, `fim`, `horas`, `horas_sinalizadas`, `meses_sem_usina`, `horas_ausentes` (`_resumo_serie`) |
| `conferencia` | `dict` | da Conferência: `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes`, `so_ons_geracao`, `so_base_evt`, `energia_ons_geracao_mwh`, `energia_base_evt_mwh`, `tolerancia_mw` |
| `mensal` | `DataFrame` | da Conferência: `mes` ("AAAA-MM"), `energia_base_evt_mwh`, `energia_ons_geracao_mwh`, `diferenca_mwh` (série oficial − base de EVT), `horas_so_base_evt`, `horas_so_ons_geracao` |
| `anual` | `DataFrame` | soma da mensal por `ano` (str) + `ano_parcial` |
| `divergencias` | `DataFrame` | da Conferência: `inicio`, `fim`, `horas`, `diferenca_media_mw`, `diferenca_maxima_mw` |
| `auditoria`, `ausencias` | `DataFrame` | do Tratamento |
| `obtido_em` | `str` | data de obtenção do conjunto |

### 3.9 Cadastro e dicionários

| Campo | Tipo | Conteúdo |
|---|---|---|
| `cadastro["ficha"]` | `dict` | `nom_usina`, `ceg`, `id_ons`, `nom_modalidadeoperacao`, `sgl_centrooperacao`, `nom_pontoconexao`, `val_potenciaautorizada`, `id_estado`, `sts_aneel`, `data_consulta_utc`, `arquivo_origem`, `homonimos`, `linhas_so_identificador`, `linhas_so_conferencia`, `divergencias` |
| `cadastro["divergencias"]` | `str` | texto das divergências da Conferência, separadas por "; "; vazio sem divergência |
| `cadastro["obtido_em"]` | `str` | `data_consulta_utc` da ficha |
| `cadastro["auditoria"]` | `DataFrame` | `arquivo`, `formato`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia`, `status`, `mensagem` |
| `dicionarios["registro"]` | `DataFrame` | `dicionarios.csv` da Coleta, como está (`conjunto`, `pasta`, `formato`, `arquivo`, `url`, `resultado_ultima_obtencao`, `obtido_em_utc`, `sha256`, `tamanho_bytes`, `versoes_anteriores`, `ultima_versao_anterior`) |

### 3.10 Constatações (`achados`, `montar_achados`)

Lista de `(título, texto)`, nesta ordem; os títulos são fixos.

| # | Título | Função | Gerada quando |
|---|---|---|---|
| 1 | Cobertura dos dados | `_achado_cobertura` | sempre |
| 2 | Cadastro da usina no ONS | `_achado_cadastro` | `cadastro["divergencias"]` não vazio |
| 3 | Disponibilidade | `_achado_disponibilidade` | sempre |
| 4 | Indicadores oficiais de disponibilidade (ONS) | `_achado_indicadores_ons` | há `ons["disp_periodo"]` |
| 5 | Estados operativos das unidades geradoras (ONS) | `_achado_estados_operativos` | há `ons["horas_periodo"]` |
| 6 | Indisponibilidades | `_achado_indisponibilidade` | sempre |
| 7 | Geração e garantia física | `_achado_geracao` | sempre |
| 8 | Energia vertida turbinável | `_achado_evt` | sempre |
| 9 | EVT e nível de geração | `_achado_evt_nivel_geracao` | sempre |
| 10 | EVT com a usina parada | `_achado_paradas` | sempre |
| 11 | Programação diária do ONS | `_achado_programacao` | há `programacao["periodo"]` |
| 12 | Disponibilidade sincronizada | `_achado_disponibilidade_sincronizada` | há `disponibilidade` |
| 13 | Afluência e vertimento | `_achado_afluencia` | há `hidrologia` (sem `publicado`, só a cobertura e a conferência) |
| 14 | Horas com geração zero | `_achado_geracao_zero` | sempre |
| 15 | Concentração diurna | `_achado_perfil_diurno` | sempre |
| 16 | Distribuição ao longo do ano | `_achado_sazonalidade` | sempre (sem anos completos com EVT, diz que não há como avaliar) |
| 17 | Mudança de classificação do vertimento pelo ONS | `_achado_mudanca_classificacao` | há `mudanca_classificacao["mes"]` (mudança detectada) |
| 18 | Conferência da geração | `_achado_conferencia_geracao` | a conferência da geração tem `divergentes`, `so_ons_geracao` ou `so_base_evt` > 0 |
| 19 | Qualidade dos dados | `_achado_qualidade` | sempre |

Na constatação 5, a frase da reprodução da TEIFa e da TEIP usa `recalculo_resumo`: "nos N meses com janela de 60 meses completa" quando `reproduzidos` = `meses`; senão, "em X dos N meses …", com a tolerância de 0,001 p.p. Sem meses comparados, a frase não aparece.

Na São Domingos: 17 constatações (sem a 2 e a 18), com 21 dos 21 meses reproduzidos. `texto_conferencia_geracao` e `_texto_alinhamento` também são usadas pela Geração do relatório, no texto das seções de geração e de hidrologia.

### 3.11 Conclusão (`conclusao`, `montar_conclusao`)

Item:

| Campo | Tipo | Descrição |
|---|---|---|
| `lista` | `str` | `pontos_atencao`, `possiveis_problemas`, `confirmar_agente` ou `verificar_campo` |
| `ordem` | `int` | posição na lista, de 1 em diante |
| `regra` | `str` | `C1` a `C11` |
| `texto` | `str` | uma frase, sem ponto final, com os números formatados |
| `secoes` | `list[str]` | chaves das seções de origem (seção 5.4), na ordem de citação |

Regras (`REGRAS_CONCLUSAO`, uma função cada; limiares na seção 5.2):

| Regra | Usa | Gera item em | Seções |
|---|---|---|---|
| C1 | `globais`, `indicadores_anuais`, `programacao["periodo"]` | pontos de atenção, a confirmar, a verificar | `eventos`, mais `programacao` quando cita a programação (a verificar: só `eventos`) |
| C2 | `ons["horas_mensal"]`, `taxa_ultima`, `decomposicao` | possíveis problemas, a confirmar, a verificar: um item por unidade, na ordem das unidades | `indicadores_ons` |
| C3 | `hidrologia` com `publicado` | pontos de atenção | `hidrologia` |
| C4 | os dois últimos anos de `indicadores_anuais` | pontos de atenção | `perfil_horario` |
| C5 | `globais`, `ons["disp_periodo"]`, `ons["taxa_ultima"]` | pontos de atenção (um item) | `indicadores_anuais` (disponibilidade declarada) e `indicadores_ons` (DISPF ou taxas) |
| C6 | `programacao["periodo"]` | possíveis problemas, a confirmar, a verificar | `programacao` |
| C7 | `disponibilidade["anual"]`, `ons["divergencias"]` | possíveis problemas, a confirmar | `disponibilidade_sincronizada` (anos) e `indicadores_ons` (meses-unidade); `qualidade` no item a confirmar quando a C8 também dispara |
| C8 | horas da R7 em `resumo_anomalias` | possíveis problemas; a confirmar só quando a C7 não dispara | `qualidade` |
| C9 | `globais`, anos completos de `indicadores_anuais` | pontos de atenção | `indicadores_anuais` |
| C10 | `eventos_indisponibilidade_total`, `ons["ug_anual"]` (anos completos) | a confirmar, a verificar | `disponibilidade_geracao` (evento) e `indicadores_ons` (unidades) |
| C11 | `hidrologia["resumo"]["horas_sinalizadas"]`, horas da R9 | a verificar (um item) | `hidrologia` e `qualidade` |

`montar_conclusao` ordena os itens de forma estável por lista (na ordem de `LISTAS_CONCLUSAO`) e pelo número da regra, e numera `ordem` em cada lista. Todos os itens ficam no arquivo. Na São Domingos: 19 itens (5 pontos de atenção, 4 possíveis problemas, 5 a confirmar e 5 a verificar), com as onze regras.

## 4. Manifesto da etapa (`etapa.json`)

Campos comuns (`etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status`, `codigo_saida`, `etapa_anterior`, `arquivos`, `resumo`) e transições de `status`: [data-model da Coleta](../001-coleta-dados/data-model.md). Nesta etapa:
- `versao_formato` = 1 (`pipeline.VERSAO_FORMATO["analises"]`);
- `etapa_anterior` = `{"etapa": "conferencia", "concluida_em": …}`;
- `arquivos` = `resultados.pkl`, com `bytes` e `sha256`, mesmo quando o conteúdo não mudou;
- em erro: `status` `falha`, `codigo_saida` 1, `arquivos` vazio e `resumo` = `{"erro": "<mensagem>"}`; na interrupção pelo usuário (Ctrl+C), `{"erro": "interrompida pelo usuário"}`.

`resumo` (`executar_analises`):

| Campo | Tipo | Conteúdo |
|---|---|---|
| `periodo.inicio`, `periodo.fim` | `str` | primeiro e último registro da base de EVT ("AAAA-MM-DD HH:MM:SS") |
| `horas_analisadas` | `int` | registros da base de EVT (`cobertura["horas_observadas"]`) |
| `constatacoes` | `int` | quantidade de constatações |
| `conclusao` | `dict` | itens por lista, com as chaves em ordem alfabética; lista sem item não aparece |
| `regras_da_conclusao` | `list[str]` | regras com ao menos um item, em ordem numérica |
| `bases_complementares` | `dict[str, bool]` | `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao`, `cadastro`: verdadeiro quando o resultado da base foi preenchido (a hidrologia, mesmo sem a meta) |

Na São Domingos:

```json
"resumo": {
 "periodo": {"inicio": "2018-08-28 00:00:00", "fim": "2026-09-28 23:00:00"},
 "horas_analisadas": 70895,
 "constatacoes": 17,
 "conclusao": {"confirmar_agente": 5, "pontos_atencao": 5, "possiveis_problemas": 4, "verificar_campo": 5},
 "regras_da_conclusao": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11"],
 "bases_complementares": {"indicadores": true, "programacao": true, "disponibilidade": true,
                          "hidrologia": true, "geracao": true, "cadastro": true}
}
```

## 5. Regras, estados e validações

### 5.1 Regras gerais

Iguais para qualquer usina; o perfil não as altera.

| Regra | Valor | Onde |
|---|---|---|
| Usina parada; programação zero | geração ≤ 1 MW; programação ≤ 1 MW | `LIMIAR_GERACAO_PARADA_MW` (`src/comum/regras.py`) |
| Hora com EVT | `val_energiavertidaturbinavel` > 0 | `analises.comum._mascara_evt` |
| Indisponibilidade total | disponibilidade ≤ 0,001 MW | `LIMIAR_INDISPONIBILIDADE_TOTAL_MW` |
| Disponibilidade até a metade | > 0,001 MW e ≤ P ÷ 2 | `calcular_indicadores_anuais` |
| Plena carga | geração ≥ 0,90 × P | `FRACAO_PLENA_CARGA` |
| EVT acima da folga de geração | EVT − folga > 10⁻⁶ MW | literal em `calcular_indicadores_globais` |
| Janelas horárias (hora de início) | diurna 9h a 15h; noturna 20h a 5h | `HORAS_DIURNAS`, `HORAS_NOTURNAS` |
| Concentração diurna | razão diurna ÷ noturna ≥ 2 | `RAZAO_DIURNA_RELEVANTE` |
| Evento | horas consecutivas, de hora em hora | `identificar_eventos`, `eventos_desvio` |
| Indisponibilidade longa (constatação 6) | evento ≥ 24 h | `DURACAO_MINIMA_EVENTO_RELATORIO_H` |
| Desvio da programação | usina parada com programação > 5 MW | `LIMIAR_DESVIO_PROGRAMACAO_MW` |
| Unidade sincronizada | disponibilidade sincronizada > 1 MW | `LIMIAR_SINCRONIZADA_MW` |
| Janela da TEIFa e da TEIP | 60 meses | `JANELA_TAXAS_MESES` |
| Identidade das horas por estado | \|`residuo_identidade_h`\| ≤ 0,1 h | `TOLERANCIA_IDENTIDADE_HORAS` |
| DISPF × horas contido na reserva desligada (constatação 5) | horas de INDISPPF − HDP ≤ HRD + 1 h | `TOLERANCIA_DIVERGENCIA_HORAS` |
| Mês com a TEIFa e a TEIP reproduzidas (constatação 5) | as duas diferenças ≤ 0,001 p.p., contado pela Conferência | `TOLERANCIA_REPRODUCAO_TAXAS_PP` |
| Não sincronizada × reserva desligada (constatação 12) | coincide com \|diferença\| ≤ 100 MWh (0,1 GWh) | literal em `_achado_disponibilidade_sincronizada` |
| Distribuição ao longo do ano | anos completos; maio a outubro × janeiro a abril; 3 meses de maior EVT | `MESES_MAIO_A_OUTUBRO`, `MESES_JANEIRO_A_ABRIL` (`constatacoes.py`) |
| Ano parcial | primeiro registro depois de 1º/jan 00h ou último antes de 31/dez 23h | `analisar_cobertura` |
| Horas ausentes citadas (constatação 1) | até 5 | literal em `_achado_cobertura` |

### 5.2 Limiares da conclusão (`src/comum/regras.py`)

| Constante | Valor | Regra e condição |
|---|---|---|
| `LIMIAR_CONCLUSAO_EVT_PARADA_PCT` | 10,0 | C1: `evt_parada_pct` ≥ 10 |
| `LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT` | 50,0 | C1 cita a programação quando `pct_horas_programacao_zero` ≥ 50 |
| `LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA` | 2/3 | C2 (a): TEIFa mais recente acima da TEIF de referência e participação da unidade (HDF + HEDF) ≥ 2/3 |
| `LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT` | 50,0 | C2 (b): meses com HEDF > 0 ÷ meses com horas por estado ≥ 50 % |
| `LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT` | 80,0 | C3: horas com EVT até uma unidade e entre uma e N unidades ≥ 80 % das horas com EVT (inclusive sem dado) |
| `RAZAO_DIURNA_RELEVANTE` | 2,0 | C4: razão diurna ÷ noturna da EVT num dos dois últimos anos |
| referências do perfil | — | C5: disponibilidade declarada ou DISPF abaixo da disponibilidade de referência; TEIFa acima da TEIF de referência; TEIP acima do IP de referência |
| `LIMIAR_DESVIO_PROGRAMACAO_MW` | 5,0 | C6: ao menos um evento de desvio |
| `LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH` | 5,0 | C7: \|`diferenca_mwh`\| ≥ 5.000 MWh num ano (anos sem reserva não entram); ou ao menos um mês-unidade divergente |
| `LIMIAR_CONCLUSAO_R7_HORAS` | 100 | C8: horas da regra R7 |
| 100 % (literal) | — | C9: geração média abaixo de 100 % da garantia física; ou, com ao menos dois anos completos, EVT do último ano completo ≥ a de todos os anos completos |
| `LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS` | 30 | C10: evento de indisponibilidade total ≥ 30 × 24 h |
| `LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT` | 20,0 | C10: `indisppf` anual de uma unidade ≥ 20 num ano completo |
| `LIMIAR_CONCLUSAO_R9_HORAS` | 24 | C11: horas da regra R9; ou dados hidrológicos com alguma hora sinalizada |
| `MAXIMO_ITENS_CONCLUSAO` | 5 | itens por lista no PDF e no Markdown, aplicado pela Geração do relatório |

### 5.3 Versões de formato

| Onde | Valor | Conferida por |
|---|---|---|
| `resultados.pkl` → `versao_formato` | 1 (`src/analises/resultados.VERSAO_FORMATO`) | `carregar_resultados` (Geração do relatório) |
| `etapa.json` → `versao_formato` | 1 (`src/pipeline.VERSAO_FORMATO`) | pré-requisito da Geração do relatório |
| `conferencias.pkl` → `versao_formato` | 1 | `carregar_conferencias`, na leitura das entradas |

### 5.4 Enumerações e rótulos

- **`qualidade_registro`** (base de EVT): `OK` ou as regras violadas (`R6` a `R9`) separadas por ";".
- **Faixas de geração** (`faixa_geracao`): "até 1 MW (usina parada)"; "de a a b MW" para cada intervalo do perfil (limites sem casas decimais); "de <último limite> a <plena carga> MW"; "<plena carga> MW ou mais (plena carga)", com a plena carga numa casa decimal (na São Domingos, "de 40 a 43,2 MW" e "43,2 MW ou mais (plena carga)").
- **Classes da programação** (`classe`, `DESCRICAO_CLASSES`; o "1 MW" das descrições vem de `LIMIAR_GERACAO_PARADA_MW`):

  | Código | Descrição | Condição |
  |---|---|---|
  | `PARADA_EVT_PROGRAMACAO_ZERO` | usina parada com EVT e programação de até 1 MW | geração ≤ 1, EVT > 0, programação ≤ 1 |
  | `PARADA_EVT_PROGRAMACAO_POSITIVA` | usina parada com EVT e programação acima de 1 MW | geração ≤ 1, EVT > 0, programação > 1 |
  | `PARADA_SEM_EVT` | usina parada sem EVT | geração ≤ 1, EVT = 0 |
  | `GERANDO_PROGRAMACAO_ZERO` | usina gerando com programação de até 1 MW | geração > 1, programação ≤ 1 |
  | `GERANDO_COM_PROGRAMACAO` | usina gerando com programação acima de 1 MW | geração > 1, programação > 1 |

- **Horas paradas da disponibilidade**: `sincronizacao` = `SINCRONIZADA` ou `NAO_SINCRONIZADA`; `evt` = `COM_EVT` ou `SEM_EVT`; `classe_programacao` = uma das cinco classes acima ou `SEM_PROGRAMACAO` (hora sem classe da programação: fora do período da programação ou, dentro dele, sem valor programado, como as dos dias sem arquivo), que o relatório apresenta como "sem programação: fora do período ou sem valor programado".
- **Faixas de afluência** (`faixa_afluencia`, `faixas_afluencia()`), em ordem:

  | Código | Condição |
  |---|---|
  | `ATE_UMA_UNIDADE` | afluência ≤ engolimento por unidade |
  | `ENTRE_UMA_E_<N>_UNIDADES` | engolimento por unidade < afluência ≤ engolimento máximo |
  | `ACIMA_ENGOLIMENTO_USINA` | afluência > engolimento máximo |
  | `SEM_DADO_HIDROLOGICO` | afluência vazia, apagada por sinalização ou hora ausente na hidrologia |

  `<N>` é o número de unidades por extenso, no feminino, sem acento e em maiúsculas (`numero_por_extenso`): `DUAS` para 2, `TRES` para 3; acima de 10, em algarismos.
- **Grupos de dias** (`grupo_dias`): `COM_PARADA_EVT` (dia com ao menos uma hora de usina parada com EVT na base de EVT) e `DEMAIS`.
- **Qualidade das séries complementares**: `OK` ou as regras violadas separadas por "," (disponibilidade: `D1` a `D4`; hidrologia: `H1` a `H4`).
- **Parcelas das taxas** (`DESCRICAO_PARCELA`): `HDF` (desligamentos forçados) e `HEDF` (operação com limitação forçada de potência), na TEIFa; `HDP` (desligamentos programados) e `HEDP` (operação com limitação programada de potência), na TEIP.
- **Listas da conclusão** (`LISTAS_CONCLUSAO`): `pontos_atencao` "Pontos de atenção", `possiveis_problemas` "Possíveis problemas", `confirmar_agente` "A confirmar com o agente", `verificar_campo` "A verificar em campo". As frases `FRASE_ABERTURA_CONCLUSAO` e `FRASE_CONCLUSAO_VAZIA` ficam em `conclusao.py` e são usadas só pela Geração do relatório.
- **Seções citadas pelos itens** (chaves das seções do relatório): `eventos`, `programacao`, `indicadores_ons`, `hidrologia`, `perfil_horario`, `indicadores_anuais`, `disponibilidade_geracao`, `disponibilidade_sincronizada` e `qualidade`.

### 5.5 Estados: o que existe em cada execução

| Resultado | Preenchido quando | Sem a condição |
|---|---|---|
| `ons` | os quatro CSV de indicadores existem | `{}`; constatações 4 e 5 e regras C2, C10 (unidades) e parte da C5 e da C7 omitidas |
| `programacao` | a programação horária existe e tem horas | `{}`; constatação 11, C6 e a parcela de programação da C1 omitidas |
| `disponibilidade` | a série existe e tem horas | `{}`; constatação 12 e a parte anual da C7 omitidas |
| `hidrologia` | a série existe e tem horas | `{}`; constatação 13, C3 e a parte hidrológica da C11 omitidas |
| cruzamentos hidrológicos | `hidrologia["publicado"]` | só o resumo e a conferência; C3 não dispara; C11 continua a usar as sinalizações |
| `geracao_oficial` | a série existe e tem horas | `{}`; constatação 18 omitida |
| `cadastro` | a ficha existe e tem linha | `{}`; constatação 2 omitida |
| `ons["decomposicao"]` | o mês da TEIFa mais recente tem a janela de 60 meses completa | sem decomposição; C2 só pela limitação forçada |
| `mudanca_classificacao["mes"]` | mês detectado | `None`; constatação 17 omitida, e a figura de EVT mensal sai sem a linha do mês |

### 5.6 Validações e invariantes

Invariantes do cálculo, conferidos nos testes:
- a soma de `horas_observadas` dos anos é o número de registros, e `globais["evt_mwh"]` é a soma da EVT horária;
- a EVT das faixas de geração soma a EVT total, e `participacao_evt_pct` soma 100;
- o `total` de `horas_geracao_zero` soma as horas com geração igual a zero;
- as classes da programação somam `horas_comuns`, e as horas paradas com EVT se dividem entre as duas classes de parada com EVT;
- as combinações de `classes` da disponibilidade somam `horas_paradas`;
- as faixas de afluência somam as horas com EVT do período da hidrologia;
- nenhum registro sinalizado entra em `perfil_estatistico` nem em `extremos`;
- itens da conclusão: ordenados por lista e regra; `ordem` de 1 em diante; ao menos uma seção; texto de uma frase, sem ponto final, sem os termos "satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente" e "culpa", e sem frase de constatação com 40 caracteres ou mais.
