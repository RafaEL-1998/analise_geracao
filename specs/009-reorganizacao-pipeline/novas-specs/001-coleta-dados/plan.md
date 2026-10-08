# Implementation Plan: Coleta de dados

**Spec**: [spec.md](spec.md) · **Etapa**: 1 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-08

## Summary

A Coleta de dados (`src/coleta/`) consulta o catálogo CKAN do ONS para os dez conjuntos, baixa em streaming só os arquivos novos ou republicados (cache pelo manifesto de cada pasta, até duas versões anteriores por arquivo) e obtém sempre os dicionários de dados. Depois extrai dos arquivos locais as linhas da usina do perfil, por um identificador conferido por um segundo campo, com uma linha de auditoria por arquivo; a EVT vem primeiro e define o período dos demais, e a coleta para no primeiro conjunto com falha. Os resultados vão para `data/usinas/<slug>/coleta/`, com o `etapa.json`. As regras comuns às cinco etapas (linha de comando, perfil, `etapa.json`, pré-requisitos, `completo`, cópia de segurança e log) estão em `src/__main__.py`, `src/pipeline.py` e `src/comum/`.

## Technical Context

**Language/Version**: Python 3.14.6 no `venv` do projeto; mínimo 3.11, porque o perfil é lido com `tomllib`.

**Primary Dependencies**:
- `pandas`: tabelas e leitura de CSV (como texto) e de Parquet;
- `pyarrow`: projeção de colunas e filtros na leitura de Parquet;
- biblioteca padrão: `urllib.request` (catálogo e downloads), `csv` (varredura da EVT), `concurrent.futures` (downloads simultâneos), `hashlib`, `json`, `tomllib`, `argparse`, `unicodedata` e `shutil`;
- `openpyxl` é carregado por `src/comum/persistencia.py`, mas a etapa não grava planilha; `pytest` nos testes.

**Storage**: arquivos.
- `data/raw/`, compartilhado por todas as usinas: arquivos do ONS com o nome da URL, `_manifesto_ons.json` em cada pasta, `_versoes_anteriores/` e `_dicionarios/` (com manifesto próprio);
- `data/usinas/<slug>/coleta/`: `evt_extraido.csv`, cinco `*_extraido.parquet`, sete `auditoria_*.csv`, `cadastro_ficha.csv`, `dicionarios.csv` e `etapa.json`; todos, menos o `etapa.json`, gravados por `src/comum/persistencia.py` (`gravar_linhas_csv` na EVT e na auditoria dela, `gravar_csv` e `gravar_parquet` nos demais), com `.bak` da versão anterior, conteúdo idêntico não regravado, conferência no disco e restauração em falha ou interrupção (código 1), como descrito no [plano do Tratamento de dados](../002-tratamento-dados/plan.md) (D13);
- CSV com `;`, UTF-8 sem BOM e fim de linha do sistema (CRLF no Windows); datas `AAAA-MM-DD HH:MM:SS`;
- perfil em `usinas/<slug>/perfil.toml`; cópias de segurança em `_backup_<AAAA-MM-DD>_<motivo>/`, na raiz do projeto.

**Testing**: pytest sem rede (D6); 384 testes na suíte, entre eles:
- `tests/coleta/` (78): catálogo, cache, versões, dicionários, extração e auditoria de cada conjunto;
- `tests/comum/` (88): perfil, `etapa.json` e pré-requisitos, interrupção, gravação segura, cópia de segurança, conformidade e ausência de valores de usina no código;
- `tests/integracao/` (33): linha de comando e as cinco etapas de uma usina fictícia com `--sem-portal`.

**Target Platform**: Windows 11, execução local no `venv`, PowerShell.

**Project Type**: projeto único; pipeline de linha de comando (`python -m src`).

