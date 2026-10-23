# Data Model: Geração do relatório

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-23

## 1. Entradas

| Entrada | Produzida por | Lida por | Uso |
|---|---|---|---|
| `data/usinas/<slug>/analises/etapa.json` | Análises | `pipeline.etapa_anterior_concluida` | pré-requisito: `status` `concluida` e `versao_formato` 3; senão, código 5 |
| `data/usinas/<slug>/analises/resultados.pkl` | Análises | `analises.resultados.carregar_resultados`, chamada por `etapa.executar_relatorio` | pickle `{"versao_formato": 3, "resultados": ResultadosAnalise}`; outra versão gera `ValueError` (código 1) |
| `usinas/<slug>/perfil.toml` | usuário, validado na linha de comando | `comum.perfil.perfil_ativo()` | valores da usina (1.3) |
| `src/comum/regras.py` | regras gerais | importação | limiares, metas, tolerâncias, endereços do ONS, resolução e tamanho das figuras, glossário e limites do resumo (seção 5) |

A etapa não lê `data/raw/`, os dados brutos nem os tratados, nem a pasta `data/usinas/<slug>/conferencia/`: os resultados da Conferência e as datas de obtenção registradas pela Coleta chegam dentro de `ResultadosAnalise`. As entradas da carteira e das referências estão nas seções 6 e 7.

### 1.1 Resultados das Análises

`ResultadosAnalise` está descrito no [data-model das Análises](../004-analises/data-model.md). O caminho do relatório é escolhido por `sem_evt(res)`: verdadeiro quando `comum` não está vazio (usina sem EVT); falso na hidrelétrica com EVT. A etapa usa:

| Campo | Tipo | Uso |
|---|---|---|
| `tipo`, `modalidade` | texto | linha de tipo e modalidade da capa e do resumo; título por tipo; seções do tipo; tabela de parâmetros |
| `cobertura` | dict | subtítulo da capa e período (`inicio`, `fim`, `horas_observadas`); bloco de identificação (`identificacao`, `agentes`); quadro da seção `cobertura` (`horas_esperadas`, `horas_faltantes`, `duplicadas`, `por_ano`, `arquivos`, `manifesto`); anos parciais (`anos_parciais`); abas COBERTURA_POR_ANO e AGENTES. Na usina sem EVT, também `horas_ausentes`, `horas_sem_valor`, `niveis` (horas por nível), `trechos` e `meses_distintos`, no quadro da cobertura e na sazonalidade |
| `datas_obtencao` | dict {pacote do ONS: {`arquivos_registrados`, `publicacao_mais_recente`, `obtencao_mais_recente`}} | datas de obtenção das legendas e da tabela dos conjuntos (1.2) |
| `globais` | dict | indicadores principais da capa; aba INDICADORES_GLOBAIS; registros sinalizados do resumo |
| `indicadores_anuais` | DataFrame, um ano por linha | tabelas das seções `indicadores_anuais` e `perfil_horario`; figura 04; aba INDICADORES_ANUAIS e CSV; evolução anual e anos parciais do resumo |
| `serie_diaria`, `vazoes_anuais` | DataFrame | figuras 01 e 05 (médias calculadas nas Análises) |
| `evt_mensal` | DataFrame, um mês por linha | figura 02 e a sua legenda; aba EVT_MENSAL |
| `perfil_horario_geracao`, `perfil_horario_evt` | DataFrame ano × hora | figura 03; abas PERFIL_HORARIO_GERACAO e PERFIL_HORARIO_EVT |
| `eventos_indisponibilidade_total`, `eventos_parada_com_evt` | DataFrame, um evento por linha | faixas da figura 01; tabelas resumidas das seções `disponibilidade_geracao` e `eventos`; abas EVENTOS_INDISP_TOTAL e EVENTOS_PARADA_COM_EVT |
| `evt_por_faixa_geracao`, `horas_geracao_zero`, `validacao`, `resumo_anomalias`, `extremos` | DataFrame | tabelas das seções `eventos`, `geracao_zero` e `qualidade`; abas de mesmo conteúdo |
| `distribuicao_mes_do_ano`, `anomalias`, `perfil_estatistico` | DataFrame | só na planilha |
| `mudanca_classificacao` | dict (`mes`) | marco da figura 02; legendas das figuras 02 e 05; aba INDICADORES_GLOBAIS |
| `achados` | lista de (título, texto) | constatações no início das seções; aba CONSTATACOES |
| `conclusao` | lista de dicts (`lista`, `ordem`, `regra`, `texto`, `secoes`) | seção `conclusao`; aba CONCLUSAO; bloco de conclusão do resumo |
| `ons` | dict | seção `indicadores_ons` e `indicadores_ons_comum` (`disp_anual`, `decomposicao`, `ug_anual`, `horas_anual`, `divergencias`, `taxa_ultima`); indicador DISPF da capa (`disp_periodo`, `taxa_ultima`); legendas (`recalculo_resumo`, `divergencias`); abas ONS_* (também `horas_mensal` e `recalculo_taxas`) |
| `programacao` | dict | seção `programacao` (`mensal`, `perfil`, `eventos`, `periodo`); abas PROG_* (também `dias_ausentes`, `auditoria`, `classificadas`); vazio na usina sem EVT, que usa `comum["programacao"]` |
| `disponibilidade` | dict | seção e figura 06; notas (`resumo`); parâmetros (`resumo`, `obtido_em`); legenda (`conferencia`); abas DISP_*; vazio na usina sem EVT |
| `hidrologia` | dict | na hidrelétrica com EVT: seção, figuras 07 e 08 e tabelas de cruzamento só com `publicado`; notas (`resumo`, `alinhamento`); parâmetros (`resumo`, `obtido_em`); legenda (`alinhamento`); abas HID_*. Na hidrelétrica sem EVT (`sem_evt` verdadeiro no dict): seção `hidrologia_comum` com `publicado`, `anual` e `mensal`; conferência da hora (`alinhamento`, com as correlações, ou `motivo_alinhamento`); abas HID_* da usina sem EVT |
| `geracao_oficial` | dict | seção `geracao_oficial`; notas e parâmetros (`resumo`, `obtido_em`); legenda (`conferencia`); abas GER_* |
| `cadastro` | dict (`ficha`, `divergencias`, `obtido_em`, `auditoria`) | bloco "Cadastro no ONS"; nota e parâmetros; legenda; abas CAD_FICHA e CAD_AUDITORIA |
| `dicionarios` | dict (`registro`) | aba DICIONARIOS |
| `comum` | dict | usina sem EVT: `cobertura`, `anuais`, `mensal`, `sazonalidade`, `perfil_horario`, `serie_diaria`, `disponibilidade` (`resumo`, `anual`, `mensal`, `eventos_indisponibilidade_total`), `programacao` (`resumo`, `mensal`, `eventos`, `nivel`), `programacao_coletada`, `programacao_horas`, `qualidade` (`sinalizacoes`, `ausencias`, `horas_sinalizadas`, `linhas_usina_sem_valor`, `linhas_usina_sem_valor_periodo`), `agentes` (`proprietario`, `operador`) e `conferencias_nao_aplicaveis`; vazio na hidrelétrica com EVT |
| `niveis` | dict | nível e identificador de cada base da usina sem EVT (`geracao`: `nivel`, `identificador_usina`, `identificador_conjunto`, `nome`; `programacao`, `disponibilidade`, `fator_capacidade` e `restricao_razao`: `nivel`, `identificador`): legendas, tabela dos conjuntos, rótulos das figuras e nível da geração na carteira |
| `trechos` | DataFrame | tabela de trechos da seção 1; aba TRECHOS |
| `termica` | dict | seções de térmica (2.9): `periodo`, `codigos`, `motivos_anual`, `motivos_mensal`, `horas_com_despacho`, `horas_com_despacho_anual`, `inflexibilidade`, `inflexibilidade_resumo`, `atendimento` (`anual`, `mensal`, `maiores_desvios`), `disponivel_sem_despacho` (`anual`), `cvu_cmo` (`resumo`, `semanal`), `cvu_coletado`, `cmo_coletado`, `sem_geracao` e `conferencias` (G3 e G4) |
| `renovavel` | dict | seções de eólica e solar (2.9): `fator_capacidade` (`anual`, `mensal`, `resumo`, `nivel`), `restricao` (`anual`, `mensal`, `por_razao`, `resumo`, `nivel_razao`), `recurso` (`faixas`, `resumo`, `grandeza`, `unidade`, `largura`, `limite`), `programacao` (`maiores_desvios`) e `conferencias` (G1, G2 e G5) |
| `conjunto` | dict | seção do conjunto e relatório em duas partes (2.9): `id`, `nome`, `trechos`, `mensal`, `composicao`, `tipo_publicado`, `peso_usina` e `com_capacidade` |
| `omitidos` | lista de dicts (`item`, `tipo`, `motivo`) | tabela das seções e regras sem base, nas notas; aba OMITIDOS; regras não avaliadas na nota da conclusão |
| `indicadores_carteira` | dict | só na carteira (seção 6) |
| `parametros`, `fontes` | — | preenchidos por esta etapa (seção 3) |

Resultados das conferências usados nas legendas (ids de `fontes.CONFERENCIAS`):

| Conferência | Onde está | Campos lidos |
|---|---|---|
| `geracao` | `geracao_oficial["conferencia"]` | `horas_comuns`, `coincidentes`, `pct_coincidentes`, `divergentes`, `so_ons_geracao`, `so_base_evt` |
| `disponibilidade` | `disponibilidade["conferencia"]` | os mesmos, com `so_ons_disponibilidade` |
| `vazoes` | `hidrologia["alinhamento"]`, uma linha | `horas_comuns`, `coincidentes_ambas`, `pct_coincidencia`, `confirmado` |
| `teifa_teip` | `ons["recalculo_resumo"]`, a contagem da Conferência levada pelas Análises | `meses`, `reproduzidos`, `diferenca_maxima_pp`; sem `reproduzidos` (chamada direta), a legenda refaz a contagem a partir de `ons["recalculo_taxas"]` |
| `dispf_horas` | `ons["divergencias"]` | uma linha por mês-unidade divergente |
| `cadastro` | `cadastro["divergencias"]` | texto; vazio sem divergência |
| `programacao_despacho` (G3), `verificada_despacho` (G4) | `termica["conferencias"]` | `aplicavel`, `horas_comuns`, `coincidentes`, `pct_coincidentes`, `divergentes`, `so_a` |
| `geracao_fontes` (G1) | `renovavel["conferencias"]` | `aplicavel`, `comparados`, `coincidentes`, `divergentes`, `pares` |
| `soma_conjunto` (G2), `programacao_renovaveis` (G5) | `renovavel["conferencias"]` | `aplicavel`, `horas_comuns`, `coincidentes`, `pct_coincidentes`, `divergentes`, `so_a`; na G2, também `horas_incompletas` |
| `alinhamento_hidrologia` | `hidrologia["alinhamento"]` da usina sem EVT, uma linha; `hidrologia["motivo_alinhamento"]` | `correlacao_0h`, `correlacao_menos_1h`, `correlacao_mais_1h`, `horas_comuns`, `confirmado` |

Na hidrelétrica com EVT, só as seis primeiras entram nas legendas, e as das eólicas e solares nunca entram. Na usina sem EVT, entram só as que não dependem da EVT e têm base nesta execução (`conferencia_feita`): o conjunto da base carregado e, nas G1, G2 e G5, `aplicavel` verdadeiro; a da hora da hidrologia, só na hidrelétrica sem EVT.

### 1.2 Datas de obtenção

Para cada conjunto, a data é a `obtencao_mais_recente` registrada pela Coleta em `datas_obtencao.csv` (formato no [data-model da Coleta](../001-coleta-dados/data-model.md)), levada pelas Análises em `res.datas_obtencao`, pelo pacote do ONS (`fontes.datas_obtencao`); sem registro, fica vazia, e a legenda diz "data de obtenção não registrada".

| Id em `fontes.CONJUNTOS` | Conjunto no catálogo (pacote) |
|---|---|
| `evt` | `energia-vertida-turbinavel` |
| `dispf_mensal` | `ind_disponibilidade_fgeracao_uge_mensal` |
| `dispf_anual` | `ind_disponibilidade_fgeracao_uge_anual` |
| `teif_teip` | `taxa_teif_teip` |
| `teif_teip_parametro` | `taxa_teif_teip_parametro` |
| `programacao` | `programacao_diaria` |
| `disponibilidade` | `disponibilidade_usina` |
| `hidrologia` | `dados_hidrologicos_ho` |
| `geracao` | `geracao-usina-2` |
| `cadastro` | `modalidade-usina` |
| `composicao` | `usina_conjunto` |
| `capacidade`, `capacidade_membros` | `capacidade-geracao` |
| `despacho` | `geracao-termica-despacho-2` |
| `cvu` | `cvu-usitermica` |
| `cmo` | `cmo-semanal` |
| `fator_capacidade` | `fator-capacidade-2` |
| `restricao_detalhe` | variante do tipo: `restricao_coff_eolica_detail` ou `restricao_coff_fotovoltaica_detail` |
| `restricao_razao` | variante do tipo: `restricao_coff_eolica_usi` ou `restricao_coff_fotovoltaica` |

As notas e a tabela de parâmetros das bases complementares da hidrelétrica com EVT usam o `obtido_em` gravado pelas Análises (das mesmas datas de obtenção; no cadastro, a `data_consulta_utc` da ficha). A linha "Versão dos arquivos" do quadro da cobertura também vem de `datas_obtencao.csv`, pelas Análises.

### 1.3 Perfil da usina

| Campo | Onde aparece |
|---|---|
| `usina.nome` | título do PDF e do Markdown, cabeçalho das páginas, metadados do PDF e título do resumo |
| `usina.estado` | notas da disponibilidade, da geração e do cadastro (conferência pelo estado); bloco de identificação da usina sem EVT; linha de tipo do resumo |
| `usina.tipo`, `usina.modalidade` | linha de tipo do resumo (o tipo dos resultados, quando há) |
| `usina.subsistema` | identificação e notas das térmicas com o despacho; identificador do CMO |
| `usina.inicio_operacao_comercial` | linha "Início da operação comercial" dos parâmetros |
| `identificacao.cod_usina` | legendas da EVT e da hidrologia; critério de extração; notas |
| `identificacao.ceg`, `identificacao.id_ons` | legendas dos indicadores, da disponibilidade, da geração, do cadastro, do despacho e das restrições; parâmetros; notas; identificação da usina sem EVT |
| `identificacao.cod_programacao`, `identificacao.codigos_programacao` | legenda, nota e parâmetro da programação; identificação da usina sem EVT |
| `identificacao.id_reservatorio` | legenda, nota e parâmetro da hidrologia |
| `identificacao.id_conjunto` | identificação, legendas do conjunto e da composição, tabela dos conjuntos e notas da usina em conjunto |
| `identificacao.planejamento` (`codigo`, `inicio`, `fim`) | identificação, legenda, nota e parâmetros das térmicas |
| `cobertura` | conjuntos coletados e o nível de cada um (pelo registro da Coleta), na tabela dos conjuntos, nas legendas e nos parâmetros da usina sem EVT |
| `parametros.potencia_instalada_mw`, `unidades_geradoras`, `potencia_unitaria_mw`, `tipo_turbina`, `engolimento_nominal_ug_m3s`, `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia` | bloco de parâmetros da capa; linhas de referência e rótulos das figuras; legendas descritivas; notas; parâmetros |
| `parametros.potencias_unidades_mw`, `parametros.combustivel` | bloco de parâmetros e tabela de parâmetros da usina sem EVT |
| `parametros.queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` | parâmetros; a vazão remanescente também na definição de vertimento mínimo |
| `parametros.fontes.geral` | origem dos parâmetros técnicos |
| `parametros.fontes.garantia_fisica` | origem da garantia física nos parâmetros e na nota; o trecho até a primeira vírgula é o órgão citado ao lado da garantia física na capa (`conteudo.orgao_garantia_fisica`) |
| `parametros.fontes.inicio_operacao_comercial` (opcional) | origem do início da operação comercial; vazia sem o campo |
| `parametros.fontes.ip_teif` (opcional) | frase da origem do IP e do TEIF nas notas; omitida sem o campo |
| `analises.vertimento_minimo_m3s` | figura 02 e a sua legenda; nota da tabela anual; notas; parâmetros |
| `analises.descricao_vertimento_minimo` (opcional) | complemento da definição de vertimento mínimo nas notas |
| `analises.fontes.vertimento_minimo` (opcional) | base do limiar de vertimento mínimo nos parâmetros |
| `textos.ressalva_volume_util` (opcional) | nota da hidrologia |
| derivados: `engolimento_maximo_m3s`, `disponibilidade_referencia`, `produtividade_nominal_mw_m3s` | capa, figuras 04, 05, 07 e 15, faixas de afluência, notas e parâmetros |

`usina.nome_curto`, `identificacao.nome_ons` e `analises.faixas_geracao_mw` não são usados nesta etapa. Na carteira, o perfil dá também `usina.situacao`, o nome e a potência (seção 6).

## 2. Saídas

### 2.1 Arquivos em `reports/<slug>/`

