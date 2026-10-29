# Data Model: Tratamento de dados

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-23

Convenções de todas as saídas:
- pasta `data/usinas/<slug>/tratamento/`, com os nomes de `src/comum/caminhos.ARQUIVOS_TRATAMENTO`;
- só os arquivos do tipo e da cobertura da usina (spec, seção "Aplicabilidade por tipo"): na hidrelétrica com EVT, os das seções 2.1 a 2.5; nas usinas sem EVT, os das seções 2.3 a 2.5 que a cobertura declara e os das seções 2.7 a 2.9;
- CSV com `;`, ponto decimal, UTF-8 sem BOM, sem índice, datas `AAAA-MM-DD HH:MM:SS` (sem frações de segundo), ausente como célula vazia, verdadeiro e falso como `True` e `False`, fim de linha do sistema (CRLF no Windows) e aspas só no campo que contém `;`;
- instantes sem fuso, no horário publicado pelo ONS; `din_instante` é sempre a hora de início (nas semi-horárias, o início da meia hora); nas semanais, `semana_inicio` é o sábado que abre a semana operativa;
- `nivel` é o nível em que o ONS publica a série: `usina` ou `conjunto`;
- todo arquivo de dados é gravado por `src/comum/persistencia.py` (seções 3.6 e 5.6).

---

## 1. Entradas

| Arquivo | Gravado por | Lido por | Uso |
|---|---|---|---|
| `data/usinas/<slug>/coleta/etapa.json` | Coleta | `pipeline.etapa_anterior_concluida`; nas usinas sem EVT, também `etapa._tratar_sem_evt` | pré-requisito: `status` `concluida` e `versao_formato` atual (2); nas usinas sem EVT, `resumo.periodo` (`inicio`, `fim`) é o período de referência |
| `coleta/evt_extraido.csv` | Coleta | `validacao.carregar_base_consolidada` (`pd.read_csv(sep=";", low_memory=False)`) | base de EVT: 18 colunas obrigatórias, mais `arquivo_origem` e `tipo_match` |
| `coleta/indicadores_extraido.parquet` | Coleta | `indicadores.montar_indicadores` (`separar_conjuntos`) | linhas dos quatro conjuntos de indicadores, com a coluna `conjunto` e as colunas como publicadas (texto) |
| `coleta/programacao_extraido.parquet` | Coleta | `programacao.montar_programacao` | `dia`, `num_patamar`, `geracao_programada_mw`, `arquivo_origem` e, com mais de um código, `cod_exibicaousina` |
| `coleta/auditoria_programacao.csv` | Coleta | `etapa.ler_auditoria_coleta(..., ["dia"])` | `dia` e `obtido` de cada arquivo diário |
| `coleta/disponibilidade_extraido.parquet`, `hidrologia_extraido.parquet`, `geracao_extraido.parquet` | Coleta | `series.montar_serie`, via `tratar_<conjunto>` | `din_instante` como publicado, colunas de valor, `_nao_numerico` (algum valor não numérico na fonte) e `arquivo_origem` |
| `coleta/auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv`, `auditoria_geracao.csv` | Coleta | `etapa.ler_auditoria_coleta` → `series.montar_serie` | uma linha por arquivo, na ordem de leitura (data de publicação e nome); base da auditoria completa |
| `coleta/dicionario_evt.json` | Coleta (cópia do dicionário de dados da EVT) | `validacao.carregar_dicionario_dados` e `versao_dicionario_dados`, com o caminho passado por `evt.tratar_evt` (ao lado de `evt_extraido.csv`) | colunas descritas e versão do dicionário |
| `coleta/geracao_complemento.parquet` | Coleta (usinas sem EVT) | `base_horaria.montar_base_horaria` | `din_instante`, `cod_modalidadeoperacao` e `nivel` de cada hora da série de referência |
| `coleta/trechos.csv` | Coleta (usinas sem EVT) | `base_horaria.montar_base_horaria` | `trecho`, `inicio` e `fim` (as demais colunas não são usadas) |
| `coleta/despacho_extraido.parquet`, `cvu_extraido.parquet`, `cmo_extraido.parquet` | Coleta (térmicas) | `termica.montar_despacho`, `montar_cvu`, `montar_cmo` | colunas da tabela "Colunas dos conjuntos novos", `_nao_numerico` e `arquivo_origem` |
| `coleta/fator_capacidade_extraido.parquet`, `restricao_detalhe_extraido.parquet`, `restricao_razao_extraido.parquet` | Coleta (eólicas e solares) | `renovavel.tratar_fator_capacidade`, `montar_restricao`, `montar_razao` | idem |
| `coleta/restricao_membros_extraido.parquet` | Coleta (eólicas e solares em conjunto, com os membros no perfil) | `renovavel.montar_membros` | as colunas da restrição com detalhe e `id_ons` de cada membro |
| `coleta/auditoria_despacho.csv`, `auditoria_cvu.csv`, `auditoria_cmo.csv`, `auditoria_fator_capacidade.csv`, `auditoria_restricao_detalhe.csv`, `auditoria_restricao_razao.csv` | Coleta | `etapa.ler_auditoria_coleta` | ordem de leitura dos arquivos (duplicatas) e meses com arquivo (ausências); base da auditoria completa, menos na razão |
| `usinas/<slug>/perfil.toml` | usuário | `perfil.carregar_perfil`, na linha de comando | campos da tabela abaixo |

`ler_auditoria_coleta` lê `arquivo`, `formato`, `periodo`, `data_publicacao`, `status` e `mensagem` como texto, do jeito que foram gravados (o `periodo` `2018` de um arquivo anual continua texto), converte `obtido` em verdadeiro ou falso e as colunas de data pedidas em data e hora.

Na EVT extraída, a Coleta já troca a vírgula decimal por ponto e deixa vazio o valor não numérico (contado em `valores_invalidos` de `auditoria_evt.csv`, que o Tratamento não lê); a tipagem do Tratamento repete a troca e conta esses vazios no log, junto com os ausentes.

**Colunas de valor dos conjuntos horários** (`DescricaoConjunto.colunas_valor` e `convencao_hora`, declaradas no registro dos conjuntos, `src/coleta/registro.py`):

| Conjunto | Colunas de valor | Convenção de hora publicada |
|---|---|---|
| disponibilidade | `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` | início |
| hidrologia | `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas`, `val_nivelmontante`, `val_niveljusante`, `val_volumeutil` | fim (a última hora do dia vem como 23:59) |
| geração | `val_geracao` | início |
| fator de capacidade | `val_geracaoprogramada`, `val_geracaoverificada`, `val_capacidadeinstalada`, `val_fatorcapacidade` | início |

Com a cobertura da usina e do conjunto na geração, `geracao_extraido.parquet` traz, em cada hora, a série da usina quando ela tem valor, senão a do conjunto; o nível de cada hora está em `geracao_complemento.parquet`.

**Colunas dos conjuntos novos** (declaradas em `src/coleta/registro.py`; a Coleta as grava como publicadas, sem levar à hora nem escolher a revisão):

