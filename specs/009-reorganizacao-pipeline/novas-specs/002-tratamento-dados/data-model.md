# Data Model: Tratamento de dados

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-08

Convenções de todas as saídas:
- pasta `data/usinas/<slug>/tratamento/`, com os nomes de `src/comum/caminhos.ARQUIVOS_TRATAMENTO`;
- CSV com `;`, ponto decimal, UTF-8 sem BOM, sem índice, datas `AAAA-MM-DD HH:MM:SS` (sem frações de segundo), ausente como célula vazia, verdadeiro e falso como `True` e `False`, fim de linha do sistema (CRLF no Windows) e aspas só no campo que contém `;`;
- instantes sem fuso, no horário publicado pelo ONS; `din_instante` é sempre a hora de início;
- todo arquivo de dados é gravado por `src/comum/persistencia.py` (seções 3.6 e 5.6).

---

## 1. Entradas

| Arquivo | Gravado por | Lido por | Uso |
|---|---|---|---|
| `data/usinas/<slug>/coleta/etapa.json` | Coleta | `pipeline.etapa_anterior_concluida` | pré-requisito: `status` `concluida` e `versao_formato` atual (1) |
| `coleta/evt_extraido.csv` | Coleta | `validacao.carregar_base_consolidada` (`pd.read_csv(sep=";", low_memory=False)`) | base de EVT: 18 colunas obrigatórias, mais `arquivo_origem` e `tipo_match` |
| `coleta/indicadores_extraido.parquet` | Coleta | `indicadores.montar_indicadores` (`separar_conjuntos`) | linhas dos quatro conjuntos de indicadores, com a coluna `conjunto` e as colunas como publicadas (texto) |
| `coleta/programacao_extraido.parquet` | Coleta | `programacao.montar_programacao` | `dia`, `num_patamar`, `geracao_programada_mw`, `arquivo_origem` |
| `coleta/auditoria_programacao.csv` | Coleta | `etapa.ler_auditoria_coleta(..., ["dia"])` | `dia` e `obtido` de cada arquivo diário |
| `coleta/disponibilidade_extraido.parquet`, `hidrologia_extraido.parquet`, `geracao_extraido.parquet` | Coleta | `series.montar_serie`, via `tratar_<conjunto>` | `din_instante` como publicado, colunas de valor, `_nao_numerico` (algum valor não numérico na fonte) e `arquivo_origem` |
| `coleta/auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv`, `auditoria_geracao.csv` | Coleta | `etapa.ler_auditoria_coleta` → `series.montar_serie` | uma linha por arquivo, na ordem de leitura (data de publicação e nome); base da auditoria completa |
| `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json` | Coleta | `validacao.carregar_dicionario_dados` e `versao_dicionario_dados` (caminho de `caminhos.dicionario_evt()`) | colunas descritas e versão do dicionário |
| `usinas/<slug>/perfil.toml` | usuário | `perfil.carregar_perfil`, na linha de comando | campos da tabela abaixo |

`ler_auditoria_coleta` lê `arquivo`, `formato`, `periodo`, `data_publicacao`, `status` e `mensagem` como texto, do jeito que foram gravados (o `periodo` `2018` de um arquivo anual continua texto), converte `obtido` em verdadeiro ou falso e as colunas de data pedidas em data e hora.

Na EVT extraída, a Coleta já troca a vírgula decimal por ponto e deixa vazio o valor não numérico (contado em `valores_invalidos` de `auditoria_evt.csv`, que o Tratamento não lê); a tipagem do Tratamento repete a troca e conta esses vazios no log, junto com os ausentes.

**Colunas de valor dos conjuntos horários** (`DescricaoConjunto.colunas_valor` e `convencao_hora`, declaradas em `src/coleta/conjuntos.py`):

| Conjunto | Colunas de valor | Convenção de hora publicada |
|---|---|---|
| disponibilidade | `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` | início |
| hidrologia | `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas`, `val_nivelmontante`, `val_niveljusante`, `val_volumeutil` | fim (a última hora do dia vem como 23:59) |
| geração | `val_geracao` | início |

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

`descricoes(perfil)` também recebe os identificadores da usina, mas o Tratamento usa das descrições só `colunas_valor`, `convencao_hora` e `pacote` (no log).

**Não lidos**: os arquivos de dados de `data/raw/` e as versões anteriores deles, `auditoria_evt.csv`, `auditoria_indicadores.csv`, `cadastro_ficha.csv`, `auditoria_cadastro.csv`, `dicionarios.csv`, nem cópias `.bak` ou temporários.

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

`indicadores_ug_mensal.csv`: uma linha por mês e UG, em ordem de `mes` e `ug`.

