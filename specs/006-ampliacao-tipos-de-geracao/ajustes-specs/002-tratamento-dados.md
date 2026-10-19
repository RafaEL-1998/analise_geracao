# Ajustes à spec do Tratamento de dados — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/002-tratamento-dados/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec do Tratamento (a partir da FR-035).

## Requisitos alterados

- **FR-002** (entradas): o dicionário de dados da EVT passa a vir da Coleta (`dicionario_evt.json`), e não de `data/raw/_dicionarios/`. A etapa não lê nada de `data/raw/`.
- **FR-003** (conjuntos tratados): os conjuntos que a Coleta extraiu para a usina, conforme o tipo e a cobertura. Na hidrelétrica com EVT, os nove de hoje.
- **FR-004** (período de referência): o da série de referência gravada pela Coleta. Na hidrelétrica com EVT, o da base de EVT, como hoje.
- **FR-006** (dicionário da EVT): a conferência das dez grandezas usa `data/usinas/<slug>/coleta/dicionario_evt.json`.
- **FR-028 a FR-032** (cópia `.bak` e conferência da gravação): valem também para os arquivos novos desta fase.
- **Formato**: o Tratamento passa ao formato 2 (a base horária comum, que as Análises leem nas usinas sem EVT).
- **Programação diária** (programação horária): com mais de um código, os códigos são somados em cada patamar antes da média da hora. O patamar só tem soma quando todos os códigos da extração têm valor nele; sem a linha ou sem o valor de algum código, a soma fica ausente, nunca completada.

## Requisitos novos

- **FR-035** (base horária comum): nas usinas sem EVT, a etapa DEVE gravar `base_horaria.csv`, uma linha por hora da série de referência no período, com:
  - `din_instante`;
  - `geracao_mw`, da série de referência tratada;
  - `nivel` (`usina` ou `conjunto`);
  - `disponibilidade_operacional_mw` e `disponibilidade_sincronizada_mw`, quando há cobertura;
  - `geracao_programada_mw`, quando há;
  - `trecho`, o número do trecho de `trechos.csv`;
  - `sinalizacoes`: os códigos da geração (G1), da disponibilidade (D1 a D4) e a regra R7 (geração acima da disponibilidade declarada), esta só com a geração e a disponibilidade da usina.
  - As horas ausentes da série de referência ficam listadas nas ausências, nunca preenchidas, e nenhum registro é excluído.
- **FR-036** (panorama dos agregados): a soma mensal dos agregados do catálogo (`agregados.csv`, montado pelo catálogo da Coleta, que aplica estas regras) DEVE seguir as regras desta spec:
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
| 19/10/2026 | Ajustes da conferência do código da fase A contra este rascunho (tarefa T073), aprovados pelo usuário. |

## Fase B — térmicas e nucleares (rascunho para aprovação, tarefa T077)

### Requisitos novos

- **FR-037** (despacho por hora): o Tratamento DEVE gravar `despacho_horario.csv` (soma das unidades de planejamento por hora) e `despacho_unidades_horario.csv` (por unidade), com a geração programada e a verificada de cada motivo de despacho, na hora de início do intervalo (decisão R11). A convenção é conferida pela G4: se a coincidência melhorar com uma hora de deslocamento, a convenção declarada está errada e vira correção, nunca ajuste automático.
- **FR-038** (CVU): um valor por unidade de planejamento e semana operativa, o da revisão mais recente, em `cvu_semanal.csv`, com `sinal_cvu` para o CVU ausente ou negativo, sem descarte (FR-017 da spec 006).
- **FR-039** (CMO): um valor por subsistema e semana operativa, o da publicação mais recente, em `cmo_semanal.csv`; as duplicatas são contadas.
- **FR-040** (semanais em hora): o CVU e o CMO são levados à hora pelo intervalo da semana operativa, só para os cruzamentos.
- Ausências e duplicatas seguem as regras de hoje (FR-016), com `<chave>_ausencias.csv` e `auditoria_<chave>.csv`; a base horária comum (FR-035) não muda de colunas.

### Aplicabilidade por tipo (fase B, acréscimo)

| Tratamento | UTE, UTN | Demais tipos |
|---|---|---|
| Despacho por hora e por unidade, CVU, CMO e sinal do CVU | com a cobertura | não se aplica |
