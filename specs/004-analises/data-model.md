# Data Model: Análises

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-23

Pastas relativas a `data/usinas/<slug>/`, salvo indicação. Tipos: `int`, `float`, `bool`, `str`, `datetime` (coluna de data e hora), `Timestamp` (valor de data e hora), `Period[M]` (mês), `list`, `dict` e `DataFrame` (tabela pandas). "Hidrelétrica com EVT" é a UHE, PCH ou CGH cuja série de referência é a energia vertida turbinável; as demais são as "usinas sem EVT".

## 1. Entradas

### 1.1 Arquivos lidos

**Hidrelétrica com EVT**: lidos por `src/analises/etapa.carregar_entradas`, salvo indicação. As Análises não alteram nenhum arquivo e não leem nada de `data/raw/`.

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
| `coleta/datas_obtencao.csv` | Coleta | `datas_da_coleta` | por conjunto: `arquivos_registrados`, `publicacao_mais_recente` e `obtencao_mais_recente` (→ `datas_obtencao`; resumo do manifesto da EVT na cobertura; `obtido_em` das bases complementares) |

**Usina sem EVT**: lidos por `src/analises/etapa.carregar_entradas_sem_evt`; os da hidrelétrica com EVT que se repetem (indicadores, programação, `conferencias.pkl`, ficha e auditoria do cadastro, `auditoria_programacao.csv`, `dicionarios.csv` e `datas_obtencao.csv`) são lidos do mesmo modo. A EVT, `validacao_fisica.csv` e as séries de disponibilidade e de geração (exceto no caso abaixo) não são lidas: a disponibilidade e a geração vêm da base horária comum.

| Arquivo | Gravado por | Lido por | O que as Análises usam |
|---|---|---|---|
| `tratamento/base_horaria.csv` | Tratamento | `carregar_base_horaria` | `din_instante`, `geracao_mw`, `nivel`, `disponibilidade_operacional_mw`, `disponibilidade_sincronizada_mw`, `geracao_programada_mw`, `trecho`, `sinalizacoes` (→ `comum`) |
| `tratamento/geracao_ausencias.csv` ou, com a restrição com detalhe como série de referência, `restricao_ausencias.csv` | Tratamento | `carregar_entradas_sem_evt` | horas ausentes da série de referência |
| `tratamento/hidrologia_horaria.csv` (com ausências e auditoria) | Tratamento | `carregar_hidrologia_tratada` | hidrelétrica sem EVT (→ `hidrologia`, seção 3.17) |
| `tratamento/despacho_horario.csv`, `despacho_unidades_horario.csv`, `cvu_semanal.csv`, `cmo_semanal.csv` | Tratamento | `carregar_despacho_tratado`, `carregar_semanal_tratado` | térmicas (→ `termica`, seção 3.14) |
| `tratamento/fator_capacidade_horario.csv`, `restricao_semi_horaria.csv` | Tratamento | `carregar_renovavel` | eólicas e solares (→ `renovavel`, seção 3.15) |
| `tratamento/geracao_horaria.csv` | Tratamento | `carregar_geracao_tratada` | só com a restrição com detalhe como série de referência: a Geração por usina do conjunto, para a seção do conjunto e a comparação com a programação do conjunto |
| `conferencia/nao_aplicaveis.csv` | Conferência | `carregar_entradas_sem_evt` | `conferencia`, `motivo` (→ `comum["conferencias_nao_aplicaveis"]`) |
| `coleta/etapa.json` | Coleta | `carregar_entradas_sem_evt` | do `resumo`: `linhas_usina_sem_valor` e `linhas_usina_sem_valor_periodo` (`inicio`, `fim`) |
| `coleta/trechos.csv` | Coleta | `carregar_entradas_sem_evt` | trechos do período (→ `trechos`; base dos trechos de composição) |
| `coleta/composicao_conjunto.csv` | Coleta | `carregar_entradas_sem_evt` | usinas do conjunto, com o tipo, as datas e o nome do conjunto |
| `coleta/capacidade_ficha.csv` | Coleta | `agentes_atuais` | agentes proprietário e operador das unidades ativas |
| `coleta/capacidade_membros.csv` | Coleta | `analisar_conjunto` | unidades das usinas do conjunto: `ceg`, `val_potenciaefetiva`, `dat_entradaoperacao`, `dat_desativacao`; ausente nas Coletas mais antigas (a composição sai sem a potência) |
| `coleta/tipo_publicado.csv` | Coleta | `analisar_conjunto` | `trecho`, `inicio`, `fim`, `nom_tipousina`, `nom_tipocombustivel`, `horas` |

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

Nas usinas sem EVT, `conferencias.pkl` traz só as conferências aplicadas (as não aplicáveis ficam em `nao_aplicaveis.csv`):

