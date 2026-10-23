# Implementation Plan: Conferência

**Spec**: [spec.md](spec.md) · **Etapa**: 3 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-23

## Summary

A Conferência lê os dados tratados e a ficha do cadastro gravada pela Coleta, faz as conferências do catálogo que se
aplicam à usina e grava os resultados em `data/usinas/<slug>/conferencia/`. Cada conferência é uma função de um módulo
próprio que devolve um `ResultadoConferencia`, o registro comum: bases, período, unidade, quantidades comparada,
coincidente e divergente, tolerância, meta (só nas vazões) e tabelas de detalhe.

O catálogo (`aplicabilidade.py`) declara, para cada uma das doze conferências, os tipos de usina, os conjuntos do ONS
que ela compara e o nível exigido, e escreve o motivo quando ela não se aplica. Há dois caminhos, escolhidos pela série
de referência da usina:
- **hidrelétrica com EVT**: as seis conferências da FR-002, exatamente como antes da ampliação para todos os tipos;
  todas vão para `conferencias.pkl`, aplicáveis ou não;
- **usinas sem EVT**: só as conferências aplicáveis do catálogo (indicadores oficiais, cadastro, G3 e G4 nas
  térmicas, G1, G2 e G5 nas eólicas e solares, alinhamento da hidrologia pela geração nas hidrelétricas); só as
  aplicadas vão para `conferencias.pkl`.

Em todas as usinas, `nao_aplicaveis.csv` registra as conferências do catálogo que não se aplicam, com o motivo. As
tabelas vão para CSV de consulta, sem `.bak`. Base ausente vira "não aplicável", com o motivo; a meta das vazões não
atingida faz a etapa terminar com o código 3, depois de gravar tudo. As conferências novas não têm meta.

## Technical Context

**Language/Version**: Python ≥ 3.11 (o `venv` local usa o 3.14), código tipado e documentado.

**Primary Dependencies**: `pandas` (todas as comparações) e `pyarrow` (motor de `pandas.read_parquet` para a base de
EVT tratada); da biblioteca padrão, `pickle`, `dataclasses` e `pathlib`. Testes com `pytest`. Nenhuma dependência nova
com a ampliação para todos os tipos.

**Storage**: só arquivos.
- **Lê**: Parquet e CSV de `data/usinas/<slug>/tratamento/` (na hidrelétrica com EVT, a base de EVT; nas usinas sem
  EVT, a base horária comum e as séries do tipo) e `cadastro_ficha.csv` de `data/usinas/<slug>/coleta/`. Nunca lê
  `data/raw/`.
- **Grava** em `data/usinas/<slug>/conferencia/`: um pickle (`conferencias.pkl`), até catorze CSV de conferência (`;`,
  UTF-8), `nao_aplicaveis.csv` e o `etapa.json`.

**Testing**: `pytest`, sem rede, com dados sintéticos: `tests/conferencia/` (ver **Project Structure**), mais:
- `tests/comum/`: o código 3 grava `concluida` e para o `completo`, e sem a etapa anterior sai 5 sem gravar
  (`test_pipeline.py`); gravação só pela persistência, logger declarado, nível de log único e nenhum valor da São
  Domingos nem identificador das usinas piloto no código (`test_conformidade.py`, `test_literais.py`);
- `tests/relatorio/test_invariantes_uhe.py`: o relatório e a planilha da hidrelétrica com EVT com as conferências de
  sempre;
- `tests/integracao/`: comando e opções (`test_cli.py`); fluxo completo de uma usina fictícia com dois meses de dados,
  em que a TEIFa e a TEIP ficam não aplicáveis e a etapa termina com 0 (`test_usina_ficticia.py`); uma usina fictícia
  de cada tipo de ponta a ponta, com G1 a G5, o alinhamento da hidrologia e os motivos de `nao_aplicaveis.csv`
  (`test_usinas_ficticias.py`).

**Target Platform**: Windows 11, execução local no `venv`, com PowerShell.

**Project Type**: projeto único, pipeline de linha de comando (`python -m src`).

**Performance Goals**: cerca de 1 s na São Domingos (`iniciada_em` → `concluida_em` do `etapa.json`); menos de 1 s na
UTE William Arjona.

