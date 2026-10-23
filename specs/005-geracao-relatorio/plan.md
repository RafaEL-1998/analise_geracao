# Implementation Plan: Geração do relatório

**Spec**: [spec.md](spec.md) · **Etapa**: 5 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-23

## Summary

A etapa lê os resultados gravados pelas Análises em `resultados.pkl`, que já trazem os da Conferência e as datas de obtenção que as Análises leem de `datas_obtencao.csv` da Coleta, e o perfil da usina. Grava em `reports/<slug>/` o PDF (reportlab), o mesmo relatório em Markdown, a planilha com uma aba por tabela, o CSV dos indicadores anuais, as figuras em seaborn e o resumo executivo, em PDF e em Markdown. Não lê `data/raw/` e não calcula resultados: monta a tabela de parâmetros e a origem dos dados, formata e organiza.

- **Dois caminhos** (D15): a hidrelétrica com EVT segue as 17 seções da FR-007, sem mudança, protegida por testes de invariantes (D17); as demais usinas seguem as seções comuns sobre a base horária comum e as seções do tipo, montadas como blocos em `comum.py` e nos módulos `secoes_termica.py`, `secoes_renovavel.py` e `secoes_conjunto.py`, com o nível de cada número nas legendas (D16, D18 a D20).
- **Uma estrutura única** de seções (`estrutura.py`), módulos de conteúdo comuns ao PDF e ao Markdown (`conteudo.py` e `comum.py`) e um mapa único de fontes (`fontes.py`) fazem PDF, Markdown e planilha terem as mesmas seções, tabelas e legendas.
- **Gravação**: as saídas são geradas numa pasta temporária, conferidas e só então substituem as da execução anterior.
- **Resumo executivo** (D23 a D34): montado com as mesmas funções do relatório, depois do PDF dele, na mesma pasta temporária e na mesma troca, com a conclusão copiada igual e a regra das duas páginas.
- **Reprodutibilidade**: `--data-geracao` fixa a data e torna os PDFs reproduzíveis byte a byte. A ferramenta `comparar` (`src/comum/comparacao.py`) confere o relatório contra uma versão guardada; `referencia` e `comparar --todas [--coleta]` (`src/comum/referencias.py`) guardam os relatórios aprovados com a Coleta e o perfil congelados e os refazem num espaço isolado (D21).
- **Carteira** (D22): `python -m src carteira` (`carteira.py`, `carteira_pdf.py` e `carteira_figuras.py`) monta o relatório de um estado, de um tipo ou dos dois só com o que já está gravado.

## Technical Context

**Language/Version**: Python 3.11 ou mais recente (venv do projeto com Python 3.14).

**Primary Dependencies**: `pandas` (tabelas, planilha e CSV); `seaborn` sobre `matplotlib`, com o backend `Agg` (figuras); `reportlab` (PDF e sumário com `TableOfContents`); `openpyxl` (motor da planilha, contagem de abas e leitura célula a célula no `comparar`). O caminho sem EVT, o resumo executivo, a carteira e as referências não trouxeram dependência nova.

**Storage**: arquivos.
- **Relatório**: entradas `data/usinas/<slug>/analises/resultados.pkl` (pickle com versão de formato 3, com as datas de obtenção da Coleta) e `usinas/<slug>/perfil.toml`. Saídas em `reports/<slug>/`: PDF, Markdown (UTF-8), XLSX, CSV (`;`, UTF-8), `figures/*.png` (300 DPI), `resumo_executivo.pdf`, `resumo_executivo.md` e `etapa.json`, sem `.bak`. A cada execução, as saídas são geradas em `reports/<slug>/.gravando/` e movidas para o lugar depois de conferidas.
- **Carteira**: lê `data/catalogo/` (`usinas.csv`, `agregados.csv` e `catalogo.json`), `usinas/*/perfil.toml` e o `etapa.json` e o `resultados.pkl` das Análises de cada usina; grava `reports/carteiras/<nome>/` (`relatorio_carteira.pdf`, `relatorio_carteira.md`, `carteira.xlsx` e `figures/`), pela mesma pasta temporária e troca, sem `.bak`.
- **Referências**: `relatorios_referencia/<slug>/`, com o relatório aprovado e o perfil (no git, o PDF por exceção no `.gitignore`), a Coleta congelada (fora do git) e o `referencia.json`. O `comparar --todas` trabalha num espaço isolado temporário (`caminhos.espaco_isolado`), com um `data/raw/` vazio para as etapas 2 a 5; com `--coleta`, a Coleta refeita lê os brutos de `data/raw/` com `--sem-portal`, sem gravar neles.

**Testing**: pytest sem rede, com dados sintéticos (`tests/conftest.py`, `tests/relatorio/apoio.py` e `tests/fixtures/`); a suíte inteira tinha 840 testes aprovados em 23/10/2026.
- `tests/relatorio/`: estrutura e numeração dos dois caminhos, mapa de fontes e legendas, PDF, Markdown, bases complementares, conclusão, gravação com pasta temporária e troca das saídas, invariantes da hidrelétrica com EVT, resumo executivo e carteira;
- `tests/comum/test_comparacao.py` e `tests/comum/test_referencias.py`: o `comparar`, o `referencia` e o `comparar --todas [--coleta]`;
- `tests/comum/test_conformidade.py` e `tests/comum/test_literais.py`: seaborn em toda figura, gravação segura, dependências e nenhum valor da São Domingos nem identificador das usinas piloto em `src/`;
- `tests/integracao/`: linha de comando, usina fictícia de três unidades geradoras, as sete usinas fictícias (uma por tipo) de ponta a ponta, com o resumo e a carteira, e as etapas 2 a 5 com `data/raw/` vazio.

**Target Platform**: Windows 11, local, PowerShell, venv.

**Project Type**: projeto único, pipeline de linha de comando (`python -m src`).

**Performance Goals**:
- relatório: até 1 minuto com os resultados das Análises gravados (SC-012). Na São Domingos, 20 s (`etapa.json`: iniciada às 13:54:19Z e concluída às 13:54:39Z), com o PDF montado em duas passagens; na William Arjona, 5 s;
- carteira de MS: até 5 minutos (SC-012); na prática, 2,9 s, e 3,1 s na `brasil_ute`;
- `comparar --todas` com as cinco referências: até 20 minutos (as etapas 2 a 5 de cada uma).

**Constraints**:
- sem rede e sem cálculo novo: só apresenta o que as etapas anteriores gravaram, sem ler `data/raw/` (FR-001);
- com a mesma `--data-geracao` e o mesmo ambiente (Windows, fonte Arial, mesmas versões das dependências), PDF, Markdown, CSV, figuras e resumo executivo idênticos byte a byte e planilha idêntica célula a célula (FR-005);
- nenhum valor próprio de usina no código: tudo vem do perfil ativo (FR-019);
- a hidrelétrica com EVT sem nenhuma mudança: um teste por invariante e `comparar --todas` (D17);
- nenhum número de conjunto ou de agregado apresentado como da usina nem dividido entre as usinas (D16);
- uma falha não deixa relatório misturado: as saídas da execução anterior só são trocadas depois de todas as novas conferidas, e voltam se a troca falhar (FR-003);
- capa só na página 1, conclusão numa página do PDF e resumo executivo em até duas páginas.

**Scale/Scope**:
- **São Domingos**, com os dez conjuntos:
  - 70.895 registros horários, de 28/08/2018 a 28/09/2026 (nove anos civis, 2018 e 2026 parciais);
  - 17 seções, 17 constatações e 19 itens da conclusão;
  - PDF com 30 páginas (2,3 MB); Markdown com 768 linhas, 30 tabelas, 8 figuras e 38 legendas de fonte;
  - planilha com 58 abas (2,9 MB), a maior com 61.067 linhas (HID_HORAS_EVT); CSV com 9 anos e 29 colunas; 8 figuras (1,6 MB);
  - resumo executivo com 2 páginas e 933 palavras fora das tabelas.
- **Referências**: cinco usinas piloto aprovadas (UHE São Domingos, UTE William Arjona, UFV Seriemas 1, EOL Praia Formosa e PCH Bandeirante). Exemplos: William Arjona com 15 seções e 27 páginas; Bandeirante, em duas partes, com 6 seções e 13 páginas.
- **Carteira de MS** (catálogo de 22/10/2026): 149 usinas, sem as 22 linhas de conjunto; 4 com resultado e 145 sem (46 só agregado no ONS e 99 sem perfil).

## Constitution Check

