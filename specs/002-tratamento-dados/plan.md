# Implementation Plan: Tratamento de dados

**Spec**: [spec.md](spec.md) · **Etapa**: 2 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-08

## Summary

O Tratamento lê só o que a Coleta gravou para a usina (`data/usinas/<slug>/coleta/`) e o dicionário de dados da EVT, e grava em `data/usinas/<slug>/tratamento/` os 21 arquivos que a Conferência e as Análises usam. A base de EVT é tipada (ausente continua ausente), conferida pelas regras R1 a R9 (R1 bloqueia; R6 a R9 sinalizam sem excluir) e gravada em Parquet, planilha e CSV, com o relatório de validação gerado dos números. Os indicadores e as taxas ficam na versão mais recente, a programação passa a valores horários, e as séries de disponibilidade, hidrologia e geração passam por um motor único: hora de início, uma hora por instante, recorte no período da EVT, ausências listadas, sinalização de qualidade e auditoria completa. Toda gravação passa pela persistência comum (`src/comum/persistencia.py`), com `.bak` da versão anterior, conferência no disco e restauração em falha.

## Technical Context

**Language/Version**: Python 3.11 ou mais recente (no `venv`: CPython 3.14.6).

**Primary Dependencies**: `pandas` (3.0.6), `numpy` (2.5.3), `pyarrow` (25.0.1: leitura dos extraídos e gravação do Parquet) e `openpyxl` (3.1.5: planilhas e propriedade `assinatura_dados`), com as versões mínimas de `requirements.txt`; da biblioteca padrão, `hashlib`, `zipfile`, `shutil`, `json` e `unicodedata`.

**Storage**: arquivos locais.
- Entrada: `data/usinas/<slug>/coleta/` (CSV `;` da EVT e das auditorias, Parquet dos extraídos, `etapa.json`) e `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json`.
- Saída: `data/usinas/<slug>/tratamento/`, com Parquet, planilhas `.xlsx`, CSV (`;`, ponto decimal, UTF-8), Markdown, `etapa.json` e um `<arquivo>.bak` por arquivo de dados já alterado. Detalhes em [data-model.md](data-model.md).

**Testing**: `pytest`, sem rede, com dados sintéticos (`tests/conftest.py`, `tests/fixtures/`).
- `tests/tratamento/` (40 testes): tipagem, formatos e nome da aba da EVT, regras R1 a R9 e relatório, motor das séries, sinalizações D, H e G, indicadores e programação.
- `tests/comum/test_persistencia.py` e `test_persistencia_gravadores.py` (23 testes): as quatro gravações, falhas simuladas, interrupção pelo usuário, planilha pela assinatura, cada gravador da Coleta e do Tratamento e leitores que ignoram `.bak` e `.tmp`.
- `tests/comum/` (pré-requisito, interrupção, gravação só pela persistência, nível de log, literais da usina) e `tests/integracao/` (linha de comando e fluxo completo de uma usina fictícia, sem literais da São Domingos nos arquivos de texto das etapas).
- Um teste lê o dicionário local da EVT e outro a EVT extraída real; os dois são pulados se o arquivo não existir. A suíte do projeto tem 395 testes.

**Target Platform**: Windows 11, execução local no `venv`, com PowerShell.

**Project Type**: projeto único, pipeline de linha de comando (`python -m src tratamento --usina <slug>`).

**Performance Goals**: menos de 10 minutos sem rede (SC-010). Execução real da São Domingos registrada no `etapa.json`: 41 s, com os 21 arquivos `INALTERADO` (mesmo assim, cada arquivo é gravado num temporário e conferido antes da comparação).

**Constraints**: sem rede e sem ler dados brutos (só o dicionário da EVT); entradas só da Coleta concluída (FR-002); nenhum registro da EVT removido e nenhum valor preenchido ou interpolado; mesmos dados que a base de referência aprovada (SC-001); saídas determinísticas, para que a reexecução fique `INALTERADO` (FR-034); CSV e Markdown com o fim de linha do sistema (CRLF no Windows).

