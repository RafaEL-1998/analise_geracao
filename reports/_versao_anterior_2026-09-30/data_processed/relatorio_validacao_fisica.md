# Relatório de Auditoria e Validação Física - UHE São Domingos

**Usina**: UHE São Domingos (Código ONS: 153)
**Submercado / Bacia / Rio**: SE / PARANA / VERDE
**Referência Normativa**: DicionarioDados_EnergiaVertidaTurbinavel.json (Versão 2.0)
**Tolerância Numérica Adotada**: $\epsilon = 0.0001$

---

## 1. Sumário de Conformidade das Regras Físicas e Regulatórias

| Regra | Nome da Regra | Expressão Avaliada | Registros | Conformes | Violações | Taxa Conformidade | Status |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **R1** | Não-Negatividade das Grandezas | `val_x >= 0 para todas as 10 colunas val_*` | 70,895 | 70,895 | 0 | 100.00% | **CONFORME** |
| **R2** | Conservação de Vertimento de Energia | `val_energiavertida >= val_energiavertidaturbinavel` | 70,895 | 70,895 | 0 | 100.00% | **CONFORME** |
| **R3** | Conservação de Vazão Vertida | `val_vazaovertida >= val_vazaovertidaturbinavel + val_vazaovertidanaoturbinavel` | 70,895 | 70,895 | 0 | 100.00% | **CONFORME** |
| **R4** | Equação da Energia Vertida Turbinável | `val_energiavertidaturbinavel = val_vazaovertidaturbinavel * val_produtividade` | 70,895 | 70,895 | 0 | 100.00% | **CONFORME** |
| **R5** | Equação de Folga Operacional de Geração | `val_folgadegeracao = max(0, val_disponibilidade - val_geracao)` | 70,895 | 70,895 | 0 | 100.00% | **CONFORME** |

---

## 2. Parecer Técnico sobre Grandezas Críticas

- **Não-Negatividade (R1)**: Nenhuma das 10 colunas métricas apresenta registros negativos.
- **Energia Vertida Turbinável (R2 & R4)**: Comprovado que $val\_energiavertidaturbinavel \le val\_energiavertida$ e que a equação hidrotécnica $val\_vazaovertidaturbinavel \times val\_produtividade$ é rigorosamente satisfeita.
- **Folga de Geração (R5)**: O valor de folga de geração reflete com exatidão a disponibilidade remanescente não gerada da usina.

---

## 3. Perfilamento Estatístico Anual de Vertimento (2018 a 2026)

| Ano | Horas Totais | Horas c/ Vertimento | Vertimento Turbinável (MWh) | Vertimento Total (MWh) | Vert. Turb. Máx (MWmed) | Geração Média (MWmed) | Produtividade Média |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2018 | 3,023 | 3,023 | 5,444.01 | 11,217.93 | 11.900 | 35.472 | 0.3027 |
| 2019 | 8,760 | 8,760 | 11,454.20 | 94,976.52 | 32.860 | 27.407 | 0.3054 |
| 2020 | 8,784 | 8,783 | 18,967.00 | 36,421.82 | 22.657 | 27.337 | 0.3043 |
| 2021 | 8,760 | 8,760 | 17,701.87 | 22,152.85 | 31.938 | 28.050 | 0.3048 |
| 2022 | 8,760 | 8,760 | 15,403.28 | 42,717.32 | 34.782 | 26.395 | 0.3058 |
| 2023 | 8,760 | 8,754 | 13,078.01 | 22,287.41 | 32.860 | 30.274 | 0.3044 |
| 2024 | 8,784 | 8,776 | 8,940.34 | 18,295.40 | 41.565 | 27.667 | 0.3045 |
| 2025 | 8,760 | 8,758 | 30,689.93 | 41,352.73 | 44.719 | 23.614 | 0.3060 |
| 2026 | 6,504 | 6,499 | 25,972.46 | 28,194.06 | 46.774 | 21.541 | 0.3075 |
