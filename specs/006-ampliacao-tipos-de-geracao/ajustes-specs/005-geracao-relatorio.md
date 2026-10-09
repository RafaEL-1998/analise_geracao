# Ajustes à spec da Geração do relatório — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/005-geracao-relatorio/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec da Geração do relatório (a partir da FR-041). O contrato [cli-referencias.md](../contracts/cli-referencias.md) passa a ser desta spec na incorporação.

## Requisitos alterados

- **Estrutura** (seções, sumário e numeração):
  - **hidrelétrica com EVT**: exatamente as 17 seções de hoje, na ordem de hoje, com os mesmos títulos;
  - **usina sem EVT**: as seções da tabela da FR-041, com numeração contínua; seção sem base é omitida, com o motivo nas notas.
- **Capa e título**:
  - **hidrelétrica com EVT**: como hoje; a modalidade já vem da ficha do cadastro;
  - **usina sem EVT**: o título "<nome> — desempenho operacional", a linha de tipo e modalidade no bloco de identificação, os parâmetros do tipo e os indicadores da capa do tipo.
- **Legendas**: citam o identificador da usina, como hoje. Num dado de conjunto ou de agregado, citam o identificador dele com o nível escrito, por exemplo "(conjunto de usinas, id ONS CJU_…)". As datas de obtenção vêm das Análises, que as leem da Coleta.
- **Planilha**: as abas DICIONARIOS e FONTES listam só os conjuntos da usina. Na hidrelétrica com EVT, os dez de hoje, na mesma ordem.
- **Notas**: nas usinas sem EVT, entram as omissões, os níveis dos dados e as conferências não aplicáveis. Na hidrelétrica com EVT, as notas de hoje, sem parágrafo novo.
- **`comparar`** (US8): ganha o modo `--todas [--coleta]` (FR-043).

## Requisitos novos

- **FR-041** (seções da usina sem EVT): nesta ordem, conforme a cobertura:
  1. fonte e cobertura dos dados;
  2. indicadores anuais;
  3. disponibilidade e geração por ano;
  4. indicadores oficiais do ONS por unidade geradora;
  5. série temporal da geração e da disponibilidade;
  6. geração mensal e sazonalidade;
  7. perfil horário da geração;
  8. seções do tipo (fases B a D);
  9. programação diária × verificada;
  10. disponibilidade operacional e sincronizada;
  11. afluência, vertimento e nível do reservatório (hidrelétrica sem EVT, com hidrologia);
  12. conferência da geração entre fontes;
  13. qualidade dos dados;
  14. conclusão;
  15. notas metodológicas e limitações.
- **FR-042** (relatórios de referência): `python -m src referencia --usina <slug> --data-geracao "DD/MM/AAAA HH:MM" --aprovado-em "DD/MM/AAAA"` DEVE registrar o relatório aprovado em `relatorios_referencia/<slug>/`:
  - **conteúdo**: os arquivos do relatório; o perfil (`perfil.toml`); a Coleta congelada (só os arquivos do `etapa.json` dela, sem `.bak`); o `referencia.json` com `usina`, `data_geracao`, `aprovado_em`, `periodo`, `arquivos`, `perfil` e `coleta` (SHA-256);
  - **gravação**: numa pasta temporária, conferida antes da troca;
  - **recusa**: substituir uma referência ainda não commitada;
  - **git**: o relatório e o perfil entram no git, inclusive o PDF; a Coleta congelada não.
- **FR-043** (`comparar --todas [--coleta]`):
  - para cada referência, DEVE refazer o Tratamento, a Conferência, as Análises e o Relatório num espaço isolado, a partir da Coleta e do perfil congelados, com a data do `referencia.json`, e comparar com o relatório aprovado;
  - avisa, sem o código 6, quando o perfil atual difere do congelado;
  - não muda `data/usinas/`, `reports/` nem `data/raw/`;
  - com `--coleta`, refaz também a Coleta com `--sem-portal` e compara as séries no período da referência e as contagens das auditorias, sem as colunas de execução; `dicionarios.csv` e `datas_obtencao.csv` só como informação;
  - códigos: 0 sem diferença, 1 erro, 2 opção inválida, 6 com diferença.

## Aplicabilidade por tipo (fase A)

| Elemento | Hidrelétrica com EVT | Usinas sem EVT |
|---|---|---|
| Estrutura, capa, título e notas | como hoje | FR-041 e "Capa e título" |
| Legendas | como hoje | com o nível quando o dado é de conjunto ou de agregado |
| Conclusão | C1 a C11 e a nota de hoje | regras do tipo e nota gerada do catálogo |

## Critérios de sucesso (acréscimos)

- **SC-013**: as hidrelétricas com EVT passam nos testes dos invariantes da decisão R29 do research da spec 006.
- **SC-014**: `comparar --todas --coleta` dá código 0 no fim de cada fase da ampliação.

## Decisões do usuário (acréscimo)

| Data | Decisão |
|---|---|
| 09/10/2026 | Ampliação para todos os tipos de usina (spec 006, aprovada). Relatórios aprovados guardados com a Coleta e o perfil congelados e comparados num espaço isolado. |
