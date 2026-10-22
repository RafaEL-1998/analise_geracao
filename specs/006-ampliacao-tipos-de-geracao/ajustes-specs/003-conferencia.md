# Ajustes à spec da Conferência — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/003-conferencia/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec da Conferência (a partir da FR-018).

## Requisitos alterados

- **FR-002** (as seis conferências): continuam as mesmas. As que comparam com a base de EVT (geração, disponibilidade e vazões) só se aplicam à hidrelétrica com EVT. As conferências novas das fases B e C entram no catálogo da FR-019.
- **FR-004** (não aplicável): o registro passa a ser também o arquivo da FR-018.
- **Formato e resultados**: a Conferência passa ao formato 2 (`nao_aplicaveis.csv`, que as Análises leem nas usinas sem EVT). Nas hidrelétricas com EVT, `conferencias.pkl` traz as seis de hoje, como hoje; nas usinas sem EVT, só as conferências aplicadas.

## Requisitos novos

- **FR-018** (`nao_aplicaveis.csv`): a etapa DEVE gravar `nao_aplicaveis.csv`, com `conferencia` e `motivo`, para todas as conferências do catálogo que não se aplicam à usina, inclusive na UHE.
  - O arquivo é só registro (princípio VI).
  - O relatório e a planilha da hidrelétrica com EVT não o leem e continuam com as conferências de hoje.
  - Nas usinas sem EVT, as notas do relatório citam as não aplicáveis do tipo, com o motivo.
- **FR-019** (catálogo das conferências): cada conferência DEVE declarar:
  - a condição de aplicação: tipo, nível e bases;
  - o motivo escrito quando não se aplica.

## Aplicabilidade por tipo (fase A)

| Conferência | Hidrelétrica com EVT | UHE, PCH, CGH sem EVT | UTE, UTN | EOL, UFV |
|---|---|---|---|---|
| Geração (EVT × Geração por usina) | sim | não aplicável: sem EVT | não aplicável: sem EVT | não aplicável: sem EVT |
| Disponibilidade (EVT × Disponibilidade por usina) | sim | não aplicável: sem EVT | não aplicável: sem EVT | não aplicável: sem EVT |
| Vazões (EVT × Dados hidrológicos) | sim | não aplicável: sem EVT | não aplicável: tipo | não aplicável: tipo |
| DISPF × horas por estado operativo | com os indicadores | com os indicadores | com os indicadores | não aplicável: tipo |
| TEIFa e TEIP refeitas | com as taxas | com as taxas | com as taxas | não aplicável: tipo |
| Cadastro × perfil | sim | sim | sim | sim |

## Decisões do usuário (acréscimo)

| Data | Decisão |
|---|---|
| 09/10/2026 | Ampliação para todos os tipos de usina (spec 006, aprovada). As conferências que não se aplicam ficam registradas em `nao_aplicaveis.csv`, inclusive na UHE, sem mudar o relatório dela. |
| 19/10/2026 | Ajustes da conferência do código da fase A contra este rascunho (tarefa T073), aprovados pelo usuário. |

## Fase B — térmicas e nucleares (rascunho para aprovação, tarefa T077)

### Requisitos novos

- **FR-020** (G3, `programacao_despacho.csv`): em UTE e UTN, a Programação diária (média horária dos patamares) DEVE ser comparada com a geração programada do despacho, hora a hora, com a tolerância de hoje (0,01 MW) e sem meta.
- **FR-021** (G4, `verificada_despacho.csv`): em UTE e UTN, a geração verificada do despacho DEVE ser comparada com a Geração por usina, hora a hora, com a mesma tolerância e sem meta.
- **FR-022** (indicadores das térmicas): a DISPF × horas por estado operativo e a TEIFa e a TEIP refeitas usam o código de hoje, pelo CEG. No fim da fase A, as taxas refeitas da William Arjona não reproduziram nenhum dos 4 meses com a janela completa (diferenças de até 2,07 p.p.): a fase B DEVE apurar a causa. Se for uma regra própria das térmicas publicada pelo ONS, a regra entra nesta spec, com a fonte; sem fonte, a divergência continua registrada como hoje, sem ajuste.
- As conferências novas só registram (decisão R13); uma meta só depois das pilotos, com a aprovação do usuário.

### Aplicabilidade por tipo (fase B, acréscimo)

| Conferência | UTE, UTN com despacho | UTE, UTN sem despacho | Demais tipos |
|---|---|---|---|
| G3 (programação × despacho) | sim | não aplicável: sem o despacho | não aplicável: tipo |
| G4 (verificada do despacho × Geração por usina) | sim | não aplicável: sem o despacho | não aplicável: tipo |

