# Specification Quality Checklist: Tratamento, Padronização e Validação Física dos Dados - UHE São Domingos

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-30
**Revalidated**: 2026-10-05 (spec revisada retroativamente; versão anterior deste checklist em `requirements.md.2026-10-05.bak`)
**Feature**: [spec.md](../spec.md)

## Content Quality

- [ ] No implementation details (languages, frameworks, APIs) — *Desvio aceito*: a spec revisada cita `float64`, NaN, tipos do Parquet (`double`, `timestamp`), nomes de colunas e de arquivos e, nas notas de revisão, módulos de `src/`. Como a revisão é retroativa e documenta um sistema já implementado, esses termos foram mantidos para permitir a conferência com o código.
- [x] Focused on user value and business needs
- [ ] Written for non-technical stakeholders — *Desvio aceito*: o público é a fiscalização técnica (desempenho de usinas); as regras R1 a R9 exigem fórmulas e unidades físicas.
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous — limites, tolerâncias e faixas estão explícitos (50,4 MW; 171,2 m³/s; 1,0 MW; 0,214 a 0,398 MW/(m³/s); $10^{-4}$).
- [x] Success criteria are measurable — SC-002 e SC-005 trazem as contagens da execução de 30/09/2026.
- [x] Success criteria are technology-agnostic (no implementation details) — SC-003 cita `.xlsx` e `.parquet` porque os formatos são entregas pedidas pelo usuário.
- [x] All acceptance scenarios are defined — US1 com 6 cenários, US2 com 6; US3 transferida para a Feature 003.
- [x] Edge cases are identified — 12 casos, incluindo ausentes, instante inválido, colunas faltantes, violação de R1 e validação desligada.
- [x] Scope is clearly bounded — entrada da Feature 001; perfil estatístico anual na Feature 003.
- [x] Dependencies and assumptions identified — dicionário v2.0, parâmetros da usina com fonte (RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3), natureza de triagem das tolerâncias, período da base.

## Feature Readiness

- [ ] All functional requirements have clear acceptance criteria — FR-001 a FR-016, FR-018 e FR-019 têm cenário ou caso de borda correspondente; **FR-017** (parâmetros centralizados, com fonte, e limites calculados) é verificável apenas por inspeção de `src/config.py` e não tem cenário Given/When/Then nem teste automatizado.
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria — conferido em 2026-10-05 nos arquivos de 30/09/2026: 10 métricas `float64` sem texto e sem ausentes convertidos (SC-001); 9 regras com contagens documentadas (SC-002); `.xlsx` com células numéricas e `.parquet` com `double` (SC-003); ressalva sobre R1 a R5 no relatório (SC-004); 70.895 registros na base consolidada e na tratada (SC-005); 526 sinalizados localizáveis por `qualidade_registro`, incluindo 15/05/2019 14h `R6;R7;R8` (SC-006).
- [ ] No implementation details leak into specification — ver o primeiro item de Content Quality.

## Notes

- Revalidação de 2026-10-05: os itens desmarcados são desvios aceitos (linguagem técnica em uma spec retroativa) ou lacunas registradas (FR-017 sem critério de aceite automatizado).
- Pendência: a suíte `tests/test_processor.py` e `tests/test_validator.py` não foi executada nesta revisão (tarefa T050 em `tasks.md`); a conferência dos critérios de sucesso foi feita sobre as saídas gravadas em `data/processed/`.
- Checklist original (30/09/2026): todos os itens marcados e a nota "All items reviewed and satisfied for requirements quality. Ready for planning phase (`/speckit-plan`)". A marcação foi refeita porque a spec mudou e porque SC-004 original ("comprova documentalmente a legitimidade dos valores") não era atingível.