**Constraints**: sem rede; não altera o perfil nem as etapas anteriores; grava só na própria pasta, só pela persistência
e sem `.bak`; tolerâncias e meta gerais, fora do perfil; nenhum valor de usina no código; na hidrelétrica com EVT, os
seis resultados e os CSV iguais aos de antes da ampliação.

**Scale/Scope**:
- São Domingos (hidrelétrica com EVT):
  - entradas: 70.895 horas da base de EVT, de Geração por usina e de Disponibilidade por usina (28/08/2018 a
    28/09/2026); 70.760 horas hidrológicas; 196 meses-unidade de indicadores (2 UG); 160 meses-unidade de horas por
    estado operativo (01/2020 a 08/2026); 61 meses de taxas (08/2021 a 08/2026); ficha do cadastro com 1 linha;
  - saídas: `conferencias.pkl` com 17 KB; `geracao.csv` com 98 meses; `teifa_teip.csv` com 61 meses (21 com janela
    completa); `dispf_horas.csv` com 4 meses-unidade; `nao_aplicaveis.csv` com 6 linhas (G1 a G5 e o alinhamento da
    hidrologia); os demais CSV com 1 a 4 linhas, ou só o cabeçalho;
- usinas piloto sem EVT, além do cadastro: UTE William Arjona (46.243 horas da série de referência; G3, G4, DISPF ×
  horas e TEIFa e TEIP), UFV Seriemas 1 (G1, G2 e G5), EOL Praia Formosa (G1 e G5) e PCH Bandeirante (nenhuma outra);
- catálogo: doze conferências.

## Constitution Check

| Princípio / requisito da constituição 3.1.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa; cada etapa lê só os resultados das anteriores | cumpre | spec própria; lê só `tratamento/` e a ficha de `coleta/`, nunca `data/raw/`; da Coleta, importa só o código do registro dos conjuntos e da escolha da série de referência, que leem o perfil; sem o Tratamento concluído e atualizado, sai com código 5 sem gravar nada (`src/pipeline.py`) |
| II. Relatório fiel aos dados | cumpre | os números citados nas legendas (FR-005), os textos das divergências do cadastro e os motivos das não aplicáveis são refeitos a cada execução, a partir dos dados e do perfil |
| III. Uma usina por execução, definida pelo perfil | cumpre | pastas pelo `usina.slug`; o tipo, a `[cobertura]` e os membros do conjunto declarados no perfil decidem as conferências aplicáveis; as séries das outras usinas do conjunto só entram na G2, identificadas; tolerâncias e meta em `src/comum/regras.py`, iguais para qualquer usina |
| IV. Coleta completa e rastreável | não se aplica | a etapa não acessa o portal; a ficha do cadastro chega pronta da Coleta |
| V. Tratamento sem descarte | cumpre | nada é corrigido nem excluído dos dados (FR-007); os registros sinalizados da base de EVT entram; os valores sinalizados das outras bases só ficam fora da comparação |
| VI. Conferência entre fontes | cumpre | catálogo com o registro comum; toda conferência do catálogo que não se aplica à usina fica em `nao_aplicaveis.csv`, com o motivo, inclusive na UHE; meta só nas vazões, e a não atingida dá o código 3, que para o `completo`; as conferências novas só registram; só as conferências refeitas a cada execução |
| VII. Relatório padronizado | não se aplica | as legendas são da Geração do relatório; a etapa entrega os números (FR-005) |
| VIII. Granularidade declarada | cumpre | toda comparação entre fontes é no mesmo nível (usina com usina, conjunto com conjunto); par de níveis diferentes não é comparado; nada do conjunto é dividido entre as usinas |
| IX. Relatórios aprovados protegidos | cumpre | na hidrelétrica com EVT, os seis resultados e os CSV de antes, sem mudança, e `nao_aplicaveis.csv` fora do relatório (teste próprio); `comparar --todas` refaz a Conferência a partir da Coleta e do perfil congelados de cada referência |
| Requisito técnico 1: Python, `venv`, dependências mínimas | cumpre | só `pandas` e `pyarrow`, já no `requirements.txt` |
| Requisito técnico 2: Windows e PowerShell | cumpre | caminhos com `pathlib`; exemplos em PowerShell no [contrato](contracts/cli-conferencia.md) |
| Requisito técnico 3: gravação segura | cumpre | `gravar_bytes` e `gravar_csv` com `copia=False`: sem `.bak`, conteúdo idêntico não regravado, gravação conferida no disco e restauração em falha ou interrupção |
| Requisito técnico 4: versões dos arquivos brutos | não se aplica | não lê nem grava `data/raw/` |
| Requisito técnico 5: cópias de segurança do projeto | não se aplica | ferramenta comum `copia-seguranca`, fora da etapa |
| Requisito técnico 6: pastas | cumpre | grava só em `data/usinas/<slug>/conferencia/` |
| Requisito técnico 7: log | cumpre | logger `conferencia`, declarado em `LOGGERS_PIPELINE`; um só nível, pelo `--log-level`, mantido nos módulos importados depois |
| Qualidade 1: testes sem rede | cumpre | ver **Testing** |
| Qualidade 2: comparação com os relatórios de referência | cumpre | `comparar --todas` refaz a Conferência das cinco referências sem diferença no relatório |
| Qualidade 3: recuperação | cumpre | os resultados são refeitos a partir dos dados tratados; a persistência restaura o arquivo em falha |

