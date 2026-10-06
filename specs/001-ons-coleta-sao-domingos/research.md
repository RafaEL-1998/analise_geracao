# Research: Coleta e Filtragem de Dados ONS - UHE São Domingos

Este documento consolida as decisões técnicas, padrões arquiteturais e diretrizes adotadas para a implementação da coleta, download e filtragem exaustiva dos dados de Energia Vertida Turbinável da UHE São Domingos.

**Revisão de 2026-10-05**: as seções 2 a 5 foram atualizadas para as decisões em vigor após a auditoria de 30/09/2026, mantendo a decisão original como alternativa rejeitada; as seções 6 (cobertura da série) e 7 (validação externa de 02/10/2026) são novas. A versão anterior está em `research.md.2026-10-05.bak`.

---

## 1. Mecanismo de Descoberta dos Recursos de Dados

- **Decisão**: Utilização da API REST oficial CKAN do Portal de Dados Abertos do ONS (`https://dados.ons.org.br/api/3/action/package_show?id=energia-vertida-turbinavel`), com 3 tentativas e recuo exponencial também na consulta ao catálogo. Um recurso é aceito quando o formato é `CSV` ou a URL termina em `.csv`; de cada recurso são lidos URL, nome, identificador, tamanho (`size`) e data de última modificação (`last_modified`, com recurso a `metadata_modified` ou `created` quando ausente).
- **Justificativa**: A chamada `package_show` retorna a lista completa e estruturada em JSON de todos os recursos, com URLs diretas no AWS S3 (`ons-aws-prod-opendata.s3.amazonaws.com/dataset/energia_vertida_turbinavel_ho/`). Em 30/09/2026 eram 42 arquivos CSV: 9 anuais (2015 a 2023) e 33 mensais (01/2024 a 09/2026). Isso elimina a fragilidade de web scraping baseado em seletores HTML.
- **Alternativas consideradas**:
  - *Web Scraping em HTML com BeautifulSoup*: Rejeitado por ser mais frágil a mudanças de layout e templates do portal.
  - *Hardcoding de URLs/anos*: Rejeitado expressamente pela Constituição (Princípio III - Varredura Exaustiva), pois impediria a descoberta de novos meses/anos e violaria a integridade da série temporal.

---

## 2. Estratégia de Download, Atualização e Idempotência

- **Decisão (em vigor desde 30/09/2026)**: Download via streaming HTTP com a biblioteca padrão `urllib.request`, em blocos de 1 MB, timeout de 60 s, 3 tentativas com espera de 2 s e 4 s. O conteúdo é gravado em `<arquivo>.part` e só substitui o arquivo final ao término do download (troca atômica). Um manifesto (`data/raw/_manifesto_ons.json`, gravado também de forma atômica) registra por arquivo a URL, o `last_modified` e o tamanho publicados, o tamanho local, a data e hora do registro (UTC) e a origem do registro (`DOWNLOAD` ou `ARQUIVO_EXISTENTE`). A cópia local é reaproveitada (`CACHED`) só se o tamanho local e o `last_modified` coincidirem com o manifesto; sem entrada no manifesto (primeira execução), basta o tamanho local ser igual ao publicado. Caso contrário o arquivo é baixado novamente (`UPDATED`). `--force-download` ignora o cache.
- **Justificativa**: Os arquivos do ONS têm de 15 MB (mensais) a 200 MB (anuais), e o download em blocos evita picos de memória. O ONS revisa arquivos já publicados: em 30/09/2026 o arquivo de 09/2026 foi republicado (`last_modified` 2026-09-30T15:05) com outro tamanho e foi baixado novamente. A conferência só por tamanho (decisão original) não detectaria uma revisão de mesmo tamanho.
- **Risco residual observado**: na primeira execução com manifesto (30/09/2026), o arquivo de 08/2026 tinha no catálogo `last_modified` (2026-09-30T15:06) posterior ao download local, mas o mesmo tamanho publicado, e foi aceito pela regra de tamanho. A conferência externa de 02/10/2026 (seção 7) confirmou que os registros da usina nesse mês são idênticos aos publicados. Desde então, o `last_modified` registrado no manifesto é usado nas execuções seguintes.
- **Comportamento em falha**: esgotadas as tentativas de um arquivo, é lançado `DownloadError` com o nome do recurso, a sincronização é interrompida (os arquivos seguintes não são baixados nessa execução), o manifesto é gravado com o que já foi sincronizado e o pipeline retorna código 1.
- **Alternativas consideradas**:
  - *Verificação de tamanho local versus `Content-Length` (decisão original de 30/09/2026)*: Substituída porque não detecta revisões de mesmo tamanho e não deixa registro da versão baixada.
  - *Carregar arquivo integralmente na memória via `response.content`*: Rejeitado pelo risco de estouro de memória em arquivos de grandes dimensões.
  - *Sobrescrever sempre todos os arquivos*: Rejeitado por baixar cerca de 2,2 GB a cada execução sem necessidade.

