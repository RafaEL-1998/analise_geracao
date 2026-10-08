# Data Model: Coleta de dados

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-08

Além dos arquivos da Coleta, este documento descreve as estruturas comuns às cinco etapas, citadas pelas demais specs: o perfil da usina (seções 3.1 e 5.1), o `etapa.json` (seção 4), os manifestos, as versões anteriores e os dicionários dos dados brutos (seção 2.1) e a cópia de segurança do projeto (seção 2.4).

## 1. Entradas

### 1.1 Perfil da usina

`usinas/<slug>/perfil.toml`, lido e validado por `src.comum.perfil.carregar_perfil` em `src/__main__.py`, antes de qualquer outra ação. A Coleta usa estes campos (os demais são validados aqui e usados pelas etapas seguintes; seção 5.1 e [contracts/perfil-usina.md](contracts/perfil-usina.md)):

| Campo | Uso na Coleta |
|---|---|
| `usina.slug` | pasta `data/usinas/<slug>/coleta/` |
| `usina.estado` | conferência na Programação diária, na Disponibilidade por usina, na Geração por usina e no cadastro |
| `identificacao.cod_usina` | identificador na EVT e nos Dados hidrológicos horários |
| `identificacao.nome_ons` | conferência ("contém") na EVT, na hidrologia e na programação; contagem de homônimos no cadastro |
| `identificacao.ceg` | identificador nos indicadores, nas taxas e no cadastro; conferência na disponibilidade e na geração |
| `identificacao.id_ons` | identificador na disponibilidade e na geração; conferência nos indicadores por UG e no cadastro |
| `identificacao.cod_programacao` | identificador na Programação diária |
| `identificacao.id_reservatorio` | conferência na hidrologia |

### 1.2 Portal de dados abertos do ONS

Catálogo CKAN `https://dados.ons.org.br/api/3/action/package_show?id=<id>` (`ONS_CKAN_PACKAGE_SHOW_URL`), lido por `catalogo.fetch_ckan_package_metadata`. De cada recurso, `catalogo.parse_ckan_resources` guarda `url`, `name`, `id`, `format`, `size` e a publicação (`last_modified`, ou `metadata_modified`, ou `created`). Ids e pastas ficam em `src/comum/regras.py` (`CONJUNTO_*`, `CONJUNTOS_INDICADORES_ONS`, `PASTA_*_RAW` e `CONJUNTOS_PIPELINE`).

| Conjunto do ONS | Id no catálogo | Pasta em `data/raw/` | Recursos aceitos | Seleção | Sincronização |
|---|---|---|---|---|---|
| Energia Vertida Turbinável (EVT) | `energia-vertida-turbinavel` | a própria `data/raw/` | CSV | todos | `evt.sincronizar_evt` |
| Indicadores por UG, base mensal | `ind_disponibilidade_fgeracao_uge_mensal` | `indicadores_ons/<id>/` | CSV | ano do nome (`_AAAA.csv`) entre o ano do início e o do fim do período; arquivo sem ano, sempre | `indicadores.sincronizar_indicadores` |
| Indicadores por UG, base anual | `ind_disponibilidade_fgeracao_uge_anual` | idem | CSV | idem | idem |
| Parâmetros das taxas TEIFa e TEIP | `taxa_teif_teip_parametro` | idem | CSV | idem | idem |
| Taxas TEIFa e TEIP | `taxa_teif_teip` | idem | CSV | idem | idem |
| Programação diária | `programacao_diaria` | `programacao_diaria/` | Parquet | dia do nome (`_AAAA_MM_DD.`) entre o dia do início e o do fim | `programacao.sincronizar_programacao` |
| Disponibilidade por usina | `disponibilidade_usina` | `disponibilidade_usina/` | Parquet e CSV | ano ou mês do nome (`_AAAA[_MM].<ext>`) sobreposto ao período; por período, o Parquet, senão o CSV | `conjuntos.sincronizar_conjunto` |
| Dados hidrológicos horários | `dados_hidrologicos_ho` | `dados_hidrologicos_ho/` | idem | idem | idem |
| Geração por usina | `geracao-usina-2` | `geracao_usina_2/` | idem | idem | idem |
| Modalidade das usinas | `modalidade-usina` | `modalidade_usina/` | o primeiro recurso de formato CSV cujo nome, sem acento, não contém "DICIONARIO" | arquivo único | `cadastro.sincronizar_cadastro` |
| Dicionários dos dez conjuntos | os mesmos | `<pasta do conjunto>/_dicionarios/` | PDF e JSON cujo nome, sem acento, contém "DICIONARIO" | todos | `dicionarios.sincronizar_dicionarios` |

Um recurso é aceito pelo formato declarado ou pela extensão da URL (no cadastro e nos dicionários, só pelo formato declarado). O período é o da EVT extraída: do primeiro ao último `din_instante`.

### 1.3 Arquivos locais lidos

A leitura não desce às subpastas, de modo que `_versoes_anteriores/` e `_dicionarios/` nunca são lidos como dados.

| Conjunto | Arquivos lidos | Ordem de leitura | Função |
|---|---|---|---|
| EVT | `data/raw/*.csv` | nome (anuais antes dos mensais) | `evt.filter_all_raw_files` |
| Indicadores e taxas | `indicadores_ons/<id>/*.csv` dos anos do período e sem ano | `ind_..._mensal`, `ind_..._anual`, `taxa_teif_teip_parametro`, `taxa_teif_teip`; dentro de cada um, nome | `indicadores.extrair_indicadores` |
| Programação diária | `programacao_diaria/*.parquet` dos dias do período | nome | `programacao.extrair_programacao` |
| Disponibilidade, hidrologia e geração | um arquivo por ano ou mês sobreposto ao período: o `.parquet`, senão o `.csv` | data de publicação no manifesto, depois nome | `conjuntos.extrair_conjunto` |
| Modalidade das usinas | o CSV sincronizado nesta execução ou, sem ele, o primeiro `*.csv` da pasta | — | `cadastro.extrair_cadastro` |

Os manifestos das pastas também são lidos: dão a data de publicação de cada arquivo na auditoria e, no cadastro, a data da consulta.

### 1.4 Colunas lidas dos arquivos do ONS

| Conjunto | Colunas de identificação | Colunas extraídas |
|---|---|---|
| EVT | `cod_usina`, `nom_reservatorio` | as 18 colunas publicadas |
| Indicadores por UG | `ceg`, `id_usina` | todas as colunas publicadas |
| Taxas e parâmetros | `cod_ceg` | todas as colunas publicadas |
| Programação diária | `cod_exibicaousina`, `nom_usina`, `id_estado`; `din_programacaodia` (conferência da data) | `num_patamar`, `val_geracaoprogramada` |
| Disponibilidade por usina | `id_ons`, `ceg`, `id_estado` | `din_instante`, `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` |
| Dados hidrológicos horários | `cod_usina`, `nom_reservatorio`, `id_reservatorio` | `din_instante`, `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas`, `val_nivelmontante`, `val_niveljusante`, `val_volumeutil` |
| Geração por usina | `id_ons`, `ceg`, `id_estado` | `din_instante`, `val_geracao` |
| Modalidade das usinas | `ceg`, `id_ons`, `id_estado`, `nom_usina` (obrigatórias) | as colunas da ficha (seção 2.2) |

