# Implementation Plan: Conferência com Outras Fontes do ONS e Programação Diária - UHE São Domingos

**Branch**: `004-conferencia-outros` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-conferencia-outros/spec.md`

## Summary

Incluir no pipeline o conjunto "Dados dos Valores da Programação Diária" do ONS (US1): obter os arquivos diários do período da base de EVT, extrair a usina (`PRUHSD`), converter os 48 patamares em programação horária, cruzar com a base de EVT e classificar as horas de usina parada com vertimento turbinável segundo a programação; levar os resultados à planilha, ao Markdown e ao PDF. Formalizar o que foi entregue sem spec em 02/10/2026: o módulo de indicadores oficiais por unidade geradora (US2) e o registro das conferências com outras fontes (US3).

A abordagem segue o padrão já usado por `src/indicadores_ons.py`: módulo próprio com download pelo catálogo CKAN e manifesto de versões, pasta bruta separada, tabelas tratadas em `data/processed/`, funções puras de análise chamadas por `src/analyzer.py`, etapa opcional no `src/main.py` e seções opcionais no relatório (ausentes quando os dados não existem).

## Technical Context

**Language/Version**: Python 3.10+ (ambiente atual: CPython 3.14 no `venv`)

**Primary Dependencies**: pandas, pyarrow (leitura dos arquivos diários compactos e gravação Parquet), openpyxl, matplotlib, reportlab — todas já em `requirements.txt`; nenhuma dependência nova

**Storage**: arquivos locais — brutos em `data/raw/programacao_diaria/` (um arquivo por dia + manifesto), tratados em `data/processed/` (CSV com `;` e planilha)

**Testing**: pytest (`tests/`), com arquivos sintéticos gravados em pastas temporárias; nenhum teste acessa a rede

**Target Platform**: Windows 11 + PowerShell (compatível com outros SOs)

**Project Type**: CLI / pipeline de dados

**Performance Goals**: leitura, cruzamento e exportação da programação em menos de 2 minutos com os arquivos já obtidos (SC-005); download inicial de ~730 arquivos de ~150 KB

**Constraints**: não alterar a base de EVT nem as saídas das specs 001 a 003 (SC-006); respeitar `--raw-dir`/`--processed-dir`; testes sem rede; todo texto do relatório gerado a partir dos dados

**Scale/Scope**: ~732 dias × 48 patamares × 1 usina (~35 mil linhas extraídas de ~1 milhão lidas); ~17 mil horas cruzadas com a base de EVT

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Situação | Observação |
|---|---|---|
| I. SDD | ⚠️ Justificado | US1 segue spec → plan → tasks → implement. US2 e US3 foram implementadas em 02/10/2026 por solicitação direta, antes da spec; esta spec as formaliza (ver Complexity Tracking). |
| II. Python exclusivo | ✅ | Toda a lógica em `src/programacao_ons.py`; nenhum script shell com regra de negócio. |
| III. Varredura exaustiva | ✅ | Todos os arquivos diários publicados no período da base de EVT são inspecionados; dias ausentes são listados, nunca presumidos. O princípio III, escrito para o conjunto de EVT, não é afetado. |
| IV. Filtragem precisa e rastreabilidade | ✅ / pendência | Extração pelo código `PRUHSD` conferido por nome e estado; `arquivo_origem` em cada linha; auditoria por arquivo. Pendência herdada: o princípio IV ainda cita a chave textual com o nome do agente, superada em 30/09/2026 (registrado na revisão da spec 001; requer emenda da constituição). |
| V. Idempotência e observabilidade | ✅ | Manifesto de versões por arquivo (reaproveita a lógica de `src/collector.py`); download atômico; logs por etapa; brutos preservados. |
| Persistência segura (.bak) | ⚠️ Justificado | Antes desta feature foi criada a cópia integral `_backup_2026-10-05_antes_spec004/` (src, tests, specs, reports, README). Arquivos de spec alterados recebem `.2026-10-05.bak`. |
| Raw × processed segregados | ✅ | `data/raw/programacao_diaria/` × `data/processed/`. |
| QA e não regressão | ✅ | Testes unitários e de integração; validação com os arquivos reais antes do relatório; suíte completa sem regressões. |

**Re-check pós-design (Phase 1)**: sem novas violações. O design reutiliza `download_resource`, `fetch_ckan_package_metadata`, o manifesto e o padrão de seções opcionais do relatório.

## Project Structure

### Documentation (this feature)

```text
specs/004-conferencia-outros/
├── spec.md
├── plan.md              # este arquivo
├── research.md          # decisões e registro das conferências (US3)
├── data-model.md        # entidades da programação e dos indicadores
├── quickstart.md        # roteiro de validação
├── contracts/
│   └── cli-contract.md  # comandos e saídas
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── config.py            # + parâmetros e caminhos da programação diária
├── collector.py         # + aceitar recursos em formato compacto (nome de arquivo preservado)
├── indicadores_ons.py   # US2 (existente, 02/10/2026)
├── programacao_ons.py   # NOVO (US1): download, extração, programação horária, classificação, eventos
├── main.py              # + etapa 4 e flags --programacao-only / --sem-programacao
├── analyzer.py          # + resumo da programação, constatação, tabelas, notas, abas
└── pdf_generator.py     # + seção "Operação verificada e programação diária do ONS"

tests/
├── test_programacao_ons.py      # NOVO
├── test_indicadores_ons.py      # existente (US2)
├── integration/test_pipeline.py # + etapa 4 simulada
└── ...

data/
├── raw/programacao_diaria/      # NOVO: PROGRAMACAO_DIARIA_AAAA_MM_DD.<formato compacto> + manifesto
└── processed/uhe_sao_domingos_ons_programacao_*.csv
```

**Structure Decision**: projeto único (CLI). A programação ganha um módulo próprio, como os indicadores, para manter `analyzer.py` responsável apenas por análise e texto.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| US2 e US3 implementadas antes da spec | Pedido direto do usuário em 02/10/2026, com prazo da fiscalização (14 a 16/10/2026) | Desfazer e refazer pelo fluxo não traria ganho; a formalização retroativa nesta spec restabelece a rastreabilidade |
| Cópia integral em pasta datada em vez de `.bak` por arquivo de código | Preserva o estado coerente do conjunto (código, testes, relatórios) e não sobrescreve os `.bak` antigos de `src/` (versão anterior à auditoria) | `.bak` arquivo a arquivo misturaria versões de datas diferentes e apagaria o histórico existente |
