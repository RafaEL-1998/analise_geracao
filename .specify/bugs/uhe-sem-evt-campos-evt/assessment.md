# Bug Assessment: UHE sem EVT recusada pelos campos da trilha da EVT

- **Slug**: uhe-sem-evt-campos-evt
- **Created**: 2026-10-26
- **Source**: pasted text (achado 1 de `propostas/2026-10-26-homologacao-lote-1.md`)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

Na homologação de 26/10/2026, o perfil das UHE sem EVT foi recusado pelos mesmos campos exigidos da UHE com EVT:

> UHE Canastra (RS) e UHE Pimental (PA), com Dados hidrológicos e sem EVT: "parametros.engolimento_nominal_ug_m3s, garantia_fisica_mwmed, ip_referencia, teif_referencia, queda_bruta_m, perda_hidraulica_m, rendimento_turbina_gerador, vazao_remanescente_m3s, tipo_turbina, analises.vertimento_minimo_m3s, analises.faixas_geracao_mw: campo obrigatório ausente". UHE Anta (MG), sem EVT nem hidrologia: os mesmos 11 e mais 8 de cadastro.

## Symptom

A UHE sem EVT segue a trilha comum (a mesma da PCH e da CGH sem EVT), mas a conferência do perfil exige dela todos os campos da trilha da EVT, inclusive os que essa trilha não usa (garantia física, IP e TEIF de referência obrigatórios; vertimento mínimo e faixas de geração, que só a análise da EVT usa). A PCH, na mesma situação, roda.

## Reproduction

1. `python -m src perfil --ceg UHE.PH.RS.000635-1.01 --slug uhe_canastra` (catálogo de 23/10/2026).
2. Aceitar o rascunho só com os dados do ONS: `situacao = "conferido"`, `pendentes = []`, `parametros.fontes.geral` preenchida.
3. `python -m src completo --usina uhe_canastra`: o perfil é recusado com os 11 campos acima.

## Suspected Code Paths

- `src/comum/perfil_campos.py:CAMPOS` — no grupo `"UHE"`, os campos hidráulicos (`HIDRAULICOS`), `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia`, `analises`, `cod_usina`, `nome_ons` e `id_reservatorio` são `O` (obrigatórios sem condição); no grupo `"PCH_CGH"`, os mesmos são condicionados à cobertura (`_EVT_OU_HIDROLOGIA`, `_c("hidrologia")`, `_c("evt")`) ou opcionais.
- `src/comum/perfil_campos.py:1-13` — a docstring registra a decisão da fase A: "Na UHE, os campos e as regras de hoje continuam iguais" (para não mudar a São Domingos).
- `src/analises/hidrologia.py:55` e `src/relatorio/figuras_comum.py:_grafico_hidrologia_comum` — a trilha sem EVT com hidrologia usa o engolimento (faixas de afluência e linha do engolimento máximo).

## Root Cause Hypothesis

Na fase A, as exigências da UHE foram mantidas como as da São Domingos (trilha da EVT), e na fase D a trilha da hidrelétrica sem EVT foi criada só com PCH e CGH nos testes; nenhuma UHE sem EVT foi exercitada (em MS não há). A tabela `CAMPOS` não distingue a UHE com EVT da sem EVT. Confiança: alta.

## Proposed Remediation

**Preferred**: no grupo `"UHE"`, condicionar à cobertura os campos que só a trilha da EVT usa, como já é na PCH e na CGH: `analises` com `_c("evt")`; `garantia_fisica_mwmed`, `ip_referencia` e `teif_referencia` obrigatórios só com `_c("evt")` (opcionais sem a EVT, como na PCH); `HIDRAULICOS`, `cod_usina` e `nome_ons` com `_EVT_OU_HIDROLOGIA`; `id_reservatorio` com `_c("hidrologia")`. Na UHE com EVT (São Domingos), nada muda.

Efeito esperado na homologação: a UHE Anta passa a depender só do cadastro (dado ausente no ONS); Canastra e Pimental continuam exigindo os seis campos hidráulicos, porque a trilha com hidrologia usa o engolimento. Rodar essas duas só com dados do ONS depende do achado 2 (a trilha rodar sem os parâmetros técnicos), que é uma decisão de desenho à parte.

**Alternatives**:
- Unificar os grupos `"UHE"` e `"PCH_CGH"` numa só regra de hidrelétrica: mais simples, mas o `id_conjunto` e os membros hoje são "não se aplica" na UHE (nenhuma UHE do catálogo está em conjunto), e mudar isso é outra decisão.

**Files likely to change**:
- `src/comum/perfil_campos.py`
- `specs/001-coleta-dados/spec.md` (tabela dos campos do perfil por tipo) e `specs/001-coleta-dados/data-model.md` (seção 5.1)
- `tests/comum/test_perfil.py` (ou o teste dos campos por tipo)

**Tests to add or update**:
- UHE sem EVT e sem hidrologia: perfil válido sem os campos hidráulicos, sem `analises` e sem garantia física, IP e TEIF.
- UHE sem EVT com hidrologia: exige os campos hidráulicos e `id_reservatorio`, não exige `analises` nem garantia física, IP e TEIF.
- UHE com EVT: as exigências de hoje (todos obrigatórios).

## Risks & Considerations

- Princípio IX: nenhuma referência é UHE sem EVT; a São Domingos (com EVT) não muda. Conferir com `comparar --todas`.
- O rascunho do perfil (`perfil_rascunho.py`) lista os pendentes pela mesma tabela; a lista da UHE sem EVT fica menor, o que é o esperado.
- Spec da Coleta: a decisão "UHE como hoje" precisa ser revista na tabela de exigências, com a aprovação do usuário.

## Open Questions

- Respondida pelo usuário em 26/10/2026 ("I agree with item 1"): na UHE sem EVT, a garantia física, o IP e o TEIF ficam opcionais, como na PCH. A UHE com EVT continua como hoje: a análise da EVT e todos os campos obrigatórios ficam iguais.
