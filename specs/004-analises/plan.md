# Implementation Plan: Análises

**Spec**: [spec.md](spec.md) · **Etapa**: 4 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-08

## Summary

A etapa lê os dados tratados, os resultados da Conferência, o perfil da usina e os registros da Coleta, e calcula tudo o que o relatório mostra:
- da base de EVT: cobertura, indicadores anuais e do período, eventos, distribuições, perfis, perfil estatístico e extremos;
- o cruzamento com as bases complementares do ONS;
- os dados das figuras, as constatações e os itens da conclusão (regras C1 a C11).

`src/analises/etapa.analisar` monta tudo com pandas num único `ResultadosAnalise`, gravado em `data/usinas/<slug>/analises/resultados.pkl` (pickle com versão de formato), que a Geração do relatório só formata e desenha. Os valores da usina vêm do perfil ativo; os limiares, de `src/comum/regras.py`.

## Technical Context

**Language/Version**: Python ≥ 3.11 (o `venv` do projeto usa o 3.14), com anotações de tipo e PEP 8.

**Primary Dependencies**: `pandas` (tabelas, agrupamentos e séries horárias), `numpy` (máscaras e `np.select` das faixas) e `pyarrow` (leitura do Parquet); `pickle` e `json` da biblioteca padrão.

**Storage**: arquivos locais. Lê CSV (`;`, UTF-8) e Parquet do Tratamento, `conferencias.pkl` da Conferência, CSV da Coleta e os `_manifesto_ons.json` de `data/raw/`. Grava `data/usinas/<slug>/analises/resultados.pkl` (pickle, sem `.bak`) e o `etapa.json`.

**Testing**: pytest, sem rede, com dados sintéticos:
- `tests/analises/` (7 arquivos, 36 testes): base de EVT, indicadores do ONS, programação, disponibilidade, hidrologia, conclusão e gravação dos resultados;
- `tests/relatorio/test_complementar.py`: bases complementares (hidrologia sem a meta; geração e cadastro só com divergência);
- `tests/integracao/`: usina fictícia de três unidades no fluxo completo; `analises` sem a Conferência (código 5);
- `tests/comum/`: pré-requisito e `etapa.json`, gravação só pela persistência, loggers e nenhum valor da São Domingos no código.

**Target Platform**: Windows 11, execução local no `venv` do projeto, PowerShell.

**Project Type**: projeto único, fluxo de linha de comando (`python -m src analises --usina <slug>`).

**Performance Goals**: SC-010 pede a base de EVT em menos de 30 s e o cruzamento com a programação em menos de 2 min. Na São Domingos, a etapa inteira (leitura, análises e gravação) levou 3 s (`iniciada_em` → `concluida_em` do `etapa.json`).

**Constraints**:
- sem acesso ao portal do ONS; lê só o que as etapas anteriores gravaram;
- não refaz o tratamento nem as conferências: usa as sinalizações e os resultados como estão;
- nenhum nome, identificador ou valor de usina no código: tudo vem do perfil ou dos dados;
- `src/analises` nunca importa `src/relatorio`;
- com o perfil e os dados da São Domingos, o relatório gerado é idêntico ao de referência (SC-001).

**Scale/Scope** (São Domingos):
- base de EVT: 70.895 registros horários, de 28/08/2018 00h a 28/09/2026 23h; 9 anos civis (2 parciais), 98 meses, 1 hora ausente;
- bases complementares: 196 meses-unidade de indicadores, 160 de horas por estado, 61 meses de TEIFa/TEIP; 16.992 horas de programação (708 dias com arquivo, 20 sem); 70.895 horas de disponibilidade, 70.760 de hidrologia e 70.895 de geração;
- saída: `resultados.pkl` com 6,1 MB; 345 eventos de usina parada com EVT, 138 de indisponibilidade total e 68 de desvio da programação; 17 constatações e 19 itens da conclusão.

## Constitution Check