| Conjunto | Colunas usadas | Resolução e instante |
|---|---|---|
| despacho (`geracao-termica-despacho-2`) | `cod_usinaplanejamento`, `nom_tipopatamar`, 17 colunas programadas (`val_proggeracao`, `val_progordemmerito`, `val_progordemdemeritoref`, `val_progordemdemeritoacimadainflex`, `val_proginflexibilidade`, `val_proginflexembutmerito`, `val_proginflexpura`, `val_prograzaoeletrica`, `val_proggarantiaenergetica`, `val_proggfom`, `val_progreposicaoperdas`, `val_progexportacao`, `val_progreservapotencia`, `val_proggsub`, `val_progunitcommitment`, `val_progconstrainedoff`, `val_proginflexibilidadedessem`), 15 verificadas (`val_verifgeracao`, `val_verifordemmerito`, `val_verifordemdemeritoacimadainflex`, `val_verifinflexibilidade`, `val_verifinflexembutmerito`, `val_verifinflexpura`, `val_verifrazaoeletrica`, `val_verifgarantiaenergetica`, `val_verifgfom`, `val_verifreposicaoperdas`, `val_verifexportacao`, `val_verifreservapotencia`, `val_verifgsub`, `val_verifunitcommitment`, `val_verifconstrainedoff`), `tip_restricaoeletrica` | horária, início |
| CVU (`cvu-usitermica`) | `din_instante` (início da semana), `cod_usinaplanejamento`, `num_revisao`, `val_cvu`, `dat_fimsemana` | semanal |
| CMO (`cmo-semanal`) | `din_instante` (data publicada da semana), `val_cmomediasemanal`, `val_cmoleve`, `val_cmomedia`, `val_cmopesada` | semanal |
| restrição com detalhe (`restricao_coff_eolica_detail` ou `restricao_coff_fotovoltaica_detail`) | `val_geracaoverificada`, `val_geracaoestimada`, o recurso (`val_ventoverificado` ou `val_irradianciaverificado`) e a marca de recurso inválido (`flg_dadoventoinvalido` ou `flg_dadoirradianciainvalido`), `flg_geracaorestrita` | semi-horária, início |
| restrição com a razão (`restricao_coff_eolica_usi` ou `restricao_coff_fotovoltaica`) | `val_geracao`, `val_geracaolimitada`, `val_disponibilidade`, `val_geracaoreferencia`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene`, `cod_razaorestricao`, `nivel` | semi-horária, início |

**Colunas usadas dos indicadores** (`conjunto` de cada linha):

| Conjunto | Colunas usadas |
|---|---|
| `ind_disponibilidade_fgeracao_uge_mensal` | `dat_mesreferencia`, `num_unidadegeradora`, `cod_equipamento`, `val_potencia`, `val_dispf`, `val_indisppf`, `val_indispff`, `val_dmdff`, `val_fdff`, `val_tdff`, `id_usina`, `nom_agenteproprietario`, `nom_modalidadeoperacao`, `arquivo_origem` |
| `ind_disponibilidade_fgeracao_uge_anual` | as mesmas, com `din_ano` no lugar de `dat_mesreferencia` |
| `taxa_teif_teip_parametro` | `dat_periodo` (`MM/AAAA`), `nom_unidadegeradora`, `nom_tpinsumo`, `val_parametro`, `num_versao` |
| `taxa_teif_teip` | `din_mes`, `nom_taxa`, `val_taxa`, `num_versao`, `din_calculo` (na falta dela, `din_instante`) |

**Dicionário da EVT**: a chave `dicionario_simplificado` é uma lista de `{codigo, descricao}`. Os itens cujo `codigo` não começa por algarismo são as colunas; o item cujo `codigo` começa por algarismo é a versão, citada como `<descricao> (<codigo>)` (na São Domingos: `Versão 2.0 (06-06-2024)`). Sem esse item, ou com o arquivo ilegível, a versão sai "não identificada".

**Campos do perfil usados**:

| Campo | Uso |
|---|---|
| `usina.slug` | pastas de entrada e de saída |
| `usina.nome` | título e cabeçalho de `validacao_fisica.md`; nome da aba de `evt_tratado.xlsx` |
| `identificacao.cod_usina` | cabeçalho de `validacao_fisica.md` |
| `parametros.potencia_instalada_mw` | limite de potência de R6 |
| `parametros.unidades_geradoras`, `parametros.engolimento_nominal_ug_m3s` | limite de vazão de R6 |
| `parametros.queda_bruta_m`, `parametros.perda_hidraulica_m`, `parametros.rendimento_turbina_gerador` | produtividade nominal e faixa de R8 |
| `usina.tipo` (ou o prefixo do CEG) e `[cobertura]` | caminho (série de referência, `serie_referencia.escolher`), conjuntos tratados (`registro.conjuntos_da_usina`) e nível de cada um (`registro.nivel_coletado`) |
| `[[identificacao.planejamento]]` (`codigo`, `inicio`, `fim`, em `AAAA-MM`) | códigos de planejamento do despacho e do CVU, cada um no seu período |
| `usina.subsistema` | subsistema do CMO |

`descricoes(perfil)` também recebe os identificadores da usina, mas o Tratamento usa das descrições só `colunas_valor`, `convencao_hora`, `nivel` e `pacote` (no log).

**Não lidos**: nada de `data/raw/` (dados, versões anteriores e dicionários); da pasta da Coleta, `auditoria_evt.csv`, `auditoria_indicadores.csv`, `cadastro_ficha.csv`, `auditoria_cadastro.csv`, `dicionarios.csv`, `datas_obtencao.csv`, `composicao_conjunto.csv`, `capacidade_ficha.csv`, `capacidade_membros.csv`, `tipo_publicado.csv` e as auditorias deles, nem `auditoria_restricao_membros.csv`; nem cópias `.bak` ou temporários.

---

## 2. Saídas

### 2.1 Base de EVT tratada: `evt_tratado.parquet`, `evt_tratado.xlsx`, `evt_tratado.csv`

Uma linha por registro horário da EVT: os mesmos registros de `evt_extraido.csv`, na mesma ordem (cronológica). O conteúdo é o mesmo nos três arquivos.

| Coluna | Tipo (pandas → Parquet) | Descrição |
|---|---|---|
| `id_subsistema`, `nom_subsistema`, `nom_bacia`, `nom_rio`, `nom_agente`, `nom_reservatorio` | texto → `large_string` | identificação como publicada, sem espaços nas bordas |
| `cod_usina` | `Int64` → `int64` | código da usina; inválido fica vazio |
| `din_instante` | data e hora sem fuso → `timestamp[us]` | hora de início do registro |
| `val_geracao` | `float64` → `double` | geração (MWmed) |
| `val_disponibilidade` | `float64` → `double` | disponibilidade declarada (MWmed) |
| `val_vazaoturbinada` | `float64` → `double` | vazão turbinada (m³/s) |
| `val_vazaovertida` | `float64` → `double` | vazão vertida (m³/s) |
| `val_vazaovertidanaoturbinavel` | `float64` → `double` | vazão vertida não turbinável (m³/s) |
| `val_produtividade` | `float64` → `double` | produtividade (MW/(m³/s)) |
| `val_folgadegeracao` | `float64` → `double` | folga de geração (MWmed) |
| `val_energiavertida` | `float64` → `double` | energia vertida (MWmed) |
| `val_vazaovertidaturbinavel` | `float64` → `double` | vazão vertida turbinável (m³/s) |
| `val_energiavertidaturbinavel` | `float64` → `double` | energia vertida turbinável (MWmed) |
| `arquivo_origem` | texto → `large_string` | arquivo bruto do registro |
| `tipo_match` | texto → `large_string` | critério de identificação da Coleta (na São Domingos, sempre `CODIGO_E_NOME`) |
| `anomalia_limite_fisico` | `bool` | viola R6 |
| `anomalia_geracao_acima_disponibilidade` | `bool` | viola R7 |
| `anomalia_produtividade` | `bool` | viola R8 |
| `anomalia_geracao_sem_vazao_turbinada` | `bool` | viola R9 |
| `qualidade_registro` | texto → `string` | `OK` ou os códigos violados, na ordem R6 a R9, separados por `;` |

As unidades são as do dicionário da EVT. Sem `arquivo_origem` ou `tipo_match` na entrada, a base sai sem essas colunas.

| Formato | Particularidades |
|---|---|
| Parquet | `pyarrow`, sem índice |
| Planilha | uma aba de nome `evt.nome_aba(perfil)`: `usina.nome` sem acentos, em maiúsculas, com `_` no lugar dos espaços e dos caracteres de `CARACTERES_PROIBIDOS_ABA` (`\ / ? * : [ ]`), cortado em `TAMANHO_MAXIMO_ABA` = 31 caracteres (na São Domingos, `UHE_SAO_DOMINGOS`); grandezas e `cod_usina` em células numéricas no formato "General"; `din_instante` como data e hora (`YYYY-MM-DD HH:MM:SS`); sinalizações como valores lógicos; cabeçalho congelado (`A2`); largura de cada coluna = maior entre o tamanho do nome e 12, mais 3; propriedade `assinatura_dados` |
| CSV | o número real de 64 bits com todas as suas casas (ex.: `0.3053061224489796`); sinalizações `True` e `False` |

Precisão (decisão do usuário): a EVT extraída é lida pelo conversor padrão do pandas, que pode mudar só o último algarismo significativo do texto (1 ulp; na São Domingos, em 81.692 dos 708.950 valores). Os três formatos guardam esse mesmo número real de 64 bits, sem arredondamento.

### 2.2 Relatório de validação: `validacao_fisica.csv` e `validacao_fisica.md`

`validacao_fisica.csv`: uma linha por regra, de R1 a R9, nessa ordem.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codigo_regra` | texto | `R1` a `R9` |
| `grupo` | texto | `Consistência interna ONS` (R1 a R5) ou `Plausibilidade física` (R6 a R9) |
| `nome_regra` | texto | nome da regra |
| `expressao` | texto | condição avaliada, com os limites da usina no padrão brasileiro (a de R6 vem entre aspas, porque contém `;`) |
| `total_linhas` | inteiro | registros avaliados |
| `conformes` | inteiro | registros sem violação |
| `violacoes` | inteiro | registros com violação |
| `taxa_conformidade_pct` | real, 4 casas | `conformes` ÷ `total_linhas` × 100 (100 sem registros) |
| `desvio_maximo` | real, 6 casas | desvio da regra (seção 5.2) |
| `desvio_medio` | real, 6 casas | média das diferenças absolutas em R4 e R5; 0 nas demais |
| `status` | texto | `CONFORME` (nenhuma violação) ou `VIOLADA` |

`validacao_fisica.md` (UTF-8, fim de linha do sistema):

| Parte | Conteúdo |
|---|---|
| Título | `# Relatório de Validação dos Dados - <usina.nome>` |
| Cabeçalho | `**Usina**: <usina.nome> (cod_usina <identificacao.cod_usina> nos arquivos do ONS)`; versão do dicionário; tolerância das identidades (`0.0001`); faixa de R8 (3 casas) e produtividade nominal (4 casas) |
| `## 1. Resultado das regras` | tabela com Regra, Grupo, Descrição, Expressão, Registros, Violações, % com violação (3 casas) e Status |
| `## 2. Leitura dos resultados` | uma frase por regra e a ressalva de que R1 a R5 não atestam a correção dos valores e R6 a R9 usam os parâmetros da usina |
| `## 3. Registros sinalizados (<n> no total; primeiros <k> em ordem cronológica)` | até 40 registros, com Data/hora (`DD/MM/AAAA HHh`), Regras, Geração (MW, 3 casas), Disponibilidade (MW, 3 casas), Vazão turbinada (m³/s, 1 casa) e Produtividade (3 casas) |

