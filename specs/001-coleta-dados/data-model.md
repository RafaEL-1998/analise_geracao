# Data Model: Coleta de dados

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-23

Além dos arquivos da Coleta, este documento descreve as estruturas comuns às cinco etapas, citadas pelas demais specs: o perfil da usina (seções 3.1 e 5.1), o `etapa.json` (seção 4), os manifestos, as versões anteriores e os dicionários dos dados brutos (seção 2.1) e a cópia de segurança do projeto (seção 2.4). Descreve também o catálogo de usinas (seção 2.5), o rascunho do perfil (seção 2.6), o registro dos conjuntos do ONS (seção 6), a série de referência e os trechos (seção 7) e as usinas fictícias dos testes (seção 8).

Os arquivos e as colunas que o relatório da UHE usa não mudam com os demais tipos: informação nova vai para arquivo novo (decisão técnica D26).

## 1. Entradas

### 1.1 Perfil da usina

`usinas/<slug>/perfil.toml`, lido e validado por `src.comum.perfil.carregar_perfil` em `src/__main__.py`, antes de qualquer outra ação. A Coleta usa estes campos (os demais são validados aqui e usados pelas etapas seguintes; seção 5.1 e [contracts/perfil-usina.md](contracts/perfil-usina.md)):

| Campo | Uso na Coleta |
|---|---|
| `usina.slug` | pasta `data/usinas/<slug>/coleta/` |
| `usina.tipo` | conjuntos do tipo no registro (seção 6), série de referência (seção 7) e variante das restrições; na Programação diária, a conferência pelo nome só nas hidrelétricas |
| `usina.modalidade` | resumo do `etapa.json` |
| `usina.estado` | conferência na Programação diária, na Disponibilidade por usina, na Geração por usina (da usina e do conjunto), no fator de capacidade e na razão da restrição do conjunto, na Composição dos conjuntos, na Capacidade de geração e no cadastro |
| `usina.nome_curto` | homônimos no cadastro, nos tipos sem `nome_ons` |
| `usina.subsistema` | identificador no CMO semanal; conferência no CVU |
| `[cobertura]` | conjuntos de série obtidos e o nível de cada um (`proprio` → usina, `conjunto` → conjunto) |
| `identificacao.cod_usina` | identificador na EVT e nos Dados hidrológicos horários |
| `identificacao.nome_ons` | conferência ("contém") na EVT, na hidrologia e, nas hidrelétricas, na programação; homônimos no cadastro |
| `identificacao.ceg` | identificador nos indicadores, nas taxas, no cadastro, no despacho e na Capacidade de geração; conferência na disponibilidade, na geração, no fator de capacidade e nas restrições da usina; a usina na composição do conjunto |
| `identificacao.id_ons` | identificador na disponibilidade, na geração, no fator de capacidade e nas restrições da usina; conferência nos indicadores por UG e no cadastro |
| `identificacao.id_conjunto` | identificador na geração, no fator de capacidade e na razão da restrição do conjunto e na Composição dos conjuntos |
| `identificacao.cod_programacao` ou `codigos_programacao` | identificador na Programação diária (um ou mais códigos de exibição) |
| `identificacao.id_reservatorio` | conferência na hidrologia |
| `[[identificacao.planejamento]]` | conferência no despacho (código no período dele); identificador no CVU; cortes dos trechos |
| `[[identificacao.membros]]` | restrição com detalhe das outras usinas do conjunto |

### 1.2 Portal de dados abertos do ONS

Catálogo CKAN `https://dados.ons.org.br/api/3/action/package_show?id=<id>` (`ONS_CKAN_PACKAGE_SHOW_URL`), lido por `catalogo.fetch_ckan_package_metadata`. De cada recurso, `catalogo.parse_ckan_resources` guarda `url`, `name`, `id`, `format`, `size` e a publicação (`last_modified`, ou `metadata_modified`, ou `created`). Ids e pastas ficam em `src/comum/regras.py` (`CONJUNTO_*`, `CONJUNTOS_INDICADORES_ONS` e `PASTA_*_RAW`); a lista dos conjuntos do fluxo (`CONJUNTOS_PIPELINE`) é derivada do registro (seção 6).

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
| Geração por usina | `geracao-usina-2` | `geracao_usina_2/` | idem | idem; na série de referência, todos os arquivos publicados | idem |
| Geração térmica por motivo de despacho | `geracao-termica-despacho-2` | `geracao_termica_despacho_2/` | idem | idem | idem |
| CVU das usinas térmicas | `cvu-usitermica` | `cvu_usitermica/` | idem | idem | idem |
| CMO semanal | `cmo-semanal` | `cmo_semanal/` | idem | idem | idem |
| Fator de capacidade | `fator-capacidade-2` | `fator_capacidade_2/` | idem | idem | idem |
| Restrição com detalhe, eólica e fotovoltaica | `restricao_coff_eolica_detail`, `restricao_coff_fotovoltaica_detail` | pasta com o nome do id | idem | idem, só a variante do tipo; na série de referência, todos os arquivos publicados | idem |
| Restrição com a razão, eólica e fotovoltaica | `restricao_coff_eolica_usi`, `restricao_coff_fotovoltaica` | pasta com o nome do id | idem | idem, só a variante do tipo | idem |
| Modalidade das usinas | `modalidade-usina` | `modalidade_usina/` | o primeiro recurso de formato CSV cujo nome, sem acento, não contém "DICIONARIO" | arquivo único | `cadastro.sincronizar_cadastro` |
| Composição dos conjuntos | `usina_conjunto` | `usina_conjunto/` | Parquet, senão CSV, sem "DICIONARIO" no nome | arquivo único (entre repetidos, o recurso preferido) | `catalogo_usinas.sincronizar_cadastral` |
| Capacidade de geração | `capacidade-geracao` | `capacidade_geracao/` | idem | idem | idem |
| Reservatórios | `reservatorio` | `reservatorio/` | idem | idem; só o catálogo de usinas o obtém | idem |
| Dicionários dos conjuntos da usina | os mesmos | `<pasta do conjunto>/_dicionarios/` | PDF e JSON cujo nome, sem acento, contém "DICIONARIO" | todos | `dicionarios.sincronizar_dicionarios` |

Um recurso é aceito pelo formato declarado ou pela extensão da URL (no cadastro, nos cadastrais do catálogo e nos dicionários, só pelo formato declarado). Em todos os conjuntos, entre recursos repetidos no catálogo para o mesmo arquivo, fica o que tem publicação e, em empate, o maior (`catalogo.recurso_preferido`). O período é o da série de referência (seção 7): na hidrelétrica com EVT, do primeiro ao último `din_instante` da EVT extraída. A série de referência fora da EVT é sincronizada de 1990 (`INICIO_VARREDURA`) até um ano depois da data da execução, ou seja, com todos os arquivos publicados.

### 1.3 Arquivos locais lidos

A leitura não desce às subpastas, de modo que `_versoes_anteriores/` e `_dicionarios/` nunca são lidos como dados.

| Conjunto | Arquivos lidos | Ordem de leitura | Função |
|---|---|---|---|
| EVT | `data/raw/*.csv` | nome (anuais antes dos mensais) | `evt.filter_all_raw_files` |
| Indicadores e taxas | `indicadores_ons/<id>/*.csv` dos anos do período e sem ano | `ind_..._mensal`, `ind_..._anual`, `taxa_teif_teip_parametro`, `taxa_teif_teip`; dentro de cada um, nome | `indicadores.extrair_indicadores` |
| Programação diária | `programacao_diaria/*.parquet` dos dias do período | nome | `programacao.extrair_programacao` |
| Conjuntos do motor comum (disponibilidade, hidrologia, geração, despacho, CVU, CMO, fator de capacidade e restrições) | um arquivo por ano ou mês sobreposto ao período: o `.parquet`, senão o `.csv` | data de publicação no manifesto, depois nome | `conjuntos.extrair_conjunto` |
| Série de referência fora da EVT | todos os arquivos locais do conjunto, por ano ou mês, no formato preferido | idem | `serie_referencia.extrair_referencia` |
| Restrição com detalhe das outras usinas do conjunto | os arquivos do período, um membro por vez | idem | `etapa._coletar_membros` |
| Modalidade das usinas | o CSV sincronizado nesta execução ou, sem ele, o primeiro `*.csv` da pasta | — | `cadastro.extrair_cadastro` |
| Composição dos conjuntos e Capacidade de geração | o primeiro arquivo da pasta no formato preferido (Parquet, senão CSV) | — | `catalogo_usinas.ler_cadastral` |

Os manifestos das pastas também são lidos: dão a data de publicação de cada arquivo na auditoria, as datas de obtenção (`datas_obtencao.csv`) e, no cadastro, a data da consulta.

### 1.4 Colunas lidas dos arquivos do ONS

| Conjunto | Colunas de identificação | Colunas extraídas |
|---|---|---|
| EVT | `cod_usina`, `nom_reservatorio` | as 18 colunas publicadas |
| Indicadores por UG | `ceg`, `id_usina` | todas as colunas publicadas |
| Taxas e parâmetros | `cod_ceg` | todas as colunas publicadas |
| Programação diária | `cod_exibicaousina`, `nom_usina`, `id_estado`; `din_programacaodia` (conferência da data) | `num_patamar`, `val_geracaoprogramada`; com mais de um código, também `cod_exibicaousina` |
| Disponibilidade por usina | `id_ons`, `ceg`, `id_estado` | `din_instante`, `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` |
| Dados hidrológicos horários | `cod_usina`, `nom_reservatorio`, `id_reservatorio` | `din_instante`, `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas`, `val_nivelmontante`, `val_niveljusante`, `val_volumeutil` |
| Geração por usina | `id_ons`, `ceg`, `id_estado` (da usina); `id_ons`, `id_estado` (do conjunto) | `din_instante`, `val_geracao`; na série de referência, também `cod_modalidadeoperacao` e, no conjunto, `nom_tipousina` e `nom_tipocombustivel` (texto) |
| Geração térmica por motivo de despacho | `ceg`, `cod_usinaplanejamento` | `din_instante`, `cod_usinaplanejamento`, as 17 colunas `val_prog*` e as 15 `val_verif*` (seção 2.2), `tip_restricaoeletrica`; `nom_tipopatamar` (texto) |
| CVU das usinas térmicas | `cod_usinaplanejamento`, `id_subsistema` | `dat_iniciosemana` (gravada como `din_instante`), `cod_usinaplanejamento`, `num_revisao`, `val_cvu`; `dat_iniciosemana` e `dat_fimsemana` (texto) |
| CMO semanal | `id_subsistema` | `din_instante`, `val_cmomediasemanal`, `val_cmoleve`, `val_cmomedia`, `val_cmopesada`; `id_subsistema` (texto) |
| Fator de capacidade | `id_ons`, e `ceg` (usina) ou `id_estado` (conjunto) | `din_instante`, `val_geracaoprogramada`, `val_geracaoverificada`, `val_capacidadeinstalada`, `val_fatorcapacidade` |
| Restrição com detalhe | `id_ons`, `ceg` | `din_instante`, `val_geracaoestimada`, `val_geracaoverificada`, `val_ventoverificado` e `flg_dadoventoinvalido` (EOL) ou `val_irradianciaverificado` e `flg_dadoirradianciainvalido` (UFV), `flg_geracaorestrita`, `val_geracaoreferenciafinal`; `id_ons_conjuntousina` e `nom_modalidadeoperacao` (texto) |
| Restrição com a razão | `id_ons`, e `ceg` (usina) ou `id_estado` (conjunto) | `din_instante`, `val_geracao`, `val_geracaolimitada`, `val_disponibilidade`, `val_geracaoreferencia`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene`; `cod_razaorestricao` (texto) |
| Modalidade das usinas | `ceg`, `id_ons`, `id_estado`, `nom_usina` (obrigatórias) | as colunas da ficha (seção 2.2) |
| Composição dos conjuntos | `id_ons_conjunto`, `estad_id` | `id_ons_conjunto`, `nom_conjunto`, `ceg`, `id_ons_usina`, `nom_usina`, `id_tipousina`, `dat_iniciorelacionamento`, `dat_fimrelacionamento`, `estad_id`, `id_subsistema` |
| Capacidade de geração | `ceg`, `id_estado`; nas usinas do conjunto, `ceg` e `id_subsistema` | `cod_equipamento`, `num_unidadegeradora`, `nom_unidadegeradora`, `val_potenciaefetiva`, `nom_combustivel`, `dat_entradateste`, `dat_entradaoperacao`, `dat_desativacao`, `nom_agenteproprietario`, `nom_agenteoperador`; nas usinas do conjunto, também `ceg` e `nom_usina` |

## 2. Saídas

### 2.1 Dados brutos compartilhados (`data/raw/`)

Gravados só pela Coleta (comandos `coleta`, `completo` e `usinas`) e só quando ela consulta o portal; servem a todas as usinas e ao catálogo.

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
├── modalidade_usina/
├── usina_conjunto/
├── capacidade_geracao/
├── reservatorio/
├── geracao_termica_despacho_2/
├── cvu_usitermica/
├── cmo_semanal/
├── fator_capacidade_2/
├── restricao_coff_eolica_detail/
├── restricao_coff_fotovoltaica_detail/
├── restricao_coff_eolica_usi/
└── restricao_coff_fotovoltaica/
```

