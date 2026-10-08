# Data Model: Geração do relatório

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Atualizado em**: 2026-10-08

## 1. Entradas

| Entrada | Produzida por | Lida por | Uso |
|---|---|---|---|
| `data/usinas/<slug>/analises/etapa.json` | Análises | `pipeline.etapa_anterior_concluida` | pré-requisito: `status` `concluida` e `versao_formato` 1; senão, código 5 |
| `data/usinas/<slug>/analises/resultados.pkl` | Análises | `analises.resultados.carregar_resultados`, chamada por `etapa.executar_relatorio` | pickle `{"versao_formato": 1, "resultados": ResultadosAnalise}`; outra versão gera `ValueError` (código 1) |
| `_manifesto_ons.json` de cada conjunto, em `data/raw/` | Coleta | `fontes.datas_obtencao`, por `coleta.conjuntos.data_obtencao` | data de obtenção das legendas (1.2) |
| `usinas/<slug>/perfil.toml` | usuário, validado na linha de comando | `comum.perfil.perfil_ativo()` | valores da usina (1.3) |
| `src/comum/regras.py` | regras gerais | importação | limiares, metas, tolerâncias, endereços do ONS, resolução e tamanho das figuras (seção 5) |

A etapa não lê os dados brutos nem os tratados, nem a pasta `data/usinas/<slug>/conferencia/`: os resultados da Conferência chegam dentro de `ResultadosAnalise`.

### 1.1 Resultados das Análises

`ResultadosAnalise` está descrito no [data-model das Análises](../004-analises/data-model.md) (seção 3). A etapa usa:

| Campo | Tipo | Uso |
|---|---|---|
| `cobertura` | dict | subtítulo da capa e período (`inicio`, `fim`, `horas_observadas`); bloco de identificação (`identificacao`, `agentes`); quadro da seção `cobertura` (`horas_esperadas`, `horas_faltantes`, `duplicadas`, `por_ano`, `arquivos`, `manifesto`); anos parciais (`anos_parciais`); abas COBERTURA_POR_ANO e AGENTES |
| `globais` | dict | indicadores principais da capa; aba INDICADORES_GLOBAIS |
| `indicadores_anuais` | DataFrame, um ano por linha | tabelas das seções `indicadores_anuais` e `perfil_horario`; figura 04; aba INDICADORES_ANUAIS e CSV |
| `serie_diaria`, `vazoes_anuais` | DataFrame | figuras 01 e 05 (médias calculadas nas Análises) |
| `evt_mensal` | DataFrame, um mês por linha | figura 02 e a sua legenda; aba EVT_MENSAL |
| `perfil_horario_geracao`, `perfil_horario_evt` | DataFrame ano × hora | figura 03; abas PERFIL_HORARIO_GERACAO e PERFIL_HORARIO_EVT |
| `eventos_indisponibilidade_total`, `eventos_parada_com_evt` | DataFrame, um evento por linha | faixas da figura 01; tabelas resumidas das seções `disponibilidade_geracao` e `eventos`; abas EVENTOS_INDISP_TOTAL e EVENTOS_PARADA_COM_EVT |
| `evt_por_faixa_geracao`, `horas_geracao_zero`, `validacao`, `resumo_anomalias`, `extremos` | DataFrame | tabelas das seções `eventos`, `geracao_zero` e `qualidade`; abas de mesmo conteúdo |
| `distribuicao_mes_do_ano`, `anomalias`, `perfil_estatistico` | DataFrame | só na planilha |
| `mudanca_classificacao` | dict (`mes`) | marco da figura 02; legendas das figuras 02 e 05; aba INDICADORES_GLOBAIS |
| `achados` | lista de (título, texto) | constatações no início das seções; aba CONSTATACOES |
| `conclusao` | lista de dicts (`lista`, `ordem`, `regra`, `texto`, `secoes`) | seção `conclusao`; aba CONCLUSAO |
| `ons` | dict | seção `indicadores_ons` (`disp_anual`, `decomposicao`, `ug_anual`, `horas_anual`, `divergencias`, `taxa_ultima`); indicador DISPF da capa (`disp_periodo`, `taxa_ultima`); legendas (`recalculo_resumo`, `divergencias`); abas ONS_* (também `horas_mensal` e `recalculo_taxas`) |
| `programacao` | dict | seção `programacao` (`mensal`, `perfil`, `eventos`, `periodo`); abas PROG_* (também `dias_ausentes`, `auditoria`, `classificadas`) |
| `disponibilidade` | dict | seção e figura 06; notas (`resumo`); parâmetros (`resumo`, `obtido_em`); legenda (`conferencia`); abas DISP_* |
| `hidrologia` | dict | seção, figuras 07 e 08 e tabelas de cruzamento só com `publicado`; notas (`resumo`, `alinhamento`); parâmetros (`resumo`, `obtido_em`); legenda (`alinhamento`); abas HID_* |
| `geracao_oficial` | dict | seção `geracao_oficial`; notas e parâmetros (`resumo`, `obtido_em`); legenda (`conferencia`); abas GER_* |
| `cadastro` | dict (`ficha`, `divergencias`, `obtido_em`, `auditoria`) | bloco "Cadastro no ONS"; nota e parâmetros; legenda; abas CAD_FICHA e CAD_AUDITORIA |
| `dicionarios` | dict (`registro`) | aba DICIONARIOS |
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