## 2. Saídas

### 2.1 Dados brutos compartilhados (`data/raw/`)

Gravados só pela Coleta e só quando ela consulta o portal; servem a todas as usinas.

```text
data/raw/
├── ENERGIA_VERTIDA_TURBINAVEL_<AAAA>[_<MM>].csv   # EVT, na própria raiz
├── _manifesto_ons.json
├── _versoes_anteriores/                           # criada na primeira versão preservada
├── _dicionarios/                                  # dicionários da EVT, com manifesto e _versoes_anteriores/
├── indicadores_ons/
│   └── <id do conjunto>/                          # quatro pastas
├── programacao_diaria/
├── disponibilidade_usina/
├── dados_hidrologicos_ho/
├── geracao_usina_2/
└── modalidade_usina/
```

Cada pasta de conjunto tem os arquivos de dados, `_manifesto_ons.json`, `_versoes_anteriores/` (quando houver) e `_dicionarios/`.

**Arquivos de dados**: o nome é o último trecho da URL, sem parâmetros; se ele não termina na extensão do formato, `<nome do recurso>.<ext>` (`catalogo._local_filename`). O download vai para `<nome>.part`, que substitui o arquivo só quando completo. Nenhum arquivo é editado: ele só é substituído inteiro por uma versão publicada.

#### Manifesto de versões (`_manifesto_ons.json`)

JSON em UTF-8, com indentação 2 e chaves em ordem alfabética, gravado por `catalogo.save_manifest` (temporário `.json.part` e troca atômica). Um objeto por arquivo, com o nome do arquivo como chave. Um manifesto ilegível é tratado como vazio e recriado, com aviso no log.

| Campo | Tipo | Conteúdo |
|---|---|---|
| `url` | texto | URL do recurso |
| `ultima_modificacao` | texto ISO | data de publicação no catálogo; vazio se o catálogo não a informa |
| `tamanho_publicado_bytes` | inteiro | `size` do catálogo; 0 se ausente |
| `tamanho_bytes` | inteiro | tamanho local (baixado ou existente) |
| `registrado_em_utc` | texto `AAAA-MM-DD HH:MM:SS` | data e hora do registro; não muda quando a cópia já registrada é reaproveitada |
| `origem_registro` | texto | `DOWNLOAD` ou `ARQUIVO_EXISTENTE` (cópia aceita sem registro anterior) |
| `versoes_anteriores` | lista | só quando há versões preservadas (abaixo) |
| `versoes_excluidas` | lista | só quando houve poda (abaixo) |
| `recursos_duplicados_catalogo` | inteiro | só nos conjuntos horários: recursos repetidos no catálogo para o mesmo período, descartados |

- Item de `versoes_anteriores`: `arquivo_preservado` (`_versoes_anteriores/<nome>`), `ultima_modificacao` (publicação da versão preservada), `tamanho_bytes`, `sha256` e `arquivado_em_utc`. As mais recentes ficam no fim da lista.
- Item de `versoes_excluidas`: `arquivo_preservado`, `ultima_modificacao`, `sha256` e `excluido_em_utc`.
- **Data de obtenção de um conjunto**: o maior `registrado_em_utc` do manifesto da pasta (`conjuntos.data_obtencao`); no resumo da Coleta, a entrada `indicadores` junta as quatro pastas.

Exemplo real (`data/raw/modalidade_usina/_manifesto_ons.json`):

```json
{
  "MODALIDADE_USINA.csv": {
    "origem_registro": "DOWNLOAD",
    "registrado_em_utc": "2026-10-05 15:07:29",
    "tamanho_bytes": 833845,
    "tamanho_publicado_bytes": 833845,
    "ultima_modificacao": "2026-10-05T15:05:02.911662",
    "url": "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/modalidade_usina/MODALIDADE_USINA.csv",
    "versoes_anteriores": [
      {
        "arquivado_em_utc": "2026-10-05 15:07:29",
        "arquivo_preservado": "_versoes_anteriores/MODALIDADE_USINA__pub_20261004T220450.csv",
        "sha256": "55b11e10043c2d18407bd5b9c5c7ac825990bc746e8c504b81944ef881f991eb",
        "tamanho_bytes": 833309,
        "ultima_modificacao": "2026-10-04T22:04:50.673859"
      }
    ]
  }
}
```

#### Versões anteriores (`_versoes_anteriores/`)

- **Quando**: o download da nova versão terminou e o SHA-256 da cópia local é diferente do baixado. Conteúdo idêntico não gera versão; falha no download não move nada.
- **Nome**: `<nome sem extensão>__pub_<AAAAMMDDTHHMMSS><extensão>`, pela `ultima_modificacao` registrada no manifesto; sem ela, `<nome sem extensão>__arq_<AAAAMMDDTHHMMSS><extensão>`, pela data e hora (UTC) do arquivamento. Se o nome existir, acrescenta `_2`, `_3` e assim por diante antes da extensão.
- **Limite**: `MAXIMO_VERSOES_ANTERIORES` (2) por arquivo. Ao preservar a terceira, as mais antigas são excluídas e vão para `versoes_excluidas`; um registro sem arquivo no disco é registrado como excluído, com aviso. A exclusão usa só o nome do arquivo, dentro de `_versoes_anteriores/`.
- Vale para os arquivos de dados e para os dicionários.

#### Dicionários de dados (`_dicionarios/`)

- **Arquivos**: o PDF e o JSON de cada conjunto, com o nome da URL (na EVT, `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.{pdf,json}`).
- **Manifesto** (`_dicionarios/_manifesto_ons.json`): as entradas dos arquivos obtidos têm os campos da tabela anterior (`origem_registro` `DOWNLOAD`; o catálogo não informa `size`, e `ultima_modificacao` vem de `metadata_modified` ou `created`), mais:

| Campo | Conteúdo |
|---|---|
| `conjunto` | id do conjunto no catálogo |
| `formato` | `PDF` ou `JSON` |
| `resultado_ultima_obtencao` | `NOVO`, `INALTERADO`, `ALTERADO` ou `FALHA` |
| `obtido_em_utc` | data e hora (UTC) da última consulta |
| `sha256` | SHA-256 da cópia local |

- **Entrada `_consulta`** (uma por manifesto): `obtido_em_utc`, `formatos_publicados` (lista dos formatos encontrados no catálogo) e `falha` (texto; vazio sem falha). Com o catálogo inacessível, `falha` traz o erro e todas as entradas existentes passam a `FALHA`, com a mesma data.

