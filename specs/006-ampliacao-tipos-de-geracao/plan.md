# Implementation Plan: Relatórios de Desempenho para Todos os Tipos de Usina

**Branch**: `006-ampliacao-tipos-de-geracao` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-ampliacao-tipos-de-geracao/spec.md`

## Summary

O fluxo de cinco etapas, hoje feito para usina hidrelétrica, passa a atender qualquer usina que os dados abertos do ONS cobrem: UHE, PCH, CGH, UTE, UTN, EOL e UFV. Com isso, o fiscal:
- escolhe a usina num catálogo montado do cadastro do ONS;
- gera o rascunho do perfil, confere e completa;
- obtém o relatório com as seções comuns e as próprias do tipo, cada número identificado como da usina, do conjunto ou de um agregado;
- obtém também o relatório de carteira de um estado, de um tipo ou dos dois.

**Abordagem técnica**: reaproveitar o núcleo e acrescentar as regras por tipo em tabelas declarativas dentro das etapas, sem pacote por tipo:
- **Núcleo reaproveitado**: linha de comando única, `etapa.json`, gravação segura, motor dos conjuntos horários, estrutura do relatório, catálogo da conclusão e `comparar`.
- **Perfil**: ganha tipo, modalidade, situação e a tabela `[cobertura]`, validados por uma tabela de campos por tipo (R4, R5).
- **Coleta**:
  - um registro declarativo diz que conjunto do ONS serve a que tipo e como identificar a usina nele (R8, R9);
  - o período vem da série de referência do tipo, dividida em trechos quando muda o nível do dado, a composição do conjunto ou o código de planejamento (R6, R7);
  - entram dez conjuntos do ONS: despacho térmico por motivo, CVU, CMO, fator de capacidade, restrição por constrained-off com detalhe e com razão (eólica e fotovoltaica), composição dos conjuntos e capacidade de geração.
- **Análises**: nas usinas sem EVT, as seções e as regras comuns usam uma base horária comum (R30). As hidrelétricas com EVT seguem o caminho de hoje. As regras da conclusão declaram os tipos e só usam dado da usina (R16).
- **Relatório**: as seções declaram os tipos, numa ordem fixa (R14).
- **Comandos novos**:
  - `usinas` (catálogo, na Coleta);
  - `perfil` (rascunho, só a partir do catálogo);
  - `carteira` (só resultados gravados);
  - `referencia` e `comparar --todas`, para os relatórios aprovados (R22).

**Proteção dos relatórios aprovados** (R22, R29):
- Cada referência guarda a Coleta e o perfil congelados da usina. O `comparar --todas` refaz as etapas 2 a 5 num espaço isolado a partir deles; com `--coleta`, refaz também a Coleta e a compara no período da referência. O resultado não depende dos brutos compartilhados nem de outras usinas.
- O layout, as regras e os arquivos das hidrelétricas com EVT ficam iguais aos de hoje, com um teste por invariante.
- As etapas 2 a 5 deixam de ler `data/raw/`: as datas de obtenção, o resumo do manifesto e o dicionário da EVT passam a vir da Coleta (princípio I).

**Achados que mudaram o desenho** ([research.md](research.md)):
- **Nos dados do ONS**:
  - nomes e ids mudaram em 05/2026 (A3), e a térmica piloto teve três códigos de planejamento (A4);
  - as solares de MS só têm série por usina desde 08/2026 (A7);
  - a razão da restrição só existe na base sem detalhe (A8);
  - o conjunto da PCH piloto teve térmicas até 07/2025 (A2).
- **No código atual**:
  - as etapas 2 a 5 leem `data/raw/`, compartilhado: datas de obtenção, resumo do manifesto e dicionário da EVT (B1);
  - a planilha traz as auditorias e o registro dos dicionários com todos os conjuntos (B2, B3);
  - as Análises partem da base de EVT (B4).

Esses achados levaram a ajustes no rascunho da spec (R25). Por decisão do usuário de 09/10/2026, a implementação começa antes da fiscalização de 14 a 16/10/2026. A fiscalização usa a versão aprovada da São Domingos, congelada numa pasta fora do projeto, com os próprios dados (FR-028).

## Technical Context

**Language/Version**: Python 3.14.6 no `venv` do projeto; mínimo 3.11 (`tomllib`).

**Primary Dependencies**:
- **Sem dependência nova**: pandas, numpy, pyarrow, openpyxl, matplotlib, seaborn, reportlab e pytest, os de `requirements.txt`. O perfil continua no `tomllib`.
- **Rede**: o catálogo CKAN do ONS e os downloads continuam só em `src/coleta/catalogo.py`.

**Storage**: arquivos.
- **`data/raw/`**: compartilhado; ganha uma pasta por conjunto novo, todos em Parquet quando publicado (A14).
- **`data/catalogo/`** (novo): `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`, sem `.bak`.
- **`data/usinas/<slug>/<etapa>/`**: os arquivos de hoje, sem mudança na UHE, e os novos por tipo ([data-model](data-model.md), seção 6).
- **`reports/<slug>/`** e **`reports/carteiras/<nome>/`** (novo).
- **`relatorios_referencia/<slug>/`** (novo): o relatório aprovado e o perfil congelado, no git (o PDF por exceção no `.gitignore`), e a Coleta congelada, fora do git. A pasta é copiada para cada cópia de segurança.
- **Perfis**: `usinas/<slug>/perfil.toml`.
- **Cópias de segurança**: `_backup_<data>_<motivo>/`, no máximo duas.

**Testing**:
- pytest com a rede bloqueada (proxy inválido), como hoje: 396 testes;
- uma usina fictícia por tipo, de ponta a ponta (R23);
- um teste por invariante do relatório da UHE (R29);
- `comparar --todas [--coleta]` contra as referências.

**Target Platform**: Windows 11, PowerShell.

**Project Type**: projeto único; pipeline de dados em lote com linha de comando (`python -m src`), que gera PDF, Markdown e planilha.

**Performance Goals**:
- rascunho do perfil em menos de 1 minuto (SC-003);
- fluxo completo de uma usina piloto em até 15 minutos com os dados locais (SC-006);
- carteira de MS em até 5 minutos (SC-006);
- catálogo do Brasil sem portal em até 3 minutos (meta do plano);
- `comparar --todas` com as cinco referências em até 20 minutos (meta do plano; as etapas 2 a 5 de cada uma).

**Constraints**:
- relatório da São Domingos igual à referência ao fim de cada fase (SC-001);
- só a Coleta, inclusive o catálogo, acessa o portal (princípio I);
- no projeto principal, nenhuma coleta com o portal até o item 2 da fase A e nenhum download de outra usina antes do novo congelamento da Coleta da São Domingos (R22). A versão de fiscalização tem os próprios dados e não entra nessa regra;
- nenhum valor de usina no código (princípio II), conferido por teste também para as usinas piloto;
- no máximo duas cópias de segurança, com as referências (RT5);
- código só depois de congelada e conferida a versão de fiscalização da São Domingos (FR-028);
- Parquet sempre que publicado: em CSV, os conjuntos novos passam de 20 GB (A14).

**Scale/Scope**:
- 7 tipos de usina e 5 usinas piloto, 1 delas já aprovada;
- 30 FR e 8 SC;
- conjuntos do ONS: de 10 para 20 pacotes;
- cadastro: 6.017 linhas, 171 em MS;
- código atual: cerca de 12.600 linhas em `src/`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Conferência contra a constituição **3.0.0**, a que está em vigor:

| Princípio ou requisito | Situação | Como o plano cumpre |
|---|---|---|
| I. Uma spec por etapa; só a Coleta acessa o portal; cada etapa lê só as anteriores | Passa | A spec 006 é de mudança temporária (Governança 2), com os ajustes das specs das etapas em `ajustes-specs/`, aprovados antes do código de cada fase (R26). O catálogo é da Coleta (R2); `perfil` e `carteira` só leem arquivos gravados. O plano corrige um desvio de hoje: as etapas 2 a 5 deixam de ler `data/raw/` (datas, manifesto e dicionário da EVT), com um teste que as roda com `data/raw/` vazio (B1, R22) |
| II. Relatório fiel aos dados | Passa | Regras da conclusão por tipo em catálogo, com limiares em `regras.py` e nas notas, calibrados nas pilotos e aprovados (R16). O que não tem base é omitido, com o motivo (R17). `test_literais.py` cobre também os identificadores das pilotos (R23) |
| III. Uma usina por execução, perfil, catálogo e carteira | Passa | O perfil declara tipo, modalidade, identificadores e cobertura (R4). O rascunho é recusado até ser conferido (R5). Homônimos e grafias variáveis são tratados pelos códigos (R9). Séries de outras usinas só entram como contexto identificado (G2, R13). A carteira só lê resultados gravados, sem nota nem parecer (R21) |
| IV. Coleta completa e rastreável | Passa | Só o portal do ONS. A série de referência é varrida inteira; os demais conjuntos, pelo período (R6). Ausências listadas (R28). Versões e dicionários também nos conjuntos novos e no catálogo (R2, R8). Identificador com conferência (R9) |
| V. Tratamento sem descarte | Passa | Sinalizações novas sem exclusão (FR-017). Semi-horárias na resolução publicada e em hora cheia. Convenção de hora declarada e conferida. Regras de duplicatas e ausências também no panorama (R11) |
| VI. Conferência entre fontes | Passa | G1 a G5, sempre no mesmo nível, sem meta até as pilotos. Todas as conferências do catálogo que não se aplicam à usina, inclusive na UHE, ficam registradas com o motivo em `nao_aplicaveis.csv` (R13). As de hoje continuam iguais |
| VII. Relatório padronizado | Passa | Estrutura fixa com seções por tipo (R14); legendas com o identificador e o nível (R15); figuras em seaborn; a carteira segue as mesmas regras e usa a aba FONTES (R21) |
| VIII. Granularidade declarada | Passa | Nível em todo número; nada de conjunto dividido entre usinas; trechos de composição (R7, R15, R20). Regras da conclusão só com dado da usina (R16) |
| IX. Relatórios aprovados protegidos | Passa | Referências guardadas com a Coleta e o perfil congelados e copiadas para cada cópia de segurança. A anterior fica no histórico do git: o `referencia` recusa substituir uma referência não commitada (R22). `comparar --todas --coleta` no fim de cada fase, independente dos brutos compartilhados (R27). Diferença só com aprovação |
| RT1. Python, `venv`, dependências | Passa | Nenhuma dependência nova |
| RT2. Windows e PowerShell | Passa | Exemplos e caminhos em PowerShell ([quickstart](quickstart.md)) |
| RT3. Gravação segura | Passa | Coleta e Tratamento pela `persistencia`, com `.bak`. Catálogo, carteira e referências sem `.bak`, gravados em pasta temporária e conferidos no disco |
| RT4. Versões dos brutos | Passa | O limite de duas versões vale para os conjuntos novos (mesmo catálogo) |
| RT5. Cópias de segurança | Passa | No máximo duas, agora com `relatorios_referencia/` (R22) |
| RT6. Pastas | Passa | `data/catalogo/` e `reports/carteiras/<nome>/`, como a constituição define; `carteiras` reservado como slug. `relatorios_referencia/` não está na lista do RT6, que não a proíbe; atende ao princípio IX |
| RT7. Log | Passa | Os loggers de hoje: `coleta` no catálogo e no rascunho; `relatorio` na carteira; `pipeline` nas referências |
| Qualidade 1. Testes | Passa | Sem rede, com uma usina fictícia por tipo (R23), os invariantes das hidrelétricas com EVT (R29) e as etapas 2 a 5 sem `data/raw/` (R22) |
| Qualidade 2 e 3. Entrega e recuperação | Passa | `comparar --todas --coleta` em toda entrega; cópias com as referências; git |
| Governança 2. Mudanças | Passa | As mudanças na spec feitas durante o plano estão na R25 e foram aprovadas pelo usuário em 09/10/2026, com a spec, o plano e a constituição 3.0.0. Os rascunhos das specs das etapas são aprovados antes do código de cada fase (R26) |

**Resultado**: o gate passa, sem violação.

**Reavaliação depois do desenho** (Phase 1):
- O data-model, os contratos e o quickstart mantêm as decisões acima.
- Duas revisões cruzadas dos documentos (09/10/2026) apontaram riscos:
  - ao princípio I e ao IX: brutos compartilhados, leituras de `data/raw/` nas etapas 2 a 5, referência fora do git;
  - ao princípio VI: conferências não aplicáveis da UHE sem registro;
  - ao princípio VIII: regras com dado de conjunto e MMGD por área do estado;
  - à planilha e ao relatório da UHE.
- As decisões R13, R16, R22, R25, R29 e R30 os resolvem. O princípio VIII teve a redação ajustada na constituição 3.0.0, com a aprovação do usuário (R25).
- Não ficou violação.

## Fases de implementação e pontos de controle

Uma fase por história, na ordem da spec (FR-028, R27). Em toda fase:
- **Início**: cópia de segurança e aprovação dos rascunhos das specs das etapas da fase (`ajustes-specs/`), antes de qualquer código (R26).
- **Fim**: a suíte; a análise estática (`pyflakes`, rodado de fora do `venv`, como hoje, sem entrar no `requirements.txt`); `/speckit-converge`; `comparar --todas --coleta` com código 0; e a aprovação do usuário nos pontos indicados.

| Fase | História | Entregas, na ordem | Ponto de controle |
|---|---|---|---|
| A | US1, fundação | 1. referências: `referencia`, `comparar --todas [--coleta]`, `copia-seguranca` com `relatorios_referencia/`; a Coleta no formato 2 (datas de obtenção, resumo do manifesto e dicionário da EVT); as etapas 2 a 5 sem `data/raw/`; testes dos invariantes (R22, R29). 2. migração da referência da São Domingos, com a Coleta e o perfil congelados. 3. correções P1 a P5 (R10); registro dos conjuntos, com dicionários e fontes por usina (R8); perfil por tipo, com a São Domingos ganhando só duas linhas (R4). 4. novo congelamento, se o formato da Coleta mudou; a partir daqui, downloads liberados. 5. catálogo de usinas, com composição, capacidade e códigos (R1 a R3). 6. rascunho do perfil (R5). 7. série de referência por tipo e trechos (R6, R7). 8. base horária comum; seções com tipos, título, capa e legendas por caminho; omissões nas notas (R30, R14, R15, R17). 9. conclusão com tipos, listas e nível exigido (R16). 10. usinas fictícias de todos os tipos com as seções comuns (R23) | `comparar --todas --coleta` depois de cada item. **Aprovação**: catálogo de MS e rascunho da William Arjona |
| B | US2, térmicas | despacho, CVU e CMO na Coleta (com `planejamento.csv` no catálogo) e no Tratamento; G3 e G4; análises e seções de térmica, com a inflexibilidade; C12 a C15; C2, C5, C8 e C10 sobre a base horária comum | **Aprovação** do relatório da William Arjona e dos limiares; `referencia` |
| C | US3, eólicas e solares | fator de capacidade e restrição com detalhe e com razão; semi-horárias no motor da Coleta; G1, G2 e G5; análises e seções de renováveis; C16 a C19 | **Aprovação** da Seriemas 1 e da Praia Formosa e dos limiares; `referencia` |
| D | US4, PCH e CGH | geração do conjunto por trecho de composição; composição; omissões e notas do nível de conjunto; conclusão sem base na usina | **Aprovação** da Bandeirante; `referencia` |
| E | US5, carteira | `indicadores_carteira` nas Análises; comando `carteira` por estado, por tipo ou pelos dois; panorama dos agregados | **Aprovação** da carteira de MS |
| F | fechamento | incorporação de `ajustes-specs/` às specs 001 a 005; troca das citações da spec 006 no código; README com todos os tipos; exclusão da pasta da spec 006 | **Aprovação** da exclusão; SC-008 |

**Riscos e respostas**:

| Risco | Resposta |
|---|---|
| Uma correção ou refatoração muda o relatório da São Domingos | entregas separadas e conferidas uma a uma com `comparar --todas --coleta` (fase A); um teste por invariante (R29); diferença só com aprovação |
| Os brutos compartilhados mudam com a coleta de outra usina ou com uma republicação do ONS | referência com a Coleta e o perfil congelados e comparação no espaço isolado (R22); nenhuma coleta com o portal até a migração e nenhum download de outra usina antes do novo congelamento |
| Desenvolvimento durante a fiscalização de 14 a 16/10 | a fiscalização usa a versão congelada fora do projeto, com os próprios dados; uma coleta com o portal feita nela não afeta o projeto principal (FR-028) |
| O ONS muda de novo nomes, ids ou colunas | identificação só por códigos, com conferência (R9); coluna de conferência ausente vira `FALHA` (P4); a auditoria mostra as linhas que conferem só em parte |
| Limiares das regras novas sem base | começam nas pilotos e só entram com aprovação (R16) |
| Volume dos conjuntos novos | Parquet e período da usina (A14, R28) |
| Série curta das solares de MS | seções e regras com período mínimo (R17); a EOL piloto cobre a série longa |

## Project Structure

### Documentation (this feature)

```text
specs/006-ampliacao-tipos-de-geracao/
├── spec.md                  # spec de mudança temporária (ajustada no plano, R25)
├── plan.md                  # este arquivo
├── research.md              # achados A1 a A14 e B1 a B7; decisões R1 a R30
├── data-model.md            # catálogo, perfil por tipo, registro, trechos, resultados, carteira, referências
├── quickstart.md            # validação por fase
├── contracts/
│   ├── cli-usinas.md        # catálogo de usinas
│   ├── cli-perfil.md        # rascunho do perfil
│   ├── cli-carteira.md      # relatório de carteira
│   ├── cli-referencias.md   # referencia, comparar --todas e copia-seguranca
│   └── perfil-multitipo.md  # perfil para todos os tipos, com exemplos das pilotos
├── checklists/
│   └── requirements.md
├── ajustes-specs/           # um rascunho por spec de etapa, aprovado no início de cada fase (R26)
└── tasks.md                 # /speckit-tasks (ainda não criado)
```

A pasta inteira sai no fechamento (FR-030), com aprovação do usuário, e fica no histórico do git.

### Source Code (repository root)

`+` = módulo novo; `~` = módulo que muda.

```text
src/
├── __main__.py                ~ comandos usinas, perfil, carteira e referencia; comparar --todas [--coleta]
├── pipeline.py                ~ etapas executáveis num espaço isolado (para o comparar --todas)
├── comum/
│   ├── perfil.py              ~ tipo, modalidade, situação, cobertura, unidades; validação por tipo
│   ├── perfil_campos.py       + tabela de campos por tipo (data-model, seção 3.2)
│   ├── regras.py              ~ pacotes e pastas novos; limiares de C12 a C19; tolerâncias novas
│   ├── caminhos.py            ~ data/catalogo/, reports/carteiras/, relatorios_referencia/; raiz trocável
│   ├── copia_seguranca.py     ~ copia relatorios_referencia/ e confere os SHA-256
│   ├── referencias.py         + comando referencia; Coleta e perfil congelados; conferência no git; espaço isolado do comparar --todas
│   └── comparacao.py          ~ --todas e --coleta; ignora referencia.json e coleta/
├── coleta/
│   ├── registro.py            + registro declarativo dos conjuntos (R8)
│   ├── conjuntos.py           ~ motor: semi-horária, semanal, usina ou conjunto; P2 a P4
│   ├── catalogo.py            ~ P1: recurso repetido escolhido em todos os conjuntos; .part por recurso
│   ├── evt.py, indicadores.py, programacao.py, cadastro.py   ~ P1, P3, P5; lista de códigos de programação
│   ├── dicionarios.py         ~ registro só com os conjuntos do tipo e da cobertura da usina
│   ├── catalogo_usinas.py     + comando usinas: catálogo, cobertura, códigos e agregados (R2, R3)
│   ├── perfil_rascunho.py     + comando perfil (R5)
│   ├── serie_referencia.py    + série de referência e trechos (R6, R7)
│   └── etapa.py               ~ conjuntos pelo registro e pela cobertura; formato 2: datas_obtencao.csv e dicionario_evt.json
├── tratamento/
│   ├── base_horaria.py        + base horária comum das usinas sem EVT (R30)
│   ├── series.py              ~ semi-horária em hora; semanais
│   ├── termica.py             + despacho, CVU e CMO
│   ├── renovavel.py           + fator de capacidade, restrição, razão e energia cortada
│   ├── validacao.py           ~ sinalizações novas (FR-017); dicionário da EVT lido da Coleta (B1)
│   └── etapa.py               ~
├── conferencia/
│   ├── fontes.py              + G1 a G5
│   ├── aplicabilidade.py      + conferências não aplicáveis, com o motivo
│   └── etapa.py               ~
├── analises/
│   ├── comum_tipos.py         + seções comuns sobre a base horária comum
│   ├── termica.py             + despacho por motivo, inflexibilidade, atendimento, disponível sem despacho, CVU × CMO
│   ├── renovavel.py           + fator de capacidade, energia cortada, recurso × geração, aderência
│   ├── conjunto.py            + composição e geração do conjunto por trecho
│   ├── carteira.py            + indicadores_carteira
│   ├── geracao.py, disponibilidade.py, hidrologia.py, cobertura.py   ~ datas e resumo do manifesto lidos da Coleta (B1)
│   ├── resultados.py          ~ campos novos; VERSAO_FORMATO 2
│   ├── conclusao.py           ~ regras com tipos, listas e nível exigido; C12 a C19
│   ├── constatacoes.py        ~ nível nos textos
│   └── etapa.py               ~
└── relatorio/
    ├── estrutura.py           ~ tipos, títulos e legendas por tipo
    ├── secoes_termica.py      + seções de térmica
    ├── secoes_renovavel.py    + seções de eólica e solar
    ├── secoes_conjunto.py     + seções de conjunto
    ├── fontes.py              ~ nível na legenda; datas de obtenção lidas da Coleta (B1)
    ├── figuras.py             ~ figuras novas, em seaborn
    ├── carteira.py            + relatório de carteira
    └── conteudo.py, markdown.py, pdf.py, planilha.py   ~ capa e notas por tipo; UHE sem mudança