### 1.2 Datas de obtenção

Para cada conjunto, a data é o maior `registrado_em_utc` do manifesto (formato no [data-model da Coleta](../001-coleta-dados/data-model.md), seção 2.1); sem manifesto ou sem registro, fica vazia e a legenda diz "data de obtenção não registrada".

| Id em `fontes.CONJUNTOS` | Conjunto no catálogo | Manifesto |
|---|---|---|
| `evt` | `energia-vertida-turbinavel` | `data/raw/_manifesto_ons.json` |
| `dispf_mensal` | `ind_disponibilidade_fgeracao_uge_mensal` | `data/raw/indicadores_ons/ind_disponibilidade_fgeracao_uge_mensal/_manifesto_ons.json` |
| `dispf_anual` | `ind_disponibilidade_fgeracao_uge_anual` | `data/raw/indicadores_ons/ind_disponibilidade_fgeracao_uge_anual/_manifesto_ons.json` |
| `teif_teip` | `taxa_teif_teip` | `data/raw/indicadores_ons/taxa_teif_teip/_manifesto_ons.json` |
| `teif_teip_parametro` | `taxa_teif_teip_parametro` | `data/raw/indicadores_ons/taxa_teif_teip_parametro/_manifesto_ons.json` |
| `programacao` | `programacao_diaria` | `data/raw/programacao_diaria/_manifesto_ons.json` |
| `disponibilidade` | `disponibilidade_usina` | `data/raw/disponibilidade_usina/_manifesto_ons.json` |
| `hidrologia` | `dados_hidrologicos_ho` | `data/raw/dados_hidrologicos_ho/_manifesto_ons.json` |
| `geracao` | `geracao-usina-2` | `data/raw/geracao_usina_2/_manifesto_ons.json` |
| `cadastro` | `modalidade-usina` | `data/raw/modalidade_usina/_manifesto_ons.json` |

As notas e a tabela de parâmetros das bases complementares usam o `obtido_em` gravado pelas Análises (do mesmo manifesto; no cadastro, a `data_consulta_utc` da ficha).

### 1.3 Perfil da usina

| Campo | Onde aparece |
|---|---|
| `usina.nome` | título do PDF e do Markdown, cabeçalho das páginas e metadados do PDF |
| `usina.estado` | notas da disponibilidade, da geração e do cadastro (conferência pelo estado) |
| `usina.inicio_operacao_comercial` | linha "Início da operação comercial" dos parâmetros |
| `identificacao.cod_usina` | legendas da EVT e da hidrologia; critério de extração; notas |
| `identificacao.ceg`, `identificacao.id_ons` | legendas dos indicadores, da disponibilidade, da geração e do cadastro; parâmetros; notas |
| `identificacao.cod_programacao` | legenda, nota e parâmetro da programação |
| `identificacao.id_reservatorio` | legenda, nota e parâmetro da hidrologia |
| `parametros.potencia_instalada_mw`, `unidades_geradoras`, `potencia_unitaria_mw`, `tipo_turbina`, `engolimento_nominal_ug_m3s`, `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia` | bloco de parâmetros da capa; linhas de referência e rótulos das figuras; legendas descritivas; notas; parâmetros |
| `parametros.queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` | parâmetros; a vazão remanescente também na definição de vertimento mínimo |
| `parametros.fontes.geral` | origem dos parâmetros técnicos |
| `parametros.fontes.garantia_fisica` | origem da garantia física nos parâmetros e na nota; o trecho até a primeira vírgula é o órgão citado ao lado da garantia física na capa (`conteudo.orgao_garantia_fisica`) |
| `parametros.fontes.inicio_operacao_comercial` (opcional) | origem do início da operação comercial; vazia sem o campo |
| `parametros.fontes.ip_teif` (opcional) | frase da origem do IP e do TEIF nas notas; omitida sem o campo |
| `analises.vertimento_minimo_m3s` | figura 02 e a sua legenda; nota da tabela anual; notas; parâmetros |
| `analises.descricao_vertimento_minimo` (opcional) | complemento da definição de vertimento mínimo nas notas |
| `analises.fontes.vertimento_minimo` (opcional) | base do limiar de vertimento mínimo nos parâmetros |
| `textos.ressalva_volume_util` (opcional) | nota da hidrologia |
| derivados: `engolimento_maximo_m3s`, `disponibilidade_referencia`, `produtividade_nominal_mw_m3s` | capa, figuras 04, 05 e 07, faixas de afluência, notas e parâmetros |

