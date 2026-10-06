# Implementation Plan: Tratamento, Padronização e Validação Física dos Dados - UHE São Domingos

**Branch**: `002-tratamento-dados` | **Date**: 2026-09-30 (revisado em 2026-10-05) | **Spec**: [specs/002-tratamento-dados/spec.md](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/002-tratamento-dados/spec.md)

**Input**: Feature specification from `specs/002-tratamento-dados/spec.md`

**Revisão retroativa (2026-10-05)**: plano atualizado para descrever a implementação existente após a auditoria de 30/09/2026. A versão anterior está em `plan.md.2026-10-05.bak`; as mudanças estão resumidas em "Notas de revisão", ao final.

---

## Summary

O objetivo desta feature é sanar a inconsistência de formatação no Excel (colunas como `val_geracao`, `val_disponibilidade` e `val_produtividade` aparecendo com mistura de tipos "Número" e "Geral/Texto" por causa da diferença entre o ponto decimal do ONS e a vírgula decimal do padrão brasileiro) e auditar todas as grandezas operacionais quanto à consistência interna e à plausibilidade física, com conferência das colunas contra o dicionário oficial `DicionarioDados_EnergiaVertidaTurbinavel.json`.

A abordagem técnica implementada consiste em:
1. Tipar as 10 colunas métricas operacionais (`val_*`) como `float64`, convertendo vírgula decimal e removendo espaços, sem preencher valores ausentes (um dado ausente continua NaN); `cod_usina` como `Int64` (inteiro anulável) e `din_instante` como data/hora, com interrupção se algum instante for inválido (`src/processor.py`, `padronizar_tipagem_numerica`).
2. Validar 100% dos 70.895 registros contra 9 regras (`src/validator.py`, `validar_regras_fisicas`):
   - R1 a R5 (consistência interna das grandezas do ONS): não-negatividade e as identidades de cálculo de energia vertida, vazão vertida, energia vertida turbinável e folga de geração, com tolerância $10^{-4}$;
   - R6 a R9 (plausibilidade física): limites de potência (48 MW + 5%) e de vazão (2 × 81,5 m³/s + 5%), geração acima da disponibilidade (tolerância de 1,0 MW), produtividade fora da faixa de 70% a 130% da nominal teórica e geração com vazão turbinada nula.
3. Sinalizar, sem remover, os registros que violam R6 a R9, com uma coluna booleana por regra (`anomalia_*`) e a coluna-resumo `qualidade_registro` (`src/validator.py`, `sinalizar_anomalias`).
4. Exportar a base tratada (`src/processor.py`):
   - Planilha Excel (`.xlsx`) via `openpyxl`, com células numéricas nativas, aba `UHE_SAO_DOMINGOS` e cabeçalho congelado;
   - Parquet (`.parquet`) via `pyarrow`, com `double` para as métricas e `timestamp` para o instante;
   - CSV (`.csv`) com delimitador `;`, ponto decimal, UTF-8 e precisão integral;
   - Relatórios de validação em Markdown (`relatorio_validacao_fisica.md`) e CSV (`relatorio_validacao_fisica.csv`), com texto derivado dos resultados e números no padrão brasileiro (`src/formatacao.py`).
5. Encerrar com código de saída 3 se R1 for violada; violações de R2 a R9 são registradas sem alterar o código de saída.

O perfil estatístico anual, previsto originalmente nesta feature (User Story 3), foi transferido para a Feature 003 (`src/analyzer.py`).

---

## Technical Context

**Language/Version**: Python 3.10+ (ambiente ativo: Python 3.14.6 no ambiente virtual `.\venv`)

**Primary Dependencies** (mínimo em `requirements.txt`; versão instalada no `venv` em 2026-10-05):
- `pandas>=2.0.0` (3.0.6) - manipulação, tipagem e coerção
- `openpyxl>=3.1.0` (3.1.5) - planilha Excel `.xlsx` com células numéricas nativas
- `pyarrow>=14.0.0` (25.0.1) - arquivo Apache Parquet `.parquet`
- `pytest>=7.0.0` - testes unitários e de integração

**Storage**:
- Entrada: `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv` (70.895 linhas e 20 colunas, consolidadas pela Feature 001)
- Referências: `DicionarioDados_EnergiaVertidaTurbinavel.json` (dicionário oficial, versão 2.0 de 06-06-2024) e parâmetros técnicos da usina em `src/config.py` (fonte: RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3)
- Saídas: `data/processed/` (`.xlsx`, `.parquet`, `.csv` da base tratada e relatórios `.md` e `.csv`)