| Princípio / requisito da constituição 3.1.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | spec única da etapa, com os dois caminhos, o resumo executivo, a carteira e as referências; lê só os resultados das Análises (com as datas de obtenção da Coleta) e o perfil, sem `data/raw/`; sem as Análises concluídas, sai com código 5 sem gravar nada; a carteira só lê o que está gravado |
| II. Relatório fiel aos dados | cumpre | todo número e frase vem de `ResultadosAnalise`, do perfil ativo ou de `src/comum/regras.py`; cada constatação uma vez, no início da sua seção; a conclusão das Análises só é apresentada, e o resumo a copia igual; seção, figura, conferência e aba sem base são omitidas, com o motivo nas notas nas usinas sem EVT; nenhum termo de parecer, conferido por teste |
| III. Uma usina por execução | cumpre | `--usina` e `perfil_ativo()`; nome, identificadores, parâmetros e fontes vêm do perfil; teste de literais e testes com uma usina fictícia por tipo; a carteira é o produto de várias usinas, só com resultados gravados, sem nota nem parecer |
| IV. Coleta completa e rastreável | não se aplica | a etapa não coleta; só apresenta a auditoria da Coleta (quadro da cobertura e abas de auditoria) |
| V. Tratamento sem descarte | cumpre | informa as sinalizações: regras R1 a R9, registros sinalizados, regras H1 a H4, horas inconsistentes e, nas usinas sem EVT, as horas sinalizadas da base horária comum, mantidas nos totais |
| VI. Conferência entre fontes | cumpre | as legendas citam as conferências refeitas pelo fluxo, com o resultado, ou "não feita nesta execução"; nas usinas sem EVT, só as aplicadas, e as não aplicáveis ficam nas notas, com o motivo; conferências manuais não aparecem; cruzamentos hidrológicos omitidos abaixo da meta |
| VII. Relatório padronizado | cumpre | estrutura fixa com as seções do tipo em ordem fixa; legenda de fonte em toda figura, tabela e bloco, também na carteira; PDF e Markdown com o mesmo conteúdo; aba FONTES; resumo com o bloco "Sobre os dados" e a seção de origem em cada tabela; figuras em seaborn com tema, paleta, tamanhos e resolução centralizados e paletas conferidas para deficiência de visão de cores |
| VIII. Granularidade declarada | cumpre | nível em toda legenda de dado de conjunto ou de agregado; números do conjunto identificados e nunca divididos; relatório em duas partes na usina em conjunto sem série própria; panorama da carteira identificado como agregado (D16, D20, D22) |
| IX. Relatórios aprovados protegidos | cumpre | `referencia` guarda o relatório aprovado com a Coleta e o perfil congelados e recusa substituir uma referência fora do git; `comparar --todas [--coleta]` refaz cada referência num espaço isolado; `copia-seguranca` leva `relatorios_referencia/` (D21) |
| Req. 1 — Python, venv e dependências | cumpre | cinco dependências diretas (pandas, matplotlib, seaborn, reportlab e openpyxl), todas em `requirements.txt`, o que um teste confere; código tipado e documentado |
| Req. 2 — Windows e PowerShell | cumpre | fontes TrueType de `%WINDIR%\Fonts`; exemplos em PowerShell |
| Req. 3 — Gravação segura | cumpre | relatórios e carteiras sem `.bak`, como a constituição prevê; as saídas são geradas em `.gravando/`, conferidas no disco e só então trocadas com `os.replace`; se a geração ou a troca falharem, as da execução anterior ficam como estavam; código 1 e `etapa.json` em `falha`; a referência é gravada numa pasta temporária e conferida antes da troca |
| Req. 4 — Versões dos brutos | não se aplica | não lê os brutos |
| Req. 5 — Cópias de segurança | não se aplica | ferramenta da Coleta; ela leva os relatórios de referência e os confere pelos SHA-256 do `referencia.json` |
| Req. 6 — Pastas | cumpre | `reports/<slug>/`, `reports/<slug>/figures/` e `reports/carteiras/<nome>/` (`carteiras` reservado como slug); `relatorios_referencia/<slug>/` para os relatórios de referência (princípio IX) |
| Req. 7 — Log | cumpre | logger `relatorio` na etapa e na carteira e `pipeline` nas referências, no nível único da linha de comando, mantido pelos módulos importados depois dela; o resumo e a pasta saem no fim da etapa |
| Qualidade 1 — testes sem rede | cumpre | suítes listadas em Testing, com uma usina fictícia por tipo |
| Qualidade 2 — comparação com a referência | cumpre | `--data-geracao`, `comparar` e `comparar --todas --coleta` |

## Project Structure

### Documentation (this feature)

```text
specs/005-geracao-relatorio/
├── spec.md
├── plan.md
├── data-model.md
├── contracts/
│   ├── cli-relatorio.md      # comando relatorio e ferramenta comparar
│   ├── resumo-executivo.md   # o resumo executivo: geração, arquivos e documento
│   ├── cli-carteira.md       # comando carteira
│   └── cli-referencias.md    # comandos referencia e comparar --todas; copia-seguranca com as referências
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/relatorio/
├── etapa.py              # executar_relatorio: carrega os resultados, completa parâmetros e fontes (por caminho), gera as saídas e o resumo em .gravando/, confere (_conferir_saidas) e troca (_trocar_saidas)
├── estrutura.py          # Secao (caminhos, tipos, título por tipo, período mínimo), SECOES, os mapas de constatações dos dois caminhos e das duas partes, secoes_presentes, constatacoes_da_secao, sumario
├── conteudo.py           # conteúdo comum ao PDF e ao Markdown na hidrelétrica com EVT: linhas das tabelas, textos, notas, legendas, capa (titulo_capa_relatorio, orgao_garantia_fisica) e conclusão; nota da conclusão gerada do catálogo (nota_conclusao_catalogo)
├── comum.py              # caminho sem EVT: Bloco e blocos_secao de cada seção, capa (identificação, parâmetros, indicadores), cobertura, níveis, trechos, tabelas, legendas descritivas, notas, tabela de parâmetros e as duas partes
├── secoes_termica.py     # seções de térmica: tabelas, textos, legendas, nota e blocos
├── secoes_renovavel.py   # seções de eólica e solar e aderência à programação; série de referência na restrição (referencia_restricao) e pacote da variante
├── secoes_conjunto.py    # seção "Composição e geração do conjunto": tabelas, legenda, nota e blocos
├── fontes.py             # mapa único de fontes (CONJUNTOS, CONFERENCIAS, MAPA_FONTES, abas), identificador com o nível, legendas, textos curtos das conferências, fontes_resumo e aba FONTES
├── parametros.py         # tabela "Parâmetros utilizados" (aba PARAMETROS) da hidrelétrica com EVT
├── figuras.py            # gerar_graficos: oito figuras em seaborn da hidrelétrica com EVT, tema, paleta e nomes; chama figuras_comum no caminho sem EVT
├── figuras_comum.py      # figuras 01 a 15 do caminho sem EVT, em seaborn (comuns, térmica, eólica e solar, conjunto e vazões)
├── pdf.py                # PDFReportGenerator: PDF A4 paisagem, capa, sumário, seções dos dois caminhos (_secao_blocos) e paginação
├── markdown.py           # gerar_relatorio_md: Markdown com a estrutura do PDF, nos dois caminhos (_md_blocos)
├── planilha.py           # exportar_tabelas: planilha dos dois caminhos (FONTES por último) e CSV dos indicadores anuais
├── resumo.py             # ResumoExecutivo, montar_resumo, COLUNAS_RESUMO_ANUAL, Markdown e gerar_resumo (regra das duas páginas)
├── resumo_pdf.py         # gerar_resumo_pdf: A4 retrato, blocos emitidos; paginas_do_pdf
├── carteira.py           # relatório de carteira: recorte, situação de cada usina, ordenação, panorama, documento em blocos, Markdown, planilha, gravação e executar_carteira
├── carteira_pdf.py       # gerar_pdf_carteira: A4 retrato, com os estilos do resumo executivo
└── carteira_figuras.py   # as duas figuras da carteira, em seaborn

src/comum/
├── comparacao.py         # ferramenta comparar (comparar, executar_comparacao) e comparar --todas [--coleta] (executar_comparacao_todas)
├── referencias.py        # comando referencia (registrar_referencia), conferência dos congelados e das referências
├── caminhos.py           # ARQUIVOS_RELATORIO, ARQUIVOS_CARTEIRA, pasta_relatorio, pasta_carteira, pasta_referencia, espaco_isolado
├── regras.py             # limiares, tolerâncias, metas, conjuntos e endereços do ONS, DPI e tamanhos das figuras, limiares da conclusão, GLOSSARIO_RESUMO e limites do resumo
├── formatacao.py         # números, datas e listas no padrão brasileiro
├── perfil.py             # perfil_ativo(); carteiras como slug reservado
└── logger.py             # setup_logger("relatorio") e setup_logger("pipeline")
src/pipeline.py           # executar_etapa: pré-requisito, perfil ativo e etapa.json
src/__main__.py           # comandos relatorio, comparar (--usina/--referencia ou --todas [--coleta]), referencia e carteira; --data-geracao (ler_data_geracao) e --aprovado-em
```