Frases: sem violação, `- **R<n>** (<nome>): nenhuma violação em <total> registros.`; com violação, `- **R<n>** (<nome>): <n> registro viola a regra` (ou `registros violam`) `(<percentual, 3 casas> do total); desvio máximo de <3 casas>.` Os números saem de `fmt_int`, `fmt_num` e `fmt_pct` (milhar com ponto, decimal com vírgula).

### 2.3 Indicadores

**Unidade geradora (`ug`)**: é o rótulo que o ONS publica, sem espaços. Nos indicadores, ele vem de `num_unidadegeradora`. Nos parâmetros das taxas, vem do último termo de `nom_unidadegeradora` antes da sigla do estado. Nos dados de 29/10/2026, os dois são iguais em todas as 126.307 linhas dos indicadores.
- **Formato**: rótulo só de algarismos perde os zeros à esquerda ("07" vira "7"). "UG" seguido só de algarismos vale o número ("UG1" vira "1"): a UHE Santa Branca publica "UG1" e "UG2" nos parâmetros das taxas até 2025 e "1" e "2" nos indicadores e nos parâmetros de 2026.
- **Tipo**:
  - inteiro, quando todos os rótulos da usina são só algarismos (todas as usinas com perfil até 29/10/2026);
  - texto, quando algum tem letra. Exemplos: o ciclo combinado da UTE Três Lagoas ("1A", "1B", "1C", "2A", "2B", "2C"), "TG10", "ST1", e Itaipu, que mistura "1" a "18" com "9A" e "G18A".
- **Mesmo tipo nas três tabelas**: a Conferência e as Análises juntam as tabelas por mês e unidade. Por isso as três têm o mesmo tipo, e a leitura do CSV refaz a mesma escolha.
- **Ordem**: a ordem de `ug` é a natural. "2" vem antes de "10", "18" antes de "18A", "1A" antes de "1B" e de "2A", e "TG4" antes de "TG10".
- **Sem rótulo**: a linha fica com `ug` vazio, e o log informa quantas linhas ficaram assim.
- **No texto e nas tabelas**: a unidade aparece como "UG" seguido do rótulo ("UG1", "UG1A"). Quando o rótulo começa por letra, há um espaço entre os dois ("UG TG10").

`indicadores_ug_mensal.csv`: uma linha por mês e UG, em ordem de `mes` e `ug`.

| Coluna | Tipo | Origem |
|---|---|---|
| `mes` | data (dia 1) | `dat_mesreferencia` |
| `ug` | inteiro ou texto (rótulo com letra) | `num_unidadegeradora` |
| `cod_equipamento` | texto | `cod_equipamento` |
| `potencia_mw` | real | `val_potencia` |
| `dispf`, `indisppf`, `indispff`, `dmdff`, `fdff`, `tdff` | real | `val_dispf` a `val_tdff`, como publicados (vírgula decimal aceita) |
| `id_usina` | texto | `id_usina` |
| `agente` | texto | `nom_agenteproprietario` |
| `modalidade` | texto | `nom_modalidadeoperacao` |
| `arquivo_origem` | texto | arquivo da linha mantida |

`indicadores_ug_anual.csv`: uma linha por ano e UG, com as mesmas colunas e `ano` (inteiro, de `din_ano`) no lugar de `mes`.

`horas_estado_mensal.csv`: uma linha por mês e UG, em ordem de `mes` e `ug`.

| Coluna | Tipo | Origem |
|---|---|---|
| `mes` | data (dia 1) | `dat_periodo` |
| `ug` | inteiro ou texto (rótulo com letra) | último termo de `nom_unidadegeradora`, antes da sigla do estado |
| `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HDCE`, `HEDP`, `HEDF` | real (h) | `val_parametro` de cada `nom_tpinsumo`, na maior versão |
| `num_versao` | real | maior versão usada no mês e UG |
| `residuo_identidade_h` | real (h) | HP − (HS + HRD + HDP + HDF + HDCE + HEDP + HEDF) |
| `potencia_mw` | real | potência da UG nos indicadores mensais do mesmo mês; vazia se não houver |

`teifa_teip_mensal.csv`: uma linha por mês, em ordem de `mes`.

| Coluna | Tipo | Origem |
|---|---|---|
| `mes` | data (dia 1) | `din_mes` |
| `teifa`, `teip` | real, fração de 0 a 1 | `val_taxa` das linhas com `nom_taxa` `TEIFA` e `TEIP` (comparação em maiúsculas), na maior versão |
| `num_versao` | real | maior versão do mês |
| `din_calculo` | data e hora | data de cálculo mais recente do mês (no CSV, sem frações de segundo) |

`indicadores.xlsx`: abas nesta ordem, todas com cabeçalho congelado, datas como data e hora, números no formato "General" e a propriedade `assinatura_dados`.

| Aba | Conteúdo |
|---|---|
| `UG_MENSAL` | a tabela de `indicadores_ug_mensal.csv` |
| `UG_ANUAL` | a tabela de `indicadores_ug_anual.csv` |
| `HORAS_ESTADO_UG_MENSAL` | a tabela de `horas_estado_mensal.csv` |
| `TEIFA_TEIP_MENSAL` | a tabela de `teifa_teip_mensal.csv` |
| `SIGLAS_HORAS` | `sigla` e `descricao` das oito siglas de HP a HEDF (`indicadores.INSUMOS_HORAS`) |

Conjunto sem linhas da usina: a tabela é gravada sem linhas e sem colunas (CSV só com a quebra de linha; aba vazia).

### 2.4 Programação

`programacao_horaria.csv`: uma linha por hora de início com ao menos um patamar, dentro do período, em ordem cronológica.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | `dia` + ((`num_patamar` − 1) ÷ 2, divisão inteira) horas |
| `geracao_programada_mw` | real (MW) | média dos patamares da hora (patamar sem valor não entra na média) |
| `patamares` | inteiro | patamares da hora, com ou sem valor (2 = hora completa) |

`programacao_dias_ausentes.csv`: uma linha por dia sem arquivo obtido, do primeiro dia com arquivo até o último dia do período.

| Coluna | Tipo | Descrição |
|---|---|---|
| `dia` | data (`AAAA-MM-DD 00:00:00`) | dia sem arquivo |

A auditoria dos arquivos diários fica na Coleta (`auditoria_programacao.csv`, que marca `INCOMPLETO` o dia sem os 48 patamares). Usina sem programação: as duas tabelas saem só com o cabeçalho.

### 2.5 Séries horárias

`disponibilidade_horaria.csv`, `hidrologia_horaria.csv` e `geracao_horaria.csv`: uma linha por hora de início com valor da usina, dentro do período, sem hora repetida, em ordem cronológica.

| Arquivo | Colunas, nesta ordem |
|---|---|
| `disponibilidade_horaria.csv` | `din_instante`, `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada`, `qualidade`, `arquivo_origem` |
| `hidrologia_horaria.csv` | `din_instante`, `din_instante_publicado`, `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas`, `val_nivelmontante`, `val_niveljusante`, `val_volumeutil`, `qualidade`, `arquivo_origem` |
| `geracao_horaria.csv` | `din_instante`, `val_geracao`, `qualidade`, `arquivo_origem` |

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | hora de início |
| `din_instante_publicado` | data e hora | só na hidrologia: instante publicado (hora de fim; 23:59 na última hora do dia) |
| `val_*` | real | valores como extraídos, sem correção, nas unidades do dicionário de cada conjunto; vazio quando a fonte não tem valor ou tinha texto não numérico |
| `qualidade` | texto | `OK` ou os códigos violados, separados por vírgula (seção 5.3) |
| `arquivo_origem` | texto | arquivo de onde veio o valor mantido |

`disponibilidade_ausencias.csv`, `hidrologia_ausencias.csv` e `geracao_ausencias.csv`: uma linha por mês inteiro ou intervalo contínuo de horas ausentes, em ordem cronológica.

| Coluna | Tipo | Descrição |
|---|---|---|
| `tipo` | texto | `MES_SEM_ARQUIVO`, `MES_SEM_USINA` ou `HORAS` |
| `inicio` | data e hora | primeira hora ausente (no mês inteiro, a primeira hora do mês dentro do período) |
| `fim` | data e hora | última hora ausente |
| `horas` | inteiro | horas ausentes |

`auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv` e `auditoria_geracao.csv`: uma linha por arquivo da auditoria da Coleta, na mesma ordem.

| Coluna | Tipo | Descrição |
|---|---|---|
| `arquivo` | texto | da Coleta |
| `formato` | texto | `CSV` ou `PARQUET` |
| `periodo` | texto | `AAAA` (arquivo anual) ou `AAAA-MM` |
| `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia` | inteiro | da Coleta |
| `horas_usina` | inteiro | horas distintas da usina no arquivo, já na hora de início, antes das duplicatas e do recorte; 0 se o arquivo não foi obtido |
| `valores_invalidos` | inteiro | da Coleta |
| `duplicatas_conflitantes` | inteiro | horas deste arquivo descartadas porque outro arquivo, lido depois, trouxe valor diferente |
| `recursos_duplicados_catalogo` | inteiro | da Coleta |
| `status` | texto | da Coleta: `PROCESSADO` ou `SEM_REGISTROS` |
| `mensagem` | texto | da Coleta |

