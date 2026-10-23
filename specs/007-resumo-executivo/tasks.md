---

description: "Tarefas da spec 007: resumo executivo do relatório de desempenho"
---

# Tasks: Resumo Executivo do Relatório de Desempenho

**Input**: documentos de `specs/007-resumo-executivo/`: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/resumo-executivo.md](contracts/resumo-executivo.md) e [quickstart.md](quickstart.md)

**Tests**: incluídos. A constituição (Qualidade 1) exige testes automatizados sem rede em cada etapa, e o plano define as verificações da decisão R11. Os testes de cada história são escritos antes do código e devem falhar até a implementação.

**Organization**: tarefas agrupadas por história da spec. Em cada fase, os testes vêm antes do código.

**Regras deste arquivo**:
- Nenhum código antes da fase 1 concluída: portão da fase A da 006 e aprovações do usuário (decisão R13).
- Toda evidência (comando, data, resultado) vai para "Registro de execução", no fim deste arquivo.
- "decisão Rn" = decisão do [research.md](research.md) desta spec. "regra Rn" = regra de validação física R1 a R9 do Tratamento. "Cn" = regra da conclusão.
- Os nomes de funções citados são os de hoje. Se a fase A da 006 os renomear, vale o nome novo, registrado na T005.
- Rodar a suíte como `python -m pytest tests -q -p no:cacheprovider`, nunca `pytest` sozinho, que coleta as pastas `_backup_*`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história da spec (US1, US2, US3)

---

## Phase 1: Setup (pré-condições e aprovações)

**Purpose**: garantir o ponto de partida e as aprovações antes do código.

- [X] T001 Conferir que o portão do fim da fase A da 006 (T074 em `specs/006-ampliacao-tipos-de-geracao/tasks.md`) está aprovado e que `python -m src comparar --todas --coleta` termina com código 0. Sem isso, parar e avisar o usuário (decisão R13). Registrar em `specs/007-resumo-executivo/tasks.md`.
- [X] T002 Conferir com `git status --short relatorios_referencia/sao_domingos` que a referência da São Domingos está commitada, sem mudança pendente. O `referencia` da T032 recusa substituir uma referência não commitada (decisão R12). Com mudança pendente, pedir o commit ao usuário. Registrar.
- [X] T003 Criar a cópia de segurança com `python -m src copia-seguranca --motivo antes_resumo_executivo` e conferir que ficam no máximo duas cópias, a nova com `relatorios_referencia/` (RT5). Registrar.
- [X] T004 Levar ao usuário e registrar a aprovação de:
  - ajuste A1 ([plan.md](plan.md), "Ajustes na spec"): na FR-002 e no cenário 4 da US1 de `specs/007-resumo-executivo/spec.md`, "pedir só o resumo" passa a "executar só a Geração do relatório";
  - ajuste A2: na FR-013, "no máximo quatro linhas" passa a "no máximo 250 palavras";
  - texto do `GLOSSARIO_RESUMO` ([data-model.md](data-model.md), 2.1).

  Aplicar os ajustes aprovados na spec e registrar a data em "Decisões do usuário". Se A1 ou A2 for recusado, parar e refazer as tarefas afetadas (T008, T014 a T018) antes do código.
- [X] T005 Ler, no código depois da fase A da 006, as funções que o resumo reaproveita e registrar o nome e a assinatura atuais de cada uma (ou "sem mudança"):
  - `listas_conclusao`, `indicadores_capa`, `linhas_tabela_anual`, `pares_identificacao`, `pares_identificacao_cadastro` e `secoes_presentes`, em `src/relatorio/conteudo.py` e `src/relatorio/estrutura.py`;
  - `FRASE_ABERTURA_CONCLUSAO` e `FRASE_CONCLUSAO_VAZIA`, em `src/analises/conclusao.py`;
  - o título da capa do PDF, em `src/relatorio/pdf.py`, `_capa`;
  - o critério de caminho (com ou sem EVT) da decisão R14 da 006.
- [X] T006 [P] Retirar o comentário "Sync Impact Report" do topo de `.specify/memory/constitution.md`, se ainda estiver lá, antes do commit da constituição 3.1.0.

**Checkpoint**: aprovações registradas; código liberado.

---

## Phase 2: Foundational (pré-requisitos de todas as histórias)

**Purpose**: caminhos, regras gerais e textos de fonte que o resumo usa.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T007 [P] Em `src/comum/caminhos.py`, acrescentar a `ARQUIVOS_RELATORIO` as chaves `"resumo_pdf": "resumo_executivo.pdf"` e `"resumo_md": "resumo_executivo.md"` (data-model 4).
- [X] T008 [P] Em `src/comum/regras.py`, numa seção "Resumo executivo", acrescentar as constantes com um comentário de uma linha cada (data-model 2.3):
  - `RESUMO_MAXIMO_PAGINAS: int = 2`;
  - `RESUMO_CORPO_PT: float = 10.0`;
  - `RESUMO_TABELA_PT: float = 9.0`;
  - `RESUMO_MAXIMO_PALAVRAS: int = 1000`, fora das tabelas;
  - `RESUMO_MAXIMO_PALAVRAS_DADOS: int = 250`, ajuste A2;
  - `GLOSSARIO_RESUMO: Dict[str, str]`, com o texto aprovado na T004, nas chaves EVT, DISPF, TEIFa, TEIP, UG, GF, Pinst e MWmed.
