# Contract: Linha de comando — relatório de carteira (`carteira`)

**Spec**: [spec.md](../spec.md) (FR-026, FR-027, SC-006, SC-007) · **Data model**: [seções 2.6 e 7](../data-model.md) · **Research**: R21

## Sintaxe

```text
python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao "DD/MM/AAAA HH:MM"] [--log-level <nível>]
```

| Opção | Efeito |
|---|---|
| `--estado <UF>` | sigla do estado (2 letras) |
| `--tipo <tipo>` | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL` ou `UFV` |
| `--data-geracao` | fixa a data de geração e torna o PDF reproduzível byte a byte, como no relatório da usina |

É preciso pelo menos uma das opções `--estado` e `--tipo`: a carteira é de um estado, de um tipo ou de um tipo num estado (constituição, princípio III). Sem nenhuma das duas, código 2.

## Entradas

Só resultados já gravados (princípio I). Nenhuma etapa é executada e o portal não é consultado.
- **Catálogo** (`data/catalogo/`): o recorte (as usinas do estado e do tipo) e o panorama dos agregados.
- **De cada usina do recorte**: o perfil, achado pelo CEG em `usinas/*/perfil.toml`, e o `etapa.json` e o `resultados.pkl` das Análises em `data/usinas/<slug>/analises/`.

Entra com resultado a usina com perfil conferido e Análises `concluida` no formato atual. As demais vão para a lista "sem resultado", com um destes motivos:
- sem perfil;
- perfil em rascunho;
- perfil inválido;
- Análises ausentes, com falha, desatualizadas ou em formato antigo;
- só agregado no ONS (ver o panorama).

As linhas de conjunto do catálogo não contam como usina.

## Saída

`reports/carteiras/<nome>/`, com `<nome>` = `<uf>`, `<uf>_<tipo>` ou `brasil_<tipo>`, em minúsculas:
- `relatorio_carteira.pdf` e `relatorio_carteira.md`, com o mesmo conteúdo e na mesma ordem;
- `carteira.xlsx`, com as abas `USINAS`, `INDICADORES`, `ORDENACAO`, `SEM_RESULTADO`, `PANORAMA` e `FONTES`;
- `figures/`, em seaborn.

A gravação usa o mecanismo do relatório da usina: pasta temporária, conferência e troca. Sem `.bak` (RT3).

**Conteúdo**, nesta ordem (FR-027):
1. capa: recorte, data do catálogo, quantidade de usinas com e sem resultado;
2. quadro das usinas: tipo, modalidade, potência, cobertura e período;
3. indicadores comparáveis por tipo, só os aplicáveis, cada um com o nível;
4. ordenação pela quantidade de todos os itens de "possíveis problemas", depois de "pontos de atenção";
5. usinas sem resultado, com o motivo;
6. com `--estado`, o panorama dos agregados (pequenas usinas e MMGD) do estado, por tipo e por mês, identificado como agregado, com as horas ausentes e com os valores de usinas Tipo III identificados como previsão do ONS. Na carteira só por tipo, o panorama é omitido, com o motivo nas notas: os agregados são publicados por área do estado;
7. notas: fontes, níveis dos dados e a frase de que a carteira não atribui nota nem parecer.

Nenhum texto usa "satisfatório", "insatisfatório", "cumpre", "descumpre" ou equivalente de parecer (SC-007).

## Códigos de saída

| Código | Situação |
|---|---|
| 0 | carteira gerada |
| 1 | erro de gravação ou inesperado |
| 2 | opção inválida, inclusive sem `--estado` nem `--tipo` |
| 5 | catálogo ausente, ou nenhuma usina do recorte com resultado (nada é gravado) |

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Fim | log, `INFO` | `Carteira <nome>: <N> usinas com resultado e <S> sem resultado. Pasta: reports/carteiras/<nome>/` |
| Catálogo ausente (5) | log, `ERROR` | `O catálogo de usinas não foi montado. Execute antes: python -m src usinas` |
| Sem nenhuma usina com resultado (5) | log, `ERROR` | `Nenhuma usina do recorte <recorte> tem as Análises concluídas. Execute antes: python -m src completo --usina <slug>` |

## Exemplos

```powershell
# Carteira de MS, com data de geração fixa
python -m src carteira --estado MS --data-geracao "30/10/2026 09:00"

# Só as solares de MS
python -m src carteira --estado MS --tipo UFV

# Todas as térmicas com perfil, no Brasil
python -m src carteira --tipo UTE
```
