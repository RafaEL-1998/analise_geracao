# Implementation Plan: Coleta de dados

**Spec**: [spec.md](spec.md) · **Etapa**: 1 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-23

## Summary

A Coleta de dados (`src/coleta/`) atende qualquer usina que os dados abertos do ONS cobrem: UHE, PCH, CGH, UTE, UTN, EOL e UFV. Um registro declarativo (`registro.py`) diz que conjunto do ONS serve a que tipo de usina e como identificar a usina nele; a Coleta percorre o registro filtrado pelo tipo e pela `[cobertura]` do perfil. Para esses conjuntos, ela consulta o catálogo CKAN do ONS, baixa em streaming só os arquivos novos ou republicados (cache pelo manifesto de cada pasta, até duas versões anteriores por arquivo) e obtém sempre os dicionários de dados. A série de referência do tipo vem primeiro e define o período: a EVT, na hidrelétrica com EVT; senão a Geração por usina, da usina ou do conjunto, ou a restrição com detalhe da usina; fora da EVT, o período é dividido em trechos. Depois a Coleta extrai dos arquivos locais as linhas da usina, por um identificador conferido por um segundo campo, com uma linha de auditoria por arquivo, e para no primeiro conjunto com falha. Os resultados vão para `data/usinas/<slug>/coleta/`, no formato 2: as etapas seguintes leem as datas de obtenção e o dicionário da EVT da pasta da Coleta, nunca `data/raw/`. A Coleta também monta o catálogo de usinas (`catalogo_usinas.py`, comando `usinas`) e o rascunho do perfil (`perfil_rascunho.py`, comando `perfil`). As regras comuns às cinco etapas (linha de comando, perfil por tipo, `etapa.json`, pré-requisitos, `completo`, cópia de segurança e log) estão em `src/__main__.py`, `src/pipeline.py` e `src/comum/`.

## Technical Context

**Language/Version**: Python 3.14.6 no `venv` do projeto; mínimo 3.11, porque o perfil é lido com `tomllib`.

**Primary Dependencies**:
- `pandas`: tabelas e leitura de CSV (como texto) e de Parquet;
- `pyarrow`: projeção de colunas e filtros na leitura de Parquet, filtro da Programação diária (`pyarrow.compute`) e esquema dos arquivos do catálogo;
- biblioteca padrão: `urllib.request` (catálogo e downloads), `csv` (varredura da EVT), `concurrent.futures` (downloads simultâneos), `hashlib`, `json`, `tomllib` (perfil, perfis achados pelo CEG e conferência do rascunho), `argparse`, `unicodedata` e `shutil`;
- `openpyxl` é carregado por `src/comum/persistencia.py`, mas a etapa não grava planilha; `pytest` nos testes. Nenhuma dependência nova para os tipos de usina.

**Storage**: arquivos.
- `data/raw/`, compartilhado por todas as usinas e pelo catálogo: arquivos do ONS com o nome da URL, `_manifesto_ons.json` em cada pasta, `_versoes_anteriores/` e `_dicionarios/` (com manifesto próprio); uma pasta por pacote do registro (21 pacotes); Parquet sempre que publicado. Cerca de 5,8 GB em 23/10/2026.
- `data/catalogo/`: `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`, gravados por `gravar_csv` e `gravar_bytes` sem `.bak`, numa pasta temporária (`.gravando`) conferida antes da troca (`os.replace`).
- `data/usinas/<slug>/coleta/`: os extraídos, as auditorias, `cadastro_ficha.csv`, `dicionarios.csv`, `datas_obtencao.csv`, `etapa.json` e, conforme o tipo e a cobertura, `dicionario_evt.json`, `geracao_complemento.parquet`, `trechos.csv`, `capacidade_ficha.csv`, `composicao_conjunto.csv`, `capacidade_membros.csv` e `tipo_publicado.csv` ([data-model](data-model.md), seção 2.2); todos, menos o `etapa.json`, gravados por `src/comum/persistencia.py` (`gravar_linhas_csv` na EVT e na auditoria dela, `gravar_bytes` no dicionário da EVT, `gravar_csv` e `gravar_parquet` nos demais), com `.bak` da versão anterior, conteúdo idêntico não regravado, conferência no disco e restauração em falha ou interrupção (código 1), como descrito no [plano do Tratamento de dados](../002-tratamento-dados/plan.md) (D13);
- `usinas/<slug>/perfil.toml`: o rascunho, gravado por `gravar_bytes` sem `.bak`, só quando o perfil não existe;
- CSV com `;`, UTF-8 sem BOM e fim de linha do sistema (CRLF no Windows); datas `AAAA-MM-DD HH:MM:SS`;
- cópias de segurança em `_backup_<AAAA-MM-DD>_<motivo>/`, na raiz do projeto, com `relatorios_referencia/`.

**Testing**: pytest sem rede (D6); 840 testes na suíte em 23/10/2026, entre eles:
- `tests/coleta/`: catálogo CKAN, cache, versões, dicionários, extração e auditoria de cada conjunto, correções P1 a P5, registro, catálogo de usinas, rascunho do perfil, série de referência e trechos, conjuntos das térmicas e das eólicas e solares, usina em conjunto e datas de obtenção;
- `tests/comum/`: perfil por tipo, `etapa.json` e pré-requisitos, interrupção, gravação segura, cópia de segurança com as referências, conformidade e ausência de valores de usina no código, inclusive os identificadores das usinas piloto;
- `tests/integracao/`: linha de comando, as cinco etapas da usina fictícia, uma usina fictícia de cada tipo de ponta a ponta (D30) e as etapas 2 a 5 com `data/raw/` vazio (D29).

**Target Platform**: Windows 11, execução local no `venv`, PowerShell.

**Project Type**: projeto único; pipeline de linha de comando (`python -m src`).

**Performance Goals**: execuções reais, registradas no `etapa.json` ou no log:
- São Domingos com `--sem-portal`: etapa completa em 4 min 20 s; leitura dos 42 arquivos da EVT (14.993.512 linhas) em cerca de 45 s; metas da SC-012: menos de 10 min e menos de 3 min;
- William Arjona com o portal: Coleta em 4 min 59 s, com a varredura de toda a Geração por usina e da programação desde 2021; meta do fluxo completo de uma usina piloto, com os dados locais: 15 min;
- catálogo de usinas: `python -m src usinas --estado MS` com o portal em 112 s (19/10/2026); meta do catálogo do Brasil sem portal: 3 min;
- rascunho do perfil: 1,1 s (meta da SC-016: 1 min);
- com o portal, soma-se o tempo de rede; sem novidade, só os dicionários são baixados.

**Constraints**:
- só a Coleta acessa a rede (comandos `coleta`, `completo` e `usinas`): só `src/coleta/catalogo.py` usa `urllib`;
- nenhum arquivo bruto é editado; com `--sem-portal`, nada é criado, alterado ou excluído em `data/raw/`;
- as etapas 2 a 5 não leem `data/raw/` (D29);
- no máximo duas versões anteriores por arquivo; brutos, manifestos, dicionários e catálogo sem `.bak`;
- leitura sem recursão nas pastas brutas: `_versoes_anteriores/` e `_dicionarios/` nunca são lidos como dados;
- coluna nova só em arquivo novo: os arquivos da UHE mantêm as colunas (D26);
- nenhum valor de usina no código, inclusive os identificadores e os CEG das usinas piloto (`tests/comum/test_literais.py`).

**Scale/Scope**: São Domingos, período de 28/08/2018 00h a 28/09/2026 23h; `data/raw/` com cerca de 4,1 GB nos dez conjuntos da UHE.

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

Demais tipos:
- registro com 16 entradas e 21 pacotes do ONS;
- cadastro do ONS com 6.024 linhas em 19/10/2026, 171 em MS;
- `planejamento.csv` com 220 códigos (20/10/2026); Programação diária com 733 arquivos diários desde 01/10/2024 (109 MB, 22/10/2026); Geração por usina com 80 arquivos, de 2000 a 2026 (0,73 GB);
- usinas piloto, pela Coleta de cada uma:

| Usina | Tipo | Série de referência | Período | Trechos |
|---|---|---|---|---|
| São Domingos | UHE | EVT (`cod_usina` 153) | de 28/08/2018 a 19/10/2026 (Coleta de 22/10/2026) | — |
| William Arjona | UTE | Geração por usina (id ONS MSUTWI) | de 10/07/2021 a 18/10/2026 | 3 |
| Praia Formosa | EOL | Geração por usina (id ONS CEUFM), 80 arquivos | de 01/07/2009 a 19/10/2026 | 1 |
| Seriemas 1 | UFV | restrição com detalhe (id ONS MSSRI1), 31 arquivos | de 22/08/2026 a 19/10/2026 23h30 | 1 |
| Bandeirante | PCH | Geração por usina do conjunto (CJU_MSCAO), recortada pela composição | de 22/08/2019 a 20/10/2026 | 3 |

