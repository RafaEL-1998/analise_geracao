# Implementation Plan: Geração do relatório

**Spec**: [spec.md](spec.md) · **Etapa**: 5 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-08

## Summary

A etapa lê os resultados gravados pelas Análises em `resultados.pkl`, que já trazem os da Conferência, as datas de obtenção registradas pela Coleta nos manifestos de `data/raw/` e o perfil da usina, e grava em `reports/<slug>/` o PDF (reportlab), o mesmo relatório em Markdown, a planilha com uma aba por tabela, o CSV dos indicadores anuais e até oito figuras em seaborn. Não calcula resultados: monta a tabela de parâmetros e a origem dos dados, formata e organiza. Uma estrutura única de seções (`estrutura.py`), um módulo de conteúdo comum (`conteudo.py`) e um mapa único de fontes (`fontes.py`) fazem PDF, Markdown e planilha terem as mesmas seções, tabelas e legendas. As saídas são geradas numa pasta temporária, conferidas e só então substituem as da execução anterior. `--data-geracao` fixa a data e torna o PDF reproduzível byte a byte, e a ferramenta `comparar` (`src/comum/comparacao.py`) confere o relatório contra uma versão guardada.

## Technical Context

**Language/Version**: Python 3.11 ou mais recente (venv do projeto com Python 3.14).

**Primary Dependencies**: `pandas` (tabelas, planilha e CSV); `seaborn` sobre `matplotlib`, com o backend `Agg` (figuras); `reportlab` (PDF e sumário com `TableOfContents`); `openpyxl` (motor da planilha, contagem de abas e leitura célula a célula no `comparar`).

**Storage**: arquivos. Entradas: `data/usinas/<slug>/analises/resultados.pkl` (pickle com versão de formato), os `_manifesto_ons.json` dos dez conjuntos em `data/raw/` e `usinas/<slug>/perfil.toml`. Saídas em `reports/<slug>/`: PDF, Markdown (UTF-8), XLSX, CSV (`;`, UTF-8), `figures/*.png` (300 DPI) e `etapa.json`, sem `.bak`. A cada execução, as saídas são geradas em `reports/<slug>/.gravando/` e movidas para o lugar depois de conferidas.

**Testing**: pytest sem rede, com dados sintéticos (`tests/conftest.py` e `tests/relatorio/apoio.py`):
- `tests/relatorio/` (98 testes): estrutura e numeração, mapa de fontes e legendas, PDF, Markdown, bases complementares, conclusão, limpeza das figuras de uma execução anterior e gravação com pasta temporária e troca das saídas;
- `tests/comum/test_comparacao.py` (9 testes): a ferramenta `comparar`, inclusive planilha ilegível;
- `tests/comum/test_conformidade.py` e `tests/comum/test_literais.py`: seaborn em toda figura, dependências e nenhum valor da São Domingos em `src/`;
- `tests/integracao/`: linha de comando e usina fictícia de três unidades geradoras, de ponta a ponta.

**Target Platform**: Windows 11, local, PowerShell, venv.

**Project Type**: projeto único, pipeline de linha de comando (`python -m src`).

**Performance Goals**: até 1 minuto com os resultados das Análises gravados (SC-012). Na São Domingos, 20 s (`etapa.json`: iniciada às 13:54:19Z e concluída às 13:54:39Z), com o PDF montado em duas passagens.

**Constraints**:
- sem rede e sem cálculo novo: só apresenta o que as etapas anteriores gravaram (FR-001);
- com a mesma `--data-geracao` e o mesmo ambiente (Windows, fonte Arial, mesmas versões das dependências), PDF, Markdown, CSV e figuras idênticos byte a byte e planilha idêntica célula a célula (FR-005);
- nenhum valor próprio de usina no código: tudo vem do perfil ativo (FR-019);
- uma falha não deixa relatório misturado: as saídas da execução anterior só são trocadas depois de todas as novas conferidas, e voltam se a troca falhar (FR-003);
- capa só na página 1 e conclusão numa página do PDF.

**Scale/Scope** (São Domingos, com os dez conjuntos):
- 70.895 registros horários, de 28/08/2018 a 28/09/2026 (nove anos civis, 2018 e 2026 parciais);
- 17 seções, 17 constatações e 19 itens da conclusão;
- PDF com 30 páginas (2,3 MB); Markdown com 768 linhas, 30 tabelas, 8 figuras e 38 legendas de fonte;
- planilha com 58 abas (2,9 MB), a maior com 61.067 linhas (HID_HORAS_EVT); CSV com 9 anos e 29 colunas; 8 figuras (1,6 MB).

