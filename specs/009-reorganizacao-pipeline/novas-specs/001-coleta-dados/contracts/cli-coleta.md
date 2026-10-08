# Contract: Linha de comando — Coleta de dados

**Spec**: [spec.md](../spec.md)

Este contrato traz o comando da Coleta e as regras comuns às cinco etapas: comandos, `--log-level`, códigos de saída, mensagens obrigatórias, `completo` e `copia-seguranca`. Os contratos das demais etapas remetem a ele.

## Sintaxe

```text
python -m src <comando> --usina <slug> [opções]
```

- Executar na raiz do projeto, com o `venv` ativo; o comando roda sem interação com o usuário.
- As opções vêm depois do comando.
- `--usina` é obrigatório em todos os comandos, exceto `copia-seguranca`. O slug é o nome da pasta em `usinas/`.

| Comando | Faz | Opções próprias |
|---|---|---|
| `coleta` | Coleta de dados (esta spec) | `--sem-portal`, `--forcar-download` |
| `tratamento` | [Tratamento de dados](../../002-tratamento-dados/spec.md) | nenhuma |
| `conferencia` | [Conferência](../../003-conferencia/spec.md) | nenhuma |
| `analises` | [Análises](../../004-analises/spec.md) | nenhuma |
| `relatorio` | [Geração do relatório](../../005-geracao-relatorio/spec.md) | `--data-geracao "DD/MM/AAAA HH:MM"` |
| `completo` | as cinco etapas, na ordem | `--sem-portal`, `--forcar-download`, `--data-geracao` |
| `copia-seguranca --motivo <texto>` | cópia de segurança do projeto; não usa `--usina` | nenhuma |
| `comparar --usina <slug> --referencia <pasta>` | compara o relatório da usina com o de outra pasta ([Geração do relatório](../../005-geracao-relatorio/spec.md)) | nenhuma |

Não há outro ponto de entrada, nem opção para executar ou pular um conjunto do ONS ou parte de uma etapa.

## Comando `coleta`

```text
python -m src coleta --usina <slug> [--sem-portal] [--forcar-download] [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

| Opção | Efeito |
|---|---|
| `--usina <slug>` | obrigatória; perfil em `usinas/<slug>/perfil.toml`, lido e validado antes de qualquer outra ação |
| `--sem-portal` | não consulta o portal; extrai só dos arquivos locais, com as mesmas regras de período e formato; não cria, altera nem exclui nada em `data/raw/`; os dicionários não são obtidos, e `dicionarios.csv` é montado dos manifestos locais; no resumo, `baixados` e `reaproveitados` ficam 0 |
| `--forcar-download` | baixa de novo todos os arquivos de dados dos dez conjuntos, sem reaproveitar cópias locais; só o conteúdo diferente gera versão anterior. Sem efeito com `--sem-portal` (o resumo registra `forcar_download: false`) |
| `--log-level` | nível do log (seção seguinte) |

A coleta grava em `data/raw/` (só quando consulta o portal) e em `data/usinas/<slug>/coleta/`; os arquivos estão no [data-model](../data-model.md), seção 2.

## Opção comum `--log-level`

- Valores: `DEBUG`, `INFO` (padrão), `WARNING`, `ERROR`; outro valor é recusado pelo argparse (código 2).
- O log sai só na saída padrão, sem arquivo, no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] <logger> - <mensagem>`. Os loggers são `pipeline`, `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio` e `persistencia`.
- O nível é aplicado a todos esses loggers no início do comando (`configurar_nivel_log`) e vale também para os módulos carregados depois, como o da etapa executada: com `WARNING`, nenhuma mensagem informativa aparece; com `DEBUG`, as de depuração podem aparecer em qualquer módulo.

## Códigos de saída

Tabela comum a todos os comandos. A Coleta termina com 0, 1, 2 ou 4.

| Código | Significado | Comandos |
|---|---|---|
| 0 | sucesso; no `comparar`, nenhuma diferença | todos |
| 1 | erro: catálogo do ONS inacessível, dado que impede a etapa, falha de gravação (com o arquivo restaurado), interrupção pelo usuário (Ctrl+C) ou erro inesperado; na `copia-seguranca`, motivo inválido, cópia já existente ou falha na criação ou na conferência; no `comparar`, pasta inexistente ou erro na leitura | todos |
| 2 | Coleta: arquivo de dados não obtido ou não lido, usina sem linha na EVT ou sem ficha no cadastro. Qualquer comando: opção inválida ou ausente, recusada pelo argparse antes de qualquer execução | `coleta`, `completo`; todos |
| 3 | conferência das vazões com a hidrologia abaixo da meta | `conferencia`, `completo` |
| 4 | perfil da usina ausente ou inválido | todos com `--usina` |
| 5 | etapa anterior sem resultado concluído: ausente, ilegível, com falha, desatualizada ou em formato antigo; nada é gravado | `tratamento`, `conferencia`, `analises`, `relatorio` |
| 6 | o `comparar` encontrou diferenças | `comparar` |