| Conferência (`id`) | O que segue | Vai para |
|---|---|---|
| `dispf_horas`, `teifa_teip`, `cadastro` | como na hidrelétrica com EVT | `ons` e `cadastro` |
| `programacao_despacho` (G3), `verificada_despacho` (G4) | `aplicavel`, `motivo`, `comparados`, `coincidentes`, `divergentes`, o `resumo` e as tabelas `mensal` e `divergencias` | `termica["conferencias"]` |
| `geracao_fontes` (G1), `soma_conjunto` (G2), `programacao_renovaveis` (G5) | os mesmos campos, mais a tabela `pares` | `renovavel["conferencias"]` |
| `alinhamento_hidrologia` | a tabela `alinhamento` (correlações com −1, 0 e +1 h, horas comuns e `confirmado`) e, sem a conferência, o motivo | `hidrologia["alinhamento"]` e `hidrologia["motivo_alinhamento"]`; `publicado` = `confirmado` |

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
| `usina.tipo` (ou o prefixo do CEG), `usina.modalidade` | `tipo` e `modalidade`; regras do tipo; seções do tipo |
| `[cobertura]` | caminho (série de referência), nível de cada base (`registro.nivel_coletado`) e motivo das omissões |
| `identificacao.ceg`, `identificacao.id_conjunto` | composição do conjunto e peso da usina; texto da série de referência da restrição com detalhe |
| `identificacao.cod_programacao` ou `codigos_programacao` | identificador da programação em `niveis` |
| `usina.nome`, `parametros.potencia_instalada_mw` | constatação "A usina no conjunto" |
| `parametros.garantia_fisica_mwmed` ÷ `potencia_instalada_mw` | regra C18 (eólicas e solares, só com a garantia física) |
| `parametros.ip_referencia`, `parametros.teif_referencia` | nas usinas sem EVT, opcionais: sem eles, a C5 não é avaliada, a C2 só dispara pela limitação forçada recorrente e a distância à referência do DISPF fica vazia |

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
| `versao_formato` | `int` | `resultados.VERSAO_FORMATO` = 3; muda quando os campos mudam (2: `datas_obtencao`; 3: `tipo`, `modalidade`, `niveis`, `trechos`, `comum`, `termica`, `renovavel`, `conjunto`, `indicadores_carteira` e `omitidos`) |
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
| `programacao` | `dict` | programação diária (3.5); `{}` sem a base; vazio nas usinas sem EVT (a programação delas está em `comum`) |
| `disponibilidade` | `dict` | disponibilidade operacional e sincronizada (3.6); `{}` sem a base; vazio nas usinas sem EVT |
| `hidrologia` | `dict` | afluência, vertimento e nível (3.7); `{}` sem a base; na hidrelétrica sem EVT, a versão sem os cruzamentos com a EVT (3.17) |
| `geracao_oficial` | `dict` | geração por usina (3.8); `{}` sem a base; vazio nas usinas sem EVT |
| `cadastro` | `dict` | ficha do cadastro (3.9); `{}` sem a ficha |
| `dicionarios` | `dict` | `{"registro": DataFrame}` (3.9); `{}` sem o registro |
| `datas_obtencao` | `dict` | conjunto → `arquivos_registrados`, `publicacao_mais_recente`, `obtencao_mais_recente`, de `datas_obtencao.csv` |
| `fontes` | `dict` | vazio no arquivo; montado pela Geração do relatório |
| `serie_diaria`, `vazoes_anuais` | `DataFrame` | dados das figuras 01 e 05 (3.3) |
| `tipo`, `modalidade` | `str` | do perfil (o tipo, ou o prefixo do CEG), nos dois caminhos |
| `niveis` | `dict` | nível e identificador de cada base de nível variável (3.13); `{}` na hidrelétrica com EVT |
| `trechos` | `DataFrame` | `trechos.csv` da Coleta (3.13); vazio na hidrelétrica com EVT |
| `comum` | `dict` | seções comuns sobre a base horária comum (3.12); `{}` na hidrelétrica com EVT, o que define o caminho (`resultados.sem_evt`) |
| `termica` | `dict` | seções de térmica (3.14); `{}` fora das térmicas ou sem o despacho |
| `renovavel` | `dict` | seções de eólica e solar (3.15); `{}` fora delas ou sem nenhuma base |
| `conjunto` | `dict` | composição e geração do conjunto (3.16); `{}` fora de conjunto ou sem a geração do conjunto |
| `indicadores_carteira` | `dict` | indicadores da carteira (3.19), nos dois caminhos |
| `omitidos` | `list[dict]` | seções e regras não avaliadas, com o motivo (3.18); vazio na hidrelétrica com EVT |

Na hidrelétrica com EVT, os campos de antes têm os mesmos valores, e dos campos novos só `tipo`, `modalidade` e `indicadores_carteira` são preenchidos. Nas usinas sem EVT, os campos da base de EVT (`globais`, `indicadores_anuais`, `evt_mensal`, eventos, distribuições, perfis, `mudanca_classificacao`, sinalizados, extremos, `validacao`, `horas_geracao_zero`, `serie_diaria`, `vazoes_anuais`) ficam vazios, e `cobertura` é a cobertura da série de referência (`comum["cobertura"]`, seção 3.12).

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
| `manifesto` | `dict` | resumo do manifesto da EVT, da linha da EVT em `datas_obtencao.csv` (`{}` sem ela ou sem arquivos registrados): `arquivos` (`arquivos_registrados`), `ultima_modificacao_mais_recente` (`publicacao_mais_recente`), `registro_mais_recente_utc` (`obtencao_mais_recente`) (str) |

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
- **DISPF** (`_media_ponderada`): peso = horas da base de EVT no mês × `potencia_mw` (sem potência, `parametros.potencia_unitaria_mw`); só os meses presentes na base de EVT. Nas usinas sem EVT, as horas são as da base horária comum no nível da usina, e `disponibilidade_declarada_pct` de `disp_anual` é a disponibilidade operacional relativa dos indicadores anuais comuns; sem o IP e a TEIF de referência no perfil, `desvio_dispf_referencia_pp` fica vazio.
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
| `obtido_em` | `str` | data de obtenção (UTC) do conjunto, `obtencao_mais_recente` de `datas_obtencao.csv`; vazio sem registro |

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

Nas usinas sem EVT, `montar_achados_comum`, nesta ordem (títulos fixos):

| # | Título | Função | Gerada quando |
|---|---|---|---|
| 1 | Cobertura dos dados | `_achado_cobertura_comum` | sempre |
| 2 | Cadastro da usina no ONS | `_achado_cadastro` | `cadastro["divergencias"]` não vazio |
| 3 | A usina no conjunto | `conjunto.achado_usina_no_conjunto` | `em_duas_partes(res)` |
| 4 | Geração | `_achado_geracao_comum` | sempre (uma frase por nível) |
| 5 | Disponibilidade | `_achado_disponibilidade_comum` | há `comum["disponibilidade"]` |
| 6 | Programação diária do ONS | `_achado_programacao_comum` | há `comum["programacao"]` |
| 7 | Despacho por motivo | `termica.achados_termica` | há `termica` (sem geração, diz que a usina não gerou e ficou disponível) |
| 8 | Atendimento ao despacho | idem | há horas com programação ou sem programação com geração acima dela |
| 9 | Disponível sem despacho | idem | há `disponivel_sem_despacho` e a usina gerou |
| 10 | CVU e CMO | idem | há `cvu_cmo` |
| 11 | Fator de capacidade | `renovavel.achados_renovavel` | há `renovavel["fator_capacidade"]` |
| 12 | Energia cortada | idem | há `renovavel["restricao"]` |
| 13 | Recurso × geração | idem | há semi-horas com o recurso inválido ou acima do limite físico |
| 14 | Composição do conjunto | `conjunto.achados_conjunto` | há `conjunto` (até 5 composições no texto) |
| 15 | Afluência e vertimento | `_achado_afluencia_comum` | há `hidrologia` com `sem_evt` |
| 16 | Qualidade dos dados | `_achado_qualidade_comum` | sempre; com as frases de `conjunto.frases_tipo_publicado` quando o tipo publicado diverge |