- [X] T009 [P] Em `src/relatorio/fontes.py`, a forma curta das conferências (data-model 3):
  - a dataclass `Conferencia` ganha o campo `texto_curto: Callable[[Any], str]`;
  - uma função curta para cada uma das seis conferências de `CONFERENCIAS`, com os mesmos resultados e a mesma formatação de números da função longa. Exemplos: "geração: 100,0% das horas coincidentes com a série oficial"; "TEIFa e TEIP: 21 de 21 meses reproduzidos"; "DISPF e horas por estado operativo: 4 divergências (meses-unidade)"; "cadastro: sem divergência";
  - `texto_conferencia_curto(res, cid)`, com o mesmo aviso de "não feita nesta execução" de `texto_conferencia`;
  - `fontes_resumo(res) -> List[str]`: os conjuntos carregados (`_carregados(res)`), agrupados por identificador da usina (`identificador_da_usina`) e data de obtenção, um texto por grupo, como "Energia Vertida Turbinável e Dados hidrológicos horários (cod_usina 153), obtidos em 30/09/2026". O exemplo é da São Domingos; nada fixo no código.
  - Acrescentar os nomes novos a `__all__`. As legendas atuais não mudam.
- [X] T010 Garantir que o título da capa do PDF do relatório venha de uma função só. Se a fase A da 006 já criou essa função (T005), usá-la. Senão, criar `titulo_capa_relatorio(res) -> str` em `src/relatorio/conteudo.py`, com o texto de hoje ("<nome> — Análise do desempenho operacional"), e usá-la em `src/relatorio/pdf.py`, `_capa`. A saída deve continuar igual byte a byte (conferido na T013).
- [X] T011 [P] Em `tests/relatorio/test_fontes.py`, testes da T009:
  - cada número do texto curto de cada conferência aparece no texto longo da mesma conferência, com os resultados sintéticos de `tests/relatorio/apoio.py` (`analisar_com_bases`);
  - conferência sem base carregada: o texto curto diz "não feita";
  - `fontes_resumo` cita cada conjunto carregado uma vez, com a data de obtenção.
- [X] T012 Rodar a suíte em `tests/`; corrigir até passar.
- [X] T013 Conferir que nada mudou no relatório de `relatorios_referencia/sao_domingos/`: `python -m src comparar --todas --coleta` com código 0 (as fundações não criam arquivo novo). Registrar.

**Checkpoint**: fundações prontas, relatório igual à referência.

---

## Phase 3: User Story 1 - Ler em duas páginas o que o relatório completo encontrou (Priority: P1) 🎯 MVP

**Goal**: a etapa 5 gera o resumo em PDF e em Markdown, com cabeçalho, conclusão, indicadores-chave, evolução anual e "Sobre os dados", em no máximo duas páginas.

**Independent Test**: gerar o relatório da usina fictícia e o da São Domingos e conferir: no máximo duas páginas A4 sem figura; blocos na ordem; cada número igual ao do relatório completo; a seção de origem de cada tabela.

### Tests for User Story 1 ⚠️

> Escrever primeiro e confirmar que falham por falta do resumo.

- [X] T014 [P] [US1] Criar `tests/relatorio/test_resumo.py`. Usar os resultados de `analisar_com_bases(df_sintetico, ...)` de `tests/relatorio/apoio.py` e, para "todas as regras", `_tudo(df_base)` de `tests/analises/test_conclusao.py`. Gerar o relatório completo e o resumo numa pasta temporária, com a data fixa `datetime(2026, 10, 7, 8, 53)`. Testes:
  - os dois arquivos existem, o PDF começa com `%PDF-`, e o resumo tem o mesmo "Gerado em" do relatório;
  - os títulos `##` do Markdown estão na ordem: Conclusão, Indicadores-chave, Evolução anual, Sobre os dados, depois do `#` do cabeçalho;
  - as linhas da tabela de indicadores-chave são iguais às de `indicadores_capa(res)`;
  - a evolução anual tem só os cabeçalhos de `COLUNAS_RESUMO_ANUAL["evt"]`, com os mesmos textos das colunas correspondentes de `linhas_tabela_anual(res)`, linha a linha, e a nota com "* Ano parcial." e a seção de origem;
  - todo número do resumo, encontrado por expressão regular de números no padrão brasileiro, aparece no Markdown do relatório completo; única exceção, o número de páginas do relatório no cabeçalho (FR-014);
  - `paginas_do_pdf` do resumo ≤ `RESUMO_MAXIMO_PAGINAS`; o PDF não contém `/Subtype /Image`; o Markdown tem no máximo duas tabelas (blocos de linhas iniciadas por `|`);
  - palavras fora das tabelas ≤ `RESUMO_MAXIMO_PALAVRAS`; palavras de "Sobre os dados" ≤ `RESUMO_MAXIMO_PALAVRAS_DADOS`;
  - "Sobre os dados" traz o texto curto de cada conferência feita e os textos de `fontes_resumo(res)`;
  - a linha de termos tem só as siglas do `GLOSSARIO_RESUMO` que aparecem no resumo, na ordem da primeira ocorrência;
  - duas gerações com a mesma data fixa produzem PDFs iguais byte a byte (decisão R10);
  - os blocos emitidos pelo gerador do PDF (`blocos_emitidos`) são os mesmos, na mesma ordem, que os títulos do Markdown (FR-003).
- [X] T015 [P] [US1] Em `tests/relatorio/test_resumo.py`, a regra das duas páginas (FR-006, decisão R10), com `monkeypatch` em `listas_conclusao`:
  - conclusão com cinco itens por lista e textos longos que passam de duas páginas só com a evolução anual: o resumo sai sem a evolução anual, com a frase "A evolução anual está na seção <n> do relatório completo.", e `info["evolucao_anual"]` é `False`;
  - conclusão que passa de duas páginas mesmo sem a evolução anual: `executar_relatorio` termina com erro, `reports/<slug>/` fica como estava (nenhum `resumo_executivo.*` novo, relatório anterior intacto) e a pasta temporária `.gravando` some.