Cada pasta de conjunto tem os arquivos de dados, `_manifesto_ons.json`, `_versoes_anteriores/` (quando houver) e `_dicionarios/`.

**Arquivos de dados**: o nome é o último trecho da URL, sem parâmetros; se ele não termina na extensão do formato, `<nome do recurso>.<ext>` (`catalogo._local_filename`). O download vai para `<nome>.<id do recurso>.part` (ou `<nome>.part`, sem id), que substitui o arquivo só quando completo. Nenhum arquivo é editado: ele só é substituído inteiro por uma versão publicada.

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
| `recursos_duplicados_catalogo` | inteiro | só quando houve repetição: recursos repetidos no catálogo para o mesmo arquivo, descartados (em todos os conjuntos) |

- Item de `versoes_anteriores`: `arquivo_preservado` (`_versoes_anteriores/<nome>`), `ultima_modificacao` (publicação da versão preservada), `tamanho_bytes`, `sha256` e `arquivado_em_utc`. As mais recentes ficam no fim da lista.
- Item de `versoes_excluidas`: `arquivo_preservado`, `ultima_modificacao`, `sha256` e `excluido_em_utc`.
- **Data de obtenção de um conjunto**: o maior `registrado_em_utc` do manifesto da pasta; na usina, contado só nos arquivos do escopo dela (`datas_obtencao.csv`, seção 2.2); no resumo da Coleta, a entrada `indicadores` junta as quatro pastas.

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
- Vale para os arquivos de dados e para os dicionários, em todos os conjuntos.

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

Cada usina tem só os arquivos dos conjuntos coletados para ela (spec, FR-016 e "Aplicabilidade por tipo"). Regras comuns:
- gravados por `src/comum/persistencia.py`: `.bak` da versão anterior (`<nome>.bak`), conteúdo idêntico não regravado, conferência no disco e restauração em falha ou interrupção (Ctrl+C);
- CSV com `;`, UTF-8 sem BOM e fim de linha do sistema (CRLF no Windows); data e hora `AAAA-MM-DD HH:MM:SS`; booleanos `True` e `False`; vazio = ausente;
- Parquet gravado pelo pyarrow, sem índice;
- cada execução que chega a um arquivo o grava de novo, mas o conteúdo igual ao anterior não é regravado (`INALTERADO`); a `auditoria_evt.csv` muda sempre, porque traz a hora da leitura.

#### `evt_extraido.csv`

Uma linha por (`cod_usina`, `din_instante`), em ordem cronológica, sem horas criadas nem preenchidas. Gravado por `evt.save_consolidated_records` (`gravar_linhas_csv`, módulo `csv`). Só na hidrelétrica com EVT.

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
| `mensagem` | texto | motivo da falha; no CSV vazio (sem cabeçalho), "arquivo vazio" |

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

Uma linha por dia e patamar da usina (com mais de um código, por dia, código e patamar); num patamar repetido no mesmo arquivo e código, fica a última ocorrência.

| Coluna | Tipo | Descrição |
|---|---|---|
| `dia` | data e hora (meia-noite) | dia do nome do arquivo |
| `num_patamar` | inteiro | patamar de 30 minutos, de 1 a 48 |
| `geracao_programada_mw` | real | `val_geracaoprogramada` (MWmed), vírgula ou ponto decimal |
| `arquivo_origem` | texto | arquivo bruto |
| `cod_exibicaousina` | texto | só com mais de um código no perfil: o código da linha; a soma por patamar é do Tratamento de dados |

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
| `linhas_so_conferencia` | inteiro | a conferência (estado e, nas hidrelétricas, nome) confere, o código não |
| `valores_invalidos` | inteiro | `num_patamar` ou `val_geracaoprogramada` preenchidos e não numéricos |
| `patamares` | inteiro | patamares distintos da usina |
| `data_interna_confere` | booleano | `din_programacaodia` igual ao dia do nome; `True` sem linhas da usina; `False` na falha |
| `status` | texto | `PROCESSADO`, `SEM_REGISTROS`, `INCOMPLETO` (patamares diferentes de 48) ou `FALHA` |
| `mensagem` | texto | motivo da falha |

#### Extraídos do motor comum: `disponibilidade_extraido.parquet`, `hidrologia_extraido.parquet`, `geracao_extraido.parquet` e os dos demais tipos

Uma linha por linha da usina com instante válido, na ordem de leitura dos arquivos; as repetições entre arquivos ficam todas, para o Tratamento.

| Coluna | Tipo | Descrição |
|---|---|---|
| `din_instante` | data e hora | instante como publicado: hora de início na disponibilidade, na geração e nos conjuntos dos demais tipos; hora de fim na hidrologia (`DescricaoConjunto.convencao_hora`, aplicada pelo Tratamento); no CVU, o início da semana operativa (`dat_iniciosemana`); nas restrições, a semi-hora |
| colunas de valor | real | ver abaixo; ausente quando vazio ou não numérico na fonte |
| colunas de texto | texto | ver abaixo; sem espaços nas pontas, vazias quando ausentes no arquivo |
| `_nao_numerico` | booleano | a linha tinha algum valor não numérico na fonte (as linhas com instante inválido ficam fora do arquivo) |
| `arquivo_origem` | texto | arquivo bruto |
| `nivel` | texto | só no fator de capacidade e na razão da restrição: `usina` ou `conjunto` |
| `id_ons` | texto | só em `restricao_membros_extraido.parquet`: o id ONS do membro |

