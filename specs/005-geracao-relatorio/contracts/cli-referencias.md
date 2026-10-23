# Contract: Relatórios de referência — `referencia`, `comparar --todas` e `copia-seguranca`

**Spec**: [spec.md](../spec.md) (FR-042, FR-043, FR-069, US8, SC-001, SC-013, SC-014) · **Data model**: [seção 7](../data-model.md) · **Plano**: decisões técnicas D17 e D21

Os relatórios aprovados ficam em `relatorios_referencia/<slug>/`, com a Coleta e o perfil congelados da usina. A pasta é copiada para cada cópia de segurança (constituição, princípio IX e Requisito Técnico 5). Este contrato descreve o comando `referencia`, o modo `--todas` do `comparar` e o que a `copia-seguranca` faz com as referências. O `comparar --usina --referencia` está em [cli-relatorio.md](cli-relatorio.md); as regras comuns, no [contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md).

## `referencia`

```text
python -m src referencia --usina <slug> --data-geracao "DD/MM/AAAA HH:MM" --aprovado-em "DD/MM/AAAA" [--log-level <nível>]
```

- Registra como referência o relatório da usina aprovado pelo usuário. É usado só depois da aprovação, cuja data vai em `--aprovado-em`.
- Lê e valida o perfil (código 4).
- **Exige**:
  - `reports/<slug>/` com o `etapa.json` do relatório `concluida` (não `desatualizada`) no formato atual, gerado com a data de `--data-geracao`, conferida no `resumo` do `etapa.json`;
  - a Coleta da usina `concluida`, no formato atual;
  - quando já existe uma referência da usina, que ela esteja commitada no git, para a anterior ficar no histórico (princípio IX).
- **Grava** numa pasta temporária (`relatorios_referencia/.gravando_<slug>/`), confere os SHA-256 e só então troca a referência anterior da usina:
  - os arquivos do relatório, os do `etapa.json` dele, inclusive o resumo executivo, cada um conferido contra o SHA-256 de origem;
  - a Coleta congelada, em `coleta/`: só os arquivos listados no `etapa.json` da Coleta e o próprio `etapa.json`, sem `.bak`;
  - a cópia do perfil, em `perfil.toml`;
  - o `referencia.json`, com `usina`, `data_geracao`, `aprovado_em`, `periodo`, `arquivos`, `perfil` e `coleta`.
- Termina com a sugestão de commit: o relatório e o perfil entram no git, inclusive o PDF, por exceção no `.gitignore`. A Coleta congelada fica fora do git.

| Código | Situação |
|---|---|
| 0 | referência registrada e conferida |
| 1 | relatório gerado com outra data; referência anterior não commitada; falha de gravação ou de conferência (a referência anterior fica intacta) |
| 2 | opção inválida, inclusive data em formato inválido |
| 4 | perfil inválido |
| 5 | relatório ou Coleta da usina ausente, não concluída, desatualizada ou em formato antigo |

## `comparar --todas`

```text
python -m src comparar --usina <slug> --referencia <pasta>     # cli-relatorio.md
python -m src comparar --todas [--coleta] [--log-level <nível>]
```

Com `--todas`, para cada `relatorios_referencia/<slug>/` (sem as pastas que começam por "." ou "_"):
1. confere o perfil e a Coleta congelados pelos SHA-256 do `referencia.json`;
2. copia a Coleta e o perfil congelados para um espaço isolado (pasta temporária);
3. executa ali o Tratamento, a Conferência, as Análises e o Relatório, com a data de geração do `referencia.json`. As etapas não leem `data/raw/`;
4. compara o relatório refeito com a referência, como o `comparar` de `cli-relatorio.md`: PDF, Markdown, CSV, figuras e resumo executivo byte a byte; a planilha, célula a célula. `referencia.json`, `perfil.toml` e `coleta/` ficam fora da comparação;
5. avisa à parte, sem código 6, quando o perfil atual da usina difere do congelado;
6. apaga o espaço isolado.

Com `--coleta`, também:
- executa a Coleta da usina com `--sem-portal` e o perfil congelado, noutro espaço isolado, lendo os brutos de `data/raw/` sem gravar neles;
- compara o resultado com a Coleta congelada:
  - as séries extraídas, linha a linha, só nas linhas cujo intervalo (hora, dia, mês ou ano) toca o período da referência;
  - as auditorias, só nas contagens por arquivo, sem as colunas de execução (`data_hora_processamento`);
  - `dicionarios.csv`, `datas_obtencao.csv` e `dicionario_evt.json`, só como informação, sem código 6;
