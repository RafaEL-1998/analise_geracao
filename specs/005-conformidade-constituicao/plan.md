# Implementation Plan: Conformidade com a Constituição 1.1.0 - UHE São Domingos

**Branch**: `005-conformidade-constituicao` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-conformidade-constituicao/spec.md`

## Summary

Fechar as lacunas entre o pipeline e a constituição 1.1.0 sem alterar números nem textos do relatório: (US1) preservar em `_versoes_anteriores/` a versão anterior de arquivos brutos republicados pelo ONS, com registro no manifesto; (US2) refazer as 5 figuras com seaborn, mantendo nomes, conteúdo e paleta; (US3) aplicar o nível de log a todos os loggers do pipeline por uma função única em `src/logger.py`; (US4) contar e avisar linhas de EVT com número de campos diferente do cabeçalho; (US5) alinhar `requirements.txt` aos pacotes importados, com teste automático.

## Technical Context

**Language/Version**: Python 3.14 (venv do projeto; compatível com 3.10+)

**Primary Dependencies**: pandas 3.0, numpy 2.5, pyarrow 25, openpyxl 3.1, matplotlib 3.11, seaborn 0.13.2, reportlab 5.0; pytest 9 (testes). `hashlib` (biblioteca padrão) para a soma de verificação.

**Storage**: arquivos locais; versões anteriores em `<pasta bruta>/_versoes_anteriores/`; manifesto `_manifesto_ons.json` de cada pasta bruta ganha a lista `versoes_anteriores` por arquivo.

**Testing**: pytest com arquivos sintéticos em pastas temporárias, sem rede (download simulado por `unittest.mock`).

**Target Platform**: Windows 11 + PowerShell

**Project Type**: CLI / pipeline de dados

**Performance Goals**: sem regressão perceptível; a soma de verificação só é calculada quando um arquivo é baixado de novo.

**Constraints**: relatório com textos e tabelas idênticos (FR-007); não baixar de novo os arquivos brutos atuais; paleta e estilo atuais de `src/analyzer.py`; carregar a skill de visualização antes de escrever código de gráfico.

**Scale/Scope**: 3 pastas brutas (EVT: 42 CSV; indicadores: 18 CSV; programação: 712 Parquet); 5 figuras; 10 loggers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / requisito (v1.1.0) | Situação | Observação |
|---|---|---|
| I. SDD | ✅ | spec → plan → tasks → implement nesta feature |
| II. Python exclusivo | ✅ | sem scripts shell com regra de negócio |
| III. Varredura exaustiva | ✅ | inalterada; nenhuma heurística nova de descarte |
| IV. Filtragem e rastreabilidade | ✅ após US4 | linhas irregulares passam a ser registradas em log e na auditoria |
| V. Idempotência e observabilidade | ✅ após US1 e US3 | versão anterior preservada; nível de log em todos os módulos |
| VI. Escopo exclusivo da usina | ✅ | nenhuma mudança de identificação |
| Req. 1 — dependências usadas | ✅ após US5 | teste automático compara imports e `requirements.txt` |
| Req. 3 — `.bak` antes de escrever | ✅ | cópia integral `_backup_2026-10-05_antes_spec005/` (código, testes, specs, relatórios) antes da implementação |
| Req. 5 — gráficos com seaborn | ✅ após US2 | 5 figuras refeitas; anotações sobre os eixos do seaborn |

**Re-check pós-design**: sem violações. Nenhuma justificativa de complexidade necessária.

## Project Structure

### Documentation (this feature)

```text
specs/005-conformidade-constituicao/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── logger.py            # + LOGGERS_PIPELINE e configurar_nivel_log()
├── collector.py         # + preservação da versão anterior (US1)
├── models.py            # + AuditoriaArquivo.registros_formato_irregular (US4)
├── filter.py            # + contagem e aviso de linhas irregulares (US4)
├── consolidator.py      # + coluna nova no relatório de auditoria (US4)
├── main.py              # usa configurar_nivel_log (US3)
├── processor.py         # usa configurar_nivel_log (US3)
├── analyzer.py          # figuras com seaborn (US2); usa configurar_nivel_log (US3)
├── pdf_generator.py     # --log-level no main (US3)
├── indicadores_ons.py   # --log-level no main (US3)
└── programacao_ons.py   # --log-level no main (US3)

tests/
├── unit/test_collector.py      # + republicação (US1)
├── unit/test_filter.py         # + linhas irregulares (US4)
├── test_conformidade.py        # NOVO: nível de log (US3), dependências (US5), figuras com seaborn (US2)
└── test_analyzer.py            # figuras: mesmos 5 arquivos

requirements.txt                # US5
```

**Structure Decision**: mudanças localizadas nos módulos existentes; um único teste novo agrupa as verificações de conformidade transversais.

## Complexity Tracking

Nenhuma violação a justificar.