`do_nivel` escreve " do conjunto <nome>" nos números do nível do conjunto. Nas usinas piloto: William Arjona, 9 constatações; Seriemas 1, 9; Praia Formosa, 7; Bandeirante, 6.

### 3.11 Conclusão (`conclusao`, `montar_conclusao`)

Item:

| Campo | Tipo | Descrição |
|---|---|---|
| `lista` | `str` | `pontos_atencao`, `possiveis_problemas`, `confirmar_agente` ou `verificar_campo` |
| `ordem` | `int` | posição na lista, de 1 em diante |
| `regra` | `str` | `C1` a `C19` |
| `texto` | `str` | uma frase, sem ponto final, com os números formatados |
| `secoes` | `list[str]` | chaves das seções de origem (seção 5.4), na ordem de citação |

**`RegraConclusao`** (`src/analises/conclusao.py`; o catálogo `CATALOGO_CONCLUSAO` tem C1 a C19, nessa ordem):

| Campo | Tipo | Conteúdo |
|---|---|---|
| `codigo` | `str` | `C1` a `C19` |
| `tipos` | `tuple[str]` | tipos em que a regra é avaliada (`HIDRELETRICAS`, `TERMICAS`, `RENOVAVEIS` do registro da Coleta) |
| `listas` | `tuple[str]` | listas em que a regra pode gerar itens; cada item traz a sua |
| `funcao` | função ou `None` | a regra sobre a base de EVT (C1 a C11); `None` de C12 em diante |
| `secoes` | `tuple[str]` | seções de origem |
| `limiares` | `tuple[str]` | nomes das constantes de `regras.py` |
| `nivel_exigido` | `str` | `usina`: só entradas do nível da usina |
| `periodo_minimo_meses` | `int` ou `None` | meses distintos da série; só a C18 (12) |
| `funcao_comum` | função ou `None` | a regra nas usinas sem EVT (C2, C5, C8, C10 e C12 a C19); `None` nas que dependem da base de EVT |
| `bases_comuns` | `tuple[str]` | bases da usina de que a regra precisa (basta uma): `disponibilidade`, `indicadores`, `despacho`, `cvu_cmo`, `restricao`, `recurso`, `fator_capacidade` (no nível da usina), `programacao` (no nível da usina) |
| `exige_referencias` | `bool` | pede o IP e a TEIF de referência no perfil (C5) |
| `exige_garantia_fisica` | `bool` | pede a garantia física no perfil (C18) |
| `descricao` | função ou `None` | texto da regra na nota da conclusão das usinas sem EVT, com os limiares |

Na hidrelétrica com EVT, `_avaliar` roda `REGRAS_CONCLUSAO` (as `funcao` de C1 a C11), como antes. Na usina sem EVT, roda a `funcao_comum` das regras do tipo (`regras_do_tipo`) que têm base: alguma das `bases_comuns` presente, as referências e a garantia física pedidas, e o período mínimo; as seções citadas passam às chaves do caminho sem EVT (`SECOES_SEM_EVT`: `indicadores_ons` → `indicadores_ons_comum`, `qualidade` → `qualidade_comum`, `disponibilidade_geracao` → `disponibilidade_geracao_comum`, `indicadores_anuais` → `anuais_comum`). As demais regras do tipo vão para `omitidos` (`regras_omitidas`), com o motivo: "regra da base de EVT, que a usina não tem"; "sem <bases> no nível da usina"; "sem IP e TEIF de referência no perfil da usina"; "sem a garantia física no perfil da usina"; ou "a série tem N meses distintos, menos que o período mínimo de 12". `frase_sem_itens` dá a frase da conclusão vazia: a de antes na hidrelétrica com EVT; nas usinas sem EVT, a de antes quando alguma regra foi avaliada, a de que o ONS publica só os números do conjunto quando a série de referência é do conjunto e nenhuma regra tem base, ou a de que nenhuma regra do tipo tem base para a usina.

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

Nas usinas sem EVT (funções `funcao_comum`):

| Regra | Usa | Gera item em | Seções |
|---|---|---|---|
| C2 | `_regra_c2`, como na tabela acima; sem a TEIF de referência, só a limitação forçada recorrente | possíveis problemas, a confirmar, a verificar | `indicadores_ons_comum` |
| C5 | `_regra_c5_comum`: `comum["disponibilidade"]["resumo"]["disponibilidade_relativa_pct"]` (operacional), `ons["disp_periodo"]`, `ons["taxa_ultima"]` | pontos de atenção (um item) | `disponibilidade_geracao_comum` (disponibilidade) e `indicadores_ons_comum` (DISPF ou taxas) |
| C8 | `_regra_c8_comum`: horas com o código `R7` em `comum["qualidade"]["sinalizacoes"]` | possíveis problemas e a confirmar | `qualidade_comum` |
| C10 | `_regra_c10_comum`: `comum["disponibilidade"]["eventos_indisponibilidade_total"]` e `ons["ug_anual"]`, com os anos seguidos de mesmas unidades juntos (`_unidades_agrupadas`: "de todas as unidades em …") | a confirmar, a verificar | `disponibilidade_geracao_comum` e `indicadores_ons_comum` |
| C12 | `termica["atendimento"]["resumo"]["horas_abaixo"]` | possíveis problemas, a confirmar | `atendimento_despacho` |
| C13 | `termica["cvu_cmo"]["horas_disponivel_cvu_abaixo"]` e `semanas_disponivel_cvu_abaixo` | a confirmar | `disponivel_sem_despacho` |
| C14 | `termica["inflexibilidade_resumo"]["nao_verificada_pct"]` | pontos de atenção | `despacho_motivo` |
| C15 | `termica["atendimento"]["resumo"]["horas_sem_programacao"]` | a confirmar | `atendimento_despacho` |
| C16 | `renovavel["restricao"]["resumo"]["pct_estimada"]` | pontos de atenção | `energia_cortada` |
| C17 | `renovavel["recurso"]["resumo"]["pct_invalidas"]` | a verificar | `recurso_geracao` |
| C18 | `renovavel["fator_capacidade"]["anual"]` (nível da usina, anos completos) e a garantia física | pontos de atenção | `fator_capacidade` |
| C19 | `renovavel["programacao"]` (nível da usina): `desvio_medio_absoluto_pct` | a confirmar | `programacao_comum` |