- [X] T016 [P] [US1] Em `tests/integracao/test_usina_ficticia.py`:
  - `resumo_executivo.pdf` e `resumo_executivo.md` entre as saídas do relatório;
  - o `etapa.json` do relatório lista os dois arquivos e traz `resumo.resumo_executivo` com `paginas`, `evolucao_anual` e `palavras`;
  - nenhum literal da São Domingos no resumo da usina fictícia.

### Implementation for User Story 1

- [X] T017 [US1] Criar `src/relatorio/resumo.py`, com docstring do módulo citando a spec da Geração do relatório (resumo executivo) e o logger `relatorio`:
  - a dataclass `ResumoExecutivo`, com os campos do data-model 1: `titulo`, `subtitulo`, `identificacao`, `referencia_relatorio`, `termos`, `conclusao`, `aviso_secoes`, `indicadores`, `evolucao_anual`, `remissao_anual` e `sobre_os_dados`;
  - `COLUNAS_RESUMO_ANUAL: Dict[str, List[str]] = {"evt": ["Ano", "Disp. média (% Pinst)", "Fator de capacidade", "Geração / GF", "EVT (MWh)", "Horas parada c/ EVT"]}`. Um cabeçalho ausente na tabela levanta `KeyError` com o nome do cabeçalho;
  - `montar_resumo(res, paginas_relatorio: int, data_geracao: datetime, com_evolucao_anual: bool = True) -> ResumoExecutivo`, com:
    - **cabeçalho** (data-model 1.1): título "<nome> — resumo executivo"; subtítulo com o período e os registros de `res.cobertura` e o "Gerado em" no formato da capa; linha de tipo, UF, modalidade e potência; linha "Agente" igual à de `pares_identificacao(res)`; linha "Resume o relatório completo "<título da capa (T010)>", de <n> páginas, gerado na mesma data."; linha sem dado é omitida;
    - **conclusão**: `FRASE_ABERTURA_CONCLUSAO` e `listas_conclusao(res)`, sem alteração; `aviso_secoes` = "As seções e as notas metodológicas citadas são as do relatório completo.";
    - **indicadores**: cabeçalho ["Indicador", "Valor", "Detalhe"] e as linhas de `indicadores_capa(res)[0]`;
    - **evolução anual**: as colunas de `COLUNAS_RESUMO_ANUAL` tiradas de `linhas_tabela_anual(res)` pelo cabeçalho, com a nota "* Ano parcial. Colunas e definições na seção <n> do relatório completo.", em que n é o número da seção `indicadores_anuais` em `secoes_presentes(res)`. Com `com_evolucao_anual=False`, a tabela fica vazia e `remissao_anual` recebe a frase da T015;
    - **"Sobre os dados"**, em três parágrafos (data-model 1.2): (1) cobertura com início, fim, registros e anos parciais (`ano_parcial` de `res.indicadores_anuais`) e registros sinalizados com `globais["horas_com_anomalia"]` e a mesma parcela e formatação da constatação de qualidade (`fmt_pct(..., 2)`); (2) "Conferências: " com os textos de `texto_conferencia_curto` das conferências cuja base foi carregada, mais a frase geral "Os dados abertos do ONS não informam a causa das paradas nem os eventos individuais de desligamento."; (3) "Fontes: " com `fontes_resumo(res)`. Com mais de `RESUMO_MAXIMO_PALAVRAS_DADOS` palavras, levantar `ValueError`;
    - **termos**: as siglas de `GLOSSARIO_RESUMO` presentes no texto montado, inclusive na conclusão e nos cabeçalhos das tabelas, na ordem da primeira ocorrência.
  - Nenhum número, nome ou frase própria de usina fixo no código (`tests/comum/test_literais.py`).
- [X] T018 [US1] Em `src/relatorio/resumo.py`, `gerar_resumo_md(resumo: ResumoExecutivo, caminho: Path) -> Path`, no formato do [contrato](contracts/resumo-executivo.md), seção 3:
  - `#` título; subtítulo, identificação, referência e "Termos: …";
  - `## Conclusão`, a linha `aviso_secoes` e o bloco da conclusão com as mesmas linhas que `src/relatorio/markdown.py` escreve na seção de conclusão (frase, linha em branco, `### <lista>`, linha em branco, `- <item>`);
  - `## Indicadores-chave` com a tabela e "Seção de origem: capa do relatório completo.";
  - `## Evolução anual` com a tabela e a nota (ou a frase de remissão);
  - `## Sobre os dados` com os três parágrafos.
  - Tabelas no mesmo formato de `_tabela_md` do relatório. Gravar em UTF-8.
- [X] T019 [US1] Criar `src/relatorio/resumo_pdf.py`, com `gerar_resumo_pdf(resumo: ResumoExecutivo, caminho: Path, invariante: bool) -> List[str]`, que devolve os blocos emitidos, na ordem:
  - A4 retrato (`reportlab.lib.pagesizes.A4`), margens `MARGEM_LATERAL`, `MARGEM_SUPERIOR` e `MARGEM_INFERIOR` importadas de `src/relatorio/pdf.py`;
  - fonte de `_registrar_fontes()`; cores `TINTA`, `TINTA_SECUNDARIA`, `AZUL_TITULO`, `LINHA`, `FUNDO_CABECALHO` e `FUNDO_ZEBRA` de `pdf.py`;
  - texto em `RESUMO_CORPO_PT` com entrelinha de 13 pt; tabelas em `RESUMO_TABELA_PT`;
  - rodapé com a numeração por `_canvas_numerado(cabecalho, fonte)`, com o cabeçalho "Resumo executivo — <nome> · <dd/mm/aaaa> a <dd/mm/aaaa>";
  - itens da conclusão com "• ", como no relatório; título de cada lista com `keepWithNext`, sem bloco indivisível na conclusão (decisão R9);
  - `rl_config.invariant = 1` durante o `build` quando `invariante`, restaurado depois, como em `PDFReportGenerator.build_pdf`;
  - metadados do PDF: título "<nome> — resumo executivo".

  O `pdf.py` do relatório não muda.