**Scale/Scope** (São Domingos):
- EVT: 70.895 registros horários, de 28/08/2018 00h a 28/09/2026 23h (cerca de 8 anos), 25 colunas na base tratada.
- Indicadores: 1.628 linhas extraídas → 196 linhas mensais, 18 anuais, 160 meses-unidade de horas por estado e 61 meses de taxas.
- Programação: 708 arquivos diários, 33.984 patamares → 16.992 horas e 20 dias ausentes.
- Disponibilidade: 98 arquivos (53 CSV, 45 Parquet), 70.943 linhas → 70.895 horas.
- Hidrologia: 98 arquivos (97 Parquet, 1 CSV), 71.456 linhas → 70.760 horas, 136 h ausentes em 48 intervalos, 2.546 h sinalizadas.
- Geração: 61 arquivos Parquet (anuais até 2021, mensais depois), 76.679 linhas → 70.895 horas.
- Saída: 21 arquivos, cerca de 46 MB.

## Constitution Check

| Princípio / requisito da constituição 2.0.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | spec aprovada; este plano descreve o código atual. Lê só os resultados da Coleta (e o dicionário que ela obteve), grava só na sua pasta e, sem a Coleta concluída, sai com 5 sem gravar. Não acessa o portal |
| II. Relatório fiel aos dados | cumpre | o relatório de validação sai dos resultados das regras e do perfil (nome, `cod_usina`, limites), sem conclusão fixa e com números no padrão brasileiro |
| III. Uma usina por execução, definida pelo perfil | cumpre | `--usina` escolhe o perfil; limites de R6 e R8, cabeçalho do relatório e aba da planilha vêm dele; tolerâncias em `src/comum/regras.py`; nenhum valor de usina no código (`tests/comum/test_literais.py`) |
| IV. Coleta completa e rastreável | cumpre, no que toca à etapa | toda linha tratada mantém `arquivo_origem` (nas séries, o arquivo do valor mantido); a auditoria da Coleta é preservada linha a linha e completada |
| V. Tratamento sem descarte | cumpre | R6 a R9, D1 a D4, H1 a H4 e G1 sinalizam e não excluem; a FR-019 declara o que sai do uso. Convenção de hora, duplicatas e recorte estão na spec e são aplicados pelo mesmo motor aos três conjuntos horários; ausências listadas por conjunto |
| VI. Conferência entre fontes | não se aplica | a etapa não compara fontes; isso é da Conferência |
| VII. Relatório padronizado | não se aplica | a etapa não produz o relatório nem figuras |
| RT 1. Python ≥ 3.11, `venv`, dependências mínimas, regras só em Python | cumpre | quatro dependências de dados; `requirements.txt` conferido contra os imports (`tests/comum/test_conformidade.py`) |
| RT 2. Windows e PowerShell | cumpre | caminhos com `pathlib`; troca atômica na mesma pasta; exemplos em PowerShell |
| RT 3. Gravação segura | cumpre | `.bak` da versão anterior, conteúdo idêntico não regravado, conferência no disco e restauração em falha, inclusive na interrupção pelo usuário (D13) |
| RT 4. Versões dos brutos | não se aplica | é da Coleta |
| RT 5. Cópias de segurança do projeto | não se aplica | ferramenta comum, descrita na spec da Coleta |
| RT 6. Pastas | cumpre | grava só em `data/usinas/<slug>/tratamento/` |
| RT 7. Log | cumpre | log na saída padrão, com arquivos, linhas, resultados das gravações e avisos; o nível de `--log-level` vale também para os loggers dos módulos da etapa, importados só na execução (ver o [contrato](contracts/cli-tratamento.md)) |
| Testes sem rede para cada etapa | cumpre | 40 testes da etapa, 23 da persistência e o fluxo da usina fictícia |
| Entrega: suíte aprovada, execução real e comparação com a referência | cumpre | suíte aprovada; execução real registrada no `etapa.json` (41 s, 21 arquivos `INALTERADO`); relatório da São Domingos idêntico à linha de base aprovada |
| Recuperação do último estado íntegro | cumpre | `.bak` da versão imediatamente anterior de cada arquivo |

## Project Structure

### Documentation (this feature)

