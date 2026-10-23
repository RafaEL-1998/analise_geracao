# Ajustes à spec da Geração do relatório — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/005-geracao-relatorio/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec da Geração do relatório (a partir da FR-041). O contrato [cli-referencias.md](../contracts/cli-referencias.md) passa a ser desta spec na incorporação.

## Requisitos alterados

- **Estrutura** (seções, sumário e numeração):
  - **hidrelétrica com EVT**: exatamente as 17 seções de hoje, na ordem de hoje, com os mesmos títulos;
  - **usina sem EVT**: as seções da tabela da FR-041, com numeração contínua; seção sem base é omitida, com o motivo nas notas.
- **Capa e título**:
  - **hidrelétrica com EVT**: como hoje; a modalidade já vem da ficha do cadastro;
  - **usina sem EVT**: o mesmo título da capa da hidrelétrica com EVT aprovada em 19/10/2026 ("<nome> — Análise do desempenho operacional", que não cita a EVT), a linha de tipo e modalidade e o agente atual das unidades (Capacidade de geração, sem o histórico; decisão do usuário de 19/10/2026) no bloco de identificação, os parâmetros do tipo e os indicadores da capa do tipo.
- **Conclusão**: a mesma seção nos dois caminhos; sem itens, a frase de hoje nas hidrelétricas com EVT e, nas usinas sem EVT, a frase que diz por que não há itens.
- **Título por tipo**: nas eólicas e solares, que não têm a disponibilidade no ONS, a seção 5 da FR-041 se chama "Série temporal da geração".
- **Resumo executivo**: nas usinas sem EVT, só a partir da US3 da spec 007; até lá, a etapa avisa e não o gera.
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
  11. afluência, vertimento e nível do reservatório (hidrelétrica sem EVT, com hidrologia; fase D, omitida na fase A com o motivo nas notas);
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
| 19/10/2026 | Ajustes da conferência do código da fase A contra este rascunho (tarefa T073), aprovados pelo usuário. |

## Fase B — térmicas e nucleares (rascunho para aprovação, tarefa T077)

### Requisitos novos

- **FR-044** (seções de térmica, item 8 da FR-041): nas UTE e UTN com o despacho, em ordem fixa:
  1. geração por motivo de despacho e inflexibilidade;
  2. atendimento ao despacho;
  3. disponível sem despacho e CVU × CMO (esta parte só com o CVU).
  - Figuras em seaborn: geração mensal por motivo (empilhada); inflexibilidade programada × verificada; CVU das unidades × CMO do subsistema, por semana.
  - Seção sem base é omitida, com o motivo nas notas.
- **Capa das térmicas** (data-model 6.5): geração média, horas com despacho, disponibilidade média e TEIFa, quando há.
- **Legendas**: o despacho cita o CEG e os códigos de planejamento; o CVU, os códigos de planejamento; o CMO, o subsistema com o nível escrito ("subsistema SE, agregado").
- **Notas**: os limiares de C12 a C15 na nota da conclusão gerada do catálogo; o CMO como contexto do subsistema.
- **Resumo executivo** (spec 007, decisão R6): nas térmicas, a evolução anual ganha o principal indicador de perda do tipo (horas disponíveis sem despacho); os termos novos (CVU, CMO) entram no glossário do resumo com o texto aprovado pelo usuário.

### Aplicabilidade por tipo (fase B, acréscimo)

| Elemento | UTE, UTN | Demais tipos |
|---|---|---|
| Seções de térmica (FR-044) | com o despacho | não se aplica |
| Indicadores da capa de térmica | com o despacho e a disponibilidade | não se aplica |

## Fase C — eólicas e solares (rascunho para aprovação, tarefa T098)

### Requisitos novos

- **FR-045** (seções de renováveis, item 8 da FR-041): nas EOL e UFV, em ordem fixa:
  1. fator de capacidade (publicado, com o nível, e o calculado, quando há série própria);
  2. energia cortada por restrição de operação (constrained-off), por mês e por razão;
  3. recurso × geração.
  - A aderência à programação fica na seção comum de programação, com os maiores desvios.
  - Figuras em seaborn: fator de capacidade mensal; energia cortada mensal por razão (empilhada); geração média por faixa de recurso; desvio da programação.
  - Seção sem base é omitida, com o motivo nas notas; na série curta, a sazonalidade sai com o motivo (decisão R17).