### 2.2 Arquivos da usina (`data/usinas/<slug>/coleta/`)

Regras comuns:
- gravados por `src/comum/persistencia.py`: `.bak` da versão anterior (`<nome>.bak`), conteúdo idêntico não regravado, conferência no disco e restauração em falha ou interrupção (Ctrl+C);
- CSV com `;`, UTF-8 sem BOM e fim de linha do sistema (CRLF no Windows); data e hora `AAAA-MM-DD HH:MM:SS`; booleanos `True` e `False`; vazio = ausente;
- Parquet gravado pelo pyarrow, sem índice;
- cada execução que chega a um arquivo o grava de novo, mas o conteúdo igual ao anterior não é regravado (`INALTERADO`); a `auditoria_evt.csv` muda sempre, porque traz a hora da leitura.

#### `evt_extraido.csv`

Uma linha por (`cod_usina`, `din_instante`), em ordem cronológica, sem horas criadas nem preenchidas. Gravado por `evt.save_consolidated_records` (`gravar_linhas_csv`, módulo `csv`).

| Coluna | Tipo | Descrição |
|---|---|---|
| `id_subsistema`, `nom_subsistema` | texto | subsistema |
| `nom_bacia`, `nom_rio` | texto | bacia e rio |
| `nom_agente` | texto | agente; muda ao longo da série e não entra na identificação |
| `nom_reservatorio` | texto | nome do reservatório (conferência) |
| `cod_usina` | texto | código da usina nos modelos de otimização (identificador) |
| `din_instante` | texto `AAAA-MM-DD HH:MM:SS` | instante como publicado (hora de início) |
| `val_geracao`, `val_disponibilidade`, `val_folgadegeracao`, `val_energiavertida`, `val_energiavertidaturbinavel` | real | MWmed |
| `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaovertidaturbinavel` | real | m³/s |
| `val_produtividade` | real | MW/(m³/s) |
| `arquivo_origem` | texto | arquivo bruto de onde veio o registro mantido |
| `tipo_match` | texto | critério de identificação: sempre `CODIGO_E_NOME` |

Os valores são gravados na representação do Python, com ponto decimal e sem arredondamento; o valor ausente ou não numérico na fonte fica vazio (o não numérico conta em `valores_invalidos` da auditoria, com aviso no log).

#### `auditoria_evt.csv`

Uma linha por CSV de `data/raw/`, inclusive os sem linhas da usina, mais uma por arquivo publicado não obtido nesta execução. Gravada por `evt.save_audit_report`; colunas em `evt.AUDIT_CSV_COLUMNS`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `nome_arquivo` | texto | arquivo |
| `periodo_referencia` | texto | nome do arquivo sem extensão |
| `total_linhas_arquivo` | inteiro | linhas não vazias depois do cabeçalho, inclusive as irregulares |
| `registros_extraidos` | inteiro | linhas com código e nome do reservatório (antes da consolidação) |
| `registros_codigo_sem_nome` | inteiro | só o identificador confere |
| `registros_nome_sem_codigo` | inteiro | só a conferência confere |
| `codificacao` | texto | `utf-8` ou `latin-1` |
| `status_processamento` | texto | `PROCESSADO`, `SEM_REGISTROS` ou `FALHA` |
| `data_hora_processamento` | texto `AAAA-MM-DD HH:MM:SS` | data e hora (UTC) do fim da leitura |
| `registros_formato_irregular` | inteiro | linhas com número de campos diferente do cabeçalho, não extraídas |
| `valores_invalidos` | inteiro | valores preenchidos e não numéricos nas 10 grandezas das linhas extraídas, que ficam vazios (`null`, `none` e `nan` valem como vazio) |
| `formato` | texto | `CSV` |
| `data_publicacao` | texto ISO | `ultima_modificacao` do manifesto |
| `obtido` | booleano | `False`: arquivo publicado que não pôde ser obtido nesta execução |
| `mensagem` | texto | motivo da falha |

#### `indicadores_extraido.parquet`

Uma linha por linha da usina num arquivo dos quatro conjuntos. Todas as colunas são texto, como publicadas e sem espaços nas pontas; a coluna de um conjunto fica nula nas linhas dos outros. `indicadores.separar_conjuntos` separa a tabela de volta por conjunto, sem as colunas nulas.

| Coluna | Conteúdo |
|---|---|
| `conjunto` | id do conjunto de origem (primeira coluna) |
| colunas publicadas | ver abaixo |
| `arquivo_origem` | arquivo bruto |

| Conjunto | Colunas publicadas nos arquivos atuais |
|---|---|
| `ind_disponibilidade_fgeracao_uge_mensal` | `id_subsistema`, `nom_subsistema`, `id_estado`, `nom_estado`, `nom_modalidadeoperacao`, `nom_agenteproprietario`, `id_tipousina`, `id_usina`, `nom_usina`, `ceg`, `cod_equipamento`, `num_unidadegeradora`, `nom_unidadegeradora`, `val_potencia`, `dat_mesreferencia`, `val_dispf`, `val_indisppf`, `val_indispff`, `val_dmdff`, `val_fdff`, `val_tdff` |
| `ind_disponibilidade_fgeracao_uge_anual` | as do mensal, com `estad_id` no lugar de `id_estado` e `din_ano` no lugar de `dat_mesreferencia` |
| `taxa_teif_teip_parametro` | `id_tipousina`, `nom_usina`, `nom_unidadegeradora`, `cod_ceg`, `dat_periodo`, `nom_tpinsumo`, `val_parametro`, `num_versao`, `din_parametro` |
| `taxa_teif_teip` | `nom_usina`, `cod_ceg`, `num_versao`, `tip_usina`, `din_mes`, `nom_taxa`, `val_taxa`, `din_calculo` |

#### `auditoria_indicadores.csv`

Uma linha por arquivo lido ou não obtido dos quatro conjuntos (`indicadores.COLUNAS_AUDITORIA_INDICADORES`).

| Coluna | Tipo | Descrição |
|---|---|---|
| `conjunto` | texto | id do conjunto |
| `arquivo` | texto | arquivo |
| `formato` | texto | `CSV` |
| `periodo` | texto | ano do nome (`AAAA`); vazio no arquivo único |
| `data_publicacao` | texto ISO | do manifesto |
| `obtido` | booleano | `False`: não obtido nesta execução |
| `linhas_lidas` | inteiro | linhas de dados, inclusive as irregulares |
| `linhas_formato_irregular` | inteiro | linhas com número de campos diferente do cabeçalho |
| `linhas_usina` | inteiro | linhas extraídas |
| `linhas_so_identificador` | inteiro | CEG confere, id ONS não; vazio nas taxas e nos parâmetros |
| `linhas_so_conferencia` | inteiro | id ONS confere, CEG não; vazio nas taxas e nos parâmetros |
| `status` | texto | `PROCESSADO`, `SEM_REGISTROS` ou `FALHA` |
| `mensagem` | texto | motivo da falha |

