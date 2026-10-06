# UHE São Domingos - Coleta, Tratamento e Análise da Energia Vertida Turbinável (ONS)

Pipeline em Python que baixa o conjunto de dados **Energia Vertida Turbinável** do Portal de Dados Abertos do ONS, extrai os registros horários da **UHE São Domingos**, valida sua consistência e plausibilidade física e gera indicadores, gráficos e um relatório em PDF. Desenvolvido sob a metodologia **Spec-Driven Development (SDD)**.

---

## Visão geral

- **Empreendimento**: UHE São Domingos, rio Verde, municípios de Água Clara e Ribas do Rio Pardo (MS). Nos arquivos do ONS: `cod_usina` 153, reservatório `SAO DOMINGOS`, subsistema Sudeste, bacia do Paraná.
- **Características técnicas**: 48 MW, 2 unidades de 24 MW com turbinas Kaplan de eixo vertical e engolimento nominal de 81,5 m³/s por unidade (RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3); garantia física de 36,4 MWmed (ANEEL, valor vigente). Os parâmetros ficam em `src/config.py`, com a fonte indicada.
- **Fonte de dados**: [Portal de Dados Abertos do ONS - Energia Vertida Turbinável](https://dados.ons.org.br/dataset/energia-vertida-turbinavel). O catálogo publica um CSV por ano até 2023 e um por mês a partir de 2024; o ONS revisa arquivos já publicados.
- **Indicadores oficiais por unidade geradora** (ONS, identificados pelo CEG `UHE.PH.MS.028761-0.01`): [DISPF mensal](https://dados.ons.org.br/dataset/ind_disponibilidade_fgeracao_uge_mensal) e [anual](https://dados.ons.org.br/dataset/ind_disponibilidade_fgeracao_uge_anual), [horas por estado operativo](https://dados.ons.org.br/dataset/taxa_teif_teip_parametro) e [TEIFa/TEIP](https://dados.ons.org.br/dataset/taxa_teif_teip), recortados no período da base de EVT. Nenhum conjunto aberto do ONS traz os eventos individuais de desligamento (início, fim e causa).
- **Programação diária do ONS** ([Dados dos Valores da Programação Diária](https://dados.ons.org.br/dataset/programacao_diaria), usina `PRUHSD`, desde 01/10/2024): geração programada em 48 patamares de 30 minutos, cruzada hora a hora com a operação verificada para saber se a usina parada com vertimento seguiu a programação do ONS (spec 004).
- **Bases complementares do ONS** (spec 006), no período da base de EVT e sem baixá-la de novo:
  - [disponibilidade por usina](https://dados.ons.org.br/dataset/disponibilidade_usina) (operacional e sincronizada, id ONS `MSUHSD`);
  - [dados hidrológicos horários](https://dados.ons.org.br/dataset/dados_hidrologicos_ho) (afluência, níveis e volume útil, `cod_usina` 153, reservatório `PNUHSD`);
  - [geração por usina](https://dados.ons.org.br/dataset/geracao-usina-2) (conferência independente da geração);
  - [modalidade das usinas](https://dados.ons.org.br/dataset/modalidade-usina) (ficha cadastral, CEG).
- **Dicionários de dados**: o PDF e o JSON de cada um dos 10 conjuntos são obtidos a cada coleta e guardados em `_dicionarios/`, junto aos dados brutos (constituição 1.2.0).
- **Cobertura**: a usina só aparece no conjunto de dados a partir de 28/08/2018; os arquivos de 2015 a 2017 não a contêm. O período entre o início da operação comercial (2013) e essa data não é coberto por esta fonte.
- **Resultados**: não são repetidos aqui para não ficarem desatualizados. Consulte `reports/relatorio_analise_estatistica.pdf`, gerado a cada execução a partir dos dados.

---

## Estrutura de artefatos

### Dados (`data/`)
- `raw/`: CSVs originais do ONS e `_manifesto_ons.json` (versão de cada arquivo: `last_modified` e tamanho publicados no catálogo). Quando o ONS republica um arquivo com conteúdo diferente, a versão anterior é preservada em `_versoes_anteriores/` (em cada pasta bruta) e registrada no manifesto (`versoes_anteriores`); os leitores não percorrem essa subpasta.
- `processed/uhe_sao_domingos_energia_vertida_consolidado.csv`: registros da usina extraídos de todos os arquivos, com `arquivo_origem`.
- `processed/relatorio_auditoria_varredura.csv`: por arquivo, linhas lidas, registros extraídos, linhas em que só o código ou só o nome do reservatório conferem e linhas com formato irregular (`registros_formato_irregular`).
- `processed/uhe_sao_domingos_energia_vertida_tratado.{parquet,xlsx,csv}`: base tipada (valores ausentes permanecem ausentes) com as colunas de sinalização `anomalia_*` e `qualidade_registro`.
- `processed/relatorio_validacao_fisica.{md,csv}`: resultado das regras R1 a R9.
- `raw/indicadores_ons/<conjunto>/`: CSVs dos quatro conjuntos de indicadores, cada pasta com seu manifesto (fora da varredura da base de EVT).
- `processed/uhe_sao_domingos_ons_*.csv` e `processed/uhe_sao_domingos_indicadores_ons.xlsx`: indicadores por unidade (mensal e anual), horas por estado operativo, TEIFa/TEIP (versão mais recente e recálculo), divergências entre conjuntos e auditoria dos arquivos.
- `raw/programacao_diaria/`: um arquivo Parquet por dia (`PROGRAMACAO_DIARIA_AAAA_MM_DD.parquet`) e manifesto de versões.
- `processed/uhe_sao_domingos_ons_programacao_horaria.csv`, `..._programacao_dias_ausentes.csv` e `relatorio_auditoria_programacao_ons.csv`: programação horária da usina, dias sem arquivo no portal e auditoria por arquivo.
- `raw/disponibilidade_usina/`, `raw/dados_hidrologicos_ho/`, `raw/geracao_usina_2/` e `raw/modalidade_usina/`: arquivos das bases complementares, um por mês (anual na geração até 2021), cada pasta com manifesto e `_versoes_anteriores/`.
- **Formato por mês**: o motor escolhe, para cada mês, o formato publicado. Por exemplo, a disponibilidade só tem Parquet para 01–02/2015 e de 2023 em diante, e os outros meses vêm do CSV.
- `processed/uhe_sao_domingos_ons_{disponibilidade,hidrologia,geracao}_horaria.csv`, `..._ausencias.csv` e `relatorio_auditoria_{disponibilidade,hidrologia,geracao}_ons.csv`: séries horárias da usina (com a coluna `qualidade`), meses e horas ausentes (nunca interpolados) e auditoria por arquivo, inclusive as linhas de formato irregular (contadas e não extraídas).
- `processed/uhe_sao_domingos_ons_hidrologia_alinhamento.csv`: coincidência das vazões turbinada e vertida com a base de EVT depois da conversão da hora de fim para a de início (meta de 99%).
- `processed/uhe_sao_domingos_ons_cadastro.csv` e `relatorio_auditoria_cadastro_ons.csv`: ficha cadastral da usina no ONS e auditoria da leitura do cadastro.
- `raw/**/_dicionarios/` e `processed/relatorio_dicionarios_ons.csv`: dicionários de dados dos 10 conjuntos e registro da última obtenção (NOVO, INALTERADO, ALTERADO, FALHA, NAO_PUBLICADO ou NAO_OBTIDO).
- **`processed/*.bak`**: versão anterior de cada arquivo regravado em `data/processed/`.
  - A gravação passa por `src/persistencia.py`: temporário → conferência → comparação → cópia `.bak` → troca → verificação.
  - Conteúdo idêntico não é regravado e não muda o `.bak`.
  - Em falha, o arquivo volta à versão anterior.

### Relatórios (`reports/`)
- `relatorio_analise_estatistica.pdf`: relatório completo (A4 paisagem) com constatações, indicadores, eventos, qualidade dos dados, notas metodológicas e figuras.
- `relatorio_analise_estatistica.md`: mesmo conteúdo em Markdown.
- **Fonte de cada figura e tabela** (spec 007): logo abaixo de cada uma, no PDF e no Markdown, a linha "Fonte dos dados" (ou "Calculado neste relatório a partir de") cita os conjuntos do ONS usados, com o identificador da usina e a data de obtenção, e as conferências com outra fonte refeitas pelo pipeline, com o resultado; quando não há outra fonte (ex.: EVT), a legenda diz isso. O rodapé do PDF e o cabeçalho do Markdown dizem quantos conjuntos entraram.
- `perfil_estatistico_anual.xlsx`: todas as tabelas calculadas.
  - Base: indicadores anuais e globais, EVT mensal, eventos de parada com EVT, eventos de indisponibilidade, anomalias, extremos, parâmetros.
  - `ONS_*` e `PROG_*`: indicadores oficiais por unidade geradora e cruzamento com a programação diária.
  - `DISP_*`, `HID_*`, `GER_*`, `CAD_FICHA`, `CAD_AUDITORIA` e `DICIONARIOS`: bases complementares.
  - `FONTES` (última aba): conjuntos de origem e conferências de cada aba.
- `perfil_estatistico_anual.csv`: indicadores anuais.
- `figures/`: até 8 figuras (300 DPI, produzidas com seaborn).
  - Sempre: série temporal diária, EVT mensal, perfil horário por ano, disponibilidade e geração anuais, vazões defluentes anuais.
  - Com as bases complementares: 06 disponibilidade operacional × sincronizada × geração; 07 horas com EVT por faixa de afluência; 08 perfil horário de vazões e nível.
- `_versao_anterior_2026-09-30/`: relatórios da versão anterior, preservados apenas para comparação (contêm informações incorretas; ver `LEIA-ME.txt`).

### Cópia de segurança
- `_backup_2026-10-02_relatorio_aprovado/`: código, testes e relatórios da versão aprovada em 02/10/2026, antes dos indicadores oficiais (ver `LEIA-ME.txt`).
- `_backup_2026-10-05_antes_spec004/`: código, testes, specs e relatórios antes da spec 004 e da revisão das specs 001 a 003.
- `_backup_2026-10-05_antes_spec006/`: código, testes, specs, relatórios e `.specify/` antes da spec 006.
- Regra (constituição 1.2.0, Requisito Técnico 3):
  - `.bak` nos arquivos de `data/processed/` e nas alterações em código, testes, specs aprovadas e constituição;
  - relatórios, manifestos, dicionários e rascunhos ficam dispensados.

---

## Instalação

Ambiente recomendado: Windows 10/11 com PowerShell e Python 3.10+.

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Como executar

```powershell
# 1. Coleta e extração: sincroniza os CSVs com o catálogo do ONS, extrai a usina e
#    baixa os indicadores oficiais por unidade geradora no mesmo período
python -m src.main --full-pipeline

#    Só os indicadores oficiais, mantendo a base de EVT existente:
python -m src.main --indicadores-only

#    Só a programação diária do ONS, mantendo a base de EVT existente:
python -m src.main --programacao-only

#    Bases complementares (disponibilidade, hidrologia, geração por usina, cadastro) e seus
#    dicionários, sem tocar a base de EVT (comando recomendado):
python -m src.main --complementares-only

#    Uma base de cada vez: --disponibilidade-only, --hidrologia-only, --geracao-only, --cadastro-only
#    Só os dicionários de dados dos 10 conjuntos:
python -m src.main --dicionarios-only

# 2. Tratamento, validação (R1 a R9) e exportação multi-formato
python -m src.processor

# 3. Análise, figuras, planilha, relatório Markdown e PDF
python -m src.analyzer

# Testes
pytest tests/ -v
```

Opções úteis:
- `--log-level`: vale para todos os módulos do pipeline, em qualquer ponto de entrada.
- `--force-download`: baixa tudo de novo.
- `--filter-only`: só extração.
- `--sem-indicadores`, `--sem-programacao`, `--sem-disponibilidade`, `--sem-hidrologia`, `--sem-geracao`, `--sem-cadastro`: pulam a etapa correspondente.
- `--sem-dicionarios`: uso excepcional.
- `--cod-usina`, `--no-validate-physics`, `--no-generate-plots` (reaproveita as figuras existentes).

Códigos de saída:

| Código | Significado |
|---|---|
| 0 | sucesso |
| 1 | erro, inclusive falha de gravação em `data/processed/`, com o arquivo restaurado |
| 2 | arquivo de dados não obtido ou não lido |
| 3 | alinhamento da hidrologia abaixo de 99% |

Falha ao obter um dicionário não muda o código de saída.

---

## Metodologia resumida

- **Extração**: um registro é extraído quando `cod_usina` = 153 e o nome do reservatório contém `SAO DOMINGOS`. O nome do agente não é usado, porque mudou ao longo da série (CGT ELETROSUL até fev/2026, AXIA SUL depois). Linhas em que só um dos critérios confere são contadas na auditoria.
- **Atualização**: um arquivo local só é reaproveitado se corresponder à versão publicada (`last_modified` registrado no manifesto, ou tamanho igual ao publicado na primeira execução).
- **Validação**: R1 a R5 conferem a consistência interna das grandezas do ONS (não-negatividade e identidades de cálculo); R6 a R9 conferem a plausibilidade física frente aos parâmetros da usina (limites de potência e vazão, geração acima da disponibilidade, faixa de produtividade, geração sem vazão turbinada). Registros que violam R6 a R9 são mantidos nos totais e sinalizados.
- **Indicadores**: disponibilidade média declarada e fator de capacidade (em % da potência instalada), comparação com a disponibilidade de referência da garantia física, (1 − IP) × (1 − TEIF), e com a própria garantia física, EVT anual e mensal, eventos de usina parada com EVT, indisponibilidades e perfil horário.
- **Indicadores oficiais**: DISPF da usina = média das unidades ponderada pela potência e pelas horas da base de EVT; horas por estado operativo conferidas pela identidade HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF; TEIFa = Σ(HDF + HEDF) ÷ Σ(HP − HDP − HEDP) e TEIP = Σ(HDP + HEDP) ÷ ΣHP em janela de 60 meses, que reproduzem as taxas publicadas e permitem decompô-las por unidade e parcela; meses em que o DISPF e as horas do TEIP divergem são listados.
- **Programação diária**: data de cada dia pelo nome do arquivo (a data interna aparece em dois formatos); hora = média dos dois patamares; horas comuns à base de EVT classificadas em usina parada com EVT e programação ≤ 1 MW, parada com EVT e programação > 1 MW, parada sem EVT, gerando com e sem programação; desvio = usina parada com programação > 5 MW (eventos listados). A programação diária não registra reprogramações em tempo real nem o motivo da programação para hidráulicas.
- **Disponibilidade** (spec 006):
  - a operacional é conferida hora a hora com a disponibilidade declarada da base de EVT;
  - as horas paradas são classificadas pela sincronização (alguma unidade sincronizada quando a sincronizada passa de 1 MW), pela EVT e pela classe da programação;
  - a capacidade não sincronizada é comparada mês a mês com as horas em reserva desligada (HRD × potência) dos parâmetros TEIFa/TEIP;
  - qualidade D1 a D4: horas sinalizadas ficam fora das análises.
- **Hidrologia** (spec 006):
  - a hora de fim (a última do dia vem às 23:59) é convertida para a de início;
  - o alinhamento é confirmado pela coincidência das vazões turbinada e vertida (meta de 99%);
  - as horas com EVT são classificadas pela afluência em relação ao engolimento de uma unidade (81,5 m³/s) e da usina (163 m³/s);
  - o perfil por hora do dia separa os dias com parada com EVT dos demais;
  - qualidade H1 a H4: vazão negativa, volume útil fora de 0 a 100%, valor não numérico, nível a mais de 10 m da mediana; o valor é excluído só no campo afetado.
- **Geração por usina**: conferência hora a hora (diferença de até 0,01 MW) e por mês; constatação só se houver divergência.
- **Cadastro**: ficha pelo CEG; id ONS, estado e potência conferidos (as divergências viram constatação); homônimos contados.
- **Limitações**:
  - a disponibilidade declarada e o fator de capacidade são aproximações a partir do conjunto de EVT;
  - o FID não é publicado pelo ONS;
  - os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS;
  - nenhum dos conjuntos informa a causa do vertimento, das reduções de geração ou dos desligamentos.

---

## Histórico

**30/09/2026 - correções após auditoria**:
- Removidos números e conclusões fixos no código (fator de disponibilidade de 96,1%, parecer "SATISFATÓRIO", "cumpre integralmente ANEEL", vertimento atribuído à plena carga e ao 1º trimestre, período 18/05/2018 a 30/09/2026, turbinas "Francis", engolimento de 154 m³/s). Todo o texto dos relatórios passou a ser gerado a partir dos dados.
- Extração por `cod_usina` e deduplicação por usina e horário; cache sensível às revisões do ONS.
- Valores ausentes não são mais convertidos em zero; o CSV tratado mantém precisão integral.
- Limites físicos derivados dos parâmetros da usina passaram a ser aplicados (R6 a R9).
- Mudança de classificação do vertimento contínuo pelo ONS (dez/2022) identificada e tratada nas análises; anos parciais sinalizados.
- Parâmetros de linha de comando que não podiam ser desligados foram corrigidos; falha na geração do PDF deixou de ser ignorada.

**02/10/2026**: garantia física atualizada para 36,4 MWmed (valor vigente na ANEEL; o relatório de 2017 trazia 36,9 MWmed); incluída a contagem mensal de horas com geração zero.

**02/10/2026 - indicadores oficiais do ONS por unidade geradora**: novo módulo `src/indicadores_ons.py` (DISPF, INDISPPF, INDISPFF, horas por estado operativo e TEIFa/TEIP), integrado ao `src.main` (etapa 3) e ao relatório (nova seção e duas constatações). A versão anterior foi preservada em `_backup_2026-10-02_relatorio_aprovado/`.

**05/10/2026 - spec 004 e regularização das specs**: criada a spec `specs/004-conferencia-outros` (spec, plano, pesquisa, modelo de dados, contrato de CLI, roteiro de validação e tarefas), que formaliza os indicadores oficiais e o registro das conferências com outras fontes (feitos em 02/10/2026 sem spec) e inclui a programação diária do ONS no pipeline (`src/programacao_ons.py`, etapa 4 do `src.main`, nova constatação e nova seção do relatório). As specs 001 a 003 foram revisadas para o estado implementado, com `.2026-10-05.bak` e histórico de revisões.

**05/10/2026 - constituição 1.1.0 e spec 005**: a constituição explicita o escopo exclusivo da UHE São Domingos (MS), o identificador da usina em cada conjunto, a preservação de versões anteriores, o nível de log único e o uso de seaborn em qualquer gráfico. A spec `specs/005-conformidade-constituicao` implementa essas regras: versões anteriores em `_versoes_anteriores/`, `--log-level` em todos os módulos, contagem de linhas com formato irregular, `requirements.txt` conferido por teste e as 5 figuras refeitas com seaborn (textos e tabelas do relatório inalterados).

**05/10/2026 - constituição 1.2.0 e spec 006**:
- A constituição passou a listar os identificadores das bases novas, a exigir os dicionários de dados a cada coleta e a restringir o `.bak` aos itens de maior impacto.
- A spec `specs/006-bases-complementares` implementa:
  - gravação com cópia de segurança em `data/processed/` (`src/persistencia.py`);
  - dicionários de dados (`src/dicionarios_ons.py`);
  - motor comum dos conjuntos horários (`src/conjuntos_ons.py`);
  - disponibilidade operacional e sincronizada, hidrologia, geração por usina e cadastro, cada um com seu módulo, a etapa no `src.main` e a seção no relatório.
- Os números das seções que já existiam não mudaram.

**05/10/2026 - convergência da spec 006**: revisão do código contra a spec, o plano e a constituição (`/speckit-converge`), em duas passagens, com 9 ajustes:
- linhas de formato irregular nos CSV das bases novas contadas, avisadas e não extraídas (nenhuma nos arquivos atuais);
- EVT (MWh) por faixa de afluência e por ano no relatório e na aba `HID_FAIXAS_ANUAL`;
- bases novas na relação de fontes do Markdown;
- legenda da hidrologia corrigida (exclusão só no campo afetado);
- data da consulta na identificação do cadastro no PDF;
- auditoria da leitura do cadastro;
- documentação do PDF da disponibilidade e do estado `NAO_OBTIDO` dos dicionários;
- na segunda passagem, a ressalva de que os dados hidrológicos não informam o motivo das paradas, na constatação de afluência.
Cópias anteriores em `_backup_2026-10-05_antes_convergencia006/` e `_backup_2026-10-05_antes_t062/`. Os números das seções existentes não mudaram.

**06/10/2026 - spec 007, fonte explícita em cada figura e tabela**: o rodapé do PDF deixou de citar só o conjunto de EVT. Cada figura e tabela ganhou a legenda de fonte e de conferência, gerada de um mapa único (`src/fontes_relatorio.py`) e dos resultados das conferências; a planilha ganhou a aba `FONTES`. Números, constatações, abas e figuras existentes não mudaram. Cópia anterior em `_backup_2026-10-06_antes_spec007/`.
