# Specification Quality Checklist: Etapa 3 — Conferência

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-07
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Validação em 07/10/2026, primeira iteração: todos os itens aprovados.
- **Interface citada de propósito**: comando, opção comum, códigos de saída, pastas, nomes de arquivo (inclusive `conferencias.pkl` e `etapa.json`), nomes das seis conferências e campos do perfil são a interface da etapa, não escolhas de implementação. Nenhum módulo, função ou biblioteca é citado.
- **Regras de negócio com valores**: tolerâncias (0,01 MW; 0,5 m³/s; 1 h; 0,001 p.p.; 0,001 MW), meta de 99 %, janela de 60 meses e fórmulas da TEIFa e da TEIP são regras gerais do domínio, iguais para qualquer usina, tiradas do comportamento atual. Cada uma é testável com dados sintéticos.
- **Valores da São Domingos** aparecem só no cenário marcado "(perfil da São Domingos)", nas decisões do usuário, no critério de não regressão (SC-001) e na seção "Conferências manuais (fora do fluxo)", que guarda os resultados das conferências manuais.
- **Sem marcadores de esclarecimento**. Os pontos em aberto tiveram default no comportamento atual:
  - código 3: a etapa grava os seis resultados e fica concluída com o código 3; o `completo` para, e as etapas seguintes podem ser executadas à parte, como hoje o relatório sai sem os cruzamentos hidrológicos (FR-013);
  - ficha do cadastro lida da pasta da Coleta, porque o cadastro não passa por tratamento;
  - o cadastro confere também o id ONS e o CEG em linha única, como faz hoje;
  - `geracao.csv` traz a tabela mensal; o resumo de cada conferência fica em `conferencias.pkl` e no `resumo` do `etapa.json`;
  - TEIFa e TEIP sem nenhum mês com janela completa ficam não aplicáveis, com a tabela mês a mês registrada.
- **Fronteiras**: a identidade das horas por estado operativo fica no Tratamento; a decomposição da TEIFa e da TEIP, a capacidade não sincronizada × reserva desligada, a disponibilidade declarada × DISPF por ano e a programação ficam nas Análises; a redação das legendas fica na Geração do relatório.
- **Pontos de aprovação do usuário**: o tratamento do código 3 no `etapa.json` (FR-013) e a seção "Conferências manuais (fora do fluxo)", que inclui a conferência da base de EVT com o S3 do ONS além das feitas com a CCEE e com o BI da ANEEL.