## Constitution Check

| Princípio / requisito da constituição 2.0.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | spec única da etapa; lê só os resultados das Análises, os manifestos da Coleta e o perfil; sem as Análises concluídas, sai com código 5 sem gravar nada |
| II. Relatório fiel aos dados | cumpre | todo número e frase vem de `ResultadosAnalise`, do perfil ativo ou de `src/comum/regras.py`; cada constatação uma vez, no início da sua seção; a conclusão das Análises só é apresentada; seção, figura e aba sem base são omitidas |
| III. Uma usina por execução | cumpre | `--usina` e `perfil_ativo()`; nome, identificadores, parâmetros e fontes vêm do perfil; teste de literais e teste com usina fictícia |
| IV. Coleta completa e rastreável | não se aplica | a etapa não coleta; só apresenta a auditoria da Coleta (quadro da cobertura e abas de auditoria) |
| V. Tratamento sem descarte | cumpre | informa as sinalizações: regras R1 a R9, registros sinalizados, regras H1 a H4 e horas inconsistentes nas notas |
| VI. Conferência entre fontes | cumpre | as legendas citam as seis conferências refeitas pelo fluxo, com o resultado, ou "não feita nesta execução"; conferências manuais não aparecem; cruzamentos hidrológicos omitidos abaixo da meta |
| VII. Relatório padronizado | cumpre | estrutura fixa; legenda de fonte em toda figura, tabela e bloco; PDF e Markdown com o mesmo conteúdo; aba FONTES; figuras em seaborn com tema, paleta, tamanhos e resolução centralizados e paleta conferida para deficiência de visão de cores |
| Req. 1 — Python, venv e dependências | cumpre | cinco dependências diretas (pandas, matplotlib, seaborn, reportlab e openpyxl), todas em `requirements.txt`, o que um teste confere; código tipado e documentado |
| Req. 2 — Windows e PowerShell | cumpre | fontes TrueType de `%WINDIR%\Fonts`; exemplos em PowerShell |
| Req. 3 — Gravação segura | cumpre | relatórios sem `.bak`, como a constituição prevê; as saídas são geradas em `.gravando/`, conferidas no disco e só então trocadas com `os.replace`; se a geração ou a troca falharem, as da execução anterior ficam como estavam; código 1 e `etapa.json` em `falha` |
| Req. 4 — Versões dos brutos | não se aplica | só lê os manifestos |
| Req. 5 — Cópias de segurança | não se aplica | ferramenta da Coleta; as versões aprovadas do relatório ficam nessas cópias e servem de referência ao `comparar` |
| Req. 6 — Pastas | cumpre | `reports/<slug>/` e `reports/<slug>/figures/` |
| Req. 7 — Log | cumpre | logger `relatorio`, no nível único da linha de comando, mantido pelos módulos importados depois dela; o resumo e a pasta saem no fim da etapa |
| Qualidade 1 — testes sem rede | cumpre | suítes listadas em Testing |
| Qualidade 2 — comparação com a referência | cumpre | `--data-geracao` e `comparar` |

## Project Structure

### Documentation (this feature)

```text
specs/005-geracao-relatorio/
├── spec.md
├── plan.md
├── data-model.md
├── contracts/
│   └── cli-relatorio.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/relatorio/
├── etapa.py        # executar_relatorio: carrega os resultados, completa parâmetros e fontes, gera as saídas em .gravando/, confere (_conferir_saidas) e troca (_trocar_saidas)
├── estrutura.py    # SECOES, MAPA_CONSTATACOES, secoes_presentes, constatacoes_da_secao, sumario
├── conteudo.py     # conteúdo comum ao PDF e ao Markdown: linhas das tabelas, textos, notas, legendas, capa (com orgao_garantia_fisica) e conclusão
├── fontes.py       # mapa único de fontes (CONJUNTOS, CONFERENCIAS, MAPA_FONTES, abas), legendas e aba FONTES
├── parametros.py   # tabela "Parâmetros utilizados" (aba PARAMETROS)
├── figuras.py      # gerar_graficos: oito figuras em seaborn, tema, paleta e nomes dos arquivos
├── pdf.py          # PDFReportGenerator: PDF A4 paisagem, capa, sumário, seções e paginação
├── markdown.py     # gerar_relatorio_md: Markdown com a estrutura do PDF
└── planilha.py     # exportar_tabelas: planilha (FONTES por último) e CSV dos indicadores anuais

src/comum/
├── comparacao.py   # ferramenta comparar (comparar, executar_comparacao)
├── caminhos.py     # ARQUIVOS_RELATORIO, pasta_relatorio, pasta_etapa, RAW_DATA_DIR
├── regras.py       # limiares, tolerâncias, metas, conjuntos e endereços do ONS, DPI e tamanho padronizado, limiares da conclusão
├── formatacao.py   # números, datas e listas no padrão brasileiro
├── perfil.py       # perfil_ativo()
└── logger.py       # setup_logger("relatorio")
src/pipeline.py     # executar_etapa: pré-requisito, perfil ativo e etapa.json
src/__main__.py     # comandos relatorio e comparar; --data-geracao (ler_data_geracao)
```