Nomes em `caminhos.ARQUIVOS_RELATORIO`; sem `.bak`. A cada execução:
- todas as saídas são geradas em `reports/<slug>/.gravando/` (`etapa.PASTA_TEMPORARIA`), com a mesma estrutura (`figures/` incluída);
- `_conferir_saidas` exige que cada uma exista e não esteja vazia, e que os PDFs comecem com `%PDF-`;
- `_trocar_saidas` move cada uma para o lugar com `os.replace`; a anterior fica em `.gravando/.anteriores/` até o fim da troca;
- se a troca falhar, cada arquivo volta à versão anterior; a versão anterior que não puder voltar vai para `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`, que fica até o usuário recuperá-la;
- `.gravando/` é apagada ao fim, com ou sem erro;
- depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/` (as opcionais dos dois caminhos).

| Arquivo | Formato | Grava | Conteúdo |
|---|---|---|---|
| `relatorio_analise_estatistica.pdf` | PDF, A4 paisagem | `pdf.PDFReportGenerator.build_pdf` | relatório (2.2 a 2.4 e 2.9) |
| `relatorio_analise_estatistica.md` | Markdown, UTF-8 sem BOM, fim de linha do sistema | `markdown.gerar_relatorio_md` | o mesmo relatório (2.5) |
| `perfil_estatistico_anual.xlsx` | XLSX (openpyxl) | `planilha.exportar_tabelas` | uma aba por tabela (2.7 e 2.9) |
| `perfil_estatistico_anual.csv` | CSV `;`, ponto decimal, UTF-8 sem BOM, fim de linha do sistema | `planilha.exportar_tabelas` | indicadores anuais (2.8) |
| `figures/<nn>_<nome>.png` | PNG, 300 DPI | `figuras.gerar_graficos` | até oito figuras na hidrelétrica com EVT (2.6) e até 15 na usina sem EVT (2.9) |
| `resumo_executivo.pdf` | PDF, A4 retrato, no máximo duas páginas, sem imagem | `resumo_pdf.gerar_resumo_pdf`, por `resumo.gerar_resumo` | resumo executivo (2.10) |
| `resumo_executivo.md` | Markdown, UTF-8 sem BOM, fim de linha do sistema | `resumo.gerar_resumo_md` | o mesmo resumo |
| `etapa.json` | JSON | `pipeline.executar_etapa` | manifesto (seção 4) |

### 2.2 PDF

- **Página**: A4 paisagem (841,9 × 595,3 pt); margens de 36 pt (laterais), 50 pt (superior) e 42 pt (inferior); largura útil de cerca de 769,9 pt.
- **Cabeçalho** (página 2 em diante): "`<usina.nome>` — energia vertida turbinável (dados ONS) · `<dd/mm/aaaa>` a `<dd/mm/aaaa>`", com um fio abaixo; na usina sem EVT, "`<usina.nome>` — desempenho operacional (dados ONS) · `<dd/mm/aaaa>` a `<dd/mm/aaaa>`".
- **Rodapé**: fio e "Página X de Y", à direita.
- **Metadados**: título "`<usina.nome>` — energia vertida turbinável e desempenho operacional" (na usina sem EVT, o título da capa); assunto "Análise dos dados abertos do ONS, `<início>` a `<fim>`"; autor "Pipeline de análise `<usina.nome>` (dados ONS)". Com `--data-geracao`, `CreationDate` e `ModDate` ficam `D:20000101000000+00'00'`.
- **Fontes**: Arial (`arial.ttf`, `arialbd.ttf`, `ariali.ttf`, `arialbi.ttf` de `%WINDIR%\Fonts`) ou DejaVu Sans do matplotlib; Helvetica só se nenhuma existir.
- **Página 1 (capa)**, nesta ordem:
  1. título "`<usina.nome>` — Análise do desempenho operacional" (`conteudo.titulo_capa_relatorio`);
  2. subtítulo "Análise dos dados abertos do ONS · `<dd/mm/aaaa HHh>` a `<dd/mm/aaaa HHh>` · `<N>` registros horários · Gerado em `<dd/mm/aaaa HH:MM>`", com a mesma data de geração do Markdown, do resumo e do `resumo`;
  3. blocos lado a lado, cada um com a sua legenda de fonte: "Identificação nos dados do ONS" (`bloco_identificacao`: cod_usina, Reservatório, Rio / bacia, Subsistema, Agente); "Cadastro no ONS" (`bloco_cadastro`, só com o cadastro: Usina, Modalidade de operação, Centro de operação, Ponto de conexão, Potência autorizada, Estado · situação na ANEEL, Homônimos excluídos pelo CEG); "Parâmetros técnicos da usina" (`bloco_parametros`: Potência instalada, Turbinas, Engolimento nominal, Garantia física com o órgão de `orgao_garantia_fisica`, IP / TEIF de referência);
  4. indicadores principais em cartões (`tab_capa_indicadores`): Disponibilidade média declarada; Disponibilidade apurada pelo ONS (DISPF), só com os indicadores; Fator de capacidade; Energia vertida turbinável; EVT com a usina parada. Abaixo, a nota e a legenda de fonte;
  5. "Sumário" em duas colunas, com o número, o título e a página de cada seção; quebra de página.
- **Página 2 em diante**: as seções (2.3; na usina sem EVT, 2.9).

### 2.3 Seções do PDF e do Markdown

Cada seção começa com "N. Título" e as suas constatações ("**Título.** texto"). Cada tabela vem com o subtítulo (quando `textos_tabelas` o define), a tabela, a nota (quando há) e a legenda de fonte; cada figura, com a imagem, a legenda descritiva (`legenda_figura`) e a legenda de fonte. Na São Domingos, com todos os conjuntos, são 17 seções e 30 páginas; só com a base de EVT, 12 seções. Esta é a lista da hidrelétrica com EVT (`caminhos=("evt",)`); a da usina sem EVT está em 2.9.

| Chave | Título | Presente | Conteúdo, na ordem (chaves do mapa de fontes) |
|---|---|---|---|
| `cobertura` | Fonte e cobertura dos dados | sempre | quadro `tab_cobertura` |
| `indicadores_anuais` | Indicadores anuais | sempre | `tab_indicadores_anuais` |
| `disponibilidade_geracao` | Disponibilidade e geração por ano | sempre | figura `disponibilidade_anual` (04); `tab_eventos_indisponibilidade` ou "Nenhum período com essa duração." |
| `indicadores_ons` | Indicadores oficiais do ONS por unidade geradora | `res.ons` | `tab_ons_disp_anual`; `tab_ons_decomposicao`, aberta pelo texto `texto_taxas_ons`; `tab_ons_ug_anual`; `tab_ons_horas`; `tab_ons_divergencias` |
| `serie_temporal` | Série temporal de disponibilidade, geração e EVT | sempre | figura `serie_temporal` (01) |
| `evt_mensal` | Energia vertida turbinável mensal | sempre | figura `evt_mensal` (02) |
| `perfil_horario` | Perfil horário da geração e da EVT | sempre | figura `perfil_horario` (03); `tab_perfil_horario` |
| `eventos` | EVT por nível de geração e eventos de usina parada | sempre | `tab_evt_por_nivel`; `tab_eventos_parada_evt` ou "Nenhum evento." |
| `programacao` | Operação verificada e programação diária do ONS | `res.programacao` | `tab_programacao_mensal`; `tab_programacao_hora`; `tab_programacao_eventos`; frase dos dias sem arquivo no portal |
| `disponibilidade_sincronizada` | Disponibilidade operacional e sincronizada (ONS) | `res.disponibilidade` | `tab_disponibilidade_anual`; figura `disponibilidade_sincronizada` (06); `tab_disponibilidade_paradas`; `tab_disponibilidade_divergencias`; notas (`notas_disponibilidade`) |
| `hidrologia` | Afluência, vertimento e nível do reservatório (ONS) | `res.hidrologia` | só com `publicado`: `tab_faixas_afluencia`, `tab_faixas_afluencia_evt`, figura `faixas_afluencia` (07), `tab_hidrologia_anual`, `tab_hidrologia_perfil`, figura `perfil_hidrologico` (08); sempre: notas (`notas_hidrologia`) |
| `geracao_zero` | Horas com geração zero por mês | sempre | `tab_geracao_zero` |
| `vazoes` | Vazões defluentes por ano | sempre | figura `vazoes_defluentes` (05) |
| `geracao_oficial` | Conferência da geração com a série oficial (ONS) | `res.geracao_oficial` | texto `texto_conferencia_geracao`, quando não há a constatação "Conferência da geração"; `tab_geracao_oficial` |
| `qualidade` | Qualidade dos dados | sempre | `tab_regras_validacao`; `tab_registros_sinalizados`; `tab_extremos` |
| `conclusao` | Conclusão | sempre (nos dois caminhos) | frase de abertura e listas (`listas_conclusao`), ou a frase de `frase_sem_itens` |
| `notas` | Notas metodológicas e limitações | sempre | notas (`notas_metodologicas`, a última com as regras da conclusão); `tab_parametros` |

### 2.4 Tabelas do relatório

Cabeçalhos fixos, em `conteudo.py`; valores formatados no padrão brasileiro (5.9). As tabelas da usina sem EVT estão em 2.9.

| Chave | Cabeçalho | Linhas |
|---|---|---|
| `tab_cobertura` | pares item × valor: Conjunto de dados, Critério de extração, Arquivos lidos, Versão dos arquivos, Período, Registros, Anos parciais | "Arquivos lidos" e "Versão dos arquivos" só com a auditoria e as datas de obtenção da Coleta |
| `tab_indicadores_anuais` | Ano, Cobertura, Disp. média (% Pinst), Δ vs ref. GF, Fator de capacidade, Geração / GF, EVT (MWh), EVT no vert. mínimo, Índice EVT, Horas c/ EVT, Horas parada c/ EVT, Horas indisp. total | um ano por linha |
| `tab_eventos_indisponibilidade` | Início, Fim, Duração (h), Duração (dias), Vazão vertida média (m³/s) | eventos com duração ≥ `DURACAO_MINIMA_EVENTO_RELATORIO_H` |
| `tab_ons_disp_anual` | Ano, Disp. declarada (EVT, % Pinst), DISPF (média das UGs), Indisp. programada, Indisp. forçada, Δ DISPF vs ref. GF | um ano por linha |
| `tab_ons_decomposicao` | Taxa, UG, Parcela, Horas na janela, Contribuição (p.p.), Participação na taxa | taxa × unidade × parcela |
| `tab_ons_ug_anual` | Ano, UG, DISPF, INDISPPF, INDISPFF, DMDFF (h) | ano × unidade |
| `tab_ons_horas` | Ano, UG, Meses, HP, HS, HRD, HDP, HDF, HDCE, HEDP, HEDF | ano × unidade |
| `tab_ons_divergencias` | Mês, UG, HS, HRD, HDP (TEIP), Programadas pelo DISPF (h), HDF (TEIP), Forçadas pelo DISPF (h) | mês-unidade divergente |
| `tab_perfil_horario` | Ano, EVT diurna (MWmed), EVT noturna (MWmed), Razão EVT diurna/noturna, Geração diurna (MW), Geração noturna (MW), Geração diurna ÷ noturna | um ano por linha |
| `tab_evt_por_nivel` | Geração na hora, Horas, EVT (MWh), Participação na EVT, Geração média (MW), Disponibilidade média (MW) | uma faixa de geração por linha |
| `tab_eventos_parada_evt` | Início, Fim, Duração (h), Disponibilidade média (MW), Vazão vertida média (m³/s), EVT (MWh) | os `NUMERO_EVENTOS_RELATORIO` maiores pela EVT |
| `tab_programacao_mensal` | Mês, Horas comuns, Paradas c/ EVT, c/ programação ≤ 1 MW, EVT nessas horas (MWh), % da EVT do mês, Paradas c/ programação > 5 MW, Gerou c/ programação ≤ 1 MW | um mês por linha |
| `tab_programacao_hora` | Hora, 0h … 23h | uma linha ("Horas") |
| `tab_programacao_eventos` | Início, Fim, Duração (h), Programação média (MW), Disponibilidade média (MW), EVT (MWh) | os `NUMERO_EVENTOS_RELATORIO` maiores pela duração (e pela EVT) |
| `tab_disponibilidade_anual` | Ano, Horas, Operacional (MW), Declarada EVT (MW), Sincronizada (MW), Geração (MW), Não sincronizada (GWh), Reserva desligada TEIFa/TEIP (GWh) | um ano por linha |
| `tab_disponibilidade_paradas` | Sincronização, EVT, Programação do ONS, Horas, EVT (MWh) | uma classe por linha |
| `tab_disponibilidade_divergencias` | Início, Fim, Horas, Diferença média (MW), Diferença máxima (MW) | os `NUMERO_EVENTOS_RELATORIO` maiores pelas horas, em ordem cronológica |
| `tab_faixas_afluencia`, `tab_faixas_afluencia_evt` | Ano, Até `<q1>` m³/s, `<q1>` a `<qmáx>` m³/s, Acima de `<qmáx>` m³/s, Sem dado, Total, Cabia nas turbinas | um ano por linha; horas ou EVT (MWh). `q1` = engolimento de uma unidade, `qmáx` = engolimento máximo |
| `tab_hidrologia_anual` | Ano, Horas, Afluência média (m³/s), Afluência máx. (m³/s), Turbinada (m³/s), Vertida (m³/s), Nível mont. mín.–máx. (m), Volume útil (%), Horas acima do engolimento | um ano por linha |
| `tab_hidrologia_perfil` | Hora, Turbinada c/ parada (m³/s), Vertida c/ parada (m³/s), Nível c/ parada (m), Turbinada demais (m³/s), Vertida demais (m³/s), Nível demais (m) | 0h a 21h, de 3 em 3 h |
| `tab_geracao_zero` | Ano, Jan … Dez, Total, Com disp. zero, Com usina disponível | um ano por linha |
| `tab_geracao_oficial` | Ano, Base de EVT (GWh), Geração por usina (GWh), Diferença (MWh), Horas só na base de EVT, Horas só na série oficial | um ano por linha |
| `tab_regras_validacao` | Regra, Grupo, Descrição, Registros com violação, % dos registros, Status | R1 a R9 |
| `tab_registros_sinalizados` | Regra, Descrição, Horas, Primeira ocorrência, Última ocorrência | uma regra por linha |
| `tab_extremos` | Grandeza, Unidade, Máximo, Data/hora do máximo, Mínimo, Data/hora do mínimo | uma grandeza por linha |
| `tab_parametros` | Grupo, Parâmetro, Valor, Unidade, Origem | `res.parametros` (seção 3) |

Rótulos de `tab_disponibilidade_paradas` (`conteudo._ROTULOS_CLASSES_PARADA`): sincronização "alguma unidade sincronizada" ou "nenhuma unidade sincronizada"; EVT "com EVT" ou "sem EVT"; programação do ONS, a classe da hora (`DESCRICAO_CLASSES` das Análises) ou, sem programação para a hora, "sem programação: fora do período ou sem valor programado".

`tab_indicadores_anuais`, `tab_perfil_horario`, `tab_geracao_zero`, `tab_geracao_oficial` e o quadro da cobertura não têm subtítulo próprio. As tabelas das bases complementares só aparecem com linhas; `tab_eventos_indisponibilidade` e `tab_eventos_parada_evt`, sem linhas, mantêm o subtítulo e mostram a frase.

### 2.5 Markdown

Mesmo conteúdo do PDF, nesta ordem:
1. `# <usina.nome> — energia vertida turbinável e desempenho operacional (dados ONS)`; na usina sem EVT, `# <usina.nome> — Análise do desempenho operacional`;
2. `**Período**: <dd/mm/aaaa HHh> a <dd/mm/aaaa HHh> (<N> registros horários)` (na usina sem EVT, "`<N>` registros horários da série de referência, `<série com o identificador e o nível>`") e `**Gerado em**: <dd/mm/aaaa HH:MM>`;
3. `### Identificação nos dados do ONS`, `### Cadastro no ONS` (com o cadastro) e `### Parâmetros técnicos da usina`, em tabelas "Item | Valor", cada uma com a legenda de fonte;
4. `### Indicadores principais`, em tabela "Indicador | Valor | Detalhe", com a nota e a legenda;
5. `## Sumário`, lista numerada com links para as âncoras das seções (`_ancora_md`: minúsculas, sem pontuação, espaços por hífens);
6. cada seção, `## N. Título`: constatações, tabelas (`### <subtítulo>`, tabela, nota com `*` escapado, legenda) e figuras no corpo (`![<título da seção>](figures/<arquivo>.png)`, legenda descritiva, legenda de fonte); notas das seções e das notas metodológicas em itens `- `; na conclusão, `### <lista>` e itens `- `. Na usina sem EVT, os blocos de `comum.blocos_secao` (`_md_blocos`), com as subseções como `### <título>`.

Figura ausente do dicionário de figuras é omitida. Na São Domingos: 768 linhas, 30 tabelas, 8 figuras e 38 legendas de fonte.

### 2.6 Figuras da hidrelétrica com EVT

Nomes em `figuras.NOMES_FIGURAS` (sempre) e `figuras.NOMES_FIGURAS_OPCIONAIS` (com a condição de `_GERADORES_OPCIONAIS`); 300 DPI. As da usina sem EVT estão em 2.9.

