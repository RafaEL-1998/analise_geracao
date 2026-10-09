# Ajustes à spec da Conferência — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/003-conferencia/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec da Conferência (a partir da FR-018).

## Requisitos alterados

- **FR-002** (as seis conferências): continuam as mesmas. As que comparam com a base de EVT (geração, disponibilidade e vazões) só se aplicam à hidrelétrica com EVT. As conferências novas das fases B e C entram no catálogo da FR-019.
- **FR-004** (não aplicável): o registro passa a ser também o arquivo da FR-018.

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
