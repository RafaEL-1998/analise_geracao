# Ajustes à spec das Análises — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/004-analises/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec das Análises (a partir da FR-052).

## Requisitos alterados

- **Entradas**: as datas de obtenção e o resumo do manifesto (linha "Versão dos arquivos" da cobertura) passam a vir de `datas_obtencao.csv`, gravado pela Coleta. A etapa não lê nada de `data/raw/`. Os valores da São Domingos não mudam.
- **Formato** (`resultados.pkl`): passa ao `VERSAO_FORMATO` 2, com os campos:
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
    - afluência e nível, quando há hidrologia sem EVT;
    - qualidade dos dados.
- **FR-053** (período mínimo): a sazonalidade (distribuição por mês do ano) DEVE pedir 12 meses distintos. Sem eles, é omitida e entra em `omitidos`. Uma regra nova com limiar anual só é avaliada nos anos com o período mínimo dela.
- **FR-054** (regra só com dado da usina): uma regra cujas entradas são do nível do conjunto ou do agregado NÃO DEVE gerar item. Ela entra em `omitidos`. Na usina em conjunto sem base própria, a conclusão não tem itens e traz a frase que explica a falta de base no nível da usina.
- **FR-055** (nota da conclusão): nas usinas sem EVT, a nota DEVE ser gerada do catálogo das regras do tipo, com os limiares.

## Aplicabilidade por tipo (fase A)

| Análise | Hidrelétrica com EVT | Usinas sem EVT |
|---|---|---|
| EVT, eventos de parada, perfis da EVT, faixas de afluência | como hoje | não se aplica |
| Seções comuns sobre a base horária comum (FR-052) | não se aplica (o caminho de hoje já as tem) | sempre, conforme a cobertura |
| Conclusão C1 a C11 | como hoje | não se aplica (as regras do tipo entram nas fases B a D) |

## Decisões do usuário (acréscimo)

| Data | Decisão |
|---|---|
| 09/10/2026 | Ampliação para todos os tipos de usina (spec 006, aprovada). Indícios da conclusão só com dado da usina. |
