# Specification Quality Checklist: Etapa 5 — Geração do relatório

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
- **Interface incluída de propósito**: comando, opções, códigos de saída, pastas e nomes de arquivos, nomes das abas e das figuras, títulos das seções, frases fixas (conclusão, avisos) e formato das legendas. São a interface da etapa e o padrão aprovado do relatório, que a não regressão confere palavra a palavra; não são escolhas de implementação.
- **Regras de leiaute com números** (285 pt de altura das figuras, tabelas de 12 linhas inteiras, 6 linhas no início de uma tabela longa, capa numa página, conclusão numa página): estáveis e testáveis. Ficaram de fora medidas de desenho mais finas, que cabem no plano.
- **seaborn** é citado porque é regra do usuário e da constituição para todo gráfico, não escolha desta spec. Nenhum módulo ou função do código é citado.
- **Valores da São Domingos** só aparecem em exemplos rotulados "(perfil da São Domingos)", nas Decisões do usuário e no critério de não regressão (SC-001). Os requisitos citam campos do perfil e regras gerais.
- **Fronteira**: os cálculos, os textos das constatações e dos itens da conclusão, o catálogo C1 a C11 e os seus limiares estão nas Análises; as conferências, na Conferência; o perfil, as regras comuns, `completo` e `copia-seguranca`, na Coleta. Esta spec só apresenta o que essas etapas gravam.
- **Sem marcadores de esclarecimento**. Dois pontos tiveram um default registrado em Assumptions, para decisão do usuário na aprovação:
  - textos que citam locais de arquivo que mudam com a nova organização (nota de sinalizações da hidrologia; origem dos limiares na tabela de parâmetros): o default é citar os locais novos, e eles ficam como diferença aceita no SC-001;
  - trechos que hoje descrevem a usina sem vir do perfil (garantia física da época do IP e do TEIF, fonte do início da operação comercial, patamar de vertimento mínimo, ressalva do volume útil): o default é levá-los ao perfil, o que pede campos novos no contrato do perfil, na spec da Coleta.