A etapa usa constantes e funções de texto de outras etapas, sem recalcular nada; nenhuma delas importa `src.relatorio`:
- `src/analises/`: `ResultadosAnalise` e `carregar_resultados`; `LISTAS_CONCLUSAO` e as frases da conclusão; `texto_conferencia_geracao` e `_texto_alinhamento`; rótulos das faixas de afluência e dos grupos de dias; `DESCRICAO_PARCELA`, `DESCRICAO_CLASSES` e `SEM_PROGRAMACAO`;
- `src/tratamento/`: `INSUMOS_HORAS`, `faixa_produtividade` e `TOLERANCIA_IDENTIDADE_HORAS` (definida em `regras.py`);
- `src/conferencia/resultado.py`: `diferenca_absoluta` (|diferença| arredondada a 9 casas), só na contagem de reserva da legenda da TEIFa e da TEIP, quando os resultados não trazem a contagem da Conferência;
- `src/coleta/conjuntos.py`: `data_obtencao` (data mais recente de um manifesto).

```text
tests/relatorio/
├── apoio.py               # ResultadosAnalise sintético, com conferências, parâmetros e fontes, como na etapa
├── test_estrutura.py      # ordem e numeração, constatação → seção, capa e sumário, PDF = Markdown, paginação, cadastro na capa, figuras padronizadas, conclusão, figura opcional antiga apagada
├── test_fontes.py         # catálogo e mapa, legendas, conferências (TEIFa e TEIP pela contagem da Conferência), "não feita nesta execução", aba FONTES (DICIONARIOS com os dez conjuntos), órgão da garantia física, rótulo das horas sem programação
├── test_complementar.py   # bases complementares: seções, abas, figuras 06 a 08, legenda em toda tabela e figura, notas
├── test_gravacao.py       # pasta temporária apagada; falha na geração ou na troca mantém as saídas anteriores; restauração incompleta guarda as anteriores em .anteriores_<data>
├── test_markdown.py       # Markdown com os valores calculados, figuras só com a EVT, limite de itens da conclusão
└── test_pdf.py            # PDF com e sem figuras, legendas = itens desenhados, rodapé, sumário, --data-geracao
tests/comum/test_comparacao.py           # igualdade, célula, byte, arquivo a mais, ordem das abas, etapa.json, tolerância, planilha ilegível
tests/comum/test_conformidade.py         # seaborn em toda função _grafico_*, dependências
tests/comum/test_literais.py             # nenhum valor da São Domingos em src/
tests/integracao/test_cli.py             # opções de relatorio e comparar, data inválida (código 2), completo, comparar 0/6/1
tests/integracao/test_usina_ficticia.py  # fluxo completo de usina fictícia de três unidades, sem a São Domingos no relatório
```

## Fluxo de execução

