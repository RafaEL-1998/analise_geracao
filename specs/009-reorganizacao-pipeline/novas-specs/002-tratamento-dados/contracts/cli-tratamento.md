# Contract: Linha de comando — Tratamento de dados

**Spec**: [spec.md](../spec.md)

As regras comuns às cinco etapas (sintaxe geral, perfil da usina, `etapa.json`, pré-requisitos, comando `completo`, tabela completa dos códigos de saída e mensagens comuns) estão no [contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md).

## Sintaxe

```text
python -m src <comando> --usina <slug> [opções]
python -m src tratamento --usina <slug> [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

| Opção | Obrigatória | Efeito |
|---|---|---|
| `--usina <slug>` | sim | usina do perfil `usinas/<slug>/perfil.toml`; entrada em `data/usinas/<slug>/coleta/` e saída em `data/usinas/<slug>/tratamento/` |
| `--log-level` | não | nível do log: `DEBUG`, `INFO` (padrão), `WARNING` ou `ERROR`, aplicado por `configurar_nivel_log` a todos os loggers do fluxo (`pipeline`, `tratamento`, `persistencia`, `coleta` e os das demais etapas) |

- O comando não tem opções próprias (FR-001): a validação R1 a R9, o relatório de validação e os três formatos da base de EVT sempre fazem parte da etapa. Qualquer outra opção, como `--no-validate-physics`, é recusada pelo `argparse` com código 2, antes de qualquer execução.
- No `completo`, o Tratamento roda depois da Coleta, também sem opções.
- Os módulos da etapa só são importados quando ela começa; `setup_logger` mantém neles o nível já aplicado pela linha de comando.

## O que o comando faz

1. Carrega e valida o perfil (inválido: código 4).
2. Confere o `etapa.json` da Coleta: precisa estar `concluida` e no `versao_formato` atual. Senão, sai com 5 sem gravar nada.
3. Executa `src.tratamento.etapa.executar_tratamento` (passos no [plano](../plan.md#fluxo-de-execução)) e grava em `data/usinas/<slug>/tratamento/` os 21 arquivos descritos no [data-model](../data-model.md#2-saídas), cada um com `.bak` da versão anterior quando o conteúdo muda.
4. Grava o `etapa.json` da etapa (`concluida` com 0; `falha` com 1). Com 0, as etapas seguintes que já existirem ficam `desatualizada`, mesmo que todos os arquivos tenham ficado `INALTERADO`.

## Códigos de saída

| Código | Quando |
|---|---|
| 0 | tratamento concluído, inclusive com violações de R2 a R9, horas sinalizadas, ausências e avisos no log |
| 1 | violação de R1, EVT extraída ausente, coluna obrigatória ausente, dicionário da EVT ausente ou instante inválido: nada é gravado; extraído ou auditoria da Coleta ilegível: ficam os arquivos gravados antes do erro; falha de gravação ou interrupção pelo usuário (Ctrl+C): o arquivo em gravação volta à versão anterior, sem temporários; qualquer outro erro. O `etapa.json` fica `falha` (na interrupção, com `resumo` `{"erro": "interrompida pelo usuário"}`), e a Conferência recusa rodar (5) até um novo Tratamento concluído |
| 5 | `etapa.json` da Coleta ausente, ilegível, com `status` diferente de `concluida` ou com outro `versao_formato`; nada é gravado, nem o `etapa.json` |

Antes de a etapa começar, a linha de comando comum ainda pode sair com 2 (opção inválida ou `--usina` ausente) ou 4 (perfil inválido, com a lista dos problemas).

## Mensagens no log

Formato: `AAAA-MM-DD HH:MM:SS [NÍVEL] <logger> - <mensagem>`, só na saída padrão.

| Situação | Logger | Mensagem |
|---|---|---|
| Coleta não concluída | `pipeline` (ERROR) | `A etapa 'tratamento' precisa da etapa 'coleta' concluída para a usina '<slug>'. Execute antes: python -m src coleta --usina <slug>` |
| Violação de R1 | `tratamento` (ERROR) | `Violação da R1 (valores negativos na EVT) em <n> registros: a base não é tratada.` |
| Resultado de cada gravação | `persistencia` (INFO) | `NOVO: <arquivo> (<descrição>)`, `ALTERADO: <arquivo> (<descrição>); versão anterior em <arquivo>.bak` ou `INALTERADO: <arquivo> (<descrição>)` |
| Falha de gravação | `persistencia` (ERROR) | `Falha ao gravar <caminho>: <motivo>. O arquivo foi mantido na versão anterior (verifique se ele está aberto em outro programa).` |
| Interrupção (Ctrl+C) durante uma gravação | `persistencia` (ERROR) | `Gravação de <caminho> interrompida; o arquivo foi mantido na versão anterior.` |
| Interrupção (Ctrl+C) da etapa | `pipeline` (ERROR) | `Etapa 'tratamento' da usina '<slug>' interrompida pelo usuário.` |
| Fim da etapa | `pipeline` (INFO) | `Etapa 'tratamento' da usina '<slug>': <status> (código <n>). Resumo: <resumo em JSON>. Pasta: <pasta>` |

Os avisos (`WARNING`, logger `tratamento`) dizem: colunas de rastreabilidade ausentes na EVT, grandezas fora do dicionário, `cod_usina` inválidos, valores ausentes por grandeza e no total, quantidade de linhas com chave repetida nos indicadores, meses-unidade com resíduo acima de 0,1 h, horas repetidas com valores diferentes por conjunto, horas sinalizadas por código na disponibilidade e na hidrologia, e meses sem a usina na disponibilidade.

## Exemplos

```powershell
# Tratar a São Domingos depois da Coleta concluída
python -m src tratamento --usina sao_domingos

# Fluxo completo sem consultar o portal: o Tratamento roda logo depois da Coleta
python -m src completo --usina sao_domingos --sem-portal

# Ver o resumo gravado pela última execução do Tratamento
(Get-Content data\usinas\sao_domingos\tratamento\etapa.json -Raw -Encoding UTF8 | ConvertFrom-Json).resumo | ConvertTo-Json -Depth 4
```
