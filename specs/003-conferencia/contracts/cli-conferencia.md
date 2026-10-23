# Contract: Linha de comando — Conferência

**Spec**: [spec.md](../spec.md)

As regras comuns do fluxo (sintaxe geral, perfil inválido ou em rascunho, pré-requisitos, `etapa.json`, comando
`completo` e ferramenta `copia-seguranca`) estão no [contrato da Coleta de dados](../../001-coleta-dados/contracts/cli-coleta.md).

## Sintaxe

```text
python -m src <comando> --usina <slug> [opções]

python -m src conferencia --usina <slug> [--log-level {DEBUG,INFO,WARNING,ERROR}]
```

| Opção | Obrigatória | Efeito |
|---|---|---|
| `--usina <slug>` | sim | nome da pasta da usina em `usinas/`; define o perfil e as pastas `data/usinas/<slug>/…` |
| `--log-level` | não | `DEBUG`, `INFO` (padrão), `WARNING` ou `ERROR`, em maiúsculas; vale para todos os loggers da chamada (`pipeline`, `coleta`, `tratamento`, `conferencia`, `analises`, `relatorio` e `persistencia`), inclusive os dos módulos carregados depois |

A Conferência não tem opções próprias. No `completo`, ela é a terceira etapa e roda sem opções. O `comparar --todas`
(contrato na spec da Geração do relatório) refaz a Conferência de cada relatório de referência num espaço isolado, a
partir da Coleta e do perfil congelados.

## O que o comando faz

1. Valida as opções e o perfil da usina.
2. Confere o `etapa.json` do Tratamento de dados: precisa estar `concluida` e no formato atual.
3. Faz as conferências do catálogo que se aplicam à usina:
   - na hidrelétrica com EVT, as seis de sempre (`geracao`, `disponibilidade`, `vazoes`, `dispf_horas`, `teifa_teip` e
     `cadastro`);
   - nas demais usinas, as aplicáveis ao tipo e aos níveis dos dados: `dispf_horas`, `teifa_teip` e `cadastro`; nas
     térmicas, `programacao_despacho` (G3) e `verificada_despacho` (G4); nas eólicas e solares, `geracao_fontes` (G1),
     `soma_conjunto` (G2) e `programacao_renovaveis` (G5); nas hidrelétricas sem EVT, `alinhamento_hidrologia`.
4. Grava em `data/usinas/<slug>/conferencia/` o `conferencias.pkl`, os CSV das conferências que têm tabela nesta
   execução, `nao_aplicaveis.csv` (as conferências do catálogo que não se aplicam, com o motivo) e o `etapa.json`.
5. Mostra no log o resumo da etapa e a pasta de saída.

Só lê arquivos locais (dados tratados, ficha do cadastro e perfil); nunca acessa a rede nem altera as etapas anteriores.

## Códigos de saída

| Código | Quando | O que fica gravado |
|---|---|---|
| 0 | conferências da usina gravadas; as vazões atingiram a meta, não são aplicáveis ou não fazem parte das conferências da usina | resultados, `nao_aplicaveis.csv` e `etapa.json` `concluida` |
| 1 | erro: arquivo de entrada ilegível, falha de gravação (com o arquivo restaurado), erro inesperado ou interrupção pelo usuário (Ctrl+C) | `etapa.json` com `falha` e `resumo.erro`; o que foi gravado antes do erro fica, mas as Análises recusam rodar |
| 2 | opção inválida ou `--usina` ausente, recusadas antes de qualquer ação | nada |
| 3 | só na hidrelétrica com EVT: vazões coincidentes em menos de 99 % das horas comuns, ou nenhuma hora comum | seis resultados, `nao_aplicaveis.csv` e `etapa.json` `concluida`, com `codigo_saida` 3; o `completo` para aqui |
| 4 | perfil da usina inválido, inclusive em rascunho | nada |
| 5 | Tratamento sem `etapa.json`, com `falha`, `desatualizada` ou em formato antigo | nada |

Divergências entre as fontes não mudam o código, nem o resultado das conferências sem meta (G1 a G5 e o alinhamento da
hidrologia pela geração). Com o código 3, as Análises e a Geração do relatório podem ser executadas à parte; as Análises
omitem os cruzamentos hidrológicos.