- [X] T020 [US1] Em `src/relatorio/resumo.py`, a função de orquestração da decisão R10. `gerar_resumo(res, caminho_pdf: Path, caminho_md: Path, data_geracao: datetime, invariante: bool, paginas_relatorio: int) -> Tuple[Path, Path, Dict[str, Any]]`:
  1. montar e gerar o PDF; contar as páginas com `paginas_do_pdf` (de `src/relatorio/etapa.py`; mover a função para `src/relatorio/resumo_pdf.py` ou para um módulo comum, se a importação ficar circular, mantendo o nome importável de `etapa.py`);
  2. com mais de `RESUMO_MAXIMO_PAGINAS` páginas, montar com `com_evolucao_anual=False`, gerar de novo e registrar no log a omissão;
  3. ainda com mais páginas, levantar `RuntimeError("resumo executivo com <n> páginas, acima do máximo de 2, mesmo sem a evolução anual")`;
  4. gerar o Markdown do mesmo `ResumoExecutivo` final;
  5. devolver `info = {"paginas": n, "evolucao_anual": bool, "palavras": <palavras fora das tabelas>}`.
- [X] T021 [US1] Em `src/relatorio/etapa.py`, `executar_relatorio`:
  - depois de `pdf = gerador.build_pdf()`, chamar `gerar_resumo(res, temporaria / arq["resumo_pdf"], temporaria / arq["resumo_md"], gerado_em, data_geracao is not None, paginas_do_pdf(pdf))`;
  - incluir os dois arquivos em `novos`, antes de `_conferir_saidas`, para entrarem na conferência e na troca atômica;
  - acrescentar `"resumo_executivo": info` ao `resumo` do `etapa.json`;
  - atualizar a docstring do módulo (saídas da etapa). Um erro no resumo segue o fluxo atual: a pasta temporária é apagada, as saídas anteriores ficam, e a etapa termina com código 1.
- [X] T022 [US1] Rodar `tests/relatorio/test_resumo.py`, `tests/relatorio/test_fontes.py` e `tests/integracao/test_usina_ficticia.py`; corrigir até passar. Depois, a suíte inteira.

**Checkpoint**: o resumo sai junto com o relatório, em até duas páginas, com números iguais aos do relatório.

---

## Phase 4: User Story 2 - Conclusão igual à do relatório completo (Priority: P1)

**Goal**: garantir que o bloco de conclusão é a conclusão do relatório, caractere por caractere, inclusive nos casos de lista vazia e de conclusão vazia.

**Independent Test**: comparar o bloco de conclusão do resumo com a seção de conclusão do relatório completo da mesma execução.

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Em `tests/relatorio/test_resumo.py`:
  - com `_tudo(df_base)` (todas as regras) e com os resultados de `analisar_com_bases(df_sintetico)`: o texto entre `## Conclusão` + `aviso_secoes` e `## Indicadores-chave` no Markdown do resumo é igual, caractere por caractere, ao texto da seção `## <n>. Conclusão` do Markdown do relatório completo, sem o título;
  - a linha logo abaixo de `## Conclusão` é `aviso_secoes`;
  - lista sem itens no relatório não aparece no resumo;
  - com `_neutro(df_base)` (nenhuma regra dispara): o bloco traz só `aviso_secoes` e `FRASE_CONCLUSAO_VAZIA`;
  - os itens da conclusão emitidos pelo PDF do resumo são iguais aos de `listas_conclusao(res)`.
- [X] T024 [P] [US2] Em `tests/relatorio/test_resumo.py`: o resumo sem o bloco de conclusão não contém, sem distinguir maiúsculas, "satisfatório", "insatisfatório", "cumpre" nem "descumpre" (constituição II).

### Implementation for User Story 2

- [X] T025 [US2] Em `src/relatorio/resumo.py` e `src/relatorio/resumo_pdf.py`, completar o que os testes T023 e T024 apontarem:
  - conclusão vazia com `FRASE_CONCLUSAO_VAZIA` e sem títulos de lista;
  - formatação do bloco no Markdown igual à de `src/relatorio/markdown.py`, sem escapar nem alterar o texto dos itens;
  - no PDF, o mesmo texto com `escape` só para o XML do `reportlab`, como em `PDFReportGenerator._secao_conclusao`.
- [X] T026 [US2] Rodar `tests/relatorio/test_resumo.py` e a suíte; corrigir até passar.

**Checkpoint**: as histórias 1 e 2 completas; o resumo é o MVP entregável.

---

## Phase 5: User Story 3 - O mesmo resumo para qualquer tipo de usina (Priority: P2)

**Goal**: o resumo sai para todos os caminhos da 006, com os indicadores e as colunas anuais de cada um e os números de conjunto identificados.

**Independent Test**: gerar o resumo das usinas fictícias de cada tipo e conferir o limite de páginas, as colunas do caminho e o nível dos números.

**Dependência**: usinas fictícias de todos os tipos e a tabela anual da base horária comum da 006 (tarefas T052, T053 e T063 a T065 da 006).

### Tests for User Story 3 ⚠️