## Constitution Check

| Princípio / requisito da constituição 3.1.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | a spec descreve a etapa inteira, para todos os tipos, com a tabela de aplicabilidade por tipo, e as regras comuns; só a Coleta acessa o portal, e o catálogo de usinas é dela; o `perfil` só lê o catálogo; a partir do Tratamento, `src/pipeline.py` recusa a etapa sem a anterior concluída (código 5); as etapas 2 a 5 não leem `data/raw/` (D29) |
| II. Relatório fiel aos dados | cumpre | nenhum valor de usina no código; toda linha extraída traz o arquivo de origem; `datas_obtencao.csv` guarda as datas de publicação e de obtenção usadas nas legendas |
| III. Uma usina por execução, definida pelo perfil | cumpre | perfil por tipo, validado antes de qualquer ação, com todos os problemas (código 4); rascunho recusado até ser conferido; regras gerais em `src/comum/regras.py`; homônimos excluídos pelos códigos e contados; séries de outras usinas só como contexto identificado (`restricao_membros_extraido.parquet`, `capacidade_membros.csv`); catálogo do cadastro e dos conjuntos do ONS |
| IV. Coleta completa e rastreável | cumpre | só o portal do ONS; a série de referência é varrida em todos os arquivos publicados, e os demais conjuntos, pelo período; cache pelo manifesto; versões anteriores; dicionários a cada consulta ao portal, também quando a coleta para com 2; identificador com conferência, inclusive nos conjuntos novos (D27); linhas parciais, linhas irregulares e valores inválidos contados na auditoria. As limitações da primeira versão foram corrigidas (D28); fica só a comparação do código da EVT como texto (D12) |
| V. Tratamento sem descarte | não se aplica | as sinalizações são do Tratamento; a coleta entrega os valores como publicados, com a marca `_nao_numerico` nos conjuntos do motor comum |
| VI. Conferência entre fontes | não se aplica | a coleta entrega a ficha cadastral, as contagens e as séries que a Conferência compara, inclusive as das outras usinas do conjunto |
| VII. Relatório padronizado | não se aplica | a coleta fornece as datas, as auditorias e o registro dos dicionários citados nas legendas e notas |
| VIII. Granularidade declarada | cumpre | o nível (`usina` ou `conjunto`) vem da cobertura do perfil e fica em cada hora (`geracao_complemento.parquet`) e nas linhas do fator de capacidade e da razão da restrição; trechos de composição; período da usina em conjunto recortado pela composição; nada é dividido entre usinas |
| IX. Relatórios aprovados protegidos | cumpre | `copia-seguranca` leva `relatorios_referencia/` e a confere pelos SHA-256; a Coleta das referências é congelada e comparada com a refeita (spec da Geração do relatório) |
| RT 1. Python, `venv` e dependências usadas | cumpre | `requirements.txt` conferido contra os imports (`test_requirements_corresponde_aos_imports`); nada em script de shell |
| RT 2. Windows e PowerShell | cumpre | caminhos com `pathlib`; exemplos em PowerShell |
| RT 3. Gravação segura | cumpre | todo arquivo da usina passa por `src/comum/persistencia.py` (`test_etapas_gravam_dados_so_pela_persistencia`); catálogo sem `.bak`, gravado numa pasta temporária conferida; brutos, manifestos e dicionários sem `.bak` |
| RT 4. Versões dos brutos | cumpre | `MAXIMO_VERSOES_ANTERIORES = 2`, também nos conjuntos novos e no catálogo; a poda é registrada em `versoes_excluidas` |
| RT 5. Cópias de segurança do projeto | cumpre | `copia-seguranca` confere a cópia nova, com as referências, antes de excluir a mais antiga; ficam duas |
| RT 6. Pastas | cumpre | `src/comum/caminhos.py`, com `data/catalogo/`, `reports/carteiras/<nome>/` e `relatorios_referencia/<slug>/`; `carteiras` reservado como slug |
| RT 7. Log | cumpre | formato e saída padrão comuns; `--log-level` aplicado aos loggers de `LOGGERS_PIPELINE` e mantido nos módulos carregados depois (D5); o catálogo e o rascunho usam o logger `coleta` |
| Qualidade 1. Testes | cumpre | sem rede, com dados sintéticos e uma usina fictícia de cada tipo (D30) |
| Qualidade 2 e 3. Entrega e recuperação | cumpre | SC-014 conferida na execução real; `comparar --todas --coleta` com as referências; `.bak`, cópias de segurança e git |

## Project Structure

### Documentation (this feature)

