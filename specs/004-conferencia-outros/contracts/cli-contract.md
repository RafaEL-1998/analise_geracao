# CLI Contract: Conferência com Outras Fontes do ONS e Programação Diária

**Feature**: `004-conferencia-outros` | **Date**: 2026-10-05

## `python -m src.main` (coleta)

| Opção | Efeito |
|---|---|
| `--full-pipeline` (padrão) | Etapas 1 e 2 (EVT, spec 001), 3 (indicadores, US2) e 4 (programação diária, US1), no período da base recém-consolidada |
| `--indicadores-only` | Só a etapa 3, no período da base de EVT existente (não altera a base) |
| `--programacao-only` | Só a etapa 4, no período da base de EVT existente (não altera a base) |
| `--sem-indicadores` | Pula a etapa 3 |
| `--sem-programacao` | Pula a etapa 4 |
| `--filter-only` | Etapas 2 a 4 sem download (usa os arquivos já baixados) |
| `--force-download` | Baixa de novo todos os arquivos das etapas executadas |
| `--raw-dir`, `--processed-dir` | Pastas de entrada e saída; as etapas 3 e 4 usam `<raw-dir>/indicadores_ons` e `<raw-dir>/programacao_diaria` |

Códigos de saída: 0 sucesso; 1 erro; 2 arquivo que não pôde ser lido (EVT, indicadores ou programação).

## `python -m src.programacao_ons`

| Opção | Efeito |
|---|---|
| (nenhuma) | Sincroniza os arquivos diários do período da base de EVT existente, extrai, converte e exporta |
| `--no-download` | Usa apenas os arquivos já presentes em `data/raw/programacao_diaria/` |
| `--force-download` | Baixa todos de novo |

Saídas em `data/processed/`:
- `uhe_sao_domingos_ons_programacao_horaria.csv`
- `uhe_sao_domingos_ons_programacao_dias_ausentes.csv`
- `relatorio_auditoria_programacao_ons.csv`

## `python -m src.indicadores_ons` (US2, existente)

`--no-download`, `--force-download`; saídas listadas em [data-model.md](../data-model.md).

## `python -m src.analyzer` (spec 003)

Carrega automaticamente os indicadores (US2) e a programação (US1) se os arquivos tratados existirem; caso contrário, registra aviso e gera o relatório sem as seções correspondentes. Abas novas da planilha: `PROG_RESUMO_MENSAL`, `PROG_EVENTOS_DESVIO`, `PROG_HORA_DO_DIA`, `PROG_DIAS_AUSENTES`.