#### `programacao_extraido.parquet`

Uma linha por dia e patamar da usina; num patamar repetido no mesmo arquivo, fica a última ocorrência.

| Coluna | Tipo | Descrição |
|---|---|---|
| `dia` | data e hora (meia-noite) | dia do nome do arquivo |
| `num_patamar` | inteiro | patamar de 30 minutos, de 1 a 48 |
| `geracao_programada_mw` | real | `val_geracaoprogramada` (MWmed), vírgula decimal aceita |
| `arquivo_origem` | texto | arquivo bruto |

#### `auditoria_programacao.csv`

Uma linha por arquivo diário do período, lido ou não obtido (`programacao.COLUNAS_AUDITORIA_PROGRAMACAO`). Os dias sem linha são dias sem arquivo, listados pelo Tratamento.

| Coluna | Tipo | Descrição |
|---|---|---|
| `arquivo` | texto | arquivo |
| `dia` | texto `AAAA-MM-DD 00:00:00` | dia do nome do arquivo |
| `formato` | texto | `PARQUET` |
| `data_publicacao` | texto ISO | do manifesto |
| `obtido` | booleano | `False`: não obtido nesta execução |
| `linhas_lidas` | inteiro | linhas do arquivo (todas as usinas) |
| `linhas_usina` | inteiro | linhas com código e conferência (antes de juntar os patamares repetidos) |
| `linhas_codigo_sem_conferencia` | inteiro | só o código de exibição confere |
| `linhas_so_conferencia` | inteiro | nome e estado conferem, código não |
| `valores_invalidos` | inteiro | `num_patamar` ou `val_geracaoprogramada` preenchidos e não numéricos |
| `patamares` | inteiro | patamares distintos da usina |
| `data_interna_confere` | booleano | `din_programacaodia` igual ao dia do nome; `True` sem linhas da usina; `False` na falha |
| `status` | texto | `PROCESSADO`, `SEM_REGISTROS`, `INCOMPLETO` (patamares diferentes de 48) ou `FALHA` |
| `mensagem` | texto | motivo da falha |

#### `disponibilidade_extraido.parquet`, `hidrologia_extraido.parquet` e `geracao_extraido.parquet`

Uma linha por linha da usina com instante válido, na ordem de leitura dos arquivos; as repetições entre arquivos ficam todas, para o Tratamento.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | instante como publicado: hora de início na disponibilidade e na geração; hora de fim na hidrologia (`DescricaoConjunto.convencao_hora`, aplicada pelo Tratamento) |
| colunas de valor | real | ver abaixo; ausente quando vazio ou não numérico na fonte |
| `_nao_numerico` | booleano | a linha tinha algum valor não numérico na fonte (as linhas com instante inválido ficam fora do arquivo) |
| `arquivo_origem` | texto | arquivo bruto |

| Arquivo | Colunas de valor |
|---|---|
| `disponibilidade_extraido.parquet` | `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` (MW) |
| `hidrologia_extraido.parquet` | `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas` (m³/s); `val_nivelmontante`, `val_niveljusante` (m); `val_volumeutil` (%) |
| `geracao_extraido.parquet` | `val_geracao` (MWmed) |

#### `auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv` e `auditoria_geracao.csv`

Uma linha por arquivo do período, lido ou não obtido, na ordem de leitura (`conjuntos.COLUNAS_AUDITORIA_COLETA`). O Tratamento completa essa auditoria com as horas da usina e as duplicatas entre arquivos.

| Coluna | Tipo | Descrição |
|---|---|---|
| `arquivo` | texto | arquivo |
| `formato` | texto | `PARQUET` ou `CSV` |
| `periodo` | texto | `AAAA` ou `AAAA-MM`, pelo nome |
| `data_publicacao` | texto ISO | do manifesto |
| `obtido` | booleano | `False`: não obtido nesta execução |
| `linhas_lidas` | inteiro | Parquet: linhas do arquivo (metadados); CSV: linhas lidas mais as irregulares |
| `linhas_formato_irregular` | inteiro | só CSV |
| `linhas_usina` | inteiro | identificador e conferência conferem |
| `linhas_so_identificador` | inteiro | só o identificador confere |
| `linhas_so_conferencia` | inteiro | só a conferência confere |
| `valores_invalidos` | inteiro | instantes não interpretáveis mais valores não numéricos, nas linhas da usina |
| `recursos_duplicados_catalogo` | inteiro | recursos repetidos no catálogo para o arquivo (do manifesto) |
| `status` | texto | `PROCESSADO`, `SEM_REGISTROS` ou `FALHA` |
| `mensagem` | texto | motivo da falha |

#### `cadastro_ficha.csv`

Uma linha (a primeira com o CEG do perfil) ou nenhuma, se a usina não está no cadastro (`cadastro.COLUNAS_FICHA`).

| Coluna | Tipo | Descrição |
|---|---|---|
| `nom_usina` | texto | nome no cadastro |
| `ceg`, `id_ons` | texto | identificação |
| `nom_modalidadeoperacao` | texto | modalidade de operação |
| `sgl_centrooperacao` | texto | centro de operação |
| `nom_pontoconexao` | texto | ponto de conexão |
| `val_potenciaautorizada` | real | potência autorizada (MW) |
| `id_estado` | texto | estado |
| `sts_aneel` | texto | situação na ANEEL (`A`, `I`, `P`, `C` ou `O`) |
| `data_consulta_utc` | texto `AAAA-MM-DD HH:MM:SS` | `registrado_em_utc` do arquivo no manifesto |
| `arquivo_origem` | texto | arquivo bruto |
| `homonimos` | inteiro | linhas com `nome_ons` no nome da usina e outro CEG |
| `linhas_so_identificador` | inteiro | linhas com o CEG e id ONS ou estado diferente do perfil |
| `linhas_so_conferencia` | inteiro | linhas com id ONS e estado do perfil e outro CEG |
| `linhas_ceg` | inteiro | linhas com o CEG; mais de uma indica CEG repetido |

#### `auditoria_cadastro.csv`

Uma linha pela leitura do arquivo local (sem arquivo local, nenhuma), mais uma por falha de download (`cadastro.COLUNAS_AUDITORIA_CADASTRO`): `arquivo`, `formato` (`CSV`), `data_publicacao`, `obtido`, `linhas_lidas` (linhas mais as irregulares), `linhas_formato_irregular`, `linhas_usina` (linhas com o CEG), `linhas_so_identificador`, `linhas_so_conferencia` (como na ficha), `status` (`PROCESSADO`, `SEM_REGISTROS` ou `FALHA`) e `mensagem`.

#### `dicionarios.csv`

