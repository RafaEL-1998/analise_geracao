# Implementation Plan: Análises

**Spec**: [spec.md](spec.md) · **Etapa**: 4 de 5 · **Situação**: implementado · **Atualizado em**: 2026-10-23

## Summary

A etapa lê os dados tratados, os resultados da Conferência, o perfil da usina e os registros da Coleta, e calcula tudo o que o relatório mostra, para qualquer tipo de usina (UHE, PCH, CGH, UTE, UTN, EOL e UFV). O caminho segue a série de referência da usina (D16):
- **hidrelétrica com EVT**: da base de EVT, a cobertura, os indicadores anuais e do período, os eventos, as distribuições, os perfis, o perfil estatístico e os extremos; o cruzamento com as bases complementares do ONS;
- **usina sem EVT**: as seções comuns sobre a base horária comum do Tratamento, com o nível de cada número (D17), e as seções do tipo: térmica (D20), eólica e solar (D21), conjunto de usinas (D22) e afluência sem os cruzamentos com a EVT (D23);
- **nos dois caminhos**: os dados das figuras, as constatações, os itens da conclusão (catálogo C1 a C19 por tipo, D18), as seções e regras omitidas, com o motivo, e os indicadores da carteira (D24).

`src/analises/etapa.executar_analises` escolhe o caminho; `analisar` (com EVT) ou `analisar_sem_evt` monta tudo com pandas num único `ResultadosAnalise`, gravado em `data/usinas/<slug>/analises/resultados.pkl` (pickle com versão de formato, hoje a 3), que a Geração do relatório só formata e desenha. Os valores da usina vêm do perfil ativo; os limiares, de `src/comum/regras.py`.

## Technical Context

**Language/Version**: Python ≥ 3.11 (o `venv` do projeto usa o 3.14.6), com anotações de tipo e PEP 8.

**Primary Dependencies**: `pandas` (tabelas, agrupamentos e séries horárias), `numpy` (máscaras e `np.select` das faixas) e `pyarrow` (leitura do Parquet); `pickle` e `json` da biblioteca padrão. Os tipos novos não trouxeram dependência nova.

**Storage**: arquivos locais. Lê CSV (`;`, UTF-8) e Parquet do Tratamento, `conferencias.pkl` e `nao_aplicaveis.csv` da Conferência, e CSV e o `etapa.json` da Coleta; nada de `data/raw/` (D25). Grava `data/usinas/<slug>/analises/resultados.pkl` (pickle, sem `.bak`) e o `etapa.json`.

**Testing**: pytest, sem rede, com dados sintéticos:
- `tests/analises/` (13 arquivos): base de EVT, indicadores do ONS, programação, disponibilidade, hidrologia (com e sem EVT), seções comuns, térmica, renovável, conjunto, conclusão (C1 a C19), indicadores da carteira e gravação dos resultados;
- `tests/relatorio/test_complementar.py`: bases complementares (hidrologia sem a meta; geração e cadastro só com divergência); `tests/relatorio/test_invariantes_uhe.py`: um teste por invariante da hidrelétrica com EVT;
- `tests/integracao/`: usina fictícia de três unidades no fluxo completo; `test_usinas_ficticias.py`, com uma usina fictícia por tipo de ponta a ponta; `test_sem_raw.py`, com as etapas 2 a 5 sem `data/raw/`; `analises` sem a Conferência (código 5);
- `tests/comum/`: pré-requisito e `etapa.json`, gravação só pela persistência, loggers e nenhum valor de usina real no código (São Domingos e usinas piloto).

**Target Platform**: Windows 11, execução local no `venv` do projeto, PowerShell.

**Project Type**: projeto único, fluxo de linha de comando (`python -m src analises --usina <slug>`).

**Performance Goals**: SC-010 pede a base de EVT em menos de 30 s e o cruzamento com a programação em menos de 2 min. Na São Domingos, a etapa inteira (leitura, análises e gravação) levou 3 s (`iniciada_em` → `concluida_em` do `etapa.json`); na UTE William Arjona, 1 s.

