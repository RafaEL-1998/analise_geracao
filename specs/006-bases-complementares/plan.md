# Implementation Plan: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança dos Dados Processados - UHE São Domingos

**Branch**: `006-bases-complementares` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-bases-complementares/spec.md`

## Summary

A feature fecha duas lacunas da constituição 1.2.0 e inclui no pipeline quatro bases abertas do ONS.

**Lacunas da constituição 1.2.0**:
- **US1**: toda gravação em `data/processed/` passa por um módulo único de persistência. Ele grava num temporário, confere, compara com o conteúdo atual, guarda `<nome>.bak` e faz a troca atômica, restaurando a versão anterior em caso de falha.
- **US2**: a cada coleta são obtidos os dicionários de dados (PDF e JSON) dos 10 conjuntos, com versões anteriores preservadas quando o conteúdo muda.

**Bases novas**, no período da base EVT local e sem baixá-la de novo:
- **US3**: disponibilidade operacional e sincronizada.
- **US4**: dados hidrológicos (afluência, níveis, volume útil), alinhados da convenção de fim de hora.
- **US5**: geração por usina (conferência).
- **US6**: cadastro da usina.

As três séries horárias compartilham um motor comum: período pelo nome do arquivo, formato por mês, auditoria, duplicatas e ausências. As análises cruzam as bases novas com a base EVT, a programação diária e os parâmetros TEIFa/TEIP. O resultado vai para seções, constatações, abas e três figuras em seaborn, sem alterar os números existentes do relatório. A decisão de cada ponto está em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14 (venv do projeto; compatível com 3.10+)

**Primary Dependencies**:
- Já usadas: pandas 3.0, numpy 2.5, pyarrow 25, openpyxl 3.1 (propriedades personalizadas para a assinatura das planilhas), matplotlib 3.11, seaborn 0.13.2 e reportlab 5.0; pytest 9 nos testes.
- Biblioteca padrão: `urllib`, `hashlib`, `zipfile`, `shutil`, `concurrent.futures`.
- **Nenhuma dependência nova.**

**Storage**:
- Dados brutos em pastas próprias por conjunto: `data/raw/disponibilidade_usina/`, `dados_hidrologicos_ho/`, `geracao_usina_2/`, `modalidade_usina/`. Cada uma tem `_manifesto_ons.json` e `_versoes_anteriores/`.
- Dicionários em `<pasta bruta>/_dicionarios/`.
- Saídas tratadas em `data/processed/`, com `<nome>.bak`. A lista está no [data-model.md](data-model.md), seção 9.

**Testing**: pytest com arquivos sintéticos em pastas temporárias, sem rede (download e catálogo simulados com `unittest.mock`), e integração por simulação das etapas, como em `tests/integration/test_pipeline.py`.

**Target Platform**: Windows 11 + PowerShell

**Project Type**: CLI / pipeline de dados

**Performance Goals**:
- Etapas novas em menos de 10 min sem rede (SC-009).
- A persistência acrescenta segundos às etapas existentes: a assinatura evita reler a planilha tratada, cujo custo medido é de 18 s de leitura e 34 s de gravação.

**Constraints**:
- Não baixar de novo a base EVT.
- Período e identificadores conforme a constituição 1.2.0.
- Gráficos só em seaborn, com o tema e a paleta centrais; carregar a skill dataviz antes do código de gráfico.
- Não regressão dos números existentes (SC-008).
- **Prazo**: P1 (US1 a US4) até 13/10/2026.

**Scale/Scope**:
- 4 conjuntos novos:
  - disponibilidade: 53 CSV e cerca de 45 Parquet no período;
  - hidrologia: cerca de 98 Parquet;
  - geração: 4 Parquet anuais e cerca de 57 mensais;
  - cadastro: 1 CSV.
- 20 dicionários.
- 17 arquivos existentes em `data/processed/` passam a usar a persistência, mais 12 novos.
- Cerca de 71 mil horas por série.
- Primeiro download de cerca de 1,9 GB.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / requisito (v1.2.0) | Situação | Observação |
|---|---|---|
| I. SDD | ✅ | spec → plan → tasks → implement; a constituição foi emendada (1.2.0) antes do plano |
| II. Python exclusivo | ✅ | nenhum script shell com regra de negócio |
| III. Varredura exaustiva | ✅ | todos os arquivos que se sobrepõem ao período; formato escolhido por mês, para não deduzir ausência de formato incompleto; meses e horas ausentes listados, sem interpolação |
| IV. Filtragem e rastreabilidade | ✅ | identificador e conferência por conjunto (tabela da 1.2.0); identificação parcial contada; `arquivo_origem` por linha; manifesto por pasta; valores inválidos em log e auditoria; dicionários obtidos a cada coleta (US2) |
| V. Idempotência e observabilidade | ✅ | cache por versão publicada; versões anteriores preservadas; `INALTERADO` sem regravação; nível de log também nos loggers novos |
| VI. Escopo exclusivo da usina | ✅ | homônimos excluídos pela conferência (mais de 20 no cadastro); o agregado do SIN fica fora |
| Req. 1 — dependências usadas | ✅ | nenhuma nova; o teste de conformidade continua comparando imports e `requirements.txt` |
| Req. 2 — Windows/PowerShell | ✅ | comandos do quickstart em PowerShell |
| Req. 3 — `.bak` nos itens de maior impacto | ✅ após US1 | (a) persistência em `data/processed/`; (b) cópia datada `_backup_AAAA-MM-DD_antes_spec006/` (src, tests, specs, reports, README, requirements, `.specify`) antes de alterar o código; rascunhos, manifestos, dicionários e `reports/` dispensados |
| Req. 4 — dados brutos e processados separados | ✅ | pastas brutas por conjunto; dicionários junto aos brutos |
| Req. 5 — seaborn | ✅ | figuras 06 a 08 com seaborn, tema e paleta centrais; sem eixo duplo (figura 08 em dois painéis) |
| Garantia de qualidade (amostras reais, rollback) | ✅ | sondagens de 05/10/2026 sobre arquivos reais (research R3 a R7); a persistência restaura o estado anterior em falha |

**Re-check pós-design**: sem violações; nenhuma justificativa de complexidade necessária.

## Project Structure

### Documentation (this feature)

```text
specs/006-bases-complementares/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-contract.md
│   └── persistencia-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks (ainda não criado)
```

### Source Code (repository root)

```text
src/
├── config.py               # + pacotes, pastas, arquivos e limiares das bases novas
├── persistencia.py         # NOVO (US1): gravar_csv / gravar_linhas_csv / gravar_parquet / gravar_planilha / gravar_texto
├── dicionarios_ons.py      # NOVO (US2): seleção, obtenção sempre, classificação por SHA-256, registro
├── conjuntos_ons.py        # NOVO: motor comum dos conjuntos horários (US3–US5)
├── disponibilidade_ons.py  # NOVO (US3): descrição, qualidade D1–D4, conferência, horas paradas, resumos
├── hidrologia_ons.py       # NOVO (US4): conversão de fim de hora, alinhamento, faixas, perfil, resumo mensal
├── geracao_ons.py          # NOVO (US5): conferência horária e mensal
├── cadastro_ons.py         # NOVO (US6): ficha, homônimos, divergências
├── consolidator.py         # gravação via persistência (US1)
├── processor.py            # gravação via persistência (US1; planilha com assinatura)
├── validator.py            # gravação via persistência (US1)
├── indicadores_ons.py      # gravação via persistência (US1); dicionários ao baixar (US2)
├── programacao_ons.py      # gravação via persistência (US1); dicionários ao baixar (US2)
├── main.py                 # etapas 5–8; modos --complementares-only, --X-only, --dicionarios-only, --sem-X; código 3; dicionário da EVT na etapa 1
├── logger.py               # LOGGERS_PIPELINE + loggers novos
├── analyzer.py             # ResultadosAnalise (+5 campos), constatações, seções, abas, figuras 06–08
└── pdf_generator.py        # seções novas no PDF

