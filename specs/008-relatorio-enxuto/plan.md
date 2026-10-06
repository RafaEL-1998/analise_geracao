# Implementation Plan: Relatório Mais Enxuto, com Sumário na Capa e Constatações em Cada Seção - UHE São Domingos

**Branch**: `008-relatorio-enxuto` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-relatorio-enxuto/spec.md`

## Summary

O relatório troca a lista inicial de constatações por uma capa com dados básicos, percentuais, data de geração e **sumário**. Cada constatação passa a aparecer uma vez só, no início da sua seção. O rodapé fica só com a numeração e as notas de fonte das bases novas perdem a parte já dada pelas legendas da spec 007. O Markdown passa a ter a mesma estrutura do PDF.

Tudo sai de uma **estrutura única do relatório** (`src/estrutura_relatorio.py`), com a ordem das seções, a condição de cada uma e as constatações que ela abre. O PDF e o Markdown a percorrem com o mesmo resultado. Nada de dados muda: a planilha fica igual. Decisões em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (venv do projeto; compatível com 3.10+)

**Primary Dependencies**: as já usadas. O sumário do PDF usa o `TableOfContents` do reportlab 5.0.1, já instalado. **Nenhuma dependência nova.**

**Storage**: só `reports/` (dispensado de `.bak`); `data/processed/` e a planilha não mudam.

**Testing**: pytest sem rede, com os resultados sintéticos já usados nos testes do relatório (`tests/test_relatorio_complementar.py`, `tests/test_pdf_generator.py`) e testes novos da estrutura.

**Target Platform**: Windows 11 + PowerShell

**Project Type**: CLI / pipeline de dados (camada de relatório)

**Performance Goals**: o PDF passa a ser montado em duas passagens, por causa da página de cada seção no sumário; acréscimo de poucos segundos aos cerca de 22 s atuais.

**Constraints**:
- Números, textos das constatações, tabelas, figuras, legendas de fonte e planilha inalterados (FR-012).
- Gráficos inalterados; nenhum gráfico novo (constituição, Requisito Técnico 5).
- **Prazo**: até 13/10/2026.

**Scale/Scope**:
- 17 seções no PDF com todas as bases;
- 17 a 19 constatações, conforme as divergências;
- 8 figuras;
- cerca de 30 tabelas e blocos;
- 2 saídas (PDF e Markdown).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / requisito (v1.2.0) | Situação | Observação |
|---|---|---|
| I. SDD | ✅ | spec 008 → plan → tasks → implement; revisa as FR-009 e FR-010 da spec 007, com registro no histórico dela |
| II. Python exclusivo | ✅ | módulo novo em Python, com docstrings e tipos |
| III. Varredura exaustiva | ✅ não se aplica | sem coleta |
| IV. Rastreabilidade | ✅ | legendas de fonte e conferência mantidas em 100% das figuras e tabelas; relação completa nas Notas metodológicas |
| V. Observabilidade | ✅ | aviso no log se uma constatação não tiver seção, ou se o PDF e o Markdown divergirem na estrutura |
| VI. Escopo da usina | ✅ | sem mudança |
| Req. 3 — `.bak` | ✅ | cópia datada antes de alterar código, testes e documentos (3b); `reports/` dispensado |
| Req. 5 — seaborn | ✅ | figuras inalteradas |
| Garantia de qualidade | ✅ | não regressão: cada tabela, constatação e parágrafo do relatório anterior presente no novo, e a planilha idêntica |

**Re-check pós-design**: sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/008-relatorio-enxuto/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── estrutura-relatorio-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── estrutura_relatorio.py  # NOVO: seções em ordem (chave, título, condição), constatação → seção, sumário
├── analyzer.py             # Markdown reescrito pela estrutura; legendas das figuras compartilhadas com o PDF; notas sem a parte de fonte (FR-013)
└── pdf_generator.py        # capa com data e sumário (índice com página); constatações no início de cada seção; rodapé só com a numeração; tabelas que faltavam (FR-014)

tests/
├── test_estrutura_relatorio.py    # NOVO: mapa completo, cada constatação uma vez, PDF e Markdown com as mesmas seções
├── test_relatorio_complementar.py # ajustes: cabeçalho sem "**Fontes**:", notas sem a parte de fonte
└── test_pdf_generator.py          # rodapé só com a numeração; sumário com as páginas certas
```

**Structure Decision**:
- A estrutura (ordem, títulos e mapa das constatações) é declarada uma vez e consumida pelos dois geradores. Cada gerador mantém a sua função por seção, como hoje, chamada pela chave da seção.
- As legendas descritivas das figuras, hoje escritas dentro do `pdf_generator`, passam para o `analyzer` e são usadas pelos dois.

### Sequência de entrega

| Data | Entrega |
|---|---|
| 06–07/10 | Cópia datada; estrutura do relatório e testes |
| 07–08/10 | PDF: capa, sumário, constatações nas seções, rodapé |
| 08–09/10 | Markdown com a estrutura do PDF; notas de fonte (FR-013) |
| 09/10 | Relatório regenerado e não regressão |

## Complexity Tracking

Nenhuma violação a justificar.
