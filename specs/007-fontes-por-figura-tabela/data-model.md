# Data Model: Fonte Explícita em Cada Figura e Tabela do Relatório

**Feature**: [spec.md](spec.md) · **Date**: 2026-10-06 · Decisões em [research.md](research.md)

## 1. Conjunto de origem (catálogo)

| Id | Nome no relatório | Identificador da usina (constituição, princípio IV) | Pasta do manifesto (data de obtenção) |
|---|---|---|---|
| `evt` | Energia Vertida Turbinável | cod_usina 153 (reservatório SAO DOMINGOS) | `data/raw` |
| `dispf_mensal` | Indicadores de disponibilidade por unidade geradora, base mensal | CEG UHE.PH.MS.028761-0.01 (id ONS MSUHSD) | `data/raw/indicadores_ons/ind_disponibilidade_fgeracao_uge_mensal` |
| `dispf_anual` | Indicadores de disponibilidade por unidade geradora, base anual | idem | `…/ind_disponibilidade_fgeracao_uge_anual` |
| `teif_teip` | Taxas TEIFa e TEIP | idem | `…/taxa_teif_teip` |
| `teif_teip_parametro` | Parâmetros das taxas TEIFa e TEIP (horas por estado operativo) | idem | `…/taxa_teif_teip_parametro` |
| `programacao` | Programação diária | PRUHSD (nome e estado MS) | `data/raw/programacao_diaria` |
| `disponibilidade` | Disponibilidade por usina | MSUHSD (CEG e estado MS) | `data/raw/disponibilidade_usina` |
| `hidrologia` | Dados hidrológicos horários | cod_usina 153 (reservatório PNUHSD) | `data/raw/dados_hidrologicos_ho` |
| `geracao` | Geração por usina | MSUHSD (CEG e estado MS) | `data/raw/geracao_usina_2` |
| `cadastro` | Modalidade das usinas (cadastro) | CEG UHE.PH.MS.028761-0.01 (id ONS e estado MS) | `data/raw/modalidade_usina` |

- `projeto`: parâmetros do projeto (potência, engolimento, garantia física etc.). Não é conjunto do ONS; a legenda remete à coluna "Origem" da tabela de parâmetros. Não conta em N.
- **Carregado** (rodapé, N): `evt` sempre; os 4 de indicadores com `res.ons`; `programacao` com `res.programacao`; os 4 da spec 006 com os campos correspondentes.

## 2. Conferência entre fontes

| Id | Dado | Fonte A × Fonte B | Resultado mostrado |
|---|---|---|---|
| `geracao` | geração horária | `evt` × `geracao` | horas coincidentes / horas comuns (%), divergências → `GER_DIVERGENCIAS` |
| `disponibilidade` | disponibilidade declarada | `evt` × `disponibilidade` (operacional) | idem → `DISP_DIVERGENCIAS` |
| `vazoes` | vazões turbinada e vertida | `evt` × `hidrologia` | % de horas coincidentes (meta 99%, tolerância 0,5 m³/s) |
| `teifa_teip` | TEIFa e TEIP | recalculadas de `teif_teip_parametro` × publicadas em `teif_teip` | meses reproduzidos / meses publicados (reproduzido = as duas taxas com diferença de até `TOLERANCIA_REPRODUCAO_TAXAS_PP` = 0,001 p.p.); maior diferença (p.p.) |
| `dispf_horas` | DISPF | `dispf_mensal` × `teif_teip_parametro` | meses-unidade divergentes → `ONS_DIVERGENCIAS` |
| `cadastro` | potência e estado | `cadastro` × `projeto` | sem divergência / divergências |

**Estados do texto**: `feita` (com resultado), `nao_feita` (base ausente: "conferência com … não feita nesta execução").

**Dados sem outra fonte pública** (FR-004): EVT; disponibilidade sincronizada; afluência, níveis e volume útil; programação. O DISPF tem a conferência `dispf_horas` e por isso não entra nesta lista.

## 3. Mapa de fontes (figura, tabela ou bloco)

Campos de cada entrada: `conjuntos` (ids), `conferencias` (ids), `sem_outra_fonte` (textos), `calculado` (verdadeiro quando o valor é calculado neste relatório).