`usina.nome_curto`, `identificacao.nome_ons` e `analises.faixas_geracao_mw` não são usados nesta etapa.

## 2. Saídas

### 2.1 Arquivos em `reports/<slug>/`

Nomes em `caminhos.ARQUIVOS_RELATORIO`; sem `.bak`. A cada execução:
- todas as saídas são geradas em `reports/<slug>/.gravando/` (`etapa.PASTA_TEMPORARIA`), com a mesma estrutura (`figures/` incluída);
- `_conferir_saidas` exige que cada uma exista e não esteja vazia, e que o PDF comece com `%PDF-`;
- `_trocar_saidas` move cada uma para o lugar com `os.replace`; a anterior fica em `.gravando/.anteriores/` até o fim da troca;
- se a troca falhar, cada arquivo volta à versão anterior; a versão anterior que não puder voltar vai para `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`, que fica até o usuário recuperá-la;
- `.gravando/` é apagada ao fim, com ou sem erro;
- depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/`.

| Arquivo | Formato | Grava | Conteúdo |
|---|---|---|---|
| `relatorio_analise_estatistica.pdf` | PDF, A4 paisagem | `pdf.PDFReportGenerator.build_pdf` | relatório (2.2 a 2.4) |
| `relatorio_analise_estatistica.md` | Markdown, UTF-8 sem BOM, fim de linha do sistema | `markdown.gerar_relatorio_md` | o mesmo relatório (2.5) |
| `perfil_estatistico_anual.xlsx` | XLSX (openpyxl) | `planilha.exportar_tabelas` | uma aba por tabela (2.7) |
| `perfil_estatistico_anual.csv` | CSV `;`, ponto decimal, UTF-8 sem BOM, fim de linha do sistema | `planilha.exportar_tabelas` | indicadores anuais (2.8) |
| `figures/<nn>_<nome>.png` | PNG, 300 DPI | `figuras.gerar_graficos` | até oito figuras (2.6) |
| `etapa.json` | JSON | `pipeline.executar_etapa` | manifesto (seção 4) |

### 2.2 PDF

- **Página**: A4 paisagem (841,9 × 595,3 pt); margens de 36 pt (laterais), 50 pt (superior) e 42 pt (inferior); largura útil de cerca de 769,9 pt.
- **Cabeçalho** (página 2 em diante): "`<usina.nome>` — energia vertida turbinável (dados ONS) · `<dd/mm/aaaa>` a `<dd/mm/aaaa>`", com um fio abaixo.
- **Rodapé**: fio e "Página X de Y", à direita.
- **Metadados**: título "`<usina.nome>` — energia vertida turbinável e desempenho operacional"; assunto "Análise dos dados abertos do ONS, `<início>` a `<fim>`"; autor "Pipeline de análise `<usina.nome>` (dados ONS)". Com `--data-geracao`, `CreationDate` e `ModDate` ficam `D:20000101000000+00'00'`.
- **Fontes**: Arial (`arial.ttf`, `arialbd.ttf`, `ariali.ttf`, `arialbi.ttf` de `%WINDIR%\Fonts`) ou DejaVu Sans do matplotlib; Helvetica só se nenhuma existir.
- **Página 1 (capa)**, nesta ordem:
  1. título "`<usina.nome>` — energia vertida turbinável e desempenho operacional";
  2. subtítulo "Análise dos dados abertos do ONS · `<dd/mm/aaaa HHh>` a `<dd/mm/aaaa HHh>` · `<N>` registros horários · Gerado em `<dd/mm/aaaa HH:MM>`", com a mesma data de geração do Markdown e do `resumo`;
  3. blocos lado a lado, cada um com a sua legenda de fonte: "Identificação nos dados do ONS" (`bloco_identificacao`: cod_usina, Reservatório, Rio / bacia, Subsistema, Agente); "Cadastro no ONS" (`bloco_cadastro`, só com o cadastro: Usina, Modalidade de operação, Centro de operação, Ponto de conexão, Potência autorizada, Estado · situação na ANEEL, Homônimos excluídos pelo CEG); "Parâmetros técnicos da usina" (`bloco_parametros`: Potência instalada, Turbinas, Engolimento nominal, Garantia física com o órgão de `orgao_garantia_fisica`, IP / TEIF de referência);
  4. indicadores principais em cartões (`tab_capa_indicadores`): Disponibilidade média declarada; Disponibilidade apurada pelo ONS (DISPF), só com os indicadores; Fator de capacidade; Energia vertida turbinável; EVT com a usina parada. Abaixo, a nota e a legenda de fonte;
  5. "Sumário" em duas colunas, com o número, o título e a página de cada seção; quebra de página.
- **Página 2 em diante**: as seções (2.3).

### 2.3 Seções do PDF e do Markdown

Cada seção começa com "N. Título" e as suas constatações ("**Título.** texto"). Cada tabela vem com o subtítulo (quando `textos_tabelas` o define), a tabela, a nota (quando há) e a legenda de fonte; cada figura, com a imagem, a legenda descritiva (`legenda_figura`) e a legenda de fonte. Na São Domingos, com todos os conjuntos, são 17 seções e 30 páginas; só com a base de EVT, 12 seções.

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
| `conclusao` | Conclusão | sempre | frase de abertura e listas (`listas_conclusao`), ou a frase de nenhum item |
| `notas` | Notas metodológicas e limitações | sempre | notas (`notas_metodologicas`, a última com as regras da conclusão); `tab_parametros` |

### 2.4 Tabelas do relatório

Cabeçalhos fixos, em `conteudo.py`; valores formatados no padrão brasileiro (5.9).

| Chave | Cabeçalho | Linhas |
|---|---|---|
| `tab_cobertura` | pares item × valor: Conjunto de dados, Critério de extração, Arquivos lidos, Versão dos arquivos, Período, Registros, Anos parciais | "Arquivos lidos" e "Versão dos arquivos" só com a auditoria e o manifesto da Coleta |
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
1. `# <usina.nome> — energia vertida turbinável e desempenho operacional (dados ONS)`;
2. `**Período**: <dd/mm/aaaa HHh> a <dd/mm/aaaa HHh> (<N> registros horários)` e `**Gerado em**: <dd/mm/aaaa HH:MM>`;
3. `### Identificação nos dados do ONS`, `### Cadastro no ONS` (com o cadastro) e `### Parâmetros técnicos da usina`, em tabelas "Item | Valor", cada uma com a legenda de fonte;
4. `### Indicadores principais`, em tabela "Indicador | Valor | Detalhe", com a nota e a legenda;
5. `## Sumário`, lista numerada com links para as âncoras das seções (`_ancora_md`: minúsculas, sem pontuação, espaços por hífens);
6. cada seção, `## N. Título`: constatações, tabelas (`### <subtítulo>`, tabela, nota com `*` escapado, legenda) e figuras no corpo (`![<título da seção>](figures/<arquivo>.png)`, legenda descritiva, legenda de fonte); notas das seções e das notas metodológicas em itens `- `; na conclusão, `### <lista>` e itens `- `.