```text
specs/002-tratamento-dados/
├── spec.md                  # requisitos aprovados (o quê)
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
├── etapa.py                 # executar_tratamento: orquestra a etapa e monta o resumo do etapa.json
├── evt.py                   # tratar_evt: tipagem, parada por R1, sinalização e base em três formatos
├── validacao.py             # dicionário da EVT, regras R1 a R9, sinalização e relatório de validação
├── series.py                # motor das séries horárias: hora de início, duplicatas, recorte, ausências, auditoria
├── disponibilidade.py       # regras D1 a D4 e série de disponibilidade
├── hidrologia.py            # regras H1 a H4, exclusão campo a campo (limpos) e série hidrológica
├── geracao.py               # regra G1 e série de geração
├── indicadores.py           # indicadores por UG, horas por estado, TEIFa e TEIP; CSV e indicadores.xlsx
└── programacao.py           # patamares → horas e dias sem arquivo

src/comum/                   # partes comuns usadas pela etapa
├── persistencia.py          # gravação segura de dados (descrita nesta spec; usada também pela Coleta)
├── caminhos.py              # pastas e nomes: ARQUIVOS_COLETA, ARQUIVOS_TRATAMENTO, dicionario_evt()
├── regras.py                # tolerâncias e limiares gerais
├── perfil.py                # perfil e valores derivados (limites de R6, produtividade nominal)
├── formatacao.py            # números e datas no padrão brasileiro (relatório de validação)
└── logger.py                # loggers e nível único
src/pipeline.py              # executar_etapa: pré-requisito, etapa.json, códigos de saída
src/__main__.py              # linha de comando única
src/coleta/conjuntos.py      # DescricaoConjunto e descricoes(perfil), compartilhadas com a Coleta
src/coleta/indicadores.py    # separar_conjuntos e os nomes dos quatro conjuntos de indicadores

tests/tratamento/
├── test_evt.py              # tipagem (vírgula, espaços, vazio), instante inválido, três formatos, nome da aba, R1 sem gravar
├── test_validacao.py        # dicionário, faixa de R8, cada regra R1 a R9, ausentes, sinalização, Markdown
├── test_series.py           # hora de início (23:59), duplicatas, recorte, ausências, falhas na auditoria, leitura
├── test_qualidade.py        # D1 a D4, H1 a H4 com exclusão campo a campo, G1
├── test_indicadores.py      # número da UG, versão mais recente das horas e das taxas, recorte
└── test_programacao.py      # média dos patamares e contagem por hora
tests/comum/
├── test_persistencia.py              # NOVO, ALTERADO, INALTERADO, falhas e Ctrl+C com restauração, planilha, Parquet, texto
├── test_persistencia_gravadores.py   # cada gravador guarda a versão anterior; leitores ignoram .bak e .tmp
├── test_conformidade.py              # dados gravados só pela persistência; nível de log mantido; dependências
├── test_literais.py                  # nenhum valor da São Domingos no código
└── test_pipeline.py                  # pré-requisito (código 5), interrupção (código 1) e etapa.json
tests/integracao/
├── test_cli.py                       # comando aceito; opção retirada recusada com código 2
└── test_usina_ficticia.py            # fluxo completo de uma usina fictícia de três UGs, sem programação nem São Domingos
```

## Fluxo de execução

1. `src/__main__.main` lê as opções (inválida: código 2), aplica `--log-level` (`configurar_nivel_log`) e carrega o perfil (`carregar_perfil`; inválido: código 4).
2. `src/pipeline.executar_etapa("tratamento", perfil)` lê `coleta/etapa.json` (`etapa_anterior_concluida`). Ausente, ilegível, com `status` diferente de `concluida` ou com `versao_formato` diferente do atual: mensagem e código 5, nada gravado. Senão, define o perfil ativo, importa e chama `executar_tratamento(perfil)`; qualquer exceção, ou a interrupção pelo usuário (Ctrl+C), vira código 1.
3. `executar_tratamento` abre `registrar_gravacoes()`, que guarda o arquivo e o resultado de cada gravação.
4. **EVT**: `evt.tratar_evt(perfil, coleta/evt_extraido.csv, destinos)`:
   - `validacao.carregar_base_consolidada`: coluna obrigatória ausente gera `ValueError`; sem `arquivo_origem` ou `tipo_match`, só aviso;
   - `carregar_dicionario_dados` e `verificar_colunas_no_dicionario`: sem o JSON, `FileNotFoundError`; grandeza fora do dicionário, só aviso;
   - `padronizar_tipagem_numerica`: instante inválido gera `ValueError`;
   - `validar_regras_fisicas` devolve a tabela das nove regras e os `RegraResultado`; com violação de R1, log de erro e código 1, antes de qualquer gravação;
   - `sinalizar_anomalias`, e então são gravados `validacao_fisica.md`, `validacao_fisica.csv`, `evt_tratado.xlsx`, `evt_tratado.parquet` e `evt_tratado.csv`.

   O primeiro e o último `din_instante` da EVT formam o período de referência.
