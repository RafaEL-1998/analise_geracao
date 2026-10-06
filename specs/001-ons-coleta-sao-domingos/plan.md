# Implementation Plan: Coleta e Filtragem de Dados ONS - UHE São Domingos

**Branch**: `001-ons-coleta-sao-domingos` | **Date**: 2026-09-30 (revisado em 2026-10-05) | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-ons-coleta-sao-domingos/spec.md`

**Nota de revisão (2026-10-05)**: plano atualizado para descrever o sistema como implementado após a auditoria de 30/09/2026. A versão anterior está em `plan.md.2026-10-05.bak`; as mudanças de requisito estão no "Histórico de revisões" de [spec.md](spec.md).

## Summary

O objetivo desta funcionalidade é coletar automaticamente a totalidade dos arquivos CSV de "Energia Vertida Turbinável" disponíveis no Portal de Dados Abertos do ONS (um por ano de 2015 a 2023 e um por mês a partir de 01/2024), extrair por varredura exaustiva linha a linha os registros da UHE São Domingos, identificada por `cod_usina` = 153 conferido pelo nome do reservatório (`SAO DOMINGOS`, sem acentos e em maiúsculas), e consolidá-los em uma base cronológica única, deduplicada por (`cod_usina`, `din_instante`), com rastreabilidade do arquivo de origem e relatório de auditoria de 100% dos arquivos inspecionados.

A abordagem técnica adota integração direta com a API CKAN do ONS (`package_show`), download em streaming com cache sensível às revisões do ONS (manifesto `data/raw/_manifesto_ons.json` com `last_modified` e tamanho publicados), gravação atômica (`.part`) e retentativas com recuo exponencial em `data/raw/`, leitura em streaming (`csv` com `;`, UTF-8 com releitura em Latin-1) e consolidação final em `data/processed/`.

## Technical Context

**Language/Version**: Python 3.10+ (ambiente `venv` com Python 3.14).

**Primary Dependencies**: apenas biblioteca padrão nos módulos desta feature (`urllib.request`, `csv`, `json`, `unicodedata`, `dataclasses`, `pathlib`, `logging`, `argparse`); `pytest` para os testes. `requests` consta do `requirements.txt` mas não é usado pelo código desta feature; `pandas` só é importado em `src/main.py` para a etapa 3 (indicadores oficiais, escopo de `specs/004-conferencia-outros`).

**Storage**: Arquivos locais em disco:
- `data/raw/`: CSVs originais do ONS (42 arquivos, cerca de 2,2 GB em 30/09/2026) e `_manifesto_ons.json` (versão publicada de cada arquivo). A subpasta `data/raw/indicadores_ons/` pertence à spec 004 e não é varrida, porque a busca de CSVs não é recursiva.
- `data/processed/`: base consolidada `uhe_sao_domingos_energia_vertida_consolidado.csv` e relatório `relatorio_auditoria_varredura.csv`.

**Testing**: `pytest` com 15 testes desta feature: 6 em `tests/unit/test_collector.py` (catálogo, manifesto e cache), 7 em `tests/unit/test_filter.py` (extração, Latin-1, deduplicação e ordenação), 1 em `tests/unit/test_audit.py` (relatório de auditoria) e 1 em `tests/integration/test_pipeline.py` (ponta a ponta com download simulado). Todos aprovados na verificação de 05/10/2026.

**Target Platform**: Windows 10/11 com PowerShell (ambiente virtual `venv`).

**Project Type**: CLI tool / Pipeline de Engenharia de Dados em Python.

**Performance Goals**:
- Download em streaming com buffer de 1 MB, timeout de 60 s, 3 tentativas por arquivo e espera de 2 s e 4 s entre elas.
- Varredura e filtragem local de 100% dos arquivos em menos de 3 minutos (observado: cerca de 45 s para 42 arquivos e cerca de 15 milhões de linhas em 30/09/2026).
- Leitura linha a linha, sem carregar os arquivos na memória; apenas os registros extraídos (cerca de 71 mil) ficam em memória até a consolidação.

**Constraints**:
- Não pular nenhum exercício ou ano histórico (2015 a 2017 são inspecionados mesmo sem registros da usina).
- Preservar os arquivos brutos sem edição; quando o ONS publica nova versão, o arquivo é substituído integralmente e a versão anterior não é guardada (ver Complexity Tracking).
- Identificação da usina independente do nome do agente (CGT ELETROSUL até 02/2026, AXIA SUL a partir de 03/2026).
- Estrita compatibilidade com comandos do PowerShell (sem pipes Unix ou dependências de bash).

**Scale/Scope**: 42 arquivos CSV (9 anuais e 33 mensais, cerca de 2,2 GB e 15 milhões de linhas); base filtrada com 70.895 registros horários (28/08/2018 00h a 28/09/2026 23h).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

*Reavaliado em 05/10/2026 contra a Constituição v1.0.0, com o código em vigor.*

| Princípio Constitucional | Status | Avaliação de Conformidade |
| :--- | :---: | :--- |
| **I. Spec-Driven Development (SDD)** | **PASS com ressalva** | Os artefatos foram elaborados antes do código em 30/09/2026, mas as correções da auditoria (30/09/2026) e os ajustes de 02/10/2026 foram feitos por prompt, sem atualização prévia da spec. Esta revisão regulariza a documentação retroativamente. |
| **II. Python Exclusivo & Código Limpo** | **PASS** | Pipeline e testes em Python 3, no pacote modular `src/`, com dataclasses tipadas e docstrings. |
| **III. Varredura Exaustiva & Integridade Temporal** | **PASS** | A API CKAN é consultada a cada execução e 100% dos CSVs publicados (42 em 30/09/2026) são sincronizados e varridos, sem exclusões por ano; o nome `SAO DOMINGOS` é conferido em todas as linhas de todos os arquivos. |
| **IV. Filtragem Precisa & Rastreabilidade** | **DIVERGENTE (justificado)** | A extração usa `cod_usina` 153 + nome do reservatório, e não a chave textual `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"` exigida pelo princípio (ver Complexity Tracking). A rastreabilidade é atendida com `arquivo_origem` e `tipo_match` por linha e com o manifesto e o relatório de auditoria por arquivo. Linhas com campos insuficientes são descartadas sem log (pendência). |
| **V. Idempotência & Observabilidade** | **PASS com ressalva** | Reexecuções não duplicam registros e não rebaixam arquivos atuais; os logs informam arquivo, linhas lidas, extraídas e divergentes. Ressalvas: arquivo bruto revisado pelo ONS é substituído sem guardar a versão anterior; `--log-level` só afeta o logger `main`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ons-coleta-sao-domingos/
├── spec.md                  # Especificação dos requisitos de negócio (com Histórico de revisões)
├── plan.md                  # Este plano de implementação técnica
├── research.md              # Decisões arquiteturais, justificativas e validações (Fase 0)
├── data-model.md            # Esquema de entidades e dicionário de dados (Fase 1)
├── quickstart.md            # Guia prático de execução e validação (Fase 1)
├── contracts/
│   └── cli-contract.md      # Contrato de linha de comando e artefatos de saída
├── checklists/
│   └── requirements.md      # Checklist de validação de requisitos
├── tasks.md                 # Lista de tarefas acionáveis (Fase 2 - /speckit-tasks)
└── *.2026-10-05.bak         # Cópias anteriores à revisão de 05/10/2026 (e plan.md.bak, tasks.md.bak de 30/09)
```

### Source Code (repository root)

```text
data/
├── raw/                     # CSVs originais do ONS (.gitignored)
│   ├── ENERGIA_VERTIDA_TURBINAVEL_AAAA.csv      # 2015 a 2023
│   ├── ENERGIA_VERTIDA_TURBINAVEL_AAAA_MM.csv   # 01/2024 em diante
│   └── _manifesto_ons.json  # Versão publicada de cada arquivo (last_modified e tamanho)
└── processed/               # Base consolidada e relatório de auditoria

