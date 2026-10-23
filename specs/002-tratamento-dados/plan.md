# Implementation Plan: Tratamento de dados

**Spec**: [spec.md](spec.md) · **Etapa**: 2 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-23

## Summary

O Tratamento lê só o que a Coleta gravou para a usina (`data/usinas/<slug>/coleta/`), inclusive a cópia do dicionário de dados da EVT, e grava em `data/usinas/<slug>/tratamento/` os arquivos que a Conferência e as Análises usam, conforme o tipo e a cobertura da usina. O caminho é escolhido pela série de referência da usina:
- **hidrelétrica com EVT** (UHE, PCH ou CGH): os 21 arquivos da hidrelétrica. A base de EVT é tipada (ausente continua ausente), conferida pelas regras R1 a R9 (R1 bloqueia; R6 a R9 sinalizam sem excluir) e gravada em Parquet, planilha e CSV, com o relatório de validação gerado dos números. Os indicadores e as taxas ficam na versão mais recente, a programação passa a valores horários, e as séries de disponibilidade, hidrologia e geração passam por um motor único: hora de início, uma hora por instante, recorte no período da EVT, ausências listadas, sinalização de qualidade e auditoria completa.
- **usinas sem EVT**: o período vem da série de referência gravada pela Coleta. Os conjuntos da cobertura passam pelo mesmo tratamento, e a base horária comum (`base_horaria.csv`) reúne, hora a hora, a geração da série de referência com o nível (usina ou conjunto), a disponibilidade, a programação, o trecho e as sinalizações. Nas térmicas, o despacho por motivo vai à hora por unidade de planejamento e somado, o CVU fica na revisão mais recente, com o sinal, e o CMO na publicação mais recente. Nas eólicas e solares, a restrição com detalhe fica na resolução de 30 minutos e em hora cheia, com a energia cortada só nas semi-horas restritas e a razão da restrição, e o fator de capacidade passa pelo motor das séries, com o nível e as sinalizações.

Toda gravação passa pela persistência comum (`src/comum/persistencia.py`), com `.bak` da versão anterior, conferência no disco e restauração em falha.

## Technical Context

**Language/Version**: Python 3.11 ou mais recente (no `venv`: CPython 3.14.6).

**Primary Dependencies**: `pandas` (3.0.6), `numpy` (2.5.3), `pyarrow` (25.0.1: leitura dos extraídos e gravação do Parquet) e `openpyxl` (3.1.5: planilhas e propriedade `assinatura_dados`), com as versões mínimas de `requirements.txt`; da biblioteca padrão, `hashlib`, `zipfile`, `shutil`, `json` e `unicodedata`. Os tipos novos não trouxeram dependência nova.

**Storage**: arquivos locais.
- Entrada: só `data/usinas/<slug>/coleta/`: CSV `;` da EVT, das auditorias e dos trechos, Parquet dos extraídos e do complemento da série de referência, `etapa.json` (pré-requisito e, nas usinas sem EVT, o período) e `dicionario_evt.json`. Nada de `data/raw/`.
- Saída: `data/usinas/<slug>/tratamento/`, com Parquet, planilhas `.xlsx`, CSV (`;`, ponto decimal, UTF-8), Markdown, `etapa.json` e um `<arquivo>.bak` por arquivo de dados já alterado. Detalhes em [data-model.md](data-model.md).

**Testing**: `pytest`, sem rede, com dados sintéticos (`tests/conftest.py`, `tests/fixtures/`).
- `tests/tratamento/`: tipagem, formatos e nome da aba da EVT, regras R1 a R9 e relatório, motor das séries, sinalizações D, H e G, indicadores, programação (média dos patamares e soma dos códigos vigentes no dia), base horária comum (`test_base_horaria.py`), térmicas (`test_termica.py`) e eólicas e solares (`test_renovavel.py`).
- `tests/comum/test_persistencia.py` e `test_persistencia_gravadores.py`: as quatro gravações, falhas simuladas, interrupção pelo usuário, planilha pela assinatura, cada gravador da Coleta e do Tratamento e leitores que ignoram `.bak` e `.tmp`.
- `tests/comum/` (pré-requisito, interrupção, gravação só pela persistência, nível de log, literais das usinas) e `tests/integracao/`: linha de comando, fluxo completo da usina fictícia de três UGs, as sete usinas fictícias, uma por tipo, de ponta a ponta (`test_usinas_ficticias.py`, sobre `tests/fixtures/usinas_ficticias/` e `brutos_ficticios.py`), e as etapas 2 a 5 com `data/raw/` vazio (`test_sem_raw.py`).
- Um teste lê o dicionário local da EVT e outro a EVT extraída real; os dois são pulados se o arquivo não existir. A suíte do projeto tem 840 testes (23/10/2026).

**Target Platform**: Windows 11, execução local no `venv`, com PowerShell.

**Project Type**: projeto único, pipeline de linha de comando (`python -m src tratamento --usina <slug>`).

**Performance Goals**: menos de 10 minutos sem rede (SC-010). Execuções registradas nos `etapa.json`: São Domingos, 37 s (21 arquivos); UTE William Arjona, 10 s (24 arquivos); EOL Praia Formosa, 17 s (14 arquivos); PCH Bandeirante, 7 s (6 arquivos); UFV Seriemas 1, 1 s (15 arquivos). Mesmo sem mudança, cada arquivo é gravado num temporário e conferido antes da comparação.

**Constraints**: sem rede e sem ler `data/raw/`; entradas só da Coleta concluída (FR-002), no formato 2; nenhum registro removido e nenhum valor preenchido ou interpolado; nenhum número de conjunto dividido entre as usinas nem misturado à base da usina; na hidrelétrica com EVT, os arquivos e as colunas não mudam e os dados são os da base de referência aprovada (SC-001); saídas determinísticas, para que a reexecução fique `INALTERADO` (FR-034); CSV e Markdown com o fim de linha do sistema (CRLF no Windows).

