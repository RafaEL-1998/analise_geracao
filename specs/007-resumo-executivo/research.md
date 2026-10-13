# Research: Resumo Executivo do Relatório de Desempenho

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Data**: 2026-10-13

**Fontes**:
- código atual (`src/relatorio/`, `src/comum/comparacao.py`, `src/comum/referencias.py`, `src/pipeline.py`);
- relatório de referência da São Domingos (`relatorios_referencia/sao_domingos/`, gerado em 07/10/2026);
- spec, plano, data-model e tarefas da 006, que refazem a estrutura e a capa do relatório na fase A;
- protótipo descartável do resumo da São Domingos, montado com as funções atuais do relatório e medido em 13/10/2026 (fora do projeto, na pasta temporária da sessão).

**Numeração**: R1 a R14 são as decisões deste plano. Não confundir com as regras de validação física R1 a R9 do Tratamento nem com as decisões R1 a R30 da 006. No tasks.md, escrever "decisão Rn (007)" quando houver risco de confusão.

## Medição do protótipo

O protótipo montou o resumo da São Domingos com as funções do relatório completo: `listas_conclusao`, `indicadores_capa` e `linhas_tabela_anual`. Usou A4 retrato e as margens do relatório. O texto de "Sobre os dados" era provisório, com cerca de 150 palavras.

| Corpo do texto | Corpo das tabelas | Páginas | Altura ocupada das duas páginas | Palavras fora das tabelas |
|---|---|---|---|---|
| 10 pt | 9 pt | 2 | 81% | 783 |
| 11 pt | 9 pt | 2 | 90% | 783 |
| 10 pt | 7,3 pt (o do relatório) | 2 | 77% | 783 |

- A conclusão da São Domingos tem 19 itens (5, 4, 5 e 5), um a menos que o máximo de 20 (cinco por lista). Ela ocupa quase toda a primeira página.
- Com 10 pt e 9 pt, sobram 19% das duas páginas. O 20º item ocupa cerca de 3%, e as fontes completas de "Sobre os dados" (R7), cerca de 5%. O caso mais longo previsto fica perto de 89%.

## Decisões

### R1. Spec de mudança temporária, incorporada à spec 005

- **Decisão**: manter a 007 como spec de mudança temporária. Ao concluir, os requisitos passam para `specs/005-geracao-relatorio/`, e a pasta da 007 é excluída.
- **Motivo**: o usuário pediu uma spec. A spec temporária deixa a mudança revisável à parte e chega ao mesmo estado final. Com a resposta à Q1, a mudança ficou restrita à Geração do relatório e à constituição: as Análises não mudam.
- **Alternativa rejeitada**: editar a spec 005 diretamente. O resultado é o mesmo, mas a revisão fica misturada com a spec inteira da etapa.

### R2. O resumo é gerado dentro da etapa 5, depois do PDF do relatório

- **Decisão**: `executar_relatorio` gera o resumo na mesma pasta temporária das demais saídas, depois do PDF do relatório completo, porque o resumo cita o número de páginas dele. O resumo entra na conferência no disco e na troca das saídas. Se o resumo falhar, nenhuma saída nova substitui as anteriores.
- **Motivo**: cumpre FR-001 e o caso de borda "Relatório gerado de novo". O resumo e o relatório têm sempre a mesma data, o mesmo período e o mesmo `etapa.json`.
- **Alternativa rejeitada**: uma etapa ou um comando próprio. O resumo poderia ficar ao lado de um relatório de outra execução, e o manifesto da etapa deixaria de listar todas as saídas.

### R3. "Gerar à parte" é executar só a etapa 5

- **Decisão**: `python -m src relatorio --usina <slug>` gera o relatório e o resumo a partir dos resultados gravados, sem refazer as etapas 1 a 4. Não haverá comando que gere só o resumo.
- **Motivo**: um resumo gerado sozinho precisaria conferir se o relatório ao lado veio dos mesmos resultados, com a mesma data. Isso duplicaria a lógica do manifesto para um ganho pequeno: a etapa 5 sozinha já não refaz as anteriores.
- **Ajuste na spec (A1, depende de aprovação)**: o cenário 4 da US1 e a FR-002 passam a dizer "executar só a Geração do relatório" no lugar de "pedir só o resumo".

### R4. Conclusão igual por construção

