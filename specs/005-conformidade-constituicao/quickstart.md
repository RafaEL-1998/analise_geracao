# Quickstart: Conformidade com a Constituição 1.1.0

**Feature**: `005-conformidade-constituicao` | **Date**: 2026-10-05

## 1. Testes (inclui republicação simulada, linhas irregulares, nível de log, dependências e figuras)

```powershell
pytest tests/ -v
```

Esperado: suíte aprovada, sem rede e sem alterar arquivos do projeto (SC-001 a SC-004, SC-006).

## 2. Linhas irregulares na base real, sem download

```powershell
python -m src.main --filter-only --sem-indicadores --sem-programacao --log-level WARNING
```

Esperado: nenhuma mensagem INFO (SC-002); `relatorio_auditoria_varredura.csv` com a coluna `registros_formato_irregular` = 0 em todos os arquivos (SC-003); base consolidada com o mesmo conteúdo de antes (comparar hash).

## 3. Relatório com figuras em seaborn

```powershell
python -m src.analyzer
```

Esperado: 5 figuras em `reports/figures/` com os mesmos nomes, 300 DPI; `reports/relatorio_analise_estatistica.md` idêntico ao anterior e abas da planilha com os mesmos valores (SC-005); conferência visual das figuras.

## 4. Dependências

```powershell
pip install -r requirements.txt
```

Esperado: instala apenas pacotes usados; o teste de dependências da etapa 1 confirma a correspondência (SC-004).
