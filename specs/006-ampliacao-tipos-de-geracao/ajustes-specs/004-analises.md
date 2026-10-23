# Ajustes à spec das Análises — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/004-analises/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec das Análises (a partir da FR-052).

## Requisitos alterados

- **Entradas**: as datas de obtenção e o resumo do manifesto (linha "Versão dos arquivos" da cobertura) passam a vir de `datas_obtencao.csv`, gravado pela Coleta. A etapa não lê nada de `data/raw/`. Os valores da São Domingos não mudam.
- **Formato** (`resultados.pkl`): passa ao `VERSAO_FORMATO` 3 (o 2 foi usado no item 4 da fase A, com as datas de obtenção da Coleta), com os campos:
  - `tipo` e `modalidade`;
  - `niveis` (chave da tabela ou da figura, nível e identificador);
  - `trechos`;
  - `comum`;
  - `omitidos` (seção ou regra não avaliada, com o motivo).
  - Nas hidrelétricas com EVT, os campos de hoje mantêm os mesmos valores.
- **Constatações**: um número de conjunto vem escrito "do conjunto <nome>". Nenhum número de conjunto é dividido entre as usinas.
- **Conclusão** (regras C1 a C11): o catálogo passa a ser uma lista de regras declaradas. Cada regra traz:
  - `codigo`, `tipos` e `listas` (as listas em que pode gerar itens; cada item traz a sua);
  - `nivel_exigido` (só dado da usina);
  - `limiares`, `periodo_minimo_meses` e `secoes`.
  - Nas hidrelétricas com EVT, C1 a C11 continuam com a mesma ordem, os mesmos textos, limiares e listas, sem período mínimo novo. A nota da conclusão continua o texto de hoje.

## Requisitos novos

- **FR-052** (dois caminhos): a etapa DEVE escolher o caminho pela presença da EVT:
  - **hidrelétrica com EVT** (UHE, PCH ou CGH): as análises de hoje, sem mudança;
  - **usina sem EVT**: as seções comuns calculadas sobre a base horária comum do Tratamento:
    - indicadores anuais;
    - disponibilidade e geração por ano, quando há disponibilidade;
    - indicadores oficiais, quando há;
    - série temporal;
    - geração mensal e sazonalidade;
    - perfil horário;
    - programação × verificada;
    - disponibilidade sincronizada, quando há;
    - afluência e nível, quando há hidrologia sem EVT (fase D; na fase A, omitida, com o motivo em `omitidos`);
    - qualidade dos dados.
- **FR-053** (período mínimo): a sazonalidade (distribuição por mês do ano) DEVE pedir 12 meses distintos. Sem eles, é omitida e entra em `omitidos`. Uma regra nova com limiar anual só é avaliada nos anos com o período mínimo dela.
- **FR-054** (regra só com dado da usina): uma regra cujas entradas são do nível do conjunto ou do agregado NÃO DEVE gerar item. Ela entra em `omitidos`. Na usina em conjunto sem base própria, a conclusão não tem itens e traz a frase que explica a falta de base no nível da usina.
- **FR-055** (nota da conclusão): nas usinas sem EVT, a nota DEVE ser gerada do catálogo das regras do tipo, com os limiares.

## Aplicabilidade por tipo (fase A)

| Análise | Hidrelétrica com EVT | Usinas sem EVT |
|---|---|---|
| EVT, eventos de parada, perfis da EVT, faixas de afluência | como hoje | não se aplica |
| Seções comuns sobre a base horária comum (FR-052) | não se aplica (o caminho de hoje já as tem) | sempre, conforme a cobertura |
| Conclusão C1 a C11 | como hoje | as regras comuns C2, C5, C8 e C10 sobre a base horária comum, só com dado da usina (decisão R16; sem IP e TEIF de referência no perfil, a C5 não é avaliada); as demais em `omitidos`; as regras do tipo entram nas fases B a D |

## Decisões do usuário (acréscimo)

| Data | Decisão |
|---|---|
| 09/10/2026 | Ampliação para todos os tipos de usina (spec 006, aprovada). Indícios da conclusão só com dado da usina. |
| 19/10/2026 | Ajustes da conferência do código da fase A contra este rascunho (tarefa T073), aprovados pelo usuário. |

## Fase B — térmicas e nucleares (rascunho para aprovação, tarefa T077)

### Requisitos novos