As colunas `data_publicacao` e `obtido` da auditoria da Coleta não são gravadas aqui.

### 2.6 Cópias e temporários

| Arquivo | Quando existe |
|---|---|
| `<arquivo>.bak` | versão imediatamente anterior; criado ou substituído só quando o arquivo fica `ALTERADO`; no máximo um por arquivo |
| `<arquivo>.tmp`, `<arquivo>.bak.tmp` | só durante a gravação; removidos no sucesso, na falha e na interrupção pelo usuário (seção 5.6) |

Nenhuma etapa lê esses arquivos como dado: os leitores usam nomes explícitos.

### 2.7 Base horária comum: `base_horaria.csv` (usinas sem EVT)

Uma linha por hora da série de referência tratada, dentro do período, em ordem cronológica. As horas ausentes da série de referência não têm linha: ficam em `geracao_ausencias.csv` ou, quando a série de referência é a restrição com detalhe, em `restricao_ausencias.csv`.

| Coluna | Tipo | Origem |
|---|---|---|
| `din_instante` | data e hora | hora de início da série de referência |
| `geracao_mw` | real (MW) | `val_geracao` de `geracao_horaria.csv` ou, na restrição com detalhe, `val_geracaoverificada` de `restricao_horaria.csv` |
| `nivel` | texto | `nivel` de `geracao_complemento.parquet` na hora; sem ele, o primeiro nível da série de referência (`usina` ou `conjunto`) |
| `disponibilidade_operacional_mw`, `disponibilidade_sincronizada_mw` | real (MW) | `val_dispoperacional` e `val_dispsincronizada` de `disponibilidade_horaria.csv`; vazias sem a disponibilidade tratada ou, na restrição com detalhe, sem a disponibilidade no nível da usina |
| `geracao_programada_mw` | real (MW) | `programacao_horaria.csv`; vazia sem a programação tratada ou, na restrição com detalhe, sem a programação no nível da usina |
| `trecho` | inteiro | número do primeiro trecho de `trechos.csv` que contém a hora; vazio fora de todo trecho |
| `sinalizacoes` | texto | códigos separados por vírgula, nesta ordem: a `qualidade` da geração (G1), a da disponibilidade (D1 a D4) e `R7`; vazio sem sinalização |

`R7` marca `geracao_mw` > `disponibilidade_operacional_mw` + 1,0 MW (`TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW`), só com `nivel` = `usina`; comparação com vazio não marca. G1 aqui é o código de qualidade da geração (seção 5.3), não a conferência G1 da spec da Conferência.

### 2.8 Térmicas: despacho, CVU e CMO

`despacho_unidades_horario.csv`: uma linha por hora de início e código de planejamento, em ordem de `din_instante` e `codigo`, só com os códigos de `[[identificacao.planejamento]]` e, em cada um, só as horas do período dele dentro do período de referência.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | hora de início do intervalo |
| `codigo` | inteiro | código de planejamento (`cod_usinaplanejamento`, publicado ora inteiro, ora decimal) |
| `nom_tipopatamar` | texto | patamar de carga publicado |
| `val_prog*` (17) e `val_verif*` (15) | real (MW) | geração programada e verificada de cada motivo, como publicadas (seção 1) |
| `tip_restricaoeletrica` | real | como publicado |
| `arquivo_origem` | texto | arquivo da linha mantida |

`despacho_horario.csv`: uma linha por hora com alguma unidade, em ordem cronológica: `din_instante`, `unidades` (quantos códigos têm a hora), `codigos` (os códigos separados por `;`) e as 32 colunas por motivo, somadas as unidades (coluna sem valor em todas as unidades: vazia).

`despacho_ausencias.csv`: `codigo`, `tipo`, `inicio`, `fim`, `horas`; as ausências de cada código no período dele, pela regra da seção 5.5.

`cvu_semanal.csv`: uma linha por código e semana operativa que se sobrepõe ao período, em ordem de `semana_inicio` e `codigo`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `codigo` | inteiro | código de planejamento |
| `semana_inicio`, `semana_fim` | data | sábado e sexta da semana operativa (`din_instante` e `dat_fimsemana` publicados) |
| `num_revisao` | real | revisão mantida, a mais recente |
| `val_cvu` | real (R$/MWh) | CVU publicado, sem correção |
| `sinal_cvu` | texto | `ausente`, `zero`, `negativo` ou vazio |
| `revisoes` | inteiro | revisões publicadas da semana |
| `arquivo_origem` | texto | arquivo da linha mantida |

`cmo_semanal.csv`: uma linha por semana operativa que se sobrepõe ao período, em ordem de `semana_inicio`: `subsistema` (`usina.subsistema`), `semana_inicio` (sábado da semana que contém a data publicada), `semana_fim` (`semana_inicio` + 6 dias), `din_instante_publicado`, `val_cmomediasemanal`, `val_cmoleve`, `val_cmomedia`, `val_cmopesada` (R$/MWh) e `arquivo_origem`.

`cvu_ausencias.csv` e `cmo_ausencias.csv`: `codigo` (no CMO, o subsistema), `inicio` (sábado), `fim` (sexta) e `semanas`; uma linha por intervalo contínuo de semanas operativas sem registro, no período de cada código (no CMO, no período de referência).

`auditoria_despacho.csv`: as colunas de `auditoria_<conjunto>.csv` (seção 2.5), com `horas_usina` = horas distintas no arquivo e `duplicatas_conflitantes` por hora e código. `auditoria_cvu.csv` e `auditoria_cmo.csv`: as mesmas, com `semanas_usina` (semanas distintas no arquivo) no lugar de `horas_usina`.

O CVU e o CMO não são gravados em hora: `termica.semanal_em_horas` os leva à hora (sábado 00h a sexta 23h) só na leitura pelas Análises.

### 2.9 Eólicas e solares: restrição, razão, fator de capacidade e membros

`restricao_semi_horaria.csv`: uma linha por semi-hora das horas do período, em ordem cronológica, a do arquivo publicado por último.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | início da meia hora (00:00 a 23:30) |
| `val_geracaoverificada`, `val_geracaoestimada` | real (MW) | como publicadas |
| `val_recurso` | real | vento (m/s) nas eólicas; irradiância (W/m²) nas solares |
| `flg_recurso_invalido`, `flg_geracaorestrita` | real | marcas publicadas (1 ou 0); `flg_geracaorestrita` vazia nos arquivos sem a coluna |
| `sinal_recurso_invalido` | bool | `flg_recurso_invalido` = 1 |
| `sinal_estimada_ausente` | bool | `val_geracaoestimada` = 0 e `val_geracaoverificada` > 1,0 MW (`LIMIAR_GERACAO_PARADA_MW`) |
| `restrita` | bool | `flg_geracaorestrita` = 1 |
| `sem_marca_restricao` | bool | `flg_geracaorestrita` vazia |
| `energia_cortada_mwh` | real (MWh) | máx(estimada − verificada, 0) × 0,5 nas restritas; 0 nas não restritas; vazia sem a marca e na restrita com a estimativa ausente |
| `cod_razaorestricao` | texto | razão da mesma semi-hora na restrição com a razão: `REL`, `CNF`, `ENE` ou vazio |
| `nivel_razao` | texto | nível da restrição com a razão; vazio sem ela |
| `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene` | real | minutos de cada razão na semi-hora |
| `arquivo_origem` | texto | arquivo da linha mantida |

`restricao_horaria.csv`: uma linha por hora com as duas meias-horas com `val_geracaoverificada`, em ordem cronológica.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | hora de início |
| `val_geracaoverificada`, `val_recurso` | real | média das duas meias-horas |
| `val_geracaoestimada` | real (MW) | média das meias-horas sem a estimativa ausente; vazia se as duas a têm |
| `semi_horas_recurso_invalido`, `semi_horas_estimada_ausente`, `semi_horas_restritas` | inteiro | meias-horas da hora com cada marca (0 a 2) |
| `energia_cortada_mwh` | real (MWh) | soma das duas meias-horas; vazia se as duas são vazias |

`restricao_ausencias.csv`: `tipo`, `inicio`, `fim`, `horas`, pela regra da seção 5.5, sobre as horas de `restricao_horaria.csv` (a hora incompleta conta como ausente). `auditoria_restricao_detalhe.csv`: as colunas de `auditoria_<conjunto>.csv`, com `horas_usina` = semi-horas distintas da usina no arquivo e as duplicatas conflitantes por semi-hora.

