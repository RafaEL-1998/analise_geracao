# Bug Verification: unidade geradora com letra no nome (ciclo combinado)

- **Slug**: unidade-com-letra
- **Tested**: 2026-10-29 (segunda rodada, depois do ajuste do prefixo "UG")
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

O sintoma não se repete. Com o código de antes da correção (commit `10b40ee`), a UTE Três Lagoas real para com `int(NaN)`; com o código atual, gera o relatório completo com as seis unidades separadas. A primeira rodada achou uma regressão causada pela correção, na UHE Santa Branca: o rótulo "UG1" dos parâmetros das taxas não juntava com o "1" dos indicadores. O ajuste aprovado pelo usuário ("vamos com suas recomendações") resolveu o caso. Agora a junção fecha em todo o Brasil, e as cinco referências, a suíte e o pyflakes não mudam.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reprodução antes da correção | código de `10b40ee` (`git archive`) num espaço isolado: `completo --usina ute_tres_lagoas --sem-portal --data-geracao "29/10/2026 08:00"` | pass (reproduz) | código 1: `ValueError: cannot convert float NaN to integer` no Relatório (`conteudo.py:365`). As seis unidades ficam com `ug` vazio e caem na deduplicação: 630 → 105 linhas mensais, nenhuma linha de horas por estado e Conferência `dispf_horas` "não aplicável" |
| Reprodução depois da correção | o mesmo comando, com o código atual, num espaço isolado novo | pass | código 0; 12 seções, 28 páginas. 630 linhas mensais (6 × 105), 469 meses-unidade de horas, `dispf_horas` aplicável (469 comparados). C2 e C10 entram na conclusão. "UG1A" a "UG2C" no relatório, nenhuma linha sem rótulo |
| Testes novos e alterados | `pytest tests/tratamento/test_indicadores.py`, mais os testes das Análises e da conclusão listados no `fix.md` | pass | 13 aprovados no Tratamento (com `test_unidade_com_prefixo_ug_no_nome_e_o_numero`); os das Análises e da conclusão também aprovados |
| Suíte de regressão | `python -m pytest tests` | pass | 896 aprovados (pandas 3.0.6) |
| Lint | `python -m pyflakes src tests anexos` | pass | limpo |
| Princípio IX (cinco referências) | `completo --sem-portal` num espaço isolado; `cmp` das seis tabelas por unidade e `comparar --referencia` contra o estado de antes da correção | pass | 5 de 5 sem diferença, nas duas rodadas. Não é o `comparar --todas` (sem a Coleta congelada nesta máquina) |
| Leitura do rótulo em todos os brutos do ONS | `juncao.py` com o código antigo e com o atual | pass | `ug` vazio: antes, 2.800 linhas mensais, 388 anuais e 12.246 linhas de parâmetros; agora, nenhuma. Nos indicadores, rótulo do número = rótulo do nome nas 126.307 linhas |
| Junção (CEG, mês, unidade): parâmetros × indicadores mensais, Brasil | `juncao.py`, a chave da Conferência, em todos os 246 CEG das duas bases | pass | código antigo: 456 chaves sem par (três térmicas com rótulo com letra). Primeira rodada: 144 (UHE Santa Branca, regressão). Depois do ajuste: **nenhuma das 81.754** |
| UHE Santa Branca (caso da regressão) | Tratamento das linhas do CEG `UHE.PH.SP.002696-4.01` nos brutos | pass | unidades 1 e 2, inteiras ("UG1", "UG2"); junção de 162 em 162 meses-unidade, como no código antigo (na primeira rodada, 18 de 162 e quatro unidades) |

Scripts e saídas no scratchpad da sessão:
- `C:\Users\PICHAU\AppData\Local\Temp\claude\c--Users-PICHAU-analise-geracao-analise-geracao\7763ea5b-483c-4e7a-a4a5-045980cb5d12\scratchpad\teste\rodar.sh`, que grava `resultado.txt` e os logs;
- `C:\Users\PICHAU\AppData\Local\Temp\claude\c--Users-PICHAU-analise-geracao-analise-geracao\7763ea5b-483c-4e7a-a4a5-045980cb5d12\scratchpad\teste\juncao.py`, que grava `juncao_antigo.txt` e `juncao_novo.txt`;
- a primeira rodada está nos arquivos com o sufixo `_v1`.

