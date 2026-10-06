# Quickstart: Validação e Execução do Tratamento de Dados - UHE São Domingos

Este guia fornece os passos reprodutíveis e cenários de verificação para executar o tratamento, a validação (R1 a R9), a sinalização de anomalias e a exportação multi-formato da base da UHE São Domingos.

**Revisão retroativa (2026-10-05)**: comandos conferidos contra `src/processor.py` e `src/validator.py`. Os resultados esperados correspondem à execução de 30/09/2026 registrada em `data/processed/relatorio_validacao_fisica.md`; o pipeline não foi reexecutado nesta revisão. A versão anterior está em `quickstart.md.2026-10-05.bak`.

---

## 1. Pré-requisitos e Ambiente

- **Sistema Operacional**: Windows com PowerShell.
- **Python**: Versão 3.10+ (ambiente virtual em `.\venv`, Python 3.14.6).
- **Dependências** (`requirements.txt`):
  - `pandas>=2.0.0`
  - `openpyxl>=3.1.0` (exportação Excel `.xlsx`)
  - `pyarrow>=14.0.0` (exportação Parquet `.parquet`)
  - `pytest>=7.0.0` (testes automatizados)
- **Base de Entrada**:
  - `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv` (70.895 registros horários de 28/08/2018 00h a 28/09/2026 23h, gerados pela Feature 001 com `python -m src.main --full-pipeline`).
- **Referências**:
  - `DicionarioDados_EnergiaVertidaTurbinavel.json` (dicionário oficial na raiz do projeto; obrigatório).
  - Parâmetros técnicos da usina em `src/config.py` (fonte: RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3).

---

## 2. Instalação e Preparação

No terminal PowerShell:

```powershell
# Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar/atualizar dependências
pip install -r requirements.txt
```

---

## 3. Cenários de Execução e Validação

### Cenário 1: Execução do Pipeline Completo (Tratamento, Validação, Sinalização e Exportação)

Com os valores padrão (equivalente a informar todos os argumentos abaixo):

```powershell
python -m src.processor
```

Forma explícita:

```powershell
python -m src.processor --input-file data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv --output-dir data/processed --export-formats xlsx,parquet,csv --validate-physics --generate-report
```

**Resultados Esperados**:
1. O processo finaliza com código de saída `0`. Violações de R2 a R9 não alteram o código; só uma violação de R1 (valor negativo) encerra com `3`.
2. O log informa, para cada regra, a quantidade de violações e a situação. Resultado de 30/09/2026:

   | Regra | Violações | Situação |
   | :---: | ---: | :---: |
   | R1 a R5 | 0 | CONFORME |
   | R6 | 1 | VIOLADA |
   | R7 | 293 | VIOLADA |
   | R8 | 185 | VIOLADA |
   | R9 | 63 | VIOLADA |

   e "Registros sinalizados com anomalia de plausibilidade física: 526 de 70895."
3. São gravados em `data/processed/`:
   - `uhe_sao_domingos_energia_vertida_tratado.xlsx`: aba `UHE_SAO_DOMINGOS`, 70.895 linhas e 25 colunas, métricas como células numéricas.
   - `uhe_sao_domingos_energia_vertida_tratado.parquet`: mesmas 25 colunas, métricas `double`, instante `timestamp`.
   - `uhe_sao_domingos_energia_vertida_tratado.csv`: delimitador `;`, ponto decimal, precisão integral.
   - `relatorio_validacao_fisica.md`: resultado das regras, leitura de cada uma, ressalva sobre R1 a R5 e os primeiros 40 registros sinalizados.
   - `relatorio_validacao_fisica.csv`: resultado numérico das 9 regras.

---

### Cenário 2: Verificação Isolada das Regras

Executa só a tipagem e a validação, sem gravar arquivos:

```powershell
python -c "from src.validator import carregar_base_consolidada, validar_regras_fisicas; from src.processor import padronizar_tipagem_numerica; df = padronizar_tipagem_numerica(carregar_base_consolidada()); df_res, _ = validar_regras_fisicas(df); print(df_res[['codigo_regra', 'grupo', 'violacoes', 'status']].to_string(index=False))"
```