**Scale/Scope**:
- São Domingos, na Coleta congelada da referência:
  - EVT: 70.895 registros horários, de 28/08/2018 00h a 28/09/2026 23h (cerca de 8 anos), 25 colunas na base tratada;
  - indicadores: 1.628 linhas extraídas → 196 linhas mensais, 18 anuais, 160 meses-unidade de horas por estado e 61 meses de taxas;
  - programação: 708 arquivos diários, 33.984 patamares → 16.992 horas e 20 dias ausentes;
  - disponibilidade: 98 arquivos (53 CSV, 45 Parquet), 70.943 linhas → 70.895 horas;
  - hidrologia: 98 arquivos (97 Parquet, 1 CSV), 71.456 linhas → 70.760 horas, 136 h ausentes em 48 intervalos, 2.546 h sinalizadas;
  - geração: 61 arquivos Parquet (anuais até 2021, mensais depois), 76.679 linhas → 70.895 horas;
  - saída: 21 arquivos, cerca de 46 MB.
- Usinas piloto dos demais tipos (resumo do `etapa.json`):
  - UTE William Arjona: 46.243 horas na base horária (5 ausentes, 1.322 com a R7, 3 trechos); despacho com 85.104 horas-unidade dos códigos 334 e 434; CVU com 541 registros em 274 semanas (366 com o CVU zero); CMO com 276 semanas;
  - EOL Praia Formosa: 151.598 horas de geração e de fator de capacidade, desde 07/2009; 88.560 semi-horas de restrição (16.311 restritas, 13.157 com o vento inválido, 10.408 com a estimativa ausente), 184.769 MWh cortados;
  - UFV Seriemas 1: 1.416 horas da restrição da usina como série de referência; fator de capacidade e razão no nível do conjunto; 7 membros do conjunto em hora cheia;
  - PCH Bandeirante: 62.064 horas da geração do conjunto, em 3 trechos, com 744 ausentes.

## Constitution Check

| Princípio / requisito da constituição 3.1.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | spec aprovada, para todos os tipos, com a aplicabilidade por tipo; este plano descreve o código atual. Lê só os resultados da Coleta (inclusive a cópia do dicionário da EVT), grava só na sua pasta e, sem a Coleta concluída no formato atual, sai com 5 sem gravar. Não acessa o portal nem `data/raw/` (`tests/integracao/test_sem_raw.py`) |
| II. Relatório fiel aos dados | cumpre | o relatório de validação sai dos resultados das regras e do perfil (nome, `cod_usina`, limites), sem conclusão fixa e com números no padrão brasileiro |
| III. Uma usina por execução, definida pelo perfil | cumpre | `--usina` escolhe o perfil; o tipo e a `[cobertura]` dele definem os conjuntos tratados; limites de R6 e R8, cabeçalho do relatório, aba da planilha, códigos de planejamento e subsistema vêm dele; tolerâncias em `src/comum/regras.py`; nenhum valor de usina no código (`tests/comum/test_literais.py`) |
| IV. Coleta completa e rastreável | cumpre, no que toca à etapa | toda linha tratada mantém `arquivo_origem` (nas séries, o arquivo do valor mantido); a auditoria da Coleta é preservada linha a linha e completada |
| V. Tratamento sem descarte | cumpre | R6 a R9, D1 a D4, H1 a H4, G1, R7 da base horária, `sinal_cvu`, `sinal_recurso_invalido`, `sinal_estimada_ausente`, `sem_marca_restricao` e as sinalizações do fator de capacidade sinalizam e não excluem; a spec declara o que sai do uso. Convenção de hora, duplicatas e recorte estão na spec e valem para todos os conjuntos; ausências listadas por conjunto |
| VI. Conferência entre fontes | não se aplica | a etapa não compara fontes; isso é da Conferência |
| VII. Relatório padronizado | não se aplica | a etapa não produz o relatório nem figuras |
| VIII. Granularidade declarada | cumpre | a base horária, o fator de capacidade e a razão trazem o nível de cada linha; a energia cortada é sempre da usina; a R7 só compara grandezas da usina; com a restrição com detalhe como série de referência, os dados do conjunto não entram na base da usina; nada é dividido entre as usinas |
| IX. Relatórios aprovados protegidos | cumpre | na hidrelétrica com EVT, nenhum arquivo nem coluna mudou; informação nova vai para arquivos novos; o `comparar --todas` refaz a etapa a partir da Coleta congelada de cada referência, sem diferença nos cinco relatórios aprovados |
| RT 1. Python ≥ 3.11, `venv`, dependências mínimas, regras só em Python | cumpre | quatro dependências de dados; `requirements.txt` conferido contra os imports (`tests/comum/test_conformidade.py`) |
| RT 2. Windows e PowerShell | cumpre | caminhos com `pathlib`; troca atômica na mesma pasta; exemplos em PowerShell |
| RT 3. Gravação segura | cumpre | `.bak` da versão anterior, conteúdo idêntico não regravado, conferência no disco e restauração em falha, inclusive na interrupção pelo usuário (D13), para todos os arquivos de dados, de todos os tipos |
| RT 4. Versões dos brutos | não se aplica | é da Coleta |
| RT 5. Cópias de segurança do projeto | não se aplica | ferramenta comum, descrita na spec da Coleta |
| RT 6. Pastas | cumpre | grava só em `data/usinas/<slug>/tratamento/` |
| RT 7. Log | cumpre | log na saída padrão, com arquivos, linhas, resultados das gravações e avisos; o nível de `--log-level` vale também para os loggers dos módulos da etapa, importados só na execução (ver o [contrato](contracts/cli-tratamento.md)) |
| Testes sem rede para cada etapa e uma usina fictícia por tipo | cumpre | testes da etapa, da persistência e as sete usinas fictícias de ponta a ponta |
| Entrega: suíte aprovada, execução real e comparação com as referências | cumpre | suíte aprovada; execuções reais registradas nos `etapa.json`; os cinco relatórios de referência sem diferença |
| Recuperação do último estado íntegro | cumpre | `.bak` da versão imediatamente anterior de cada arquivo |

## Project Structure

### Documentation (this feature)

```text
specs/002-tratamento-dados/
├── spec.md                  # requisitos aprovados (o quê), com a aplicabilidade por tipo
├── plan.md                  # este arquivo (como)
├── data-model.md            # entradas, saídas, objetos, etapa.json e regras
├── contracts/
│   └── cli-tratamento.md    # linha de comando da etapa
└── checklists/
    └── requirements.md      # qualidade da spec
```

### Source Code (repository root)