---

## 3. Estratégia de Parsing e Filtragem de Dados

- **Decisão (em vigor desde 30/09/2026)**: Leitura em streaming com `csv.reader` (delimitador `;`), tentando UTF-8; se ocorrer erro de decodificação, o arquivo inteiro é relido em Latin-1 e a codificação usada vai para o relatório de auditoria. As colunas `cod_usina` e `nom_reservatorio` são localizadas pelo nome no cabeçalho. Um registro é extraído quando:
  1. `cod_usina` (sem espaços) é igual a `153`; **e**
  2. `nom_reservatorio`, normalizado (decomposição Unicode sem acentos, sem espaços nas pontas, em maiúsculas), contém `SAO DOMINGOS`. Por desempenho, antes da normalização completa é feito um pré-teste barato pela última palavra do nome (`DOMINGOS`).

  Linhas em que só o critério 1 confere são contadas em `registros_codigo_sem_nome`; só o critério 2, em `registros_nome_sem_codigo`. Nenhuma das duas é extraída, e o arquivo gera alerta no log. O nome do agente, o subsistema, a bacia e o rio não são usados. Os registros extraídos recebem `tipo_match = CODIGO_E_NOME`. Os parâmetros vêm de `COD_USINA_ONS` e `NOME_RESERVATORIO_REFERENCIA` (`src/config.py`) e podem ser trocados por `--cod-usina` e `--nome-reservatorio`.
- **Justificativa**:
  - O `cod_usina` é o "código da usina nos modelos de otimização" (dicionário de dados do ONS) e é estável ao longo da série; o nome do agente não é: `CGT ELETROSUL` de 28/08/2018 a 28/02/2026 e `AXIA SUL` a partir de 01/03/2026.
  - A chave canônica original (`"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"`, os 6 primeiros campos da linha) só casava a partir de 03/2026. No relatório de auditoria da versão original (`reports/_versao_anterior_2026-09-30/data_processed/relatorio_auditoria_varredura.csv`), todos os arquivos de 2018 a 02/2026 tinham `registros_canonicos_encontrados = 0` e só eram encontrados pela busca secundária.
  - Exigir código e nome evita capturar reservatórios homônimos; contar os casos parciais torna visível uma eventual troca de código ou de nome no cadastro do ONS. Em 30/09/2026 não houve nenhum caso parcial nos 42 arquivos.
  - A leitura por streaming inspeciona os cerca de 15 milhões de linhas dos 42 arquivos em cerca de 45 s, com memória constante na leitura.
- **Limitação conhecida**: linhas com menos campos do que o índice da coluna de identificação mais à direita são contadas no total lido e descartadas sem registro em log.
- **Alternativas consideradas**:
  - *Chave canônica textual + busca secundária por `SAO DOMINGOS` no reservatório (decisão original de 30/09/2026)*: Substituída porque depende do nome do agente e extraía linhas apenas pelo nome (marcadas `SECONDARY`), sujeitas a homônimos.
  - *Somente `cod_usina`*: Rejeitado porque uma reutilização ou troca de código passaria despercebida.
  - *Ler cada CSV completo via `pandas.read_csv()` durante a filtragem*: Rejeitado porque aloca memória desnecessária para carregar milhões de linhas de outras usinas antes de filtrar.
  - *Filtro em linha de comando (grep/awk)*: Rejeitado pela Constituição (Princípio II - Python exclusivo e compatibilidade obrigatória com PowerShell/Windows).

---

## 4. Consolidação e Formato de Saída