**Critérios de Aceite**:
- A tabela lista as 9 regras (R1 a R9), cada uma com 70.895 registros avaliados.
- R1 a R5 (consistência interna ONS): 0 violações na base de 30/09/2026.
- R6 a R9 (plausibilidade física): 1, 293, 185 e 63 violações na base de 30/09/2026.
- `validar_regras_fisicas` retorna uma tupla `(DataFrame, lista de RegraResultado)`.

---

### Cenário 3: Conferência dos Registros Sinalizados

Lista os registros com anomalia na base tratada, a começar pelo único que viola R6:

```powershell
python -c "import pandas as pd; df = pd.read_parquet('data/processed/uhe_sao_domingos_energia_vertida_tratado.parquet'); print(len(df), (df['qualidade_registro'] != 'OK').sum()); print(df.loc[df['anomalia_limite_fisico'], ['din_instante', 'val_geracao', 'val_disponibilidade', 'val_produtividade', 'qualidade_registro']].to_string(index=False))"
```

**Critérios de Aceite**:
- 70.895 registros na base tratada (nenhum removido) e 526 sinalizados.
- O registro de R6 é 15/05/2019 14h, geração 68,743 MW, disponibilidade 22,817 MW, `qualidade_registro` = `R6;R7;R8`.

---

### Cenário 4: Execução sem Validação

```powershell
python -m src.processor --no-validate-physics
```

**Resultados Esperados**:
- Código de saída `0` (R1 não é avaliada, portanto o código `3` não ocorre).
- Os relatórios `relatorio_validacao_fisica.*` não são gerados nem atualizados; os arquivos já existentes continuam sendo os da execução anterior e podem não corresponder à base exportada.
- A base exportada continua com as colunas `anomalia_*` e `qualidade_registro`.

Para validar sem regravar os relatórios: `python -m src.processor --no-generate-report` (a validação roda, o log traz o resultado por regra e o código `3` continua possível).

---

### Cenário 5: Execução da Suíte de Testes da Feature

```powershell
pytest tests/test_processor.py tests/test_validator.py -v
```

**Critérios de Aceite**:
- 6 testes em `tests/test_processor.py` e 15 casos em `tests/test_validator.py`, todos aprovados.
- `test_base_real_estrutura` é ignorado se a base consolidada não existir; quando existe, verifica uma única usina, nenhum horário duplicado e a presença das 9 regras, sem fixar contagens da série.
- A suíte completa do projeto (`pytest tests/ -v`) não deve apresentar regressões nas Features 001, 003 e 004.

---

### Cenário 6: Verificação no Excel

Abrir `data/processed/uhe_sao_domingos_energia_vertida_tratado.xlsx` no Excel em português e confirmar que as colunas `val_*` são números (alinhadas à direita, somáveis) e que `din_instante` é data/hora. O `.csv` usa ponto decimal e não é o formato indicado para abrir diretamente no Excel em português.

---

## 4. Referências

- [Especificação da Feature (spec.md)](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/002-tratamento-dados/spec.md)
- [Modelo de Dados (data-model.md)](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/002-tratamento-dados/data-model.md)
- [Contrato da Interface CLI (contracts/cli-contract.md)](file:///c:/Users/rlazaro/Desktop/UHE_SAO_DOMINGOS/specs/002-tratamento-dados/contracts/cli-contract.md)

---

## Notas de revisão (2026-10-05)

- Cenário 1: o resultado esperado "código 0" deixou de significar "0 violações"; incluídos o resultado por regra e as 25 colunas de saída.
- Cenário 2: o comando original (`resultados = validar_regras_fisicas(df); print(resultados.to_string())`) não funciona com a implementação atual, que retorna uma tupla; o novo comando também aplica a tipagem antes, para que valores com vírgula decimal não virem NaN na validação. Os critérios "0 violações (100% conformes)" em R1 a R5 foram mantidos e acrescentados os de R6 a R9.
- Cenários 3, 4 e 6 acrescentados. Cenário 5 (antigo 3) restrito aos testes da feature, com contagem de casos.