tests/
├── unit/test_persistencia.py     # NOVO (contrato da US1)
├── test_dicionarios_ons.py       # NOVO
├── test_conjuntos_ons.py         # NOVO
├── test_disponibilidade_ons.py   # NOVO
├── test_hidrologia_ons.py        # NOVO
├── test_geracao_ons.py           # NOVO
├── test_cadastro_ons.py          # NOVO
├── integration/test_pipeline.py  # etapas 5–8 simuladas; pastas e período
├── test_conformidade.py          # loggers, --log-level e seaborn nos módulos novos
└── test_analyzer.py              # figuras opcionais 06–08; seções condicionais

README.md                         # comandos novos, bases, dicionários, .bak
```

**Structure Decision**:
- Um módulo por conjunto, como nas specs 004 e 005, com o motor comum em `conjuntos_ons.py`, porque disponibilidade, hidrologia e geração seguem o mesmo fluxo.
- A persistência é um módulo transversal único, usado por todos os gravadores de `data/processed/`.
- As análises de cruzamento ficam em cada módulo de conjunto. O `analyzer.py` só compõe resultados, textos, abas e figuras, como já faz com a programação.

### Sequência de entrega

| Data | Entrega |
|---|---|
| 06/10 | Cópia datada; US1 (persistência e migração dos 5 gravadores) com testes |
| 07/10 | US2 (dicionários) e motor comum com testes |
| 08–09/10 | US3 (download da disponibilidade, cerca de 1,3 GB) e análises |
| 09–10/10 | US4 (hidrologia, alinhamento) e análises |
| 11–12/10 | Relatório: seções, constatações, abas, figuras 06–08, PDF; não regressão |
| 13/10 | Quickstart completo e relatório regenerado (SC-010) |
| Depois | US5 e US6; se houver folga antes de 13/10, entram antes |

**Riscos e mitigação**:
- **Lentidão ou indisponibilidade do portal no download inicial**: cache por versão e retentativas. A etapa pode ser repetida e só baixa o que falta.
- **Alinhamento hidrológico abaixo de 99% em algum ano** (revisões do ONS): a etapa retorna 3 e a análise não publica os cruzamentos; o arquivo de alinhamento mostra a coincidência.
- **Tamanho do `analyzer.py`**: as funções de cálculo ficam nos módulos de conjunto.

## Complexity Tracking

Nenhuma violação a justificar.