**Performance Goals**: execução real da São Domingos com `--sem-portal`, registrada no `etapa.json`:
- etapa completa em 4 min 20 s (`iniciada_em` 13:49:16Z, `concluida_em` 13:53:36Z); meta da SC-012: menos de 10 min;
- leitura dos 42 arquivos da EVT (14.993.512 linhas) em cerca de 45 s; meta: menos de 3 min;
- com o portal, soma-se o tempo de rede; sem novidade, só os 20 dicionários são baixados.

**Constraints**:
- única etapa com acesso à rede: só `src/coleta/catalogo.py` usa `urllib`;
- nenhum arquivo bruto é editado; com `--sem-portal`, nada é criado, alterado ou excluído em `data/raw/`;
- no máximo duas versões anteriores por arquivo; brutos, manifestos e dicionários sem `.bak`;
- leitura sem recursão nas pastas brutas: `_versoes_anteriores/` e `_dicionarios/` nunca são lidos como dados;
- nenhum valor de usina no código (`tests/comum/test_literais.py`).

**Scale/Scope**: São Domingos, período de 28/08/2018 00h a 28/09/2026 23h; `data/raw/` com cerca de 4,1 GB.

| Conjunto | Arquivos no escopo | Linhas lidas | Linhas da usina |
|---|---|---|---|
| EVT | 42 CSV (9 anuais e 33 mensais) | 14.993.512 | 70.895 |
| Indicadores e taxas (quatro conjuntos) | 18 CSV | 822.106 | 1.628 |
| Programação diária | 708 Parquet | 134.490.960 | 33.984 |
| Disponibilidade por usina | 98 (53 CSV e 45 Parquet) | 16.936.504 | 70.943 |
| Dados hidrológicos horários | 98 (97 Parquet e 1 CSV) | 11.206.586 | 71.456 |
| Geração por usina | 61 Parquet (4 anuais e 57 mensais) | 45.685.645 | 76.679 |
| Modalidade das usinas | 1 CSV | 6.017 | 1 (e 20 homônimos) |
| Dicionários de dados | 20 (10 PDF e 10 JSON) | — | — |

## Constitution Check

| Princípio / requisito da constituição 2.0.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | a spec descreve a etapa inteira e as regras comuns; só a Coleta acessa o portal; a partir do Tratamento, `src/pipeline.py` recusa a etapa sem a anterior concluída (código 5) |
| II. Relatório fiel aos dados | cumpre | nenhum valor de usina no código; toda linha extraída traz o arquivo de origem; os manifestos guardam as datas de publicação e de obtenção usadas nas legendas |
| III. Uma usina por execução, definida pelo perfil | cumpre | perfil validado antes de qualquer ação, com todos os problemas (código 4); regras gerais em `src/comum/regras.py`; homônimos excluídos pelos identificadores e contados |
| IV. Coleta completa e rastreável | cumpre | todos os arquivos da EVT e os do período nos demais; cache pelo manifesto; versões anteriores; dicionários a cada consulta ao portal, também quando a coleta para com 2; identificador com conferência; linhas parciais, linhas irregulares e valores inválidos contados na auditoria. Limitações conhecidas, sem efeito nos dados atuais: D12, D13, D15 e D16 |
| V. Tratamento sem descarte | não se aplica | as sinalizações são do Tratamento; a coleta entrega os valores como publicados, com a marca `_nao_numerico` nos conjuntos horários |
| VI. Conferência entre fontes | não se aplica | a coleta só entrega a ficha cadastral e as contagens que a Conferência examina |
| VII. Relatório padronizado | não se aplica | a coleta fornece as datas, as auditorias e o registro dos dicionários citados nas legendas e notas |
| RT 1. Python, `venv` e dependências usadas | cumpre | `requirements.txt` conferido contra os imports (`test_requirements_corresponde_aos_imports`); nada em script de shell |
| RT 2. Windows e PowerShell | cumpre | caminhos com `pathlib`; exemplos em PowerShell |
| RT 3. Gravação segura | cumpre | todo arquivo da usina passa por `src/comum/persistencia.py` (`test_etapas_gravam_dados_so_pela_persistencia`); brutos, manifestos e dicionários sem `.bak` |
| RT 4. Versões dos brutos | cumpre | `MAXIMO_VERSOES_ANTERIORES = 2`; a poda é registrada em `versoes_excluidas` |
| RT 5. Cópias de segurança do projeto | cumpre | `copia-seguranca` confere a cópia nova antes de excluir a mais antiga; ficam duas |
| RT 6. Pastas | cumpre | `src/comum/caminhos.py` |
| RT 7. Log | cumpre | formato e saída padrão comuns; `--log-level` aplicado aos loggers de `LOGGERS_PIPELINE` e mantido nos módulos carregados depois, como o da etapa executada (D5) |
| Qualidade 1. Testes | cumpre | sem rede, com dados sintéticos e uma usina fictícia |
| Qualidade 2 e 3. Entrega e recuperação | cumpre | SC-014 conferida na execução real; `.bak`, cópias de segurança e git |