`montar_conclusao` ordena os itens de forma estável por lista (na ordem de `LISTAS_CONCLUSAO`) e pelo número da regra, e numera `ordem` em cada lista. Todos os itens ficam no arquivo. Na São Domingos: 19 itens (5 pontos de atenção, 4 possíveis problemas, 5 a confirmar e 5 a verificar), com as onze regras. Na William Arjona: 7 itens (C8, C10, C12 e C15), com a C5 em `omitidos`. Na Seriemas 1 e na Praia Formosa: C16 e C17. Na Bandeirante: nenhum item, com C1 a C11 em `omitidos`.

### 3.12 Seções comuns das usinas sem EVT (`comum`, `analisar_comum`)

Sobre `base_horaria.csv`. Toda tabela por ano, mês ou hora tem a coluna `nivel` (`usina` ou `conjunto`), uma linha por nível; a disponibilidade é sempre da usina e só entra nas horas do nível da usina. Hora sem valor fica fora das médias e é contada.

| Chave | Tipo | Conteúdo |
|---|---|---|
| `cobertura` | `dict` | `inicio`, `fim` (`Timestamp`), `horas_observadas`, `horas_esperadas` (grade horária contínua), `horas_ausentes` (das ausências da série de referência), `horas_sem_valor`, `anos_parciais`, `anos_completos` (`list[int]`), `meses_distintos` (meses do ano presentes, 1 a 12), `meses`, `niveis` (`nivel` → horas), `trechos` (quantidade) |
| `anuais` | `DataFrame` | por ano e nível: `ano`, `nivel`, `ano_parcial`, `horas`, `horas_com_valor`, `geracao_media_mw`, `energia_mwh`, `geracao_maxima_mw`, `horas_paradas` (≤ 1 MW), `pct_horas_paradas`, `fator_capacidade_pct` (só EOL e UFV, no nível da usina; vazio nos demais), `disponibilidade_media_mw` e `disponibilidade_relativa_pct` (operacional, só da usina) |
| `serie_diaria` | `DataFrame` | por dia e nível: `din_instante`, `nivel`, `geracao_mw` (média), `disponibilidade_operacional_mw` (média da usina; vazia no nível do conjunto) |
| `mensal` | `DataFrame` | por mês e nível: `mes`, `nivel`, `horas`, `horas_com_valor`, `geracao_media_mw`, `energia_mwh` |
| `sazonalidade` | `DataFrame` | por mês do ano e nível, só no nível com 12 meses distintos: `mes_do_ano`, `nivel`, `geracao_media_mw`, `anos` |
| `perfil_horario` | `DataFrame` | por hora do dia e nível: `hora`, `nivel`, `geracao_media_mw`, `horas` |
| `disponibilidade` | `dict` | `{}` sem a Disponibilidade por usina. `resumo` (`inicio`, `fim`, `horas`, `disp_operacional_media_mw`, `disp_sincronizada_media_mw`, `disponibilidade_relativa_pct`, `horas_indisponibilidade_total`, `horas_geracao_acima_disponibilidade`, `eventos_indisponibilidade_total`); `mensal` e `anual` (`periodo`, `horas_comuns`, `disp_operacional_media_mw`, `disp_sincronizada_media_mw`, `geracao_media_mw`, `capacidade_nao_sincronizada_media_mw`, `horas_indisponibilidade_total`, `horas_paradas_disponivel`, `horas_paradas_sincronizadas`, `horas_geracao_acima_disponibilidade`; a anual com `ano_parcial` e `disponibilidade_relativa_pct`); `eventos_indisponibilidade_total` (`inicio`, `fim`, `duracao_h`, `geracao_media_mw`) |
| `programacao` | `dict` | `{}` sem horas comuns no mesmo nível. `nivel`; `resumo` (`inicio`, `fim`, `horas_comuns`, `geracao_media_mw`, `programada_media_mw`, `desvio_medio_mw`, `desvio_medio_absoluto_mw`, `correlacao` (vazia com série constante), `horas_desvio_programacao`, `eventos_desvio`, `dias_ausentes`); `mensal` (`mes`, `horas_comuns`, `geracao_media_mw`, `programada_media_mw`, `desvio_medio_mw`, `desvio_medio_absoluto_mw`, `horas_desvio_programacao`); `eventos` (`inicio`, `fim`, `duracao_h`, `programacao_media_mw`) |
| `programacao_coletada`, `programacao_horas` | `bool`, `int` | a Programação diária foi coletada; horas dela no período (para o motivo da omissão) |
| `qualidade` | `dict` | `sinalizacoes` (`codigo`, `descricao`, `horas`), `horas_sinalizadas`, `horas_sem_valor`, `ausencias` (`tipo`, `inicio`, `fim`, `horas`), `linhas_usina_sem_valor`, `linhas_usina_sem_valor_periodo` (`inicio`, `fim`) |
| `conferencias_nao_aplicaveis` | `DataFrame` | `nao_aplicaveis.csv` da Conferência, como está (`conferencia`, `motivo`) |
| `agentes` | `dict` | `proprietario` e `operador` (`list[str]`): agentes das unidades ativas no fim do período, da Capacidade de geração; `{}` sem a ficha |

A comparação com a programação usa a base horária, nas horas do nível da programação; na eólica ou solar com a restrição com detalhe como série de referência e a programação do conjunto, usa `base_programacao_conjunto` (a Geração por usina do conjunto e a programação, com `nivel` = `conjunto`), fora da base da usina.

### 3.13 Níveis e trechos (`niveis`, `trechos`)

`niveis` (`niveis_da_usina`), só nas usinas sem EVT:

| Chave | Campos | Quando |
|---|---|---|
| `geracao` | `nivel` (`usina`, `conjunto` ou `usina e conjunto`), `identificador_usina` (id ONS), `identificador_conjunto` (id do conjunto), `nome` (do conjunto, da composição); `fonte` = `restricao_detalhe` quando a série de referência é a restrição com detalhe | sempre |
| `programacao` | `nivel`, `identificador` (os códigos de programação, separados por "; ") | com a Programação diária coletada |
| `disponibilidade` | `nivel` = `usina`, `identificador` (id ONS) | com a Disponibilidade por usina coletada |
| `fator_capacidade`, `restricao_razao` | `nivel`, `identificador` (id ONS ou id do conjunto) | eólicas e solares, com a base coletada |

`trechos`: `trechos.csv` da Coleta, como está (`trecho`, `inicio`, `fim`, `modalidade`, `id_conjunto`, `composicao`, `tipos_composicao`, `codigos_planejamento`, `nivel_geracao`, `mostrar`).

### 3.14 Térmica (`termica`, `analisar_termica`)

Vazio sem o despacho tratado ou sem horas dele. As somas de MW horários são MWh.

| Chave | Tipo | Conteúdo |
|---|---|---|
| `periodo` | `dict` | `inicio`, `fim`, `horas` do despacho |
| `codigos` | `list[int]` | unidades de planejamento |
| `motivos_anual`, `motivos_mensal` | `DataFrame` | `periodo`, `motivo`, `grupo` (`total`, `motivo` ou `detalhe`), `programado_mwh`, `verificado_mwh`, `parcela_programado_pct`, `parcela_verificado_pct` (sobre a geração total publicada; vazia com total nulo); só os motivos com energia |
| `inflexibilidade` | `DataFrame` | por mês: `mes`, `programada_mwh`, `verificada_mwh`, `nao_verificada_mwh` (Σ máx(programada − verificada, 0)) |
| `inflexibilidade_resumo` | `dict` | `programada_mwh`, `verificada_mwh`, `nao_verificada_mwh`, `nao_verificada_pct` (base da C14) |
| `atendimento` | `dict` | `resumo` (`horas_comuns`, `horas_programadas` (> 1 MW), `horas_abaixo`, `energia_abaixo_mwh`, `horas_acima`, `energia_acima_mwh`, `horas_sem_programacao`, `energia_sem_programacao_mwh`, `desvio_medio_mw`, `limiar_mw`); `anual` (`ano` e as horas e energias acima); `mensal` (`mes`, `energia_abaixo_mwh`, `energia_acima_mwh`); `maiores_desvios` (`din_instante`, `programado_mw`, `verificado_mw`, `desvio_mw`; até 15, empates em ordem cronológica) |
| `disponivel_sem_despacho` | `dict` | `{}` sem horas comuns com a disponibilidade. `resumo` (`horas_comuns`, `horas`, `pct_horas`, `potencia_disponivel_media_mw`, `inicio`, `fim`); `anual` (`ano`, `horas_comuns`, `horas_disponivel_sem_despacho`, `potencia_disponivel_media_mw`) |
| `horas_com_despacho`, `horas_com_despacho_anual` | `int`, `dict` | horas com programação > 1 MW, no período e por ano |
| `geracao_verificada_mwh`, `sem_geracao` | `float`, `bool` | geração verificada total; verdadeiro quando ela não passa de 1 MWh |
| `cvu_cmo` | `dict` | `{}` sem o CVU ou o CMO. `semanal` (por semana operativa e unidade: `codigo`, `semana_inicio`, `semana_fim`, `cvu`, `sinal_cvu`, `cmo`, `relacao`, `geracao_mwh`, `horas_disponivel_sem_despacho`); `resumo` (por unidade: `codigo`, `semanas`, `semanas_abaixo`, `geracao_abaixo_mwh`, `semanas_acima`, `geracao_acima_mwh`, `semanas_igual`, `semanas_sem_comparacao`, `semanas_cvu_sinalizado`); `semanas_cvu_abaixo`; `horas_disponivel_cvu_abaixo` e `semanas_disponivel_cvu_abaixo` (base da C13) |
| `cvu_coletado`, `cmo_coletado` | `bool` | o CVU e o CMO foram tratados |
| `cvu_sinalizados` | `dict` | semanas com o CVU `ausente`, `zero` e `negativo` |
| `conferencias` | `dict` | `programacao_despacho` (G3) e `verificada_despacho` (G4), seção 1.2 |

Na William Arjona: 3.264 horas com programação, 2.821 abaixo (112.233 MWh), 86 acima e 114 sem programação (3.028 MWh); CVU zero em 366 semanas-unidade, sem comparação; nenhuma hora disponível sem despacho em semana com CVU abaixo do CMO.

### 3.15 Eólica e solar (`renovavel`, `analisar_renovavel`)

Vazio sem nenhuma das seções. As energias das semi-horas são potência × 0,5 h.

| Chave | Tipo | Conteúdo |
|---|---|---|
| `tipo` | `str` | `EOL` ou `UFV` |
| `fator_capacidade` | `dict` | `{}` sem a base. `nivel`; `mensal` e `anual` (`periodo`, `nivel`, `horas`, `geracao_verificada_mwh`, `capacidade_media_mw`, `fator_capacidade_pct` = Σ verificada ÷ Σ capacidade, `horas_fc_fora_0_1`, `horas_acima_capacidade`; a anual com `ano_parcial`); `resumo` (`inicio`, `fim`, `horas`, `fator_capacidade_pct`, `horas_fc_fora_0_1`, `horas_acima_capacidade`) |
| `restricao` | `dict` | `{}` sem a restrição com detalhe. `resumo`, `mensal` e `anual` (`periodo`, `semi_horas`, `semi_horas_restritas`, `horas_restritas`, `semi_horas_sem_marca`, `semi_horas_sem_estimativa`, `semi_horas_restritas_sem_estimativa`, `energia_verificada_mwh` e `energia_estimada_mwh` (nas semi-horas com estimativa), `energia_estimada_com_marca_mwh`, `energia_cortada_mwh` (só nas restritas), `pct_estimada` (cortada ÷ estimada com a marca), `diferenca_bruta_mwh`; a mensal também `cortada_rel_mwh`, `cortada_cnf_mwh`, `cortada_ene_mwh`, `cortada_sem_razao_mwh`; o resumo também `inicio` e `fim`); `por_razao` (`razao`, `descricao`, `semi_horas`, `energia_cortada_mwh`, `pct_cortada`); `nivel_razao` |
| `recurso` | `dict` | `{}` sem semi-horas com o recurso. `grandeza` (`vento` ou `irradiância`), `unidade`, `largura`, `limite`; `faixas` (`faixa_inicio`, `faixa_fim`, `semi_horas`, `geracao_media_mw`, `estimada_media_mw`, sem as estimativas ausentes); `resumo` (`semi_horas`, `semi_horas_validas`, `semi_horas_invalidas`, `pct_invalidas`, `semi_horas_implausiveis` (acima do limite físico, sem a marca do ONS), `semi_horas_sem_recurso`) |
| `programacao` | `dict` | `{}` sem a programação comum. `nivel`, `maiores_desvios` (`din_instante`, `geracao_programada_mw`, `geracao_mw`, `desvio_mw`; até 15), `desvio_medio_absoluto_mw`, `desvio_medio_absoluto_pct` (÷ P), `horas` |
| `conferencias` | `dict` | G1, G2 e G5 aplicadas (seção 1.2) |