```text
specs/001-coleta-dados/
├── spec.md                  # requisitos da etapa, regras comuns às cinco etapas e aplicabilidade por tipo
├── plan.md                  # este arquivo
├── data-model.md            # entradas, saídas, catálogo, registro, série de referência, perfil e etapa.json
├── contracts/
│   ├── cli-coleta.md        # linha de comando, códigos de saída e regras comuns
│   ├── cli-usinas.md        # comando usinas (catálogo de usinas)
│   ├── cli-perfil.md        # comando perfil (rascunho do perfil)
│   └── perfil-usina.md      # contrato do perfil da usina, para todos os tipos
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── __main__.py              # linha de comando única (argparse): etapas, usinas, perfil, carteira, referencia, copia-seguranca e comparar; lê o perfil (código 4) e despacha
├── pipeline.py              # ordem das etapas, VERSAO_FORMATO, etapa.json, pré-requisito (código 5), desatualizada, completo
├── coleta/
│   ├── etapa.py             # executar_coleta: conjuntos pelo registro e pela cobertura, série de referência primeiro, cadastrais, membros do conjunto, trechos, dicionários, formato 2 e resumo
│   ├── registro.py          # registro dos conjuntos (EntradaRegistro, REGISTRO, CONJUNTOS_PIPELINE), Regra, DescricaoConjunto, normalizar_texto, conjuntos_da_usina e descrições com o perfil
│   ├── serie_referencia.py  # escolha da série de referência, varredura, período, recorte pela composição, complemento horário, trechos e tipo publicado
│   ├── catalogo.py          # catálogo CKAN, recurso preferido entre repetidos, download com tentativas (.part por recurso), manifesto, versões anteriores e poda
│   ├── evt.py               # EVT: sincronização, varredura com csv.reader, consolidação e auditoria
│   ├── indicadores.py       # indicadores por UG e taxas TEIFa/TEIP: seleção por ano, extração pelo CEG
│   ├── programacao.py       # Programação diária: dia pelo nome, pré-filtro pyarrow, um ou mais códigos, 48 patamares
│   ├── conjuntos.py         # motor comum (horários, semi-horários e semanais): formato por período, leitura numérica, extração e auditoria
│   ├── cadastro.py          # Modalidade das usinas: ficha pelo CEG, homônimos e auditoria
│   ├── dicionarios.py       # dicionários PDF e JSON dos conjuntos da usina: obtenção, SHA-256 e registro dicionarios.csv
│   ├── catalogo_usinas.py   # comando usinas: cadastrais, cobertura, códigos de programação e de planejamento, agregados e listagem
│   └── perfil_rascunho.py   # comando perfil: rascunho a partir do catálogo e diferenças com o perfil existente
└── comum/                   # usados pela etapa e pelas regras comuns
    ├── caminhos.py          # pastas e nomes de arquivo (ARQUIVOS_COLETA, ARQUIVOS_CATALOGO, pasta_etapa, pasta_catalogo, espaco_isolado)
    ├── perfil.py            # leitura e validação do perfil por tipo, valores derivados, perfil ativo
    ├── perfil_campos.py     # exigência de cada campo do perfil por grupo de tipos (O, C, opcional, —)
    ├── regras.py            # tipos, modalidades, subsistemas e coberturas; pacotes e pastas do ONS; download, versões; limiares
    ├── persistencia.py      # gravação segura (.bak, conteúdo idêntico, conferência, restauração)
    ├── logger.py            # formato do log, LOGGERS_PIPELINE, configurar_nivel_log e exceções
    ├── modelos.py           # RecursoONS, RegistroEnergiaVertida e AuditoriaArquivo
    ├── formatacao.py        # fmt_num e fmt_data, no log da ficha, no catálogo e no rascunho
    ├── periodos.py          # agrupamento de horas consecutivas (Conferência e Análises)
    ├── copia_seguranca.py   # comando copia-seguranca, com relatorios_referencia/
    ├── referencias.py       # comando referencia e espaço isolado do comparar --todas (spec da Geração do relatório)
    └── comparacao.py        # comando comparar (spec da Geração do relatório)

tests/
├── conftest.py                       # perfil ativo em cada teste; CSV da EVT e catálogo CKAN simulados
├── fixtures/
│   ├── usina_ficticia/               # perfil e brutos sintéticos da usina fictícia (três UG, com homônimos)
│   ├── usinas_ficticias/<tipo>/      # perfis das sete usinas fictícias (uhe, pch, cgh, ute, utn, eol, ufv)
│   ├── brutos_ficticios.py           # brutos sintéticos de todos os conjuntos do registro
│   ├── brutos_catalogo.py            # cadastro e conjuntos de um Brasil fictício (GO e MT), para o catálogo
│   └── sem_evt.py                    # etapas das usinas sem EVT numa pasta temporária
├── coleta/
│   ├── test_catalogo.py              # catálogo e suas tentativas, cache pela versão publicada, manifesto, versões
│   ├── test_versoes_anteriores.py    # limite de duas versões, poda registrada, dicionários
│   ├── test_dicionarios.py           # resultados NOVO a NAO_OBTIDO; só os conjuntos da usina; falhas não interrompem
│   ├── test_evt.py                   # código e nome, Latin-1, valores ilegíveis, consolidação, linhas irregulares
│   ├── test_auditoria_evt.py         # gravação da auditoria da EVT
│   ├── test_indicadores.py           # seleção por ano, CEG, conferência pelo id ONS, falhas
│   ├── test_programacao.py           # datas, homônimos, identificação parcial, vários códigos, INCOMPLETO, falhas
│   ├── test_conjuntos.py             # período, formato, recursos repetidos, parciais, inválidos, irregulares
│   ├── test_cadastro.py              # ficha, homônimos, auditoria, republicação, falha de download
│   ├── test_correcoes_p1_p5.py       # correções P1 a P5 (D28)
│   ├── test_registro.py              # registro, conjuntos por tipo e cobertura, dicionários por usina
│   ├── test_datas_obtencao.py        # datas_obtencao.csv e dicionario_evt.json (formato 2)
│   ├── test_catalogo_usinas.py       # catálogo de usinas: tipo, cobertura, códigos, agregados, gravação
│   ├── test_perfil_rascunho.py       # rascunho, recusas, diferenças com o perfil existente
│   ├── test_serie_referencia.py      # escolha da série, varredura, período, trechos, recorte pela composição
│   ├── test_coleta_sem_evt.py        # coleta da UTE e da PCH fictícias
│   ├── test_coleta_conjunto.py       # usina em conjunto: fora da composição, unidades das usinas do conjunto
│   ├── test_conjuntos_termicos.py    # despacho, CVU e CMO
│   └── test_conjuntos_renovaveis.py  # fator de capacidade, restrições, colunas ausentes, membros
├── comum/
│   ├── test_perfil.py                # perfil por tipo, valores derivados, recusas e mensagem
│   ├── test_pipeline.py              # etapa.json, códigos 2, 3 e 5, Ctrl+C, desatualizada, formato antigo, completo
│   ├── test_copia_seguranca.py       # cópia conferida, com as referências; duas mais recentes; falha; motivo inválido
│   ├── test_conformidade.py          # nível de log, entrada única, persistência (também no catálogo)
│   ├── test_literais.py              # nenhum valor das usinas piloto no código
│   ├── test_persistencia.py          # contrato da gravação segura, inclusive a interrupção
│   ├── test_persistencia_gravadores.py  # gravadores da Coleta e do Tratamento; leitores ignoram .bak
│   ├── test_referencias.py           # referencia e comparar --todas (spec da Geração do relatório)
│   └── test_comparacao.py            # comando comparar
└── integracao/
    ├── test_cli.py                   # comandos e opções; códigos 2, 4 e 5; completo; comparar
    ├── test_usina_ficticia.py        # cinco etapas da usina fictícia com --sem-portal, sem dados de outra usina
    ├── test_usinas_ficticias.py      # uma usina fictícia de cada tipo, de ponta a ponta
    └── test_sem_raw.py               # etapas 2 a 5 com data/raw/ vazio
```

## Fluxo de execução

1. `src/__main__.main`: `construir_parser().parse_args` (opção inválida ou ausente: o argparse sai com 2) e `configurar_nivel_log(args.log_level)`. Os comandos `usinas` e `perfil` chamam `executar_usinas` e `executar_perfil`, que devolvem o código sem ler perfil nem gravar `etapa.json`.
2. `carregar_perfil(slug)`: lê e valida o perfil pela tabela de campos por tipo; `PerfilInvalido` vira a mensagem na saída de erro e o código 4, sem gravar nada.
3. `pipeline.executar_etapa("coleta", perfil, sem_portal, forcar_download)`: anota `iniciada_em`, define o perfil ativo e importa `src.coleta.etapa.executar_coleta`. Uma exceção vira código 1, com `resumo = {"erro": <mensagem>}`; a interrupção pelo usuário (Ctrl+C) também, com `{"erro": "interrompida pelo usuário"}`.
4. `executar_coleta`:
   1. `registro.conjuntos_da_usina(perfil)`: os conjuntos do tipo e da cobertura, na ordem do registro; `serie_referencia.escolher(perfil)`: a série de referência (sem nenhuma possível, código 1, "Coleta recusada"); o resumo começa com o tipo, a modalidade e os conjuntos não aplicáveis. Cria `data/usinas/<slug>/coleta/`.
   2. Na hidrelétrica com EVT: `sincronizar_evt` → `filter_all_raw_files` → `consolidate_records` → `evt_extraido.csv` e `auditoria_evt.csv`. O período é o primeiro e o último `din_instante` consolidado.
   3. Fora dela: na usina em conjunto sem série própria, a Composição dos conjuntos primeiro; depois `_coletar_referencia`: `sincronizar_conjunto` de todos os arquivos da série, `extrair_referencia`, o recorte pela composição, o período, `geracao_extraido.parquet` (ou `restricao_detalhe_extraido.parquet`), a auditoria, `geracao_complemento.parquet` e as linhas próprias sem valor.
   4. Os demais conjuntos, na ordem do registro, cada um sincronizado (exceto com `--sem-portal`), extraído dos arquivos locais, gravado com a auditoria e registrado no resumo (`_Coleta.registrar`): indicadores e taxas; Programação diária; os conjuntos do motor comum (`descricoes(perfil)` → `sincronizar_conjunto` → `extrair_conjunto`); o cadastro (`sincronizar_cadastro` → `extrair_cadastro`); a Composição e a Capacidade (`sincronizar_cadastral` → `ler_cadastral`, com `capacidade_membros.csv` na usina em conjunto).
   5. Sem falha: a restrição com detalhe das outras usinas do conjunto (`_coletar_membros`), `trechos.csv` e `tipo_publicado.csv` (`_gravar_trechos`).
   6. Dicionários: `sincronizar_dicionarios` dos conjuntos da usina (exceto com `--sem-portal`; uma exceção só gera aviso) → `exportar_registro` → `dicionarios.csv`. Depois, `datas_obtencao.csv` e `dicionario_evt.json` (`_gravar_formato_2`). Os dois passos rodam também quando um conjunto parou a coleta com 2.
5. Código 2, com parada no conjunto depois de gravar o extraído e a auditoria dele: arquivo com `FALHA` na auditoria (não obtido ou não lido), nenhuma linha da usina na EVT, série de referência sem hora com valor, usina fora da composição do conjunto declarado, cadastral não obtido ou ficha cadastral vazia. Código 1: catálogo inacessível depois das tentativas (`DownloadError`), usina sem série de referência na cobertura, falha de gravação (`ErroPersistencia`, com o arquivo restaurado), interrupção pelo usuário ou erro inesperado.
6. `executar_etapa` grava o `etapa.json` (`concluida` com 0; `falha` com 1 ou 2), com o tamanho e o SHA-256 de cada arquivo gravado; com `concluida`, marca como `desatualizada` as etapas seguintes que já existirem; mostra no log o resumo e a pasta.

## Decisões técnicas