A etapa usa constantes e funções de texto de outras etapas, sem recalcular nada; nenhuma delas importa `src.relatorio`:
- `src/analises/`: `ResultadosAnalise`, `carregar_resultados` e `sem_evt`; `LISTAS_CONCLUSAO`, as frases da conclusão, `frase_sem_itens`, `regras_do_tipo` e `regras_omitidas`; `texto_conferencia_geracao` e `_texto_alinhamento`; rótulos das faixas de afluência e dos grupos de dias; `DESCRICAO_PARCELA`, `DESCRICAO_CLASSES` e `SEM_PROGRAMACAO`; `em_duas_partes` e `TITULO_CONJUNTO`; os títulos das seções de eólica e solar e as razões da restrição; `NOME_NIVEL`; `INDICADORES_CARTEIRA`;
- `src/tratamento/`: `INSUMOS_HORAS`, `faixa_produtividade` e `TOLERANCIA_IDENTIDADE_HORAS` (definida em `regras.py`);
- `src/conferencia/`: `diferenca_absoluta` (|diferença| arredondada a 9 casas), só na contagem de reserva da legenda da TEIFa e da TEIP, quando os resultados não trazem a contagem da Conferência; `CATALOGO_CONFERENCIAS`, para a descrição das conferências que não se aplicam;
- `src/coleta/`: o registro dos conjuntos (tipos, pacotes, conjuntos da usina e nível coletado), a escolha da série de referência (`escolher`) e, na carteira, a leitura e o filtro do catálogo (`ler_catalogo`, `filtrar`).

```text
tests/relatorio/
├── apoio.py                  # ResultadosAnalise sintético, com conferências, parâmetros e fontes, como na etapa
├── test_estrutura.py         # ordem e numeração dos dois caminhos, constatação → seção, capa e sumário, PDF = Markdown, paginação, cadastro na capa, figuras padronizadas, conclusão, figura opcional antiga apagada
├── test_fontes.py            # catálogo e mapa, legendas, conferências, "não feita nesta execução", aba FONTES, textos curtos e fontes do resumo
├── test_complementar.py      # bases complementares: seções, abas, figuras 06 a 08, legenda em toda tabela e figura, notas
├── test_gravacao.py          # pasta temporária apagada; falha na geração, no resumo ou na troca mantém as saídas anteriores
├── test_invariantes_uhe.py   # um teste por invariante da hidrelétrica com EVT, contra tests/fixtures/invariantes_uhe.json (D17)
├── test_markdown.py          # Markdown com os valores calculados, figuras só com a EVT, limite de itens da conclusão
├── test_pdf.py               # PDF com e sem figuras, legendas = itens desenhados, rodapé, sumário, --data-geracao
├── test_resumo.py            # verificações automáticas do resumo executivo (D32)
└── test_carteira.py          # recorte, motivos, ordenação, indicadores vazios, panorama, planilha, legendas, FONTES, termos de parecer, códigos
tests/comum/test_comparacao.py           # igualdade, célula, byte, arquivo a mais, ordem das abas, etapa.json, tolerância, planilha ilegível
tests/comum/test_referencias.py          # referencia (congelados, data, git, formato) e comparar --todas [--coleta]
tests/comum/test_conformidade.py         # seaborn em toda função _grafico_*, gravação segura, dependências
tests/comum/test_literais.py             # nenhum valor da São Domingos nem identificador das usinas piloto em src/
tests/integracao/test_cli.py             # opções de relatorio e comparar, data inválida (código 2), completo, comparar 0/6/1
tests/integracao/test_usina_ficticia.py  # fluxo completo de usina fictícia de três unidades, sem a São Domingos no relatório, com o resumo
tests/integracao/test_usinas_ficticias.py  # as sete usinas fictícias de ponta a ponta: seções do caminho, níveis, resumo e carteira
tests/integracao/test_sem_raw.py         # etapas 2 a 5 com data/raw/ vazio
```

## Fluxo de execução

