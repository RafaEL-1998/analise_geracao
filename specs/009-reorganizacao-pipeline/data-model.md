# Data Model: Reorganização do Projeto num Fluxo de Cinco Etapas

**Feature**: [spec.md](spec.md) · **Decisões**: [research.md](research.md) · **Date**: 2026-10-07

---

## 1. Classificação das constantes de `src/config.py` (R6)

| Grupo | Constantes de hoje | Destino |
|---|---|---|
| Identificação da usina | `COD_USINA_ONS` (153), `NOME_RESERVATORIO_REFERENCIA` ("SAO DOMINGOS"), `CEG_USINA`, `ID_ONS_USINA` ("MSUHSD"), `COD_EXIBICAO_USINA_PROGRAMACAO` ("PRUHSD"), `ID_RESERVATORIO_ONS` ("PNUHSD"), `ESTADO_USINA` ("MS") | perfil, `[identificacao]` e `[usina]` |
| Parâmetros técnicos | `NOMINAL_INSTALLED_CAPACITY_MW`, `NUMERO_UNIDADES_GERADORAS`, `POTENCIA_UNITARIA_MW`, `TIPO_TURBINA`, `ENGOLIMENTO_NOMINAL_UG_M3S`, `GARANTIA_FISICA_MWMED`, `IP_REFERENCIA`, `TEIF_REFERENCIA`, `QUEDA_BRUTA_M`, `PERDA_HIDRAULICA_M`, `RENDIMENTO_TURBINA_GERADOR`, `VAZAO_REMANESCENTE_M3S`, `ANO_INICIO_OPERACAO_COMERCIAL` | perfil, `[parametros]` e `[usina]` |
| Fontes dos parâmetros | `FONTE_PARAMETROS_USINA`, `FONTE_GARANTIA_FISICA` | perfil, `[parametros.fontes]` |
| Características da usina usadas nas análises | `LIMIAR_VERTIMENTO_MINIMO_M3S` (6,0, patamar contínuo da série); `FAIXAS_GERACAO_INTERMEDIARIAS_MW` (10, 20, 30 e 40 MW, hoje em `analyzer.py`) | perfil, `[analises]` |
| Derivadas do perfil | `ENGOLIMENTO_MAXIMO_USINA_M3S`, `POTENCIA_AUTORIZADA_ESPERADA_MW`, `DISPONIBILIDADE_REFERENCIA`, `PRODUTIVIDADE_NOMINAL_MW_M3S`, `_LIMITE_POTENCIA_MW`, `_LIMITE_VAZAO_TURBINAVEL_M3S`, `LIMITES_FISICOS_SUPERIORES` | calculadas na leitura do perfil |
| Regras gerais de classificação | `LIMIAR_GERACAO_PARADA_MW` (1), `LIMIAR_SINCRONIZADA_MW` (1), `LIMIAR_DESVIO_PROGRAMACAO_MW` (5), `LIMIAR_INDISPONIBILIDADE_TOTAL_MW` (0,001), `FRACAO_PLENA_CARGA` (0,90), `DURACAO_MINIMA_EVENTO_RELATORIO_H` (24), `NUMERO_EVENTOS_RELATORIO` (15), `HORAS_DIURNAS`, `HORAS_NOTURNAS`, `RAZAO_DIURNA_RELEVANTE` (2, hoje em `analyzer.py`) | `src/comum/regras.py` |
| Tolerâncias e metas | `TOLERANCIA_DIVERGENCIA_HORAS`, `TOLERANCIA_COINCIDENCIA_MW`, `TOLERANCIA_COINCIDENCIA_VAZAO_M3S`, `TOLERANCIA_REPRODUCAO_TAXAS_PP`, `META_ALINHAMENTO_HIDROLOGIA_PCT`, `TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW`, `DESVIO_MAXIMO_NIVEL_M`, `PHYSICAL_TOLERANCE_EPSILON`, `TOLERANCIA_LIMITES_FISICOS`, `FAIXA_PRODUTIVIDADE_RELATIVA`, `TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW` | `src/comum/regras.py` |
| Fontes do ONS | `ONS_CKAN_PACKAGE_URL`, `ONS_DATASET_URL`, `ONS_CKAN_PACKAGE_SHOW_URL`, `ONS_PORTAL_DATASET_URL`, `CONJUNTO_*`, `CONJUNTOS_INDICADORES_ONS`, `CONJUNTOS_PIPELINE`, `FORMATO_PROGRAMACAO_DIARIA`, `PATAMARES_POR_DIA`, `OPERATIONAL_METRIC_COLUMNS` | `src/comum/regras.py` |
| Download | `DOWNLOAD_CHUNK_SIZE`, `REQUEST_TIMEOUT`, `MAX_DOWNLOAD_RETRIES`, `RETRY_BACKOFF_FACTOR` | `src/comum/regras.py` |
| Caminhos | `BASE_DIR`, `DATA_DIR`, `RAW_DATA_DIR`, `*_RAW_DIR`, `RAW_MANIFEST_FILE`, `DIRETORIO_DICIONARIOS` (compartilhados); `PROCESSED_DATA_DIR`, `REPORTS_DIR` e todos os `*_FILE` (por usina) | `src/comum/caminhos.py` (funções que recebem o slug) |
| Dicionário legado | `DATA_DICTIONARY_JSON` (arquivo na raiz) | sai; o validador usa o dicionário baixado (R15) |
| Figuras | `DEFAULT_PLOT_DPI` (300); `TAMANHO_FIGURA_PADRONIZADA` (hoje em `analyzer.py`) | `src/comum/regras.py` |
| Limiares da conclusão (novos, R17) | EVT parada ≥ 10 %; programação ≤ 1 MW ≥ 50 %; afluência no engolimento ≥ 80 %; unidade ≥ 2/3 da TEIFa ou limitação forçada (HEDF) em ≥ 50 % dos meses; não sincronizada × reserva ≥ 5 GWh; R7 ≥ 100 h; indisponibilidade total ≥ 30 dias; programada da unidade ≥ 20 %; R9 ≥ 24 h; até 5 itens por lista | `src/config.py` na fase 1; `src/comum/regras.py` depois |

