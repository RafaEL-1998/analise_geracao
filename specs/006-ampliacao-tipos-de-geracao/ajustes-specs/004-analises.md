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
