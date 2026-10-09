# Specification Quality Checklist: Etapa 2, Tratamento de dados

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
- **Interface da etapa citada de propósito**: comando `tratamento`, códigos de saída, pastas, nomes de arquivos, colunas, abas, campos do perfil e formatos (Parquet, planilha, CSV e Markdown). São o que a etapa entrega às seguintes e o que a não regressão compara. `double` e `timestamp` são tipos do formato Parquet; o SHA-256 e a propriedade `assinatura_dados` descrevem como a gravação é conferida. Nenhuma linguagem, biblioteca, módulo ou função é citado.
- **Usina**: os limites de R6 e R8 são expressos por campos do perfil; as tolerâncias gerais (ε = 0,0001; 5 %; 70 % a 130 %; 1,0 MW; 0,01 MW; 10 m; 0,1 h) aparecem com os números. Valores da São Domingos só nos cenários marcados "(perfil da São Domingos)", nas Decisões do usuário e na SC-001.
- **Fronteira**: a extração, a leitura numérica e a auditoria de extração ficam na Coleta; as conferências entre fontes, inclusive o alinhamento das vazões com a meta de 99 %, ficam na Conferência; o uso dos valores sinalizados segue a coluna "Sai do uso nas etapas seguintes" da FR-019, aplicada pela Conferência e pelas Análises.
- **Sem marcadores de esclarecimento**. Cinco escolhas têm default razoável e ficam para confirmação na aprovação:
  1. valor negativo na EVT (R1) sai com o código 1, e não mais com o 3: a etapa só tem os códigos 0, 1 e 5, e o 3 é da Conferência; como antes, nada é gravado;
  2. `indicadores.xlsx` fica só com as abas do Tratamento; o recálculo da TEIFa e da TEIP e as divergências DISPF × horas vão para a Conferência, e a auditoria dos arquivos fica na Coleta;
  3. a aba da planilha da EVT leva o nome da usina do perfil, normalizado, o que mantém `UHE_SAO_DOMINGOS` para a São Domingos;
  4. o `resumo` do `etapa.json` reúne números que hoje só aparecem no log;
  5. o limite de 10 minutos da SC-010 vem do limite que já valia para as bases complementares; ainda não foi medido para a etapa isolada.
