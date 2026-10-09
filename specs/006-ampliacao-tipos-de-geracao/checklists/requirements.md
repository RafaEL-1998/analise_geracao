# Specification Quality Checklist: Relatórios de Desempenho para Todos os Tipos de Usina com Dados Abertos do ONS

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-09
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

- **Interface do projeto**: os comandos (`python -m src usinas`, `perfil`, `carteira`), as pastas (`data/catalogo/`, `reports/carteiras/`) e os nomes dos conjuntos do ONS fazem parte do que o fiscal usa e de onde vêm os dados. Por isso aparecem na spec, como nas specs das cinco etapas. Linguagem, bibliotecas e módulos ficam para o plano.
- **Decisões em aberto**: a proposta deixou três, todas resolvidas com padrões documentados em "Assumptions": a ordem das fases (a da proposta), as usinas piloto (escolhidas pela cobertura dos dados) e as fontes da ANEEL (fora, pela constituição). O usuário pode mudá-las com `/speckit-clarify` antes do plano ou das tarefas.
- **Critérios de aceitação das FR**: os de tratamento e conferência (FR-016 a FR-019) são verificados pelos cenários das histórias 2 a 4 e pelos testes das usinas fictícias (SC-005).
- **Spec de mudança temporária**: ao concluir, seus requisitos vão para as specs das etapas (FR-030), como manda a governança da constituição 3.0.0.
- **Ajustes feitos durante o plano** (09/10/2026, a partir da pesquisa nos dados do ONS e da revisão cruzada; ver [research.md](../research.md), R25):
  - FR-013 ganhou dois conjuntos: a restrição por constrained-off com a razão da restrição (sem ela, a energia cortada não sai por tipo de restrição, como pede a FR-021) e a capacidade de geração por unidade geradora (catálogo e rascunho do perfil). CVU e CMO passam a valer também para UTN;
  - FR-012: a série de EVT vale para a UHE, a PCH ou a CGH que a tiver;
  - FR-018: as comparações são sempre no mesmo nível e incluem a geração verificada do despacho × a da Geração por usina e a programação diária × a programada do fator de capacidade;
  - FR-022: uma regra só é avaliada com dados do nível da usina (princípio VIII);
  - FR-024: a legenda identifica o nível pelo identificador citado, o que mantém sem mudança as legendas da São Domingos (SC-001);
  - FR-026: a carteira sai por estado, por tipo ou pelos dois, como a constituição prevê;
  - quatro casos de borda novos e os dados das usinas piloto nas Assumptions.
  - Os itens do checklist continuam atendidos.
