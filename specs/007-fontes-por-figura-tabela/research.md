# Research: Fonte Explícita em Cada Figura e Tabela do Relatório

**Feature**: [spec.md](spec.md) · **Date**: 2026-10-06

Nenhum item do contexto técnico ficou como NEEDS CLARIFICATION. Abaixo, as decisões de projeto com base no código atual.

## R1. Mapa de fontes único e declarativo

- **Decisão**: módulo novo `src/fontes_relatorio.py` com três tabelas declarativas: os conjuntos, as conferências e o mapa chave → (conjuntos, conferências, dados sem outra fonte, cálculo do relatório). As funções de texto recebem `ResultadosAnalise` e a chave.
- **Motivo**: FR-008 exige que PDF, Markdown e planilha não divirjam. Hoje o Markdown e o PDF montam as tabelas em funções diferentes (`secao_*_md` e `_secao_*`); um mapa único evita duplicar textos.
- **Alternativas**: texto escrito em cada seção, rejeitado por repetir a informação três vezes e por deixar resultados fixos (FR-006); campo novo em cada função `linhas_tabela_*`, rejeitado porque mistura conteúdo de tabela com rastreabilidade e mudaria assinaturas usadas em testes.

## R2. Chaves estáveis

- **Decisão**: as figuras usam as chaves já existentes em `NOMES_FIGURAS` e `NOMES_FIGURAS_OPCIONAIS` (ex.: `serie_temporal`, `disponibilidade_sincronizada`). As tabelas ganham chaves novas com prefixo `tab_` (ex.: `tab_indicadores_anuais`, `tab_faixas_afluencia_evt`), e os blocos do PDF o prefixo `bloco_` (ex.: `bloco_identificacao`, `bloco_cadastro`). As abas usam o próprio nome.
- **Motivo**: as chaves das figuras já ligam o gerador de gráfico ao PDF e ao Markdown.

## R3. Datas de obtenção

- **Decisão**: ler uma vez, ao montar `ResultadosAnalise`, a data mais recente de registro (`registrado_em_utc`) de cada manifesto:
  - raiz de `data/raw` para a EVT;
  - `data/raw/indicadores_ons/<conjunto>` para os 4 conjuntos de indicadores;
  - `data/raw/programacao_diaria`;
  - as 4 pastas da spec 006, já lidas hoje por `data_obtencao`.
  Guardar em `res.fontes["obtencao"]`. Sem registro: "data de obtenção não registrada".
- **Motivo**: a função `data_obtencao` do motor comum já faz isso; vale para todas as pastas, porque o manifesto tem o mesmo formato (spec 005).

## R4. Conjuntos carregados e N do rodapé

- **Decisão**: um conjunto conta como carregado quando os seus dados entraram no `ResultadosAnalise`:
  - EVT: sempre;
  - indicadores: os 4 quando `res.ons` não está vazio;
  - programação: `res.programacao`;
  - disponibilidade, hidrologia, geração e cadastro: os campos da spec 006.
  N é o total. Os parâmetros do projeto não são conjunto do ONS e não entram em N.
- **Motivo**: FR-009 pede N calculado das bases carregadas, e não dos manifestos existentes.

## R5. Conferências citadas (decisão A: só as refeitas pelo pipeline)

| Id | Conferência | Origem do resultado |
|---|---|---|
| `geracao` | geração da EVT × Geração por usina | `res.geracao_oficial["conferencia"]` |
| `disponibilidade` | disponibilidade declarada da EVT × Disponibilidade por usina (operacional) | `res.disponibilidade["conferencia"]` |
| `vazoes` | vazões turbinada e vertida da EVT × Dados hidrológicos | `res.hidrologia["alinhamento"]` |
| `teifa_teip` | TEIFa e TEIP recalculadas × publicadas | recálculo com `recalcular_taxas` (indicadores_ons) sobre os indicadores já carregados, guardado em `res.ons["recalculo"]` |
| `dispf_horas` | DISPF × horas por estado operativo | `res.ons["divergencias"]` |
| `cadastro` | potência e estado do cadastro × parâmetros do projeto | `res.cadastro["divergencias"]` |

- O texto traz a contagem e a proporção (ex.: "70.895 de 70.895 horas coincidentes (100,0%)"), ou a quantidade de divergências e a aba onde estão listadas.
- Base ausente: "conferência com <conjunto> não feita nesta execução" (FR-005).
- O recálculo da TEIFa/TEIP é feito na camada de análise, sobre dados já carregados; não há leitura de arquivo bruto.

## R6. Formato da legenda

- **Decisão**: uma linha logo abaixo da tabela ou da legenda da figura:
  - `Fonte dos dados: <conjunto (identificador), obtido em dd/mm/aaaa>; … Conferência: <texto>; … Sem outra fonte para conferir: <dados>.`
  - Cálculo do relatório: `Calculado neste relatório a partir de: …`.
  - Parâmetros do projeto: `Parâmetros do projeto (origem na tabela de parâmetros)`.
- **Motivo**: um prefixo fixo ("Fonte dos dados:") permite à não regressão ignorar só essas linhas e a um teste contar as legendas. As notas existentes, como "- Fonte: conjunto …" nas seções da spec 006, não mudam.

## R7. Rodapé e cabeçalho

- **Decisão**:
  - rodapé: `Fontes: ONS – Dados Abertos, N conjuntos; fonte de cada figura e tabela na legenda; relação completa nas Notas metodológicas. Gerado em dd/mm/aaaa hh:mm.`;
  - Markdown: a mesma frase numa linha `**Fontes**:` do cabeçalho;
  - sai a "publicação mais recente" do rodapé atual, que só valia para a EVT; as datas de cada base ficam nas legendas e nas notas.
- **Motivo**: FR-009 e FR-010.

## R8. Aba FONTES

- **Decisão**: aba `FONTES`, a última da planilha, com as colunas `aba`, `conjuntos_origem`, `conferencias`, `sem_outra_fonte` e `calculado_no_relatorio`, uma linha para cada aba exportada. O mapa das abas usa prefixos (`ONS_`, `PROG_`, `DISP_`, `HID_`, `GER_`, `CAD_`) e nomes para as abas da EVT. Aba sem entrada gera aviso no log e aparece com "origem não mapeada", o que um teste impede.
- **Motivo**: FR-011 e US3/AC2. Acrescentar a aba no fim não muda a ordem nem o conteúdo das 56 atuais.

## R9. Garantia de cobertura (SC-001 e SC-002)

- **PDF**: o gerador conta as tabelas e figuras desenhadas e as legendas emitidas. Um teste exige que os dois números sejam iguais, com todas as bases e sem as bases novas.
- **Markdown**: um teste exige que toda tabela (linha `| --- |`) seja seguida, antes da próxima seção ou tabela, de uma linha "Fonte dos dados:", e que cada figura listada tenha a sua.
- **Mapa**: um teste confere que toda chave usada pelo PDF e pelo Markdown existe no mapa e que todo conjunto citado existe no catálogo.
- **SC-002** (correção do conteúdo): conferência manual do mapa contra o código de cada seção, registrada em `tasks.md`.

## R10. Não regressão

- **Decisão**: o script de não regressão da spec 006 passa a ignorar as linhas que começam com "Fonte dos dados:" e a linha `**Fontes**:` do cabeçalho; a aba `FONTES` entra como aba nova. Todo o resto continua comparado com o relatório atual.