## Mensagens

| Situação | Nível e logger | Texto |
|---|---|---|
| Tratamento não concluído (código 5) | ERROR, `pipeline` | `A etapa 'conferencia' precisa da etapa 'tratamento' concluída para a usina '<slug>'. Execute antes: python -m src tratamento --usina <slug>` |
| Perfil inválido ou em rascunho (código 4) | saída de erro | `Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):`, seguido de uma linha por problema (no rascunho, `usina.situacao: perfil em rascunho; …`) |
| Início | INFO, `pipeline` | `Etapa 'conferencia' da usina '<slug>' iniciada.` |
| Conferência feita | INFO, `conferencia` | `Conferência '<id>': <coincidentes> de <comparados> <unidade> coincidentes; <divergentes> divergentes.` |
| Conferência executada e não aplicável | WARNING, `conferencia` | `Conferência '<id>' não aplicável: <motivo>.` (as que o catálogo descarta antes de rodar só aparecem em `nao_aplicaveis.csv` e no `resumo`) |
| G4 com coincidência maior com uma hora de deslocamento | WARNING, `conferencia` | `G4: a coincidência do despacho com a Geração por usina melhora com uma hora de deslocamento (<pct>% contra <pct>%); conferir a convenção de hora declarada e corrigi-la, sem ajuste automático.` |
| Meta das vazões não atingida (código 3) | ERROR, `conferencia` | `Alinhamento das vazões abaixo da meta: <pct>% de <horas> horas comuns (meta 99%); os cruzamentos hidrológicos não serão publicados.` |
| Cada arquivo gravado | INFO, `persistencia` | `NOVO`, `ALTERADO` ou `INALTERADO`, com o nome do arquivo |
| Falha de gravação (código 1) | ERROR, `persistencia` | `Falha ao gravar <arquivo>: <motivo>. O arquivo foi mantido na versão anterior (verifique se ele está aberto em outro programa).` |
| Erro (código 1) | ERROR, `pipeline`, com o rastreamento | `Etapa 'conferencia' da usina '<slug>' terminou com erro: <erro>` |
| Interrupção pelo usuário (código 1) | ERROR, `persistencia`, se uma gravação estava em curso, e `pipeline` | `Gravação de <arquivo> interrompida; o arquivo foi mantido na versão anterior.` e `Etapa 'conferencia' da usina '<slug>' interrompida pelo usuário.` |
| Análises ou Relatório já executados (códigos 0 e 3) | INFO, `pipeline` | `Etapas seguintes marcadas como desatualizadas: <etapas>.` |
| Fim da etapa | INFO, `pipeline` | `Etapa 'conferencia' da usina '<slug>': <status> (código <n>). Resumo: <resumo em JSON, com a chave nao_aplicaveis>. Pasta: <pasta>` |
| Parada do `completo` (códigos 1 e 3) | WARNING, `pipeline` | `Fluxo completo interrompido na etapa 'conferencia' (código <n>).` |

O log sai na saída padrão, no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] logger - mensagem`. Os motivos de não aplicabilidade
e o `resumo` estão no [data model](../data-model.md) (seções 4 e 5.2).

## Exemplos

```powershell
# Refazer a Conferência da São Domingos depois do Tratamento de dados
python -m src conferencia --usina sao_domingos

# Só avisos e erros no log: conferências não aplicáveis, convenção de hora da G4 e meta das vazões
python -m src conferencia --usina sao_domingos --log-level WARNING

# Com o código 3 (meta das vazões não atingida), seguir à parte, sem os cruzamentos hidrológicos
python -m src conferencia --usina sao_domingos
if ($LASTEXITCODE -eq 3) {
    python -m src analises --usina sao_domingos
    if ($LASTEXITCODE -eq 0) { python -m src relatorio --usina sao_domingos }
}

# Térmica: G3, G4 e os indicadores; ver as conferências que não se aplicam
python -m src conferencia --usina william_arjona
Import-Csv data\usinas\william_arjona\conferencia\nao_aplicaveis.csv -Delimiter ';' -Encoding UTF8
```