Figura ausente do dicionário de figuras é omitida. Na São Domingos: 768 linhas, 30 tabelas, 8 figuras e 38 legendas de fonte.

### 2.6 Figuras

Nomes em `figuras.NOMES_FIGURAS` (sempre) e `figuras.NOMES_FIGURAS_OPCIONAIS` (com a condição de `_GERADORES_OPCIONAIS`); 300 DPI.

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

### 2.7 Planilha (`perfil_estatistico_anual.xlsx`)

Uma aba por quadro, na ordem abaixo; cabeçalho na linha 1, congelado em `A2`; largura de coluna `min(max(len(nome), 12) + 3, 60)`; sem índice. As abas da base de EVT existem sempre; as demais, só com o conjunto carregado e com linhas. Na São Domingos: 58 abas, todas menos DISP_DIVERGENCIAS e GER_DIVERGENCIAS, sem linhas.

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

Uma linha por ano civil da série, com as mesmas colunas da aba INDICADORES_ANUAIS; `;` como separador, ponto decimal, sem índice. Na São Domingos: 9 linhas.

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

## 3. Objetos em memória e entre etapas

A etapa não grava pickle: as suas saídas são finais. Ela completa `ResultadosAnalise` em memória (`etapa.completar_resultados`), sem regravar `resultados.pkl`:

| Campo | Tipo | Conteúdo |
|---|---|---|
| `res.parametros` | DataFrame `grupo`, `parametro`, `valor`, `unidade`, `origem` (texto) | `parametros.tabela_parametros(com_indicadores, com_programacao)`: grupos `Usina` (12 linhas do perfil, com a fonte de `parametros.fontes`), `Derivado` (engolimento máximo, disponibilidade de referência e produtividade nominal, com a fórmula), `Análise` e `Validação` (limiares, origem "Parâmetro de análise" e, quando há, a base do limiar) e `Fonte` (conjunto e endereço; identificador da usina nas linhas dos indicadores, da programação e das bases complementares); mais as linhas de `parametros_disponibilidade`, `parametros_hidrologia` e `parametros_geracao_cadastro`, com período e data de obtenção. Na São Domingos, 41 linhas |
| `res.fontes` | dict | `obtencao`: {id do conjunto: data UTC em texto, ou ""}; `carregados`: ids dos conjuntos cujos dados entraram (`evt` sempre; os quatro de indicadores com `res.ons`; `programacao`, `disponibilidade`, `hidrologia`, `geracao` e `cadastro` com o campo correspondente) |

Estruturas da etapa:

| Estrutura | Módulo | Campos |
|---|---|---|
| `Secao` (dataclass imutável) | `estrutura` | `chave: str`, `titulo: str`, `presente: Callable[[res], bool]` (padrão: sempre) |
| `Conjunto` (dataclass imutável) | `fontes` | `nome: str`; `identificador: str`, modelo com `{cod_usina}`, `{ceg}`, `{id_ons}`, `{cod_programacao}`, `{id_reservatorio}`; `catalogo: str` (vazio em `projeto`) |
| `Conferencia` (dataclass imutável) | `fontes` | `dado: str`; `base: str`, id do conjunto que permite a conferência; `texto: Callable[[res], str]` |
| `Entrada` (dataclass imutável) | `fontes` | `conjuntos`, `conferencias`, `sem_outra_fonte` (tuplas), `calculado: bool` e `todos: bool` (cita os conjuntos mesmo quando não carregados) |
| dicionário de figuras | `figuras.gerar_graficos` | {chave: caminho do PNG}, só as figuras geradas; passado ao Markdown e ao PDF |
| `PDFReportGenerator` | `pdf` | depois de `build_pdf`: `titulos_secoes`, `constatacoes_emitidas`, `legendas_emitidas` (chaves), `paginas_secoes` ({título: página}), `sumario_entradas` ([(n, título, página)]), `subtitulo_capa`; contadores `_desenhados` e `_legendas` |
| `ResultadoEtapa` | `src/pipeline.py` | `codigo`, `arquivos` (PDF, Markdown, XLSX, CSV e figuras, em ordem), `resumo` |
| diferenças do `comparar` | `src/comum/comparacao.py` | lista de textos, um por diferença (formatos no [contrato](contracts/cli-relatorio.md)) |

## 4. Manifesto da etapa (`etapa.json`)

Campos comuns (`etapa`, `usina`, `versao_formato`, `iniciada_em`, `concluida_em`, `status`, `codigo_saida`, `etapa_anterior`, `arquivos`, `resumo`) e status no [data-model da Coleta](../001-coleta-dados/data-model.md), seção 4. Nesta etapa:
- fica em `reports/<slug>/etapa.json`, não em `data/usinas/<slug>/`;
- `etapa_anterior` é `{"etapa": "analises", "concluida_em": …}`;
- `arquivos` traz, nesta ordem, o PDF, o Markdown, a planilha, o CSV e as figuras, já no lugar final, com o nome relativo à pasta (por exemplo, `figures/01_serie_temporal_disponibilidade_geracao_evt.png`), `bytes` e `sha256`; com falha, fica vazio, e as saídas da execução anterior continuam na pasta;
- como última etapa, não marca nenhuma outra como `desatualizada`; ela própria fica `desatualizada` quando uma etapa anterior é concluída de novo;
- o `comparar` ignora o arquivo.

`resumo` (`etapa.executar_relatorio`):

| Campo | Tipo | Significado |
|---|---|---|
| `data_geracao` | texto `dd/mm/aaaa HH:MM` | `--data-geracao`, ou a hora da execução; a mesma do PDF e do Markdown |
| `secoes` | int | seções presentes (`len(secoes_presentes(res))`) |
| `paginas_pdf` | int | objetos `/Type /Page` do PDF (`paginas_do_pdf`) |
| `figuras` | int | figuras geradas |
| `abas_planilha` | int | abas da planilha |

Com falha (código 1), o `resumo` é `{"erro": "<mensagem>"}`; com a interrupção pelo usuário, `{"erro": "interrompida pelo usuário"}`. Na São Domingos: `{"data_geracao": "07/10/2026 08:53", "secoes": 17, "paginas_pdf": 30, "figuras": 8, "abas_planilha": 58}`.

## 5. Regras, estados e validações

### 5.1 Presença