- **FR-056** (seções de térmica, decisão R18), no campo `termica` dos resultados:
  - **geração por motivo**: energia verificada e programada de cada motivo, por mês e por ano, com a parcela no total;
  - **inflexibilidade**: a programada e a verificada, por mês (tabela e figura), dentro da geração por motivo;
  - **atendimento ao despacho**: nas horas com geração programada, o desvio verificado − programado; horas e energia abaixo e acima, além do limiar de desvio de `regras.py`; os maiores desvios, até `NUMERO_EVENTOS_RELATORIO`;
  - **disponível sem despacho**: horas com a disponibilidade operacional acima do limiar, sem programação e sem geração, com a potência disponível média;
  - **CVU × CMO**: por semana operativa, o CVU de cada unidade de planejamento e o CMO médio semanal do subsistema; semanas com o CVU abaixo, acima e igual ao CMO, com a geração em cada caso, sem julgar o despacho; o CVU sinalizado (ausente, zero ou negativo) fica sem comparação (decisão do usuário de 20/10/2026);
  - **usina sem geração no período**: nenhuma divisão por zero; a constatação diz que a usina ficou disponível e não foi despachada, com as horas e a potência disponível.
- **FR-057** (regras C12 a C15, decisão R16): UTE e UTN, só com dados da usina:
  - C12: geração abaixo da programada em horas recorrentes (possíveis problemas; a confirmar com o agente);
  - C13: horas disponíveis sem despacho em semanas com o CVU abaixo do CMO (a confirmar com o agente);
  - C14: geração por inflexibilidade abaixo da programada (pontos de atenção);
  - C15: geração acima da programada, sem programação correspondente, em horas recorrentes (a confirmar com o agente).
  - Os limiares ficam em `regras.py`, calibrados na William Arjona e aprovados pelo usuário no fim da fase; uma regra com limiar anual só é avaliada nos anos com o período mínimo dela (FR-053).
- As regras comuns C2, C5, C8 e C10 continuam sobre a base horária comum (fase A).

### Aplicabilidade por tipo (fase B, acréscimo)

| Análise | UTE, UTN | Demais tipos |
|---|---|---|
| Seções de térmica (FR-056) | com o despacho; CVU × CMO com o CVU | não se aplica |
| Regras C12 a C15 | com as bases no nível da usina | não se aplica |

## Fase C — eólicas e solares (rascunho para aprovação, tarefa T098)

### Requisitos novos

- **FR-058** (seções de renováveis, decisão R19), no campo `renovavel` dos resultados:
  - **fator de capacidade**: o publicado, da usina ou do conjunto (com o nível), por mês e por ano; com série própria, também o calculado da geração da usina e da capacidade do perfil, identificado como "calculado neste relatório";
  - **energia cortada**: a geração verificada e a estimada sem restrição, nas mesmas semi-horas (as com estimativa), a energia cortada por mês e por razão (REL, CNF, ENE) e as horas restritas; com a razão do conjunto, a tabela diz que a razão é do conjunto e a energia é da usina; as semi-horas sem a marca de restrição e as semi-horas sem estimativa (FR-042 do rascunho 002), em especial as restritas, em que o corte não pôde ser calculado, contadas à parte;
  - **recurso × geração**: geração verificada média por faixa de vento (m/s) ou de irradiância (W/m²), sem as semi-horas com o recurso inválido ou fisicamente implausível (vento acima de 40 m/s, irradiância acima de 1.500 W/m²; decisão do usuário de 21/10/2026, com as 111 semi-horas de vento até 246 m/s da Praia Formosa sem a marca do ONS), contadas (US3-3); a estimada média sem as estimativas ausentes;
  - **aderência à programação**: na seção comum de programação, com o desvio médio e os maiores desvios (US3-4);
  - **série curta** (decisão R17): seção ou parte com período mínimo declarado (a sazonalidade, 12 meses distintos) é omitida, com o motivo.
- **FR-059** (regras C16 a C19, decisão R16): EOL e UFV, só com dados da usina:
  - C16: energia cortada da usina acima de um limiar da energia estimada (pontos de atenção);
  - C17: recurso (vento ou irradiância) inválido acima de um limiar das semi-horas da usina (a verificar em campo);
  - C18: fator de capacidade próprio abaixo da razão entre a garantia física e a capacidade instalada, só com a garantia física no perfil (pontos de atenção);
  - C19: desvio médio entre a geração programada e a verificada da usina acima de um limiar, só com a programação no nível da usina (a confirmar com o agente).
  - Os limiares ficam em `regras.py`, calibrados na Seriemas 1 e na Praia Formosa e aprovados pelo usuário no fim da fase; uma regra com limiar anual só é avaliada nos anos com o período mínimo dela.
  - Calibração aprovada pelo usuário em 21/10/2026 (tarefa T115): C16 em 5 % da energia estimada, C17 em 10 % das semi-horas e C18 como proposta; C19 em 15 % da potência instalada (os 10 % iniciais apontavam desvios usuais da previsão de vento: 10,4 % na Praia Formosa).
- As regras comuns da fase A (C2, C5, C8 e C10) não valem para eólicas e solares, que não têm a Disponibilidade por usina nem os indicadores por unidade no ONS (achado A11); o catálogo das eólicas e solares fica com C16 a C19.