**Constraints**:
- sem acesso ao portal do ONS nem a `data/raw/`; lê só o que as etapas anteriores gravaram;
- não refaz o tratamento nem as conferências: usa as sinalizações e os resultados como estão;
- nenhum nome, identificador ou valor de usina no código: tudo vem do perfil ou dos dados;
- nenhum número do conjunto dividido entre as usinas nem usado na conclusão; regras só com dado da usina;
- `src/analises` nunca importa `src/relatorio`;
- com o perfil e a Coleta congelados de cada usina aprovada, o relatório gerado é idêntico ao de referência (SC-001, SC-012); o caminho da EVT não muda.

**Scale/Scope**:
- **São Domingos** (UHE com EVT):
  - base de EVT: 70.895 registros horários, de 28/08/2018 00h a 28/09/2026 23h; 9 anos civis (2 parciais), 98 meses, 1 hora ausente;
  - bases complementares: 196 meses-unidade de indicadores, 160 de horas por estado, 61 meses de TEIFa/TEIP; 16.992 horas de programação (708 dias com arquivo, 20 sem); 70.895 horas de disponibilidade, 70.760 de hidrologia e 70.895 de geração;
  - saída: `resultados.pkl` com 6,1 MB; 345 eventos de usina parada com EVT, 138 de indisponibilidade total e 68 de desvio da programação; 17 constatações e 19 itens da conclusão.
- **Usinas sem EVT** (referências aprovadas):
  - UTE William Arjona: 46.243 horas da geração da usina, de 10/07/2021 a 18/10/2026, 3 trechos; despacho, CVU de duas unidades de planejamento e CMO; 9 constatações e 7 itens da conclusão;
  - UFV Seriemas 1: 2.832 semi-horas (1.416 horas) da restrição com detalhe da usina, de 22/08 a 19/10/2026; o fator de capacidade, a razão da restrição e a programação do conjunto de 8 usinas;
  - EOL Praia Formosa: 151.598 horas da geração da usina, de 07/2009 a 10/2026, com o fator de capacidade da usina no mesmo período; 88.560 semi-horas da restrição com detalhe, desde 10/2021;
  - PCH Bandeirante: 62.064 horas da geração do conjunto, de 22/08/2019 a 20/10/2026, em 3 trechos de composição; nenhuma regra avaliada com dado da usina.

## Constitution Check