1. `src/__main__.main` lê a linha de comando. `ler_data_geracao` converte `--data-geracao` ("DD/MM/AAAA HH:MM"); formato inválido termina com código 2 antes de qualquer execução. Seguem `configurar_nivel_log` e `carregar_perfil` (perfil inválido: código 4).
2. `pipeline.executar_etapa("relatorio", perfil, data_geracao=…)` confere o `etapa.json` das Análises (`status` `concluida` e `versao_formato` 1). Sem isso, registra a mensagem com o comando das Análises e devolve 5, sem gravar nada. Depois define o perfil ativo e chama `executar_relatorio(perfil, data_geracao)`.
3. `carregar_resultados` lê `analises/resultados.pkl` e recusa outra versão de formato (`ValueError`).
4. `completar_resultados` monta `res.parametros` (`tabela_parametros` e as linhas de disponibilidade, hidrologia, geração e cadastro, se carregados) e `res.fontes` (`origem_dos_dados`: datas de obtenção e conjuntos carregados).
5. A pasta temporária `reports/<slug>/.gravando/` (`PASTA_TEMPORARIA`) é recriada vazia. Nela, `gerar_graficos` grava as cinco figuras fixas e as opcionais cuja condição é atendida (`{chave: caminho}`), e `exportar_tabelas` grava a planilha e o CSV.
6. A data de geração é calculada uma vez (`gerado_em = data_geracao or datetime.now()`). `gerar_relatorio_md` grava o Markdown com ela; `PDFReportGenerator(…, data_geracao=gerado_em, invariante=data_geracao is not None).build_pdf` monta a capa e as seções de `secoes_presentes` com `multiBuild`, no modo invariante só com `--data-geracao`.
7. `_conferir_saidas` confere no disco que cada saída existe e não está vazia e que o PDF começa com `%PDF-`. A planilha é aberta para contar as abas e fechada antes da troca. O `resumo` reúne a mesma data de geração, as seções, as páginas do PDF (`paginas_do_pdf`), as figuras e as abas.
8. `_trocar_saidas` move cada saída para `reports/<slug>/` com `os.replace`, guardando a anterior em `.gravando/.anteriores/` durante a troca. Se algo falhar, cada arquivo volta à versão anterior, um de cada vez; o que não voltar tem a versão anterior movida para `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`, citada no log. A pasta `.gravando/` é apagada num `finally`, com ou sem erro. Depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/`, e a função devolve `ResultadoEtapa(codigo=0, arquivos=[pdf, md, xlsx, csv, figuras…], resumo)`, com os caminhos finais.
9. `executar_etapa` grava `reports/<slug>/etapa.json` com o SHA-256 de cada arquivo e registra o resumo e a pasta no log. Qualquer exceção (resultado em formato antigo, campo ausente, falha na geração, na conferência ou na troca) vira código 1, com o erro no log e `status` `falha`; a interrupção pelo usuário (Ctrl+C) também, com `resumo` `{"erro": "interrompida pelo usuário"}`. Em todos esses casos, as saídas da execução anterior ficam como estavam, salvo a que não voltar de uma troca interrompida, guardada em `.anteriores_<AAAAMMDDTHHMMSS>/`.

`comparar` não é etapa: carrega o perfil só para achar `reports/<slug>/`, compara com `--referencia`, imprime as diferenças e devolve 0 ou 6, sem gravar nada e sem conferir `etapa.json`; qualquer erro (pasta inexistente, planilha ilegível) sai como "Erro na comparação: …", com código 1.

## Decisões técnicas

### D1 — Estrutura única das seções
- **Decisão**: `estrutura.SECOES` lista as 17 seções em ordem, cada uma com chave, título e condição de presença sobre `ResultadosAnalise`; `secoes_presentes` numera as presentes sem lacunas. `MAPA_CONSTATACOES` liga o título de cada constatação à chave da seção; sem destino, ou com a seção ausente, a constatação vai para `cobertura`, com aviso no log. O PDF (`_secao_<chave>`) e o Markdown (`_md_conteudo_secao`) percorrem a mesma lista.
- **Motivo**: mesmas seções, mesma ordem e cada constatação uma vez nas duas saídas (FR-007, FR-009).
- **Alternativas rejeitadas**: modelo abstrato de documento com dois renderizadores (reescrita grande); duas ordens conferidas por teste (a divergência voltaria a cada mudança).

### D2 — Conteúdo comum ao PDF e ao Markdown
- **Decisão**: `conteudo.py` gera uma vez as linhas formatadas de cada tabela (`linhas_tabela_*`), o subtítulo e a nota de cada tabela (`textos_tabelas`), as notas, as legendas descritivas (`legenda_figura`), os blocos e os indicadores da capa e as listas da conclusão. Onde as duas saídas tinham colunas diferentes, ficou a versão do PDF. Os valores das regras gerais citados nos textos (como `LIMIAR_GERACAO_PARADA_MW`, `LIMIAR_DESVIO_PROGRAMACAO_MW` e `JANELA_TAXAS_MESES`) são formatados das constantes de `regras.py`, e o órgão ao lado da garantia física na capa (`orgao_garantia_fisica`) é o início de `parametros.fontes.garantia_fisica`, até a primeira vírgula.
- **Motivo**: os mesmos números e textos nas duas saídas, sem valor fixo no código (FR-018, FR-019); a formatação brasileira fica em `src/comum/formatacao.py`.

### D3 — Mapa único de fontes
- **Decisão**: `fontes.py` declara `CONJUNTOS` (nome, modelo do identificador preenchido pelo perfil e id no catálogo), `CONFERENCIAS` (dado, conjunto que permite a conferência e texto do resultado), `MAPA_FONTES` (chave → conjuntos, conferências, dados sem outra fonte e cálculo do relatório) e o mapa das abas (nomes exatos e prefixos). As chaves são as das figuras, `tab_*` e `bloco_*`. A legenda cita os conjuntos carregados; a linha DICIONARIOS da aba FONTES cita os dez, carregados ou não (`Entrada.todos`), porque os dicionários de todos são obtidos; a data de obtenção é o maior `registrado_em_utc` do manifesto de cada conjunto, lido na geração; os resultados das conferências são os que a Conferência gravou e que chegam em `ResultadosAnalise`, inclusive a contagem de meses reproduzidos da TEIFa e da TEIP (`ons["recalculo_resumo"]`).
- **Motivo**: PDF, Markdown e planilha com a mesma origem (FR-023 a FR-028); os prefixos fixos ("Fonte dos dados:", "Calculado neste relatório a partir de:") permitem contar as legendas nos testes.
- **Alternativas rejeitadas**: texto de fonte em cada seção (repetição e resultados fixos); campo de fonte em cada `linhas_tabela_*` (mistura conteúdo com rastreabilidade).

### D4 — PDF em reportlab
- **Decisão**: A4 paisagem, margens de 36 pt (laterais), 50 pt (superior) e 42 pt (inferior); fontes TrueType Arial (`%WINDIR%\Fonts`) ou DejaVu Sans (distribuída com o matplotlib), com Helvetica e aviso no log se nenhuma existir; canvas de duas passagens (`_canvas_numerado`) para o cabeçalho a partir da página 2 e "Página X de Y"; título, assunto e autor gerados de `usina.nome` e do período. O sumário é um `TableOfContents` em duas colunas (`_SumarioDuasColunas`), alimentado por `afterFlowable` e resolvido por `multiBuild`; a capa termina com `PageBreak`.
- **Motivo**: ≤, ≥ e − exigem fonte TrueType; a página real de cada seção exige duas passagens (FR-011, FR-014, FR-015).

### D5 — Paginação
- **Decisão**: figura e legendas num `KeepTogether`, com altura máxima de 285 pt (`ALTURA_MAXIMA_FIGURA`), exceto as `FIGURAS_PADRONIZADAS`, desenhadas na largura útil; tabela de até 12 linhas inteira (`LINHAS_TABELA_INTEIRA`); a mais longa começa na página corrente se couberem o subtítulo e 6 linhas (`LINHAS_MINIMAS_NA_PAGINA`, por `CondPageBreak`) e repete o cabeçalho (`repeatRows=1`); título e constatações sempre juntos e, até 150 pt (`ALTURA_ABERTURA_CURTA`), também com o primeiro bloco; conclusão inteira num `KeepTogether`. Com o cadastro, os três blocos da capa ocupam 26 %, 38 % e 36 % da largura (`BLOCOS_CAPA_TRES`).
- **Motivo**: sem meia página em branco, capa numa página e conclusão numa página (FR-014, FR-016, FR-031).

### D6 — Figuras em seaborn, com tema único
- **Decisão**: cada `_grafico_*` desenha as marcas com seaborn dentro de `_tema_graficos`, que aplica `sns.set_theme(style="ticks", palette=PALETA_CATEGORICA, rc=_estilo_graficos())` num `plt.rc_context` e restaura o estado ao sair: `lineplot` (01, 06 e 08), `histplot` com `weights` e `multiple="stack"` (02, 05 e 07), `heatmap` (03) e `barplot` com `hue` (04). Linhas de referência, faixas e anotações vão nos mesmos eixos. O seaborn empilha da última categoria (base) para a primeira (topo), por isso o `hue_order` das barras empilhadas é invertido. Fonte Arial (ou DejaVu Sans) de 9 pt, título à esquerda, grade leve, legenda abaixo dos eixos e rótulos das referências à direita, fora da área dos dados; números no padrão brasileiro e anos parciais com "*" e a nota "* ano parcial".
- **Motivo**: regra da constituição para todo gráfico (FR-035); `barplot` não empilha, e o `histplot` ponderado é o empilhamento nativo.
- **Alternativas rejeitadas**: `seaborn.objects` (API experimental); matplotlib puro (viola a constituição).

### D7 — Paleta das figuras
- **Decisão**: cores fixas por grandeza, constantes de `src/relatorio/figuras.py`, validadas sobre fundo branco com o validador de paleta da skill de visualização de dados:

  | Grandeza | Constante | Cor |
  |---|---|---|
  | geração | `COR_GERACAO` | azul `#2a78d6` |
  | disponibilidade | `COR_DISPONIBILIDADE` | verde `#1baf7a` |
  | EVT | `COR_EVT` | laranja `#eb6834` |
  | contexto (vertimento mínimo, vertida não turbinável, sem dado) | `COR_CONTEXTO` | cinza `#b5b3ac` |
  | disponibilidade sincronizada | `COR_SINCRONIZADA` | amarelo `#eda100` |
  | vazão afluente | `COR_AFLUENCIA` | violeta `#4a3aa7` |
  | geração por ano e hora (figura 03) | `RAMPA_AZUL` | oito tons, de `#f3f8fe` a `#0d366b` |
  | EVT por ano e hora (figura 03) | `RAMPA_LARANJA` | sete tons, de `#fdf3ee` a `#8c3612` |
  | faixas de afluência (figura 07) | `RAMPA_FAIXAS_AFLUENCIA` | `#ef8a5d`, `#c24f1f` e `#8c3612` (tons 4, 6 e 7 da rampa laranja) |

  Ordem categórica (`PALETA_CATEGORICA`): geração, disponibilidade, EVT. Tintas `#0b0b0b`, `#52514e` e `#898781`; grade `#e1e0d9`; eixos `#c3c2b7`; faixa de indisponibilidade e janela diurna `#e7e5de`; intervalo branco de 0,8 pt entre barras empilhadas (`LARGURA_INTERVALO_BARRAS`).