| Princípio / requisito da constituição 2.0.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | lê só os resultados da Coleta, do Tratamento e da Conferência; sem a Conferência concluída e atualizada, sai com código 5 sem gravar (`src/pipeline.py`) |
| II. Relatório fiel aos dados | cumpre | textos montados dos resultados, do perfil e das regras gerais; constatações sem parecer (termos proibidos testados); conclusão pelo catálogo C1–C11, com vocabulário de indício; análises de base ausente omitidas |
| III. Uma usina por execução, definida pelo perfil | cumpre | valores da usina lidos de `perfil_ativo()`; regras gerais em `src/comum/regras.py`; teste da usina fictícia e varredura de literais |
| IV. Coleta completa e rastreável | não se aplica | é da Coleta; a cobertura só resume a auditoria da extração e o manifesto |
| V. Tratamento sem descarte | cumpre | registros sinalizados (R6 a R9) ficam nos totais e saem só do perfil estatístico e dos extremos; hidrologia excluída campo a campo; disponibilidade sinalizada (D1 a D4) sai por hora inteira; nada é corrigido |
| VI. Conferência entre fontes | cumpre | resultados lidos de `conferencias.pkl`, sem refazer; com as vazões abaixo da meta, nenhum cruzamento hidrológico |
| VII. Relatório padronizado | não se aplica | é da Geração do relatório; as Análises entregam os dados de cada figura e tabela |
| RT 1. Python ≥ 3.11, `venv`, dependências mínimas | cumpre | pandas, numpy e pyarrow, já no `requirements.txt` |
| RT 2. Windows e PowerShell | cumpre | caminhos com `pathlib`; exemplos em PowerShell no contrato |
| RT 3. Gravação segura | cumpre | `resultados.pkl` por `gravar_bytes(..., copia=False)`: conferido, troca atômica, restauração em falha, sem `.bak` |
| RT 4 e RT 5. Versões de brutos e cópias do projeto | não se aplica | são da Coleta e da ferramenta `copia-seguranca` |
| RT 6. Pastas | cumpre | `data/usinas/<slug>/analises/` |
| RT 7. Log | cumpre | logger `analises`, no nível da linha de comando; aviso para cada base complementar ausente |
| Testes sem rede e entrega com comparação | cumpre | dados sintéticos e usina fictícia; `python -m src comparar` contra o relatório de referência |

## Project Structure

### Documentation (this feature)

```text
specs/004-analises/
├── spec.md                 # requisitos aprovados
├── plan.md                 # este arquivo
├── data-model.md           # entradas, resultados.pkl, etapa.json e regras
├── contracts/
│   └── cli-analises.md     # comando da etapa e códigos de saída
└── checklists/
    └── requirements.md     # qualidade da spec
```

### Source Code (repository root)

```text
src/analises/
├── __init__.py
├── etapa.py            # executar_analises (função da etapa), carregar_entradas, ficha_do_cadastro, analisar
├── resultados.py       # ResultadosAnalise, VERSAO_FORMATO, salvar_resultados, carregar_resultados
├── comum.py            # máscaras (EVT, parada, vertimento mínimo, indisponibilidade), médias, razões, rótulos
├── cobertura.py        # analisar_cobertura: período, ausências, anos parciais, agentes, auditoria e manifesto
├── evt.py              # indicadores, eventos, distribuições, perfis, extremos, sinalizados, figuras 01 e 05
├── indicadores.py      # analisar_indicadores_ons (DISPF ponderado, horas por estado, TEIFa e TEIP), decompor_taxas
├── programacao.py      # classificar_horas, resumo_mensal, eventos_desvio, perfil_hora_do_dia, analisar_programacao
├── disponibilidade.py  # classificar_horas_paradas, resumir_disponibilidade, analisar_disponibilidade
├── hidrologia.py       # faixas de afluência, perfil por hora do dia, resumos, analisar_hidrologia
├── geracao.py          # analisar_geracao_oficial: resumo da série e totais anuais da conferência
├── cadastro.py         # analisar_cadastro: ficha, divergências e auditoria
├── constatacoes.py     # montar_achados e as 19 constatações (_achado_*)
└── conclusao.py        # montar_conclusao, _regra_c1 a _regra_c11, LISTAS_CONCLUSAO e frases da conclusão
```

Módulos compartilhados:
- `src/comum/`: `regras.py` (limiares e tolerâncias), `perfil.py` (`perfil_ativo()` e valores derivados), `caminhos.py`, `persistencia.py` (`gravar_bytes`, `registrar_gravacoes`), `formatacao.py` e `logger.py`;
- `src/pipeline.py` e `src/__main__.py`: comando, pré-requisito e `etapa.json`;
- só para ler e filtrar: `src/tratamento/` (leitores, `SerieConjunto`, `IndicadoresONS`, `ProgramacaoONS`, colunas de qualidade, `limpos`), `src/conferencia/` (`carregar_conferencias`, `janela`, `peso`, `validas`) e `src/coleta/conjuntos.data_obtencao`.