- **Decisão**: o bloco de conclusão usa as mesmas funções e frases do relatório completo: `listas_conclusao(res)`, `FRASE_ABERTURA_CONCLUSAO` e `FRASE_CONCLUSAO_VAZIA`. Os números de seção citados nos itens saem de `secoes_presentes(res)`, os mesmos do relatório.
- **Motivo**: FR-009 e SC-002. Copiar o texto do Markdown do relatório criaria uma dependência de formato. Chamar as mesmas funções garante o mesmo texto e o mesmo limite de cinco itens por lista.
- **Verificação**: teste que compara, caractere por caractere, o bloco do resumo em Markdown com a seção de conclusão do relatório em Markdown.

### R5. Indicadores-chave = indicadores da capa

- **Decisão**: a tabela usa `indicadores_capa(res)`, com as colunas Indicador, Valor e Detalhe. A coluna Detalhe já traz a referência e a comparação, com o mesmo texto da capa. A nota da capa não entra; o que ela explica sobre as fontes está em "Sobre os dados".
- **Motivo**: FR-011 e FR-014: mesmos números e mesmo texto. Depois da fase A da 006, `indicadores_capa` passa a ter os indicadores de cada caminho, e o resumo os acompanha sem mudança.

### R6. Evolução anual = colunas escolhidas da tabela anual do relatório

- **Decisão**: o resumo escolhe colunas da tabela anual do relatório pelo cabeçalho, conforme um mapa declarado por caminho (`COLUNAS_RESUMO_ANUAL`). Os valores são os mesmos textos da tabela, com o "*" dos anos parciais. Hidrelétrica com EVT: Ano, Disp. média (% Pinst), Fator de capacidade, Geração / GF, EVT (MWh) e Horas parada c/ EVT.
- **Caminho sem EVT**: as colunas são declaradas nas tarefas, depois que a fase A da 006 definir a tabela anual da base horária comum. Regra da escolha: Ano e até cinco colunas, com a disponibilidade, o fator de capacidade, a geração ÷ garantia física (quando o tipo tem garantia física) e o principal indicador de perda do tipo (energia cortada nas eólicas e solares, horas disponíveis sem despacho nas térmicas).
- **Nota da tabela**: "* Ano parcial." e a seção de origem no relatório completo. As definições das colunas ficam na linha de termos (R8).
- **Motivo**: FR-012 e FR-014. Escolher colunas da tabela pronta evita formatar os números de novo.

### R7. "Sobre os dados" com fontes e conferências completas, em texto curto

- **Decisão**: o bloco é montado a partir dos resultados, em três parágrafos:
  1. **dados**: cobertura (início, fim, registros e anos parciais) e registros sinalizados (quantidade e parcela, os mesmos da seção de qualidade);
  2. **conferências e limites**: uma frase curta por conferência feita, gerada pelo mapa de conferências de `fontes.py` com os mesmos números do texto longo; uma frase geral sobre o que os dados abertos não informam (causa das paradas e eventos individuais);
  3. **fontes**: os conjuntos carregados, agrupados por identificador da usina e data de obtenção.
- **Motivo**: a emenda 3.1.0 (VII) aceita um bloco único no lugar das legendas, com as mesmas informações de fonte e de conferência. Na São Domingos, isso dá cerca de 14 linhas a 10 pt, ou 220 palavras, e o resumo ainda cabe em duas páginas (medição acima).
- **Ajuste na spec (A2, depende de aprovação)**: a FR-013 limita o bloco a "quatro linhas", o que não comporta os identificadores, as datas e as conferências exigidos pela constituição. Proposta: "no máximo 250 palavras".
- **Alternativa rejeitada**: citar só "ver as legendas do relatório completo". Não atende a constituição 3.1.0.

### R8. Linha de termos no cabeçalho, a partir de um glossário declarado

- **Decisão**: um glossário nas regras gerais (`GLOSSARIO_RESUMO`, em `src/comum/regras.py`) explica as siglas e grandezas: EVT, DISPF, TEIFa, TEIP, UG, GF, Pinst e MWmed. O cabeçalho traz só os termos que aparecem no resumo, na ordem da primeira ocorrência. O texto do glossário é aprovado pelo usuário nas tarefas, como as demais regras gerais.
- **Motivo**: FR-017. A conclusão é copiada igual e usa siglas sem explicação. Com a linha de termos antes dela, o diretor lê a conclusão já sabendo o que cada sigla significa.

