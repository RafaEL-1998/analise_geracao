# Bug Verification: UHE sem EVT recusada pelos campos da trilha da EVT

- **Slug**: uhe-sem-evt-campos-evt
- **Tested**: 2026-10-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

O sintoma não se repete. Com o código de antes da correção (commit `10b40ee`), Canastra e Pimental são recusadas pelos 11 campos da trilha da EVT, e a Anta por 19; com o código atual, Canastra e Pimental só pelos seis parâmetros hidráulicos que a trilha com hidrologia usa, e a Anta só pelo cadastro e pelo código de programação. A UHE com EVT (São Domingos) não muda. Com valores fictícios nos seis parâmetros, a Canastra roda o fluxo inteiro: é a primeira UHE sem EVT exercitada de ponta a ponta. Nenhuma regressão.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reprodução antes da correção | código de `10b40ee` num espaço isolado: `perfil --ceg <CEG> --slug <slug>`, rascunho aceito só com os dados do ONS, `completo --sem-portal` | pass (reproduz) | Canastra e Pimental: código 4, os 11 campos do relato (hidráulicos, garantia física, IP, TEIF, vertimento mínimo e faixas de geração). Anta: os mesmos 11 e mais 8 |
| Reprodução depois da correção | o mesmo, com o código atual, num espaço isolado novo | pass | Canastra e Pimental: só os seis hidráulicos ("obrigatório para UHE com a cobertura "proprio" em hidrologia"). Anta: só início da operação, potência instalada e unitária, unidades e `cod_programacao` (cadastro que o ONS não publica e melhoria 5) |
| Trilha da UHE sem EVT de ponta a ponta | Canastra com os seis hidráulicos FICTÍCIOS (só no espaço isolado), `completo --sem-portal` | pass | código 0 nas cinco etapas; 12 seções, 18 páginas; regras C8, C10 e C20; nenhuma exceção. O relatório não tem uso: os valores não são da usina |
| Testes novos e alterados | `pytest tests/comum/test_perfil.py` (dentro da suíte) | pass | os seis casos do `fix.md` aprovados |
| Suíte de regressão | `python -m pytest tests` no commit `ff0e449` | pass | 896 aprovados (pandas 3.0.6) |
| Lint | `python -m pyflakes src tests anexos` | pass | limpo |
| Princípio IX | as cinco referências com o código de `10b40ee` e com o atual, num espaço isolado, `completo --sem-portal` e `comparar` | pass | São Domingos, William Arjona, Seriemas 1 e Praia Formosa sem nenhuma diferença; Bandeirante, só as duas células do bug `zero-negativo-tabela` (aprovadas em 29/10/2026). Não é o `comparar --todas` (sem a Coleta congelada nesta máquina) |
| Rascunho das referências | `perfil --ceg` das cinco referências, da Ilha Solteira e da Angra I, com os dois códigos | pass | código 0 e rascunho gravado nos dois |

Scripts e logs no scratchpad da sessão: `C:\Users\PICHAU\AppData\Local\Temp\claude\c--Users-PICHAU-analise-geracao-analise-geracao\7763ea5b-483c-4e7a-a4a5-045980cb5d12\scratchpad\teste\rodar_bugs.sh` (com `aceitar.py`), que grava `resultado_bugs.txt` e os logs em `casos\`.

## Output Excerpts

Código de antes, Canastra (e Pimental):

```
parametros.engolimento_nominal_ug_m3s, garantia_fisica_mwmed, ip_referencia, teif_referencia, queda_bruta_m,
perda_hidraulica_m, rendimento_turbina_gerador, vazao_remanescente_m3s, tipo_turbina,
analises.vertimento_minimo_m3s, analises.faixas_geracao_mw: campo obrigatório ausente
```

Código atual, Canastra (e Pimental):

```
Perfil da usina 'uhe_canastra' inválido (usinas/uhe_canastra/perfil.toml):
- parametros.engolimento_nominal_ug_m3s: obrigatório para UHE com a cobertura "proprio" em hidrologia
- parametros.queda_bruta_m / perda_hidraulica_m / rendimento_turbina_gerador / vazao_remanescente_m3s / tipo_turbina: idem
```

Código atual, Anta:

```
- usina.inicio_operacao_comercial: campo obrigatório ausente
- identificacao.cod_programacao: campo obrigatório ausente
- parametros.potencia_instalada_mw / unidades_geradoras / potencia_unitaria_mw: campo obrigatório ausente
```

Canastra com os hidráulicos fictícios:

```
Etapa 'coleta' … 'tratamento' … 'conferencia' … 'analises' … 'relatorio': concluida (código 0)
"regras_da_conclusao": ["C8", "C10", "C20"]   "secoes": 12, "paginas_pdf": 18
```

## Residual Risks

- Canastra e Pimental continuam sem relatório só com os dados do ONS, porque a trilha com hidrologia usa o engolimento. Isso é o achado 2 da homologação, decisão de desenho à parte, e não este bug.
- A trilha da UHE sem EVT e sem hidrologia (caso da Anta) não rodou de ponta a ponta, porque faltam o cadastro e o código de programação. A da PCH, na mesma trilha, roda nas referências.
- Princípio IX conferido contra o código anterior, e não contra as referências congeladas. É preciso repetir `comparar --todas` na máquina com a Coleta congelada.

## Recommendation

Fechar o bug: está verificado com os casos reais da homologação, antes e depois, sem mudança na UHE com EVT nem nas referências. Para rodar a Canastra e a Pimental só com os dados do ONS, o caminho é o achado 2, em avaliação própria.
