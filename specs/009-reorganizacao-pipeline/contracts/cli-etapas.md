# Contract: Linha de Comando Única

**Feature**: `009-reorganizacao-pipeline` | **Date**: 2026-10-07 | Decisões: [research.md](../research.md) (R2 e R9)

## Sintaxe

```text
python -m src <comando> --usina <slug> [opções]
```

`--usina` é obrigatório nos comandos de etapa e no `comparar`. O slug é o nome da pasta em `usinas/`, por exemplo `sao_domingos`.

## Comandos de etapa

| Comando | Faz | Opções próprias |
|---|---|---|
| `coleta` | varre o portal do ONS e baixa só o que é novo ou mudou; guarda versões e dicionários; extrai a usina dos dez conjuntos e audita | `--sem-portal`: não consulta o portal e extrai só dos arquivos locais. `--forcar-download`: baixa tudo de novo |
| `tratamento` | padroniza, valida (R1 a R9), alinha horários, lista ausências e grava os dados tratados | n/a |
| `conferencia` | executa as seis conferências entre fontes e grava os resultados | n/a |
| `analises` | calcula indicadores, eventos, perfis, constatações e os dados das figuras | n/a |
| `relatorio` | gera as figuras, o PDF, o Markdown e a planilha | `--data-geracao "DD/MM/AAAA HH:MM"`: fixa a data de geração e torna o PDF reproduzível byte a byte |
| `completo` | executa as cinco etapas na ordem e para na primeira que não terminar com 0 | aceita as opções de `coleta` e de `relatorio` |

## Ferramentas

| Comando | Faz |
|---|---|
| `copia-seguranca --motivo <texto>` | cria `_backup_<data>_<motivo>/`, confere a cópia e só então mantém as duas mais recentes. Não usa `--usina` |
| `comparar --usina <slug> --referencia <pasta>` | compara o relatório atual da usina com o de outra pasta: PDF, Markdown, CSV e figuras byte a byte; planilha célula a célula. Lista as diferenças |

## Opção comum

- `--log-level {DEBUG,INFO,WARNING,ERROR}`: o padrão é `INFO`. Vale para todos os módulos executados na chamada.

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | sucesso (no `comparar`, nenhuma diferença) |
| 1 | erro, inclusive falha de gravação, com o arquivo restaurado |
| 2 | arquivo de dados não obtido ou não lido (coleta) |
| 3 | alinhamento da hidrologia abaixo da meta (conferência) |
| 4 | perfil da usina inválido; a mensagem lista os campos |
| 5 | etapa anterior sem resultados concluídos, ou com resultados desatualizados; nada é gravado |
| 6 | `comparar` encontrou diferenças |

## Mensagens obrigatórias

- **Etapa anterior ausente**: `A etapa '<etapa>' precisa da etapa '<anterior>' concluída para a usina '<slug>'. Execute antes: python -m src <anterior> --usina <slug>`.
- **Perfil inválido**: `Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):`, seguido de uma linha por problema.
- **Ao final de cada etapa**: o resumo da etapa (seção `resumo` do `etapa.json`) e o caminho da pasta de saída.

## Comandos e opções que deixam de existir

| Antes | Agora |
|---|---|
| `python -m src.main --full-pipeline` | `python -m src completo --usina <slug>` |
| `python -m src.main --complementares-only`, `--indicadores-only`, `--programacao-only`, `--disponibilidade-only`, `--hidrologia-only`, `--geracao-only`, `--cadastro-only`, `--dicionarios-only` | `python -m src coleta --usina <slug>`; sem novidade no portal, nada é baixado |
| `--sem-indicadores`, `--sem-programacao`, `--sem-disponibilidade`, `--sem-hidrologia`, `--sem-geracao`, `--sem-cadastro`, `--sem-dicionarios` | não há substituto: os dez conjuntos fazem parte da coleta |
| `--filter-only` | `python -m src coleta --usina <slug> --sem-portal` |
| `--download-only` | não há substituto: a coleta sempre extrai |
| `--cod-usina`, `--nome-reservatorio` | perfil da usina |
| `python -m src.processor` | `python -m src tratamento --usina <slug>` |
| `python -m src.analyzer` | `python -m src conferencia`, depois `analises` e `relatorio`, todos com `--usina <slug>` |
| `--no-validate-physics`, `--no-generate-plots` | não há substituto: a validação faz parte do tratamento, e as figuras, do relatório |
| `python -m src.indicadores_ons`, `src.programacao_ons`, `src.cadastro_ons`, `src.dicionarios_ons`, `src.disponibilidade_ons`, `src.hidrologia_ons`, `src.geracao_ons`, `src.pdf_generator` | o comando de etapa correspondente |

## Exemplos

```powershell
# Fluxo completo da São Domingos, com consulta ao portal
python -m src completo --usina sao_domingos

# Sem internet: só os arquivos já baixados, com data de geração fixa (conferência de reprodutibilidade)
python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"

# Só refazer o relatório depois de um ajuste de leiaute
python -m src relatorio --usina sao_domingos

# Cópia de segurança antes de mudar o código
python -m src copia-seguranca --motivo antes_ajuste_x
```