`restricao_razao_semi_horaria.csv`: uma linha por semi-hora das horas do período, em ordem cronológica, a do arquivo publicado por último: `din_instante`, `nivel` (`usina` ou `conjunto`), `val_geracao`, `val_geracaolimitada`, `val_disponibilidade`, `val_geracaoreferencia`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene`, `cod_razaorestricao` (em maiúsculas, vazio sem razão) e `arquivo_origem`. A razão não tem arquivo de ausências nem auditoria no Tratamento: as repetições entre arquivos são resolvidas sem contagem, e a auditoria da extração fica na Coleta.

`fator_capacidade_horario.csv`: série horária pelo motor das séries (seção 5.5), em ordem cronológica.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | hora de início |
| `nivel` | texto | `usina` ou `conjunto`, o da cobertura |
| `val_geracaoprogramada`, `val_geracaoverificada`, `val_capacidadeinstalada`, `val_fatorcapacidade` | real | como publicados |
| `sinal_fc_fora_0_1` | bool | `val_fatorcapacidade` < 0 ou > 1 |
| `sinal_acima_capacidade` | bool | `val_geracaoverificada` > `val_capacidadeinstalada` + 1,0 MW |
| `arquivo_origem` | texto | arquivo do valor mantido |

`fator_capacidade_ausencias.csv` e `auditoria_fator_capacidade.csv`: como os da seção 2.5. O fator de capacidade não tem a coluna `qualidade`: um valor não numérico chega vazio da Coleta e não é sinalizado.

`restricao_membros_horaria.csv` (só com os membros do conjunto no perfil e com linhas): `din_instante`, `id_ons` e `val_geracaoverificada`, a média das duas meias-horas de cada membro (hora incompleta fora), em ordem de `id_ons` e `din_instante`. Só para a G2; não entra na base horária.

---

## 3. Objetos em memória e entre etapas

### 3.1 `ResultadoEtapa` (`src/pipeline.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `codigo` | `int` | 0 ou 1 |
| `arquivos` | `List[Path]` | arquivos gravados na execução, na ordem (`registrar_gravacoes`) |
| `resumo` | `Dict[str, Any]` | seção 4 |

### 3.2 `RegraResultado` (`src/tratamento/validacao.py`)

| Campo | Tipo |
|---|---|
| `codigo_regra`, `grupo`, `nome_regra`, `expressao`, `status` | `str` |
| `total_linhas`, `conformes`, `violacoes` | `int` |
| `taxa_conformidade`, `desvio_maximo`, `desvio_medio` | `float`, sem arredondamento (o CSV arredonda) |

### 3.3 `SerieConjunto` (`src/tratamento/series.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `horaria` | `DataFrame` | série da seção 2.5; em memória, também `_nao_numerico` e `_ordem` (ordem de leitura do arquivo), que não são gravadas |
| `ausencias` | `DataFrame` | colunas `COLUNAS_AUSENCIAS` |
| `auditoria` | `DataFrame` | colunas `COLUNAS_AUDITORIA` |

### 3.4 `IndicadoresONS` (`src/tratamento/indicadores.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `ug_mensal`, `ug_anual`, `horas_estado`, `taxas` | `DataFrame` | tabelas da seção 2.3 |
| `divergencias` | `DataFrame` | vazia no Tratamento; as Análises a preenchem com o resultado da Conferência |
| `auditoria` | `DataFrame` | vazia no Tratamento |

### 3.5 `ProgramacaoONS` (`src/tratamento/programacao.py`)

| Campo | Tipo | Conteúdo |
|---|---|---|
| `horaria`, `dias_ausentes` | `DataFrame` | tabelas da seção 2.4 |
| `auditoria` | `DataFrame` | auditoria da Coleta nas colunas `COLUNAS_AUDITORIA_RELATORIO` (`arquivo`, `dia`, `linhas_lidas`, `linhas_usina`, `linhas_codigo_sem_conferencia`, `patamares`, `data_interna_confere`, `status`); não é gravada pelo Tratamento |

### 3.6 Persistência (`src/comum/persistencia.py`)

| Nome | Tipo | Papel |
|---|---|---|
| `ResultadoGravacao` | `str`, `Enum` | `NOVO`, `ALTERADO`, `INALTERADO` |
| `ErroPersistencia(destino, motivo)` | exceção (subclasse de `ONSError`) | falha de gravação, com o arquivo restaurado; vira código 1 |
| `registrar_gravacoes()` | gerenciador de contexto | lista (arquivo, resultado) de cada gravação feita dentro do bloco |
| `gravar_csv(tabela, destino, copia=True, **opcoes)` | função | CSV do pandas; padrão `;`, UTF-8, sem índice, datas `%Y-%m-%d %H:%M:%S` |
| `gravar_linhas_csv(cabecalho, linhas, destino, delimitador=";")` | função | CSV com o módulo `csv` (usada pela Coleta na EVT extraída e na auditoria da EVT) |
| `gravar_parquet(tabela, destino)` | função | Parquet com `pyarrow`, sem índice |
| `gravar_planilha(abas, destino, formatar=None)` | função | xlsx com `openpyxl`, abas na ordem, `formatar(writer)` para larguras e painéis, propriedade `assinatura_dados` |
| `gravar_texto(texto, destino, newline=None)` | função | texto UTF-8 com o fim de linha do sistema |
| `gravar_bytes(conteudo, destino, copia=True)` | função | bytes (resultados serializados da Conferência e das Análises) |
| `assinatura_dados(abas)`, `ler_assinatura(caminho)` | funções | calcula a assinatura; lê a assinatura de `docProps/custom.xml` sem abrir as abas |

`assinatura_dados` = SHA-256 de, para cada aba na ordem, o nome da aba, uma quebra de linha e o CSV da aba (`;`, sem índice, fim de linha `\n`, datas `%Y-%m-%d %H:%M:%S`). A Coleta e o Tratamento gravam com `.bak` (padrão); a Conferência e as Análises usam `copia=False`, que mantém a conferência e a restauração em falha, sem `.bak`.

Na interrupção pelo usuário (`KeyboardInterrupt`), a gravação também restaura a versão anterior e remove os temporários, mas não vira `ErroPersistencia`: a interrupção segue até `executar_etapa`, que a registra com código 1.

### 3.7 Leitores oferecidos às etapas seguintes

| Função ou arquivo | Devolve | Usado por |
|---|---|---|
| `disponibilidade.carregar_disponibilidade_tratada(pasta)` | `SerieConjunto`, ou `None` sem a série | Conferência, Análises |
| `hidrologia.carregar_hidrologia_tratada(pasta)` | `SerieConjunto`, ou `None` | Conferência, Análises |
| `geracao.carregar_geracao_tratada(pasta)` | `SerieConjunto`, ou `None` | Conferência, Análises |
| `indicadores.carregar_indicadores_tratados(pasta)` | `IndicadoresONS`, ou `None` se faltar um dos quatro CSV | Conferência, Análises |
| `programacao.carregar_programacao_tratada(pasta, auditoria_coleta)` | `ProgramacaoONS`, ou `None` sem a série | Análises |
| `hidrologia.limpos(hid)` | cópia da série com os valores de H1, H2 e H4 vazios só no campo afetado | conferência das vazões, Análises |
| `evt_tratado.parquet` (`pd.read_parquet`) | base de EVT | Conferência (só as colunas usadas), Análises |
| `validacao_fisica.csv` | resultado das regras | Análises |
| `base_horaria.carregar_base_horaria(pasta)` | base horária comum, com `trecho` inteiro que admite vazio e `sinalizacoes` vazia como texto vazio; `None` na hidrelétrica com EVT | Conferência, Análises |
| `termica.carregar_despacho_tratado(pasta)` | `DespachoTratado` (unidades, horário e ausências), ou `None` sem o despacho | Conferência, Análises |
| `termica.carregar_semanal_tratado(pasta, "cvu" ou "cmo")` | `SemanalTratado` (semanal e ausências), ou `None` | Análises |
| `termica.semanal_em_horas(semanal, colunas, chaves)` | uma linha por hora de cada semana operativa, com as colunas da semana | Análises |
| `renovavel.carregar_renovavel(pasta)` | tabelas `fator_capacidade_horario`, `restricao_semi_horaria`, `restricao_horaria`, `restricao_razao_semi_horaria`, `restricao_membros_horaria` e `restricao_ausencias` (`None` nas ausentes), com as marcas como verdadeiro ou falso | Conferência, Análises |
| `renovavel.em_hora_cheia(semi, colunas_media, colunas_soma, completa)` | hora cheia pela média das duas meias-horas, sem a hora incompleta | Conferência (a restrição com a razão em hora cheia) |

Os leitores convertem em data e hora `din_instante`, `din_instante_publicado`, `inicio`, `fim`, `mes`, `din_calculo`, `dia`, `semana_inicio` e `semana_fim`, e aceitam tabela gravada sem colunas. A etapa não grava objetos serializados (pickle); o formato dos seus arquivos é identificado por `versao_formato` no `etapa.json`.

### 3.8 Objetos dos conjuntos novos

| Objeto | Campos | Conteúdo |
|---|---|---|
| `DespachoTratado` (`termica.py`) | `unidades`, `horario`, `ausencias`, `auditoria` | tabelas da seção 2.8 |
| `SemanalTratado` (`termica.py`) | `semanal`, `ausencias`, `auditoria`, `resumo` | CVU ou CMO (seção 2.8) e o resumo da seção 4 |
| `RestricaoTratada` (`renovavel.py`) | `semi_horaria`, `horaria`, `ausencias`, `auditoria`, `resumo` | tabelas da seção 2.9 e o resumo da seção 4 |
| `SerieConjunto` da restrição (`renovavel.serie_da_referencia`) | `horaria` (`din_instante`, `val_geracao`, `qualidade` `OK`, `arquivo_origem` vazio), `ausencias`, `auditoria` | a restrição com detalhe como série de referência da base horária |

---

## 4. Manifesto da etapa (`etapa.json`)