## Project Structure

### Documentation (this feature)

```text
specs/003-conferencia/
├── spec.md                  # requisitos aprovados (o quê), com a aplicabilidade por tipo
├── plan.md                  # este plano (como)
├── data-model.md            # entradas, saídas, objetos, catálogo, manifesto e regras
├── contracts/
│   └── cli-conferencia.md   # linha de comando da etapa
└── checklists/
    └── requirements.md      # qualidade da spec
```

### Source Code (repository root)

```text
src/conferencia/
├── __init__.py              # pacote da etapa 3
├── etapa.py                 # executar_conferencia (função da etapa), conferir (os dois caminhos), fontes_da_geracao,
│                            # carregar_ficha_cadastro, COLUNAS_EVT, CSV_CONFERENCIA
├── aplicabilidade.py        # catálogo: ConferenciaCatalogo, CATALOGO_CONFERENCIAS, NOMES_CONJUNTOS, aplicaveis,
│                            # niveis_coletados, tabela_nao_aplicaveis (nao_aplicaveis.csv)
├── resultado.py             # ResultadoConferencia, nao_aplicavel, diferenca_absoluta, salvar/carregar_conferencias,
│                            # CONFERENCIAS, VERSAO_FORMATO
├── geracao.py               # base de EVT × Geração por usina: conferir_geracao, conferencia_geracao
├── disponibilidade.py       # declarada × operacional: validas, conferir_com_evt, conferencia_disponibilidade
├── vazoes.py                # turbinada e vertida × Dados hidrológicos: alinhar_com_evt, conferencia_vazoes;
│                            # hidrelétrica sem EVT: alinhar_com_geracao, conferencia_alinhamento_hidrologia
├── indicadores.py           # DISPF × horas e TEIFa e TEIP: comparar_indicadores_e_horas, janela, janela_completa,
│                            # peso, recalcular_taxas, reproducao_das_taxas, VALORES_DISPF, VALORES_TAXAS
├── cadastro.py              # ficha do cadastro × perfil: divergencias_cadastro, conferencia_cadastro
└── fontes.py                # conferências entre fontes: conferir_series (comum); G3 e G4 (térmicas); G1, G2
                             # (soma_do_conjunto) e G5 (eólicas e solares)
```

Módulos comuns usados:
- `src/__main__.py` e `src/pipeline.py` (`executar_etapa`, `ResultadoEtapa`, `CODIGO_SUCESSO`, `CODIGO_META_HIDROLOGIA`,
  `VERSAO_FORMATO`);
- `src/comum/`: `caminhos.py` (`pasta_etapa`, `ARQUIVOS_TRATAMENTO`, `ARQUIVOS_COLETA`, `ARQUIVOS_CONFERENCIA`),
  `regras.py` (tolerâncias, meta, janela e `TIPOS_USINA`), `persistencia.py` (`gravar_bytes`, `gravar_csv`,
  `registrar_gravacoes`), `periodos.py` (`periodos_continuos`), `formatacao.py` (`fmt_num`), `logger.py` e `perfil.py`
  (`Perfil`);