## Project Structure

### Documentation (this feature)

```text
specs/001-coleta-dados/
├── spec.md                  # requisitos da etapa e regras comuns às cinco etapas
├── plan.md                  # este arquivo
├── data-model.md            # entradas, saídas, manifestos, perfil e etapa.json
├── contracts/
│   ├── cli-coleta.md        # linha de comando, códigos de saída e regras comuns
│   └── perfil-usina.md      # contrato do perfil da usina
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── __main__.py              # linha de comando única (argparse); lê o perfil (código 4) e despacha
├── pipeline.py              # ordem das etapas, etapa.json, pré-requisito (código 5), desatualizada, completo
├── coleta/
│   ├── etapa.py             # executar_coleta: ordem dos conjuntos, parada na falha, resumo do etapa.json
│   ├── catalogo.py          # catálogo CKAN, download com tentativas, manifesto, versões anteriores e poda
│   ├── evt.py               # EVT: sincronização, varredura com csv.reader, consolidação e auditoria
│   ├── indicadores.py       # indicadores por UG e taxas TEIFa/TEIP: seleção por ano, extração pelo CEG
│   ├── programacao.py       # Programação diária: dia pelo nome, pré-filtro pyarrow, 48 patamares
│   ├── conjuntos.py         # motor dos conjuntos horários: descrição, formato por período, extração
│   ├── cadastro.py          # Modalidade das usinas: ficha pelo CEG, homônimos e auditoria
│   └── dicionarios.py       # dicionários PDF e JSON: obtenção, SHA-256 e registro dicionarios.csv
└── comum/                   # usados pela etapa e pelas regras comuns
    ├── caminhos.py          # pastas e nomes de arquivo (ARQUIVOS_COLETA, pasta_etapa)
    ├── perfil.py            # leitura e validação do perfil, valores derivados, perfil ativo
    ├── regras.py            # conjuntos e pastas do ONS, download, versões, limiares da validação do perfil
    ├── persistencia.py      # gravação segura (.bak, conteúdo idêntico, conferência, restauração)
    ├── logger.py            # formato do log, LOGGERS_PIPELINE, configurar_nivel_log e exceções
    ├── modelos.py           # RecursoONS, RegistroEnergiaVertida e AuditoriaArquivo
    ├── formatacao.py        # fmt_num, no log da ficha cadastral
    ├── copia_seguranca.py   # comando copia-seguranca
    └── comparacao.py        # comando comparar (spec da Geração do relatório)

tests/
├── conftest.py                       # perfil ativo em cada teste; CSV da EVT e catálogo CKAN simulados
├── fixtures/                         # perfil e brutos sintéticos da usina fictícia (três UG, com homônimos)
├── coleta/
│   ├── test_catalogo.py              # catálogo e suas tentativas, cache pela versão publicada, manifesto, versões
│   ├── test_versoes_anteriores.py    # limite de duas versões, poda registrada, dicionários
│   ├── test_dicionarios.py           # resultados NOVO a NAO_OBTIDO; falhas não interrompem; coleta parada com 2
│   ├── test_evt.py                   # código e nome, Latin-1, valores ilegíveis, consolidação, linhas irregulares
│   ├── test_auditoria_evt.py         # gravação da auditoria da EVT
│   ├── test_indicadores.py           # seleção por ano, CEG, conferência pelo id ONS, falhas
│   ├── test_programacao.py           # datas, homônimos, identificação parcial avisada, INCOMPLETO, falhas
│   ├── test_conjuntos.py             # período, formato, recursos repetidos, parciais, inválidos, irregulares
│   └── test_cadastro.py              # ficha, homônimos, auditoria, republicação, falha de download
├── comum/
│   ├── test_perfil.py                # perfil válido, valores derivados, recusas e mensagem
│   ├── test_pipeline.py              # etapa.json, códigos 2, 3 e 5, Ctrl+C, desatualizada, formato antigo, completo
│   ├── test_copia_seguranca.py       # cópia conferida, duas mais recentes, falha, motivo inválido
│   ├── test_conformidade.py          # nível de log (também em módulo carregado depois), entrada única, persistência
│   ├── test_literais.py              # nenhum valor da São Domingos no código
│   ├── test_persistencia.py          # contrato da gravação segura, inclusive a interrupção
│   ├── test_persistencia_gravadores.py  # gravadores da Coleta e do Tratamento; leitores ignoram .bak
│   └── test_comparacao.py            # comando comparar
└── integracao/
    ├── test_cli.py                   # comandos e opções; códigos 2, 4 e 5; completo; comparar
    └── test_usina_ficticia.py        # cinco etapas da usina fictícia com --sem-portal, sem dados de outra usina
```

