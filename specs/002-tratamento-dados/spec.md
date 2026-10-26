# Spec da Etapa 2: Tratamento de dados

**Etapa**: 2 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-23

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

Transformar o que a Coleta extraiu da usina em dados prontos para a Conferência e as Análises, sem descartar nenhum registro. A etapa padroniza os números, confere a base de EVT pelas regras R1 a R9 e sinaliza os registros suspeitos, põe todas as séries na hora de início usada pela EVT, deixa um valor por hora, recorta tudo no período da base de EVT, lista as ausências, sinaliza os valores impossíveis das bases complementares e grava os dados tratados com cópia da versão anterior e conferência da gravação. Ela não acessa o portal do ONS, não compara uma fonte com outra (isso é da Conferência) e não calcula indicadores de análise.

A etapa atende todos os tipos de usina que os dados abertos do ONS cobrem: UHE, PCH, CGH, UTE, UTN, EOL e UFV. O tipo e a cobertura declarados no perfil definem os conjuntos tratados (seção "Aplicabilidade por tipo"):
- **hidrelétrica com EVT** (UHE, PCH ou CGH com série própria na Energia Vertida Turbinável): tudo como descrito acima;
- **usinas sem EVT**: o período é o da série de referência gravada pela Coleta, e a etapa grava a base horária comum, que as Análises usam no lugar da base de EVT;
- **térmicas e nucleares** (UTE, UTN): também o despacho por motivo, o CVU e o CMO;
- **eólicas e solares** (EOL, UFV): também o fator de capacidade e as restrições de operação (constrained-off), na resolução publicada de 30 minutos e em hora cheia, com a energia cortada.

Todo dado tratado guarda o nível em que o ONS o publica (usina ou conjunto), e nenhum número de conjunto é dividido entre as usinas.

## Entradas e saídas

**Comando**: `python -m src tratamento --usina <slug>`, sem opções próprias, para todos os tipos de usina. As regras comuns do fluxo (sintaxe, `--log-level`, perfil da usina, `etapa.json`, pré-requisitos e tabela completa de códigos de saída) estão na spec da Coleta de dados.

**Entradas** (a etapa lê só estas):

| Onde | O que |
|---|---|
| `data/usinas/<slug>/coleta/` | `etapa.json` da Coleta, concluído e no formato 2 (nas usinas sem EVT, com o período da série de referência no `resumo`); nas hidrelétricas com EVT, `dicionario_evt.json` (cópia do dicionário de dados da EVT gravada pela Coleta) e `evt_extraido.csv`; `<conjunto>_extraido.parquet` de indicadores, programação, disponibilidade, hidrologia e geração; `auditoria_<conjunto>.csv` de programação, disponibilidade, hidrologia e geração |
| `data/usinas/<slug>/coleta/`, só nos tipos que os usam | usinas sem EVT: `geracao_complemento.parquet` (nível de cada hora da série de referência) e `trechos.csv`; térmicas: `despacho_extraido.parquet`, `cvu_extraido.parquet` e `cmo_extraido.parquet`; eólicas e solares: `fator_capacidade_extraido.parquet`, `restricao_detalhe_extraido.parquet`, `restricao_razao_extraido.parquet` e, com os membros do conjunto no perfil, `restricao_membros_extraido.parquet`; a auditoria de cada um, menos a dos membros |
| `usinas/<slug>/perfil.toml` | `usina.nome` e `identificacao.cod_usina` (relatório de validação e planilha da EVT); `parametros.potencia_instalada_mw`, `parametros.unidades_geradoras`, `parametros.engolimento_nominal_ug_m3s`, `parametros.queda_bruta_m`, `parametros.perda_hidraulica_m` e `parametros.rendimento_turbina_gerador` (limites de R6 e R8); `usina.tipo` e a tabela `[cobertura]` (conjuntos tratados, série de referência e nível de cada conjunto); nas térmicas, `[[identificacao.planejamento]]` (códigos de planejamento, com o período de cada um: despacho e CVU) e `usina.subsistema` (CMO) |

Os cadastrais não têm tratamento: a ficha do cadastro, a composição do conjunto, a capacidade de geração (da usina e das usinas do conjunto) e o tipo publicado na série do conjunto vão da Coleta direto para as etapas seguintes.

**Saídas** em `data/usinas/<slug>/tratamento/`, conforme o tipo e a cobertura da usina (seção "Aplicabilidade por tipo"). Todos os CSV usam `;`, ponto decimal, UTF-8 e datas `AAAA-MM-DD HH:MM:SS`.

