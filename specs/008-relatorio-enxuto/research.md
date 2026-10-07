# Research: Relatório Mais Enxuto

**Feature**: [spec.md](spec.md) · **Date**: 2026-10-06

Nenhum item ficou como NEEDS CLARIFICATION (decisões 1A e 2A do usuário já incorporadas à spec).

## R1. Estrutura única do relatório

- **Decisão**: módulo `src/estrutura_relatorio.py` com a lista ordenada das seções (chave, título, condição de presença sobre `ResultadosAnalise`) e o mapa título da constatação → chave da seção. As funções `secoes_presentes(res)` (com a numeração), `constatacoes_da_secao(res, chave)` e `sumario(res)` servem ao PDF e ao Markdown.
- **Motivo**: FR-005 e SC-008 exigem a mesma ordem e as mesmas constatações nas duas saídas; hoje cada gerador tem a sua ordem, e o Markdown tem seções diferentes das do PDF.
- **Alternativas**:
  - modelo de documento abstrato (parágrafos, tabelas, figuras) com dois renderizadores: rejeitado por ser uma reescrita grande às vésperas da fiscalização;
  - manter duas ordens e conferir por teste: rejeitado porque a divergência voltaria a cada mudança.

## R2. Ordem das seções (a do PDF atual)

A ordem atual do PDF é mantida, porque é a versão que o usuário lê e aprovou:

1. Fonte e cobertura dos dados
2. Identificação da usina no cadastro do ONS (com cadastro)
3. Indicadores anuais
4. Disponibilidade e geração por ano
5. Indicadores oficiais do ONS por unidade geradora (com indicadores)
6. Série temporal de disponibilidade, geração e EVT
7. Energia vertida turbinável mensal
8. Perfil horário da geração e da EVT
9. EVT por nível de geração e eventos de usina parada
10. Operação verificada e programação diária do ONS (com programação)
11. Disponibilidade operacional e sincronizada (ONS) (com disponibilidade)
12. Afluência, vertimento e nível do reservatório (ONS) (com hidrologia)
13. Horas com geração zero por mês
14. Vazões defluentes por ano
15. Conferência da geração com a série oficial (ONS) (com geração por usina)
16. Qualidade dos dados
17. Notas metodológicas e limitações

O Markdown passa a ter exatamente essa lista. As seções "Eventos de indisponibilidade total", "Maiores eventos de usina parada com EVT", "EVT por nível de geração", "Registros sinalizados" e "Extremos do período" deixam de ser seções próprias no Markdown e entram como subseções (tabelas com subtítulo) das seções 4, 9 e 16, como no PDF. A seção "Figuras" do Markdown deixa de existir.

## R3. Constatações nas seções

- **Decisão**: o mapa da tabela do Contexto da spec, pelo título da constatação (os títulos são fixos em `montar_achados`). Na seção, as constatações vêm logo depois do título, na ordem de `res.achados`, no formato "**Título.** texto", como hoje na lista.
- **Constatação sem seção presente**: vai para a primeira seção ("Fonte e cobertura dos dados"), com aviso no log. Um teste garante que todos os títulos possíveis estão no mapa.
- O PDF passa a mostrar no início da seção o título e o texto das constatações que hoje aparecem só no texto corrido (ex.: "Programação diária do ONS"), sem repeti-los mais abaixo.
- A seção "Principais constatações" sai do PDF e a "Constatações" sai do Markdown.

## R4. Sumário com página no PDF

- **Decisão**: `TableOfContents` do reportlab, montado com `multiBuild` (duas passagens). Um `SimpleDocTemplate` derivado avisa o índice no `afterFlowable` sempre que desenha um título de seção (estilo "secao").
- Estilo compacto (fonte de 8,5 pt, entrelinha de 11 pt), logo abaixo dos indicadores da capa. Se não couber na página 1, o restante flui para a página 2 (spec, casos de borda).
- O canvas numerado continua contando o total de páginas em cada passagem; o rodapé fica só com "Página X de Y".
- **Alternativas**: sumário sem páginas, rejeitado porque a spec pede a página no PDF (FR-003); índice em duas colunas montado à mão, que fica como recurso se o sumário passar da página 1.

## R5. Capa e cabeçalho

- **PDF**: o subtítulo da capa ganha "Gerado em dd/mm/aaaa hh:mm". O cabeçalho das páginas 2 em diante continua (nome da usina e período).
- **Markdown**:
  - cabeçalho atual, menos a linha `**Fontes**:` e mais `**Gerado em**: dd/mm/aaaa hh:mm`;
  - os indicadores da capa numa tabela "Indicadores principais", com os mesmos rótulos e valores do PDF e a sua legenda de fonte (`tab_capa_indicadores`);
  - depois, o "Sumário", em lista numerada com links para as seções.
- O texto dos indicadores da capa passa para uma função compartilhada (`indicadores_capa(res)` no `analyzer`), usada pelos dois geradores.

## R6. Figuras e tabelas iguais nos dois (FR-014)

