# Implementation Plan: Reorganização do Projeto num Fluxo de Cinco Etapas, Reutilizável para Outras Usinas

**Branch**: `009-reorganizacao-pipeline` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-reorganizacao-pipeline/spec.md`

## Summary

O relatório ganha uma única mudança de conteúdo, a seção **Conclusão** (US6):
- quatro listas curtas: pontos de atenção, possíveis problemas (inclusive indício em unidade geradora), o que confirmar com o agente e o que verificar em campo;
- os itens são gerados por um catálogo de regras declaradas (C1 a C11) a partir dos resultados.

Ela é implementada primeiro, no código atual, para estar pronta antes da fiscalização de 14 a 16/10/2026. Depois de aprovada pelo usuário, o relatório com a conclusão vira a referência, e a partir daí ele continua igual, byte a byte. O que muda é a organização do projeto:

- **Fluxo**: cinco etapas (Coleta → Tratamento → Conferência → Análises → Relatório), com um único comando `python -m src <etapa> --usina <slug>`. Cada etapa grava os seus resultados numa pasta própria, com manifesto, e só lê o que as anteriores gravaram.
- **Código**: organizado em pacotes por etapa. As funções são movidas sem reescrever a lógica, e as seis conferências entre fontes passam a formar a etapa de Conferência.
- **Perfil da usina** (TOML): reúne tudo o que é próprio de uma usina. A São Domingos é o primeiro perfil, e as análises que supõem duas unidades ou faixas fixas passam a derivar do perfil.
- **Constituição**: reescrita como 2.0.0, sem emendas e sem valores de usina.
- **Specs**: as oito atuais viram cinco, uma por etapa, com um mapeamento aprovado pelo usuário.
- **Cópias de segurança**: no máximo duas, e a limpeza segue um inventário aprovado.
- **Prova de não regressão**: uma linha de base gerada pelo código atual com a data fixa e o PDF em modo invariante, comparada byte a byte com a saída do fluxo novo.

## Technical Context

**Language/Version**:
- Python 3.14.6 no `venv` do projeto.
- O mínimo passa a ser 3.11, por causa do `tomllib`, que lê o perfil.

**Primary Dependencies**:
- Sem dependência nova: pandas, numpy, pyarrow, openpyxl, matplotlib, seaborn, reportlab e pytest.
- O perfil usa o `tomllib` da biblioteca padrão.

**Storage**: arquivos.
- **Brutos compartilhados**: `data/raw/`, como hoje.
- **Por usina e por etapa**: `data/usinas/<slug>/<etapa>/`, com CSV, Parquet, XLSX, pickle versionado e `etapa.json`.
- **Relatório**: `reports/<slug>/`.
- **Perfil**: `usinas/<slug>/perfil.toml`.

**Testing**:
- pytest com a rede bloqueada (proxy inválido), como hoje.
- Dados sintéticos de hoje, mais uma usina fictícia em `tests/fixtures/`.
- Comparação byte a byte com a linha de base (comando `comparar`).

**Target Platform**: Windows 11 com PowerShell.

**Project Type**: pipeline de dados em lote, com interface de linha de comando, que gera relatório em PDF, Markdown e planilha.

**Performance Goals**:
- `completo --sem-portal` para a São Domingos em até 15 min, a partir dos ~4,1 GB brutos locais.
- `relatorio` sozinho em até 1 min.
- Suíte de testes em até 2 min.

**Constraints**:
- Relatório da São Domingos idêntico ao de referência (SC-001): o aprovado em 07/10/2026 com a conclusão aprovada.
- Nenhum download novo nem base nova; a base de EVT local é mantida.
- Nenhuma exclusão fora do inventário aprovado.
- A versão aprovada continua no git (commit `a8315cc`) e na cópia `antes_reorganizacao`.
- A fiscalização presencial é de 14 a 16/10/2026: o relatório aprovado fica disponível o tempo todo, e cada fase termina com o relatório reproduzível.

**Scale/Scope**:
- 10.725 linhas em 24 módulos de `src/`; o `analyzer.py` sozinho tem 3.823.
- 3.650 linhas de testes, com 244 casos.
- 8 specs, com 143 FR, a consolidar em 5.
- 10 conjuntos do ONS.
- 1 usina real e 1 fictícia de teste.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Conferência contra a constituição **1.2.0**, a que está em vigor:

| Princípio ou requisito | Situação | Observação |
|---|---|---|
| I. SDD | Passa | spec, plano, tarefas e implementação; a conclusão está especificada nesta spec (US6) antes do código; as specs das etapas são escritas e aprovadas antes da reorganização do código (fase 3) |
| II. Python exclusivo e código limpo | Passa | reorganização em pacotes por etapa, com tipos e docstrings preservados; scripts de apoio em Python |
| III. Varredura exaustiva | Passa | a coleta continua varrendo todos os arquivos publicados; nada muda no critério |
| IV. Filtragem precisa e rastreabilidade | Passa | identificador e conferência por conjunto mantidos; os valores passam ao perfil, com os mesmos números da tabela do princípio; auditoria, manifesto e dicionários mantidos |
| V. Idempotência e versões | **Conflito**, resolvido antes | a FR-030 limita a duas as versões anteriores de cada arquivo bruto, e o texto atual manda preservar todas. A poda só é implementada depois da constituição 2.0.0 (fase 2) |
| VI. Escopo exclusivo da São Domingos | **Conflito**, resolvido antes | a US3 pede outras usinas. A constituição 2.0.0 (uma usina por perfil, homônimos excluídos) é aprovada e entra em vigor na fase 2, antes de qualquer código com perfil (fase 4 em diante) |
| Conclusão (US6) | Passa | a constituição 1.2.0 não trata de parecer; a proibição está na FR-005 da spec 003, que esta spec mantém e complementa com a conclusão por regras, sem afirmar causa (FR-039). A conclusão usa só resultados já calculados e respeita os princípios III e IV |
| Req. 1. Dependências | Passa | nenhuma nova; o `tomllib` é da biblioteca padrão |
| Req. 2. Windows e PowerShell | Passa | `python -m src ...` e exemplos em PowerShell |
| Req. 3. Persistência segura | Passa | `.bak` de uma versão nos dados de coleta e tratamento; cópia datada antes das mudanças, agora no máximo duas (FR-027), regra que entra na 2.0.0 |
| Req. 4. Bruto e processado separados | Passa | `data/raw/` compartilhado, separado de `data/usinas/<slug>/` |
| Req. 5. Seaborn | Passa | as figuras não mudam |
| Qualidade e não regressão | Passa | linha de base byte a byte; suíte sem rede a cada fase |

**Resultado**: o gate passa com uma condição. A constituição 2.0.0 tem de estar aprovada e em vigor antes das fases 4 a 6, que mexem no escopo (VI) e nas versões (V). As fases 0, 1 e 3 não dependem disso; a fase 2 é a própria mudança da constituição.

**Reavaliação depois do desenho (fase 1 do plano)**:
- O desenho atende ao esboço da constituição 2.0.0 (research R13): uma spec por etapa, relatório fiel aos dados, uma usina por perfil, coleta rastreável, tratamento sem descarte, conferência registrada, relatório padronizado, no máximo duas cópias e duas versões, e testes sem rede.
- Não surgiu violação nova.

## Fases de implementação e pontos de controle

As fases detalham a research R1. Cada uma termina com a suíte sem rede e, a partir da fase 4, com o `comparar` contra a linha de base.

| Fase | Entrega | Ponto de controle |
|---|---|---|
| 0. Preparação | cópia `antes_conclusao`; exclusão das cópias de 06/10 ou antes; poda para duas; `inventario-limpeza.md` | **aprovação do usuário** do inventário; aplicação do aprovado |
| 1. Conclusão (código atual) | regras C1 a C11 (R17); seção "Conclusão" no PDF, no Markdown e no sumário; aba CONCLUSAO; nota metodológica; testes | **aprovação do usuário** do texto gerado; em seguida, cópia `antes_reorganizacao` com a linha de base (código com a conclusão, data fixa, PDF invariante) |
| 2. Constituição | rascunho da 2.0.0 (R13), já com a conclusão por regras | **aprovação do usuário**; gravação com `/speckit-constitution`, sem relatório de impacto |
| 3. Specs das etapas | `novas-specs/001` a `005` (`spec.md`) e `mapeamento-specs.md` | **aprovação do usuário** |
| 4. Perfil | `usinas/sao_domingos/perfil.toml`, leitura e validação, regras gerais × perfil; código lendo o perfil | suíte; `comparar` = 0 (fluxo antigo) |
| 5. Código por etapa | pacotes `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio` e `comum`; `python -m src`; `etapa.json`; pastas por usina; testes por etapa; migração um conjunto por vez | suíte; `comparar` = 0 a cada conjunto migrado; dados tratados iguais aos atuais |
| 6. Generalização | faixas e textos do perfil; usina fictícia; varredura de literais | suíte, inclusive a usina fictícia; `comparar` = 0 |
| 7. Fechamento | `plan.md` e `data-model.md` das cinco specs, conforme o código; README; inventário final (layout antigo); remoção das specs antigas e da 009 | **aprovação do usuário** da remoção; validação final do quickstart |

## Project Structure

### Documentation (this feature)

```text
specs/009-reorganizacao-pipeline/
├── spec.md                 # requisitos da reorganização
├── plan.md                 # este arquivo
├── research.md             # decisões R1 a R16
├── data-model.md           # constantes, perfil, etapa.json, artefatos, objetos, destino dos módulos
├── quickstart.md           # cenários de validação
├── contracts/
│   ├── cli-etapas.md       # linha de comando única, opções e códigos de saída
│   └── perfil-usina.md     # perfil TOML, com o da São Domingos
├── checklists/requirements.md
├── inventario-limpeza.md   # fase 0, aprovado pelo usuário
├── mapeamento-specs.md     # fase 2, aprovado pelo usuário
├── novas-specs/            # fase 2: as cinco specs, até o fechamento
└── tasks.md                # /speckit-tasks (ainda não criado)
```

A pasta inteira sai no fechamento (FR-019) e fica no histórico do git.

### Source Code (repository root)

Layout ao final da reorganização:

```text
src/
├── __main__.py              # python -m src <comando> --usina <slug>
├── pipeline.py              # ordem das etapas, etapa.json, pré-requisitos, invalidação das seguintes
├── comum/
│   ├── perfil.py            # leitura e validação do perfil; valores derivados
│   ├── regras.py            # regras gerais (limiares, tolerâncias, conjuntos e endereços do ONS)
│   ├── caminhos.py          # pastas compartilhadas e pastas por usina e etapa
│   ├── logger.py  formatacao.py  persistencia.py  modelos.py  series_utils.py
│   ├── copia_seguranca.py   # copia-seguranca (no máximo duas)
│   └── comparacao.py        # comparar (byte a byte e célula a célula)
├── coleta/
│   ├── catalogo.py          # catálogo CKAN, download, manifesto, versões anteriores (poda para duas)
│   ├── dicionarios.py
│   ├── conjuntos.py         # descrição dos conjuntos, identificação, leitura numérica, auditoria
│   ├── evt.py               # extração e consolidação da EVT
│   ├── indicadores.py  programacao.py  cadastro.py
│   └── etapa.py             # executa a coleta da usina
├── tratamento/
│   ├── evt.py               # padronização e exportação da EVT
│   ├── validacao.py         # regras R1 a R9
│   ├── series.py            # convenção de hora, duplicatas, período, ausências
│   ├── indicadores.py  programacao.py  disponibilidade.py  hidrologia.py  geracao.py
│   └── etapa.py
├── conferencia/
│   ├── geracao.py  disponibilidade.py  vazoes.py  indicadores.py  cadastro.py
│   └── etapa.py             # executa as seis e grava conferencias.pkl e os CSV
├── analises/
│   ├── resultados.py        # ResultadosAnalise, gravação e leitura versionadas
│   ├── cobertura.py  evt.py  indicadores.py  programacao.py  disponibilidade.py  hidrologia.py  geracao.py  cadastro.py
│   ├── constatacoes.py
│   ├── conclusao.py         # catálogo de regras C1 a C11 → itens da conclusão
│   └── etapa.py             # analisar(); dados das figuras
└── relatorio/
    ├── figuras.py           # gráficos a partir dos resultados (seaborn)
    ├── conteudo.py          # tabelas, textos, notas e legendas compartilhados pelo PDF e pelo Markdown
    ├── fontes.py  estrutura.py
    ├── planilha.py  markdown.py  pdf.py
    └── etapa.py