- [X] T027 [P] [US3] Em `tests/integracao/test_usinas_ficticias.py` (da 006), para cada usina fictícia:
  - o resumo tem no máximo `RESUMO_MAXIMO_PAGINAS` páginas;
  - a evolução anual tem os cabeçalhos de `COLUNAS_RESUMO_ANUAL` do caminho da usina;
  - nas usinas sem EVT, o resumo não contém "EVT" nem "energia vertida";
  - na usina em conjunto de usinas, os números do conjunto vêm com "do conjunto", como no relatório completo (FR-016);
  - "Sobre os dados" fica dentro de `RESUMO_MAXIMO_PALAVRAS_DADOS`.

### Implementation for User Story 3

- [X] T028 [US3] Em `src/relatorio/resumo.py`:
  - acrescentar a `COLUNAS_RESUMO_ANUAL` a entrada do caminho sem EVT, com os cabeçalhos exatos da tabela anual da base horária comum da 006, pela regra da decisão R6: Ano e até cinco colunas, com a disponibilidade, o fator de capacidade, a geração ÷ garantia física (quando o tipo tem) e o principal indicador de perda do tipo;
  - escolher a entrada pelo mesmo critério de caminho da 006 (registrado na T005);
  - a linha de tipo do cabeçalho passa a usar `res.tipo` quando existir.
- [X] T029 [US3] Em `src/comum/regras.py`, acrescentar ao `GLOSSARIO_RESUMO` os termos dos tipos novos que aparecerem nos resumos das usinas fictícias, como constrained-off e CVU, com o texto aprovado pelo usuário. Registrar a aprovação.
- [X] T030 [US3] Rodar `tests/integracao/test_usinas_ficticias.py` e a suíte; corrigir até passar.

**Checkpoint**: todas as histórias funcionando.

---

## Phase 6: Polish & Cross-Cutting Concerns (validação real, referência e encerramento)

**Purpose**: execução real, aprovação, referência e incorporação à spec 005.

- [X] T031 Execução real da São Domingos ([quickstart](quickstart.md), seções 2 a 4):
  - `python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"`, com código 0;
  - conferir o log e `reports/sao_domingos/etapa.json` (`resumo_executivo` com `paginas` 2, `evolucao_anual` verdadeiro e `palavras` até 1.000);
  - rodar a conferência da conclusão do quickstart (seção 3), com o resultado `True`;
  - ver as duas páginas: renderizar o PDF em PNG com `pymupdf`, instalado com `pip install --target <scratchpad>/libs pymupdf` e usado com `PYTHONPATH`, fora do `requirements.txt`;
  - conferir os itens da seção 4 do quickstart.

  Registrar.
- [X] T032 Guarda do relatório aprovado: `python -m src comparar --todas --coleta` deve terminar com código 6 e exatamente duas diferenças, `resumo_executivo.pdf` e `resumo_executivo.md`, ambas "só na pasta atual", e nenhuma no relatório, na planilha, no CSV e nas figuras (decisão R12, SC-006). Qualquer outra diferença: parar e corrigir. Registrar.
- [X] T033 Levar ao usuário o `reports/sao_domingos/resumo_executivo.pdf` e as cinco perguntas da SC-005. Registrar a aprovação ou os ajustes pedidos. Ajuste no texto gerado volta às tarefas da história afetada.
- [X] T034 Com a aprovação da T033 (princípio IX): `python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "<data da aprovação>"`. Conferir em `relatorios_referencia/sao_domingos/referencia.json` os dois arquivos do resumo, depois `python -m src comparar --todas --coleta` com código 0. Registrar.
- [X] T035 [P] Em `README.md`, na árvore de pastas (linha de `reports/<slug>/`) e onde as saídas são citadas, acrescentar `resumo_executivo.pdf` e `.md`, com uma frase sobre o resumo.
- [X] T036 Portão final: suíte sem rede; `pyflakes` de fora do `venv` em `src/` e `tests/` (`pip install --target <pasta temporária> pyflakes`, usado com `PYTHONPATH`); `/speckit-converge`. Registrar.
- [X] T037 Incorporar a mudança à spec da etapa (Governança 2):
  - em `specs/005-geracao-relatorio/spec.md`: objetivo, entradas e saídas, a história do resumo, as FR-001 a FR-021 desta spec (com A1 e A2), os casos de borda e os critérios de sucesso, renumerados no padrão da 005;
  - no `plan.md`, no `data-model.md` e nos `contracts/` da 005, o que vier do plano, do data-model e do contrato desta spec;
  - levar ao usuário e registrar a aprovação.
- [X] T038 Com a aprovação da T037:
  - excluir `specs/007-resumo-executivo/`;
  - apontar `.specify/feature.json` para a spec ativa seguinte (a 006, se ainda aberta, ou `specs/005-geracao-relatorio`);
  - atualizar no `README.md` qualquer citação à pasta excluída.

---

## Revisão 1 (13/10/2026): conclusão por último

**Purpose**: pedido do usuário ao ver o resumo da São Domingos. A ordem dos blocos passa a ser cabeçalho, indicadores-chave, evolução anual, "Sobre os dados" e conclusão (FR-007 e cenário 2 da US1, revisados na spec, no contrato e no quickstart).