---

## 2. Perfil da usina (`usinas/<slug>/perfil.toml`)

| Seção.campo | Tipo | Validação | São Domingos |
|---|---|---|---|
| `usina.slug` | texto | `[a-z0-9_]+`; igual ao nome da pasta | `sao_domingos` |
| `usina.nome` | texto | não vazio; usado no título e nos textos | `UHE São Domingos` |
| `usina.estado` | texto | 2 letras maiúsculas | `MS` |
| `usina.inicio_operacao_comercial` | inteiro | 1900 a ano atual | `2013` |
| `identificacao.cod_usina` | inteiro | > 0 | `153` |
| `identificacao.nome_ons` | texto | maiúsculas sem acento; nome da usina e do reservatório nos conjuntos do ONS | `SAO DOMINGOS` |
| `identificacao.ceg` | texto | padrão `UHE.PH.UF.NNNNNN-D.DD` | `UHE.PH.MS.028761-0.01` |
| `identificacao.id_ons` | texto | não vazio | `MSUHSD` |
| `identificacao.cod_programacao` | texto | não vazio | `PRUHSD` |
| `identificacao.id_reservatorio` | texto | não vazio | `PNUHSD` |
| `parametros.potencia_instalada_mw` | real | > 0 | `48.0` |
| `parametros.unidades_geradoras` | inteiro | ≥ 1 | `2` |
| `parametros.potencia_unitaria_mw` | real | > 0; × unidades = potência instalada (± 0,1) | `24.0` |
| `parametros.tipo_turbina` | texto | não vazio | `Kaplan de eixo vertical` |
| `parametros.engolimento_nominal_ug_m3s` | real | > 0 | `81.5` |
| `parametros.garantia_fisica_mwmed` | real | > 0; ≤ potência instalada | `36.4` |
| `parametros.ip_referencia` | real | 0 ≤ x < 1 | `0.06861` |
| `parametros.teif_referencia` | real | 0 ≤ x < 1 | `0.02333` |
| `parametros.queda_bruta_m` | real | > 0 | `35.24` |
| `parametros.perda_hidraulica_m` | real | ≥ 0; < queda bruta | `0.747` |
| `parametros.rendimento_turbina_gerador` | real | 0 < x ≤ 1 | `0.9053` |
| `parametros.vazao_remanescente_m3s` | real | ≥ 0 | `4.78` |
| `parametros.fontes.geral` | texto | não vazio | `RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3` |
| `parametros.fontes.garantia_fisica` | texto | não vazio | `ANEEL, valor vigente consultado em 02/10/2026` |
| `analises.vertimento_minimo_m3s` | real | ≥ 0 (0 = usina sem vertimento contínuo) | `6.0` |
| `analises.faixas_geracao_mw` | lista de reais | crescente; todos > 1 MW (parada) e < plena carga | `[10.0, 20.0, 30.0, 40.0]` |