| Chave | Onde | Conjuntos | Conferências | Calculado |
|---|---|---|---|---|
| `bloco_identificacao` | capa do PDF | evt | — | não |
| `bloco_parametros` | capa do PDF | projeto | — | não |
| `bloco_cadastro` | PDF; seção de identificação | cadastro | cadastro | não |
| `tab_cobertura` | PDF, "Fonte e cobertura dos dados" (se houver tabela) | evt | — | não |
| `tab_indicadores_anuais` | Indicadores anuais | evt, projeto | geracao, disponibilidade | sim |
| `tab_disponibilidade_geracao_anual` | PDF, Disponibilidade e geração por ano | evt, projeto | geracao, disponibilidade | sim |
| `tab_ons_disp_anual` | Indicadores ONS: declarada × DISPF | evt, dispf_mensal | disponibilidade, dispf_horas | sim |
| `tab_ons_decomposicao` | Indicadores ONS: contribuição para TEIFa/TEIP | teif_teip_parametro, teif_teip | teifa_teip | sim |
| `tab_ons_ug_anual` | Indicadores ONS: anuais por unidade | dispf_anual | dispf_horas | não |
| `tab_ons_horas` | Indicadores ONS: horas por estado operativo | teif_teip_parametro | dispf_horas | não |
| `tab_ons_divergencias` | Indicadores ONS: DISPF × horas | dispf_mensal, teif_teip_parametro | dispf_horas | não |
| `tab_eventos_indisponibilidade` | Eventos de indisponibilidade total | evt | disponibilidade | sim |
| `tab_eventos_parada_evt` | Maiores eventos de parada com EVT | evt | geracao | sim |
| `tab_evt_por_nivel` | EVT por nível de geração | evt | geracao | sim |
| `tab_programacao_mensal`, `tab_programacao_hora`, `tab_programacao_eventos` | Programação diária | programacao, evt | geracao | sim |
| `tab_disponibilidade_anual` | Disponibilidade sincronizada por ano | disponibilidade, evt, teif_teip_parametro | disponibilidade, geracao | sim |
| `tab_disponibilidade_paradas` | Horas paradas por sincronização | disponibilidade, evt, programacao | disponibilidade, geracao | sim |
| `tab_disponibilidade_divergencias` | Divergências operacional × declarada | disponibilidade, evt | disponibilidade | não |
| `tab_faixas_afluencia`, `tab_faixas_afluencia_evt` | Hidrologia: faixas | hidrologia, evt | vazoes | sim |
| `tab_hidrologia_anual`, `tab_hidrologia_perfil` | Hidrologia: anual e perfil | hidrologia, evt | vazoes | sim |
| `tab_geracao_zero` | Horas com geração zero | evt | geracao | sim |
| `tab_geracao_oficial` | Conferência da geração | geracao, evt | geracao | não |
| `tab_vazoes` | PDF, Vazões defluentes por ano | evt | vazoes | sim |
| `tab_regras_validacao`, `tab_registros_sinalizados` | Qualidade dos dados | evt | — | sim |
| `tab_extremos` | Extremos do período | evt | geracao, disponibilidade, vazoes | sim |
| `tab_parametros` | PDF, Parâmetros utilizados | projeto | — | não |
| `serie_temporal` (fig. 01) | — | evt | geracao, disponibilidade | não |
| `evt_mensal` (fig. 02) | — | evt | — | sim |
| `perfil_horario` (fig. 03) | — | evt | geracao | sim |
| `disponibilidade_anual` (fig. 04) | — | evt | geracao, disponibilidade | sim |
| `vazoes_defluentes` (fig. 05) | — | evt | vazoes | sim |
| `disponibilidade_sincronizada` (fig. 06) | — | disponibilidade, evt | disponibilidade, geracao | sim |
| `faixas_afluencia` (fig. 07) | — | hidrologia, evt | vazoes | sim |
| `perfil_hidrologico` (fig. 08) | — | hidrologia, evt | vazoes | sim |

A lista final de chaves de tabela é fechada na implementação, a partir dos pontos de emissão no código (`_tabela_md` e `self._tabela`/`_bloco_chave_valor`). O teste de cobertura (research R9) garante que nenhuma fique sem entrada.

## 4. Mapa das abas

| Abas | Conjuntos | Conferências |
|---|---|---|
| `INDICADORES_ANUAIS`, `INDICADORES_GLOBAIS`, `COBERTURA_POR_ANO`, `AGENTES`, `EVT_*`, `PERFIL_HORARIO_*`, `EVENTOS_*`, `HORAS_GERACAO_ZERO_MES`, `ANOMALIAS`, `RESUMO_ANOMALIAS`, `VALIDACAO_REGRAS`, `EXTREMOS`, `PERFIL_ESTATISTICO_ANUAL` | evt | as que se aplicam às grandezas da aba (geracao, disponibilidade, vazoes) |
| `CONSTATACOES` | todos os carregados | todas as feitas |
| `PARAMETROS` | projeto e todos os carregados | — |
| `ONS_*` | conforme seção 3 | teifa_teip, dispf_horas |
| `PROG_*` | programacao, evt | geracao |
| `DISP_*` | disponibilidade, evt (e programacao, teif_teip_parametro em `DISP_CLASSES_PARADA`, `DISP_HORAS_PARADAS`, `DISP_MENSAL`, `DISP_ANUAL`) | disponibilidade |
| `HID_*` | hidrologia, evt | vazoes |
| `GER_*` | geracao, evt | geracao |
| `CAD_*` | cadastro | cadastro |
| `DICIONARIOS` | dicionários dos conjuntos | — |

**Aba `FONTES`** (última da planilha): `aba`, `conjuntos_origem`, `conferencias`, `sem_outra_fonte`, `calculado_no_relatorio`; uma linha por aba exportada.

## 5. Campo novo em `ResultadosAnalise`

| Campo | Conteúdo |
|---|---|
| `fontes` | `obtencao` (id do conjunto → data UTC ou vazio) e `carregados` (lista de ids, que dá N) |
| `ons["recalculo_taxas"]` | TEIFa/TEIP recalculadas × publicadas; já existia (spec 004), não foi preciso recalcular |

## 6. Ajustes feitos na implementação (06/10/2026)

- **Chaves a mais**: `tab_capa_indicadores` (indicadores da capa do PDF) e `tab_perfil_horario` (tabela diurna × noturna do PDF); `tab_cobertura` confirmada (tabela da seção "Fonte e cobertura dos dados").
- **Figura 01**: médias diárias, por isso "Calculado neste relatório"; os indicadores da capa citam também a conferência da TEIFa/TEIP.
- **Recálculo da TEIFa/TEIP**: já existia em `res.ons["recalculo_taxas"]` (spec 004); na base real, 21 de 21 meses reproduzidos.
- **Cobertura**: no PDF, `_figura` e `_bloco_chave_valor` emitem a legenda sozinhos; cada `_tabela` e as duas tabelas montadas à mão recebem a legenda pela chave. Os contadores `_desenhados` e `_legendas` são conferidos em `build_pdf`.