Na Praia Formosa: 184.769 MWh cortados nas 16.311 semi-horas restritas, 16,6 % da estimada, contra 355.038 MWh da diferença bruta; 10.504 semi-horas sem estimativa, 441 delas restritas; 13.157 semi-horas com o vento inválido e 111 acima de 40 m/s.

### 3.16 Conjunto (`conjunto`, `analisar_conjunto`)

Vazio fora de conjunto, sem a geração do conjunto, sem os trechos ou sem a composição.

| Chave | Tipo | Conteúdo |
|---|---|---|
| `id`, `nome`, `nivel` | `str` | id e nome do conjunto; `nivel` = `conjunto` |
| `com_capacidade` | `bool` | há `capacidade_membros.csv` |
| `trechos` | `DataFrame` | por trecho de composição: `trecho`, `inicio`, `fim`, `usinas`, `tipos`, `horas`, `horas_com_valor`, `energia_mwh`, `geracao_media_mw`, `geracao_maxima_mw`, `potencia_somada_mw` (vazia sem a capacidade), `usinas_sem_potencia` |
| `composicao` | `DataFrame` | por trecho e usina: `trecho`, `ceg`, `usina`, `tipo`, `entrada`, `saida`, `unidades`, `potencia_mw` (unidades em operação em algum momento do trecho; vazia sem unidade) |
| `mensal` | `DataFrame` | `mes`, `trecho`, `horas_com_valor`, `geracao_media_mw`, `energia_mwh` |
| `tipo_publicado` | `DataFrame` | por trecho de composição e tipo publicado: `trecho`, `inicio`, `fim`, `tipo_publicado`, `combustivel_publicado`, `horas`, `tipos_composicao`, `corresponde` |
| `peso_usina` | `DataFrame` | `trecho`, `inicio`, `fim`, `potencia_usina_mw`, `potencia_somada_mw`, `peso_pct` (vazio sem potência da usina no trecho); vazia sem a capacidade |
| `resumo` | `dict` | `inicio`, `fim`, `composicoes`, `horas_com_valor`, `trechos_tipo_divergente` |

Trecho de composição: os trechos consecutivos de `trechos.csv` com a mesma `composicao`, juntos. A geração do conjunto vem das horas do nível do conjunto da base horária (série de referência do conjunto) ou, na eólica ou solar com série própria, da Geração por usina do conjunto (`serie_do_conjunto`). O tipo publicado corresponde quando o tipo do ONS (pela tabela `TIPOS_ONS`) inclui algum tipo da composição. `em_duas_partes(res)`: há `conjunto` e todas as horas da série de referência são do nível do conjunto.

Na Bandeirante: três trechos de composição (8 usinas, PCH e UTE, até 26/09/2019; 9 até 30/06/2025; 4 PCH desde 01/07/2025, com 47,0 MWmed e 78,5 MW somados); peso de 6,7 % e 35,7 % nos dois últimos (no primeiro, sem unidade em operação); o tipo publicado "TÉRMICA" (Biomassa) não corresponde no terceiro.

### 3.17 Hidrologia da hidrelétrica sem EVT (`hidrologia`, `analisar_hidrologia_sem_evt`)

Vazio sem a série no período. Sempre: `resumo` (`_resumo_serie` e `sinalizadas_por_regra`, como na seção 3.7), `alinhamento` (da conferência `alinhamento_hidrologia`; sem ela, só `confirmado` falso), `auditoria`, `ausencias`, `obtido_em`, `publicado` (= `confirmado`), `sem_evt` (verdadeiro) e `motivo_alinhamento` (vazio com a conferência aplicada). Só com `publicado`: `mensal` e `anual` (as colunas de `resumir_hidrologia`, seção 3.7; a anual com `ano_parcial`) e, no `resumo`, `afluencia_media_m3s`, `afluencia_maxima_m3s`, `turbinada_media_m3s`, `vertida_media_m3s` e `horas_afluencia_acima_engolimento`, todos sobre a cópia `limpos`. Sem faixas de afluência, perfil por grupo de dias nem pico de afluência.

### 3.18 Omissões (`omitidos`)

Lista de `{"item", "tipo", "motivo"}`, na ordem do relatório; vazia na hidrelétrica com EVT.

| `tipo` | `item` | Exemplos de motivo |
|---|---|---|
| `secao` | título da seção (por exemplo "Disponibilidade e geração por ano", "Sazonalidade (distribuição por mês do ano)", "Seções de térmica", "CVU × CMO", "Fator de capacidade", "Composição e geração do conjunto", "Programação diária × geração verificada", "Afluência, vertimento e nível do reservatório", "Conferência da geração entre fontes") | "sem a Disponibilidade por usina (cobertura: ausente)"; "a série do nível usina tem menos de 12 meses distintos (3)"; "o despacho não tem horas no período da série de referência"; "sem horas com a programação e a geração verificada no mesmo nível" |
| `regra` | código da regra (`C1` a `C19`) | os da seção 3.11 (`regras_omitidas`) |

A "Conferência da geração entre fontes" é sempre omitida nas usinas sem EVT: nas térmicas e nas eólicas e solares, os resultados das conferências G1 a G5 vão nas legendas das seções do tipo e nas abas da planilha; nos demais, nenhuma conferência entre fontes de geração se aplica.