## Output Excerpts

Código antigo, UTE Três Lagoas:

```
[WARNING] tratamento - indicadores mensais: 630 linhas com chave repetida ['mes', 'ug']; prevalece o arquivo lido por último.
[WARNING] conferencia - Conferência 'dispf_horas' não aplicável: ...
  File "...\src\relatorio\conteudo.py", line 365, in linhas_tabela_ons_ug_anual
    [_rotulo_ano(r.ano, r.ano_parcial), f"UG{int(r.ug)}", ...
ValueError: cannot convert float NaN to integer
Fluxo completo interrompido na etapa 'relatorio' (código 1).
```

Código atual, UTE Três Lagoas:

```
"indicadores": {"linhas_mensais": 630, "linhas_anuais": 94, "meses_unidade_horas_estado": 469, ...}
"dispf_horas": {"aplicavel": true, "unidade": "meses-unidade", "comparados": 469, "coincidentes": 449, "divergentes": 20}
"regras_da_conclusao": ["C2", "C10", "C12", "C14", "C15"]
Etapa 'relatorio' ...: concluida (código 0). {"secoes": 12, "paginas_pdf": 28, ...}
```

Cinco referências: `Nenhuma diferença.` e `comparar: código 0` nas cinco.

Junção no Brasil, depois do ajuste:

```
parâmetros das taxas: 674347 linhas; sem rótulo no nome 0
CEG nas duas bases: 246; com rótulo dos parâmetros ausente nos indicadores: 0
chaves (CEG, mês, unidade) dos parâmetros: 81754; sem par nos indicadores: 0
```

UHE Santa Branca:

```
brutos, parâmetros 2020–2025: "UG 28,0 MW SANTA BRANCA UG1 SP"   2026 e indicadores: "... SANTA BRANCA 1 SP"
primeira rodada: horas ['UG1', 'UG2', '1', '2'] | junção (mês, ug): 18 de 162
após o ajuste:   horas [1, 2] Int64            | junção (mês, ug): 162 de 162
```

## Residual Risks

- **A reprodução difere da avaliação**. O código antigo parou no Relatório (`conteudo.py:365`), e não na C10 das Análises. Com os dados de 29/10/2026, as seis unidades viram uma só unidade vazia antes das Análises, e a C10 nem se aplica. A causa é a mesma (`ug` vazio e depois `int(NaN)`). O código atual roda a C10 e a C2 com rótulos com letra.
- **Princípio IX conferido contra uma linha de base**, e não contra as referências congeladas. É preciso repetir `comparar --todas` na máquina com a Coleta congelada.
- **Usinas sem perfil**: o fluxo completo rodou só na Três Lagoas. Nas outras usinas com rótulo com letra ou prefixo (Itaipu, Fontes Nova, Prosperidade II e III, Paulínia Verde, Santa Branca etc.), foram conferidos a leitura do rótulo e a junção. A Itaipu depende do achado 2.
- **Rótulo de formato novo**: um formato que o ONS publique no futuro só numa das bases (como foi o "UG1") quebraria a junção sem erro. O `juncao.py` mede isso. Fica a sugestão de um aviso da Conferência quando houver unidades dos parâmetros sem par nos indicadores, mas isso está fora do escopo deste bug.
- **O nome "UG TG10"**, com espaço quando o rótulo começa por letra, não apareceu em nenhum relatório real.

## Recommendation

Fechar o bug: está verificado de ponta a ponta, com a reprodução real antes e depois, sem regressão nas referências nem na junção em todo o Brasil. Fica pendente só o `comparar --todas` na máquina com a Coleta congelada, junto com o novo registro da Bandeirante (bug `zero-negativo-tabela`).