| Princípio / requisito da constituição 3.1.0 | Situação | Como a etapa cumpre |
|---|---|---|
| I. SDD, uma spec por etapa | cumpre | uma spec para todos os tipos, com o que é de um tipo identificado nela; lê só os resultados da Coleta, do Tratamento e da Conferência, sem `data/raw/`; sem a Conferência concluída e atualizada, sai com código 5 sem gravar (`src/pipeline.py`) |
| II. Relatório fiel aos dados | cumpre | textos montados dos resultados, do perfil e das regras gerais; constatações sem parecer (termos proibidos testados); conclusão pelo catálogo C1–C19, com os tipos de cada regra e vocabulário de indício; seção ou regra sem base omitida, com o motivo em `omitidos` |
| III. Uma usina por execução, definida pelo perfil | cumpre | valores da usina lidos de `perfil_ativo()`; o tipo do perfil define o caminho, as seções e as regras; regras gerais em `src/comum/regras.py`, iguais para o mesmo tipo; testes das usinas fictícias e varredura de literais |
| IV. Coleta completa e rastreável | não se aplica | é da Coleta; a cobertura só resume a auditoria da extração e as datas de obtenção |
| V. Tratamento sem descarte | cumpre | registros sinalizados (R6 a R9) ficam nos totais e saem só do perfil estatístico e dos extremos; hidrologia excluída campo a campo; disponibilidade sinalizada (D1 a D4) sai por hora inteira; recurso inválido, estimativa ausente e CVU sinalizado ficam fora só do cálculo que afetam e são contados; nada é corrigido |
| VI. Conferência entre fontes | cumpre | resultados lidos de `conferencias.pkl` e `nao_aplicaveis.csv`, sem refazer; com as vazões abaixo da meta, ou a hora da hidrologia não confirmada, nenhum cruzamento hidrológico |
| VII. Relatório padronizado | não se aplica | é da Geração do relatório; as Análises entregam os dados de cada figura e tabela, com o nível |
| VIII. Granularidade declarada | cumpre | `niveis` e uma linha por nível nas tabelas; constatações com "do conjunto <nome>"; nenhum número do conjunto dividido nem na base da usina (D17, D22); regras só com dado da usina, e as demais em `omitidos` (D18) |
| IX. Relatórios aprovados protegidos | cumpre | caminho da EVT sem mudança (D16); testes dos invariantes da hidrelétrica com EVT; `python -m src comparar --todas` contra as cinco referências |
| RT 1. Python ≥ 3.11, `venv`, dependências mínimas | cumpre | pandas, numpy e pyarrow, já no `requirements.txt` |
| RT 2. Windows e PowerShell | cumpre | caminhos com `pathlib`; exemplos em PowerShell no contrato |
| RT 3. Gravação segura | cumpre | `resultados.pkl` por `gravar_bytes(..., copia=False)`: conferido, troca atômica, restauração em falha, sem `.bak` |
| RT 4 e RT 5. Versões de brutos e cópias do projeto | não se aplica | são da Coleta e da ferramenta `copia-seguranca` |
| RT 6. Pastas | cumpre | `data/usinas/<slug>/analises/` |
| RT 7. Log | cumpre | logger `analises`, no nível da linha de comando; aviso para cada base complementar ausente na hidrelétrica com EVT |
| Testes sem rede e entrega com comparação | cumpre | dados sintéticos e uma usina fictícia por tipo; `python -m src comparar --todas` contra os relatórios de referência |

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
├── etapa.py            # executar_analises (escolhe o caminho), carregar_entradas e analisar (com EVT), carregar_entradas_sem_evt
│                       # e analisar_sem_evt, niveis_da_usina, serie_do_conjunto, datas_da_coleta, ficha_do_cadastro
├── resultados.py       # ResultadosAnalise, VERSAO_FORMATO (3), sem_evt, salvar_resultados, carregar_resultados
├── comum.py            # máscaras (EVT, parada, vertimento mínimo, indisponibilidade), médias, razões, rótulos, _resumo_serie
├── cobertura.py        # analisar_cobertura: período, ausências, anos parciais, agentes, auditoria e resumo do manifesto
├── evt.py              # indicadores, eventos, distribuições, perfis, extremos, sinalizados, figuras 01 e 05
├── indicadores.py      # analisar_indicadores_ons (DISPF ponderado, horas por estado, TEIFa e TEIP), decompor_taxas
├── programacao.py      # classificar_horas, resumo_mensal, eventos_desvio, perfil_hora_do_dia, analisar_programacao
├── disponibilidade.py  # classificar_horas_paradas, resumir_disponibilidade, analisar_disponibilidade
├── hidrologia.py       # faixas de afluência, perfil por hora do dia, resumos, analisar_hidrologia, analisar_hidrologia_sem_evt
├── geracao.py          # analisar_geracao_oficial: resumo da série e totais anuais da conferência
├── cadastro.py         # analisar_cadastro: ficha, divergências e auditoria
├── comum_tipos.py      # seções comuns sobre a base horária comum (analisar_comum), base_programacao_conjunto, agentes_atuais,
│                       # omissoes
├── termica.py          # analisar_termica: geração por motivo, inflexibilidade, atendimento, disponível sem despacho, CVU × CMO;
│                       # achados_termica
├── renovavel.py        # analisar_renovavel: fator de capacidade, energia cortada, recurso × geração, desvios da programação;
│                       # achados_renovavel, omissoes_renovavel
├── conjunto.py         # analisar_conjunto: trechos de composição, composição, geração por trecho, tipo publicado,
│                       # peso_da_usina; em_duas_partes, achados_conjunto, achado_usina_no_conjunto, frases_tipo_publicado
├── carteira.py         # indicadores_carteira, ano_dos_indicadores, contagens_conclusao
├── constatacoes.py     # montar_achados (as 19 constatações com EVT) e montar_achados_comum (sem EVT); do_nivel
└── conclusao.py        # RegraConclusao, CATALOGO_CONCLUSAO (C1 a C19), REGRAS_CONCLUSAO (C1 a C11), montar_conclusao,
                        # regras_do_tipo, regras_omitidas, frase_sem_itens, LISTAS_CONCLUSAO e frases da conclusão