- **Figuras**: no Markdown, cada figura vai para o corpo da sua seção, com `![título](figures/<arquivo>.png)`, a legenda descritiva (a mesma do PDF, gerada por `legenda_figura(res, chave)` no `analyzer`) e a legenda de fonte.
- **Tabelas que só existem no PDF** e passam ao Markdown: cobertura (pares chave-valor), identificação e parâmetros técnicos (capa), indicadores da capa, perfil diurno × noturno, regras de validação e parâmetros utilizados.
- **Tabelas que só existem no Markdown** e passam ao PDF: registros sinalizados (resumo por regra) e vazões e nível por hora do dia (hidrologia).
- **Tabelas com colunas diferentes** entre PDF e Markdown (eventos de indisponibilidade, EVT por nível de geração): fica a versão do PDF nos dois, que tem as colunas a mais. Os números das colunas comuns não mudam.
- O mapa de fontes da spec 007 já tem as chaves dessas tabelas; o `tab_hidrologia_perfil` passa a ser usado também no PDF.

## R7. Notas de fonte das bases novas (FR-013)

- **Disponibilidade** (primeira nota): sai "Fonte: conjunto … obtido em …."; fica "A disponibilidade operacional é a mesma informação da disponibilidade declarada da base de EVT; a sincronizada indica a capacidade das unidades ligadas à rede."
- **Hidrologia** (primeira nota): sai a parte da fonte; fica a ressalva a partir de "Os dados são informados pelos agentes e não são consistidos pelo ONS; …".
- **Geração**: sai a nota "- Fonte: conjunto Geração por usina …"; o critério "coincidência = diferença de até 0,01 MW na mesma hora" já está na legenda da tabela (PDF) e passa à nota da tabela no Markdown.
- **Cadastro**: "Fonte: conjunto Modalidade das usinas do ONS (cadastro sem série histórica; …)" vira "Cadastro sem série histórica; as versões anteriores do arquivo ficam preservadas.", no PDF e no Markdown.
- As fontes continuam nas legendas (spec 007) e na relação completa das Notas metodológicas.

## R8. Não regressão (SC-005)

O script de comparação muda de "seção a seção" para "conteúdo a conteúdo":
- cada tabela do relatório anterior está no novo, com as mesmas linhas (na versão do PDF, nas tabelas da R6);
- cada constatação, com o mesmo texto, aparece uma vez;
- cada parágrafo e nota do relatório anterior está no novo, exceto os removidos pela FR-013, comparados na forma nova;
- a planilha (57 abas) idêntica célula a célula;
- as 8 figuras com o mesmo SHA-256.

## R9. Paginação do PDF (decidida na implementação, com a base real)

Com as constatações no início das seções, figuras e tabelas passaram a não caber depois delas e saltavam para a página seguinte, deixando até 400 pt em branco. O PDF ficou com 33 páginas, e o sumário de 17 seções não cabia na capa. Decisões, todas de leiaute, sem mudar números, textos nem os PNG das figuras:
- **Capa**: sumário em duas colunas e quebra de página depois dele; a capa ocupa só a página 1 (SC-002).
- **Figuras**: desenhadas no PDF com no máximo 285 pt de altura (`ALTURA_MAXIMA_FIGURA`), para caberem numa página com o título e as constatações da seção, e mantidas juntas deles.
- **Tabelas**: até 12 linhas ficam inteiras. As mais longas começam na página corrente se o subtítulo e 6 linhas couberem, e continuam na seguinte com o cabeçalho repetido.
- **Abertura da seção**: título e constatações sempre juntos. Até 150 pt, ficam também com o primeiro bloco; acima disso, podem ficar no pé da página, com a tabela na seguinte.
- **Resultado**: 30 páginas (31 no relatório anterior).

## R10. Ficha do cadastro na capa (revisão de 07/10/2026, FR-015)

- **Decisão**: bloco próprio "Cadastro no ONS" entre a identificação e os parâmetros, os três lado a lado na capa do PDF (no Markdown, três tabelas em sequência), cada um com a sua legenda de fonte e conferência. Sem o cadastro carregado, a capa fica com os dois blocos de antes.
- **Por quê**: cada bloco mantém a legenda da spec 007 sem misturar conjuntos (Energia Vertida Turbinável, Modalidade das usinas e parâmetros do projeto); a conferência do cadastro com os parâmetros continua na legenda do bloco.
- **Alternativa descartada**: fundir os itens do cadastro no bloco de identificação. A legenda passaria a misturar dois conjuntos, e a coluna da esquerda ficaria com o dobro das linhas da direita, alongando a capa.
- **Sem a nota abaixo da ficha**: a ressalva "cadastro sem série histórica" já está nas Notas metodológicas; a divergência, quando houver, aparece na constatação (seção "Fonte e cobertura dos dados") e na legenda de conferência do bloco.

## R11. Figuras maiores e padronizadas (revisão 2, 07/10/2026, FR-016)

- **Antes**: as figuras 01 e 02 eram geradas com 11 × 5,0 polegadas e as 05 e 06 com 11 × 4,6; no PDF, a altura máxima de 285 pt (R9) as deixava com 627 e 682 pt de largura, de 770 pt úteis.
- **Decisão**: as quatro passam a 11 × 4,3 polegadas (mesma proporção) e, no PDF, são desenhadas na largura útil (cerca de 760 × 297 pt), fora do limite de altura da R9, que continua valendo para as demais figuras.
- **Por quê**: 4,3 polegadas é a maior altura com a qual a seção de EVT mensal (título, três constatações, figura e legendas) ainda cabe numa página.
