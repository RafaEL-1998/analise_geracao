# Contract: Estrutura do Relatório (PDF e Markdown)

**Feature**: `008-relatorio-enxuto` | **Date**: 2026-10-06

## Capa (página 1 do PDF; início do Markdown)

1. Título: "UHE São Domingos — energia vertida turbinável e desempenho operacional".
2. Subtítulo: período, quantidade de registros horários e "Gerado em dd/mm/aaaa hh:mm".
3. Blocos "Identificação nos dados do ONS" e "Parâmetros técnicos da usina", cada um com a sua legenda de fonte.
4. Indicadores principais (mesmos rótulos e valores de hoje), com a nota da capa e a legenda de fonte.
5. "Sumário": as seções presentes, numeradas, na ordem do [data-model.md](../data-model.md), seção 1.
   - PDF: "<n>. <título> …… <página>".
   - Markdown: lista numerada, cada item com link para o título da seção.

Sem texto de constatação na capa nem no sumário.

## Seção

```text
<n>. <título>
**<título da constatação>.** <texto>        (0 ou mais, na ordem de res.achados)
<subtítulo, tabela, nota, legenda de fonte>  (como hoje)
<figura, legenda descritiva, legenda de fonte>
```

- Cada constatação aparece uma única vez no relatório (PDF e Markdown).
- Markdown, figura: `![<título da seção>](figures/<arquivo>.png)`, depois a legenda descritiva e a legenda de fonte, em parágrafos.

## Rodapé (PDF)

Só "Página X de Y", à direita. Sem frase de fontes e sem data.

## Cabeçalho das páginas (PDF, a partir da 2)

Como hoje: "UHE São Domingos — energia vertida turbinável (dados ONS) · <período>".

## Markdown

- Sem a linha `**Fontes**:` e sem a seção "Figuras".
- Seções com os mesmos títulos e na mesma ordem do PDF (`## <n>. <título>`).

## Comandos

Sem opção nova: `python -m src.analyzer` (Markdown, planilha e PDF) e `python -m src.pdf_generator`.
