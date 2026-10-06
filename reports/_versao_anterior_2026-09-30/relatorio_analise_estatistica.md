# Relatório Executivo: Análise Estatística e Diagnóstico de Performance - UHE São Domingos

**Usina Hidrelétrica**: UHE São Domingos (Código ONS: 153)
**Capacidade Instalada de Referência**: 48,00 MW (2 Turbinas Francis de ~24 MW)
**Submercado / Bacia / Rio**: Sudeste (SE) / Rio Paraná / Rio Verde
**Período Analisado**: 18/05/2018 a 30/09/2026 (70.895 horas observadas)

---

## 1. Diagnóstico Geral de Performance Operacional

A performance global da UHE São Domingos ao longo do ciclo histórico 2018–2026 é classificada como **SATISFATÓRIA**.

### Principais Destaques do Diagnóstico:
- **Fator de Disponibilidade Médio ($FID$)**: Manteve-se em níveis elevados (média de **96,1%**), superando com folga o padrão de referência regulatório da ANEEL (90,0%). As máquinas estiveram plenamente operacionais durante a quase totalidade do período.
- **Fator de Capacidade Médio ($FC$)**: Média histórica de **56,8%** (com pico anual de 73,9% em 2018 e 63,1% em 2023), compatível com usinas a fio d'água de médio porte na bacia do Alto Paraná.
- **Causa Predominante do Vertimento Turbinável**: O vertimento turbinável registrado na usina ocorre **preponderantemente quando a usina já está operando em sua capacidade plena (próxima a 48 MW)**, decorrente de picos de vazão afluente que excedem a vazão máxima turbinável da usina. Não foram identificadas perdas crônicas por indisponibilidade prolongada de geradores durante os períodos de afluência.

---

## 2. Indicadores Anuais de Performance Energética (2018–2026)

| Ano | Horas | Geração Média (MWmed) | Fator Capacidade ($FC$) | Fator Disponibilidade ($FID$) | Geração (MWh) | Vert. Turbinável (MWh) | Índice Vert. Turb. ($IVT$) | Horas Vert. | Parecer | Causa Predominante |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2018** | 3,023 | 35.47 | 73.9% | 94.3% | 107,233.2 | 5,444.0 | 4.8% | 3,023 | **SATISFATÓRIO** | Restrição de despacho / ordem do ONS (constrained-off) |
| **2019** | 8,760 | 27.41 | 57.1% | 71.4% | 240,085.8 | 11,454.2 | 4.5% | 8,760 | **CRÍTICO** | Indisponibilidade eletromecânica parcial |
| **2020** | 8,784 | 27.34 | 57.0% | 90.9% | 240,130.4 | 18,967.0 | 7.3% | 8,783 | **SATISFATÓRIO** | Restrição de despacho / ordem do ONS (constrained-off) |
| **2021** | 8,760 | 28.05 | 58.4% | 93.8% | 245,719.6 | 17,701.9 | 6.7% | 8,760 | **SATISFATÓRIO** | Restrição de despacho / ordem do ONS (constrained-off) |
| **2022** | 8,760 | 26.39 | 55.0% | 81.8% | 231,220.3 | 15,403.3 | 6.2% | 8,760 | **ATENÇÃO** | Indisponibilidade eletromecânica parcial |
| **2023** | 8,760 | 30.27 | 63.1% | 90.5% | 265,201.5 | 13,078.0 | 4.7% | 8,754 | **SATISFATÓRIO** | Restrição de despacho / ordem do ONS (constrained-off) |
| **2024** | 8,784 | 27.67 | 57.6% | 91.2% | 243,027.6 | 8,940.3 | 3.5% | 8,776 | **SATISFATÓRIO** | Restrição de despacho / ordem do ONS (constrained-off) |
| **2025** | 8,760 | 23.61 | 49.2% | 91.2% | 206,856.9 | 30,689.9 | 12.9% | 8,758 | **SATISFATÓRIO** | Restrição de despacho / ordem do ONS (constrained-off) |
| **2026** | 6,504 | 21.54 | 44.9% | 90.0% | 140,101.8 | 25,972.5 | 15.6% | 6,499 | **ATENÇÃO** | Restrição de despacho / ordem do ONS (constrained-off) |

---

## 3. Mapeamento de Recordes Históricos e Extremos Temporais

Identificação dos valores mínimos e máximos registrados em toda a série horária com timestamp exato:

| Grandeza Operacional | Unidade | Máximo Histórico | Data/Hora do Máximo | Mínimo Histórico | Data/Hora do Mínimo |
| :--- | :---: | :---: | :--- | :---: | :--- |
| `val_geracao` | MWmed | **68.743** | 2019-05-15 14:00:00 | **0.000** | 2018-10-10 15:00:00 |
| `val_disponibilidade` | MWmed | **47.977** | 2020-03-06 14:00:00 | **0.000** | 2018-10-10 15:00:00 |
| `val_vazaoturbinada` | m³/s | **159.000** | 2019-04-24 12:00:00 | **0.000** | 2018-10-10 15:00:00 |
| `val_vazaovertida` | m³/s | **445.000** | 2026-07-16 09:00:00 | **0.000** | 2020-12-17 03:00:00 |
| `val_vazaovertidanaoturbinavel` | m³/s | **104.000** | 2023-05-07 08:00:00 | **0.000** | 2018-08-28 00:00:00 |
| `val_produtividade` | MW/(m³/s) | **3.592** | 2019-03-28 09:00:00 | **0.028** | 2026-09-17 16:00:00 |
| `val_folgadegeracao` | MWmed | **46.782** | 2025-04-20 10:00:00 | **0.000** | 2018-10-10 15:00:00 |
| `val_energiavertida` | MWmed | **427.408** | 2019-03-28 09:00:00 | **0.000** | 2020-12-17 03:00:00 |
| `val_vazaovertidaturbinavel` | m³/s | **152.309** | 2026-07-16 09:00:00 | **0.000** | 2018-10-10 15:00:00 |
| `val_energiavertidaturbinavel` | MWmed | **46.774** | 2026-07-16 09:00:00 | **0.000** | 2018-10-10 15:00:00 |

---

## 4. Catálogo de Gráficos Analíticos Gerados

Todas as figuras em alta resolução (300 DPI) estão salvas no diretório `reports/figures/`:

1. **Série Temporal Multi-Anual**: `reports/figures/01_serie_temporal_geracao_vertimento.png`
   - Traçado contínuo da disponibilidade, geração e área de vertimento turbinável em relação ao teto de 48 MW.
2. **Heatmap de Sazonalidade (Mês x Hora)**: `reports/figures/02_heatmap_sazonalidade_vertimento.png`
   - Matriz Mês x Hora do dia demonstrando a média aritmética horária de todo o período histórico (2018–2026).
3. **Heatmap Interanual (Ano x Mês)**: `reports/figures/02b_heatmap_ano_mes_vertimento.png`
   - Matriz Ano x Mês evidenciando a distribuição interanual e evolução do vertimento mês a mês.
4. **Dispersão e Curva de Produtividade**: `reports/figures/03_dispersao_vazao_energia_produtividade.png`
   - Comprovação visual da relação hidrotécnica linear entre vazão vertida turbinável e energia vertida.
5. **Boxplots Comparativos Anuais**: `reports/figures/04_boxplots_distribuicao_anual.png`
   - Variabilidade, medianas e quartis de geração e vertimento turbinável de 2018 a 2026.
6. **Balanço Hídrico de Vazões**: `reports/figures/05_balanco_hidrico_anual_vazoes.png`
   - Proporção anual de vazão turbinada frente às parcelas de vertimento turbinável e não-turbinável.