```

Módulos compartilhados:
- `src/comum/`: `regras.py` (limiares e tolerâncias), `perfil.py` (`perfil_ativo()` e valores derivados), `caminhos.py`, `persistencia.py` (`gravar_bytes`, `registrar_gravacoes`), `formatacao.py` e `logger.py`;
- `src/pipeline.py` e `src/__main__.py`: comando, pré-requisito e `etapa.json`;
- só para ler e filtrar:
  - `src/tratamento/`: leitores, `SerieConjunto`, `IndicadoresONS`, `ProgramacaoONS`, colunas de qualidade, `limpos`, `carregar_base_horaria`, `carregar_despacho_tratado`, `carregar_semanal_tratado`, `semanal_em_horas` e os sinais do CVU, `carregar_renovavel`;
  - `src/conferencia/`: `carregar_conferencias`, `janela`, `peso`, `validas`;
  - `src/coleta/`: `registro` (tipos, `tipo_da_usina`, `nivel_coletado`, `normalizar_texto`) e `serie_referencia.escolher`.

```text
tests/analises/
├── test_evt.py                # eventos, cobertura, mudança de classificação (com e sem), indicadores, faixas, extremos
├── test_indicadores.py        # decomposição das taxas, DISPF ponderado, constatações, meses reproduzidos da Conferência
├── test_programacao.py        # cinco classes, resumo mensal, eventos de desvio, perfil por hora, horas sem programação
├── test_disponibilidade.py    # horas paradas (D1 fora, SEM_PROGRAMACAO), resumo mensal com a reserva desligada
├── test_hidrologia.py         # faixas de afluência nos limites, perfil por hora do dia, resumo mensal
├── test_hidrologia_sem_evt.py # afluência sem os cruzamentos com a EVT, com e sem a hora confirmada
├── test_comum_tipos.py        # indicadores anuais por ano e nível, sazonalidade com 12 meses, programação no mesmo nível
├── test_termica.py            # geração por motivo, atendimento, disponível sem despacho, CVU × CMO, usina sem geração
├── test_renovavel.py          # fator de capacidade, energia cortada só nas restritas, recurso válido e limite físico
├── test_conjunto.py           # trechos de composição, potência, tipo publicado, peso da usina, relatório em duas partes
├── test_conclusao.py          # catálogo C1–C19; cada regra dispara e não dispara; omissões; ordem; termos proibidos
├── test_carteira.py           # chaves fixas, ano dos indicadores, vazios, TEIFa de dezembro, contagens vazias
└── test_resultados.py         # gravação e leitura de resultados.pkl, sem .bak; formato diferente recusado
```

## Fluxo de execução

1. `src/__main__.main` carrega o perfil (inválido → código 4) e chama `pipeline.executar_etapa("analises", perfil)`.
2. `etapa_anterior_concluida` lê `conferencia/etapa.json`. Sem `status` `concluida`, ou com outra `versao_formato` (a 2, `pipeline.VERSAO_FORMATO["conferencia"]`), registra a mensagem de pré-requisito e devolve 5, sem gravar nada. A Conferência concluída com código 3 é aceita.
3. O pipeline define o perfil ativo e chama `executar_analises(perfil)`, que escolhe o caminho pela série de referência (`serie_referencia.escolher(perfil)`): `evt` → passos 4 e 5; qualquer outra → passo 6.
4. **Com EVT**: `carregar_entradas(slug)` lê `conferencias.pkl` (`carregar_conferencias`, que recusa outro formato), `evt_tratado.parquet`, `validacao_fisica.csv`, as bases complementares tratadas (`None` quando o arquivo não existe) e, da Coleta, `auditoria_programacao.csv`, `cadastro_ficha.csv`, `auditoria_cadastro.csv`, `dicionarios.csv` e `datas_obtencao.csv` (`datas_da_coleta`). Cada base complementar ausente gera um aviso no log.
5. `analisar(**entradas)` monta o `ResultadosAnalise`:
   1. base de EVT: `preparar_dados` (só se faltar `ano` ou `qualidade_registro`), `analisar_cobertura` (com `auditoria_evt.csv` e a linha da EVT de `datas_obtencao.csv`), indicadores anuais e globais, EVT mensal e por mês do ano, EVT por faixa de geração, perfis horários, eventos, mudança de classificação, sinalizados, extremos, perfil estatístico, validação R1 a R9 e horas com geração zero;
   2. bases complementares, cada uma só se existir e tiver horas: `analisar_indicadores_ons`, `analisar_programacao`, `analisar_disponibilidade` (com as horas classificadas pela programação), `analisar_hidrologia`, `analisar_geracao_oficial`, `analisar_cadastro` e o registro dos dicionários, cada uma com o resultado da sua conferência e a data de obtenção;
   3. `montar_achados` (constatações), depois `montar_conclusao` (itens C1 a C11);
   4. `calcular_serie_diaria` e `calcular_vazoes_anuais` (dados das figuras 01 e 05);
   5. em `executar_analises`, `tipo`, `modalidade` e `indicadores_carteira`.
6. **Sem EVT**: `carregar_entradas_sem_evt(slug, referencia)` lê `base_horaria.csv`, as ausências da série de referência, os indicadores, a programação, a hidrologia, o despacho, o CVU e o CMO e as tabelas de renováveis do Tratamento (`None` quando faltam), `conferencias.pkl` e `nao_aplicaveis.csv` da Conferência e, da Coleta, o resumo do `etapa.json`, `trechos.csv`, `composicao_conjunto.csv`, `capacidade_ficha.csv`, `capacidade_membros.csv`, `tipo_publicado.csv`, `datas_obtencao.csv`, a ficha e a auditoria do cadastro, `auditoria_programacao.csv` e `dicionarios.csv`; com a restrição com detalhe como série de referência, também a Geração por usina do conjunto. `analisar_sem_evt` monta o `ResultadosAnalise`:
   1. `niveis_da_usina`, `analisar_conjunto` (com `serie_do_conjunto`) e, nas hidrelétricas, `analisar_hidrologia_sem_evt`;
   2. `analisar_comum` (seções comuns e omissões), com `base_programacao_conjunto` quando a programação é do conjunto e a base é da usina; as conferências não aplicáveis e `agentes_atuais`;
   3. nas térmicas, `analisar_termica` e os resultados da G3 e da G4; nas eólicas e solares, `analisar_renovavel`, os da G1, da G2 e da G5 e `omissoes_renovavel`;
   4. `analisar_indicadores_ons` sobre as horas da usina na base horária, `analisar_cadastro` e o registro dos dicionários;
   5. `montar_achados_comum`, `montar_conclusao` (regras do tipo), `regras_omitidas` e `indicadores_carteira`.
7. `salvar_resultados` grava `{"versao_formato": 3, "resultados": res}` em `analises/resultados.pkl`, dentro de `registrar_gravacoes`.
8. `executar_analises` devolve `ResultadoEtapa(codigo=0, arquivos, resumo)`. O pipeline grava o `etapa.json` como `concluida`, marca o do relatório como `desatualizada` (se existir) e registra no log o resumo e a pasta.

**Código diferente de 0**: 5 no passo 2; 1 em qualquer exceção dos passos 3 a 7 (entrada ausente ou ilegível, formato de `conferencias.pkl` diferente, falha de gravação) e na interrupção pelo usuário (Ctrl+C), com o `etapa.json` em `falha` e o `resultados.pkl` anterior intacto; 4 (perfil inválido) e 2 (opção inválida), antes da etapa.

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
- **Decisão**: cada `_achado_*` recebe o `ResultadosAnalise` e devolve `(título, texto)` ou `None`, na ordem fixa de `montar_achados` (e, nas usinas sem EVT, de `montar_achados_comum`). `REGRAS_CONCLUSAO` são as funções `_regra_c1` … `_regra_c11` do catálogo (D18), e cada regra devolve 0 ou mais itens. `montar_conclusao` ordena por lista e regra (a C2 na ordem das unidades) e numera `ordem`. Todos os itens ficam nos resultados; o corte em `MAXIMO_ITENS_CONCLUSAO` é do relatório.
- **Motivo**: números sempre iguais aos dos resultados, catálogo reproduzível e igual para qualquer usina.
- **Alternativas rejeitadas**: texto escrito à mão; resumo automático das constatações, que repetiria texto; nota de desempenho, que seria parecer.

### D15 — Sentido das dependências e chamada direta
- **Decisão**: `src/analises` importa `src/comum`, `src/pipeline` e funções de leitura e filtro das etapas anteriores (inclusive o registro dos conjuntos e a escolha da série de referência da Coleta), nunca `src/relatorio`. O relatório importa de `src/analises` o `ResultadosAnalise`, rótulos e códigos (`LISTAS_CONCLUSAO`, `DESCRICAO_CLASSES`, `DESCRICAO_PARCELA`, faixas de afluência), as frases da conclusão, o catálogo da conclusão e `texto_conferencia_geracao`. Numa chamada direta de `analisar` (testes), `preparar_dados` sinaliza R6 a R9 e `validar_regras_fisicas` avalia R1 a R9 quando faltam; na etapa, os dois vêm do Tratamento.
- **Motivo**: o código segue o sentido do fluxo, e os testes usam séries sintéticas.

### D16 — Dois caminhos pela série de referência; base horária comum nas usinas sem EVT
- **Decisão**: `executar_analises` escolhe o caminho pela série de referência do perfil (`serie_referencia.escolher`). Com a EVT, `analisar` roda como antes, e só entram `tipo`, `modalidade` e `indicadores_carteira`; C1 a C11 mantêm a ordem, o texto, os limiares e as listas, sem período mínimo. Sem a EVT, `analisar_sem_evt` parte de `base_horaria.csv` do Tratamento (geração da série de referência com o nível de cada hora, disponibilidade operacional e sincronizada, programação, trecho e sinalizações) e preenche `comum`; os campos da base de EVT ficam vazios. `resultados.sem_evt` (campo `comum` não vazio) diz o caminho às etapas seguintes. Seções sem base vão para `omitidos` (`item`, `tipo` = `secao` ou `regra`, `motivo`).
- **Motivo**: as Análises partiam da base de EVT, que os outros tipos não têm; o caminho da EVT fica intacto, para os relatórios aprovados não mudarem (testes dos invariantes e `comparar --todas`).
- **Alternativas rejeitadas**: simular uma base de EVT com colunas vazias, que esconderia o tipo da usina e arriscaria textos de hidrelétrica em outros tipos; um pacote de análises por tipo, que duplicaria o núcleo.

### D17 — Nível de cada número, sem dividir o conjunto
- **Decisão**: `niveis` guarda o nível (usina ou conjunto) e o identificador da série de referência, da programação, da disponibilidade, do fator de capacidade e da razão da restrição (`niveis_da_usina`). As tabelas por ano, por mês e por hora têm uma linha por nível, e a disponibilidade (sempre da usina) só é comparada com a geração da usina. As constatações escrevem "do conjunto <nome>" (`do_nivel`). Nenhum número do conjunto é dividido entre as usinas nem entra na base horária da usina: na eólica ou solar com a série própria na restrição com detalhe e a programação do conjunto, a comparação com a programação usa a geração do conjunto numa base à parte (`base_programacao_conjunto`), sem a C19.
- **Motivo**: princípio VIII; o identificador já diz o nível.
- **Alternativas rejeitadas**: escrever "nível: usina" em todo número, o que mudaria a hidrelétrica com EVT sem acrescentar informação; misturar na base da usina as horas do conjunto.

### D18 — Catálogo da conclusão por tipo, só com dado da usina
- **Decisão**: `RegraConclusao` declara `codigo`, `tipos`, `listas`, `funcao` (a regra sobre a base de EVT, só C1 a C11), `secoes`, `limiares` (nomes das constantes de `regras.py`), `nivel_exigido` (`usina`), `periodo_minimo_meses`, `funcao_comum` (a regra das usinas sem EVT), `bases_comuns` (as bases da usina de que precisa), `exige_referencias`, `exige_garantia_fisica` e `descricao` (texto da nota). `CATALOGO_CONCLUSAO` tem C1 a C19. Na usina sem EVT, `_avaliar` roda as regras do tipo com alguma das `bases_comuns` no nível da usina, as referências e a garantia física exigidas e o período mínimo; as demais vão para `omitidos` com o motivo (`regras_omitidas`). As regras comuns C2, C5, C8 e C10 usam a base horária comum; as seções citadas passam às chaves do caminho sem EVT (`SECOES_SEM_EVT`). `frase_sem_itens` explica a conclusão vazia; a nota da conclusão das usinas sem EVT sai das `descricao`.
- **Motivo**: princípios II e VIII: regras iguais para o mesmo tipo, indício só com dado da usina; a ordem dos itens continua por lista e número da regra.
- **Alternativas rejeitadas**: avaliar regras com dado do conjunto, que atribuiria à usina números de outras, inclusive de térmicas que saíram do conjunto; prefixos novos por tipo (os códigos R, D e H já são das regras de qualidade); limiares fixados sem as usinas piloto.

### D19 — Período mínimo para a série curta
- **Decisão**: a sazonalidade pede 12 meses distintos (`PERIODO_MINIMO_SAZONALIDADE_MESES`) na série de cada nível; sem eles, é omitida. A C18 declara `periodo_minimo_meses` = 12 (meses distintos da série) e só usa os anos completos. As tabelas por ano aceitam o ano parcial, marcado. C1 a C11 não têm período mínimo.
- **Motivo**: as solares de MS têm série por usina só desde 08/2026; a UFV Seriemas 1 tem cerca de dois meses.
- **Alternativas rejeitadas**: recusar a análise abaixo de 12 meses, o que deixaria de fora quase toda a geração solar de MS.

### D20 — Térmicas e nucleares
- **Decisão**: `analisar_termica` parte do despacho tratado (soma das unidades de planejamento por hora e o detalhe por unidade), da base horária (disponibilidade da usina) e do CVU e do CMO semanais. A geração por motivo usa os totais publicados (`val_proggeracao`, `val_verifgeracao`) como base das parcelas, com os detalhes à parte. O atendimento usa as horas com programação acima de 1 MW e o limiar `LIMIAR_DESVIO_DESPACHO_MW`. O CVU × CMO compara por semana operativa e leva a relação à hora com `semanal_em_horas` para os cruzamentos; o CVU sinalizado (ausente, zero ou negativo) fica sem comparação. A UTN segue o mesmo caminho.
- **Motivo**: os motivos publicados não formam uma partição exata (em cerca de 8 % das horas de 2026 da UTE William Arjona, a ordem de demérito acima da inflexibilidade toma o lugar da ordem de mérito); o CVU zero, publicado em 250 das 267 semanas de uma unidade da William Arjona, respondia sozinho pelas semanas "abaixo do CMO" e por toda a base da C13 (decisão do usuário de 20/10/2026).
- **Alternativas rejeitadas**: CMO semi-horário, porque o CVU é semanal e resoluções diferentes criariam falsos cruzamentos; somar os motivos como total.

### D21 — Eólicas e solares
- **Decisão**: `analisar_renovavel` calcula o fator de capacidade publicado como Σ verificada ÷ Σ capacidade, por mês, por ano e nível; o calculado da série própria fica nos indicadores anuais comuns (só EOL e UFV, no nível da usina). A energia cortada usa `energia_cortada_mwh` do Tratamento, só nas semi-horas com a marca de restrição, com a estimada dessas semi-horas como base do percentual e a diferença bruta à parte; as semi-horas sem estimativa (`sinal_estimada_ausente`) ficam fora dos totais e das médias da estimada. O recurso × geração usa faixas de `FAIXA_VENTO_MS` e `FAIXA_IRRADIANCIA_WM2` até `LIMITE_VENTO_PLAUSIVEL_MS` e `LIMITE_IRRADIANCIA_PLAUSIVEL_WM2`. Os maiores desvios da programação ficam no nível da programação.
- **Motivo**: a diferença entre a estimada e a verificada fora das semi-horas restritas é erro de previsão, não corte; a estimada zero com a usina gerando e o recurso acima do limite físico são falhas de dado.
- **Alternativas rejeitadas**: curva de potência ajustada, que seria um modelo e não um dado; a diferença bruta como energia cortada.

### D22 — Composição e geração do conjunto
- **Decisão**: `analisar_conjunto` junta os trechos consecutivos da Coleta com a mesma composição (trechos de composição); dá a composição de cada trecho, com a potência das unidades da Capacidade de geração em operação em algum momento dele; a geração do conjunto por trecho e por mês; o tipo publicado comparado com os tipos da composição (o tipo vem do CEG); e o peso da usina na potência do conjunto (`peso_da_usina`). Vale para toda usina em conjunto com a geração do conjunto. `em_duas_partes` marca a usina em conjunto sem série própria, para o relatório em duas partes.
- **Motivo**: princípio VIII: a usina em conjunto só tem números do conjunto, que precisam aparecer como tais, com a composição de cada período.
- **Alternativas rejeitadas**: ratear a geração do conjunto pela potência, que viola o princípio VIII; calcular o fator de capacidade do conjunto pela potência somada.

### D23 — Afluência na hidrelétrica sem EVT
- **Decisão**: `analisar_hidrologia_sem_evt` reusa `resumir_hidrologia` (tabelas mensal e anual, com `limpos`), só com a hora confirmada pela conferência do alinhamento da hidrologia pela geração; sem ela, só a cobertura e o resultado da conferência. Sem as faixas de afluência, o perfil por hora do dia nos dias com parada com EVT e as regras C3 e C11.
- **Motivo**: sem a base de EVT, não há a conferência das vazões com ela nem horas com EVT para cruzar; a geração da usina é a referência que resta para conferir a hora.
- **Alternativas rejeitadas**: usar a série sem conferir a hora; omitir a seção em toda hidrelétrica sem EVT.

### D24 — Indicadores da carteira gravados pelas Análises
- **Decisão**: `indicadores_carteira` grava, nos dois caminhos, as chaves fixas com números já calculados para o relatório da usina, no último ano completo da série (sem ele, no parcial mais recente, marcado): o fator de capacidade e a disponibilidade da tabela anual (só no nível da usina), a TEIFa publicada de dezembro (vazia sem dezembro; no ano parcial, a do último mês), a energia cortada da tabela anual da restrição e o atendimento ao despacho (horas dentro de 5 MW da programada ÷ horas com programação, o único cálculo novo). As contagens são de todos os itens de cada lista, com as regras avaliadas e não avaliadas; sem regra avaliada, as contagens ficam vazias. O campo não muda a versão do formato.
- **Motivo**: a carteira só lê resultados gravados, sem refazer cálculo de nenhuma usina (princípio I).
- **Alternativas rejeitadas**: a carteira ler os dados tratados de cada usina, o que refaria cálculos fora das Análises; contar só os itens exibidos.

### D25 — Datas de obtenção lidas da Coleta, sem `data/raw/`
- **Decisão**: as datas de obtenção e o resumo do manifesto da EVT (linha "Versão dos arquivos" da cobertura) vêm de `coleta/datas_obtencao.csv` (`datas_da_coleta`), no campo `datas_obtencao`; nenhuma leitura de `data/raw/`. O formato dos resultados passou a 2 com esse campo.
- **Motivo**: `data/raw/` é compartilhado por todas as usinas; a coleta de outra usina mudaria as datas e a contagem de arquivos do relatório aprovado; o princípio I pede que cada etapa leia só as anteriores.
- **Alternativas rejeitadas**: continuar lendo os manifestos de `data/raw/`.

### Desvios registrados na implementação

| Data | O que mudou | Quem aprovou |
|---|---|---|
| 19/10/2026 | Formato dos resultados: o plano da ampliação previa o formato 2 com os campos novos; o 2 já tinha sido usado pelas datas de obtenção (D25), e os campos novos levaram ao 3. | usuário, na conferência do código das usinas sem EVT ("aprovado, siga") |
| 19/10/2026 | As regras comuns C2, C5, C8 e C10 sobre a base horária comum, previstas com as térmicas, entraram já com as seções comuns, para toda usina sem EVT com a base no nível da usina. | usuário, na mesma aprovação |
| 22 e 23/10/2026 | Os testes dos indicadores da carteira (`tests/analises/test_carteira.py`) foram escritos depois do código, na mesma sessão, fora da ordem de testes antes do código. | registrado na convergência de 23/10/2026; a fase foi aprovada pelo usuário em 23/10/2026 |

## Complexity Tracking

Sem desvios da constituição.