O perfil é recusado antes da coleta (código 4) quando falta campo, quando o tipo ou a faixa estão errados ou quando há incoerência. A mensagem lista todos os problemas de uma vez.

O contrato completo, com o arquivo da São Domingos, está em [contracts/perfil-usina.md](contracts/perfil-usina.md).

---

## 3. Manifesto da etapa (`etapa.json`, uma por pasta de etapa)

| Campo | Conteúdo |
|---|---|
| `etapa` | `coleta`, `tratamento`, `conferencia`, `analises` ou `relatorio` |
| `usina` | slug |
| `versao_formato` | inteiro; muda quando os arquivos da etapa mudam de formato |
| `iniciada_em`, `concluida_em` | data e hora (UTC) |
| `status` | `concluida`, `falha` ou `desatualizada` |
| `codigo_saida` | código da execução |
| `etapa_anterior` | `{etapa, concluida_em}` da etapa usada como entrada (vazio na coleta) |
| `arquivos` | lista `{nome, bytes, sha256}` dos arquivos gravados |
| `resumo` | números principais da etapa, como registros extraídos, horas tratadas, situação de cada conferência e quantidade de constatações |

**Transições**:
- Ao iniciar, a etapa confere se a anterior está `concluida`. Se não estiver, sai com código 5, sem gravar nada.
- Ao terminar com sucesso, grava `concluida` e marca como `desatualizada` o manifesto das etapas seguintes que já existirem. Elas precisam rodar de novo antes das que dependem delas.
- Em erro, grava `falha` com o código, e a etapa seguinte recusa.

---

## 4. Artefatos de cada etapa (layout da R7)

| Etapa | Pasta | Arquivos | Origem hoje |
|---|---|---|---|
| Coleta (compartilhado) | `data/raw/` | arquivos de cada conjunto, `_manifesto_ons.json` por pasta, `_dicionarios/` e `_versoes_anteriores/` (no máximo duas por arquivo) | igual |
| Coleta (usina) | `data/usinas/<slug>/coleta/` | `evt_extraido.csv`, `auditoria_evt.csv`, `<conjunto>_extraido.parquet` (indicadores, programação, disponibilidade, hidrologia, geração), `cadastro_ficha.csv`, `auditoria_<conjunto>.csv` (parte da extração), `dicionarios.csv`, `etapa.json` | `uhe_sao_domingos_energia_vertida_consolidado.csv`, `relatorio_auditoria_varredura.csv`, `uhe_sao_domingos_ons_cadastro.csv`, `relatorio_auditoria_cadastro_ons.csv`, `relatorio_dicionarios_ons.csv`; os extraídos em Parquet são novos |
| Tratamento | `data/usinas/<slug>/tratamento/` | `evt_tratado.parquet`, `.csv` e `.xlsx`; `validacao_fisica.csv` e `.md`; `indicadores_ug_mensal.csv`, `indicadores_ug_anual.csv`, `horas_estado_mensal.csv`, `teifa_teip_mensal.csv`, `indicadores.xlsx`; `programacao_horaria.csv`, `programacao_dias_ausentes.csv`; `<conjunto>_horaria.csv` e `<conjunto>_ausencias.csv` (disponibilidade, hidrologia, geração); `auditoria_<conjunto>.csv` (completa); `.bak` de cada arquivo; `etapa.json` | os arquivos de mesmo conteúdo em `data/processed/` |
| Conferência | `data/usinas/<slug>/conferencia/` | `conferencias.pkl` (seção 5) e um CSV por conferência: `geracao.csv`, `geracao_divergencias.csv`, `disponibilidade.csv`, `disponibilidade_divergencias.csv`, `vazoes.csv`, `dispf_horas.csv`, `teifa_teip.csv`, `cadastro.csv`; `etapa.json` | `uhe_sao_domingos_ons_hidrologia_alinhamento.csv`, `uhe_sao_domingos_ons_divergencias_indicadores.csv`; os demais eram só abas da planilha |
| Análises | `data/usinas/<slug>/analises/` | `resultados.pkl` (seção 5) e `etapa.json` | em memória, dentro do `analyzer` |
| Relatório | `reports/<slug>/` | `relatorio_analise_estatistica.pdf` e `.md`, `perfil_estatistico_anual.xlsx` e `.csv`, `figures/*.png` (8), `etapa.json` | `reports/` |

Os nomes de arquivo deixam de levar o prefixo `uhe_sao_domingos_` porque a pasta já identifica a usina. Os nomes das abas da planilha e das figuras não mudam.

---

## 5. Objetos passados entre etapas

