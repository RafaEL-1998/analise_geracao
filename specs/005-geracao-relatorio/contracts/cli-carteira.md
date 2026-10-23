# Contract: Linha de comando — relatório de carteira (`carteira`)

**Spec**: [spec.md](../spec.md) (FR-049, US10, SC-012) · **Data model**: [seção 6](../data-model.md) · **Plano**: decisão técnica D22

As regras comuns (sintaxe geral, `--log-level` e códigos de saída) estão no [contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md). O catálogo de usinas é montado pelo comando `usinas`, da Coleta.

## Sintaxe

```text
python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao "DD/MM/AAAA HH:MM"] [--log-level <nível>]
```

| Opção | Efeito |
|---|---|
| `--estado <UF>` | sigla do estado (2 letras, sem diferença entre maiúsculas e minúsculas) |
| `--tipo <tipo>` | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL` ou `UFV` (a linha de conjunto do catálogo não é usina) |
| `--data-geracao` | fixa a data de geração e torna o PDF reproduzível byte a byte, como no relatório da usina |

É preciso pelo menos uma das opções `--estado` e `--tipo`: a carteira é de um estado, de um tipo ou de um tipo num estado (constituição, princípio III). Sem nenhuma das duas, código 2, com `carteira: use --estado, --tipo ou os dois`. Estado ou tipo inválido também dá código 2 (`estado inválido: '<texto>' (use a sigla, com 2 letras)`; `tipo inválido: '<texto>' (use UHE, PCH, CGH, UTE, UTN, EOL, UFV)`).

## Entradas

Só resultados já gravados (constituição, princípio I). Nenhuma etapa é executada, nenhum `etapa.json` é gravado, e o portal não é consultado.
- **Catálogo** (`data/catalogo/`): o recorte (as usinas do estado e do tipo), a cobertura de cada usina e o panorama dos agregados.
- **De cada usina do recorte**: o perfil, achado pelo CEG em `usinas/*/perfil.toml`, e o `etapa.json` e o `resultados.pkl` das Análises em `data/usinas/<slug>/analises/`, com os indicadores da carteira.

Entra com resultado a usina com perfil conferido e válido e Análises `concluida` no formato atual, com os indicadores da carteira. As demais vão para a lista "sem resultado", com o primeiro destes motivos:
1. só agregado no ONS (ver o panorama);
2. sem perfil;
3. perfil em rascunho;
4. perfil inválido, inclusive dois perfis com o mesmo CEG;
5. Análises ausentes, em formato antigo (inclusive sem os indicadores da carteira), com falha ou desatualizadas.

As linhas de conjunto do catálogo não contam como usina. Um perfil ilegível fica de fora, com o aviso `Perfil ilegível, fora da carteira: <arquivo>`.

## Saída

`reports/carteiras/<nome>/`, com `<nome>` = `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`, em minúsculas:
- `relatorio_carteira.pdf` (A4 retrato) e `relatorio_carteira.md`, com o mesmo conteúdo e na mesma ordem;
- `carteira.xlsx`, com as abas `USINAS`, `INDICADORES`, `ORDENACAO`, `SEM_RESULTADO`, `PANORAMA` e `FONTES`;
- `figures/01_itens_da_conclusao_por_usina.png` e, com o panorama, `figures/02_panorama_agregados_mensal.png`, em seaborn.

A gravação usa o mecanismo do relatório da usina: pasta temporária, conferência e troca, sem `.bak` (constituição, Requisito Técnico 3). A figura de uma execução anterior que não tem mais base é apagada.

**Conteúdo**, nesta ordem:
1. capa: título "Relatório de carteira — `<recorte>`", recorte, data do catálogo, linhas de conjunto que não contam, quantidade de usinas com e sem resultado e data de geração;
2. usinas com resultado: tipo, modalidade, potência, cobertura, nível da geração e período;
3. indicadores comparáveis: só os que se aplicam a algum tipo do recorte, cada um do nível da usina, salvo os identificados, com "—" onde não se aplica;
4. ordenação pela quantidade de todos os itens de "possíveis problemas", depois de "pontos de atenção" e pelo nome, com as usinas sem regra avaliada no fim, e a figura 1;
5. usinas sem resultado, com o motivo, a cobertura e a quantidade por motivo;
6. com `--estado`, o panorama dos agregados (pequenas usinas e MMGD) do estado, por modalidade, tipo e mês, identificado como agregado, com as horas sem valor e ausentes e com os valores de usinas Tipo III identificados como previsão do ONS, e a figura 2. Com `--estado` e `--tipo`, só o tipo do ONS correspondente. Na carteira só por tipo, o panorama é omitido, com o motivo nas notas: os agregados são publicados por área do estado;
7. notas: fontes, definições dos indicadores, níveis dos dados e a frase de que a carteira não atribui nota nem parecer.

Cada tabela e cada figura tem, logo abaixo, a legenda de fonte ("Fonte dos dados: …" ou "Calculado neste relatório a partir de: …"), a mesma origem da aba `FONTES`. Nenhum texto usa "satisfatório", "insatisfatório", "cumpre", "descumpre" ou equivalente de parecer.

## Códigos de saída

| Código | Situação |
|---|---|
| 0 | carteira gerada |
| 1 | erro de gravação ou inesperado, ou interrupção pelo usuário; as saídas anteriores ficam como estavam |
| 2 | opção inválida, inclusive sem `--estado` nem `--tipo` |
| 5 | catálogo ausente, ou nenhuma usina do recorte com resultado (nada é gravado) |

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Fim | log, `INFO` | `Carteira <nome>: <N> usinas com resultado e <S> sem resultado. Pasta: reports/carteiras/<nome>/` |
| Catálogo ausente (5) | log, `ERROR` | `O catálogo de usinas não foi montado. Execute antes: python -m src usinas` |
| Sem nenhuma usina com resultado (5) | log, `ERROR` | `Nenhuma usina do recorte <recorte> tem as Análises concluídas. Execute antes: python -m src completo --usina <slug>` (o slug da primeira usina sem resultado pelas Análises, ou `<slug>`) |
| Interrupção (1) | log, `ERROR` | `Carteira <nome> interrompida pelo usuário.` |
| Erro inesperado (1) | log, `ERROR` | `Carteira <nome>: erro inesperado: <motivo>` |

## Exemplos

```powershell
# Carteira de MS, com data de geração fixa
python -m src carteira --estado MS --data-geracao "22/10/2026 14:00"

# Só as solares de MS
python -m src carteira --estado MS --tipo UFV

# Todas as térmicas com perfil, no Brasil
python -m src carteira --tipo UTE
```
