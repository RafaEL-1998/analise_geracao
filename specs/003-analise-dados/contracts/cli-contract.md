# CLI Contract: Módulo de Análise, Figuras e Relatórios

Este documento define a interface de linha de comando (CLI), os parâmetros, as saídas e os códigos de retorno do módulo de análise da UHE São Domingos.

> **Revisão retroativa (2026-10-05)**: contrato conferido com `main()` e `executar_pipeline_analise()` em `src/analyzer.py` e com `main()` em `src/pdf_generator.py`. A versão anterior está em `cli-contract.md.2026-10-05.bak`; as diferenças estão na seção 6.

---

## 1. Comandos de Execução

Comando principal (análise completa):

```powershell
python -m src.analyzer [OPÇÕES]
```

Comando auxiliar, sem opções (recalcula os resultados a partir da base tratada e regenera só o PDF, com as figuras existentes):

```powershell
python -m src.pdf_generator
```

---

## 2. Argumentos de Linha de Comando (`python -m src.analyzer`)

| Flag | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `--input-file` | Caminho | nenhum: usa `data/processed/uhe_sao_domingos_energia_vertida_tratado.parquet` ou, se não existir, o `.xlsx` | Base tratada de entrada (`.parquet`, `.xlsx`/`.xls` ou `.csv` com separador `;`). |
| `--output-dir` | Caminho | `reports` | Pasta do PDF, do Markdown, da planilha e do CSV. |
| `--figures-dir` | Caminho | `reports/figures` | Pasta das figuras PNG. |
| `--dpi` | Inteiro | `300` | Resolução das figuras. |
| `--generate-plots` / `--no-generate-plots` | Booleano | ligado | Gera as 5 figuras; desligado, reaproveita as figuras existentes na pasta. |
| `--generate-report` / `--no-generate-report` | Booleano | ligado | Gera planilha, CSV, Markdown e PDF; desligado, só calcula (e gera as figuras, se ligadas). |
| `--log-level` | Escolha | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 3. Códigos de Retorno (Exit Codes)

| Código | Significado | Descrição |
| :---: | :--- | :--- |
| `0` | **Sucesso** | Análise, figuras e relatórios gerados conforme as opções. |
| `1` | **Erro de Execução / I/O** | Base tratada não encontrada ou qualquer exceção durante a análise, a gravação das figuras, da planilha ou do Markdown, ou a geração do PDF. A exceção é registrada no log. |
| `2` | **Erro de Argumentos** | Parâmetros inválidos (tratados pelo `argparse`). |

---

## 4. Artefatos de Saída Gerados

1. **Relatório em PDF (`reports/relatorio_analise_estatistica.pdf`)**: A4 paisagem; capa com identificação da usina nos dados do ONS, parâmetros técnicos e quadros-resumo; seções numeradas com constatações, fonte e cobertura dos dados, indicadores anuais, figuras com legendas geradas dos dados, eventos, horas com geração zero, qualidade dos dados, notas metodológicas e tabela de parâmetros; cabeçalho, rodapé com fonte e data de geração e "Página X de Y".
2. **Relatório em Markdown (`reports/relatorio_analise_estatistica.md`)**: cabeçalho (período, identificação, agentes, usina) e seções numeradas automaticamente: constatações, indicadores anuais, eventos de indisponibilidade total, maiores eventos de usina parada com EVT, horas com geração zero por mês, EVT por nível de geração, registros sinalizados, extremos, notas metodológicas e lista de figuras.
3. **Planilha (`reports/perfil_estatistico_anual.xlsx`)**: 19 abas, uma por tabela calculada (lista em `data-model.md`, seção 3).
4. **CSV (`reports/perfil_estatistico_anual.csv`)**: indicadores anuais, separador `;`, UTF-8.
5. **Figuras (`reports/figures/`)**:
   - `01_serie_temporal_disponibilidade_geracao_evt.png`
   - `02_evt_mensal.png`
   - `03_perfil_horario_geracao_evt.png`
   - `04_disponibilidade_geracao_anual.png`
   - `05_vazoes_defluentes_anuais.png`

Os arquivos são regravados a cada execução, sem `.bak`.

---

## 5. Comportamentos

- **Dados opcionais da spec 004**: se não existirem, o log registra um aviso e os relatórios saem sem as seções, constatações e abas correspondentes (12 constatações). Se existirem, são incluídos automaticamente; não há opção de linha de comando para desligá-los neste módulo.
- **Arquivos auxiliares da Feature 001**: o resumo da auditoria da varredura e do manifesto de versões entra na seção de cobertura do PDF quando os arquivos existem; na ausência, essas linhas são omitidas.
- **Figura ausente**: o PDF traz um aviso no lugar da figura; o Markdown lista apenas as figuras existentes.
- **Logs**: mensagens do analisador com prefixo `[analyzer]`: início e fim da execução, número de registros carregados, caminhos gravados e exceções com rastreamento (a base não encontrada é registrada em uma linha, sem rastreamento).

---

## 6. Alterações em Relação à Versão Anterior do Contrato

| Item | Antes | Agora | Desde |
| :--- | :--- | :--- | :--- |
| `--input-file` | Padrão documentado: o Parquet; Parquet ou Excel. | Sem padrão explícito (Parquet, depois `.xlsx`); aceita também `.csv`. | 30/09/2026 |
| `--generate-plots`, `--generate-report` | Booleanos sem forma de desligar (padrão ligado). | Pares `--generate-*` / `--no-generate-*`; `--no-generate-plots` reaproveita as figuras existentes. | 30/09/2026 |
| Exit code 1 | Falha de leitura ou gravação; uma falha no PDF era só registrada como aviso. | Qualquer falha, inclusive no PDF. | 30/09/2026 |
| Artefatos | Relatório Markdown com "parecer técnico regulatório anual"; gráficos Seaborn com outros nomes; sem PDF. | PDF e Markdown sem parecer; 5 figuras em matplotlib com os nomes acima; planilha com 19 abas. | 30/09/2026 (aba `HORAS_GERACAO_ZERO_MES` e seção correspondente em 02/10/2026) |
| `python -m src.pdf_generator` | Não documentado. | Documentado como comando auxiliar. | 05/10/2026 |
