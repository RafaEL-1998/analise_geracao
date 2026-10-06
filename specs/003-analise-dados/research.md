# Research: Análise Estatística, Indicadores Operacionais, Visualização Gráfica e Relatório - UHE São Domingos

Este documento consolida as decisões técnicas e metodológicas das análises estatísticas, dos indicadores, das figuras e dos relatórios da UHE São Domingos.

> **Revisão retroativa (2026-10-05)**: as decisões abaixo descrevem a implementação atual (`src/analyzer.py`, `src/pdf_generator.py`, `src/formatacao.py`, `src/config.py`). As decisões revogadas na auditoria de 30/09/2026 (FID, FIT, decomposição causal do vertimento, classificação Satisfatória/Atenção/Crítica e gráficos com seaborn) estão registradas na seção 10, com o motivo. O texto anterior está em `research.md.2026-10-05.bak`.

---

## 1. Agregação Estatística e Extremos

- **Decisão**: Operações vetorizadas do `pandas` sobre a base tratada (Parquet), agrupando por ano civil as 10 grandezas `val_*` e considerando apenas os registros com `qualidade_registro = "OK"` (sem violação das regras R6 a R9).
- **Métricas computadas** (`calcular_perfil_estatistico_anual`):
  - Registros considerados ($N$).
  - Média ($\mu$) e desvio-padrão amostral ($\sigma$, `ddof=1`).
  - Mediana e percentis 25% e 75%.
  - Soma acumulada anual.
  - Mínimo e máximo com o `din_instante` correspondente, via `idxmin()` e `idxmax()`.
- **Extremos do período** (`mapear_extremos_historicos`): máximo e mínimo de cada grandeza em toda a série, com data e hora, também sem os registros sinalizados.
- **Justificativa**: rastreabilidade temporal dos picos de cheia, vertimento e geração. Os registros sinalizados são dados publicados pelo ONS, por isso continuam nos totais e indicadores, mas não podem definir extremos: a maior geração registrada na série (68,7 MW em 15/05/2019 14h) supera a potência instalada de 48 MW.
- **Alternativas consideradas**:
  - *Calcular apenas média e desvio-padrão global*: rejeitado porque oculta a variação entre anos e não identifica as datas dos picos.
  - *Incluir os registros sinalizados no perfil e nos extremos*: abandonado em 30/09/2026, pelo motivo acima.

---

## 2. Cobertura e Anos Parciais

- **Decisão** (`analisar_cobertura`): comparar os registros com a grade horária contínua entre o primeiro e o último instante para obter horas esperadas, ausentes e duplicadas; um ano é parcial quando o primeiro registro é posterior a 1º/jan 00h ou o último é anterior a 31/dez 23h. A cobertura inclui os agentes (com o período de cada um), a identificação da usina nos dados do ONS e, se existirem, o resumo da auditoria da varredura (`relatorio_auditoria_varredura.csv`) e do manifesto de versões (`_manifesto_ons.json`).
- **Justificativa**: a usina só aparece no conjunto do ONS a partir de 28/08/2018, e a série atual termina em 28/09/2026; a versão anterior afirmava o período 18/05/2018 a 30/09/2026. Anos parciais aparecem nas tabelas com asterisco e ficam fora das comparações entre anos.

---

## 3. Indicadores de Desempenho Operacional