| Elemento | Condição | Onde |
|---|---|---|
| seções `indicadores_ons`, `programacao`, `disponibilidade_sincronizada`, `hidrologia`, `geracao_oficial` | campo correspondente de `ResultadosAnalise` não vazio | `estrutura.SECOES` |
| demais seções | sempre | `estrutura.SECOES` |
| tabelas e figuras de cruzamento hidrológico | `hidrologia["publicado"]`, a conferência das vazões na meta | `pdf._secao_hidrologia`, `markdown._md_conteudo_secao` |
| figuras 06 a 08 | `_GERADORES_OPCIONAIS` (2.6) | `figuras` |
| bloco "Cadastro no ONS" | `res.cadastro` | `pdf._capa`, `markdown.gerar_relatorio_md` |
| cartão do DISPF na capa | `ons["disp_periodo"]` e `ons["taxa_ultima"]` | `conteudo.indicadores_capa` |
| nota da capa | com `res.ons`, distingue indicadores calculados e apurados pelo ONS; sem, diz que são aproximações | `conteudo.indicadores_capa` |
| tabela das bases complementares e da qualidade | só com linhas | `pdf`, `markdown` |
| `tab_indicadores_anuais`, `tab_perfil_horario`, `tab_evt_por_nivel`, `tab_geracao_zero`, `tab_parametros` | sempre | `pdf`, `markdown` |
| texto da conferência da geração na seção | sem a constatação "Conferência da geração" | `pdf`, `markdown` |
| notas dos anos parciais, dos indicadores, da programação e das bases complementares | anos parciais existentes; conjunto carregado | `conteudo.notas_metodologicas` |
| aba opcional | conjunto carregado e quadro com linhas | `planilha.exportar_tabelas` |

### 5.2 Constatação → seção (`estrutura.MAPA_CONSTATACOES`)

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

### 5.3 Mapa de fontes (`fontes.MAPA_FONTES`)

`projeto` = parâmetros do projeto. Conferências: `geracao`, `disponibilidade`, `vazoes`, `teifa_teip`, `dispf_horas`, `cadastro`. Dados sem outra fonte: EVT = "energia vertida turbinável (EVT)"; SINC = "disponibilidade sincronizada"; AFL = "afluência"; AFL-N = "afluência e nível do reservatório"; AFL-NV = "afluência, níveis e volume útil"; PROG = "programação diária".

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

A legenda cita só os conjuntos carregados (e `projeto`); se nenhum da entrada estiver carregado, cita todos os da entrada. Uma entrada com `todos` cita todos os seus conjuntos, carregados ou não (só a linha DICIONARIOS da FONTES).

### 5.4 Abas na FONTES (`fontes._entrada_aba`)

| Aba | Entrada |
|---|---|
| CONSTATACOES, CONCLUSAO | todos os conjuntos carregados e as conferências cujo conjunto está carregado; calculado |
| PARAMETROS | `projeto` e os conjuntos carregados |
| DICIONARIOS | os dez conjuntos do catálogo, carregados ou não (`todos`) |
| INDICADORES_ANUAIS, INDICADORES_GLOBAIS | `tab_indicadores_anuais` |
| COBERTURA_POR_ANO | evt, calculado; AGENTES: evt |
| EVT_MENSAL, EVT_MES_DO_ANO | `evt_mensal` |
| EVT_POR_FAIXA_GERACAO | `tab_evt_por_nivel` |
| PERFIL_HORARIO_GERACAO | evt, conferência `geracao`, calculado; PERFIL_HORARIO_EVT: evt, sem outra fonte EVT, calculado |
| EVENTOS_PARADA_COM_EVT, HORAS_GERACAO_ZERO_MES, EVENTOS_INDISP_TOTAL, VALIDACAO_REGRAS, EXTREMOS | `tab_eventos_parada_evt`, `tab_geracao_zero`, `tab_eventos_indisponibilidade`, `tab_regras_validacao`, `tab_extremos` |
| ANOMALIAS, RESUMO_ANOMALIAS | `tab_registros_sinalizados` |
| PERFIL_ESTATISTICO_ANUAL | evt; geracao, disponibilidade, vazoes; EVT; calculado |
| ONS_DISP_ANUAL_USINA, ONS_UG_ANUAL, ONS_DECOMPOSICAO_TAXAS, ONS_DIVERGENCIAS | as tabelas `tab_ons_*` correspondentes |
| ONS_HORAS_UG_ANUAL, ONS_HORAS_UG_MENSAL | `tab_ons_horas` |
| ONS_TEIFA_TEIP | teif_teip, conferência `teifa_teip` |
| PROG_DIAS_AUSENTES, PROG_AUDITORIA_ARQUIVOS | programacao |
| DISP_CONFERENCIA | disponibilidade, evt; conferência `disponibilidade`; DISP_DIVERGENCIAS: `tab_disponibilidade_divergencias` |
| DISP_AUSENCIAS, DISP_AUDITORIA | disponibilidade |
| HID_ALINHAMENTO | hidrologia, evt; conferência `vazoes` |
| HID_ANUAL, HID_MENSAL | `tab_hidrologia_anual`; HID_PERFIL_HORA_DO_DIA: `tab_hidrologia_perfil` |
| HID_AUSENCIAS, HID_AUDITORIA | hidrologia |
| GER_AUSENCIAS, GER_AUDITORIA | geracao |
| CAD_FICHA | `bloco_cadastro`; CAD_AUDITORIA: cadastro |
| demais `PROG_`, `DISP_`, `HID_` e `GER_` (por prefixo) | `tab_programacao_mensal`, `tab_disponibilidade_paradas`, `tab_faixas_afluencia` e `tab_geracao_oficial` |
| aba sem entrada | `origem não mapeada`, "—", "—", "não", com aviso no log |

