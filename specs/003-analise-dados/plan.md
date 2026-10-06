# Implementation Plan: Análise Estatística, Indicadores Operacionais, Visualização Gráfica e Relatório - UHE São Domingos

**Branch**: `003-analise-dados` | **Date**: 2026-09-30 (revisado em 2026-10-05) | **Spec**: [specs/003-analise-dados/spec.md](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/003-analise-dados/spec.md)

**Input**: Feature specification from `specs/003-analise-dados/spec.md`

> **Revisão retroativa (2026-10-05)**: este plano descreve a implementação atual. O plano anterior (seaborn, FID/FIT, parecer de desempenho, figuras com outros nomes e módulos `scraper.py`/`extractor.py` que não existem) está preservado em `plan.md.2026-10-05.bak`. As mudanças estão registradas no Histórico de revisões da spec e na fase "Revisão pós-auditoria" de `tasks.md`.

---

## Summary

A feature extrai indicadores e constatações da base tratada da UHE São Domingos (na versão atual, 70.895 registros horários de 28/08/2018 00h a 28/09/2026 23h) e entrega:
1. Perfil estatístico anual das 10 grandezas `val_*` e extremos do período com data e hora, calculados sem os registros sinalizados com anomalia (R6 a R9).
2. Indicadores anuais e globais de disponibilidade declarada (em % da potência instalada, comparada com a disponibilidade de referência da garantia física, (1 − IP) × (1 − TEIF) = 90,97%), fator de capacidade, razão com a garantia física (36,4 MWmed), EVT e suas parcelas, eventos de usina parada com EVT e de indisponibilidade total, distribuições da EVT (mensal, por mês do ano, por faixa de geração, por hora), horas com geração zero por mês e detecção da mudança de classificação do vertimento contínuo pelo ONS (dez/2022).
3. Doze constatações em texto montadas a partir dos resultados, sem parecer categórico nem atribuição de causa, e notas metodológicas.
4. Cinco figuras em matplotlib a 300 DPI.
5. Relatório em PDF (A4 paisagem, reportlab) e em Markdown, planilha Excel com todas as tabelas e CSV com os indicadores anuais, todos montados a partir do mesmo objeto `ResultadosAnalise`, sem números fixos.

O relatório aceita seções e constatações opcionais definidas na spec 004 (`specs/004-conferencia-outros`); sem esses dados, sai com 12 constatações.

---

## Technical Context

**Language/Version**: Python 3.10+ (ambiente ativo: Python 3.14.6 no ambiente virtual `.\venv`)

**Primary Dependencies** (versões instaladas no `.\venv` em 05/10/2026):
- `pandas` 3.0.6 (agregações, eventos, tabelas dinâmicas) e `numpy` 2.5.3 (classificação por faixas e detecção da mudança de classificação; dependência transitiva do pandas, não listada no `requirements.txt`)
- `pyarrow` 25.0.1 (leitura do Parquet)
- `openpyxl` 3.1.5 (planilha Excel)
- `matplotlib` 3.11.2 (as 5 figuras, backend `Agg`, fonte Arial ou DejaVu Sans)
- `reportlab` 5.0.1 (PDF A4 paisagem, fontes TrueType Arial ou DejaVu Sans)
- `pytest` 9.1.1 (testes)
- `seaborn` 0.13.2 continua no `requirements.txt` (`seaborn>=0.13.0`), mas nenhum módulo o importa desde a revisão de 30/09/2026.
- Módulos internos: `src/config.py` (parâmetros e limiares), `src/formatacao.py` (números, datas e listas no padrão brasileiro), `src/validator.py` (sinalização R6 a R9, regras R1 a R9 e faixa de produtividade, da Feature 002) e os módulos da spec 004 que fornecem os dados opcionais (`src/indicadores_ons.py` e, em desenvolvimento, `src/programacao_ons.py`).

**Storage**:
- Entrada: `data/processed/uhe_sao_domingos_energia_vertida_tratado.parquet` (ou `.xlsx`; `.csv` com separador `;` quando informado em `--input-file`). Opcionais: `data/processed/relatorio_auditoria_varredura.csv` e `data/raw/_manifesto_ons.json` (Feature 001), para a cobertura.
- Saídas:
  - `reports/relatorio_analise_estatistica.pdf`
  - `reports/relatorio_analise_estatistica.md`
  - `reports/perfil_estatistico_anual.xlsx` (19 abas, mais as abas da spec 004 quando há esses dados)
  - `reports/perfil_estatistico_anual.csv` (indicadores anuais, separador `;`)
  - `reports/figures/01_serie_temporal_disponibilidade_geracao_evt.png`
  - `reports/figures/02_evt_mensal.png`
  - `reports/figures/03_perfil_horario_geracao_evt.png`
  - `reports/figures/04_disponibilidade_geracao_anual.png`
  - `reports/figures/05_vazoes_defluentes_anuais.png`