### R9. Página e tipografia

- **Decisão**: A4 retrato, com as margens do relatório (laterais de 36 pt, superior de 50 pt e inferior de 42 pt), a mesma fonte (Arial, ou DejaVu Sans sem Arial), as mesmas cores e o mesmo rodapé com a numeração. Texto em 10 pt com entrelinha de 13 pt; tabelas em 9 pt.
- A conclusão não fica num bloco indivisível, como no relatório, porque isso a empurraria inteira para a segunda página. Cada título de lista fica junto do primeiro item.
- **Motivo**: FR-004 e o protótipo, que ocupa 81% das duas páginas com esses corpos.
- **Reuso**: `_registrar_fontes`, `_canvas_numerado` e as cores de `pdf.py`, importados sem alterar o PDF do relatório.

### R10. Regra das duas páginas e reprodutibilidade

- **Decisão**:
  1. gerar o PDF e contar as páginas (`paginas_do_pdf`);
  2. com mais de duas páginas, gerar de novo sem a evolução anual, com a frase de remissão à seção;
  3. ainda com mais de duas, levantar erro: a etapa termina com código 1, e nenhuma saída é trocada.

  O Markdown é gerado depois dessa decisão, para ter o mesmo conteúdo do PDF. Com `--data-geracao`, o PDF do resumo usa o modo invariante, como o do relatório, e sai igual byte a byte.
- **Motivo**: FR-006 e o princípio IX: o `comparar` confere o PDF byte a byte.

### R11. Verificações automáticas

| Verificação | Requisito |
|---|---|
| Conclusão do resumo igual à seção de conclusão do relatório, em Markdown | FR-009, SC-002 |
| Todo número do resumo presente no Markdown do relatório; única exceção, o número de páginas do relatório no cabeçalho | FR-014, SC-003 |
| No máximo duas páginas, nenhuma imagem no PDF e no máximo duas tabelas no Markdown | FR-004, FR-005, SC-001 |
| No máximo 1.000 palavras fora das tabelas | SC-004 |
| Ordem dos blocos e o mesmo conteúdo no PDF e no Markdown (ambos montados do mesmo objeto, com os blocos emitidos registrados pelo gerador do PDF) | FR-003, FR-007 |
| Conclusão longa: a evolução anual é omitida; conclusão ainda mais longa: erro e nada gravado | FR-006 |
| Nenhum termo de parecer fora da conclusão; nenhuma constante de usina no código (`test_literais.py`) | FR-015, constituição II |
| Conclusão vazia: a frase do relatório | caso de borda |

### R12. Referência da São Domingos

- **Decisão**:
  1. Depois da implementação, `comparar --todas` deve acusar exatamente duas diferenças: `resumo_executivo.pdf` e `resumo_executivo.md`, "só na pasta atual". O relatório completo e a planilha ficam sem diferença (FR-021).
  2. Com a aprovação do resumo pelo usuário, `referencia` registra de novo a São Domingos, já com os dois arquivos (FR-020). O `referencia.json` lista os arquivos a partir do `etapa.json` do relatório, então não precisa mudar.
- **Pré-requisito**: o `referencia` recusa substituir uma referência não commitada. A referência atual, alterada pela fase A da 006, precisa estar commitada antes.
- **Invariantes da 006**: a fotografia `invariantes_uhe.json` não inclui a lista de arquivos do relatório e não muda.

### R13. Ordem em relação à 006

- **Decisão**: o código da 007 começa depois do portão do fim da fase A da 006 (T074). O plano e as tarefas podem ser feitos antes.
- **Motivo**: as tarefas T064 a T066 da 006 mudam a estrutura, a capa, as legendas e a conclusão por caminho. O resumo chama essas funções pelo nome e acompanha as mudanças. Começar antes faria a 007 ser refeita, e o `comparar` da fase A ficaria com as diferenças do resumo misturadas.

### R14. Sem dependência nova e sem mudança de formato da etapa

- **Decisão**: o resumo usa o `reportlab`, que já está em `requirements.txt`. O `VERSAO_FORMATO` do relatório continua 1: nenhuma etapa lê o manifesto do relatório, e o `referencia` só lê a lista de arquivos, que ganha dois itens.
- O resumo do `etapa.json` ganha `resumo_executivo` com as páginas, a presença da evolução anual e as palavras fora das tabelas.
