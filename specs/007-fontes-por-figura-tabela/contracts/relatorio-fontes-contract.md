# Contract: Legendas de Fonte, Rodapé e Aba FONTES

**Feature**: `007-fontes-por-figura-tabela` | **Date**: 2026-10-06

## Legenda de fonte (PDF e Markdown)

Uma linha logo abaixo de cada tabela, bloco ou figura (no PDF, depois da legenda descritiva da figura; no Markdown, depois da nota da tabela ou do item da figura na seção "Figuras"):

```text
Fonte dos dados: <conjunto> (<identificador>), obtido em <dd/mm/aaaa>; <conjunto> (...). Conferência: <dado> conferido com <conjunto>: <resultado>; ... Sem outra fonte para conferir: <dados>.
```

- **Resultado da conferência**:
  - "<coincidentes> de <comuns> horas coincidentes (<pct>%)";
  - ou "<n> divergências, listadas na aba <ABA>";
  - ou, para TEIFa/TEIP, "<m> de <n> meses reproduzidos (diferença máxima de <x> p.p.)".
- **Base ausente**: "conferência com <conjunto> não feita nesta execução".
- **Cálculo do relatório**: a primeira parte vira "Calculado neste relatório a partir de: <conjuntos>".
- **Parâmetros do projeto**: "parâmetros do projeto (origem na tabela de parâmetros)".
- **Data sem registro**: "data de obtenção não registrada".
- Números formatados como no restante do relatório (separador de milhar ".", decimal ",").

## Rodapé das páginas do PDF

```text
Fontes: ONS – Dados Abertos, <N> conjuntos; fonte de cada figura e tabela na legenda; relação completa nas Notas metodológicas. Gerado em <dd/mm/aaaa hh:mm>.
```

N = conjuntos carregados ([data-model.md](../data-model.md), seção 1). Com N = 1: "1 conjunto".

## Cabeçalho do Markdown

Linha nova após as linhas atuais do cabeçalho:

```text
**Fontes**: ONS – Dados Abertos, <N> conjuntos; fonte de cada figura e tabela na legenda; relação completa nas notas metodológicas.
```

## Aba FONTES da planilha

| Coluna | Conteúdo |
|---|---|
| `aba` | nome da aba |
| `conjuntos_origem` | conjuntos com identificador e data de obtenção, separados por "; " |
| `conferencias` | textos das conferências com resultado, ou "—" |
| `sem_outra_fonte` | dados sem outra fonte para conferir, ou "—" |
| `calculado_no_relatorio` | "sim" ou "não" |

Uma linha para cada aba exportada, na ordem da planilha; a aba `FONTES` é a última.

## Comandos

Sem opção nova: `python -m src.analyzer` (Markdown, planilha e PDF) e `python -m src.pdf_generator` aplicam o contrato.