**Testing**:
- `tests/test_analyzer.py` (10 testes): eventos quebrados por lacunas, cobertura e eventos, mudança de classificação, indicadores anuais, EVT por faixa somando o total, extremos sem registros sinalizados, texto do relatório sem as afirmações removidas e com a tabela anual calculada, geração das 5 figuras, horas com geração zero por mês e um teste de integração com a base real (pulado se a base não existir; confere totais e 12 constatações).
- `tests/test_pdf_generator.py` (2 testes): PDF válido com figuras e sem figuras.
- Série sintética `df_sintetico` em `tests/conftest.py` (nov/2023 a fev/2024, com 30 h de indisponibilidade total, 5 h de parada com EVT, mudança de classificação em jan/2024 e um registro anômalo).
- `tests/test_indicadores_ons.py` (spec 004) também cobre o relatório sem os dados opcionais (12 constatações e numeração das seções).

**Target Platform**: Windows 10/11 com terminal PowerShell.

**Project Type**: Módulo analítico com CLI (`python -m src.analyzer`); `python -m src.pdf_generator` regenera só o PDF a partir da base tratada e das figuras existentes.

**Performance Goals**:
- Metas originais: perfil estatístico e extremos em menos de 2 segundos; 5 figuras a 300 DPI em menos de 25 segundos; total abaixo de 30 segundos (SC-004).
- Não foram medidas novamente após 30/09/2026; a execução passou a gerar também o PDF.

**Constraints**:
- Parâmetros da usina fixados em `src/config.py` com a fonte: RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3 (48 MW, 2 × 24 MW, Kaplan de eixo vertical, 2 × 81,5 m³/s, IP 6,861%, TEIF 2,333%, queda, perda, rendimento, vazão remanescente); garantia física de 36,4 MWmed (ANEEL, valor vigente consultado em 02/10/2026).
- Nenhum número, data ou conclusão fixo nos textos; todo texto de relatório é montado a partir de `ResultadosAnalise`.
- Números no padrão brasileiro; títulos, eixos rotulados e unidades explícitas nas figuras.
- Consumo de memória inferior a 600 MB (meta original, não medida).
- Execução nativa em PowerShell no Windows.

**Scale/Scope**:
- 70.895 registros horários, 10 grandezas, 9 anos (2018 e 2026 parciais), 5 figuras, 19 abas de planilha, 12 constatações (mais as opcionais da spec 004).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reavaliado em 2026-10-05 sobre a implementação atual.

| Princípio Constitucional | Requisito do Projeto | Status | Avaliação |
| :--- | :--- | :---: | :--- |
| **I. Spec-Driven Development (SDD)** | Especificação aprovada antes do código; mudanças de lógica exigem atualização prévia da spec. | **VIOLADO (regularizado)** | As correções de 30/09/2026 e os ajustes de 02/10/2026 foram feitos por prompt, sem atualizar a spec. Esta revisão retroativa atualiza spec, plano, pesquisa, modelo de dados, contrato, quickstart e tarefas. Ver Complexity Tracking. |
| **II. Ecossistema Python Exclusivo & Código Limpo** | 100% Python, tipagem explícita, docstrings, módulos coesos. | **PASS (com ressalva)** | Tudo em Python, com anotações de tipo e docstrings; formatação em `src/formatacao.py` e PDF em `src/pdf_generator.py`. Ressalva: `src/analyzer.py` tem cerca de 2.170 linhas e reúne cálculo, constatações, figuras, exportação, Markdown e CLI. |
| **III. Varredura Exaustiva & Integridade Temporal** | Considerar 100% do histórico, sem descartar registros. | **PASS** | Todos os registros entram nos totais, inclusive os sinalizados; anos parciais sinalizados; horas ausentes e duplicadas informadas; lacunas de horário encerram eventos. |
| **IV. Filtragem Precisa, Rastreabilidade & Validação Semântica** | Rastreabilidade dos eventos e coerência das grandezas. | **PASS** | Extremos e eventos com `din_instante`; registros R6 a R9 sinalizados e listados; resultado das regras R1 a R9 no PDF e na planilha; parâmetros com origem; resumo da auditoria da varredura e do manifesto de versões no PDF. |
| **V. Idempotência, Resiliência & Observabilidade** | Geração determinística e sem corrupção; logs; exceções explícitas. | **PASS** | Cada execução regrava as mesmas saídas a partir da mesma base (o rodapé do PDF registra a data e a hora de geração); logs com nível configurável; falha em qualquer etapa, inclusive no PDF, retorna código 1. |
| **Diretrizes de Ambiente (Windows & PowerShell)** | PowerShell, `.\venv`, backup `.bak` antes de escrever e validação da gravação. | **PARCIAL** | PowerShell e `.\venv` atendidos. O analisador regrava `reports/` e `reports/figures/` sem criar `.bak`; as cópias de segurança são feitas manualmente em pastas datadas (`reports/_versao_anterior_2026-09-30/`, `_backup_2026-10-02_relatorio_aprovado/`, `_backup_2026-10-05_antes_spec004/`). A gravação é registrada em log (o PDF com o tamanho em bytes), sem verificação adicional. |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-analise-dados/
├── spec.md                     # Especificação funcional (revisada em 2026-10-05, com Histórico de revisões)
├── plan.md                     # Este arquivo
├── research.md                 # Decisões metodológicas, definições dos indicadores e das figuras
├── data-model.md               # Estruturas de ResultadosAnalise, abas da planilha e catálogo de figuras
├── quickstart.md               # Guia de execução e validação
├── contracts/
│   └── cli-contract.md         # Contrato da CLI (parâmetros, saídas e exit codes)
├── checklists/
│   └── requirements.md         # Checklist de qualidade da especificação
├── tasks.md                    # Tarefas, inclusive a fase de revisão pós-auditoria
└── *.2026-10-05.bak            # Cópias dos arquivos antes da revisão de 2026-10-05 (e *.bak anteriores)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py                   # Caminhos, parâmetros da usina com fonte, limiares de análise e de validação
├── formatacao.py               # Números, datas, meses e listas no padrão brasileiro
├── validator.py                # Regras R1 a R9 e sinalização de anomalias (Feature 002), usado pela análise
├── analyzer.py                 # ResultadosAnalise, indicadores, eventos, constatações, notas, figuras, planilha, Markdown e CLI
├── pdf_generator.py            # PDFReportGenerator: PDF A4 paisagem montado a partir de ResultadosAnalise
├── indicadores_ons.py          # Indicadores oficiais do ONS por unidade geradora (spec 004; opcional para a análise)
├── programacao_ons.py          # Programação diária do ONS (spec 004; em desenvolvimento em 05/10/2026; opcional)
├── collector.py, filter.py, consolidator.py, models.py, logger.py, main.py   # Coleta e extração (Feature 001)
└── processor.py                # Tipagem e exportação multi-formato (Feature 002)