```text
src/tratamento/
├── __init__.py              # pacote da etapa 2
├── etapa.py                 # executar_tratamento: escolhe o caminho pela série de referência e monta o resumo
├── evt.py                   # tratar_evt: tipagem, parada por R1, sinalização e base em três formatos
├── validacao.py             # dicionário da EVT (o da Coleta), regras R1 a R9, sinalização e relatório de validação
├── series.py                # motor das séries horárias: hora de início, duplicatas, recorte, ausências, auditoria
├── disponibilidade.py       # regras D1 a D4 e série de disponibilidade
├── hidrologia.py            # regras H1 a H4, exclusão campo a campo (limpos) e série hidrológica
├── geracao.py               # regra G1 e série de geração
├── indicadores.py           # indicadores por UG, horas por estado, TEIFa e TEIP; CSV e indicadores.xlsx
├── programacao.py           # patamares → horas, soma dos códigos vigentes e dias sem arquivo
├── base_horaria.py          # base horária comum das usinas sem EVT, com nível, trecho e sinalizações
├── termica.py               # despacho por unidade e somado, CVU, CMO, semanas operativas e semanais em hora
└── renovavel.py             # restrição semi-horária e em hora cheia, energia cortada, razão, fator de capacidade, membros

src/comum/                   # partes comuns usadas pela etapa
├── persistencia.py          # gravação segura de dados (descrita nesta spec; usada também pela Coleta)
├── caminhos.py              # pastas e nomes: ARQUIVOS_COLETA, ARQUIVOS_TRATAMENTO, dicionario_evt()
├── regras.py                # tolerâncias e limiares gerais
├── perfil.py                # perfil e valores derivados (limites de R6, produtividade nominal, códigos de planejamento)
├── formatacao.py            # números e datas no padrão brasileiro (relatório de validação)
└── logger.py                # loggers e nível único
src/pipeline.py              # executar_etapa: pré-requisito, VERSAO_FORMATO, etapa.json, códigos de saída
src/__main__.py              # linha de comando única
src/coleta/registro.py       # registro dos conjuntos: DescricaoConjunto, descricoes(perfil), conjuntos_da_usina, nivel_coletado,
                             # tipo_da_usina e as colunas de cada conjunto, compartilhados com a Coleta
src/coleta/serie_referencia.py  # escolher(perfil): a série de referência e os níveis dela
src/coleta/conjuntos.py      # coluna do instante e período coberto por cada arquivo (motor da Coleta)
src/coleta/indicadores.py    # separar_conjuntos e os nomes dos quatro conjuntos de indicadores
src/coleta/programacao.py    # nome da coluna do código de programação

tests/tratamento/
├── test_evt.py              # tipagem (vírgula, espaços, vazio), instante inválido, três formatos, nome da aba, R1 sem gravar
├── test_validacao.py        # dicionário, faixa de R8, cada regra R1 a R9, ausentes, sinalização, Markdown
├── test_series.py           # hora de início (23:59), duplicatas, recorte, ausências, falhas na auditoria, leitura
├── test_qualidade.py        # D1 a D4, H1 a H4 com exclusão campo a campo, G1
├── test_indicadores.py      # número da UG, versão mais recente das horas e das taxas, recorte
├── test_programacao.py      # média dos patamares e contagem por hora; soma dos códigos vigentes no dia
├── test_base_horaria.py     # colunas, nível do conjunto, R7 sinalizada e mantida, ausências, soma dos códigos
├── test_termica.py          # despacho por unidade e somado, CVU pela revisão com o sinal, CMO, semanas em hora
└── test_renovavel.py        # energia cortada, sem a marca, hora cheia, recurso inválido, estimativa ausente, razão,
                             # fator de capacidade, restrição como série de referência, membros, gravação e leitura
tests/comum/
├── test_persistencia.py              # NOVO, ALTERADO, INALTERADO, falhas e Ctrl+C com restauração, planilha, Parquet, texto
├── test_persistencia_gravadores.py   # cada gravador guarda a versão anterior; leitores ignoram .bak e .tmp
├── test_conformidade.py              # dados gravados só pela persistência; nível de log mantido; dependências
├── test_literais.py                  # nenhum valor das usinas reais no código
└── test_pipeline.py                  # pré-requisito (código 5), interrupção (código 1) e etapa.json
tests/integracao/
├── test_cli.py                       # comando aceito; opção retirada recusada com código 2
├── test_usina_ficticia.py            # fluxo completo de uma usina fictícia de três UGs, sem programação nem São Domingos
├── test_usinas_ficticias.py          # as sete usinas fictícias, uma por tipo, de ponta a ponta
└── test_sem_raw.py                   # etapas 2 a 5 com data/raw/ vazio
tests/fixtures/
├── usinas_ficticias/<tipo>/perfil.toml   # perfis fictícios de UHE, PCH, CGH, UTE, UTN, EOL e UFV
├── brutos_ficticios.py                   # brutos sintéticos de todos os conjuntos
└── sem_evt.py                            # etapas das usinas fictícias sem EVT numa pasta temporária
```

## Fluxo de execução

1. `src/__main__.main` lê as opções (inválida: código 2), aplica `--log-level` (`configurar_nivel_log`) e carrega o perfil (`carregar_perfil`; inválido ou em rascunho: código 4).
2. `src/pipeline.executar_etapa("tratamento", perfil)` lê `coleta/etapa.json` (`etapa_anterior_concluida`). Ausente, ilegível, com `status` diferente de `concluida` ou com `versao_formato` diferente do atual (2): mensagem e código 5, nada gravado. Senão, define o perfil ativo, importa e chama `executar_tratamento(perfil)`; qualquer exceção, ou a interrupção pelo usuário (Ctrl+C), vira código 1.
3. `executar_tratamento` abre `registrar_gravacoes()`, que guarda o arquivo e o resultado de cada gravação, e escolhe o caminho pela série de referência (`serie_referencia.escolher(perfil)`): EVT (passos 4 a 7) ou sem EVT (passo 8).
4. **EVT**: `evt.tratar_evt(perfil, coleta/evt_extraido.csv, destinos)`:
   - `validacao.carregar_base_consolidada`: coluna obrigatória ausente gera `ValueError`; sem `arquivo_origem` ou `tipo_match`, só aviso;
   - `carregar_dicionario_dados(coleta/dicionario_evt.json)` e `verificar_colunas_no_dicionario`: sem o JSON, `FileNotFoundError`; grandeza fora do dicionário, só aviso;
   - `padronizar_tipagem_numerica`: instante inválido gera `ValueError`;
   - `validar_regras_fisicas` devolve a tabela das nove regras e os `RegraResultado`; com violação de R1, log de erro e código 1, antes de qualquer gravação;
   - `sinalizar_anomalias`, e então são gravados `validacao_fisica.md` (com a versão do mesmo dicionário), `validacao_fisica.csv`, `evt_tratado.xlsx`, `evt_tratado.parquet` e `evt_tratado.csv`.

   O primeiro e o último `din_instante` da EVT formam o período de referência.