### Aplicabilidade por tipo (fase C, acréscimo)

| Análise | EOL, UFV | Demais tipos |
|---|---|---|
| Seções de renováveis (FR-058) | com as bases; números do conjunto identificados | não se aplica |
| Regras C16 a C19 | com as bases no nível da usina | não se aplica |

## Fase D — PCH e CGH em conjunto; hidrelétricas sem EVT com hidrologia (rascunho para aprovação, tarefa T119)

Já entregue na fase A, sem mudança: as seções comuns sobre a geração do conjunto, identificada como tal; a disponibilidade e os indicadores oficiais omitidos, com o motivo; as linhas próprias sem valor na qualidade dos dados; a conclusão sem itens, com a frase de que o ONS publica para a usina só os números do conjunto (FR-054).

### Requisitos novos

- **FR-060** (composição e geração do conjunto, decisão R20), no campo `conjunto` dos resultados. Vale para toda usina em conjunto com a Geração por usina do conjunto coletada, inclusive a eólica ou solar com série própria (Seriemas 1). Usa `trechos.csv`, `composicao_conjunto.csv`, `capacidade_membros.csv` e `tipo_publicado.csv` da Coleta e a base horária do Tratamento.
  - **Composição por trecho**: as usinas de cada trecho, com o nome, o tipo (pelo CEG), o CEG, a entrada e a saída no conjunto e a potência no trecho (unidades ativas da Capacidade de geração). A potência somada das usinas do trecho é identificada como "calculado neste relatório".
  - **Geração do conjunto por trecho de composição**: horas, horas com valor, energia (MWh), média (MWmed) e máxima (MW) de cada trecho, com os tipos do trecho; a média mensal, para a figura.
  - **Tipo publicado**: o tipo e o combustível que o ONS publica na série do conjunto, por trecho, comparados com os tipos da composição. A divergência entra na qualidade dos dados, como fato (no Conj. Chapadão, "TÉRMICA"/"Biomassa" também no trecho só com as quatro PCH).
  - Nenhum número do conjunto é dividido entre as usinas (FR-023 da spec 006), nem entra na conclusão (FR-054). A geração do conjunto não é dividida pela potência somada: nenhum fator de capacidade do conjunto é calculado.
  - **Peso da usina na potência do conjunto** (decisão do usuário de 22/10/2026), por trecho de composição: a potência das unidades da usina em operação no trecho ÷ a potência somada das usinas do trecho. É fato da Capacidade de geração e nunca estima a geração da usina (a geração do conjunto não é dividida pela potência, decisão R20). Na Bandeirante: 6,7 % de 27/09/2019 a 30/06/2025 e 35,7 % desde 01/07/2025; antes de 12/10/2019, as unidades dela ainda não estavam em operação.
  - Constatação "A usina no conjunto", só no relatório em duas partes da FR-048 do rascunho 005: o peso por composição e o que o ONS publica da usina isolada.
- **Linhas próprias sem valor**: o texto da qualidade dos dados passa a dizer o período dessas linhas (FR-047 e FR-048 da Coleta). Na Bandeirante: 4.128 linhas, de 01/05/2026 a 19/10/2026.
- **FR-061** (afluência, vertimento e nível na hidrelétrica sem EVT; tarefa T150), no campo `hidrologia` dos resultados, que hoje fica vazio nesse caminho:
  - **com o alinhamento confirmado** pela FR-026 da Conferência:
    - a tabela anual de hoje: horas, afluência média e máxima, vazões turbinada e vertida, nível de montante mínimo e máximo, volume útil e horas acima do engolimento máximo;
    - as médias mensais da afluência e das vazões turbinada e vertida, para a figura;
  - **sem o alinhamento confirmado**: só a cobertura e o resultado da conferência, como a FR-034 faz hoje;
  - **sem os cruzamentos com a EVT**: ficam de fora as horas e a EVT por faixa de afluência, o perfil por hora do dia nos dias com parada com EVT e as regras C3 e C11, que continuam só no caminho com EVT, como na fase A.
  - Os valores sinalizados saem só do campo afetado, como hoje (regra H4 e volume útil negativo).

### Aplicabilidade por tipo (fase D, acréscimo)

| Análise | Usina em conjunto (PCH, CGH, EOL, UFV) | UHE, PCH, CGH sem EVT, com hidrologia | Demais |
|---|---|---|---|
| Composição e geração do conjunto (FR-060) | com a geração do conjunto | — | não se aplica |
| Afluência, vertimento e nível (FR-061) | — | com o alinhamento confirmado; sem ele, só a cobertura | hidrelétrica com EVT: como hoje; demais tipos: não se aplica |
| Conclusão | PCH e CGH: sem itens, com a frase (fase A); EOL e UFV: C16 a C19 só com a usina | as regras comuns da fase A; C3 e C11 só com a EVT | sem mudança |