tests/
├── conftest.py                 # Série sintética df_sintetico e fixtures das Features 001 e 002
├── test_analyzer.py            # Testes da análise, do Markdown e das figuras
├── test_pdf_generator.py       # Testes do PDF
├── test_indicadores_ons.py     # Spec 004 (inclui o relatório sem os dados opcionais)
├── test_processor.py, test_validator.py                                      # Feature 002
├── unit/                       # test_audit.py, test_collector.py, test_filter.py (Feature 001)
└── integration/                # test_pipeline.py (Feature 001)

reports/
├── relatorio_analise_estatistica.pdf   # Relatório A4 paisagem
├── relatorio_analise_estatistica.md    # Mesmo conteúdo em Markdown
├── perfil_estatistico_anual.xlsx       # Todas as tabelas calculadas
├── perfil_estatistico_anual.csv        # Indicadores anuais
├── figures/                            # 5 figuras (300 DPI)
│   ├── 01_serie_temporal_disponibilidade_geracao_evt.png
│   ├── 02_evt_mensal.png
│   ├── 03_perfil_horario_geracao_evt.png
│   ├── 04_disponibilidade_geracao_anual.png
│   └── 05_vazoes_defluentes_anuais.png
└── _versao_anterior_2026-09-30/        # Versão anterior à auditoria, com informações incorretas (ver LEIA-ME.txt)
```

**Structure Decision**:
O cálculo fica em `src/analyzer.py`, que produz um único `ResultadosAnalise`; planilha, Markdown e PDF são montados a partir dele, e as tabelas usadas nos dois relatórios (indicadores anuais, horas com geração zero) são formatadas por funções compartilhadas (`linhas_tabela_anual`, `linhas_tabela_geracao_zero`), para que o Markdown e o PDF mostrem os mesmos valores. O PDF fica em `src/pdf_generator.py` e a formatação pt-BR em `src/formatacao.py`. Os artefatos ficam em `reports/`.

---

## Complexity Tracking

| Violação | Por que ocorreu | Alternativa mais simples rejeitada porque |
| :--- | :--- | :--- |
| Princípio I (SDD): correções de 30/09/2026 e ajustes de 02/10/2026 implementados por prompt, sem atualização prévia da spec. | A auditoria de 30/09/2026 encontrou números e conclusões falsos fixos no relatório que apoia a fiscalização de 14 a 16/10/2026; os ajustes de 02/10/2026 (garantia física, horas com geração zero, numeração automática das seções) também foram pedidos diretamente por prompt. | Não registrado na época. A documentação foi atualizada retroativamente em 2026-10-05 (esta revisão). |
| Diretriz de persistência segura: o analisador regrava os relatórios e as figuras sem criar `.bak`. | O pipeline regenera todos os artefatos a cada execução. | Não há backup automático implementado; as versões relevantes são preservadas manualmente em pastas datadas antes de cada alteração. |