## Fase C — eólicas e solares (rascunho para aprovação, tarefa T098)

### Requisitos novos

- **FR-023** (G1, `geracao_fontes.csv`): em EOL e UFV, a geração da usina DEVE ser comparada entre as fontes que a trazem, sempre duas a duas e no mesmo nível: Geração por usina, Fator de capacidade (`val_geracaoverificada`), restrição com detalhe (média horária) e restrição com a razão (`val_geracao`, média horária). Par de níveis diferentes não é comparado.
- **FR-024** (G2, `soma_conjunto.csv`): em EOL e UFV em conjunto, com os `[[identificacao.membros]]` no perfil, a soma das usinas do conjunto (restrição com detalhe, média horária) DEVE ser comparada com a geração do conjunto (Geração por usina do conjunto), só nos trechos com todas as usinas da composição. Sem os membros no perfil, a G2 fica não aplicável, com o motivo.
- **FR-025** (G5, `programacao_renovaveis.csv`): a Programação diária (média horária dos patamares) DEVE ser comparada com a geração programada do Fator de capacidade, no mesmo nível.
- As três usam a tolerância de hoje (0,01 MW) e só registram, sem meta (decisão R13); uma meta só depois das pilotos, com a aprovação do usuário.

### Aplicabilidade por tipo (fase C, acréscimo)

| Conferência | EOL, UFV com as bases | EOL, UFV sem uma base | Demais tipos |
|---|---|---|---|
| G1 (geração entre fontes) | só os pares do mesmo nível | não aplicável: sem duas fontes no mesmo nível | não aplicável: tipo |
| G2 (soma das usinas × conjunto) | em conjunto, com os membros | não aplicável: fora de conjunto ou sem os membros | não aplicável: tipo |
| G5 (programação × fator de capacidade) | no mesmo nível | não aplicável: sem uma das bases ou níveis diferentes | não aplicável: tipo |

## Fase D — PCH e CGH em conjunto; hidrelétricas sem EVT com hidrologia (rascunho para aprovação, tarefa T119)

Na PCH e na CGH em conjunto, nenhuma conferência nova: a usina não tem série própria com valor, e a soma das usinas do conjunto (como a G2) não existe, porque o ONS publica vazias as linhas próprias das PCH. As conferências de hoje continuam não aplicáveis, com o motivo.

### Requisitos novos

- **FR-026** (alinhamento da hidrologia pela geração, `alinhamento_hidrologia.csv`; decisão do usuário de 22/10/2026): na hidrelétrica sem EVT, com os Dados hidrológicos e a Geração por usina no nível da usina, a hora da hidrologia DEVE ser conferida pela geração, porque não há a EVT para a conferência das vazões de hoje (FR-012 e FR-013).
  - O cálculo: a correlação entre a vazão turbinada (já na hora de início, deslocada −1 h pelo Tratamento) e a geração da usina, com deslocamento de −1, 0 e +1 hora.
  - O alinhamento é confirmado quando a maior correlação é a do deslocamento 0. Sem isso, as Análises publicam só a cobertura e o resultado desta conferência (como a FR-034 faz hoje, sem a meta).
  - Sem meta e sem o código 3: a conferência só registra o resultado (decisão R13). A convenção de hora nunca é ajustada automaticamente (decisão R11).
  - Sem a geração no nível da usina (hidrelétrica em conjunto), a conferência fica não aplicável, com o motivo.

### Aplicabilidade por tipo (fase D, acréscimo)

| Conferência | UHE, PCH, CGH sem EVT, com hidrologia e geração própria | UHE, PCH, CGH sem EVT, sem uma das duas | Demais tipos e hidrelétrica com EVT |
|---|---|---|---|
| Alinhamento da hidrologia pela geração (FR-026) | sim | não aplicável: sem a hidrologia ou sem a geração no nível da usina | hidrelétrica com EVT: não aplicável, vale a conferência das vazões de hoje; demais tipos: sem linha em `nao_aplicaveis.csv` |

Precisão na implementação (22/10/2026): nos tipos fora das hidrelétricas, a conferência não ganha linha em `nao_aplicaveis.csv`, porque a conferência das vazões já registra que a hidrologia não se aplica ao tipo. Assim os relatórios aprovados da William Arjona e da Praia Formosa não mudam, como diz o efeito nas referências do rascunho 005.