```text
tests/analises/
├── test_evt.py              # eventos, cobertura, mudança de classificação (com e sem), indicadores, faixas, extremos
├── test_indicadores.py      # decomposição das taxas, DISPF ponderado, constatações, meses reproduzidos da Conferência
├── test_programacao.py      # cinco classes, resumo mensal, eventos de desvio, perfil por hora, horas sem programação
├── test_disponibilidade.py  # horas paradas (D1 fora, SEM_PROGRAMACAO), resumo mensal com a reserva desligada
├── test_hidrologia.py       # faixas de afluência nos limites, perfil por hora do dia, resumo mensal
├── test_conclusao.py        # cada regra C1–C11 dispara e não dispara; ordem; termos proibidos; sem repetir constatação
└── test_resultados.py       # gravação e leitura de resultados.pkl, sem .bak; formato diferente recusado
```

## Fluxo de execução

1. `src/__main__.main` carrega o perfil (inválido → código 4) e chama `pipeline.executar_etapa("analises", perfil)`.
2. `etapa_anterior_concluida` lê `conferencia/etapa.json`. Sem `status` `concluida`, ou com outra `versao_formato`, registra a mensagem de pré-requisito e devolve 5, sem gravar nada. A Conferência concluída com código 3 é aceita.
3. O pipeline define o perfil ativo e chama `executar_analises(perfil)`.
4. `carregar_entradas(slug)` lê `conferencias.pkl` (`carregar_conferencias`, que recusa outro formato), `evt_tratado.parquet`, `validacao_fisica.csv`, as bases complementares tratadas (`None` quando o arquivo não existe) e, da Coleta, `auditoria_programacao.csv`, `cadastro_ficha.csv`, `auditoria_cadastro.csv` e `dicionarios.csv`. Cada base complementar ausente gera um aviso no log.
5. `analisar(**entradas)` monta o `ResultadosAnalise`:
   1. base de EVT: `preparar_dados` (só se faltar `ano` ou `qualidade_registro`), `analisar_cobertura` (com `auditoria_evt.csv` e `data/raw/_manifesto_ons.json`), indicadores anuais e globais, EVT mensal e por mês do ano, EVT por faixa de geração, perfis horários, eventos, mudança de classificação, sinalizados, extremos, perfil estatístico, validação R1 a R9 e horas com geração zero;
   2. bases complementares, cada uma só se existir e tiver horas: `analisar_indicadores_ons`, `analisar_programacao`, `analisar_disponibilidade` (com as horas classificadas pela programação), `analisar_hidrologia`, `analisar_geracao_oficial`, `analisar_cadastro` e o registro dos dicionários, cada uma com o resultado da sua conferência;
   3. `montar_achados` (constatações), depois `montar_conclusao` (itens C1 a C11);
   4. `calcular_serie_diaria` e `calcular_vazoes_anuais` (dados das figuras 01 e 05).
6. `salvar_resultados` grava `{"versao_formato": 1, "resultados": res}` em `analises/resultados.pkl`, dentro de `registrar_gravacoes`.
7. `executar_analises` devolve `ResultadoEtapa(codigo=0, arquivos, resumo)`. O pipeline grava o `etapa.json` como `concluida`, marca o do relatório como `desatualizada` (se existir) e registra no log o resumo e a pasta.

**Código diferente de 0**: 5 no passo 2; 1 em qualquer exceção dos passos 4 a 6 (entrada ausente ou ilegível, formato de `conferencias.pkl` diferente, falha de gravação) e na interrupção pelo usuário (Ctrl+C), com o `etapa.json` em `falha` e o `resultados.pkl` anterior intacto; 4 (perfil inválido) e 2 (opção inválida), antes da etapa.

## Decisões técnicas

### D1 — Um objeto de resultados, em pickle com versão de formato
- **Decisão**: o dataclass `ResultadosAnalise` reúne tudo o que o relatório mostra. `salvar_resultados` grava `{"versao_formato": VERSAO_FORMATO, "resultados": res}` com `gravar_bytes(copia=False)`; `carregar_resultados` recusa outra versão.
- **Motivo**: preserva os tipos (datas, `Period`, inteiros com vazio) e é o mesmo objeto que o relatório usaria em memória, o que mantém o relatório idêntico. A planilha do relatório é a versão legível.
- **Alternativas rejeitadas**: JSON ou Parquet campo a campo (muito código e risco de mudar tipos); recalcular no relatório.