- **Decisão (em vigor desde 30/09/2026)**: Os arquivos são lidos em ordem alfabética de nome, o que coloca os anuais (`..._AAAA.csv`) antes dos mensais (`..._AAAA_MM.csv`). A consolidação mantém um registro por par (`cod_usina`, `din_instante`), prevalecendo o lido por último, e conta as duplicatas idênticas e as conflitantes (estas com alerta no log indicando os dois arquivos). Registros sem `din_instante` são descartados. A base é ordenada por (`din_instante`, `cod_usina`) e gravada em `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv`; o relatório de auditoria, em `data/processed/relatorio_auditoria_varredura.csv`.
- **Justificativa**: O CSV com delimitador `;`, UTF-8 sem BOM, é compatível com Python, Excel e Power BI e com os relatórios de fiscalização da AGEMS/ANEEL. A regra "último arquivo lido prevalece" é determinística e dispensa comparar datas de emissão. Na execução de 30/09/2026 não houve duplicatas: a soma dos registros extraídos por arquivo (70.895) é igual ao total da base. A rastreabilidade é assegurada pela coluna `arquivo_origem` em cada registro. Os valores numéricos são regravados com a representação decimal do Python (ponto decimal), que reproduz os valores publicados pelo ONS; ausentes ficam em branco.
- **Alternativas consideradas**:
  - *Deduplicar só por `din_instante`, prevalecendo "o arquivo com data de emissão mais recente ou o registro canônico mais completo" (regra original do data-model)*: Substituída porque, com o `cod_usina` na chave, registros de usinas diferentes no mesmo instante não se anulam (caso coberto por `test_consolidate_nao_mistura_usinas_no_mesmo_instante`), porque a ordem de leitura já é determinística e porque deixou de existir a distinção canônico/secundário.
  - *Banco de dados SQLite/PostgreSQL*: Desnecessário para o volume filtrado de uma única UHE (cerca de 71 mil linhas horárias), violando a simplicidade (KISS).
  - *Múltiplos arquivos parciais soltos*: Rejeitado por dificultar a análise cronológica contínua do vertimento da usina.

---

## 5. Padrões de Código e Dependências

- **Decisão**: Código Python 3.10+ modularizado no pacote `src/`, executável via CLI (`python -m src.main`), usando apenas biblioteca padrão nos módulos desta feature (`urllib`, `csv`, `json`, `unicodedata`, `dataclasses`, `pathlib`, `logging`, `argparse`). Logs na saída padrão no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] módulo - mensagem`; o pipeline não grava arquivo de log.
- **Justificativa**: Reduz atrito de ambiente e dependências e facilita a execução imediata no `venv` existente. A versão original previa `requests` e `pandas` para orquestração e formatação; nenhum dos dois é usado pelos módulos de coleta, filtragem e consolidação (o `pandas` só aparece em `src/main.py`, na etapa 3, escopo de `specs/004-conferencia-outros`).

---

## 6. Cobertura e Completude da Série (constatado em 30/09/2026)

- **Primeiro registro**: 28/08/2018 00h. Os arquivos de 2015, 2016 e 2017 foram varridos (cerca de 1,2 milhão de linhas cada) e não contêm a usina: nem por código, nem por nome. A operação comercial começou em 2013; o período de 2013 a 27/08/2018 não é coberto por este conjunto de dados.
- **Último registro**: 28/09/2026 23h (arquivo de 09/2026, parcial, publicado em 30/09/2026).
- **Volume**: 70.895 registros horários, sem duplicatas, em 39 arquivos com registros (2018 a 09/2026). A série tem 1 hora ausente, 04/11/2018 00h, por causa do início do horário de verão (hora inexistente no horário legal). O pipeline não preenche horas ausentes.
- **Agentes**: `CGT ELETROSUL` em 65.807 registros (28/08/2018 a 28/02/2026) e `AXIA SUL` em 5.088 registros (01/03/2026 a 28/09/2026). Subsistema `SE`/`SUDESTE`, bacia `PARANA`, rio `VERDE` e reservatório `SAO DOMINGOS` são constantes na série.
- **Leitura**: os 42 arquivos foram lidos em UTF-8; nenhum `FALHA`; nenhuma linha com identificação divergente; nenhum valor numérico ausente na base da usina.

---

## 7. Validação Externa da Base (02/10/2026)

- **Método**: consulta aos dados abertos do ONS pelo servidor MCP `ons-dados` (registrado em `.mcp.json`, `https://mcp.dados.tiago.ons.org.br/`), comparando os registros horários da usina na base local com os publicados pelo ONS no S3.
- **Resultado**: a base local bate exatamente com o S3 do ONS em todos os meses de 08/2018 a 08/2026. O mês 09/2026 (parcial) não fez parte da conferência.
- **Implicações**: confirma o SC-002 (zero registros omitidos) no período conferido, confirma que a troca do critério de extração não perdeu nem acrescentou registros e afasta o risco residual da seção 2 para 08/2026.
- **Limitação**: a conferência foi interativa; não há script nem arquivo de saída dela versionado no repositório (pendência registrada no Histórico de revisões de [spec.md](spec.md)). As conferências com outros conjuntos do ONS (geração por usina, indicadores por unidade geradora etc.) pertencem a `specs/004-conferencia-outros`.