Os campos comuns (`etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status`, `codigo_saida`, `etapa_anterior`, `arquivos`, `resumo`) e os estados estão no [data-model da Coleta](../001-coleta-dados/data-model.md). No Tratamento:
- `etapa` = `tratamento`; `versao_formato` = 2 (`pipeline.VERSAO_FORMATO`: a base horária comum entrou no formato), conferido pela Conferência e pelas Análises antes de rodar;
- `etapa_anterior` = `{"etapa": "coleta", "concluida_em": <concluida_em da Coleta>}`;
- `arquivos`: os arquivos na ordem de gravação, cada um com `nome`, `bytes` e `sha256`; os `INALTERADO` também entram:
  - hidrelétrica com EVT, 21: `validacao_fisica.md`, `validacao_fisica.csv`, `evt_tratado.xlsx`, `evt_tratado.parquet`, `evt_tratado.csv`, os quatro CSV de indicadores, `indicadores.xlsx`, os dois da programação e, para disponibilidade, hidrologia e geração, a série, as ausências e a auditoria;
  - usinas sem EVT, só os tratados, nesta ordem: indicadores, programação, disponibilidade, hidrologia e geração (como acima); fator de capacidade (série, ausências e auditoria); restrição com detalhe (semi-horária, horária, ausências e auditoria), razão e membros; `base_horaria.csv`; despacho (horário, por unidade, ausências e auditoria), CVU e CMO (semanal, ausências e auditoria). Na UTE William Arjona, 24; na EOL Praia Formosa, 14; na UFV Seriemas 1, 15; na PCH Bandeirante, 6;
- o próprio `etapa.json` não tem `.bak`: é gravado em `etapa.json.tmp` e trocado.

`resumo` com código 0 (FR-033), só com os conjuntos tratados para a usina:

| Campo | Tipo | Conteúdo |
|---|---|---|
| `periodo.inicio`, `periodo.fim` | texto `AAAA-MM-DD HH:MM:SS` | primeiro e último instante da EVT ou, nas usinas sem EVT, o período da série de referência gravado pela Coleta: o período de referência |
| `evt.registros` | inteiro | registros tratados (iguais aos extraídos) |
| `evt.valores_ausentes` | inteiro | células vazias nas dez grandezas |
| `evt.violacoes` | objeto `R1` … `R9` → inteiro | registros que violam cada regra |
| `evt.sinalizados` | inteiro | registros com `qualidade_registro` diferente de `OK` |
| `indicadores.linhas_mensais`, `indicadores.linhas_anuais` | inteiro | linhas de `indicadores_ug_mensal.csv` e `indicadores_ug_anual.csv` |
| `indicadores.meses_unidade_horas_estado` | inteiro | linhas de `horas_estado_mensal.csv` |
| `indicadores.meses_taxas` | inteiro | linhas de `teifa_teip_mensal.csv` |
| `indicadores.meses_unidade_residuo_acima_tolerancia` | inteiro | meses-unidade com \|`residuo_identidade_h`\| > 0,1 h |
| `programacao.horas`, `programacao.dias_ausentes` | inteiro | linhas de `programacao_horaria.csv` e de `programacao_dias_ausentes.csv` |
| `<conjunto>.horas` | inteiro | horas da série tratada (`disponibilidade`, `hidrologia`, `geracao`) |
| `<conjunto>.horas_ausentes` | inteiro | soma de `horas` nas ausências |
| `<conjunto>.horas_sinalizadas` | objeto código → inteiro | horas com cada código; uma hora com dois códigos conta nos dois; `{}` sem sinalização |
| `<conjunto>.duplicatas_conflitantes` | inteiro | soma da coluna na auditoria |
| `base_horaria.horas`, `base_horaria.horas_ausentes` | inteiro | linhas de `base_horaria.csv` e soma das horas nas ausências da série de referência (usinas sem EVT) |
| `base_horaria.niveis` | objeto nível → inteiro | horas por nível |
| `base_horaria.sinalizacoes` | objeto código → inteiro | horas com cada código; `{}` sem sinalização |
| `base_horaria.trechos` | inteiro | trechos distintos com horas na base |
| `despacho.horas`, `despacho.horas_unidade` | inteiro | linhas de `despacho_horario.csv` e de `despacho_unidades_horario.csv` |
| `despacho.codigos` | lista de inteiros | códigos com horas no período |
| `despacho.horas_ausentes`, `despacho.duplicatas_conflitantes` | inteiro | soma de `horas` nas ausências e da coluna na auditoria |
| `cvu.semanas`, `cvu.registros`, `cvu.codigos` | inteiro, inteiro, lista | semanas distintas, linhas de `cvu_semanal.csv` e códigos |
| `cvu.sinalizados` | objeto sinal → inteiro | linhas com cada `sinal_cvu`; `{}` sem sinal |
| `cvu.revisoes_descartadas`, `cvu.duplicatas_conflitantes`, `cvu.semanas_ausentes` | inteiro | revisões anteriores descartadas, conflitos entre arquivos e semanas nas ausências |
| `cmo.semanas`, `cmo.duplicatas`, `cmo.duplicatas_conflitantes`, `cmo.semanas_ausentes` | inteiro | semanas de `cmo_semanal.csv`, semanas repetidas entre publicações, as repetidas com valor diferente e semanas nas ausências |
| `fator_capacidade` | objeto | os campos de `<conjunto>` acima, mais `nivel`, `horas_fc_fora_0_1` e `horas_acima_capacidade` |
| `restricao_razao.semi_horas`, `restricao_razao.nivel`, `restricao_razao.semi_horas_por_razao` | inteiro, texto, objeto | linhas de `restricao_razao_semi_horaria.csv`, o nível e as semi-horas por razão (`sem razão` para o código vazio) |
| `restricao_detalhe` | objeto | `semi_horas`, `horas`, `horas_ausentes`, `semi_horas_restritas`, `semi_horas_sem_marca`, `semi_horas_recurso_invalido`, `semi_horas_estimada_ausente`, `semi_horas_restritas_sem_estimativa`, `energia_cortada_mwh` (real) e `duplicatas_conflitantes` |
| `membros_restricao` | objeto id ONS → inteiro | horas de cada membro do conjunto em hora cheia |
| `gravacoes` | objeto resultado → inteiro | arquivos por resultado de gravação; só os resultados que ocorreram aparecem |

Na hidrelétrica com EVT, o `resumo` traz `periodo`, `evt`, `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao` e `gravacoes`. Nas usinas sem EVT, não há `evt`, e entram só os campos dos conjuntos tratados, mais `base_horaria`.

Outros casos:
- **Violação de R1**: `resumo` com `periodo` e `evt` (sem `sinalizados`), `arquivos` vazio, `status` `falha`, `codigo_saida` 1.
- **Exceção**: `resumo` = `{"erro": "<mensagem>"}`, `status` `falha`, `codigo_saida` 1.
- **Interrupção pelo usuário (Ctrl+C)**: `resumo` = `{"erro": "interrompida pelo usuário"}`, `status` `falha`, `codigo_saida` 1; a Conferência recusa rodar até um novo Tratamento concluído.
- **Código 5**: nenhum `etapa.json` é gravado; o anterior, se houver, fica como estava.

Na São Domingos, com a Coleta congelada da referência (execução com os 21 arquivos `INALTERADO`; as 2.546 horas hidrológicas sinalizadas somam 2.550 por código, porque 4 têm `H1,H2`):

```json
{
 "periodo": {"inicio": "2018-08-28 00:00:00", "fim": "2026-09-28 23:00:00"},
 "evt": {"registros": 70895, "valores_ausentes": 0,
         "violacoes": {"R1": 0, "R2": 0, "R3": 0, "R4": 0, "R5": 0, "R6": 1, "R7": 293, "R8": 185, "R9": 63},
         "sinalizados": 526},
 "indicadores": {"linhas_mensais": 196, "linhas_anuais": 18, "meses_unidade_horas_estado": 160, "meses_taxas": 61,
                 "meses_unidade_residuo_acima_tolerancia": 0},
 "programacao": {"horas": 16992, "dias_ausentes": 20},
 "disponibilidade": {"horas": 70895, "horas_ausentes": 1, "horas_sinalizadas": {}, "duplicatas_conflitantes": 0},
 "hidrologia": {"horas": 70760, "horas_ausentes": 136, "horas_sinalizadas": {"H1": 216, "H2": 2321, "H4": 13},
                "duplicatas_conflitantes": 0},
 "geracao": {"horas": 70895, "horas_ausentes": 1, "horas_sinalizadas": {}, "duplicatas_conflitantes": 0},
 "gravacoes": {"INALTERADO": 21}
}
```

Na UTE William Arjona (usina sem EVT, com o despacho, o CVU e o CMO; 24 arquivos):

```json
{
 "periodo": {"inicio": "2021-07-10 00:00:00", "fim": "2026-10-18 23:00:00"},
 "indicadores": {"linhas_mensais": 314, "linhas_anuais": 30, "meses_unidade_horas_estado": 309, "meses_taxas": 61,
                 "meses_unidade_residuo_acima_tolerancia": 0},
 "programacao": {"horas": 5760, "dias_ausentes": 20},
 "disponibilidade": {"horas": 46243, "horas_ausentes": 5, "horas_sinalizadas": {}, "duplicatas_conflitantes": 0},
 "geracao": {"horas": 46243, "horas_ausentes": 5, "horas_sinalizadas": {}, "duplicatas_conflitantes": 0},
 "base_horaria": {"horas": 46243, "horas_ausentes": 5, "niveis": {"usina": 46243}, "sinalizacoes": {"R7": 1322},
                  "trechos": 3},
 "despacho": {"horas": 46248, "horas_unidade": 85104, "codigos": [334, 434], "horas_ausentes": 624,
              "duplicatas_conflitantes": 61},
 "cvu": {"semanas": 274, "registros": 541, "codigos": [334, 434], "sinalizados": {"zero": 366},
         "revisoes_descartadas": 0, "duplicatas_conflitantes": 0, "semanas_ausentes": 8},
 "cmo": {"semanas": 276, "duplicatas": 0, "duplicatas_conflitantes": 0, "semanas_ausentes": 0},
 "gravacoes": {"ALTERADO": 1, "INALTERADO": 23}
}
```

