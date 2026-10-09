# Implementation Plan: Conferência

**Spec**: [spec.md](spec.md) · **Etapa**: 3 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-08

## Summary

A Conferência lê os dados tratados e a ficha do cadastro gravada pela Coleta, faz as seis conferências da FR-002 e grava
os resultados em `data/usinas/<slug>/conferencia/`. Cada conferência é uma função de um módulo próprio que devolve um
`ResultadoConferencia`, o registro comum: bases, período, unidade, quantidades comparada, coincidente e divergente,
tolerância, meta (só nas vazões) e tabelas de detalhe. Os seis resultados vão para `conferencias.pkl`, lido pelas
Análises, e as tabelas, para CSV de consulta, sem `.bak`. Base ausente vira "não aplicável", com o motivo; a meta das
vazões não atingida faz a etapa terminar com o código 3, depois de gravar tudo.

## Technical Context

**Language/Version**: Python ≥ 3.11 (o `venv` local usa o 3.14), código tipado e documentado.

**Primary Dependencies**: `pandas` (todas as comparações) e `pyarrow` (motor de `pandas.read_parquet` para a base de
EVT tratada); da biblioteca padrão, `pickle`, `dataclasses` e `pathlib`. Testes com `pytest`.

**Storage**: só arquivos. Lê Parquet e CSV de `data/usinas/<slug>/tratamento/` e `cadastro_ficha.csv` de
`data/usinas/<slug>/coleta/`. Grava em `data/usinas/<slug>/conferencia/` um pickle (`conferencias.pkl`), oito CSV
(`;`, UTF-8) e o `etapa.json`.

**Testing**: `pytest`, sem rede, com dados sintéticos: `tests/conferencia/` (ver **Project Structure**), mais:
- `tests/comum/`: o código 3 grava `concluida` e para o `completo`, e sem a etapa anterior sai 5 sem gravar
  (`test_pipeline.py`); gravação só pela persistência, logger declarado, nível de log único e nenhum valor da São
  Domingos no código (`test_conformidade.py`, `test_literais.py`);
- `tests/integracao/`: comando e opções (`test_cli.py`); fluxo completo de uma usina fictícia com dois meses de dados, em
  que a TEIFa e a TEIP ficam não aplicáveis e a etapa termina com 0 (`test_usina_ficticia.py`).

**Target Platform**: Windows 11, execução local no `venv`, com PowerShell.

**Project Type**: projeto único, pipeline de linha de comando (`python -m src`).

**Performance Goals**: cerca de 1 s na São Domingos (`iniciada_em` → `concluida_em` do `etapa.json`).

**Constraints**: sem rede; não altera o perfil nem as etapas anteriores; grava só na própria pasta, só pela persistência
e sem `.bak`; tolerâncias e meta gerais, fora do perfil; nenhum valor de usina no código.

**Scale/Scope** (São Domingos):
- entradas: 70.895 horas da base de EVT, de Geração por usina e de Disponibilidade por usina (28/08/2018 a 28/09/2026);
  70.760 horas hidrológicas; 196 meses-unidade de indicadores (2 UG); 160 meses-unidade de horas por estado operativo
  (01/2020 a 08/2026); 61 meses de taxas (08/2021 a 08/2026); ficha do cadastro com 1 linha;
- saídas: `conferencias.pkl` com 17 KB; `geracao.csv` com 98 meses; `teifa_teip.csv` com 61 meses (21 com janela
  completa); `dispf_horas.csv` com 4 meses-unidade; os demais CSV com 1 a 4 linhas, ou só o cabeçalho.

## Constitution Check