### 3.19 Indicadores da carteira (`indicadores_carteira`, `src/analises/carteira.py`)

Gravado nos dois caminhos (`indicadores_carteira(res)`).

| Chave | Tipo | Conteúdo |
|---|---|---|
| `tipo` | `str` | tipo da usina |
| `periodo` | `dict` | `inicio`, `fim` da série de referência (`cobertura`) |
| `ano`, `ano_parcial` | `int`, `bool` | `ano_dos_indicadores`: o maior de `anos_completos`; sem ele, o maior de `anos_parciais`, com `ano_parcial` verdadeiro |
| `fator_capacidade` | `dict` ou `None` | `fator_capacidade_pct` do ano: `indicadores_anuais` (com EVT) ou `comum["anuais"]` no nível da usina (sem EVT; só EOL e UFV têm valor) |
| `disponibilidade` | `dict` ou `None` | `disponibilidade_relativa_pct` do ano, das mesmas tabelas (declarada com EVT; operacional sem EVT) |
| `teifa` | `dict` ou `None` | `ons["taxas"]`: no ano completo, a TEIFa de dezembro (sem dezembro, `None`); no parcial, a do último mês publicado do ano; × 100; com `mes` |
| `energia_cortada` | `dict` ou `None` | `pct_estimada` da linha do ano em `renovavel["restricao"]["anual"]` |
| `atendimento_despacho` | `dict` ou `None` | da linha do ano em `termica["atendimento"]["anual"]`: (`horas_programadas` − `horas_abaixo` − `horas_acima`) ÷ `horas_programadas` × 100, com `horas_dentro` e `horas_programadas`; `None` sem hora com programação |
| `conclusao` | `dict` | `pontos_atencao`, `possiveis_problemas`, `confirmar_agente`, `verificar_campo` (todos os itens de cada lista; `None` quando nenhuma regra foi avaliada), `regras_avaliadas` e `regras_nao_avaliadas` (quantidades: C1 a C11 com EVT; as regras do tipo menos as de `omitidos` sem EVT) |

Cada indicador presente é `{"valor": float, "nivel": "usina", "unidade": "%", ...}`; valor ausente, não numérico ou não finito dá `None`, nunca zero.

## 4. Manifesto da etapa (`etapa.json`)

Campos comuns (`etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status`, `codigo_saida`, `etapa_anterior`, `arquivos`, `resumo`) e transições de `status`: [data-model da Coleta](../001-coleta-dados/data-model.md). Nesta etapa:
- `versao_formato` = 3 (`pipeline.VERSAO_FORMATO["analises"]`);
- `etapa_anterior` = `{"etapa": "conferencia", "concluida_em": …}`;
- `arquivos` = `resultados.pkl`, com `bytes` e `sha256`, mesmo quando o conteúdo não mudou;
- em erro: `status` `falha`, `codigo_saida` 1, `arquivos` vazio e `resumo` = `{"erro": "<mensagem>"}`; na interrupção pelo usuário (Ctrl+C), `{"erro": "interrompida pelo usuário"}`.

`resumo` (`executar_analises`), na hidrelétrica com EVT:

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

Na usina sem EVT (`_executar_sem_evt`), o `resumo` traz os mesmos `periodo`, `horas_analisadas`, `constatacoes`, `conclusao` e `regras_da_conclusao`, sobre a série de referência, e mais:

| Campo | Tipo | Conteúdo |
|---|---|---|
| `tipo` | `str` | tipo da usina |
| `niveis` | `dict[str, int]` | horas da série de referência por nível |
| `omitidos` | `list[str]` | itens de `omitidos` (seções e regras), na ordem |
| `bases_complementares` | `dict[str, bool]` | `indicadores`, `programacao` (a comparação comum), `disponibilidade`, `cadastro`; nas térmicas, `despacho` e `cvu_cmo`; nas eólicas e solares, `fator_capacidade`, `restricao` e `recurso`; na usina em conjunto, `conjunto`; nas hidrelétricas, `hidrologia` |

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
| Sazonalidade nas usinas sem EVT; período mínimo da C18 | 12 meses distintos | `PERIODO_MINIMO_SAZONALIDADE_MESES` (a C18 declara o seu em `RegraConclusao`) |
| Fator de capacidade nos indicadores anuais comuns | só EOL e UFV, no nível da usina | `TIPOS_COM_FATOR_CAPACIDADE` |
| Atendimento ao despacho | horas com programação > 1 MW; desvio além de 5 MW; sem programação, verificada > programada + 5 MW | `LIMIAR_GERACAO_PARADA_MW`, `LIMIAR_DESVIO_DESPACHO_MW` |
| Disponível sem despacho | disponibilidade operacional > 0,001 MW; programação e geração ≤ 1 MW | `LIMIAR_INDISPONIBILIDADE_TOTAL_MW`, `LIMIAR_GERACAO_PARADA_MW` |
| Maiores desvios (térmicas, eólicas e solares) | 15 horas | `NUMERO_EVENTOS_RELATORIO` |
| Energia de uma semi-hora | potência × 0,5 h | `DURACAO_SEMI_HORA_H` |
| Faixas do recurso | 2 m/s; 100 W/m² | `FAIXA_VENTO_MS`, `FAIXA_IRRADIANCIA_WM2` |
| Limite físico do recurso | vento ≤ 40 m/s; irradiância ≤ 1.500 W/m² | `LIMITE_VENTO_PLAUSIVEL_MS`, `LIMITE_IRRADIANCIA_PLAUSIVEL_WM2` |
| Composições citadas na constatação do conjunto | até 5 | `MAXIMO_TRECHOS_NA_CONSTATACAO` (`conjunto.py`) |

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
| `LIMIAR_DESVIO_DESPACHO_MW` | 5,0 | C12 e C15: desvio da geração verificada em relação à programada |
| `LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS` | 24 | C12: `horas_abaixo` |
| `LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS` | 168 | C13: `horas_disponivel_cvu_abaixo` |
| `LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT` | 5,0 | C14: `nao_verificada_pct` |
| `LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS` | 24 | C15: `horas_sem_programacao` |
| `LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT` | 5,0 | C16: `pct_estimada` |
| `LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT` | 10,0 | C17: `pct_invalidas` |
| garantia física ÷ potência instalada | — | C18: fator de capacidade publicado da usina num ano completo abaixo da razão |
| `LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT` | 15,0 | C19: `desvio_medio_absoluto_pct` |
| `MAXIMO_ITENS_CONCLUSAO` | 5 | itens por lista no PDF e no Markdown, aplicado pela Geração do relatório |