- **Decisão**: indicadores por ano (`calcular_indicadores_anuais`) e para o período completo, ponderados por hora (`calcular_indicadores_globais`), com $P_{inst} = 48,00\text{ MW}$ (2 unidades de 24 MW com turbinas Kaplan de eixo vertical, conforme o RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3) e garantia física $GF = 36,4\text{ MWmed}$ (ANEEL, valor vigente consultado em 02/10/2026):
  1. **Disponibilidade relativa** (indicador aproximado; não é o FID regulatório):
     $$D_{rel} = \frac{\overline{val\_disponibilidade}}{48,00\text{ MW}}$$
  2. **Disponibilidade de referência da garantia física**, com IP = 6,861% e TEIF = 2,333% do cálculo de garantia física registrado no RF 0009/2017-AGEPAN-SFG:
     $$D_{ref} = (1 - IP) \times (1 - TEIF) = 90,97\%$$
     e o desvio $D_{rel} - D_{ref}$ em pontos percentuais.
  3. **Fator de capacidade**:
     $$FC = \frac{\overline{val\_geracao}}{48,00\text{ MW}}$$
  4. **Geração sobre a garantia física**: $\overline{val\_geracao} / 36,4\text{ MWmed}$ (comparação indicativa: não considera perdas até o centro de gravidade, sazonalização nem MRE).
  5. **Índice EVT** (mesma fórmula do antigo IVT):
     $$I_{EVT} = \frac{\sum val\_energiavertidaturbinavel}{\sum val\_geracao + \sum val\_energiavertidaturbinavel}$$
  6. **Parcela da EVT no vertimento mínimo**: EVT das horas com `val_vazaovertida` ≤ 6 m³/s (patamar contínuo da série, da ordem da vazão remanescente de 4,78 m³/s) e EVT das demais horas.
  7. **Condições operativas**: horas com EVT > 0; usina parada com EVT (geração ≤ 1 MW e EVT > 0); indisponibilidade total (disponibilidade ≤ 0,001 MW); disponibilidade acima de zero e até 24 MW; plena carga (geração ≥ 90% de 48 MW = 43,2 MW, só no período completo).
  8. **Janelas horárias**: EVT média e geração média das 9h às 15h (diurna) e das 20h às 5h (noturna), e as razões diurna/noturna; razão de EVT a partir de 2 é destacada no texto.
  9. **Período completo**: também folga média de geração nas horas com EVT, horas em que a EVT ultrapassa a folga, disponibilidade média nas paradas com EVT, horas com geração zero (total e com EVT), EVT nos registros sinalizados e maior geração registrada.
- **Justificativa**: o conjunto de Energia Vertida Turbinável traz a disponibilidade declarada hora a hora, mas não os parâmetros do FID regulatório (razão IDv/ID com TEIP e TEIFa apurados); a comparação com a disponibilidade de referência usada no cálculo da garantia física é a referência objetiva disponível. A EVT é calculada pelo ONS como vazão vertida turbinável × produtividade, limitada pela folga de geração; o conjunto não informa a causa do vertimento nem da redução de geração, por isso os indicadores quantificam as condições (usina parada, plena carga, faixas de geração) sem atribuir causa.
- **Limitação registrada nas notas**: o IP e o TEIF de referência são os de 2017, quando a garantia física era de 36,9 MWmed; a revisão da garantia física pode tê-los alterado.

---

## 4. Eventos de Horas Consecutivas

- **Decisão** (`identificar_eventos`): agrupar horas consecutivas em que uma condição é verdadeira; uma diferença diferente de 1 h entre instantes consecutivos (lacuna) encerra o evento. Aplicado a: usina parada com EVT (`listar_eventos_parada_com_evt`: duração, geração média, disponibilidade média, vazão vertida média, EVT) e indisponibilidade total (`listar_eventos_indisponibilidade_total`: duração, vazão vertida média, geração média).
- **Apresentação**: o relatório lista os eventos de indisponibilidade total com pelo menos 24 h e os 15 maiores eventos de parada por EVT; as listas completas vão para as abas `EVENTOS_INDISP_TOTAL` e `EVENTOS_PARADA_COM_EVT`.
- **Justificativa**: a hora ausente da série (início do horário de verão em 2018) não pode unir dois eventos distintos.

---

## 5. Mudança de Classificação do Vertimento Contínuo

- **Decisão** (`detectar_mudanca_classificacao`): calcular a mediana mensal de `val_vazaovertidanaoturbinavel`; o mês da mudança é o primeiro de uma sequência que vai até o fim da série com mediana positiva, desde que o mês anterior tenha mediana nula. São informados a vazão típica registrada como não turbinável depois da mudança e, antes dela, a vazão turbinável típica, a EVT média e o percentual de horas de vertimento mínimo contadas como turbináveis.
- **Resultado na série atual**: dez/2022; cerca de 5 m³/s do vertimento contínuo passam a ser registrados como não turbináveis.
- **Tratamento**: os dados publicados não são alterados. A EVT é separada em parcela do vertimento mínimo e demais horas (tabela anual e figura 02, com marco no mês detectado), e a constatação correspondente registra que a série de EVT não é homogênea entre os dois períodos.

---

## 6. Distribuições da EVT, Perfil Horário e Horas com Geração Zero