### D2 — Registros sinalizados nos totais, fora do perfil estatístico e dos extremos
- **Decisão**: indicadores, totais, eventos e distribuições usam todos os registros. O perfil estatístico e os extremos usam só `qualidade_registro == "OK"` e valores não vazios.
- **Motivo**: são dados publicados pelo ONS, mas não podem definir extremos (na São Domingos, os 68,7 MW de 15/05/2019 14h superam os 48 MW instalados).

### D3 — Cobertura pela grade horária e eventos por horas consecutivas
- **Decisão**: horas esperadas = grade horária contínua entre o primeiro e o último registro; ano parcial quando começa depois de 1º de janeiro 00h ou termina antes de 31 de dezembro 23h; médias e somas com as horas reais. `identificar_eventos` agrupa as horas em que a condição vale, e um intervalo diferente de 1 h encerra o evento (`eventos_desvio` faz o mesmo nas horas com programação). As listas completas ficam nos resultados; a seleção (≥ 24 h, maiores eventos) é do relatório.
- **Motivo**: nada é extrapolado nem interpolado, e uma hora ausente não une dois eventos.

### D4 — Limiares gerais, iguais para qualquer usina
- **Decisão**: usina parada e programação zero ≤ 1 MW; indisponibilidade total ≤ 0,001 MW; plena carga ≥ 90 % da potência; desvio > 5 MW; sincronizada > 1 MW; janelas diurna e noturna; razão diurna ≥ 2; janela de 60 meses. Ficam em `src/comum/regras.py`, e alguns no módulo que os usa ([data-model](data-model.md), seção 5).
- **Motivo**: o limiar de 1 MW evita valores residuais; o de 5 MW separa desvio operacional de arredondamento e rampa.
- **Alternativas rejeitadas**: comparação estrita com zero.

### D5 — Disponibilidade relativa, sem classificação de desempenho
- **Decisão**: disponibilidade declarada média ÷ potência instalada ("disponibilidade relativa"), comparada com (1 − IP) × (1 − TEIF) do perfil. Geração média ÷ garantia física é uma comparação indicativa.
- **Motivo**: o conjunto de EVT não traz os parâmetros do FID regulatório; a referência da garantia física é a disponível.
- **Alternativas rejeitadas**: FID e FIT calculados deste conjunto; faixas de desempenho; decomposição do vertimento em causas por limiares.

### D6 — EVT do vertimento mínimo e mudança de classificação
- **Decisão**: a EVT é separada nas horas com `val_vazaovertida` ≤ `analises.vertimento_minimo_m3s`. `detectar_mudanca_classificacao` usa a mediana mensal de `val_vazaovertidanaoturbinavel`: o mês detectado é o seguinte ao último mês com mediana não positiva. Os valores típicos são medianas nas horas de vertimento mínimo. Sem mês detectado, a constatação da mudança não é gerada. Os dados não são alterados.
- **Motivo**: uma reclassificação pelo ONS torna a série de EVT não homogênea (na São Domingos, em dez/2022, cerca de 5 m³/s).

### D7 — Faixas derivadas do perfil
- **Decisão**: faixas de geração: até 1 MW, os intervalos de `analises.faixas_geracao_mw`, até a plena carga e plena carga ou mais (`np.select`); faixa vazia fica com 0 h. Faixas de afluência: `ATE_UMA_UNIDADE`, `ENTRE_UMA_E_<N por extenso>_UNIDADES` e `ACIMA_ENGOLIMENTO_USINA`, pelo engolimento por unidade e por N × engolimento, mais `SEM_DADO_HIDROLOGICO`.
- **Motivo**: mesmas análises para qualquer usina; na São Domingos, a chave continua `ENTRE_UMA_E_DUAS_UNIDADES`.
- **Alternativas rejeitadas**: faixas pela disponibilidade horária, que misturaria duas fontes numa classe.

### D8 — DISPF da usina ponderado por potência e horas da base de EVT
- **Decisão**: peso de cada mês-unidade = horas da base de EVT no mês × potência publicada (ou `parametros.potencia_unitaria_mw`), só nos meses presentes na base de EVT.
- **Motivo**: unidades de potências diferentes e meses parciais pesam o que pesam na base.

