# Contract: Linha de comando — catálogo de usinas (`usinas`)

**Spec**: [spec.md](../spec.md) (FR-051 e FR-052) · **Data model**: [seção 2.5](../data-model.md) · **Plano**: decisões técnicas D19 a D21 e D33

Os códigos de saída, o `--log-level` e o formato do log são os do [contrato da Coleta](cli-coleta.md).

## Sintaxe

```text
python -m src usinas [--estado <UF>] [--tipo <tipo>] [--modalidade <modalidade>] [--sem-portal] [--forcar-download] [--log-level <nível>]
```

- Não usa `--usina` nem valida perfil; só lê `usinas/*/perfil.toml` para mostrar o slug do perfil de cada usina, achado pelo CEG.
- É um comando da Coleta. Junto com `coleta` e `completo`, é o único que acessa o portal do ONS (princípio I da constituição).
- Os downloads vão para as pastas compartilhadas de `data/raw/`, as mesmas da Coleta das usinas. Por isso, as referências refazem as etapas a partir da Coleta congelada de cada usina, e não dos brutos (spec da Geração do relatório).

| Opção | Efeito |
|---|---|
| `--estado <UF>` | filtra a listagem pela sigla do estado (2 letras; sem diferença entre maiúsculas e minúsculas); o catálogo é sempre montado para o Brasil inteiro |
| `--tipo <tipo>` | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL`, `UFV` ou `conjunto`, sem diferença entre maiúsculas e minúsculas |
| `--modalidade <modalidade>` | como no cadastro (`"TIPO I"` … `"TIPO III"`), comparada sem acento e sem diferença entre maiúsculas e minúsculas |
| `--sem-portal` | não consulta o portal; monta o catálogo só com os arquivos locais |
| `--forcar-download` | baixa de novo os arquivos usados pelo catálogo; sem efeito com `--sem-portal` |

## O que faz

1. **Sincroniza** (exceto com `--sem-portal`), com o catálogo CKAN, o cache e as versões da Coleta:
   - os quatro cadastrais: Modalidade das usinas, Composição dos conjuntos, Capacidade de geração e Reservatórios (estes ligam o CEG ao `cod_usina` e ao reservatório da EVT e dos dados hidrológicos);
   - o arquivo mais recente de cada conjunto de série do registro (nos indicadores, o da base mensal; nas restrições, o de cada variante, eólica e fotovoltaica);
   - todos os arquivos da Geração térmica por motivo de despacho, para os códigos de planejamento;
   - todos os arquivos da Programação diária, para os códigos de exibição de todo o período;
   - os arquivos da Geração por usina dos últimos 12 meses completos, para o panorama dos agregados;
   - os dicionários de dados desses conjuntos (princípio IV); falha num dicionário só gera aviso.
2. **Monta o catálogo** e grava `data/catalogo/` por inteiro, sem `.bak`, numa pasta temporária conferida antes da troca: `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`.
3. **Lista na saída padrão**, sempre a partir dos arquivos gravados, as usinas do filtro, ordenadas por estado, tipo e nome, com:
   - estado, tipo, nome (até 40 caracteres), CEG, id ONS, modalidade, potência autorizada (MW) e conjunto;
   - a cobertura de cada conjunto de série, numa coluna por conjunto (`EVT`, `IND`, `PRG`, `DSP`, `HID`, `GER`, `DES`, `CVU`, `FC`, `RDT`, `RRZ`): `P` (próprio), `C` (conjunto), `A` (agregado), `-` (ausente), ou em branco quando o conjunto não serve ao tipo;
   - o slug do perfil (`PERFIL`), quando há perfil com o CEG.
4. Termina com a linha `Por tipo: <tipo> <n>, …` das usinas do filtro e, no log, a mensagem de fim, com a pasta do catálogo.

## Códigos de saída

| Código | Situação |
|---|---|
| 0 | catálogo montado e listado, inclusive quando o filtro não tem nenhuma usina (com aviso) |
| 1 | catálogo do ONS inacessível depois das tentativas, falha de gravação, catálogo gravado não encontrado na releitura, interrupção pelo usuário ou erro inesperado |
| 2 | opção inválida (argparse); Modalidade das usinas, Composição dos conjuntos, Capacidade de geração ou Reservatórios não obtido: sem recurso no catálogo, download sem sucesso ou, com `--sem-portal`, arquivo local ausente |

Falha num dicionário não muda o código, como na Coleta.

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Fim | log, `INFO` | `Catálogo de usinas: <N> linhas do cadastro (publicado em <data>), <M> no filtro. Pasta: data/catalogo/` |
| Filtro vazio | log, `WARNING` | `Nenhuma usina no filtro (<filtro>).` |
| Tipo do ONS diferente do tipo do CEG | log, `WARNING` | `<K> usinas com o tipo publicado pelo ONS diferente do tipo do CEG; ver a coluna "divergencias" de data/catalogo/usinas.csv.` |
| Cadastral não obtido (código 2) | log, `ERROR` | `Conjunto cadastral do ONS não obtido (<conjunto>): <motivo>.` |
| Catálogo do ONS inacessível (código 1) | log, `ERROR` | `Catálogo do ONS inacessível: <erro>` |

## Exemplos

```powershell
# Catálogo atualizado e as usinas de MS
python -m src usinas --estado MS

# Só as térmicas de MS, sem consultar o portal
python -m src usinas --estado MS --tipo UTE --sem-portal

# Solares de MS em conjunto de usinas
python -m src usinas --estado MS --tipo UFV --modalidade "TIPO II-C"
```