- **EVT mensal** (`calcular_evt_mensal`): por mês da série, com horas, energia gerada, geração e disponibilidade médias, EVT total, EVT do vertimento mínimo e das demais horas.
- **Mês do ano** (`calcular_distribuicao_mes_do_ano`): participação de cada mês na EVT, somando apenas os anos completos; a constatação compara maio a outubro com janeiro a abril e cita os três meses de maior EVT.
- **Faixa de geração** (`calcular_evt_por_faixa_geracao`): horas com EVT classificadas pela geração na mesma hora: até 1 MW (usina parada); 1 a 10; 10 a 20; 20 a 30; 30 a 40; 40 a 43,2; 43,2 MW ou mais (plena carga).
- **Perfil horário** (`calcular_perfil_horario`): média por ano × hora do dia para geração e EVT.
- **Horas com geração zero** (`calcular_horas_geracao_zero`, incluída em 02/10/2026): contagem por ano × mês de horas com `val_geracao` igual a zero; meses sem registros ficam vazios (não zero); totais anuais separados entre disponibilidade zero e usina declarada disponível.
- **Justificativa**: a versão anterior afirmava que o vertimento turbinável ocorria na plena carga e se concentrava no 1º trimestre; essas distribuições permitem verificar as duas afirmações, e os dados as contradizem.

---

## 7. Constatações e Notas Metodológicas Geradas a Partir dos Dados

- **Decisão**: cada constatação é uma função (`_achado_*`) que recebe `ResultadosAnalise` e devolve `(tema, texto)`; `montar_achados` as reúne nesta ordem: cobertura dos dados, disponibilidade, indisponibilidades, geração e garantia física, energia vertida turbinável, EVT e nível de geração, EVT com a usina parada, horas com geração zero, concentração diurna, distribuição ao longo do ano, mudança de classificação do vertimento pelo ONS e qualidade dos dados. As constatações opcionais da spec 004 são intercaladas nas posições definidas naquela spec. Sem os dados opcionais, são 12.
- **Notas metodológicas** (`notas_metodologicas`): definições e limitações sem valores de resultado (fonte e revisões do ONS, horário legal, disponibilidade relativa × FID, origem da garantia física e do IP/TEIF, caráter indicativo da comparação com a garantia física, cálculo da EVT e ausência de causa, limiares, tratamento dos registros sinalizados, anos parciais).
- **Formatação**: `src/formatacao.py` (milhar ".", decimal ",", "–" para ausente, diferenças em p.p. com sinal, datas `dd/mm/aaaa HHh`, meses `mmm/aaaa`, listas "a, b e c", singular/plural).
- **Justificativa**: na versão anterior, o texto do relatório era fixo no código (fator de disponibilidade de 96,1%, "SATISFATÓRIO", "cumpre integralmente", vertimento na plena carga e no 1º trimestre, período 18/05/2018 a 30/09/2026, turbinas "Francis", engolimento de 154 m³/s). Com texto gerado dos dados, uma revisão da base pelo ONS se reflete automaticamente no relatório, e os testes verificam que as afirmações antigas não reaparecem.

---

## 8. Visualização Gráfica com Matplotlib

- **Decisão**: 5 figuras feitas diretamente em `matplotlib` (backend `Agg`), 300 DPI por padrão, gravadas em `reports/figures/` com os nomes de `NOMES_FIGURAS`:
  1. `01_serie_temporal_disponibilidade_geracao_evt.png`: médias diárias de disponibilidade declarada, geração e EVT (área), faixas cinza nos eventos de indisponibilidade total ≥ 24 h, linhas da potência instalada (48 MW) e da garantia física (36,4 MWmed).
  2. `02_evt_mensal.png`: EVT mensal em barras empilhadas (cinza: vertimento mínimo; laranja: demais horas), com linha vertical e anotação no mês da mudança de classificação.
  3. `03_perfil_horario_geracao_evt.png`: dois mapas de calor ano × hora (geração em rampa azul, EVT em rampa laranja).
  4. `04_disponibilidade_geracao_anual.png`: barras por ano de disponibilidade média declarada e fator de capacidade (% da potência), com linhas da disponibilidade de referência (90,97%) e da garantia física em % da potência.
  5. `05_vazoes_defluentes_anuais.png`: barras empilhadas das vazões médias anuais turbinada, vertida turbinável e vertida não turbinável, com linha do engolimento máximo (2 × 81,5 = 163 m³/s).