5. **Indicadores**: `indicadores.montar_indicadores` sobre `indicadores_extraido.parquet` (`separar_conjuntos` → `tratar_indicadores_ug` mensal e anual, `tratar_horas_estado`, `tratar_taxas` → `recortar_periodo` → potência nas horas por estado → aviso de resíduo) e `exportar_indicadores` (quatro CSV e `indicadores.xlsx`).
6. **Programação**: `programacao.montar_programacao` sobre `programacao_extraido.parquet` (com mais de um código, `somar_codigos` antes da média) e a auditoria da Coleta (`ler_auditoria_coleta(..., ["dia"])`), e `exportar_programacao` (dois CSV).
7. **Séries horárias**, nesta ordem: disponibilidade, hidrologia e geração. Para cada uma, `tratar_<conjunto>(descricoes(perfil)[conjunto], extraído, auditoria da Coleta, início, fim, pasta)` chama `series.montar_serie` (hora de início, uma hora por instante, recorte, `listar_ausencias`, auditoria), acrescenta a coluna `qualidade` e chama `exportar_serie` (série, ausências e auditoria).
8. **Sem EVT** (`_tratar_sem_evt`): o período é o `periodo` do `resumo` do `etapa.json` da Coleta; só os conjuntos de `conjuntos_da_usina(perfil)` são tratados, nesta ordem:
   - indicadores e programação, como nos passos 5 e 6;
   - disponibilidade, hidrologia e geração, como no passo 7;
   - eólicas e solares (`_tratar_renovavel`): `tratar_fator_capacidade` (motor das séries, nível e sinalizações), `montar_razao`, `montar_restricao` (com a razão da mesma semi-hora) e, com `restricao_membros_extraido.parquet`, `montar_membros`; `exportar_renovavel` grava a restrição (semi-horária, horária, ausências e auditoria), a razão e os membros;
   - base horária: a série de referência é a geração tratada ou, na restrição com detalhe, `serie_da_referencia(restricao)`, com a disponibilidade e a programação só quando estão no nível da usina; `montar_base_horaria` junta o nível de `geracao_complemento.parquet`, a disponibilidade, a programação e o trecho de `trechos.csv`, e `exportar_base_horaria` grava `base_horaria.csv`;
   - térmicas (`_tratar_termica`): `montar_despacho` (códigos de `[[identificacao.planejamento]]`), `montar_cvu` e `montar_cmo` (subsistema do perfil); `exportar_termica` grava os arquivos de cada um.
9. O `resumo` é montado (FR-033; `_resumo_serie` nas séries; `resumo_base_horaria`; os resumos do despacho, do CVU, do CMO e da restrição; `gravacoes` conta os resultados) e volta em `ResultadoEtapa(0, arquivos, resumo)`.
10. `executar_etapa` grava o `etapa.json` (`concluida`; com código 1, `falha`), no formato 2, marca como `desatualizada` as etapas seguintes que já existirem e registra no log o resumo e a pasta.

Código diferente de 0: 2 e 4 no passo 1; 5 no passo 2; 1 com R1 no passo 4, com qualquer exceção (coluna obrigatória, dicionário, instante inválido, extraído ilegível, `ErroPersistencia`) ou com Ctrl+C. Um erro ou uma interrupção depois do passo 4 (ou durante o passo 8) deixa gravados os arquivos anteriores a ela; o arquivo que estava sendo gravado volta à versão anterior.

## Decisões técnicas

### D1 — Fronteira com a Coleta
- **Decisão**: a Coleta identifica a usina, lê os números sem arredondar, marca os valores não numéricos (`_nao_numerico`) e audita cada arquivo. O Tratamento aplica a convenção de hora, resolve as horas repetidas entre arquivos, recorta o período, lista as ausências, sinaliza a qualidade e completa a auditoria (`horas_usina`, `duplicatas_conflitantes`). A EVT chega consolidada pela Coleta (ordem cronológica, sem hora repetida). As descrições dos conjuntos (`DescricaoConjunto`: colunas de valor, convenção de hora e nível), os conjuntos da usina e a separação dos quatro conjuntos de indicadores (`separar_conjuntos`) são declarados uma vez no pacote da Coleta (`src/coleta/registro.py`) e reusados aqui. Nos conjuntos novos, a Coleta entrega as linhas como publicadas: as semi-horárias em 30 minutos, o CVU com todas as revisões e o CMO com todas as publicações; levar à hora e escolher a revisão é do Tratamento.
- **Motivo**: cada spec descreve uma etapa inteira; alinhar os horários é tratamento, não extração. Um motor único (`series.montar_serie`) evita triplicar código e testes.
- **Alternativas rejeitadas**: extração e tratamento juntos nos conjuntos complementares (a spec da Coleta passaria a descrever tratamento).

### D2 — Período de referência
- **Decisão**: na hidrelétrica com EVT, o período vai do primeiro ao último `din_instante` da EVT tratada. Nas usinas sem EVT, é o `periodo` que a Coleta grava no `resumo` do `etapa.json` (a série de referência do tipo, FR-054 da spec da Coleta de dados); o Tratamento não o recalcula. As séries horárias e a programação ficam só nesse intervalo, inclusive nas pontas; as tabelas mensais, do mês inicial ao final; a anual, do ano inicial ao final; as semi-horárias, as semi-horas das horas do período; o CVU e o CMO, as semanas operativas que se sobrepõem a ele.
- **Motivo**: decisão do usuário (a extensão da geração para antes da EVT foi recusada); as bases ficam alinhadas hora a hora com a série de referência, e a escolha dela fica num lugar só, a Coleta.