| Princípio / requisito da constituição 2.0.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa; cada etapa lê só os resultados das anteriores | cumpre | spec própria; lê só `tratamento/` e a ficha de `coleta/`; sem o Tratamento concluído e atualizado, sai com código 5 sem gravar nada (`src/pipeline.py`) |
| II. Relatório fiel aos dados | cumpre | os números citados nas legendas (FR-005) e os textos das divergências do cadastro são refeitos a cada execução, a partir dos dados e do perfil |
| III. Uma usina por execução, definida pelo perfil | cumpre | pastas pelo `usina.slug`; o perfil só entra no cadastro (potência, estado e id ONS); tolerâncias e meta em `src/comum/regras.py`, iguais para qualquer usina |
| IV. Coleta completa e rastreável | não se aplica | a etapa não acessa o portal; a ficha do cadastro chega pronta da Coleta |
| V. Tratamento sem descarte | cumpre | nada é corrigido nem excluído dos dados (FR-007); os registros sinalizados da base de EVT entram; os valores sinalizados das outras bases só ficam fora da comparação |
| VI. Conferência entre fontes | cumpre | seis conferências com o registro comum; não aplicável com o motivo; meta das vazões não atingida → código 3, que para o `completo`; só as conferências refeitas a cada execução |
| VII. Relatório padronizado | não se aplica | as legendas são da Geração do relatório; a etapa entrega os números (FR-005) |
| Requisito técnico 1: Python, `venv`, dependências mínimas | cumpre | só `pandas` e `pyarrow`, já no `requirements.txt` |
| Requisito técnico 2: Windows e PowerShell | cumpre | caminhos com `pathlib`; exemplos em PowerShell no [contrato](contracts/cli-conferencia.md) |
| Requisito técnico 3: gravação segura | cumpre | `gravar_bytes` e `gravar_csv` com `copia=False`: sem `.bak`, conteúdo idêntico não regravado, gravação conferida no disco e restauração em falha ou interrupção |
| Requisito técnico 4: versões dos arquivos brutos | não se aplica | não lê nem grava `data/raw/` |
| Requisito técnico 5: cópias de segurança do projeto | não se aplica | ferramenta comum `copia-seguranca`, fora da etapa |
| Requisito técnico 6: pastas | cumpre | grava só em `data/usinas/<slug>/conferencia/` |
| Requisito técnico 7: log | cumpre | logger `conferencia`, declarado em `LOGGERS_PIPELINE`; um só nível, pelo `--log-level`, mantido nos módulos importados depois |
| Qualidade 1: testes sem rede | cumpre | ver **Testing** |
| Qualidade 2: comparação com o relatório de referência | cumpre | o relatório da São Domingos refeito pelo fluxo é idêntico ao de referência (`comparar`) |
| Qualidade 3: recuperação | cumpre | os resultados são refeitos a partir dos dados tratados; a persistência restaura o arquivo em falha |

## Project Structure

### Documentation (this feature)

```text
specs/003-conferencia/
├── spec.md                  # requisitos aprovados (o quê)
├── plan.md                  # este plano (como)
├── data-model.md            # entradas, saídas, objetos, manifesto e regras
├── contracts/
│   └── cli-conferencia.md   # linha de comando da etapa
└── checklists/
    └── requirements.md      # qualidade da spec
```

### Source Code (repository root)

```text
src/conferencia/
├── __init__.py              # pacote da etapa 3
├── etapa.py                 # executar_conferencia (função da etapa), conferir, carregar_ficha_cadastro, CSV_CONFERENCIA
├── resultado.py             # ResultadoConferencia, nao_aplicavel, diferenca_absoluta, salvar/carregar_conferencias, VERSAO_FORMATO
├── geracao.py               # base de EVT × Geração por usina: conferir_geracao, conferencia_geracao
├── disponibilidade.py       # declarada × operacional: validas, conferir_com_evt, conferencia_disponibilidade
├── vazoes.py                # turbinada e vertida × Dados hidrológicos: alinhar_com_evt, conferencia_vazoes
├── indicadores.py           # DISPF × horas e TEIFa e TEIP: comparar_indicadores_e_horas, janela, janela_completa,
│                            # peso, recalcular_taxas, reproducao_das_taxas, VALORES_DISPF, VALORES_TAXAS
└── cadastro.py              # ficha do cadastro × perfil: divergencias_cadastro, conferencia_cadastro
```