### D1 — Uma linha de comando, com códigos de saída fixos
- **Decisão**: `python -m src <comando>` (`src/__main__.py`, argparse com subcomandos) é o único ponto de entrada. Os comandos de etapa chamam `pipeline.executar_etapa`, que importa a função da etapa por `FUNCOES_ETAPA` ("módulo:função") só na execução. Os comandos sem etapa (`usinas`, `perfil`, `carteira`, `referencia`, `comparar`, `copia-seguranca`) importam o módulo deles só na execução e devolvem o código. Os códigos 0 a 6 são constantes de `src/pipeline.py`; uma exceção ou a interrupção pelo usuário (Ctrl+C) na função da etapa vira 1, com o `etapa.json` em `falha`.
- **Motivo**: um só lugar para perfil, pré-requisito, manifesto e código de saída; nenhum outro módulo tem `__main__` ou argparse (`test_ponto_de_entrada_unico`).
- **Alternativas rejeitadas**: um `main()` por módulo com um orquestrador por cima; opções para pular conjuntos ou partes da coleta.

### D2 — Perfil em TOML, validado de uma vez, e perfil ativo
- **Decisão**: `usinas/<slug>/perfil.toml`, lido com `tomllib`. `validar_perfil` acumula todos os problemas antes de recusar (`PerfilInvalido`). Os valores derivados (engolimento máximo, disponibilidade de referência, produtividade nominal, plena carga, limites físicos, potência de cada unidade, códigos de planejamento vigentes) são propriedades de `Perfil`, não campos. `executar_etapa` define o perfil ativo durante a etapa (`definir_perfil_ativo`) e o limpa no fim; as Análises e o Relatório o leem com `perfil_ativo()`. A exigência de cada campo por tipo está na D22.
- **Motivo**: o fiscal lê o perfil e comenta a origem de cada valor; sem dependência nova; perfil no git.
- **Alternativas rejeitadas**: YAML (dependência nova), JSON (sem comentários), módulo Python (mistura dado e código), planilha (difícil de versionar e de validar).

### D3 — `etapa.json`, pré-requisito e comando `completo`
- **Decisão**: `executar_etapa` grava o `etapa.json` de forma atômica (`etapa.json.tmp` e `os.replace`), sem `.bak`. A etapa seguinte só roda com a anterior `concluida` e no `versao_formato` atual (`VERSAO_FORMATO`: Coleta 2, Tratamento 2, Conferência 2, Análises 3, Relatório 1); manifesto ausente ou ilegível conta como ausente. Uma etapa concluída marca como `desatualizada` as seguintes que já existirem. `executar_completo` roda as cinco com o mesmo perfil e para na primeira que não termina com 0, devolvendo o código dela.
- **Motivo**: não misturar resultados de execuções diferentes, sem comparar conteúdo.