- da Coleta, só código que lê o perfil: `registro.py` (`tipo_da_usina`, `conjuntos_da_usina`, `cobertura_da_usina`,
  `nivel_coletado`, `descricoes`, `entrada`, `NIVEL_DA_COBERTURA`, `HIDRELETRICAS`, `TERMICAS`) e
  `serie_referencia.escolher` (o caminho com ou sem EVT);
- do Tratamento, só para ler: `carregar_geracao_tratada`, `carregar_disponibilidade_tratada`,
  `carregar_hidrologia_tratada`, `carregar_indicadores_tratados`, `carregar_base_horaria`,
  `carregar_programacao_tratada`, `carregar_despacho_tratado`, `carregar_renovavel`, `em_hora_cheia`, `SerieConjunto`,
  `IndicadoresONS` e `limpos`;
- no sentido inverso, as Análises importam `janela`, `peso` (decomposição das taxas), `reproducao_das_taxas`, `validas`,
  `ResultadoConferencia` e `carregar_conferencias`, e a Geração do relatório importa `diferenca_absoluta` e
  `CATALOGO_CONFERENCIAS` (a descrição de cada conferência na tabela das não aplicáveis); a Conferência não importa as
  etapas seguintes.

```text
tests/conferencia/
├── test_conferencias.py        # 22 testes (26 casos): as seis conferências, não aplicáveis, invariantes, janela
│                               # completa, limite da tolerância, hora sinalizada, valores ausentes, textos do cadastro
│                               # (também sem id ONS), alinhamento da hidrologia pela geração e a função da etapa
│                               # (código 3, CSV antigo apagado, nenhum .bak, releitura do .pkl)
├── test_aplicabilidade.py      # 9 testes: catálogo, nao_aplicaveis.csv na UHE e nas usinas sem EVT, o relatório sem
│                               # ler o arquivo, o alinhamento só nas hidrelétricas
├── test_fontes_termica.py      # 5 testes: G3, G4 com o deslocamento, aplicabilidade, taxas sem a usina, DISPF × horas
│                               # numa térmica
└── test_fontes_renovaveis.py   # 6 testes: G1 só no mesmo nível, G2 com a composição vigente, G5, aplicabilidade
                                # pelos níveis
```

## Fluxo de execução

1. `src/__main__.main` lê as opções (código 2 se inválidas), aplica o `--log-level` e valida o perfil (código 4, inclusive
   o perfil em rascunho).
2. `src/pipeline.executar_etapa("conferencia", perfil)` confere `tratamento/etapa.json` (`status` `concluida` e
   `versao_formato` atual). Sem isso, registra a mensagem do pré-requisito e sai com código 5, sem gravar nada.
3. `executar_conferencia(perfil)` cria a pasta e chama `conferir(perfil)`, que escolhe o caminho pela série de referência
   (`escolher(perfil).conjunto == "evt"`):
   - **com EVT**: lê de `evt_tratado.parquet` só as cinco colunas de `COLUNAS_EVT`, carrega as séries e os indicadores
     tratados (`None` quando faltam os arquivos) e a ficha do cadastro (vazia quando falta), e chama, nesta ordem, as
     funções `conferencia_<id>` das seis conferências;
   - **sem EVT**: `aplicaveis(perfil)` dá as conferências do catálogo que se aplicam, na ordem do catálogo, e só elas
     são executadas, cada uma com as tabelas tratadas de que precisa;
   - cada resultado vai para o log: INFO, com as quantidades, ou WARNING, com o motivo, se não aplicável.
4. `tabela_nao_aplicaveis(perfil, resultados)` monta `nao_aplicaveis.csv`: os motivos do catálogo e os dos resultados
   sem base. Nas usinas sem EVT, os resultados não aplicáveis saem dos resultados gravados.
5. Dentro de `registrar_gravacoes()`, `salvar_conferencias` grava `conferencias.pkl`. Para cada par de
   `CSV_CONFERENCIA`, a tabela presente vai para o CSV por `gravar_csv(..., copia=False)` (um dicionário vira uma
   linha); a tabela ausente apaga o CSV que sobrou de uma execução anterior. Por fim, `nao_aplicaveis.csv`.
