# Bug Verification: rascunho do perfil aceito para usina sem série de referência

- **Slug**: rascunho-sem-serie-referencia
- **Tested**: 2026-10-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

O sintoma não se repete. Com o código de antes da correção (commit `10b40ee`), as nove usinas da homologação ganham o rascunho e são recusadas só na Coleta; com o código atual, as nove são recusadas já no rascunho, com código 2, a mensagem nova e nada gravado. As usinas com série de referência (as cinco referências, Ilha Solteira, Angra I) continuam com o rascunho. No catálogo inteiro, a decisão do rascunho passa a ser a mesma da Coleta. Nenhuma regressão.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reprodução antes da correção | código de `10b40ee` num espaço isolado: `perfil --ceg <CEG> --slug <slug>`, rascunho aceito, `completo --sem-portal` | pass (reproduz) | as nove usinas (UTE Suzano RRP1, Amandina II, Fibria MS, Fibria MS-II, Costa Rica, Iaco Agrícola, Bracell; PCH São Lourenço-MT e Cabeça de Boi): `perfil` código 0 com o rascunho gravado e Coleta recusada (código 1) por falta de série de referência |
| Reprodução depois da correção | `perfil --ceg` com o código atual, num espaço isolado novo | pass | as nove: código 2, "O ONS não publica a série de referência da usina …", nenhum `perfil.toml` gravado |
| Usinas com série de referência | `perfil --ceg` das cinco referências, da UHE Ilha Solteira e da UTN Angra I, com os dois códigos | pass | código 0 e rascunho gravado nos dois. Inclui a geração do conjunto (Bandeirante) e a restrição com detalhe própria (Seriemas 1) |
| Catálogo inteiro | `rascunho_catalogo.py`: decisão do rascunho antes × agora nas 5.937 usinas dos tipos atendidos | pass | 69 usinas passam a ser recusadas (51 UTE e 18 PCH; em MS, as seis da homologação), todas sem série de referência; nenhuma passa a ganhar rascunho; `_resolver_usina` concorda com a regra da Coleta em todas |
| Testes novos e alterados | `pytest tests/coleta/test_perfil_rascunho.py tests/coleta/test_serie_referencia.py tests/coleta/test_registro.py` (dentro da suíte) | pass | os quatro casos do `fix.md` aprovados |
| Suíte de regressão | `python -m pytest tests` no commit `ff0e449` | pass | 896 aprovados (pandas 3.0.6) |
| Lint | `python -m pyflakes src tests anexos` | pass | limpo |
| Princípio IX | as cinco referências com o código de `10b40ee` e com o atual, num espaço isolado, `completo --sem-portal` e `comparar` | pass | São Domingos, William Arjona, Seriemas 1 e Praia Formosa sem nenhuma diferença; Bandeirante, só as duas células do bug `zero-negativo-tabela` (aprovadas em 29/10/2026). Não é o `comparar --todas` (sem a Coleta congelada nesta máquina) |

Scripts e logs no scratchpad da sessão: `C:\Users\PICHAU\AppData\Local\Temp\claude\c--Users-PICHAU-analise-geracao-analise-geracao\7763ea5b-483c-4e7a-a4a5-045980cb5d12\scratchpad\teste\rodar_bugs.sh` (logs em `casos\`) e `rascunho_catalogo.py` (saída em `rascunho_catalogo.txt`).

## Output Excerpts

Código de antes, UTE Suzano RRP1 (o mesmo nas nove):

```
antigo ute_suzano_rrp1 perfil=0 rascunho=sim completo=1
[ERROR] coleta - Coleta recusada: a usina 'ute_suzano_rrp1' não tem série de referência: nem a Energia Vertida
Turbinável nem a Geração por usina (da usina ou do conjunto) na [cobertura].
```

Código atual:

```
novo ute_suzano_rrp1 perfil=2 rascunho=nao
[ERROR] O ONS não publica a série de referência da usina UTE SUZANO RRP1 (UTE.FL.MS.049647-2.01): nem a Energia
Vertida Turbinável nem a Geração por usina, da usina ou do conjunto. Dos conjuntos de série, o catálogo encontra só:
programacao = "proprio". Sem a série de referência, a usina não tem relatório individual.
```

Catálogo inteiro:

```
usinas dos tipos atendidos: 5937
  rascunho antes e agora: 1946
  rascunho antes, recusada agora (sem série de referência): 69
  recusada antes e agora: 3922
  recusada antes, rascunho agora: 0
_resolver_usina diverge da regra acima: 0
```

## Residual Risks

- Os números de cobertura do catálogo (as usinas "próprias" no Brasil) ainda contam as 69 usinas sem série de referência. A recontagem fica para a coluna `serie_referencia` da melhoria 5, como o usuário decidiu.
- Princípio IX conferido contra o código anterior, e não contra as referências congeladas. É preciso repetir `comparar --todas` na máquina com a Coleta congelada.

## Recommendation

Fechar o bug: está verificado com as nove usinas reais da homologação, antes e depois, e com a decisão do rascunho igual à da Coleta no catálogo inteiro.