- **Motivo**: a mesma cor para a mesma grandeza em todas as figuras e leitura por quem tem deficiência de visão de cores (constituição, VII). O amarelo tem contraste abaixo de 3:1, compensado por rótulo direto e tabela; o violeta é o único que passa em todos os pares com a turbinada e a vertida, linhas que se cruzam; o passo claro da rampa das faixas tem contraste de 2,48:1.
- **Alternativas rejeitadas**: magenta para a afluência, reprovado contra o laranja da vertida (ΔE 12,9).

### D8 — Tamanho e resolução das figuras
- **Decisão**: 300 DPI (`DEFAULT_PLOT_DPI`). As figuras 01, 02, 05 e 06 têm 11 × 4,3 polegadas (`TAMANHO_FIGURA_PADRONIZADA`, 3300 × 1290 px) e, no PDF, a largura útil (cerca de 760 × 297 pt); a 03 tem 11 × 4,4 e é desenhada com 710 × 284 pt; a 04, a 07 e a 08 têm 11 × 4,6 e ficam limitadas a 285 pt de altura.
- **Motivo**: 4,3 polegadas é a maior altura com que a seção de EVT mensal (título, constatações, figura e legendas) cabe numa página (FR-036).

### D9 — Markdown espelho do PDF
- **Decisão**: cabeçalho com título, período e "Gerado em"; blocos da capa e indicadores em tabelas ("Item | Valor" e "Indicador | Valor | Detalhe"); "## Sumário" com links para as âncoras no padrão do GitHub (`_ancora_md`); seções "## N. Título"; figura no corpo da seção, com `![<título da seção>](figures/<arquivo>.png)`, a legenda descritiva e a legenda de fonte; `*` escapado nas notas das tabelas. UTF-8 sem BOM, com o fim de linha do sistema.
- **Motivo**: as mesmas seções, tabelas e figuras do PDF (FR-017).