### D3 — Tipagem da EVT sem fabricar valores
- **Decisão**: `padronizar_tipagem_numerica` apara os textos; `cod_usina` vira `Int64` (inválido fica vazio, com aviso); `din_instante` vira data e hora sem fuso (inválido gera `ValueError`, código 1); as dez grandezas viram `float64` com `pd.to_numeric(errors="coerce")`, depois de trocar vírgula por ponto e aparar espaços. Ausentes ficam `NaN`, contados no log por coluna.
- **Motivo**: zero no lugar de ausente fabricaria uma medição (uma hora sem dado pareceria usina parada); um instante inválido não tem lugar na série.
- **Alternativas rejeitadas**: preencher com zero, remover a linha ou interpolar.

### D4 — Base de EVT em três formatos
- **Decisão**:
  - Parquet: `double`, `int64`, `timestamp[us]` e `bool`.
  - Planilha: números nativos no formato "General", instante como data e hora, cabeçalho congelado e largura das colunas pelo cabeçalho. A aba se chama `nome_aba(perfil)`: `usina.nome` sem acentos, em maiúsculas, com `_` no lugar dos espaços e dos caracteres que o Excel não aceita em nome de aba (`CARACTERES_PROIBIDOS_ABA`: `\ / ? * : [ ]`), cortado em 31 caracteres (`TAMANHO_MAXIMO_ABA`).
  - CSV: `;`, ponto decimal, ausente como célula vazia e o número real de 64 bits com todas as suas casas. A EVT extraída é lida pelo conversor padrão do pandas, que pode mudar só o último algarismo significativo do texto; os três formatos guardam esse mesmo número.
- **Motivo**: o Excel em português usa vírgula e o ONS publica com ponto; o CSV arredondado impediria refazer R4 e R5 com ε = 0,0001. O nome da aba e a leitura dos números são decisões do usuário. O nome normalizado vale para qualquer usina, e como o arquivo tem uma aba só, o corte em 31 caracteres não gera nome repetido. A leitura atual mantém os dados tratados e o relatório aprovados; na São Domingos, 81.692 dos 708.950 valores diferem do texto extraído em 1 ulp, cerca de 10⁻¹⁶ em termos relativos.
- **Alternativas rejeitadas**: só CSV com vírgula decimal (quebraria Python, R e Power BI); CSV arredondado; parar com código 1 diante de um nome de aba inválido (obrigaria a encurtar `usina.nome`, que também dá o título do relatório); conversão exata na leitura (mudaria esses valores em `evt_tratado.*`, sem ganho para o relatório, cujos números saem arredondados).

### D5 — Regras R1 a R9: sinalizar, nunca excluir
- **Decisão**: `validar_regras_fisicas` avalia 100 % dos registros, contando registros e não células. R6 a R9 saem de uma só função de máscaras (`mascaras_plausibilidade`), usada tanto na contagem quanto nas colunas `anomalia_*` e `qualidade_registro` (`sinalizar_anomalias`); ausentes não violam. Violação de R1 encerra com código 1 antes de qualquer gravação, porque a etapa só usa os códigos 0, 1 e 5; R2 a R9 vão ao relatório e ao log, sem mudar o código.
- **Motivo**: R1 a R5 mostram só a coerência de cálculo entre colunas do ONS; uma geração impossível passa por elas e só aparece contra os parâmetros da usina. Um registro sinalizado é indício, não erro confirmado, e removê-lo mudaria os totais publicados. Valor negativo é impossível por definição e põe a base inteira em dúvida.
- **Alternativas rejeitadas**: detecção estatística de outliers (menos verificável em campo); remover ou corrigir registros (não há fonte para o valor correto).

### D6 — Limites pelo perfil, tolerâncias gerais e dicionário só como referência
- **Decisão**: os limites de R6 e a faixa de R8 são propriedades do perfil (`limites_fisicos_superiores`, `produtividade_nominal_mw_m3s`); ε, a folga de 5 %, a faixa de 70 % a 130 % e o 1,0 MW de R7 ficam em `src/comum/regras.py`; R9 usa o mesmo 1,0 MW da usina parada (`LIMIAR_GERACAO_PARADA_MW`). O dicionário da EVT só confirma as dez colunas e dá a versão citada no relatório.
- **Motivo**: limites conferíveis pelo fiscal e coerentes se um parâmetro for corrigido; relatórios comparáveis entre usinas. O dicionário traz código, descrição e unidade, sem faixas de valores.

### D7 — Relatório de validação gerado dos números
- **Decisão**: `gerar_relatorio_validacao_md` monta título e cabeçalho pelo perfil, a tabela das nove regras, uma frase por regra (`_frase_regra`), a ressalva sobre R1 a R5 e R6 a R9 e os 40 primeiros sinalizados em ordem cronológica, com `fmt_num`, `fmt_int` e `fmt_pct`. `gerar_relatorio_validacao_csv` grava a mesma tabela com a taxa em 4 casas e os desvios em 6.
- **Motivo**: o texto diz o que os dados mostram, sem conclusão anunciada antes da execução.

### D8 — Hora de início em todas as séries
- **Decisão**: EVT, disponibilidade, geração, despacho, fator de capacidade e as semi-horárias das restrições já vêm na hora de início. A hidrologia (`convencao_hora="fim"`) passa por `hora_de_inicio`: instante arredondado para cima até a hora cheia, menos 1 h (01:00 → 00:00; 23:59 → 23:00 do mesmo dia); o publicado fica em `din_instante_publicado`. Na programação, a hora vem do número do patamar (D12).
- **Motivo**: na base real da São Domingos (jan/2025), com a conversão, turbinada e vertida coincidem com a EVT em 744 de 744 h; sem ela, a turbinada coincide em 374.
- **Alternativas rejeitadas**: recuar 1 h sem tratar o 23:59 (a última hora de cada dia sairia do lugar).