- [X] T039 [US1] Em `tests/relatorio/test_resumo.py`, `test_blocos_na_ordem_fixa` com a ordem nova: Indicadores-chave, Evolução anual, Sobre os dados, Conclusão. Confirmar que falha.
- [X] T040 [US1] Em `src/relatorio/resumo.py`: `TITULOS_BLOCOS` na ordem nova; `texto_corrido` seguindo `blocos()`, para que a linha de termos siga a ordem de leitura; docstring do módulo com a ordem nova. Rodar `tests/relatorio/` e a suíte.
- [X] T041 [US1] Execução real: `python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"`; resumo com no máximo duas páginas, renderizado para conferência; `comparar --usina sao_domingos --referencia <linha de base da 007>` só com os dois arquivos do resumo. Registrar.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (fase 1)**: depende do portão da fase A da 006 (T001). Bloqueia tudo.
- **Foundational (fase 2)**: depende da fase 1. Bloqueia as histórias.
- **US1 (fase 3)**: depende da fase 2.
- **US2 (fase 4)**: depende da US1. O bloco de conclusão nasce na T017; a US2 fecha os casos de borda e a igualdade estrita.
- **US3 (fase 5)**: depende da US1 e das usinas fictícias e da tabela anual da base horária comum da 006. Pode ficar para depois do encerramento da São Domingos (T031 a T034) se a 006 ainda não tiver esses itens.
- **Polish (fase 6)**: T031 a T034 dependem da US1 e da US2. T036 a T038 dependem de todas as histórias.

### Within Each User Story

- Testes escritos e falhando antes do código.
- `resumo.py` (montagem, T017) → Markdown (T018) e PDF (T019) → orquestração (T020) → etapa (T021).

### Parallel Opportunities

- Fase 1: T006 em paralelo com T001 a T005.
- Fase 2: T007, T008, T009 e T011 em paralelo (arquivos diferentes). T010 mexe em `conteudo.py` e `pdf.py`, sem conflito com as outras.
- US1: T014, T015 e T016 em paralelo (T014 e T015 no mesmo arquivo novo: escrever em sequência se forem feitos pelo mesmo agente). T018 e T019 em paralelo depois da T017.
- US2: T023 e T024 em paralelo (mesmo arquivo; mesma ressalva).
- Fase 6: T035 em paralelo com T031 a T034.

---

## Parallel Example: User Story 1

```text
# Testes da US1, juntos:
Task: "T014 testes do documento em tests/relatorio/test_resumo.py"
Task: "T016 saídas do resumo em tests/integracao/test_usina_ficticia.py"

# Depois da montagem (T017), os dois geradores, juntos:
Task: "T018 gerar_resumo_md em src/relatorio/resumo.py"
Task: "T019 gerar_resumo_pdf em src/relatorio/resumo_pdf.py"
```

---

## Implementation Strategy

### MVP (US1 + US2)

1. Fases 1 e 2: aprovações, fundações e `comparar` sem diferença.
2. US1: o resumo completo sai com o relatório.
3. US2: a conclusão igual, com os casos de borda.
4. **Parar e validar**: T031 a T034, com a São Domingos e a aprovação do usuário.

### Entrega incremental

1. MVP aprovado e registrado como referência.
2. US3 quando a 006 tiver as usinas fictícias de todos os tipos e a tabela anual da base horária comum.
3. Encerramento: T035 a T038.

---

## Notes

- Tarefas marcadas com [P]: arquivos diferentes, sem dependência.
- Cada tarefa termina com a suíte aprovada. Commit só quando o usuário pedir.
- Nunca editar `src/` com um `completo` ou `comparar --todas` rodando em segundo plano: cada processo novo importa o código editado.
- Os números da São Domingos citados neste arquivo servem só de exemplo e para a validação real; nenhum entra no código.

---

## Registro de execução

