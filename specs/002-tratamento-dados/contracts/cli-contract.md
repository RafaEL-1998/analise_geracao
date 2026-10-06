# CLI Contract: Módulo Processador, Validador e Exportador Multi-Formato

Este documento define a interface de linha de comando (CLI), os parâmetros, as saídas e os códigos de retorno do tratamento, da validação e da exportação da base tratada.

**Revisão retroativa (2026-10-05)**: contrato conferido contra `main()` e `executar_pipeline_tratamento()` em `src/processor.py`. A versão anterior está em `cli-contract.md.2026-10-05.bak`.

---

## 1. Comando de Execução

O processador é acionado de forma independente (não é chamado por `python -m src.main`):

```powershell
python -m src.processor [OPÇÕES]
```

A mesma lógica está disponível como função: `executar_pipeline_tratamento(input_file, output_dir, export_formats, validate_physics, generate_report) -> int`, que retorna o código de saída em vez de encerrar o processo.

---

## 2. Argumentos de Linha de Comando (Flags)

| Flag | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `--input-file` | Caminho | `data/processed/uhe_sao_domingos_energia_vertida_consolidado.csv` | Base consolidada de entrada (CSV com `;`). |
| `--output-dir` | Caminho | `data/processed` | Diretório onde a base tratada e os relatórios são gravados (criado se não existir). |
| `--export-formats` | Texto (lista separada por vírgula) | `xlsx,parquet,csv` | Formatos a gerar. Aceita `xlsx`, `parquet` e `csv`, sem diferenciar maiúsculas; valores não reconhecidos são ignorados sem erro; lista vazia equivale ao padrão. |
| `--validate-physics` / `--no-validate-physics` | Booleano (`argparse.BooleanOptionalAction`) | ativado | Executa as regras R1 a R9. Desligado, R1 não é avaliada (o código `3` não ocorre) e os relatórios não são gerados; as colunas de sinalização continuam sendo acrescentadas. |
| `--generate-report` / `--no-generate-report` | Booleano (`argparse.BooleanOptionalAction`) | ativado | Grava `relatorio_validacao_fisica.md` e `.csv`. Só tem efeito com a validação ativada. |
| `--log-level` | Escolha | `INFO` | Nível de log dos módulos `processor` e `validator` (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 3. Sequência de Execução

1. Carrega a base consolidada e confere as colunas obrigatórias (6 de identificação, `cod_usina`, `din_instante` e as 10 métricas); avisa se faltar `arquivo_origem` ou `tipo_match`.
2. Carrega o dicionário de dados e confere as 10 colunas métricas (ausência no dicionário gera aviso).
3. Tipagem: métricas em `float64` (ausentes permanecem NaN), `cod_usina` em `Int64`, `din_instante` em data/hora.
4. Se a validação estiver ativada: avalia R1 a R9 e registra cada resultado no log; se R1 tiver violação, encerra com código `3`.
5. Acrescenta as colunas `anomalia_*` e `qualidade_registro` (sempre).
6. Se validação e relatório estiverem ativados: grava os relatórios.
7. Exporta nos formatos selecionados.

---

## 4. Códigos de Retorno (Exit Codes)

| Código | Significado | Descrição |
| :---: | :--- | :--- |
| `0` | **Sucesso** | Tratamento concluído e arquivos exportados. Ocorre também quando há violações de R2 a R9, que ficam registradas no log, nos relatórios e nas colunas de sinalização. |
| `1` | **Erro de Execução / Dados** | Base consolidada ou dicionário não encontrado, coluna obrigatória ausente, `din_instante` inválido, falha de leitura/escrita ou qualquer erro inesperado. |
| `2` | **Erro de Argumentos** | Parâmetro desconhecido ou valor inválido (ex.: `--log-level` fora das opções); emitido pelo `argparse`. |
| `3` | **Inconsistência Física Crítica** | Ao menos um registro com valor negativo (violação de R1). O processamento para antes da sinalização, dos relatórios e da exportação; nenhum arquivo é gravado. |

---

## 5. Artefatos de Saída Gerados

Gravados em `--output-dir`, sobrescrevendo versões anteriores:

1. **Excel (`uhe_sao_domingos_energia_vertida_tratado.xlsx`)**: aba `UHE_SAO_DOMINGOS`, cabeçalho congelado, métricas como células numéricas nativas, 25 colunas (20 da base consolidada, 4 `anomalia_*` e `qualidade_registro`).
2. **Parquet (`uhe_sao_domingos_energia_vertida_tratado.parquet`)**: mesmas 25 colunas; métricas `double`, `cod_usina` `int64`, instante `timestamp`, anomalias `bool`.
3. **CSV (`uhe_sao_domingos_energia_vertida_tratado.csv`)**: delimitador `;`, ponto decimal, UTF-8, datas `YYYY-MM-DD HH:MM:SS`, precisão integral; ausentes como célula vazia.
4. **Relatório de Validação (`relatorio_validacao_fisica.md` e `relatorio_validacao_fisica.csv`)**: resultado de R1 a R9 por regra; o Markdown inclui a leitura de cada regra, a ressalva sobre R1 a R5 e os primeiros 40 registros sinalizados.

---

## 6. Logging

Formato `[AAAA-MM-DD HH:MM:SS] [NÍVEL] [processor|validator] mensagem`, com: arquivos de entrada e destino, formatos selecionados, linhas e colunas carregadas, ausentes por coluna, resultado de cada regra (`R# nome: N violações (SITUAÇÃO)`), total de registros sinalizados e caminho de cada arquivo gravado.

---

## Notas de revisão (2026-10-05)

- `--validate-physics` e `--generate-report` passaram a ter a forma negativa (`--no-...`); no contrato original eram booleanos com padrão `True` sem forma de desligar.
- `--export-formats`: documentados o tratamento de valores não reconhecidos e da lista vazia.
- Código `0`: deixou de significar "0 violações físicas"; violações de R2 a R9 não alteram o código.
- Código `1`: incluídos `din_instante` inválido, coluna obrigatória ausente e dicionário ausente.
- Código `3`: restrito a R1 e explicitado que nada é gravado.
- Acrescentadas as seções de sequência de execução e de logging e a descrição das 25 colunas de saída.