Módulos comuns usados:
- `src/__main__.py` e `src/pipeline.py` (`executar_etapa`, `ResultadoEtapa`, `CODIGO_SUCESSO`, `CODIGO_META_HIDROLOGIA`);
- `src/comum/`: `caminhos.py` (`pasta_etapa`, `ARQUIVOS_TRATAMENTO`, `ARQUIVOS_COLETA`, `ARQUIVOS_CONFERENCIA`),
  `regras.py` (tolerâncias, meta e janela), `persistencia.py` (`gravar_bytes`, `gravar_csv`, `registrar_gravacoes`),
  `periodos.py` (`periodos_continuos`), `formatacao.py` (`fmt_num`), `logger.py` e `perfil.py` (`Perfil`);
- do Tratamento, só para ler: `carregar_geracao_tratada`, `carregar_disponibilidade_tratada`,
  `carregar_hidrologia_tratada`, `carregar_indicadores_tratados`, `SerieConjunto`, `IndicadoresONS` e `limpos`;
- no sentido inverso, as Análises importam `janela`, `peso` (decomposição das taxas), `reproducao_das_taxas` e
  `validas`, e a Geração do relatório importa `diferenca_absoluta`; a Conferência não importa as etapas seguintes.

```text
tests/conferencia/
└── test_conferencias.py     # 17 testes (21 casos): as seis conferências, não aplicáveis, invariantes, janela completa,
                             # limite da tolerância, hora sinalizada, valores ausentes, textos do cadastro e a função
                             # da etapa (código 3, CSV antigo apagado, nenhum .bak, releitura do .pkl)
```

## Fluxo de execução

1. `src/__main__.main` lê as opções (código 2 se inválidas), aplica o `--log-level` e valida o perfil (código 4).
2. `src/pipeline.executar_etapa("conferencia", perfil)` confere `tratamento/etapa.json` (`status` `concluida` e
   `versao_formato` atual). Sem isso, registra a mensagem do pré-requisito e sai com código 5, sem gravar nada.
3. `executar_conferencia(perfil)` cria a pasta e chama `conferir(perfil)`, que:
   - lê de `evt_tratado.parquet` só as cinco colunas de `COLUNAS_EVT`, e carrega as séries e os indicadores tratados
     (`None` quando faltam os arquivos) e a ficha do cadastro (vazia quando falta);
   - chama, nesta ordem, as funções `conferencia_<id>` das seis conferências e registra cada resultado no log (INFO) ou,
     se não aplicável, o motivo (WARNING).
4. Dentro de `registrar_gravacoes()`, `salvar_conferencias` grava `conferencias.pkl`. Para cada par de
   `CSV_CONFERENCIA`, a tabela presente vai para o CSV por `gravar_csv(..., copia=False)` (um dicionário vira uma
   linha); a tabela ausente apaga o CSV que sobrou de uma execução anterior.
5. O código é 3 (`CODIGO_META_HIDROLOGIA`, com ERROR no log) quando as vazões são aplicáveis e `meta_atingida` é falso;
   senão, 0. A função devolve `ResultadoEtapa(codigo, arquivos, resumo)`, com `resumo = {id: resultado.resumo()}`.
6. `executar_etapa` grava o `etapa.json`: `concluida` com 0 ou 3, e as Análises e o Relatório já executados ficam
   `desatualizada`. Qualquer exceção (arquivo de entrada ilegível, falha de gravação) e a interrupção pelo usuário
   (Ctrl+C) viram código 1, com `falha` e `resumo = {"erro": …}`. Por fim, o log mostra o resumo e a pasta.
7. No `completo`, o código 3 para o fluxo; as Análises e o Relatório podem ser executados à parte.

## Decisões técnicas