Os limiares de C12 a C15 foram aprovados pelo usuário em 20/10/2026, e os de C16 a C19 em 21/10/2026 (o da C19 subiu de 10 % para 15 %).

### 5.3 Versões de formato

| Onde | Valor | Conferida por |
|---|---|---|
| `resultados.pkl` → `versao_formato` | 3 (`src/analises/resultados.VERSAO_FORMATO`) | `carregar_resultados` (Geração do relatório, no relatório da usina e no de carteira) |
| `etapa.json` → `versao_formato` | 3 (`src/pipeline.VERSAO_FORMATO`) | pré-requisito da Geração do relatório; o relatório de carteira trata outra versão como "Análises em formato antigo" |
| `etapa.json` da Conferência → `versao_formato` | 2 | pré-requisito desta etapa (código 5 com outra versão) |
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
- **Seções citadas pelos itens** (chaves das seções do relatório): `eventos`, `programacao`, `indicadores_ons`, `hidrologia`, `perfil_horario`, `indicadores_anuais`, `disponibilidade_geracao`, `disponibilidade_sincronizada` e `qualidade`; nas usinas sem EVT, também `indicadores_ons_comum`, `qualidade_comum`, `disponibilidade_geracao_comum`, `anuais_comum`, `programacao_comum`, `despacho_motivo`, `atendimento_despacho`, `disponivel_sem_despacho`, `fator_capacidade`, `energia_cortada` e `recurso_geracao`.
- **Tipos de usina** (`tipo`): `UHE`, `PCH`, `CGH` (hidrelétricas), `UTE`, `UTN` (térmicas), `EOL`, `UFV` (eólicas e solares).
- **Nível do dado** (`nivel`): `usina`, `conjunto` ou `agregado`.
- **Omissões** (`omitidos[].tipo`): `secao` ou `regra`.
- **Sinalizações da base horária comum** (`sinalizacoes`, separadas por ","): `G1` (geração com valor não numérico), `D1` a `D4` (disponibilidade) e `R7` (geração acima da disponibilidade declarada).
- **Grupos dos motivos do despacho** (`grupo`): `total` (geração total publicada), `motivo` (ordem de mérito, inflexibilidade, razão elétrica, garantia energética, GFOM, reposição de perdas, exportação, reserva de potência, GSUB, unit commitment) e `detalhe` (inflexibilidade pura, inflexibilidade embutida no mérito, ordem de demérito acima da inflexibilidade, ordem de demérito de referência, inflexibilidade do DESSEM, constrained-off).
- **Relação do CVU com o CMO** (`relacao`): `abaixo`, `acima`, `igual` e `sem comparação` (CVU sinalizado ou sem CMO na semana). **Sinal do CVU** (`sinal_cvu`, do Tratamento): vazio, `ausente`, `zero` ou `negativo`.
- **Razões da restrição** (`razao`): `REL` (indisponibilidade externa), `CNF` (confiabilidade elétrica), `ENE` (razão energética) e "sem razão publicada" (semi-hora restrita sem código).

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

Nas usinas sem EVT:

| Resultado | Preenchido quando | Sem a condição |
|---|---|---|
| `comum` | sempre (a base horária comum existe) | — |
| `comum["disponibilidade"]` | a disponibilidade da usina tem horas na base horária | `{}`; seções de disponibilidade em `omitidos`; C8 e C10 sem a base de disponibilidade |
| `comum["programacao"]` | há horas com a programação e a geração no mesmo nível | `{}`; seção de programação em `omitidos`, com o motivo (não coletada, sem horas no período ou sem o mesmo nível); C19 não avaliada |
| `comum["sazonalidade"]` | o nível tem 12 meses distintos | sem as linhas do nível; sazonalidade em `omitidos` |
| `ons` | os indicadores existem e têm meses | `{}`; seção em `omitidos` (hidrelétricas e térmicas) |
| `termica` | térmica com o despacho no período | `{}`; "Seções de térmica" em `omitidos`; C12, C14 e C15 não avaliadas |
| `termica["cvu_cmo"]` | o CVU e o CMO com semanas comuns | `{}`; "CVU × CMO" em `omitidos`; C13 não avaliada |
| `renovavel["fator_capacidade"]`, `["restricao"]`, `["recurso"]` | a base com horas ou semi-horas no período | `{}`; a seção em `omitidos`; C18, C16 ou C17 não avaliada |
| `conjunto` | usina em conjunto com a geração do conjunto, os trechos e a composição | `{}`; "Composição e geração do conjunto" em `omitidos` (só com `identificacao.id_conjunto`) |
| `hidrologia` | hidrelétrica com os Dados hidrológicos no período | `{}`; seção em `omitidos` |
| `hidrologia["mensal"]`, `["anual"]` | a hora confirmada pela geração (`publicado`) | só a cobertura e o resultado da conferência |
| itens da conclusão | alguma regra do tipo com base e com a condição atendida | conclusão sem itens, com `frase_sem_itens`; sem regra avaliada, contagens da carteira vazias |

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

Nas usinas sem EVT, também valem:
- nas tabelas de `comum`, nenhuma linha mistura níveis, e a disponibilidade só aparece no nível da usina;
- nenhum número do conjunto entra na conclusão: cada regra avaliada tem alguma das suas bases no nível da usina, e as demais estão em `omitidos`;
- nenhum número do conjunto é dividido entre as usinas, e nenhum fator de capacidade do conjunto é calculado;
- a energia cortada só soma as semi-horas com a marca de restrição e com estimativa, e a energia por razão soma a energia cortada;
- nenhuma semi-hora com o recurso inválido ou acima do limite físico entra nas faixas do recurso × geração;
- nenhuma semana com o CVU sinalizado entra na comparação com o CMO;
- os campos da base de EVT ficam vazios, e `indicadores_carteira` traz sempre as chaves fixas, com `None` (nunca zero) no que não se aplica.