| Arquivo | Chave | Marca seaborn | Dados (`ResultadosAnalise`) | Polegadas (px) | Gerada | No PDF |
|---|---|---|---|---|---|---|
| `01_serie_temporal_disponibilidade_geracao_evt.png` | `serie_temporal` | `lineplot` e área da EVT | `serie_diaria`; faixas de `eventos_indisponibilidade_total` ≥ 24 h; potência instalada e garantia física | 11 × 4,3 (3300 × 1290) | sempre | largura útil, ≈ 760 × 297 pt |
| `02_evt_mensal.png` | `evt_mensal` | `histplot` empilhado, com pesos | `evt_mensal` (`evt_vertimento_minimo_mwh`, `evt_demais_horas_mwh`); `mudanca_classificacao` | 11 × 4,3 (3300 × 1290) | sempre | largura útil |
| `03_perfil_horario_geracao_evt.png` | `perfil_horario` | `heatmap`, dois painéis | `perfil_horario_geracao`, `perfil_horario_evt` | 11 × 4,4 (3300 × 1320) | sempre | 710 × 284 pt |
| `04_disponibilidade_geracao_anual.png` | `disponibilidade_anual` | `barplot` com `hue` | `indicadores_anuais`; disponibilidade de referência; garantia física em % da potência | 11 × 4,6 (3300 × 1380) | sempre | altura de 285 pt |
| `05_vazoes_defluentes_anuais.png` | `vazoes_defluentes` | `histplot` empilhado, discreto | `vazoes_anuais`; engolimento máximo | 11 × 4,3 (3300 × 1290) | sempre | largura útil |
| `06_disponibilidade_operacional_sincronizada_mensal.png` | `disponibilidade_sincronizada` | `lineplot` | `disponibilidade["mensal"]`; potência instalada | 11 × 4,3 (3300 × 1290) | `res.disponibilidade` com `mensal` não vazio | largura útil |
| `07_evt_por_faixa_de_afluencia.png` | `faixas_afluencia` | `histplot` empilhado, discreto, com o total no topo | `hidrologia["faixas_anual"]` | 11 × 4,6 (3300 × 1380) | `hidrologia["publicado"]` e `faixas_anual` não vazio | altura de 285 pt |
| `08_perfil_horario_nivel_vazoes.png` | `perfil_hidrologico` | `lineplot`, dois painéis | `hidrologia["perfil"]`; janela diurna | 11 × 4,6 (3300 × 1380) | `hidrologia["publicado"]` e `perfil` não vazio | altura de 285 pt |

Metadado do PNG: só "Software" do matplotlib. Paleta e tema: plano, D6 e D7. A figura opcional que não é gerada numa execução sai de `figures/`: `executar_relatorio` a apaga depois da troca das saídas, com uma mensagem no log (`gerar_graficos` faz o mesmo na pasta em que grava).

### 2.7 Planilha (`perfil_estatistico_anual.xlsx`) da hidrelétrica com EVT

Uma aba por quadro, na ordem abaixo; cabeçalho na linha 1, congelado em `A2`; largura de coluna `min(max(len(nome), 12) + 3, 60)`; sem índice. As abas da base de EVT existem sempre; as demais, só com o conjunto carregado e com linhas. Na São Domingos: 58 abas, todas menos DISP_DIVERGENCIAS e GER_DIVERGENCIAS, sem linhas. As abas da usina sem EVT estão em 2.9.

**Constatações e conclusão** (sempre)

| Aba | Origem | Colunas |
|---|---|---|
| CONSTATACOES | `achados` | `tema`, `constatacao` |
| CONCLUSAO | `conteudo.tabela_conclusao(res)` | `lista` (título da lista), `ordem`, `regra`, `texto`, `secoes` ("N. Título" de cada seção de origem presente, separados por "; ") |

**Base de EVT** (sempre)

| Aba | Origem | Colunas |
|---|---|---|
| INDICADORES_ANUAIS | `indicadores_anuais` | as 29 colunas do CSV (2.8) |
| INDICADORES_GLOBAIS | `globais` e cinco linhas da cobertura (`planilha._globais_como_tabela`) | `indicador`, `valor`; as chaves de `globais`, `inicio_serie`, `fim_serie`, `horas_ausentes`, `anos_parciais`, `mes_mudanca_classificacao_vertimento` |
| COBERTURA_POR_ANO | `cobertura["por_ano"]` | `ano`, `primeiro_registro`, `ultimo_registro`, `horas_observadas`, `horas_calendario`, `cobertura_pct`, `ano_parcial` |
| AGENTES | `cobertura["agentes"]` | `nom_agente`, `primeiro_registro`, `ultimo_registro`, `horas` |
| EVT_MENSAL | `evt_mensal` | `mes`, `horas`, `energia_gerada_mwh`, `geracao_media_mw`, `disponibilidade_media_mw`, `evt_mwh`, `evt_vertimento_minimo_mwh`, `evt_demais_horas_mwh` |
| EVT_MES_DO_ANO | `distribuicao_mes_do_ano` | `mes`, `mes_nome`, `evt_mwh`, `participacao_pct` |
| EVT_POR_FAIXA_GERACAO | `evt_por_faixa_geracao` | `faixa_geracao`, `horas`, `evt_mwh`, `geracao_media_mw`, `disponibilidade_media_mw`, `participacao_evt_pct` |
| PERFIL_HORARIO_GERACAO | `perfil_horario_geracao` | `ano`, `0` a `23` |
| PERFIL_HORARIO_EVT | `perfil_horario_evt` | `ano`, `0` a `23` |
| EVENTOS_PARADA_COM_EVT | `eventos_parada_com_evt` | `inicio`, `fim`, `duracao_h`, `geracao_media_mw`, `disponibilidade_media_mw`, `vazao_vertida_media_m3s`, `evt_mwh` |
| HORAS_GERACAO_ZERO_MES | `horas_geracao_zero` | `ano`, `jan` a `dez`, `total`, `com_disponibilidade_zero`, `com_usina_disponivel` |
| EVENTOS_INDISP_TOTAL | `eventos_indisponibilidade_total` | `inicio`, `fim`, `duracao_h`, `vazao_vertida_media_m3s`, `geracao_media_mw` |
| ANOMALIAS | `anomalias` | `din_instante`, `qualidade_registro`, `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_produtividade`, `val_energiavertida`, `val_energiavertidaturbinavel` |
| RESUMO_ANOMALIAS | `resumo_anomalias` | `regra`, `descricao`, `horas`, `primeira_ocorrencia`, `ultima_ocorrencia`, `evt_mwh` |
| VALIDACAO_REGRAS | `validacao` | `codigo_regra`, `grupo`, `nome_regra`, `expressao`, `total_linhas`, `conformes`, `violacoes`, `taxa_conformidade_pct`, `desvio_maximo`, `desvio_medio`, `status` |
| EXTREMOS | `extremos` | `variavel`, `unidade`, `maximo_historico`, `data_hora_max`, `minimo_historico`, `data_hora_min` |
| PERFIL_ESTATISTICO_ANUAL | `perfil_estatistico` | `ano`, `variavel`, `unidade`, `registros_considerados`, `media`, `desvio_padrao`, `mediana`, `percentil_25`, `percentil_75`, `soma_acumulada`, `valor_minimo`, `data_hora_min`, `valor_maximo`, `data_hora_max` |
| PARAMETROS | `parametros` (seção 3) | `grupo`, `parametro`, `valor`, `unidade`, `origem` |

**Indicadores por unidade geradora** (com `res.ons`)

| Aba | Origem | Colunas |
|---|---|---|
| ONS_DISP_ANUAL_USINA | `ons["disp_anual"]` | `ano`, `ano_parcial`, `disponibilidade_declarada_pct`, `dispf_pct`, `indisppf_pct`, `indispff_pct`, `desvio_dispf_referencia_pp` |
| ONS_UG_ANUAL | `ons["ug_anual"]` | `ano`, `ug`, `cod_equipamento`, `potencia_mw`, `dispf`, `indisppf`, `indispff`, `dmdff`, `fdff`, `tdff`, `id_usina`, `agente`, `modalidade`, `arquivo_origem`, `ano_parcial` |
| ONS_HORAS_UG_ANUAL | `ons["horas_anual"]` | `ano`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HDCE`, `HEDP`, `HEDF`, `meses`, `ano_parcial` |
| ONS_HORAS_UG_MENSAL | `ons["horas_mensal"]` | `mes`, `ug`, `HP` a `HEDF`, `num_versao`, `residuo_identidade_h`, `potencia_mw`, `ano` |
| ONS_TEIFA_TEIP | `ons["recalculo_taxas"]` | `mes`, `meses_na_janela`, `teifa_publicada`, `teifa_recalculada`, `teip_publicada`, `teip_recalculada`, `diferenca_teifa_pp`, `diferenca_teip_pp` |
| ONS_DECOMPOSICAO_TAXAS | `ons["decomposicao"]` | `taxa`, `ug`, `parcela`, `horas`, `contribuicao_pp`, `participacao_pct` |
| ONS_DIVERGENCIAS | `ons["divergencias"]` | `mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `horas_programadas_indisppf`, `HDF`, `horas_forcadas_indispff`, `diferenca_programada_h`, `diferenca_forcada_h` |

**Programação diária** (com `res.programacao`)

| Aba | Origem | Colunas |
|---|---|---|
| PROG_RESUMO_MENSAL | `programacao["mensal"]` | `mes`, `horas_comuns`, `horas_parada_evt_programacao_zero`, `horas_parada_evt_programacao_positiva`, `horas_parada_sem_evt`, `horas_gerando_programacao_zero`, `horas_gerando_com_programacao`, `horas_parada_com_evt`, `evt_mwh`, `evt_parada_programacao_zero_mwh`, `participacao_evt_programacao_zero_pct`, `horas_desvio_programacao`, `disponibilidade_media_parada_programacao_zero_mw`, `desvio_medio_absoluto_mw` |
| PROG_EVENTOS_DESVIO | `programacao["eventos"]` | `inicio`, `fim`, `duracao_h`, `programacao_media_mw`, `disponibilidade_media_mw`, `evt_mwh` |
| PROG_HORA_DO_DIA | `programacao["perfil"]` | `hora`, `horas`, `evt_mwh` |
| PROG_DIAS_AUSENTES | `programacao["dias_ausentes"]` | `dia` |
| PROG_AUDITORIA_ARQUIVOS | `programacao["auditoria"]` | `arquivo`, `dia`, `linhas_lidas`, `linhas_usina`, `linhas_codigo_sem_conferencia`, `patamares`, `data_interna_confere`, `status` |
| PROG_HORAS_CLASSIFICADAS | `programacao["classificadas"]` | `din_instante`, `val_geracao`, `val_energiavertidaturbinavel`, `val_disponibilidade`, `geracao_programada_mw`, `classe`, `desvio_programacao` |

**Disponibilidade por usina** (com `res.disponibilidade`)

| Aba | Origem | Colunas |
|---|---|---|
| DISP_CONFERENCIA | `disponibilidade["conferencia"]`, uma linha | `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes`, `so_ons_disponibilidade`, `so_base_evt`, `horas_sinalizadas_excluidas`, `tolerancia_mw` |
| DISP_DIVERGENCIAS | `disponibilidade["divergencias"]` | `inicio`, `fim`, `horas`, `diferenca_media_mw`, `diferenca_maxima_mw` |
| DISP_CLASSES_PARADA | `disponibilidade["classes"]` | `sincronizacao`, `evt`, `classe_programacao`, `horas`, `evt_mwh` |
| DISP_HORAS_PARADAS | `disponibilidade["horas_paradas"]` | `din_instante`, `val_geracao`, `val_dispoperacional`, `val_dispsincronizada`, `val_energiavertidaturbinavel`, `sincronizacao`, `evt`, `classe_programacao` |
| DISP_MENSAL | `disponibilidade["mensal"]` | `periodo`, `horas_comuns`, `disp_operacional_media_mw`, `disp_declarada_media_mw`, `disp_sincronizada_media_mw`, `geracao_media_mw`, `capacidade_nao_sincronizada_media_mw`, `capacidade_nao_sincronizada_mwh`, `horas_paradas`, `horas_paradas_sem_sincronizacao`, `horas_paradas_sincronizadas`, `reserva_desligada_teif_mwh`, `diferenca_mwh` |
| DISP_ANUAL | `disponibilidade["anual"]` | as de DISP_MENSAL e `ano_parcial` |
| DISP_AUSENCIAS | `disponibilidade["ausencias"]` | `tipo`, `inicio`, `fim`, `horas` |
| DISP_AUDITORIA | `disponibilidade["auditoria"]` | `arquivo`, `formato`, `periodo`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia`, `horas_usina`, `valores_invalidos`, `duplicatas_conflitantes`, `recursos_duplicados_catalogo`, `status`, `mensagem` |

**Dados hidrológicos** (com `res.hidrologia`; HID_ALINHAMENTO, HID_AUSENCIAS e HID_AUDITORIA sempre que tiverem linhas, as demais só com `publicado`)

| Aba | Origem | Colunas |
|---|---|---|
| HID_ALINHAMENTO | `hidrologia["alinhamento"]`, uma linha | `horas_comuns`, `coincidentes_turbinada`, `coincidentes_vertida`, `coincidentes_ambas`, `pct_coincidencia`, `meta_pct`, `tolerancia_m3s`, `deslocamento_aplicado_h`, `confirmado` |
| HID_FAIXAS_AFLUENCIA | `hidrologia["faixas_mensal"]` | `periodo`, `faixa_afluencia`, `horas`, `evt_mwh` |
| HID_FAIXAS_ANUAL | `hidrologia["faixas_anual"]` | `periodo`, `faixa_afluencia`, `horas`, `evt_mwh`, `ano_parcial` |
| HID_HORAS_EVT | `hidrologia["faixas"]` | `din_instante`, `val_vazaoafluente`, `faixa_afluencia`, `val_energiavertidaturbinavel`, `val_geracao` |
| HID_MENSAL | `hidrologia["mensal"]` | `mes`, `horas`, `afluencia_media_m3s`, `afluencia_maxima_m3s`, `turbinada_media_m3s`, `vertida_media_m3s`, `vertida_nao_turbinavel_media_m3s`, `nivel_montante_min_m`, `nivel_montante_medio_m`, `nivel_montante_max_m`, `nivel_jusante_medio_m`, `volume_util_medio_pct`, `horas_afluencia_acima_engolimento` |
| HID_ANUAL | `hidrologia["anual"]` | `periodo`, as demais de HID_MENSAL e `ano_parcial` |
| HID_PERFIL_HORA_DO_DIA | `hidrologia["perfil"]` | `grupo_dias`, `hora`, `dias`, `nivel_montante_medio_m`, `afluencia_media_m3s`, `turbinada_media_m3s`, `vertida_media_m3s` |
| HID_AUSENCIAS | `hidrologia["ausencias"]` | `tipo`, `inicio`, `fim`, `horas` |
| HID_AUDITORIA | `hidrologia["auditoria"]` | as de DISP_AUDITORIA |

**Geração por usina** (com `res.geracao_oficial`)

| Aba | Origem | Colunas |
|---|---|---|
| GER_CONFERENCIA | `geracao_oficial["conferencia"]`, uma linha | `horas_comuns`, `coincidentes`, `divergentes`, `pct_coincidentes`, `so_ons_geracao`, `so_base_evt`, `energia_ons_geracao_mwh`, `energia_base_evt_mwh`, `tolerancia_mw` |
| GER_MENSAL | `geracao_oficial["mensal"]` | `mes`, `energia_base_evt_mwh`, `energia_ons_geracao_mwh`, `diferenca_mwh`, `horas_so_base_evt`, `horas_so_ons_geracao` |
| GER_ANUAL | `geracao_oficial["anual"]` | `ano`, as demais de GER_MENSAL e `ano_parcial` |
| GER_DIVERGENCIAS | `geracao_oficial["divergencias"]` | `inicio`, `fim`, `horas`, `diferenca_media_mw`, `diferenca_maxima_mw` |
| GER_AUSENCIAS | `geracao_oficial["ausencias"]` | `tipo`, `inicio`, `fim`, `horas` |
| GER_AUDITORIA | `geracao_oficial["auditoria"]` | as de DISP_AUDITORIA |

**Cadastro, dicionários e fontes**

| Aba | Origem | Presente | Colunas |
|---|---|---|---|
| CAD_FICHA | `cadastro["ficha"]`, uma linha | com o cadastro | `nom_usina`, `ceg`, `id_ons`, `nom_modalidadeoperacao`, `sgl_centrooperacao`, `nom_pontoconexao`, `val_potenciaautorizada`, `id_estado`, `sts_aneel`, `data_consulta_utc`, `arquivo_origem`, `homonimos`, `linhas_so_identificador`, `linhas_so_conferencia`, `divergencias` |
| CAD_AUDITORIA | `cadastro["auditoria"]` | com linhas | `arquivo`, `formato`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia`, `status`, `mensagem` |
| DICIONARIOS | `dicionarios["registro"]` | com o registro dos dicionários | `conjunto`, `pasta`, `formato`, `arquivo`, `url`, `resultado_ultima_obtencao`, `obtido_em_utc`, `sha256`, `tamanho_bytes`, `versoes_anteriores`, `ultima_versao_anterior` |
| FONTES | `fontes.tabela_fontes_abas(res, abas)` | sempre, por último | `aba`, `conjuntos_origem`, `conferencias` (ou "—"), `sem_outra_fonte` (ou "—"), `calculado_no_relatorio` ("sim" ou "não"); uma linha por outra aba, na ordem da planilha (regras em 5.4) |

As colunas das abas de auditoria chegam fixadas pelas etapas anteriores: `COLUNAS_AUDITORIA` de `src/tratamento/series.py` (DISP, HID e GER), `COLUNAS_AUDITORIA_RELATORIO` de `src/tratamento/programacao.py` (PROG) e `COLUNAS_AUDITORIA_CADASTRO` de `src/analises/etapa.py` (CAD).

### 2.8 CSV (`perfil_estatistico_anual.csv`)