6. O código é 3 (`CODIGO_META_HIDROLOGIA`, com ERROR no log) quando as vazões são aplicáveis e `meta_atingida` é falso;
   senão, 0. A função devolve `ResultadoEtapa(codigo, arquivos, resumo)`, com `resumo = {id: resultado.resumo()}` e a
   chave `nao_aplicaveis`, a lista das conferências do arquivo.
7. `executar_etapa` grava o `etapa.json` (formato 2): `concluida` com 0 ou 3, e as Análises e o Relatório já executados
   ficam `desatualizada`. Qualquer exceção (arquivo de entrada ilegível, falha de gravação) e a interrupção pelo usuário
   (Ctrl+C) viram código 1, com `falha` e `resumo = {"erro": …}`. Por fim, o log mostra o resumo e a pasta.
8. No `completo`, o código 3 para o fluxo; as Análises e o Relatório podem ser executados à parte.

## Decisões técnicas

### D1 — Um registro comum para todas as conferências
- **Decisão**: cada conferência devolve um `ResultadoConferencia` (dataclass). `__post_init__` recusa um `id` fora de
  `CONFERENCIAS` e, na conferência aplicável, `comparados ≠ coincidentes + divergentes`. As tabelas de detalhe ficam em
  `tabelas`, com as chaves que as Análises leem.
- **Motivo**: a FR-003 e a SC-002 ficam garantidas na construção; as Análises e as legendas leem sempre os mesmos campos.

### D2 — Base ausente vira "não aplicável"
- **Decisão**: sem a série (ou com ela vazia), sem os indicadores ou sem a ficha, a função devolve
  `nao_aplicavel(...)`, com o motivo, e as demais conferências seguem. A base de EVT, que o Tratamento sempre entrega à
  hidrelétrica com EVT, não é testada: sem ela, a etapa termina com código 1. Na TEIFa e na TEIP sem nenhum mês de
  janela completa, o resultado é não aplicável, mas guarda a tabela `recalculo`, e o CSV é gravado na hidrelétrica com
  EVT. Nas seis conferências da FR-002, com as bases presentes e nada comparável (horas sem par, horas sinalizadas,
  meses sem alguma taxa), a conferência é aplicável, com 0 comparados; nas conferências entre fontes G1 a G5, sem hora
  comum, ela é não aplicável (D13).
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
  (= `parametros.potencia_instalada_mw`), `usina.estado`, `identificacao.id_ons` e 1. O perfil sem id ONS (usina em
  conjunto sem id próprio) vale texto vazio: só diverge da ficha com id ONS, e o texto diz "não informado", nunca
  "None". O texto de cada divergência vai pronto para o relatório, com a potência do perfil sem casas quando inteira e
  com uma casa nos demais casos.
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

### D11 — Catálogo das conferências e `nao_aplicaveis.csv`
- **Decisão**: `CATALOGO_CONFERENCIAS` (`aplicabilidade.py`) declara, para cada conferência, a descrição, os tipos, os
  conjuntos do registro da Coleta que precisam ter sido coletados para a usina e as condições de nível (data-model,
  seção 3.7). `_motivo_estatico` decide, só com o perfil (tipo, `[cobertura]`, membros do conjunto e nível de cada
  conjunto), se a conferência se aplica, e escreve o motivo quando não se aplica; o resultado sem base acrescenta o
  motivo dele. `nao_aplicaveis.csv` lista, na ordem do catálogo, todas as que não se aplicam, inclusive na UHE; o
  alinhamento da hidrologia pela geração só é registrado nas hidrelétricas (`registrada_so_nos_tipos`).
- **Motivo**: FR-018 e FR-019; constituição, princípio VI: a conferência sem base para a usina, o tipo ou o nível fica
  registrada, com o motivo. Exemplos: vazões fora das hidrelétricas; G2 numa usina Tipo I; TEIFa e TEIP de usina ausente
  das taxas; G1 a G5 numa UHE.

