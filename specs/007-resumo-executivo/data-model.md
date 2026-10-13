# Data Model: Resumo Executivo do Relatório de Desempenho

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Research**: [research.md](research.md)

O resumo não cria dado novo. Ele formata resultados que as Análises já gravam (`resultados.pkl`), com as mesmas funções do relatório completo. As entidades abaixo são as estruturas da Geração do relatório e as saídas.

## 1. `ResumoExecutivo` (montado em `src/relatorio/resumo.py`)

Objeto único de onde saem o PDF e o Markdown. Por isso os dois têm o mesmo conteúdo, na mesma ordem (FR-003).

| Campo | Conteúdo | Origem |
|---|---|---|
| `nome_usina` | nome da usina | perfil |
| `titulo` | "<nome da usina> — resumo executivo" | perfil |
| `subtitulo` | período analisado, registros horários e "Gerado em" | `res.cobertura` e a data de geração da execução |
| `cabecalho_pagina` | cabeçalho das páginas seguintes à primeira, no PDF: "Resumo executivo — <nome> · <início> a <fim>" | perfil e `res.cobertura` |
| `identificacao` | linhas do cabeçalho (ver 1.1) | perfil e `pares_identificacao(res)` |
| `referencia_relatorio` | título da capa do relatório completo e número de páginas | `titulo_capa_relatorio()` e `paginas_do_pdf` do PDF recém-gerado |
| `termos` | lista de (sigla, explicação), só com os termos que aparecem no resumo, na ordem da primeira ocorrência | `GLOSSARIO_RESUMO` (2.1) |
| `frase_conclusao` | frase de abertura da conclusão, ou a frase de conclusão vazia | `FRASE_ABERTURA_CONCLUSAO` e `FRASE_CONCLUSAO_VAZIA`, sem alteração |
| `listas_conclusao` | as listas da conclusão, cada uma com título e itens | `listas_conclusao(res)`, sem alteração |
| `aviso_secoes` | "As seções e as notas metodológicas citadas são as do relatório completo." | texto geral |
| `indicadores` | `Tabela` com o cabeçalho ["Indicador", "Valor", "Detalhe"], as linhas e a nota "Seção de origem: capa do relatório completo." | `indicadores_capa(res)` |
| `evolucao_anual` | `Tabela` com as colunas escolhidas, as linhas e a nota com a seção de origem; `None` quando omitida | `linhas_tabela_anual(res)` e `COLUNAS_RESUMO_ANUAL` (2.2) |
| `remissao_anual` | frase de remissão à seção, quando a evolução anual é omitida pela regra das duas páginas | número da seção em `secoes_presentes(res)` |
| `sobre_os_dados` | três parágrafos: dados; conferências e limites; fontes (ver 1.2) | `res.cobertura`, `res.globais`, `res.indicadores_anuais` e `fontes.py` |

`Tabela` tem `cabecalho`, `linhas` (os textos já formatados do relatório completo) e `nota`. O método `blocos()` dá os blocos presentes, na ordem fixa, para o PDF e o Markdown.

### 1.1 Linhas do cabeçalho

| Linha | Exemplo (São Domingos) |
|---|---|
| tipo, estado, modalidade e potência | UHE · MS · TIPO II-A · 48,0 MW |
| agentes, cada um com o seu período | o mesmo texto da linha "Agente" da capa |
| período e geração | 28/08/2018 00h a 28/09/2026 23h · gerado em 07/10/2026 08:53 |
| relatório completo | o título do relatório completo, a mesma data e o número de páginas |

Linha sem dado é omitida. Antes da 006, o tipo vem do perfil; depois, do campo `tipo` dos resultados (data-model 6.4 da 006).

### 1.2 Parágrafos de "Sobre os dados" (no máximo 250 palavras, ajuste A2)

| Parágrafo | Conteúdo | Números iguais aos de |
|---|---|---|
| Dados | início, fim, registros e anos parciais; registros sinalizados, com a quantidade e a parcela | seção de cobertura; seção de qualidade |
| Conferências e limites | uma frase curta por conferência feita; frase geral: os dados abertos não informam a causa das paradas nem os eventos individuais | textos longos das mesmas conferências nas legendas |
| Fontes | conjuntos carregados, agrupados por identificador da usina e data de obtenção | legendas de fonte |

## 2. Regras gerais novas

### 2.1 `GLOSSARIO_RESUMO` (`src/comum/regras.py`)

Mapa sigla → explicação curta, igual para todas as usinas. O texto é aprovado pelo usuário nas tarefas.

| Sigla | Explicação (implementada; aprovação do usuário na T033) |
|---|---|
| EVT | energia vertida turbinável, a que a água vertida poderia ter gerado nas turbinas disponíveis |
| ONS | Operador Nacional do Sistema Elétrico |
| DISPF | disponibilidade das unidades geradoras apurada pelo ONS |
| TEIFa | taxa de indisponibilidade forçada apurada pelo ONS em 60 meses |
| TEIF | taxa de indisponibilidade forçada de referência, usada no cálculo da garantia física |
| TEIP | taxa de indisponibilidade programada apurada pelo ONS em 60 meses |
| UG | unidade geradora |
| GF | garantia física |
| Pinst | potência instalada |
| MWmed | megawatt médio, a energia dividida pelas horas do período |

A sigla é reconhecida como palavra, também seguida de algarismos (UG2). "TEIF" não casa com "TEIFa".

Os tipos da 006 acrescentam os seus termos, como "constrained-off" e CVU, quando as seções deles entrarem.