Situação gravada no `etapa.json` da etapa (detalhes no [data-model](../data-model.md), seção 4):

| Código | `status` | Etapas seguintes |
|---|---|---|
| 0 | `concluida` | as que já existem ficam `desatualizada` |
| 3 | `concluida`, com `codigo_saida` 3 | idem; o `completo` para, mas a etapa seguinte, executada à parte, aceita a anterior |
| 1 ou 2, inclusive a interrupção pelo usuário | `falha`, com o código | não mudam; a seguinte recusa rodar (código 5) |
| 4, 5 ou opção inválida | nada é gravado | não mudam |

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Perfil inválido (código 4) | saída de erro | `Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):`, seguido de uma linha `- <problema>` por problema ([contracts/perfil-usina.md](perfil-usina.md)) |
| Etapa anterior sem resultado concluído (código 5) | log, `ERROR` | `A etapa '<etapa>' precisa da etapa '<anterior>' concluída para a usina '<slug>'. Execute antes: python -m src <anterior> --usina <slug>` |
| Fim de cada etapa | log, `INFO` | `Etapa '<etapa>' da usina '<slug>': <status> (código <N>). Resumo: <resumo do etapa.json em JSON>. Pasta: <pasta da etapa>` |
| Etapas seguintes invalidadas | log, `INFO` | `Etapas seguintes marcadas como desatualizadas: <etapas>.` |
| Interrupção pelo usuário (código 1) | log, `ERROR` | `Etapa '<etapa>' da usina '<slug>' interrompida pelo usuário.` |
| `completo` interrompido | log, `WARNING` | `Fluxo completo interrompido na etapa '<etapa>' (código <N>).` |
| Opção inválida (código 2) | saída de erro | uso e erro do argparse |
| Erro no `comparar` (código 1) | saída de erro | `Erro na comparação: <erro>` |

Na Coleta, o log também traz as linhas lidas e extraídas (por arquivo na EVT, por conjunto nos demais); os avisos de linhas que conferem só em parte, de linhas irregulares (arquivo, quantidade e as cinco primeiras), de valores numéricos ilegíveis na EVT, de duplicatas conflitantes na EVT, de tamanho baixado diferente do publicado e de dicionários alterados; as versões preservadas e excluídas; e, na parada, o conjunto e os arquivos com falha.

## Comando `completo`

```text
python -m src completo --usina <slug> [--sem-portal] [--forcar-download] [--data-geracao "DD/MM/AAAA HH:MM"] [--log-level <nível>]
```

- Lê o perfil uma vez e executa `coleta`, `tratamento`, `conferencia`, `analises` e `relatorio`, nesta ordem; `--sem-portal` e `--forcar-download` vão para a coleta, e `--data-geracao`, para o relatório.
- Para na primeira etapa que não termina com 0 e sai com o código dela (inclusive 3). Cada etapa executada grava o seu `etapa.json`.

## Ferramenta `copia-seguranca`

```text
python -m src copia-seguranca --motivo <texto> [--log-level <nível>]
```

- Não lê perfil. O motivo aceita letras, algarismos, `_` e `-`; outro texto termina com 1.
- Cria `_backup_<AAAA-MM-DD>_<motivo>/` na raiz do projeto; se a pasta já existe, termina com 1.
- Copia `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `usinas/*/perfil.toml`, `README.md` e `requirements.txt`, e acrescenta `copia.json` (nome, tamanho e SHA-256 de cada arquivo), `conftest.py` (impede o pytest de varrer a cópia) e `LEIA-ME.txt` (data, motivo e conteúdo). Dados, documentos de referência e `venv/` ficam fora.
- Confere a cópia (quantidade de arquivos e SHA-256 de cada um) e só então exclui as cópias mais antigas até ficarem duas.
- Em falha na criação ou na conferência, apaga a cópia incompleta, não exclui nenhuma outra e termina com 1.

## Exemplos

```powershell
# Coleta com consulta ao portal: baixa só o que é novo ou mudou; depois, o código de saída
python -m src coleta --usina sao_domingos
$LASTEXITCODE

# Sem internet: extrai só dos arquivos já baixados, sem mexer em data\raw
python -m src coleta --usina sao_domingos --sem-portal

# Cópia de segurança antes de mudar o código; depois, o fluxo completo sem portal, com data de geração fixa
python -m src copia-seguranca --motivo antes_ajuste_x
python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"
```