## Fase E — carteira (rascunho para aprovação, tarefa T129)

### Requisitos novos

- **FR-062** (indicadores da carteira, decisão R21), no campo `indicadores_carteira` dos resultados, que existe desde o formato 3 e hoje fica vazio. As Análises o gravam nos dois caminhos, com e sem EVT; o formato dos resultados não muda de versão. O campo reúne números que as Análises já calculam para o relatório da usina; o único cálculo novo é a razão do atendimento ao despacho.
  - **Chaves fixas**:
    - `tipo`;
    - `periodo`: início e fim da série de referência;
    - `ano` e `ano_parcial`: o ano dos indicadores, que é o último ano completo da série; sem ano completo, o ano parcial mais recente, marcado como parcial;
    - `fator_capacidade`, `disponibilidade`, `teifa`, `energia_cortada` e `atendimento_despacho`, cada um com `valor`, `nivel` (o do dado de origem: usina, conjunto ou agregado) e `unidade`. Quando o indicador não se aplica ao tipo ou falta a base, fica vazio, e nunca zero;
    - `conclusao`: a quantidade de todos os itens de cada lista (possíveis problemas, pontos de atenção, confirmar com o agente, verificar em campo), contados como na aba CONCLUSAO, e não só os 5 exibidos; e as regras avaliadas e as não avaliadas.
  - **Origem**: cada indicador é o número da tabela anual do relatório da usina, no ano escolhido.

    | Indicador | Origem | Aplica-se a |
    |---|---|---|
    | Fator de capacidade (%) | geração média ÷ potência instalada, dos indicadores anuais | UHE com EVT; EOL e UFV com série da usina (como no relatório, decisão R14) |
    | Disponibilidade (%) | disponibilidade operacional média ÷ potência instalada, dos indicadores anuais | usinas com a disponibilidade no nível da usina |
    | TEIFa (%) | taxa publicada pelo ONS para dezembro do ano (janela de 60 meses); no ano parcial, a do último mês publicado | usinas com os indicadores oficiais do ONS |
    | Energia cortada (%) | energia cortada ÷ energia estimada nas semi-horas com a marca de restrição, da tabela anual da restrição | EOL e UFV com a restrição |
    | Atendimento ao despacho (%) | horas com programação (acima de 1 MW) em que a geração ficou a até 5 MW da programada ÷ horas com programação, da tabela anual do atendimento | UTE e UTN com o despacho; vazio no ano sem hora com programação |

  - **Conclusão sem regra avaliada**: quando nenhuma regra foi avaliada com dado da usina (todas em `omitidos`, como na usina em conjunto sem série própria), as contagens ficam vazias, e não zero. Aí a falta de itens não quer dizer falta de indício (FR-054).
  - **Hidrelétricas com EVT**: só o campo novo muda; o relatório não (T011).
  - **Nas pilotos de MS**, com os resultados gravados hoje:
    - William Arjona (UTE, 2025): disponibilidade 20,9 %, TEIFa 30,5 % (12/2025) e atendimento ao despacho 6,25 %, exibido como 6,2 % pelo arredondamento do projeto (2 de 32 horas com programação); fator de capacidade e energia cortada vazios; 2 possíveis problemas, 0 pontos de atenção, 4 itens a confirmar com o agente e 1 a verificar em campo.
    - Seriemas 1 (UFV, 2026 parcial, de 22/08 a 19/10/2026): fator de capacidade 17,2 % e energia cortada 16,3 %; disponibilidade, TEIFa e atendimento vazios; 0, 1, 0 e 1 itens.
    - Bandeirante (PCH em conjunto sem série própria): indicadores e contagens vazios.
    - São Domingos (UHE com EVT): fator de capacidade, disponibilidade e TEIFa de 2025, depois de refeitas as etapas. As Análises gravadas dela são de 09/10/2026, no formato 2.

### Aplicabilidade por tipo (fase E, acréscimo)

| Indicador | UHE com EVT | UHE, PCH, CGH sem EVT | UTE, UTN | EOL, UFV | Usina em conjunto sem série própria |
|---|---|---|---|---|---|
| Fator de capacidade | sim | vazio | vazio | sim | vazio |
| Disponibilidade | sim | com a disponibilidade da usina | com a disponibilidade da usina | com a disponibilidade da usina | vazio |
| TEIFa | com os indicadores oficiais | com os indicadores oficiais | com os indicadores oficiais | com os indicadores oficiais | vazio |
| Energia cortada | vazio | vazio | vazio | com a restrição | vazio |
| Atendimento ao despacho | vazio | vazio | com o despacho | vazio | vazio |
| Contagens da conclusão | sim | sim | sim | sim | vazias |
