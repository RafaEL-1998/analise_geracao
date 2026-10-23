# Contract: Linha de comando — Coleta de dados

**Spec**: [spec.md](../spec.md)

Este contrato traz o comando da Coleta e as regras comuns às cinco etapas: comandos, `--log-level`, códigos de saída, mensagens obrigatórias, `completo` e `copia-seguranca`. Os contratos das demais etapas remetem a ele. Os comandos `usinas` e `perfil`, também da Coleta, têm contratos próprios: [cli-usinas.md](cli-usinas.md) e [cli-perfil.md](cli-perfil.md).

## Sintaxe

```text
python -m src <comando> [--usina <slug>] [opções]
```

- Executar na raiz do projeto, com o `venv` ativo; o comando roda sem interação com o usuário.
- As opções vêm depois do comando.
- `--usina` é obrigatório nos comandos de etapa, no `completo`, no `referencia` e no `comparar` com `--referencia`. O slug é o nome da pasta em `usinas/`.

| Comando | Faz | Opções próprias |
|---|---|---|
| `coleta` | Coleta de dados (esta spec) | `--sem-portal`, `--forcar-download` |
| `tratamento` | [Tratamento de dados](../../002-tratamento-dados/spec.md) | nenhuma |
| `conferencia` | [Conferência](../../003-conferencia/spec.md) | nenhuma |
| `analises` | [Análises](../../004-analises/spec.md) | nenhuma |
| `relatorio` | [Geração do relatório](../../005-geracao-relatorio/spec.md) | `--data-geracao "DD/MM/AAAA HH:MM"` |
| `completo` | as cinco etapas, na ordem | `--sem-portal`, `--forcar-download`, `--data-geracao` |
| `usinas` | catálogo de usinas ([cli-usinas.md](cli-usinas.md)); não usa `--usina` | `--estado`, `--tipo`, `--modalidade`, `--sem-portal`, `--forcar-download` |
| `perfil --ceg <CEG>` | rascunho do perfil, só a partir do catálogo ([cli-perfil.md](cli-perfil.md)); não usa `--usina` | `--slug` |
| `carteira` | relatório de carteira de um estado, de um tipo ou dos dois, só com os resultados gravados ([Geração do relatório](../../005-geracao-relatorio/spec.md)); não usa `--usina` | `--estado <UF>`, `--tipo <tipo>` (pelo menos uma das duas), `--data-geracao` |
| `referencia --usina <slug>` | registra o relatório aprovado da usina em `relatorios_referencia/<slug>/`, com a Coleta e o perfil congelados ([Geração do relatório](../../005-geracao-relatorio/spec.md)) | `--data-geracao "DD/MM/AAAA HH:MM"` e `--aprovado-em "DD/MM/AAAA"`, obrigatórias |
| `copia-seguranca --motivo <texto>` | cópia de segurança do projeto; não usa `--usina` | nenhuma |
| `comparar --usina <slug> --referencia <pasta>` | compara o relatório da usina com o de outra pasta ([Geração do relatório](../../005-geracao-relatorio/spec.md)) | nenhuma |
| `comparar --todas [--coleta]` | refaz, num espaço isolado, cada relatório de `relatorios_referencia/` e o compara; com `--coleta`, refaz também a Coleta ([Geração do relatório](../../005-geracao-relatorio/spec.md)); não usa `--usina` | `--coleta` |

Não há outro ponto de entrada, nem opção para executar ou pular um conjunto do ONS ou parte de uma etapa. Combinações inválidas são recusadas pelo argparse com o código 2: `carteira` sem `--estado` nem `--tipo`; `comparar --todas` com `--usina` ou `--referencia`; `comparar` sem `--todas` e sem o par `--usina`/`--referencia`; `--coleta` sem `--todas`.

## Comando `coleta`

```text
python -m src coleta --usina <slug> [--sem-portal] [--forcar-download] [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

| Opção | Efeito |
|---|---|
| `--usina <slug>` | obrigatória; perfil em `usinas/<slug>/perfil.toml`, lido e validado antes de qualquer outra ação |
| `--sem-portal` | não consulta o portal; extrai só dos arquivos locais, com as mesmas regras de período e formato; não cria, altera nem exclui nada em `data/raw/`; os dicionários não são obtidos, e `dicionarios.csv` é montado dos manifestos locais; no resumo, `baixados` e `reaproveitados` ficam 0 |
| `--forcar-download` | baixa de novo todos os arquivos de dados dos conjuntos da usina, sem reaproveitar cópias locais; só o conteúdo diferente gera versão anterior. Sem efeito com `--sem-portal` (o resumo registra `forcar_download: false`) |
| `--log-level` | nível do log (seção seguinte) |

A coleta obtém os conjuntos do tipo e da `[cobertura]` da usina, pelo registro dos conjuntos (na UHE sem `[cobertura]`, os dez conjuntos da UHE). Grava em `data/raw/` (só quando consulta o portal) e em `data/usinas/<slug>/coleta/`; os arquivos estão no [data-model](../data-model.md), seção 2.

## Opção comum `--log-level`

- Valores: `DEBUG`, `INFO` (padrão), `WARNING`, `ERROR`; outro valor é recusado pelo argparse (código 2).
- O log sai só na saída padrão, sem arquivo, no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] <logger> - <mensagem>`. Os loggers são `pipeline`, `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio` e `persistencia`; o catálogo de usinas e o rascunho do perfil usam o `coleta`.
- O nível é aplicado a todos esses loggers no início do comando (`configurar_nivel_log`) e vale também para os módulos carregados depois, como o da etapa executada: com `WARNING`, nenhuma mensagem informativa aparece; com `DEBUG`, as de depuração podem aparecer em qualquer módulo.

