# Contract: Linha de comando — catálogo de usinas (`usinas`)

**Spec**: [spec.md](../spec.md) (FR-003 a FR-005) · **Data model**: [seção 2](../data-model.md) · **Research**: R1 a R3

Os códigos de saída, o `--log-level` e o formato do log são os do [contrato da Coleta](../../001-coleta-dados/contracts/cli-coleta.md).

## Sintaxe

```text
python -m src usinas [--estado <UF>] [--tipo <tipo>] [--modalidade <modalidade>] [--sem-portal] [--forcar-download] [--log-level <nível>]
```

- Não usa `--usina` nem lê perfil.
- É um comando da Coleta. Junto com `coleta` e `completo`, é o único que acessa o portal do ONS (princípio I).
- O primeiro `usinas` com o portal só roda depois de congelada a Coleta da São Domingos (R22, R27): ele baixa arquivos nas pastas compartilhadas de `data/raw/`.

| Opção | Efeito |
|---|---|
| `--estado <UF>` | filtra a listagem pela sigla do estado (2 letras); o catálogo é sempre montado para o Brasil inteiro |
| `--tipo <tipo>` | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL`, `UFV` ou `conjunto` |
| `--modalidade <modalidade>` | como no cadastro (`"TIPO I"` … `"TIPO III"`), sem diferença entre maiúsculas e minúsculas |
| `--sem-portal` | não consulta o portal; monta o catálogo só com os arquivos locais |
| `--forcar-download` | baixa de novo os arquivos usados pelo catálogo; sem efeito com `--sem-portal` |

## O que faz

1. **Sincroniza** (exceto com `--sem-portal`), com o catálogo CKAN, o cache e as versões de hoje:
   - Modalidade das usinas, Composição dos conjuntos e Capacidade de geração;
   - o arquivo mais recente de cada conjunto de série já implementado;
   - todos os arquivos do despacho térmico (a partir da fase B);
   - os arquivos de geração dos últimos 12 meses completos;
   - os dicionários de dados desses conjuntos (princípio IV).
2. **Monta o catálogo** e grava `data/catalogo/` por inteiro, sem `.bak`: `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`.
3. **Lista na tela** as usinas do filtro, ordenadas por estado, tipo e nome, com:
   - nome, CEG, id ONS, tipo, modalidade, potência autorizada e conjunto;
   - a cobertura de cada conjunto de série do tipo, numa coluna por conjunto: `P` (próprio), `C` (conjunto), `A` (agregado) ou `-` (ausente) (FR-003);
   - o slug do perfil, quando existe, achado pelo CEG em `usinas/*/perfil.toml`.
4. Termina com as contagens por tipo do filtro e a pasta do catálogo.

## Códigos de saída

| Código | Situação |
|---|---|
| 0 | catálogo montado e listado, inclusive quando o filtro não tem nenhuma usina (com aviso) |
| 1 | catálogo do ONS inacessível depois das tentativas, falha de gravação, interrupção pelo usuário ou erro inesperado |
| 2 | opção inválida (argparse); Modalidade, Composição ou Capacidade não obtida: download sem sucesso ou, com `--sem-portal`, arquivo local ausente |

Falha num dicionário não muda o código, como na Coleta de hoje.

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Fim | log, `INFO` | `Catálogo de usinas: <N> linhas do cadastro (publicado em <data>), <M> no filtro. Pasta: data/catalogo/` |
| Filtro vazio | log, `WARNING` | `Nenhuma usina no filtro (<filtro>).` |
| Tipo do ONS diferente do tipo do CEG | log, `WARNING` | `<K> usinas com o tipo publicado pelo ONS diferente do tipo do CEG; ver a coluna "divergencias" de data/catalogo/usinas.csv.` |
| Cadastral não obtido (código 2) | log, `ERROR` | `Conjunto cadastral do ONS não obtido (<conjunto>): <motivo>.` |

## Exemplos

```powershell
# Catálogo atualizado e as usinas de MS
python -m src usinas --estado MS

# Só as térmicas de MS, sem consultar o portal
python -m src usinas --estado MS --tipo UTE --sem-portal

# Solares de MS em conjunto de usinas
python -m src usinas --estado MS --tipo UFV --modalidade "TIPO II-C"
```