## Fluxo de execução

1. `src/__main__.main`: `construir_parser().parse_args` (opção inválida ou ausente: o argparse sai com 2) e `configurar_nivel_log(args.log_level)`.
2. `carregar_perfil(slug)`: lê e valida o perfil; `PerfilInvalido` vira a mensagem na saída de erro e o código 4, sem gravar nada.
3. `pipeline.executar_etapa("coleta", perfil, sem_portal, forcar_download)`: anota `iniciada_em`, define o perfil ativo e importa `src.coleta.etapa.executar_coleta`. Uma exceção vira código 1, com `resumo = {"erro": <mensagem>}`; a interrupção pelo usuário (Ctrl+C) também, com `{"erro": "interrompida pelo usuário"}`.
4. `executar_coleta` cria `data/usinas/<slug>/coleta/` e trata os conjuntos nesta ordem. Em cada um: sincroniza (exceto com `--sem-portal`), extrai dos arquivos locais, grava o extraído e a auditoria e registra o resumo (`_Coleta.registrar`).
   1. EVT: `sincronizar_evt` → `filter_all_raw_files` → `consolidate_records` → `evt_extraido.csv` e `auditoria_evt.csv`. O período é o primeiro e o último `din_instante` consolidado.
   2. Indicadores e taxas: `sincronizar_indicadores` → `extrair_indicadores` → `indicadores_extraido.parquet` e `auditoria_indicadores.csv`.
   3. Programação diária: `sincronizar_programacao` → `extrair_programacao` → `programacao_extraido.parquet` e `auditoria_programacao.csv`.
   4. Disponibilidade, hidrologia e geração: `descricoes(perfil)` → `sincronizar_conjunto` → `extrair_conjunto` → `<conjunto>_extraido.parquet` e `auditoria_<conjunto>.csv`.
   5. Cadastro: `sincronizar_cadastro` → `extrair_cadastro` → `cadastro_ficha.csv` e `auditoria_cadastro.csv`.
   6. Dicionários: `sincronizar_dicionarios` dos dez conjuntos (exceto com `--sem-portal`; uma exceção só gera aviso) → `exportar_registro` → `dicionarios.csv`. Este passo roda também quando um conjunto parou a coleta com 2.