Na hidrelétrica com EVT, uma linha por ano civil da série, com as mesmas colunas da aba INDICADORES_ANUAIS; `;` como separador, ponto decimal, sem índice. Na São Domingos: 9 linhas. Na usina sem EVT, as colunas da aba BASE_ANUAL (`comum["anuais"]`, uma linha por ano e nível), com o mesmo formato.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | int | ano civil |
| `ano_parcial` | bool | ano sem todas as horas na série |
| `horas_observadas` | int | registros horários do ano |
| `cobertura_pct` | float | horas observadas ÷ horas do ano × 100 |
| `geracao_media_mwmed` | float | média de `val_geracao` |
| `disponibilidade_media_mwmed` | float | média de `val_disponibilidade` |
| `fator_capacidade_pct` | float | geração média ÷ potência instalada × 100 |
| `disponibilidade_relativa_pct` | float | disponibilidade média ÷ potência instalada × 100 |
| `desvio_disponibilidade_referencia_pp` | float | disponibilidade relativa − disponibilidade de referência, em p.p. |
| `geracao_sobre_garantia_fisica_pct` | float | geração média ÷ garantia física × 100 |
| `energia_gerada_mwh` | float | soma de `val_geracao` |
| `evt_mwh` | float | soma de `val_energiavertidaturbinavel` |
| `evt_vertimento_minimo_mwh` | float | EVT das horas com vazão vertida ≤ `analises.vertimento_minimo_m3s` |
| `evt_demais_horas_mwh` | float | EVT das demais horas |
| `participacao_vertimento_minimo_pct` | float | EVT no vertimento mínimo ÷ EVT × 100 |
| `indice_evt_pct` | float | EVT ÷ (geração + EVT) × 100 |
| `horas_com_evt` | int | horas com EVT > 0 |
| `horas_com_evt_pct` | float | horas com EVT ÷ horas observadas × 100 |
| `horas_parada_com_evt` | int | horas com geração ≤ `LIMIAR_GERACAO_PARADA_MW` e EVT > 0 |
| `evt_parada_mwh` | float | EVT dessas horas |
| `horas_indisponibilidade_total` | int | horas com disponibilidade ≤ `LIMIAR_INDISPONIBILIDADE_TOTAL_MW` |
| `horas_disponibilidade_ate_metade` | int | horas com disponibilidade acima desse limiar e até a metade da potência instalada |
| `evt_media_diurna_mw`, `evt_media_noturna_mw` | float | EVT média nas horas de `HORAS_DIURNAS` e de `HORAS_NOTURNAS` |
| `razao_evt_diurna_noturna` | float | razão entre as duas |
| `geracao_media_diurna_mw`, `geracao_media_noturna_mw` | float | geração média nas mesmas janelas |
| `razao_geracao_diurna_noturna` | float | razão entre as duas |
| `horas_com_anomalia` | int | horas com `qualidade_registro` diferente de `OK` |

### 2.9 Relatório da usina sem EVT

Montado por `comum.py`, `secoes_termica.py`, `secoes_renovavel.py`, `secoes_conjunto.py` e `figuras_comum.py`, só a partir de `ResultadosAnalise` e do perfil. Os arquivos são os mesmos de 2.1; o PDF e o Markdown seguem 2.2 e 2.5, com as diferenças abaixo.

#### 2.9.1 Capa

| Elemento | Conteúdo | Origem |
|---|---|---|
| Título | "`<usina.nome>` — Análise do desempenho operacional", o mesmo da hidrelétrica com EVT | `comum.titulo_relatorio` |
| Subtítulo | "Análise dos dados abertos do ONS · `<início>` a `<fim>` · `<N>` registros horários da série de referência, `<série>` · Gerado em `<dd/mm/aaaa HH:MM>`"; a série é "Geração por usina (id ONS X)", "Geração por usina (conjunto de usinas, id ONS CJU_…)" ou, na eólica ou solar com série própria, "Restrição com detalhe (id ONS X; CEG Y)" | `comum.subtitulo_capa`, `serie_referencia_texto` |
| "Identificação nos dados do ONS" (`bloco_identificacao_comum`) | Tipo · modalidade; CEG; id ONS (quando há); Conjunto de usinas (id e nome, quando há); Programação diária (códigos); Estado; Subsistema e Códigos de planejamento (térmicas com o despacho, com o período de cada código); Agente atual ("A (proprietário e operador)" ou "A (proprietário); B (operador)"), quando a Capacidade de geração o traz | `comum.pares_identificacao`, `texto_agentes` |
| "Cadastro no ONS" (`bloco_cadastro`) | o mesmo da hidrelétrica com EVT | `conteudo.pares_identificacao_cadastro` |
| "Parâmetros técnicos da usina" (`bloco_parametros`) | Potência instalada com as unidades ("N × P MW" ou "N unidades: a, b e c MW"); Combustível; Garantia física; IP / TEIF de referência; Início da operação comercial, quando o perfil os traz | `comum.pares_parametros` |
| Indicadores principais (`tab_capa_indicadores_comum`) | até quatro cartões: para cada nível da série, "Geração média" (com "do conjunto <nome>" no nível do conjunto), com a energia e as horas com valor, seguido do indicador do tipo — "Fator de capacidade" e "Energia cortada" (eólicas e solares, com a série da usina), "Horas com despacho" (térmicas com o despacho, com a série da usina) ou "Horas com geração até 1 MW" (demais); "Disponibilidade operacional média" (com a Disponibilidade por usina); "Disponibilidade apurada pelo ONS (DISPF)", com a TEIFa e o mês (com os indicadores). Nota: indicadores calculados a partir da série de referência e da disponibilidade publicadas, que não substituem os índices regulatórios; com números do conjunto, que eles são da soma das usinas e não são divididos | `comum.indicadores_capa` |

Na capa com três blocos, a identificação ocupa 26 % da largura, com a coluna das chaves de 82 pt (`BLOCOS_CAPA_TRES["bloco_identificacao_comum"]`).

#### 2.9.2 Seções

Seções com `caminhos=("sem_evt",)`, na ordem de `estrutura.SECOES`, filtradas pelo tipo da usina (`tipos`) e pela condição de presença; a conclusão é a mesma dos dois caminhos. As seções sem construtor próprio no PDF são desenhadas por `_secao_blocos`, e no Markdown por `_md_blocos`, a partir de `comum.blocos_secao(res, chave)`.

| Chave | Título | Tipos | Presente | Blocos, na ordem (chaves do mapa de fontes) |
|---|---|---|---|---|
| `fonte_cobertura` | Fonte e cobertura dos dados | todos | sempre | `tab_fonte_cobertura` (chave × valor); `tab_niveis`; `tab_trechos`, com mais de um trecho ou com a usina em conjunto |
| `usina_no_conjunto` | A usina no conjunto | todos | `em_duas_partes(res)` | texto do que o ONS publica da usina isolada e de onde obter a geração dela; `tab_usina_peso_potencia` |
| `anuais_comum` | Indicadores anuais | todos | fora das duas partes | `tab_anuais_comum` |
| `disponibilidade_geracao_comum` | Disponibilidade e geração por ano | UHE, PCH, CGH, UTE, UTN | `comum["disponibilidade"]` | `tab_disponibilidade_anual_comum`; `tab_eventos_indisponibilidade_comum` ou "Nenhum período com essa duração." |
| `indicadores_ons_comum` | Indicadores oficiais do ONS por unidade geradora | UHE, PCH, CGH, UTE, UTN | `res.ons` | `tab_ons_disp_anual_comum`, `tab_ons_decomposicao`, `tab_ons_ug_anual`, `tab_ons_horas`, `tab_ons_divergencias`, cada uma com linhas |
| `serie_temporal_comum` | Série temporal da geração e da disponibilidade; EOL e UFV: Série temporal da geração | todos | fora das duas partes | figura `serie_temporal_comum` (01) |
| `geracao_mensal` | Geração mensal e sazonalidade | todos | fora das duas partes | figura `geracao_mensal` (02); figura `sazonalidade` (03) ou o texto "Sazonalidade omitida: a série tem N meses distintos, abaixo dos 12 necessários." |
| `perfil_horario_comum` | Perfil horário da geração | todos | fora das duas partes | figura `perfil_horario_comum` (04) |
| `despacho_motivo` | Geração por motivo de despacho e inflexibilidade | UTE, UTN | `res.termica` | texto do período e das unidades; `tab_motivos_termica`; `tab_despacho_anual`; figuras `despacho_motivo_mensal` (06) e `inflexibilidade_mensal` (07), conforme a base |
| `atendimento_despacho` | Atendimento ao despacho | UTE, UTN | `res.termica` | `tab_atendimento_anual`; `tab_maiores_desvios` e figura `desvios_despacho` (08), ou "Nenhuma hora com desvio além de 5 MW." |
| `disponivel_sem_despacho` | Disponível sem despacho; com o CVU × CMO, Disponível sem despacho e CVU × CMO | UTE, UTN | `termica["disponivel_sem_despacho"]` ou `termica["cvu_cmo"]` | `tab_disponivel_anual`; `tab_cvu_cmo` e figura `cvu_cmo` (09) |
| `fator_capacidade` | Fator de capacidade | EOL, UFV | `renovavel["fator_capacidade"]` | texto do calculado, com série própria; `tab_fc_anual`; figura `fc_mensal` (10) |
| `energia_cortada` | Energia cortada por restrição de operação (constrained-off) | EOL, UFV | `renovavel["restricao"]` | texto do período e das semi-horas restritas; `tab_corte_anual`; `tab_corte_razao` e figura `corte_razao_mensal` (11), ou "Nenhuma semi-hora com a marca de restrição." |
| `recurso_geracao` | Recurso × geração | EOL, UFV | `renovavel["recurso"]` | texto das faixas e das semi-horas válidas; `tab_recurso_faixas` e figura `recurso_geracao` (12) |
| `conjunto` | Composição e geração do conjunto | todos | `res.conjunto`, fora das duas partes | `tab_conjunto_trechos`; figura `conjunto_mensal` (14); `tab_conjunto_composicao` |
| `programacao_comum` | Programação diária × geração verificada | todos | `comum["programacao"]`, fora das duas partes | texto do nível, do período, das horas comuns, da correlação e dos dias sem arquivo; `tab_programacao_mensal_comum`; `tab_programacao_eventos_comum`; nas eólicas e solares, `tab_desvios_programacao_renovavel` e figura `desvio_programacao` (13) |
| `disponibilidade_sincronizada_comum` | Disponibilidade operacional e sincronizada (ONS) | UHE, PCH, CGH, UTE, UTN | `comum["disponibilidade"]` | figura `disponibilidade_comum` (05) |
| `hidrologia_comum` | Afluência, vertimento e nível do reservatório (ONS) | UHE, PCH, CGH | `res.hidrologia` | com `publicado`: `tab_hidrologia_anual_comum` e figura `hidrologia_mensal_comum` (15); sem ele, só a constatação |
| `qualidade_comum` | Qualidade dos dados | todos | sempre | `tab_sinalizacoes` ou "Nenhuma hora sinalizada."; `tab_ausencias` ou "Nenhuma hora ausente." |
| `parte_conjunto` | Operação do conjunto `<nome>` (`<id>`) | todos | `em_duas_partes(res)` | subseções (`Bloco("subtitulo")`) "Indicadores anuais do conjunto", "Série temporal da geração do conjunto", "Geração mensal e sazonalidade do conjunto", "Perfil horário da geração do conjunto", os blocos de `conjunto` e "Programação diária × geração verificada do conjunto" (com a programação), cada uma com os blocos da seção correspondente |
| `conclusao` | Conclusão | todos | sempre | frase de abertura e listas, ou a frase de `frase_sem_itens` |
| `notas_comum` | Notas metodológicas e limitações | todos | sempre | notas (`comum.notas`); `tab_omitidos` e `tab_nao_aplicaveis`, com linhas; `tab_parametros_comum` |

`em_duas_partes(res)`: a usina tem a seção do conjunto (`res.conjunto` não vazio) e todas as horas da base horária comum são do nível do conjunto.

#### 2.9.3 Tabelas

Cabeçalhos fixos, em `comum.py` e nos módulos das seções do tipo; os subtítulos e as notas em `comum.textos_tabelas`. As colunas entre colchetes só entram quando o tipo ou a base as têm.

| Chave | Cabeçalho | Linhas |
|---|---|---|
| `tab_fonte_cobertura` | pares item × valor: Série de referência (com o endereço no portal), Período, Registros (horas observadas, esperadas, ausentes em N intervalos, sem valor), Níveis (horas por nível), Anos parciais, [Trechos] | — |
| `tab_niveis` | Conjunto do ONS, Nível, Identificador, Obtenção | série de referência; Geração por usina (na série da restrição); Programação diária; Disponibilidade por usina; Fator de capacidade; Restrição com a razão; Restrição com detalhe; Indicadores de desempenho do ONS; Modalidade das usinas; Composição dos conjuntos de usinas; Capacidade de geração (usinas do conjunto); Dados hidrológicos horários — os carregados |
| `tab_trechos` | Trecho, Início, Fim, Modalidade, Nível, [Composição (CEG), sem a seção do conjunto], Tipos | um trecho por linha (`res.trechos`) |
| `tab_anuais_comum` | Ano, Nível, Horas, Com valor, Geração média (MWmed), Energia (MWh), Máxima (MW), Horas até 1 MW, % das horas, [Fator de capacidade], [Disp. média (MW), Disp. (% Pinst)], [Disp. sem despacho (h)], [Energia cortada (MWh, % est.)] | ano × nível |
| `tab_disponibilidade_anual_comum` | Ano, Horas com o dado, Disp. operacional (MW), Disp. (% Pinst), Disp. sincronizada (MW), Geração (MW), Horas indisp. total, Horas paradas disponível, Horas geração > disp. | um ano por linha |
| `tab_eventos_indisponibilidade_comum` | Início, Fim, Duração (h), Geração média (MW) | até `NUMERO_EVENTOS_RELATORIO` eventos de pelo menos 24 h, os mais longos |
| `tab_ons_disp_anual_comum` | Ano, Disp. operacional (% Pinst), DISPF (média das UGs), Indisp. programada, Indisp. forçada, Δ DISPF vs ref. GF | um ano por linha |
| `tab_ons_decomposicao`, `tab_ons_ug_anual`, `tab_ons_horas`, `tab_ons_divergencias` | os da hidrelétrica com EVT (2.4) | idem |
| `tab_programacao_mensal_comum` | Mês, Horas comuns, Verificada (MW), Programada (MW), Desvio médio (MW), Desvio absoluto (MW), Horas parada c/ programação | um mês por linha |
| `tab_programacao_eventos_comum` | Início, Fim, Duração (h), Programação média (MW) | até `NUMERO_EVENTOS_RELATORIO` eventos, os mais longos |
| `tab_sinalizacoes` | Código, Descrição, Horas, % das horas | um código por linha |
| `tab_ausencias` | Tipo (horas, mês sem a usina, mês sem arquivo), Início, Fim, Horas | até `NUMERO_EVENTOS_RELATORIO` intervalos, os mais longos, em ordem cronológica |
| `tab_omitidos` | Seção ou regra, Motivo | `res.omitidos` |
| `tab_nao_aplicaveis` | Conferência, Motivo | `comum["conferencias_nao_aplicaveis"]`, com a descrição do catálogo das conferências |
| `tab_parametros_comum` | Grupo, Parâmetro, Valor, Unidade, Origem | `res.parametros` (seção 3) |
| `tab_usina_peso_potencia` | Composição, Início, Fim, Potência da usina (MW), Potência das usinas do conjunto (MW), Peso da usina | um trecho de composição por linha; "—" com as unidades da usina fora de operação |
| `tab_hidrologia_anual_comum` | as de `tab_hidrologia_anual` | um ano por linha |
| `tab_motivos_termica` | Motivo, Programada (MWh), Verificada (MWh), % da programada, % da verificada | os motivos com energia no período, os de detalhe marcados "(detalhe)", e o total |
| `tab_despacho_anual` | Ano, Programada (MWh), Verificada (MWh), Horas com despacho, Inflexibilidade programada (MWh), Inflexibilidade verificada (MWh) | um ano por linha |
| `tab_atendimento_anual` | Ano, Horas com programação, Horas abaixo, Energia abaixo (MWh), Horas acima, Energia acima (MWh), Horas sem programação, com geração, Energia sem programação (MWh) | um ano por linha |
| `tab_maiores_desvios` | Hora, Programada (MW), Verificada (MW), Desvio (MW) | até `NUMERO_EVENTOS_RELATORIO` horas, as de maior desvio absoluto |
| `tab_disponivel_anual` | Ano, Horas com disponibilidade e despacho, Horas disponíveis sem despacho, % das horas, Potência disponível média nelas (MW) | um ano por linha |
| `tab_cvu_cmo` | Unidade de planejamento, Semanas, CVU abaixo do CMO (semanas), Geração nessas semanas (MWh), CVU acima do CMO (semanas), Geração nessas semanas (MWh), CVU igual ao CMO (semanas), Sem comparação (semanas) | uma unidade de planejamento por linha |
| `tab_fc_anual` | Ano, Nível, Horas, Geração verificada (MWh), Capacidade média (MW), FC publicado, [FC calculado (usina)], Horas com FC fora de 0 a 1, Horas acima da capacidade | ano × nível |
| `tab_corte_anual` | Ano, Verificada (MWh), Estimada (MWh), Cortada (MWh), % da estimada, Horas restritas, Restritas sem estimativa, Semi-horas sem a marca, Diferença bruta (MWh) | um ano por linha |
| `tab_corte_razao` | Razão, Semi-horas restritas, Energia cortada (MWh), % da cortada | REL, CNF, ENE e sem razão publicada, as que têm semi-horas |
| `tab_recurso_faixas` | Faixa de `<vento ou irradiância>` (`<m/s ou W/m²>`), Semi-horas, Geração verificada média (MW), Geração estimada média (MW) | uma faixa por linha |
| `tab_desvios_programacao_renovavel` | Hora, Programada (MW), Verificada (MW), Desvio (MW) | até `NUMERO_EVENTOS_RELATORIO` horas, no nível da programação |
| `tab_conjunto_trechos` | Trecho, Início, Fim, Usinas, Tipos, Horas com valor, Energia (MWh), Média (MWmed), Máxima (MW), [Potência somada (MW)] | um trecho de composição por linha |
| `tab_conjunto_composicao` | Usina, Tipo, CEG, Entrada no conjunto, Saída, [Potência (MW)] | uma usina da composição por linha, por tipo, entrada e nome |

#### 2.9.4 Figuras