src/
├── __init__.py              # Marcador de pacote Python
├── config.py                # Caminhos, URL do CKAN, COD_USINA_ONS = 153, NOME_RESERVATORIO_REFERENCIA, rede
├── models.py                # Dataclasses RecursoONS, RegistroEnergiaVertida, AuditoriaArquivo
├── logger.py                # Logger para a saída padrão e exceções (ONSError, DownloadError, FilterError)
├── collector.py             # Descoberta via CKAN, manifesto de versões e download atômico em streaming
├── filter.py                # Leitura em streaming e extração por cod_usina + nome do reservatório
├── consolidator.py          # Deduplicação, ordenação e gravação da base e do relatório de auditoria
└── main.py                  # Ponto de entrada CLI (etapas 1 e 2; a etapa 3 é da spec 004)

tests/
├── __init__.py
├── conftest.py              # Fixtures, linhas sintéticas do ONS e mock da resposta CKAN
├── unit/
│   ├── test_collector.py    # Catálogo, manifesto, cache e novo download de arquivo revisado
│   ├── test_filter.py       # Extração por código e nome, Latin-1, deduplicação e ordenação
│   └── test_audit.py        # Colunas e conteúdo do relatório de auditoria
└── integration/
    └── test_pipeline.py     # Pipeline ponta a ponta em diretórios temporários (download simulado)

requirements.txt             # Dependências Python do projeto
.gitignore                   # Ignora data/raw/*, caches, venv/ e *.bak
```

Os demais módulos de `src/` (`processor.py`, `validator.py`, `analyzer.py`, `pdf_generator.py`, `formatacao.py` e `indicadores_ons.py`) pertencem às specs 002, 003 e 004.

**Structure Decision**: A organização em pacote único `src/` com responsabilidades segregadas (`collector`, `filter`, `consolidator`, `main`, apoiados por `config`, `models` e `logger`) atende o escopo de um pipeline de engenharia de dados e permite testar cada fase isoladamente.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Princípio IV: extração por `cod_usina` 153 + nome do reservatório no lugar da chave textual `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"` | A chave inclui o nome do agente, que mudou de CGT ELETROSUL para AXIA SUL em 03/2026; aplicada estritamente, deixaria de fora 65.807 dos 70.895 registros (28/08/2018 a 28/02/2026). | Chave textual + busca secundária (versão original): depende do nome do agente e extraía por nome isolado, sujeito a homônimos. Só o código: não revela mudança de cadastro. Só o nome: sujeito a homônimos. |

**Pendências sem justificativa (a corrigir ou a levar à emenda da constituição)**:

- Princípio IV: a constituição ainda cita a chave textual; requer emenda (registrado no Histórico de revisões de [spec.md](spec.md)).
- Princípio IV: linhas com menos campos que o necessário são descartadas sem registro em log (`src/filter.py`).
- Princípio V: o arquivo bruto revisado pelo ONS substitui o anterior sem preservá-lo (`src/collector.py`).
- Princípio V: `--log-level` não se propaga aos loggers `collector`, `filter` e `consolidator` (`src/main.py`).