| Arquivo | Conteúdo |
|---|---|
| `evt_tratado.parquet`, `evt_tratado.xlsx`, `evt_tratado.csv` | base de EVT tratada: as 20 colunas extraídas (identificação, `cod_usina`, `din_instante`, dez grandezas, `arquivo_origem`, `tipo_match`) e as 5 de sinalização (FR-013) |
| `validacao_fisica.csv`, `validacao_fisica.md` | resultado das regras R1 a R9 (FR-014) |
| `indicadores_ug_mensal.csv` | `mes`, `ug`, `cod_equipamento`, `potencia_mw`, `dispf`, `indisppf`, `indispff`, `dmdff`, `fdff`, `tdff`, `id_usina`, `agente`, `modalidade`, `arquivo_origem` |
| `indicadores_ug_anual.csv` | as mesmas colunas, com `ano` no lugar de `mes` |
| `horas_estado_mensal.csv` | `mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HDCE`, `HEDP`, `HEDF`, `num_versao`, `residuo_identidade_h`, `potencia_mw` |
| `teifa_teip_mensal.csv` | `mes`, `teifa`, `teip`, `num_versao`, `din_calculo`; com as taxas operativas da usina, também `teifa_oper`, `teip_oper`, `num_versao_oper`, `din_calculo_oper` (FR-045) |
| `indicadores.xlsx` | as quatro tabelas acima e as siglas das horas (FR-025) |
| `programacao_horaria.csv` | `din_instante`, `geracao_programada_mw`, `patamares` |
| `programacao_dias_ausentes.csv` | `dia` |
| `disponibilidade_horaria.csv` | `din_instante`, `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada`, `qualidade`, `arquivo_origem` |
| `hidrologia_horaria.csv` | `din_instante`, `din_instante_publicado`, `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas`, `val_nivelmontante`, `val_niveljusante`, `val_volumeutil`, `qualidade`, `arquivo_origem` |
| `geracao_horaria.csv` | `din_instante`, `val_geracao`, `qualidade`, `arquivo_origem` |
| `disponibilidade_ausencias.csv`, `hidrologia_ausencias.csv`, `geracao_ausencias.csv` | `tipo`, `inicio`, `fim`, `horas` (FR-018) |
| `auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv`, `auditoria_geracao.csv` | `arquivo`, `formato`, `periodo`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina`, `linhas_so_identificador`, `linhas_so_conferencia`, `horas_usina`, `valores_invalidos`, `duplicatas_conflitantes`, `recursos_duplicados_catalogo`, `status`, `mensagem` (FR-020) |
| `base_horaria.csv` | usinas sem EVT: `din_instante`, `geracao_mw`, `nivel`, `disponibilidade_operacional_mw`, `disponibilidade_sincronizada_mw`, `geracao_programada_mw`, `trecho`, `sinalizacoes` (FR-035) |
| `despacho_horario.csv` | térmicas: `din_instante`, `unidades`, `codigos` e, somadas as unidades de planejamento, a geração programada (`val_prog*`, 17 colunas) e a verificada (`val_verif*`, 15 colunas) de cada motivo de despacho (FR-037) |
| `despacho_unidades_horario.csv` | térmicas: `din_instante`, `codigo`, `nom_tipopatamar`, as mesmas 32 colunas por motivo, `tip_restricaoeletrica`, `arquivo_origem` (FR-037) |
| `despacho_ausencias.csv` | térmicas: `codigo`, `tipo`, `inicio`, `fim`, `horas` (FR-037) |
| `cvu_semanal.csv` | térmicas: `codigo`, `semana_inicio`, `semana_fim`, `num_revisao`, `val_cvu`, `sinal_cvu`, `revisoes`, `arquivo_origem` (FR-038) |
| `cmo_semanal.csv` | térmicas: `subsistema`, `semana_inicio`, `semana_fim`, `din_instante_publicado`, `val_cmomediasemanal`, `val_cmoleve`, `val_cmomedia`, `val_cmopesada`, `arquivo_origem` (FR-039) |
| `cvu_ausencias.csv`, `cmo_ausencias.csv` | térmicas: `codigo` (no CMO, o subsistema), `inicio`, `fim`, `semanas` (FR-038, FR-039) |
| `fator_capacidade_horario.csv` | eólicas e solares: `din_instante`, `nivel`, `val_geracaoprogramada`, `val_geracaoverificada`, `val_capacidadeinstalada`, `val_fatorcapacidade`, `sinal_fc_fora_0_1`, `sinal_acima_capacidade`, `arquivo_origem` (FR-044) |
| `restricao_semi_horaria.csv` | eólicas e solares: `din_instante`, `val_geracaoverificada`, `val_geracaoestimada`, `val_recurso`, `flg_recurso_invalido`, `flg_geracaorestrita`, `sinal_recurso_invalido`, `sinal_estimada_ausente`, `restrita`, `sem_marca_restricao`, `energia_cortada_mwh`, `cod_razaorestricao`, `nivel_razao`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene`, `arquivo_origem` (FR-041 a FR-043) |
| `restricao_horaria.csv` | eólicas e solares: `din_instante`, `val_geracaoverificada`, `val_geracaoestimada`, `val_recurso`, `semi_horas_recurso_invalido`, `semi_horas_estimada_ausente`, `semi_horas_restritas`, `energia_cortada_mwh` (FR-041) |
| `restricao_razao_semi_horaria.csv` | eólicas e solares: `din_instante`, `nivel`, `val_geracao`, `val_geracaolimitada`, `val_disponibilidade`, `val_geracaoreferencia`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene`, `cod_razaorestricao`, `arquivo_origem` (FR-043) |
| `restricao_membros_horaria.csv` | eólicas e solares em conjunto, com os membros no perfil: `din_instante`, `id_ons`, `val_geracaoverificada` (FR-041) |
| `fator_capacidade_ausencias.csv`, `restricao_ausencias.csv` | `tipo`, `inicio`, `fim`, `horas` (FR-018) |
| `auditoria_despacho.csv`, `auditoria_fator_capacidade.csv`, `auditoria_restricao_detalhe.csv` | as colunas das auditorias acima (FR-020) |
| `auditoria_cvu.csv`, `auditoria_cmo.csv` | as mesmas, com `semanas_usina` no lugar de `horas_usina` (FR-020) |
| `<arquivo>.bak` | versão imediatamente anterior de cada arquivo acima (FR-028) |
| `etapa.json` | manifesto da etapa, no formato 2, com o `resumo` (FR-033) |

Nas séries horárias, as linhas seguem a ordem das horas, e `arquivo_origem` é o arquivo de onde veio o valor mantido. Na hidrelétrica com EVT, a etapa grava os 21 arquivos de dados das linhas acima, da base de EVT às auditorias das séries; nos demais tipos, só os do tipo e da cobertura, sem nenhum arquivo da EVT.

**Códigos de saída**:

| Código | Quando |
|---|---|
| 0 | tratamento concluído, inclusive com violações de R2 a R9 e valores sinalizados |
| 1 | erro: coluna obrigatória ausente, dicionário ausente, instante inválido ou valor negativo na base de EVT, sem gravar nada (FR-005, FR-006, FR-007, FR-012); arquivo da Coleta ilegível; falha de gravação ou interrupção pelo usuário, com o arquivo de volta à versão anterior (FR-030) |
| 5 | Coleta da usina sem resultados concluídos, desatualizada ou em formato antigo (anterior ao 2); nada é gravado |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tratar os dados da usina a partir da Coleta (Priority: P1)

Como fiscal da AGEMS, quero tratar de uma vez, com um comando, tudo o que a Coleta extraiu da usina e encontrar os dados tratados na pasta da usina, com um resumo do que foi feito. Assim a Conferência e as Análises partem sempre dos mesmos dados, e eu sei quantos registros foram sinalizados e quantas horas faltam em cada base.

**Why this priority**: É a entrada de todas as etapas seguintes; sem ela, o fluxo para. E os dados tratados têm de continuar sendo os que sustentam o relatório aprovado (SC-001).

**Independent Test**: Com a Coleta concluída para o perfil da São Domingos, executar `python -m src tratamento --usina sao_domingos` e conferir a SC-001. Executar de novo e conferir que nada é regravado. Executar para um perfil sem Coleta e conferir o código 5.

**Acceptance Scenarios**:

1. **Given** a Coleta da usina concluída, **When** a etapa é executada, **Then** ela lê só as entradas previstas, grava os arquivos da tabela de saídas em `data/usinas/<slug>/tratamento/` e o `etapa.json` com o resumo, e termina com 0.
2. **Given** a Coleta da usina não concluída ou desatualizada, **When** a etapa é executada, **Then** ela termina com 5, não grava nada e indica a Coleta como etapa a executar antes.
3. **Given** os extraídos da São Domingos regenerados dos dados brutos locais do relatório aprovado (perfil da São Domingos), **When** a etapa é executada, **Then** o `resumo` do `etapa.json` e os arquivos tratados trazem os números de referência da SC-001.
4. **Given** uma segunda execução sem mudança nas entradas, **When** a etapa termina, **Then** todos os arquivos ficam `INALTERADO` e os `.bak` ficam como estavam.
5. **Given** o perfil de outra usina, **When** a etapa é executada, **Then** os limites de R6 e R8, o cabeçalho do relatório de validação e o nome da aba da planilha da EVT saem do perfil dela.

---

### User Story 2 - Base de EVT com números uniformes, em três formatos (Priority: P1)

Como fiscal, quero que as dez grandezas da EVT sejam sempre números, sem mistura de "número" e "geral" no Excel nem diferença de separador decimal, e que um valor ausente continue ausente, nunca zero. Assim abro a base direto no Excel ou numa ferramenta de análise sem erro de soma ou de média.

**Why this priority**: Toda conta das etapas seguintes depende do tipo certo. Um ausente convertido em zero fabricaria uma medição: uma hora sem dado pareceria usina parada.

**Independent Test**: Com uma amostra que tenha vírgula decimal, espaços e célula vazia, conferir que as dez grandezas saem como números, que `"30,500"` vira 30,5 e `" 100.0 "` vira 100,0, que a célula vazia continua vazia e que os três arquivos são gravados.

**Acceptance Scenarios**:

1. **Given** a base de EVT extraída, **When** tratada, **Then** as dez grandezas ficam como números reais.
2. **Given** um valor com vírgula decimal ou espaços (`"30,500"`, `" 100.0 "`), **When** tratado, **Then** vira o número correspondente (30,5; 100,0).
3. **Given** um valor ausente ou não numérico numa grandeza, **When** tratado, **Then** fica vazio, a quantidade por coluna vai para o log e nada vira zero.
4. **Given** um `cod_usina` inválido, **When** tratado, **Then** fica vazio, com aviso, e nunca vira 0.
5. **Given** um `din_instante` que não pode ser lido, **When** tratado, **Then** a etapa para com código 1 e nada é gravado.
6. **Given** a base tratada, **When** gravada, **Then** saem o Parquet, a planilha com números nativos, numa aba com o nome da usina (perfil da São Domingos: `UHE_SAO_DOMINGOS`), e o CSV com `;`, ponto decimal e todas as casas decimais.

---

### User Story 3 - Regras R1 a R9: sinalizar sem excluir (Priority: P1)

Como fiscal, quero conferir 100 % dos registros da EVT pelas identidades entre as grandezas publicadas pelo ONS (R1 a R5) e pelos parâmetros técnicos da usina (R6 a R9), com os registros suspeitos sinalizados e mantidos na base, e um relatório de validação que diga o que cada regra mostrou. Assim sei quais horas olhar com cuidado, sem perder nenhum dado publicado.

**Why this priority**: As identidades do ONS mostram só que as colunas derivadas foram calculadas de forma coerente; não mostram que os valores medidos estão certos. Um valor fisicamente impossível passa por R1 a R5 e só aparece quando comparado com os parâmetros da usina.

**Independent Test**: Validar uma base sintética com um registro conhecido para cada regra e conferir as contagens, as colunas de sinalização e o relatório. Validar uma base com um valor negativo e conferir a parada.

**Acceptance Scenarios**:

1. **Given** a base de EVT tratada, **When** validada, **Then** o resultado de cada regra (registros, conformes, violações, taxa e desvios) é apurado sem pressupor conformidade.
2. **Given** um registro que viola R6 a R9, **When** sinalizado, **Then** ele continua na base, a coluna de cada regra violada fica verdadeira e `qualidade_registro` lista os códigos separados por `;`; os demais registros ficam `OK`.
3. **Given** o registro de 15/05/2019 14h, com geração de 68,743 MW, disponibilidade de 22,817 MW e produtividade de 0,929 MW/(m³/s) (perfil da São Domingos), **When** validado, **Then** recebe `R6;R7;R8` e continua na base.
4. **Given** o perfil da São Domingos, **When** os limites são calculados, **Then** são 50,4 MW (48 × 1,05), 171,15 m³/s (2 × 81,5 × 1,05, mostrado como 171,2) e a faixa de 0,214 a 0,398 MW/(m³/s) em torno da produtividade nominal de 0,3063 (perfil da São Domingos).
5. **Given** ao menos um registro com valor negativo, **When** validado, **Then** a etapa para com código 1, antes da sinalização, do relatório e de qualquer gravação.
6. **Given** valores ausentes, **When** validados, **Then** não contam como violação, e o total vai para o log.
7. **Given** a validação concluída, **When** o relatório é gravado, **Then** ele traz a tabela das nove regras, uma frase por regra gerada dos números, a ressalva sobre R1 a R5 e os 40 primeiros registros sinalizados em ordem cronológica.

---

### User Story 4 - Bases horárias complementares na hora da EVT (Priority: P2)

Como fiscal, quero a disponibilidade, os dados hidrológicos e a geração por usina na mesma convenção de hora da EVT, com um valor por hora, só no período da EVT, com as horas que faltam listadas e os valores impossíveis sinalizados. Assim a Conferência compara a hora certa com a hora certa, e as Análises não usam leituras impossíveis.

**Why this priority**: As bases complementares acrescentam seções e conferências ao relatório; sem elas, o relatório sai só com a EVT. Mas uma hora deslocada ou repetida invalidaria todos os cruzamentos.

**Independent Test**: Com arquivos sintéticos de um conjunto (hora de fim com 23:59, hora repetida em dois arquivos, mês sem arquivo, mês sem a usina, horas faltando, valores impossíveis), conferir a série, as ausências, as sinalizações e a auditoria.

**Acceptance Scenarios**:

1. **Given** dados hidrológicos publicados na hora de fim, **When** tratados, **Then** 01:00 vira 00:00, 23:59 vira 23:00 do mesmo dia e o instante publicado fica guardado.
2. **Given** a mesma hora em dois arquivos, com valores diferentes, **When** tratada, **Then** fica o valor do arquivo publicado por último, e a repetição conflitante é contada na auditoria do outro arquivo.
3. **Given** horas fora do período da base de EVT, **When** tratadas, **Then** saem da série.
4. **Given** um mês sem arquivo, um mês com arquivo mas sem a usina e horas isoladas faltando, **When** as ausências são listadas, **Then** aparecem como `MES_SEM_ARQUIVO`, `MES_SEM_USINA` e `HORAS`, e nenhuma hora é interpolada.
5. **Given** uma hora de disponibilidade com a sincronizada acima da operacional em mais de 0,01 MW, **When** sinalizada, **Then** recebe `D1` e sai inteira do uso nas etapas seguintes.
6. **Given** uma hora hidrológica com volume útil negativo e vazões válidas, **When** sinalizada, **Then** recebe `H2`; só o volume útil sai do uso, e as vazões continuam valendo.
7. **Given** um nível de jusante a mais de 10 m da mediana da série, **When** sinalizado, **Then** recebe `H4`, e só esse nível sai do uso.
8. **Given** um campo vazio, **When** tratado, **Then** continua vazio, não vira zero e não é sinalizado.

---

### User Story 5 - Indicadores por unidade geradora e programação diária (Priority: P2)

Como fiscal, quero os indicadores oficiais por unidade geradora, as horas por estado operativo, a TEIFa e a TEIP na versão mais recente e no período da EVT, e a programação diária em valores horários, com os dias sem arquivo listados. Assim a Conferência refaz as taxas e as Análises cruzam a programação com a operação hora a hora.

**Why this priority**: Sustentam as seções de indicadores e de programação; sem elas, o relatório sai sem essas seções.

**Independent Test**: Com arquivos sintéticos (mês repetido em dois arquivos de indicadores, horas por estado em duas versões, identidade com resíduo, patamares de 30 minutos e dias sem arquivo), conferir as tabelas tratadas e a lista de dias ausentes.

**Acceptance Scenarios**:

1. **Given** o mesmo mês e unidade em dois arquivos de indicadores, **When** tratados, **Then** fica a linha do arquivo lido por último, com aviso no log.
2. **Given** horas por estado publicadas em duas versões, **When** tratadas, **Then** fica, para cada mês, unidade e estado, o valor de maior número de versão.
3. **Given** um mês-unidade em que HP difere da soma das parcelas em mais de 0,1 h, **When** tratado, **Then** o resíduo fica na tabela, o log avisa e o mês-unidade não é excluído.
4. **Given** TEIFa e TEIP publicadas em mais de uma versão, **When** tratadas, **Then** fica a de maior número de versão, como fração.
5. **Given** indicadores fora do período da base de EVT, **When** recortados, **Then** ficam só os meses e os anos do período.
6. **Given** os patamares 1 e 2 de um dia, com 10 e 20 MW, e o patamar 3 sozinho, com 22 MW, **When** convertidos, **Then** a hora 00:00 fica com 15 MW e 2 patamares, e a hora 01:00 com 22 MW e 1 patamar.
7. **Given** dias sem arquivo de programação, **When** a lista é montada, **Then** cada um deles, do primeiro dia com arquivo até o fim do período, aparece nela.

---

### User Story 6 - Cópia da versão anterior e conferência da gravação (Priority: P2)

Como fiscal, quero que toda regravação de um dado tratado guarde antes a versão anterior e confira a nova gravação no disco. Assim volto aos dados que sustentaram uma constatação se uma execução nova der resultado inesperado ou for interrompida.

**Why this priority**: Não muda nenhum resultado, mas protege os dados do relatório contra falhas de execução e de disco.

**Independent Test**: Numa pasta de teste, gravar o mesmo arquivo quatro vezes (sem versão anterior, com conteúdo alterado, com conteúdo idêntico e com falha simulada) e conferir o arquivo e o `.bak` depois de cada passo.

**Acceptance Scenarios**:

1. **Given** um arquivo tratado existente, **When** a etapa o regrava com conteúdo diferente, **Then** a versão atual vai antes para `<nome do arquivo>.bak`, no lugar da cópia anterior, e a nova gravação é conferida no disco.
2. **Given** conteúdo novo idêntico ao atual, **When** a etapa é executada, **Then** o arquivo não é regravado e o `.bak` fica como estava.
3. **Given** uma falha durante a gravação ou na conferência, **When** detectada, **Then** a versão anterior volta, o log diz o arquivo e a etapa termina com código 1.
4. **Given** um arquivo gravado pela primeira vez, **When** a etapa é executada, **Then** nenhuma cópia é criada e a gravação é conferida.
5. **Given** cópias `.bak` na pasta do Tratamento, **When** qualquer etapa lê os dados tratados, **Then** nenhuma cópia é lida como dado.
6. **Given** uma planilha regravada com os mesmos dados, **When** comparada, **Then** fica `INALTERADO`: a comparação usa a assinatura dos dados, e não os bytes, que mudam a cada gravação.

---

### Edge Cases

- **Coleta não concluída, desatualizada ou em formato antigo**: código 5, nada gravado.
- **Dicionário da EVT ausente** (a Coleta registrou falha ao obtê-lo): código 1, nada gravado. Grandeza ausente do dicionário: só aviso.
- **Coluna obrigatória ausente na EVT**: código 1. Sem `arquivo_origem` ou `tipo_match`: só aviso.
- **Instante inválido na EVT**: código 1, nada gravado. `cod_usina` inválido: fica vazio, com aviso, e a etapa segue.
- **Valor negativo na EVT (R1)**: código 1 antes de qualquer gravação, inclusive do relatório de validação; o caso é analisado pelo log.
- **Valor ausente numa grandeza**: fica vazio, é contado e não viola regra.
- **Arredondamento**: nas identidades, diferenças de até 0,0001 não contam; em R1, valores entre −0,0001 e 0 não contam como negativos.
- **Geração nula**: R5 exige folga igual à disponibilidade; R8 não é avaliada sem vazão turbinada, porque a produtividade não tem sentido físico sem vazão; R9 sinaliza geração acima de 1,0 MW com vazão turbinada nula.
- **Valores no limite**: geração exatamente 1,0 MW acima da disponibilidade não viola R7; geração de exatamente 1,0 MW com vazão turbinada nula não viola R9.
- **Várias regras no mesmo registro**: todas são sinalizadas (ex.: `R7;R8`).
- **Última hora do dia nos dados hidrológicos**: publicada às 23:59, vira 23:00 do mesmo dia; as demais horas de fim recuam 1 h.
- **Mesma hora em arquivos diferentes** (republicação pelo ONS): fica o arquivo publicado por último; a repetição com valores diferentes é contada; com valores iguais, só unificada.
- **Séries que vão além da base de EVT**: começam antes ou terminam depois do período; só as horas do período ficam.
- **Início do horário de verão**: a hora que não existe no horário legal aparece como hora ausente nas séries, sem preenchimento.
- **Campo vazio** (ex.: nível de jusante, vazão vertida não turbinável): continua vazio e não é sinalizado.
- **Volume útil negativo com o reservatório rebaixado numa parada**: H2 tira só o volume útil; as vazões e os níveis da hora continuam valendo.
- **Leitura trocada de nível** (centenas de metros fora do normal): H4 tira só o nível afetado; um rebaixamento real de poucos metros não é sinalizado.
- **Pico isolado de afluência**: não é sinalizado; não há limite superior para as vazões, só para valores negativos.
- **Programação**: hora com um só patamar fica com `patamares` igual a 1; a lista de dias ausentes começa no primeiro dia com arquivo, porque a programação pode começar depois do início da base de EVT.
- **Indicadores**: mês e unidade repetidos em dois arquivos: fica o lido por último, com aviso; resíduo da identidade acima de 0,1 h: aviso, sem exclusão.
- **Usina sem registros num conjunto complementar** (ex.: fora da programação diária): as tabelas desse conjunto são gravadas sem linhas (nas séries horárias, com as ausências do período), o resumo registra zero e a etapa termina com 0.
- **Tabela sem linhas** (ex.: nenhuma ausência): é gravada assim mesmo.
- **Arquivo aberto em outro programa, disco cheio ou execução interrompida pelo usuário durante a gravação**: o arquivo volta à versão anterior, os temporários são apagados e a etapa termina com 1.
- **Usina sem EVT**: o período vem da série de referência gravada pela Coleta; nenhum arquivo da EVT é gravado, e a base horária comum fica no lugar da base de EVT.
- **Série de referência do conjunto** (PCH, CGH, EOL ou UFV em conjunto sem série própria): a base horária traz o nível `conjunto` nessas horas, e a R7 não é avaliada nelas, porque a disponibilidade é da usina. Com a cobertura da usina e do conjunto na geração, o nível muda hora a hora, conforme o complemento gravado pela Coleta.
- **Restrição com detalhe como série de referência** (eólica ou solar em conjunto com série própria): a base horária é da usina; a disponibilidade e a programação entram nela só quando são da usina, e os números do conjunto ficam nos arquivos próprios, com o nível.
- **Hora com uma só meia-hora** nas semi-horárias: fica fora da hora cheia e é contada nas ausências.
- **Semi-horas sem a coluna da marca de restrição** (fotovoltaica de 05 a 12/2024): ficam com `sem_marca_restricao`, a energia cortada vazia, contadas e fora do total.
- **Estimada 0 com a usina gerando** (acima de 1 MW): estimativa ausente, sinalizada e fora dos totais e das médias da estimada; na semi-hora restrita, o corte não é calculado.
- **Diferença entre a estimada e a verificada fora das semi-horas restritas**: é erro da estimativa, não corte, e não entra na energia cortada.
- **Razão da restrição publicada para o conjunto**: a semi-hora recebe a razão com o nível `conjunto`; a energia cortada continua sendo a da usina.
- **Recurso fisicamente impossível sem a marca do ONS** (vento de até 246 m/s na EOL Praia Formosa, em mar e abr/2024): fica na base tratada como publicado, sem sinalização do Tratamento; o limite físico do recurso (40 m/s; 1.500 W/m²) é aplicado pelas Análises (spec das Análises).
- **CVU publicado como 0,00** (semanas sem CVU da unidade): `sinal_cvu` = `zero`, como o ausente e o negativo; a semana fica no arquivo.
- **CVU com várias revisões na semana operativa**: fica a mais recente; as descartadas são contadas no resumo.
- **CMO publicado na sexta-feira que fecha a semana operativa**: vai para a semana operativa (sábado a sexta) que contém a data publicada.
- **Código de planejamento trocado no tempo** (código novo, ou uma unidade por combustível): cada código entra só no período dele no perfil, e as ausências do despacho e do CVU são listadas por código.
- **Intervalo longo sem dados** num conjunto novo (ex.: meses sem despacho de um código): listado nas ausências, nunca preenchido.
- **Conjunto que troca os códigos de programação no período** (Conj. Chapadão em 07/2025): a soma por patamar usa só os códigos vigentes em cada dia.

---

## Requirements *(mandatory)*

### Functional Requirements

**Execução e entradas (US1)**

- **FR-001**: A etapa DEVE rodar pelo comando `python -m src tratamento --usina <slug>`, sem opções próprias, para todos os tipos de usina. Na hidrelétrica com EVT, a validação R1 a R9, o relatório de validação e os três formatos da base de EVT fazem sempre parte da etapa: não há opção para desligá-los nem para escolher formatos.
- **FR-002**: A etapa DEVE ler só as entradas da tabela "Entradas", gravadas pela Coleta da usina, e o perfil. NÃO DEVE acessar o portal do ONS nem ler nada de `data/raw/` (dados brutos dos conjuntos, versões anteriores deles ou dicionários), nem ler cópias `.bak` ou arquivos temporários como dados.
- **FR-003**: A etapa DEVE tratar os conjuntos do ONS que a Coleta extraiu para a usina, conforme o tipo e a cobertura do perfil (seção "Aplicabilidade por tipo"), menos os cadastrais:
  - na hidrelétrica com EVT, os dez conjuntos do fluxo da hidrelétrica: Energia Vertida Turbinável; indicadores por unidade geradora, mensais e anuais; parâmetros da TEIFa e da TEIP (horas por estado operativo); taxas TEIFa e TEIP; taxas TEIFa Oper e TEIP Oper; programação diária; disponibilidade por usina; dados hidrológicos horários; geração por usina;
  - nas usinas sem EVT, entre esses, os que a cobertura declara, sem a EVT, e os próprios do tipo: o despacho térmico por motivo, o CVU e o CMO, nas térmicas; o fator de capacidade e as restrições por constrained-off com detalhe e com a razão, nas eólicas e solares.
- **FR-004**: O período de referência DEVE ser o da série de referência gravada pela Coleta (FR-054 da spec da Coleta de dados):
  - na hidrelétrica com EVT, o da base de EVT da usina: do primeiro ao último instante horário extraído;
  - nas usinas sem EVT, o `periodo` do `resumo` do `etapa.json` da Coleta.

  As demais bases DEVEM ser recortadas nele; nenhuma série é estendida para antes ou para depois.

**Base de EVT: padronização (US2)**

- **FR-005**: A base de EVT extraída DEVE ter as colunas obrigatórias:
  - as seis de identificação: `id_subsistema`, `nom_subsistema`, `nom_bacia`, `nom_rio`, `nom_agente`, `nom_reservatorio`;
  - `cod_usina` e `din_instante`;
  - as dez grandezas: `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`.

  Faltando alguma, a etapa DEVE parar com código 1 sem gravar nada. Faltando uma coluna de rastreabilidade (`arquivo_origem`, `tipo_match`), DEVE só avisar no log.
- **FR-006**: A etapa DEVE conferir que as dez grandezas constam do dicionário de dados da EVT gravado pela Coleta em `data/usinas/<slug>/coleta/dicionario_evt.json` (grandeza ausente: aviso no log, sem parar) e citar a versão do dicionário no relatório de validação, ou "não identificada", se o dicionário não a informar. Sem o arquivo do dicionário, DEVE parar com código 1 sem gravar nada. O dicionário traz só código, descrição e unidade de cada coluna: NÃO DEVE ser usado como fonte de limites.
- **FR-007**: Tipos da base de EVT:
  - as dez grandezas DEVEM ser números reais: a vírgula decimal vira ponto, e os espaços saem;
  - valor ausente ou não numérico DEVE ficar vazio, contado no log por coluna, e NUNCA virar zero;
  - `cod_usina` DEVE ser inteiro que admite vazio: código inválido fica vazio, com aviso, e nunca vira 0;
  - `din_instante` DEVE ser data e hora sem fuso, no horário publicado pelo ONS; um instante que não possa ser lido DEVE parar a etapa com código 1, sem gravar nada;
  - as colunas de texto (identificação e rastreabilidade) DEVEM ficar sem espaços nas bordas.
- **FR-008**: A base de EVT tratada DEVE ter os mesmos registros da extraída, na mesma ordem, com as colunas extraídas e as cinco de sinalização (FR-013), e o mesmo conteúdo em três formatos:
  - **Parquet**, para ferramentas de análise: grandezas como números reais (`double`), `cod_usina` inteiro, `din_instante` como data e hora (`timestamp`) e sinalizações como verdadeiro/falso;
  - **planilha** (`.xlsx`), para o Excel: uma aba com o nome da usina do perfil (`usina.nome` em maiúsculas, sem acentos, com `_` no lugar dos espaços e dos caracteres que o Excel não aceita em nome de aba, `\ / ? * : [ ]`, cortado em 31 caracteres, o máximo do Excel), cabeçalho congelado, grandezas em células numéricas nativas (formato "Geral", sem número fixo de casas) e instante como data e hora;
  - **CSV**, para qualquer ferramenta: o número real de 64 bits com todas as suas casas, sem arredondamento, e ausente como célula vazia; a conversão do texto da base extraída em número pode mudar só o último algarismo significativo.

**Base de EVT: regras R1 a R9 e sinalização (US3)**

- **FR-009**: A etapa DEVE avaliar 100 % dos registros da base de EVT pelas nove regras abaixo, com ε = 0,0001. Cada regra conta registros, não células.

  | Regra | Grupo | O registro viola quando | Desvio informado |
  |---|---|---|---|
  | R1. Não-negatividade das grandezas | Consistência interna ONS | alguma das dez grandezas é menor que −ε | valor absoluto do menor valor encontrado |
  | R2. Energia vertida turbinável contida na energia vertida | Consistência interna ONS | `val_energiavertida` − `val_energiavertidaturbinavel` < −ε | maior déficit |
  | R3. Parcelas da vazão vertida contidas no total | Consistência interna ONS | `val_vazaovertida` − (`val_vazaovertidaturbinavel` + `val_vazaovertidanaoturbinavel`) < −ε | maior déficit |
  | R4. Energia vertida turbinável = vazão × produtividade | Consistência interna ONS | a diferença, em valor absoluto, entre `val_energiavertidaturbinavel` e `val_vazaovertidaturbinavel` × `val_produtividade` passa de ε | maior e média das diferenças absolutas, em toda a base |
  | R5. Folga de geração = disponibilidade − geração | Consistência interna ONS | a diferença, em valor absoluto, entre `val_folgadegeracao` e o maior entre 0 e `val_disponibilidade` − `val_geracao` passa de ε | maior e média das diferenças absolutas, em toda a base |
  | R6. Valor acima do limite físico da usina | Plausibilidade física | `val_geracao`, `val_disponibilidade`, `val_folgadegeracao` ou `val_energiavertidaturbinavel` acima do limite de potência; ou `val_vazaoturbinada` ou `val_vazaovertidaturbinavel` acima do limite de vazão | maior excesso sobre o limite |
  | R7. Geração acima da disponibilidade declarada | Plausibilidade física | `val_geracao` > `val_disponibilidade` + 1,0 MW | maior excesso da geração sobre a disponibilidade |
  | R8. Produtividade fora da faixa física | Plausibilidade física | `val_vazaoturbinada` > 0 e `val_produtividade` fora da faixa de produtividade | maior distância à produtividade nominal |
  | R9. Geração com vazão turbinada nula | Plausibilidade física | `val_vazaoturbinada` ≤ 0 e `val_geracao` > 1,0 MW | maior geração nesses registros |

  Em R1 a R3 e R6 a R9, o desvio é só o máximo, apurado nos registros que violam a regra (sem violação, vale 0); o desvio médio existe só em R4 e R5.
- **FR-010**: Os limites de R6 e R8 DEVEM ser calculados do perfil, nunca digitados:
  - limite de potência = `parametros.potencia_instalada_mw` × 1,05;
  - limite de vazão = `parametros.unidades_geradoras` × `parametros.engolimento_nominal_ug_m3s` × 1,05;
  - produtividade nominal, em MW/(m³/s) = 1000 × 9,81 × (`parametros.queda_bruta_m` − `parametros.perda_hidraulica_m`) × `parametros.rendimento_turbina_gerador` ÷ 1.000.000;
  - faixa de produtividade = de 0,70 a 1,30 vez a produtividade nominal.

  A tolerância ε, a folga de 5 %, a faixa de 70 % a 130 % e o 1,0 MW de R7 e de R9 são regras gerais, iguais para qualquer usina. Vazão vertida, vazão vertida não turbinável e energia vertida não têm limite superior, porque dependem da cheia: passam só por R1 a R3.
- **FR-011**: Valor ausente NÃO DEVE contar como violação de nenhuma regra. O total de valores ausentes nas grandezas DEVE ir para o log.
- **FR-012**: Se algum registro violar R1, a etapa DEVE parar com código 1, antes da sinalização, do relatório de validação e de qualquer gravação, e o log DEVE dizer a regra e a quantidade de registros. Violações de R2 a R9 DEVEM ir para o relatório de validação e para o log, sem mudar o código de saída.
- **FR-013**: Todo registro que viola R6 a R9 DEVE continuar na base tratada, sem correção, com:
  - uma coluna verdadeiro/falso por regra: `anomalia_limite_fisico` (R6), `anomalia_geracao_acima_disponibilidade` (R7), `anomalia_produtividade` (R8) e `anomalia_geracao_sem_vazao_turbinada` (R9);
  - a coluna `qualidade_registro`: `OK`, ou os códigos violados na ordem de R6 a R9, separados por `;` (ex.: `R7;R8`).

  As colunas de sinalização e as contagens do relatório de validação DEVEM sair do mesmo critério, de modo que coincidam.
- **FR-014**: O relatório de validação DEVE ter:
  - **`validacao_fisica.csv`**: uma linha por regra, com `codigo_regra`, `grupo`, `nome_regra`, `expressao` (a condição avaliada, com os limites da usina), `total_linhas`, `conformes`, `violacoes`, `taxa_conformidade_pct` (4 casas), `desvio_maximo` e `desvio_medio` (6 casas) e `status` (`CONFORME` ou `VIOLADA`);
  - **`validacao_fisica.md`**:
    - título e cabeçalho com o nome da usina (`usina.nome`), o `identificacao.cod_usina`, a versão do dicionário, a tolerância das identidades e a faixa de R8, com a produtividade nominal;
    - a tabela das nove regras, com grupo, descrição, expressão, registros, violações, percentual de violação e situação;
    - uma frase por regra, gerada dos números;
    - a ressalva de que R1 a R5 verificam só a consistência interna das grandezas publicadas pelo ONS e não atestam que os valores medidos estejam corretos, e de que R6 a R9 comparam os registros com os parâmetros técnicos da usina;
    - o total de registros sinalizados e os 40 primeiros, em ordem cronológica, com data e hora, regras, geração, disponibilidade, vazão turbinada e produtividade.

  Todo texto DEVE sair dos resultados, sem conclusão fixa, com os números das tabelas e das frases no padrão brasileiro (milhar com ponto e decimal com vírgula).

**Bases horárias complementares: disponibilidade, hidrologia e geração (US4)**

- **FR-015**: Toda série horária DEVE ficar na hora de início, a convenção da EVT:
  - nos dados hidrológicos, publicados na hora de fim, a hora de início é o instante publicado arredondado para cima até a hora cheia, menos 1 h: 01:00 vira 00:00, 15:00 vira 14:00, e 23:59, a última hora do dia, vira 23:00 do mesmo dia; o instante publicado fica em `din_instante_publicado`;
  - a disponibilidade e a geração já vêm na hora de início e não mudam; o despacho, o fator de capacidade e as semi-horárias das restrições também (FR-037, FR-041, FR-044), e o CVU e o CMO são semanais (FR-038, FR-039).
- **FR-016**: Cada hora DEVE ter um único valor. Quando a mesma hora vier de mais de um arquivo, DEVE ficar o do arquivo publicado por último, pela data de publicação registrada pela Coleta e, em empate, pelo nome do arquivo. As repetições com valores diferentes DEVEM ser contadas em `duplicatas_conflitantes`, na linha de auditoria do arquivo cujo valor saiu, e avisadas no log; as repetições com valores iguais só são unificadas.
- **FR-017**: Só as horas do período de referência, inclusive a primeira e a última, DEVEM ficar na série.
- **FR-018**: As horas do período sem valor da usina DEVEM ser listadas em `<conjunto>_ausencias.csv`, nunca interpoladas nem preenchidas:
  - todas as horas de um mês do período sem a usina: `MES_SEM_ARQUIVO`, se nenhum arquivo cobre o mês, ou `MES_SEM_USINA`, se há arquivo do mês sem horas da usina;
  - nos demais meses, cada intervalo contínuo de horas ausentes: `HORAS`;
  - cada linha com início, fim e quantidade de horas.
- **FR-019**: Cada hora DEVE receber a coluna `qualidade`: `OK`, ou os códigos das regras violadas, separados por vírgula (ex.: `H1,H2`). O arquivo tratado guarda os valores como vieram: nada é corrigido nem apagado. Campo vazio não é erro nem zero. A sinalização diz o que as etapas seguintes deixam de usar:

  | Base | Código | Sinaliza quando | Sai do uso nas etapas seguintes |
  |---|---|---|---|
  | Disponibilidade | D1 | sincronizada > operacional + 0,01 MW | a hora inteira |
  | Disponibilidade | D2 | operacional > potência instalada publicada na mesma hora + 0,01 MW | a hora inteira |
  | Disponibilidade | D3 | potência instalada, operacional ou sincronizada negativa | a hora inteira |
  | Disponibilidade | D4 | algum valor não numérico na fonte | a hora inteira |
  | Hidrologia | H1 | alguma vazão negativa (afluente, defluente, turbinada, vertida, vertida não turbinável ou por outras estruturas) | só a vazão negativa |
  | Hidrologia | H2 | volume útil abaixo de 0 % ou acima de 100 % | só o volume útil |
  | Hidrologia | H3 | algum valor não numérico na fonte | só esse valor, que já fica vazio |
  | Hidrologia | H4 | nível de montante ou de jusante a mais de 10 m da mediana desse nível na série da usina | só o nível afastado |
  | Geração | G1 | valor não numérico na fonte | a hora inteira |

  Na hidrologia, a hora sinalizada continua valendo para os demais campos. As horas sinalizadas DEVEM ser contadas por código no resumo da etapa (FR-033).
- **FR-020**: Para a disponibilidade, a hidrologia e a geração, a etapa DEVE gravar `auditoria_<conjunto>.csv`: a auditoria de extração da Coleta, uma linha por arquivo e na mesma ordem, completada por `horas_usina` (horas distintas da usina no arquivo, já na hora de início) e `duplicatas_conflitantes` (FR-016). O despacho, o CVU, o CMO, o fator de capacidade e a restrição com detalhe seguem a mesma regra (FR-037 a FR-039, FR-041 e FR-044); no CVU e no CMO, a contagem é de semanas (`semanas_usina`).

**Indicadores por unidade geradora e taxas (US5)**

- **FR-021**: Os indicadores mensais e anuais por unidade geradora DEVEM ter uma linha por mês de referência (ou ano) e unidade, com o código do equipamento, a potência, DISPF, INDISPPF, INDISPFF, DMDFF, FDFF e TDFF, o id da usina, o agente, a modalidade e o arquivo de origem; os valores numéricos são convertidos com a vírgula decimal aceita. Quando o mesmo mês (ou ano) e unidade aparecer mais de uma vez, DEVE ficar a linha do arquivo lido por último, na ordem dos nomes dos arquivos, com aviso no log.
- **FR-022**: As horas por estado operativo DEVEM ter uma linha por mês e unidade, com HP, HS, HRD, HDP, HDF, HDCE, HEDP e HEDF. Para cada mês, unidade e estado, DEVE ficar o valor de maior número de versão. A unidade é o número no fim do nome da unidade publicado. A linha DEVE trazer também:
  - o maior número de versão usado;
  - o resíduo da identidade das horas: HP menos a soma das demais parcelas; resíduo acima de 0,1 h, em valor absoluto, DEVE ser avisado no log, sem excluir o mês-unidade;
  - a potência da unidade, tirada dos indicadores mensais do mesmo mês.
- **FR-023**: A TEIFa e a TEIP mensais DEVEM manter, para cada mês e taxa, o valor de maior número de versão, como fração de 0 a 1, com o número de versão e a data do cálculo.
- **FR-024**: As tabelas mensais DEVEM manter só os meses do mês inicial ao mês final do período de referência, e a anual, só os anos do ano inicial ao final. As tabelas ficam em ordem de mês (ou ano) e unidade.
- **FR-025**: A planilha `indicadores.xlsx` DEVE reunir as tabelas tratadas nas abas `UG_MENSAL`, `UG_ANUAL`, `HORAS_ESTADO_UG_MENSAL`, `TEIFA_TEIP_MENSAL` e `SIGLAS_HORAS` (sigla e descrição de cada estado operativo), nesta ordem, com cabeçalho congelado. O recálculo da TEIFa e da TEIP e as divergências entre DISPF e horas ficam com a Conferência; a auditoria dos arquivos, com a Coleta.

**Programação diária (US5)**

- **FR-026**: A programação horária DEVE ser a média dos patamares de 30 minutos de cada hora, na hora de início: o patamar n pertence à hora (n − 1) ÷ 2, em divisão inteira, contada a partir de 00:00 do dia do arquivo. Cada hora DEVE trazer quantos patamares a formam (2 = hora completa). As horas fora do período de referência DEVEM sair. Com mais de um código de programação (usina ou conjunto programado por barra), os códigos DEVEM ser somados em cada patamar antes da média da hora:
  - cada código vale do primeiro ao último dia em que aparece na extração, porque um conjunto pode trocar os códigos no período;
  - o patamar só tem soma quando todos os códigos vigentes no dia têm valor nele; sem a linha ou sem o valor de algum deles, a soma fica ausente, nunca completada.
- **FR-027**: Os dias sem arquivo publicado, do primeiro dia com arquivo até o último dia do período de referência, DEVEM ser listados em `programacao_dias_ausentes.csv`, sem interpolação. Os dias com patamares incompletos ficam marcados na auditoria da Coleta.

**Gravação segura (US6)**

- **FR-028**: Antes de regravar um arquivo de dados com conteúdo diferente, a etapa DEVE copiar a versão atual para `<nome do arquivo>.bak`, na mesma pasta, no lugar da cópia anterior. Cada arquivo DEVE ter no máximo uma cópia: a da versão imediatamente anterior. Arquivo gravado pela primeira vez não ganha cópia.
- **FR-029**: Conteúdo idêntico ao atual NÃO DEVE ser regravado, e o `.bak` existente DEVE ficar como está, para que execuções repetidas não apaguem a versão anterior. CSV, Markdown e Parquet DEVEM ser comparados byte a byte. As planilhas, cujos bytes mudam a cada gravação, DEVEM ser comparadas pela assinatura dos dados gravada nelas: a propriedade `assinatura_dados`, com o SHA-256 do nome e do conteúdo de cada aba, na ordem.
- **FR-030**: Cada arquivo DEVE ser gravado primeiro num temporário da mesma pasta e conferido: existe, pode ser lido e tem os registros e as colunas pretendidos (na planilha, as abas na ordem, as dimensões de cada uma e a assinatura; no Markdown, o texto igual ao pretendido). Só então substitui o atual, e o conteúdo final DEVE ser conferido pelo SHA-256. Em qualquer falha, a versão anterior DEVE voltar (ou o arquivo novo sair), os temporários DEVEM ser apagados, o log DEVE dizer o arquivo, e a etapa DEVE terminar com código 1.
- **FR-031**: O log DEVE dizer o resultado de cada gravação: `NOVO`, `ALTERADO` (com o nome da cópia) ou `INALTERADO`.
- **FR-032**: A regra de cópia vale para todos os arquivos de dados da tabela de saídas, inclusive os das usinas sem EVT, das térmicas e das eólicas e solares, que seguem também as FR-028 a FR-031; o `etapa.json`, arquivo de controle, fica fora dela. As cópias `.bak` e os temporários da pasta do Tratamento NÃO DEVEM ser lidos como dados por nenhuma etapa.

**Resumo e reprodutibilidade (US1)**

- **FR-033**: O `etapa.json` da etapa DEVE estar no formato 2 (`versao_formato`), que a Conferência e as Análises exigem, porque a base horária comum entrou nele. Ao terminar com código 0, a etapa DEVE gravar no `resumo`, só com os conjuntos tratados para a usina:
  - o período de referência (início e fim);
  - EVT (só na hidrelétrica com EVT): registros tratados, violações de cada regra (R1 a R9), registros sinalizados e valores ausentes nas grandezas;
  - indicadores: linhas mensais e anuais por unidade, meses-unidade de horas por estado, meses de TEIFa e TEIP e meses-unidade com resíduo acima de 0,1 h;
  - programação: horas e dias ausentes;
  - disponibilidade, hidrologia e geração: horas, horas ausentes, horas sinalizadas por código (uma hora com dois códigos conta nos dois) e duplicatas conflitantes;
  - base horária comum (usinas sem EVT): horas, horas ausentes da série de referência, horas por nível, horas por sinalização e quantidade de trechos;
  - térmicas: despacho (horas, horas-unidade, códigos, horas ausentes e duplicatas conflitantes), CVU (semanas, registros, códigos, semanas por sinal, revisões descartadas, duplicatas conflitantes e semanas ausentes) e CMO (semanas, semanas repetidas entre publicações, duplicatas conflitantes e semanas ausentes);
  - eólicas e solares: fator de capacidade (como as séries horárias, com o nível e as horas de cada sinalização), restrição com a razão (semi-horas, nível e semi-horas por razão), restrição com detalhe (semi-horas, horas, horas ausentes, semi-horas restritas, sem a marca, com o recurso inválido, com a estimativa ausente e restritas sem estimativa, energia cortada e duplicatas conflitantes) e, com os membros do conjunto, as horas de cada um;
  - quantos arquivos ficaram em cada resultado de gravação (`NOVO`, `ALTERADO` ou `INALTERADO`), só com os resultados que ocorreram.
- **FR-034**: Com as mesmas entradas, a etapa DEVE gerar os mesmos dados tratados. Uma nova execução sem mudança nas entradas DEVE deixar todos os arquivos `INALTERADO`.

**Usinas sem EVT: base horária comum**

- **FR-035**: Nas usinas sem EVT, a etapa DEVE gravar `base_horaria.csv`, uma linha por hora da série de referência tratada no período, em ordem cronológica, com:
  - `din_instante`;
  - `geracao_mw`, da série de referência tratada: a geração por usina, da usina ou do conjunto, ou, na eólica ou solar com série própria na restrição com detalhe (FR-059 da spec da Coleta de dados), a geração verificada da usina em hora cheia (FR-041);
  - `nivel` (`usina` ou `conjunto`), hora a hora, do complemento da série gravado pela Coleta;
  - `disponibilidade_operacional_mw` e `disponibilidade_sincronizada_mw`, quando há cobertura;
  - `geracao_programada_mw`, quando há;
  - `trecho`, o número do trecho de `trechos.csv`;
  - `sinalizacoes`: os códigos da geração (G1), da disponibilidade (D1 a D4) e a regra R7 (geração acima da disponibilidade operacional declarada + 1,0 MW, a mesma tolerância da base de EVT), esta só nas horas em que a geração é da usina; separados por vírgula, e vazio sem sinalização.

  Na série de referência da restrição com detalhe, a base é da usina: a disponibilidade e a programação entram só quando estão no nível da usina. As horas ausentes da série de referência ficam listadas nas ausências dela (`geracao_ausencias.csv` ou `restricao_ausencias.csv`), nunca preenchidas, e nenhum registro é excluído: a hora sinalizada fica na base, com os valores como vieram.

**Panorama dos agregados**

- **FR-036**: A soma mensal dos agregados do catálogo de usinas (`agregados.csv`, montado pelo catálogo da Coleta, que aplica estas regras) DEVE seguir as regras desta spec:
  - um valor por hora, o do arquivo publicado por último (FR-016);
  - as horas sem registro, contadas.

**Térmicas e nucleares: despacho, CVU e CMO**

- **FR-037**: Nas térmicas com o despacho na cobertura, a etapa DEVE gravar `despacho_unidades_horario.csv` (uma linha por hora e unidade de planejamento) e `despacho_horario.csv` (a soma das unidades de planejamento por hora), com a geração programada e a verificada de cada motivo de despacho, na hora de início do intervalo (decisão técnica D16):
  - cada código de planejamento entra só no período dele no perfil (`[[identificacao.planejamento]]`), dentro do período de referência;
  - cada hora e unidade tem um único valor, o do arquivo publicado por último, com as duplicatas conflitantes contadas em `auditoria_despacho.csv` (FR-016, FR-020);
  - na soma, a coluna sem valor em todas as unidades da hora fica vazia;
  - as horas ausentes de cada código, no período dele, ficam em `despacho_ausencias.csv`, com o código (FR-018), nunca preenchidas.

  A convenção de hora é conferida pela comparação da geração verificada do despacho com a geração por usina (G4, FR-021 da spec da Conferência): se a coincidência melhorar com uma hora de deslocamento, a convenção declarada está errada e vira correção, nunca ajuste automático.
- **FR-038**: Nas térmicas com o CVU na cobertura, `cvu_semanal.csv` DEVE ter um valor por unidade de planejamento e semana operativa, o da revisão mais recente (entre arquivos com a mesma revisão, o publicado por último), com a quantidade de revisões publicadas e `sinal_cvu`:
  - `ausente`, `zero` ou `negativo`, sem descarte: a semana sinalizada fica no arquivo e sai só da comparação do CVU com o CMO nas Análises;
  - o zero entra por decisão do usuário de 20/10/2026: o ONS publica 0,00 nas semanas sem CVU da unidade (na UTE William Arjona, todas as semanas da unidade a óleo desde 2022).

  Ficam as semanas que se sobrepõem ao período de referência. As semanas ausentes de cada código, no período dele, vão para `cvu_ausencias.csv`; a auditoria por arquivo, com as duplicatas conflitantes, para `auditoria_cvu.csv`.
- **FR-039**: Nas térmicas com o subsistema no perfil, `cmo_semanal.csv` DEVE ter um valor por semana operativa (sábado a sexta) do subsistema, o da publicação mais recente. A data publicada fica em `din_instante_publicado`, ao lado da semana operativa que a contém. As semanas repetidas entre publicações são contadas no resumo, e as conflitantes, em `auditoria_cmo.csv`; as semanas ausentes vão para `cmo_ausencias.csv`. O CMO é contexto do subsistema (nível agregado), nunca dado da usina.
- **FR-040**: O CVU e o CMO DEVEM ser levados à hora pelo intervalo da semana operativa (de sábado 00h a sexta 23h), só para os cruzamentos das Análises com o despacho e a disponibilidade. Nenhum arquivo horário deles é gravado.

**Eólicas e solares: restrição, energia cortada e fator de capacidade**

- **FR-041**: Nas eólicas e solares com a restrição com detalhe na cobertura, a etapa DEVE gravar `restricao_semi_horaria.csv` na resolução publicada (30 minutos, no instante de início), uma linha por semi-hora, a do arquivo publicado por último, com as duplicatas conflitantes contadas em `auditoria_restricao_detalhe.csv` (FR-016, FR-020). A geração verificada, a estimada e o recurso (vento ou irradiância) DEVEM ser levados à hora cheia, em `restricao_horaria.csv`, pela média das duas meias-horas, só para os cruzamentos com as séries horárias:
  - a hora com uma só meia-hora com a geração verificada fica fora da hora cheia e é contada em `restricao_ausencias.csv` (FR-018);
  - a hora cheia traz também as semi-horas com o recurso inválido, com a estimativa ausente e restritas, e a energia cortada somada.
  - **Sinalização sem descarte**: o vento ou a irradiância marcados como inválidos pelo ONS (`flg_dadoventoinvalido` ou `flg_dadoirradianciainvalido` = 1) viram `sinal_recurso_invalido`; a semi-hora fica na base e sai só do recurso × geração das Análises, onde é contada.
  - **Membros do conjunto**: com os membros declarados no perfil, a geração verificada das outras usinas do conjunto vai à hora cheia, por id ONS, em `restricao_membros_horaria.csv`, só para a conferência da soma do conjunto (G2, spec da Conferência).
- **FR-042**: A energia cortada da usina (decisão técnica D17) é a soma de máx(estimada − verificada, 0) × 0,5 h nas semi-horas com a marca de restrição (`flg_geracaorestrita = 1`), em `energia_cortada_mwh`. A diferença fora das semi-horas restritas é erro da estimativa e não entra (vale 0). As semi-horas sem a coluna da marca (fotovoltaica de 05 a 12/2024) ficam com `sem_marca_restricao` e a energia cortada vazia, contadas e fora do total.
  - **Estimativa ausente** (decisão do usuário de 21/10/2026): geração estimada 0 com geração verificada acima de 1 MW (o limiar da usina parada, `LIMIAR_GERACAO_PARADA_MW`) é estimativa que o ONS não calculou (a UFV Seriemas 1 tem 341 das 609 semi-horas com irradiância acima de 200 W/m² assim, nos primeiros meses de operação). A semi-hora fica com `sinal_estimada_ausente`, contada, e a estimada dela fica fora dos totais e das médias; na semi-hora restrita, a energia cortada não é calculada (fica vazia), e a semi-hora é contada como restrita sem estimativa.
- **FR-043**: Com a restrição com a razão na cobertura, a etapa DEVE gravar `restricao_razao_semi_horaria.csv`: uma linha por semi-hora, a do arquivo publicado por último, com o nível (usina ou conjunto), as grandezas publicadas, os minutos de cada razão e a razão (REL, CNF ou ENE; vazia, sem razão). Cada semi-hora da restrição com detalhe recebe, da semi-hora correspondente da restrição com a razão, o código da razão, os minutos de cada razão e o nível dela (`nivel_razao`). Quando a razão é do conjunto, a energia cortada continua sendo a da usina.
- **FR-044**: Com o fator de capacidade na cobertura, a etapa DEVE gravar `fator_capacidade_horario.csv` pelo motor das séries horárias (FR-015 a FR-018 e FR-020, com `fator_capacidade_ausencias.csv` e `auditoria_fator_capacidade.csv`), com o nível (usina ou conjunto) e as sinalizações, sem descarte:
  - `sinal_fc_fora_0_1`: fator de capacidade fora de 0 a 1;
  - `sinal_acima_capacidade`: geração verificada acima da capacidade instalada publicada na mesma hora, com a folga de 1,0 MW da R7.

  A hora sinalizada continua no fator de capacidade publicado, e as horas sinalizadas são contadas.
- **FR-045**: As taxas operativas (Taxas TEIFa Oper e TEIP Oper) DEVEM ser tratadas pela regra das taxas oficiais: a versão de maior número de cada mês e taxa, como fração entre 0 e 1. Elas DEVEM ser juntadas à tabela mensal das oficiais pelos meses das oficiais, nas colunas `teifa_oper`, `teip_oper`, `num_versao_oper` e `din_calculo_oper`; o mês das oficiais sem a operativa fica com as colunas vazias. Sem linhas das operativas, a tabela não ganha as colunas.

### Key Entities

- **Período de referência**: início e fim da base de EVT da usina ou, nas usinas sem EVT, da série de referência gravada pela Coleta; recorta todas as outras bases.
- **Registro tratado da EVT**: medição horária com as colunas extraídas, os tipos garantidos, os ausentes preservados e as cinco colunas de sinalização.
- **Regra de validação**: código (R1 a R9), nome, grupo (consistência interna ONS ou plausibilidade física), condição, limite ou tolerância.
- **Resultado de regra**: registros avaliados, conformes, violações, taxa de conformidade, desvios máximo e médio e situação (`CONFORME` ou `VIOLADA`).
- **Relatório de validação**: CSV e Markdown com o resultado das regras, a leitura de cada uma, a ressalva sobre R1 a R5 e os primeiros registros sinalizados.
- **Série horária tratada**: disponibilidade, hidrologia ou geração; uma linha por hora de início, com os valores, a sinalização de qualidade e o arquivo de origem.
- **Sinalização de qualidade**: código (D1 a D4, H1 a H4, G1), condição e o que sai do uso nas etapas seguintes.
- **Ausência**: tipo (`MES_SEM_ARQUIVO`, `MES_SEM_USINA` ou `HORAS`), início, fim e horas.
- **Auditoria completa por arquivo**: a auditoria de extração da Coleta, mais as horas da usina e as duplicatas conflitantes.
- **Indicadores tratados**: indicadores por unidade (mensais e anuais), horas por estado operativo com o resíduo da identidade e a potência, TEIFa e TEIP mensais.
- **Programação horária**: hora de início, geração programada média e número de patamares; e a lista de dias sem arquivo.
- **Cópia `.bak`**: versão imediatamente anterior de um arquivo de dados tratado; no máximo uma por arquivo.
- **Resumo da etapa**: números principais do Tratamento, gravados no `etapa.json`.
- **Nível do dado**: `usina` ou `conjunto`, o nível em que o ONS publica a série; o CMO é contexto do subsistema (agregado).
- **Base horária comum**: nas usinas sem EVT, uma linha por hora da série de referência, com a geração e o nível, a disponibilidade, a programação, o trecho e as sinalizações.
- **Despacho tratado**: geração programada e verificada por motivo de despacho, por hora e unidade de planejamento e somada por hora, com as ausências por código.
- **CVU e CMO semanais**: um valor por semana operativa (sábado a sexta), por unidade de planejamento ou do subsistema, com o sinal do CVU e as semanas ausentes.
- **Restrição por semi-hora**: geração verificada e estimada, recurso, marcas de restrição e de recurso inválido, sinalizações, energia cortada e razão da restrição, na resolução publicada e em hora cheia.
- **Energia cortada**: máx(estimada − verificada, 0) × 0,5 h nas semi-horas restritas, sempre da usina.
- **Fator de capacidade horário**: geração programada e verificada, capacidade instalada e fator publicados, com o nível e as sinalizações.

---

## Aplicabilidade por tipo

"Hidrelétrica com EVT" é a UHE, PCH ou CGH com série própria na Energia Vertida Turbinável. "Com a cobertura" quer dizer: quando a tabela `[cobertura]` do perfil declara o conjunto no nível da usina ou do conjunto (na UHE sem `[cobertura]`, os dez conjuntos do fluxo da hidrelétrica, com o cadastro). "—" = não se aplica.

| Tratamento | Hidrelétrica com EVT | Hidrelétrica sem EVT (UHE, PCH, CGH) | Térmica (UTE, UTN) | Eólica e solar (EOL, UFV) |
|---|---|---|---|---|
| Período de referência (FR-004) | base de EVT | série de referência da Coleta | série de referência da Coleta | série de referência da Coleta |
| Base de EVT, regras R1 a R9 e relatório de validação (FR-005 a FR-014) | sempre | — | — | — |
| Indicadores por unidade geradora e taxas (FR-021 a FR-025) | sempre | com a cobertura | com a cobertura | — |
| Programação diária, com a soma dos códigos (FR-026, FR-027) | sempre | com a cobertura | com a cobertura | com a cobertura |
| Disponibilidade (FR-015 a FR-020) | sempre | com a cobertura | com a cobertura | — |
| Dados hidrológicos (FR-015 a FR-020) | sempre | com a cobertura | — | — |
| Geração por usina, da usina ou do conjunto (FR-015 a FR-020) | sempre (da usina) | com a cobertura | com a cobertura | com a cobertura |
| Base horária comum (FR-035) | — | sempre | sempre | sempre |
| Despacho por hora e por unidade (FR-037) | — | — | com a cobertura | — |
| CVU com o sinal (FR-038) e CMO do subsistema (FR-039), levados à hora (FR-040) | — | — | CVU com a cobertura; CMO com o subsistema no perfil | — |
| Restrição com detalhe em semi-hora e hora cheia, energia cortada e recurso inválido (FR-041, FR-042) | — | — | — | com a cobertura |
| Razão da restrição (FR-043) | — | — | — | com a cobertura, da usina ou do conjunto |
| Fator de capacidade com as sinalizações (FR-044) | — | — | — | com a cobertura, da usina ou do conjunto |
| Membros do conjunto em hora cheia (FR-041) | — | — | — | em conjunto, com os membros no perfil |
| Gravação segura, resumo e reprodutibilidade (FR-028 a FR-034) | sempre | sempre | sempre | sempre |

A usina em conjunto sem série própria (PCH, CGH, EOL ou UFV) tem a série de referência no nível do conjunto: a base horária traz o nível `conjunto`, e a R7 não é avaliada nessas horas.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Não regressão. Com o perfil da São Domingos e os dados brutos locais do relatório aprovado, a etapa termina com 0, o `resumo` do `etapa.json` e os arquivos tratados trazem os números de referência abaixo, e o relatório gerado a partir dos dados tratados é idêntico ao relatório de referência da não regressão, exceto a data de geração (comando `comparar`).

  Números de referência:
  - EVT: 70.895 registros, de 28/08/2018 00h a 28/09/2026 23h; R1 a R5 sem violação; R6 com 1, R7 com 293, R8 com 185 e R9 com 63; 526 registros sinalizados;
  - disponibilidade e geração: 70.895 horas cada, com 1 hora ausente;
  - hidrologia: 70.760 horas, 136 horas ausentes em 48 intervalos e 2.546 horas sinalizadas (H1 em 216, H2 em 2.321 e H4 em 13; 4 horas têm H1 e H2);
  - programação: 16.992 horas e 20 dias ausentes;
  - indicadores: 196 linhas mensais, 18 anuais, 160 meses-unidade de horas por estado e 61 meses de taxas.

  A conferência é feita pelo `comparar --todas` (spec da Geração do relatório), que refaz o Tratamento a partir da Coleta e do perfil congelados da referência da usina. Nas demais usinas com relatório de referência, o relatório refeito também sai idêntico ao aprovado.
- **SC-002**: 100 % das células das dez grandezas da EVT tratada são numéricas ou vazias; nenhuma é texto e nenhum valor ausente vira zero. A planilha abre no Excel com números nativos, sem problema de vírgula e ponto.
- **SC-003**: 100 % dos registros da EVT são avaliados pelas nove regras, e a base tratada tem o mesmo número de registros da extraída. Todo registro sinalizado é localizável pela coluna `qualidade_registro`, e as violações de R6 a R9 do relatório coincidem com as colunas de sinalização. O relatório separa consistência interna (R1 a R5) de plausibilidade física (R6 a R9) e traz a ressalva sobre R1 a R5.
- **SC-004**: Em cada série horária complementar, as horas da série mais as horas listadas como ausentes somam 100 % das horas do período de referência, sem hora repetida e sem valor interpolado.
- **SC-005**: 100 % dos dias da programação, do primeiro dia com arquivo até o fim do período de referência, têm arquivo na auditoria da Coleta ou estão na lista de dias ausentes.
- **SC-006**: No teste das quatro gravações (sem versão anterior, conteúdo alterado, conteúdo idêntico e falha simulada), a versão anterior à última alteração está sempre recuperável pelo `.bak`; depois da falha, o arquivo volta idêntico ao que era; nenhum arquivo tem mais de um `.bak`.
- **SC-007**: Uma segunda execução sem mudança nas entradas termina com 100 % dos arquivos `INALTERADO` e os `.bak` intactos (mesmo conteúdo e mesma data de modificação).
- **SC-008**: Com o perfil de uma usina fictícia, sobre dados de teste, os limites de R6 e R8, o cabeçalho do relatório de validação e o nome da aba da planilha da EVT saem do perfil dela, e nenhum arquivo tratado menciona a São Domingos.
- **SC-009**: Nos testes, 100 % das situações de parada (coluna obrigatória ausente, dicionário ausente, instante inválido e valor negativo na EVT; Coleta não concluída) terminam com o código previsto (1 ou 5), sem gravar nenhum arquivo de dados; violações de R2 a R9 e valores sinalizados terminam com 0.
- **SC-010**: Com os extraídos já gravados, o Tratamento da usina termina em menos de 10 minutos, sem acesso à rede.
- **SC-011**: Nos testes, sem rede, cada uma das sete usinas fictícias (uma por tipo) passa pelo Tratamento com código 0. Nas usinas sem EVT, o período é o da série de referência da Coleta, a base horária comum é gravada e nenhum arquivo da EVT existe; nas térmicas e nas eólicas e solares, os arquivos do tipo são gravados, com as sinalizações e as ausências.

---

## Decisões do usuário

| Data | Decisão | Onde se aplica |
|---|---|---|
| 30/09/2026 | Pedido que originou o tratamento: todas as grandezas da EVT como número no Excel, sem mistura de "número" e "geral", e conferência de todas as colunas quanto a valores negativos e absurdos | FR-007, FR-008, FR-009 |
| 02/10/2026 | A base de EVT local é mantida e define o período de todas as bases. A extensão da geração por usina para antes desse período (dados desde 18/06/2015) foi recusada | FR-004, FR-017, FR-024, FR-026 |
| 05/10/2026 | Antes de regravar um dado tratado, guardar a versão anterior em `.bak` e conferir fisicamente a nova gravação | FR-028, FR-029, FR-030 |
| 05/10/2026 | A cópia `.bak` serve para recuperar o estado anterior se o código falhar: vale para os dados; relatórios, manifestos, dicionários e demais arquivos de controle ficam dispensados | FR-032 |
| 05/10/2026 | Uma cópia por arquivo basta; cópias `.bak` datadas e acumuladas foram rejeitadas | FR-028 |
| 07/10/2026 | Nos dados tratados, cada arquivo mantém só a cópia da versão imediatamente anterior | FR-028 |
| 07/10/2026 | As bases do relatório estão completas: nenhuma base nova é incluída, e os dados tratados regenerados devem coincidir com os atuais | FR-003, FR-034, SC-001 |
| 07/10/2026 | Inventário aprovado: o dicionário de dados da raiz do projeto saiu, e o tratamento lê o dicionário da EVT que a Coleta mantém atualizado | FR-006 |
| 08/10/2026 | `data/processed/` excluída depois da conferência da não regressão: 20 dos seus 30 arquivos de dados são idênticos byte a byte aos dados tratados novos, e os outros 10 têm os mesmos dados, reorganizados entre as etapas. A não regressão passa a usar os números de referência e o relatório de referência | SC-001 |
| 08/10/2026 | Na planilha da EVT tratada, os caracteres que o Excel não aceita em nome de aba viram `_`, e o nome é cortado em 31 caracteres; o CSV guarda o número real de 64 bits lido da base extraída. | FR-008 |
| 09/10/2026 | Ampliação do fluxo para todos os tipos de usina (UHE, PCH, CGH, UTE, UTN, EOL e UFV). O Tratamento deixa de ler `data/raw/`: o dicionário da EVT vem da Coleta | FR-002, FR-003, FR-006 |
| 09/10/2026 | Requisitos das usinas sem EVT aprovados: período da série de referência, base horária comum, soma dos códigos de programação e regras do panorama dos agregados | FR-004, FR-026, FR-035, FR-036 |
| 19/10/2026 | Conferência do código das usinas sem EVT contra os requisitos, com os ajustes aprovados: uma linha da base horária por hora da série de referência; soma dos códigos de programação só com todos os códigos com valor no patamar; Tratamento no formato 2; regra dos agregados aplicada pelo catálogo da Coleta | FR-026, FR-033, FR-035, FR-036 |
| 19/10/2026 | Requisitos das térmicas e nucleares aprovados: despacho por hora e por unidade, CVU pela revisão mais recente com o sinal, CMO sem duplicatas e semanais levados à hora | FR-037 a FR-040 |
| 20/10/2026 | CVU zero ("Zero fica fora"): o ONS publica 0,00 nas semanas sem CVU da unidade; `sinal_cvu` = `zero`, mantido no arquivo e fora da comparação com o CMO, como o ausente e o negativo | FR-038 |
| 20/10/2026 | Requisitos das eólicas e solares aprovados: semi-horárias na resolução publicada e em hora cheia, energia cortada só nas semi-horas restritas, razão por semi-hora com o nível, fator de capacidade com as sinalizações e recurso inválido sinalizado | FR-041 a FR-044 |
| 21/10/2026 | Estimativa ausente: geração estimada 0 com a verificada acima de 1 MW é estimativa que o ONS não calculou; sinalizada, contada, fora dos totais e das médias da estimada, e sem energia cortada na semi-hora restrita | FR-042 |
| 21/10/2026 | Limite físico do recurso (vento acima de 40 m/s, irradiância acima de 1.500 W/m²): falha de medição sem a marca do ONS, tirada do recurso × geração pelas Análises; no Tratamento, o valor fica como publicado | FR-041, casos de borda |
| 23/10/2026 | As taxas operativas entram na tabela mensal das taxas, ao lado das oficiais, uma linha por mês (aprovado pelo usuário). | FR-045 |

---

## Assumptions

- **O que a Coleta entrega**:
  - a base de EVT extraída já consolidada: ordem cronológica, sem hora repetida, com o arquivo de origem e o critério de identificação de cada registro;
  - os extraídos das bases complementares com os valores lidos como número, sem arredondamento, o instante publicado, o arquivo de origem e a marca dos valores não numéricos, contados na auditoria de extração;
  - para cada arquivo lido, o período que ele cobre e a data de publicação, registrados junto dos extraídos: servem para escolher o valor de uma hora repetida (FR-016) e para separar mês sem arquivo de mês sem a usina (FR-018);
  - na programação, uma linha de auditoria por arquivo diário, com o dia; com mais de um código, cada linha extraída traz o código (`cod_exibicaousina`);
  - o dicionário de dados da EVT, copiado para a pasta da Coleta da usina;
  - nas usinas sem EVT, o período da série de referência, o nível de cada hora e os trechos;
  - nos conjuntos novos, as linhas como publicadas, sem levar à hora nem escolher a revisão: as semi-horárias em 30 minutos, o CVU com todas as revisões e o CMO com todas as publicações.
- **Período**: a base de EVT tem registros da usina e define o período de referência na hidrelétrica com EVT; nos demais tipos, a série de referência da Coleta tem pelo menos uma hora com valor.
- **Dicionário**: o da EVT traz só código, descrição e unidade de cada coluna, sem faixas de valores; por isso os limites físicos vêm do perfil.
- **Perfil**: os parâmetros usados nos limites já foram validados ao carregar o perfil (regras comuns, na spec da Coleta).
- **Critérios de triagem**: a folga de 5 %, a faixa de 70 % a 130 %, o 1,0 MW de R7 e de R9 (também na base horária comum, na geração acima da capacidade instalada e na estimativa ausente), os 0,01 MW de D1 e D2 e os 10 m de H4 são critérios de triagem, não valores normativos. Um registro sinalizado é indício a verificar, não erro confirmado. A tolerância de 0,0001 nas identidades cobre a precisão com que o ONS publica as grandezas.
- **Dados hidrológicos**: são informados pelos agentes e não são consistidos pelo ONS. A etapa sinaliza e nunca corrige.
- **CSV no Excel**: o CSV usa ponto decimal e pode ser mal lido num Excel em português; para o Excel, vale a planilha.
- **Horário**: os instantes ficam no horário publicado pelo ONS, sem conversão de fuso.
- **Escopo**: na hidrelétrica com EVT, nenhuma base nova é incluída, e os arquivos e as colunas da hidrelétrica não mudam; os conjuntos novos entram só nos tipos que os usam, em arquivos novos; os cadastrais não têm tratamento.