Nomes em `figuras_comum.NOMES_FIGURAS_COMUM` (sempre) e `NOMES_FIGURAS_COMUM_OPCIONAIS` (com a condição de `_CONDICOES`); 300 DPI; todas com 11 × 4,3 polegadas (`TAMANHO_FIGURA_PADRONIZADA`). No PDF, as de `FIGURAS_PADRONIZADAS_COMUM` (01 a 05) ocupam a largura útil; as demais ficam limitadas a 285 pt de altura.

| Arquivo | Chave | Marca seaborn | Dados | Gerada |
|---|---|---|---|---|
| `01_serie_temporal_geracao_disponibilidade.png` | `serie_temporal_comum` | `lineplot` | `comum["serie_diaria"]`, por nível, e a disponibilidade operacional; potência instalada com a série da usina | sempre |
| `02_geracao_mensal.png` | `geracao_mensal` | `histplot` com pesos | `comum["mensal"]`, por nível | sempre |
| `03_geracao_por_mes_do_ano.png` | `sazonalidade` | `barplot` | `comum["sazonalidade"]` | com pelo menos 12 meses distintos |
| `04_perfil_horario_geracao.png` | `perfil_horario_comum` | `lineplot` | `comum["perfil_horario"]` | sempre |
| `05_disponibilidade_operacional_sincronizada_mensal.png` | `disponibilidade_comum` | `lineplot` | `comum["disponibilidade"]["mensal"]`; potência instalada | com a Disponibilidade por usina |
| `06_despacho_por_motivo_mensal.png` | `despacho_motivo_mensal` | `histplot` empilhado e `scatterplot` do total | `termica["motivos_mensal"]` | térmica com geração no período |
| `07_inflexibilidade_mensal.png` | `inflexibilidade_mensal` | `histplot` lado a lado | `termica["inflexibilidade"]` | térmica com inflexibilidade programada ou verificada |
| `08_desvios_despacho_mensal.png` | `desvios_despacho` | `histplot` para cima e para baixo | `termica["atendimento"]["mensal"]` | térmica com os maiores desvios |
| `09_cvu_cmo_semanal.png` | `cvu_cmo` | `lineplot`, interrompido na semana sem comparação | `termica["cvu_cmo"]["semanal"]` | térmica com o CVU × CMO |
| `10_fator_capacidade_mensal.png` | `fc_mensal` | `lineplot`, o calculado tracejado | `renovavel["fator_capacidade"]["mensal"]` e `comum["mensal"]` da usina | com o Fator de capacidade |
| `11_energia_cortada_por_razao_mensal.png` | `corte_razao_mensal` | `histplot` empilhado | `renovavel["restricao"]["mensal"]` | com semi-hora restrita por razão |
| `12_geracao_por_faixa_de_recurso.png` | `recurso_geracao` | `barplot` da verificada e `lineplot` da estimada | `renovavel["recurso"]["faixas"]` | com faixas do recurso |
| `13_desvio_programacao_mensal.png` | `desvio_programacao` | `histplot` do desvio absoluto e `scatterplot` do desvio médio | `comum["programacao"]["mensal"]` | eólica ou solar com os maiores desvios |
| `14_geracao_do_conjunto_por_trecho.png` | `conjunto_mensal` | `lineplot` por trecho e da potência somada; linhas verticais nas mudanças | `conjunto["mensal"]` e `conjunto["trechos"]` | com a seção do conjunto |
| `15_vazoes_mensais.png` | `hidrologia_mensal_comum` | `lineplot`; linha do engolimento máximo | `hidrologia["mensal"]` | hidrelétrica sem EVT com `publicado` |

O eixo do tempo tem marcas por ano a partir de 3 anos, por mês abaixo disso e por dia nas séries diárias de até dois meses; as figuras mensais nunca por dia. A figura opcional que não é gerada numa execução sai de `figures/`, como na hidrelétrica com EVT.

#### 2.9.5 Planilha e CSV

Uma aba por quadro, na ordem abaixo, com o mesmo formato de 2.7; cada aba só com linhas, salvo CONSTATACOES, CONCLUSAO, BASE_ANUAL e OMITIDOS, sempre presentes. As colunas são as dos quadros de `ResultadosAnalise` (data-model das Análises).

| Aba | Origem | Presente |
|---|---|---|
| CONSTATACOES | `achados` | sempre |
| CONCLUSAO | `conteudo.tabela_conclusao(res)` | sempre |
| BASE_ANUAL | `comum["anuais"]` | sempre |
| BASE_MENSAL, BASE_MES_DO_ANO, BASE_HORA_DO_DIA | `comum["mensal"]`, `comum["sazonalidade"]`, `comum["perfil_horario"]` | com linhas |
| BASE_SINALIZACOES, GER_AUSENCIAS | `comum["qualidade"]["sinalizacoes"]`, `comum["qualidade"]["ausencias"]` | com linhas |
| TRECHOS | `res.trechos` | com linhas |
| OMITIDOS | `res.omitidos` (`item`, `tipo`, `motivo`) | sempre |
| CONF_NAO_APLICAVEIS | `comum["conferencias_nao_aplicaveis"]` | com linhas |
| PARAMETROS | `res.parametros` | sempre |
| DISP_MENSAL, DISP_ANUAL, DISP_EVENTOS_INDISP_TOTAL | `comum["disponibilidade"]` | com a Disponibilidade por usina |
| PROG_RESUMO_MENSAL, PROG_EVENTOS_DESVIO | `comum["programacao"]` (`mensal`, `eventos`) | com a programação |
| TERM_MOTIVOS_ANUAL, TERM_MOTIVOS_MENSAL, TERM_INFLEXIBILIDADE, TERM_ATENDIMENTO_ANUAL, TERM_ATENDIMENTO_MENSAL, TERM_MAIORES_DESVIOS, TERM_DISP_SEM_DESPACHO, TERM_CVU_CMO_SEMANAL, TERM_CVU_CMO_RESUMO | `res.termica` | com as seções de térmica |
| CONF_G3_MENSAL, CONF_G3_DIVERGENCIAS, CONF_G4_MENSAL, CONF_G4_DIVERGENCIAS | `termica["conferencias"]` | com as seções de térmica |
| REN_FC_ANUAL, REN_FC_MENSAL, REN_CORTE_ANUAL, REN_CORTE_MENSAL, REN_CORTE_RAZAO, REN_RECURSO_FAIXAS, REN_DESVIOS_PROGRAMACAO | `res.renovavel` | com as seções de eólica e solar |
| CONF_G1_PARES, CONF_G1_MENSAL, CONF_G1_DIVERGENCIAS, CONF_G2_MENSAL, CONF_G2_DIVERGENCIAS, CONF_G5_MENSAL, CONF_G5_DIVERGENCIAS | `renovavel["conferencias"]` | com as seções de eólica e solar |
| CONJ_TRECHOS, CONJ_COMPOSICAO, CONJ_MENSAL, CONJ_TIPO_PUBLICADO | `res.conjunto` | com a seção do conjunto |
| CONJ_PESO_USINA | `conjunto["peso_usina"]` | no relatório em duas partes |
| HID_ALINHAMENTO, HID_MENSAL, HID_ANUAL, HID_AUSENCIAS, HID_AUDITORIA | `res.hidrologia` | hidrelétrica sem EVT, com os Dados hidrológicos |
| ONS_*, CAD_FICHA, CAD_AUDITORIA, DICIONARIOS | como em 2.7 (`planilha._abas_complementares`) | como em 2.7 |
| FONTES | `fontes.tabela_fontes_abas(res, abas)` | sempre, por último |

O CSV traz `comum["anuais"]` (2.8).

### 2.10 Resumo executivo

Montado por `resumo.montar_resumo` num objeto único, `ResumoExecutivo`, de onde saem o PDF (`resumo_pdf.gerar_resumo_pdf`) e o Markdown (`resumo.gerar_resumo_md`), com o mesmo conteúdo, na mesma ordem. Não cria dado novo: usa as mesmas funções do relatório completo.

#### 2.10.1 `ResumoExecutivo`

| Campo | Conteúdo | Origem |
|---|---|---|
| `nome_usina` | nome da usina | perfil |
| `titulo` | "`<nome da usina>` — resumo executivo" | perfil |
| `subtitulo` | "`<início>` a `<fim>` (`<N>` registros horários) · Gerado em `<dd/mm/aaaa HH:MM>`" | `res.cobertura` e a data de geração da execução |
| `cabecalho_pagina` | cabeçalho das páginas, no PDF: "Resumo executivo — `<nome>` · `<início>` a `<fim>`" | perfil e `res.cobertura` |
| `identificacao` | linhas do cabeçalho (2.10.2) | perfil, `res.tipo` e a identificação da capa |
| `referencia_relatorio` | 'Resume o relatório completo "`<título da capa>`", de `<n>` páginas, gerado na mesma data.' | `titulo_capa_relatorio()` e `paginas_do_pdf` do PDF recém-gerado |
| `termos` | lista de (sigla, explicação), só com os termos que aparecem no resumo, na ordem da primeira ocorrência no texto corrido (que segue a ordem dos blocos) | `GLOSSARIO_RESUMO` (5.6) |
| `frase_conclusao` | `FRASE_ABERTURA_CONCLUSAO` com itens; sem itens, a frase de `frase_sem_itens(res)` | sem alteração |
| `listas_conclusao` | as listas da conclusão, cada uma com título e itens | `listas_conclusao(res)`, sem alteração |
| `aviso_secoes` | "As seções e as notas metodológicas citadas são as do relatório completo." | texto geral |
| `indicadores` | `Tabela` com o cabeçalho ["Indicador", "Valor", "Detalhe"], as linhas dos indicadores da capa e a nota "Seção de origem: capa do relatório completo." | `conteudo.indicadores_capa(res)` ou `comum.indicadores_capa(res)` |
| `evolucao_anual` | `Tabela` com as colunas escolhidas, as linhas e a nota "[* Ano parcial. ]Colunas e definições na seção `<n>` do relatório completo."; `None` quando omitida ou sem tabela anual | `conteudo.linhas_tabela_anual(res)` ou `comum.linhas_tabela_anuais(res)` e `COLUNAS_RESUMO_ANUAL` (2.10.3) |
| `remissao_anual` | "A evolução anual está na seção `<n>` do relatório completo.", quando a evolução anual é omitida pela regra das duas páginas | número da seção em `secoes_presentes(res)`: `indicadores_anuais`; na usina sem EVT, `anuais_comum` ou, no relatório em duas partes, `parte_conjunto` |
| `sobre_os_dados` | três parágrafos (2.10.4) | `res.cobertura`, `res.globais` ou `comum["qualidade"]`, `res.indicadores_anuais` e `fontes.py` |

`Tabela` tem `cabecalho`, `linhas` (os textos já formatados do relatório completo) e `nota`. O método `blocos()` dá os blocos presentes, na ordem fixa (`TITULOS_BLOCOS`): Indicadores-chave, Evolução anual, Sobre os dados e Conclusão; a evolução anual só falta quando não há tabela anual.

#### 2.10.2 Linhas do cabeçalho

| Linha | Conteúdo |
|---|---|
| tipo, estado, modalidade e potência | "`<tipo>` · `<UF>` · `<modalidade>` · `<potência>` MW" (exemplo, perfil da São Domingos: "UHE · MS · TIPO II-A · 48,0 MW") |
| agentes | na hidrelétrica com EVT, "Agente: …" ou "Agentes: …", com o mesmo texto da linha "Agente" da capa, cada um com o seu período; na usina sem EVT, "Agente atual (Capacidade de geração do ONS): …" |
| referência ao relatório completo | `referencia_relatorio` |
| termos | "**Termos.** `<sigla>`: `<explicação>`; …" |

Linha sem dado é omitida.

#### 2.10.3 `COLUNAS_RESUMO_ANUAL` (`src/relatorio/resumo.py`)

Mapa caminho → cabeçalhos da tabela anual do relatório que entram no resumo, em ordem.

| Caminho | Colunas |
|---|---|
| `evt` (hidrelétrica com EVT) | Ano, Disp. média (% Pinst), Fator de capacidade, Geração / GF, EVT (MWh), Horas parada c/ EVT; um cabeçalho ausente na tabela levanta `KeyError` |
| `sem_evt` | Ano, Nível, Geração média (MWmed), Energia (MWh), Fator de capacidade, Disp. (% Pinst), Disp. sem despacho (h), Energia cortada (MWh, % est.), só as que a tabela da usina tem, nesta ordem (no máximo seis por tipo) |

#### 2.10.4 Parágrafos de "Sobre os dados" (no máximo 250 palavras)

| Parágrafo | Conteúdo | Números iguais aos de |
|---|---|---|
| Dados | hidrelétrica com EVT: início, fim, registros e anos parciais; registros que violam ao menos uma regra de plausibilidade física, com a quantidade e a parcela (`globais["horas_com_anomalia"]`), mantidos nos totais. Usina sem EVT: a série de referência com o identificador e o nível, início, fim, registros, anos parciais e horas ausentes, não preenchidas; as horas sinalizadas (`comum["qualidade"]["horas_sinalizadas"]`), com a parcela, mantidas nos totais | seção de cobertura; seção de qualidade |
| Conferências e limites | "Conferências: " com o texto curto de cada conferência feita (`texto_conferencia_curto`; na usina sem EVT, só as de `CONFERENCIAS_SEM_EVT`); "Os dados abertos do ONS não informam a causa das paradas nem os eventos individuais de desligamento." | textos longos das mesmas conferências nas legendas |
| Fontes | "Fontes: " com os conjuntos carregados, agrupados por identificador (com o nível) e data de obtenção (`fontes_resumo`) | legendas de fonte |

Acima de `RESUMO_MAXIMO_PALAVRAS_DADOS` palavras, `ValueError`.

#### 2.10.5 Textos curtos das conferências (`src/relatorio/fontes.py`)

Cada conferência do mapa de `fontes.py` tem um texto curto, montado com os mesmos resultados e os mesmos números do texto longo. Exemplos (perfil da São Domingos; o código não tem número fixo):

| Conferência | Texto longo (legenda) | Texto curto (resumo) |
|---|---|---|
| geração | geração conferida com Geração por usina: 70.895 de 70.895 horas coincidentes (100,0%) | geração coincidente com Geração por usina em 100,0% das horas |
| disponibilidade | disponibilidade declarada conferida com Disponibilidade por usina (operacional): … | disponibilidade declarada coincidente com Disponibilidade por usina em …% das horas |
| vazões | vazões turbinada e vertida conferidas com Dados hidrológicos horários: … | vazões turbinada e vertida coincidentes com Dados hidrológicos horários em …% das horas |
| TEIFa e TEIP | … `<m>` de `<n>` meses reproduzidos (diferença máxima de `<x>` p.p.) | TEIFa e TEIP refeitas em `<m>` de `<n>` meses |
| DISPF × horas | … `<n>` divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS | DISPF e horas por estado operativo com `<n>` divergências (meses-unidade) |
| cadastro | … sem divergência | cadastro sem divergência |
| G1 a G5 e hora da hidrologia | os da FR-026 | a parcela de horas coincidentes, com as divergências; a hora da hidrologia confirmada ou não, com a correlação |

Conferência não feita nesta execução: o texto curto diz "`<dado>`: conferência não feita nesta execução".

#### 2.10.6 Documento

Markdown (`gerar_resumo_md`), na ordem: `# <titulo>`; subtítulo; as linhas de identificação; a referência ao relatório; `**Termos.** …`; para cada bloco, `## <título>`:
- **Indicadores-chave**: a tabela e a nota;
- **Evolução anual**: a tabela e a nota (com `*` escapado), ou a frase de remissão;
- **Sobre os dados**: os três parágrafos;
- **Conclusão**: `aviso_secoes`, a frase e, para cada lista, `### <lista>` e os itens `- `, com as mesmas linhas da seção de conclusão do Markdown do relatório.

PDF: A4 retrato, margens e fontes do relatório; texto em `RESUMO_CORPO_PT` (10 pt) com entrelinha de 13 pt; tabelas em `RESUMO_TABELA_PT` (9 pt), com as larguras dos indicadores 29 %, 12 % e 59 % e a coluna do ano da evolução anual com 10 %; itens da conclusão com "• "; título de cada lista junto do primeiro item, sem bloco indivisível na conclusão; rodapé com a numeração e o cabeçalho `cabecalho_pagina`; metadados com o título do resumo. `gerar_resumo_pdf` devolve os blocos emitidos, na ordem, para a verificação de que o PDF e o Markdown têm os mesmos blocos.

## 3. Objetos em memória e entre etapas

A etapa não grava pickle: as suas saídas são finais. Ela completa `ResultadosAnalise` em memória (`etapa.completar_resultados`), sem regravar `resultados.pkl`:

| Campo | Tipo | Conteúdo |
|---|---|---|
| `res.parametros` | DataFrame `grupo`, `parametro`, `valor`, `unidade`, `origem` (texto) | hidrelétrica com EVT: `parametros.tabela_parametros(com_indicadores, com_programacao)`: grupos `Usina` (12 linhas do perfil, com a fonte de `parametros.fontes`), `Derivado` (engolimento máximo, disponibilidade de referência e produtividade nominal, com a fórmula), `Análise` e `Validação` (limiares, origem "Parâmetro de análise" e, quando há, a base do limiar) e `Fonte` (conjunto e endereço; identificador da usina nas linhas dos indicadores, da programação e das bases complementares); mais as linhas de `parametros_disponibilidade`, `parametros_hidrologia` e `parametros_geracao_cadastro`, com período e data de obtenção. Na São Domingos, 41 linhas. Usina sem EVT: `comum.tabela_parametros(res)`, com os grupos `Usina` (tipo e modalidade, potência, unidades, combustível, garantia física e início da operação comercial), `Análise`, `Validação` e `Fonte` (série de referência, programação, disponibilidade, cadastro, despacho, CVU, CMO, Fator de capacidade e restrições, conforme o tipo) |
| `res.fontes` | dict | `obtencao`: {id do conjunto: data UTC em texto, ou ""}; `carregados`: ids dos conjuntos cujos dados entraram. Hidrelétrica com EVT: `evt` sempre; os quatro de indicadores com `res.ons`; `programacao`, `disponibilidade`, `hidrologia`, `geracao` e `cadastro` com o campo correspondente. Usina sem EVT: `geracao` sempre; os de indicadores; `programacao`, `disponibilidade`, `cadastro`, `composicao` (com o conjunto no perfil), `capacidade` (com os agentes), `capacidade_membros`, `hidrologia`, `despacho`, `cvu`, `cmo` e, conforme o nível coletado, `fator_capacidade`, `restricao_detalhe` e `restricao_razao` |

