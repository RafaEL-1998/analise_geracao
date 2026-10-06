# Data Model: Relatório Mais Enxuto

**Feature**: [spec.md](spec.md) · **Date**: 2026-10-06 · Decisões em [research.md](research.md)

## 1. Seção

| Campo | Conteúdo |
|---|---|
| `chave` | identificador estável (ex.: `cobertura`, `evt_mensal`) |
| `titulo` | título exibido, igual no PDF e no Markdown |
| `presente(res)` | condição de presença (ex.: indicadores do ONS só com `res.ons`) |

Ordem e condições (research R2):

| # | `chave` | `titulo` | Presente quando |
|---|---|---|---|
| 1 | `cobertura` | Fonte e cobertura dos dados | sempre |
| 2 | `cadastro` | Identificação da usina no cadastro do ONS | `res.cadastro` |
| 3 | `indicadores_anuais` | Indicadores anuais | sempre |
| 4 | `disponibilidade_geracao` | Disponibilidade e geração por ano | sempre |
| 5 | `indicadores_ons` | Indicadores oficiais do ONS por unidade geradora | `res.ons` |
| 6 | `serie_temporal` | Série temporal de disponibilidade, geração e EVT | sempre |
| 7 | `evt_mensal` | Energia vertida turbinável mensal | sempre |
| 8 | `perfil_horario` | Perfil horário da geração e da EVT | sempre |
| 9 | `eventos` | EVT por nível de geração e eventos de usina parada | sempre |
| 10 | `programacao` | Operação verificada e programação diária do ONS | `res.programacao` |
| 11 | `disponibilidade_sincronizada` | Disponibilidade operacional e sincronizada (ONS) | `res.disponibilidade` |
| 12 | `hidrologia` | Afluência, vertimento e nível do reservatório (ONS) | `res.hidrologia` |
| 13 | `geracao_zero` | Horas com geração zero por mês | sempre |
| 14 | `vazoes` | Vazões defluentes por ano | sempre |
| 15 | `geracao_oficial` | Conferência da geração com a série oficial (ONS) | `res.geracao_oficial` |
| 16 | `qualidade` | Qualidade dos dados | sempre |
| 17 | `notas` | Notas metodológicas e limitações | sempre |

A numeração exibida é a posição entre as seções presentes (1, 2, 3, … sem lacunas).

## 2. Constatação → seção

| Título da constatação | `chave` da seção |
|---|---|
| Cobertura dos dados | `cobertura` |
| Cadastro da usina no ONS | `cadastro` |
| Disponibilidade | `indicadores_anuais` |
| Indicadores oficiais de disponibilidade (ONS) | `indicadores_ons` |
| Estados operativos das unidades geradoras (ONS) | `indicadores_ons` |
| Indisponibilidades | `disponibilidade_geracao` |
| Geração e garantia física | `disponibilidade_geracao` |
| Energia vertida turbinável | `evt_mensal` |
| EVT e nível de geração | `eventos` |
| EVT com a usina parada | `eventos` |
| Programação diária do ONS | `programacao` |
| Disponibilidade sincronizada | `disponibilidade_sincronizada` |
| Afluência e vertimento | `hidrologia` |
| Horas com geração zero | `geracao_zero` |
| Concentração diurna | `perfil_horario` |
| Distribuição ao longo do ano | `evt_mensal` |
| Mudança de classificação do vertimento pelo ONS | `evt_mensal` |
| Conferência da geração | `geracao_oficial` |
| Qualidade dos dados | `qualidade` |

**Regras**:
- Dentro da seção, as constatações seguem a ordem de `res.achados`.
- Título fora do mapa, ou seção ausente: a constatação vai para `cobertura`, com aviso no log; nenhuma constatação desaparece (spec, casos de borda).
- Cada constatação aparece uma vez em cada saída (SC-001).

## 3. Sumário

Lista das seções presentes: `numero`, `titulo` e, no PDF, `pagina` (página em que o título da seção é desenhado). No Markdown, cada item é um link para o título da seção.

## 4. Conteúdo compartilhado pelo PDF e pelo Markdown (FR-014)

| Item | Função (no `analyzer`) | Hoje |
|---|---|---|
| Indicadores da capa (rótulo, valor, complemento) | `indicadores_capa(res)` | só no PDF |
| Legenda descritiva de cada figura | `legenda_figura(res, chave)` | só no PDF |
| Cobertura (pares chave-valor) | `pares_cobertura(res)` | só no PDF |
| Identificação e parâmetros técnicos (capa) | `pares_identificacao(res)`, `pares_parametros()` | só no PDF |
| Perfil diurno × noturno | `linhas_tabela_perfil_diurno(res)` | só no PDF |
| Regras de validação | `linhas_tabela_regras(res)` | só no PDF |
| Parâmetros utilizados | `linhas_tabela_parametros(res)` | só no PDF |
| Registros sinalizados | `linhas_tabela_registros_sinalizados(res)` | só no Markdown |
| Vazões e nível por hora do dia | `linhas_tabela_perfil_hidrologico(res)` (já existe) | só no Markdown |
| Eventos de indisponibilidade; EVT por nível de geração | versão do PDF (colunas a mais) | diferentes |

## 5. Notas sem a parte de fonte (FR-013)

| Onde | Sai | Fica |
|---|---|---|
| `notas_disponibilidade`, 1ª nota | "Fonte: conjunto Disponibilidade por usina do ONS (…), obtido em …." | "A disponibilidade operacional é a mesma informação …" |
| `notas_hidrologia`, 1ª nota | "Fonte: conjunto Dados hidrológicos horários do ONS (…), obtido em …." | "Os dados são informados pelos agentes e não são consistidos pelo ONS; …" |
| `secao_geracao_oficial_md` | nota "- Fonte: conjunto Geração por usina do ONS …" | critério de coincidência na nota da tabela |
| cadastro (Markdown e `nota_identificacao_cadastro`) | "Fonte: conjunto Modalidade das usinas do ONS (…)" | "Cadastro sem série histórica; as versões anteriores do arquivo ficam preservadas." |