5. **Indicadores**: `indicadores.montar_indicadores` sobre `indicadores_extraido.parquet` (`separar_conjuntos` → `tratar_indicadores_ug` mensal e anual, `tratar_horas_estado`, `tratar_taxas` → `recortar_periodo` → potência nas horas por estado → aviso de resíduo) e `exportar_indicadores` (quatro CSV e `indicadores.xlsx`).
6. **Programação**: `programacao.montar_programacao` sobre `programacao_extraido.parquet` e a auditoria da Coleta (`ler_auditoria_coleta(..., ["dia"])`), e `exportar_programacao` (dois CSV).
7. **Séries horárias**, nesta ordem: disponibilidade, hidrologia e geração. Para cada uma, `tratar_<conjunto>(descricoes(perfil)[conjunto], extraído, auditoria da Coleta, início, fim, pasta)` chama `series.montar_serie` (hora de início, uma hora por instante, recorte, `listar_ausencias`, auditoria), acrescenta a coluna `qualidade` e chama `exportar_serie` (série, ausências e auditoria).
8. O `resumo` é montado (FR-033; `_resumo_serie` nas séries; `gravacoes` conta os resultados) e volta em `ResultadoEtapa(0, arquivos, resumo)`.
9. `executar_etapa` grava o `etapa.json` (`concluida`; com código 1, `falha`), marca como `desatualizada` as etapas seguintes que já existirem e registra no log o resumo e a pasta.

Código diferente de 0: 2 e 4 no passo 1; 5 no passo 2; 1 com R1 no passo 4, com qualquer exceção (coluna obrigatória, dicionário, instante inválido, extraído ilegível, `ErroPersistencia`) ou com Ctrl+C. Um erro ou uma interrupção depois do passo 4 deixa gravados os arquivos anteriores a ela; o arquivo que estava sendo gravado volta à versão anterior.

## Decisões técnicas

### D1 — Fronteira com a Coleta
- **Decisão**: a Coleta identifica a usina, lê os números sem arredondar, marca os valores não numéricos (`_nao_numerico`) e audita cada arquivo. O Tratamento aplica a convenção de hora, resolve as horas repetidas entre arquivos, recorta o período, lista as ausências, sinaliza a qualidade e completa a auditoria (`horas_usina`, `duplicatas_conflitantes`). A EVT chega consolidada pela Coleta (ordem cronológica, sem hora repetida). As descrições dos conjuntos horários (`DescricaoConjunto`: colunas de valor e convenção de hora) e a separação dos quatro conjuntos de indicadores (`separar_conjuntos`) são declaradas uma vez no pacote da Coleta e reusadas aqui.
- **Motivo**: cada spec descreve uma etapa inteira; alinhar os horários é tratamento, não extração. Um motor único (`series.montar_serie`) evita triplicar código e testes.
- **Alternativas rejeitadas**: extração e tratamento juntos nos conjuntos complementares (a spec da Coleta passaria a descrever tratamento).

### D2 — Período de referência é o da EVT
- **Decisão**: o período vai do primeiro ao último `din_instante` da EVT tratada. As séries horárias e a programação ficam só nesse intervalo, inclusive nas pontas; as tabelas mensais, do mês inicial ao final; a anual, do ano inicial ao final.
- **Motivo**: decisão do usuário (a extensão da geração para antes da EVT foi recusada); as bases ficam alinhadas hora a hora com a EVT.

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
- **Decisão**: EVT, disponibilidade e geração já vêm na hora de início. A hidrologia (`convencao_hora="fim"`) passa por `hora_de_inicio`: instante arredondado para cima até a hora cheia, menos 1 h (01:00 → 00:00; 23:59 → 23:00 do mesmo dia); o publicado fica em `din_instante_publicado`. Na programação, a hora vem do número do patamar (D12).
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
- **Decisão**: nos indicadores por UG, a chave é (mês ou ano, UG) e fica a última linha na ordem de leitura (arquivos em ordem de nome), com aviso. Nas horas por estado, a UG é o número no fim de `nom_unidadegeradora` (`numero_ug`), fica o maior `num_versao` por (mês, UG, estado), e `residuo_identidade_h` = HP − (HS + HRD + HDP + HDF + HDCE + HEDP + HEDF); acima de 0,1 h em valor absoluto (`TOLERANCIA_IDENTIDADE_HORAS`, em `src/comum/regras.py`), só aviso. A potência vem dos indicadores mensais do mesmo mês. Nas taxas, fica o maior `num_versao` por (mês, taxa). `indicadores.xlsx` traz a aba `SIGLAS_HORAS` (`INSUMOS_HORAS`), porque o dicionário do ONS não define as siglas.
- **Motivo**: o ONS republica os parâmetros e as taxas com nova versão. A identidade é conferida sem descartar meses; o recálculo das taxas e a divergência DISPF × horas são da Conferência.