tests/
├── conftest.py              # dados sintéticos de hoje
├── fixtures/                # perfil e brutos sintéticos da usina fictícia
├── comum/  coleta/  tratamento/  conferencia/  analises/  relatorio/
└── integracao/              # fluxo completo da usina fictícia; CLI; pré-requisitos

usinas/
└── sao_domingos/
    ├── perfil.toml
    └── documentos/          # documentos de referência da usina (fora do git)

referencias/                 # documentos gerais (fora do git)
data/raw/                    # compartilhado (inalterado)
data/usinas/sao_domingos/{coleta,tratamento,conferencia,analises}/
reports/sao_domingos/        # PDF, Markdown, planilha, CSV, figures/

specs/
├── 001-coleta-dados/        # spec.md, plan.md, data-model.md, contracts/, checklists/
├── 002-tratamento-dados/
├── 003-conferencia/
├── 004-analises/
└── 005-geracao-relatorio/
```

**Structure Decision**:
- **Projeto único, organizado pelas etapas do fluxo**: os pacotes de `src/`, as pastas de `tests/`, de `data/usinas/<slug>/` e de `specs/` seguem a mesma ordem.
- **Origem do código**: o destino de cada módulo atual está no data-model (seção 6), e os artefatos de cada etapa, na seção 4.
- **Compatibilidade**: os módulos antigos de `src/` não sobrevivem. Não há fachadas de compatibilidade, porque o único usuário dos módulos é o próprio projeto.

## Complexity Tracking

| Ponto | Por que é necessário | Alternativa mais simples rejeitada porque |
|---|---|---|
| Mudança dos princípios V e VI da constituição em vigor | a US3 (outras usinas) e a FR-030 (duas versões) são pedidos do usuário | manter o escopo exclusivo impediria o reuso pedido; a mudança é feita antes do código, como a governança exige |
| Specs antigas e novas convivendo durante a migração (novas em `009/novas-specs/`) | as antigas são a referência para conferir que nada se perde na consolidação | excluir primeiro deixaria a migração sem referência; o mapeamento aprovado só existe com as duas à vista |
| Objeto serializado (pickle) entre Conferência, Análises e Relatório | entrega a mesma estrutura que hoje passa na memória, o que garante o relatório idêntico | JSON ou Parquet campo a campo exigiria muito código e arriscaria mudar tipos (datas e inteiros com ausentes) |
| Conclusão implementada no código atual e depois movida na reorganização | precisa estar no relatório da fiscalização de 14 a 16/10/2026, e a reorganização é longa | implementar só depois da reorganização deixaria a fiscalização sem a conclusão; o custo extra é mover um módulo a mais na fase 5 |
| Opção `--data-geracao`, com o PDF em modo invariante | é a única forma de provar byte a byte que o relatório não mudou sem um leitor de PDF no projeto; serve também a mudanças futuras | comparar só páginas e Markdown não cobre o conteúdo próprio do PDF |