### Resultado de conferência (um por conferência, em `conferencias.pkl`)

| Campo | Conteúdo |
|---|---|
| `id` | `geracao`, `disponibilidade`, `vazoes`, `dispf_horas`, `teifa_teip` ou `cadastro` |
| `aplicavel` | falso quando a base não existe para a usina; vem com `motivo` |
| `bases` | as duas bases comparadas |
| `periodo` | início e fim comparados |
| `unidade` | horas, meses, meses-unidade ou campos |
| `comparados`, `coincidentes`, `divergentes` | quantidades |
| `tolerancia` | critério de coincidência (ex.: 0,01 MW; 0,5 m³/s; 1 h; 0,001 p.p.) |
| `meta`, `meta_atingida` | só nas vazões (99 %); meta não atingida faz a etapa sair com código 3 |
| `tabelas` | os DataFrames que as funções de hoje já produzem, como a conferência e as divergências da geração, o alinhamento da hidrologia, as divergências do DISPF e o recálculo da TEIFa e da TEIP |

### Resultados das análises (`resultados.pkl`)

- É o `ResultadosAnalise` de hoje, com os mesmos campos, mais:
  - `conclusao`: itens da conclusão (seção 10), acrescentado na fase 1;
  - `serie_diaria`: médias diárias de disponibilidade, geração e EVT da figura 01, hoje calculadas dentro do gráfico;
  - `vazoes_anuais`: médias anuais das vazões da figura 05, idem.
- Os resultados de conferência entram nos mesmos campos de hoje (`ons`, `disponibilidade`, `hidrologia`, `geracao_oficial`, `cadastro`), para que o mapa de fontes e o relatório não mudem.
- O arquivo traz `versao_formato`, que é conferida na leitura.

---

## 6. Destino de cada módulo atual (R10)

| Hoje | Destino |
|---|---|
| `main.py` | `src/__main__.py` (linha de comando) e `src/pipeline.py` (etapas, manifestos e pré-requisitos) |
| `config.py` | `src/comum/regras.py`, `src/comum/caminhos.py` e `src/comum/perfil.py` (seção 1) |
| `logger.py`, `formatacao.py`, `persistencia.py`, `models.py` | `src/comum/` (`logger.py`, `formatacao.py`, `persistencia.py`, `modelos.py`) |
| (novo) | `src/comum/copia_seguranca.py`; `src/comum/comparacao.py` (comando `comparar`) |
| `collector.py` | `src/coleta/catalogo.py`, com a poda das versões anteriores |
| `filter.py`, `consolidator.py` | `src/coleta/evt.py` |
| `dicionarios_ons.py` | `src/coleta/dicionarios.py` |
| `conjuntos_ons.py` | `src/coleta/conjuntos.py`: descrição, seleção, sincronização, identificação, leitura numérica e auditoria; `src/tratamento/series.py`: hora de início, duplicatas, período, ausências, gravação e leitura; `periodos_continuos` vai para `src/comum/` |
| `indicadores_ons.py` | `src/coleta/indicadores.py` (seleção, sincronização, filtro por CEG); `src/tratamento/indicadores.py` (tratar e recortar, montar, gravar e ler); `src/conferencia/indicadores.py` (comparação DISPF × horas e recálculo TEIFa/TEIP); `src/analises/indicadores.py` (decomposição e `analisar_indicadores_ons`) |
| `programacao_ons.py` | `src/coleta/programacao.py`; `src/tratamento/programacao.py` (programação horária, montar, gravar e ler); `src/analises/programacao.py` (classificação das horas, resumos, eventos, perfil e `analisar_programacao`) |
| `disponibilidade_ons.py` | coleta (descrição); `src/tratamento/disponibilidade.py` (qualidade, gravar e ler); `src/conferencia/disponibilidade.py` (`conferir_com_evt`); `src/analises/disponibilidade.py` (horas paradas, resumos e `analisar_disponibilidade`) |
| `hidrologia_ons.py` | coleta (descrição); `src/tratamento/hidrologia.py` (qualidade, nível implausível, gravar e ler); `src/conferencia/vazoes.py` (`alinhar_com_evt`); `src/analises/hidrologia.py` (faixas, perfis, resumos e `analisar_hidrologia`) |
| `geracao_ons.py` | coleta (descrição); `src/tratamento/geracao.py`; `src/conferencia/geracao.py` (`conferir_geracao`); `src/analises/geracao.py` (`analisar_geracao_oficial`) |
| `cadastro_ons.py` | `src/coleta/cadastro.py` (sincronização, leitura, auditoria e ficha); `src/conferencia/cadastro.py` (divergências com o perfil); `src/analises/cadastro.py` |
| `processor.py` | `src/tratamento/evt.py` |
| `validator.py` | `src/tratamento/validacao.py` |
| `analyzer.py`, parte de análise | `src/analises/`: `resultados.py` (`ResultadosAnalise`, gravação e leitura), `cobertura.py`, `evt.py` (indicadores, eventos, perfis, faixas e mudança de classificação), `constatacoes.py` (`montar_achados` e `_achado_*`), `conclusao.py` (`montar_conclusao` e regras C1 a C11), `etapa.py` (`analisar` e dados das figuras) |
| `analyzer.py`, parte de apresentação | `src/relatorio/`: `figuras.py` (gráficos, só a partir dos resultados), `planilha.py` (`exportar_tabelas`), `markdown.py` (`gerar_relatorio_md`), `conteudo.py` (`linhas_tabela_*`, `textos_tabelas`, `indicadores_capa`, `pares_*`, `legenda_figura` e `notas_*`) |
| `pdf_generator.py` | `src/relatorio/pdf.py` |
| `fontes_relatorio.py` | `src/relatorio/fontes.py` |
| `estrutura_relatorio.py` | `src/relatorio/estrutura.py` |

