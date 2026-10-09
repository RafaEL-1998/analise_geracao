# Specification Quality Checklist: Etapa 1 — Coleta de dados

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
- **Interface citada de propósito**: a spec traz o comando e as opções, os códigos de saída, as pastas e os nomes de arquivo, os campos do perfil e do `etapa.json`, os ids dos conjuntos no catálogo do ONS e as colunas do ONS usadas na identificação da usina. São a interface da etapa e o vocabulário do domínio do usuário, não escolhas de implementação. Nenhum módulo, função ou biblioteca é citado.
- **Termos técnicos que são da fonte ou do contrato**: a API CKAN é o catálogo público do portal do ONS; CSV e Parquet são os formatos publicados pelo ONS e os dos arquivos da etapa; TOML é o formato aprovado do perfil; o SHA-256 é a conferência de conteúdo registrada nos manifestos e nas cópias.
- **Regras comuns**: as FR-001 a FR-015 (linha de comando, códigos de saída, perfil, pastas, `etapa.json`, pré-requisitos, `completo` e `copia-seguranca`) ficam nesta spec e valem para as cinco etapas. As demais specs trazem só o que é da etapa delas.
- **Fronteira com o Tratamento de dados**: a coleta identifica a usina, lê os números sem arredondar e audita cada arquivo; a convenção de hora, as duplicatas entre arquivos, o recorte no período, as ausências e as sinalizações de qualidade são do Tratamento (FR-040). A EVT é a exceção: sai da coleta já consolidada (FR-041).
- **Situação do `etapa.json` e códigos de saída** (FR-012 e FR-013): o código 3 grava `concluida`, com o código, porque a Conferência grava todos os resultados e só registra a meta não atingida; o `completo` para nele, mas a etapa seguinte, executada à parte, aceita a anterior. Os códigos 1 e 2 gravam `falha`, e a etapa seguinte recusa com código 5. Os códigos 4 e 5 não gravam nada. A regra foi alinhada com as specs das demais etapas.
- **Campos de texto do perfil** (FR-006): `usina.nome_curto` (obrigatório) e cinco textos opcionais levam ao relatório os trechos próprios da usina que hoje estão fixos no código, para que o relatório da São Domingos não mude e nenhum texto de usina fique fora do perfil. Os valores da São Domingos aparecem na tabela como exemplo identificado.
- **Sem marcadores de esclarecimento**: os pontos em aberto tinham default razoável, registrado nos requisitos e listado abaixo para a aprovação.
- **Pontos para a aprovação do usuário**, em que a spec uniformiza o comportamento de hoje entre os conjuntos:
  - arquivo de dados não obtido termina com código 2 em todos os conjuntos, depois de tentar os demais arquivos do conjunto (FR-026); hoje, na EVT, nos indicadores e na programação, a primeira falha de download interrompe a sincronização com código 1, e no cadastro a cópia local é usada sem falha;
  - as contagens de linhas só com o identificador, só com a conferência, irregulares e de valores inválidos valem para todos os conjuntos em que se aplicam (FR-036, FR-038, FR-039 e FR-046); hoje faltam nos indicadores, a contagem "só conferência" falta na programação, e os valores inválidos não são contados na EVT nem na programação;
  - nos indicadores por unidade geradora, a conferência pelo id ONS passa a valer em cada linha (hoje é só um aviso no log); nas taxas TEIFa e TEIP e nos parâmetros, que não publicam o id ONS, a extração continua só pelo CEG (FR-034 e FR-036);
  - usina sem nenhuma linha na EVT termina com código 2, como já acontece com a usina fora do cadastro (FR-041 e FR-045); hoje termina com 0 e só pula os demais conjuntos;
  - a auditoria passa a trazer o período e a data de publicação de cada arquivo, que o Tratamento usa para escolher entre horas repetidas e separar mês sem arquivo de mês sem a usina (FR-046);
  - o perfil ganha `usina.nome_curto` e cinco campos de texto opcionais, que não estavam no contrato do perfil (FR-006);
  - a poda das versões anteriores acontece quando uma nova versão é preservada (FR-029); hoje nenhum arquivo tem mais de uma versão anterior.
