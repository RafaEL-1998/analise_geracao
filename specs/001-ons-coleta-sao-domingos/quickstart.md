# Quickstart: Validação e Execução do Pipeline ONS

Este guia rápido fornece as instruções práticas para preparar o ambiente virtual, executar a validação de ponta a ponta e inspecionar os artefatos de dados gerados.

**Revisão de 2026-10-05**: comandos e resultados esperados atualizados para o código em vigor (extração por `cod_usina` + nome do reservatório, manifesto de versões, colunas reais do relatório de auditoria). A versão anterior está em `quickstart.md.2026-10-05.bak`.

---

## 1. Pré-Requisitos do Ambiente

- **Sistema Operacional**: Windows 10/11 com PowerShell.
- **Python**: Versão 3.10 ou superior instalada (verifique com `python --version`; o `venv` do projeto usa Python 3.14).
- **Ambiente Virtual**: Diretório `venv` na raiz do projeto.
- **Rede**: acesso a `dados.ons.org.br` e `ons-aws-prod-opendata.s3.amazonaws.com` apenas para as execuções com download.

---

## 2. Preparação do Ambiente

No PowerShell, certifique-se de que o ambiente virtual está ativado e as dependências instaladas:

```powershell
# Ativação do ambiente virtual no Windows
.\venv\Scripts\Activate.ps1

# Instalação das dependências do projeto
pip install -r requirements.txt
```

Os módulos desta feature usam apenas a biblioteca padrão; o `requirements.txt` atende também as specs 002 a 004.

---

## 3. Comandos de Validação e Execução

> **Atenção**: as execuções das seções 3.2 a 3.4 regravam `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv` e `relatorio_auditoria_varredura.csv` sem gerar `.bak`, e as que baixam dados podem substituir CSVs de `data/raw/` revisados pelo ONS. A base local usada nos relatórios é a de 30/09/2026; faça cópia de segurança de `data/` antes de reexecutar.

### 3.1 Execução de Testes Automatizados
Valide a extração por código e nome, o manifesto de versões, a deduplicação e o relatório de auditoria (sem acesso à rede):

```powershell
pytest -v tests/unit tests/integration
```
*Resultado Esperado:* 15 testes aprovados (6 em `test_collector.py`, 7 em `test_filter.py`, 1 em `test_audit.py` e 1 em `test_pipeline.py`), código de retorno 0. Para a suíte completa do projeto (specs 001 a 004), use `pytest -v tests/`.

### 3.2 Execução do Pipeline Completo
Dispare a descoberta de recursos no CKAN do ONS, a sincronização dos arquivos com a versão publicada e a filtragem exaustiva. Para executar somente as etapas desta feature, acrescente `--sem-indicadores` (a etapa 3 pertence a `specs/004-conferencia-outros`):

```powershell
python -m src.main --full-pipeline --sem-indicadores
$LASTEXITCODE   # 0 = sucesso; 1 = erro de rede/execução; 2 = arquivo não lido (base incompleta) ou argumento inválido
```

Para baixar tudo de novo, ignorando o manifesto, acrescente `--force-download`.

### 3.3 Execução Apenas de Filtragem (Reprocessamento Local)
Caso os arquivos brutos já estejam em `data/raw/` e se deseje reprocessar a filtragem sem acessar a rede:

```powershell
python -m src.main --filter-only --sem-indicadores
```

### 3.4 Execução Apenas da Sincronização

```powershell
python -m src.main --download-only
```

---

## 4. Verificação dos Resultados

Após a execução bem-sucedida, valide a presença e o conteúdo dos arquivos gerados. Os valores esperados abaixo são os da base de 30/09/2026.

1. **Base Consolidada**:
   - Arquivo: `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv`
   - Verifique as primeiras linhas:
   ```powershell
   Get-Content -Path data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv -TotalCount 5
   ```
   - Verifique total, período e ausência de duplicatas:
   ```powershell
   python -c "import pandas as pd; df = pd.read_csv('data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv', sep=';'); print(len(df), df['din_instante'].min(), df['din_instante'].max(), df.duplicated(['cod_usina', 'din_instante']).sum())"
   ```
   *Resultado Esperado:* `70895 2018-08-28 00:00:00 2026-09-28 23:00:00 0`.

2. **Relatório de Auditoria**:
   - Arquivo: `data/processed/relatorio_auditoria_varredura.csv`
   - Comprove a inspeção de 100% dos arquivos e a ausência de falhas e divergências:
   ```powershell
   python -c "import pandas as pd; a = pd.read_csv('data/processed/relatorio_auditoria_varredura.csv', sep=';'); print(len(a), a['status_processamento'].value_counts().to_dict(), a['registros_extraidos'].sum(), (a['registros_codigo_sem_nome'] + a['registros_nome_sem_codigo']).sum())"
   ```
   *Resultado Esperado:* `42 {'PROCESSADO': 39, 'SEM_REGISTROS': 3} 70895 0`. Os 3 arquivos `SEM_REGISTROS` são os de 2015, 2016 e 2017; a soma de `registros_extraidos` deve ser igual ao total da base consolidada.

3. **Manifesto de Versões**:
   - Arquivo: `data/raw/_manifesto_ons.json`
   - Confira se há uma entrada por CSV, com `ultima_modificacao` e tamanhos:
   ```powershell
   (Get-Content -Raw -Encoding utf8 data/raw/_manifesto_ons.json | ConvertFrom-Json).PSObject.Properties.Name.Count
   ```
   *Resultado Esperado:* `42`.

4. **Log**: na saída do comando, confira o resumo final ("Arquivos inspecionados", "Total de registros consolidados") e a ausência das mensagens "Divergência de identificação", "Registro duplicado com valores diferentes" e "Arquivos com falha de leitura".

---

## 5. Referências

- [Especificação de Requisitos (spec.md)](spec.md)
- [Modelo de Dados (data-model.md)](data-model.md)
- [Contrato de CLI (contracts/cli-contract.md)](contracts/cli-contract.md)
- [Pesquisa e decisões (research.md)](research.md)
- [Constituição do Projeto (.specify/memory/constitution.md)](../../.specify/memory/constitution.md)
