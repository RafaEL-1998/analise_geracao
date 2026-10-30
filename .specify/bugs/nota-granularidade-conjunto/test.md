# Bug Verification: nota de granularidade errada na usina de conjunto com série própria

- **Slug**: nota-granularidade-conjunto
- **Tested**: 2026-10-30
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

O sintoma não se repete. Com o código de antes da correção (commit `10b40ee`), as quatro usinas da homologação trazem a nota "o ONS publica a geração do conjunto … (), e não a da usina isolada", com o identificador vazio. Com o código atual, a nota diz que a geração é a da própria usina e cita a Programação diária do conjunto com os códigos. Nos quatro relatórios, a única linha que muda é a da nota. Bandeirante e Seriemas 1 não mudam. Nenhuma regressão.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reprodução antes da correção | código de `10b40ee` num espaço isolado: `perfil --ceg <CEG>`, rascunho aceito só com os dados do ONS, `completo --sem-portal` | pass (reproduz) | UTE Eldorado, PCH Eng. E. J. Dreher, PCH Eng. Henrique Kotzian e UTE Santa Luzia I: relatório gerado (código 0) com a nota errada e "()" |
| Reprodução depois da correção | o mesmo, com o código atual, num espaço isolado novo | pass | as quatro: código 0; nota nova com a Programação diária e os códigos do conjunto; nenhum "()" no relatório |
| Escopo da mudança | `diff` do relatório em Markdown e `cmp` do resumo executivo, antes × depois, nas quatro | pass | no relatório, só a linha da nota (2 linhas no `diff`); resumo executivo igual (ele não repete a granularidade) |
| Códigos citados | conferência dos códigos da nota no catálogo da Programação diária | pass | Dreher e Kotzian citam "RSBCMO-9222; RSBCMO-9224; RSBCMO". O "RSBCMO" sem sufixo é um código publicado de fato pelo ONS, de 09/04/2025 a 14/08/2025 |
| Testes novos e alterados | `pytest tests/relatorio/test_estrutura.py` (dentro da suíte) | pass | `test_granularidade_com_a_geracao_da_usina_e_a_programacao_do_conjunto` e `test_notas_com_omissoes_niveis_e_nao_aplicaveis` aprovados |
| Suíte de regressão | `python -m pytest tests` no commit `ff0e449` | pass | 896 aprovados (pandas 3.0.6) |
| Lint | `python -m pyflakes src tests anexos` | pass | limpo |
| Princípio IX | as cinco referências com o código de `10b40ee` e com o atual, num espaço isolado, `completo --sem-portal` e `comparar` | pass | Bandeirante (geração do conjunto) e Seriemas 1 (restrição com detalhe), os dois ramos da nota que já existiam: a nota não muda. Única diferença: as duas células da Bandeirante do bug `zero-negativo-tabela` (aprovadas em 29/10/2026). Não é o `comparar --todas` (sem a Coleta congelada nesta máquina) |

Scripts e logs no scratchpad da sessão: `C:\Users\PICHAU\AppData\Local\Temp\claude\c--Users-PICHAU-analise-geracao-analise-geracao\7763ea5b-483c-4e7a-a4a5-045980cb5d12\scratchpad\teste\rodar_bugs.sh`, que grava `resultado_bugs.txt` e os relatórios em `casos\<versão>_<usina>\reports\`.

## Output Excerpts

UTE Eldorado, `diff` do relatório antes × depois (a única diferença):

```
< - Granularidade: o ONS publica a geração do conjunto Conj. Rio Brilhante (), e não a da usina isolada. Os números
<   do conjunto são identificados como tais e não são divididos entre as usinas; a conclusão da usina não usa números
<   do conjunto.
> - Granularidade: a geração é a da própria usina, mas o ONS publica a Programação diária (MSCRBR-9561; MSCRBR-9582)
>   do conjunto Conj. Rio Brilhante, e não da usina isolada. Esses números são identificados como do conjunto e não
>   são divididos entre as usinas; a conclusão da usina não usa números do conjunto.
```

PCH Dreher e Kotzian: "… a Programação diária (RSBCMO-9222; RSBCMO-9224; RSBCMO) do conjunto Conj. Boca do Monte …".

## Residual Risks

- O ramo novo da nota foi exercitado só com a Programação diária do conjunto. Os outros casos que ele cobre (fator de capacidade ou razão da restrição do conjunto, com a geração da usina) não têm usina real conhecida e estão só no código.
- Princípio IX conferido contra o código anterior, e não contra as referências congeladas. É preciso repetir `comparar --todas` na máquina com a Coleta congelada.

## Recommendation

Fechar o bug: está verificado com as quatro usinas reais da homologação, antes e depois. A mudança se limita à linha da nota, e as referências não mudam.
