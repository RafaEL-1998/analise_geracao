# Data Model: Relatórios de Desempenho para Todos os Tipos de Usina

**Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md) · **Data**: 2026-10-09

Este documento traz só o que é novo ou muda. O que continua igual está nos data-models das etapas: [Coleta](../001-coleta-dados/data-model.md), [Tratamento](../002-tratamento-dados/data-model.md), [Conferência](../003-conferencia/data-model.md), [Análises](../004-analises/data-model.md) e [Geração do relatório](../005-geracao-relatorio/data-model.md).

Convenções de hoje que continuam valendo:
- CSV com `;`, em UTF-8 sem BOM;
- datas `AAAA-MM-DD HH:MM:SS`;
- dados da usina gravados por `src/comum/persistencia.py`, com `.bak` só na Coleta e no Tratamento;
- `etapa.json` por etapa.

**Regra para a UHE**: os arquivos e as colunas que o relatório da UHE usa não mudam. Informação nova vai para arquivos novos (R8, R29).

## 1. Enumerações

| Nome | Valores | Origem |
|---|---|---|
| Tipo | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL`, `UFV`; no catálogo também `conjunto` (linha de conjunto do cadastro) e `outro` | prefixo do CEG (R1) |
| Modalidade | `TIPO I`, `TIPO II-A`, `TIPO II-B`, `TIPO II-C`, `TIPO III`, `TIPO III (EM DIT)` | cadastro do ONS, em maiúsculas; Tipo III não recebe perfil |
| Nível do dado | `usina`, `conjunto`, `agregado` | princípio VIII; o CMO do subsistema é `agregado` |
| Cobertura | `proprio`, `conjunto`, `agregado`, `ausente` | R3 |
| Situação do perfil | `rascunho`, `conferido` | R5 |
| Resolução | `horaria`, `semi_horaria` (inclusive os 48 patamares da programação), `semanal`, `mensal_anual`, `estatica` | R8 |
| Razão da restrição | `REL`, `CNF`, `ENE`, mais `sem razão` | restrição sem detalhe (A8) |

## 2. Catálogo de usinas (`data/catalogo/`)

Gravado pela Coleta (`python -m src usinas`), sem `.bak`, por inteiro a cada montagem (RT3). Nenhuma etapa da usina escreve aqui.

### 2.1 `catalogo.json`

| Campo | Tipo | Conteúdo |
|---|---|---|
| `versao_formato` | int | 1; muda quando os arquivos do catálogo mudam de formato |
| `montado_em_utc` | texto | data e hora da montagem |
| `sem_portal` | bool | montado só com os arquivos locais |
| `cadastro` | objeto | arquivo e data de publicação de Modalidade das usinas, Composição dos conjuntos e Capacidade de geração |
| `cobertura` | lista | por conjunto do ONS: pacote, arquivo verificado e data de publicação (FR-004) |
| `agregados` | objeto | arquivos de geração e meses usados no panorama |
| `contagens` | objeto | linhas por tipo e por estado (SC-002) |

### 2.2 `usinas.csv`

Uma linha por linha do cadastro do ONS. São 6.017 em 09/10/2026, sem filtro (SC-002).

| Coluna | Conteúdo |
|---|---|
| `ceg` | como publicado; vazio nas linhas de conjunto |
| `id_ons` | como publicado; pode vir vazio (A1) |
| `nom_usina` | como publicado; só exibição, nunca identificação |
| `tipo` | R1 |
| `modalidade` | do cadastro |
| `id_estado`, `sgl_centrooperacao`, `nom_pontoconexao`, `sts_aneel` | do cadastro |
| `subsistema` | da Capacidade de geração ou da Composição dos conjuntos |
| `potencia_autorizada_mw` | número; vírgula decimal aceita (P2) |
| `id_conjunto`, `nom_conjunto` | conjunto vigente, da Composição dos conjuntos; vazio fora de conjunto |
| `unidades_geradoras`, `potencia_efetiva_mw`, `combustivel`, `entrada_operacao` | da Capacidade de geração, só unidades ativas |
| `cobertura_resumo` | o melhor nível entre os conjuntos de série do tipo |
| `divergencias` | por exemplo, o tipo do ONS diferente do tipo do CEG (R1), ou a potência autorizada diferente da soma das unidades |

O perfil de cada usina é achado pelo CEG em `usinas/*/perfil.toml` na hora de cada comando, não guardado no catálogo.

### 2.3 `conjuntos.csv` — composição com datas

| Coluna | Conteúdo |
|---|---|
| `id_conjunto`, `nom_conjunto` | do ONS |
| `ceg`, `id_ons_usina`, `nom_usina` | usina membro |
| `tipo` | pelo CEG da usina membro (R1) |
| `tipo_ons` | `id_tipousina` publicado, só para conferência |
| `inicio`, `fim` | datas da relação; vazio ou data sentinela = vigente |
| `estado`, `subsistema` | do ONS |

### 2.4 `cobertura.csv`

Uma linha por usina (ou conjunto) e conjunto do ONS de série já implementado.

| Coluna | Conteúdo |
|---|---|
| `ceg` ou `id_conjunto` | usina ou conjunto |
| `conjunto_ons` | chave do registro (seção 4) |
| `nivel` | `proprio`, `conjunto`, `agregado` ou `ausente` |
| `identificador` | coluna e valor usados (R9) |
| `linhas`, `linhas_sem_valor` | contagens no arquivo verificado |
| `arquivo`, `publicacao` | arquivo e data de publicação usados na verificação (FR-004) |

### 2.5 `planejamento.csv` e `programacao.csv` — códigos para o rascunho

| Arquivo | Colunas |
|---|---|
| `planejamento.csv` | `ceg`, `codigo` (número), `primeiro_mes`, `ultimo_mes`, `nomes_publicados` (só exibição), `arquivos` |
| `programacao.csv` | `codigo_exibicao`, `id_usina_ou_conjunto`, `modalidade`, `estado`, `arquivo` |

Ligação entre código de programação e usina, sem usar o nome (R5):
- o código igual ao id ONS da usina;
- ou, no conjunto, os códigos que começam pelo id do conjunto sem o prefixo `CJU_` (A10);
- nos demais casos, o rascunho deixa o campo pendente e lista os códigos do estado para o fiscal escolher. A São Domingos, por exemplo, tem o código `PRUHSD` para o id `MSUHSD`.

### 2.6 `agregados.csv` — panorama da carteira

Os agregados de cada estado, por mês, dos últimos 12 meses completos (R21).

| Coluna | Conteúdo |
|---|---|
| `id_estado`, `mes` | estado e mês |
| `modalidade` | `Pequenas Usinas (MMGD)`, `Pequenas Usinas (Tipo III)` ou `TIPO III` |
| `tipo_ons` | `nom_tipousina` publicado |
| `grupo` | `nom_usina` publicado (só exibição) |
| `energia_mwh`, `horas`, `horas_ausentes` | soma, horas com valor e horas sem registro, com as duplicatas tratadas como no Tratamento (R11) |
| `previsao` | verdadeiro nas usinas Tipo III, cujo valor é previsão do ONS (A3) |
| `arquivo` | arquivo de geração de origem |

## 3. Perfil da usina (`usinas/<slug>/perfil.toml`)

O formato é o de hoje ([contrato atual](../001-coleta-dados/contracts/perfil-usina.md)), com as tabelas e campos abaixo. O contrato completo, com exemplos, está em [contracts/perfil-multitipo.md](contracts/perfil-multitipo.md).

### 3.1 Campos comuns

| Campo | Tipo | Regra |
|---|---|---|
| `usina.slug`, `nome`, `nome_curto`, `estado` | texto | como hoje; o slug não pode ser `carteiras` |
| `usina.tipo` | enumeração | obrigatório; igual ao prefixo do CEG |
| `usina.modalidade` | enumeração | obrigatória; `TIPO III` e `TIPO III (EM DIT)` são recusadas |
| `usina.situacao` | enumeração | `rascunho` é recusado (código 4); ausente = `conferido` |
| `usina.pendentes` | lista de texto | campos ainda a preencher; precisa estar vazia ou ausente quando `conferido` |
| `usina.inicio_operacao_comercial` | inteiro | como hoje |
| `usina.subsistema` | `SE`, `S`, `NE` ou `N` | obrigatório em UTE e UTN com `cvu` na cobertura (fase B), para o CMO; o rascunho o traz do catálogo |
| `identificacao.ceg` | texto | obrigatório; padrão `^(UHE\|PCH\|CGH\|UTE\|UTN\|EOL\|UFV)\.[A-Z]{2}\.[A-Z]{2}\.\d{6}-\d\.\d{2}$` |
| `[cobertura]` | tabela | nível de cada conjunto do ONS de série (seção 3.3); obrigatória fora da UHE |
| `parametros.potencia_instalada_mw`, `unidades_geradoras` | número | como hoje; em EOL e UFV, a potência instalada é a capacidade instalada |
| `parametros.potencia_unitaria_mw` ou `potencias_unidades_mw` | número ou lista | um dos dois: a potência única das unidades ou a lista, uma por unidade, quando diferem. A soma tem de dar a potência instalada, com a tolerância de hoje (0,1 MW). A UHE continua com `potencia_unitaria_mw` |
| `parametros.garantia_fisica_mwmed` | número | obrigatória na UHE; opcional nos demais |
| `parametros.fontes.geral` | texto | obrigatória; `garantia_fisica` obrigatória quando há garantia física |

### 3.2 Campos por tipo

`O` = obrigatório; `C` = obrigatório quando um conjunto do ONS que usa o campo tem cobertura `proprio` ou `conjunto`; `—` = não se aplica (presença é recusada).

| Campo | UHE | PCH e CGH | UTE e UTN | EOL e UFV |
|---|---|---|---|---|
| `identificacao.id_ons` | O | C | O | C |
| `identificacao.cod_usina`, `nome_ons` | O | C (EVT ou hidrologia) | — | — |
| `identificacao.id_reservatorio` | O | C (hidrologia) | — | — |
| `identificacao.cod_programacao` ou `codigos_programacao` | O | O | O | O |
| `identificacao.id_conjunto` | — | C | C | C |
| `[[identificacao.planejamento]]` (`codigo`, `inicio`, `fim`) | — | — | C (despacho ou CVU), pelo menos um | — |
| `[[identificacao.membros]]` (`id_ons`, `ceg`, `inicio`, `fim`) | — | opcional | — | opcional |
| `parametros.tipo_turbina`, `engolimento_nominal_ug_m3s`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` | O | C (EVT ou hidrologia) | — | — |
| `parametros.ip_referencia`, `teif_referencia` | O | opcional | opcional | — |
| `parametros.combustivel` | — | — | O | — |
| `[analises]` (`vertimento_minimo_m3s`, `faixas_geracao_mw`) | O | C (EVT) | — | — |
| `[textos]` | opcional | opcional | opcional | opcional |

Na UHE, os campos e as regras de hoje continuam iguais. O perfil da São Domingos ganha só `usina.tipo = "UHE"` e `usina.modalidade = "TIPO II-A"` (FR-011).

### 3.3 Tabela `[cobertura]`

Uma chave por conjunto de série do registro (seção 4), com o nível declarado pelo fiscal a partir do rascunho:

```toml
[cobertura]
geracao = "conjunto"          # a série do conjunto: o identificador é o id_conjunto
programacao = "conjunto"
restricao_detalhe = "proprio"
fator_capacidade = "conjunto"
```

- **O que a Coleta obtém** (FR-015):
  - os conjuntos com `proprio` ou `conjunto`. O nível escolhe o identificador: o da usina com `proprio`, o do conjunto com `conjunto`;
  - com uma lista (`["proprio", "conjunto"]`), as duas séries. Os trechos dizem qual vale em cada hora (R7). No conjunto da série de referência, o período é a união das duas (R6);
  - sempre, os cadastrais (Modalidade, Composição e Capacidade) e, em UTE e UTN, o CMO, que é contexto do subsistema. Exceção: a UHE sem `[cobertura]`.
- **Chave `indicadores`**: cobre os quatro conjuntos de indicadores e taxas. Um deles sem linhas da usina vira conferência não aplicável, com o motivo (A12).
- **Conjunto `ausente` ou `agregado`**: vira conferência e seção não aplicáveis, com o motivo "sem cobertura no ONS, conforme o perfil" (FR-019, FR-024).
- **Chave desconhecida, ou de conjunto que não serve ao tipo**: recusada. O registro só traz os conjuntos já implementados. Um perfil de uma fase anterior ganha as chaves novas quando o fiscal confere as diferenças mostradas pelo `perfil` (código 6).
- **Sem a tabela**: só na UHE, com os dez conjuntos de hoje e mais nenhum.

### 3.4 Situação e transições

```text
(sem perfil) --perfil --ceg--> rascunho --fiscal confere e completa--> conferido
conferido --perfil --ceg (de novo)--> conferido, sem mudança: código 0 sem diferença; 6 com diferença (só mostra)
```

- Em `rascunho`, toda etapa recusa o perfil (código 4). A mensagem lista `pendentes` e os demais problemas, todos de uma vez, como hoje.
- Para passar a `conferido`, o fiscal troca `situacao`, preenche os pendentes com a fonte e esvazia `pendentes`.

### 3.5 Valores derivados

| Valor | Tipos | Regra |
|---|---|---|
| `engolimento_maximo_m3s`, `produtividade_nominal_mw_m3s`, `limite_vazao_turbinavel_m3s` | hidrelétricas com EVT ou hidrologia | como hoje; nos demais, erro ao pedir |
| `disponibilidade_referencia` | quando há IP e TEIF de referência | como hoje |
| `plena_carga_mw`, `limite_potencia_mw` | todos | sobre a potência instalada |
| `potencias_das_unidades_mw` | todos | a lista do perfil, ou a potência única repetida pelas unidades |
| `codigos_planejamento_em(data)` | UTE, UTN | códigos vigentes numa data |

## 4. Registro dos conjuntos do ONS (`src/coleta/registro.py`)

Cada entrada é uma `DescricaoConjunto`. Ela traz o que a de hoje já tem (pacote, pasta, identificador, conferências, colunas de valor, convenção de hora, formatos e filtro do Parquet) e ganha:
- `chave`;
- `tipos`;
- `nivel`;
- `resolucao` (seção 1);
- `referencia` (pode ser série de referência);
- `variantes` (a eólica e a fotovoltaica, quando o pacote muda com o tipo).

| Chave | Pacote do ONS | Tipos | Nível | Resolução | Identificador | Conferência | Ref. | Fase |
|---|---|---|---|---|---|---|---|---|
| `evt` | `energia-vertida-turbinavel` | UHE, PCH, CGH | usina | horária | `cod_usina` | nome | sim | hoje |
| `indicadores` | os quatro de hoje | UHE, PCH, CGH, UTE, UTN | usina | mensal e anual | CEG | id ONS | não | hoje |
| `programacao` | `programacao_diaria` | todos | usina ou conjunto | semi-horária (48 patamares) | `cod_exibicaousina` entre os códigos do perfil | estado; na UHE, também o nome, como hoje | não | hoje |
| `disponibilidade` | `disponibilidade_usina` | UHE, PCH, CGH, UTE, UTN | usina | horária | id ONS | CEG, estado | não | hoje |
| `hidrologia` | `dados_hidrologicos_ho` | UHE, PCH, CGH | usina | horária | `cod_usina` | reservatório | não | hoje |
| `geracao` | `geracao-usina-2` | todos | usina ou conjunto | horária | id ONS da usina, ou id do conjunto | CEG e estado (usina) ou estado (conjunto) | sim | hoje; conjunto na A |
| `cadastro` | `modalidade-usina` | todos | usina | estática | CEG | id ONS, estado | não | hoje |
| `composicao` | `usina_conjunto` | em conjunto | conjunto | estática | id do conjunto | CEG da usina | não | A |
| `capacidade` | `capacidade-geracao` | todos | usina | estática | CEG | estado | não | A |
| `despacho` | `geracao-termica-despacho-2` | UTE, UTN | usina | horária | CEG | código de planejamento do perfil | não | B |
| `cvu` | `cvu-usitermica` | UTE, UTN | usina | semanal | código de planejamento do perfil | subsistema | não | B |
| `cmo` | `cmo-semanal` | UTE, UTN | agregado | semanal | subsistema | — | não | B |
| `fator_capacidade` | `fator-capacidade-2` | EOL, UFV | usina ou conjunto | horária | id ONS ou id do conjunto | CEG ou estado | não | C |
| `restricao_detalhe` | `restricao_coff_eolica_detail`, `restricao_coff_fotovoltaica_detail` | EOL, UFV | usina | semi-horária | id ONS | CEG | sim | C |
| `restricao_razao` | `restricao_coff_eolica_usi`, `restricao_coff_fotovoltaica` | EOL, UFV | usina ou conjunto | semi-horária | id ONS ou id do conjunto | CEG ou estado | não | C |

- As colunas de valor de cada conjunto novo estão na seção 6.1.
- O registro dos dicionários e as abas DICIONARIOS e FONTES de cada usina listam só os conjuntos do tipo e da cobertura dela. Na UHE sem `[cobertura]`, são os dez de hoje, na mesma ordem (R8).
- Arquivo novo numa etapa não muda o `VERSAO_FORMATO` dela; só a mudança num arquivo existente muda.

## 5. Série de referência e trechos

### 5.1 Série de referência (no resumo do `etapa.json` da Coleta)

| Campo | Conteúdo |
|---|---|
| `conjunto` | chave do registro (R6) |
| `identificador` | coluna e valor |
| `inicio`, `fim` | primeira e última hora com valor |
| `arquivos_varridos` | todos os publicados do conjunto |
| `motivo` | linha da tabela da R6 que se aplicou |

### 5.2 `trechos.csv` (Coleta, nas usinas sem EVT)

Um trecho é um intervalo sem mudança de modalidade, de composição do conjunto nem de códigos de planejamento (R7).

| Coluna | Conteúdo |
|---|---|
| `inicio`, `fim` | limites do trecho, dentro do período |
| `modalidade` | da coluna de modalidade da geração, hora a hora |
| `id_conjunto`, `composicao` | conjunto e CEG das usinas do conjunto no trecho |
| `tipos_composicao` | tipos das usinas do conjunto no trecho, por exemplo `PCH;UTE` |
| `codigos_planejamento` | códigos vigentes (UTE e UTN) |
| `nivel_geracao` | `usina` ou `conjunto` |
| `mostrar` | verdadeiro quando o trecho muda o nível ou a composição (só esses aparecem no relatório) |

## 6. Resultados das etapas: o que muda

O `VERSAO_FORMATO` de uma etapa sobe quando muda um arquivo que ela já grava, ou quando a etapa seguinte passa a exigir um arquivo novo; arquivo novo opcional não muda o formato (R8). A etapa seguinte recusa o formato antigo (código 5), como hoje. A Coleta passa ao formato 2 no item 1 da fase A. A referência de cada usina é refeita a partir da Coleta congelada (seção 8).

### 6.1 Coleta (`data/usinas/<slug>/coleta/`)

**Para todos os tipos** (formato 2; as etapas 2 a 5 deixam de ler `data/raw/`, R22):

| Arquivo | Conteúdo |
|---|---|
| `datas_obtencao.csv` | por conjunto: `arquivos_registrados` no escopo da usina, `publicacao_mais_recente` e `obtencao_mais_recente`. Substitui a leitura dos manifestos nas Análises e no Relatório, inclusive a linha "Versão dos arquivos" da cobertura |
| `dicionario_evt.json` | nas hidrelétricas com EVT: cópia do dicionário de dados da EVT, que o Tratamento passa a ler daqui |

**Só nos tipos que os usam**, cada um com a auditoria (`auditoria_<chave>.csv`, com as colunas de hoje):

| Arquivo | Colunas de valor, além de `din_instante` e `arquivo_origem` |
|---|---|
| `despacho_extraido.parquet` | `cod_usinaplanejamento`, `nom_tipopatamar`, `val_prog*` (17), `val_verif*` (15), `tip_restricaoeletrica` |
| `cvu_extraido.parquet` | `cod_usinaplanejamento`, `dat_iniciosemana`, `dat_fimsemana`, `num_revisao`, `val_cvu` |
| `cmo_extraido.parquet` | `id_subsistema`, `val_cmomediasemanal`, `val_cmoleve`, `val_cmomedia`, `val_cmopesada` |
| `fator_capacidade_extraido.parquet` | `val_geracaoprogramada`, `val_geracaoverificada`, `val_capacidadeinstalada`, `val_fatorcapacidade`, `nivel` |
| `restricao_detalhe_extraido.parquet` | `val_geracaoestimada`, `val_geracaoverificada`, `val_ventoverificado` ou `val_irradianciaverificado`, `flg_dado*invalido`, `flg_geracaorestrita`, `val_geracaoreferenciafinal`, `id_ons_conjuntousina` |
| `restricao_razao_extraido.parquet` | `val_geracao`, `val_geracaolimitada`, `val_disponibilidade`, `val_geracaoreferencia`, `cod_razaorestricao`, `num_minutos_rel`, `num_minutos_cnf`, `num_minutos_ene`, `nivel` |
| `geracao_complemento.parquet` | nas usinas sem EVT: `cod_modalidadeoperacao` e `nivel` por hora, para os trechos |
| `composicao_conjunto.csv` | as colunas de `conjuntos.csv` (seção 2.3), só do conjunto da usina |
| `capacidade_ficha.csv` | unidades geradoras: `cod_equipamento`, `num_unidadegeradora`, `val_potenciaefetiva`, `nom_combustivel`, datas |
| `trechos.csv` | seção 5.2 |

- `geracao_extraido.parquet` e as auditorias de hoje mantêm as colunas. Com a cobertura `conjunto`, `geracao_extraido.parquet` traz a série do conjunto.
- As linhas próprias sem valor da usina (A3) são contadas no resumo do `etapa.json` (`linhas_usina_sem_valor`), não numa coluna da auditoria.
- O resumo do `etapa.json` ganha `tipo`, `modalidade`, `serie_referencia` (5.1), `trechos` (quantidade) e `conjuntos_nao_aplicaveis`.

### 6.2 Tratamento (`data/usinas/<slug>/tratamento/`)

| Arquivo | Conteúdo |
|---|---|
| `base_horaria.csv` | nas usinas sem EVT: a base comum (R30): geração da série de referência com o nível, disponibilidade, programação, trecho e sinalizações |
| `despacho_horario.csv` | soma das unidades de planejamento por hora; por motivo, programado e verificado |
| `despacho_unidades_horario.csv` | o mesmo, por unidade de planejamento |
| `cvu_semanal.csv` | um valor por unidade e semana operativa (revisão mais recente), com `sinal_cvu` |
| `cmo_semanal.csv` | um valor por semana do subsistema |
| `fator_capacidade_horario.csv` | com `sinal_fc_fora_0_1` e `sinal_acima_capacidade` |
| `restricao_semi_horaria.csv` | resolução publicada, com `sinal_recurso_invalido`, `restrita`, `sem_marca_restricao` e `energia_cortada_mwh` (R12) |
| `restricao_horaria.csv` | média das duas meias-horas; hora incompleta ausente e contada (R11) |
| `restricao_razao_semi_horaria.csv` | razão por semi-hora, com o nível |

- Cada conjunto novo ganha `<chave>_ausencias.csv` e `auditoria_<chave>.csv`, como os de hoje.
- Sinalização não exclui registro (princípio V).

### 6.3 Conferência (`data/usinas/<slug>/conferencia/`)

| Arquivo | Conteúdo |
|---|---|
| `geracao_fontes.csv` | G1, só pares do mesmo nível (R13) |
| `soma_conjunto.csv` | G2 |
| `programacao_despacho.csv` | G3 |
| `verificada_despacho.csv` | G4 |
| `programacao_renovaveis.csv` | G5 |
| `nao_aplicaveis.csv` | `conferencia`, `motivo` (FR-019, princípio VI): todas as conferências do catálogo que não se aplicam à usina, inclusive na UHE |

- `conferencias.pkl` ganha as mesmas entradas, menos as não aplicáveis, que ficam só no arquivo.
- Cada resultado traz o de hoje: bases, período, quantidade comparada, coincidências, divergências e tolerância.
- Nas hidrelétricas com EVT, o relatório e a planilha não leem `nao_aplicaveis.csv` e ficam como hoje (R29).

### 6.4 Análises (`resultados.pkl`, `VERSAO_FORMATO` 2)

Campos novos em `ResultadosAnalise`:

| Campo | Conteúdo |
|---|---|
| `tipo`, `modalidade` | do perfil |
| `niveis` | chave da tabela ou figura → nível e identificador (R15) |
| `trechos` | tabela da seção 5.2 |
| `comum` | seções comuns calculadas sobre a base horária comum, nas usinas sem EVT (R30) |
| `termica` | despacho por motivo, inflexibilidade, atendimento ao despacho, disponível sem despacho, CVU × CMO (R18) |
| `renovavel` | fator de capacidade, energia cortada por razão, recurso × geração, aderência (R19) |
| `conjunto` | composição e geração do conjunto por trecho (R20) |
| `indicadores_carteira` | chaves fixas da R21, cada indicador com valor, nível e unidade |
| `omitidos` | seções e regras não avaliadas, com o motivo (R16, R17, FR-024) |

- Os campos de EVT ficam vazios nas usinas sem EVT.
- Nas hidrelétricas com EVT, os campos de hoje têm os mesmos valores. Os novos ficam vazios, salvo `tipo`, `modalidade` e `indicadores_carteira`.

### 6.5 Estrutura do relatório e conclusão

**`Secao`** (`src/relatorio/estrutura.py`):

| Campo | Conteúdo |
|---|---|
| `chave` | estável, como hoje |
| `titulo` | texto; ou mapa tipo → título, com o da UHE igual ao de hoje |
| `tipos` | tipos em que a seção existe |
| `presente` | condição sobre os resultados e a cobertura, como hoje |
| `legenda` | chave da legenda de fonte (`fontes.py`) por tipo |
| `periodo_minimo_meses` | opcional (R17) |

A lista e a ordem das seções de cada caminho estão na R14.

**Título e capa por caminho**:

| Elemento | Hidrelétrica com EVT | Usina sem EVT |
|---|---|---|
| Título | o de hoje: "<nome> — energia vertida turbinável e desempenho operacional" | "<nome> — desempenho operacional" |
| Subtítulo | o de hoje: dados abertos do ONS, período, registros horários e data de geração | o mesmo, com o período e os registros da série de referência e o nível dela |
| Bloco "Identificação nos dados do ONS" | o de hoje | os identificadores do perfil, com a linha de tipo e modalidade e o conjunto, quando há |
| Bloco "Cadastro no ONS" | o de hoje (ficha do cadastro, com a modalidade) | o mesmo |
| Bloco "Parâmetros técnicos" | o de hoje | os parâmetros do tipo (seção 3.2), com as fontes |
| Indicadores da capa | os de hoje | térmicas: geração média, horas com despacho, disponibilidade média e TEIFa, quando há; eólicas e solares: fator de capacidade, geração média e energia cortada (%); usina em conjunto: os do conjunto, identificados como tal |
| Legendas das seções comuns | as de hoje, com a EVT | as mesmas chaves, com o conjunto do ONS da série de referência no lugar da EVT |

**`RegraConclusao`** (`src/analises/conclusao.py`):

| Campo | Conteúdo |
|---|---|
| `codigo` | `C1` a `C19` (R16) |
| `tipos` | tipos em que a regra é avaliada |
| `listas` | listas em que a regra pode gerar itens; cada item traz a sua (B5) |
| `nivel_exigido` | `usina`: a regra só é avaliada com entradas do nível da usina |
| `funcao` | recebe os resultados e devolve os itens |
| `limiares` | nomes das constantes em `regras.py`, citados nas notas |
| `periodo_minimo_meses` | opcional; ausente em C1 a C11 |
| `secoes` | seções de origem, como hoje |

A ordem dos itens é a de hoje: por lista e depois pelo número da regra.

## 7. Relatório de carteira (`reports/carteiras/<nome>/`)

`<nome>` = `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`, em minúsculas (R21).

| Arquivo | Conteúdo |
|---|---|
| `relatorio_carteira.pdf`, `relatorio_carteira.md` | mesmo conteúdo, na mesma ordem (princípio VII) |
| `carteira.xlsx` | abas `USINAS`, `INDICADORES`, `ORDENACAO`, `SEM_RESULTADO`, `PANORAMA` e `FONTES` |
| `figures/` | figuras em seaborn |

**Linha da carteira** (aba `USINAS`):

| Campo | Conteúdo |
|---|---|
| `slug`, `nome`, `ceg`, `tipo`, `modalidade`, `potencia_mw` | do perfil e do catálogo |
| `cobertura`, `nivel_geracao` | do catálogo e dos trechos |
| `periodo` | início e fim da série de referência |
| indicadores | os de `indicadores_carteira` aplicáveis ao tipo, cada um com o nível; vazio, nunca zero, quando não se aplica |
| `possiveis_problemas`, `pontos_atencao`, `confirmar_agente`, `verificar_campo` | quantidade de todos os itens de cada lista da conclusão |
| `analises_concluida_em` | do `etapa.json` das Análises |

**Sem resultado** (aba `SEM_RESULTADO`): cada usina do recorte com o motivo: sem perfil, perfil em rascunho, perfil inválido, Análises ausentes, com falha, desatualizadas ou em formato antigo, ou só agregado no ONS (ver o panorama). As linhas de conjunto do catálogo não contam como usina.

**Ordenação**: possíveis problemas (decrescente), pontos de atenção (decrescente) e nome (FR-027).

**Panorama** (aba `PANORAMA`): só com `--estado`. Na carteira só por tipo, é omitido, com o motivo nas notas (R21).

## 8. Relatórios de referência (`relatorios_referencia/`)

```text
relatorios_referencia/
└── <slug>/
    ├── referencia.json
    ├── perfil.toml                             # perfil usado na geração
    ├── relatorio_analise_estatistica.pdf      # no git, por exceção no .gitignore
    ├── relatorio_analise_estatistica.md
    ├── perfil_estatistico_anual.xlsx
    ├── perfil_estatistico_anual.csv
    ├── figures/
    └── coleta/                                 # Coleta congelada: só os arquivos do etapa.json e ele; fora do git
```

| Campo de `referencia.json` | Conteúdo |
|---|---|
| `usina` | slug |
| `data_geracao` | data fixa usada na geração ("DD/MM/AAAA HH:MM") |
| `aprovado_em` | data da aprovação pelo usuário |
| `periodo` | início e fim da série de referência |
| `arquivos` | nome, bytes e SHA-256 de cada arquivo do relatório |
| `perfil` | SHA-256 do perfil congelado |
| `coleta` | nome, bytes e SHA-256 de cada arquivo da Coleta congelada |

- **Git**: o relatório e o perfil congelado entram no git; a Coleta congelada não.
- **Cópias de segurança**: `copia-seguranca` copia `relatorios_referencia/` inteira para cada cópia nova e a confere pelos SHA-256 (R22).
- **Substituição**: a referência só é substituída com a aprovação do usuário e só depois de a atual estar commitada. A anterior continua no histórico do git e nas cópias de segurança.
- **Comparação**: `comparar --todas` refaz as etapas 2 a 5 num espaço isolado a partir de `coleta/` e do `perfil.toml` congelados e compara com o relatório. `referencia.json`, `perfil.toml` e `coleta/` ficam fora da comparação. Um perfil atual diferente do congelado gera só um aviso.

## 9. Usinas fictícias (`tests/fixtures/usinas_ficticias/`)

Uma pasta por tipo (`uhe`, `pch`, `cgh`, `ute`, `utn`, `eol`, `ufv`), cada uma com:
- o `perfil.toml`, com valores inventados;
- os brutos sintéticos gerados por `tests/fixtures/brutos_ficticios.py`, no formato de cada conjunto do registro.

O que cada uma exercita está na R23.

## 10. Requisitos × entidades

| Requisitos | Entidades |
|---|---|
| FR-001, FR-002 | enumerações (1); registro (4) |
| FR-003 a FR-005 | catálogo (2) |
| FR-006 a FR-011 | perfil (3); códigos para o rascunho (2.5) |
| FR-012, FR-015 | série de referência e trechos (5); cobertura do perfil (3.3) |
| FR-013, FR-014 | registro (4); Coleta (6.1) |
| FR-016, FR-017 | Tratamento (6.2) |
| FR-018, FR-019 | Conferência (6.3) |
| FR-020 a FR-023 | Análises (6.4); estrutura e conclusão (6.5) |
| FR-024, FR-025 | estrutura (6.5); legendas (R15); invariantes da UHE (R29) |
| FR-026, FR-027 | carteira (7); agregados (2.6) |
| FR-028, FR-029, SC-001 | referências (8) |
| FR-030, SC-008 | `ajustes-specs/` (R26) |
