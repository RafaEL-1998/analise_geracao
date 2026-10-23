# Contract: Linha de comando — Análises

**Spec**: [spec.md](../spec.md)

As regras comuns a todas as etapas estão no [contrato da Coleta de dados](../../001-coleta-dados/contracts/cli-coleta.md): sintaxe geral, perfil inválido, pré-requisito, `etapa.json`, comando `completo` e ferramenta `copia-seguranca`.

## Sintaxe

```text
python -m src analises --usina <slug> [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

| Opção | Obrigatória | Efeito |
|---|---|---|
| `--usina <slug>` | sim | usina do perfil `usinas/<slug>/perfil.toml` |
| `--log-level` | não | nível de log de todos os módulos executados na chamada; padrão `INFO` |

A etapa não tem opções próprias e vale para todos os tipos de usina (UHE, PCH, CGH, UTE, UTN, EOL e UFV). No `completo`, ela roda depois da Conferência, também sem opções.

## O que o comando faz

- **Escolhe o caminho** pela série de referência do perfil: na hidrelétrica com EVT, as análises sobre a base de EVT; nas demais usinas, as seções comuns sobre a base horária comum e as seções do tipo (spec, FR-052).
- **Lê** (só leitura):
  - `data/usinas/<slug>/tratamento/`: na hidrelétrica com EVT, a base de EVT e as bases complementares; nas demais, a base horária comum e as bases do tipo;
  - `data/usinas/<slug>/conferencia/conferencias.pkl` e, nas usinas sem EVT, `nao_aplicaveis.csv`;
  - os registros da Coleta em `data/usinas/<slug>/coleta/`, inclusive `datas_obtencao.csv` (datas de obtenção e resumo do manifesto) e, nas usinas sem EVT, o `etapa.json`, os trechos, a composição do conjunto, as unidades das usinas do conjunto e o tipo publicado.
  - Nada de `data/raw/`.
- **Grava**:
  - `data/usinas/<slug>/analises/resultados.pkl`, no formato 3, sem cópia `.bak`; conteúdo idêntico não é regravado;
  - `data/usinas/<slug>/analises/etapa.json`.
- Não acessa o portal do ONS e não altera nada das etapas anteriores. Os campos estão no [data-model](../data-model.md).

## Códigos de saída

| Código | Quando |
|---|---|
| 0 | sucesso: `resultados.pkl` gravado (ou inalterado) e `etapa.json` `concluida` |
| 1 | erro: entrada ausente ou ilegível, `conferencias.pkl` em outro formato, falha de gravação, outra exceção ou interrupção pelo usuário (Ctrl+C). O `etapa.json` fica `falha`, com o erro no `resumo`; o `resultados.pkl` anterior, se houver, fica como estava |
| 5 | Conferência sem `etapa.json` `concluida`: ausente, `falha`, `desatualizada` ou em outro formato (o atual é o 2). Nada é gravado. A Conferência concluída com código 3 (vazões abaixo da meta) é aceita |

Antes da etapa, o comando também pode terminar com 4 (perfil inválido) ou 2 (opção inválida), pelas regras comuns.

## Mensagens no log

- **Início**: `Etapa 'analises' da usina '<slug>' iniciada.`
- **Pré-requisito** (código 5): `A etapa 'analises' precisa da etapa 'conferencia' concluída para a usina '<slug>'. Execute antes: python -m src conferencia --usina <slug>`
- **Base complementar ausente** (aviso, só na hidrelétrica com EVT; a etapa continua): `Base '<base>' sem dados tratados para a usina: o relatório sai sem a seção correspondente.`, com `<base>` = `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao` ou `cadastro`. Nas usinas sem EVT, as seções e regras sem base não geram aviso: ficam em `omitidos`, com o motivo, e no `resumo` do `etapa.json`.
- **Gravação**: `<resultado>: resultados.pkl (<n> bytes)`, com `<resultado>` = `NOVO`, `ALTERADO` ou `INALTERADO`.
- **Erro** (código 1): `Etapa 'analises' da usina '<slug>' terminou com erro: <mensagem>`, com o rastreamento da exceção.
- **Interrupção** (código 1): `Etapa 'analises' da usina '<slug>' interrompida pelo usuário.`; se ocorrer durante a gravação, antes vem `Gravação de <arquivo> interrompida; o arquivo foi mantido na versão anterior.`
- **Fim**: `Etapa 'analises' da usina '<slug>': <status> (código <n>). Resumo: {…}. Pasta: <pasta>`, com o `resumo` do `etapa.json`.

Ao concluir, o `etapa.json` da Geração do relatório, se existir, passa a `desatualizada`.

## Exemplos

```powershell
# Refazer só as Análises da São Domingos, com a Conferência concluída
python -m src analises --usina sao_domingos

# Com log detalhado de todos os módulos
python -m src analises --usina sao_domingos --log-level DEBUG

# Uma usina sem EVT (térmica), com a Conferência concluída
python -m src analises --usina william_arjona

# Análises e relatório em sequência, só se as Análises terminarem com 0
python -m src analises --usina sao_domingos; if ($LASTEXITCODE -eq 0) { python -m src relatorio --usina sao_domingos }
```