### D9 — Uma hora por instante e ausências listadas
- **Decisão**: `montar_serie` ordena por instante e pela ordem de leitura da Coleta (as linhas obtidas da auditoria, já em ordem de data de publicação e de nome) e fica com a última ocorrência. A repetição com algum valor diferente (vazio igual a vazio) é contada, antes do recorte, em `duplicatas_conflitantes` do arquivo descartado. `listar_ausencias` compara a série com a grade horária do período: mês inteiro ausente é `MES_SEM_USINA` se algum arquivo obtido cobre o mês (o anual cobre os doze), senão `MES_SEM_ARQUIVO`; nos demais meses, cada intervalo contínuo é `HORAS`. A hora que não existe no início do horário de verão aparece como ausente.
- **Motivo**: o ONS republica arquivos, e o publicado por último é o vigente. Série mais ausências cobrem 100 % do período, sem hora repetida nem interpolada (SC-004).

### D10 — Qualidade das séries: o que sai do uso, e onde
- **Decisão**: a coluna `qualidade` traz `OK` ou os códigos separados por vírgula: D1 a D4 e G1 tiram a hora inteira; H1, H2 e H4, só o campo afetado; H3 marca um valor não numérico, que já chega vazio da Coleta. O arquivo guarda os valores como vieram, e a exclusão é aplicada na leitura pelas etapas seguintes: na disponibilidade e na geração entram só as horas `OK` (`conferencia.disponibilidade.validas`, usada pela Conferência e pelas Análises, e o filtro da conferência da geração); na hidrologia, `hidrologia.limpos` (conferência das vazões e Análises). H4 compara cada nível com a mediana da própria série no período (10 m).
- **Motivo**: as regras da disponibilidade envolvem os três campos. Na hidrologia, uma hora com volume útil impossível pode ter vazões válidas (na São Domingos, volume útil negativo em 2019, numa parada com o reservatório rebaixado). Leituras trocadas de nível (na São Domingos, montante de 308,67 m e jusante de 3,09 m e 730,9 m) distorciam o perfil horário; um rebaixamento real de poucos metros não deve ser sinalizado.
- **Alternativas rejeitadas**: excluir a hora inteira na hidrologia (perderia vazões válidas); faixa fixa de nível (dependeria da usina).
- **Limitação conhecida**: a Coleta não converte vírgula decimal nos conjuntos horários; um valor assim chega vazio e marcado como não numérico, e o Tratamento o sinaliza como D4, H3 ou G1.

### D11 — Indicadores: versão mais recente e resíduo só avisado
- **Decisão**: nos indicadores por UG, a chave é (mês ou ano, UG) e fica a última linha na ordem de leitura (arquivos em ordem de nome), com aviso. Nas horas por estado, a UG é o número no fim de `nom_unidadegeradora` (`numero_ug`), fica o maior `num_versao` por (mês, UG, estado), e `residuo_identidade_h` = HP − (HS + HRD + HDP + HDF + HDCE + HEDP + HEDF); acima de 0,1 h em valor absoluto (`TOLERANCIA_IDENTIDADE_HORAS`, em `src/comum/regras.py`), só aviso. A potência vem dos indicadores mensais do mesmo mês. Nas taxas, fica o maior `num_versao` por (mês, taxa). `indicadores.xlsx` traz a aba `SIGLAS_HORAS` (`INSUMOS_HORAS`), porque o dicionário do ONS não define as siglas. Nas térmicas, o mesmo código, pelo CEG.
- **Motivo**: o ONS republica os parâmetros e as taxas com nova versão. A identidade é conferida sem descartar meses; o recálculo das taxas e a divergência DISPF × horas são da Conferência.