### D12 — Dois caminhos, com a hidrelétrica com EVT intacta
- **Decisão**: o caminho sai da série de referência da usina (`escolher(perfil)`, da Coleta). Na hidrelétrica com EVT,
  as seis conferências rodam como antes da ampliação e ficam todas em `conferencias.pkl`; `nao_aplicaveis.csv` é um
  arquivo a mais, que o relatório e a planilha dela não leem. Nas usinas sem EVT, só as aplicáveis rodam, e só as
  aplicadas ficam em `conferencias.pkl`; as não aplicáveis ficam só no arquivo, que as Análises leem para as notas.
- **Motivo**: o relatório da UHE São Domingos não pode mudar (constituição, princípio IX). Um teste por invariante
  aponta a causa de uma diferença antes do `comparar --todas`: no relatório e na planilha da hidrelétrica com EVT, as
  conferências de sempre, sem G1 a G5, e as não aplicáveis só no arquivo.
- **Alternativas rejeitadas**: confiar só no `comparar --todas`, que mostra que algo mudou, mas não por quê.

### D13 — Conferências entre fontes G1 a G5: mesmo nível, 0,01 MW, sem meta
- **Decisão**: `fontes.conferir_series` compara duas séries horárias (`valor_a` e `valor_b`) para todas: junção externa
  pelas horas com valor, horas comuns coincidentes com diferença de até 0,01 MW (`diferenca_absoluta`), horas só em cada
  fonte (`so_a`, `so_b`), energia de cada fonte nas horas comuns, tabela mensal e períodos contínuos das divergentes. Sem
  hora comum, a conferência é não aplicável, com o motivo. O nível de cada base é conferido antes, no catálogo, e, na
  G1, de novo par a par. Nenhuma tem meta: só registram e nunca mudam o código.
- **Motivo**: FR-019 a FR-025. Comparar níveis diferentes, como a usina e o conjunto, não confere nada (princípio VIII).
  Sem histórico, uma meta seria arbitrária e poderia parar o fluxo sem motivo (princípio VI); depois das usinas piloto,
  só o usuário pode aprovar uma meta.
- **Alternativas rejeitadas**: usar a meta de 99 % das vazões, que é de outra grandeza, de outra fonte.

### D14 — A G4 confere a convenção de hora, sem ajuste automático
- **Decisão**: a G4 mede também a coincidência com a Geração por usina deslocada de +1 h e de −1 h
  (`pct_coincidentes_deslocada`, no `resumo`). Se alguma for maior que a sem deslocamento, o log avisa (WARNING) que a
  convenção declarada deve ser corrigida no Tratamento; nada é ajustado.
- **Motivo**: FR-021. A convenção de hora do despacho é a do início do intervalo, como na Geração por usina; a
  conferência com a geração horária a confirma. Na UTE William Arjona, 99,7 % das horas coincidem sem deslocamento e
  92,9 % com uma hora.
- **Alternativas rejeitadas**: ajustar a hora automaticamente, que esconderia um erro de convenção do Tratamento.

### D15 — Fontes da geração da G1 e soma da G2
- **Decisão**:
  - **G1** (`etapa.fontes_da_geracao`): a Geração por usina vem da base horária comum quando é a série de referência
    (com o nível de cada hora) e, senão, de `geracao_horaria.csv`, com o nível da cobertura; o Fator de capacidade, de
    `fator_capacidade_horario.csv`, com o nível; a restrição com detalhe, de `restricao_horaria.csv`, no nível da usina;
    a restrição com a razão, de `restricao_razao_semi_horaria.csv`, levada à hora por `em_hora_cheia` (só as horas com
    as duas meias-horas). Os pares seguem a ordem Geração por usina, Fator de capacidade, restrição com detalhe,
    restrição com a razão, e cada par é comparado em cada nível que as duas fontes têm.
  - **G2** (`fontes.soma_do_conjunto`): soma, hora a hora, a restrição com detalhe da usina e dos membros do perfil
    (`restricao_membros_horaria.csv`), só nas horas em que toda usina vigente tem valor; cada membro vale do dia de
    `inicio` ao de `fim` declarados no perfil, e a usina do relatório vale sempre. As horas incompletas são contadas
    (`horas_incompletas`). A soma é comparada com a Geração por usina no nível do conjunto.
- **Motivo**: FR-023 e FR-024; princípio III (as séries das outras usinas só entram como contexto identificado) e
  princípio VIII (nenhum número do conjunto é dividido entre as usinas).