### D1 — Um registro comum para as seis conferências
- **Decisão**: cada conferência devolve um `ResultadoConferencia` (dataclass). `__post_init__` recusa um `id` fora de
  `CONFERENCIAS` e, na conferência aplicável, `comparados ≠ coincidentes + divergentes`. As tabelas de detalhe ficam em
  `tabelas`, com as chaves que as Análises leem.
- **Motivo**: a FR-003 e a SC-002 ficam garantidas na construção; as Análises e as legendas leem sempre os mesmos campos.

### D2 — Base ausente vira "não aplicável"
- **Decisão**: sem a série (ou com ela vazia), sem os indicadores ou sem a ficha, a função devolve
  `nao_aplicavel(...)`, com o motivo, e as demais conferências seguem. A base de EVT, que o Tratamento sempre entrega,
  não é testada: sem ela, a etapa termina com código 1. Na TEIFa e na TEIP sem nenhum mês de janela completa, o
  resultado é não aplicável, mas guarda a tabela `recalculo` e o CSV é gravado. Com as bases presentes e nada
  comparável (horas sem par, horas sinalizadas, meses sem alguma taxa), a conferência é aplicável, com 0 comparados.
- **Motivo**: FR-004 e FR-016; constituição, princípio VI.

### D3 — Tolerâncias e meta como regras gerais
- **Decisão**: todos os valores ficam em `src/comum/regras.py` (0,01 MW; 0,5 m³/s; 1 h; 0,001 p.p.; 0,001 MW na potência
  do cadastro; janela de 60 meses; meta de 99 %). Toda comparação passa por `resultado.diferenca_absoluta`: a diferença
  absoluta, arredondada a 9 casas (`CASAS_COMPARACAO`), coincide quando é menor ou igual à tolerância (limite incluído).
- **Motivo**: as tolerâncias acompanham o arredondamento dos valores publicados e são iguais para qualquer usina
  (princípio III); o arredondamento tira o resíduo do ponto flutuante (30,01 − 30,00 dá 0,010000000000001563).
- **Alternativas rejeitadas**: tolerâncias no perfil, que tornariam incomparáveis os relatórios de usinas diferentes;
  comparação sem arredondamento, em que uma diferença igual à tolerância cairia de um lado ou do outro.

### D4 — Geração e disponibilidade, hora a hora
- **Decisão**: só os valores não nulos entram. Na geração, as horas de Geração por usina com `qualidade` `OK` definem o
  intervalo, e a base de EVT é recortada nele; a junção externa separa as horas comuns das horas só numa fonte, e a hora
  sinalizada de Geração por usina conta como só na base de EVT. Na disponibilidade, as horas sinalizadas (D1 a D4) saem
  e são contadas só em `horas_sinalizadas_excluidas`; as horas só na base de EVT são as que faltam em Disponibilidade
  por usina, no intervalo das horas válidas. As horas divergentes viram períodos contínuos (`periodos_continuos`). Só a
  geração tem a tabela mensal, com a diferença Geração por usina − base de EVT.
- **Motivo**: FR-010 e FR-011. A série de Geração por usina anterior à base de EVT não é conferida (decisão do usuário
  registrada na spec); o Tratamento já a recorta no período da base.

### D5 — Vazões, meta e código 3
- **Decisão**: a hidrologia chega do Tratamento na hora de início; a Conferência não desloca nada e só registra
  `deslocamento_aplicado_h = -1`. A função `limpos`, do Tratamento, exclui a vazão negativa só no campo; entram as horas
  com as duas vazões nas duas fontes. A meta é atingida com 99 % ou mais e ao menos uma hora comum (`confirmado`). Sem a
  meta, a etapa grava os seis resultados e só depois devolve o código 3, registrado como `concluida`.
- **Motivo**: FR-012 e FR-013. A coincidência das duas vazões confirma a convenção de hora; sem ela, as Análises não
  fazem os cruzamentos com a afluência.
- **Alternativas rejeitadas**: excluir a hora sinalizada inteira, o que perderia horas com as duas vazões válidas.

