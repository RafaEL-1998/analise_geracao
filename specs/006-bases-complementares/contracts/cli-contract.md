# CLI Contract: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança

**Feature**: `006-bases-complementares` | **Date**: 2026-10-05

## `python -m src.main` (coleta)

Etapas: 1 (download da EVT), 2 (filtragem e consolidação), 3 (indicadores), 4 (programação) e, nesta feature:
- 5: disponibilidade;
- 6: hidrologia;
- 7: geração;
- 8: cadastro.

As etapas 5 a 8 usam o período da base consolidada (ou da base tratada existente, nos modos `-only`).

| Opção | Efeito |
|---|---|
| `--full-pipeline` (padrão) | Etapas 1 a 8. **Baixa de novo a EVT, se o ONS republicar**; para não tocar a base EVT, use `--complementares-only` |
| `--complementares-only` (novo) | Etapas 5 a 8 e seus dicionários, no período da base EVT existente. **Não toca a base EVT.** Comando recomendado |
| `--disponibilidade-only` (novo) | Só a etapa 5 (e os dicionários do conjunto) |
| `--hidrologia-only` (novo) | Só a etapa 6 (e os dicionários do conjunto) |
| `--geracao-only` (novo) | Só a etapa 7 (e os dicionários do conjunto) |
| `--cadastro-only` (novo) | Só a etapa 8 (e os dicionários do conjunto) |
| `--dicionarios-only` (novo) | Só os dicionários (PDF e JSON) dos 10 conjuntos, sem baixar dados |
| `--sem-disponibilidade`, `--sem-hidrologia`, `--sem-geracao`, `--sem-cadastro` (novos) | Pulam a etapa correspondente no pipeline completo |
| `--sem-dicionarios` (novo) | Não obtém dicionários nesta execução (uso excepcional; registrado em log como aviso) |
| `--indicadores-only`, `--programacao-only`, `--sem-indicadores`, `--sem-programacao` | Como antes. Quando baixam dados, também obtêm os dicionários dos seus conjuntos |
| `--filter-only` | Etapas 2 a 8 sem download (usa os arquivos já baixados e não obtém dicionários) |
| `--force-download` | Baixa de novo os arquivos de dados das etapas executadas. Os dicionários são sempre obtidos |
| `--raw-dir`, `--processed-dir` | Pastas de entrada e saída. As etapas novas usam `<raw-dir>/disponibilidade_usina`, `<raw-dir>/dados_hidrologicos_ho`, `<raw-dir>/geracao_usina_2` e `<raw-dir>/modalidade_usina` |
| `--log-level` | Nível de log de todos os módulos, inclusive os novos |

Os modos `--*-only` são mutuamente exclusivos.

**Códigos de saída**:

| Código | Significado |
|---|---|
| 0 | sucesso |
| 1 | erro, inclusive falha de gravação em `data/processed/` (o arquivo afetado é restaurado e informado no log) |
| 2 | arquivo de dados que não pôde ser lido, em qualquer etapa |
| 3 (novo) | falha de alinhamento da hidrologia: coincidência das vazões turbinada e vertida abaixo de 99% |

Falha ao obter um dicionário **não** altera o código de saída: é registrada no log (aviso) e em `relatorio_dicionarios_ons.csv`.

## Módulos executáveis isoladamente (novos)

| Comando | Opções | Saídas em `data/processed/` |
|---|---|---|
| `python -m src.disponibilidade_ons` | `--no-download`, `--force-download`, `--log-level` | `uhe_sao_domingos_ons_disponibilidade_horaria.csv`, `uhe_sao_domingos_ons_disponibilidade_ausencias.csv`, `relatorio_auditoria_disponibilidade_ons.csv` |
| `python -m src.hidrologia_ons` | idem | `uhe_sao_domingos_ons_hidrologia_horaria.csv`, `uhe_sao_domingos_ons_hidrologia_ausencias.csv`, `uhe_sao_domingos_ons_hidrologia_alinhamento.csv`, `relatorio_auditoria_hidrologia_ons.csv` |
| `python -m src.geracao_ons` | idem | `uhe_sao_domingos_ons_geracao_horaria.csv`, `uhe_sao_domingos_ons_geracao_ausencias.csv`, `relatorio_auditoria_geracao_ons.csv` |
| `python -m src.cadastro_ons` | idem | `uhe_sao_domingos_ons_cadastro.csv`, `relatorio_auditoria_cadastro_ons.csv` |
| `python -m src.dicionarios_ons` | `--conjuntos <id ...>` (padrão: os 10), `--log-level` | `relatorio_dicionarios_ons.csv`; os arquivos ficam em `<pasta bruta do conjunto>/_dicionarios/` |

Os mesmos códigos de saída valem para cada módulo. As colunas de cada arquivo estão em [data-model.md](../data-model.md).

## `python -m src.analyzer` (spec 003)

Carrega automaticamente, se existirem, a disponibilidade, a hidrologia, a geração oficial, o cadastro e o registro de dicionários. O que faltar gera um aviso no log com o comando para gerá-lo, e o relatório sai sem a seção correspondente.

- **Seções novas** (Markdown e PDF):
  - "Identificação da usina no cadastro do ONS";
  - "Disponibilidade sincronizada";
  - "Afluência, vertimento e nível do reservatório";
  - "Conferência da geração com a série oficial".
- **Abas novas**:
  - `DISP_CONFERENCIA`, `DISP_DIVERGENCIAS`, `DISP_CLASSES_PARADA`, `DISP_HORAS_PARADAS`, `DISP_MENSAL`, `DISP_ANUAL`, `DISP_AUSENCIAS`, `DISP_AUDITORIA`;
  - `HID_ALINHAMENTO`, `HID_FAIXAS_AFLUENCIA`, `HID_FAIXAS_ANUAL`, `HID_HORAS_EVT`, `HID_MENSAL`, `HID_ANUAL`, `HID_PERFIL_HORA_DO_DIA`, `HID_AUSENCIAS`, `HID_AUDITORIA`;
  - `GER_CONFERENCIA`, `GER_MENSAL`, `GER_ANUAL`, `GER_DIVERGENCIAS`, `GER_AUSENCIAS`, `GER_AUDITORIA`;
  - abas sem linhas não são criadas (ex.: `DISP_DIVERGENCIAS` quando não há divergência);
  - `CAD_FICHA` e `CAD_AUDITORIA`;
  - `DICIONARIOS`.
- **Figuras novas**:
  - `06_disponibilidade_operacional_sincronizada_mensal.png`;
  - `07_evt_por_faixa_de_afluencia.png`;
  - `08_perfil_horario_nivel_vazoes.png`.