### 5.5 Textos das legendas (`fontes.legenda_fonte`)

- Formato: `<prefixo> <conjunto (identificador), obtido em dd/mm/aaaa>; …. Conferência: <texto>; …. Sem outra fonte para conferir: <dados>.` O prefixo é `PREFIXO_FONTE` ("Fonte dos dados:") ou, com `calculado`, `PREFIXO_CALCULADO` ("Calculado neste relatório a partir de:"); as partes de conferência e de dados sem outra fonte só aparecem quando a entrada as tem.
- `projeto` aparece como "parâmetros do projeto (origem na tabela de parâmetros)"; sem data, `SEM_REGISTRO` ("data de obtenção não registrada"); chave fora do mapa, "Fonte dos dados: origem não mapeada.", com aviso.
- Identificador e nome de cada conjunto: `fontes.CONJUNTOS`, com os valores do perfil (FR-025).
- Conferência sem o conjunto carregado: "`<dado>`: conferência com `<conjunto>` não feita nesta execução". TEIFa e TEIP sem mês com a janela completa: "TEIFa e TEIP: conferência com Taxas TEIFa e TEIP não feita nesta execução".
- Textos das conferências com o conjunto carregado: FR-026. Na TEIFa e na TEIP, os meses comparados, os reproduzidos e a diferença máxima (com três casas) vêm de `ons["recalculo_resumo"]`, gravados pela Conferência; `meses` igual a zero dá o texto de "não feita nesta execução". Só sem essa contagem (chamada direta), a legenda a refaz sobre `ons["recalculo_taxas"]`, comparando `diferenca_absoluta` (|diferença| arredondada a `CASAS_COMPARACAO` casas) com `TOLERANCIA_REPRODUCAO_TAXAS_PP`. "Abaixo da meta de 99%" usa `META_ALINHAMENTO_HIDROLOGIA_PCT`.

### 5.6 Constantes