Estruturas da etapa:

| Estrutura | Módulo | Campos |
|---|---|---|
| `Secao` (dataclass imutável) | `estrutura` | `chave: str`; `titulo`: texto, mapa tipo → título (chave "" como padrão) ou função dos resultados; `presente: Callable[[res], bool]` (padrão: sempre); `caminhos` (`evt`, `sem_evt` ou os dois; padrão `evt`); `tipos` (filtram o caminho sem EVT; padrão: todos); `periodo_minimo_meses` (opcional) |
| `Bloco` (dataclass) | `comum` | `tipo` (`chave_valor`, `tabela`, `figura`, `texto`, `subtitulo`, `notas` ou `sem_linhas`), `chave` (do mapa de fontes), `cabecalho`, `linhas`, `larguras`, `numericas`, `intro`, `textos`, `pares` |
| `Conjunto` (dataclass imutável) | `fontes` | `nome: str`; `identificador: str`, modelo com `{cod_usina}`, `{ceg}`, `{id_ons}`, `{cod_programacao}`, `{id_reservatorio}`, `{id_conjunto}`, `{planejamento}`, `{subsistema}`; `catalogo: str` (vazio em `projeto`; `variante` nas restrições) |
| `Conferencia` (dataclass imutável) | `fontes` | `dado: str`; `base: str`, id do conjunto que permite a conferência; `texto: Callable[[res], str]`; `texto_curto: Callable[[res], str]` |
| `Entrada` (dataclass imutável) | `fontes` | `conjuntos`, `conferencias`, `sem_outra_fonte` (tuplas), `calculado: bool` e `todos: bool` (cita os conjuntos mesmo quando não carregados) |
| dicionário de figuras | `figuras.gerar_graficos` | {chave: caminho do PNG}, só as figuras geradas; passado ao Markdown e ao PDF |
| `PDFReportGenerator` | `pdf` | depois de `build_pdf`: `titulos_secoes`, `constatacoes_emitidas`, `legendas_emitidas` (chaves), `paginas_secoes` ({título: página}), `sumario_entradas` ([(n, título, página)]), `subtitulo_capa`; contadores `_desenhados` e `_legendas` |
| `ResumoExecutivo`, `Tabela` | `resumo` | 2.10 |
| `ResultadoEtapa` | `src/pipeline.py` | `codigo`, `arquivos` (PDF, Markdown, XLSX, CSV, resumo em PDF e em Markdown e figuras, em ordem), `resumo` |
| diferenças do `comparar` | `src/comum/comparacao.py` | lista de textos, um por diferença (formatos no [contrato](contracts/cli-relatorio.md)) |
| `Recorte`, `UsinaComResultado`, `UsinaSemResultado`, `Carteira`, `TabelaCarteira`, `Bloco`, `Documento` | `carteira` | seção 6 |

## 4. Manifesto da etapa (`etapa.json`)

Campos comuns (`etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status`, `codigo_saida`, `etapa_anterior`, `arquivos`, `resumo`) e status no [data-model da Coleta](../001-coleta-dados/data-model.md), seção 4. Nesta etapa:
- fica em `reports/<slug>/etapa.json`, não em `data/usinas/<slug>/`;
- `versao_formato` é 1;
- `etapa_anterior` é `{"etapa": "analises", "concluida_em": …}`;
- `arquivos` traz, nesta ordem, o PDF, o Markdown, a planilha, o CSV, o resumo executivo em PDF e em Markdown e as figuras, já no lugar final, com o nome relativo à pasta (por exemplo, `figures/01_serie_temporal_disponibilidade_geracao_evt.png`), `bytes` e `sha256`; com falha, fica vazio, e as saídas da execução anterior continuam na pasta. É dessa lista que o `referencia` tira os arquivos do relatório de referência;
- como última etapa, não marca nenhuma outra como `desatualizada`; ela própria fica `desatualizada` quando uma etapa anterior é concluída de novo;
- o `comparar` ignora o arquivo.

`resumo` (`etapa.executar_relatorio`):

| Campo | Tipo | Significado |
|---|---|---|
| `data_geracao` | texto `dd/mm/aaaa HH:MM` | `--data-geracao`, ou a hora da execução; a mesma do PDF, do Markdown e do resumo executivo; conferida pelo `referencia` |
| `secoes` | int | seções presentes (`len(secoes_presentes(res))`) |
| `paginas_pdf` | int | objetos `/Type /Page` do PDF (`paginas_do_pdf`) |
| `figuras` | int | figuras geradas |
| `abas_planilha` | int | abas da planilha |
| `resumo_executivo` | dict | `paginas` (páginas do PDF do resumo), `evolucao_anual` (falso quando omitida pela regra das duas páginas) e `palavras` (fora das tabelas, no Markdown) |

Com falha (código 1), o `resumo` é `{"erro": "<mensagem>"}`; com a interrupção pelo usuário, `{"erro": "interrompida pelo usuário"}`. Na São Domingos: `{"data_geracao": "07/10/2026 08:53", "secoes": 17, "paginas_pdf": 30, "figuras": 8, "abas_planilha": 58, "resumo_executivo": {"paginas": 2, "evolucao_anual": true, "palavras": 933}}`.

## 5. Regras, estados e validações

### 5.1 Presença

| Elemento | Condição | Onde |
|---|---|---|
| caminho do relatório | `sem_evt(res)`: `res.comum` não vazio | `estrutura.caminho` |
| seções `indicadores_ons`, `programacao`, `disponibilidade_sincronizada`, `hidrologia`, `geracao_oficial` | campo correspondente de `ResultadosAnalise` não vazio | `estrutura.SECOES` |
| demais seções da hidrelétrica com EVT | sempre | `estrutura.SECOES` |
| seções da usina sem EVT | tipo da usina em `Secao.tipos` e a condição de 2.9.2 | `estrutura.SECOES` |
| tabelas e figuras de cruzamento hidrológico | `hidrologia["publicado"]`, a conferência das vazões na meta (na usina sem EVT, a hora confirmada pela geração) | `pdf._secao_hidrologia`, `markdown._md_conteudo_secao`, `comum.blocos_secao` |
| figuras 06 a 08 da hidrelétrica com EVT | `_GERADORES_OPCIONAIS` (2.6) | `figuras` |
| figuras 03 e 05 a 15 da usina sem EVT | `_CONDICOES` (2.9.4) | `figuras_comum` |
| bloco "Cadastro no ONS" | `res.cadastro` | `pdf._capa`, `markdown.gerar_relatorio_md` |
| cartão do DISPF na capa | `ons["disp_periodo"]` e `ons["taxa_ultima"]` | `conteudo.indicadores_capa`, `comum.indicadores_capa` |
| nota da capa | hidrelétrica com EVT: com `res.ons`, distingue indicadores calculados e apurados pelo ONS; sem, diz que são aproximações. Usina sem EVT: a frase da série de referência e, com o nível do conjunto, a dos números do conjunto | `conteudo.indicadores_capa`, `comum.indicadores_capa` |
| tabela das bases complementares e da qualidade | só com linhas | `pdf`, `markdown` |
| `tab_indicadores_anuais`, `tab_perfil_horario`, `tab_evt_por_nivel`, `tab_geracao_zero`, `tab_parametros` | sempre | `pdf`, `markdown` |
| texto da conferência da geração na seção | sem a constatação "Conferência da geração" | `pdf`, `markdown` |
| notas dos anos parciais, dos indicadores, da programação e das bases complementares | anos parciais existentes; conjunto carregado | `conteudo.notas_metodologicas` |
| parágrafo de granularidade (usina sem EVT) | algum número do relatório é do conjunto | `comum.notas` |
| notas das seções do tipo, do conjunto e dos Dados hidrológicos (usina sem EVT) | a seção correspondente presente | `comum.notas` |
| tabela de trechos | mais de um trecho, ou a usina em conjunto; sem a coluna dos CEGs com a seção do conjunto | `comum.blocos_secao` |
| aba opcional | conjunto carregado e quadro com linhas | `planilha.exportar_tabelas` |
| evolução anual do resumo | tabela anual com linhas e o resumo com até duas páginas com ela | `resumo.gerar_resumo` |

### 5.2 Constatação → seção

Hidrelétrica com EVT (`estrutura.MAPA_CONSTATACOES`):

| Título da constatação | Seção |
|---|---|
| Cobertura dos dados; Cadastro da usina no ONS | `cobertura` |
| Disponibilidade | `indicadores_anuais` |
| Indisponibilidades; Geração e garantia física | `disponibilidade_geracao` |
| Indicadores oficiais de disponibilidade (ONS); Estados operativos das unidades geradoras (ONS) | `indicadores_ons` |
| Energia vertida turbinável; Distribuição ao longo do ano; Mudança de classificação do vertimento pelo ONS | `evt_mensal` |
| Concentração diurna | `perfil_horario` |
| EVT e nível de geração; EVT com a usina parada | `eventos` |
| Programação diária do ONS | `programacao` |
| Disponibilidade sincronizada | `disponibilidade_sincronizada` |
| Afluência e vertimento | `hidrologia` |
| Horas com geração zero | `geracao_zero` |
| Conferência da geração | `geracao_oficial` |
| Qualidade dos dados | `qualidade` |

Título fora do mapa, ou seção ausente: `SECAO_PADRAO` (`cobertura`), com aviso. Na seção, a ordem é a de `res.achados`.

Usina sem EVT (`MAPA_CONSTATACOES_SEM_EVT`; no relatório em duas partes, `MAPA_CONSTATACOES_DUAS_PARTES`, com as diferenças da última coluna); título fora do mapa, ou seção ausente: `SECAO_PADRAO_SEM_EVT` (`fonte_cobertura`), com aviso:

| Título da constatação | Seção | Em duas partes |
|---|---|---|
| Cobertura dos dados; Cadastro da usina no ONS | `fonte_cobertura` | a mesma |
| A usina no conjunto | — | `usina_no_conjunto` |
| Geração | `anuais_comum` | `parte_conjunto` |
| Disponibilidade | `disponibilidade_geracao_comum` | a mesma |
| Programação diária do ONS | `programacao_comum` | `parte_conjunto` |
| Despacho por motivo | `despacho_motivo` | — |
| Atendimento ao despacho | `atendimento_despacho` | — |
| Disponível sem despacho; CVU e CMO | `disponivel_sem_despacho` | — |
| Fator de capacidade | `fator_capacidade` | — |
| Energia cortada | `energia_cortada` | — |
| Recurso × geração | `recurso_geracao` | — |
| Composição do conjunto | `conjunto` | `parte_conjunto` |
| Afluência e vertimento | `hidrologia_comum` | a mesma |
| Qualidade dos dados | `qualidade_comum` | a mesma |

### 5.3 Mapa de fontes (`fontes.MAPA_FONTES`)

`projeto` = parâmetros do projeto. Conferências: `geracao`, `disponibilidade`, `vazoes`, `teifa_teip`, `dispf_horas`, `cadastro` e, no caminho sem EVT, `programacao_despacho` (G3), `verificada_despacho` (G4), `geracao_fontes` (G1), `soma_conjunto` (G2), `programacao_renovaveis` (G5) e `alinhamento_hidrologia`. Dados sem outra fonte: EVT = "energia vertida turbinável (EVT)"; SINC = "disponibilidade sincronizada"; AFL = "afluência"; AFL-N = "afluência e nível do reservatório"; AFL-NV = "afluência, níveis e volume útil"; PROG = "programação diária"; GER = "geração"; MOT = "motivos de despacho"; CVU = "CVU e CMO"; EST = "geração estimada e marca de restrição"; REC = "vento ou irradiância".

Hidrelétrica com EVT:

| Chave | Conjuntos | Conferências | Sem outra fonte | Calculado |
|---|---|---|---|---|
| `bloco_identificacao`, `tab_cobertura` | evt | — | — | não |
| `bloco_parametros`, `tab_parametros` | projeto | — | — | não |
| `bloco_cadastro` | cadastro | cadastro | — | não |
| `tab_capa_indicadores` | evt, dispf_mensal, teif_teip | geracao, disponibilidade, dispf_horas, teifa_teip | EVT | sim |
| `tab_indicadores_anuais` | evt, projeto | geracao, disponibilidade | EVT | sim |
| `tab_eventos_indisponibilidade` | evt | disponibilidade, vazoes | — | sim |
| `tab_perfil_horario`, `perfil_horario` | evt | geracao | EVT | sim |
| `tab_evt_por_nivel`, `serie_temporal` | evt | geracao, disponibilidade | EVT | sim |
| `tab_eventos_parada_evt`, `tab_extremos` | evt | geracao, disponibilidade, vazoes | EVT | sim |
| `tab_geracao_zero` | evt | geracao, disponibilidade | — | sim |
| `tab_regras_validacao`, `tab_registros_sinalizados` | evt | — | — | sim |
| `tab_ons_disp_anual` | evt, dispf_mensal | disponibilidade, dispf_horas | — | sim |
| `tab_ons_decomposicao` | teif_teip_parametro, teif_teip | teifa_teip | — | sim |
| `tab_ons_ug_anual` | dispf_anual | dispf_horas | — | não |
| `tab_ons_horas` | teif_teip_parametro | dispf_horas | — | não |
| `tab_ons_divergencias` | dispf_mensal, teif_teip_parametro | dispf_horas | — | não |
| `tab_programacao_mensal`, `tab_programacao_hora`, `tab_programacao_eventos` | programacao, evt | geracao | PROG, EVT | sim |
| `tab_disponibilidade_anual` | disponibilidade, evt, teif_teip_parametro | disponibilidade, geracao | SINC | sim |
| `tab_disponibilidade_paradas` | disponibilidade, evt, programacao | disponibilidade, geracao | SINC, EVT | sim |
| `tab_disponibilidade_divergencias` | disponibilidade, evt | disponibilidade | — | não |
| `tab_faixas_afluencia`, `tab_faixas_afluencia_evt`, `faixas_afluencia` | hidrologia, evt | vazoes | AFL, EVT | sim |
| `tab_hidrologia_anual` | hidrologia | vazoes | AFL-NV | sim |
| `tab_hidrologia_perfil`, `perfil_hidrologico` | hidrologia, evt | vazoes | AFL-N | sim |
| `tab_geracao_oficial` | geracao, evt | geracao | — | sim |
| `evt_mensal` | evt | — | EVT | sim |
| `disponibilidade_anual` | evt, projeto | geracao, disponibilidade | — | sim |
| `vazoes_defluentes` | evt | vazoes | — | sim |
| `disponibilidade_sincronizada` | disponibilidade, evt | disponibilidade, geracao | SINC | sim |

Usina sem EVT. `referencia` = a série de referência da usina: a Geração por usina ou, na eólica ou solar com série própria, a restrição com detalhe; `geracao_programacao` = a geração comparada com a programação: a Geração por usina do conjunto quando a programação é do conjunto e a referência é a restrição com detalhe da usina, senão a série de referência.

| Chave | Conjuntos | Conferências | Sem outra fonte | Calculado |
|---|---|---|---|---|
| `bloco_identificacao_comum` | cadastro, referencia, capacidade, despacho | — | — | não |
| `tab_capa_indicadores_comum` | referencia, disponibilidade, dispf_mensal, teif_teip, restricao_detalhe | dispf_horas, teifa_teip | GER | sim |
| `tab_fonte_cobertura` | referencia | — | — | não |
| `tab_niveis` | referencia, geracao, programacao, disponibilidade, dispf_mensal, cadastro, composicao, fator_capacidade, restricao_detalhe, restricao_razao | — | — | não |
| `tab_trechos` | referencia, composicao | — | — | sim |
| `tab_anuais_comum` | referencia, disponibilidade, restricao_detalhe, projeto | soma_conjunto | GER | sim |
| `tab_disponibilidade_anual_comum` | disponibilidade, referencia | — | SINC, GER | sim |
| `tab_eventos_indisponibilidade_comum` | disponibilidade, referencia | — | — | sim |
| `tab_ons_disp_anual_comum` | disponibilidade, dispf_mensal | dispf_horas | — | sim |
| `tab_programacao_mensal_comum`, `tab_programacao_eventos_comum` | programacao, geracao_programacao | programacao_renovaveis | PROG, GER | sim |
| `tab_sinalizacoes` | referencia, disponibilidade | — | — | sim |
| `tab_ausencias` | referencia | — | — | não |
| `tab_omitidos`, `tab_nao_aplicaveis` | projeto | — | — | sim |
| `tab_parametros_comum` | projeto | — | — | não |
| `serie_temporal_comum` | referencia, disponibilidade | — | GER | sim |
| `geracao_mensal`, `sazonalidade`, `perfil_horario_comum` | referencia | — | GER | sim |
| `disponibilidade_comum` | disponibilidade, referencia | — | SINC | sim |
| `tab_motivos_termica`, `despacho_motivo_mensal` | despacho | verificada_despacho | MOT | sim |
| `tab_despacho_anual`, `tab_atendimento_anual`, `desvios_despacho` | despacho | programacao_despacho, verificada_despacho | — | sim |
| `tab_maiores_desvios` | despacho | verificada_despacho | — | não |
| `tab_disponivel_anual` | disponibilidade, despacho | verificada_despacho | — | sim |
| `tab_cvu_cmo` | cvu, cmo, despacho | — | CVU | sim |
| `inflexibilidade_mensal` | despacho | — | MOT | sim |
| `cvu_cmo` | cvu, cmo | — | CVU | sim |
| `tab_fc_anual`, `fc_mensal` | fator_capacidade, referencia, projeto | geracao_fontes, programacao_renovaveis | — | sim |
| `tab_corte_anual` | restricao_detalhe | geracao_fontes, soma_conjunto | EST | sim |
| `tab_corte_razao`, `corte_razao_mensal` | restricao_detalhe, restricao_razao | geracao_fontes | EST | sim |
| `tab_recurso_faixas`, `recurso_geracao` | restricao_detalhe | geracao_fontes | REC | sim |
| `tab_desvios_programacao_renovavel` | programacao, geracao_programacao | programacao_renovaveis | — | não |
| `desvio_programacao` | programacao, geracao_programacao | programacao_renovaveis | — | sim |
| `tab_conjunto_trechos`, `conjunto_mensal` | geracao, composicao, capacidade_membros | soma_conjunto | GER | sim |
| `tab_conjunto_composicao`, `tab_usina_peso_potencia` | composicao, capacidade_membros | — | — | sim |
| `tab_hidrologia_anual_comum` | hidrologia, projeto | alinhamento_hidrologia | AFL-NV | sim |
| `hidrologia_mensal_comum` | hidrologia | alinhamento_hidrologia | AFL | sim |