1. `src/__main__.main` lê a linha de comando. `ler_data_geracao` converte `--data-geracao` ("DD/MM/AAAA HH:MM"); formato inválido termina com código 2 antes de qualquer execução. Seguem `configurar_nivel_log` e `carregar_perfil` (perfil inválido: código 4).
2. `pipeline.executar_etapa("relatorio", perfil, data_geracao=…)` confere o `etapa.json` das Análises (`status` `concluida` e `versao_formato` 3). Sem isso, registra a mensagem com o comando das Análises e devolve 5, sem gravar nada. Depois define o perfil ativo e chama `executar_relatorio(perfil, data_geracao)`.
3. `carregar_resultados` lê `analises/resultados.pkl` e recusa outra versão de formato (`ValueError`).
4. `completar_resultados` monta `res.parametros` e `res.fontes` (`origem_dos_dados`: datas de obtenção, lidas de `res.datas_obtencao`, e conjuntos carregados). Na hidrelétrica com EVT, `tabela_parametros` e as linhas de disponibilidade, hidrologia, geração e cadastro, se carregados; na usina sem EVT (`sem_evt(res)`), `comum.tabela_parametros`.
5. A pasta temporária `reports/<slug>/.gravando/` (`PASTA_TEMPORARIA`) é recriada vazia. Nela, `gerar_graficos` grava as figuras do caminho (`{chave: caminho}`), e `exportar_tabelas` grava a planilha e o CSV.
6. A data de geração é calculada uma vez (`gerado_em = data_geracao or datetime.now()`). `gerar_relatorio_md` grava o Markdown com ela; `PDFReportGenerator(…, data_geracao=gerado_em, invariante=data_geracao is not None).build_pdf` monta a capa e as seções de `secoes_presentes` com `multiBuild`, no modo invariante só com `--data-geracao`. As seções do caminho sem EVT, sem construtor próprio, são desenhadas por `_secao_blocos` a partir de `comum.blocos_secao`.
7. `gerar_resumo` monta o resumo executivo com as páginas do PDF recém-gerado (`paginas_do_pdf`), grava o PDF do resumo, aplica a regra das duas páginas e grava o Markdown (D31).
8. `_conferir_saidas` confere no disco que cada saída existe e não está vazia e que os PDFs começam com `%PDF-`. A planilha é aberta para contar as abas e fechada antes da troca. O `resumo` reúne a mesma data de geração, as seções, as páginas do PDF, as figuras, as abas e o `resumo_executivo`.
9. `_trocar_saidas` move cada saída para `reports/<slug>/` com `os.replace`, guardando a anterior em `.gravando/.anteriores/` durante a troca. Se algo falhar, cada arquivo volta à versão anterior, um de cada vez; o que não voltar tem a versão anterior movida para `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`, citada no log. A pasta `.gravando/` é apagada num `finally`, com ou sem erro. Depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/` (as dos dois caminhos), e a função devolve `ResultadoEtapa(codigo=0, arquivos=[pdf, md, xlsx, csv, resumo_pdf, resumo_md, figuras…], resumo)`, com os caminhos finais.
10. `executar_etapa` grava `reports/<slug>/etapa.json` com o SHA-256 de cada arquivo e registra o resumo e a pasta no log. Qualquer exceção (resultado em formato antigo, campo ausente, falha na geração, resumo acima de duas páginas, falha na conferência ou na troca) vira código 1, com o erro no log e `status` `falha`; a interrupção pelo usuário (Ctrl+C) também, com `resumo` `{"erro": "interrompida pelo usuário"}`. Em todos esses casos, as saídas da execução anterior ficam como estavam, salvo a que não voltar de uma troca interrompida, guardada em `.anteriores_<AAAAMMDDTHHMMSS>/`.

`comparar` não é etapa: carrega o perfil só para achar `reports/<slug>/`, compara com `--referencia`, imprime as diferenças e devolve 0 ou 6, sem gravar nada e sem conferir `etapa.json`; qualquer erro (pasta inexistente, planilha ilegível) sai como "Erro na comparação: …", com código 1. `comparar --todas`, `referencia` e `carteira` estão em D21 e D22 e nos contratos.

## Decisões técnicas

### D1 — Estrutura única das seções
- **Decisão**: `estrutura.SECOES` lista as seções em ordem, cada uma com chave, título e condição de presença sobre `ResultadosAnalise`; `secoes_presentes` numera as presentes sem lacunas. `MAPA_CONSTATACOES` liga o título de cada constatação à chave da seção; sem destino, ou com a seção ausente, a constatação vai para a primeira seção (`cobertura`), com aviso no log. O PDF (`_secao_<chave>`) e o Markdown (`_md_conteudo_secao`) percorrem a mesma lista. Os dois caminhos estão em D15.
- **Motivo**: mesmas seções, mesma ordem e cada constatação uma vez nas duas saídas (FR-007, FR-009).
- **Alternativas rejeitadas**: modelo abstrato de documento com dois renderizadores (reescrita grande); duas ordens conferidas por teste (a divergência voltaria a cada mudança).

### D2 — Conteúdo comum ao PDF e ao Markdown
- **Decisão**: `conteudo.py` gera uma vez as linhas formatadas de cada tabela (`linhas_tabela_*`), o subtítulo e a nota de cada tabela (`textos_tabelas`), as notas, as legendas descritivas (`legenda_figura`), os blocos e os indicadores da capa e as listas da conclusão. Onde as duas saídas tinham colunas diferentes, ficou a versão do PDF. Os valores das regras gerais citados nos textos (como `LIMIAR_GERACAO_PARADA_MW`, `LIMIAR_DESVIO_PROGRAMACAO_MW` e `JANELA_TAXAS_MESES`) são formatados das constantes de `regras.py`, e o órgão ao lado da garantia física na capa (`orgao_garantia_fisica`) é o início de `parametros.fontes.garantia_fisica`, até a primeira vírgula. O título da capa vem de uma função só (`titulo_capa_relatorio`), também citada no resumo executivo. No caminho sem EVT, o mesmo papel é de `comum.py` (D15).
- **Motivo**: os mesmos números e textos nas duas saídas, sem valor fixo no código (FR-018, FR-019); a formatação brasileira fica em `src/comum/formatacao.py`.

### D3 — Mapa único de fontes
- **Decisão**: `fontes.py` declara `CONJUNTOS` (nome, modelo do identificador preenchido pelo perfil e id no catálogo), `CONFERENCIAS` (dado, conjunto que permite a conferência, texto do resultado e texto curto para o resumo), `MAPA_FONTES` (chave → conjuntos, conferências, dados sem outra fonte e cálculo do relatório) e o mapa das abas (nomes exatos, nomes do caminho sem EVT e prefixos). As chaves são as das figuras, `tab_*` e `bloco_*`. A legenda cita os conjuntos carregados; a linha DICIONARIOS da aba FONTES cita os conjuntos do tipo e da cobertura da usina, carregados ou não (`Entrada.todos`), porque os dicionários de todos são obtidos (na hidrelétrica com EVT, os mesmos dez conjuntos); a data de obtenção é a `obtencao_mais_recente` de `datas_obtencao.csv`, que as Análises levam em `res.datas_obtencao`; os resultados das conferências são os que a Conferência gravou e que chegam em `ResultadosAnalise`, inclusive a contagem de meses reproduzidos da TEIFa e da TEIP (`ons["recalculo_resumo"]`).
- **Motivo**: PDF, Markdown e planilha com a mesma origem (FR-023 a FR-028); os prefixos fixos ("Fonte dos dados:", "Calculado neste relatório a partir de:") permitem contar as legendas nos testes; as datas vêm da Coleta da usina, e não dos manifestos compartilhados de `data/raw/`, que mudam com a coleta de outras usinas.
- **Alternativas rejeitadas**: texto de fonte em cada seção (repetição e resultados fixos); campo de fonte em cada `linhas_tabela_*` (mistura conteúdo com rastreabilidade).

### D4 — PDF em reportlab
- **Decisão**: A4 paisagem, margens de 36 pt (laterais), 50 pt (superior) e 42 pt (inferior); fontes TrueType Arial (`%WINDIR%\Fonts`) ou DejaVu Sans (distribuída com o matplotlib), com Helvetica e aviso no log se nenhuma existir; canvas de duas passagens (`_canvas_numerado`) para o cabeçalho a partir da página 2 e "Página X de Y"; título, assunto e autor gerados de `usina.nome` e do período. O sumário é um `TableOfContents` em duas colunas (`_SumarioDuasColunas`), alimentado por `afterFlowable` e resolvido por `multiBuild`; a capa termina com `PageBreak`.
- **Motivo**: ≤, ≥ e − exigem fonte TrueType; a página real de cada seção exige duas passagens (FR-011, FR-014, FR-015).

### D5 — Paginação
- **Decisão**: figura e legendas num `KeepTogether`, com altura máxima de 285 pt (`ALTURA_MAXIMA_FIGURA`), exceto as `FIGURAS_PADRONIZADAS` e as `FIGURAS_PADRONIZADAS_COMUM`, desenhadas na largura útil; tabela de até 12 linhas inteira (`LINHAS_TABELA_INTEIRA`); a mais longa começa na página corrente se couberem o subtítulo e 6 linhas (`LINHAS_MINIMAS_NA_PAGINA`, por `CondPageBreak`) e repete o cabeçalho (`repeatRows=1`); título e constatações sempre juntos e, até 150 pt (`ALTURA_ABERTURA_CURTA`), também com o primeiro bloco; subseção junto da figura seguinte ou com espaço para o início da tabela; conclusão inteira num `KeepTogether`. Com o cadastro, os três blocos da capa ocupam 26 %, 38 % e 36 % da largura (`BLOCOS_CAPA_TRES`).
- **Motivo**: sem meia página em branco, capa numa página e conclusão numa página (FR-014, FR-016, FR-031).

### D6 — Figuras em seaborn, com tema único
- **Decisão**: cada `_grafico_*` desenha as marcas com seaborn dentro de `_tema_graficos`, que aplica `sns.set_theme(style="ticks", palette=PALETA_CATEGORICA, rc=_estilo_graficos())` num `plt.rc_context` e restaura o estado ao sair: `lineplot` (01, 06 e 08), `histplot` com `weights` e `multiple="stack"` (02, 05 e 07), `heatmap` (03) e `barplot` com `hue` (04). Linhas de referência, faixas e anotações vão nos mesmos eixos. O seaborn empilha da última categoria (base) para a primeira (topo), por isso o `hue_order` das barras empilhadas é invertido. Fonte Arial (ou DejaVu Sans) de 9 pt, título à esquerda, grade leve, legenda abaixo dos eixos e rótulos das referências à direita, fora da área dos dados; números no padrão brasileiro e anos parciais com "*" e a nota "* ano parcial". As figuras do caminho sem EVT (`figuras_comum.py`) e da carteira (`carteira_figuras.py`) usam o mesmo tema; cada série leva o nível no rótulo quando não é da usina, e níveis diferentes nunca são somados na mesma barra ou linha.
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

  No caminho sem EVT e na carteira (`figuras_comum.py` e `carteira_figuras.py`), também validadas com o mesmo validador, com o contraste abaixo de 3:1 de algumas cores compensado pela legenda e pela tabela de cada figura:

  | Grandeza | Constante | Cores |
  |---|---|---|
  | série do conjunto, ao lado da azul da usina | `COR_CONJUNTO` | azul escuro `#184f95` |
  | motivos de despacho, cada um na sua posição; os demais motivos juntos | `CORES_MOTIVOS` | `#2a78d6`, `#eb6834`, `#1baf7a`, `#eda100`, `#e87ba4`, `#008300`; demais em `COR_CONTEXTO` |
  | CVU de cada unidade de planejamento | `CORES_UNIDADES` | `#2a78d6`, `#1baf7a`, `#eda100`, `#e87ba4` |
  | razões da restrição (REL, CNF, ENE); sem razão publicada | `CORES_RAZOES` | `#2a78d6`, `#eb6834`, `#1baf7a`; `COR_CONTEXTO` |
  | trechos de composição do conjunto; do sexto em diante, "Demais composições" | `CORES_TRECHOS` | `#2a78d6`, `#eb6834`, `#1baf7a`, `#eda100`, `#e87ba4`; `COR_CONTEXTO` |
  | listas da conclusão e séries do panorama, na carteira | `ORDEM_CATEGORICA` | `#2a78d6`, `#eb6834`, `#1baf7a`, `#eda100`, `#e87ba4`, `#008300`, `#6250d6` |

- **Motivo**: a mesma cor para a mesma grandeza em todas as figuras e leitura por quem tem deficiência de visão de cores (constituição, VII). O amarelo tem contraste abaixo de 3:1, compensado por rótulo direto e tabela; o violeta é o único que passa em todos os pares com a turbinada e a vertida, linhas que se cruzam; o passo claro da rampa das faixas tem contraste de 2,48:1. Nas categorias, a cor segue a categoria, nunca a posição na figura.
- **Alternativas rejeitadas**: magenta para a afluência, reprovado contra o laranja da vertida (ΔE 12,9).