**Testing**:
- `tests/test_processor.py` (6 testes): tipagem sem preencher ausentes, rejeição de instante inválido, células numéricas no `.xlsx`, schema `double` no `.parquet`, precisão integral no `.csv` e pipeline completo sobre base sintética com 1 registro sinalizado.
- `tests/test_validator.py` (15 casos): dicionário e versão, linha conforme nas 9 regras, contagem de R1 por registro, identidades R2 a R5, R6 a R9, ausentes não violam, sinalização, texto do relatório e estrutura da base real (ignorado se a base consolidada não existir).
- Base sintética: `gerar_df_sintetico` em `tests/conftest.py` (nov/2023 a fev/2024, identidades do ONS respeitadas e 1 registro anômalo).

**Target Platform**: Windows 10/11 com terminal PowerShell.

**Project Type**: CLI de processamento de dados e biblioteca modular Python (`python -m src.processor`), executada separadamente de `python -m src.main` (Feature 001).

**Performance Goals** (metas do plano original; não medidas na revisão de 2026-10-05, que não executou o pipeline):
- Leitura, tipagem e validação dos 70.895 registros em menos de 10 segundos.
- Exportação completa (`.xlsx`, `.parquet`, `.csv`) e relatórios em menos de 25 segundos.

**Constraints**:
- Toda violação apurada é documentada nos relatórios; nenhuma conformidade é presumida.
- Nenhum registro é removido da base tratada; anomalias são sinalizadas.
- Nenhum valor ausente é convertido em zero.
- 100% das células métricas no Excel reconhecidas como números.
- Consumo de memória RAM inferior a 500 MB (meta original; não medida).
- Comandos compatíveis com PowerShell (sem sintaxe Unix).

**Scale/Scope**:
- 70.895 linhas horárias (28/08/2018 00h a 28/09/2026 23h).
- Entrada com 20 colunas: 6 de identificação em texto, `cod_usina`, `din_instante`, 10 métricas contínuas e 2 de rastreabilidade (`arquivo_origem`, `tipo_match`).
- Saída com 25 colunas: as 20 de entrada, 4 booleanas `anomalia_*` e `qualidade_registro`.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio Constitucional | Requisito do Projeto | Status | Avaliação |
| :--- | :--- | :---: | :--- |
| **I. Spec-Driven Development (SDD)** | Especificação aprovada, plano formalizado e rastreável. | **PASS com ressalva** | Os artefatos foram gerados antes da implementação original. As correções da auditoria de 30/09/2026 foram feitas direto no código, sem atualizar a spec antes; a revisão de 2026-10-05 regulariza a documentação (ver Complexity Tracking). |
| **II. Ecossistema Python Exclusivo & Código Limpo** | 100% Python, tipagem explícita, docstrings e PEP 8. | **PASS** | `src/validator.py`, `src/processor.py`, `src/config.py` e `src/formatacao.py` em Python, com type hints e docstrings nas funções públicas principais (algumas auxiliares de `src/formatacao.py` não têm docstring); nenhum script shell. |
| **III. Varredura Exaustiva & Integridade Temporal** | Processar 100% dos registros sem filtros arbitrários. | **PASS** | Os 70.895 registros são validados e exportados; registros anômalos são sinalizados, não descartados. |
| **IV. Filtragem Precisa, Rastreabilidade & Validação Semântica** | Rastreabilidade e validação semântica com dicionário. | **PASS** | `arquivo_origem` e `tipo_match` são preservados (ausência gera aviso); as colunas métricas são conferidas contra o dicionário ONS v2.0. Observação: `tipo_match` vale `CODIGO_E_NOME` (extração da Feature 001 por `cod_usina` e reservatório), e não a chave canônica citada no Princípio IV; a divergência pertence à Feature 001 e à constituição, fora do escopo desta revisão. |
| **V. Idempotência, Resiliência & Observabilidade** | Execuções determinísticas, logging e dados brutos intactos. | **PASS** | As saídas são regeneradas de forma determinística a partir da base consolidada; `data/raw/` não é tocado; log por etapa e por regra, com nível configurável. |
| **Diretrizes de Ambiente (Windows & PowerShell)** | Scripts nativos Windows, PowerShell e criação de `.bak`. | **PASS com ressalva** | Edições de código e de documentação seguem a regra do `.bak`. O processador sobrescreve as saídas em `data/processed/` sem `.bak` e sem releitura de conferência; as saídas são regeneráveis e os testes releem os arquivos exportados (ver Complexity Tracking). |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-tratamento-dados/
├── spec.md                     # Especificação (histórias, requisitos, critérios e histórico de revisões)
├── plan.md                     # Plano de implementação e arquitetura técnica
├── research.md                 # Decisões técnicas e justificativas
├── data-model.md               # Modelo de dados, regras R1 a R9 e sinalização
├── quickstart.md               # Guia de execução e verificação
├── tasks.md                    # Tarefas (originais e revisão pós-auditoria)
├── contracts/
│   └── cli-contract.md         # Contrato da CLI (parâmetros, saídas e códigos de saída)
├── checklists/
│   └── requirements.md         # Checklist de qualidade da especificação
└── *.bak                       # Versões anteriores (*.md.bak de 30/09/2026 e *.md.2026-10-05.bak)
```

### Source Code (repository root)

```text
src/
├── config.py                   # Caminhos, colunas métricas, tolerância, parâmetros da usina e limites R6 a R9
├── formatacao.py               # Números e datas no padrão brasileiro para o relatório
├── validator.py                # Dicionário, carregamento, regras R1 a R9, sinalização e relatórios
└── processor.py                # Tipagem, orquestração, exportação multi-formato e CLI
# Demais módulos (collector, filter, consolidator, main, analyzer, pdf_generator,
# indicadores_ons, programacao_ons) pertencem às Features 001, 003 e 004.

