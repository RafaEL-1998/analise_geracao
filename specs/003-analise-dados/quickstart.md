# Quickstart: Execução e Validação da Análise, das Figuras e dos Relatórios - UHE São Domingos

Este guia traz os passos reprodutíveis para gerar os indicadores, as constatações, as figuras, a planilha e os relatórios em PDF e Markdown da UHE São Domingos, e para conferir o resultado.

> **Revisão retroativa (2026-10-05)**: comandos e saídas conferidos com `src/analyzer.py`, `src/pdf_generator.py` e o README. A versão anterior deste guia (nomes de figuras antigos, sem PDF) está em `quickstart.md.2026-10-05.bak`.

---

## 1. Pré-requisitos e Ambiente

- **Sistema Operacional**: Windows com PowerShell.
- **Python**: versão 3.10+ (ambiente virtual em `.\venv`, hoje com Python 3.14.6).
- **Dependências usadas pela análise** (todas no `requirements.txt`, exceto o `numpy`, que vem com o `pandas`):
  - `pandas>=2.0.0` e `numpy`
  - `pyarrow>=14.0.0`
  - `openpyxl>=3.1.0`
  - `matplotlib>=3.8.0`
  - `reportlab>=4.0.0`
  - `pytest>=7.0.0`
  - O `requirements.txt` ainda lista `seaborn>=0.13.0`, que não é mais usado.
- **Base de entrada**:
  - `data/processed/uhe_sao_domingos_energia_vertida_tratado.parquet` (gerada na Feature 002; na versão atual, 70.895 registros de 28/08/2018 00h a 28/09/2026 23h).
  - Opcionais: `data/processed/relatorio_auditoria_varredura.csv` e `data/raw/_manifesto_ons.json` (Feature 001), usados na seção de cobertura do PDF; e os dados processados da spec 004, que acrescentam seções opcionais ao relatório.

---

## 2. Preparação do Ambiente

No terminal PowerShell, na raiz do projeto:

```powershell
# Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar as dependências
pip install -r requirements.txt
```

O analisador regrava `reports/` e `reports/figures/` sem criar `.bak`. Antes de regenerar uma versão já aprovada, copie esses arquivos para uma pasta datada (como `_backup_2026-10-02_relatorio_aprovado/`).

---

## 3. Cenários de Execução

### Cenário 1: Execução Completa

Lê a base tratada, calcula indicadores, eventos, distribuições, perfil estatístico e extremos, monta as constatações e gera figuras, planilha, CSV, Markdown e PDF:

```powershell
python -m src.analyzer
```

Equivale a `python -m src.analyzer --input-file data/processed/uhe_sao_domingos_energia_vertida_tratado.parquet --output-dir reports --figures-dir reports/figures --dpi 300 --generate-plots --generate-report`.

**Resultados Esperados**:
1. O comando termina com código de saída `0` e o log registra `=== PIPELINE ANALÍTICO CONCLUÍDO COM SUCESSO! ===`.
2. Se os dados opcionais da spec 004 não existirem, o log traz um aviso e o relatório sai sem as seções correspondentes, com 12 constatações.
3. Arquivos gerados em `reports/`:
   - `relatorio_analise_estatistica.pdf`: relatório A4 paisagem com capa, constatações, cobertura, indicadores, figuras, eventos, qualidade dos dados, notas metodológicas e parâmetros.
   - `relatorio_analise_estatistica.md`: mesmo conteúdo em Markdown, com seções numeradas.
   - `perfil_estatistico_anual.xlsx`: 19 abas com todas as tabelas calculadas (mais as abas da spec 004, se houver esses dados).
   - `perfil_estatistico_anual.csv`: indicadores anuais (separador `;`).
4. Figuras em `reports/figures/` (300 DPI):
   - `01_serie_temporal_disponibilidade_geracao_evt.png`
   - `02_evt_mensal.png`
   - `03_perfil_horario_geracao_evt.png`
   - `04_disponibilidade_geracao_anual.png`
   - `05_vazoes_defluentes_anuais.png`

---

### Cenário 2: Regenerar os Relatórios Reaproveitando as Figuras

```powershell
python -m src.analyzer --no-generate-plots
```

Usa as figuras já existentes em `reports/figures/`; as ausentes aparecem no PDF como aviso. Para gerar só as figuras, sem planilha nem relatórios: `python -m src.analyzer --no-generate-report`.

---

### Cenário 3: Regenerar Apenas o PDF

```powershell
python -m src.pdf_generator
```

Recalcula os resultados a partir da base tratada (e dos dados opcionais da spec 004, se houver) e monta o PDF com as figuras existentes.

---

### Cenário 4: Consulta Rápida aos Extremos do Período

```powershell
python -c "from src.analyzer import carregar_dados_tratados, mapear_extremos_historicos; df = carregar_dados_tratados(); print(mapear_extremos_historicos(df).to_string())"
```

Mostra, para cada grandeza, o máximo e o mínimo do período com data e hora, sem os registros sinalizados (R6 a R9).

---

### Cenário 5: Conferência do Relatório Gerado

```powershell
# Nenhuma das afirmações removidas na auditoria de 30/09/2026 deve aparecer (saída vazia esperada;
# se algum termo aparecer, conferir o contexto da linha)
Select-String -Path reports\relatorio_analise_estatistica.md -Pattern '96,1%','Francis','18/05/2018','SATISFAT','cumpre integralmente','154 m'

# Quantidade de constatações: 12 sem os dados opcionais da spec 004
(Select-String -Path reports\relatorio_analise_estatistica.md -Pattern '^\d+\. \*\*').Count

# Período, parâmetros e garantia física no cabeçalho do Markdown
Get-Content reports\relatorio_analise_estatistica.md -TotalCount 6
```

Conferir no cabeçalho: período iniciando em 28/08/2018, turbinas Kaplan de eixo vertical e garantia física de 36,4 MWmed.

---

### Cenário 6: Execução da Suíte de Testes

```powershell
# Testes desta feature
pytest tests/test_analyzer.py tests/test_pdf_generator.py -v

# Suíte completa
pytest tests/ -v
```

`test_integracao_base_real` usa a base tratada real e é pulado se ela não existir.

---

## 4. Referências

- [Especificação da Feature (spec.md)](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/003-analise-dados/spec.md)
- [Modelo de Dados Analítico (data-model.md)](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/003-analise-dados/data-model.md)
- [Contrato da Interface CLI (contracts/cli-contract.md)](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/003-analise-dados/contracts/cli-contract.md)
- Seções opcionais do relatório: `specs/004-conferencia-outros`