Vinte linhas: os dez conjuntos de `CONJUNTOS_PIPELINE`, nessa ordem, em PDF e em JSON. Montado só dos manifestos de `_dicionarios/` (`dicionarios.montar_registro`), inclusive com `--sem-portal`.

| Coluna | Tipo | Descrição |
|---|---|---|
| `conjunto` | texto | id do conjunto |
| `pasta` | texto | pasta dos dicionários, relativa a `data/raw/` (ex.: `_dicionarios`, `indicadores_ons/<id>/_dicionarios`) |
| `formato` | texto | `PDF` ou `JSON` |
| `arquivo` | texto | nome do arquivo; vazio sem registro |
| `url` | texto | URL do recurso |
| `resultado_ultima_obtencao` | texto | `NOVO`, `INALTERADO`, `ALTERADO`, `FALHA`, `NAO_PUBLICADO` ou `NAO_OBTIDO` |
| `obtido_em_utc` | texto | data e hora da última consulta |
| `sha256` | texto | SHA-256 da cópia local |
| `tamanho_bytes` | inteiro | tamanho da cópia local |
| `versoes_anteriores` | inteiro | versões preservadas |
| `ultima_versao_anterior` | texto | `arquivo_preservado` da mais recente |

### 2.3 Quem lê cada saída

| Saída | Lida por |
|---|---|
| `evt_extraido.csv` | Tratamento (`tratar_evt`) |
| `indicadores_extraido.parquet` | Tratamento (`montar_indicadores`, com `separar_conjuntos`) |
| `programacao_extraido.parquet` e `auditoria_programacao.csv` | Tratamento (`montar_programacao`); a auditoria também nas Análises |
| `<conjunto>_extraido.parquet` e `auditoria_<conjunto>.csv` (disponibilidade, hidrologia, geração) | Tratamento (`tratar_disponibilidade`, `tratar_hidrologia`, `tratar_geracao`) |
| `cadastro_ficha.csv` | Conferência (cadastro) e Análises |
| `auditoria_evt.csv`, `auditoria_cadastro.csv` e `dicionarios.csv` | Análises (cobertura e registros mostrados no relatório) |
| `auditoria_indicadores.csv` | nenhuma etapa; registro da varredura |
| `data/raw/_manifesto_ons.json` | Análises (cobertura da EVT) |
| manifestos das pastas dos conjuntos | Análises e Relatório (datas de obtenção, `conjuntos.data_obtencao`) |
| `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json` | Tratamento (validação física) |

### 2.4 Cópia de segurança do projeto (`_backup_<AAAA-MM-DD>_<motivo>/`)

Criada na raiz do projeto por `python -m src copia-seguranca --motivo <texto>` (`src/comum/copia_seguranca.py`).

| Item | Conteúdo |
|---|---|
| Pastas copiadas | `src/`, `tests/`, `specs/`, `reports/` e `.specify/`, sem `__pycache__`, `*.pyc` e `.pytest_cache` |
| Arquivos copiados | `usinas/<slug>/perfil.toml` de cada usina, `README.md` e `requirements.txt` |
| `copia.json` | lista JSON (indentação 1) com `{"arquivo": <caminho relativo com "/">, "bytes": <tamanho>, "sha256": <SHA-256>}` de cada arquivo copiado, conferido contra a origem |
| `conftest.py` | `collect_ignore_glob = ["*"]`, que impede o pytest de varrer a cópia |
| `LEIA-ME.txt` | data (DD/MM/AAAA), motivo, o que foi copiado e o papel de `copia.json` e `conftest.py` |
| Fora da cópia | todo o resto, inclusive `data/` (brutos e etapas), `usinas/<slug>/documentos/`, `referencias/` e `venv/` |

Conferência: a quantidade de arquivos (sem os três de controle) e o SHA-256 de cada um, contra o registro. Poda: das pastas `_backup_<AAAA-MM-DD>_*`, ordenadas pela data do nome e, no empate, pela data de criação, ficam as duas mais recentes (`MAXIMO_COPIAS`).

## 3. Objetos em memória e entre etapas

A Coleta não grava objeto serializado (pickle); o formato dos seus arquivos é identificado por `versao_formato` = 1 no `etapa.json` (`pipeline.VERSAO_FORMATO`).

### 3.1 Perfil da usina (`src/comum/perfil.py`)

Dataclasses imutáveis, montadas por `carregar_perfil`:

| Classe | Campos |
|---|---|
| `Perfil` | `usina: Usina`, `identificacao: Identificacao`, `parametros: Parametros`, `analises: Analises`, `textos: Textos`, `arquivo: Path` |
| `Usina` | `slug`, `nome`, `nome_curto`, `estado` (texto); `inicio_operacao_comercial` (int) |
| `Identificacao` | `cod_usina` (int); `nome_ons`, `ceg`, `id_ons`, `cod_programacao`, `id_reservatorio` (texto) |
| `Parametros` | `potencia_instalada_mw`, `potencia_unitaria_mw`, `engolimento_nominal_ug_m3s`, `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` (float); `unidades_geradoras` (int); `tipo_turbina` (texto); `fontes: FontesParametros` |
| `FontesParametros` | `geral`, `garantia_fisica` (texto); `inicio_operacao_comercial`, `ip_teif` (texto ou `None`) |
| `Analises` | `vertimento_minimo_m3s` (float); `faixas_geracao_mw` (tupla de float); `descricao_vertimento_minimo` (texto ou `None`); `fontes: FontesAnalises` |
| `FontesAnalises` | `vertimento_minimo` (texto ou `None`) |
| `Textos` | `ressalva_volume_util` (texto ou `None`) |

Valores derivados (propriedades de `Perfil`; o perfil não os traz):

| Propriedade | Cálculo |
|---|---|
| `engolimento_maximo_m3s` | `unidades_geradoras` × `engolimento_nominal_ug_m3s` |
| `potencia_autorizada_esperada_mw` | `potencia_instalada_mw` |
| `disponibilidade_referencia` | (1 − `ip_referencia`) × (1 − `teif_referencia`) |
| `produtividade_nominal_mw_m3s` | 1000 × 9,81 × (`queda_bruta_m` − `perda_hidraulica_m`) × `rendimento_turbina_gerador` / 10⁶ |
| `plena_carga_mw` | `FRACAO_PLENA_CARGA` (0,90) × `potencia_instalada_mw` |
| `limite_potencia_mw` | `potencia_instalada_mw` × (1 + `TOLERANCIA_LIMITES_FISICOS`), com tolerância de 0,05 |
| `limite_vazao_turbinavel_m3s` | `engolimento_maximo_m3s` × (1 + 0,05) |
| `limites_fisicos_superiores` | dicionário da validação física do Tratamento: `val_geracao`, `val_disponibilidade`, `val_folgadegeracao` e `val_energiavertidaturbinavel` → `limite_potencia_mw`; `val_vazaoturbinada` e `val_vazaovertidaturbinavel` → `limite_vazao_turbinavel_m3s` |

