# CLI Contract: Pipeline de Coleta e Filtragem ONS

Este documento define a interface de linha de comando (CLI), parâmetros, códigos de saída e formato de dados de saída para os scripts Python do pipeline.

**Revisão de 2026-10-05**: contrato alinhado a `src/main.py`, `src/collector.py` e `src/consolidator.py` em vigor. Removidos `--filter-key` e `--secondary-term` e o código de saída 3 (nunca implementado); incluídos `--cod-usina` e `--nome-reservatorio` (auditoria de 30/09/2026); registradas `--indicadores-only` e `--sem-indicadores`, que pertencem a `specs/004-conferencia-outros`; colunas do relatório de auditoria corrigidas para as reais. A versão anterior está em `cli-contract.md.2026-10-05.bak`.

---

## 1. Comando de Execução

O pipeline é executado a partir da raiz do repositório utilizando o interpretador do ambiente virtual Python:

```powershell
python -m src.main [OPÇÕES]
```

Sem nenhuma opção de modo, o comportamento é o mesmo de `--full-pipeline`.

---

## 2. Argumentos de Linha de Comando (Flags)

As opções `--full-pipeline`, `--download-only`, `--filter-only` e `--indicadores-only` são mutuamente exclusivas; informar duas delas é erro de argumento (código 2).

| Flag | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `--full-pipeline` | Flag booleano | `False` | Executa o fluxo completo: descoberta, download, filtragem e consolidação (etapas 1 e 2). Em seguida executa a etapa 3 (indicadores oficiais), salvo com `--sem-indicadores`; ver `specs/004-conferencia-outros`. |
| `--download-only` | Flag booleano | `False` | Executa apenas a descoberta e a sincronização dos CSVs em `--raw-dir` (etapa 1). Não regrava a base nem o relatório. |
| `--filter-only` | Flag booleano | `False` | Executa apenas a filtragem e a consolidação a partir dos CSVs já existentes em `--raw-dir` (etapa 2), sem acessar o catálogo. A etapa 3 também é executada, salvo com `--sem-indicadores`. |
| `--indicadores-only` | Flag booleano | `False` | Fora do escopo desta feature: atualiza só os indicadores oficiais do ONS por unidade geradora. Ver `specs/004-conferencia-outros`. |
| `--sem-indicadores` | Flag booleano | `False` | Fora do escopo desta feature: pula a etapa 3. Use-o para executar somente as etapas desta feature. Ver `specs/004-conferencia-outros`. |
| `--raw-dir` | Caminho | `<raiz do projeto>/data/raw` | Diretório dos CSVs originais e do manifesto `_manifesto_ons.json`. Só os `*.csv` do próprio diretório são varridos (subpastas não). |
| `--processed-dir` | Caminho | `<raiz do projeto>/data/processed` | Diretório onde a base consolidada e o relatório de auditoria são gravados. |
| `--cod-usina` | Inteiro | `153` | `cod_usina` da usina nos arquivos do ONS (critério principal de extração). |
| `--nome-reservatorio` | String | `SAO DOMINGOS` | Nome do reservatório usado para conferir o `cod_usina`. É normalizado (sem acentos, maiúsculas) antes da comparação por "contém". |
| `--force-download` | Flag booleano | `False` | Baixa novamente todos os arquivos, ignorando o manifesto e as cópias locais. |
| `--log-level` | Escolha | `INFO` | `DEBUG`, `INFO`, `WARNING` ou `ERROR`. **Limitação**: só altera o logger `main`; os loggers `collector`, `filter` e `consolidator` permanecem em `INFO`. |

**Removidas na auditoria de 30/09/2026**: `--filter-key` (chave canônica textual) e `--secondary-term` (termo da busca secundária), substituídas por `--cod-usina` e `--nome-reservatorio` (ver Histórico de revisões de [spec.md](../spec.md)).

### 2.1 Etapas executadas por modo

| Modo | Etapa 1: catálogo e download | Etapa 2: filtragem, consolidação e auditoria | Etapa 3: indicadores (spec 004) |
| :--- | :---: | :---: | :---: |
| (nenhum) ou `--full-pipeline` | Sim | Sim | Sim, se a base não estiver vazia e sem `--sem-indicadores` |
| `--download-only` | Sim | Não | Não |
| `--filter-only` | Não | Sim | Sim, se a base não estiver vazia e sem `--sem-indicadores` |
| `--indicadores-only` | Não | Não | Só a etapa 3 |

---

## 3. Códigos de Retorno (Exit Codes)

