# Ajustes à spec do Tratamento de dados — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/002-tratamento-dados/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec do Tratamento (a partir da FR-035).

## Requisitos alterados

- **FR-002** (entradas): o dicionário de dados da EVT passa a vir da Coleta (`dicionario_evt.json`), e não de `data/raw/_dicionarios/`. A etapa não lê nada de `data/raw/`.
- **FR-003** (conjuntos tratados): os conjuntos que a Coleta extraiu para a usina, conforme o tipo e a cobertura. Na hidrelétrica com EVT, os nove de hoje.
- **FR-004** (período de referência): o da série de referência gravada pela Coleta. Na hidrelétrica com EVT, o da base de EVT, como hoje.
- **FR-006** (dicionário da EVT): a conferência das dez grandezas usa `data/usinas/<slug>/coleta/dicionario_evt.json`.
- **FR-028 a FR-032** (cópia `.bak` e conferência da gravação): valem também para os arquivos novos desta fase.

## Requisitos novos

- **FR-035** (base horária comum): nas usinas sem EVT, a etapa DEVE gravar `base_horaria.csv`, uma linha por hora do período, com:
  - `din_instante`;
  - `geracao_mw`, da série de referência tratada;
  - `nivel` (`usina` ou `conjunto`);
  - `disponibilidade_operacional_mw` e `disponibilidade_sincronizada_mw`, quando há cobertura;
  - `geracao_programada_mw`, quando há;
  - `trecho`, o número do trecho de `trechos.csv`;
  - `sinalizacoes`.
  - As horas sem valor ficam listadas nas ausências, nunca preenchidas, e nenhum registro é excluído.
- **FR-036** (panorama dos agregados): a soma mensal dos agregados do catálogo (Coleta, `agregados.csv`) DEVE seguir as regras desta spec:
  - um valor por hora, o do arquivo publicado por último (FR-016);
  - as horas sem registro, contadas.

## Aplicabilidade por tipo (fase A)

| Tratamento | UHE, PCH, CGH com EVT | Usinas sem EVT |
|---|---|---|
| Base de EVT, regras R1 a R9, relatório de validação | como hoje | não se aplica |
| Disponibilidade, hidrologia, geração, indicadores e programação | como hoje | os que a cobertura declara, na hora de início |
| Base horária comum (FR-035) | não se aplica | sempre |

## Decisões do usuário (acréscimo)

| Data | Decisão |
|---|---|
| 09/10/2026 | Ampliação para todos os tipos de usina (spec 006, aprovada). O Tratamento deixa de ler `data/raw/`. |