5. Código 2, com parada no conjunto depois de gravar o extraído e a auditoria dele: arquivo com `FALHA` na auditoria (não obtido ou não lido), nenhuma linha da usina na EVT, ou ficha cadastral vazia. Código 1: catálogo inacessível depois das tentativas (`DownloadError`), falha de gravação (`ErroPersistencia`, com o arquivo restaurado), interrupção pelo usuário ou erro inesperado.
6. `executar_etapa` grava o `etapa.json` (`concluida` com 0; `falha` com 1 ou 2), com o tamanho e o SHA-256 de cada arquivo gravado; com `concluida`, marca como `desatualizada` as etapas seguintes que já existirem; mostra no log o resumo e a pasta.

## Decisões técnicas

### D1 — Uma linha de comando, com códigos de saída fixos
- **Decisão**: `python -m src <comando>` (`src/__main__.py`, argparse com subcomandos) é o único ponto de entrada. Os comandos de etapa chamam `pipeline.executar_etapa`, que importa a função da etapa por `FUNCOES_ETAPA` ("módulo:função") só na execução. Os códigos 0 a 6 são constantes de `src/pipeline.py`; uma exceção ou a interrupção pelo usuário (Ctrl+C) na função da etapa vira 1, com o `etapa.json` em `falha`.
- **Motivo**: um só lugar para perfil, pré-requisito, manifesto e código de saída; nenhum outro módulo tem `__main__` ou argparse (`test_ponto_de_entrada_unico`).
- **Alternativas rejeitadas**: um `main()` por módulo com um orquestrador por cima; opções para pular conjuntos ou partes da coleta.

### D2 — Perfil em TOML, validado de uma vez, e perfil ativo
- **Decisão**: `usinas/<slug>/perfil.toml`, lido com `tomllib`. `validar_perfil` acumula todos os problemas antes de recusar (`PerfilInvalido`). Os valores derivados (engolimento máximo, disponibilidade de referência, produtividade nominal, plena carga, limites físicos) são propriedades de `Perfil`, não campos. `executar_etapa` define o perfil ativo durante a etapa (`definir_perfil_ativo`) e o limpa no fim; as Análises e o Relatório o leem com `perfil_ativo()`.
- **Motivo**: o fiscal lê o perfil e comenta a origem de cada valor; sem dependência nova; perfil no git.
- **Alternativas rejeitadas**: YAML (dependência nova), JSON (sem comentários), módulo Python (mistura dado e código), planilha (difícil de versionar e de validar).

### D3 — `etapa.json`, pré-requisito e comando `completo`
- **Decisão**: `executar_etapa` grava o `etapa.json` de forma atômica (`etapa.json.tmp` e `os.replace`), sem `.bak`. A etapa seguinte só roda com a anterior `concluida` e no `versao_formato` atual (`VERSAO_FORMATO`, hoje 1 em todas); manifesto ausente ou ilegível conta como ausente. Uma etapa concluída marca como `desatualizada` as seguintes que já existirem. `executar_completo` roda as cinco com o mesmo perfil e para na primeira que não termina com 0, devolvendo o código dela.
- **Motivo**: não misturar resultados de execuções diferentes, sem comparar conteúdo.