| Tarefa | Data | Comando ou ação | Resultado |
|---|---|---|---|
| T001 | 13/10/2026 | Conferência do portão da fase A da 006 | Não atingido (T042 a T074 da 006 abertas). O usuário pediu a implementação assim mesmo ("aprovo A1 e A2, implemente"): decisão R13 ajustada, registrada em "Decisões do usuário" da spec. A guarda do relatório passa a ser a comparação com a linha de base gerada pelo código de antes da mudança |
| T002 | 13/10/2026 | `git status --short relatorios_referencia/sao_domingos` | Referência com mudanças não commitadas (`perfil.toml`, `perfil_estatistico_anual.xlsx`, `referencia.json`, do novo congelamento da 006). A T034 (registro da nova referência) fica para depois do commit pelo usuário. Também há edições do usuário não commitadas em `src/relatorio/pdf.py` (título da capa) e `src/relatorio/figuras.py` (títulos de duas figuras), mantidas como estão |
| T003 | 13/10/2026 | `python -m src copia-seguranca --motivo antes_resumo_executivo` | Código 0: `_backup_2026-10-13_antes_resumo_executivo` criada e conferida (264 arquivos); excluída a mais antiga, `_backup_2026-10-08_antes_ampliacao_tipos_de_geracao` (a `linha_de_base` dela continua em `relatorios_referencia/sao_domingos/` e no commit `c5efe0b`). Ficam duas cópias |
| — | 13/10/2026 | Linha de base da 007: `python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"` com o código de antes da mudança, copiada para a pasta temporária da sessão | Código 0, 21 s, PDF de 30 páginas |
| T004 | 13/10/2026 | Ajustes A1 e A2 aprovados pelo usuário e aplicados à spec (FR-002, cenário 4 da US1, FR-013, "Decisões do usuário") | Feito. O texto do `GLOSSARIO_RESUMO` vai à aprovação junto com o resumo da São Domingos (T033) |
| T005 | 13/10/2026 | Leitura das funções reaproveitadas | Sem mudança da 006 (fase A ainda sem as T063 a T066): `listas_conclusao`, `indicadores_capa`, `linhas_tabela_anual`, `pares_identificacao`, `secoes_presentes`, `FRASE_ABERTURA_CONCLUSAO`, `FRASE_CONCLUSAO_VAZIA`; título da capa em `pdf.py`, `_capa`; caminho único (hidrelétrica com EVT) |
| T006 | 13/10/2026 | Comentário "Sync Impact Report" retirado de `.specify/memory/constitution.md` | Feito |
| T007 a T011 | 13/10/2026 | Caminhos, regras gerais, textos curtos das conferências, `fontes_resumo`, `titulo_capa_relatorio` e testes | `tests/relatorio/test_fontes.py`: 60 aprovados. A contagem da TEIFa e da TEIP passou a `_reproducao_taxas`, usada pelo texto longo (sem mudança) e pelo curto |
| T012 | 13/10/2026 | `python -m pytest tests -q -p no:cacheprovider` | 496 aprovados (155 s) |
| T013 | 13/10/2026 | `relatorio` e `comparar --usina sao_domingos --referencia <linha de base da 007>` | "Nenhuma diferença." (código 0) |
| T014 a T016 | 13/10/2026 | Testes escritos antes do código: `tests/relatorio/test_resumo.py` (13 da US1), `tests/relatorio/test_gravacao.py` (resumo simulado e falha no resumo), `tests/integracao/test_usina_ficticia.py` (resumo entre as saídas) | Falharam por falta de `src/relatorio/resumo.py`, como esperado |
| T017 a T021 | 13/10/2026 | `src/relatorio/resumo.py` (montagem, Markdown e regra das duas páginas), `src/relatorio/resumo_pdf.py` (PDF A4 retrato; `paginas_do_pdf` passou para cá e é importada por `etapa.py`) e integração em `src/relatorio/etapa.py` | Feito. Nos testes com `_tudo` e `_neutro`, a conclusão é refeita com `montar_conclusao` e as conferências recebem um resultado mínimo (esses resultados só trazem os campos das regras) |
| T022 | 13/10/2026 | `python -m pytest tests -q -p no:cacheprovider` | 515 aprovados (163 s) |
| T023 a T026 | 13/10/2026 | Testes da US2 (conclusão igual à do relatório com as regras do sintético, com todas as regras e vazia; sem termos de parecer fora dela) | Aprovados sem mudança no código: a conclusão já vinha das mesmas funções e frases do relatório |
| T031 | 13/10/2026 | `python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"`; páginas renderizadas com `pymupdf` (pasta temporária) | Código 0. Resumo com 2 páginas: cabeçalho e conclusão (19 itens) na primeira; fim da conclusão, indicadores, evolução anual e "Sobre os dados" na segunda, com folga. Na primeira execução, 997 palavras fora das tabelas pela contagem de `\w+`, que conta datas e códigos como várias palavras; a contagem passou a palavras separadas por espaço: 933. Glossário com ONS e TEIF acrescentados e textos encurtados. `comparar --usina sao_domingos --referencia <linha de base da 007>`: só `resumo_executivo.md` e `resumo_executivo.pdf`, "só na pasta atual" (código 6, o esperado) |
| T035 | 13/10/2026 | `README.md`: o resumo nas saídas do relatório e na árvore de pastas | Feito |
| T036 (parcial) | 13/10/2026 | `pyflakes` de fora do `venv` em `src/` e `tests/` | Só os 6 avisos de antes (`tests/relatorio/test_markdown.py`); o `test_resumo.py` usa fixtures locais, sem avisos. Falta o `/speckit-converge`, depois das T033 e T034 |
| T032 (em aberto) | 13/10/2026 | `python -m src comparar --todas --coleta` | Código 6, com 5 diferenças: `resumo_executivo.md` e `resumo_executivo.pdf` "só na pasta atual" (desta mudança) e `relatorio_analise_estatistica.pdf`, `figures/02_evt_mensal.png` e `figures/06_disponibilidade_operacional_sincronizada_mensal.png` com conteúdo diferente. As três últimas vêm das edições não commitadas do usuário em `src/relatorio/pdf.py` (título da capa) e `src/relatorio/figuras.py` (rótulo da figura 02 e título da figura 06), anteriores a esta mudança: a linha de base da 007, gerada antes de qualquer código desta spec, já as tinha, e o relatório atual é igual a ela. A Coleta refeita não acusou diferença. A tarefa fecha quando o usuário decidir sobre as suas edições (aprovar como parte da nova referência ou desfazer) |
| — | 13/10/2026 | `python -m pytest tests -q -p no:cacheprovider`, depois do glossário e da contagem de palavras | 515 aprovados (171 s) |
| Revisão 1: T039 a T041 | 13/10/2026 | Pedido do usuário ("resumo ficou EXCELENTE! porém troque a ordem, a conclusão deve ficar por último"): spec (FR-007, cenário 2 da US1, premissa e decisão), contrato, quickstart, `test_blocos_na_ordem_fixa` (falhou antes do código), `TITULOS_BLOCOS` e `texto_corrido` em `src/relatorio/resumo.py` | `tests/relatorio`: 135 aprovados; suíte: 515 aprovados (154 s). `relatorio` da São Domingos: 2 páginas, 933 palavras; página 1 com cabeçalho, termos, indicadores, evolução anual e "Sobre os dados"; página 2 só com a conclusão. `comparar` com a linha de base da 007: só os dois arquivos do resumo |
| T032 a T034 | 19/10/2026 | Aprovação do usuário ("esse relatório está aprovado"), inclusive das edições dele no título da capa e nos títulos das figuras 02 e 06 e do texto da linha de termos; `referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "19/10/2026"`; `comparar --todas --coleta` | `referencia`: código 0, já com `resumo_executivo.pdf` e `.md`. `comparar --todas --coleta`: código 0, sem diferença |
| T027 | 19/10/2026 | `tests/integracao/test_usinas_ficticias.py` (+3, escritos antes do código) | Para as sete usinas fictícias: resumo com até 2 páginas e listado no `etapa.json`; evolução anual com os cabeçalhos de `COLUNAS_RESUMO_ANUAL` do caminho; sem "EVT" nem "energia vertida" nas usinas sem EVT; "Sobre os dados" dentro do limite; na PCH em conjunto, os números do conjunto como do conjunto (indicadores e coluna Nível) e a frase da conclusão sem itens; na UTE, a conclusão do relatório copiada igual. |
| T028 | 19/10/2026 | `src/relatorio/resumo.py` e `src/relatorio/etapa.py` | Caminho pelo mesmo critério da 006 (`sem_evt`); `COLUNAS_RESUMO_ANUAL["sem_evt"]` = Ano, Nível, Geração média (MWmed), Energia (MWh), Fator de capacidade e Disp. (% Pinst), nas que a tabela da usina tem (regra R6; a geração ÷ garantia física e o indicador de perda do tipo entram com as seções do tipo, fases B e C da 006); indicadores e tabela anual de `src/relatorio/comum.py`; linha de tipo com `res.tipo`; sem agentes fora do caminho da EVT; "Sobre os dados" com a série de referência e o nível, as horas sinalizadas e só as conferências que não dependem da EVT; frase da conclusão vazia por caminho (`frase_sem_itens`). A etapa do relatório volta a gerar o resumo para todas as usinas. |
| T029 | 19/10/2026 | resumos das sete usinas fictícias e da William Arjona | Nenhum termo novo na fase A: os resumos usam as siglas do glossário (ONS, MWmed, Pinst, DISPF, TEIFa, TEIP, TEIF); CEG, R7 e o código do tipo já apareciam sem glossário no resumo aprovado da São Domingos. CVU, CMO e constrained-off entram com as fases B e C da 006, com o texto aprovado pelo usuário (rascunho 005 da fase B). |
| T030 | 19/10/2026 | suíte, pyflakes e `comparar --todas --coleta` | 687 aprovados; pyflakes sem aviso; `comparar` só com as diferenças da Coleta aceitas pelo usuário (republicação do ONS), sem diferença no relatório e no resumo da São Domingos. Resumo da William Arjona: 2 páginas, 399 palavras, com a evolução anual. |