---

## 5. Regras, estados e validações

### 5.1 Tolerâncias e limites

| Regra ou limite | Valor | Onde fica | Uso |
|---|---|---|---|
| ε das identidades | 0,0001 | `regras.PHYSICAL_TOLERANCE_EPSILON` | R1 (valor < −ε), R2 e R3 (diferença < −ε), R4 e R5 (diferença absoluta > ε) |
| folga sobre os nominais | 5 % | `regras.TOLERANCIA_LIMITES_FISICOS` | limites de R6 |
| limite de potência | `potencia_instalada_mw` × 1,05 | `Perfil.limite_potencia_mw` | R6 em `val_geracao`, `val_disponibilidade`, `val_folgadegeracao` e `val_energiavertidaturbinavel` |
| limite de vazão | `unidades_geradoras` × `engolimento_nominal_ug_m3s` × 1,05 | `Perfil.limite_vazao_turbinavel_m3s` | R6 em `val_vazaoturbinada` e `val_vazaovertidaturbinavel` |
| produtividade nominal | 1000 × 9,81 × (`queda_bruta_m` − `perda_hidraulica_m`) × `rendimento_turbina_gerador` ÷ 1.000.000 | `Perfil.produtividade_nominal_mw_m3s` | R8 |
| faixa de produtividade | 0,70 a 1,30 × nominal | `regras.FAIXA_PRODUTIVIDADE_RELATIVA`, `validacao.faixa_produtividade` | R8 |
| geração acima da disponibilidade | 1,0 MW | `regras.TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW` | R7 |
| geração com vazão turbinada nula | 1,0 MW | `regras.LIMIAR_GERACAO_PARADA_MW` (o mesmo da usina parada) | R9 |
| D1 e D2 | 0,01 MW | `regras.TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW` | disponibilidade |
| H4 | 10 m da mediana | `regras.DESVIO_MAXIMO_NIVEL_M` | hidrologia |
| identidade das horas | 0,1 h | `regras.TOLERANCIA_IDENTIDADE_HORAS` | aviso no log e `meses_unidade_residuo_acima_tolerancia` |
| registros sinalizados no Markdown | 40 | parâmetro `limite_linhas_anomalias` de `gerar_relatorio_validacao_md` | relatório de validação |
| nome da aba da planilha da EVT | até 31 caracteres; `\ / ? * : [ ]` viram `_` | `evt.TAMANHO_MAXIMO_ABA`, `evt.CARACTERES_PROIBIDOS_ABA` | `evt.nome_aba` |
| geração acima da disponibilidade na base horária | 1,0 MW | `regras.TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW` | R7 de `base_horaria.csv` |
| geração acima da capacidade instalada | 1,0 MW | `regras.TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW` | `sinal_acima_capacidade` |
| estimativa ausente | estimada 0 com verificada > 1,0 MW | `regras.LIMIAR_GERACAO_PARADA_MW` | `sinal_estimada_ausente` |
| duração da semi-hora | 0,5 h | `regras.DURACAO_SEMI_HORA_H` | energia cortada |
| semana operativa | sábado a sexta | `termica.SABADO`, `termica.inicio_da_semana_operativa` | CVU, CMO e semanais em hora |

Na São Domingos: 50,4 MW, 171,15 m³/s (171,2 no relatório), produtividade nominal de 0,3063 e faixa de 0,214 a 0,398 MW/(m³/s).

### 5.2 Regras R1 a R9 (`validar_regras_fisicas` e `mascaras_plausibilidade`)

| Regra | O registro viola quando | `desvio_maximo` |
|---|---|---|
| R1 | alguma das dez grandezas < −ε | valor absoluto do menor valor da base, se houver violação |
| R2 | `val_energiavertida` − `val_energiavertidaturbinavel` < −ε | maior déficit entre os registros violados |
| R3 | `val_vazaovertida` − (`val_vazaovertidaturbinavel` + `val_vazaovertidanaoturbinavel`) < −ε | maior déficit entre os registros violados |
| R4 | \|`val_energiavertidaturbinavel` − `val_vazaovertidaturbinavel` × `val_produtividade`\| > ε | maior diferença absoluta na base (e a média em `desvio_medio`) |
| R5 | \|`val_folgadegeracao` − max(0, `val_disponibilidade` − `val_geracao`)\| > ε | maior diferença absoluta na base (e a média em `desvio_medio`) |
| R6 | alguma grandeza com limite (seção 5.1) acima dele | maior excesso sobre o limite |
| R7 | `val_geracao` > `val_disponibilidade` + 1,0 | maior `val_geracao` − `val_disponibilidade` entre os violados |
| R8 | `val_vazaoturbinada` > 0 e `val_produtividade` fora da faixa | maior \|`val_produtividade` − nominal\| entre os violados |
| R9 | `val_vazaoturbinada` ≤ 0 e `val_geracao` > 1,0 | maior `val_geracao` entre os violados |

- A contagem é por registro, não por célula.
- Sem violação, `desvio_maximo` vale 0, menos em R4 e R5, que são apurados sempre.
- Comparação com valor ausente não viola (as máscaras de R6 a R9 usam `fillna(False)`).
- Violação de R1: código 1, antes da sinalização e de qualquer gravação.
- As colunas `anomalia_*` e `qualidade_registro` saem das mesmas máscaras de R6 a R9 usadas na contagem.

### 5.3 Sinalização de qualidade das séries horárias

| Base | Código | Condição no código | Sai do uso nas etapas seguintes | Aplicada por |
|---|---|---|---|---|
| Disponibilidade | D1 | `val_dispsincronizada` > `val_dispoperacional` + 0,01 | a hora inteira | `conferencia.disponibilidade.validas` (Conferência e Análises) |
| Disponibilidade | D2 | `val_dispoperacional` > `val_potenciainstalada` + 0,01 | a hora inteira | idem |
| Disponibilidade | D3 | alguma das três colunas < 0 | a hora inteira | idem |
| Disponibilidade | D4 | `_nao_numerico` | a hora inteira | idem |
| Hidrologia | H1 | alguma das seis vazões < 0 | só a vazão negativa | `hidrologia.limpos` |
| Hidrologia | H2 | `val_volumeutil` < 0 ou > 100 | só o volume útil | `hidrologia.limpos` |
| Hidrologia | H3 | `_nao_numerico` | só o valor não numérico, que já chega vazio | (nenhuma ação) |
| Hidrologia | H4 | \|nível − mediana desse nível na série tratada\| > 10, em `val_nivelmontante` ou `val_niveljusante` | só o nível afastado | `hidrologia.limpos` |
| Geração | G1 | `_nao_numerico` | a hora inteira | filtro `qualidade == "OK"` da conferência da geração |

Os códigos seguem a ordem da tabela e são separados por vírgula. Campo vazio não viola nenhuma regra (comparação com vazio dá falso).

Limitação conhecida: a Coleta não converte vírgula decimal nos conjuntos horários. Um valor como `30,5` chega vazio, com `_nao_numerico`, e recebe D4, H3 ou G1 em vez de virar número.

**Sinalizações dos conjuntos novos** (sem descarte; o valor fica como veio):

| Arquivo | Sinalização | Condição no código | Efeito nas etapas seguintes |
|---|---|---|---|
| `base_horaria.csv` | G1, D1 a D4 | `qualidade` da geração e da disponibilidade na hora | a hora fica na base; contada por código na qualidade dos dados |
| `base_horaria.csv` | R7 | `nivel` = `usina` e `geracao_mw` > `disponibilidade_operacional_mw` + 1,0 | contada; base da regra da conclusão sobre a geração acima da disponibilidade declarada |
| `cvu_semanal.csv` | `sinal_cvu` = `ausente`, `zero` ou `negativo` | `val_cvu` vazio, = 0 ou < 0 | a semana sai da comparação do CVU com o CMO e é contada |
| `restricao_semi_horaria.csv` | `sinal_recurso_invalido` | `flg_recurso_invalido` = 1 | a semi-hora sai do recurso × geração e é contada |
| `restricao_semi_horaria.csv` | `sinal_estimada_ausente` | `val_geracaoestimada` = 0 e `val_geracaoverificada` > 1,0 | a estimada sai dos totais e das médias; na restrita, sem energia cortada |
| `restricao_semi_horaria.csv` | `sem_marca_restricao` | `flg_geracaorestrita` vazia | a semi-hora sai do total da energia cortada e é contada |
| `fator_capacidade_horario.csv` | `sinal_fc_fora_0_1`, `sinal_acima_capacidade` | seção 2.9 | a hora fica no fator de capacidade publicado; as horas sinalizadas são contadas |

O limite físico do recurso (vento acima de 40 m/s, irradiância acima de 1.500 W/m²) não é sinalizado no Tratamento: as Análises o aplicam no recurso × geração.

### 5.4 Enumerações