tests/
├── conftest.py                 # gerar_df_sintetico (base horária sintética)
├── test_processor.py           # Tipagem, exportação e pipeline
└── test_validator.py           # Regras R1 a R9, sinalização e relatório

data/
├── raw/                        # 42 CSVs do ONS (2015 a 2026-09) e manifesto - não alterados por esta feature
└── processed/
    ├── uhe_sao_domingos_energia_vertida_consolidado.csv     # entrada (Feature 001)
    ├── uhe_sao_domingos_energia_vertida_tratado.xlsx
    ├── uhe_sao_domingos_energia_vertida_tratado.parquet
    ├── uhe_sao_domingos_energia_vertida_tratado.csv
    ├── relatorio_validacao_fisica.md
    └── relatorio_validacao_fisica.csv
```

**Structure Decision**:
Pacote único Python em `src/`. `validator.py` concentra a lógica das regras e da sinalização (as máscaras de R6 a R9 em `mascaras_plausibilidade` são a fonte única para a validação e para as colunas de anomalia); `processor.py` concentra tipagem, orquestração, exportação e CLI; `config.py` concentra os parâmetros da usina e os limites derivados. A Feature 003 (`src/analyzer.py`) reutiliza `sinalizar_anomalias` e as constantes de `validator.py`.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Princípio I: correções da auditoria de 30/09/2026 implementadas sem atualização prévia da spec | Os erros encontrados (ausentes convertidos em zero, CSV arredondado, ausência de limites físicos, relatório com conclusões fixas, opções da CLI que não podiam ser desligadas) comprometiam os resultados e foram corrigidos de imediato, por prompt. | Manter a spec desatualizada não era aceitável; a revisão retroativa de 2026-10-05 registra cada mudança no histórico da spec e nas tarefas da fase "Revisão pós-auditoria". |
| Diretrizes de Ambiente: saídas em `data/processed/` sobrescritas sem `.bak` e sem releitura de conferência | Comportamento atual de `src/processor.py`, sem decisão registrada. Mitigação: as saídas são derivadas e regeneráveis a partir da base consolidada e do código, e os testes releem os arquivos exportados. | Não alterado nesta revisão (revisão apenas documental). A versão anterior dos relatórios de validação foi preservada manualmente em `reports/_versao_anterior_2026-09-30/data_processed/`, e o código que gera as saídas em `_backup_2026-10-02_relatorio_aprovado/` e `_backup_2026-10-05_antes_spec004/`. Cabe decidir se o processador deve gerar `.bak` das saídas. |

---

## Notas de revisão (2026-10-05)

- **Summary**: a abordagem passou de "5 regras hidrotécnicas" e "comprovação" de conformidade para R1 a R9 em dois grupos, sinalização sem remoção, preservação de ausentes e código de saída 3 apenas para R1; o perfil anual saiu desta feature.
- **Technical Context**: incluídas as versões instaladas, os parâmetros da usina como referência, a contagem de testes e a composição das colunas de saída (25). A restrição original "Zero violações físicas não documentadas; 100% de conformidade com equações de conservação de energia e vazão" foi substituída por "toda violação apurada é documentada; nenhuma conformidade é presumida", porque a conformidade é um resultado da execução, não uma restrição de projeto. As metas de desempenho e de memória foram mantidas, marcadas como não medidas.
- **Constitution Check**: Princípio I e Diretrizes de Ambiente passaram a "PASS com ressalva", com justificativa em Complexity Tracking; o original declarava "Nenhuma violação constitucional detectada".
- **Project Structure**: a árvore original citava `src/scraper.py`, `src/extractor.py`, `tests/test_scraper.py` e `tests/test_extractor.py`, que não existem no projeto; substituída pelos arquivos reais. `relatorio_auditoria_varredura.csv` saiu da lista por ser saída da Feature 001.