## Phase 7: Convergence

- [X] T042 Pôr a parcela total de horas sinalizadas na constatação de qualidade das usinas sem EVT (`src/analises/constatacoes.py`), para que o número citado em "Sobre os dados" esteja no relatório completo também quando uma hora tem mais de um código, e estender a verificação "todo número do resumo está no relatório" aos resumos das sete usinas fictícias (`tests/integracao/test_usinas_ficticias.py`) per FR-014 e SC-003 (partial)
- [X] T043 Decidir com o usuário os agentes do cabeçalho nas usinas sem EVT, que hoje saem sem agente: o agente atual de cada unidade da Capacidade de geração, identificado como tal na capa e no resumo, ou a limitação registrada na FR-008 per FR-008 (partial)

### Registro da convergência (19/10/2026)

| Tarefa | Data | Comando | Resultado |
|---|---|---|---|
| T036 | 19/10/2026 | suíte, `pyflakes` (Python do sistema, fora do `venv`) e `/speckit-converge` | 687 aprovados; pyflakes sem aviso; converge com 2 achados, anexados como Phase 7: Convergence (T042 e T043). |
| T042 | 19/10/2026 | `src/analises/constatacoes.py` e `tests/integracao/test_usinas_ficticias.py` | A constatação de qualidade das usinas sem EVT traz a parcela total das horas sinalizadas (citada em "Sobre os dados"); a verificação "todo número do resumo está no relatório" vale para os sete resumos fictícios. |
| T043 | 19/10/2026 | — | Em aberto: decisão do usuário sobre os agentes do cabeçalho nas usinas sem EVT. |
| T043 | 19/10/2026 | decisão do usuário ("Mostrar agente atual"); `src/coleta/etapa.py`, `src/analises/comum_tipos.py`, `src/analises/etapa.py`, `src/relatorio/comum.py`, `src/relatorio/fontes.py` e `src/relatorio/resumo.py` | A Coleta grava o agente proprietário e o operador de cada unidade em `capacidade_ficha.csv`; as Análises tiram os das unidades ativas no fim do período (`comum["agentes"]`); a capa ("Agente atual") e o resumo ("Agente atual (Capacidade de geração do ONS)") os mostram, com a Capacidade de geração na legenda de fonte da identificação. Teste em `tests/integracao/test_usinas_ficticias.py`; FR-008 e decisões da spec registradas. |
| T037 e T038 | 19/10/2026 | decisão do usuário ("faça o item 3 como achar melhor") | Ficam para o fechamento da spec 006 (fase F), junto com os ajustes da 006 na spec 005, para editar a spec 005 uma vez só. |

### 23/10/2026 — T037 e T038 (no fechamento da spec 006)

- **T037**: a spec foi incorporada à spec da Geração do relatório (`specs/005-geracao-relatorio/`): a história do resumo como US11, as FR-001 a FR-021 como FR-050 a FR-070 (FR-n → FR-(n+49)), os critérios SC-001 a SC-006 como SC-015 a SC-020, as decisões R2 a R12 e R14 como D23 a D33 e D34 do plano, o data-model na seção 2.10 e o contrato `resumo-executivo.md`. Aprovada pelo usuário com o fechamento da 006.
- **T038**: por decisão do usuário de 23/10/2026, a pasta não é excluída e fica como histórico (o cabeçalho do `spec.md` diz que ela foi incorporada); `.specify/feature.json` não muda; o README não cita esta pasta.