| Arquivo | Colunas de valor | Colunas de texto |
|---|---|---|
| `disponibilidade_extraido.parquet` | `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` (MW) | — |
| `hidrologia_extraido.parquet` | `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas` (m³/s); `val_nivelmontante`, `val_niveljusante` (m); `val_volumeutil` (%) | — |
| `geracao_extraido.parquet` | `val_geracao` (MWmed) | — |
| `despacho_extraido.parquet` | `cod_usinaplanejamento`; programadas `val_proggeracao`, `val_progordemmerito`, `val_progordemdemeritoref`, `val_progordemdemeritoacimadainflex`, `val_proginflexibilidade`, `val_proginflexembutmerito`, `val_proginflexpura`, `val_prograzaoeletrica`, `val_proggarantiaenergetica`, `val_proggfom`, `val_progreposicaoperdas`, `val_progexportacao`, `val_progreservapotencia`, `val_proggsub`, `val_progunitcommitment`, `val_progconstrainedoff`, `val_proginflexibilidadedessem`; verificadas `val_verifgeracao`, `val_verifordemmerito`, `val_verifordemdemeritoacimadainflex`, `val_verifinflexibilidade`, `val_verifinflexembutmerito`, `val_verifinflexpura`, `val_verifrazaoeletrica`, `val_verifgarantiaenergetica`, `val_verifgfom`, `val_verifreposicaoperdas`, `val_verifexportacao`, `val_verifreservapotencia`, `val_verifgsub`, `val_verifunitcommitment`, `val_verifconstrainedoff`; `tip_restricaoeletrica` | `nom_tipopatamar` |
| `cvu_extraido.parquet` | `cod_usinaplanejamento`, `num_revisao`, `val_cvu` (R$/MWh) | `dat_iniciosemana`, `dat_fimsemana` |
| `cmo_extraido.parquet` | `val_cmomediasemanal`, `val_cmoleve`, `val_cmomedia`, `val_cmopesada` (R$/MWh) | `id_subsistema` |
| `fator_capacidade_extraido.parquet` | `val_geracaoprogramada`, `val_geracaoverificada`, `val_capacidadeinstalada`, `val_fatorcapacidade` | — |
| `restricao_detalhe_extraido.parquet` e `restricao_membros_extraido.parquet` | `val_geracaoestimada`, `val_geracaoverificada`, `val_ventoverificado` e `flg_dadoventoinvalido` (EOL) ou `val_irradianciaverificado` e `flg_dadoirradianciainvalido` (UFV), `flg_geracaorestrita`, `val_geracaoreferenciafinal` (marcas booleanas lidas como 1 e 0) | `id_ons_conjuntousina`, `nom_modalidadeoperacao` |
| `restricao_razao_extraido.parquet` | `val_geracao`, `val_geracaolimitada`, `val_disponibilidade`, `val_geracaoreferencia`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene` | `cod_razaorestricao` |

- **`geracao_extraido.parquet` fora da hidrelétrica com EVT**: com a Geração por usina como série de referência, uma linha por hora do período, a da usina quando ela tem valor e senão a do conjunto, com as mesmas colunas (seção 7). Com a cobertura `conjunto`, traz a série do conjunto. Na eólica ou solar cuja série de referência é a restrição com detalhe, traz a Geração por usina no nível da cobertura, no período.
- **`restricao_detalhe_extraido.parquet` como série de referência**: a série inteira do período, com todas as colunas extraídas.
- **`restricao_membros_extraido.parquet`**: a restrição com detalhe das outras usinas de `[[identificacao.membros]]`, uma por vez, pelo id ONS e pelo CEG de cada uma, no período; só para a conferência da soma das usinas com o conjunto.

#### Auditorias do motor comum: `auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv`, `auditoria_geracao.csv` e as dos demais tipos

Uma linha por arquivo do período, lido ou não obtido, na ordem de leitura (`conjuntos.COLUNAS_AUDITORIA_COLETA`). Valem também para `auditoria_despacho.csv`, `auditoria_cvu.csv`, `auditoria_cmo.csv`, `auditoria_fator_capacidade.csv`, `auditoria_restricao_detalhe.csv`, `auditoria_restricao_razao.csv` e `auditoria_restricao_membros.csv` (esta com a coluna `id_ons` a mais, uma linha por arquivo e membro). Na série de referência fora da EVT, a auditoria lista todos os arquivos varridos. O Tratamento completa essas auditorias com as horas da usina e as duplicatas entre arquivos.

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
| `linhas_so_conferencia` | inteiro | só a conferência confere; 0 no CMO, sem conferência |
| `valores_invalidos` | inteiro | instantes não interpretáveis mais valores não numéricos, nas linhas da usina |
| `recursos_duplicados_catalogo` | inteiro | recursos repetidos no catálogo para o arquivo (do manifesto) |
| `status` | texto | `PROCESSADO`, `SEM_REGISTROS` ou `FALHA` |
| `mensagem` | texto | motivo da falha (inclusive "coluna de conferência ausente: <coluna>"); sem falha, nos conjuntos com colunas que faltam em parte dos arquivos, "colunas ausentes no arquivo: <colunas>" |

#### Auditorias dos cadastrais: `auditoria_composicao.csv`, `auditoria_capacidade.csv` e `auditoria_capacidade_membros.csv`

Uma linha pela leitura do arquivo único, com as colunas da auditoria do motor comum, `periodo` = `estatico`, `formato` pela extensão (`PARQUET` ou `CSV`) e `linhas_lidas` = linhas do arquivo. Na Composição, `linhas_usina` são as linhas do conjunto com o estado do perfil, e `linhas_so_identificador`, as do conjunto com outro estado; na Capacidade, as unidades com o CEG e o estado do perfil, e as só com o CEG. Em `auditoria_capacidade_membros.csv`, `linhas_usina` são as unidades das usinas da composição com o subsistema da linha delas na composição, `linhas_so_identificador` as só com o CEG, e `mensagem` traz `usinas da composição no período: <n>; com unidades: <m>`. Cadastral não obtido: uma linha `FALHA`, com `obtido = False` e o motivo.

#### `cadastro_ficha.csv`

Uma linha (a primeira com o CEG do perfil) ou nenhuma, se a usina não está no cadastro (`cadastro.COLUNAS_FICHA`).

| Coluna | Tipo | Descrição |
|---|---|---|
| `nom_usina` | texto | nome no cadastro |
| `ceg`, `id_ons` | texto | identificação |
| `nom_modalidadeoperacao` | texto | modalidade de operação |
| `sgl_centrooperacao` | texto | centro de operação |
| `nom_pontoconexao` | texto | ponto de conexão |
| `val_potenciaautorizada` | real | potência autorizada (MW), vírgula ou ponto decimal |
| `id_estado` | texto | estado |
| `sts_aneel` | texto | situação na ANEEL (`A`, `I`, `P`, `C` ou `O`) |
| `data_consulta_utc` | texto `AAAA-MM-DD HH:MM:SS` | `registrado_em_utc` do arquivo no manifesto |
| `arquivo_origem` | texto | arquivo bruto |
| `homonimos` | inteiro | linhas com `nome_ons` (nos tipos sem ele, `nome_curto`) no nome da usina e outro CEG |
| `linhas_so_identificador` | inteiro | linhas com o CEG e id ONS ou estado diferente do perfil |
| `linhas_so_conferencia` | inteiro | linhas com id ONS e estado do perfil e outro CEG |
| `linhas_ceg` | inteiro | linhas com o CEG; mais de uma indica CEG repetido |

#### `auditoria_cadastro.csv`

Uma linha pela leitura do arquivo local (sem arquivo local, nenhuma), mais uma por falha de download (`cadastro.COLUNAS_AUDITORIA_CADASTRO`): `arquivo`, `formato` (`CSV`), `data_publicacao`, `obtido`, `linhas_lidas` (linhas mais as irregulares), `linhas_formato_irregular`, `linhas_usina` (linhas com o CEG), `linhas_so_identificador`, `linhas_so_conferencia` (como na ficha), `status` (`PROCESSADO`, `SEM_REGISTROS` ou `FALHA`) e `mensagem`.

#### `capacidade_ficha.csv`

As unidades geradoras do CEG da usina na Capacidade de geração, conferidas pelo estado, todas as que o arquivo traz (ativas e desativadas): `cod_equipamento`, `num_unidadegeradora`, `nom_unidadegeradora`, `val_potenciaefetiva`, `nom_combustivel`, `dat_entradateste`, `dat_entradaoperacao`, `dat_desativacao`, `nom_agenteproprietario` e `nom_agenteoperador`, como publicados (`etapa.COLUNAS_CAPACIDADE_FICHA`). Com `[cobertura]`.

#### `composicao_conjunto.csv`

As linhas do conjunto da usina na Composição dos conjuntos, conferidas pelo estado, com as colunas de `conjuntos.csv` do catálogo (seção 2.5): `id_conjunto`, `nom_conjunto`, `ceg`, `id_ons_usina`, `nom_usina`, `tipo` (pelo CEG), `tipo_ons`, `inicio`, `fim` (`AAAA-MM-DD`; vazio ou data sentinela = vigente), `estado` e `subsistema`. Na usina com `id_conjunto`.

#### `capacidade_membros.csv`

As unidades geradoras de cada usina que esteve na composição do conjunto em algum momento do período, conferidas pelo subsistema da linha dela na composição (`etapa.COLUNAS_CAPACIDADE_MEMBROS`): `ceg`, `nom_usina` e as colunas de `capacidade_ficha.csv`. Na usina com `id_conjunto` e a composição coletada.

#### `tipo_publicado.csv`

Na usina cuja série de referência é a Geração por usina do conjunto (`serie_referencia.COLUNAS_TABELA_TIPO_PUBLICADO`):

| Coluna | Conteúdo |
|---|---|
| `trecho`, `inicio`, `fim` | trecho de `trechos.csv` |
| `nom_tipousina`, `nom_tipocombustivel` | tipo e combustível publicados na série do conjunto |
| `horas` | horas do trecho com esse tipo e esse combustível |

Exemplo (Bandeirante): o Conj. Chapadão publicado como `TÉRMICA` e `Biomassa` nos três trechos, inclusive no último, só com PCH.

#### `geracao_complemento.parquet` e `trechos.csv`

Fora da hidrelétrica com EVT: `geracao_complemento.parquet` traz, por hora do período, `din_instante`, `cod_modalidadeoperacao` (a modalidade publicada na série de referência; na restrição com detalhe, `nom_modalidadeoperacao`) e `nivel` (`usina` ou `conjunto`); nas séries semi-horárias, uma linha por hora cheia. `trechos.csv` está na seção 7.2.

#### `dicionarios.csv`

Uma linha por conjunto da usina e formato (PDF e JSON), na ordem do registro; na UHE sem `[cobertura]`, vinte linhas, os dez conjuntos da UHE. Montado só dos manifestos de `_dicionarios/` (`dicionarios.montar_registro`), inclusive com `--sem-portal`; nas restrições, só a variante do tipo.

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

#### `datas_obtencao.csv`

Uma linha por conjunto coletado (os quatro de indicadores e taxas em linhas separadas), na ordem do registro (`etapa.COLUNAS_DATAS_OBTENCAO`), gravada no fim da coleta, também quando ela para com 2. Substitui a leitura dos manifestos de `data/raw/` nas Análises e no Relatório, inclusive a linha "Versão dos arquivos" da cobertura.

| Coluna | Conteúdo |
|---|---|
| `conjunto` | id do conjunto no catálogo |
| `arquivos_registrados` | arquivos do escopo da usina obtidos (pela auditoria) e registrados no manifesto da pasta |
| `publicacao_mais_recente` | maior `ultima_modificacao` desses arquivos |
| `obtencao_mais_recente` | maior `registrado_em_utc` desses arquivos |

#### `dicionario_evt.json`

Na hidrelétrica com EVT: a cópia de `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json`, gravada por `gravar_bytes`. Sem o dicionário em `data/raw/`, a Coleta avisa no log e não grava a cópia; o Tratamento recusa a base.

### 2.3 Quem lê cada saída

| Saída | Lida por |
|---|---|
| `evt_extraido.csv` e `dicionario_evt.json` | Tratamento (`tratar_evt` e a validação física) |
| `indicadores_extraido.parquet` | Tratamento (`montar_indicadores`, com `separar_conjuntos`) |
| `programacao_extraido.parquet` e `auditoria_programacao.csv` | Tratamento (`montar_programacao`); a auditoria também nas Análises |
| extraídos e auditorias do motor comum | Tratamento (séries horárias, térmicas e renováveis) |
| `restricao_membros_extraido.parquet` | Tratamento (membros em hora cheia, para a conferência da soma do conjunto) |
| `geracao_complemento.parquet` e `trechos.csv` | Tratamento (base horária comum); os trechos também nas Análises |
| `composicao_conjunto.csv`, `capacidade_ficha.csv`, `capacidade_membros.csv` e `tipo_publicado.csv` | Análises (conjunto, peso da usina, agente atual, qualidade dos dados) |
| `cadastro_ficha.csv` | Conferência (cadastro) e Análises |
| `auditoria_evt.csv`, `auditoria_cadastro.csv`, `dicionarios.csv` e `datas_obtencao.csv` | Análises (cobertura, datas de obtenção e registros mostrados no relatório) |
| `auditoria_indicadores.csv`, auditorias dos cadastrais | nenhuma etapa; registro da varredura |
| `etapa.json` (resumo) | Tratamento e Análises (período, série de referência, linhas próprias sem valor) |
| `data/raw/` | nenhuma etapa além da Coleta (decisão técnica D29) |
| `data/catalogo/` | comando `perfil` e relatório de carteira (spec da Geração do relatório) |

### 2.4 Cópia de segurança do projeto (`_backup_<AAAA-MM-DD>_<motivo>/`)

Criada na raiz do projeto por `python -m src copia-seguranca --motivo <texto>` (`src/comum/copia_seguranca.py`).

| Item | Conteúdo |
|---|---|
| Pastas copiadas | `src/`, `tests/`, `specs/`, `reports/` e `.specify/`, sem `__pycache__`, `*.pyc` e `.pytest_cache`; `relatorios_referencia/` inteira, sem as pastas temporárias `.gravando_*` e `.anterior_*` |
| Arquivos copiados | `usinas/<slug>/perfil.toml` de cada usina, `README.md` e `requirements.txt` |
| `copia.json` | lista JSON (indentação 1) com `{"arquivo": <caminho relativo com "/">, "bytes": <tamanho>, "sha256": <SHA-256>}` de cada arquivo copiado, conferido contra a origem |
| `conftest.py` | `collect_ignore_glob = ["*"]`, que impede o pytest de varrer a cópia |
| `LEIA-ME.txt` | data (DD/MM/AAAA), motivo, o que foi copiado, as referências levadas e o papel de `copia.json` e `conftest.py` |
| Fora da cópia | todo o resto, inclusive `data/` (brutos, catálogo e etapas), `usinas/<slug>/documentos/`, `referencias/` e `venv/` |

Conferência: a quantidade de arquivos (sem os três de controle) e o SHA-256 de cada um, contra o registro; cada referência copiada, contra os SHA-256 do `referencia.json` dela. Poda: das pastas `_backup_<AAAA-MM-DD>_*`, ordenadas pela data do nome e, no empate, pela data de criação, ficam as duas mais recentes (`MAXIMO_COPIAS`).

### 2.5 Catálogo de usinas (`data/catalogo/`)

Gravado pelo comando `usinas` (`src/coleta/catalogo_usinas.py`), por inteiro a cada montagem, sem `.bak`: numa pasta temporária (`.gravando`), conferida (arquivo presente e não vazio) antes da troca. Nenhuma etapa da usina grava aqui. A listagem e o `perfil` leem o catálogo só pelos arquivos gravados (`ler_catalogo`, todas as colunas como texto); catálogo sem `catalogo.json` ou com outro `versao_formato` conta como ausente.

#### `catalogo.json`

| Campo | Conteúdo |
|---|---|
| `versao_formato` | `VERSAO_FORMATO_CATALOGO` (1); muda quando os arquivos do catálogo mudam de formato |
| `montado_em_utc` | data e hora da montagem |
| `sem_portal` | montado só com os arquivos locais |
| `cadastro` | por pacote cadastral (`modalidade-usina`, `usina_conjunto`, `capacidade-geracao`, `reservatorio`), o `arquivo` e a `publicacao` |
| `cobertura` | por conjunto de série verificado: `conjunto` (chave do registro), `variante` (nas restrições), `pacote`, `arquivo` e `publicacao` |
| `agregados` | `meses` usados no panorama, `meses_sem_arquivo` e `arquivos` |
| `contagens` | `por_tipo` e `por_estado`: linhas do cadastro |

#### `usinas.csv`

Uma linha por linha do cadastro do ONS, sem filtro (6.024 em 19/10/2026).

| Coluna | Conteúdo |
|---|---|
| `ceg`, `id_ons`, `nom_usina` | como publicados, sem espaços nas pontas; o nome só para exibição, nunca para identificação; `id_ons` pode vir vazio |
| `tipo` | pelo prefixo do CEG (decisão técnica D19): um dos sete, `conjunto` ou `outro` |
| `modalidade`, `id_estado`, `sgl_centrooperacao`, `nom_pontoconexao`, `sts_aneel` | do cadastro |
| `subsistema` | da Capacidade de geração ou, sem ela, da Composição dos conjuntos vigente |
| `potencia_autorizada_mw` | número; vírgula ou ponto decimal |
| `id_conjunto`, `nom_conjunto` | conjunto vigente, da Composição dos conjuntos; vazio fora de conjunto |
| `unidades_geradoras`, `potencia_efetiva_mw`, `potencias_unidades_mw`, `combustivel`, `entrada_operacao` | da Capacidade de geração, só unidades ativas (sem desativação passada); `potencias_unidades_mw` é a potência de cada unidade, separada por `;`, na ordem do número da unidade; `entrada_operacao` é a da primeira unidade ativa |
| `cod_usina`, `nom_reservatorio`, `id_reservatorio` | dos Reservatórios, pelo CEG (`cod_resplanejamento`, nome, `res_id`); vazios sem linha nos Reservatórios |
| `cobertura_resumo` | o melhor nível entre os conjuntos de série do tipo (`proprio`, `conjunto`, `agregado`, `ausente`) |
| `divergencias` | o tipo do ONS diferente do tipo do CEG; a potência autorizada diferente da soma das unidades ativas em mais de 0,1 MW |

O perfil de cada usina é achado pelo CEG em `usinas/*/perfil.toml` na hora de cada comando, não guardado no catálogo.

#### `conjuntos.csv`

A Composição dos conjuntos inteira, uma linha por usina e relação (`catalogo_usinas.montar_conjuntos`):

| Coluna | Conteúdo |
|---|---|
| `id_conjunto`, `nom_conjunto` | do ONS (`id_ons_conjunto`, `nom_conjunto`) |
| `ceg`, `id_ons_usina`, `nom_usina` | usina membro |
| `tipo` | pelo CEG da usina membro |
| `tipo_ons` | `id_tipousina` publicado, só para conferência |
| `inicio`, `fim` | datas da relação, `AAAA-MM-DD`; vazio ou data sentinela = vigente |
| `estado`, `subsistema` | do ONS (`estad_id`, `id_subsistema`) |

#### `cobertura.csv`

Uma linha por usina (linha com CEG de um dos sete tipos) e conjunto de série do registro que serve ao tipo; nas restrições, a variante do tipo (decisão técnica D21).

| Coluna | Conteúdo |
|---|---|
| `ceg` | usina |
| `conjunto_ons` | chave do registro (seção 6) |
| `nivel` | `proprio`, `conjunto`, `agregado` ou `ausente` |
| `identificador` | coluna e valor usados (`id_ons=...`, `ceg=...`, `cod_usina=...`, `cod_exibicaousina=...;...`, `cod_usinaplanejamento=...;...`) |
| `linhas`, `linhas_sem_valor` | contagens no arquivo verificado |
| `arquivo`, `publicacao` | arquivo e data de publicação usados na verificação |

#### `planejamento.csv` e `programacao.csv`

| Arquivo | Colunas |
|---|---|
| `planejamento.csv` | `ceg`, `codigo` (número; inteiro quando inteiro), `primeiro_mes`, `ultimo_mes` (`AAAA-MM`), `nomes_publicados` (só exibição, separados por `; `), `arquivos` (arquivos do despacho em que aparece) |
| `programacao.csv` | `codigo_exibicao`, `id_usina_ou_conjunto` (vazio sem ligação), `modalidade`, `estado` e `arquivo` (do último dia em que aparece), `primeiro_dia`, `ultimo_dia` (`AAAA-MM-DD`) |

Ligação entre código de programação e usina, sem usar o nome:
- o código igual ao id ONS da usina;
- ou, no conjunto, os códigos que começam pelo id do conjunto sem o prefixo `CJU_` (`MSCAO-9764` para `CJU_MSCAO`);
- sempre com os ids sem os espaços das pontas (o cadastro do ONS publica "CEUFM ");
- nos demais casos, sem ligação: o rascunho deixa o campo pendente e lista os códigos do estado. A São Domingos, por exemplo, tem o código `PRUHSD`, sem ligação com o id `MSUHSD`.

#### `agregados.csv`

Os agregados de cada estado, por mês, nos últimos 12 meses completos (`MESES_AGREGADOS_CATALOGO`), escolhidos pela modalidade publicada (`MODALIDADES_AGREGADAS_GERACAO`), nunca pelo nome ou pelo id; um valor por hora em cada grupo (o último publicado) e as horas sem registro contadas, como no Tratamento.

| Coluna | Conteúdo |
|---|---|
| `id_estado`, `mes` | estado e mês (`AAAA-MM`) |
| `modalidade` | `Pequenas Usinas (MMGD)`, `Pequenas Usinas (Tipo III)` ou `TIPO III`, como publicada |
| `tipo_ons` | `nom_tipousina` publicado |
| `grupo` | `nom_usina` publicado (só exibição) |
| `energia_mwh`, `horas`, `horas_ausentes` | soma, horas com valor e horas sem registro |
| `previsao` | verdadeiro nas modalidades Tipo III, cujo valor é previsão do ONS (`MODALIDADES_PREVISAO_GERACAO`) |
| `arquivo` | arquivo de geração de origem |

#### Listagem

Na saída padrão, as usinas do filtro, ordenadas por estado, tipo e nome, com as colunas `UF`, `TIPO`, `USINA` (40 caracteres), `CEG`, `ID ONS`, `MODALIDADE`, `MW` (potência autorizada), `CONJUNTO`, uma por conjunto de série (`EVT`, `IND`, `PRG`, `DSP`, `HID`, `GER`, `DES`, `CVU`, `FC`, `RDT`, `RRZ`, com `P` próprio, `C` conjunto, `A` agregado, `-` ausente e espaço quando o conjunto não serve ao tipo) e `PERFIL` (o slug, quando há perfil com o CEG); no fim, a linha `Por tipo: <tipo> <n>, …`.

### 2.6 Rascunho do perfil (`usinas/<slug>/perfil.toml`)

Gravado pelo comando `perfil` (`src/coleta/perfil_rascunho.py`) só quando nenhum perfil tem o CEG, por `gravar_bytes`, sem `.bak`, e lido de novo como TOML. O conteúdo e a ordem dos campos estão no [contrato do perfil](contracts/perfil-usina.md), seção "Rascunho": cabeçalho com a data de montagem do catálogo; `[usina]` com `situacao = "rascunho"` e `pendentes`; `[identificacao]`, com os códigos de programação e os períodos deles em comentário; `[[identificacao.membros]]`; `[[identificacao.planejamento]]`; `[cobertura]`; `[parametros]`; `[parametros.fontes]`; e `[analises]` onde há EVT. Cada valor traz a origem em comentário (o conjunto do ONS e a data de publicação do arquivo usado no catálogo); cada pendente é uma linha comentada, com o campo da fonte. O log informa os campos preenchidos com dados do ONS e os pendentes.

## 3. Objetos em memória e entre etapas

A Coleta não grava objeto serializado (pickle); o formato dos seus arquivos é identificado por `versao_formato` = 2 no `etapa.json` (`pipeline.VERSAO_FORMATO`).

### 3.1 Perfil da usina (`src/comum/perfil.py`)

Dataclasses imutáveis, montadas por `carregar_perfil`:

| Classe | Campos |
|---|---|
| `Perfil` | `usina: Usina`, `identificacao: Identificacao`, `parametros: Parametros`, `analises: Analises` ou `None` (só onde há EVT), `textos: Textos`, `arquivo: Path`, `cobertura` (dicionário chave → nível ou lista; vazio na UHE sem a tabela) |
| `Usina` | `slug`, `nome`, `nome_curto`, `estado`, `tipo`, `modalidade` (texto); `inicio_operacao_comercial` (int); `situacao` (`conferido` por padrão); `pendentes` (tupla de texto); `subsistema` (texto ou `None`) |
| `Identificacao` | `cod_usina` (int ou `None`); `nome_ons`, `id_ons`, `id_reservatorio`, `id_conjunto` (texto ou `None`); `ceg` (texto); `cod_programacao` (o primeiro dos códigos); `codigos_programacao` (tupla); `planejamento` (tupla de `Planejamento`); `membros` (tupla de `Membro`) |
| `Planejamento` | `codigo` (int), `inicio` (`AAAA-MM`), `fim` (`AAAA-MM` ou vazio = vigente) |
| `Membro` | `id_ons`, `ceg`, `inicio` (`AAAA-MM-DD`), `fim` (`AAAA-MM-DD` ou vazio = vigente) |
| `Parametros` | `potencia_instalada_mw` (float); `unidades_geradoras` (int); `potencia_unitaria_mw`, `engolimento_nominal_ug_m3s`, `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` (float ou `None`); `tipo_turbina`, `combustivel` (texto ou `None`); `potencias_unidades_mw` (tupla de float); `fontes: FontesParametros` |
| `FontesParametros` | `geral` (texto); `garantia_fisica`, `inicio_operacao_comercial`, `ip_teif` (texto ou `None`) |
| `Analises` | `vertimento_minimo_m3s` (float); `faixas_geracao_mw` (tupla de float); `descricao_vertimento_minimo` (texto ou `None`); `fontes: FontesAnalises` |
| `FontesAnalises` | `vertimento_minimo` (texto ou `None`) |
| `Textos` | `ressalva_volume_util` (texto ou `None`) |

Valores derivados (propriedades e métodos de `Perfil`; o perfil não os traz):

| Valor | Tipos | Cálculo |
|---|---|---|
| `engolimento_maximo_m3s` | hidrelétricas com EVT ou hidrologia | `unidades_geradoras` × `engolimento_nominal_ug_m3s` |
| `potencia_autorizada_esperada_mw` | todos | `potencia_instalada_mw` |
| `disponibilidade_referencia` | com IP e TEIF de referência | (1 − `ip_referencia`) × (1 − `teif_referencia`) |
| `produtividade_nominal_mw_m3s` | hidrelétricas com EVT ou hidrologia | 1000 × 9,81 × (`queda_bruta_m` − `perda_hidraulica_m`) × `rendimento_turbina_gerador` / 10⁶ |
| `plena_carga_mw` | todos | `FRACAO_PLENA_CARGA` (0,90) × `potencia_instalada_mw` |
| `limite_potencia_mw` | todos | `potencia_instalada_mw` × (1 + `TOLERANCIA_LIMITES_FISICOS`), com tolerância de 0,05 |
| `limite_vazao_turbinavel_m3s` | hidrelétricas com EVT ou hidrologia | `engolimento_maximo_m3s` × (1 + 0,05) |
| `limites_fisicos_superiores` | hidrelétricas com EVT | dicionário da validação física do Tratamento: `val_geracao`, `val_disponibilidade`, `val_folgadegeracao` e `val_energiavertidaturbinavel` → `limite_potencia_mw`; `val_vazaoturbinada` e `val_vazaovertidaturbinavel` → `limite_vazao_turbinavel_m3s` |
| `potencias_das_unidades_mw` | todos | a lista do perfil ou, sem ela, a potência unitária repetida pelas unidades |
| `codigos_planejamento_em(data)` | UTE e UTN | códigos de planejamento vigentes no mês da data, na ordem do perfil |

Nos tipos sem os valores hidráulicos, pedir um valor derivado deles levanta `ValueError` com o campo e o tipo; sem IP e TEIF de referência, a `disponibilidade_referencia` também.

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
| `Regra` | `src/coleta/registro.py` | `coluna`, `valor`, `modo`: `igual` (texto normalizado ou número), `contem` (texto normalizado), `em` (um dos números de `valor`) ou `codigo_no_periodo` (`valor` com (código, início `AAAA-MM`, fim `AAAA-MM` ou vazio): o número da linha é um dos códigos e o instante dela está no período dele) |
| `DescricaoConjunto` | idem | `pacote`, `pasta`, `identificador` (`Regra`), `conferencias` (tupla de `Regra`), `colunas_valor`, `convencao_hora` (`inicio` ou `fim`, aplicada pelo Tratamento), `formatos_preferidos` (`PARQUET`, `CSV`), `filtro_parquet`, `chave`, `tipos`, `nivel`, `resolucao`, `referencia`, `variantes`, `colunas_texto`, `coluna_instante` (padrão `din_instante`; no CVU, `dat_iniciosemana`) e `avisar_colunas_ausentes`; `colunas_leitura` junta as colunas a ler |
| `EntradaRegistro` | idem | uma entrada do registro (seção 6): `chave`, `pacotes` ((pacote, pasta), na ordem de coleta), `tipos`, `niveis`, `resolucao`, `referencia`, `variantes`, `descricao` (função que monta a `DescricaoConjunto` com o perfil), `so_catalogo`, `campo_usina`; `na_cobertura` diz se o conjunto entra na `[cobertura]` |
| `Escolha` | `src/coleta/serie_referencia.py` | a série de referência: `conjunto` (chave do registro), `niveis` (`usina`, `conjunto` ou os dois) e `motivo` (a linha da tabela da seção 7.1) |
| Falha de download | `sincronizar_*` | dicionário no formato da linha de auditoria: `arquivo` e `mensagem`, mais `status` (`FALHA`), `formato` e, conforme o conjunto, `periodo`, `dia` ou `conjunto`; na auditoria, recebe `obtido = False` |
| `_Coleta` | `src/coleta/etapa.py` | estado de uma execução: perfil, opções, pasta, início (UTC), arquivos gravados, resumo, datas de obtenção por conjunto, conjuntos da usina (`entradas`) e pacotes da variante do tipo, série de referência escolhida, complemento horário, composição do conjunto, série do conjunto (para o tipo publicado) e período |
| `Cadastral` | `src/coleta/catalogo_usinas.py` | `pacote`, `pasta` e `formatos` de um cadastral (`CADASTRAIS`: `cadastro`, `composicao`, `capacidade`, `reservatorio`) |
| `CadastralNaoObtido` | idem | exceção com `pacote` e `motivo`: cadastral sem recurso no catálogo, com download sem sucesso ou sem arquivo local (código 2) |
| `Serie` | idem | conjunto de série verificado na cobertura: `chave`, `formatos`, `prefixo` (só a EVT, na raiz de `data/raw/`) e `variante` (nas restrições); `SERIES` traz as onze chaves, as restrições uma vez por variante |
| `Leituras` | idem | os quatro cadastrais lidos, o arquivo e a publicação de cada um, o arquivo mais recente de cada série (com a publicação e a tabela), `planejamento` e os códigos de programação de todos os arquivos |
| `Catalogo` | idem | as seis tabelas de `data/catalogo/` e o conteúdo de `catalogo.json` |

## 4. Manifesto da etapa (`etapa.json`)

### 4.1 Campos comuns às cinco etapas

Gravado por `pipeline.executar_etapa` em `data/usinas/<slug>/<etapa>/etapa.json` (no relatório, `reports/<slug>/etapa.json`): JSON em UTF-8, indentação 1, troca atômica pelo temporário `etapa.json.tmp`, sem `.bak`.

| Campo | Tipo | Conteúdo |
|---|---|---|
| `etapa` | texto | `coleta`, `tratamento`, `conferencia`, `analises` ou `relatorio` |
| `usina` | texto | slug |
| `versao_formato` | inteiro | `VERSAO_FORMATO[etapa]`, atualmente Coleta 2, Tratamento 2, Conferência 2, Análises 3 e Relatório 1. Sobe quando muda um arquivo que a etapa já grava, ou quando a etapa seguinte passa a exigir um arquivo novo; arquivo novo opcional não muda o formato |
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

**Pré-requisito** (`etapa_anterior_concluida`): a partir do Tratamento, a etapa só roda se o `etapa.json` da anterior existe, é legível, tem `status` `concluida` (com qualquer `codigo_saida`) e o `versao_formato` atual. Senão, sai com 5 antes de gravar qualquer arquivo. A Coleta no formato 1 é recusada pelo Tratamento.

### 4.3 Resumo da Coleta

```json
{
  "sem_portal": false,
  "forcar_download": false,
  "conjuntos": { "<chave>": { "<15 campos abaixo>": "..." } },
  "tipo": "UHE",
  "modalidade": "TIPO II-A",
  "trechos": 0,
  "linhas_usina_sem_valor": 0,
  "conjuntos_nao_aplicaveis": [],
  "periodo": { "inicio": "AAAA-MM-DD HH:MM:SS", "fim": "AAAA-MM-DD HH:MM:SS" },
  "serie_referencia": { "conjunto": "evt", "identificador": "cod_usina=153", "inicio": "...", "fim": "...",
                        "arquivos_varridos": 43, "motivo": "UHE, PCH ou CGH com Energia Vertida Turbinável" },
  "dicionarios": { "<resultado>": 0 }
}
```

- `sem_portal`: a opção da execução; `forcar_download`: a opção efetiva (`false` com `--sem-portal`).
- `tipo` e `modalidade`: do perfil.
- `conjuntos`: uma entrada por conjunto tratado até o fim ou até a parada, montada por `etapa.resumo_conjunto` a partir da auditoria e dos manifestos das pastas do conjunto. As chaves são `energia-vertida-turbinavel`, `indicadores` (os quatro conjuntos juntos), `programacao_diaria`, `modalidade-usina` e, nos demais, o id do conjunto no catálogo (`disponibilidade_usina`, `dados_hidrologicos_ho`, `geracao-usina-2`, `usina_conjunto`, `capacidade-geracao`, `geracao-termica-despacho-2`, `cvu-usitermica`, `cmo-semanal`, `fator-capacidade-2` e o pacote da variante de cada restrição).
- `periodo`: primeiro e último instante da série de referência; ausente se a série parou a coleta.
- `serie_referencia`: seção 7.1.
- `trechos`: quantidade de linhas de `trechos.csv` (0 na hidrelétrica com EVT).
- `conjuntos_nao_aplicaveis`: chaves de conjuntos de série do tipo que a `[cobertura]` não manda obter (`agregado` ou `ausente`); vazia sem `[cobertura]`.
- `linhas_usina_sem_valor`: na série de referência do conjunto, com o id ONS no perfil, as linhas próprias da usina sem valor na Geração por usina, no período; com elas, `linhas_usina_sem_valor_periodo` (`inicio` e `fim`).
- Na usina em conjunto: `composicao_da_usina` (lista de `{"inicio", "fim"}` da usina na composição; vazio = sem limite) e `capacidade_membros` (`usinas`, `com_unidades`, `linhas_so_identificador`).
- Com `[[identificacao.membros]]`: `membros_restricao` (id ONS → linhas extraídas da restrição com detalhe).
- `dicionarios`: quantidade de linhas de `dicionarios.csv` por `resultado_ultima_obtencao`; presente nas execuções com código 0 ou 2 (com código 1, o resumo é só `{"erro": …}` ou o que foi montado antes da recusa).

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

Exemplo (na Bandeirante, Coleta de 22/10/2026): `"serie_referencia": {"conjunto": "geracao", "identificador": "id_ons=CJU_MSCAO", "inicio": "2019-08-22 00:00:00", "fim": "2026-10-20 23:00:00", "arquivos_varridos": 80, ...}`, `"trechos": 3`, `"linhas_usina_sem_valor": 4152`, `"linhas_usina_sem_valor_periodo": {"inicio": "2026-05-01 00:00:00", "fim": "2026-10-20 23:00:00"}`, `"conjuntos_nao_aplicaveis": ["evt", "indicadores", "disponibilidade", "hidrologia"]`, `"composicao_da_usina": [{"inicio": "2019-08-22 00:00:00", "fim": ""}]`, `"capacidade_membros": {"usinas": 9, "com_unidades": 9, "linhas_so_identificador": 0}`.

## 5. Regras, estados e validações

### 5.1 Perfil da usina: campos e validação

Regras gerais de `validar_perfil`:
- TOML em UTF-8; arquivo ausente ou ilegível é um problema (e o único da mensagem);
- "inteiro" aceita só inteiro do TOML; "real" aceita inteiro ou real; booleano nunca é número; "texto" exige texto não vazio (sem contar espaços);
- campo opcional ausente é aceito; presente, segue as regras de texto;
- o tipo usado nas regras é o do prefixo do CEG, quando o CEG é válido; senão, o de `usina.tipo`;
- a exigência de cada campo por tipo vem de `src/comum/perfil_campos.py` (tabela abaixo): `O` lido como obrigatório; `C` obrigatório quando um dos conjuntos indicados tem, na `[cobertura]`, um dos níveis indicados, e lido se presente; `opcional` lido se presente; `—` recusado se presente;
- as faixas e as coerências só são conferidas quando os campos envolvidos têm o tipo certo;
- campos não previstos são ignorados;
- todos os problemas vão numa só mensagem (código 4). Os textos de cada mensagem estão em [contracts/perfil-usina.md](contracts/perfil-usina.md).

| Campo | Tipo | Validação |
|---|---|---|
| `usina.slug` | texto | `^[a-z0-9_]+$`; igual ao nome da pasta em `usinas/`; diferente de `carteiras` (`SLUG_RESERVADO`) |
| `usina.nome`, `usina.nome_curto` | texto | não vazio |
| `usina.estado` | texto | `^[A-Z]{2}$` |
| `usina.inicio_operacao_comercial` | inteiro | de 1900 até o ano atual |
| `usina.tipo` | texto | um de `TIPOS_USINA`; igual ao prefixo do CEG |
| `usina.modalidade` | texto | um de `MODALIDADES_COM_PERFIL`; `MODALIDADES_TIPO_III` recusadas |
| `usina.situacao` | texto, opcional | `rascunho` ou `conferido` (ausente = `conferido`); `rascunho` sempre recusado, com os pendentes |
| `usina.pendentes` | lista de textos não vazios, opcional | vazia ou ausente quando `conferido` |
| `usina.subsistema` | texto | um de `SUBSISTEMAS` (`SE`, `S`, `NE`, `N`) |
| `identificacao.ceg` | texto | `^(UHE\|PCH\|CGH\|UTE\|UTN\|EOL\|UFV)\.[A-Z]{2}\.[A-Z]{2}\.\d{6}-\d\.\d{2}$` |
| `identificacao.cod_programacao` ou `codigos_programacao` | texto ou lista de textos | um dos dois, nunca os dois; a lista não vazia; obrigatório só com a Programação diária coletada (sem a `[cobertura]`, na UHE, ou com a programação `proprio` ou `conjunto`); com a programação `ausente`, um código informado é aceito e não é usado |
| `identificacao.cod_usina` | inteiro | > 0 |
| `identificacao.nome_ons` | texto | `^[A-Z0-9 .\-/]+$` (maiúsculas sem acento) |
| `identificacao.id_ons`, `id_reservatorio`, `id_conjunto` | texto | não vazio |
| `[[identificacao.planejamento]]` | lista de tabelas | `codigo` inteiro > 0; `inicio` `AAAA-MM`; `fim` `AAAA-MM` ≥ `inicio` ou vazio; o mesmo código sem períodos sobrepostos |
| `[[identificacao.membros]]` | lista de tabelas | `id_ons` não vazio; `ceg` no padrão; `inicio` `AAAA-MM-DD`; `fim` `AAAA-MM-DD` ou vazio |
| `[cobertura]` | tabela | chaves de `registro.chaves_da_cobertura(tipo)`; valor em `COBERTURAS` ou a lista `["proprio", "conjunto"]` (em qualquer ordem); obrigatória fora da UHE |
| `parametros.potencia_instalada_mw` | real | > 0 |
| `parametros.unidades_geradoras` | inteiro | ≥ 1 |
| `parametros.potencia_unitaria_mw` | real | > 0; \|unitária × unidades − instalada\| ≤ `TOLERANCIA_POTENCIA_PERFIL_MW` (0,1 MW); na UHE, sempre esta |
| `parametros.potencias_unidades_mw` | lista de números | fora da UHE, no lugar da unitária (nunca as duas); um valor > 0 por unidade; \|soma − instalada\| ≤ 0,1 MW |
| `parametros.tipo_turbina`, `combustivel` | texto | não vazio |
| `parametros.engolimento_nominal_ug_m3s` | real | > 0 |
| `parametros.garantia_fisica_mwmed` | real | > 0 e ≤ potência instalada |
| `parametros.ip_referencia`, `teif_referencia` | real | 0 ≤ x < 1 |
| `parametros.queda_bruta_m` | real | > 0 |
| `parametros.perda_hidraulica_m` | real | ≥ 0 e < queda bruta |
| `parametros.rendimento_turbina_gerador` | real | 0 < x ≤ 1 |
| `parametros.vazao_remanescente_m3s` | real | ≥ 0 |
| `parametros.fontes.geral` | texto | obrigatório em todos os tipos |
| `parametros.fontes.garantia_fisica` | texto | obrigatório quando há garantia física; senão, opcional |
| `parametros.fontes.inicio_operacao_comercial`, `parametros.fontes.ip_teif` | texto | opcional; se presente, não vazio |
| `analises.vertimento_minimo_m3s` | real | ≥ 0 (0 = sem vertimento contínuo) |
| `analises.faixas_geracao_mw` | lista de números | não vazia; estritamente crescente; cada valor > `LIMIAR_GERACAO_PARADA_MW` (1 MW) e < `FRACAO_PLENA_CARGA` (0,90) × potência instalada |
| `analises.descricao_vertimento_minimo`, `analises.fontes.vertimento_minimo` | texto | opcional; se presente, não vazio |
| `textos.ressalva_volume_util` | texto | opcional; se presente, não vazio |

Obrigatórios em todos os tipos: `usina.slug`, `nome`, `nome_curto`, `estado`, `inicio_operacao_comercial`, `tipo` e `modalidade`; `identificacao.ceg` e o código ou a lista de códigos de programação; `parametros.potencia_instalada_mw`, `unidades_geradoras`, a potência das unidades e `parametros.fontes.geral`. Exigência dos demais (`perfil_campos.CAMPOS`, por grupo de tipos):

| Campo | UHE | PCH e CGH | UTE e UTN | EOL e UFV |
|---|---|---|---|---|
| `identificacao.id_ons` | O | C: `geracao` ou `disponibilidade` com `proprio` | O | C: `geracao`, `fator_capacidade`, `restricao_detalhe` ou `restricao_razao` com `proprio` |
| `identificacao.cod_usina`, `nome_ons` | O sem a `[cobertura]`; C: `evt` ou `hidrologia` | C: `evt` ou `hidrologia` com `proprio` ou `conjunto` | — | — |
| `identificacao.id_reservatorio` | O sem a `[cobertura]`; C: `hidrologia` | C: `hidrologia` | — | — |
| `identificacao.id_conjunto` | — | C: `geracao`, `fator_capacidade` ou `restricao_razao` com `conjunto` | idem | idem |
| `identificacao.planejamento` | — | — | C: `despacho` ou `cvu` | — |
| `identificacao.membros` | — | opcional | — | opcional |
| `usina.subsistema` | opcional | opcional | C: `cvu` | opcional |
| hidráulicos (`tipo_turbina`, `engolimento_nominal_ug_m3s`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s`) | O sem a `[cobertura]`; C: `evt` ou `hidrologia` | C: `evt` ou `hidrologia` | — | — |
| `parametros.garantia_fisica_mwmed` | O sem a `[cobertura]`; C: `evt` | opcional | opcional | opcional |
| `parametros.ip_referencia`, `teif_referencia` | O sem a `[cobertura]`; C: `evt` | opcional | opcional | — |
| `parametros.combustivel` | — | — | O | — |
| `[analises]` | O sem a `[cobertura]`; C: `evt` | C: `evt` | — | — |

**Situação do perfil**:

```text
(sem perfil) --perfil --ceg--> rascunho --fiscal confere e completa--> conferido
conferido --perfil --ceg (de novo)--> conferido, sem mudança: código 0 sem diferença; 6 com diferença (só mostra)
```

Em `rascunho`, toda etapa recusa o perfil (código 4). Para passar a `conferido`, o fiscal troca `situacao`, preenche os pendentes com a fonte e esvazia `pendentes`.

### 5.2 Identificação da usina em cada conjunto

`conjuntos._corresponde` (indicadores e motor comum): coluna ausente → nenhuma linha confere; modo `em` ou `codigo_no_periodo` → número da coluna (`numero_publicado`) entre os códigos (no período deles); valor do perfil inteiro ou real → `pd.to_numeric(coluna) == valor`; texto → igualdade ou "contém" (sem expressão regular) entre textos normalizados por `registro.normalizar_texto` (NFKD sem acento, sem espaços nas pontas, maiúsculas).

| Conjunto | Identificador | Conferência | Como compara | Linhas só em parte |
|---|---|---|---|---|
| EVT | `cod_usina` = `cod_usina` | `nom_reservatorio` contém `nome_ons` | código como texto (`strip`) igual a `str(cod_usina)`; nome normalizado, uma vez por valor distinto | `registros_codigo_sem_nome`, `registros_nome_sem_codigo` |
| Indicadores por UG | `ceg` = `ceg` | `id_usina` = `id_ons` | `_corresponde` | `linhas_so_identificador`, `linhas_so_conferencia` |
| Taxas TEIFa e TEIP e parâmetros | `cod_ceg` = `ceg` | não há | `_corresponde` | não se aplica (vazio) |
| Programação diária | `cod_exibicaousina` entre `codigos_programacao` | `id_estado` = `estado` e, nas hidrelétricas, `nom_usina` contém `nome_ons` | código, estado e nome normalizados; antes, o pyarrow mantém só as linhas com o estado ou com os valores publicados do código cuja forma normalizada confere | `linhas_codigo_sem_conferencia`, `linhas_so_conferencia` |
| Disponibilidade por usina | `id_ons` = `id_ons` | `ceg` = `ceg`, e `id_estado` = `estado` | `_corresponde` | `linhas_so_identificador`, `linhas_so_conferencia` |
| Dados hidrológicos horários | `cod_usina` = `cod_usina` | `nom_reservatorio` contém `nome_ons`, e `id_reservatorio` = `id_reservatorio` | `_corresponde` (código como número) | idem |
| Geração por usina, da usina | `id_ons` = `id_ons` | `ceg` = `ceg`, e `id_estado` = `estado` | `_corresponde`, depois do filtro do Parquet `id_ons` ou `ceg` em (valor do perfil, forma normalizada) | idem |
| Geração por usina, do conjunto | `id_ons` = `id_conjunto` | `id_estado` = `estado` | idem, com o filtro `id_ons` = id do conjunto | idem |
| Geração térmica por motivo de despacho | `ceg` = `ceg` | `cod_usinaplanejamento` entre os códigos do perfil, no período de cada um (pelo instante da linha) | código como número; filtro do Parquet pelo CEG ou pelos códigos | idem |
| CVU das usinas térmicas | `cod_usinaplanejamento` entre os códigos do perfil (`em`) | `id_subsistema` = `subsistema` | código como número | idem |
| CMO semanal | `id_subsistema` = `subsistema` | não há | `_corresponde` | só identificador; `linhas_so_conferencia` = 0 |
| Fator de capacidade; restrição com a razão | da usina: `id_ons` = `id_ons`; do conjunto: `id_ons` = `id_conjunto` | da usina: `ceg` = `ceg`; do conjunto: `id_estado` = `estado` | `_corresponde`, depois do filtro do Parquet | idem |
| Restrição com detalhe (e membros) | `id_ons` = `id_ons` (do membro) | `ceg` = `ceg` (do membro) | idem | idem |
| Modalidade das usinas | `ceg` = `ceg` | `id_ons` = `id_ons` e `id_estado` = `estado`: só contados, não excluem a linha | textos normalizados | `linhas_so_identificador`, `linhas_so_conferencia`; homônimos: nome com `nome_ons` (ou `nome_curto`) e outro CEG |
| Composição dos conjuntos | `id_ons_conjunto` = `id_conjunto` | `estad_id` = `estado` | textos normalizados | `linhas_so_identificador` |
| Capacidade de geração | `ceg` = `ceg` | `id_estado` = `estado` | textos normalizados | `linhas_so_identificador` |
| Capacidade das usinas do conjunto | `ceg` entre os CEG da composição no período | `id_subsistema` = `subsistema` da linha da usina na composição | textos normalizados | `linhas_so_identificador` |

Colunas obrigatórias na leitura (sem elas, o arquivo fica `FALHA`): EVT, `cod_usina` e `nom_reservatorio`; indicadores por UG, `ceg` e `id_usina`; taxas e parâmetros, `cod_ceg`; programação, as seis colunas lidas; motor comum, o identificador, a coluna do instante e as colunas de conferência declaradas ("coluna de conferência ausente: <coluna>"); cadastro, `nom_usina`, `ceg`, `id_ons` e `id_estado`. No motor comum, as colunas de valor e de texto que faltam num arquivo ficam vazias; nos conjuntos com `avisar_colunas_ausentes` (fator de capacidade e restrições), a ausência vai para a mensagem da auditoria e para o log.

### 5.3 Situações e enumerações

| Onde | Valores |
|---|---|
| Tipo da usina (`TIPOS_USINA`) | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL`, `UFV`; no catálogo, também `conjunto` (linha de conjunto do cadastro) e `outro` |
| Grupos de tipos | hidrelétricas (`UHE`, `PCH`, `CGH`), térmicas (`UTE`, `UTN`), renováveis (`EOL`, `UFV`) |
| Modalidade | `TIPO I`, `TIPO II-A`, `TIPO II-B`, `TIPO II-C` (com perfil); `TIPO III`, `TIPO III (EM DIT)` (só agregado, sem perfil) |
| Nível do dado | `usina`, `conjunto`, `agregado`; o CMO do subsistema é `agregado` |
| Cobertura | `proprio`, `conjunto`, `agregado`, `ausente`; no perfil, também a lista `["proprio", "conjunto"]` |
| Situação do perfil | `rascunho`, `conferido` |
| Subsistema | `SE`, `S`, `NE`, `N` |
| Resolução | `horaria`, `semi_horaria` (inclusive os 48 patamares da programação), `semanal`, `mensal_anual`, `estatica` |
| Razão da restrição (`cod_razaorestricao`, como publicada) | `REL`, `CNF`, `ENE` ou vazia |
| `status` das auditorias | `PROCESSADO` (com linhas da usina), `SEM_REGISTROS` (lido, sem linhas da usina), `FALHA` (não obtido, vazio, corrompido ou sem coluna obrigatória); na programação, também `INCOMPLETO` |
| `resultado_ultima_obtencao` dos dicionários | `NOVO`, `INALTERADO`, `ALTERADO`, `FALHA`; no registro, também `NAO_PUBLICADO` (formato ausente do catálogo na última consulta) e `NAO_OBTIDO` (conjunto nunca consultado) |
| `origem_registro` do manifesto | `DOWNLOAD`, `ARQUIVO_EXISTENTE` |
| `tipo_match` da EVT | `CODIGO_E_NOME` |
| `status` do `etapa.json` | `concluida`, `falha`, `desatualizada` |

### 5.4 Cache, versões e falhas

- **Reaproveitamento** (`_is_local_copy_current`, sem `--forcar-download`): arquivo local não vazio e, com registro no manifesto, `tamanho_bytes` igual e `ultima_modificacao` igual à do catálogo (só o tamanho, se o catálogo não traz a publicação); sem registro, tamanho igual ao publicado (qualquer tamanho, se o catálogo não traz o `size`), e a cópia é registrada como `ARQUIVO_EXISTENTE`. Nos demais casos, novo download.
- **Recursos repetidos**: em todos os conjuntos, fica o recurso com publicação e, em empate, o maior; a quantidade de descartados vai para `recursos_duplicados_catalogo` do manifesto e, no motor comum, da auditoria.
- **Download**: até 3 tentativas, com espera de 2 s e 4 s e limite de 60 s cada, para `<arquivo>.<id do recurso>.part`; tamanho baixado diferente do publicado gera aviso. Esgotadas as tentativas, o arquivo vira `FALHA` na auditoria (`obtido = False`, com a mensagem), a cópia local fica intacta e é lida se existir.
- **Catálogo**: até 3 tentativas, com as mesmas esperas, em qualquer erro de rede ou de leitura (`OSError`, `http.client.HTTPException`), de JSON (`ValueError`) e na resposta com `success` falso. Catálogo inacessível depois delas levanta `DownloadError` (código 1), exceto o dos dicionários, que vira `FALHA` no registro.
- **Cadastro**: sem recurso CSV no catálogo, a coleta registra erro no log e lê a cópia local; sem cópia local, a ficha fica vazia (código 2).
- **Composição e Capacidade**: sem recurso no catálogo, download sem sucesso ou, com `--sem-portal`, arquivo local ausente: `CadastralNaoObtido`, uma linha `FALHA` na auditoria e código 2.
- **Leitura**: arquivo vazio, corrompido ou sem coluna obrigatória → `FALHA`, com o motivo, e a leitura segue nos demais. No CSV vazio da EVT, o motivo é "arquivo vazio"; o CSV só com o cabeçalho fica `SEM_REGISTROS`.
- **Instantes**: na EVT, o registro sem `din_instante` é descartado na consolidação; no motor comum, a linha da usina com instante não interpretável conta em `linhas_usina` e em `valores_invalidos` e fica fora do extraído.
- **Série de referência**: sem nenhuma hora com valor, ou com a usina fora da composição do conjunto declarado, a auditoria da série é gravada e a coleta termina com 2; sem série possível na cobertura, código 1, sem gravar extraído.

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
| `TIPOS_USINA`, `MODALIDADES_COM_PERFIL`, `MODALIDADES_TIPO_III`, `SUBSISTEMAS`, `COBERTURAS` | seção 5.3 | idem |
| `TOLERANCIA_POTENCIA_PERFIL_MW` | 0,1 MW | idem (validação do perfil e divergência de potência no catálogo) |
| `LIMIAR_GERACAO_PARADA_MW`, `FRACAO_PLENA_CARGA` | 1,0 MW; 0,90 | idem (faixas de geração do perfil) |
| `TOLERANCIA_LIMITES_FISICOS` | 0,05 | idem (valores derivados do perfil) |
| `MESES_AGREGADOS_CATALOGO` | 12 | idem (panorama dos agregados) |
| `MODALIDADES_AGREGADAS_GERACAO` | `PEQUENAS USINAS (TIPO III)`, `PEQUENAS USINAS (MMGD)`, `TIPO III` | idem |
| `MODALIDADES_PREVISAO_GERACAO` | `PEQUENAS USINAS (TIPO III)`, `TIPO III` | idem |
| `PREFIXO_CONJUNTO` | `CJU_` | idem |
| `TIPOS_ONS` | tipo publicado pelo ONS → tipos do CEG que ele admite | idem |
| `DATAS_SENTINELA` | `9999-12-31`, `2999-12-31`, `0001-01-01` e as mesmas em `DD/MM/AAAA` | idem |
| `DIRETORIO_VERSOES_ANTERIORES` | `_versoes_anteriores` | `src/coleta/catalogo.py` |
| `DOWNLOADS_SIMULTANEOS` | 8 | `src/coleta/conjuntos.py` e `src/coleta/programacao.py` |
| `FORMATOS_DICIONARIO`, `CHAVE_CONSULTA` | (`PDF`, `JSON`); `_consulta` | `src/coleta/dicionarios.py` |
| `CHAVES_SEM_COBERTURA` | `evt`, `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao`, `cadastro` | `src/coleta/registro.py` |
| `INICIO_VARREDURA` | 1990-01-01 | `src/coleta/serie_referencia.py` |
| `VERSAO_FORMATO_CATALOGO`, `PASTA_TEMPORARIA` | 1; `.gravando` | `src/coleta/catalogo_usinas.py` |
| `SLUG_RESERVADO` | `carteiras` | `src/comum/perfil.py` e `src/coleta/perfil_rascunho.py` |
| `VERSAO_FORMATO` | Coleta 2, Tratamento 2, Conferência 2, Análises 3, Relatório 1 | `src/pipeline.py` |
| `CODIGO_SUCESSO` … `CODIGO_DIFERENCAS` | 0 a 6 | idem |
| `NIVEIS_LOG`, `LOGGERS_PIPELINE` | `DEBUG`, `INFO`, `WARNING`, `ERROR`; `pipeline`, `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio`, `persistencia` | `src/comum/logger.py` |
| `MAXIMO_COPIAS` | 2 | `src/comum/copia_seguranca.py` |

### 5.6 Códigos de saída da Coleta

| Código | `coleta` | `usinas` | `perfil` |
|---|---|---|---|
| 0 | os conjuntos da usina tratados sem `FALHA`, com a série de referência, a ficha cadastral e, na usina em conjunto, a usina na composição | catálogo montado e listado, inclusive com o filtro vazio | rascunho gravado, ou perfil existente sem diferença |
| 1 | catálogo inacessível depois das tentativas, usina sem série de referência na cobertura, falha de gravação (arquivo restaurado), interrupção pelo usuário ou erro inesperado | catálogo do ONS inacessível, falha de gravação, interrupção ou erro inesperado | erro de gravação, perfil existente ilegível, interrupção ou erro inesperado |
| 2 | algum arquivo `FALHA` no conjunto em tratamento (a coleta para nele), nenhuma linha da usina na EVT, série de referência sem hora com valor, usina fora da composição do conjunto declarado, cadastral não obtido, ficha cadastral vazia; ou opção inválida na linha de comando | cadastral não obtido; opção inválida | slug inválido, CEG fora do catálogo, tipo fora dos sete, usina Tipo III ou só com agregado; opção inválida |
| 4 | perfil inválido, inclusive em rascunho | — | — |
| 5 | — | — | catálogo ausente ou em formato antigo |
| 6 | — | — | perfil existente com diferenças em relação ao catálogo |

A tabela completa, comum às cinco etapas, está em [contracts/cli-coleta.md](contracts/cli-coleta.md).

## 6. Registro dos conjuntos do ONS (`src/coleta/registro.py`)

Cada entrada (`EntradaRegistro`) declara o conjunto, e a `DescricaoConjunto` montada com o perfil traz a identificação (seção 3.3). A ordem é a da coleta; os conjuntos da usina são filtrados por `conjuntos_da_usina` (spec, FR-016).

| Chave | Pacote do ONS | Tipos | Níveis | Resolução | Identificador | Conferência | Pode ser série de referência | Leitura |
|---|---|---|---|---|---|---|---|---|
| `evt` | `energia-vertida-turbinavel` | UHE, PCH, CGH | usina | horária | `cod_usina` | nome do reservatório | sim | `evt.py` |
| `indicadores` | os quatro de indicadores e taxas | UHE, PCH, CGH, UTE, UTN | usina | mensal e anual | CEG | id ONS (indicadores por UG) | não | `indicadores.py` |
| `programacao` | `programacao_diaria` | todos | usina, conjunto | semi-horária (48 patamares) | `cod_exibicaousina` entre os códigos do perfil | estado; nas hidrelétricas, também o nome | não | `programacao.py` |
| `disponibilidade` | `disponibilidade_usina` | UHE, PCH, CGH, UTE, UTN | usina | horária | id ONS | CEG, estado | não | motor comum |
| `hidrologia` | `dados_hidrologicos_ho` | UHE, PCH, CGH | usina | horária (hora de fim) | `cod_usina` | nome do reservatório, `id_reservatorio` | não | motor comum |
| `geracao` | `geracao-usina-2` | todos | usina, conjunto | horária | id ONS da usina, ou id do conjunto | CEG e estado (usina) ou estado (conjunto) | sim | motor comum |
| `cadastro` | `modalidade-usina` | todos | usina | estática | CEG | id ONS, estado (só contados) | não | `cadastro.py` |
| `composicao` | `usina_conjunto` | todos (na usina em conjunto) | conjunto | estática | id do conjunto | estado | não | `catalogo_usinas.ler_cadastral` |
| `capacidade` | `capacidade-geracao` | todos | usina | estática | CEG | estado | não | idem |
| `despacho` | `geracao-termica-despacho-2` | UTE, UTN | usina | horária | CEG | código de planejamento do perfil, no período | não | motor comum |
| `cvu` | `cvu-usitermica` | UTE, UTN | usina | semanal | código de planejamento do perfil | subsistema | não | motor comum |
| `cmo` | `cmo-semanal` | UTE, UTN (com `usina.subsistema`) | agregado | semanal | subsistema | — | não | motor comum |
| `fator_capacidade` | `fator-capacidade-2` | EOL, UFV | usina, conjunto | horária | id ONS ou id do conjunto | CEG ou estado | não | motor comum |
| `restricao_detalhe` | `restricao_coff_eolica_detail` (EOL), `restricao_coff_fotovoltaica_detail` (UFV) | EOL, UFV | usina | semi-horária | id ONS | CEG | sim | motor comum |
| `restricao_razao` | `restricao_coff_eolica_usi` (EOL), `restricao_coff_fotovoltaica` (UFV) | EOL, UFV | usina, conjunto | semi-horária | id ONS ou id do conjunto | CEG ou estado | não | motor comum |
| `reservatorio` | `reservatorio` | UHE, PCH, CGH | usina | estática | CEG | — | não | só no catálogo (`so_catalogo`) |

- Os conjuntos estáticos e o CMO não entram na `[cobertura]` (`na_cobertura`); são obtidos sempre que servem ao tipo (a Composição, só com `id_conjunto`; o CMO, só com o subsistema no perfil).
- Sem `[cobertura]` (só na UHE): as chaves de `CHAVES_SEM_COBERTURA`, os dez pacotes da UHE.
- O registro dos dicionários, as datas de obtenção e as abas DICIONARIOS e FONTES de cada usina listam só os conjuntos do tipo e da cobertura dela, na ordem do registro; nas restrições, só a variante do tipo.
- Arquivo novo numa etapa não muda o `VERSAO_FORMATO` dela; só a mudança num arquivo existente, ou a exigência de um arquivo novo pela etapa seguinte, muda.

## 7. Série de referência e trechos

### 7.1 Série de referência (no resumo do `etapa.json` da Coleta)

Escolhida por `serie_referencia.escolher`:

| Situação | Conjunto | Níveis | Identificador | Motivo gravado |
|---|---|---|---|---|
| UHE, PCH ou CGH com a EVT coletada | `evt` | usina | `cod_usina` | "UHE, PCH ou CGH com Energia Vertida Turbinável" |
| geração própria (`geracao = "proprio"`) | `geracao` | usina | id ONS | "geração própria: Geração por usina, pelo id ONS da usina" |
| em conjunto, sem série própria (`geracao = "conjunto"`) | `geracao` | conjunto | id do conjunto | "usina em conjunto, sem série própria: Geração por usina, pelo id do conjunto" |
| mudou de nível (`geracao = ["proprio", "conjunto"]`) | `geracao` | usina e conjunto | id ONS e id do conjunto | "a usina mudou de nível no período: Geração por usina, da usina e do conjunto" |
| EOL ou UFV sem geração própria, com a restrição com detalhe da usina | `restricao_detalhe` | usina | id ONS | "usina em conjunto, com série própria na restrição com detalhe: geração verificada da usina, pelo id ONS" |

| Campo do resumo | Conteúdo |
|---|---|
| `conjunto` | chave do registro |
| `identificador` | coluna e valor (`cod_usina=...` ou `id_ons=...`; com os dois níveis, `id_ons=<usina>;<conjunto>`) |
| `inicio`, `fim` | primeira e última hora (ou semi-hora) com valor |
| `arquivos_varridos` | arquivos distintos na auditoria da série: todos os publicados do conjunto |
| `motivo` | linha da tabela acima que se aplicou |

Na usina em conjunto sem série própria, as horas do conjunto só contam nos intervalos [entrada, saída) da usina em `composicao_conjunto.csv` (`intervalos_da_usina`), gravados no resumo em `composicao_da_usina`.

### 7.2 `trechos.csv` (fora da hidrelétrica com EVT)

Um trecho é um intervalo sem mudança de modalidade, de nível do dado, de composição do conjunto nem de códigos de planejamento (`serie_referencia.trechos`; colunas em `COLUNAS_TRECHOS`).

| Coluna | Conteúdo |
|---|---|
| `trecho` | número, a partir de 1 |
| `inicio`, `fim` | primeira e última hora do trecho, dentro do período |
| `modalidade` | a modalidade publicada na série de referência, hora a hora |
| `id_conjunto` | conjunto do perfil; vazio fora de conjunto |
| `composicao` | CEG das usinas do conjunto no início do trecho, separados por `;` |
| `tipos_composicao` | tipos dessas usinas, pelo CEG, por exemplo `PCH;UTE` |
| `codigos_planejamento` | códigos vigentes (UTE e UTN), separados por `;` |
| `nivel_geracao` | `usina` ou `conjunto` |
| `mostrar` | verdadeiro quando o nível ou a composição difere do trecho anterior ou do seguinte (só esses aparecem no relatório) |

Os cortes caem: em cada mudança da modalidade ou do nível; nas datas de entrada e de saída da composição (à meia-noite); no primeiro dia do mês de início de cada código de planejamento e no primeiro dia do mês seguinte ao de fim.

Exemplo (Bandeirante, Coleta de 22/10/2026): três trechos, todos com `mostrar`: até 26/09/2019, com três PCH e cinco UTE; de 27/09/2019 a 30/06/2025, com a Areado; desde 01/07/2025, só com as quatro PCH.

## 8. Usinas fictícias (`tests/fixtures/usinas_ficticias/`)

Uma pasta por tipo (`uhe`, `pch`, `cgh`, `ute`, `utn`, `eol`, `ufv`), cada uma com o `perfil.toml`, com valores inventados. Os brutos sintéticos, no formato de cada conjunto do registro, são gerados por `tests/fixtures/brutos_ficticios.py`; o catálogo fictício, por `tests/fixtures/brutos_catalogo.py`. O que cada uma exercita está na decisão técnica D30 do [plano](plan.md).

| Usina | Tipo e modalidade | `[cobertura]` |
|---|---|---|
| `uhe_ficticia` | UHE, TIPO II-A | sem a tabela (os dez conjuntos da UHE) |
| `pch_ficticia` | PCH, TIPO II-C, em conjunto | `geracao` e `programacao` com `conjunto`; os demais `ausente` |
| `cgh_ficticia` | CGH, TIPO II-C | `geracao` e `hidrologia` com `proprio`; os demais `ausente` |
| `ute_ficticia` | UTE, TIPO I | `geracao`, `disponibilidade`, `programacao`, `despacho` e `cvu` com `proprio`; `indicadores` `ausente` |
| `utn_ficticia` | UTN, TIPO I | `geracao`, `disponibilidade`, `indicadores`, `despacho` e `cvu` com `proprio`; `programacao` `ausente` |
| `eol_ficticia` | EOL, TIPO I | `geracao`, `programacao`, `fator_capacidade`, `restricao_detalhe` e `restricao_razao` com `proprio` |
| `ufv_ficticia` | UFV, TIPO II-C, em conjunto, com membros | `restricao_detalhe` com `proprio`; `geracao`, `programacao`, `fator_capacidade` e `restricao_razao` com `conjunto` |

## 9. Requisitos × entidades

| Requisitos da spec | Entidades |
|---|---|
| FR-001 a FR-005 | linha de comando e códigos de saída (5.6; [contracts/cli-coleta.md](contracts/cli-coleta.md)) |
| FR-006 a FR-009, FR-056 | perfil (1.1, 3.1, 5.1; [contracts/perfil-usina.md](contracts/perfil-usina.md)) |
| FR-010 a FR-013 | pastas e `etapa.json` (4) |
| FR-014, FR-015 | cópia de segurança (2.4) |
| FR-016, FR-049 | registro (6); portal (1.2); enumerações (5.3) |
| FR-017 a FR-022, FR-054, FR-059 | série de referência e trechos (7); arquivos locais (1.3); arquivos da usina (2.2) |
| FR-023 a FR-033 | dados brutos, manifestos, versões e dicionários (2.1); cache e falhas (5.4) |
| FR-034 a FR-040, FR-055, FR-057, FR-058 | identificação (5.2); colunas lidas (1.4); extraídos (2.2) |
| FR-041 a FR-047, FR-050, FR-060, FR-061 | arquivos da usina e auditorias (2.2) |
| FR-048 | resumo da Coleta (4.3) |
| FR-051 a FR-053 | catálogo de usinas (2.5); rascunho do perfil (2.6; [contracts/cli-usinas.md](contracts/cli-usinas.md) e [contracts/cli-perfil.md](contracts/cli-perfil.md)) |
| SC-013 | usinas fictícias (8) |