### D12 — Programação: patamares em horas
- **Decisão**: hora de início = dia do arquivo + ((patamar − 1) // 2) h; valor = média dos patamares da hora; `patamares` = quantos formam a hora (2 = completa). Os dias ausentes vão do primeiro dia com arquivo obtido ao último dia do período.
- **Motivo**: o patamar 1 é 00:00–00:30. Na base real da São Domingos (jul/2026), 222 das 232 horas de usina parada com EVT coincidem com programação zero, o que confirma o alinhamento (1 h de defasagem descasaria as bordas das paradas). A programação pode começar depois da EVT (na São Domingos, em 01/10/2024).
- **Alternativas rejeitadas**: usar só o primeiro patamar de cada hora (perde as reprogramações de meia hora).

### D13 — Gravação segura
- **Decisão**: todo arquivo de dados passa por `persistencia._gravar_com_copia`:
  1. grava `<nome>.tmp` na mesma pasta e o confere (CSV relido: linhas e colunas; Parquet: metadados; planilha: abas, dimensões e assinatura; texto: igual ao pretendido);
  2. se o conteúdo é igual ao atual, apaga o temporário e registra `INALTERADO`, sem tocar no arquivo nem no `.bak`;
  3. senão, copia o atual para `<nome>.bak.tmp`, troca o destino pelo temporário (`Path.replace`, atômica na mesma unidade), confere o SHA-256 e só então promove `<nome>.bak.tmp` a `<nome>.bak`;
  4. em qualquer falha, inclusive a interrupção pelo usuário (Ctrl+C), volta a versão anterior (ou apaga o arquivo que não existia) e remove os temporários; o erro vira `ErroPersistencia`, e a interrupção segue para `executar_etapa`. Nos dois casos, a etapa grava o `etapa.json` com `falha` e sai com 1.

  CSV, Parquet e texto são comparados byte a byte, sem cache; a planilha, pela propriedade `assinatura_dados` (SHA-256 do nome e do CSV de cada aba, na ordem).
- **Motivo**: recuperar o estado anterior se o código falhar ou a execução for interrompida, sem acumular cópias, e sem que reexecuções apaguem a versão anterior. A planilha muda de bytes a cada gravação (datas internas), e reler as 70.895 × 25 células da EVT custaria cerca de 18 s; a assinatura é lida em milissegundos.
- **Alternativas rejeitadas**: copiar sempre para `.bak` (reexecuções apagariam a versão anterior); `.bak` datados acumulados (recusados pelo usuário); registro externo de assinaturas (mais um arquivo de controle); `filecmp.cmp` (o cache por tamanho e data dava `INALTERADO` falso).

### D14 — Formatos estáveis e leitura pelas etapas seguintes
- **Decisão**: as saídas são CSV com `;` e, na EVT, Parquet, planilha e CSV. As etapas seguintes leem pelos leitores do próprio pacote (`carregar_disponibilidade_tratada`, `carregar_hidrologia_tratada`, `carregar_geracao_tratada`, `carregar_indicadores_tratados`, `carregar_programacao_tratada`), pelo Parquet da EVT e pelo `validacao_fisica.csv`, sempre por nome explícito: `.bak` e `.tmp` nunca são lidos como dado.
- **Motivo**: os valores que chegam à Conferência e às Análises são os mesmos da base de referência; com saídas determinísticas, a reexecução sem mudança fica 100 % `INALTERADO`.

## Complexity Tracking

Sem desvios da constituição.
