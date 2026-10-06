# Implementation Plan: Fonte Explícita em Cada Figura e Tabela do Relatório - UHE São Domingos

**Branch**: `007-fontes-por-figura-tabela` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-fontes-por-figura-tabela/spec.md`

## Summary

Cada figura e tabela do relatório (PDF e Markdown) ganha uma legenda "Fonte dos dados", com os conjuntos do ONS de origem e as conferências com outra fonte feitas pelo pipeline, com o resultado. O rodapé das páginas do PDF e o cabeçalho do Markdown passam a citar a quantidade de conjuntos carregados, e não só a EVT. A planilha ganha a aba `FONTES`.

Tudo sai de um **mapa de fontes único** (`src/fontes_relatorio.py`), consumido pelo `analyzer.py` (Markdown e planilha) e pelo `pdf_generator.py` (legendas e rodapé). Os textos são gerados a partir dos resultados já calculados e das datas de obtenção dos manifestos. Nenhum dado é baixado ou reprocessado. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (venv do projeto; compatível com 3.10+)

**Primary Dependencies**: as já usadas (pandas, openpyxl, reportlab). **Nenhuma dependência nova.**

**Storage**: leitura dos manifestos `_manifesto_ons.json` das pastas brutas, só para as datas de obtenção. Saídas só em `reports/`, que é dispensado de `.bak`; nada novo em `data/processed/`.

**Testing**: pytest sem rede. Testes de cobertura do mapa, de geração dos textos a partir de `ResultadosAnalise` sintéticos, de contagem de legendas no PDF e de não regressão do relatório sem bases novas.

**Target Platform**: Windows 11 + PowerShell

**Project Type**: CLI / pipeline de dados (camada de relatório)

**Performance Goals**: geração do relatório sem acréscimo perceptível (hoje cerca de 22 s).

**Constraints**:
- Figuras inalteradas: a legenda fica fora da imagem (FR-013).
- Números, constatações, seções, tabelas e abas existentes inalterados (FR-012).
- Só as conferências refeitas pelo pipeline (decisão A do usuário).
- **Prazo**: até 13/10/2026.

**Scale/Scope**:
- 10 conjuntos do ONS e os parâmetros do projeto;
- 6 conferências;
- 8 figuras, cerca de 22 tabelas no Markdown e cerca de 28 tabelas e blocos no PDF;
- 56 abas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / requisito (v1.2.0) | Situação | Observação |
|---|---|---|
| I. SDD | ✅ | spec 007 → plan → tasks → implement |
| II. Python exclusivo | ✅ | módulo novo em Python, com docstrings e tipos |
| III. Varredura exaustiva | ✅ não se aplica | não há coleta nova |
| IV. Rastreabilidade | ✅ | a feature reforça o princípio: origem e conferência de cada figura, tabela e aba |
| V. Idempotência e observabilidade | ✅ | relatório determinístico para as mesmas bases; aviso no log se uma figura ou tabela não tiver entrada no mapa |
| VI. Escopo exclusivo da usina | ✅ | identificadores da constituição em cada legenda |
| Req. 1 — dependências usadas | ✅ | nenhuma nova |
| Req. 3 — `.bak` | ✅ | cópia datada antes de alterar código, testes e documentos (3b); `reports/` dispensado |
| Req. 5 — seaborn | ✅ | nenhum gráfico novo nem alterado |
| Garantia de qualidade | ✅ | não regressão contra o relatório atual; teste de cobertura do mapa |

**Re-check pós-design**: sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/007-fontes-por-figura-tabela/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── relatorio-fontes-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── fontes_relatorio.py   # NOVO: catálogo dos conjuntos, conferências, mapa de fontes, textos de legenda, rodapé e aba FONTES
├── analyzer.py           # res.fontes (datas e conferências); legenda após cada tabela e figura no Markdown; cabeçalho; aba FONTES; recálculo TEIFa/TEIP em res.ons
└── pdf_generator.py      # legenda após cada tabela, bloco e figura; rodapé genérico; contagem de legendas emitidas

tests/
├── test_fontes_relatorio.py      # NOVO: cobertura do mapa, textos gerados dos resultados, ausências, rodapé
├── test_relatorio_complementar.py  # legendas no Markdown e aba FONTES com as bases novas
└── test_pdf_generator.py         # toda tabela e figura do PDF com legenda; rodapé com N conjuntos
```

**Structure Decision**: módulo único e declarativo para o mapa (FR-008), sem lógica de layout. O `analyzer` e o `pdf_generator` só pedem o texto pela chave da figura ou tabela.

### Sequência de entrega

| Data | Entrega |
|---|---|
| 06/10 | Cópia datada; módulo do mapa com testes |
| 07/10 | Legendas no Markdown e aba FONTES |
| 08/10 | Legendas e rodapé no PDF |
| 09/10 | Relatório regenerado, não regressão e conferência das legendas |

## Complexity Tracking

Nenhuma violação a justificar.