### D12 — Programação: patamares em horas
- **Decisão**: hora de início = dia do arquivo + ((patamar − 1) // 2) h; valor = média dos patamares da hora; `patamares` = quantos formam a hora (2 = completa). Os dias ausentes vão do primeiro dia com arquivo obtido ao último dia do período. Com mais de um código, a soma por patamar vem antes (D20).
- **Motivo**: o patamar 1 é 00:00–00:30. Na base real da São Domingos (jul/2026), 222 das 232 horas de usina parada com EVT coincidem com programação zero, o que confirma o alinhamento (1 h de defasagem descasaria as bordas das paradas). A programação pode começar depois da série de referência (na São Domingos, em 01/10/2024).
- **Alternativas rejeitadas**: usar só o primeiro patamar de cada hora (perde as reprogramações de meia hora).

### D13 — Gravação segura
- **Decisão**: todo arquivo de dados passa por `persistencia._gravar_com_copia`:
  1. grava `<nome>.tmp` na mesma pasta e o confere (CSV relido: linhas e colunas; Parquet: metadados; planilha: abas, dimensões e assinatura; texto: igual ao pretendido);
  2. se o conteúdo é igual ao atual, apaga o temporário e registra `INALTERADO`, sem tocar no arquivo nem no `.bak`;
  3. senão, copia o atual para `<nome>.bak.tmp`, troca o destino pelo temporário (`Path.replace`, atômica na mesma unidade), confere o SHA-256 e só então promove `<nome>.bak.tmp` a `<nome>.bak`;
  4. em qualquer falha, inclusive a interrupção pelo usuário (Ctrl+C), volta a versão anterior (ou apaga o arquivo que não existia) e remove os temporários; o erro vira `ErroPersistencia`, e a interrupção segue para `executar_etapa`. Nos dois casos, a etapa grava o `etapa.json` com `falha` e sai com 1.

  CSV, Parquet e texto são comparados byte a byte, sem cache; a planilha, pela propriedade `assinatura_dados` (SHA-256 do nome e do CSV de cada aba, na ordem). Os arquivos das usinas sem EVT, das térmicas e das eólicas e solares são CSV gravados por `gravar_csv`, com a mesma regra.
- **Motivo**: recuperar o estado anterior se o código falhar ou a execução for interrompida, sem acumular cópias, e sem que reexecuções apaguem a versão anterior. A planilha muda de bytes a cada gravação (datas internas), e reler as 70.895 × 25 células da EVT custaria cerca de 18 s; a assinatura é lida em milissegundos.
- **Alternativas rejeitadas**: copiar sempre para `.bak` (reexecuções apagariam a versão anterior); `.bak` datados acumulados (recusados pelo usuário); registro externo de assinaturas (mais um arquivo de controle); `filecmp.cmp` (o cache por tamanho e data dava `INALTERADO` falso).

### D14 — Formatos estáveis e leitura pelas etapas seguintes
- **Decisão**: as saídas são CSV com `;` e, na EVT, Parquet, planilha e CSV. As etapas seguintes leem pelos leitores do próprio pacote (`carregar_disponibilidade_tratada`, `carregar_hidrologia_tratada`, `carregar_geracao_tratada`, `carregar_indicadores_tratados`, `carregar_programacao_tratada`, `carregar_base_horaria`, `carregar_despacho_tratado`, `carregar_semanal_tratado` e `carregar_renovavel`), pelo Parquet da EVT e pelo `validacao_fisica.csv`, sempre por nome explícito: `.bak` e `.tmp` nunca são lidos como dado. Leitor de conjunto não tratado devolve `None`.
- **Motivo**: os valores que chegam à Conferência e às Análises são os mesmos da base de referência; com saídas determinísticas, a reexecução sem mudança fica 100 % `INALTERADO`.

### D15 — Base horária comum das usinas sem EVT
- **Decisão**: `base_horaria.montar_base_horaria` grava uma linha por hora da série de referência tratada: a geração por usina tratada ou, quando a restrição com detalhe é a série de referência, `renovavel.serie_da_referencia` (a geração verificada da usina em hora cheia). O nível de cada hora vem de `geracao_complemento.parquet` (sem ele, o primeiro nível da série escolhida); a disponibilidade e a programação horária entram quando foram tratadas; o trecho vem de `trechos.csv` (o primeiro trecho que contém a hora). `sinalizacoes` junta a `qualidade` da geração (G1) e a da disponibilidade (D1 a D4) e a R7 (geração > disponibilidade operacional + `TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW`), só nas horas de nível `usina`. As horas ausentes ficam nas ausências da série de referência; nada é preenchido.
- **Motivo**: as Análises da hidrelétrica partem da base de EVT, que os outros tipos não têm; as seções comuns e as regras comuns da conclusão (a geração acima da disponibilidade declarada e a indisponibilidade total) precisam de uma base horária única. A R7 só compara grandezas do mesmo nível (princípio VIII).
- **Alternativas rejeitadas**: simular uma base de EVT com colunas vazias (esconderia o tipo da usina nas Análises e arriscaria textos de hidrelétrica em outros tipos).

### D16 — Séries novas: resolução, hora, versão e sinalizações
- **Decisão**:
  - **Semi-horárias** (restrição com detalhe): gravadas na resolução de 30 minutos, no instante de início (00:00 a 23:30, conferido nos dados do ONS), e também em hora cheia pela média das duas meias-horas (`renovavel.em_hora_cheia`); a hora com uma só meia-hora com a geração verificada fica fora e é contada nas ausências.
  - **Convenção de hora** do despacho, do fator de capacidade e das semi-horárias: início do intervalo, como na geração por usina. A G4 confirma no despacho: na UTE William Arjona, 99,7 % de coincidência com a geração por usina, que cai para 92,9 % com uma hora de deslocamento. Deslocamento melhor vira correção, nunca ajuste automático.
  - **Uma linha por chave**: `termica._sem_repeticoes` fica com a linha do arquivo publicado por último (ordem da auditoria da Coleta) e conta, por arquivo, as descartadas com valor diferente, como o motor das séries (D9): no despacho, por hora e código; no CVU, por código, semana e revisão; no CMO, por semana; na restrição com detalhe e na razão, por semi-hora. Na razão, a contagem não é gravada.
  - **CVU**: um valor por unidade de planejamento e semana operativa, o da revisão mais recente (`num_revisao`); `revisoes` diz quantas a semana teve.
  - **CMO**: um valor por semana operativa, o da publicação mais recente. A data publicada é a sexta-feira que fecha a semana, embora o contrato do ONS diga "início"; `inicio_da_semana_operativa` põe o CMO na semana (sábado a sexta) que contém a data, o que vale nos dois casos. As semanas repetidas entre publicações são contadas.
  - **Semanais em hora**: `termica.semanal_em_horas` leva o CVU e o CMO à hora pelo intervalo da semana operativa, só para os cruzamentos das Análises; nada é gravado em hora.
  - **Sinalizações, sem descarte**: recurso marcado como inválido pelo ONS, fator de capacidade fora de 0 a 1, geração acima da capacidade instalada (folga de 1 MW, a da R7), CVU ausente, zero ou negativo.
  - **Ausências**: `listar_ausencias`, o mesmo das séries, no fator de capacidade, na restrição em hora cheia e no despacho, por código no período dele; nas semanais, as semanas ausentes em intervalos contínuos.
- **Motivo**: o princípio V pede a convenção de hora, as duplicatas e o recorte declarados e aplicados a todos os conjuntos. A resolução publicada fica para as análises por semi-hora; a hora cheia serve aos cruzamentos com as séries horárias.
- **Alternativas rejeitadas**: converter tudo para hora na Coleta (perderia a resolução publicada e misturaria etapas).

### D17 — Energia cortada e razão da restrição
- **Decisão**:
  - energia cortada = máx(estimada − verificada, 0) × 0,5 h (`DURACAO_SEMI_HORA_H`) só nas semi-horas com `flg_geracaorestrita = 1`; nas demais, 0; sem a coluna da marca (fotovoltaica de 05 a 12/2024), `sem_marca_restricao` e vazia;
  - estimativa ausente (decisão do usuário de 21/10/2026): estimada 0 com verificada acima de `LIMIAR_GERACAO_PARADA_MW` vira `sinal_estimada_ausente`; a estimada sai da média da hora cheia e, na semi-hora restrita, a energia cortada fica vazia;
  - a razão (REL, CNF, ENE) e os minutos de cada uma vêm da restrição com a razão, na mesma semi-hora, com o nível dela (`nivel_razao`); quando a razão é do conjunto, a energia cortada continua sendo a da usina.
- **Motivo**: na EOL Praia Formosa, de 10/2021 a 10/2026, a energia cortada nas semi-horas restritas é de 184.769 MWh, e a diferença bruta, de 355.038 MWh: somar a bruta quase dobraria o corte. A razão só existe na base sem detalhe. O ONS publica estimada 0 em semi-horas em que a usina gerou (na UFV Seriemas 1, 341 das 609 semi-horas com irradiância acima de 200 W/m², nos primeiros meses de operação).
- **Alternativas rejeitadas**: a diferença bruta em todas as semi-horas (superestima o corte); `val_geracaoreferenciafinal` (só nas restrições REL já apuradas, nula na maior parte das linhas).

### D18 — Térmicas: unidades de planejamento e códigos no tempo
- **Decisão**: o despacho da usina é a soma das unidades de planejamento por hora (`somar_unidades`, com `min_count=1`: a coluna sem valor em todas as unidades fica vazia), com `unidades` e `codigos` de cada hora; o arquivo por unidade fica ao lado, para o CVU por unidade nas Análises. Cada código de `[[identificacao.planejamento]]` (meses `AAAA-MM`; fim vazio, vigente) entra só na interseção do período dele com o da usina (`_limites_do_codigo`), e as ausências do despacho e do CVU são listadas por código. O código publicado ora inteiro, ora decimal, é comparado como número. O CMO é o do subsistema do perfil (`usina.subsistema`). Os totais publicados (`val_proggeracao`, `val_verifgeracao`) e as parcelas de cada motivo ficam como vieram.
- **Motivo**: a UTE William Arjona teve três códigos de planejamento (34 até 08/2018; 334 desde 07/2021; 434, a unidade a óleo, de 08/2021 a 01/2026); somar só os vigentes não mistura unidades de outra época e deixa as lacunas visíveis (o 434 sem despacho de 01 a 26/08/2021 aparece como ausência). Os motivos não formam uma partição exata (em cerca de 8 % das horas de 2026, a ordem de demérito acima da inflexibilidade toma o lugar da ordem de mérito na soma), por isso nada é forçado a fechar.

### D19 — Eólicas e solares: a base da usina e o contexto do conjunto
- **Decisão**:
  - o fator de capacidade passa pelo motor das séries (`series.montar_serie`), com o nível declarado na cobertura e as duas sinalizações; o fator calculado a partir da geração da usina e da capacidade do perfil é das Análises;
  - com a restrição com detalhe como série de referência, a base horária vem dela, e a disponibilidade e a programação entram só quando coletadas no nível da usina (`nivel_coletado`): a base é da usina, e os números do conjunto ficam nos arquivos próprios, com o nível;
  - o recurso marcado como inválido pelo ONS é sinalizado e mantido; o limite físico do recurso (40 m/s; 1.500 W/m²) não é aplicado no Tratamento, mas pelas Análises, no recurso × geração;
  - os membros do conjunto (`restricao_membros_extraido.parquet`) vão à hora cheia, por id ONS, só para a G2, sem entrar na base.
- **Motivo**: princípio VIII: nível em todo número, nada de conjunto dividido nem misturado aos dados da usina; a G1 e a G2 comparam fontes só no mesmo nível.

### D20 — Programação com vários códigos
- **Decisão**: com `cod_exibicaousina` na extração (mais de um código), `programacao.somar_codigos` soma os códigos por dia e patamar antes da média da hora. Cada código vale do primeiro ao último dia em que aparece na extração; o patamar só tem soma quando todos os códigos vigentes no dia têm valor nele; senão, a soma fica vazia. Com um código, nada muda.
- **Motivo**: o conjunto Chapadão é programado em quatro códigos, um por barra, e trocou os quatro em 07/2025 (`MSCAO-9761`, `-9762`, `-9763` e `-9766` até 02/07/2025; `MSCAO-9764`, `-9765`, `-9784` e `-10205` desde 05/07/2025). Completar um código sem valor fabricaria programação (princípio V). Os quatro códigos têm o mesmo valor em todos os patamares (o programado do conjunto dividido em partes iguais): a soma é do conjunto, nunca da usina.
- **Alternativas rejeitadas**: exigir todos os códigos da lista em todos os dias (deixaria a programação da PCH Bandeirante inteira sem soma); completar o código ausente.

### D21 — Formato 2 e nada de `data/raw/`
- **Decisão**: o dicionário da EVT vem de `coleta/dicionario_evt.json`, passado a `carregar_dicionario_dados` e a `gerar_relatorio_validacao_md`; o padrão dessas funções em `data/raw/` fica só para as chamadas diretas dos testes. `pipeline.VERSAO_FORMATO["tratamento"]` = 2, porque as Análises passam a exigir a base horária; a Coleta no formato 1 é recusada com o código 5. Na hidrelétrica com EVT, os arquivos e as colunas não mudam: informação nova vai para arquivos novos.
- **Motivo**: `data/raw/` é compartilhado por todas as usinas: a coleta de outra usina mudaria o que o Tratamento lê, e ele não rodaria sem o dicionário lá (princípio I). O formato de uma etapa muda quando um arquivo dela muda ou quando a etapa seguinte passa a exigir um arquivo novo; arquivo novo opcional não muda o formato. Arquivos novos protegem os relatórios aprovados (princípio IX).
- **Alternativas rejeitadas**: camadas de compatibilidade de leitura do formato antigo (código a mais para um único refazer, sem download).

### Desvios registrados na implementação

| Data | O que mudou | Quem aprovou |
|---|---|---|
| 20/10/2026 | O CVU zero passou a ser sinalizado (`sinal_cvu` = `zero`), além do ausente e do negativo previstos nas sinalizações aprovadas, e fica fora da comparação com o CMO | usuário ("Zero fica fora"), na calibração do relatório da UTE William Arjona |
| 21/10/2026 | A restrição semi-horária ganhou a estimativa ausente (`sinal_estimada_ausente`), fora dos totais e das médias, sem energia cortada na semi-hora restrita; o limite físico do recurso ficou com as Análises, sem sinalização no Tratamento | usuário, na análise dos relatórios da UFV Seriemas 1 e da EOL Praia Formosa |
| 22/10/2026 | A soma dos códigos de programação passou a usar os códigos vigentes em cada dia, e não todos os códigos da extração, que deixavam a programação da PCH Bandeirante sem soma depois da troca de códigos de 07/2025 | usuário, com a aprovação do relatório da PCH Bandeirante |
| 23/10/2026 | Módulos: as semi-horárias, as semanais e as sinalizações novas ficaram em `renovavel.py` e `termica.py`, e não no motor das séries (`series.py`) e em `validacao.py`, como previa a estrutura de módulos da ampliação; `series.py` não mudou, e `validacao.py` só passou a receber o caminho do dicionário | registrado na incorporação, sem efeito nos requisitos |

## Complexity Tracking

Sem desvios da constituição.
