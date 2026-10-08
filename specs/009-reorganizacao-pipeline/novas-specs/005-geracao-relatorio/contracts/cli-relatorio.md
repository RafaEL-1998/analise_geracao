# Contract: Linha de comando — Geração do relatório

**Spec**: [spec.md](../spec.md)

As regras comuns às cinco etapas (sintaxe geral, perfil da usina, `etapa.json`, pré-requisitos, comando `completo`, ferramenta `copia-seguranca` e tabela completa dos códigos de saída) estão no [contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md).

## Sintaxe

```text
python -m src relatorio --usina <slug> [--data-geracao "DD/MM/AAAA HH:MM"] [--log-level {DEBUG,INFO,WARNING,ERROR}]
python -m src comparar  --usina <slug> --referencia <pasta> [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

O comando `completo` aceita `--data-geracao` e a repassa a esta etapa.

## Comando `relatorio`

| Opção | Obrigatória | Valor | Efeito |
|---|---|---|---|
| `--usina` | sim | slug, o nome da pasta em `usinas/` | usina do relatório; o perfil é lido e validado antes da etapa |
| `--data-geracao` | não | `"DD/MM/AAAA HH:MM"` | fixa a data e a hora de geração na capa do PDF, no cabeçalho do Markdown e no `resumo` do `etapa.json`, e monta o PDF no modo invariante, sem data de criação nem identificador variáveis. Sem a opção, vale a hora da execução, lida uma vez e igual nas três saídas, e o PDF sai sem o modo invariante |
| `--log-level` | não | `DEBUG`, `INFO` (padrão), `WARNING` ou `ERROR` | nível de todos os módulos executados na chamada |

- **Lê**: `data/usinas/<slug>/analises/etapa.json` e `resultados.pkl`, os `_manifesto_ons.json` de `data/raw/` e `usinas/<slug>/perfil.toml`. Não acessa a rede.
- **Grava**, em `reports/<slug>/`: `relatorio_analise_estatistica.pdf`, `relatorio_analise_estatistica.md`, `perfil_estatistico_anual.xlsx`, `perfil_estatistico_anual.csv`, `figures/*.png` e `etapa.json`, sem `.bak` ([data-model](../data-model.md), seção 2). As saídas são geradas em `reports/<slug>/.gravando/`, conferidas e só então substituem as da execução anterior; a pasta `.gravando/` é apagada ao fim. Se a geração, a conferência ou a troca falharem, as saídas anteriores ficam como estavam; a que não puder voltar de uma troca interrompida fica em `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`. Depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/`.
- **Pré-requisito**: Análises concluídas e no formato atual. Senão, o log registra `A etapa 'relatorio' precisa da etapa 'analises' concluída para a usina '<slug>'. Execute antes: python -m src analises --usina <slug>`, e o comando termina com código 5, sem gravar nada.
- **`--data-geracao` em formato inválido**: recusada pela linha de comando antes de qualquer execução, com o uso do comando e `argument --data-geracao: data de geração inválida: '<texto>' (use "DD/MM/AAAA HH:MM")`; código 2.
- **Log**: as mensagens da etapa (figuras, planilha, CSV, Markdown e PDF gravados; figura de execução anterior removida) e, no fim, `Etapa 'relatorio' da usina '<slug>': <status> (código <n>). Resumo: {...}. Pasta: <pasta do relatório>`. Avisos sem falha: constatação sem seção, chave ou aba sem fonte mapeada, figura sem legenda, fonte TrueType ausente, legendas ou constatações do PDF em número diferente do esperado. Uma troca interrompida registra o erro "Troca das saídas do relatório interrompida; as da execução anterior foram mantidas." ou, se algum arquivo não voltou, a lista deles e a pasta `.anteriores_<AAAAMMDDTHHMMSS>/`.

### Códigos de saída

| Código | Quando |
|---|---|
| 0 | relatório gravado; `etapa.json` `concluida` |
| 1 | erro ao montar, conferir ou trocar qualquer saída, inclusive o PDF, `resultados.pkl` em outra versão de formato ou interrupção pelo usuário (Ctrl+C); erro no log, `etapa.json` `falha` e saídas da execução anterior mantidas |
| 2 | opção inválida, inclusive `--data-geracao` fora do formato; nada é executado |
| 4 | perfil da usina inválido; nada é gravado |
| 5 | Análises ausentes, com falha, desatualizadas ou em outro formato; nada é gravado |

## Ferramenta `comparar`

Compara o relatório atual, `reports/<slug>/`, com o de uma pasta de referência de mesma estrutura, como a pasta `reports/<slug>/` de uma cópia de segurança do projeto. Não é etapa: não confere o `etapa.json` nem grava nada.

| Opção | Obrigatória | Valor | Efeito |
|---|---|---|---|
| `--usina` | sim | slug | define a pasta atual; o perfil é lido e validado |
| `--referencia` | sim | pasta | pasta com o relatório de referência |
| `--log-level` | não | como acima | aceito; a comparação escreve só na saída padrão |

**Regras**:
- os arquivos das duas pastas são percorridos com as subpastas, inclusive as ocultas (uma `.anteriores_<AAAAMMDDTHHMMSS>/` deixada por uma troca interrompida aparece como arquivos só numa das pastas); todo arquivo chamado `etapa.json` fica fora;
- arquivo presente só numa das pastas é diferença;
- `.xlsx`: comparada aba a aba, com as mesmas abas na mesma ordem (senão, uma diferença e nenhuma célula comparada), a mesma quantidade de linhas e cada célula; números iguais até a 12ª casa relativa (`rel_tol` 1e-12), NaN igual a NaN, texto e booleano por igualdade; até 20 células listadas por aba, mais uma linha com o total;
- todos os demais arquivos (PDF, Markdown, CSV, figuras): byte a byte.

**Saída padrão**: uma linha por diferença, em ordem de arquivo, num destes formatos:

```text
<arquivo>: só na referência
<arquivo>: só na pasta atual
<arquivo>: conteúdo diferente (<n> bytes na atual, <m> na referência)
<planilha>: abas diferentes ou em outra ordem (só na atual: [...]; só na referência: [...])
<planilha> [<aba>]: <n> linhas na atual e <m> na referência
<planilha> [<aba>] <célula>: <valor> na atual, <valor> na referência
<planilha> [<aba>]: mais <k> células diferentes (<t> no total)
```

A última linha é `<n> diferença(s).` ou, sem diferença, `Nenhuma diferença.`.

Qualquer erro na comparação, como pasta inexistente, arquivo ilegível ou planilha que não abre como XLSX, sai na saída de erro como `Erro na comparação: <motivo>` (por exemplo, `pasta inexistente: <pasta>`), com código 1.

### Códigos de saída

| Código | Quando |
|---|---|
| 0 | nenhuma diferença |
| 6 | há diferenças, listadas na saída |
| 1 | erro: pasta atual ou de referência inexistente, arquivo ilegível ou planilha que não abre |
| 2 | opção inválida, como `--referencia` ausente |
| 4 | perfil da usina inválido |

## Exemplos

```powershell
# Gerar o relatório da São Domingos; a data de geração é a da execução
python -m src relatorio --usina sao_domingos

# Regerar com a data da versão de referência e conferir que o relatório não mudou
python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"
python -m src comparar --usina sao_domingos --referencia "_backup_AAAA-MM-DD_motivo\reports\sao_domingos"
```