- mostra a diferença numa série com a data de publicação no ONS dos arquivos de origem, para o usuário decidir;
- as etapas 2 a 5 continuam partindo da Coleta congelada, não da refeita.

O modo `--todas`:
- não toca em `data/usinas/`, em `reports/` nem em `data/raw/`;
- não depende de outras usinas;
- com erro numa referência (Coleta ou perfil congelados ausentes ou com SHA-256 diferente, ou erro numa etapa refeita), segue para as demais e termina com código 1.

| Código | Situação |
|---|---|
| 0 | nenhuma diferença em nenhuma usina |
| 1 | sem referências; Coleta ou perfil congelados ausentes ou com SHA-256 diferente; erro numa etapa refeita |
| 2 | opção inválida (`--usina` ou `--referencia` com `--todas`, `--coleta` sem `--todas`, ou nenhum dos modos) |
| 6 | alguma usina com diferença |

## `copia-seguranca` com as referências

O comportamento da ferramenta está no [contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md). Com as referências:
- copia `relatorios_referencia/` inteira para a cópia nova, inclusive a Coleta e o perfil congelados de cada usina, sem as pastas temporárias do `referencia`;
- confere os arquivos pelos SHA-256 do `referencia.json` de cada usina;
- só então exclui as cópias mais antigas até ficarem duas;
- em falha, apaga a cópia nova, não exclui nenhuma outra e sai com 1;
- o `LEIA-ME.txt` lista as referências levadas, com a data de geração e a de aprovação de cada uma.

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Referência registrada | log, `INFO` | `Referência de '<slug>' registrada em relatorios_referencia/<slug>/ (gerada em <data>, aprovada em <data>). Sugestão de commit: git add relatorios_referencia/<slug> && git commit -m "docs: relatório de referência de <slug> (gerado em <data>, aprovado em <data>)"` |
| Etapa não concluída (`referencia`, 5) | log, `ERROR` | `A etapa '<relatorio ou coleta>' da usina '<slug>' não está concluída no formato atual (ausente, desatualizada, com falha ou em formato antigo). Execute: python -m src completo --usina <slug>` |
| Data diferente (`referencia`, 1) | log, `ERROR` | `O relatório de '<slug>' foi gerado em <data do etapa.json>, não em <data pedida>. Gere com: python -m src relatorio --usina <slug> --data-geracao "<data pedida>"` |
| Referência anterior não commitada (1) | log, `ERROR` | `A referência atual de '<slug>' tem mudanças fora do git. Faça o commit antes de substituí-la.` |
| Falha de gravação ou de conferência (1) | log, `ERROR` | `Referência de '<slug>' não registrada: <motivo>. A referência anterior não foi alterada.` |
| Linha de cada usina (`--todas`) | saída padrão | `<slug>: nenhuma diferença`, ou `<slug>: <N> diferenças` seguida da lista de diferenças do `comparar` |
| Perfil alterado | saída padrão | `<slug>: aviso: o perfil atual difere do congelado na referência (a comparação usou o congelado)` |
| Diferença na Coleta (`--coleta`) | saída padrão | `<slug>, Coleta: <arquivo>: <N> linhas diferentes no período da referência (publicação no ONS: <data>)`; ou `: ausente na Coleta refeita`, `: só na Coleta refeita`, `: <N> arquivos com contagens diferentes`, `: <N> linhas diferentes`, `: conteúdo diferente` |
| Informação da Coleta (`--coleta`) | saída padrão | `<slug>, Coleta (informação): <arquivo>: diferente do congelado` |
| Erro numa referência | saída de erro | `<slug>: erro: <motivo>` |
| Sem referências (1) | saída de erro | `Nenhum relatório de referência em <pasta>.` |
| Fim (`--todas`) | saída padrão | `Referências comparadas: <N>; com diferença: <D>.`; com erro, também `Referências com erro: <E>.` na saída de erro |

## Exemplos

```powershell
# Depois de cada mudança do código: refaz cada referência a partir da Coleta congelada, refaz também a Coleta, e compara
python -m src comparar --todas --coleta
$LASTEXITCODE   # 0 = nenhuma diferença

# Depois da aprovação do usuário, o relatório piloto vira referência
python -m src completo --usina william_arjona --data-geracao "20/10/2026 09:00"
python -m src referencia --usina william_arjona --data-geracao "20/10/2026 09:00" --aprovado-em "20/10/2026"
```