### D16 — Indicadores das térmicas pelo CEG
- **Decisão**: a DISPF × horas e a TEIFa e a TEIP refeitas usam nas térmicas o mesmo código das hidrelétricas, com os
  indicadores obtidos pelo CEG e o HP publicado (que nas térmicas soma as horas equivalentes). Com as horas por estado
  operativo e sem as taxas publicadas, a TEIFa e a TEIP ficam não aplicáveis com o motivo próprio ("a usina não consta
  das taxas TEIFa e TEIP publicadas pelo ONS no período").
- **Motivo**: FR-022. Na UTE William Arjona, a TEIFa refeita não reproduz nenhum dos 4 meses de janela completa
  (−2,07; −0,92; −0,53 e −0,08 p.p. de 06 a 09/2026): a diferença cai à medida que os meses iniciais saem da janela, o
  que é compatível com uma janela completada por valores de referência nos meses sem histórico, mas não há fonte
  publicada dessa regra nem os valores de referência da usina.
- **Alternativas rejeitadas**: ajustar o recálculo das térmicas por suposição, sem fonte publicada pelo ONS.

### D17 — Alinhamento da hidrologia pela geração, nas hidrelétricas sem EVT
- **Decisão**: `vazoes.alinhar_com_geracao` correlaciona (Pearson) a vazão turbinada tratada, depois de `limpos`, com a
  geração da base horária comum no nível da usina, com a hidrologia deslocada de −1, 0 e +1 hora
  (`DESLOCAMENTOS_ALINHAMENTO_H`). A correlação é indefinida (NaN) com menos de duas horas ou série constante, sem divisão
  por zero. O alinhamento é confirmado quando a correlação sem deslocamento é maior que cada outra definida. O resultado
  conta as horas comuns sem deslocamento, todas coincidentes se confirmado e todas divergentes se não; não tem período,
  tolerância nem meta, e nunca dá o código 3.
- **Motivo**: FR-026 e decisão do usuário de 22/10/2026. Sem a EVT, a geração da própria usina é a única série horária
  que responde à vazão turbinada. Sem histórico, a meta seria arbitrária (D13), e a convenção de hora nunca é ajustada
  automaticamente (D14).
- **Alternativas rejeitadas**: aplicar a meta de 99 % e o código 3 das vazões, que comparam a mesma grandeza em duas
  fontes, e não uma correlação.

### D18 — Formato 2 do `etapa.json`, pickle na versão 1
- **Decisão**: `src/pipeline.VERSAO_FORMATO["conferencia"]` passou a 2, porque as Análises passaram a exigir
  `nao_aplicaveis.csv`; o pré-requisito das Análises recusa o formato 1 com o código 5. O pickle continua na versão 1
  (`resultado.VERSAO_FORMATO`): o `ResultadoConferencia` não mudou de campos, só ganhou ids. Os CSV das conferências
  novas são arquivos opcionais e não mudam o formato.
- **Motivo**: a versão do formato sobe quando muda um arquivo que a etapa já grava ou quando a etapa seguinte passa a
  exigir um arquivo novo; arquivo novo opcional não a muda.
- **Alternativas rejeitadas**: camadas de compatibilidade de leitura, que seriam código a mais para um único refazer,
  sem download.

### Desvios registrados na implementação

| Data | O que mudou | Aprovação |
|---|---|---|
| 22/10/2026 | O alinhamento da hidrologia pela geração não ganha linha em `nao_aplicaveis.csv` fora das hidrelétricas, embora a regra aprovada fosse "todas as conferências do catálogo que não se aplicam". Nos demais tipos, a conferência das vazões já registra que a hidrologia não se aplica; assim, os relatórios aprovados da UTE William Arjona e da EOL Praia Formosa não mudam. | usuário, em 22/10/2026, com o relatório da PCH Bandeirante e as referências |

## Complexity Tracking

Sem desvios da constituição. O ponto abaixo traz complexidade e está justificado:

| Ponto | Por que é necessário | Alternativa mais simples rejeitada porque |
|---|---|---|
| Conferências novas sem meta | não há histórico para calibrar | uma meta arbitrária poderia parar o fluxo sem motivo (princípio VI) |
