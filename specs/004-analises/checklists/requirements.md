# Specification Quality Checklist: Etapa 4, Análises

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
- **Interface da etapa citada de propósito**: o comando `python -m src analises --usina <slug>`, os códigos de saída, as pastas e os nomes dos arquivos (`resultados.pkl`, `etapa.json`), os campos do perfil, os títulos das seções e das constatações e os nomes de abas citados nos textos (como PROG_EVENTOS_DESVIO) são a interface da etapa com o usuário e com as etapas vizinhas, não escolhas de implementação. Nenhum módulo, função ou biblioteca é citado.
- **Limiares com valores**: as regras gerais (FR-006) e o catálogo C1 a C11 são regras de negócio do domínio, iguais para qualquer usina; cada regra é testável (dispara ou não dispara), e a linguagem de indício é verificável por lista de termos (FR-047).
- **Valores da São Domingos**: aparecem só nos cenários de aceitação, marcados "(perfil da São Domingos)", nas Decisões do usuário e nos critérios que usam os dados reais (SC-001 e SC-010); o nome da usina aparece ainda onde se verifica a não regressão e a ausência de menção a ela (US5, US6 e SC-008). Os requisitos citam campos do perfil e regras gerais.
- **Fronteiras**:
  - as conferências entre fontes, o recálculo da TEIFa e da TEIP e as divergências DISPF × horas são lidos da Conferência, nunca refeitos (FR-003);
  - o que o relatório lista ou corta (eventos com ≥ 24 h, 15 maiores eventos, cinco itens por lista), as seções, as legendas e as notas ficam na spec da Geração do relatório;
  - as regras comuns do fluxo (sintaxe, `--log-level`, perfil e código 4, `etapa.json`, `completo`) ficam na spec da Coleta de dados.
- **Escolhas deliberadas, para a aprovação do usuário**:
  - a constatação "Mudança de classificação do vertimento pelo ONS" só aparece quando a mudança é detectada, porque um fenômeno próprio de uma usina não deve gerar constatação no relatório de outra; o código atual emite, sem mudança, a frase "Não foi detectada mudança…". Para a São Domingos nada muda;
  - as entradas incluem os registros da Coleta (auditoria da EVT e manifesto, para a cobertura; ficha do cadastro; datas de obtenção), além dos dados tratados e da Conferência, porque a cobertura e a tabela de parâmetros de hoje dependem deles;
  - a FR-034 mantém o comportamento de hoje para a conferência das vazões abaixo da meta (sem cruzamentos hidrológicos), mesmo que o fluxo normalmente pare na Conferência com código 3;
  - regras gerais que existem no código, mas não estavam listadas entre as constantes do projeto, ficaram explícitas na FR-006: maio a outubro × janeiro a abril, 0,1 GWh, 0,1 h e 10⁻⁶ MW.