A legenda cita só os conjuntos carregados (e `projeto`); se nenhum da entrada estiver carregado, cita todos os da entrada. Uma entrada com `todos` cita todos os seus conjuntos, carregados ou não (só a linha DICIONARIOS da FONTES). Na usina sem EVT, a conferência sem base nesta execução sai da legenda (fica nas notas), e a programação conferida pela G5 nesta execução deixa de constar como dado sem outra fonte. Na hidrelétrica com EVT, as conferências das eólicas e solares nunca entram.

### 5.4 Abas na FONTES (`fontes._entrada_aba`)

| Aba | Entrada |
|---|---|
| CONSTATACOES, CONCLUSAO | todos os conjuntos carregados e as conferências feitas nesta execução (na usina sem EVT, só as de `CONFERENCIAS_SEM_EVT`); calculado |
| PARAMETROS | `projeto` e os conjuntos carregados |
| DICIONARIOS | os conjuntos do tipo e da cobertura da usina, cada pacote do ONS uma vez, carregados ou não (`todos`); na hidrelétrica com EVT, os mesmos dez conjuntos |
| INDICADORES_ANUAIS, INDICADORES_GLOBAIS | `tab_indicadores_anuais` |
| COBERTURA_POR_ANO | evt, calculado; AGENTES: evt |
| EVT_MENSAL, EVT_MES_DO_ANO | `evt_mensal` |
| EVT_POR_FAIXA_GERACAO | `tab_evt_por_nivel` |
| PERFIL_HORARIO_GERACAO | evt, conferência `geracao`, calculado; PERFIL_HORARIO_EVT: evt, sem outra fonte EVT, calculado |
| EVENTOS_PARADA_COM_EVT, HORAS_GERACAO_ZERO_MES, EVENTOS_INDISP_TOTAL, VALIDACAO_REGRAS, EXTREMOS | `tab_eventos_parada_evt`, `tab_geracao_zero`, `tab_eventos_indisponibilidade`, `tab_regras_validacao`, `tab_extremos` |
| ANOMALIAS, RESUMO_ANOMALIAS | `tab_registros_sinalizados` |
| PERFIL_ESTATISTICO_ANUAL | evt; geracao, disponibilidade, vazoes; EVT; calculado |
| ONS_DISP_ANUAL_USINA, ONS_UG_ANUAL, ONS_DECOMPOSICAO_TAXAS, ONS_DIVERGENCIAS | as tabelas `tab_ons_*` correspondentes (na usina sem EVT, ONS_DISP_ANUAL_USINA: `tab_ons_disp_anual_comum`) |
| ONS_HORAS_UG_ANUAL, ONS_HORAS_UG_MENSAL | `tab_ons_horas` |
| ONS_TEIFA_TEIP | teif_teip, conferência `teifa_teip` |
| PROG_DIAS_AUSENTES, PROG_AUDITORIA_ARQUIVOS | programacao |
| DISP_CONFERENCIA | disponibilidade, evt; conferência `disponibilidade`; DISP_DIVERGENCIAS: `tab_disponibilidade_divergencias` |
| DISP_AUSENCIAS, DISP_AUDITORIA | disponibilidade |
| HID_ALINHAMENTO | hidrologia, evt; conferência `vazoes` (na usina sem EVT: hidrologia, geracao; conferência `alinhamento_hidrologia`) |
| HID_ANUAL, HID_MENSAL | `tab_hidrologia_anual` (na usina sem EVT, `tab_hidrologia_anual_comum` e `hidrologia_mensal_comum`); HID_PERFIL_HORA_DO_DIA: `tab_hidrologia_perfil` |
| HID_AUSENCIAS, HID_AUDITORIA | hidrologia |
| GER_AUSENCIAS, GER_AUDITORIA | geracao (na usina sem EVT, GER_AUSENCIAS: `tab_ausencias`) |
| CAD_FICHA | `bloco_cadastro`; CAD_AUDITORIA: cadastro |
| BASE_ANUAL, BASE_MENSAL, BASE_MES_DO_ANO, BASE_HORA_DO_DIA, BASE_SINALIZACOES | `tab_anuais_comum`, `geracao_mensal`, `sazonalidade`, `perfil_horario_comum`, `tab_sinalizacoes` |
| TRECHOS, OMITIDOS, CONF_NAO_APLICAVEIS, DISP_EVENTOS_INDISP_TOTAL | `tab_trechos`, `tab_omitidos`, `tab_nao_aplicaveis`, `tab_eventos_indisponibilidade_comum` |
| PROG_RESUMO_MENSAL, PROG_EVENTOS_DESVIO (usina sem EVT) | `tab_programacao_mensal_comum`, `tab_programacao_eventos_comum` |
| DISP_MENSAL, DISP_ANUAL (usina sem EVT) | `disponibilidade_comum`, `tab_disponibilidade_anual_comum` |
| TERM_MOTIVOS_ANUAL, TERM_MOTIVOS_MENSAL, TERM_INFLEXIBILIDADE, TERM_ATENDIMENTO_ANUAL, TERM_ATENDIMENTO_MENSAL, TERM_MAIORES_DESVIOS, TERM_DISP_SEM_DESPACHO, TERM_CVU_CMO_SEMANAL, TERM_CVU_CMO_RESUMO | `tab_motivos_termica`, `despacho_motivo_mensal`, `inflexibilidade_mensal`, `tab_atendimento_anual`, `desvios_despacho`, `tab_maiores_desvios`, `tab_disponivel_anual`, `cvu_cmo`, `tab_cvu_cmo` |
| CONF_G3_* | programacao, despacho; conferência `programacao_despacho` |
| CONF_G4_* | despacho, geracao; conferência `verificada_despacho` |
| REN_FC_ANUAL, REN_FC_MENSAL, REN_CORTE_ANUAL, REN_CORTE_MENSAL, REN_CORTE_RAZAO, REN_RECURSO_FAIXAS, REN_DESVIOS_PROGRAMACAO | `tab_fc_anual`, `fc_mensal`, `tab_corte_anual`, `corte_razao_mensal`, `tab_corte_razao`, `tab_recurso_faixas`, `tab_desvios_programacao_renovavel` |
| CONF_G1_* | geracao, fator_capacidade, restricao_detalhe, restricao_razao; conferência `geracao_fontes` |
| CONF_G2_* | restricao_detalhe, geracao; conferência `soma_conjunto` |
| CONF_G5_* | programacao, fator_capacidade; conferência `programacao_renovaveis` |
| CONJ_TRECHOS, CONJ_COMPOSICAO, CONJ_MENSAL, CONJ_PESO_USINA | `tab_conjunto_trechos`, `tab_conjunto_composicao`, `conjunto_mensal`, `tab_usina_peso_potencia`; CONJ_TIPO_PUBLICADO: geracao, composicao |
| demais `PROG_`, `DISP_`, `HID_` e `GER_` (por prefixo) | `tab_programacao_mensal`, `tab_disponibilidade_paradas`, `tab_faixas_afluencia` e `tab_geracao_oficial` |
| aba sem entrada | `origem não mapeada`, "—", "—", "não", com aviso no log |

### 5.5 Textos das legendas (`fontes.legenda_fonte`)

- Formato: `<prefixo> <conjunto (identificador), obtido em dd/mm/aaaa>; …. Conferência: <texto>; …. Sem outra fonte para conferir: <dados>.` O prefixo é `PREFIXO_FONTE` ("Fonte dos dados:") ou, com `calculado`, `PREFIXO_CALCULADO` ("Calculado neste relatório a partir de:"); as partes de conferência e de dados sem outra fonte só aparecem quando a entrada as tem.
- `projeto` aparece como "parâmetros do projeto (origem na tabela de parâmetros)"; sem data, `SEM_REGISTRO` ("data de obtenção não registrada"); chave fora do mapa, "Fonte dos dados: origem não mapeada.", com aviso.
- Identificador e nome de cada conjunto: `fontes.CONJUNTOS`, com os valores do perfil (FR-025). Na usina sem EVT, `identificador_com_nivel` dá o identificador com o nível, pelos `res.niveis`: na geração, "id ONS X", "conjunto de usinas, id ONS CJU_…" ou os dois; na programação do conjunto, "conjunto de usinas, `<códigos>`"; no Fator de capacidade e na razão da restrição do conjunto, "conjunto de usinas, id ONS `<id>`"; na eólica ou solar com série própria, a Geração por usina com o nível coletado.
- Conferência sem o conjunto carregado: "`<dado>`: conferência com `<conjunto>` não feita nesta execução". TEIFa e TEIP sem mês com a janela completa: "TEIFa e TEIP: conferência com Taxas TEIFa e TEIP não feita nesta execução". Na usina sem EVT, a conferência sem base fica fora da legenda.
- Textos das conferências com o conjunto carregado: FR-026. Na TEIFa e na TEIP, os meses comparados, os reproduzidos e a diferença máxima (com três casas) vêm de `ons["recalculo_resumo"]`, gravados pela Conferência; `meses` igual a zero dá o texto de "não feita nesta execução". Só sem essa contagem (chamada direta), a legenda a refaz sobre `ons["recalculo_taxas"]`, comparando `diferenca_absoluta` (|diferença| arredondada a `CASAS_COMPARACAO` casas) com `TOLERANCIA_REPRODUCAO_TAXAS_PP`. "Abaixo da meta de 99%" usa `META_ALINHAMENTO_HIDROLOGIA_PCT`.

### 5.6 Constantes

| Constante | Valor | Onde | Uso |
|---|---|---|---|
| `DEFAULT_PLOT_DPI` | 300 | `src/comum/regras.py` | resolução das figuras |
| `TAMANHO_FIGURA_PADRONIZADA` | (11, 4,3) pol | `src/comum/regras.py` | figuras 01, 02, 05 e 06 da hidrelétrica com EVT e todas as da usina sem EVT |
| `LARGURA_FIGURA_CARTEIRA` | 7,5 pol | `src/comum/regras.py` | figuras da carteira (A4 retrato) |
| `DURACAO_MINIMA_EVENTO_RELATORIO_H` | 24 h | `src/comum/regras.py` | indisponibilidade total na tabela e nas faixas da figura 01 |
| `NUMERO_EVENTOS_RELATORIO` | 15 | `src/comum/regras.py` | eventos de parada com EVT, de desvio da programação, períodos de divergência, maiores desvios do despacho e da programação e intervalos ausentes mostrados |
| `MAXIMO_ITENS_CONCLUSAO` | 5 | `src/comum/regras.py` | itens por lista no PDF e no Markdown |
| `HORAS_DIURNAS`, `HORAS_NOTURNAS` | 9h às 15h; 20h às 5h | `src/comum/regras.py` | textos, figura 08 e parâmetros |
| `LIMIAR_GERACAO_PARADA_MW`, `LIMIAR_DESVIO_PROGRAMACAO_MW`, `JANELA_TAXAS_MESES` | 1 MW; 5 MW; 60 meses | `src/comum/regras.py` | cabeçalhos, subtítulos e notas das tabelas, cartão da capa, notas metodológicas e parâmetros |
| `LIMIAR_DESVIO_DESPACHO_MW` | 5 MW | `src/comum/regras.py` | atendimento ao despacho: tabela, figura, notas e parâmetros |
| `PERIODO_MINIMO_SAZONALIDADE_MESES` | 12 | `src/comum/regras.py` | sazonalidade da usina sem EVT |
| `TIPOS_COM_FATOR_CAPACIDADE` | EOL, UFV | `src/comum/regras.py` | fator de capacidade nos indicadores anuais e na capa da usina sem EVT |
| `FAIXA_VENTO_MS`, `FAIXA_IRRADIANCIA_WM2` | 2 m/s; 100 W/m² | `src/comum/regras.py` | faixas do recurso × geração (texto e parâmetros) |
| `LIMITE_VENTO_PLAUSIVEL_MS`, `LIMITE_IRRADIANCIA_PLAUSIVEL_WM2` | 40 m/s; 1.500 W/m² | `src/comum/regras.py` | limite físico do recurso (texto, notas e parâmetros) |
| demais `LIMIAR_*`, `FRACAO_PLENA_CARGA`, tolerâncias (como `TOLERANCIA_IDENTIDADE_HORAS`, 0,1 h, e `TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW`, 1 MW), `META_ALINHAMENTO_HIDROLOGIA_PCT`, `LIMIAR_CONCLUSAO_*` | regras gerais | `src/comum/regras.py` | notas, legendas e parâmetros (texto, nunca recálculo) |
| `TOLERANCIA_REPRODUCAO_TAXAS_PP`; `CASAS_COMPARACAO` | 0,001 p.p.; 9 casas | `src/comum/regras.py`; `src/conferencia/resultado.py` | contagem de reserva dos meses reproduzidos na legenda da TEIFa e da TEIP |
| `RESUMO_MAXIMO_PAGINAS` | 2 | `src/comum/regras.py` | regra das duas páginas do resumo |
| `RESUMO_CORPO_PT`, `RESUMO_TABELA_PT` | 10 pt; 9 pt | `src/comum/regras.py` | corpo do texto e das tabelas do resumo |
| `RESUMO_MAXIMO_PALAVRAS` | 1.000 (fora das tabelas; palavras separadas por espaço, sem as marcas de Markdown) | `src/comum/regras.py` | aviso no log; verificação dos testes |
| `RESUMO_MAXIMO_PALAVRAS_DADOS` | 250 | `src/comum/regras.py` | limite de "Sobre os dados" |
| `GLOSSARIO_RESUMO` | sigla → explicação: EVT, ONS, DISPF, TEIFa, TEIF, TEIP, UG, GF, Pinst, MWmed, CVU, CMO e constrained-off, com o texto aprovado pelo usuário | `src/comum/regras.py` | linha de termos do resumo |
| `COLUNAS_RESUMO_ANUAL` | 2.10.3 | `src/relatorio/resumo.py` | evolução anual do resumo |
| `PASTA_TEMPORARIA` | `.gravando` | `src/relatorio/etapa.py` | pasta, dentro de `reports/<slug>/` e de `reports/carteiras/<nome>/`, onde as saídas são geradas e conferidas antes da troca |
| `MARGEM_LATERAL`, `MARGEM_SUPERIOR`, `MARGEM_INFERIOR` | 36, 50 e 42 pt | `src/relatorio/pdf.py` | página do relatório, do resumo e da carteira |
| `ALTURA_MAXIMA_FIGURA` | 285 pt | `src/relatorio/pdf.py` | figuras não padronizadas |
| `FIGURAS_PADRONIZADAS` | `serie_temporal`, `evt_mensal`, `disponibilidade_sincronizada`, `vazoes_defluentes` | `src/relatorio/pdf.py` | largura útil |
| `FIGURAS_PADRONIZADAS_COMUM` | `serie_temporal_comum`, `geracao_mensal`, `sazonalidade`, `perfil_horario_comum`, `disponibilidade_comum` | `src/relatorio/pdf.py` | largura útil, na usina sem EVT |
| `LINHAS_TABELA_INTEIRA`, `LINHAS_MINIMAS_NA_PAGINA` | 12; 6 | `src/relatorio/pdf.py` | paginação das tabelas |
| `ALTURA_ABERTURA_CURTA` | 150 pt | `src/relatorio/pdf.py` | abertura junto do primeiro bloco; espaço para a subseção |
| `BLOCOS_CAPA_TRES` | identificação 0,26 (chave de 62 pt; na usina sem EVT, 82 pt); cadastro 0,38 (112 pt); parâmetros 0,36 (88 pt) | `src/relatorio/pdf.py` | capa com três blocos; com dois, metade da largura e chave de 118 pt |
| cores e rampas | plano, D7 | `src/relatorio/figuras.py`, `figuras_comum.py`, `carteira_figuras.py` | figuras |
| `ENTRELINHA_CORPO`, `LARGURAS_INDICADORES`, `FRACAO_COLUNA_ANO` | 13 pt; 0,29, 0,12 e 0,59; 0,10 | `src/relatorio/resumo_pdf.py` | página do resumo |
| `ALTURA_MAXIMA_FIGURA`, `TABELA_PT` (carteira) | 330 pt; 8 pt | `src/relatorio/carteira_pdf.py` | figuras e tabelas do PDF da carteira |
| `TOLERANCIA_RELATIVA_CELULA` | 1e-12 | `src/comum/comparacao.py` | igualdade de células numéricas |
| `MAXIMO_CELULAS_POR_ABA` | 20 | `src/comum/comparacao.py` | células listadas por aba |
| `IGNORADOS` | `etapa.json` | `src/comum/comparacao.py` | fora da comparação |
| `FORA_DO_RELATORIO` | `referencia.json`, `perfil.toml`, `coleta` | `src/comum/comparacao.py` | fora da comparação do relatório refeito (`--todas`) |
| `COLETA_INFORMATIVOS`, `COLUNAS_EXECUCAO` | `dicionarios.csv`, `datas_obtencao.csv`, `dicionario_evt.json`; `data_hora_processamento` | `src/comum/comparacao.py` | Coleta refeita (`--coleta`): só informação; colunas fora da comparação das auditorias |