### D6 — DISPF × horas por estado operativo
- **Decisão**: junção interna por `mes` e `ug`. INDISPPF e INDISPFF viram horas (% × HP ÷ 100) e são comparadas com HDP
  e HDF; o mês-unidade diverge quando alguma das diferenças passa de 1 h em valor absoluto. O mês-unidade sem algum dos
  valores de `VALORES_DISPF` (HP, HDP, HDF, INDISPPF, INDISPFF) não é comparado: fica fora das quantidades e do período
  e é contado em `tabelas["sem_valor"]`. A lista guarda também HS e HRD, que as Análises usam para ver se a diferença
  cabe nas horas de reserva desligada.
- **Motivo**: FR-014; são duas apurações do ONS para a mesma unidade e o mesmo mês. A falta de valor não é discordância
  entre as fontes e, como nas conferências hora a hora, fica fora da comparação.
- **Alternativas rejeitadas**: contar o valor ausente como divergência, que o levaria à constatação e à conclusão.

### D7 — Recálculo da TEIFa e da TEIP
- **Decisão**: para cada mês publicado, `janela` toma as horas dos 60 meses que terminam nele e `peso` usa
  `potencia_mw` (juntada às horas pelo Tratamento), ou 1 quando falta. TEIFa = Σ P·(HDF + HEDF) ÷ Σ P·(HP − HDP − HEDP)
  e TEIP = Σ P·(HDP + HEDP) ÷ Σ P·HP. A janela é completa (`janela_completa`) quando o primeiro mês dela não é anterior
  ao primeiro mês das horas; senão, as taxas recalculadas ficam vazias. `reproducao_das_taxas` compara os meses de
  janela completa com as quatro taxas (`VALORES_TAXAS`) e conta à parte os que não têm alguma (`sem_valor`). A diferença
  em p.p. é (recalculada − publicada) × 100, e o mês é reproduzido com as duas diferenças de até 0,001 p.p.; a maior
  diferença vale só para os meses comparados. As Análises e a legenda usam essa contagem, sem refazê-la.
- **Motivo**: FR-015 e FR-016; é a janela móvel das taxas publicadas pelo ONS.

### D8 — Cadastro com o perfil
- **Decisão**: usa a primeira linha de `cadastro_ficha.csv`, que a Coleta monta com a primeira linha do CEG e a contagem
  `linhas_ceg`. Confere potência autorizada, estado, id ONS e linhas com o CEG com `Perfil.potencia_autorizada_esperada_mw`
  (= `parametros.potencia_instalada_mw`), `usina.estado`, `identificacao.id_ons` e 1. O texto de cada divergência vai
  pronto para o relatório, com a potência do perfil sem casas quando inteira e com uma casa nos demais casos.
- **Motivo**: FR-017.

### D9 — `conferencias.pkl` para a etapa seguinte, CSV para consulta
- **Decisão**: pickle de `{"versao_formato": 1, "resultados": {id: ResultadoConferencia}}`, por `gravar_bytes`, e uma
  tabela por CSV (`CSV_CONFERENCIA`), por `gravar_csv`, os dois com `copia=False`. `carregar_conferencias` recusa outra
  versão do formato, pedindo para refazer a Conferência.
- **Motivo**: as Análises recebem o mesmo objeto que existia na memória, com os tipos preservados (datas, inteiros,
  vazios); a planilha do relatório continua sendo a versão legível e completa.
- **Alternativas rejeitadas**: JSON ou Parquet campo a campo (muito código e risco de mudar tipos); refazer as
  conferências nas Análises (fronteira entre as etapas).

### D10 — Nenhum resto de execução anterior
- **Decisão**: o CSV de uma conferência sem a tabela nesta execução é apagado e não entra no `etapa.json`. Os resultados
  não têm `.bak`, porque são refeitos a partir dos dados tratados.
- **Motivo**: a pasta nunca mistura execuções diferentes; constituição, requisito técnico 3.

## Complexity Tracking

Sem desvios da constituição.
