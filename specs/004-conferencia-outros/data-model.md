# Data Model: Conferência com Outras Fontes do ONS e Programação Diária

**Feature**: `004-conferencia-outros` | **Date**: 2026-10-05

## US1 — Programação diária

### ProgramacaoPatamar (extraída dos arquivos diários)
| Campo | Tipo | Origem / regra |
|---|---|---|
| `dia` | data | nome do arquivo `PROGRAMACAO_DIARIA_AAAA_MM_DD` |
| `num_patamar` | inteiro 1–48 | `num_patamar` (1 = 00:00–00:30) |
| `geracao_programada_mw` | real | `val_geracaoprogramada` (texto → número; vírgula decimal aceita) |
| `arquivo_origem` | texto | nome do arquivo lido |

Regras: só linhas com `cod_exibicaousina == "PRUHSD"`; `nom_usina` contém "SAO DOMINGOS" e `id_estado == "MS"` (conferência). Chave única (`dia`, `num_patamar`).

### ProgramacaoHoraria → `data/processed/uhe_sao_domingos_ons_programacao_horaria.csv`
| Campo | Tipo | Regra |
|---|---|---|
| `din_instante` | data-hora | `dia` + ((`num_patamar` − 1) ÷ 2) horas — hora de início |
| `geracao_programada_mw` | real | média dos patamares da hora |
| `patamares` | inteiro | número de patamares usados (2 = hora completa) |

### AuditoriaProgramacao → `data/processed/relatorio_auditoria_programacao_ons.csv`
| Campo | Regra |
|---|---|
| `arquivo`, `dia` | identificação |
| `linhas_lidas`, `linhas_usina` | contagens |
| `linhas_codigo_sem_conferencia` | código `PRUHSD` com nome ou estado diferentes |
| `patamares` | patamares distintos da usina |
| `data_interna_confere` | data interna (qualquer formato publicado) = data do nome |
| `status` | `PROCESSADO`, `INCOMPLETO` (≠ 48 patamares), `SEM_REGISTROS` ou `FALHA` |

### DiasAusentes → `data/processed/uhe_sao_domingos_ons_programacao_dias_ausentes.csv`
Dias do período (primeiro ao último dia recortado) sem arquivo publicado.

### ClassificacaoHoraria (calculada na análise, sobre as horas comuns à base de EVT)
| Classe | Condição |
|---|---|
| `PARADA_EVT_PROGRAMACAO_ZERO` | geração ≤ 1 MW, EVT > 0, programação ≤ 1 MW |
| `PARADA_EVT_PROGRAMACAO_POSITIVA` | geração ≤ 1 MW, EVT > 0, programação > 1 MW |
| `PARADA_SEM_EVT` | geração ≤ 1 MW, EVT = 0 |
| `GERANDO_PROGRAMACAO_ZERO` | geração > 1 MW, programação ≤ 1 MW |
| `GERANDO_COM_PROGRAMACAO` | geração > 1 MW, programação > 1 MW |

Horas da base de EVT sem programação (dias ausentes ou patamar faltante) ficam fora da classificação e são contadas à parte.

### ResumoMensalProgramacao (aba `PROG_RESUMO_MENSAL`)
`mes`, `horas_comuns`, horas por classe, `evt_mwh`, `evt_parada_programacao_zero_mwh`, `participacao_evt_programacao_zero_pct`, `horas_parada_programacao_acima_limiar`, `disponibilidade_media_parada_programacao_zero_mw`, `desvio_medio_absoluto_mw`.

### EventoDesvioProgramacao (aba `PROG_EVENTOS_DESVIO`)
Horas consecutivas com geração ≤ 1 MW e programação > 5 MW: `inicio`, `fim`, `duracao_h`, `programacao_media_mw`, `disponibilidade_media_mw`, `evt_mwh`.

### PerfilHorario (aba `PROG_HORA_DO_DIA`)
Por hora do dia: horas `PARADA_EVT_PROGRAMACAO_ZERO` e EVT correspondente.

## US2 — Indicadores oficiais (implementado em 02/10/2026)

Arquivos em `data/processed/` (ver `src/indicadores_ons.py`):
- `uhe_sao_domingos_ons_ug_indicadores_mensal.csv`: `mes`, `ug`, `cod_equipamento`, `potencia_mw`, `dispf`, `indisppf`, `indispff`, `dmdff`, `fdff`, `tdff`, `id_usina`, `agente`, `modalidade`, `arquivo_origem`.
- `uhe_sao_domingos_ons_ug_indicadores_anual.csv`: idem com `ano`.
- `uhe_sao_domingos_ons_ug_horas_estado_mensal.csv`: `mes`, `ug`, `HP`, `HS`, `HRD`, `HDP`, `HDF`, `HDCE`, `HEDP`, `HEDF`, `num_versao`, `residuo_identidade_h`, `potencia_mw`. Identidade: HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF.
- `uhe_sao_domingos_ons_teifa_teip_mensal.csv`: `mes`, `teifa`, `teip` (fração), `num_versao`, `din_calculo`.
- `uhe_sao_domingos_ons_divergencias_indicadores.csv` e `relatorio_auditoria_indicadores_ons.csv`.
- Fórmulas (janela de 60 meses, ponderadas pela potência): TEIFa = Σ(HDF + HEDF) ÷ Σ(HP − HDP − HEDP); TEIP = Σ(HDP + HEDP) ÷ ΣHP.

## Relações
- ClassificacaoHoraria = base de EVT tratada (spec 002) ⋈ ProgramacaoHoraria por `din_instante`.
- Os resultados de US1 e US2 alimentam `ResultadosAnalise` (spec 003) como blocos opcionais; sem os arquivos tratados, o relatório sai sem as seções correspondentes.