| Constante | Valor | Onde | Uso |
|---|---|---|---|
| `DEFAULT_PLOT_DPI` | 300 | `src/comum/regras.py` | resolução das figuras |
| `TAMANHO_FIGURA_PADRONIZADA` | (11, 4,3) pol | `src/comum/regras.py` | figuras 01, 02, 05 e 06 |
| `DURACAO_MINIMA_EVENTO_RELATORIO_H` | 24 h | `src/comum/regras.py` | indisponibilidade total na tabela e nas faixas da figura 01 |
| `NUMERO_EVENTOS_RELATORIO` | 15 | `src/comum/regras.py` | eventos de parada com EVT, de desvio da programação e períodos de divergência mostrados |
| `MAXIMO_ITENS_CONCLUSAO` | 5 | `src/comum/regras.py` | itens por lista no PDF e no Markdown |
| `HORAS_DIURNAS`, `HORAS_NOTURNAS` | 9h às 15h; 20h às 5h | `src/comum/regras.py` | textos, figura 08 e parâmetros |
| `LIMIAR_GERACAO_PARADA_MW`, `LIMIAR_DESVIO_PROGRAMACAO_MW`, `JANELA_TAXAS_MESES` | 1 MW; 5 MW; 60 meses | `src/comum/regras.py` | cabeçalhos, subtítulos e notas das tabelas, cartão da capa, notas metodológicas e parâmetros |
| demais `LIMIAR_*`, `FRACAO_PLENA_CARGA`, tolerâncias (como `TOLERANCIA_IDENTIDADE_HORAS`, 0,1 h), `META_ALINHAMENTO_HIDROLOGIA_PCT`, `LIMIAR_CONCLUSAO_*` | regras gerais | `src/comum/regras.py` | notas, legendas e parâmetros (texto, nunca recálculo) |
| `TOLERANCIA_REPRODUCAO_TAXAS_PP`; `CASAS_COMPARACAO` | 0,001 p.p.; 9 casas | `src/comum/regras.py`; `src/conferencia/resultado.py` | contagem de reserva dos meses reproduzidos na legenda da TEIFa e da TEIP |
| `PASTA_TEMPORARIA` | `.gravando` | `src/relatorio/etapa.py` | pasta, dentro de `reports/<slug>/`, onde as saídas são geradas e conferidas antes da troca |
| `MARGEM_LATERAL`, `MARGEM_SUPERIOR`, `MARGEM_INFERIOR` | 36, 50 e 42 pt | `src/relatorio/pdf.py` | página |
| `ALTURA_MAXIMA_FIGURA` | 285 pt | `src/relatorio/pdf.py` | figuras não padronizadas |
| `FIGURAS_PADRONIZADAS` | `serie_temporal`, `evt_mensal`, `disponibilidade_sincronizada`, `vazoes_defluentes` | `src/relatorio/pdf.py` | largura útil |
| `LINHAS_TABELA_INTEIRA`, `LINHAS_MINIMAS_NA_PAGINA` | 12; 6 | `src/relatorio/pdf.py` | paginação das tabelas |
| `ALTURA_ABERTURA_CURTA` | 150 pt | `src/relatorio/pdf.py` | abertura junto do primeiro bloco |
| `BLOCOS_CAPA_TRES` | identificação 0,26 (chave de 62 pt); cadastro 0,38 (112 pt); parâmetros 0,36 (88 pt) | `src/relatorio/pdf.py` | capa com três blocos; com dois, metade da largura e chave de 118 pt |
| cores e rampas | plano, D7 | `src/relatorio/figuras.py` | figuras |
| `TOLERANCIA_RELATIVA_CELULA` | 1e-12 | `src/comum/comparacao.py` | igualdade de células numéricas |
| `MAXIMO_CELULAS_POR_ABA` | 20 | `src/comum/comparacao.py` | células listadas por aba |
| `IGNORADOS` | `etapa.json` | `src/comum/comparacao.py` | fora da comparação |

### 5.7 Estados e códigos

| Situação | Código | `etapa.json` |
|---|---|---|
| saídas gravadas | 0 | `concluida` |
| Análises ausentes, com falha, desatualizadas ou em outro formato | 5 | não é gravado; nada é gravado |
| `resultados.pkl` em outra versão, campo ausente, falha de figura, planilha, Markdown ou PDF, saída vazia ou PDF inválido na conferência, falha na troca | 1 | `falha`, com `resumo.erro`; as saídas anteriores ficam como estavam |
| interrupção pelo usuário (Ctrl+C) | 1 | `falha`, com `resumo.erro` "interrompida pelo usuário"; as saídas anteriores ficam como estavam |
| `--data-geracao` inválida ou opção inválida | 2 | não é gravado (recusa antes da etapa) |
| perfil inválido | 4 | não é gravado |

### 5.8 Avisos no log, sem falhar

- constatação sem seção no mapa, ou com a seção ausente;
- chave de figura ou tabela, ou aba, sem entrada no mapa de fontes;
- figura sem legenda descritiva;
- fontes TrueType ausentes (Helvetica);
- no PDF, quantidade de legendas de fonte diferente da de tabelas, blocos e figuras desenhados, ou de constatações emitidas diferente das calculadas.

Em nível INFO, a etapa registra também cada saída gravada e a remoção de uma figura opcional de execução anterior ("Figura de execução anterior removida: `<arquivo>`"). Uma troca interrompida gera um erro no log: "Troca das saídas do relatório interrompida; as da execução anterior foram mantidas." ou, se algum arquivo não voltou, a lista deles e a pasta `.anteriores_<AAAAMMDDTHHMMSS>/` onde estão as versões anteriores.

### 5.9 Formatação (`src/comum/formatacao.py`)

- `fmt_num`: milhar ".", decimal ","; ausente, NaN ou infinito vira "–"; `fmt_int` sem casas; `fmt_pct` com "%";
- `fmt_pp`: sinal "+" ou "−" e " p.p.";
- `fmt_data` "dd/mm/aaaa"; `fmt_data_hora` "dd/mm/aaaa HHh"; `fmt_mes_ano` "mmm/aaaa" (jan a dez); `fmt_utc` "dd/mm/aaaa HH:MM UTC";
- `fmt_lista`: "a, b e c"; `plural`; `numero_por_extenso` de 1 a 10 ("duas", no feminino, para 2);
- anos parciais com "*" (`_rotulo_ano`) nas tabelas e nas figuras, com a nota "* ano parcial" nas figuras.