- `PerfilInvalido(Exception)`: `slug`, `arquivo`, `problemas` (lista de textos); a mensagem é o cabeçalho seguido de uma linha `- <problema>` por problema.
- **Perfil ativo**: `definir_perfil_ativo(perfil)` e `perfil_ativo()`. `pipeline.executar_etapa` define o perfil antes da função da etapa e o limpa depois, mesmo com erro; sem etapa em execução, `perfil_ativo()` levanta `RuntimeError`.

### 3.2 Resultado de uma etapa (`src/pipeline.py`)

`ResultadoEtapa`: `codigo` (int, padrão 0), `arquivos` (lista de `Path` gravados) e `resumo` (dicionário). É o que a função de cada etapa devolve a `executar_etapa`, que monta o `etapa.json`.

### 3.3 Objetos da Coleta

| Objeto | Onde | Campos e papel |
|---|---|---|
| `RecursoONS` | `src/comum/modelos.py` | `id_recurso`, `nome_recurso`, `url_download`, `formato`, `tamanho_bytes` (0 se ausente), `ultima_modificacao`, `arquivo_local`, `status_sincronizacao` (`PENDING`, `DOWNLOADED`, `UPDATED`, `CACHED`, `FAILED`; só para o log) |
| `RegistroEnergiaVertida` | idem | as 8 colunas de texto da EVT, as 10 grandezas (float ou `None`), `arquivo_origem` e `tipo_match` |
| `AuditoriaArquivo` | idem | uma linha de `auditoria_evt.csv`; `data_hora_processamento` é preenchida na criação |
| `Regra` | `src/coleta/conjuntos.py` | `coluna`, `valor`, `modo` (`igual` ou `contem`) |
| `DescricaoConjunto` | idem | `pacote` (id no catálogo), `pasta`, `identificador` (`Regra`), `conferencias` (tupla de `Regra`), `colunas_valor`, `convencao_hora` (`inicio` ou `fim`, aplicada pelo Tratamento), `formatos_preferidos` (`PARQUET`, `CSV`), `filtro_parquet`; `descricoes(perfil)` monta as três, com os valores do perfil |
| Falha de download | `sincronizar_*` | dicionário no formato da linha de auditoria: `arquivo` e `mensagem`, mais `status` (`FALHA`), `formato` e, conforme o conjunto, `periodo`, `dia` ou `conjunto`; na auditoria, recebe `obtido = False` |
| `_Coleta` | `src/coleta/etapa.py` | estado de uma execução: perfil, opções, pasta, início (UTC), arquivos gravados, resumo e período da EVT |

## 4. Manifesto da etapa (`etapa.json`)

### 4.1 Campos comuns às cinco etapas

Gravado por `pipeline.executar_etapa` em `data/usinas/<slug>/<etapa>/etapa.json` (no relatório, `reports/<slug>/etapa.json`): JSON em UTF-8, indentação 1, troca atômica pelo temporário `etapa.json.tmp`, sem `.bak`.

| Campo | Tipo | Conteúdo |
|---|---|---|
| `etapa` | texto | `coleta`, `tratamento`, `conferencia`, `analises` ou `relatorio` |
| `usina` | texto | slug |
| `versao_formato` | inteiro | `VERSAO_FORMATO[etapa]`, hoje 1 em todas; muda quando os arquivos da etapa mudam de formato |
| `iniciada_em`, `concluida_em` | texto `AAAA-MM-DDTHH:MM:SSZ` | UTC |
| `status` | texto | `concluida`, `falha` ou `desatualizada` |
| `codigo_saida` | inteiro | código da execução |
| `etapa_anterior` | objeto ou `null` | `{"etapa", "concluida_em"}` da etapa usada como entrada; `null` na Coleta |
| `arquivos` | lista | `{"nome", "bytes", "sha256"}` de cada arquivo devolvido pela etapa e existente no disco, na ordem de gravação; `nome` relativo à pasta da etapa, com `/` |
| `resumo` | objeto | definido na spec de cada etapa; `{"erro": <mensagem>}` quando a etapa levantou exceção |

### 4.2 Situação e transições

| Fim da execução | `etapa.json` da etapa | Etapas seguintes |
|---|---|---|
| código 0 ou 3 | `concluida`, com o código | as que já existem e não estão `desatualizada` passam a `desatualizada` (só o `status` muda) |
| código 1 ou 2, inclusive exceção | `falha`, com o código | não mudam; a seguinte recusa rodar (código 5) |
| interrupção pelo usuário (Ctrl+C) | `falha`, com o código 1 e `resumo` `{"erro": "interrompida pelo usuário"}`; o arquivo de dados que estava sendo gravado volta à versão anterior | não mudam; a seguinte recusa rodar (código 5); o `completo` para |
| código 4, 5 ou opção inválida | não é gravado | não mudam |

**Pré-requisito** (`etapa_anterior_concluida`): a partir do Tratamento, a etapa só roda se o `etapa.json` da anterior existe, é legível, tem `status` `concluida` (com qualquer `codigo_saida`) e o `versao_formato` atual. Senão, sai com 5 antes de gravar qualquer arquivo.

### 4.3 Resumo da Coleta

```json
{
  "sem_portal": false,
  "forcar_download": false,
  "conjuntos": { "<chave>": { "<15 campos abaixo>": "..." } },
  "periodo": { "inicio": "AAAA-MM-DD HH:MM:SS", "fim": "AAAA-MM-DD HH:MM:SS" },
  "dicionarios": { "<resultado>": 0 }
}
```

- `sem_portal`: a opção da execução; `forcar_download`: a opção efetiva (`false` com `--sem-portal`).
- `conjuntos`: uma entrada por conjunto tratado até o fim ou até a parada, com as chaves `energia-vertida-turbinavel`, `indicadores` (os quatro conjuntos juntos), `programacao_diaria`, `disponibilidade_usina`, `dados_hidrologicos_ho`, `geracao-usina-2` e `modalidade-usina`. Montada por `etapa.resumo_conjunto` a partir da auditoria e dos manifestos das pastas do conjunto.
- `periodo`: primeiro e último `din_instante` da EVT consolidada; ausente se a EVT parou a coleta.
- `dicionarios`: quantidade de linhas de `dicionarios.csv` por `resultado_ultima_obtencao`; presente nas execuções com código 0 ou 2 (com código 1, o resumo é só `{"erro": …}`).