- **Capa das renováveis** (data-model 6.5): fator de capacidade, geração média e energia cortada (% da estimada); os números do conjunto identificados como tais.
- **Legendas**: a restrição com detalhe cita o id ONS e o CEG da usina; o Fator de capacidade e a razão da restrição do conjunto citam "conjunto de usinas, id ONS CJU_…".
- **Notas**: a energia cortada só nas semi-horas com a marca de restrição; as semi-horas sem a marca (fotovoltaica de 05 a 12/2024) fora do total; a estimativa ausente (estimada 0 com geração verificada) fora dos totais, com o corte não calculado nas semi-horas restritas sem estimativa; o recurso inválido fora das faixas; os limiares de C16 a C19 na nota da conclusão gerada do catálogo.
- **Resumo executivo** (spec 007, decisão R6): nas eólicas e solares, a evolução anual ganha o principal indicador de perda do tipo (energia cortada, em MWh e em % da estimada); os termos novos do resumo (por exemplo, constrained-off e as razões REL, CNF e ENE) entram no glossário com o texto aprovado pelo usuário. Aprovado em 21/10/2026: "constrained-off: redução da geração da usina por comando do ONS, por razão externa a ela (indisponibilidade externa, confiabilidade elétrica ou razão energética)"; REL, CNF e ENE não aparecem no resumo das pilotos.

### Aplicabilidade por tipo (fase C, acréscimo)

| Elemento | EOL, UFV | Demais tipos |
|---|---|---|
| Seções de renováveis (FR-045) | com as bases | não se aplica |
| Indicadores da capa de renováveis | com as bases | não se aplica |

## Fase D — PCH e CGH em conjunto; hidrelétricas sem EVT com hidrologia (rascunho para aprovação, tarefa T119)

Já entregue na fase A, sem mudança: a capa com os indicadores do conjunto identificados; a nota de granularidade ("o ONS publica a geração do conjunto … e não a da usina isolada"); as omissões com o motivo; a frase da conclusão sem itens.

### Requisitos novos

- **FR-046** (seção "Composição e geração do conjunto", item 8 da FR-041, depois das seções do tipo): em toda usina em conjunto com a geração do conjunto (FR-060 das Análises), inclusive a eólica ou solar com série própria (decisão do usuário de 22/10/2026). A seção sai da lista das omitidas, onde hoje aparece como "seção ainda não gerada pelo pipeline".
  - **Texto**: a composição de cada trecho e a geração do conjunto, sempre "do conjunto <nome>"; a divergência do tipo publicado, quando há.
  - **Tabelas**:
    - composição: usina, tipo, CEG, entrada e saída no conjunto, potência (MW);
    - geração por trecho: trecho, início, fim, tipos, horas com valor, energia (MWh), média (MWmed), máxima (MW) e a potência somada das usinas do trecho (MW).
  - **Figura em seaborn**: a geração média mensal do conjunto, colorida por trecho de composição, com a potência somada de cada trecho em degrau e uma linha vertical em cada mudança de composição.
  - **Legendas**: "Geração por usina (conjunto de usinas, id ONS CJU_…)", "Composição dos conjuntos de usinas (CJU_…)" e "Capacidade de geração (CEG das usinas da composição)"; a potência somada como "calculado neste relatório".
  - **Seção 1** (fonte e cobertura): na usina com esta seção, a tabela de trechos deixa a coluna "Composição (CEG)", que passa a esta seção com os nomes das usinas. Na usina sem conjunto, a tabela não muda.
- **FR-047** (seção "Afluência, vertimento e nível do reservatório" na hidrelétrica sem EVT, item 11 da FR-041; tarefa T150), com a FR-061 das Análises:
  - **com o alinhamento confirmado**: o texto com a cobertura e o resultado do alinhamento, a tabela anual de hoje e uma figura em seaborn com as médias mensais da afluência e das vazões turbinada e vertida;
  - **sem o alinhamento confirmado**: só o texto com a cobertura e o resultado da conferência;
  - **legendas**: "Dados hidrológicos horários (cod_usina …, reservatório …)", com o alinhamento pela geração como conferência;
  - sem a tabela e a figura das faixas de afluência da EVT e sem o perfil por hora do dia, que comparam os dias com parada com EVT.