---

## 7. Cópia de segurança

| Campo | Conteúdo |
|---|---|
| Pasta | `_backup_<AAAA-MM-DD>_<motivo>/` |
| Conteúdo | `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, `usinas/*/perfil.toml`, `README.md`, `requirements.txt` |
| `LEIA-ME.txt` | data, motivo e o que foi copiado |
| `conftest.py` | `collect_ignore_glob = ["*"]` |
| `copia.json` | lista `{arquivo, bytes, sha256}`, conferida depois da cópia |
| Regra | no máximo duas; a mais antiga só sai depois de a nova estar conferida |

---

## 8. Inventário de limpeza (`inventario-limpeza.md`)

| Campo | Conteúdo |
|---|---|
| Item | caminho (arquivo ou pasta) |
| Tamanho | em KB ou MB |
| Uso atual | quem usa (fluxo, testes, specs, constituição, relatório) ou "nenhum" |
| Ação proposta | excluir, mover (com o destino) ou manter |
| Motivo | uma frase |
| Decisão do usuário | aprovado, recusado ou alterado |

---

## 9. Mapeamento das specs (`mapeamento-specs.md`)

| Campo | Conteúdo |
|---|---|
| Origem | spec antiga e item (US, FR ou SC), com o título resumido |
| Situação | em vigor ou superado |
| Destino | spec nova e item novo, ou o motivo de estar superado (ex.: "rodapé com N conjuntos: revisto pela spec 008") |
| Decisão do usuário associada | quando houver, com a data |

---

## 10. Conclusão do relatório (US6, R17)

### Item da conclusão (`res.conclusao`)

| Campo | Conteúdo | Validação |
|---|---|---|
| `lista` | `pontos_atencao`, `possiveis_problemas`, `confirmar_agente` ou `verificar_campo` | uma das quatro |
| `ordem` | posição na lista, na ordem do catálogo | começa em 1 |
| `regra` | `C1` a `C11` | regra do catálogo |
| `texto` | uma frase, com o número que sustenta o item | sem termos de avaliação de desempenho; sem texto de constatação |
| `secoes` | chaves das seções de origem (ex.: `eventos`, `programacao`) | chaves de `estrutura_relatorio.SECOES` presentes |

### Na apresentação

- **PDF e Markdown**:
  - seção "Conclusão" (chave `conclusao`), antes de "Notas metodológicas e limitações";
  - uma frase de abertura e quatro subtítulos com as listas;
  - até cinco itens por lista;
  - cada item termina com "(seção N)" ou "(seções N e M)", com os números das seções presentes.
- **Planilha**: aba `CONCLUSAO`, com as colunas `lista`, `ordem`, `regra`, `texto` e `secoes`. Traz todos os itens gerados, inclusive os que passam do limite, e é coberta pela aba `FONTES`.
- **Notas metodológicas**: um item com as regras e os limiares.

### Regra da conclusão

| Campo | Conteúdo |
|---|---|
| `id` | C1 a C11 (catálogo da spec) |
| `condicao` | função dos resultados que diz se a regra dispara |
| `listas` | listas em que a regra gera item e o modelo de cada frase |
| `secoes` | seções de origem citadas |
| `bases` | bases necessárias; sem elas, a regra não dispara |
