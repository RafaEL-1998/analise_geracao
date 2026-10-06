# Specification Quality Checklist: Coleta e Filtragem de Dados ONS - UHE São Domingos

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-30
**Revalidated**: 2026-10-05 (spec revisada retroativamente; ver "Histórico de revisões" em spec.md)
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

- 2026-09-30: All items reviewed and satisfied for requirements quality. Ready for planning phase (`/speckit-plan`).

### Revalidação de 2026-10-05

- **Detalhes de implementação**: os requisitos não citam linguagem, framework nem biblioteca. Citam identificadores da fonte de dados (`cod_usina`, `nom_reservatorio`, `din_instante`), separador e codificações dos arquivos do ONS e códigos de saída, que fazem parte do contrato com a fonte e com o usuário fiscalizador, não da solução. O CKAN aparece apenas nas premissas. Caminhos de código e de dados aparecem só no "Histórico de revisões", como evidência.
- **Testabilidade**: cada FR tem verificação objetiva. FR-001 a FR-003 → US1, cenários 1 a 4; FR-004 e FR-005 → US2, cenários 1 e 4; FR-006 → US2, cenário 3; FR-007 → US2, cenário 5; FR-008 → US3, cenário 1; FR-009 e FR-010 → US3, cenário 2 e casos-limite.
- **Critérios de sucesso**: SC-001 a SC-006 são mensuráveis e foram verificados com evidência (execução de 30/09/2026, conferência externa de 02/10/2026 e inspeção de 05/10/2026), registrada sob cada critério.
- **Escopo**: delimitado; a etapa 3 de `src/main.py` e as opções `--indicadores-only`/`--sem-indicadores` estão explicitamente fora, remetidas a `specs/004-conferencia-outros`.
- **Aderência do código à spec revisada**: o código em vigor (`src/collector.py`, `src/filter.py`, `src/consolidator.py`, `src/models.py`, `src/main.py`) atende FR-001 a FR-010; os 15 testes da feature passam (05/10/2026).
- **Pendências que não bloqueiam a spec, mas impedem conformidade plena com a constituição**: (1) princípio IV ainda cita a chave textual `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"` (requer emenda); (2) linhas com campos insuficientes descartadas sem log; (3) versão anterior de bruto revisado não preservada; (4) `--log-level` restrito ao logger `main`; (5) conferência de 02/10/2026 sem artefato reproduzível no repositório. Detalhes no "Histórico de revisões" de spec.md e nas tarefas T039 a T043 de tasks.md.
