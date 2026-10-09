# Contract: Relatórios de referência — `referencia`, `comparar --todas` e `copia-seguranca`

**Spec**: [spec.md](../spec.md) (FR-028, FR-029, SC-001) · **Data model**: [seção 8](../data-model.md) · **Research**: R22, R29

Os relatórios aprovados ficam em `relatorios_referencia/<slug>/`, com a Coleta e o perfil congelados da usina. A pasta é copiada para cada cópia de segurança (princípio IX, RT5). Este contrato cria o comando `referencia` e muda o `comparar` e a `copia-seguranca` de hoje.

## `referencia` (novo)

```text
python -m src referencia --usina <slug> --data-geracao "DD/MM/AAAA HH:MM" --aprovado-em "DD/MM/AAAA" [--log-level <nível>]
```

- Registra como referência o relatório da usina aprovado pelo usuário. É usado só depois da aprovação, cuja data vai em `--aprovado-em`.
- Lê e valida o perfil (código 4).
- **Exige**:
  - `reports/<slug>/` com o `etapa.json` do relatório `concluida` (não `desatualizada`), gerado com a data de `--data-geracao`, conferida no resumo do `etapa.json`;
  - a Coleta da usina `concluida`, no formato atual;
  - quando já existe uma referência da usina, que ela esteja commitada no git, para a anterior ficar no histórico (princípio IX).
- **Grava** numa pasta temporária, confere os SHA-256 e só então troca a referência anterior da usina (RT3):
  - os arquivos do relatório;
  - a Coleta congelada, em `coleta/`: só os arquivos listados no `etapa.json` da Coleta e o próprio `etapa.json`, sem `.bak`;
  - a cópia do perfil, em `perfil.toml`;
  - o `referencia.json`.
- Termina com a sugestão de commit: o relatório e o perfil entram no git, inclusive o PDF, por exceção no `.gitignore`. A Coleta congelada fica fora do git.

| Código | Situação |
|---|---|
| 0 | referência registrada e conferida |
| 1 | relatório gerado com outra data; referência anterior não commitada; falha de gravação ou de conferência (a referência anterior fica intacta) |
| 2 | opção inválida |
| 4 | perfil inválido |
| 5 | relatório ou Coleta da usina ausente, não concluída, desatualizada ou em formato antigo |

## `comparar --todas` (novo modo)

```text
python -m src comparar --usina <slug> --referencia <pasta>     # como hoje
python -m src comparar --todas [--coleta] [--log-level <nível>]
```

Com `--todas`, para cada `relatorios_referencia/<slug>/`:
1. copia a Coleta e o perfil congelados para um espaço isolado (pasta temporária);
2. executa ali o Tratamento, a Conferência, as Análises e o Relatório, com a data de geração do `referencia.json`. As etapas não leem `data/raw/`;
3. compara o relatório refeito com a referência, como o `comparar` de hoje: PDF, Markdown, CSV e figuras byte a byte; a planilha, célula a célula. `referencia.json`, `perfil.toml` e `coleta/` ficam fora da comparação;
4. avisa à parte, sem código 6, quando o perfil atual da usina difere do congelado;
5. apaga o espaço isolado.

Com `--coleta`, também:
- executa a Coleta da usina com `--sem-portal` e o perfil congelado, no espaço isolado;
- compara o resultado com a Coleta congelada:
  - as séries extraídas, linha a linha, só no período da referência;
  - as auditorias, só nas contagens por arquivo, sem as colunas de execução, como a data e a hora do processamento;
  - `dicionarios.csv` e `datas_obtencao.csv`, só como informação, sem código 6;
- mostra a diferença causada por arquivo republicado pelo ONS com o arquivo e a data de publicação, para o usuário decidir;
- as etapas 2 a 5 continuam partindo da Coleta congelada, não da refeita.

O `--coleta` é usado no fim de toda fase e, na fase A, depois de cada item (R27).

O modo `--todas`:
- não toca em `data/usinas/`, em `reports/` nem em `data/raw/`;
- não depende de outras usinas.

| Código | Situação |
|---|---|
| 0 | nenhuma diferença em nenhuma usina |
| 1 | sem referências; Coleta ou perfil congelados ausentes ou com SHA-256 diferente; erro numa etapa refeita |
| 2 | opção inválida (`--usina` com `--todas`, ou nenhum dos dois) |
| 6 | alguma usina com diferença |

## `copia-seguranca` (muda)

O comportamento de hoje continua ([contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md)). Além disso:
- copia `relatorios_referencia/` inteira para a cópia nova, inclusive a Coleta e o perfil congelados de cada usina;
- confere os arquivos pelos SHA-256 do `referencia.json` de cada usina;
- só então exclui as cópias mais antigas até ficarem duas;
- em falha, apaga a cópia nova, não exclui nenhuma outra e sai com 1;
- o `LEIA-ME.txt` lista as referências levadas, com a data de geração e a de aprovação de cada uma.

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Referência registrada | log, `INFO` | `Referência de '<slug>' registrada em relatorios_referencia/<slug>/ (gerada em <data>, aprovada em <data>). Sugestão de commit: <mensagem>` |
| Data diferente (`referencia`) | log, `ERROR` | `O relatório de '<slug>' foi gerado em <data do etapa.json>, não em <data pedida>. Gere com: python -m src relatorio --usina <slug> --data-geracao "<data pedida>"` |
| Referência anterior não commitada | log, `ERROR` | `A referência atual de '<slug>' tem mudanças fora do git. Faça o commit antes de substituí-la.` |
| Linha de cada usina (`--todas`) | saída padrão | `<slug>: nenhuma diferença`, ou `<slug>: <N> diferenças` seguida da lista de hoje |
| Perfil alterado | saída padrão | `<slug>: aviso: o perfil atual difere do congelado na referência (a comparação usou o congelado)` |
| Diferença na Coleta (`--coleta`) | saída padrão | `<slug>, Coleta: <arquivo>: <N> linhas diferentes no período da referência (publicação no ONS: <data>)` |
| Fim (`--todas`) | saída padrão | `Referências comparadas: <N>; com diferença: <D>.` |

## Exemplos

```powershell
# Fim de fase: refaz cada referência a partir da Coleta congelada, refaz também a Coleta, e compara
python -m src comparar --todas --coleta
$LASTEXITCODE   # 0 = nenhuma diferença

# Depois da aprovação do usuário, o relatório piloto vira referência
python -m src completo --usina william_arjona --data-geracao "30/10/2026 09:00"
python -m src referencia --usina william_arjona --data-geracao "30/10/2026 09:00" --aprovado-em "31/10/2026"
```