| Coluna | Tipo | Origem |
|---|---|---|
| `mes` | data (dia 1) | `dat_mesreferencia` |
| `ug` | inteiro | `num_unidadegeradora` |
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
| `ug` | inteiro | número no fim de `nom_unidadegeradora` (antes da sigla do estado) |
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

Os leitores convertem em data e hora `din_instante`, `din_instante_publicado`, `inicio`, `fim`, `mes`, `din_calculo` e `dia`, e aceitam tabela gravada sem colunas. A etapa não grava objetos serializados (pickle); o formato dos seus arquivos é identificado por `versao_formato` no `etapa.json`.

---

## 4. Manifesto da etapa (`etapa.json`)

Os campos comuns (`etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status`, `codigo_saida`, `etapa_anterior`, `arquivos`, `resumo`) e os estados estão no [data-model da Coleta](../001-coleta-dados/data-model.md). No Tratamento:
- `etapa` = `tratamento`; `versao_formato` = 1 (`pipeline.VERSAO_FORMATO`), conferido pela Conferência antes de rodar;
- `etapa_anterior` = `{"etapa": "coleta", "concluida_em": <concluida_em da Coleta>}`;
- `arquivos`: os 21 arquivos na ordem de gravação (`validacao_fisica.md`, `validacao_fisica.csv`, `evt_tratado.xlsx`, `evt_tratado.parquet`, `evt_tratado.csv`, os quatro CSV de indicadores, `indicadores.xlsx`, os dois da programação e, para disponibilidade, hidrologia e geração, a série, as ausências e a auditoria), cada um com `nome`, `bytes` e `sha256`; os `INALTERADO` também entram;
- o próprio `etapa.json` não tem `.bak`: é gravado em `etapa.json.tmp` e trocado.

`resumo` com código 0 (FR-033):

| Campo | Tipo | Conteúdo |
|---|---|---|
| `periodo.inicio`, `periodo.fim` | texto `AAAA-MM-DD HH:MM:SS` | primeiro e último instante da EVT: o período de referência |
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
| `gravacoes` | objeto resultado → inteiro | arquivos por resultado de gravação; só os resultados que ocorreram aparecem |

Outros casos:
- **Violação de R1**: `resumo` com `periodo` e `evt` (sem `sinalizados`), `arquivos` vazio, `status` `falha`, `codigo_saida` 1.
- **Exceção**: `resumo` = `{"erro": "<mensagem>"}`, `status` `falha`, `codigo_saida` 1.
- **Interrupção pelo usuário (Ctrl+C)**: `resumo` = `{"erro": "interrompida pelo usuário"}`, `status` `falha`, `codigo_saida` 1; a Conferência recusa rodar até um novo Tratamento concluído.
- **Código 5**: nenhum `etapa.json` é gravado; o anterior, se houver, fica como estava.

Na São Domingos (execução com os 21 arquivos `INALTERADO`; as 2.546 horas hidrológicas sinalizadas somam 2.550 por código, porque 4 têm `H1,H2`):

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

### 5.5 Regras de montagem

| Tabela | Regra |
|---|---|
| Séries horárias | instante na hora de início; entre ocorrências da mesma hora, fica a última na ordem de leitura da Coleta; valores comparados nas colunas de valor, com vazio igual a vazio; só as horas de início a fim, inclusive |
| Ausências | grade horária do período; mês do período sem nenhuma hora da usina é `MES_SEM_USINA` se algum arquivo obtido cobre aquele ano e mês pelo nome (o anual cobre os doze), senão `MES_SEM_ARQUIVO`; nos demais meses, intervalos contínuos `HORAS` |
| Indicadores por UG | chave (`mes` ou `ano`, `ug`); fica a última linha na ordem de leitura (arquivos em ordem de nome); aviso com a quantidade de linhas de chave repetida; meses do mês inicial ao final do período, anos do ano inicial ao final |
| Horas por estado | maior `num_versao` por mês, UG e estado; resíduo acima de 0,1 h só no log; potência juntada pelos indicadores mensais |
| Taxas | maior `num_versao` por mês e taxa; `num_versao` e `din_calculo` do mês são os maiores entre as duas taxas |
| Programação | patamar sem número descartado; hora = dia + ((n − 1) ÷ 2); dias ausentes = dias do primeiro dia com arquivo obtido até o dia do fim do período, menos os dias com arquivo obtido |

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
| `cod_usina` inválido, grandeza fora do dicionário, coluna de rastreabilidade ausente, valores ausentes, violações de R2 a R9, resíduo acima de 0,1 h, chave repetida nos indicadores, hora repetida com valor diferente, horas sinalizadas | aviso no log | 0 |
