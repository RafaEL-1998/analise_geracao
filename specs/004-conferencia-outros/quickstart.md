# Quickstart: Conferência com Outras Fontes do ONS e Programação Diária

**Feature**: `004-conferencia-outros` | **Date**: 2026-10-05

## Pré-requisitos
- Base de EVT tratada em `data/processed/` (specs 001 e 002).
- Ambiente: `.\venv\Scripts\Activate.ps1`.

## 1. Programação diária (US1), sem alterar a base de EVT

```powershell
python -m src.main --programacao-only
```

Esperado:
- `data/raw/programacao_diaria/` com um arquivo por dia publicado no período e `_manifesto_ons.json`.
- Log com arquivos lidos, linhas da usina, dias incompletos e dias ausentes.
- `data/processed/uhe_sao_domingos_ons_programacao_horaria.csv` com 24 linhas por dia publicado.
- Segunda execução: nenhum arquivo baixado de novo (SC-003).

## 2. Indicadores oficiais (US2)

```powershell
python -m src.main --indicadores-only
```

Esperado: log "TEIFa/TEIP recalculadas a partir das horas em N meses; diferença máxima ≈ 0" e as tabelas listadas em [data-model.md](data-model.md).

## 3. Relatório

```powershell
python -m src.analyzer
```

Esperado:
- Constatação "Programação diária do ONS" e seção "Operação verificada e programação diária do ONS" no PDF e no Markdown.
- Abas `PROG_*` em `reports/perfil_estatistico_anual.xlsx`.
- Soma das classes das horas paradas com EVT = total dessas horas no período comum (SC-002).
- Números da constatação iguais aos da aba `PROG_RESUMO_MENSAL` (SC-004).

## 4. Testes

```powershell
pytest tests/ -v
```

Esperado: suíte completa aprovada, sem acesso à rede e sem alterar arquivos do projeto.

## 5. Não regressão (SC-006)

A base de EVT (`uhe_sao_domingos_energia_vertida_tratado.*`, `..._consolidado.csv`) mantém data de modificação e conteúdo após os passos 1 a 3.