- **Notas** (só quando a seção nova aparece):
  - usina em conjunto: o período começa na entrada da usina no conjunto (FR-054 da Coleta); a composição vem da Composição dos conjuntos e a potência, das unidades da Capacidade de geração;
  - hidrelétrica sem EVT: a hora da hidrologia conferida pela geração da usina (FR-026 da Conferência), e não pela EVT.
- **FR-048** (relatório em duas partes; decisões do usuário de 22/10/2026, depois de ver o relatório da Bandeirante): na usina em conjunto sem série própria, em que todos os números de operação são do conjunto (série de referência = Geração por usina do conjunto), o relatório tem duas partes:
  1. **a usina**: a seção "A usina no conjunto", logo depois da fonte e cobertura dos dados, com o que o ONS publica da usina isolada (a ficha do cadastro, na capa; as unidades e a entrada no conjunto; as linhas próprias sem valor) e o que não publica (geração, disponibilidade, indicadores), onde a geração da usina pode ser obtida (medição da CCEE e registros do agente, fora deste relatório, que usa só os dados abertos do ONS) e a tabela do peso da usina na potência do conjunto por composição (FR-060 das Análises). As seções com base própria da usina, quando há (disponibilidade, indicadores, afluência), continuam no lugar de hoje;
  2. **o conjunto**: uma seção "Operação do conjunto <nome> (<id>)" logo antes da conclusão (depois da qualidade dos dados), com as análises do conjunto em subseções: indicadores anuais, série temporal da geração, geração mensal e sazonalidade, perfil horário, composição e geração por trecho e programação × verificada. As constatações do conjunto ficam no início dela.
  - A usina em conjunto com série própria (Seriemas 1) mantém a estrutura da FR-046. O resumo executivo remete à seção do conjunto para a evolução anual.
  - Proposta registrada para uma spec futura (decisão do usuário de 22/10/2026): a geração da usina isolada pela medição da CCEE, com download manual (a CCEE bloqueia o download por script), para medir quanto a usina pesa na geração do conjunto.
- **Resumo executivo**: sem indicador novo; os números do conjunto continuam identificados como tais.
- **Efeito nas referências**: a São Domingos, a William Arjona e a Praia Formosa não mudam (fora de conjunto e, a São Domingos, com EVT). A Seriemas 1 ganha a seção do conjunto (Conj. Inocência 230 kV, oito usinas) e perde a coluna de composição na tabela de trechos e a linha da seção nas omitidas. Por isso a referência dela é refeita, com a aprovação do usuário, junto com a da Bandeirante (tarefa T126).

### Aplicabilidade por tipo (fase D, acréscimo)

| Elemento | Usina em conjunto (PCH, CGH, EOL, UFV) | UHE, PCH, CGH sem EVT, com hidrologia | Demais |
|---|---|---|---|
| Seção do conjunto (FR-046) | com a geração do conjunto | — | não se aplica |
| Seção de afluência sem EVT (FR-047) | — | sim | hidrelétrica com EVT: a seção de hoje; demais tipos: não se aplica |
| Tabela de trechos da seção 1 | sem a coluna de composição | como hoje | como hoje |

## Fase E — relatório de carteira (rascunho para aprovação, tarefa T129)

### Requisitos novos