### D10 — Planilha e CSV
- **Decisão**: `pd.ExcelWriter` com openpyxl, uma aba por tabela, na ordem montada em `exportar_tabelas`; abas das bases complementares só com linhas; FONTES montada por último a partir da lista das demais; cabeçalho congelado (`A2`) e largura de coluna `min(max(len(nome), 12) + 3, 60)`. O CSV é `indicadores_anuais.to_csv(sep=";", index=False, encoding="utf-8")`, com ponto decimal. As colunas das abas são as dos quadros de `ResultadosAnalise`; as auditorias chegam já reduzidas às colunas da FR-038.
- **Motivo**: versão completa dos resultados, com a origem de cada aba (FR-028, FR-038, FR-039).

### D11 — `--data-geracao` e reprodutibilidade
- **Decisão**: `executar_relatorio` calcula a data de geração uma vez, a de `--data-geracao` ou a hora da execução, e a passa ao Markdown, ao PDF e ao `resumo`. Só com `--data-geracao` (`invariante=True`), `rl_config.invariant = 1` vale durante o `multiBuild` (restaurado num `finally`), o que fixa `CreationDate` e `ModDate` em `D:20000101000000+00'00'` e torna o identificador do arquivo determinístico. PNG (só o metadado "Software" do matplotlib), Markdown e CSV já são determinísticos. A planilha não se reproduz byte a byte (o openpyxl grava a hora nas propriedades do arquivo) e é comparada célula a célula.
- **Motivo**: provar a não regressão (FR-004, FR-005, SC-009) sem leitor de PDF no projeto.
- **Alternativas rejeitadas**: comparar só as páginas e o Markdown (fraco); dependência de leitura de PDF só para teste.