| Código | Significado | Descrição |
| :---: | :--- | :--- |
| `0` | **Sucesso** | Etapas concluídas; com a etapa 2, todos os arquivos foram lidos e as saídas gravadas. |
| `1` | **Erro de Execução / Rede** | Falha definitiva ao consultar o catálogo ou ao baixar um arquivo após 3 tentativas (`DownloadError`), outro erro do pipeline (`ONSError`), erro inesperado ou interrupção pelo usuário (Ctrl+C). Na falha de download, a sincronização para no arquivo que falhou e o manifesto é gravado com o que já foi sincronizado. |
| `2` | **Base Incompleta** ou **Erro de Argumentos** | (a) Um ou mais arquivos com status `FALHA` na varredura: a base e o relatório são gravados mesmo assim, o log lista os arquivos e informa que a base está incompleta, e a etapa 3 não é executada. (b) Argumentos inválidos ou incompatíveis, rejeitados pelo `argparse` antes da execução (ex.: dois modos ao mesmo tempo, `--log-level` inválido, `--cod-usina` não inteiro). |
| outros | **Etapa 3** | Códigos não nulos retornados pela etapa 3 ou por `--indicadores-only` são repassados; ver `specs/004-conferencia-outros`. |

O código `3` ("Inconsistência de Dados Crítica"), previsto na versão original deste contrato, nunca foi implementado e foi removido; arquivo ilegível resulta no código 2.

**Observação**: se `--raw-dir` não contiver nenhum CSV, a etapa 2 emite aviso no log, grava a base e o relatório apenas com o cabeçalho e retorna `0`.

---

## 4. Artefatos de Saída Gerados

As saídas da etapa 2 são regravadas integralmente a cada execução, sem cópia `.bak` automática.

### 4.1 Base Consolidada (`<processed-dir>/uhe_sao_domingos_energia_vertida_consolidado.csv`)
- **Separador**: Ponto e vírgula (`;`).
- **Codificação**: UTF-8 sem BOM; fim de linha CRLF.
- **Cabeçalho** (20 colunas): as 18 colunas do ONS (`id_subsistema`, `nom_subsistema`, `nom_bacia`, `nom_rio`, `nom_agente`, `nom_reservatorio`, `cod_usina`, `din_instante`, `val_geracao`, `val_disponibilidade`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_produtividade`, `val_folgadegeracao`, `val_energiavertida`, `val_vazaovertidaturbinavel`, `val_energiavertidaturbinavel`) acrescidas de `arquivo_origem` e `tipo_match` (sempre `CODIGO_E_NOME`).
- **Valores**: números com ponto decimal; valores ausentes em branco.
- **Unicidade**: um registro por par (`cod_usina`, `din_instante`).
- **Ordenação**: Cronológica ascendente por `din_instante` (desempate por `cod_usina`).

### 4.2 Relatório de Auditoria (`<processed-dir>/relatorio_auditoria_varredura.csv`)
- **Separador**: Ponto e vírgula (`;`).
- **Codificação**: UTF-8 sem BOM; fim de linha CRLF.
- **Linhas**: uma por arquivo `*.csv` de `--raw-dir`, em ordem alfabética de nome.
- **Colunas**:
  - `nome_arquivo`: Nome do arquivo CSV inspecionado.
  - `periodo_referencia`: Nome do arquivo sem extensão.
  - `total_linhas_arquivo`: Linhas não vazias lidas após o cabeçalho.
  - `registros_extraidos`: Linhas em que `cod_usina` e nome do reservatório conferem.
  - `registros_codigo_sem_nome`: Linhas com o `cod_usina` e outro reservatório (não extraídas).
  - `registros_nome_sem_codigo`: Linhas com o reservatório e outro `cod_usina` (não extraídas).
  - `codificacao`: `utf-8` ou `latin-1`.
  - `status_processamento`: `PROCESSADO`, `SEM_REGISTROS` ou `FALHA`.
  - `data_hora_processamento`: Data e hora em UTC, no formato `AAAA-MM-DD HH:MM:SS`.

### 4.3 Manifesto de Versões (`<raw-dir>/_manifesto_ons.json`)
- **Formato**: JSON em UTF-8, indentado, com chaves ordenadas; gravado de forma atômica (`.json.part` renomeado) ao final da etapa 1, inclusive quando ela é interrompida por falha.
- **Conteúdo**: um objeto por arquivo local com `url`, `ultima_modificacao`, `tamanho_publicado_bytes`, `tamanho_bytes`, `registrado_em_utc` e `origem_registro` (`DOWNLOAD` ou `ARQUIVO_EXISTENTE`). Detalhes em [data-model.md](../data-model.md), seção 2.2.

### 4.4 Logs
- Emitidos apenas na saída padrão (não há arquivo de log), no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] módulo - mensagem`.
- Avisos relevantes para auditoria: divergência de identificação por arquivo, duplicata conflitante na consolidação, tamanho baixado diferente do publicado e arquivos com falha de leitura.