### D8 — Tamanho e resolução das figuras
- **Decisão**: 300 DPI (`DEFAULT_PLOT_DPI`). As figuras 01, 02, 05 e 06 têm 11 × 4,3 polegadas (`TAMANHO_FIGURA_PADRONIZADA`, 3300 × 1290 px) e, no PDF, a largura útil (cerca de 760 × 297 pt); a 03 tem 11 × 4,4 e é desenhada com 710 × 284 pt; a 04, a 07 e a 08 têm 11 × 4,6 e ficam limitadas a 285 pt de altura. No caminho sem EVT, todas têm 11 × 4,3 polegadas; as figuras 01 a 05 (`FIGURAS_PADRONIZADAS_COMUM`) ocupam a largura útil, e as demais ficam limitadas a 285 pt de altura. Na carteira, em A4 retrato, as figuras têm 7,5 polegadas de largura (`LARGURA_FIGURA_CARTEIRA`) e até 330 pt de altura no PDF; a da ordenação cresce com a quantidade de usinas.
- **Motivo**: 4,3 polegadas é a maior altura com que a seção de EVT mensal (título, constatações, figura e legendas) cabe numa página (FR-036).

### D9 — Markdown espelho do PDF
- **Decisão**: cabeçalho com título, período e "Gerado em"; blocos da capa e indicadores em tabelas ("Item | Valor" e "Indicador | Valor | Detalhe"); "## Sumário" com links para as âncoras no padrão do GitHub (`_ancora_md`); seções "## N. Título"; subseções "### Título"; figura no corpo da seção, com `![<título da seção>](figures/<arquivo>.png)`, a legenda descritiva e a legenda de fonte; `*` escapado nas notas das tabelas. UTF-8 sem BOM, com o fim de linha do sistema.
- **Motivo**: as mesmas seções, tabelas e figuras do PDF (FR-017).

### D10 — Planilha e CSV
- **Decisão**: `pd.ExcelWriter` com openpyxl, uma aba por tabela, na ordem montada em `exportar_tabelas` (no caminho sem EVT, `_abas_sem_evt` e `_abas_complementares`); abas das bases complementares só com linhas; FONTES montada por último a partir da lista das demais; cabeçalho congelado (`A2`) e largura de coluna `min(max(len(nome), 12) + 3, 60)`. O CSV é `indicadores_anuais.to_csv(sep=";", index=False, encoding="utf-8")` (no caminho sem EVT, `comum["anuais"]`), com ponto decimal. As colunas das abas são as dos quadros de `ResultadosAnalise`; as auditorias chegam já reduzidas às colunas da FR-038.
- **Motivo**: versão completa dos resultados, com a origem de cada aba (FR-028, FR-038, FR-039).

### D11 — `--data-geracao` e reprodutibilidade
- **Decisão**: `executar_relatorio` calcula a data de geração uma vez, a de `--data-geracao` ou a hora da execução, e a passa ao Markdown, ao PDF, ao resumo executivo e ao `resumo`. Só com `--data-geracao` (`invariante=True`), `rl_config.invariant = 1` vale durante o `multiBuild` do relatório e o `build` do resumo (restaurado num `finally`), o que fixa `CreationDate` e `ModDate` em `D:20000101000000+00'00'` e torna o identificador do arquivo determinístico. PNG (só o metadado "Software" do matplotlib), Markdown e CSV já são determinísticos. A planilha não se reproduz byte a byte (o openpyxl grava a hora nas propriedades do arquivo) e é comparada célula a célula.
- **Motivo**: provar a não regressão (FR-004, FR-005, SC-009) sem leitor de PDF no projeto.
- **Alternativas rejeitadas**: comparar só as páginas e o Markdown (fraco); dependência de leitura de PDF só para teste.

### D12 — Ferramenta `comparar`
- **Decisão**: `src/comum/comparacao.py`, fora do pacote da etapa. Percorre as duas pastas recursivamente; ignora todo arquivo `etapa.json`; compara byte a byte todo arquivo que não é `.xlsx`; compara a planilha aba a aba (mesmas abas na mesma ordem, mesma quantidade de linhas, cada célula), com células numéricas iguais por `math.isclose(rel_tol=1e-12, abs_tol=0)`, NaN igual a NaN e booleanos fora da regra numérica; lista até 20 células por aba, com o total numa linha. Qualquer exceção, inclusive planilha ilegível, vira "Erro na comparação: …" na saída de erro e código 1. Não grava nada.
- **Motivo**: os bytes do XLSX mudam a cada gravação; abaixo de 1e-12 relativo, a diferença é resto de ponto flutuante (por exemplo, número lido de um CSV pelo leitor padrão do pandas) e não muda texto nem figura (FR-040).

### D13 — Entrada única e troca conferida das saídas
- **Decisão**: a etapa lê só `resultados.pkl` e o perfil; as datas de obtenção chegam dentro dos resultados; preenche em memória `res.parametros` e `res.fontes`, sem regravar o pickle. Todas as saídas, inclusive o resumo executivo, são geradas em `reports/<slug>/.gravando/`, conferidas no disco (`_conferir_saidas`) e só então trocadas, uma a uma, com `os.replace` (`_trocar_saidas`), sem `.bak`. Durante a troca, cada anterior fica em `.gravando/.anteriores/`; se a troca falhar, cada uma volta ao lugar, e a que não puder voltar é preservada em `reports/<slug>/.anteriores_<AAAAMMDDTHHMMSS>/`, citada no log. A planilha é fechada antes da troca, porque o Windows não move arquivo aberto. Depois da troca, a figura opcional de uma execução anterior que não foi gerada agora é apagada de `figures/`. O `etapa.json` guarda o SHA-256 de cada arquivo final. A carteira usa as mesmas funções de conferência e de troca.
- **Motivo**: uma falha no meio da geração não deixa relatório misturado nem perde o anterior (FR-003; constituição, Requisito Técnico 3); o relatório é regenerado a partir dos resultados, e as versões aprovadas ficam como relatórios de referência.
- **Alternativas rejeitadas**: gravar direto no lugar (uma falha no PDF deixaria as figuras e a planilha novas ao lado do PDF anterior); cópia `.bak` de cada saída (a constituição dispensa os relatórios de `.bak`).

### D14 — Conclusão na apresentação
- **Decisão**: a seção `conclusao`, sempre presente antes das notas e a mesma nos dois caminhos, mostra `FRASE_ABERTURA_CONCLUSAO` e as listas de `LISTAS_CONCLUSAO` com até `MAXIMO_ITENS_CONCLUSAO` (5) itens, na ordem de `res.conclusao`; sem itens, a frase de `frase_sem_itens` (na hidrelétrica com EVT, `FRASE_CONCLUSAO_VAZIA`). O rótulo "(seção N)" é resolvido na geração (`_rotulo_secoes`): os números das seções de origem presentes, em ordem crescente, juntados por `fmt_lista`. A aba CONCLUSAO (`tabela_conclusao`) traz todos os itens. A nota metodológica da conclusão é `nota_conclusao`, montada com as constantes de `regras.py`, na hidrelétrica com EVT, e `nota_conclusao_catalogo`, gerada do catálogo das regras do tipo, com os limiares e as regras não avaliadas, na usina sem EVT.
- **Motivo**: a numeração depende das seções presentes, que só o relatório conhece (FR-029 a FR-033); a nota da hidrelétrica com EVT não pode mudar.

### D15 — Dois caminhos e seções por tipo numa lista única
- **Decisão**: `Secao` ganha `caminhos` (`evt`, `sem_evt` ou os dois), `tipos`, título fixo, por tipo (mapa tipo → título) ou função dos resultados, e `periodo_minimo_meses`. Continua uma única lista, em ordem fixa; `caminho(res)` escolhe o caminho pela presença das seções comuns nos resultados (`sem_evt`), e `secoes_presentes` devolve só as do caminho e, no caminho sem EVT, as do tipo da usina, numeradas sem lacunas.
  - **Hidrelétrica com EVT**: exatamente as 17 seções da FR-007, na mesma ordem, com os mesmos títulos, as mesmas legendas e os construtores próprios (`_secao_<chave>`).
  - **Usina sem EVT**: as seções da FR-041, com chave própria (sufixo `_comum` ou nome novo), para que o PDF e o Markdown da hidrelétrica com EVT não mudem de código. Cada seção é uma lista de blocos (`comum.Bloco`: `chave_valor`, `tabela`, `figura`, `texto`, `subtitulo`, `notas` ou `sem_linhas`) montada por `comum.blocos_secao` e pelos módulos das seções do tipo; o PDF (`_secao_blocos`) e o Markdown (`_md_blocos`) desenham os mesmos blocos. A legenda de fonte é de cada tabela e figura, pela chave do bloco, e não da seção.
  - **Relatório em duas partes** (FR-048): as seções "A usina no conjunto" e "Operação do conjunto" só existem quando `em_duas_partes(res)`; as seções dos números do conjunto ficam fora do corpo e entram como subseções (`Bloco("subtitulo")`) da parte do conjunto, com o mapa de constatações próprio.
  - A conferência da geração entre fontes não tem seção: os resultados ficam nas legendas e nas abas CONF_*, e as Análises a listam entre as omitidas.