- **FR-049** (relatório de carteira; decisão R21 e contrato [cli-carteira.md](../contracts/cli-carteira.md)): o comando `python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao ...]` gera o relatório em `reports/carteiras/<nome>/` só com o que já está gravado: o catálogo, os perfis e os resultados das Análises. Nenhuma etapa é executada e o portal não é consultado.
  - **Recorte**: as linhas do catálogo (`usinas.csv`) do estado, do tipo ou dos dois. As linhas de conjunto não contam como usina.
  - **Com resultado**: a usina com perfil achado pelo CEG, conferido e válido, e com as Análises `concluida` no formato atual, com `indicadores_carteira` (FR-062 das Análises).
  - **Sem resultado**: um motivo por usina, o primeiro desta ordem:
    1. só agregado no ONS (ver o panorama): cobertura `agregado` no catálogo;
    2. sem perfil;
    3. perfil em rascunho;
    4. perfil inválido, inclusive dois perfis com o mesmo CEG (com os dois slugs);
    5. Análises ausentes, com falha, desatualizadas ou em formato antigo, com o caso da usina.
    - A lista traz também a cobertura do catálogo (própria, conjunto, agregado, ausente), que mostra quais usinas têm série no ONS para um perfil.
  - **Conteúdo**, na ordem do contrato:
    1. **capa**: recorte, data do catálogo e quantidade de usinas com e sem resultado;
    2. **quadro das usinas com resultado**: nome, tipo, modalidade, potência, cobertura, nível da geração e período da série;
    3. **indicadores** (FR-062 das Análises): uma linha por usina, com o ano dos indicadores. Entram só as colunas que se aplicam a algum tipo do recorte, com "—" onde não se aplica; o valor de conjunto ou de agregado vem identificado como tal;
    4. **ordenação**: possíveis problemas (decrescente), pontos de atenção (decrescente) e nome, com as quatro contagens e as regras avaliadas de cada usina. As usinas sem regra avaliada vêm no fim, com a frase de que a conclusão delas não tem base no nível da usina;
    5. **usinas sem resultado**: o motivo e a cobertura de cada uma, com a quantidade por motivo;
    6. **panorama** (só com `--estado`): os agregados do estado (`agregados.csv`) dos 12 últimos meses completos, por modalidade, tipo e mês, com energia (MWh), horas com valor e horas ausentes. Vêm identificados como agregado, com os valores das usinas Tipo III marcados como previsão do ONS, e não são atribuídos a nenhuma usina (princípio VIII). Com `--estado` e `--tipo`, só o tipo do ONS correspondente: hidrelétrica (UHE, PCH e CGH, que o agregado não separa), térmica (UTE e UTN), fotovoltaica ou eólica. Na carteira só por tipo, o panorama é omitido, com o motivo nas notas;
    7. **notas**: fontes (o catálogo e a data das Análises de cada usina), níveis dos dados e a frase de que a carteira não atribui nota nem parecer: a ordenação só conta os itens da conclusão de cada usina, que dependem das regras avaliadas e do período de cada uma.
  - **Figuras em seaborn**:
    - itens da conclusão por usina, na ordem da ordenação: barras horizontais empilhadas pelas quatro listas, na ordem da conclusão, com legenda;
    - panorama: energia mensal dos agregados em barras empilhadas por modalidade e tipo, com a previsão Tipo III identificada na legenda.
  - **Planilha** `carteira.xlsx`: abas `USINAS`, `INDICADORES` (valor, nível e unidade de cada indicador), `ORDENACAO`, `SEM_RESULTADO`, `PANORAMA` (na carteira só por tipo, só com o motivo) e `FONTES`.
  - **Gravação**: pasta temporária, conferência e troca, como no relatório da usina, sem `.bak`. Com `--data-geracao`, o PDF é reproduzível byte a byte.
  - **Textos**: nenhum termo de parecer (SC-007), conferido por teste.
  - **Códigos e mensagens**: os do contrato (0, 1, 2 e 5).
- **Efeito nas referências**: nenhum. A carteira é uma saída nova, fora de `relatorios_referencia/`, e nenhum relatório de usina muda.
- **Na prática** (catálogo de 22/10/2026):
  - **MS**: 149 usinas, sem as 22 linhas de conjunto.
    - Com resultado: as quatro pilotos. A São Domingos entra depois de refeitas as etapas; hoje sairia como "Análises em formato antigo".
    - Sem resultado: 46 só agregado no ONS e 99 sem perfil, das quais 71 sem série no ONS (cobertura ausente).
    - Panorama de 10/2025 a 09/2026: MMGD fotovoltaica (2,91 TWh) e pequenas usinas Tipo III hidrelétricas (1,16 TWh) e térmicas (0,22 TWh), estas como previsão; e duas térmicas Tipo III publicadas uma a uma, com zero de 10/2025 a 04/2026 e sem nenhum valor de 05/2026 a 09/2026 (depois da troca do nome pelo ONS). O mês de uma série sem nenhuma hora com valor aparece como "sem valor", e não como zero.
  - **`brasil_ute`**: 617 usinas; só a William Arjona com resultado.

### Aplicabilidade por recorte (fase E, acréscimo)

| Elemento | `--estado` | `--estado` e `--tipo` | `--tipo` |
|---|---|---|---|
| Pasta | `<uf>` | `<uf>_<tipo>` | `brasil_<tipo>` |
| Quadro, indicadores, ordenação e sem resultado | todas as usinas do estado | as usinas do tipo no estado | as usinas do tipo no Brasil |
| Panorama | todos os tipos do ONS | o tipo do ONS correspondente | omitido, com o motivo nas notas |