### 2.2 `COLUNAS_RESUMO_ANUAL` (`src/relatorio/resumo.py`)

Mapa caminho → cabeçalhos da tabela anual do relatório que entram no resumo, em ordem, com no máximo seis colunas.

| Caminho | Colunas |
|---|---|
| hidrelétrica com EVT | Ano, Disp. média (% Pinst), Fator de capacidade, Geração / GF, EVT (MWh), Horas parada c/ EVT |
| sem EVT (006) | declaradas nas tarefas, depois da fase A da 006, pela regra da decisão R6 |

Um cabeçalho do mapa que não exista na tabela é erro de programação: o teste da usina fictícia de cada caminho o acusa.

### 2.3 Limites (`src/comum/regras.py`)

| Constante | Valor | Requisito |
|---|---|---|
| `RESUMO_MAXIMO_PAGINAS` | 2 | FR-004 |
| `RESUMO_CORPO_PT` | 10 | FR-004 |
| `RESUMO_TABELA_PT` | 9 | FR-004 |
| `RESUMO_MAXIMO_PALAVRAS` | 1.000 (fora das tabelas; palavras separadas por espaço, sem as marcas de Markdown) | SC-004 |
| `RESUMO_MAXIMO_PALAVRAS_DADOS` | 250 | FR-013 com o ajuste A2 |

## 3. Conferências: texto curto (`src/relatorio/fontes.py`)

Cada conferência do mapa de `fontes.py` ganha um texto curto, montado com os mesmos resultados e os mesmos números do texto longo.

| Conferência | Texto longo (legenda, como hoje) | Texto curto (resumo) |
|---|---|---|
| geração | geração conferida com Geração por usina: 70.895 de 70.895 horas coincidentes (100,0%) | geração: 100,0% das horas coincidentes com a série oficial |
| disponibilidade | disponibilidade declarada conferida com Disponibilidade por usina (operacional): 70.895 de 70.895 horas coincidentes (100,0%) | disponibilidade: 100,0% das horas coincidentes |
| TEIFa e TEIP | … 21 de 21 meses reproduzidos (diferença máxima de 0,000 p.p.) | TEIFa e TEIP: 21 de 21 meses reproduzidos |
| DISPF × horas | … 4 divergências (meses-unidade), listadas na aba ONS_DIVERGENCIAS | DISPF e horas por estado operativo: 4 divergências (meses-unidade) |
| vazões | … 70.731 de 70.731 horas coincidentes (100,0%) | vazões: 100,0% das horas coincidentes |
| cadastro | … sem divergência | cadastro: sem divergência |

Conferência não feita nesta execução: o texto curto diz "não feita", como o longo. Os exemplos são da São Domingos; o código não tem número fixo.

## 4. Saídas da etapa 5

| Arquivo em `reports/<slug>/` | Situação |
|---|---|
| `relatorio_analise_estatistica.pdf`, `.md`, `perfil_estatistico_anual.xlsx`, `.csv`, `figures/` | sem mudança (FR-021) |
| `resumo_executivo.pdf` | novo: A4 retrato, no máximo duas páginas |
| `resumo_executivo.md` | novo: o mesmo conteúdo do PDF |

`caminhos.ARQUIVOS_RELATORIO` ganha as chaves `resumo_pdf` e `resumo_md`.

### 4.1 `etapa.json` do relatório

- **`arquivos`**: ganha os dois arquivos do resumo, com bytes e SHA-256.
- **`resumo`**: ganha a chave `resumo_executivo`:

| Campo | Exemplo |
|---|---|
| `paginas` | 2 |
| `evolucao_anual` | true; false quando omitida pela regra das duas páginas |
| `palavras` | 850, fora das tabelas |

O `versao_formato` do relatório continua 1 (decisão R14).

## 5. Referência da usina (`relatorios_referencia/<slug>/`)

| Item | Mudança |
|---|---|
| `resumo_executivo.pdf`, `resumo_executivo.md` | entram na referência quando o usuário aprova o resumo e o `referencia` é executado de novo (FR-020) |
| `referencia.json` | lista os dois arquivos, com bytes e SHA-256; o formato não muda |
| `comparar` | compara o PDF do resumo byte a byte e o Markdown byte a byte, como os do relatório; sem mudança de código |

## 6. Requisitos × entidades

| Requisito | Onde |
|---|---|
| FR-001, FR-002 | etapa 5 (`executar_relatorio`); decisões R2 e R3 |
| FR-003, FR-007 | `ResumoExecutivo` (1) |
| FR-004, FR-005, FR-006 | limites (2.3); regra das duas páginas (R10) |
| FR-008 | cabeçalho (1.1) |
| FR-009, FR-010 | `conclusao` e `aviso_secoes` (1) |
| FR-011 | `indicadores` (1) |
| FR-012 | `evolucao_anual` (1) e `COLUNAS_RESUMO_ANUAL` (2.2) |
| FR-013 | `sobre_os_dados` (1.2) e textos curtos (3) |
| FR-014, FR-015, FR-018 | origem de cada campo (1); verificação da decisão R11 |
| FR-016 | linhas de conjunto identificadas, como nas funções do relatório que o resumo reaproveita |
| FR-017 | `termos` (1) e `GLOSSARIO_RESUMO` (2.1) |
| FR-019 | `COLUNAS_RESUMO_ANUAL` por caminho; funções da capa e da conclusão por caminho (006) |
| FR-020, FR-021 | saídas (4) e referência (5) |