- **Motivo**: FR-007, FR-041; o mesmo relatório padronizado para todos os tipos (constituição, VII) sem mudar a hidrelétrica com EVT.
- **Alternativas rejeitadas**: um relatório por tipo em módulos separados (duplicaria o PDF e o Markdown); numeração própria por tipo (dá no mesmo e é mais difícil de testar).

### D16 — Nível do dado nas legendas, nos números e nas notas
- **Decisão**: todo dado de tabela e de figura do caminho sem EVT leva o nível (`usina`, `conjunto` ou `agregado`) e o identificador, de `res.niveis`. A legenda do dado da usina cita o identificador da usina, como na hidrelétrica com EVT; a de um dado de conjunto ou de agregado cita o identificador dele com o nível escrito (`identificador_com_nivel`: "conjunto de usinas, id ONS CJU_…", "subsistema SE, agregado"). As constatações e os rótulos das figuras dizem "do conjunto <nome>". O parágrafo de granularidade das notas só entra quando algum número não é da usina. Nenhum número de conjunto é dividido entre as usinas. A linha "Fontes" do resumo executivo usa o mesmo identificador com o nível.
- **Motivo**: princípio VIII (FR-024, FR-026); o relatório da hidrelétrica com EVT não muda.
- **Alternativas rejeitadas**: escrever "nível: usina" em todas as legendas (mudaria todas as legendas da São Domingos sem acrescentar informação, porque o identificador já diz o nível).

### D17 — Invariantes do relatório das hidrelétricas com EVT
- **Decisão**: cada item abaixo tem um teste de regressão próprio (`tests/relatorio/test_invariantes_uhe.py`, contra a fotografia `tests/fixtures/invariantes_uhe.json`, tirada com o código de antes da ampliação e refeita só com a aprovação do usuário), além do `comparar --todas`:

  | Invariante | Como se mantém |
  |---|---|
  | Seções, títulos, ordem e numeração | o caminho da hidrelétrica com EVT (D15) |
  | Capa e título | sem linha nova; a modalidade já vem da ficha do cadastro |
  | Legendas | identificador da usina, sem o nível escrito (D16); datas de obtenção e contagem de arquivos lidas da Coleta, iguais às anteriores |
  | Conferências | no relatório e na planilha, as seis da FR-026, sem G1 a G5; a do cadastro sem a modalidade; as não aplicáveis não são lidas pelo relatório |
  | Conclusão | C1 a C11 com a mesma ordem, texto, limiares e listas; nota da conclusão com o texto da FR-033 |
  | Trechos | não calculados nem mostrados |
  | Planilha | as mesmas abas e colunas; DICIONARIOS com os mesmos dez conjuntos; auditorias sem colunas novas |
  | Notas | sem o parágrafo de granularidade |
  | Coleta | os mesmos arquivos, com as mesmas colunas, mais as datas de obtenção e o dicionário da EVT |
  | Markdown | completo, igual ao da fotografia |

- **Motivo**: SC-001, SC-013 e princípio IX. Um teste por invariante aponta a causa de uma diferença antes do `comparar`.
- **Alternativas rejeitadas**: confiar só no `comparar` (mostra que algo mudou, mas não por quê).

### D18 — Seções de térmica
- **Decisão**: `secoes_termica.py` monta as três seções da FR-044 com `res.termica`: os motivos e os totais como publicados, somadas as unidades de planejamento por hora, com a parcela sobre a geração total publicada (os motivos podem se sobrepor); o atendimento ao despacho nas horas com geração programada acima de 1 MW, com o limiar de desvio de `regras.py` (`LIMIAR_DESVIO_DESPACHO_MW`) e os maiores desvios na quantidade das demais listas (`NUMERO_EVENTOS_RELATORIO`); o disponível sem despacho; o CVU × CMO por semana operativa, unidade a unidade, com o CVU ausente, zero ou negativo sem comparação e as semanas com o CVU igual ao CMO, sem julgar o despacho. As figuras 06 a 09 ficam em `figuras_comum.py`, e o indicador da capa, em `comum.py`.
- **Motivo**: FR-044; a térmica piloto despacha pouco e teve três códigos de planejamento, por isso a soma das unidades e o CVU por unidade.
- **Alternativas rejeitadas**: CMO semi-horário (o CVU é semanal, e comparar resoluções diferentes criaria falsos cruzamentos).

### D19 — Seções de eólica e solar
- **Decisão**: `secoes_renovavel.py` monta as três seções da FR-045 com `res.renovavel`: o fator de capacidade publicado, da usina ou do conjunto, e, com série própria, o calculado neste relatório, identificado como tal; a energia cortada só nas semi-horas com a marca de restrição, por ano e por razão; a geração por faixa de recurso, sem as semi-horas com o recurso inválido ou acima do limite físico, contadas. A aderência à programação fica na seção comum de programação (`blocos_programacao`), com os maiores desvios. `referencia_restricao()` diz quando a série de referência é a restrição com detalhe da usina; aí o relatório cita essa base, e a programação do conjunto é comparada com a geração do conjunto, fora da base horária da usina. As figuras 10 a 13 ficam em `figuras_comum.py`, e o indicador da capa, em `comum.py`.
- **Motivo**: FR-045; a série da usina existe só nas restrições, e a geração e o fator de capacidade vêm quase sempre do conjunto.
- **Alternativas rejeitadas**: curva de potência ajustada (seria um modelo, não um dado).

### D20 — Usina em conjunto
- **Decisão**: `secoes_conjunto.py` monta a seção da FR-046 com `res.conjunto`: a geração do conjunto por trecho de composição, a composição, uma linha por usina, com a maior potência em operação nos trechos dela, e a figura 14. A potência somada é identificada como calculada neste relatório e não divide a geração do conjunto. Na usina em conjunto sem série própria, o relatório tem as duas partes da FR-048 (D15): a parte da usina, com o que o ONS publica dela, onde obter a geração dela e o peso dela na potência do conjunto, e a parte do conjunto, antes da conclusão. A disponibilidade e os indicadores oficiais da usina, que o ONS não publica, são omitidos, com o motivo nas notas.
- **Motivo**: FR-046 a FR-048; princípio VIII; o fiscal precisa ver o que é da usina e o que é do conjunto sem confundir os dois.
- **Alternativas rejeitadas**: ratear a geração do conjunto pela potência (viola o princípio VIII).

### D21 — Relatórios de referência reproduzíveis
- **Decisão**:
  - **Onde ficam**: em `relatorios_referencia/<slug>/`, na raiz do projeto, com os arquivos do relatório aprovado (os do `etapa.json` dele, inclusive o resumo executivo), a Coleta congelada (`coleta/`: só os arquivos do `etapa.json` da Coleta e o próprio `etapa.json`, sem `.bak`), a cópia do perfil usado (`perfil.toml`) e o `referencia.json`, com a data de geração fixa, a data da aprovação, o período e o SHA-256 de cada arquivo.
  - **Controle de versões**: o relatório e o perfil entram no git, com uma exceção no `.gitignore` para o PDF; a Coleta congelada fica fora, como `data/`. O `referencia` recusa substituir uma referência com mudanças fora do git, para que a anterior fique no histórico.
  - **`referencia`** (`src/comum/referencias.py`): exige o relatório e a Coleta concluídos no formato atual e a data de geração pedida no `etapa.json` do relatório; grava em `.gravando_<slug>`, confere os SHA-256 (também os de origem, contra os `etapa.json`) e só então troca a anterior, que volta se a troca falhar; sugere o commit no log.
  - **`comparar --todas`** (`src/comum/comparacao.py`): para cada referência, copia a Coleta e o perfil congelados para um espaço isolado (`caminhos.espaco_isolado`, que troca `DATA_DIR`, `RAW_DATA_DIR`, `REPORTS_DIR`, `USINAS_DIR` e a raiz do perfil), refaz as etapas 2 a 5 por `pipeline.executar_etapa`, com um `data/raw/` vazio e a data da referência, e compara com a referência pelas regras do `comparar`, fora `referencia.json`, `perfil.toml` e `coleta/`; avisa quando o perfil atual difere do congelado.
  - **`--coleta`**: refaz também a Coleta com `--sem-portal` e o perfil congelado, noutro espaço isolado, e a compara com a congelada: as séries linha a linha, só nas linhas cujo intervalo (hora, dia, mês ou ano) toca o período da referência; as auditorias só nas colunas numéricas, por arquivo, sem `data_hora_processamento`; `dicionarios.csv`, `datas_obtencao.csv` e `dicionario_evt.json` só como informação; a diferença numa série traz a data de publicação no ONS dos arquivos de origem.
  - **Cópias de segurança**: a `copia-seguranca` da Coleta leva `relatorios_referencia/` inteira e a confere pelos SHA-256.