### 5.7 Estados e códigos

| Situação | Código | `etapa.json` |
|---|---|---|
| saídas gravadas | 0 | `concluida` |
| Análises ausentes, com falha, desatualizadas ou em outro formato | 5 | não é gravado; nada é gravado |
| `resultados.pkl` em outra versão, campo ausente, falha de figura, planilha, Markdown, PDF ou resumo executivo, resumo com mais de duas páginas mesmo sem a evolução anual, "Sobre os dados" acima de 250 palavras, saída vazia ou PDF inválido na conferência, falha na troca | 1 | `falha`, com `resumo.erro`; as saídas anteriores ficam como estavam |
| interrupção pelo usuário (Ctrl+C) | 1 | `falha`, com `resumo.erro` "interrompida pelo usuário"; as saídas anteriores ficam como estavam |
| `--data-geracao` inválida ou opção inválida | 2 | não é gravado (recusa antes da etapa) |
| perfil inválido | 4 | não é gravado |

### 5.8 Avisos no log, sem falhar

- constatação sem seção no mapa, ou com a seção ausente;
- chave de figura ou tabela, ou aba, sem entrada no mapa de fontes;
- figura sem legenda descritiva;
- fontes TrueType ausentes (Helvetica);
- no PDF, quantidade de legendas de fonte diferente da de tabelas, blocos e figuras desenhados, ou de constatações emitidas diferente das calculadas;
- resumo executivo com mais de duas páginas, gerado de novo sem a evolução anual;
- resumo executivo com mais de 1.000 palavras fora das tabelas.

Em nível INFO, a etapa registra também cada saída gravada, a remoção de uma figura opcional de execução anterior ("Figura de execução anterior removida: `<arquivo>`") e as páginas e palavras do resumo ("Resumo executivo: `<n>` páginas, `<p>` palavras fora das tabelas[, sem a evolução anual]."). Uma troca interrompida gera um erro no log: "Troca das saídas do relatório interrompida; as da execução anterior foram mantidas." ou, se algum arquivo não voltou, a lista deles e a pasta `.anteriores_<AAAAMMDDTHHMMSS>/` onde estão as versões anteriores.

### 5.9 Formatação (`src/comum/formatacao.py`)

- `fmt_num`: milhar ".", decimal ","; ausente, NaN ou infinito vira "–"; `fmt_int` sem casas; `fmt_pct` com "%";
- `fmt_pp`: sinal "+" ou "−" e " p.p.";
- `fmt_data` "dd/mm/aaaa"; `fmt_data_hora` "dd/mm/aaaa HHh"; `fmt_mes_ano` "mmm/aaaa" (jan a dez); `fmt_utc` "dd/mm/aaaa HH:MM UTC";
- `fmt_lista`: "a, b e c"; `plural`; `numero_por_extenso` de 1 a 10 ("duas", no feminino, para 2);
- anos parciais com "*" (`_rotulo_ano`) nas tabelas e nas figuras, com a nota "* ano parcial" nas figuras.

## 6. Relatório de carteira (`reports/carteiras/<nome>/`)

`<nome>` = `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`, em minúsculas (`Recorte.nome`). `carteiras` é nome reservado: o perfil recusa esse slug.

### 6.1 Entradas

| Entrada | Produzida por | Uso |
|---|---|---|
| `data/catalogo/usinas.csv` | Coleta (catálogo de usinas) | recorte (`filtrar` pelo estado e pelo tipo), linhas de conjunto (não contam como usina), nome, estado, tipo, modalidade e `cobertura_resumo` de cada usina |
| `data/catalogo/agregados.csv` | Coleta | panorama: `id_estado`, `mes`, `modalidade`, `tipo_ons`, `grupo`, `energia_mwh`, `horas`, `horas_ausentes`, `previsao`, `arquivo` |
| `data/catalogo/catalogo.json` | Coleta | `montado_em_utc`; `agregados.meses` (os 12 últimos meses completos); `cadastro` (publicação da Modalidade das usinas) |
| `usinas/*/perfil.toml` | usuário | perfil achado pelo CEG normalizado (`perfis_por_ceg`), com a `usina.situacao`; o ilegível fica de fora, com aviso; o perfil é validado (`carregar_perfil`) |
| `data/usinas/<slug>/analises/etapa.json` e `resultados.pkl` | Análises | situação das Análises (`status`, `versao_formato` 3, `concluida_em`), `indicadores_carteira` e `niveis` |

Nenhuma etapa é executada, nenhum `etapa.json` é gravado, e o portal não é consultado.

### 6.2 Situação de cada usina (`situacao_da_usina`)

Com resultado (`UsinaComResultado`): perfil achado pelo CEG, único, conferido e válido, e Análises `concluida` no formato atual, com `indicadores_carteira`. Sem resultado (`UsinaSemResultado`): o primeiro motivo desta ordem (`ORDEM_MOTIVOS`), com o detalhe:

| Motivo | Quando | Detalhe |
|---|---|---|
| só agregado no ONS (ver o panorama) | `cobertura_resumo` `agregado` | — |
| sem perfil | nenhum perfil com o CEG | — |
| perfil em rascunho | `usina.situacao` `rascunho` | slug |
| perfil inválido | dois perfis com o mesmo CEG, ou perfil recusado pela validação | os dois slugs, ou o slug |
| Análises ausentes | sem `etapa.json` ou sem `resultados.pkl` | slug |
| Análises em formato antigo | `versao_formato` diferente do atual, `resultados.pkl` ilegível ou sem os indicadores da carteira | slug (e "sem os indicadores da carteira") |
| Análises com falha | `status` diferente de `concluida` e de `desatualizada` | slug |
| Análises desatualizadas | `status` `desatualizada` | slug |

As usinas sem resultado ficam na ordem dos motivos, do tipo e do nome.

### 6.3 Ordenação (`chave_ordenacao`)

Possíveis problemas (decrescente), pontos de atenção (decrescente) e nome; a usina sem regra avaliada (`indicadores_carteira["conclusao"]["regras_avaliadas"]` vazio ou zero) vai para o fim, sem posição.

### 6.4 Documento

`Documento` (`titulo` "Relatório de carteira — `<recorte>`", `subtitulo`, `cabecalho_pagina`, `blocos`), com `Bloco` de tipo `secao`, `paragrafo`, `tabela` ou `figura`, na ordem: capa (parágrafos do recorte e das quantidades); 1. Usinas com resultado; 2. Indicadores comparáveis; 3. Ordenação pelos itens da conclusão (com a figura 1); 4. Usinas sem resultado; 5. Panorama dos agregados de `<UF>` (só com estado; com a figura 2); Notas. O Markdown (`gerar_md_carteira`) e o PDF (`gerar_pdf_carteira`, A4 retrato, com os estilos do resumo executivo e tabelas em 8 pt) saem dele.

| Tabela | Cabeçalho | Legenda (origem) |
|---|---|---|
| Usinas com resultado | Usina, [UF, sem estado], Tipo, Modalidade, Potência (MW), Cobertura (própria, conjunto, agregado, ausente), Nível da geração ("usina" ou "conjunto (CJU_…)"), Período | Fonte dos dados: Modalidade das usinas (CEG de cada usina), com a publicação, pelo catálogo, com a cobertura; nome e potência do perfil; período e nível das Análises |
| Indicadores comparáveis | Usina, Ano (com "*" no ano parcial), e as colunas dos indicadores que se aplicam aos tipos do recorte: Fator de capacidade, Disponibilidade, TEIFa, Energia cortada, Atendimento ao despacho; nota do ano parcial e do "—" | Calculado neste relatório a partir de: resultados gravados das Análises de cada usina, com as bases de cada indicador; o identificador e a data de obtenção estão na legenda da tabela anual do relatório de cada usina |
| Ordenação | Posição, Usina, Tipo, Possíveis problemas, Pontos de atenção, A confirmar com o agente, A verificar em campo, Regras avaliadas ("n de m"); nota da contagem de todos os itens | Calculado neste relatório a partir de: itens da conclusão dos resultados das Análises (aba CONCLUSAO do relatório de cada usina) |
| Usinas sem resultado | Usina, [UF], Tipo, Modalidade, Cobertura, Motivo (com o detalhe) | Calculado neste relatório a partir de: cobertura no catálogo; perfis em `usinas/` e `etapa.json` das Análises |
| Panorama | Mês, `<série>` (MWh) para cada série presente (modalidade e tipo do ONS, "(previsão)" no Tipo III), em ordem fixa (`ORDEM_SERIES_PANORAMA`); "sem valor" quando nenhum grupo da série tem hora com valor no mês; "—" sem a série no mês | Fonte dos dados: Geração por usina (agregados do estado por modalidade, nível agregado), arquivos mensais do período, lidos pelo catálogo |

Indicadores na tabela (`texto_indicador`): o valor em %; na TEIFa, o mês, quando não é dezembro ou o ano é parcial; no atendimento ao despacho, "(`<horas a até 5 MW da programada>` de `<horas com programação>` h)"; fora do nível da usina, "(do `<nível>`)"; sem o indicador, "—".

Figuras (`carteira_figuras.NOMES_FIGURAS_CARTEIRA`), em seaborn, 7,5 polegadas de largura:

| Arquivo | Chave | Mostra | Gerada |
|---|---|---|---|
| `01_itens_da_conclusao_por_usina.png` | `ordenacao` | barras horizontais empilhadas pelas quatro listas da conclusão, na ordem da conclusão, uma barra por usina, na ordem da ordenação; a usina sem regra avaliada, identificada | com usinas com resultado |
| `02_panorama_agregados_mensal.png` | `panorama` | energia mensal dos agregados (GWh) em barras empilhadas por série, com a previsão Tipo III na legenda | com estado e agregados no período |

### 6.5 Planilha `carteira.xlsx`

Cabeçalho congelado em `A2`; largura de coluna pelo maior texto das 200 primeiras linhas, entre 8 e 60.

| Aba | Linhas | Colunas |
|---|---|---|
| USINAS | uma por usina com resultado, na ordem da ordenação | `slug`, `nome`, `ceg`, `estado`, `tipo`, `modalidade`, `potencia_mw`, `cobertura`, `nivel_geracao`, `periodo_inicio`, `periodo_fim`, `ano`, `ano_parcial`, `<indicador>_pct` e `<indicador>_nivel` de cada um dos cinco indicadores (vazios, nunca zero, quando não se aplicam), `pontos_atencao`, `possiveis_problemas`, `confirmar_agente`, `verificar_campo` (todos os itens de cada lista), `regras_avaliadas`, `regras_nao_avaliadas`, `analises_concluida_em` |
| INDICADORES | uma por usina e indicador | `slug`, `nome`, `tipo`, `ano`, `ano_parcial`, `indicador`, `valor`, `nivel`, `unidade`, `detalhe` (mês da TEIFa; horas do atendimento) |
| ORDENACAO | uma por usina com resultado | `posicao` (vazia sem regra avaliada), `slug`, `nome`, `tipo`, as quatro contagens, `regras_avaliadas`, `regras_nao_avaliadas` |
| SEM_RESULTADO | uma por usina sem resultado | `ceg`, `nome`, `estado`, `tipo`, `modalidade`, `cobertura`, `motivo`, `detalhe` |
| PANORAMA | com estado: as linhas de `agregados.csv` do recorte, com `horas_sem_valor`, `previsao` e `serie`; na carteira só por tipo, uma linha com o motivo da omissão | as de `agregados.csv` e as três calculadas; ou `motivo` |
| FONTES | uma por aba (USINAS, INDICADORES, ORDENACAO, SEM_RESULTADO, PANORAMA) | `aba`, `conjuntos_origem` (a mesma origem da legenda; "–" sem panorama), `conferencias` ("–"), `sem_outra_fonte` ("–"), `calculado_no_relatorio` ("sim" ou "não"); as mesmas colunas da aba FONTES do relatório da usina |

Contagens e `ano` em inteiro com vazio (`Int64`).

### 6.6 Gravação

Pasta temporária `reports/carteiras/<nome>/.gravando/`, conferência (`_conferir_saidas`) e troca (`_trocar_saidas`) do relatório da usina, sem `.bak`; a figura de uma execução anterior que não tem mais base é apagada. Com `--data-geracao`, o PDF sai no modo invariante. Arquivos em `caminhos.ARQUIVOS_CARTEIRA`: `relatorio_carteira.pdf`, `relatorio_carteira.md`, `carteira.xlsx` e `figures/`.

## 7. Relatórios de referência (`relatorios_referencia/`)

```text
relatorios_referencia/
└── <slug>/
    ├── referencia.json
    ├── perfil.toml                             # perfil usado na geração
    ├── relatorio_analise_estatistica.pdf      # no git, por exceção no .gitignore
    ├── relatorio_analise_estatistica.md
    ├── perfil_estatistico_anual.xlsx
    ├── perfil_estatistico_anual.csv
    ├── resumo_executivo.pdf
    ├── resumo_executivo.md
    ├── figures/
    └── coleta/                                 # Coleta congelada: só os arquivos do etapa.json e ele; fora do git
```

| Campo de `referencia.json` | Conteúdo |
|---|---|
| `usina` | slug |
| `data_geracao` | data fixa usada na geração ("DD/MM/AAAA HH:MM") |
| `aprovado_em` | data da aprovação pelo usuário ("DD/MM/AAAA") |
| `periodo` | `inicio` e `fim` da série de referência (do resumo da Coleta; sem ele, do das Análises) |
| `arquivos` | `nome`, `bytes` e `sha256` de cada arquivo do relatório (os do `etapa.json` do relatório) |
| `perfil` | SHA-256 do perfil congelado |
| `coleta` | `nome`, `bytes` e `sha256` de cada arquivo da Coleta congelada, inclusive o `etapa.json` |

- **Gravação**: em `relatorios_referencia/.gravando_<slug>/`; cada arquivo copiado é conferido contra o SHA-256 do `etapa.json` de origem; depois de gravado o `referencia.json`, a pasta inteira é conferida (`conferir_referencia`) e não pode ter arquivo a mais nem a menos. A troca guarda a anterior em `.anterior_<slug>`, que volta se a troca falhar e é apagada no fim.
- **Git**: o relatório e o perfil congelado entram no git; a Coleta congelada não (`.gitignore`: `!relatorios_referencia/**/*.pdf`, `relatorios_referencia/*/coleta/` e `relatorios_referencia/.*/`). Uma referência existente só é substituída sem mudanças fora do git (`git status --porcelain -- relatorios_referencia/<slug>` vazio).
- **Cópias de segurança**: `copia-seguranca` copia `relatorios_referencia/` inteira, sem as pastas temporárias, para cada cópia nova e a confere pelos SHA-256 antes da poda.
- **Comparação**: `comparar --todas` percorre as pastas de `relatorios_referencia/` (sem as que começam por "." ou "_"), confere o perfil e a Coleta congelados (`conferir_congelados`), refaz as etapas 2 a 5 num espaço isolado e compara com o relatório; `referencia.json`, `perfil.toml` e `coleta/` ficam fora da comparação. Um perfil atual diferente do congelado gera só um aviso. Com `--coleta`, a Coleta refeita é comparada com a congelada (plano, D21).
- **Substituição**: a referência só é substituída com a aprovação do usuário e só depois de a atual estar commitada. A anterior continua no histórico do git e nas cópias de segurança.

## 8. Requisitos × entidades

| Requisitos | Entidades |
|---|---|
| FR-001, FR-002 | entradas (1); datas de obtenção (1.2) |
| FR-007 a FR-010, FR-041 | seções (2.3, 2.9.2); constatação → seção (5.2); `Secao` (3) |
| FR-011 a FR-014 | capa (2.2, 2.9.1) |
| FR-020 a FR-022 | notas e parâmetros (2.3, 2.9.2, 3) |
| FR-023 a FR-028 | mapa de fontes (5.3); abas na FONTES (5.4); legendas (5.5); conferências (1.1) |
| FR-034 a FR-037 | figuras (2.6, 2.9.4) |
| FR-038, FR-039 | planilha e CSV (2.7, 2.8, 2.9.5) |
| FR-040, FR-042, FR-043 | diferenças do `comparar` (3); referências (7) |
| FR-044 a FR-047 | seções, tabelas e figuras do tipo e do conjunto (2.9.2 a 2.9.4); `termica`, `renovavel`, `conjunto`, `hidrologia` (1.1) |
| FR-048 | `parte_conjunto`, `usina_no_conjunto` e `em_duas_partes` (2.9.2); mapa das duas partes (5.2) |
| FR-049 | carteira (6) |
| FR-050 a FR-055 | etapa (2.1, 4); regra das duas páginas (2.10, 5.7) |
| FR-056 a FR-062 | `ResumoExecutivo` (2.10.1 a 2.10.4); textos curtos (2.10.5) |
| FR-063 a FR-067 | origem de cada campo (2.10.1); `GLOSSARIO_RESUMO` (5.6) |
| FR-068 | `COLUNAS_RESUMO_ANUAL` por caminho (2.10.3) |
| FR-069, FR-070 | referências (7); `etapa.json` (4) |