- **Estilo**: fonte Arial (ou DejaVu Sans), títulos alinhados à esquerda, grade leve, legendas abaixo do gráfico, rótulos das linhas de referência à direita, números no padrão brasileiro, anos parciais com asterisco; cores fixas por grandeza (geração azul, EVT laranja, disponibilidade verde, contexto cinza).
- **Justificativa**: cada figura corresponde a uma ou mais constatações; o seaborn não é necessário para esses tipos de gráfico.

---

## 9. Relatórios, Planilha e Pontos de Extensão

- **Decisão**: um único objeto `ResultadosAnalise` (produzido por `analisar`) alimenta:
  - **PDF** (`PDFReportGenerator.build_pdf`): `reportlab`, A4 paisagem, fontes TrueType (Arial ou DejaVu Sans, para exibir ≤, ≥ e −), cabeçalho com usina e período a partir da 2ª página, rodapé com a fonte, a publicação mais recente no portal (do manifesto) e a data de geração, "Página X de Y", seções numeradas, quadros-resumo na capa e aviso no lugar de figura ausente.
  - **Markdown** (`gerar_relatorio_md`): seções numeradas automaticamente pela função interna `secao()`.
  - **Planilha** (`exportar_tabelas`): 19 abas, uma por tabela, com cabeçalho congelado e largura de coluna ajustada; **CSV** com os indicadores anuais (separador `;`).
  - Tabelas compartilhadas entre Markdown e PDF (`linhas_tabela_anual`, `linhas_tabela_geracao_zero`), para que os dois mostrem os mesmos valores formatados.
- **Pontos de extensão (spec 004)**: `analisar` aceita dados opcionais por parâmetros próprios (o primeiro, `indicadores`, criado em 02/10/2026), guardados em campos opcionais de `ResultadosAnalise` (como `ons`); quando presentes, acrescentam constatações, seções no Markdown e no PDF e abas na planilha. O conteúdo é especificado em `specs/004-conferencia-outros`. Sem esses dados, os campos ficam vazios e o relatório sai com 12 constatações.
- **Justificativa**: a versão anterior montava o PDF lendo a planilha e com textos fixos, e uma falha no PDF era apenas registrada como aviso; agora a falha encerra a execução com código 1.

---

## 10. Decisões Revogadas em 30/09/2026

| Decisão anterior | Motivo da revogação |
| :--- | :--- |
| **Fator de Disponibilidade** $FID = \overline{val\_disponibilidade} / 48$ e **Fator de Indisponibilidade Total** $FIT = 1 - FID$. | O FID regulatório é a razão IDv/ID calculada com TEIP e TEIFa apurados e não pode ser obtido deste conjunto. A mesma razão foi mantida com o nome "disponibilidade relativa", como aproximação. A versão anterior publicava FID de 96,1%; o valor calculado a partir dos dados é 87,8%. |
| **Decomposição causal** do vertimento turbinável em "gargalo de capacidade instalada", "restrição sistêmica de despacho (constrained-off)" e "indisponibilidade eletromecânica", por limiares de geração, folga e disponibilidade. | O conjunto não informa a causa; a classificação dependia de limiares arbitrários. A afirmação de que o vertimento ocorria com a usina a plena carga foi contradita: no relatório de 02/10/2026, 4,6% da EVT ocorreu a partir de 43,2 MW e 28,4% com a usina parada. |
| **Classificação da performance**: Satisfatória (FID ≥ 90%), Atenção (80% ≤ FID < 90%), Crítica (FID < 80%). | Os limiares não tinham base regulatória e dependiam do FID calculado de forma inadequada. |
| **Gráficos com seaborn**: série temporal horária com médias móveis, heatmap mês × hora, dispersão vazão vertida turbinável × EVT com produtividade, boxplots anuais e balanço hídrico em barras. | Substituídos pelas figuras da seção 8. O texto associado ao heatmap afirmava concentração do vertimento turbinável no 1º trimestre; nos anos completos, maio a outubro concentraram 59,4% da EVT e janeiro a abril, 23,0% (relatório de 02/10/2026). |
| Capacidade e turbinas "conforme o modelo do RF xxx/2026-AGEMS-SFT". | O usuário pediu para não citar o modelo de RF de 2026 como fonte; os parâmetros passaram a citar o RF 0009/2017-AGEPAN-SFG. |