| Campo de cada conjunto | Significado |
|---|---|
| `arquivos_no_escopo` | arquivos distintos na auditoria (lidos ou não obtidos) |
| `baixados` | arquivos obtidos registrados no manifesto por `DOWNLOAD` durante esta execução; 0 com `--sem-portal` |
| `reaproveitados` | arquivos obtidos menos os baixados; 0 com `--sem-portal` |
| `nao_obtidos` | arquivos com `obtido = False` |
| `lidos` | linhas da auditoria com o arquivo obtido e sem `FALHA` |
| `sem_linhas_da_usina` | linhas com `SEM_REGISTROS` |
| `com_falha` | linhas com `FALHA` (não obtidos ou não lidos) |
| `linhas_extraidas` | soma das linhas da usina (EVT: antes da consolidação; cadastro: linhas com o CEG) |
| `linhas_so_identificador`, `linhas_so_conferencia` | soma das linhas que conferem só em parte |
| `linhas_formato_irregular` | soma das linhas irregulares |
| `valores_invalidos` | soma dos valores inválidos; 0 onde a auditoria não tem essa contagem (indicadores, cadastro). Na EVT, vem da coluna `valores_invalidos` da auditoria, levada ao resumo por `auditoria_evt_normalizada` |
| `registrados_no_manifesto` | entradas dos manifestos das pastas do conjunto, inclusive arquivos fora do período |
| `publicacao_mais_recente` | maior `ultima_modificacao` desses manifestos |
| `data_obtencao` | maior `registrado_em_utc` desses manifestos |

Exemplo (na São Domingos, com `--sem-portal`): `"energia-vertida-turbinavel": {"arquivos_no_escopo": 42, "baixados": 0, "reaproveitados": 0, "nao_obtidos": 0, "lidos": 42, "sem_linhas_da_usina": 3, "com_falha": 0, "linhas_extraidas": 70895, "linhas_so_identificador": 0, "linhas_so_conferencia": 0, "linhas_formato_irregular": 0, "valores_invalidos": 0, "registrados_no_manifesto": 42, "publicacao_mais_recente": "2026-09-30T15:06:00.141888", "data_obtencao": "2026-09-30 16:55:59"}`.

## 5. Regras, estados e validações

### 5.1 Perfil da usina: campos e validação

Regras gerais de `validar_perfil`:
- TOML em UTF-8; arquivo ausente ou ilegível é um problema (e o único da mensagem);
- "inteiro" aceita só inteiro do TOML; "real" aceita inteiro ou real; booleano nunca é número; "texto" exige texto não vazio (sem contar espaços);
- campo opcional ausente é aceito; presente, segue as regras de texto;
- as faixas e as coerências só são conferidas quando os campos envolvidos têm o tipo certo;
- campos não previstos são ignorados;
- todos os problemas vão numa só mensagem (código 4). Os textos de cada mensagem estão em [contracts/perfil-usina.md](contracts/perfil-usina.md).

| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `usina.slug` | texto | sim | `^[a-z0-9_]+$`; igual ao nome da pasta em `usinas/` |
| `usina.nome` | texto | sim | não vazio |
| `usina.nome_curto` | texto | sim | não vazio |
| `usina.estado` | texto | sim | `^[A-Z]{2}$` |
| `usina.inicio_operacao_comercial` | inteiro | sim | de 1900 até o ano atual |
| `identificacao.cod_usina` | inteiro | sim | > 0 |
| `identificacao.nome_ons` | texto | sim | `^[A-Z0-9 .\-/]+$` (maiúsculas sem acento) |
| `identificacao.ceg` | texto | sim | `^UHE\.PH\.[A-Z]{2}\.\d{6}-\d\.\d{2}$` |
| `identificacao.id_ons`, `cod_programacao`, `id_reservatorio` | texto | sim | não vazio |
| `parametros.potencia_instalada_mw` | real | sim | > 0 |
| `parametros.unidades_geradoras` | inteiro | sim | ≥ 1 |
| `parametros.potencia_unitaria_mw` | real | sim | > 0; \|unitária × unidades − instalada\| ≤ `TOLERANCIA_POTENCIA_PERFIL_MW` (0,1 MW) |
| `parametros.tipo_turbina` | texto | sim | não vazio |
| `parametros.engolimento_nominal_ug_m3s` | real | sim | > 0 |
| `parametros.garantia_fisica_mwmed` | real | sim | > 0 e ≤ potência instalada |
| `parametros.ip_referencia`, `teif_referencia` | real | sim | 0 ≤ x < 1 |
| `parametros.queda_bruta_m` | real | sim | > 0 |
| `parametros.perda_hidraulica_m` | real | sim | ≥ 0 e < queda bruta |
| `parametros.rendimento_turbina_gerador` | real | sim | 0 < x ≤ 1 |
| `parametros.vazao_remanescente_m3s` | real | sim | ≥ 0 |
| `parametros.fontes.geral`, `parametros.fontes.garantia_fisica` | texto | sim | não vazio |
| `parametros.fontes.inicio_operacao_comercial`, `parametros.fontes.ip_teif` | texto | não | se presente, não vazio |
| `analises.vertimento_minimo_m3s` | real | sim | ≥ 0 (0 = sem vertimento contínuo) |
| `analises.faixas_geracao_mw` | lista de números | sim | não vazia; estritamente crescente; cada valor > `LIMIAR_GERACAO_PARADA_MW` (1 MW) e < `FRACAO_PLENA_CARGA` (0,90) × potência instalada |
| `analises.descricao_vertimento_minimo`, `analises.fontes.vertimento_minimo` | texto | não | se presente, não vazio |
| `textos.ressalva_volume_util` | texto | não | se presente, não vazio |

### 5.2 Identificação da usina em cada conjunto

`conjuntos._corresponde` (indicadores e conjuntos horários): coluna ausente → nenhuma linha confere; valor do perfil inteiro ou real → `pd.to_numeric(coluna) == valor`; texto → igualdade ou "contém" (sem expressão regular) entre textos normalizados (NFKD sem acento, sem espaços nas pontas, maiúsculas).

| Conjunto | Identificador | Conferência | Como compara | Linhas só em parte |
|---|---|---|---|---|
| EVT | `cod_usina` = `cod_usina` | `nom_reservatorio` contém `nome_ons` | código como texto (`strip`) igual a `str(cod_usina)`; nome normalizado, depois de um pré-teste: a última palavra de `nome_ons` precisa estar no texto só convertido para maiúsculas (com acento) | `registros_codigo_sem_nome`, `registros_nome_sem_codigo` |
| Indicadores por UG | `ceg` = `ceg` | `id_usina` = `id_ons` | `_corresponde` | `linhas_so_identificador`, `linhas_so_conferencia` |
| Taxas TEIFa e TEIP e parâmetros | `cod_ceg` = `ceg` | não há | `_corresponde` | não se aplica (vazio) |
| Programação diária | `cod_exibicaousina` = `cod_programacao` | `nom_usina` contém `nome_ons`, e `id_estado` = `estado` | código e estado com `strip`, sem mudar caixa nem acento; nome normalizado; antes, o pyarrow mantém só as linhas com o código ou o estado | `linhas_codigo_sem_conferencia`, `linhas_so_conferencia` |
| Disponibilidade por usina | `id_ons` = `id_ons` | `ceg` = `ceg`, e `id_estado` = `estado` | `_corresponde` | `linhas_so_identificador`, `linhas_so_conferencia` |
| Dados hidrológicos horários | `cod_usina` = `cod_usina` | `nom_reservatorio` contém `nome_ons`, e `id_reservatorio` = `id_reservatorio` | `_corresponde` (código como número) | idem |
| Geração por usina | `id_ons` = `id_ons` | `ceg` = `ceg`, e `id_estado` = `estado` | `_corresponde`, depois do filtro do Parquet `id_ons == <id_ons>` ou `ceg == <ceg>` (valores como publicados) | idem |
| Modalidade das usinas | `ceg` = `ceg` | `id_ons` = `id_ons` e `id_estado` = `estado`: só contados, não excluem a linha | textos normalizados, comparados com os valores do perfil em maiúsculas | `linhas_so_identificador`, `linhas_so_conferencia`; homônimos: nome com `nome_ons` e outro CEG |