### D4 — Cópia de segurança conferida antes da poda
- **Decisão**: `copia-seguranca` (`src/comum/copia_seguranca.py`) copia `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `usinas/*/perfil.toml`, `README.md` e `requirements.txt` (sem `__pycache__`, `*.pyc` e `.pytest_cache`), confere cada SHA-256 contra a origem, grava `copia.json`, `conftest.py` e `LEIA-ME.txt`, confere a quantidade e os SHA-256 contra o registro e só então exclui as cópias além de duas (`MAXIMO_COPIAS`). Em qualquer falha, apaga a cópia nova e sai com 1.
- **Motivo**: a cópia mais antiga só sai quando existe outra íntegra.

### D5 — Um nível de log para todos os loggers
- **Decisão**: cada módulo usa um logger nomeado criado por `setup_logger` (saída padrão, formato `%(asctime)s [%(levelname)s] %(name)s - %(message)s`, sem arquivo). `configurar_nivel_log` aplica o nível de `--log-level` aos loggers de `LOGGERS_PIPELINE` no início do comando. `setup_logger(nome)`, sem nível, mantém o nível já aplicado e só usa `INFO` em logger ainda sem nível; assim o nível vale também para os módulos importados depois, como o da etapa executada. Os testes conferem que todo `setup_logger` do código usa um nome da lista e que um logger configurado depois da linha de comando mantém o nível.
- **Motivo**: um só nível para todos os módulos da chamada.
- **Alternativas rejeitadas**: logger raiz único (mudaria o formato e duplicaria mensagens).

### D6 — Testes sem rede
- **Decisão**: a camada de rede é simulada (`urllib.request.urlopen` trocado por catálogo e arquivos falsos; `time.sleep` pelas esperas), e a suíte roda com `HTTP_PROXY` e `HTTPS_PROXY` em `http://127.0.0.1:9`, como proteção adicional. O fluxo de ponta a ponta roda com `--sem-portal` sobre brutos sintéticos da usina fictícia, em pastas temporárias (`caminhos.DATA_DIR`, `RAW_DATA_DIR`, `REPORTS_DIR` e `perfil.RAIZ_PROJETO` redirecionados).
- **Motivo**: testes reprodutíveis, rápidos e sem tocar em `data/`.

### D7 — Catálogo CKAN e cache pela versão publicada
- **Decisão**: `package_show?id=<conjunto>`, com 3 tentativas em qualquer erro de rede, de leitura ou de JSON e na resposta de insucesso (`success` falso). Um recurso é aceito pelo formato declarado ou pela extensão da URL; publicação = `last_modified` (ou `metadata_modified`, ou `created`); tamanho = `size`. A cópia local é reaproveitada se o tamanho local e a publicação forem os do manifesto (só o tamanho, sem publicação no catálogo); sem registro, se o tamanho for o publicado (ou o arquivo não for vazio, sem tamanho no catálogo), e fica registrada como `ARQUIVO_EXISTENTE`.
- **Motivo**: o ONS republica arquivos, às vezes com o mesmo tamanho; a data de publicação detecta a revisão.
- **Alternativas rejeitadas**: raspagem do HTML do portal; URLs fixas por ano; conferência só pelo tamanho; baixar tudo a cada execução.

### D8 — Download em streaming, com tentativas e em paralelo
- **Decisão**: `download_resource` lê blocos de 1 MiB para `<arquivo>.part`, que só substitui o arquivo quando completo; 3 tentativas, com espera de 2 s e 4 s e limite de 60 s por tentativa; tamanho diferente do publicado gera aviso. A Programação diária e os conjuntos horários usam 8 downloads simultâneos (`DOWNLOADS_SIMULTANEOS`); os demais, um por vez. Um arquivo não obtido vira `FALHA` na auditoria, e os outros continuam.
- **Motivo**: arquivos de até 200 MB sem pico de memória; centenas de arquivos diários pequenos.
- **Alternativas rejeitadas**: carregar a resposta inteira na memória.

### D9 — Manifesto de versões por pasta
- **Decisão**: um `_manifesto_ons.json` por pasta de conjunto (e por `_dicionarios/`), com uma entrada por arquivo, gravado no fim da sincronização num bloco `finally`, mesmo se ela for interrompida, de forma atômica (`.json.part` e `replace`, chaves ordenadas). A data de obtenção de um conjunto é o maior `registrado_em_utc` do manifesto (`conjuntos.data_obtencao`).
- **Motivo**: registro da versão de cada arquivo, compartilhado por todas as usinas.

### D10 — Versões anteriores: só com conteúdo diferente, no máximo duas
- **Decisão**: depois do download completo, se o SHA-256 da cópia local difere do novo, ela vai para `_versoes_anteriores/<nome>__pub_<AAAAMMDDTHHMMSS><ext>` (publicação registrada) ou `__arq_<data do arquivamento>`, com `_2`, `_3`… se o nome existir. Acima de `MAXIMO_VERSOES_ANTERIORES` (2), as mais antigas são excluídas e registradas em `versoes_excluidas`; a exclusão só atua dentro de `_versoes_anteriores/`.
- **Motivo**: reproduzir um relatório entregue sem acumular cópias; republicação idêntica não gera versão.
- **Alternativas rejeitadas**: conferir só o tamanho; guardar todas as versões; uma pasta única de versões para todos os conjuntos.

### D11 — Dicionários sempre baixados e comparados pelo conteúdo
- **Decisão**: recursos PDF e JSON cujo nome, sem acento, contém "DICIONARIO", baixados com `force=True` para `<pasta do conjunto>/_dicionarios/`. O resultado (`NOVO`, `INALTERADO`, `ALTERADO` com versão preservada como em D10, ou `FALHA`) vai para o manifesto da pasta, que tem também a entrada `_consulta`. `dicionarios.csv` é montado só dos manifestos (`NAO_PUBLICADO`, `NAO_OBTIDO`). O passo roda no fim da coleta, também quando um conjunto a parou com 2; falha nele não muda o código de saída.
- **Motivo**: o catálogo não informa tamanho nem data dos dicionários.
- **Alternativas rejeitadas**: baixar só o que falta (não detecta mudança); pasta central de dicionários; interromper a coleta por um dicionário.

### D12 — Identificador de extração e campo de conferência
- **Decisão**: a linha só é extraída se o identificador e a conferência do perfil conferem; as que conferem só em parte são contadas na auditoria e avisadas no log, com o arquivo. Textos sem acento, sem espaços nas pontas e em maiúsculas; números como número (`conjuntos._corresponde`, usado nos indicadores e nos conjuntos horários; a seção 5.2 do [data-model](data-model.md) traz a comparação de cada conjunto). O nome do agente nunca entra. Exceções: taxas e parâmetros da TEIFa e da TEIP só pelo CEG; no cadastro, a ficha é localizada pelo CEG, e id ONS e estado só são contados.
- **Motivo**: homônimos com o mesmo nome em outros estados e tipos de usina; troca de agente na mesma usina.
- **Alternativas rejeitadas**: chave textual com o nome do agente (quebra com a troca de agente); só o código (uma troca de código passaria despercebida).
- **Limitações conhecidas**: na EVT, o código é comparado como texto e o pré-teste do nome usa o texto ainda com acento; na programação, código e estado são comparados só sem os espaços das pontas; o filtro do Parquet da geração usa os valores como publicados; num conjunto horário sem a coluna de conferência, as linhas contam como "só identificador", sem `FALHA`.

### D13 — Formato e período de cada conjunto
- **Decisão**:
  - EVT: todos os CSV publicados, lidos em ordem de nome (anuais antes dos mensais);
  - indicadores e taxas: CSV com o ano do nome dentro dos anos do período, e os arquivos sem ano;
  - Programação diária: só o Parquet, um por dia; o dia vem do nome, e a data interna (`AAAA-MM-DD` ou `DD/MM/AAAA`) só é conferida;
  - disponibilidade, hidrologia e geração: por ano ou mês do nome sobreposto ao período, o Parquet quando publicado e senão o CSV; entre recursos repetidos, o que tem publicação e, em empate, o maior;
  - cadastro: o CSV único.
- **Motivo**: em CSV, a programação diária do período somaria cerca de 26 GB (o Parquet, cerca de 106 MB); o Parquet da disponibilidade falta em parte dos meses (na São Domingos, 53 meses vêm do CSV).
- **Alternativas rejeitadas**: dia da programação pela coluna interna (a leitura automática inverteu dia e mês); disponibilidade só em Parquet (perde meses) ou só em CSV (cerca de 1 GB a mais, sem ganho).
- **Limitação conhecida**: só os conjuntos horários escolhem entre recursos repetidos no catálogo; na EVT, nos indicadores e na programação, cada repetição é baixada (na programação, em paralelo e com o mesmo `<arquivo>.part`).

### D14 — Leitura em streaming na EVT e com filtros nos demais
- **Decisão**: a EVT é lida linha a linha com `csv.reader`, com um pré-teste pela última palavra do nome antes da normalização. Os CSV dos demais conjuntos são lidos pelo pandas como texto, só com as colunas necessárias, e os Parquet com projeção de colunas. Na Programação diária, `pyarrow.compute` mantém só as linhas com o código ou o estado da usina; na Geração por usina, o filtro do Parquet mantém as linhas com o id ONS ou o CEG.
- **Motivo**: cerca de 15 milhões de linhas da EVT com memória constante; 134 milhões de linhas da programação sem montar a tabela inteira.
- **Alternativas rejeitadas**: ler cada CSV da EVT inteiro com pandas; filtrar fora do Python.

### D15 — Codificação e linhas irregulares
- **Decisão**: CSV com `;`, em UTF-8 (`utf-8-sig` nos lidos pelo pandas) e, com erro de decodificação, relido inteiro em Latin-1. Colunas localizadas pelo nome. Linhas não vazias com número de campos diferente do cabeçalho não são extraídas: são contadas e avisadas no log com o arquivo, a quantidade e as cinco primeiras (número da linha no arquivo, com o cabeçalho na linha 1).
- **Motivo**: uma linha curta não entra com campos vazios, e uma longa não perde o excedente em silêncio.
- **Alternativas rejeitadas**: truncar as linhas longas (valores deslocados).
- **Limitação conhecida**: o CSV vazio da EVT fica `FALHA` sem o motivo na auditoria.

### D16 — Valores como publicados
- **Decisão**: a EVT e a programação aceitam vírgula decimal e guardam o número sem arredondar (na EVT, na representação do Python, com ponto). Nos conjuntos horários, cada valor passa por `pd.to_numeric` (ponto decimal). Em todos esses conjuntos, vazio fica ausente, e texto não numérico fica ausente e conta em `valores_invalidos` (na EVT, `null`, `none` e `nan` valem como vazio; nos horários, a linha ganha `_nao_numerico`). Indicadores, taxas e cadastro ficam como texto sem espaços nas pontas (só a potência autorizada da ficha vira número).
- **Motivo**: convenção de hora, duplicatas entre arquivos, recorte e sinalizações são do [Tratamento de dados](../002-tratamento-dados/spec.md).
- **Limitação conhecida**: nos conjuntos horários e na potência autorizada da ficha, a vírgula decimal não é aceita: o valor fica ausente (e, nos horários, conta como inválido).

### D17 — Consolidação só na EVT
- **Decisão**: `consolidate_records` deixa um registro por (`cod_usina`, `din_instante`), o do arquivo lido por último; conta as duplicatas idênticas e as conflitantes (estas avisadas com os dois arquivos); descarta registro sem instante; ordena por instante.
- **Motivo**: a EVT define o período dos demais conjuntos; o código na chave impede que usinas diferentes no mesmo instante se anulem.

### D18 — `--sem-portal`, `--forcar-download` e parada na falha
- **Decisão**: com `--sem-portal`, nenhuma sincronização roda e `--forcar-download` é ignorado; a extração usa as mesmas regras de período e formato sobre os arquivos locais, e o registro dos dicionários vem dos manifestos. Com `--forcar-download`, todo arquivo de dados é baixado de novo. Um conjunto com `FALHA` encerra a coleta com 2 depois de gravar o extraído e a auditoria dele; os quatro conjuntos de indicadores formam um bloco.
- **Motivo**: reproduzir o relatório sem rede e não seguir com um conjunto incompleto.

## Complexity Tracking

Sem desvios da constituição.