### D9 — TEIFa e TEIP: valor publicado, recálculo lido e decomposição
- **Decisão**: `taxa_ultima` é o mês mais recente publicado. O recálculo e a contagem dos meses reproduzidos (`comparados` e `coincidentes` da conferência `teifa_teip`) vêm prontos da Conferência e ficam em `recalculo_resumo`; a constatação diz "nos N meses" quando todos são reproduzidos e "em X dos N meses" quando não. Numa chamada direta, a contagem sai de `reproducao_das_taxas`, a mesma regra da Conferência. `decompor_taxas` reusa `janela` e `peso` da Conferência (peso 1 sem potência) e só roda quando o mês mais recente tem recálculo, isto é, janela de 60 meses completa.
- **Motivo**: as Análises não refazem conferências; a decomposição mostra a unidade e a parcela que pesam na taxa.

### D10 — Programação: cinco classes e horas sem programação à parte
- **Decisão**: junção interna da base de EVT com a programação horária não vazia; classes pelo limiar de 1 MW; desvio = usina parada com programação > 5 MW. As horas da base no período da programação sem valor programado são contadas à parte, sem interpolação.
- **Motivo**: a programação de usinas hidráulicas não traz o motivo nem as reprogramações em tempo real; os textos dizem só se a parada seguiu a programação.

### D11 — Disponibilidade sincronizada e reserva desligada
- **Decisão**: `validas` tira a hora inteira com D1 a D4. A capacidade não sincronizada (operacional − sincronizada, em MWh) é comparada com Σ(HRD × potência) das horas por estado, por mês e por ano; a diferença é publicada sem meta e fica vazia sem horas por estado.
- **Motivo**: são duas apurações diferentes; a diferença é indício, não divergência de conferência.

### D12 — Hidrologia: cruzamentos só com a meta, exclusão campo a campo
- **Decisão**: `publicado` = `confirmado` do alinhamento da conferência das vazões; sem ele, ficam só o resumo da série, o alinhamento, a auditoria e as ausências. `limpos` apaga só o campo afetado por H1, H2 ou H4.
- **Motivo**: são dados dos agentes, não consistidos pelo ONS; com as vazões desalinhadas, o cruzamento hora a hora não vale.
- **Alternativas rejeitadas**: excluir a hora inteira, o que perderia campos válidos da mesma hora.

### D13 — Conferências lidas como estão, junto da base
- **Decisão**: as tabelas de cada conferência aplicável vão no dicionário da base correspondente, e a contagem dos meses reproduzidos da TEIFa e da TEIP vai em `recalculo_resumo`. As Análises só somam por ano a tabela mensal da geração. Conferência de base ausente não entra nos resultados.
- **Motivo**: o relatório cita as conferências sem refazê-las.

### D14 — Constatações e conclusão como funções dos resultados
- **Decisão**: cada `_achado_*` recebe o `ResultadosAnalise` e devolve `(título, texto)` ou `None`, na ordem fixa de `montar_achados`. `REGRAS_CONCLUSAO` é a tupla `_regra_c1` … `_regra_c11`, e cada regra devolve 0 ou mais itens. `montar_conclusao` ordena por lista e regra (a C2 na ordem das unidades) e numera `ordem`. Todos os itens ficam nos resultados; o corte em `MAXIMO_ITENS_CONCLUSAO` é do relatório.
- **Motivo**: números sempre iguais aos dos resultados, catálogo reproduzível e igual para qualquer usina.
- **Alternativas rejeitadas**: texto escrito à mão; resumo automático das constatações, que repetiria texto; nota de desempenho, que seria parecer.

### D15 — Sentido das dependências e chamada direta
- **Decisão**: `src/analises` importa `src/comum`, `src/pipeline` e funções de leitura e filtro das etapas anteriores, nunca `src/relatorio`. O relatório importa de `src/analises` o `ResultadosAnalise`, rótulos e códigos (`LISTAS_CONCLUSAO`, `DESCRICAO_CLASSES`, `DESCRICAO_PARCELA`, faixas de afluência), as frases da conclusão e `texto_conferencia_geracao`. Numa chamada direta de `analisar` (testes), `preparar_dados` sinaliza R6 a R9 e `validar_regras_fisicas` avalia R1 a R9 quando faltam; na etapa, os dois vêm do Tratamento.
- **Motivo**: o código segue o sentido do fluxo, e os testes usam séries sintéticas.

## Complexity Tracking

Sem desvios da constituição.