Colunas obrigatórias na leitura (sem elas, o arquivo fica `FALHA`): EVT, `cod_usina` e `nom_reservatorio`; indicadores por UG, `ceg` e `id_usina`; taxas e parâmetros, `cod_ceg`; programação, as seis colunas lidas; conjuntos horários, o identificador e `din_instante` (sem a coluna de conferência, as linhas contam como "só identificador"); cadastro, `nom_usina`, `ceg`, `id_ons` e `id_estado`.

### 5.3 Situações e enumerações

| Onde | Valores |
|---|---|
| `status` das auditorias | `PROCESSADO` (com linhas da usina), `SEM_REGISTROS` (lido, sem linhas da usina), `FALHA` (não obtido, vazio, corrompido ou sem coluna obrigatória); na programação, também `INCOMPLETO` |
| `resultado_ultima_obtencao` dos dicionários | `NOVO`, `INALTERADO`, `ALTERADO`, `FALHA`; no registro, também `NAO_PUBLICADO` (formato ausente do catálogo na última consulta) e `NAO_OBTIDO` (conjunto nunca consultado) |
| `origem_registro` do manifesto | `DOWNLOAD`, `ARQUIVO_EXISTENTE` |
| `tipo_match` da EVT | `CODIGO_E_NOME` |
| `status` do `etapa.json` | `concluida`, `falha`, `desatualizada` |

### 5.4 Cache, versões e falhas

- **Reaproveitamento** (`_is_local_copy_current`, sem `--forcar-download`): arquivo local não vazio e, com registro no manifesto, `tamanho_bytes` igual e `ultima_modificacao` igual à do catálogo (só o tamanho, se o catálogo não traz a publicação); sem registro, tamanho igual ao publicado (qualquer tamanho, se o catálogo não traz o `size`), e a cópia é registrada como `ARQUIVO_EXISTENTE`. Nos demais casos, novo download.
- **Download**: até 3 tentativas, com espera de 2 s e 4 s e limite de 60 s cada; tamanho baixado diferente do publicado gera aviso. Esgotadas as tentativas, o arquivo vira `FALHA` na auditoria (`obtido = False`, com a mensagem), a cópia local fica intacta e é lida se existir.
- **Catálogo**: até 3 tentativas, com as mesmas esperas, em qualquer erro de rede ou de leitura (`OSError`, `http.client.HTTPException`), de JSON (`ValueError`) e na resposta com `success` falso. Catálogo inacessível depois delas levanta `DownloadError` (código 1), exceto o dos dicionários, que vira `FALHA` no registro.
- **Cadastro**: sem recurso CSV no catálogo, a coleta registra erro no log e lê a cópia local; sem cópia local, a ficha fica vazia (código 2).
- **Leitura**: arquivo vazio, corrompido ou sem coluna obrigatória → `FALHA`, com o motivo (no CSV vazio da EVT, sem motivo), e a leitura segue nos demais.
- **Instantes**: na EVT, o registro sem `din_instante` é descartado na consolidação; nos conjuntos horários, a linha da usina com instante não interpretável conta em `linhas_usina` e em `valores_invalidos` e fica fora do extraído.

### 5.5 Constantes

| Constante | Valor | Onde |
|---|---|---|
| `DOWNLOAD_CHUNK_SIZE` | 1 MiB | `src/comum/regras.py` |
| `REQUEST_TIMEOUT` | 60 s | idem |
| `MAX_DOWNLOAD_RETRIES` | 3 | idem |
| `RETRY_BACKOFF_FACTOR` | 2,0 (espera de 2^tentativa s: 2 s e 4 s) | idem |
| `MAXIMO_VERSOES_ANTERIORES` | 2 | idem |
| `FORMATO_PROGRAMACAO_DIARIA` | `PARQUET` | idem |
| `PATAMARES_POR_DIA` | 48 | idem |
| `DIRETORIO_DICIONARIOS` | `_dicionarios` | idem |
| `TOLERANCIA_POTENCIA_PERFIL_MW` | 0,1 MW | idem (validação do perfil) |
| `LIMIAR_GERACAO_PARADA_MW`, `FRACAO_PLENA_CARGA` | 1,0 MW; 0,90 | idem (faixas de geração do perfil) |
| `TOLERANCIA_LIMITES_FISICOS` | 0,05 | idem (valores derivados do perfil) |
| `DIRETORIO_VERSOES_ANTERIORES` | `_versoes_anteriores` | `src/coleta/catalogo.py` |
| `DOWNLOADS_SIMULTANEOS` | 8 | `src/coleta/conjuntos.py` e `src/coleta/programacao.py` |
| `FORMATOS_DICIONARIO`, `CHAVE_CONSULTA` | (`PDF`, `JSON`); `_consulta` | `src/coleta/dicionarios.py` |
| `VERSAO_FORMATO` | 1 por etapa | `src/pipeline.py` |
| `CODIGO_SUCESSO` … `CODIGO_DIFERENCAS` | 0 a 6 | idem |
| `NIVEIS_LOG`, `LOGGERS_PIPELINE` | `DEBUG`, `INFO`, `WARNING`, `ERROR`; `pipeline`, `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio`, `persistencia` | `src/comum/logger.py` |
| `MAXIMO_COPIAS` | 2 | `src/comum/copia_seguranca.py` |

### 5.6 Códigos de saída da Coleta

| Código | Quando |
|---|---|
| 0 | os dez conjuntos tratados sem `FALHA`, com a usina na EVT e no cadastro |
| 1 | catálogo inacessível depois das tentativas, falha de gravação (arquivo restaurado), interrupção pelo usuário ou erro inesperado |
| 2 | algum arquivo `FALHA` no conjunto em tratamento (a coleta para nele), nenhuma linha da usina na EVT, ficha cadastral vazia; ou opção inválida na linha de comando |
| 4 | perfil inválido |

A tabela completa, comum às cinco etapas, está em [contracts/cli-coleta.md](contracts/cli-coleta.md).