## Códigos de saída

Tabela comum a todos os comandos. A Coleta termina com 0, 1, 2 ou 4.

| Código | Significado | Comandos |
|---|---|---|
| 0 | sucesso; no `comparar`, nenhuma diferença; no `perfil`, rascunho gravado ou perfil existente igual ao catálogo | todos |
| 1 | erro: catálogo do ONS inacessível, dado que impede a etapa (na Coleta, usina sem série de referência na `[cobertura]`), falha de gravação (com o arquivo restaurado), interrupção pelo usuário (Ctrl+C) ou erro inesperado; na `copia-seguranca`, motivo inválido, cópia já existente ou falha na criação ou na conferência; no `comparar`, pasta inexistente ou erro na leitura; no `comparar --todas`, também sem referências ou com a Coleta congelada ausente; no `referencia`, relatório gerado com outra data, referência atual não commitada ou falha na gravação ou na conferência; no `perfil`, perfil existente ilegível | todos |
| 2 | Coleta: arquivo de dados não obtido ou não lido, usina sem linha na EVT, série de referência sem hora com valor, usina fora da composição do conjunto declarado no perfil, cadastral não obtido ou usina sem ficha no cadastro. `usinas`: Modalidade das usinas, Composição dos conjuntos, Capacidade de geração ou Reservatórios não obtido. `perfil`: slug inválido, CEG fora do catálogo, tipo fora dos sete, usina Tipo III ou só com agregado. Qualquer comando: opção inválida ou ausente, recusada pelo argparse antes de qualquer execução | `coleta`, `completo`, `usinas`, `perfil`; todos |
| 3 | conferência das vazões com a hidrologia abaixo da meta | `conferencia`, `completo` |
| 4 | perfil da usina ausente, inválido ou em rascunho | todos com `--usina` |
| 5 | etapa anterior sem resultado concluído: ausente, ilegível, com falha, desatualizada ou em formato antigo; nada é gravado. No `perfil`, catálogo de usinas ausente ou em formato antigo. Na `carteira`, catálogo ausente ou nenhuma usina do recorte com as Análises concluídas. No `referencia`, relatório ou Coleta da usina ausente ou não concluída | `tratamento`, `conferencia`, `analises`, `relatorio`, `perfil`, `carteira`, `referencia` |
| 6 | o `comparar` encontrou diferenças; o `perfil` encontrou um perfil existente com diferenças em relação ao catálogo (nada é gravado) | `comparar`, `perfil` |

Situação gravada no `etapa.json` da etapa (detalhes no [data-model](../data-model.md), seção 4); os comandos sem etapa (`usinas`, `perfil`, `carteira`, `referencia`, `comparar`, `copia-seguranca`) não gravam `etapa.json`:

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
| Coleta: usina sem série de referência na `[cobertura]` (código 1) | log, `ERROR` | `Coleta recusada: a usina '<slug>' não tem série de referência: nem a Energia Vertida Turbinável nem a Geração por usina (da usina ou do conjunto) na [cobertura].` |
| Coleta: usina fora da composição do conjunto declarado (código 2) | log, `ERROR` | `A usina (CEG <CEG>) não está na Composição dos conjuntos do conjunto <id do conjunto> declarado no perfil; a série do conjunto não tem hora da usina e os demais conjuntos não são coletados.` |
| Coleta: série de referência sem hora com valor (código 2) | log, `ERROR` | `A série de referência da usina '<slug>' (<motivo>) não tem nenhuma hora com valor; os demais conjuntos não são coletados.` |

Na Coleta, o log também traz as linhas lidas e extraídas (por arquivo na EVT, por conjunto nos demais); a série de referência escolhida e o período; os avisos de linhas que conferem só em parte, de linhas irregulares (arquivo, quantidade e as cinco primeiras), de colunas de valor ausentes num arquivo, de valores numéricos ilegíveis na EVT, de duplicatas conflitantes na EVT, de recursos repetidos no catálogo, de tamanho baixado diferente do publicado, de unidades das usinas do conjunto com o CEG e outro subsistema e de dicionários alterados; as versões preservadas e excluídas; e, na parada, o conjunto e os arquivos com falha.

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
- Copia `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `usinas/*/perfil.toml`, `README.md`, `requirements.txt` e `relatorios_referencia/` inteira (sem as pastas temporárias do `referencia`), e acrescenta `copia.json` (nome, tamanho e SHA-256 de cada arquivo), `conftest.py` (impede o pytest de varrer a cópia) e `LEIA-ME.txt` (data, motivo, conteúdo e as referências levadas). Dados (brutos, catálogo e etapas), documentos de referência e `venv/` ficam fora.
- Confere a cópia (quantidade de arquivos, SHA-256 de cada um e, em cada referência, os SHA-256 do `referencia.json`) e só então exclui as cópias mais antigas até ficarem duas.
- Em falha na criação ou na conferência, apaga a cópia incompleta, não exclui nenhuma outra e termina com 1.

## Exemplos

```powershell
# Coleta com consulta ao portal: baixa só o que é novo ou mudou; depois, o código de saída
python -m src coleta --usina sao_domingos
$LASTEXITCODE

# Sem internet: extrai só dos arquivos já baixados, sem mexer em data\raw
python -m src coleta --usina sao_domingos --sem-portal

# Usina nova: catálogo do estado, rascunho do perfil e, depois de conferido, o fluxo completo
python -m src usinas --estado MS
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona
python -m src completo --usina william_arjona

# Cópia de segurança antes de mudar o código; depois, o fluxo completo sem portal, com data de geração fixa
python -m src copia-seguranca --motivo antes_ajuste_x
python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"
```