- **Motivo**: princípio IX (referência junto às cópias de segurança, comparação a cada mudança e referência anterior no controle de versões); os brutos são compartilhados e mudam com a coleta de outras usinas e com republicações do ONS, então só a Coleta congelada reproduz a referência; um perfil corrigido depois mudaria o relatório sem mudança de código.
- **Alternativas rejeitadas**: referências só dentro das cópias de segurança (a anterior sairia na poda e não ficaria no git); refazer a Coleta a cada comparação (depende dos brutos compartilhados); congelar os brutos (vários GB por usina).

### D22 — Relatório de carteira
- **Decisão**:
  - **Comando**: `python -m src carteira [--estado <UF>] [--tipo <tipo>] [--data-geracao ...]` (`src/relatorio/carteira.py`), com pelo menos uma das duas opções.
  - **Entradas, só gravadas**: o catálogo (`ler_catalogo`, `filtrar`) e, de cada usina do recorte, o perfil achado pelo CEG em `usinas/*/perfil.toml`, o `etapa.json` e o `resultados.pkl` das Análises, com `indicadores_carteira`. Nenhuma etapa é refeita.
  - **Situação de cada usina** (`situacao_da_usina`): com resultado, ou o primeiro motivo de `ORDEM_MOTIVOS`; as linhas de conjunto do catálogo não contam como usina.
  - **Contagem e ordenação**: todos os itens de cada lista da conclusão, como a aba CONCLUSAO, e não só os cinco exibidos; ordem por possíveis problemas, pontos de atenção e nome (`chave_ordenacao`), com as usinas sem regra avaliada no fim.
  - **Panorama**: as linhas de `agregados.csv` do estado (e do tipo do ONS correspondente, com `--tipo`), os 12 últimos meses completos do catálogo, selecionados pelo estado e pela modalidade, nunca pelo nome ou pelo id; o grupo sem nenhuma hora com valor fica sem energia, e não zero; os valores Tipo III marcados como previsão. Só com `--estado`, porque os agregados são publicados por área do estado.
  - **Documento**: `Documento` com os blocos na ordem do contrato, de onde saem o Markdown e o PDF (`carteira_pdf.py`, A4 retrato, com os estilos do resumo executivo e tabelas em 8 pt); a legenda de fonte de cada tabela e figura vem de `origens`, a mesma da aba FONTES; as figuras em `carteira_figuras.py`.
  - **Gravação**: a pasta temporária, a conferência e a troca do relatório da usina, sem `.bak`.
  - **Textos**: nenhum termo de parecer, conferido por teste.
- **Motivo**: princípios III, VII e VIII; o fiscal escolhe onde fiscalizar a partir dos resultados de cada usina, sem refazer cálculo e sem nota.
- **Alternativas rejeitadas**: ler os dados tratados de cada usina (refaria cálculos fora das Análises); panorama lido dos brutos pela própria carteira (acessaria dados fora das etapas).

### D23 — Resumo executivo gerado dentro da etapa, depois do PDF do relatório
- **Decisão**: `executar_relatorio` gera o resumo na mesma pasta temporária das demais saídas, depois do PDF do relatório completo, porque o resumo cita o número de páginas dele. O resumo entra na conferência no disco e na troca das saídas. Se o resumo falhar, nenhuma saída nova substitui as anteriores.
- **Motivo**: FR-050 e o caso de borda "relatório gerado de novo": o resumo e o relatório têm sempre a mesma data, o mesmo período e o mesmo `etapa.json`.
- **Alternativa rejeitada**: uma etapa ou um comando próprio (o resumo poderia ficar ao lado de um relatório de outra execução, e o manifesto da etapa deixaria de listar todas as saídas).

### D24 — "Gerar à parte" é executar só a Geração do relatório
- **Decisão**: `python -m src relatorio --usina <slug>` gera o relatório e o resumo a partir dos resultados gravados, sem refazer as etapas 1 a 4. Não há comando que gere só o resumo.
- **Motivo**: um resumo gerado sozinho precisaria conferir se o relatório ao lado veio dos mesmos resultados, com a mesma data. Isso duplicaria a lógica do manifesto para um ganho pequeno: a etapa sozinha já não refaz as anteriores (FR-051).

### D25 — Conclusão igual por construção
- **Decisão**: o bloco de conclusão usa as mesmas funções e frases do relatório completo: `listas_conclusao(res)`, `FRASE_ABERTURA_CONCLUSAO` e `frase_sem_itens(res)`. Os números de seção citados nos itens saem de `secoes_presentes(res)`, os mesmos do relatório.
- **Motivo**: FR-058 e SC-016. Copiar o texto do Markdown do relatório criaria uma dependência de formato; chamar as mesmas funções garante o mesmo texto e o mesmo limite de cinco itens por lista.
- **Verificação**: teste que compara, caractere por caractere, o bloco do resumo em Markdown com a seção de conclusão do relatório em Markdown.

### D26 — Indicadores-chave = indicadores da capa
- **Decisão**: a tabela usa os indicadores da capa do caminho da usina (`conteudo.indicadores_capa` ou `comum.indicadores_capa`), com as colunas Indicador, Valor e Detalhe. A coluna Detalhe já traz a referência e a comparação, com o mesmo texto da capa. A nota da capa não entra; o que ela explica sobre as fontes está em "Sobre os dados".
- **Motivo**: FR-060 e FR-063: mesmos números e mesmo texto, para todos os tipos.

### D27 — Evolução anual = colunas escolhidas da tabela anual do relatório
- **Decisão**: o resumo escolhe colunas da tabela anual do relatório pelo cabeçalho, conforme um mapa declarado por caminho (`COLUNAS_RESUMO_ANUAL`). Os valores são os mesmos textos da tabela, com o "*" dos anos parciais.
  - **Hidrelétrica com EVT**: Ano, Disp. média (% Pinst), Fator de capacidade, Geração / GF, EVT (MWh) e Horas parada c/ EVT; um cabeçalho do mapa ausente na tabela é erro.
  - **Usina sem EVT**: das colunas Ano, Nível, Geração média (MWmed), Energia (MWh), Fator de capacidade, Disp. (% Pinst), Disp. sem despacho (h) e Energia cortada (MWh, % est.), as que a tabela da usina tem, nesta ordem. Regra da escolha: Ano e até cinco colunas, com a disponibilidade, o fator de capacidade e o principal indicador de perda do tipo (horas disponíveis sem despacho nas térmicas, energia cortada nas eólicas e solares).
  - **Nota da tabela**: "* Ano parcial." e a seção de origem no relatório completo (no relatório em duas partes, a da operação do conjunto). As definições das colunas ficam na linha de termos.
- **Motivo**: FR-061 e FR-063. Escolher colunas da tabela pronta evita formatar os números de novo.

### D28 — "Sobre os dados" com fontes e conferências completas, em texto curto
- **Decisão**: o bloco é montado a partir dos resultados, em três parágrafos:
  1. **dados**: cobertura (início, fim, registros e anos parciais; na usina sem EVT, a série de referência com o nível e as horas ausentes) e registros ou horas sinalizados (quantidade e parcela, os mesmos da seção de qualidade);
  2. **conferências e limites**: uma frase curta por conferência feita, gerada pelo mapa de conferências de `fontes.py` com os mesmos números do texto longo (na usina sem EVT, só as que não dependem da EVT); uma frase geral sobre o que os dados abertos não informam (causa das paradas e eventos individuais);
  3. **fontes**: os conjuntos carregados, agrupados por identificador (com o nível) e data de obtenção (`fontes_resumo`).

  Com mais de 250 palavras, é erro.