### D12 — Ferramenta `comparar`
- **Decisão**: `src/comum/comparacao.py`, fora do pacote da etapa. Percorre as duas pastas recursivamente; ignora todo arquivo `etapa.json`; compara byte a byte todo arquivo que não é `.xlsx`; compara a planilha aba a aba (mesmas abas na mesma ordem, mesma quantidade de linhas, cada célula), com células numéricas iguais por `math.isclose(rel_tol=1e-12, abs_tol=0)`, NaN igual a NaN e booleanos fora da regra numérica; lista até 20 células por aba, com o total numa linha. Qualquer exceção, inclusive planilha ilegível, vira "Erro na comparação: …" na saída de erro e código 1. Não grava nada.
- **Motivo**: os bytes do XLSX mudam a cada gravação; abaixo de 1e-12 relativo, a diferença é resto de ponto flutuante (por exemplo, número lido de um CSV pelo leitor padrão do pandas) e não muda texto nem figura (FR-040).

### D13 — Entrada única e troca conferida das saídas
- **Decisão**: a etapa lê só `resultados.pkl`, os manifestos de `data/raw/` e o perfil; preenche em memória `res.parametros` e `res.fontes`, sem regravar o pickle. Todas as saídas são geradas em `reports/<slug>/.gravando/`, conferidas no disco (`_conferir_saidas`) e só então trocadas, uma a uma, com `os.replace` (`_trocar_saidas`), sem `.bak`. Durante a troca, cada anterior fica em `.gravando/.anteriores/`; se a troca falhar, cada uma volta ao lugar, e a que não puder voltar é preservada em `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`, citada no log. A planilha é fechada antes da troca, porque o Windows não move arquivo aberto. Depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/`. O `etapa.json` guarda o SHA-256 de cada arquivo final.
- **Motivo**: uma falha no meio da geração não deixa relatório misturado nem perde o anterior (FR-003; constituição, Requisito Técnico 3); o relatório é regenerado a partir dos resultados, e as versões aprovadas ficam nas cópias de segurança do projeto.
- **Alternativas rejeitadas**: gravar direto no lugar (uma falha no PDF deixaria as figuras e a planilha novas ao lado do PDF anterior); cópia `.bak` de cada saída (a constituição dispensa os relatórios de `.bak`).

### D14 — Conclusão na apresentação
- **Decisão**: a seção `conclusao`, sempre presente antes das notas, mostra `FRASE_ABERTURA_CONCLUSAO` e as listas de `LISTAS_CONCLUSAO` com até `MAXIMO_ITENS_CONCLUSAO` (5) itens, na ordem de `res.conclusao`. O rótulo "(seção N)" é resolvido na geração (`_rotulo_secoes`): os números das seções de origem presentes, em ordem crescente, juntados por `fmt_lista`. A aba CONCLUSAO (`tabela_conclusao`) traz todos os itens, e a nota metodológica da conclusão (`nota_conclusao`) é montada com as constantes de `regras.py`.
- **Motivo**: a numeração depende das seções presentes, que só o relatório conhece (FR-029 a FR-033).

## Complexity Tracking

Sem desvios da constituição.
