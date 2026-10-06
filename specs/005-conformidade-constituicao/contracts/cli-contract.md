# CLI Contract: Conformidade com a Constituição 1.1.0

**Feature**: `005-conformidade-constituicao` | **Date**: 2026-10-05

## `--log-level {DEBUG,INFO,WARNING,ERROR}` (padrão INFO)

| Ponto de entrada | Antes | Depois |
|---|---|---|
| `python -m src.main` | só o logger `main` | todos os loggers do pipeline |
| `python -m src.processor` | `processor` e `validator` | todos |
| `python -m src.analyzer` | só `analyzer` | todos (inclui PDF, indicadores e programação carregados) |
| `python -m src.indicadores_ons` | sem a opção | aceita e aplica a todos |
| `python -m src.programacao_ons` | sem a opção | aceita e aplica a todos |
| `python -m src.pdf_generator` | sem a opção | aceita e aplica a todos |

Valor inválido: erro de argumento (código 2), sem execução.

## Versões anteriores

Sem opção nova. Em qualquer coleta (`src.main`, `--indicadores-only`, `--programacao-only`, `src.indicadores_ons`, `src.programacao_ons`, inclusive com `--force-download`), arquivo republicado com conteúdo diferente tem a cópia anterior movida para `<pasta bruta>/_versoes_anteriores/` e registrada no manifesto; o log informa `Versão anterior preservada: <arquivo>`.

## Auditoria da filtragem

`data/processed/relatorio_auditoria_varredura.csv` ganha a coluna `registros_formato_irregular`. O código de saída do `src.main` não muda por causa dela (linhas irregulares são avisadas, não são falha de leitura).