tests/
├── fixtures/
│   ├── usinas_ficticias/<tipo>/   + perfis das sete usinas fictícias
│   └── brutos_ficticios.py        ~ brutos sintéticos de todos os conjuntos
├── coleta/        + registro, catálogo de usinas, rascunho, série de referência, P1 a P5, conjuntos novos, datas de obtenção
├── comum/         ~ perfil por tipo, referências, comparar --todas, literais das pilotos
├── tratamento/    + base horária comum, térmica, renovável
├── conferencia/   + G1 a G5, não aplicáveis
├── analises/      + seções comuns, térmica, renovável, conjunto; ~ conclusão
├── relatorio/     ~ estrutura por tipo; + invariantes da UHE (R29); + carteira
└── integracao/    + uma usina fictícia por tipo, de ponta a ponta; + etapas 2 a 5 com data/raw/ vazio; ~ linha de comando

usinas/<slug>/perfil.toml          + perfis das quatro usinas piloto novas, conferidos pelo usuário
relatorios_referencia/<slug>/      + relatórios aprovados (no git) e Coleta congelada (fora do git)
data/catalogo/                     + catálogo (fora do git, como data/)
reports/carteiras/<nome>/          + relatórios de carteira
.gitignore                         ~ exceção para os PDFs de relatorios_referencia/; exclusão de relatorios_referencia/*/coleta/
```

**Structure Decision**:
- O projeto continua único e organizado pelas etapas.
- O que é próprio de um tipo fica dentro do pacote da etapa, em tabelas declarativas (registro, campos do perfil, seções, regras) e em módulos por assunto (`termica`, `renovavel`, `conjunto`). Não há pacote por tipo, como manda o princípio I para as specs.
- Os comandos novos entram no `src/__main__.py` de hoje, o único ponto de entrada.

## Complexity Tracking

Sem violação da constituição. Os pontos abaixo trazem complexidade e estão justificados:

| Ponto | Por que é necessário | Alternativa mais simples rejeitada porque |
|---|---|---|
| Specs das etapas sem mudança até o fechamento, com os ajustes em `ajustes-specs/` | Governança 2 e pedido do usuário; o padrão da spec 009 | alterar as specs a cada fase misturaria texto aprovado e em construção |
| Referência com a Coleta e o perfil congelados, comparada num espaço isolado | os brutos são compartilhados e mudam com outras usinas e com republicações do ONS (B6); um perfil corrigido depois mudaria o relatório sem mudança de código; o princípio IX pede a comparação a cada fase | refazer a Coleta a cada comparação não reproduz a referência; congelar os brutos ocuparia vários GB por usina |
| `relatorios_referencia/` no git e copiada para as cópias | o princípio IX pede a referência junto às cópias e a anterior no controle de versões | só dentro das cópias, a anterior sairia na poda e não ficaria no git |
| Tabela `[cobertura]` no perfil, além do catálogo | o princípio III manda o perfil declarar os conjuntos que cobrem a usina, conferidos pelo fiscal | ler a cobertura do catálogo a cada execução faria uma atualização do ONS mudar o fluxo sem o fiscal saber |
| Base horária comum separada da base de EVT | as Análises de hoje partem da EVT, que os outros tipos não têm (B4) | simular uma base de EVT esconderia o tipo da usina e arriscaria textos de UHE em outros tipos |
| `VERSAO_FORMATO` 2 na Coleta e nas Análises | a Coleta grava arquivos que as etapas seguintes passam a exigir, e o `resultados.pkl` ganha campos; o formato antigo é recusado com o código 5 e a indicação da etapa a refazer | camadas de compatibilidade de leitura seriam código a mais para um único refazer, sem download |
| Conferências novas sem meta | não há histórico para calibrar | uma meta arbitrária poderia parar o fluxo sem motivo (princípio VI) |