| Campo | Valores |
|---|---|
| `qualidade_registro` | `OK`, ou códigos de R6 a R9 separados por `;` (na São Domingos: `R7`, `R8`, `R9`, `R7;R8`, `R7;R9` e `R6;R7;R8`) |
| `status` da regra | `CONFORME`, `VIOLADA` |
| `grupo` da regra | `Consistência interna ONS`, `Plausibilidade física` |
| `qualidade` das séries | `OK`, ou códigos da seção 5.3 separados por vírgula (ex.: `H1,H2`) |
| `tipo` da ausência | `MES_SEM_ARQUIVO`, `MES_SEM_USINA`, `HORAS` |
| `status` da auditoria | `PROCESSADO`, `SEM_REGISTROS` (um arquivo `FALHA` encerra a Coleta com código 2, e o Tratamento não roda) |
| resultado da gravação | `NOVO`, `ALTERADO`, `INALTERADO` |
| `status` do `etapa.json` | `concluida` (código 0) ou `falha` (código 1); `desatualizada` quando a Coleta é refeita depois |
| `nivel` (base horária, fator de capacidade, razão) e `nivel_razao` | `usina`, `conjunto` (`nivel_razao` vazio sem a razão) |
| `sinalizacoes` da base horária | vazio, ou `G1`, `D1` a `D4` e `R7` separados por vírgula |
| `sinal_cvu` | vazio, `ausente`, `zero`, `negativo` |
| `cod_razaorestricao` | `REL`, `CNF`, `ENE` ou vazio (sem razão; `sem razão` no resumo) |
| `tipo` da ausência do despacho e da restrição | os mesmos das séries: `MES_SEM_ARQUIVO`, `MES_SEM_USINA`, `HORAS` |

### 5.5 Regras de montagem

| Tabela | Regra |
|---|---|
| Séries horárias | instante na hora de início; entre ocorrências da mesma hora, fica a última na ordem de leitura da Coleta; valores comparados nas colunas de valor, com vazio igual a vazio; só as horas de início a fim, inclusive |
| Ausências | grade horária do período; mês do período sem nenhuma hora da usina é `MES_SEM_USINA` se algum arquivo obtido cobre aquele ano e mês pelo nome (o anual cobre os doze), senão `MES_SEM_ARQUIVO`; nos demais meses, intervalos contínuos `HORAS` |
| Indicadores por UG | chave (`mes` ou `ano`, `ug`); fica a última linha na ordem de leitura (arquivos em ordem de nome); aviso com a quantidade de linhas de chave repetida; meses do mês inicial ao final do período, anos do ano inicial ao final |
| Horas por estado | maior `num_versao` por mês, UG e estado; resíduo acima de 0,1 h só no log; potência juntada pelos indicadores mensais |
| Taxas | maior `num_versao` por mês e taxa; `num_versao` e `din_calculo` do mês são os maiores entre as duas taxas |
| Programação | patamar sem número descartado; com mais de um código, soma por dia e patamar antes da média: cada código vale do primeiro ao último dia em que aparece, e a soma fica vazia se algum código vigente no dia não tem valor no patamar; hora = dia + ((n − 1) ÷ 2); dias ausentes = dias do primeiro dia com arquivo obtido até o dia do fim do período, menos os dias com arquivo obtido |
| Base horária | uma linha por hora da série de referência; disponibilidade e programação juntadas pela hora (a primeira linha de cada hora); nível pelo complemento; trecho pelo primeiro intervalo [`inicio`, `fim`] que contém a hora |
| Despacho | por hora e código, fica a linha do arquivo publicado por último (ordem da auditoria da Coleta); repetidas com valor diferente contadas no arquivo descartado; cada código no período dele (`inicio` no dia 1 do mês; `fim` na última hora do mês; vazio: até o fim do período); soma por hora com `min_count=1`; ausências por código pela regra das séries |
| CVU | por código, semana e revisão, o arquivo publicado por último; depois, por código e semana, a maior revisão; ficam as semanas que se sobrepõem ao período; semanas ausentes por código, em intervalos contínuos |
| CMO | semana = sábado da semana que contém a data publicada; por semana, a publicação mais recente; semanas repetidas contadas; ficam as semanas que se sobrepõem ao período |
| Restrição com detalhe e razão | por semi-hora, o arquivo publicado por último; semi-horas das horas de início a fim do período (a série de referência pode terminar na meia hora); hora cheia só com as duas meias-horas com a geração verificada; ausências sobre a hora cheia |
| Fator de capacidade | o motor das séries horárias (convenção de início), com o nível e as duas sinalizações |
| Membros do conjunto | por id ONS, a última linha de cada semi-hora; hora cheia só com as duas meias-horas |

### 5.6 Gravação segura: estados de um arquivo de dados

| Antes | Conteúdo novo | Resultado | Arquivo | `.bak` |
|---|---|---|---|---|
| não existe | qualquer | `NOVO` | gravado e conferido | não é criado |
| existe | igual (bytes; na planilha, a assinatura) | `INALTERADO` | intocado | intocado |
| existe | diferente | `ALTERADO` | trocado e conferido pelo SHA-256 | passa a ser a versão anterior |
| qualquer | exceção na gravação ou numa conferência | `ErroPersistencia`, código 1 | fica (ou volta) na versão anterior; se não existia, é apagado | intocado |
| qualquer | interrupção pelo usuário (Ctrl+C) durante a gravação | `KeyboardInterrupt`, código 1 | fica (ou volta) na versão anterior; se não existia, é apagado | intocado |

Conferência do temporário, antes da troca:
- CSV: relido como texto, com as linhas e as colunas pretendidas (tabela sem colunas: só a existência);
- Parquet: `num_rows` e `num_columns` dos metadados;
- planilha: abas na ordem, dimensões de cada aba (linhas + cabeçalho, colunas) e assinatura gravada;
- texto: relido igual ao pretendido.

O log registra cada resultado: `NOVO: <arquivo> (<descrição>)`, `ALTERADO: <arquivo> (<descrição>); versão anterior em <arquivo>.bak` ou `INALTERADO: <arquivo> (<descrição>)`. Na falha, `Falha ao gravar <caminho>: <motivo>. O arquivo foi mantido na versão anterior (...)`; na interrupção, `Gravação de <caminho> interrompida; o arquivo foi mantido na versão anterior.`

### 5.7 Erros e códigos de saída

| Situação | Onde | Código |
|---|---|---|
| `coleta/etapa.json` ausente, ilegível, não `concluida` ou com outro `versao_formato` | `pipeline.executar_etapa` | 5, nada gravado |
| EVT extraída ausente | `carregar_base_consolidada` (`FileNotFoundError`) | 1, nada gravado |
| coluna obrigatória ausente na EVT | `carregar_base_consolidada` (`ValueError`) | 1, nada gravado |
| dicionário da EVT ausente | `carregar_dicionario_dados` (`FileNotFoundError`) | 1, nada gravado |
| instante inválido na EVT | `padronizar_tipagem_numerica` (`ValueError`) | 1, nada gravado |
| violação de R1 | `tratar_evt` (retorno) | 1, nada gravado |
| extraído ou auditoria da Coleta ilegível | leitura com pandas ou pyarrow | 1; ficam os arquivos gravados antes |
| falha de gravação | `ErroPersistencia` | 1; o arquivo volta à versão anterior |
| interrupção pelo usuário (Ctrl+C) | `executar_etapa` (`KeyboardInterrupt`) | 1; o arquivo em gravação volta à versão anterior e ficam os gravados antes |
| `cod_usina` inválido, grandeza fora do dicionário, coluna de rastreabilidade ausente, valores ausentes, violações de R2 a R9, resíduo acima de 0,1 h, chave repetida nos indicadores, hora repetida com valor diferente (também no fator de capacidade e, por hora e código, no despacho), horas sinalizadas | aviso no log | 0 |
| semanas do CMO repetidas entre publicações; resumo do despacho e da restrição com detalhe | informação no log | 0 |

---

## 6. Requisitos × saídas

| Requisitos | Entradas e saídas | Seções |
|---|---|---|
| FR-002, FR-006 | `coleta/dicionario_evt.json`; nada de `data/raw/` | 1 |
| FR-003, FR-004 | `coleta/etapa.json` (período das usinas sem EVT); conjuntos pelo tipo e pela cobertura | 1, 4 |
| FR-005 a FR-014 | base de EVT e relatório de validação | 2.1, 2.2, 5.1, 5.2 |
| FR-015 a FR-020 | séries horárias, ausências e auditorias, inclusive as dos conjuntos novos | 2.5, 2.8, 2.9, 5.3, 5.5 |
| FR-021 a FR-025 | indicadores | 2.3 |
| FR-026, FR-027 | programação, com a soma dos códigos | 2.4, 5.5 |
| FR-028 a FR-032 | gravação segura de todos os arquivos de dados | 2.6, 3.6, 5.6 |
| FR-033, FR-034 | `etapa.json` no formato 2 e o `resumo` | 4 |
| FR-035 | `base_horaria.csv` | 2.7, 5.3 |
| FR-036 | `agregados.csv` do catálogo, montado pela Coleta (spec da Coleta de dados) | — |
| FR-037 a FR-040 | `despacho_*`, `cvu_*`, `cmo_*` e as auditorias | 2.8, 5.5 |
| FR-041 a FR-044 | `restricao_*`, `fator_capacidade_*`, `restricao_membros_horaria.csv` e as auditorias | 2.9, 5.3, 5.5 |