### D4 — Cópia de segurança conferida antes da poda
- **Decisão**: `copia-seguranca` (`src/comum/copia_seguranca.py`) copia `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `usinas/*/perfil.toml`, `README.md` e `requirements.txt` (sem `__pycache__`, `*.pyc` e `.pytest_cache`) e `relatorios_referencia/` inteira (sem as pastas temporárias `.gravando_*` e `.anterior_*` do comando `referencia`), confere cada SHA-256 contra a origem e cada referência contra o `referencia.json` dela (`referencias.conferir_referencia`), grava `copia.json`, `conftest.py` e `LEIA-ME.txt` (com as referências levadas), confere a quantidade e os SHA-256 contra o registro e só então exclui as cópias além de duas (`MAXIMO_COPIAS`). Em qualquer falha, apaga a cópia nova e sai com 1.
- **Motivo**: a cópia mais antiga só sai quando existe outra íntegra; o princípio IX pede as referências junto às cópias.

### D5 — Um nível de log para todos os loggers
- **Decisão**: cada módulo usa um logger nomeado criado por `setup_logger` (saída padrão, formato `%(asctime)s [%(levelname)s] %(name)s - %(message)s`, sem arquivo). `configurar_nivel_log` aplica o nível de `--log-level` aos loggers de `LOGGERS_PIPELINE` no início do comando. `setup_logger(nome)`, sem nível, mantém o nível já aplicado e só usa `INFO` em logger ainda sem nível; assim o nível vale também para os módulos importados depois, como o da etapa executada. Os testes conferem que todo `setup_logger` do código usa um nome da lista e que um logger configurado depois da linha de comando mantém o nível.
- **Motivo**: um só nível para todos os módulos da chamada.
- **Alternativas rejeitadas**: logger raiz único (mudaria o formato e duplicaria mensagens).

### D6 — Testes sem rede
- **Decisão**: a camada de rede é simulada (`urllib.request.urlopen` trocado por catálogo e arquivos falsos; `time.sleep` pelas esperas), e a suíte roda com `HTTP_PROXY` e `HTTPS_PROXY` em `http://127.0.0.1:9`, como proteção adicional. O fluxo de ponta a ponta roda com `--sem-portal` sobre brutos sintéticos das usinas fictícias, em pastas temporárias (`caminhos.DATA_DIR`, `RAW_DATA_DIR`, `REPORTS_DIR` e `perfil.RAIZ_PROJETO` redirecionados).
- **Motivo**: testes reprodutíveis, rápidos e sem tocar em `data/`.

### D7 — Catálogo CKAN e cache pela versão publicada
- **Decisão**: `package_show?id=<conjunto>`, com 3 tentativas em qualquer erro de rede, de leitura ou de JSON e na resposta de insucesso (`success` falso). Um recurso é aceito pelo formato declarado ou pela extensão da URL; publicação = `last_modified` (ou `metadata_modified`, ou `created`); tamanho = `size`. A cópia local é reaproveitada se o tamanho local e a publicação forem os do manifesto (só o tamanho, sem publicação no catálogo); sem registro, se o tamanho for o publicado (ou o arquivo não for vazio, sem tamanho no catálogo), e fica registrada como `ARQUIVO_EXISTENTE`.
- **Motivo**: o ONS republica arquivos, às vezes com o mesmo tamanho; a data de publicação detecta a revisão.
- **Alternativas rejeitadas**: raspagem do HTML do portal; URLs fixas por ano; conferência só pelo tamanho; baixar tudo a cada execução.

### D8 — Download em streaming, com tentativas e em paralelo
- **Decisão**: `download_resource` lê blocos de 1 MiB para `<arquivo>.<id do recurso>.part` (D28), que só substitui o arquivo quando completo; 3 tentativas, com espera de 2 s e 4 s e limite de 60 s por tentativa; tamanho diferente do publicado gera aviso. A Programação diária e os conjuntos do motor comum usam 8 downloads simultâneos (`DOWNLOADS_SIMULTANEOS`); os demais, um por vez. Um arquivo não obtido vira `FALHA` na auditoria, e os outros continuam.
- **Motivo**: arquivos de até 200 MB sem pico de memória; centenas de arquivos diários pequenos.
- **Alternativas rejeitadas**: carregar a resposta inteira na memória.

### D9 — Manifesto de versões por pasta
- **Decisão**: um `_manifesto_ons.json` por pasta de conjunto (e por `_dicionarios/`), com uma entrada por arquivo, gravado no fim da sincronização num bloco `finally`, mesmo se ela for interrompida, de forma atômica (`.json.part` e `replace`, chaves ordenadas). A data de obtenção de um conjunto é o maior `registrado_em_utc` do manifesto, contado só nos arquivos do escopo da usina em `datas_obtencao.csv` (D29).
- **Motivo**: registro da versão de cada arquivo, compartilhado por todas as usinas.

### D10 — Versões anteriores: só com conteúdo diferente, no máximo duas
- **Decisão**: depois do download completo, se o SHA-256 da cópia local difere do novo, ela vai para `_versoes_anteriores/<nome>__pub_<AAAAMMDDTHHMMSS><ext>` (publicação registrada) ou `__arq_<data do arquivamento>`, com `_2`, `_3`… se o nome existir. Acima de `MAXIMO_VERSOES_ANTERIORES` (2), as mais antigas são excluídas e registradas em `versoes_excluidas`; a exclusão só atua dentro de `_versoes_anteriores/`.
- **Motivo**: reproduzir um relatório entregue sem acumular cópias; republicação idêntica não gera versão.
- **Alternativas rejeitadas**: conferir só o tamanho; guardar todas as versões; uma pasta única de versões para todos os conjuntos.

### D11 — Dicionários sempre baixados e comparados pelo conteúdo
- **Decisão**: recursos PDF e JSON cujo nome, sem acento, contém "DICIONARIO", baixados com `force=True` para `<pasta do conjunto>/_dicionarios/`. O resultado (`NOVO`, `INALTERADO`, `ALTERADO` com versão preservada como em D10, ou `FALHA`) vai para o manifesto da pasta, que tem também a entrada `_consulta`. `dicionarios.csv` é montado só dos manifestos (`NAO_PUBLICADO`, `NAO_OBTIDO`), com os conjuntos da usina, na ordem do registro (D26). O passo roda no fim da coleta, também quando um conjunto a parou com 2; falha nele não muda o código de saída.
- **Motivo**: o catálogo não informa tamanho nem data dos dicionários.
- **Alternativas rejeitadas**: baixar só o que falta (não detecta mudança); pasta central de dicionários; interromper a coleta por um dicionário.

### D12 — Identificador de extração e campo de conferência
- **Decisão**: a linha só é extraída se o identificador e a conferência do perfil conferem; as que conferem só em parte são contadas na auditoria e avisadas no log, com o arquivo. Textos pela normalização única `registro.normalizar_texto` (sem acento, sem espaços nas pontas e em maiúsculas); números como número (`conjuntos._corresponde`, usado nos indicadores e no motor comum; a seção 5.2 do [data-model](data-model.md) traz a comparação de cada conjunto). O nome do agente nunca entra. Exceções: taxas e parâmetros da TEIFa e da TEIP só pelo CEG; CMO só pelo subsistema; no cadastro, a ficha é localizada pelo CEG, e id ONS e estado só são contados.
- **Motivo**: homônimos com o mesmo nome em outros estados e tipos de usina; troca de agente na mesma usina.
- **Alternativas rejeitadas**: chave textual com o nome do agente (quebra com a troca de agente); só o código (uma troca de código passaria despercebida).
- **Limitação conhecida**: na EVT, o código é comparado como texto sem os espaços das pontas, igual ao `cod_usina` do perfil. As demais limitações da primeira versão foram corrigidas (D28).

### D13 — Formato e período de cada conjunto
- **Decisão**:
  - EVT: todos os CSV publicados, lidos em ordem de nome (anuais antes dos mensais);
  - indicadores e taxas: CSV com o ano do nome dentro dos anos do período, e os arquivos sem ano;
  - Programação diária: só o Parquet, um por dia; o dia vem do nome, e a data interna (`AAAA-MM-DD` ou `DD/MM/AAAA`) só é conferida;
  - conjuntos do motor comum: por ano ou mês do nome sobreposto ao período, o Parquet quando publicado e senão o CSV; na série de referência, todos os arquivos publicados;
  - cadastro: o CSV único; Composição, Capacidade e Reservatórios: o arquivo único, em Parquet, senão em CSV;
  - em todos, entre recursos repetidos, o que tem publicação e, em empate, o maior (D28).
- **Motivo**: em CSV, a programação diária do período somaria cerca de 26 GB (o Parquet, cerca de 106 MB), e os conjuntos dos demais tipos passariam de 20 GB; o Parquet da disponibilidade falta em parte dos meses (na São Domingos, 53 meses vêm do CSV).
- **Alternativas rejeitadas**: dia da programação pela coluna interna (a leitura automática inverteu dia e mês); disponibilidade só em Parquet (perde meses) ou só em CSV (cerca de 1 GB a mais, sem ganho).

### D14 — Leitura em streaming na EVT e com filtros nos demais
- **Decisão**: a EVT é lida linha a linha com `csv.reader`, com o nome do reservatório normalizado uma vez por valor distinto. Os CSV dos demais conjuntos são lidos pelo pandas como texto, só com as colunas necessárias, e os Parquet com projeção de colunas. Na Programação diária, `pyarrow.compute` mantém só as linhas com o estado ou com o código da usina (os valores publicados cuja forma normalizada confere); no motor comum, o filtro do Parquet (`filtro_parquet`) mantém as linhas com o identificador ou a conferência, nas duas formas do valor.
- **Motivo**: cerca de 15 milhões de linhas da EVT com memória constante; 134 milhões de linhas da programação sem montar a tabela inteira; a Geração por usina inteira (0,73 GB) varrida na série de referência.
- **Alternativas rejeitadas**: ler cada CSV da EVT inteiro com pandas; filtrar fora do Python.

### D15 — Codificação e linhas irregulares
- **Decisão**: CSV com `;`, em UTF-8 (`utf-8-sig` nos lidos pelo pandas) e, com erro de decodificação, relido inteiro em Latin-1. Colunas localizadas pelo nome. Linhas não vazias com número de campos diferente do cabeçalho não são extraídas: são contadas e avisadas no log com o arquivo, a quantidade e as cinco primeiras (número da linha no arquivo, com o cabeçalho na linha 1). O CSV vazio da EVT fica `FALHA` com o motivo "arquivo vazio" (D28).
- **Motivo**: uma linha curta não entra com campos vazios, e uma longa não perde o excedente em silêncio.
- **Alternativas rejeitadas**: truncar as linhas longas (valores deslocados).

### D16 — Valores como publicados
- **Decisão**: a EVT guarda o número sem arredondar, na representação do Python, com ponto; a programação e o motor comum leem cada valor por `conjuntos.numero_publicado`, que aceita vírgula e ponto decimal e lê as marcas booleanas como 1 e 0 (D28). Em todos esses conjuntos, vazio fica ausente, e texto não numérico fica ausente e conta em `valores_invalidos` (na EVT, `null`, `none` e `nan` valem como vazio; no motor comum, a linha ganha `_nao_numerico`). Indicadores, taxas e cadastro ficam como texto sem espaços nas pontas (só a potência autorizada da ficha vira número, também por `numero_publicado`).
- **Motivo**: convenção de hora, duplicatas entre arquivos, recorte e sinalizações são do [Tratamento de dados](../002-tratamento-dados/spec.md).

### D17 — Consolidação só na EVT
- **Decisão**: `consolidate_records` deixa um registro por (`cod_usina`, `din_instante`), o do arquivo lido por último; conta as duplicatas idênticas e as conflitantes (estas avisadas com os dois arquivos); descarta registro sem instante; ordena por instante.
- **Motivo**: a EVT define o período dos demais conjuntos na hidrelétrica com EVT; o código na chave impede que usinas diferentes no mesmo instante se anulem.

### D18 — `--sem-portal`, `--forcar-download` e parada na falha
- **Decisão**: com `--sem-portal`, nenhuma sincronização roda e `--forcar-download` é ignorado; a extração usa as mesmas regras de período e formato sobre os arquivos locais, e o registro dos dicionários vem dos manifestos. Com `--forcar-download`, todo arquivo de dados é baixado de novo. Um conjunto com `FALHA` encerra a coleta com 2 depois de gravar o extraído e a auditoria dele; os quatro conjuntos de indicadores formam um bloco. O comando `usinas` segue as mesmas regras.
- **Motivo**: reproduzir o relatório sem rede e não seguir com um conjunto incompleto.

### D19 — Tipo da usina pelo prefixo do CEG
- **Decisão**:
  - O tipo são as três primeiras letras do CEG: UHE, PCH, CGH, UTE, UTN, EOL ou UFV (`catalogo_usinas.tipo_do_ceg`; no perfil, `registro.tipo_da_usina`).
  - A linha do cadastro sem CEG (ou com "-") é de conjunto de usinas (tipo `conjunto`), e o tipo do conjunto vem da composição.
  - Prefixo fora da lista vira `outro`: aparece no catálogo e não recebe perfil.
  - Os tipos publicados pelo ONS (`nom_tipousina`, `id_tipousina`) só são conferidos (`TIPOS_ONS` em `regras.py`); a divergência vai para a coluna `divergencias` do catálogo e, na série do conjunto, para `tipo_publicado.csv`.
- **Motivo**: o cadastro do ONS não tem coluna de tipo. Os tipos do ONS juntam PCH e UHE (a Composição dos conjuntos classifica PCH como "UHE") e já publicaram um conjunto hidráulico como térmico (Conj. Chapadão).
- **Alternativas rejeitadas**: `nom_tipousina` da geração (instável e não separa PCH e CGH de UHE); a Capacidade de geração (também não separa, e só cobre usinas com unidade cadastrada).

### D20 — Catálogo de usinas na Coleta
- **Decisão**:
  - `python -m src usinas` é da Coleta (`src/coleta/catalogo_usinas.py`). Sem `--sem-portal`, sincroniza com o mesmo catálogo CKAN, cache e versões dos demais conjuntos: os quatro cadastrais (`CADASTRAIS`: Modalidade das usinas, Composição dos conjuntos, Capacidade de geração e Reservatórios); o arquivo mais recente de cada série de `SERIES` (os conjuntos de série do registro, nas restrições uma por variante); todos os arquivos do despacho e da Programação diária; a Geração por usina dos últimos 12 meses completos (`MESES_AGREGADOS_CATALOGO`); e os dicionários desses conjuntos.
  - Grava `data/catalogo/` por inteiro, sem `.bak`, numa pasta temporária (`.gravando`), conferida antes da troca; `catalogo.json` traz `versao_formato` (`VERSAO_FORMATO_CATALOGO`, 1), que o `perfil` exige.
  - Lista as usinas do filtro sempre a partir dos arquivos gravados (`ler_catalogo`), com o slug do perfil achado pelo CEG em `usinas/*/perfil.toml`.
  - Os downloads vão para as pastas compartilhadas de `data/raw/`; por isso, as referências usam a Coleta congelada (spec da Geração do relatório).
- **Motivo**: princípio I (só a Coleta acessa o portal, e o catálogo é dela) e reaproveitamento dos arquivos baixados. O rascunho do perfil precisa dos códigos sem ler os brutos. O cadastro é pequeno (6.017 linhas), e o despacho inteiro tem 0,14 GB. A programação inteira é lida porque um conjunto pode trocar os códigos (o Conj. Chapadão, em 07/2025).
- **Alternativas rejeitadas**: montar o catálogo a cada `perfil` (repetiria a consulta ao portal fora da Coleta); catálogo no git (muda todo dia; os dados ficam em `data/`); só o arquivo mais recente da programação (o perfil perderia os códigos anteriores do conjunto).

### D21 — Cobertura de cada conjunto de série
- **Decisão**:
  - Para cada usina e cada conjunto de série do registro que serve ao tipo, o nível é `proprio` (linhas com o identificador da usina e valor), `conjunto` (o conjunto da usina tem linhas com valor; vale também quando a usina tem linhas próprias sem valor, como as PCH Tipo II-C na Geração por usina), `agregado` (usina Tipo III) ou `ausente`.
  - A verificação usa o arquivo mais recente de cada conjunto de série (nos indicadores, o DISPF mensal) e os identificadores da D27; na EVT e nos dados hidrológicos, o `cod_usina` dos Reservatórios (D33); na programação, só os códigos ligados presentes no arquivo; no CVU, os códigos de planejamento do último mês publicado do despacho.
  - `cobertura.csv` grava, por usina e conjunto, o nível, o identificador usado, as linhas, as linhas sem valor, o arquivo e a data de publicação; `usinas.csv` traz o melhor nível em `cobertura_resumo`.
  - A cobertura só lista os conjuntos já registrados; um conjunto novo no registro entra no catálogo no `usinas` seguinte.
- **Motivo**: um arquivo por conjunto mantém o catálogo do Brasil em minutos; a Coleta da usina escolhida confirma depois o período inteiro.
- **Alternativas rejeitadas**: varrer todos os arquivos de cada conjunto para todas as usinas (vários GB, e é o que a Coleta já faz para a usina escolhida); deduzir a cobertura só pelo tipo e pela modalidade (erraria nas PCH em conjunto e nas usinas que mudam de modalidade).

### D22 — Perfil por tipo, compatível com o perfil da UHE
- **Decisão**:
  - Continua o mesmo `usinas/<slug>/perfil.toml`, lido com `tomllib`.
  - Em `[usina]`, entram `tipo` e `modalidade` (Tipo III recusado), `situacao` (`rascunho` ou `conferido`; sem o campo, conferido), `pendentes` e, nas térmicas, `subsistema`.
  - Em `[identificacao]`, os campos passam a ser exigidos conforme o tipo e a cobertura; entram `id_conjunto`, `codigos_programacao` (com `cod_programacao` ainda aceito), `[[identificacao.planejamento]]` e `[[identificacao.membros]]` (só para a conferência da soma das usinas do conjunto).
  - Em `[parametros]`, os comuns (potência instalada, unidades, garantia física, opcional fora da UHE) e a potência das unidades, como `potencia_unitaria_mw` ou a lista `potencias_unidades_mw`, com a soma igual à potência instalada; os hidráulicos só onde há EVT ou hidrologia; `combustivel` nas térmicas. `[analises]` só onde há EVT.
  - A tabela `[cobertura]` declara o nível de cada conjunto de série; o valor pode ser a lista `["proprio", "conjunto"]`.
  - A validação usa a tabela de campos por grupo de tipos de `src/comum/perfil_campos.py` (`O`, `C` com os conjuntos e os níveis que o exigem, `opcional`, `—`); as chaves válidas da `[cobertura]` vêm do registro (`chaves_da_cobertura`). O padrão do CEG aceita os sete prefixos. Fora das hidrelétricas com EVT ou hidrologia, pedir um valor derivado hidráulico é erro claro.
  - O perfil da São Domingos ganha só `tipo = "UHE"` e `modalidade = "TIPO II-A"`.
- **Motivo**: a São Domingos fica sem mudança no relatório; o TOML já foi aprovado (D2); o princípio III manda o perfil declarar os conjuntos que cobrem a usina, conferidos pelo fiscal.
- **Alternativas rejeitadas**: um formato de perfil por tipo (duplicaria a leitura); classes por tipo (mais código para a mesma regra); campos de UHE opcionais para todos (perderia a validação da UHE); ler a cobertura do catálogo a cada execução (uma atualização do ONS mudaria o fluxo sem o fiscal saber).

### D23 — Rascunho do perfil a partir do catálogo
- **Decisão**:
  - `python -m src perfil --ceg <CEG> [--slug <slug>]` (`src/coleta/perfil_rascunho.py`) lê só `data/catalogo/`, sem portal e sem os brutos.
  - Recusa sem gravar, nesta ordem: slug inválido ou reservado (2); catálogo ausente ou em formato antigo (5); CEG fora do catálogo (2); tipo fora dos sete (2); usina Tipo III, ou só com cobertura agregada ou ausente (2), com a mensagem que remete ao panorama da carteira.
  - Perfil existente (na pasta do slug ou outro com o mesmo CEG): nada é gravado; `diferencas` lista os campos diferentes do catálogo e o comando sai com 6, ou com 0 sem diferença.
  - O rascunho traz `situacao = "rascunho"`, `pendentes` e a origem de cada valor em comentário (o conjunto do ONS e a data de publicação do arquivo usado no catálogo). Os parâmetros que o ONS publica (unidades ativas, potência efetiva, combustível, entrada em operação) entram preenchidos e a conferir; só contam as unidades sem data de desativação passada. A potência autorizada do cadastro diferente da soma das unidades vai para um comentário. Os demais campos do tipo ficam pendentes, como linhas comentadas.
  - É gravado por `gravar_bytes`, sem `.bak`, conferido no disco e lido de novo como TOML.
- **Motivo**: o fiscal completa só os parâmetros técnicos (SC-016); nada é sobrescrito; os códigos mudam no tempo, e o fiscal precisa vê-los para conferir.
- **Alternativas rejeitadas**: ler os brutos no `perfil` (acessaria dados fora da Coleta); deixar a Coleta descobrir os códigos sozinha (a extração passaria a depender de identificadores que não estão no perfil, princípio IV); preencher a garantia física e o IP e a TEIF de referência (não vêm do ONS).

### D24 — Série de referência e período
- **Decisão**:
  - `serie_referencia.escolher` escolhe pelo tipo e pela cobertura: a EVT quando ela é coletada; senão a Geração por usina, nos níveis declarados em `geracao`; na EOL ou UFV sem geração própria e com a restrição com detalhe da usina coletada, essa restrição. Sem nenhuma, `ValueError` e código 1.
  - Fora da EVT, a série é varrida em todos os arquivos publicados (de `INICIO_VARREDURA`, 1990, até um ano depois da data da execução), com o filtro do identificador na leitura do Parquet. O período vai da primeira à última hora com valor; com a lista `["proprio", "conjunto"]`, é a união, e cada hora fica com a da usina quando ela tem valor (`combinar`).
  - Na usina em conjunto sem série própria, a Composição dos conjuntos é coletada antes, e as horas do conjunto só contam nos intervalos da usina na composição (`intervalos_da_usina`, `no_intervalo`; decisão do usuário de 22/10/2026). Usina fora da composição: código 2, com o CEG e o id do conjunto na mensagem.
  - Sem hora com valor: código 2, depois de gravar a auditoria da série.
  - O resumo traz a série escolhida (`Escolha`: conjunto, níveis e motivo), o identificador, o início, o fim e os arquivos varridos. A hidrelétrica com EVT segue o caminho da EVT sem mudança.
- **Motivo**: princípio IV (período pela série de referência, com todos os arquivos publicados). A Geração por usina inteira em Parquet tem 0,73 GB, e a leitura filtra pelo identificador. Antes da entrada da usina, a geração do conjunto não a inclui.
- **Alternativas rejeitadas**: período fixo, como os últimos cinco anos (viola o princípio IV); período pela data de entrada em operação do cadastro (não reflete os dados publicados); toda a série do conjunto na usina que entrou depois (atribuiria à usina anos sem ela).

### D25 — Trechos dentro do período
- **Decisão**:
  - Fora das hidrelétricas com EVT, `serie_referencia.trechos` divide o período quando muda a modalidade da usina (hora a hora, na coluna de modalidade da série de referência), o nível do dado, a composição do conjunto (pelas datas da Composição dos conjuntos) ou o código de planejamento da térmica (pelos meses do perfil).
  - `trechos.csv` traz, por trecho, a composição e os tipos dela, os códigos vigentes, o nível e `mostrar`, verdadeiro no trecho cujo nível ou composição difere do anterior ou do seguinte; `geracao_complemento.parquet` traz a modalidade e o nível de cada hora (nas séries semi-horárias, por hora cheia).
  - O relatório só mostra os trechos com `mostrar`; a mudança só de modalidade ou de código vai para a planilha. Nas hidrelétricas com EVT, não há trechos.
- **Motivo**: princípio VIII; o Conj. Chapadão teve térmicas até 07/2025.
- **Alternativas rejeitadas**: usar a composição atual em todo o período (atribuiria às PCH a geração das térmicas que saíram); mostrar todos os trechos (na UHE, mudaria o relatório aprovado sem ganho de informação).

### D26 — Registro declarativo dos conjuntos do ONS
- **Decisão**:
  - `src/coleta/registro.py` traz `REGISTRO`, com 16 entradas (`EntradaRegistro`: chave, pacotes e pastas, tipos, níveis, resolução, se pode ser série de referência, variantes por tipo, descrição para o motor comum, se é só do catálogo e o campo do perfil sem o qual não é obtido). `CONJUNTOS_PIPELINE` (21 pacotes) é derivado dele.
  - `conjuntos_da_usina(perfil)`: sem `[cobertura]`, só na UHE, os sete conjuntos de `CHAVES_SEM_COBERTURA` (os dez pacotes da UHE); com ela, os conjuntos de série com `proprio` ou `conjunto` e, sempre, os estáticos e o CMO (com o subsistema). `descricoes(perfil)` monta as descrições do motor comum no nível da cobertura; `pacotes(entradas, tipo)` escolhe a variante do tipo.
  - `DescricaoConjunto` ganhou `chave`, `tipos`, `nivel`, `resolucao`, `referencia`, `variantes`, `colunas_texto` (colunas mantidas como texto), `coluna_instante` (a data publicada gravada como `din_instante`) e `avisar_colunas_ausentes`.
  - EVT, indicadores, programação e cadastro mantêm os módulos próprios, mas ficam registrados, para o filtro por tipo e os dicionários.
  - **Dicionários e fontes por usina**: o registro dos dicionários e as abas DICIONARIOS e FONTES listam só os conjuntos do tipo e da cobertura da usina; na UHE sem `[cobertura]`, os dez conjuntos da UHE, na mesma ordem.
  - **Arquivos e colunas**: coluna nova só entra em arquivo novo, nunca num arquivo que o relatório da UHE já usa.
  - **Formato**: o `VERSAO_FORMATO` de uma etapa sobe quando muda um arquivo que ela já grava, ou quando a etapa seguinte passa a exigir um arquivo novo; arquivo novo opcional não muda o formato.
- **Motivo**: um só lugar diz o que se coleta para cada tipo (a tabela de aplicabilidade da spec); reaproveita o motor dos conjuntos horários (seleção por período e formato, cache e auditoria); sem as regras de dicionários, colunas e formato, a planilha da São Domingos mudaria (a aba DICIONARIOS passaria de 20 para 40 linhas).
- **Alternativas rejeitadas**: um módulo por conjunto novo (repetiria o motor); um `if tipo` em cada etapa (espalharia a regra pelo código).

### D27 — Identificação nos conjuntos dos demais tipos
- **Decisão**: `Regra` tem os modos `igual`, `contem`, `em` (um dos números) e `codigo_no_periodo` (o número da linha é um dos códigos e o instante dela está no período dele).

  | Conjunto | Identificador | Conferência | Observação |
  |---|---|---|---|
  | Geração térmica por motivo de despacho | CEG | código de planejamento entre os do perfil, no período de cada um | código comparado como número; linha com o CEG e código fora da lista conta como "só identificador" |
  | CVU das usinas térmicas | código de planejamento entre os do perfil | subsistema do perfil | todas as revisões; a escolha é do Tratamento |
  | CMO semanal | subsistema do perfil | nenhuma: é contexto do subsistema | nível agregado |
  | Fator de capacidade; restrição com a razão | id ONS da usina ou do conjunto | CEG (usina) ou estado (conjunto, de CEG "-") | |
  | Restrição com detalhe | id ONS da usina | CEG | o id do conjunto falta de 05 a 12/2024 na fotovoltaica e fica como texto, sem conferir |
  | Geração por usina, do conjunto | id do conjunto | estado | CEG "-" desde 05/2026 |
  | Composição dos conjuntos | id do conjunto | estado | estático; a usina é localizada pelo CEG na composição |
  | Capacidade de geração | CEG | estado | estático |
  | Capacidade de geração das usinas do conjunto | CEG da usina na composição, no período | subsistema da linha da usina na composição | o estado não serve (Conj. Chapadão, de MS, com UTE de GO); as linhas só com o CEG vão para `auditoria_capacidade_membros.csv` |

  Nomes nunca identificam nem conferem: mudam de grafia.
- **Motivo**: princípio IV, com identificador e conferência, nunca o nome; homônimos excluídos pelos códigos (princípio III).
- **Alternativas rejeitadas**: nome normalizado como conferência (falha com "Willian/William" e "230kV/230 kV"); CVU pelo nome (o CVU não tem CEG); unidades das usinas do conjunto sem conferência (as linhas parciais não seriam contadas).

### D28 — Correções das limitações da primeira versão (P1 a P5)
- **Decisão**: corrigidas antes dos conjuntos novos e antes de qualquer download de outra usina:

  | Correção | Limitação da primeira versão | Como ficou |
  |---|---|---|
  | P1 | só os conjuntos horários escolhiam entre recursos repetidos no catálogo; a EVT, os indicadores e a programação baixavam cada repetição, a programação em paralelo e com o mesmo `<arquivo>.part` | `recurso_preferido`, `escolher_entre_repetidos` e `registrar_repetidos` (`catalogo.py`) em todos os conjuntos; o temporário é `<arquivo>.<id do recurso>.part` |
  | P2 | vírgula decimal não aceita nos conjuntos horários e na potência da ficha | `conjuntos.numero_publicado`, com vírgula e ponto, no motor comum, na programação e na ficha |
  | P3 | o pré-teste da EVT usava o texto com acento; a programação só tirava espaços; o filtro do Parquet da geração usava o valor como publicado | `registro.normalizar_texto` em toda a extração e nos pré-filtros; na EVT, o nome normalizado uma vez por valor distinto; na programação, o filtro do pyarrow com os valores publicados cuja forma normalizada confere; no Parquet do motor comum, as duas formas do valor |
  | P4 | num conjunto horário sem a coluna de conferência, as linhas contavam como "só identificador", sem `FALHA` | `_exigir_conferencias`: "coluna de conferência ausente: <coluna>" e `FALHA` |
  | P5 | o CSV vazio da EVT ficava `FALHA` sem o motivo | o motivo "arquivo vazio" na auditoria; o CSV só com o cabeçalho continua `SEM_REGISTROS` |

- **Motivo**: com outras usinas, os casos aparecem (nomes e códigos com acentos e grafias variadas). Na São Domingos, as correções não mudaram nada, conferido pela comparação com a referência depois de cada uma.
- **Alternativas rejeitadas**: corrigir junto com cada conjunto novo (misturaria a correção com o conjunto e dificultaria isolar uma diferença no relatório da São Domingos).

### D29 — Etapas 2 a 5 sem `data/raw/` (formato 2)
- **Decisão**: a Coleta grava `datas_obtencao.csv` (uma linha por conjunto coletado, só com os arquivos obtidos do escopo da usina) e, na hidrelétrica com EVT, `dicionario_evt.json` (a cópia de `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json`), pela persistência, também quando para com 2. `VERSAO_FORMATO["coleta"]` = 2. As etapas 2 a 5 leem só esses arquivos, o `dicionarios.csv` e os demais resultados da Coleta; `tests/integracao/test_sem_raw.py` as roda com `data/raw/` vazio.
- **Motivo**: princípio I; antes, as Análises e o Relatório liam as datas de obtenção e o resumo do manifesto da EVT em `data/raw/`, compartilhado, e o Tratamento lia lá o dicionário da EVT: a coleta de outra usina mudaria as datas e a contagem de arquivos do relatório da São Domingos. As referências refazem as etapas 2 a 5 a partir da Coleta congelada.
- **Alternativas rejeitadas**: continuar lendo os manifestos de `data/raw/` (depende dos brutos compartilhados); ler o formato 1 com uma camada de compatibilidade (código a mais para um único refazer, sem download).

### D30 — Uma usina fictícia por tipo
- **Decisão**: sete usinas fictícias em `tests/fixtures/usinas_ficticias/<tipo>/`, com brutos sintéticos no formato de cada conjunto do registro (`tests/fixtures/brutos_ficticios.py`), valores inventados; cada uma roda `completo --sem-portal` sem rede (`tests/integracao/test_usinas_ficticias.py`). O catálogo é testado com um Brasil fictício (`tests/fixtures/brutos_catalogo.py`). `tests/comum/test_literais.py` procura também os identificadores e os CEG das usinas piloto no código.

  | Tipo | O que exercita |
  |---|---|
  | UHE | a usina fictícia original (`tests/fixtures/usina_ficticia/`), com outro slug |
  | PCH | em conjunto, que ela integra em 10/01/2024 (período recortado), com uma térmica que sai em 15/02/2024 (três trechos de composição), o conjunto publicado como térmico, uma CGH membro sem unidade cadastrada e as linhas próprias sem valor |
  | CGH | geração própria e Dados hidrológicos: a hidrelétrica sem EVT |
  | UTE | 2023 inteiro sem geração e disponível, com um código de planejamento trocado em 01/2024 por duas unidades (gás e óleo); o arquivo anual de 2024 repetindo os mensais; CVU com duas revisões por semana e um valor negativo; CMO com uma semana republicada; a disponibilidade com horas de geração acima dela e uma parada |
  | UTN | uma unidade de planejamento; nuclear como térmica, com os indicadores e as taxas |
  | EOL | Tipo I; vento inválido; semi-horas restritas com as três razões; restrição desde 15/01/2024 |
  | UFV | em conjunto, com um membro; série curta; a restrição com detalhe como série de referência; o arquivo de janeiro no esquema antigo, com colunas ausentes |

- **Motivo**: SC-013 e a constituição (Qualidade 1): todo tipo testado de ponta a ponta, sem rede.
- **Alternativas rejeitadas**: recortes dos brutos reais nos testes (poriam valores de usina real no código).

### D31 — Códigos de saída dos comandos sem etapa
- **Decisão**: os comandos `usinas`, `perfil`, `carteira`, `referencia` e `comparar --todas` reaproveitam os códigos 0 a 6, como na FR-005, sem gravar `etapa.json`. O argparse recusa com 2 as opções inválidas, inclusive a `carteira` sem `--estado` nem `--tipo` e as combinações inválidas do `comparar`; no `usinas`, `--tipo` aceita os sete tipos e `conjunto`, sem diferença entre maiúsculas e minúsculas.
- **Motivo**: os códigos 0 a 6 já cobrem os casos; o fiscal e os testes leem um único significado por código.
- **Alternativas rejeitadas**: códigos novos, de 7 em diante (não há caso que os códigos 0 a 6 não cubram).

### D32 — Outros casos
- **UTN**: segue as regras de térmica, com o combustível nuclear; CVU, CMO, DISPF e TEIFa entram quando o ONS os publica para a usina.
- **Usina com intervalo longo sem dados** (a William Arjona sem despacho de 08/2018 a 07/2021): a Coleta extrai o que há, sem preencher nada; o Tratamento lista o intervalo nas ausências.
- **Desempenho**: as leituras são em Parquet, com filtro e só no período da usina; a série de referência inteira é o que mais pesa (0,73 GB na Geração por usina; menos nas restrições).

### D33 — Reservatórios: o CEG das séries identificadas pelo código da usina
- **Problema**: a Energia Vertida Turbinável e os Dados hidrológicos horários identificam a usina só pelo `cod_usina` (código nos modelos de planejamento) e pelo reservatório, sem CEG nem id ONS. Sem uma ligação ao CEG, o catálogo não verifica a cobertura desses dois conjuntos, e o rascunho do perfil não traz os códigos da hidrelétrica.
- **Decisão** (do usuário, em 19/10/2026): o conjunto Reservatórios (`reservatorio`) é o quarto cadastral do catálogo, só dele (`so_catalogo`; a Coleta da usina não o obtém). Ele traz, por reservatório, o CEG, o `cod_resplanejamento` (o `cod_usina` da EVT e dos dados hidrológicos), o `res_id` (o `id_reservatorio` dos dados hidrológicos) e o nome. A cobertura da EVT e dos dados hidrológicos é verificada pelo `cod_usina`; usina sem linha nos Reservatórios fica `ausente` nos dois. O rascunho das hidrelétricas traz `cod_usina`, `nome_ons` (o nome do reservatório, sem acento, em maiúsculas) e `id_reservatorio`, com a fonte e a conferir.
- **Conferido em 19/10/2026**: UHE São Domingos, CEG `UHE.PH.MS.028761-0.01` → `cod_resplanejamento` 153 e `res_id` PNUHSD, os mesmos do perfil aprovado.
- **Motivo**: princípio IV (identificação pelos códigos, nunca pelo nome) e a cobertura de cada conjunto no catálogo.
- **Alternativa rejeitada**: deixar a EVT e a hidrologia `ausente` no catálogo e os códigos a cargo do fiscal (o catálogo diria que nenhuma hidrelétrica tem EVT).

### Desvios registrados na implementação

| Data | O que mudou | Aprovação |
|---|---|---|
| 21/10/2026 | A EOL fictícia tem a restrição com detalhe desde 15/01/2024, dentro do período sintético de jan e fev/2024, e não desde 10/2021, como previa a tabela das usinas fictícias (D30). | registrada nos testes das eólicas e solares e aceita pelo usuário com a aprovação das referências da Seriemas 1 e da Praia Formosa (21/10/2026) |
| 22/10/2026 | A CGH fictícia tem geração própria e Dados hidrológicos (é a hidrelétrica sem EVT), e não "em conjunto, só o nível do conjunto"; o caso da CGH em conjunto é o mesmo caminho da PCH, cujo conjunto fictício tem uma CGH (D30). | aceita pelo usuário com a aprovação da PCH Bandeirante (22/10/2026) |
| 22/10/2026 | O rascunho da PCH Bandeirante traz oito códigos de programação, e não os quatro do exemplo do contrato do perfil: são os códigos de todo o período (FR-051 e FR-053); o exemplo do contrato foi atualizado. | usuário, ao completar o perfil e aprovar o relatório da Bandeirante (22/10/2026) |
| 26/10/2026 | O dicionário das taxas operativas chama duas colunas de `id_tipousina` e `din_instante`, e o arquivo publica `tip_usina` e `din_calculo`. A diferença não é registrada na auditoria da Coleta, como previa o rascunho aprovado; valem as colunas do arquivo, e o Tratamento aceita os dois nomes da data de cálculo. | aceito pelo usuário em 26/10/2026 |

## Complexity Tracking

Sem desvios da constituição. Os pontos abaixo trazem complexidade e estão justificados:

| Ponto | Por que é necessário | Alternativa mais simples rejeitada porque |
|---|---|---|
| Tabela `[cobertura]` no perfil, além do catálogo | o princípio III manda o perfil declarar os conjuntos que cobrem a usina, conferidos pelo fiscal | ler a cobertura do catálogo a cada execução faria uma atualização do ONS mudar o fluxo sem o fiscal saber |
| `VERSAO_FORMATO` 2 na Coleta | a Coleta grava arquivos que as etapas seguintes passam a exigir; o formato antigo é recusado com o código 5 e a indicação da etapa a refazer | uma camada de compatibilidade de leitura seria código a mais para um único refazer, sem download |