- **Motivo**: a constituição (VII) aceita um bloco único no lugar das legendas, com as mesmas informações de fonte e de conferência. Na São Domingos, isso dá cerca de 220 palavras, e o resumo cabe em duas páginas (FR-062).
- **Alternativa rejeitada**: citar só "ver as legendas do relatório completo" (não atende a constituição).

### D29 — Linha de termos no cabeçalho, a partir de um glossário declarado
- **Decisão**: um glossário nas regras gerais (`GLOSSARIO_RESUMO`, em `src/comum/regras.py`) explica as siglas e grandezas, com o texto aprovado pelo usuário. O cabeçalho traz só os termos que aparecem no resumo, na ordem da primeira ocorrência; a sigla é reconhecida como palavra, também seguida de algarismos (UG2), e "TEIF" não casa com "TEIFa".
- **Motivo**: FR-066. A conclusão é copiada igual e usa siglas sem explicação; com a linha de termos antes dela, o diretor lê a conclusão já sabendo o que cada sigla significa.

### D30 — Página e tipografia do resumo
- **Decisão**: A4 retrato, com as margens do relatório (laterais de 36 pt, superior de 50 pt e inferior de 42 pt), a mesma fonte (Arial, ou DejaVu Sans sem Arial), as mesmas cores e o mesmo rodapé com a numeração; cabeçalho das páginas "Resumo executivo — <nome> · <início> a <fim>". Texto em 10 pt com entrelinha de 13 pt; tabelas em 9 pt. A conclusão não fica num bloco indivisível, como no relatório, porque isso a empurraria inteira para a segunda página; cada título de lista fica junto do primeiro item. `_registrar_fontes`, `_canvas_numerado`, as margens e as cores vêm de `pdf.py`, importados sem alterar o PDF do relatório.
- **Motivo**: FR-053; o protótipo da São Domingos, com esses corpos, ocupou 81 % das duas páginas.

### D31 — Regra das duas páginas e reprodutibilidade do resumo
- **Decisão**:
  1. gerar o PDF e contar as páginas (`paginas_do_pdf`);
  2. com mais de duas páginas, gerar de novo sem a evolução anual, com a frase de remissão à seção, e registrar a omissão no log;
  3. ainda com mais de duas, levantar erro: a etapa termina com código 1, e nenhuma saída é trocada.

  O Markdown é gerado depois dessa decisão, para ter o mesmo conteúdo do PDF. Com `--data-geracao`, o PDF do resumo usa o modo invariante, como o do relatório, e sai igual byte a byte. Acima de 1.000 palavras fora das tabelas, um aviso no log.
- **Motivo**: FR-055 e o princípio IX: o `comparar` confere o PDF byte a byte.

### D32 — Verificações automáticas do resumo
- **Decisão**: `tests/relatorio/test_resumo.py` e os testes das usinas fictícias conferem:

  | Verificação | Requisito |
  |---|---|
  | Conclusão do resumo igual à seção de conclusão do relatório, em Markdown, com as regras do sintético, com todas as regras e vazia | FR-058, SC-016 |
  | Todo número do resumo presente no Markdown do relatório; única exceção, o número de páginas do relatório no cabeçalho; também nas usinas fictícias de cada tipo | FR-063, SC-017 |
  | No máximo duas páginas, nenhuma imagem no PDF e no máximo duas tabelas no Markdown | FR-053, FR-054, SC-015 |
  | No máximo 1.000 palavras fora das tabelas e 250 em "Sobre os dados" | FR-062, SC-018 |
  | Ordem dos blocos e o mesmo conteúdo no PDF e no Markdown (os blocos emitidos pelo gerador do PDF iguais aos títulos do Markdown) | FR-052, FR-056 |
  | Conclusão longa: a evolução anual é omitida; conclusão ainda mais longa: erro e nada gravado | FR-055 |
  | Nenhum termo de parecer fora da conclusão; nenhuma constante de usina no código (`test_literais.py`) | FR-064 |
  | Usinas sem EVT: sem "EVT" nem "energia vertida"; números do conjunto como do conjunto; colunas do caminho | FR-061, FR-065, FR-068 |

- **Motivo**: SC-015 a SC-017 por verificação automática, sem leitor de PDF no projeto.

### D33 — Resumo na referência
- **Decisão**: o resumo entra na referência quando o usuário o aprova e o `referencia` é executado de novo: o `referencia.json` lista os arquivos a partir do `etapa.json` do relatório, que passou a ter os dois do resumo, sem mudança de formato. O `comparar` confere o PDF e o Markdown do resumo byte a byte, como os do relatório, sem mudança de código. O `referencia` recusa substituir uma referência não commitada, por isso a anterior precisa estar commitada antes. A fotografia dos invariantes da hidrelétrica com EVT não inclui a lista de arquivos do relatório e não muda.
- **Motivo**: FR-069 e FR-070; princípio IX.

### D34 — Sem dependência nova e sem mudança de formato da etapa
- **Decisão**: o resumo usa o `reportlab`, que já está em `requirements.txt`. O `VERSAO_FORMATO` do relatório continua 1: nenhuma etapa lê o manifesto do relatório, e o `referencia` só lê a lista de arquivos, que ganhou dois itens. O `resumo` do `etapa.json` ganhou `resumo_executivo`, com as páginas, a presença da evolução anual e as palavras fora das tabelas.
- **Motivo**: constituição, Requisito Técnico 1; nenhuma etapa precisa refazer nada por causa do resumo.

## Desvios registrados na implementação

| Data | O que mudou | Aprovação |
|---|---|---|
| 19/10/2026 | O caminho sem EVT ganhou os módulos `src/relatorio/comum.py` (capa, tabelas, legendas, notas e blocos das seções) e `src/relatorio/figuras_comum.py` (figuras em seaborn), que o plano não previa; o plano previa mudar `conteudo.py`, `figuras.py`, `markdown.py`, `pdf.py` e `planilha.py`. Assim o código da hidrelétrica com EVT não muda. As Análises passaram ao formato 3 (o 2 já tinha sido usado pelas datas de obtenção da Coleta). | usuário, na conferência do código contra os requisitos ("aprovado, siga") |
| 20/10/2026 | As figuras e o indicador da capa das térmicas ficaram em `figuras_comum.py` e `comum.py`, e não em `figuras.py` e `conteudo.py`; o CVU zero passou a ser sinalizado e fica sem comparação. | usuário, com o relatório da William Arjona |
| 21/10/2026 | As figuras e os indicadores da capa das eólicas e solares, também em `figuras_comum.py` e `comum.py`; a estimativa ausente e o limite físico do recurso, decididos pelo usuário. A restrição da EOL fictícia começa em 15/01/2024, dentro do período sintético, e não em 10/2021. | usuário, com os relatórios da Seriemas 1 e da Praia Formosa |
| 22/10/2026 | As figuras do conjunto e das vazões, em `figuras_comum.py`; os blocos e as notas, em `comum.py` e `secoes_conjunto.py` (o plano citava `figuras.py` e `conteudo.py`); o relatório em duas partes, o bloco `subtitulo` e as abas CONJ_* e HID_*; a linha "Fontes" do resumo com o nível. A CGH fictícia tem geração própria, por isso não tem a seção do conjunto (o caso da CGH em conjunto é o da PCH); a Bandeirante tem oito códigos de programação, e não quatro. | usuário, com o relatório da Bandeirante |
| 23/10/2026 | A carteira ganhou os módulos `carteira_pdf.py` e `carteira_figuras.py`, não previstos; os testes da carteira foram escritos depois do código, na mesma sessão. | registrado na convergência, depois da aprovação da carteira de MS pelo usuário |

## Complexity Tracking

Sem desvios da constituição. Os pontos abaixo trazem complexidade e estão justificados:

| Ponto | Por que é necessário | Alternativa mais simples rejeitada porque |
|---|---|---|
| Dois caminhos na mesma etapa, com módulos próprios para o caminho sem EVT | o relatório da hidrelétrica com EVT não pode mudar (princípio IX), e os outros tipos não têm a EVT | adaptar os construtores da hidrelétrica com EVT mudaria o código e arriscaria o relatório aprovado |
| Referência com a Coleta e o perfil congelados, comparada num espaço isolado | os brutos são compartilhados e mudam com outras usinas e com republicações do ONS; um perfil corrigido depois mudaria o relatório sem mudança de código | refazer a Coleta a cada comparação não reproduz a referência; congelar os brutos ocuparia vários GB por usina |
| `relatorios_referencia/` no git e copiada para as cópias de segurança | o princípio IX pede a referência junto às cópias e a anterior no controle de versões | só dentro das cópias, a anterior sairia na poda e não ficaria no git |
