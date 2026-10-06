# Specification Quality Checklist: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança dos Dados Processados

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-10-05
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

- Validação em 2026-10-05, em três iterações.
  - 1ª iteração: reprovados "Requirements are testable and unambiguous" e "All functional requirements have clear acceptance criteria".
    - O critério "havendo achado, uma constatação" era subjetivo. Passou a ser fixo: constatação sempre para disponibilidade e hidrologia; para geração e cadastro, só quando houver divergência.
    - Foram acrescentados cenários de aceitação para o resumo hidrológico mensal e para os requisitos de relatório.
    - O requisito de não obter de novo a base EVT passou a ser medido num critério de sucesso.
  - 2ª iteração: todos os itens aprovados.
  - 3ª iteração, após as decisões do usuário de 05/10/2026:
    - a cópia `.bak` ficou restrita a `data/processed/`, com os manifestos retirados da regra (FR-012);
    - entrou a nova US2 (dicionários de dados, P1), com FR-013 a FR-015 e SC-007; as histórias seguintes foram renumeradas (US3 a US6);
    - o Contexto e as Assumptions passaram a citar a constituição 1.2.0, a conferência da geração já feita em 02/10/2026 e a comparação manual com CCEE e ANEEL.
    - Revalidação: todos os itens aprovados.
- Termos que parecem de implementação e por que ficam na spec:
  - `data/processed/`, o nome `<arquivo>.bak` e "seaborn" (FR-032) são restrições impostas pelo usuário e pela constituição 1.2.0 (Requisitos Técnicos 3 e 5), não escolhas desta spec.
  - Os identificadores de cada conjunto (FR-004) e os formatos dos dicionários publicados (PDF e JSON) fazem parte do contrato com a fonte de dados, como nas specs 001 e 004.
  - "Manifesto" é termo do domínio de auditoria do projeto (specs 001, 004 e 005).
  - Os formatos dos dados aparecem só como "compacto" e "completo".
  - Os critérios de sucesso não citam tecnologia.
- Nenhum marcador de esclarecimento. As decisões em aberto (limiares de sincronização e de coincidência, faixas de afluência pelo engolimento nominal, prazo da P1) receberam padrões razoáveis, registrados em Assumptions.
- A descrição de entrada afirmava "a usina aparece desde 01/2023" na disponibilidade. A sondagem de 05/10/2026 mostrou que isso vinha do formato compacto incompleto. A correção está no Contexto, no FR-003 e nos Edge Cases.
